# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class unreconciled_entries(models.Model):
#     _name = 'unreconciled_entries.unreconciled_entries'
#     _description = 'unreconciled_entries.unreconciled_entries'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
