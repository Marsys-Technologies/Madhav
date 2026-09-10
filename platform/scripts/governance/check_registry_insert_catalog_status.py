#!/usr/bin/env python3
"""check_registry_insert_catalog_status.py — a migration that registers an asset must set catalog_status.

NIRMĀṆA L2-W3 (L2_W2_DECIDE_v1_0.md N-20). This guard exists because the defect it
catches has now been introduced, diagnosed, swept, and re-introduced.

The history
-----------
`asset_registry.catalog_status` has DEFAULT 'DRAFT'. An INSERT that omits the column
therefore registers a fully-built, fully-consumed asset as a draft — and the Nirmāṇa
cockpit filters on catalog_status, so the asset becomes invisible to the operator
without anything failing.

`platform/migrations/294_catalog_status_current.sql` diagnosed exactly this in its own
header ("Root cause: several registry migrations omitted catalog_status from their
INSERT ... are invisible in the Nirmāṇa cockpit") and swept the assets that existed at
the time. Eight later migrations — 358, 438, 445, 446, 450, 451, 452, 453 — omitted it
again, leaving nine L2 Bodha assets DRAFT until migration 660 swept them a second time.

Sweeping is not a fix. A sweep corrects the rows that exist on the day it runs; the
next registry migration reintroduces the defect, and the only thing standing between
the two is that somebody remembers. This guard is what replaces remembering.

Why a STATIC check rather than a DB assertion
---------------------------------------------
The obvious guard is "no asset with a writer and rows may be DRAFT", which needs a live
DB and only fires AFTER the bad migration has been written, reviewed, merged and
applied. This one fires in the pull request that introduces it, needs no database, and
names the actual cause: the omission, not its consequence.

What it flags
-------------
Any `INSERT INTO asset_registry (...)` in platform/migrations/**.sql or
platform/supabase/migrations/**.sql whose explicit column list does not name
`catalog_status`.

What it does NOT flag, deliberately
-----------------------------------
  - UPDATE statements. Correcting or re-pointing an existing row is not registration,
    and migration 660 itself is full of them.
  - INSERTs that name catalog_status and set it to 'DRAFT'. A deliberate draft is a
    legitimate state; this guard is about SILENCE, not about the value. An asset that
    is genuinely not ready should say so out loud.
  - INSERT ... SELECT with no explicit column list, which cannot be read statically.
    Reported as a warning, never a failure — the guard does not claim reach it lacks.
  - Anything outside the two migration directories.

Baseline: pre-existing offenders are allowlisted by filename in ALLOWLIST below, each
with the reason it is closed. Migration 660 corrected their DATA; the files themselves
are applied and immutable (CLAUDE.md §N.4 — never edit an applied migration), so they
are quarantined rather than fixed.

Exit codes: 0 clean, 1 violation(s), 2 invocation error.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
MIGRATION_DIRS = (
    Path("platform/migrations"),
    Path("platform/supabase/migrations"),
)

# Applied, immutable migrations that omitted catalog_status before this guard existed.
# Their DATA was corrected by 294 (L0/L1 assets) and 660 (L2 Bodha assets); the files
# stay as they are because an applied migration is never edited.
ALLOWLIST: dict[str, str] = {
    # ── L2 Bodha: data corrected by migration 660 (this session) ──────────────
    "358_bodha_orphaned_writer_registry.sql":
        "bo_chart_gestalt / bo_cdlm_summary / bo_cgm_motifs / bo_cgm_paths — data corrected by 326/327 and 660",
    "438_bo_sudarshana_asset_registry.sql": "bo_sudarshana — data corrected by 660",
    "445_bodha_mechanisms.sql": "bo_yantra_mechanism — data corrected by 660",
    "446_bo_laksana_rerank_registry.sql": "bo_laksana_rerank — data corrected by 660",
    "450_bo_nakshatra_semantic_asset_registry.sql": "bo_nakshatra_semantic — data corrected by 660",
    "451_bo_arudha_asset_registry.sql": "bo_arudha — data corrected by 660",
    "452_bo_special_lagna_asset_registry.sql": "bo_special_lagna — data corrected by 660",
    "453_bo_vargottama_dhana_asset_registry.sql": "bo_vargottama_dhana — data corrected by 660",

    # ── Other layers: file quarantined here, DATA still uncorrected ───────────
    # These are NOT closed. Writing this guard surfaced that the omission reaches
    # far beyond L2: 46 assets are catalog_status='DRAFT' live, and L3 (11), L4 (9)
    # and L5 (15) are DRAFT in their ENTIRETY — layers that CLAUDE.md §E records as
    # CLOSED and SEALED. Because the cockpit filters on catalog_status, three sealed
    # layers are invisible in it.
    #
    # An applied migration is never edited (CLAUDE.md §N.4), so the file-level
    # violation is permanently unfixable and is quarantined here. The DATA fix
    # belongs to each layer's own session and its own migration range — L2 must not
    # write another layer's registry rows (charter C5). Raised for routing as a
    # NIRMĀṆA adjudication issue; see L2_STATE.md § ADJUDICATIONS RAISED.
    "266_bg_transit_tables.sql": "L0 — file immutable; live DRAFT set is L0's to correct",
    "291_ga_prashna_asset_registry.sql": "L1 — file immutable; ga_prashna disposition is L1's",
    "292_ga_nakshatra_registry.sql": "L1 — file immutable; live row is CURRENT, no data defect",
    "435_ga_vichara.sql": "L1 — file immutable; ga_vichara IS live-DRAFT, L1's to correct",
    "440_vidhi_registry_schema.sql": "L0/vidhi — file immutable; bg_vidhi_floors IS live-DRAFT, L0's to correct",
    "174_brahmagyan_naming_reconciliation.sql": "L0 — file immutable; live rows are CURRENT, no data defect",
    "179_l0_phase_alpha_asset_registry.sql": "L0 — file immutable; live rows are CURRENT, no data defect",
    "195_ganita_naming_reconciliation.sql": "L1 — file immutable; live rows are CURRENT, no data defect",
    "423_ba_lel_r2_2_step1_chart_scope.sql": "L5 — file immutable; lel_events IS live-DRAFT, L5's to correct",
    "240_ga_yoga.sql": "L1 — file immutable; live row is CURRENT, no data defect",
    "262_bg_prashna_rules_asset_registry.sql": "L0 — file immutable; live row is CURRENT, no data defect",
}

# INSERT INTO asset_registry ( ... ) — capture the parenthesised column list.
_INSERT_WITH_COLUMNS = re.compile(
    r"INSERT\s+INTO\s+(?:public\.)?asset_registry\s*\(([^)]*)\)",
    re.IGNORECASE | re.DOTALL,
)
# INSERT INTO asset_registry not followed by a column list (INSERT ... SELECT / VALUES).
_INSERT_ANY = re.compile(
    r"INSERT\s+INTO\s+(?:public\.)?asset_registry\b",
    re.IGNORECASE,
)


def _strip_sql_comments(sql: str) -> str:
    """Drop -- line comments and /* */ blocks so commented-out SQL is never flagged."""
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    return re.sub(r"--[^\n]*", " ", sql)


def scan_file(path: Path) -> tuple[list[str], list[str]]:
    """Return (violations, warnings) for one migration file."""
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:  # unreadable file is an invocation problem, not a verdict
        return ([], [f"{path}: unreadable ({exc})"])

    sql = _strip_sql_comments(raw)
    violations: list[str] = []
    warnings: list[str] = []

    with_columns = list(_INSERT_WITH_COLUMNS.finditer(sql))
    for match in with_columns:
        columns = {c.strip().strip('"').lower() for c in match.group(1).split(",")}
        if "catalog_status" not in columns:
            line = sql[: match.start()].count("\n") + 1
            violations.append(
                f"{path}:{line} — INSERT INTO asset_registry omits catalog_status from its "
                f"column list, so every row it registers silently takes the DEFAULT 'DRAFT' "
                f"and is invisible in the Nirmāṇa cockpit. Name the column explicitly — "
                f"'CURRENT' if the asset is built and consumed, 'DRAFT' if it genuinely is not."
            )

    # An INSERT with no readable column list is out of static reach. Say so; do not fail.
    if len(_INSERT_ANY.findall(sql)) > len(with_columns):
        warnings.append(
            f"{path} — contains an INSERT INTO asset_registry with no explicit column list "
            f"(INSERT ... SELECT, or a column list this scanner could not parse). Not "
            f"checked: static analysis cannot reach it, and this guard does not claim to."
        )
    return (violations, warnings)


def run_self_test() -> int:
    """Prove the scanner catches the defect and does not flag the safe forms."""
    import tempfile

    cases: list[tuple[str, str, bool]] = [
        ("omits catalog_status",
         "INSERT INTO asset_registry (asset_id, layer, target_table)\nVALUES ('x','bodha','t');",
         True),
        ("names catalog_status = CURRENT",
         "INSERT INTO asset_registry (asset_id, layer, catalog_status)\nVALUES ('x','bodha','CURRENT');",
         False),
        ("names catalog_status = DRAFT (deliberate, allowed)",
         "INSERT INTO asset_registry (asset_id, catalog_status)\nVALUES ('x','DRAFT');",
         False),
        ("UPDATE is not registration",
         "UPDATE asset_registry SET target_table='t' WHERE asset_id='x';",
         False),
        ("commented-out INSERT is not code",
         "-- INSERT INTO asset_registry (asset_id, layer) VALUES ('x','bodha');",
         False),
        ("multi-line column list, catalog_status present",
         "INSERT INTO asset_registry (\n  asset_id,\n  layer,\n  catalog_status\n) VALUES ('x','bodha','CURRENT');",
         False),
    ]
    failures = 0
    with tempfile.TemporaryDirectory() as tmp:
        for name, sql, should_flag in cases:
            p = Path(tmp) / "case.sql"
            p.write_text(sql, encoding="utf-8")
            violations, _ = scan_file(p)
            flagged = bool(violations)
            if flagged != should_flag:
                print(f"  SELF-TEST FAIL: {name!r} — expected flagged={should_flag}, got {flagged}")
                failures += 1
    if failures:
        print(f"check_registry_insert_catalog_status: SELF-TEST FAILED ({failures} case(s)).")
        return 1
    print(
        f"check_registry_insert_catalog_status: SELF-TEST PASS "
        f"({len(cases)} case(s): defect caught, safe forms silent)."
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true",
                        help="run bundled fixtures instead of scanning the repo")
    args = parser.parse_args()

    if args.self_test:
        return run_self_test()

    all_violations: list[str] = []
    all_warnings: list[str] = []
    allowlisted = 0
    scanned = 0

    for rel_dir in MIGRATION_DIRS:
        directory = REPO_ROOT / rel_dir
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.sql")):
            scanned += 1
            violations, warnings = scan_file(path)
            all_warnings.extend(warnings)
            if not violations:
                continue
            if path.name in ALLOWLIST:
                allowlisted += len(violations)
                continue
            all_violations.extend(violations)

    for warning in all_warnings:
        print(f"  [warn] {warning}")
    for violation in all_violations:
        print(f"  [violation] {violation}")

    if all_violations:
        print(
            f"check_registry_insert_catalog_status: {len(all_violations)} violation(s) "
            f"across {scanned} migration(s). FAIL."
        )
        return 1
    print(
        f"check_registry_insert_catalog_status: 0 new violations "
        f"({allowlisted} pre-existing, allowlisted; {scanned} migrations scanned). PASS."
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(2)
