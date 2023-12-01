odoo.define('pos_custom_buttons.CustomTicketButtons', function (require) {
    'use strict';
    const { Gui } = require('point_of_sale.Gui');
    const PosComponent = require('point_of_sale.PosComponent');
    const { posbus } = require('point_of_sale.utils');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const { useListener } = require('web.custom_hooks');
    const Registries = require('point_of_sale.Registries');
    const PaymentScreen = require('point_of_sale.PaymentScreen');
    var rpc = require('web.rpc');
    var session = require('web.session');

    const CustomButtonPaymentScreen = (PaymentScreen) =>
        class extends PaymentScreen {
            constructor() {
                super(...arguments);
            }

            async onClick() {
                const self = this;
                const order = this.env.pos.get_order();

                if (order) {
                    const { confirmed: cardScanConfirmed, payload: { santriQR } } = await this.showCardScanPopup();

                    if (cardScanConfirmed) {
                        const { confirmed: pinConfirmed, payload: { pin_pass } } = await this.showPINPopup();

                        if (pinConfirmed) {
                            var hsl;
                            var keterangan;
                            var nama;
                            var data;
                            var user = session.user_id;

                            const orderLines = order.get_orderlines();
                            const totalPrice = orderLines.reduce((sum, orderLine) => sum + orderLine.get_price_with_tax(), 0);

                            // console.log("Card Scan Result:", santriQR);
                            // console.log("Pin:", pin_pass);

                            rpc.query({
                                model: 'mubapay.payment',
                                method: 'do_trx',
                                args: [totalPrice, santriQR, pin_pass, user]
                            }).then(function (result) {
                                hsl = result;   
                                keterangan = hsl['keterangan']  
                                data = hsl.data
                                nama = data.nama

                                Gui.showPopup("ConfirmPopup", {
                                    title: self.env._t(`${keterangan}`),
                                    body: self.env._t(`Nama: ${nama}
                                                   Saldo Terpotong: Rp.${totalPrice}.-`),
                                    confirmText: 'Ok',
                                    cancelText: 'Cancel',
                                });
                            });
                        } else {
                            Gui.showPopup("ErrorPopup", {
                                title: self.env._t('Error'),
                                body: self.env._t('PIN entry canceled.'),
                            });
                        }
                    } else {
                        Gui.showPopup("ErrorPopup", {
                            title: self.env._t('Error'),
                            body: self.env._t('Card scan canceled.'),
                        });
                    }
                } else {
                    Gui.showPopup("ErrorPopup", {
                        title: self.env._t('Error'),
                        body: self.env._t('No order found.'),
                    });
                }
            }

            async showCardScanPopup() {
                return new Promise((resolve) => {
                    const $popup = $(`<div style="position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); background-color: #fff; padding: 20px; border: 1px solid #ddd; box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.1); max-width: 300px; text-align: center;">
                        <span style="position: absolute; top: 10px; right: 10px; cursor: pointer; font-size: 20px;" id="scan-cancel">&times;</span>
                        <h5 style="margin-bottom: 20px;">Scan Kartu</h5>
                        <form style="display: flex; flex-direction: column; align-items: center;">
                            <div style="margin-bottom: 15px; width: 100%;">
                                <input type="text" style="width: 100%; padding: 8px; box-sizing: border-box;" id="scan-username" required autofocus>
                            </div>
                            <button type="button" style="background-color: #007bff; color: #fff; padding: 10px; border: none; cursor: pointer; width: 100%;" id="scan-confirm">Scan</button>
                        </form>
                        <script>document.getElementById("scan-username").focus();</script>
                    </div>`);   

                    // $popup.find('#scan-confirm').on('click', function () {
                    //     // const santriQR = $popup.find('#scan-username').val();
                    //     var vals = document.getElementById("scan-username")
                    //     var santriQR = vals.value
                    //     resolve({ confirmed: true, payload: { santriQR } });
                    //     $popup.modal('hide');
                    // });
                    
                    $popup.find('#scan-username').on('keyup', function () {
                        var vals = document.getElementById("scan-username")
                        var santriQR = vals.value
                        resolve({ confirmed: true, payload: { santriQR } });    
                        $popup.modal('hide');
                        // const santriQR = $popup.find('#scan-username').val();
                        if(santriQR.length === 64){
                            $popup.find('#scan-confirm').on('click', function () {
                                resolve({ confirmed: true, payload: { santriQR } });
                                $popup.modal('hide');
                            });                 
                        }
                    });

                    $popup.find('#scan-cancel').on('click', function (e) {
                        e.preventDefault();
                        resolve({ confirmed: false });
                        $popup.remove();
                    });
            
                    $popup.modal('show');
                });
            }

            async showPINPopup() {
                return new Promise((resolve) => {
                    const $popup = $(`<div style="position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); background-color: #fff; padding: 20px; border: 1px solid #ddd; box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.1); max-width: 300px; text-align: center;">
                    <span style="position: absolute; top: 10px; right: 10px; cursor: pointer; font-size: 20px;" id="login-cancel">&times;</span>
                    <h5 style="margin-bottom: 20px;">Login</h5>
                    <form style="display: flex; flex-direction: column; align-items: center;">
                        <div style="margin-bottom: 15px; width: 100%;">
                            <label for="login-username" style="display: block; margin-bottom: 5px; text-align: left;">PIN:</label>
                            <input type="password" style="width: 100%; padding: 8px; box-sizing: border-box;" id="login-username" required autofocus>
                        </div>
                        <button type="button" style="background-color: #007bff; color: #fff; padding: 10px; border: none; cursor: pointer; width: 100%;" id="login-confirm">Login</button>
                    </form>
                </div>`);

                    $popup.find('#login-confirm').on('click', function () {
                        const pin_pass = $popup.find('#login-username').val();
                        resolve({ confirmed: true, payload: { pin_pass } });
                        $popup.modal('hide');
                    });

                    $popup.find('#login-cancel').on('click', function (e) {
                        e.preventDefault();
                        resolve({ confirmed: false });
                        $popup.remove();
                    });

                    $popup.modal('show');
                });
            }
        }

    Registries.Component.extend(PaymentScreen, CustomButtonPaymentScreen);
    return CustomButtonPaymentScreen
});
