#!/usr/bin/env python3
"""Render the Vista Assistant reference architecture to PNG (matplotlib, no extra deps).

Layout is computed in a simple grid rather than hand-placed: box heights are derived
from their line counts so text can never overflow its container.

Left-to-right: sources -> Unity Catalog storage -> agent layer -> app -> user, with a
Unity Catalog governance band underneath and a numbered request walkthrough.
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.patheffects as pe                              # noqa: E402
import matplotlib.pyplot as plt                                  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch    # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "architecture.png")

NAVY, ACCENT, GREEN, PURPLE = "#0B2545", "#1B6CA8", "#0F7B55", "#6B3F86"
INK, INK2, LINE, SOFT = "#14181F", "#4C5666", "#CBD5E0", "#EDF2F7"

# geometry, in figure fractions
TITLE_H = 10.0      # title font
BODY_H = 8.0        # body font
PAD_TOP = 0.046     # gap from box top to the title baseline
LINE_GAP = 0.034    # vertical gap between body lines
PAD_BOT = 0.024     # gap below the last line


def box_height(n_lines: int) -> float:
    return PAD_TOP + 0.030 + n_lines * LINE_GAP + PAD_BOT


def box(ax, x, y_top, w, title, lines, edge=LINE, face="white", tcol=NAVY, lw=1.3):
    """Draw a box whose height fits its content. y_top is the TOP edge.
    Returns (y_bottom, y_center)."""
    h = box_height(len(lines))
    y = y_top - h
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.008,rounding_size=0.014",
        linewidth=lw, edgecolor=edge, facecolor=face, zorder=3))
    ax.text(x + w / 2, y_top - PAD_TOP, title, ha="center", va="center",
            fontsize=TITLE_H, fontweight="bold", color=tcol, zorder=4)
    for i, ln in enumerate(lines):
        ax.text(x + w / 2, y_top - PAD_TOP - 0.032 - i * LINE_GAP, ln,
                ha="center", va="center", fontsize=BODY_H, color=INK2, zorder=4)
    return y, y - h / 2 + h / 2 if False else (y + h / 2)


def arrow(ax, p1, p2, label=None, col=ACCENT, rad=0.0, lw=1.6):
    ax.add_patch(FancyArrowPatch(
        p1, p2, arrowstyle="-|>", mutation_scale=14, linewidth=lw, color=col,
        zorder=2, connectionstyle=f"arc3,rad={rad}",
        shrinkA=2, shrinkB=3))
    if label:
        ax.text((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2 + 0.022, label,
                ha="center", va="bottom", fontsize=7.4, color=col,
                fontweight="bold", zorder=5,
                path_effects=[pe.withStroke(linewidth=3.4, foreground="white")])


fig, ax = plt.subplots(figsize=(17, 9.2), dpi=170)
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")
fig.patch.set_facecolor("white")

# ------------------------------------------------------------------- heading
ax.text(0.010, 0.985, "Vista Assistant — reference architecture",
        fontsize=16, fontweight="bold", color=NAVY, va="top")
ax.text(0.010, 0.945,
        "One chat entry point for Finance & Accounting. A supervisor agent routes each "
        "question to the specialist that can answer it. No data movement.",
        fontsize=9.4, color=INK2, va="top")

# ------------------------------------------------------------------- columns
COLS = [(0.010, 0.148, "SOURCE SYSTEMS"),
        (0.196, 0.196, "UNITY CATALOG"),
        (0.436, 0.190, "AGENT LAYER · Agent Bricks"),
        (0.676, 0.146, "ORCHESTRATION"),
        (0.856, 0.134, "CONSUMPTION")]
for x, w, t in COLS:
    ax.text(x + w / 2, 0.898, t, fontsize=8.2, fontweight="bold",
            color=ACCENT, ha="center", va="center")

TOP = 0.878

# ------------------------------------------------------------------- sources
x0, w0 = COLS[0][0], COLS[0][1]
b_erp, _ = box(ax, x0, TOP, w0, "ERP / GL",
               ["SAP S/4 general ledger", "trial balance", "AP / AR sub-ledgers"])
b_plan, _ = box(ax, x0, b_erp - 0.030, w0, "Planning",
                ["annual operating plan", "AOP_2026_v3", "latest re-forecast"])
b_doc, _ = box(ax, x0, b_plan - 0.030, w0, "Documents",
               ["policy PDFs", "SOPs, audit memos", "board decks (PPTX)"])

# --------------------------------------------------------------- unity catalog
x1, w1 = COLS[1][0], COLS[1][1]
b_tab, _ = box(ax, x1, TOP, w1, "Delta tables + views",
               ["11 tables · 5 views",
                "fact_gl_balance  22,716 rows",
                "fact_budget  22,716 rows",
                "v_opex_variance encodes the",
                "budget join, the variance sign",
                "convention and the FX split"],
               edge=ACCENT, face="#F5F9FC")
b_vol, _ = box(ax, x1, b_tab - 0.042, w1, "UC Volume",
               ["/<volume>/policies",
                "8 documents",
                "5 PDF · 1 DOCX · 1 PPTX",
                "FIN-ACC-014 · FIN-FX-007",
                "FIN-IC-021 · FSSC-SOP-002",
                "Helios case · IA-2026-11"],
               edge=GREEN, face="#F4F9F6")

# --------------------------------------------------------------------- agents
x2, w2 = COLS[2][0], COLS[2][1]
b_genie, c_genie = box(ax, x2, TOP, w2, "Genie space",
                       ["natural language → SQL",
                        "10 tables / views attached",
                        "10 example question→SQL",
                        "8 benchmarks · 8 measures",
                        "instruction-tuned for the",
                        "variance sign convention"],
                       edge=ACCENT, face="#F5F9FC")
b_ka, c_ka = box(ax, x2, b_genie - 0.042, w2, "Knowledge Assistant",
                 ["document Q&A over the Volume",
                  "chunk + index + retrieve",
                  "returns cited passages",
                  "its description drives routing"],
                 edge=GREEN, face="#F4F9F6")

# ----------------------------------------------------------------- supervisor
x3, w3 = COLS[3][0], COLS[3][1]
sup_lines = ["multi-agent router", "",
             "numbers  →  Genie",
             "rules  →  Knowledge",
             "why  →  both", "",
             "synthesises one grounded answer"]
sup_h = box_height(len(sup_lines))
sup_top = TOP - 0.115
b_sup, c_sup = box(ax, x3, sup_top, w3, "Supervisor", sup_lines,
                   edge=PURPLE, face="#FAF6FC", tcol=PURPLE, lw=1.8)

# --------------------------------------------------------------- app and user
x4, w4 = COLS[4][0], COLS[4][1]
b_app, c_app = box(ax, x4, TOP, w4, "Databricks App",
                   ["FastAPI backend", "SSE token streaming",
                    "runs as a service principal"],
                   edge=NAVY, face=SOFT)
b_user, c_user = box(ax, x4, b_app - 0.055, w4, "Finance analyst",
                     ["one chat interface", "tokens appear as generated",
                      "tables rendered, not raw",
                      "shows which agent answered"],
                     edge=NAVY, face=SOFT)

# --------------------------------------------------------------------- arrows
mid0 = lambda a, b: (a + b) / 2  # noqa: E731
arrow(ax, (x0 + w0, b_erp + 0.075), (x1, b_tab + 0.16))
arrow(ax, (x0 + w0, b_plan + 0.075), (x1, b_tab + 0.06))
arrow(ax, (x0 + w0, b_doc + 0.075), (x1, b_vol + 0.12))
arrow(ax, (x1 + w1, b_tab + 0.14), (x2, b_genie + 0.16), "SQL")
arrow(ax, (x1 + w1, b_vol + 0.12), (x2, b_ka + 0.12), "retrieval")
arrow(ax, (x2 + w2, b_genie + 0.10), (x3, c_sup + 0.055))
arrow(ax, (x2 + w2, b_ka + 0.10), (x3, c_sup - 0.055))
# app <-> supervisor
arrow(ax, (x4, b_app + 0.055), (x3 + w3, c_sup + 0.030), "question", col=INK2, rad=-0.12)
arrow(ax, (x3 + w3, c_sup - 0.030), (x4, b_app + 0.020), "answer", col=ACCENT, rad=-0.12)
# app -> user
arrow(ax, (x4 + w4 * 0.34, b_app), (x4 + w4 * 0.34, b_user + box_height(4)),
      None, col=NAVY)
ax.text(x4 + w4 * 0.36, mid0(b_app, b_user + box_height(4)) + 0.004,
        "SSE stream", fontsize=7.4, color=NAVY, fontweight="bold", va="center",
        path_effects=[pe.withStroke(linewidth=3.4, foreground="white")])

# --------------------------------------------------------------- governance band
band_y = 0.128
ax.add_patch(FancyBboxPatch(
    (0.010, band_y), 0.980, 0.062,
    boxstyle="round,pad=0.006,rounding_size=0.012",
    linewidth=1.4, edgecolor=NAVY, facecolor=SOFT, zorder=1))
ax.text(0.024, band_y + 0.040, "Unity Catalog",
        fontsize=10.4, fontweight="bold", color=NAVY, va="center")
ax.text(0.024, band_y + 0.018,
        "one permission model over tables, views and documents · lineage · audit  |  "
        "the App's service principal holds least-privilege grants: warehouse CAN_USE, "
        "schema SELECT, Volume READ, endpoints CAN_QUERY, Genie space CAN_RUN",
        fontsize=7.8, color=INK2, va="center")

# ------------------------------------------------------------------ walkthrough
ax.text(0.010, 0.104, "How one question is answered",
        fontsize=9.6, fontweight="bold", color=NAVY, va="top")
steps_l = [
    '1   Analyst asks "Why is Cards & Payments over budget, and was the spend approved?"',
    "2   App posts to the Supervisor over the responses API with stream=true",
    "3   Supervisor decides the question needs both a figure and a justification",
]
steps_r = [
    "4   Genie queries v_opex_variance  →  +USD 2.72m unfavourable for 2026-06",
    "5   Knowledge Assistant retrieves the Helios case  →  approved Feb 2026, after plan lock",
    "6   Supervisor synthesises one answer; tokens stream and render as prose + a table",
]
for i, s in enumerate(steps_l):
    ax.text(0.010, 0.082 - i * 0.024, s, fontsize=8.1, color=INK, va="top")
for i, s in enumerate(steps_r):
    ax.text(0.505, 0.082 - i * 0.024, s, fontsize=8.1, color=INK, va="top")

plt.savefig(OUT, bbox_inches="tight", facecolor="white", pad_inches=0.22)
print("wrote", OUT)
