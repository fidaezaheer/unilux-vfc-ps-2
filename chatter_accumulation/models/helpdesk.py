# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    helpdesk_ids = fields.One2many("helpdesk.ticket", "sale_order_id", "Helpdesk Tickets")


class Message(models.Model):
    _inherit = 'mail.message'

    @api.model
    def create(self, vals):
        new_val = vals
        res = super(Message, self).create(vals)
        self._create_accumulation(new_val)
        return res

    def _create_accumulation(self, vals):
        print("_create_accumulation >>>>>>>>>>>>>>", self, vals)
        model_info = ['project.task', 'sale.order', 'res.partner', 'account.move', 'helpdesk.ticket']
        if vals.get('model') in model_info:
            record = self.env[vals.get('model')].search([('id', '=', vals.get('res_id'))])
            print("record >>>>>>>>>>>>>", record)
            if vals.get('model') == 'helpdesk.ticket':
                print("record.partner_id >>>>>>>>>>>>>>", record.partner_id)
                if record.partner_id:
                    vals['model'] = 'res.partner'
                    vals['res_id'] = record.partner_id.id
                    record.partner_id.message_post(body=vals.get('body'))
                    # self.create(vals)
            elif vals.get('model') == 'project.task':
                print("record.helpdesk_ticket_id >>>>>>>>>>>>>>", record.helpdesk_ticket_id)
                if record.helpdesk_ticket_id:
                    vals['model'] = 'helpdesk.ticket'
                    vals['res_id'] = record.helpdesk_ticket_id.id
                    record.helpdesk_ticket_id.message_post(body=vals.get('body'))
                    # self.create(vals)
            elif vals.get('model') == 'sale.order':
                print("record.helpdesk_ids >>>>>>>>>>>>>", record.helpdesk_ids)
                if record.helpdesk_ids:
                    for helpdesk in record.helpdesk_ids:
                        vals['model'] = 'helpdesk.ticket'
                        vals['res_id'] = helpdesk.id
                        helpdesk.message_post(body=vals.get('body'))
                        # self.create(vals)
                elif record.task_id and record.task_id.helpdesk_ticket_id:
                    vals['model'] = 'helpdesk.ticket'
                    vals['res_id'] = record.task_id.helpdesk_ticket_id.id
                    record.task_id.helpdesk_ticket_id.message_post(body=vals.get('body'))
                    # self.create(vals)
            elif vals.get('model') == 'account.move':
                if record.invoice_line_ids and record.invoice_line_ids.mapped('sale_line_ids') and record.invoice_line_ids.mapped('sale_line_ids').mapped('task_id') and record.invoice_line_ids.mapped('sale_line_ids').mapped('task_id').mapped('helpdesk_ticket_id'):
                    print("record.invoice_line_ids.mapped('sale_line_ids').mapped('task_id').mapped('helpdesk_ticket_id') >>>>>>>>>>>", record.invoice_line_ids.mapped('sale_line_ids').mapped('task_id').mapped('helpdesk_ticket_id'))
                    for helpdesk in record.invoice_line_ids.mapped('sale_line_ids').mapped('task_id').mapped('helpdesk_ticket_id'):
                        vals['model'] = 'helpdesk.ticket'
                        vals['res_id'] = helpdesk.id
                        helpdesk.message_post(body=vals.get('body'))
                        # self.create(vals)
        return True
