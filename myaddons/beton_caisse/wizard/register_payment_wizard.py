from odoo import models, fields, api, _
from odoo.exceptions import UserError


class BetonRegisterPaymentWizard(models.TransientModel):
    _name = 'beton.register.payment.wizard'
    _description = 'Enregistrer un paiement caisse béton'

    cashbox_id = fields.Many2one(
        'beton.cashbox',
        string='Caisse',
        required=True,
        default=lambda self: self._default_cashbox(),
    )
    montant = fields.Monetary(
        string='Montant à payer',
        required=True,
        currency_field='currency_id',
    )
    description = fields.Text(string='Description')
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id,
    )

    payment_method = fields.Selection([
        ('cash', 'Espèces'),
        ('cheque', 'Chèque'),
        ('virement', 'Virement bancaire'),
        ('carte', 'Carte bancaire'),
    ], string='Mode de paiement', default='cash', required=True)
    bank_id = fields.Many2one('res.bank', string='Banque')
    bank_account_id = fields.Many2one(
        'res.partner.bank',
        string='Compte bancaire',
        domain="[('partner_id', '=', partner_id)]",
    )
    bank_reference = fields.Char(string='Référence / N° chèque')
    bank_date = fields.Date(string='Date chèque / virement')
    bank_holder = fields.Char(string='Titulaire')
    bank_note = fields.Text(string='Observations bancaires')

    # Context fields
    sale_order_id = fields.Many2one('sale.order', string='Bon de commande')
    purchase_order_id = fields.Many2one('purchase.order', string="Bon d'achat")
    expense_sheet_id = fields.Many2one('hr.expense.sheet', string='Note de frais')
    partner_id = fields.Many2one('res.partner', string='Bénéficiaire', readonly=True)
    payment_type = fields.Selection([
        ('sale', 'Encaissement (Vente)'),
        ('purchase', 'Décaissement (Achat)'),
        ('expense_sheet', 'Décaissement (Note de frais)'),
    ], string='Type', readonly=True)

    # Info
    amount_total = fields.Monetary(
        string='Montant total',
        currency_field='currency_id',
        readonly=True,
    )
    amount_already_paid = fields.Monetary(
        string='Déjà versé',
        currency_field='currency_id',
        readonly=True,
    )
    amount_remaining = fields.Monetary(
        string='Reste à payer',
        currency_field='currency_id',
        compute='_compute_amount_remaining',
    )

    def _default_cashbox(self):
        cashbox = self.env['beton.cashbox'].search([
            ('type', '=', 'principale'),
            ('responsible_ids', 'in', self.env.user.id),
        ], limit=1)
        if not cashbox:
            cashbox = self.env['beton.cashbox'].search([
                ('type', '=', 'principale'),
            ], limit=1)
        return cashbox

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        ctx = self._context

        if ctx.get('active_model') == 'sale.order' and ctx.get('active_id'):
            so = self.env['sale.order'].browse(ctx['active_id'])
            existing = self.env['beton.caisse.entry'].search([
                ('sale_order_id', '=', so.id),
                ('state', '=', 'approuve'),
            ])
            cumul = sum(existing.mapped('amount_paid'))
            remaining = so.amount_total - cumul
            res.update({
                'sale_order_id': so.id,
                'partner_id': so.partner_id.id,
                'payment_type': 'sale',
                'amount_total': so.amount_total,
                'amount_already_paid': cumul,
                'montant': max(remaining, 0),
                'description': 'Paiement %s' % so.name,
            })

        elif ctx.get('active_model') == 'purchase.order' and ctx.get('active_id'):
            po = self.env['purchase.order'].browse(ctx['active_id'])
            existing = self.env['beton.caisse.expense'].search([
                ('purchase_id', '=', po.id),
                ('state', '=', 'approuve'),
            ])
            cumul = sum(existing.mapped('amount_paid'))
            remaining = po.amount_total - cumul
            res.update({
                'purchase_order_id': po.id,
                'partner_id': po.partner_id.id,
                'payment_type': 'purchase',
                'amount_total': po.amount_total,
                'amount_already_paid': cumul,
                'montant': max(remaining, 0),
                'description': 'Paiement %s' % po.name,
            })

        elif ctx.get('active_model') == 'hr.expense.sheet' and ctx.get('active_id'):
            sheet = self.env['hr.expense.sheet'].browse(ctx['active_id'])
            existing = self.env['beton.caisse.expense'].search([
                ('expense_sheet_id', '=', sheet.id),
                ('state', '=', 'approuve'),
            ])
            cumul = sum(existing.mapped('amount_paid'))
            remaining = sheet.total_amount - cumul
            employee = sheet.employee_id
            partner = employee.work_contact_id or (employee.user_id.partner_id if employee.user_id else False)
            res.update({
                'expense_sheet_id': sheet.id,
                'partner_id': partner.id if partner else False,
                'payment_type': 'expense_sheet',
                'amount_total': sheet.total_amount,
                'amount_already_paid': cumul,
                'montant': max(remaining, 0),
                'description': 'Paiement %s' % sheet.name,
            })

        return res

    @api.depends('amount_total', 'amount_already_paid')
    def _compute_amount_remaining(self):
        for rec in self:
            rec.amount_remaining = rec.amount_total - rec.amount_already_paid

    def action_register_payment(self):
        self.ensure_one()
        if self.montant <= 0:
            raise UserError(_("Le montant doit être supérieur à zéro."))

        if self.amount_remaining <= 0:
            raise UserError(_("Ce bon est déjà totalement payé."))

        if self.montant > self.amount_remaining:
            raise UserError(
                _("Le montant (%s) dépasse le reste à payer (%s).")
                % (self.montant, self.amount_remaining)
            )

        if self.payment_method in ('cheque', 'virement') and not self.bank_reference:
            raise UserError(_(
                "Veuillez saisir la référence bancaire (N° de chèque ou référence de virement)."
            ))

        if self.payment_type == 'sale':
            self._register_sale_payment()
        elif self.payment_type == 'purchase':
            self._register_purchase_payment()
        elif self.payment_type == 'expense_sheet':
            self._register_expense_sheet_payment()

        return {'type': 'ir.actions.act_window_close'}

    def _bank_vals(self):
        self.ensure_one()
        return {
            'payment_method': self.payment_method,
            'bank_id': self.bank_id.id if self.bank_id else False,
            'bank_account_id': self.bank_account_id.id if self.bank_account_id else False,
            'bank_reference': self.bank_reference,
            'bank_date': self.bank_date,
            'bank_holder': self.bank_holder,
            'bank_note': self.bank_note,
        }

    def _register_sale_payment(self):
        """Encaissement client direct sans facture."""
        self.ensure_one()
        so = self.sale_order_id
        existing = self.env['beton.caisse.entry'].search([
            ('sale_order_id', '=', so.id),
            ('state', '=', 'approuve'),
        ])
        cumul = sum(existing.mapped('amount_paid'))

        vals = {
            'cashbox_id': self.cashbox_id.id,
            'sale_order_id': so.id,
            'client_id': so.partner_id.id,
            'amount': so.amount_total,
            'amount_paid': self.montant,
            'amount_verse': cumul + self.montant,
            'description': self.description or 'Paiement %s' % so.name,
        }
        vals.update(self._bank_vals())
        entry = self.env['beton.caisse.entry'].create(vals)
        entry.action_approve()

    def _register_purchase_payment(self):
        """Décaissement fournisseur direct sans facture."""
        self.ensure_one()
        po = self.purchase_order_id

        if self.cashbox_id.total_amount < self.montant:
            raise UserError(
                _("Solde insuffisant dans '%s'. Solde : %s")
                % (self.cashbox_id.name, self.cashbox_id.total_amount)
            )

        existing = self.env['beton.caisse.expense'].search([
            ('purchase_id', '=', po.id),
            ('state', '=', 'approuve'),
        ])
        cumul = sum(existing.mapped('amount_paid'))

        vals = {
            'cashbox_id': self.cashbox_id.id,
            'purchase_id': po.id,
            'fournisseur': po.partner_id.id,
            'amount': po.amount_total,
            'amount_paid': self.montant,
            'amount_verse': cumul + self.montant,
            'description': self.description or 'Paiement %s' % po.name,
        }
        vals.update(self._bank_vals())
        expense = self.env['beton.caisse.expense'].create(vals)
        expense.action_approve()

    def _register_expense_sheet_payment(self):
        """Décaissement note de frais (paiement d'un employé)."""
        self.ensure_one()
        sheet = self.expense_sheet_id

        if self.cashbox_id.total_amount < self.montant:
            raise UserError(
                _("Solde insuffisant dans '%s'. Solde : %s")
                % (self.cashbox_id.name, self.cashbox_id.total_amount)
            )

        existing = self.env['beton.caisse.expense'].search([
            ('expense_sheet_id', '=', sheet.id),
            ('state', '=', 'approuve'),
        ])
        cumul = sum(existing.mapped('amount_paid'))

        employee = sheet.employee_id
        partner = employee.work_contact_id or (employee.user_id.partner_id if employee.user_id else False)

        vals = {
            'cashbox_id': self.cashbox_id.id,
            'expense_sheet_id': sheet.id,
            'fournisseur': partner.id if partner else False,
            'amount': sheet.total_amount,
            'amount_paid': self.montant,
            'amount_verse': cumul + self.montant,
            'description': self.description or 'Paiement %s' % sheet.name,
        }
        vals.update(self._bank_vals())
        expense = self.env['beton.caisse.expense'].create(vals)
        expense.action_approve()
