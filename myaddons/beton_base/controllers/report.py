import json

from odoo.addons.web.controllers.report import ReportController
from odoo.http import content_disposition, request, route


class BetonReportController(ReportController):

    @route()
    def report_download(self, data, context=None, token=None):
        response = super().report_download(data, context=context, token=token)
        if not response:
            return response
        try:
            url = json.loads(data)[0]
            if 'beton_base.report_purchase_order_list' not in url:
                return response

            part = url.split('/report/pdf/')[-1].split('?')[0]
            if '/' not in part:
                return response

            docids_str = part.split('/', 1)[1]
            ids = [int(x) for x in docids_str.split(',') if x.isdigit()]
            if not ids:
                return response

            orders = request.env['purchase.order'].browse(ids)
            states = list(dict.fromkeys(orders.mapped('state')))

            if all(s in ('draft', 'sent') for s in states):
                title = 'Liste des Demandes de Prix'
            elif states == ['purchase']:
                title = 'Liste des Bons de Commande'
            elif states == ['done']:
                title = 'Liste des Bons de Commande Verrouilles'
            elif states == ['cancel']:
                title = "Liste des Bons d'Achats Annules"
            else:
                title = "Liste des Bons d'Achats"

            response.headers['Content-Disposition'] = content_disposition(
                '%s.pdf' % title
            )
        except Exception:
            pass
        return response
