from odoo import models, fields, api, _
from odoo.exceptions import UserError

MSG_LECTURE_SEULE = _("Accès refusé : vous avez uniquement un accès en lecture sur les caisses béton.")


class BetonCashboxRecharge(models.Model):
    _name = 'beton.cashbox.recharge'
    _description = 'Recharge Caisse Béton'
    _order = 'date desc, id desc'
    _rec_name = 'cashbox_id'

    cashbox_id = fields.Many2one(
        'beton.cashbox',
        string='Caisse',
        required=True,
        tracking=True,
    )
    date = fields.Datetime(
        string='Date',
        default=fields.Datetime.now,
        readonly=True,
    )
    amount = fields.Monetary(
        string='Montant',
        required=True,
        currency_field='company_currency_id',
    )
    note = fields.Text(string='Note')
    user_id = fields.Many2one(
        'res.users',
        string='Utilisateur',
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

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.user.has_group('beton_caisse.group_beton_caisse_lecture_seule'):
            raise UserError(MSG_LECTURE_SEULE)
        return super().create(vals_list)

    def action_preview_report(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': '/report/pdf/beton_caisse.report_beton_recharge_template/%s' % self.id,
            'target': 'new',
        }
