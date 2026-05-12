from odoo import fields, models


class FleetSocieteAppartenance(models.Model):
    _name = 'fleet.societe.appartenance'
    _description = "Société d'Appartenance du véhicule"
    _order = 'name'

    name = fields.Char(string="Nom", required=True)
    code = fields.Char(string="Code")
    description = fields.Text(string="Description")
    active = fields.Boolean(default=True)
