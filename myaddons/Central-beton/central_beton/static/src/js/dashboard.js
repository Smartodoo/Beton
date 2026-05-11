/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onWillStart, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

class CentralBetonDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            fabricationsToday: 0,
            volumeToday: 0,
            livraisonsEnCours: 0,
            camionsDisponibles: 0,
            ncOuvertes: 0,
            essaisEnAttente: 0,
        });

        onWillStart(async () => {
            await this.loadData();
        });
    }

    async loadData() {
        const today = new Date().toISOString().split('T')[0];

        // Productions today (MRP)
        const productions = await this.orm.searchCount("mrp.production", [
            ["date_start", ">=", today],
            ["is_beton_production", "=", true],
            ["state", "in", ["progress", "to_close", "done"]],
        ]);
        this.state.fabricationsToday = productions;

        // Volume today
        const prodData = await this.orm.searchRead(
            "mrp.production",
            [
                ["date_start", ">=", today],
                ["is_beton_production", "=", true],
                ["state", "=", "done"],
            ],
            ["volume_produit"]
        );
        this.state.volumeToday = prodData.reduce((sum, p) => sum + p.volume_produit, 0);

        // Livraisons en cours
        this.state.livraisonsEnCours = await this.orm.searchCount(
            "central.beton.livraison",
            [["state", "in", ["charge", "en_route", "sur_site"]]]
        );

        // Camions disponibles
        this.state.camionsDisponibles = await this.orm.searchCount(
            "fleet.vehicle",
            [["is_camion_malaxeur", "=", true], ["etat_camion", "=", "disponible"]]
        );

        // NC ouvertes
        this.state.ncOuvertes = await this.orm.searchCount(
            "central.beton.non.conformite",
            [["state", "in", ["ouverte", "en_traitement"]]]
        );

        // Essais en attente
        this.state.essaisEnAttente = await this.orm.searchCount(
            "central.beton.essai",
            [["conforme", "=", "en_attente"]]
        );
    }

    onClickFabrications() {
        this.action.doAction("central_beton.action_beton_production");
    }

    onClickLivraisons() {
        this.action.doAction("central_beton.action_livraison");
    }

    onClickCamions() {
        this.action.doAction("central_beton.action_camion_malaxeur");
    }

    onClickNC() {
        this.action.doAction("central_beton.action_non_conformite");
    }

    onClickEssais() {
        this.action.doAction("central_beton.action_essai");
    }
}

CentralBetonDashboard.template = "central_beton.Dashboard";

registry.category("actions").add("central_beton.dashboard", CentralBetonDashboard);
