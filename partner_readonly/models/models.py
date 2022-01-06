# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountMoveInh(models.Model):
    _inherit = 'account.move'

    is_created_so_po = fields.Boolean()


class SaleOrderInh(models.Model):
    _inherit = 'sale.order'

    def _prepare_invoice(self, ):
        invoice_vals = super(SaleOrderInh, self)._prepare_invoice()
        invoice_vals.update({
            'is_created_so_po': True,
        })
        return invoice_vals


class PurchaseOrderInh(models.Model):
    _inherit = 'purchase.order'

    def _prepare_invoice(self, ):
        invoice_vals = super(PurchaseOrderInh, self)._prepare_invoice()
        invoice_vals.update({
            'is_created_so_po': True,
        })
        return invoice_vals
