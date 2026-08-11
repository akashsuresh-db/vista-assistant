"""Group Finance Management Discussion & Analysis - Q2 2026 Board Pack

This module defines the MDA presentation for Q2 2026 board reporting, covering the quarter
ended 30 June 2026. The pack addresses two key themes: (1) the Cards & Payments technology
overrun driven by Project Helios, a platform migration approved after budget lock; and
(2) the EMEA FX translation headwind, which reflects currency strength rather than local
overspending.

Format: PPTX presentation with 11 slides, each using slide blocks containing bullets.
Two-space indented bullets render as sub-bullets.
"""

DOC = {
    "filename": "Group_Finance_MDA_Q2_2026_Board_Pack.pptx",
    "title": "Group Finance - Management Discussion & Analysis",
    "subtitle": "Q2 2026 Board Reporting Pack",
    "meta": [
        ("Period", "Q2 2026 (quarter ended 30 June 2026)"),
        ("Prepared by", "Group Financial Planning & Analysis"),
        ("Status", "Final - presented to the Board Finance Committee, 2026-07-22"),
        ("Classification", "Internal - Restricted"),
    ],
    "blocks": [
        ("slide", "Executive Summary", [
            "• Group operating expense: USD 28.95m actual vs USD 26.22m budget for Cards & Payments (unfavourable +USD 2.72m)",
            "• This overrun is driven by Project Helios, the card-processing platform migration to cloud, approved February 2026 after AOP lock",
            "• Helios is a multi-month programme ramp (Mar +0.53m, Apr +0.65m, May +1.46m, Jun +2.72m), not a control failure",
            "• EMEA entities (MB-UK, MB-DE) report unfavourable USD variances, but 77-81% are FX translation; local overspend is modest",
            "• FX headwind: GBP strengthened 1.178 → 1.299; EUR 0.992 → 1.091, creating USD reporting headwinds",
            "• Board should reset expectations for H2 re-forecast; manage FX at Group Treasury level; and monitor accrual ageing and intercompany breaks",
        ]),
        ("slide", "Group Operating Expense Summary", [
            "• Total group unfavourable variance: USD 2.72m in Cards & Payments; smaller variances in Corporate Banking (+0.34m), Technology (+0.32m), Operations (+0.30m)",
            "• Of the reported USD variance, material portion is FX translation rather than local-currency overspend",
            "• Constant-currency accountability: cost centre managers held accountable only for local-currency variance; Group Treasury owns FX translation",
            "• MB-UK: +798k USD variance, but only +107k constant-currency; 691k is translation (GBP 1.18 → 1.30)",
            "• MB-DE: +228k USD variance, but only +49k constant-currency; 179k is translation (EUR 0.99 → 1.09)",
            "• Implication: underlying cost control is reasonable; reported unfavourable USD variance overstates operational performance",
        ]),
        ("slide", "Cards & Payments Deep Dive - June 2026", [
            "• June 2026 actual: USD 28.95m vs budget USD 26.22m; +USD 2.72m unfavourable",
            "• Largest drivers all tied to Project Helios and platform engineering:",
            "  Professional Fees - Consulting (Cards Platform) +USD 979k; Cloud Hosting & Compute +USD 608k; Software Licences +USD 361k",
            "  Professional Fees (Cards Issuing) +USD 241k; Software Licences (Cards Issuing) +USD 121k",
            "• Operational cost driver: Contractor & Temp Labour (Payments Operations) +USD 111k as headcount ramped",
            "• Vendors: Helix Consulting (SI), Northwind Cloud Services (cloud), Kestrel Software (licences)",
            "• These costs are programme-driven, not permanent; forecast to reduce as Helios deployment completes in H2 2026",
        ]),
        ("slide", "Project Helios - Context and Approval", [
            "• Project Helios: card-processing platform migration to cloud; approved February 2026",
            "• Timing: AOP 2026 v3 was locked in January 2026; Helios approval post-lock means costs are unbudgeted in baseline cost centre plans",
            "• FY2026 approved Helios cost: estimated USD 8.5m; deployment through H2 2026",
            "• H2 re-forecast planned to reset cost centre budgets and establish revised Helios trajectory",
            "• Three vendor partners: Helix Consulting (system integration), Northwind Cloud (hosting), Kestrel Software (platform licensing)",
            "• Platform Go-Live target: December 2026; current status on track",
        ]),
        ("slide", "Variance Trajectory - The Helios Ramp", [
            "• Project Helios manifests as a controlled ramp, not a spike or uncontrolled overrun:",
            "  2026-03: +USD 0.53m; 2026-04: +USD 0.65m; 2026-05: +USD 1.46m; 2026-06: +USD 2.72m",
            "• Cumulative Q2 2026 Helios variance: USD 4.86m YTD",
            "• Ramp trajectory matches project phasing: Q1 discovery & contracting, Q2 detailed design & infrastructure, Q3/H2 build & deployment",
            "• This is a programme delivery curve; it reflects planned expenditure, not cost control drift",
            "• Key mitigation: H2 re-forecast will re-baseline cost centre budgets and clarify final Helios cost",
        ]),
        ("slide", "Contractor and Resourcing Impact", [
            "• Cards Platform Engineering contractor headcount: 35 FTE (2026-01) → 95 FTE (2026-06)",
            "• Ramp driven by Helios platform build; contractors sourced via Helix and staffing partners (Aster Staffing Solutions)",
            "• Contractor rate: average USD 85k-95k per FTE annually; blended in-house rate USD 125k",
            "• Planned reversal: contractor headcount to reduce to baseline (~25 FTE) by Q1 2027 as core build phases complete",
            "• Cost impact: contractor & temp labour variance +USD 111k in June; trend continues in Q3 before reversal",
            "• Staffing plan contingent on Helios milestone achievements; review every 30 days vs project schedule",
        ]),
        ("slide", "FX Translation Impact - EMEA Headwind", [
            "• GBP plan rate (January 2026): 1.178; June 2026 actual monthly average: 1.299; GBP strengthened 10.3%",
            "• EUR plan rate: 0.992; June 2026 actual: 1.091; EUR strengthened 9.95%",
            "• MB-UK: USD variance +798k total; constant-currency +107k; FX translation 691k (86% of reported variance)",
            "• MB-DE: USD variance +228k total; constant-currency +49k; FX translation 179k (78% of reported variance)",
            "• In GBP terms, MB-UK is approximately 6% FAVOURABLE; in EUR terms, MB-DE is close to plan",
            "• Translation impact is a macro effect outside cost centre control; Group Treasury manages hedging strategy and FX governance",
        ]),
        ("slide", "Balance Sheet and Control Matters", [
            "• Aged accruals policy (FIN-ACC-014): 6 accruals >90 days old, total USD 1,339,800 at 2026-06-30",
            "  4 in Cards & Payments (Helios-related): Helix Consulting USD 486k (153 days), Northwind Cloud USD 312.5k (125 days)",
            "  Kestrel Software USD 208.4k (154 days); Trident Payment Networks USD 174.2k (124 days)",
            "• Internal Audit memo IA-2026-11 flags these as policy breach; remediation plan submitted for 2026-07 close",
            "• Intercompany break MB-UK to MB-SG (Treasury Funding): USD 482,000 unresolved in both 2026-05 and 2026-06",
            "• Break exceeds reportable threshold (USD 250k); crosses escalation rule (>1 period open); logged against FIN-IC-021",
        ]),
        ("slide", "Working Capital and Disputed Payables", [
            "• Largest 90+ day AP exposure: Helix Consulting Partners, USD 1,310,500 across 4 invoices (Cards Platform Engineering account 530100)",
            "• ALL Helix invoices disputed; match_status: PRICE_VARIANCE on Project Helios change requests",
            "• Dispute root cause: Helix billed at blended rate higher than MSA rate schedule; relates to scope changes and extended engagement",
            "• Next largest 90+ exposures: Solstice Print & Fulfilment USD 413k; Kestrel Software USD 350k (smaller disputes)",
            "• Procurement and Legal being engaged for rate-card reconciliation and potential credit note negotiation",
            "• Expected resolution: 2026-08 or 2026-09; interim accrual treatment per accounting policy",
        ]),
        ("slide", "Close Performance - SLA Breaches", [
            "• Three SLA breaches in 2026-06 close cycle (Group consolidation target = business day 8):",
            "• MB-US Accrual calculation & upload: SLA day 2, actual day 5 (3 days late); Record to Report team",
            "• MB-UK Intercompany billing & matching: SLA day 3, actual day 6 (3 days late); Record to Report team",
            "• MB-SG Sub-ledger cut-off - Accounts Payable: SLA day 1, actual day 3 (2 days late); Procure to Pay team",
            "• Root causes: (1) late accrual documentation from Cards & Payments; (2) intercompany break uncertainty delaying MB-UK close",
            "• Mitigations: escalate accrual owners; implement dedicated intercompany break task force for Q3",
        ]),
        ("slide", "Outlook and Management Actions", [
            "• H2 2026 Re-forecast: reset Helios cost budget and establish monthly run-rate expectations for Q3 and Q4",
            "• Accrual remediation: target all 6 breached accruals resolved in 2026-07 close; 90-day rule compliance enforced from 2026-08",
            "• Helix Consulting dispute escalation: Procurement and Legal to resolve rate-card and scope variance by 2026-09-15",
            "• Intercompany break clearance: Treasury and entities to resolve MB-UK → MB-SG USD 482k before Q3 consolidation (2026-09-05)",
            "• FX headwind: Group Treasury to review hedging effectiveness; no cost centre action required",
            "• Close SLA tracking: daily cadence on accrual and intercompany items; target zero breaches in Q3",
        ]),
        ("slide", "Appendix - Basis of Preparation", [
            "• Data sources: GL balances from fact_gl_balance; budgets from fact_budget; variance calculated from v_opex_variance view",
            "• FX convention: budgets locked at plan rates (Jan 2026 spot for FY2026); actuals translate at monthly average rates",
            "• Constant-currency variance = (Actual Local – Budget Local) × Plan Rate; FX impact = residual",
            "• Accruals sourced from fact_accrual and v_aged_accrual (policy_status = BREACH_OVER_90_DAYS)",
            "• Intercompany sourced from fact_intercompany; open items defined as status = UNRESOLVED_BREAK",
            "• Close performance from fact_close_task with actual vs SLA day comparison",
        ]),
    ],
}

