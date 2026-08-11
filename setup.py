#!/usr/bin/env python3
"""Vista Assistant — one-command setup.

Runs every step that CAN be automated, and stops with clear instructions at the two that
cannot (Agent Bricks has no create API for the Knowledge Assistant or the Supervisor).

    python setup.py                # run everything that is ready
    python setup.py --step data    # run one step
    python setup.py --status       # what is done, what is next
    python setup.py --list         # all steps

The script is idempotent: every step is safe to re-run, so if a step fails you can fix the
cause and run the same command again.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "scripts"))

from config import CFG, CONFIG_FILE, EXAMPLE_FILE  # noqa: E402

C_OK, C_WARN, C_ERR, C_DIM, C_END, C_BOLD = (
    "\033[92m", "\033[93m", "\033[91m", "\033[2m", "\033[0m", "\033[1m")


def say(msg: str = "") -> None:
    print(msg, flush=True)


def head(n: int, total: int, title: str) -> None:
    say(f"\n{C_BOLD}[{n}/{total}] {title}{C_END}")


def ok(msg: str) -> None:
    say(f"  {C_OK}✓{C_END} {msg}")


def warn(msg: str) -> None:
    say(f"  {C_WARN}!{C_END} {msg}")


def die(msg: str, hint: str = "") -> None:
    say(f"  {C_ERR}✗ {msg}{C_END}")
    if hint:
        say(f"    {hint}")
    raise SystemExit(1)


def run(cmd: list[str], cwd: Path | None = None, quiet: bool = True) -> str:
    r = subprocess.run(cmd, cwd=cwd or ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout).strip()[:900])
    return r.stdout


def db(*args: str) -> str:
    """Databricks CLI with the configured profile."""
    return run(["databricks", *args, "-p", CFG.profile])


# ============================================================== step functions
def step_check() -> None:
    """Preflight: config present, CLI installed, workspace reachable."""
    if not CONFIG_FILE.exists():
        die(f"{CONFIG_FILE.name} not found",
            f"Run:  cp {EXAMPLE_FILE.name} {CONFIG_FILE.name}   then edit it.")
    CFG.require("profile", "warehouse_id", "catalog", "schema")

    try:
        run(["databricks", "--version"])
    except Exception:
        die("the Databricks CLI is not installed",
            "See https://docs.databricks.com/dev-tools/cli/install.html")
    ok("Databricks CLI found")

    try:
        me = json.loads(db("current-user", "me", "-o", "json"))
        ok(f"authenticated as {me.get('userName', '?')}")
    except Exception as e:
        die(f"cannot reach the workspace with profile '{CFG.profile}'",
            f"Try:  databricks auth login --profile {CFG.profile}\n    ({e})")

    try:
        wh = json.loads(db("warehouses", "get", CFG.warehouse_id, "-o", "json"))
        ok(f"warehouse '{wh.get('name')}' ({wh.get('state')})")
    except Exception:
        die(f"warehouse {CFG.warehouse_id} not found",
            "List them with:  databricks warehouses list -p " + CFG.profile)

    for tool in ("reportlab", "pptx", "docx"):
        try:
            __import__(tool)
        except ImportError:
            warn(f"python package for '{tool}' missing — "
                 f"run: pip install -r requirements.txt")


def step_uc() -> None:
    """Create the schema and the documents Volume."""
    from run_sql import run_stmt
    run_stmt(f"CREATE SCHEMA IF NOT EXISTS {CFG.fq_schema} "
             f"COMMENT 'Vista Assistant demo — Meridian Bank FnA shared services'",
             schema="default")
    ok(f"schema {CFG.fq_schema}")
    try:
        db("volumes", "create", CFG.catalog, CFG.schema, CFG.volume, "MANAGED")
        ok(f"volume {CFG.volume_path}")
    except Exception as e:
        if "already exists" in str(e).lower():
            ok(f"volume {CFG.volume_path} (already existed)")
        else:
            raise


def step_data() -> None:
    """Generate the synthetic marts and verify the planted stories."""
    run([sys.executable, "scripts/gen_structured.py"])
    ok("11 CSV datasets generated")
    out = run([sys.executable, "scripts/verify_local.py"])
    if "ALL CHECKS PASSED" not in out:
        die("the generated data failed its own consistency checks", out[-400:])
    ok("12/12 data-story checks pass")


def step_tables() -> None:
    """Upload the CSVs and build the Delta tables and views."""
    from run_sql import run_file
    staging = f"{CFG.volume_path}/_staging_csv"
    try:
        db("fs", "mkdir", f"dbfs:{staging}")
    except Exception:
        pass
    csvs = sorted((ROOT / "data").glob("*.csv"))
    if not csvs:
        die("no CSVs in data/ — run the 'data' step first")
    for f in csvs:
        db("fs", "cp", str(f), f"dbfs:{staging}/{f.name}", "--overwrite")
    ok(f"{len(csvs)} CSVs uploaded")

    run_file(ROOT / "sql" / "01_tables.sql")
    ok("11 Delta tables created (with column comments for Genie)")
    run_file(ROOT / "sql" / "02_views.sql")
    ok("5 analyst views created")

    # the staged CSVs are disposable once Delta has copied them, and leaving them in the
    # Volume would pollute the Knowledge Assistant's document index
    try:
        db("fs", "rm", f"dbfs:{staging}", "--recursive")
        ok("staging CSVs removed from the Volume")
    except Exception:
        warn("could not remove the staging CSVs — delete "
             f"{staging} by hand so the KA does not index them")


def step_docs() -> None:
    """Render the policy documents and upload them to the Volume."""
    import glob
    import importlib
    sys.path.insert(0, str(ROOT / "scripts"))
    from render import render
    mods = sorted(Path(p).stem for p in glob.glob("scripts/docs_content/d*.py"))
    paths = []
    for m in mods:
        paths.append(render(importlib.import_module(f"docs_content.{m}").DOC))
    ok(f"{len(paths)} documents rendered (PDF / DOCX / PPTX)")

    try:
        db("fs", "mkdir", f"dbfs:{CFG.docs_path}")
    except Exception:
        pass
    for p in paths:
        db("fs", "cp", p, f"dbfs:{CFG.docs_path}/{Path(p).name}", "--overwrite")
    ok(f"uploaded to {CFG.docs_path}")


def step_chart_fn() -> None:
    """Create the Vega-Lite chart UC function."""
    from run_sql import run_file
    run_file(ROOT / "sql" / "03_vegalite_function.sql")
    ok(f"UC function {CFG.table('make_chart')} created and granted")


def step_genie() -> None:
    """Create the Genie space and record its id in config.yaml."""
    out = run([sys.executable, "scripts/build_genie_space.py"])
    line = next((l for l in out.splitlines() if "SPACE_ID" in l), "")
    if not line:
        die("could not determine the new Genie space id", out[-400:])
    ok(line.strip())
    ok("space id written to config.yaml")


def step_app() -> None:
    """Deploy the Databricks App."""
    if not CFG.supervisor_endpoint:
        die("supervisor_endpoint is not set in config.yaml",
            "Create the Supervisor Agent first — see docs/SETUP.md step 7, then paste its\n"
            "    endpoint name (mas-xxxxxxxx-endpoint) into config.yaml.")
    out = run(["bash", "scripts/deploy_app.sh"])
    url = next((l.split()[-1] for l in out.splitlines() if l.startswith("deployed:")), "")
    ok(f"app deployed{': ' + url if url else ''}")


def step_verify() -> None:
    """Run the suites that need a live workspace."""
    from run_sql import run_file
    run_file(ROOT / "tests" / "test_warehouse_stories.sql")
    ok("warehouse story checks ran")
    for name, script in (("charts", "tests/test_charts.py"),
                         ("genie", "tests/test_genie.py"),
                         ("knowledge assistant", "tests/test_ka.py"),
                         ("supervisor", "tests/test_supervisor.py")):
        try:
            out = run([sys.executable, script])
            last = [l for l in out.strip().splitlines() if l.strip()][-1]
            (ok if ("PASSED" in last or "SKIP" in last) else warn)(f"{name}: {last[:70]}")
        except Exception as e:
            warn(f"{name}: {str(e).splitlines()[0][:70]}")


# ================================================================== the manual bits
MANUAL_KA = f"""
{C_BOLD}MANUAL STEP — create the Knowledge Assistant{C_END}
Agent Bricks has no create API, so this is done in the UI (2 minutes).

  1. Open the workspace → left nav → {C_BOLD}Agents{C_END} → {C_BOLD}Create Agent{C_END}
  2. Choose {C_BOLD}Knowledge Assistant{C_END}
  3. Name it            : vista-knowledge-assistant
  4. Knowledge source   : Files in a Volume →
                          {C_BOLD}{CFG.docs_path}{C_END}
  5. Paste the description from {C_BOLD}docs/SETUP.md step 6{C_END}
  6. Create, and wait for the sources to finish indexing
  7. Copy the serving endpoint name (ka-xxxxxxxx-endpoint) into
     {C_BOLD}config.yaml → ka_endpoint{C_END}

Screenshots for every click: {C_BOLD}docs/SETUP.md{C_END}
"""

MANUAL_SUP = f"""
{C_BOLD}MANUAL STEP — create the Supervisor Agent{C_END}

  1. {C_BOLD}Agents{C_END} → {C_BOLD}Create Agent{C_END} → {C_BOLD}Supervisor Agent{C_END}
  2. Name it: vista-supervisor
  3. Attach THREE things:
       • the Genie space  (id {CFG.genie_space_id or "<from the genie step>"})
       • the Knowledge Assistant ({CFG.ka_endpoint or "<from the previous step>"})
       • the UC function  {CFG.table('make_chart')}   (as a UC Function tool)
  4. Paste the instructions from {C_BOLD}docs/SETUP.md step 7{C_END}
  5. Copy the endpoint name (mas-xxxxxxxx-endpoint) into
     {C_BOLD}config.yaml → supervisor_endpoint{C_END}
"""

STEPS = [
    ("check",    "Preflight checks",                      step_check,    None),
    ("uc",       "Create schema and Volume",              step_uc,       None),
    ("data",     "Generate the synthetic datasets",       step_data,     None),
    ("tables",   "Build Delta tables and views",          step_tables,   None),
    ("docs",     "Render and upload the policy documents", step_docs,    None),
    ("chart-fn", "Create the Vega-Lite UC function",      step_chart_fn, None),
    ("genie",    "Create the Genie space",                step_genie,    None),
    ("ka",       "Knowledge Assistant (manual)",          None,          MANUAL_KA),
    ("supervisor", "Supervisor Agent (manual)",           None,          MANUAL_SUP),
    ("app",      "Deploy the Databricks App",             step_app,      None),
    ("verify",   "Run the live test suites",              step_verify,   None),
]


def status() -> None:
    say(f"\n{C_BOLD}Vista Assistant — configuration{C_END}")
    say(CFG.summary())
    say(f"\n{C_BOLD}Next{C_END}")
    if not CFG.genie_space_id:
        say("  run:  python setup.py           (creates data, docs, Genie space)")
    elif not CFG.ka_endpoint:
        say("  create the Knowledge Assistant  → docs/SETUP.md step 6")
    elif not CFG.supervisor_endpoint:
        say("  create the Supervisor Agent     → docs/SETUP.md step 7")
    else:
        say("  run:  python setup.py --step app     then --step verify")
    say()


def main() -> int:
    ap = argparse.ArgumentParser(description="Vista Assistant setup")
    ap.add_argument("--step", help="run a single step by name")
    ap.add_argument("--status", action="store_true", help="show configuration and next step")
    ap.add_argument("--list", action="store_true", help="list all steps")
    args = ap.parse_args()

    if args.list:
        say(f"\n{C_BOLD}Steps{C_END}")
        for name, title, fn, _ in STEPS:
            say(f"  {name:<11} {title}{'' if fn else C_DIM + '  (manual, UI only)' + C_END}")
        say()
        return 0
    if args.status:
        status()
        return 0

    chosen = [s for s in STEPS if s[0] == args.step] if args.step else STEPS
    if args.step and not chosen:
        die(f"unknown step '{args.step}'", "python setup.py --list")

    say(f"\n{C_BOLD}Vista Assistant setup{C_END}  "
        f"{C_DIM}({CFG.fq_schema} on profile {CFG.profile or '?'}){C_END}")

    total = len(chosen)
    for i, (name, title, fn, manual) in enumerate(chosen, 1):
        head(i, total, title)
        if fn is None:
            say(manual)
            if not args.step:
                say(f"{C_WARN}Setup paused here.{C_END} Complete the step above, put the "
                    f"endpoint into config.yaml,\nthen re-run: "
                    f"{C_BOLD}python setup.py{C_END} (finished steps are skipped)\n")
                return 0
            continue
        # skip work that is already done, so re-running is cheap and safe
        if not args.step and name == "genie" and CFG.genie_space_id:
            ok(f"already created ({CFG.genie_space_id}) — skipping")
            continue
        if not args.step and name == "app" and not CFG.supervisor_endpoint:
            warn("supervisor_endpoint not set yet — skipping the app deploy")
            continue
        try:
            fn()
        except SystemExit:
            raise
        except Exception as e:
            die(f"{title} failed", str(e).splitlines()[0][:300] if str(e) else "")

    say(f"\n{C_OK}{C_BOLD}Done.{C_END}  Run "
        f"{C_BOLD}python setup.py --status{C_END} to see what is next.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
