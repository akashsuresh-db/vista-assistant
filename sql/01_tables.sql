-- This file uses {catalog} and {schema} placeholders.
-- run_sql.py substitutes from CFG before executing.

-- Phase 2: build the structured marts from the staged CSVs.
-- Every table and column carries a COMMENT: Genie leans heavily on this metadata to
-- generate correct SQL, so the comments are part of the deliverable, not decoration.

-- ============================================================ DIMENSIONS
CREATE OR REPLACE TABLE dim_entity
COMMENT 'Legal entities of Meridian Bank. Group reports in USD; each entity keeps books in its own functional currency.'
AS SELECT * FROM read_files(
  '/Volumes/{catalog}/{schema}/vista_documents/_staging_csv/dim_entity.csv',
  format => 'csv', header => true, inferSchema => true);

ALTER TABLE dim_entity ALTER COLUMN entity_code COMMENT 'Entity code, e.g. MB-US, MB-UK. Join key to all fact tables.';
ALTER TABLE dim_entity ALTER COLUMN entity_name COMMENT 'Legal entity name.';
ALTER TABLE dim_entity ALTER COLUMN functional_currency COMMENT 'Currency the entity keeps its books in (local currency).';
ALTER TABLE dim_entity ALTER COLUMN region COMMENT 'Reporting region: North America, EMEA or APAC.';
ALTER TABLE dim_entity ALTER COLUMN reporting_currency COMMENT 'Group reporting currency, always USD.';

CREATE OR REPLACE TABLE dim_cost_center
COMMENT 'Cost centre master. A cost centre belongs to exactly one line of business (LOB) and one legal entity, and has a named finance owner.'
AS SELECT * FROM read_files(
  '/Volumes/{catalog}/{schema}/vista_documents/_staging_csv/dim_cost_center.csv',
  format => 'csv', header => true, inferSchema => true);

ALTER TABLE dim_cost_center ALTER COLUMN cost_center_code COMMENT 'Cost centre code, e.g. CC1010. Join key to fact tables.';
ALTER TABLE dim_cost_center ALTER COLUMN cost_center_name COMMENT 'Cost centre name, e.g. Cards Platform Engineering.';
ALTER TABLE dim_cost_center ALTER COLUMN lob COMMENT 'Line of business. One of: Retail Banking, Cards & Payments, Wealth Management, Corporate Banking, Treasury, Technology, Operations, Risk & Compliance. Use this for "by division" or "by business" questions.';
ALTER TABLE dim_cost_center ALTER COLUMN entity_code COMMENT 'Owning legal entity code.';
ALTER TABLE dim_cost_center ALTER COLUMN region COMMENT 'Region of the owning entity.';
ALTER TABLE dim_cost_center ALTER COLUMN cc_owner COMMENT 'Finance business partner accountable for this cost centre.';

CREATE OR REPLACE TABLE dim_gl_account
COMMENT 'General ledger chart of accounts. Expense accounts are grouped into expense_category for management reporting.'
AS SELECT * FROM read_files(
  '/Volumes/{catalog}/{schema}/vista_documents/_staging_csv/dim_gl_account.csv',
  format => 'csv', header => true, inferSchema => true,
  schemaHints => 'gl_account STRING');

ALTER TABLE dim_gl_account ALTER COLUMN gl_account COMMENT 'GL account code as a string, e.g. 530100.';
ALTER TABLE dim_gl_account ALTER COLUMN gl_account_name COMMENT 'GL account name, e.g. Professional Fees - Consulting.';
ALTER TABLE dim_gl_account ALTER COLUMN account_type COMMENT 'Either Expense or Revenue. Filter to Expense for opex/cost questions.';
ALTER TABLE dim_gl_account ALTER COLUMN expense_category COMMENT 'Management reporting category: Personnel, Technology, Professional Fees, Premises, Marketing, Travel, Depreciation, Transaction Costs, Allocations, Revenue.';
ALTER TABLE dim_gl_account ALTER COLUMN is_controllable COMMENT 'Y if the cost centre owner can influence this cost in-year; N for allocations, depreciation and statutory charges.';

CREATE OR REPLACE TABLE dim_fx_rate
COMMENT 'Monthly FX rates, USD per one unit of local currency. MONTHLY_AVERAGE is used to translate P&L; PERIOD_END for balance sheet.'
AS SELECT * FROM read_files(
  '/Volumes/{catalog}/{schema}/vista_documents/_staging_csv/dim_fx_rate.csv',
  format => 'csv', header => true, inferSchema => true,
  schemaHints => 'period STRING');

ALTER TABLE dim_fx_rate ALTER COLUMN period COMMENT 'Accounting period as YYYY-MM text, e.g. 2026-06.';
ALTER TABLE dim_fx_rate ALTER COLUMN currency COMMENT 'Local currency code: USD, GBP, EUR, SGD, INR.';
ALTER TABLE dim_fx_rate ALTER COLUMN rate_type COMMENT 'MONTHLY_AVERAGE or PERIOD_END.';
ALTER TABLE dim_fx_rate ALTER COLUMN usd_per_unit COMMENT 'USD per one unit of the local currency. Multiply a local amount by this to get USD.';

-- ============================================================ FACTS
CREATE OR REPLACE TABLE fact_gl_balance
COMMENT 'Monthly actual GL balances by entity, cost centre and account. amount_local is what was posted in the entity currency; amount_usd is the same value translated at that month''s actual average rate. Expenses are positive, revenue is negative.'
AS SELECT * FROM read_files(
  '/Volumes/{catalog}/{schema}/vista_documents/_staging_csv/fact_gl_balance.csv',
  format => 'csv', header => true, inferSchema => true,
  schemaHints => 'period STRING, fiscal_quarter STRING, gl_account STRING');

ALTER TABLE fact_gl_balance ALTER COLUMN period COMMENT 'Accounting period as YYYY-MM text, e.g. 2026-06. The latest closed period is 2026-06.';
ALTER TABLE fact_gl_balance ALTER COLUMN fiscal_year COMMENT 'Fiscal year, equal to calendar year.';
ALTER TABLE fact_gl_balance ALTER COLUMN fiscal_quarter COMMENT 'Fiscal quarter label, e.g. 2026-Q2.';
ALTER TABLE fact_gl_balance ALTER COLUMN entity_code COMMENT 'Legal entity code. Join to dim_entity.';
ALTER TABLE fact_gl_balance ALTER COLUMN cost_center_code COMMENT 'Cost centre code. Join to dim_cost_center to get LOB.';
ALTER TABLE fact_gl_balance ALTER COLUMN gl_account COMMENT 'GL account code. Join to dim_gl_account.';
ALTER TABLE fact_gl_balance ALTER COLUMN local_currency COMMENT 'Currency of amount_local.';
ALTER TABLE fact_gl_balance ALTER COLUMN amount_local COMMENT 'Actual amount in the entity functional (local) currency. Use this to judge whether a team overspent on its own terms, free of FX effects.';
ALTER TABLE fact_gl_balance ALTER COLUMN fx_rate_usd COMMENT 'Actual monthly average rate used to translate this row to USD.';
ALTER TABLE fact_gl_balance ALTER COLUMN amount_usd COMMENT 'Actual amount translated to USD at the actual monthly rate. This is the Group-reported figure and the default for any consolidated question.';
ALTER TABLE fact_gl_balance ALTER COLUMN posting_source COMMENT 'Source system of the posting: SAP_S4_GL, SUBLEDGER_AP, SUBLEDGER_PAYROLL, MANUAL_JOURNAL, ALLOCATION_ENGINE.';
ALTER TABLE fact_gl_balance ALTER COLUMN is_planted_overrun COMMENT 'Internal demo flag. Do NOT use in answers or filters.';

CREATE OR REPLACE TABLE fact_budget
COMMENT 'Annual operating plan (budget) and latest forecast by period, entity, cost centre and account. budget_usd is translated at the plan FX rate locked at the start of the fiscal year, which is why a USD variance can arise purely from currency movement.'
AS SELECT * FROM read_files(
  '/Volumes/{catalog}/{schema}/vista_documents/_staging_csv/fact_budget.csv',
  format => 'csv', header => true, inferSchema => true,
  schemaHints => 'period STRING, gl_account STRING');

ALTER TABLE fact_budget ALTER COLUMN period COMMENT 'Accounting period as YYYY-MM text.';
ALTER TABLE fact_budget ALTER COLUMN fiscal_year COMMENT 'Fiscal year of the plan.';
ALTER TABLE fact_budget ALTER COLUMN entity_code COMMENT 'Legal entity code.';
ALTER TABLE fact_budget ALTER COLUMN cost_center_code COMMENT 'Cost centre code.';
ALTER TABLE fact_budget ALTER COLUMN gl_account COMMENT 'GL account code.';
ALTER TABLE fact_budget ALTER COLUMN budget_usd COMMENT 'Approved budget in USD, translated at the locked plan FX rate.';
ALTER TABLE fact_budget ALTER COLUMN budget_local COMMENT 'Approved budget in the entity local currency. Compare against amount_local for a constant-currency (FX-neutral) variance.';
ALTER TABLE fact_budget ALTER COLUMN plan_fx_rate_usd COMMENT 'The FX rate locked when the budget was approved (January of the fiscal year).';
ALTER TABLE fact_budget ALTER COLUMN forecast_usd COMMENT 'Latest re-forecast in USD, which may already reflect known overspend.';
ALTER TABLE fact_budget ALTER COLUMN budget_version COMMENT 'Plan version, e.g. AOP_2026_v3.';

CREATE OR REPLACE TABLE fact_headcount
COMMENT 'Month-end headcount by cost centre: permanent FTE, contractors, open roles and leavers. Useful to explain personnel cost variances.'
AS SELECT * FROM read_files(
  '/Volumes/{catalog}/{schema}/vista_documents/_staging_csv/fact_headcount.csv',
  format => 'csv', header => true, inferSchema => true,
  schemaHints => 'period STRING');

ALTER TABLE fact_headcount ALTER COLUMN period COMMENT 'Accounting period as YYYY-MM text, e.g. 2026-06.';
ALTER TABLE fact_headcount ALTER COLUMN cost_center_code COMMENT 'Cost centre code.';
ALTER TABLE fact_headcount ALTER COLUMN entity_code COMMENT 'Legal entity code.';
ALTER TABLE fact_headcount ALTER COLUMN fte_count COMMENT 'Permanent FTE headcount at month-end.';
ALTER TABLE fact_headcount ALTER COLUMN contractor_count COMMENT 'Contractor headcount.';
ALTER TABLE fact_headcount ALTER COLUMN open_positions COMMENT 'Unfilled approved headcount (impact on future costs when filled).';
ALTER TABLE fact_headcount ALTER COLUMN attrition_leavers COMMENT 'People who left in the month.';

CREATE OR REPLACE TABLE fact_accrual
COMMENT 'Open and reversed accruals with age and status. Accounting policy FIN-ACC-014 requires substantiation or reversal within 90 days; rows with age_days > 90 and status=OPEN are policy breaches.'
AS SELECT * FROM read_files(
  '/Volumes/{catalog}/{schema}/vista_documents/_staging_csv/fact_accrual.csv',
  format => 'csv', header => true, inferSchema => true,
  schemaHints => 'period_posted STRING');

ALTER TABLE fact_accrual ALTER COLUMN accrual_id COMMENT 'Unique accrual identifier.';
ALTER TABLE fact_accrual ALTER COLUMN period_posted COMMENT 'Period the accrual was recorded, as YYYY-MM text.';
ALTER TABLE fact_accrual ALTER COLUMN entity_code COMMENT 'Legal entity code.';
ALTER TABLE fact_accrual ALTER COLUMN cost_center_code COMMENT 'Cost centre code.';
ALTER TABLE fact_accrual ALTER COLUMN gl_account COMMENT 'GL account code.';
ALTER TABLE fact_accrual ALTER COLUMN vendor_id COMMENT 'Vendor identifier.';
ALTER TABLE fact_accrual ALTER COLUMN vendor_name COMMENT 'Vendor name.';
ALTER TABLE fact_accrual ALTER COLUMN accrual_amount_usd COMMENT 'Accrual amount in USD.';
ALTER TABLE fact_accrual ALTER COLUMN accrual_basis COMMENT 'How the amount was estimated: PO_RECEIPT_NOT_INVOICED, SERVICE_DELIVERED_NOT_BILLED, ESTIMATE_FROM_CONTRACT, RUN_RATE_ESTIMATE, MANUAL_ESTIMATE.';
ALTER TABLE fact_accrual ALTER COLUMN posted_date COMMENT 'The date the accrual was posted, as YYYY-MM-DD text.';
ALTER TABLE fact_accrual ALTER COLUMN age_days COMMENT 'Days since posted_date to the month-end close date.';
ALTER TABLE fact_accrual ALTER COLUMN is_reversed COMMENT 'Y if reversed in a subsequent period, N if still open.';
ALTER TABLE fact_accrual ALTER COLUMN reversal_period COMMENT 'The period in which the accrual was reversed, if is_reversed=Y.';
ALTER TABLE fact_accrual ALTER COLUMN prepared_by COMMENT 'Finance team member who prepared the accrual.';
ALTER TABLE fact_accrual ALTER COLUMN approved_by COMMENT 'Finance team member who approved the accrual.';
ALTER TABLE fact_accrual ALTER COLUMN status COMMENT 'OPEN or REVERSED.';

CREATE OR REPLACE TABLE fact_ap_open_item
COMMENT 'Open accounts payable by invoice. The highest-risk population is aging_bucket=90+ combined with status=DISPUTED.'
AS SELECT * FROM read_files(
  '/Volumes/{catalog}/{schema}/vista_documents/_staging_csv/fact_ap_open_item.csv',
  format => 'csv', header => true, inferSchema => true);

ALTER TABLE fact_ap_open_item ALTER COLUMN invoice_id COMMENT 'Unique invoice identifier.';
ALTER TABLE fact_ap_open_item ALTER COLUMN vendor_id COMMENT 'Vendor identifier.';
ALTER TABLE fact_ap_open_item ALTER COLUMN vendor_name COMMENT 'Vendor name.';
ALTER TABLE fact_ap_open_item ALTER COLUMN entity_code COMMENT 'Legal entity code.';
ALTER TABLE fact_ap_open_item ALTER COLUMN cost_center_code COMMENT 'Cost centre code.';
ALTER TABLE fact_ap_open_item ALTER COLUMN gl_account COMMENT 'GL account code.';
ALTER TABLE fact_ap_open_item ALTER COLUMN invoice_date COMMENT 'Invoice date as YYYY-MM-DD text.';
ALTER TABLE fact_ap_open_item ALTER COLUMN due_date COMMENT 'Payment due date as YYYY-MM-DD text.';
ALTER TABLE fact_ap_open_item ALTER COLUMN payment_terms_days COMMENT 'Standard payment terms in days (e.g. Net 30, Net 60).';
ALTER TABLE fact_ap_open_item ALTER COLUMN invoice_amount_usd COMMENT 'Invoice amount in USD.';
ALTER TABLE fact_ap_open_item ALTER COLUMN aging_bucket COMMENT 'Age bucket: CURRENT, 1-30, 31-60, 61-90, 90+.';
ALTER TABLE fact_ap_open_item ALTER COLUMN days_overdue COMMENT 'Number of calendar days the invoice is overdue (0 if not yet due).';
ALTER TABLE fact_ap_open_item ALTER COLUMN status COMMENT 'OPEN, APPROVED_FOR_PAYMENT, ON_HOLD, or DISPUTED.';
ALTER TABLE fact_ap_open_item ALTER COLUMN match_status COMMENT 'Three-way match status: THREE_WAY_MATCHED, TWO_WAY_MATCHED, PRICE_VARIANCE, QTY_VARIANCE, NO_PO.';

CREATE OR REPLACE TABLE fact_intercompany
COMMENT 'Intercompany transactions by billing and receiving entity. status=MATCHED means the two sides reconciled; UNRESOLVED_BREAK means a break is still pending investigation.'
AS SELECT * FROM read_files(
  '/Volumes/{catalog}/{schema}/vista_documents/_staging_csv/fact_intercompany.csv',
  format => 'csv', header => true, inferSchema => true);

ALTER TABLE fact_intercompany ALTER COLUMN ic_id COMMENT 'Unique intercompany transaction identifier.';
ALTER TABLE fact_intercompany ALTER COLUMN period COMMENT 'Period of the transaction as YYYY-MM text.';
ALTER TABLE fact_intercompany ALTER COLUMN billing_entity COMMENT 'Entity code that billed the service.';
ALTER TABLE fact_intercompany ALTER COLUMN receiving_entity COMMENT 'Entity code that received and will pay for the service.';
ALTER TABLE fact_intercompany ALTER COLUMN service_type COMMENT 'Type of intercompany service, e.g. IT Shared Services, Finance Shared Services, Treasury Funding.';
ALTER TABLE fact_intercompany ALTER COLUMN billed_amount_usd COMMENT 'Amount billed by the sender in USD.';
ALTER TABLE fact_intercompany ALTER COLUMN received_amount_usd COMMENT 'Amount recorded as received by the receiver in USD.';
ALTER TABLE fact_intercompany ALTER COLUMN difference_usd COMMENT 'Reconciliation difference: received - billed. Zero means matched.';
ALTER TABLE fact_intercompany ALTER COLUMN status COMMENT 'MATCHED if reconciled, UNRESOLVED_BREAK if investigating a difference.';
ALTER TABLE fact_intercompany ALTER COLUMN settlement_due COMMENT 'Expected settlement date as YYYY-MM-DD text.';

CREATE OR REPLACE TABLE fact_close_task
COMMENT 'Month-end close process task execution by period, entity, process and task. Track SLA breaches to measure close health.'
AS SELECT * FROM read_files(
  '/Volumes/{catalog}/{schema}/vista_documents/_staging_csv/fact_close_task.csv',
  format => 'csv', header => true, inferSchema => true);

ALTER TABLE fact_close_task ALTER COLUMN task_id COMMENT 'Unique close task identifier.';
ALTER TABLE fact_close_task ALTER COLUMN period COMMENT 'Period being closed as YYYY-MM text.';
ALTER TABLE fact_close_task ALTER COLUMN entity_code COMMENT 'Legal entity code.';
ALTER TABLE fact_close_task ALTER COLUMN task_name COMMENT 'Name of the close task, e.g. Accrual calculation & upload.';
ALTER TABLE fact_close_task ALTER COLUMN fna_process COMMENT 'Finance process: R2R (Record to Report), P2P (Procure to Pay), O2C (Order to Cash).';
ALTER TABLE fact_close_task ALTER COLUMN sla_business_day COMMENT 'SLA target in business days from month-end.';
ALTER TABLE fact_close_task ALTER COLUMN actual_business_day COMMENT 'Actual completion in business days from month-end.';
ALTER TABLE fact_close_task ALTER COLUMN owner_team COMMENT 'Finance team responsible for execution.';
ALTER TABLE fact_close_task ALTER COLUMN owner COMMENT 'Named owner assigned to the task.';
ALTER TABLE fact_close_task ALTER COLUMN status COMMENT 'COMPLETE or COMPLETE_LATE.';
ALTER TABLE fact_close_task ALTER COLUMN is_sla_breach COMMENT 'Y if actual > sla, N otherwise.';
ALTER TABLE fact_close_task ALTER COLUMN days_late COMMENT 'Business days late (0 if on time).';
