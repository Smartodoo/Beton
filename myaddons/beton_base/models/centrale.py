from odoo import api, fields, models


class BetonCentrale(models.Model):
    _name = 'beton.centrale'
    _description = 'Centrale à Béton'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Nom de la centrale", required=True, tracking=True)
    code = fields.Char(string="Code")
    adresse = fields.Char(string="Adresse")
    capacite_horaire = fields.Float(string="Capacité horaire (m³/h)")
    heures_travail_jour = fields.Float(
        string="Heures de travail / jour",
        default=8.0,
        help="Nombre d'heures de travail par jour pour calculer la capacité journalière.",
    )
    capacite_journaliere = fields.Float(
        string="Capacité journalière (m³/jour)",
        compute='_compute_capacite_journaliere',
        store=True,
        help="Capacité maximale produite par jour = capacité horaire × heures de travail.",
    )

    @api.depends('capacite_horaire', 'heures_travail_jour')
    def _compute_capacite_journaliere(self):
        for rec in self:
            rec.capacite_journaliere = (rec.capacite_horaire or 0.0) * (rec.heures_travail_jour or 0.0)

    responsable_id = fields.Many2one('hr.employee', string="Responsable")
    etat = fields.Selection([
        ('operationnelle', 'Opérationnelle'),
        ('maintenance', 'En maintenance'),
        ('arret', "À l'arrêt"),
    ], string="État", default='operationnelle', tracking=True)
    warehouse_id = fields.Many2one('stock.warehouse', string="Entrepôt associé")
    document_ids = fields.Many2many(
        'ir.attachment', 'beton_centrale_ir_attachment_rel',
        'centrale_id', 'attachment_id',
        string="Pièces jointes")
    company_id = fields.Many2one('res.company', string="Société", default=lambda self: self.env.company)
    active = fields.Boolean(default=True)
