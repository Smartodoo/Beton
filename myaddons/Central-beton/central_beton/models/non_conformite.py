# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CentralBetonNonConformite(models.Model):
    _name = 'central.beton.non.conformite'
    _description = 'Non-Conformite'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_detection desc, id desc'

    name = fields.Char(
        string='Reference', required=True, copy=False,
        readonly=True, default='Nouveau')
    date_detection = fields.Date(
        string='Date de Detection', default=fields.Date.today, required=True)
    detecte_par_id = fields.Many2one(
        'res.users', string='Detecte Par',
        default=lambda self: self.env.user)

    essai_id = fields.Many2one(
        'central.beton.essai', string='Essai')
    production_id = fields.Many2one(
        'mrp.production', string='Ordre de Fabrication')
    chantier_id = fields.Many2one(
        'central.beton.chantier', string='Chantier')

    type_nc = fields.Selection([
        ('resistance', 'Resistance Insuffisante'),
        ('consistance', 'Consistance Hors Norme'),
        ('aspect', 'Defaut d\'Aspect'),
        ('dosage', 'Erreur de Dosage'),
        ('temperature', 'Temperature Hors Norme'),
        ('autre', 'Autre'),
    ], string='Type', required=True, tracking=True)

    gravite = fields.Selection([
        ('mineure', 'Mineure'),
        ('majeure', 'Majeure'),
        ('critique', 'Critique'),
    ], string='Gravite', required=True, tracking=True)

    description = fields.Text(string='Description', required=True)
    cause_analyse = fields.Text(string='Analyse des Causes')
    action_immediate = fields.Text(string='Action Immediate')
    action_corrective = fields.Text(string='Action Corrective')
    date_cloture = fields.Date(string='Date de Cloture')
    responsable_id = fields.Many2one(
        'res.users', string='Responsable Traitement')

    state = fields.Selection([
        ('ouverte', 'Ouverte'),
        ('en_traitement', 'En Traitement'),
        ('cloturee', 'Cloturee'),
    ], string='Etat', default='ouverte', tracking=True)

    company_id = fields.Many2one(
        'res.company', string='Societe',
        default=lambda self: self.env.company)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nouveau') == 'Nouveau':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'central.beton.non.conformite') or 'Nouveau'
        return super().create(vals_list)

    def action_traiter(self):
        self.write({'state': 'en_traitement'})
        return True

    def action_cloturer(self):
        self.write({
            'state': 'cloturee',
            'date_cloture': fields.Date.today(),
        })
        return True

    def action_rouvrir(self):
        self.write({
            'state': 'ouverte',
            'date_cloture': False,
        })
        return True
