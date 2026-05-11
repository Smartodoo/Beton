# -*- coding: utf-8 -*-

from odoo import models, fields, api


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    is_beton_production = fields.Boolean(
        string='Production Beton',
        compute='_compute_is_beton_production', store=True)
    centrale_id = fields.Many2one(
        'central.beton.centrale', string='Centrale', tracking=True,
        domain="[('state', '=', 'operationnelle')]")
    chantier_id = fields.Many2one(
        'central.beton.chantier', string='Chantier')
    commande_id = fields.Many2one(
        'sale.order', string='Commande Client')
    bon_livraison_id = fields.Many2one(
        'central.beton.livraison', string='Bon de Livraison')
    numero_gachee = fields.Char(string='Numero de Gachee')
    temperature_beton = fields.Float(string='Temperature Beton (C)')
    affaissement = fields.Float(string='Affaissement (cm)')
    volume_produit = fields.Float(string='Volume Produit (m3)', tracking=True)

    cout_total = fields.Float(
        string='Cout Total', compute='_compute_cout_total', store=True)
    cout_m3 = fields.Float(
        string='Cout / m3', compute='_compute_cout_total', store=True)

    @api.depends('bom_id', 'bom_id.is_beton_bom')
    def _compute_is_beton_production(self):
        for rec in self:
            rec.is_beton_production = rec.bom_id.is_beton_bom if rec.bom_id else False

    @api.depends('move_raw_ids.product_id.standard_price',
                 'move_raw_ids.quantity', 'volume_produit')
    def _compute_cout_total(self):
        for rec in self:
            total = 0.0
            for move in rec.move_raw_ids:
                total += move.quantity * move.product_id.standard_price
            rec.cout_total = total
            rec.cout_m3 = total / rec.volume_produit if rec.volume_produit else 0.0
