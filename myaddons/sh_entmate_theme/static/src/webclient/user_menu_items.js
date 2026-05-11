/** @odoo-module **/

import { registry } from "@web/core/registry";
import { preferencesItem } from "@web/webclient/user_menu/user_menu_items";

export function ShProfilePreference(env)  {
    return Object.assign(
        {}, 
        preferencesItem(env),
        {
            callback: async function () {
                const actionDescription = await env.services.orm.call("res.users", "action_get");
                actionDescription.res_id = env.services.user.userId;
                env.services.action.doAction(actionDescription);
                setTimeout(function () {
                    if($("body").hasClass("sh_sidebar_background_enterprise")){
                        $("body").removeClass("sh_sidebar_background_enterprise")
                    }
                    if($(".sh_entmate_theme_appmenu_div").hasClass("show")){
                        $(".sh_entmate_theme_appmenu_div").removeClass("show")
                    }
                }, 1000);
            },
        }
    );
}

registry.category("user_menuitems").add('profile', ShProfilePreference, { force: true })
