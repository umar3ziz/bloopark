# -*- coding: utf-8 -*-
#################################################################################
# Author      : Omar Abdelaziz <omar_3ziz@hotmail.com>
# Copyright(c): Developer -Omar Abdelaziz-
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#################################################################################
""" This Module For Stock Move """

from odoo import models, fields, api


class StockMove(models.Model):
    """ stock.move Model to Add Fields to moves to serve Exchanges """
    _inherit = 'stock.move'

    origin_exchange_move_id = fields.Many2one(
        'stock.move', 'Origin Exchanged move',
        copy=False, help='Move that created the exchange move'
    )
    exchanged = fields.Boolean(help='True if this move already exchanged')
