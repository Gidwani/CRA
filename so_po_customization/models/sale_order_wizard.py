
from odoo import models, fields, api


class SaleOrderWizard(models.TransientModel):
    _name = 'sale.order.wizard'

    sale_id = fields.Many2many('sale.order')
    product_lines = fields.One2many('sale.order.wizard.line', 'sale_id')

    @api.onchange('sale_id')
    def onchange_sale_id(self):
        for res in self:
            val_list = []
            my_list = []
            for rec in res.product_lines:
                my_list.append(rec.sale_order)

            for order in res.sale_id:
                if order.name not in my_list:
                    for line in order._origin.order_line:
                        print(line.number)
                        val = {
                            'sale_id': res.id,
                            'sale_order': order.name,
                            'sr_no': line.number,
                            'qty': line.product_uom_qty,
                            'product_id': line.product_id.id,
                        }
                        val_list.append(val)
            move = self.env['sale.order.wizard.line'].create(val_list)

    def action_get_products(self):
        model = self.env.context.get('active_model')
        rec = self.env[model].browse(self.env.context.get('active_id'))
        val_list = []
        for line in self.product_lines:
            if line.is_selected:
                val = {
                    'order_id': rec.id,
                    'product_id': line.product_id.id,
                    'name': line.product_id.name,
                    'date_planned': rec.date_order,
                    'product_qty': line.qty,
                    'price_unit': line.product_id.list_price,
                }
                val_list.append(val)
        products = self.env['purchase.order.line'].create(val_list)


class SaleOrderLineWizard(models.TransientModel):
    _name = 'sale.order.wizard.line'

    sale_id = fields.Many2one('sale.order.wizard')
    is_selected = fields.Boolean()
    sale_order = fields.Char('Sale Order')
    product_id = fields.Many2one('product.product')
    sr_no = fields.Integer('SR #', store=True)
    qty = fields.Integer('QTY')
