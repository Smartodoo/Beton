from odoo import models, fields, api


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    bank_name = fields.Char(string='Nom de la banque', help="Nom de la banque")
    bank_check_number = fields.Char(string='Numéro de chèque', help="Numéro de chèque")
    virement_ref = fields.Char(string='Référence de virement', help="Référence de virement")

    show_check_number = fields.Boolean(compute='_compute_show_fields')
    show_virement_ref = fields.Boolean(compute='_compute_show_fields')

    @api.depends('payment_method_line_id.code')
    def _compute_show_fields(self):
        for rec in self:
            code = rec.payment_method_line_id.code
            rec.show_check_number = code == 'Chèque'
            rec.show_virement_ref = code == 'VI'  # code de virement

    def _create_payment_vals_from_wizard(self, batch_result):
        res = super(AccountPaymentRegister, self)._create_payment_vals_from_wizard(batch_result)
        res.update({
            'bank_name': self.bank_name,
            'bank_check_number': self.bank_check_number,
            'virement_ref': self.virement_ref,
        })
        return res


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    bank_name = fields.Char(string='Nom de la banque', help="Nom de la banque")
    bank_check_number = fields.Char(string='Numéro de chèque', help="Numéro de chèque")
    virement_ref = fields.Char(string='Référence de virement', help="Référence de virement")

    show_check_number = fields.Boolean(compute='_compute_show_fields')
    show_virement_ref = fields.Boolean(compute='_compute_show_fields')

    @api.depends('payment_method_line_id.code')
    def _compute_show_fields(self):
        for rec in self:
            code = rec.payment_method_line_id.code
            rec.show_check_number = code == 'Chèque'
            rec.show_virement_ref = code == 'VI'  # code de virement
