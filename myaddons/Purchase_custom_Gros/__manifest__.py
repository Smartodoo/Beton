# -*- coding: utf-8 -*-
{
    'name': "Achat_personalisation_Gros",
    'summary': "",
    'description': """
    """,

    'author': "Meziani",
    'website': "",
    'category': 'Achat',
    'version': '0.1',
    'depends': ['base', 'sale', 'hr', 'purchase', 'contacts','stock'],
    'data': [
      'views/purchase_order.xml',
      'report/report_supplier_products.xml',
      'security/regles_de_securites.xml',
    ],
    'installable': True,
    'application': False,
}
