-- This file uses {catalog} and {schema} placeholders.
-- run_sql.py substitutes from CFG before executing.

-- Vega-Lite chart generation as a Unity Catalog function.
--
-- This follows the Agent Bricks recipe for adding visualisation to a Supervisor Agent
-- (go/agentbricks/faq -> "How can I add visualization capabilities to my Multi-Agent
-- System?", and the Databricks/AstraZeneca blog "Bringing visualizations to life in
-- multi-agent systems with Vega-Lite"): create a UC function that returns a Vega-Lite
-- spec, expose it to the agent over the managed MCP endpoint for UC functions, and render
-- the returned spec client-side.
--
-- Why a UC function rather than letting the model emit a spec free-hand:
--   * the spec is built by code, so it is always valid Vega-Lite v6 - no malformed JSON;
--   * field types are INFERRED from the data, so encodings are right (temporal vs ordinal
--     vs quantitative) without the model having to reason about it;
--   * it is a governed, auditable UC object with EXECUTE permissions, not prompt text;
--   * far cheaper and faster than a Python sandbox round-trip that renders a PNG.

CREATE OR REPLACE FUNCTION {catalog}.{schema}.make_chart(
  chart_type STRING COMMENT 'One of: bar, line, area, point (scatter), pie. Use line or area for a trend over time, bar to compare categories, point to relate two measures, pie only for parts of a single whole.',
  data_json  STRING COMMENT 'The rows to plot, as a JSON array of flat objects with identical keys, e.g. [{"period":"2026-01","variance_usd_m":0.2},{"period":"2026-02","variance_usd_m":0.07}]. Keep it under ~200 rows.',
  title      STRING COMMENT 'Chart title, written for a finance audience, e.g. "Cards & Payments variance by month, 2026 (USD m)".',
  x_field    STRING COMMENT 'Field name for the x axis (the category or time dimension).',
  y_field    STRING COMMENT 'Field name for the y axis (the measure).',
  series_field STRING COMMENT 'Optional field name to split the data into coloured series, or an empty string for a single series.'
)
RETURNS STRING
LANGUAGE PYTHON
COMMENT 'Builds a Vega-Lite v6 chart specification from a set of rows and returns it as JSON. Call this whenever a numeric answer would be clearer as a chart - a trend across periods, a ranking of cost centres or lines of business, a comparison of actual against budget. Pass the rows you already retrieved; do not invent data. Returns a JSON string starting with {"$schema": "https://vega.github.io/schema/vega-lite/v6.json". If the input cannot be charted it returns a JSON object with an "error" key instead.'
AS $$
import json


def _is_number(v):
    if isinstance(v, bool):
        return False
    if isinstance(v, (int, float)):
        return True
    if isinstance(v, str):
        s = v.strip().replace(",", "")
        for suffix in ("%",):
            if s.endswith(suffix):
                s = s[:-1]
        for prefix in ("$", "£", "€", "₹"):
            if s.startswith(prefix):
                s = s[1:]
        if s.startswith("(") and s.endswith(")"):   # accounting negatives
            s = "-" + s[1:-1]
        try:
            float(s)
            return True
        except ValueError:
            return False
    return False


def _to_number(v):
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return v
    s = str(v).strip().replace(",", "")
    neg = s.startswith("(") and s.endswith(")")
    if neg:
        s = s[1:-1]
    for ch in ("$", "£", "€", "₹", "%"):
        s = s.replace(ch, "")
    try:
        n = float(s)
    except ValueError:
        return None
    return -n if neg else n


# Period strings in this model are 'YYYY-MM' text, which Vega-Lite will happily treat as
# temporal if told to - but ordinal keeps the axis labels exactly as the ledger shows them,
# which is what a finance reader expects. Full dates are treated as temporal.
def _infer_type(values):
    vals = [v for v in values if v is not None and v != ""]
    if not vals:
        return "nominal"
    if all(_is_number(v) for v in vals):
        return "quantitative"
    if all(isinstance(v, str) and len(v) == 7 and v[4] == "-" for v in vals):
        return "ordinal"          # YYYY-MM accounting period
    if all(isinstance(v, str) and len(v) == 10 and v[4] == "-" and v[7] == "-"
           for v in vals):
        return "temporal"         # YYYY-MM-DD
    return "nominal"


def _err(msg):
    return json.dumps({"error": msg})


try:
    rows = json.loads(data_json) if data_json else None
except Exception as e:
    rows = None

if not isinstance(rows, list) or not rows:
    return _err("data_json must be a non-empty JSON array of objects")
rows = [r for r in rows if isinstance(r, dict)]
if not rows:
    return _err("data_json contained no objects")
if len(rows) > 500:
    rows = rows[:500]

keys = list(rows[0].keys())
if not keys:
    return _err("the first row has no fields")

ct = (chart_type or "bar").strip().lower()
alias = {"scatter": "point", "column": "bar", "donut": "arc", "pie": "arc",
         "barh": "bar", "trend": "line", "histogram": "bar"}
ct = alias.get(ct, ct)
if ct not in ("bar", "line", "area", "point", "arc"):
    ct = "bar"

x = (x_field or "").strip() or keys[0]
# default the measure to the first numeric field that is not the x axis
if (y_field or "").strip():
    y = y_field.strip()
else:
    y = next((k for k in keys
              if k != x and _infer_type([r.get(k) for r in rows]) == "quantitative"),
             keys[-1])
series = (series_field or "").strip()

for f, label in ((x, "x_field"), (y, "y_field")):
    if f not in keys:
        return _err(f"{label} '{f}' is not present in the data (fields: {keys})")
if series and series not in keys:
    series = ""

x_type = _infer_type([r.get(x) for r in rows])
y_type = _infer_type([r.get(y) for r in rows])
if y_type != "quantitative":
    return _err(f"y_field '{y}' is not numeric, so it cannot be plotted on the value axis")

# coerce the measure to real numbers so Vega-Lite does not have to parse '1,234' or '$5'
clean = []
for r in rows:
    row = dict(r)
    n = _to_number(r.get(y))
    if n is None:
        continue
    row[y] = n
    if series:
        row[series] = "" if r.get(series) is None else str(r.get(series))
    clean.append(row)
if not clean:
    return _err(f"no rows had a numeric value for '{y}'")

# Accent colour from configuration, with a categorical ramp for multi-series charts.
ACCENT = "#a100ff"
RANGE = ["#a100ff", "#7500c0", "#c86bff", "#460073", "#e0b3ff", "#2b0044"]

ACRONYMS = {"usd", "gbp", "eur", "sgd", "inr", "fx", "gl", "lob", "ytd", "sla",
            "po", "ap", "ar", "id", "pct", "qty", "m", "k", "bn"}
UNIT = {"m": "USD m", "k": "USD k", "usd": "USD", "pct": "%"}


def axis_title(f):
    """Human axis label. Finance acronyms must not be title-cased into 'Usd'."""
    parts = [p for p in f.replace("-", "_").split("_") if p]
    out = []
    for p in parts:
        out.append(p.upper() if p.lower() in ACRONYMS else p.capitalize())
    return " ".join(out)

spec = {
    "$schema": "https://vega.github.io/schema/vega-lite/v6.json",
    "title": {"text": title or axis_title(y), "anchor": "start",
              "fontSize": 14, "fontWeight": 600, "color": "#0d0d0d",
              "subtitleColor": "#767676"},
    "data": {"values": clean},
    "width": "container",
    "height": 300,
    # "fit" lays the plot out inside the container width, leaving room for axis labels.
    # This only works if CSS does not then rescale the canvas - see the note in styles.css.
    "autosize": {"type": "fit", "contains": "padding"},
    "background": "transparent",
    "config": {
        "font": "-apple-system, BlinkMacSystemFont, Segoe UI, Inter, Roboto, sans-serif",
        "axis": {"labelColor": "#4a4a4a", "titleColor": "#4a4a4a",
                 "labelFontSize": 11, "titleFontSize": 11,
                 "gridColor": "#eeeeee", "domainColor": "#e4e4e7",
                 "tickColor": "#e4e4e7"},
        "legend": {"labelColor": "#4a4a4a", "titleColor": "#4a4a4a",
                   "labelFontSize": 11, "titleFontSize": 11},
        "view": {"stroke": None},
        "range": {"category": RANGE},
    },
}

tooltip = [
    {"field": x, "type": x_type, "title": axis_title(x)},
    {"field": y, "type": "quantitative", "title": axis_title(y), "format": ",.4~f"},
]
if series:
    tooltip.append({"field": series, "type": "nominal", "title": axis_title(series)})

# A chart is a summary, not a listing. Beyond ~14 categories the bars get too thin to
# compare and the chart grows taller than the screen, so keep the biggest by absolute
# value and say so in the subtitle - the full set is already in the answer's table.
# This applies to both arc (pie) and non-arc charts.
CAP = 14
cats = list(dict.fromkeys(str(r.get(x)) for r in clean))
trimmed = 0
if ct in ("bar", "arc") and not series and len(cats) > CAP:
    totals = {}
    for r in clean:
        k = str(r.get(x))
        totals[k] = totals.get(k, 0) + abs(_to_number(r.get(y)) or 0)
    keep = {k for k, _ in sorted(totals.items(), key=lambda kv: -kv[1])[:CAP]}
    trimmed = len(cats) - len(keep)
    clean = [r for r in clean if str(r.get(x)) in keep]
    spec["data"] = {"values": clean}
    spec["title"]["subtitle"] = (
        f"Top {CAP} of {len(cats)} by value ({trimmed} smaller not shown)")
    spec["title"]["subtitleFontSize"] = 11

if ct == "arc":
    # parts of a whole: theta by the measure, colour by the category
    spec["mark"] = {"type": "arc", "innerRadius": 58, "outerRadius": 110,
                    "stroke": "#ffffff", "strokeWidth": 1.5}
    spec["height"] = 280
    spec["encoding"] = {
        "theta": {"field": y, "type": "quantitative", "stack": True},
        "color": {"field": x, "type": "nominal",
                  "title": axis_title(x),
                  "scale": {"range": RANGE},
                  "legend": {"orient": "right"}},
        "tooltip": tooltip,
    }
else:
    # cornerRadiusEnd rounds the *value* end of the bar; Vega-Lite picks the correct pair
    # of corners from the orientation, so this is right for horizontal bars too.
    mark = {"bar": {"type": "bar", "cornerRadiusEnd": 3},
            "line": {"type": "line", "point": {"filled": True, "size": 55},
                     "strokeWidth": 2.5},
            "area": {"type": "area", "line": {"strokeWidth": 2.5},
                     "opacity": 0.75, "point": {"filled": True, "size": 45}},
            "point": {"type": "point", "filled": True, "size": 90}}[ct]
    if not series:
        mark["color"] = ACCENT
        # `mark.color` does not cascade to the point overlay on line/area marks, which
        # would otherwise render in Vega-Lite's default blue.
        if isinstance(mark.get("point"), dict):
            mark["point"]["color"] = ACCENT
        if isinstance(mark.get("line"), dict):
            mark["line"]["color"] = ACCENT
    spec["mark"] = mark

    # Long category names (line-of-business, cost-centre and vendor names all run long)
    # collide at labelAngle 0. Angle them once the labels get wide, and cap the label
    # length so the axis cannot eat the plot area.
    # ---- ORIENTATION
    # Long category names (line-of-business, cost-centre and vendor names all run long)
    # cannot fit side by side on a vertical axis. Rotating them 45 degrees is the usual
    # reflex but it stays hard to read and still collides in a narrow column, so a
    # CATEGORICAL BAR CHART WITH LONG NAMES IS DRAWN HORIZONTALLY instead: the category
    # sits on y, where a long label has the whole row width to itself and stays upright.
    # Time series are never flipped - a period axis must read left to right.
    longest = max((len(str(r.get(x, ""))) for r in clean), default=0)
    horizontal = (ct == "bar" and x_type == "nominal"
                  and (longest > 12 or len(clean) > 6))

    # Ordinal time axes (YYYY-MM) are dense and collide at labelAngle 0. When there are
    # many periods, angle them. A period axis is the one case we DO angle rather than flip,
    # because time has to read left to right.
    # NOTE the sign: -45 slants the text down-to-the-right so each label ends AT its tick
    # and is read on a natural downward sweep. +45 slants the other way, so labels lean
    # away from their tick and the eye has to travel upward against the reading direction.
    x_label_angle = 0
    x_label_align = "center"
    if x_type == "ordinal" and not horizontal and len(clean) > 12:
        x_label_angle, x_label_align = -45, "right"
    cat_axis = {"field": x, "type": x_type, "title": axis_title(x),
                "axis": {"labelLimit": 220, "labelAngle": x_label_angle,
                         "labelAlign": x_label_align,
                         "labelBaseline": "middle" if x_label_angle else "top"}}
    val_axis = {"field": y, "type": "quantitative", "title": axis_title(y),
                "axis": {"format": ",.4~f"}}

    if horizontal:
        # ranking: biggest at the top, so the eye lands on what matters first
        if not series:
            cat_axis["sort"] = "-x"
        enc = {"y": cat_axis, "x": val_axis, "tooltip": tooltip}
        # Height grows per row so bars never squash, but is CAPPED: an uncapped chart of
        # every cost centre ran to 1300px, which is a scrolling exercise rather than a
        # chart. Rows are trimmed to a top-N above (see cap_rows) so the two stay in step.
        n_cats = len(set(str(r.get(x)) for r in clean))
        per_row = 30 if series else 26
        spec["height"] = min(430, max(150, per_row * n_cats + 30))

        # THE OVERLAP BUG WAS HERE. cat_axis is built for a VERTICAL axis, so it carries
        # labelAlign "center" / labelBaseline "top" (correct under an x axis). Reused
        # unchanged on a y axis those centre each label horizontally ON the plot area, so
        # the text sits on top of the bars. A y axis needs the labels right-aligned and
        # vertically centred against their row, OUTSIDE the plot.
        cat_axis["axis"]["labelAlign"] = "right"
        cat_axis["axis"]["labelBaseline"] = "middle"
        cat_axis["axis"]["labelPadding"] = 6
        # Cap how much width a label may claim so a very long name cannot squeeze the bars
        # into nothing; `autosize: fit` reserves the rest.
        cat_axis["axis"]["labelLimit"] = min(200, max(70, int(longest * 6.4) + 12))
        if series:
            enc["yOffset"] = {"field": series}
    else:
        if ct == "bar" and x_type == "nominal" and not series:
            cat_axis["sort"] = "-y"
        enc = {"x": cat_axis, "y": val_axis, "tooltip": tooltip}
        if series and ct == "bar":
            enc["xOffset"] = {"field": series}   # grouped, not stacked

    if series:
        enc["color"] = {"field": series, "type": "nominal",
                        "title": axis_title(series),
                        "scale": {"range": RANGE}}
    spec["encoding"] = enc

return json.dumps(spec)
$$;

-- GRANTS ARE PART OF THIS FILE ON PURPOSE.
-- CREATE OR REPLACE FUNCTION *drops* existing grants. When that happened silently after an
-- edit, the Supervisor could no longer register the tool and then failed EVERY request with
-- "Failed to register UC function tool ... Verify the function exists and is accessible",
-- which surfaced in the app as an empty response. Re-issuing the grants here makes the file
-- self-contained and idempotent.
--
-- `account users` is granted because the Supervisor invokes tools as its own identity,
-- which cannot be enumerated through the API. Narrow this in a real deployment.
GRANT EXECUTE ON FUNCTION {catalog}.{schema}.make_chart
  TO `account users`;
