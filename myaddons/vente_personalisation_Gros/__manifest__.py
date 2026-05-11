# -*- coding: utf-8 -*-
{
    'name': "vente_personalisation_Gros",
    'summary': "",
    'description': """
    """,

    'author': "tech",
    'website': "",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base', 'sale', 'hr', 'contacts', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_views_inherit.xml',
        'views/programme.xml',
        'report/programme_pdf.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'vente_personalisation_Gros/static/src/css/mon_style.css',
        ],
    },
    'installable': True,
    'application': False,
}
