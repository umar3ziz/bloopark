# -*- coding: utf-8 -*-
#################################################################################
# Author      : Omar Abdelaziz <omar_3ziz@hotmail.com>
# Copyright(c): Developer -Omar Abdelaziz-
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#################################################################################

""" Wizards to enable Exchanges"""

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round, float_is_zero


class StockExchangeLine(models.TransientModel):
    _name = "stock.exchange.line"
    _rec_name = 'product_id'
    _description = 'Exchange Picking Line'

    product_id = fields.Many2one(
        'product.product', string="Product",
        required=True, domain="[('id', '=', product_id)]"
    )
    exchange_product_id = fields.Many2one(
        'product.product', string="Exchange Product",
        required=False, domain="[('id', '!=', product_id)]"
    )
    quantity = fields.Float(
        "Quantity", digits=dp.get_precision('Product Unit of Measure'), required=True
    )
    price_unit = fields.Float(
        string='Unit Price', required=False,
        digits=dp.get_precision('Product Price')
    )
    currency_id = fields.Many2one('res.currency')
    price_subtotal = fields.Monetary(
        compute='_compute_amount',
        string='Subtotal',
        readonly=True, store=True
    )
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure')
    exchange_id = fields.Many2one('stock.exchange', string="Wizard")
    move_id = fields.Many2one('stock.move', "Move")

    @api.depends('quantity', 'price_unit')
    def _compute_amount(self):
        """
        Compute the subtotal to be able to compare the exchanged prices.
        """
        for line in self:
            line.update({
                'price_subtotal': line.price_unit * line.quantity,
            })

    @api.onchange('exchange_product_id')
    def _onchange_exchange_product(self):
        """ Onchange exchange_product_id to get line values """
        values = {
                'quantity': False,
                'price_unit': False,
                'uom_id': False,
            }
        line = self.move_id.sale_line_id or self.move_id.purchase_line_id
        if self.exchange_product_id:
            values.update({
                'quantity': self.move_id.product_uom_qty,
                'price_unit': self.exchange_product_id.lst_price,
                'uom_id': self.exchange_product_id.uom_id.id,
            })
        else:
            values.update({
                'quantity': self.move_id.product_uom_qty,
                'price_unit': line.price_unit,
                'uom_id': line.product_uom.id,
            })
        self.update(values)


class StockExchange(models.TransientModel):
    _name = 'stock.exchange'
    _description = 'Delivery Exchange'

    picking_id = fields.Many2one('stock.picking')
    exchange_line_ids = fields.One2many('stock.exchange.line', 'exchange_id', 'Moves')
    location_id = fields.Many2one(
        'stock.location', 'Exchange Location',
        domain="['|', ('exchange_location', '=', True), ('return_location', '=', True)]"
    )

    @api.model
    def default_get(self, fields):
        """
            Override to set default values for the new exchange lines
        """
        if len(self.env.context.get('active_ids', list())) > 1:
            raise UserError(_("You may only exchange one picking at a time."))
        res = super(StockExchange, self).default_get(fields)

        exchange_line_ids = []
        picking = self.env['stock.picking'].browse(self.env.context.get('active_id'))
        if picking:
            res.update({'picking_id': picking.id})
            if picking.state != 'done':
                raise UserError(_("You may only exchange Done pickings."))
            for move in picking.move_lines:
                if move.scrapped or move.exchanged:
                    continue
                quantity = move.product_qty - sum(
                    move.move_dest_ids.filtered(
                        lambda m: m.state in ['partially_available', 'assigned', 'done']
                    ).mapped('move_line_ids').mapped('product_qty')
                )
                quantity = float_round(
                    quantity, precision_rounding=move.product_uom.rounding
                )
                # exchange should be from sale or purchase
                line = move.sale_line_id or move.purchase_line_id
                if line:
                    exchange_line_ids.append(
                        (0, 0, {
                            'product_id': move.product_id.id,
                            'quantity': quantity,
                            'move_id': move.id,
                            'price_unit': line.price_unit,
                            'uom_id': move.product_uom.id,
                            'price_subtotal': quantity * line.price_unit,
                            'currency_id': line.currency_id.id
                        })
                    )

            if not exchange_line_ids:
                raise UserError(_(
                    "No products to exchange (only lines in Done state and not fully "
                    "exchanged yet can be exchange)."
                ))
            if 'exchange_line_ids' in fields:
                res.update({'exchange_line_ids': exchange_line_ids})
            if 'location_id' in fields:
                location_id = picking.location_id.id
                exchange_picking_type = picking.picking_type_id.exchange_picking_type_id
                dest_location = exchange_picking_type.default_location_dest_id
                if dest_location.exchange_location:
                    location_id = dest_location.id
                res['location_id'] = location_id
        return res

    def _prepare_move_default_values(self, exchange_line, new_picking):
        """
        Prepare new move line dict values
        :param exchange_line: move related Exchange line obj
        :param new_picking: Obj of the new created picking
        :return: Dict of values
        """
        product = exchange_line.exchange_product_id or exchange_line.product_id
        location = self.location_id or exchange_line.move_id.location_id
        vals = {
            'product_id': product.id,
            'product_uom_qty': exchange_line.quantity,
            'product_uom': exchange_line.uom_id.id,
            'picking_id': new_picking.id,
            'state': 'draft',
            'date_expected': fields.Datetime.now(),
            'location_id': exchange_line.move_id.location_dest_id.id,
            'location_dest_id': location.id,
            'picking_type_id': new_picking.picking_type_id.id,
            'warehouse_id': self.picking_id.picking_type_id.warehouse_id.id,
            'origin_exchange_move_id': exchange_line.move_id.id,
            'procure_method': 'make_to_stock',
        }
        return vals

    def _create_exchanges(self):
        """
            To finalize data and create the Exchanged picking and Invoices if necessary
        :return: Int of the new created picking ID, Int of the picking type ID
        """
        # create new picking for exchanged products
        if self.picking_id.picking_type_id.exchange_picking_type_id:
            picking_type_id = self.picking_id.picking_type_id.exchange_picking_type_id.id
        elif self.picking_id.picking_type_id.return_picking_type_id:
            picking_type_id = self.picking_id.picking_type_id.return_picking_type_id.id
        else:
            picking_type_id = self.picking_id.picking_type_id.id
        moves = self.picking_id.move_ids_without_package
        purchase_lines = moves.mapped('purchase_line_id')
        purchase_order = purchase_lines.mapped('order_id')
        new_picking = self.picking_id.copy({
            'move_lines': [],
            'sale_id': False,
            'picking_type_id': picking_type_id,
            'exchange_sale_id': self.picking_id.sale_id.id,
            'exchange_purchase_id': purchase_order and purchase_order[0].id,
            'state': 'draft',
            'origin': _("Exchange of %s") % self.picking_id.name,
            'location_id': self.picking_id.location_dest_id.id,
            'location_dest_id': self.location_id.id
        })
        new_picking.message_post_with_view(
            'mail.message_origin_link', values={
                'self': new_picking, 'origin': self.picking_id
            }, subtype_id=self.env.ref('mail.mt_note').id
        )
        exchanged_lines = 0
        invoices_values = []
        for exchange_line in self.exchange_line_ids:
            if not exchange_line.move_id:
                raise UserError(_(
                    "You have manually created product lines, "
                    "please delete them to proceed."
                ))
            if not float_is_zero(
                    exchange_line.quantity,
                    precision_rounding=exchange_line.uom_id.rounding
            ):
                exchanged_lines += 1
                vals = self._prepare_move_default_values(exchange_line, new_picking)
                move = exchange_line.move_id.copy(vals)
                exchange_line.move_id.exchanged = True
                val = {'exchange_move_id': move.id}
                line = move.sale_line_id or move.purchase_line_id
                invoice_value = self._prepare_invoice_lines(exchange_line, line)
                if invoice_value:
                    invoices_values.append(invoice_value)
                line.write(val)
        if not exchanged_lines:
            raise UserError(_("Please specify at least one non-zero quantity."))
        if invoices_values:
            self.action_create_invoices(invoices_values)
        new_picking.action_confirm()
        new_picking.action_assign()
        return new_picking.id, picking_type_id

    def _prepare_invoice_lines(self, exchange_line, order_line):
        """
            Prepare new invoice lines dict values
        :param exchange_line: move related Exchange line obj
        :param order_line: Obj of Sale or purchase line the related to this invoice line
        :return: Dict of values
        """
        invoice_type = {
            'sale.order.line': {
                'higher': 'out_invoice', 'lower': 'out_refund',
                'type': 'sale', 'field': 'exchange_sale_line_id'
            },
            'purchase.order.line': {
                'higher': 'in_invoice', 'lower': 'in_refund',
                'type': 'purchase', 'field': 'exchange_purchase_line_id'
            },
        }
        product = exchange_line.exchange_product_id or exchange_line.product_id
        data = {
            'invoice_type': False,
            'values': {
                'product_id': product.id,
                'quantity': exchange_line.quantity,
                'name': 'Exchange for [%s]' % exchange_line.product_id.display_name,
            }
        }
        if exchange_line.exchange_product_id or \
                exchange_line.price_subtotal > order_line.price_subtotal:
            data['invoice_type'] = invoice_type[order_line._name]['higher']
        elif exchange_line.price_subtotal < order_line.price_subtotal:
            data['invoice_type'] = invoice_type[order_line._name]['lower']
        else:
            return {}
        data[invoice_type[order_line._name]['type']] = order_line.order_id
        data['values'][invoice_type[order_line._name]['field']] = order_line.id
        data['values']['price_unit'] = exchange_line.price_unit
        # TODO i think we should take the different between prices NOT the all price
            # abs(exchange_line.price_unit - order_line.price_unit)
        return data

    @api.multi
    def action_create_invoices(self, data):
        """
            Clean the incoming data and specify each line with its invoice types
        :param data: list of values that needed to create invoice lines
        :return: None
        """
        invoice_obj = self.env['account.invoice']
        values = {}
        for val in data:
            values.setdefault(val['invoice_type'], {
                'order': val.get('sale', val.get('purchase')),
                'values': []
            })
            values[val['invoice_type']]['values'].append((0, 0, val['values']))

        for inv_type, inv_data in values.items():
            invoice = invoice_obj.new(self._prepare_invoice(inv_type))
            invoice._onchange_partner_id()
            inv = invoice._convert_to_write({
                name: invoice[name] for name in invoice._cache
            })
            for _, _, line in inv_data['values']:
                line['account_id'] = inv['account_id']
            inv['invoice_line_ids'] = inv_data['values']
            new_invoice = invoice_obj.sudo().create(inv)
            new_invoice.action_invoice_open()
            inv_data['order'].write({
                'exchange_invoice_ids': [(4, new_invoice.id)]
            })

    def _prepare_invoice(self, invoice_type):
        """
        Prepare the dict of values to create the new invoice for a Exchange move.
        """
        return {
            'partner_id': self.picking_id.partner_id.id,
            'company_id': self.picking_id.company_id.id,
            'type': invoice_type,
            'name': _('Exchange Inv for %s') % self.picking_id.name,
            'currency_id': self.env.user.company_id.currency_id.id,
        }

    def create_exchanges(self):
        """
        :return: Action for the final exchange Picking
        """
        for wizard in self:
            new_picking_id, pick_type_id = wizard._create_exchanges()
        # Override the context to disable all the potential filters
        # that could have been set previously
        ctx = dict(self.env.context)
        ctx.update({
            'search_default_picking_type_id': pick_type_id,
            'search_default_draft': False,
            'search_default_assigned': False,
            'search_default_confirmed': False,
            'search_default_ready': False,
            'search_default_late': False,
            'search_default_available': False,
        })
        return {
            'name': _('Exchanged Picking'),
            'view_type': 'form',
            'view_mode': 'form,tree,calendar',
            'res_model': 'stock.picking',
            'res_id': new_picking_id,
            'type': 'ir.actions.act_window',
            'context': ctx,
        }
