# -*- coding: utf-8 -*-
#################################################################################
# Author      : Omar Abdelaziz <omar_3ziz@hotmail.com>
# Copyright(c): Developer -Omar Abdelaziz-
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#################################################################################
""" This Module For Inventory"""

from odoo import models, fields, api


class StockPicking(models.Model):
    """ stock.picking Model to Connect Picking with exchange orders and purchases"""
    _inherit = "stock.picking"

    exchange_sale_id = fields.Many2one(
        'sale.order',
        'Origin Exchanged Sale'
    )
    exchange_purchase_id = fields.Many2one(
        'purchase.order',
        'Origin Exchanged Purchase'
    )
