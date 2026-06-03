/** @odoo-module **/

import { ListController } from "@web/views/list/list_controller";
import { patch } from "@web/core/utils/patch";

/**
 * Filtre le menu Imprimer sur res.partner selon le type de partenaire.
 * - Vue filtrée sur « Client »      → masque les impressions fournisseur
 * - Vue filtrée sur « Fournisseur »  → masque les impressions client
 * - Aucun filtre                     → affiche tout
 */

function getPartnerTypeFromDomain(domain) {
    for (const leaf of domain) {
        if (
            Array.isArray(leaf) &&
            leaf[0] === "type_partenaire_beton" &&
            leaf[1] === "="
        ) {
            return leaf[2];
        }
    }
    return null;
}

patch(ListController.prototype, {
    get actionMenuItems() {
        const menuItems = super.actionMenuItems;
        if (this.props.resModel !== "res.partner") {
            return menuItems;
        }
        const domain = this.model.root.domain || [];
        const partnerType = getPartnerTypeFromDomain(domain);
        if (!partnerType || !menuItems.print) {
            return menuItems;
        }
        if (partnerType === "client") {
            menuItems.print = menuItems.print.filter((item) => {
                return !(item.name || "").toLowerCase().includes("fournisseur");
            });
        } else if (partnerType === "fournisseur") {
            menuItems.print = menuItems.print.filter((item) => {
                return !(item.name || "").toLowerCase().includes("client");
            });
        }
        return menuItems;
    },
});
