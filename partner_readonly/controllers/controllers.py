# -*- coding: utf-8 -*-
# from odoo import http


# class PartnerReadonly(http.Controller):
#     @http.route('/partner_readonly/partner_readonly/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/partner_readonly/partner_readonly/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('partner_readonly.listing', {
#             'root': '/partner_readonly/partner_readonly',
#             'objects': http.request.env['partner_readonly.partner_readonly'].search([]),
#         })

#     @http.route('/partner_readonly/partner_readonly/objects/<model("partner_readonly.partner_readonly"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('partner_readonly.object', {
#             'object': obj
#         })
