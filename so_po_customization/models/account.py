

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountMoveInh(models.Model):
    _inherit = 'account.move'

    perc_discount = fields.Float('Discount', compute='_compute_discount')
    net_total = fields.Float('Net Total', compute="_compute_net_total")
    perc = fields.Float(compute='compute_percentage')
    net_tax = fields.Float('Tax', compute='compute_taxes')
    subtotal_amount = fields.Float('Subtotal Amount', compute='_compute_net_total')
    total_amount_net = fields.Float('Total')
    total_amount_due = fields.Float('Amount Due')

    def get_payment_term_id(self):
        order = self.env['sale.order'].search([('name', '=', self.invoice_origin)])
        return order.payment_term_id.name

    def get_do_no(self):
        picking = self.env['stock.picking'].search([('origin', '=', self.invoice_origin), ('backorder_id', '=', False)], limit=1)
        # print(picking.name.split('/'))
        a = picking.name.split('/')
        name = a[1] + '/' + a[2] + '/' + a[3]
        return name

    def compute_taxes(self):
        flag = False
        total = 0
        for rec in self.invoice_line_ids:
            if rec.tax_ids:
                for tax in rec.tax_ids:
                    if tax.name == 'VAT 5%':
                        flag = True
                        total = total + rec.subtotal
        if flag:
            self.net_tax = (5 / 100) * total
        else:
            self.net_tax = 0

    def compute_percentage(self):
        for rec in self:
            if rec.discount_type == 'percent':
                rec.perc = rec.discount_rate
            else:
                rec.perc = (rec.discount_rate / rec.subtotal_amount) * 100

    def _compute_discount(self):
        for rec in self:
            if rec.discount_type == 'percent':
                rec.perc_discount = (rec.discount_rate / 100) * rec.subtotal_amount
            else:
                rec.perc_discount = rec.discount_rate

    @api.depends('invoice_line_ids.subtotal')
    def _compute_net_total(self):
        for rec in self:
            subtotal = 0
            for line in rec.invoice_line_ids:
                subtotal = subtotal + line.subtotal
            rec.subtotal_amount = subtotal
            rec.net_total = rec.subtotal_amount - rec.perc_discount
            rec.total_amount_net = rec.net_total + rec.net_tax
            rec.total_amount_due = rec.net_total + rec.net_tax


class AccountMoveLineInh(models.Model):
    _inherit = 'account.move.line'

    remarks = fields.Char("Remarks", compute='_compute_remarks')
    number = fields.Integer(compute='_compute_get_number', store=True)
    vat_amount = fields.Float('VAT Amount', compute='_compute_vat_amount')
    subtotal = fields.Float('Subtotal', compute='_compute_subtotal')

    @api.depends('price_unit', 'quantity')
    def _compute_subtotal(self):
        for rec in self:
            rec.subtotal = rec.quantity * rec.price_unit

    def _compute_vat_amount(self):
        for rec in self:
            amount = 0
            for tax in rec.tax_ids:
                if tax.name == 'VAT 5%':
                    amount = amount + tax.amount
            rec.vat_amount = (amount/100) * rec.price_unit

    @api.depends('sequence', 'move_id')
    def _compute_get_number(self):
        for order in self.mapped('move_id'):
            number = 1
            for line in order.invoice_line_ids:
                line.number = number
                number += 1

    def _compute_remarks(self):
        for rec in self:
            remark = ''
            purchases = self.env['purchase.order'].search([('name', '=', rec.move_id.invoice_origin)])
            sales = self.env['sale.order'].search([('name', '=', rec.move_id.invoice_origin)])
            if purchases:
                for purchase in purchases:
                    for line in purchase.order_line:
                        if rec.product_id.id == line.product_id.id:
                            remark = line.remarks
            if sales:
                for sale in sales:
                    for line in sale.order_line:
                        if rec.product_id.id == line.product_id.id:
                            remark = line.remarks
            rec.remarks = remark
