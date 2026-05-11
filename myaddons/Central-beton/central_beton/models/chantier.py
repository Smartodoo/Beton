# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CentralBetonChantier(models.Model):
    _name = 'central.beton.chantier'
    _description = 'Chantier'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(
        string='Reference', required=True, copy=False,
        readonly=True, default='Nouveau')
    designation = fields.Char(string='Designation', required=True)
    client_id = fields.Many2one(
        'res.partner', string='Client', required=True,
        domain="[('is_beton_client', '=', True)]", tracking=True)
    adresse = fields.Text(string='Adresse du Chantier')
    responsable_chantier = fields.Char(string='Responsable Chantier')
    telephone = fields.Char(string='Telephone')
    distance_km = fields.Float(string='Distance (km)')
    date_debut = fields.Date(string='Date de Debut')
    date_fin_prevue = fields.Date(string='Date de Fin Prevue')
    date_fin_reelle = fields.Date(string='Date de Fin Reelle')
    volume_commande = fields.Float(string='Volume Commande (m3)')
    latitude = fields.Float(string='Latitude', digits=(10, 7))
    longitude = fields.Float(string='Longitude', digits=(10, 7))
    notes = fields.Text(string='Notes')

    state = fields.Selection([
        ('nouveau', 'Nouveau'),
        ('en_cours', 'En Cours'),
        ('termine', 'Termine'),
        ('suspendu', 'Suspendu'),
    ], string='Etat', default='nouveau', tracking=True)

    livraison_ids = fields.One2many(
        'central.beton.livraison', 'chantier_id', string='Livraisons')
    commande_ids = fields.One2many(
        'sale.order', 'chantier_id', string='Commandes')
    production_ids = fields.One2many(
        'mrp.production', 'chantier_id', string='Ordres de Fabrication')

    volume_livre = fields.Float(
        string='Volume Livre (m3)',
        compute='_compute_volumes', store=True)
    volume_restant = fields.Float(
        string='Volume Restant (m3)',
        compute='_compute_volumes', store=True)
    taux_avancement = fields.Float(
        string='Taux d\'Avancement (%)',
        compute='_compute_volumes', store=True)
    livraison_count = fields.Integer(
        string='Nombre de Livraisons',
        compute='_compute_volumes', store=True)

    company_id = fields.Many2one(
        'res.company', string='Societe',
        default=lambda self: self.env.company)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nouveau') == 'Nouveau':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'central.beton.chantier') or 'Nouveau'
        return super().create(vals_list)

    @api.depends('livraison_ids', 'livraison_ids.volume', 'livraison_ids.state',
                 'volume_commande')
    def _compute_volumes(self):
        for rec in self:
            livraisons = rec.livraison_ids.filtered(
                lambda l: l.state == 'livre')
            rec.volume_livre = sum(livraisons.mapped('volume'))
            rec.volume_restant = max(
                rec.volume_commande - rec.volume_livre, 0)
            rec.taux_avancement = (
                (rec.volume_livre / rec.volume_commande * 100)
                if rec.volume_commande else 0.0)
            rec.livraison_count = len(livraisons)

    def action_start(self):
        self.write({'state': 'en_cours'})
        return True

    def action_done(self):
        self.write({
            'state': 'termine',
            'date_fin_reelle': fields.Date.today(),
        })
        return True

    def action_suspend(self):
        self.write({'state': 'suspendu'})
        return True

    def action_resume(self):
        self.write({'state': 'en_cours'})
        return True

    def action_view_livraisons(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Livraisons',
            'res_model': 'central.beton.livraison',
            'view_mode': 'tree,form',
            'domain': [('chantier_id', '=', self.id)],
            'context': {'default_chantier_id': self.id},
        }
