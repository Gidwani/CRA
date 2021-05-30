# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleOrderInh(models.Model):
    _inherit = 'sale.order'

    perc_discount = fields.Float('Discount', compute="_compute_discount")
    net_total = fields.Float('Net Total', compute="_compute_net_total")
    perc = fields.Float(compute='compute_percentage')

    def compute_percentage(self):
        for rec in self:
            if rec.global_discount_type == 'percent':
                rec.perc = rec.global_order_discount
            else:
                rec.perc = (rec.global_order_discount/rec.amount_untaxed) * 100


    def _compute_discount(self):
        for rec in self:
            if rec.global_discount_type == 'percent':
                rec.perc_discount = (rec.global_order_discount / 100) * rec.amount_untaxed
            else:
                rec.perc_discount = rec.global_order_discount

    def _compute_net_total(self):
        for rec in self:
            rec.net_total = rec.amount_untaxed - rec.perc_discount
            rec.amount_total = rec.net_total + rec.amount_tax

    # @api.onchange('global_order_discount')
    # def _onchange_total_discount(self):
    #     self.perc = self.global_order_discount


class SaleOrderLineInh(models.Model):
    _inherit = 'sale.order.line'

    remarks = fields.Char('Remarks')
    number = fields.Integer(compute='_compute_get_number', store=True)
    vat_amount = fields.Float('VAT Amount', compute='_compute_vat_amount')


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