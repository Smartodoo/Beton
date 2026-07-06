import logging
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


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
        default=lambda self: self._default_objectif(),
        help="Quantité objectif à produire pour cet ordre. "
             "Obligatoire (> 0) pour confirmer la fabrication. "
             "Valeur par défaut définie globalement via 'Objectif de Production'.",
    )

    @api.model
    def _default_objectif(self):
        """Objectif par défaut des nouveaux OF, défini globalement via le
        wizard 'Objectif de Production' (paramètre système)."""
        val = self.env['ir.config_parameter'].sudo().get_param(
            'beton_base.objectif_defaut', 0.0)
        try:
            return float(val)
        except (TypeError, ValueError):
            return 0.0
    taux_production = fields.Float(
        string="Taux de production (%)",
        compute='_compute_taux_production',
        store=True,
        digits=(6, 2),
        help="(qty_produced / objectif) × 100. Peut dépasser 100% si la "
             "production dépasse l'objectif.",
    )
    objectif_history_ids = fields.One2many(
        'beton.objectif.history', 'production_id',
        string="Historique des objectifs")
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
    vente_ids = fields.One2many(
        'sale.order', 'production_beton_id', string="Ventes liées")
    vente_id = fields.Many2one(
        'sale.order', string="Vente associée",
        compute='_compute_vente_associee', store=True)
    vente_state = fields.Selection(
        related='vente_id.state', string="Statut de la vente", store=True)
    alerte_vente_envoyee = fields.Boolean(
        string="Alerte 'sans vente' envoyée", default=False, copy=False)

    def _log_objectif_history(self, entries):
        """Crée les lignes d'historique d'objectif (en sudo pour éviter les
        problèmes de droits sur les utilisateurs standards)."""
        if entries:
            self.env['beton.objectif.history'].sudo().create(entries)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        entries = []
        for rec in records:
            if rec.objectif:
                entries.append({
                    'production_id': rec.id,
                    'ancien_objectif': 0.0,
                    'nouvel_objectif': rec.objectif,
                    'source': 'creation',
                })
        self._log_objectif_history(entries)
        return records

    def write(self, vals):
        if 'objectif' not in vals:
            return super().write(vals)
        source = self.env.context.get('objectif_source', 'manuel')
        new_val = vals.get('objectif') or 0.0
        anciens = {rec.id: rec.objectif for rec in self}
        res = super().write(vals)
        entries = []
        for rec in self:
            ancien = anciens.get(rec.id, 0.0)
            if ancien != new_val:
                entries.append({
                    'production_id': rec.id,
                    'ancien_objectif': ancien,
                    'nouvel_objectif': new_val,
                    'source': source,
                })
        self._log_objectif_history(entries)
        return res

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

    @api.depends('objectif', 'qty_produced')
    def _compute_ecart_beton(self):
        """Écart = production réelle - objectif. Négatif = sous-production."""
        for rec in self:
            rec.ecart_production = rec.qty_produced - rec.objectif

    @api.depends('objectif', 'qty_produced')
    def _compute_taux_production(self):
        """Taux = (qty_produced / objectif) × 100.
        Peut dépasser 100% si la production dépasse l'objectif.
        Objectif = 0 (non renseigné) ⇒ taux 0 (pas de fausse valeur à 100%)."""
        for rec in self:
            if rec.objectif and rec.objectif > 0:
                rec.taux_production = rec.qty_produced / rec.objectif * 100.0
            else:
                rec.taux_production = 0.0

    @api.constrains('objectif', 'state')
    def _check_objectif_positif(self):
        """Empêche de confirmer/produire un ordre dont l'objectif vaut 0.
        Les brouillons et ordres annulés restent tolérés (objectif saisi plus tard)."""
        for rec in self:
            if rec.state not in ('draft', 'cancel') and (not rec.objectif or rec.objectif <= 0):
                raise ValidationError(_(
                    "L'objectif (m³) doit être supérieur à 0 pour l'ordre %s. "
                    "Veuillez renseigner un objectif avant de confirmer la fabrication.",
                    rec.name or '',
                ))

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

    @api.depends('vente_ids', 'vente_ids.state')
    def _compute_vente_associee(self):
        """Vente associée à l'OF : la plus récente non annulée (à défaut la
        plus récente). Stockée pour permettre filtre et regroupement."""
        for rec in self:
            orders = rec.vente_ids
            non_annulees = orders.filtered(lambda o: o.state != 'cancel')
            chosen = non_annulees[:1] or orders[:1]
            rec.vente_id = chosen.id if chosen else False

    def _build_alerte_vente_body(self):
        """Corps HTML de l'alerte 'OF sans vente confirmée'."""
        self.ensure_one()
        libelles = dict(self.env['sale.order']._fields['state']._description_selection(self.env))
        if not self.vente_id:
            statut = "Aucune vente associée"
        else:
            statut = "Vente %s — %s" % (
                self.vente_id.name,
                libelles.get(self.vente_state, self.vente_state or ''),
            )
        return (
            '<div style="border-left:4px solid #ee8126; padding:8px 12px; '
            'background:#fff8f2;">'
            '<strong style="color:#1a3c69;">Ordre de fabrication sans vente '
            'confirmée depuis plus d\'une semaine</strong>'
            '<table style="margin-top:6px; border-collapse:collapse; font-size:13px;">'
            '<tr><td style="padding:4px 8px; color:#555;">Ordre</td>'
            '<td style="padding:4px 8px; font-weight:bold;">%s</td></tr>'
            '<tr style="background:#fff;"><td style="padding:4px 8px; color:#555;">Client</td>'
            '<td style="padding:4px 8px;">%s</td></tr>'
            '<tr><td style="padding:4px 8px; color:#555;">Chantier</td>'
            '<td style="padding:4px 8px;">%s</td></tr>'
            '<tr style="background:#fff;"><td style="padding:4px 8px; color:#555;">Créé le</td>'
            '<td style="padding:4px 8px;">%s</td></tr>'
            '<tr><td style="padding:4px 8px; color:#555;">Vente</td>'
            '<td style="padding:4px 8px; font-weight:bold; color:#c0392b;">%s</td></tr>'
            '</table></div>'
        ) % (
            self.name or '',
            self.client_id.name or '—',
            self.chantier or '—',
            self.create_date and self.create_date.strftime('%d/%m/%Y') or '—',
            statut,
        )

    @api.model
    def _cron_check_of_sans_vente(self):
        """Cron : notifie sur le canal Discuss les ordres de fabrication créés
        depuis plus d'une semaine qui n'ont pas de vente ou dont la vente
        n'est pas confirmée. Chaque ordre n'est notifié qu'une seule fois."""
        channel = self.env.ref(
            'beton_base.channel_of_sans_vente', raise_if_not_found=False)
        if not channel:
            _logger.warning(
                "Canal 'OF sans vente' introuvable "
                "(beton_base.channel_of_sans_vente).")
            return
        # Abonner les groupes Responsable et Technique au canal
        groups = self.env['res.groups']
        for xid in ('beton_base.group_beton_responsable', 'base.group_system'):
            grp = self.env.ref(xid, raise_if_not_found=False)
            if grp:
                groups |= grp
        missing = groups - channel.sudo().group_ids
        if missing:
            channel.sudo().write({'group_ids': [(4, g.id) for g in missing]})

        cutoff = fields.Datetime.now() - timedelta(days=7)
        ordres = self.search([
            ('create_date', '<=', cutoff),
            ('state', '!=', 'cancel'),
            ('alerte_vente_envoyee', '=', False),
            ('product_id.product_tmpl_id.detailed_type', '=', 'fabrique'),
        ])
        for ordre in ordres:
            # Pas de vente, ou vente non confirmée (ni 'sale' ni 'done')
            if not ordre.vente_id or ordre.vente_state not in ('sale', 'done'):
                channel.sudo().message_post(
                    body=ordre._build_alerte_vente_body(),
                    message_type='comment',
                    subtype_xmlid='mail.mt_comment',
                )
                ordre.alerte_vente_envoyee = True

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

    def action_ouvrir_annulation(self):
        """Ouvre le wizard de confirmation/motif avant annulation."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': "Annulation de l'ordre de fabrication",
            'res_model': 'beton.annulation.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_production_id': self.id},
        }

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
