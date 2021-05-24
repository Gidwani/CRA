from odoo import models, fields, api


class PurchaseOrderInh(models.Model):
    _inherit = 'purchase.order'

    do_no = fields.Char("Supplier Do #")


class PurchaseOrderLineInh(models.Model):
    _inherit = 'purchase.order.line'

    remarks = fields.Char("Remarks")

    @api.onchange('product_id')
    def onchange_get_tax(self):
        tax = self.env['account.tax'].search([('type_tax_use', '=', 'purchase'), ('amount', '=', 5)])
        for rec in self:
            rec.taxes_id = tax

    def _compute_tax_id(self):
        for line in self:
            line = line.with_company(line.company_id)
            fpos = line.order_id.fiscal_position_id or line.order_id.fiscal_position_id.get_fiscal_position(line.order_id.partner_id.id)
            # filter taxes by company
            # taxes = line.product_id.supplier_taxes_id.filtered(lambda r: r.company_id == line.env.company)
            # line.taxes_id = fpos.map_tax(taxes, line.product_id, line.order_id.partner_id)