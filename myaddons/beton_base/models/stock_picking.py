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
    adjuvant_chantier = fields.Float(string="Adjuvant chantier (L)")
    motif_retour = fields.Text(string="Motif du retour")
    qte_transportee = fields.Float(
        string="Quantité transportée (m³)",
        compute='_compute_qte_transportee',
        help="Quantité totale livrée sur ce bon (somme des mouvements de stock).",
    )
    document_ids = fields.Many2many(
        'ir.attachment', 'stock_picking_ir_attachment_rel',
        'picking_id', 'attachment_id',
        string="Pièces jointes")

    @api.depends('move_ids.quantity')
    def _compute_qte_transportee(self):
        for rec in self:
            rec.qte_transportee = sum(rec.move_ids.mapped('quantity'))

    @api.depends('heure_depart', 'heure_arrivee')
    def _compute_temps_trajet(self):
        for rec in self:
            if rec.heure_arrivee and rec.heure_depart:
                diff = rec.heure_arrivee - rec.heure_depart
                rec.temps_trajet = diff.total_seconds() / 60
            else:
                rec.temps_trajet = 0

    def _register_hook(self):
        super()._register_hook()
        report = self.env.ref('stock.action_report_delivery', raise_if_not_found=False)
        if report:
            report.with_context(lang='fr_FR').write({'name': 'Bon de Réception'})
            report.with_context(lang='en_US').write({'name': 'Bon de Réception'})
