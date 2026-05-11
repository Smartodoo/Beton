from odoo import fields, models


class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    document_ids = fields.Many2many(
        'ir.attachment', 'stock_scrap_ir_attachment_rel',
        'scrap_id', 'attachment_id',
        string="Pièces jointes")
