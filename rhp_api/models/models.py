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

    attachment_line = fields.One2many('ir.attachment', 'res_id', string='Attachment Lines')


    def _compute_image_count(self):
        attachment_data = self.env['ir.attachment'].sudo().search([('res_model', '=', 'crm.lead'), ('res_id', '=', self.id), ])
        self.image_count = len(attachment_data)
    
    def action_attachment(self):
        action = self.env["ir.actions.actions"]._for_xml_id("base.action_attachment")
        action['context'] = {
            'default_res_model': self._name,
            'default_res_id': self.ids[0]
        }
        action['domain'] = ['&', ('res_model', '=', 'crm.lead'), ('res_id', 'in', self.ids)]
        return action


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    size = fields.Char('Size')
    quantity = fields.Integer('Quantity')
    res_partner_id = fields.Many2one('res.partner', 'Manufacturer')