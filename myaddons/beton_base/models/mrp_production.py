from odoo import _, api, fields, models
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    # Champs spécifiques béton ajoutés à l'ordre de fabrication standard
    centrale_id = fields.Many2one('beton.centrale', string="Centrale")
    client_id = fields.Many2one(
        'res.partner',
        string="Client",
        domain="[('type_partenaire_beton', '=', 'client')]",
        context={'default_type_partenaire_beton': 'client', 'default_is_company': True},
    )
    chantier = fields.Char(string="Chantier")
    destination = fields.Char(string="Destination")
    distance = fields.Float(string="Distance (km)")

    # Quantités spécifiques béton
    nombre_camion = fields.Integer(string="Nombre de camions")
    nombre_gachees = fields.Integer(string="Nombre de gâchées")
    ecart_production = fields.Float(
        string="Écart (m³)",
        compute='_compute_ecart_beton',
        store=True,
    )
    objectif = fields.Float(
        string="Objectif (m³)",
        help="Quantité objectif à produire pour cet ordre. "
             "Si vide, on utilise la quantité demandée (product_qty).",
    )
    objectif_effectif = fields.Float(
        string="Objectif effectif",
        compute='_compute_taux_production',
        store=True,
        help="Objectif s'il est renseigné, sinon quantité demandée.",
    )
    taux_production = fields.Float(
        string="Taux de production (%)",
        compute='_compute_taux_production',
        store=True,
        digits=(6, 2),
        help="(qty_produced / objectif_effectif) × 100",
    )
    cout_total = fields.Float(
        string="Coût",
        compute='_compute_cout_total',
        store=True,
    )

    # Timing
    operateur_id = fields.Many2one('hr.employee', string="Opérateur")
    heure_debut = fields.Float(string="Heure début")
    heure_fin = fields.Float(string="Heure fin")

    # Service (Pompe à béton, etc.)
    inclure_service = fields.Boolean(string="Inclure un service")
    service_product_id = fields.Many2one(
        'product.product', string="Produit service",
        domain="[('detailed_type', '=', 'service')]")

    # Transport
    transport_ligne_ids = fields.One2many(
        'beton.transport.ligne',
        'production_id',
        string="Transport",
    )
    document_ids = fields.Many2many(
        'ir.attachment', 'mrp_production_ir_attachment_rel',
        'production_id', 'attachment_id',
        string="Pièces jointes")
    vente_count = fields.Integer(string="Vente", compute='_compute_vente_count')

    @api.onchange('move_raw_ids')
    def _onchange_move_raw_ids_qty_minimum(self):
        alerts = []
        for move in self.move_raw_ids:
            product = move.product_id
            tmpl = product.product_tmpl_id if product else False
            if tmpl and tmpl.qty_minimum > 0 and product.qty_available <= tmpl.qty_minimum:
                alerts.append(_(
                    "• %(product)s : stock disponible %(qty)s ≤ seuil minimum %(min)s",
                    product=product.name,
                    qty=product.qty_available,
                    min=tmpl.qty_minimum,
                ))
        if alerts:
            return {
                'warning': {
                    'title': _("Alerte quantité minimum"),
                    'message': '\n'.join(alerts),
                    'type': 'notification',
                }
            }

    @api.depends('product_qty', 'qty_produced')
    def _compute_ecart_beton(self):
        for rec in self:
            rec.ecart_production = rec.qty_produced - rec.product_qty

    @api.depends('objectif', 'product_qty', 'qty_produced')
    def _compute_taux_production(self):
        """Objectif effectif = objectif renseigné ou, à défaut, quantité demandée.
        Taux = (qty_produced / objectif_effectif) × 100."""
        for rec in self:
            obj_eff = rec.objectif if rec.objectif and rec.objectif > 0 else (rec.product_qty or 0.0)
            rec.objectif_effectif = obj_eff
            rec.taux_production = (rec.qty_produced / obj_eff * 100.0) if obj_eff > 0 else 0.0

    @api.depends('move_raw_ids.quantity', 'move_raw_ids.product_id.standard_price')
    def _compute_cout_total(self):
        for rec in self:
            rec.cout_total = sum(
                m.quantity * m.product_id.standard_price
                for m in rec.move_raw_ids
            )

    def _compute_vente_count(self):
        for rec in self:
            rec.vente_count = self.env['sale.order'].search_count([
                ('production_beton_id', '=', rec.id),
            ])

    def _prepare_vente_vals(self):
        """Prépare les valeurs d'une vente unique pour toute la fabrication."""
        total_qty = sum(self.transport_ligne_ids.mapped('quantite'))
        order_lines = [(0, 0, {
            'product_id': self.product_id.id,
            'product_uom_qty': total_qty,
            'product_uom': self.product_uom_id.id,
        })]
        # Ajouter le produit service si coché
        if self.inclure_service and self.service_product_id:
            order_lines.append((0, 0, {
                'product_id': self.service_product_id.id,
                'product_uom_qty': 1,
                'product_uom': self.service_product_id.uom_id.id,
            }))
        return {
            'partner_id': self.client_id.id,
            'origin': self.name,
            'production_beton_id': self.id,
            'chantier': self.chantier or '',
            'order_line': order_lines,
        }

    def _creer_vente(self):
        """Crée une vente unique pour la fabrication."""
        self.ensure_one()
        if not self.transport_ligne_ids:
            raise UserError("Veuillez ajouter au moins une ligne de transport.")
        if not self.client_id:
            raise UserError("Veuillez renseigner le client.")
        if any(l.quantite <= 0 for l in self.transport_ligne_ids):
            raise UserError("Veuillez renseigner la quantité pour chaque camion.")
        existing = self.env['sale.order'].search_count([
            ('production_beton_id', '=', self.id),
            ('state', '!=', 'cancel'),
        ])
        if existing:
            raise UserError("Une vente existe déjà pour cette fabrication.")
        return self.env['sale.order'].create(self._prepare_vente_vals())

    def action_creer_vente(self):
        """Crée la vente (brouillon)."""
        self._creer_vente()

    def action_creer_confirmer_vente(self):
        """Crée et confirme la vente avec livraisons séparées par camion."""
        order = self._creer_vente()
        order.action_confirm()

    def action_reset_to_draft(self):
        """Remettre un ordre de fabrication annulé en brouillon."""
        for rec in self:
            if rec.state != 'cancel':
                raise UserError("Seuls les ordres annulés peuvent être remis en brouillon.")
            moves = rec.move_raw_ids | rec.move_finished_ids
            moves.filtered(lambda m: m.state == 'cancel').write({'state': 'draft'})
            rec.state = 'draft'

    def action_voir_vente(self):
        """Ouvre la vente liée."""
        self.ensure_one()
        orders = self.env['sale.order'].search([('production_beton_id', '=', self.id)])
        if len(orders) == 1:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Vente',
                'res_model': 'sale.order',
                'view_mode': 'form',
                'res_id': orders.id,
            }
        return {
            'type': 'ir.actions.act_window',
            'name': 'Ventes',
            'res_model': 'sale.order',
            'view_mode': 'tree,form',
            'domain': [('production_beton_id', '=', self.id)],
        }


class BetonTransportLigne(models.Model):
    _name = 'beton.transport.ligne'
    _description = 'Ligne de transport'

    production_id = fields.Many2one('mrp.production', string="Ordre de fabrication", ondelete='cascade')
    vehicle_id = fields.Many2one('fleet.vehicle', string="Camion")
    chauffeur_id = fields.Many2one('hr.employee', string="Chauffeur", domain="[('role_employe', '=', 'chauffeur')]")
    quantite = fields.Float(string="Quantité (m³)")
    heure_depart = fields.Datetime(string="Heure départ centrale")
    heure_arrivee = fields.Datetime(string="Heure arrivée chantier")
    temps_attente = fields.Float(string="Temps d'attente (min)")
