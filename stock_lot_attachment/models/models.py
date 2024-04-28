# -*- coding: utf-8 -*-

from odoo import models, fields


class StockLotInh(models.Model):
    _inherit = 'stock.lot'

    attachment_ids = fields.Binary(string="Attachment")


class StockMoveLineInh(models.Model):
    _inherit = 'stock.move.line'

    attachment_ids = fields.Binary(string="Attachment", related='lot_id.attachment_ids')
