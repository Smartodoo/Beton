from odoo import api, fields, models

class AccountMove(models.Model):
    _inherit = 'account.move'

    chantier = fields.Char(string="Chantier")
    livraison_ids = fields.Many2many('stock.picking', string="Bons de livraison associés",
                                     domain="[('picking_type_code', '=', 'outgoing')]")
