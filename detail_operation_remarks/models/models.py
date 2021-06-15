# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockMoveLineInh(models.Model):
    _inherit = 'stock.move.line'

    remarks = fields.Char("Remarks", compute='_compute_remarks')
    number = fields.Integer(compute='_compute_get_number', store=True)
    so_no = fields.Integer(compute='compute_so_sr_no')

    def compute_so_sr_no(self):
        for rec in self:
            if rec.picking_id.sale_id:
                for line in rec.picking_id.sale_id.order_line:
                    if line.product_id.id == rec.product_id.id:
                        rec.so_no = line.number
            else:
                rec.so_no = 0

    @api.depends('picking_id')
    def _compute_get_number(self):
        for order in self.mapped('picking_id'):
            number = 1
            for line in order.move_line_ids_without_package:
                line.number = number
                number += 1

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
