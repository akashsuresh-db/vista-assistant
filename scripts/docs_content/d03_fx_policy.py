"""Foreign Currency Translation and Constant-Currency Reporting Policy (FIN-FX-007)

This module defines the policy content for FIN-FX-007, which governs how Meridian Bank
translates foreign-currency transactions and balances into the Group reporting currency
(USD) and how cost centre accountability is separated from translation effects.

The key concept: budgets are locked at the plan rate established in January of the fiscal
year; actuals translate at the monthly average rate. This means USD variances often contain
a translation component that is not controllable at cost centre level. Constant-currency
variance is the accountability measure.
"""

DOC = {
    "filename": "FIN-FX-007_Foreign_Currency_Translation_Policy.pdf",
    "title": "Foreign Currency Translation and Constant-Currency Reporting Policy",
    "subtitle": "FIN-FX-007 v3.0 | Effective 2026-01-01 | Group Treasury & Financial Control",
    "meta": [
        ("Policy Ref", "FIN-FX-007"),
        ("Version", "3.0"),
        ("Effective Date", "2026-01-01"),
        ("Owner", "Group Treasury & Financial Control"),
        ("Last Updated", "2025-12-15"),
    ],
    "blocks": [
        ("h1", "Policy Scope and Objective"),
        ("p", "This policy establishes the standards for translating foreign-currency transactions, "
         "balances, and results into United States Dollars (USD) for Group financial reporting. The policy "
         "aligns with International Accounting Standard 21 (IAS 21) <i>The Effects of Changes in Foreign "
         "Exchange Rates</i> and ensures consistent treatment of FX translation across all operating entities. "
         "Critically, this policy distinguishes between transactional FX, translational FX, and economic FX "
         "impacts, and clarifies which cost centre managers are accountable for each."),
        ("h2", "Functional and Presentation Currency"),
        ("p", "Each operating entity maintains its own functional currency (the currency of the economic "
         "environment in which it primarily operates). The Group's presentation currency is United States Dollars. "
         "Entities and their functional currencies are:"),
        ("table", [
            ["Entity", "Entity Code", "Functional Currency", "Region", "Reporting Status"],
            ["Meridian Bank N.A.", "MB-US", "USD", "North America", "Parent"],
            ["Meridian Bank plc", "MB-UK", "GBP", "EMEA", "Consolidated"],
            ["Meridian Bank Europe GmbH", "MB-DE", "EUR", "EMEA", "Consolidated"],
            ["Meridian Bank Singapore Ltd", "MB-SG", "SGD", "APAC", "Consolidated"],
            ["Meridian Global Services India", "MB-IN", "INR", "APAC", "Consolidated"],
        ]),
        ("h2", "Exchange Rates and Data Sources"),
        ("p", "All FX rates are sourced from <b>dim_fx_rate</b> in the Unity Catalog. Rates are stored "
         "with <b>rate_type</b> indicating either <b>MONTHLY_AVERAGE</b> or <b>PERIOD_END</b>. The rate "
         "value is expressed as <b>usd_per_unit</b> (i.e. the USD value of one unit of local currency). "
         "Example: GBP rate of 1.299 means 1 GBP = 1.299 USD."),
        ("h1", "Translation Methodology"),
        ("h2", "Income Statement (P&L) Translation"),
        ("p", "Income statement items are translated using the <b>monthly average exchange rate</b> for "
         "the reporting period in which the transaction occurred. This method is applied consistently to all "
         "revenue, cost of revenue, operating expenses, and other P&L line items."),
        ("bullets", [
            "Monthly average rates are established by Group Treasury on the first business day of each month.",
            "If an item straddles multiple months (e.g., accruals), the rate in effect when the item was first "
            "recognized is used unless a specific correction is identified.",
            "Monthly average rates are sourced from the closing rate published by the ECB (EUR), Bank of England (GBP), "
            "Monetary Authority of Singapore (SGD), and RBI (INR).",
        ]),
        ("h2", "Balance Sheet Translation"),
        ("p", "Balance sheet items are translated using the <b>period-end exchange rate</b> in effect on the "
         "last day of the reporting period. This applies to all assets, liabilities, and their components."),
        ("h2", "Equity Translation"),
        ("p", "Equity items (contributed capital, retained earnings) are translated at <b>historical rates</b> "
         "(the rates in effect when the equity was originally contributed or earned). Cumulative translation "
         "differences are captured in Other Comprehensive Income (OCI) and presented separately in the consolidated "
         "statement of changes in equity."),
        ("h1", "Budget Translation and Variance Decomposition"),
        ("h2", "Budget Rate Lock and Planning"),
        ("p", "Annual operating plan (AOP) budgets are established in late Q4 of the prior year and locked no later "
         "than January 31 of the fiscal year. At the time of lock, the <b>plan rate</b> for each foreign-currency "
         "entity is determined based on the spot rate as of January 15 of that fiscal year. This plan rate is held "
         "constant for the entire fiscal year and is used to translate all budgeted amounts in foreign currencies into USD."),
        ("p", "The plan rate is not adjusted for economic reforecasts, consensus updates, or mid-year rate movements. "
         "If a new plan is developed during the year (e.g., AOP v2, AOP v3), the plan rate may be reset only if the "
         "new plan extends beyond the end of the current fiscal year. Mid-period plan amendments that do not extend the "
         "plan horizon retain the original plan rate."),
        ("h2", "Constant-Currency Variance"),
        ("p", "Cost centre management accountability is measured on a <b>constant-currency basis</b>. This isolates "
         "the controllable spending decision (Did we spend more in local currency than we budgeted?) from the "
         "uncontrollable FX translation effect (Did the local currency strengthen or weaken relative to USD?)."),
        ("p", "<b>Constant-currency variance</b> is calculated as:"),
        ("callout", "<b>Constant-Currency Variance (USD) = (Actual Local – Budget Local) × Plan Rate</b>"),
        ("p", "In words: we measure the local-currency spending variance and multiply it by the plan rate that was "
         "locked at the start of the year. A favourable local-currency variance (actual local spending is lower than "
         "budget) produces a favourable constant-currency variance, regardless of how the actual rate moved."),
        ("h2", "FX Translation Impact"),
        ("p", "The <b>FX translation impact</b> is the residual between the total USD variance and the constant-currency variance. "
         "It reflects the effect of the actual monthly average rate differing from the plan rate."),
        ("p", "<b>FX Translation Impact (USD) = Actual Local × (Actual Rate – Plan Rate)</b>"),
        ("p", "When the actual rate is higher (local currency is stronger), and the actual spending is positive, the "
         "translation impact is favourable from a USD perspective. When the actual rate is lower (local currency is weaker), "
         "the translation impact is unfavourable."),
        ("h2", "Total USD Variance"),
        ("p", "The total USD variance, as reported in the general ledger and variance reporting, is the sum of the two components:"),
        ("callout", "<b>Total USD Variance = Constant-Currency Variance + FX Translation Impact</b><br/>"
         "where positive variance is unfavourable (overspend) and negative is favourable (underspend)."),
        ("h1", "Worked Example: 2026-06 EMEA Expense Variance"),
        ("h2", "MB-UK (GBP)"),
        ("p", "In June 2026, Meridian Bank plc (MB-UK) reported a total unfavourable USD variance of +798k USD in its "
         "consolidated expenses. At first glance, this suggests the entity overspent significantly. Decomposing this variance reveals:"),
        ("table", [
            ["Metric", "MB-UK GBP", "MB-UK USD (calc)"],
            ["Budget 2026 (Jan lock date, plan rate 1.178)", "—", "—"],
            ["Actual Expenses 2026-06 (local)", "—", "—"],
            ["Actual Monthly Avg Rate 2026-06", "1.299", "1.299"],
            ["Plan Rate (Jan 2026)", "1.178", "1.178"],
            ["Actual Spend USD (local × actual rate)", "—", "FX basis"],
            ["Budget Spend USD (locked at plan rate)", "—", "FX basis"],
            ["", "", ""],
            ["Constant-Currency Variance", "+107k USD", "(Unfav. in GBP)"],
            ["FX Translation Impact", "+691k USD", "(Unfav. due to GBP strength)"],
            ["Total USD Variance", "+798k USD", "Reported"],
        ]),
        ("p", "<b>Interpretation:</b> While the total USD variance is +798k unfavourable, only +107k is due to "
         "cost-control performance. The remaining 691k is attributable to GBP strengthening from 1.178 to 1.299 "
         "(approximately 10.3% appreciation). In local GBP terms, MB-UK was approximately 6% <b>favourable</b> and "
         "is not overspending. The strong GBP is a translation headwind that cost-centre management cannot control."),
        ("h2", "MB-DE (EUR)"),
        ("p", "Similarly, MB-DE reported a total unfavourable USD variance of +228k USD. The decomposition:"),
        ("table", [
            ["Component", "Amount USD", "Rate Movement"],
            ["Constant-Currency Variance", "+49k", "Unfav. in EUR"],
            ["FX Translation Impact", "+179k", "Unfav. due to EUR strength"],
            ["Total USD Variance", "+228k", "Reported"],
        ]),
        ("p", "<b>Interpretation:</b> EUR strengthened from 0.992 to 1.091 (approximately 9.95% appreciation). "
         "Cost-centre spending variance was only +49k unfavourable; the majority of the reported USD variance is "
         "translation-driven and outside cost-centre control."),
        ("h1", "Accountability Framework"),
        ("h2", "Cost Centre Owner Accountability"),
        ("p", "Cost centre managers are <b>accountable for constant-currency variance only</b>. Their performance is "
         "measured on whether they controlled spend in local currency relative to the plan locked at the start of the year. "
         "FX translation impacts are excluded from cost-centre scorecards because FX is not operationally controllable at the "
         "local level."),
        ("h2", "Group Treasury Accountability"),
        ("p", "<b>Group Treasury is accountable for FX translation impacts.</b> Treasury hedges certain exposures to mitigate "
         "translation and transaction volatility. Hedging decisions, hedge accounting classification, and the realization of "
         "hedging gains/losses are the responsibility of Group Treasury, not individual cost centres."),
        ("h2", "Hedging Policy"),
        ("p", "Group Treasury hedges:"),
        ("bullets", [
            "Net investment exposures in major operating entities (MB-UK, MB-DE, MB-SG) using forward contracts or cross-currency swaps.",
            "Material intercompany funding flows and balance-sheet exposures in excess of designated thresholds.",
            "Transaction exposures exceeding 250k USD notional in any single currency pair.",
        ]),
        ("p", "Cost centres do <b>not</b> enter into hedges independently. All FX derivatives must be authorized by Group Treasury."),
        ("h1", "Reporting and Commentary Guidelines"),
        ("h2", "Variance Commentary Best Practices"),
        ("p", "When explaining significant variances in MD&A, close reports, or analyst communications, cost centre leaders must:"),
        ("bullets", [
            "Lead with the constant-currency variance: 'We achieved a 3% favourable variance in local currency.'",
            "Identify FX translation separately: 'However, currency headwinds added 250k USD unfavourable impact.'",
            "Quantify the local-currency percentage variance to add context that is comparable across entities.",
            "Do not attribute FX translation to local operational drivers; cite it as a macro effect.",
            "For significant breaks (variance >500k USD total), provide both the constant-currency and total figures in the same commentary.",
        ]),
        ("h2", "Reporting Hierarchy"),
        ("p", "Reporting views in the analytics layer maintain both figures:"),
        ("bullets", [
            "<b>v_opex_variance</b> includes: variance_usd (total), variance_usd_constant_ccy, and fx_translation_impact_usd.",
            "Monthly close packs and MD&A templates shall show all three metrics for any entity with a net unfavourable variance >300k USD.",
        ]),
        ("h1", "Re-Plan and Rate-Reset Rules"),
        ("h2", "Mid-Year Re-Plan"),
        ("p", "If the Group issues a revised operating plan mid-year (e.g., AOP v2 for 2026-Q3/Q4), the plan rate is "
         "<b>reset to the spot rate as of the date the re-plan is locked</b>. Variance for the locked periods (Q1–Q2) is "
         "calculated against the original plan rate. Variance for future periods is calculated against the new plan rate."),
        ("h2", "Month-End Actuals Cut-Off"),
        ("p", "Actual transactions are recorded in the period in which they occur. If an invoice is dated 2026-06-30 but "
         "received and recorded on 2026-07-05, the 2026-06 rate applies (the rate in effect when the legal obligation arose). "
         "Group Treasury may post a correction if evidence of a pricing error is provided."),
        ("h1", "Common Misinterpretations and Clarifications"),
        ("h2", "Misinterpretation 1: 'A favourable USD variance means we are performing well.'"),
        ("p", "<b>Clarification:</b> Not necessarily. A USD variance is favourable only if the constant-currency variance is "
         "favourable or if the FX translation impact is sufficiently favourable to overcome an unfavourable constant-currency "
         "variance. The constant-currency variance is the true measure of performance."),
        ("h2", "Misinterpretation 2: 'We can eliminate FX variance by operational adjustments.'"),
        ("p", "<b>Clarification:</b> FX translation variance is determined by macroeconomic factors (the movement of spot rates) "
         "outside operational control. Individual cost centres cannot 'hedge themselves' back to budget. Only Group Treasury can "
         "implement hedges. Operational adjustments (cost reductions) affect constant-currency variance but do not change the "
         "translation component of the total USD variance."),
        ("h2", "Misinterpretation 3: 'The plan rate should update if the actual rate moves significantly.'"),
        ("p", "<b>Clarification:</b> The plan rate is fixed for the fiscal year and does not adjust for market movements or "
         "management forecasts during the year. The plan rate represents a fair baseline for cost-centre accountability; if we "
         "allowed it to drift, we would lose the fixed-baseline comparison. Re-planning may occur, but it resets the rate only "
         "for future periods, not historical ones."),
        ("h1", "Governance and Escalation"),
        ("h2", "Quarterly Treasury Review"),
        ("p", "Group Treasury reviews all material FX impacts (>500k USD translation variance in any entity or line of business) "
         "in a quarterly governance meeting. Decisions regarding hedge effectiveness, rebalancing, or hedge accounting changes are "
         "documented and approved by the Chief Financial Officer."),
        ("h2", "Annual Rate Review"),
        ("p", "In Q4 of each fiscal year, Group Treasury establishes the plan rate for the following fiscal year and communicates "
         "it to all finance teams by December 15 to allow finance planning for the AOP."),
        ("h1", "References"),
        ("bullets", [
            "International Accounting Standard 21: The Effects of Changes in Foreign Exchange Rates (IASB, 2021).",
            "Meridian Bank FIN-ACC-014: Accruals and Estimates Policy (treatment of accruals with FX components).",
            "Meridian Bank FIN-IC-021: Intercompany Reconciliation Standard (treatment of cross-currency funding).",
            "dim_fx_rate table: stored in Unity Catalog with rate_type and usd_per_unit columns.",
        ]),
    ],
    "footer": "Meridian Bank - Group Finance",
    "classification": "Internal",
}
