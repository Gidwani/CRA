# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import UserError


class IrAttachmentInh(models.Model):
    _inherit = 'ir.attachment'

    temp_file_name = fields.Char()


class StockQuantInh(models.Model):
    _inherit = 'stock.quant'

    attachment_ids = fields.Many2many('ir.attachment', string="Add File", related='lot_id.attachment_ids')
    inventory_quantity_auto_apply = fields.Float('Inventoried Quantity', digits='Product Unit of Measure',
        compute='_compute_inventory_quantity_auto_apply',
        inverse='_set_inventory_quantity', groups='stock.group_stock_manager,stock.group_stock_user'
    )

    def action_download(self):
        for r in self:
            for rec in r.attachment_ids:
                return {
                    "type": "ir.actions.act_url",
                    "target": "new",
                    "url": "/web/content?model=ir.attachment&download=true&field=datas&id={}".format(
                        rec.id),
                }

    @api.model
    def _get_quants_action(self, domain=None, extend=False):
        """ Returns an action to open (non-inventory adjustment) quant view.
        Depending of the context (user have right to be inventory mode or not),
        the list view will be editable or readonly.

        :param domain: List for the domain, empty by default.
        :param extend: If True, enables form, graph and pivot views. False by default.
        """
        if not self.env['ir.config_parameter'].sudo().get_param('stock.skip_quant_tasks'):
            self._quant_tasks()
        ctx = dict(self.env.context or {})
        ctx['inventory_report_mode'] = True
        ctx.pop('group_by', None)
        action = {
            'name': _('Locations'),
            'view_mode': 'list,form',
            'res_model': 'stock.quant',
            'type': 'ir.actions.act_window',
            'context': ctx,
            'domain': domain or [],
            'help': """
                    <p class="o_view_nocontent_empty_folder">{}</p>
                    <p>{}</p>
                    """.format(_('No Stock On Hand'),
                               _('This analysis gives you an overview of the current stock level of your products.')),
        }

        target_action = self.env.ref('stock.dashboard_open_quants', False)
        if target_action:
            action['id'] = target_action.id

        form_view = self.env.ref('stock.view_stock_quant_form_editable').id
        if self.env.context.get('inventory_mode') and self.user_has_groups('stock.group_stock_manager'):
            action['view_id'] = self.env.ref('stock.view_stock_quant_tree_editable').id
        else:
            action['view_id'] = self.env.ref('stock.view_stock_quant_tree_editable').id
            # action['view_id'] = self.env.ref('stock.view_stock_quant_tree').id
        action.update({
            'views': [
                (action['view_id'], 'list'),
                (form_view, 'form'),
            ],
        })
        if extend:
            action.update({
                'view_mode': 'tree,form,pivot,graph',
                'views': [
                    (action['view_id'], 'list'),
                    (form_view, 'form'),
                    (self.env.ref('stock.view_stock_quant_pivot').id, 'pivot'),
                    (self.env.ref('stock.stock_quant_view_graph').id, 'graph'),
                ],
            })
        return action


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

