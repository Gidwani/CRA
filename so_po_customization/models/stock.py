# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ProductTemplateInh(models.Model):
    _inherit = 'product.template'

    available_qty = fields.Float('Availbale Quantity', compute="cal_available_qty")

    def cal_available_qty(self):
        for rec in self:
            total = 0
            # quants = self.env['stock.quant'].search([('product_tmpl_id', '=', rec.id)])
            quants = self.get_quant_lines()
            quants = self.env['stock.quant'].browse(quants)
            for line in quants:
                # print(line.on_hand)
                # if line.on_hand:
                if line.product_tmpl_id.id == rec.id:
                    total = total + line.available_quantity
            rec.available_qty = total

    def get_quant_lines(self):
        domain_loc = self.env['product.product']._get_domain_locations()[0]
        quant_ids = [l['id'] for l in self.env['stock.quant'].search_read(domain_loc, ['id'])]
        return quant_ids


class StockPickingInh(models.Model):
    _inherit = 'stock.picking'

    do_no = fields.Char("Supplier Do #")

    # @api.model
    # def create(self, vals):
    #     if vals.get('name', _('New')) == _('New'):
    #         vals['name'] = self.env['ir.sequence'].next_by_code('stock.picking.sequence') or _('New')
    #     result = super(StockPickingInh, self).create(vals)
    #     return result


class StockPickingLineInh(models.Model):
    _inherit = 'stock.move'

    remarks = fields.Char("Remarks", compute='_compute_remarks')
    number = fields.Integer(compute='_compute_get_number', store=True)

    def _compute_remarks(self):
        for rec in self:
            if rec.picking_id.sale_id:
                for line in rec.picking_id.sale_id.order_line:
                    if rec.product_id.id == line.product_id.id:
                        rec.remarks = line.remarks
            if rec.picking_id.purchase_id:
                for line in rec.picking_id.purchase_id.order_line:
                    if rec.product_id.id == line.product_id.id:
                        rec.remarks = line.remarks


    @api.depends('picking_id')
    def _compute_get_number(self):
        for order in self.mapped('picking_id'):
            number = 1
            for line in order.move_ids_without_package:
                line.number = number
                number += 1