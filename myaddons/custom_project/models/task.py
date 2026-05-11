# -*- coding: utf-8 -*-
# (تنويهة: هذا الملف هو نسخة كاملة مبسطة/محسنة من models.py؛
# حافظت على باقي التعريفات كما في الإصدار السابق)
import base64
import io
import logging
import re
import traceback

import pandas as pd
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round

_logger = logging.getLogger(__name__)


class CustomTaskLots(models.Model):
    _name = "custom.task.lots"
    _description = "Lot de Projet"
    _order = "sequence, id"



    no = fields.Char("N°", readonly=False, copy=False)
    sequence = fields.Integer(string="Sequence", default=10)
    name = fields.Char(string="Designation des Lots", required=True)
    project_id = fields.Many2one("custom.project", string="Projet", required=True, ondelete="cascade")
    company_id = fields.Many2one("res.company", string="Société", default=lambda self: self.env.company)
    task_ids = fields.One2many("custom.task", "lot_id", string="Tâches")
    s_total = fields.Float(string="SOUS TOTAL", compute="_compute_s_total", store=True)
    import_source = fields.Selection([("primary", "Primary"), ("secondary", "Secondary")], default="primary",
                                     string="Source import")
    user_id = fields.Many2one('res.users', string='Utilisateur', default=lambda self: self.env.user)
    @api.depends('task_ids.total_price')
    def _compute_s_total(self):
        for lot in self:
            lot.s_total = float_round(sum((t.total_price or 0.0) for t in lot.task_ids.filtered(lambda r: not r.parent_id)), precision_digits=2)


class CustomTask(models.Model):
    _name = "custom.task"
    _description = "Tâche de Projet"
    _order = "sequence, id"

    sequence = fields.Integer(string="Sequence", default=10)
    no = fields.Char("N°", readonly=False, copy=False)
    name = fields.Char(string="Designation des Ouvrages", required=True)
    unit = fields.Many2one("uom.uom", string="U")
    unit_name = fields.Char(string="U (texte from Excel)")
    quantity = fields.Float(string="Quantité", default=0.0)
    unit_price = fields.Float(string="Prix Unitaire", default=0.0)
    total_price = fields.Float("Montant", compute="_compute_total_price", store=True)
    is_subtotal = fields.Boolean(string="Is Subtotal", default=False)
    is_title = fields.Boolean(string="Is Title", default=False)
    is_category = fields.Boolean(string="Is Category", default=False)
    parent_id = fields.Many2one("custom.task", string="Parent Task", ondelete="cascade")
    child_ids = fields.One2many("custom.task", "parent_id", string="Sub-tasks")
    project_id = fields.Many2one("custom.project", string="Projet", required=True, ondelete="cascade")
    company_id = fields.Many2one("res.company", string="Société", default=lambda self: self.env.company)
    lot_id = fields.Many2one("custom.task.lots", string="Lot")
    import_source = fields.Selection([("primary", "Primary"), ("secondary", "Secondary")], default="primary",
                                     string="Source import")
    user_id = fields.Many2one('res.users', string='Utilisateur', default=lambda self: self.env.user)
    @api.depends('quantity', 'unit_price', 'child_ids.total_price')
    def _compute_total_price(self):
        for rec in self:
            if rec.child_ids:
                rec.total_price = float_round(sum(child.total_price or 0.0 for child in rec.child_ids), precision_digits=2)
            else:
                rec.total_price = float_round((rec.quantity or 0.0) * (rec.unit_price or 0.0), precision_digits=2)
    def _get_or_create_unit(self, unit_name):
        """Crée une unité si elle n'existe pas, sinon retourne l'unité existante"""
        if not unit_name:
            return False

        # Nettoyer le nom de l'unité
        unit_name = unit_name.strip()

        # Chercher si l'unité existe déjà
        unit = self.env['uom.uom'].search([
            ('name', '=ilike', unit_name)
        ], limit=1)

        if unit:
            return unit.id
        else:
            # Créer une nouvelle unité
            try:
                category_id = self.env.ref('uom.product_uom_categ_unit').id
                new_unit = self.env['uom.uom'].create({
                    'name': unit_name,
                    'category_id': category_id,
                    'factor': 1.0,
                    'uom_type': 'reference',
                    'rounding': 0.001,
                })
                _logger.info(f"Unité créée: {unit_name} (ID: {new_unit.id})")
                return new_unit.id
            except Exception as e:
                _logger.error(f"Erreur lors de la création de l'unité {unit_name}: {str(e)}")
                return False

    @api.onchange('unit_name')
    def _onchange_unit_name(self):
        """Lorsque le nom d'unité change, créer ou associer l'unité"""
        for rec in self:
            if rec.unit_name:
                rec.unit = rec._get_or_create_unit(rec.unit_name)  # Ligne corrigée

    @api.model
    def create(self, vals):
        """Override create pour gérer l'unité à partir du nom"""
        if vals.get('unit_name') and not vals.get('unit'):
            unit_id = self._get_or_create_unit(vals['unit_name'])
            if unit_id:
                vals['unit'] = unit_id
        return super(CustomTask, self).create(vals)

    def write(self, vals):
        """Override write pour gérer l'unité à partir du nom"""
        if vals.get('unit_name') and not vals.get('unit'):
            unit_id = self._get_or_create_unit(vals['unit_name'])
            if unit_id:
                vals['unit'] = unit_id
        return super(CustomTask, self).write(vals)

class StockProject(models.Model):
    _name = "custom.stock"
    _description = "Stock Projet"
    _rec_name = "name"

    # Best: store product as Many2one
    product_id = fields.Many2one("product.product", string="Product", required=True)
    project_id = fields.Many2one("custom.project", string="Projet")
    quantity = fields.Float("Quantité", required=True, default=1.0)
    unit = fields.Many2one("uom.uom", string="Unité")
    partner_id = fields.Many2one('res.partner', 'Sous-traitant')
    name = fields.Char(
        compute="_compute_name",
        store=True
    )

    @api.depends('product_id', 'project_id', 'partner_id')
    def _compute_name(self):
        for rec in self:
            parts = []
            if rec.product_id:
                parts.append(rec.product_id.display_name)
            if rec.project_id:
                parts.append(rec.project_id.name)
            if rec.partner_id:
                parts.append(rec.partner_id.name)
            rec.name = " - ".join(parts)


class Bons(models.Model):
    _name = "custom.bons"
    _description = "Bons de commande"

    project_id = fields.Many2one("custom.project", string="Projet")
    name = fields.Char("Numéro du Bon", required=True)
    date = fields.Date("Date", default=fields.Date.context_today)
    article_ids = fields.One2many("custom.article", "bon_id", string="Articles")
    total_price = fields.Float(string="Total HT", compute="_compute_total_price", store=True)
    currency_id = fields.Many2one(
        "res.currency",
        string="Devise",
        default=lambda self: self.env.company.currency_id
    )
    description = fields.Text("Description")
    vendor_id = fields.Many2one(
        'res.partner',
        string='Fournisseur',
        domain=[('contact_type', '=', 'SUPPLIER'), ('is_company', '=', True)],
        help='Sélectionner le fournisseur lié à cette situation.'
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Fournisseur',
        domain=[('contact_type', '=', 'SUBCONTRACTOR'), ('is_company', '=', True)],
        help='Sélectionner le fournisseur lié à cette situation.'
    )

    @api.depends('article_ids.total_price')
    def _compute_total_price(self):
        for rec in self:
            rec.total_price = sum(article.total_price for article in rec.article_ids)

    @api.model
    def create(self, vals):
        bon = super(Bons, self).create(vals)
        Stock = self.env['custom.stock']
        for article in bon.article_ids:
            product_id = article.product.id
            stock = Stock.search([('product_id', '=', product_id), ('project_id', '=', bon.project_id.id), ('partner_id', '=', bon.vendor_id.id)], limit=1)
            if stock:
                # use assignment to ensure ORM update
                stock.quantity = stock.quantity + article.quantity
            else:
                Stock.create({
                    'product_id': article.product.id,
                    'project_id': bon.project_id.id,
                    'partner_id': bon.vendor_id.id,
                    'quantity': article.quantity,
                    'unit': article.unit.id if article.unit else False,
                })
        return bon

    def write(self, vals):
        # cache old quantities (by article id) BEFORE write
        old_articles = {}
        for bon in self:
            for a in bon.article_ids:
                old_articles[a.id] = a.quantity
        res = super(Bons, self).write(vals)
        Stock = self.env['custom.stock']
        for bon in self:
            for article in bon.article_ids:
                product_id = article.product.id
                stock = Stock.search([('product_id', '=', product_id), ('project_id', '=', bon.project_id.id), ('partner_id', '=', bon.vendor_id.id)], limit=1)
                old_qty = old_articles.get(article.id, 0.0)
                if stock:
                    stock.quantity = stock.quantity + (article.quantity - old_qty)
                else:
                    Stock.create({
                        'product_id': product_id,
                        'project_id': bon.project_id.id,
                        'quantity': article.quantity,
                        'partner_id': bon.vendor_id.id,
                        'unit': article.unit.id if article.unit else False,
                    })
        return res


class Article(models.Model):
    _name = "custom.article"
    _description = "Articles des Bons de commande"

    bon_id = fields.Many2one("custom.bons", string="Bon de commande")
    product = fields.Many2one("product.product", required=True)
    quantity = fields.Float("Quantité", required=True, default=1.0)
    unit_price = fields.Float("Prix Unitaire", required=True, default=0.0)
    total_price = fields.Float("Total", compute="_compute_total_price", store=True)
    unit = fields.Many2one("uom.uom", string="Unité")
    currency_id = fields.Many2one(
        "res.currency",
        string="Devise",
        default=lambda self: self.env.company.currency_id
    )

    @api.depends('quantity', 'unit_price')
    def _compute_total_price(self):
        for rec in self:
            rec.total_price = rec.quantity * rec.unit_price



class CunsomationStock(models.Model):
    _name = "cunsomation.stock"
    _description = "Consommation Stock"

    product_id = fields.Many2one(
        "product.product",
        "Produit",
        required=True,
        domain="[('id', 'in', available_product_ids)]"
    )
    project_id = fields.Many2one("custom.project", string="Projet")
    quantity = fields.Float("Quantité consommée", required=True, default=0.0)
    date_consumption = fields.Datetime("Date de consommation", default=fields.Datetime.now)
    purchase_order_id = fields.Many2one("custom.bons", string="Bon de commande")
    company_id = fields.Many2one('res.company', string='Société', default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='Utilisateur', default=lambda self: self.env.user)
    available_product_ids = fields.Many2many(
        'product.product',
        compute='_compute_available_products',
        string='Produits disponibles'
    )

    @api.depends('project_id')
    def _compute_available_products(self):
        for record in self:
            if record.project_id:
                stock_records = self.env['custom.stock'].search([
                    ('project_id', '=', record.project_id.id),
                    ('quantity', '>', 0)
                ])
                record.available_product_ids = stock_records.mapped('product_id')
            else:
                record.available_product_ids = self.env['product.product']

    # Add onchange to update product domain when project changes
    @api.onchange('project_id')
    def _onchange_project_id(self):
        if self.project_id:
            return {
                'domain': {
                    'product_id': [('id', 'in', self.available_product_ids.ids)]
                }
            }
        else:
            return {
                'domain': {
                    'product_id': []
                }
            }

    @api.model
    def create(self, vals):
        # Check if there's enough stock before creating consumption
        stock = self.env['custom.stock'].search([
            ('product_id', '=', vals.get('product_id')),
            ('project_id', '=', vals.get('project_id'))
        ], limit=1)

        if stock:
            if stock.quantity < vals.get('quantity', 0):
                raise UserError(
                    f"Stock insuffisant! Stock disponible: {stock.quantity}, Quantité demandée: {vals.get('quantity')}")
            # Deduct from stock
            stock.quantity -= vals.get('quantity', 0)
        else:
            product = self.env['product.product'].browse(vals.get('product_id'))
            raise UserError(
                f"Le produit {product.display_name} n'existe pas dans le stock pour ce projet!"
            )

        return super(CunsomationStock, self).create(vals)

    def write(self, vals):
        # Handle stock adjustments when consumption quantity changes
        if 'quantity' in vals:
            for record in self:
                stock = self.env['custom.stock'].search([
                    ('product_id', '=', record.product_id.id),
                    ('project_id', '=', record.project_id.id)
                ], limit=1)

                if stock:
                    # First, add back the old quantity
                    stock.quantity += record.quantity

                    # Check if new quantity is available
                    if stock.quantity < vals['quantity']:
                        # Restore original stock
                        stock.quantity -= record.quantity
                        raise UserError(
                            f"Stock insuffisant! Stock disponible: {stock.quantity - record.quantity}, Quantité demandée: {vals['quantity']}")

                    # Deduct the new quantity
                    stock.quantity -= vals['quantity']

        return super(CunsomationStock, self).write(vals)

    def unlink(self):
        # Restore stock when consumption is deleted
        for record in self:
            stock = self.env['custom.stock'].search([
                ('product_id', '=', record.product_id.id),
                ('project_id', '=', record.project_id.id)
            ], limit=1)

            if stock:
                stock.quantity += record.quantity

        return super(CunsomationStock, self).unlink()

