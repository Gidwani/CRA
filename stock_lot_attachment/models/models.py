# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


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


class StockPickingInh(models.Model):
    _inherit = 'stock.picking'

    def action_download_attachment(self):
        """Method to Download the attachment"""

        url = '/web/binary/download_document?tab_id=%s' % self.move_line_ids_without_package.mapped('attachment_ids').ids
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }

