from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    vat_company = fields.Char(string="N.I.F")
    nis = fields.Char(string='N.I.S')
    ai = fields.Char(string='Article d\'imposition')
    company_registry = fields.Char(string="R.C")


class ResPartnerExt(models.Model):
    _inherit = 'res.partner'


    contact_type = fields.Selection(
        [('SUPPLIER', 'Fournisseur'), ('CLIENT', 'Client'), ('SUBCONTRACTOR', 'Sous-traitant')], string='Contact Type',
        default='CLIENT')
    vat = fields.Char(string='N.I.F', index=True,
                      help="The Tax Identification Number. Complete it if the contact is subjected to government taxes. Used in some legal statements.")
    nis = fields.Char(string='N.I.S')
    ai = fields.Char(string='Article d\'imposition')
    company_registry = fields.Char(string='R.C')


class versement_in(models.Model):
    _name = 'versement.in'
    _description = 'Versement Entrant'

    name = fields.Char(string='Référence', required=True, readonly=True, copy=False, default='/')
    amount = fields.Float(string='Montant', required=True)
    date = fields.Date(string='Date', required=True, default=fields.Date.context_today)
    partner_id = fields.Many2one('res.partner', string='Partenaire', required=True)
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('validated', 'Validé'),
    ], string='Statut', default='draft', required=True)

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code('versement.in') or '/'
        return super(versement_in, self).create(vals)

    def action_validate(self):
        for rec in self:
            rec.state = 'validated'
