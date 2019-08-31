# -*- coding: utf-8 -*-
#################################################################################
# Author      : Omar Abdelaziz <omar_3ziz@hotmail.com>
# Copyright(c): Developer -Omar Abdelaziz-
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#################################################################################
""" This Module For Inventory Type """

from odoo import models, fields, api


class StockPickingType(models.Model):
    """ stock.picking.type Model to Add Fields to stock types to serve Exchanges """
    _inherit = "stock.picking.type"

    exchange_picking_type_id = fields.Many2one(
        'stock.picking.type',
        'Operation Type for Exchanges'
    )
