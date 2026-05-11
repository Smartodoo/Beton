from odoo import api, fields, models


class BetonCoutRevient(models.Model):
    _name = 'beton.cout.revient'
    _description = 'Coût de Revient m³'
    _inherit = ['mail.thread']

    name = fields.Char(string="Référence", compute='_compute_name', store=True)
    formule_beton_id = fields.Many2one('mrp.bom', string="Formule béton", required=True)
    periode = fields.Date(string="Période")
    matiere_ligne_ids = fields.One2many(
        'beton.cout.matiere.ligne',
        'cout_revient_id',
        string="Coûts matières premières",
    )
    cout_matieres = fields.Float(
        string="Total matières premières",
        compute='_compute_cout_matieres',
        store=True,
    )
    cout_transport = fields.Float(string="Coût transport")
    cout_maintenance = fields.Float(string="Coût maintenance")
    cout_energie = fields.Float(string="Coût énergie")
    cout_main_oeuvre = fields.Float(string="Coût main d'œuvre")
    cout_total_m3 = fields.Float(
        string="Coût total / m³",
        compute='_compute_cout_total',
        store=True,
    )
    prix_vente_m3 = fields.Float(string="Prix de vente / m³")
    marge_brute = fields.Float(
        string="Marge brute (%)",
        compute='_compute_marge',
        store=True,
    )
    document_ids = fields.Many2many(
        'ir.attachment', 'beton_cout_revient_ir_attachment_rel',
        'cout_revient_id', 'attachment_id',
        string="Pièces jointes")
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    company_id = fields.Many2one('res.company', string="Société", default=lambda self: self.env.company)

    @api.depends('formule_beton_id', 'periode')
    def _compute_name(self):
        for rec in self:
            formule = rec.formule_beton_id.code_formule or rec.formule_beton_id.code or ''
            periode = rec.periode.strftime('%m/%Y') if rec.periode else ''
            rec.name = f"CR - {formule} - {periode}" if formule else 'Nouveau'

    @api.depends('matiere_ligne_ids.sous_total')
    def _compute_cout_matieres(self):
        for rec in self:
            rec.cout_matieres = sum(rec.matiere_ligne_ids.mapped('sous_total'))

    @api.depends('cout_matieres', 'cout_transport', 'cout_maintenance', 'cout_energie', 'cout_main_oeuvre')
    def _compute_cout_total(self):
        for rec in self:
            rec.cout_total_m3 = (
                rec.cout_matieres + rec.cout_transport + rec.cout_maintenance
                + rec.cout_energie + rec.cout_main_oeuvre
            )

    @api.depends('cout_total_m3', 'prix_vente_m3')
    def _compute_marge(self):
        for rec in self:
            if rec.prix_vente_m3:
                rec.marge_brute = ((rec.prix_vente_m3 - rec.cout_total_m3) / rec.prix_vente_m3) * 100
            else:
                rec.marge_brute = 0.0

    @api.onchange('formule_beton_id')
    def _onchange_formule_beton_id(self):
        self.matiere_ligne_ids = [(5, 0, 0)]
        if self.formule_beton_id:
            lines = []
            for line in self.formule_beton_id.bom_line_ids:
                lines.append((0, 0, {
                    'product_id': line.product_id.id,
                    'quantite': line.product_qty,
                    'cout_unitaire': line.product_id.standard_price,
                }))
            self.matiere_ligne_ids = lines


class BetonCoutMatiereLigne(models.Model):
    _name = 'beton.cout.matiere.ligne'
    _description = 'Ligne coût matière première'

    cout_revient_id = fields.Many2one('beton.cout.revient', string="Coût de revient", ondelete='cascade')
    product_id = fields.Many2one('product.product', string="Matière première", readonly=True)
    quantite = fields.Float(string="Quantité / m³", readonly=True)
    cout_unitaire = fields.Float(string="Coût unitaire", readonly=True)
    sous_total = fields.Float(string="Sous-total", compute='_compute_sous_total', store=True)

    @api.depends('quantite', 'cout_unitaire')
    def _compute_sous_total(self):
        for line in self:
            line.sous_total = line.quantite * line.cout_unitaire
