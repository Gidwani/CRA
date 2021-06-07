

{
    'name': 'Sale Discount on Total Amount',
    'version': '14.0.1.1.0',
    'category': 'Sales Management',
    'summary': "Discount on Total in Sale and Invoice With Discount Limit and Approval",
    'author': 'Fazeel',
    'company': 'abc',
    'website': 'http://www.abc.com',
    'description': """

Sale Discount for Total Amount
=======================
Module to manage discount on total amount in Sale.
        as an specific amount or percentage
""",
    'depends': ['sale',
                'account', 'delivery'
                ],
    'data': [
        'views/sale_view.xml',
        'views/account_invoice_view.xml',
        # 'views/invoice_report.xml',
        # 'views/sale_order_report.xml',
        'views/res_config_view.xml',

    ],
    # 'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'application': True,
    'installable': True,
    'auto_install': False,
}
