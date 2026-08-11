#!/usr/bin/env python3
"""Ask the Genie space the demo questions and check the answers contain the right facts.

This is the real test of whether the space's instructions work: it exercises text-to-SQL
end to end and asserts on the returned numbers, not just that a query ran.

Usage: python test_genie.py [space_id]
"""
import re
import sys

from databricks.sdk import WorkspaceClient
from scripts.config import CFG

SPACE_ID = sys.argv[1] if len(sys.argv) > 1 else CFG.genie_space_id
if not SPACE_ID:
    print("SKIP: genie_space_id not configured in config.yaml", file=sys.stderr)
    sys.exit(0)

w = WorkspaceClient(profile=CFG.profile) if CFG.profile else WorkspaceClient()

# (question, [regex that must match the answer text or result rows])
CASES = [
    ("Which line of business overspent the most in June 2026?",
     [r"cards\s*&?\s*payments", r"2[.,]7|2,7\d\d|272\d\d\d\d"]),
    ("What drove the Cards & Payments overspend in June 2026? Show the top expense accounts.",
     [r"professional fees|consulting", r"cloud|hosting", r"licen"]),
    ("How much of the MB-UK June 2026 expense variance is FX translation rather than local overspend?",
     [r"69\d[,.]?\d*|691", r"10[67]|107"]),
    ("Which accruals breach the 90-day policy?",
     [r"acr518[3-8]", r"486[,.]?000|486000"]),
    ("Which close tasks missed their SLA in June 2026?",
     [r"accrual calculation", r"intercompany billing", r"sub-?ledger cut-?off"]),
    ("Which vendor has the largest 90+ day payables exposure?",
     [r"helix", r"1[,.]?310[,.]?500|1310500|1[.,]31"]),
    ("Are there any unresolved intercompany breaks?",
     [r"mb-uk", r"mb-sg", r"482[,.]?000|482000"]),
    ("Show the Cards & Payments expense variance trend across 2026 by month.",
     [r"2026-0[1-6]", r"1[.,]4\d|146\d\d\d\d", r"2[.,]7\d|272\d\d\d\d"]),
]


def answer_text(space_id, question):
    """Send one question and flatten the response (prose + any result rows) to text."""
    msg = w.genie.start_conversation_and_wait(space_id, question)
    parts = []
    if msg.content:
        parts.append(msg.content)
    for att in (msg.attachments or []):
        if att.text and att.text.content:
            parts.append(att.text.content)
        if att.query:
            if att.query.description:
                parts.append(att.query.description)
            if att.query.query:
                parts.append(att.query.query)
            try:
                res = w.genie.get_message_query_result_by_attachment(
                    space_id, msg.conversation_id, msg.id, att.attachment_id)
                if res.statement_response and res.statement_response.result:
                    for row in (res.statement_response.result.data_array or []):
                        parts.append(" | ".join(str(c) for c in row))
            except Exception as e:
                parts.append(f"[result fetch failed: {e}]")
    return "\n".join(parts)


def main():
    fails = []
    for q, pats in CASES:
        print("=" * 78)
        print("Q:", q)
        try:
            txt = answer_text(SPACE_ID, q)
        except Exception as e:
            print("  ERROR:", e)
            fails.append((q, f"exception: {e}"))
            continue
        low = txt.lower()
        print("  answer excerpt:", " ".join(txt.split())[:300])
        missing = [p for p in pats if not re.search(p, low)]
        if missing:
            print("  FAIL missing:", missing)
            fails.append((q, missing))
        else:
            print("  PASS")
    print("\n" + "=" * 78)
    if fails:
        print(f"{len(fails)}/{len(CASES)} FAILED")
        for q, m in fails:
            print(f"  - {q}\n      missing {m}")
        return 1
    print(f"ALL {len(CASES)} GENIE CASES PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
