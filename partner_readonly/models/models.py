# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockQuantIh(models.Model):
    _inherit = "stock.quant"

    def write(self, vals):
        record = super(StockQuantIh, self).write(vals)
        self.cal_incoming_quantity()
        return record

    def cal_incoming_quantity(self):
        for res_line in self:
            total = 0
            quants = self.get_quant_lines()
            quants = self.env['stock.quant'].browse(quants)
            for q_line in quants:
                if q_line.product_tmpl_id.id == res_line.product_tmpl_id.id:
                    total = total + q_line.available_quantity
            res_line.product_tmpl_id.available_qty = total

    def get_quant_lines(self):
        domain_loc = self.env['product.product']._get_domain_locations()[0]
        quant_ids = [l['id'] for l in self.env['stock.quant'].search_read(domain_loc, ['id'])]
        return quant_ids

# class StockInventoryIh(models.Model):
#     _inherit = "stock.inventory"
#
#     def post_inventory(self):
#         res = super(StockInventoryIh, self).post_inventory()
#         self.cal_incoming_quantity()
#         return res
#
#     def cal_incoming_quantity(self):
#         for res_line in self.product_ids:
#             total = 0
#             quants = self.get_quant_lines()
#             quants = self.env['stock.quant'].browse(quants)
#             for q_line in quants:
#                 if q_line.product_tmpl_id.id == res_line.product_tmpl_id.id:
#                     total = total + q_line.available_quantity
#             res_line.product_tmpl_id.available_qty = total
#
#     def get_quant_lines(self):
#         domain_loc = self.env['product.product']._get_domain_locations()[0]
#         quant_ids = [l['id'] for l in self.env['stock.quant'].search_read(domain_loc, ['id'])]
#         return quant_ids


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
