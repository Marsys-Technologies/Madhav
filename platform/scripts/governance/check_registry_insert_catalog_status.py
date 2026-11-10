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

Baseline: exact repository paths and SHA-256 digests identify the applied,
immutable migrations exempt from this check (CLAUDE.md §N.4). Dispositions
below refer to later source evidence and do not attest to live database state.

Exit codes: 0 clean, 1 violation(s), 2 invocation error.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
MIGRATION_DIRS = (
    Path("platform/migrations"),
    Path("platform/supabase/migrations"),
)

# Historical source exceptions. Match both path and bytes before exempting any finding.
ALLOWLIST: dict[str, str] = {
    # bo_chart_gestalt / bo_cdlm_summary / bo_cgm_motifs / bo_cgm_paths — data corrected by 326/327 and 660
    "platform/migrations/358_bodha_orphaned_writer_registry.sql":
        "b4216382bb279f5e97bc141904962f7c1583539d995b756950be119582634496",
    # bo_sudarshana — data corrected by 660
    "platform/migrations/438_bo_sudarshana_asset_registry.sql":
        "0ae74c6f782f5413a40cea37603bc8ddb4b9a1caa7a56aa8f1ee3940ad777de8",
    # bo_yantra_mechanism — data corrected by 660
    "platform/migrations/445_bodha_mechanisms.sql":
        "5bbfc9a3c0477d4237369efcc8b6d256771c50ae5fc3c049bc68769a1ee6fca9",
    # bo_laksana_rerank — data corrected by 660
    "platform/migrations/446_bo_laksana_rerank_registry.sql":
        "c355605fe1ee27ba47e0b5adbd35b568ea05fbbfab761fdf3120dc020d6f19e3",
    # bo_nakshatra_semantic — data corrected by 660
    "platform/migrations/450_bo_nakshatra_semantic_asset_registry.sql":
        "dd71357eaf0cb3f56dad6b7645fc781f80ae180c8a3f3919ae257dfa6d3b28b7",
    # bo_arudha — data corrected by 660
    "platform/migrations/451_bo_arudha_asset_registry.sql":
        "7608b8e236482118f20be6817c291f095da3a88f0d74b68fcc7a56d38c13a331",
    # bo_special_lagna — data corrected by 660
    "platform/migrations/452_bo_special_lagna_asset_registry.sql":
        "a3397791ce3120a86fe2576b7400ea9d56868b8bbd56ede751ff4c1eccece8e2",
    # bo_vargottama_dhana — data corrected by 660
    "platform/migrations/453_bo_vargottama_dhana_asset_registry.sql":
        "a08c8206cc02d9e16cfc5d831a977702de89f328166038b72c0df213fe638e7e",
    # 294 promotes both bg_transit_engine and bg_transit_rules.
    "platform/migrations/266_bg_transit_tables.sql":
        "0c1ec8e3eb8ac57adfb32e0597c77d217ab386f280c6fe811594122a021cbe1b",
    # 650 records the owner-approved dormant disposition.
    "platform/migrations/291_ga_prashna_asset_registry.sql":
        "c6b7c35020cff5af0e8c0b7d5f66037195f3195e61034c895406c5a223e39a88",
    # 294 promotes ga_nakshatra.
    "platform/migrations/292_ga_nakshatra_registry.sql":
        "39943574018a85258c381069b3d055364f482651b03f927d899f4a0af7287332",
    # 650 promotes ga_vichara.
    "platform/migrations/435_ga_vichara.sql":
        "9d7301556a60ff9f87ce5088b553def7f8d72db7b5cad37e159a9a436668217a",
    # 642 records CURRENT primitives and the intentional DRAFT floors.
    "platform/migrations/440_vidhi_registry_schema.sql":
        "a4e0761f2bea17cb231b9fc289c741ee053c42d05de962b97d56ab64d9c5c8ff",
    # L0 — file immutable; live rows are CURRENT, no data defect
    "platform/supabase/migrations/174_brahmagyan_naming_reconciliation.sql":
        "173152db2607efa51ffd0ffd7ac626b71a3683ec8cdddf1fe2f1d91969a3cc2c",
    # L0 — file immutable; live rows are CURRENT, no data defect
    "platform/supabase/migrations/179_l0_phase_alpha_asset_registry.sql":
        "80a9418aa2fb95c6bc7b580249d1cb4acde5c51aeab44876b07fd47e95b9f794",
    # L1 — file immutable; live rows are CURRENT, no data defect
    "platform/supabase/migrations/195_ganita_naming_reconciliation.sql":
        "358b4558b45652fe5496de6396f34fb3491c4b027c8fc01f18feda1b159f1d78",
    # 691 promotes lel_events.
    "platform/supabase/migrations/423_ba_lel_r2_2_step1_chart_scope.sql":
        "a53007047c5d5b4ad0f79212a9c9d651e5ca2746bbe3319f5cc8e0c67c1df126",
    # L1 — file immutable; live row is CURRENT, no data defect
    "platform/migrations/240_ga_yoga.sql":
        "daf58ccc136be72ab6b17103e4b175b47be27b025a03ca3e60779b0b01acd96b",
    # 294 promotes bg_prashna_rules.
    "platform/migrations/262_bg_prashna_rules_asset_registry.sql":
        "d5c9b6b2565e5e8f6959a986050a1f5806dbd1007edf9c7800df7e0170996d8a",
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
    missing_exceptions = set(ALLOWLIST)

    for rel_dir in MIGRATION_DIRS:
        directory = REPO_ROOT / rel_dir
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.sql")):
            scanned += 1
            violations, warnings = scan_file(path)
            all_warnings.extend(warnings)
            rel_path = path.relative_to(REPO_ROOT).as_posix()
            expected_digest = ALLOWLIST.get(rel_path)
            if expected_digest is not None:
                missing_exceptions.discard(rel_path)
                if hashlib.sha256(path.read_bytes()).hexdigest() == expected_digest:
                    allowlisted += len(violations)
                    continue
                all_violations.append(f"{rel_path} — immutable migration bytes changed")
            all_violations.extend(violations)

    for rel_path in sorted(missing_exceptions):
        all_violations.append(f"{rel_path} — immutable migration missing")

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
