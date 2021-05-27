# -*- coding: utf-8 -*-
{
    'name': "Header Multi",

    'summary': """
        Header Multi""",

    'description': """
        Header Multi
    """,

    'author': "Atif",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'purchase'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/assets.xml',
        'views/purchase_views.xml',
        'views/sale_views.xml',
        'wizard/select_products_wizard_view.xml',
    ],

}
