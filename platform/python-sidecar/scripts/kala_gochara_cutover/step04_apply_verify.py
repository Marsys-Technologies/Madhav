#!/usr/bin/env python3
"""step04_apply_verify.py — WP10 runbook step 4 (plan §9): schema apply + verify.

Applies this run's Gochara-family migrations — 1080 through 1084 in
`platform/migrations/` (renumbered per ESCALATIONS.md E-007 addendum; the brief
text's "1075/1076" is the pre-renumber label for 1080/1081) — to the target database,
then diffs `information_schema` against the expected object list. Applied
state is verified, never assumed (§N.4). Both migration directories are
checked for a higher-numbered gochara migration before applying (E-009
re-scan discipline); if a newer one exists it is included in the apply set
and listed in the report.

Tranche 1 (PRODUCTION_TRANCHE_1_AUTHORIZED). Sheet A-2.
Reversal: each migration's own down block (1081 carries a ROLLBACK section).

NOT in the apply set, deliberately (E-010; G9_DISPOSITION_v1_0.md):
  * 1085 (G-9 bg_transit_rules repair) was RETIRED. It would abort against
    production — its BPHS sweep raises while 19 rows still cite the struck source
    — and the repair it performs was already applied by the L0 session (PR #2727).
  * 1086 (G-10 ga_strength contributor digest spec) is an L1 registry change. Sheet
    A-2 authorises this tranche's schema step as the Gochara migrations only; an L1
    governed-digest revision needs its own authorisation and a matching writer
    deploy + rebuild, so it is applied by the L1 lane, never here.

Usage:
    python3 step04_apply_verify.py --dsn postgresql://... [--evidence]

Exit codes:
    0 — all migrations applied; information_schema diff empty
    3 — cannot proceed (driver/files missing)
    4 — refused: production DSN without the tranche flag
    5 — a migration failed or the post-apply diff is non-empty
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import connect, step_parser, write_evidence  # noqa: E402

MIGRATION_DIRS = [
    Path(__file__).resolve().parents[3] / "migrations",
    Path(__file__).resolve().parents[3] / "supabase" / "migrations",
]

# The migrations this cutover applies, in order. 1080-1084 only — see the module
# docstring for why 1085 (retired) and 1086 (L1 lane) are absent.
APPLY_SET = [
    "1080_nirmana_l3_gochara_resonance_target_resolution_state.sql",
    "1081_nirmana_l3_gochara_ledger_coverage_publication.sql",
    "1082_nirmana_l3_vedha_moorti_stamp_columns.sql",
    "1083_l5_ledger_contact_id.sql",
    "1084_wp7_k1_v1_registry_edges.sql",
]

# Numbers that must never be applied by this script, whatever a re-scan finds.
REFUSED = {
    "1085": "retired (E-010): would abort in production; repair already applied by L0",
    "1086": "L1 ga_strength digest revision — not authorised by sheet A-2 for this tranche",
}

# Expected post-apply state, as (relation, column) pairs for the ALTER
# migrations and bare relation names for the CREATE TABLE migrations.
EXPECTED_COLUMNS = [
    ("gochara_resonance_map", "target_resolution_state"),
    ("gochara_resonance_map", "target_qualifier"),
    ("kala_vedha_gochara", "source_qualification"),
    ("kala_vedha_gochara", "precision_regime"),
    ("kala_moorti_nirnaya", "source_qualification"),
    ("kala_moorti_nirnaya", "precision_regime"),
    ("brahma_prospective_ledger", "contact_id"),
    ("mimamsa_predictions", "contact_id"),
]
EXPECTED_TABLES = [
    "kala_gochara_convention",
    "kala_gochara_publication",
    "kala_gochara_contacts",
    "kala_gochara_coverage",
]
EXPECTED_TRIGGER = ("kala_gochara_convention", "kala_gochara_convention_immutable")
EXPECTED_INDEXES = [
    "kala_gochara_publication_one_published",
    "idx_kgpub_chart",
    "idx_kgc_serve_p4",
    "idx_kgc_independence",
    "idx_kgc_target",
    "idx_kgcov_chart",
]


def assert_no_refused_migrations(apply_set=None):
    """Fail closed if the apply set contains a number this script must never apply.

    Reads REFUSED, so the refusal is a real check and not a comment: re-adding 1085
    or 1086 to APPLY_SET makes this exit 3 before any database is touched.
    """
    for name in (APPLY_SET if apply_set is None else apply_set):
        num = name.split("_", 1)[0]
        if num in REFUSED:
            print(f"ERROR: refusing to apply {name}: {REFUSED[num]}", file=sys.stderr)
            sys.exit(3)


def find_migrations():
    assert_no_refused_migrations()
    found = {}
    for d in MIGRATION_DIRS:
        if not d.exists():
            continue
        for f in d.iterdir():
            m = re.match(r"(\d+)_.*\.sql$", f.name)
            if m and f.name in APPLY_SET:
                found[f.name] = f
    missing = [n for n in APPLY_SET if n not in found]
    if missing:
        print(f"ERROR: migration files not found: {missing}", file=sys.stderr)
        sys.exit(3)
    return [found[n] for n in APPLY_SET]


def verify(conn) -> list[str]:
    """Return the list of missing expected objects (empty = gate green)."""
    missing = []
    with conn.cursor() as cur:
        for table, column in EXPECTED_COLUMNS:
            cur.execute(
                "SELECT count(*) FROM information_schema.columns "
                "WHERE table_schema='public' AND table_name=%s AND column_name=%s",
                (table, column))
            if cur.fetchone()[0] == 0:
                missing.append(f"column {table}.{column}")
        for table in EXPECTED_TABLES:
            cur.execute(
                "SELECT count(*) FROM information_schema.tables "
                "WHERE table_schema='public' AND table_name=%s", (table,))
            if cur.fetchone()[0] == 0:
                missing.append(f"table {table}")
        cur.execute(
            "SELECT count(*) FROM information_schema.triggers "
            "WHERE trigger_schema='public' AND event_object_table=%s AND trigger_name=%s",
            EXPECTED_TRIGGER)
        if cur.fetchone()[0] == 0:
            missing.append(f"trigger {EXPECTED_TRIGGER[1]} on {EXPECTED_TRIGGER[0]}")
        for idx in EXPECTED_INDEXES:
            cur.execute("SELECT to_regclass(%s)", (f"public.{idx}",))
            if cur.fetchone()[0] is None:
                missing.append(f"index {idx}")
    return missing


def main() -> int:
    parser = step_parser(4, __doc__)
    args = parser.parse_args()
    conn = connect(args.dsn, step=4)
    applied, failed = [], []
    for path in find_migrations():
        sql = path.read_text()
        up = sql.split("-- DOWN (manual rollback):")[0]
        try:
            with conn.cursor() as cur:
                cur.execute(up)
        except Exception as exc:  # noqa: BLE001
            failed.append((path.name, str(exc)))
            break
        applied.append(path.name)
    missing = verify(conn) if not failed else ["(verify skipped: apply failed)"]
    conn.close()

    for name in applied:
        print(f"applied: {name}")
    if failed:
        print(f"FAILED: {failed[0][0]}: {failed[0][1]}", file=sys.stderr)
    ok = not failed and not missing
    if missing and not failed:
        print("information_schema diff — MISSING:", file=sys.stderr)
        for item in missing:
            print(f"  {item}", file=sys.stderr)
    if args.evidence:
        write_evidence(
            4, "GREEN" if ok else "RED",
            "applied: " + ", ".join(applied)
            + ("\nmissing:\n" + "\n".join(f"- {m}" for m in missing) if missing else ""))
    return 0 if ok else 5


if __name__ == "__main__":
    sys.exit(main())
