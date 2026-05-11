/* @odoo-module */

import { Component, useState, xml } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { session } from "@web/session";

export class NightMode extends Component {
       static template = "NightModeTemplate";

       setup() {
            this.orm = useService("orm");
            this.onWillStart()
        }

       async onWillStart() {
        if ($('.o_web_client').hasClass('sh_night_mode')) {
            this.day_mode = false;
        } else {
            this.day_mode = true;
        }

        const data = await this.orm.searchRead(
            "res.users",
            [['id', '=', session.uid]],
            ["sh_enable_night_mode"]
            );
            if (data) {
                if (! data[0].sh_enable_night_mode) {
                    $('.o_night_mode').hide();
                    }
            }
        }

        _click_moon_button() {
			localStorage.setItem("is_night_mode", "t");
			$('.o_web_client').addClass('sh_night_mode');
			$('#moon_button').css("display", "none");
			$('#sun_button').css("display", "inline-flex");
		}

		_click_sun_button() {
			localStorage.setItem("is_night_mode", "f");
			$('.o_web_client').removeClass('sh_night_mode');
			$('#moon_button').css("display", "inline-flex");
			$('#sun_button').css("display", "none");
		}

}

registry.category("systray").add("NightModeTemplate", { Component: NightMode });