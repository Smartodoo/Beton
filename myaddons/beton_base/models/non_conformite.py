from odoo import api, fields, models


class BetonNonConformite(models.Model):
    _name = 'beton.non.conformite'
    _description = 'Non-Conformité'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(string="Numéro NC", readonly=True, default='Nouveau', copy=False)
    date = fields.Date(string="Date", required=True, default=fields.Date.today, tracking=True)
    essai_id = fields.Many2one('beton.essai', string="Essai associé")
    origine = fields.Selection([
        ('production', 'Production'),
        ('livraison', 'Livraison'),
        ('laboratoire', 'Laboratoire'),
        ('client', 'Réclamation client'),
    ], string="Origine", required=True)
    description = fields.Text(string="Description", required=True)
    gravite = fields.Selection([
        ('mineure', 'Mineure'),
        ('majeure', 'Majeure'),
        ('critique', 'Critique'),
    ], string="Gravité", required=True, tracking=True)
    action_corrective = fields.Text(string="Action corrective")
    responsable_id = fields.Many2one('hr.employee', string="Responsable")
    date_traitement = fields.Date(string="Date de traitement")
    traitement = fields.Selection([
        ('oui', 'Traité'),
        ('non', 'Non traité'),
    ], string="Traitement", default='non', tracking=True)
    document_ids = fields.Many2many(
        'ir.attachment', 'beton_nc_ir_attachment_rel',
        'nc_id', 'attachment_id',
        string="Pièces jointes")
    company_id = fields.Many2one('res.company', string="Société", default=lambda self: self.env.company)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nouveau') == 'Nouveau':
                vals['name'] = self.env['ir.sequence'].next_by_code('beton.non.conformite') or 'Nouveau'
        return super().create(vals_list)
