#!/usr/bin/env python3
"""Streaming + formatting tests — the stated success criterion for the chat.

Covers three separable concerns:

  A. supervisor.stream() event semantics, driven by a FAKE endpoint that replays a
     realistic `agent/v1/responses` SSE transcript. This proves we (i) forward deltas
     incrementally, (ii) SUPPRESS tool-routing narration, and (iii) emit route + done.
  B. The /api/chat SSE wire format, via the real FastAPI app with the supervisor stubbed.
     Asserts frames arrive PROGRESSIVELY (not one buffered burst) — the failure mode that
     makes a "streaming" chat feel broken.
  C. The markdown renderer, executed as real JS (node) against the shipped app.js, so
     tables/bold/bullets are verified rather than assumed.

Run: python tests/test_streaming.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "app"))

FAILURES: list[str] = []


def check(label, cond, detail=""):
    print(f"{'PASS' if cond else 'FAIL'}  {label}{(' — ' + detail) if detail else ''}")
    if not cond:
        FAILURES.append(label)


# ===================================================================== part A
# A realistic transcript: the supervisor first narrates that it will call a sub-agent
# (item msg_1), calls it, then streams the real answer (item msg_2). msg_1 must NOT
# reach the user.
TRANSCRIPT = [
    {"type": "response.output_item.added",
     "item_id": "msg_1", "item": {"id": "msg_1", "type": "message"}},
    {"type": "response.output_text.delta", "item_id": "msg_1",
     "delta": "I'll query the FnA Analytics "},
    {"type": "response.output_text.delta", "item_id": "msg_1",
     "delta": "agent to get the variance."},
    # REAL behaviour (observed against the supervisor endpoint): the narration item is
    # reported done TWICE - first as a plain "message", and only on the SECOND done is it
    # revealed to be a function_call. Releasing on the first one leaks the narration, so
    # this pair is the regression guard for that bug.
    {"type": "response.output_item.done", "item_id": "msg_1",
     "item": {"id": "msg_1", "type": "message"}},
    {"type": "response.output_item.done", "item_id": "msg_1",
     "item": {"id": "msg_1", "type": "function_call", "name": "fna_analytics_genie"}},
    # the supervisor also emits some empty intermediate message items
    {"type": "response.output_item.done", "item_id": "tool_result_1",
     "item": {"id": "tool_result_1", "type": "message"}},
    {"type": "response.output_item.added",
     "item_id": "msg_2", "item": {"id": "msg_2", "type": "message"}},
    {"type": "response.output_text.delta", "item_id": "msg_2",
     "delta": "**Cards & Payments** overspent by "},
    {"type": "response.output_text.delta", "item_id": "msg_2", "delta": "**USD 2.72m** "},
    {"type": "response.output_text.delta", "item_id": "msg_2",
     "delta": "in 2026-06.\n\n| Driver | Variance |\n|---|---|\n| Consulting | 979k |\n"},
    {"type": "response.output_item.done", "item_id": "msg_2",
     "item": {"id": "msg_2", "type": "message"}},
    {"type": "response.completed"},
]

# No tool call at all: the buffered text IS the answer and must still be delivered.
TRANSCRIPT_NO_TOOL = [
    {"type": "response.output_item.added",
     "item_id": "m1", "item": {"id": "m1", "type": "message"}},
    {"type": "response.output_text.delta", "item_id": "m1", "delta": "The 90-day rule "},
    {"type": "response.output_text.delta", "item_id": "m1",
     "delta": "requires reversal (FIN-ACC-014)."},
    {"type": "response.output_item.done", "item_id": "m1",
     "item": {"id": "m1", "type": "message"}},
    {"type": "response.completed"},
]

# The REAL stream shape (verified against the supervisor endpoint): a sub-agent's reply is
# streamed verbatim but every one of its deltas carries `tool_call_id` + `tool_name`, while
# the supervisor's own narration and final synthesis carry neither. That makes sub-agent
# output identifiable ON ARRIVAL, so it is never shown and never has to be retracted.
TRANSCRIPT_TOOLTEXT = [
    {"type": "response.output_item.added",
     "item_id": "n1", "item": {"id": "n1", "type": "message"}},
    {"type": "response.output_text.delta", "item_id": "n1", "step": 1,
     "delta": "I'll check the finance data and the policy documents."},
    # the narration item is reported done TWICE - first "message", then "function_call"
    {"type": "response.output_item.done", "item_id": "n1",
     "item": {"id": "n1", "type": "message"}},
    {"type": "response.output_item.done", "item_id": "n1",
     "item": {"id": "n1", "type": "function_call", "name": "genie-space-id",
              "arguments": '{"genie_query": "Cards & Payments variance for 2026-06"}'}},
    # sub-agent output: carries tool_call_id, must NEVER reach the client
    {"type": "response.output_text.delta", "item_id": "t1", "step": 1,
     "tool_call_id": "toolu_abc", "tool_name": "genie-space-id",
     "delta": "SUBAGENT_ROWS: |cc|actual|budget|\n|Cards Platform Eng|8511847|6545433|"},
    {"type": "response.output_item.done", "item_id": "t1",
     "item": {"id": "t1", "type": "message"}},
    # SECOND narration, arriving BETWEEN tool calls. This is the reported bug: it is
    # supervisor-authored (no tool_call_id) and it comes after a tool call, so any rule of
    # the form "non-tool text after a tool call is the answer" wrongly admits it.
    {"type": "response.output_text.delta", "item_id": "n2", "step": 1,
     "delta": "Now let me check the approval documentation for this spend:"},
    {"type": "response.output_item.done", "item_id": "n2",
     "item": {"id": "n2", "type": "message"}},
    {"type": "response.output_item.done", "item_id": "n2",
     "item": {"id": "n2", "type": "function_call", "name": "ka-endpoint"}},
    {"type": "response.output_text.delta", "item_id": "t2", "step": 1,
     "tool_call_id": "toolu_def", "tool_name": "ka-endpoint",
     "delta": "SUBAGENT_DOC: Project Helios was approved on 2026-02-20."},
    # citations for the document the KA used
    {"type": "response.output_text.annotation.added", "item_id": "t2",
     "annotation": {"type": "url_citation",
                    "title": "PROJ-HELIOS_Business_Case_and_Cost_Approval.pdf",
                    "url": "https://host/x/PROJ-HELIOS_Business_Case_and_Cost_Approval.pdf"
                           "#page=5:~:text=approved%20by%20the%20Group%20Investment%20Committee"}},
    {"type": "response.output_text.annotation.added", "item_id": "t2",
     "annotation": {"type": "url_citation",
                    "title": "PROJ-HELIOS_Business_Case_and_Cost_Approval.pdf",
                    "url": "https://host/x/PROJ-HELIOS_Business_Case_and_Cost_Approval.pdf"
                           "#page=1:~:text=AOP_2026_v3%20was%20locked"}},
    # A UC FUNCTION result. Unlike a sub-agent, this does NOT stream as text deltas - it
    # arrives once as a `function_call_output` item whose `output` is the
    # Statement-Execution envelope {"columns":[...],"rows":[[value]]}. Missing this shape
    # silently loses the chart, which is the regression this guards.
    {"type": "response.output_item.done",
     "item": {"type": "function_call_output", "call_id": "toolu_chart",
              "name": "main__vista_assistant__make_chart",
              "output": json.dumps({"is_truncated": False, "columns": ["output"],
                                    "rows": [[json.dumps({
                                        "$schema": "https://vega.github.io/schema/vega-lite/v6.json",
                                        "mark": {"type": "bar", "color": "#a100ff"},
                                        "title": {"text": "Variance by LOB"},
                                        "data": {"values": [{"lob": "Cards", "v": 2.72}]},
                                        "encoding": {"x": {"field": "lob"}}})]]})}},
    # the supervisor's own synthesis: no tool_call_id, highest step. Includes a footnote
    # marker and a <name> tag, both of which must be stripped.
    {"type": "response.output_text.delta", "item_id": "f1", "step": 3,
     "delta": "<name>FnA-Agent</name>**Cards & Payments** is $2.7m over budget[^nAI8-1] "},
    {"type": "response.output_text.delta", "item_id": "f1", "step": 3,
     "delta": "and the spend was approved.\n\n| Driver | Variance |\n|---|---|\n| Consulting | 979k |\n"},
    {"type": "response.output_item.done", "item_id": "f1",
     "item": {"id": "f1", "type": "message"}},
    {"type": "response.completed"},
]

# THE "empty response" BUG: the agent ends on a tool call and never writes a closing
# message, so EVERY message item resolves into a function_call and is classified as
# narration. The old code then had no candidate and returned
# "the agent returned an empty response", discarding a perfectly good summary.
TRANSCRIPT_NO_FINAL_MSG = [
    {"type": "response.output_item.added",
     "item_id": "s1", "item": {"id": "s1", "type": "message"}},
    {"type": "response.output_text.delta", "item_id": "s1", "step": 1,
     "delta": "I'll get the variance data."},
    {"type": "response.output_item.done", "item_id": "s1",
     "item": {"id": "s1", "type": "function_call", "name": "genie-space-id"}},
    # a substantive summary - but this item ALSO resolves into a function_call, because the
    # agent's last act is to call the chart tool
    {"type": "response.output_text.delta", "item_id": "s2", "step": 2,
     "delta": "**Cards & Payments** is $2.72m over budget in June 2026. "},
    {"type": "response.output_text.delta", "item_id": "s2", "step": 2,
     "delta": "Let me chart that."},
    {"type": "response.output_item.done", "item_id": "s2",
     "item": {"id": "s2", "type": "function_call",
              "name": "main__vista_assistant__make_chart"}},
    {"type": "response.completed"},
]

_ACTIVE = {"transcript": TRANSCRIPT, "delay": 0.0, "status": 200}


class FakeEndpoint(BaseHTTPRequestHandler):
    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        self.rfile.read(n)
        if _ACTIVE["status"] != 200:
            self.send_response(_ACTIVE["status"])
            self.end_headers()
            self.wfile.write(b"boom")
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        for ev in _ACTIVE["transcript"]:
            self.wfile.write(f"data: {json.dumps(ev)}\n\n".encode())
            self.wfile.flush()
            if _ACTIVE["delay"]:
                time.sleep(_ACTIVE["delay"])
        self.wfile.write(b"data: [DONE]\n\n")
        self.wfile.flush()

    def log_message(self, *a):
        pass


def start_fake():
    srv = HTTPServer(("127.0.0.1", 0), FakeEndpoint)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def part_a():
    print("\n=== A. supervisor.stream() semantics (fake endpoint) ===")
    srv = start_fake()
    port = srv.server_address[1]

    from backend import supervisor as sup

    sup.ENDPOINT = "fake-endpoint"

    class Cfg:
        host = f"http://127.0.0.1:{port}"

        def authenticate(self):
            return {"Authorization": "Bearer test"}

    class W:
        config = Cfg()

    sup._w = W()

    # --- with a tool call
    _ACTIVE["transcript"], _ACTIVE["delay"], _ACTIVE["status"] = TRANSCRIPT, 0.0, 200
    evs = list(sup.stream("which LOB overspent?"))
    kinds = [e["type"] for e in evs]
    text = "".join(e["text"] for e in evs if e["type"] == "chunk")

    check("emits a route event", "route" in kinds, str([e for e in evs if e["type"] == "route"]))
    check("route names the sub-agent",
          any(e.get("agent") == "fna_analytics_genie" for e in evs if e["type"] == "route"))
    check("suppresses tool-routing narration",
          "I'll query" not in text and "FnA Analytics agent to get" not in text,
          f"text={text[:70]!r}")
    check("delivers the real answer", "Cards & Payments" in text and "2.72m" in text)
    check("preserves markdown table syntax", "| Driver | Variance |" in text)
    check("ends with done", kinds[-1] == "done")
    done = evs[-1]
    check("done carries history",
          isinstance(done.get("history"), list) and len(done["history"]) >= 2)
    check("history last turn is the assistant answer",
          done["history"][-1]["role"] == "assistant"
          and "Cards & Payments" in done["history"][-1]["content"])
    # The ANSWER is deliberately a single chunk: it is only identifiable once the stream
    # closes. Progressive feedback is carried by trace events instead, which is what keeps
    # the UI alive while the agent works.
    check("answer delivered as one chunk", kinds.count("chunk") == 1,
          f"{kinds.count('chunk')} chunks")
    check("progress surfaced as trace events while working",
          kinds.count("trace") >= 2, f"{kinds.count('trace')} traces")
    check("traces arrive BEFORE the answer",
          kinds.index("trace") < kinds.index("chunk"))

    # --- no tool call: buffered text must still be released
    _ACTIVE["transcript"] = TRANSCRIPT_NO_TOOL
    evs2 = list(sup.stream("what is the 90 day rule?"))
    t2 = "".join(e["text"] for e in evs2 if e["type"] == "chunk")
    check("no-tool answer still delivered", "FIN-ACC-014" in t2, t2[:60])
    check("no-tool path ends with done", evs2[-1]["type"] == "done")

    # --- THE REAL STREAM SHAPE: sub-agent text is filtered by tool_call_id, so the user
    # never sees it and it is never retracted. This is the flicker fix.
    _ACTIVE["transcript"] = TRANSCRIPT_TOOLTEXT
    evs5 = list(sup.stream("why is cards over budget and was it approved?"))
    kinds5 = [e["type"] for e in evs5]
    visible = "".join(e["text"] for e in evs5 if e["type"] == "chunk")
    done5 = evs5[-1]
    srcs = done5.get("sources", [])

    check("NO reset events - nothing is shown then taken back",
          "reset" not in kinds5, str(kinds5))
    check("sub-agent rows never appear in the answer", "SUBAGENT_ROWS" not in visible)
    check("sub-agent document text never appears in the answer",
          "SUBAGENT_DOC" not in visible)
    check("first narration not in the answer", "I'll check the finance data" not in visible)
    check("SECOND narration (between tool calls) not in the answer",
          "Now let me check the approval documentation" not in visible,
          f"{visible[:100]!r}")
    check("answer is exactly the final synthesis",
          visible.strip().startswith("**Cards & Payments**"), f"{visible[:60]!r}")
    check("answer sent as a single chunk once identifiable",
          len([e for e in evs5 if e["type"] == "chunk"]) == 1,
          f"{len([e for e in evs5 if e['type'] == 'chunk'])} chunks")
    check("<name> element removed entirely", "<name>" not in visible
          and "FnA-Agent" not in visible)
    check("citation footnote markers stripped", "[^" not in visible)
    check("markdown table preserved", "| Driver | Variance |" in visible)
    check("both sub-agents reported as routes",
          len([e for e in evs5 if e["type"] == "route"]) == 2)

    # --- a chart returned by a UC function must be picked up from function_call_output
    charts5 = done5.get("charts", [])
    check("UC function chart spec extracted from function_call_output",
          len(charts5) == 1, f"{len(charts5)} charts")
    if charts5:
        c = charts5[0]
        mk = c.get("mark")
        check("chart spec is intact (mark + data survive the envelope)",
              (mk.get("type") if isinstance(mk, dict) else mk) == "bar"
              and len(c.get("data", {}).get("values", [])) == 1,
              str(mk))
    check("chart spec JSON never reaches the answer text",
          "vega.github.io" not in visible and "$schema" not in visible)

    # --- the working is surfaced as traces, so the user is never staring at a blank screen
    traces = [e for e in evs5 if e["type"] == "trace"]
    tkinds = {e.get("kind") for e in traces}
    ttext = " ".join(e["text"] for e in traces)
    check("trace events emitted for the working", len(traces) >= 4, f"{len(traces)} traces")
    check("traces cover thought, call and result",
          tkinds == {"thought", "call", "result"}, str(sorted(tkinds)))
    check("narration appears in the TRACE (not the answer)",
          "Now let me check the approval documentation" in ttext)
    check("sub-agent output appears in the TRACE",
          "SUBAGENT_ROWS" in ttext and "SUBAGENT_DOC" in ttext)
    check("tool calls described in business terms, not endpoint ids",
          any("finance data" in e["text"].lower() or "policy documents" in e["text"].lower()
              for e in traces if e.get("kind") == "call"),
          str([e["text"] for e in traces if e.get("kind") == "call"]))

    # --- sources assembled from annotations + the genie query
    doc = next((x for x in srcs if x["kind"] == "document"), None)
    dat = next((x for x in srcs if x["kind"] == "data"), None)
    check("a document source is reported", doc is not None)
    if doc:
        check("document title is the real filename",
              doc["title"] == "PROJ-HELIOS_Business_Case_and_Cost_Approval.pdf")
        check("document de-duplicated to one entry with both pages",
              sorted(doc["pages"]) == ["1", "5"], str(doc["pages"]))
        check("quoted passage is decoded from the deep link",
              any("Group Investment Committee" in q for q in doc["quotes"]),
              str(doc["quotes"])[:90])
        check("document url kept for click-through", doc["url"].startswith("https://"))
    check("a data source is reported with the question asked of it",
          dat is not None and any("Cards & Payments variance" in q for q in dat["quotes"]),
          str(dat)[:110] if dat else "none")

    # --- agent ends on a tool call with no closing message: must NOT error out
    _ACTIVE["transcript"] = TRANSCRIPT_NO_FINAL_MSG
    evs7 = list(sup.stream("chart the variance"))
    k7 = [e["type"] for e in evs7]
    vis7 = "".join(e["text"] for e in evs7 if e["type"] == "chunk")
    check("no-final-message does NOT return an empty-response error",
          "error" not in k7, str([e.get("error") for e in evs7 if e["type"] == "error"]))
    check("falls back to the substantive summary",
          "2.72m over budget" in vis7, f"{vis7[:80]!r}")
    check("no-final-message still ends with done", k7[-1] == "done")

    # --- endpoint error surfaces as an error event, not an exception
    _ACTIVE["transcript"] = TRANSCRIPT
    _ACTIVE["status"] = 500
    evs3 = list(sup.stream("boom"))
    check("http error becomes an error event",
          any(e["type"] == "error" for e in evs3),
          str(evs3[:1]))
    _ACTIVE["status"] = 200

    # --- unconfigured endpoint
    old = sup.ENDPOINT
    sup.ENDPOINT = ""
    evs4 = list(sup.stream("x"))
    check("missing endpoint reports an error",
          evs4 and evs4[0]["type"] == "error")
    sup.ENDPOINT = old
    srv.shutdown()


# ===================================================================== part B
STUB_APP = r'''
import time, os, sys
sys.path.insert(0, os.environ["APP_DIR"])
from backend import supervisor as sup

def slow_stream(question, history=None):
    yield {"type": "route", "agent": "fna_analytics_genie"}
    for part in ["**Cards & Payments** ", "overspent by **USD 2.72m**.\n\n",
                 "| Driver | Variance |\n", "|---|---|\n", "| Consulting | 979k |\n"]:
        time.sleep(0.12)
        yield {"type": "chunk", "text": part}
    yield {"type": "done",
           "history": [{"role": "user", "content": question},
                       {"role": "assistant", "content": "ok"}],
           "routes": ["fna_analytics_genie"]}

sup.stream = slow_stream
from backend.main import app          # noqa: E402  (import after the stub is installed)
'''


def part_b():
    print("\n=== B. /api/chat SSE wire format + progressive delivery ===")
    # Run a REAL uvicorn server: fastapi's TestClient drives the ASGI app in-process and
    # hands back the whole body, so it cannot distinguish streamed from buffered. Only a
    # real socket proves frames leave the server progressively.
    import socket

    import httpx

    with tempfile.TemporaryDirectory() as td:
        mod = os.path.join(td, "stub_app.py")
        with open(mod, "w") as f:
            f.write(STUB_APP)
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        s.close()

        env = dict(os.environ, APP_DIR=os.path.join(ROOT, "app"),
                   PYTHONPATH=td + os.pathsep + os.path.join(ROOT, "app"))
        proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "stub_app:app",
             "--host", "127.0.0.1", "--port", str(port), "--log-level", "warning"],
            cwd=td, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        try:
            base = f"http://127.0.0.1:{port}"
            for _ in range(80):
                try:
                    httpx.get(f"{base}/api/health", timeout=1.0)
                    break
                except Exception:
                    time.sleep(0.25)
            else:
                out = proc.stdout.read(1500) if proc.stdout else ""
                check("stub server started", False, out[:400])
                return

            stamps, frames = [], []
            with httpx.Client(timeout=30.0) as client:
                with client.stream("POST", f"{base}/api/chat",
                                   json={"question": "which LOB overspent?",
                                         "history": []}) as r:
                    check("status 200", r.status_code == 200)
                    check("content-type is text/event-stream",
                          "text/event-stream" in r.headers.get("content-type", ""),
                          r.headers.get("content-type", ""))
                    check("X-Accel-Buffering disabled for the proxy",
                          r.headers.get("x-accel-buffering") == "no")
                    t0 = time.time()
                    buf = ""
                    for chunk in r.iter_raw():
                        buf += chunk.decode("utf-8", "replace")
                        while "\n\n" in buf:
                            frame, buf = buf.split("\n\n", 1)
                            if frame.strip():
                                stamps.append(time.time() - t0)
                                frames.append(frame)
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()

    data_frames = [f for f in frames if f.startswith("data:")]
    evs = [json.loads(f[5:].strip()) for f in data_frames]
    kinds = [e["type"] for e in evs]

    check("frames use the `data: ` SSE prefix", len(data_frames) >= 5,
          f"{len(data_frames)} data frames")
    check("every frame is valid JSON", len(evs) == len(data_frames))
    check("route then chunks then done",
          kinds and kinds[0] == "route" and kinds[-1] == "done" and "chunk" in kinds,
          str(kinds))
    # 5 chunks x 0.12s of server-side work: if the proxy/ASGI layer buffered, every
    # frame would land at once and the span would collapse to ~0.
    span = stamps[-1] - stamps[0] if len(stamps) > 1 else 0
    check("delivery is progressive, not one buffered burst", span > 0.3,
          f"first→last frame span {span:.2f}s across {len(stamps)} frames")
    joined = "".join(e.get("text", "") for e in evs if e["type"] == "chunk")
    check("markdown survives the wire intact",
          "**USD 2.72m**" in joined and "| Driver | Variance |" in joined)


# ===================================================================== part C
JS_TESTS = r"""
const path = require('path');
const { renderMarkdown } = require(process.argv[2]);
let fails = [];
function t(label, cond, detail) {
  console.log((cond ? 'PASS  ' : 'FAIL  ') + label + (detail ? ' — ' + detail : ''));
  if (!cond) fails.push(label);
}

// table
const tbl = renderMarkdown(
  'Summary:\n\n| LOB | Variance (USD) |\n|---|---|\n| Cards & Payments | 2,722,824 |\n| Technology | 320,145 |\n\nDone.'
);
t('table -> <table class="chat-tbl">', tbl.includes('<table class="chat-tbl">'));
t('table header cell rendered', tbl.includes('<th>LOB</th>'));
t('table escapes ampersand in cell', tbl.includes('Cards &amp; Payments'));
t('numeric cell right-aligned', tbl.includes('<td class="num">2,722,824</td>'));
t('two body rows', (tbl.match(/<tr>/g) || []).length === 3, String((tbl.match(/<tr>/g)||[]).length) + ' rows incl header');
t('prose around the table kept', tbl.includes('<p>Summary:</p>') && tbl.includes('<p>Done.</p>'));
t('no raw pipes leak into output', !tbl.includes('| LOB |'));

// bold / italic / code
const em = renderMarkdown('Total **USD 2.72m** with `variance_usd` and *constant currency*.');
t('bold rendered', em.includes('<strong>USD 2.72m</strong>'));
t('inline code rendered', em.includes('<code>variance_usd</code>'));
t('italic rendered', em.includes('<em>constant currency</em>'));

// bullets + numbered
const ul = renderMarkdown('Findings:\n- six accruals over 90 days\n- total USD 1,339,800');
t('bullets -> <ul><li>', ul.includes('<ul>') && ul.includes('<li>six accruals over 90 days</li>'));
const ol = renderMarkdown('Steps:\n1. substantiate\n2. reverse');
t('numbered -> <ol><li>', ol.includes('<ol>') && ol.includes('<li>substantiate</li>'));

// An ordered list interrupted by nested bullets must CONTINUE its numbering, not restart
// at 1 (the agent writes 1..4 with a sub-list in the middle).
const split = renderMarkdown('1. first\n2. second:\n\n- sub a\n- sub b\n\n3. third\n4. fourth');
t('interrupted ordered list resumes numbering', split.includes('<ol start="3">'));
t('nested bullets still render', split.includes('<li>sub a</li>'));

// headings
t('heading rendered', renderMarkdown('## Drivers').includes('<h4>Drivers</h4>'));

// xss / escaping
const xss = renderMarkdown('<img src=x onerror=alert(1)> and <script>bad()</script>');
t('html escaped (no live tags)', !xss.includes('<img') && !xss.includes('<script>'));

// code fence
t('fenced code -> <pre><code>', renderMarkdown('```\nSELECT 1\n```').includes('<pre><code>SELECT 1'));

// a partial table (mid-stream) must not throw
let ok = true;
try { renderMarkdown('| LOB | Var |\n|---|'); } catch (e) { ok = false; }
t('partial table during streaming does not throw', ok);

if (fails.length) { console.log('\nJS FAILURES: ' + fails.join(', ')); process.exit(1); }
console.log('\nall markdown checks passed');
"""


def part_c():
    print("\n=== C. markdown renderer (real JS via node) ===")
    node = subprocess.run(["which", "node"], capture_output=True, text=True)
    if node.returncode != 0:
        check("node available for JS tests", False, "node not installed")
        return
    app_js = os.path.join(ROOT, "app", "static", "app.js")
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
        f.write(JS_TESTS)
        tf = f.name
    r = subprocess.run(["node", tf, app_js], capture_output=True, text=True)
    print(r.stdout.rstrip())
    if r.stderr.strip():
        print("  stderr:", r.stderr.strip()[:400])
    check("markdown renderer suite", r.returncode == 0)
    os.unlink(tf)


def main():
    part_a()
    part_b()
    part_c()
    print("\n" + "=" * 70)
    if FAILURES:
        print(f"{len(FAILURES)} FAILURES: {FAILURES}")
        return 1
    print("ALL STREAMING + FORMATTING TESTS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
