/** @odoo-module **/
// Souhrn detailu ocenění podle náhledu docs/vzhled/nahled-investra.html (CP-2026-11-13, Claude):
// podnadpis „Ocenění k …“ a dlaždice FK fondu, změna FK od minulého ocenění a poslední zveřejněný kurz každé třídy.
// Jen zobrazení existujících údajů: nic se nepočítá jinak než ve výpočtu ocenění. Změna FK je změna kapitálu
// (zahrnuje úpisy a odkupy), ne výkonnost; kurzy jsou zveřejněné, v měně třídy, bez přepočtu
// (rozhodnutí 2026-11-13 „Historie kurzů tříd pro grafy“).

import { Component, onWillStart, onWillUpdateProps, proxy, useProps } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { formatMonetary } from "@web/views/fields/formatters";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";

const { DateTime } = luxon;
const MAX_PRICE_DIGITS = 8;
const NOT_COMPUTED = ["draft", "returned"];

function formatDate(value) {
    const date = typeof value === "string" ? DateTime.fromISO(value) : value;
    return date && date.isValid ? date.toFormat("d. M. yyyy") : "";
}

function formatNumber(value, digits) {
    return value.toLocaleString("cs-CZ", { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

export class InvestraValuationSummary extends Component {
    static template = "investra_nav.ValuationSummary";
    props = useProps({ ...standardWidgetProps });

    setup() {
        this.orm = useService("orm");
        this.requestId = 0;
        this.loadedKey = null;
        this.state = proxy({ previousCapital: null, prices: [], error: false });
        onWillStart(() => this.reload(this.props.record));
        onWillUpdateProps((nextProps) => this.reload(nextProps.record));
    }

    get data() {
        return this.props.record.data;
    }

    get subtitle() {
        const date = formatDate(this.data.date);
        if (!date) {
            return "";
        }
        return this.data.version ? `Ocenění k ${date} · verze ${this.data.version}` : `Ocenění k ${date}`;
    }

    get computed() {
        return this.props.record.resId && !NOT_COMPUTED.includes(this.data.state);
    }

    money(value) {
        const currency = this.data.currency_id;
        return formatMonetary(value, { currencyId: currency && currency.id });
    }

    get capitalTile() {
        return { value: this.computed ? this.money(this.data.fund_capital) : "—" };
    }

    get changeTile() {
        const previous = this.state.previousCapital;
        if (!this.computed || previous === null) {
            return { value: "—", pct: "", sign: 0 };
        }
        const change = this.data.fund_capital - previous;
        const sign = change > 0 ? 1 : change < 0 ? -1 : 0;
        const prefix = sign > 0 ? "+" : "";
        const pct = previous ? `${prefix}${formatNumber((change / previous) * 100, 2)} %` : "";
        return { value: `${prefix}${this.money(change)}`, pct, sign };
    }

    recordKey(record) {
        const data = record.data || {};
        const ids = [data.fund_id, data.previous_id].map((value) => value && value.id);
        return JSON.stringify([record.resId, String(data.date), data.state, ...ids]);
    }

    async reload(record) {
        const key = this.recordKey(record);
        if (key === this.loadedKey || record.dirty) {
            return;
        }
        this.loadedKey = key;
        const requestId = ++this.requestId;
        const data = record.data;
        if (!record.resId || !data.fund_id || !data.date) {
            Object.assign(this.state, { previousCapital: null, prices: [], error: false });
            return;
        }
        try {
            const valuationDate = typeof data.date === "string" ? data.date : data.date.toISODate();
            const [previous, classes, rows] = await Promise.all([
                data.previous_id ? this.orm.read("investra.valuation", [data.previous_id.id], ["fund_capital"]) : [],
                this.orm.searchRead("investra.fund.class", [["fund_id", "=", data.fund_id.id]], ["code", "price_digits"], {
                    context: { active_test: false },
                }),
                this.orm.searchRead(
                    "investra.valuation.price.history",
                    [["fund_id", "=", data.fund_id.id], ["date", "<=", valuationDate]],
                    ["date", "class_id", "currency_id", "price"],
                    { order: "date desc" }
                ),
            ]);
            if (requestId !== this.requestId) {
                return;
            }
            const classById = new Map(classes.map((item) => [item.id, item]));
            const latest = new Map();
            for (const row of rows) {
                if (!latest.has(row.class_id[0])) {
                    latest.set(row.class_id[0], row); // řádky jsou od nejnovějšího
                }
            }
            const prices = [...latest.values()]
                .map((row) => {
                    const fundClass = classById.get(row.class_id[0]);
                    const digits = Math.min(fundClass ? fundClass.price_digits : MAX_PRICE_DIGITS, MAX_PRICE_DIGITS);
                    return {
                        key: row.class_id[0],
                        code: fundClass ? fundClass.code : row.class_id[1],
                        value: formatNumber(row.price, digits),
                        sub: `k ${formatDate(row.date)} · ${row.currency_id[1]}`,
                    };
                })
                .sort((a, b) => a.code.localeCompare(b.code));
            Object.assign(this.state, {
                previousCapital: previous.length ? previous[0].fund_capital : null,
                prices,
                error: false,
            });
        } catch (error) {
            if (requestId === this.requestId) {
                console.error("Souhrn ocenění nelze načíst", error);
                Object.assign(this.state, { previousCapital: null, prices: [], error: true });
            }
        }
    }
}

registry.category("view_widgets").add("investra_valuation_summary", {
    component: InvestraValuationSummary,
});
