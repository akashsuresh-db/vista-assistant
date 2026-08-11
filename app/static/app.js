/* Vista Assistant chat UI — minimal, single-input, Accenture-themed.
 *
 * Dependency-free on purpose: a Databricks App serves static files and the workspace pypi
 * proxy is flaky, so avoiding a node build step removes a failure mode.
 *
 * Three deliberate behaviours:
 *   1. The ANSWER area only ever shows the supervisor's final synthesis. All intermediate
 *      working (narration, tool calls, sub-agent replies) goes to a collapsible greyed
 *      trace tile, so nothing shown is ever taken back.
 *   2. Correct formatting. Finance answers are tabular, so markdown tables/bold/bullets
 *      are rendered — an unrendered pipe table looks broken.
 *   3. Charts. The agent calls a Unity Catalog function that returns a Vega-Lite v6 spec;
 *      the spec is rendered here with vegaEmbed, already themed server-side.
 */

const $ = (s) => document.querySelector(s);

const state = {
  history: [],
  streaming: false,
};

/* ------------------------------------------------------------------ markdown */
function escapeHtml(s) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function inline(s) {
  let t = escapeHtml(s);
  t = t.replace(/`([^`]+)`/g, "<code>$1</code>");
  t = t.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  t = t.replace(/(^|[\s(])\*([^*\n]+)\*(?=[\s.,;:)]|$)/g, "$1<em>$2</em>");
  t = t.replace(/\[([^\]]+)\]\(([^)]+)\)/g,
    '<a href="$2" target="_blank" rel="noopener">$1</a>');
  return t;
}

function isTableRow(l) {
  return /^\s*\|.*\|\s*$/.test(l);
}
function isTableSep(l) {
  return /^\s*\|?[\s:-]*-{2,}[\s:|-]*\|?\s*$/.test(l) && l.includes("-");
}
function splitRow(l) {
  return l.trim().replace(/^\|/, "").replace(/\|$/, "").split("|").map((c) => c.trim());
}

/** Minimal block-level markdown -> HTML: tables, headings, bullets, numbered lists,
 *  fenced code and paragraphs. */
function renderMarkdown(md) {
  const lines = md.replace(/\r/g, "").split("\n");
  const out = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    if (/^\s*```/.test(line)) {
      const buf = [];
      i++;
      while (i < lines.length && !/^\s*```/.test(lines[i])) buf.push(lines[i++]);
      i++;
      out.push(`<pre><code>${escapeHtml(buf.join("\n"))}</code></pre>`);
      continue;
    }

    if (isTableRow(line) && i + 1 < lines.length && isTableSep(lines[i + 1])) {
      const head = splitRow(line);
      i += 2;
      const rows = [];
      while (i < lines.length && isTableRow(lines[i])) rows.push(splitRow(lines[i++]));
      const th = head.map((h) => `<th>${inline(h)}</th>`).join("");
      const tb = rows
        .map((r) => {
          const tds = r
            .map((c) => {
              // right-align anything that reads as money or a percentage
              const num = /^[-+(]?[$£€₹]?\s?[\d,.]+%?\)?$/.test(c.trim()) && /\d/.test(c);
              return `<td class="${num ? "num" : ""}">${inline(c)}</td>`;
            })
            .join("");
          return `<tr>${tds}</tr>`;
        })
        .join("");
      out.push(`<div class="tbl-wrap"><table class="chat-tbl"><thead><tr>${th}</tr></thead><tbody>${tb}</tbody></table></div>`);
      continue;
    }

    const h = line.match(/^(#{1,4})\s+(.*)$/);
    if (h) {
      const lvl = Math.min(h[1].length + 2, 6);
      out.push(`<h${lvl}>${inline(h[2])}</h${lvl}>`);
      i++;
      continue;
    }

    if (/^\s*[-*•]\s+/.test(line)) {
      const items = [];
      while (i < lines.length && /^\s*[-*•]\s+/.test(lines[i])) {
        items.push(inline(lines[i].replace(/^\s*[-*•]\s+/, "")));
        i++;
      }
      out.push(`<ul>${items.map((x) => `<li>${x}</li>`).join("")}</ul>`);
      continue;
    }

    if (/^\s*\d+[.)]\s+/.test(line)) {
      const items = [];
      // Keep the author's own numbers. An ordered list is often interrupted by a nested
      // bullet list or a paragraph, which would otherwise start a fresh <ol> at 1 —
      // producing "1. 1. 1." for what the model wrote as 1., 2., 3.
      const first = parseInt(line.match(/^\s*(\d+)/)[1], 10);
      while (i < lines.length && /^\s*\d+[.)]\s+/.test(lines[i])) {
        items.push(inline(lines[i].replace(/^\s*\d+[.)]\s+/, "")));
        i++;
      }
      const startAttr = first > 1 ? ` start="${first}"` : "";
      out.push(`<ol${startAttr}>${items.map((x) => `<li>${x}</li>`).join("")}</ol>`);
      continue;
    }

    if (!line.trim()) {
      i++;
      continue;
    }

    const buf = [];
    while (
      i < lines.length &&
      lines[i].trim() &&
      !isTableRow(lines[i]) &&
      !/^\s*[-*•]\s+/.test(lines[i]) &&
      !/^\s*\d+[.)]\s+/.test(lines[i]) &&
      !/^(#{1,4})\s+/.test(lines[i]) &&
      !/^\s*```/.test(lines[i])
    ) {
      buf.push(lines[i++]);
    }
    out.push(`<p>${inline(buf.join(" "))}</p>`);
  }
  return out.join("\n");
}

/* --------------------------------------------------------------------- chat */
function addMsg(role, html) {
  const wrap = document.createElement("div");
  wrap.className = `msg ${role}`;
  const body = document.createElement("div");
  body.className = "body";
  body.innerHTML = html;
  wrap.append(body);
  $("#thread").append(wrap);
  scrollDown();
  return body;
}

function scrollDown() {
  const st = $("#stage");
  st.scrollTop = st.scrollHeight;
}

function waitingDots() {
  return '<div class="thinking"><span></span><span></span><span></span></div>';
}

/* ---------------------------------------------------------------------- trace */
/** The live "working" tile. The supervisor's narration, its tool calls and each
 *  sub-agent's raw reply stream in here, greyed and de-emphasised, so the user can watch
 *  progress without mistaking any of it for the answer. Open while working, collapsed once
 *  the answer lands — but always available to expand. */
function makeTrace() {
  const wrap = document.createElement("details");
  wrap.className = "trace";
  wrap.open = true;
  wrap.innerHTML =
    '<summary><span class="trace-live"></span>' +
    '<span class="trace-label">Working…</span></summary>' +
    '<div class="trace-body"></div>';
  return wrap;
}

const TRACE_PREFIX = { call: "→ ", result: "← ", thought: "" };

function appendTrace(traceEl, kind, text) {
  const body = traceEl.querySelector(".trace-body");
  const last = body.lastElementChild;
  // Consecutive events of the same kind belong to one streamed passage, so append to the
  // existing line rather than making a new one per token.
  if (last && last.dataset.kind === kind && kind !== "call") {
    last.textContent += text;
  } else {
    const line = document.createElement("div");
    line.className = `trace-line trace-${kind}`;
    line.dataset.kind = kind;
    line.textContent = (TRACE_PREFIX[kind] || "") + text;
    body.append(line);
  }
  body.scrollTop = body.scrollHeight;
}

function settleTrace(traceEl, steps) {
  if (!traceEl) return;
  traceEl.open = false;
  traceEl.classList.add("done");
  const label = traceEl.querySelector(".trace-label");
  const live = traceEl.querySelector(".trace-live");
  if (live) live.remove();
  if (label) {
    label.textContent = steps
      ? `How this was answered (${steps} step${steps === 1 ? "" : "s"})`
      : "How this was answered";
  }
}

/* --------------------------------------------------------------------- charts */
/** Render the Vega-Lite specs the make_chart UC function returned.
 *  The spec already carries the Accenture palette and typography (set server-side in the
 *  UC function) so nothing is re-themed here — we only size it to the container and turn
 *  off the actions menu. */
function renderCharts(container, charts) {
  if (!charts || !charts.length) return;
  if (typeof vegaEmbed === "undefined") {
    // vendored bundle missing: say so rather than failing silently
    const warn = document.createElement("p");
    warn.className = "chart-err";
    warn.textContent = "Chart could not be displayed (visualisation library unavailable).";
    container.append(warn);
    return;
  }
  charts.forEach((spec) => {
    const holder = document.createElement("div");
    holder.className = "chart";
    container.append(holder);

    // width:"container" makes Vega measure the holder, but it measures it BEFORE the
    // surrounding flex layout has settled, so it computes a plot area that leaves no room
    // for the y-axis labels — they then render on top of the bars. Measuring the holder
    // ourselves and passing a concrete pixel width removes the race entirely.
    const measured = Math.max(
      320, Math.floor(holder.getBoundingClientRect().width) || 680);
    const sized = { ...spec, width: measured };

    vegaEmbed(holder, sized, {
      actions: { export: true, source: false, compiled: false, editor: false },
      renderer: "canvas",
    })
      .then((res) => {
        // keep it responsive: re-render at the new width when the column changes size
        if (typeof ResizeObserver === "undefined") return;
        let last = measured;
        const ro = new ResizeObserver(() => {
          const w = Math.floor(holder.getBoundingClientRect().width);
          if (w > 320 && Math.abs(w - last) > 24) {
            last = w;
            res.view.width(w - 0).runAsync();
          }
        });
        ro.observe(holder);
      })
      .catch((e) => {
        holder.className = "chart-err";
        holder.textContent = `Chart could not be displayed (${e.message || e}).`;
      });
  });
}

/* -------------------------------------------------------------------- sources */
/** Render the provenance panel: which documents (with page + quoted passage) and which
 *  dataset the answer was grounded in. Collapsed by default — the answer is the point. */
function renderSources(sources) {
  if (!sources || !sources.length) return "";
  const n = sources.length;
  const items = sources
    .map((s) => {
      const isDoc = s.kind === "document";
      const label = isDoc ? "Document" : "Data";
      const title = escapeHtml(s.title || "");
      const titleHtml = s.url
        ? `<a href="${escapeHtml(s.url)}" target="_blank" rel="noopener">${title}</a>`
        : title;
      const pages = (s.pages || []).length
        ? `page ${(s.pages || []).join(", ")}`
        : "";
      const quotes = (s.quotes || [])
        .map((q) => `<p class="src-quote">${escapeHtml(q)}</p>`)
        .join("");
      return `<div class="src">
        <div class="src-head">
          <span class="src-kind">${label}</span>
          <span class="src-title">${titleHtml}</span>
          ${pages ? `<span class="src-meta">${escapeHtml(pages)}</span>` : ""}
        </div>${quotes}
      </div>`;
    })
    .join("");
  return `<details class="sources">
    <summary>Sources (${n})</summary>${items}
  </details>`;
}

/* ------------------------------------------------------------------- starters */
const STARTERS = [
  { kind: "Finance data", q: "Which line of business overspent the most in June 2026?" },
  { kind: "Policy", q: "What must happen to an accrual open more than 90 days?" },
  { kind: "Data + policy", q: "Why is Cards & Payments over budget, and was the spend approved?" },
  { kind: "Finance data", q: "How much of the MB-UK variance is FX translation rather than real overspend?" },
  { kind: "Data + policy", q: "Which accruals breach the 90-day policy, and what must I do about them?" },
  { kind: "Finance data", q: "Which close tasks missed their SLA in June 2026?" },
];

async function ask(question) {
  const q = (question || "").trim();
  if (state.streaming || !q) return;

  state.streaming = true;
  $("#send").disabled = true;
  $("#q").value = "";
  $("#q").style.height = "auto";
  document.body.classList.add("chatting");

  addMsg("user", `<p>${inline(q)}</p>`);
  const body = addMsg("assistant", "");

  // The trace tile is a real element (not innerHTML) so it survives the final render and
  // keeps whatever the user expanded or collapsed.
  const traceEl = makeTrace();
  const answerEl = document.createElement("div");
  answerEl.className = "answer";
  answerEl.innerHTML = waitingDots();
  body.append(traceEl, answerEl);
  scrollDown();

  let raw = "";
  let sources = [];
  let charts = [];
  let toolCalls = 0;

  const finish = (err) => {
    state.streaming = false;
    $("#send").disabled = false;
    settleTrace(traceEl, toolCalls);
    if (err) {
      // Leave the working tile OPEN on failure: it holds whatever the agent did manage to
      // produce, which is far more useful than a bare error message.
      traceEl.open = true;
      answerEl.innerHTML =
        `<p class="err">${inline(err)}</p>` +
        '<p class="err-hint">The steps the agent took are shown above.</p>';
    } else {
      answerEl.innerHTML = renderMarkdown(raw.trim() || "_No answer was returned._");
      // charts sit between the prose and the provenance panel
      renderCharts(answerEl, charts);
      answerEl.insertAdjacentHTML("beforeend", renderSources(sources));
    }
    scrollDown();
    $("#q").focus();
  };

  try {
    const resp = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: q, history: state.history }),
    });
    if (!resp.ok || !resp.body) {
      finish(`Request failed (${resp.status}).`);
      return;
    }

    const reader = resp.body.getReader();
    const dec = new TextDecoder();
    let buf = "";

    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });

      // SSE frames are separated by a blank line
      const frames = buf.split("\n\n");
      buf = frames.pop() ?? "";

      for (const frame of frames) {
        const dataLine = frame.split("\n").find((l) => l.startsWith("data:"));
        if (!dataLine) continue;
        let ev;
        try {
          ev = JSON.parse(dataLine.slice(5).trim());
        } catch {
          continue;
        }

        if (ev.type === "trace") {
          if (ev.kind === "call") toolCalls += 1;
          appendTrace(traceEl, ev.kind, ev.text);
          scrollDown();
        } else if (ev.type === "chunk") {
          // The answer arrives as one chunk once the stream closes — it is only
          // identifiable then. Progress was visible in the trace tile meanwhile.
          raw += ev.text;
        } else if (ev.type === "done") {
          state.history = ev.history || state.history;
          sources = ev.sources || [];
          charts = ev.charts || [];
          finish(null);
          return;
        } else if (ev.type === "error") {
          finish(ev.error);
          return;
        }
        // 'route' events are intentionally ignored: which specialist agent answered is
        // an implementation detail the business user should not see. The backend now
        // classifies sub-agent output by tool_call_id, so no 'reset' handling is needed —
        // nothing is ever shown that has to be taken back.
      }
    }
    finish(null);
  } catch (e) {
    finish(String(e));
  }
}

/* --------------------------------------------------------------------- init */
function init() {
  const box = $("#q");

  const grid = $("#starters-grid");
  if (grid) {
    STARTERS.forEach((s) => {
      const b = document.createElement("button");
      b.className = "starter";
      b.innerHTML = `<em>${escapeHtml(s.kind)}</em>${escapeHtml(s.q)}`;
      b.onclick = () => ask(s.q);
      grid.append(b);
    });
  }

  const autosize = () => {
    box.style.height = "auto";
    box.style.height = Math.min(box.scrollHeight, 168) + "px";
  };

  $("#send").onclick = () => ask(box.value);
  box.addEventListener("input", autosize);
  box.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      ask(box.value);
    }
  });
  box.focus();
}

// exported for the unit tests
if (typeof module !== "undefined") module.exports = { renderMarkdown, inline };
if (typeof window !== "undefined") { window.renderMarkdown = renderMarkdown; init(); }
