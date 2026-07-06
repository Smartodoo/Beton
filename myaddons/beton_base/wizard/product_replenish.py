from odoo import fields, models


class ProductReplenish(models.TransientModel):
    _inherit = 'product.replenish'

    # Informations affichées sur le wizard de réapprovisionnement du produit :
    # la quantité disponible en stock et le seuil minimum béton du produit.
    qty_disponible = fields.Float(
        string="Quantité disponible",
        related='product_id.qty_available',
        readonly=True,
    )
    seuil_minimum = fields.Float(
        string="Seuil minimum",
        related='product_id.qty_minimum',
        readonly=True,
        help="Seuil minimum béton du produit (utilisé pour les alertes).",
    )
