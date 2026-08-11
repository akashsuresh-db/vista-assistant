#!/usr/bin/env python3
"""Single source of workspace configuration.

Every script imports from here, so there is exactly one place to edit and nothing
workspace-specific is hardcoded anywhere else in the repo.

Values resolve in this order (first wins):
  1. an environment variable  (VISTA_CATALOG, VISTA_PROFILE, ...)
  2. config.yaml at the repo root
  3. a safe default, where one exists

Usage:
    from config import CFG
    print(CFG.catalog, CFG.fq_schema)
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = ROOT / "config.yaml"
EXAMPLE_FILE = ROOT / "config.example.yaml"

_DEFAULTS = {
    "profile": "",
    "warehouse_id": "",
    "catalog": "main",
    "schema": "vista_assistant",
    "volume": "vista_documents",
    "app_name": "vista-assistant",
    "genie_space_id": "",
    "ka_endpoint": "",
    "supervisor_endpoint": "",
    "reporting_currency": "USD",
    "accent_colour": "#a100ff",
}

# Keys that must be set before the setup script can do anything useful.
_REQUIRED = ("profile", "warehouse_id", "catalog", "schema")


def _load_yaml(path: Path) -> dict:
    """Minimal `key: value` reader.

    Deliberately not using PyYAML: this keeps `python setup.py` runnable on a bare
    interpreter, which matters when someone clones the repo and just wants to go.
    The config file is a flat map of scalars, so a full parser is not needed.
    """
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.split(" #", 1)[0].strip()      # strip trailing comment
        if value and value[0] in "\"'" and value[-1] == value[0]:
            value = value[1:-1]                       # strip quotes
        out[key] = value
    return out


@dataclass
class Config:
    profile: str = ""
    warehouse_id: str = ""
    catalog: str = "main"
    schema: str = "vista_assistant"
    volume: str = "vista_documents"
    app_name: str = "vista-assistant"
    genie_space_id: str = ""
    ka_endpoint: str = ""
    supervisor_endpoint: str = ""
    reporting_currency: str = "USD"
    accent_colour: str = "#a100ff"
    _source: str = field(default="defaults", repr=False)

    # ---------------------------------------------------------------- helpers
    @property
    def fq_schema(self) -> str:
        return f"{self.catalog}.{self.schema}"

    @property
    def volume_path(self) -> str:
        return f"/Volumes/{self.catalog}/{self.schema}/{self.volume}"

    @property
    def docs_path(self) -> str:
        return f"{self.volume_path}/policies"

    def table(self, name: str) -> str:
        return f"{self.fq_schema}.{name}"

    def require(self, *keys: str) -> None:
        """Fail with an actionable message rather than a confusing API error later."""
        missing = [k for k in (keys or _REQUIRED) if not getattr(self, k, "")]
        if not missing:
            return
        print(f"\nMissing required configuration: {', '.join(missing)}\n", file=sys.stderr)
        if not CONFIG_FILE.exists():
            print(f"  There is no {CONFIG_FILE.name} yet. Create one with:\n"
                  f"      cp {EXAMPLE_FILE.name} {CONFIG_FILE.name}\n"
                  f"  then edit it.\n", file=sys.stderr)
        else:
            print(f"  Edit {CONFIG_FILE} and set: {', '.join(missing)}\n", file=sys.stderr)
        raise SystemExit(2)

    def summary(self) -> str:
        def shown(v: str) -> str:
            return v if v else "(not set)"
        return "\n".join([
            f"  profile              {shown(self.profile)}",
            f"  warehouse_id         {shown(self.warehouse_id)}",
            f"  catalog.schema       {self.fq_schema}",
            f"  volume               {self.volume_path}",
            f"  app_name             {self.app_name}",
            f"  genie_space_id       {shown(self.genie_space_id)}",
            f"  ka_endpoint          {shown(self.ka_endpoint)}",
            f"  supervisor_endpoint  {shown(self.supervisor_endpoint)}",
        ])


def _build() -> Config:
    values = dict(_DEFAULTS)
    source = "defaults"
    from_file = _load_yaml(CONFIG_FILE)
    if from_file:
        values.update({k: v for k, v in from_file.items() if k in _DEFAULTS})
        source = str(CONFIG_FILE.name)
    # env wins, so CI and one-off overrides work without editing the file
    for key in _DEFAULTS:
        env = os.environ.get(f"VISTA_{key.upper()}")
        if env:
            values[key] = env
            source = f"{source} + env"
    cfg = Config(**values)
    cfg._source = source
    return cfg


CFG = _build()


def set_value(key: str, value: str) -> None:
    """Write a value back into config.yaml.

    Used by the setup script to record ids it creates (e.g. the Genie space id) so the
    user does not have to copy them by hand.
    """
    if key not in _DEFAULTS:
        raise KeyError(key)
    if not CONFIG_FILE.exists():
        CONFIG_FILE.write_text(EXAMPLE_FILE.read_text())
    lines = CONFIG_FILE.read_text().splitlines()
    written = False
    for i, raw in enumerate(lines):
        stripped = raw.strip()
        if stripped.startswith("#") or ":" not in stripped:
            continue
        if stripped.partition(":")[0].strip() == key:
            lines[i] = f'{key}: "{value}"'
            written = True
            break
    if not written:
        lines.append(f'{key}: "{value}"')
    CONFIG_FILE.write_text("\n".join(lines) + "\n")
    setattr(CFG, key, value)


if __name__ == "__main__":
    print(f"Vista Assistant configuration (from {CFG._source}):\n")
    print(CFG.summary())
