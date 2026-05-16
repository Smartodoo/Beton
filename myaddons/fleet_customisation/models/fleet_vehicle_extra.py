# -*- coding: utf-8 -*-
from odoo import api, fields, models


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    # === Traçabilité & affectation ===
    ancien_matricule = fields.Char(string="Ancien Matricule")
    societe_appartenance_id = fields.Many2one(
        'fleet.societe.appartenance',
        string="Société d'Appartenance",
    )

    # === Conducteur - Permis de conduire ===
    numero_permis = fields.Char(string="Numéro de permis de conduire")
    date_delivrance_permis = fields.Date(string="Date de délivrance")
    date_expiration_permis = fields.Date(string="Date d'expiration")
    categorie_permis_id = fields.Many2one(
        'fleet.vehicle.model.category',
        string="Catégorie de permis",
    )

    # === Informations administratives ===
    service_utilisateur_id = fields.Many2one(
        'hr.department',
        string="Service utilisateur"
    )
    date_acquisition = fields.Date(string="Date d'acquisition")
    mode_acquisition = fields.Selection([
        ('achat', 'Achat'),
        ('location', 'Location'),
        ('leasing', 'Leasing'),
    ], string="Mode d'acquisition")
    fournisseur_id = fields.Many2one(
        'res.partner',
        string="Fournisseur / Concessionnaire"
    )

    # === Données techniques ===
    capacite_reservoir = fields.Float(string="Capacité du réservoir (L)")
    kilometrage_actuel = fields.Float(string="Kilométrage actuel")
    consommation_moyenne = fields.Float(string="Consommation moyenne (L/100km)")
    etat_vehicule = fields.Selection([
        ('bon', 'Bon'),
        ('moyen', 'Moyen'),
        ('en_panne', 'En panne'),
        ('hors_service', 'Hors service'),
    ], string="État du véhicule", default='bon')

    x_type_vehicule_choix = fields.Selection(
        selection=[
            ('light', 'Léger'),
            ('utility', 'Utilitaire'),
            ('heavy', 'Poids lourd'),
            ('machinery', 'Engin'),
            ('other', 'Autre')
        ],
        string="Type de véhicule",
        default='light',
        store=True
    )
    x_annee_circulation = fields.Char(
        string="Année de mise en circulation",
        store=True
    )
    x_couleur_vehicule = fields.Char(
        string="Couleur",
        store=True
    )

    document_reglementaire_ids = fields.One2many(
        'fleet.vehicle.document',
        'vehicle_id',
        string="Documents réglementaires"
    )

    maintenance_ids = fields.One2many(
        'fleet.vehicle.maintenance',
        'vehicle_id',
        string="Suivi de maintenance"
    )

    @api.onchange('model_id')
    def _onchange_model_id_categorie(self):
        if self.model_id and self.model_id.category_id:
            self.categorie_permis_id = self.model_id.category_id

    @api.onchange('driver_id')
    def _onchange_driver_id_permis(self):
        """Auto-remplir les champs permis depuis la fiche employé chauffeur."""
        if not self.driver_id:
            return
        employee = self.env['hr.employee'].sudo().search([
            ('work_contact_id', '=', self.driver_id.id),
            ('role_employe', '=', 'chauffeur'),
        ], limit=1)
        if employee:
            self.numero_permis = employee.numero_permis
            self.date_expiration_permis = employee.date_expiration_permis


class FleetVehicleLogContract(models.Model):
    _inherit = 'fleet.vehicle.log.contract'

    # Champs related pour récupérer automatiquement les infos du véhicule
    vehicle_brand_id = fields.Many2one(
        'fleet.vehicle.model.brand', string="Marque",
        related='vehicle_id.brand_id', readonly=True, store=False)
    vehicle_model_id = fields.Many2one(
        'fleet.vehicle.model', string="Modèle",
        related='vehicle_id.model_id', readonly=True, store=False)
    vehicle_license_plate = fields.Char(
        string="Immatriculation",
        related='vehicle_id.license_plate', readonly=True, store=False)
    vehicle_vin_sn = fields.Char(
        string="N° Châssis (VIN)",
        related='vehicle_id.vin_sn', readonly=True, store=False)
    vehicle_model_year = fields.Char(
        string="Année du modèle",
        related='vehicle_id.model_year', readonly=True, store=False)
    vehicle_color = fields.Char(
        string="Couleur",
        related='vehicle_id.color', readonly=True, store=False)
    vehicle_fuel_type = fields.Selection(
        related='vehicle_id.fuel_type', string="Type de carburant",
        readonly=True, store=False)
    vehicle_transmission = fields.Selection(
        related='vehicle_id.transmission', string="Transmission",
        readonly=True, store=False)
    vehicle_horsepower = fields.Integer(
        string="Puissance (CV)",
        related='vehicle_id.horsepower', readonly=True, store=False)
    vehicle_power = fields.Integer(
        string="Puissance (kW)",
        related='vehicle_id.power', readonly=True, store=False)
    document_ids = fields.Many2many(
        'ir.attachment', 'fleet_contract_ir_attachment_rel',
        'contract_id', 'attachment_id',
        string="Pièces jointes")


class FleetVehicleDocument(models.Model):
    _name = 'fleet.vehicle.document'
    _description = 'Documents réglementaires du véhicule'

    vehicle_id = fields.Many2one('fleet.vehicle', required=True)

    # Carte grise
    carte_grise_numero = fields.Char(string="N° Carte grise")
    carte_grise_date = fields.Date(string="Date carte grise")

    # Assurance
    assurance_compagnie = fields.Char(string="Compagnie d'assurance")
    assurance_numero_police = fields.Char(string="N° de police")
    assurance_date_debut = fields.Date(string="Date de début Assurance")
    assurance_date_expiration = fields.Date(string="Date d'expiration Assurance")
    assurance_cout = fields.Float(string="Coût assurance")

    # Contrôle technique
    controle_date_validite = fields.Date(string="Date de validité Contrôle")
    controle_date_expiration = fields.Date(string="Date d'expiration Contrôle")
    controle_etablissement = fields.Char(string="Établissement de contrôle")
    controle_cout = fields.Float(string="Coût contrôle ")

    # Vignette
    vignette_date_validite = fields.Date(string="Date de validité Vignette")
    vignette_date_expiration = fields.Date(string="Date d'expiration Vignette")
    vignette_cout = fields.Float(string="Coût vignette ")


class FleetVehicleMaintenance(models.Model):
    _name = 'fleet.vehicle.maintenance'
    _description = 'Suivi de maintenance'

    vehicle_id = fields.Many2one('fleet.vehicle', required=True)

    date_intervention = fields.Date(string="Date", required=True)
    type_intervention = fields.Selection([
        ('entretien_periodique', 'Entretien périodique'),
        ('reparation', 'Réparation'),
        ('vidange', 'Vidange'),
        ('changement_pieces', 'Changement de pièces'),
    ], string="Type d'intervention", required=True)
    description = fields.Text(string="Description")
    cout = fields.Float(string="Coût")
    prestataire_id = fields.Many2one('res.partner', string="Prestataire")
