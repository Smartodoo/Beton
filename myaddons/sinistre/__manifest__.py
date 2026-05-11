# Copyright 2015 ABF OSIELL <https://osiell.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "sinistre",
    'version': '17.0.1.0.0',
    "author": "hamitouche younes",
    'description': '',
    "category": "Tools",
    "license": "AGPL-3",
    "depends": ['hr', 'fleet', 'base', 'contacts', ],
    "data": [
        'security/ir.model.access.csv',
        'wizard/print_report_accident_date.xml',
        'wizard/sinistre_print_year_wizard_view.xml',
        'wizard/sinistre_print_state_wizard_view.xml',
        'report/external_layout_hide_fiscal_sinistre_final.xml',
        'report/sinistre_report_template.xml',
        'views/sinistre.xml',

    ],

    "application": True,
    "installable": True,
    'auto_install': False,
    'icon': 'sinistre/static/description/icon.png',
}
