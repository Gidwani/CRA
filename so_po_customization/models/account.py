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

    def compute_taxes(self):
        flag = False
        for rec in self.invoice_line_ids:
            if rec.tax_ids:
                flag = True
        if flag:
            self.net_tax = (5 / 100) * self.net_total
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
            # rec.amount_total = rec.net_total + rec.net_tax
            rec.total_amount_due = rec.net_total + rec.net_tax

    # def action_post(self):
    #     rec = super(AccountMoveInh, self).action_post()
    #     debit_sum = 0.0
    #     credit_sum = 0.0
    #     expense_account = self.env['account.account'].search([('name', '=', 'Global Invoice Discount')])[0]
    #     pay_account = self.env['account.account'].search([('user_type_id', '=', 'Payable')])[0]
    #     line_ids = []
    #     for line in self.line_ids:
    #         print(line)
    #         if line.account_id.name == 'Global Invoice Discount':
    #             debit_line = (0, 0, {
    #                 'name': 'VAT 5.00%',
    #                 'debit': 0.0,
    #                 'credit': self.perc_discount - 0.75,
    #                 'account_id': line.account_id.id,
    #                 'exclude_from_invoice_tab': True,
    #             })
    #             line_ids.append(debit_line)
    #             debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']
    #         if line.account_id.name == 'Tax Received':
    #             credit_line = (0, 0, {
    #                 'name': 'Global Discount',
    #                 'debit': self.net_tax,
    #                 'credit': 0.0,
    #                 'account_id': line.account_id.id,
    #                 'exclude_from_invoice_tab': True,
    #             })
    #             line_ids.append(credit_line)
    #             credit_sum += credit_line[2]['credit'] - credit_line[2]['debit']
    #     vals = {
    #         # 'date': fields.Date.today(),
    #         # 'move_type': 'entry',
    #         'line_ids': line_ids,
    #     }
    #     # print(self.perc_discount - 0.75, self.net_tax)
    #     move = super(AccountMoveInh, self).write(vals)
    #
    #     return rec


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
