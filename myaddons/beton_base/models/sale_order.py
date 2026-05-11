from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    production_beton_id = fields.Many2one('mrp.production', string="Ordre de fabrication")
    vehicle_id = fields.Many2one('fleet.vehicle', string="Camion")
    chauffeur_id = fields.Many2one('hr.employee', string="Chauffeur", domain="[('role_employe', '=', 'chauffeur')]")
    chantier = fields.Char(string="Chantier")
    bon_sortie_ids = fields.One2many('beton.bon.sortie', 'sale_order_id', string="Bons de sortie")
    bon_sortie_count = fields.Integer(string="Bons de sortie", compute='_compute_bon_sortie_count')

    def _compute_bon_sortie_count(self):
        for order in self:
            order.bon_sortie_count = len(order.bon_sortie_ids)

    def action_confirm(self):
        res = super().action_confirm()
        for order in self:
            # Créer les bons de sortie pour les produits de type service
            order._create_bons_sortie_service()
            # Gestion transport béton
            production = order.production_beton_id
            if production and production.transport_ligne_ids:
                order._split_pickings_per_truck(production)
            elif order.vehicle_id or order.chauffeur_id:
                for picking in order.picking_ids:
                    picking.write({
                        'vehicle_id': order.vehicle_id.id if order.vehicle_id else False,
                        'chauffeur_id': order.chauffeur_id.id if order.chauffeur_id else False,
                        'chantier': order.chantier or '',
                    })
        return res

    def _create_bons_sortie_service(self):
        """Crée un bon de sortie pour chaque ligne de produit de type service."""
        for line in self.order_line:
            if line.product_id and line.product_id.detailed_type == 'service':
                self.env['beton.bon.sortie'].create({
                    'sale_order_id': self.id,
                    'partner_id': self.partner_id.id,
                    'product_id': line.product_id.id,
                    'quantity': line.product_uom_qty,
                    'chantier': self.chantier or '',
                    'description': line.name,
                    'state': 'confirmed',
                })

    def action_view_bon_sortie(self):
        """Ouvre les bons de sortie liés à cette vente."""
        self.ensure_one()
        if self.bon_sortie_count == 1:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Bon de Sortie',
                'res_model': 'beton.bon.sortie',
                'view_mode': 'form',
                'res_id': self.bon_sortie_ids.id,
            }
        return {
            'type': 'ir.actions.act_window',
            'name': 'Bons de Sortie',
            'res_model': 'beton.bon.sortie',
            'view_mode': 'tree,form',
            'domain': [('sale_order_id', '=', self.id)],
        }

    def _split_pickings_per_truck(self, production):
        """Remplace le BL auto-créé par un BL par camion (ligne de transport)."""
        auto_pickings = self.picking_ids.filtered(lambda p: p.state not in ('cancel', 'done'))
        if not auto_pickings:
            return

        picking_ref = auto_pickings[0]
        picking_type = picking_ref.picking_type_id
        location_src = picking_ref.location_id
        location_dest = picking_ref.location_dest_id
        group_id = picking_ref.group_id
        sale_line = self.order_line[0]

        # Supprimer les BL auto-créés
        auto_pickings.action_cancel()
        auto_pickings.sudo().unlink()

        # Créer un BL par ligne de transport
        for ligne in production.transport_ligne_ids:
            if ligne.quantite <= 0:
                continue
            new_picking = self.env['stock.picking'].create({
                'partner_id': self.partner_id.id,
                'picking_type_id': picking_type.id,
                'location_id': location_src.id,
                'location_dest_id': location_dest.id,
                'origin': self.name,
                'group_id': group_id.id if group_id else False,
                'vehicle_id': ligne.vehicle_id.id if ligne.vehicle_id else False,
                'chauffeur_id': ligne.chauffeur_id.id if ligne.chauffeur_id else False,
                'chantier': production.chantier or '',
                'formule_beton_id': production.bom_id.id if production.bom_id else False,
                'distance': production.distance,
                'heure_depart': ligne.heure_depart,
                'heure_arrivee': ligne.heure_arrivee,
            })
            self.env['stock.move'].create({
                'name': sale_line.product_id.display_name,
                'product_id': sale_line.product_id.id,
                'product_uom_qty': ligne.quantite,
                'product_uom': sale_line.product_uom.id,
                'location_id': location_src.id,
                'location_dest_id': location_dest.id,
                'picking_id': new_picking.id,
                'sale_line_id': sale_line.id,
                'group_id': group_id.id if group_id else False,
            })
            new_picking.action_confirm()
            new_picking.action_assign()
