from odoo import models, api


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    def update_payment_method_in_journal(self):

        # Récupérer les méthodes de paiement
        methods_map = {
            'bank': [
                self.env.ref('custom_project.account_payment_method_virement_in', raise_if_not_found=False),
                self.env.ref('custom_project.account_payment_method_versement_in', raise_if_not_found=False),
                self.env.ref('custom_project.account_payment_method_cheque_in', raise_if_not_found=False),

            ],
            'cash': [
                self.env.ref('custom_project.account_payment_method_espece_in', raise_if_not_found=False),
                self.env.ref('custom_project.account_payment_method_aterme_in', raise_if_not_found=False)
            ]
        }

        # Méthodes de paiement sortantes
        methods_map_out = {
            'bank': [
                self.env.ref('custom_project.account_payment_method_virement_out', raise_if_not_found=False),
                self.env.ref('custom_project.account_payment_method_versement_out', raise_if_not_found=False),
                self.env.ref('custom_project.account_payment_method_cheque_out', raise_if_not_found=False),

            ],
            'cash': [
                self.env.ref('custom_project.account_payment_method_espece_out', raise_if_not_found=False),
                self.env.ref('custom_project.account_payment_method_aterme_out', raise_if_not_found=False)
            ]
        }

        # Supprimer les anciennes lignes de méthodes de paiement
        self.inbound_payment_method_line_ids.unlink()
        self.outbound_payment_method_line_ids.unlink()

        # Ajouter les nouvelles méthodes associées au type de journal
        methods_in = methods_map.get(self.type, [])
        methods_out = methods_map_out.get(self.type, [])

        # Ajouter les méthodes de paiement valides
        if methods_in:
            self.inbound_payment_method_line_ids = [(0, 0, {'payment_method_id': method.id}) for method in methods_in if
                                                    method]

        if methods_out:
            self.outbound_payment_method_line_ids = [(0, 0, {'payment_method_id': method.id}) for method in methods_out
                                                     if method]

        print(f"✅ Méthodes de paiement mises à jour pour le journal : {self.name}")
