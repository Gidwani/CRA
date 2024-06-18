# -*- coding: utf-8 -*-
import os
from datetime import datetime
from pytz import timezone
from odoo import models, fields, api
from odoo.http import request
from odoo.osv import expression


class ProductProductInh(models.Model):
    _inherit = 'product.product'

    def name_get(self):
        res = []
        for rec in self:
            res.append((rec.id, '%s ' % (rec.name)))
        return res


class ProductTemplateInh(models.Model):
    _inherit = 'product.template'

    available_qty = fields.Float('Available Quantity', copy=False)
    incoming_quantity = fields.Float('Incoming Quantity', copy=False)
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

    # @api.model
    # def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    #     result = super(StockPickingInh, self).fields_view_get(
    #         view_id=view_id, view_type=view_type, toolbar=toolbar,
    #         submenu=submenu)
    #     if view_type == 'form':
    #         for repo in result['toolbar']['print']:
    #             if repo['name'] == 'Delivery Slip':
    #                 result['toolbar']['print'].remove(repo)
    #         result['toolbar']['print'].reverse()
    #     return result

    def get_lines(self):
        pro_list = []
        for line in self.move_ids_without_package:
            lot_list = []
            if line.move_line_ids:
                for rec in line.move_line_ids:
                    if rec.lot_id:
                        lot_list.append({
                            'lot_name': rec.lot_id.name,
                            'lot_qty': rec.quantity/6 if rec.product_uom_id.name == 'Mtr' else rec.quantity,
                        })
                lot_str = ''
                if lot_list:
                    for f in lot_list:
                        lot_str = lot_str + f.get('lot_name')+' : ' +str(f.get('lot_qty')) + ', '
                pro_list.append({
                    'number': line.number,
                    'onhand': self.get_onhand_qty_picklist(line),
                    'product_qty': self.get_product_qty_picklist(line),
                    'product': rec.product_id.name,
                    'remarks': rec.remarks,
                    'qty': line.product_uom_qty/6 if line.product_uom.name == 'Mtr' else line.product_uom_qty,
                    'uom': 'Lth' if line.product_uom.name == 'Mtr' else rec.product_uom_id.name,
                    'lot': lot_list,
                })
            else:
                pro_list.append({
                    'number': line.number,
                    'onhand': self.get_onhand_qty_picklist(line),
                    'product_qty': self.get_product_qty_picklist(line),
                    'product': line.product_id.name,
                    'remarks': line.remarks,
                    'qty': line.product_uom_qty/6 if line.product_uom.name == 'Mtr' else line.product_uom_qty,
                    'uom': 'Lth' if line.product_uom.name == 'Mtr' else line.product_uom.name,
                    'lot': '',
                })
        return pro_list

    def get_total_qty(self):
        total = 0
        for rec in self.move_line_ids_without_package:
            total = total + rec.quantity
        return round(total, 2)

    def get_delivery(self):
        delivery = self.env['stock.picking.type'].search([('code', '=', 'outgoing')], limit=1)
        if self.picking_type_id.code == 'outgoing':
            return 1
        else:
            return 0

    def get_current_date(self):
        now_utc_date = datetime.now()
        now_dubai = now_utc_date.astimezone(timezone('Asia/Karachi'))
        return now_dubai.strftime('%d/%m/%Y %H:%M:%S')

    def get_seq(self, picking):
        # return 'Picklist/'+picking.name.split('/')[1]+"/"+picking.name.split('/')[2] + "/"+picking.name.split('/')[3]
        return 'Picklist/'+picking.name.split('/')[1]+"/"+picking.name.split('/')[2]

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

    def get_lot_onhand_qty(self, line):
        domain_loc = self.env['product.product']._get_domain_locations()[0]
        quant_ids = [l['id'] for l in self.env['stock.quant'].search_read(domain_loc, ['id'])]
        quants = self.env['stock.quant'].browse(quant_ids)
        total = 0
        for q_line in quants:
            if q_line.product_tmpl_id.id == line.product_id.product_tmpl_id.id and q_line.lot_id.id == line.lot_id.id:
                total = total + q_line.inventory_quantity
        return total
        # rec.available_qty = total

    def get_onhand_qty_picklist(self, ml):
        print(ml)
        # if ml.lot_id:
        #     product_qty = self.get_lot_onhand_qty(ml)
        # else:
        product_qty = self.env['product.template'].search([('id', '=', ml.product_id.product_tmpl_id.id)]).qty_available
        # for line in ml.sale_id.order_line:
        if ml.product_uom.name == 'Mtr':
            qty = int(product_qty)/6
            formatted_float = "{:.2f}".format(float(qty))
            qty = str(formatted_float) + " Lth"
        else:
            qty = float(product_qty)
            formatted_float = "{:.2f}".format(qty)
            qty = str(formatted_float) + ' ' +  ml.product_id.uom_id.name
        return qty

    # def get_onhand_qty_picklist_lot(self, ml):
    #     print(ml)
    #     if ml.lot_id:
    #         product_qty = self.get_lot_onhand_qty(ml)
    #     else:
    #         product_qty = self.env['product.template'].search([('id', '=', ml.product_id.product_tmpl_id.id)]).qty_available
    #     # for line in ml.sale_id.order_line:
    #     if ml.product_uom_id.name == 'Lth':
    #         qty = int(product_qty)/6
    #         formatted_float = "{:.2f}".format(float(qty))
    #         qty = str(formatted_float) + " Lth"
    #     else:
    #         qty = float(product_qty)
    #         formatted_float = "{:.2f}".format(qty)
    #         qty = str(formatted_float) + ' ' +  ml.product_id.uom_id.name
    #     return qty

    def get_product_qty_picklist(self, ml):
        product_qty = self.env['product.template'].search([('id', '=', ml.product_id.product_tmpl_id.id)])
        # for line in ml.sale_id.order_line:
        if ml.product_uom.name == 'Mtr':
            qty = int(product_qty.available_qty)/6
            formatted_float = "{:.2f}".format(float(qty))
            qty = str(formatted_float) + " Lth"
        else:
            qty = float(product_qty.available_qty)
            formatted_float = "{:.2f}".format(qty)
            qty = str(formatted_float) + ' ' + product_qty.uom_id.name
        return qty



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

    def _trigger_assign(self):
        """ Check for and trigger action_assign for confirmed/partially_available moves related to done moves.
            Disable auto reservation if user configured to do so.
        """
        if not self or self.env['ir.config_parameter'].sudo().get_param('stock.picking_no_auto_reserve'):
            return

        domains = []
        for move in self:
            domains.append([('product_id', '=', move.product_id.id), ('location_id', '=', move.location_dest_id.id)])
        static_domain = [('state', 'in', ['confirmed', 'partially_available']),
                         ('procure_method', '=', 'make_to_stock'),
                         ('reservation_date', '<=', fields.Date.today())]
        moves_to_reserve = self.env['stock.move'].search(expression.AND([static_domain, expression.OR(domains)]),
                                                         order='reservation_date, priority desc, date asc, id asc')

        if move.purchase_line_id and move.purchase_line_id.sale_order:
            new_moves_list = []
            for r in moves_to_reserve:
                if move.purchase_line_id.sale_order == r.sale_line_id.order_id.name:
                    new_moves_list.append(r.id)
            if new_moves_list:
                new_moves_to_reserve = self.env['stock.move'].browse(new_moves_list)
                new_moves_to_reserve._action_assign()
        else:
            moves_to_reserve._action_assign()

    def get_lot(self):
        lot_list = []
        for rec in self.picking_id.move_line_ids_without_package:
            if rec.move_id.id == self.id:
                lot_list.append(rec.lot_id.name)
        return ','.join(lot_list)

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

            if rec.picking_id.backorder_id.sale_id:
                for line in rec.picking_id.backorder_id.sale_id.order_line:
                    if rec.sale_line_id.id == line.id:
                        rem = line.remarks
            rec.remarks = rem

    @api.depends('picking_id')
    def _compute_get_number(self):
        # if not self.picking_id.backorder_id:
        for order in self.mapped('picking_id'):
            number = 1
            for line in order.move_ids_without_package:
                line.number = number
                number += 1
