odoo.define('tku_zero_stock.pos', function(require) {
	"use strict";

	const models = require('point_of_sale.models');
	var model_list = models.PosModel.prototype.models;
	var product_model = null;
	var exports = {};

	models.load_fields('product.product', ['qty_available','type']);


});
