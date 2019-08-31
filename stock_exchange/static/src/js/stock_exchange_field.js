odoo.define('stock_exchange.exchange', function (require) {
    "use strict";

    var AbstractField = require('web.AbstractField');
    var core = require('web.core');
    var field_registry = require('web.field_registry');

    var QWeb = core.qweb;


    var ShowExchangeLineWidget = AbstractField.extend({
        supportedFieldTypes: ['char'],

        //--------------------------------------------------------------------------
        // Public
        //--------------------------------------------------------------------------

        /**
         * @override
         * @returns {boolean}
         */
        isSet: function() {
            return true;
        },

        //--------------------------------------------------------------------------
        // Private
        //--------------------------------------------------------------------------

        /**
         * @private
         * @override
         */
        _render: function() {
            var self = this;
            var info = JSON.parse(this.value);
            if (!info) {
                this.$el.html('');
                return;
            }
            this.$el.html(QWeb.render('ShowExchangeIcon', {
                exchange: info.exchange,
                title: info.title
            }));
            this.$('.js_exchange_info').hover(function(){
                var content = info.content;
                var options = {
                    content: function () {
                        var $content = $(QWeb.render('ExchangePopOver', {
                            lines: content,
                            invoices: info.invoices,
                            pickings: info.pickings
                        }));
                        $content.filter('.js_open_pickings').on('click', self._onOpenPickingAction.bind(self));
                        $content.filter('.js_open_invoices').on('click', self._onOpenInvoiceAction.bind(self));
                        return $content;
                    },
                    html: true,
                    placement: 'bottom',
                    title: 'Exchange Information',
                    trigger: 'focus',
                    delay: { "show": 0, "hide": 100 },
                    container: $(this).parent()
                };
                $(this).popover(options);

            });
        },

        //--------------------------------------------------------------------------
        // Handlers
        //--------------------------------------------------------------------------

        _onOpenAction: function (Model, object) {
            var Ids = object.ids;
            var title = object.title;
            if (Model && Ids) {
                this.do_action({
                    type: 'ir.actions.act_window',
                    name: title,
                    res_model: Model,
                    views: [[object.ListId || false, 'list'], [ object.FormId || false, 'form']],
                    view_type: 'list',
                    view_mode: 'list',
                    domain: [['id', 'in', Ids]]
                });
            }
        },
        _onOpenInvoiceAction: function () {
            var model = 'account.invoice';
            var info = JSON.parse(this.value);
            this._onOpenAction(model, info.invoices)
        },
        _onOpenPickingAction: function () {
            var model = 'stock.picking';
            var info = JSON.parse(this.value);
            this._onOpenAction(model, info.pickings)
        }
    });

    field_registry.add('exchange', ShowExchangeLineWidget);

    return {
        ShowExchangeLineWidget: ShowExchangeLineWidget
    };

});
