# -*- coding: utf-8 -*-
import base64
import io
import logging
import re
import traceback

from openpyxl import load_workbook
import html as pyhtml
import pandas as pd

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round



# -*- coding: utf-8 -*-
import base64
import io
import logging
import re
import traceback

import pandas as pd
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round

_logger = logging.getLogger(__name__)


class CustomProject(models.Model):
    _name = "custom.project"
    _description = "Projet BTP"

    # Subtotal keywords constant
    SUBTOTAL_KEYWORDS = ['S/TOTAL', 'S-TOTAL', 'S_TOTAL', 'S TOTAL', 'SOUS-TOTAL', 'TOTAL PARTIEL', 'TOTAL GENERAL',
                         'TOTAL LOT', 'SOUS TOTAL']

    name = fields.Char('Nom du Projet', required=True)
    client_id = fields.Many2one('res.partner', string='Contractant', required=True)
    description = fields.Text('Description')
    state = fields.Selection([('draft', 'Brouillon'), ('confirmed', 'Confirmé'),
                              ('done', 'Terminé'), ('cancelled', 'Annulé')],
                             string='État', default='draft')
    task_ids = fields.One2many('custom.task', 'project_id', string='Tâches', readonly=False)
    lots_ids = fields.One2many('custom.task.lots', 'project_id', string='Lots', readonly=False)
    total_price = fields.Float(string='Total HT', compute='_compute_total_price', store=True)
    currency_id = fields.Many2one('res.currency', string='Devise', default=lambda self: self.env.company.currency_id)
    company_id = fields.Many2one('res.company', string='Société', default=lambda self: self.env.company)

    # Primary taxes with explicit relation table
    tax_ids = fields.Many2many(
        'account.tax',
        'custom_project_tax_primary_rel',
        'project_id',
        'tax_id',
        string='Taxes Principales (19%)'
    )

    tax_totale = fields.Float('Totale', compute='_compute_tax_totale', store=True)
    total = fields.Float('Total TTC', compute='_compute_total', store=True)

    # Primary import file
    import_file = fields.Binary('Fichier Excel')
    import_filename = fields.Char('Nom fichier')

    # HTML previews
    table_html = fields.Html(string='Project Table', compute='_compute_table_html', sanitize=False)

    tax_ids_2 = fields.Many2many(
        'account.tax',
        'custom_project_tax_secondary_rel',
        'project_id',
        'tax_id',
        string='Taxes logments (9%)',
        domain="[('type_tax_use', '=', 'sale')]"
    )
    vendor_ids = fields.Many2many('res.partner', string='Vendors', compute='_compute_vendor_count', store=False)
    vendor_count = fields.Integer(string="Fournisseurs", compute='_compute_vendor_count', store=False)
    consumption_count = fields.Integer(
        string="Consommations",
        compute='_compute_consumption_count'
    )




    def _compute_consumption_count(self):
        for project in self:
            project.consumption_count = self.env['cunsomation.stock'].search_count([
                ('project_id', '=', project.id)
            ])

    def action_view_consumptions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Consommations - {self.name}',
            'res_model': 'cunsomation.stock',
            'view_mode': 'tree,form',
            'domain': [('project_id', '=', self.id)],
            'context': {
                'default_project_id': self.id,
                'search_default_project_id': self.id,
            }
        }
    def _compute_vendor_count(self):
        Bons = self.env['custom.bons']
        Partner = self.env['res.partner']
        for rec in self:
            # read_group on custom.bons grouped by vendor_id for this project
            grouped = Bons.read_group([('project_id', '=', rec.id)], ['vendor_id'], ['vendor_id'])
            # grouped is list of dicts, each dict has 'vendor_id': (id, name)
            rec.vendor_count = len(grouped)
            # collect partner ids
            partner_ids = []
            for g in grouped:
                v = g.get('vendor_id')
                if v:
                    # v is like (id, display_name)
                    partner_ids.append(v[0])
            rec.vendor_ids = Partner.browse(partner_ids)

    def action_get_vendor_record(self):
        """Open a partners window showing suppliers that appear in custom.bons for this project."""
        self.ensure_one()
        Bons = self.env['custom.bons']
        # نأخذ الموردين distinct المرتبطين بالمشروع الحالي
        vendor_ids = Bons.search([('project_id', '=', self.id)]).mapped('vendor_id.id')
        if not vendor_ids:
            vendor_ids = self.env['res.partner'].search([
                ('contact_type', '=', 'SUPPLIER'),
                ('is_company', '=', True)
            ]).ids
        return {
            'name': _('Fournisseurs'),
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_mode': 'tree,form',
            'domain': [
                ('contact_type', '=', 'SUPPLIER'),
                ('is_company', '=', True),
                ('id', 'in', vendor_ids)
            ],
            'context': {'default_contact_type': 'SUPPLIER', 'default_is_company': True, 'default_project_ids': [(4, self.id)]},
        }

    # ---------- Helpers ----------
    def _clean_cell(self, v):
        if v is None:
            return None
        try:
            if isinstance(v, float) and pd.isna(v):
                return None
        except Exception:
            pass
        s = str(v).strip()
        if s == '':
            return None
        s = s.replace('\xa0', ' ')
        s = re.sub(r'\s+', ' ', s)
        return s

    def _is_numeric_like(self, v):
        if v is None:
            return False
        s = str(v).strip()
        if s == '':
            return False
        s2 = s.replace('\xa0', '').replace(' ', '')
        return bool(re.match(r'^[\+\-]?\d[\d\.,]*$', s2))

    def _parse_number(self, value):
        try:
            if value is None:
                return 0.0
            if isinstance(value, (int, float)):
                return float(value)
            s = str(value).strip()
            if s == '':
                return 0.0
            s = s.replace('\xa0', '').replace(' ', '')
            if ',' in s and '.' in s:
                if s.rfind(',') > s.rfind('.'):
                    s = s.replace('.', '').replace(',', '.')
                else:
                    s = s.replace(',', '')
            elif ',' in s and '.' not in s:
                s = s.replace(',', '.')
            s = re.sub(r'[^\d\.\-]', '', s)
            return float(s) if s not in ('', '.', '-') else 0.0
        except Exception:
            return 0.0

    def _format_number(self, value, decimals=3):
        try:
            if value is None:
                fmt = "{:,.{prec}f}".format(0.0, prec=decimals)
                return fmt.replace(",", " ").replace(".", ",")
            fmt = "{:,.{prec}f}".format(float(value), prec=decimals)
            return fmt.replace(",", " ").replace(".", ",")
        except Exception:
            return str(value or "")

    def _split_multiline_cell(self, sraw):
        if not sraw:
            return []
        lines = [l.strip() for l in re.split(r'[\r\n]+', str(sraw)) if l and l.strip()]
        return lines

    def _parse_subline_tokens(self, line):
        desc = ''
        unit_text = ''
        qty = price = amount = 0.0
        tokens = re.split(r'\t|\s{2,}|\s+', line)
        tokens = [t for t in tokens if t is not None and str(t).strip() != '']
        numeric_idx = [i for i, t in enumerate(tokens) if self._is_numeric_like(t)]
        if numeric_idx:
            amount_idx = numeric_idx[-1]
            price_idx = numeric_idx[-2] if len(numeric_idx) >= 2 else None
            qty_idx = numeric_idx[-3] if len(numeric_idx) >= 3 else None
            if qty_idx is not None:
                qty = self._parse_number(tokens[qty_idx])
            if price_idx is not None:
                price = self._parse_number(tokens[price_idx])
            if amount_idx is not None:
                amount = self._parse_number(tokens[amount_idx])
            if qty_idx is not None and qty_idx - 1 >= 0:
                cand = tokens[qty_idx - 1]
                if cand and not self._is_numeric_like(cand) and len(cand) <= 8:
                    unit_text = cand
            if numeric_idx:
                first_num = numeric_idx[0]
                if first_num > 0:
                    desc = ' '.join(tokens[:first_num])
        else:
            desc = line
        return desc.strip(), (unit_text or '').strip(), qty, price, amount

    def _contains_subtotal_keyword(self, row):
        """
        Check if any cell in the row contains subtotal keywords
        """
        for cell in row:
            if cell and isinstance(cell, str):
                cell_upper = cell.upper()
                for keyword in self.SUBTOTAL_KEYWORDS:
                    if keyword.upper() in cell_upper:
                        return True
        return False

    def _looks_like_subtotal(self, text, row_text_upper=None):
        """
        Enhanced subtotal detection with more patterns
        """
        if not text and not row_text_upper:
            return False

        # Normalize text for comparison
        t = (str(text) if text else "").upper().strip()
        ru = (row_text_upper or "").upper().strip()

        # Check for exact subtotal keywords
        for keyword in self.SUBTOTAL_KEYWORDS:
            if keyword.upper() in t or keyword.upper() in ru:
                return True

        # Extended patterns for subtotal detection
        patterns = [
            r'\bS[\s_/\\-]*TOTAL\b',
            r'\bSOUS[\s_/\\-]*TOTAL\b',
            r'\bTOTAL\s+PARTIEL\b',
            r'\bTOTAL\s+LOT\b',
            r'\bTOTAL\s+[A-Z]+\b',
            r'\bS\.TOTAL\b',
            r'\bSTOTAL\b',
            r'\bTOTAL\s+S/\b',
            r'\bTOTAL\s+GENERAL\b',
            r'\bTOTAL\s+DU\b',
            r'\bTOTAL\s+DES\b'
        ]

        # Check patterns in both text and row_text_upper
        for pattern in patterns:
            if re.search(pattern, t) or re.search(pattern, ru):
                return True

        # Additional direct matches
        direct_matches = ['S/TOTAL', 'S-TOTAL', 'S_TOTAL', 'S TOTAL', 'SOUS-TOTAL', 'TOTAL PARTIEL', 'TOTAL GENERAL',
                          'TOTAL LOT', 'SOUS TOTAL']
        for match in direct_matches:
            if match in t or match in ru:
                return True

        # Match lines starting with S/ followed by text (common in French documents)
        if re.match(r'^S\/\s*\w+', t) or re.match(r'^S\s+\w+', t):
            return True

        # Match lines that are mostly "TOTAL" with some prefixes
        if t.startswith('TOTAL') and len(t) < 20:
            return True

        return False

    def _ensure_tva_19(self):
        """Ensure 19% tax exists"""
        company = self.env.company
        tax = self.env['account.tax'].search([
            ('company_id', '=', company.id),
            ('amount', '=', 19.0),
            ('type_tax_use', '=', 'sale')
        ], limit=1)
        if not tax:
            tax = self.env['account.tax'].create({
                'name': 'TVA 19%',
                'amount': 19.0,
                'amount_type': 'percent',
                'type_tax_use': 'sale',
                'company_id': company.id,
            })
        return tax

    def _ensure_tva_9(self):
        """Ensure 9% tax exists"""
        company = self.env.company
        tax = self.env['account.tax'].search([
            ('company_id', '=', company.id),
            ('amount', '=', 9.0),
            ('type_tax_use', '=', 'sale')
        ], limit=1)
        if not tax:
            tax = self.env['account.tax'].create({
                'name': 'TVA 9%',
                'amount': 9.0,
                'amount_type': 'percent',
                'type_tax_use': 'sale',
                'company_id': company.id,
            })
        return tax

    def _process_sheet_table_only(self, xls, sheet_name, suffix='', source='primary'):
        try:
            df = pd.read_excel(xls, sheet_name=sheet_name, header=None, dtype=object, engine="openpyxl")
        except Exception:
            df = pd.read_excel(xls, sheet_name=sheet_name, header=None, dtype=object)

        clean_matrix = []
        for idx, row in df.iterrows():
            clean_matrix.append([self._clean_cell(c) for c in row.tolist()])

        # Find header row
        header_row_idx = None
        main_headers = {'DESGNATION', 'DESIGNATION', 'QUANTITES', 'QUANTITE', 'PRIX', 'MONTANT', 'U', 'UNITE'}
        for i, row in enumerate(clean_matrix[:160]):
            row_text = ' '.join([str(c).upper() for c in row if c])
            if not row_text:
                continue
            count = sum(1 for k in main_headers if k in row_text)
            if count >= 2:
                header_row_idx = i
                break
        if header_row_idx is None:
            _logger.info("No table header found in sheet %s - skipping", sheet_name)
            return

        start_idx = header_row_idx + 1
        sequence = 10
        current_lot = None
        current_section = None
        current_parent_task = None
        task_code_map = {}
        _suffix = suffix or ''
        _source = source or 'primary'

        for ri in range(start_idx, len(clean_matrix)):
            try:
                row = clean_matrix[ri]

                # ========== EARLY SUBTOTAL KEYWORD DETECTION ==========
                # Skip entire row if any cell contains subtotal keywords
                if self._contains_subtotal_keyword(row):
                    _logger.info("🚫 SKIPPING SUBTOTAL ROW: %s", [str(c) for c in row if c])
                    continue
                # ========== END EARLY SUBTOTAL KEYWORD DETECTION ==========

                # DEBUG: Print all non-empty rows
                if any(cell for cell in row if cell and not self._is_numeric_like(cell)):
                    print(f"📖 ROW {ri}: {[str(c)[:50] if c else '' for c in row]}")

                if all(c is None for c in row):
                    continue
                row_text_upper = ' '.join([str(c).upper() for c in row if c]).strip()
                if row_text_upper and re.match(r'^[\d\.,\s\-\+]+$', row_text_upper):
                    # skip numeric-only footers/lines
                    continue

                first_non = next((c for c in row if c), None)
                if first_non:
                    first_up = str(first_non).upper()
                    if any(kw in first_up for kw in ['PROJET', 'ATTACH', 'ATTACHEMENT', 'TVA', 'TOTAL EN']):
                        continue

                # ========== ENHANCED SUBTOTAL DETECTION AND HANDLING ==========
                # Check if this is a subtotal line using multiple strategies
                is_subtotal_line = False
                subtotal_keywords = ['S/TOTAL', 'SOUS-TOTAL', 'SOUS TOTAL', 'TOTAL PARTIEL', 'TOTAL LOT', 'TOTAL S/']

                # Check if this is a subtotal line using multiple strategies
                if row_text_upper:
                    # Strategy 1: Use the existing pattern matching
                    is_subtotal_line = self._looks_like_subtotal(row_text_upper)

                    # Strategy 2: Direct keyword matching in row text
                    if not is_subtotal_line:
                        for keyword in subtotal_keywords:
                            if keyword in row_text_upper:
                                is_subtotal_line = True
                                break

                    # Strategy 3: Check first cell for subtotal patterns
                    if not is_subtotal_line and first_non:
                        first_cell_upper = str(first_non).upper()
                        for keyword in subtotal_keywords:
                            if keyword in first_cell_upper:
                                is_subtotal_line = True
                                break
                        # Also check for patterns like "S/ TOTAL", "S / TOTAL", etc.
                        if re.match(r'^S[/\s]*TOTAL', first_cell_upper):
                            is_subtotal_line = True

                if is_subtotal_line:
                    _logger.info("🔍 SUBTOTAL DETECTED: %s", row_text_upper)
                    # Skip creating any task for subtotal lines
                    continue
                # ========== END SUBTOTAL HANDLING ==========

                # Detect LOT by numeric-first-cell + text after (e.g. "1 Designation...")
                non_empty = [c for c in row if c]
                if non_empty and isinstance(non_empty[0], str):
                    first_val = non_empty[0].strip()
                    if re.match(r'^\d+$', first_val):
                        others_numeric = any(self._is_numeric_like(c) for c in row[1:])
                        has_text_after = any(c and (not self._is_numeric_like(c)) for c in row[1:])
                        if (not others_numeric) and has_text_after:
                            lot_name = " ".join([str(c) for c in row if c])
                            try:
                                with self.env.cr.savepoint():
                                    current_lot = self.env['custom.task.lots'].create({
                                        'name': (lot_name or '') + _suffix,
                                        'project_id': self.id,
                                        'sequence': sequence,
                                        'company_id': self.env.company.id,
                                        'import_source': _source,
                                    })
                            except Exception as e:
                                _logger.exception("Failed create lot '%s' (sheet %s row %s): %s", lot_name, sheet_name,
                                                  ri, e)
                                current_lot = None
                            sequence += 10
                            current_section = None
                            current_parent_task = None
                            task_code_map = {}
                            continue

                # Explicit LOT lines
                if non_empty and isinstance(non_empty[0], str) and (
                        any(k in non_empty[0].upper() for k in ('LOT N°', 'LOT N', 'LOT:')) or non_empty[
                    0].strip().upper().startswith('LOT ')):
                    lot_name = non_empty[0]
                    try:
                        with self.env.cr.savepoint():
                            current_lot = self.env['custom.task.lots'].create({
                                'name': (lot_name or '') + _suffix,
                                'project_id': self.id,
                                'sequence': sequence,
                                'company_id': self.env.company.id,
                                'import_source': _source,
                            })
                    except Exception as e:
                        _logger.exception("Failed create lot '%s' (sheet %s row %s): %s", lot_name, sheet_name, ri, e)
                        current_lot = None
                    sequence += 10
                    current_section = None
                    current_parent_task = None
                    task_code_map = {}
                    continue

                # Title detection: lines starting with 'a/' etc.
                first_non_index = None
                first_non_cell = None
                for i_c, c in enumerate(row):
                    if c:
                        first_non_index = i_c
                        first_non_cell = c
                        break
                title_match = False
                if first_non_cell and isinstance(first_non_cell, str) and re.match(r'^[A-Za-z]\/',
                                                                                   first_non_cell.strip()):
                    title_match = True

                if title_match:
                    title_parts = []
                    txt = re.sub(r'^[A-Za-z]\/\s*', '', str(first_non_cell).strip())
                    title_parts.append(txt)
                    for j in range(first_non_index + 1, len(row)):
                        if row[j] and not self._is_numeric_like(row[j]):
                            title_parts.append(str(row[j]))
                    full_title = " ".join([p for p in title_parts if p]).strip()
                    if not full_title:
                        full_title = str(first_non_cell).strip()

                    title_vals = {
                        'no': '',
                        'name': full_title,
                        'unit_name': '',
                        'quantity': 0.0,
                        'unit_price': 0.0,
                        'is_title': True,
                        'is_category': True,
                        'project_id': self.id,
                        'sequence': sequence,
                        'company_id': self.env.company.id,
                        'import_source': _source,
                    }
                    if current_lot:
                        title_vals['lot_id'] = current_lot.id
                    try:
                        with self.env.cr.savepoint():
                            self.env['custom.task'].create(title_vals)
                    except Exception as e:
                        _logger.exception("Failed create title line (sheet %s row %s): %s", sheet_name, ri, e)
                    sequence += 5
                    continue

                # Find numeric code like 6.08, 1.2.3 ...
                code_idx = None
                code_val = None
                for i, c in enumerate(row):
                    if c and re.match(r'^\d+(\.\d+)*$', str(c).strip()):
                        code_idx = i
                        code_val = str(c).strip()
                        break

                if code_val:
                    # Additional safeguard: Check if this is actually a subtotal line disguised as a code
                    row_desc = ' '.join([str(c) for c in row if c and not self._is_numeric_like(c)]).upper()
                    if self._looks_like_subtotal(row_desc):
                        _logger.info("🚫 Skipping subtotal line disguised as code: %s", row_desc)
                        continue

                    dot_count = code_val.count('.')
                    is_section = (dot_count == 1)
                    is_task = (dot_count == 2)
                    is_subtask = (dot_count >= 3)

                    raw_cell = df.iloc[ri, code_idx] if code_idx is not None else None
                    desc = ''
                    if raw_cell:
                        sraw = str(raw_cell).strip()
                        parts = re.split(r'\t|\n{1,}|\s{2,}', sraw)
                        if len(parts) > 1:
                            desc = " ".join(parts[1:]).strip()
                    if not desc:
                        for j in range(code_idx + 1, min(len(row), code_idx + 6)):
                            if row[j] and not self._is_numeric_like(row[j]):
                                desc = (desc + ' ' + row[j]).strip()

                    # Robust fallback for empty desc
                    if not desc or len(desc.strip()) <= 2:
                        text_cells = []
                        for j in range(code_idx + 1, min(len(row), code_idx + 8)):
                            if row[j] and not self._is_numeric_like(row[j]):
                                text_cells.append(str(row[j]).strip())
                        if text_cells:
                            desc = ' '.join(text_cells).strip()
                        else:
                            if raw_cell:
                                desc = re.sub(r'^\d+(\.\d+)*\s*', '', str(raw_cell)).strip()

                    # Handle multiline parent with explicit sub-lines inside same cell
                    multiline_lines = self._split_multiline_cell(raw_cell) if raw_cell else []
                    handled_multiline = False
                    if len(multiline_lines) > 1:
                        has_numeric_in_sublines = any(
                            any(self._is_numeric_like(t) for t in re.split(r'\t|\s{2,}|\s+', ln))
                            for ln in multiline_lines[1:]
                        )
                        if has_numeric_in_sublines:
                            parent_no = f"{code_val}.01"
                            parent_name = multiline_lines[0]
                            parent_name = re.sub(r'^\d+(\.\d+)*\s*', '', parent_name).strip()

                            parent_vals = {
                                'no': parent_no,
                                'name': parent_name,
                                'unit_name': '',
                                'quantity': 0.0,
                                'unit_price': 0.0,
                                'project_id': self.id,
                                'sequence': sequence,
                                'company_id': self.env.company.id,
                                'import_source': _source,
                            }
                            if current_lot:
                                parent_vals['lot_id'] = current_lot.id
                            try:
                                with self.env.cr.savepoint():
                                    parent_task = self.env['custom.task'].create(parent_vals)
                                    current_parent_task = parent_task
                                    task_code_map[parent_no] = parent_task
                            except Exception as e:
                                _logger.exception("Failed create parent (multiline) %s (sheet %s row %s): %s",
                                                  parent_no, sheet_name, ri, e)
                                parent_task = None
                                current_parent_task = None

                            sequence += 10

                            idx_sub = 2
                            for ln in multiline_lines[1:]:
                                sub_code = f"{code_val}.{idx_sub:02d}"
                                sdesc, sunit, sqty, sprice, samount = self._parse_subline_tokens(ln)

                                # fallback for empty sdesc: strip bullets, then take non-numeric tokens
                                sdesc = (sdesc or '').strip()
                                if not sdesc:
                                    ln_text = str(ln).strip()
                                    ln_text = re.sub(r'^\d+(\.\d+)*\s*', '', ln_text)
                                    ln_text = re.sub(r'^[A-Za-z]\)\s*', '', ln_text)
                                    parts = [p for p in re.split(r'\t|\s{2,}|\s+', ln_text) if
                                             p and not self._is_numeric_like(p)]
                                    sdesc = ' '.join(parts).strip() if parts else ln_text.strip()

                                sub_vals = {
                                    'no': sub_code,
                                    'name': sdesc,
                                    'unit_name': sunit or '',
                                    'quantity': sqty or 0.0,
                                    'unit_price': sprice or 0.0,
                                    'project_id': self.id,
                                    'parent_id': parent_task.id if parent_task else None,
                                    'sequence': sequence,
                                    'company_id': self.env.company.id,
                                    'import_source': _source,
                                }
                                if current_lot:
                                    sub_vals['lot_id'] = current_lot.id

                                if sunit:
                                    try:
                                        uom = self.env['uom.uom'].search([('name', 'ilike', sunit)], limit=1)
                                        if uom:
                                            sub_vals['unit'] = uom.id
                                    except Exception:
                                        pass

                                try:
                                    with self.env.cr.savepoint():
                                        self.env['custom.task'].create(sub_vals)
                                except Exception as e:
                                    _logger.exception("Failed create multiline sub-task %s (sheet %s row %s): %s",
                                                      sub_code, sheet_name, ri, e)

                                idx_sub += 1
                                sequence += 10

                            handled_multiline = True

                    if handled_multiline:
                        continue

                    # numeric extraction for single-row tasks/subtasks
                    numeric_idx = [i for i, c in enumerate(row) if c and self._is_numeric_like(c)]
                    qty = price = amount = 0.0
                    unit_text = ''
                    if numeric_idx:
                        amount_idx = numeric_idx[-1]
                        price_idx = numeric_idx[-2] if len(numeric_idx) >= 2 else None
                        qty_idx = numeric_idx[-3] if len(numeric_idx) >= 3 else None

                        if qty_idx is not None:
                            qty = self._parse_number(df.iloc[ri, qty_idx])
                        if price_idx is not None:
                            price = self._parse_number(df.iloc[ri, price_idx])
                        if amount_idx is not None:
                            amount = self._parse_number(df.iloc[ri, amount_idx])

                        if qty_idx is not None and qty_idx - 1 >= 0:
                            cand = row[qty_idx - 1]
                            if cand and not self._is_numeric_like(cand) and len(cand) <= 8:
                                unit_text = cand
                        if not unit_text:
                            for k in range(code_idx + 1, min(len(row), code_idx + 4)):
                                if row[k] and not self._is_numeric_like(row[k]) and len(row[k]) <= 8:
                                    unit_text = row[k]
                                    break

                    if (not price or price == 0.0) and qty and amount:
                        try:
                            price = amount / qty
                        except Exception:
                            price = 0.0

                    # Skip if description contains subtotal keywords
                    if any(k in (desc or "").upper() for k in self.SUBTOTAL_KEYWORDS):
                        continue

                    # build main vals. Only set 'no' for section/task (not deeper subtasks)
                    vals = {
                        'name': desc,
                        'unit_name': unit_text,
                        'quantity': qty,
                        'unit_price': price,
                        'project_id': self.id,
                        'sequence': sequence,
                        'company_id': self.env.company.id,
                        'import_source': _source,
                    }
                    if current_lot:
                        vals['lot_id'] = current_lot.id

                    # parent resolution
                    parent_id = False
                    if is_section:
                        parent_id = False
                    elif is_task:
                        parent_id = current_section.id if current_section else False
                    elif is_subtask:
                        parent_code = '.'.join(code_val.split('.')[:-1])
                        parent_task = task_code_map.get(parent_code)
                        if parent_task:
                            parent_id = parent_task.id
                        elif current_parent_task:
                            parent_id = current_parent_task.id

                    if parent_id:
                        vals['parent_id'] = parent_id

                    if code_val and [is_subtask, is_task, is_section]:
                        vals['no'] = code_val

                    if unit_text:
                        try:
                            uom = self.env['uom.uom'].search([('name', 'ilike', unit_text)], limit=1)
                            if uom:
                                vals['unit'] = uom.id
                        except Exception:
                            pass

                    try:
                        with self.env.cr.savepoint():
                            new_task = self.env['custom.task'].create(vals)
                            task_code_map[code_val] = new_task
                            if is_section:
                                current_section = new_task
                                current_parent_task = None
                            elif is_task:
                                current_parent_task = new_task
                    except Exception as e:
                        _logger.exception("Failed create task %s (sheet %s row %s): %s", code_val, sheet_name, ri, e)

                    sequence += 10
                    continue

                # ========== IMPROVED UNIT-CODED SUBTASKS WITH SMART NAMES ==========
                # معالجة المهام الفرعية التي تبدأ برموز وحدات (F, U, ML) مع إنشاء أسماء ذكية
                has_unit_code = False
                unit_code = None
                unit_code_index = None

                # البحث عن رموز الوحدات في الأعمدة الأولى
                for i in range(min(4, len(row))):
                    if row[i] and isinstance(row[i], str):
                        cell_upper = row[i].strip().upper()
                        # قائمة موسعة لرموز الوحدات الشائعة
                        unit_symbols = ['F', 'U', 'ML', 'M2', 'M3', 'M', 'KG', 'T', 'L', 'P', 'UNITE', 'UNIT', 'M²',
                                        'M³']
                        if cell_upper in unit_symbols:
                            has_unit_code = True
                            unit_code = cell_upper
                            unit_code_index = i
                            break

                if has_unit_code and current_parent_task:
                    # Check if this unit-coded line contains subtotal keywords
                    if self._contains_subtotal_keyword(row):
                        _logger.info("🚫 Skipping subtotal line in unit-coded section: %s", row)
                        continue

                    # ========== STRATEGY 1: البحث عن وصف في الخلايا المجاورة ==========
                    description_parts = []

                    # البحث في الخلايا قبل وبعد رمز الوحدة
                    search_range = []
                    if unit_code_index > 0:
                        search_range.extend(range(0, unit_code_index))  # الخلايا قبل
                    if unit_code_index + 1 < len(row):
                        search_range.extend(
                            range(unit_code_index + 1, min(unit_code_index + 4, len(row))))  # الخلايا بعد

                    for j in search_range:
                        if (row[j] and not self._is_numeric_like(row[j]) and
                                j != unit_code_index and
                                row[j].strip().upper() not in unit_symbols):

                            cell_content = str(row[j]).strip()
                            # تنظيف المحتوى من الرموز غير المرغوب فيها
                            cell_content = re.sub(r'^[\-\*\.\s]+|[\-\*\.\s]+$', '', cell_content)
                            if cell_content and len(cell_content) > 1:  # تجاهل النصوص القصيرة جداً
                                description_parts.append(cell_content)

                    # ========== STRATEGY 2: استخدام وصف المهمة الرئيسية مع تخصيص ==========
                    if not description_parts and current_parent_task.name:
                        # إنشاء أسماء ذكية بناءً على نوع الوحدة والمهمة الرئيسية
                        unit_descriptions = {
                            'F': 'Forfait',
                            'U': 'Unité',
                            'ML': 'Mètre Linéaire',
                            'M2': 'Mètre Carré',
                            'M3': 'Mètre Cube',
                            'M': 'Mètre',
                            'KG': 'Kilogramme',
                            'T': 'Tonne',
                            'L': 'Litre',
                            'P': 'Pièce'
                        }

                        unit_desc = unit_descriptions.get(unit_code, unit_code)
                        parent_name_short = current_parent_task.name
                        # تقصير الاسم الطويل إذا لزم الأمر
                        if len(parent_name_short) > 50:
                            parent_name_short = parent_name_short[:47] + "..."

                        sub_desc = f"{parent_name_short} - {unit_desc}"
                    elif description_parts:
                        sub_desc = ' '.join(description_parts)
                    else:
                        sub_desc = f"Tâche {unit_code}"

                    # ========== STRATEGY 3: استخدام السياق من الصفوف السابقة ==========
                    # إذا كان الاسم لا يزال عاماً جداً، نبحث في الصفوف السابقة لمزيد من السياق
                    if sub_desc == f"Tâche {unit_code}" and ri > 0:
                        prev_row = clean_matrix[ri - 1]
                        prev_text_cells = [str(c).strip() for c in prev_row if c and not self._is_numeric_like(c)]
                        if prev_text_cells and len(prev_text_cells[0]) > 10:
                            sub_desc = f"{prev_text_cells[0]} - {unit_code}"

                    # تنظيف الوصف النهائي
                    sub_desc = re.sub(r'\s+', ' ', sub_desc).strip()

                    # ========== استخراج القيم الرقمية ==========
                    sub_numeric_idx = [i for i, c in enumerate(row) if c and self._is_numeric_like(c)]
                    sub_qty = sub_price = sub_amount = 0.0

                    if sub_numeric_idx:
                        # تحديد مواقع القيم بناءً على عدد القيم الرقمية
                        if len(sub_numeric_idx) == 1:
                            # إذا كان هناك قيمة رقمية واحدة فقط، فهي عادة المبلغ
                            sub_amount = self._parse_number(df.iloc[ri, sub_numeric_idx[0]])
                        elif len(sub_numeric_idx) == 2:
                            # إذا كان هناك قيمتان، فهما عادة الكمية والمبلغ
                            sub_qty = self._parse_number(df.iloc[ri, sub_numeric_idx[0]])
                            sub_amount = self._parse_number(df.iloc[ri, sub_numeric_idx[1]])
                        elif len(sub_numeric_idx) >= 3:
                            # إذا كان هناك ثلاث قيم أو أكثر، فهي الكمية والسعر والمبلغ
                            sub_qty = self._parse_number(df.iloc[ri, sub_numeric_idx[0]])
                            sub_price = self._parse_number(df.iloc[ri, sub_numeric_idx[1]])
                            sub_amount = self._parse_number(df.iloc[ri, sub_numeric_idx[2]])

                        # الحسابات التلقائية للقيم المفقودة
                        if sub_amount == 0.0 and sub_qty != 0.0 and sub_price != 0.0:
                            sub_amount = float_round(sub_qty * sub_price, precision_digits=2)
                        elif (sub_price == 0.0) and sub_qty != 0.0 and sub_amount != 0.0:
                            sub_price = float_round(sub_amount / sub_qty, precision_digits=2) if sub_qty != 0.0 else 0.0

                    # ========== إنشاء المهمة الفرعية ==========
                    parent_no = current_parent_task.no if current_parent_task and current_parent_task.no else ""
                    if parent_no:
                        # Count existing subtasks for this parent to generate sequential code
                        existing_subtasks = self.env['custom.task'].search([
                            ('parent_id', '=', current_parent_task.id),
                            ('project_id', '=', self.id)
                        ])
                        sub_code_number = len(existing_subtasks) + 1
                        no = f"{parent_no}.{sub_code_number:02d}"
                    else:
                        # Fallback if parent has no code
                        no = f"SUB.{sequence:03d}"

                    sub_vals = {  # <-- This is the existing line, add the block above it
                        'no': no,  # <-- Add 'no' field here
                        'name': sub_desc,
                        'unit_name': unit_code,
                        'quantity': sub_qty,
                        'unit_price': sub_price,
                        'project_id': self.id,
                        'parent_id': current_parent_task.id,
                        'sequence': sequence,
                        'company_id': self.env.company.id,
                        'import_source': _source,
                    }

                    if current_lot:
                        sub_vals['lot_id'] = current_lot.id

                    if unit_code:
                        try:
                            unit_mapping = {
                                'F': 'Unité', 'U': 'Unité', 'ML': 'Mètre Linéaire',
                                'M2': 'Mètre Carré', 'M3': 'Mètre Cube', 'M': 'Mètre',
                                'KG': 'Kilogramme', 'T': 'Tonne', 'L': 'Litre', 'P': 'Pièce',
                                'UNITE': 'Unité', 'UNIT': 'Unité', 'M²': 'Mètre Carré', 'M³': 'Mètre Cube'
                            }
                            unit_search = unit_mapping.get(unit_code, unit_code)
                            uom = self.env['uom.uom'].search([('name', 'ilike', unit_search)], limit=1)
                            if not uom:
                                uom = self.env['uom.uom'].search([('name', 'ilike', unit_code)], limit=1)
                            if uom:
                                sub_vals['unit'] = uom.id
                        except Exception as e:
                            _logger.debug("Failed to find UOM for %s: %s", unit_code, e)

                    try:
                        with self.env.cr.savepoint():
                            new_subtask = self.env['custom.task'].create(sub_vals)
                            _logger.info(
                                "✅ Created unit-coded subtask: '%s' (Parent: '%s', Qty: %s, Price: %s, Amount: %s)",
                                sub_desc, current_parent_task.name, sub_qty, sub_price, sub_amount)
                    except Exception as e:
                        _logger.exception("Failed create unit-coded subtask (sheet %s row %s): %s", sheet_name, ri, e)

                    sequence += 10
                    continue

                # Continuation / sub-line when there's a current_parent_task (row without explicit code)
                if current_parent_task and any(c for c in row if c):
                    # Check if continuation line contains subtotal keywords
                    if self._contains_subtotal_keyword(row):
                        _logger.info("🚫 Skipping subtotal line in continuation section: %s", row)
                        continue

                    if any(self._is_numeric_like(c) for c in row):
                        # description: first non-numeric text cell
                        desc = ''
                        for j in range(len(row)):
                            if row[j] and not self._is_numeric_like(row[j]):
                                desc = row[j]
                                break

                        numeric_idx = [i for i, c in enumerate(row) if c and self._is_numeric_like(c)]
                        qty = price = amount = 0.0
                        unit_text = ''
                        if numeric_idx:
                            amount_idx = numeric_idx[-1]
                            price_idx = numeric_idx[-2] if len(numeric_idx) >= 2 else None
                            qty_idx = numeric_idx[-3] if len(numeric_idx) >= 3 else None

                            if qty_idx is not None:
                                qty = self._parse_number(df.iloc[ri, qty_idx])
                            if price_idx is not None:
                                price = self._parse_number(df.iloc[ri, price_idx])
                            if amount_idx is not None:
                                amount = self._parse_number(df.iloc[ri, amount_idx])

                            if qty_idx is not None and qty_idx - 1 >= 0:
                                cand = row[qty_idx - 1]
                                if cand and not self._is_numeric_like(cand) and len(cand) <= 8:
                                    unit_text = cand
                            if not unit_text:
                                for k in range(min(len(row), 6)):
                                    if row[k] and not self._is_numeric_like(row[k]) and len(row[k]) <= 8:
                                        unit_text = row[k]
                                        break

                        if (not price or price == 0.0) and qty and amount:
                            try:
                                price = amount / qty
                            except Exception:
                                price = 0.0

                        sub_vals = {
                            'name': desc,
                            'unit_name': unit_text,
                            'quantity': qty,
                            'unit_price': price,
                            'project_id': self.id,
                            'parent_id': current_parent_task.id,
                            'sequence': sequence,
                            'company_id': self.env.company.id,
                            'import_source': _source,
                        }
                        if current_lot:
                            sub_vals['lot_id'] = current_lot.id

                        if unit_text:
                            try:
                                uom = self.env['uom.uom'].search([('name', 'ilike', unit_text)], limit=1)
                                if uom:
                                    sub_vals['unit'] = uom.id
                            except Exception:
                                pass

                        try:
                            with self.env.cr.savepoint():
                                self.env['custom.task'].create(sub_vals)
                        except Exception as e:
                            _logger.exception("Failed create sub-task (continuation) (sheet %s row %s): %s", sheet_name,
                                              ri, e)

                        sequence += 10
                        continue

                # Continuation lines: append to last created task name
                text_cells = [c for c in row if c and not self._is_numeric_like(c)]
                if text_cells:
                    # Check if continuation text contains subtotal keywords
                    continuation_text = ' '.join(text_cells)
                    if any(keyword in continuation_text.upper() for keyword in self.SUBTOTAL_KEYWORDS):
                        _logger.info("🚫 Skipping subtotal continuation text: %s", continuation_text)
                        continue

                    try:
                        with self.env.cr.savepoint():
                            last = self.env['custom.task'].search([('project_id', '=', self.id)], order='id desc',
                                                                  limit=1)
                            if last:
                                if len(continuation_text.strip()) > 2:
                                    last.write({'name': (last.name or '') + ' ' + continuation_text})
                    except Exception as e:
                        _logger.exception("Failed append continuation (sheet %s row %s): %s", sheet_name, ri, e)
                    continue

            except Exception as e_row:
                _logger.exception("Error parsing row %s sheet %s: %s", ri, sheet_name, e_row)
                continue

    def import_excel_file(self):
        """Import principal"""
        self.ensure_one()
        if not self.import_file:
            raise UserError(_("Aucun fichier fourni!"))

        try:
            data = base64.b64decode(self.import_file)
        except Exception as e:
            _logger.exception("Base64 decode failed: %s", e)
            raise UserError(_("Erreur décodage base64 du fichier : %s") % str(e))

        try:
            xls_obj = pd.ExcelFile(io.BytesIO(data))
        except Exception:
            try:
                xls_obj = pd.ExcelFile(io.BytesIO(data), engine='openpyxl')
            except Exception as e:
                _logger.exception("Could not open Excel: %s", e)
                raise UserError(_("Impossible d'ouvrir le fichier Excel. Format invalide ou dépendances manquantes."))

        # remove old data
        try:
            with self.env.cr.savepoint():
                self.lots_ids.unlink()
                self.task_ids.unlink()
        except Exception as e:
            _logger.warning("Could not unlink existing tasks/lots: %s", e)

        # ensure tax 19% exists and assign to project
        tax19 = self._ensure_tva_19()
        if tax19 and tax19 not in self.tax_ids:
            self.tax_ids = [(4, tax19.id)]

        sheet_errors = []
        processed = []

        for sheet in xls_obj.sheet_names:
            try:
                try:
                    df_quick = pd.read_excel(xls_obj, sheet_name=sheet, header=None, nrows=8, dtype=object)
                    if df_quick.dropna(how='all').shape[0] < 2:
                        _logger.info("Skipping sheet (probably empty/cover): %s", sheet)
                        continue
                except Exception:
                    pass

                self._process_sheet_table_only(xls_obj, sheet, suffix='', source='primary')
                processed.append(sheet)
            except Exception as e:
                tb = traceback.format_exc()
                _logger.exception("Error processing sheet %s: %s", sheet, tb)
                sheet_errors.append((sheet, str(e)))
                continue

        if sheet_errors:
            msg = "Feuilles traitées: %s\nFeuilles en erreur:\n" % (", ".join(processed) or "aucune")
            for s, msg_err in sheet_errors:
                msg += "- %s : %s\n" % (s, msg_err)
            _logger.warning("Import partial: %s", msg)
            raise UserError(_("Import partiel terminé. Résumé:\n%s") % msg)

        return True

    # debug preview
    def debug_excel_preview(self):
        self.ensure_one()
        if not self.import_file:
            raise UserError(_("Aucun fichier fourni!"))

        try:
            data = base64.b64decode(self.import_file)
        except Exception as e:
            raise UserError(_("Erreur décodage base64: %s") % str(e))
        try:
            xls = pd.ExcelFile(io.BytesIO(data))
        except Exception:
            try:
                xls = pd.ExcelFile(io.BytesIO(data), engine='openpyxl')
            except Exception as e:
                _logger.exception("debug_excel_preview open failed: %s", e)
                raise UserError(_("Impossible d'ouvrir le fichier pour preview: %s. Voir logs.") % str(e))

        out = "Feuilles trouvées: %s\n\n" % ", ".join(xls.sheet_names)
        for sheet in xls.sheet_names:
            try:
                df = pd.read_excel(xls, sheet_name=sheet, header=None, nrows=30, dtype=object)
                out += "=== %s ===\n" % sheet
                for idx, row in df.iterrows():
                    cells = [str(x)[:400].replace("\n", " ") for x in row.fillna('').tolist()]
                    out += " | ".join(cells) + "\n"
                out += "\n"
            except Exception as e:
                out += "=== %s ===\nERROR reading preview: %s\n\n" % (sheet, str(e))
        raise UserError(out)

    def _render_task_with_children(self, task, all_tasks, level=0):
        """Recursively render a task and its children for primary table"""
        html = ""
        no = task.no or ''
        unit_display = task.unit_name or (task.unit.name if task.unit else '')

        # Handle different task types
        if getattr(task, 'is_title', False):
            if getattr(task, 'is_category', False):
                html += f'<tr style="background-color:#d4edda;color:#155724;font-weight:bold;"><td colspan="6" style="border:1px solid #ddd;">{task.name or ""}</td></tr>'
            else:
                html += f'<tr style="background-color:#fff3cd;font-weight:bold;"><td colspan="6" style="border:1px solid #ddd;">{task.name or ""}</td></tr>'
            return html

        # ========== ADD SUBTOTAL ROW HANDLING ==========
        # Check if this is a subtotal row (contains subtotal keywords in name)
        task_name_upper = (task.name or "").upper()
        is_subtotal = any(keyword in task_name_upper for keyword in self.SUBTOTAL_KEYWORDS)

        if is_subtotal:
            # Render subtotal row with different styling
            html += f'<tr style="background-color:#e8f4fd;font-weight:bold;border-top:2px solid #007bff;">'
            html += f'<td style="border:1px solid #ddd;"></td>'  # Empty code cell
            html += f'<td style="border:1px solid #ddd;font-style:italic;">{task.name or ""}</td>'
            html += f'<td style="border:1px solid #ddd;"></td>'  # Empty unit cell
            html += f'<td style="border:1px solid #ddd;text-align:right;"></td>'  # Empty quantity
            html += f'<td style="border:1px solid #ddd;text-align:right;"></td>'  # Empty unit price
            html += f'<td style="border:1px solid #ddd;text-align:right;font-weight:bold;">{self._format_number(task.total_price, 2)}</td>'
            html += '</tr>'
            return html
        # ========== END SUBTOTAL ROW HANDLING ==========

        if no == 's/total':
            html += f'<tr style="background-color:#dff0d8;color:#155724;font-weight:bold;"><td colspan="2" style="border:1px solid #ddd;">{task.name or ""}</td><td style="border:1px solid #ddd;text-align:right;" colspan="4">{self._format_number(task.total_price, 2)}</td></tr>'
            return html

        # Calculate padding for child tasks
        padding_left = level * 20
        name_style = f"border:1px solid #ddd;padding-left:{padding_left}px;"
        cell_style = "border:1px solid #ddd;"

        # Get child tasks
        child_tasks = all_tasks.filtered(lambda t: t.parent_id == task).sorted(key=lambda r: r.sequence)

        # If this task has children, it's a parent task
        if child_tasks:
            # Render parent task (show total but no quantity/price details)
            html += f'<tr style="background-color:#f7f7f7;font-weight:bold;">'
            html += f'<td style="{cell_style}">{no}</td>'
            html += f'<td style="{name_style}">{task.name or ""}</td>'
            html += f'<td style="{cell_style}"></td>'
            html += f'<td style="{cell_style};text-align:right;"></td>'
            html += f'<td style="{cell_style};text-align:right;"></td>'
            html += f'<td style="{cell_style};text-align:right;">{self._format_number(task.total_price, 2)}</td>'
            html += '</tr>'

            # Render all child tasks
            for child in child_tasks:
                html += self._render_task_with_children(child, all_tasks, level + 1)

            # ========== ADD AUTOMATIC SUBTOTAL FOR PARENT TASKS ==========
            # Calculate subtotal for this parent task's children
            child_total = sum(child.total_price for child in child_tasks)
            if abs(child_total - task.total_price) > 0.01:  # If there's a difference
                html += f'<tr style="background-color:#f8f9fa;font-weight:bold;border-top:1px solid #dee2e6;">'
                html += f'<td style="{cell_style}"></td>'
                html += f'<td style="{name_style};font-style:italic;">S/TOTAL {task.name or ""}</td>'
                html += f'<td style="{cell_style}"></td>'
                html += f'<td style="{cell_style};text-align:right;"></td>'
                html += f'<td style="{cell_style};text-align:right;"></td>'
                html += f'<td style="{cell_style};text-align:right;font-weight:bold;">{self._format_number(child_total, 2)}</td>'
                html += '</tr>'
            # ========== END AUTOMATIC SUBTOTAL ==========

        else:
            # This is a leaf task (no children) - show full details
            html += f'<tr>'
            html += f'<td style="{cell_style}">{no}</td>'
            html += f'<td style="{name_style}">{task.name or ""}</td>'
            html += f'<td style="{cell_style}">{unit_display}</td>'
            html += f'<td style="{cell_style};text-align:right;">{self._format_number(task.quantity, 3)}</td>'
            html += f'<td style="{cell_style};text-align:right;">{self._format_number(task.unit_price, 3)}</td>'
            html += f'<td style="{cell_style};text-align:right;">{self._format_number(task.total_price, 3)}</td>'
            html += '</tr>'

        return html

    # ----------------------------
    # HTML Table Rendering (primary)
    # ----------------------------
    @api.depends('task_ids', 'lots_ids', 'task_ids.total_price', 'lots_ids.task_ids.total_price')
    def _compute_table_html(self):
        for project in self:
            lots_file1 = project.lots_ids.filtered(lambda l: l.import_source == 'primary')
            html = """<table class="table table-bordered" style="border-collapse:collapse;width:100%;">
                            <thead>
                              <tr style="background-color:#f2f2f2;">
                                <th style="width:5%;border:1px solid #ddd;">N°</th>
                                <th style="width:55%;border:1px solid #ddd;">DESIGNATION DES OUVRAGES</th>
                                <th style="width:5%;border:1px solid #ddd;">U</th>
                                <th style="width:10%;border:1px solid #ddd;text-align:right;">QUANTITES</th>
                                <th style="width:10%;border:1px solid #ddd;text-align:right;">PRIX UNITAIRES</th>
                                <th style="width:15%;border:1px solid #ddd;text-align:right;">MONTANT</th>
                              </tr>
                            </thead>
                            <tbody>"""

            for lot in lots_file1:
                html += f'<tr style="background-color:#d9edf7;font-weight:bold;"><td colspan="6">{lot.name or ""}</td></tr>'

                # Get all tasks for this lot (both parent and child tasks)
                all_tasks = lot.task_ids.filtered(lambda t: t.import_source == 'primary').sorted(
                    key=lambda r: r.sequence)

                # Find top-level tasks (no parent)
                top_tasks = all_tasks.filtered(lambda t: not t.parent_id)

                for task in top_tasks:
                    html += self._render_task_with_children(task, all_tasks)

                # ========== ADD LOT SUBTOTAL ==========
                lot_total = sum(task.total_price for task in top_tasks)
                html += f'<tr style="background-color:#cce7ff;font-weight:bold;border-top:2px solid #0056b3;">'
                html += f'<td colspan="5" style="border:1px solid #ddd;text-align:right;font-style:italic;">TOTAL {lot.name or "LOT"}</td>'
                html += f'<td style="border:1px solid #ddd;text-align:right;font-weight:bold;">{self._format_number(lot_total, 2)}</td>'
                html += '</tr>'
                # ========== END LOT SUBTOTAL ==========

            # ========== ADD PROJECT GRAND TOTAL ==========

            # html += f'<tr style="background-color:#b3d9ff;font-weight:bold;border-top:3px double #004085;">'
            # # html += f'<td colspan="5" style="border:1px solid #ddd;text-align:right;">TOTAL GÉNÉRAL PROJET</td>'
            # # html += f'<td style="border:1px solid #ddd;text-align:right;font-weight:bold;">{self._format_number(2)}</td>'
            # html += '</tr>'
            # ========== END PROJECT GRAND TOTAL ==========

            html += "</tbody></table>"
            project.table_html = html

    # ----------------------------
    # HTML Table Rendering (secondary)
    # ----------------------------

    def debug_check_subtasks(self):
        """Debug method to check subtask relationships"""
        self.ensure_one()
        tasks = self.task_ids.sorted('sequence')

        debug_info = f"Total tasks: {len(tasks)}\n\n"

        for task in tasks:
            debug_info += f"Task: {task.no or 'No Code'} - '{task.name}'\n"
            debug_info += f"  Parent: {task.parent_id.name if task.parent_id else 'None'}\n"
            debug_info += f"  Children: {len(task.child_ids)}\n"
            debug_info += f"  Lot: {task.lot_id.name if task.lot_id else 'None'}\n"
            debug_info += f"  Import Source: {task.import_source}\n"
            debug_info += "  ---\n"

        raise UserError(debug_info)

    def action_draft(self):
        self.state = 'draft'

    def action_confirm(self):
        self.state = 'confirmed'

    def action_done(self):
        self.state = 'done'

    def action_cancel(self):
        self.state = 'cancelled'

    @api.depends('task_ids.total_price')
    def _compute_total_price(self):
        """Somme des montants des tâches principales (ignore child tasks pour éviter double comptage)."""
        for project in self:
            total = 0.0
            if project.task_ids:
                main_tasks = project.task_ids.filtered(lambda t: not t.parent_id)
                for t in main_tasks:
                    total += t.total_price or 0.0
            project.total_price = float_round(total, precision_digits=2)

    @api.depends('total_price', 'tax_ids.amount', 'tax_ids.amount_type')
    def _compute_tax_totale(self):
        for project in self:
            tax_total = 0.0
            base = project.total_price or 0.0
            for tax in project.tax_ids:
                try:
                    if tax.amount_type == 'percent':
                        tax_total += base * (tax.amount or 0.0) / 100.0
                    elif tax.amount_type == 'fixed':
                        tax_total += (tax.amount or 0.0)
                    else:
                        tax_total += base * (tax.amount or 0.0) / 100.0
                except Exception:
                    _logger.exception("Erreur calcul taxe pour project %s", project.id)
            project.tax_totale = float_round(tax_total, precision_digits=2)

    @api.depends('total_price', 'tax_totale')
    def _compute_total(self):
        for project in self:
            project.total = float_round((project.total_price or 0.0) + (project.tax_totale or 0.0), precision_digits=2)

    def action_export_final_situation(self):
        self.ensure_one()
        # Find or create a temporary situation final record for this project
        situation_final = self.env['situation.final'].search([
            ('project_id', '=', self.id)
        ], limit=1)

        if not situation_final:
            situation_final = self.env['situation.final'].create({
                'project_id': self.id,
                'no': '001',
                'article2': 'Export temporaire'
            })

        return situation_final.export_final_situation_xlsx()
