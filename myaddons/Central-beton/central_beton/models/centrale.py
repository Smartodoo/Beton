# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CentralBetonCentrale(models.Model):
    _name = 'central.beton.centrale'
    _description = 'Centrale a Beton'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nom', required=True, tracking=True)
    code = fields.Char(string='Code', required=True)
    adresse = fields.Text(string='Adresse')
    responsable_id = fields.Many2one('res.users', string='Responsable', tracking=True)
    capacite_horaire = fields.Float(string='Capacite Horaire (m3/h)', default=60.0)
    date_mise_service = fields.Date(string='Date de Mise en Service')
    active = fields.Boolean(string='Actif', default=True)
    state = fields.Selection([
        ('operationnelle', 'Operationnelle'),
        ('maintenance', 'En Maintenance'),
        ('arret', 'A l\'Arret'),
    ], string='Etat', default='operationnelle', tracking=True)

    equipement_ids = fields.One2many(
        'maintenance.equipment', 'centrale_id', string='Equipements')
    production_ids = fields.One2many(
        'mrp.production', 'centrale_id', string='Ordres de Fabrication')

    production_count = fields.Integer(
        string='Nombre de Fabrications', compute='_compute_production_count')

    company_id = fields.Many2one(
        'res.company', string='Societe',
        default=lambda self: self.env.company)

    @api.depends('production_ids')
    def _compute_production_count(self):
        for rec in self:
            rec.production_count = len(rec.production_ids)

    def action_set_maintenance(self):
        self.write({'state': 'maintenance'})
        return True

    def action_set_operationnelle(self):
        self.write({'state': 'operationnelle'})
        return True

    def action_set_arret(self):
        self.write({'state': 'arret'})
        return True

    def action_view_productions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Ordres de Fabrication',
            'res_model': 'mrp.production',
            'view_mode': 'tree,form',
            'domain': [('centrale_id', '=', self.id)],
            'context': {'default_centrale_id': self.id},
        }
