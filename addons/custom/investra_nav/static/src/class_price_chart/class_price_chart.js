/** @odoo-module **/

import { Component, onWillStart, onWillUpdateProps, t, useProps, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { useChart } from "@web/core/utils/chart_hook";
import { DateTime } from "luxon";

const LEFT_AXIS_COLORS = ["#112e3c", "#596e78", "#2c2927"];
const RIGHT_AXIS_COLORS = ["#0b5156", "#eb5b1f", "#6a6967"];
const GRID_COLOR = "#e8ebec";
const PERIOD_MONTHS = { "3m": 3, "6m": 6, "1y": 12, all: null };

function getRelation(value, fieldName) {
    if (
        !Array.isArray(value) ||
        value.length < 2 ||
        !Number.isInteger(value[0]) ||
        typeof value[1] !== "string" ||
        !value[1]
    ) {
        throw new Error(`Neplatná relace ${fieldName} v datech ocenění.`);
    }
    return { id: value[0], label: value[1] };
}

function formatPrice(value) {
    return value.toLocaleString("cs-CZ", { maximumFractionDigits: 8 });
}

function formatDate(value) {
    const date = DateTime.fromISO(value);
    if (!date.isValid) {
        throw new Error(`Neplatné datum ocenění: ${value}`);
    }
    return date.setLocale("cs").toFormat("d. M. yyyy");
}

export class InvestraClassPriceChart extends Component {
    static template = "investra_nav.ClassPriceChart";
    props = useProps({ record: t.any() });
    chart = useChart(() => this.getChartConfig());

    setup() {
        this.orm = useService("orm");
        this.historyRequest = 0;
        this.currentValuationId = null;
        this.state = useState({
            status: "loading",
            period: "all",
            valuationDate: null,
            dates: [],
            currencies: [],
            series: [],
        });

        onWillStart(() => this.loadValuationHistory(this.props.record.resId));
        onWillUpdateProps((nextProps) => this.loadValuationHistory(nextProps.record.resId));
    }

    async loadValuationHistory(valuationId) {
        const requestId = ++this.historyRequest;
        if (this.currentValuationId !== valuationId) {
            this.currentValuationId = valuationId;
            this.state.period = "all";
        }
        this.state.status = "loading";
        this.state.valuationDate = null;
        this.state.dates = [];
        this.state.currencies = [];
        this.state.series = [];

        if (!Number.isInteger(valuationId) || valuationId <= 0) {
            this.state.status = "unsaved";
            return;
        }

        const valuations = await this.orm.searchRead(
            "investra.valuation",
            [["id", "=", valuationId]],
            ["fund_id", "date"],
            { limit: 1 }
        );
        if (requestId !== this.historyRequest) {
            return;
        }
        if (!valuations.length) {
            throw new Error(`Ocenění ${valuationId} nebylo nalezeno.`);
        }
        const valuation = valuations[0];
        if (typeof valuation.date !== "string") {
            throw new Error(`Ocenění ${valuationId} nemá platné datum.`);
        }
        formatDate(valuation.date);
        const fund = getRelation(valuation.fund_id, "fund_id");
        this.state.valuationDate = valuation.date;

        const rows = await this.orm.searchRead(
            "investra.valuation.price.history",
            [
                ["fund_id", "=", fund.id],
                ["date", "<=", valuation.date],
            ],
            ["date", "class_id", "currency_id", "price"],
            { order: "date asc, class_id asc" }
        );
        if (requestId !== this.historyRequest) {
            return;
        }

        if (!rows.length) {
            this.state.status = "empty";
            return;
        }

        const currenciesById = new Map();
        const seriesByKey = new Map();
        const dateSet = new Set();

        for (const row of rows) {
            if (typeof row.date !== "string") {
                throw new Error("V historii kurzů chybí datum ocenění.");
            }
            formatDate(row.date);

            const fundClass = getRelation(row.class_id, "class_id");
            const currency = getRelation(row.currency_id, "currency_id");
            if (typeof row.price !== "number" || !Number.isFinite(row.price)) {
                throw new Error(`Neplatný kurz pro třídu ${fundClass.label} k ${row.date}.`);
            }

            if (!currenciesById.has(currency.id)) {
                currenciesById.set(currency.id, { id: currency.id, code: currency.label });
            }

            const seriesKey = `${fundClass.id}:${currency.id}`;
            if (!seriesByKey.has(seriesKey)) {
                seriesByKey.set(seriesKey, {
                    classId: fundClass.id,
                    classCode: fundClass.label,
                    currencyId: currency.id,
                    currencyCode: currency.label,
                    pricesByDate: new Map(),
                });
            }
            const series = seriesByKey.get(seriesKey);
            if (series.pricesByDate.has(row.date)) {
                throw new Error(`Duplicitní zveřejněný kurz třídy ${fundClass.label} k ${row.date}.`);
            }
            series.pricesByDate.set(row.date, row.price);
            dateSet.add(row.date);
        }

        const currencies = [...currenciesById.values()];
        if (currencies.length > 2) {
            this.state.status = "too_many_currencies";
            return;
        }

        const dates = [...dateSet].sort();
        const colorIndexes = new Map();
        const series = [...seriesByKey.values()]
            .sort((left, right) => left.classId - right.classId || left.currencyId - right.currencyId)
            .map((item) => {
                const currencyIndex = currencies.findIndex((currency) => currency.id === item.currencyId);
                const axisColors = currencyIndex === 0 ? LEFT_AXIS_COLORS : RIGHT_AXIS_COLORS;
                const colorIndex = colorIndexes.get(item.currencyId) || 0;
                colorIndexes.set(item.currencyId, colorIndex + 1);
                return {
                    ...item,
                    label: `${item.classCode} · ${item.currencyCode}`,
                    axisId: currencyIndex === 0 ? "y" : "y1",
                    color: axisColors[colorIndex % axisColors.length],
                    data: dates.map((date) =>
                        item.pricesByDate.has(date) ? item.pricesByDate.get(date) : null
                    ),
                };
            });

        this.state.dates = dates;
        this.state.currencies = currencies;
        this.state.series = series;
        this.state.status = "ready";
    }

    setPeriod(period) {
        if (!Object.prototype.hasOwnProperty.call(PERIOD_MONTHS, period)) {
            throw new Error(`Neznámé období grafu: ${period}`);
        }
        this.state.period = period;
    }

    getVisibleData() {
        const periodMonths = PERIOD_MONTHS[this.state.period];
        const startDate =
            periodMonths === null
                ? null
                : DateTime.fromISO(this.state.valuationDate)
                      .minus({ months: periodMonths })
                      .toISODate();
        const startIndex = startDate
            ? this.state.dates.findIndex((date) => date >= startDate)
            : 0;
        const index = startIndex === -1 ? this.state.dates.length : startIndex;
        return {
            dates: this.state.dates.slice(index),
            series: this.state.series.map((series) => ({
                ...series,
                data: series.data.slice(index),
            })),
        };
    }

    hasVisibleData() {
        return this.getVisibleData().dates.length > 0;
    }

    getChartConfig() {
        const { dates, series } = this.getVisibleData();
        const axes = {
            x: {
                type: "category",
                grid: { color: GRID_COLOR },
                ticks: {
                    color: "#6a6967",
                    autoSkip: true,
                    callback: (_value, index) => formatDate(dates[index]),
                },
            },
        };

        this.state.currencies.forEach((currency, index) => {
            const axisId = index === 0 ? "y" : "y1";
            const firstSeries = this.state.series.find((item) => item.currencyId === currency.id);
            axes[axisId] = {
                type: "linear",
                position: index === 0 ? "left" : "right",
                beginAtZero: false,
                grid: {
                    color: GRID_COLOR,
                    drawOnChartArea: index === 0,
                },
                border: { color: firstSeries.color },
                ticks: {
                    color: firstSeries.color,
                    callback: (value) => formatPrice(value),
                },
                title: {
                    display: true,
                    text: currency.code,
                    color: firstSeries.color,
                },
            };
        });

        return {
            type: "line",
            data: {
                labels: dates,
                datasets: series.map((series) => ({
                    label: series.label,
                    currencyCode: series.currencyCode,
                    data: series.data,
                    yAxisID: series.axisId,
                    borderColor: series.color,
                    backgroundColor: series.color,
                    pointBackgroundColor: series.color,
                    pointBorderColor: series.color,
                    pointRadius: 3,
                    borderWidth: 2,
                    fill: false,
                    spanGaps: false,
                })),
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                font: { family: "Montserrat, Arial, sans-serif" },
                interaction: { mode: "index", intersect: false },
                scales: axes,
                plugins: {
                    legend: {
                        position: "bottom",
                        labels: { font: { family: "Montserrat, Arial, sans-serif" } },
                    },
                    tooltip: {
                        backgroundColor: "#ffffff",
                        titleColor: "#2c2927",
                        bodyColor: "#2c2927",
                        borderColor: GRID_COLOR,
                        borderWidth: 1,
                        callbacks: {
                            title: (items) => (items.length ? formatDate(items[0].label) : ""),
                            label: (context) =>
                                `${context.dataset.label}: ${formatPrice(context.parsed.y)} ${context.dataset.currencyCode}`,
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
