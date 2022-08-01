{
    'name': "SRCS Purchase",

    'summary': """
        """,

    'description': """
    """,
    'version': '15.0',
    'author': "IATL International",
    'website': "http://www.iatl-sd.com",
    # 'category': 'Accounting/Common',
    'depends': ['purchase', 'purchase_requisition', 'hr', 'accounting_srcs', 'base', 'stock'],
    'data': [
            'security/ir.model.access.csv',
            'security/srcs_security.xml',
            'data/seq.xml',
            'views/srcs_purchase.xml',
            'views/srcs_requestion.xml',
            # 'views/srcs_stock.xml',
            'views/finacial_limit.xml',
            # 'views/product.xml',
            'reports/quotation.xml',
            'reports/requisition.xml',
            'reports/contract.xml',
    ],
}