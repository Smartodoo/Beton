from odoo import api, fields, models
from odoo.exceptions import UserError


class BetonLivraison(models.Model):
    _name = 'beton.livraison'
    _description = 'Bon de Livraison Béton'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(string="Numéro BL", readonly=True, default='Nouveau', copy=False)
    date = fields.Date(string="Date", required=True, default=fields.Date.today, tracking=True)
    fabrication_id = fields.Many2one('beton.fabrication', string="Ordre de fabrication")
    client_id = fields.Many2one(
        'res.partner',
        string="Client",
        required=True,
        domain="[('type_partenaire_beton', '=', 'client')]",
        context={'default_type_partenaire_beton': 'client', 'default_is_company': True},
    )
    chantier = fields.Char(string="Chantier")
    formule_beton_id = fields.Many2one('beton.formule', string="Formule béton")
    quantite_livree = fields.Float(string="Quantité livrée (m³)", required=True)
    vehicle_id = fields.Many2one(
        'fleet.vehicle',
        string="Camion",
    )
    chauffeur_id = fields.Many2one('hr.employee', string="Chauffeur")
    heure_depart = fields.Datetime(string="Heure départ centrale")
    heure_arrivee = fields.Datetime(string="Heure arrivée chantier")
    temps_attente = fields.Float(string="Temps d'attente (min)")
    temps_trajet = fields.Float(
        string="Temps trajet (min)",
        compute='_compute_temps_trajet',
        store=True,
    )
    distance = fields.Float(string="Distance (km)")
    state = fields.Selection([
        ('prevu', 'Prévu'),
        ('en_cours', 'En cours'),
        ('livre', 'Livré'),
        ('annule', 'Annulé'),
    ], string="Statut", default='prevu', tracking=True)
    company_id = fields.Many2one('res.company', string="Société", default=lambda self: self.env.company)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nouveau') == 'Nouveau':
                vals['name'] = self.env['ir.sequence'].next_by_code('beton.livraison') or 'Nouveau'
        return super().create(vals_list)

    @api.depends('heure_depart', 'heure_arrivee')
    def _compute_temps_trajet(self):
        for rec in self:
            if rec.heure_arrivee and rec.heure_depart:
                diff = rec.heure_arrivee - rec.heure_depart
                rec.temps_trajet = diff.total_seconds() / 60
            else:
                rec.temps_trajet = 0

    @api.onchange('fabrication_id')
    def _onchange_fabrication(self):
        if self.fabrication_id:
            self.client_id = self.fabrication_id.client_id
            self.chantier = self.fabrication_id.chantier
            self.formule_beton_id = self.fabrication_id.formule_beton_id

    def action_depart(self):
        for rec in self:
            rec.state = 'en_cours'

    def action_livrer(self):
        for rec in self:
            rec.state = 'livre'

    def action_annuler(self):
        for rec in self:
            rec.state = 'annule'
