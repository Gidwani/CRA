from odoo import models, fields, api


class PurchaseOrderInh(models.Model):
    _inherit = 'purchase.order'

    perc_discount = fields.Float('Discount', compute='_compute_discount')
    net_total = fields.Float('Net Total', compute='_compute_net_total')
    perc = fields.Float(compute='compute_percentage')
    net_tax = fields.Float('Tax', compute='compute_taxes')
    note_picklist = fields.Char('Note')
    subtotal_amount = fields.Float('Subtotal Amount')

    @api.model
    def create(self, vals_list):
        rec = super().create(vals_list)
        rec.action_po_update_subtotal()
        return rec

    def action_po_update_subtotal(self):
        for rec in self:
            subtotal = 0
            for line in rec.order_line:
                subtotal = subtotal + line.subtotal
            rec.subtotal_amount = subtotal

    @api.depends('order_line', 'discount_type', 'discount_rate', 'perc')
    def compute_taxes(self):
        for order in self:
            # amount_tax = 0.0
            # for line in order.order_line:
            #     print(line.price_tax)
            #     amount_tax += line.price_tax
            # order.net_tax = amount_tax
            amount = 0
            for rec in order.order_line:
                if rec.taxes_id:
                    # if rec.taxes_id.filtered(lambda i:i.name != 'Reverse Charge Provision'):
                    if rec.taxes_id.filtered(lambda i: i.id == [19, 21]):
                        amount += rec.vat_amount

            if order.discount_type == 'percent':
                amt = amount - ((order.discount_rate / 100) * amount)
            else:
                amt = amount - ((order.perc / 100) * amount)
            order.net_tax = amt
            # flag = False
            # amount = 0
            # for rec in order.order_line:
            #     if rec.taxes_id and rec.taxes_id.filtered(lambda i: i.id != 23) and rec.taxes_id.filtered(
            #             lambda i: i.amount != 0):
            #         flag = True
            #         amount = True
            # if flag:
            #     order.net_tax = (5 / 100) * order.net_total
            # else:
            #     order.net_tax = 0

    @api.depends('discount_rate', 'discount_type', 'subtotal_amount')
    def compute_percentage(self):
        for rec in self:
            disc = 0
            if rec.discount_type == 'percent':
                disc = rec.discount_rate
            else:
                disc = (rec.discount_rate / (rec.subtotal_amount if rec.subtotal_amount != 0 else 1)) * 100
            rec.perc = disc

    @api.depends('order_line.price_total', 'order_line.subtotal', 'discount_rate', 'discount_type', )
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            amount_untaxed = amount_tax = amount_discount = subtotal = 0.0
            for line in order.order_line:
                # amount_untaxed += line.price_subtotal
                # amount_tax += line.price_tax
                # amount_discount += (line.product_qty * line.price_unit * line.discount) / 100
                # amount_discount += (line.product_qty * line.price_unit) / 100
                subtotal = subtotal + line.subtotal

            order.update({
                'amount_untaxed': amount_untaxed,
                'amount_tax': amount_tax,
                'amount_discount': amount_discount,
                'amount_total': amount_untaxed + amount_tax,
                'subtotal_amount': subtotal,
                # 'net_total': subtotal - disc
            })

    @api.depends('order_line', 'discount_rate', 'discount_type', 'order_line.subtotal')
    def _compute_net_total(self):
        for rec in self:
            # subtotal = 0
            # for line in rec.order_line:
            #     subtotal = subtotal + line.subtotal
            # rec.subtotal_amount = subtotal
            rec.net_total = rec.subtotal_amount - rec.perc_discount
            rec.amount_tax = rec.net_tax
            rec.amount_total = rec.net_total + rec.amount_tax
            # rec.total_amount_due = rec.amount_total

    @api.depends('discount_rate', 'discount_type')
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

    def get_so_ref(self):
        if self.sale_order and self.so_ref:
            order = self.sale_order.split('/')[-1]
            return order + '-' + str(self.so_ref)
        return ''

    @api.depends('price_unit', 'product_qty', 'product_uom')
    def _compute_subtotal(self):
        for rec in self:
            rec.subtotal = rec.product_qty * rec.price_unit

    @api.depends('taxes_id', 'price_unit', 'product_qty')
    def _compute_vat_amount(self):
        for rec in self:
            amount = 0
            for tax in rec.taxes_id:
                if tax.id in [19, 21]:
                    amount = amount + tax.amount
            rec.vat_amount = (amount * rec.product_qty / 100) * rec.price_unit

    @api.depends('sequence', 'order_id')
    def _compute_get_number(self):
        for order in self.mapped('order_id'):
            number = 1
            for line in order.order_line:
                line.number = number
                number += 1

    @api.onchange('product_id')
    def onchange_get_tax(self):
        tax = self.env['account.tax'].search(
            [('type_tax_use', '=', 'purchase'), ('amount', '=', 5), ('name', '=', 'VAT 5%')])
        for rec in self:
            rec.taxes_id = tax

    # def _compute_tax_id(self):
    #     for line in self:
    #         line = line.with_company(line.company_id)
    #         fpos = line.order_id.fiscal_position_id or line.order_id.fiscal_position_id.get_fiscal_position(line.order_id.partner_id.id)
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
