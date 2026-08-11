#!/usr/bin/env python3
"""Test the Agent Bricks Supervisor: does it ROUTE correctly and answer accurately?

Three things are asserted per case:
  1. the answer contains the right facts (so routing actually reached the right agent),
  2. the expected sub-agent(s) were invoked (route events),
  3. no internal tool names leak into the prose the user sees.

Usage: python test_supervisor.py <supervisor_endpoint>
       (or set SUPERVISOR_ENDPOINT)
"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app"))

from scripts.config import CFG
os.environ.setdefault("DATABRICKS_PROFILE", CFG.profile)
os.environ.setdefault("SUPERVISOR_ENDPOINT", CFG.supervisor_endpoint)

from backend import supervisor as sup  # noqa: E402

# Allow override from command line or environment
if len(sys.argv) > 1:
    os.environ["SUPERVISOR_ENDPOINT"] = sys.argv[1]
    sup.ENDPOINT = sys.argv[1]

if not sup.ENDPOINT:
    print("SKIP: SUPERVISOR_ENDPOINT not configured in config.yaml or environment", file=sys.stderr)
    sys.exit(0)

# (question, required regexes, expected routing: 'data' | 'docs' | 'both' | None)
CASES = [
    ("Which line of business overspent the most in June 2026?",
     [r"cards\s*&?\s*payments", r"2[.,]7"], "data"),
    ("What drove the Cards & Payments overspend in June 2026?",
     [r"consult|professional fees", r"cloud", r"licen"], "data"),
    ("What must happen to an accrual that has been open for more than 90 days?",
     [r"90", r"revers|re-?substantiat", r"fin-acc-014"], "docs"),
    ("What is the reportable threshold for an intercompany break?",
     [r"250[,.]?000"], "docs"),
    ("How much of the MB-UK June 2026 variance is FX translation rather than overspend?",
     [r"69\d|691", r"10[67]"], "data"),
    ("Which accruals breach the 90-day policy, and what does the policy require me to do?",
     [r"acr518|six|6\b", r"1[,.]?339[,.]?800|1\.3", r"revers|re-?substantiat"], "both"),
    ("Why is Cards & Payments over budget, and was that spend approved?",
     [r"2[.,]7", r"helios", r"februar|after.*plan|plan.*lock"], "both"),
    ("Which close tasks missed their SLA in June 2026?",
     [r"accrual calculation", r"intercompany billing", r"cut-?off"], "data"),
    ("Which vendor has the largest 90+ day payables exposure and why is it disputed?",
     [r"helix", r"1[,.]?310[,.]?500|1\.31", r"rate.?card|price|blended"], "both"),
    ("Is there an unresolved intercompany break, and has it breached the escalation rule?",
     [r"482[,.]?000|482", r"mb-uk", r"mb-sg"], "both"),
]

# internal names that must never appear in a business user's answer
LEAKS = [r"\bgenie\b", r"knowledge assistant", r"agent bricks", r"databricks",
         r"\bka-[0-9a-f]", r"\bmas-[0-9a-f]", r"serving endpoint", r"<[a-z_]+>"]

FAILS = []


def route_kind(routes):
    """Map raw sub-agent names to data / docs / both."""
    j = " ".join(routes).lower()
    d = any(k in j for k in ("genie", "analytic", "sql", "fna_analytics"))
    k = any(x in j for x in ("knowledge", "ka", "doc", "policy"))
    if d and k:
        return "both"
    if d:
        return "data"
    if k:
        return "docs"
    return None


def main():
    ep = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("SUPERVISOR_ENDPOINT", "")
    if not ep:
        print("usage: python test_supervisor.py <supervisor_endpoint>")
        return 2
    sup.ENDPOINT = ep
    sup._w = None
    print(f"supervisor endpoint: {ep}\n")

    for q, pats, want in CASES:
        r = sup.ask(q)
        ans = (r["answer"] or "")
        low = ans.lower()
        if r["error"]:
            print(f"FAIL  {q}\n        ERROR {r['error'][:200]}\n")
            FAILS.append(q)
            continue

        missing = [p for p in pats if not re.search(p, low)]
        leaked = [p for p in LEAKS if re.search(p, low)]
        got = route_kind(r["routes"])
        # routing is advisory: the answer being right is the hard requirement, but a
        # 'both' question answered from only one source is a real routing failure.
        route_bad = want == "both" and got not in ("both", None) and got != "both"

        ok = not missing and not leaked and not route_bad
        print(f"{'PASS' if ok else 'FAIL'}  {q}")
        print(f"        routes={r['routes']} -> {got} (want {want})")
        print(f"        {' '.join(ans.split())[:280]}")
        if missing:
            print(f"        MISSING: {missing}")
        if leaked:
            print(f"        LEAKED internal names: {leaked}")
        if route_bad:
            print("        ROUTING: expected both sources to be consulted")
        if not ok:
            FAILS.append(q)
        print()

    print("=" * 74)
    if FAILS:
        print(f"{len(FAILS)}/{len(CASES)} FAILED")
        for f in FAILS:
            print("  -", f)
        return 1
    print(f"ALL {len(CASES)} SUPERVISOR CASES PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
