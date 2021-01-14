# -*- coding: utf-8 -*-

from odoo import models, fields, api

# class my_module(models.Model):
#     _name = 'my_module.my_module'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100

class LeadInherit(models.Model):
    _inherit = "crm.lead"
    image_count = fields.Integer('# Image', compute='_compute_image_count')

    def _compute_image_count(self):
        print("*****_compute_image_count")
        attachment_data = self.env['ir.attachment'].sudo().search([('res_model', '=', self.id)])
        self.image_count = len(attachment_data)
    def action_attachment(self):
        return