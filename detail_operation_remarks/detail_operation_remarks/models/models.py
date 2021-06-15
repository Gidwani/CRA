# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockMoveLineInh(models.Model):
    _inherit = 'stock.move.line'

    remarks = fields.Char("Remarks", compute='_compute_remarks')
    number = fields.Integer(compute='_compute_get_number', store=True)

    def _compute_remarks(self):
        for rec in self:
            if rec.picking_id.sale_id:
                for line in rec.picking_id.sale_id.order_line:
                    if rec.product_id.id == line.product_id.id:
                        rec.remarks = line.remarks

            elif rec.picking_id.purchase_id:
                for line in rec.picking_id.purchase_id.order_line:
                    if rec.product_id.id == line.product_id.id:
                        rec.remarks = line.remarks
            else:
                rec.remarks = ''
