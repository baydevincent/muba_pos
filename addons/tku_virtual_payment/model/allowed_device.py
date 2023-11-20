from odoo import models, fields
import uuid
import hashlib

class ResUsersInherit(models.Model):
    _inherit = 'res.users'

    allowed_device = fields.One2many('allowed.device', 'user', string='IP')


class AllowedDevice(models.Model):
    _name = 'allowed.device'

    user = fields.Many2one('res.users', string='User')
    merchant_user = fields.Char(string='Merchant User')
    device_id = fields.Char(string='Device ID')
    passwd = fields.Char(string='Password')
    