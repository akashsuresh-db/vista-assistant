"""Month-End Close Procedure (FSSC-SOP-002)

This module defines the standard operating procedure for Meridian Bank's month-end
close process, operated by the Finance Shared Services Centre (FSSC) in Chennai.
The procedure encompasses Record-to-Report (R2R), Procure-to-Pay (P2P), and Order-to-Cash
(O2C) process owners across all five operating entities: MB-US, MB-UK, MB-DE, MB-SG, MB-IN.

The close calendar is the primary control mechanism; it specifies a sequence of tasks
with SLA targets, defined owners, and dependencies. Breaches are tracked and escalated.
"""

DOC = {
    "filename": "FSSC-SOP-002_Month_End_Close_Procedure.pdf",
    "title": "Month-End Close Procedure",
    "subtitle": "FSSC-SOP-002 v7.1 | Effective 2026-01-01 | Finance Shared Services Centre, Chennai",
    "meta": [
        ("SOP Reference", "FSSC-SOP-002"),
        ("Version", "7.1"),
        ("Effective Date", "2026-01-01"),
        ("Owner", "Head of Record to Report"),
        ("FSSC Location", "Chennai / Bangalore"),
        ("Last Updated", "2026-02-28"),
    ],
    "blocks": [
        ("h1", "Purpose and Scope"),
        ("p", "This Standard Operating Procedure (SOP) establishes the mandatory process, timeline, "
         "quality gates, and escalation protocols for closing the monthly financial statements for Meridian Bank. "
         "The month-end close is a coordinated effort across three process pillars: <b>Procure-to-Pay (P2P)</b>, "
         "<b>Order-to-Cash (O2C)</b>, and <b>Record-to-Report (R2R)</b>. The Finance Shared Services Centre (FSSC), "
         "headquartered in Chennai with backup capacity in Bangalore, operates the close process for all five operating entities."),

        ("h2", "Entities in Scope"),
        ("p", "This SOP applies to the following entities, which report to the Group Finance function:"),
        ("bullets", [
            "Meridian Bank N.A. (MB-US, functional currency USD) — North America",
            "Meridian Bank plc (MB-UK, functional currency GBP) — EMEA",
            "Meridian Bank Europe GmbH (MB-DE, functional currency EUR) — EMEA",
            "Meridian Bank Singapore Ltd (MB-SG, functional currency SGD) — APAC",
            "Meridian Global Services India (MB-IN, functional currency INR) — APAC Finance Service Centre",
        ]),

        ("h2", "FSSC Operating Model"),
        ("p", "The FSSC employs approximately 200 finance analysts organized into specialized teams:"),
        ("bullets", [
            "<b>Record-to-Report (R2R) Team:</b> Manages GL reconciliations, accruals, fixed asset accounting, "
            "FX revaluation, intercompany matching, cost allocation, trial balance, variance analysis, and close sign-off.",
            "<b>Procure-to-Pay (P2P) Team:</b> Owns vendor invoice receipt, matching (3-way and invoice-to-PO-receipt), "
            "payment processing, and AP aging management.",
            "<b>Order-to-Cash (O2C) Team:</b> Manages billing, revenue recognition, AR aging, and collections.",
            "<b>Analytics & Controls:</b> Operates close monitoring dashboards, exception management, and escalation."
        ]),

        ("h1", "Month-End Close Calendar"),
        ("h2", "Close Timeline and Task Dependencies"),
        ("p", "The close process runs on a defined 8-business-day cycle beginning on the first business day "
         "after month-end. Each task has a target completion day (SLA), an assigned owner team, and documented dependencies. "
         "The following table specifies the full close calendar:"),

        ("table", [
            ["Day", "Task Name", "Owner Team", "SLA Day", "Entities", "Dependencies"],
            ["1", "Sub-ledger cut-off - AP (Procure to Pay)", "P2P", "1", "All", "Vendor invoice receipt completed"],
            ["1", "Sub-ledger cut-off - AR (Order to Cash)", "O2C", "1", "All", "Customer invoice issuance completed"],
            ["1", "Payroll interface posting (Record to Report)", "R2R", "1", "All", "HR/Payroll system extract available"],
            ["2", "Accrual calculation & upload", "R2R", "2", "All", "Sub-ledger cut-offs complete; cost drivers available"],
            ["2", "Prepaid amortisation run", "R2R", "2", "All", "Prepaid register updated"],
            ["2", "Fixed asset depreciation run", "R2R", "2", "All", "Asset disposals reconciled; depreciation schedule validated"],
            ["3", "FX revaluation run", "R2R", "3", "MB-UK / MB-DE / MB-SG / MB-IN", "Monthly average FX rates locked by Treasury"],
            ["3", "Intercompany billing & matching", "R2R", "3", "All", "Intercompany billings issued; prior-month breaks identified"],
            ["3", "Bank reconciliation sign-off", "R2R", "3", "All", "Bank statements received; reconciling items cleared"],
            ["4", "Cost allocation cycle", "R2R", "4", "All", "Allocation drivers validated; cost pool definitions confirmed"],
            ["4", "Trial balance review - entity", "R2R", "4", "All", "All GL postings complete; reconciliations signed"],
            ["5", "Variance analysis & commentary", "R2R", "5", "All", "Budget data loaded; actual actuals finalized"],
            ["5", "Balance sheet substantiation", "R2R", "5", "All", "GL reconciliations complete; inter-company matches complete"],
            ["6", "Flux report to Group", "R2R", "6", "All", "Consolidation-ready balances prepared"],
            ["6", "Management pack preparation", "R2R", "6", "All", "All variance commentary signed"],
            ["7", "Regulatory return feed", "R2R", "7", "MB-UK / MB-DE", "Consolidated balances finalized"],
            ["7", "Statutory ledger close", "R2R", "7", "All", "Regulatory feed complete"],
            ["8", "Group consolidation submission", "R2R", "8", "All (consol)", "All entity closes signed; consolidation reconciliations matched"],
        ]),

        ("h1", "SLA Breach Management"),
        ("h2", "SLA Definition and Escalation"),
        ("callout", "<b>SLA Breach:</b> A task is considered in breach when its actual completion business day "
         "exceeds its scheduled SLA business day. Example: if a task has an SLA of day 2 but is not completed until day 4, "
         "the breach is 2 days late (days_late = 4 – 2 = 2). "
         "<b>Escalation Protocol:</b> Breaches are reported in real-time in the close performance dashboard (fact_close_task / v_close_performance). "
         "A single task >1 day late is escalated to the Head of Record-to-Report same business day. "
         "Any entity with >2 tasks late OR any task >2 days late triggers escalation to the Group Financial Controller. "
         "All breaches are rolled into the weekly close scorecard and reviewed with Group Finance leadership."),

        ("h2", "Monitoring and Reporting"),
        ("p", "The close performance view (<b>v_close_performance</b>) includes columns: is_sla_breach (boolean), "
         "days_late (integer), task_name, entity, owner_team, actual_completion_date, scheduled_sla_date. "
         "The Analytics team runs a daily 14:00 UTC close check and posts results to the FSSC Slack channel. "
         "Any breach is escalated immediately via exception notification."),

        ("h1", "Variance Analysis and Commentary Standards"),
        ("h2", "Variance Threshold and Accountability"),
        ("p", "Variance commentary is required for all items exceeding either <b>USD 250,000 absolute value</b> "
         "or <b>5% of the budgeted line</b>, whichever is the lower threshold. For example, if a cost centre budgeted "
         "USD 8 million for salaries, a 5% threshold is USD 400,000; hence commentary is required for any variance above "
         "USD 250,000 (the lower of the two). All variance explanations are subject to sign-off by the relevant cost centre "
         "owner and reviewed by the Head of R2R before close sign-off."),

        ("h2", "Required Elements of Variance Commentary"),
        ("p", "Every variance commentary must include the following elements:"),
        ("bullets", [
            "<b>Driver:</b> A clear statement of the business root cause (e.g., 'Project Helios platform migration costs', "
            "'GBP strengthened from 1.178 to 1.299', 'Higher-than-budgeted contractor spend due to unanticipated departures').",
            "<b>One-Off vs. Run-Rate:</b> Explicit classification of whether the variance is a one-time event or a "
            "structural change to spending that will continue into future periods.",
            "<b>Accountable Owner:</b> The individual cost centre owner responsible for the variance (name and title).",
            "<b>Corrective Action (if unfavourable):</b> A specific remediation plan with target timeline. If the variance is "
            "controllable and recurrence is expected, state the mitigation or budget reforecasting action. If uncontrollable "
            "(e.g., pure FX translation), state 'N/A — uncontrollable translation effect' and cite policy FIN-FX-007.",
        ]),

        ("h2", "Variance Commentary Examples"),
        ("p", "<b>Example 1: Good Commentary (Project Helios, Cards Platform Engineering, 2026-06)</b>"),
        ("callout", "<b>Driver:</b> Project Helios, the card-processing platform migration to cloud, generated unbudgeted costs: "
         "consulting services (Helix Consulting Partners) +USD 979k, cloud hosting and compute +USD 608k, software licences +USD 361k. "
         "The project was approved after the AOP_2026_v3 plan was locked. Contractor headcount in Cards Platform Engineering rose from "
         "35 to 95 between January and June 2026. <br/>"
         "<b>One-Off vs. Run-Rate:</b> This is a ramp spend (not a one-off). Monthly actuals: Mar +0.53m, Apr +0.65m, May +1.46m, Jun +2.72m. "
         "We expect this spend to plateau at approximately USD 2.8–3.0m per month through Q3 2026 and then decline as the platform "
         "stabilization phase completes (currently slated for end-Q3). <br/>"
         "<b>Accountable Owner:</b> John Chen, VP Cards Platform Engineering. <br/>"
         "<b>Corrective Action:</b> We have submitted a reforecast (AOP_2026_v4) to the CFO with an updated Project Helios trajectory. "
         "The project is tracking to the contractual milestone schedule; no further cost inflation is anticipated beyond the current "
         "forecast. Monthly reviews of vendor invoices and resource utilization have been implemented."),

        ("p", "<b>Example 2: Poor Commentary (Not Sufficient)</b>"),
        ("callout", "<b>Driver:</b> Variance due to operational efficiency issues. <br/>"
         "<b>One-Off vs. Run-Rate:</b> Ongoing. <br/>"
         "<b>Accountable Owner:</b> Finance Team. <br/>"
         "<b>Corrective Action:</b> We will review costs. "
         "<br/><br/>"
         "<i>Issues with this commentary:</i> (1) 'Operational efficiency issues' is vague; it does not pinpoint the cost driver. "
         "(2) 'Finance Team' is not a named individual; accountability is unclear. (3) 'We will review costs' is not a concrete action "
         "with a timeline or expected outcome. (4) No quantification of which GL accounts or cost drivers are affected."),

        ("h1", "FX Translation and Constant-Currency Reporting"),
        ("h2", "FX Policy Integration (FIN-FX-007)"),
        ("p", "All foreign-currency variances must be decomposed into two components per policy <b>FIN-FX-007</b>:"),
        ("bullets", [
            "<b>Budget Rate Lock:</b> Annual operating plan budgets are translated to USD at the plan rate, which is fixed on January 15 "
            "of each fiscal year. For fiscal 2026, the plan rates were: GBP 1.178, EUR 0.992, SGD 0.741, INR 0.0120. These rates do not change "
            "during the fiscal year unless a full replan is issued.",
            "<b>Actual Translation at Monthly Average Rate:</b> Actual P&L items are translated at the monthly average exchange rate published "
            "by the ECB (EUR), Bank of England (GBP), Monetary Authority of Singapore (SGD), and RBI (INR). June 2026 actual rates were: "
            "GBP 1.299 (+10.3%), EUR 1.091 (+9.95%), SGD 0.752 (+1.5%), INR 0.0120 (flat).",
            "<b>Constant-Currency Variance:</b> The accountability measure for cost centre owners. This isolates spending control "
            "(Did we spend more in local currency?) from translation effects (Did the local currency move?). Cost centre managers are held "
            "accountable for constant-currency variance only.",
        ]),

        ("h2", "Variance Reporting Example: MB-UK 2026-06"),
        ("p", "MB-UK reported a total USD variance of +USD 798k unfavourable. The breakdown:"),
        ("table", [
            ["Component", "Amount", "Interpretation"],
            ["Constant-Currency Variance", "+USD 107k", "Unfavourable; actual spending exceeded budget in GBP terms"],
            ["FX Translation Impact", "+USD 691k", "Unfavourable due to GBP strengthening from 1.178 to 1.299 plan rate"],
            ["Total USD Variance (Reported)", "+USD 798k", "Overspend in USD reporting currency"],
            ["Local Currency Performance", "~6% favourable", "MB-UK achieved a 6% cost savings in GBP; management performed well"],
        ]),
        ("p", "The key insight: <b>in local GBP terms, MB-UK was under budget. The reported USD variance is misleading without "
         "decomposition.</b> Cost centre managers are <b>not accountable</b> for the USD 691k translation headwind; this is a macro "
         "effect controlled by Group Treasury (hedging) and macroeconomic factors. Variance commentary for MB-UK should lead with the "
         "constant-currency result and then note the translation headwind as context."),

        ("h1", "Quality Gates and Four-Eyes Review Protocol"),
        ("h2", "Inter-Process Handoffs"),
        ("p", "The close process includes formal quality gates at each process transition to ensure data integrity and prevent downstream rework:"),
        ("bullets", [
            "<b>P2P to R2R Handoff (Day 1):</b> P2P certifies that vendor invoices have been reconciled to POs and receiving documents; "
            "disputed items and price variances are flagged in <b>fact_ap_open_item</b> with match_status codes (PRICE_VARIANCE, QTY_VARIANCE, UNMATCHED). "
            "R2R cannot proceed with accrual calculations until P2P reconciliation is complete and sign-off received.",
            "<b>O2C to R2R Handoff (Day 1):</b> O2C confirms that all customer billings have been issued and revenue recognition entries posted. "
            "Revenue accruals for goods-delivered-not-invoiced items are prepared by O2C and handed to R2R for GL posting.",
            "<b>R2R Internal Review (Day 4):</b> Trial balance is reviewed by a second R2R analyst (not the original preparer) to validate "
            "reconciliation completeness and identify unusual or unreconciled balances. This is the <b>four-eyes review</b> gate.",
            "<b>Cost Centre Owner Sign-Off (Day 5):</b> Variance commentary and balance sheet substantiation are reviewed and signed by the "
            "responsible cost centre owner before forwarding to the Head of R2R.",
            "<b>Head of R2R Final Review (Day 7):</b> The Head of R2R validates that all variance commentary meets the quality standard, "
            "all four-eyes reviews are complete, and the financial statements are ready for group consolidation.",
        ]),

        ("h2", "Four-Eyes Review Definition"),
        ("p", "A <b>four-eyes review</b> (also called 'dual control' or 'independent review') means that a transaction, reconciliation, or "
         "variance commentary is prepared by one analyst and reviewed/approved by a second analyst who was not involved in the preparation. "
         "The reviewer must have the authority to challenge the preparer. At minimum, the reviewer initials and dates the work paper. "
         "For materiality threshold items (variance > USD 500k), the four-eyes review is mandatory. For all other items, four-eyes reviews "
         "are applied at the manager's discretion based on risk and complexity."),

        ("h1", "Common Close Issues and Troubleshooting"),
        ("h2", "Incident Log and Root Cause Framework"),
        ("p", "The close process frequently encounters recurring bottlenecks and data issues. The following table catalogs the most common "
         "close incidents, their typical symptoms, likely root causes, and recommended resolution steps. When a close issue is identified, "
         "the owning team should consult this table, execute the resolution, and log the incident in the close exception log (available in "
         "the FSSC Slack channel #close-exceptions) for trend analysis."),

        ("table", [
            ["Symptom", "Typical Cause", "Team", "Resolution"],
            ["AP cut-off delayed", "Vendor invoices late; 3-way match errors", "P2P", "Confirm receipts; flag unmatched as disputed; proceed on known items"],
            ["Payroll posting rejected", "Invalid GL/CC codes; missing HRIS records", "R2R + Payroll", "Validate mappings; cross-check employee master; resubmit"],
            ["Accrual calc delayed", "Missing cost drivers; prior accruals not cleared", "R2R", "Confirm driver availability; estimate using YTD average; document"],
            ["FX revaluation blocked", "Treasury rates not published; late transactions", "R2R + Treasury", "Use preliminary rates; post true-up next month"],
            ["Intercompany break", "Different periods; rate disagreement; no match received", "R2R", "Pull fact_intercompany; contact receiving team; escalate if >90 days"],
            ["Bank reconciliation pending", "Outstanding items; exceptions unresolved", "R2R", "Investigate with bank; request explanations; post adjustment if immaterial"],
            ["Allocation driver missing", "Source team data not submitted", "R2R", "Use prior-month distribution; request retroactively"],
            ["Unreconciled GL balances", "Entries without detail; clearing accounts OOB", "R2R", "Query entries; match to detail; reverse if error"],
            ["Variance commentary gaps", "Owner unavailable; insufficient detail", "R2R + Owner", "Re-engage with template; prepare draft if unavailable"],
            ["Statutory close rejected", "GL mismatch to prior; mapping errors", "R2R + Regulatory", "Run statutory reconciliation; correct mappings; clear aged breaks"],
        ]),

        ("h1", "Data Integrity and Close Reconciliation"),
        ("h2", "Daily Close Reconciliation Checks"),
        ("p", "The R2R team executes a standard set of daily reconciliation checks to ensure close data quality. These checks are automated where possible "
         "and are documented in the close exception log daily at 16:00 UTC:"),
        ("bullets", [
            "<b>GL Control Totals:</b> Sum of all GL account balances reconciles to the consolidated trial balance summary report. Variance > USD 1 "
            "triggers an investigation.",
            "<b>Intercompany Reciprocal Check:</b> For each intercompany balance, the billing entity's sent amount reconciles to the receiving entity's "
            "received amount (allowing for timing of postings). Unmatched breaks are logged in fact_intercompany with UNRESOLVED_BREAK status.",
            "<b>Accrual Aging:</b> All accruals created >90 days prior to the current close date are flagged and reviewed against policy FIN-ACC-014. "
            "If still open, the cost centre owner is contacted to clear or formally extend the accrual.",
            "<b>Bank/AP/AR Reconciliation:</b> Bank balance equals GL bank account balance; AP subsidiary ledger reconciles to GL AP control account; "
            "AR subsidiary ledger reconciles to GL AR control account.",
            "<b>FX Rate Validation:</b> For all foreign-currency entities, current-month translation rates match the dim_fx_rate table. Plan rates match "
            "the rate_type = PLAN_2026.",
        ]),

        ("h2", "Close Sign-Off and Certification"),
        ("p", "The close is considered complete when the following sign-offs are obtained, in sequence:"),
        ("bullets", [
            "<b>P2P Team Lead (Day 1 EOD):</b> Certifies that sub-ledger cut-off is complete and all 3-way matches have been performed.",
            "<b>O2C Team Lead (Day 1 EOD):</b> Certifies that billing cut-off and revenue accruals are complete.",
            "<b>R2R Analyst (Day 4 EOD):</b> Completes trial balance and GL reconciliations; second analyst (four-eyes) reviews and signs.",
            "<b>Cost Centre Owners (Day 5 EOD):</b> Review and sign off on variance commentary and balance sheet substantiation.",
            "<b>Head of R2R (Day 7 EOD):</b> Reviews all sign-offs, validates quality gate completion, and approves close for group consolidation.",
            "<b>Group Consolidation Lead (Day 8):</b> Receives signed entity closes, reconciles consolidation journals, and submits group financials to "
            "the CFO's office.",
        ]),

        ("h1", "References and Related Policies"),
        ("bullets", [
            "<b>FIN-FX-007:</b> Foreign Currency Translation and Constant-Currency Reporting Policy — governs budget rate lock, constant-currency "
            "variance, and accountabilities for FX translation impacts.",
            "<b>FIN-ACC-014:</b> Accruals and Estimates Policy — defines the 90-day accrual aging rule and documentation requirements for accrual "
            "justification.",
            "<b>FIN-IC-021:</b> Intercompany Reconciliation Standard — establishes process for billings, matching, and resolution of intercompany breaks.",
            "<b>Meridian Bank Group Finance GL Chart of Accounts:</b> Defines all GL account codes (e.g., 510100 Salaries & Wages, 520100 Software "
            "Licences, 530100 Professional Fees - Consulting, 590100 Intercompany Service Recharge).",
            "<b>Data sources (the finance marts in Unity Catalog):</b> dim_entity, dim_cost_center, dim_gl_account, dim_fx_rate, fact_gl_balance, "
            "fact_budget, fact_headcount, fact_accrual, fact_ap_open_item, fact_intercompany, fact_close_task, v_opex_variance, v_aged_accrual, "
            "v_close_performance, v_ap_aging, v_headcount_cost.",
        ]),

        ("h1", "Document Control"),
        ("bullets", [
            "This SOP is reviewed annually by the Head of Record-to-Report and updated as needed to reflect process improvements or policy changes.",
            "All changes to the close calendar (Day 1–8 task list, SLA targets, owner teams) must be approved by the Head of R2R and communicated "
            "to all process owners 30 days in advance of implementation.",
            "The most recent version is maintained in the FSSC Wiki and distributed to all analysts during the monthly close kick-off.",
        ]),
    ],
    "footer": "Meridian Bank - Group Finance",
    "classification": "Internal",
}
