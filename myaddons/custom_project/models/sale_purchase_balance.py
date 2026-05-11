from odoo import models, fields, api
from datetime import datetime, timedelta


class SpreadsheetDashboard(models.Model):
    _inherit = 'spreadsheet.dashboard'

    has_purchase_balance = fields.Boolean(string='Has Purchase Balance', default=False)






class SalePurchaseBalance(models.Model):
    _name = 'sale.purchase.balance'
    _description = 'Sales and Purchase Balance'
    _auto = False

    date = fields.Date(string='Date')
    sales_amount = fields.Float(string='Sales Amount')
    purchase_amount = fields.Float(string='Purchase Amount')
    balance = fields.Float(string='Balance')

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        # تنفيذ استعلام مخصص لتجميع بيانات المبيعات والشراء
        # هذا مثال مبسط، يجب تطويره وفقاً لاحتياجاتك
        result = []

        # الحصول على التواريخ المطلوبة للتجميع
        today = datetime.now().date()
        dates = [today - timedelta(days=30 * i) for i in range(6)]

        for date in dates:
            # استعلامات افتراضية - يجب استبدالها باستعلامات حقيقية
            sales_amount = 10000 * (6 - dates.index(date))  # مثال
            purchase_amount = 8000 * (6 - dates.index(date))  # مثال
            balance = sales_amount - purchase_amount

            result.append({
                'date:month': date.strftime('%Y-%m'),
                'sales_amount': sales_amount,
                'purchase_amount': purchase_amount,
                'balance': balance,
                '__count': 1,
                '__domain': [],
            })

        return result