#!/usr/bin/env python3
"""Generate the structured FnA datasets for Meridian Bank Finance Shared Services.

Writes CSVs to ../data/ using only the stdlib (pandas is broken in this env).
The numbers are deliberately internally consistent: FX-translated USD amounts tie
to local amounts, budget/actual variances tie to the planted stories, and the
unstructured policy documents reference the same figures.

PLANTED STORIES (each one is answerable from the data and cross-referenced by a
document in the UC Volume):
  S1  Cards & Payments technology overrun in 2026-06: +2.40m USD unfavourable,
      concentrated in Professional Fees / Software Licences on the cloud migration.
  S2  EMEA FX headwind: GBP/EUR weakened through H1-2026, so MB-UK and MB-DE look
      unfavourable in USD but are on-budget in local currency.
  S3  Intercompany break of 482k USD between MB-UK and MB-SG, unresolved 2 periods.
  S4  Aged accruals: 6 accruals older than 90 days (policy requires reversal),
      4 of them in Cards & Payments -> ties to the internal audit memo.
  S5  Month-end close SLA breaches in 2026-06: 3 tasks late, 2 teams.
  S6  AP aging spike: vendor Helix Consulting disputed invoices, 1.31m > 90 days.
"""
import csv
import os
import random
from datetime import date, timedelta

random.seed(20260806)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------- periods / fx
PERIODS = []  # 2025-01 .. 2026-06
for y in (2025, 2026):
    for m in range(1, 13):
        if y == 2026 and m > 6:
            break
        PERIODS.append(f"{y}-{m:02d}")

ENTITIES = [
    # entity_code, entity_name, currency, region
    ("MB-US", "Meridian Bank N.A.", "USD", "North America"),
    ("MB-UK", "Meridian Bank plc", "GBP", "EMEA"),
    ("MB-DE", "Meridian Bank Europe GmbH", "EUR", "EMEA"),
    ("MB-SG", "Meridian Bank Singapore Ltd", "SGD", "APAC"),
    ("MB-IN", "Meridian Global Services India", "INR", "APAC"),
]

# S2: GBP and EUR STRENGTHEN against USD across the horizon. Because MB-UK / MB-DE
# spend in GBP/EUR but Group reports in USD, a stronger local currency makes the same
# local spend cost MORE in USD -> unfavourable in USD while on-budget locally.
FX_BASE = {"USD": 1.0, "GBP": 1.180, "EUR": 0.995, "SGD": 0.735, "INR": 0.01175}
FX_DRIFT = {"USD": 0.0, "GBP": 0.0068, "EUR": 0.0055, "SGD": 0.0004, "INR": 0.000012}


_FX_CACHE = {}


def fx_rate(currency: str, period: str) -> float:
    """USD per 1 unit of local currency. Monotone drift + small monthly noise.
    Memoised so every consumer (facts, budgets, dim_fx_rate) sees the same rate."""
    if currency == "USD":
        return 1.0
    key = (currency, period)
    if key not in _FX_CACHE:
        i = PERIODS.index(period)
        base = FX_BASE[currency] + FX_DRIFT[currency] * i
        noise = random.uniform(-0.003, 0.003) * FX_BASE[currency]
        _FX_CACHE[key] = round(base + noise, 6)
    return _FX_CACHE[key]


# ------------------------------------------------------------------- dimensions
LOBS = [
    "Retail Banking",
    "Cards & Payments",
    "Wealth Management",
    "Corporate Banking",
    "Treasury",
    "Technology",
    "Operations",
    "Risk & Compliance",
]

OWNERS = [
    "A. Raghavan", "M. Okonkwo", "S. Lindqvist", "P. Nakamura", "D. Ferreira",
    "H. Al-Mansouri", "J. Whitfield", "L. Moreau", "R. Chatterjee", "T. Novak",
    "C. Bianchi", "N. Oyelaran", "V. Sokolov", "E. Bergström", "K. Dlamini",
]

COST_CENTERS = []  # cc_code, cc_name, lob, entity, region, owner, fte_band
_cc_seq = 1000


def add_cc(name, lob, entity):
    global _cc_seq
    _cc_seq += 10
    code = f"CC{_cc_seq}"
    ent = [e for e in ENTITIES if e[0] == entity][0]
    COST_CENTERS.append({
        "cost_center_code": code,
        "cost_center_name": name,
        "lob": lob,
        "entity_code": entity,
        "region": ent[3],
        "cc_owner": random.choice(OWNERS),
    })
    return code


CC_LAYOUT = [
    ("Retail Branch Network", "Retail Banking", "MB-US"),
    ("Retail Digital Channels", "Retail Banking", "MB-US"),
    ("Retail Banking UK", "Retail Banking", "MB-UK"),
    ("Retail Products EMEA", "Retail Banking", "MB-DE"),
    ("Mortgages & Lending", "Retail Banking", "MB-US"),
    ("Cards Issuing", "Cards & Payments", "MB-US"),
    ("Cards Acquiring", "Cards & Payments", "MB-US"),
    ("Cards Platform Engineering", "Cards & Payments", "MB-US"),
    ("Payments Operations", "Cards & Payments", "MB-IN"),
    ("Cards UK", "Cards & Payments", "MB-UK"),
    ("Fraud & Disputes", "Cards & Payments", "MB-IN"),
    ("Private Banking", "Wealth Management", "MB-UK"),
    ("Wealth Advisory APAC", "Wealth Management", "MB-SG"),
    ("Asset Management", "Wealth Management", "MB-US"),
    ("Corporate Coverage", "Corporate Banking", "MB-US"),
    ("Trade Finance", "Corporate Banking", "MB-SG"),
    ("Transaction Banking EMEA", "Corporate Banking", "MB-DE"),
    ("Syndicated Lending", "Corporate Banking", "MB-UK"),
    ("Treasury ALM", "Treasury", "MB-US"),
    ("Liquidity Management", "Treasury", "MB-UK"),
    ("Markets Treasury APAC", "Treasury", "MB-SG"),
    ("Core Banking Platform", "Technology", "MB-US"),
    ("Cloud & Infrastructure", "Technology", "MB-US"),
    ("Data & Analytics Platform", "Technology", "MB-IN"),
    ("Cyber Security", "Technology", "MB-US"),
    ("Technology EMEA", "Technology", "MB-UK"),
    ("Enterprise Applications", "Technology", "MB-IN"),
    ("Finance Shared Services", "Operations", "MB-IN"),
    ("Record to Report", "Operations", "MB-IN"),
    ("Procure to Pay", "Operations", "MB-IN"),
    ("Order to Cash", "Operations", "MB-IN"),
    ("Client Onboarding Ops", "Operations", "MB-SG"),
    ("Branch Operations Support", "Operations", "MB-US"),
    ("Regulatory Reporting", "Risk & Compliance", "MB-UK"),
    ("Financial Crime Compliance", "Risk & Compliance", "MB-SG"),
    ("Enterprise Risk", "Risk & Compliance", "MB-US"),
    ("Internal Audit", "Risk & Compliance", "MB-US"),
    ("Model Risk Management", "Risk & Compliance", "MB-UK"),
]
for nm, lob, ent in CC_LAYOUT:
    add_cc(nm, lob, ent)

CC_BY_LOB = {}
for cc in COST_CENTERS:
    CC_BY_LOB.setdefault(cc["lob"], []).append(cc)


def cc_by_name(name):
    return [c for c in COST_CENTERS if c["cost_center_name"] == name][0]


# GL accounts: code, name, type, category, is_controllable, typical monthly scale (USD)
GL_ACCOUNTS = [
    ("510100", "Salaries & Wages", "Expense", "Personnel", "Y", 900_000),
    ("510200", "Bonus & Incentives", "Expense", "Personnel", "Y", 260_000),
    ("510300", "Employer Social Charges", "Expense", "Personnel", "N", 140_000),
    ("510400", "Contractor & Temp Labour", "Expense", "Personnel", "Y", 180_000),
    ("510500", "Recruitment Costs", "Expense", "Personnel", "Y", 32_000),
    ("510600", "Training & Development", "Expense", "Personnel", "Y", 24_000),
    ("520100", "Software Licences", "Expense", "Technology", "Y", 210_000),
    ("520200", "Cloud Hosting & Compute", "Expense", "Technology", "Y", 185_000),
    ("520300", "Data Centre & Hardware", "Expense", "Technology", "Y", 95_000),
    ("520400", "Telecom & Network", "Expense", "Technology", "Y", 42_000),
    ("520500", "IT Support & Maintenance", "Expense", "Technology", "Y", 88_000),
    ("530100", "Professional Fees - Consulting", "Expense", "Professional Fees", "Y", 130_000),
    ("530200", "Legal Fees", "Expense", "Professional Fees", "Y", 48_000),
    ("530300", "Audit & Assurance Fees", "Expense", "Professional Fees", "N", 36_000),
    ("530400", "Outsourced Service Fees", "Expense", "Professional Fees", "Y", 105_000),
    ("540100", "Premises Rent", "Expense", "Premises", "N", 165_000),
    ("540200", "Utilities & Facilities", "Expense", "Premises", "Y", 38_000),
    ("540300", "Repairs & Maintenance", "Expense", "Premises", "Y", 22_000),
    ("550100", "Marketing & Advertising", "Expense", "Marketing", "Y", 120_000),
    ("550200", "Client Entertainment", "Expense", "Marketing", "Y", 18_000),
    ("550300", "Sponsorships", "Expense", "Marketing", "Y", 45_000),
    ("560100", "Travel - Air & Rail", "Expense", "Travel", "Y", 34_000),
    ("560200", "Accommodation & Subsistence", "Expense", "Travel", "Y", 19_000),
    ("570100", "Depreciation - Software", "Expense", "Depreciation", "N", 76_000),
    ("570200", "Depreciation - Property & Equipment", "Expense", "Depreciation", "N", 54_000),
    ("570300", "Amortisation - Intangibles", "Expense", "Depreciation", "N", 31_000),
    ("580100", "Card Scheme & Interchange Fees", "Expense", "Transaction Costs", "N", 240_000),
    ("580200", "Payment Processing Fees", "Expense", "Transaction Costs", "Y", 96_000),
    ("580300", "Bank Charges", "Expense", "Transaction Costs", "N", 14_000),
    ("590100", "Intercompany Service Recharge", "Expense", "Allocations", "N", 175_000),
    ("590200", "Corporate Allocation - Overhead", "Expense", "Allocations", "N", 145_000),
    ("610100", "Net Interest Income", "Revenue", "Revenue", "N", -2_400_000),
    ("610200", "Fee & Commission Income", "Revenue", "Revenue", "N", -1_350_000),
    ("610300", "Card Interchange Revenue", "Revenue", "Revenue", "N", -880_000),
    ("610400", "Trading & Other Income", "Revenue", "Revenue", "N", -420_000),
]

# which categories apply to which LOB (keeps the data plausible)
LOB_CATEGORY_WEIGHT = {
    "Technology": {"Technology": 1.6, "Personnel": 1.2, "Professional Fees": 1.1,
                   "Premises": 0.5, "Marketing": 0.05, "Travel": 0.5,
                   "Depreciation": 1.4, "Transaction Costs": 0.05, "Allocations": 0.8, "Revenue": 0.0},
    "Cards & Payments": {"Technology": 1.1, "Personnel": 1.0, "Professional Fees": 0.9,
                         "Premises": 0.5, "Marketing": 1.3, "Travel": 0.5,
                         "Depreciation": 0.8, "Transaction Costs": 1.8, "Allocations": 0.9, "Revenue": 1.0},
    "Retail Banking": {"Technology": 0.7, "Personnel": 1.4, "Professional Fees": 0.6,
                       "Premises": 1.6, "Marketing": 1.5, "Travel": 0.6,
                       "Depreciation": 0.7, "Transaction Costs": 0.4, "Allocations": 1.0, "Revenue": 1.0},
    "Wealth Management": {"Technology": 0.6, "Personnel": 1.3, "Professional Fees": 0.8,
                          "Premises": 0.9, "Marketing": 1.0, "Travel": 1.4,
                          "Depreciation": 0.4, "Transaction Costs": 0.3, "Allocations": 1.0, "Revenue": 1.0},
    "Corporate Banking": {"Technology": 0.6, "Personnel": 1.2, "Professional Fees": 0.9,
                          "Premises": 0.8, "Marketing": 0.6, "Travel": 1.3,
                          "Depreciation": 0.4, "Transaction Costs": 0.5, "Allocations": 1.0, "Revenue": 1.0},
    "Treasury": {"Technology": 0.7, "Personnel": 0.9, "Professional Fees": 0.6,
                 "Premises": 0.4, "Marketing": 0.1, "Travel": 0.5,
                 "Depreciation": 0.3, "Transaction Costs": 0.6, "Allocations": 0.8, "Revenue": 1.0},
    "Operations": {"Technology": 0.6, "Personnel": 1.5, "Professional Fees": 1.0,
                   "Premises": 0.9, "Marketing": 0.05, "Travel": 0.4,
                   "Depreciation": 0.3, "Transaction Costs": 0.3, "Allocations": 1.1, "Revenue": 0.0},
    "Risk & Compliance": {"Technology": 0.5, "Personnel": 1.3, "Professional Fees": 1.3,
                          "Premises": 0.5, "Marketing": 0.05, "Travel": 0.6,
                          "Depreciation": 0.2, "Transaction Costs": 0.1, "Allocations": 1.0, "Revenue": 0.0},
}

# per-cost-centre size multiplier so cost centres aren't clones
CC_SCALE = {cc["cost_center_code"]: round(random.uniform(0.45, 1.55), 3) for cc in COST_CENTERS}

# seasonality by month number (1..12): Q4 push, quiet August, bonus in March
SEASON = {1: 0.97, 2: 0.98, 3: 1.05, 4: 1.00, 5: 1.01, 6: 1.03,
          7: 0.99, 8: 0.93, 9: 1.02, 10: 1.04, 11: 1.06, 12: 1.10}

# ------------------------------------------------------------- planted stories
S1_CC = {  # Cards & Payments cloud-migration overrun, 2026-06 (USD, unfavourable)
    "Cards Platform Engineering": {"530100": 980_000, "520200": 610_000, "520100": 355_000},
    "Cards Issuing": {"530100": 240_000, "520100": 120_000},
    "Payments Operations": {"510400": 95_000},
}
# ramp so the overrun reads as a trend an analyst can spot building, not a one-off spike
S1_RAMP = {"2026-03": 0.06, "2026-04": 0.22, "2026-05": 0.55, "2026-06": 1.0}


def gl_pattern(cc, acct, period):
    """DETERMINISTIC expected run-rate for a cost-centre/account/period, expressed in
    USD-at-plan-rate. Both actual and budget are derived from this same shape (plus
    independent small noise), so background variance is small and random-signed and
    the planted stories dominate any aggregation. Returns None if not applicable."""
    code, name, atype, category, controllable, scale = acct
    w = LOB_CATEGORY_WEIGHT[cc["lob"]].get(category, 1.0)
    if w == 0.0:
        return None
    mth, yr = int(period[5:]), int(period[:4])
    growth = 1.0 + (0.028 if yr == 2026 else 0.0) + (PERIODS.index(period) * 0.0016)
    base = scale * w * CC_SCALE[cc["cost_center_code"]] * SEASON[mth] * growth
    if code == "510200":            # bonus lands in March
        base *= 2.6 if mth == 3 else 0.55
    if code == "530300":            # audit fees land in Q1
        base *= 2.2 if mth in (1, 2, 3) else 0.5
    if category == "Marketing":     # marketing lands in campaign months
        base *= 1.6 if mth in (3, 6, 9, 11) else 0.8
    return base


def plan_rate(currency: str, fiscal_year: int) -> float:
    """The FX rate the annual budget was locked at (January of the fiscal year)."""
    return fx_rate(currency, f"{fiscal_year}-01")


def write_csv(fname, rows, fieldnames):
    path = os.path.join(OUT, fname)
    with open(path, "w", newline="") as f:
        wtr = csv.DictWriter(f, fieldnames=fieldnames)
        wtr.writeheader()
        wtr.writerows(rows)
    print(f"{fname:38s} {len(rows):>7,} rows")
    return path


# ------------------------------------------------------------------- dim tables
ent_rows = [{"entity_code": e[0], "entity_name": e[1], "functional_currency": e[2],
             "region": e[3], "reporting_currency": "USD"} for e in ENTITIES]
write_csv("dim_entity.csv", ent_rows,
          ["entity_code", "entity_name", "functional_currency", "region", "reporting_currency"])

write_csv("dim_cost_center.csv", COST_CENTERS,
          ["cost_center_code", "cost_center_name", "lob", "entity_code", "region", "cc_owner"])

gl_rows = [{"gl_account": a[0], "gl_account_name": a[1], "account_type": a[2],
            "expense_category": a[3], "is_controllable": a[4]} for a in GL_ACCOUNTS]
write_csv("dim_gl_account.csv", gl_rows,
          ["gl_account", "gl_account_name", "account_type", "expense_category", "is_controllable"])

fx_rows = []
for p in PERIODS:
    for _, _, ccy, _ in ENTITIES:
        r = fx_rate(ccy, p)
        fx_rows.append({"period": p, "currency": ccy, "rate_type": "MONTHLY_AVERAGE",
                        "usd_per_unit": r})
        fx_rows.append({"period": p, "currency": ccy, "rate_type": "PERIOD_END",
                        "usd_per_unit": round(r * random.uniform(0.997, 1.003), 6) if ccy != "USD" else 1.0})
write_csv("dim_fx_rate.csv", fx_rows, ["period", "currency", "rate_type", "usd_per_unit"])

# --------------------------------------------------------- fact_gl_balance + budget
gl_facts, budget_facts = [], []
cc_local_ccy = {cc["cost_center_code"]: [e[2] for e in ENTITIES if e[0] == cc["entity_code"]][0]
                for cc in COST_CENTERS}

for cc in COST_CENTERS:
    ccy = cc_local_ccy[cc["cost_center_code"]]
    for acct in GL_ACCOUNTS:
        code, name, atype, category, controllable, _ = acct
        if LOB_CATEGORY_WEIGHT[cc["lob"]].get(category, 1.0) == 0.0:
            continue
        # revenue lines only on a subset of cost centres (the ones that own P&L)
        if atype == "Revenue" and cc["lob"] not in (
                "Retail Banking", "Cards & Payments", "Wealth Management",
                "Corporate Banking", "Treasury"):
            continue
        if gl_pattern(cc, acct, PERIODS[0]) is None:
            continue
        for p in PERIODS:
            yr, mth = int(p[:4]), int(p[5:])
            pattern = gl_pattern(cc, acct, p)          # USD-at-plan-rate run-rate
            sign = -1.0 if atype == "Revenue" else 1.0
            mag = abs(pattern)

            # ACTUAL is generated in LOCAL currency: the business spends locally.
            # Small, random-signed operational noise only (+/- ~4%).
            actual_local = (mag / plan_rate(ccy, yr)) * random.uniform(0.96, 1.04)

            # BUDGET is set in local currency from the same pattern (+/- ~2% planning
            # noise) and then translated to USD at the LOCKED PLAN RATE. This is what
            # makes an FX translation variance real rather than cosmetic.
            budget_local = (mag / plan_rate(ccy, yr)) * random.uniform(0.98, 1.02)
            if atype == "Expense":
                budget_local *= 0.995     # finance plans slightly tight on cost

            # ---- S1: Cards cloud-migration overrun. Unbudgeted, in local currency.
            overrun_local = 0.0
            planted = S1_CC.get(cc["cost_center_name"], {})
            if code in planted and p in S1_RAMP:
                overrun_local = (planted[code] * S1_RAMP[p]) / plan_rate(ccy, yr)
                actual_local += overrun_local

            rate = fx_rate(ccy, p)                     # live translation rate
            amount_local = sign * actual_local
            amount_usd = amount_local * rate
            budget_usd = sign * budget_local * plan_rate(ccy, yr)
            forecast_usd = budget_usd + (
                sign * overrun_local * rate * 0.55 if p in ("2026-05", "2026-06") else 0.0)

            gl_facts.append({
                "period": p,
                "fiscal_year": yr,
                "fiscal_quarter": f"{yr}-Q{(mth - 1) // 3 + 1}",
                "entity_code": cc["entity_code"],
                "cost_center_code": cc["cost_center_code"],
                "gl_account": code,
                "local_currency": ccy,
                "amount_local": round(amount_local, 2),
                "fx_rate_usd": rate,
                "amount_usd": round(round(amount_local, 2) * rate, 2),
                "posting_source": random.choices(
                    ["SAP_S4_GL", "SUBLEDGER_AP", "SUBLEDGER_PAYROLL", "MANUAL_JOURNAL", "ALLOCATION_ENGINE"],
                    weights=[0.42, 0.22, 0.14, 0.09, 0.13])[0],
                "is_planted_overrun": "Y" if overrun_local else "N",
            })
            budget_facts.append({
                "period": p,
                "fiscal_year": yr,
                "entity_code": cc["entity_code"],
                "cost_center_code": cc["cost_center_code"],
                "gl_account": code,
                "budget_usd": round(budget_usd, 2),
                "budget_local": round(sign * budget_local, 2),
                "plan_fx_rate_usd": plan_rate(ccy, yr),
                # forecast is a re-plan: it partially catches the overrun from 2026-05
                "forecast_usd": round(forecast_usd, 2),
                "budget_version": "AOP_2026_v3" if yr == 2026 else "AOP_2025_v2",
            })

write_csv("fact_gl_balance.csv", gl_facts,
          ["period", "fiscal_year", "fiscal_quarter", "entity_code", "cost_center_code",
           "gl_account", "local_currency", "amount_local", "fx_rate_usd", "amount_usd",
           "posting_source", "is_planted_overrun"])
write_csv("fact_budget.csv", budget_facts,
          ["period", "fiscal_year", "entity_code", "cost_center_code", "gl_account",
           "budget_usd", "budget_local", "plan_fx_rate_usd", "forecast_usd", "budget_version"])

# ------------------------------------------------------------------- headcount
hc_rows = []
for cc in COST_CENTERS:
    base_fte = round(random.uniform(18, 220) * CC_SCALE[cc["cost_center_code"]], 0)
    for p in PERIODS:
        i = PERIODS.index(p)
        fte = base_fte * (1 + 0.0035 * i) * random.uniform(0.99, 1.01)
        contractors = fte * random.uniform(0.04, 0.22)
        # S1 knock-on: contractor surge in Cards Platform Engineering for the migration
        if cc["cost_center_name"] == "Cards Platform Engineering" and p in S1_RAMP:
            contractors += 34 * S1_RAMP[p]
        hc_rows.append({
            "period": p, "cost_center_code": cc["cost_center_code"],
            "entity_code": cc["entity_code"],
            "fte_count": round(fte, 1), "contractor_count": round(contractors, 1),
            "open_positions": random.randint(0, 9),
            "attrition_leavers": random.randint(0, 5),
        })
write_csv("fact_headcount.csv", hc_rows,
          ["period", "cost_center_code", "entity_code", "fte_count", "contractor_count",
           "open_positions", "attrition_leavers"])

# ------------------------------------------------------------------- accruals
VENDORS = [
    ("V1001", "Helix Consulting Partners", "Professional Fees", "MB-US"),
    ("V1002", "Northwind Cloud Services", "Technology", "MB-US"),
    ("V1003", "Kestrel Software Ltd", "Technology", "MB-UK"),
    ("V1004", "Sable & Roan LLP", "Professional Fees", "MB-UK"),
    ("V1005", "Orion Facilities Group", "Premises", "MB-US"),
    ("V1006", "Lumen Media Agency", "Marketing", "MB-US"),
    ("V1007", "Trident Payment Networks", "Transaction Costs", "MB-US"),
    ("V1008", "Aster Staffing Solutions", "Personnel", "MB-IN"),
    ("V1009", "Cobalt Data Systems", "Technology", "MB-SG"),
    ("V1010", "Meridian Verify GmbH", "Professional Fees", "MB-DE"),
    ("V1011", "Pinewood Travel Management", "Travel", "MB-US"),
    ("V1012", "Quantum Assurance Advisors", "Professional Fees", "MB-US"),
    ("V1013", "Beacon Telecom Networks", "Technology", "MB-UK"),
    ("V1014", "Solstice Print & Fulfilment", "Marketing", "MB-IN"),
    ("V1015", "Vantage Legal Group", "Professional Fees", "MB-SG"),
]
CAT_ACCT = {}
for a in GL_ACCOUNTS:
    CAT_ACCT.setdefault(a[3], []).append(a[0])

CLOSE_DATE = date(2026, 6, 30)
accr_rows = []
_aid = 5000
# a normal population of accruals across the last 6 periods
for p in PERIODS[-6:]:
    for _ in range(random.randint(26, 34)):
        _aid += 1
        cc = random.choice(COST_CENTERS)
        v = random.choice(VENDORS)
        acct = random.choice(CAT_ACCT.get(v[2], ["530100"]))
        posted = date(int(p[:4]), int(p[5:]), random.randint(24, 28))
        amt = round(random.uniform(18_000, 620_000), 2)
        age = (CLOSE_DATE - posted).days
        # Anything older than 60 days is always reversed in the background population,
        # so the only >90-day OPEN accruals in the data are the planted policy breaches.
        reversed_flag = "Y" if age > 60 or (age > 35 and random.random() < 0.82) else "N"
        accr_rows.append({
            "accrual_id": f"ACR{_aid}",
            "period_posted": p,
            "entity_code": cc["entity_code"],
            "cost_center_code": cc["cost_center_code"],
            "gl_account": acct,
            "vendor_id": v[0],
            "vendor_name": v[1],
            "accrual_amount_usd": amt,
            "accrual_basis": random.choice(
                ["PO_RECEIPT_NOT_INVOICED", "SERVICE_DELIVERED_NOT_BILLED",
                 "ESTIMATE_FROM_CONTRACT", "RUN_RATE_ESTIMATE", "MANUAL_ESTIMATE"]),
            "posted_date": posted.isoformat(),
            "age_days": age,
            "is_reversed": reversed_flag,
            "reversal_period": p if reversed_flag == "Y" else "",
            "prepared_by": random.choice(OWNERS),
            "approved_by": random.choice(OWNERS),
            "status": "REVERSED" if reversed_flag == "Y" else "OPEN",
        })

# ---- S4: 6 aged accruals > 90 days still OPEN (policy breach), 4 in Cards & Payments
AGED = [
    ("Cards Platform Engineering", "530100", "V1001", 486_000, date(2026, 1, 28), "ESTIMATE_FROM_CONTRACT"),
    ("Cards Platform Engineering", "520200", "V1002", 312_500, date(2026, 2, 25), "RUN_RATE_ESTIMATE"),
    ("Cards Issuing", "530400", "V1007", 174_200, date(2026, 2, 26), "SERVICE_DELIVERED_NOT_BILLED"),
    ("Payments Operations", "510400", "V1008", 96_800, date(2026, 3, 27), "MANUAL_ESTIMATE"),
    ("Technology EMEA", "520100", "V1003", 208_400, date(2026, 1, 27), "ESTIMATE_FROM_CONTRACT"),
    ("Regulatory Reporting", "530200", "V1004", 61_900, date(2026, 3, 26), "MANUAL_ESTIMATE"),
]
for nm, acct, vid, amt, posted, basis in AGED:
    _aid += 1
    cc = cc_by_name(nm)
    v = [x for x in VENDORS if x[0] == vid][0]
    accr_rows.append({
        "accrual_id": f"ACR{_aid}",
        "period_posted": f"{posted.year}-{posted.month:02d}",
        "entity_code": cc["entity_code"],
        "cost_center_code": cc["cost_center_code"],
        "gl_account": acct,
        "vendor_id": vid,
        "vendor_name": v[1],
        "accrual_amount_usd": float(amt),
        "accrual_basis": basis,
        "posted_date": posted.isoformat(),
        "age_days": (CLOSE_DATE - posted).days,
        "is_reversed": "N",
        "reversal_period": "",
        "prepared_by": random.choice(OWNERS),
        "approved_by": random.choice(OWNERS),
        "status": "OPEN",
    })
write_csv("fact_accrual.csv", accr_rows,
          ["accrual_id", "period_posted", "entity_code", "cost_center_code", "gl_account",
           "vendor_id", "vendor_name", "accrual_amount_usd", "accrual_basis", "posted_date",
           "age_days", "is_reversed", "reversal_period", "prepared_by", "approved_by", "status"])

# ------------------------------------------------------------------- AP open items
ap_rows = []
_inv = 700000
for _ in range(560):
    _inv += 1
    v = random.choice(VENDORS)
    # keep Helix (V1001) out of the background 90+ population so the planted
    # disputed concentration is the only 90+ Helix exposure in the data
    while v[0] == "V1001":
        v = random.choice(VENDORS)
    cc = random.choice([c for c in COST_CENTERS if c["entity_code"] == v[3]] or COST_CENTERS)
    inv_date = CLOSE_DATE - timedelta(days=random.randint(1, 150))
    terms = random.choice([30, 30, 45, 60])
    due = inv_date + timedelta(days=terms)
    days_out = (CLOSE_DATE - due).days
    bucket = ("CURRENT" if days_out <= 0 else "1-30" if days_out <= 30
              else "31-60" if days_out <= 60 else "61-90" if days_out <= 90 else "90+")
    # keep background 90+ invoices small so the planted Helix dispute is the clear
    # top exposure rather than one of several similar-sized vendor balances
    amt = round(random.uniform(4_000, 90_000 if bucket == "90+" else 340_000), 2)
    ap_rows.append({
        "invoice_id": f"INV{_inv}",
        "vendor_id": v[0], "vendor_name": v[1],
        "entity_code": v[3], "cost_center_code": cc["cost_center_code"],
        "gl_account": random.choice(CAT_ACCT.get(v[2], ["530100"])),
        "invoice_date": inv_date.isoformat(), "due_date": due.isoformat(),
        "payment_terms_days": terms,
        "invoice_amount_usd": amt,
        "aging_bucket": bucket, "days_overdue": max(days_out, 0),
        "status": random.choices(["OPEN", "APPROVED_FOR_PAYMENT", "ON_HOLD", "DISPUTED"],
                                weights=[0.55, 0.28, 0.09, 0.08])[0],
        "match_status": random.choices(["THREE_WAY_MATCHED", "TWO_WAY_MATCHED", "PRICE_VARIANCE",
                                       "QTY_VARIANCE", "NO_PO"], weights=[0.6, 0.16, 0.1, 0.06, 0.08])[0],
    })
# ---- S6: Helix Consulting disputed 90+ concentration (1.31m)
for amt in (412_000.00, 355_500.00, 288_900.00, 254_100.00):
    _inv += 1
    inv_date = CLOSE_DATE - timedelta(days=random.randint(128, 158))
    due = inv_date + timedelta(days=30)
    ap_rows.append({
        "invoice_id": f"INV{_inv}", "vendor_id": "V1001",
        "vendor_name": "Helix Consulting Partners", "entity_code": "MB-US",
        "cost_center_code": cc_by_name("Cards Platform Engineering")["cost_center_code"],
        "gl_account": "530100", "invoice_date": inv_date.isoformat(),
        "due_date": due.isoformat(), "payment_terms_days": 30,
        "invoice_amount_usd": amt, "aging_bucket": "90+",
        "days_overdue": (CLOSE_DATE - due).days, "status": "DISPUTED",
        "match_status": "PRICE_VARIANCE",
    })
write_csv("fact_ap_open_item.csv", ap_rows,
          ["invoice_id", "vendor_id", "vendor_name", "entity_code", "cost_center_code",
           "gl_account", "invoice_date", "due_date", "payment_terms_days",
           "invoice_amount_usd", "aging_bucket", "days_overdue", "status", "match_status"])

# ------------------------------------------------------------------- intercompany
ic_rows = []
_ic = 300
IC_PAIRS = [("MB-UK", "MB-SG"), ("MB-US", "MB-IN"), ("MB-DE", "MB-UK"),
            ("MB-US", "MB-UK"), ("MB-SG", "MB-IN"), ("MB-US", "MB-DE")]
for p in PERIODS[-6:]:
    for a, b in IC_PAIRS:
        _ic += 1
        billed = round(random.uniform(400_000, 3_200_000), 2)
        diff = round(random.choice([0, 0, 0, random.uniform(-38_000, 42_000)]), 2)
        ic_rows.append({
            "ic_id": f"IC{_ic}", "period": p, "billing_entity": a, "receiving_entity": b,
            "service_type": random.choice(["IT Shared Services", "Finance Shared Services",
                                           "Treasury Funding", "Brand & Marketing Recharge",
                                           "Risk & Compliance Support"]),
            "billed_amount_usd": billed, "received_amount_usd": round(billed - diff, 2),
            "difference_usd": diff,
            "status": "MATCHED" if abs(diff) < 1_000 else "UNDER_INVESTIGATION",
            "settlement_due": (date(int(p[:4]), int(p[5:]), 28) + timedelta(days=45)).isoformat(),
        })
# ---- S3: the 482k unresolved break, present in two consecutive periods
for p, d in (("2026-05", 482_000.00), ("2026-06", 482_000.00)):
    _ic += 1
    ic_rows.append({
        "ic_id": f"IC{_ic}", "period": p, "billing_entity": "MB-UK", "receiving_entity": "MB-SG",
        "service_type": "Treasury Funding", "billed_amount_usd": 2_940_000.00,
        "received_amount_usd": 2_458_000.00, "difference_usd": d,
        "status": "UNRESOLVED_BREAK",
        "settlement_due": (date(int(p[:4]), int(p[5:]), 28) + timedelta(days=45)).isoformat(),
    })
write_csv("fact_intercompany.csv", ic_rows,
          ["ic_id", "period", "billing_entity", "receiving_entity", "service_type",
           "billed_amount_usd", "received_amount_usd", "difference_usd", "status", "settlement_due"])

# ------------------------------------------------------------------- close tasks
CLOSE_TASKS = [
    ("Sub-ledger cut-off - AP", "P2P", 1), ("Sub-ledger cut-off - AR", "O2C", 1),
    ("Payroll interface posting", "R2R", 1), ("Accrual calculation & upload", "R2R", 2),
    ("Prepaid amortisation run", "R2R", 2), ("Fixed asset depreciation run", "R2R", 2),
    ("FX revaluation run", "R2R", 3), ("Intercompany billing & matching", "R2R", 3),
    ("Bank reconciliation sign-off", "R2R", 3), ("Cost allocation cycle", "R2R", 4),
    ("Trial balance review - entity", "R2R", 4), ("Variance analysis & commentary", "R2R", 5),
    ("Balance sheet substantiation", "R2R", 5), ("Flux report to Group", "R2R", 6),
    ("Management pack preparation", "R2R", 6), ("Regulatory return feed", "R2R", 7),
    ("Statutory ledger close", "R2R", 7), ("Group consolidation submission", "R2R", 8),
]
ct_rows = []
_ct = 8000
for p in PERIODS[-4:]:
    for tname, proc, sla in CLOSE_TASKS:
        for ent in ("MB-US", "MB-UK", "MB-SG", "MB-DE", "MB-IN"):
            _ct += 1
            if p == "2026-06":
                # the current close is clean apart from the three planted breaches below,
                # so "which tasks missed SLA this month" has one unambiguous answer
                actual = sla - random.choice([0, 0, 1])
            else:
                actual = sla + random.choices([0, 0, 0, 1, -1, 2],
                                              weights=[.5, .17, .13, .12, .05, .03])[0]
            ct_rows.append({
                "task_id": f"CT{_ct}", "period": p, "entity_code": ent,
                "task_name": tname, "fna_process": proc,
                "sla_business_day": sla, "actual_business_day": max(actual, 1),
                "owner_team": {"R2R": "Record to Report", "P2P": "Procure to Pay",
                               "O2C": "Order to Cash"}[proc],
                "owner": random.choice(OWNERS),
                "status": "COMPLETE",
                "is_sla_breach": "Y" if actual > sla else "N",
                "days_late": max(actual - sla, 0),
            })
# ---- S5: three explicit SLA breaches in 2026-06 across two teams
BREACHES = [
    ("2026-06", "MB-US", "Accrual calculation & upload", "R2R", 2, 5, "Record to Report", 3),
    ("2026-06", "MB-UK", "Intercompany billing & matching", "R2R", 3, 6, "Record to Report", 3),
    ("2026-06", "MB-SG", "Sub-ledger cut-off - AP", "P2P", 1, 3, "Procure to Pay", 2),
]
for p, ent, tname, proc, sla, act, team, late in BREACHES:
    ct_rows = [r for r in ct_rows
               if not (r["period"] == p and r["entity_code"] == ent and r["task_name"] == tname)]
    _ct += 1
    ct_rows.append({
        "task_id": f"CT{_ct}", "period": p, "entity_code": ent, "task_name": tname,
        "fna_process": proc, "sla_business_day": sla, "actual_business_day": act,
        "owner_team": team, "owner": random.choice(OWNERS), "status": "COMPLETE_LATE",
        "is_sla_breach": "Y", "days_late": late,
    })
write_csv("fact_close_task.csv", ct_rows,
          ["task_id", "period", "entity_code", "task_name", "fna_process", "sla_business_day",
           "actual_business_day", "owner_team", "owner", "status", "is_sla_breach", "days_late"])

# --------------------------------------------------------------------- summary
tot = {}
for r in gl_facts:
    if r["period"] == "2026-06":
        tot[r["gl_account"]] = tot.get(r["gl_account"], 0) + r["amount_usd"]
print("\n--- sanity: planted S1 total overrun (2026-06, USD) ---")
s1 = sum(v * S1_RAMP["2026-06"] for d in S1_CC.values() for v in d.values())
print(f"  {s1:,.0f}")
print(f"--- aged accruals >90d still OPEN: "
      f"{sum(1 for r in accr_rows if r['status'] == 'OPEN' and r['age_days'] > 90)}")
print(f"--- Helix 90+ disputed USD: "
      f"{sum(r['invoice_amount_usd'] for r in ap_rows if r['vendor_id'] == 'V1001' and r['aging_bucket'] == '90+'):,.0f}")
print(f"--- 2026-06 SLA breaches: "
      f"{sum(1 for r in ct_rows if r['period'] == '2026-06' and r['is_sla_breach'] == 'Y')}")
