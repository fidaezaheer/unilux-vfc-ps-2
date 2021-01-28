# -*- coding: utf-8 -*-

from odoo import models, fields, api
import pytz
from datetime import datetime, timedelta, time
from dateutil import rrule
from dateutil.relativedelta import relativedelta
import calendar as cal
from babel.dates import format_datetime
from odoo.tools.misc import get_lang

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


class CalendarAppointmentTypeInherit(models.Model):
    _inherit = "calendar.appointment.type"

    def _get_appointment_slots(self, timezone, employee=None):
        print("**** OUR _get_appointment_slots")
        """ Fetch available slots to book an appointment
            :param timezone: timezone string e.g.: 'Europe/Brussels' or 'Etc/GMT+1'
            :param employee: if set will only check available slots for this employee
            :returns: list of dicts (1 per month) containing available slots per day per week.
                      complex structure used to simplify rendering of template
        """
        self.ensure_one()
        appt_tz = pytz.timezone(self.appointment_tz)
        requested_tz = pytz.timezone(timezone)
        first_day = requested_tz.fromutc(datetime.utcnow() + relativedelta(hours=self.min_schedule_hours))
        last_day = requested_tz.fromutc(datetime.utcnow() + relativedelta(days=self.max_schedule_days))

        # Compute available slots (ordered)
        slots = self._slots_generate(first_day.astimezone(appt_tz), last_day.astimezone(appt_tz), timezone)
        if not employee or employee in self.employee_ids:
            self._slots_available(slots, first_day.astimezone(pytz.UTC), last_day.astimezone(pytz.UTC), employee)

        # Compute calendar rendering and inject available slots
        today = requested_tz.fromutc(datetime.utcnow())
        start = today
        month_dates_calendar = cal.Calendar(0).monthdatescalendar
        months = []
        while (start.year, start.month) <= (last_day.year, last_day.month):
            dates = month_dates_calendar(start.year, start.month)
            for week_index, week in enumerate(dates):
                for day_index, day in enumerate(week):
                    mute_cls = weekend_cls = today_cls = None
                    today_slots = []
                    if day.weekday() in (cal.SUNDAY, cal.SATURDAY):
                        weekend_cls = 'o_weekend'
                    if day == today.date() and day.month == today.month:
                        today_cls = 'o_today'
                    if day.month != start.month:
                        mute_cls = 'text-muted o_mute_day'
                    else:
                        # slots are ordered, so check all unprocessed slots from until > day
                        while slots and (slots[0][timezone][0].date() <= day):
                            if (slots[0][timezone][0].date() == day) and ('employee_id' in slots[0]):
                                today_slots.append({
                                    'employee_id': slots[0]['employee_id'].id,
                                    'datetime': slots[0][timezone][0].strftime('%Y-%m-%d %H:%M:%S'),
                                    'hours': slots[0][timezone][0].strftime('%I:%M %p')
                                })
                            slots.pop(0)
                    dates[week_index][day_index] = {
                        'day': day,
                        'slots': today_slots,
                        'mute_cls': mute_cls,
                        'weekend_cls': weekend_cls,
                        'today_cls': today_cls
                    }

            months.append({
                'month': format_datetime(start, 'MMMM Y', locale=get_lang(self.env).code),
                'weeks': dates
            })
            start = start + relativedelta(months=1)
        return months