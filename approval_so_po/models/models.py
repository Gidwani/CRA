# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from lxml import etree
from odoo.tools.float_utils import float_compare

from odoo.exceptions import UserError


class SaleOrderInh(models.Model):
    _inherit = 'sale.order'

    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('manager', 'Approval From Manager'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, tracking=3, default='draft')

    x_css = fields.Html(string='CSS', sanitize=False, compute='_compute_css', store=False)

    @api.depends('state')
    def _compute_css(self):
        for application in self:
            # Modify below condition
            if self.env.user.has_group('approval_so_po.group_sale_remove_edit_user') and application.state != 'draft':
                application.x_css = '<style>.o_form_button_edit {display: none !important;}</style>'
            else:
                application.x_css = False

    def action_reject(self):
        self.state = 'draft'

    def action_confirm(self):
        self.state = 'manager'

    def action_manager_approve(self):
        record = super(SaleOrderInh, self).action_confirm()


class PurchaseOrderInh(models.Model):
    _inherit = 'purchase.order'

    state = fields.Selection([
        ('draft', 'RFQ'),
        ('sent', 'RFQ Sent'),
        ('to approve', 'To Approve'),
        ('manager', 'Approval From Manager'),
        ('purchase', 'Purchase Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, index=True, copy=False, default='draft', tracking=True)
    x_css = fields.Html(string='CSS', sanitize=False, compute='_compute_css', store=False)

    @api.depends('state')
    def _compute_css(self):
        for application in self:
            # Modify below condition
            if self.env.user.has_group('approval_so_po.group_purchase_remove_edit_user') and application.state != 'draft':
                application.x_css = '<style>.o_form_button_edit {display: none !important;}</style>'
            else:
                application.x_css = False

    def action_reject(self):
        self.state = 'draft'

    def button_confirm(self):
        self.state = 'manager'

    def action_manager_approve(self):
        for order in self:
            if order.state not in ['draft', 'sent', 'manager']:
                continue
            order._add_supplier_to_product()
            # Deal with double validation process
            if order._approval_allowed():
                order.button_approve()
            else:
                order.write({'state': 'to approve'})
            if order.partner_id not in order.message_partner_ids:
                order.message_subscribe([order.partner_id.id])
        return True


class AccountPaymentInh(models.Model):
    _inherit = 'account.payment'

    x_css = fields.Html(string='CSS', sanitize=False, compute='_compute_css', store=False)

    @api.depends('state')
    def _compute_css(self):
        for application in self:
            # Modify below condition
            if self.env.user.has_group(
                    'approval_so_po.group_account_remove_edit_user') and application.state != 'draft':
                application.x_css = '<style>.o_form_button_edit {display: none !important;}</style>'
            else:
                application.x_css = False

    def action_post(self):
        self.state = 'manager'

    def action_reject(self):
        self.state = 'draft'

    def action_manager_approve(self):
        record = super(AccountPaymentInh, self).action_post()

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        result = super(AccountPaymentInh, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu)
        if self.env.user.has_group('account.group_account_manager'):
            pass
        elif self.env.user.has_group('approval_so_po.group_view_only_user'):
            temp = etree.fromstring(result['arch'])
            temp.set('duplicate', '0')
            temp.set('edit', '0')
            temp.set('create', '0')
            temp.set('delete', '0')
            result['arch'] = etree.tostring(temp)
        else:
            temp = etree.fromstring(result['arch'])
            temp.set('duplicate', '0')
            temp.set('delete', '0')
            result['arch'] = etree.tostring(temp)
        return result

class AccountMoveInh(models.Model):
    _inherit = 'account.move'

    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('manager', 'Approval from Manager'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled'),
    ], string='Status', required=True, readonly=True, copy=False, tracking=True,
        default='draft')

    x_css = fields.Html(string='CSS', sanitize=False, compute='_compute_css', store=False)

    @api.depends('state')
    def _compute_css(self):
        for application in self:
            # Modify below condition
            if self.env.user.has_group(
                    'approval_so_po.group_account_remove_edit_user') and application.state != 'draft':
                application.x_css = '<style>.o_form_button_edit {display: none !important;}</style>'
            else:
                application.x_css = False

    def action_reject(self):
        self.state = 'draft'

    def action_post(self):
        if self.invoice_origin:
            sale_order = self.env['sale.order'].search([('name', '=', self.invoice_origin)])
            purchase_order = self.env['purchase.order'].search([('name', '=', self.invoice_origin)])
            if sale_order:
                total_qty = 0
                total_invoice_qty = 0
                for line in sale_order.order_line:
                    total_qty = total_qty + line.product_uom_qty
                for invoice_line in self.invoice_line_ids:
                    total_invoice_qty = total_invoice_qty + invoice_line.quantity
                if total_invoice_qty <= total_qty:
                    self.state = 'manager'
                else:
                    raise UserError('Quantity Should be equal to Sale Order Quantity')
            if purchase_order:
                print('Purchase')
                total_qty = 0
                total_invoice_qty = 0
                for line in purchase_order.order_line:
                    total_qty = total_qty + line.product_uom_qty
                for invoice_line in self.invoice_line_ids:
                    total_invoice_qty = total_invoice_qty + invoice_line.quantity
                if total_invoice_qty <= total_qty:
                    self.state = 'manager'
                else:
                    raise UserError('Quantity Should be equal to Purchase Order Quantity')
        else:
            record = super(AccountMoveInh, self).action_post()

    def action_manager_approve(self):
        record = super(AccountMoveInh, self).action_post()

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        result = super(AccountMoveInh, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu)
        if self.env.user.has_group('account.group_account_manager'):
            pass
        elif self.env.user.has_group('approval_so_po.group_view_only_user'):
            temp = etree.fromstring(result['arch'])
            temp.set('duplicate', '0')
            temp.set('edit', '0')
            temp.set('create', '0')
            temp.set('delete', '0')
            result['arch'] = etree.tostring(temp)
        else:
            temp = etree.fromstring(result['arch'])
            temp.set('duplicate', '0')
            temp.set('delete', '0')
            result['arch'] = etree.tostring(temp)
        return result


class StockPickingInh(models.Model):
    _inherit = 'stock.picking'

    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting'),
        ('assigned', 'Ready'),
        ('manager', 'Approval from Manager'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', compute='_compute_state',
        copy=False, index=True, readonly=True, store=True, tracking=True,
        help=" * Draft: The transfer is not confirmed yet. Reservation doesn't apply.\n"
             " * Waiting another operation: This transfer is waiting for another operation before being ready.\n"
             " * Waiting: The transfer is waiting for the availability of some products.\n(a) The shipping policy is \"As soon as possible\": no product could be reserved.\n(b) The shipping policy is \"When all products are ready\": not all the products could be reserved.\n"
             " * Ready: The transfer is ready to be processed.\n(a) The shipping policy is \"As soon as possible\": at least one product has been reserved.\n(b) The shipping policy is \"When all products are ready\": all product have been reserved.\n"
             " * Done: The transfer has been processed.\n"
             " * Cancelled: The transfer has been cancelled.")

    x_css = fields.Html(string='CSS', sanitize=False, compute='_compute_css', store=False)

    @api.depends('state')
    def _compute_css(self):
        for application in self:
            # Modify below condition
            if self.env.user.has_group(
                    'approval_so_po.group_stock_remove_edit_user') and application.state not in ['assigned', 'draft']:
                application.x_css = '<style>.o_form_button_edit {display: none !important;}</style>'
            else:
                application.x_css = False

    def action_reject(self):
        self.state = 'assigned'

    def button_validate(self):
        flag = False
        for line in self.move_ids_without_package:
            if line.quantity_done <= line.product_uom_qty:
                flag = True
            else:
                raise UserError('Done Quantity Cannot be greater than Demand')
        if flag:
            self.state = 'manager'

    def action_manager_approve(self):
        record = super(StockPickingInh, self).button_validate()
        return record

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        result = super(StockPickingInh, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu)
        if self.env.user.has_group('stock.group_stock_manager'):
            pass
        else:
            temp = etree.fromstring(result['arch'])
            temp.set('duplicate', '0')
            temp.set('delete', '0')
            result['arch'] = etree.tostring(temp)
        return result


class StockBackorderConfirmationInh(models.TransientModel):
    _inherit = 'stock.backorder.confirmation'

    def process(self):
        pickings_to_do = self.env['stock.picking']
        pickings_not_to_do = self.env['stock.picking']
        for line in self.backorder_confirmation_line_ids:
            if line.to_backorder is True:
                pickings_to_do |= line.picking_id
            else:
                pickings_not_to_do |= line.picking_id

        for pick_id in pickings_not_to_do:
            moves_to_log = {}
            for move in pick_id.move_lines:
                if float_compare(move.product_uom_qty,
                                 move.quantity_done,
                                 precision_rounding=move.product_uom.rounding) > 0:
                    moves_to_log[move] = (move.quantity_done, move.product_uom_qty)
            pick_id._log_less_quantities_than_expected(moves_to_log)

        pickings_to_validate = self.env.context.get('button_validate_picking_ids')
        if pickings_to_validate:
            pickings_to_validate = self.env['stock.picking'].browse(pickings_to_validate).with_context(
                skip_backorder=True)
            if pickings_not_to_do:
                pickings_to_validate = pickings_to_validate.with_context(
                    picking_ids_not_to_backorder=pickings_not_to_do.ids)
            return pickings_to_validate.action_manager_approve()
        return True

    def process_cancel_backorder(self):
        pickings_to_validate = self.env.context.get('button_validate_picking_ids')
        if pickings_to_validate:
            return self.env['stock.picking'] \
                .browse(pickings_to_validate) \
                .with_context(skip_backorder=True, picking_ids_not_to_backorder=self.pick_ids.ids) \
                .action_manager_approve()
        return True


class StockImmediateTransferInh(models.TransientModel):
    _inherit = 'stock.immediate.transfer'

    def process(self):
        pickings_to_do = self.env['stock.picking']
        pickings_not_to_do = self.env['stock.picking']
        for line in self.immediate_transfer_line_ids:
            if line.to_immediate is True:
                pickings_to_do |= line.picking_id
            else:
                pickings_not_to_do |= line.picking_id

        for picking in pickings_to_do:
            # If still in draft => confirm and assign
            if picking.state == 'draft':
                picking.action_confirm()
                if picking.state != 'assigned':
                    picking.action_assign()
                    if picking.state != 'assigned':
                        raise UserError(_("Could not reserve all requested products. Please use the \'Mark as Todo\' button to handle the reservation manually."))
            for move in picking.move_lines.filtered(lambda m: m.state not in ['done', 'cancel']):
                for move_line in move.move_line_ids:
                    move_line.qty_done = move_line.product_uom_qty

        pickings_to_validate = self.env.context.get('button_validate_picking_ids')
        if pickings_to_validate:
            pickings_to_validate = self.env['stock.picking'].browse(pickings_to_validate)
            pickings_to_validate = pickings_to_validate - pickings_not_to_do
            return pickings_to_validate.with_context(skip_immediate=True).action_manager_approve()
        return True
