/** @odoo-module **/
// Blok „Ke zpracování“ na kartě Přehledu fondů (rozhodnutí 2026-11-14). Položky, jejich počty, role a filtr
// seznamu počítá model (investra.fund.dashboard_todo); widget je jen vykreslí a po kliknutí otevře seznam
// metodou modelu action_open_todo. Nic nepočítá a nic nemění.
import { Component, useProps } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";

export class InvestraFundTodo extends Component {
    static template = "investra_dashboard.FundTodo";
    props = useProps({ ...standardWidgetProps });

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
    }

    get items() {
        return this.props.record.data.dashboard_todo || [];
    }

    async open(item) {
        const action = await this.orm.call("investra.fund", "action_open_todo", [[this.props.record.resId], item.key]);
        if (action) {
            await this.action.doAction(action);
        }
    }
}

registry.category("view_widgets").add("investra_fund_todo", {
    component: InvestraFundTodo,
    fieldDependencies: [{ name: "dashboard_todo", type: "json" }],
});
