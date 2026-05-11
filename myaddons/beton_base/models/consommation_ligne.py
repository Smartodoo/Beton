from odoo import api, fields, models


class BetonConsommationLigne(models.Model):
    _name = 'beton.consommation.ligne'
    _description = 'Ligne de consommation matière'

    fabrication_id = fields.Many2one('beton.fabrication', string="Fabrication", ondelete='cascade')
    product_id = fields.Many2one('product.product', string="Matière première", required=True)
    qte_theorique = fields.Float(string="Qté théorique")
    qte_reelle = fields.Float(string="Qté réelle")
    ecart = fields.Float(string="Écart", compute='_compute_ecart', store=True)

    @api.depends('qte_theorique', 'qte_reelle')
    def _compute_ecart(self):
        for ligne in self:
            ligne.ecart = ligne.qte_reelle - ligne.qte_theorique
