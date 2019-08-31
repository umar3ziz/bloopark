# -*- coding: utf-8 -*-
#################################################################################
# Author      : Omar Abdelaziz <omar_3ziz@hotmail.com>
# Copyright(c): Developer -Omar Abdelaziz-
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#################################################################################
""" This Module For Stock Locations """

from odoo import models, fields, api


class StockLocation(models.Model):
    """ stock.location Model to Add Fields to stock locations to serve Exchanges """
    _inherit = "stock.location"

    exchange_location = fields.Boolean(
        'Is a Exchange Location?',
        help='Check this box to allow using this location as a exchange location.'
    )
