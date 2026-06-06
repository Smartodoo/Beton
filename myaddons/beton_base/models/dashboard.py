from odoo import api, fields, models, tools
from datetime import timedelta, date as date_cls
import calendar


class BetonDashboard(models.Model):
    _name = 'beton.dashboard'
    _description = 'Tableau de Bord Centrale à Béton'
    _auto = False

    name = fields.Char(string="Indicateur")

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT 1 AS id, 'dashboard' AS name
            )
        """ % self._table)

    # ===== Helpers =====
    @api.model
    def _get_target_date(self, year=None, month=None, date_str=None):
        """Retourne la date de référence pour les calculs.
        - Si date_str fournie (YYYY-MM-DD) : utilise cette date directement (prioritaire).
        - Sinon, si année/mois fournis : dernier jour de ce mois (ou today si mois courant).
        - Sinon : today.
        """
        today = fields.Date.today()
        if date_str:
            try:
                return fields.Date.from_string(date_str)
            except (TypeError, ValueError):
                pass
        if not year or not month:
            return today
        try:
            year = int(year)
            month = int(month)
        except (TypeError, ValueError):
            return today
        if year == today.year and month == today.month:
            return today
        last_day = calendar.monthrange(year, month)[1]
        return date_cls(year, month, last_day)


    @api.model
    def _get_period(self, date=None):
        """Retourne le début du mois et la date de fin (date passée ou today)."""
        if not date:
            date = fields.Date.today()
        debut_mois = date.replace(day=1)
        return debut_mois, date

    @api.model
    def _get_previous_period(self, date=None):
        """Retourne le début et fin du mois précédent (même nb de jours)."""
        if not date:
            date = fields.Date.today()
        debut_mois = date.replace(day=1)
        fin_mois_prec = debut_mois - timedelta(days=1)
        jour = min(date.day, fin_mois_prec.day)
        date_prec = fin_mois_prec.replace(day=jour)
        debut_mois_prec = fin_mois_prec.replace(day=1)
        return debut_mois_prec, date_prec

    @api.model
    def _compute_trend(self, current, previous):
        """Calcule la tendance en % entre deux valeurs."""
        if not previous:
            return 0
        return round(((current - previous) / previous) * 100, 1)

    # ===== Production =====
    @api.model
    def get_production_journaliere(self, date=None):
        if not date:
            date = fields.Date.today()
        fabrications = self.env['mrp.production'].search([
            ('date_start', '>=', str(date) + ' 00:00:00'),
            ('date_start', '<=', str(date) + ' 23:59:59'),
            ('state', 'in', ('progress', 'done')),
        ])
        return sum(fabrications.mapped('qty_produced'))

    @api.model
    def get_production_mensuelle(self, date=None):
        debut_mois, date = self._get_period(date)
        fabrications = self.env['mrp.production'].search([
            ('date_start', '>=', str(debut_mois) + ' 00:00:00'),
            ('date_start', '<=', str(date) + ' 23:59:59'),
            ('state', 'in', ('progress', 'done')),
        ])
        return sum(fabrications.mapped('qty_produced'))

    @api.model
    def get_production_mensuelle_precedente(self, date=None):
        debut, fin = self._get_previous_period(date)
        fabrications = self.env['mrp.production'].search([
            ('date_start', '>=', str(debut) + ' 00:00:00'),
            ('date_start', '<=', str(fin) + ' 23:59:59'),
            ('state', 'in', ('progress', 'done')),
        ])
        return sum(fabrications.mapped('qty_produced'))

    @api.model
    def get_taux_pertes(self, date=None):
        debut_mois, date = self._get_period(date)
        fabrications = self.env['mrp.production'].search([
            ('date_start', '>=', str(debut_mois) + ' 00:00:00'),
            ('date_start', '<=', str(date) + ' 23:59:59'),
            ('state', '=', 'done'),
        ])
        total_produit = sum(fabrications.mapped('qty_produced'))
        total_ecart = sum(abs(f.ecart_production) for f in fabrications if f.ecart_production < 0)
        if total_produit:
            return round((total_ecart / total_produit) * 100, 2)
        return 0.0

    @api.model
    def get_fabrications_count(self, date=None):
        """Nombre total d'ordres de fabrication du mois."""
        debut_mois, date = self._get_period(date)
        return self.env['mrp.production'].search_count([
            ('date_start', '>=', str(debut_mois) + ' 00:00:00'),
            ('date_start', '<=', str(date) + ' 23:59:59'),
            ('state', 'in', ('progress', 'done')),
        ])

    # ===== Logistique =====
    @api.model
    def get_livraisons_jour(self, date=None):
        if not date:
            date = fields.Date.today()
        return self.env['stock.picking'].search_count([
            ('scheduled_date', '>=', str(date) + ' 00:00:00'),
            ('scheduled_date', '<=', str(date) + ' 23:59:59'),
            ('picking_type_code', '=', 'outgoing'),
            ('state', '!=', 'cancel'),
        ])

    @api.model
    def get_volume_livre_mois(self, date=None):
        debut_mois, date = self._get_period(date)
        pickings = self.env['stock.picking'].search([
            ('scheduled_date', '>=', str(debut_mois) + ' 00:00:00'),
            ('scheduled_date', '<=', str(date) + ' 23:59:59'),
            ('picking_type_code', '=', 'outgoing'),
            ('state', '=', 'done'),
        ])
        total = 0.0
        for p in pickings:
            total += sum(p.move_ids.mapped('quantity'))
        return total

    @api.model
    def get_volume_livre_mois_precedent(self, date=None):
        debut, fin = self._get_previous_period(date)
        pickings = self.env['stock.picking'].search([
            ('scheduled_date', '>=', str(debut) + ' 00:00:00'),
            ('scheduled_date', '<=', str(fin) + ' 23:59:59'),
            ('picking_type_code', '=', 'outgoing'),
            ('state', '=', 'done'),
        ])
        total = 0.0
        for p in pickings:
            total += sum(p.move_ids.mapped('quantity'))
        return total

    # ===== Qualité =====
    @api.model
    def get_taux_non_conformite(self, date=None):
        debut_mois, date = self._get_period(date)
        total_essais = self.env['beton.essai'].search_count([
            ('date', '>=', debut_mois),
            ('date', '<=', date),
        ])
        essais_nc = self.env['beton.essai'].search_count([
            ('date', '>=', debut_mois),
            ('date', '<=', date),
            ('conforme', '=', 'non'),
        ])
        if total_essais:
            return round((essais_nc / total_essais) * 100, 2)
        return 0.0

    @api.model
    def get_nc_non_traitees(self):
        return self.env['beton.non.conformite'].search_count([
            ('traitement', '=', 'non'),
        ])

    @api.model
    def get_total_essais_mois(self, date=None):
        debut_mois, date = self._get_period(date)
        return self.env['beton.essai'].search_count([
            ('date', '>=', debut_mois),
            ('date', '<=', date),
        ])

    # ===== Centrales =====
    @api.model
    def get_disponibilite_centrales(self):
        total = self.env['beton.centrale'].search_count([])
        operationnelles = self.env['beton.centrale'].search_count([
            ('etat', '=', 'operationnelle'),
        ])
        if total:
            return round((operationnelles / total) * 100, 2)
        return 0.0

    @api.model
    def get_centrales_stats(self):
        """Détail par centrale."""
        total = self.env['beton.centrale'].search_count([])
        operationnelles = self.env['beton.centrale'].search_count([('etat', '=', 'operationnelle')])
        return {
            'total': total,
            'operationnelles': operationnelles,
            'en_panne': total - operationnelles,
        }

    @api.model
    def get_capacite_production_journaliere(self):
        """Somme des capacités journalières des centrales opérationnelles."""
        centrales = self.env['beton.centrale'].search([('etat', '=', 'operationnelle')])
        return sum(centrales.mapped('capacite_journaliere'))

    @api.model
    def get_taux_production_jour(self, date=None):
        """Taux d'utilisation = production_jour / capacité_totale_journalière * 100.
        Garde l'ancien indicateur basé sur la capacité des centrales."""
        capacite = self.get_capacite_production_journaliere()
        if not capacite:
            return 0.0
        production = self.get_production_journaliere(date)
        return round((production / capacite) * 100, 1)

    # ---- Nouveaux KPIs basés sur les ordres de fabrication ----

    @api.model
    def _get_period_mo(self, date=None):
        """Recordset des MO progress/done sur la période (mois courant -> date)."""
        debut_mois, date = self._get_period(date)
        return self.env['mrp.production'].search([
            ('date_start', '>=', str(debut_mois) + ' 00:00:00'),
            ('date_start', '<=', str(date) + ' 23:59:59'),
            ('state', 'in', ('progress', 'done')),
        ])

    @api.model
    def get_taux_production_global(self, date=None):
        """Taux GLOBAL pondéré sur la période :
        Σ qty_produced / Σ product_qty × 100.
        Utilise product_qty (quantité planifiée, même UdM que qty_produced)
        car le champ objectif peut contenir des valeurs incohérentes
        (capacité journalière centrale au lieu d'objectif par ordre)."""
        mos = self._get_period_mo(date)
        total_obj = 0.0
        total_prod = 0.0
        for mo in mos:
            total_obj += mo.product_qty or 0.0
            total_prod += mo.qty_produced
        if not total_obj:
            return 0.0
        return round((total_prod / total_obj) * 100, 1)

    @api.model
    def get_taux_production_moyen(self, date=None):
        """Taux MOYEN sur les ordres de la période :
        moyenne arithmétique des taux par ordre.
        Utilise product_qty comme dénominateur pour cohérence avec le taux global."""
        mos = self._get_period_mo(date)
        if not mos:
            return 0.0
        rates = []
        for mo in mos:
            obj = mo.product_qty or 0.0
            if obj > 0:
                rates.append(mo.qty_produced / obj * 100.0)
        if not rates:
            return 0.0
        return round(sum(rates) / len(rates), 1)

    # ===== Maintenance =====
    @api.model
    def get_equipements_en_panne(self):
        return self.env['maintenance.equipment'].search_count([
            ('etat_equipement', '=', 'panne'),
        ])

    @api.model
    def get_interventions_en_cours(self):
        return self.env['maintenance.request'].search_count([
            ('stage_id.done', '=', False),
            ('close_date', '=', False),
        ])

    # ===== Commercial =====
    @api.model
    def get_chantiers_actifs(self):
        return self.env['beton.chantier'].search_count([
            ('statut', '=', 'en_cours'),
        ])

    @api.model
    def get_clients_actifs(self):
        return self.env['res.partner'].search_count([
            ('is_client_beton', '=', True),
        ])

    # ===== Consommation =====
    @api.model
    def get_consommation_matieres_m3(self, date=None):
        debut_mois, date = self._get_period(date)
        fabrications = self.env['mrp.production'].search([
            ('date_start', '>=', str(debut_mois) + ' 00:00:00'),
            ('date_start', '<=', str(date) + ' 23:59:59'),
            ('state', '=', 'done'),
        ])
        total_produit = sum(fabrications.mapped('qty_produced'))
        total_consomme = 0.0
        for fab in fabrications:
            total_consomme += sum(fab.move_raw_ids.filtered(
                lambda m: m.state == 'done'
            ).mapped('quantity'))
        if total_produit:
            return round(total_consomme / total_produit, 2)
        return 0.0

    @api.model
    def get_marge_par_chantier(self):
        couts = self.env['beton.cout.revient'].search([])
        if couts:
            marges = [c.marge_brute for c in couts if c.marge_brute]
            if marges:
                return round(sum(marges) / len(marges), 2)
        return 0.0

    # ===== Finance =====
    @api.model
    def get_chiffre_affaires_mois(self, date=None):
        debut_mois, date = self._get_period(date)
        factures = self.env['account.move'].search([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('invoice_date', '>=', debut_mois),
            ('invoice_date', '<=', date),
        ])
        return sum(factures.mapped('amount_total'))

    @api.model
    def get_chiffre_affaires_mois_precedent(self, date=None):
        debut, fin = self._get_previous_period(date)
        factures = self.env['account.move'].search([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('invoice_date', '>=', debut),
            ('invoice_date', '<=', fin),
        ])
        return sum(factures.mapped('amount_total'))

    @api.model
    def get_factures_impayees(self):
        """Montant total des factures impayées."""
        factures = self.env['account.move'].search([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', 'in', ('not_paid', 'partial')),
        ])
        return sum(factures.mapped('amount_residual'))

    # ===== Top Chantiers =====
    @api.model
    def get_top_chantiers(self, date=None, limit=5):
        """Top chantiers par volume produit ce mois."""
        debut_mois, date = self._get_period(date)
        fabrications = self.env['mrp.production'].search([
            ('date_start', '>=', str(debut_mois) + ' 00:00:00'),
            ('date_start', '<=', str(date) + ' 23:59:59'),
            ('state', 'in', ('progress', 'done')),
            ('chantier', '!=', False),
        ])
        chantier_volumes = {}
        for fab in fabrications:
            chantier = fab.chantier or 'Non défini'
            chantier_volumes[chantier] = chantier_volumes.get(chantier, 0) + fab.qty_produced
        sorted_chantiers = sorted(chantier_volumes.items(), key=lambda x: x[1], reverse=True)[:limit]
        return [{'name': c[0], 'volume': round(c[1], 1)} for c in sorted_chantiers]

    # ===== Top Clients =====
    @api.model
    def get_top_clients(self, date=None, limit=5):
        """Top clients par volume produit ce mois."""
        debut_mois, date = self._get_period(date)
        fabrications = self.env['mrp.production'].search([
            ('date_start', '>=', str(debut_mois) + ' 00:00:00'),
            ('date_start', '<=', str(date) + ' 23:59:59'),
            ('state', 'in', ('progress', 'done')),
            ('client_id', '!=', False),
        ])
        client_volumes = {}
        for fab in fabrications:
            client_name = fab.client_id.name
            client_volumes[client_name] = client_volumes.get(client_name, 0) + fab.qty_produced
        sorted_clients = sorted(client_volumes.items(), key=lambda x: x[1], reverse=True)[:limit]
        return [{'name': c[0], 'volume': round(c[1], 1)} for c in sorted_clients]

    # ===== Fabrications récentes =====
    @api.model
    def get_fabrications_recentes(self, date=None, limit=7):
        """Dernières fabrications du mois sélectionné (ou today)."""
        debut_mois, date = self._get_period(date)
        fabrications = self.env['mrp.production'].search([
            ('state', 'in', ('progress', 'done', 'to_close')),
            ('date_start', '>=', str(debut_mois) + ' 00:00:00'),
            ('date_start', '<=', str(date) + ' 23:59:59'),
        ], order='date_start desc', limit=limit)
        result = []
        for fab in fabrications:
            result.append({
                'id': fab.id,
                'name': fab.name,
                'product': fab.product_id.name if fab.product_id else '',
                'qty': round(fab.qty_produced, 1),
                'date': str(fab.date_start.date()) if fab.date_start else '',
                'client': fab.client_id.name if fab.client_id else '',
                'state': fab.state,
                'state_label': dict(fab._fields['state'].selection).get(fab.state, fab.state),
            })
        return result

    # ===== Données Graphiques =====
    @api.model
    def get_chart_production_journaliere(self, date=None):
        """Production par jour du mois en cours (pour graphique barres)."""
        debut_mois, date = self._get_period(date)
        fabrications = self.env['mrp.production'].search([
            ('date_start', '>=', str(debut_mois) + ' 00:00:00'),
            ('date_start', '<=', str(date) + ' 23:59:59'),
            ('state', 'in', ('progress', 'done')),
        ])
        # Agréger par jour
        daily = {}
        for fab in fabrications:
            if fab.date_start:
                jour = fab.date_start.strftime('%d/%m')
                daily[jour] = daily.get(jour, 0) + fab.qty_produced
        # Remplir les jours manquants
        labels = []
        values = []
        current = debut_mois
        while current <= date:
            jour_str = current.strftime('%d/%m')
            labels.append(jour_str)
            values.append(round(daily.get(jour_str, 0), 1))
            current += timedelta(days=1)
        return {'labels': labels, 'values': values}

    @api.model
    def get_chart_production_par_produit(self, date=None):
        """Répartition de la production par produit (pour graphique camembert)."""
        debut_mois, date = self._get_period(date)
        fabrications = self.env['mrp.production'].search([
            ('date_start', '>=', str(debut_mois) + ' 00:00:00'),
            ('date_start', '<=', str(date) + ' 23:59:59'),
            ('state', 'in', ('progress', 'done')),
        ])
        produit_volumes = {}
        for fab in fabrications:
            produit = fab.product_id.name if fab.product_id else 'Autre'
            produit_volumes[produit] = produit_volumes.get(produit, 0) + fab.qty_produced
        sorted_produits = sorted(produit_volumes.items(), key=lambda x: x[1], reverse=True)[:8]
        return {
            'labels': [p[0] for p in sorted_produits],
            'values': [round(p[1], 1) for p in sorted_produits],
        }

    @api.model
    def get_chart_ca_mensuel(self, date=None):
        """CA des 6 derniers mois ENDING au mois de la date passée (ou today)."""
        today = date or fields.Date.today()
        labels = []
        values = []
        mois_names = ['Jan', 'Fev', 'Mar', 'Avr', 'Mai', 'Juin',
                      'Juil', 'Aout', 'Sep', 'Oct', 'Nov', 'Dec']
        for i in range(5, -1, -1):
            # Reculer de i mois
            mois = today.month - i
            annee = today.year
            while mois <= 0:
                mois += 12
                annee -= 1
            debut = today.replace(year=annee, month=mois, day=1)
            # Fin du mois
            if mois == 12:
                fin = today.replace(year=annee + 1, month=1, day=1) - timedelta(days=1)
            else:
                fin = today.replace(year=annee, month=mois + 1, day=1) - timedelta(days=1)
            # Pour le mois "courant" du contexte, borner à la date passée
            if i == 0:
                fin = today
            factures = self.env['account.move'].search([
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted'),
                ('invoice_date', '>=', debut),
                ('invoice_date', '<=', fin),
            ])
            labels.append(mois_names[mois - 1])
            values.append(round(sum(factures.mapped('amount_total')), 2))
        return {'labels': labels, 'values': values}

    @api.model
    def get_chart_livraisons_semaine(self, date=None):
        """Livraisons des 7 derniers jours ending à la date passée (ou today)."""
        today = date or fields.Date.today()
        labels = []
        values = []
        jours = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']
        for i in range(6, -1, -1):
            jour = today - timedelta(days=i)
            count = self.env['stock.picking'].search_count([
                ('scheduled_date', '>=', str(jour) + ' 00:00:00'),
                ('scheduled_date', '<=', str(jour) + ' 23:59:59'),
                ('picking_type_code', '=', 'outgoing'),
                ('state', '!=', 'cancel'),
            ])
            labels.append(jours[jour.weekday()] + ' ' + jour.strftime('%d'))
            values.append(count)
        return {'labels': labels, 'values': values}

    # ===== Achats =====
    @api.model
    def _get_period_purchases(self, date=None, states=('purchase', 'done')):
        """Retourne le recordset des bons d'achat confirmés sur la période (mois courant -> date)."""
        debut_mois, date = self._get_period(date)
        return self.env['purchase.order'].search([
            ('date_order', '>=', str(debut_mois) + ' 00:00:00'),
            ('date_order', '<=', str(date) + ' 23:59:59'),
            ('state', 'in', list(states)),
        ])

    @api.model
    def get_achats_mois(self, date=None):
        """Montant total des achats confirmés du mois."""
        orders = self._get_period_purchases(date)
        return sum(orders.mapped('amount_total'))

    @api.model
    def get_achats_mois_precedent(self, date=None):
        debut, fin = self._get_previous_period(date)
        orders = self.env['purchase.order'].search([
            ('date_order', '>=', str(debut) + ' 00:00:00'),
            ('date_order', '<=', str(fin) + ' 23:59:59'),
            ('state', 'in', ('purchase', 'done')),
        ])
        return sum(orders.mapped('amount_total'))

    @api.model
    def get_achats_count(self, date=None):
        """Nombre de bons d'achat confirmés du mois."""
        return len(self._get_period_purchases(date))

    @api.model
    def get_achats_count_precedent(self, date=None):
        debut, fin = self._get_previous_period(date)
        return self.env['purchase.order'].search_count([
            ('date_order', '>=', str(debut) + ' 00:00:00'),
            ('date_order', '<=', str(fin) + ' 23:59:59'),
            ('state', 'in', ('purchase', 'done')),
        ])

    @api.model
    def get_achats_draft_count(self):
        """Demandes de prix / brouillons en cours (toutes périodes)."""
        return self.env['purchase.order'].search_count([
            ('state', 'in', ('draft', 'sent', 'to approve')),
        ])

    @api.model
    def get_achats_a_facturer(self):
        """Achats confirmés à facturer (invoice_status='to invoice')."""
        return self.env['purchase.order'].search_count([
            ('state', 'in', ('purchase', 'done')),
            ('invoice_status', '=', 'to invoice'),
        ])

    @api.model
    def get_achats_a_recevoir(self):
        """Achats confirmés non encore totalement réceptionnés."""
        orders = self.env['purchase.order'].search([
            ('state', '=', 'purchase'),
        ])
        count = 0
        for po in orders:
            pickings = po.picking_ids.filtered(lambda p: p.state not in ('done', 'cancel'))
            if pickings:
                count += 1
        return count

    @api.model
    def get_panier_moyen_achat(self, date=None):
        """Montant moyen par bon d'achat (mois courant)."""
        orders = self._get_period_purchases(date)
        if not orders:
            return 0.0
        return round(sum(orders.mapped('amount_total')) / len(orders), 2)

    @api.model
    def get_top_fournisseurs(self, date=None, limit=5):
        """Top fournisseurs par montant d'achat du mois."""
        orders = self._get_period_purchases(date)
        totals = {}
        for po in orders:
            name = po.partner_id.name or 'N/D'
            totals[name] = totals.get(name, 0.0) + po.amount_total
        sorted_items = sorted(totals.items(), key=lambda x: x[1], reverse=True)[:limit]
        return [{'name': it[0], 'amount': round(it[1], 2)} for it in sorted_items]

    @api.model
    def get_top_produits_achetes(self, date=None, limit=5):
        """Top produits achetés par montant (mois courant)."""
        orders = self._get_period_purchases(date)
        totals = {}
        qties = {}
        for po in orders:
            for line in po.order_line:
                if not line.product_id:
                    continue
                name = line.product_id.display_name
                totals[name] = totals.get(name, 0.0) + line.price_subtotal
                qties[name] = qties.get(name, 0.0) + line.product_qty
        sorted_items = sorted(totals.items(), key=lambda x: x[1], reverse=True)[:limit]
        return [{
            'name': it[0],
            'amount': round(it[1], 2),
            'qty': round(qties.get(it[0], 0.0), 2),
        } for it in sorted_items]

    @api.model
    def get_chart_achats_par_etat(self, date=None):
        """Répartition des bons d'achat par état (mois courant)."""
        debut_mois, date = self._get_period(date)
        states = ['draft', 'sent', 'to approve', 'purchase', 'done', 'cancel']
        labels_map = {
            'draft': 'Brouillon',
            'sent': 'Envoyé',
            'to approve': 'À approuver',
            'purchase': 'Confirmé',
            'done': 'Verrouillé',
            'cancel': 'Annulé',
        }
        labels = []
        values = []
        for st in states:
            cnt = self.env['purchase.order'].search_count([
                ('date_order', '>=', str(debut_mois) + ' 00:00:00'),
                ('date_order', '<=', str(date) + ' 23:59:59'),
                ('state', '=', st),
            ])
            if cnt:
                labels.append(labels_map[st])
                values.append(cnt)
        return {'labels': labels, 'values': values}

    @api.model
    def get_chart_achats_mensuels(self, date=None):
        """Montant des achats sur les 6 derniers mois."""
        today = date or fields.Date.today()
        labels = []
        values = []
        mois_names = ['Jan', 'Fev', 'Mar', 'Avr', 'Mai', 'Juin',
                      'Juil', 'Aout', 'Sep', 'Oct', 'Nov', 'Dec']
        for i in range(5, -1, -1):
            mois = today.month - i
            annee = today.year
            while mois <= 0:
                mois += 12
                annee -= 1
            debut = today.replace(year=annee, month=mois, day=1)
            if mois == 12:
                fin = today.replace(year=annee + 1, month=1, day=1) - timedelta(days=1)
            else:
                fin = today.replace(year=annee, month=mois + 1, day=1) - timedelta(days=1)
            if i == 0:
                fin = today
            orders = self.env['purchase.order'].search([
                ('date_order', '>=', str(debut) + ' 00:00:00'),
                ('date_order', '<=', str(fin) + ' 23:59:59'),
                ('state', 'in', ('purchase', 'done')),
            ])
            labels.append(mois_names[mois - 1])
            values.append(round(sum(orders.mapped('amount_total')), 2))
        return {'labels': labels, 'values': values}

    @api.model
    def get_achats_recents(self, date=None, limit=7):
        """Derniers bons d'achat du mois sélectionné."""
        debut_mois, date = self._get_period(date)
        orders = self.env['purchase.order'].search([
            ('date_order', '>=', str(debut_mois) + ' 00:00:00'),
            ('date_order', '<=', str(date) + ' 23:59:59'),
            ('state', 'in', ('purchase', 'done', 'sent', 'to approve')),
        ], order='date_order desc', limit=limit)
        result = []
        for po in orders:
            result.append({
                'id': po.id,
                'name': po.name,
                'partner': po.partner_id.name if po.partner_id else '',
                'amount': round(po.amount_total, 2),
                'date': str(po.date_order.date()) if po.date_order else '',
                'state': po.state,
                'state_label': dict(po._fields['state'].selection).get(po.state, po.state),
            })
        return result

    # ===== Ventes =====
    @api.model
    def _get_period_sales(self, date=None, states=('sale', 'done')):
        """Retourne le recordset des ventes confirmées sur la période (mois courant -> date)."""
        debut_mois, date = self._get_period(date)
        return self.env['sale.order'].search([
            ('date_order', '>=', str(debut_mois) + ' 00:00:00'),
            ('date_order', '<=', str(date) + ' 23:59:59'),
            ('state', 'in', list(states)),
        ])

    @api.model
    def get_ventes_mois(self, date=None):
        orders = self._get_period_sales(date)
        return sum(orders.mapped('amount_total'))

    @api.model
    def get_ventes_mois_precedent(self, date=None):
        debut, fin = self._get_previous_period(date)
        orders = self.env['sale.order'].search([
            ('date_order', '>=', str(debut) + ' 00:00:00'),
            ('date_order', '<=', str(fin) + ' 23:59:59'),
            ('state', 'in', ('sale', 'done')),
        ])
        return sum(orders.mapped('amount_total'))

    @api.model
    def get_ventes_count(self, date=None):
        return len(self._get_period_sales(date))

    @api.model
    def get_ventes_count_precedent(self, date=None):
        debut, fin = self._get_previous_period(date)
        return self.env['sale.order'].search_count([
            ('date_order', '>=', str(debut) + ' 00:00:00'),
            ('date_order', '<=', str(fin) + ' 23:59:59'),
            ('state', 'in', ('sale', 'done')),
        ])

    @api.model
    def get_devis_en_cours(self):
        """Devis ouverts (draft/sent)."""
        return self.env['sale.order'].search_count([
            ('state', 'in', ('draft', 'sent')),
        ])

    @api.model
    def get_ventes_a_facturer(self):
        """Ventes confirmées à facturer."""
        return self.env['sale.order'].search_count([
            ('state', 'in', ('sale', 'done')),
            ('invoice_status', '=', 'to invoice'),
        ])

    @api.model
    def get_ventes_a_livrer(self):
        """Ventes confirmées non encore totalement livrées."""
        orders = self.env['sale.order'].search([
            ('state', '=', 'sale'),
        ])
        count = 0
        for so in orders:
            pickings = so.picking_ids.filtered(lambda p: p.state not in ('done', 'cancel'))
            if pickings:
                count += 1
        return count

    @api.model
    def get_panier_moyen_vente(self, date=None):
        orders = self._get_period_sales(date)
        if not orders:
            return 0.0
        return round(sum(orders.mapped('amount_total')) / len(orders), 2)

    @api.model
    def get_taux_conversion_devis(self, date=None):
        """Taux de conversion = ventes confirmées / total devis créés ce mois."""
        debut_mois, date = self._get_period(date)
        total = self.env['sale.order'].search_count([
            ('date_order', '>=', str(debut_mois) + ' 00:00:00'),
            ('date_order', '<=', str(date) + ' 23:59:59'),
            ('state', '!=', 'cancel'),
        ])
        confirmes = self.env['sale.order'].search_count([
            ('date_order', '>=', str(debut_mois) + ' 00:00:00'),
            ('date_order', '<=', str(date) + ' 23:59:59'),
            ('state', 'in', ('sale', 'done')),
        ])
        if not total:
            return 0.0
        return round((confirmes / total) * 100, 1)

    @api.model
    def get_top_clients_vente(self, date=None, limit=5):
        """Top clients par CA confirmé du mois."""
        orders = self._get_period_sales(date)
        totals = {}
        for so in orders:
            name = so.partner_id.name or 'N/D'
            totals[name] = totals.get(name, 0.0) + so.amount_total
        sorted_items = sorted(totals.items(), key=lambda x: x[1], reverse=True)[:limit]
        return [{'name': it[0], 'amount': round(it[1], 2)} for it in sorted_items]

    @api.model
    def get_top_produits_vendus(self, date=None, limit=5):
        """Top produits vendus par montant du mois."""
        orders = self._get_period_sales(date)
        totals = {}
        qties = {}
        for so in orders:
            for line in so.order_line:
                if not line.product_id:
                    continue
                name = line.product_id.display_name
                totals[name] = totals.get(name, 0.0) + line.price_subtotal
                qties[name] = qties.get(name, 0.0) + line.product_uom_qty
        sorted_items = sorted(totals.items(), key=lambda x: x[1], reverse=True)[:limit]
        return [{
            'name': it[0],
            'amount': round(it[1], 2),
            'qty': round(qties.get(it[0], 0.0), 2),
        } for it in sorted_items]

    @api.model
    def get_chart_ventes_par_etat(self, date=None):
        """Répartition des ventes par état (mois courant)."""
        debut_mois, date = self._get_period(date)
        states = ['draft', 'sent', 'sale', 'done', 'cancel']
        labels_map = {
            'draft': 'Devis',
            'sent': 'Devis envoyé',
            'sale': 'Confirmée',
            'done': 'Verrouillée',
            'cancel': 'Annulée',
        }
        labels = []
        values = []
        for st in states:
            cnt = self.env['sale.order'].search_count([
                ('date_order', '>=', str(debut_mois) + ' 00:00:00'),
                ('date_order', '<=', str(date) + ' 23:59:59'),
                ('state', '=', st),
            ])
            if cnt:
                labels.append(labels_map[st])
                values.append(cnt)
        return {'labels': labels, 'values': values}

    @api.model
    def get_chart_ventes_mensuelles(self, date=None):
        """Montant des ventes sur les 6 derniers mois."""
        today = date or fields.Date.today()
        labels = []
        values = []
        mois_names = ['Jan', 'Fev', 'Mar', 'Avr', 'Mai', 'Juin',
                      'Juil', 'Aout', 'Sep', 'Oct', 'Nov', 'Dec']
        for i in range(5, -1, -1):
            mois = today.month - i
            annee = today.year
            while mois <= 0:
                mois += 12
                annee -= 1
            debut = today.replace(year=annee, month=mois, day=1)
            if mois == 12:
                fin = today.replace(year=annee + 1, month=1, day=1) - timedelta(days=1)
            else:
                fin = today.replace(year=annee, month=mois + 1, day=1) - timedelta(days=1)
            if i == 0:
                fin = today
            orders = self.env['sale.order'].search([
                ('date_order', '>=', str(debut) + ' 00:00:00'),
                ('date_order', '<=', str(fin) + ' 23:59:59'),
                ('state', 'in', ('sale', 'done')),
            ])
            labels.append(mois_names[mois - 1])
            values.append(round(sum(orders.mapped('amount_total')), 2))
        return {'labels': labels, 'values': values}

    @api.model
    def get_ventes_recentes(self, date=None, limit=7):
        debut_mois, date = self._get_period(date)
        orders = self.env['sale.order'].search([
            ('date_order', '>=', str(debut_mois) + ' 00:00:00'),
            ('date_order', '<=', str(date) + ' 23:59:59'),
            ('state', 'in', ('sale', 'done', 'sent', 'draft')),
        ], order='date_order desc', limit=limit)
        result = []
        for so in orders:
            result.append({
                'id': so.id,
                'name': so.name,
                'partner': so.partner_id.name if so.partner_id else '',
                'amount': round(so.amount_total, 2),
                'date': str(so.date_order.date()) if so.date_order else '',
                'state': so.state,
                'state_label': dict(so._fields['state'].selection).get(so.state, so.state),
            })
        return result

    # ===== Méthode principale =====
    @api.model
    def get_dashboard_data(self, year=None, month=None, date_str=None):
        """Retourne toutes les données du dashboard en un seul appel.
        - date_str optionnelle (YYYY-MM-DD) : pilote la période d'analyse (prioritaire).
        - year/month optionnels : utilisés si date_str non fournie.
        - Si rien : mois courant (today).
        """
        target_date = self._get_target_date(year, month, date_str)
        currency = self.env.company.currency_id

        # Valeurs de la période sélectionnée
        prod_mois = self.get_production_mensuelle(target_date)
        vol_livre = self.get_volume_livre_mois(target_date)
        ca_mois = self.get_chiffre_affaires_mois(target_date)

        # Valeurs mois précédent (pour tendances)
        prod_mois_prec = self.get_production_mensuelle_precedente(target_date)
        vol_livre_prec = self.get_volume_livre_mois_precedent(target_date)
        ca_mois_prec = self.get_chiffre_affaires_mois_precedent(target_date)

        # Achats / Ventes
        achats_mois = self.get_achats_mois(target_date)
        achats_mois_prec = self.get_achats_mois_precedent(target_date)
        achats_count = self.get_achats_count(target_date)
        achats_count_prec = self.get_achats_count_precedent(target_date)
        ventes_mois = self.get_ventes_mois(target_date)
        ventes_mois_prec = self.get_ventes_mois_precedent(target_date)
        ventes_count = self.get_ventes_count(target_date)
        ventes_count_prec = self.get_ventes_count_precedent(target_date)

        return {
            # Production
            'production_jour': self.get_production_journaliere(target_date),
            'capacite_jour': self.get_capacite_production_journaliere(),
            'taux_production_jour': self.get_taux_production_jour(target_date),
            'taux_production_global': self.get_taux_production_global(target_date),
            'taux_production_moyen': self.get_taux_production_moyen(target_date),
            'production_mois': prod_mois,
            'production_mois_trend': self._compute_trend(prod_mois, prod_mois_prec),
            'taux_pertes': self.get_taux_pertes(target_date),
            'fabrications_count': self.get_fabrications_count(target_date),
            'consommation_m3': self.get_consommation_matieres_m3(target_date),
            # Centrales (état actuel, indépendant de la période)
            'disponibilite_centrales': self.get_disponibilite_centrales(),
            'centrales_stats': self.get_centrales_stats(),
            # Logistique
            'livraisons_jour': self.get_livraisons_jour(target_date),
            'volume_livre_mois': vol_livre,
            'volume_livre_trend': self._compute_trend(vol_livre, vol_livre_prec),
            # Qualité
            'taux_nc': self.get_taux_non_conformite(target_date),
            'nc_non_traitees': self.get_nc_non_traitees(),
            'total_essais': self.get_total_essais_mois(target_date),
            # Maintenance (état actuel)
            'equipements_panne': self.get_equipements_en_panne(),
            'interventions_en_cours': self.get_interventions_en_cours(),
            # Commercial (état actuel)
            'chantiers_actifs': self.get_chantiers_actifs(),
            'clients_actifs': self.get_clients_actifs(),
            # Finance
            'ca_mois': ca_mois,
            'ca_mois_trend': self._compute_trend(ca_mois, ca_mois_prec),
            'marge_chantier': self.get_marge_par_chantier(),
            'factures_impayees': self.get_factures_impayees(),
            # Listes
            'top_chantiers': self.get_top_chantiers(target_date),
            'top_clients': self.get_top_clients(target_date),
            'fabrications_recentes': self.get_fabrications_recentes(target_date),
            # Achats
            'achats_mois': achats_mois,
            'achats_mois_trend': self._compute_trend(achats_mois, achats_mois_prec),
            'achats_count': achats_count,
            'achats_count_trend': self._compute_trend(achats_count, achats_count_prec),
            'achats_draft_count': self.get_achats_draft_count(),
            'achats_a_facturer': self.get_achats_a_facturer(),
            'achats_a_recevoir': self.get_achats_a_recevoir(),
            'panier_moyen_achat': self.get_panier_moyen_achat(target_date),
            'top_fournisseurs': self.get_top_fournisseurs(target_date),
            'top_produits_achetes': self.get_top_produits_achetes(target_date),
            'achats_recents': self.get_achats_recents(target_date),
            # Ventes
            'ventes_mois': ventes_mois,
            'ventes_mois_trend': self._compute_trend(ventes_mois, ventes_mois_prec),
            'ventes_count': ventes_count,
            'ventes_count_trend': self._compute_trend(ventes_count, ventes_count_prec),
            'devis_en_cours': self.get_devis_en_cours(),
            'ventes_a_facturer': self.get_ventes_a_facturer(),
            'ventes_a_livrer': self.get_ventes_a_livrer(),
            'panier_moyen_vente': self.get_panier_moyen_vente(target_date),
            'taux_conversion_devis': self.get_taux_conversion_devis(target_date),
            'top_clients_vente': self.get_top_clients_vente(target_date),
            'top_produits_vendus': self.get_top_produits_vendus(target_date),
            'ventes_recentes': self.get_ventes_recentes(target_date),
            # Graphiques
            'chart_production': self.get_chart_production_journaliere(target_date),
            'chart_produits': self.get_chart_production_par_produit(target_date),
            'chart_ca': self.get_chart_ca_mensuel(target_date),
            'chart_livraisons': self.get_chart_livraisons_semaine(target_date),
            'chart_achats_etat': self.get_chart_achats_par_etat(target_date),
            'chart_achats_mensuels': self.get_chart_achats_mensuels(target_date),
            'chart_ventes_etat': self.get_chart_ventes_par_etat(target_date),
            'chart_ventes_mensuelles': self.get_chart_ventes_mensuelles(target_date),
            # Meta
            'currency_symbol': currency.symbol,
            'currency_id': currency.id,
            'today': str(target_date),
            'mois_label': target_date.strftime('%B %Y').capitalize(),
            'selected_year': target_date.year,
            'selected_month': target_date.month,
        }
