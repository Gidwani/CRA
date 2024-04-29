# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


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

