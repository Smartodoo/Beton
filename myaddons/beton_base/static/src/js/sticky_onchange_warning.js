/** @odoo-module **/

import { RelationalModel } from "@web/model/relational_model/relational_model";
import { patch } from "@web/core/utils/patch";

patch(RelationalModel.prototype, {
    async _onchange(config, params) {
        const origAdd = this.notification.add;
        const notifService = this.notification;
        // Rendre les notifications onchange de type warning persistantes (sticky)
        this.notification = Object.assign(Object.create(notifService), {
            add(message, options = {}) {
                if (options.type === "warning") {
                    options.sticky = true;
                }
                return origAdd.call(notifService, message, options);
            },
        });
        try {
            return await super._onchange(config, params);
        } finally {
            this.notification = notifService;
        }
    },
});
