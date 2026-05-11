# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class CentralBetonLivraison(models.Model):
    _name = 'central.beton.livraison'
    _description = 'Livraison Beton'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_chargement desc, id desc'

    name = fields.Char(
        string='Numero BL', required=True, copy=False,
        readonly=True, default='Nouveau')
    production_id = fields.Many2one(
        'mrp.production', string='Ordre de Fabrication', tracking=True)
    chantier_id = fields.Many2one(
        'central.beton.chantier', string='Chantier',
        required=True, tracking=True)
    client_id = fields.Many2one(
        'res.partner', string='Client',
        related='chantier_id.client_id', store=True, readonly=True)
    bom_id = fields.Many2one(
        'mrp.bom', string='Formule', tracking=True,
        domain="[('is_beton_bom', '=', True)]")
    vehicule_id = fields.Many2one(
        'fleet.vehicle', string='Camion Malaxeur',
        domain="[('is_camion_malaxeur', '=', True)]", tracking=True)
    chauffeur_id = fields.Many2one(
        'res.partner', string='Chauffeur',
        related='vehicule_id.driver_id', readonly=True)
    centrale_id = fields.Many2one(
        'central.beton.centrale', string='Centrale')

    volume = fields.Float(string='Volume (m3)', required=True, tracking=True)
    date_chargement = fields.Datetime(
        string='Date/Heure Chargement', default=fields.Datetime.now)
    date_depart = fields.Datetime(string='Date/Heure Depart')
    date_arrivee = fields.Datetime(string='Date/Heure Arrivee')
    date_debut_dechargement = fields.Datetime(
        string='Debut Dechargement')
    date_fin_dechargement = fields.Datetime(
        string='Fin Dechargement')
    date_retour = fields.Datetime(string='Date/Heure Retour')

    temps_trajet = fields.Float(
        string='Temps Trajet (min)',
        compute='_compute_temps_trajet', store=True)
    temps_sur_site = fields.Float(
        string='Temps sur Site (min)',
        compute='_compute_temps_sur_site', store=True)
    temps_rotation = fields.Float(
        string='Temps Rotation Total (min)',
        compute='_compute_temps_rotation', store=True)

    ticket_pesee = fields.Float(string='Ticket Pesee (kg)')
    affaissement = fields.Float(string='Affaissement (cm)')
    temperature = fields.Float(string='Temperature (C)')
    eau_ajoutee = fields.Float(string='Eau Ajoutee (L)')
    pompe = fields.Boolean(string='Avec Pompe', default=False)

    notes = fields.Text(string='Notes')
    commande_id = fields.Many2one(
        'sale.order', string='Commande Client')

    state = fields.Selection([
        ('prevu', 'Prevu'),
        ('charge', 'Charge'),
        ('en_route', 'En Route'),
        ('sur_site', 'Sur Site'),
        ('livre', 'Livre'),
        ('annule', 'Annule'),
    ], string='Etat', default='prevu', tracking=True)

    company_id = fields.Many2one(
        'res.company', string='Societe',
        default=lambda self: self.env.company)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nouveau') == 'Nouveau':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'central.beton.livraison') or 'Nouveau'
        return super().create(vals_list)

    @api.depends('date_depart', 'date_arrivee')
    def _compute_temps_trajet(self):
        for rec in self:
            if rec.date_depart and rec.date_arrivee:
                delta = rec.date_arrivee - rec.date_depart
                rec.temps_trajet = delta.total_seconds() / 60.0
            else:
                rec.temps_trajet = 0.0

    @api.depends('date_arrivee', 'date_fin_dechargement')
    def _compute_temps_sur_site(self):
        for rec in self:
            if rec.date_arrivee and rec.date_fin_dechargement:
                delta = rec.date_fin_dechargement - rec.date_arrivee
                rec.temps_sur_site = delta.total_seconds() / 60.0
            else:
                rec.temps_sur_site = 0.0

    @api.depends('date_chargement', 'date_retour')
    def _compute_temps_rotation(self):
        for rec in self:
            if rec.date_chargement and rec.date_retour:
                delta = rec.date_retour - rec.date_chargement
                rec.temps_rotation = delta.total_seconds() / 60.0
            else:
                rec.temps_rotation = 0.0

    def action_charger(self):
        for rec in self:
            if rec.state != 'prevu':
                raise UserError('Seules les livraisons prevues peuvent etre chargees.')
            rec.write({
                'state': 'charge',
                'date_chargement': fields.Datetime.now(),
            })
        return True

    def action_depart(self):
        for rec in self:
            if rec.state != 'charge':
                raise UserError('Le camion doit etre charge avant le depart.')
            if rec.vehicule_id:
                rec.vehicule_id.write({'etat_camion': 'en_livraison'})
            rec.write({
                'state': 'en_route',
                'date_depart': fields.Datetime.now(),
            })
        return True

    def action_arrivee(self):
        for rec in self:
            if rec.state != 'en_route':
                raise UserError('Le camion doit etre en route.')
            rec.write({
                'state': 'sur_site',
                'date_arrivee': fields.Datetime.now(),
            })
        return True

    def action_livrer(self):
        for rec in self:
            if rec.state != 'sur_site':
                raise UserError('Le camion doit etre sur site.')
            if rec.vehicule_id:
                rec.vehicule_id.write({'etat_camion': 'disponible'})
            rec.write({
                'state': 'livre',
                'date_fin_dechargement': fields.Datetime.now(),
                'date_retour': fields.Datetime.now(),
            })
        return True

    def action_cancel(self):
        for rec in self:
            if rec.state == 'livre':
                raise UserError('Une livraison effectuee ne peut pas etre annulee.')
            if rec.vehicule_id and rec.state in ('en_route', 'sur_site'):
                rec.vehicule_id.write({'etat_camion': 'disponible'})
            rec.write({'state': 'annule'})
        return True
