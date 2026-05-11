# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CentralBetonCoutRevient(models.Model):
    _name = 'central.beton.cout.revient'
    _description = 'Cout de Revient'
    _inherit = ['mail.thread']
    _order = 'date desc, id desc'

    name = fields.Char(
        string='Reference', required=True, copy=False,
        readonly=True, default='Nouveau')
    date = fields.Date(
        string='Date', default=fields.Date.today, required=True)
    bom_id = fields.Many2one(
        'mrp.bom', string='Formule', required=True,
        domain="[('is_beton_bom', '=', True)]")
    periode_debut = fields.Date(string='Debut Periode', required=True)
    periode_fin = fields.Date(string='Fin Periode', required=True)

    # Couts matieres
    cout_ciment = fields.Float(string='Cout Ciment')
    cout_sable = fields.Float(string='Cout Sable')
    cout_gravier = fields.Float(string='Cout Gravier')
    cout_eau = fields.Float(string='Cout Eau')
    cout_adjuvant = fields.Float(string='Cout Adjuvant')
    cout_matieres = fields.Float(
        string='Total Matieres',
        compute='_compute_couts', store=True)

    # Autres couts
    cout_main_oeuvre = fields.Float(string="Main d'Oeuvre")
    cout_energie = fields.Float(string='Energie')
    cout_transport = fields.Float(string='Transport')
    cout_maintenance = fields.Float(string='Maintenance')
    cout_amortissement = fields.Float(string='Amortissement')
    cout_indirect = fields.Float(string='Frais Indirects')

    cout_total = fields.Float(
        string='Cout Total', compute='_compute_couts', store=True)
    volume_produit = fields.Float(string='Volume Produit (m3)')
    cout_m3 = fields.Float(
        string='Cout / m3', compute='_compute_couts', store=True)

    notes = fields.Text(string='Notes')
    company_id = fields.Many2one(
        'res.company', string='Societe',
        default=lambda self: self.env.company)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nouveau') == 'Nouveau':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'central.beton.cout.revient') or 'Nouveau'
        return super().create(vals_list)

    @api.depends(
        'cout_ciment', 'cout_sable', 'cout_gravier', 'cout_eau',
        'cout_adjuvant', 'cout_main_oeuvre', 'cout_energie',
        'cout_transport', 'cout_maintenance', 'cout_amortissement',
        'cout_indirect', 'volume_produit')
    def _compute_couts(self):
        for rec in self:
            rec.cout_matieres = (
                rec.cout_ciment + rec.cout_sable + rec.cout_gravier
                + rec.cout_eau + rec.cout_adjuvant)
            rec.cout_total = (
                rec.cout_matieres + rec.cout_main_oeuvre + rec.cout_energie
                + rec.cout_transport + rec.cout_maintenance
                + rec.cout_amortissement + rec.cout_indirect)
            rec.cout_m3 = (
                rec.cout_total / rec.volume_produit
                if rec.volume_produit else 0.0)

    def action_calculer(self):
        """Calculate costs from production data for the period."""
        for rec in self:
            productions = self.env['mrp.production'].search([
                ('bom_id', '=', rec.bom_id.id),
                ('state', '=', 'done'),
                ('date_start', '>=', rec.periode_debut),
                ('date_start', '<=', rec.periode_fin),
            ])
            rec.volume_produit = sum(productions.mapped('volume_produit'))

            cout_par_type = {}
            for prod in productions:
                for move in prod.move_raw_ids:
                    mat_type = move.product_id.type_matiere_beton
                    if mat_type:
                        cout_par_type.setdefault(mat_type, 0.0)
                        cout_par_type[mat_type] += move.quantity * move.product_id.standard_price

            rec.cout_ciment = cout_par_type.get('ciment', 0.0)
            rec.cout_sable = cout_par_type.get('sable', 0.0)
            rec.cout_gravier = cout_par_type.get('gravier', 0.0)
            rec.cout_eau = cout_par_type.get('eau', 0.0)
            rec.cout_adjuvant = cout_par_type.get('adjuvant', 0.0)
        return True
