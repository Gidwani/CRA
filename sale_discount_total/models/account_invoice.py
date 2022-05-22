
from odoo import api, fields, models ,_
from odoo.exceptions import UserError


class AccountInvoice(models.Model):
    _inherit = "account.move"

    @api.depends(
        'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual',
        'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual_currency',
        'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual',
        'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual_currency',
        'line_ids.debit',
        'line_ids.credit',
        'line_ids.currency_id',
        'line_ids.amount_currency',
        'line_ids.amount_residual',
        'line_ids.amount_residual_currency',
        'line_ids.payment_id.state',
        'line_ids.full_reconcile_id')
    def _compute_amount(self):
        for move in self:
            if move.payment_state == 'invoicing_legacy':
                # invoicing_legacy state is set via SQL when setting setting field
                # invoicing_switch_threshold (defined in account_accountant).
                # The only way of going out of this state is through this setting,
                # so we don't recompute it here.
                move.payment_state = move.payment_state
                continue

            total_untaxed = 0.0
            total_untaxed_currency = 0.0
            total_tax = 0.0
            total_tax_currency = 0.0
            total_to_pay = 0.0
            total_residual = 0.0
            total_residual_currency = 0.0
            total = 0.0
            total_currency = 0.0
            currencies = set()

            for line in move.line_ids:
                if line.currency_id:
                    currencies.add(line.currency_id)
                if move.is_invoice(include_receipts=True):
                    # === Invoices ===

                    if not line.exclude_from_invoice_tab:
                        # Untaxed amount.
                        total_untaxed += line.balance
                        total_untaxed_currency += line.amount_currency
                        total += line.balance
                        total_currency += line.amount_currency
                    elif line.tax_line_id:
                        # Tax amount.
                        total_tax += line.balance
                        total_tax_currency += line.amount_currency
                        total += line.balance
                        total_currency += line.amount_currency
                    elif line.account_id.user_type_id.type in ('receivable', 'payable'):
                        # Residual amount.
                        total_to_pay += line.balance
                        total_residual += line.amount_residual
                        total_residual_currency += line.amount_residual_currency
                else:
                    # === Miscellaneous journal entry ===
                    if line.debit:
                        total += line.balance
                        total_currency += line.amount_currency

            if move.move_type == 'entry' or move.is_outbound():
                sign = 1
            else:
                sign = -1
            if move.discount_type == 'percent':
                move.amount_discount = sum \
                    ((line.quantity * line.price_unit * line.discount) / 100 for line in move.invoice_line_ids)
            else:
                move.amount_discount = move.discount_rate
            move.amount_untaxed = sign * (total_untaxed_currency if len(currencies) == 1 else total_untaxed)
            move.amount_tax = sign * (total_tax_currency if len(currencies) == 1 else total_tax)
            move.amount_total = sign * (total_currency if len(currencies) == 1 else total)
            move.amount_residual = -sign * (total_residual_currency if len(currencies) == 1 else total_residual)
            move.amount_untaxed_signed = -total_untaxed
            move.amount_tax_signed = -total_tax
            move.amount_total_signed = abs(total) if move.move_type == 'entry' else -total
            move.amount_residual_signed = total_residual

            currency = len(currencies) == 1 and currencies.pop() or move.company_id.currency_id

            # Compute 'payment_state'.
            new_pmt_state = 'not_paid' if move.move_type != 'entry' else False

            if move.is_invoice(include_receipts=True) and move.state == 'posted':

                if currency.is_zero(move.amount_residual):
                    if all(payment.is_matched for payment in move._get_reconciled_payments()):
                        new_pmt_state = 'paid'
                    else:
                        new_pmt_state = move._get_invoice_in_payment_state()
                elif currency.compare_amounts(total_to_pay, total_residual) != 0:
                    new_pmt_state = 'partial'

            if new_pmt_state == 'paid' and move.move_type in ('in_invoice', 'out_invoice', 'entry'):
                reverse_type = move.move_type == 'in_invoice' and 'in_refund' or move.move_type == 'out_invoice' and 'out_refund' or 'entry'
                reverse_moves = self.env['account.move'].search(
                    [('reversed_entry_id', '=', move.id), ('state', '=', 'posted'), ('move_type', '=', reverse_type)])

                # We only set 'reversed' state in cas of 1 to 1 full reconciliation with a reverse entry; otherwise, we use the regular 'paid' state
                reverse_moves_full_recs = reverse_moves.mapped('line_ids.full_reconcile_id')
                if reverse_moves_full_recs.mapped('reconciled_line_ids.move_id').filtered(lambda x: x not in (
                        reverse_moves + reverse_moves_full_recs.mapped('exchange_move_id'))) == move:
                    new_pmt_state = 'reversed'

            move.payment_state = new_pmt_state

    discount_type = fields.Selection([('percent', 'Percentage'), ('amount', 'Amount')], string='Discount Type',
                                     readonly=True, states={'draft': [('readonly', False)]}, default='percent')
    discount_rate = fields.Float('Discount Amount', digits=(16, 2), readonly=True,
                                 states={'draft': [('readonly', False)]})
    amount_discount = fields.Monetary(string='Discount', store=True, readonly=True, compute='_compute_amount',
                                      track_visibility='always')

    @api.onchange('discount_type', 'discount_rate', 'invoice_line_ids')
    def supply_rate(self):
        for inv in self:
            if inv.discount_type == 'percent':
                for line in inv.line_ids:
                    line.discount = inv.discount_rate
                    line._onchange_price_subtotal()
            else:
                total = discount = 0.0
                for line in inv.invoice_line_ids:
                    total += (line.quantity * line.price_unit)
                if inv.discount_rate != 0:
                    discount = (inv.discount_rate / total) * 100
                else:
                    discount = inv.discount_rate
                for line in inv.line_ids:
                    line.discount = discount
                    line._onchange_price_subtotal()

            inv._compute_invoice_taxes_by_group()

    def button_dummy(self):
        self.supply_rate()
        return True

    def action_manager_approve(self):
        for move in self:
            if move.move_type == 'in_invoice':
                sale = \
                    (self.env['sale.order'].browse(self._context.get('active_id')) if move.discount_rate == 0 else move)
                purchase_tax_acc = move.line_ids.mapped(
                    'purchase_line_id.taxes_id.tax_group_id.property_tax_receivable_account_id')
                # if move and move.move_type == 'out_invoice' and not move.line_ids.filtered(
                #         lambda line: line.name == ('Discount Amount')):
                #     discount_account_id = int(self.env['ir.config_parameter'].sudo().get_param('sales_discount_account_id'))
                #     if move.discount_rate > 0:
                #         if not discount_account_id:
                #             raise UserError(_('Please select sale/purchase discount account first in accounting settings.'))
                #         else:
                #             ml = {'account_id': discount_account_id,
                #                   'name': 'Discount Amount',
                #                   'partner_id': move.partner_id.id,
                #                   'move_id': move.id,
                #                   'exclude_from_invoice_tab': True,
                #                   }
                #             self.write({'invoice_line_ids': [(0, 0, ml)]})
                #     elif sale.discount_rate > 0:
                #         if not discount_account_id:
                #             raise UserError(_('Please select sale/purchase discount account first in accounting settings.'))
                #         else:
                #             ml = {'account_id': discount_account_id,
                #                   'name': 'Discount Amount',
                #                   'partner_id': move.partner_id.id,
                #                   'move_id': move.id,
                #                   'exclude_from_invoice_tab': True,
                #                   }
                #             self.write({'invoice_line_ids': [(0, 0, ml)]})
                if move and move.move_type == 'in_invoice' and not move.line_ids.filtered(
                        lambda line: line.name == ('Discount Amount')):
                    discount_account_id = int(
                        self.env['ir.config_parameter'].sudo().get_param('purchase_discount_account_id'))
                    if move.discount_rate > 0:
                        if not discount_account_id:
                            raise UserError(_('Please select purchase discount account first in accounting settings.'))
                        else:
                            ml = {'account_id': discount_account_id,
                                  'name': 'Discount Amount',
                                  'partner_id': move.partner_id.id,
                                  'move_id': move.id,
                                  'exclude_from_invoice_tab': True,
                                  }
                            self.write({'invoice_line_ids': [(0, 0, ml)]})
                to_write = {
                    'line_ids': []
                }
                if move.move_type == 'in_invoice':
                    net = move.total_amount_net
                    print(net)
                    if move.discount_rate > 0:
                        for line in move.line_ids.filtered(
                                lambda line: line.name == ('Discount Amount')):
                            to_write['line_ids'].append((1, line.id, {'credit': move.perc_discount}))
                        for line in move.line_ids.filtered(
                                lambda line: line.account_id.user_type_id.type in ('receivable', 'payable')):
                            to_write['line_ids'].append((1, line.id, {'credit': net}))
                        tot = 0
                        for line in move.line_ids.filtered(
                                lambda line, acc = purchase_tax_acc: line.account_id.id == acc.id):
                            for rec in move.line_ids.mapped('purchase_line_id'):
                                # discounted_total = rec.subtotal - (rec.subtotal * (move.perc_discount / 100))
                                discounted_total = (rec.price_unit*rec.qty_received)  - ((rec.price_unit*rec.qty_received) * (move.discount_rate / 100))
                                print(discounted_total)
                                dt_amount = discounted_total * (line.tax_line_id.amount / 100)
                                # print(dt_amount)
                                # print(line.tax_line_id.amount)
                                tot = tot + dt_amount
                        print(tot)
                        if tot > 0:
                            # print(move.net_tax)
                            to_write['line_ids'].append((1, line.id, {'debit': tot}))
                        print(to_write)
                # elif move.move_type == 'out_invoice':
                #     if move.discount_rate > 0:
                #         for line in move.line_ids.filtered(
                #                 lambda line: line.name == ('Discount Amount')):
                #             to_write['line_ids'].append((1, line.id, {'debit': move.discount}))
                #         for line in move.line_ids.filtered(
                #                 lambda line: line.account_id.user_type_id.type in ('receivable', 'payable')):
                #             to_write['line_ids'].append((1, line.id, {'debit': move.net_total}))
                move.write(to_write)
        rec = super(AccountInvoice, self).action_manager_approve()
        return rec


class AccountInvoiceLine(models.Model):
    _inherit = "account.move.line"

    discount = fields.Float(string='Discount (%)', digits=(16, 20), default=0.0)
