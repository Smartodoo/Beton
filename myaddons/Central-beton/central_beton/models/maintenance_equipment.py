# -*- coding: utf-8 -*-

from odoo import models, fields


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    code_equipement = fields.Char(string='Code Equipement')
    centrale_id = fields.Many2one(
        'central.beton.centrale', string='Centrale')
    heures_fonctionnement = fields.Float(
        string='Heures de Fonctionnement')
    etat_equipement = fields.Selection([
        ('operationnel', 'Operationnel'),
        ('degrade', 'Fonctionnement Degrade'),
        ('arret', 'A l\'Arret'),
        ('reforme', 'Reforme'),
    ], string='Etat Equipement', default='operationnel')
    type_equipement = fields.Selection([
        ('malaxeur', 'Malaxeur'),
        ('doseur', 'Doseur'),
        ('convoyeur', 'Convoyeur'),
        ('silo', 'Silo'),
        ('pompe', 'Pompe'),
        ('compresseur', 'Compresseur'),
        ('automate', 'Automate'),
        ('autre', 'Autre'),
    ], string='Type Equipement')
    puissance_kw = fields.Float(string='Puissance (kW)')
    date_mise_service = fields.Date(
        string='Date de Mise en Service')
    date_derniere_revision = fields.Date(
        string='Derniere Revision')
    prochaine_revision = fields.Date(
        string='Prochaine Revision')
    notes_techniques = fields.Text(string='Notes Techniques')
