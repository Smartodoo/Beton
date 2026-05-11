from odoo import models, fields, api, _
from odoo.exceptions import UserError

MSG_LECTURE_SEULE = _("Accès refusé : vous avez uniquement un accès en lecture sur les caisses béton.")


class BetonCashbox(models.Model):
    _name = 'beton.cashbox'
    _description = 'Caisse Béton'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'type, name'

    name = fields.Char(string='Nom', required=True, tracking=True)
    type = fields.Selection([
        ('principale', 'Caisse Principale'),
        ('secondaire', 'Caisse Secondaire'),
        ('banque', 'Caisse Banque'),
    ], string='Type', required=True, default='principale', tracking=True)
    active = fields.Boolean(default=True)
    total_amount = fields.Monetary(
        string='Solde',
        currency_field='company_currency_id',
        tracking=True,
    )
    responsible_ids = fields.Many2many(
        'res.users',
        'beton_cashbox_responsible_rel',
        string='Responsables',
        required=True,
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
    notes = fields.Text(string='Notes')

    # Relations
    entry_ids = fields.One2many('beton.caisse.entry', 'cashbox_id', string='Encaissements')
    expense_ids = fields.One2many('beton.caisse.expense', 'cashbox_id', string='Décaissements')
    transfer_source_ids = fields.One2many('beton.caisse.transfer', 'source_cashbox_id', string='Transferts sortants')
    transfer_dest_ids = fields.One2many('beton.caisse.transfer', 'destination_cashbox_id', string='Transferts entrants')
    recharge_ids = fields.One2many('beton.cashbox.recharge', 'cashbox_id', string='Recharges')

    # Compteurs
    entry_count = fields.Integer(compute='_compute_counts')
    expense_count = fields.Integer(compute='_compute_counts')
    transfer_count = fields.Integer(compute='_compute_counts')
    recharge_count = fields.Integer(compute='_compute_counts')

    _sql_constraints = [
        ('name_uniq', 'unique(name, company_id)', 'Le nom de la caisse doit être unique par société.'),
    ]

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

    def _compute_counts(self):
        for rec in self:
            rec.entry_count = len(rec.entry_ids)
            rec.expense_count = len(rec.expense_ids)
            rec.transfer_count = len(rec.transfer_source_ids) + len(rec.transfer_dest_ids)
            rec.recharge_count = len(rec.recharge_ids)

    def action_view_entries(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Encaissements',
            'res_model': 'beton.caisse.entry',
            'view_mode': 'tree,form',
            'domain': [('cashbox_id', '=', self.id)],
            'context': {'default_cashbox_id': self.id},
        }

    def action_view_expenses(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Décaissements',
            'res_model': 'beton.caisse.expense',
            'view_mode': 'tree,form',
            'domain': [('cashbox_id', '=', self.id)],
            'context': {'default_cashbox_id': self.id},
        }

    def action_view_transfers(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Transferts',
            'res_model': 'beton.caisse.transfer',
            'view_mode': 'tree,form',
            'domain': [
                '|',
                ('source_cashbox_id', '=', self.id),
                ('destination_cashbox_id', '=', self.id),
            ],
        }

    def action_view_recharges(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Recharges',
            'res_model': 'beton.cashbox.recharge',
            'view_mode': 'tree,form',
            'domain': [('cashbox_id', '=', self.id)],
        }

    def action_recharge(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Enrichir la caisse',
            'res_model': 'beton.cashbox.recharge.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_cashbox_id': self.id},
        }

    def action_archive(self):
        for rec in self:
            if rec.total_amount != 0:
                raise UserError("Impossible d'archiver une caisse dont le solde n'est pas à zéro.")
        self.write({'active': False})

    def action_repair_cumul_verse(self):
        """Recalcule le champ 'amount_verse' (Cumul versé) pour tous les
        encaissements et décaissements approuvés. À utiliser une seule fois
        pour réparer les données impactées par l'ancien bug de double comptage."""
        Entry = self.env['beton.caisse.entry'].sudo()
        Expense = self.env['beton.caisse.expense'].sudo()

        # Réparer les encaissements (groupés par sale_order ou client)
        entries = Entry.search([('state', '=', 'approuve')], order='date asc, id asc')
        cumul_by_key = {}
        for entry in entries:
            if entry.sale_order_id:
                key = ('so', entry.sale_order_id.id)
                effective = entry.amount_paid
            elif entry.client_id:
                key = ('client', entry.client_id.id)
                effective = entry.amount_paid or entry.amount
            else:
                entry.amount_verse = entry.amount_paid or entry.amount
                continue
            cumul = cumul_by_key.get(key, 0.0) + effective
            entry.amount_verse = cumul
            cumul_by_key[key] = cumul

        # Réparer les décaissements (groupés par purchase ou fournisseur)
        expenses = Expense.search([('state', '=', 'approuve')], order='date asc, id asc')
        cumul_by_key = {}
        for expense in expenses:
            if expense.purchase_id:
                key = ('po', expense.purchase_id.id)
            elif expense.fournisseur:
                key = ('fournisseur', expense.fournisseur.id)
            else:
                expense.amount_verse = expense.amount_paid
                continue
            cumul = cumul_by_key.get(key, 0.0) + expense.amount_paid
            expense.amount_verse = cumul
            cumul_by_key[key] = cumul

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Réparation terminée',
                'message': "Cumul versé recalculé : %d encaissements, %d décaissements."
                           % (len(entries), len(expenses)),
                'type': 'success',
                'sticky': False,
            }
        }
