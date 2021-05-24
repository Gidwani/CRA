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

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('stock.picking.sequence') or _('New')
        result = super(StockPickingInh, self).create(vals)
        return result