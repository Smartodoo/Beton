from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime


class PurchaseOrderInheri(models.Model):
    _inherit = 'purchase.order'

    active = fields.Boolean(default=True)  # Permet d'archiver les bons de commande
    payment_purchase_ids = fields.One2many('account.payment', 'purchase_order_id', string='Payments')
    amount_paid_purchase = fields.Monetary(string="Montant payé", compute="_compute_amount_paid", store=True)
    payment_count_purchase = fields.Integer(string="Nombre de paiements", compute="_compute_payment_count", store=True)
    amount_due_purchase = fields.Monetary(string="Montant dû", compute="_compute_amount_due", store=True)
    is_payment_term_purchase = fields.Boolean(string="À Terme", compute="_compute_is_payment_term", store=True)
    date_bon = fields.Datetime(string="date de bon", default=fields.Datetime.now)
    date_today = fields.Datetime(string="date de saisie", default=fields.Datetime.now)
    num_bon = fields.Char(string="Numéro de bon", required=False)


    @api.depends('payment_purchase_ids.amount')
    def _compute_amount_paid(self):
        """Calculer la somme des paiements enregistrés."""
        for order in self:
            order.amount_paid_purchase = sum(order.payment_purchase_ids.mapped('amount'))

    @api.depends('amount_paid_purchase', 'amount_total')
    def _compute_amount_due(self):
        """Calcule le montant restant à payer."""
        for order in self:
            order.amount_due_purchase = order.amount_total - order.amount_paid_purchase

    @api.depends("payment_purchase_ids")
    def _compute_is_payment_term(self):
        """Détermine si le dernier paiement est en mode 'À Terme'"""
        for order in self:
            latest_payment = order.payment_purchase_ids.sorted(lambda p: p.create_date, reverse=True)[
                             :1]  # Dernier paiement
            order.is_payment_term_purchase = (
                latest_payment.payment_method_line_id.code == 'A-terme'
                if latest_payment else False
            )

    @api.depends('payment_purchase_ids')
    def _compute_payment_count(self):
        """Calcule le nombre de paiements effectués sur ce bon de commande"""
        for order in self:
            order.payment_count_purchase = len(order.payment_purchase_ids)

    def action_open_payments(self):
        """Ouvre la liste des paiements liés à ce bon de commande"""
        return {
            'name': "Paiements enregistrés",
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'view_mode': 'tree,form',
            'domain': [('purchase_order_id', '=', self.id)],
            'context': {'default_purchase_order_id': self.id},
        }

    def action_register_payment(self):
        """Créer un paiement et l'affecter au bon de commande"""
        self.ensure_one()

        # Vérifier si le montant payé couvre déjà le total
        if self.amount_paid_purchase >= self.amount_total:
            raise ValidationError("Le paiement total a déjà été effectué pour ce bon de commande.")
        return {
            'name': "Enregistrer un paiement",
            'view_mode': 'form',
            'res_model': 'account.payment',
            'view_id': self.env.ref('account.view_account_payment_form').id,
            'type': 'ir.actions.act_window',
            'context': {
                'default_purchase_order_id': self.id,
                'default_partner_id': self.partner_id.id,
                'default_amount': self.amount_total - self.amount_paid_purchase,
                'default_currency_id': self.currency_id.id,
                'default_payment_type': 'outbound',
                'default_payment_method_id': self.env.ref('account.account_payment_method_manual_in').id,
            },
            'target': 'new',
        }

    def button_confirm(self):
        # 1) Appel du standard pour créer le picking normalement
        res = super().button_confirm()

        for order in self:
            # 🚚 2) Valider immédiatement les réceptions
            for picking in order.picking_ids.filtered(lambda p: p.state not in ('done', 'cancel')):
                # Confirmer le picking s'il est en 'draft'
                if picking.state == 'draft':
                    picking.action_confirm()

                # Réserver les produits
                picking.action_assign()

                # Valider automatiquement le picking (ou traiter le wizard si besoin)
                if not picking.button_validate():
                    wiz = self.env['stock.immediate.transfer'].search([('pick_ids', 'in', picking.id)], limit=1)
                    if wiz:
                        wiz.process()
        return res

    # Cree des paiements automatiquement
    def action_create_auto_payments(self):
        """Créer automatiquement les paiements pour les bons sélectionnés."""
        AccountPayment = self.env['account.payment']
        PaymentMethod = self.env.ref('account.account_payment_method_manual_in')

        # Vérifier si tous les bons sont confirmés (purchase ou done)
        not_confirmed = self.filtered(lambda o: o.state not in ['purchase', 'done'])
        if not_confirmed:
            raise UserError("⚠️ Il faut confirmer toutes les commandes avant de créer les paiements.")

        # Vérifier s'il y a des bons déjà payés
        already_paid = self.filtered(lambda o: o.amount_due_purchase <= 0)
        if already_paid:
            raise UserError("⚠️ Il existe déjà des bons totalement payés dans la sélection.")

        payments_created = 0

        for order in self:
            # Crée un paiement pour le montant dû
            payment_vals = {
                'payment_type': 'outbound',  # sortie d'argent
                'partner_id': order.partner_id.id,
                'amount': order.amount_due_purchase,
                'currency_id': order.currency_id.id,
                'payment_method_id': PaymentMethod.id,
                'date': fields.Date.today(),  # ✅ champ correct
                'purchase_order_id': order.id,
                'ref': f"Paiement auto - {order.name}",
            }

            payment = AccountPayment.create(payment_vals)
            payment.action_post()  # valider le paiement

            # Met à jour les montants
            order.amount_paid_purchase = order.amount_total
            order.amount_due_purchase = 0

            payments_created += 1

        if payments_created == 0:
            raise UserError("Aucun paiement n’a été créé.")

        # Notification de succès
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': "Paiements créés avec succès ✅",
                'message': f"{payments_created} paiement(s) ont été générés automatiquement.",
                'type': 'success',
                'sticky': False,
            }
        }




class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    product_id = fields.Many2one(
        'product.product',
        string="Product",
        domain="[('purchase_ok', '=', True)]",
        ondelete="restrict",
        required=True,
        context="{'default_type': 'product'}",  # 👉 forcer type = stockable
    )


class AccountPaymentInherit(models.Model):
    _inherit = 'account.payment'

    purchase_order_id = fields.Many2one('purchase.order', string="Bon d'achat")
