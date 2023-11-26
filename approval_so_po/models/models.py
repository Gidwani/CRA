# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from lxml import etree
from odoo.tools.float_utils import float_compare

from odoo.exceptions import UserError


class StockScrapInh(models.Model):
    _inherit = 'stock.scrap'

    state = fields.Selection([
        ('draft', 'Draft'),
        ('manager', 'Approval From Manager'),
        ('done', 'Done')],
        string='Status', default="draft", readonly=True, tracking=True)
    x_css = fields.Html(string='CSS', sanitize=False, compute='_compute_css', store=False)

    def action_reject(self):
        self.state = 'draft'

    def action_validate(self):
        self.state = 'manager'

    def action_manager_approve(self):
        record = super(StockScrapInh, self).action_validate()

    @api.depends('state')
    def _compute_css(self):
        for application in self:
            # Modify below condition
            if self.env.user.has_group('approval_so_po.group_sale_remove_edit_user') and application.state != 'draft':
                application.x_css = '<style>.o_form_button_edit {display: none !important;}</style>'
            else:
                application.x_css = False


class StockMoveLineInh(models.Model):
    _inherit = 'stock.move.line'

    @api.onchange('product_id')
    def onchange_product_id(self):
        outgoing = self.env['stock.picking.type'].search([('code', '=', 'outgoing')])
        # incoming = self.env['stock.picking.type'].search([('code', '=', 'incoming')])
        if self.picking_id.sale_id:
            if self.picking_id.origin and self.picking_id.picking_type_id.id == outgoing.id:
                raise UserError('You cannot add Product in this Stage')

    @api.onchange('qty_done')
    def onchange_done_qty(self):
        for rec in self:
            # print(rec.move_id)
            # print(rec.move_id.product_uom_qty)
            # for do_line in rec.picking_id.move_ids_without_package:
            # print(do_line)
            #     if rec.product_id.id == do_line.product_id.id:
            # print(do_line.product_uom_qty, rec.qty_done)
            # if rec.move_id.product_uom_qty == rec.qty_done:
            if not rec.qty_done <= rec.move_id.product_uom_qty:
                raise UserError('Quantity Should be Less or Equal to Reserved')


class StockMoveInh(models.Model):
    _inherit = 'stock.move'

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.picking_id.origin:
            raise UserError('You cannot add Product in this Stage')

# class StockReturnPickingLineInh(models.TransientModel):
#     _inherit = 'stock.return.picking.line'
#
#     product_uom_category_id = fields.Many2one(related='uom_id.category_id', readonly=True)


class StockReturnPickingInh(models.TransientModel):
    _inherit = 'stock.return.picking'

    def create_returns(self):
        model = self.env.context.get('active_model')
        rec = self.env[model].browse(self.env.context.get('active_id'))
        if rec.sale_id:
            total_qty = 0
            for line in rec.sale_id.order_line:
                total_qty = total_qty + line.product_uom_qty

            incoming = self.env['stock.picking.type'].search([('code', '=', 'incoming')], limit=1)
            returns_do = self.env['stock.picking'].search(
                [('picking_type_id', '=', incoming.id), ('sale_id', '=', rec.sale_id.id), ('state', '=', 'done')])
            total_return = 0
            for do_line in returns_do:
                for rec_line in do_line.move_ids_without_package:
                    total_return = total_return + rec_line.quantity_done
            for return_line in self.product_return_moves:
                for pro_line in rec.sale_id.order_line:
                    if pro_line.product_uom.id == return_line.uom_id.id:
                        if not return_line.quantity <= (total_qty - total_return):
                            raise UserError('Quantity Should be Less or Equal to Sale order Qty')
                        else:
                            new_picking = super(StockReturnPickingInh, self).create_returns()
                            print(new_picking['res_id'])
                            pic = self.env['stock.picking'].browse([new_picking['res_id']])
                            pic.is_return_order = True
                            return new_picking
                    else:
                        if not (return_line.quantity/6) <= (total_qty - total_return):
                            raise UserError('Quantity Should be Less or Equal to Sale order Qty')
                        else:
                            new_picking = super(StockReturnPickingInh, self).create_returns()
                            print(new_picking['res_id'])
                            pic = self.env['stock.picking'].browse([new_picking['res_id']])
                            pic.is_return_order = True
                            return new_picking
        elif rec.purchase_id:
            print('Purchase')
            total_qty = 0
            for line in rec.purchase_id.order_line:
                total_qty = total_qty + line.product_qty

            outgoing = self.env['stock.picking.type'].search([('code', '=', 'outgoing')], limit=1)
            returns_do = self.env['stock.picking'].search(
                [('picking_type_id', '=', outgoing.id), ('purchase_id', '=', rec.purchase_id.id),
                 ('state', '=', 'done')])
            print(returns_do)
            total_return = 0
            for do_line in returns_do:
                for rec_line in do_line.move_ids_without_package:
                    total_return = total_return + rec_line.quantity_done

            for return_line in self.product_return_moves:
                for pro_line in rec.purchase_id.order_line:
                    if pro_line.product_uom.id == return_line.uom_id.id:
                        if not return_line.quantity <= (total_qty - total_return):
                            raise UserError('Quantity Should be Less or Equal to Sale order Qty')
                        else:
                            new_picking = super(StockReturnPickingInh, self).create_returns()
                            print(new_picking['res_id'])
                            pic = self.env['stock.picking'].browse([new_picking['res_id']])
                            pic.is_return_order = True
                            return new_picking
                    else:
                        if not (return_line.quantity / 6) <= (total_qty - total_return):
                            raise UserError('Quantity Should be Less or Equal to Sale order Qty')
                        else:
                            new_picking = super(StockReturnPickingInh, self).create_returns()
                            print(new_picking['res_id'])
                            pic = self.env['stock.picking'].browse([new_picking['res_id']])
                            pic.is_return_order = True
                            return new_picking
        else:
            new_picking = super(StockReturnPickingInh, self).create_returns()
            print(new_picking['res_id'])
            pic = self.env['stock.picking'].browse([new_picking['res_id']])
            pic.is_return_order = True
            return new_picking


class ResPartnerInh(models.Model):
    _inherit = 'res.partner'

    state = fields.Selection([
        ('manager', 'Waiting for Approval'),
        ('approved', 'Approved')],
        string='Status', default="manager", readonly=True, tracking=True)

    x_css = fields.Html(string='CSS', sanitize=False, compute='_compute_css', store=False)
    x_css_set = fields.Html(string='CSS', sanitize=False, compute='_compute_css_set', store=False)

    def _compute_css(self):
        for application in self:
            if self.env.user.has_group('approval_so_po.group_contact_user'):
                application.x_css = '<style>.o_cp_action_menus {display: none !important;}</style>'
            else:
                application.x_css = False

    def _compute_css_set(self):
        for application in self:
            if self.env.user.has_group('base.group_system'):
                application.x_css_set = False
            else:
                application.x_css_set = '<style>.o_cp_action_menus {display: none !important;}</style>'

    def write(self, vals):
        pre_name = self.name
        res = super().write(vals)
        if 'fromso' not in self._context and 'Iscreated' not in self._context and self.env.user.has_group('approval_so_po.group_contact_user') and 'copy' not in pre_name:
            raise UserError('You cannot edit this form.')
        return res

    @api.model
    def create(self, vals):
        record = super(ResPartnerInh, self.with_context(Iscreated=True)).create(vals)
        record.update({
            'active': False,
            'state': 'manager',
        })
        return record

    def action_reject(self):
        self.active = False

    def action_manager_approve(self):
        self.state = 'approved'
        self.active = True


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

    @api.model
    def create(self, vals):
        record = super(SaleOrderInh, self.with_context(fromso=True)).create(vals)
        return record

    def action_reject(self):
        self.state = 'draft'

    def action_confirm(self):
        self.state = 'manager'

    def get_quant_lines(self):
        domain_loc = self.env['product.product']._get_domain_locations()[0]
        quant_ids = [l['id'] for l in self.env['stock.quant'].search_read(domain_loc, ['id'])]
        return quant_ids

    def action_manager_approve(self):
        record = super(SaleOrderInh, self).action_confirm()
        for res_line in self.order_line:
            total = 0
            quants = self.get_quant_lines()
            quants = self.env['stock.quant'].browse(quants)
            for q_line in quants:
                if q_line.product_tmpl_id.id == res_line.product_id.product_tmpl_id.id:
                    total = total + q_line.available_quantity
            res_line.product_id.product_tmpl_id.available_qty = total


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
            if self.env.user.has_group(
                    'approval_so_po.group_purchase_remove_edit_user') and application.state != 'draft':
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
            # for line in self.order_line:
            #     line.product_id.product_tmpl_id.incoming_quantity = line.product_id.product_tmpl_id.incoming_quantity + line.product_qty
        return True

    def _approval_allowed(self):
        """Returns whether the order qualifies to be approved by the current user"""
        self.ensure_one()
        return (
                self.company_id.po_double_validation == 'one_step'
                or (self.company_id.po_double_validation == 'two_step'
                    and self.amount_total < self.env.company.currency_id._convert(
                    self.company_id.po_double_validation_amount, self.currency_id, self.company_id,
                    self.date_order or fields.Date.today()))
                or self.user_has_groups('purchase.group_purchase_manager'))


class AccountPaymentRegisterInh(models.TransientModel):
    _inherit = 'account.payment.register'

    available_partner_bank_ids = fields.Many2many('res.partner.bank')


class AccountPaymentInh(models.Model):
    _inherit = 'account.payment'

    x_css = fields.Html(string='CSS', sanitize=False, compute='_compute_css', store=False)
    available_partner_bank_ids = fields.Many2many('res.partner.bank')

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


class AccountMoveLineInh(models.Model):
    _inherit = 'account.move.line'

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.move_id.invoice_origin:
            raise UserError('You cannot add Product in this Stage')

    @api.onchange('price_unit')
    def onchange_price_unit(self):
        if self.move_id.invoice_origin:
            raise UserError('You cannot change Product Price')

    @api.onchange('discount')
    def onchange_discount(self):
        if self.move_id.invoice_origin:
            raise UserError('You cannot change Discount')


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

    # x_css_tree = fields.Html(string='CSS', sanitize=False, compute='_compute_css_tree', store=False)

    @api.depends('state')
    def _compute_css(self):
        for application in self:
            # Modify below condition
            if self.env.user.has_group(
                    'approval_so_po.group_account_remove_edit_user') and application.state != 'draft':
                application.x_css = '<style>.o_form_button_edit {display: none !important;}</style>'
            else:
                application.x_css = False

    # def _compute_css_tree(self):
    #     for application in self:
    #         # Modify below condition
    #         if self.env.user.has_group(
    #                 'approval_so_po.group_payment_manager') or self.env.user.has_group(
    #                 'approval_so_po.group_payment_user'):
    #             application.x_css_tree = '<style>.btn btn-secondary {display: none !important;}</style>'
    #         else:
    #             application.x_css_tree = False

    def action_reject(self):
        self.state = 'draft'

    def action_post(self):
        if self.invoice_origin:
            sale_order = self.env['sale.order'].search([('name', '=', self.invoice_origin)])
            purchase_order = self.env['purchase.order'].search([('name', '=', self.invoice_origin)])
            if sale_order:
                if self.move_type == 'out_invoice':
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
                    for invoice_line in self.invoice_line_ids:
                        total_invoice_qty = total_invoice_qty + invoice_line.quantity
                    if total_invoice_qty <= total_qty:
                        self.state = 'manager'
                    else:
                        raise UserError('Quantity Should be less or equal to Sale Order Quantity')
                if self.move_type == 'out_refund':
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
                    for invoice_line in self.invoice_line_ids:
                        total_refund_invoice_qty = total_refund_invoice_qty + invoice_line.quantity
                    if total_refund_invoice_qty <= total_refund_qty:
                        self.state = 'manager'
                    else:
                        raise UserError('Return Quantity Should be less or equal to Sale Order Quantity')

            if purchase_order:
                if self.move_type == 'in_invoice':
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
                    for invoice_line in self.invoice_line_ids:
                        total_invoice_qty = total_invoice_qty + invoice_line.quantity
                    if total_invoice_qty <= total_qty:
                        self.state = 'manager'
                    else:
                        raise UserError('Quantity Should be less or equal to Purchase Order Quantity')
                if self.move_type == 'in_refund':
                    total_refund_qty = 0
                    total_refund_invoice_qty = 0
                    purchase_refund_invoices = self.env['account.move'].search(
                        [('invoice_origin', '=', purchase_order.name),
                         ('move_type', '=', 'in_refund'),
                         ('state', '=', 'posted')])
                    if purchase_refund_invoices:
                        for rec in purchase_refund_invoices.invoice_line_ids:
                            total_refund_invoice_qty = total_refund_invoice_qty + rec.quantity
                    print(purchase_refund_invoices)
                    for line in purchase_order.order_line:
                        total_refund_qty = total_refund_qty + line.product_uom_qty
                    for invoice_line in self.invoice_line_ids:
                        total_refund_invoice_qty = total_refund_invoice_qty + invoice_line.quantity
                    if total_refund_invoice_qty <= total_refund_qty:
                        self.state = 'manager'
                    else:
                        raise UserError('Return Quantity Should be less or equal to Purchase Order Quantity')
        else:
            self.state = 'manager'
            # record = super(AccountMoveInh, self).action_post()

    def action_manager_approve(self):
        if self.invoice_origin:
            sale_order = self.env['sale.order'].search([('name', '=', self.invoice_origin)])
            purchase_order = self.env['purchase.order'].search([('name', '=', self.invoice_origin)])
            if sale_order:
                if self.move_type == 'out_invoice':
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
                    for invoice_line in self.invoice_line_ids:
                        total_invoice_qty = total_invoice_qty + invoice_line.quantity
                    if total_invoice_qty <= total_qty:
                        record = super(AccountMoveInh, self).action_post()
                    else:
                        raise UserError('Quantity Should be less or equal to Sale Order Quantity')
                if self.move_type == 'out_refund':
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
                    for invoice_line in self.invoice_line_ids:
                        total_refund_invoice_qty = total_refund_invoice_qty + invoice_line.quantity
                    if total_refund_invoice_qty <= total_refund_qty:
                        record = super(AccountMoveInh, self).action_post()
                    else:
                        raise UserError('Return Quantity Should be less or equal to Sale Order Quantity')

            if purchase_order:
                if self.move_type == 'in_invoice':
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
                    for invoice_line in self.invoice_line_ids:
                        if invoice_line.product_id:
                            total_invoice_qty = total_invoice_qty + invoice_line.quantity
                    if total_invoice_qty <= total_qty:
                        record = super(AccountMoveInh, self).action_post()
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
                    for invoice_line in self.invoice_line_ids:
                        total_refund_invoice_qty = total_refund_invoice_qty + invoice_line.quantity
                    if total_refund_invoice_qty <= total_refund_qty:
                        record = super(AccountMoveInh, self).action_post()
                    else:
                        raise UserError('Return Quantity Should be less or equal to Purchase Order Quantity')
        else:
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


class SaleAdvancePaymentInh(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    def create_invoices(self):
        if self.env.user.has_group('approval_so_po.group_allow_full_refund'):
            rec = super(SaleAdvancePaymentInh, self).create_invoices()
        elif not self.env.user.has_group(
                'approval_so_po.group_allow_full_refund') and self.advance_payment_method == 'delivered':
            rec = super(SaleAdvancePaymentInh, self).create_invoices()
        else:
            raise UserError('You cannot create Down Payment.')


class AccountMoveReversalInh(models.TransientModel):
    _inherit = 'account.move.reversal'

    def reverse_moves(self):
        if self.env.user.has_group('approval_so_po.group_allow_full_refund'):
            self.action_reverse_inh()
        elif not self.env.user.has_group('approval_so_po.group_allow_full_refund') and self.refund_method == 'refund':
            self.action_reverse_inh()
        else:
            raise UserError('You cannot Full Refund.')

    def action_reverse_inh(self):
        self.ensure_one()
        moves = self.move_ids

        # Create default values.
        default_values_list = []
        for move in moves:
            default_values_list.append(self._prepare_default_reversal(move))

        batches = [
            [self.env['account.move'], [], True],  # Moves to be cancelled by the reverses.
            [self.env['account.move'], [], False],  # Others.
        ]
        for move, default_vals in zip(moves, default_values_list):
            is_auto_post = bool(default_vals.get('auto_post'))
            is_cancel_needed = not is_auto_post and self.refund_method in ('cancel', 'modify')
            batch_index = 0 if is_cancel_needed else 1
            batches[batch_index][0] |= move
            batches[batch_index][1].append(default_vals)

        # Handle reverse method.
        moves_to_redirect = self.env['account.move']
        for moves, default_values_list, is_cancel_needed in batches:
            new_moves = moves._reverse_moves(default_values_list, cancel=is_cancel_needed)

            if self.refund_method == 'modify':
                moves_vals_list = []
                for move in moves.with_context(include_business_fields=True):
                    moves_vals_list.append(
                        move.copy_data({'date': self.date if self.date_mode == 'custom' else move.date})[0])
                new_moves = self.env['account.move'].create(moves_vals_list)

            moves_to_redirect |= new_moves

        self.new_move_ids = moves_to_redirect

        # Create action.
        action = {
            'name': _('Reverse Moves'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
        }
        if len(moves_to_redirect) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': moves_to_redirect.id,
            })
        else:
            action.update({
                'view_mode': 'tree,form',
                'domain': [('id', 'in', moves_to_redirect.ids)],
            })
        return action


class ProductTemplateInh(models.Model):
    _inherit = 'product.template'

    x_css = fields.Html(string='CSS', sanitize=False, compute='_compute_css', store=False)

    def _compute_css(self):
        for application in self:
            if self.env.user.has_group('approval_so_po.group_contact_user'):
                application.x_css = '<style>.o_cp_action_menus {display: none !important;}.o_report_buttons {display: none !important;}</style>'
            else:
                application.x_css = False

    @api.constrains('name')
    def remove_duplication(self):
        if self.name:
            record = self.env['product.template'].search([('name', '=', self.name)])
            if len(record) > 1:
                raise UserError('Product Already Exists')

    # @api.model
    # def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    #     result = super(ProductTemplateInh, self).fields_view_get(
    #         view_id=view_id, view_type=view_type, toolbar=toolbar,
    #         submenu=submenu)
    #     if self.env.user.has_group('approval_so_po.group_product_remove_edit_user'):
    #         temp = etree.fromstring(result['arch'])
    #         temp.set('edit', '0')
    #         temp.set('create', '0')
    #         result['arch'] = etree.tostring(temp)
    #     return result

    def write(self, vals):
        res = super().write(vals)
        if 'available_qty' not in vals and self.env.user.has_group('approval_so_po.group_product_remove_edit_user'):
            raise UserError('You cannot edit this form.')
        return res


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
    is_return_order = fields.Boolean()

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
            if round(line.quantity_done, 2) <= round(line.product_uom_qty, 2):
                flag = True
            else:
                raise UserError('Done Quantity Cannot be greater than Demand')
        if flag:
            if self.state == 'assigned':
                if self.picking_type_id.code == 'outgoing':
                    check = False
                    for rec in self.move_line_ids_without_package:
                        if rec.qty_done == 0 and not rec.is_backorder:
                            check = True
                    if check:
                        raise UserError('Kindly Add Done Quantities Before Validate')
                    else:
                        # self.action_remove_done_qty()
                        # self.do_unreserve()
                        # self.action_assign()
                        # self.action_add_done_qty()
                        self.state = 'manager'
                else:
                    check = False
                    for rec in self.move_ids_without_package:
                        if rec.quantity_done == 0 and not rec.is_backorder:
                            check = True
                    if check:
                        raise UserError('Kindly Add Done Quantities Before Validate')
                    else:
                        self.state = 'manager'

    def action_manager_approve(self):
        flag = False
        for line in self.move_ids_without_package:
            if round(line.quantity_done, 2) <= round(line.product_uom_qty, 2):
                flag = True
            else:
                raise UserError('Done Quantity Cannot be greater than Demand')
        if flag:
            record = super(StockPickingInh, self).button_validate()
            backorder = self.env['stock.picking'].search([('backorder_id', '=', self.id)])
            if backorder:
                backorder.update({
                    'is_done_added': False,
                })
                for res in backorder.move_line_ids_without_package:
                    res.is_backorder = False
                for res in backorder.move_ids_without_package:
                    res.is_backorder = False

            # if self.picking_type_id.code == 'incoming':
            #     for rec_line in self.move_ids_without_package:
            #         rec_line.product_id.product_tmpl_id.incoming_quantity = rec_line.product_id.product_tmpl_id.incoming_quantity - rec_line.product_uom_qty
            #         total = 0
            #         quants = self.get_quant_lines()
            #         quants = self.env['stock.quant'].browse(quants)
            #         for q_line in quants:
            #             if q_line.product_tmpl_id.id == rec_line.product_tmpl_id.id:
            #                 total = total + q_line.available_quantity
            #         rec_line.product_id.product_tmpl_id.available_qty = rec_line.product_id.product_tmpl_id.available_qty + rec_line.quantity_done
            # if self.picking_type_id.code == 'outgoing':
            #     for res_line in self.move_ids_without_package:
            #         res_line.product_id.product_tmpl_id.available_qty = res_line.product_id.product_tmpl_id.available_qty - res_line.quantity_done
            for res_line in self.move_ids_without_package:
                total = 0
                quants = self.get_quant_lines()
                quants = self.env['stock.quant'].browse(quants)
                for q_line in quants:
                    if q_line.product_tmpl_id.id == res_line.product_id.product_tmpl_id.id:
                        total = total + q_line.available_quantity
                res_line.product_id.product_tmpl_id.available_qty = total
            return record

    # def get_quant_lines(self):
    #     domain_loc = self.env['product.product']._get_domain_locations()[0]
    #     quant_ids = [l['id'] for l in self.env['stock.quant'].search_read(domain_loc, ['id'])]
    #     return quant_ids

    def do_unreserve(self):
        rec = super(StockPickingInh, self).do_unreserve()
        for res_line in self.move_ids_without_package:
            total = 0
            quants = self.get_quant_lines()
            quants = self.env['stock.quant'].browse(quants)
            for q_line in quants:
                if q_line.product_tmpl_id.id == res_line.product_id.product_tmpl_id.id:
                    total = total + q_line.available_quantity
            res_line.product_id.product_tmpl_id.available_qty = total
        return

    def action_assign(self):
        record = super(StockPickingInh, self).action_assign()
        for res_line in self.move_line_ids_without_package:
            total = 0
            quants = self.get_quant_lines()
            quants = self.env['stock.quant'].browse(quants)
            for q_line in quants:
                if q_line.product_tmpl_id.id == res_line.product_id.product_tmpl_id.id:
                    total = total + q_line.available_quantity
            res_line.product_id.product_tmpl_id.available_qty = total

    def action_cancel(self):
        record = super(StockPickingInh, self).action_cancel()
        for res_line in self.move_ids_without_package:
            total = 0
            quants = self.get_quant_lines()
            quants = self.env['stock.quant'].browse(quants)
            for q_line in quants:
                if q_line.product_tmpl_id.id == res_line.product_id.product_tmpl_id.id:
                    total = total + q_line.available_quantity
            res_line.product_id.product_tmpl_id.available_qty = total

    def get_quant_lines(self):
        domain_loc = self.env['product.product']._get_domain_locations()[0]
        quant_ids = [l['id'] for l in self.env['stock.quant'].search_read(domain_loc, ['id'])]
        return quant_ids

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
                        raise UserError(
                            _("Could not reserve all requested products. Please use the \'Mark as Todo\' button to handle the reservation manually."))
            for move in picking.move_lines.filtered(lambda m: m.state not in ['done', 'cancel']):
                for move_line in move.move_line_ids:
                    move_line.qty_done = move_line.product_uom_qty

        pickings_to_validate = self.env.context.get('button_validate_picking_ids')
        if pickings_to_validate:
            pickings_to_validate = self.env['stock.picking'].browse(pickings_to_validate)
            pickings_to_validate = pickings_to_validate - pickings_not_to_do
            return pickings_to_validate.with_context(skip_immediate=True).action_manager_approve()
        return True
