#!/usr/bin/env python3
"""Test the Knowledge Assistant retrieves the right facts from each document.

Checks retrieval breadth (does it reach all 8 documents?) and accuracy (does it return
the actual figures, not plausible-sounding invented ones?).

Usage: python test_ka.py [endpoint_name]
"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app"))

from scripts.config import CFG
os.environ.setdefault("DATABRICKS_PROFILE", CFG.profile)

from backend import supervisor as sup  # noqa: E402

ENDPOINT = sys.argv[1] if len(sys.argv) > 1 else CFG.ka_endpoint
if not ENDPOINT:
    print("SKIP: ka_endpoint not configured in config.yaml", file=sys.stderr)
    sys.exit(0)

CASES = [
    ("What must happen to an accrual older than 90 days under FIN-ACC-014?",
     [r"90", r"revers|re-?substantiat", r"breach|exception"], "accrual policy"),
    ("Above what value does a MANUAL_ESTIMATE accrual need Financial Controller sign-off?",
     [r"50[,.]?000"], "accrual thresholds"),
    ("Under FIN-FX-007, how do I split a USD variance into local overspend and FX?",
     [r"constant.currency", r"plan rate|plan_?fx|locked"], "FX policy"),
    ("What is the reportable break threshold in the intercompany standard FIN-IC-021?",
     [r"250[,.]?000"], "intercompany policy"),
    ("On which close business day is the Group consolidation submission due?",
     [r"\b8\b|day 8|eight"], "close SOP"),
    ("What is the variance commentary threshold in the month-end close procedure?",
     [r"250[,.]?000"], "close SOP commentary rule"),
    ("Why was Project Helios spend not in the 2026 cost centre budgets?",
     [r"februar|after", r"aop.?2026|plan.*lock|locked"], "Helios business case"),
    ("What did internal audit memo IA-2026-11 find, and how much was involved?",
     [r"1[,.]?339[,.]?800|1\.3\d?\s*m", r"six|6\b"], "audit memo"),
    ("What did the Q2 2026 board pack say about the MB-UK FX translation impact?",
     [r"691|798|107"], "MD&A deck"),
    ("Which vendor has a disputed payables balance and why is it disputed?",
     [r"helix", r"rate.?card|price|blended"], "commentary / audit cross-doc"),
]

FAILS = []


def main():
    sup.ENDPOINT = ENDPOINT
    sup._w = None
    print(f"endpoint: {ENDPOINT}\n")
    for q, pats, doc in CASES:
        r = sup.ask(q)
        ans = (r["answer"] or "").lower()
        if r["error"]:
            print(f"FAIL  [{doc}] {q}\n        ERROR {r['error'][:160]}")
            FAILS.append(doc)
            continue
        missing = [p for p in pats if not re.search(p, ans)]
        ok = not missing
        print(f"{'PASS' if ok else 'FAIL'}  [{doc}] {q}")
        print(f"        {' '.join(r['answer'].split())[:260]}")
        if not ok:
            print(f"        missing: {missing}")
            FAILS.append(doc)
        print()
    print("=" * 70)
    if FAILS:
        print(f"{len(FAILS)}/{len(CASES)} FAILED: {FAILS}")
        return 1
    print(f"ALL {len(CASES)} KNOWLEDGE ASSISTANT CASES PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
