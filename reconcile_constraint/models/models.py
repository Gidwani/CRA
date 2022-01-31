# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AccountRegisterInh(models.TransientModel):
    _inherit = 'account.payment.register'

    def _create_payments(self):
        self.ensure_one()
        batches = self._get_batches()
        edit_mode = self.can_edit_wizard and (len(batches[0]['lines']) == 1 or self.group_payment)

        to_reconcile = []
        if edit_mode:
            payment_vals = self._create_payment_vals_from_wizard()
            payment_vals_list = [payment_vals]
            to_reconcile.append(batches[0]['lines'])
        else:
            # Don't group payments: Create one batch per move.
            if not self.group_payment:
                new_batches = []
                for batch_result in batches:
                    for line in batch_result['lines']:
                        new_batches.append({
                            **batch_result,
                            'lines': line,
                        })
                batches = new_batches

            payment_vals_list = []
            for batch_result in batches:
                payment_vals_list.append(self._create_payment_vals_from_batch(batch_result))
                to_reconcile.append(batch_result['lines'])

        payments = self.env['account.payment'].create(payment_vals_list)

        # If payments are made using a currency different than the source one, ensure the balance match exactly in
        # order to fully paid the source journal items.
        # For example, suppose a new currency B having a rate 100:1 regarding the company currency A.
        # If you try to pay 12.15A using 0.12B, the computed balance will be 12.00A for the payment instead of 12.15A.
        if edit_mode:
            for payment, lines in zip(payments, to_reconcile):
                # Batches are made using the same currency so making 'lines.currency_id' is ok.
                if payment.currency_id != lines.currency_id:
                    liquidity_lines, counterpart_lines, writeoff_lines = payment._seek_for_lines()
                    source_balance = abs(sum(lines.mapped('amount_residual')))
                    payment_rate = liquidity_lines[0].amount_currency / liquidity_lines[0].balance
                    source_balance_converted = abs(source_balance) * payment_rate

                    # Translate the balance into the payment currency is order to be able to compare them.
                    # In case in both have the same value (12.15 * 0.01 ~= 0.12 in our example), it means the user
                    # attempt to fully paid the source lines and then, we need to manually fix them to get a perfect
                    # match.
                    payment_balance = abs(sum(counterpart_lines.mapped('balance')))
                    payment_amount_currency = abs(sum(counterpart_lines.mapped('amount_currency')))
                    if not payment.currency_id.is_zero(source_balance_converted - payment_amount_currency):
                        continue

                    delta_balance = source_balance - payment_balance

                    # Balance are already the same.
                    if self.company_currency_id.is_zero(delta_balance):
                        continue

                    # Fix the balance but make sure to peek the liquidity and counterpart lines first.
                    debit_lines = (liquidity_lines + counterpart_lines).filtered('debit')
                    credit_lines = (liquidity_lines + counterpart_lines).filtered('credit')

                    payment.move_id.write({'line_ids': [
                        (1, debit_lines[0].id, {'debit': debit_lines[0].debit + delta_balance}),
                        (1, credit_lines[0].id, {'credit': credit_lines[0].credit + delta_balance}),
                    ]})

        payments.action_post()

        # domain = [('account_internal_type', 'in', ('receivable', 'payable')), ('reconciled', '=', False)]
        # for payment, lines in zip(payments, to_reconcile):
        #
        #     # When using the payment tokens, the payment could not be posted at this point (e.g. the transaction failed)
        #     # and then, we can't perform the reconciliation.
        #     if payment.state != 'posted':
        #         continue
        #
        #     payment_lines = payment.line_ids.filtered_domain(domain)
        #     for account in payment_lines.account_id:
        #         (payment_lines + lines)\
        #             .filtered_domain([('account_id', '=', account.id), ('reconciled', '=', False)])\
        #             .reconcile()

        return payments
#
#
# class AccountMoveInh(models.Model):
#     _inherit = 'account.move.line'
#
#     def reconcile(self):
#         ''' Reconcile the current move lines all together.
#         :return: A dictionary representing a summary of what has been done during the reconciliation:
#                 * partials:             A recorset of all account.partial.reconcile created during the reconciliation.
#                 * full_reconcile:       An account.full.reconcile record created when there is nothing left to reconcile
#                                         in the involved lines.
#                 * tax_cash_basis_moves: An account.move recordset representing the tax cash basis journal entries.
#         '''
#         results = {}
#
#         if not self:
#             return results
#
#         # List unpaid invoices
#         not_paid_invoices = self.move_id.filtered(
#             lambda move: move.is_invoice(include_receipts=True) and move.payment_state not in ('paid', 'in_payment')
#         )
#
#         # ==== Check the lines can be reconciled together ====
#         company = None
#         account = None
#         for line in self:
#             if line.reconciled:
#                 raise UserError(_("You are trying to reconcile some entries that are already reconciled."))
#             if not line.account_id.reconcile and line.account_id.internal_type != 'liquidity':
#                 raise UserError(_("Account %s does not allow reconciliation. First change the configuration of this account to allow it.")
#                                 % line.account_id.display_name)
#             if line.move_id.state != 'posted':
#                 raise UserError(_('You can only reconcile posted entries.'))
#             if company is None:
#                 company = line.company_id
#             elif line.company_id != company:
#                 raise UserError(_("Entries doesn't belong to the same company: %s != %s")
#                                 % (company.display_name, line.company_id.display_name))
#             if account is None:
#                 account = line.account_id
#             elif line.account_id != account:
#                 raise UserError(_("Entries are not from the same account: %s != %s")
#                                 % (account.display_name, line.account_id.display_name))
#
#         sorted_lines = self.sorted(key=lambda line: (line.date_maturity or line.date, line.currency_id))
#
#         # ==== Collect all involved lines through the existing reconciliation ====
#
#         involved_lines = sorted_lines
#         involved_partials = self.env['account.partial.reconcile']
#         current_lines = involved_lines
#         current_partials = involved_partials
#         while current_lines:
#             current_partials = (current_lines.matched_debit_ids + current_lines.matched_credit_ids) - current_partials
#             involved_partials += current_partials
#             current_lines = (current_partials.debit_move_id + current_partials.credit_move_id) - current_lines
#             involved_lines += current_lines
#
#         # ==== Create partials ====
#
#         partials = self.env['account.partial.reconcile'].create(sorted_lines._prepare_reconciliation_partials())
#
#         # Track newly created partials.
#         results['partials'] = partials
#         involved_partials += partials
#
#         # ==== Create entries for cash basis taxes ====
#
#         is_cash_basis_needed = account.user_type_id.type in ('receivable', 'payable')
#         if is_cash_basis_needed and not self._context.get('move_reverse_cancel'):
#             tax_cash_basis_moves = partials._create_tax_cash_basis_moves()
#             results['tax_cash_basis_moves'] = tax_cash_basis_moves
#
#         # ==== Check if a full reconcile is needed ====
#
#         if involved_lines[0].currency_id and all(line.currency_id == involved_lines[0].currency_id for line in involved_lines):
#             is_full_needed = all(line.currency_id.is_zero(line.amount_residual_currency) for line in involved_lines)
#         else:
#             is_full_needed = all(line.company_currency_id.is_zero(line.amount_residual) for line in involved_lines)
#
#         if is_full_needed:
#
#             # ==== Create the exchange difference move ====
#
#             if self._context.get('no_exchange_difference'):
#                 exchange_move = None
#             else:
#                 exchange_move = involved_lines._create_exchange_difference_move()
#                 if exchange_move:
#                     exchange_move_lines = exchange_move.line_ids.filtered(lambda line: line.account_id == account)
#
#                     # Track newly created lines.
#                     involved_lines += exchange_move_lines
#
#                     # Track newly created partials.
#                     exchange_diff_partials = exchange_move_lines.matched_debit_ids \
#                                              + exchange_move_lines.matched_credit_ids
#                     involved_partials += exchange_diff_partials
#                     results['partials'] += exchange_diff_partials
#
#                     exchange_move._post(soft=False)
#
#             # ==== Create the full reconcile ====
#
#             results['full_reconcile'] = self.env['account.full.reconcile'].create({
#                 'exchange_move_id': exchange_move and exchange_move.id,
#                 'partial_reconcile_ids': [(6, 0, involved_partials.ids)],
#                 'reconciled_line_ids': [(6, 0, involved_lines.ids)],
#             })
#
#         # Trigger action for paid invoices
#         not_paid_invoices\
#             .filtered(lambda move: move.payment_state in ('paid', 'in_payment'))\
#             .action_invoice_paid()
#
#         return results
