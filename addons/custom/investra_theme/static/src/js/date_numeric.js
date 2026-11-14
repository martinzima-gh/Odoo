/** @odoo-module **/
// Datum vždy jako 30.09.2026 (rozhodnutí 2026-11-13 „Formát data v aplikaci“, doplněno 2026-11-14):
// Odoo u letošních dat v seznamech a formulářích vynechává rok („30. 11.“). Volba `numeric` vypíše datum
// ve formátu jazyka (cs_CZ dd.MM.yyyy) vždy celé. Platí pro všechna pole typu datum, pokud pohled
// výslovně neuvede `options="{'numeric': false}"`. Jen zobrazení, hodnoty se nemění.
import { registry } from "@web/core/registry";

const dateFormatter = registry.category("formatters").get("date");
const extractOptions = dateFormatter.extractOptions;
dateFormatter.extractOptions = (fieldInfo) => ({
    ...(extractOptions ? extractOptions(fieldInfo) : {}),
    numeric: fieldInfo.options?.numeric ?? true,
});

const dateField = registry.category("fields").get("date");
const extractProps = dateField.extractProps;
dateField.extractProps = (fieldInfo, dynamicInfo) => ({
    ...extractProps(fieldInfo, dynamicInfo),
    numeric: fieldInfo.options?.numeric ?? true,
});
