# -*- coding: utf-8 -*-
{
    'name': 'Central Beton',
    'version': '17.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Gestion de Centrale a Beton',
    'description': """
        Central Beton - Systeme de Gestion de Centrale a Beton
        ======================================================

        Module complet pour la gestion d'une centrale a beton :
        * Gestion des formules et recettes de beton
        * Ordres de fabrication et production
        * Gestion des matieres premieres et stocks
        * Suivi des livraisons et transport
        * Controle qualite et essais laboratoire
        * Gestion de la maintenance des equipements
        * Analyse des couts de revient
        * Tableaux de bord et reporting
    """,
    'author': 'Central Beton',
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'sale_management',
        'stock',
        'purchase',
        'account',
        'hr',
        'maintenance',
        'fleet',
        'product',
        'mrp',
    ],
    'data': [
        # Security
        'security/central_beton_security.xml',
        'security/ir.model.access.csv',
        # Data
        'data/sequence_data.xml',
        'data/product_data.xml',
        'data/bom_data.xml',
        # Views - Custom models
        'views/centrale_views.xml',
        'views/mrp_bom_views.xml',
        'views/mrp_production_views.xml',
        'views/mouvement_stock_views.xml',
        'views/essai_views.xml',
        'views/non_conformite_views.xml',
        'views/chantier_views.xml',
        'views/livraison_views.xml',
        'views/cout_revient_views.xml',
        # Views - Inherited models
        'views/product_template_views.xml',
        'views/res_partner_views.xml',
        'views/sale_order_views.xml',
        'views/fleet_vehicle_views.xml',
        'views/maintenance_equipment_views.xml',
        'views/maintenance_request_views.xml',
        'views/account_move_views.xml',
        # Reports (before menus since menus reference report actions)
        'report/production_report_views.xml',
        'report/livraison_report_views.xml',
        'report/report_bon_livraison.xml',
        'report/report_fabrication.xml',
        # Wizard
        'wizard/wizard_production_report_views.xml',
        # Menus (last, references all actions above)
        'views/menu_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'central_beton/static/src/css/central_beton.css',
            'central_beton/static/src/js/dashboard.js',
            'central_beton/static/src/xml/dashboard_templates.xml',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
