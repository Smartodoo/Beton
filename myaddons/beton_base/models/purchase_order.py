from odoo import api, models, fields
from odoo.tools.float_utils import float_compare


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    qty_en_stock = fields.Float(
        related='product_id.qty_available',
        string="Qté en stock",
        digits='Product Unit of Measure',
        readonly=True,
        store=False,
    )

    @api.depends('product_id', 'product_uom', 'company_id')
    def _compute_price_unit_and_date_planned_and_name(self):
        """Override : on force le prix unitaire à refléter le coût ACTUEL du
        produit (standard_price), peu importe le supplierinfo.

        Dépendances restreintes à ('product_id', 'product_uom', 'company_id')
        pour ne PAS écraser un prix saisi manuellement quand l'utilisateur
        change la quantité, le partenaire, la date, ou confirme la commande
        (changement de state). Le prix proposé n'est posé qu'à la sélection
        du produit (ou changement d'UdM/société)."""
        super()._compute_price_unit_and_date_planned_and_name()
        for line in self:
            if not line.product_id or line.invoice_lines or not line.company_id:
                continue
            product = line.product_id
            # Toujours proposer le Coût (standard_price), peu importe la classification.
            cost = product.standard_price
            if cost <= 0:
                continue
            # Convertir vers l'UoM de la ligne
            if line.product_uom and line.product_uom != product.uom_id:
                cost = product.uom_id._compute_price(cost, line.product_uom)
            # Convertir vers la devise de la commande
            company_currency = line.company_id.currency_id
            order_currency = line.order_id.currency_id or company_currency
            if order_currency != company_currency:
                cost = company_currency._convert(
                    cost, order_currency, line.company_id,
                    line.order_id.date_order or fields.Date.today(),
                )
            line.price_unit = cost


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def button_confirm(self):
        result = super().button_confirm()
        for order in self:
            order._beton_update_product_cost_from_lines()
        return result

    def _beton_update_product_cost_from_lines(self):
        """À la confirmation d'un bon de commande, si le prix d'achat d'une ligne
        diffère du coût de la fiche produit, mettre à jour le coût et tracer
        la modification dans l'historique des coûts (avec fournisseur + PO)."""
        self.ensure_one()
        history_obj = self.env['product.cost.history'].sudo()
        for line in self.order_line:
            product = line.product_id
            if not product or line.price_unit <= 0:
                continue
            # Convertir le prix unitaire vers l'UoM de référence du produit
            if line.product_uom and line.product_uom != product.uom_id:
                price_unit = line.product_uom._compute_price(line.price_unit, product.uom_id)
            else:
                price_unit = line.price_unit
            # Convertir vers la devise de la société si nécessaire
            if self.currency_id and self.currency_id != self.company_id.currency_id:
                price_unit = self.currency_id._convert(
                    price_unit,
                    self.company_id.currency_id,
                    self.company_id,
                    self.date_order or fields.Date.today(),
                )
            tmpl = product.product_tmpl_id
            common_vals = {
                'product_tmpl_id': tmpl.id,
                'fournisseur_id': self.partner_id.id,
                'purchase_order_id': self.id,
                'source': 'purchase',
                'note': "Mise à jour automatique via achat %s" % self.name,
            }
            # Pour les matières premières : on compare price_unit au Coût (standard_price).
            # Si différent, on met à jour prix_achat = price_unit, et standard_price
            # se recalcule automatiquement = prix_achat + cout_divers.
            if tmpl.classification_produit == 'matiere_premiere':
                ancien_cout = product.standard_price
                rounding = product.uom_id.rounding or 0.01
                if float_compare(price_unit, ancien_cout, precision_rounding=rounding) == 0:
                    self._beton_sync_supplierinfo(product, price_unit)
                    continue
                nouveau_cout = price_unit + tmpl.cout_divers
                difference = nouveau_cout - ancien_cout
                history_obj.create({
                    **common_vals,
                    'ancien_cout': ancien_cout,
                    'difference': difference,
                    'nouveau_cout': nouveau_cout,
                })
                tmpl.with_context(
                    skip_cost_history=True,
                    beton_purchase_history=True,
                ).sudo().prix_achat = price_unit
            else:
                ancien_cout = product.standard_price
                rounding = product.uom_id.rounding or 0.01
                if float_compare(price_unit, ancien_cout, precision_rounding=rounding) == 0:
                    self._beton_sync_supplierinfo(product, price_unit)
                    continue
                difference = price_unit - ancien_cout
                history_obj.create({
                    **common_vals,
                    'ancien_cout': ancien_cout,
                    'difference': difference,
                    'nouveau_cout': price_unit,
                })
                product.with_context(skip_cost_history=True).sudo().standard_price = price_unit
            # Synchronise le tarif fournisseur (product.supplierinfo) pour que le
            # prix unitaire proposé sur les prochaines lignes reflète le dernier prix.
            self._beton_sync_supplierinfo(product, price_unit)

    def _beton_sync_supplierinfo(self, product, price_unit):
        """Met à jour (ou crée) le tarif fournisseur pour ce produit afin que
        Odoo propose ce prix sur la prochaine sélection du produit pour ce
        partenaire — sinon le natif lit l'ancien prix de supplierinfo."""
        self.ensure_one()
        if not product or not self.partner_id:
            return
        Supplierinfo = self.env['product.supplierinfo'].sudo()
        domain = [
            ('partner_id', '=', self.partner_id.id),
            '|',
                ('product_id', '=', product.id),
                '&', ('product_id', '=', False),
                     ('product_tmpl_id', '=', product.product_tmpl_id.id),
        ]
        seller = Supplierinfo.search(domain, order='min_qty asc, price asc, sequence', limit=1)
        if seller:
            seller.write({
                'price': price_unit,
                'currency_id': self.currency_id.id,
            })
        else:
            Supplierinfo.create({
                'partner_id': self.partner_id.id,
                'product_tmpl_id': product.product_tmpl_id.id,
                'product_id': product.id,
                'price': price_unit,
                'currency_id': self.currency_id.id,
                'min_qty': 0.0,
            })
