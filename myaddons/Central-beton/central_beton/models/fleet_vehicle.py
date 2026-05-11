# -*- coding: utf-8 -*-

from odoo import models, fields, api


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    is_camion_malaxeur = fields.Boolean(
        string='Camion Malaxeur', default=False)
    capacite_m3 = fields.Float(string='Capacite (m3)')
    etat_camion = fields.Selection([
        ('disponible', 'Disponible'),
        ('en_livraison', 'En Livraison'),
        ('en_maintenance', 'En Maintenance'),
        ('hors_service', 'Hors Service'),
    ], string='Etat Camion', default='disponible', tracking=True)
    immatriculation = fields.Char(string='Immatriculation')
    date_derniere_vidange = fields.Date(
        string='Derniere Vidange')
    km_derniere_vidange = fields.Float(
        string='Km Derniere Vidange')
    prochaine_vidange_km = fields.Float(
        string='Prochaine Vidange (km)')
    centrale_id = fields.Many2one(
        'central.beton.centrale', string='Centrale')

    livraison_ids = fields.One2many(
        'central.beton.livraison', 'vehicule_id', string='Livraisons')
    livraison_count = fields.Integer(
        string='Nombre de Livraisons',
        compute='_compute_livraison_count')

    @api.depends('livraison_ids')
    def _compute_livraison_count(self):
        for vehicle in self:
            vehicle.livraison_count = len(vehicle.livraison_ids)

    def action_view_livraisons(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Livraisons',
            'res_model': 'central.beton.livraison',
            'view_mode': 'tree,form',
            'domain': [('vehicule_id', '=', self.id)],
        }

    def action_disponible(self):
        self.write({'etat_camion': 'disponible'})
        return True

    def action_maintenance(self):
        self.write({'etat_camion': 'en_maintenance'})
        return True

    def action_hors_service(self):
        self.write({'etat_camion': 'hors_service'})
        return True
