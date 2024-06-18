# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class IrAttachmentInh(models.Model):
    _inherit = 'ir.attachment'

    temp_file_name = fields.Char()


class StockQuantInh(models.Model):
    _inherit = 'stock.quant'

    attachment_ids = fields.Many2many('ir.attachment', string="Add File", related='lot_id.attachment_ids')

    def action_download(self):
        for r in self:
            for rec in r.attachment_ids:
                return {
                    "type": "ir.actions.act_url",
                    "target": "new",
                    "url": "/web/content?model=ir.attachment&download=true&field=datas&id={}".format(
                        rec.id),
                }


class StockLotInh(models.Model):
    _inherit = 'stock.lot'

    attachment_ids = fields.Many2many('ir.attachment', string="Add File")

    @api.constrains('attachment_ids')
    def name_no_duplication(self):
        if len(self.attachment_ids.ids) > 1:
            raise UserError('You can attach only 1 file.')

    def action_download(self):
        for r in self:
            for rec in r.attachment_ids:
                return {
                    "type": "ir.actions.act_url",
                    "target": "new",
                    "url": "/web/content?model=ir.attachment&download=true&field=datas&id={}".format(
                        rec.id),
                }


class StockMoveLineInh(models.Model):
    _inherit = 'stock.move.line'

    attachment_ids = fields.Many2many('ir.attachment', string="Attachment", related='lot_id.attachment_ids')

    def action_download(self):
        for rec in self.attachment_ids:
            return {
                "type": "ir.actions.act_url",
                "target": "new",
                "url": "/web/content?model=ir.attachment&download=true&field=datas&id={}".format(
                    rec.id),
            }

    def action_download_tree(self):
        url = '/web/binary/download_document?tab_id=%s' % self.picking_id.move_line_ids_without_package.mapped(
            'attachment_ids').ids
        for rec in self.picking_id.move_line_ids_without_package:
            if rec.attachment_ids:
                for r in rec.attachment_ids:
                    r.temp_file_name = str(rec.so_no) + ' - ' + r.name + ' - ' + str(rec.quantity) + ' ' + (
                        rec.product_uom_id.name)
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }


class StockPickingInh(models.Model):
    _inherit = 'stock.picking'

    def action_download_attachment(self):
        url = '/web/binary/download_document?tab_id=%s' % self.move_line_ids_without_package.mapped('attachment_ids').ids
        for rec in self.move_line_ids_without_package:
            if rec.attachment_ids:
                for r in rec.attachment_ids:
                    r.temp_file_name = str(rec.so_no) + ' - ' + r.name + ' - ' + str(rec.quantity) + ' ' + (rec.product_uom_id.name)
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }

