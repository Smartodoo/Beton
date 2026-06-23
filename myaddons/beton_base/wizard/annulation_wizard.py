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

        # Récupération de la/les vente(s) liée(s) à cet ordre de fabrication
        orders = self.env['sale.order'].search([
            ('production_beton_id', '=', production.id),
            ('state', '!=', 'cancel'),
        ])
        if not orders:
            return {'type': 'ir.actions.act_window_close'}

        for order in orders:
            # Remettre la vente en brouillon pour autoriser la suppression
            # des lignes et la modification par l'utilisateur.
            if order.state not in ('draft', 'sent'):
                order.write({'state': 'draft'})
            # Supprimer toutes les lignes de produits dont le type n'est pas
            # « service » ; les lignes de service (ex. pompe à béton) sont
            # conservées. Les lignes de section/note sont laissées intactes.
            lignes_a_supprimer = order.order_line.filtered(
                lambda l: not l.display_type
                and l.product_id.detailed_type != 'service'
            )
            if lignes_a_supprimer:
                lignes_a_supprimer.unlink()

        # Ouvrir la vente liée pour permettre sa modification.
        return {
            'type': 'ir.actions.act_window',
            'name': "Vente",
            'res_model': 'sale.order',
            'view_mode': 'form',
            'res_id': orders[0].id,
            'target': 'current',
        }
