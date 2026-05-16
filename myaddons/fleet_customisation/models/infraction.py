# -*- coding: utf-8 -*-
from odoo import api, fields, models


class FleetInfraction(models.Model):
    _name = 'fleet.infraction'
    _description = "Historique des infractions"
    _order = 'date_infraction desc'

    conducteur_id = fields.Many2one(
        'hr.employee',
        string="Conducteur",
        domain="[('role_employe', '=', 'chauffeur')]",
        required=True
    )

    date_infraction = fields.Date(
        string="Date de l'infraction", required=True, default=fields.Date.today)

    type_infraction = fields.Selection([
        ('vitesse', 'Excès de vitesse'),
        ('stationnement', 'Stationnement gênant'),
        ('accident', 'Accident responsable'),
        ('code', 'Non-respect du code de la route'),
        ('autre', 'Autre'),
    ], string="Type d'infraction", required=True)

    description = fields.Text(string="Description détaillée")
    lieu = fields.Char(string="Lieu de l'incident")

    vehicle_id = fields.Many2one('fleet.vehicle', string="Véhicule concerné")

    gravite = fields.Selection([
        ('mineure', 'Mineure'),
        ('moyenne', 'Moyenne'),
        ('grave', 'Grave'),
    ], string="Niveau de gravité")

    sanction = fields.Selection([
        ('avertissement', 'Avertissement'),
        ('suspension', 'Suspension du permis/brevet'),
        ('amende', 'Amende'),
        ('autre', 'Autre sanction'),
    ], string="Sanction appliquée")

    name = fields.Char(string="Référence", compute='_compute_name', store=True)

    @api.depends('conducteur_id', 'date_infraction')
    def _compute_name(self):
        for record in self:
            if record.conducteur_id and record.date_infraction:
                record.name = f"Infraction - {record.conducteur_id.name} - {record.date_infraction}"
            else:
                record.name = "Nouvelle Infraction"
