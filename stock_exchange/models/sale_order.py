# -*- coding: utf-8 -*-
#################################################################################
# Author      : Omar Abdelaziz <omar_3ziz@hotmail.com>
# Copyright(c): Developer -Omar Abdelaziz-
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#################################################################################
""" This Module For Sales """

import json
from odoo.tools import date_utils
from odoo import models, fields, api, _


class SaleOrder(models.Model):
    """ sale.order Model to Connect Sales with all its pickings and invoices """
    _inherit = 'sale.order'

    exchange_picking_ids = fields.One2many(
        'stock.picking', 'exchange_sale_id', string='Exchanged Pickings'
    )
    exchange_invoice_ids = fields.Many2many(
        'account.invoice', string='Exchange Invoices',
        copy=False, help='Invoices that created by the Exchange'
    )
    exchange_widget = fields.Text(compute='_get_exchange_info_JSON')

    @api.one
    @api.depends('order_line.exchange_move_id')
    def _get_exchange_info_JSON(self):
        self.exchange_widget = json.dumps(False)
        info = {
            'title': _('Exchange Info'),
            'exchange': bool(self.exchange_picking_ids),
            'invoices': {
                'title': _('Invoices/Refunds'),
                'ids': self.exchange_invoice_ids.ids,
                'ListId': self.env.ref('account.invoice_tree').id,
                'FormId': self.env.ref('account.invoice_form').id,
            },
            'pickings': {
                'title': _('Receipts'),
                'ids': self.exchange_picking_ids.ids,
                'ListId': self.env.ref('stock.vpicktree').id,
                'FormId': self.env.ref('stock.view_picking_form').id,
            },
            'content': self._get_exchanges_data()}
        self.exchange_widget = json.dumps(info, default=date_utils.json_default)

    def _get_exchanges_data(self):
        inv_line_obj = self.env['account.invoice.line']
        list_values = []
        for move in self.exchange_picking_ids.mapped('move_ids_without_package'):
            if move.sale_line_id:
                inv_line = inv_line_obj.search([
                    ('exchange_sale_line_id', '=', move.sale_line_id.id)
                ])
                values = {
                    'product': move.product_id.display_name,
                    'qty': move.product_qty,
                    'invoice': inv_line.invoice_id.number,
                    'price': (inv_line or move.sale_line_id).price_unit,
                    'total': (inv_line or move.sale_line_id).price_total,
                    'currency': (inv_line or move.sale_line_id).currency_id.symbol,
                }
                list_values.append(values)
        return len(list_values) > 10 and list_values[:10] or list_values


class SaleOrderLine(models.Model):
    """ sale.order.line Model to Connect sale lines with exchange moves """
    _inherit = 'sale.order.line'

    exchange_move_id = fields.Many2one(
        'stock.move', 'Origin Exchanged move',
        copy=False, help='Move that created for the Exchange'
    )
