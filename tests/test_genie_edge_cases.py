#!/usr/bin/env python3
"""Probe Genie with awkward/edge-case questions to find robustness issues."""
import re
import sys
from databricks.sdk import WorkspaceClient

from scripts.config import CFG

SPACE_ID = sys.argv[1] if len(sys.argv) > 1 else CFG.genie_space_id
if not SPACE_ID:
    print("SKIP: genie_space_id not configured in config.yaml", file=sys.stderr)
    sys.exit(0)

w = WorkspaceClient(profile=CFG.profile) if CFG.profile else WorkspaceClient()

def answer_text(space_id, question):
    """Send one question and flatten the response to text."""
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

# Test cases: (question, expected_behavior)
CASES = [
    # Ambiguous period: "last month" in a dataset ending June 2026 — should map to 2026-06
    ("What was the expense variance last month?",
     ["2026-06", "variance"], "handle 'last month' as 2026-06"),

    # Metric that doesn't exist in our warehouse
    ("Show me EBITDA by region",
     ["don't", "have", "don't have", "cannot", "no data"], "gracefully handle non-existent metric"),

    # Question that should return empty result
    ("Which accruals breach the policy in 2025-03?",
     ["no", "none", "0", "not found", "2025-03", "empty"], "handle query returning zero rows"),

    # Sign convention edge case: cost performance can be ambiguous
    # (most FAVOURABLE variance should win, not largest USD amount)
    ("Which cost center had the best cost performance in June 2026?",
     ["favour", "negative variance", "under budget", "-", "savings"],
     "handle sign convention (best = most negative/favourable)"),

    # Vague question that should prompt clarification or return something reasonable
    ("What's wrong with the financial data?",
     ["breach", "aged", "unresolved", "missing", "no issues"],
     "handle vague question"),
]

def check_answer(answer_text, keywords):
    """Check if any of the keywords appear in the answer (case-insensitive)."""
    low = answer_text.lower()
    return any(re.search(re.escape(kw), low) for kw in keywords)

def main():
    fails = []
    for q, keywords, expectation in CASES:
        print("=" * 78)
        print(f"Q: {q}")
        print(f"   Expectation: {expectation}")
        try:
            answer = answer_text(SPACE_ID, q)
            excerpt = " ".join(answer.split())[:400]
            print(f"   Answer: {excerpt}")

            if check_answer(answer, keywords):
                print(f"   PASS")
            else:
                print(f"   FAIL: expected one of {keywords}")
                fails.append((q, f"keywords not found: {keywords}"))
        except Exception as e:
            print(f"   ERROR: {e}")
            fails.append((q, f"exception: {e}"))

    print("\n" + "=" * 78)
    if fails:
        print(f"FAILURES ({len(fails)}):")
        for q, reason in fails:
            print(f"  {q[:60]}...\n    {reason}")
        sys.exit(1)
    else:
        print("ALL EDGE-CASE TESTS PASSED")
        sys.exit(0)

if __name__ == "__main__":
    main()
