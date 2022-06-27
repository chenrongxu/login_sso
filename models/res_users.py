import hashlib

from passlib.context import CryptContext
from werkzeug import security

from odoo import models, fields, api
from odoo.exceptions import AccessDenied
from odoo.http import request


class ResUsers(models.Model):

    _inherit = 'res.users'

    oauth_access_token = fields.Char(string='OAuth Access Token', readonly=True, copy=False)

    @api.model
    def create(self, vals):
        vals['name'] = vals['name'].strip()
        return super(ResUsers, self).create(vals)

    @api.model
    def auth_oauth(self, userid, timestamp, token):

        uid = self._auth_oauth_signin(userid, timestamp)
        if not uid:
            raise AccessDenied()
        # return user credentials
        return (self.env.cr.dbname, userid, token)


        #if not user:
         #  return self._crypt_context().encrypt(user.oauth_id + params)

    @api.model
    def _auth_oauth_signin(self, userid, timestamp):
        secret = self.env['ir.config_parameter'].sudo().get_param('app_secret')
        try:
            oauth_user = self.search([("login", "=", userid)])
            if not oauth_user:
                raise AccessDenied()
            assert len(oauth_user) == 1
            access_token = oauth_user.get_encrypt_token(secret + ':' + userid + ':' + timestamp + ':qis')
            oauth_user.write({ 'oauth_access_token': access_token })
            return oauth_user.id
        except AccessDenied as access_denied_exception:
            raise access_denied_exception

    @api.model
    def _check_credentials(self, password):
        try:
            result = super(ResUsers, self)._check_credentials(password)
            return result
        except AccessDenied:
            res = self.sudo().search([('id', '=', self.env.uid), ('oauth_access_token', '=', password)])
            if not res:
                raise
            ip_address = request.httprequest.environ['REMOTE_ADDR']
            employee = self.env['hr.employee'].sudo().search([('permit_no', '=', res.login)])
            vals = {'name': self.name,
                    'ip_address': ip_address,
                    'menu_name': 'sso',
                    'dept': employee.department_id.name if employee else ''
                    }
            self.env['login.detail'].sudo().create(vals)

    def get_encrypt_token(self, token):
        #return self._crypt_context().encrypt(token)
        sha256 = hashlib.sha256()
        sha256.update(token.encode())
        return sha256.hexdigest()