# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    @api.model
    def create(self, vals):
        res = super(HelpdeskTicket, self).create(vals)
        print("HelpdeskTicket, create >>>>>>>>>>>>>>>>", res, dir(res))
        return res

    def write(self, vals):
        res = super(HelpdeskTicket, self).write(vals)
        print("HelpdeskTicket, write >>>>>>>>>>>>>>>>", res, dir(res))
        return res

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        print("HelpdeskTicket message_post >>>>>>>>>>>>", self, kwargs)
        res = super(HelpdeskTicket, self).message_post(**kwargs)
        return res


class Task(models.Model):
    _inherit = 'project.task'

    @api.model
    def create(self, vals):
        res = super(Task, self).create(vals)
        print("Task, create >>>>>>>>>>>>>>>>", res, dir(res))
        return res

    def write(self, vals):
        res = super(Task, self).write(vals)
        print("Task, write >>>>>>>>>>>>>>>>", res, dir(res))
        return res

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        print("Task message_post >>>>>>>>>>>>", self, kwargs)
        res = super(Task, self).message_post(**kwargs)
        return res


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    helpdesk_ids = fields.One2many("helpdesk.ticket", "sale_order_id", "Helpdesk Tickets")

    @api.model
    def create(self, vals):
        res = super(SaleOrder, self).create(vals)
        print("SaleOrder, create >>>>>>>>>>>>>>>>", res, dir(res))
        return res

    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        print("SaleOrder write >>>>>>>>>>>>>>>>", res, dir(res))
        return res

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        print("SaleOrder message_post >>>>>>>>>>>>", self, kwargs)
        res = super(SaleOrder, self).message_post(**kwargs)
        return res


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model
    def create(self, vals):
        res = super(AccountMove, self).create(vals)
        print("AccountMove, create >>>>>>>>>>>>>>>>", res, dir(res))
        return res

    def write(self, vals):
        res = super(AccountMove, self).write(vals)
        print("AccountMove write >>>>>>>>>>>>>>>>", res, dir(res))
        return res

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        print("AccountMove message_post >>>>>>>>>>>>", self, kwargs)
        res = super(AccountMove, self).message_post(**kwargs)
        return res


class Partner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def create(self, vals):
        res = super(Partner, self).create(vals)
        print("Partner create >>>>>>>>>>>>>>>>", res, dir(res))
        return res

    def write(self, vals):
        res = super(Partner, self).write(vals)
        print("Partner write >>>>>>>>>>>>>>>>", res, dir(res))
        return res

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        print("Partner message_post >>>>>>>>>>>>", self, kwargs)
        res = super(Partner, self).message_post(**kwargs)
        return res


class Message(models.Model):
    _inherit = 'mail.message'

    @api.model
    def create(self, vals):
        new_val = vals
        res = super(Message, self).create(vals)
        print("Message create >>>>>>>>>>>>>>>>", res, dir(res))
        self._create_accumulation(new_val)
        return res

    def _create_accumulation(self, vals):
        model_info = ['project.task', 'sale.order', 'res.partner', 'account.move', 'helpdesk.ticket']
        if vals.get('model') in model_info:
            record = self.env[vals.get('model')].search([('id', '=', vals.get('res_id'))])
            print("record >>>>>>>>>>>>>", record)
            if vals.get('model') == 'helpdesk.ticket':
                if record.partner_id:
                    vals['model'] = 'res.partner'
                    vals['res_id'] = record.partner_id.id
                    self.create(vals)
            elif vals.get('model') == 'project.task':
                if record.helpdesk_ticket_id:
                    vals['model'] = 'helpdesk.ticket'
                    vals['res_id'] = record.helpdesk_ticket_id.id
                    self.create(vals)
            elif vals.get('model') == 'sale.order':
                if record.helpdesk_ids:
                    for helpdesk in record.helpdesk_ids:
                        vals['model'] = 'helpdesk.ticket'
                        vals['res_id'] = helpdesk.id
                        self.create(vals)
                elif record.task_id and record.task_id.helpdesk_ticket_id:
                    vals['model'] = 'helpdesk.ticket'
                    vals['res_id'] = record.task_id.helpdesk_ticket_id.id
                    self.create(vals)
            elif vals.get('model') == 'account.move':
                if record.invoice_line_ids and record.invoice_line_ids.mapped('sale_line_ids') and record.invoice_line_ids.mapped('sale_line_ids').mapped('task_id') and record.invoice_line_ids.mapped('sale_line_ids').mapped('task_id').mapped('helpdesk_ticket_id'):
                    for helpdesk in record.invoice_line_ids.mapped('sale_line_ids').mapped('task_id').mapped('helpdesk_ticket_id'):
                        vals['model'] = 'helpdesk.ticket'
                        vals['res_id'] = helpdesk.id
                        self.create(vals)
        return True
