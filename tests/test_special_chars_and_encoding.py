#!/usr/bin/env python3
"""Encoding safety: currency symbols and non-ASCII text must survive the whole path.

The demo carries GBP/EUR/INR amounts and vendor names with ampersands, and the chat
protocol is JSON-over-SSE. This checks nothing gets mangled between the warehouse, the
SSE frame and the rendered HTML.

Usage: python test_special_chars_and_encoding.py
"""
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from run_sql import run  # noqa: E402  (uses the shared statement-execution helper)

FAILS = []


def check(label, cond, detail=""):
    print(f"{'PASS' if cond else 'FAIL'}  {label}{(' — ' + detail) if detail else ''}")
    if not cond:
        FAILS.append(label)


def rows(stmt):
    r = run(stmt, show=False)
    return [list(x) for x in (r.result.data_array or [])] if r.result else []


def main():
    # ---- warehouse side
    ccy = [x[0] for x in rows("SELECT DISTINCT functional_currency FROM dim_entity "
                              "ORDER BY functional_currency")]
    check("all five currencies present", set(ccy) >= {"USD", "GBP", "EUR", "SGD", "INR"},
          str(ccy))

    amp = rows("SELECT lob FROM dim_cost_center WHERE lob LIKE '%&%' LIMIT 1")
    check("ampersand survives the warehouse round-trip",
          amp and "&" in amp[0][0], str(amp[:1]))

    # A vendor name and an LOB with an ampersand must be JSON-encodable for SSE.
    payload = {"type": "chunk", "text": "Cards & Payments — £798k / €228k / ₹1,31,000 · 6% ✓"}
    try:
        enc = json.dumps(payload)
        dec = json.loads(enc)
        ok = dec["text"] == payload["text"]
    except (UnicodeEncodeError, ValueError) as e:
        ok, enc = False, str(e)
    check("currency symbols + em dash survive JSON encode/decode", ok)

    # ---- SSE frame integrity: json.dumps must not emit a bare newline that would
    # split an SSE frame early.
    tricky = {"type": "chunk", "text": "line one\nline two\n\n| a | b |\n|---|---|\n"}
    frame = f"data: {json.dumps(tricky)}\n\n"
    check("embedded newlines are escaped, so one event stays one SSE frame",
          frame.count("\n\n") == 1 and "\\n" in frame,
          f"{frame.count(chr(10) + chr(10))} frame terminators")

    # ---- renderer side: non-ASCII and ampersands must render, and script must not
    js = r"""
const { renderMarkdown } = require(process.argv[2]);
let f = [];
const t = (l, c) => { console.log((c ? 'PASS  ' : 'FAIL  ') + l); if (!c) f.push(l); };

const out = renderMarkdown('**Cards & Payments** — £798k, €228k, ₹1,310,500 · 6% favourable');
t('ampersand escaped to &amp;', out.includes('Cards &amp; Payments'));
t('pound symbol preserved', out.includes('£798k'));
t('euro symbol preserved', out.includes('€228k'));
t('rupee symbol preserved', out.includes('₹1,310,500'));
t('em dash preserved', out.includes('—'));
t('middot preserved', out.includes('·'));

const tbl = renderMarkdown('| Vendor | Exposure |\n|---|---|\n| Sable & Roan LLP | £61,900 |');
t('ampersand in a table cell escaped', tbl.includes('Sable &amp; Roan LLP'));
t('currency cell right-aligned as numeric', tbl.includes('class="num"'));

const bad = renderMarkdown('<script>alert(1)</script> & <img src=x onerror=y>');
t('script tag neutralised', !bad.includes('<script>'));
t('img tag neutralised', !bad.includes('<img'));
t('lone ampersand escaped', bad.includes('&amp;'));

if (f.length) { console.log('JS FAILURES: ' + f.join(', ')); process.exit(1); }
"""
    if subprocess.run(["which", "node"], capture_output=True).returncode == 0:
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as fh:
            fh.write(js)
            tf = fh.name
        r = subprocess.run(["node", tf, os.path.join(ROOT, "app", "static", "app.js")],
                           capture_output=True, text=True)
        print(r.stdout.rstrip())
        check("renderer encoding suite", r.returncode == 0, r.stderr.strip()[:200])
        os.unlink(tf)
    else:
        print("SKIP  node not available for the renderer checks")

    print()
    if FAILS:
        print(f"{len(FAILS)} FAILURES: {FAILS}")
        return 1
    print("ALL ENCODING CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
