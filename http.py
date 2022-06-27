import json
import logging
from odoo import registry as registry_get,SUPERUSER_ID, api
from odoo.http import Root

ori_get_request = Root.get_request

_logger = logging.getLogger(__name__)

def get_request(self, httprequest):
    db = httprequest.session.db
    data = httprequest.data
    uid = httprequest.session.uid
    ip_address = httprequest.environ['REMOTE_ADDR']

    if db and data and uid:
        action_id = json.loads(data).get('params', {'action_id': -1}).get('action_id')
        if action_id:
            registry = registry_get(db)
            with registry.cursor() as cr:
                try:
                    env = api.Environment(cr, 2, {})
                    action_name = env['ir.actions.actions'].sudo().search_read([('id','=',action_id)],['name','type'])
                    menu = env['ir.ui.menu'].sudo().search([('action', '=', '%s,%s' % (action_name[0]['type'],action_name[0]['id']))])
                    _logger.info(menu)
                    user_name = env['res.users'].search_read([('id', '=', uid)], ['login','name'])
                    employee = env['hr.employee'].sudo().search([('permit_no', '=', user_name[0]['login'])])
                    env['login.detail'].sudo().create({
                        'name': user_name[0]['name'],
                        'ip_address': ip_address,
                        'menu_name': action_name[0]['name'] if not menu else menu[0].complete_name,
                        #'menu_name': menu[0].complete_name if menu else '',
                        'dept': employee.department_id.name if employee else ''
                    })
                    cr.commit()
                except Exception as e:
                    raise e

    return ori_get_request(self, httprequest)

Root.get_request = get_request