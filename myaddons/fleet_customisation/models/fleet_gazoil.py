# -*- coding: utf-8 -*-
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
        compute='_compute_from_employee',
        store=True,
        readonly=False,
    )
    department_id = fields.Many2one(
        comodel_name='hr.department',
        string="Departement",
        compute='_compute_from_employee',
        store=True,
        readonly=False,
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

    @api.depends('employee_id')
    def _compute_from_employee(self):
        for rec in self:
            emp = rec.employee_id
            if emp:
                rec.department_id = emp.department_id
                vehicle = self.env['fleet.vehicle'].search(
                    [('driver_id', '=', emp.work_contact_id.id)], limit=1
                )
                rec.vehicle_id = vehicle
            else:
                rec.department_id = False
                rec.vehicle_id = False
