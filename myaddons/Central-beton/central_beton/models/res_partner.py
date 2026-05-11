# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_beton_client = fields.Boolean(
        string='Client Beton', default=False)
    type_client_beton = fields.Selection([
        ('particulier', 'Particulier'),
        ('entreprise', 'Entreprise BTP'),
        ('promoteur', 'Promoteur Immobilier'),
        ('etatique', 'Marche Public'),
    ], string='Type Client Beton')
    plafond_credit = fields.Float(string='Plafond Credit')
    encours_client = fields.Float(
        string='Encours Client',
        compute='_compute_encours_client')
    depassement_credit = fields.Boolean(
        string='Depassement Credit',
        compute='_compute_encours_client')
    chantier_ids = fields.One2many(
        'central.beton.chantier', 'client_id', string='Chantiers')
    chantier_count = fields.Integer(
        string='Nombre de Chantiers',
        compute='_compute_chantier_count')
    conditions_paiement_beton = fields.Text(
        string='Conditions de Paiement Beton')

    @api.depends('invoice_ids', 'invoice_ids.amount_residual',
                 'invoice_ids.state', 'invoice_ids.move_type')
    def _compute_encours_client(self):
        for partner in self:
            invoices = self.env['account.move'].search([
                ('partner_id', '=', partner.id),
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted'),
                ('payment_state', 'in', ('not_paid', 'partial')),
            ])
            partner.encours_client = sum(invoices.mapped('amount_residual'))
            partner.depassement_credit = (
                partner.plafond_credit > 0
                and partner.encours_client > partner.plafond_credit)

    @api.depends('chantier_ids')
    def _compute_chantier_count(self):
        for partner in self:
            partner.chantier_count = len(partner.chantier_ids)

    def action_view_chantiers(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Chantiers',
            'res_model': 'central.beton.chantier',
            'view_mode': 'tree,form',
            'domain': [('client_id', '=', self.id)],
            'context': {'default_client_id': self.id},
        }
