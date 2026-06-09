from odoo import api, fields, models


class FleetGazoil(models.Model):
    _name = 'fleet.gazoil'
    _description = 'Consommation Gazoil'
    _order = 'date desc'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string="Conducteur",
        required=True,
        domain=[('role_employe', '=', 'chauffeur')],
    )
    vehicle_id = fields.Many2one(
        comodel_name='fleet.vehicle',
        string="Vehicule",
    )
    department_id = fields.Many2one(
        comodel_name='hr.department',
        string="Departement",
    )
    telephone_chauffeur = fields.Char(
        string="N° Telephone",
        related='employee_id.telephone_chauffeur',
        readonly=True,
    )
    numero_permis = fields.Char(
        string="N° Permis",
        related='employee_id.numero_permis',
        readonly=True,
    )
    date_expiration_permis = fields.Date(
        string="Expiration Permis",
        related='employee_id.date_expiration_permis',
        readonly=True,
    )
    vehicle_license_plate = fields.Char(
        string="Immatriculation",
        related='vehicle_id.license_plate',
        readonly=True,
    )
    vehicle_model_id = fields.Many2one(
        comodel_name='fleet.vehicle.model',
        string="Modele",
        related='vehicle_id.model_id',
        readonly=True,
    )
    vehicle_fuel_type = fields.Selection(
        string="Type de carburant",
        related='vehicle_id.fuel_type',
        readonly=True,
    )
    fournisseur = fields.Char(
        string="Fournisseur",
    )
    observations = fields.Char(
        string="Observations",
    )
    date = fields.Date(
        string="Date",
        required=True,
        default=fields.Date.today,
    )
    montant = fields.Float(
        string="Montant (DA)",
        digits=(10, 2),
        required=True,
    )
    nombre_litres = fields.Float(
        string="Nombre de litres",
        digits=(10, 2),
    )
    kilometrage_actuel = fields.Float(
        string="Kilometrage actuel",
        digits=(10, 2),
    )
    ancien_kilometrage = fields.Float(
        string="Ancien kilometrage",
        digits=(10, 2),
    )
    consommation_moyenne = fields.Float(
        string="Consommation moyenne (L/100km)",
        digits=(10, 2),
        compute='_compute_consommation_moyenne',
        store=True,
    )

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        for rec in self:
            emp = rec.employee_id
            if not emp:
                continue
            rec.department_id = emp.department_id
            if emp.work_contact_id:
                vehicle = self.env['fleet.vehicle'].search(
                    [('driver_id', '=', emp.work_contact_id.id)], limit=1
                )
                if vehicle:
                    rec.vehicle_id = vehicle

    @api.onchange('vehicle_id')
    def _onchange_vehicle_id(self):
        for rec in self:
            vehicle = rec.vehicle_id
            if not vehicle or not vehicle.driver_id:
                continue
            employee = self.env['hr.employee'].search([
                ('work_contact_id', '=', vehicle.driver_id.id),
                ('role_employe', '=', 'chauffeur'),
            ], limit=1)
            if employee:
                rec.employee_id = employee
                if employee.department_id:
                    rec.department_id = employee.department_id

    @api.depends('nombre_litres', 'kilometrage_actuel', 'ancien_kilometrage')
    def _compute_consommation_moyenne(self):
        for rec in self:
            distance = rec.kilometrage_actuel - rec.ancien_kilometrage
            if distance > 0 and rec.nombre_litres:
                rec.consommation_moyenne = (rec.nombre_litres / distance) * 100
            else:
                rec.consommation_moyenne = 0.0
