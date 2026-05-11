from odoo import api, SUPERUSER_ID
from odoo.addons.beton_caisse.hooks import sync_beton_payment_method_lines


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    sync_beton_payment_method_lines(env)
