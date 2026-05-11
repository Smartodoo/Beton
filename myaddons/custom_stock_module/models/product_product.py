from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # emplacement = fields.Char(string='Emplacement', help='Emplacement du produit')
    emplacement_id = fields.Many2one('emplacement.product', string='Emplacement')


class EmplacementProduct(models.Model):
    _name = 'emplacement.product'
    _description = 'Emplacement du produit'


    name = fields.Char(string='Emplacement')