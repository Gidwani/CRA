{
    "name": "Odoo Advanced in tree/list view for Account",
    "version": "16.0.1.0.0",
    "summary": "Odoo Advanced in tree/list view for Account.",
    "category": "Other",
    "description": """By installing this module, user can see row number in Odoo backend tree view. sequence in list, Numbering List View, row count, row counting, show count list, list view row count, number in row, rij nummer, номер строки, numéro de ligne, Zeilennummer, numero de fila, رقم الصف , nomor baris, ListView Row Count,list view row number, number in list view, tree row number, tree view row number, list view row number, dynamic sequence, dynamic row number, line sequence, sequence in report, record count, dynamic list view, dynamic tree view, dynamic listview, listview advance, list editor, list row sequence, backup, sticky, document, list view number, listview number, list number, tree number, treeview number, stick list, row number report, sequence number, sequencial number, number in list, dynamic number""",
    "depends": ["odoo_advance_search", "account"],
    "data": [],
    "assets": {
        "web.assets_backend": [
            "advance_search_in_account/static/src/xml/list_render.xml",
        ],
    },
    "images": ["static/description/rowno_tree-banner.png"],
    "auto_install": True,
    "license": "LGPL-3",
    # Author
    "author": "Synodica Solutions Pvt. Ltd.",
    "website": "https://synodica.com",
    "maintainer": "Synodica Solutions Pvt. Ltd.",
    "installable": True,
    "application": False,
    # "auto_install": False,
}
