# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle 
#
##############################################################################

from odoo import api, fields, models, _
import xlwt
from io import BytesIO
import base64
from xlwt import easyxf
from datetime import datetime


class bulk_export(models.TransientModel):
    _name ='bulk.export'
    
    
    def get_customer_detail(self,partner):
        customer = '\n'
        if partner.name:
            customer += partner.name+'\n'
        if partner.street:
            customer += partner.street+'\n'
        if partner.street2:
            customer += partner.street2+'\n'
        if partner.city:
            customer += partner.city
            if partner.zip:
                customer += ', '+partner.zip+'\n'
            else:
                customer += '\n'
        
        if partner.state_id:
            customer += partner.state_id.name
            if partner.country_id:
                customer += ', '+partner.country_id.name+'\n'
            else:
                customer += '\n'
                    
        if not partner.state_id:
            if partner.country_id:
                customer += partner.country_id.name+'\n'

        return customer
        
             
    
    def export_excel(self):
        active_ids = self._context.get('active_ids')
        model = self._context.get('active_model')
        model_pool=self.env[model]
        record_ids = model_pool.browse(active_ids)
        main_header_style = easyxf('font:height 400;pattern: pattern solid, fore_color gray25;'
                                   'align: horiz center;font: color black; font:bold True;'
                                   "borders: top thin,left thin,right thin,bottom thin")

        header_style = easyxf('font:height 200;pattern: pattern solid, fore_color gray25;'
                              'align: horiz center;font: color black; font:bold True;'
                              "borders: top thin,left thin,right thin,bottom thin")
                                   
        text_left = easyxf('font:height 200; align: horiz left;' "borders: top thin,bottom thin")
        text_center = easyxf('font:height 200; align: horiz center;' "borders: top thin,bottom thin")
        text_left_bold = easyxf('font:height 200; align: horiz left;font:bold True;' "borders: top thin,bottom thin")
        text_right = easyxf('font:height 150; align: horiz right;' "borders: top thin,bottom thin",
                            num_format_str='0.00')

        workbook = xlwt.Workbook()
        worksheet = []
        for l in range(0, len(active_ids)):
            worksheet.append(l)
            
        work = 0
        if model == 'sale.order':
            filename='Sale Export.xls'
        elif model == 'purchase.order':
            filename = 'Purchase Export.xls'
        else:
            filename = 'Invoice Export.xls'
        for record in record_ids:
            if model == 'account.move':
                number = ''
                if record.name:
                    number = str(record.name)
                    number= number.replace('/','_')
                else:
                    number = 'Unknown_'+str(work)
                worksheet[work] = workbook.add_sheet(number)
            else:
                worksheet[work] = workbook.add_sheet(record.name)

            if model == 'sale.order':
                worksheet[work].write_merge(0, 1, 1, 6, 'SALE ORDER: '+record.name, main_header_style)
            elif model == 'purchase.order':
                worksheet[work].write_merge(0, 1, 1, 6, 'PURCHASE ORDER: ' + record.name, main_header_style)
            else:
                inv_name = 'INVOICE'
                if record.name:
                    inv_name = inv_name + ' : '+record.name
                worksheet[work].write_merge(0, 1, 1, 6, inv_name, main_header_style)

            customer = self.get_customer_detail(record.partner_id)
            worksheet[work].write_merge(2, 3, 0, 7, ' ')
            # worksheet[work].write_merge(4, 4, 0, 2, 'Customer', text_left_bold)
            worksheet[work].write_merge(4, 9, 0, 2, customer, text_left)

            worksheet[work].write_merge(4, 4, 4, 5, 'Date', text_left_bold)
            if model == 'account.move':
                worksheet[work].write_merge(5, 5, 4, 5, 'Origin', text_left_bold)
            else:
                worksheet[work].write_merge(5, 5, 4, 5, 'Reference', text_left_bold)
            worksheet[work].write_merge(6, 6, 4, 5, 'Payment Term', text_left_bold)
            worksheet[work].write_merge(7, 7, 4, 5, 'Currency', text_left_bold)
            if model == 'sale.order':
                worksheet[work].write_merge(8, 8, 4, 5, 'Salesperson', text_left_bold)

            date_order=''
            if model == 'account.move':
                if record.invoice_date:
                    date_order = record.invoice_date
#                    date_order = datetime.strptime(date_order, '%Y-%m-%d')
                    date_order = date_order.strftime("%d-%m-%Y")
            else:
                date_order = record.date_order
                print ("=====",date_order,type(date_order))
#                date_order = datetime.strptime(date_order, '%Y-%m-%d %H:%M:%S')
                date_order = date_order.strftime("%d-%m-%Y %H:%M:%S")
            worksheet[work].write_merge(4, 4, 6, 7, date_order or '', text_left)
            if model == 'sale.order':
                worksheet[work].write_merge(5, 5, 6, 7, record.client_order_ref or '', text_left)
                worksheet[work].write_merge(6, 6, 6, 7, record.payment_term_id.name or '', text_left)
            elif model == 'purchase.order':
                worksheet[work].write_merge(5, 5, 6, 7, record.partner_ref or '', text_left)
                worksheet[work].write_merge(6, 6, 6, 7, record.payment_term_id.name or '', text_left)
            else:
                worksheet[work].write_merge(5, 5, 6, 7, record.invoice_origin or '', text_left)
                worksheet[work].write_merge(6, 6, 6, 7, record.invoice_payment_term_id.name or '', text_left)


            


            if model == 'account.move' or model == 'purchase.order':
                worksheet[work].write_merge(7, 7, 6, 7, record.currency_id.name or '', text_left)
            else:
                worksheet[work].write_merge(7, 7, 6, 7, record.pricelist_id.currency_id.name or '', text_left)

            if model == 'sale.order':
                worksheet[work].write_merge(8, 8, 6, 7, record.user_id.name or '', text_left)


            worksheet[work].write_merge(10, 11, 0, 7, ' ')
            r=12
            # worksheet[work].write_merge(r, r, 0, 1, 'CODE', header_style)
            # worksheet[work].write_merge(r, r, 2, 3, 'PRODUCT', header_style)
            # worksheet[work].write(r, 4, 'QTY', header_style)
            # worksheet[work].write(r, 5, 'UOM', header_style)
            # worksheet[work].write(r, 6, 'PRICE', header_style)
            # worksheet[work].write(r, 7, 'SUB-TOTAL', header_style)
            worksheet[work].write(r, 1, 'Descriptions', header_style)
            worksheet[work].write(r, 2, 'Units', header_style)
            worksheet[work].write(r, 3, 'QTY', header_style)
            worksheet[work].write(r, 4, 'U.Price', header_style)
            worksheet[work].write(r, 5, 'T.Price', header_style)
            worksheet[work].write(r, 6, 'U.Weight', header_style)
            worksheet[work].write(r, 7, 'T.Weight', header_style)
            worksheet[work].write(r, 8, 'HS Code', header_style)
            worksheet[work].write(r, 9, 'COO', header_style)
            r+=1
            rec_lines=False
            if model == 'account.move':
                rec_lines = record.invoice_line_ids
            else:
                rec_lines = record.order_line
            for line in rec_lines:
                worksheet[work].write(r, 1, line.product_id.name, text_left)
                # worksheet[work].write_merge(r, r, 2, 3, line.product_id.name, text_left)
                if model == 'sale.order':
                    worksheet[work].write(r, 2, line.product_uom.name, text_center)
                    worksheet[work].write(r, 3, line.product_uom_qty, text_right)
                elif model == 'purchase.order':
                    worksheet[work].write(r, 4, line.product_qty, text_right)
                else:
                    worksheet[work].write(r, 2, line.product_uom_id.name, text_center)
                    worksheet[work].write(r, 3, line.quantity, text_right)
                # if model == 'account.move':
                #     worksheet[work].write(r, 5, line.product_uom_id.name, text_center)
                # else:
                #     worksheet[work].write(r, 7, line.product_uom.name, text_center)
                worksheet[work].write(r, 4, line.price_unit, text_center)
                worksheet[work].write(r, 5, line.price_subtotal, text_center)
                worksheet[work].write(r, 6, line.product_id.weight, text_center)
                if model == 'sale.order':
                    worksheet[work].write(r, 7, (line.product_id.weight * line.product_uom_qty), text_center)
                if model == 'account.move':
                    worksheet[work].write(r, 7, (line.product_id.weight * line.quantity), text_center)
                worksheet[work].write(r, 8, line.product_id.hs_code, text_center)
                r+=1
            worksheet[work].write_merge(r, r, 0, 7, '')
            r+=1
            worksheet[work].write_merge(r, r+2, 0, 4, '')
            worksheet[work].write_merge(r, r, 6, 8, 'SUBTOTAL', header_style)
            worksheet[work].write(r, 9, record.amount_untaxed, text_right)
            r+=1
            worksheet[work].write_merge(r, r, 6, 8, 'TAX', header_style)
            worksheet[work].write(r, 9, record.amount_tax, text_right)
            r += 1
            worksheet[work].write_merge(r, r, 6, 8, 'TOTAL', header_style)
            worksheet[work].write(r, 9, record.amount_total, text_right)

            work+=1
            
        fp = BytesIO()
        workbook.save(fp)
        export_id = self.env['bulk.export.excel'].create(
            {'excel_file': base64.encodestring(fp.getvalue()), 'file_name': filename})
        fp.close()

        return {
            'view_mode': 'form',
            'res_id': export_id.id,
            'res_model': 'bulk.export.excel',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
            
        
    
     
bulk_export()


class bulk_export_excel(models.TransientModel):
    _name= "bulk.export.excel"
    
    excel_file = fields.Binary('Excel File')
    file_name = fields.Char('Excel Name', size=64)

bulk_export_excel()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
