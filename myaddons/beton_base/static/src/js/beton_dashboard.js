/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onWillStart, onMounted, onWillUnmount, useState, useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { loadJS } from "@web/core/assets";

class BetonDashboard extends Component {
    static template = "beton_base.Dashboard";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        const today = new Date();
        this.state = useState({
            data: {},
            loading: true,
            selectedMonth: today.getMonth() + 1,
            selectedYear: today.getFullYear(),
            selectedDate: "",  // YYYY-MM-DD ; si vide, on prend today
        });

        // Chart refs
        this.chartProductionRef = useRef("chartProduction");
        this.chartProduitsRef = useRef("chartProduits");
        this.chartCARef = useRef("chartCA");
        this.chartLivraisonsRef = useRef("chartLivraisons");
        this.charts = [];

        onWillStart(async () => {
            await loadJS("/web/static/lib/Chart/Chart.js");
            await this.loadDashboardData();
        });

        onMounted(() => {
            if (!this.state.loading) {
                this.renderCharts();
            }
        });

        onWillUnmount(() => {
            this.destroyCharts();
        });
    }

    async loadDashboardData() {
        this.state.loading = true;
        this.state.data = await this.orm.call(
            "beton.dashboard",
            "get_dashboard_data",
            [this.state.selectedYear, this.state.selectedMonth, this.state.selectedDate || null]
        );
        this.state.loading = false;
        // Render charts after DOM update
        setTimeout(() => this.renderCharts(), 100);
    }

    async refresh() {
        this.destroyCharts();
        await this.loadDashboardData();
    }

    async onDateChange(ev) {
        const value = ev.target.value;  // "YYYY-MM-DD" ou ""
        this.state.selectedDate = value;
        if (value) {
            // Synchronise mois/année avec la date sélectionnée
            const [y, m] = value.split("-");
            this.state.selectedYear = parseInt(y, 10);
            this.state.selectedMonth = parseInt(m, 10);
        }
        this.destroyCharts();
        await this.loadDashboardData();
    }

    async clearDate() {
        this.state.selectedDate = "";
        this.destroyCharts();
        await this.loadDashboardData();
    }

    destroyCharts() {
        for (const chart of this.charts) {
            if (chart) chart.destroy();
        }
        this.charts = [];
    }

    renderCharts() {
        this.destroyCharts();
        const data = this.state.data;
        if (!data || !data.chart_production) return;

        // Chart 1: Production journaliere (barres)
        const ctxProd = this.chartProductionRef.el;
        if (ctxProd) {
            this.charts.push(new Chart(ctxProd, {
                type: "bar",
                data: {
                    labels: data.chart_production.labels,
                    datasets: [{
                        label: "Production (m\u00b3)",
                        data: data.chart_production.values,
                        backgroundColor: "rgba(21, 101, 192, 0.7)",
                        borderColor: "rgba(21, 101, 192, 1)",
                        borderWidth: 1,
                        borderRadius: 4,
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: { font: { size: 11 } },
                            grid: { color: "rgba(0,0,0,0.05)" },
                        },
                        x: {
                            ticks: { font: { size: 10 }, maxRotation: 45 },
                            grid: { display: false },
                        },
                    },
                },
            }));
        }

        // Chart 2: Production par produit (doughnut)
        const ctxProduits = this.chartProduitsRef.el;
        if (ctxProduits && data.chart_produits.labels.length) {
            const colors = [
                "#1565c0", "#2e7d32", "#e65100", "#6a1b9a",
                "#00695c", "#c62828", "#f57f17", "#283593",
            ];
            this.charts.push(new Chart(ctxProduits, {
                type: "doughnut",
                data: {
                    labels: data.chart_produits.labels,
                    datasets: [{
                        data: data.chart_produits.values,
                        backgroundColor: colors.slice(0, data.chart_produits.labels.length),
                        borderWidth: 2,
                        borderColor: "#fff",
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: "right",
                            labels: { font: { size: 11 }, padding: 12 },
                        },
                    },
                    cutout: "60%",
                },
            }));
        }

        // Chart 3: CA mensuel (barres)
        const ctxCA = this.chartCARef.el;
        if (ctxCA) {
            this.charts.push(new Chart(ctxCA, {
                type: "bar",
                data: {
                    labels: data.chart_ca.labels,
                    datasets: [{
                        label: "CA (" + (data.currency_symbol || "DA") + ")",
                        data: data.chart_ca.values,
                        backgroundColor: "rgba(106, 27, 154, 0.7)",
                        borderColor: "rgba(106, 27, 154, 1)",
                        borderWidth: 1,
                        borderRadius: 6,
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                font: { size: 11 },
                                callback: (val) => {
                                    if (val >= 1000000) return (val / 1000000).toFixed(1) + "M";
                                    if (val >= 1000) return (val / 1000).toFixed(0) + "K";
                                    return val;
                                },
                            },
                            grid: { color: "rgba(0,0,0,0.05)" },
                        },
                        x: {
                            ticks: { font: { size: 11 } },
                            grid: { display: false },
                        },
                    },
                },
            }));
        }

        // Chart 4: Livraisons semaine (ligne)
        const ctxLiv = this.chartLivraisonsRef.el;
        if (ctxLiv) {
            this.charts.push(new Chart(ctxLiv, {
                type: "line",
                data: {
                    labels: data.chart_livraisons.labels,
                    datasets: [{
                        label: "Livraisons",
                        data: data.chart_livraisons.values,
                        borderColor: "#2e7d32",
                        backgroundColor: "rgba(46, 125, 50, 0.1)",
                        borderWidth: 2,
                        fill: true,
                        tension: 0.3,
                        pointBackgroundColor: "#2e7d32",
                        pointRadius: 5,
                        pointHoverRadius: 7,
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: { font: { size: 11 }, stepSize: 1 },
                            grid: { color: "rgba(0,0,0,0.05)" },
                        },
                        x: {
                            ticks: { font: { size: 10 } },
                            grid: { display: false },
                        },
                    },
                },
            }));
        }
    }

    // ===== Navigation actions =====
    openFabricationsJour() {
        this.action.doAction("beton_base.action_dashboard_fabrications_jour");
    }

    openLivraisonsJour() {
        this.action.doAction("beton_base.action_dashboard_livraisons_jour");
    }

    openNCNonTraitees() {
        this.action.doAction("beton_base.action_dashboard_nc_non_traitees");
    }

    openEquipementsPanne() {
        this.action.doAction("beton_base.action_dashboard_equipements_panne");
    }

    openChantiersActifs() {
        this.action.doAction("beton_base.action_dashboard_chantiers_actifs");
    }

    openInterventionsEnCours() {
        this.action.doAction("beton_base.action_dashboard_interventions_cours");
    }

    openFabrications() {
        this.action.doAction("beton_base.action_beton_mrp_production");
    }

    openLivraisons() {
        this.action.doAction("beton_base.action_beton_stock_picking_livraison");
    }

    openEssais() {
        this.action.doAction("beton_base.action_beton_essai");
    }

    openCoutsRevient() {
        this.action.doAction("beton_base.action_beton_cout");
    }

    openFabrication(id) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "mrp.production",
            res_id: id,
            views: [[false, "form"]],
        });
    }

    // ===== Formatters =====
    formatNumber(value, decimals = 0) {
        if (value === undefined || value === null) return "0";
        return Number(value).toLocaleString("fr-FR", {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals,
        });
    }

    formatCurrency(value) {
        if (value === undefined || value === null) return "0";
        const symbol = this.state.data.currency_symbol || "DA";
        return Number(value).toLocaleString("fr-FR", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        }) + " " + symbol;
    }
}

registry.category("actions").add("beton_dashboard", BetonDashboard);
