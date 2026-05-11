from odoo import api, fields, models


class BetonFormule(models.Model):
    _name = 'beton.formule'
    _description = 'Formule Béton'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'display_name'

    name = fields.Char(string="Désignation", required=True, tracking=True)
    code_formule = fields.Char(string="Code formule", required=True)
    display_name = fields.Char(compute='_compute_display_name', store=True)
    classe_resistance = fields.Selection([
        ('b15', 'B15'),
        ('b20', 'B20'),
        ('b25', 'B25'),
        ('b30', 'B30'),
        ('b35', 'B35'),
        ('b40', 'B40'),
    ], string="Classe de résistance", required=True, tracking=True)
    type_beton = fields.Selection([
        ('bpe', 'BPE'),
        ('banche', 'Béton banché'),
        ('autoplacant', 'Béton autoplaçant'),
        ('fibre', 'Béton fibré'),
        ('autre', 'Autre'),
    ], string="Type de béton")

    # Dosages par m³
    qte_ciment = fields.Float(string="Ciment (kg/m³)")
    qte_sable = fields.Float(string="Sable (kg/m³)")
    qte_gravier1 = fields.Float(string="Gravier 3/8 (kg/m³)")
    qte_gravier2 = fields.Float(string="Gravier 8/15 (kg/m³)")
    qte_gravier3 = fields.Float(string="Gravier 15/25 (kg/m³)")
    qte_eau = fields.Float(string="Eau (L/m³)")
    adjuvant_type = fields.Char(string="Type d'adjuvant")
    adjuvant_dosage = fields.Float(string="Dosage adjuvant (kg/m³)")

    # Performance
    rendement_theorique = fields.Float(string="Rendement théorique (m³)")
    tolerance_dosage = fields.Float(string="Tolérance dosage (%)", default=5.0)
    cout_theorique_m3 = fields.Float(
        string="Coût théorique/m³",
        compute='_compute_cout_theorique',
        store=True,
    )

    # Composants liés aux produits stock
    ligne_composant_ids = fields.One2many(
        'beton.formule.ligne',
        'formule_id',
        string="Composants",
    )

    statut = fields.Selection([
        ('actif', 'Actif'),
        ('archive', 'Archivé'),
    ], string="Statut", default='actif', tracking=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string="Société", default=lambda self: self.env.company)

    @api.depends('code_formule', 'name')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"[{rec.code_formule}] {rec.name}" if rec.code_formule else rec.name

    @api.depends('ligne_composant_ids.cout_total')
    def _compute_cout_theorique(self):
        for rec in self:
            rec.cout_theorique_m3 = sum(rec.ligne_composant_ids.mapped('cout_total'))


class BetonFormuleLigne(models.Model):
    _name = 'beton.formule.ligne'
    _description = 'Ligne de composant formule'

    formule_id = fields.Many2one('beton.formule', string="Formule", ondelete='cascade')
    product_id = fields.Many2one(
        'product.product',
        string="Matière première",
        required=True,
        domain="[('product_tmpl_id.classification_produit', '=', 'matiere_premiere')]",
    )
    quantite = fields.Float(string="Quantité par m³", required=True)
    unite = fields.Char(string="Unité", related='product_id.uom_id.name', readonly=True)
    cout_unitaire = fields.Float(string="Coût unitaire", related='product_id.standard_price', readonly=True)
    cout_total = fields.Float(string="Coût total/m³", compute='_compute_cout_total', store=True)

    @api.depends('quantite', 'cout_unitaire')
    def _compute_cout_total(self):
        for ligne in self:
            ligne.cout_total = ligne.quantite * ligne.cout_unitaire
