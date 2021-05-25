from odoo import models, fields, api


class AccountMoveInh(models.Model):
    _inherit = 'account.move.line'

    remarks = fields.Char("Remarks", compute='_compute_remarks')
    number = fields.Integer(compute='_compute_get_number', store=True)

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
            purchases = self.env['purchase.order'].search([('name', '=', rec.move_id.invoice_origin)])
            sales = self.env['sale.order'].search([('name', '=', rec.move_id.invoice_origin)])
            if purchases:
                for purchase in purchases:
                    for line in purchase.order_line:
                        if rec.product_id.id == line.product_id.id:
                            remark = line.remarks
            if sales:
                for sale in sales:
                    for line in sale.order_line:
                        if rec.product_id.id == line.product_id.id:
                            remark = line.remarks
            rec.remarks = remark
