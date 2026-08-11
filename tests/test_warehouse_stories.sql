-- Warehouse-side verification: run the exact aggregations an analyst (or Genie) would
-- write, and confirm each planted story is the answer that falls out.

-- Q1: Which LOB overspent most in 2026-06? Expect Cards & Payments ~ +2.7m.
SELECT lob,
       round(sum(actual_usd)/1e6, 2)   AS actual_m,
       round(sum(budget_usd)/1e6, 2)   AS budget_m,
       round(sum(variance_usd)/1e6, 2) AS variance_m
FROM v_opex_variance
WHERE period = '2026-06' AND account_type = 'Expense'
GROUP BY lob ORDER BY variance_m DESC;

-- Q2: What drove the Cards & Payments overrun? Expect consulting + cloud + licences.
SELECT gl_account_name, cost_center_name,
       round(sum(variance_usd)/1e3, 0) AS variance_k
FROM v_opex_variance
WHERE period = '2026-06' AND account_type = 'Expense' AND lob = 'Cards & Payments'
GROUP BY gl_account_name, cost_center_name
HAVING sum(variance_usd) > 50000
ORDER BY variance_k DESC LIMIT 8;

-- Q3: Is the overrun a trend? Expect a rising ramp Mar -> Jun.
SELECT period, round(sum(variance_usd)/1e6, 2) AS variance_m
FROM v_opex_variance
WHERE lob = 'Cards & Payments' AND account_type = 'Expense'
  AND period >= '2026-01'
GROUP BY period ORDER BY period;

-- Q4: FX story. MB-UK / MB-DE unfavourable in USD but favourable in local currency.
SELECT entity_code, functional_currency,
       round(sum(variance_usd)/1e3, 0)               AS var_usd_k,
       round(sum(variance_usd_constant_ccy)/1e3, 0)  AS var_const_ccy_k,
       round(sum(fx_translation_impact_usd)/1e3, 0)  AS fx_impact_k
FROM v_opex_variance
WHERE period = '2026-06' AND account_type = 'Expense'
GROUP BY entity_code, functional_currency ORDER BY fx_impact_k DESC;

-- Q5: Aged accruals breaching the 90-day policy. Expect 6 rows, 4 in Cards & Payments.
SELECT policy_status, count(*) AS n, round(sum(accrual_amount_usd), 0) AS total_usd
FROM v_aged_accrual GROUP BY policy_status ORDER BY policy_status;

SELECT accrual_id, cost_center_name, lob, vendor_name, accrual_amount_usd, age_days, accrual_basis
FROM v_aged_accrual WHERE policy_status = 'BREACH_OVER_90_DAYS'
ORDER BY accrual_amount_usd DESC;

-- Q6: Close SLA breaches in 2026-06. Expect exactly 3, two teams.
SELECT period, entity_code, task_name, owner_team, sla_business_day, actual_business_day, days_late
FROM v_close_performance WHERE period = '2026-06' AND is_sla_breach = 'Y'
ORDER BY days_late DESC;

-- Q7: Largest 90+ day payables exposure. Expect Helix ~1.31m, all disputed.
SELECT vendor_name, count(*) AS invoices,
       round(sum(invoice_amount_usd), 0) AS amount_usd,
       collect_set(status) AS statuses
FROM v_ap_aging WHERE aging_bucket = '90+'
GROUP BY vendor_name ORDER BY amount_usd DESC LIMIT 5;

-- Q8: Unresolved intercompany breaks. Expect MB-UK -> MB-SG, 482k, 2 periods.
SELECT period, billing_entity, receiving_entity, service_type, difference_usd, status
FROM fact_intercompany WHERE status = 'UNRESOLVED_BREAK' ORDER BY period;

-- Q9: Contractor surge explaining part of the Cards overrun.
SELECT period, cost_center_name, fte_count, contractor_count,
       round(personnel_cost_usd/1e3, 0) AS personnel_k
FROM v_headcount_cost
WHERE cost_center_name = 'Cards Platform Engineering' AND period >= '2026-01'
ORDER BY period;

-- Q10: Row counts / freshness sanity.
SELECT 'fact_gl_balance' t, count(*) n, min(period) lo, max(period) hi FROM fact_gl_balance
UNION ALL SELECT 'fact_budget', count(*), min(period), max(period) FROM fact_budget
UNION ALL SELECT 'v_opex_variance', count(*), min(period), max(period) FROM v_opex_variance
UNION ALL SELECT 'fact_accrual', count(*), min(period_posted), max(period_posted) FROM fact_accrual
UNION ALL SELECT 'fact_ap_open_item', count(*), min(invoice_date), max(invoice_date) FROM fact_ap_open_item
UNION ALL SELECT 'fact_close_task', count(*), min(period), max(period) FROM fact_close_task
UNION ALL SELECT 'fact_intercompany', count(*), min(period), max(period) FROM fact_intercompany
UNION ALL SELECT 'fact_headcount', count(*), min(period), max(period) FROM fact_headcount;
