from odoo import api, fields, models


class BetonChantier(models.Model):
    _name = 'beton.chantier'
    _description = 'Chantier'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'code_chantier desc'

    name = fields.Char(string="Désignation", required=True, tracking=True)
    code_chantier = fields.Char(string="Code chantier", readonly=True, default='Nouveau', copy=False)
    client_id = fields.Many2one(
        'res.partner',
        string="Client",
        required=True,
        domain="[('type_partenaire_beton', '=', 'client')]",
        context={'default_type_partenaire_beton': 'client', 'default_is_company': True},
        tracking=True,
    )
    adresse_chantier = fields.Char(string="Adresse du chantier")
    type_ouvrage = fields.Selection([
        ('batiment', 'Bâtiment'),
        ('pont', 'Pont'),
        ('route', 'Route'),
        ('barrage', 'Barrage'),
        ('infrastructure', 'Infrastructure'),
        ('autre', 'Autre'),
    ], string="Type d'ouvrage")
    volume_total_prevu = fields.Float(string="Volume total prévu (m³)")
    volume_livre = fields.Float(
        string="Volume livré (m³)",
        compute='_compute_volume_livre',
        store=True,
    )
    responsable_chantier_id = fields.Many2one('hr.employee', string="Responsable chantier")
    distance_centrale = fields.Float(string="Distance de la centrale (km)")
    statut = fields.Selection([
        ('en_cours', 'En cours'),
        ('termine', 'Terminé'),
        ('suspendu', 'Suspendu'),
    ], string="Statut", default='en_cours', tracking=True)
    company_id = fields.Many2one('res.company', string="Société", default=lambda self: self.env.company)
    active = fields.Boolean(default=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code_chantier', 'Nouveau') == 'Nouveau':
                vals['code_chantier'] = self.env['ir.sequence'].next_by_code('beton.chantier') or 'Nouveau'
        return super().create(vals_list)

    def _compute_volume_livre(self):
        for chantier in self:
            pickings = self.env['stock.picking'].search([
                ('chantier_id', '=', chantier.id),
                ('picking_type_code', '=', 'outgoing'),
                ('state', '=', 'done'),
            ])
            total = 0.0
            for p in pickings:
                total += sum(p.move_ids.mapped('quantity'))
            chantier.volume_livre = total
