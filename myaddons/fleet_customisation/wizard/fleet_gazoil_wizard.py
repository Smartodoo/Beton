# -*- coding: utf-8 -*-
from odoo import fields, models


class FleetGazoilWizard(models.TransientModel):
    _name = 'fleet.gazoil.wizard'
    _description = 'Rapport Consommation Gazoil - Periode'

    date_debut = fields.Date(string="Date de debut", required=True)
    date_fin = fields.Date(
        string="Date de fin",
        required=True,
        default=fields.Date.today,
    )
    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string="Conducteur (optionnel)",
        domain=[('role_employe', '=', 'chauffeur')],
    )

    def action_generate_report(self):
        self.ensure_one()
        domain = [
            ('date', '>=', self.date_debut),
            ('date', '<=', self.date_fin),
        ]
        if self.employee_id:
            domain.append(('employee_id', '=', self.employee_id.id))

        records = self.env['fleet.gazoil'].search(domain, order='date asc')

        data = {
            'date_debut': self.date_debut.strftime('%d/%m/%Y') if self.date_debut else '',
            'date_fin': self.date_fin.strftime('%d/%m/%Y') if self.date_fin else '',
        }

        return self.env.ref('fleet_customisation.action_report_gazoil').report_action(
            records, data=data
        )
