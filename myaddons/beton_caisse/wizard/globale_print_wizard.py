from odoo import models, fields, api


class BetonGlobalePrintWizard(models.TransientModel):
    _name = 'beton.globale.print.wizard'
    _description = 'Assistant Impression Dépenses Globales Béton'

    globale_id = fields.Many2one(
        'beton.caisse.globale',
        string='Dépense Globale',
        required=True,
    )
    date_from = fields.Date(string='De', required=True)
    date_to = fields.Date(string='Au', required=True)
    partner_id = fields.Many2one(
        'res.partner',
        string='Partenaire',
        related='globale_id.partner_id',
        readonly=True,
    )
    partner_type = fields.Selection(
        related='globale_id.partner_type',
        readonly=True,
    )
    company_id = fields.Many2one(
        related='globale_id.company_id',
        readonly=True,
    )
    company_currency_id = fields.Many2one(
        related='globale_id.company_currency_id',
        readonly=True,
    )

    # Paiements filtrés
    entry_ids = fields.Many2many(
        'beton.caisse.entry',
        compute='_compute_payments',
    )
    expense_ids = fields.Many2many(
        'beton.caisse.expense',
        compute='_compute_payments',
    )

    @api.depends('globale_id', 'date_from', 'date_to')
    def _compute_payments(self):
        for wizard in self:
            if wizard.partner_type == 'client':
                wizard.entry_ids = wizard.globale_id.entry_ids.filtered(
                    lambda l: l.state == 'approuve'
                    and l.date.date() >= wizard.date_from
                    and l.date.date() <= wizard.date_to
                )
                wizard.expense_ids = False
            else:
                wizard.expense_ids = wizard.globale_id.expense_ids.filtered(
                    lambda l: l.state == 'approuve'
                    and l.date.date() >= wizard.date_from
                    and l.date.date() <= wizard.date_to
                )
                wizard.entry_ids = False

    # Totaux calculés
    total_amount = fields.Monetary(
        compute='_compute_totals',
        currency_field='company_currency_id',
    )
    total_paid = fields.Monetary(
        compute='_compute_totals',
        currency_field='company_currency_id',
    )
    total_residual = fields.Monetary(
        compute='_compute_totals',
        currency_field='company_currency_id',
    )

    @api.depends('entry_ids', 'expense_ids')
    def _compute_totals(self):
        for wizard in self:
            records = wizard.entry_ids or wizard.expense_ids
            wizard.total_amount = sum(records.mapped('amount'))
            wizard.total_paid = sum(records.mapped('amount_verse'))
            wizard.total_residual = sum(records.mapped('amount_residual'))

    def action_preview_report(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': '/report/pdf/beton_caisse.report_beton_partner_payments_template/%s' % self.id,
            'target': 'new',
        }

    def action_print_report(self):
        self.ensure_one()
        return self.env.ref('beton_caisse.action_report_beton_partner_payments').report_action(self)
