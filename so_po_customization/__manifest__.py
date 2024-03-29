# -*- coding: utf-8 -*-
{
    'name': "So Po Customization",

    'summary': """
        So Po Customization""",

    'description': """
        So Po Customization
    """,

    'author': "Atif Ali",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'sale', 'purchase', 'stock', 'sale_margin',  'sale_stock', 'approval_so_po', 'product', 'web', 'sale_discount_total', 'l10n_ae'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/sale_views.xml',
        'views/purchase_views.xml',
        'views/account_views.xml',
        'views/stock_views.xml',
        'reports/sale_report.xml',
        'reports/purchase_report.xml',
        'reports/account_report.xml',
        'reports/stock_report.xml',
        'reports/delivery_report.xml',
        'reports/stock_picklist.xml',
        'wizard/sale_wizard.xml',
        # 'wizard/select_products_wizard_view.xml',
    ],
'license': 'AGPL-3',




}
