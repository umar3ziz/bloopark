# -*- coding: utf-8 -*-
#################################################################################
# Author      : Omar Abdelaziz <omar_3ziz@hotmail.com>
# Copyright(c): Developer -Omar Abdelaziz-
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#################################################################################
""" This Module For Invoicing """

from odoo import models, fields, api


class AccountInvoiceLine(models.Model):
    """ account.invoice.line Model to Connect invoice lines with exchange order lines"""
    _inherit = 'account.invoice.line'

    exchange_sale_line_id = fields.Many2one(
        'sale.order.line', 'Origin Exchanged Sale Line',
        copy=False
    )
    exchange_purchase_line_id = fields.Many2one(
        'purchase.order.line', 'Origin Exchanged Purchase Line',
        copy=False
    )
