from odoo import fields, models
from odoo.exceptions import UserError


class BetonAnnulationWizard(models.TransientModel):
    _name = 'beton.annulation.wizard'
    _description = "Confirmation d'annulation d'un ordre de fabrication"

    production_id = fields.Many2one(
        'mrp.production', string="Ordre de fabrication", required=True)
    motif = fields.Text(string="Motif d'annulation", required=True)

    def action_confirmer_annulation(self):
        """Enregistre le motif, journalise l'annulation puis annule l'ordre."""
        self.ensure_one()
        production = self.production_id
        if not production:
            raise UserError("Aucun ordre de fabrication associé.")

        # Enregistrement du motif dans la table de suivi
        self.env['beton.motif.annulation'].create({
            'production_id': production.id,
            'production_name': production.name,
            'motif': self.motif,
            'state_avant': production.state,
            'centrale_id': production.centrale_id.id,
            'client_id': production.client_id.id,
            'chantier': production.chantier,
            'product_id': production.product_id.id,
            'product_qty': production.product_qty,
            'company_id': production.company_id.id,
        })

        # Trace dans le chatter de l'ordre
        production.message_post(
            body="Ordre de fabrication annulé.<br/><b>Motif :</b> %s" % self.motif)

        # Annulation standard Odoo
        production.action_cancel()

        return {'type': 'ir.actions.act_window_close'}
