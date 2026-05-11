from odoo import models, fields, api


class HrEmployeeExt(models.Model):
    _inherit = 'hr.employee'

    is_commercial = fields.Boolean(string="Est un commercial", help="Employé responsable de la vente")


class Partner(models.Model):
    _inherit = 'res.partner'

    credit = fields.Monetary(string='Crédit', readonly=True, compute='_compute_credit', store=True)
    versement_in_ids = fields.One2many('versement.in', 'partner_id', string='Versements entrants')
    sales_order_ids = fields.One2many('sale.order', 'partner_id', string='Ventes')

    @api.depends('sales_order_ids.state', 'sales_order_ids.amount_total', 'versement_in_ids.state',
                 'versement_in_ids.amount')
    def _compute_credit(self):
        for partner in self:
            # Achats confirmés
            sales = self.env['sale.order'].search([
                ('partner_id', '=', partner.id),
                ('state', '=', 'sale')
            ])
            total_sales = sum(sales.mapped('amount_total'))

            # Versements validés
            versements = self.env['versement.in'].search([
                ('partner_id', '=', partner.id),
                ('state', '=', 'validated')
            ])
            total_versements = sum(versements.mapped('amount'))

            partner.credit = total_sales - total_versements
