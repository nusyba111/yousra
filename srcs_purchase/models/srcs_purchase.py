from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools.float_utils import float_is_zero

class SrcsPurchase(models.Model):
    _inherit = "purchase.order"

    # is_single_source = fields.Boolean('Is Single Source Tender')
    gift_certificate = fields.Binary('Gift Certificate')
    way_bill = fields.Binary('Way Bill/Bill of Leading')
    packing_list = fields.Binary('Packing List')
    proforma_invoice = fields.Binary('Proforma Invoice')
    is_purchase_request = fields.Boolean(string="Is Purchase Request" )
    purchase_request_id = fields.Many2one(comodel_name="purchase.request", string="Purchase Request", required=True, readonly=True )
    mean_transport = fields.Selection([
        ('air', 'Air'),('road','Road'),('sea','Sea'),('other','Other'),
    ], string='Mean of Transport')
    is_committee = fields.Boolean('Is Committee',related="requisition_id.is_committee")
    is_cba = fields.Boolean('CBA(Comparative bid analysis)',related="requisition_id.is_cba")
    one_quotaion = fields.Boolean('One Quotation',related="requisition_id.one_quotaion")
    arrival_date = fields.Date('Date of Arrival')
    bill_leading = fields.Char('Bill of Leading')
    vessel = fields.Char('Vessel')
    flight_number = fields.Char('Flight Number')
    truck_number = fields.Char('Truck Number')
    service = fields.Boolean('Service order')
    tender_type = fields.Selection([
        ('rest_tender', 'Restricted Tenders'),
        ('publish_tender','Published Tender'),
        ('single_tender','Single Source Tender'),
    ], string='Tender Type')
    cv = fields.Binary(string="CV")
    regestration_certificate = fields.Binary(string="Registration Certificate")
    tax_regs_no = fields.Binary(string="Tax Regs No")
    expereince = fields.Binary(string="Experience")
    insurance = fields.Binary(string="Insurance")
    finanical_offer = fields.Char(string="Financial Offer",related='tax_totals_json')
    state = fields.Selection([('draft', 'RFQ'),('sent', 'RFQ Sent'),
        ('pro_officer', 'Procurement Officer '),('pro_head','procurement Head'),('re_dep_manager','Requester Department Manager'),
        ('secratry_general','Secretary General'),('tender_procedure','Tendering Procedure'),('committee_minute','Committee Minute'),
        ('cba','CBA'),('purchase','Purchase Order'),('grn','GRN'),('payment','Payment'),('receive_goods','receiving goods/service'),
        ('done', 'Locked'),('cancel', 'Cancelled'),
    ],default='draft', string='State')
    invoice_status = fields.Selection([
        ('no', 'Nothing to Bill'),
        ('to invoice', 'Waiting Bills'),
        ('invoiced', 'Fully Billed'),
    ], string='Billing Status', compute='_get_invoiced', store=True, readonly=True, copy=False, default='no')
    # new field
    date_of_receipt = fields.Date('Date')
    @api.depends('state', 'order_line.qty_to_invoice')
    def _get_invoiced(self):
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for order in self:
            # if order.state not in ('purchase', 'done','grn','cba','pro_officer','pro_head','re_dep_manager','secratry_general','tender_procedure','committee_minute','draft'):
            #     print('___________state',order.state)
            #     order.invoice_status = 'no'
            #     continue
            if any(
                not float_is_zero(line.qty_to_invoice, precision_digits=precision)
                for line in order.order_line.filtered(lambda l: not l.display_type)
            ):
                print('________________to invoice',order.state)
                order.invoice_status = 'to invoice'
            elif (
                all(
                    float_is_zero(line.qty_to_invoice, precision_digits=precision)
                    for line in order.order_line.filtered(lambda l: not l.display_type)
                )
                and order.invoice_ids
            ):
                print('________________invoiceed',order.state)
                order.invoice_status = 'invoiced'
            else:
                order.invoice_status = 'no'

    
    def procurement_offcer(self):
        self.state = 'pro_officer'

    def procurement_head(self):
        self.state = 'pro_head'

    def department_manager(self):
        self.state = 're_dep_manager'

    def secratry_general(self):
        self.state = 'secratry_general'

    #modify confirm order to include cba and secratry_general state
    def button_confirm(self):
        for order in self:
            if order.state not in ['draft', 'sent','cba','secratry_general','committee_minute']:
                print('_______________33')
                continue
            order._add_supplier_to_product()
            # Deal with double validation process
            if order._approval_allowed():
                print('_______________111111111')
                order.button_approve()
            else:
                order.write({'state': 'to approve'})
                print('_______________to')
            if order.partner_id not in order.message_partner_ids:
                print('_______________message')
                order.message_subscribe([order.partner_id.id])
        return True

    def action_quotaion_approve(self):
        if self.tender_type == 'rest_tender':
            if self.is_cba and not self.is_committee:
                print('_________________@222222222')
                self.state = 'cba'
            if self.is_committee and not self.is_cba:
                print('_________________@33333333')
                self.state = 'committee_minute'
            #to be overviewed
            if not self.is_cba and not self.is_committee:
                print('_________________@only one qutaion')
                self.button_confirm()
        if self.tender_type == 'publish_tender':
            if self.is_cba and self.is_committee:
                print('_________________@555555')
                self.state = 'tender_procedure'
        if self.tender_type == 'single_tender':
            self.button_confirm()

    def committee(self):
        self.state = 'committee_minute'

    def compatitive_bid_analysis(self):
        # if self.tender_type == 'publish_tender': 
        #     if self.is_cba and self.is_committee:    
        self.state = 'cba'

    def goods_receive_note(self):
        self.state = 'grn'

    def payment(self):
        #create invoice here
        self.action_create_invoice()
        self.state = 'payment'

    def receive_goods(self):
        self.state = 'receive_goods'

    # add fields to picking 
    def _prepare_picking(self):
        result = super(SrcsPurchase , self)._prepare_picking()
        result.update({
            'mean_transport': self.mean_transport,
            'arrival_date': self.arrival_date,
            'bill_leading': self.bill_leading,
            'vessel': self.vessel,
            'flight_number': self.flight_number,
            'truck_number': self.truck_number,
        })
        print('____________reuslt',result)
        return result

    @api.onchange('requisition_id')
    def _onchange_requisition_id(self):
        res = super(SrcsPurchase, self)._onchange_requisition_id()
        if self.requisition_id.is_restricted:
            print('________________restricted')
            self.tender_type = 'rest_tender' 
        if self.requisition_id.is_published:
            print('________________published')
            self.tender_type = 'publish_tender'
        if self.requisition_id.is_service:
            self.service = True
        self.purchase_request_id = self.requisition_id.purchase_request_id.id 
        self.currency_id = self.requisition_id.currency_id.id  
        print('______________res',res)
        return res

class SrcsOrderLine(models.Model):
    _inherit = "purchase.order.line"

    vendor_desc = fields.Char('Vendor Description')

    @api.depends('invoice_lines.move_id.state', 'invoice_lines.quantity', 'qty_received', 'product_uom_qty', 'order_id.state')
    def _compute_qty_invoiced(self):
        for line in self:
            # compute qty_invoiced
            qty = 0.0
            for inv_line in line._get_invoice_lines():
                if inv_line.move_id.state not in ['cancel']:
                    if inv_line.move_id.move_type == 'in_invoice':
                        qty += inv_line.product_uom_id._compute_quantity(inv_line.quantity, line.product_uom)
                    elif inv_line.move_id.move_type == 'in_refund':
                        qty -= inv_line.product_uom_id._compute_quantity(inv_line.quantity, line.product_uom)
            line.qty_invoiced = qty

            # compute qty_to_invoice
            if line.order_id.state in ['purchase', 'done','grn','cba','pro_officer','pro_head','re_dep_manager','secratry_general','tender_procedure','committee_minute','draft']:
                if line.product_id.purchase_method == 'purchase':
                    line.qty_to_invoice = line.product_qty - line.qty_invoiced
                else:
                    line.qty_to_invoice = line.qty_received - line.qty_invoiced
            else:
                line.qty_to_invoice = 0

class PurchaseRequest(models.Model):
    _name = 'purchase.request'
    _rec_name = 'sequence'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'A Model For Purchase Requests.'

    sequence = fields.Char(string='Sequence', readonly=True, copy=False, index=True,
                           default=lambda self: 'New Purchase Requestion')
    requester_id = fields.Many2one(comodel_name="res.users", string="Employee", required=True,
                                   default=lambda self: self.env.user)
    request_date = fields.Date(string="Request Date", required=False, default=fields.Date.today())
    department_id = fields.Many2one(comodel_name="hr.department", string="Department", required=False,
                                    related='requester_id.department_id', readonly=True)
    #approval informatiom
    program_coordinator = fields.Many2one("res.users", string="Program Coordinator", tracking=True, readonly=True)
    program_coordinator_date = fields.Date("Program Coordinator Date", tracking=True, readonly=True)
    department_user = fields.Many2one("res.users", string="Department User", tracking=True, readonly=True)
    department_date = fields.Date("Department Date", tracking=True, readonly=True)
    finance_user = fields.Many2one("res.users", string="Finance User", tracking=True, readonly=True)
    finance_date = fields.Date("Finance Date", tracking=True, readonly=True)
    secratry_general = fields.Many2one("res.users", string="Secretary General", tracking=True, readonly=True)
    secratry_general_date = fields.Date("Secretary General Date", tracking=True, readonly=True)
    procument_user = fields.Many2one("res.users", string="Procurement User", tracking=True, readonly=True)
    procument_date = fields.Date("procurement Date", tracking=True, readonly=True)
    supply_chain_user = fields.Many2one("res.users", string="Supply Chain User", tracking=True, readonly=True)
    supply_chain_date = fields.Date("Supply Chain Date", tracking=True, readonly=True)
    inventory_user = fields.Many2one("res.users", string="Inventory User", tracking=True, readonly=True)
    inventory_date = fields.Date("Inventory Date", tracking=True, readonly=True)
    purchase_order_id = fields.Many2one(comodel_name="purchase.order", string="Purchase Order", required=False, )
    partner_id = fields.Many2one(comodel_name="res.partner", string="Vendor", required=False, )
    state = fields.Selection(string="State",
                             selection=[('draft', 'Draft'), ('program_cordinator', 'Program Coordinator Approval'),
                                        ('department', 'Department'),('finance', 'Finance Confirmed'), 
                                        ('secratry_general','Secretary General'),('procument','Procurement Officer'),('pro','Procurement'),('agreement','Agreement'),
                                        ('supply_chain','Supply Chain Manager'), ('inventory','Inventory')],
                              default='draft', track_visibility='onchange')
    request_reason = fields.Text(string="Request Reason", required=False, )
    budget_currency = fields.Many2one(related='budget_line_id.currency_budget_line')
    currency_id = fields.Many2one('res.currency', string='Currency', required=True)
    account_id = fields.Many2one('account.account', string='Account', domain="[('internal_group','in',['expense','asset'])]")
    analytic_activity_id = fields.Many2one('account.analytic.account', 'Output/Activity', domain="[('type','=','activity')]")
    donor_id = fields.Many2one('res.partner', string='Donor')
    project_id = fields.Many2one('account.analytic.account',string='Project', domain="[('type','=','project')]")
    budget_line_id = fields.Many2one('crossovered.budget.lines', string='Budget Line', readonly=True, store=True)
    budget_limit = fields.Monetary('Budget Limit ', currency_field='budget_currency', readonly=True, store=True)
    purchase_request_line_ids = fields.One2many(comodel_name="purchase.request.line",
                                                inverse_name="purchase_request_id", string="", required=False, )
    purchase_order_ids = fields.One2many(comodel_name="purchase.order",
                                         inverse_name="purchase_request_id", string="", required=False, )
    is_single_source = fields.Boolean('Is Single Source Tender')
    partner_id = fields.Many2one('res.partner', string='Vendor')

    service = fields.Boolean('Service order')
    #new fields
    company_id = fields.Many2one('res.company', string='Company')
    mean_transport = fields.Selection([
        ('air', 'Air'), ('road', 'Road'), ('sea', 'Sea'), ('other', 'Other'),
    ], string='Mean of Transport')

    # #need to be checked
    # @api.constrains('total','purchase_request_line_ids')
    # def _check_total(self):
    #     print('hreeeeeeeeeeeeeeeeeeeeeeeeeeee',self.total)
    #     for record in self:
    #         # if self.currency_id:
    #         if record.currency_id == record.budget_line_id.currency_budget_line.id:
    #             if record.total > record.budget_limit:
    #                 print('_________________________________total',record.total)
    #                 raise ValidationError(_('Total Amount should be less than or equal to Budget Limit '))
    #
    #         else:
    #             print("\n\n\n\n\n\n\n\n")
    #             print("rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr")
    #             total_company_currency = 0
    #             budget_amount_company_currency = 0
    #             total_company_currency = record.total / record.currency_id.rate
    #             budget_amount_company_currency = record.budget_limit / record.budget_line_id.currency_budget_line.rate
    #             if total_company_currency > budget_amount_company_currency:
    #                 print('________________________________total_currency',budget_amount_company_currency)
    #                 raise ValidationError(_('Total Amount should be less than or equal to Budget Limit '))
    #
    count_rfq = fields.Integer(string="", required=False, compute='_get_count_rfq')

    def _get_count_rfq(self):
        count = self.env['purchase.order'].search_count([('purchase_request_id.id', '=', self.id)])
        self.count_rfq = count
    
    count_agreement = fields.Integer(string="", required=False, compute='_get_count_agreement')

    def _get_count_agreement(self):
        count = self.env['purchase.requisition'].search_count([('purchase_request_id.id', '=', self.id)])
        self.count_agreement = count

    total = fields.Monetary('Total', compute='_compute_total', default=0, currency_field='currency_id')

    @api.depends('purchase_request_line_ids.price_subtotal')
    def _compute_total(self):
        if self.purchase_request_line_ids:
            for line in self.purchase_request_line_ids:
                self.total += line.price_subtotal  
        else:
            self.total = 0

    @api.onchange('account_id','analytic_activity_id','donor_id','project_id')
    def _onchange_budget_line_id(self):
        for rec in self:
            if rec.account_id and rec.analytic_activity_id and rec.donor_id and rec.project_id:
                budget_line = self.env['crossovered.budget.lines'].search([('date_from','<=',rec.request_date),('date_to','>=',rec.request_date),
                                        ('crossovered_budget_id.donor_id','=',rec.donor_id.id),('crossovered_budget_id.state','=','validate'),
                                        ('analytic_activity_id','=',rec.analytic_activity_id.id),('analytic_account_id','=',rec.project_id.id),
                                        ('general_budget_id.account_ids','in', rec.account_id.id),])
                print('_________________budget line',budget_line)
                if budget_line:
                    # return{'domain':{'budget_line_id':[('id','in',budget_line)]}}
                    rec.budget_line_id = budget_line.id
                    rec.budget_limit = budget_line.balance_budget_currency
                else:
                    raise ValidationError(_('There is No Budget for this %s and %s and %s and %s')%(rec.account_id.name,rec.project_id.name,rec.analytic_activity_id.name,rec.donor_id.name))

    def action_program_cordinator(self):
        if not self.purchase_request_line_ids:
            raise UserError(_('Please Insert Products in lines'))
        self.write({'program_coordinator': self.env.user.id,
                    'program_coordinator_date': fields.Date.today(),
                    'state': 'program_cordinator'})

    def action_department(self):
        self.write({'department_user': self.env.user.id,
                    'department_date': fields.Date.today(),
                    'state': 'department'})
        
    def action_finance(self):
        if self.account_id and self.analytic_activity_id and self.donor_id and self.project_id:
            self.write({'finance_user': self.env.user.id,
                        'finance_date': fields.Date.today(),
                        'state': 'finance'})
        else:
            raise UserError(_('Please Insert Account and Activity and Donor and Project'))
    
    def action_secratry_general(self):
        self.write({'secratry_general': self.env.user.id,
                    'secratry_general_date': fields.Date.today(),
                    'state': 'secratry_general'})
    
    def action_procument(self):
        self.write({'procument_user': self.env.user.id,
                    'procument_date': fields.Date.today(),
                    'state': 'procument'})
  
    def action_approve(self):
        if self.account_id and self.analytic_activity_id and self.donor_id and self.project_id:
            vals = []
            available_products = []
            residual_total = 0
            
            for line in self.purchase_request_line_ids:
                if line.product_id.detailed_type == 'product':
                    if line.product_id.qty_available:
                        if len(self.purchase_request_line_ids) == 1:
                            self.write({'supply_chain_user': self.env.user.id,
                                'supply_chain_date': fields.Date.today(),
                                'state': 'supply_chain'})
                            print('__________________ddsdssssssssss')
                        # else:
                            # partially available 
                        #     raise ValidationError('%s is available in warehouse' % (line.product_id.name))
                    else:
                        
                        available_products.append(line)
                        residual_total += line.price_subtotal
                        print('_______________________________available_products',available_products,'________________\n \n \n ',residual_total)
            if not self.service:
                if len(available_products) > 0: 
                    print('_____________________________available_products \n \n \n ',available_products)
                    financial_limit = self.env['financial.limit'].search([('amount_from','<=',residual_total),('amount_to','>=',residual_total)])
                    
                        
                    if self.is_single_source == True:

                        for product in available_products:
                            vals.append((0, 0,
                                {'product_id': product.product_id.id,
                                'name': product.description,
                                'product_qty': product.product_qty,
                                'product_uom': product.product_uom.id,
                                'price_unit': product.price_unit,
                                'price_subtotal': product.price_subtotal,
                                }))
                        self.env['purchase.order'].create({
                            'partner_id': self.partner_id.id,
                            'tender_type':'single_tender',
                            'state':'draft',
                            'purchase_request_id': self.id,
                            'currency_id': self.currency_id.id,
                            'order_line': vals,
                        })
                        self.write({'state': 'pro'})
                        print('_______________________is single product',vals)
                    
                    else:
                        print('___________hrer')
                        if financial_limit:
                            print('_________',financial_limit)
                            # for limit in financial_limit:
                            if financial_limit.three_quotaions:
                                if financial_limit.munites_commitee and financial_limit.cba:
                                    for product in available_products:
                                        vals.append((0, 0,
                                            {'product_id': product.product_id.id,
                                            'product_qty': product.product_qty,
                                            'product_uom_id': product.product_uom.id,
                                            'price_unit': product.price_unit,
                                            }))
                                    self.env['purchase.requisition'].create({
                                        'purchase_request_id': self.id,
                                        'type_id':2,
                                        'is_published':True,
                                        'is_committee':True,
                                        'is_cba':True,
                                        'currency_id': self.currency_id.id,
                                        'line_ids': vals,
                                    })
                                    self.write({'state': 'agreement'})
                                    print('___________________________agreement cba and committee product',vals)
                                if financial_limit.cba and not financial_limit.munites_commitee:
                                    for product in available_products:
                                        vals.append((0, 0,
                                            {'product_id': product.product_id.id,
                                            'product_qty': product.product_qty,
                                            'product_uom_id': product.product_uom.id,
                                            'price_unit': product.price_unit,
                                            }))
                                    self.env['purchase.requisition'].create({
                                        'purchase_request_id': self.id,
                                        'type_id':2,
                                        'is_restricted': True,
                                        'is_cba':True,
                                        'currency_id': self.currency_id.id,
                                        'line_ids': vals,
                                    })
                                    self.write({'state': 'agreement'})
                                    print('___________________________agreement cba',vals)
                                if financial_limit.munites_commitee and not financial_limit.cba:
                                    for product in available_products:
                                        vals.append((0, 0,
                                            {'product_id': product.product_id.id,
                                            'product_qty': product.product_qty,
                                            'product_uom_id': product.product_uom.id,
                                            'price_unit': product.price_unit,
                                            }))
                                    self.env['purchase.requisition'].create({
                                        'purchase_request_id': self.id,
                                        'type_id':2,
                                        'is_restricted': True,
                                        'is_committee':True,
                                        'currency_id': self.currency_id.id,
                                        'line_ids': vals,
                                    })
                                    self.write({'state': 'agreement'})
                                    print('___________________________agreement committee',vals)

                            #to be overviewed
                            elif not financial_limit.three_quotaions:
                                for product in available_products:
                                    vals.append((0, 0,
                                            {'product_id': product.product_id.id,
                                            'product_qty': product.product_qty,
                                            'product_uom_id': product.product_uom.id,
                                            'price_unit': product.price_unit,
                                            }))
                                self.env['purchase.requisition'].create({
                                        'purchase_request_id': self.id,
                                        'one_quotaion':True,
                                        'type_id':1,
                                        'is_restricted': True,
                                        'currency_id': self.currency_id.id,
                                        'line_ids': vals,
                                    })
                                self.write({'state': 'agreement'})
                                print('___________________________only one quot',vals)
                        else:
                            for product in available_products:
                                vals.append((0, 0,
                                    {'product_id': product.product_id.id,
                                    'product_qty': product.product_qty,
                                    'product_uom_id': product.product_uom.id,
                                    'price_unit': product.price_unit,
                                    }))
                            self.env['purchase.requisition'].create({
                                'purchase_request_id': self.id,
                                'type_id':2,
                                'is_published':True,
                                'is_committee':True,
                                'is_cba':True,
                                # 'is_service':True,
                                'currency_id': self.currency_id.id,
                                'line_ids': vals,
                            })
                            self.write({'state': 'agreement'})
                            print('___________________________eslsssssssssagreement cba and committee',vals)

                    # else:
                    #     raise ValidationError(_('You have to enter financial limit'))        
            else:

                if self.is_single_source == True:
                    for service_line in self.purchase_request_line_ids:
                        vals.append((0, 0,
                            {'product_id': service_line.product_id.id,
                            'name': service_line.description,
                            'product_qty': service_line.product_qty,
                            'product_uom': service_line.product_uom.id,
                            'price_unit': service_line.price_unit,
                            'price_subtotal': service_line.price_subtotal,
                            }))
                    self.env['purchase.order'].create({
                        'partner_id': self.partner_id.id,
                        'tender_type':'single_tender',
                        'purchase_request_id': self.id,
                        'service':True,
                        'state':'draft',
                        'currency_id': self.currency_id.id,
                        'order_line': vals,
                    })
                    self.write({'state': 'pro'})
                    print('_______________________is single service',vals)
                else:
                    financial_limit_service = self.env['financial.limit'].search([('amount_from','<=', self.total),('amount_to','>=',self.total)])
                    if financial_limit_service:
                        print('_________',financial_limit_service)
                        
                        if financial_limit_service.three_quotaions:
                            if financial_limit_service.munites_commitee and financial_limit_service.cba:
                                for service_line in self.purchase_request_line_ids:
                                    vals.append((0, 0,
                                        {'product_id': service_line.product_id.id,
                                        'product_qty': service_line.product_qty,
                                        'product_uom_id': service_line.product_uom.id,
                                        'price_unit': service_line.price_unit,
                                        }))
                                self.env['purchase.requisition'].create({
                                    'purchase_request_id': self.id,
                                    'type_id':2,
                                    'is_published':True,
                                    'is_committee':True,
                                    'is_cba':True,
                                    'is_service':True,
                                    'currency_id': self.currency_id.id,
                                    'line_ids': vals,
                                })
                                self.write({'state': 'agreement'})
                                print('___________________________agreement cba and committee service',vals)
                            if financial_limit_service.cba and not financial_limit_service.munites_commitee:
                                for service_line in self.purchase_request_line_ids:
                                    vals.append((0, 0,
                                        {'product_id': service_line.product_id.id,
                                        'product_qty': service_line.product_qty,
                                        'product_uom_id': service_line.product_uom.id,
                                        'price_unit': service_line.price_unit,
                                        }))
                                self.env['purchase.requisition'].create({
                                    'purchase_request_id': self.id,
                                    'type_id':2,
                                    'is_restricted': True,
                                    'is_cba':True,
                                    'currency_id': self.currency_id.id,
                                    'is_service':True,
                                    'line_ids': vals,
                                })
                                self.write({'state': 'agreement'})
                                print('___________________________agreement cba',vals)
                            if financial_limit_service.munites_commitee and not financial_limit_service.cba:
                                for service_line in self.purchase_request_line_ids:
                                    vals.append((0, 0,
                                        {'product_id': service_line.product_id.id,
                                        'product_qty': service_line.product_qty,
                                        'product_uom_id': service_line.product_uom.id,
                                        'price_unit': service_line.price_unit,
                                        }))
                                self.env['purchase.requisition'].create({
                                    'purchase_request_id': self.id,
                                    'type_id':2,
                                    'is_restricted': True,
                                    'is_committee':True,
                                    'is_service':True,
                                    'currency_id': self.currency_id.id,
                                    'line_ids': vals,
                                })
                                self.write({'state': 'agreement'})
                                print('___________________________agreement committee',vals)
                        #to be overviewed
                        elif not financial_limit_service.three_quotaions:
                            for service_line in self.purchase_request_line_ids:
                                vals.append((0, 0,
                                        {'product_id': service_line.product_id.id,
                                        'product_qty': service_line.product_qty,
                                        'product_uom_id': service_line.product_uom.id,
                                        'price_unit': service_line.price_unit,
                                        }))
                            self.env['purchase.requisition'].create({
                                'purchase_request_id': self.id,
                                'one_quotaion':True,
                                'type_id':1,
                                'is_restricted': True,
                                'is_service':True,
                                'currency_id': self.currency_id.id,
                                'line_ids': vals,
                            })
                            self.write({'state': 'pro'})
                            print('___________________________only one quot service',vals)
                    else:
                        print('________________last',)
                        for service_line in self.purchase_request_line_ids:
                            vals.append((0, 0,
                                {'product_id': service_line.product_id.id,
                                'product_qty': service_line.product_qty,
                                'product_uom_id': service_line.product_uom.id,
                                'price_unit': service_line.price_unit,
                                }))
                        self.env['purchase.requisition'].create({
                            'purchase_request_id': self.id,
                            'type_id':2,
                            'is_published':True,
                            'is_committee':True,
                            'is_cba':True,
                            'is_service':True,
                            'currency_id': self.currency_id.id,
                            'line_ids': vals,
                        })
                        self.write({'state': 'agreement'})
                        print('___________________________serviceeslsssssssssagreement cba and committee',vals)
                    # else:
                    #         raise ValidationError(_('You have to enter financial limit'))        
                        
                                            
        else:
            raise UserError(_('Please Insert Account and Activity and Donor and Project'))



    
    def action_inventory(self):
        self.write({'inventory_user': self.env.user.id,
                    'inventory_date': fields.Date.today(),
                    'state': 'inventory'})
    
    def get_rfq(self):
        return {
            'name': _('Purchase Orders'),
            'domain': [('purchase_request_id', '=', self.id)],
            'view_type': 'form',
            'res_model': 'purchase.order',
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
            'context': "{'create': False}",
        }

    def get_agreement(self):
        return {
            'name': _('Purchase Agreement'),
            'domain': [('purchase_request_id', '=', self.id)],
            'view_type': 'form',
            'res_model': 'purchase.requisition',
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
            'context': "{'create': False}",
        }
        
    def action_reset_to_draft(self):
        count_order = self.env['purchase.order'].search([('purchase_request_id.id', '=', self.id)])
        count_agreement = self.env['purchase.requisition'].search([('purchase_request_id.id', '=', self.id)])
        if count_order:
            for order in count_order:
                order.button_cancel()
            count_order.unlink() 
            print('_________orderlink')
        if count_agreement:
            print("***************************",count_agreement)
            for agree in count_agreement:
                agree.action_draft()
            count_agreement.unlink() 
            print('_________agreementlink')
        self.state = "draft"

    @api.onchange('requester_id')
    def get_department(self):
        if self.requester_id:
            self.department_id = self.requester_id.department_id.id

    
    @api.model
    def create(self, vals):
        if vals.get('sequence', 'NEW') == 'NEW':
            vals['sequence'] = self.env['ir.sequence'].next_by_code('purchase.request') or 'NEW'
        result = super(PurchaseRequest, self).create(vals)
        return result

           
class PurchaseRequstLine(models.Model):
    _name = "purchase.request.line"

    purchase_request_id = fields.Many2one(comodel_name="purchase.request", string="", required=False, )
    description = fields.Text(string='Description', required=True)
    price_unit = fields.Float(string='Unit Price', required=True, digits='Product Price')
    currency_id = fields.Many2one(related='purchase_request_id.currency_id', store=True, string='Currency', readonly=True)
    product_id = fields.Many2one('product.product', string='Product', domain=[('purchase_ok', '=', True)], required=False, )
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure',related='product_id.uom_id', domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')
    product_qty = fields.Float(string="Quantity", required=False, )
    remark = fields.Char(string="Remarks", required=False, )
    # product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')
    price_unit = fields.Float(string='Unit Price', required=True, digits='Product Price')
    price_subtotal = fields.Monetary(string='Subtotal', store=True)

    @api.onchange('product_id')
    def get_description(self):
        for rec in self:
            if rec.product_id:
                rec.description = rec.product_id.name
                rec.price_unit = rec.product_id.standard_price
                
    @api.onchange('price_unit','product_qty')
    def get_subtotal(self):
        if self.product_id:
            self.price_subtotal = self.price_unit * self.product_qty
            
    @api.onchange('purchase_request_id.service','product_id')
    def _onchange_service(self):
        if self.purchase_request_id.service:
            service_item = self.env['product.product'].search([('detailed_type','in',['service','consu'])]).ids
            if service_item:
                print('________________________________________________rec service',service_item)
                return {'domain':{'product_id':[('id','in',service_item)]}}
        else:
            product_item = self.env['product.product'].search([('detailed_type','=','product')]).ids
            if product_item:
                print('________________________________________________rec product_item',product_item)
                return {'domain':{'product_id':[('id','in',product_item)]}}

class SrcsAgreement(models.Model):
    _inherit = "purchase.requisition"

    purchase_request_id = fields.Many2one(comodel_name="purchase.request", string="", required=False, ) 
    committee_ids = fields.One2many('committee.member','requisition_id', string='Committee Members')
    is_committee = fields.Boolean('Is Committee')
    is_cba = fields.Boolean('CBA(Comparative bid analysis)')
    one_quotaion = fields.Boolean('One Quotation')
    is_restricted = fields.Boolean('Is Restricted')
    is_published = fields.Boolean('Is Published')
    is_service = fields.Boolean('Is Service')
    # mean_transport = fields.Selection([('air', 'Air'),('road','Road'),('sea','Sea'),('other','Other')], string='Mean of Transport')
    
class SrcsCommitteeMember(models.Model):
    _name = "committee.member"
    _rec_name = "job_id"

    requisition_id = fields.Many2one(comodel_name="purchase.requisition", string="Agreement", required=False, ) 
    employee_id = fields.Many2one('hr.employee', string='Member')
    job_id = fields.Many2one('hr.job', string='Job Position',related="employee_id.job_id", readonly=False)
    company_id = fields.Many2one('res.company', string='company', default=lambda self:self.env.company.id)

class RESPARTNER(models.Model):
    _inherit = "res.partner"

    fax = fields.Char(string="Fax")

class RESCompany(models.Model):
    _inherit = "res.company"

    fax = fields.Char(string="Fax")
