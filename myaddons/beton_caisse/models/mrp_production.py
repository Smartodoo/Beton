from odoo import models, _
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def action_confirm(self):
        for order in self:
            order._check_beton_client_required()
            order._check_beton_plafond_credit()
        return super().action_confirm()

    def _check_beton_client_required(self):
        """Bloque la confirmation si aucun client n'est sélectionné."""
        self.ensure_one()
        if not self.client_id:
            raise UserError(_(
                "Veuillez sélectionner un client avant de confirmer l'ordre de fabrication."
            ))

    def _check_beton_plafond_credit(self):
        """Bloque la confirmation si le crédit client dépasserait le plafond.
        Vérifié sur l'ordre de fabrication, avant l'étape de vente."""
        self.ensure_one()
        partner = self.client_id
        if not partner or partner.type_partenaire_beton != 'client':
            return
        plafond = partner.plafond_credit or 0.0
        if plafond <= 0:
            return  # Pas de plafond défini -> pas de blocage

        # Montant estimé de l'OF (prix de vente catalogue)
        montant_of = (self.product_qty or 0.0) * (self.product_id.list_price or 0.0)
        if self.inclure_service and self.service_product_id:
            montant_of += self.service_product_id.list_price or 0.0

        current_credit = partner.beton_credit_client or 0.0
        future_credit = current_credit + montant_of
        if future_credit > plafond:
            overflow = future_credit - plafond
            raise UserError(_(
                "Plafond crédit dépassé pour %(partner)s !\n\n"
                "Crédit actuel             : %(current).2f\n"
                "Montant de cet OF         : %(amount).2f\n"
                "Crédit après confirmation : %(future).2f\n"
                "Plafond autorisé          : %(plafond).2f\n"
                "Dépassement               : %(overflow).2f\n\n"
                "Veuillez augmenter le plafond du client ou attendre un encaissement."
            ) % {
                'partner': partner.name,
                'current': current_credit,
                'amount': montant_of,
                'future': future_credit,
                'plafond': plafond,
                'overflow': overflow,
            })
