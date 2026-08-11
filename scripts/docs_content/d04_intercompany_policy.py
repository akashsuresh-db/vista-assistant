"""Intercompany Transactions and Reconciliation Standard (FIN-IC-021)

This module defines the policy content for FIN-IC-021, which governs intercompany
transactions, the mandatory matching and reconciliation process, and the escalation
framework for unresolved breaks.

The key concept: intercompany must eliminate exactly on consolidation. Any break blocks
Group submission. The policy establishes materiality thresholds, mandatory timetables
tied to close process, and clear escalation rules.
"""

DOC = {
    "filename": "FIN-IC-021_Intercompany_Reconciliation_Standard.pdf",
    "title": "Intercompany Transactions and Reconciliation Standard",
    "subtitle": "FIN-IC-021 v2.4 | Group Financial Controller",
    "meta": [
        ("Policy Ref", "FIN-IC-021"),
        ("Version", "2.4"),
        ("Owner", "Group Financial Controller"),
        ("Last Updated", "2025-11-30"),
        ("Effective Date", "2026-01-01"),
    ],
    "blocks": [
        ("h1", "Policy Purpose and Scope"),
        ("p", "This policy establishes the governance framework for all intercompany transactions across Meridian Bank "
         "Group entities (MB-US, MB-UK, MB-DE, MB-SG, MB-IN). The policy ensures that:"),
        ("bullets", [
            "All intercompany transactions are authorized, recorded, and documented in accordance with transfer pricing standards.",
            "Intercompany balances between any two entities reconcile and clear within defined timelines.",
            "Breaks (discrepancies between billed and received amounts) are identified, investigated, and escalated by materiality.",
            "Unresolved breaks do not impede Group consolidation; instead, they are flagged, investigated, and reported to governance.",
        ]),
        ("p", "Intercompany transactions must eliminate on consolidation. Any unmatched balance prevents the consolidated "
         "financial statements from being submitted; therefore, the close process cannot advance until all material breaks are "
         "either cleared or escalated to the Group Financial Controller with a documented root cause."),
        ("h1", "Intercompany Transaction Types"),
        ("h2", "Authorized Transaction Categories"),
        ("p", "The following intercompany transaction types are pre-authorized and follow standing guidelines:"),
        ("table", [
            ["Transaction Type", "Originating Entity", "Rate Basis", "Timing", "Timetable"],
            ["IT Shared Services", "MB-IN / MB-US", "Cost-plus 15% markup", "Monthly invoice", "Due day 2 of month"],
            ["Finance Shared Services", "MB-IN", "Cost-plus 12% markup", "Monthly invoice", "Due day 2 of month"],
            ["Treasury Funding", "MB-US", "SOFR + 120 bps spread", "As needed, daily settlement", "Due 1 day after funding"],
            ["Brand & Marketing Recharge", "MB-US", "Cost-plus 20% markup", "Quarterly invoice", "Due 5 days post-quarter-end"],
            ["Risk & Compliance Support", "MB-US", "Cost-plus 10% markup", "Quarterly invoice", "Due 5 days post-quarter-end"],
        ]),
        ("p", "All intercompany rates and markups are documented in the formal Intercompany Agreement maintained by "
         "Group Treasury (for funding) and Group Finance (for service recharges). Changes to rates or markup percentages "
         "require amendment to the agreement and approval by the CFO and General Counsel."),
        ("h2", "Transfer Pricing Basis"),
        ("p", "<b>Shared Services (IT, Finance, Risk & Compliance):</b> Charged at cost-plus basis, where cost is the "
         "fully-burdened cost of personnel and allocated overhead plus a pre-agreed markup. Markups are set annually and "
         "align with OECD Transfer Pricing Guidelines for management services."),
        ("p", "<b>Treasury Funding:</b> Charged at an arm's-length spread over the funding source rate (typically SOFR). "
         "The spread (120 basis points) is established annually by Group Treasury and reviewed against market benchmarks."),
        ("p", "<b>Brand & Marketing Recharge:</b> Charged at cost-plus 20% and covers corporate brand management, advertising, "
         "and digital marketing services provided by the North American entity to other regions."),
        ("h1", "Mandatory Matching and Reconciliation Timeline"),
        ("h2", "Intercompany Close Process Timetable"),
        ("p", "All intercompany transactions must be matched and cleared by close business day 3 of the month following the "
         "reporting period. The close calendar targets Group consolidation submission by business day 8."),
        ("table", [
            ["Close Day", "Task", "Owner", "Status", "Blocker if Late"],
            ["Day 1", "GL close and bank reconciliation", "Entity Finance", "GL locked", "No"],
            ["Day 2", "Intercompany billing submission", "Billed entity (originator)", "Invoices due", "Yes"],
            ["Day 3", "Intercompany matching and reconciliation", "Shared Services / Treasury", "All breaks identified", "Yes"],
            ["Day 4–5", "Break investigation and remediation", "Entity Financial Controllers", "Root cause documented", "Yes"],
            ["Day 6", "Consolidation builder runs", "Group Finance", "IC cleared or escalated", "Yes"],
            ["Day 8", "Group consolidation submission", "CFO", "Final submission", "—"],
        ]),
        ("h2", "Matching Process"),
        ("p", "Intercompany matching is performed in the <b>fact_intercompany</b> table in Unity Catalog (your_catalog.your_schema). "
         "Each intercompany transaction is recorded with:"),
        ("bullets", [
            "<b>biller_entity:</b> the entity that originated the invoice (e.g., MB-IN for an IT Shared Services bill).",
            "<b>receiver_entity:</b> the entity that received the bill (e.g., MB-UK).",
            "<b>transaction_type:</b> IT_SHARED_SERVICES, FINANCE_SHARED_SERVICES, TREASURY_FUNDING, BRAND_MARKETING_RECHARGE, or RISK_COMPLIANCE_SUPPORT.",
            "<b>billed_amount_usd:</b> the amount invoiced by the biller.",
            "<b>received_amount_usd:</b> the amount recorded in the receiver's books (may differ due to timing or FX).",
            "<b>transaction_date:</b> the date the invoice was issued.",
            "<b>status:</b> MATCHED, UNDER_INVESTIGATION, or UNRESOLVED_BREAK.",
            "<b>root_cause:</b> description of the discrepancy (if status is not MATCHED).",
        ]),
        ("p", "Transactions with <b>billed_amount_usd = received_amount_usd</b> are marked MATCHED. Any difference triggers "
         "a break investigation."),
        ("h1", "Break Materiality and Escalation Framework"),
        ("h2", "Materiality Thresholds"),
        ("p", "Intercompany breaks are classified and escalated according to the following threshold matrix:"),
        ("table", [
            ["Break Amount (USD)", "Classification", "Auto-Treatment", "Timetable", "Approver"],
            ["< 1,000", "Immaterial", "Auto-write-off", "Automatic", "System"],
            ["1,000 – 250,000", "Material", "Investigate & clear", "Same close cycle", "Receiving Entity CFO"],
            [">250,000", "Reportable Break", "Escalate with doc", "Within 1 close cycle", "Group Financial Controller + Audit Committee"],
        ]),
        ("h2", "Sub-1,000 USD Breaks"),
        ("p", "Differences under 1,000 USD are considered immaterial for intercompany purposes. These breaks are automatically "
         "written off in the consolidation elimination entry without investigation. No root-cause analysis is required. A monthly "
         "report of auto-written-off breaks is filed with Group Finance for archival."),
        ("h2", "1,000 – 250,000 USD Breaks"),
        ("p", "Breaks in this range must be investigated and cleared within the same close cycle. The Receiving Entity Financial "
         "Controller is accountable for identifying the root cause. Common causes include:"),
        ("bullets", [
            "<b>Timing/cut-off:</b> One side books in the current period; the other side books in the following period.",
            "<b>Rate-basis disagreement:</b> On Treasury Funding, the two entities calculated the spread differently due to "
            "different funding rates or timing of settlement.",
            "<b>Recharge approval:</b> The biller invoiced before the receiver approved the recharge, or approval was conditional.",
            "<b>FX translation:</b> The biller invoiced in one currency; the receiver recorded it in another, with a timing "
            "difference in the FX rate used.",
        ]),
        ("p", "Once the root cause is identified, the Receiving Entity Financial Controller submits a correcting entry in the "
         "earlier open accounting period (if available) or books it in the current period with full documentation. The break status "
         "is updated to MATCHED and the root cause is recorded in the register."),
        ("h2", "Greater than 250,000 USD Breaks"),
        ("callout", "<b>REPORTABLE BREAK RULE:</b> Any intercompany break exceeding 250,000 USD is a <i>reportable break</i> "
         "requiring immediate escalation. Named owners at <b>BOTH</b> the biller and receiver entities must jointly investigate, "
         "agree on the root cause, and document the correcting action. The break cannot remain unresolved for more than one "
         "consecutive accounting period. If unresolved, it escalates to the Group Financial Controller and is reported to the "
         "Audit Committee in the next governance meeting. The Group consolidation cannot proceed until the reportable break is "
         "either cleared or a documented remediation plan with a resolution date is submitted."),
        ("h1", "Multi-Period Break Escalation Rule"),
        ("h2", "Escalation Timeline"),
        ("p", "Any break (regardless of amount) that remains unresolved for more than one consecutive accounting period "
         "automatically escalates. Example: a break identified in the 2026-06 close that is not cleared in the 2026-07 close "
         "is escalated."),
        ("p", "<b>Escalation triggers:</b>"),
        ("bullets", [
            "Status remains UNDER_INVESTIGATION or UNRESOLVED_BREAK in two or more consecutive months.",
            "Biller and Receiver entities have not agreed on root cause after 15 calendar days of the close cycle.",
            "No correcting entry has been booked and approved after 20 calendar days of the close cycle.",
        ]),
        ("h2", "Escalation Process"),
        ("p", "Once escalation is triggered:"),
        ("bullets", [
            "Group Financial Controller is notified within 1 business day of the escalation threshold being met.",
            "Both entity Financial Controllers meet with the Group Financial Controller to agree on root cause within 2 business days.",
            "A remediation plan with a specific resolution date is submitted to the Group Financial Controller within 3 business days.",
            "The remediation plan is reported to the Audit Committee in the next scheduled governance meeting (typically within 2 weeks).",
            "The Group consolidation may proceed with the unresolved break flagged as 'Escalated – Pending Resolution', but no "
            "financial statements may be issued to external stakeholders until the break is cleared or a signed waiver is obtained from "
            "the CFO and the Audit Committee Chair.",
        ]),
        ("h1", "Common Root Causes and Remediation Playbook"),
        ("h2", "Timing and Cut-Off Differences"),
        ("p", "<b>Symptom:</b> Billed amount matches received amount, but in different months. Example: MB-IN invoices MB-UK "
         "on 2026-06-29 for June services; MB-UK records it on 2026-07-02."),
        ("p", "<b>Remediation:</b> No correcting entry required if the amount is not material (< 1,000 USD) and is expected to "
         "clear in the following month. If timing differences are frequent or large (> 1,000 USD), adjust the billing date "
         "to occur 2 business days before month-end to allow recording in the same period."),
        ("h2", "Rate-Basis Disagreement on Treasury Funding"),
        ("p", "<b>Symptom:</b> MB-US funds MB-SG 1,000,000 USD at SOFR + 120 bps. MB-US calculates interest at SOFR = 4.5%, "
         "funding rate = 5.7%, sends invoice for 57,000. MB-SG used SOFR = 4.2%, recorded 42,000 in expense. Discrepancy = 15,000 USD."),
        ("p", "<b>Root Cause:</b> Rate cut occurred between the funding date and invoice date. MB-SG used the rate at the time of "
         "funding; MB-US used the rate at invoice. The Intercompany Agreement specifies which rate should apply."),
        ("p", "<b>Remediation:</b> Agree on a single SOFR rate to apply (typically the rate on the funding date per the agreement). "
         "Whoever booked the incorrect rate issues a correcting entry in the current period. Book in GL account 590100 (Intercompany "
         "Service Recharge), sub-account for FX/Rate Adjustment."),
        ("h2", "Missing or Disputed Recharge Approval"),
        ("p", "<b>Symptom:</b> MB-US invoices MB-DE 250,000 USD for Brand & Marketing for 2026-Q2. MB-DE received the invoice on "
         "2026-07-03 but had not pre-approved the quarterly recharge. MB-DE's Finance team disputes the amount, claiming it was too high."),
        ("p", "<b>Root Cause:</b> Recharge approval process was not completed before billing. Cost centre ownership or scope may be unclear."),
        ("p", "<b>Remediation:</b> Both entities agree on the scope of Brand & Marketing services covered in the recharge. MB-US and "
         "MB-DE jointly review the invoice detail (headcount, project allocation). If the invoice is correct, MB-DE records it. If "
         "there is a legitimate dispute over allocation, issue a debit memo for the disputed portion and adjust for the next quarter. "
         "Both parties sign off. Implement a pre-billing approval gate for future quarters: recharges must be pre-approved by the "
         "receiving cost centre by the 2nd-to-last day of the quarter."),
        ("h2", "FX Translation on Cross-Currency Intercompany Legs"),
        ("p", "<b>Symptom:</b> MB-US bills MB-UK in GBP. On 2026-06-29, the rate is 1.25; MB-UK records 800,000 GBP = 1,000,000 USD. "
         "MB-US receives the GBP on 2026-07-02 when the rate is 1.28; MB-US records 800,000 GBP = 1,024,000 USD. Discrepancy = 24,000 USD."),
        ("p", "<b>Root Cause:</b> FX rate movement between the two booking dates. The transaction is recorded at different rates by "
         "each entity due to timing and the spot rate on the respective recording dates."),
        ("p", "<b>Remediation:</b> The Intercompany Agreement specifies the rate at which cross-currency transactions settle. Typically, "
         "the rate on the invoice date is used. MB-US revalues its received amount to the invoice date rate and books a small FX "
         "translation gain/loss in GL account 590100 (Intercompany FX Adjustment sub-account). Both entities agree on the rate and "
         "amounts are reconciled."),
        ("h1", "Intercompany Register and Data Governance"),
        ("h2", "fact_intercompany Table Structure"),
        ("p", "All intercompany transactions are recorded in <b>fact_intercompany</b> in Unity Catalog (your_catalog.your_schema). "
         "This table is the system-of-record for intercompany reconciliation:"),
        ("bullets", [
            "<b>biller_entity_code:</b> e.g., MB-IN, MB-US.",
            "<b>receiver_entity_code:</b> e.g., MB-UK.",
            "<b>transaction_type:</b> enumerated list (IT_SHARED_SERVICES, etc.).",
            "<b>billed_amount_usd:</b> the invoiced amount in USD.",
            "<b>received_amount_usd:</b> the amount recorded in the receiver's GL in USD.",
            "<b>transaction_date:</b> the invoice or transaction date.",
            "<b>status:</b> MATCHED, UNDER_INVESTIGATION, or UNRESOLVED_BREAK.",
            "<b>root_cause:</b> text field; populated only if status is not MATCHED.",
            "<b>correcting_entry_booked_date:</b> the date the correcting entry was posted (if applicable).",
            "<b>resolved_date:</b> the date the break was cleared or escalated.",
        ]),
        ("h2", "Monthly Intercompany Report"),
        ("p", "Group Finance publishes a monthly Intercompany Reconciliation Report by close day 5. The report includes:"),
        ("bullets", [
            "Summary of total billed, total received, and net break amount.",
            "Itemized list of all breaks by amount, entity pair, and status.",
            "Root cause analysis for breaks in the 1,000–250,000 USD band.",
            "Escalation flags for any break exceeding 250,000 USD or unresolved for multiple periods.",
            "Recommendations for process improvements.",
        ]),
        ("h1", "Common Misinterpretations and Best Practices"),
        ("h2", "Misinterpretation 1: 'Immaterial breaks can be left unmatched indefinitely.'"),
        ("p", "<b>Clarification:</b> Breaks under 1,000 USD are auto-written-off only within the same close cycle. If a break "
         "under 1,000 USD persists across multiple months, it should be investigated to rule out a systematic process error or "
         "fraudulent activity."),
        ("h2", "Misinterpretation 2: 'We can adjust amounts to make the intercompany break go away.'"),
        ("p", "<b>Clarification:</b> Intercompany amounts must reflect the actual invoice and actual receipt. Arbitrary adjustments "
         "violate transfer pricing standards and accounting controls. If an invoice amount is genuinely wrong, a debit memo or credit "
         "memo must be issued with documented justification (e.g., service not delivered, rate-card error)."),
        ("h2", "Misinterpretation 3: 'Reportable breaks (>250k) can be resolved by the Receiving Entity Finance team alone.'"),
        ("p", "<b>Clarification:</b> Reportable breaks require <b>joint agreement</b> between the Biller and Receiver entity Financial "
         "Controllers. Both entities must sign off on the root cause and correcting entry. The Group Financial Controller is the tie-breaker "
         "if the two entities cannot agree."),
        ("h1", "Governance and Approvals"),
        ("h2", "Pre-Approved Intercompany Rates"),
        ("p", "All intercompany rates (markups, spreads) are approved annually by the CFO and documented in the Intercompany Agreement. "
         "Any deviation requires a formal amendment and CFO sign-off before the transaction is recorded."),
        ("h2", "Audit Committee Reporting"),
        ("p", "All reportable breaks (>250,000 USD) are reported to the Audit Committee within the next scheduled meeting. Multi-period "
         "unresolved breaks are flagged to the Audit Committee with a remediation plan and target resolution date."),
        ("h1", "References and Related Policies"),
        ("bullets", [
            "FIN-FX-007: Foreign Currency Translation and Constant-Currency Reporting Policy.",
            "FIN-ACC-014: Accruals and Estimates Policy (accruals on intercompany service recharges).",
            "OECD Transfer Pricing Guidelines (2022).",
            "Meridian Bank Intercompany Agreement (document maintained by Group Treasury and Legal).",
            "fact_intercompany table: your_catalog.your_schema.",
        ]),
    ],
    "footer": "Meridian Bank - Group Finance",
    "classification": "Internal",
}
