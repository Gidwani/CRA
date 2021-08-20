# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleOrderInh(models.Model):
    _inherit = 'sale.order'

    def action_select_products(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Select Products',
            'view_id': self.env.ref('select_multiple_products.view_select_products_form', False).id,
            # 'context': {'default_ref': self.name, 'default_order_amount': self.amount_total, 'default_user_id':
            # self.user_id.id},
            'target': 'new',
            'res_model': 'select.products',
            'view_mode': 'form',
        }


class PurchaseOrderInh(models.Model):
    _inherit = 'purchase.order'

    def action_select_products(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Select Products',
            'view_id': self.env.ref('select_multiple_products.view_select_products_form', False).id,
            # 'context': {'default_ref': self.name, 'default_order_amount': self.amount_total, 'default_user_id': self.user_id.id},
            'target': 'new',
            'res_model': 'select.products',
            'view_mode': 'form',
        }
