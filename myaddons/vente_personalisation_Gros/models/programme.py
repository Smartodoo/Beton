from odoo import fields, models, api

class Programme(models.Model):
    _name = 'programme'
    _description = 'Programme'

    nom = fields.Many2one('res.partner', string='Client', tracking=True)
    adresse = fields.Char(string='Adresse', tracking=True, help='Adresse du client')
    phone = fields.Char(string='Téléphone', tracking=True, help='Téléphone du client')
    beton = fields.Char(string='Béton', tracking=True)
    qty = fields.Float(string='Quantité', tracking=True)
    date = fields.Date(string='Date', tracking=True)
    price_unit = fields.Float(string='Prix unitaire', tracking=True, help='Prix unitaire du béton')
    giraphe = fields.Selection([('1', 'AVEC GIRAPHE'), ('2', 'SANS GIRAPHE')], string='Giraphe', tracking=True)
    description = fields.Text(string='Description', tracking=True, help='Description du programme')

