# -*- coding: utf-8 -*-

from odoo import models, fields


class WizardProductionReport(models.TransientModel):
    _name = 'central.beton.wizard.production.report'
    _description = 'Assistant Rapport Production'

    date_debut = fields.Date(string='Date Debut', required=True)
    date_fin = fields.Date(string='Date Fin', required=True)
    centrale_id = fields.Many2one(
        'central.beton.centrale', string='Centrale')
    bom_id = fields.Many2one(
        'mrp.bom', string='Formule',
        domain="[('is_beton_bom', '=', True)]")
    state = fields.Selection([
        ('all', 'Toutes'),
        ('done', 'Terminees'),
        ('progress', 'En Cours'),
    ], string='Etat', default='all')

    def action_view_report(self):
        self.ensure_one()
        domain = [
            ('date_fabrication', '>=', self.date_debut),
            ('date_fabrication', '<=', self.date_fin),
        ]
        if self.centrale_id:
            domain.append(('centrale_id', '=', self.centrale_id.id))
        if self.bom_id:
            domain.append(('bom_id', '=', self.bom_id.id))
        if self.state != 'all':
            domain.append(('state', '=', self.state))

        return {
            'type': 'ir.actions.act_window',
            'name': 'Rapport Production',
            'res_model': 'central.beton.report.production',
            'view_mode': 'pivot,graph,tree',
            'domain': domain,
        }
