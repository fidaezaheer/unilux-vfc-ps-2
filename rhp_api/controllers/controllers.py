# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json
import base64
import requests
from ast import literal_eval
from datetime import datetime

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

        if customer_name and (street or street2) and zip and city and country:
            #search
            country_obj = request.env['res.country'].search([('name', '=', country)])
            
            res_partner_obj = request.env['res.partner'].sudo().search([
                ('name', '=', customer_name), 
                ('street', '=', street), 
                ('street2', '=', street2),
                ('city', '=', city),
                ('zip', '=', zip),
                ('country_id', '=', country_obj.id),
            ], limit=1)
            #not exist
                #create
            #else
                #return 
            if res_partner_obj:
                result['res.partner'] = res_partner_obj.id
            else:
                new_res_partner = request.env['res.partner'].sudo().create({
                        'name': customer_name,
                        'street': street,
                        'street2': street2,
                        'city': city,
                        'zip': zip,
                        'country_id': country_obj.id,
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
            
            
            print("manufacturer_category_obj")
            print(manufacturer_category_obj)
            manufacturer_obj = request.env['res.partner'].sudo().search([
                ('is_company', '=', True),
                ('category_id', 'in', [manufacturer_category_obj.id]),
            ])
            print("manufacturer_obj")
            print(manufacturer_obj)


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

        if leadId and imgUrl:
            #search LEAD
            lead_obj = request.env['crm.lead'].sudo().search([('id', '=', leadId)])
            if lead_obj:
                #check URL
                #convert URL to base64 and import and attach to the lead
                attachment_obj = request.env['ir.attachment'].sudo().search([('res_model', '=', 'crm.lead'), ('res_id', '=', lead_obj.id)])
                print(attachment_obj)
                number = len(attachment_obj)+1
                ir_attachment = request.env['ir.attachment'].sudo().create({
                        'name': lead_obj.name + ' ' + str(number),
                        'res_model': 'crm.lead',
                        'res_id': lead_obj.id,
                        'type': 'binary',
                        'datas': base64.b64encode(requests.get(imgUrl).content)
                     })
                if ir_attachment:
                    result['status'] = True
                else:
                    result['status'] = False
                #Get list product
                product_obj = request.env['product.product'].sudo().search([])
                product_array = []
                path_info = http.request.env['ir.config_parameter'].sudo().get_param('web.base.url')

                for a in product_obj:
                    temp = {}
                    temp['Id'] = a.id
                    temp['Name'] = a.name
                    temp['Description'] = a.description_sale
                    temp['Price'] = a.lst_price
                    temp['Image'] = str(path_info)+'/web/image?model=product.product&field=image_128&id='+str(a.id)+'&unique=1'
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
                        'company_id': lead_obj.company_id.id or self.env.company.id,
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
        datetime_object = datetime.strptime(appointment.get('DateTime'), '%a %b %d, %Y, %I:%M:%S %p')

        print(datetime_object)

        if lead:
            #update res.partner
            country_obj = request.env['res.country'].search([('name', '=', lead.get('Country'))])
            res_partner_obj = request.env['res.partner'].sudo().search([('id', '=', lead.get('res.partner'))])
            res_partner_obj.write({
                'name': lead.get('FirstName') + ' ' + lead.get('SecondName'),
                'phone': lead.get('Phone'),
                'street': lead.get('Street'),
                'street2': lead.get('Street2'),
                'city': lead.get('City'),
                'zip': lead.get('Zip'),
                'country_id': country_obj.id,
                'email': lead.get('Email')
            }) 
            result['res.partner'] = res_partner_obj.id
            #update crm.lead?
            lead_obj = request.env['crm.lead'].sudo().search([('id', '=', lead.get('leadId'))])
            lead_obj.write({
                'partner_name': lead.get('FirstName') + ' ' + lead.get('SecondName'),
                'mobile': lead.get('Phone'),
                'street': lead.get('Street'),
                'street2': lead.get('Street2'),
                'city': lead.get('City'),
                'zip': lead.get('Zip'),
                'country_id': country_obj.id,
            })
            result['leadId'] = lead_obj.id
            if appointment:
                calendar_appointment = request.env['calendar.event'].sudo().create({
                        'name': appointment.get('Name'),
                        'start': datetime.strptime(appointment.get('DateTime'), '%a %b %d, %Y, %I:%M:%S %p'),
                        'stop': datetime.strptime(appointment.get('DateTime'), '%a %b %d, %Y, %I:%M:%S %p'),
                        'partner_ids': [(6, 0, [res_partner_obj.id])],
                        'res_model': 'crm.lead',
                        'res_model_id': request.env['ir.model'].sudo().search([('model', '=', 'crm.lead')], limit=1).id,
                        'res_id': lead_obj.id,
                        'opportunity_id': lead_obj.id,
                        'active': True,
                    })
                if calendar_appointment:
                    result['calendar.appointment'] = calendar_appointment.id
                    result['status'] = True
                    return result
        result['status'] = False
        return result