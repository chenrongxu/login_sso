
from odoo import models, fields

class ResCompany(models.Model):

    _inherit = 'res.company'

    secret = fields.Char('SSO秘钥')