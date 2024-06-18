import base64
import io

from odoo import models
from datetime import date
import logging
_logger = logging.getLogger(__name__)


class ReportXlsxInh(models.AbstractModel):
    _name = 'report.follow_excel_report.report_print_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, report):
        try:
            sheet = workbook.add_worksheet('Test Report')
            center = workbook.add_format({'align': 'center','border': 1})
            style = workbook.add_format({'bold': True, 'align': 'center', 'border': 1})
            header = workbook.add_format({'bold': True, 'align': 'left'})
            date_style = workbook.add_format({'text_wrap': True, 'num_format': 'dd-mm-yyyy', 'align': 'center', 'border': 1})
            product_image = io.BytesIO(base64.b64decode(self.env.company.logo))
            sheet.insert_image(0, 0, "image.jpeg", {'image_data': product_image, 'x_scale': 0.3, 'y_scale': 0.4})
            sheet.write(0, 6, self.env.company.display_name, header)
            sheet.write(1, 6, self.env.company.street, header)
            sheet.write(2, 6, self.env.company.city, header)
            sheet.write(3, 6, self.env.company.country_id.name, header)
            sheet.set_column('A:A', 20)
            sheet.set_column('B:B', 30)
            sheet.set_column('C:C', 32)
            sheet.set_column('F:F', 15)
            sheet.set_column('D:D', 15)
            sheet.set_column('G:G', 20)
            sheet.set_column('H:H', 15)
            sheet.set_column('I:I', 15)
            sheet.set_column('J:J', 15)
            partner = self.env['res.partner'].search([('id', '=', report.id)])
            row = 12
            sheet.write(6, 1, 'Customer Name', style)
            sheet.write(6, 2, partner.name, center)

            sheet.write(7, 1, 'Date', style)
            sheet.write(7, 2, date.today(), date_style)

            sheet.write(row, 0, 'Doc Date', style)
            sheet.write(row, 1, 'Invoice No', style)
            sheet.write(row, 2, 'LPO No', style)
            sheet.write(row, 3, 'Due Date', style)
            sheet.write(row, 4, 'Invoice Balance Amount', style)
            sheet.write(row, 5, 'Invoice Total Amount', style)
            sheet.write(row, 6, 'Cumulative Due Amount', style)
            sheet.write(row, 7, 'Overdue Days', style)

            total_due = 0
            payments_list = []
            # cr_list = []
            # for p in invoices:
            #     row += 1
            #     if p.move_type == 'out_refund':
            #         total_due = total_due - p.amount_residual
            #     else:
            #         total_due = total_due + p.amount_residual
            #     sheet.write(row, 0, p.invoice_date, date_style)
            #     sheet.write(row, 1, p.name, center)
            #     sheet.write(row, 2, self.get_ref(p), center)
            #     sheet.write(row, 3, p.invoice_date_due, date_style)
            #     # print(p.total_amount_due)
            #     sheet.write(row, 4, -p.amount_residual if p.move_type == 'out_refund' else p.amount_residual, center)
            #     sheet.write(row, 5, p.amount_total_signed, center)
            #     sheet.write(row, 6, total_due, center)
            #     sheet.write(row, 7, date.today() - p.invoice_date_due, center)
            #     cr_list.append(p.id)
            #
            #     payments = self.env['account.payment'].search([('ref', '=', p.name), ('state', '=', 'posted')])
            #     for x in payments:
            #         payments_list.append(x.move_id.id)
            #         for payment in x.move_id.line_ids:
            #             # if payment.id in p.unreconciled_aml_ids:
            #                 row += 1
            #                 sheet.write(row, 0, x.date, date_style)
            #                 sheet.write(row, 1, x.name, center)
            #                 sheet.write(row, 4, -x.amount, center)
            #                 total_due = total_due - x.amount
            #                 sheet.write(row, 5, total_due, center)
            # print('dd',invoices)
            # if invoices:
            #
            #     if invoices[0].invoice_outstanding_credits_debits_widget:
            #         print(invoices[0].invoice_outstanding_credits_debits_widget)
            #         # res = json.loads(invoices[0].invoice_outstanding_credits_debits_widget)
            #         res = invoices[0].invoice_outstanding_credits_debits_widget
            #         for b in res['content']:
            #             if b['move_id'] not in payments_list:
            #                 payment_name = self.env['account.move'].browse([b['move_id']])
            #                 if payment_name.id not in cr_list:
            #                     for r in payment_name.line_ids:
            #                         if r.id in partner.unreconciled_aml_ids.ids:
            #                             row += 1
            #                             sheet.write(row, 0, payment_name.date, date_style)
            #                             sheet.write(row, 1, payment_name.name, center)
            #                             sheet.write(row, 4, -b['amount'], center)
            #                             total_due = total_due - b['amount']
            #                             sheet.write(row, 6, total_due, center)
            # if not invoices:
            for c in partner.unreconciled_aml_ids.sorted('date'):
                if not c.blocked:
                    row += 1
                    # print(c.move_id.name, c.balance if c.payment_id else c.amount_residual)
                    print(c.move_id.name,  c.amount_residual if partner.currency_id.id == c.currency_id.id else c.amount_residual_currency)
                    due_amt = ''
                    if not c.payment_id:
                        if partner.currency_id.id == c.currency_id.id:
                            due_amt = c.move_id.amount_total_signed
                        else:
                            due_amt = c.move_id.amount_total
                    print(c.move_id.name,  due_amt)
                    print('------------------------')
                    # if c.move_id.name == 'PDCR/2023/07/0018':
                    #     print('gg')
                    sheet.write(row, 0, c.date, date_style)
                    sheet.write(row, 1, c.move_id.name, center)
                    sheet.write(row, 2, self.get_ref(c.move_id) if not c.payment_id else '', center)
                    sheet.write(row, 3, c.move_id.invoice_date_due if not c.payment_id else '', date_style)
                    # sheet.write(row, 4, c.balance if c.payment_id else c.amount_residual, center)
                    sheet.write(row, 4, c.amount_residual if partner.currency_id.id == c.currency_id.id else c.amount_residual_currency, center)


                    sheet.write(row, 5, due_amt, center)
                    # amt = 0
                    # if c.payment_id:
                    #     amt = c.balance
                    # else:
                        # if c.move_id.move_type == 'out_refund':
                        #     amt = -c.amount_residual
                        # else:
                    amt = c.amount_residual if partner.currency_id.id == c.currency_id.id else c.amount_residual_currency
                    total_due = total_due + amt
                    sheet.write(row, 6, total_due, center)
                    sheet.write(row, 7, date.today() - c.move_id.invoice_date_due if not c.payment_id else '', center)
            print(total_due)
            sheet.write(row+1, 0, 'Total', style)
            sheet.write(row+1, 4, total_due, style)
        except Exception as e:
            _logger.info('There was a problem printing report', str(e))

    def get_ref(self, inv):
        order = self.env['sale.order'].search([('name', '=', inv.invoice_origin)])
        if order:
            return order.client_order_ref
        else:
            return ''
