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
    alerte_qty_minimum = fields.Boolean(
        compute='_compute_alerte_qty_minimum',
    )

    @api.depends('product_id')
    def _compute_alerte_qty_minimum(self):
        for move in self:
            product = move.product_id
            tmpl = product.product_tmpl_id if product else False
            if tmpl and tmpl.qty_minimum > 0 and product.qty_available <= tmpl.qty_minimum:
                move.alerte_qty_minimum = True
            else:
                move.alerte_qty_minimum = False

    @api.depends('price_unit', 'product_uom_qty')
    def _compute_cout_total(self):
        for move in self:
            move.cout_total = move.price_unit * move.product_uom_qty

    @api.onchange('product_id')
    def _onchange_product_id_price(self):
        for move in self:
            if move.product_id:
                move.price_unit = move.product_id.standard_price

    def _action_done(self, cancel_backorder=False):
        res = super()._action_done(cancel_backorder=cancel_backorder)
        for move in self:
            if not move.price_unit and move.product_id:
                move.price_unit = move.product_id.standard_price
        self._check_qty_minimum()
        return res

    def _check_qty_minimum(self):
        """Vérifie si le stock disponible est inférieur à la quantité minimum
        et poste une notification sur le canal Discuss 'Quantité Minimum'."""
        templates = self.mapped('product_id.product_tmpl_id').filtered(
            lambda t: t.classification_produit == 'matiere_premiere' and t.qty_minimum > 0
        )
        if not templates:
            return
        channel = self.env.ref('beton_base.channel_qty_minimum', raise_if_not_found=False)
        if not channel:
            return
        for tmpl in templates:
            # Invalider le cache pour lire les quantités à jour après le mouvement
            variants = tmpl.product_variant_ids
            variants.invalidate_recordset(['qty_available'])
            qty_available = sum(variants.mapped('qty_available'))
            if qty_available <= tmpl.qty_minimum:
                channel.sudo().message_post(
                    body=tmpl._build_qty_minimum_alert(qty_available),
                    message_type='comment',
                    subtype_xmlid='mail.mt_comment',
                )


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    price_unit = fields.Float(
        string="Coût unitaire",
        related='move_id.price_unit', store=False)
    cout_total = fields.Float(
        string="Coût total",
        related='move_id.cout_total', store=False)
