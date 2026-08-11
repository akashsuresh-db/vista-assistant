#!/usr/bin/env python3
"""Execute .sql files against the configured SQL warehouse.

The files in sql/ are TEMPLATES containing `{catalog}`, `{schema}` and `{volume}`
placeholders, so the same SQL runs in any workspace. Substitution happens here.

    python run_sql.py ../sql/01_tables.sql
    python run_sql.py -c "SELECT current_catalog()"

Importable API (used by setup.py and the tests):
    run_stmt(sql)      execute one statement
    run_file(path)     execute a whole file, statement by statement
    query(sql)         execute and return the rows
    run(...)           alias of run_stmt, kept for the tests
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import CFG  # noqa: E402

_w = None


def _client():
    """Lazily created, so importing this module needs no credentials."""
    global _w
    if _w is None:
        from databricks.sdk import WorkspaceClient
        CFG.require("profile", "warehouse_id")
        _w = WorkspaceClient(profile=CFG.profile)
    return _w


def _strip_line_comment(line: str) -> str:
    idx = line.find("--")
    return line[:idx] if idx >= 0 else line


def split_statements(sql: str) -> list[str]:
    """Split on ';' at the end of a statement's code (trailing comments removed)."""
    stmts, buf = [], []
    for line in sql.splitlines():
        code = _strip_line_comment(line).rstrip()
        if not code and not buf:
            continue
        buf.append(line)
        if code.endswith(";"):
            chunk = "\n".join(buf).strip()
            if chunk.endswith(";"):
                chunk = chunk[:-1]
            if chunk.strip():
                stmts.append(chunk.strip())
            buf = []
    tail = "\n".join(buf).strip().rstrip(";").strip()
    if tail:
        stmts.append(tail)
    return stmts


# Only these placeholders are substituted, by regex rather than str.format(): the
# Vega-Lite function body is full of JSON and dict braces, which format() would try to
# interpret as fields and fail on.
_PLACEHOLDER = re.compile(r"\{(catalog|schema|volume|volume_path|docs_path)\}")


def substitute(sql: str, schema: str | None = None) -> str:
    values = {
        "catalog": CFG.catalog,
        "schema": schema or CFG.schema,
        "volume": CFG.volume,
        "volume_path": CFG.volume_path,
        "docs_path": CFG.docs_path,
    }
    return _PLACEHOLDER.sub(lambda m: values[m.group(1)], sql)


def run_stmt(stmt: str, show: bool = False, schema: str | None = None):
    from databricks.sdk.service.sql import StatementState
    w = _client()
    sql = substitute(stmt, schema)
    resp = w.statement_execution.execute_statement(
        warehouse_id=CFG.warehouse_id,
        catalog=CFG.catalog,
        schema=schema or CFG.schema,
        statement=sql,
        wait_timeout="50s",
    )
    while resp.status.state in (StatementState.PENDING, StatementState.RUNNING):
        resp = w.statement_execution.get_statement(resp.statement_id)
    if resp.status.state != StatementState.SUCCEEDED:
        msg = resp.status.error.message if resp.status.error else str(resp.status.state)
        raise RuntimeError(f"{msg}\n--SQL--\n{sql[:600]}")
    if show and resp.result and resp.result.data_array:
        cols = [c.name for c in resp.manifest.schema.columns]
        print("  " + " | ".join(cols))
        for row in resp.result.data_array[:50]:
            print("  " + " | ".join(str(v) for v in row))
    return resp


def query(stmt: str, schema: str | None = None) -> list[list]:
    resp = run_stmt(stmt, show=False, schema=schema)
    if resp.result and resp.result.data_array:
        return [list(r) for r in resp.result.data_array]
    return []


def run_file(path, show: bool = False, quiet: bool = True) -> None:
    path = Path(path)
    stmts = split_statements(path.read_text())
    if not quiet:
        print(f"=== {path.name}: {len(stmts)} statements ===")
    for i, s in enumerate(stmts, 1):
        if not quiet:
            print(f"[{i}/{len(stmts)}] {' '.join(s.split())[:70]}")
        run_stmt(s, show=show)


# the test suites import `run`
run = run_stmt


def main() -> None:
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return
    if args[0] == "-c":
        run_stmt(args[1], show=True)
        return
    for p in args:
        run_file(p, show=True, quiet=False)
    print("DONE")


if __name__ == "__main__":
    main()
