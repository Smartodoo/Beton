from odoo import api, fields, models
from odoo.exceptions import ValidationError


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    code_equipement = fields.Char(
        string="Code équipement",
        copy=False,
        required=True,
    )
    centrale_id = fields.Many2one('beton.centrale', string="Centrale")
    marque = fields.Char(string="Marque")
    modele_equipement = fields.Char(string="Modèle")
    # effective_date standard renommé via vue en "Date de mise en service"
    heures_fonctionnement = fields.Float(string="Heures de fonctionnement")
    etat_equipement = fields.Selection([
        ('operationnel', 'Opérationnel'),
        ('panne', 'En panne'),
        ('maintenance', 'En maintenance'),
        ('reforme', 'Réformé'),
    ], string="État", default='operationnel', tracking=True)
    site = fields.Char(string="Site")

    _sql_constraints = [
        ('code_equipement_unique', 'UNIQUE(code_equipement)',
         'Le code équipement doit être unique !'),
    ]

    @api.constrains('code_equipement')
    def _check_code_equipement_unique(self):
        for record in self:
            if record.code_equipement:
                duplicate = self.search([
                    ('code_equipement', '=', record.code_equipement),
                    ('id', '!=', record.id),
                ], limit=1)
                if duplicate:
                    raise ValidationError(
                        "Le code équipement '%s' existe déjà !" % record.code_equipement
                    )


class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    # Champs standard Odoo réutilisés (renommés via vue) :
    #   name            → "N° Intervention" (renommé via vue)
    #   request_date    → "Date"
    #   equipment_id    → "Équipement"
    #   maintenance_type → "Type" (préventive/corrective)
    #   description     → "Description panne"
    #   user_id         → "Technicien"
    #   duration        → "Durée" (heures)

    # name = N° d'intervention : attribué par la séquence beton.intervention
    # à la création (le "Nouveau" saisi par défaut est remplacé)
    name = fields.Char(default="Nouveau")

    # Champs supplémentaires (non couverts par le standard) :
    action_realisee = fields.Text(string="Action réalisée")
    piece_ids = fields.One2many(
        'beton.intervention.piece',
        'request_id',
        string="Pièces utilisées",
    )
    cout_intervention = fields.Float(string="Coût intervention")
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    prochaine_echeance = fields.Date(string="Prochaine échéance")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals['name'] == 'Nouveau':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'beton.intervention') or vals.get('name') or '/'
        return super().create(vals_list)


class BetonInterventionPiece(models.Model):
    _name = 'beton.intervention.piece'
    _description = 'Pièce utilisée dans intervention'

    request_id = fields.Many2one('maintenance.request', string="Intervention", ondelete='cascade')
    product_id = fields.Many2one(
        'product.product',
        string="Pièce de rechange",
        required=True,
    )
    quantite = fields.Float(string="Quantité", default=1)
    cout_unitaire = fields.Float(
        string="Coût unitaire",
        compute='_compute_cout_unitaire',
        store=True,
        readonly=False,
    )
    cout_total = fields.Float(string="Coût total", compute='_compute_cout_total', store=True)

    @api.depends('product_id')
    def _compute_cout_unitaire(self):
        for piece in self:
            if piece.product_id:
                piece.cout_unitaire = piece.product_id.standard_price
            else:
                piece.cout_unitaire = 0.0

    @api.depends('quantite', 'cout_unitaire')
    def _compute_cout_total(self):
        for piece in self:
            piece.cout_total = piece.quantite * piece.cout_unitaire
