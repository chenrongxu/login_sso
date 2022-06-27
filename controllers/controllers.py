# -*- coding: utf-8 -*-
import logging
import werkzeug
from odoo import SUPERUSER_ID, api, http, _
from odoo import registry as registry_get
from odoo.addons.web.controllers.main import (login_and_redirect, ensure_db, set_cookie_and_redirect)
from odoo.exceptions import AccessDenied

_logger = logging.getLogger(__name__)


class SSOController(http.Controller):
    @http.route('/web/sso/signin', type='http', auth='none')
    def signin(self, redirect=None, **kwargs):
        login = kwargs.get('userid', False)
        timestamp = kwargs.get('timestamp', False)
        ssoToken = kwargs.get('ssoToken', False)
        dbname = kwargs.get('dbname', 'qis')
        registry = registry_get(dbname)
        with registry.cursor() as cr:
            try:
                env = api.Environment(cr, SUPERUSER_ID, {})
                credentials = env['res.users'].sudo().auth_oauth(login, timestamp, ssoToken)
                cr.commit()
                resp = login_and_redirect(*credentials, redirect_url='/web')
                return resp
            except AttributeError:
                # auth_signup is not installed
                _logger.error("auth_signup not installed on database %s: oauth sign up cancelled." % (dbname,))
                url = "/web/login?oauth_error=1"
            except AccessDenied:
                # oauth credentials not valid, user could be on a temporary session
                _logger.info(
                    'OAuth2: access denied, redirect to main page in case a valid session exists, without setting cookies')
                url = "/web/login?oauth_error=3"
                redirect = werkzeug.utils.redirect(url, 303)
                redirect.autocorrect_location_header = False
                return redirect
            except Exception as e:
                # signup error
                _logger.exception("OAuth2: %s" % str(e))
                url = "/web/login?oauth_error=2"

        return set_cookie_and_redirect(url)
