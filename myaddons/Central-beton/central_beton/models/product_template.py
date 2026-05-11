# -*- coding: utf-8 -*-

from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_matiere_beton = fields.Boolean(
        string='Matiere Premiere Beton', default=False)
    type_matiere_beton = fields.Selection([
        ('ciment', 'Ciment'),
        ('sable', 'Sable'),
        ('gravier', 'Gravier'),
        ('eau', 'Eau'),
        ('adjuvant', 'Adjuvant'),
        ('addition', 'Addition'),
    ], string='Type Matiere Beton')
    emplacement_beton = fields.Selection([
        ('silo', 'Silo'),
        ('tremie', 'Tremie'),
        ('bassin', 'Bassin'),
        ('cuve', 'Cuve'),
    ], string='Emplacement')
    capacite_stockage = fields.Float(string='Capacite de Stockage')
    seuil_alerte = fields.Float(
        string='Seuil d\'Alerte',
        help='Quantite minimale avant alerte de reapprovisionnement')
    fournisseur_principal_id = fields.Many2one(
        'res.partner', string='Fournisseur Principal',
        domain="[('supplier_rank', '>', 0)]")
