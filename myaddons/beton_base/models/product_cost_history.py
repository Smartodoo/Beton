from odoo import api, fields, models


class ProductCostHistory(models.Model):
    _name = 'product.cost.history'
    _description = 'Historique des coûts produit'
    _order = 'date desc, id desc'

    product_tmpl_id = fields.Many2one(
        'product.template', string="Produit",
        required=True, ondelete='cascade', index=True,
    )
    date = fields.Datetime(
        string="Date", default=fields.Datetime.now, required=True,
    )
    ancien_cout = fields.Float(string="Ancien coût", digits='Product Price')
    difference = fields.Float(string="Différence", digits='Product Price')
    nouveau_cout = fields.Float(string="Nouveau coût", digits='Product Price')
    user_id = fields.Many2one(
        'res.users', string="Modifié par",
        default=lambda self: self.env.uid, required=True,
    )
    note = fields.Char(string="Note")
    fournisseur_id = fields.Many2one(
        'res.partner',
        string="Fournisseur",
        help="Fournisseur à l'origine de la modification (vide si modification manuelle).",
    )
    purchase_order_id = fields.Many2one(
        'purchase.order',
        string="Bon d'achat",
        ondelete='set null',
    )
    source = fields.Selection([
        ('purchase', 'Bon d\'achat'),
        ('manual', 'Modification manuelle'),
    ], string="Source", default='manual')
    currency_id = fields.Many2one(
        'res.currency', string="Devise",
        default=lambda self: self.env.company.currency_id,
    )
