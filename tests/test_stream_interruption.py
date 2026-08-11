#!/usr/bin/env python3
"""Test that the UI handles stream interruption gracefully."""
import subprocess
import time
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
import os
from playwright.sync_api import sync_playwright

def test_stream_interruption():
    """Start mock server, send a request, kill it mid-stream, observe UI state."""
    # Start mock server
    mock_proc = subprocess.Popen(
        ["python", "tests/mock_server.py", "8931"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(ROOT)
    )
    time.sleep(2)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            context = browser.new_context()
            page = context.new_page()

            # Navigate to the mock app
            page.goto("http://localhost:8931/")
            page.wait_for_selector(".sugg", timeout=5000)
            print("PASS  page loaded")

            # Click on the first suggestion
            page.click(".sugg")

            # Give it a moment to start streaming
            time.sleep(0.5)

            # Kill the mock server while stream is active
            mock_proc.terminate()
            print("PASS  killed mock server mid-stream")

            # Wait a moment for the stream to detect the death
            time.sleep(1)

            # Check the UI state: should either show partial text (graceful) or error
            body = page.query_selector(".msg.assistant .body")
            if body:
                content = body.text_content()
                if content and (len(content) > 0 or "error" in content.lower()):
                    print(f"PASS  UI shows graceful state: '{content[:60]}...'")
                else:
                    print("FAIL  UI is blank after stream interruption")
                    return False
            else:
                print("FAIL  no assistant message found")
                return False

            page.close()
            context.close()
            browser.close()
            return True

    finally:
        mock_proc.terminate()
        try:
            mock_proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            mock_proc.kill()

if __name__ == "__main__":
    try:
        if test_stream_interruption():
            print("\nALL STREAM INTERRUPTION TESTS PASSED")
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
