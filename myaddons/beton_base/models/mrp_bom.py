from odoo import api, fields, models


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    # Champs spécifiques béton ajoutés à la nomenclature standard
    code_formule = fields.Char(string="Code formule")
    classe_resistance = fields.Selection([
        ('b15', 'B15'),
        ('b20', 'B20'),
        ('b25', 'B25'),
        ('b30', 'B30'),
        ('b35', 'B35'),
        ('b40', 'B40'),
    ], string="Classe de résistance", tracking=True)
    type_beton = fields.Selection([
        ('bpe', 'BPE'),
        ('banche', 'Béton banché'),
        ('autoplacant', 'Béton autoplaçant'),
        ('fibre', 'Béton fibré'),
        ('autre', 'Autre'),
    ], string="Type de béton")


    # Performance
    rendement_theorique = fields.Float(string="Rendement théorique (m³)")
    tolerance_dosage = fields.Float(string="Tolérance dosage (%)", default=5.0)
    cout_theorique_m3 = fields.Float(
        string="Coût théorique / m³",
        compute='_compute_cout_theorique_m3',
        store=True,
    )
    statut_formule = fields.Selection([
        ('actif', 'Actif'),
        ('archive', 'Archivé'),
    ], string="Statut formule", default='actif')
    document_ids = fields.Many2many(
        'ir.attachment', 'mrp_bom_ir_attachment_rel',
        'bom_id', 'attachment_id',
        string="Pièces jointes")

    @api.depends('bom_line_ids.product_qty', 'bom_line_ids.product_id')
    def _compute_cout_theorique_m3(self):
        for bom in self:
            total = 0.0
            for line in bom.bom_line_ids:
                total += line.product_qty * line.product_id.standard_price
            bom.cout_theorique_m3 = total
