from odoo import models, fields, api
from odoo.exceptions import UserError


class BetonCashboxRechargeWizard(models.TransientModel):
    _name = 'beton.cashbox.recharge.wizard'
    _description = 'Assistant Recharge Caisse Béton'

    cashbox_id = fields.Many2one(
        'beton.cashbox',
        string='Caisse',
        required=True,
    )
    amount = fields.Float(string='Montant', required=True)
    note = fields.Text(string='Note')
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company,
    )
    user_id = fields.Many2one(
        'res.users',
        default=lambda self: self.env.user,
    )

    def action_confirm_recharge(self):
        self.ensure_one()
        if self.amount <= 0:
            raise UserError("Le montant doit être supérieur à zéro.")
        self.cashbox_id.sudo().total_amount += self.amount
        self.env['beton.cashbox.recharge'].create({
            'cashbox_id': self.cashbox_id.id,
            'amount': self.amount,
            'note': self.note,
            'user_id': self.user_id.id,
            'company_id': self.company_id.id,
        })
