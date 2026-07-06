from odoo import fields, models


class BetonObjectifHistory(models.Model):
    _name = 'beton.objectif.history'
    _description = "Historique des objectifs d'un ordre de fabrication"
    _order = 'date desc, id desc'

    production_id = fields.Many2one(
        'mrp.production', string="Ordre de fabrication",
        required=True, ondelete='cascade', index=True)
    date = fields.Datetime(
        string="Date", default=fields.Datetime.now, required=True)
    ancien_objectif = fields.Float(string="Ancien objectif (m³)")
    nouvel_objectif = fields.Float(string="Nouvel objectif (m³)")
    user_id = fields.Many2one(
        'res.users', string="Modifié par",
        default=lambda self: self.env.user)
    source = fields.Selection([
        ('creation', 'Création'),
        ('manuel', 'Manuel'),
        ('global', 'Objectif global'),
    ], string="Origine", default='manuel')
