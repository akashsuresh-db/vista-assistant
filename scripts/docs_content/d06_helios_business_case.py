"""Project Helios - Card Processing Platform Migration: Business Case and Cost Approval

This module defines the business case and cost-approval document (ref PROJ-HELIOS-BC-v2)
for the card processing platform migration project. Approved February 2026 by the Group
Investment Committee, after the AOP_2026_v3 annual plan was locked (January 2026).

This document explains the cost drivers and phasing behind the Cards & Payments unfavourable
variance observed in 2026-06 P&L. It is the canonical reference for project scope, budget
authority, and governance.

Classification: Internal.
"""

DOC = {
    "filename": "PROJ-HELIOS_Business_Case_and_Cost_Approval.pdf",
    "title": "Project Helios - Card Processing Platform Migration",
    "subtitle": "Business Case and Cost Approval | PROJ-HELIOS-BC-v2 | Approved 2026-02-20",
    "meta": [
        ("Project Reference", "PROJ-HELIOS-BC-v2"),
        ("Approval Date", "2026-02-20"),
        ("Approved By", "Group Investment Committee"),
        ("Project Sponsor", "Managing Director Cards & Payments"),
        ("Finance Lead", "Cards Finance Business Partner"),
        ("Classification", "Internal"),
        ("Project Timeline", "2026-03 to 2026-Q4"),
    ],
    "blocks": [
        ("h1", "Background and Strategic Context"),
        ("p", "Meridian Bank's card processing and authorisation platform is a legacy, on-premise deployment based on vendors no longer "
         "providing first-line support. Current architecture is end-of-life as of 2027. The platform underpins card issuance, acquiring, and "
         "instant-payment processing for Meridian's retail and commercial customers across North America and EMEA."),
        ("p", "Regulatory drivers for immediate migration include:"),
        ("bullets", [
            "PCI-DSS compliance: on-premise infrastructure requires annual re-certification; cloud-native infrastructure meets DSS v3.2.1 "
            "requirements with vendor attestation, reducing Meridian's compliance burden.",
            "Resilience and SLA: current platform has quarterly 4-hour maintenance windows and single-datacenter failover (RTO 6 hours). Cloud "
            "deployment enables active–active geo-redundancy with RTO <15 minutes.",
            "Volume growth: instant-payment volumes have doubled year-over-year; current platform has reached 70% peak-capacity headroom. Cloud "
            "elasticity allows on-demand scaling without infrastructure re-provisioning.",
        ]),
        ("p", "This project, codenamed <b>Project Helios</b>, is the approved solution. Migration will occur in three waves (May, June, July 2026), "
         "with a six-week dual-running window to allow fallback if critical issues emerge. Cutover is targeted for 2026-07-31."),

        ("h1", "Critical Governance Point: Timing of Approval vs. Annual Operating Plan"),
        ("callout", "<b>IMPORTANT:</b> Project Helios was approved by the Group Investment Committee on 2026-02-20, <b>AFTER</b> the AOP_2026_v3 "
         "(annual operating plan) was locked on 2026-01-31. The program cost was <b>NOT</b> included in the 2026 operating plan and 2026 cost-centre "
         "budgets. As a result, project spending appears as an unfavourable variance against budget in Cards & Payments until the plan is re-baselined "
         "at the 2026-H2 re-forecast in July. This is a timing/approval artefact and a normal corporate-governance process. Cost-centre management "
         "is <b>NOT</b> accountable for this variance; it is a portfolio-level programme spend."),

        ("h1", "Approved Programme Cost and Workstream Phasing"),
        ("p", "The approved total programme cost for FY2026 is USD 6,820,000, phased across three core workstreams and vendor relationships. "
         "The following table details the FY2026 approved cost by workstream and vendor:"),
        ("table", [
            ["Workstream", "Vendor / Service", "Total Cost", "Mar 2026", "Apr 2026", "May 2026", "Jun 2026", "Jul–Sep 2026"],
            ["Systems Integration", "Helix Consulting Partners", "3,240,000", "45,000", "180,000", "810,000", "1,365,000", "840,000"],
            ["Cloud Hosting & Compute", "Northwind Cloud Services", "1,680,000", "120,000", "240,000", "360,000", "720,000", "240,000"],
            ["Software Licences", "Kestrel Software Ltd", "850,000", "85,000", "170,000", "255,000", "255,000", "85,000"],
            ["Contractor & Temp Labour", "Aster Staffing Solutions / Temp Agencies", "1,050,000", "30,000", "120,000", "300,000", "450,000", "150,000"],
            ["<b>TOTAL FY2026</b>", "", "<b>6,820,000</b>", "<b>280,000</b>", "<b>710,000</b>", "<b>1,725,000</b>", "<b>2,790,000</b>", "<b>1,315,000</b>"],
        ]),
        ("p", "Cumulative spend through 2026-06 is therefore USD 5,505,000 (280 + 710 + 1,725 + 2,790 = 5,505). The profile reflects a slow start "
         "in March (vendor mobilisation and infrastructure setup), acceleration through May and June as the three migration waves ramped, and "
         "planned reduction in July–September as dual-running concludes and the platform stabilises."),

        ("h2", "Cost Centres Charged"),
        ("p", "Project costs are charged to the following cost centres:"),
        ("bullets", [
            "<b>Cards Platform Engineering:</b> USD 4,720,000 (69% of total). Includes SI labour (Helix), cloud hosting (Northwind), software "
            "licences (Kestrel), and technical contractor augmentation. This is the primary benefiting cost centre.",
            "<b>Cards Issuing:</b> USD 980,000 (14% of total). Card-issuance process migration, testing, and cardholder communication.",
            "<b>Payments Operations:</b> USD 650,000 (10% of total). Instant-payment and clearing operations, staffing uplift for parallel processing.",
            "<b>Regulatory Reporting:</b> USD 470,000 (7% of total). Compliance monitoring, audit log setup, PCI audit preparation.",
        ]),

        ("h2", "GL Accounts and Expense Classification"),
        ("p", "Helios costs are charged to the following GL accounts according to expense type:"),
        ("table", [
            ["GL Account", "Description", "Estimated FY2026", "Primary Drivers"],
            ["530100", "Professional Fees - Consulting", "3,240,000", "Helix Consulting SI services"],
            ["520200", "Cloud Hosting & Compute", "1,680,000", "Northwind cloud infrastructure, data transfer, compute capacity"],
            ["520100", "Software Licences", "850,000", "Kestrel software platform and security modules"],
            ["510400", "Contractor & Temp Labour", "1,050,000", "Technical and operational staff augmentation"],
        ]),

        ("h1", "Contractor Ramp and Resource Plan"),
        ("p", "Cards Platform Engineering contractor headcount is planned as follows:"),
        ("bullets", [
            "<b>2026-01 baseline:</b> 35 contractors (legacy platform support).",
            "<b>2026-02–04 ramp:</b> 45 contractors (SI and cloud setup).",
            "<b>2026-05 peak:</b> 85 contractors (wave 1 and 2 migration execution).",
            "<b>2026-06 peak:</b> 95 contractors (wave 3 and dual-running).",
            "<b>2026-07 taper:</b> 65 contractors (cutover and stabilisation).",
            "<b>2026-08–09 retreat:</b> 40 contractors (residual support, planned descent to 25 by 2027-Q1).",
        ]),
        ("p", "This ramp-down profile is governed by the project schedule and dependent on cutover success. If critical issues arise during migration waves, "
         "the contractor count may remain elevated into Q3 or Q4 2026 for remediation work."),

        ("h1", "Benefits Case"),
        ("h2", "Capital Replacement Value and Depreciation Avoidance"),
        ("p", "The legacy platform would require a major hardware refresh in 2027 at an estimated capital cost of USD 3.2 million. Cloud migration "
         "eliminates this capital expenditure. Cloud-based platform has a recurring OpEx model; no capital refresh is required."),

        ("h2", "Operational Cost Savings (Annual Run-Rate Post-Migration)"),
        ("p", "Post-cutover, annual operational savings vs. legacy platform:"),
        ("bullets", [
            "<b>Reduced vendor support and maintenance contracts:</b> USD 450,000 annually (legacy platform end-of-support costs eliminated).",
            "<b>Staff headcount reduction:</b> USD 600,000 annually (6 FTE platform-engineering staff can be redeployed to innovation; cloud-native "
            "platform requires less hands-on infrastructure management).",
            "<b>Reduced infrastructure overhead:</b> USD 220,000 annually (datacenter space, cooling, power, and backup systems no longer needed for "
            "legacy platform).",
            "<b>Improved PCI compliance efficiency:</b> USD 120,000 annually (vendor attestation replaces internal audit effort).",
        ]),
        ("p", "<b>Total annual run-rate savings post-migration: USD 1,390,000.</b>"),

        ("h2", "Risk Mitigation and Compliance Value"),
        ("p", "PCI-DSS remediation: maintaining on-premise legacy platform exposes the organisation to a material compliance and reputational risk. "
         "Regulatory expectation (implied in FCA and OCC guidance) favours cloud-native deployment for payment systems. Estimated avoided compliance "
         "cost and potential fines: USD 500,000–1,000,000 over the next three years if migration is deferred."),

        ("h2", "Payback and NPV Analysis"),
        ("p", "Programme cost (FY2026): USD 6,820,000. Annual run-rate savings (post-2026): USD 1,390,000. Simple payback period: 4.9 years. "
         "However, if we include the avoided capital refresh (USD 3.2m in 2027), the net first-year benefit is positive. NPV at 8% discount rate over "
         "10 years: USD 2,340,000."),

        ("h1", "Governance and Reporting Framework"),
        ("h2", "Monthly Steering Committee"),
        ("p", "A Helios steering committee (chaired by the MD Cards & Payments) meets monthly to review:"),
        ("bullets", [
            "Spend vs. approved budget by workstream (variance >10% triggers escalation).",
            "Schedule vs. plan (wave completion milestones).",
            "Risk register (technical, vendor, operational, compliance).",
            "Change-request log and scope-control decisions.",
            "Migration readiness indicators (testing, cutover checklist).",
        ]),

        ("h2", "Variance Reporting in Close Pack"),
        ("p", "Monthly close reporting shall separately itemise Helios costs in the Cards & Payments variance commentary, citing this business case "
         "as the approval document. By 2026-07-31, a re-forecast will be issued (AOP_2026_v4) that re-bases the 2026-07–12 budgets to include the "
         "Helios programme. This re-baselining eliminates future-period variances attributable to the timing of project approval."),

        ("h2", "Change Control Process"),
        ("p", "Scope changes requested by the business or steering committee are evaluated against the approved cost and schedule. Changes are classified as:"),
        ("bullets", [
            "<b>In-scope:</b> Approved within the USD 6.82m budget envelope (e.g., additional test waves, vendor resource uplifts within existing contract rates). "
            "Approved by Helios steering committee without further investment approval.",
            "<b>Out-of-scope:</b> Exceeds approved budget or extends schedule beyond 2026-07-31 (e.g., new platform integrations, additional migration waves). "
            "Requires approval by the Group Investment Committee and business-case amendment.",
            "<b>Disputed:</b> Vendor change requests (scope uplift or rate-card revisions) are evaluated by Procurement for alignment with contract terms. "
            "Disputes are escalated to the Helios sponsor and General Counsel.",
        ]),
        ("p", "The rate-card dispute with Helix Consulting Partners (invoked invoices at blended rates above MSA schedule rates, citing change-order delivery) "
         "is a disputed change-control item pending resolution by Procurement and Legal."),

        ("h1", "Risk Register and Mitigation"),
        ("p", "The following material risks have been identified and mitigation strategies are in place:"),
        ("table", [
            ["Risk", "Impact if Realized", "Likelihood", "Mitigation Owner", "Mitigation Action"],
            ["Programme cost overrun (budget exceeded by >15%)", "Investment approval breach; CFO escalation", "Medium", "Helios Programme Manager", "Weekly budget tracking; change control; contingency reserve of 8% (USD 545k) held by PMO"],
            ["Vendor rate escalation / disputes", "Cost inflation; payment holds", "Medium–High", "Head of Procurement", "Contract terms locked for FY2026; rate disputes escalated via formal change-control; Helix dispute currently active"],
            ["Migration wave slippage (technical issues delay cutover beyond 2026-07-31)", "Dual-running cost extension; customer impact", "Medium", "Helios Technical Lead", "Enhanced testing; vendor accountability clauses; weekly go/no-go checkpoint before each wave"],
            ["Dual-running cost overrun (operations costs exceed 6-week estimate)", "Unbudgeted OpEx", "Low", "Head of Payments Operations", "Staffing plan locked; cost tracking; cutover insurance obtained"],
            ["Accrual / PO coverage lag (vendor billings exceed PO/receipts)", "AP ageing; cash-flow timing", "High", "Head of R2R", "Weekly PO alignment checkpoint; change requests trigger 7-day PO amendment window"],
        ]),

        ("h1", "Conclusion"),
        ("p", "Project Helios is a strategically critical initiative to migrate Meridian's card processing platform from end-of-life on-premise infrastructure "
         "to a cloud-native, resilient, and PCI-DSS-compliant platform. The USD 6.82m FY2026 investment is approved by the Group Investment Committee and is "
         "expected to deliver USD 1.39m annual run-rate operational savings post-cutover, plus avoided capital refresh and compliance risk mitigation."),
        ("p", "The apparent unfavourable variance in Cards & Payments (2026-06 +USD 2.72m) is a timing artefact of the February 2026 approval, which post-dated "
         "the January plan lock. Re-forecasting in July 2026 will re-base budgets to reflect this approved programme spend, and future-period variances will be "
         "normalised. Cost-centre management accountability and programme governance are in place to track execution against budget and schedule."),
    ],
    "footer": "Meridian Bank - Group Finance",
    "classification": "Internal",
}
