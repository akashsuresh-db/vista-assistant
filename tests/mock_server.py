#!/usr/bin/env python3
"""Serve the real app with a MOCK supervisor, for UI screenshots and manual checks
before the Agent Bricks endpoint exists.

Usage: python tests/mock_server.py [port]
"""
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "app"))

from backend import supervisor as sup  # noqa: E402

ANSWERS = {
    "data": (
        "**Cards & Payments** was the largest overspend in **2026-06**, at "
        "**USD 2.72m** unfavourable against budget.\n\n"
        "| Line of business | Actual (USD m) | Budget (USD m) | Variance (USD m) |\n"
        "|---|---|---|---|\n"
        "| Cards & Payments | 28.95 | 26.22 | +2.72 |\n"
        "| Corporate Banking | 12.41 | 12.07 | +0.34 |\n"
        "| Technology | 19.86 | 19.54 | +0.32 |\n"
        "| Operations | 9.72 | 9.42 | +0.30 |\n\n"
        "The overspend is concentrated in three accounts, all in "
        "**Cards Platform Engineering**:\n\n"
        "- Professional Fees – Consulting **+979k**\n"
        "- Cloud Hosting & Compute **+608k**\n"
        "- Software Licences **+361k**\n\n"
        "It is a rising trend rather than a one-off spike: +0.53m in March, "
        "+0.65m in April, +1.46m in May and +2.72m in June."
    ),
    "docs": (
        "Under **FIN-ACC-014** (Accruals and Provisions Policy, v4.2) an accrual must be "
        "settled, re-substantiated or reversed within **90 days** of posting.\n\n"
        "If it is still open beyond 90 days:\n\n"
        "1. It is a **policy breach** and must appear in the month-end exception pack.\n"
        "2. The cost centre owner must provide a written **re-substantiation memo**.\n"
        "3. That memo must be **countersigned by the Financial Controller**.\n\n"
        "Evidence quality matters too — `MANUAL_ESTIMATE` is the weakest basis and needs "
        "Financial Controller sign-off above **USD 50,000**."
    ),
    "both": (
        "**Cards & Payments** is **USD 2.72m** over budget in 2026-06, and yes — the spend "
        "was approved, just after the plan was locked.\n\n"
        "**What the data shows**\n\n"
        "| Driver | Cost centre | Variance (USD) |\n"
        "|---|---|---|\n"
        "| Professional Fees – Consulting | Cards Platform Engineering | +979,000 |\n"
        "| Cloud Hosting & Compute | Cards Platform Engineering | +608,000 |\n"
        "| Software Licences | Cards Platform Engineering | +361,000 |\n\n"
        "**Why it is unbudgeted**\n\n"
        "Per the Project Helios business case (PROJ-HELIOS-BC-v2), the card platform cloud "
        "migration was approved by the Group Investment Committee in **February 2026** — "
        "*after* the **AOP_2026_v3** plan was locked in January. The cost was therefore "
        "never in the cost centre budgets and will show as unfavourable until the H2 "
        "re-forecast resets the baseline.\n\n"
        "This is a timing and approval artefact, not uncontrolled overspend."
    ),
}


def classify(q: str) -> str:
    """Stand-in for the supervisor's routing decision, used only by the mock."""
    ql = q.lower()
    data_words = ("overspent", "overspend", "over budget", "variance", "how much",
                  "which vendor", "sla", "trend", "aging", "top", "count", "exposure",
                  "cost centre", "cost center", "which line of business", "figures",
                  "how many", "balance", "accruals breach")
    doc_words = ("policy", "rule", "procedure", "escalation", "approved", "approval",
                 "threshold", "say about", "standard", "sop", "governance",
                 "must i do", "allowed")
    d = any(w in ql for w in data_words)
    k = any(w in ql for w in doc_words)
    if d and k:
        return "both"
    return "docs" if k else "data"


def mock_stream(question, history=None):
    kind = classify(question)
    if kind in ("data", "both"):
        yield {"type": "route", "agent": "fna_analytics_genie"}
        time.sleep(0.5)
    if kind in ("docs", "both"):
        yield {"type": "route", "agent": "fna_knowledge_assistant"}
        time.sleep(0.5)
    text = ANSWERS[kind]
    # stream in word-ish chunks so the typing effect is visible
    step = 18
    for i in range(0, len(text), step):
        time.sleep(0.03)
        yield {"type": "chunk", "text": text[i:i + step]}
    yield {"type": "done",
           "history": (history or []) + [{"role": "user", "content": question},
                                         {"role": "assistant", "content": text}],
           "routes": []}


sup.stream = mock_stream
sup.ENDPOINT = "mock-supervisor-endpoint"

from backend.main import app  # noqa: E402

if __name__ == "__main__":
    import uvicorn
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8931
    print(f"mock Vista Assistant on http://127.0.0.1:{port}")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
