# -*- coding: utf-8 -*-
{
    'name': "Approval",

    'summary': """
        PO, SO, DO Approvals""",

    'description': """
        PO, SO, DO Approvals
    """,

    'author': "Atif Ali",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'sale_management', 'purchase', 'account', 'stock', 'contacts'],

    # always loaded
    'data': [
        'security/security.xml',
        'views/partner_views.xml',
        # 'security/ir.model.access.csv',
        'views/purchase_views.xml',
        'views/account_views.xml',
        'views/stock_views.xml',
        'views/sale_order_views.xml',

    ],
}
