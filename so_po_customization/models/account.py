from odoo import models, fields, api


class AccountMoveInh(models.Model):
    _inherit = 'account.move'

    perc_discount = fields.Float('Discount', compute='_compute_discount')
    net_total = fields.Float('Net Total', compute="_compute_net_total")
    perc = fields.Float(compute='compute_percentage')

    def compute_percentage(self):
        for rec in self:
            if rec.global_discount_type == 'percent':
                rec.perc = rec.global_order_discount
            else:
                rec.perc = (rec.global_order_discount / rec.amount_untaxed) * 100

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


class AccountMoveLineInh(models.Model):
    _inherit = 'account.move.line'

    remarks = fields.Char("Remarks", compute='_compute_remarks')
    number = fields.Integer(compute='_compute_get_number', store=True)
    vat_amount = fields.Float('VAT Amount', compute='_compute_vat_amount')

    def _compute_vat_amount(self):
        for rec in self:
            amount = 0
            for tax in rec.tax_ids:
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
