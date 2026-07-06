from odoo import fields, models


class ProductSupplierinfo(models.Model):
    _inherit = 'product.supplierinfo'

    # Informations saisies directement sur la ligne de prix fournisseur.
    type_fournisseur = fields.Char(string="Type de fournisseur")
    synthese_evaluation = fields.Char(string="Synthèse d'évaluation")
