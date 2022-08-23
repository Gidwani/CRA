from odoo import models, fields
from odoo.exceptions import UserError


class DownloadWizard(models.TransientModel):
    _name = 'display.dialog.box'

    text = fields.Text()
    partner = fields.Text()

    def action_confirm(self):
        model = self.env.context.get('active_model')
        rec_model = self.env[model].browse(self.env.context.get('active_id'))
        # print(rec_model.id)
        return rec_model.action_manager_approve()

    def action_manager_approve(self):
        model = self.env.context.get('active_model')
        rec_model = self.env[model].browse(self.env.context.get('active_id'))
        if rec_model.invoice_origin:
            sale_order = self.env['sale.order'].search([('name', '=', rec_model.invoice_origin)])
            purchase_order = self.env['purchase.order'].search([('name', '=', rec_model.invoice_origin)])
            if sale_order:
                if rec_model.move_type == 'out_invoice':
                    total_qty = 0
                    total_invoice_qty = 0
                    sale_invoices = self.env['account.move'].search(
                        [('invoice_origin', '=', sale_order.name), ('move_type', '=', 'out_invoice'),
                         ('state', '=', 'posted')])
                    if sale_invoices:
                        for rec in sale_invoices.invoice_line_ids:
                            total_invoice_qty = total_invoice_qty + rec.quantity
                    for line in sale_order.order_line:
                        total_qty = total_qty + line.product_uom_qty
                    for invoice_line in rec_model.invoice_line_ids:
                        total_invoice_qty = total_invoice_qty + invoice_line.quantity
                    if total_invoice_qty <= total_qty:
                        record = super(DownloadWizard, rec_model).action_post()
                    else:
                        raise UserError('Quantity Should be less or equal to Sale Order Quantity')
                if rec_model.move_type == 'out_refund':
                    total_refund_qty = 0
                    total_refund_invoice_qty = 0
                    sale_refund_invoices = self.env['account.move'].search([('invoice_origin', '=', sale_order.name),
                                                                            ('move_type', '=', 'out_refund'),
                                                                            ('state', '=', 'posted')])
                    if sale_refund_invoices:
                        for rec in sale_refund_invoices.invoice_line_ids:
                            total_refund_invoice_qty = total_refund_invoice_qty + rec.quantity
                    for line in sale_order.order_line:
                        total_refund_qty = total_refund_qty + line.product_uom_qty
                    for invoice_line in rec_model.invoice_line_ids:
                        total_refund_invoice_qty = total_refund_invoice_qty + invoice_line.quantity
                    if total_refund_invoice_qty <= total_refund_qty:
                        record = super(DownloadWizard, rec_model).action_post()
                    else:
                        raise UserError('Return Quantity Should be less or equal to Sale Order Quantity')

            if purchase_order:
                if rec_model.move_type == 'in_invoice':
                    print('Purchase')
                    total_qty = 0
                    total_invoice_qty = 0
                    purchase_invoices = self.env['account.move'].search([('invoice_origin', '=', purchase_order.name),
                                                                         ('state', '=', 'posted')])
                    if purchase_invoices:
                        for rec in purchase_invoices.invoice_line_ids:
                            total_invoice_qty = total_invoice_qty + rec.quantity
                    for line in purchase_order.order_line:
                        total_qty = total_qty + line.product_uom_qty
                    for invoice_line in rec_model.invoice_line_ids:
                        total_invoice_qty = total_invoice_qty + invoice_line.quantity
                    if total_invoice_qty <= total_qty:
                        record = super(DownloadWizard, self).action_post()
                    else:
                        raise UserError('Quantity Should be less or equal to Purchase Order Quantity')
                if self.move_type == 'in_refund':
                    total_refund_qty = 0
                    total_refund_invoice_qty = 0
                    purchase_refund_invoices = self.env['account.move'].search(
                        [('invoice_origin', '=', purchase_order.name),
                         ('move_type', '=', 'in_refund'),
                         ('state', '=', 'posted')])
                    # print(purchase_refund_invoices)
                    if purchase_refund_invoices:
                        for rec in purchase_refund_invoices.invoice_line_ids:
                            total_refund_invoice_qty = total_refund_invoice_qty + rec.quantity
                    for line in purchase_order.order_line:
                        total_refund_qty = total_refund_qty + line.product_uom_qty
                    for invoice_line in rec_model.invoice_line_ids:
                        total_refund_invoice_qty = total_refund_invoice_qty + invoice_line.quantity
                    if total_refund_invoice_qty <= total_refund_qty:
                        record = super(DownloadWizard, rec_model).action_post()
                    else:
                        raise UserError('Return Quantity Should be less or equal to Purchase Order Quantity')
        else:
            record = super(DownloadWizard, rec_model).action_post()