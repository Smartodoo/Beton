import base64
from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import xlsxwriter
import io
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
import base64
import io
from datetime import datetime





class ProjectsAssociated(models.Model):
    _name = 'projects.associated'
    _description = 'Projects Associated'

    project_id = fields.Many2one('custom.project', string="Project")
    client_id = fields.Many2one(related='project_id.client_id', string="Client", store=True)
    state = fields.Selection(related='project_id.state', string="State", store=True)
    task_line_ids = fields.One2many('partner.task.line', 'project_id', string="Cahier de charges")
    tax_totale = fields.Float("Total", compute="_compute_tax_totale", store=True)
    total_price = fields.Float(string="Total HT", compute="_compute_total_price", store=True)
    total = fields.Float("Total TTC", compute="_compute_total_price", store=True)
    currency_id = fields.Many2one("res.currency", string="Devise", default=lambda self: self.env.company.currency_id)
    original_subcontractor_id = fields.Many2one('res.partner', string="Sous-traitant d'origine",
                                                domain="[('contact_type','=','SUBCONTRACTOR')]")
    tax_ids = fields.Many2many(
        'account.tax',
        string="Taxes",
        default=lambda self: self.env['account.tax'].search([('amount', '=', 19.0)], limit=1),
        readonly=True
    )
    # Added Many2one field for custom.task.lots with domain to filter by current project
    lots_id = fields.Many2many('custom.task.lots', string="Lot",
                              help="Lot associé aux tâches du projet",
                              domain="[('project_id', '=', project_id)]")

    @api.depends('tax_ids', 'total_price')
    def _compute_tax_total(self):
        total_tax = 0.0
        for rec in self:
            for tax in rec.tax_ids:
                total_tax += (rec.total_price * tax.amount) / 100
        self.tax_totale = total_tax

    @api.depends('task_line_ids.total_price')
    def _compute_total_price(self):
        for rec in self:
            rec.total_price = sum(task.total_price for task in rec.task_line_ids)
            rec.total = rec.total_price + rec.tax_totale

    @api.onchange('lots_id')
    def _onchange_lots_id(self):
        for rec in self:
            if not rec.lots_id:
                rec.task_line_ids = [(5, 0, 0)]
                continue

            rec.task_line_ids = [(5, 0, 0)]
            task_lines = []
            seen = set()

            def walk(task, level=0):
                if not task or task.id in seen:
                    return
                seen.add(task.id)

                task_lines.append((0, 0, {
                    'no': task.no,
                    'task_id': task.id,
                    'description': task.name,
                    'unit': task.unit if task.unit else False,
                    'quantity': 0.0,
                    'unit_price': task.unit_price or 0.0,
                }))

                # تحقق من وجود الحقل 'sequence' بطريقة آمنة
                if 'sequence' in task.child_ids._fields:
                    children = task.child_ids.sorted('sequence')
                else:
                    children = task.child_ids

                for ch in children:
                    walk(ch, level + 1)

            # Get all tasks from all selected lots
            all_tasks = rec.lots_id.mapped('task_ids')
            top_tasks = all_tasks.filtered(lambda t: not t.parent_id)

            # تحقق من وجود الحقل 'sequence' على مستوى الـ recordset
            if 'sequence' in top_tasks._fields:
                top_tasks = top_tasks.sorted('sequence')

            for t in top_tasks:
                walk(t, level=0)

            rec.task_line_ids = task_lines

    @api.onchange('task_line_ids')
    def _check_quantity(self):
        for rec in self:
            seen_tasks = set()  # pour stocker les taches déja séléctionnés
            for task_line in rec.task_line_ids:
                # 1) Vérifier si la tâche est déjà sélectionnée
                if task_line.task_id.id in seen_tasks:
                    raise UserError(
                        "La tâche est sélectionnée plusieurs fois. Vous ne pouvez pas ajouter la même tâche deux fois"
                    )
                seen_tasks.add(task_line.task_id.id)

                # Chercher toutes les lignes de tâches qui ont la même tâche
                existing_task_lines = self.env['partner.task.line'].search([
                    ('task_id', '=', task_line.task_id.id)
                ])
                quantity_task = sum(existing_task_lines.mapped('quantity'))

                print("Task:", task_line.task_id.name, "Total Quantity:", quantity_task)

                quantity_restante = task_line.task_id.quantity - quantity_task

                print("Quantity restante:", quantity_restante, "Selected Quantity:", task_line.quantity)

                if task_line.quantity > quantity_restante:
                    raise UserError(
                        "La quantité sélectionnée est supérieure à la quantité restante :  %s" % quantity_restante
                    )

    def open_situation(self):
        self.ensure_one()
        action = self.env.ref('custom_project.action_open_view_situation').sudo().read()[0]
        # outright replace context with a real dict
        action['context'] = {
            'default_project_id': self.project_id.id,
            'default_original_subcontractor_id': self.original_subcontractor_id.id,
        }
        return action

    def get_convention_lot_tasks_data(self):
        """Retourne les données structurées par lots avec leurs tâches pour la convention"""
        self.ensure_one()

        structured_data = []

        if self.lots_id:
            for lot in self.lots_id:
                # Récupérer les tâches du lot
                lot_tasks = self.task_line_ids.filtered(
                    lambda line: line.task_id.lot_id == lot
                )

                if not lot_tasks:
                    continue

                tasks_data = []
                lot_total = 0.0

                for line in lot_tasks:
                    task_data = {
                        'no': line.no or '',
                        'description': line.description or line.task_id.name or '',
                        'quantity': line.quantity or 0.0,
                        'unit': line.unit.name if line.unit else '',
                        'unit_price': line.unit_price or 0.0,
                        'total_price': line.total_price or 0.0,
                    }
                    tasks_data.append(task_data)
                    lot_total += line.total_price or 0.0

                structured_data.append({
                    'lot_name': lot.name,
                    'tasks': tasks_data,
                    'lot_total': lot_total,
                })
        else:
            # Si pas de lots spécifiques, regrouper toutes les tâches
            all_tasks = []
            total_amount = 0.0

            for line in self.task_line_ids:
                task_data = {
                    'no': line.no or '',
                    'description': line.description or line.task_id.name or '',
                    'quantity': line.quantity or 0.0,
                    'unit': line.unit.name if line.unit else '',
                    'unit_price': line.unit_price or 0.0,
                    'total_price': line.total_price or 0.0,
                }
                all_tasks.append(task_data)
                total_amount += line.total_price or 0.0

            structured_data.append({
                'lot_name': 'TOUS LES LOTS',
                'tasks': all_tasks,
                'lot_total': total_amount,
            })

        return structured_data

    def get_convention_summary(self):
        """Retourne le récapitulatif complet de la convention"""
        self.ensure_one()

        lot_names = ", ".join(self.lots_id.mapped('name')) if self.lots_id else "Tous les lots"

        return {
            'project_name': self.project_id.name or '',
            'subcontractor_name': self.original_subcontractor_id.name if self.original_subcontractor_id else '',
            'lot_names': lot_names,
            'total_price': self.total_price or 0.0,
            'tax_totale': self.tax_totale or 0.0,
            'total': self.total or 0.0,
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
    # Ajoutez cette méthode dans la classe ProjectsAssociated
    def print_convention_pdf(self):
        """Generate and return PDF report for the convention - similar to situation PDF"""
        self.ensure_one()

        if not self.task_line_ids:
            raise UserError(_("Pas de lignes de tâches à imprimer."))

        # Récupérer les données structurées
        lot_tasks_data = self.get_convention_lot_tasks_data()
        summary_data = self.get_convention_summary()

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

        # STYLE SPÉCIAL POUR LES NOMBRES - TAILLE RÉDUITE
        number_style = ParagraphStyle(
            name='NumberStyle',
            parent=styles['Normal'],
            fontSize=7,
            alignment=1,
            leading=9
        )

        # STYLE ENCORE PLUS PETIT POUR LE CHAMP "N°"
        no_style = ParagraphStyle(
            name='NoStyle',
            parent=styles['Normal'],
            fontSize=6,  # Plus petit que les autres nombres
            alignment=1,
            leading=8
        )

        elements = []

        # En-tête
        elements.append(Paragraph("CONVENTION / CAHIER DE CHARGES", title_style))
        elements.append(Paragraph(f"<b>Projet :</b> {summary_data['project_name']}", subtitle_style))
        elements.append(Paragraph(f"<b>Sous-traitant :</b> {summary_data['subcontractor_name']}", subtitle_style))
        elements.append(Spacer(1, 10))

        # Lots
        if summary_data['lot_names']:
            elements.append(Paragraph(f"<b>Lots :</b> {summary_data['lot_names']}", normal_style))
        elements.append(Spacer(1, 15))

        # Détail par lots
        if lot_tasks_data:
            elements.append(Paragraph("<b>DÉTAIL PAR LOTS</b>", header_style))
            elements.append(Spacer(1, 8))

            for lot_data in lot_tasks_data:
                # Titre du lot
                elements.append(Paragraph(f"<b>Lot:</b> {lot_data['lot_name']}", lot_title_style))
                elements.append(Spacer(1, 4))

                # Tableau des tâches du lot
                table_data = [
                    ['N°', 'Tâche / Description', 'Quantité', 'Unité', 'Prix unitaire', 'Total HT']
                ]

                for task in lot_data['tasks']:
                    table_data.append([
                        # UTILISATION DU NO_STYLE POUR LE CHAMP "N°"
                        Paragraph(task['no'] or '', no_style),
                        Paragraph(task['description'] or '', normal_style),
                        Paragraph(self._format_number(task['quantity']), number_style),
                        Paragraph(task['unit'] or '', no_style),  # Unité aussi en petite taille
                        Paragraph(self._format_number(task['unit_price'], decimals=2), number_style),
                        Paragraph(self._format_number(task['total_price'], decimals=2), number_style)
                    ])

                # Sous-total du lot
                table_data.append([
                    '',
                    Paragraph('<b>Sous-total lot</b>', normal_style),
                    '', '', '',
                    Paragraph("<b>{}</b>".format(self._format_number(lot_data['lot_total'], decimals=2)), number_style)
                ])

                # Créer le tableau avec colonnes ajustées
                col_widths = [
                    20 * mm,  # N° - RÉDUIT
                    68 * mm,  # Tâche / Description - AUGMENTÉ
                    20 * mm,  # Quantité - RÉDUIT
                    20 * mm,  # Unité - RÉDUIT
                    20 * mm,  # Prix unitaire - RÉDUIT
                    20 * mm  # Total HT - RÉDUIT
                ]

                table = Table(table_data, colWidths=col_widths, repeatRows=1)
                table.setStyle(TableStyle([
                    # En-tête du tableau
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495E')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 6),  # En-tête en taille 6
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),

                    # Bordures
                    ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

                    # Alignement spécifique
                    ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Colonne N° centrée
                    ('ALIGN', (1, 1), (1, -1), 'LEFT'),  # Colonne description alignée à gauche
                    ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),  # Colonnes numériques alignées à droite

                    # Style spécifique pour la colonne N° - TAILLE RÉDUITE
                    ('FONTSIZE', (0, 1), (0, -2), 6),  # Colonne N° en taille 6 pour toutes les lignes de données
                    ('FONTSIZE', (3, 1), (3, -2), 6),  # Colonne Unité aussi en taille 6

                    # Style de la ligne de sous-total
                    ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#ECF0F1')),
                    ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, -1), (-1, -1), 7),  # Sous-total en taille 7

                    # Padding réduit
                    ('LEFTPADDING', (0, 0), (-1, -1), 1),  # Réduit à 1
                    ('RIGHTPADDING', (0, 0), (-1, -1), 1),  # Réduit à 1
                    ('TOPPADDING', (0, 0), (-1, -1), 1),  # Réduit à 1
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 1),  # Réduit à 1
                ]))

                elements.append(table)
                elements.append(Spacer(1, 8))  # Espacement réduit

            # Récapitulatif
            elements.append(Paragraph("<b>RÉCAPITULATIF</b>", header_style))
            elements.append(Spacer(1, 6))

            summary_table_data = [
                ['Total HT', self._format_number(summary_data['total_price'], decimals=2)],
                ['Taxes', self._format_number(summary_data['tax_totale'], decimals=2)],
                ['Total TTC', self._format_number(summary_data['total'], decimals=2)],
            ]

            summary_table = Table(summary_table_data, colWidths=[60 * mm, 35 * mm])
            summary_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (0, -1), 9),
                ('FONTSIZE', (1, 0), (1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#BDC3C7')),
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8F9FA')),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
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

            # Tableau avec toutes les tâches
            table_data = [
                ['N°', 'Tâche / Description', 'Quantité', 'Unité', 'Prix unitaire', 'Total HT']
            ]

            total_ht = 0

            for line in self.task_line_ids:
                table_data.append([
                    # UTILISATION DU NO_STYLE POUR LE CHAMP "N°"
                    Paragraph(line.no or '', no_style),
                    Paragraph(line.description or line.task_id.name or '', normal_style),
                    Paragraph(self._format_number(line.quantity), number_style),
                    Paragraph(line.unit.name if line.unit else '', no_style),  # Unité en petite taille
                    Paragraph(self._format_number(line.unit_price, decimals=2), number_style),
                    Paragraph(self._format_number(line.total_price, decimals=2), number_style)
                ])
                total_ht += line.total_price

            # Ligne de total
            table_data.append([
                '',
                Paragraph('<b>TOTAL HT</b>', normal_style),
                '', '', '',
                Paragraph("<b>{}</b>".format(self._format_number(total_ht, decimals=2)), number_style)
            ])

            col_widths = [10 * mm, 62 * mm, 16 * mm, 16 * mm, 20 * mm, 20 * mm]
            table = Table(table_data, colWidths=col_widths, repeatRows=1)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495E')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 6),
                ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 1), (0, -1), 'CENTER'),
                ('ALIGN', (1, 1), (1, -1), 'LEFT'),
                ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
                # Style spécifique pour la colonne N° - TAILLE RÉDUITE
                ('FONTSIZE', (0, 1), (0, -2), 6),  # Colonne N° en taille 6
                ('FONTSIZE', (3, 1), (3, -2), 6),  # Colonne Unité en taille 6
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#ECF0F1')),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, -1), (-1, -1), 7),
                ('LEFTPADDING', (0, 0), (-1, -1), 1),
                ('RIGHTPADDING', (0, 0), (-1, -1), 1),
                ('TOPPADDING', (0, 0), (-1, -1), 1),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
            ]))

            elements.append(table)

            # Récapitulatif même sans lots
            elements.append(Spacer(1, 12))
            elements.append(Paragraph("<b>RÉCAPITULATIF</b>", header_style))
            elements.append(Spacer(1, 6))

            summary_table_data = [
                ['Total HT', self._format_number(self.total_price, decimals=2)],
                ['Taxes', self._format_number(self.tax_totale, decimals=2)],
                ['Total TTC', self._format_number(self.total, decimals=2)],
            ]

            summary_table = Table(summary_table_data, colWidths=[60 * mm, 35 * mm])
            summary_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (0, -1), 9),
                ('FONTSIZE', (1, 0), (1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#BDC3C7')),
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8F9FA')),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ]))

            elements.append(summary_table)

        # Construction du PDF
        doc.build(elements)

        buffer.seek(0)
        pdf_data = buffer.read()
        buffer.close()

        fname = '{} - convention {}.pdf'.format(
            self.project_id.name or 'Convention',
            datetime.now().strftime('%d-%m-%Y')
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
    def _convention_xlsx_rows(self):
        """Return list of rows (list of lists) to write to excel for the convention.
           Grouped by lot with their respective tasks."""
        rows = []
        header = [
            'N° ligne', 'Tâche', 'Description', 'Quantité', 'Unité',
            'Prix unitaire', 'Total HT'
        ]

        # If no lots selected, show all tasks in one table
        if not self.lots_id:
            rows.append(header)
            for line in self.task_line_ids:
                rows.append([
                    line.no or '',
                    line.task_id.name or '',
                    line.description or '',
                    float(line.quantity or 0.0),
                    line.unit if line.unit else '',
                    float(line.unit_price or 0.0),
                    float(line.total_price or 0.0),
                ])
        else:
            # Group tasks by lot
            for lot in self.lots_id:
                # Add lot header
                rows.append(['LOT:', lot.name or ''])
                rows.append(header)

                # Get tasks for this lot
                lot_tasks = self.task_line_ids.filtered(
                    lambda line: line.task_id in lot.task_ids
                )

                # Add tasks for this lot
                lot_total = 0.0
                for line in lot_tasks:
                    rows.append([
                        line.no or '',
                        line.task_id.name or '',
                        line.description or '',
                        float(line.quantity or 0.0),
                        line.unit.name if line.unit else '',
                        float(line.unit_price or 0.0),
                        float(line.total_price or 0.0),
                    ])
                    lot_total += float(line.total_price or 0.0)

                # Add subtotal for this lot
                rows.append(['', '', '', '', '', 'Sous-total LOT', float(lot_total)])

                # Add empty row between lots
                rows.append([])

        # summary rows (these will be written after all lots)
        rows.append([])
        rows.append(['', '', '', '', 'Total HT', '', float(self.total_price or 0.0)])
        rows.append(['', '', '', '', 'Taxes', '', float(self.tax_totale or 0.0)])
        rows.append(['', '', '', '', 'Total TTC', '', float(self.total or 0.0)])
        return rows

    def export_convention_xlsx(self):
        """Generate and trigger download of an XLSX convention for the record.

        Creates an attachment and returns an action that opens the file URL.
        """
        self.ensure_one()

        # basic validation
        if not self.task_line_ids:
            raise UserError(_("Pas de lignes de tâches à exporter."))

        # Build in-memory workbook
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Convention')

        # formats
        title_fmt = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'center',
            'valign': 'vcenter'
        })
        subtitle_fmt = workbook.add_format({
            'italic': True,
            'font_size': 10,
            'align': 'left',
            'valign': 'vcenter'
        })
        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#D9E1F2', 'border': 1})
        lot_header_fmt = workbook.add_format({'bold': True, 'font_size': 12, 'bg_color': '#E6B8B7', 'border': 1})
        num_format = workbook.add_format({'num_format': '#,##0.00', 'border': 1})
        normal_format = workbook.add_format({'border': 1})
        total_fmt = workbook.add_format({'bold': True, 'bg_color': '#FFE699', 'border': 1, 'num_format': '#,##0.00'})
        subtotal_fmt = workbook.add_format({'bold': True, 'bg_color': '#F8CBAD', 'border': 1, 'num_format': '#,##0.00'})

        # Column widths
        worksheet.set_column(0, 0, 10)  # No
        worksheet.set_column(1, 1, 30)  # Task name
        worksheet.set_column(2, 2, 50)  # Description
        worksheet.set_column(3, 6, 15)

        # === Header: title, project, client, lots ===
        title = "CONVENTION / CAHIER DE CHARGES"
        project_name = self.project_id.name or "—"
        client_name = (self.original_subcontractor_id.name if self.original_subcontractor_id else (
            self.project_id.original_subcontractor_id.name if self.project_id and self.project_id.original_subcontractor_id else "—"))

        # Handle multiple lots - join their names with comma
        lot_names = ", ".join(self.lots_id.mapped('name')) if self.lots_id else "Tous les lots"

        # merge across the columns used by the table (A to G -> indices 0..6)
        worksheet.merge_range(0, 0, 0, 6, title, title_fmt)
        worksheet.write(1, 0, "Projet :", subtitle_fmt)
        worksheet.write(1, 1, project_name, subtitle_fmt)
        worksheet.write(2, 0, "Sous-Traitant D'origine :", subtitle_fmt)
        worksheet.write(2, 1, client_name, subtitle_fmt)
        worksheet.write(3, 0, "Lots :", subtitle_fmt)
        worksheet.write(3, 1, lot_names, subtitle_fmt)

        # leave one blank row then start table at row 6 (index 5)
        start_row = 5

        rows = self._convention_xlsx_rows()

        # write rows
        current_row = start_row
        for row in rows:
            if row and row[0] == 'LOT:':  # Lot header row
                worksheet.merge_range(current_row, 0, current_row, 6, row[1] if len(row) > 1 else '', lot_header_fmt)
                current_row += 1
            elif row and row[0] == 'N° ligne':  # Table header row
                for c_idx, cell in enumerate(row):
                    worksheet.write(current_row, c_idx, cell, header_fmt)
                current_row += 1
            elif row and any(row):  # Non-empty row
                # Check if this is a subtotal row (contains 'Sous-total LOT')
                is_subtotal = any(isinstance(item, str) and 'Sous-total LOT' in item for item in row)

                for c_idx, cell in enumerate(row):
                    if isinstance(cell, (int, float)):
                        if is_subtotal:
                            worksheet.write(current_row, c_idx, cell, subtotal_fmt)
                        elif any(isinstance(item, str) and 'total' in item.lower() for item in row if
                                 isinstance(item, str)):
                            worksheet.write(current_row, c_idx, cell, total_fmt)
                        else:
                            worksheet.write_number(current_row, c_idx, cell, num_format)
                    else:
                        if is_subtotal:
                            worksheet.write(current_row, c_idx, cell or '', subtotal_fmt)
                        else:
                            worksheet.write(current_row, c_idx, cell or '', normal_format)
                current_row += 1
            else:  # Empty row
                current_row += 1

        workbook.close()
        output.seek(0)
        file_data = output.read()
        output.close()

        fname = '{} - convention {}.xlsx'.format(self.project_id.name or 'Project',
                                                 datetime.now().strftime('%Y%m%d_%H%M%S'))

        # create or replace attachment
        attachment = self.env['ir.attachment'].create({
            'name': fname,
            'type': 'binary',
            'datas': base64.b64encode(file_data),
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        # return action to download the file
        download_url = '/web/content/%s?download=true' % attachment.id
        return {
            'type': 'ir.actions.act_url',
            'url': download_url,
            'target': 'self',
        }




class PartnerTaskLine(models.Model):
    _name = 'partner.task.line'
    _description = 'Ligne Tâche pour Partenaire'

    no = fields.Char()
    project_id = fields.Many2one('projects.associated', string="Partenaire")
    project = fields.Many2one(related='project_id.project_id', string="Projet", store=True, readonly=True)
    task_id = fields.Many2one('custom.task', string="Tâche", domain="[('project_id', '=', project)]")
    description = fields.Text(string="Description")
    quantity = fields.Float(string="Quantité", default=0.0)  # Default to 0.0
    unit = fields.Many2one(related='task_id.unit', string="Unité")
    unit_price = fields.Float(string="Prix Unitaire")
    total_price = fields.Float(string="Total HT", compute="_compute_total_price", store=True)
    # Added Many2one field related to custom.task lots
    lot_id = fields.Many2one('custom.task.lots', string="Lot", related='task_id.lot_id', store=True)
    # Fixed field definitions - use computed fields instead of related for boolean
    is_child_task = fields.Boolean(string="Sous-tâche", compute='_compute_is_child_task', store=True)
    parent_task_id = fields.Many2one('custom.task', string="Tâche parente", compute='_compute_parent_task', store=True)

    @api.depends('task_id.parent_id')
    def _compute_is_child_task(self):
        for rec in self:
            rec.is_child_task = bool(rec.task_id.parent_id)

    @api.depends('task_id.parent_id')
    def _compute_parent_task(self):
        for rec in self:
            rec.parent_task_id = rec.task_id.parent_id

    @api.depends('quantity', 'unit_price')
    def _compute_total_price(self):
        for rec in self:
            rec.total_price = rec.quantity * rec.unit_price

    # @api.model
    # def create(self, vals):
    #     if vals.get('task_id') and not vals.get('description'):
    #         task = self.env['custom.task'].browse(vals['task_id'])
    #         vals['description'] = task.name
    #     return super(PartnerTaskLine, self).create(vals)
    #
    # def write(self, vals):
    #     if 'task_id' in vals and not vals.get('description'):
    #         # We are going to update the description for records that currently have no description
    #         records_without_description = self.filtered(lambda rec: not rec.description)
    #         if records_without_description:
    #             new_task = self.env['custom.task'].browse(vals['task_id'])
    #             super(PartnerTaskLine, records_without_description).write({
    #                 'description': new_task.name
    #             })
    #     return super(PartnerTaskLine, self).write(vals)

class CustomProjectInherit(models.Model):
    _inherit = 'custom.project'

    nombre_achat = fields.Integer(string=' Achats liés', compute='_compute_nombre_achat')
    nombre_stock_article = fields.Integer(string='Stock', default=0, compute='_compute_nombre_stock_article')

    def open_custom_stock(self):
        return {
            'name': ('Stocks liés au projet: %s') % self.name,
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'custom.stock',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id},
        }

    def _compute_nombre_stock_article(self):
        for rec in self:
            stock_count = self.env['custom.stock'].search_count([('project_id', '=', rec.id)])
            rec.nombre_stock_article = stock_count

    def _compute_nombre_achat(self):
        for project in self:
            project.nombre_achat = self.env['purchase.order'].search_count([('project_id', '=', project.id)])

    def open_related_purchases(self):
        return {
            'name': ('Achats liés au projet: %s') % self.name,
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id},
        }


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # representant = fields.Char(string="Représentant")
    nombre_projets = fields.Integer(string="Conventions", compute="_compute_nombre_projets")
    nombre_situations = fields.Integer(string="Situations", compute="_compute_nombre_situations")
    project_ids = fields.Many2many('custom.project', 'Project')
    vendor_bons_count = fields.Integer(string="Bons Count", compute='_compute_vendor_bons', store=True)
    vendor_bons_ids = fields.One2many('custom.bons', 'vendor_id',
                                      string="Vendor Bons (computed)")  # read-only virtual list

    def _compute_nombre_projets(self):
        for partner in self:
            if partner.contact_type == 'SUBCONTRACTOR':
                partner.nombre_projets = self.env['projects.associated'].search_count([
                    ('original_subcontractor_id', '=', partner.id)
                ])
            else:
                partner.nombre_projets = 0

    def _compute_nombre_situations(self):
        for partner in self:
            if partner.contact_type == 'SUBCONTRACTOR':
                # Compter les situations uniques du modèle "situation"
                partner.nombre_situations = self.env['situation'].search_count([
                    ('original_subcontractor_id', '=', partner.id)
                ])
            else:
                partner.nombre_situations = 0

    is_subcontractor = fields.Boolean(compute="_compute_is_subcontractor")
    # Added Many2one field related to custom.task lots
    # task_lot_id = fields.Many2one('custom.task.lots', string="Lot de tâche",
    #                               help="Lot associé aux tâches personnalisées")
    stock_count = fields.Integer(string="Stocks", compute='_compute_stock_count')

    @api.depends()  # no reliable depends for search_count; kept empty
    def _compute_stock_count(self):
        for partner in self:
            partner.stock_count = self.env['custom.stock'].search_count([
                ('partner_id', '=', partner.id)
            ])

    def action_open_stock(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Stocks',
            'res_model': 'custom.stock',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
        }
    @api.depends('contact_type')
    def _compute_is_subcontractor(self):
        for rec in self:
            rec.is_subcontractor = rec.contact_type == 'SUBCONTRACTOR'
    @api.depends()  # keep depends minimal; we compute via search_count
    def _compute_vendor_bons(self):
        Bons = self.env['custom.bons']
        for partner in self:
            # count bon records where vendor_id == partner.id
            if partner.id:
                count = Bons.search_count([('vendor_id', '=', partner.id)])
                partner.vendor_bons_count = count
                # fill vendor_bons_ids (non-stored); good for quick access but not necessary
                partner.vendor_bons_ids = Bons.search([('vendor_id', '=', partner.id)])
            else:
                partner.vendor_bons_count = 0
                partner.vendor_bons_ids = Bons.browse()

    # Action to open the bons list filtered by this partner
    def action_open_vendor_bons(self):
        """Open Bons filtered by vendor (this partner) and optionally by projects selected."""
        self.ensure_one()
        domain = [('vendor_id', '=', self.id)]
        # add project filter only if partner has project_ids
        if self.project_ids:
            domain.append(('project_id', 'in', self.project_ids.ids))

        # try to use predefined action if exists, otherwise fallback
        try:
            action = self.env.ref('custom_project.action_custom_bons_tree')
            result = action.read()[0]
            result['domain'] = domain
            # pass first project id as default if exists, else False
            result['context'] = {'default_vendor_id': self.id, 'default_project_id': (self.project_ids.ids[0] if self.project_ids else False)}
            return result
        except ValueError:
            # fallback dynamic action
            return {
                'name': _('Bons'),
                'type': 'ir.actions.act_window',
                'res_model': 'custom.bons',
                'view_mode': 'tree,form',
                'domain': domain,
                'context': {'default_vendor_id': self.id, 'default_project_id': (self.project_ids.ids[0] if self.project_ids else False)},
            }




    def action_open_situations(self):
        self.ensure_one()
        domain = []

        # Filtrer par partenaire
        domain.append(('original_subcontractor_id', '=', self.id))

        # Ajouter le filtre par projets si le partenaire a des projets
        if self.project_ids:
            domain.append(('project_id', 'in', self.project_ids.ids))

        # Essayer de récupérer l'action pré-définie (si elle existe)
        try:
            action = self.env.ref('custom_project.action_situation_tree')  # remplace par ton xml_id
            result = action.read()[0]
            result['domain'] = domain
            # Context pour remplir par défaut le partenaire et éventuellement le premier projet
            result['context'] = {
                'default_original_subcontractor_id': self.id,
                'default_project_id': self.project_ids.ids[0] if self.project_ids else False,
            }
            return result
        except ValueError:
            # Fallback si l'action n'existe pas
            return {
                'name': _('Situations'),
                'type': 'ir.actions.act_window',
                'res_model': 'situation',
                'view_mode': 'tree,form',
                'domain': domain,
                'context': {
                    'default_original_subcontractor_id': self.id,
                    'default_project_id': self.project_ids.ids[0] if self.project_ids else False,
                },}