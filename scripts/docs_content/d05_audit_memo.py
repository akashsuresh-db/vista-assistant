"""Internal Audit Memorandum - Accrual Governance and Aged Balance Remediation

This module defines the audit finding memo (ref IA-2026-11) issued after a review of
accrual governance for the period 2026-01 to 2026-06. The memo documents six accruals
that breached the 90-day policy limit set by FIN-ACC-014, with concentration in Cards
& Payments driven by Project Helios (the card platform cloud migration).

Classification: Internal - Restricted. Specifically allowed to cite findings.
"""

DOC = {
    "filename": "IA-2026-11_Internal_Audit_Memo_Accrual_Governance.docx",
    "title": "Internal Audit Memorandum",
    "subtitle": "Accrual Governance and Aged Balance Remediation - IA-2026-11",
    "meta": [
        ("Memo Reference", "IA-2026-11"),
        ("Issue Date", "2026-07-15"),
        ("From", "Head of Internal Audit"),
        ("To", "Group Financial Controller; Head of FSSC"),
        ("Classification", "Internal - Restricted"),
        ("Period Covered", "2026-01-01 to 2026-06-30"),
    ],
    "blocks": [
        ("h1", "Executive Summary"),
        ("p", "A review of accrual governance and process controls for the first half of fiscal year 2026 "
         "identified six accruals that remain open beyond the 90-day policy limit established by FIN-ACC-014 "
         "<i>Accruals and Estimates Policy</i>. As at 2026-06-30, these six breaches total USD 1,339,800. "
         "Four of these (USD 1,069,500) reside in Cards & Payments and are directly linked to Project Helios, "
         "the card processing platform migration. The underlying causes are (i) scope changes outpacing purchase-order "
         "coverage, (ii) reliance on weaker evidence bases (run-rate estimates and manual estimates) where a receipt "
         "should have been obtained, and (iii) a rate-card dispute with Helix Consulting Partners that has frozen "
         "invoice clearing for USD 1,310,500 of disputed invoices in the aged payables register."),
        ("p", "Internal Audit rates this finding as <b>Requires Improvement</b> overall, with three graded sub-findings "
         "(High, Medium, Low) detailed below. Immediate action is required to substantiate or reverse these balances "
         "by month-end close for 2026-07, and to escalate the Helix dispute to Procurement and Legal."),

        ("h1", "Aged Accrual Exception Register"),
        ("p", "The following table lists the six accruals in breach of FIN-ACC-014 as at 2026-06-30:"),
        ("table", [
            ["Accrual ID", "Cost Centre", "Vendor", "USD Amount", "Age (days)", "Evidence Basis"],
            ["ACR5183", "Cards Platform Engineering", "Helix Consulting Partners", "486,000", "153", "ESTIMATE_FROM_CONTRACT"],
            ["ACR5184", "Cards Platform Engineering", "Northwind Cloud Services", "312,500", "125", "RUN_RATE_ESTIMATE"],
            ["ACR5187", "Technology EMEA", "Kestrel Software Ltd", "208,400", "154", "ESTIMATE_FROM_CONTRACT"],
            ["ACR5185", "Cards Issuing", "Trident Payment Networks", "174,200", "124", "SERVICE_DELIVERED_NOT_BILLED"],
            ["ACR5186", "Payments Operations", "Aster Staffing Solutions", "96,800", "95", "MANUAL_ESTIMATE"],
            ["ACR5188", "Regulatory Reporting", "Sable & Roan LLP", "61,900", "96", "MANUAL_ESTIMATE"],
        ]),
        ("p", "<b>Total aged accruals in breach: USD 1,339,800</b>"),

        ("h1", "Root Cause Analysis"),
        ("h2", "Project Helios Programme Impact"),
        ("p", "Project Helios is the migration of the legacy on-premise card authorisation and clearing platform "
         "to a cloud-native architecture. The programme, led by Cards & Payments, was approved in February 2026 "
         "and is scheduled to complete in Q4 2026. Cumulative spend through June 2026 is approximately USD 4.9 million "
         "across Systems Integration (Helix), Cloud Hosting (Northwind), and Software Licences (Kestrel)."),
        ("p", "Four of the six aged accruals arise directly from Helios: ACR5183 (Helix SI estimate), ACR5184 (Northwind "
         "cloud run-rate), ACR5187 (Kestrel software), and ACR5185 (Trident payment-network fees). The concentration reflects "
         "the project's accelerating ramp-up (June 2026 monthly spend of approximately USD 2.4 million) and the inherent "
         "difficulty of forecast-accuracy when managing scope changes mid-project."),

        ("h2", "Scope Changes Outpacing PO Coverage"),
        ("p", "The primary root cause is that scope changes (migration wave acceleration, cloud-resource scaling, additional "
         "test environments) have been approved and executed by the Helios steering committee faster than corresponding purchase "
         "orders and contracts have been amended. Change control process is in place but lags execution by 4–6 weeks. As a result, "
         "accruals for partial delivery exist without an underlying PO receipt or contract amendment to reference. FIN-ACC-014 "
         "requires that accruals backed by estimates should be cleared within 90 days of first recognition; here, the PO/receipt "
         "is expected but has not yet arrived."),

        ("h2", "Weak Evidence Bases"),
        ("p", "Five of the six accruals rely on weaker evidence bases:"),
        ("bullets", [
            "ACR5183 and ACR5187 use <b>ESTIMATE_FROM_CONTRACT</b> (rate-card extrapolation without a receipt); while this is "
            "policy-compliant for initial accrual, a receipt should follow within 90 days.",
            "ACR5184 uses <b>RUN_RATE_ESTIMATE</b>, derived from prior-period cloud billing actuals and forward-looking resource "
            "projections. This is inherently less precise than a vendor invoice or consumption report.",
            "ACR5185 uses <b>SERVICE_DELIVERED_NOT_BILLED</b>, indicating the service (payment-network fees) has been incurred but "
            "no invoice has been received. Clearing requires either the invoice or a written confirmation of non-billable delivery.",
            "ACR5186 and ACR5188 use <b>MANUAL_ESTIMATE</b>, staff cost extrapolations and legal-fee allocations lacking documentary "
            "support within the detail.",
        ]),

        ("h2", "Helix Consulting Rate-Card Dispute"),
        ("p", "The largest aged payables exposure is a dispute with Helix Consulting Partners (V1001), representing 4 invoices "
         "totalling USD 1,310,500, all flagged with match status <b>PRICE_VARIANCE</b> and invoice status <b>DISPUTED</b>. Helix "
         "has billed these invoices at a blended rate higher than the rates specified in the original Master Service Agreement schedule, "
         "citing change-order delivery and scope acceleration. Procurement has contested the rate uplift, and the dispute remains unresolved. "
         "Until resolution, these invoices cannot be cleared, and the related accrual (ACR5183, USD 486,000) cannot be substantiated by "
         "a receipt. This dispute is a material control failure and requires escalation to executive sponsors."),

        ("h1", "Detailed Findings and Risk Assessment"),
        ("h2", "Finding 1: High — Accruals Exceeding Policy Age Limit (FIN-ACC-014)"),
        ("p", "<b>Condition:</b> Six accruals totalling USD 1,339,800 remained open beyond the 90-day threshold as at 2026-06-30."),
        ("p", "<b>Criteria:</b> FIN-ACC-014 <i>Accruals and Estimates Policy</i> Section 3.2 states: 'All accruals shall be substantiated "
         "or reversed within 90 calendar days of first recognition. Accruals aged 91+ days require exception approval from the Group "
         "Financial Controller and re-substantiation documentation.'"),
        ("p", "<b>Risk and Impact:</b> Uncleared accruals create overstatement risk in accounts payable and expense accruals. Extended "
         "accrual ageing indicates a process breakdown in either (i) capturing underlying receipts/invoices, or (ii) resolving disputes. "
         "The concentration in Cards & Payments (USD 1,069,500 of 1,339,800) signals a localised control failure within that locus. "
         "Audit Committee is required to be notified of any accruals exceeding the policy for more than two consecutive reporting periods."),
        ("p", "<b>Recommendation:</b> (1) By 2026-07-31, substantiate each of the six accruals with a receipt, invoice, or formal "
         "non-billable confirmation. (2) For any accrual that cannot be substantiated, reverse it to the appropriate GL account and "
         "document the reversal rationale. (3) Implement a weekly-exception report on accruals aged 75+ days, escalated to the Cards "
         "Finance Business Partner and Head of R2R. (4) By 2026-09-30, conduct control testing on the accrual process for the full "
         "year-to-date population."),

        ("h2", "Finding 2: Medium — Scope Changes Not Reflected in PO/Contract Amendments"),
        ("p", "<b>Condition:</b> The Helios change-control process has approved and released delivery against four scope changes without "
         "corresponding purchase-order amendments being executed. Lead time for PO amendments averages 4–6 weeks post-delivery."),
        ("p", "<b>Criteria:</b> Meridian Bank <i>Procurement Policy 2026</i> Section 4.1 requires that 'all service delivery and material "
         "receipt must be backed by an executed purchase order or contract amendment within 14 calendar days of delivery commencement. "
         "Delivery against pending amendments is permitted only with the approval of the Head of Procurement and documented in the change "
         "register.'"),
        ("p", "<b>Risk and Impact:</b> Scope changes without contemporaneous PO amendments create accrual-recognition risk and weaken the "
         "three-way match (PO–Receipt–Invoice). Vendors may invoice at rates not aligned with the executed contract, as evidenced by the "
         "Helix rate-card dispute. Extended delays in PO execution also delay the accrual-clearance process, pushing items beyond the 90-day limit."),
        ("p", "<b>Recommendation:</b> (1) Helios steering committee to approve a change-control process modification by 2026-08-31 such that "
         "all approved scope changes are reflected in a formal PO amendment or contract amendment within 7 calendar days of steering approval, "
         "not post-delivery. (2) Helios programme manager and Head of R2R to establish a weekly 'PO alignment' checkpoint, comparing change "
         "approvals to PO records. (3) Any delivery without a corresponding PO amendment shall be flagged and escalated to the Helios sponsor "
         "(Managing Director Cards & Payments) for decision."),

        ("h2", "Finding 3: Low — Manual Estimates and Weak Evidence Bases for Accrual Recognition"),
        ("p", "<b>Condition:</b> Two of the six accruals (ACR5186, ACR5188) use <b>MANUAL_ESTIMATE</b> as the evidence basis, and two others "
         "rely on <b>RUN_RATE_ESTIMATE</b>, all of which lack supporting documentation (timesheets, invoicing details, formal rate-setting meetings)."),
        ("p", "<b>Criteria:</b> FIN-ACC-014 Section 2 defines evidence hierarchy for accruals: (Tier 1) Receipt/Invoice, (Tier 2) Executed "
         "contract + delivery confirmation, (Tier 3) Formal estimate with vendor confirmation, (Tier 4) Rate-card extrapolation, (Tier 5) "
         "Manual estimate. Tier 4 and Tier 5 are acceptable for accrual initiation but must be upgraded to Tier 1/2 within 60 days."),
        ("p", "<b>Risk and Impact:</b> Over-reliance on Tier 4/5 evidence bases introduces measurement uncertainty and prolongs the accrual-clearance "
         "cycle. If documentation is not obtained within the 90-day window, the accrual's supporting rationale weakens, increasing the risk of "
         "financial statement misstatement or challenge by external auditors."),
        ("p", "<b>Recommendation:</b> (1) For each accrual using Tier 4 or 5 evidence, assign responsibility to the cost-centre owner to obtain "
         "Tier 1 or 2 evidence within 60 days of accrual date and upload to the accrual management system. (2) Update the accrual policy to "
         "mandate that Tier 4/5 accruals older than 60 days trigger a weekly email alert to the Finance Business Partner. (3) Conduct a "
         "training session for Cards Finance and Payments Operations staff on evidence-basis selection by 2026-09-30."),

        ("h1", "Management Action Plan"),
        ("p", "The following table outlines required actions, owners, due dates, and current status:"),
        ("table", [
            ["Action", "Owner / Role", "Due Date", "Status"],
            ["Substantiate or reverse all six aged accruals", "Head of R2R / Cards Finance Business Partner", "2026-07-31", "Not Started"],
            ["Escalate Helix rate-card dispute to Procurement and Legal", "Helios Sponsor (MD Cards & Payments) / Head of Legal", "2026-08-15", "Not Started"],
            ["Modify Helios change-control process to mandate 7-day PO alignment", "Helios Programme Manager", "2026-08-31", "In Progress"],
            ["Establish weekly accrual-ageing exception report (75+ days)", "Head of R2R", "2026-08-20", "Not Started"],
            ["Conduct control testing on YTD accrual population", "Internal Audit", "2026-09-30", "Scheduled"],
            ["Update FIN-ACC-014 to add Tier 4/5 age-60 escalation rule", "Group Financial Controller / Head of Accounting Policy", "2026-09-15", "Not Started"],
            ["Conduct accrual-evidence-basis training for Cards & Payments finance", "Head of Training / Cards Finance Business Partner", "2026-09-30", "Scheduled"],
        ]),

        ("h1", "Conclusion and Reportable Matter"),
        ("callout", "<b>Reportable Finding:</b> The six aged accruals totalling USD 1,339,800 must be substantiated or reversed in the 2026-07 "
         "close pack and formally reported to the Audit Committee. The Helix Consulting rate-card dispute (USD 1,310,500 in disputed invoices) "
         "must be escalated to the Chief Procurement Officer and General Counsel for expedited resolution. Until the underlying dispute is "
         "resolved, the related accrual (ACR5183, USD 486,000) cannot be cleared and will remain a policy exception."),

        ("h1", "Scope and Approach"),
        ("p", "This review covered all open accruals in the GL subledger as at 2026-06-30 and compared each record against the FIN-ACC-014 "
         "90-day policy threshold. Internal Audit interviewed the Cards Finance Business Partner, Head of R2R, and Helios Programme Manager "
         "to understand the root causes. Supporting documentation reviewed included: (i) accrual master file with recognition dates, (ii) "
         "Helios change register and steering committee minutes for June 2026, (iii) AP aging report and disputed-invoice register, (iv) "
         "purchase-order and contract records for each vendor. Follow-up testing is scheduled for the 2026-09 close to confirm that remediation "
         "actions have been completed and the aged accrual population has been cleared."),
    ],
    "footer": "Meridian Bank - Group Finance",
    "classification": "Internal - Restricted",
}
