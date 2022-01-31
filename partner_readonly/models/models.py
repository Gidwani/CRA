# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare


class StockMoveInh(models.Model):
    _inherit = 'stock.move'

    def _quantity_done_set(self):
        quantity_done = self[0].quantity_done  # any call to create will invalidate `move.quantity_done`
        for move in self:
            move_lines = move._get_move_lines()
            if not move_lines:
                if quantity_done:
                    # do not impact reservation here
                    move_line = self.env['stock.move.line'].create(
                        dict(move._prepare_move_line_vals(), qty_done=quantity_done))
                    move.write({'move_line_ids': [(4, move_line.id)]})
            elif len(move_lines) == 1:
                move_lines[0].qty_done = quantity_done
            # else:
            #     # Bypass the error if we're trying to write the same value.
            #     ml_quantity_done = 0
            #     for move_line in move_lines:
            #         ml_quantity_done += move_line.product_uom_id._compute_quantity(move_line.qty_done, move.product_uom,
            #                                                                        round=False)
            #     if float_compare(quantity_done, ml_quantity_done, precision_rounding=move.product_uom.rounding) != 0:
            #         raise UserError(
            #             _("Cannot set the done quantity from this stock move, work directly with the move lines."))


class AccountMoveInh(models.Model):
    _inherit = 'account.move'

    is_created_so_po = fields.Boolean()


class SaleOrderInh(models.Model):
    _inherit = 'sale.order'

    def _prepare_invoice(self, ):
        invoice_vals = super(SaleOrderInh, self)._prepare_invoice()
        invoice_vals.update({
            'is_created_so_po': True,
        })
        return invoice_vals


class PurchaseOrderInh(models.Model):
    _inherit = 'purchase.order'

    def _prepare_invoice(self, ):
        invoice_vals = super(PurchaseOrderInh, self)._prepare_invoice()
        invoice_vals.update({
            'is_created_so_po': True,
        })
        return invoice_vals
