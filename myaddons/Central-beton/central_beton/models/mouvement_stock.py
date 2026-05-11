# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class CentralBetonMouvementStock(models.Model):
    _name = 'central.beton.mouvement.stock'
    _description = 'Mouvement de Stock Beton'
    _inherit = ['mail.thread']
    _order = 'date desc, id desc'

    name = fields.Char(
        string='Reference', required=True, copy=False,
        readonly=True, default='Nouveau')
    date = fields.Datetime(
        string='Date', default=fields.Datetime.now, required=True)
    type_mouvement = fields.Selection([
        ('entree', 'Entree (Reception)'),
        ('sortie', 'Sortie (Production)'),
        ('perte', 'Perte / Rebut'),
    ], string='Type', required=True, tracking=True)
    product_id = fields.Many2one(
        'product.product', string='Produit', required=True,
        domain="[('is_matiere_beton', '=', True)]")
    quantite = fields.Float(string='Quantite', required=True)
    uom_id = fields.Many2one(
        'uom.uom', string='Unite', related='product_id.uom_id', readonly=True)
    fournisseur_id = fields.Many2one(
        'res.partner', string='Fournisseur',
        domain="[('supplier_rank', '>', 0)]")
    numero_bl = fields.Char(string='Numero BL Fournisseur')
    centrale_id = fields.Many2one(
        'central.beton.centrale', string='Centrale')
    notes = fields.Text(string='Notes')
    stock_move_id = fields.Many2one(
        'stock.move', string='Mouvement Stock', readonly=True)
    state = fields.Selection([
        ('brouillon', 'Brouillon'),
        ('valide', 'Valide'),
        ('annule', 'Annule'),
    ], string='Etat', default='brouillon', tracking=True)

    company_id = fields.Many2one(
        'res.company', string='Societe',
        default=lambda self: self.env.company)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nouveau') == 'Nouveau':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'central.beton.mouvement.stock') or 'Nouveau'
        return super().create(vals_list)

    def action_validate(self):
        for rec in self:
            if rec.state != 'brouillon':
                raise UserError('Seuls les mouvements en brouillon peuvent etre valides.')
            rec._create_stock_move()
            rec.write({'state': 'valide'})
        return True

    def action_cancel(self):
        for rec in self:
            if rec.state == 'valide' and rec.stock_move_id:
                raise UserError(
                    'Un mouvement valide avec un transfert stock ne peut pas etre annule.')
            rec.write({'state': 'annule'})
        return True

    def _create_stock_move(self):
        """Create a real stock.move based on movement type."""
        StockMove = self.env['stock.move']
        for rec in self:
            warehouse = self.env['stock.warehouse'].search(
                [('company_id', '=', rec.company_id.id)], limit=1)
            if not warehouse:
                raise UserError('Aucun entrepot configure pour cette societe.')

            if rec.type_mouvement == 'entree':
                location_src = self.env.ref('stock.stock_location_suppliers')
                location_dest = warehouse.lot_stock_id
            elif rec.type_mouvement == 'sortie':
                location_src = warehouse.lot_stock_id
                location_dest = self.env.ref('stock.stock_location_production')
            else:  # perte
                location_src = warehouse.lot_stock_id
                location_dest = self.env.ref('stock.stock_location_scrapped')

            move = StockMove.create({
                'name': rec.name,
                'product_id': rec.product_id.id,
                'product_uom_qty': rec.quantite,
                'product_uom': rec.uom_id.id,
                'location_id': location_src.id,
                'location_dest_id': location_dest.id,
                'origin': rec.name,
                'company_id': rec.company_id.id,
            })
            move._action_confirm()
            move._action_assign()
            move.quantity = rec.quantite
            move.picked = True
            move._action_done()
            rec.stock_move_id = move.id
