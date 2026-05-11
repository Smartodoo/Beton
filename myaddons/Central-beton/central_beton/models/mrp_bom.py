# -*- coding: utf-8 -*-

from odoo import models, fields, api


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    is_beton_bom = fields.Boolean(string='Formule Beton', default=False)
    classe_resistance = fields.Selection([
        ('c20_25', 'C20/25'),
        ('c25_30', 'C25/30'),
        ('c30_37', 'C30/37'),
        ('c35_45', 'C35/45'),
        ('c40_50', 'C40/50'),
        ('c45_55', 'C45/55'),
        ('c50_60', 'C50/60'),
    ], string='Classe de Resistance', tracking=True)
    consistance = fields.Selection([
        ('s1', 'S1 - Ferme'),
        ('s2', 'S2 - Plastique'),
        ('s3', 'S3 - Tres Plastique'),
        ('s4', 'S4 - Fluide'),
        ('s5', 'S5 - Tres Fluide'),
    ], string='Consistance', default='s3')
    exposition = fields.Selection([
        ('x0', 'X0 - Aucun risque'),
        ('xc1', 'XC1 - Sec'),
        ('xc2', 'XC2 - Humide'),
        ('xc3', 'XC3 - Humidite moderee'),
        ('xc4', 'XC4 - Alternance'),
        ('xf1', 'XF1 - Gel modere'),
    ], string="Classe d'Exposition", default='xc1')
    dmax = fields.Float(string='Dmax (mm)', default=25.0,
                        help='Diametre maximal des granulats')

    cout_theorique_m3 = fields.Float(
        string='Cout Theorique / m3',
        compute='_compute_cout_theorique', store=True)
    rapport_eau_ciment = fields.Float(
        string='Rapport E/C',
        compute='_compute_rapport_eau_ciment', store=True)
    masse_totale = fields.Float(
        string='Masse Totale (kg/m3)',
        compute='_compute_masse_totale', store=True)

    @api.depends('bom_line_ids.cout_ligne')
    def _compute_cout_theorique(self):
        for rec in self:
            if rec.is_beton_bom:
                rec.cout_theorique_m3 = sum(rec.bom_line_ids.mapped('cout_ligne'))
            else:
                rec.cout_theorique_m3 = 0.0

    @api.depends('bom_line_ids.product_qty', 'bom_line_ids.product_id')
    def _compute_rapport_eau_ciment(self):
        for rec in self:
            if rec.is_beton_bom:
                eau = sum(l.product_qty for l in rec.bom_line_ids
                          if l.product_id.type_matiere_beton == 'eau')
                ciment = sum(l.product_qty for l in rec.bom_line_ids
                             if l.product_id.type_matiere_beton == 'ciment')
                rec.rapport_eau_ciment = eau / ciment if ciment else 0.0
            else:
                rec.rapport_eau_ciment = 0.0

    @api.depends('bom_line_ids.product_qty')
    def _compute_masse_totale(self):
        for rec in self:
            if rec.is_beton_bom:
                rec.masse_totale = sum(rec.bom_line_ids.mapped('product_qty'))
            else:
                rec.masse_totale = 0.0


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    prix_unitaire = fields.Float(
        string='Prix Unitaire', related='product_id.standard_price', readonly=True)
    cout_ligne = fields.Float(
        string='Cout Ligne', compute='_compute_cout_ligne', store=True)

    @api.depends('product_qty', 'prix_unitaire')
    def _compute_cout_ligne(self):
        for rec in self:
            rec.cout_ligne = rec.product_qty * rec.prix_unitaire
