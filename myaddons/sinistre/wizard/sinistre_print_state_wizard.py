from odoo import models, fields, api
from odoo.exceptions import UserError


class SinistrePrintStateWizard(models.TransientModel):
    _name = 'sinistre.print.state.wizard'
    _description = 'Wizard Impression Sinistres par État'

    # Liste des états disponibles
    state = fields.Selection([
        ('draft', 'En Attente de PV'),
        ('en_cours', 'En cours'),
        ('termine', 'Clôturé')
    ], string="État du sinistre", required=True)

    def print_report_state(self):
        """Impression des sinistres filtrés par état"""
        sinistres = self.env['sinistre'].search([('state', '=', self.state)])

        if not sinistres:
            raise UserError("Aucun sinistre trouvé pour l'état sélectionné.")

        # Nom lisible de l’état pour le rapport
        state_label = dict(self._fields['state'].selection).get(self.state)

        # Contexte transmis au rapport
        ctx = {
            'report_state': state_label,
        }

        # On réutilise le même template QWeb que les autres impressions
        return self.env.ref('sinistre.action_report_sinistre_by_state') \
            .with_context(ctx) \
            .report_action(sinistres)

class SinistrePrintStateReglementWizard(models.TransientModel):
    _name = 'sinistre.print.state.reglement.wizard'
    _description = "Impression des sinistres par état de règlement"

    payment_state = fields.Selection([
        ('payé', 'Réglé'),
        ('pas_payé', 'Non Réglé'),
    ], string="État de règlement", required=True)

    def print_report_reglement(self):
        # Recherche des sinistres selon l'état de règlement
        sinistres = self.env['sinistre'].search([
            ('payment_state', '=', self.payment_state)
        ])

        if not sinistres:
            raise UserError("Aucun sinistre trouvé pour l'état de règlement sélectionné.")

        # Déterminer le libellé pour l'affichage dans le rapport
        state_label = dict(self._fields['payment_state'].selection).get(self.payment_state)

        # Contexte transmis au rapport
        ctx = {
            'report_payment_state': state_label,
        }

        # On réutilise le même template QWeb que les autres impressions
        return self.env.ref('sinistre.action_report_sinistre_by_state_reglement') \
            .with_context(ctx) \
            .report_action(sinistres)


class SinistrePrintDriverWizard(models.TransientModel):
    _name = 'sinistre.print.driver.wizard'
    _description = 'Impression des sinistres par conducteur'

    # Champ pour choisir le conducteur depuis les sinistres existants
    driver_id = fields.Many2one(
        'res.partner',
        string="Conducteur",
        domain=lambda self: self._get_driver_domain(),
        required=True
    )

    @api.model
    def _get_driver_domain(self):
        """Afficher uniquement les conducteurs ayant des sinistres enregistrés"""
        driver_ids = self.env['sinistre'].search([]).mapped('driver_id.id')
        return [('id', 'in', driver_ids)]

    def print_report_driver(self):
        # Recherche des sinistres du conducteur sélectionné
        sinistres = self.env['sinistre'].search([
            ('driver_id', '=', self.driver_id.id)
        ])

        if not sinistres:
            raise UserError("Aucun sinistre trouvé pour ce conducteur.")

        # Contexte pour le rapport
        ctx = {
            'report_driver_name': self.driver_id.name,
        }

        # Action d'impression
        return self.env.ref('sinistre.action_report_sinistre_by_driver') \
            .with_context(ctx) \
            .report_action(sinistres)

class SinistrePrintPlateWizard(models.TransientModel):
    _name = 'sinistre.print.plate.wizard'
    _description = "Impression des sinistres par plaque d'immatriculation"

    # Liste déroulante des plaques d’immatriculation existantes dans sinistre
    license_plate = fields.Selection(
        selection=lambda self: self._get_license_plates(),
        string="Plaque d’immatriculation",
        required=True
    )

    @api.model
    def _get_license_plates(self):
        """Retourne la liste des plaques existantes dans les sinistres"""
        # On récupère toutes les plaques enregistrées
        plates = self.env['sinistre'].search([]).mapped('license_plate')
        # Nettoyer : supprimer les espaces et mettre en majuscules
        plates = [p.strip().upper() for p in plates if p]
        # Supprimer les doublons et trier alphabétiquement
        plates = sorted(set(plates))
        # Retour au format attendu par le champ Selection
        return [(p, p) for p in plates]

    def print_report_plate(self):
        """Imprime uniquement les sinistres ayant la plaque sélectionnée"""
        # Récupérer les enregistrements correspondants
        sinistres = self.env['sinistre'].search([('license_plate', '=', self.license_plate)
        ])

        # Si aucun enregistrement trouvé → erreur utilisateur
        if not sinistres:
            raise UserError("Aucun sinistre trouvé pour cette plaque d’immatriculation.")

        # Contexte pour passer la plaque au rapport
        ctx = {'report_license_plate': self.license_plate}
        # Action d'impression
        return self.env.ref('sinistre.action_report_sinistre_by_plate') \
            .with_context(ctx) \
            .report_action(sinistres)


