from odoo import models, fields, api, _


# Mapping : code du payment_method_line_id natif -> valeur Selection des modèles béton
PAYMENT_METHOD_CODE_MAP = {
    'beton_cheque': 'cheque',
    'beton_virement': 'virement',
    'beton_carte': 'carte',
    'beton_especes': 'cash',
}


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    beton_cashbox_id = fields.Many2one('beton.cashbox', string='Caisse Béton')
    beton_bank_holder = fields.Char(string='Titulaire (Béton)')
    beton_bank_note = fields.Text(string='Observations bancaires (Béton)')

    # Champs spécifiques au paiement par chèque (mode 'beton_cheque')
    cheque_reference = fields.Char(
        string="N° de chèque",
        copy=False,
        help="Numéro du chèque utilisé pour ce paiement.",
    )
    cheque_date = fields.Date(
        string="Date du chèque",
        copy=False,
        help="Date d'émission du chèque.",
    )
    cheque_domiciliation = fields.Char(
        string="Domiciliation bancaire",
        copy=False,
        help="Banque / agence sur laquelle le chèque est tiré.",
    )
    payment_method_code = fields.Char(
        related='payment_method_line_id.code',
        string="Code mode paiement",
        readonly=True,
        store=True,
    )

    def _get_beton_cashbox(self):
        """Retourne la caisse béton selon le journal du paiement.
        - journal banque   -> caisse de type 'banque'
        - journal espèces  -> caisse de type 'principale'
        - sinon            -> caisse principale de l'utilisateur (fallback).
        """
        Cashbox = self.env['beton.cashbox']
        target_type = 'principale'
        jtype = self.journal_id.type if self.journal_id else False
        if jtype == 'bank':
            target_type = 'banque'
        elif jtype == 'cash':
            target_type = 'principale'

        cashbox = Cashbox.search([
            ('type', '=', target_type),
            ('responsible_ids', 'in', self.env.user.id),
        ], limit=1)
        if not cashbox:
            cashbox = Cashbox.search([('type', '=', target_type)], limit=1)
        if not cashbox:
            # Ultime fallback : n'importe quelle caisse principale
            cashbox = Cashbox.search([('type', '=', 'principale')], limit=1)
        return cashbox

    def _derive_beton_payment_method(self):
        """Traduit le payment_method_line_id natif en valeur Selection béton."""
        self.ensure_one()
        code = self.payment_method_line_id.code if self.payment_method_line_id else False
        if code in PAYMENT_METHOD_CODE_MAP:
            return PAYMENT_METHOD_CODE_MAP[code]
        jtype = self.journal_id.type if self.journal_id else False
        if jtype == 'cash':
            return 'cash'
        return 'virement'

    def _beton_bank_vals(self):
        """Valeurs bancaires à propager vers beton.caisse.entry/expense."""
        self.ensure_one()
        journal_bank = self.journal_id.bank_account_id if self.journal_id else False
        partner_bank = self.partner_bank_id
        holder = self.beton_bank_holder or (
            partner_bank.acc_holder_name if partner_bank else False
        ) or (self.partner_id.name if self.partner_id else False)
        return {
            'payment_method': self._derive_beton_payment_method(),
            'bank_id': journal_bank.bank_id.id if journal_bank and journal_bank.bank_id else False,
            'bank_account_id': partner_bank.id if partner_bank else False,
            'bank_reference': self.ref or False,
            'bank_date': self.date,
            'bank_holder': holder,
            'bank_note': self.beton_bank_note or False,
            # Champs spécifiques chèque
            'cheque_number': self.cheque_reference or False,
            'cheque_date': self.cheque_date or False,
            'cheque_domiciliation': self.cheque_domiciliation or False,
        }

    def action_post(self):
        res = super().action_post()
        for payment in self:
            payment._create_beton_caisse_records()
        return res

    def _create_beton_caisse_records(self, invoices=None):
        """Crée automatiquement les enregistrements de caisse béton après
        confirmation du paiement de facture.
        - payment_type == 'inbound'  -> beton.caisse.entry
        - payment_type == 'outbound' -> beton.caisse.expense
        Le record est lié à la SO/PO/note de frais si présente, sinon
        directement à la facture.

        :param invoices: optionnel, recordset account.move à traiter ;
            si None, utilise self.reconciled_invoice_ids.
        """
        self.ensure_one()
        cashbox = self.beton_cashbox_id or self._get_beton_cashbox()
        if not cashbox:
            return

        if invoices is None:
            invoices = self.reconciled_invoice_ids
        if not invoices:
            return

        bank_vals = self._beton_bank_vals()

        for invoice in invoices:
            if self.payment_type == 'inbound':
                self._create_beton_entry_for_invoice(cashbox, invoice, bank_vals)
            elif self.payment_type == 'outbound':
                self._create_beton_expense_for_invoice(cashbox, invoice, bank_vals)

    def _create_beton_entry_for_invoice(self, cashbox, invoice, bank_vals):
        """Encaissement client pour un paiement de facture."""
        self.ensure_one()
        # Déduplication : un seul record par (payment, invoice)
        if self.env['beton.caisse.entry'].search_count([
            ('payment_id', '=', self.id),
            ('invoice_id', '=', invoice.id),
        ]):
            return

        sale_order = invoice.mapped('invoice_line_ids.sale_line_ids.order_id')[:1]

        # Montant total et référence selon la source
        if sale_order:
            amount_total = sale_order.amount_total
            ref_name = sale_order.name
            cumul_domain = [('sale_order_id', '=', sale_order.id), ('state', '=', 'approuve')]
        else:
            amount_total = invoice.amount_total
            ref_name = invoice.name or invoice.display_name
            cumul_domain = [('invoice_id', '=', invoice.id), ('state', '=', 'approuve')]

        existing = self.env['beton.caisse.entry'].search(cumul_domain)
        cumul = sum(existing.mapped('amount_paid'))

        vals = {
            'cashbox_id': cashbox.id,
            'sale_order_id': sale_order.id if sale_order else False,
            'invoice_id': invoice.id,
            'client_id': invoice.partner_id.id,
            'amount': amount_total,
            'amount_paid': self.amount,
            'amount_verse': cumul + self.amount,
            'description': 'Paiement %s - %s' % (ref_name, self.name),
            'payment_id': self.id,
        }
        vals.update(bank_vals)
        entry = self.env['beton.caisse.entry'].create(vals)
        entry.action_approve()

    def _create_beton_expense_for_invoice(self, cashbox, invoice, bank_vals):
        """Décaissement fournisseur ou note de frais pour un paiement de facture."""
        self.ensure_one()
        # Déduplication : un seul record par (payment, invoice)
        if self.env['beton.caisse.expense'].search_count([
            ('payment_id', '=', self.id),
            ('invoice_id', '=', invoice.id),
        ]):
            return

        purchase_order = invoice.mapped('invoice_line_ids.purchase_line_id.order_id')[:1]
        expense_sheet = (
            invoice.expense_sheet_id
            if 'expense_sheet_id' in invoice._fields else False
        )

        # Détermine source + montant total + bénéficiaire
        if purchase_order:
            amount_total = purchase_order.amount_total
            ref_name = purchase_order.name
            partner_id = purchase_order.partner_id.id
            cumul_domain = [('purchase_id', '=', purchase_order.id), ('state', '=', 'approuve')]
            vals_source = {
                'purchase_id': purchase_order.id,
                'expense_sheet_id': False,
            }
        elif expense_sheet:
            employee = expense_sheet.employee_id
            employee_partner = employee.work_contact_id or (
                employee.user_id.partner_id if employee.user_id else False
            )
            amount_total = expense_sheet.total_amount
            ref_name = expense_sheet.name
            partner_id = employee_partner.id if employee_partner else invoice.partner_id.id
            cumul_domain = [('expense_sheet_id', '=', expense_sheet.id), ('state', '=', 'approuve')]
            vals_source = {
                'purchase_id': False,
                'expense_sheet_id': expense_sheet.id,
            }
        else:
            amount_total = invoice.amount_total
            ref_name = invoice.name or invoice.display_name
            partner_id = invoice.partner_id.id
            cumul_domain = [('invoice_id', '=', invoice.id), ('state', '=', 'approuve')]
            vals_source = {
                'purchase_id': False,
                'expense_sheet_id': False,
            }

        existing = self.env['beton.caisse.expense'].search(cumul_domain)
        cumul = sum(existing.mapped('amount_paid'))

        vals = {
            'cashbox_id': cashbox.id,
            'invoice_id': invoice.id,
            'fournisseur': partner_id,
            'amount': amount_total,
            'amount_paid': self.amount,
            'amount_verse': cumul + self.amount,
            'description': 'Paiement %s - %s' % (ref_name, self.name),
            'payment_id': self.id,
        }
        vals.update(vals_source)
        vals.update(bank_vals)
        expense = self.env['beton.caisse.expense'].create(vals)
        # Auto-approbation forcée : la caisse est débitée même si solde insuffisant
        # (protection conservée pour les approbations manuelles)
        expense.with_context(beton_force_approve=True).action_approve()
        if cashbox.total_amount < 0:
            expense.message_post(body=_(
                "Attention : la caisse '%s' est passée en solde négatif (%s)."
            ) % (cashbox.name, cashbox.total_amount))


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    beton_cashbox_id = fields.Many2one(
        'beton.cashbox',
        string='Caisse Béton',
        compute='_compute_beton_cashbox_by_journal',
        store=True,
        readonly=False,
    )
    beton_bank_holder = fields.Char(string='Titulaire (Béton)')
    beton_bank_note = fields.Text(string='Observations bancaires (Béton)')

    @api.depends('journal_id')
    def _compute_beton_cashbox_by_journal(self):
        """Pré-remplit la caisse béton selon le type de journal :
        - Banque  -> caisse de type 'banque'
        - Espèces -> caisse de type 'principale'
        Utilise en priorité une caisse dont l'utilisateur courant est responsable.
        """
        Cashbox = self.env['beton.cashbox']
        for wizard in self:
            target_type = 'principale'
            if wizard.journal_id and wizard.journal_id.type == 'bank':
                target_type = 'banque'
            cashbox = Cashbox.search([
                ('type', '=', target_type),
                ('active', '=', True),
                ('responsible_ids', 'in', self.env.user.id),
            ], limit=1)
            if not cashbox:
                cashbox = Cashbox.search([
                    ('type', '=', target_type),
                    ('active', '=', True),
                ], limit=1)
            if not cashbox and target_type != 'principale':
                cashbox = Cashbox.search([
                    ('type', '=', 'principale'),
                    ('active', '=', True),
                ], limit=1)
            wizard.beton_cashbox_id = cashbox

    # Champs spécifiques au paiement par chèque
    cheque_reference = fields.Char(string="N° de chèque")
    cheque_date = fields.Date(string="Date du chèque")
    cheque_domiciliation = fields.Char(string="Domiciliation bancaire")
    payment_method_code = fields.Char(
        related='payment_method_line_id.code',
        string="Code mode paiement",
        readonly=True,
    )

    def _create_payment_vals_from_wizard(self, batch_result):
        vals = super()._create_payment_vals_from_wizard(batch_result)
        vals.update({
            'beton_cashbox_id': self.beton_cashbox_id.id if self.beton_cashbox_id else False,
            'beton_bank_holder': self.beton_bank_holder,
            'beton_bank_note': self.beton_bank_note,
            'cheque_reference': self.cheque_reference,
            'cheque_date': self.cheque_date,
            'cheque_domiciliation': self.cheque_domiciliation,
        })
        return vals

    def _create_payments(self):
        """Déclenche le hook béton APRÈS la réconciliation native.
        - Force l'écriture des champs béton sur tous les paiements créés
          (couvre les modes edit ET batch d'Odoo).
        - Passe explicitement les invoices au hook (line_ids du wizard) pour
          ne pas dépendre de reconciled_invoice_ids qui peut être en retard.
        """
        payments = super()._create_payments()
        if not payments:
            return payments

        # Force-set des champs béton + chèque sur tous les paiements créés
        write_vals = {}
        if self.beton_cashbox_id:
            write_vals['beton_cashbox_id'] = self.beton_cashbox_id.id
        if self.beton_bank_holder:
            write_vals['beton_bank_holder'] = self.beton_bank_holder
        if self.beton_bank_note:
            write_vals['beton_bank_note'] = self.beton_bank_note
        if self.cheque_reference:
            write_vals['cheque_reference'] = self.cheque_reference
        if self.cheque_date:
            write_vals['cheque_date'] = self.cheque_date
        if self.cheque_domiciliation:
            write_vals['cheque_domiciliation'] = self.cheque_domiciliation
        if write_vals:
            payments.write(write_vals)

        # Récupère les invoices payées depuis les line_ids du wizard
        wizard_invoices = self.line_ids.move_id

        # Invalide le cache pour les computes potentiels
        payments.invalidate_recordset(['reconciled_invoice_ids'])

        for payment in payments:
            target_invoices = payment.reconciled_invoice_ids or wizard_invoices
            payment._create_beton_caisse_records(invoices=target_invoices)
        return payments
