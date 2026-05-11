from odoo import models, fields, api, _
from odoo.exceptions import UserError

MSG_LECTURE_SEULE = _("Accès refusé : vous avez uniquement un accès en lecture sur les caisses béton.")


class BetonCaisseTransfer(models.Model):
    _name = 'beton.caisse.transfer'
    _description = 'Transfert entre Caisses Béton'
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
    source_cashbox_id = fields.Many2one(
        'beton.cashbox',
        string='Caisse source',
        required=True,
        domain="[('type', '=', 'principale')]",
        tracking=True,
    )
    destination_cashbox_id = fields.Many2one(
        'beton.cashbox',
        string='Caisse destination',
        required=True,
        domain="[('type', '=', 'secondaire')]",
        tracking=True,
    )
    total_amount_source = fields.Monetary(
        related='source_cashbox_id.total_amount',
        string='Solde source',
        currency_field='company_currency_id',
    )
    total_amount_destination = fields.Monetary(
        related='destination_cashbox_id.total_amount',
        string='Solde destination',
        currency_field='company_currency_id',
    )
    amount = fields.Monetary(
        string='Montant',
        required=True,
        currency_field='company_currency_id',
        tracking=True,
    )
    description = fields.Text(
        string='Description',
        compute='_compute_description',
        store=True,
        readonly=False,
    )
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('confirmed', 'Confirmé'),
        ('cancel', 'Annulé'),
    ], string='État', default='draft', tracking=True)

    user_id = fields.Many2one(
        'res.users',
        string='Comptable',
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

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.user.has_group('beton_caisse.group_beton_caisse_lecture_seule'):
            raise UserError(MSG_LECTURE_SEULE)
        for vals in vals_list:
            if vals.get('name', 'Nouveau') == 'Nouveau':
                vals['name'] = self.env['ir.sequence'].next_by_code('beton.caisse.transfer') or 'Nouveau'
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
                raise UserError("Impossible de supprimer un transfert confirmé ou annulé.")
        return super().unlink()

    @api.depends('source_cashbox_id', 'destination_cashbox_id', 'amount')
    def _compute_description(self):
        for rec in self:
            if rec.source_cashbox_id and rec.destination_cashbox_id:
                rec.description = "Transfert de %s vers %s" % (
                    rec.source_cashbox_id.name,
                    rec.destination_cashbox_id.name,
                )
            else:
                rec.description = ''

    def action_confirm(self):
        for rec in self:
            if rec.state != 'draft':
                continue
            if rec.source_cashbox_id == rec.destination_cashbox_id:
                raise UserError("La caisse source et destination doivent être différentes.")
            if rec.amount <= 0:
                raise UserError("Le montant doit être supérieur à zéro.")
            if rec.source_cashbox_id.total_amount < rec.amount:
                raise UserError(
                    "Solde insuffisant dans '%s'. Solde : %s"
                    % (rec.source_cashbox_id.name, rec.source_cashbox_id.total_amount)
                )
            rec.source_cashbox_id.sudo().total_amount -= rec.amount
            rec.destination_cashbox_id.sudo().total_amount += rec.amount
            rec.state = 'confirmed'

    def action_cancel(self):
        for rec in self:
            if rec.state == 'confirmed':
                rec.source_cashbox_id.sudo().total_amount += rec.amount
                rec.destination_cashbox_id.sudo().total_amount -= rec.amount
                rec.state = 'cancel'

    def action_to_draft(self):
        for rec in self:
            if rec.state == 'cancel':
                rec.state = 'draft'
            elif rec.state == 'confirmed':
                rec.source_cashbox_id.sudo().total_amount += rec.amount
                rec.destination_cashbox_id.sudo().total_amount -= rec.amount
                rec.state = 'draft'

    def action_preview_report(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': '/report/pdf/beton_caisse.report_beton_transfer_template/%s' % self.id,
            'target': 'new',
        }
