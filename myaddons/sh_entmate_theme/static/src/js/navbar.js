/** @odoo-module **/
import { MenuDropdown, MenuItem, NavBar } from '@web/webclient/navbar/navbar';
import { isMobileOS } from "@web/core/browser/feature_detection";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";

import { jsonrpc } from "@web/core/network/rpc_service";
import { session } from "@web/session";
import { onWillStart } from "@odoo/owl";
import { onMounted } from "@odoo/owl";

var app_icon_style = 'style_1';
var backend_all_icon_style = 'backend_fontawesome_icon';
var enable_multi_tab = false


patch(NavBar.prototype, {
    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    /**
     * @override
     */

    setup() {
            super.setup();
            this.orm = useService("orm");
            this.searchTheme()

            enable_multi_tab = session.sh_enable_multi_tab
            onMounted(() => {
                if (enable_multi_tab){
                   this.addmultitabtags()
                }
            });
        },

     async searchTheme() {
            const data = await this.orm.searchRead(
            "sh.ent.theme.config.settings",
            [],
            ["app_icon_style","backend_all_icon_style"]
            );
             if (data) {
                    if (data[0]['app_icon_style']) {
                        app_icon_style = data[0]['app_icon_style'];
                    }
                    if (data[0]['backend_all_icon_style']) {
                        backend_all_icon_style = data[0]['backend_all_icon_style'];
                    }
                }
     },

    onNavBarDropdownItemSelection(menu) {
       if (enable_multi_tab){
            if(window.event.shiftKey){
                this._createMultiTab(menu)
//                localStorage.setItem("sh_add_tab",1)
            }else{
//                localStorage.setItem("sh_add_tab",0)
            }
       }
        if(this.websiteCustomMenus){
            const websiteMenu = this.websiteCustomMenus.get(menu.xmlid);
            if (websiteMenu) {
                return this.websiteCustomMenus.open(menu);
            }
        }
       
        if (menu) {
            this.menuService.selectMenu(menu);
        }
    },
    // NEW 28TH MARCH MULTITAB CODE 
    _createMultiTab: function (ev) {
        var tab_name = ev.name
        var url = '#menu_id='+ev.id + '&action='+ ev.actionID
        var actionId = ev.actionID
        var menuId = ev.id
        var menu_xmlid = ev.xmlid
        var self = this
        localStorage.setItem('LastCreatedTab',actionId)

        jsonrpc('/add/mutli/tab', {
                'name':tab_name,
                'url':url,
                'actionId':actionId,
                'menuId':menuId,
                'menu_xmlid':menu_xmlid,
            }).then((rec) => {
                self.addmultitabtags(ev)
            });
     },

    addmultitabtags: async function (ev) {
        var self = this
        var rec = await jsonrpc('/get/mutli/tab', {});
        if (rec){
                $('.multi_tab_section').empty()
                $.each(rec, function( key, value ) {
                    var tab_tag = '<div class="d-flex justify-content-between multi_tab_div align-items-center"><a href="'+ value.url +'"'+' class="flex-fill" data-xml-id="'+ value.menu_xmlid +'" data-menu="'+ value.menuId +'" data-action-id="'+ value.actionId +'" multi_tab_id="'+value.id+'" multi_tab_name="'+value.name+'"><span>'+value.name+'</span></a><span class="remove_tab ml-4">X</span></div>'
                    $('.multi_tab_section').append(tab_tag)
                })
                var ShstoredActionId = sessionStorage.getItem("sh_current_action_id");
                var ShstoredAction = sessionStorage.getItem("sh_current_action");
                if (ShstoredActionId){
                    var TabDiv = $('.multi_tab_section .multi_tab_div');
                    var ActiveMenu = TabDiv.find('a[data-action-id="'+ ShstoredActionId +'"]');
                    ActiveMenu.parent().addClass('tab_active')
                }

                if (ev) {
                    var actionId = ev.actionID
                    var menu_xmlid = ev.xmlid
                    if(localStorage.getItem('LastCreatedTab')){
                        var target = '.multi_tab_section .multi_tab_div a[data-action-id="'+ localStorage.getItem('LastCreatedTab') +'"]'
                        $(target).parent().addClass('tab_active')
                        localStorage.removeItem('LastCreatedTab')
                    } else {
                        var target = '.multi_tab_section .multi_tab_div a[data-xml-id="'+ menu_xmlid +'"]'
                        $(target).parent().addClass('tab_active')
                    }
                }
                $('body').addClass("multi_tab_enabled");
            } else {
                $('body').removeClass("multi_tab_enabled");
            }
        $('.multi_tab_section .remove_tab').on('click', function (ev) {
                    self._RemoveTab(ev)
                });
        $('.multi_tab_section .multi_tab_div a').on('click', function (ev) {
                    self._TabClicked(ev)
                });
        },

    _RemoveTab: function (ev) {
        var self = this
        var multi_tab_id = $(ev.target).parent().find('a').attr('multi_tab_id')
        jsonrpc('/remove/multi/tab', {
            'multi_tab_id':multi_tab_id,
        }).then(function(rec) {
            if (rec){
                if(rec['removeTab']){
                    $(ev.target).parent().remove()
                    var FirstTab = $('.multi_tab_section').find('.multi_tab_div:first-child')
                    if(FirstTab.length){
                        $(FirstTab).find('a')[0].click()
                        $(FirstTab).addClass('tab_active')
                    }
                }
                if(rec['multi_tab_count'] == 0){
                    $('body').removeClass("multi_tab_enabled");
                }
            }
        });
        },

    _TabClicked: function (ev){
    localStorage.setItem("TabClick", true);
    localStorage.setItem("TabClickTilteUpdate", true);
    if($(ev.target).data('action-id')){
    $('.multi_tab_section').find('.tab_active').removeClass('tab_active');
    $(ev.target).parent().addClass('tab_active')
    console.log('$(ev.target).parent()',$(ev.target).parent())
    }
    else{
    if($(ev.currentTarget).data('action-id')){
        $('.multi_tab_section').find('.tab_active').removeClass('tab_active');
        $(ev.currentTarget).parent().addClass('tab_active')
        console.log('$(ev.target).parent()',$(ev.target).parent())
    }
    }
    },
    // NEW 28TH MARCH MULTITAB CODE 

    onNavBarDropdownItemClick(ev) {
        if(ev.shiftKey){
            localStorage.setItem("sh_add_tab",1)
        }else{
            localStorage.setItem("sh_add_tab",0)
        }
    },
    getAppClassName(app){
        var app_name = app.xmlid
        return app_name.replaceAll('.', '_')
    },
    getIconStyle() {
        return app_icon_style;
    },
    getBackend_icon(){
        return backend_all_icon_style;
    },
    isMobile(ev) {
        return isMobileOS;
    },
    click_secondary_submenu(ev) {
        if (isMobileOS) {
            $(".sh_sub_menu_div").addClass("o_hidden");
        }

        $(".o_menu_sections").removeClass("show")
    },
    click_close_submenu(ev) {
        $(".sh_sub_menu_div").addClass("o_hidden");
        $(".o_menu_sections").removeClass("show")
    },
    click_mobile_toggle(ev) {
        $(".sh_sub_menu_div").removeClass("o_hidden");
    },
    click_app_toggle(ev) {
        /* close pop-ups */
        $(".todo_layout").removeClass("sh_theme_model")
        $('.sh_wqm_quick_menu_submenu_list_cls').css('display','none')
        $('.o_user_bookmark_menu').removeClass('bookmark_active')
        $('.backmate_theme_layout').removeClass("sh_theme_model");
        $('.sh_calc_util').removeClass("active")
        $(".sh_calc_results").html("");

        if($(".sh_entmate_theme_appmenu_div").hasClass("sh_first_load")){
            $(".sh_entmate_theme_appmenu_div").removeClass("show")
            $(".sh_entmate_theme_appmenu_div").removeClass("sh_first_load")
        }
        if ($(".sh_entmate_theme_appmenu_div").hasClass("show")) {
            $("body").removeClass("sh_sidebar_background_enterprise");
            $(".sh_search_container").css("display", "none");

            $(".sh_entmate_theme_appmenu_div").removeClass("show")
            $(".o_action_manager").removeClass("d-none");
            $(".o_menu_brand").css("display", "block");
            $(".full").removeClass("sidebar_arrow");
            $(".o_menu_sections").css("display", "flex");
        } else {
            $(".sh_entmate_theme_appmenu_div").addClass("show")
            $("body").addClass("sh_sidebar_background_enterprise");
            $(".sh_entmate_theme_appmenu_div").css("opacity", "1");
            // 24-3-2023 // 
            // to fix issue of list view column width//
            // $(".o_action_manager").addClass("d-none");
            $(".full").addClass("sidebar_arrow");
            $(".o_menu_brand").css("display", "none");
            $(".o_menu_sections").css("display", "none");
        }
    },
});


