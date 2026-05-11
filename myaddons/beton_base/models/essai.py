from odoo import api, fields, models


class BetonEssai(models.Model):
    _name = 'beton.essai'
    _description = 'Essai Béton'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(string="Numéro", readonly=True, default='Nouveau', copy=False)
    date = fields.Date(string="Date de prélèvement", required=True, default=fields.Date.today, tracking=True)
    formule_beton_id = fields.Many2one('mrp.bom', string="Formule béton", required=True)
    fabrication_id = fields.Many2one('mrp.production', string="Ordre de fabrication")
    client_id = fields.Many2one(
        'res.partner',
        string="Client",
        domain="[('type_partenaire_beton', '=', 'client')]",
        context={'default_type_partenaire_beton': 'client', 'default_is_company': True},
    )
    chantier = fields.Char(string="Chantier")
    heure_prelevement = fields.Float(string="Heure de prélèvement")
    temperature_beton = fields.Float(string="Température béton (°C)")

    # Résistances
    resistance_7j = fields.Float(string="Résistance 7 jours (MPa)")
    resistance_14j = fields.Float(string="Résistance 14 jours (MPa)")
    resistance_21j = fields.Float(string="Résistance 21 jours (MPa)")
    resistance_28j = fields.Float(string="Résistance 28 jours (MPa)")

    conforme = fields.Selection([
        ('oui', 'Conforme'),
        ('non', 'Non conforme'),
        ('en_attente', 'En attente'),
    ], string="Conforme", default='en_attente', tracking=True)
    reference_lot = fields.Char(string="Référence lot")
    nom_laboratoire = fields.Char(string="Nom du laboratoire")
    observations = fields.Text(string="Observations")
    document_ids = fields.Many2many(
        'ir.attachment', 'beton_essai_ir_attachment_rel',
        'essai_id', 'attachment_id',
        string="Pièces jointes")
    company_id = fields.Many2one('res.company', string="Société", default=lambda self: self.env.company)

    # Champs Non-Conformité (visibles uniquement quand conforme = 'non')
    nc_description = fields.Text(string="Description de la non-conformité")
    nc_gravite = fields.Selection([
        ('mineure', 'Mineure'),
        ('majeure', 'Majeure'),
        ('critique', 'Critique'),
    ], string="Gravité")
    nc_action_corrective = fields.Text(string="Action corrective")
    nc_responsable_id = fields.Many2one('hr.employee', string="Responsable NC")

    # Lien vers la NC créée automatiquement
    nc_id = fields.Many2one('beton.non.conformite', string="Non-Conformité associée", readonly=True)
    nc_created = fields.Boolean(string="NC créée", default=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nouveau') == 'Nouveau':
                vals['name'] = self.env['ir.sequence'].next_by_code('beton.essai') or 'Nouveau'
        records = super().create(vals_list)
        # Créer la NC automatiquement si conforme = 'non' et champs remplis
        for rec in records:
            if rec.conforme == 'non' and rec.nc_description and rec.nc_gravite:
                rec._create_non_conformite()
        return records

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            # Créer la NC si conforme passe à 'non', champs remplis, et NC pas encore créée
            if rec.conforme == 'non' and rec.nc_description and rec.nc_gravite and not rec.nc_created:
                rec._create_non_conformite()
        return res

    def _create_non_conformite(self):
        """Crée automatiquement une fiche Non-Conformité depuis l'essai."""
        self.ensure_one()
        nc = self.env['beton.non.conformite'].create({
            'date': self.date,
            'essai_id': self.id,
            'origine': 'laboratoire',
            'description': self.nc_description,
            'gravite': self.nc_gravite,
            'action_corrective': self.nc_action_corrective,
            'responsable_id': self.nc_responsable_id.id if self.nc_responsable_id else False,
        })
        self.write({
            'nc_id': nc.id,
            'nc_created': True,
        })
