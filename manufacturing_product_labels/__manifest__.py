# -*- coding: utf-8 -*-
{
    'name': "manufacturing_product_labels",

    'summary': """
        Manufacturing product labels generator""",

    'description': """
        Manufacturing product labels generator. 
    """,

    'author': "Ergo Ventures Pvt Ltd.",
    'website': "http://ergo-ventures.com/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Report',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','mrp'],

    # always loaded
    'data': [
        'views/report_manufacturing_product_labels.xml',
        'report/report_manufacturing_product_labels.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
}