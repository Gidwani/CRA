# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, _


class SaleReportInh(models.Model):
    _inherit = 'sale.report'

    sale_average = fields.Float('Average Sale', readonly=True, group_operator="avg")

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        with_ = ("WITH %s" % with_clause) if with_clause else ""

        select_ = """
            coalesce(min(l.id), -s.id) as id,
            l.product_id as product_id,
            avg(l.price_unit) as sale_average,
            t.uom_id as product_uom,
            CASE WHEN l.product_id IS NOT NULL THEN sum(l.product_uom_qty / u.factor * u2.factor) ELSE 0 END as product_uom_qty,
            CASE WHEN l.product_id IS NOT NULL THEN sum(l.qty_delivered / u.factor * u2.factor) ELSE 0 END as qty_delivered,
            CASE WHEN l.product_id IS NOT NULL THEN sum(l.qty_invoiced / u.factor * u2.factor) ELSE 0 END as qty_invoiced,
            CASE WHEN l.product_id IS NOT NULL THEN sum(l.qty_to_invoice / u.factor * u2.factor) ELSE 0 END as qty_to_invoice,
            CASE WHEN l.product_id IS NOT NULL THEN sum(l.price_total / CASE COALESCE(s.currency_rate, 0) WHEN 0 THEN 1.0 ELSE s.currency_rate END) ELSE 0 END as price_total,
            CASE WHEN l.product_id IS NOT NULL THEN sum(l.price_subtotal / CASE COALESCE(s.currency_rate, 0) WHEN 0 THEN 1.0 ELSE s.currency_rate END) ELSE 0 END as price_subtotal,
            CASE WHEN l.product_id IS NOT NULL THEN sum(l.untaxed_amount_to_invoice / CASE COALESCE(s.currency_rate, 0) WHEN 0 THEN 1.0 ELSE s.currency_rate END) ELSE 0 END as untaxed_amount_to_invoice,
            CASE WHEN l.product_id IS NOT NULL THEN sum(l.untaxed_amount_invoiced / CASE COALESCE(s.currency_rate, 0) WHEN 0 THEN 1.0 ELSE s.currency_rate END) ELSE 0 END as untaxed_amount_invoiced,
            count(*) as nbr,
            s.name as name,
            s.margin as margin,
            s.date_order as date,
            s.state as state,
            s.partner_id as partner_id,
            s.user_id as user_id,
            s.company_id as company_id,
            s.campaign_id as campaign_id,
            s.medium_id as medium_id,
            s.source_id as source_id,
            extract(epoch from avg(date_trunc('day',s.date_order)-date_trunc('day',s.create_date)))/(24*60*60)::decimal(16,2) as delay,
            t.categ_id as categ_id,
            s.pricelist_id as pricelist_id,
            s.analytic_account_id as analytic_account_id,
            s.team_id as team_id,
            p.product_tmpl_id,
            partner.country_id as country_id,
            partner.industry_id as industry_id,
            partner.commercial_partner_id as commercial_partner_id,
            CASE WHEN l.product_id IS NOT NULL THEN sum(p.weight * l.product_uom_qty / u.factor * u2.factor) ELSE 0 END as weight,
            CASE WHEN l.product_id IS NOT NULL THEN sum(p.volume * l.product_uom_qty / u.factor * u2.factor) ELSE 0 END as volume,
            l.discount as discount,
            CASE WHEN l.product_id IS NOT NULL THEN sum((l.price_unit * l.product_uom_qty * l.discount / 100.0 / CASE COALESCE(s.currency_rate, 0) WHEN 0 THEN 1.0 ELSE s.currency_rate END))ELSE 0 END as discount_amount,
            s.id as order_id

        """

        for field in fields.values():
            select_ += field

        from_ = """
                sale_order_line l
                      right outer join sale_order s on (s.id=l.order_id)
                      join res_partner partner on s.partner_id = partner.id
                        left join product_product p on (l.product_id=p.id)
                            left join product_template t on (p.product_tmpl_id=t.id)
                    left join uom_uom u on (u.id=l.product_uom)
                    left join uom_uom u2 on (u2.id=t.uom_id)
                    left join product_pricelist pp on (s.pricelist_id = pp.id)
                %s
        """ % from_clause

        groupby_ = """
            l.product_id,
            l.price_unit,
            l.order_id,
            t.uom_id,
            t.categ_id,
            s.name,
            s.date_order,
            s.partner_id,
            s.user_id,
            s.state,
            s.company_id,
            s.campaign_id,
            s.medium_id,
            s.source_id,
            s.pricelist_id,
            s.analytic_account_id,
            s.team_id,
            p.product_tmpl_id,
            partner.country_id,
            partner.industry_id,
            partner.commercial_partner_id,
            l.discount,
            s.id %s
        """ % (groupby)

        return '%s (SELECT %s FROM %s GROUP BY %s)' % (with_, select_, from_, groupby_)

    def init(self):
        # self._table = sale_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % (self._table, self._query()))

    # def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
    #     with_ = ("WITH %s" % with_clause) if with_clause else ""
    #
    #     select_ = """
    #     l.id as id,
    #     l.price_unit as sale_average
    #
    #     """
    #
    #     for field in fields.values():
    #         select_ += field
    #
    #     from_ = """
    #             sale_order_line l
    #             %s
    #     """ % from_clause
    #
    #     groupby_ = """
    #     l.id,
    #     l.price_unit,
    #     l.product_id
    #     %s
    #     """ % (groupby)
    #
    #     return '%s (SELECT %s FROM %s GROUP BY %s)' % (with_, select_, from_, groupby_)
    #
    # def init(self):
    #     # self._table = sale_report
    #     tools.drop_view_if_exists(self.env.cr, self._table)
    #     self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % (self._table, self._query()))


class SaleOrderInh(models.Model):
    _inherit = 'sale.order'

    perc_discount = fields.Float('Discount', compute='_compute_discount')
    net_total = fields.Float('Net Total',compute='_compute_net_total')
    perc = fields.Float(compute='compute_percentage')
    net_tax = fields.Float('Tax', compute='compute_taxes')
    note_picklist = fields.Char('Note')
    subtotal_amount = fields.Float('Subtotal Amount', compute='_compute_net_total')
    # po_no = fields.Char()

    # def _prepare_invoice(self, ):
    #     invoice_vals = super(SaleOrderInh, self)._prepare_invoice()
    #     invoice_vals.update({
    #         'po_no': self.po_no,
    #     })
    #     return invoice_vals

    @api.depends('order_line', 'discount_rate')
    def compute_taxes(self):
        flag = False
        for rec in self.order_line:
            if rec.tax_id and rec.tax_id.amount != 0:
                flag = True
        if flag:
            self.net_tax = (5 / 100) * self.net_total
        else:
            self.net_tax = 0

    @api.depends('discount_rate')
    def compute_percentage(self):
        for rec in self:
            if rec.discount_type == 'percent':
                rec.perc = rec.discount_rate
            else:
                rec.perc = (rec.discount_rate / rec.subtotal_amount) * 100

    @api.depends('discount_rate')
    def _compute_discount(self):
        for rec in self:
            if rec.discount_type == 'percent':
                rec.perc_discount = (rec.discount_rate / 100) * rec.subtotal_amount
            else:
                rec.perc_discount = rec.discount_rate

    @api.depends('order_line', 'order_line.subtotal', 'discount_rate', 'discount_type')
    def _compute_net_total(self):
        for rec in self:
            subtotal = 0
            for line in rec.order_line:
                subtotal = subtotal + line.subtotal
            rec.subtotal_amount = subtotal
            rec.net_total = rec.subtotal_amount - rec.perc_discount
            rec.amount_total = rec.net_total + rec.amount_tax

    def get_lot_no(self, line):
        picking = self.env['stock.picking'].search([('sale_id', '=', line.order_id.id)])
        lot = ''
        if picking:
            for rec in picking.move_line_ids_without_package:
                if rec.product_id.id == line.product_id.id and rec.so_no == line.number:
                    # lot.append(rec.lot_id.name)
                    lot = rec.lot_id.name
        # a = ''
        # if lot:
        #     if len(lot) > 1:
        #         a = ','.join(lot)
        #     else:
        #         a = a[0]
        # return a
        return lot

    def get_product_qty(self, ml):
        product_qty = self.env['product.template'].search([('id', '=', ml.product_id.product_tmpl_id.id)])
        # for line in ml.sale_id.order_line:
        if ml.product_uom.name == 'Lth':
            qty = int(product_qty.available_qty)/6
            formatted_float = "{:.2f}".format(float(qty))
            qty = str(formatted_float) + " Lth"
        else:
            qty = float(product_qty.available_qty)
            formatted_float = "{:.2f}".format(qty)
            qty = str(formatted_float) + ' ' + product_qty.uom_id.name
        return qty

    def get_onhand_qty(self, ml):
        product_qty = self.env['product.template'].search([('id', '=', ml.product_id.product_tmpl_id.id)])
        # for line in ml.sale_id.order_line:
        if ml.product_uom.name == 'Lth':
            qty = int(product_qty.qty_available)/6
            formatted_float = "{:.2f}".format(float(qty))
            qty = str(formatted_float) + " Lth"
        else:
            qty = float(product_qty.qty_available)
            formatted_float = "{:.2f}".format(qty)
            qty = str(formatted_float) + ' ' + product_qty.uom_id.name
        return qty


class SaleOrderLineInh(models.Model):
    _inherit = 'sale.order.line'

    remarks = fields.Char('Remarks')
    number = fields.Integer(compute='_compute_get_number', store=True)
    vat_amount = fields.Float('VAT Amount', compute='_compute_vat_amount')
    subtotal = fields.Float('Subtotal', compute='_compute_subtotal')

    def write(self, vals):
        old = self.price_unit
        record = super().write(vals)
        if 'price_unit' in vals:
            self.order_id.message_post(body=_("Unit Price of product %s changed from:%s to %s.", self.product_id.name,
                                     old, self.price_unit)
                              )
        return record

    def unlink(self):
        for res in self:
            i = 1
            for rec in res.order_id.order_line:
                if rec.id != res.id:
                    rec.update({
                        'number': i
                    })
                    i = i + 1
        record = super(SaleOrderLineInh, self).unlink()

    @api.depends('price_unit', 'product_uom_qty')
    def _compute_subtotal(self):
        for rec in self:
            rec.subtotal = rec.product_uom_qty * rec.price_unit

    def _compute_vat_amount(self):
        for rec in self:
            amount = 0
            for tax in rec.tax_id:
                amount = amount + tax.amount
            rec.vat_amount = ((amount/100) * rec.price_unit) * rec.product_uom_qty

    @api.depends('sequence', 'order_id')
    def _compute_get_number(self):
        for order in self.mapped('order_id'):
            number = 1
            for line in order.order_line:
                line.number = number
                number += 1