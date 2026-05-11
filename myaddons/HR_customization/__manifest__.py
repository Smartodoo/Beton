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
    'name': 'Customize In HR',
    'version': '17.0.1.0.0',
    'category': 'HR',
    'summary': 'Personnaliser HR',
    'description': '',
    'author': 'MEZIANI NABILA',
    'company': 'SmartOdoo',
    'maintainer': 'SmartOdoo',
    'website': '',
    'depends': ['base', 'contacts', 'hr', 'sale', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'data/versement_sequence.xml',
        'views/res_partner.xml',
        'views/hr_employee.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
