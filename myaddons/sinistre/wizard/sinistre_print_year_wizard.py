from odoo import models, fields, api
from datetime import date
from odoo.exceptions import UserError


class SinistrePrintYearWizard(models.TransientModel):
    _name = 'sinistre.print.year.wizard'
    _description = 'Wizard Impression Sinistres par Année'

    # Champ de sélection des années existantes
    year = fields.Selection(
        selection=lambda self: self._get_existing_years(),
        string="Année",
        required=True,
    )

    @api.model
    def _get_existing_years(self):
        """Retourne la liste des années trouvées dans les enregistrements de sinistres"""
        query = """
            SELECT DISTINCT EXTRACT(YEAR FROM date_accident) AS year
            FROM sinistre
            WHERE date_accident IS NOT NULL
            ORDER BY year DESC
        """
        self.env.cr.execute(query)
        results = self.env.cr.fetchall()
        years = [(str(int(r[0])), str(int(r[0]))) for r in results if r[0]]
        return years

    def print_report_year(self):
        """Méthode d'impression du rapport par année"""
        selected_year = int(self.year)
        date_from = date(selected_year, 1, 1)
        date_to = date(selected_year + 1, 1, 1)

        sinistres = self.env['sinistre'].search([
            ('date_accident', '>=', date_from),
            ('date_accident', '<', date_to)
        ])

        if not sinistres:
            raise UserError("Aucun sinistre trouvé pour l'année sélectionnée.")

        ctx = {
            'report_year': selected_year,
            'report_date_from': str(date_from),
            'report_date_to': str(date_to),
        }

        return self.env.ref('sinistre.action_report_sinistre_by_year') \
            .with_context(ctx) \
            .report_action(sinistres)
