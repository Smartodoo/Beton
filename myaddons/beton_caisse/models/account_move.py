from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    beton_source_fully_paid = fields.Boolean(
        string='Source payée via Caisse Béton',
        compute='_compute_beton_source_fully_paid',
        help="Vrai si tous les bons (ventes/achats) liés à cette facture "
             "sont totalement payés via la caisse béton.",
    )

    @api.depends(
        'invoice_line_ids.sale_line_ids.order_id.beton_is_fully_paid',
        'invoice_line_ids.purchase_line_id.order_id.beton_is_fully_paid',
    )
    def _compute_beton_source_fully_paid(self):
        for move in self:
            sale_orders = move.invoice_line_ids.sale_line_ids.order_id
            purchase_orders = move.invoice_line_ids.purchase_line_id.order_id
            has_source = bool(sale_orders) or bool(purchase_orders)
            all_paid = True
            if sale_orders:
                all_paid = all_paid and all(sale_orders.mapped('beton_is_fully_paid'))
            if purchase_orders:
                all_paid = all_paid and all(purchase_orders.mapped('beton_is_fully_paid'))
            move.beton_source_fully_paid = has_source and all_paid

    def action_register_payment(self):
        for move in self:
            if move.beton_source_fully_paid:
                raise UserError(_(
                    "La facture %s ne peut pas être payée : le bon d'origine "
                    "est déjà totalement payé via la caisse béton."
                ) % (move.name or move.display_name))
        return super().action_register_payment()

    def _get_cheque_payments(self):
        """Retourne les paiements (account.payment) réconciliés à cette facture
        qui ont au moins un champ chèque renseigné (n°, date, domiciliation).
        Les champs cheque_* sont définis dans ce module beton_caisse."""
        self.ensure_one()
        Payment = self.env['account.payment']
        payments = Payment
        for line in self.line_ids:
            for partial in line.matched_debit_ids:
                counterpart = partial.debit_move_id
                if counterpart.payment_id:
                    payments |= counterpart.payment_id
            for partial in line.matched_credit_ids:
                counterpart = partial.credit_move_id
                if counterpart.payment_id:
                    payments |= counterpart.payment_id
        return payments.filtered(
            lambda p: p.cheque_reference or p.cheque_date or p.cheque_domiciliation
        )
