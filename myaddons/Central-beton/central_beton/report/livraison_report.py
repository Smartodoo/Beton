# -*- coding: utf-8 -*-

from odoo import models, fields, tools


class CentralBetonReportLivraison(models.Model):
    _name = 'central.beton.report.livraison'
    _description = 'Analyse Livraisons Beton'
    _auto = False
    _order = 'date_chargement desc'

    date_chargement = fields.Date(string='Date', readonly=True)
    chantier_id = fields.Many2one(
        'central.beton.chantier', string='Chantier', readonly=True)
    client_id = fields.Many2one(
        'res.partner', string='Client', readonly=True)
    bom_id = fields.Many2one(
        'mrp.bom', string='Formule', readonly=True)
    vehicule_id = fields.Many2one(
        'fleet.vehicle', string='Vehicule', readonly=True)
    centrale_id = fields.Many2one(
        'central.beton.centrale', string='Centrale', readonly=True)
    state = fields.Selection([
        ('prevu', 'Prevu'),
        ('charge', 'Charge'),
        ('en_route', 'En Route'),
        ('sur_site', 'Sur Site'),
        ('livre', 'Livre'),
        ('annule', 'Annule'),
    ], string='Etat', readonly=True)
    volume = fields.Float(string='Volume (m3)', readonly=True)
    temps_trajet = fields.Float(string='Temps Trajet (min)', readonly=True)
    temps_sur_site = fields.Float(string='Temps sur Site (min)', readonly=True)
    temps_rotation = fields.Float(string='Temps Rotation (min)', readonly=True)
    pompe = fields.Boolean(string='Avec Pompe', readonly=True)
    nb_livraisons = fields.Integer(string='Nb Livraisons', readonly=True)
    company_id = fields.Many2one(
        'res.company', string='Societe', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    l.id AS id,
                    l.date_chargement::date AS date_chargement,
                    l.chantier_id AS chantier_id,
                    l.client_id AS client_id,
                    l.bom_id AS bom_id,
                    l.vehicule_id AS vehicule_id,
                    l.centrale_id AS centrale_id,
                    l.state AS state,
                    l.volume AS volume,
                    l.temps_trajet AS temps_trajet,
                    l.temps_sur_site AS temps_sur_site,
                    l.temps_rotation AS temps_rotation,
                    l.pompe AS pompe,
                    1 AS nb_livraisons,
                    l.company_id AS company_id
                FROM central_beton_livraison l
            )
        """ % self._table)
