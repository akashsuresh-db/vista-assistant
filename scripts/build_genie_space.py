#!/usr/bin/env python3
"""Create (or update) the Vista Assistant Genie space via the Genie spaces REST API.

The space is defined by a `serialized_space` JSON blob (version 2). The instruction
text is the highest-leverage part: text-to-SQL on finance data goes wrong in a few
very predictable ways, so each rule below exists to prevent a specific wrong answer.

Usage: python build_genie_space.py [--update <space_id>]
"""
import json
import subprocess
import sys
import uuid

from scripts.config import CFG, set_value

CAT = CFG.fq_schema

TABLES = [
    f"{CAT}.v_opex_variance",
    f"{CAT}.v_aged_accrual",
    f"{CAT}.v_ap_aging",
    f"{CAT}.v_close_performance",
    f"{CAT}.v_headcount_cost",
    f"{CAT}.fact_intercompany",
    f"{CAT}.dim_entity",
    f"{CAT}.dim_cost_center",
    f"{CAT}.dim_gl_account",
    f"{CAT}.dim_fx_rate",
]

INSTRUCTIONS = f"""
This space answers Finance & Accounting (FnA) questions for Meridian Bank, a
multi-entity bank. Group reports in USD. The latest closed accounting period is
2026-06. `period` is TEXT in 'YYYY-MM' form (e.g. '2026-06') in every table - never
cast it to a date and never use date functions on it. For "latest month", "this
month", "current period" or "June" use period = '2026-06'.

### Which table to use
- ANY question about budget, variance, overspend, overrun, underspend, actual vs
  budget, flux, or cost by division/LOB/entity/account -> `v_opex_variance`.
  This view already joins actuals to budget and to all dimensions. Do NOT join
  fact_gl_balance to fact_budget yourself.
- Aged/unreversed accruals, accrual policy breaches -> `v_aged_accrual`.
- Payables aging, overdue invoices, disputed invoices, vendor exposure -> `v_ap_aging`.
- Month-end close, SLA, late tasks, close performance -> `v_close_performance`.
- Headcount, FTE, contractors, cost per FTE -> `v_headcount_cost`.
- Intercompany billing, matching, breaks -> `fact_intercompany`.

### THE VARIANCE SIGN CONVENTION - this is the most important rule
In `v_opex_variance`: variance_usd = actual_usd - budget_usd.
For EXPENSES a POSITIVE variance means the business SPENT MORE THAN BUDGET, i.e. an
OVERSPEND / OVERRUN / UNFAVOURABLE variance. A NEGATIVE variance is an UNDERSPEND /
FAVOURABLE variance. So:
- "who overspent", "biggest overrun", "worst variance", "over budget" -> ORDER BY
  sum(variance_usd) DESC and/or filter variance_usd > 0.
- "underspent", "savings", "favourable" -> variance_usd < 0.
The column `variance_direction` already holds 'UNFAVOURABLE' / 'FAVOURABLE' /
'ON_BUDGET' if you prefer to filter on it.
ALWAYS filter account_type = 'Expense' for opex / cost / spend questions, otherwise
revenue rows (which are stored as negative numbers) will distort the totals.

### FX: constant currency vs reported USD
A USD variance can be caused purely by currency movement, because budget_usd is
translated at the FX rate locked when the plan was approved (plan_fx_rate) while
actual_usd is translated at the actual monthly rate (actual_fx_rate).
- variance_usd                = total reported USD variance
- variance_usd_constant_ccy   = the variance excluding FX (the LOCAL overspend)
- fx_translation_impact_usd   = the part of the USD variance caused only by FX
- variance_local_ccy          = actual minus budget in the entity's own currency
If the user asks "is this real overspend or just FX", "constant currency",
"FX-neutral", "local currency" or "why is EMEA unfavourable", return
variance_usd, variance_usd_constant_ccy AND fx_translation_impact_usd side by side
so the split is visible. Cost centre owners are accountable for the
constant-currency variance; FX translation is owned by Group Treasury.

### Business vocabulary
- "LOB", "division", "business", "business line" -> the `lob` column
  (values: Retail Banking, Cards & Payments, Wealth Management, Corporate Banking,
  Treasury, Technology, Operations, Risk & Compliance).
- "entity", "legal entity", "country book" -> entity_code / entity_name
  (MB-US, MB-UK, MB-DE, MB-SG, MB-IN).
- "cost centre"/"cost center"/"team" -> cost_center_name.
- "opex", "cost", "spend", "expense" -> account_type = 'Expense'.
- "controllable" cost -> is_controllable = 'Y'.
- "driver" of a variance -> group by gl_account_name (and cost_center_name).
- "category" -> expense_category.
- Aged accrual / policy breach -> v_aged_accrual policy_status = 'BREACH_OVER_90_DAYS'
  (accounting policy FIN-ACC-014 requires reversal or re-substantiation within 90 days).
- Close SLA breach -> v_close_performance is_sla_breach = 'Y' (days_late > 0).
- Intercompany break -> fact_intercompany status = 'UNRESOLVED_BREAK' is the most
  severe; 'UNDER_INVESTIGATION' is in progress; difference_usd is the break amount.
- AP high risk -> v_ap_aging aging_bucket = '90+' combined with status = 'DISPUTED'.

### Output conventions
- Amounts are USD unless the user explicitly asks for local currency.
- Round money to whole dollars, or present in millions when the number is large -
  and label the unit in the column alias (e.g. variance_usd_m).
- Round percentages with ROUND(x, 2) and label them _pct.
- When the user asks "why" or "what drove", return the top contributing rows
  (by gl_account_name and cost_center_name) ordered by variance_usd DESC, not just
  a single total - the breakdown IS the answer.
- Do NOT add `WHERE col IS NOT NULL` filters on grouping columns unless asked.
- Never filter or expose the column `is_planted_overrun`; it is an internal flag.

### NEVER return a bare total - always show where it comes from
A single aggregate number is not a useful answer to a finance analyst; the follow-up
question is always "where?". So whenever a question would collapse to ONE row -
"what is our full-year forecast versus plan", "how much are we over budget", "what is
total opex", "what is the variance" - ALSO break the result down by `lob` (and by
cost_center_name if the user named an LOB or entity), ordered by variance_usd DESC.
Include a total row or state the total in the summary, but the per-LOB rows must be
there. The same applies to counts: if you report "6 accruals breach the policy", list
them. Concentration is usually the real finding - for example a group-level overspend
that turns out to sit almost entirely in one line of business.

### Always state the scope you used
Say which period (or period range), which entity or LOB filter, and whether figures are
USD or local currency, so the analyst can reproduce or challenge the number. If the
question did not specify a period, use 2026-06 (the latest closed period) and SAY SO.

### Ranking "best" and "worst" cost performance
Because a positive variance is an overspend, "best cost performance", "most favourable",
"biggest saving" or "who came in under budget" means ORDER BY sum(variance_usd) ASC
(most negative first), while "worst", "biggest overrun" or "over budget" means
ORDER BY sum(variance_usd) DESC. If every group is over budget, say so rather than
implying the top of the list performed well.

### When the data cannot answer the question
The ledger only covers 2025-01 to 2026-06. If asked about a future period (a forecast
for a month after 2026-06) or a metric that does not exist in these tables (EBITDA,
headcount attrition rate, revenue per customer, share price), say plainly that it is not
available, then offer the closest thing that IS available - for example the latest
`forecast_usd` in fact_budget, or the year-to-date run rate - rather than stopping at
"no data".
""".strip()


def _id():
    return uuid.uuid4().hex


EXAMPLE_SQLS = [
    ("Which line of business overspent the most in June 2026?",
     f"""SELECT lob,
       ROUND(SUM(actual_usd)/1e6, 2)   AS actual_usd_m,
       ROUND(SUM(budget_usd)/1e6, 2)   AS budget_usd_m,
       ROUND(SUM(variance_usd)/1e6, 2) AS variance_usd_m
FROM {CAT}.v_opex_variance
WHERE period = '2026-06' AND account_type = 'Expense'
GROUP BY lob
ORDER BY variance_usd_m DESC"""),

    ("What drove the Cards & Payments overspend in June 2026?",
     f"""SELECT gl_account_name, cost_center_name,
       ROUND(SUM(variance_usd), 0) AS variance_usd
FROM {CAT}.v_opex_variance
WHERE period = '2026-06' AND account_type = 'Expense'
  AND lob = 'Cards & Payments'
GROUP BY gl_account_name, cost_center_name
HAVING SUM(variance_usd) > 0
ORDER BY variance_usd DESC
LIMIT 10"""),

    ("Is the MB-UK variance real overspend or just FX translation?",
     f"""SELECT entity_code, functional_currency,
       ROUND(SUM(variance_usd), 0)               AS variance_usd,
       ROUND(SUM(variance_usd_constant_ccy), 0)  AS variance_constant_ccy_usd,
       ROUND(SUM(fx_translation_impact_usd), 0)  AS fx_translation_usd
FROM {CAT}.v_opex_variance
WHERE period = '2026-06' AND account_type = 'Expense'
GROUP BY entity_code, functional_currency
ORDER BY fx_translation_usd DESC"""),

    ("Show the Cards & Payments variance trend this year",
     f"""SELECT period,
       ROUND(SUM(variance_usd)/1e6, 2) AS variance_usd_m
FROM {CAT}.v_opex_variance
WHERE lob = 'Cards & Payments' AND account_type = 'Expense'
  AND period >= '2026-01'
GROUP BY period
ORDER BY period"""),

    ("Which accruals breach the 90-day policy?",
     f"""SELECT accrual_id, cost_center_name, lob, vendor_name,
       accrual_amount_usd, age_days, accrual_basis
FROM {CAT}.v_aged_accrual
WHERE policy_status = 'BREACH_OVER_90_DAYS'
ORDER BY accrual_amount_usd DESC"""),

    ("Which close tasks missed their SLA in June 2026?",
     f"""SELECT entity_code, task_name, owner_team,
       sla_business_day, actual_business_day, days_late
FROM {CAT}.v_close_performance
WHERE period = '2026-06' AND is_sla_breach = 'Y'
ORDER BY days_late DESC"""),

    ("Which vendor has the largest 90+ day payables exposure?",
     f"""SELECT vendor_name,
       COUNT(*)                            AS invoice_count,
       ROUND(SUM(invoice_amount_usd), 0)   AS exposure_usd,
       COLLECT_SET(status)                 AS statuses,
       COLLECT_SET(match_status)           AS match_statuses
FROM {CAT}.v_ap_aging
WHERE aging_bucket = '90+'
GROUP BY vendor_name
ORDER BY exposure_usd DESC
LIMIT 10"""),

    ("Are there any unresolved intercompany breaks?",
     f"""SELECT period, billing_entity, receiving_entity, service_type,
       billed_amount_usd, received_amount_usd, difference_usd, status
FROM {CAT}.fact_intercompany
WHERE status IN ('UNRESOLVED_BREAK', 'UNDER_INVESTIGATION')
ORDER BY ABS(difference_usd) DESC"""),

    ("Did contractor headcount rise in Cards Platform Engineering?",
     f"""SELECT period, cost_center_name, fte_count, contractor_count,
       ROUND(personnel_cost_usd, 0) AS personnel_cost_usd
FROM {CAT}.v_headcount_cost
WHERE cost_center_name = 'Cards Platform Engineering'
  AND period >= '2026-01'
ORDER BY period"""),

    ("Show the top 10 cost centres over budget in June 2026",
     f"""SELECT cost_center_name, lob, entity_code, cc_owner,
       ROUND(SUM(actual_usd), 0)   AS actual_usd,
       ROUND(SUM(budget_usd), 0)   AS budget_usd,
       ROUND(SUM(variance_usd), 0) AS variance_usd
FROM {CAT}.v_opex_variance
WHERE period = '2026-06' AND account_type = 'Expense'
GROUP BY cost_center_name, lob, entity_code, cc_owner
HAVING SUM(variance_usd) > 0
ORDER BY variance_usd DESC
LIMIT 10"""),

    # Teaches the "never return a bare total" rule: the question sounds like one number,
    # but the useful answer shows the concentration by line of business.
    ("What is our full-year 2026 forecast versus plan?",
     f"""SELECT lob,
       ROUND(SUM(budget_usd)/1e6, 2)                        AS budget_usd_m,
       ROUND(SUM(forecast_usd)/1e6, 2)                      AS forecast_usd_m,
       ROUND((SUM(forecast_usd) - SUM(budget_usd))/1e6, 2)  AS variance_usd_m
FROM {CAT}.v_opex_variance
WHERE fiscal_year = 2026 AND account_type = 'Expense'
GROUP BY lob
ORDER BY variance_usd_m DESC"""),

    # Teaches the ASC ordering for "best" / favourable performance.
    ("Which line of business had the best cost performance in June 2026?",
     f"""SELECT lob,
       ROUND(SUM(actual_usd)/1e6, 2)   AS actual_usd_m,
       ROUND(SUM(budget_usd)/1e6, 2)   AS budget_usd_m,
       ROUND(SUM(variance_usd)/1e6, 2) AS variance_usd_m,
       CASE WHEN SUM(variance_usd) < 0 THEN 'FAVOURABLE'
            ELSE 'UNFAVOURABLE' END    AS direction
FROM {CAT}.v_opex_variance
WHERE period = '2026-06' AND account_type = 'Expense'
GROUP BY lob
ORDER BY variance_usd_m ASC"""),

    # Teaches breaking a group-level number down to where it actually sits.
    ("How much are we over budget in total, and where does it sit?",
     f"""SELECT lob, entity_code,
       ROUND(SUM(variance_usd), 0)                  AS variance_usd,
       ROUND(SUM(variance_usd_constant_ccy), 0)     AS constant_ccy_usd,
       ROUND(SUM(fx_translation_impact_usd), 0)     AS fx_usd
FROM {CAT}.v_opex_variance
WHERE period = '2026-06' AND account_type = 'Expense'
GROUP BY lob, entity_code
HAVING SUM(variance_usd) <> 0
ORDER BY variance_usd DESC"""),
]

BENCHMARKS = [
    ("Which line of business had the largest unfavourable opex variance in June 2026?",
     f"SELECT lob, ROUND(SUM(variance_usd), 0) AS variance_usd FROM {CAT}.v_opex_variance "
     f"WHERE period = '2026-06' AND account_type = 'Expense' GROUP BY lob "
     f"ORDER BY variance_usd DESC LIMIT 1"),
    ("How many accruals breach the 90-day policy and what is their total value?",
     f"SELECT COUNT(*) AS breach_count, ROUND(SUM(accrual_amount_usd), 0) AS total_usd "
     f"FROM {CAT}.v_aged_accrual WHERE policy_status = 'BREACH_OVER_90_DAYS'"),
    ("How much of the MB-UK June 2026 expense variance is FX translation?",
     f"SELECT ROUND(SUM(variance_usd), 0) AS variance_usd, "
     f"ROUND(SUM(variance_usd_constant_ccy), 0) AS constant_ccy_usd, "
     f"ROUND(SUM(fx_translation_impact_usd), 0) AS fx_usd FROM {CAT}.v_opex_variance "
     f"WHERE period = '2026-06' AND account_type = 'Expense' AND entity_code = 'MB-UK'"),
    ("What is the total unresolved intercompany break value?",
     f"SELECT ROUND(SUM(difference_usd), 0) AS break_usd FROM {CAT}.fact_intercompany "
     f"WHERE status = 'UNRESOLVED_BREAK'"),
    ("How many close tasks missed SLA in June 2026?",
     f"SELECT COUNT(*) AS breach_count FROM {CAT}.v_close_performance "
     f"WHERE period = '2026-06' AND is_sla_breach = 'Y'"),
    ("What are the top three expense accounts driving the Cards & Payments June 2026 overspend?",
     f"SELECT gl_account_name, ROUND(SUM(variance_usd), 0) AS variance_usd "
     f"FROM {CAT}.v_opex_variance WHERE period = '2026-06' AND account_type = 'Expense' "
     f"AND lob = 'Cards & Payments' GROUP BY gl_account_name ORDER BY variance_usd DESC LIMIT 3"),
    ("Which vendor has the largest disputed 90+ day payables balance?",
     f"SELECT vendor_name, ROUND(SUM(invoice_amount_usd), 0) AS exposure_usd "
     f"FROM {CAT}.v_ap_aging WHERE aging_bucket = '90+' AND status = 'DISPUTED' "
     f"GROUP BY vendor_name ORDER BY exposure_usd DESC LIMIT 1"),
    ("Show the monthly trend of Cards & Payments expense variance in 2026",
     f"SELECT period, ROUND(SUM(variance_usd), 0) AS variance_usd FROM {CAT}.v_opex_variance "
     f"WHERE lob = 'Cards & Payments' AND account_type = 'Expense' AND period >= '2026-01' "
     f"GROUP BY period ORDER BY period"),
    ("What is the 2026 forecast versus plan by line of business?",
     f"SELECT lob, ROUND(SUM(budget_usd), 0) AS budget_usd, "
     f"ROUND(SUM(forecast_usd), 0) AS forecast_usd, "
     f"ROUND(SUM(forecast_usd) - SUM(budget_usd), 0) AS variance_usd "
     f"FROM {CAT}.v_opex_variance WHERE fiscal_year = 2026 AND account_type = 'Expense' "
     f"GROUP BY lob ORDER BY variance_usd DESC"),
    ("Which line of business had the most favourable cost variance in June 2026?",
     f"SELECT lob, ROUND(SUM(variance_usd), 0) AS variance_usd FROM {CAT}.v_opex_variance "
     f"WHERE period = '2026-06' AND account_type = 'Expense' GROUP BY lob "
     f"ORDER BY variance_usd ASC LIMIT 1"),
]

SAMPLE_QUESTIONS = [
    "Which line of business overspent the most in June 2026, and what drove it?",
    "Is the MB-UK cost variance real overspend or just FX translation?",
    "Which accruals breach the 90-day policy and who owns them?",
    "Which close tasks missed their SLA in June 2026?",
    "Which vendor has the largest 90+ day payables exposure?",
    "Show the Cards & Payments variance trend across 2026",
]

MEASURES = [
    ("Actual expense (USD)", "SUM(v_opex_variance.actual_usd)"),
    ("Budget (USD)", "SUM(v_opex_variance.budget_usd)"),
    ("Variance (USD, positive = overspend)", "SUM(v_opex_variance.variance_usd)"),
    ("Constant-currency variance (USD)", "SUM(v_opex_variance.variance_usd_constant_ccy)"),
    ("FX translation impact (USD)", "SUM(v_opex_variance.fx_translation_impact_usd)"),
    ("Aged accrual exposure (USD)", "SUM(v_aged_accrual.accrual_amount_usd)"),
    ("Payables exposure (USD)", "SUM(v_ap_aging.invoice_amount_usd)"),
    ("SLA breach count", "COUNT(CASE WHEN v_close_performance.is_sla_breach = 'Y' THEN 1 END)"),
]

FILTERS = [
    ("Latest closed period (2026-06)", "v_opex_variance.period = '2026-06'"),
    ("Expenses only", "v_opex_variance.account_type = 'Expense'"),
    ("Unfavourable variances (overspend)", "v_opex_variance.variance_usd > 0"),
    ("Controllable cost only", "v_opex_variance.is_controllable = 'Y'"),
    ("Accruals breaching 90-day policy", "v_aged_accrual.policy_status = 'BREACH_OVER_90_DAYS'"),
    ("Close SLA breaches", "v_close_performance.is_sla_breach = 'Y'"),
    ("Payables 90+ days overdue", "v_ap_aging.aging_bucket = '90+'"),
    ("Unresolved intercompany breaks", "fact_intercompany.status = 'UNRESOLVED_BREAK'"),
]


def _ids(n):
    """n unique ids in ascending order.

    The export-proto validator requires every collection to be sorted by id, so we
    hand out pre-sorted ids rather than sorting the objects afterwards (which would
    scramble the intended display order of questions and snippets)."""
    return sorted(uuid.uuid4().hex for _ in range(n))


def build_serialized_space():
    sq = _ids(len(SAMPLE_QUESTIONS))
    ex = _ids(len(EXAMPLE_SQLS))
    fl = _ids(len(FILTERS))
    ms = _ids(len(MEASURES))
    bm = _ids(len(BENCHMARKS))
    return {
        "version": 2,
        "config": {
            "sample_questions": [{"id": sq[i], "question": [q]}
                                 for i, q in enumerate(SAMPLE_QUESTIONS)]
        },
        # the API rejects the payload unless tables are sorted by identifier
        "data_sources": {"tables": [{"identifier": t} for t in sorted(TABLES)]},
        "instructions": {
            "text_instructions": [{"id": _id(), "content": [INSTRUCTIONS]}],
            "example_question_sqls": [
                {"id": ex[i], "question": [q], "sql": [s]}
                for i, (q, s) in enumerate(EXAMPLE_SQLS)
            ],
            "sql_snippets": {
                "filters": [{"id": fl[i], "sql": [s], "display_name": n}
                            for i, (n, s) in enumerate(FILTERS)],
                "measures": [{"id": ms[i], "sql": [s], "display_name": n}
                             for i, (n, s) in enumerate(MEASURES)],
                "expressions": [],
            },
        },
        "benchmarks": {
            "questions": [
                {"id": bm[i], "question": [q],
                 "answer": [{"format": "SQL", "content": [s]}]}
                for i, (q, s) in enumerate(BENCHMARKS)
            ]
        },
    }


def main():
    payload = {
        "title": "FnA Analytics - Meridian Bank",
        "description": (
            "Finance & Accounting structured analytics for Meridian Bank: GL actuals vs "
            "budget with FX decomposition, opex variance by LOB/entity/cost centre, aged "
            "accruals, payables aging, intercompany reconciliation, month-end close SLA "
            "performance and headcount."
        ),
        "warehouse_id": CFG.warehouse_id,
        "serialized_space": json.dumps(build_serialized_space(), indent=2),
    }

    update_id = None
    if len(sys.argv) > 2 and sys.argv[1] == "--update":
        update_id = sys.argv[2]

    path = f"/api/2.0/genie/spaces/{update_id}" if update_id else "/api/2.0/genie/spaces"
    verb = "patch" if update_id else "post"
    if update_id:
        # PATCH requires the current etag to avoid clobbering concurrent edits
        cur = json.loads(subprocess.run(
            ["databricks", "api", "get",
             f"/api/2.0/genie/spaces/{update_id}?include_serialized_space=true",
             "-p", CFG.profile], capture_output=True, text=True, check=True).stdout)
        payload["etag"] = cur["etag"]

    with open("/tmp/genie_payload.json", "w") as f:
        json.dump(payload, f)

    r = subprocess.run(
        ["databricks", "api", verb, path, "--json", "@/tmp/genie_payload.json", "-p", CFG.profile],
        capture_output=True, text=True)
    print(r.stdout[:1500] or r.stderr[:1500])
    if r.returncode != 0:
        sys.exit(1)
    try:
        out = json.loads(r.stdout)
        space_id = out.get("space_id")
        print("\nSPACE_ID =", space_id)
        # Record the space_id in config.yaml so other scripts can find it
        if space_id:
            set_value("genie_space_id", space_id)
    except Exception:
        pass


if __name__ == "__main__":
    main()
