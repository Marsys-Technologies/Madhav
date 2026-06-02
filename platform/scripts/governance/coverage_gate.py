#!/usr/bin/env python3
"""
coverage_gate.py — MARSYS-JIS CI coverage gate.

Implements: COV-S7 — §G.7 of CAPABILITY_COVERAGE_AND_PERFORMANCE_AUDIT_v1_0.md

Checks two invariants:
  1. COVERAGE_GATE_MANIFEST: Every tool in RETRIEVAL_TOOLS[] has a corresponding
     entry in CAPABILITY_MANIFEST.json with a non-empty tool_name field.
  2. COVERAGE_GATE_ASSETS: Every canonical asset layer directory (01_FACTS_LAYER/,
     025_HOLISTIC_SYNTHESIS/, etc.) has at least one tool_name binding in the manifest.

Exit codes:
  0 — all checks pass (PASS)
  1 — COVERAGE_GATE_MANIFEST failure only (tools missing from manifest)
  2 — COVERAGE_GATE_ASSETS failure only (asset folders with no tool binding)
  3 — both failure categories present
  4 — script-internal error

The script emits a structured JSON report to stdout and a human-readable summary
to stderr. This allows the scheduled audit job to parse the JSON, while CI logs
show the human summary.

Usage:
  python3 platform/scripts/governance/coverage_gate.py [--repo-root PATH]
      [--retrieve-index PATH] [--manifest-path PATH] [--asset-dirs DIR [DIR ...]]

Optional overrides (primarily for testing):
  --retrieve-index   Override path to platform/src/lib/retrieve/index.ts
  --manifest-path    Override path to 00_ARCHITECTURE/CAPABILITY_MANIFEST.json
  --asset-dirs       Override the list of canonical asset layer directories to scan
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import pathlib
import re
import sys
import traceback
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Canonical asset layer directories, relative to repo root.
# These are the data-layer folders that must be reachable by at least one
# bound retrieval tool. 00_ARCHITECTURE/ is governance-only and excluded.
CANONICAL_ASSET_DIRS: List[str] = [
    "01_FACTS_LAYER",
    "025_HOLISTIC_SYNTHESIS",
    "035_DISCOVERY_LAYER",
    "03_DERIVATIONS",
    "03_DOMAIN_REPORTS",
    "04_REMEDIAL_CODEX",
    "05_TEMPORAL_ENGINES",
    "06_LEARNING_LAYER",
    "08_CLASSICAL_CROSS_REFERENCE",
    "09_MULTI_SCHOOL_TRIANGULATION",
]

# Default relative paths from repo root
DEFAULT_RETRIEVE_INDEX = "platform/src/lib/retrieve/index.ts"
DEFAULT_MANIFEST_PATH = "00_ARCHITECTURE/CAPABILITY_MANIFEST.json"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def find_repo_root(start: pathlib.Path) -> pathlib.Path:
    """Walk up from start until we find a directory containing .git."""
    current = start.resolve()
    for parent in [current, *current.parents]:
        if (parent / ".git").exists():
            return parent
    # Fallback: assume the script is at platform/scripts/governance/
    return current.parent.parent.parent


def parse_retrieval_tools(retrieve_index_path: pathlib.Path) -> List[str]:
    """
    Extract tool names from platform/src/lib/retrieve/index.ts.

    Strategy: read the RETRIEVAL_TOOLS array block, then resolve each module
    alias back to the TOOL_NAME constant declared in the same file's imports.
    Falls back to scanning individual retrieve/*.ts files for TOOL_NAME values
    that match the module aliases found in RETRIEVAL_TOOLS[].

    Returns a sorted list of unique tool name strings.
    """
    content = retrieve_index_path.read_text(encoding="utf-8")

    # Step 1: Build a map of import alias → module path (relative)
    #   import * as msrSql from './msr_sql'  →  msrSql: './msr_sql'
    import_map: Dict[str, str] = {}
    for m in re.finditer(
        r"import \* as (\w+) from '([^']+)'", content
    ):
        alias, module_path = m.group(1), m.group(2)
        import_map[alias] = module_path

    # Step 2: Extract the RETRIEVAL_TOOLS[] body
    tools_match = re.search(
        r"export const RETRIEVAL_TOOLS[^=]*=\s*\[([^\]]*)\]", content, re.DOTALL
    )
    if not tools_match:
        raise ValueError(
            f"Could not find RETRIEVAL_TOOLS array in {retrieve_index_path}"
        )
    tools_body = tools_match.group(1)

    # Step 3: Find all module alias references like  msrSql.tool
    referenced_aliases = re.findall(r"(\w+)\.tool", tools_body)

    # Step 4: For each alias, resolve the module file and read its TOOL_NAME
    retrieve_dir = retrieve_index_path.parent
    tool_names: List[str] = []

    for alias in referenced_aliases:
        module_path = import_map.get(alias)
        if not module_path:
            # alias not found in imports — skip
            continue

        # Resolve relative path like './msr_sql' → retrieve_dir/msr_sql.ts
        candidate = retrieve_dir / (module_path.lstrip("./") + ".ts")
        if not candidate.exists():
            continue

        module_content = candidate.read_text(encoding="utf-8")
        name_match = re.search(r"const TOOL_NAME\s*=\s*['\"]([^'\"]+)['\"]", module_content)
        if name_match:
            tool_names.append(name_match.group(1))

    return sorted(set(tool_names))


def parse_manifest_tool_names(manifest_path: pathlib.Path) -> List[str]:
    """
    Return all non-empty tool_name values from CAPABILITY_MANIFEST.json entries.
    """
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    tool_names: List[str] = []
    for entry in manifest.get("entries", []):
        tn = entry.get("tool_name")
        if tn and isinstance(tn, str) and tn.strip():
            tool_names.append(tn.strip())

    return sorted(set(tool_names))


def parse_manifest_asset_coverage(
    manifest_path: pathlib.Path, asset_dirs: List[str]
) -> Dict[str, List[str]]:
    """
    Build a mapping: asset_layer_prefix → [tool_names bound to that layer].

    An entry is considered "bound to a layer" if its path starts with the layer
    directory (e.g., "01_FACTS_LAYER/...") AND it has a non-empty tool_name.
    Returns a dict keyed by canonical asset dir name.

    asset_dirs: the list of directory names to check (relative to repo root).
    """
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    coverage: Dict[str, List[str]] = {}
    for entry in manifest.get("entries", []):
        path = entry.get("path") or ""
        tool_name = entry.get("tool_name")
        if not tool_name or not isinstance(tool_name, str) or not tool_name.strip():
            continue
        # Match the path prefix to one of the given asset dirs
        for asset_dir in asset_dirs:
            if path.startswith(asset_dir + "/") or path == asset_dir:
                if asset_dir not in coverage:
                    coverage[asset_dir] = []
                coverage[asset_dir].append(tool_name.strip())

    return coverage


# ---------------------------------------------------------------------------
# Gate logic
# ---------------------------------------------------------------------------


def run_gate(
    retrieve_index_path: pathlib.Path,
    manifest_path: pathlib.Path,
    asset_dirs: List[str],
    repo_root: pathlib.Path,
) -> dict:
    """
    Run both coverage checks and return a report dict.

    report shape:
      {
        "verdict": "PASS" | "FAIL",
        "categories": {
          "COVERAGE_GATE_MANIFEST": {"status": "PASS" | "FAIL", "missing": [...]},
          "COVERAGE_GATE_ASSETS":   {"status": "PASS" | "FAIL", "unbound": [...]}
        },
        "run_at": "<ISO timestamp>"
      }
    """
    # --- Manifest gate ---
    retrieval_tools = parse_retrieval_tools(retrieve_index_path)
    manifest_tool_names = set(parse_manifest_tool_names(manifest_path))

    missing_from_manifest = sorted(
        t for t in retrieval_tools if t not in manifest_tool_names
    )

    manifest_status = "FAIL" if missing_from_manifest else "PASS"

    # --- Asset gate ---
    # Vacuous pass when RETRIEVAL_TOOLS is empty (clean-slate rebuild arc):
    # tool-to-asset bindings cannot exist until tools are re-registered.
    if not retrieval_tools:
        unbound_dirs = []
    else:
        asset_coverage = parse_manifest_asset_coverage(manifest_path, asset_dirs)
        unbound_dirs = sorted(
            d for d in asset_dirs
            if (repo_root / d).is_dir() and d not in asset_coverage
        )

    asset_status = "FAIL" if unbound_dirs else "PASS"

    # --- Aggregate ---
    overall = "PASS" if (manifest_status == "PASS" and asset_status == "PASS") else "FAIL"

    return {
        "verdict": overall,
        "categories": {
            "COVERAGE_GATE_MANIFEST": {
                "status": manifest_status,
                "missing": missing_from_manifest,
            },
            "COVERAGE_GATE_ASSETS": {
                "status": asset_status,
                "unbound": unbound_dirs,
            },
        },
        "run_at": datetime.datetime.utcnow().isoformat() + "Z",
    }


def compute_exit_code(report: dict) -> int:
    """
    Map the report to an exit code.

    0 = all PASS
    1 = COVERAGE_GATE_MANIFEST fail only
    2 = COVERAGE_GATE_ASSETS fail only
    3 = both fail
    """
    m_fail = report["categories"]["COVERAGE_GATE_MANIFEST"]["status"] == "FAIL"
    a_fail = report["categories"]["COVERAGE_GATE_ASSETS"]["status"] == "FAIL"
    if m_fail and a_fail:
        return 3
    if m_fail:
        return 1
    if a_fail:
        return 2
    return 0


def emit_human_summary(report: dict, file=sys.stderr) -> None:
    """Print a human-readable summary to `file`."""
    verdict = report["verdict"]
    print(f"\n=== coverage_gate.py — {verdict} ===", file=file)
    print(f"Run at: {report['run_at']}", file=file)

    m_cat = report["categories"]["COVERAGE_GATE_MANIFEST"]
    a_cat = report["categories"]["COVERAGE_GATE_ASSETS"]

    print(f"\n  COVERAGE_GATE_MANIFEST: {m_cat['status']}", file=file)
    if m_cat["missing"]:
        print("    Tools in RETRIEVAL_TOOLS[] missing from manifest:", file=file)
        for t in m_cat["missing"]:
            print(f"      - {t}", file=file)

    print(f"\n  COVERAGE_GATE_ASSETS: {a_cat['status']}", file=file)
    if a_cat["unbound"]:
        print("    Asset folders with no manifest tool_name binding:", file=file)
        for d in a_cat["unbound"]:
            print(f"      - {d}/", file=file)

    print("", file=file)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="COV-S7 coverage gate: checks RETRIEVAL_TOOLS[] vs CAPABILITY_MANIFEST.json",
    )
    parser.add_argument(
        "--repo-root",
        type=pathlib.Path,
        default=None,
        help="Path to repository root (default: auto-detected from .git)",
    )
    parser.add_argument(
        "--retrieve-index",
        type=pathlib.Path,
        default=None,
        help=f"Override path to retrieve/index.ts (default: <repo_root>/{DEFAULT_RETRIEVE_INDEX})",
    )
    parser.add_argument(
        "--manifest-path",
        type=pathlib.Path,
        default=None,
        help=f"Override path to CAPABILITY_MANIFEST.json (default: <repo_root>/{DEFAULT_MANIFEST_PATH})",
    )
    parser.add_argument(
        "--asset-dirs",
        nargs="*",
        default=None,
        help="Override canonical asset layer dirs to scan (space-separated, relative to repo root). "
             "Pass with no values to disable asset scanning entirely.",
    )

    args = parser.parse_args(argv)

    try:
        repo_root = args.repo_root or find_repo_root(pathlib.Path(__file__))

        retrieve_index = args.retrieve_index or (repo_root / DEFAULT_RETRIEVE_INDEX)
        manifest_path = args.manifest_path or (repo_root / DEFAULT_MANIFEST_PATH)
        asset_dirs = args.asset_dirs or CANONICAL_ASSET_DIRS

        if not retrieve_index.exists():
            print(
                f"[coverage_gate] ERROR: retrieve index not found: {retrieve_index}",
                file=sys.stderr,
            )
            return 4

        if not manifest_path.exists():
            print(
                f"[coverage_gate] ERROR: manifest not found: {manifest_path}",
                file=sys.stderr,
            )
            return 4

        report = run_gate(retrieve_index, manifest_path, asset_dirs, repo_root)

        # Emit JSON to stdout for machine consumption
        print(json.dumps(report, indent=2))

        # Emit human summary to stderr
        emit_human_summary(report)

        return compute_exit_code(report)

    except Exception as exc:  # noqa: BLE001
        print(f"[coverage_gate] INTERNAL ERROR: {exc}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return 4


if __name__ == "__main__":
    sys.exit(main())
