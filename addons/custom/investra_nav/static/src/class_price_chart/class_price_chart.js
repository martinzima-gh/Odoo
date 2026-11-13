/** @odoo-module **/
// Graf zveřejněných kurzů tříd v detailu ocenění (CP-2026-11-13, rozhodnutí 2026-11-13 „Historie kurzů tříd pro grafy“).
// Jen zveřejněná ocenění do data otevřeného ocenění; kurzy v měně třídy, nic se nepřepočítává ani nedopočítává.
// Jedna nebo dvě měny = jeden graf s levou a pravou osou; tři a více měn = samostatný graf pro každou měnu
// (varianta B, uživatel 2026-11-13).
// Převzetí od Copilota (Claude): OWL 3 v Odoo 20 nemá useState (je proxy), šablony odkazují přes this.,
// luxon je globální objekt, ne modul; chyba grafu nesmí zablokovat formulář ocenění.

import { Component, onWillStart, onWillUpdateProps, proxy, t, useProps } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { useChart } from "@web/core/utils/chart_hook";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";

const { DateTime } = luxon;

const LEFT_AXIS_COLORS = ["#112e3c", "#596e78", "#2c2927"];
const RIGHT_AXIS_COLORS = ["#0b5156", "#eb5b1f", "#6a6967"];
const GRID_COLOR = "#e8ebec";
const TEXT_COLOR = "#2c2927";
const MUTED_COLOR = "#6a6967";
const FONT = { family: "Montserrat, Arial, sans-serif" };
const PERIOD_MONTHS = { "3m": 3, "6m": 6, "1y": 12, all: null };
// Přehled kurzů ukládá kurz jako číslo na 8 desetinných míst (investra.valuation.price.history.price).
const MAX_PRICE_DIGITS = 8;

function formatDate(isoDate) {
    return DateTime.fromISO(isoDate).toFormat("d. M. yyyy");
}

function formatPrice(value, digits) {
    if (digits === undefined) {
        return value.toLocaleString("cs-CZ", { maximumFractionDigits: MAX_PRICE_DIGITS });
    }
    return value.toLocaleString("cs-CZ", { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

/** Jeden graf (canvas). Konfiguraci skládá rodič; při každé změně props se graf překreslí (useChart). */
class InvestraPriceChartPanel extends Component {
    static template = "investra_nav.ClassPriceChartPanel";
    props = useProps({
        getConfig: t.function(),
        height: t.number(),
    });

    chart = useChart(() => this.props.getConfig());
}

export class InvestraClassPriceChart extends Component {
    static template = "investra_nav.ClassPriceChart";
    static components = { InvestraPriceChartPanel };
    props = useProps({ ...standardWidgetProps });

    setup() {
        this.orm = useService("orm");
        this.requestId = 0;
        this.loadedKey = null;
        this.state = proxy({
            status: "loading",
            period: "all",
            valuationDate: null,
            dates: [],
            currencies: [],
            series: [],
        });
        onWillStart(() => this.reload(this.props.record));
        // Znovu načíst jen při jiném záznamu nebo po změně uloženého data, fondu či stavu – ne při každém poli.
        onWillUpdateProps((nextProps) => this.reload(nextProps.record));
    }

    recordKey(record) {
        const data = record.data || {};
        const fund = data.fund_id;
        return JSON.stringify([record.resId, record.dirty ? null : [String(data.date), fund && fund.id, data.state]]);
    }

    async reload(record) {
        const key = this.recordKey(record);
        if (key === this.loadedKey || (record.dirty && record.resId === this.loadedResId)) {
            return;
        }
        if (record.resId !== this.loadedResId) {
            this.state.period = "all";
        }
        this.loadedKey = key;
        this.loadedResId = record.resId;
        const requestId = ++this.requestId;
        if (!record.resId) {
            this.state.status = "unsaved";
            return;
        }
        this.state.status = "loading";
        let result;
        try {
            result = await this.fetchHistory(record.resId);
        } catch (error) {
            if (requestId === this.requestId) {
                console.error("Graf kurzů tříd nelze načíst", error);
                this.state.status = "error";
            }
            return;
        }
        if (requestId !== this.requestId) {
            return; // zastaralá odpověď nesmí přepsat novější požadavek
        }
        Object.assign(this.state, result);
    }

    async fetchHistory(valuationId) {
        const [valuation] = await this.orm.read("investra.valuation", [valuationId], ["fund_id", "date"]);
        if (!valuation || !valuation.fund_id || !valuation.date) {
            return { status: "empty" };
        }
        const fundId = valuation.fund_id[0];
        const [classes, rows] = await Promise.all([
            this.orm.searchRead("investra.fund.class", [["fund_id", "=", fundId]], ["code", "price_digits"], {
                context: { active_test: false },
            }),
            this.orm.searchRead(
                "investra.valuation.price.history",
                [["fund_id", "=", fundId], ["date", "<=", valuation.date]],
                ["date", "class_id", "currency_id", "price"],
                { order: "date asc, class_id asc" }
            ),
        ]);
        if (!rows.length) {
            return { status: "empty", valuationDate: valuation.date };
        }
        const classById = new Map(classes.map((item) => [item.id, item]));
        const currencies = [];
        const seriesByKey = new Map();
        const dateSet = new Set();
        for (const row of rows) {
            const [classId] = row.class_id;
            const [currencyId, currencyCode] = row.currency_id;
            if (!currencies.some((currency) => currency.id === currencyId)) {
                currencies.push({ id: currencyId, code: currencyCode });
            }
            const key = `${classId}:${currencyId}`;
            if (!seriesByKey.has(key)) {
                const fundClass = classById.get(classId);
                seriesByKey.set(key, {
                    classId,
                    classCode: fundClass ? fundClass.code : row.class_id[1],
                    priceDigits: Math.min(fundClass ? fundClass.price_digits : MAX_PRICE_DIGITS, MAX_PRICE_DIGITS),
                    currencyId,
                    currencyCode,
                    prices: new Map(),
                });
            }
            seriesByKey.get(key).prices.set(row.date, row.price);
            dateSet.add(row.date);
        }
        const dates = [...dateSet].sort();
        const usedColors = new Map();
        const series = [...seriesByKey.values()]
            .sort((a, b) => a.classCode.localeCompare(b.classCode) || a.currencyId - b.currencyId)
            .map((item) => {
                const currencyIndex = currencies.findIndex((currency) => currency.id === item.currencyId);
                const palette = currencies.length === 2 && currencyIndex === 1 ? RIGHT_AXIS_COLORS : LEFT_AXIS_COLORS;
                const colorIndex = usedColors.get(item.currencyId) || 0;
                usedColors.set(item.currencyId, colorIndex + 1);
                return {
                    label: `${item.classCode} · ${item.currencyCode}`,
                    currencyId: item.currencyId,
                    currencyCode: item.currencyCode,
                    priceDigits: item.priceDigits,
                    color: palette[colorIndex % palette.length],
                    data: dates.map((date) => (item.prices.has(date) ? item.prices.get(date) : null)),
                };
            });
        return { status: "ready", valuationDate: valuation.date, dates, currencies, series };
    }

    // --- zobrazení ------------------------------------------------------------------------------

    setPeriod(period) {
        this.state.period = period;
    }

    get periods() {
        return [
            { key: "3m", label: "3M" },
            { key: "6m", label: "6M" },
            { key: "1y", label: "1R" },
            { key: "all", label: "Max" },
        ];
    }

    /** Index prvního data ve zvoleném období (relativně k datu ocenění, z již načtené historie). */
    get startIndex() {
        const months = PERIOD_MONTHS[this.state.period];
        if (!months) {
            return 0;
        }
        const start = DateTime.fromISO(this.state.valuationDate).minus({ months }).toISODate();
        const index = this.state.dates.findIndex((date) => date >= start);
        return index === -1 ? this.state.dates.length : index;
    }

    get hasVisibleData() {
        return this.startIndex < this.state.dates.length;
    }

    get splitByCurrency() {
        return this.state.currencies.length > 2;
    }

    /** Grafy k vykreslení: jeden společný (1–2 měny), nebo jeden pro každou měnu (3 a více). */
    get panels() {
        if (!this.splitByCurrency) {
            return [{ key: "all", currencies: this.state.currencies, height: 360 }];
        }
        return this.state.currencies.map((currency) => ({ key: currency.code, currencies: [currency], height: 240 }));
    }

    get note() {
        if (this.splitByCurrency) {
            return "Zveřejněné kurzy v měně třídy. Každá měna má vlastní graf a stupnici – sklon čar mezi grafy nesrovnávejte.";
        }
        if (this.state.currencies.length === 2) {
            return "Zveřejněné kurzy v měně třídy. Osy mají různé stupnice – sklon čar nesrovnávejte.";
        }
        return "Zveřejněné kurzy v měně třídy.";
    }

    getChartConfig(panel) {
        const start = this.startIndex;
        const dates = this.state.dates.slice(start);
        const currencyIds = panel.currencies.map((currency) => currency.id);
        const series = this.state.series.filter((item) => currencyIds.includes(item.currencyId));
        const scales = {
            x: {
                type: "category",
                grid: { color: GRID_COLOR },
                ticks: { color: MUTED_COLOR, font: FONT, callback: (_value, index) => formatDate(dates[index]) },
            },
        };
        panel.currencies.forEach((currency, index) => {
            const color = series.find((item) => item.currencyId === currency.id).color;
            scales[index === 0 ? "y" : "y1"] = {
                type: "linear",
                position: index === 0 ? "left" : "right",
                beginAtZero: false,
                grid: { color: GRID_COLOR, drawOnChartArea: index === 0 },
                border: { color },
                ticks: { color, font: FONT, callback: (value) => formatPrice(value) },
                title: { display: true, text: currency.code, color, font: { ...FONT, weight: 600 } },
            };
        });
        return {
            type: "line",
            data: {
                labels: dates,
                datasets: series.map((item) => ({
                    label: item.label,
                    currencyCode: item.currencyCode,
                    priceDigits: item.priceDigits,
                    data: item.data.slice(start),
                    yAxisID: currencyIds.indexOf(item.currencyId) === 0 ? "y" : "y1",
                    borderColor: item.color,
                    backgroundColor: item.color,
                    pointBackgroundColor: item.color,
                    pointBorderColor: item.color,
                    pointRadius: 3,
                    borderWidth: 2,
                    fill: false,
                    spanGaps: false,
                })),
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: false,
                interaction: { mode: "index", intersect: false },
                scales,
                plugins: {
                    legend: { position: "bottom", labels: { color: TEXT_COLOR, font: FONT } },
                    tooltip: {
                        backgroundColor: "#ffffff",
                        titleColor: TEXT_COLOR,
                        bodyColor: TEXT_COLOR,
                        borderColor: GRID_COLOR,
                        borderWidth: 1,
                        titleFont: FONT,
                        bodyFont: FONT,
                        callbacks: {
                            title: (items) => (items.length ? formatDate(items[0].label) : ""),
                            label: (context) =>
                                `${context.dataset.label}: ${formatPrice(context.parsed.y, context.dataset.priceDigits)} ${context.dataset.currencyCode}`,
                        },
                    },
                },
            },
        };
    }
}

registry.category("view_widgets").add("investra_class_price_chart", {
    component: InvestraClassPriceChart,
});
