# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    chantier_id = fields.Many2one(
        'central.beton.chantier', string='Chantier')
    bom_id = fields.Many2one(
        'mrp.bom', string='Formule Beton',
        domain="[('is_beton_bom', '=', True)]")
    volume_total = fields.Float(
        string='Volume Total (m3)',
        compute='_compute_volume_total', store=True)
    production_ids = fields.One2many(
        'mrp.production', 'commande_id',
        string='Ordres de Fabrication')
    production_count = fields.Integer(
        string='Nombre de Fabrications',
        compute='_compute_production_count')
    livraison_beton_ids = fields.One2many(
        'central.beton.livraison', 'commande_id',
        string='Livraisons Beton')

    @api.depends('order_line.product_uom_qty')
    def _compute_volume_total(self):
        for order in self:
            order.volume_total = sum(
                line.product_uom_qty
                for line in order.order_line
                if line.product_id.is_matiere_beton
                or line.product_id.categ_id.name == 'Beton'
            )

    @api.depends('production_ids')
    def _compute_production_count(self):
        for order in self:
            order.production_count = len(order.production_ids)

    def action_view_productions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Ordres de Fabrication',
            'res_model': 'mrp.production',
            'view_mode': 'tree,form',
            'domain': [('commande_id', '=', self.id)],
            'context': {'default_commande_id': self.id},
        }


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    bom_id = fields.Many2one(
        'mrp.bom', string='Formule Beton',
        domain="[('is_beton_bom', '=', True)]")
    volume_m3 = fields.Float(string='Volume (m3)')
