/** @odoo-module **/
// Souhrn detailu ocenění podle návrhu docs/vzhled/navrh-detail-oceneni.html (uživatel 2026-11-13).
// Řádek údajů ocenění, pás FK fondu / změna FK od minula / výsledek za období a karta každé třídy:
// kurz tohoto ocenění, změna proti minulému ocenění a malý graf zveřejněných kurzů za 12 měsíců;
// úsek grafu od minulého ocenění k tomuto má barvu změny (růst Lagoon, pokles Ember).
// Jen zobrazení údajů, které uložil výpočet (přemostění kapitálu tříd, rozhodnutí 2026-11-10):
//   FK = FK (t−1) + úpisy − odkupy − dividendy + změna společná + změna specifická.
// Změna FK zahrnuje pohyby investorů, není to výkonnost. Kurzy jsou v měně třídy, nic se nepřepočítává
// (rozhodnutí 2026-11-13 „Historie kurzů tříd pro grafy“); každý graf má vlastní stupnici.

import { Component, onWillStart, onWillUpdateProps, proxy, useProps } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { formatFloat, formatMonetary } from "@web/views/fields/formatters";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";

const { DateTime } = luxon;
const NOT_COMPUTED = ["draft", "returned"];
const HISTORY_MONTHS = 12;
const SPARK = { width: 260, height: 56, pad: 6 };
const SPARK_COLORS = ["#112e3c", "#0b5156", "#596e78", "#2c2927"];
const LINE_FIELDS = [
    "class_id", "class_code", "currency_name", "units", "capital", "opening_capital", "subscription_amount",
    "redemption_amount", "dividend_amount", "shared_result", "delta", "price", "opening_price",
];

function toDate(value) {
    return typeof value === "string" ? DateTime.fromISO(value) : value;
}

function formatDate(value) {
    const date = toDate(value);
    // Jednotný formát data v Investře (uživatel 2026-11-13): 30.09.2026.
    return date && date.isValid ? date.toFormat("dd.MM.yyyy") : "";
}

function sum(lines, field) {
    return lines.reduce((total, line) => total + (line[field] || 0), 0);
}

/**
 * Body malého grafu. Plná čára = zveřejněné kurzy. Změna se v grafu kreslí stejně jako v čísle karty:
 * od předchozího ocenění k tomuto (rozhodnutí 2026-11-14 „Graf kurzu – změna od předchozího ocenění“).
 * Předchozí ocenění, které ještě není zveřejněné, je v grafu samostatný bod napojený tečkovaně.
 *
 * @param published zveřejněné kurzy [{date, price}] vzestupně
 * @param current kurz tohoto ocenění, pokud ještě není zveřejněný, jinak null
 * @param previous předchozí ocenění {date, price}, nebo null u prvního ocenění
 */
export function sparkline(published, current, previous = null) {
    const values = published.map((point) => point.price);
    let previousIndex = previous ? published.findIndex((point) => point.date === previous.date) : -1;
    const bridged = previousIndex < 0 && previous !== null && current !== null;
    if (bridged) {
        values.push(previous.price);
        previousIndex = values.length - 1;
    }
    if (current !== null) {
        values.push(current);
    }
    if (!values.length) {
        return null;
    }
    const low = Math.min(...values);
    const high = Math.max(...values);
    const span = high - low || 1;
    const step = values.length > 1 ? (SPARK.width - 2 * SPARK.pad) / (values.length - 1) : 0;
    const points = values.map((value, index) => ({
        x: values.length > 1 ? SPARK.pad + index * step : SPARK.width / 2,
        y: high === low ? SPARK.height / 2 : SPARK.height - SPARK.pad - ((value - low) / span) * (SPARK.height - 2 * SPARK.pad),
    }));
    const solid = points.slice(0, published.length);
    const last = solid[solid.length - 1] || null;
    const currentPoint = current !== null ? points[points.length - 1] : null;
    // Konec úseku změny: nezveřejněné toto ocenění, jinak poslední zveřejněný bod (toto ocenění po zveřejnění).
    const end = currentPoint || last;
    const start = previousIndex >= 0 ? points[previousIndex] : null;
    return {
        viewBox: `0 0 ${SPARK.width} ${SPARK.height}`,
        line: solid.map((point) => `${point.x.toFixed(1)},${point.y.toFixed(1)}`).join(" "),
        last,
        bridge: bridged ? points[previousIndex] : null,
        change: start && end && start !== end ? { from: start, to: end, dashed: currentPoint !== null } : null,
        current: currentPoint,
        end,
    };
}

export class InvestraValuationSummary extends Component {
    static template = "investra_nav.ValuationSummary";
    props = useProps({ ...standardWidgetProps });

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.requestId = 0;
        this.loadedKey = null;
        this.state = proxy({ lines: [], classes: [], error: false });
        onWillStart(() => this.reload(this.props.record));
        onWillUpdateProps((nextProps) => this.reload(nextProps.record));
    }

    get data() {
        return this.props.record.data;
    }

    get computed() {
        return Boolean(this.props.record.resId) && !NOT_COMPUTED.includes(this.data.state) && this.state.lines.length > 0;
    }

    get facts() {
        const facts = [];
        const date = formatDate(this.data.date);
        if (date) {
            facts.push({ key: "date", label: "Ocenění k", value: date });
        }
        if (this.data.version) {
            facts.push({ key: "version", label: "verze", value: String(this.data.version) });
        }
        if (this.data.previous_id) {
            facts.push({ key: "previous", label: "předchozí", value: this.data.previous_id.display_name, link: true });
        }
        if (this.data.preparer_id) {
            facts.push({ key: "preparer", label: "zadal", value: this.data.preparer_id.display_name });
        }
        return facts;
    }

    openPrevious() {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "investra.valuation",
            res_id: this.data.previous_id.id,
            views: [[false, "form"]],
        });
    }

    money(value, signed = false) {
        const currency = this.data.currency_id;
        const text = formatMonetary(value, { currencyId: currency && currency.id });
        return signed && value > 0 ? `+${text}` : text;
    }

    tone(value) {
        return value > 0 ? "o_investra_up" : value < 0 ? "o_investra_down" : "";
    }

    /** Pás nahoře; součty z řádků tříd odpovídají přemostění kapitálu. */
    get kpi() {
        if (!this.computed) {
            return null;
        }
        const lines = this.state.lines;
        const opening = sum(lines, "opening_capital");
        const capital = this.data.fund_capital;
        const change = capital - opening;
        const dividends = sum(lines, "dividend_amount");
        const flows = sum(lines, "subscription_amount") - sum(lines, "redemption_amount") - dividends;
        const result = sum(lines, "shared_result") + sum(lines, "delta");
        const first = !this.data.previous_id;
        return {
            capital: this.money(capital),
            change: first ? "—" : this.money(change, true),
            changeTone: first ? "" : this.tone(change),
            changePct: !first && opening ? `${change > 0 ? "+" : ""}${formatFloat((change / opening) * 100, { digits: [16, 2] })} %` : "",
            flowsLabel: dividends ? "z toho úpisy − odkupy − dividendy" : "z toho úpisy − odkupy",
            flows: first ? "" : this.money(flows, true),
            result: first ? "—" : this.money(result, true),
            resultTone: first ? "" : this.tone(result),
        };
    }

    recordKey(record) {
        const data = record.data || {};
        return JSON.stringify([record.resId, String(data.date), data.state, data.fund_id && data.fund_id.id]);
    }

    async reload(record) {
        const key = this.recordKey(record);
        if (key === this.loadedKey || record.dirty) {
            return;
        }
        this.loadedKey = key;
        const requestId = ++this.requestId;
        const data = record.data;
        if (!record.resId || !data.fund_id || !data.date || NOT_COMPUTED.includes(data.state)) {
            Object.assign(this.state, { lines: [], classes: [], error: false });
            return;
        }
        try {
            const date = toDate(data.date);
            const [lines, fundClasses, history, previous] = await Promise.all([
                this.orm.searchRead("investra.valuation.class", [["valuation_id", "=", record.resId]], LINE_FIELDS),
                this.orm.searchRead("investra.fund.class", [["fund_id", "=", data.fund_id.id]], ["price_digits"], {
                    context: { active_test: false },
                }),
                this.orm.searchRead(
                    "investra.valuation.price.history",
                    [
                        ["fund_id", "=", data.fund_id.id],
                        ["date", "<=", date.toISODate()],
                        ["date", ">", date.minus({ months: HISTORY_MONTHS }).toISODate()],
                    ],
                    ["date", "class_id", "price"],
                    { order: "date asc" }
                ),
                data.previous_id ? this.orm.read("investra.valuation", [data.previous_id.id], ["date"]) : [],
            ]);
            if (requestId !== this.requestId) {
                return; // zastaralá odpověď nesmí přepsat novější
            }
            const previousDate = previous.length ? formatDate(previous[0].date) : "";
            const previousIso = previous.length ? toDate(previous[0].date).toISODate() : "";
            Object.assign(this.state, {
                lines,
                classes: this.buildClasses(lines, fundClasses, history, date, previousDate, previousIso),
                error: false,
            });
        } catch (error) {
            if (requestId === this.requestId) {
                console.error("Souhrn ocenění nelze načíst", error);
                Object.assign(this.state, { lines: [], classes: [], error: true });
            }
        }
    }

    buildClasses(lines, fundClasses, history, date, previousDate, previousIso) {
        const digitsById = new Map(fundClasses.map((item) => [item.id, item.price_digits]));
        const isoDate = date.toISODate();
        return [...lines]
            .sort((a, b) => (a.class_code || "").localeCompare(b.class_code || ""))
            .map((line, index) => {
                const classId = line.class_id[0];
                const digits = digitsById.get(classId) ?? 4;
                const price = parseFloat(line.price);
                const opening = line.opening_price ? parseFloat(line.opening_price) : null;
                const published = history.filter((row) => row.class_id[0] === classId);
                const thisPublished = published.length && published[published.length - 1].date === isoDate;
                const change = opening ? price - opening : null;
                const previousPoint = opening && previousIso ? { date: previousIso, price: opening } : null;
                const spark = sparkline(published, thisPublished || Number.isNaN(price) ? null : price, previousPoint);
                const fmt = (value) => formatFloat(value, { digits: [16, digits] });
                return {
                    key: classId,
                    code: line.class_code,
                    currency: line.currency_name,
                    price: Number.isNaN(price) ? line.price : fmt(price),
                    change: change === null ? "" : `${change > 0 ? "▲ +" : change < 0 ? "▼ " : ""}${fmt(change)}`,
                    changePct: change === null ? "" : `(${change > 0 ? "+" : ""}${formatFloat((change / opening) * 100, { digits: [16, 2] })} %)`,
                    tone: change === null ? "" : this.tone(change),
                    since: previousDate,
                    capital: this.money(line.capital),
                    units: formatFloat(line.units, { digits: [16, 0] }),
                    spark,
                    color: SPARK_COLORS[index % SPARK_COLORS.length],
                    sparkNote: published.length ? `zveřejněno za ${HISTORY_MONTHS} měsíců` : "zatím bez zveřejněných kurzů",
                    pending: Boolean(spark && spark.current),
                };
            });
    }
}

registry.category("view_widgets").add("investra_valuation_summary", {
    component: InvestraValuationSummary,
});
