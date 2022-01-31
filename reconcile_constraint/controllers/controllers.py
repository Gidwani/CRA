# -*- coding: utf-8 -*-
# from odoo import http


# class ReconcileConstraint(http.Controller):
#     @http.route('/reconcile_constraint/reconcile_constraint/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/reconcile_constraint/reconcile_constraint/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('reconcile_constraint.listing', {
#             'root': '/reconcile_constraint/reconcile_constraint',
#             'objects': http.request.env['reconcile_constraint.reconcile_constraint'].search([]),
#         })

#     @http.route('/reconcile_constraint/reconcile_constraint/objects/<model("reconcile_constraint.reconcile_constraint"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('reconcile_constraint.object', {
#             'object': obj
#         })
