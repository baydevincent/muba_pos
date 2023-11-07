'''
Created on Mar 08, 2023

@author: BYDEV
'''

from odoo import api, fields, models, _
from odoo.exceptions import UserError,Warning
import midtransclient
from random import randint
import requests


snap = midtransclient.Snap(
    is_production=False,
    server_key='SB-Mid-server-wffqTHANHuCka9HbeAMNAMV7',
    client_key='SB-Mid-client-zQKfwZ4u4tSEKiCZ'
)

def random_with_N_digits(n):
    range_start = 10**(n-1)
    range_end = (10**n)-1
        
    return randint(range_start, range_end)

class VirtualPayment(models.Model):
    _name = "virtual.payment"
    _description = "Create Virtual Payment"
                
    name = fields.Char(string='Order Reference', required=True, copy=False, states={'draft': [('readonly', False)]}, index=True, default=lambda self: _('New'))
    user_id = fields.Many2one('res.users', string='Responsible', required=True, states={'done': [('readonly', True)], 'confirmed': [('readonly', True)]})
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
        ], string='Status', readonly=True, copy=False, index=True, tracking=3, default='draft')
    date_order = fields.Datetime(string='Tanggal Order', 
                                 required=True, readonly=True, index=True, 
                                 states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, 
                                 copy=False, default=fields.Datetime.now)
    topup_amount = fields.Integer(string='Amount')
    external_id = fields.Char(string='Kode Transaksi', readonly=True)
    payment_status = fields.Char(string='Payment Status')
    payment_link = fields.Char(string='Payment Link', readonly=True)
    
    @api.model
    def create(self,vals):
        vals = vals
        name = self.env['ir.sequence'].next_by_code('va.payment')
        sequence_pembayaran = 'BCA-Fixed - ' + str(random_with_N_digits(8))
        if vals['name'] == 'New':      
            vals.update({'name' : name,
                         'external_id' : sequence_pembayaran,
                         })
        result = super(VirtualPayment, self).create(vals)
        return result
        
    def bayar(self):
        param = {
        "transaction_details": {
            "order_id": self['external_id'],
            "gross_amount": self['topup_amount']
        }, "credit_card":{
            "secure" : True
            }
        }
        
        transaction = snap.create_transaction(param)
        # transaction token
        transaction_token = transaction['token']
        print('transaction_token:')
        print(transaction_token)
        
        # transaction redirect url
        transaction_redirect_url = transaction['redirect_url']
        print('transaction_redirect_url:')
        print(transaction_redirect_url)
        
        self.write({'payment_link': transaction_redirect_url})
           
        return {                   
                  'name'     : 'Payment',
                  'res_model': 'ir.actions.act_url',
                  'type'     : 'ir.actions.act_url',
                  'target'   : 'new',
                  'url'      : transaction_redirect_url
               }
        
        
        

        
        
        
        
    
        
        

    