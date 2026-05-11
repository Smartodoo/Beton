from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    responsable_id = fields.Many2one('hr.employee', string="Responsable")
    justification = fields.Text(string="Justification")
    cout_total = fields.Float(
        string="Coût total",
        compute='_compute_cout_total',
        store=True,
    )

    @api.depends('price_unit', 'product_uom_qty')
    def _compute_cout_total(self):
        for move in self:
            move.cout_total = move.price_unit * move.product_uom_qty

    def _action_done(self, cancel_backorder=False):
        res = super()._action_done(cancel_backorder=cancel_backorder)
        for move in self:
            if not move.price_unit and move.product_id:
                move.price_unit = move.product_id.standard_price
        return res


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    price_unit = fields.Float(
        string="Coût unitaire",
        related='move_id.price_unit', store=False)
    cout_total = fields.Float(
        string="Coût total",
        related='move_id.cout_total', store=False)
