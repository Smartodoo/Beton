from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # ===== Relations inverses (nécessaires pour les depends des computes stockés) =====
    beton_entry_ids = fields.One2many(
        'beton.caisse.entry', 'client_id',
        string='Encaissements béton',
    )
    beton_expense_ids = fields.One2many(
        'beton.caisse.expense', 'fournisseur',
        string='Décaissements béton',
    )
    beton_versement_ids = fields.One2many(
        'beton.versement', 'partner_id',
        string='Versements béton',
    )
    # One2many vers les bons d'achat (purchase n'expose pas cette relation
    # nativement sur res.partner)
    beton_purchase_order_ids = fields.One2many(
        'purchase.order', 'partner_id',
        string='Bons achat béton',
    )

    # ===== Totaux Encaissements (clients) =====
    beton_ca_total = fields.Monetary(
        string='Montant total ventes',
        currency_field='currency_id',
        compute='_compute_beton_finance', store=True,
    )
    beton_verse_client = fields.Monetary(
        string='Total versé (client)',
        currency_field='currency_id',
        compute='_compute_beton_finance', store=True,
    )
    beton_credit_client = fields.Monetary(
        string='Crédit client',
        currency_field='currency_id',
        compute='_compute_beton_finance', store=True,
    )

    # ===== Totaux Décaissements (fournisseurs) =====
    beton_achat_total = fields.Monetary(
        string='Montant total achats',
        currency_field='currency_id',
        compute='_compute_beton_finance', store=True,
    )
    beton_verse_fournisseur = fields.Monetary(
        string='Total versé (fournisseur)',
        currency_field='currency_id',
        compute='_compute_beton_finance', store=True,
    )
    beton_credit_fournisseur = fields.Monetary(
        string='Crédit fournisseur',
        currency_field='currency_id',
        compute='_compute_beton_finance', store=True,
    )

    # ===== Compteurs =====
    beton_entry_count = fields.Integer(
        compute='_compute_beton_finance', store=True,
    )
    beton_expense_count = fields.Integer(
        compute='_compute_beton_finance', store=True,
    )
    beton_versement_count = fields.Integer(
        compute='_compute_beton_finance', store=True,
    )

    # ===== Alerte plafond crédit =====
    beton_credit_over_limit = fields.Boolean(
        string="Crédit dépassé",
        compute='_compute_beton_credit_over_limit',
        store=True,
        help="Vrai si le crédit (client ou fournisseur) dépasse le plafond crédit.",
    )
    beton_credit_overflow = fields.Monetary(
        string="Dépassement",
        compute='_compute_beton_credit_over_limit',
        store=True,
        currency_field='currency_id',
        help="Montant du dépassement (crédit - plafond).",
    )

    @api.depends(
        'beton_credit_client', 'beton_credit_fournisseur',
        'plafond_credit', 'type_partenaire_beton',
    )
    def _compute_beton_credit_over_limit(self):
        for p in self:
            plafond = p.plafond_credit or 0.0
            if plafond <= 0:
                # Pas de plafond défini -> pas d'alerte
                p.beton_credit_over_limit = False
                p.beton_credit_overflow = 0.0
                continue
            if p.type_partenaire_beton == 'client':
                credit = p.beton_credit_client or 0.0
            elif p.type_partenaire_beton == 'fournisseur':
                credit = p.beton_credit_fournisseur or 0.0
            else:
                p.beton_credit_over_limit = False
                p.beton_credit_overflow = 0.0
                continue
            p.beton_credit_over_limit = credit > plafond
            p.beton_credit_overflow = max(credit - plafond, 0.0)

    @api.depends(
        # Sale orders (source de la dette client)
        'sale_order_ids.state',
        'sale_order_ids.amount_total',
        # Purchase orders (source de la dette fournisseur)
        'beton_purchase_order_ids.state',
        'beton_purchase_order_ids.amount_total',
        # Encaissements (paiements réels)
        'beton_entry_ids.state',
        'beton_entry_ids.amount_paid',
        # Décaissements
        'beton_expense_ids.state',
        'beton_expense_ids.amount_paid',
        # Versements
        'beton_versement_ids',
    )
    def _compute_beton_finance(self):
        """Calcule les totaux financiers béton du partenaire.

        Côté CLIENT :
          - ca_total       = somme des SO confirmés
          - verse_client   = somme des amount_paid des encaissements approuvés
          - credit_client  = max(ca_total - verse_client, 0)

        Côté FOURNISSEUR :
          - achat_total       = somme des PO confirmés
          - verse_fournisseur = somme des amount_paid des décaissements approuvés
          - credit_fournisseur= max(achat_total - verse_fournisseur, 0)
        """
        SaleOrder = self.env['sale.order']
        PurchaseOrder = self.env['purchase.order']
        for partner in self:
            # ===== CLIENT =====
            # Total = somme des bons de commande client confirmés (sale, done)
            sale_orders = SaleOrder.search([
                ('partner_id', '=', partner.id),
                ('state', 'in', ('sale', 'done')),
            ])
            ca_total = sum(sale_orders.mapped('amount_total'))

            # Versé = somme amount_paid de TOUS les encaissements approuvés
            entries = partner.beton_entry_ids.filtered(lambda e: e.state == 'approuve')
            verse_client = sum(entries.mapped('amount_paid'))

            partner.beton_ca_total = ca_total
            partner.beton_verse_client = verse_client
            partner.beton_credit_client = max(ca_total - verse_client, 0.0)
            partner.beton_entry_count = len(entries)

            # ===== FOURNISSEUR =====
            # Total = somme des bons d'achat confirmés
            purchase_orders = PurchaseOrder.search([
                ('partner_id', '=', partner.id),
                ('state', 'in', ('purchase', 'done')),
            ])
            achat_total = sum(purchase_orders.mapped('amount_total'))

            expenses = partner.beton_expense_ids.filtered(lambda e: e.state == 'approuve')
            verse_fourn = sum(expenses.mapped('amount_paid'))

            partner.beton_achat_total = achat_total
            partner.beton_verse_fournisseur = verse_fourn
            partner.beton_credit_fournisseur = max(achat_total - verse_fourn, 0.0)
            partner.beton_expense_count = len(expenses)

            # ===== Versements =====
            partner.beton_versement_count = len(partner.beton_versement_ids)

    def action_view_beton_entries(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Encaissements',
            'res_model': 'beton.caisse.entry',
            'view_mode': 'tree,form',
            'domain': [('client_id', '=', self.id)],
        }

    def action_view_beton_expenses(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Décaissements',
            'res_model': 'beton.caisse.expense',
            'view_mode': 'tree,form',
            'domain': [('fournisseur', '=', self.id)],
        }

    def action_view_beton_versements(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Versements',
            'res_model': 'beton.versement',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
        }

    def action_create_beton_versement(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Enregistrer un versement',
            'res_model': 'beton.versement',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_partner_id': self.id,
            },
        }
