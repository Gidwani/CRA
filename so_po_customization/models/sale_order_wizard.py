from datetime import datetime

from odoo import models, fields, api


class SaleOrderWizard(models.TransientModel):
    _name = 'sale.order.wizard'

    sale_id = fields.Many2many('sale.order')
    product_lines = fields.One2many('sale.order.wizard.line', 'sale_id')

    @api.onchange('sale_id')
    def onchange_sale_id(self):
        # for rec in self.product_lines:
        #     rec.unlink()
        vals_list = []
        for order in self.sale_id:
            for line in order.order_line:
                val = {
                    'sale_id': self.id,
                    'sale_order': order.name,
                    'product_id': line.product_id.id,
                }
                vals_list.append(val)
        move = self.env['sale.order.wizard.line'].create(vals_list)

    def action_get_products(self):
        model = self.env.context.get('active_model')
        rec = self.env[model].browse(self.env.context.get('active_id'))
        vals_list = []
        for line in self.product_lines:
            if line.is_selected:
                val = {
                    'order_id': rec.id,
                    'product_id': line.product_id.id,
                    'name': line.product_id.name,
                    'date_planned': rec.date_order,
                    'product_qty': 1,
                    'price_unit': line.product_id.list_price,
                }
                vals_list.append(val)
        move = self.env['purchase.order.line'].create(vals_list)


class SaleOrderLineWizard(models.TransientModel):
    _name = 'sale.order.wizard.line'

    sale_id = fields.Many2one('sale.order.wizard')
    is_selected = fields.Boolean()
    sale_order = fields.Char('Sale Order')
    product_id = fields.Many2one('product.product')
