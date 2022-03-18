# -*- coding: utf-8 -*-
from datetime import datetime

from pytz import timezone

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare
from odoo.tools.float_utils import float_compare, float_is_zero, float_round


class ProductProductInh(models.Model):
    _inherit = 'product.product'

    def name_get(self):
        res = []
        for rec in self:
            res.append((rec.id, '%s ' % (rec.name)))
        return res


class ProductTemplateInh(models.Model):
    _inherit = 'product.template'

    available_qty = fields.Float('Available Quantity')
    incoming_quantity = fields.Float('Incoming Quantity')
    hs_code = fields.Char('HS CODE')
    weight = fields.Float(
        'Weight', compute='_compute_weight', digits='Stock Weight',
        inverse='_set_weight', store=True, copy=True)

    volume = fields.Float(
        'Volume', compute='_compute_volume', inverse='_set_volume', digits='Volume', store=True, copy=True)

    @api.depends('product_variant_ids', 'product_variant_ids.volume')
    def _compute_volume(self):
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.volume = template.product_variant_ids.volume
        for template in (self - unique_variants):
            template.volume = 0.0

    def _set_volume(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids.volume = template.volume

    def _set_weight(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids.weight = template.weight

    @api.depends('product_variant_ids', 'product_variant_ids.weight')
    def _compute_weight(self):
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.weight = template.product_variant_ids.weight
        for template in (self - unique_variants):
            template.weight = 0.0

    def cal_incoming_quantity(self):
        for rec in self:
            # qty = 0
            # pickings = self.env['stock.move'].search([('product_id.product_tmpl_id', '=', rec.id), ('picking_code', '=', 'incoming'), ('state', 'not in', ['done', 'cancel'])])
            # for pick in pickings:
            #     qty = qty + pick.product_uom_qty
            # rec.incoming_quantity = qty
        # all = self.env['product.template'].search([])
        # for rec in all:
        #     incoming = self.env['stock.picking.type'].search([('code', '=', 'incoming')], limit=1)
        #     pickings = self.env['stock.picking'].search([('picking_type_id', '=', incoming.id), ('state', 'not in', ['done', 'cancel'])])
        #     qty = 0
        #     for picking in pickings:
        #         for line in picking.move_ids_without_package:
        #             if line.product_id.product_tmpl_id.id == rec.id:
        #                 qty = qty + line.product_uom_qty
        #     rec.incoming_quantity = qty
            total = 0
            quants = self.get_quant_lines()
            quants = self.env['stock.quant'].browse(quants)
            for q_line in quants:
                if q_line.product_tmpl_id.id == rec.id:
                    total = total + q_line.available_quantity
            rec.available_qty = total

    # @api.depends('qty_available')
    # def cal_available_qty(self):
    #     for rec in self:
    #         total = 0
    #         quants = self.get_quant_lines()
    #         quants = self.env['stock.quant'].browse(quants)
    #         for line in quants:
    #             if line.product_tmpl_id.id == rec.id:
    #                 total = total + line.available_quantity
    #         rec.available_qty = total

    def get_quant_lines(self):
        domain_loc = self.env['product.product']._get_domain_locations()[0]
        quant_ids = [l['id'] for l in self.env['stock.quant'].search_read(domain_loc, ['id'])]
        return quant_ids


class StockPickingInh(models.Model):
    _inherit = 'stock.picking'

    do_no = fields.Char("Supplier Do #")
    is_receipt = fields.Boolean(compute='compute_is_receipt')
    invoice_link = fields.Boolean(string='Invoice link')

    def get_total_qty(self):
        total = 0
        for rec in self.move_line_ids_without_package:
            total = total + rec.qty_done
        return round(total, 2)

    def get_delivery(self):
        delivery = self.env['stock.picking.type'].search([('code', '=', 'outgoing')], limit=1)
        if self.picking_type_id.code == 'outgoing':
            return 1
        else:
            return 0

    # def check_state(self):
    #     if self.state != 'done':
    #         raise UserWarning(('You cannot print report in this state'))
    #     else:
    #         return "True"

    def get_current_date(self):
        # print('hello')
        now_utc_date = datetime.now()
        now_dubai = now_utc_date.astimezone(timezone('Asia/Karachi'))
        return now_dubai.strftime('%d/%m/%Y %H:%M:%S')

    def get_seq(self, picking):
        # print(picking.name)
        return 'Picklist/'+picking.name.split('/')[1]+"/"+picking.name.split('/')[2] + "/"+picking.name.split('/')[3]

    def compute_is_receipt(self):
        for rec in self:
            if rec.picking_type_id.code == 'incoming':
                rec.is_receipt = True
            else:
                rec.is_receipt = False

    # @api.model
    # def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    #     result = super(StockPickingInh, self).fields_view_get(
    #         view_id=view_id, view_type=view_type, toolbar=toolbar,
    #         submenu=submenu)
    #     reports = self.env['ir.actions.report'].sudo().search([('report_name', 'in', ['stock.report_picking'])])
    #     for report in reports:
    #         report.unlink_action()
    #     return result


class StockMoveLineInh(models.Model):
    _inherit = 'stock.move.line'

    # remarks = fields.Char("Remarks", compute='_compute_remarks')
    # number = fields.Integer(compute='_compute_get_number', store=True)
    #
    # def _compute_remarks(self):
    #     for rec in self:
    #         if rec.picking_id.sale_id:
    #             for line in rec.picking_id.sale_id.order_line:
    #                 if rec.product_id.id == line.product_id.id:
    #                     rec.remarks = line.remarks
    #
    #         elif rec.picking_id.purchase_id:
    #             for line in rec.picking_id.purchase_id.order_line:
    #                 if rec.product_id.id == line.product_id.id:
    #                     rec.remarks = line.remarks
    #         else:
    #             rec.remarks = ''

    @api.depends('picking_id')
    def _compute_get_number(self):
        for order in self.mapped('picking_id'):
            number = 1
            for line in order.move_line_ids_without_package:
                line.number = number
                number += 1

    def get_product_uom_lot(self, ml):
        product_qty = self.env['product.template'].search([('name', '=', ml.product_id.name)])
        uom = ''
        if ml.picking_id.sale_id:
            for line in ml.picking_id.sale_id.order_line:
                if line.product_id.id == ml.product_id.id and line.number == ml.so_no:
                    if line.product_uom.name == 'Lth' and ml.product_uom_id.name == 'Mtr':
                        # uom = int(line.product_uom_qty)
                        uom = " Mtr"
                    else:
                        # qty = float(line.product_uom_qty)
                        uom = product_qty.uom_id.name
        if ml.picking_id.purchase_id:
            for line in ml.picking_id.purchase_id.order_line:
                if line.product_id.id == ml.product_id.id and line.number == ml.so_no:
                    if line.product_uom.name == 'Lth' and ml.product_uom_id.name == 'Mtr':
                        # qty = int(line.product_qty)
                        uom =  " Lth"
                    else:
                        # qty = float(line.product_qty)
                        uom = product_qty.uom_id.name
        return uom

    def get_product_qty_lot(self, ml):
        product_qty = self.env['product.template'].search([('name', '=', ml.product_id.name)])
        qty = 0
        if ml.picking_id.sale_id:
            for line in ml.picking_id.sale_id.order_line:
                if line.product_id.id == ml.product_id.id and line.number == ml.so_no:
                    if line.product_uom.name == 'Lth' and ml.product_uom_id.name == 'Mtr':
                        qty = int(line.product_uom_qty)
                        qty = str(round(qty, 2))
                    else:
                        qty = float(line.product_uom_qty)
                        qty = str(round(qty, 2))
        if ml.picking_id.purchase_id:
            for line in ml.picking_id.purchase_id.order_line:
                if line.product_id.id == ml.product_id.id and line.number == ml.number:
                    if line.product_uom.name == 'Lth' and ml.product_uom_id.name == 'Mtr':
                        qty = int(line.product_qty)
                        qty = str(round(qty, 2))
                    else:
                        qty = float(line.product_qty)
                        qty = str(round(qty, 2))
        return qty

    def get_product_qty(self, ml):
        product_qty = self.env['product.template'].search([('name', '=', ml.product_id.name)])
        qty = 0
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

    def get_sr_no(self, picking, product):
        for line in picking.move_ids_without_package:
            if line.product_id.id == product.id:
                sr = line.number
        return sr

    def get_remarks(self, picking, rec):
        sr = ''
        for line in picking.move_ids_without_package:
            if line.product_id.id == rec.product_id.id:
                sr = line.remarks
        return sr


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

    def get_product_uom_lot(self, ml):
        product_qty = self.env['product.template'].search([('name', '=', ml.product_id.name)])
        uom = ''

        if ml.picking_id.sale_id:
            for line in ml.picking_id.sale_id.order_line:
                if line.product_id.id == ml.product_id.id and line.number == ml.so_no:
                    if line.product_uom.name == 'Lth' and ml.product_uom_id.name == 'Mtr':
                        # uom = int(line.product_uom_qty)
                        uom = " Lth"
                    else:
                        # qty = float(line.product_uom_qty)
                        uom = product_qty.uom_id.name
        if ml.picking_id.purchase_id:
            for line in ml.picking_id.purchase_id.order_line:
                if line.product_id.id == ml.product_id.id and line.number == ml.number:
                    if line.product_uom.name == 'Lth' and ml.product_uom_id.name == 'Mtr':
                        # qty = int(line.product_qty)
                        uom = " Lth"
                    else:
                        # qty = float(line.product_qty)
                        uom = product_qty.uom_id.name
        return uom

    def get_product_qty_lot(self, ml):
        product_qty = self.env['product.template'].search([('name', '=', ml.product_id.name)])
        qty = 0
        for line in ml.picking_id.sale_id.order_line:
            if line.product_id.id == ml.product_id.id and line.number == ml.number:
                if line.product_uom.name == 'Lth' and ml.product_uom.name == 'Mtr':
                    qty = int(line.product_uom_qty)
                    qty = str(round(qty, 2))
                else:
                    qty = float(line.product_uom_qty)
                    qty = str(round(qty, 2))
        return qty

    def get_product_uom_id(self, ml, picking):
        for line in picking.sale_id.order_line:
            if line.product_id.id == ml.product_id.id:
                uom = line.product_uom.name
            else:
                uom = line.product_uom.name
        return uom

    def _compute_remarks(self):
        for rec in self:
            rem = ''
            if rec.picking_id.sale_id:
                for line in rec.picking_id.sale_id.order_line:
                    if rec.sale_line_id.id == line.id:
                        rem = line.remarks

            elif rec.picking_id.purchase_id:
                for line in rec.picking_id.purchase_id.order_line:
                    if rec.product_id.id == line.product_id.id:
                        rem = line.remarks

            if rec.backorder_id.sale_id:
                for line in rec.backorder_id.sale_id.order_line:
                    if rec.sale_line_id.id == line.id:
                        rem = line.remarks
            rec.remarks = rem

    @api.depends('picking_id')
    def _compute_get_number(self):
        if not self.picking_id.backorder_id:
            for order in self.mapped('picking_id'):
                number = 1
                for line in order.move_ids_without_package:
                    line.number = number
                    number += 1
