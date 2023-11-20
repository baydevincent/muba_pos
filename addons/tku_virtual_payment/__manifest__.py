# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'TKU Payment Gateway',
    'version': '1.0',
    'category': 'Accounting',
    'sequence': 10,
    'summary': 'Manage Monthly Budgeting for andara',
    'description': "",
    'website': 'https://bydev.tech',
    'qweb': [
        'static/src/xml/mubapay_payment_button_view.xml',
    ],
    'depends': ['base', 'point_of_sale'],
    
    'data': [
        'security/ir.model.access.csv',
        'views/payment_method_pos_view.xml',
        'views/allowed_device_id_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False
}