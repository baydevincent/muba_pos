'''
Created on Mar 08, 2023

@author: BYDEV
'''

from odoo import api, fields, models, _

class PurchaseOrder(models.Model):
    _inherit = ['purchase.order']
    
    def print_jasper_sale_order(self):
        data = {}
        data.update({'parameters': {
                'customer_name': self.partner_id.name,
            'order_name': self.name,
                }
        })
        return {
            'data': data,
                'type': 'ir.actions.report',
            'report_name': 'sale_order_report_with_parameter',
            'report_type': 'jasper',
        }
