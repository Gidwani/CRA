from collections import defaultdict

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero
from odoo.tools.float_utils import float_compare


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
    status_in_payment = fields.Selection(
        selection_add=[("manager", "manager")],
        ondelete={"manager": "cascade"},
    )

    def _check_vendor_refund_return_quantities(self):
        """Limit vendor refunds to quantities physically returned to the vendor."""
        for move in self.filtered(lambda record: record.move_type == 'in_refund'):
            refund_lines = move.invoice_line_ids.filtered(
                lambda line: (
                    line.display_type == 'product'
                    and line.product_id.type != 'service'
                    and line.purchase_line_id
                    and line.quantity > 0
                )
            )
            if not refund_lines:
                continue

            purchase_lines = refund_lines.purchase_line_id
            requested_by_purchase_line = defaultdict(float)
            returned_by_purchase_line = defaultdict(float)
            already_refunded_by_purchase_line = defaultdict(float)
            source_billed_by_purchase_line = defaultdict(float)
            source_refunded_by_purchase_line = defaultdict(float)

            for line in refund_lines:
                purchase_line = line.purchase_line_id
                purchase_uom = purchase_line.product_uom_id or line.product_id.uom_id
                invoice_uom = line.product_uom_id or line.product_id.uom_id
                requested_by_purchase_line[purchase_line.id] += invoice_uom._compute_quantity(
                    line.quantity,
                    purchase_uom,
                )

            source_bill = move.reversed_entry_id.filtered(lambda source: source.move_type == 'in_invoice')
            for line in source_bill.invoice_line_ids.filtered(
                lambda source_line: source_line.display_type == 'product' and source_line.purchase_line_id
            ):
                purchase_line = line.purchase_line_id
                purchase_uom = purchase_line.product_uom_id or line.product_id.uom_id
                invoice_uom = line.product_uom_id or line.product_id.uom_id
                source_billed_by_purchase_line[purchase_line.id] += invoice_uom._compute_quantity(
                    line.quantity,
                    purchase_uom,
                )

            returned_moves = purchase_lines.move_ids.filtered(
                lambda stock_move: (
                    stock_move.state == 'done'
                    and stock_move.location_dest_id.usage == 'supplier'
                    and stock_move.purchase_line_id
                )
            )
            for stock_move in returned_moves:
                purchase_line = stock_move.purchase_line_id
                purchase_uom = purchase_line.product_uom_id or stock_move.product_id.uom_id
                returned_by_purchase_line[purchase_line.id] += stock_move.product_uom._compute_quantity(
                    stock_move.quantity,
                    purchase_uom,
                )

            other_refund_domain = [
                ('move_id.move_type', '=', 'in_refund'),
                ('move_id.state', 'in', ('manager', 'posted')),
                ('purchase_line_id', 'in', purchase_lines.ids),
                ('display_type', '=', 'product'),
            ]
            current_move_id = move._origin.id
            if current_move_id:
                other_refund_domain.append(('move_id', '!=', current_move_id))
            other_refund_lines = self.env['account.move.line'].search(other_refund_domain)
            for line in other_refund_lines:
                purchase_line = line.purchase_line_id
                purchase_uom = purchase_line.product_uom_id or line.product_id.uom_id
                invoice_uom = line.product_uom_id or line.product_id.uom_id
                already_refunded_by_purchase_line[purchase_line.id] += invoice_uom._compute_quantity(
                    line.quantity,
                    purchase_uom,
                )
                if source_bill and line.move_id.reversed_entry_id == source_bill:
                    source_refunded_by_purchase_line[purchase_line.id] += invoice_uom._compute_quantity(
                        line.quantity,
                        purchase_uom,
                    )

            for purchase_line in purchase_lines:
                rounding = purchase_line.product_uom_id.rounding or purchase_line.product_id.uom_id.rounding
                returned_quantity = returned_by_purchase_line[purchase_line.id]
                already_refunded_quantity = already_refunded_by_purchase_line[purchase_line.id]
                requested_quantity = requested_by_purchase_line[purchase_line.id]
                remaining_quantity = max(returned_quantity - already_refunded_quantity, 0.0)
                if source_bill:
                    source_remaining_quantity = max(
                        source_billed_by_purchase_line[purchase_line.id]
                        - source_refunded_by_purchase_line[purchase_line.id],
                        0.0,
                    )
                    remaining_quantity = min(remaining_quantity, source_remaining_quantity)
                if float_compare(requested_quantity, remaining_quantity, precision_rounding=rounding) > 0:
                    raise UserError(_(
                        "The RBill quantity for %(product)s cannot exceed the quantity physically "
                        "returned to the vendor.\n\n"
                        "Returned quantity: %(returned)s %(uom)s\n"
                        "Already used on other RBills: %(refunded)s %(uom)s\n"
                        "Remaining quantity available: %(remaining)s %(uom)s\n"
                        "Requested RBill quantity: %(requested)s %(uom)s",
                        product=purchase_line.product_id.display_name,
                        returned=returned_quantity,
                        refunded=already_refunded_quantity,
                        remaining=remaining_quantity,
                        requested=requested_quantity,
                        uom=purchase_line.product_uom_id.name or purchase_line.product_id.uom_id.name,
                    ))

    def action_post(self):
        self._check_vendor_refund_return_quantities()
        return super().action_post()

    def action_manager_approve(self):
        self._check_vendor_refund_return_quantities()
        return super().action_manager_approve()

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
                # amount_tax += rec.l10n_ae_vat_amount
                amount_tax += rec.vat_amount
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
                all_pickings = self.invoice_line_ids.sale_line_ids.move_ids.picking_id.filtered(
                    lambda p: p.state == 'done').sorted('date_done')
                saleorder = self.env['sale.order'].search([("name", '=', r.invoice_origin)])
                already_linked = saleorder.invoice_ids.filtered(lambda i:i.id != self.id).mapped('do_link')
                new_picking = all_pickings.filtered(lambda i:i.name not in already_linked)
                r.do_link = ";".join(new_picking.mapped('name'))
                for k in r.invoice_line_ids:
                    for l in saleorder.picking_ids:
                        if r.invoice_origin == l.sale_id.name:
                            for j in l.move_line_ids:
                                if j.picking_id.invoice_link != True:
                                    if j.product_id == k.product_id:
                                        if j.quantity == k.quantity:
                                            # r.do_link = l.name
                                            j.picking_id.invoice_link = True

    def get_payment_term_id(self):
        order = self.env['sale.order'].search([('name', '=', self.invoice_origin)])
        return order.payment_term_id.name

    def get_client_order_ref(self):
        order = self.env['sale.order'].search([('name', '=', self.invoice_origin)])
        return order.client_order_ref

    def get_do_no(self):
        pickings = self.env['stock.picking'].search([('name', '=', self.do_link)], limit=1)
        if pickings:
            name = pickings.name
        else:
            name = self.do_link
        return name

    def get_reversed_invoice(self):
        if self.reversed_entry_id:
            name = self.reversed_entry_id.name.replace('/', '-')
            date = self.reversed_entry_id.invoice_date
            return {
                'name': name,
                'date': date,
            }
        else:
            order = self.env['sale.order'].search([('name', '=', self.invoice_origin)], limit=1)
            if order and order.invoice_ids and order.invoice_ids.filtered(lambda i:i.move_type == 'out_invoice'):
                inv = order.invoice_ids.filtered(lambda i:i.move_type == 'out_invoice')
                if inv:
                    return {
                        'name': inv[-1].name,
                        'date': inv[-1].invoice_date,
                    }
            return {
                    'name': "",
                    'date': ""
                }

    @api.depends('invoice_line_ids', 'perc_discount', 'invoice_line_ids.tax_ids', 'invoice_line_ids.subtotal')
    def compute_taxes(self):
        for res in self:
            amount_tax = 0.0
            for rec in res.invoice_line_ids:
                amount_tax += rec.l10n_gcc_invoice_tax_amount
                # amount_tax += rec.vat_amount
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

    @api.onchange('tax_ids', 'price_unit')
    def _onchange_sale_taxes(self):
        for line in self:
            if line.sale_line_ids or line.purchase_order_id:
                raise UserError('You cannot change invoice/bill values.')

    @api.onchange('quantity')
    def _onchange_quantity(self):
        for line in self:
            if not (line.sale_line_ids or line.purchase_order_id):
                continue
            if line.move_id.move_type == 'in_refund':
                line.move_id._check_vendor_refund_return_quantities()
            else:
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
                    if tax.id in [1,48]:
                        amount = amount + tax.amount
                else:
                    if tax.id in [19, 65]:
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
