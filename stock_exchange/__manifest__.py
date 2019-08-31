# -*- coding: utf-8 -*-
#################################################################################
# Author      : Omar Abdelaziz <omar_3ziz@hotmail.com>
# Copyright(c): Developer -Omar Abdelaziz-
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#################################################################################
{
    'name': "Delivery Exchange",
    'summary': "Delivery Exchange Process",
    'author': "Omar Abdelaziz",
    'category': 'Stock',
    'version': '12.0.1.0.0',
    'website': "https://www.linkedin.com/in/umar3ziz/",
    'licence': 'mit',
    'depends': [
        'sale_management',
        'sale_stock',
        'purchase_stock',
    ],
    'data': [
        'templates/exchange.xml',

        'wizard/stock_exchange_views.xml',

        'views/stock_picking_views.xml',
        'views/sale_order_view.xml',
        'views/purchase_order_view.xml',
        'views/stock_location_views.xml',
        'views/stock_picking_type_views.xml',
    ],
    'price': 74.99,
    'currency': 'EUR',
    'qweb': ['static/src/xml/*.xml'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
