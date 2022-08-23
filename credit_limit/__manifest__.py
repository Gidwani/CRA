# -*- coding: utf-8 -*-
{
    'name': "Customer Credit Management",
    'summary': """
         Credit limits for each customer""",
    'description': """
        - Define a credit limit on the partner
        
    """,
    'author': "Atif",
    'website': "www.abc.com",
    'category': 'Sales',
    'version': '14.0.0.0.0',
    'depends': ['base','sale_management', 'approval_so_po',
                'account'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/message_box.xml',
        'views/views.xml',
    ],


}
