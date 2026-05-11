# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
{
    "name": "EnterpriseMate Backend Theme [For Community Edition]",
    "author": "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",
    "license": "OPL-1",
    "category": "Themes/Backend",
    "version": "0.0.3",
    "summary": "Enterprise Backend Theme, Enterprise Theme, Backend Enterprise Theme, Flexible Enterprise Theme, Enter prise Theme Odoo",
    "description": """Do you want odoo enterpise look in your community version? Are You looking for modern, creative, clean, clear, materialise odoo enterpise look theme for your backend? So you are at the right place, We have made sure that this theme is highly clean, modern, fully customizable enterprise look theme. Cheers!""",
    "depends":
    [
        "web",
        "mail"
    ],

    "data":
    [
        "data/theme_config_data.xml",
        "security/base_security.xml",
        "security/ir.model.access.csv",
        "views/views.xml",
        "views/assets.xml",
        "views/login_layout.xml",
        "views/notifications_view.xml",
        "views/send_notifications.xml",
        "views/web_push_notification.xml",
        "views/ent_theme_config_view.xml",
        "views/global_search_view.xml",
        "wizard/theme_preview_wizard.xml",
    ],

    'assets': {

        'web.assets_backend': [

            # header // 
            "sh_entmate_theme/static/src/scss/header/header.scss",

            # sidebar styles // 
            "sh_entmate_theme/static/src/scss/sidebar/sidebar.scss",


            'sh_entmate_theme/static/src/scss/font_family/fonts.scss',

            #common style
            'sh_entmate_theme/static/src/scss/common/common.scss',

            #button_style
            'sh_entmate_theme/static/src/scss/buttons/buttons.scss',

            # background type color/image
            'sh_entmate_theme/static/src/scss/background_style/background_style.scss',

            # separator
            'sh_entmate_theme/static/src/scss/separator/separator.scss',


            # responsive
            'sh_entmate_theme/static/src/scss/responsive.scss',


            # form element style
            'sh_entmate_theme/static/src/scss/form_element_style/form_element_style.scss',


            # notification style
            'sh_entmate_theme/static/src/scss/notification/notification.scss',

            # breadcrumb style
            'sh_entmate_theme/static/src/scss/breadcrumb/breadcrumb.scss',

            # night mode scss 
            'sh_entmate_theme/static/src/scss/entmate_night_mode/entmate_night_mode.scss',

            # checkbox style
            'sh_entmate_theme/static/src/scss/checkbox_style/checkbox_style.scss',

            # radio button style
            'sh_entmate_theme/static/src/scss/radio_btn_style/radio_btn_style.scss',

            # scrollbar style
            'sh_entmate_theme/static/src/scss/scrollbar/scrollbar_style.scss',

            # predefined list view style
            'sh_entmate_theme/static/src/scss/list_view/list_view.scss',

            # icon_style
            'sh_entmate_theme/static/src/scss/fontawesome_icon/font_awesome_light_icon.scss',
            'sh_entmate_theme/static/src/scss/fontawesome_icon/font_awesome_regular_icon.scss',
            'sh_entmate_theme/static/src/scss/fontawesome_icon/font_awesome_std_icon.scss',
            'sh_entmate_theme/static/src/scss/fontawesome_icon/font_awesome_thin_icon.scss',
            "sh_entmate_theme/static/src/scss/odoo_oi_icon/oi_light_icon.scss",
            "sh_entmate_theme/static/src/scss/odoo_oi_icon/oi_regular_icon.scss",
            "sh_entmate_theme/static/src/scss/odoo_oi_icon/oi_thin_icon.scss",
            # App icon styles //
            'sh_entmate_theme/static/src/scss/app_icon_style/app_icon_style.scss',


            # progressbar
            'sh_entmate_theme/static/src/scss/nprogress.scss',


            "sh_entmate_theme/static/src/xml/theme_config.xml",
            # theme config panel design
            "sh_entmate_theme/static/src/scss/theme_config.scss",


            'sh_entmate_theme/static/src/js/menu_service.js',

            # Menu Structure
            "sh_entmate_theme/static/src/xml/menu.xml",
            'sh_entmate_theme/static/src/js/navbar.js',

            # # Odoo standard js
            # 'sh_entmate_theme/static/src/js/route_service.js',
            # 'sh_entmate_theme/static/src/js/action_service.js',
            'sh_entmate_theme/static/src/js/dropdown.js',

            # # On refresh custom js
            "sh_entmate_theme/static/src/js/On_refresh.js",

            # # Refresh Feature
            "sh_entmate_theme/static/src/js/kanban_controller.js",
            'sh_entmate_theme/static/src/js/list_controller.js',
            'sh_entmate_theme/static/src/js/calendar_controller.js',
            "sh_entmate_theme/static/src/xml/refresh.xml",
            'sh_entmate_theme/static/src/scss/refresh_page/refresh_page.scss',

            # # Quick Menu Feature
            'sh_entmate_theme/static/src/js/quick_menu_custom.js',
            "sh_entmate_theme/static/src/xml/web_quick_menu.xml",
            'sh_entmate_theme/static/src/scss/quick_menu/quick_menu.scss',

            # # Calculator
            'sh_entmate_theme/static/src/js/calculator_custom.js',
            "sh_entmate_theme/static/src/xml/Calculator.xml",
            'sh_entmate_theme/static/src/scss/calculator/calculator.scss',


            # # Language
            'sh_entmate_theme/static/src/js/language_selector_custom.js',
            "sh_entmate_theme/static/src/xml/Language.xml",
            'sh_entmate_theme/static/src/scss/language_selector/language_selector.scss',

            # # Todo feature
            "sh_entmate_theme/static/src/js/todo_widget_custom.js",
            'sh_entmate_theme/static/src/js/todo_custom.js',
            "sh_entmate_theme/static/src/xml/todo.xml",
            "sh_entmate_theme/static/src/xml/todo_card.xml",
            'sh_entmate_theme/static/src/scss/todo/todo.scss',

            # # Global Search TODO
            'sh_entmate_theme/static/src/js/global_search_fronted.js',
            'sh_entmate_theme/static/src/scss/global_search/global_search.scss',
            "sh_entmate_theme/static/src/xml/global_search.xml",

            # # Zoom Widget
            "sh_entmate_theme/static/src/webclient/web_client.js",
            "sh_entmate_theme/static/src/webclient/zoomwidget/zoomwidget_custom.js",
            "sh_entmate_theme/static/src/webclient/user_menu_items.js",
            "sh_entmate_theme/static/src/xml/Zoom.xml",
            'sh_entmate_theme/static/src/scss/zoom_in_out/zoom_in_out.scss',

            # # Night Mode
            'sh_entmate_theme/static/src/js/night_mode_custom.js',
            "sh_entmate_theme/static/src/xml/NightMode.xml",

            # # Sticky
            'sh_entmate_theme/static/src/scss/sticky/sticky_form.scss',
            'sh_entmate_theme/static/src/scss/sticky/sticky_list_inside_form.scss',
            'sh_entmate_theme/static/src/scss/sticky/sticky_list.scss',
            'sh_entmate_theme/static/src/scss/sticky/sticky_pivot.scss',
            'sh_entmate_theme/static/src/js/pivot_view_sticky/pivot_sticky_dropdown.js',

            # # Firebase  and bus Notification
            'https://www.gstatic.com/firebasejs/8.4.3/firebase-app.js',
            'https://www.gstatic.com/firebasejs/8.4.3/firebase-messaging.js',
            "sh_entmate_theme/static/src/js/firebase.js",
            "sh_entmate_theme/static/src/xml/notification.xml",

            #
            # # Horizontal/vertical Tab
            'sh_entmate_theme/static/src/scss/tab/tab.scss',
            #
            # # Discuss Chatter
            'sh_entmate_theme/static/src/components/message/message.js',
            "sh_entmate_theme/static/src/xml/message.xml",

            # # Multi Tab
            'sh_entmate_theme/static/src/webclient/navtab/navtab.js',
            "sh_entmate_theme/static/src/xml/navbar.xml",
            'sh_entmate_theme/static/src/scss/multi_tab_at_control_panel/multi_tab.scss',
            'sh_entmate_theme/static/src/webclient/action_container.js',
            # 'sh_entmate_theme/static/src/js/owl.carousel.js',

            # kanban view style 

            'sh_entmate_theme/static/src/scss/kanban_view_style/kanban_view_style.scss',



            # # Disable Auto edit feature
            "sh_entmate_theme/static/src/js/form_controller_custom.js",
            "sh_entmate_theme/static/src/xml/form_controller.xml",
            "sh_entmate_theme/static/src/scss/form_controller/form_controller.scss",
            # # sh_attachment_in_tree_view
            '/sh_entmate_theme/static/src/scss/attachment/attachment.scss',

            # # open record in new tab feature
            'sh_entmate_theme/static/src/xml/open_record_in_new_tab/action_menus.xml',
            'sh_entmate_theme/static/src/xml/open_record_in_new_tab/list_rendered.xml',
            'sh_entmate_theme/static/src/js/open_record.js',
            #

            # theme configurator
            "sh_entmate_theme/static/src/xml/ThemeConfigSystray.xml",
            "sh_entmate_theme/static/src/xml/theme_config.xml",
            "sh_entmate_theme/static/src/js/theme_config_custom.js",

        ],

        'web.assets_frontend': [
            'sh_entmate_theme/static/src/scss/login_page_style.scss',
            'sh_entmate_theme/static/src/scss/font_family/fonts.scss',
        ],
        'web._assets_primary_variables': [
          ('after', 'web/static/src/scss/primary_variables.scss', '/sh_entmate_theme/static/src/scss/back_theme_config_main_scss.scss'),
        ],

    },


    'images': [
        'static/description/banner.gif',
        'static/description/splash-screen_screenshot.gif'
    ],
    "live_test_url": "https://softhealer.com/support?ticket_type=demo_request",
    "installable": True,
    "application": True,
    "price": 98,
    "currency": "EUR",
    "bootstrap": True
}
