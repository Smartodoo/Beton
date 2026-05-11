# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ProjectObservation(models.Model):
    _name = "project.observation"
    _description = "Observation / Suivi de projet"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "date_start desc, id desc"



    # Basic Info
    name = fields.Char("Titre", required=True, tracking=True)
    description = fields.Text("Description", tracking=True)
    obs_type = fields.Selection([
        ('progress', 'Progress'),
        ('issue', 'Issue'),
        ('quality', 'Quality'),
        ('safety', 'Safety'),
        ('general', 'General'),
    ], string="Type", default='general', tracking=True)

    # Project & Partner
    project_id = fields.Many2one('custom.project', string="Projet", required=True, ondelete='cascade', index=True, tracking=True)
    partner_id = fields.Many2one('res.partner', string="Partenaire / Sous-traitant", index=True)

    # Dates for Calendar
    date_start = fields.Datetime("Start Date", default=fields.Datetime.now, required=True, tracking=True)
    date_stop = fields.Datetime("End Date", compute='_compute_date_stop', store=True)

    # Responsible user
    user_id = fields.Many2one('res.users', string="Utilisateur", default=lambda self: self.env.user, tracking=True)

    # Status
    state = fields.Selection([
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
    ], string='State', default='open', tracking=True)

    # Attachments
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')

    # Action required
    is_action_required = fields.Boolean("Action requise ?", default=False)

    @api.depends('date_start')
    def _compute_date_stop(self):
        """Default duration 1 hour for calendar events"""
        for rec in self:
            rec.date_stop = rec.date_start + timedelta(hours=1) if rec.date_start else False

    def action_mark_done(self):
        for rec in self:
            rec.state = 'done'
            rec.message_post(body=_("Marked as done by %s") % self.env.user.name)

    @api.model
    def create(self, vals):
        rec = super(ProjectObservation, self).create(vals)
        if rec.project_id:
            rec.project_id.message_post(
                body=_("New observation: <b>%s</b>") % rec.name,
                subtype_xmlid="mail.mt_comment"
            )
        return rec


class CustomProject(models.Model):
    _inherit = 'custom.project'

    observation_count = fields.Integer(string="Observations", compute='_compute_observation_count')

    def _compute_observation_count(self):
        for rec in self:
            rec.observation_count = self.env['project.observation'].search_count([('project_id', '=', rec.id)])

    def action_view_observations(self):
        self.ensure_one()
        return {
            'name': _('Observations'),
            'type': 'ir.actions.act_window',
            'res_model': 'project.observation',
            'view_mode': 'kanban,tree,form,calendar',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id},
        }
