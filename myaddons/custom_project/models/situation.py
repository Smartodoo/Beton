import base64
import io
from datetime import datetime

import xlsxwriter
from odoo import models, fields, api, _


# from odoo17.odoo.exceptions import UserError
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
import base64
import io
from datetime import datetime






class SituationSousTraitant(models.Model):
    _name = "situation.sous.traitants"
    _description = "la situation des articles pour chaque sous traitant"

    # article = fields.Many2one("stock.articles", string="Article", domain="[('project_id','=',project_id)]")
    no = fields.Char(string="N")
    article1 = fields.Char(string="Article")
    # quantity_given = fields.Float(string="QTD(1)", help="Quantité donnée")
    supply_quantity = fields.Float(string="Q.APP(2)", help="Quantité d'approvisionnement")
    price_unit_sale = fields.Float(string="P.U.V(3)", help="Prix unitaire de vente")
    done_quantity = fields.Float(string="QR mois préc(4)", help="Quantité réalisée le mois précédent")
    done_quantity_current = fields.Float(string="QR M.E.C(5)", help="Quantité réalisée ce mois en cours")
    total_done_quantity = fields.Float(string="QRT(6)", compute='_compute_differences',
                                       help="Quantité réalisée totale(le mois précédent + ce mois)")
    price_unit_convention = fields.Float(string="P.U.C(7)", help="Prix unitaire de la convention")
    # difference1 = fields.Float(string="Diff(1)-(2)", compute='_compute_differences')
    difference2 = fields.Float(string="Diff(2)-(5)", compute='_compute_differences')
    supply_amount = fields.Float(string="Mnt appro(2)*(3)", compute='_compute_differences',
                                 help="Montant d'approvisionnement")
    done_amount = fields.Float(string="Mnt.R(6)*(7)", compute='_compute_differences', help="Montant réalisé")
    project_id = fields.Many2one(related="situation_id.project_id", string="Projet", store=True)
    # produit = fields.Many2many('custom.stock', string="Produit", domain="[('project_id', '=', project_id)]")
    original_subcontractor_id = fields.Many2one(related="situation_id.original_subcontractor_id",
                                                string="Sous-traitant d'origine",
                                                domain="[('contact_type','=','SUBCONTRACTOR')]", store=True)
    product_stock = fields.Many2one('custom.stock', string="Produit", domain="[('partner_id', '=', original_subcontractor_id)]")

    situation_id = fields.Many2one("situation", string="Situation", required=True)
    lot_id = fields.Many2one('custom.task.lots', string="Lot",
                             domain="[('project_id', '=', project_id)]")
    def update_stock_on_supply_change(self, old_supply, new_supply):
        """Mettre à jour le stock quand la quantité d'approvisionnement change."""
        diff = new_supply - old_supply
        if diff == 0:
            return

        stock = self.product_stock
        if stock:
            # si supply a augmenté => diminuer stock
            # si supply a diminué => ré-augmenter stock
            stock.quantity -= diff

    @api.model_create_multi
    def create(self, vals_list):
        recs = super().create(vals_list)

        Finale = self.env['situation.final']
        for rec in recs:
            art_id = rec.article1
            domain = [
                ('project_id', '=', rec.project_id.id),
                ('article2', '=', art_id),
            ]
            finale_rec = Finale.search(domain, limit=1)
            if not finale_rec:
                Finale.create({
                    'project_id': rec.project_id.id,
                    'article2': art_id,
                    'no': rec.no,
                    'supply_quantity': rec.supply_quantity,
                    'done_quantity': rec.done_quantity,
                })
            else:
                finale_rec.supply_quantity += rec.supply_quantity
                finale_rec.done_quantity += rec.done_quantity

            # Mise à jour stock sur création
            rec.update_stock_on_supply_change(0, rec.supply_quantity)
        return recs

    def write(self, vals):
        for rec in self:
            # ----- Cas 1: Mise à jour de la quantité supply -----
            if "supply_quantity" in vals:
                old_supply = rec.supply_quantity
                new_supply = vals.get("supply_quantity", old_supply)
                rec.update_stock_on_supply_change(old_supply, new_supply)

            # ----- Cas 2: Changement de produit -----
            if "product_stock" in vals:
                new_product_id = vals.get("product_stock")
                old_product = rec.product_stock
                new_product = self.env['custom.stock'].browse(new_product_id) if new_product_id else False

                # restituer l'ancienne quantité au stock de l’ancien produit
                if old_product:
                    old_product.quantity += rec.supply_quantity

                # retirer la quantité du nouveau produit
                if new_product:
                    new_product.quantity -= vals.get("supply_quantity", rec.supply_quantity)

        return super().write(vals)

    @api.onchange('date')
    def _onchange_article_fill_last_done_quantity(self):

        if not self.article1 or not self.situation_id:
            return

        # bloqué la creation d'un article deux fois
        duplicates = self.situation_id.situation_sous_traitant_ids.filtered(
            lambda l: l.article1 == self.article1 and l != self and l.situation_id == self.situation_id
        )

        if duplicates:
            raise UserError(_("L'article %s est déjà ajouté à cette situation.") % self.article.name)

        # Remplir done_quantity_current avec la dernière situation enregistrée pour le même article
        project = self.situation_id.project_id
        subcontractor = self.situation_id.original_subcontractor_id

        domain = [
            ('project_id', '=', project.id),
            ('original_subcontractor_id', '=', subcontractor.id)
        ]

        # Exclure self.situation_id seulement s’il est "réel" (enregistré)
        if self.situation_id.id and isinstance(self.situation_id.id, int):
            domain.append(('id', '!=', self.situation_id.id))

        last_situation = self.env['situation'].search(domain, order='date desc', limit=1)

        if last_situation:
            for line in last_situation.situation_sous_traitant_ids:
                if line.article1 == self.article1:
                    self.done_quantity = line.done_quantity_current

    @api.depends('supply_quantity', 'done_quantity', 'done_quantity_current', 'price_unit_sale',
                 'price_unit_convention', 'total_done_quantity')
    def _compute_differences(self):
        for rec in self:
            # rec.difference1 = rec.quantity_given - rec.supply_quantity
            rec.difference2 = rec.supply_quantity - rec.done_quantity_current
            rec.total_done_quantity = rec.done_quantity + rec.done_quantity_current
            rec.supply_amount = rec.supply_quantity * rec.price_unit_sale
            rec.done_amount = rec.total_done_quantity * rec.price_unit_convention


# class SituationFinale(models.Model):
#     _name = "situation.final"
#     _description = "Situation finale des articles"
#
#     # article = fields.Many2one("stock.articles", string="Article", domain="[('project_id','=',project_id)]")
#     no = fields.Char(string="N")
#     article2 = fields.Char(string="Article")
#     quantity_chantier = fields.Float(string="Quantité chantier")
#     # quantity_given = fields.Float(string="Quantité donnée")
#     supply_quantity = fields.Float(string="Quantité d'approvisionnement")
#     done_quantity = fields.Float(string="Quantité réalisée")
#     # difference1 = fields.Float(string="Différence 1", compute='_compute_differences')
#     difference2 = fields.Float(string="Différence 2", compute='_compute_differences')
#     difference3 = fields.Float(string="Différence 3", compute='_compute_differences')
#     project_id = fields.Many2one("custom.project", string="Projet", required=True)
#
#     @api.depends('quantity_chantier', 'supply_quantity', 'done_quantity')
#     def _compute_differences(self):
#         for rec in self:
#             # rec.difference1 = rec.quantity_given - rec.supply_quantity
#             rec.difference2 = rec.supply_quantity - rec.done_quantity
#             rec.difference3 = rec.quantity_chantier - rec.done_quantity
#


class SituationFinale(models.Model):
    _name = "situation.final"
    _description = "Situation finale des articles"

    no = fields.Char(string="N")
    article2 = fields.Char(string="Article")
    quantity_chantier = fields.Float(string="Quantité chantier")
    supply_quantity = fields.Float(string="Quantité d'approvisionnement")
    done_quantity = fields.Float(string="Quantité réalisée")
    difference2 = fields.Float(string="Différence 2", compute='_compute_differences')
    difference3 = fields.Float(string="Différence 3", compute='_compute_differences')
    project_id = fields.Many2one("custom.project", string="Projet", required=True)

    @api.depends('quantity_chantier', 'supply_quantity', 'done_quantity')
    def _compute_differences(self):
        for rec in self:
            rec.difference2 = rec.supply_quantity - rec.done_quantity
            rec.difference3 = rec.quantity_chantier - rec.done_quantity

    def export_final_situation_xlsx(self):
        """Génère un XLSX pour la situation finale avec tous les sous-traitants et lots"""
        self.ensure_one()

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Situation Finale')

        # Styles
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 16,
            'align': 'center',
            'valign': 'vcenter'
        })
        subtitle_format = workbook.add_format({
            'italic': True,
            'font_size': 11,
            'align': 'center',
            'valign': 'vcenter'
        })
        bold = workbook.add_format({'bold': True, 'bg_color': '#D9E1F2', 'border': 1})
        money_format = workbook.add_format({'num_format': '#,##0.00', 'border': 1})
        normal_format = workbook.add_format({'border': 1})
        header_format = workbook.add_format({'bold': True, 'border': 1, 'bg_color': '#E6E6E6'})
        total_format = workbook.add_format({'bold': True, 'border': 1, 'num_format': '#,##0.00', 'bg_color': '#F2F2F2'})

        # Column widths
        worksheet.set_column(0, 0, 6)  # N
        worksheet.set_column(1, 1, 35)  # Article
        worksheet.set_column(2, 6, 15)  # Other columns

        # === En-tête ===
        title = "SITUATION FINALE DES TRAVAUX"
        project_name = self.project_id.name or "Projet non défini"
        date_str = datetime.now().strftime("%d/%m/%Y")

        worksheet.merge_range('A1:G1', title, title_format)
        worksheet.merge_range('A2:G2', f"Projet : {project_name}", subtitle_format)
        worksheet.merge_range('A3:G3', f"Date de situation : {date_str}", subtitle_format)
        worksheet.write_blank('A4', None)

        # === Table header ===
        headers = [
            'N',
            'Article',
            'Quantité chantier',
            'Quantité d\'approvisionnement',
            'Quantité réalisée',
            'Différence 2',
            'Différence 3'
        ]

        for col, header in enumerate(headers):
            worksheet.write(4, col, header, header_format)

        # === Get all final situation records for this project ===
        final_records = self.search([('project_id', '=', self.project_id.id)])

        current_row = 5
        total_chantier = 0
        total_supply = 0
        total_done = 0
        total_diff2 = 0
        total_diff3 = 0

        # === Write data rows ===
        for record in final_records:
            worksheet.write(current_row, 0, record.no or '', normal_format)
            worksheet.write(current_row, 1, record.article2 or '', normal_format)
            worksheet.write_number(current_row, 2, record.quantity_chantier or 0.0, money_format)
            worksheet.write_number(current_row, 3, record.supply_quantity or 0.0, money_format)
            worksheet.write_number(current_row, 4, record.done_quantity or 0.0, money_format)
            worksheet.write_number(current_row, 5, record.difference2 or 0.0, money_format)
            worksheet.write_number(current_row, 6, record.difference3 or 0.0, money_format)

            # Accumulate totals
            total_chantier += record.quantity_chantier or 0.0
            total_supply += record.supply_quantity or 0.0
            total_done += record.done_quantity or 0.0
            total_diff2 += record.difference2 or 0.0
            total_diff3 += record.difference3 or 0.0

            current_row += 1

        # === Write totals row ===
        worksheet.write(current_row, 1, "TOTAUX", bold)
        worksheet.write_number(current_row, 2, total_chantier, total_format)
        worksheet.write_number(current_row, 3, total_supply, total_format)
        worksheet.write_number(current_row, 4, total_done, total_format)
        worksheet.write_number(current_row, 5, total_diff2, total_format)
        worksheet.write_number(current_row, 6, total_diff3, total_format)

        # === Add section for subcontractors ===
        current_row += 2
        worksheet.write(current_row, 0, "SOUS-TRAITANTS ASSOCIÉS AU PROJET", bold)
        current_row += 1

        # Get all subcontractors for this project
        subcontractors = self.env['projects.associated'].search([
            ('project_id', '=', self.project_id.id)
        ]).mapped('original_subcontractor_id')

        if subcontractors:
            for sub in subcontractors:
                worksheet.write(current_row, 0, f"• {sub.name or 'Sous-traitant sans nom'}", normal_format)
                current_row += 1
        else:
            worksheet.write(current_row, 0, "Aucun sous-traitant associé", normal_format)
            current_row += 1

        # === Add section for lots ===
        current_row += 1
        worksheet.write(current_row, 0, "LOTS DU PROJET", bold)
        current_row += 1

        # Get all lots for this project
        lots = self.env['custom.task.lots'].search([
            ('project_id', '=', self.project_id.id)
        ])

        if lots:
            for lot in lots:
                worksheet.write(current_row, 0, f"• {lot.name or 'Lot sans nom'}", normal_format)
                current_row += 1
        else:
            worksheet.write(current_row, 0, "Aucun lot défini", normal_format)
            current_row += 1

        # Finalize workbook
        workbook.close()
        output.seek(0)
        file_data = output.read()
        output.close()

        fname = '{} - situation finale {}.xlsx'.format(project_name, date_str.replace('/', '-'))

        attachment = self.env['ir.attachment'].create({
            'name': fname,
            'type': 'binary',
            'datas': base64.b64encode(file_data),
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }

    # Alternative method to export final situation for a specific project
    def export_project_final_situation_xlsx(self, project_id):
        """Export final situation for a specific project"""
        project = self.env['custom.project'].browse(project_id)
        if not project:
            raise models.UserError(_("Projet non trouvé"))

        # Create a temporary record to use the export method
        temp_record = self.create({
            'project_id': project_id,
            'no': 'TEMP',
            'article2': 'TEMP'
        })

        return temp_record.export_final_situation_xlsx()


class Situation(models.Model):
    _name = "situation"
    _description = "Situation des sous-traitants et des articles de stock dans le projet BTP"

    name = fields.Char("Nom de la situation", required=True)
    date = fields.Date("Date de la situation", required=True)
    situation_sous_traitant_ids = fields.One2many("situation.sous.traitants", "situation_id",
                                                  string="Situation des sous-traitants")
    currency_id = fields.Many2one("res.currency", string="Devise", default=lambda self: self.env.company.currency_id)
    project_id = fields.Many2one("custom.project", string="Projet", required=True)
    lot_ids = fields.Many2many('custom.task.lots', string="Lot",
                               help="Lot associé aux tâches du projet",
                               domain="[('project_id', '=', project_id)]")
    original_subcontractor_id = fields.Many2one('res.partner', string="Sous-traitant d'origine",
                                                domain="[('contact_type','=','SUBCONTRACTOR')]")
    situation_amount_previous = fields.Float("Montant de la situation précédente",
                                             compute="_get_previous_situation_amount", )
    situation_amount = fields.Float("Montant de la situation", compute="_compute_totals")
    situation_amount_difference = fields.Float("Différence montant situations", compute="_compute_totals")
    tva = fields.Float("TVA", compute="_compute_totals")
    ttc_amount = fields.Float("Montant TTC", compute="_compute_totals")
    guarantee_retained = fields.Float("Garantie retenue", compute="_compute_totals")
    net_amount = fields.Float("Montant net", compute="_compute_totals")
    previous_existing = fields.Boolean(string="Situation précédente existante",
                                       compute="_get_previous_situation_amount")
    total_done_amount = fields.Float("Montant total réalisé", compute="_compute_totals")
    total_R_G_C = fields.Float("Total RGC", compute="_get_previous_situation_amount")

    def _get_previous_situation_amount(self):
        for rec in self:
            previous_situation = self.env['situation'].search([
                ('project_id', '=', rec.project_id.id),
                ('original_subcontractor_id', '=', rec.original_subcontractor_id.id),
                ('create_date', '<', rec.create_date)
            ], order='date desc', limit=1)
            rec.previous_existing = bool(previous_situation)
            rec.situation_amount_previous = previous_situation.total_done_amount if previous_situation else 0.0
            previous_situations = self.env['situation'].search([('project_id', '=', rec.project_id.id),
                                                                ('original_subcontractor_id', '=',
                                                                 rec.original_subcontractor_id.id),
                                                                ('create_date', '<=', rec.create_date)
                                                                ], order='date desc')
            rec.total_R_G_C = sum(situation.guarantee_retained for situation in previous_situations)

    @api.depends('situation_sous_traitant_ids.done_amount', 'situation_sous_traitant_ids.supply_amount',
                 'project_id.tax_ids.amount')
    def _compute_totals(self):
        for rec in self:
            total_app = sum(sous_traitant.supply_amount for sous_traitant in rec.situation_sous_traitant_ids)
            rec.total_done_amount = sum(
                sous_traitant.done_amount for sous_traitant in rec.situation_sous_traitant_ids)
            rec.situation_amount_difference = rec.total_done_amount - rec.situation_amount_previous
            rec.situation_amount = rec.situation_amount_difference - total_app
            rec.tva = rec.situation_amount * 0.19  # Assuming a fixed TVA rate of 19%
            rec.ttc_amount = rec.situation_amount + rec.tva
            rec.guarantee_retained = rec.ttc_amount * 0.05
            rec.net_amount = rec.ttc_amount - rec.guarantee_retained

    @api.model
    def default_get(self, fields):

        defaults = super().default_get(fields)
        project_id = self.env.context.get('default_project_id')
        subcontractor_id = self.env.context.get('default_original_subcontractor_id')
        last_situation_id = self.env['situation'].search([
            ('project_id', '=', project_id),
            ('original_subcontractor_id', '=', subcontractor_id),
        ], order='date desc', limit=1)
        if project_id and subcontractor_id:
            assoc = self.env['projects.associated'].search([
                ('project_id', '=', project_id),
                ('original_subcontractor_id', '=', subcontractor_id),
            ], limit=1)

            if assoc:
                defaults['lot_ids'] = [(6, 0, assoc.lots_id.ids)]
                task_lines = []
                all_lots = self.env['custom.task.lots'].search([('project_id', '=', project_id)])

                for lot in all_lots:
                    # Filtrer les tâches par lot
                    lot_tasks = assoc.task_line_ids.filtered(lambda line: line.task_id.lot_id == lot)

                for line in assoc.task_line_ids:
                        # Récupérer les lignes correspondantes dans la dernière situation (peut être plusieurs)
                        last_lines = last_situation_id.situation_sous_traitant_ids.filtered(
                            lambda l: l.article1 == line.task_id.name) if last_situation_id else self.env[
                            'situation.sous.traitants']
                        # Prendre la première correspondance si existe, sinon 0.0
                        done_qty = last_lines[0].done_quantity_current if last_lines else 0.0

                        task_lines.append((0, 0, {
                            'article1': line.task_id.name,
                            'no': line.task_id.no,
                            'price_unit_convention': line.unit_price,
                            'done_quantity': done_qty,
                            'lot_id': line.task_id.lot_id.id,
                        }))

                defaults['situation_sous_traitant_ids'] = task_lines

        return defaults

    def _situation_xlsx_rows(self):
        """Prépare les lignes du tableau XLSX pour cette situation."""
        rows = []
        return rows

    def _get_tasks_of_lot(self, lot):
        """Try to retrieve tasks from a lot record using common field names.
        Return a list of dicts with minimal fields: {'name', 'no', 'unit_price'}."""
        tasks = []
        # possible fields that could hold tasks or task lines
        candidates = ['task_ids', 'task_line_ids', 'tasks', 'lines', 'task_lines']
        for cand in candidates:
            if hasattr(lot, cand):
                records = getattr(lot, cand) or []
                for rec in records:
                    if hasattr(rec, 'task_id'):
                        t = rec.task_id
                    else:
                        t = rec
                    if not t:
                        continue
                    tasks.append({
                        'name': getattr(t, 'name', '') or getattr(t, 'task_name', '') or '',
                        'no': getattr(t, 'no', '') or '',
                        'unit_price': float(getattr(t, 'unit_price', 0.0) or 0.0)
                    })
                if tasks:
                    break
        return tasks

    def _get_tasks_of_lot_existing_in_situation(self, lot):
        """Return tasks from lot but only those whose names exist in this situation's lines."""
        raw_tasks = self._get_tasks_of_lot(lot)
        if not raw_tasks:
            return []

        names_in_situation = {
            (line.article1 or '').strip().lower()
            for line in self.situation_sous_traitant_ids
            if line.article1
        }

        filtered = []
        for t in raw_tasks:
            tname = (t.get('name') or '').strip().lower()
            if tname and tname in names_in_situation:
                filtered.append(t)
        return filtered

    def export_situation_xlsx(self):
        """Génère un XLSX pour la situation avec titre, projet, date,
        puis sections par lot et sous-total par lot, et totaux récapitulatifs à la fin."""
        self.ensure_one()

        if not self.situation_sous_traitant_ids:
            raise UserError(_("Pas de lignes à exporter pour cette situation."))

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Situation')

        # Styles
        title_format = workbook.add_format({'bold': True, 'font_size': 16, 'align': 'center', 'valign': 'vcenter'})
        subtitle_format = workbook.add_format({'italic': True, 'font_size': 11, 'align': 'center', 'valign': 'vcenter'})
        bold = workbook.add_format({'bold': True, 'bg_color': '#D9E1F2', 'border': 1})
        money_format = workbook.add_format({'num_format': '#,##0.00', 'border': 1})
        normal_format = workbook.add_format({'border': 1})
        lot_header_format = workbook.add_format({'bold': True, 'border': 1})
        lot_subtotal_format = workbook.add_format({'bold': True, 'border': 1, 'num_format': '#,##0.00'})
        summary_label_format = workbook.add_format({'bold': True})
        summary_money_format = workbook.add_format({'num_format': '#,##0.00', 'bold': True})

        # Column widths
        worksheet.set_column(0, 0, 6)
        worksheet.set_column(1, 1, 35)
        worksheet.set_column(2, 9, 15)

        # === En-tête ===
        title = "SITUATION DES TRAVAUX"
        project_name = self.project_id.name or "Projet non défini"
        date_str = self.date.strftime("%d/%m/%Y") if self.date else datetime.now().strftime("%d/%m/%Y")

        worksheet.merge_range('A1:J1', title, title_format)
        worksheet.merge_range('A2:J2', f"Projet : {project_name}", subtitle_format)
        worksheet.merge_range('A3:J3', f"Date de situation : {date_str}", subtitle_format)
        worksheet.write_blank('A4', None)
        worksheet.write_blank('A5', None)

        # === Main tableau (situation_sous_traitant_ids) ===
        rows = self._situation_xlsx_rows()
        start_row = 5  # ligne 6 (index 5)

        for r_idx, row in enumerate(rows):
            for c_idx, cell in enumerate(row):
                fmt = normal_format
                if r_idx == 0:
                    fmt = bold
                elif isinstance(cell, (int, float)):
                    fmt = money_format
                worksheet.write(start_row + r_idx, c_idx, cell or '', fmt)

        current_row = start_row + len(rows) + 1  # leave a blank line before lots

        # === Sous-traitant info (NEW) ===
        subcontractor = self.original_subcontractor_id
        if subcontractor:
            worksheet.write(current_row, 0, f"Sous-traitant : {subcontractor.name}", lot_header_format)
        else:
            worksheet.write(current_row, 0, "Sous-traitant : (non défini)", lot_header_format)
        current_row += 2

        # === Sections per Lot ===
        if self.lot_ids:
            worksheet.write(current_row, 0, "DETAIL PAR LOTS", lot_header_format)
            current_row += 1
            for lot in self.lot_ids:
                lot_name = getattr(lot, 'name', str(lot)) or "Lot (sans nom)"
                worksheet.write(current_row, 0, f"Lot: {lot_name}", lot_header_format)
                current_row += 1

                # Write header for lot tasks
                lot_headers = ['N', 'Tâche / Article', 'Q.APP (2)', 'P.U.V (3)', 'QR mois préc (4)',
                               'QR M.E.C (5)', 'QRT (6)', 'P.U.C (7)', 'Mnt appro (2)*(3)', 'Mnt.R (6)*(7)']
                for c_idx, h in enumerate(lot_headers):
                    worksheet.write(current_row, c_idx, h, bold)
                current_row += 1

                # Get tasks for lot but only those that also exist in this situation's lines
                tasks = self._get_tasks_of_lot_existing_in_situation(lot)

                # If no explicit tasks on lot filtered by situation, try to infer tasks from situation lines that reference this lot
                if not tasks:
                    lines_for_lot = self.situation_sous_traitant_ids.filtered(
                        lambda l: getattr(l, 'lot_id', False) and l.lot_id == lot)
                    if lines_for_lot:
                        for idx, l in enumerate(lines_for_lot, start=1):
                            tasks.append({'name': l.article1 or f'Article {idx}', 'no': l.no or idx,
                                          'unit_price': float(l.price_unit_convention or 0.0)})

                # If still no tasks, write a note
                if not tasks:
                    worksheet.write(current_row, 0, '-', normal_format)
                    worksheet.write(current_row, 1, "Aucune tâche trouvée pour ce lot", normal_format)
                    current_row += 1
                    worksheet.write(current_row, 7, "Sous-total lot", lot_header_format)
                    worksheet.write_number(current_row, 9, 0.0, lot_subtotal_format)
                    current_row += 2
                    continue

                # For each task, try to find matching situation lines by name and compute amounts
                lot_subtotal = 0.0
                for idx, task in enumerate(tasks, start=1):
                    task_name = task.get('name') or ''
                    task_no = task.get('no') or idx
                    task_unit_price = float(task.get('unit_price') or 0.0)

                    # find matching lines in situation by comparing article1 with task name (case-insensitive trim)
                    matched_lines = self.situation_sous_traitant_ids.filtered(
                        lambda l: (l.article1 or '').strip().lower() == (task_name or '').strip().lower()
                    )

                    supply_qty = sum(float(getattr(l, 'supply_quantity', 0.0) or 0.0) for l in
                                     matched_lines) if matched_lines else 0.0
                    price_unit_sale = matched_lines[0].price_unit_sale if matched_lines and hasattr(matched_lines[0],
                                                                                                    'price_unit_sale') else 0.0
                    done_prev = sum(
                        float(getattr(l, 'done_quantity', 0.0) or 0.0) for l in matched_lines) if matched_lines else 0.0
                    done_current = sum(float(getattr(l, 'done_quantity_current', 0.0) or 0.0) for l in
                                       matched_lines) if matched_lines else 0.0
                    total_done = sum(float(getattr(l, 'total_done_quantity', 0.0) or 0.0) for l in
                                     matched_lines) if matched_lines else 0.0
                    price_unit_conv = matched_lines[0].price_unit_convention if matched_lines and hasattr(
                        matched_lines[0], 'price_unit_convention') else task_unit_price
                    supply_amount = supply_qty * (price_unit_sale or 0.0)
                    done_amount = total_done * (price_unit_conv or 0.0)

                    lot_subtotal += done_amount

                    # write the task row
                    row_vals = [
                        task_no,
                        task_name,
                        float(supply_qty),
                        float(price_unit_sale or 0.0),
                        float(done_prev),
                        float(done_current),
                        float(total_done),
                        float(price_unit_conv or 0.0),
                        float(supply_amount),
                        float(done_amount),
                    ]
                    for c_idx, cell in enumerate(row_vals):
                        if isinstance(cell, (int, float)):
                            worksheet.write_number(current_row, c_idx, cell, money_format)
                        else:
                            worksheet.write(current_row, c_idx, cell or '', normal_format)
                    current_row += 1

                # Write subtotal for the lot
                worksheet.write(current_row, 7, "Sous-total lot", lot_header_format)
                worksheet.write_number(current_row, 9, lot_subtotal, lot_subtotal_format)
                current_row += 2  # space before next lot

        # === Totaux récapitulatifs (écrits après toutes les tables) ===
        worksheet.write_blank(current_row, 0, None)
        current_row += 1

        summary_rows = [
            ('Montant total réalisé en H.T', float(self.total_done_amount or 0.0)),
            ('Montant situation précédente en H.T', float(self.situation_amount_previous or 0.0)),
            ('Différence montant situations', float(self.situation_amount_difference or 0.0)),
            ('Montant situation Neveux', float(self.situation_amount or 0.0)),
            ('TVA', float(self.tva or 0.0)),
            ('Montant TTC', float(self.ttc_amount or 0.0)),
            ('Garantie retenue', float(self.guarantee_retained or 0.0)),
            ('Montant net', float(self.net_amount or 0.0)),
        ]

        for label, value in summary_rows:
            worksheet.write(current_row, 7, label, summary_label_format)
            worksheet.write_number(current_row, 9, value, summary_money_format)
            current_row += 1

        # finalize workbook
        workbook.close()
        output.seek(0)
        file_data = output.read()
        output.close()

        fname = '{} - situation {}.xlsx'.format(project_name, date_str.replace('/', '-'))

        attachment = self.env['ir.attachment'].create({
            'name': fname,
            'type': 'binary',
            'datas': base64.b64encode(file_data),
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }

    def get_lot_tasks_data(self):
        """Retourne les données structurées par lots avec leurs tâches - version alternative"""
        self.ensure_one()

        structured_data = []

        if self.lot_ids:
            for lot in self.lot_ids:
                lot_tasks = []
                lot_total = 0.0

                # Obtenir les tâches associées à ce lot depuis projects.associated
                assoc = self.env['projects.associated'].search([
                    ('project_id', '=', self.project_id.id),
                    ('original_subcontractor_id', '=', self.original_subcontractor_id.id),
                ], limit=1)

                if assoc:
                    # Filtrer les tâches du lot dans projects.associated
                    lot_task_lines = assoc.task_line_ids.filtered(
                        lambda line: line.task_id.lot_id == lot
                    )

                    for task_line in lot_task_lines:
                        # Trouver la ligne correspondante dans situation_sous_traitant_ids
                        situation_line = self.situation_sous_traitant_ids.filtered(
                            lambda line: line.article1 == task_line.task_id.name
                        )

                        if situation_line:
                            line = situation_line[0]  # Prendre la première correspondance
                            task_data = {
                                'no': line.no or task_line.no or '',
                                'name': line.article1 or task_line.task_id.name or '',
                                'supply_quantity': line.supply_quantity or 0.0,
                                'price_unit_sale': line.price_unit_sale or 0.0,
                                'done_quantity_previous': line.done_quantity or 0.0,
                                'done_quantity_current': line.done_quantity_current or 0.0,
                                'total_done_quantity': line.total_done_quantity or 0.0,
                                'price_unit_convention': line.price_unit_convention or task_line.unit_price or 0.0,
                                'supply_amount': line.supply_amount or 0.0,
                                'done_amount': line.done_amount or 0.0,
                            }
                            lot_tasks.append(task_data)
                            lot_total += line.done_amount or 0.0

                if lot_tasks:  # Only add if there are tasks for this lot
                    structured_data.append({
                        'lot_name': lot.name,
                        'lot_id': lot.id,
                        'tasks': lot_tasks,
                        'lot_total': lot_total,
                    })
        else:
            # Si pas de lots spécifiques, regrouper toutes les tâches
            all_tasks = []
            total_amount = 0.0

            for line in self.situation_sous_traitant_ids:
                task_data = {
                    'no': line.no or '',
                    'name': line.article1 or '',
                    'supply_quantity': line.supply_quantity or 0.0,
                    'price_unit_sale': line.price_unit_sale or 0.0,
                    'done_quantity_previous': line.done_quantity or 0.0,
                    'done_quantity_current': line.done_quantity_current or 0.0,
                    'total_done_quantity': line.total_done_quantity or 0.0,
                    'price_unit_convention': line.price_unit_convention or 0.0,
                    'supply_amount': line.supply_amount or 0.0,
                    'done_amount': line.done_amount or 0.0,
                }
                all_tasks.append(task_data)
                total_amount += line.done_amount or 0.0

            structured_data.append({
                'lot_name': 'TOUS LES LOTS',
                'tasks': all_tasks,
                'lot_total': total_amount,
            })

        return structured_data

    def get_situation_summary(self):
        """Retourne le récapitulatif complet de la situation"""
        self.ensure_one()

        # Calcul des totaux à partir des lignes
        total_supply_amount = sum(self.situation_sous_traitant_ids.mapped('supply_amount'))
        total_done_amount = sum(self.situation_sous_traitant_ids.mapped('done_amount'))

        return {
            'project_name': self.project_id.name,
            'date': self.date.strftime("%d/%m/%Y") if self.date else '',
            'subcontractor_name': self.original_subcontractor_id.name if self.original_subcontractor_id else '',
            'total_supply_amount': total_supply_amount,
            'total_done_amount': total_done_amount,
            'situation_amount_previous': self.situation_amount_previous or 0.0,
            'situation_amount_difference': self.situation_amount_difference or 0.0,
            'situation_amount': self.situation_amount or 0.0,
            'tva': self.tva or 0.0,
            'ttc_amount': self.ttc_amount or 0.0,
            'guarantee_retained': self.guarantee_retained or 0.0,
            'net_amount': self.net_amount or 0.0,
        }

    def export_situation_pdf(self):
        """Export the situation as a PDF using model data"""
        self.ensure_one()

        if not self.situation_sous_traitant_ids:
            raise UserError(_("Pas de lignes à exporter pour cette situation."))

        # Récupérer les données structurées
        lot_tasks_data = self.get_lot_tasks_data()
        summary_data = self.get_situation_summary()

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                leftMargin=10 * mm, rightMargin=10 * mm,
                                topMargin=10 * mm, bottomMargin=10 * mm)

        styles = getSampleStyleSheet()

        # Styles personnalisés
        title_style = ParagraphStyle(
            name='Title',
            parent=styles['Heading1'],
            alignment=1,
            fontSize=16,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=15
        )

        subtitle_style = ParagraphStyle(
            name='Subtitle',
            parent=styles['Normal'],
            alignment=1,
            fontSize=11,
            spaceAfter=8
        )

        header_style = ParagraphStyle(
            name='Header',
            parent=styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=10
        )

        lot_title_style = ParagraphStyle(
            name='LotTitle',
            parent=styles['Heading3'],
            fontSize=11,
            textColor=colors.white,
            backColor=colors.HexColor('#3498DB'),
            alignment=0,
            leftIndent=5
        )

        normal_style = ParagraphStyle(
            name='NormalCustom',
            parent=styles['Normal'],
            fontSize=8,
            leading=10
        )

        # STYLE TRÈS RÉDUIT POUR LE CHAMP "N°"
        no_style = ParagraphStyle(
            name='NoStyle',
            parent=styles['Normal'],
            fontSize=5,  # Très réduit
            alignment=1,
            leading=6
        )

        # STYLE RÉDUIT POUR LES NOMBRES
        number_style = ParagraphStyle(
            name='NumberStyle',
            parent=styles['Normal'],
            fontSize=6,  # Réduit
            alignment=1,
            leading=7
        )

        elements = []

        # En-tête
        elements.append(Paragraph("SITUATION DES TRAVAUX", title_style))
        elements.append(Paragraph(f"<b>Projet :</b> {summary_data['project_name']}", subtitle_style))
        elements.append(Paragraph(f"<b>Date de situation :</b> {summary_data['date']}", subtitle_style))
        elements.append(Spacer(1, 10))

        # Sous-traitant
        if summary_data['subcontractor_name']:
            elements.append(Paragraph(f"<b>Sous-traitant :</b> {summary_data['subcontractor_name']}", normal_style))
        elements.append(Spacer(1, 15))

        # Détail par lots
        if lot_tasks_data:
            elements.append(Paragraph("<b>DÉTAIL PAR LOTS</b>", header_style))
            elements.append(Spacer(1, 8))

            for lot_data in lot_tasks_data:
                # Titre du lot
                elements.append(Paragraph(f"<b>Lot:</b> {lot_data['lot_name']}", lot_title_style))
                elements.append(Spacer(1, 4))

                # Tableau des tâches du lot avec TOUTES LES COLONNES
                table_data = [
                    ['N', 'Tâche / Article', 'Q.APP\n(2)', 'P.U.V\n(3)', 'QR mois préc\n(4)',
                     'QR M.E.C\n(5)', 'QRT\n(6)', 'P.U.C\n(7)', 'Mnt appro\n(2)*(3)', 'Mnt.R\n(6)*(7)']
                ]

                for task in lot_data['tasks']:
                    table_data.append([
                        # CHAMP "N" EN TRÈS PETITE TAILLE
                        Paragraph(task['no'] or '', no_style),
                        Paragraph(task['name'] or '', normal_style),
                        # UTILISATION DU NUMBER_STYLE POUR LES NOMBRES
                        Paragraph(self._format_number(task['supply_quantity']), number_style),
                        Paragraph(self._format_number(task['price_unit_sale'], decimals=2), number_style),
                        Paragraph(self._format_number(task['done_quantity_previous']), number_style),
                        Paragraph(self._format_number(task['done_quantity_current']), number_style),
                        Paragraph(self._format_number(task['total_done_quantity']), number_style),
                        Paragraph(self._format_number(task['price_unit_convention'], decimals=2), number_style),
                        Paragraph(self._format_number(task['supply_amount'], decimals=2), number_style),
                        Paragraph(self._format_number(task['done_amount'], decimals=2), number_style)
                    ])

                # Calcul des totaux pour ce lot
                lot_supply_total = sum(task['supply_amount'] for task in lot_data['tasks'])
                lot_done_total = lot_data['lot_total']

                # Sous-total du lot
                table_data.append([
                    '',
                    Paragraph('<b>Sous-total lot</b>', normal_style),
                    '', '', '', '', '', '',
                    Paragraph("<b>{}</b>".format(self._format_number(lot_supply_total, decimals=2)), number_style),
                    Paragraph("<b>{}</b>".format(self._format_number(lot_done_total, decimals=2)), number_style)
                ])

                # Créer le tableau avec les colonnes réduites pour tenir sur la page
                col_widths = [
                    10 * mm,  # N (très réduit - était 12mm)
                    42 * mm,  # Tâche / Article (augmenté pour compenser)
                    16 * mm,  # Q.APP (2) (réduit - était 18mm)
                    16 * mm,  # P.U.V (3) (réduit - était 18mm)
                    16 * mm,  # QR mois préc (4) (réduit - était 18mm)
                    16 * mm,  # QR M.E.C (5) (réduit - était 18mm)
                    16 * mm,  # QRT (6) (réduit - était 18mm)
                    16 * mm,  # P.U.C (7) (réduit - était 18mm)
                    20 * mm,  # Mnt appro (2)*(3) (réduit - était 22mm)
                    20 * mm  # Mnt.R (6)*(7) (réduit - était 22mm)
                ]

                table = Table(table_data, colWidths=col_widths, repeatRows=1)
                table.setStyle(TableStyle([
                    # En-tête du tableau
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495E')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 5),  # Taille réduite pour l'en-tête (était 6)
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),

                    # Bordures
                    ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

                    # Alignement spécifique
                    ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Colonne N centrée
                    ('ALIGN', (1, 1), (1, -1), 'LEFT'),  # Colonne description alignée à gauche
                    ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),  # Colonnes numériques alignées à droite

                    # Style spécifique pour les colonnes numériques
                    ('FONTSIZE', (0, 1), (0, -2), 5),  # Colonne N en taille 5
                    ('FONTSIZE', (2, 1), (2, -2), 6),  # Colonnes numériques en taille 6
                    ('FONTSIZE', (3, 1), (3, -2), 6),
                    ('FONTSIZE', (4, 1), (4, -2), 6),
                    ('FONTSIZE', (5, 1), (5, -2), 6),
                    ('FONTSIZE', (6, 1), (6, -2), 6),
                    ('FONTSIZE', (7, 1), (7, -2), 6),
                    ('FONTSIZE', (8, 1), (8, -2), 6),
                    ('FONTSIZE', (9, 1), (9, -2), 6),

                    # Style de la ligne de sous-total
                    ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#ECF0F1')),
                    ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, -1), (-1, -1), 6),  # Taille pour les totaux (était 7)

                    # Padding réduit au minimum
                    ('LEFTPADDING', (0, 0), (-1, -1), 1),  # Réduit (était 2)
                    ('RIGHTPADDING', (0, 0), (-1, -1), 1),  # Réduit (était 2)
                    ('TOPPADDING', (0, 0), (-1, -1), 0),  # Réduit à 0
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 0),  # Réduit à 0
                ]))

                elements.append(table)
                elements.append(Spacer(1, 8))  # Espacement réduit

            # Récapitulatif avec nombres formatés
            elements.append(Paragraph("<b>RÉCAPITULATIF</b>", header_style))
            elements.append(Spacer(1, 6))

            summary_table_data = [
                ['Montant total approvisionnement',
                 self._format_number(summary_data['total_supply_amount'], decimals=2)],
                ['Montant total réalisé', self._format_number(summary_data['total_done_amount'], decimals=2)],
                ['Montant situation précédente',
                 self._format_number(summary_data['situation_amount_previous'], decimals=2)],
                ['Différence montant situations',
                 self._format_number(summary_data['situation_amount_difference'], decimals=2)],
                ['', ''],
                ['Montant situation', self._format_number(summary_data['situation_amount'], decimals=2)],
                ['TVA', self._format_number(summary_data['tva'], decimals=2)],
                ['Montant TTC', self._format_number(summary_data['ttc_amount'], decimals=2)],
                ['Garantie retenue', self._format_number(summary_data['guarantee_retained'], decimals=2)],
                ['Montant net', self._format_number(summary_data['net_amount'], decimals=2)],
            ]

            summary_table = Table(summary_table_data, colWidths=[75 * mm, 35 * mm])
            summary_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (0, -1), 9),
                ('FONTSIZE', (1, 0), (1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#BDC3C7')),
                ('BACKGROUND', (0, 5), (-1, -1), colors.HexColor('#F8F9FA')),
                ('FONTNAME', (0, 5), (-1, -1), 'Helvetica-Bold'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))

            elements.append(summary_table)

        else:
            # Si pas de lots, afficher toutes les tâches dans un seul tableau
            elements.append(Paragraph("<b>TOUTES LES TÂCHES</b>", header_style))
            elements.append(Spacer(1, 6))

            # Tableau avec toutes les colonnes
            table_data = [
                ['N', 'Tâche / Article', 'Q.APP\n(2)', 'P.U.V\n(3)', 'QR mois préc\n(4)',
                 'QR M.E.C\n(5)', 'QRT\n(6)', 'P.U.C\n(7)', 'Mnt appro\n(2)*(3)', 'Mnt.R\n(6)*(7)']
            ]

            total_supply_amount = 0
            total_done_amount = 0

            for line in self.situation_sous_traitant_ids:
                table_data.append([
                    # CHAMP "N" EN TRÈS PETITE TAILLE
                    Paragraph(line.no or '', no_style),
                    Paragraph(line.article1 or '', normal_style),
                    Paragraph(self._format_number(line.supply_quantity), number_style),
                    Paragraph(self._format_number(line.price_unit_sale, decimals=2), number_style),
                    Paragraph(self._format_number(line.done_quantity), number_style),
                    Paragraph(self._format_number(line.done_quantity_current), number_style),
                    Paragraph(self._format_number(line.total_done_quantity), number_style),
                    Paragraph(self._format_number(line.price_unit_convention, decimals=2), number_style),
                    Paragraph(self._format_number(line.supply_amount, decimals=2), number_style),
                    Paragraph(self._format_number(line.done_amount, decimals=2), number_style)
                ])
                total_supply_amount += line.supply_amount
                total_done_amount += line.done_amount

            # Ligne de total
            table_data.append([
                '',
                Paragraph('<b>TOTAL</b>', normal_style),
                '', '', '', '', '', '',
                Paragraph("<b>{}</b>".format(self._format_number(total_supply_amount, decimals=2)), number_style),
                Paragraph("<b>{}</b>".format(self._format_number(total_done_amount, decimals=2)), number_style)
            ])

            # Colonnes ajustées avec largeurs réduites
            col_widths = [10 * mm, 45 * mm, 16 * mm, 16 * mm, 16 * mm, 16 * mm, 16 * mm, 16 * mm, 20 * mm, 20 * mm]
            table = Table(table_data, colWidths=col_widths, repeatRows=1)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495E')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 5),  # En-tête en taille 5 (était 6)
                ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 1), (0, -1), 'CENTER'),
                ('ALIGN', (1, 1), (1, -1), 'LEFT'),
                ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
                # Style spécifique pour les colonnes
                ('FONTSIZE', (0, 1), (0, -2), 5),  # Colonne N en taille 5
                ('FONTSIZE', (2, 1), (9, -2), 6),  # Toutes les colonnes numériques en taille 6
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#ECF0F1')),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, -1), (-1, -1), 6),  # Sous-total en taille 6
                ('LEFTPADDING', (0, 0), (-1, -1), 1),
                ('RIGHTPADDING', (0, 0), (-1, -1), 1),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ]))

            elements.append(table)

        # Construction du PDF
        doc.build(elements)

        buffer.seek(0)
        pdf_data = buffer.read()
        buffer.close()

        fname = '{} - situation {}.pdf'.format(
            summary_data['project_name'],
            summary_data['date'].replace('/', '-')
        )

        attachment = self.env['ir.attachment'].create({
            'name': fname,
            'type': 'binary',
            'datas': base64.b64encode(pdf_data),
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/pdf',
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }

    def _format_number(self, value, decimals=0):
        """Formatte un nombre avec séparateurs de milliers et décimales optionnelles"""
        if value is None:
            value = 0.0

        try:
            value = float(value)
            if decimals == 0:
                # Pour les quantités entières
                if value == int(value):
                    return "{:,.0f}".format(value).replace(",", " ")
                else:
                    return "{:,.2f}".format(value).replace(",", " ").replace(".", ",")
            else:
                # Pour les montants avec décimales
                formatted = "{:,.2f}".format(value)
                return formatted.replace(",", " ").replace(".", ",")
        except (ValueError, TypeError):
            return "0" if decimals == 0 else "0,00"