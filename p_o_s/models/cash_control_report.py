import statistics
from statistics import mode, mean

from odoo import models, fields, api
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime

# class CashControlReportWizard(models.TransientModel):
#     _name = 'cash.control.report.wizard'
#     _description = 'Cash Control Report'

#     # from_date = fields.Date('From', default=fields.Date.today())
#     # to_date = fields.Date('To', default=fields.Date.today())
#     pos_config_id = fields.Many2one('pos.config',"Point Of Sale")
    
#     def get_report(self):
#         data = {
#             'ids': self.ids,
#             'model': self._name,
#             'form': {
#                 # 'from_date': fields.Date.from_string(self.from_date),
#                 # 'to_date': fields.Date.from_string(self.to_date),
#                 'pos_config_id':self.pos_config_id.id,
#             },
#         }

#         return self.env.ref('p_o_s.cash_control_report').report_action(self, data=data)


# class CashControlReport(models.AbstractModel):
#     _name = 'report.p_o_s.cash_control_template'

#     @api.model
#     def _get_report_values(self, docids, data=None):
#         cashbox_list = []
#         pos_config_id = data['form']['pos_config_id']
#         # from_date = data['form']['from_date']
#         # to_date = data['form']['to_date']
    
#         statement_cashbox_list = self.env['account.bank.statement.cashbox'].search([('config_id','=',pos_config_id)])
#         print("*****************",statement_cashbox_list)
#         cashbox_list = statement_cashbox_list
        # for line in statement_cashbox_list:
        #     # print("*****************",line.pos_config_ids)
        #     for rec in line.pos_config_ids:
        #         print("*****************",rec.id)
        #         print("*****************",pos_config_id)
        #         if rec.id == pos_config_id:
        #             cashbox_list = line



      
        # return {
        #     'doc_ids': data['ids'],
        #     'doc_model': data['model'],
        #     # 'from_date': from_date,
        #     # 'to_date': to_date,
        #     'docs': cashbox_list,
        # }
        
        # point_of_sale.view_account_bnk_stmt_cashbox_footer"
        # access_account_bank_statement_cashbox,account_bank_statement_cashbox.account_bank_statement_cashbox,model_account_bank_statement_cashbox,,1,1,1,1

class Cash(models.Model):
    _inherit = 'account.bank.statement.cashbox'


    # total_wiz = fields.Float(compute='_compute_total')


    # @api.depends('cashbox_lines_ids', 'cashbox_lines_ids.coin_value', 'cashbox_lines_ids.number')
    # def _compute_total(self):
    #     for cashbox in self:
    #         cashbox.total = sum([line.subtotal for line in cashbox.cashbox_lines_ids])



class AccountBankStmtCashWizard(models.Model):
    _inherit = 'account.cashbox.line'

    config_id = fields.Many2one('pos.session',string ="Point Of Sale")
    total_wiz = fields.Float(compute="get_total_wiz", string='Total')

    # @api.multi
    # def get_total_wiz(self):

    # self.total_new()
    #   self.total == self.env['account.bank.statement.cashbox'].search([('config_id','=',pos_config_id)])        
    #     self.qty_delivered = self.technical_id.product_qty_delivered


class AccountBankStmtCashWizard(models.Model):
    _inherit = 'pos.session'

    @api.model
    def get_default_bank_id(self):
        bank_id = self.env['account.bank.statement'].search([('pos_session_id','=',self.id)]) 
        return bank_id.cashbox_start_id.id

    bank_statment_cashbox_id = fields.Many2one('account.bank.statement.cashbox',default=get_default_bank_id)
# ,related=bank_statment_cashbox_id.cashbox_lines_ids
    cash_box = fields.One2many('account.cashbox.line','config_id',related="bank_statment_cashbox_id.cashbox_lines_ids")


    account_emp = fields.Many2one('res.users', string='Accountant Employee')
    safety_emp = fields.Many2one('res.users', string='Security Employee')
    comment = fields.Text(string='Comment')
    note = fields.Text(string='Remark')
    user_id = fields.Many2one('res.users', string=' Casheir Employee')
    signature = fields.Char(string='Signature')




