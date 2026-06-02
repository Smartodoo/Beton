from odoo import api, fields, models


class BetonMotifAnnulation(models.Model):
    _name = 'beton.motif.annulation'
    _description = "Motif d'annulation d'un ordre de fabrication"
    _order = 'date_annulation desc, id desc'
    _rec_name = 'production_name'

    name = fields.Char(string="Référence", default='Nouveau', copy=False, readonly=True)

    production_id = fields.Many2one(
        'mrp.production', string="Ordre de fabrication", ondelete='set null')
    # Copie de la référence : conservée même si l'OF est supprimé
    production_name = fields.Char(string="Réf. ordre de fabrication")

    motif = fields.Text(string="Motif d'annulation", required=True)
    state_avant = fields.Char(string="Statut avant annulation")

    user_id = fields.Many2one(
        'res.users', string="Annulé par",
        default=lambda self: self.env.user, readonly=True)
    date_annulation = fields.Datetime(
        string="Date d'annulation",
        default=fields.Datetime.now, readonly=True)

    # Informations de l'ordre (copiées pour l'historique)
    centrale_id = fields.Many2one('beton.centrale', string="Centrale")
    client_id = fields.Many2one('res.partner', string="Client")
    chantier = fields.Char(string="Chantier")
    product_id = fields.Many2one('product.product', string="Produit")
    product_qty = fields.Float(string="Quantité")

    company_id = fields.Many2one(
        'res.company', string="Société", default=lambda self: self.env.company)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nouveau') == 'Nouveau':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'beton.motif.annulation') or 'Nouveau'
        return super().create(vals_list)
