# -*- coding: utf-8 -*-
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_chauffeur = fields.Boolean(string="Est un chauffeur")
