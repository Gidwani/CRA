# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools.misc import formatLang, format_date, get_lang


class AccountFollowupInh(models.AbstractModel):
    _inherit = 'account.followup.report'

    def _get_lines(self, options, line_id=None):
        """
        Override
        Compute and return the lines of the columns of the follow-ups report.
        """
        # Get date format for the lang
        partner = options.get('partner_id') and self.env['res.partner'].browse(options['partner_id']) or False
        if not partner:
            return []

        lang_code = partner.lang if self._context.get('print_mode') else self.env.user.lang or get_lang(self.env).code
        lines = []
        res = {}
        today = fields.Date.today()
        line_num = 0
        for l in partner.unreconciled_aml_ids.filtered(lambda l: l.company_id == self.env.company):
            if l.company_id == self.env.company:
                if self.env.context.get('print_mode') and l.blocked:
                    continue
                currency = l.currency_id or l.company_id.currency_id
                if currency not in res:
                    res[currency] = []
                res[currency].append(l)
        for currency, aml_recs in res.items():
            total = 0
            total_issued = 0
            for aml in aml_recs:
                amount = aml.amount_residual_currency if aml.currency_id else aml.amount_residual
                date_due = format_date(self.env, aml.date_maturity or aml.date, lang_code=lang_code)
                total += not aml.blocked and amount or 0
                is_overdue = today > aml.date_maturity if aml.date_maturity else today > aml.date
                is_payment = aml.payment_id
                if is_overdue or is_payment:
                    total_issued += not aml.blocked and amount or 0
                if is_overdue:
                    date_due = {'name': date_due, 'class': 'color-red date', 'style': 'white-space:nowrap;text-align:center;color: red;'}
                if is_payment:
                    date_due = ''
                move_line_name = self._format_aml_name(aml.name, aml.move_id.ref, aml.move_id.name)
                if self.env.context.get('print_mode'):
                    move_line_name = {'name': move_line_name, 'style': 'text-align:right; white-space:normal;'}
                amount = formatLang(self.env, amount, currency_obj=currency)
                line_num += 1
                expected_pay_date = format_date(self.env, aml.expected_pay_date, lang_code=lang_code) if aml.expected_pay_date else ''
                invoice_origin = aml.move_id.invoice_origin or ''
                if len(invoice_origin) > 43:
                    invoice_origin = invoice_origin[:40] + '...'
                columns = [
                    format_date(self.env, aml.date, lang_code=lang_code),
                    date_due,
                    invoice_origin,
                    move_line_name,
                    (expected_pay_date and expected_pay_date + ' ') + (aml.internal_note or ''),
                    {'name': '', 'blocked': aml.blocked},
                    amount,
                ]
                if self.env.context.get('print_mode'):
                    columns = columns[:4] + columns[6:]
                lines.append({
                    'id': aml.id,
                    'account_move': aml.move_id,
                    'name': aml.move_id.name,
                    'caret_options': 'followup',
                    'move_id': aml.move_id.id,
                    'type': is_payment and 'payment' or 'unreconciled_aml',
                    'unfoldable': False,
                    'columns': [type(v) == dict and v or {'name': v} for v in columns],
                })
            total_due = formatLang(self.env, total, currency_obj=currency)
            line_num += 1
            lines.append({
                'id': line_num,
                'name': '',
                'class': 'total',
                'style': 'border-top-style: double',
                'unfoldable': False,
                'level': 3,
                'columns': [{'name': v} for v in [''] * (3 if self.env.context.get('print_mode') else 5) + [total >= 0 and _('Total Due') or '', total_due]],
            })
            if total_issued > 0:
                total_issued = formatLang(self.env, total_issued, currency_obj=currency)
                line_num += 1
                lines.append({
                    'id': line_num,
                    'name': '',
                    'class': 'total',
                    'unfoldable': False,
                    'level': 3,
                    'columns': [{'name': v} for v in [''] * (3 if self.env.context.get('print_mode') else 5) + [_('Total Overdue'), total_issued]],
                })
            # Add an empty line after the total to make a space between two currencies
            line_num += 1
            lines.append({
                'id': line_num,
                'name': '',
                'class': '',
                'style': 'border-bottom-style: none',
                'unfoldable': False,
                'level': 0,
                'columns': [{} for col in columns],
            })
        # Remove the last empty line
        print(lines)
        if lines:
            lines.pop()
        new_lines = []
        sorted_lines = []
        i = -3
        if lines:
            for rec in range(0, len(lines)-2):
                new_lines.append(lines[i])
                i = i -1
            print(len(lines))
            print("--------------------------")

            sorted_lines = sorted(new_lines, key=lambda i: i['id'])

            sorted_lines.append(lines[-2])
            sorted_lines.append(lines[-1])
        # print(new_lines)
        return sorted_lines


class StockMoveInh(models.Model):
    _inherit = 'stock.move'

    is_backorder = fields.Boolean()


class StockMoveLineInh(models.Model):
    _inherit = 'stock.move.line'

    remarks = fields.Char("Remarks", compute='_compute_remarks')
    number = fields.Integer(compute='_compute_get_number', store=True)
    so_no = fields.Integer(compute='compute_so_sr_no')
    is_backorder = fields.Boolean()

    def compute_so_sr_no(self):
        for rec in self:
            if not rec.picking_id.backorder_id:
                if rec.picking_id.sale_id:
                    for line in rec.picking_id.sale_id.order_line:
                        if rec.move_id.sale_line_id.id == line.id:
                            rec.so_no = line.number
                if rec.picking_id.purchase_id:
                    for line in rec.picking_id.purchase_id.order_line:
                        if rec.move_id.purchase_line_id.id == line.id:
                            rec.so_no = line.number
            else:
                if rec.picking_id.backorder_id.sale_id:
                    for line in rec.picking_id.backorder_id.sale_id.order_line:
                        if rec.move_id.sale_line_id.id == line.id:
                            rec.so_no = line.number
                if rec.picking_id.backorder_id.purchase_id:
                    for line in rec.picking_id.backorder_id.purchase_id.order_line:
                        if rec.move_id.purchase_line_id.id == line.id:
                            rec.so_no = line.number
            if rec.picking_id.sale_id:
                for line in rec.picking_id.sale_id.order_line:
                    if line.product_id.id == rec.product_id.id and line.number == rec.number:
                        rec.so_no = line.number

            else:
                rec.so_no = 0

    @api.depends('picking_id')
    def _compute_get_number(self):
        for order in self.mapped('picking_id'):
            number = 1
            for line in order.move_line_ids_without_package:
                line.number = number
                number += 1

    def _compute_remarks(self):
        for rec in self:
            rem = ''
            if rec.picking_id.sale_id:
                for line in rec.picking_id.sale_id.order_line:
                    if rec.move_id.sale_line_id.id == line.id:
                        rem = line.remarks
            if rec.picking_id.purchase_id:
                for line in rec.picking_id.purchase_id.order_line:
                    if rec.product_id.id == line.product_id.id:
                        rem = line.remarks
            if rec.picking_id.backorder_id.sale_id:
                for line in rec.picking_id.backorder_id.sale_id.order_line:
                    if rec.move_id.sale_line_id.id == line.id:
                        rem = line.remarks
            rec.remarks = rem


class StockPickingInh(models.Model):
    _inherit = 'stock.picking'

    is_done_added = fields.Boolean()
    is_delivery = fields.Boolean(compute='compute_is_delivery')

    def compute_is_delivery(self):
        if self.picking_type_id.code == 'outgoing':
            self.is_delivery = True
        else:
            self.is_delivery = False

    # def action_add_done_qty(self):
    #     if self.move_ids_without_package:
    #         for line in self.move_ids_without_package:
    #             # line.quantity_done = line.product_uom_qty
    #             if line.move_line_ids:
    #                 for rec in line.move_line_ids:
    #                     rec.qty_done = rec.reserved_uom_qty
    #             else:
    #                 line.quantity_done = line.forecast_availability
    #         self.is_done_added = True
    #
    # def action_remove_done_qty(self):
    #     if self.move_ids_without_package:
    #         for line in self.move_ids_without_package:
    #             if line.move_line_ids:
    #                 for rec in line.move_line_ids:
    #                     rec.qty_done = 0
    #             else:
    #                 line.quantity_done = 0
    #         self.is_done_added = False

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        result = super(StockPickingInh, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu)
        if view_type == 'form':
            print(result['toolbar']['print'])
            for repo in result['toolbar']['print']:
                if repo['name'] == 'Delivery Slip':
                    result['toolbar']['print'].remove(repo)
            result['toolbar']['print'].reverse()
        return result
