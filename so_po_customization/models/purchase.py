from odoo import models, fields, api


class PurchaseOrderInh(models.Model):
    _inherit = 'purchase.order'

    def action_show_sale_products(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sale Order Products',
            'view_id': self.env.ref('so_po_customization.view_sale_order_wizard_form', False).id,
            'target': 'new',
            'res_model': 'sale.order.wizard',
            'view_mode': 'form',
        }

    def action_select_products(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Select Products',
            'view_id': self.env.ref('so_po_customization.view_select_products_form', False).id,
            # 'context': {'default_ref': self.name, 'default_order_amount': self.amount_total, 'default_user_id': self.user_id.id},
            'target': 'new',
            'res_model': 'select.products',
            'view_mode': 'form',
        }


class PurchaseOrderLineInh(models.Model):
    _inherit = 'purchase.order.line'

    remarks = fields.Char("Remarks")
    number = fields.Integer(compute='_compute_get_number', store=True)

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