from odoo import api, fields, models


class BetonBonSortie(models.Model):
    _name = 'beton.bon.sortie'
    _description = 'Bon de Sortie Service'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(string="Numéro", readonly=True, default='Nouveau', copy=False)
    date = fields.Date(string="Date de sortie", required=True, default=fields.Date.today, tracking=True)
    sale_order_id = fields.Many2one('sale.order', string="Bon de commande", readonly=True)
    partner_id = fields.Many2one('res.partner', string="Client", required=True, tracking=True)
    product_id = fields.Many2one(
        'product.product', string="Produit / Service",
        required=True, tracking=True,
        domain="[('detailed_type', '=', 'service')]")
    quantity = fields.Float(string="Quantité", default=1.0)
    product_uom_id = fields.Many2one(
        'uom.uom', string="Unité",
        related='product_id.uom_id', readonly=True)
    chantier = fields.Char(string="Chantier")
    description = fields.Text(string="Description")
    document_ids = fields.Many2many(
        'ir.attachment', 'beton_bon_sortie_ir_attachment_rel',
        'bon_sortie_id', 'attachment_id',
        string="Pièces jointes")
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('confirmed', 'Confirmé'),
        ('done', 'Terminé'),
        ('cancel', 'Annulé'),
    ], string="Statut", default='draft', tracking=True)
    company_id = fields.Many2one('res.company', string="Société", default=lambda self: self.env.company)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nouveau') == 'Nouveau':
                vals['name'] = self.env['ir.sequence'].next_by_code('beton.bon.sortie') or 'Nouveau'
        return super().create(vals_list)

    def action_confirm(self):
        for rec in self:
            rec.state = 'confirmed'

    def action_done(self):
        for rec in self:
            rec.state = 'done'

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'

    def action_reset_draft(self):
        for rec in self:
            rec.state = 'draft'
