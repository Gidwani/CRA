# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################

{
   'name': 'Global Discount on Sales Order, Purchase Order and Invoice (Community)',
   'version': '1.0',
   'author': 'Acespritech Solutions Pvt. Ltd.',
   'category': 'Product',
   'description': """
       Module allows to give global discount in sales, purchase and invoice.
   """,
   'website': 'http://www.acespritech.com',
   'price': 30,
   'currency': 'EUR',
   'summary': 'Module allows to give global discount in sales, purchase and invoice.',
   'depends': ['base', 'sale_management', 'sale_purchase', 'purchase', 'product', 'account'],
   'data': [
        'views/discount_config_setting_views.xml',
        'views/sales_views.xml',
        'views/purchase_views.xml',
        'views/invoice_views.xml',
        'report/sale_report_views.xml',
        'report/purchase_report_views.xml',
        'report/invoice_report_views.xml'
   ],
   'images': ['static/description/main_screeshot.png'],
   'installable': True,
   'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4
