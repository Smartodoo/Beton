from datetime import timedelta
from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    role_employe = fields.Selection([
        ('chauffeur', 'Chauffeur'),
        ('operateur', 'Opérateur'),
        ('laborantin', 'Laborantin'),
        ('commercial', 'Commercial'),
        ('administratif', 'Administratif'),
        ('autre', 'Autre'),
    ], string="Rôle")

    # Permis de conduire (visible si rôle = chauffeur)
    categorie_permis = fields.Selection([
        ('a', 'A - Motocycle'),
        ('b', 'B - Véhicule léger'),
        ('c', 'C - Poids lourd'),
        ('d', 'D - Transport en commun'),
        ('e', 'E - Remorque'),
        ('ec', 'EC - Poids lourd + Remorque'),
    ], string="Catégorie de permis")
    numero_permis = fields.Char(string="N° Permis")
    date_expiration_permis = fields.Date(string="Date d'expiration du permis")

    # Brevet (visible si rôle = chauffeur)
    brevet = fields.Char(string="Brevet")
    date_expiration_brevet = fields.Date(string="Date d'expiration du brevet")

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for emp in records:
            if emp.role_employe == 'chauffeur':
                emp._sync_chauffeur_partner()
        return records

    def write(self, vals):
        res = super().write(vals)
        if 'role_employe' in vals:
            for emp in self:
                emp._sync_chauffeur_partner()
        return res

    def _sync_chauffeur_partner(self):
        """Synchronise le statut chauffeur sur le contact lié (res.partner)."""
        self.ensure_one()
        is_chauffeur = self.role_employe == 'chauffeur'
        if self.work_contact_id:
            self.work_contact_id.sudo().write({'is_chauffeur': is_chauffeur})
        elif is_chauffeur:
            # Créer le contact si inexistant
            partner = self.env['res.partner'].sudo().create({
                'name': self.name,
                'is_chauffeur': True,
                'company_id': self.company_id.id,
                'type': 'contact',
            })
            self.work_contact_id = partner

    @api.model
    def _cron_check_expiration_chauffeur(self):
        """Cron : envoie des notifications pour les permis/brevets qui expirent dans moins de 15 jours."""
        today = fields.Date.today()
        limit = today + timedelta(days=15)
        chauffeurs = self.search([
            ('role_employe', '=', 'chauffeur'),
            '|',
            '&', ('date_expiration_permis', '<=', limit), ('date_expiration_permis', '>=', today),
            '&', ('date_expiration_brevet', '<=', limit), ('date_expiration_brevet', '>=', today),
        ])
        for emp in chauffeurs:
            messages = []
            if emp.date_expiration_permis and today <= emp.date_expiration_permis <= limit:
                jours = (emp.date_expiration_permis - today).days
                messages.append(f"Le permis de conduire de {emp.name} expire dans {jours} jour(s) ({emp.date_expiration_permis})")
            if emp.date_expiration_brevet and today <= emp.date_expiration_brevet <= limit:
                jours = (emp.date_expiration_brevet - today).days
                messages.append(f"Le brevet de {emp.name} expire dans {jours} jour(s) ({emp.date_expiration_brevet})")
            if not messages:
                continue
            body = "<br/>".join(messages)
            # Notification dans le chatter de l'employé
            emp.message_post(
                body=f"<strong>Alerte expiration chauffeur</strong><br/>{body}",
                message_type='notification',
                subtype_xmlid='mail.mt_note',
            )
            # Notification via Discuss au responsable (ou à l'utilisateur courant)
            notify_partner = (
                emp.parent_id.work_contact_id
                or emp.department_id.manager_id.work_contact_id
                or self.env.user.partner_id
            )
            if notify_partner:
                self.env['mail.message'].create({
                    'message_type': 'notification',
                    'subtype_id': self.env.ref('mail.mt_note').id,
                    'body': f"<strong>Alerte expiration chauffeur</strong><br/>{body}",
                    'partner_ids': [notify_partner.id],
                    'model': 'hr.employee',
                    'res_id': emp.id,
                    'notification_ids': [(0, 0, {
                        'res_partner_id': notify_partner.id,
                        'notification_type': 'inbox',
                    })],
                })
