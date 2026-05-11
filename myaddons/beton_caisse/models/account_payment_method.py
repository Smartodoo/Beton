from odoo import models, api


class AccountPaymentMethod(models.Model):
    _inherit = 'account.payment.method'

    @api.model
    def _get_payment_method_information(self):
        res = super()._get_payment_method_information()
        res['beton_cheque'] = {'mode': 'multi', 'type': ('bank',)}
        res['beton_virement'] = {'mode': 'multi', 'type': ('bank',)}
        res['beton_carte'] = {'mode': 'multi', 'type': ('bank',)}
        res['beton_especes'] = {'mode': 'multi', 'type': ('cash',)}
        return res
