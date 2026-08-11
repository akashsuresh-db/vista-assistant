-- This file uses {catalog} and {schema} placeholders.
-- run_sql.py substitutes from CFG before executing.

-- Phase 2b: analyst-facing views.
-- Rationale: the actual-vs-budget join plus the sign convention for "favourable" is the
-- single thing a text-to-SQL agent is most likely to get wrong. Encoding it once in a
-- view makes Genie's job description-lookup rather than derivation.

CREATE OR REPLACE VIEW v_opex_variance
COMMENT 'Month-by-month opex actual vs budget vs forecast, fully enriched with entity, cost centre, LOB and account attributes. Variance convention: variance_usd = actual - budget, so a POSITIVE variance is an OVERSPEND (unfavourable) and a NEGATIVE variance is an UNDERSPEND (favourable). variance_local_ccy compares in local currency and therefore excludes FX; fx_translation_impact_usd isolates the portion of the USD variance caused purely by currency movement. This is the primary view for any budget-variance, overspend, overrun or flux question.'
AS
SELECT
  a.period,
  a.fiscal_year,
  a.fiscal_quarter,
  a.entity_code,
  e.entity_name,
  e.region,
  e.functional_currency,
  a.cost_center_code,
  c.cost_center_name,
  c.lob,
  c.cc_owner,
  a.gl_account,
  g.gl_account_name,
  g.account_type,
  g.expense_category,
  g.is_controllable,
  a.amount_usd                                          AS actual_usd,
  b.budget_usd,
  b.forecast_usd,
  a.amount_usd - b.budget_usd                           AS variance_usd,
  CASE WHEN b.budget_usd <> 0
       THEN (a.amount_usd - b.budget_usd) / abs(b.budget_usd) END AS variance_pct,
  CASE WHEN a.amount_usd - b.budget_usd > 0 THEN 'UNFAVOURABLE'
       WHEN a.amount_usd - b.budget_usd < 0 THEN 'FAVOURABLE'
       ELSE 'ON_BUDGET' END                             AS variance_direction,
  a.local_currency,
  a.amount_local                                        AS actual_local_ccy,
  b.budget_local                                        AS budget_local_ccy,
  a.amount_local - b.budget_local                       AS variance_local_ccy,
  a.fx_rate_usd                                         AS actual_fx_rate,
  b.plan_fx_rate_usd                                    AS plan_fx_rate,
  a.amount_local * (a.fx_rate_usd - b.plan_fx_rate_usd) AS fx_translation_impact_usd,
  (a.amount_local - b.budget_local) * b.plan_fx_rate_usd AS variance_usd_constant_ccy,
  a.posting_source
FROM fact_gl_balance a
JOIN fact_budget b
  ON  a.period           = b.period
  AND a.cost_center_code = b.cost_center_code
  AND a.gl_account       = b.gl_account
JOIN dim_entity      e ON e.entity_code      = a.entity_code
JOIN dim_cost_center c ON c.cost_center_code = a.cost_center_code
JOIN dim_gl_account  g ON g.gl_account       = a.gl_account;

CREATE OR REPLACE VIEW v_aged_accrual
COMMENT 'Open accruals enriched with cost centre, LOB and owner, plus a policy_status flag. Accounting policy FIN-ACC-014 requires an accrual to be substantiated or reversed within 90 days, so policy_status = BREACH_OVER_90_DAYS rows are the exceptions an analyst must action. Use for aged-accrual, unreversed-accrual and accrual-policy questions.'
AS
SELECT
  ac.accrual_id,
  ac.period_posted,
  ac.entity_code,
  e.entity_name,
  ac.cost_center_code,
  c.cost_center_name,
  c.lob,
  c.cc_owner,
  ac.gl_account,
  g.gl_account_name,
  g.expense_category,
  ac.vendor_id,
  ac.vendor_name,
  ac.accrual_amount_usd,
  ac.accrual_basis,
  ac.posted_date,
  ac.age_days,
  ac.status,
  ac.is_reversed,
  ac.prepared_by,
  ac.approved_by,
  CASE WHEN ac.status = 'OPEN' AND ac.age_days > 90  THEN 'BREACH_OVER_90_DAYS'
       WHEN ac.status = 'OPEN' AND ac.age_days > 60  THEN 'WATCH_60_TO_90_DAYS'
       WHEN ac.status = 'OPEN'                       THEN 'WITHIN_POLICY'
       ELSE 'REVERSED' END AS policy_status
FROM fact_accrual ac
JOIN dim_entity      e ON e.entity_code      = ac.entity_code
JOIN dim_cost_center c ON c.cost_center_code = ac.cost_center_code
JOIN dim_gl_account  g ON g.gl_account       = ac.gl_account;

CREATE OR REPLACE VIEW v_close_performance
COMMENT 'Month-end close task performance with SLA breach detail by period, entity, team and process. Use for close-cycle, SLA, late-task and close-health questions.'
AS
SELECT
  t.task_id,
  t.period,
  t.entity_code,
  e.entity_name,
  e.region,
  t.task_name,
  t.fna_process,
  t.owner_team,
  t.owner,
  t.sla_business_day,
  t.actual_business_day,
  t.days_late,
  t.is_sla_breach,
  t.status
FROM fact_close_task t
JOIN dim_entity e ON e.entity_code = t.entity_code;

CREATE OR REPLACE VIEW v_ap_aging
COMMENT 'Open payables enriched with cost centre and LOB, for aging, overdue, disputed-invoice and vendor-exposure questions. aging_bucket 90+ combined with status DISPUTED is the highest-risk population.'
AS
SELECT
  ap.invoice_id,
  ap.vendor_id,
  ap.vendor_name,
  ap.entity_code,
  e.entity_name,
  ap.cost_center_code,
  c.cost_center_name,
  c.lob,
  ap.gl_account,
  g.gl_account_name,
  g.expense_category,
  ap.invoice_date,
  ap.due_date,
  ap.payment_terms_days,
  ap.invoice_amount_usd,
  ap.aging_bucket,
  ap.days_overdue,
  ap.status,
  ap.match_status
FROM fact_ap_open_item ap
JOIN dim_entity      e ON e.entity_code      = ap.entity_code
JOIN dim_cost_center c ON c.cost_center_code = ap.cost_center_code
JOIN dim_gl_account  g ON g.gl_account       = ap.gl_account;

CREATE OR REPLACE VIEW v_headcount_cost
COMMENT 'Personnel cost per period and cost centre alongside FTE and contractor counts, with cost per FTE. Use to explain whether a personnel variance came from volume (more people) or rate (more expensive people).'
AS
SELECT
  h.period,
  h.cost_center_code,
  c.cost_center_name,
  c.lob,
  h.entity_code,
  h.fte_count,
  h.contractor_count,
  h.open_positions,
  h.attrition_leavers,
  p.personnel_cost_usd,
  CASE WHEN h.fte_count > 0 THEN p.personnel_cost_usd / h.fte_count END AS cost_per_fte_usd
FROM fact_headcount h
JOIN dim_cost_center c ON c.cost_center_code = h.cost_center_code
LEFT JOIN (
  SELECT b.period, b.cost_center_code, sum(b.amount_usd) AS personnel_cost_usd
  FROM fact_gl_balance b
  JOIN dim_gl_account g ON g.gl_account = b.gl_account
  WHERE g.expense_category = 'Personnel'
  GROUP BY b.period, b.cost_center_code
) p ON p.period = h.period AND p.cost_center_code = h.cost_center_code;
