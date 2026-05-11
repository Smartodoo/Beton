from odoo import models, fields, api
from odoo.exceptions import UserError


class BetonDateFilterWizard(models.TransientModel):
    _name = 'beton.date.filter.wizard'
    _description = 'Filtrer par Période (Caisse Béton)'

    date_from = fields.Date(string='De', required=True)
    date_to = fields.Date(string='Au', required=True)
    model_name = fields.Char(string='Modèle', required=True)
    date_field = fields.Char(string='Champ Date', default='date')

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for wizard in self:
            if wizard.date_from > wizard.date_to:
                raise UserError("La date 'De' doit être inférieure ou égale à la date 'Au'.")

    def action_apply_filter(self):
        self.ensure_one()
        domain = [
            (self.date_field, '>=', self.date_from),
            (self.date_field, '<=', self.date_to),
        ]
        return {
            'name': 'Résultats du %s au %s' % (
                self.date_from.strftime("%d/%m/%Y"),
                self.date_to.strftime("%d/%m/%Y"),
            ),
            'type': 'ir.actions.act_window',
            'res_model': self.model_name,
            'view_mode': 'tree,form',
            'domain': domain,
            'context': dict(self.env.context, create=False),
        }
