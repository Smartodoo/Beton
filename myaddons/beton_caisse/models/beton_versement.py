from odoo import models, fields, api, _
from odoo.exceptions import UserError

MSG_LECTURE_SEULE = _("Accès refusé : vous avez uniquement un accès en lecture sur les caisses béton.")


class BetonVersement(models.Model):
    _name = 'beton.versement'
    _description = 'Versement Béton'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(string='Référence', readonly=True, default='/', copy=False)
    partner_id = fields.Many2one(
        'res.partner',
        string='Partenaire',
        required=True,
        tracking=True,
    )
    partner_type = fields.Selection(
        related='partner_id.type_partenaire_beton',
        string='Type',
        store=True,
        readonly=True,
    )
    cashbox_id = fields.Many2one(
        'beton.cashbox',
        string='Caisse',
        required=True,
        tracking=True,
    )
    montant = fields.Monetary(
        string='Montant à verser',
        required=True,
        currency_field='currency_id',
        tracking=True,
    )
    date = fields.Date(
        string='Date',
        required=True,
        default=fields.Date.today,
        tracking=True,
    )
    description = fields.Text(string='Objet du versement')

    # Liens optionnels
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Bon de commande',
        domain="[('partner_id', '=', partner_id)]",
    )
    purchase_order_id = fields.Many2one(
        'purchase.order',
        string="Bon d'achat",
        domain="[('partner_id', '=', partner_id)]",
    )

    # Info calculées du partenaire
    montant_total_partenaire = fields.Monetary(
        string='Montant total',
        compute='_compute_partenaire_totals',
        currency_field='currency_id',
    )
    montant_deja_verse = fields.Monetary(
        string='Déjà versé',
        compute='_compute_partenaire_totals',
        currency_field='currency_id',
    )
    montant_credit = fields.Monetary(
        string='Crédit restant',
        compute='_compute_partenaire_totals',
        currency_field='currency_id',
    )

    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('confirmed', 'Confirmé'),
    ], string='État', default='draft', tracking=True)

    # Lien vers l'encaissement/décaissement créé
    entry_id = fields.Many2one('beton.caisse.entry', string='Encaissement créé', readonly=True)
    expense_id = fields.Many2one('beton.caisse.expense', string='Décaissement créé', readonly=True)

    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id,
    )
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company,
        required=True,
    )
    user_id = fields.Many2one(
        'res.users',
        string='Responsable',
        default=lambda self: self.env.user,
        readonly=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.user.has_group('beton_caisse.group_beton_caisse_lecture_seule'):
            raise UserError(MSG_LECTURE_SEULE)
        for vals in vals_list:
            if vals.get('name', '/') in (False, '/', ''):
                vals['name'] = self.env['ir.sequence'].next_by_code('beton.versement') or '/'
        return super().create(vals_list)

    def write(self, vals):
        if self.env.user.has_group('beton_caisse.group_beton_caisse_lecture_seule'):
            raise UserError(MSG_LECTURE_SEULE)
        return super().write(vals)

    def unlink(self):
        if self.env.user.has_group('beton_caisse.group_beton_caisse_lecture_seule'):
            raise UserError(MSG_LECTURE_SEULE)
        for rec in self:
            if rec.state != 'draft':
                raise UserError("Impossible de supprimer un versement confirmé.")
        return super().unlink()

    @api.depends('partner_id', 'partner_type')
    def _compute_partenaire_totals(self):
        for rec in self:
            if rec.partner_type == 'client':
                entries = self.env['beton.caisse.entry'].search([
                    ('client_id', '=', rec.partner_id.id),
                    ('state', '=', 'approuve'),
                ])
                rec.montant_total_partenaire = sum(entries.mapped('amount'))
                rec.montant_deja_verse = sum(entries.mapped('amount_verse'))
                rec.montant_credit = sum(entries.mapped('amount_residual'))
            elif rec.partner_type == 'fournisseur':
                expenses = self.env['beton.caisse.expense'].search([
                    ('fournisseur', '=', rec.partner_id.id),
                    ('state', '=', 'approuve'),
                ])
                rec.montant_total_partenaire = sum(expenses.mapped('amount'))
                rec.montant_deja_verse = sum(expenses.mapped('amount_verse'))
                rec.montant_credit = sum(expenses.mapped('amount_residual'))
            else:
                rec.montant_total_partenaire = 0
                rec.montant_deja_verse = 0
                rec.montant_credit = 0

    def action_confirm(self):
        for rec in self:
            if rec.state != 'draft':
                continue
            if rec.montant <= 0:
                raise UserError("Le montant doit être supérieur à zéro.")

            if rec.partner_type == 'client':
                rec._confirm_client_versement()
            elif rec.partner_type == 'fournisseur':
                rec._confirm_fournisseur_versement()
            else:
                raise UserError("Le partenaire doit être de type Client ou Fournisseur.")
            rec.state = 'confirmed'

    def _confirm_client_versement(self):
        """Client verse de l'argent → encaissement dans la caisse."""
        self.ensure_one()
        # Chercher un encaissement existant pour cette vente ou en créer un nouveau
        vals = {
            'cashbox_id': self.cashbox_id.id,
            'client_id': self.partner_id.id,
            'sale_order_id': self.sale_order_id.id if self.sale_order_id else False,
            'amount': self.sale_order_id.amount_total if self.sale_order_id else self.montant,
            'amount_paid': self.montant,
            'description': self.description or 'Versement %s' % self.name,
        }
        # Calculer cumul versé
        existing = self.env['beton.caisse.entry'].search([
            ('client_id', '=', self.partner_id.id),
            ('state', '=', 'approuve'),
        ])
        cumul = sum(existing.mapped('amount_paid'))
        vals['amount_verse'] = cumul + self.montant

        entry = self.env['beton.caisse.entry'].create(vals)
        entry.action_approve()
        self.entry_id = entry.id

    def _confirm_fournisseur_versement(self):
        """On verse de l'argent au fournisseur → décaissement de la caisse."""
        self.ensure_one()
        if self.cashbox_id.total_amount < self.montant:
            raise UserError(
                "Solde insuffisant dans '%s'. Solde : %s"
                % (self.cashbox_id.name, self.cashbox_id.total_amount)
            )
        vals = {
            'cashbox_id': self.cashbox_id.id,
            'fournisseur': self.partner_id.id,
            'purchase_id': self.purchase_order_id.id if self.purchase_order_id else False,
            'amount': self.purchase_order_id.amount_total if self.purchase_order_id else self.montant,
            'amount_paid': self.montant,
            'description': self.description or 'Versement %s' % self.name,
        }
        existing = self.env['beton.caisse.expense'].search([
            ('fournisseur', '=', self.partner_id.id),
            ('state', '=', 'approuve'),
        ])
        cumul = sum(existing.mapped('amount_paid'))
        vals['amount_verse'] = cumul + self.montant

        expense = self.env['beton.caisse.expense'].create(vals)
        expense.action_approve()
        self.expense_id = expense.id

    def action_to_draft(self):
        for rec in self:
            if rec.state != 'confirmed':
                continue
            # Annuler l'encaissement/décaissement lié
            if rec.entry_id:
                rec.entry_id.action_to_draft()
            if rec.expense_id:
                rec.expense_id.action_to_draft()
            rec.state = 'draft'

    def action_preview_report(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': '/report/pdf/beton_caisse.report_beton_versement_template/%s' % self.id,
            'target': 'new',
        }
