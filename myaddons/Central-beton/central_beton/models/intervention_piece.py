# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CentralBetonInterventionPiece(models.Model):
    _name = 'central.beton.intervention.piece'
    _description = 'Piece de Rechange Intervention'

    request_id = fields.Many2one(
        'maintenance.request', string='Intervention',
        required=True, ondelete='cascade')
    product_id = fields.Many2one(
        'product.product', string='Piece',
        required=True)
    quantite = fields.Float(string='Quantite', default=1.0)
    prix_unitaire = fields.Float(
        string='Prix Unitaire',
        related='product_id.standard_price', readonly=True)
    cout_total = fields.Float(
        string='Cout Total',
        compute='_compute_cout_total', store=True)
    notes = fields.Char(string='Notes')

    @api.depends('quantite', 'prix_unitaire')
    def _compute_cout_total(self):
        for rec in self:
            rec.cout_total = rec.quantite * rec.prix_unitaire
