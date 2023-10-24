from odoo import api, fields, models, _


class PosConfig(models.Model):
	_inherit = "pos.config"

	restrict_zero_stock = fields.Boolean(string='Restrict Zero Stock')

