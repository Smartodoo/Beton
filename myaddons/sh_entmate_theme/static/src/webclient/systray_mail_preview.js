/** @odoo-module **/

import { registerPatch } from '@mail/model/model_core';

// ChannelPreviewView
registerPatch({
    name: 'ChannelPreviewView',
    recordMethods: {
        /**
         * @param {MouseEvent} ev
         */
        onClick(ev) {
            if($("body").hasClass("sh_sidebar_background_enterprise")){
                $("body").removeClass("sh_sidebar_background_enterprise")
            }
            if($(".sh_entmate_theme_appmenu_div").hasClass("show")){
                $(".sh_entmate_theme_appmenu_div").removeClass("show")
            }
            return this._super(ev)
        },
    }
});

// NotificationGroupView 
registerPatch({
    name: 'NotificationGroupView',
    recordMethods: {
        /**
         * @param {MouseEvent} ev
         */
        onClick(ev) {
            if($("body").hasClass("sh_sidebar_background_enterprise")){
                $("body").removeClass("sh_sidebar_background_enterprise")
            }
            if($(".sh_entmate_theme_appmenu_div").hasClass("show")){
                $(".sh_entmate_theme_appmenu_div").removeClass("show")
            }
            return this._super(ev)
        },
    }
});

// ThreadNeedactionPreviewView

registerPatch({
    name: 'ThreadNeedactionPreviewView',
    recordMethods: {
        /**
         * @param {MouseEvent} ev
         */
        onClick(ev) {
            if($("body").hasClass("sh_sidebar_background_enterprise")){
                $("body").removeClass("sh_sidebar_background_enterprise")
            }
            if($(".sh_entmate_theme_appmenu_div").hasClass("show")){
                $(".sh_entmate_theme_appmenu_div").removeClass("show")
            }
            return this._super(ev)
        },
    }
});


// ActivityGroupView

registerPatch({
    name: 'ActivityGroupView',
    recordMethods: {
        /**
         * @param {MouseEvent} ev
         */
        onClick(ev) {
            if($("body").hasClass("sh_sidebar_background_enterprise")){
                $("body").removeClass("sh_sidebar_background_enterprise")
            }
            if($(".sh_entmate_theme_appmenu_div").hasClass("show")){
                $(".sh_entmate_theme_appmenu_div").removeClass("show")
            }
            this._super(ev)
        },

        onClickFilterButton(ev) {
            if($("body").hasClass("sh_sidebar_background_enterprise")){
                $("body").removeClass("sh_sidebar_background_enterprise")
            }
            if($(".sh_entmate_theme_appmenu_div").hasClass("show")){
                $(".sh_entmate_theme_appmenu_div").removeClass("show")
            }
            this._super(ev)
        },
    }
});