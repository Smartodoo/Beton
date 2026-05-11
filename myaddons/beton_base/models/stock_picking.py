from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    chantier = fields.Char(string="Chantier")
    formule_beton_id = fields.Many2one('mrp.bom', string="Formule béton")
    vehicle_id = fields.Many2one('fleet.vehicle', string="Camion")
    chauffeur_id = fields.Many2one('hr.employee', string="Chauffeur", domain="[('role_employe', '=', 'chauffeur')]")
    heure_depart = fields.Datetime(string="Heure départ centrale")
    heure_arrivee = fields.Datetime(string="Heure arrivée chantier")
    temps_attente = fields.Float(string="Temps d'attente (min)")
    temps_trajet = fields.Float(
        string="Temps trajet (min)",
        compute='_compute_temps_trajet',
        store=True,
    )
    distance = fields.Float(string="Distance (km)")
    document_ids = fields.Many2many(
        'ir.attachment', 'stock_picking_ir_attachment_rel',
        'picking_id', 'attachment_id',
        string="Pièces jointes")

    @api.depends('heure_depart', 'heure_arrivee')
    def _compute_temps_trajet(self):
        for rec in self:
            if rec.heure_arrivee and rec.heure_depart:
                diff = rec.heure_arrivee - rec.heure_depart
                rec.temps_trajet = diff.total_seconds() / 60
            else:
                rec.temps_trajet = 0
