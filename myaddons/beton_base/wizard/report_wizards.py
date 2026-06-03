from odoo import api, fields, models
from odoo.exceptions import UserError


# ============================================================
# 0. FILTRE PAR PÉRIODE - COÛTS DE REVIENT
# ============================================================
class CoutRevientPeriodFilterWizard(models.TransientModel):
    _name = 'cout.revient.period.filter.wizard'
    _description = 'Filtrer les Coûts de Revient par Période'

    date_from = fields.Date(string='De', required=True)
    date_to = fields.Date(string='Au', required=True)

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for wizard in self:
            if wizard.date_from > wizard.date_to:
                raise UserError("La date 'De' doit être inférieure ou égale à la date 'Au'.")

    def action_apply_filter(self):
        self.ensure_one()
        domain = [
            ('periode', '>=', self.date_from),
            ('periode', '<=', self.date_to),
        ]
        return {
            'name': 'Coûts de Revient du %s au %s' % (
                self.date_from.strftime("%d/%m/%Y"),
                self.date_to.strftime("%d/%m/%Y"),
            ),
            'type': 'ir.actions.act_window',
            'res_model': 'beton.cout.revient',
            'view_mode': 'tree,form',
            'domain': domain,
            'context': dict(self.env.context, create=False),
        }


# ============================================================
# 1. PRODUITS
# ============================================================
class ProductReportWizard(models.TransientModel):
    _name = 'product.report.wizard'
    _description = 'Assistant Rapport Produits'

    date_from = fields.Date(string="Période du")
    date_to = fields.Date(string="Période au")

    classification_produit = fields.Selection([
        ('matiere_premiere', 'Matière première'),
    ], string="Classification produit")

    # Type de matière : choix multiple (cases à cocher)
    type_matiere_ciment = fields.Boolean(string="Ciment")
    type_matiere_sable = fields.Boolean(string="Sable")
    type_matiere_gravier = fields.Boolean(string="Gravier")
    type_matiere_adjuvant = fields.Boolean(string="Adjuvant")
    type_matiere_eau = fields.Boolean(string="Eau")
    type_matiere_autre = fields.Boolean(string="Autre")

    supplier_id = fields.Many2one(
        'res.partner',
        string="Fournisseur",
        domain="[('supplier_rank', '>', 0)]",
    )

    statut_matiere = fields.Selection([
        ('actif', 'Actif'),
        ('indisponible', 'Indisponible'),
        ('archive', 'Archivé'),
    ], string="Statut matière")
    emplacement_beton = fields.Selection([
        ('silo', 'Silo'),
        ('tremie', 'Trémie'),
        ('depot', 'Dépôt'),
        ('cuve', 'Cuve'),
    ], string="Emplacement")

    _TYPE_MATIERE_MAPPING = [
        ('ciment', 'Ciment'),
        ('sable', 'Sable'),
        ('gravier', 'Gravier'),
        ('adjuvant', 'Adjuvant'),
        ('eau', 'Eau'),
        ('autre', 'Autre'),
    ]

    def _get_label(self, field_name):
        val = getattr(self, field_name)
        if not val:
            return 'Tous'
        return dict(self._fields[field_name].selection).get(val, val)

    def _get_selected_types_matiere(self):
        return [
            key for key, _ in self._TYPE_MATIERE_MAPPING
            if getattr(self, 'type_matiere_%s' % key)
        ]

    def action_print(self):
        # NB : la période (date_from/date_to) ne filtre PAS la sélection des
        # produits — elle sert à borner les transactions (achats, ventes,
        # mouvements de stock) affichées dans le rapport. Un produit ancien
        # reste donc affiché si son activité tombe dans la période.
        domain = []
        if self.classification_produit:
            domain.append(('classification_produit', '=', self.classification_produit))
        selected_types = self._get_selected_types_matiere()
        if selected_types:
            domain.append(('type_matiere', 'in', selected_types))
        if self.supplier_id:
            domain.append(('seller_ids.partner_id', '=', self.supplier_id.id))
        if self.statut_matiere:
            domain.append(('statut_matiere', '=', self.statut_matiere))
        if self.emplacement_beton:
            domain.append(('emplacement_beton', '=', self.emplacement_beton))
        records = self.env['product.template'].search(domain)

        type_matiere_labels = [
            label for key, label in self._TYPE_MATIERE_MAPPING
            if key in selected_types
        ]
        data = {
            'doc_ids': records.ids,
            # Bornes de période transmises au rapport pour filtrer les
            # transactions (chaînes datetime, inclusives sur la journée).
            'dt_from': self.date_from.strftime('%Y-%m-%d 00:00:00') if self.date_from else False,
            'dt_to': self.date_to.strftime('%Y-%m-%d 23:59:59') if self.date_to else False,
            'filters': {
                'date_from': self.date_from.strftime('%d/%m/%Y') if self.date_from else 'Tous',
                'date_to': self.date_to.strftime('%d/%m/%Y') if self.date_to else 'Tous',
                'classification': self._get_label('classification_produit'),
                'type_matiere': ', '.join(type_matiere_labels) or 'Tous',
                'fournisseur': self.supplier_id.name or 'Tous',
                'statut': self._get_label('statut_matiere'),
                'emplacement': self._get_label('emplacement_beton'),
            },
            'total': len(records),
            'cout_moyen': sum(records.mapped('standard_price')) / len(records) if records else 0,
        }
        return self.env.ref('beton_base.action_report_product_analysis').report_action(self, data=data)


class ReportProductAnalysis(models.AbstractModel):
    _name = 'report.beton_base.report_product_analysis'
    _description = 'Rapport Analyse Produits'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['product.template'].browse((data or {}).get('doc_ids', []))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'product.template',
            'docs': docs,
            'data': data or {},
        }


class ReportProductAnalysisTemplate(models.AbstractModel):
    # Modèle de rendu du template détaillé (report_product_analysis_template).
    # Sans lui, Odoo retombe sur le rendu par défaut et tente de parcourir
    # product.template avec l'id du wizard -> aucun produit filtré n'apparaît.
    _name = 'report.beton_base.report_product_analysis_template'
    _description = 'Rapport Analytique Produit'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['product.template'].browse((data or {}).get('doc_ids', []))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'product.template',
            'docs': docs,
            'data': data or {},
        }


# ============================================================
# 2. NOMENCLATURES / FORMULES
# ============================================================
class BomReportWizard(models.TransientModel):
    _name = 'bom.report.wizard'
    _description = 'Assistant Rapport Formules Béton'

    date_from = fields.Date(string="Période du")
    date_to = fields.Date(string="Période au")
    product_tmpl_ids = fields.Many2many('product.template', 'bom_wizard_product_tmpl_rel',
                                       string="Produits",
                                       domain="[('detailed_type', '=', 'fabrique')]")
    classe_resistance = fields.Selection([
        ('b15', 'B15'), ('b20', 'B20'), ('b25', 'B25'),
        ('b30', 'B30'), ('b35', 'B35'), ('b40', 'B40'),
    ], string="Classe de résistance")
    type_beton = fields.Selection([
        ('bpe', 'BPE'),
        ('banche', 'Béton banché'),
        ('autoplacant', 'Béton autoplaçant'),
        ('fibre', 'Béton fibré'),
        ('autre', 'Autre'),
    ], string="Type de béton")
    statut_formule = fields.Selection([
        ('actif', 'Actif'),
        ('archive', 'Archivé'),
    ], string="Statut formule")

    def _get_label(self, field_name):
        val = getattr(self, field_name)
        if not val:
            return 'Tous'
        return dict(self._fields[field_name].selection).get(val, val)

    def action_print(self):
        domain = []
        if self.date_from:
            domain.append(('create_date', '>=', self.date_from))
        if self.date_to:
            domain.append(('create_date', '<=', self.date_to))
        if self.product_tmpl_ids:
            domain.append(('product_tmpl_id', 'in', self.product_tmpl_ids.ids))
        if self.classe_resistance:
            domain.append(('classe_resistance', '=', self.classe_resistance))
        if self.type_beton:
            domain.append(('type_beton', '=', self.type_beton))
        if self.statut_formule:
            domain.append(('statut_formule', '=', self.statut_formule))
        records = self.env['mrp.bom'].search(domain)
        data = {
            'doc_ids': records.ids,
            'filters': {
                'date_from': self.date_from.strftime('%d/%m/%Y') if self.date_from else 'Tous',
                'date_to': self.date_to.strftime('%d/%m/%Y') if self.date_to else 'Tous',
                'produit': ', '.join(self.product_tmpl_ids.mapped('name')) or 'Tous',
                'classe': self._get_label('classe_resistance'),
                'type_beton': self._get_label('type_beton'),
                'statut': self._get_label('statut_formule'),
            },
            'total': len(records),
            'cout_moyen': sum(records.mapped('cout_theorique_m3')) / len(records) if records else 0,
            'cout_produit_moyen': (
                sum(records.mapped('product_tmpl_id.standard_price')) / len(records)
                if records else 0
            ),
        }
        return self.env.ref('beton_base.action_report_bom_analysis').report_action(self, data=data)


class ReportBomAnalysis(models.AbstractModel):
    _name = 'report.beton_base.report_bom_analysis'
    _description = 'Rapport Analyse Formules'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['mrp.bom'].browse(data.get('doc_ids', []))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'mrp.bom',
            'docs': docs,
            'data': data or {},
        }


# ============================================================
# 3. FABRICATION / ORDRES DE PRODUCTION
# ============================================================
class ProductionReportWizard(models.TransientModel):
    _name = 'production.report.wizard'
    _description = 'Assistant Rapport Fabrication'

    date_from = fields.Date(string="Date début")
    date_to = fields.Date(string="Date fin")
    centrale_id = fields.Many2one('beton.centrale', string="Centrale")
    client_id = fields.Many2one('res.partner', string="Client",
                                 domain="[('is_client_beton', '=', True)]")
    product_ids = fields.Many2many('product.product', 'production_wizard_product_rel',
                                   string="Produits",
                                   domain="[('product_tmpl_id.detailed_type', '=', 'fabrique')]")
    operateur_id = fields.Many2one('hr.employee', string="Opérateur")
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('confirmed', 'Confirmé'),
        ('progress', 'En cours'),
        ('done', 'Fait'),
        ('cancel', 'Annulé'),
    ], string="Statut")

    def action_print(self):
        domain = []
        if self.date_from:
            domain.append(('date_start', '>=', self.date_from))
        if self.date_to:
            domain.append(('date_start', '<=', self.date_to))
        if self.centrale_id:
            domain.append(('centrale_id', '=', self.centrale_id.id))
        if self.client_id:
            domain.append(('client_id', '=', self.client_id.id))
        if self.product_ids:
            domain.append(('product_id', 'in', self.product_ids.ids))
        if self.operateur_id:
            domain.append(('operateur_id', '=', self.operateur_id.id))
        if self.state:
            domain.append(('state', '=', self.state))
        records = self.env['mrp.production'].search(domain)
        data = {
            'doc_ids': records.ids,
            'filters': {
                'date_from': str(self.date_from) if self.date_from else 'Tous',
                'date_to': str(self.date_to) if self.date_to else 'Tous',
                'centrale': self.centrale_id.name or 'Toutes',
                'client': self.client_id.name or 'Tous',
                'produit': ', '.join(self.product_ids.mapped('name')) or 'Tous',
                'operateur': self.operateur_id.name or 'Tous',
                'statut': dict(self._fields['state'].selection).get(self.state, 'Tous') if self.state else 'Tous',
            },
            'total': len(records),
            'qte_totale': sum(records.mapped('product_qty')),
            'qte_produite': sum(records.mapped('qty_produced')),
            'cout_total': sum(records.mapped('cout_total')),
        }
        return self.env.ref('beton_base.action_report_production_analysis').report_action(self, data=data)


class ReportProductionAnalysis(models.AbstractModel):
    _name = 'report.beton_base.report_production_analysis'
    _description = 'Rapport Analyse Fabrication'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['mrp.production'].browse(data.get('doc_ids', []))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'mrp.production',
            'docs': docs,
            'data': data or {},
        }


# ============================================================
# 4. LIVRAISONS (stock.picking)
# ============================================================
class PickingReportWizard(models.TransientModel):
    _name = 'picking.report.wizard'
    _description = 'Assistant Rapport Livraisons'

    date_from = fields.Date(string="Date début")
    date_to = fields.Date(string="Date fin")
    partner_id = fields.Many2one('res.partner', string="Client")
    chantier = fields.Char(string="Chantier")
    vehicle_id = fields.Many2one('fleet.vehicle', string="Camion")
    chauffeur_id = fields.Many2one('hr.employee', string="Chauffeur")
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('waiting', 'En attente'),
        ('confirmed', 'En attente'),
        ('assigned', 'Prêt'),
        ('done', 'Fait'),
        ('cancel', 'Annulé'),
    ], string="Statut")

    def action_print(self):
        domain = [('picking_type_code', '=', 'outgoing')]
        if self.date_from:
            domain.append(('scheduled_date', '>=', self.date_from))
        if self.date_to:
            domain.append(('scheduled_date', '<=', self.date_to))
        if self.partner_id:
            domain.append(('partner_id', '=', self.partner_id.id))
        if self.chantier:
            domain.append(('chantier', 'ilike', self.chantier))
        if self.vehicle_id:
            domain.append(('vehicle_id', '=', self.vehicle_id.id))
        if self.chauffeur_id:
            domain.append(('chauffeur_id', '=', self.chauffeur_id.id))
        if self.state:
            domain.append(('state', '=', self.state))
        records = self.env['stock.picking'].search(domain)
        data = {
            'doc_ids': records.ids,
            'filters': {
                'date_from': str(self.date_from) if self.date_from else 'Tous',
                'date_to': str(self.date_to) if self.date_to else 'Tous',
                'client': self.partner_id.name or 'Tous',
                'chantier': self.chantier or 'Tous',
                'camion': self.vehicle_id.name or 'Tous',
                'chauffeur': self.chauffeur_id.name or 'Tous',
                'statut': dict(self._fields['state'].selection).get(self.state, 'Tous') if self.state else 'Tous',
            },
            'total': len(records),
            'distance_totale': sum(records.mapped('distance')),
        }
        return self.env.ref('beton_base.action_report_picking_analysis').report_action(self, data=data)


class ReportPickingAnalysis(models.AbstractModel):
    _name = 'report.beton_base.report_picking_analysis'
    _description = 'Rapport Analyse Livraisons'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['stock.picking'].browse(data.get('doc_ids', []))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'stock.picking',
            'docs': docs,
            'data': data or {},
        }


# ============================================================
# 5. COÛTS DE REVIENT
# ============================================================
class CoutRevientReportWizard(models.TransientModel):
    _name = 'cout.revient.report.wizard'
    _description = 'Assistant Rapport Coûts de Revient'

    date_from = fields.Date(string="Période début")
    date_to = fields.Date(string="Période fin")
    formule_beton_id = fields.Many2one('mrp.bom', string="Formule béton")
    marge_type = fields.Selection([
        ('positive', 'Marge positive uniquement'),
        ('negative', 'Marge négative uniquement'),
    ], string="Type de marge")

    def action_print(self):
        domain = []
        if self.date_from:
            domain.append(('periode', '>=', self.date_from))
        if self.date_to:
            domain.append(('periode', '<=', self.date_to))
        if self.formule_beton_id:
            domain.append(('formule_beton_id', '=', self.formule_beton_id.id))
        if self.marge_type == 'positive':
            domain.append(('marge_brute', '>', 0))
        elif self.marge_type == 'negative':
            domain.append(('marge_brute', '<=', 0))
        records = self.env['beton.cout.revient'].search(domain)
        data = {
            'doc_ids': records.ids,
            'filters': {
                'date_from': str(self.date_from) if self.date_from else 'Tous',
                'date_to': str(self.date_to) if self.date_to else 'Tous',
                'formule': self.formule_beton_id.display_name or 'Toutes',
                'marge': dict(self._fields['marge_type'].selection).get(self.marge_type, 'Tous') if self.marge_type else 'Tous',
            },
            'total': len(records),
            'cout_moyen': sum(records.mapped('cout_total_m3')) / len(records) if records else 0,
            'marge_moyenne': sum(records.mapped('marge_brute')) / len(records) if records else 0,
        }
        return self.env.ref('beton_base.action_report_cout_analysis').report_action(self, data=data)


class ReportCoutAnalysis(models.AbstractModel):
    _name = 'report.beton_base.report_cout_analysis'
    _description = 'Rapport Analyse Coûts'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['beton.cout.revient'].browse(data.get('doc_ids', []))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'beton.cout.revient',
            'docs': docs,
            'data': data or {},
        }


# ============================================================
# 6. MOUVEMENTS DE STOCK
# ============================================================
class StockMoveReportWizard(models.TransientModel):
    _name = 'stock.move.report.wizard'
    _description = 'Assistant Rapport Mouvements de Stock'

    date_from = fields.Date(string="Date début")
    date_to = fields.Date(string="Date fin")
    product_ids = fields.Many2many('product.product', 'stock_move_wizard_product_rel',
                                   string="Produits")
    location_id = fields.Many2one('stock.location', string="Emplacement source")
    location_dest_id = fields.Many2one('stock.location', string="Emplacement destination")
    state = fields.Selection([
        ('draft', 'Nouveau'),
        ('confirmed', 'En attente'),
        ('assigned', 'Disponible'),
        ('done', 'Fait'),
        ('cancel', 'Annulé'),
    ], string="Statut")

    def action_print(self):
        domain = []
        if self.date_from:
            domain.append(('date', '>=', self.date_from))
        if self.date_to:
            domain.append(('date', '<=', self.date_to))
        if self.product_ids:
            domain.append(('product_id', 'in', self.product_ids.ids))
        if self.location_id:
            domain.append(('location_id', '=', self.location_id.id))
        if self.location_dest_id:
            domain.append(('location_dest_id', '=', self.location_dest_id.id))
        if self.state:
            domain.append(('state', '=', self.state))
        records = self.env['stock.move'].search(domain, limit=500)
        data = {
            'doc_ids': records.ids,
            'filters': {
                'date_from': str(self.date_from) if self.date_from else 'Tous',
                'date_to': str(self.date_to) if self.date_to else 'Tous',
                'produit': ', '.join(self.product_ids.mapped('name')) or 'Tous',
                'emplacement_source': self.location_id.complete_name or 'Tous',
                'emplacement_dest': self.location_dest_id.complete_name or 'Tous',
                'statut': dict(self._fields['state'].selection).get(self.state, 'Tous') if self.state else 'Tous',
            },
            'total': len(records),
            'qte_totale': sum(records.mapped('product_uom_qty')),
            'cout_total': sum(records.mapped('cout_total')),
        }
        return self.env.ref('beton_base.action_report_stock_move_analysis').report_action(self, data=data)


class ReportStockMoveAnalysis(models.AbstractModel):
    _name = 'report.beton_base.report_stock_move_analysis'
    _description = 'Rapport Analyse Mouvements'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['stock.move'].browse(data.get('doc_ids', []))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'stock.move',
            'docs': docs,
            'data': data or {},
        }


# ============================================================
# 7. VENTES (sale.order)
# ============================================================
class SaleReportWizard(models.TransientModel):
    _name = 'sale.report.wizard'
    _description = 'Assistant Rapport Ventes'

    date_from = fields.Date(string="Date début")
    date_to = fields.Date(string="Date fin")
    client_id = fields.Many2one('res.partner', string="Client",
                                domain="[('is_client_beton', '=', True)]")
    product_ids = fields.Many2many('product.product', 'sale_wizard_product_rel',
                                   string="Produits")
    state = fields.Selection([
        ('draft', 'Devis'),
        ('sent', 'Devis envoyé'),
        ('sale', 'Bon de commande'),
        ('done', 'Verrouillé'),
        ('cancel', 'Annulé'),
    ], string="Statut")

    def action_print(self):
        domain = []
        if self.date_from:
            domain.append(('date_order', '>=', self.date_from))
        if self.date_to:
            domain.append(('date_order', '<=', self.date_to))
        if self.client_id:
            domain.append(('partner_id', '=', self.client_id.id))
        if self.product_ids:
            domain.append(('order_line.product_id', 'in', self.product_ids.ids))
        if self.state:
            domain.append(('state', '=', self.state))
        records = self.env['sale.order'].search(domain)
        data = {
            'doc_ids': records.ids,
            'filters': {
                'date_from': self.date_from.strftime('%d/%m/%Y') if self.date_from else 'Tous',
                'date_to': self.date_to.strftime('%d/%m/%Y') if self.date_to else 'Tous',
                'client': self.client_id.name or 'Tous',
                'produit': ', '.join(self.product_ids.mapped('name')) or 'Tous',
                'statut': dict(self._fields['state'].selection).get(self.state, 'Tous') if self.state else 'Tous',
            },
            'total': len(records),
            'montant_ht': sum(records.mapped('amount_untaxed')),
            'montant_ttc': sum(records.mapped('amount_total')),
        }
        return self.env.ref('beton_base.action_report_sale_analysis').report_action(self, data=data)


class ReportSaleAnalysis(models.AbstractModel):
    _name = 'report.beton_base.report_sale_analysis'
    _description = 'Rapport Analyse Ventes'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['sale.order'].browse(data.get('doc_ids', []))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'sale.order',
            'docs': docs,
            'data': data or {},
        }


# ============================================================
# 8. ACHATS (purchase.order)
# ============================================================
class PurchaseReportWizard(models.TransientModel):
    _name = 'purchase.report.wizard'
    _description = 'Assistant Rapport Achats'

    date_from = fields.Date(string="Date début")
    date_to = fields.Date(string="Date fin")
    fournisseur_id = fields.Many2one('res.partner', string="Fournisseur",
                                     domain="[('type_partenaire_beton', '=', 'fournisseur')]")
    product_ids = fields.Many2many('product.product', 'purchase_wizard_product_rel',
                                   string="Produits")
    state = fields.Selection([
        ('draft', 'Demande de prix'),
        ('sent', 'Demande de prix envoyée'),
        ('purchase', 'Bon de commande'),
        ('done', 'Verrouillé'),
        ('cancel', 'Annulé'),
    ], string="Statut")

    def action_print(self):
        domain = []
        if self.date_from:
            domain.append(('date_order', '>=', self.date_from))
        if self.date_to:
            domain.append(('date_order', '<=', self.date_to))
        if self.fournisseur_id:
            domain.append(('partner_id', '=', self.fournisseur_id.id))
        if self.product_ids:
            domain.append(('order_line.product_id', 'in', self.product_ids.ids))
        if self.state:
            domain.append(('state', '=', self.state))
        records = self.env['purchase.order'].search(domain)
        data = {
            'doc_ids': records.ids,
            'filters': {
                'date_from': self.date_from.strftime('%d/%m/%Y') if self.date_from else 'Tous',
                'date_to': self.date_to.strftime('%d/%m/%Y') if self.date_to else 'Tous',
                'fournisseur': self.fournisseur_id.name or 'Tous',
                'produit': ', '.join(self.product_ids.mapped('name')) or 'Tous',
                'statut': dict(self._fields['state'].selection).get(self.state, 'Tous') if self.state else 'Tous',
            },
            'total': len(records),
            'montant_ht': sum(records.mapped('amount_untaxed')),
            'montant_ttc': sum(records.mapped('amount_total')),
        }
        return self.env.ref('beton_base.action_report_purchase_analysis').report_action(self, data=data)


class ReportPurchaseAnalysis(models.AbstractModel):
    _name = 'report.beton_base.report_purchase_analysis'
    _description = 'Rapport Analyse Achats'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['purchase.order'].browse(data.get('doc_ids', []))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'purchase.order',
            'docs': docs,
            'data': data or {},
        }
