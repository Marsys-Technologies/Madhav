#!/usr/bin/env python3
"""Guard: a migration that INSERTs into asset_registry must name catalog_status.

WHY THIS EXISTS (NIRMANA D-CND-13, issues #1753 / #1807)
--------------------------------------------------------
`asset_registry.catalog_status` has `DEFAULT 'DRAFT'`, and the Nirmana cockpit
FILTERS on that column. So a migration that registers a fully-built, fully-consumed
asset without naming the column registers it as a draft -- and the asset simply does
not appear in the operator surface, with nothing failing.

This is not hypothetical and it is not new. Migration `294_catalog_status_current.sql`
diagnosed exactly this in its own header and swept the assets that existed then:

    "Fix catalog_status for built assets that defaulted to 'DRAFT'. Root cause:
     several registry migrations omitted catalog_status from their [INSERT] ...
     are invisible in the Nirmana cockpit (which filters on catalog_status)."

**The sweep fixed the data and nothing fixed the mechanism**, so the condition came
straight back: 46 assets across L0/L2/L3/L4/L5 were DRAFT again by 2026-09-05, and
migrations landing AFTER 294 re-introduced the defect it had just closed.

D-CND-13 states the general form: *a column whose DEFAULT is the wrong answer for the
common case is a defect in the schema, not in the callers that forget it. Where a
sweep has already run once and the condition returned, the sweep is not the fix.*

Two things now close it: PR #1813 made `catalog_status` migration-governed in the seed
(a CURRENT row stays CURRENT through a re-seed), and this guard stops a NEW migration
silently minting another DRAFT.

WHAT IT FLAGS
-------------
Any `INSERT INTO [public.]asset_registry (...)` in platform/migrations/*.sql whose
column list does not name `catalog_status`. The historical instances are allowlisted
with their reason -- they predate the rule, their data was swept by 294 and re-swept
by this campaign, and rewriting an applied migration is forbidden outright.

Exit codes:  0 pass  ·  1 non-allowlisted violation or self-test failure  ·  2 usage
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO = SCRIPT_DIR.parents[1]
MIGRATIONS = REPO / "migrations"
ALLOWLIST_PATH = SCRIPT_DIR / "asset_registry_catalog_status_allowlist.json"

# INSERT INTO [public.]asset_registry  ( ...column list... )
_RE_INSERT = re.compile(
    r"INSERT\s+INTO\s+(?:public\.)?asset_registry\s*\(([^)]*)\)",
    re.IGNORECASE | re.DOTALL,
)


def violations_in(text: str) -> list[tuple[int, str]]:
    """Return (line, column-list snippet) for INSERTs that omit catalog_status."""
    out: list[tuple[int, str]] = []
    for m in _RE_INSERT.finditer(text):
        cols = m.group(1)
        if re.search(r"\bcatalog_status\b", cols, re.IGNORECASE):
            continue
        line = text.count("\n", 0, m.start()) + 1
        out.append((line, " ".join(cols.split())[:120]))
    return out


def load_allowlist() -> dict:
    if not ALLOWLIST_PATH.exists():
        return {}
    try:
        data = json.loads(ALLOWLIST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return {e["file"]: e for e in data.get("entries", []) if e.get("file")}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--strict", action="store_true", help="fail on allowlisted too")
    args = ap.parse_args()

    if args.self_test:
        bad = "INSERT INTO asset_registry (asset_id, layer, target_table) VALUES ('x','L1','t');"
        good = "INSERT INTO asset_registry (asset_id, layer, catalog_status) VALUES ('x','L1','CURRENT');"
        good_q = "INSERT INTO public.asset_registry\n  (asset_id,\n   catalog_status)\nVALUES ('x','CURRENT');"
        fails = []
        if not violations_in(bad):
            fails.append("FAIL fixture (omits catalog_status) was not flagged")
        if violations_in(good):
            fails.append("PASS fixture (names catalog_status) was flagged")
        if violations_in(good_q):
            fails.append("PASS fixture (multiline, public-qualified) was flagged")
        if fails:
            print("check_asset_registry_catalog_status: SELF-TEST FAILED", file=sys.stderr)
            for f in fails:
                print(f"  {f}", file=sys.stderr)
            return 1
        print("check_asset_registry_catalog_status: SELF-TEST PASS (1 fail / 2 pass fixtures)")
        return 0

    if not MIGRATIONS.is_dir():
        print(f"ERROR: {MIGRATIONS} not found", file=sys.stderr)
        return 2

    allow = load_allowlist()
    new: list[str] = []
    allowed = 0
    for path in sorted(MIGRATIONS.glob("*.sql")):
        rel = path.relative_to(REPO.parent).as_posix()
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for line, snippet in violations_in(text):
            key = path.name
            if key in allow and not args.strict:
                allowed += 1
                continue
            new.append(f"  {rel}:{line} — INSERT INTO asset_registry omits catalog_status "
                       f"(DEFAULT 'DRAFT'; the cockpit filters on it). Columns: {snippet}")

    if allowed:
        print(f"check_asset_registry_catalog_status: {allowed} allowlisted "
              f"(pre-rule migrations, data swept — see {ALLOWLIST_PATH.name})")
    if new:
        print(f"check_asset_registry_catalog_status: {len(new)} NON-ALLOWLISTED violation(s). FAIL.",
              file=sys.stderr)
        for v in new:
            print(v, file=sys.stderr)
        print("\nName catalog_status explicitly in the INSERT. 'CURRENT' for a built asset; "
              "'DRAFT' only if it genuinely is one (D-CND-13, issues #1753/#1807).", file=sys.stderr)
        return 1
    print("check_asset_registry_catalog_status: 0 new violations. PASS.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
