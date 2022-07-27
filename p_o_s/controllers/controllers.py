# -*- coding: utf-8 -*-
# from odoo import http


# class POS(http.Controller):
#     @http.route('/p_o_s/p_o_s/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/p_o_s/p_o_s/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('p_o_s.listing', {
#             'root': '/p_o_s/p_o_s',
#             'objects': http.request.env['p_o_s.p_o_s'].search([]),
#         })

#     @http.route('/p_o_s/p_o_s/objects/<model("p_o_s.p_o_s"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('p_o_s.object', {
#             'object': obj
#         })
