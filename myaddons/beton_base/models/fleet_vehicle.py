from odoo import api, fields, models


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    capacite_m3 = fields.Float(string="Capacité (m³)")
    consommation_moyenne = fields.Float(string="Consommation moyenne (L/100km)")
    cout_km = fields.Float(string="Coût par km")
    etat_camion = fields.Selection([
        ('disponible', 'Disponible'),
        ('en_mission', 'En mission'),
        ('en_panne', 'En panne'),
        ('en_maintenance', 'En maintenance'),
    ], string="État opérationnel", default='disponible', tracking=True)
    document_ids = fields.Many2many(
        'ir.attachment', 'fleet_vehicle_ir_attachment_rel',
        'vehicle_id', 'attachment_id',
        string="Pièces jointes")


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
    vehicle_capacite_m3 = fields.Float(
        string="Capacité (m³)",
        related='vehicle_id.capacite_m3', readonly=True, store=False)
    vehicle_consommation_moyenne = fields.Float(
        string="Consommation moyenne (L/100km)",
        related='vehicle_id.consommation_moyenne', readonly=True, store=False)
    vehicle_cout_km = fields.Float(
        string="Coût par km",
        related='vehicle_id.cout_km', readonly=True, store=False)
    vehicle_etat_camion = fields.Selection(
        related='vehicle_id.etat_camion', string="État opérationnel",
        readonly=True, store=False)
    document_ids = fields.Many2many(
        'ir.attachment', 'fleet_contract_ir_attachment_rel',
        'contract_id', 'attachment_id',
        string="Pièces jointes")
