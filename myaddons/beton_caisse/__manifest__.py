{
    'name': 'Caisse Béton',
    'version': '17.0.1.0.1',
    'category': 'Accounting',
    'summary': 'Gestion de caisse pour centrale à béton (principale & secondaire)',
    'description': """
        Module de gestion de caisse dédié à la centrale à béton.
        - Deux caisses : Principale (encaissements clients) et Secondaire/Verte
        - Encaissements liés aux ventes
        - Décaissements liés aux achats fournisseurs
        - Transferts entre caisses
        - Recharges
        - Suivi crédit/versements
        - Dépenses globales par partenaire
        - Rapports PDF
    """,
    'author': 'Custom',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'account',
        'sale_management',
        'purchase',
        'hr_expense',
        'beton_base',
    ],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'security/rules.xml',
        'data/ir_sequence.xml',
        'data/default_cashboxes.xml',
        'data/account_payment_method_data.xml',
        'wizard/cashbox_recharge_wizard.xml',
        'wizard/date_filter_wizard.xml',
        'wizard/globale_print_wizard.xml',
        'wizard/register_payment_wizard.xml',
        'views/beton_cashbox_views.xml',
        'views/beton_caisse_entry_views.xml',
        'views/beton_caisse_expense_views.xml',
        'views/beton_caisse_transfer_views.xml',
        'views/beton_cashbox_recharge_views.xml',
        'views/beton_caisse_globale_views.xml',
        'views/account_payment_views.xml',
        'views/account_move_views.xml',
        'views/report_invoice_inherit.xml',
        'views/beton_versement_views.xml',
        'views/sale_order_views.xml',
        'views/purchase_order_views.xml',
        'views/hr_expense_sheet_views.xml',
        'views/res_partner_views.xml',
        'report/beton_caisse_reports.xml',
        'report/report_entry_template.xml',
        'report/report_expense_template.xml',
        'report/report_transfer_template.xml',
        'report/report_recharge_template.xml',
        'report/report_globale_template.xml',
        'report/report_versement_template.xml',
        'report/report_expense_list_template.xml',
        'report/report_partner_payments_template.xml',
        'report/report_analyse_globale_template.xml',
        'views/beton_caisse_menu.xml',
    ],
    'installable': True,
    'application': True,
    'post_init_hook': 'post_init_hook',
}
