from odoo import fields, models, api


class Sinistre(models.Model):
    _name = 'sinistre'
    _description = 'sinistre'
    _order = 'date_accident desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    user_id = fields.Many2one('res.users', string="Utilisateur actuel", default=lambda self: self.env.user)
    model_id = fields.Many2one('fleet.vehicle.model', 'Model', tracking=True, required=True)
    license_plate = fields.Char(tracking=True, string="Plaque d'immatriculation",
                                help="Numéro de plaque d'immatriculation du véhicule")
    date_accident = fields.Date("Date de l'accident", help="Date de l'accident")
    agence_assurance1 = fields.Many2one('res.partner', "Agence d'assurance", tracking=True, help="Agence d'assurance",
                                        domain=[('contact_type', '=', 'SUPPLIER'), ])
    numero_police = fields.Char('Numéro de police', tracking=True, help='Numéro de police')

    driver_id = fields.Many2one('res.partner', 'Conducteur', tracking=True, help='Adresse du conducteur du véhicule',
                                copy=False)

    accident_type = fields.Selection([('tiers', 'Avec adversaire'), ('sans', 'Sans adversaire')],
                                     string="Type d'accident",
                                     default='sans', tracking=True, help="type d'accident")
    nom_tiers = fields.Char('Nom complet du tiers', tracking=True, help='Nom du tiers')
    prenom_tiers = fields.Char('Adresse du tiers', tracking=True, help='Prenom du tiers')
    agence_assurance2 = fields.Char('Agence dassurance', tracking=True, help="Agence d'assurance")
    degat_sur_vehicule = fields.Char('Degat sur vehicule', tracking=True, help='Degat sur vehicule')
    date_expertise = fields.Date('Date dexpertisé', help="Date d'expertisé")
    nom_expert = fields.Char("Nom de l'expert", tracking=True, help="Nom de l'expert")
    numero_cloque = fields.Integer('Numéro de chéque', tracking=True, help='Numéro de chéque')
    date_reparation = fields.Date('Date de payment', help="Date de payment")
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.company.currency_id)
    montant_reparation = fields.Monetary('Montant', currency_field='currency_id', tracking=True,
                                         help='Montant')
    degat_sur_vehicule1 = fields.Char('Degat sur vehicule', tracking=True, help='Degat sur vehicule')
    degat_sur_vehicule2 = fields.Html('Degat sur vehicule', help='Degat sur vehicule')
    degat_sur_vehicule_html = fields.Html('Degat sur vehicule', help='Degat sur vehicule')
    numero_pv = fields.Char('Numéro de PV', tracking=True, help='Numéro de PV')
    payment_state = fields.Selection([
        ('payé', 'Régler'),
        ('pas_payé', 'Non régler')
    ], string='État du réglement', default='pas_payé')

    accident_type = fields.Selection([('tiers', 'Avec adversaire'), ('sans', 'Sans adversaire')],
                                     string="Type d'accident",
                                     default='sans', tracking=True, help="type d'accident")
    technical_file = fields.Many2many('ir.attachment', string="Téléchargez vos constats", tracking=True)
    technical_file_name = fields.Char(string='Nom du Fichier', tracking=True)
    state = fields.Selection([('draft', 'En Attente de PV'), ('en_cours', 'En cours'), ('termine', 'Clôturé')],
                             string='État', tracking=True, help="État du sinistre", readonly=False, default='draft')

    date_effet = fields.Date('Date d\'effet', tracking=True, help="Date d'effet du sinistre")
    date_expertation = fields.Date('Date d\'expertation', tracking=True, help="Date d'expertation du sinistre")
    assurence = fields.Char("Compagnie d'assurance", tracking=True, help="Assurance du sinistre")
    assurence2 = fields.Char("Compagnie d'assurance", tracking=True, help="Assurance du sinistre")
    date_effet_1 = fields.Date('Date d\'effet', tracking=True, help="Date d'effet du sinistre")
    date_expertation_1 = fields.Date('Date d\'expertation', tracking=True, help="Date d'expertation du sinistre")
    # numero_police = fields.Char('Numéro de police', tracking=True, help='Numéro de police')
    numero_police2 = fields.Char('Numéro de police', tracking=True, help='Numéro de police')
    numero_sinistre = fields.Char('Numéro de sinistre', tracking=True, help='Numéro de sinistre')
    numero_serie = fields.Char('Numéro de série', tracking=True, help='Numéro de série du véhicule')

    @api.onchange('model_id')
    def _onchange_model_id(self):
        if self.model_id:
            related_service = self.env['fleet.vehicle'].search([
                ('model_id', '=', self.model_id.id)], limit=1)
            if related_service:

                self.license_plate = related_service.license_plate
                self.driver_id = related_service.driver_id
                print(related_service)
                service_assurance_related = self.env['fleet.vehicle.log.services'].search([
                    ('vehicle_id', '=', related_service.id),
                    ('service_type_id', '=', 'Assurance')
                ], limit=1)
                print(service_assurance_related)
                if service_assurance_related:

                    self.agence_assurance1 = service_assurance_related.vendor_id.id
                    self.numero_police = service_assurance_related.n_police
                    print(service_assurance_related.vendor_id)
                else:

                    self.agence_assurance1 = ""
                    self.numero_police = 0

    @api.onchange('montant_reparation')
    def _onchange_montant_reparation(self):
        if self.montant_reparation != 0:
            self.payment_state = 'payé'
        elif self.montant_reparation == 0:
            self.payment_state = 'pas_payé'


class FleetVhicleModelInherit(models.Model):
    _inherit = 'fleet.vehicle.model'

    vehicle_type_1 = fields.Many2one('vehicle.type', string='Type de véhicule', required=True)

    def update_old_record_with_vehicle_type(self):
        for rec in self:
            if rec.vehicle_type:
                if rec.vehicle_type == 'car':
                    vehicle_type = self.env['vehicle.type'].search([('name', '=', 'Voiture')]).id
                    if vehicle_type:
                        rec.vehicle_type_1 = vehicle_type
                else:
                    vehicle_type = self.env['vehicle.type'].search([('name', '=', 'Vélo')]).id
                    if vehicle_type:
                        rec.vehicle_type_1 = vehicle_type


class VehicleType(models.Model):
    _name = 'vehicle.type'
    _description = 'Type de véhicule'

    name = fields.Char(string='Type de véhicule', help='Type de véhicule')


