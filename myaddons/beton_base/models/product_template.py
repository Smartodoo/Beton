import logging
import math

from markupsafe import Markup
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    detailed_type = fields.Selection(
        selection_add=[('fabrique', 'Produit fabriqué')],
        ondelete={'fabrique': 'set consu'},
    )

    def _detailed_type_mapping(self):
        mapping = super()._detailed_type_mapping()
        mapping['fabrique'] = 'product'
        return mapping

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            rec._notify_prix_vente_reminder()
        return records

    def _notify_prix_vente_reminder(self):
        """Envoie un rappel non-bloquant à l'utilisateur courant pour vérifier
        le prix de vente du produit nouvellement créé."""
        self.ensure_one()
        self.env['bus.bus']._sendone(
            self.env.user.partner_id,
            'simple_notification',
            {
                'type': 'warning',
                'title': _("Rappel - Prix de vente"),
                'message': _(
                    "N'oubliez pas de saisir une valeur convenable pour le prix "
                    "de vente du produit '%s'."
                ) % (self.name or ''),
                'sticky': True,
            },
        )

    def write(self, vals):
        recalc_cout = (
            ('prix_achat' in vals or 'cout_divers' in vals)
            and not self.env.context.get('skip_recalc_cout')
        )
        track_history = (
            'standard_price' in vals
            and not self.env.context.get('skip_cost_history')
        )
        # Capture des anciens coûts AVANT modification (pour traçage manuel + recalc cout_divers)
        old_costs = {}
        old_state = {}
        if track_history:
            old_costs = {tmpl.id: tmpl.standard_price for tmpl in self}
        if 'cout_divers' in vals:
            old_state = {
                tmpl.id: (tmpl.standard_price or 0.0, tmpl.cout_divers or 0.0)
                for tmpl in self
            }

        if 'type' not in vals and 'detailed_type' not in vals:
            res = super().write(vals)
            if recalc_cout:
                self._recalc_standard_price(old_state)
            if track_history:
                # Si recalc_cout a tourné, les matières premières ont déjà
                # leur entrée d'historique créée par _recalc_standard_price :
                # on les exclut pour éviter un double log.
                to_log = self
                if recalc_cout:
                    to_log = self.filtered(lambda r: r.classification_produit != 'matiere_premiere')
                to_log._log_manual_cost_history(old_costs)
            return res

        # Extraire les changements de type pour bypasser les restrictions stock
        type_change = {}
        if 'type' in vals:
            type_change['type'] = vals.pop('type')
        if 'detailed_type' in vals:
            type_change['detailed_type'] = vals.pop('detailed_type')

        # Ecrire les autres champs normalement
        res = super().write(vals) if vals else True

        # Calculer type/detailed_type cohérents
        if 'detailed_type' in type_change and 'type' not in type_change:
            mapping = self._detailed_type_mapping()
            type_change['type'] = mapping.get(type_change['detailed_type'], type_change['detailed_type'])
        elif 'type' in type_change and 'detailed_type' not in type_change:
            type_change['detailed_type'] = type_change['type']

        # Ecriture directe pour éviter les vérifications du module stock
        self.env.cr.execute(
            "UPDATE product_template SET type=%(type)s, detailed_type=%(detailed_type)s, "
            "write_date=(NOW() AT TIME ZONE 'UTC'), write_uid=%(uid)s "
            "WHERE id IN %(ids)s",
            {
                'type': type_change['type'],
                'detailed_type': type_change['detailed_type'],
                'uid': self.env.uid,
                'ids': tuple(self.ids),
            }
        )
        self.invalidate_recordset(['type', 'detailed_type'])

        if recalc_cout:
            self._recalc_standard_price(old_state)

        if track_history:
            to_log = self
            if recalc_cout:
                to_log = self.filtered(lambda r: r.classification_produit != 'matiere_premiere')
            to_log._log_manual_cost_history(old_costs)

        return res

    def _log_manual_cost_history(self, old_costs):
        """Crée une entrée d'historique pour chaque template dont le coût
        a réellement changé (modification manuelle, sans bon d'achat)."""
        history_obj = self.env['product.cost.history'].sudo()
        for tmpl in self:
            old = old_costs.get(tmpl.id, 0.0)
            new = tmpl.standard_price
            if abs((new or 0.0) - (old or 0.0)) < 0.0001:
                continue
            history_obj.create({
                'product_tmpl_id': tmpl.id,
                'ancien_cout': old,
                'difference': new - old,
                'nouveau_cout': new,
                'source': 'manual',
                'note': 'Modification manuelle',
            })

    def _recalc_standard_price(self, old_state=None):
        """Recalcule le Coût pour les matières premières.

        - Si cout_divers vient d'être modifié, on applique la formule
          incrémentale : nouveau_cout = (ancien_cout - ancien_cout_divers) + nouveau_cout_divers.
          Cela garantit que le coût se met à jour correctement même si
          prix_achat n'est pas synchronisé (ancien produit, valeur initiale, etc.).
        - Sinon (cas prix_achat changé), on applique
          standard_price = prix_achat + cout_divers.
        - On synchronise prix_achat = standard_price - cout_divers pour
          garder l'invariant à jour pour les prochaines opérations.
        - Si le Coût a réellement changé suite à une modification manuelle
          (prix_achat ou cout_divers édités sur la fiche), on logue une
          entrée d'historique. Le contexte 'beton_purchase_history' évite
          le double-log quand la mise à jour vient d'une confirmation de PO
          (l'historique est déjà créé côté purchase.order avec le fournisseur).
        """
        old_state = old_state or {}
        history_obj = self.env['product.cost.history'].sudo()
        skip_manual_log = self.env.context.get('beton_purchase_history')
        for rec in self:
            if rec.classification_produit != 'matiere_premiere':
                continue
            if rec.id in old_state:
                ancien_cout, ancien_cout_divers = old_state[rec.id]
                nouveau_cout = ancien_cout - ancien_cout_divers + (rec.cout_divers or 0.0)
            else:
                ancien_cout = rec.standard_price or 0.0
                nouveau_cout = (rec.prix_achat or 0.0) + (rec.cout_divers or 0.0)
            rec.with_context(skip_cost_history=True, skip_recalc_cout=True).standard_price = nouveau_cout
            rec.with_context(skip_cost_history=True, skip_recalc_cout=True).prix_achat = nouveau_cout - (rec.cout_divers or 0.0)
            if not skip_manual_log and abs(nouveau_cout - ancien_cout) >= 0.0001:
                history_obj.create({
                    'product_tmpl_id': rec.id,
                    'ancien_cout': ancien_cout,
                    'difference': nouveau_cout - ancien_cout,
                    'nouveau_cout': nouveau_cout,
                    'source': 'manual',
                    'note': 'Modification manuelle (prix d\'achat ou coût divers)',
                })

    classification_produit = fields.Selection([
        ('matiere_premiere', 'Matière première'),
    ], string="Classification produit")
    type_matiere = fields.Selection([
        ('ciment', 'Ciment'),
        ('sable', 'Sable'),
        ('gravier', 'Gravier'),
        ('adjuvant', 'Adjuvant'),
        ('eau', 'Eau'),
        ('autre', 'Autre'),
    ], string="Type de matière")
    emplacement_beton = fields.Selection([
        ('silo', 'Silo'),
        ('tremie', 'Trémie'),
        ('depot', 'Dépôt'),
        ('cuve', 'Cuve'),
    ], string="Emplacement")
    delai_approvisionnement = fields.Integer(string="Délai d'approvisionnement (jours)")
    qty_minimum = fields.Float(string="Quantité minimum", default=0.0)
    statut_matiere = fields.Selection([
        ('actif', 'Actif'),
        ('indisponible', 'Indisponible'),
        ('archive', 'Archivé'),
    ], string="Statut matière", default='actif')

    prix_achat = fields.Float(
        string="Prix d'achat",
        digits='Product Price',
    )
    cout_divers = fields.Float(
        string="Coût divers",
        digits='Product Price',
    )

    @api.onchange('cout_divers')
    def _onchange_cout_divers(self):
        """Au changement de cout_divers, recalcule incrémentalement le Coût :
        nouveau_cout = (ancien_cout - ancien_cout_divers) + nouveau_cout_divers."""
        if self.classification_produit != 'matiere_premiere':
            return
        ancien_cout = self._origin.standard_price or 0.0
        ancien_cout_divers = self._origin.cout_divers or 0.0
        self.standard_price = ancien_cout - ancien_cout_divers + (self.cout_divers or 0.0)

    @api.onchange('prix_achat')
    def _onchange_prix_achat(self):
        if self.classification_produit == 'matiere_premiere':
            self.standard_price = (self.prix_achat or 0.0) + (self.cout_divers or 0.0)

    cost_history_ids = fields.One2many(
        'product.cost.history', 'product_tmpl_id',
        string="Historique des coûts",
    )
    cost_history_count = fields.Integer(
        string="Nb modifications", compute='_compute_cost_history_count',
    )

    @api.depends('cost_history_ids')
    def _compute_cost_history_count(self):
        for rec in self:
            rec.cost_history_count = len(rec.cost_history_ids)

    def _format_qty(self, value):
        """Formate un nombre : sans décimales si entier, sinon 2 décimales,
        avec séparateur de milliers (espace)."""
        if value == math.floor(value):
            return '{:,.0f}'.format(value).replace(',', ' ')
        return '{:,.2f}'.format(value).replace(',', ' ')

    def _build_qty_minimum_alert(self, qty_available):
        """Construit le corps HTML de l'alerte stock minimum."""
        self.ensure_one()
        uom = self.uom_id.name or ''
        return Markup(
            '<div style="padding:12px 16px; border-left:4px solid #e74c3c; '
            'background:#fdf2f2; border-radius:4px; margin:4px 0;">'
            '<div style="font-size:14px; font-weight:bold; color:#c0392b; '
            'margin-bottom:8px;">'
            '&#9888; Alerte Stock Minimum'
            '</div>'
            '<table style="width:100%%; border-collapse:collapse; font-size:13px;">'
            '<tr>'
            '<td style="padding:4px 8px; color:#555;">Produit</td>'
            '<td style="padding:4px 8px; font-weight:bold;">%s</td>'
            '</tr>'
            '<tr style="background:#fff;">'
            '<td style="padding:4px 8px; color:#555;">Stock actuel</td>'
            '<td style="padding:4px 8px; font-weight:bold; color:#e74c3c;">'
            '%s %s</td>'
            '</tr>'
            '<tr>'
            '<td style="padding:4px 8px; color:#555;">Seuil minimum</td>'
            '<td style="padding:4px 8px; font-weight:bold;">%s %s</td>'
            '</tr>'
            '</table>'
            '</div>'
        ) % (
            self.name,
            self._format_qty(qty_available), uom,
            self._format_qty(self.qty_minimum), uom,
        )

    @api.model
    def _cron_check_qty_minimum(self):
        """Cron : vérifie toutes les matières premières dont le stock est
        inférieur ou égal à la quantité minimum et poste une alerte
        sur le canal Discuss 'Quantité Minimum'."""
        channel = self.env.ref('beton_base.channel_qty_minimum', raise_if_not_found=False)
        if not channel:
            _logger.warning("Canal 'Quantité Minimum' introuvable (beton_base.channel_qty_minimum).")
            return
        # S'assurer que les groupes Responsable et Technique sont abonnés au canal
        groups = self.env['res.groups']
        for xid in ('beton_base.group_beton_responsable', 'base.group_system'):
            grp = self.env.ref(xid, raise_if_not_found=False)
            if grp:
                groups |= grp
        missing = groups - channel.sudo().group_ids
        if missing:
            channel.sudo().write({'group_ids': [(4, g.id) for g in missing]})
        templates = self.search([
            ('classification_produit', '=', 'matiere_premiere'),
            ('qty_minimum', '>', 0),
        ])
        _logger.info("Vérification qty minimum : %d matière(s) première(s) à vérifier.", len(templates))
        for tmpl in templates:
            qty_available = sum(tmpl.product_variant_ids.mapped('qty_available'))
            _logger.info(
                "Produit '%s' : stock=%.2f, minimum=%.2f",
                tmpl.name, qty_available, tmpl.qty_minimum,
            )
            if qty_available <= tmpl.qty_minimum:
                channel.sudo().message_post(
                    body=tmpl._build_qty_minimum_alert(qty_available),
                    message_type='comment',
                    subtype_xmlid='mail.mt_comment',
                )

