from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # === Chauffeur ===
    is_chauffeur = fields.Boolean(string="Est un chauffeur")

    # === Champs Client Béton ===
    is_client_beton = fields.Boolean(string="Client Béton")
    code_client = fields.Char(string="Code Client", readonly=True, copy=False)
    code_fournisseur = fields.Char(string="Code Fournisseur", readonly=True, copy=False)
    type_partenaire_beton = fields.Selection([
        ('client', 'Client'),
        ('fournisseur', 'Fournisseur'),
    ], string="Client / Fournisseur")
    type_client_ie = fields.Selection([
        ('interne', 'Interne'),
        ('externe', 'Externe'),
    ], string="Type client")
    type_client_beton = fields.Selection([
        ('particulier', 'Particulier'),
        ('entreprise', 'Entreprise'),
    ], string="Type de client")
    classification_client = fields.Selection([
        ('vip', 'VIP'),
        ('standard', 'Standard'),
        ('occasionnel', 'Occasionnel'),
    ], string="Classification client")
    classification_fournisseur = fields.Selection([
        ('strategique', 'Stratégique'),
        ('standard', 'Standard'),
        ('occasionnel', 'Occasionnel'),
    ], string="Classification fournisseur")
    mode_paiement_beton = fields.Selection([
        ('comptant', 'Comptant'),
        ('credit', 'Crédit'),
        ('cheque', 'Chèque'),
    ], string="Mode de paiement")
    plafond_credit = fields.Float(string="Plafond crédit")
    statut_client_beton = fields.Selection([
        ('actif', 'Actif'),
        ('bloque', 'Bloqué'),
        ('archive', 'Archivé'),
    ], string="Statut client", default='actif')
    satisfaction_client = fields.Selection([
        ('tres_satisfait', 'Très satisfait'),
        ('satisfait', 'Satisfait'),
        ('neutre', 'Neutre'),
        ('insatisfait', 'Insatisfait'),
    ], string="Satisfaction client")

    # === Coordonnées ===
    fax = fields.Char(string="Fax")

    # === Coordonnées Fiscales ===
    rc = fields.Char(string="RC")
    nis = fields.Char(string="NIS")
    nif = fields.Char(string="NIF")
    ai = fields.Char(string="AI")

    # === Coordonnées bancaires ===
    rib = fields.Char(string="RIB")

    # === Champs Chantier Béton ===
    is_chantier_beton = fields.Boolean(string="Chantier Béton")
    code_chantier = fields.Char(string="Code chantier", readonly=True, copy=False)
    client_chantier_id = fields.Many2one(
        'res.partner',
        string="Client du chantier",
        domain="[('type_partenaire_beton', '=', 'client')]",
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
    statut_chantier = fields.Selection([
        ('en_cours', 'En cours'),
        ('termine', 'Terminé'),
        ('suspendu', 'Suspendu'),
    ], string="Statut chantier", default='en_cours')

    def _compute_volume_livre(self):
        for partner in self:
            if partner.is_chantier_beton:
                pickings = self.env['stock.picking'].search([
                    ('chantier_id', '=', partner.id),
                    ('picking_type_code', '=', 'outgoing'),
                    ('state', '=', 'done'),
                ])
                total = 0.0
                for p in pickings:
                    total += sum(p.move_ids.mapped('quantity'))
                partner.volume_livre = total
            else:
                partner.volume_livre = 0.0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('is_chantier_beton') and not vals.get('code_chantier'):
                vals['code_chantier'] = self.env['ir.sequence'].next_by_code('beton.chantier') or ''
            if (
                vals.get('type_partenaire_beton') == 'client'
                and not vals.get('code_client')
            ):
                vals['code_client'] = self.env['ir.sequence'].next_by_code('beton.client') or ''
            if (
                vals.get('type_partenaire_beton') == 'fournisseur'
                and not vals.get('code_fournisseur')
            ):
                vals['code_fournisseur'] = self.env['ir.sequence'].next_by_code('beton.fournisseur') or ''
        return super().create(vals_list)

    def write(self, vals):
        res = super().write(vals)
        if vals.get('is_chantier_beton'):
            for partner in self:
                if not partner.code_chantier:
                    partner.code_chantier = self.env['ir.sequence'].next_by_code('beton.chantier') or ''
        if vals.get('type_partenaire_beton') == 'client':
            for partner in self:
                if not partner.code_client:
                    partner.code_client = self.env['ir.sequence'].next_by_code('beton.client') or ''
        if vals.get('type_partenaire_beton') == 'fournisseur':
            for partner in self:
                if not partner.code_fournisseur:
                    partner.code_fournisseur = self.env['ir.sequence'].next_by_code('beton.fournisseur') or ''
        return res
