# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockPickingInh(models.Model):
    _inherit = 'stock.picking'

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        result = super(StockPickingInh, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu)
        if view_type == 'form':
            for repo in result['toolbar']['print']:
                if repo['name'] == 'Delivery Slip':
                    result['toolbar']['print'].remove(repo)
            result['toolbar']['print'].reverse()
        return result
