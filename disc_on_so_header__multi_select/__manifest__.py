# -*- coding: utf-8 -*-
{
    'name': "Combined Modules",

    'summary': """
       Combined Modules""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Fazeel",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'sale_management'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/account_move_view.xml',
        'views/res_config_settings_view.xml',
        'views/sale_portal_templates.xml',
        'views/sale_views.xml',
        'views/purchase_views.xml',
        'report/report_invoice.xml',
        'report/sale_report_templates.xml',
        'data/discount_demo.xml',
        'wizard/select_products_wizard_view.xml',
        'views/assets.xml',
    ],

}
