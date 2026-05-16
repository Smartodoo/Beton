# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date


class FleetVehicleLogServicesInherit(models.Model):
    _inherit = "fleet.vehicle.log.services"

    date_de_fin = fields.Date(help='Date when the cost has been ended')
    vendor_id = fields.Many2one('res.partner', 'Vendor', domain=[('contact_type', '=', 'SUPPLIER'), ])
    purchaser_id = fields.Many2one('res.partner', string="Driver", compute='_compute_purchaser_id', readonly=False,
                                   store=True)
    name_service = fields.Char(related='service_type_id.name', string='service related')
    prochaine_vidange = fields.Float(string='prochaine vidange',
                                     help='Selon les recommandations , le prochaine vidange doit être effectuée')
    n_police = fields.Char(string='n° police', help="n° police de l\'assurance")


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    image_128 = fields.Image(related='model_id.image_128', readonly=False)
    carrosserie_id = fields.Many2one('fleet.carrosserie', string='Carrosserie', tracking=True)
    type_vin = fields.Char(string='Type', tracking=True)
    point_total = fields.Float(string='Point total', tracking=True)
    unite_mesure = fields.Many2one('uom.category', string="Unité de mesure", domain=[('name', '=', 'Poids')])
    uom_ids = fields.One2many(related='unite_mesure.uom_ids', string="Unités de mesure", readonly=True)
    charge_utile = fields.Float(string='Charge utile', tracking=True)
    unite_point_total = fields.Many2one('uom.uom',
                                        string="Unité de charge utile",
                                        domain="[('category_id', '=', 2)]",
                                        default=lambda self: self.env['uom.uom'].search(
                                            [('name', '=', 'kg'), ('category_id', '=', 2)], limit=1).id)

    unite_charge_utile = fields.Many2one(
        'uom.uom',
        string="Unité de charge utile",
        domain="[('category_id', '=', 2)]",
        default=lambda self: self.env['uom.uom'].search([('name', '=', 'kg'), ('category_id', '=', 2)], limit=1).id

    )
    technical_file = fields.Many2many(
        'ir.attachment',
        'fleet_vehicle_technical_file_rel',
        'vehicle_id', 'attachment_id',
        string="Téléchargez vos fichiers", tracking=True)

    technical_file_name = fields.Char(string='Nom du Fichier', tracking=True)

    @api.onchange('image_128')
    def _onchange_field_1(self):
        if self.model_id:
            self.model_id.image_128 = self.image_128


class FleetVehicleLogContract(models.Model):
    _inherit = 'fleet.vehicle.log.contract'

    expiration_color = fields.Char(string="Expiration Color", compute="_compute_expiration_color")

    @api.depends('expiration_date')
    def _compute_expiration_color(self):
        today = date.today()
        for record in self:
            if record.expiration_date:
                delta_days = (record.expiration_date - today).days
                if delta_days <= 7:
                    # rouge transparent
                    record.expiration_color = 'rgba(255,0,0,0.3)'
                elif delta_days <= 15:
                    # orange transparent
                    record.expiration_color = 'rgba(255,121,0,0.3)'
                else:
                    record.expiration_color = ''
            else:
                record.expiration_color = ''

        # ✅ Vérification immédiate lors de la sélection de la date d'expiration

    @api.onchange('expiration_date')
    def _onchange_expiration_date(self):
        if self.start_date and self.expiration_date:
            if self.expiration_date < self.start_date:
                self.expiration_date = False  # réinitialise le champ pour forcer l'utilisateur à choisir une date correcte
                return {
                    'warning': {
                        'title': "Erreur de date",
                        'message': "La date d'expiration doit être supérieure ou égale à la date de début du contrat."
                    }
                }
