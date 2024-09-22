

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero


class AccountMoveInh(models.Model):
    _inherit = 'account.move'

    perc_discount = fields.Float('Discount', compute='_compute_discount')
    net_total = fields.Float('Net Total', )
    perc = fields.Float(compute='compute_percentage')
    net_tax = fields.Float('Tax', compute='compute_taxes')
    subtotal_amount = fields.Float('Subtotal Amount', compute='_compute_net_total')
    total_amount_net = fields.Float('Total')
    total_amount_due = fields.Float('Amount Due')

    do_link = fields.Char(string='DO link')
    # po_no = fields.Char()

    @api.onchange('discount_rate', 'discount_type')
    def _onchange_sale_discount(self):
        for move in self:
            if move.invoice_line_ids:
                if move.invoice_line_ids[0].sale_line_ids or move.invoice_line_ids[0].purchase_order_id:
                    raise UserError('You cannot change invoice values.')

    def get_total(self):
        subtotal = 0
        for line in self.invoice_line_ids:
            subtotal = subtotal + line.subtotal
        subtotal_amount = subtotal

        if self.discount_type == 'percent':
            discount = (self.discount_rate / 100) * subtotal_amount
        else:
            discount = self.discount_rate
        net_total = subtotal_amount
        return net_total - discount

    def get_tax(self):
        for res in self:
            amount_tax = 0.0
            for rec in res.invoice_line_ids:
                amount_tax += rec.l10n_ae_vat_amount
            return amount_tax
        # flag = False
        # total = 0
        # for res in self:
        #     for rec in res.invoice_line_ids:
        #         if rec.tax_ids:
        #             for tax in rec.tax_ids:
        #                 # if tax.name == 'VAT 5% (Dubai)':
        #                 if tax.id == 1:
        #                     if res.move_type == 'out_invoice' or res.move_type == 'out_refund':
        #                         flag = True
        #                         total = total + rec.subtotal
        #                 else:
        #                     if tax.name == 'VAT 5%':
        #                         flag = True
        #                         total = total + rec.subtotal
        #     if flag:
        #         if res.discount_type == 'percent':
        #             subtotal = 0
        #             for line in res.invoice_line_ids:
        #                 subtotal = subtotal + line.subtotal
        #             subtotal_amount = subtotal
        #             discount = (res.discount_rate / 100) * subtotal_amount
        #         else:
        #             discount = res.discount_rate
        #         tax = (5 / 100) * (total - discount)
        #         return tax
        #     else:
        #         tax = 0
        #         return tax

    @api.model_create_multi
    def create(self, vals_list):
        res_ids = super(AccountMoveInh, self).create(vals_list)
        res_ids._assign_the_DO_link()
        return res_ids

    def _assign_the_DO_link(self):
        for r in self:
            if not r.do_link:
                for k in r.invoice_line_ids:
                    saleorder = self.env['sale.order'].search([("name", '=', r.invoice_origin)])
                    for l in saleorder.picking_ids:
                        if r.invoice_origin == l.sale_id.name:
                            for j in l.move_line_ids_without_package:
                                if j.picking_id.invoice_link != True:
                                    if j.product_id == k.product_id:
                                        if j.quantity == k.quantity:
                                            r.do_link = l.name
                                            j.picking_id.invoice_link = True

    def get_payment_term_id(self):
        order = self.env['sale.order'].search([('name', '=', self.invoice_origin)])
        return order.payment_term_id.name

    def get_client_order_ref(self):
        order = self.env['sale.order'].search([('name', '=', self.invoice_origin)])
        return order.client_order_ref

    def get_do_no(self):
        pickings = self.env['stock.picking'].search([('name', '=', self.do_link)])
        return pickings.name

    @api.depends('invoice_line_ids', 'perc_discount', 'invoice_line_ids.tax_ids', 'invoice_line_ids.subtotal')
    def compute_taxes(self):
        for res in self:
            amount_tax = 0.0
            for rec in res.invoice_line_ids:
                amount_tax += rec.l10n_ae_vat_amount
            res.net_tax = amount_tax
        # flag = False
        # total = 0
        # for res in self:
        #     for rec in res.invoice_line_ids:
        #         if rec.tax_ids:
        #             for tax in rec.tax_ids:
        #                 # if tax.name == 'VAT 5% (Dubai)':
        #                 if tax.id == 1:
        #                     if res.move_type == 'out_invoice' or res.move_type == 'out_refund':
        #                         flag = True
        #                         total = total + rec.subtotal
        #                 else:
        #                     if tax.name == 'VAT 5%':
        #                         flag = True
        #                         total = total + rec.subtotal
        #     if flag:
        #         res.net_tax = (5 / 100) * (total - res.perc_discount)
        #     else:
        #         res.net_tax = 0

    @api.depends('discount_rate', 'discount_type')
    def compute_percentage(self):
        for rec in self:
            if rec.discount_type == 'percent':
                rec.perc = rec.discount_rate
            else:
                rec.perc = (rec.discount_rate / rec.subtotal_amount) * 100

    @api.depends('discount_rate', 'discount_type')
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
            # rec.total_amount_net = rec.net_total + rec.net_tax
            rec.total_amount_net = rec.amount_total
            rec.total_amount_due = rec.amount_residual


class AccountMoveLineInh(models.Model):
    _inherit = 'account.move.line'

    remarks = fields.Char("Remarks", compute='_compute_remarks')
    number = fields.Integer(compute='_compute_get_number', store=True)
    vat_amount = fields.Float('VAT Amount', compute='_compute_vat_amount_custom')
    subtotal = fields.Float('Subtotal', compute='_compute_subtotal')

    @api.onchange('tax_ids', 'price', 'quantity')
    def _onchange_sale_taxes(self):
        for line in self:
            if line.sale_line_ids or line.purchase_order_id:
                raise UserError('You cannot change invoice/bill values.')

    @api.depends('price_unit', 'quantity')
    def _compute_subtotal(self):
        for rec in self:
            rec.subtotal = rec.quantity * rec.price_unit

    @api.depends('tax_ids', 'price_unit', 'quantity')
    def _compute_vat_amount_custom(self):
        for rec in self:
            amount = 0
            for tax in rec.tax_ids:
                if rec.move_id.move_type == 'out_invoice' or rec.move_id.move_type == 'out_refund':
                    if tax.id == 1:
                        amount = amount + tax.amount
                else:
                    if tax.id == 19:
                        amount = amount + tax.amount
            rec.vat_amount = ((amount/100) * rec.price_unit) * rec.quantity

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
            if rec.sale_line_ids:
                remark = rec.sale_line_ids[0].remarks
            if rec.purchase_line_id:
                remark = rec.purchase_line_id.remarks
            rec.remarks = remark
