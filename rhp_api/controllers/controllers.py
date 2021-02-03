# -*- coding: utf-8 -*-
from odoo import http, fields
from odoo.http import request
import json
import base64
import requests
from ast import literal_eval
from datetime import datetime, timedelta
from ics import Calendar, Event
from werkzeug.urls import url_encode
from odoo.tools import html2plaintext
import pytz

class RhpApi(http.Controller):


    @http.route('/api/StartAppointment', type='json', auth="public", website=True)
    def start_appointment(self, **post):
        post_data = json.loads(request.httprequest.data)
        result = {}

        customer_name = post_data.get('Customer')
        street = post_data.get('Street')
        street2 = post_data.get('Street2')
        zip = post_data.get('Zip')
        city = post_data.get('City')
        country = post_data.get('Country')
        province = post_data.get('Province')

        if customer_name:
            #search
            new_res_partner = request.env['res.partner'].sudo().create({
                    'name': customer_name,
                    'street': street or '',
                    'street2': street2 or '',
                    'city': city or '',
                    'zip': zip or '',
                    'country_id': request.env['res.country'].search([('name', '=', country)]).id or None,
                    'state_id': request.env['res.country.state'].search([('name', '=', province)]).id or None,
                    })
            if new_res_partner:
                result['res.partner'] = new_res_partner.id
            #Create lead
            company_obj = request.env['res.company'].sudo().search([('name', '=', 'Unilux RHP')])
            new_crm_lead = request.env['crm.lead'].sudo().create({
                        'name': customer_name+"'s opportunity",
                        'type': 'opportunity',
                        'partner_id': result['res.partner'],
                        'active': True,
                        'company_id': company_obj.id if company_obj else 1
                     })
            if new_crm_lead:
                result['leadId'] = new_crm_lead.id

            #Get list manufacturer
            manufacturer_category_obj = request.env['res.partner.category'].sudo().search([('name', '=ilike', 'manufacturer')])
            
            manufacturer_obj = request.env['res.partner'].sudo().search([
                ('is_company', '=', True),
                ('category_id', 'in', [manufacturer_category_obj.id]),
            ])

            manufacturer_array = []
            for a in manufacturer_obj:
                temp = {}
                temp['Id'] = a.id
                temp['Name'] = a.name
                manufacturer_array.append(temp)
            result['manufacturer'] = manufacturer_array
        return result

    @http.route('/api/UploadImage', type='json', auth="public", website=True)
    def upload_image(self, **post):
        post_data = json.loads(request.httprequest.data)
        result = {}

        leadId = post_data.get('leadId')
        imgUrl = post_data.get('Image')
        manufacturer_name = post_data.get('Manufacturer')
        quantity = post_data.get('Quantity')
        size = post_data.get('Size')

        

        if leadId and imgUrl and manufacturer_name and quantity and size:
            #search LEAD
            lead_obj = request.env['crm.lead'].sudo().search([('id', '=', leadId)])
            if lead_obj:
                manufacturer_category_obj = request.env['res.partner.category'].sudo().search([('name', '=ilike', 'manufacturer')])
                manufacturer_obj = request.env['res.partner'].sudo().search([
                        ('is_company', '=', True),
                        ('category_id', 'in', [manufacturer_category_obj.id]),
                        ('name', '=', manufacturer_name),
                    ])

                company_obj = request.env['res.company'].sudo().search([('name', '=', 'Unilux RHP')])


                #convert URL to base64 and import and attach to the lead
                attachment_obj = request.env['ir.attachment'].sudo().search([('res_model', '=', 'crm.lead'), ('res_id', '=', lead_obj.id)])
                print(attachment_obj)
                number = len(attachment_obj)+1
                ir_attachment = request.env['ir.attachment'].sudo().create({
                        'name': lead_obj.name + ' ' + str(number),
                        'res_model': 'crm.lead',
                        'res_id': lead_obj.id,
                        'type': 'binary',
                        'datas': base64.b64encode(requests.get(imgUrl).content),
                        'res_partner_id': manufacturer_obj.id,
                        'quantity': quantity,
                        'size': size,
                        'company_id': company_obj.id if company_obj else 1
                     })
                if ir_attachment:
                    result['status'] = True
                else:
                    result['status'] = False
                #Get list product
                product_obj = request.env['product.product'].sudo().search([('company_id', '=', company_obj.id)])
                product_array = []
                #path_info = http.request.env['ir.config_parameter'].sudo().get_param('web.base.url')
                path_info = 'https://unilux-vfc-rhp-1894585.dev.odoo.com'

                for a in product_obj:
                    temp = {}
                    if a.default_code:
                        temp['Id'] = a.id
                        temp['Name'] = a.name
                        temp['Description'] = a.description_sale
                        temp['Price'] = a.lst_price
                        temp['Image'] = str(path_info)+'/web/image?model=product.product&field=image_128&id='+str(a.id)+'&unique=1'
                        temp['IsProduct'] = True
                        if a.default_code.find("RHPA") != -1:
                            temp['IsProduct'] = False
                        
                        product_array.append(temp)
                result['products'] = product_array
        return result
    

    @http.route('/api/UpdateProduct', type='json', auth="public", website=True)
    def upload_product(self, **post):
        post_data = json.loads(request.httprequest.data)
        result = {}

        leadId = post_data.get('leadId')
        manufacturer = post_data.get('manufacturer')
        product = literal_eval(post_data.get('product'))
        print(product)

        if leadId and manufacturer and product:
            #search LEAD
            lead_obj = request.env['crm.lead'].sudo().search([('id', '=', leadId)])
            company_obj = request.env['res.company'].sudo().search([('name', '=', 'Unilux RHP')])
            if lead_obj:
                #create quotation with those Products
                quotation = request.env['sale.order'].sudo().create({
                        'opportunity_id': lead_obj.id,
                        'partner_id': lead_obj.partner_id.id,
                        'team_id': lead_obj.team_id.id,
                        'campaign_id': lead_obj.campaign_id.id,
                        'medium_id': lead_obj.medium_id.id,
                        'origin': lead_obj.name,
                        'source_id': lead_obj.source_id.id,
                        'company_id': company_obj.id if company_obj else 1,
                        'tag_ids': [(6, 0, lead_obj.tag_ids.ids)],
                        'state': 'draft'
                     })
                #create sale.order.line
                for pro in product:
                    request.env['sale.order.line'].sudo().create({
                        'order_id': quotation.id,
                        'product_id': pro
                    })
                if quotation:
                    result['status'] = True
                else:
                    result['status'] = False
        return result

    @http.route('/api/UpdateLeadAndCreateAppointment', type='json', auth="public", website=True)
    def upload_lead_and_create_appointment(self, **post):
        post_data = json.loads(request.httprequest.data)
        result = {}

        lead = post_data.get('lead')
        appointment = post_data.get('appointment')

        if lead:
            #update res.partner
            res_partner_obj = request.env['res.partner'].sudo().search([('id', '=', lead.get('res.partner'))])
            res_partner_obj.write({
                'name': lead.get('FirstName') + ' ' + lead.get('SecondName'),
                'phone': lead.get('Phone'),
                'street': lead.get('Street'),
                'street2': lead.get('Street2'),
                'city': lead.get('City'),
                'zip': lead.get('Zip'),
                'country_id': request.env['res.country'].search([('name', '=', lead.get('Country'))]).id or None,
                'state_id': request.env['res.country.state'].search([('name', '=', lead.get('Province'))]).id or None,
                'email': lead.get('Email')
            }) 
            result['res.partner'] = res_partner_obj.id
            #update crm.lead?
            lead_obj = request.env['crm.lead'].sudo().search([('id', '=', lead.get('leadId'))])
            lead_obj.write({
                'name': lead.get('FirstName') + ' ' + lead.get('SecondName') + "'s opportunity",
                'partner_name': lead.get('FirstName') + ' ' + lead.get('SecondName'),
                'mobile': lead.get('Phone'),
                'street': lead.get('Street'),
                'street2': lead.get('Street2'),
                'city': lead.get('City'),
                'zip': lead.get('Zip'),
                'country_id': request.env['res.country'].search([('name', '=', lead.get('Country'))]).id or None,
            })
            result['leadId'] = lead_obj.id
            if appointment:
                appoinement_type = request.env['calendar.appointment.type'].sudo().search([], limit=1)

                datetime_api = datetime.strptime(appointment.get('DateTime'), '%Y-%m-%d %H:%M:%S')
                backend = pytz.timezone('UTC')
                frontend = pytz.timezone(appoinement_type.appointment_tz)
                offset = (frontend.localize(datetime_api) -  backend.localize(datetime_api).astimezone(frontend)).seconds/3600
                start = datetime_api + timedelta(hours=offset)
                end = start + timedelta(hours=appoinement_type.appointment_duration)
                date_start = start.strftime('%Y-%m-%d %H:%M:%S')
                date_end = end.strftime('%Y-%m-%d %H:%M:%S')

                google_start = start.strftime('%Y%m%dT%H%M%SZ')
                google_end = end.strftime('%Y%m%dT%H%M%SZ')
                print(google_start)
                print(google_end)

                calendar_appointment = request.env['calendar.event'].sudo().create({
                        'name': appointment.get('Name'),
                        'start': date_start,
                        'stop': date_end,
                        'partner_ids': [(6, 0, [res_partner_obj.id])],
                        'res_model': 'calendar.appointment.type',
                        'res_model_id': request.env['ir.model'].sudo().search([('model', '=', 'calendar.appointment.type')], limit=1).id,
                        
                        'res_id': request.env['calendar.appointment.type'].sudo().search([], limit=1).id,
                        'appointment_type_id': request.env['calendar.appointment.type'].sudo().search([], limit=1).id,
                        'opportunity_id': lead_obj.id,
                        'active': True,
                    })
                
                if calendar_appointment:
                    result['calendar.appointment'] = calendar_appointment.id
                    #Send Email
                    address = lead.get('Street') +  ' ' + lead.get('Street2') + ', ' + lead.get('City') + ', ' + lead.get('Zip') + ', ' + lead.get('Country')
                    template = request.env.ref('rhp_api.mail_template_appointment_create').sudo()
                    total = 0
                    quotation_lines = []
                    for order in lead_obj.order_ids:
                        if order.state in ('draft', 'sent'):
                            quotation_lines.append(order.order_line)
                            total += order.amount_total

                    #Email
                    details = "RHP Appointment: " + appointment.get('Name') + ' on ' + datetime.strptime(appointment.get('DateTime'), '%Y-%m-%d %H:%M:%S').strftime('%a %b %d, %Y %I:%M %p') + ' at ' + address
                    params = {
                        'action': 'TEMPLATE',
                        'text': 'RHP Appointment',
                        'dates': google_start + '/' + google_end,
                        'details': html2plaintext(details.encode('utf-8'))
                    }
                    if calendar_appointment.location:
                        params.update(location=calendar_appointment.location.replace('\n', ' '))
                    encoded_params = url_encode(params)
                    google_url = 'https://www.google.com/calendar/render?' + encoded_params
                    

                    email_values = {'date': datetime.strptime(appointment.get('DateTime'), '%Y-%m-%d %H:%M:%S').strftime('%a %b %d, %Y'),
                                    'time': datetime.strptime(appointment.get('DateTime'), '%Y-%m-%d %H:%M:%S').strftime('%I:%M %p'),
                                    'address': address,
                                    'quotation_lines': quotation_lines,
                                    'total': total,
                                    'google_url': google_url,
                                    }
                    template.write({'email_from': 'toan@syncoria.com'})
                    template.write({'email_to': appointment.get('Email')})

                    #Attachment
                    c = Calendar()
                    e = Event()
                    e.name = "RHP Appointment: "+ lead.get('FirstName') + ' ' + lead.get('SecondName')
                    e.begin = datetime.strptime(date_start, '%Y-%m-%d %H:%M:%S')
                    e.end = datetime.strptime(date_end, '%Y-%m-%d %H:%M:%S')
                    c.events.add(e)
                    c.events

                    company_obj = request.env['res.company'].sudo().search([('name', '=', 'Unilux RHP')])
                    attachment = request.env['ir.attachment'].sudo().create({
                        'name': 'RHP_' + lead_obj.name + '_Appointment.ics',
                        'res_model': 'calendar.event',
                        'res_id': calendar_appointment.id,
                        'type': 'binary',
                        'datas': base64.b64encode(bytes(str(c), 'utf-8')),
                        'company_id': company_obj.id if company_obj else 1
                     })
                    template.attachment_ids = [(6,0,[attachment.id])]
                    
                    #Link
                    
                    template.with_context(email_values).send_mail(calendar_appointment.id, force_send=True, email_values=None)
                    #END Send Email

                    result['status'] = True
                    return result
        result['status'] = False
        return result

    @http.route('/api/UpdateCustomer', type='json', auth="public", website=True)
    def upload_customer(self, **post):
        post_data = json.loads(request.httprequest.data)
        result = {}
        res_partner_obj = request.env['res.partner'].sudo().search([('id', '=', post_data.get('res.partner'))])
        street = post_data.get('Street')
        street2 = post_data.get('Street2')
        zip = post_data.get('Zip')
        city = post_data.get('City')
        country = post_data.get('Country')
        province = post_data.get('Province')
        phone = post_data.get('Phone')
        email = post_data.get('Email')
        additional_detail = post_data.get('AdditionalDetail')

        if res_partner_obj:
            #update res.partner
            res_partner_obj.write({
                'street': street,
                'street2': street2,
                'city': city,
                'zip': zip,
                'country_id': request.env['res.country'].search([('name', '=', country)]).id or None,
                'state_id': request.env['res.country.state'].search([('name', '=', province)]).id or None,
                'phone': phone,
                'email': email,
                'comment': additional_detail,
            }) 
            result['res.partner'] = res_partner_obj.id
            result['status'] = True
            return result
        result['status'] = False
        return result
    
    @http.route('/api/GetProducts', type='http', auth="public", methods=['GET'], website=True)
    def get_products(self, **get):
        company_obj = request.env['res.company'].sudo().search([('name', '=', 'Unilux RHP')])
        product_obj = request.env['product.product'].sudo().search([('company_id', '=', company_obj.id)])
        product_array = []
        result = {}
        # path_info = http.request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        path_info = 'https://unilux-vfc-rhp-1894585.dev.odoo.com'
        for a in product_obj:
            temp = {}
            if a.default_code:
                temp['Id'] = a.id
                temp['Name'] = a.name
                temp['Description'] = a.description_sale
                temp['Price'] = a.lst_price
                temp['Image'] = str(path_info)+'/web/image?model=product.product&field=image_128&id='+str(a.id)+'&unique=1'
                temp['IsProduct'] = True
                if a.default_code.find("RHPA") != -1:
                    temp['IsProduct'] = False
                
                product_array.append(temp)
        result['products'] = product_array
        return json.dumps(result)