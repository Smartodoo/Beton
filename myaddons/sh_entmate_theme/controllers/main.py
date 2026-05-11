# Part of Softhealer Technologies.
import json
from odoo import http
import base64
from io import BytesIO
from odoo.tools.misc import file_open
from datetime import datetime
from odoo.tools.safe_eval import safe_eval
from odoo.http import request, route, Controller


class todo(Controller):
    @route('/todo/get_all', type='json', auth='public', methods=['POST'])
    def todo_get_all(self, name, rec, is_done):
        html = request.env['ir.ui.view']._render_template('sh_entmate_theme.todo_card',
                                           {'name': name, 'rec': rec, 'is_done': is_done})
        return html


class Main(http.Controller):
    @http.route('/get_theme_style', type='json', auth="public")
    def get_theme_style(self):
        theme_setting_rec = request.env['sh.ent.theme.config.settings'].sudo().search([
            ('id', '=', 1)], limit=1)

        return {
                'theme_style': theme_setting_rec.theme_style,
                'sidebar_bg_color': theme_setting_rec.sidebar_color,
                'sidebar_font_color': theme_setting_rec.sidebar_font_color,
                'sidebar_img': theme_setting_rec.sidebar_img,
                'primary_color': theme_setting_rec.primary_color,
                'secondary_color': theme_setting_rec.secondary_color,
                'extra_color': theme_setting_rec.extra_color,
                'header_background_type': theme_setting_rec.header_background_type,
                'header_background_color': theme_setting_rec.header_background_color,
                'header_background_image': theme_setting_rec.header_background_image,
                'header_font_color': theme_setting_rec.header_font_color,
                'body_background_type': theme_setting_rec.body_background_type,
                'body_background_color': theme_setting_rec.body_background_color,
                'body_background_image': theme_setting_rec.body_background_image,
                'body_font_family': theme_setting_rec.body_font_family,
                'body_google_font_family': theme_setting_rec.body_google_font_family,
                'separator_style': theme_setting_rec.separator_style,
                'separator_color': theme_setting_rec.separator_color,
                'button_style': theme_setting_rec.button_style,
                'app_icon_style': theme_setting_rec.app_icon_style,
                'is_sticky_form': theme_setting_rec.is_sticky_form,
                'is_sticky_list': theme_setting_rec.is_sticky_list,
                'is_sticky_list_inside_form': theme_setting_rec.is_sticky_list_inside_form,
                'is_sticky_pivot': theme_setting_rec.is_sticky_pivot,
                'tab_style':theme_setting_rec.horizontal_tab_style,
                'predefined_list_view_boolean': theme_setting_rec.predefined_list_view_boolean,
                'predefined_list_view_style': theme_setting_rec.predefined_list_view_style,
                'list_view_border': theme_setting_rec.list_view_border,
                'list_view_even_row_color': theme_setting_rec.list_view_even_row_color,
                'list_view_odd_row_color': theme_setting_rec.list_view_odd_row_color,
                'list_view_is_hover_row': theme_setting_rec.list_view_is_hover_row,
                'list_view_hover_bg_color': theme_setting_rec.list_view_hover_bg_color,
                'login_page_style': theme_setting_rec.login_page_style,
                'login_page_background_type': theme_setting_rec.login_page_background_type,
                'login_page_background_color': theme_setting_rec.login_page_background_color,
                'login_page_box_color': theme_setting_rec.login_page_box_color,
                'progress_style': theme_setting_rec.progress_style,
                'progress_height': theme_setting_rec.progress_height,
                'progress_color': theme_setting_rec.progress_color,
                'form_element_style': theme_setting_rec.form_element_style,
                'breadcrumb_style': theme_setting_rec.breadcrumb_style,
                'checkbox_style': theme_setting_rec.checkbox_style,
                'radio_style': theme_setting_rec.radio_style,
                'scrollbar_style': theme_setting_rec.scrollbar_style,
                'kanban_box_style': theme_setting_rec.kanban_box_style,
                'backend_all_icon_style': theme_setting_rec.backend_all_icon_style,
        }

    @http.route('/api/upload/multi', type='http', auth="none", csrf=False)
    def Upload_image(self, **kwargs):

        theme_setting_rec = request.env['sh.ent.theme.config.settings'].sudo().search([
            ('id', '=', 1)], limit=1)

        if kwargs.get('body_background_img'):
            body_background_img = base64.b64encode(
                kwargs.get('body_background_img').read())
            if theme_setting_rec:
                theme_setting_rec.write(
                    {'body_background_image': body_background_img})

        if kwargs.get('header_background_img'):
            body_background_img = base64.b64encode(
                kwargs.get('header_background_img').read())
            if theme_setting_rec:
                theme_setting_rec.write(
                    {'header_background_image': body_background_img})

        if kwargs.get('login_page_background_img'):
            login_page_background_image = base64.b64encode(
                kwargs.get('login_page_background_img').read())
            if login_page_background_image:
                theme_setting_rec.write(
                    {'login_page_background_image': login_page_background_image})

        return json.dumps({})

    @http.route('/firebase-messaging-sw.js', type='http', auth="public")
    def sw_http(self):
        if request.env.company and request.env.company.enable_web_push_notification:
            config_obj = request.env.company.config_details
            
            js = """
            this.addEventListener('install', function(e) {
         e.waitUntil(
           caches.open('video-store').then(function(cache) {
             return cache.addAll([
                 '/sh_entmate_theme/static/index.js'
             ]);
           })
         );
        });
        
        this.addEventListener('fetch', function(e) {
          e.respondWith(
            caches.match(e.request).then(function(response) {
              return response || fetch(e.request);
            })
          );
        });
            importScripts('https://www.gstatic.com/firebasejs/8.4.2/firebase-app.js');
            importScripts('https://www.gstatic.com/firebasejs/8.4.2/firebase-messaging.js');
            var firebaseConfig =
            """+ config_obj +""" ;
            firebase.initializeApp(firebaseConfig);
    
            const messaging = firebase.messaging();
    
            messaging.setBackgroundMessageHandler(function(payload) {
            const notificationTitle = "Background Message Title";
            const notificationOptions = {
                body: payload.notification.body,
                icon:'https://i.pinimg.com/originals/3f/77/56/3f7756330cd418e46e642254a900a507.jpg',
            };
            return self.registration.showNotification(
                notificationTitle,
                notificationOptions,
            );
            });
    
            """
            return http.request.make_response(js, [('Content-Type', 'text/javascript')])
        else:
            
            js = """
           this.addEventListener('install', function(e) {
         e.waitUntil(
           caches.open('video-store').then(function(cache) {
             return cache.addAll([
                 '/sh_entmate_theme/static/index.js'
             ]);
           })
         );
        });
        
        this.addEventListener('fetch', function(e) {
          e.respondWith(
            caches.match(e.request).then(function(response) {
              return response || fetch(e.request);
            })
          );
        });
    
            """
            return http.request.make_response(js, [('Content-Type', 'text/javascript')])
        
    @http.route('/web/push_token', type='http', auth="public", csrf=False)
    def getToken(self,**post):
        device_search = request.env['sh.push.notification'].sudo().search(
            [('register_id', '=', post.get('name'))], limit=1)
        
        if device_search and not request.env.user._is_public() and device_search.user_id != request.env.user.id:
            if request.env.user.has_group('base.group_portal'):
                device_search.write({'user_id':request.env.user.id,'user_type':'portal'})
            elif request.env.user:
                device_search.write({'user_id':request.env.user.id,'user_type':'internal'})
                
        if not device_search:
            vals = {
                'register_id' : post.get('name'),
                'datetime' : datetime.now()
            }
            if request.env.user._is_public():
                public_users = request.env['res.users'].sudo()
                public_groups = request.env.ref("base.group_public", raise_if_not_found=False)
                if public_groups:
                    public_users = public_groups.sudo().with_context(active_test=False).mapped("users")
                    if public_users:
                        vals.update({'user_id':public_users[0].id,'user_type':'public'})
            elif request.env.user.has_group('base.group_portal'):
                vals.update({'user_id':request.env.user.id,'user_type':'portal'})
            elif request.env.user:
                vals.update({'user_id':request.env.user.id,'user_type':'internal'})
            
            request.env['sh.push.notification'].sudo().create(vals)

    @http.route('/web/_config', type='json', auth="public")
    def sendConfig(self):

        config_vals = {}
        if request.env.company and request.env.company.enable_web_push_notification:

            config_obj = request.env.company.config_details.replace(" ","")
            config_obj = request.env.company.config_details.replace("\n","").replace("\t","").replace(" ","").replace("\"","'").replace('apiKey','\'apiKey\'').replace('authDomain','\'authDomain\'').replace('projectId','\'projectId\'').replace('storageBucket','\'storageBucket\'').replace('messagingSenderId','\'messagingSenderId\'').replace('appId','\'appId\'').replace('measurementId','\'measurementId\'')

            config_vals['apiKey'] = safe_eval(config_obj)['apiKey']
            config_vals['authDomain'] =  safe_eval(config_obj)['authDomain']
            config_vals['projectId'] =  safe_eval(config_obj)['projectId']
            config_vals['storageBucket'] =  safe_eval(config_obj)['storageBucket']
            config_vals['messagingSenderId'] = safe_eval(config_obj)['messagingSenderId']
            config_vals['appId'] = safe_eval(config_obj)['appId']
            config_vals['measurementId'] =  safe_eval(config_obj)['measurementId']
            
            vals = {
                'vapid' : request.env.company.vapid,
                'config':   config_vals
            }
            json_vals = json.dumps(vals)
            return json_vals
    
    # MULTI TAB START
    @http.route(['/add/mutli/tab'], type='json', auth='public')
    def add_multi_tab(self, **kw):
        user = request.env.user

        multi_tab_ids = user.multi_tab_ids.filtered(
            lambda mt: mt.name == kw.get('name'))
        if not multi_tab_ids:
            user.sudo().write({
                'multi_tab_ids': [(0, 0,  {
                    'name': kw.get('name'),
                    'url': kw.get('url'),
                    'actionId': kw.get('actionId'),
                    'menuId': kw.get('menuId'),
                    'menu_xmlid': kw.get('menu_xmlid'),
                })]
            })

        return True

    @http.route(['/get/mutli/tab'], type='json', auth='public')
    def get_multi_tab(self, **kw):
        obj = request.env['biz.multi.tab']
        user = request.env.user
        if user.multi_tab_ids:
            record_dict = user.multi_tab_ids.sudo().read(set(obj._fields))
            return record_dict
        else:
            return False

    @http.route(['/remove/multi/tab'], type='json', auth='public')
    def remove_multi_tab(self, **kw):
        multi_tab = request.env['biz.multi.tab'].sudo().search(
            [('id', '=', kw.get('multi_tab_id'))])
        multi_tab.unlink()
        user = request.env.user
        multi_tab_count = len(user.multi_tab_ids)
        values = {
            'removeTab': True,
            'multi_tab_count': multi_tab_count,
        }
        return values

    @http.route(['/update/tab/details'], type='json', auth='public')
    def update_tabaction(self, **kw):
        tabId = kw.get('tabId')
        TabTitle = kw.get('TabTitle')
        url = kw.get('url')
        ActionId = kw.get('ActionId')
        menu_xmlid = kw.get('menu_xmlid')

        multi_tab = request.env['biz.multi.tab'].sudo().search(
            [('id', '=', tabId)])
        if multi_tab:
            multi_tab.sudo().write({
                'name': TabTitle or multi_tab.name,
                'url': url or multi_tab.url,
                'actionId': ActionId or multi_tab.ActionId,
                'menu_xmlid': menu_xmlid or multi_tab.menu_xmlid,
            })
        return True
    # MULTI TAB END
