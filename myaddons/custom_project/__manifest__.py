{
    "name": "Projects_sous traitons",
    "version": "1.0",
    "depends": ["base", "contacts", "HR_customization", "uom", "account", "spreadsheet_dashboard_sale"],
    "author": "SmartOdoo",
    "category": "Project",
    "description": "Custom Project Management with Subcontractors",
    "data": [
        "security/ir.model.access.csv",
        "data/account_payment_method_data.xml",
        "views/menu.xml",
        "views/situation.xml",
        "views/project_views.xml",
        "views/res_partner.xml",
        "views/account_payment.xml",
        "views/project_observation_views.xml",
        "views/consommation_stock_views.xml",

    ],
    "installable": True,
    "application": True,
    "auto_install": False,
    'icon': 'custom_project/static/description/closure.png',
}
