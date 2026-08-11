#!/usr/bin/env python3
"""Test the Vega-Lite chart path.

Three layers:
  A. the make_chart UC function - valid v6 specs, type inference, number coercion,
     Accenture palette, and clean errors on bad input;
  B. spec extraction in the backend - finds specs inside tool output/prose, survives
     braces inside strings, and strips the JSON out of the answer text;
  C. the specs actually render (vl-convert), so a spec that is "valid JSON" but not a
     drawable chart is caught.

Usage: python tests/test_charts.py
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, os.path.join(ROOT, "app"))

from config import CFG  # noqa: E402
from run_sql import run  # noqa: E402

FAILS = []
FN = CFG.table("make_chart")

# the real planted story: the Cards & Payments ramp
TREND = [{"period": "2026-01", "variance_usd_m": 0.2},
         {"period": "2026-02", "variance_usd_m": 0.07},
         {"period": "2026-03", "variance_usd_m": 0.53},
         {"period": "2026-04", "variance_usd_m": 0.65},
         {"period": "2026-05", "variance_usd_m": 1.46},
         {"period": "2026-06", "variance_usd_m": 2.72}]


def check(label, cond, detail=""):
    print(f"{'PASS' if cond else 'FAIL'}  {label}{(' — ' + detail) if detail else ''}")
    if not cond:
        FAILS.append(label)


def make(ct, data, title="T", x="", y="", series=""):
    stmt = (f"SELECT {FN}({ct!r}, {json.dumps(data)!r}, {title!r}, "
            f"{x!r}, {y!r}, {series!r})")
    return run(stmt, show=False).result.data_array[0][0]


def part_a():
    print("\n=== A. make_chart UC function ===")
    raw = make("line", TREND, "Cards & Payments variance by month, 2026 (USD m)",
               "period", "variance_usd_m")
    spec = json.loads(raw)
    check("returns Vega-Lite v6 schema",
          spec.get("$schema") == "https://vega.github.io/schema/vega-lite/v6.json",
          str(spec.get("$schema")))
    check("line mark for a trend", spec["mark"]["type"] == "line")
    check("data embedded in the spec", len(spec["data"]["values"]) == 6)
    check("YYYY-MM period kept ordinal, not mangled to a date",
          spec["encoding"]["x"]["type"] == "ordinal")
    check("period labels preserved exactly",
          spec["data"]["values"][0]["period"] == "2026-01")
    check("Accenture purple applied to the mark",
          spec["mark"].get("color") == "#a100ff")
    check("point overlay also purple (does not inherit)",
          spec["mark"].get("point", {}).get("color") == "#a100ff")
    check("axis acronyms not title-cased into 'Usd'",
          "USD" in spec["encoding"]["y"]["title"], spec["encoding"]["y"]["title"])
    check("width is container-relative for responsive layout",
          spec.get("width") == "container")
    check("tooltip present for interactivity", "tooltip" in spec["encoding"])

    # money strings must be coerced to numbers
    money = [{"lob": "Cards & Payments", "variance": "$2,722,824"},
             {"lob": "Corporate Banking", "variance": "$340,120"},
             {"lob": "Technology", "variance": "(1,200)"}]
    s2 = json.loads(make("bar", money, "Variance by LOB", "lob", "variance"))
    vals = [v["variance"] for v in s2["data"]["values"]]
    check("currency symbols and thousands separators coerced",
          vals[0] == 2722824.0 and vals[1] == 340120.0, str(vals))
    check("accounting negatives coerced to negative numbers",
          vals[2] == -1200.0, str(vals[2]))
    # ORIENTATION: long category names go HORIZONTAL (category on y), because rotated
    # x labels stay hard to read and collide in a narrow column. Ranked biggest-first.
    check("long-named categories drawn horizontally",
          s2["encoding"]["y"]["field"] == "lob", str(list(s2["encoding"].keys())))
    check("horizontal bars ranked biggest first",
          s2["encoding"]["y"].get("sort") == "-x")
    check("category labels upright (never rotated)",
          s2["encoding"]["y"]["axis"].get("labelAngle") == 0)
    check("height grows with the row count so bars are not squashed",
          s2["height"] >= 150)

    short = [{"entity": "MB-UK", "v": 798}, {"entity": "MB-DE", "v": 228}]
    s2b = json.loads(make("bar", short, "Short labels", "entity", "v"))
    check("short labels with few categories stay vertical",
          s2b["encoding"]["x"]["field"] == "entity")

    period_bars = json.loads(make("bar", TREND, "Periods", "period", "variance_usd_m"))
    check("a period axis is never flipped (must read left to right)",
          period_bars["encoding"]["x"]["field"] == "period")

    # ordinal x-axis (YYYY-MM periods) collide at labelAngle 0; rotate them when >12 rows
    long_trend = [{"period": f"202{5+i//12}-{(i%12)+1:02d}", "v": 100 + i*5}
                  for i in range(18)]
    line_18 = json.loads(make("line", long_trend, "18-month trend", "period", "v"))
    check("ordinal x-axis with >12 rows angles labels for readability",
          line_18["encoding"]["x"]["axis"].get("labelAngle") == -45)

    short_trend = [{"period": f"202{5}-{i+1:02d}", "v": 100 + i*10} for i in range(6)]
    line_6 = json.loads(make("line", short_trend, "6-month trend", "period", "v"))
    check("ordinal x-axis with <=12 rows stays upright (labelAngle 0)",
          line_6["encoding"]["x"]["axis"].get("labelAngle") == 0)

    # multi-series -> grouped, with the purple ramp
    ms = [{"entity": "MB-UK", "kind": "Reported", "v": 798},
          {"entity": "MB-UK", "kind": "Constant ccy", "v": 107},
          {"entity": "MB-DE", "kind": "Reported", "v": 228},
          {"entity": "MB-DE", "kind": "Constant ccy", "v": 49}]
    s3 = json.loads(make("bar", ms, "Reported vs constant currency", "entity", "v", "kind"))
    check("multi-series bars are grouped, not stacked",
          "xOffset" in s3["encoding"] or "yOffset" in s3["encoding"],
          str(list(s3["encoding"].keys())))
    check("series uses the purple categorical ramp",
          s3["encoding"]["color"]["scale"]["range"][0] == "#a100ff")

    # pie/arc
    s4 = json.loads(make("pie", money, "Share", "lob", "variance"))
    check("pie maps to an arc mark with theta",
          s4["mark"]["type"] == "arc" and "theta" in s4["encoding"])

    # aliases and unknown types degrade sensibly
    s5 = json.loads(make("scatter", TREND, "t", "period", "variance_usd_m"))
    check("'scatter' aliases to a point mark", s5["mark"]["type"] == "point")
    s6 = json.loads(make("banana", TREND, "t", "period", "variance_usd_m"))
    check("unknown chart type falls back to bar", s6["mark"]["type"] == "bar")

    # inference when fields are omitted
    s7 = json.loads(make("line", TREND, "t"))
    check("x/y inferred when not supplied",
          s7["encoding"]["x"]["field"] == "period"
          and s7["encoding"]["y"]["field"] == "variance_usd_m")

    # errors
    print("  -- error handling")
    for label, out, needle in [
        ("empty array", make("bar", [], "t", "a", "b"), "non-empty"),
        ("non-numeric y", make("bar", [{"a": "x", "b": "y"}], "t", "a", "b"), "not numeric"),
        ("missing field", make("bar", TREND, "t", "nope", "variance_usd_m"), "not present"),
    ]:
        d = json.loads(out)
        check(f"{label} returns a clear error", "error" in d and needle in d["error"],
              out[:90])

    bad = json.loads(run(f"SELECT {FN}('bar', 'not json', 't', 'a', 'b', '')",
                         show=False).result.data_array[0][0])
    check("malformed JSON returns an error, not a crash", "error" in bad)


def part_a2():
    """Angled period labels must use the -45 convention."""
    print("\n=== A2. period axis label angle ===")
    per = [{"period": f"{y}-{m:02d}", "v": m} for y in (2025, 2026) for m in range(1, 13)][:18]
    many = json.loads(make("line", per, "18 periods", "period", "v"))
    ax = many["encoding"]["x"]["axis"]
    # -45 slants text down-to-the-right so each label ENDS at its tick; +45 leans the
    # other way and reads against the eye's direction of travel.
    check("dense period axis angles labels at -45 (not +45)",
          ax.get("labelAngle") == -45, str(ax.get("labelAngle")))
    check("angled labels right-aligned so they end at the tick",
          ax.get("labelAlign") == "right", str(ax.get("labelAlign")))
    few = json.loads(make("line", per[:6], "6 periods", "period", "v"))
    check("sparse period axis stays horizontal",
          few["encoding"]["x"]["axis"].get("labelAngle") == 0)


def part_b():
    print("\n=== B. backend spec extraction ===")
    from backend.supervisor import _extract_vega_specs, _strip_vega_blocks

    spec = ('{"$schema":"https://vega.github.io/schema/vega-lite/v6.json",'
            '"mark":"line","data":{"values":[{"a":1}]},"encoding":{}}')

    check("finds a bare spec in prose",
          len(_extract_vega_specs(f"Trend:\n\n{spec}\n\nClear.")) == 1)
    check("finds a fenced spec",
          len(_extract_vega_specs(f"See:\n```json\n{spec}\n```\n")) == 1)
    check("finds two specs", len(_extract_vega_specs(f"{spec} and {spec}")) == 2)

    tricky = ('{"$schema":"https://vega.github.io/schema/vega-lite/v6.json",'
              '"mark":"bar","title":"a } brace {","data":{"values":[]},"encoding":{}}')
    got = _extract_vega_specs(tricky)
    check("braces inside strings do not break brace matching",
          len(got) == 1 and got[0]["title"] == "a } brace {")

    check("ignores JSON that is not a chart spec",
          _extract_vega_specs('{"$schema":"https://example.com/x.json","a":1}') == [])
    check("no spec in plain prose", _extract_vega_specs("just prose") == [])

    stripped = _strip_vega_blocks(f"Here is the trend:\n\n```json\n{spec}\n```\n\nDone.")
    check("spec JSON removed from the answer text",
          "$schema" not in stripped and "Here is the trend:" in stripped
          and "Done." in stripped, repr(stripped)[:80])
    check("empty code fence cleaned up", "```" not in stripped)
    check("prose without a spec is untouched",
          _strip_vega_blocks("just prose") == "just prose")


def part_c():
    print("\n=== C. specs actually render ===")
    try:
        import vl_convert as vlc
    except ImportError:
        print("SKIP  vl-convert-python not installed")
        return
    for ct in ("line", "bar", "area", "point", "pie"):
        spec = json.loads(make(ct, TREND, f"Variance ({ct})", "period", "variance_usd_m"))
        spec["width"] = 500          # container width is browser-only
        try:
            png = vlc.vegalite_to_png(json.dumps(spec), scale=1)
            ok = len(png) > 5000
        except Exception as e:
            ok, png = False, b""
            print("   render error:", str(e)[:160])
        check(f"{ct} renders to an image", ok, f"{len(png)} bytes")

    print("  -- edge cases")
    # Extreme label length
    extreme = [{"entity": "Financial Crime Compliance and Regulatory Reporting EMEA Division", "v": 100}]
    s_ext = json.loads(make("bar", extreme, "Extreme label", "entity", "v"))
    spec_ext = dict(s_ext)
    spec_ext["width"] = 700
    try:
        png_ext = vlc.vegalite_to_png(json.dumps(spec_ext), scale=1)
        check("extreme 60+ char label renders without clipping", len(png_ext) > 3000)
    except Exception as e:
        check("extreme label renders", False, str(e)[:80])

    # Many categories with multi-series at narrow width
    ms_8 = [{"cat": f"C{i}", "series": s, "v": 100 + i*10 + (10 if s == "S2" else 0)}
            for i in range(8) for s in ("S1", "S2")]
    s_ms = json.loads(make("bar", ms_8, "Multi-series 8x2", "cat", "v", "series"))
    spec_ms = dict(s_ms)
    spec_ms["width"] = 480
    try:
        png_ms = vlc.vegalite_to_png(json.dumps(spec_ms), scale=1)
        check("multi-series grouped bar at 480px renders", len(png_ms) > 3000)
    except Exception as e:
        check("multi-series at 480px renders", False, str(e)[:80])

    # Pie with 20 categories (should trim)
    pie_20 = [{"item": f"Item{i:02d}", "amount": 100 + (20-i)*10} for i in range(20)]
    s_pie = json.loads(make("pie", pie_20, "Pie 20 items", "item", "amount"))
    check("pie with >14 categories has trimmed subtitle",
          s_pie["title"].get("subtitle") and "Top 14" in s_pie["title"]["subtitle"])
    spec_pie = dict(s_pie)
    spec_pie["width"] = 480
    try:
        png_pie = vlc.vegalite_to_png(json.dumps(spec_pie), scale=1)
        check("pie trimmed to 14 renders at 480px", len(png_pie) > 3000)
    except Exception as e:
        check("pie at 480px renders", False, str(e)[:80])

    # Mixed positive/negative
    mixed = [{"period": "2026-01", "v": 100},
             {"period": "2026-02", "v": -50},
             {"period": "2026-03", "v": 75}]
    s_mixed = json.loads(make("bar", mixed, "Mixed", "period", "v"))
    spec_mixed = dict(s_mixed)
    spec_mixed["width"] = 700
    try:
        png_mixed = vlc.vegalite_to_png(json.dumps(spec_mixed), scale=1)
        check("mixed pos/neg bar chart renders", len(png_mixed) > 3000)
    except Exception as e:
        check("mixed pos/neg renders", False, str(e)[:80])


def main():
    part_a()
    part_a2()
    part_b()
    part_c()
    print("\n" + "=" * 70)
    if FAILS:
        print(f"{len(FAILS)} FAILURES: {FAILS}")
        return 1
    print("ALL CHART TESTS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
