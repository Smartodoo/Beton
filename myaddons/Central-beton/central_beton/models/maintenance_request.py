# -*- coding: utf-8 -*-

from odoo import models, fields, api


class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    description_panne = fields.Text(string='Description de la Panne')
    action_realisee = fields.Text(string='Action Realisee')
    duree_arret = fields.Float(string='Duree d\'Arret (h)')
    cout_intervention = fields.Float(
        string='Cout Intervention',
        compute='_compute_cout_intervention', store=True)
    cout_main_oeuvre = fields.Float(string='Cout Main d\'Oeuvre')
    prochaine_echeance = fields.Date(
        string='Prochaine Echeance')
    type_intervention = fields.Selection([
        ('preventive', 'Preventive'),
        ('corrective', 'Corrective'),
        ('ameliorative', 'Ameliorative'),
    ], string='Type Intervention', default='corrective')
    priorite_beton = fields.Selection([
        ('basse', 'Basse'),
        ('normale', 'Normale'),
        ('haute', 'Haute'),
        ('urgente', 'Urgente'),
    ], string='Priorite', default='normale')
    centrale_id = fields.Many2one(
        'central.beton.centrale', string='Centrale',
        related='equipment_id.centrale_id', store=True, readonly=True)

    piece_ids = fields.One2many(
        'central.beton.intervention.piece', 'request_id',
        string='Pieces de Rechange')

    @api.depends('piece_ids.cout_total', 'cout_main_oeuvre')
    def _compute_cout_intervention(self):
        for rec in self:
            cout_pieces = sum(rec.piece_ids.mapped('cout_total'))
            rec.cout_intervention = cout_pieces + rec.cout_main_oeuvre
