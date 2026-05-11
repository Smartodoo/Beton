from odoo import models, fields, api, _
from odoo.exceptions import UserError

MSG_LECTURE_SEULE = _("Accès refusé : vous avez uniquement un accès en lecture sur les caisses béton.")


class BetonCaisseEntry(models.Model):
    _name = 'beton.caisse.entry'
    _description = 'Encaissement Caisse Béton'
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
        domain="[('type', '=', 'principale')]",
        tracking=True,
    )
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Bon de commande',
        tracking=True,
    )
    client_id = fields.Many2one(
        'res.partner',
        string='Client',
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
        domain="[('partner_id', '=', client_id)]",
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

    is_totally_paid = fields.Boolean(compute='_compute_payment_status', store=True)
    is_partially_paid = fields.Boolean(compute='_compute_payment_status', store=True)

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.user.has_group('beton_caisse.group_beton_caisse_lecture_seule'):
            raise UserError(MSG_LECTURE_SEULE)
        for vals in vals_list:
            if vals.get('name', 'Nouveau') == 'Nouveau':
                vals['name'] = self.env['ir.sequence'].next_by_code('beton.caisse.entry') or 'Nouveau'
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
                raise UserError("Impossible de supprimer un encaissement approuvé.")
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

    @api.onchange('sale_order_id')
    def _onchange_sale_order_id(self):
        if self.sale_order_id:
            self.client_id = self.sale_order_id.partner_id
            self.amount = self.sale_order_id.amount_total
            self.description = self.sale_order_id.name

    def action_approve(self):
        for rec in self:
            if rec.state == 'draft':
                effective_amount = rec.amount_paid if rec.sale_order_id else rec.amount
                rec.cashbox_id.sudo().total_amount += effective_amount
                rec.state = 'approuve'
                # Mettre à jour la globale partenaire
                rec._update_globale()

    def action_to_draft(self):
        for rec in self:
            if rec.state == 'approuve':
                effective_amount = rec.amount_paid if rec.sale_order_id else rec.amount
                rec.cashbox_id.sudo().total_amount -= effective_amount
                rec.state = 'draft'
                if rec.payment_id:
                    rec.payment_id.sudo().unlink()
                    rec.payment_id = False

    def _update_globale(self):
        """Crée ou met à jour la dépense globale pour le client."""
        self.ensure_one()
        partner = self.client_id
        if not partner:
            return
        globale = self.env['beton.caisse.globale'].search([
            ('partner_id', '=', partner.id),
            ('partner_type', '=', 'client'),
        ], limit=1)
        if globale:
            if self.id not in globale.entry_ids.ids:
                globale.write({'entry_ids': [(4, self.id)]})
        else:
            self.env['beton.caisse.globale'].create({
                'partner_id': partner.id,
                'partner_type': 'client',
                'entry_ids': [(4, self.id)],
            })

    def action_preview_report(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': '/report/pdf/beton_caisse.report_beton_entry_template/%s' % self.id,
            'target': 'new',
        }

    def action_preview_report_multi(self):
        if not self:
            raise UserError("Veuillez sélectionner au moins un enregistrement.")
        ids_str = ','.join(str(r.id) for r in self)
        return {
            'type': 'ir.actions.act_url',
            'url': '/report/pdf/beton_caisse.report_beton_entry_template/%s' % ids_str,
            'target': 'new',
        }
