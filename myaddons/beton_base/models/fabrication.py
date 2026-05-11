from odoo import api, fields, models
from odoo.exceptions import UserError


class BetonFabrication(models.Model):
    _name = 'beton.fabrication'
    _description = 'Ordre de Fabrication'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(string="Numéro", readonly=True, default='Nouveau', copy=False)
    date = fields.Date(string="Date", required=True, default=fields.Date.today, tracking=True)
    centrale_id = fields.Many2one('beton.centrale', string="Centrale", required=True)
    formule_beton_id = fields.Many2one(
        'beton.formule',
        string="Formule béton",
        required=True,
        domain="[('statut', '=', 'actif')]",
    )
    client_id = fields.Many2one(
        'res.partner',
        string="Client",
        required=True,
        domain="[('type_partenaire_beton', '=', 'client')]",
        context={'default_type_partenaire_beton': 'client', 'default_is_company': True},
    )
    chantier = fields.Char(string="Chantier")
    destination = fields.Char(string="Destination")
    distance = fields.Float(string="Distance (km)")

    # Quantités
    nombre_camion = fields.Integer(string="Nombre de camions")
    qte_demandee = fields.Float(string="Quantité demandée (m³)", required=True)
    qte_produite = fields.Float(string="Quantité produite (m³)")
    ecart_production = fields.Float(
        string="Écart (m³)",
        compute='_compute_ecart',
        store=True,
    )
    nombre_gachees = fields.Integer(string="Nombre de gâchées")

    # Timing
    operateur_id = fields.Many2one('hr.employee', string="Opérateur")
    heure_debut = fields.Float(string="Heure début")
    heure_fin = fields.Float(string="Heure fin")

    # State
    state = fields.Selection([
        ('prevu', 'Prévu'),
        ('en_cours', 'En cours'),
        ('termine', 'Terminé'),
        ('annule', 'Annulé'),
    ], string="Statut", default='prevu', tracking=True)

    # Consommations
    consommation_ids = fields.One2many(
        'beton.consommation.ligne',
        'fabrication_id',
        string="Consommations matières",
    )

    company_id = fields.Many2one('res.company', string="Société", default=lambda self: self.env.company)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nouveau') == 'Nouveau':
                vals['name'] = self.env['ir.sequence'].next_by_code('beton.fabrication') or 'Nouveau'
        return super().create(vals_list)

    @api.depends('qte_demandee', 'qte_produite')
    def _compute_ecart(self):
        for rec in self:
            rec.ecart_production = rec.qte_produite - rec.qte_demandee

    def action_generer_consommations(self):
        """Génère les lignes de consommation depuis la formule béton."""
        for fab in self:
            if not fab.formule_beton_id.ligne_composant_ids:
                raise UserError("La formule sélectionnée n'a pas de composants définis.")
            # Supprimer les anciennes lignes
            fab.consommation_ids.unlink()
            # Créer les nouvelles lignes
            for ligne in fab.formule_beton_id.ligne_composant_ids:
                self.env['beton.consommation.ligne'].create({
                    'fabrication_id': fab.id,
                    'product_id': ligne.product_id.id,
                    'qte_theorique': ligne.quantite * fab.qte_demandee,
                    'qte_reelle': 0.0,
                })

    def action_demarrer(self):
        """Passer à l'état 'En cours' et générer les consommations."""
        for fab in self:
            fab.action_generer_consommations()
            fab.state = 'en_cours'

    def action_terminer(self):
        """Terminer la fabrication et créer les mouvements de stock (sortie)."""
        for fab in self:
            if fab.qte_produite <= 0:
                raise UserError("Veuillez renseigner la quantité produite avant de terminer.")
            # Créer les mouvements de stock pour chaque consommation
            for cons in fab.consommation_ids:
                if cons.qte_reelle > 0:
                    self.env['stock.move'].create({
                        'name': f"Consommation {fab.name} - {cons.product_id.name}",
                        'product_id': cons.product_id.id,
                        'product_uom_qty': cons.qte_reelle,
                        'product_uom': cons.product_id.uom_id.id,
                        'location_id': fab.centrale_id.warehouse_id.lot_stock_id.id if fab.centrale_id.warehouse_id else self.env.ref('stock.stock_location_stock').id,
                        'location_dest_id': self.env.ref('stock.stock_location_customers').id,
                        'origin': fab.name,
                        'company_id': fab.company_id.id,
                    })._action_confirm()
            fab.state = 'termine'

    def action_annuler(self):
        for fab in self:
            fab.state = 'annule'

    def action_remettre_prevu(self):
        for fab in self:
            fab.state = 'prevu'
