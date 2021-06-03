# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, Warning, ValidationError
from odoo.addons import decimal_precision as dp
from num2words import num2words
from datetime import datetime
import textwrap

class ChequePrintExpensesBankPayment(models.Model):
    _inherit = 'expense.bank.payments'
    _description = 'Cheque print expense bank payments'

    expense_pay_to = fields.Char(string='Pay To', track_visibility='onchange')

    cheque_reference = fields.Many2one('receive.cheque', string='Cheque Reference', copy=False, track_visibility='onchange')

    cheque_no = fields.Char(string='Cheque No', copy=False, track_visibility='onchange', readonly=True)
    processing_method = fields.Selection([('manual', 'Manual'),
                                        ('cheque', 'Cheque')], 
    default='cheque', copy=False, string="Method")
    cheque_type = fields.Selection([('ac_payee', 'A/C payee'),
                    ('cash', 'Cash')], 
    default='ac_payee', copy=False, string="Cheque Type")
   
    @api.multi
    def do_print(self):
        if self.expense_pay_to:
            tmp = ''.join([x for x in self.expense_pay_to if x != ' '])
            if len(tmp) < 3:
                raise Warning(_("Invalid Pay To"))
            else:
                self.message_post(body="<ul><li>Cheque Printed </li></ul>")
                return self.env.ref('mir_cheque_print.action_report_expense_cheque_print').report_action(self)
        else:
            raise Warning(_("Please fill in the Pay To input field!"))

    def fill_stars(self, amount_in_word):
        return '**' + str(amount_in_word) + '**'

    def plain_date(self):
        if self.expense_date:
            return datetime.strptime(self.expense_date, "%Y-%m-%d %H:%M:%S").strftime("%d%m%Y")

    @api.model
    def create(self, vals):
        if vals['processing_method'] == 'cheque':
            journal_id = vals.get('journal_id')

            if journal_id:
                cheque_info = self.env['cheque.info'].search([('bank_name', '=', journal_id),
                    ('state', '=', 'activated'),("is_complete", "=", False)],limit=1)
            
                if cheque_info:
                    vals['cheque_no'] = cheque_info.cheque_serial
                    cheque_info.update_cheque_number(journal_id)
                else:
                    raise Warning(_("No activated cheque is associated with selected journal!!"))
                
                return super(ChequePrintExpensesBankPayment, self).create(vals)

        else:
            return super(ChequePrintExpensesBankPayment, self).create(vals)

    @api.multi
    def write(self, vals):
        if self.processing_method == 'cheque':
            journal_id = vals.get('journal_id')
            processing_method = vals.get('processing_method')

            if journal_id or processing_method == 'cheque':
                if journal_id:
                    if self.processing_method != 'cheque':
                        return super(ChequePrintExpensesBankPayment, self).write(vals)
                    else:
                        pass

                cheque_info = self.env['cheque.info'].search([('bank_name', '=', journal_id or self.journal_id.id),
                    ('state', '=', 'activated'),("is_complete", "=", False)],limit=1)
                
                if cheque_info:
                    vals['cheque_no'] = cheque_info.cheque_serial
                    journal_id = journal_id if journal_id else self.journal_id.id
                    cheque_info.update_cheque_number(journal_id)
                else:
                    raise Warning(_("No activated cheque is associated with selected journal!!"))
                
                return super(ChequePrintExpensesBankPayment, self).write(vals)
            
            else:
                return super(ChequePrintExpensesBankPayment, self).write(vals)
        else:
            return super(ChequePrintExpensesBankPayment, self).write(vals)
    
    
    @api.multi
    def action_post(self):
        if self.state == 'approved':
            if any(self.payment_line_ids.mapped('expense_id').mapped(lambda exp: exp.state not in  ['approved', 'progress'])):
                raise UserError(_('Only approved expenses can be selected for payment posting'))

            account_move_obj = self.env['account.move']
            vals = {
                'company_id': self.company_id.id,
                'journal_id': self.journal_id.id,
                'date': self.expense_date,
                'ref': self.name,
                'is_account_expense_entry': True,
            }
            account_move_id = account_move_obj.create(vals)

            if account_move_id:
                account_move_lines = []

                if self.payment_line_ids:
                    for line in self.payment_line_ids:
                        move_line_debit_vals = {
                            'account_id': line.expense_type_id.expense_account_id.id,
                            'move_id': account_move_id.id, 
                            'debit': line.expense_amount,
                            'credit': 0.0,
                        }
                        account_move_lines.append(move_line_debit_vals)
                        
                    move_line_credit_vals = {
                        'account_id': self.expense_account_id.id,
                        'move_id': account_move_id.id, 
                        'debit': 0.0,
                        'credit': self.total_expense_amount,
                    }
                    account_move_lines.append(move_line_credit_vals)
                
                    account_move_id.line_ids = account_move_lines
                    account_move_id.post()
                    
                    self.write({
                        'state': 'done',
                        'move_id': account_move_id.id,
                        'posted_date': account_move_id.date,
                    })

                    self.payment_line_ids.mapped('expense_id').write({
                        'payment_ref_id': self.id,
                        'state': 'done',
                        })

            
            if self.processing_method == 'cheque':
                cheque_info_line = self.env['cheque.info.lines'].search([('cheque_no', '=', self.cheque_no),('info_id.bank_name', '=', self.journal_id.id),('info_id.state', '=', 'activated')],limit=1)
                if cheque_info_line:
                    cheque_info_line.write({
                        'expense_pay_to': self.expense_pay_to,
                        'expense_payment_id': self.id,
                        'pay_date': self.expense_date,
                        'cheque_state': self.state,
                        'page_state' : 'use',
                        })

        return True

