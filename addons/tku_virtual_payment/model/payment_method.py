from odoo import api, fields, models, _
from odoo.exceptions import UserError,Warning

class PosPaymentMethod(models.Model):
    _inherit = ['pos.payment.method']
    
    
    mubapay_payment = fields.Boolean(
        string='Mubapay Payment',
        default=False,)
