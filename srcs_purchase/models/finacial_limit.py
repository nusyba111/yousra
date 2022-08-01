from odoo import fields, models, api, _

class SrcsFinancialLimit(models.Model):
    _name = "financial.limit"
    _rec_name = 'sequence'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    tender_type = fields.Char('Tender Type')
    amount_from = fields.Float('From')
    amount_to = fields.Float('To')
    # tender_procedure = fields.Boolean('Tendering Procedure')
    cba = fields.Boolean('CBA(Comparative bid analysis)')
    three_quotaions = fields.Boolean('Three Quotations')
    munites_commitee = fields.Boolean('Minutes Of Committee')
    sequence = fields.Char(string='Sequence', readonly=True, copy=False, index=True,
                           default=lambda self: 'New Financial Limit')

    @api.model
    def create(self, vals):
        if vals.get('sequence', 'NEW') == 'NEW':
            vals['sequence'] = self.env['ir.sequence'].next_by_code('financial.limit') or 'NEW'
        result = super(SrcsFinancialLimit, self).create(vals)
        return result
        