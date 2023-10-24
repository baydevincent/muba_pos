odoo.define('tku_zero_stock.productScreen', function(require) {
	"use strict";

	const Registries = require('point_of_sale.Registries');
	const ProductScreen = require('point_of_sale.ProductScreen');
	var rpc = require('web.rpc')

	const NewProductScreen = (ProductScreen) =>
		class extends ProductScreen {
			constructor() {
				super(...arguments);
			}
			async _onClickPay() {
				var self = this;
				let order = this.env.pos.get_order();
				let lines = order.get_orderlines();
				let pos_config = self.env.pos.config;				
				let call_super = true;
				var config_id=self.env.pos.config.id;
				let prod_used_qty = {};
				let restrict = false;
				if(pos_config.restrict_zero_stock){
					$.each(lines, function( i, line ){
						let prd = line.product;
						if (prd.type == 'product'){
							if(prd.id in prod_used_qty){
								let old_qty = prod_used_qty[prd.id][1];
								prod_used_qty[prd.id] = [prd.qty_available,line.quantity+old_qty]
							}else{
								prod_used_qty[prd.id] = [prd.qty_available,line.quantity]
							}
						}
						if (prd.type == 'product'){
							if(prd.qty_available <= 0){
								restrict = true;
								call_super = false;
								let wrning = '['+ prd.display_name + '] Stock kosong, Pastikan produk yang di transaksikan memiliki Stock.';
								self.showPopup('ErrorPopup', {
									title: self.env._t('Stock Kosong!'),
									body: self.env._t(wrning),
								});
							}
						}
					});
					if(restrict === false){
						$.each(prod_used_qty, function( i, pq ){
							let product = self.env.pos.db.get_product_by_id(i);
							let check = pq[0] - pq[1];
							let wrning = product.display_name + ' Stock kosong, Pastikan produk yang di transaksikan memiliki Stock.';
							if (product.type == 'product'){
								if (check < 0){
									call_super = false;
									self.showPopup('ErrorPopup', {
										title: self.env._t('Order ditolak'),
										body: self.env._t(wrning),
									});
								}
							}
						});
					}	
				}
				if(call_super){
					super._onClickPay();
				}
			}
		};

	Registries.Component.extend(ProductScreen, NewProductScreen);

	return ProductScreen;

});
