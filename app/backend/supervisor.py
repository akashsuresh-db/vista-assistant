"""Streaming client for the Agent Bricks Supervisor (multi-agent) endpoint.

The endpoint is task type `agent/v1/responses`. Three things matter for a clean UX:

1. TRUE streaming. The SDK's api_client.do() buffers the whole body, so we use
   `requests` with stream=True and forward `response.output_text.delta` events as they
   arrive. Without this the user waits ~45s then gets everything at once.

2. SEPARATING THE ANSWER FROM THE WORKING. The stream interleaves three kinds of text:

     a. the supervisor's routing narration ("I'll check the finance data...", and again
        "Now let me check the approval documentation" BETWEEN tool calls);
     b. each sub-agent's raw reply — identifiable immediately because those deltas carry
        `tool_call_id` / `tool_name`, which supervisor-authored text never does;
     c. the supervisor's final synthesis — indistinguishable from (a) while it streams.

   Because (a) recurs between tool calls, "text after a tool call is the answer" is wrong:
   it admits the second narration. Nothing in an individual delta says "this is final", so
   the ONLY reliable signal is ordering — the last supervisor-authored item wins.

   Therefore: every delta is emitted as a `trace` event (shown live in a collapsible,
   greyed "thinking" tile so the user is never staring at a blank screen), supervisor text
   is buffered per item_id, and when the stream closes the highest-`step` buffered item is
   emitted once as the `chunk` that becomes the answer. Nothing is ever retracted.

3. SOURCES. `response.output_text.annotation.added` events carry url_citation annotations
   with a document `title` and a deep link (`#page=N:~:text=...`) into the UC Volume file.
   We de-duplicate these and send them with the final `done` event so the UI can show what
   the answer was grounded in. Genie tool calls carry no annotations, so for those we
   record the question that was put to the data instead.
"""
from __future__ import annotations

import json
import os
import re
from typing import Iterator
from urllib.parse import unquote

import requests
from databricks.sdk import WorkspaceClient

ENDPOINT = os.environ.get("SUPERVISOR_ENDPOINT", "")
MAX_HISTORY_TURNS = 8

# Endpoint and space ids are meaningless to a business user, so the data source is
# described by what it actually is.
GENIE_LABEL = "Finance data — ledger, budget, accruals, payables, close tracker"

_w: WorkspaceClient | None = None


def _client() -> WorkspaceClient:
    global _w
    if _w is None:
        profile = os.environ.get("DATABRICKS_PROFILE")
        # In a deployed App the SP credentials come from the environment; locally we
        # fall back to a named CLI profile.
        _w = WorkspaceClient(profile=profile) if profile else WorkspaceClient()
    return _w


def _endpoint_url(w: WorkspaceClient) -> str:
    host = w.config.host.rstrip("/")
    return f"{host}/serving-endpoints/{ENDPOINT}/invocations"


def _build_input(question: str, history: list[dict] | None) -> list[dict]:
    """The responses API is stateless, so prior turns are replayed each call."""
    msgs: list[dict] = []
    for turn in (history or [])[-MAX_HISTORY_TURNS:]:
        role, content = turn.get("role"), turn.get("content")
        if role in ("user", "assistant") and content:
            msgs.append({"role": role, "content": content})
    msgs.append({"role": "user", "content": question})
    return msgs


# The supervisor wraps delegated output in a name tag, e.g.
# "<name>fna-knowledge-assistant</name>". Remove the WHOLE element, tags and the agent
# name inside them - stripping only the angle brackets would leave the name in the prose.
_NAME_EL = re.compile(r"<name>.*?</name>", re.I | re.S)
# any other stray pseudo-tag
_TAG = re.compile(r"</?[a-z0-9_\-]{2,40}>", re.I)
# Footnote markers the knowledge assistant leaves behind, e.g. [^nAI8-1]
_FOOTNOTE = re.compile(r"\[\^[A-Za-z0-9\-]+\]")


def _clean(text: str) -> str:
    return _FOOTNOTE.sub("", _TAG.sub("", _NAME_EL.sub("", text)))


def _is_genie(name: str) -> bool:
    return "genie" in (name or "").lower()


def _is_chart_tool(name: str) -> bool:
    return "make_chart" in (name or "").lower()


def _tool_label(name: str) -> str:
    """What to show the user when a tool is invoked.

    Must be derived from the tool, not assumed: an earlier version labelled everything
    that was not Genie as "Searching the policy documents", so a chart call was reported
    as a document search.
    """
    n = (name or "").lower()
    if _is_genie(n):
        return "Querying the finance data"
    if _is_chart_tool(n):
        return "Rendering visuals"
    if "knowledge" in n or n.startswith("ka-") or "-ka-" in n:
        return "Searching the policy documents"
    # unknown tool: name it plainly rather than guessing what it does
    pretty = (name or "tool").split("__")[-1].replace("_", " ").strip()
    return f"Running {pretty}" if pretty else "Running a tool"


def _quoted_text(url: str) -> str:
    """Pull the highlighted snippet out of a `#...:~:text=` deep link."""
    if ":~:text=" not in url:
        return ""
    return " ".join(unquote(url.split(":~:text=", 1)[1]).split())


def _page_of(url: str) -> str:
    m = re.search(r"#page=(\d+)", url)
    return m.group(1) if m else ""


# A Vega-Lite spec returned by the make_chart UC function. It arrives inside a tool
# result, often wrapped in prose or a fenced block, so it is located by its schema marker
# and then extracted by brace matching (a regex cannot balance braces).
_VL_MARKER = "vega.github.io/schema/vega-lite"


def _extract_vega_specs(text: str) -> list[dict]:
    """Pull every Vega-Lite spec out of a blob of text."""
    specs: list[dict] = []
    pos = 0
    while True:
        marker = text.find(_VL_MARKER, pos)
        if marker == -1:
            return specs
        start = text.rfind("{", 0, marker)
        if start == -1:
            return specs
        depth, in_str, esc, end = 0, False, False, -1
        for i, ch in enumerate(text[start:], start):
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
                continue
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        if end == -1:
            return specs
        try:
            spec = json.loads(text[start:end])
            # only accept a real spec: it must have data and something to draw
            if isinstance(spec, dict) and "$schema" in spec and (
                    "mark" in spec or "layer" in spec or "encoding" in spec):
                specs.append(spec)
        except json.JSONDecodeError:
            pass
        pos = max(end, marker + len(_VL_MARKER))


def _strip_vega_blocks(text: str) -> str:
    """Remove any Vega-Lite spec the model pasted into its prose.

    The chart is rendered from the extracted spec, so leaving the raw JSON in the answer
    just shows the reader a wall of braces. Handles both a fenced ```json block and a bare
    object, and tidies up the empty fence left behind."""
    out = text
    for spec in _extract_vega_specs(text):
        blob = json.dumps(spec)
        # the spec in the text may be formatted differently, so locate it structurally
        marker = out.find(_VL_MARKER)
        while marker != -1:
            start = out.rfind("{", 0, marker)
            if start == -1:
                break
            depth, in_str, esc, end = 0, False, False, -1
            for i, ch in enumerate(out[start:], start):
                if in_str:
                    if esc:
                        esc = False
                    elif ch == "\\":
                        esc = True
                    elif ch == '"':
                        in_str = False
                    continue
                if ch == '"':
                    in_str = True
                elif ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        break
            if end == -1:
                break
            out = out[:start] + out[end:]
            marker = out.find(_VL_MARKER)
        del blob
    # collapse the leftovers: empty fences and runs of blank lines
    out = re.sub(r"```(?:json|vega-lite|vega)?\s*```", "", out)
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out.strip()


def stream(question: str, history: list[dict] | None = None) -> Iterator[dict]:
    """Yield dicts: {'type': 'trace'|'chunk'|'route'|'done'|'error', ...}.

    'trace'  live working - the supervisor's narration, the tool calls it makes and each
             sub-agent's raw reply. `kind` is 'thought' | 'call' | 'result'. The UI shows
             these in a collapsible greyed tile while the answer is being worked out.
    'chunk'  the finished answer, sent once when the stream closes.
    'route'  which sub-agent was engaged (kept for diagnostics; the UI ignores it).
    'done'   conversation history + a de-duplicated `sources` list.
    """
    if not ENDPOINT:
        yield {"type": "error", "error": "SUPERVISOR_ENDPOINT is not configured"}
        return

    w = _client()
    try:
        headers = w.config.authenticate()
    except Exception as e:
        yield {"type": "error", "error": f"auth failed: {e}"}
        return
    headers = dict(headers)
    headers["Content-Type"] = "application/json"

    payload = {"input": _build_input(question, history), "stream": True}

    buffers: dict[str, str] = {}    # item_id -> supervisor text, pending classification
    # Same text, but never pruned when an item turns out to be narration. Used only as a
    # last-resort fallback when the agent ends on a tool call and writes no closing
    # message, so the user gets the substance instead of an "empty response" error.
    buffers_all: dict[str, str] = {}
    tool_items: set[str] = set()    # items that are sub-agent output (carry tool_call_id)
    suppressed: set[str] = set()    # items proven to be routing narration
    steps: dict[str, int] = {}      # item_id -> step, to pick the final synthesis
    full_answer: list[str] = []
    routes: list[str] = []
    docs: dict[str, dict] = {}      # title -> source record (de-duplicated)
    data_queries: list[str] = []
    events_seen = 0                 # SSE events parsed, for diagnostics on an empty answer
    charts: list[dict] = []         # Vega-Lite specs returned by the make_chart function
    chart_seen: set[str] = set()
    tool_text: dict[str, str] = {}  # item_id -> raw tool output, scanned for chart specs

    try:
        with requests.post(_endpoint_url(w), headers=headers, json=payload,
                           stream=True, timeout=(15, 300)) as r:
            if r.status_code != 200:
                body = r.text[:600]
                print(f"[supervisor] endpoint {r.status_code}: {body}", flush=True)
                yield {"type": "error",
                       "error": f"endpoint {r.status_code}: {body[:300]}"}
                return

            for raw in r.iter_lines(decode_unicode=True):
                if not raw:
                    continue
                line = raw.strip()
                if line.startswith("data:"):
                    line = line[5:].strip()
                if not line or line == "[DONE]":
                    continue
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    continue
                events_seen += 1
                # An Agent Bricks config error (e.g. a tool the agent cannot access)
                # arrives as a single non-stream JSON body, not an SSE event stream.
                # Surface it verbatim - it is by far the most useful thing to show.
                if events_seen == 1 and isinstance(ev, dict) and ev.get("error_code"):
                    msg = ev.get("message") or str(ev)
                    print(f"[supervisor] agent config error: {msg[:400]}", flush=True)
                    yield {"type": "error", "error": f"Agent error: {msg[:400]}"}
                    return

                etype = ev.get("type", "")

                # ------------------------------------------------ source citations
                if etype.endswith("output_text.annotation.added"):
                    ann = ev.get("annotation") or {}
                    if ann.get("type") == "url_citation" and ann.get("title"):
                        url = ann.get("url", "")
                        rec = docs.setdefault(ann["title"], {
                            "kind": "document",
                            "title": ann["title"],
                            "url": url,
                            "pages": [],
                            "quotes": [],
                        })
                        page = _page_of(url)
                        if page and page not in rec["pages"]:
                            rec["pages"].append(page)
                        q = _quoted_text(url)
                        if q and len(rec["quotes"]) < 3:
                            rec["quotes"].append(q[:280])
                    continue

                # ------------------------- a UC function returned (not a sub-agent)
                # Sub-agent replies stream as text deltas carrying tool_call_id, but a UC
                # function's result arrives ONCE as a `function_call_output` item whose
                # `output` is the Statement-Execution envelope
                # {"columns":[...],"rows":[[<value>]]}. Nothing streams for it, so it has to
                # be picked up here or the chart spec is silently lost.
                if (ev.get("item") or {}).get("type") == "function_call_output":
                    item = ev.get("item") or {}
                    out = item.get("output")
                    blob = out if isinstance(out, str) else json.dumps(out)
                    # unwrap the envelope so the spec, not the wrapper, is what we scan
                    try:
                        env = json.loads(blob)
                        if isinstance(env, dict) and "rows" in env:
                            cells = [str(c) for row in (env.get("rows") or [])
                                     for c in (row if isinstance(row, list) else [row])]
                            blob = "\n".join(cells)
                    except (json.JSONDecodeError, TypeError):
                        pass
                    key = f"__fco__{item.get('call_id') or len(tool_text)}"
                    tool_text[key] = blob
                    name = item.get("name") or ""
                    label = ("Visual rendered" if _is_chart_tool(name)
                             else f"{name.split('__')[-1] or 'tool'} returned")
                    yield {"type": "trace", "kind": "result",
                           "text": f"{label} ({len(blob)} chars)"}
                    continue

                # ------------------------------------------------ a sub-agent is called
                if "function_call" in etype or (ev.get("item") or {}).get("type") == "function_call":
                    item = ev.get("item") or {}
                    iid = ev.get("item_id") or item.get("id")
                    if iid:
                        # this item's text was routing narration, not the answer
                        suppressed.add(iid)
                        buffers.pop(iid, None)
                    name = item.get("name") or ev.get("name") or ""
                    if name and name not in routes:
                        routes.append(name)
                        yield {"type": "route", "agent": name}
                    if name:
                        yield {"type": "trace", "kind": "call", "text": _tool_label(name)}
                    if _is_genie(name):
                        # Genie returns no citations, so record WHAT was asked of the data.
                        try:
                            args = json.loads(item.get("arguments") or "{}")
                        except json.JSONDecodeError:
                            args = {}
                        q = args.get("genie_query") or args.get("query") or ""
                        if q and q not in data_queries:
                            data_queries.append(q)
                    continue

                # ------------------------------------------------ streaming text
                if etype.endswith("output_text.delta"):
                    iid = ev.get("item_id", "_")
                    delta = ev.get("delta") or ""
                    if not delta:
                        continue

                    # A sub-agent's or tool's reply: shown as a trace, never as the
                    # answer. Chart specs arrive here, so accumulate the raw text per item
                    # and extract any spec once it is complete.
                    if ev.get("tool_call_id") or ev.get("tool_name") or iid in tool_items:
                        tool_items.add(iid)
                        tool_text[iid] = tool_text.get(iid, "") + delta
                        yield {"type": "trace", "kind": "result", "text": _clean(delta)}
                        continue

                    if ev.get("step") is not None:
                        steps[iid] = ev["step"]

                    # Everything the supervisor writes goes out as a TRACE only.
                    # While a delta is arriving we cannot tell narration ("Now let me check
                    # the approval documentation") from the final synthesis: narration
                    # appears before the first tool call AND between tool calls. The only
                    # reliable signal is which item comes LAST, so every item is buffered
                    # and the winner is chosen after the stream closes.
                    buffers[iid] = buffers.get(iid, "") + delta
                    buffers_all[iid] = buffers_all.get(iid, "") + delta
                    yield {"type": "trace", "kind": "thought", "text": _clean(delta)}
                    continue

                # An item finishing tells us nothing reliable: the endpoint reports the
                # narration item done TWICE, first as "message" and only then as
                # "function_call". Classification happens above instead.

        # The answer is the last supervisor-authored item still pending. Prefer the
        # highest `step` if several remain (the synthesis always carries the highest).
        candidates = [(steps.get(i, 0), i, t) for i, t in buffers.items()
                      if t and i not in suppressed and i not in tool_items]
        if candidates:
            candidates.sort()
            full_answer.append(candidates[-1][2])
        else:
            # Every message item turned out to be narration (each one resolved into a
            # function_call) - i.e. the agent ended on a tool call and never wrote a
            # closing message. Rather than telling the user "empty response" and throwing
            # away work that did happen, fall back to the LAST narration item, which in
            # this shape is the substantive summary the agent wrote before its final call.
            fallback = [(steps.get(i, 0), i, t) for i, t in buffers_all.items()
                        if t and i not in tool_items]
            if fallback:
                fallback.sort()
                full_answer.append(fallback[-1][2])
            else:
                detail = (f"no text received (events={events_seen}, "
                          f"tool_items={len(tool_items)}, routes={len(routes)})")
                print(f"[supervisor] empty answer for {question[:60]!r}: {detail}",
                      flush=True)
                yield {"type": "error",
                       "error": "The agent did not return an answer. " + detail}
                return

    except requests.Timeout:
        yield {"type": "error", "error": "the agent timed out - please retry"}
        return
    except Exception as e:
        print(f"[supervisor] {type(e).__name__}: {e}", flush=True)
        yield {"type": "error", "error": f"{type(e).__name__}: {e}"}
        return

    # Harvest chart specs from the tool outputs. Also scan the answer, in case the model
    # pasted the spec into its prose rather than leaving it in the tool result.
    for blob in list(tool_text.values()) + ["".join(full_answer)]:
        if _VL_MARKER not in blob:
            continue
        for spec in _extract_vega_specs(blob):
            key = json.dumps(spec.get("data", {}), sort_keys=True)[:400] + str(spec.get("mark"))
            if key not in chart_seen:
                chart_seen.add(key)
                charts.append(spec)

    answer = _clean("".join(full_answer)).strip()
    # If the model echoed the spec into the answer, strip it: the chart is rendered
    # separately and a wall of JSON in the prose is unreadable.
    if _VL_MARKER in answer:
        answer = _strip_vega_blocks(answer)
    # The answer is sent as ONE chunk at the end: it is only identifiable once the stream
    # has closed, so there is nothing to stream progressively without risking narration.
    # The user is not left staring at a blank screen - the trace tile fills live meanwhile.
    if answer:
        yield {"type": "chunk", "text": answer}

    sources = list(docs.values())
    if data_queries:
        sources.append({
            "kind": "data",
            "title": GENIE_LABEL,
            "url": "",
            "pages": [],
            "quotes": data_queries[:3],
        })

    new_history = (history or []) + [
        {"role": "user", "content": question},
        {"role": "assistant", "content": answer},
    ]
    yield {"type": "done",
           "history": new_history[-MAX_HISTORY_TURNS:],
           "routes": routes,
           "sources": sources,
           "charts": charts}


def ask(question: str, history: list[dict] | None = None) -> dict:
    """Non-streaming convenience wrapper, used by the tests."""
    text, routes, sources, charts, err = [], [], [], [], None
    for ev in stream(question, history):
        if ev["type"] == "chunk":
            text.append(ev["text"])
        elif ev["type"] == "route":
            routes.append(ev["agent"])
        elif ev["type"] == "done":
            sources = ev.get("sources", [])
            charts = ev.get("charts", [])
        elif ev["type"] == "error":
            err = ev["error"]
    return {"answer": "".join(text).strip(), "routes": routes,
            "sources": sources, "charts": charts, "error": err}
