from odoo import models, fields, api, _
from odoo.exceptions import UserError


class BetonNoteFraisReportWizard(models.TransientModel):
    _name = 'beton.note.frais.report.wizard'
    _description = 'Rapport décaissements Notes de frais'

    date_from = fields.Date(
        string='Du',
        required=True,
        default=lambda self: fields.Date.today().replace(day=1),
    )
    date_to = fields.Date(
        string='Au',
        required=True,
        default=fields.Date.today,
    )
    cashbox_id = fields.Many2one('beton.cashbox', string='Caisse')
    employee_id = fields.Many2one('hr.employee', string='Employé')
    expense_sheet_id = fields.Many2one(
        'hr.expense.sheet',
        string='Note de frais',
        domain="[('employee_id', '=', employee_id)] if employee_id else []",
    )
    state = fields.Selection([
        ('all', 'Tous'),
        ('draft', 'Brouillon'),
        ('approuve', 'Approuvé'),
    ], string='État', default='approuve', required=True)

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for wiz in self:
            if wiz.date_from > wiz.date_to:
                raise UserError(_("La date 'Du' doit être inférieure ou égale à la date 'Au'."))

    def _build_domain(self):
        self.ensure_one()
        domain = [
            ('source_type', '=', 'expense_sheet'),
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
        ]
        if self.cashbox_id:
            domain.append(('cashbox_id', '=', self.cashbox_id.id))
        if self.expense_sheet_id:
            domain.append(('expense_sheet_id', '=', self.expense_sheet_id.id))
        elif self.employee_id:
            domain.append(('expense_sheet_id.employee_id', '=', self.employee_id.id))
        if self.state != 'all':
            domain.append(('state', '=', self.state))
        return domain

    def action_print_report(self):
        self.ensure_one()
        records = self.env['beton.caisse.expense'].search(
            self._build_domain(), order='date asc, id asc'
        )
        if not records:
            raise UserError(_(
                "Aucun décaissement note de frais trouvé pour la période et "
                "les filtres sélectionnés."
            ))
        data = {
            'date_from': fields.Date.to_string(self.date_from),
            'date_to': fields.Date.to_string(self.date_to),
            'filter_cashbox': self.cashbox_id.name or _('Toutes'),
            'filter_employee': self.employee_id.name or _('Tous'),
            'filter_sheet': self.expense_sheet_id.name or _('Toutes'),
            'filter_state': dict(self._fields['state'].selection).get(self.state),
            'record_ids': records.ids,
        }
        return self.env.ref(
            'beton_caisse.action_report_beton_note_frais_list'
        ).report_action(records, data=data)

    def action_view_records(self):
        """Affiche la liste filtrée sans imprimer (preview)."""
        self.ensure_one()
        return {
            'name': _('Décaissements Notes de frais (%s → %s)') % (
                self.date_from.strftime('%d/%m/%Y'),
                self.date_to.strftime('%d/%m/%Y'),
            ),
            'type': 'ir.actions.act_window',
            'res_model': 'beton.caisse.expense',
            'view_mode': 'tree,form',
            'domain': self._build_domain(),
            'context': {'create': False},
        }
