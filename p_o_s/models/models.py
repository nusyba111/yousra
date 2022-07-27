# -*- coding: utf-8 -*-

from odoo import models, fields, api,_


# class p_o_s(models.Model):
#     _inherit = 'account.bank.statement.cashbox'
    # _description = 'p_o_s.p_o_s'

    # name = fields.Char(string="test")
    # value = fields.Integer()
    # value2 = fields.Float(compute="_value_pc", store=True)
    # description = fields.Date(string="Date")

    # @api.depends('value')
    # def _value_pc(self):
    #     for record in self:
    #         record.value2 = float(record.value) / 100

# class ReportSaleDetails(models.AbstractModel):
#     _inherit = 'report.point_of_sale.report_saledetails'
#     