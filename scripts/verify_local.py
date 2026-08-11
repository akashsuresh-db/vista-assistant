#!/usr/bin/env python3
"""Verify the planted analytical stories are visible in the generated CSVs,
i.e. that a Genie-style aggregation would actually surface them."""
import csv
import os
from collections import defaultdict

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")


def load(name):
    with open(os.path.join(D, name)) as f:
        return list(csv.DictReader(f))


gl = load("fact_gl_balance.csv")
bud = load("fact_budget.csv")
cc = {r["cost_center_code"]: r for r in load("dim_cost_center.csv")}
acct = {r["gl_account"]: r for r in load("dim_gl_account.csv")}
ent = {r["entity_code"]: r for r in load("dim_entity.csv")}

bud_ix = {(r["period"], r["cost_center_code"], r["gl_account"]): r for r in bud}

fails = []


def check(label, cond, detail):
    print(f"{'PASS' if cond else 'FAIL'}  {label}: {detail}")
    if not cond:
        fails.append(label)


# ---- S1: Cards & Payments opex variance in 2026-06
def lob_var(period, lob, only_expense=True):
    a = b = 0.0
    for r in gl:
        if r["period"] != period:
            continue
        if cc[r["cost_center_code"]]["lob"] != lob:
            continue
        if only_expense and acct[r["gl_account"]]["account_type"] != "Expense":
            continue
        a += float(r["amount_usd"])
        k = (r["period"], r["cost_center_code"], r["gl_account"])
        if k in bud_ix:
            b += float(bud_ix[k]["budget_usd"])
    return a, b, a - b


a, b, v = lob_var("2026-06", "Cards & Payments")
check("S1 Cards & Payments 2026-06 unfavourable > 2.0m",
      v > 2_000_000, f"actual {a:,.0f} vs budget {b:,.0f} -> var {v:,.0f}")

# S1 should be the single largest LOB variance in 2026-06
lob_vars = sorted(((lob, lob_var("2026-06", lob)[2]) for lob in
                   {c["lob"] for c in cc.values()}), key=lambda x: -x[1])
check("S1 Cards & Payments is the #1 overrun LOB",
      lob_vars[0][0] == "Cards & Payments",
      " | ".join(f"{l}:{x/1e6:+.2f}m" for l, x in lob_vars[:4]))

# S1 driver accounts
drv = defaultdict(float)
for r in gl:
    if r["period"] == "2026-06" and cc[r["cost_center_code"]]["lob"] == "Cards & Payments":
        k = (r["period"], r["cost_center_code"], r["gl_account"])
        if k in bud_ix:
            drv[acct[r["gl_account"]]["gl_account_name"]] += (
                float(r["amount_usd"]) - float(bud_ix[k]["budget_usd"]))
top = sorted(drv.items(), key=lambda x: -x[1])[:3]
check("S1 top driver is Professional Fees - Consulting",
      top[0][0] == "Professional Fees - Consulting",
      " | ".join(f"{n}:{x/1e3:+.0f}k" for n, x in top))

# S1 is a ramp (Apr < May < Jun), not a one-month spike
ramp = [lob_var(p, "Cards & Payments")[2] for p in ("2026-03", "2026-04", "2026-05", "2026-06")]
check("S1 shows a rising trend Mar->Jun",
      ramp[0] < ramp[1] < ramp[2] < ramp[3],
      " -> ".join(f"{x/1e6:+.2f}m" for x in ramp))

# ---- S2: EMEA FX headwind - unfavourable in USD, on-budget in local currency
for e in ("MB-UK", "MB-DE"):
    au = bu = al = 0.0
    for r in gl:
        if r["period"] != "2026-06" or r["entity_code"] != e:
            continue
        if acct[r["gl_account"]]["account_type"] != "Expense":
            continue
        au += float(r["amount_usd"])
        al += float(r["amount_local"])
        k = (r["period"], r["cost_center_code"], r["gl_account"])
        if k in bud_ix:
            bu += float(bud_ix[k]["budget_usd"])
    # budget in local currency at the ORIGINAL (Jan-2025) planning rate
    fx = {r["currency"]: r for r in load("dim_fx_rate.csv")
          if r["period"] == "2026-06" and r["rate_type"] == "MONTHLY_AVERAGE"}
    ccy = ent[e]["functional_currency"]
    rate_now = float(fx[ccy]["usd_per_unit"])
    fx_jan = {r["currency"]: float(r["usd_per_unit"]) for r in load("dim_fx_rate.csv")
              if r["period"] == "2025-01" and r["rate_type"] == "MONTHLY_AVERAGE"}
    bud_local = bu / fx_jan[ccy]
    check(f"S2 {e} USD unfavourable but local on-budget",
          au > bu and abs(al - bud_local) / bud_local < 0.12,
          f"USD act {au/1e6:.2f}m vs bud {bu/1e6:.2f}m (+{(au-bu)/1e3:.0f}k) | "
          f"local act {al/1e6:.2f}m vs bud-at-plan-rate {bud_local/1e6:.2f}m "
          f"({(al-bud_local)/bud_local*100:+.1f}%) | rate {fx_jan[ccy]:.3f}->{rate_now:.3f}")

# ---- S3 intercompany
ic = load("fact_intercompany.csv")
brk = [r for r in ic if r["status"] == "UNRESOLVED_BREAK"]
check("S3 unresolved IC break 482k in 2 periods",
      len(brk) == 2 and all(float(r["difference_usd"]) == 482_000 for r in brk),
      f"{len(brk)} rows: " + ", ".join(f"{r['period']} {r['billing_entity']}->{r['receiving_entity']}" for r in brk))

# ---- S4 aged accruals
ac = load("fact_accrual.csv")
aged = [r for r in ac if r["status"] == "OPEN" and int(r["age_days"]) > 90]
cards_aged = [r for r in aged if cc[r["cost_center_code"]]["lob"] == "Cards & Payments"]
check("S4 exactly 6 aged (>90d) open accruals, 4 in Cards & Payments",
      len(aged) == 6 and len(cards_aged) == 4,
      f"{len(aged)} aged, {len(cards_aged)} in Cards, "
      f"total {sum(float(r['accrual_amount_usd']) for r in aged):,.0f} USD")

# ---- S5 close SLA
ct = load("fact_close_task.csv")
br = [r for r in ct if r["period"] == "2026-06" and r["is_sla_breach"] == "Y"]
check("S5 exactly 3 SLA breaches in 2026-06 across 2 teams",
      len(br) == 3 and len({r["owner_team"] for r in br}) == 2,
      ", ".join(f"{r['entity_code']}/{r['task_name']}(+{r['days_late']}d)" for r in br))

# ---- S6 AP aging
ap = load("fact_ap_open_item.csv")
helix = [r for r in ap if r["vendor_id"] == "V1001" and r["aging_bucket"] == "90+"]
by_vendor_90 = defaultdict(float)
for r in ap:
    if r["aging_bucket"] == "90+":
        by_vendor_90[r["vendor_name"]] += float(r["invoice_amount_usd"])
rank = sorted(by_vendor_90.items(), key=lambda x: -x[1])
check("S6 Helix is the largest 90+ AP exposure (~1.31m, all disputed)",
      rank[0][0] == "Helix Consulting Partners" and all(r["status"] == "DISPUTED" for r in helix),
      " | ".join(f"{n}:{x/1e6:.2f}m" for n, x in rank[:3]))

# ---- referential integrity
orphan_cc = {r["cost_center_code"] for r in gl} - set(cc)
orphan_ac = {r["gl_account"] for r in gl} - set(acct)
check("Referential integrity (GL -> dims)",
      not orphan_cc and not orphan_ac,
      f"orphan cc={len(orphan_cc)} orphan acct={len(orphan_ac)}")

# ---- FX consistency: amount_local * rate == amount_usd
bad = [r for r in gl if abs(float(r["amount_local"]) * float(r["fx_rate_usd"]) - float(r["amount_usd"])) > 1.0]
check("FX consistency amount_local * rate = amount_usd", not bad, f"{len(bad)} mismatched rows")

print("\n" + ("ALL CHECKS PASSED" if not fails else f"FAILURES: {fails}"))
raise SystemExit(1 if fails else 0)
