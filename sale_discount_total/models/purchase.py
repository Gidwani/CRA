

from odoo import api, fields, models
import odoo.addons.decimal_precision as dp


from odoo import api, fields, models, _


class DiscountConfigSetting(models.TransientModel):
    _inherit = 'res.config.settings'

    # sales_discount_account_id = fields.Many2one('account.account',
    #                                             string="Sales Discount Account")
    purchase_discount_account_id = fields.Many2one('account.account',
                                                   string="Purchase Discount Account")

    def get_values(self):
        res = super(DiscountConfigSetting, self).get_values()
        res.update({'purchase_discount_account_id':
                            int(self.env['ir.config_parameter'].sudo().get_param('purchase_discount_account_id'))or False})
        return res

    def set_values(self):
        res = super(DiscountConfigSetting, self).set_values()
        # if self.sales_discount_account_id:
        #     self.env['ir.config_parameter'].sudo().set_param('sales_discount_account_id',
        #                                                          self.sales_discount_account_id.id or False)
        if self.purchase_discount_account_id:
            self.env['ir.config_parameter'].sudo().set_param('purchase_discount_account_id',
                                                                self.purchase_discount_account_id.id or False)
        return res


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    # @api.depends('order_line.price_total')
    # def _amount_all(self):
    #     """
    #     Compute the total amounts of the SO.
    #     """
    #     for order in self:
    #         amount_untaxed = amount_tax = amount_discount = 0.0
    #         for line in order.order_line:
    #             amount_untaxed += line.price_subtotal
    #             amount_tax += line.price_tax
    #             amount_discount += (line.product_qty * line.price_unit * line.discount) / 100
    #             amount_discount += (line.product_qty * line.price_unit) / 100
    #         order.update({
    #             'amount_untaxed': amount_untaxed,
    #             'amount_tax': amount_tax,
    #             'amount_discount': amount_discount,
    #             'amount_total': amount_untaxed + amount_tax,
    #         })

    discount_type = fields.Selection([('percent', 'Percentage'), ('amount', 'Amount')], string='Discount type',
                                     readonly=True,
                                     states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                                     default='percent')
    discount_rate = fields.Float('Discount Rate', digits=dp.get_precision('Account'),
                                 readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, compute='_amount_all',
                                     track_visibility='always')
    amount_tax = fields.Monetary(string='Taxes', store=True, readonly=True, compute='_amount_all',
                                 track_visibility='always')
    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all',
                                   track_visibility='always')
    amount_discount = fields.Monetary(string='Discount', store=True, readonly=True, compute='_amount_all',
                                      digits=dp.get_precision('Account'), track_visibility='always')

    @api.onchange('discount_type', 'discount_rate', 'order_line')
    def supply_rate(self):

        for order in self:
            if order.discount_type == 'percent':
                for line in order.order_line:
                    line.discount = order.discount_rate
            else:
                total = discount = 0.0
                for line in order.order_line:
                    total += round((line.product_qty * line.price_unit))
                if order.discount_rate != 0:
                    discount = (order.discount_rate / total) * 100
                else:
                    discount = order.discount_rate
                for line in order.order_line:
                    line.discount = discount

    def _prepare_invoice(self, ):
        invoice_vals = super(PurchaseOrder, self)._prepare_invoice()
        invoice_vals.update({
            'discount_type': self.discount_type,
            'discount_rate': self.discount_rate,
        })
        return invoice_vals

    def button_dummy(self):
        self.supply_rate()
        return True

    def action_view_invoice(self, invoices=False):
        if invoices:
            invoices.filtered(lambda i:i.state == 'draft').supply_rate()
        return super().action_view_invoice()


class SaleOrderLine(models.Model):
    _inherit = "purchase.order.line"

    discount = fields.Float(string='Discount (%)', digits=(12, 2), default=0.0)
