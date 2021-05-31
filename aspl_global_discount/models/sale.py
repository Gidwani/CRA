# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    discount_type = fields.Selection([('fixed_amount', 'Fixed Amount'),
                                      ('percentage_discount', 'Percentage')],
                                     string="Discount Type")
    discount_rate = fields.Float(string="Discount Rate")
    discount = fields.Monetary(string="Discount", compute='_compute_net_total')
    net_total = fields.Monetary(string="Net Total", compute='_compute_net_total')

    @api.depends('discount_rate', 'amount_total', 'discount_type')
    def _compute_net_total(self):
        if self.discount_type == 'fixed_amount':
            if self.discount_rate <= self.amount_total:
                self.discount = self.discount_rate
            else:
                raise UserError(_("Discount Cannot be more than Total"))
        elif self.discount_type == 'percentage_discount':
            if self.discount_rate <= 100:
                self.discount = (self.amount_total * self.discount_rate) / 100
            else:
                raise UserError(_("Discount rate cannot be more than 100%"))
        self.net_total = (self.amount_total - self.discount)

    def action_view_invoice(self):
        invoices = self.mapped('invoice_ids')
        action = self.env.ref('account.action_move_out_invoice_type').read()[0]
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            action['views'] = [(self.env.ref('account.view_move_form').id, 'form')]
            action['res_id'] = invoices.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        for invoice in invoices:
            invoice.discount_type = self.discount_type
            invoice.discount_rate = self.discount_rate
            invoice.discount = self.discount
            invoice.net_total = self.net_total
        context = {
            'default_move_type': 'out_invoice',
        }
        if len(self) == 1:
            context.update({
                'default_partner_id': self.partner_id.id,
                'default_partner_shipping_id': self.partner_shipping_id.id,
                'default_invoice_payment_term_id': self.payment_term_id.id,
                'default_invoice_origin': self.mapped('name'),
                'default_user_id': self.user_id.id,
            })
        action['context'] = context
        return action

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4
