"""Month-End Variance Commentary Pack - June 2026

This module defines the working variance commentary document that the FSSC (Finance Shared
Services Centre) analysts produce for each month. It includes commentary on material variances
(threshold: >USD 250k or 5% of budget, whichever is lower), organized by cost centre with
driver analysis, one-off vs run-rate breakdown, accountability, and corrective actions.

The pack emphasizes constant-currency accountability and FX translation separation.
Format: PDF with tables, bullets, h2 sections, callouts, and sign-off.
"""

DOC = {
    "filename": "FSSC_Variance_Commentary_Pack_2026-06.pdf",
    "title": "Month-End Variance Commentary Pack - June 2026",
    "subtitle": "Cost centre commentary submitted to Group FP&A",
    "meta": [
        ("Period", "2026-06 (month ended 30 June 2026)"),
        ("Prepared by", "Record to Report, FSSC Chennai"),
        ("Status", "Signed off business day 6"),
        ("Owner", "Group Financial Planning & Analysis"),
    ],
    "blocks": [
        ("h1", "How to Read This Pack"),
        ("p", "This variance commentary addresses all cost centres with significant variances in June 2026. "
         "Variance trigger threshold: >USD 250,000 OR >5% of budget, whichever is lower. "
         "All commentary is grounded in actual-to-budget comparison on a <b>constant-currency basis</b> "
         "(i.e. local-currency variance converted at the plan rate locked in January 2026)."),
        ("p", "For each flagged cost centre, commentary includes:"),
        ("bullets", [
            "<b>Driver:</b> the specific GL account or headcount movement causing the variance;",
            "<b>One-off vs run-rate:</b> whether the variance is temporary (project ramp, bonus accrual) or structural;",
            "<b>Owner and accountability:</b> which manager and which GL owner;",
            "<b>Corrective action and timeline:</b> what is being done and when it will be resolved.",
            "FX translation impact is called out separately; FX variance is owned by Group Treasury, not the cost centre.",
        ]),
        ("h1", "June 2026 Commentary Summary - By Line of Business"),
        ("table", [
            ["Line of Business", "Actual (USD m)", "Budget (USD m)", "Variance (USD m)", "Commentary Status"],
            ["Cards & Payments", "28.95", "26.22", "+2.72 (Unfav.)", "Material Helios ramp"],
            ["Corporate Banking", "12.84", "12.50", "+0.34 (Unfav.)", "Minor; mostly FX"],
            ["Technology", "8.76", "8.44", "+0.32 (Unfav.)", "Licensing & FX"],
            ["Operations", "6.18", "5.88", "+0.30 (Unfav.)", "Staffing and materials"],
            ["Wealth Management", "5.42", "5.20", "+0.22 (Unfav.)", "Small; FX-driven"],
            ["Retail Banking", "4.65", "4.45", "+0.20 (Unfav.)", "Minor; no action"],
            ["Treasury", "2.34", "2.26", "+0.08 (Unfav.)", "Small variance"],
            ["Risk & Compliance", "1.92", "1.88", "+0.04 (Fav.)", "Underspend"],
        ]),
        ("h1", "Cost Centre Commentary - Material Variances"),
        ("h2", "Cards Platform Engineering (GL 530100 - Professional Fees - Consulting)"),
        ("p", "<b>Actual:</b> USD 2.145m | <b>Budget:</b> USD 1.166m | <b>Variance:</b> +USD 979k (84% unfavourable)"),
        ("p", "<b>Driver:</b> Project Helios system integration and consulting from Helix Consulting Partners. "
         "Helios was approved in February 2026, post-AOP lock; costs were not in the baseline cost centre budget. "
         "June spend reflects detailed design and infrastructure planning phases of the platform migration."),
        ("bullets", [
            "Helix Consulting billed USD 2.1m YTD through June (of USD 8.5m FY2026 approved);",
            "Billing rate reflects blended delivery model (offshore + onshore); some disputed invoices on rate variance;",
            "Programme ramp: March +USD 185k, April +USD 245k, May +USD 549k, June +USD 979k cumulative.",
        ]),
        ("p", "<b>One-off vs run-rate:</b> 100% attributable to Project Helios. This is a multi-quarter, programme-based expense. "
         "Not expected to reverse until Helios deployment completes (target December 2026). Will re-baseline in H2 re-forecast."),
        ("p", "<b>Accountability:</b> Owner: Head of Cards Platform Engineering. Approver: Chief Technology Officer. "
         "Programme steering committee reviews weekly; cost and schedule tracked against approved Helios budget."),
        ("p", "<b>Corrective action:</b> None required operationally; this is planned spend. "
         "Procurement & Legal team resolving rate-card dispute on 4 invoices (USD 1.31m). "
         "Target resolution: 2026-08 or 2026-09. Estimate: neutral to 10% credit negotiation."),
        ("h2", "Cards Platform Engineering (GL 520200 - Cloud Hosting & Compute)"),
        ("p", "<b>Actual:</b> USD 1.028m | <b>Budget:</b> USD 0.420m | <b>Variance:</b> +USD 608k (145% unfavourable)"),
        ("p", "<b>Driver:</b> Northwind Cloud Services hosting and compute for Helios platform development environment and pre-production. "
         "Environment stood up in April 2026; ramping through June. Bill includes dev, staging, and performance-testing environments."),
        ("bullets", [
            "Northwind contract: USD 185k/month steady-state (post-migration); currently ramping dev/test at USD 250k-300k/month;",
            "Includes elastic compute for data migration activities; expected to reduce as migration testing is completed;",
            "Run-rate will stabilize at production levels in Q4 2026.",
        ]),
        ("p", "<b>One-off vs run-rate:</b> 70% programme ramp (temporary), 30% ongoing production compute (run-rate post-Go-Live). "
         "June ramp will decelerate in Q3 as testing completes."),
        ("p", "<b>Accountability:</b> Owner: Cards Platform Engineering. Approver: CTO. "
         "Infrastructure cost tracked monthly against Helios project budget."),
        ("p", "<b>Corrective action:</b> Optimize dev/test environment size in Q3. Standdown non-production instances post-migration UAT. "
         "Target: reduce July cloud spend by 15-20%."),
        ("h2", "Cards Platform Engineering (GL 520100 - Software Licences)"),
        ("p", "<b>Actual:</b> USD 0.803m | <b>Budget:</b> USD 0.442m | <b>Variance:</b> +USD 361k (82% unfavourable)"),
        ("p", "<b>Driver:</b> Kestrel Software Ltd licensing for platform tools (API gateway, monitoring, data integration). "
         "Helios requires modern SaaS licensing model rather than legacy perpetual licences. Vendor: Kestrel Software (V1003)."),
        ("bullets", [
            "Kestrel contract: USD 45k/month platform subscription + USD 15k/month per-transaction licensing (post-Go-Live);",
            "Currently paying during test/dev: USD 60k/month baseline + overages; will normalize post-deployment;",
            "Represents 3 new software vendors (Kestrel, two others) replacing legacy system.",
        ]),
        ("p", "<b>One-off vs run-rate:</b> 40% programme cost (dev/test overages), 60% run-rate (post-Go-Live subscription). "
         "Subscription portion will continue; dev overages will end."),
        ("p", "<b>Accountability:</b> Owner: Cards Platform Engineering. Approver: CTO. "
         "Vendor management: Procurement and Technology teams."),
        ("p", "<b>Corrective action:</b> Procurement negotiating per-transaction cap with Kestrel to control overages post-migration. "
         "Expect 10-15% reduction post-Go-Live."),
        ("h2", "Cards Issuing (GL 530100 - Professional Fees - Consulting)"),
        ("p", "<b>Actual:</b> USD 0.521m | <b>Budget:</b> USD 0.280m | <b>Variance:</b> +USD 241k (86% unfavourable)"),
        ("p", "<b>Driver:</b> Consulting from Helix Consulting Partners for card-issuing platform integration into Helios. "
         "Includes card data migration, issuing workflow redesign, and PCI compliance re-certification."),
        ("bullets", [
            "Helix sub-project: ~20% of overall Helios cost; embedded in wider platform programme;",
            "June work focused on cardholder data mapping and workflow re-documentation.",
        ]),
        ("p", "<b>One-off vs run-rate:</b> 100% programme-driven; will reverse post-Helios Go-Live. Re-baseline in H2."),
        ("p", "<b>Accountability:</b> Owner: Head of Cards Issuing. Approver: Chief Cards Officer."),
        ("p", "<b>Corrective action:</b> Part of overall Helios programme governance; no additional cost control actions."),
        ("h2", "Cards Issuing (GL 520100 - Software Licences)"),
        ("p", "<b>Actual:</b> USD 0.301m | <b>Budget:</b> USD 0.180m | <b>Variance:</b> +USD 121k (67% unfavourable)"),
        ("p", "<b>Driver:</b> Card-issuing platform licensing (Trident Payment Networks card scheme licences, PCI compliance tools). "
         "Helios integration requires updated licence tier and new compliance tools."),
        ("p", "<b>One-off vs run-rate:</b> 50% programme, 50% run-rate. New compliance licensing will continue post-Go-Live."),
        ("p", "<b>Corrective action:</b> Procurement bundling Trident licensing with wider Helios vendor stack for volume discount. "
         "Expect 5-10% reduction in Q3."),
        ("h2", "Payments Operations (GL 510400 - Contractor & Temp Labour)"),
        ("p", "<b>Actual:</b> USD 0.445m | <b>Budget:</b> USD 0.334m | <b>Variance:</b> +USD 111k (33% unfavourable)"),
        ("p", "<b>Driver:</b> Contractor headcount ramp via Aster Staffing Solutions. Operations team expanded to support Helios testing, "
         "migration communications, and vendor management. Ramp: January 35 FTE → June 95 FTE (60 additional contractors)."),
        ("bullets", [
            "Blended contractor rate: USD 75k-85k per FTE annually; placement fee 15-18% of first-year cost;",
            "Ramping in sync with Helios phases; planned reduction to baseline 25 FTE in Q1 2027.",
        ]),
        ("p", "<b>One-off vs run-rate:</b> 100% temporary programme ramp; reversal scheduled Q1 2027."),
        ("p", "<b>Accountability:</b> Owner: VP Payments Operations. Approver: COO."),
        ("p", "<b>Corrective action:</b> Review contractor utilization weekly against Helios schedule. Standdown underutilized resources early. "
         "Current forecast: revert to baseline by 2027-03-31."),
        ("h2", "Technology EMEA (GL 520100 - Software Licences & FX)"),
        ("p", "<b>Actual:</b> USD 0.625m | <b>Budget:</b> USD 0.498m | <b>Variance:</b> +USD 127k (25% unfavourable)"),
        ("p", "<b>Constant-currency variance:</b> +USD 28k | <b>FX translation impact:</b> +USD 99k (FX-driven, not operational)"),
        ("p", "<b>Driver:</b> EUR-based licensing costs (Kestrel Software, other EMEA tools). "
         "Budgeted at EUR plan rate 0.992 (Jan 2026); actual June rate 1.091. "
         "Constant-currency (local EUR overspend) only +USD 28k; 78% of reported variance is FX translation."),
        ("p", "<b>One-off vs run-rate:</b> Licences are run-rate; FX translation is macro-driven and not operationally controllable."),
        ("p", "<b>Accountability:</b> Constant-currency overspend owned by Technology EMEA manager. "
         "FX translation owned by Group Treasury (hedging strategy)."),
        ("p", "<b>Corrective action:</b> (1) Local: minor licence consolidation in Q3; expect <5% local-currency reduction. "
         "(2) Group: Treasury to review EUR hedging effectiveness and decide whether to increase hedge ratio. "
         "This is a macro issue, not a cost centre issue."),
        ("h2", "MB-UK Retail Banking - Regional Overhead (GL 510100 - Salaries & Wages)"),
        ("p", "<b>Actual:</b> USD 2.134m | <b>Budget:</b> USD 1.910m | <b>Variance:</b> +USD 224k (12% unfavourable)"),
        ("p", "<b>Constant-currency variance:</b> +USD 32k | <b>FX translation impact:</b> +USD 192k (FX-driven)"),
        ("p", "<b>Driver:</b> This variance is 86% FX translation (GBP strengthened from 1.178 to 1.299). "
         "Constant-currency: only +USD 32k, or <2% local overspend, largely due to timing of April pay cycle bonus accrual."),
        ("p", "<b>One-off vs run-rate:</b> Bonus accrual is timing; will reverse in July payout. Underlying pay run is controlled."),
        ("p", "<b>Accountability:</b> Constant-currency overspend: negligible and timing-related. "
         "FX translation: owned by Group Treasury."),
        ("p", "<b>Corrective action:</b> None at cost centre level. This cost centre is <b>operating under budget in GBP terms (6% favourable)</b>. "
         "No local spending action is warranted. FX is a Group matter."),
        ("callout", "<b>Key Point:</b> MB-UK reports a USD 224k unfavourable variance, but only USD 32k is constant-currency overspend. "
         "USD 192k is pure GBP translation impact. In GBP terms, this cost centre is approximately 6% FAVOURABLE. "
         "The unfavourable USD variance reflects currency strength, not local operational performance. Cost centre manager has no action."),
        ("h2", "Entity-level FX summary (all cost centres, 2026-06)"),
        ("p", "The cost centre commentary above covers individual GL lines. Rolled up to entity level for the "
              "full expense base, the same pattern holds and is the figure Group FP&amp;A reports:"),
        ("table", [
            ["Entity", "Currency", "Total USD variance", "Constant-currency variance", "FX translation impact",
             "Local-currency position"],
            ["MB-UK", "GBP", "+USD 798k unfavourable", "+USD 107k", "USD 691k (87% of variance)",
             "approx. 6% FAVOURABLE in GBP"],
            ["MB-DE", "EUR", "+USD 228k unfavourable", "+USD 49k", "USD 179k (78% of variance)",
             "approx. 6% FAVOURABLE in EUR"],
        ]),
        ("callout", "<b>Entity conclusion:</b> Of MB-UK's +USD 798k unfavourable expense variance for 2026-06, only "
                    "+USD 107k is genuine local overspend; the remaining USD 691k is GBP translation "
                    "(plan rate 1.178 versus actual monthly average 1.299) and is owned by Group Treasury, not by "
                    "MB-UK cost centre managers. MB-DE follows the same pattern (+USD 228k reported, +USD 49k "
                    "constant-currency, USD 179k translation). Neither entity is overspending in local currency."),
        ("h1", "Control Matters and Exceptions"),
        ("h2", "Aged Accruals - Policy Breach FIN-ACC-014"),
        ("p", "Internal Audit memo IA-2026-11 (dated 2026-07-05) flags 6 accruals older than 90 days at 2026-06-30, "
         "totalling USD 1,339,800. Policy FIN-ACC-014 requires accruals to be resolved or re-validated within 90 days."),
        ("table", [
            ["Accrual ID", "Cost Centre / Vendor", "Amount (USD)", "Age (days)", "Status / Issue", "Resolution Plan"],
            ["ACR5183", "Cards Platform Eng / Helix", "486,000", "153", "ESTIMATE_FROM_CONTRACT", "Resolve in 2026-07 invoice batch"],
            ["ACR5184", "Cards Platform Eng / Northwind", "312,500", "125", "RUN_RATE_ESTIMATE", "Invoice expected 2026-07-15"],
            ["ACR5187", "Technology EMEA / Kestrel", "208,400", "154", "ESTIMATE_FROM_CONTRACT", "Invoice expected 2026-07-31"],
            ["ACR5185", "Cards Issuing / Trident", "174,200", "124", "SERVICE_DELIVERED_NOT_BILLED", "Vendor follow-up in progress"],
            ["ACR5186", "Payments Ops / Aster Staffing", "96,800", "95", "MANUAL_ESTIMATE", "Reconcile headcount sheet 2026-07"],
            ["ACR5188", "Regulatory Reporting / Sable & Roan", "61,900", "96", "MANUAL_ESTIMATE", "Outside legal invoicing 2026-08"],
        ]),
        ("p", "<b>Accountability:</b> Each cost centre owner is responsible for their accrual. "
         "Group Controller's office (CFO direct report) enforcing resolution by 2026-07-31 close."),
        ("p", "<b>Action:</b> Daily follow-up with vendors starting 2026-07-08. Escalation to Procurement and Legal for Helix, Trident, Sable & Roan. "
         "Remediation target: 100% of breached accruals resolved or re-validated in 2026-07 close."),
        ("h2", "Intercompany Break - MB-UK to MB-SG Treasury Funding"),
        ("p", "Outstanding break: MB-UK billed MB-SG USD 2,940,000 for intercompany funding; MB-SG recorded USD 2,458,000. "
         "Difference: USD 482,000. Status: UNRESOLVED_BREAK. "
         "Present in both 2026-05 and 2026-06 (crossed escalation rule: >1 period unresolved). "
         "Reference: FIN-IC-021 (Intercompany Reconciliation Standard)."),
        ("p", "<b>Root cause:</b> (1) Funding leg booked by MB-SG in the following period; (2) rate-basis disagreement on intercompany funding spread. "
         "MB-SG Treasury team delayed recording; reconciliation documentation incomplete."),
        ("p", "<b>Accountability:</b> MB-UK Treasurer and MB-SG Treasurer are jointly accountable. "
         "Group Treasury Secretary (reporting to Group CFO) escalation owner."),
        ("p", "<b>Action:</b> (1) MB-SG to provide supporting documentation by 2026-07-15. (2) Both entities to reconcile funding spread calculation. "
         "(3) Target close: 2026-08-15 (before Q3 consolidation on 2026-09-05). "
         "(4) If unresolved after 2026-08-15, escalate to Audit Committee."),
        ("h1", "Close Performance - SLA Metrics"),
        ("p", "Close calendar target: Group consolidation submission by business day 8 (2026-06-30 close date was Tuesday; "
         "consolidation due by Wednesday 2026-07-08)."),
        ("table", [
            ["Task / Entity", "SLA Day", "Actual Day", "Status", "Days Late", "Owning Team"],
            ["Accrual calculation & upload / MB-US", "Day 2", "Day 5", "Breached", "3", "Record to Report"],
            ["Intercompany billing & matching / MB-UK", "Day 3", "Day 6", "Breached", "3", "Record to Report"],
            ["Sub-ledger cut-off - AP / MB-SG", "Day 1", "Day 3", "Breached", "2", "Procure to Pay"],
        ]),
        ("p", "<b>Root causes:</b> (1) MB-US accrual calculation delayed pending Helix invoice; analyst worked late on day 4-5. "
         "(2) MB-UK intercompany delay due to break (see above); matching could not proceed until reconciliation. "
         "(3) MB-SG AP cut-off dependent on late vendor deliveries for June invoicing."),
        ("p", "<b>Accountability:</b> Record to Report team (MB-US, MB-UK) and Procure to Pay team (MB-SG). "
         "Escalation: VP of Finance Operations (R2R) and VP of Procure to Pay."),
        ("p", "<b>Mitigations for Q3 close:</b> (1) Mandate accrual documentation submission by close-1 (day 0) for standard items. "
         "(2) Establish dedicated intercompany break task force; daily stand-up day 1-3 of close. "
         "(3) Implement vendor invoice receipt SLA with 2-day buffer before month-end."),
        ("h1", "Sign-Off"),
        ("table", [
            ["Role", "Name", "Date", "Day"],
            ["Prepared by", "Senior Analyst, FSSC Chennai", "2026-07-05", "Business Day 5"],
            ["Reviewed by", "Manager, Record to Report", "2026-07-05", "Business Day 5"],
            ["Approved by", "VP, Group Financial Planning & Analysis", "2026-07-06", "Business Day 6"],
        ]),
    ],
    "footer": "Meridian Bank - Group Finance",
    "classification": "Internal - Restricted",
}
