# -*- coding: utf-8 -*-
{
    'name': "Unilux RHP APIs",

    'summary': "",

    'description': "",

    'author': "Syncoria",
    'website': "http://www.syncoria.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'crm', 'website_calendar', 'sale'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/calendar_template.xml',
        'views/email_appointment_template.xml',
        # 'views/attachment_view.xml'
    ],
    
}   