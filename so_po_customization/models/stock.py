# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ProductTemplateInh(models.Model):
    _inherit = 'product.template'

    available_qty = fields.Float('Available Quantity', compute="cal_available_qty")
    incoming_quantity = fields.Float('Incoming Quantity', compute='cal_incoming_quantity')
    hs_code = fields.Char('HS CODE')

    def cal_incoming_quantity(self):
        for rec in self:
            incoming = self.env['stock.picking.type'].search([('code', '=', 'incoming')], limit=1)
            pickings = self.env['stock.picking'].search([('picking_type_id', '=', incoming.id), ('state', '!=', 'done')])
            qty = 0
            for picking in pickings:
                for line in picking.move_line_ids_without_package:
                    if line.product_id.id == rec.id:
                        qty = qty + line.quantity_done
            rec.incoming_quantity = qty

    def cal_available_qty(self):
        for rec in self:
            total = 0
            quants = self.get_quant_lines()
            quants = self.env['stock.quant'].browse(quants)
            for line in quants:
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
    is_receipt = fields.Boolean(compute='compute_is_receipt')

    def get_seq(self, picking):
        return 'Picklist/'+picking.name.split('/')[1]+"/"+picking.name.split('/')[2] + "/"+picking.name.split('/')[3]

    def compute_is_receipt(self):
        for rec in self:
            if rec.picking_type_id.code == 'incoming':
                rec.is_receipt = True
            else:
                rec.is_receipt = False

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        result = super(StockPickingInh, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu)
        reports = self.env['ir.actions.report'].sudo().search([('report_name', 'in', ['stock.report_picking', 'stock.report_deliveryslip'])])
        for report in reports:
            report.unlink_action()
        return result

    # @api.model
    # def create(self, vals):
    #     if vals.get('name', _('New')) == _('New'):
    #         vals['name'] = self.env['ir.sequence'].next_by_code('stock.picking.sequence') or _('New')
    #     result = super(StockPickingInh, self).create(vals)
    #     return result


class StockMoveLineInh(models.Model):
    _inherit = 'stock.move.line'

    def get_product_qty(self, ml):
        product_qty = self.env['product.template'].search([('name', '=', ml.product_id.name)])

        for line in ml.picking_id.sale_id.order_line:
            if line.product_uom.name == 'Lth':
                qty = int(product_qty.available_qty)/6
                qty = str(round(qty, 2)) + " Lth"
            else:
                qty = float(product_qty.available_qty)
                qty = str(round(qty, 2)) + ' ' + product_qty.uom_id.name
        return qty

    def get_onhand_qty(self, ml):
        product_qty = self.env['product.template'].search([('name', '=', ml.product_id.name)])
        for line in ml.picking_id.sale_id.order_line:
            if line.product_uom.name == 'Lth':
                qty = int(product_qty.qty_available)/6
                qty = str(round(qty, 2)) + " Lth"

            else:
                qty = float(product_qty.qty_available)
                qty = str(round(qty, 2))+ ' ' + product_qty.uom_id.name
        return qty

    def get_product_uom_id(self, ml, picking):
        for line in picking.sale_id.order_line:
            if line.product_id.id == ml.product_id.id:
                uom = line.product_uom.name
            else:
                uom = line.product_uom.name
        return uom


class StockMoveInh(models.Model):
    _inherit = 'stock.move'

    remarks = fields.Char("Remarks", compute='_compute_remarks')
    number = fields.Integer(compute='_compute_get_number', store=True)
    # product_uom = fields.Many2one('uom.uom', 'Unit of Measure', required=True,
    #                               domain="[('category_id', '=', product_uom_category_id)]", compute="get_sale_uom")
    #
    # def get_sale_uom(self):
    #     for rec in self:
    #         for line in rec.picking_id.sale_id.order_line:
    #             if line.product_id == rec.product_id.id:
    #                 uom = line.product_uom
    #             else:
    #                 uom = rec.product_uom
    #         rec.product_uom = uom

    def get_product_uom_id(self, ml, picking):
        for line in picking.sale_id.order_line:
            if line.product_id.id == ml.product_id.id:
                uom = line.product_uom.name
            else:
                uom = line.product_uom.name
        return uom

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

    @api.depends('picking_id')
    def _compute_get_number(self):
        for order in self.mapped('picking_id'):
            number = 1
            for line in order.move_ids_without_package:
                line.number = number
                number += 1
