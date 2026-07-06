from odoo import fields, models


class StockWarehouseOrderpoint(models.Model):
    _inherit = 'stock.warehouse.orderpoint'

    # Colonnes ajoutées à la fiche de réapprovisionnement (Achats / Inventaire).
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
