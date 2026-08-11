#!/usr/bin/env python3
"""Drive the chat UI in a browser, verify rendered output, and save screenshots.

This is the end-to-end check that streaming reaches the DOM correctly: it asserts on
the rendered HTML (tables, bold, minimal layout), not on the network payload.

Usage: python tests/shoot_ui.py [base_url] [outdir]
"""
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8931"
OUT = sys.argv[2] if len(sys.argv) > 2 else str(ROOT / "docs" / "screenshots")
os.makedirs(OUT, exist_ok=True)

QUESTIONS = [
    ("q1_data", "Which line of business overspent the most in June 2026?"),
    ("q2_policy", "What does our accrual policy say about accruals older than 90 days?"),
    ("q3_both", "Why is Cards & Payments over budget, and was the spend approved?"),
]

FAILS = []


def check(label, cond, detail=""):
    print(f"{'PASS' if cond else 'FAIL'}  {label}{(' — ' + detail) if detail else ''}")
    if not cond:
        FAILS.append(label)


def _auth_headers():
    """A deployed Databricks App needs a bearer token; localhost does not."""
    if "databricksapps.com" not in BASE:
        return {}
    import subprocess
    out = subprocess.run(["databricks", "auth", "token", "-p", CFG.profile],
                         capture_output=True, text=True).stdout
    try:
        return {"Authorization": f"Bearer {json.loads(out)['access_token']}"}
    except Exception:
        return {}


def main():
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": 1440, "height": 940},
                            device_scale_factor=2,
                            extra_http_headers=_auth_headers())
        page = ctx.new_page()
        page.goto(BASE, wait_until="networkidle", timeout=60_000)
        page.wait_for_timeout(1200)

        check("landing page renders the title",
              "Vista Assistant" in page.inner_text("body"))
        check("single centred input present", page.locator("#q").count() == 1)
        check("starter questions offered", page.locator(".starter").count() >= 4,
              f"{page.locator('.starter').count()} starters")
        check("idle layout: thread hidden until first question",
              not page.locator("body.chatting").count())
        page.screenshot(path=f"{OUT}/00_landing.png", full_page=False)
        print(f"  saved {OUT}/00_landing.png")

        for tag, q in QUESTIONS:
            page.fill("#q", q)
            page.click("#send")

            # mid-stream: the working tile must be visible and filling, so the user is
            # never staring at a blank screen while the agent thinks
            page.wait_for_selector(".msg.assistant details.trace", timeout=30_000)
            trace = page.locator(".msg.assistant details.trace").last
            check(f"{tag}: working tile open while streaming",
                  trace.get_attribute("open") is not None)
            # first token from the agent can take several seconds, so poll rather than
            # assume a fixed delay
            filled = 0
            for _ in range(40):
                page.wait_for_timeout(500)
                filled = len(page.locator(".msg.assistant .trace-body").last.inner_text())
                if filled > 40:
                    break
            check(f"{tag}: working tile fills with the agent's steps before the answer",
                  filled > 40, f"{filled} chars in the tile")
            page.screenshot(path=f"{OUT}/{tag}_streaming.png")

            # wait for the send button to re-enable = stream finished
            page.wait_for_function("() => !document.querySelector('#send').disabled",
                                  timeout=90_000)
            page.wait_for_timeout(600)

            body = page.locator(".msg.assistant .answer").last
            html = body.inner_html()
            text = body.inner_text()

            # routing must NOT be surfaced: the user should not see which agent answered
            check(f"{tag}: no routing chip leaked to the user",
                  page.locator(".msg.assistant .chip").count() == 0)
            check(f"{tag}: working tile collapsed once answered",
                  page.locator(".msg.assistant details.trace").last
                      .get_attribute("open") is None)
            check(f"{tag}: working tile still expandable",
                  "How this was answered" in
                  page.locator(".msg.assistant .trace-label").last.inner_text())
            check(f"{tag}: bold rendered as <strong>", "<strong>" in html)
            # The agent decides whether to include a table, and that varies between runs.
            # The app's guarantee is: if one is present it renders, and raw markdown never
            # leaks either way.
            if "|" in text or 'class="chat-tbl"' in html:
                check(f"{tag}: any table is rendered, not left as raw markdown",
                      "|---" not in text and not re.search(r"\|\s*\w+\s*\|", text),
                      f"raw pipes present: {text[:80]!r}")
            check(f"{tag}: no separator rows leaked", "|---" not in text)
            check(f"{tag}: no unrendered asterisks left", "**" not in text)
            # provenance: every answer should say what it was grounded in
            check(f"{tag}: sources panel present",
                  page.locator(".msg.assistant details.sources").count() > 0)
            check(f"{tag}: at least one source listed",
                  page.locator(".msg.assistant .src").count() > 0)
            check(f"{tag}: starters hidden once chatting",
                  page.locator(".starter:visible").count() == 0)

            page.screenshot(path=f"{OUT}/{tag}_answer.png", full_page=True)
            print(f"  saved {OUT}/{tag}_answer.png")

        b.close()

    print()
    if FAILS:
        print(f"{len(FAILS)} UI FAILURES: {FAILS}")
        return 1
    print("ALL UI CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
