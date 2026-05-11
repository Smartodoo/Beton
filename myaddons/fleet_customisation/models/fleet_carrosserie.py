from odoo import models, fields, api


class FleetCarrosserie(models.Model):
    _name = 'fleet.carrosserie'
    _description = 'carrosserie'

    name = fields.Char(string="nom", required=True)