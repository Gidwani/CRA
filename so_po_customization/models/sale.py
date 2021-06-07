# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleOrderInh(models.Model):
    _inherit = 'sale.order'

    perc_discount = fields.Float('Discount', compute="_compute_discount")
    net_total = fields.Float('Net Total', compute="_compute_net_total")
    perc = fields.Float(compute='compute_percentage')
    net_tax = fields.Float('Tax', compute='compute_taxes')
    note_picklist = fields.Char('Note')
    subtotal_amount = fields.Float('Subtotal Amount', compute='_compute_net_total')

    def action_select_products(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Select Products',
            'view_id': self.env.ref('so_po_customization.view_select_products_form', False).id,
            # 'context': {'default_ref': self.name, 'default_order_amount': self.amount_total, 'default_user_id': self.user_id.id},
            'target': 'new',
            'res_model': 'select.products',
            'view_mode': 'form',
        }

    def get_lot_no(self, line):
        picking = self.env['stock.picking'].search([('sale_id', '=', line.order_id.id)])
        lot = None
        if picking:
            for rec in picking.move_line_ids_without_package:
                if rec.product_id.id == line.product_id.id:
                    lot = rec.lot_id.name
        return lot

    def get_product_qty(self, ml):
        product_qty = self.env['product.template'].search([('name', '=', ml.product_id.name)])

        # for line in ml.sale_id.order_line:
        if ml.product_uom.name == 'Lth':
            qty = int(product_qty.available_qty)/6
            qty = str(round(qty, 2)) + " Lth"
        else:
            qty = float(product_qty.available_qty)
            qty = str(round(qty, 2)) + ' ' + product_qty.uom_id.name
        return qty

    def get_onhand_qty(self, ml):
        product_qty = self.env['product.template'].search([('name', '=', ml.product_id.name)])
        # for line in ml.sale_id.order_line:
        if ml.product_uom.name == 'Lth':
            qty = int(product_qty.qty_available)/6
            qty = str(round(qty, 2)) + " Lth"

        else:
            qty = float(product_qty.qty_available)
            qty = str(round(qty, 2)) + ' ' + product_qty.uom_id.name
        return qty

    def compute_taxes(self):
        flag = False
        for rec in self.order_line:
            if rec.tax_id:
                flag = True
        if flag:
            self.net_tax = (5/100) * self.net_total
        else:
            self.net_tax = 0

    def compute_percentage(self):
        for rec in self:
            if rec.discount_type == 'percent':
                rec.perc = rec.discount_rate
            else:
                rec.perc = (rec.discount_rate/rec.subtotal_amount) * 100

    def _compute_discount(self):
        for rec in self:
            if rec.discount_type == 'percent':
                rec.perc_discount = (rec.discount_rate / 100) * rec.subtotal_amount
            else:
                rec.perc_discount = rec.discount_rate

    @api.depends('order_line.subtotal')
    def _compute_net_total(self):
        for rec in self:
            subtotal = 0
            for line in rec.order_line:
                subtotal = subtotal + line.subtotal
            rec.subtotal_amount = subtotal
            rec.net_total = rec.subtotal_amount - rec.perc_discount
            rec.amount_total = rec.net_total + rec.amount_tax
    #
    # @api.onchange('client_order_ref')
    # def _onchange_client_order_ref(self):
    #     for rec in self.order_line:
    #         print(rec.number)


class SaleOrderLineInh(models.Model):
    _inherit = 'sale.order.line'

    remarks = fields.Char('Remarks')
    number = fields.Integer(compute='_compute_get_number', store=True)
    vat_amount = fields.Float('VAT Amount', compute='_compute_vat_amount')
    subtotal = fields.Float('Subtotal', compute='_compute_subtotal')

    @api.depends('price_unit', 'product_uom_qty')
    def _compute_subtotal(self):
        for rec in self:
            rec.subtotal = rec.product_uom_qty * rec.price_unit

    def _compute_vat_amount(self):
        for rec in self:
            amount = 0
            for tax in rec.tax_id:
                amount = amount + tax.amount
            rec.vat_amount = (amount/100) * rec.price_unit

    @api.depends('sequence', 'order_id')
    def _compute_get_number(self):
        for order in self.mapped('order_id'):
            number = 1
            for line in order.order_line:
                line.number = number
                number += 1