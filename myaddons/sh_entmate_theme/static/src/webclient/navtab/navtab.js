/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";

export class NavTab extends Component {
    setup() {
        super.setup();
        this.actionService = useService("action");
        }
    }

NavTab.template = 'sh_entmate_theme.NavTab';

