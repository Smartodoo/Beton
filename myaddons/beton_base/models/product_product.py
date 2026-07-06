from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    # Quantité disponible uniquement dans le stock principal (WH/Stock),
    # au niveau de la variante — surcharge la valeur déléguée du modèle.
    qty_en_stock = fields.Float(
        string="En stock",
        compute='_compute_qty_en_stock_variant',
        digits='Product Unit of Measure',
        help="Quantité disponible uniquement dans le stock principal de "
             "l'entreprise (WH/Stock), et non le total tous emplacements.",
    )

    def _compute_qty_en_stock_variant(self):
        # Quantité strictement dans WH/Stock (emplacement exact, hors
        # sous-emplacements).
        location = self.env['product.template']._beton_wh_stock_location()
        Quant = self.env['stock.quant'].sudo()
        for product in self:
            if location:
                quants = Quant.search([
                    ('product_id', '=', product.id),
                    ('location_id', '=', location.id),
                ])
                product.qty_en_stock = sum(quants.mapped('quantity'))
            else:
                product.qty_en_stock = 0.0

    def action_print_fournisseurs_report(self):
        """Le formulaire variante hérite (vue primaire) du formulaire modèle,
        donc du bouton « Meilleurs fournisseurs ». On délègue au modèle,
        car la méthode et le rapport sont définis sur product.template."""
        self.ensure_one()
        return self.product_tmpl_id.action_print_fournisseurs_report()
