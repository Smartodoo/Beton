from odoo import models, fields, api, _
from odoo.exceptions import UserError

MSG_LECTURE_SEULE = _("Accès refusé : vous avez uniquement un accès en lecture sur les caisses béton.")


class BetonCaisseExpense(models.Model):
    _name = 'beton.caisse.expense'
    _description = 'Décaissement Caisse Béton'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'
    _rec_name = 'name'

    name = fields.Char(
        string='Référence',
        readonly=True,
        default='Nouveau',
        copy=False,
    )
    date = fields.Datetime(
        string='Date',
        required=True,
        default=fields.Datetime.now,
        tracking=True,
    )
    cashbox_id = fields.Many2one(
        'beton.cashbox',
        string='Caisse',
        required=True,
        tracking=True,
    )
    purchase_id = fields.Many2one(
        'purchase.order',
        string="Bon d'achat",
        tracking=True,
    )
    expense_sheet_id = fields.Many2one(
        'hr.expense.sheet',
        string='Note de frais',
        tracking=True,
    )
    source_type = fields.Selection([
        ('purchase', 'Achat'),
        ('expense_sheet', 'Note de frais'),
    ], string='Origine', compute='_compute_source_type', store=True, default='purchase')
    fournisseur = fields.Many2one(
        'res.partner',
        string='Bénéficiaire',
        tracking=True,
    )
    # Montants
    amount = fields.Monetary(
        string='Montant total',
        currency_field='company_currency_id',
        tracking=True,
    )
    amount_paid = fields.Monetary(
        string='Versement',
        currency_field='company_currency_id',
        tracking=True,
    )
    amount_verse = fields.Monetary(
        string='Cumul versé',
        currency_field='company_currency_id',
        readonly=True,
    )
    amount_residual = fields.Monetary(
        string='Reste à payer',
        currency_field='company_currency_id',
        compute='_compute_amount_residual',
        store=True,
    )
    description = fields.Text(string='Description', required=True)
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('approuve', 'Approuvé'),
    ], string='État', default='draft', tracking=True)

    payment_method = fields.Selection([
        ('cash', 'Espèces'),
        ('cheque', 'Chèque'),
        ('virement', 'Virement bancaire'),
        ('carte', 'Carte bancaire'),
    ], string='Mode de paiement', default='cash', required=True, tracking=True)
    bank_id = fields.Many2one('res.bank', string='Banque', tracking=True)
    bank_account_id = fields.Many2one(
        'res.partner.bank',
        string='Compte bancaire',
        domain="[('partner_id', '=', fournisseur)]",
    )
    bank_reference = fields.Char(string='Référence', tracking=True)
    bank_date = fields.Date(string='Date chèque / virement')
    bank_holder = fields.Char(string='Titulaire')
    bank_note = fields.Text(string='Observations bancaires')

    # Champs spécifiques au paiement par chèque
    cheque_number = fields.Char(string='N° de chèque')
    cheque_date = fields.Date(string='Date du chèque')
    cheque_domiciliation = fields.Char(string='Domiciliation bancaire')

    payment_id = fields.Many2one('account.payment', string='Paiement associé')
    invoice_id = fields.Many2one('account.move', string='Facture associée')
    user_id = fields.Many2one(
        'res.users',
        string='Caissier',
        default=lambda self: self.env.user,
        readonly=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Société',
        default=lambda self: self.env.company,
        required=True,
    )
    company_currency_id = fields.Many2one(
        related='company_id.currency_id',
        string='Devise',
    )
    notes = fields.Text(string='Notes')

    is_totally_paid = fields.Boolean(compute='_compute_payment_status', store=True)
    is_partially_paid = fields.Boolean(compute='_compute_payment_status', store=True)

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.user.has_group('beton_caisse.group_beton_caisse_lecture_seule'):
            raise UserError(MSG_LECTURE_SEULE)
        for vals in vals_list:
            if vals.get('name', 'Nouveau') == 'Nouveau':
                vals['name'] = self.env['ir.sequence'].next_by_code('beton.caisse.expense') or 'Nouveau'
        return super().create(vals_list)

    def write(self, vals):
        if self.env.user.has_group('beton_caisse.group_beton_caisse_lecture_seule'):
            raise UserError(MSG_LECTURE_SEULE)
        return super().write(vals)

    def unlink(self):
        if self.env.user.has_group('beton_caisse.group_beton_caisse_lecture_seule'):
            raise UserError(MSG_LECTURE_SEULE)
        for rec in self:
            if rec.state != 'draft':
                raise UserError("Impossible de supprimer un décaissement approuvé.")
        return super().unlink()

    @api.depends('amount', 'amount_verse')
    def _compute_amount_residual(self):
        for rec in self:
            rec.amount_residual = rec.amount - rec.amount_verse

    @api.depends('amount', 'amount_residual')
    def _compute_payment_status(self):
        for rec in self:
            rec.is_totally_paid = rec.state == 'approuve' and rec.amount_residual <= 0
            rec.is_partially_paid = rec.state == 'approuve' and 0 < rec.amount_residual < rec.amount

    @api.depends('purchase_id', 'expense_sheet_id')
    def _compute_source_type(self):
        for rec in self:
            if rec.expense_sheet_id:
                rec.source_type = 'expense_sheet'
            else:
                rec.source_type = 'purchase'

    @api.onchange('purchase_id')
    def _onchange_purchase_id(self):
        if self.purchase_id:
            self.fournisseur = self.purchase_id.partner_id
            self.amount = self.purchase_id.amount_total
            self.description = self.purchase_id.name
            self.expense_sheet_id = False

    @api.onchange('expense_sheet_id')
    def _onchange_expense_sheet_id(self):
        if self.expense_sheet_id:
            sheet = self.expense_sheet_id
            employee = sheet.employee_id
            partner = employee.work_contact_id or (employee.user_id.partner_id if employee.user_id else False)
            self.fournisseur = partner or False
            self.amount = sheet.total_amount
            self.description = sheet.name
            self.purchase_id = False

    def action_approve(self):
        force = self.env.context.get('beton_force_approve')
        for rec in self:
            if rec.state == 'draft':
                if not force and rec.cashbox_id.total_amount < rec.amount_paid:
                    raise UserError(
                        "Solde insuffisant dans la caisse '%s'. Solde actuel : %s"
                        % (rec.cashbox_id.name, rec.cashbox_id.total_amount)
                    )
                rec.cashbox_id.sudo().total_amount -= rec.amount_paid
                rec.state = 'approuve'
                rec._update_globale()

    def action_to_draft(self):
        for rec in self:
            if rec.state == 'approuve':
                rec.cashbox_id.sudo().total_amount += rec.amount_paid
                rec.state = 'draft'
                if rec.payment_id:
                    rec.payment_id.sudo().unlink()
                    rec.payment_id = False

    def _update_globale(self):
        """Crée ou met à jour la dépense globale pour le fournisseur."""
        self.ensure_one()
        partner = self.fournisseur
        if not partner:
            return
        globale = self.env['beton.caisse.globale'].search([
            ('partner_id', '=', partner.id),
            ('partner_type', '=', 'fournisseur'),
        ], limit=1)
        if globale:
            if self.id not in globale.expense_ids.ids:
                globale.write({'expense_ids': [(4, self.id)]})
        else:
            self.env['beton.caisse.globale'].create({
                'partner_id': partner.id,
                'partner_type': 'fournisseur',
                'expense_ids': [(4, self.id)],
            })

    def action_preview_report(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': '/report/pdf/beton_caisse.report_beton_expense_template/%s' % self.id,
            'target': 'new',
        }

    def action_preview_report_multi(self):
        if not self:
            raise UserError("Veuillez sélectionner au moins un enregistrement.")
        ids_str = ','.join(str(r.id) for r in self)
        return {
            'type': 'ir.actions.act_url',
            'url': '/report/pdf/beton_caisse.report_beton_expense_template/%s' % ids_str,
            'target': 'new',
        }
