from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    active = fields.Boolean(default=True)  # Permet d'archiver les bons de commande
    commercial_id = fields.Many2one('hr.employee', string="Commercial", help="Employé responsable de la vente",
                                    domain=[('is_commercial', '=', True)])

    payment_ids = fields.One2many('account.payment', 'sale_order_id', string="Paiements")
    amount_paid = fields.Monetary(string="Montant payé", compute="_compute_amount_paid", store=True)
    payment_count = fields.Integer(string="Nombre de paiements", compute="_compute_payment_count", store=True)
    amount_due = fields.Monetary(string="Montant dû", compute="_compute_amount_due", store=True)
    is_payment_term = fields.Boolean(string="À Terme", compute="_compute_is_payment_term", store=True)
    def action_confirm(self):
        res = super().action_confirm()
        for order in self:
            # on cherche les livraisons associées
            pickings = order.picking_ids.filtered(lambda p: p.state not in ['done', 'cancel'])
            for picking in pickings:
                if picking.state == 'draft':
                    picking.action_confirm()
                if picking.state in ['waiting', 'confirmed', 'assigned']:
                    picking.action_assign()
                if picking.state == 'assigned':
                    picking.button_validate()
        return res

    @api.depends("payment_ids")
    def _compute_is_payment_term(self):
        """Détermine si le dernier paiement est en mode 'À Terme'"""
        for order in self:
            latest_payment = order.payment_ids.sorted(lambda p: p.create_date, reverse=True)[:1]  # Dernier paiement
            order.is_payment_term = (
                latest_payment.payment_method_line_id.code == 'A-terme'
                if latest_payment else False
            )

    @api.depends('amount_paid', 'amount_total')
    def _compute_amount_due(self):
        """Calcule le montant restant à payer."""
        for order in self:
            order.amount_due = order.amount_total - order.amount_paid

    @api.depends('payment_ids')
    def _compute_payment_count(self):
        """Calcule le nombre de paiements effectués sur ce bon de commande"""
        for order in self:
            order.payment_count = len(order.payment_ids)

    def action_open_payments(self):
        """Ouvre la liste des paiements liés à ce bon de commande"""
        return {
            'name': "Paiements enregistrés",
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'view_mode': 'tree,form',
            'domain': [('sale_order_id', '=', self.id)],
            'context': {'default_sale_order_id': self.id},
        }

    @api.depends('payment_ids.amount')
    def _compute_amount_paid(self):
        """Calculer la somme des paiements enregistrés."""
        for order in self:
            order.amount_paid = sum(order.payment_ids.mapped('amount'))

    def action_register_payment(self):
        """Créer un paiement et l'affecter au bon de commande"""
        self.ensure_one()

        # Vérifier si le montant payé couvre déjà le total
        if self.amount_paid >= self.amount_total:
            raise ValidationError("Le paiement total a déjà été effectué pour ce bon de commande.")
        return {
            'name': "Enregistrer un paiement",
            'view_mode': 'form',
            'res_model': 'account.payment',
            'view_id': self.env.ref('account.view_account_payment_form').id,
            'type': 'ir.actions.act_window',
            'context': {
                'default_sale_order_id': self.id,
                'default_partner_id': self.partner_id.id,
                'default_amount': self.amount_total - self.amount_paid,
                'default_currency_id': self.currency_id.id,
                'default_payment_type': 'inbound',
                'default_payment_method_id': self.env.ref('account.account_payment_method_manual_in').id,
            },
            'target': 'new',
        }


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    price_type = fields.Selection([('unitaire', 'Prix unitaire'), ('Gros', 'Prix de Gros')], string='Type de prix',
                                  help="Type de prix de vente", default='unitaire', required=True)

    @api.onchange('price_type')
    def update_unit_price(self):
        for line in self:
            if line.price_type == 'Gros':
                line.price_unit = line.product_id.prix_de_gros
            else:
                line.price_unit = line.product_id.list_price


class AccountPayment(models.Model):
    _inherit = "account.payment"

    sale_order_id = fields.Many2one('sale.order', string="Bon de commande")

    @api.onchange('payment_method_line_id')
    def _onchange_payment_method_line_id(self):
        """Mettre à jour le montant du paiement en fonction de la méthode de paiement"""
        if self.payment_method_line_id.code == 'A-terme':
            self.amount = 0


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    sale_order_id = fields.Many2one('sale.order', string='Sale Order')
    purchase_order_id = fields.Many2one('purchase.order', string='Purchase Order')

    def _create_payments(self):
        payments = super()._create_payments()
        # Ajoute l'ordre d'achat ou de vente si fourni
        for payment in payments:
            payment.sale_order_id = self.sale_order_id.id
            payment.purchase_order_id = self.purchase_order_id.id
        return payments


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_register_payment(self):
        res = super().action_register_payment()

        if len(self) == 1 and self.move_type in ['out_invoice', 'in_invoice']:
            res_context = dict(res.get('context', {}))

            if self.move_type == 'out_invoice':
                sale_order = self.env['sale.order'].search([('name', '=', self.invoice_origin)], limit=1)
                if sale_order:
                    res_context['default_sale_order_id'] = sale_order.id

            elif self.move_type == 'in_invoice':
                purchase_order = self.env['purchase.order'].search([('name', '=', self.invoice_origin)], limit=1)
                if purchase_order:
                    res_context['default_purchase_order_id'] = purchase_order.id

            res['context'] = res_context

        return res
