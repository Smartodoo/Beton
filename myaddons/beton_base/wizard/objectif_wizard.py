from odoo import _, fields, models


class BetonObjectifWizard(models.TransientModel):
    _name = 'beton.objectif.wizard'
    _description = "Définir l'objectif pour tous les ordres de fabrication"

    objectif = fields.Float(
        string="Objectif (m³)", required=True,
        default=lambda self: self.env['mrp.production']._default_objectif(),
    )

    def action_appliquer(self):
        """Applique l'objectif saisi à TOUS les ordres de fabrication et
        l'enregistre comme valeur par défaut des nouveaux ordres."""
        self.ensure_one()
        productions = self.env['mrp.production'].search([])
        productions.with_context(objectif_source='global').write(
            {'objectif': self.objectif})
        # Mémorise la valeur pour la proposer par défaut aux nouveaux OF.
        self.env['ir.config_parameter'].sudo().set_param(
            'beton_base.objectif_defaut', self.objectif)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Objectif mis à jour"),
                'message': _(
                    "Objectif de %(obj)s m³ appliqué à %(n)s ordre(s) de "
                    "fabrication.",
                    obj=self.objectif,
                    n=len(productions),
                ),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }
