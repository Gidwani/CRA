from odoo import models, fields, api


class PurchaseOrderInh(models.Model):
    _inherit = 'purchase.order'

    perc_discount = fields.Float('Discount', compute="_compute_discount")
    net_total = fields.Float('Net Total', compute="_compute_net_total")
    perc = fields.Float(compute='compute_percentage')
    net_tax = fields.Float('Tax', compute='compute_taxes')
    note_picklist = fields.Char('Note')
    subtotal_amount = fields.Float('Subtotal Amount', compute='_compute_net_total')

    @api.depends('order_line', 'discount_rate')
    def compute_taxes(self):
        for order in self:
            amount_tax = 0.0
            for line in order.order_line:
                amount_tax += line.price_tax
            order.net_tax = amount_tax
        # flag = False
        # for rec in self.order_line:
        #     if rec.taxes_id:
        #         flag = True
        # if flag:
        #     self.net_tax = (5 / 100) * self.net_total
        # else:
        #     self.net_tax = 0

    @api.depends('discount_rate')
    def compute_percentage(self):
        for rec in self:
            if rec.discount_type == 'percent':
                rec.perc = rec.discount_rate
            else:
                rec.perc = (rec.discount_rate / rec.subtotal_amount) * 100

    @api.depends('order_line', 'discount_rate', 'discount_type')
    def _compute_net_total(self):
        for rec in self:
            subtotal = 0
            for line in rec.order_line:
                subtotal = subtotal + line.subtotal
            rec.subtotal_amount = subtotal
            rec.net_total = rec.subtotal_amount - rec.perc_discount
            rec.amount_tax = rec.net_tax
            print(rec.net_tax)
            rec.amount_total = rec.net_total + rec.amount_tax
            # rec.total_amount_due = rec.amount_total

    @api.depends('discount_rate')
    def _compute_discount(self):
        for rec in self:
            if rec.discount_type == 'percent':
                rec.perc_discount = (rec.discount_rate / 100) * rec.subtotal_amount
            else:
                rec.perc_discount = rec.discount_rate

    def action_show_sale_products(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sale Order Products',
            'view_id': self.env.ref('so_po_customization.view_sale_order_wizard_form', False).id,
            'target': 'new',
            'res_model': 'sale.order.wizard',
            'view_mode': 'form',
        }


class PurchaseOrderLineInh(models.Model):
    _inherit = 'purchase.order.line'

    remarks = fields.Char("Remarks")
    number = fields.Integer(compute='_compute_get_number', store=True)
    so_ref = fields.Integer('Ref')
    sale_order = fields.Char('Sale Order')
    vat_amount = fields.Float('VAT Amount', compute='_compute_vat_amount')
    subtotal = fields.Float('Subtotal', compute='_compute_subtotal')

    @api.depends('price_unit', 'product_qty')
    def _compute_subtotal(self):
        for rec in self:
            rec.subtotal = rec.product_uom_qty * rec.price_unit

    def _compute_vat_amount(self):
        for rec in self:
            amount = 0
            for tax in rec.taxes_id:
                amount = amount + tax.amount
            rec.vat_amount = (amount / 100) * rec.price_unit

    @api.depends('sequence', 'order_id')
    def _compute_get_number(self):
        for order in self.mapped('order_id'):
            number = 1
            for line in order.order_line:
                line.number = number
                number += 1

    @api.onchange('product_id')
    def onchange_get_tax(self):
        tax = self.env['account.tax'].search([('type_tax_use', '=', 'purchase'), ('amount', '=', 5), ('name', '=', 'VAT 5%')])
        for rec in self:
            rec.taxes_id = tax

    def _compute_tax_id(self):
        for line in self:
            line = line.with_company(line.company_id)
            fpos = line.order_id.fiscal_position_id or line.order_id.fiscal_position_id.get_fiscal_position(line.order_id.partner_id.id)
            # filter taxes by company
            # taxes = line.product_id.supplier_taxes_id.filtered(lambda r: r.company_id == line.env.company)
            # line.taxes_id = fpos.map_tax(taxes, line.product_id, line.order_id.partner_id)

    def unlink(self):
        for res in self:
            i = 1
            for rec in res.order_id.order_line:
                if rec.id != res.id:
                    rec.update({
                        'number': i
                    })
                    i = i + 1
        record = super(PurchaseOrderLineInh, self).unlink()