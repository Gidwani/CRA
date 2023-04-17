# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle 
#
##############################################################################

{
    "name": "All in one Mass/bulk Export Excel",
    'version': '14.0.1.0',
    "sequence": 1,
    "category": 'Sales',
    "summary": """
                  odoo App will help to Mass Export into Excel like Sale Order, Purchase Order,Invoice in one click, bulk excel export, mass export excel,Mass Export Excel sale order, mass Export Excel purchase order,  Mass Export Excel Invoice
        """,
    "description": """
        odoo App will help to Mass Export into Excel like Sale Order, Purchase Order,Invoice in one click
        
        Mass Export Excel sale order, mass Export Excel purchase order,  Mass Export Excel Invoice, Bulk Export Excel, Multiple Export Excel, Sale order export in excel, Purchase order export in excel, Invoice export in excel.
All in one Mass/bulk Export Excel
Odoo All in one Mass/bulk Export Excel
All in one mass export excel
Odoo all in one mass export excel
Mass excel export 
Odoo mass excel export
Bulk excel export
Odoo bulk excel export
All in one export
Odoo all in one export
Export excel
Odoo export excel
Excel report export
Odoo excel report export

    """,
    'author': 'DevIntelle Consulting Service Pvt.Ltd', 
    'website': 'http://www.devintellecs.com',
    "depends": ['sale','sale_stock','purchase'],
    "data": [
        'security/ir.model.access.csv',
        'wizard/bulk_export_views.xml',
    ],
    'demo': [],
    'test': [],
    'css': [],
    'qweb': [],
    'js': [],
    'images': ['images/main_screenshot.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'price':22.0,
    'currency':'EUR',
    #'live_test_url':'https://youtu.be/A5kEBboAh_k',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
