# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Akhil Ashok (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
{
    'name': 'Customize In fleet ',
    'version': '17.0.1.0.0',
    'category': 'fleet ',
    'summary': 'Personnaliser HR',
    'description': '',
    'author': 'hamitouche younes',
    'company': 'SmartOdoo',
    'maintainer': 'SmartOdoo',
    'website': '',
    'depends': ['fleet', 'hr', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/fleet_carrosserie_view.xml',
        'views/societe_appartenance_views.xml',
        'views/fleet_vehicle_extra_views.xml',
        'views/inherited_fleet_vehicle_view_form.xml',
        'views/hr_employee_views.xml',
        'views/infraction.xml',
        'wizard/fleet_gazoil_wizard.xml',
        'report/report_consommation_gazoil.xml',
        'views/fleet_gazoil.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
