from odoo import models, fields, api, _
from odoo.exceptions import UserError

MSG_LECTURE_SEULE = _("Accès refusé : vous avez uniquement un accès en lecture sur les caisses béton.")


class BetonCaisseGlobale(models.Model):
    _name = 'beton.caisse.globale'
    _description = 'Dépenses Globales par Partenaire (Béton)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, id desc'
    _rec_name = 'partner_id'

    partner_id = fields.Many2one(
        'res.partner',
        string='Partenaire',
        required=True,
        tracking=True,
    )
    partner_type = fields.Selection([
        ('client', 'Client'),
        ('fournisseur', 'Fournisseur'),
    ], string='Type', required=True, tracking=True)

    date_from = fields.Datetime(
        string='Du',
        compute='_compute_dates',
        store=True,
    )
    date_to = fields.Datetime(
        string='Au',
        compute='_compute_dates',
        store=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Société',
        default=lambda self: self.env.company,
        required=True,
    )
    company_currency_id = fields.Many2one(
        related='company_id.currency_id',
        string='Devise',
    )

    # Lignes liées
    entry_ids = fields.Many2many(
        'beton.caisse.entry',
        string='Encaissements',
    )
    expense_ids = fields.Many2many(
        'beton.caisse.expense',
        string='Décaissements',
    )

    # Totaux
    total_amount = fields.Monetary(
        string='Montant total',
        currency_field='company_currency_id',
        compute='_compute_totals',
        store=True,
    )
    total_paid_amount = fields.Monetary(
        string='Total versé',
        currency_field='company_currency_id',
        compute='_compute_totals',
        store=True,
    )
    total_residual_amount = fields.Monetary(
        string='Reste à payer',
        currency_field='company_currency_id',
        compute='_compute_totals',
        store=True,
    )

    user_id = fields.Many2one(
        'res.users',
        string='Utilisateur',
        default=lambda self: self.env.user,
        readonly=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.user.has_group('beton_caisse.group_beton_caisse_lecture_seule'):
            raise UserError(MSG_LECTURE_SEULE)
        return super().create(vals_list)

    def write(self, vals):
        if self.env.user.has_group('beton_caisse.group_beton_caisse_lecture_seule'):
            raise UserError(MSG_LECTURE_SEULE)
        return super().write(vals)

    def unlink(self):
        if self.env.user.has_group('beton_caisse.group_beton_caisse_lecture_seule'):
            raise UserError(MSG_LECTURE_SEULE)
        return super().unlink()

    @api.depends('entry_ids', 'expense_ids', 'entry_ids.date', 'expense_ids.date')
    def _compute_dates(self):
        for rec in self:
            dates = []
            if rec.partner_type == 'client' and rec.entry_ids:
                dates = rec.entry_ids.mapped('date')
            elif rec.partner_type == 'fournisseur' and rec.expense_ids:
                dates = rec.expense_ids.mapped('date')
            if dates:
                rec.date_from = min(dates)
                rec.date_to = max(dates)
            else:
                rec.date_from = False
                rec.date_to = False

    @api.depends(
        'entry_ids', 'entry_ids.amount', 'entry_ids.amount_verse', 'entry_ids.amount_residual', 'entry_ids.state',
        'expense_ids', 'expense_ids.amount', 'expense_ids.amount_verse', 'expense_ids.amount_residual', 'expense_ids.state',
    )
    def _compute_totals(self):
        for rec in self:
            total = paid = residual = 0.0
            if rec.partner_type == 'client':
                for line in rec.entry_ids.filtered(lambda l: l.state == 'approuve'):
                    total += line.amount
                    paid += line.amount_verse
                    residual += line.amount_residual
            elif rec.partner_type == 'fournisseur':
                for line in rec.expense_ids.filtered(lambda l: l.state == 'approuve'):
                    total += line.amount
                    paid += line.amount_verse
                    residual += line.amount_residual
            rec.total_amount = total
            rec.total_paid_amount = paid
            rec.total_residual_amount = residual

    def action_preview_report(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': '/report/pdf/beton_caisse.report_beton_globale_template/%s' % self.id,
            'target': 'new',
        }

    def action_preview_report_multi(self):
        if not self:
            raise UserError("Veuillez sélectionner au moins un enregistrement.")
        ids_str = ','.join(str(r.id) for r in self)
        return {
            'type': 'ir.actions.act_url',
            'url': '/report/pdf/beton_caisse.report_beton_globale_template/%s' % ids_str,
            'target': 'new',
        }
