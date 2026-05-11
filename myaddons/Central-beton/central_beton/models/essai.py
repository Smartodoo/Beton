# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CentralBetonEssai(models.Model):
    _name = 'central.beton.essai'
    _description = 'Essai Beton'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_prelevement desc, id desc'

    name = fields.Char(
        string='Reference', required=True, copy=False,
        readonly=True, default='Nouveau')
    production_id = fields.Many2one(
        'mrp.production', string='Ordre de Fabrication', tracking=True)
    bom_id = fields.Many2one(
        'mrp.bom', string='Formule',
        related='production_id.bom_id', store=True, readonly=True)
    chantier_id = fields.Many2one(
        'central.beton.chantier', string='Chantier')
    date_prelevement = fields.Date(
        string='Date de Prelevement', required=True,
        default=fields.Date.today)
    laborantin_id = fields.Many2one(
        'res.users', string='Laborantin',
        default=lambda self: self.env.user)

    # Resultats d'essais
    affaissement = fields.Float(string='Affaissement (cm)')
    temperature = fields.Float(string='Temperature (C)')
    teneur_air = fields.Float(string='Teneur en Air (%)')
    masse_volumique = fields.Float(string='Masse Volumique (kg/m3)')

    # Resistances
    resistance_7j = fields.Float(string='Resistance 7 jours (MPa)')
    resistance_14j = fields.Float(string='Resistance 14 jours (MPa)')
    resistance_21j = fields.Float(string='Resistance 21 jours (MPa)')
    resistance_28j = fields.Float(string='Resistance 28 jours (MPa)')

    # Conformite
    classe_resistance = fields.Selection(
        related='bom_id.classe_resistance', readonly=True)
    resistance_minimale = fields.Float(
        string='Resistance Minimale (MPa)',
        compute='_compute_resistance_minimale', store=True)
    conforme = fields.Selection([
        ('en_attente', 'En Attente'),
        ('conforme', 'Conforme'),
        ('non_conforme', 'Non Conforme'),
    ], string='Conformite', default='en_attente',
       compute='_compute_conformite', store=True, tracking=True)

    non_conformite_id = fields.Many2one(
        'central.beton.non.conformite', string='Non-Conformite',
        readonly=True)
    notes = fields.Text(string='Notes')

    state = fields.Selection([
        ('brouillon', 'Brouillon'),
        ('en_cours', 'En Cours'),
        ('termine', 'Termine'),
    ], string='Etat', default='brouillon', tracking=True)

    company_id = fields.Many2one(
        'res.company', string='Societe',
        default=lambda self: self.env.company)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nouveau') == 'Nouveau':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'central.beton.essai') or 'Nouveau'
        return super().create(vals_list)

    RESISTANCE_MAP = {
        'c20_25': 20.0,
        'c25_30': 25.0,
        'c30_37': 30.0,
        'c35_45': 35.0,
        'c40_50': 40.0,
        'c45_55': 45.0,
        'c50_60': 50.0,
    }

    @api.depends('classe_resistance')
    def _compute_resistance_minimale(self):
        for rec in self:
            rec.resistance_minimale = self.RESISTANCE_MAP.get(
                rec.classe_resistance, 0.0)

    @api.depends('resistance_28j', 'resistance_minimale')
    def _compute_conformite(self):
        for rec in self:
            if not rec.resistance_28j:
                rec.conforme = 'en_attente'
            elif rec.resistance_28j >= rec.resistance_minimale:
                rec.conforme = 'conforme'
            else:
                rec.conforme = 'non_conforme'

    def action_start(self):
        self.write({'state': 'en_cours'})
        return True

    def action_done(self):
        self.write({'state': 'termine'})
        return True

    def action_create_non_conformite(self):
        """Create a non-conformity from a failed test."""
        self.ensure_one()
        if self.non_conformite_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'central.beton.non.conformite',
                'res_id': self.non_conformite_id.id,
                'view_mode': 'form',
            }
        nc = self.env['central.beton.non.conformite'].create({
            'essai_id': self.id,
            'production_id': self.production_id.id,
            'chantier_id': self.chantier_id.id,
            'type_nc': 'resistance',
            'gravite': 'majeure' if self.resistance_28j < self.resistance_minimale * 0.8 else 'mineure',
            'description': (
                'Resistance 28j insuffisante: %.1f MPa '
                '(minimum requis: %.1f MPa pour %s)'
            ) % (
                self.resistance_28j,
                self.resistance_minimale,
                self.bom_id.display_name or '',
            ),
        })
        self.non_conformite_id = nc.id
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'central.beton.non.conformite',
            'res_id': nc.id,
            'view_mode': 'form',
        }
