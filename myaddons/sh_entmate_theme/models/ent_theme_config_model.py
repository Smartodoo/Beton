# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api, _
import base64

dict_theme_style = {

    'style_1':  {
        'primary_color': '#714B67',
        'extra_color': '#017e84',
        'secondary_color': '#E7E9ED',
        'header_background_color': '#FFFFFF',
        'header_font_color': '#1f2937',
        'kanban_box_style': 'style_1',
        'body_background_color': '#FFFFFF',
        'body_font_family': 'Ubuntu',
        'button_style': 'style_2',
        'separator_style': 'style_6',
        'separator_color': '#858585',

        'body_background_type': 'bg_color',

        'body_google_font_family': False,
        'is_used_google_font': False,

        'predefined_list_view_boolean': False,
        'predefined_list_view_style': 'style_1',
        'list_view_border': 'without_border',
        'list_view_is_hover_row': True,
        'list_view_hover_bg_color': '#f5f5f5',
        'list_view_even_row_color': '#FFFFFF',
        'list_view_odd_row_color': '#FFFFFF',

        'login_page_style': 'style_3',
        'login_page_background_type': 'bg_color',
        'login_page_background_color': '#B3FFB8',
        'login_page_box_color': '#FFFFFF',

        'sidebar_color': '#D9D7E7',
        'sidebar_img': 'style_1',
        'sidebar_font_color': '#374151',
        'breadcrumb_style': 'style_7',
        'progress_style': 'style_1',
        'progress_height': '4px',
        'progress_color':  '#ad86a3',
        
        'checkbox_style': 'default',
        'radio_style': 'default',
        'scrollbar_style' : 'style_1',
        'app_icon_style' : 'style_1',
        'dual_tone_icon_color_1' : '#714B67',
        'dual_tone_icon_color_2' : '#ac8ca4',
        'backend_all_icon_style' : 'backend_fontawesome_icon',
    },

    'style_2':  {
        'primary_color': '#ffc107',
        'extra_color': '#ffc107',
        'secondary_color': '#E7E9ED',
        'header_background_color': '#FFFFFF',
        'header_font_color': '#1f2937',
        'kanban_box_style': 'style_2',
        'body_background_color': '#FFFFFF',
        'body_font_family': 'Poppins',
        'button_style': 'style_1',
        'separator_style': 'style_6',
        'separator_color': '#c79100',

        'body_background_type': 'bg_color',

        'body_google_font_family': False,
        'is_used_google_font': False,

        'predefined_list_view_boolean': True,
        'predefined_list_view_style': 'style_1',
        'list_view_border': 'without_border',
        'list_view_is_hover_row': True,
        'list_view_hover_bg_color': '#f5f5f5',
        'list_view_even_row_color': '#FFFFFF',
        'list_view_odd_row_color': '#FFFFFF',

        'login_page_style': 'style_3',
        'login_page_background_type': 'bg_color',
        'login_page_background_color': '#B3FFB8',
        'login_page_box_color': '#FFFFFF',
        'sidebar_color': '#d1aa0e',
        'sidebar_img': 'style_2',
        'sidebar_font_color': '#374151',
        'breadcrumb_style': 'style_1',
        'progress_style': 'style_1',
        'progress_height': '4px',
        'progress_color':  '#ad8713',
        
        'checkbox_style':'style_3',
        'radio_style':'style_3',
        'scrollbar_style' : 'style_2',
        'app_icon_style' : 'style_2',
        'dual_tone_icon_color_1' : '#f3d893',
        'dual_tone_icon_color_2' : '#ffffff',
        'backend_all_icon_style' : 'backend_regular_icon',
    },

    'style_3':  {
        'primary_color': '#5c77ff',
        'extra_color': '#5c77ff',
        'secondary_color': '#E7E9ED',
        'header_background_color': '#FFFFFF',
        'header_font_color': '#1f2937',
        'kanban_box_style': 'style_3',
        'body_background_color': '#FFFFFF',
        'body_font_family': 'Raleway',
        'button_style': 'style_2',
        'separator_style': 'style_6',
        'separator_color': '#004ccb',

        'body_background_type': 'bg_color',

        'body_google_font_family': False,
        'is_used_google_font': False,

        'predefined_list_view_boolean': True,
        'predefined_list_view_style': 'style_2',
        'list_view_border': 'without_border',
        'list_view_is_hover_row': True,
        'list_view_hover_bg_color': '#f5f5f5',
        'list_view_even_row_color': '#FFFFFF',
        'list_view_odd_row_color': '#FFFFFF',

        'login_page_style': 'style_3',
        'login_page_background_type': 'bg_color',
        'login_page_background_color': '#B3FFB8',
        'login_page_box_color': '#FFFFFF',

        'sidebar_color': '#5c77ff',
        'sidebar_img': 'style_3',
        'sidebar_font_color': '#374151',
        'breadcrumb_style': 'style_2',
        'progress_style': 'style_1',
        'progress_height': '4px',
        'progress_color':  '#394cad',
        
        'checkbox_style':'style_2',
        'radio_style':'style_2',
        'scrollbar_style' : 'style_3',
        'app_icon_style' : 'style_3',
        'dual_tone_icon_color_1' : '#90c7ff',
        'dual_tone_icon_color_2' : '#ffffff',
        'backend_all_icon_style' : 'backend_light_icon',
    },
    'style_4':  {
        'primary_color': '#00bcd4',
        'extra_color': '#00bcd4',
        'secondary_color': '#E7E9ED',
        'header_background_color': '#FFFFFF',
        'header_font_color': '#1f2937',
        'kanban_box_style': 'style_4',
        'body_background_color': '#FFFFFF',
        'body_font_family': 'Oxygen',
        'button_style': 'style_2',
        'separator_style': 'style_6',
        'separator_color': '#008ba3',

        'body_background_type': 'bg_color',

        'body_google_font_family': False,
        'is_used_google_font': False,

        'predefined_list_view_boolean': True,
        'predefined_list_view_style': 'style_3',
        'list_view_border': 'without_border',
        'list_view_is_hover_row': True,
        'list_view_hover_bg_color': '#f5f5f5',
        'list_view_even_row_color': '#FFFFFF',
        'list_view_odd_row_color': '#FFFFFF',

        'login_page_style': 'style_3',
        'login_page_background_type': 'bg_color',
        'login_page_background_color': '#B3FFB8',
        'login_page_box_color': '#FFFFFF',
        'sidebar_color': '#00bcd4',
        'sidebar_img': 'style_4',
        'sidebar_font_color': '#374151',
        'breadcrumb_style': 'style_3',
        'progress_style': 'style_1',
        'progress_height': '4px',
        'progress_color':  '#008BA3',
        
        'checkbox_style':'style_3',
        'radio_style':'style_3',
        'scrollbar_style' : 'style_4',
        'app_icon_style' : 'style_4',
        'dual_tone_icon_color_1' : '#81e3ff',
        'dual_tone_icon_color_2' : '#ffffff',
        'backend_all_icon_style' : 'backend_regular_icon',
    },
    'style_5':  {
        'primary_color': '#ff5722',
        'extra_color': '#ff5722',
        'secondary_color': '#E7E9ED',
        'header_background_color': '#FFFFFF',
        'header_font_color': '#1f2937',
        'kanban_box_style': 'style_1',
        'body_background_color': '#FFFFFF',
        'body_font_family': 'KoHo',
        'button_style': 'style_1',
        'separator_style': 'style_6',
        'separator_color': '#c41c00',

        'body_background_type': 'bg_color',

        'body_google_font_family': False,
        'is_used_google_font': False,

        'predefined_list_view_boolean': False,
        'predefined_list_view_style': 'style_1',
        'list_view_border': 'without_border',
        'list_view_is_hover_row': True,
        'list_view_hover_bg_color': '#f5f5f5',
        'list_view_even_row_color': '#FFFFFF',
        'list_view_odd_row_color': '#FFFFFF',

        'login_page_style': 'style_3',
        'login_page_background_type': 'bg_color',
        'login_page_background_color': '#B3FFB8',
        'login_page_box_color': '#FFFFFF',

        'sidebar_color': '#e43a15',
        'sidebar_img': 'style_5',
        'sidebar_font_color': '#374151',
        'breadcrumb_style': 'style_4',
        'progress_style': 'style_1',
        'progress_height': '4px',
        'progress_color':  '#C41C00',
        
        'checkbox_style':'default',
        'radio_style':'default',
        'scrollbar_style' : 'style_5',
        'app_icon_style' : 'style_5',
        'dual_tone_icon_color_1' : '#fb7d68',
        'dual_tone_icon_color_2' : '#ffffff',
        'backend_all_icon_style' : 'backend_thin_icon',
    },
    'style_6':  {
        'primary_color': '#673ab7',
        'extra_color': '#673ab7',

        'secondary_color': '#E7E9ED',

        'header_background_color': '#FFFFFF',
        'header_font_color': '#1f2937',

        'kanban_box_style': 'style_2',
        'body_background_color': '#FFFFFF',
        'body_font_family': 'Roboto',
        'button_style': 'style_4',
        'separator_style': 'style_6',
        'separator_color': '#320b86',

        'body_background_type': 'bg_color',

        'body_google_font_family': False,
        'is_used_google_font': False,

        'predefined_list_view_boolean': True,
        'predefined_list_view_style': 'style_4',
        'list_view_border': 'without_border',
        'list_view_is_hover_row': True,
        'list_view_hover_bg_color': '#f5f5f5',
        'list_view_even_row_color': '#FFFFFF',
        'list_view_odd_row_color': '#FFFFFF',

        'login_page_style': 'style_3',
        'login_page_background_type': 'bg_color',
        'login_page_background_color': '#B3FFB8',
        'login_page_box_color': '#FFFFFF',
        'sidebar_color': '#6a3093',
        'sidebar_img': 'style_2',
        'sidebar_font_color': '#374151',
        'breadcrumb_style': 'style_5',
        'progress_style': 'style_1',
        'progress_height': '4px',
        'progress_color':  '#3f1b7d',
        
        'checkbox_style':'default',
        'radio_style':'default',
        'scrollbar_style' : 'style_1',
        'app_icon_style' : 'style_6',
        'dual_tone_icon_color_1' : '#ab7bff',
        'dual_tone_icon_color_2' : '#ffffff',
        'backend_all_icon_style' : 'backend_light_icon',
    },
    'style_7':  {
        'primary_color': '#9e9e9e',
        'extra_color': '#9e9e9e',

        'secondary_color': '#E7E9ED',

        'header_background_color': '#FFFFFF',
        'header_font_color': '#1f2937',

        'kanban_box_style': 'style_3',
        'body_background_color': '#FFFFFF',
        'body_font_family': 'Ubuntu',
        'button_style': 'style_3',
        'separator_style': 'style_6',
        'separator_color': '#707070',

        'body_background_type': 'bg_color',

        'body_google_font_family': False,
        'is_used_google_font': False,

        'predefined_list_view_boolean':True,
        'predefined_list_view_style': 'style_5',
        'list_view_border': 'without_border',
        'list_view_is_hover_row': True,
        'list_view_hover_bg_color': '#f5f5f5',
        'list_view_even_row_color': '#FFFFFF',
        'list_view_odd_row_color': '#FFFFFF',

        'login_page_style': 'style_3',
        'login_page_background_type': 'bg_color',
        'login_page_background_color': '#B3FFB8',
        'login_page_box_color': '#FFFFFF',

        'sidebar_color': '#757f9a',
        'sidebar_img': 'style_3',
        'sidebar_font_color': '#374151',
        'breadcrumb_style': 'style_6',
        'progress_style': 'style_1',
        'progress_height': '4px',
        'progress_color':  '#666666',
        
        'checkbox_style':'default',
        'radio_style':'default',
        'scrollbar_style' : 'style_2',
        'app_icon_style' : 'style_2',
        'dual_tone_icon_color_1' : '#d2d7e1',
        'dual_tone_icon_color_2' : '#ffffff',  
        'backend_all_icon_style' : 'backend_fontawesome_icon',      
    },
    'style_8':  {
        'primary_color': '#4caf50',
        'extra_color': '#4caf50',
        'secondary_color': '#E7E9ED',
        'header_background_color': '#FFFFFF',
        'header_font_color': '#1f2937',
        'kanban_box_style': 'style_4',
        'body_background_color': '#FFFFFF',
        'body_font_family': 'Poppins',
        'button_style': 'style_1',
        'separator_style': 'style_6',
        'separator_color': '#087f23',

        'body_background_type': 'bg_color',

        'body_google_font_family': False,
        'is_used_google_font': False,

        'predefined_list_view_boolean': True,
        'predefined_list_view_style': 'style_1',
        'list_view_border': 'without_border',
        'list_view_is_hover_row': True,
        'list_view_hover_bg_color': '#f5f5f5',
        'list_view_even_row_color': '#FFFFFF',
        'list_view_odd_row_color': '#FFFFFF',

        'login_page_style': 'style_3',
        'login_page_background_type': 'bg_color',
        'login_page_background_color': '#B3FFB8',
        'login_page_box_color': '#FFFFFF',

        'checkbox_style': 'default',
        'radio_style': 'default',
        'sidebar_color': '#1d976c',
        'sidebar_img': 'style_4',
        'sidebar_font_color': '#374151',
        'breadcrumb_style': 'style_7',
        'progress_style': 'style_1',
        'progress_height': '4px',
        'progress_color':  '#1b801f',
        
        'scrollbar_style' : 'style_3',
        'app_icon_style' : 'style_3',
        'dual_tone_icon_color_1' : '#a2efc4',
        'dual_tone_icon_color_2' : '#ffffff', 
        'backend_all_icon_style' : 'backend_light_icon',
    },
    'style_9':  {
        'primary_color': '#ff9800',
        'extra_color': '#ff9800',
        'secondary_color': '#E7E9ED',
        'header_background_color': '#FFFFFF',
        'header_font_color': '#1f2937',
        'kanban_box_style': 'style_1',
        'body_background_color': '#FFFFFF',
        'body_font_family': 'Raleway',
        'button_style': 'style_2',
        'separator_style': 'style_6',
        'separator_color': '#c66900',

        'body_background_type': 'bg_color',

        'body_google_font_family': False,
        'is_used_google_font': False,

        'predefined_list_view_boolean': True,
        'predefined_list_view_style': 'style_2',
        'list_view_border': 'without_border',
        'list_view_is_hover_row': True,
        'list_view_hover_bg_color': '#f5f5f5',
        'list_view_even_row_color': '#FFFFFF',
        'list_view_odd_row_color': '#FFFFFF',

        'login_page_style': 'style_3',
        'login_page_background_type': 'bg_color',
        'login_page_background_color': '#B3FFB8',
        'login_page_box_color': '#FFFFFF',
        'checkbox_style': 'default',
        'radio_style': 'default',
        'sidebar_color': '#ff512f',
        'sidebar_img': 'style_5',
        'sidebar_font_color': '#374151',
        'breadcrumb_style': 'style_1',
        'progress_style': 'style_1',
        'progress_height': '4px',
        'progress_color':  '#b5781f',
        
        'scrollbar_style' : 'style_4',
        'app_icon_style' : 'style_4',
        'dual_tone_icon_color_1' : '#ffb85c',
        'dual_tone_icon_color_2' : '#ffffff', 
        'backend_all_icon_style' : 'backend_fontawesome_icon',
    },

    'style_10':  {
        'primary_color': '#e91e63',
        'extra_color': '#e91e63',
        'secondary_color': '#E7E9ED',
        'header_background_color': '#FFFFFF',
        'header_font_color': '#1f2937',

        'kanban_box_style': 'style_2',
        'body_background_color': '#FFFFFF',
        'body_font_family': 'Oxygen',
        'button_style': 'style_1',
        'separator_style': 'style_6',
        'separator_color': '#b0003a',

        'body_background_type': 'bg_color',

        'body_google_font_family': False,
        'is_used_google_font': False,

        'predefined_list_view_boolean': True,
        'predefined_list_view_style': 'style_3',
        'list_view_border': 'without_border',
        'list_view_is_hover_row': True,
        'list_view_hover_bg_color': '#f5f5f5',
        'list_view_even_row_color': '#FFFFFF',
        'list_view_odd_row_color': '#FFFFFF',

        'login_page_style': 'style_3',
        'login_page_background_type': 'bg_color',
        'login_page_background_color': '#B3FFB8',
        'login_page_box_color': '#FFFFFF',

        'checkbox_style': 'default',
        'radio_style': 'default',
        'sidebar_color': '#dd2476',
        'sidebar_img': 'style_2',
        'sidebar_font_color': '#374151',
        'breadcrumb_style': 'style_2',
        'progress_style': 'style_1',
        'progress_height': '4px',
        'progress_color':  '#ab1a4b',
        
        'scrollbar_style' : 'style_5',
        'app_icon_style' : 'style_5',
        'dual_tone_icon_color_1' : '#ff728f',
        'dual_tone_icon_color_2' : '#ffffff', 
        'backend_all_icon_style' : 'backend_light_icon',
    },
    'style_11':  {
        'primary_color': '#9c27b0',
        'extra_color': '#9c27b0',

        'secondary_color': '#E7E9ED',

        'header_background_color': '#FFFFFF',
        'header_font_color': '#1f2937',

        'kanban_box_style': 'style_3',
        'body_background_color': '#FFFFFF',
        'body_font_family': 'KoHo',
        'button_style': 'style_3',
        'separator_style': 'style_6',
        'separator_color': '#6a0080',

        'body_background_type': 'bg_color',

        'body_google_font_family': False,
        'is_used_google_font': False,

        'predefined_list_view_boolean': False,
        'predefined_list_view_style': 'style_1',        
        'list_view_border': 'without_border',
        'list_view_is_hover_row': True,
        'list_view_hover_bg_color': '#f5f5f5',
        'list_view_even_row_color': '#FFFFFF',
        'list_view_odd_row_color': '#FFFFFF',

        'login_page_style': 'style_3',
        'login_page_background_type': 'bg_color',
        'login_page_background_color': '#B3FFB8',
        'login_page_box_color': '#FFFFFF',
        'checkbox_style': 'default',
        'radio_style': 'default',
        'sidebar_color': '#88219a',
        'sidebar_img': 'style_3',
        'sidebar_font_color': '#374151',
        'breadcrumb_style': 'style_3',
        'progress_style': 'style_1',
        'progress_height': '4px',
        'progress_color':  '#741485',
        
        'scrollbar_style' : 'style_1',
        'app_icon_style' : 'style_6',
        'dual_tone_icon_color_1' : '#C38FD6',
        'dual_tone_icon_color_2' : '#ffffff', 
        'backend_all_icon_style' : 'backend_thin_icon',
    },
    'style_12':  {
        'primary_color': '#f44336',
        'extra_color': '#f44336',
        'secondary_color': '#E7E9ED',

        'header_background_color': '#FFFFFF',
        'header_font_color': '#1f2937',

        'kanban_box_style': 'style_4',
        'body_background_color': '#FFFFFF',
        'body_font_family': 'Ubuntu',
        'button_style': 'style_1',
        'separator_style': 'style_6',
        'separator_color': '#ba000d',

        'body_background_type': 'bg_color',

        'body_google_font_family': False,
        'is_used_google_font': False,

        'predefined_list_view_boolean': True,
        'predefined_list_view_style': 'style_1',
        'list_view_border': 'without_border',
        'list_view_is_hover_row': True,
        'list_view_hover_bg_color': '#f5f5f5',
        'list_view_even_row_color': '#FFFFFF',
        'list_view_odd_row_color': '#FFFFFF',

        'login_page_style': 'style_3',
        'login_page_background_type': 'bg_color',
        'login_page_background_color': '#B3FFB8',
        'login_page_box_color': '#FFFFFF',

        'checkbox_style': 'default',
        'radio_style': 'default',
        'sidebar_color': '#d31027',
        'sidebar_img': 'style_4',
        'sidebar_font_color': '#374151',
        'breadcrumb_style': 'style_4',

        'progress_style': 'style_1',
        'progress_height': '4px',
        'progress_color':  '#a8332a',
        
        'scrollbar_style' : 'style_2',
        'app_icon_style' : 'style_2',
        'dual_tone_icon_color_1' : '#DB9D95',
        'dual_tone_icon_color_2' : '#ffffff', 
        'backend_all_icon_style' : 'backend_regular_icon',
    },

    'style_13':  {
        'primary_color': '#009688',
        'extra_color': '#009688',
        'secondary_color': '#E7E9ED',
        'header_background_color': '#FFFFFF',
        'header_font_color': '#1f2937',
        'kanban_box_style': 'style_1',
        'body_background_color': '#FFFFFF',
        'body_font_family': 'Ubuntu',
        'button_style': 'style_2',
        'separator_style': 'style_6',
        'separator_color': '#00675b',

        'body_background_type': 'bg_color',

        'body_google_font_family': False,
        'is_used_google_font': False,

        'predefined_list_view_boolean': False,
        'predefined_list_view_style': 'style_1',
        'list_view_border': 'without_border',
        'list_view_is_hover_row': True,
        'list_view_hover_bg_color': '#f5f5f5',
        'list_view_even_row_color': '#FFFFFF',
        'list_view_odd_row_color': '#FFFFFF',

        'login_page_style': 'style_3',
        'login_page_background_type': 'bg_color',
        'login_page_background_color': '#B3FFB8',
        'login_page_box_color': '#FFFFFF',

        'checkbox_style': 'default',
        'radio_style': 'default',
        'sidebar_color': '#007a6e',
        'sidebar_img': 'style_5',
        'sidebar_font_color': '#374151',
        'breadcrumb_style': 'style_5',
        'progress_style': 'style_1',
        'progress_height': '4px',
        'progress_color':  '#00675B',
        
        'scrollbar_style' : 'style_3',
        'app_icon_style' : 'style_3',
        'dual_tone_icon_color_1' : '#7CDAD1',
        'dual_tone_icon_color_2' : '#ffffff', 
        'backend_all_icon_style' : 'backend_regular_icon',
    },
}


class sh_entmate_theme_settings(models.Model):
    _name = 'sh.ent.theme.config.settings'
    _description = 'Back Theme Config Settings'

    name = fields.Char(string="Theme Settings")

    theme_style = fields.Selection([
        ('style_1', 'Default'),
        ('style_2', 'AMBER'),
        ('style_3', 'BLUE'),
        ('style_4', 'CYAN'),
        ('style_5', 'DEEP-ORANGE'),
        ('style_6', 'DEEP-PURPLE'),
        ('style_7', 'GRAY'),
        ('style_8', 'GREEN'),
        ('style_9', 'ORANGE'),
        ('style_10', 'PINK'),
        ('style_11', 'PURPLE'),
        ('style_12', 'RED'),
        ('style_13', 'TEAL'),
    ], string="Theme Color", default='style_1')

    primary_color = fields.Char(string='Primary Color', default='#00A09D')
    extra_color = fields.Char(string='Extra Color', default='#017e84')

    secondary_color = fields.Char(string='Secondary Color', default='#E6E6E6')

    header_background_type = fields.Selection([
        ('bg_color', 'Color'),
        ('bg_img', 'Image')
    ], string="Header Background Type", default="bg_color")
    header_background_color = fields.Char(
        string='Header Background Color', default='#875A7B')
    header_background_image = fields.Binary(string='Header Background Image ')
    header_font_color = fields.Char(
        string='Header Font Color', default='#1f2937')

    kanban_box_style = fields.Selection([
        ('style_1', 'Style 1'),
        ('style_2', 'Style 2'),
        ('style_3', 'Style 3'),
        ('style_4', 'Style 4'),
    ], string='Kanban Box Style', default="style_2")
    body_background_type = fields.Selection([
        ('bg_color', 'Color'),
        ('bg_img', 'Image')
    ], string="Body Background Type", default="bg_color")

    body_background_color = fields.Char(
        string='Body Background Color', default="#FFFFFF")
    body_background_image = fields.Binary(string='Body Background Image ')
    body_font_family = fields.Selection([
        ('Roboto', 'Roboto'),
        ('Raleway', 'Raleway'),
        ('Poppins', 'Poppins'),
        ('Oxygen', 'Oxygen'),
        ('OpenSans', 'OpenSans'),
        ('KoHo', 'KoHo'),
        ('Ubuntu', 'Ubuntu'),
        ('custom_google_font', 'Custom Google Font'),
    ], string='Body Font Family', default='Ubuntu')

    body_google_font_family = fields.Char(string="Google Font Family")
    is_used_google_font = fields.Boolean(string="Is use google font?")

    button_style = fields.Selection([
        ('style_1', 'Style 1'),
        ('style_2', 'Style 2'),
        ('style_3', 'Style 3'),
        ('style_4', 'Style 4'),
    ], string='Button Style', default="style_2")

    separator_style = fields.Selection([
        ('style_1', 'Style 1'),
        ('style_2', 'Style 2'),
        ('style_3', 'Style 3'),
        ('style_4', 'Style 4'),
        ('style_5', 'Style 5'),
        ('style_6', 'Default'),
    ], string='Separator Style', default="style_6")

    separator_color = fields.Char(string="Separator Color", default="#5D1049")

    sidebar_color = fields.Char(
        string="Background Color", default="#e7e9ed")
    sidebar_img = fields.Selection([('style_1', 'Style 1'), ('style_2', 'Style 2'), ('style_3', 'Style 3'), (
        'style_4', 'Style 4'), ('style_5', 'Style 5'),('style_6', 'Style 6')], string=" Background Image", default='style_1')

    sidebar_font_color =  fields.Char(string = 'Sidebar Font Color')

    progress_style = fields.Selection([
        ('style_1', 'Style 1'),
        ('none', 'None'),
    ], string='Progress Bar Style', default="style_1")

    progress_height = fields.Char("Height")
    progress_color = fields.Char("Color")

    predefined_list_view_boolean = fields.Boolean(string="Is Predefined List View?")
    predefined_list_view_style = fields.Selection([
        ('style_1', 'Style 1'),
        ('style_2', 'Style 2'),
        ('style_3', 'Style 3'),
        ('style_4', 'Style 4'),
        ('style_5', 'Style 5')
        ], default='style_1', string="Predefined List View Style")
    list_view_border = fields.Selection([
        ('bordered', 'Bordered'),
        ('without_border', 'Without Border')
    ], default='without_border', string="List View Border")

    list_view_is_hover_row = fields.Boolean(string="Rows Hover?", default=True)
    list_view_hover_bg_color = fields.Char(
        string="Hover Background Color", default="#f5f5f5")
    list_view_even_row_color = fields.Char(
        string="Even Row Color", default="#FFFFFF")
    list_view_odd_row_color = fields.Char(
        string="Odd Row Color", default="#FFFFFF")

    login_page_style = fields.Selection([
        ('style_0', 'Odoo Standard'),
        ('style_1', 'Style 1'),
        ('style_2', 'Style 2'),
        ('style_3', 'Style 3'),
    ], string="Style", default='style_3')

    login_page_background_type = fields.Selection([
        ('bg_color', 'Color'),
        ('bg_img', 'Image')
    ], string="Background Type", default="bg_color")

    login_page_background_color = fields.Char(
        string='Background Color', default="#B3FFB8")
    login_page_background_image = fields.Binary(string='Background Image ')
    login_page_box_color = fields.Char(string='Box Color')
    login_page_banner_image = fields.Binary(string='Banner Image')

    # Sticky
    is_sticky_form = fields.Boolean(string="Form Status Bar")
    is_sticky_list = fields.Boolean(string="List View Footer")
    is_sticky_list_inside_form = fields.Boolean(string="List View Inside Form")
    is_sticky_pivot = fields.Boolean(string="Pivot View")

    # New checkbox icon style
    checkbox_style = fields.Selection([
        ('style_1','Style 1'),
        ('style_2','Style 2'),
        ('style_3','Style 3'),
        ('default','Default'),                 
        ],string = 'Checkbox Style',default='default')


    # New Radio icon style
    radio_style = fields.Selection([
        ('style_1','Style 1'),
        ('style_2','Style 2'),
        ('style_3','Style 3'),
        ('default','Default'),                  
        ],string = 'Radio Button Style',default='default')

    scrollbar_style = fields.Selection([
        ('style_1','Style 1'),
        ('style_2','Style 2'),
        ('style_3','Style 3'),
        ('style_4','Style 4'),
        ('style_5','Style 5'),                 
        ],string = 'Scrollbar Style',default='style_1')


    app_icon_style = fields.Selection([
        ('style_1', 'Standard'),
        ('style_2', 'Line Icon'),
        ('style_3', '3D Icon'),
        ('style_4', 'Dual Tone'),
        ('style_5', 'Glass Icon'),
        ('style_6', 'Light Icon'),
        ], string='App Icon Style', default='style_1')

    dual_tone_icon_color_1 = fields.Char(string='Dual Tone Icon Color 1')
    dual_tone_icon_color_2 = fields.Char(string='Dual Tone Icon Color 2')

    backend_all_icon_style = fields.Selection([
        ('backend_fontawesome_icon', 'Standard FontAwesome Icon'),
        ('backend_regular_icon', 'Regular Icon'),
        ('backend_light_icon', 'Light Icon'),
        ('backend_thin_icon', 'Thin Icon'),
        ], string='Font Icon Style', default='backend_fontawesome_icon')

    horizontal_tab_style = fields.Selection([
        ('style_1', 'Style 1'),
        ('style_2', 'Style 2'),
        ('style_3', 'Style 3'),
        ('style_4', 'Style 4'),
        ('style_5', 'Style 5'),
        ('style_6', 'Style 6'),
        ('style_7', 'Style 7'),
    ], string='Tab Style', default='style_7')


    form_element_style = fields.Selection([
        ('style_1', 'Style 1'),
        ('style_2', 'Style 2'),
        ('style_3', 'Style 3'),
        ('style_4', 'Style 4'),
        ('style_5', 'Style 5'),
        ('style_6', 'Style 6'),
        ('style_7', 'Style 7'),
    ], string='Form Element Style', default='style_7')


    breadcrumb_style = fields.Selection([
        ('style_1', 'Style 1'),
        ('style_2', 'Style 2'),
        ('style_3', 'Style 3'),
        ('style_4', 'Style 4'),
        ('style_5', 'Style 5'),
        ('style_6', 'Style 6'),
        ('style_7', 'Style 7'),
    ], string='Breadcrumb Style', default='style_1')

    is_navbar_style = fields.Boolean()

    @api.onchange('body_font_family')
    def onchage_body_font_family(self):
        if self.body_font_family == 'custom_google_font':
            self.is_used_google_font = True
        else:
            self.is_used_google_font = False
            self.body_google_font_family = False

    def action_preview_theme_style(self):
        if self:

            context = dict(self.env.context or {})
            img_src = ""
            if context and context.get('which_style', '') == 'theme':
                img_src = "/sh_entmate_theme/static/src/img/preview/theme/style_theme.png"

            if context and context.get('which_style', '') == 'button':
                img_src = "/sh_entmate_theme/static/src/img/preview/button/style_button.png"

            if context and context.get('which_style', '') == 'separator':
                img_src = "/sh_entmate_theme/static/src/img/preview/separator/style_separator.png"

            if context and context.get('which_style', '') == 'sidebar':
                img_src = "/sh_entmate_theme/static/src/img/preview/sidebar/style sidebar.png"

            if context and context.get('which_style', '') == 'login_page':
                img_src = "/sh_entmate_theme/static/src/img/preview/login_page/style_login.png"

            if context and context.get('which_style', '') == 'mobile':
                img_src = "/sh_entmate_theme/static/src/img/preview/mobile_preview.png"

            if context and context.get('which_style', '') == 'checkbox':
                img_src = "/sh_entmate_theme/static/src/img/preview/checkbox_style_preview.png"

            if context and context.get('which_style', '') == 'scrollbar_style':
                img_src = "/sh_entmate_theme/static/src/img/preview/scrollbar_style_gif.gif"

            if context and context.get('which_style', '') == 'predefined_list_view':
                img_src = "/sh_entmate_theme/static/src/img/preview/predefined_list_view_style.png"

            if context and context.get('which_style', '') == 'app_icon_style':
                img_src = "/sh_entmate_theme/static/src/img/preview/app_icon_style.png" 

            if context and context.get('which_style', '') == 'backend_all_icon_style':
                img_src = "/sh_entmate_theme/static/src/img/preview/backend_icon_style.png"

            if context and context.get('which_style', '') == 'radio':
                img_src = "/sh_entmate_theme/static/src/img/preview/radio_btn_style_preview.png"

            if context and context.get('which_style', '') == 'enterprise_svg':
                img_src = "/sh_entmate_theme/static/src/img/preview/enterprise_svg_preview.png"

            if context and context.get('which_style', '') == 'loading':
                img_src = "/sh_entmate_theme/static/src/img/preview/loading-gif.gif"

            if context and context.get('which_style', '') == 'horizontal_tab_style':
                img_src = "/sh_entmate_theme/static/src/img/preview/horizontal_tab.png"

            context['default_img_src'] = img_src

            return {
                'name': _('Preview Style'),
                'view_mode': 'form',
                'res_model': 'sh.theme.preview.wizard',
                'view_id': self.env.ref('sh_entmate_theme.sh_entmate_theme_theme_preview_wizard_form').id,
                'type': 'ir.actions.act_window',
                'context': context,
                'target': 'new',
                'flags': {'form': {'action_buttons': False}}
            }

    def action_change_theme_style(self):
        if self and self.theme_style:
            selected_theme_style_dict = dict_theme_style.get(
                self.theme_style, False)
            if selected_theme_style_dict:
                self.update(selected_theme_style_dict)

    @api.onchange('theme_style')
    def onchage_theme_style(self):
        if self and self.theme_style:
            selected_theme_style_dict = dict_theme_style.get(
                self.theme_style, False)
            if selected_theme_style_dict:
                self.update(selected_theme_style_dict)

    @api.model
    def onchange_theme_style_js(self,theme_style):
        if theme_style:
            theme_config_rec = self.browse(1)
            selected_theme_style_dict = dict_theme_style.get(
                theme_style, False)
            if selected_theme_style_dict:
                theme_config_rec.update(selected_theme_style_dict)
                return True

    def write(self, vals):
        """
           Write theme settings data in a less file
        """

        res = super(sh_entmate_theme_settings, self).write(vals)
        if self:
            for rec in self:

                content = """   
$primaryColor:%s;
$extra_color:%s;
$secondaryColor:%s;
$header_bg_type:%s;
$header_bg_color:%s;
$header_font_color:%s;
$body_background_type:%s;
$body_background_color:%s;
$body_font_family:%s;
$button_style:%s;
$separator_style:%s;
$separator_color:%s;
$sidebar_font_color:%s;
$kanban_box_style:%s;
$body_google_font_family:%s;
$is_used_google_font:%s;
$predefined_list_view_boolean:%s;
$predefined_list_view_style:%s;
$list_view_border:%s;
$list_view_is_hover_row:%s;
$list_view_hover_bg_color:%s;
$list_view_even_row_color:%s;
$list_view_odd_row_color:%s;
$login_page_style: %s;
$login_page_background_type: %s;
$login_page_background_color:%s;
$login_page_box_color:%s;
$theme_style: %s;
$is_sticky_form:%s;
$is_sticky_list:%s;
$is_sticky_list_inside_form:%s;
$is_sticky_pivot:%s;
$checkbox_style:%s;
$radio_style:%s;
$scrollbar_style:%s;
$app_icon_style:%s;
$backend_all_icon_style:%s;
$dual_tone_icon_color_1:%s;
$dual_tone_icon_color_2:%s;
$sidebar_color:%s;
$sidebar_img:%s;
$horizontal_tab_style:%s;
$form_element_style:%s;
$breadcrumb_style:%s;
$progress_style:%s;
$progress_height:%s;
$progress_color:%s;
                """ % (

                    rec.primary_color,
                    rec.extra_color,
                    rec.secondary_color,
                    rec.header_background_type,
                    rec.header_background_color,
                    rec.header_font_color,
                    rec.body_background_type,
                    rec.body_background_color,
                    rec.body_font_family,
                    rec.button_style,
                    rec.separator_style,
                    rec.separator_color,
                    rec.sidebar_font_color,
                    rec.kanban_box_style,
                    rec.body_google_font_family,
                    rec.is_used_google_font,
                    rec.predefined_list_view_boolean,
                    rec.predefined_list_view_style,
                    rec.list_view_border,
                    rec.list_view_is_hover_row,
                    rec.list_view_hover_bg_color,
                    rec.list_view_even_row_color,
                    rec.list_view_odd_row_color,
                    rec.login_page_style,
                    rec.login_page_background_type,
                    rec.login_page_background_color,
                    rec.login_page_box_color,
                    rec.theme_style,
                    rec.is_sticky_form,
                    rec.is_sticky_list,
                    rec.is_sticky_list_inside_form,
                    rec.is_sticky_pivot,
                    rec.checkbox_style,
                    rec.radio_style,
                    rec.scrollbar_style,
                    rec.app_icon_style,
                    rec.backend_all_icon_style,
                    rec.dual_tone_icon_color_1,
                    rec.dual_tone_icon_color_2,
                    rec.sidebar_color,
                    rec.sidebar_img,
                    rec.horizontal_tab_style,
                    rec.form_element_style,
                    rec.breadcrumb_style,
                    rec.progress_style,
                    rec.progress_height,
                    rec.progress_color,
                )

                IrAttachment = self.env["ir.attachment"]
                # search default attachment by url that will created when app installed...
                url = "/sh_entmate_theme/static/src/scss/back_theme_config_main_scss.scss"

                search_attachment = IrAttachment.sudo().search([
                    ('url', '=', url),
                ], limit=1)

                # Check if the file to save had already been modified
                datas = base64.b64encode((content or "\n").encode("utf-8"))
                if search_attachment:
                    # If it was already modified, simply override the corresponding attachment content
                    search_attachment.sudo().write({"datas": datas})

                else:
                    # If not, create a new attachment
                    new_attach = {
                        "name": "Back Theme Settings scss File",
                        "type": "binary",
                        "mimetype": "text/scss",
                        "datas": datas,
                        "url": url,
                        "public": True,
                        "res_model": "ir.ui.view",
                    }

                    IrAttachment.sudo().create(new_attach)

                # clear the catch to applied our new theme effects.
                self.env.registry.clear_cache()
                IrAttachment.regenerate_assets_bundles()

        return res