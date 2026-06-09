# -*- coding: utf-8 -*-
import logging
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class FleetGazoilWizard(models.TransientModel):
    _name = 'fleet.gazoil.wizard'
    _description = 'Impression consommation gazoil par periode'

    date_debut = fields.Date(
        string="Date de debut",
        required=True,
        default=lambda self: fields.Date.today().replace(day=1),
    )
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

    @api.model
    def default_get(self, fields_list):
        """Si ouvert depuis des lignes selectionnees, cadrer la periode dessus."""
        res = super().default_get(fields_list)
        ctx = self.env.context
        if ctx.get('active_model') == 'fleet.gazoil' and ctx.get('active_ids'):
            dates = self.env['fleet.gazoil'].browse(ctx['active_ids']).exists().mapped('date')
            if dates:
                res['date_debut'] = min(dates)
                res['date_fin'] = max(dates)
        return res

    def action_generate_report(self):
        self.ensure_one()
        if self.date_debut > self.date_fin:
            raise UserError("La date de debut doit etre anterieure ou egale a la date de fin.")

        domain = [
            ('date', '>=', self.date_debut),
            ('date', '<=', self.date_fin),
        ]
        if self.employee_id:
            domain.append(('employee_id', '=', self.employee_id.id))

        records = self.env['fleet.gazoil'].search(domain, order='date asc')
        _logger.warning(
            "=== GAZOIL WIZARD DIAG === user=%s company=%s date_debut=%s date_fin=%s "
            "domain=%s -> %s records ids=%s | total fleet.gazoil visibles=%s",
            self.env.user.login, self.env.company.name,
            self.date_debut, self.date_fin, domain,
            len(records), records.ids,
            self.env['fleet.gazoil'].search_count([]),
        )
        if not records:
            raise UserError("Aucune consommation trouvee pour cette periode.")

        data = {
            'date_debut': self.date_debut.strftime('%d/%m/%Y'),
            'date_fin': self.date_fin.strftime('%d/%m/%Y'),
        }
        return self.env.ref('fleet_customisation.action_report_gazoil').report_action(
            records, data=data
        )
