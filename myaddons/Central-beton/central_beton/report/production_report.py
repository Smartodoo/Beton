# -*- coding: utf-8 -*-

from odoo import models, fields, tools


class CentralBetonReportProduction(models.Model):
    _name = 'central.beton.report.production'
    _description = 'Analyse Production Beton'
    _auto = False
    _order = 'date_fabrication desc'

    date_fabrication = fields.Date(string='Date', readonly=True)
    centrale_id = fields.Many2one(
        'central.beton.centrale', string='Centrale', readonly=True)
    bom_id = fields.Many2one(
        'mrp.bom', string='Formule', readonly=True)
    classe_resistance = fields.Selection([
        ('c20_25', 'C20/25'),
        ('c25_30', 'C25/30'),
        ('c30_37', 'C30/37'),
        ('c35_45', 'C35/45'),
        ('c40_50', 'C40/50'),
        ('c45_55', 'C45/55'),
        ('c50_60', 'C50/60'),
    ], string='Classe', readonly=True)
    operateur_id = fields.Many2one(
        'res.users', string='Operateur', readonly=True)
    chantier_id = fields.Many2one(
        'central.beton.chantier', string='Chantier', readonly=True)
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('confirmed', 'Confirme'),
        ('progress', 'En Cours'),
        ('to_close', 'A Cloturer'),
        ('done', 'Termine'),
        ('cancel', 'Annule'),
    ], string='Etat', readonly=True)
    volume_prevu = fields.Float(string='Volume Prevu', readonly=True)
    volume_produit = fields.Float(string='Volume Produit', readonly=True)
    cout_total = fields.Float(string='Cout Total', readonly=True)
    cout_m3 = fields.Float(string='Cout / m3', readonly=True)
    nb_fabrications = fields.Integer(string='Nb Fabrications', readonly=True)
    company_id = fields.Many2one(
        'res.company', string='Societe', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    p.id AS id,
                    p.date_start::date AS date_fabrication,
                    p.centrale_id AS centrale_id,
                    p.bom_id AS bom_id,
                    bom.classe_resistance AS classe_resistance,
                    p.user_id AS operateur_id,
                    p.chantier_id AS chantier_id,
                    p.state AS state,
                    p.product_qty AS volume_prevu,
                    p.volume_produit AS volume_produit,
                    p.cout_total AS cout_total,
                    p.cout_m3 AS cout_m3,
                    1 AS nb_fabrications,
                    p.company_id AS company_id
                FROM mrp_production p
                LEFT JOIN mrp_bom bom ON p.bom_id = bom.id
                WHERE bom.is_beton_bom = True
            )
        """ % self._table)
