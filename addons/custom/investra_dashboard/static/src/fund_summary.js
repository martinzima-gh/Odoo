/** @odoo-module **/
// Souhrnný pás nad kartami Přehledu fondů (rozhodnutí 2026-11-15): počty fondů podle stavu, kliknutí přepne
// filtr vyhledávání. Počty počítá model (investra.fund.dashboard_summary) přes všechny fondy uživatele bez ohledu
// na zapnuté filtry; pás nic nemění. Vzor: account.DashboardKanbanRenderer v jádru Odoo 20.
import { Component, onWillStart, proxy } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { KanbanRenderer } from "@web/views/kanban/kanban_renderer";
import { kanbanView } from "@web/views/kanban/kanban_view";

export class InvestraFundSummary extends Component {
    static template = "investra_dashboard.FundSummary";

    setup() {
        this.orm = useService("orm");
        this.state = proxy({ total: 0, cards: [] });
        onWillStart(async () => {
            try {
                const summary = await this.orm.call("investra.fund", "dashboard_summary", []);
                this.state.total = summary.total;
                this.state.cards = summary.cards;
            } catch {
                // Pás je doplněk: když se počty nenačtou, karty fungují dál bez něj.
                this.state.cards = [];
            }
        });
    }

    toggle(card) {
        // Karta s nulou je vypnutá: filtr by jen vyprázdnil seznam (nález uživatele 2026-11-15).
        if (!card.count) {
            return;
        }
        const searchModel = this.env.searchModel;
        const item = searchModel && searchModel.getSearchItems((searchItem) => searchItem.name === card.filter)[0];
        if (item) {
            searchModel.toggleSearchItem(item.id);
        }
    }
}

export class InvestraFundDashboardRenderer extends KanbanRenderer {
    static template = "investra_dashboard.FundDashboardRenderer";
    static components = { ...KanbanRenderer.components, InvestraFundSummary };
}

registry.category("views").add("investra_fund_dashboard", {
    ...kanbanView,
    Renderer: InvestraFundDashboardRenderer,
});
