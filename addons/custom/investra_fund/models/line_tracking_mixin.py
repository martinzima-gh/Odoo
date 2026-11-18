from markupsafe import Markup

from odoo import api, fields, models


class InvestraLineTrackingMixin(models.AbstractModel):
    """Společný mixin pro řádkové modely (One2many), který zapisuje změny do chatteru rodiče.

    Na One2many řádcích vestavěný tracking Odoo nefunguje a řádek nemá vlastní chatter.
    Tento mixin při create/write/unlink zapíše zprávu do rodičovského záznamu (chatteru).
    """

    _name = "investra.line.tracking.mixin"
    _description = "Sledování změn řádků v chatteru rodiče"

    # Many2one pole na rodiče (např. 'role_id', 'matrix_id') nebo cesta přes více záznamů (např. 'version_id.rule_id':
    # pásmo úplaty zapisuje do chatteru pravidla, ne verze; rozhodnutí 2026-11-18, ZJ-10 fáze 2).
    _line_tracking_parent = None
    _line_tracking_fields = None  # explicitní seznam polí, nebo None (všechna pole modelu s tracking=True)

    @api.model
    def _valid_field_parameter(self, field, name):
        return name == "tracking" or super()._valid_field_parameter(field, name)

    def _line_tracking_parent_field(self):
        """Název Many2one pole řádku, kterým cesta k rodiči začíná; None, když model rodiče nemá."""
        path = getattr(self, "_line_tracking_parent", None)
        field_name = path.split(".")[0] if path else None
        return field_name if field_name in self._fields else None

    def _line_tracking_parent_record(self):
        """Rodič řádku podle cesty `_line_tracking_parent` (prázdný záznam, když cesta nevede k rodiči)."""
        self.ensure_one()
        record = self
        for part in self._line_tracking_parent.split("."):
            record = record[part]
        return record

    def _line_tracking_desc(self):
        """Vrátí textový popis řádku pro použití ve zprávě v chatteru."""
        self.ensure_one()
        return self.display_name or f"{self._description} #{self.id}"

    def _line_tracking_get_fields(self):
        """Vrátí seznam sledovaných polí řádkového modelu."""
        if getattr(self, "_line_tracking_fields", None) is not None:
            return self._line_tracking_fields
        return tuple(name for name, field in self._fields.items() if getattr(field, "tracking", False))

    def _line_tracking_format_value(self, field_name):
        """Naformátuje hodnotu pole pro zobrazení ve zprávě."""
        field = self._fields[field_name]
        value = self[field_name]
        if field.type == "selection":
            return dict(field._description_selection(self.env)).get(value, value or "")
        if field.type == "boolean":
            return self.env._("Ano") if value else self.env._("Ne")
        if field.type == "many2one":
            return value.display_name if value else ""
        if field.type == "float":
            return f"{value:g}"
        return str(value) if value is not False and value is not None else ""

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if self.env.context.get("tracking_disable") or self.env.context.get("mail_create_nolog"):
            return records

        parent_field = self._line_tracking_parent_field()
        if parent_field:
            for parent, lines in records.grouped(lambda line: line._line_tracking_parent_record()).items():
                if not parent or not hasattr(parent, "message_post"):
                    continue
                items = []
                for line in lines:
                    desc = line._line_tracking_desc()
                    details = []
                    for fname in line._line_tracking_get_fields():
                        if fname == parent_field or fname == "sequence":
                            continue
                        fval = line._line_tracking_format_value(fname)
                        if fval:
                            details.append(f"{line._fields[fname].string}: {fval}")
                    detail_str = f" ({', '.join(details)})" if details else ""
                    items.append(Markup("<li>%s: %s%s</li>") % (self.env._("Přidáno"), desc, detail_str))
                if items:
                    parent.message_post(body=Markup("<ul>%s</ul>") % Markup().join(items))

        return records

    def write(self, vals):
        if self.env.context.get("tracking_disable"):
            return super().write(vals)

        parent_field = self._line_tracking_parent_field()
        tracked_fields = [f for f in self._line_tracking_get_fields() if f in vals]

        before = {}
        if parent_field and tracked_fields:
            for record in self:
                before[record.id] = {
                    fname: record._line_tracking_format_value(fname)
                    for fname in tracked_fields
                }

        result = super().write(vals)

        if before:
            for parent, lines in self.grouped(lambda line: line._line_tracking_parent_record()).items():
                if not parent or not hasattr(parent, "message_post"):
                    continue
                items = []
                for line in lines:
                    if line.id not in before:
                        continue
                    desc = line._line_tracking_desc()
                    for fname in tracked_fields:
                        old_val = before[line.id][fname]
                        new_val = line._line_tracking_format_value(fname)
                        if old_val != new_val:
                            label = line._fields[fname].string
                            items.append(Markup("<li>%s – %s: %s → %s</li>") % (
                                desc, label, old_val or "–", new_val or "–"
                            ))
                if items:
                    parent.message_post(body=Markup("<ul>%s</ul>") % Markup().join(items))

        return result

    def unlink(self):
        if self.env.context.get("tracking_disable"):
            return super().unlink()

        parent_field = self._line_tracking_parent_field()
        to_notify = []
        if parent_field:
            for parent, lines in self.grouped(lambda line: line._line_tracking_parent_record()).items():
                if parent and hasattr(parent, "message_post"):
                    items = [Markup("<li>%s: %s</li>") % (self.env._("Odebráno"), line._line_tracking_desc()) for line in lines]
                    to_notify.append((parent, items))

        result = super().unlink()

        for parent, items in to_notify:
            if parent.exists() and items:
                parent.message_post(body=Markup("<ul>%s</ul>") % Markup().join(items))

        return result
