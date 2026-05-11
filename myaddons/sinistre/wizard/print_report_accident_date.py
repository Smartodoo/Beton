from odoo import models, fields
from datetime import date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError


class SinistrePrintWizard(models.TransientModel):
    _name = 'sinistre.print.wizard'
    _description = 'Wizard Impression Sinistres par Mois'

    month = fields.Selection([
        ('1', 'Janvier'), ('2', 'Février'), ('3', 'Mars'), ('4', 'Avril'),
        ('5', 'Mai'), ('6', 'Juin'), ('7', 'Juillet'), ('8', 'Août'),
        ('9', 'Septembre'), ('10', 'Octobre'), ('11', 'Novembre'), ('12', 'Décembre')
    ], string="Mois", required=True)

    year = fields.Integer(string="Année", required=True, default=date.today().year)

    def print_report(self):
        month_int = int(self.month)
        date_from = date(self.year, month_int, 1)
        date_to = date_from + relativedelta(months=1)
        sinistres = self.env['sinistre'].search([
            ('date_accident', '>=', date_from),
            ('date_accident', '<', date_to)
        ])
        if not sinistres:
            raise UserError("Aucun sinistre trouvé pour la date sélectionné.")

        month_name = dict(self._fields['month'].selection)[self.month]

        ctx = {
            'report_month_name': month_name,
            'report_year': self.year,
            'report_date_from': str(date_from),
            'report_date_to': str(date_to),
        }

        # On passe par le context (fiable) :
        return self.env.ref('sinistre.action_report_sinistre_by_month') \
            .with_context(ctx) \
            .report_action(sinistres)
