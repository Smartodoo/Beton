/* @odoo-module */

import { Component, useState, xml, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { jsonrpc } from "@web/core/network/rpc_service";
import { renderToFragment } from "@web/core/utils/render";


export class ThemeConfigurationTemplate extends Component {
    static template = "ThemeConfigurationTemplate";

    async setup() {
        super.setup()
        this.orm = useService("orm");
        let userAgent = navigator.userAgent;
		let browserName;
		var isSafari = /constructor/i.test(window.HTMLElement) || (function (p) { return p.toString() === "[object SafariRemoteNotification]"; })(!window['safari'] || (typeof safari !== 'undefined' && window['safari'].pushNotification));
		var iOS = !window.MSStream && /iPad|iPhone|iPod/.test(navigator.userAgent);
		var is_iPad = navigator.userAgent.match(/iPad/i) != null;
		var is_safari = /^((?!chrome|android).)*safari/i.test(navigator.userAgent);
		if(is_safari){
			$('.o_web_client').addClass('backmate_safari')
		}
		if(iOS && !is_iPad){
			if(userAgent.match(/chrome|chromium|crios/i)){
				$('.o_web_client').addClass("sh_iphone_chrome")
			}else{
				$('.o_web_client').addClass("sh_iphone_safari")
			}
		}
        this.user = useService("user");
        var color_change = false;
        if (!$('.backmate_theme_layout').length){
            var self = this
            var theme_configuration_html = renderToFragment('ThemeConfiguration',{
                               _click_sh_theme_design: function (ev){
                                self._click_sh_theme_design(ev)
                            },
                             _click_sh_theme_design: function (ev){
                                self._click_sh_theme_design(ev)
                            },
                            _click_close_setting: function(ev){
                                $('.backmate_theme_layout').removeClass('sh_theme_model');
                            },
                             async  _click_theme_color_box(ev){
                                var color_id = $(ev.currentTarget).attr('id');

                                $.each($('.theme_color_box'), function (event) {
                                    $(event).removeClass('active');
                                    $(event).find('input[name="themeColor"]').attr('checked', false);
                                })
                                $(ev.currentTarget).addClass('active');
                                $(ev.currentTarget).find('input[name="themeColor"]').attr('checked', true);

                                color_change = true;

                                jsonrpc("/web/dataset/call_kw/res.lang/onchange_theme_style_js", {
                                            model: 'sh.ent.theme.config.settings',
                                            method: 'onchange_theme_style_js',
                                            args: [color_id],
                                            kwargs: {},
                                        }).then(async function (rec) {
                                            var result = await self.orm.write("sh.ent.theme.config.settings", [1], { theme_style : color_id });
                                            if (result){
                                                location.reload();
                                            }
                                        });
                            },
                            _click_sidebar_style_box: function(ev){
                                self._click_sidebar_style_box(ev)
                            },
                            _on_change_body_font_family: function(ev){
                                self._on_change_body_font_family(ev)
                            },
                            _click_header_background_type: function(ev){
                                self._click_header_background_type(ev)
                            },
                            _click_body_background_type: function(ev){
                                self._click_body_background_type(ev)
                            },
                            _click_separator_style_box: function(ev){
                                self._click_separator_style_box(ev)
                            },
                            _click_button_style_box: function(ev){
                                self._click_button_style_box(ev)
                            },
                            _click_app_icon_style_box: function(ev){
                                self._click_app_icon_style_box(ev)
                            },
                            _click_tab_style_box: function(ev){
                                self._click_tab_style_box(ev)
                            },
                            _click_predefined_list_view_boolean: function(ev){
                                self._click_predefined_list_view_boolean(ev)
                            },
                            _click_list_view_is_hover_row: function(ev){
                                self._click_list_view_is_hover_row(ev)
                            },
                            _click_login_style_box: function(ev){
                                self._click_login_style_box(ev)
                            },
                            _click_login_page_background_type : function(ev){
                                self._click_login_page_background_type(ev)
                            },
                            _click_progressbar_style_box : function(ev){
                                self._click_progressbar_style_box(ev)
                            },
                            _click_form_element_style_box: function(ev){
                                self._click_form_element_style_box(ev)
                            },
                            _click_breadcrumbs_style_box: function(ev){
                                self._click_breadcrumbs_style_box(ev)
                            },
                            _click_checkbox_style_box: function(ev){
                                self._click_checkbox_style_box(ev)
                            },
                            _click_radio_button_style_box: function(ev){
                                self._click_radio_button_style_box(ev)
                            },
                            _click_scrollbar_style_box: function(ev){
                                self._click_scrollbar_style_box(ev)
                            },
                            _click_kanban_style_box: function(ev){
                                self._click_kanban_style_box(ev)
                            },
                            _click_font_icon_style_box: function(ev){
                                self._click_font_icon_style_box(ev)
                            },
                            _click_listview_style_box: function(ev){
                                self._click_listview_style_box(ev)
                            },
                            _click_save_color: function(ev){
                                self._click_save_color(ev)
                            },
                            _click_discard_color : function(ev){
                                location.reload();
                            },
            });

            $('.o_web_client').append(theme_configuration_html)
            jsonrpc('/get_theme_style',{}).then(function (data) {

                var active_color = data['theme_style']
                if (active_color) {
                    $('#' + active_color).find('input[name="themeColor"]').attr('checked', true);
                }


                var sidebar_img = data['sidebar_img']
                if (sidebar_img) {
                    $('#theme_style_id').find('#' + sidebar_img).find('input[name="themeStyle"]').attr('checked', true);
                }

                var separator_style = data['separator_style']
                if (separator_style) {
                    $('#separator_style_id').find('#' + separator_style).find('input[name="separator_style"]').attr('checked', true);
                }

                var button_style = data['button_style']
                if (button_style) {
                    $('#button_style_id').find('#' + button_style).find('input[name="button_style"]').attr('checked', true);
                }


                var app_icon_style = data['app_icon_style']
                if (app_icon_style) {
                    $('#app_icon_style_id').find('#' + app_icon_style).find('input[name="app_icon_style"]').attr('checked', true);
                }

                var tab_style = data['tab_style']
                if (tab_style) {
                    $('#tab_style_id').find('#' + tab_style).find('input[name="tab_style"]').attr('checked', true);
                }

                var progress_style = data['progress_style']
                if (progress_style) {
                    $('#progressbar_style_id').find('#' + progress_style).find('input[name="progressbar_style"]').attr('checked', true);
                }

                var is_sticky_form = data['is_sticky_form']
                if (is_sticky_form) {
                    $('#is_sticky_form').attr('checked', true);
                }

                var is_sticky_list = data['is_sticky_list']
                if (is_sticky_list) {
                    $('#is_sticky_list').attr('checked', true);
                }
                var is_sticky_list_inside_form = data['is_sticky_list_inside_form']
                if (is_sticky_list_inside_form) {
                    $('#is_sticky_list_inside_form').attr('checked', true);
                }
                var is_sticky_pivot = data['is_sticky_pivot']
                if (is_sticky_pivot) {
                    $('#is_sticky_pivot').attr('checked', true);
                }

                var body_font_family = data['body_font_family']
                if (body_font_family) {
                    $('#body_font_family').val(body_font_family);
                }

                var body_font_family = $('#body_font_family').val();
                if (body_font_family == 'custom_google_font') {

                    $("#body_google_font_family").css("display", "block");
                    $("#body_google_font_family_label").css("display", "block");
                } else {
                    $("#body_google_font_family").css("display", "none");
                    $("#body_google_font_family_label").css("display", "none");
                }
                var body_google_font_family = data['body_google_font_family']
                if (body_google_font_family) {
                    $('#body_google_font_family').val(body_google_font_family);
                }

                var body_background_type = data['body_background_type']
                if (body_background_type == 'bg_img') {
                    $('#bg_img').attr('checked', true);
                    $('#body_background_color').css("display", "none");
                    $('#body_background_img').css("display", "block");
                } else if (body_background_type == 'bg_color') {
                    $('#bg_color').attr('checked', true);
                    $('#body_background_color').css("display", "block");
                    $('#body_background_img').css("display", "none");
                }

                var header_background_type = data['header_background_type']
                if (header_background_type == 'bg_img') {
                    $('#header_img').attr('checked', true);
                    $('#header_background_color').css("display", "none");
                    $('#header_background_img').css("display", "block");
                } else if (header_background_type == 'bg_color') {
                    $('#bg_color').attr('checked', true);
                    $('#header_background_color').css("display", "block");
                    $('#header_background_img').css("display", "none");
                }

                var sidebar_background_color = data['sidebar_bg_color']
                if (sidebar_background_color) {
                    $('#sidebar_bg_color').val(sidebar_background_color);
                }

                var sidebar_font_color = data['sidebar_font_color']
                if (sidebar_font_color) {
                    $('#sidebar_font_color').val(sidebar_font_color);
                }

                $('#primary_color').val(data['primary_color']);
                $('#secondary_color').val(data['secondary_color']);
                $('#extra_color').val(data['extra_color']);
                $('#header_background_color').val(data['header_background_color']);
                $('#body_background_color').val(data['body_background_color']);
                $('#header_font_color').val(data['header_font_color']);
                $('#separator_color').val(data['separator_color']);

                var predefined_list_view_boolean = data['predefined_list_view_boolean']

                if (predefined_list_view_boolean) {
                    data['list_view_is_hover_row'] = false
                    $('#predefined_list_view_boolean').attr('checked', true);
                    $(".predefined_list_view_style").css("display", "table-row");
                    $(".is_row_color_hover").css("display", "none");
                    $("#list_view_is_hover_row").css("display", "none");
                    $("#list_view_border").css("display", "none");
                    $("#list_view_even_row_color").css("display", "none");
                    $("#list_view_odd_row_color").css("display", "none");
                    $("#list_view_hover_bg_color").css("display", "none");
                    $(".list_view_border_even_row_color").css("display","none");
                    $(".row_hover_odd_row_color").css("display","none");
                } else {
                    $('#predefined_list_view_boolean').attr('checked', false);
                    $(".predefined_list_view_style").css("display", "none");
                    $(".is_row_color_hover").css("display", "table-row");
                    $("#list_view_is_hover_row").css("display", "table-row");
                    $("#list_view_border").css("display", "table-row");
                    $("#list_view_even_row_color").css("display", "table-row");
                    $("#list_view_odd_row_color").css("display", "table-row");
                    $("#list_view_hover_bg_color").css("display", "table-row");
                    $(".list_view_border_even_row_color").css("display","table-row");
                    $(".row_hover_odd_row_color").css("display","table-row");
                }

                var predefined_list_view_style = data['predefined_list_view_style']
                if (predefined_list_view_style) {
                    $('#listview_table_id').find('#' + predefined_list_view_style).find('input[name="listview_style"]').attr('checked', true);
                }

                var list_view_border = data['list_view_border']
                if (list_view_border) {
                    $('#list_view_border').val(list_view_border);
                }
                var list_view_even_row_color = data['list_view_even_row_color']
                if (list_view_even_row_color) {
                    $('#list_view_even_row_color').val(list_view_even_row_color);
                }
                var list_view_odd_row_color = data['list_view_odd_row_color']
                if (list_view_odd_row_color) {
                    $('#list_view_odd_row_color').val(list_view_odd_row_color);
                }
                var list_view_is_hover_row = data['list_view_is_hover_row']
                if (list_view_is_hover_row) {
                    $('#list_view_is_hover_row').attr('checked', true);
                    $(".is_row_color_hover").css("display", "table-row");
                } else {
                    $('#list_view_is_hover_row').attr('checked', false);
                    $(".is_row_color_hover").css("display", "none");
                }
                var list_view_hover_bg_color = data['list_view_hover_bg_color']
                if (list_view_hover_bg_color) {
                    $('#list_view_hover_bg_color').val(list_view_hover_bg_color);
                }

                var login_page_style = data['login_page_style']
                if (login_page_style) {
                    $('#login_style_id').find('#' + login_page_style).find('input[name="login_style"]').attr('checked', true);
                }

                var login_page_box_color = data['login_page_box_color']
                if (login_page_box_color) {
                    $('#login_page_box_color').val(login_page_box_color);
                }
                var login_page_background_color = data['login_page_background_color']
                if (login_page_background_color) {
                    $('#login_page_background_color').val(login_page_background_color);
                }

                if (login_page_style == 'style_1') {

                    $(".login_bg_type").css("display", "block");
                    $(".login_bg_color").css("display", "block");
                    $(".login_box_color").css("display", "none");
                    $(".login_bg_img_title").css("display", "block");
                    $(".login_bg_img").css("display", "none");

                    $(".login_banner_img").css("display", "none");
                    $('.company_icon_image').css("display", "block");
                    $('.company_name_image').css("display", "block");
                    $('.login_page_style_with_comp_logo_tr').css("display", "none");
                    var login_page_background_type = data['login_page_background_type']
                    if (login_page_background_type == 'bg_img') {
                        $('#login_bg_img').attr('checked', true);
                        $('#login_page_background_color').css("display", "none");
                        $('#login_page_background_img').css("display", "block");
                    } else if (login_page_background_type == 'bg_color') {
                        $('#login_bg_color').attr('checked', true);
                        $('#login_page_background_color').css("display", "block");
                        $('#login_page_background_img').css("display", "none");
                    }

                }

                else if (login_page_style == 'style_2') {
                        $(".login_bg_type").css("display", "none");
                        $(".login_bg_color").css("display", "none");
                        $(".login_box_color").css("display", "block");
                        $(".login_bg_img_title").css("display", "none");
                        $(".login_bg_img").css("display", "none");
                        $(".login_box_color").val("#FFFFFF");

                        $(".login_banner_img").css("display", "block");
                        $('.company_icon_image').css("display", "none");
                        $('.company_name_image').css("display", "none");
                        $('.login_page_style_with_comp_logo_tr').css("display", "none");


                    }

                else  if (login_page_style == 'style_0' || login_page_style == 'style_3' ) {
                        $(".login_bg_type").css("display", "none");
                        $(".login_box_color").css("display", "none");
                        $(".login_bg_img").css("display", "none");
                        $(".login_bg_color").css("display", "none");
                        $(".login_bg_img_title").css("display", "none");
                        $(".login_banner_img").css("display", "none");
                        $('.company_icon_image').css("display", "none");
                        $('.company_name_image').css("display", "none");
                        $('.login_page_style_with_comp_logo_tr').css("display", "none");
                    }

                var progress_style = data['progress_style']
                if (progress_style) {
                    $('#progress_style').val(progress_style);
                }
                var progress_height = data['progress_height']
                if (progress_height) {
                    $('#progress_height').val(progress_height);
                }
                if (progress_style == 'style_1') {
                    $("#progress_color_height").css("display", "table-row");
                } else {
                    $("#progress_color_height").css("display", "none");
                }
                var progress_color = data['progress_color']
                if (progress_color) {
                    $('#progress_color').val(progress_color);
                }
                var form_element_style = data['form_element_style']
                if (form_element_style) {
                    $('#form_element_style_id').find('#' + form_element_style).find('input[name="form_element_style"]').attr('checked', true);
                }
                var breadcrumbs_style = data['breadcrumb_style']
                if (breadcrumbs_style) {
                    $('#breadcrumbs_style_id').find('#' + breadcrumbs_style).find('input[name="breadcrumbs_style"]').attr('checked', true);
                }
                var checkbox_style = data['checkbox_style']
                if (checkbox_style) {
                    $('#check_box_style_id').find('#' + checkbox_style).find('input[name="checkbox_style"]').attr('checked', true);
                }
                var radio_button_style = data['radio_style']
                if (radio_button_style) {
                    $('#radio_button_style_id').find('#' + radio_button_style).find('input[name="radio_button_style"]').attr('checked', true);
                }
                var scrollbar_style = data['scrollbar_style']
                if (scrollbar_style) {
                    $('#scrollbar_style_id').find('#' + scrollbar_style).find('input[name="scrollbar_style"]').attr('checked', true);
                }
                var kanban_style = data['kanban_box_style']
                if (kanban_style) {
                    $('#kanban_style_id').find('#' + kanban_style).find('input[name="kanban_style"]').attr('checked', true);
                }
                var font_icon_style = data['backend_all_icon_style']
                if (font_icon_style) {
                    $('#font_icon_style_id').find('#' + font_icon_style).find('input[name="font_icon_style"]').attr('checked', true);
                }

            });
        }
        onWillStart(this.onWillStart);
        
        }

   async onWillStart() {
//        TODO
        /*this.is_group_theme_configuration_user = await this.user.hasGroup("sh_entmate_theme.group_theme_configuration");*/
        this.is_group_theme_configuration_user = true
    }

    _click_sh_theme_design(ev){
            if ($(ev.currentTarget.parentElement.getElementsByClassName('collapse')).css('display') == 'none')
            {
                $(ev.currentTarget.parentElement.getElementsByClassName('collapse')).slideDown('slow')
            }else{
                $(ev.currentTarget.parentElement.getElementsByClassName('collapse')).slideUp(600)
            }
        }

    _click_sh_theme_design(ev){
            if ($(ev.currentTarget.parentElement.getElementsByClassName('collapse')).css('display') == 'none')
            {
                $(ev.currentTarget.parentElement.getElementsByClassName('collapse')).slideDown('slow')
            }else{
                $(ev.currentTarget.parentElement.getElementsByClassName('collapse')).slideUp(600)
            }
        }

    _click_theme_configuration(){
        if ($('.backmate_theme_layout').length) {

				if ($('.sh_theme_model').length) {

					$('.backmate_theme_layout').removeClass('sh_theme_model');
					//	$('.o_action_manager').css("margin-right" , '0px');
				} else {
					$('.backmate_theme_layout').addClass('sh_theme_model');

					var radioValue = $("input[name='body_background_type']:checked").val();
					if (radioValue == 'bg_color') {
						$('#body_background_color').css("display", "block");
						$('#body_background_img').css("display", "none");
					} else {
						$('#body_background_color').css("display", "none");
						$('#body_background_img').css("display", "block");
					}

					var radioValue = $("input[name='header_background_type']:checked").val();
                    if (radioValue == 'bg_color') {
                        $('#header_background_color').css("display", "block");
                        $('#header_background_img').css("display", "none");
                    } else {
                        $('#header_background_color').css("display", "none");
                        $('#header_background_img').css("display", "block");
                    }

					var radioValue = $("input[name='sidebar_background_style']:checked").val();
					if (radioValue == 'color') {
						$('#sidebar_background_color').css("display", "block");
						$('#sidebar_background_img').css("display", "none");
					} else {
						$('#sidebar_background_color').css("display", "none");
						$('#sidebar_background_img').css("display", "block");
					}
				}
			}
    }

    async _click_sidebar_style_box(ev){
        var sidebar_style = $(ev.currentTarget).attr('id');
        $.each($('.theme_style_box'), function (event) {
            $(event).removeClass('active');
            $(event).find('input[name="themeStyle"]').attr('checked', false);
        })
        $(ev.currentTarget).addClass('active');
        $(ev.currentTarget).find('input[name="themeStyle"]').attr('checked', true);
        var result = await this.orm.write("sh.ent.theme.config.settings", [1], {
         sidebar_img : sidebar_style});
         if (result){
            location.reload();
         }
    }

    _on_change_body_font_family(ev){
        var body_font_family = $('#body_font_family').val();
        if (body_font_family == 'custom_google_font') {
            $("#body_google_font_family").css("display", "block");
            $("#body_google_font_family_label").css("display", "block");
        } else {
            $("#body_google_font_family").css("display", "none");
            $("#body_google_font_family_label").css("display", "none");
        }
    }

    _click_header_background_type(ev){
        var radioValue = $("input[name='header_background_type']:checked").val();
        if (radioValue == 'bg_color') {
            $('#header_background_color').css("display", "block");
            $('#header_background_img').css("display", "none");
        } else {
            $('#header_background_color').css("display", "none");
            $('#header_background_img').css("display", "block");
        }
    }

    _click_body_background_type(ev){
        var radioValue = $("input[name='body_background_type']:checked").val();
        if (radioValue == 'bg_color') {
            $('#body_background_color').css("display", "block");
            $('#body_background_img').css("display", "none");
        } else {
            $('#body_background_color').css("display", "none");
            $('#body_background_img').css("display", "block");
        }

    }

    async _click_separator_style_box(ev){
        var separator_style = $(ev.currentTarget).attr('id');
        $.each($('.theme_style_box'), function (event) {
            $(event).removeClass('active');
            $(event).find('input[name="separator_style"]').attr('checked', false);
        })
        $(ev.currentTarget).addClass('active');
        $(ev.currentTarget).find('input[name="separator_style"]').attr('checked', true);
        var result = await this.orm.write("sh.ent.theme.config.settings", [1], {
         separator_style : separator_style});
         if (result){
            location.reload();
         }

    }

    async _click_button_style_box(ev){
        var button_style = $(ev.currentTarget).attr('id');
        $.each($('.theme_style_box'), function (event) {
            $(event).removeClass('active');
            $(event).find('input[name="button_style"]').attr('checked', false);
        })
        $(ev.currentTarget).addClass('active');
        $(ev.currentTarget).find('input[name="button_style"]').attr('checked', true);
        var result = await this.orm.write("sh.ent.theme.config.settings", [1], {
         button_style : button_style});
         if (result){
            location.reload();
         }

    }

    async _click_app_icon_style_box(ev){
        var app_icon_style = $(ev.currentTarget).attr('id');
        $.each($('.theme_style_box'), function (event) {
            $(event).removeClass('active');
            $(event).find('input[name="app_icon_style"]').attr('checked', false);
        })
        $(ev.currentTarget).addClass('active');
        $(ev.currentTarget).find('input[name="app_icon_style"]').attr('checked', true);
        var result = await this.orm.write("sh.ent.theme.config.settings", [1], {
         app_icon_style : app_icon_style});
         if (result){
            location.reload();
         }

    }

    async _click_tab_style_box(ev){
        var tab_style = $(ev.currentTarget).attr('id');
        $.each($('.theme_style_box'), function (event) {
            $(event).removeClass('active');
            $(event).find('input[name="tab_style"]').attr('checked', false);
        })
        $(ev.currentTarget).addClass('active');
        $(ev.currentTarget).find('input[name="tab_style"]').attr('checked', true);
        var result = await this.orm.write("sh.ent.theme.config.settings", [1], {
         horizontal_tab_style : tab_style});
         if (result){
            location.reload();
         }

    }

    async _click_predefined_list_view_boolean(ev){
        var predefined_list_view_boolean = $("#predefined_list_view_boolean").prop("checked");
        if (predefined_list_view_boolean) {
            $('#predefined_list_view_boolean').attr('checked', true);
            $(".predefined_list_view_style").css("display", "table-row");
            $(".is_row_color_hover").css("display", "none");
            $("#list_view_is_hover_row").css("display", "none");
            $("#list_view_border").css("display", "none");
            $("#list_view_even_row_color").css("display", "none");
            $("#list_view_odd_row_color").css("display", "none");
            $("#list_view_hover_bg_color").css("display", "none");
            $(".list_view_border_even_row_color").css("display","none");
            $(".row_hover_odd_row_color").css("display","none");
        } else {
            $('#predefined_list_view_boolean').attr('checked', false);
            $(".predefined_list_view_style").css("display", "none");
            $(".is_row_color_hover").css("display", "table-row");
            $("#list_view_is_hover_row").css("display", "table-row");
            $("#list_view_border").css("display", "table-row");
            $("#list_view_even_row_color").css("display", "table-row");
            $("#list_view_odd_row_color").css("display", "table-row");
            $("#list_view_hover_bg_color").css("display", "table-row");
            $(".list_view_border_even_row_color").css("display","table-row");
            $(".row_hover_odd_row_color").css("display","table-row");
            var list_view_is_hover_row = $("#list_view_is_hover_row").prop("checked");
            if (!list_view_is_hover_row){
                $(".is_row_color_hover").css("display", "none");
            }
        }
    }

    async _click_list_view_is_hover_row(ev){
        var list_view_is_hover_row = $("#list_view_is_hover_row").prop("checked");
        if (list_view_is_hover_row) {
            $(".is_row_color_hover").css("display", "table-row");
        } else {
            $(".is_row_color_hover").css("display", "none");
        }
    }

    async _click_login_style_box(ev){
        var login_style = $(ev.currentTarget).attr('id');
        $("#login_style_id").find(".theme_style_box").removeClass('active')
        $("#login_style_id").find(".theme_style_box").find('input[name="login_style"]').attr('checked', false);
        $(ev.currentTarget).addClass('active');
        $(ev.currentTarget).find('input[name="login_style"]').attr('checked', true);

         if (login_style == 'style_1') {

                                $(".login_bg_type").css("display", "block");
                                $(".login_box_color").css("display", "none");
                                $(".login_bg_img_title").css("display", "block");

                                $(".login_bg_img_title").css("display", "block");
                                $("#login_bg_img").attr('checked', true);
                                $(".login_bg_img").css("display", 'block');
                                $(".login_bg_color").css("display", "none");


                                $(".login_banner_img").css("display", "none");
                                $('.company_icon_image').css("display", "block");
                                $('.company_name_image').css("display", "block");
                                $('.login_page_style_with_comp_logo_tr').css("display", "none");


                            }

         else if (login_style == 'style_2') {
            $(".login_bg_type").css("display", "none");
            $(".login_bg_color").css("display", "none");
            $(".login_box_color").css("display", "block");
            $(".login_bg_img_title").css("display", "none");
            $(".login_bg_img").css("display", "none");
            $(".login_box_color").val("#FFFFFF");

            $(".login_banner_img").css("display", "block");
            $('.company_icon_image').css("display", "none");
            $('.company_name_image').css("display", "none");
            $('.login_page_style_with_comp_logo_tr').css("display", "none");


        }

         else  if (login_style == 'style_0' || login_style == 'style_3' ) {
                                $(".login_bg_type").css("display", "none");
                                $(".login_box_color").css("display", "none");
                                $(".login_bg_img").css("display", "none");
                                $(".login_bg_color").css("display", "none");
                                $(".login_bg_img_title").css("display", "none");
                                $(".login_banner_img").css("display", "none");
                                $('.company_icon_image').css("display", "none");
                                $('.company_name_image').css("display", "none");
                                $('.login_page_style_with_comp_logo_tr').css("display", "none");
                            }
    }

    _click_login_page_background_type(ev){
        var radioValue = $("input[name='login_page_background_type']:checked").val();
        if (radioValue == 'bg_color') {
            $('#login_page_background_color').css("display", "block");
            $('#login_page_background_img').css("display", "none");
        } else {
            $('#login_page_background_color').css("display", "none");
            $('#login_page_background_img').css("display", "block");
        }
    }

   async _click_progressbar_style_box(ev){
        
        var progress_style = $("#progress_style").val();
        if (progress_style == 'style_1') {
            $("#progress_color_height").css("display", "table-row");
        } else {
            $("#progress_color_height").css("display", "none");
        }
    }

   async _click_form_element_style_box(ev){
        var form_element_style = $(ev.currentTarget).attr('id');
        $.each($('.theme_style_box'), function (event) {
            $(event).removeClass('active');
            $(event).find('input[name="form_element_style"]').attr('checked', false);
        })
        $(ev.currentTarget).addClass('active');
        $(ev.currentTarget).find('input[name="form_element_style"]').attr('checked', true);
        var result = await this.orm.write("sh.ent.theme.config.settings", [1], {
         form_element_style : form_element_style});
         if (result){
            location.reload();
         }
   }

   async _click_breadcrumbs_style_box(ev){
        var breadcrumbs_style = $(ev.currentTarget).attr('id');
        $.each($('.theme_style_box'), function (event) {
            $(event).removeClass('active');
            $(event).find('input[name="breadcrumbs_style"]').attr('checked', false);
        })
        $(ev.currentTarget).addClass('active');
        $(ev.currentTarget).find('input[name="breadcrumbs_style"]').attr('checked', true);
        var result = await this.orm.write("sh.ent.theme.config.settings", [1], {
         breadcrumb_style : breadcrumbs_style});
         if (result){
            location.reload();
         }
   }

   async _click_checkbox_style_box(ev){
        var checkbox_style = $(ev.currentTarget).attr('id');
        $.each($('.theme_style_box'), function (event) {
            $(event).removeClass('active');
            $(event).find('input[name="checkbox_style"]').attr('checked', false);
        })
        $(ev.currentTarget).addClass('active');
        $(ev.currentTarget).find('input[name="checkbox_style"]').attr('checked', true);
        var result = await this.orm.write("sh.ent.theme.config.settings", [1], {
         checkbox_style : checkbox_style});
         if (result){
            location.reload();
         }

   }

   async _click_radio_button_style_box(ev){
        var radio_button_style = $(ev.currentTarget).attr('id');
        $.each($('.theme_style_box'), function (event) {
            $(event).removeClass('active');
            $(event).find('input[name="radio_button_style"]').attr('checked', false);
        })
        $(ev.currentTarget).addClass('active');
        $(ev.currentTarget).find('input[name="radio_button_style"]').attr('checked', true);
        var result = await this.orm.write("sh.ent.theme.config.settings", [1], {
         radio_style : radio_button_style});
         if (result){
            location.reload();
         }
   }

   async _click_scrollbar_style_box(ev){
        var scrollbar_style = $(ev.currentTarget).attr('id');
        $.each($('.theme_style_box'), function (event) {
            $(event).removeClass('active');
            $(event).find('input[name="scrollbar_style"]').attr('checked', false);
        })
        $(ev.currentTarget).addClass('active');
        $(ev.currentTarget).find('input[name="scrollbar_style"]').attr('checked', true);
        var result = await this.orm.write("sh.ent.theme.config.settings", [1], {
         scrollbar_style : scrollbar_style});
         if (result){
            location.reload();
         }
   }

   async _click_kanban_style_box(ev){
        var kanban_style = $(ev.currentTarget).attr('id');
        $.each($('.theme_style_box'), function (event) {
            $(event).removeClass('active');
            $(event).find('input[name="kanban_style"]').attr('checked', false);
        })
        $(ev.currentTarget).addClass('active');
        $(ev.currentTarget).find('input[name="kanban_style"]').attr('checked', true);
        var result = await this.orm.write("sh.ent.theme.config.settings", [1], {
         kanban_box_style : kanban_style});
         if (result){
            location.reload();
         }
   }

   async _click_font_icon_style_box(ev){
        var font_icon_style = $(ev.currentTarget).attr('id');
        $.each($('.theme_style_box'), function (event) {
            $(event).removeClass('active');
            $(event).find('input[name="font_icon_style"]').attr('checked', false);
        })
        $(ev.currentTarget).addClass('active');
        $(ev.currentTarget).find('input[name="font_icon_style"]').attr('checked', true);
        var result = await this.orm.write("sh.ent.theme.config.settings", [1], {
         backend_all_icon_style : font_icon_style});
         if (result){
            location.reload();
         }
   }

   async _click_listview_style_box(ev){
        var listview_style = $(ev.currentTarget).attr('id');
        $("#listview_table_id").find(".theme_style_box").removeClass('active')
        $("#listview_table_id").find(".theme_style_box").find('input[name="listview_style"]').attr('checked', false);
        $(ev.currentTarget).addClass('active');
        $(ev.currentTarget).find('input[name="listview_style"]').attr('checked', true);
   }

   async _click_save_color(ev){
         var sidebar_background_color = $('#sidebar_bg_color').val();
         var sidebar_font_color = $('#sidebar_font_color').val();

         var primary_color = $('#primary_color').val();
         var secondary_color = $('#secondary_color').val();
         var extra_color = $('#extra_color').val();
         var body_background_type = $("input[name='body_background_type']:checked").val();
         var header_background_type = $("input[name='header_background_type']:checked").val();

         var separator_color = $('#separator_color').val();

        var is_sticky_form = $("#is_sticky_form").prop("checked");
        var is_sticky_list = $("#is_sticky_list").prop("checked");
        var is_sticky_list_inside_form = $("#is_sticky_list_inside_form").prop("checked");
        var is_sticky_pivot = $("#is_sticky_pivot").prop("checked");

        var predefined_list_view_boolean = $("#predefined_list_view_boolean").prop("checked");
        var predefined_list_view_style = $("input[name='listview_style']:checked").val();
        var list_view_border = $("#list_view_border").val();
        var list_view_even_row_color = $("#list_view_even_row_color").val();
        var list_view_odd_row_color = $("#list_view_odd_row_color").val();
        var list_view_is_hover_row = $("#list_view_is_hover_row").prop("checked");
        var list_view_hover_bg_color = $("#list_view_hover_bg_color").val();

        var login_style = $("input[name='login_style']:checked").val();
        var login_page_background_type = $("input[name='login_page_background_type']:checked").val();
        var login_page_box_color = $("#login_page_box_color").val();
        var login_page_background_color = $("#login_page_background_color").val();

        var progress_style = $("#progress_style").val();
        var progress_height = $("#progress_height").val();
        var progress_color = $("#progress_color").val();

         var result = await this.orm.write("sh.ent.theme.config.settings", [1], {
             sidebar_color : sidebar_background_color,
             sidebar_font_color : sidebar_font_color,
             primary_color : primary_color,
             secondary_color : secondary_color,
             extra_color : extra_color,
             body_background_type : body_background_type,
             header_background_type : header_background_type,
             separator_color : separator_color,
             is_sticky_form : is_sticky_form,
             is_sticky_list : is_sticky_list,
             is_sticky_list_inside_form : is_sticky_list_inside_form,
             is_sticky_pivot : is_sticky_pivot,
             predefined_list_view_boolean : predefined_list_view_boolean,
             predefined_list_view_style : predefined_list_view_style,
             list_view_border : list_view_border,
             list_view_even_row_color : list_view_even_row_color,
             list_view_odd_row_color : list_view_odd_row_color,
             list_view_is_hover_row : list_view_is_hover_row,
             list_view_hover_bg_color : list_view_hover_bg_color,
             login_page_style : login_style,
             login_page_background_type : login_page_background_type,
             login_page_background_color : login_page_background_color,
             login_page_box_color : login_page_box_color,
             progress_style : progress_style,
             progress_height : progress_height,
             progress_color : progress_color,

         });

         if (result){
            location.reload();
         }

         /*save image*/
        var form = $('#body_background_img')[0];
        var data = new FormData(form);
        $.ajax({
            type: "POST",
            enctype: 'multipart/form-data',
            url: "/api/upload/multi",
            data: data,
            processData: false,
            contentType: false,
            cache: false,
            timeout: 600000,
            success: function (data) {

                if(data){
                    setTimeout(function () {
                        location.reload();

                    }, 5000);
                }

            },
            error: function (e) {

                console.log("ERROR : ", e);

            }
        });

        var form = $('#header_background_img')[0];
        var data = new FormData(form);
        $.ajax({
            type: "POST",
            enctype: 'multipart/form-data',
            url: "/api/upload/multi",
            data: data,
            processData: false,
            contentType: false,
            cache: false,
            timeout: 600000,
            success: function (data) {
                if(data){
                    setTimeout(function () {
                        location.reload();
                    }, 5000);
                }

            },
            error: function (e) {

                console.log("ERROR : ", e);

            }
        });

       var login_page_background_img = $('#login_page_background_img')[0];
        var data3 = new FormData(login_page_background_img);
        $.ajax({
            type: "POST",
            enctype: 'multipart/form-data',
            url: "/api/upload/multi",
            data: data3,
            processData: false,
            contentType: false,
            cache: false,
            timeout: 600000,
            success: function (data) {

                if(data){
                    setTimeout(function () {
                        location.reload();

                    }, 5000);
                }
            },
            error: function (e) {

                console.log("ERROR : ", e);

            }
        });

    }

    }

registry.category("systray").add("sh_entmate_theme.ThemeConfigurationTemplate", { Component: ThemeConfigurationTemplate });


