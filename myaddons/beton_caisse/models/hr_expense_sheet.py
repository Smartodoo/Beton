from odoo import models, fields, api, _


class HrExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'

    beton_expense_ids = fields.One2many(
        'beton.caisse.expense',
        'expense_sheet_id',
        string='Paiements Caisse Béton',
    )
    beton_payment_count = fields.Integer(
        compute='_compute_beton_payment_info',
    )
    beton_amount_paid = fields.Monetary(
        compute='_compute_beton_payment_info',
        currency_field='currency_id',
    )
    beton_amount_residual = fields.Monetary(
        compute='_compute_beton_payment_info',
        currency_field='currency_id',
    )
    beton_is_fully_paid = fields.Boolean(
        compute='_compute_beton_payment_info',
    )
    beton_payment_state = fields.Selection([
        ('not_paid', 'Non payé'),
        ('partial', 'Partiel'),
        ('paid', 'Payé'),
    ], compute='_compute_beton_payment_info')

    @api.depends('beton_expense_ids.state', 'beton_expense_ids.amount_paid', 'total_amount')
    def _compute_beton_payment_info(self):
        for sheet in self:
            approved = sheet.beton_expense_ids.filtered(lambda e: e.state == 'approuve')
            total_paid = sum(approved.mapped('amount_paid'))
            total = sheet.total_amount or 0.0
            sheet.beton_payment_count = len(approved)
            sheet.beton_amount_paid = total_paid
            sheet.beton_amount_residual = max(total - total_paid, 0.0)
            sheet.beton_is_fully_paid = bool(total) and total_paid >= total
            if total_paid <= 0:
                sheet.beton_payment_state = 'not_paid'
            elif sheet.beton_is_fully_paid:
                sheet.beton_payment_state = 'paid'
            else:
                sheet.beton_payment_state = 'partial'

    def _get_default_beton_cashbox(self):
        cashbox = self.env['beton.cashbox'].search([
            ('type', '=', 'principale'),
            ('responsible_ids', 'in', self.env.user.id),
        ], limit=1)
        if not cashbox:
            cashbox = self.env['beton.cashbox'].search([
                ('type', '=', 'principale'),
            ], limit=1)
        return cashbox

    def action_register_payment(self):
        """Pré-remplit la caisse béton dans le wizard de paiement."""
        cashbox = self._get_default_beton_cashbox()
        action = super().action_register_payment()
        if cashbox:
            ctx = dict(action.get('context') or {})
            ctx['default_beton_cashbox_id'] = cashbox.id
            action['context'] = ctx
        return action

    def action_sheet_move_create(self):
        """Force le flux 'own_account' pour TOUTES les notes de frais
        (employé ET société) : on bascule temporairement les expenses en
        own_account pour que le natif crée un bill (au lieu d'un paiement
        auto-créé pour company_account). L'utilisateur clique ensuite
        'Enregistrer un paiement' pour choisir caisse + mode + chèque."""
        company_expenses = self.expense_line_ids.filtered(
            lambda e: e.payment_mode == 'company_account'
        )
        if company_expenses:
            company_expenses.write({'payment_mode': 'own_account'})
        try:
            return super().action_sheet_move_create()
        finally:
            if company_expenses:
                # Restaure le mode 'company_account' sur les expenses ; le bill
                # est déjà créé/posté et ne sera pas affecté. Le compute override
                # ci-dessous neutralise la logique native qui marquerait le sheet
                # comme 'paid' à cause du mode company_account.
                company_expenses.write({'payment_mode': 'company_account'})

    @api.depends('account_move_ids.payment_state', 'account_move_ids.amount_residual')
    def _compute_from_account_move_ids(self):
        """Override : neutralise la logique native qui marque automatiquement
        un sheet 'company_account' comme 'paid' dès qu'un move existe.
        Comme beton_caisse force la création d'un bill pour les deux modes,
        l'état de paiement est calculé depuis le bill, comme en mode own_account."""
        for sheet in self:
            if sheet.account_move_ids:
                sheet.amount_residual = sum(sheet.account_move_ids.mapped('amount_residual'))
                sheet.payment_state = sheet.account_move_ids[:1].payment_state
            else:
                sheet.amount_residual = 0.0
                sheet.payment_state = 'not_paid'

    def action_view_beton_payments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Paiements Caisse Béton'),
            'res_model': 'beton.caisse.expense',
            'view_mode': 'tree,form',
            'domain': [('expense_sheet_id', '=', self.id)],
            'context': {'search_default_expense_sheet_id': self.id},
        }
