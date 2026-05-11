from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        for order in self:
            order._check_beton_plafond_credit()
        return super().action_confirm()

    def _check_beton_plafond_credit(self):
        """Bloque la confirmation si le crédit client dépasserait le plafond."""
        self.ensure_one()
        partner = self.partner_id
        if not partner or partner.type_partenaire_beton != 'client':
            return
        plafond = partner.plafond_credit or 0.0
        if plafond <= 0:
            return  # Pas de plafond défini -> pas de blocage
        current_credit = partner.beton_credit_client or 0.0
        future_credit = current_credit + (self.amount_total or 0.0)
        if future_credit > plafond:
            overflow = future_credit - plafond
            raise UserError(_(
                "Plafond crédit dépassé pour %(partner)s !\n\n"
                "Crédit actuel       : %(current).2f\n"
                "Montant de cette commande : %(amount).2f\n"
                "Crédit après confirmation : %(future).2f\n"
                "Plafond autorisé    : %(plafond).2f\n"
                "Dépassement         : %(overflow).2f\n\n"
                "Veuillez augmenter le plafond du client ou attendre un encaissement."
            ) % {
                'partner': partner.name,
                'current': current_credit,
                'amount': self.amount_total or 0.0,
                'future': future_credit,
                'plafond': plafond,
                'overflow': overflow,
            })

    beton_entry_ids = fields.One2many(
        'beton.caisse.entry',
        'sale_order_id',
        string='Paiements caisse',
    )
    beton_payment_count = fields.Integer(
        string='Nb paiements',
        compute='_compute_beton_payments',
        store=True,
    )
    beton_amount_paid = fields.Monetary(
        string='Montant paye (caisse)',
        compute='_compute_beton_payments',
        store=True,
        currency_field='currency_id',
    )
    beton_amount_residual = fields.Monetary(
        string='Reste a payer (caisse)',
        compute='_compute_beton_payments',
        store=True,
        currency_field='currency_id',
    )
    beton_is_fully_paid = fields.Boolean(
        string='Totalement paye (caisse)',
        compute='_compute_beton_payments',
        store=True,
    )
    beton_payment_state = fields.Selection([
        ('not_paid', 'Non paye'),
        ('partial', 'Partiel'),
        ('paid', 'Paye'),
    ], string='Etat paiement caisse',
        compute='_compute_beton_payments',
        store=True,
    )

    @api.depends('beton_entry_ids', 'beton_entry_ids.state', 'beton_entry_ids.amount_paid', 'amount_total')
    def _compute_beton_payments(self):
        for rec in self:
            approved = rec.beton_entry_ids.filtered(lambda e: e.state == 'approuve')
            rec.beton_payment_count = len(approved)
            rec.beton_amount_paid = sum(approved.mapped('amount_paid'))
            rec.beton_amount_residual = rec.amount_total - rec.beton_amount_paid
            rec.beton_is_fully_paid = rec.beton_amount_paid >= rec.amount_total and rec.amount_total > 0
            # Etat paiement
            if rec.beton_amount_paid <= 0:
                rec.beton_payment_state = 'not_paid'
            elif rec.beton_is_fully_paid:
                rec.beton_payment_state = 'paid'
            else:
                rec.beton_payment_state = 'partial'

    def action_register_beton_payment(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Enregistrer un paiement',
            'res_model': 'beton.register.payment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'active_model': 'sale.order',
                'active_id': self.id,
            },
        }

    def action_view_beton_payments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Paiements caisse',
            'res_model': 'beton.caisse.entry',
            'view_mode': 'tree,form',
            'domain': [('sale_order_id', '=', self.id)],
            'context': {'default_sale_order_id': self.id},
        }
