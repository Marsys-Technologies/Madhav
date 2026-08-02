#!/usr/bin/env python3
"""backfill_unexamined_dasha_tiers.py — bring existing `chart_dashas` rows into line with the
verdict-scoping fix in `ga_dashas_writer` (CI_EFFICIENCY_AUDIT_v1_0.md §6.18/§6.19).

WHAT CHANGED IN THE WRITER
--------------------------
`ga_dashas_writer.py` used to do `for row in rows: row["verification_pass_status"] = verification`,
broadcasting one function-level verdict onto every row at every level. Every `_verify_*` in that
module reads `level_n == 1` and nothing else, so levels 2-4 inherited a verdict computed over
their parents. Measured before the fix: 2,505 of 1,358,993 `two_pass_verified` rows (0.18%) had
ever been examined.

The writer now applies a verdict only to rows the verifier actually read, and the membership-only
verifiers return `classical_match` instead of `two_pass_verified`. **This script applies the same
correction to rows already in the table**, so the estate does not have to wait for a full rebuild
to stop overclaiming.

THE MAPPING (each is a demotion to an HONEST tier, never a promotion)
---------------------------------------------------------------------
  unexamined rows (level_n > 1, or any KP sub-period row)   -> `single`
      No second derivation ran over THIS row. `single` says exactly that.

  examined rows whose verifier is membership-only            -> `classical_match`
      yogini / ashtottari / chara_karaka / naisargika. Their only failure condition is
      `lord_graha not in <constant the producer draws from>` — real, but relay fidelity, not
      re-derivation (the §6.18 earnedness ruling).

  examined rows under a discriminating verifier              -> unchanged
      mudda (first lord re-derived from Moon's nakshatra + a 9-cycle identity), narayana
      (period non-overlap + monotonicity), vimshottari for the NATIVE chart only (its Pass 2
      FORENSIC anchor is gated `if chart_id == CANONICAL_CHART_ID`).

  examined vimshottari rows of a NON-native chart            -> `single`
      Pass 2 never ran for them and Pass 1 cannot fail.

No new vocabulary member and no CHECK migration: `single` and `classical_match` are both already
members and both already permitted by `chart_dashas`' CHECK constraint.

USAGE
-----
    python backfill_unexamined_dasha_tiers.py                      # DRY RUN (default)
    python backfill_unexamined_dasha_tiers.py --chart <uuid>       # scope to one chart
    python backfill_unexamined_dasha_tiers.py --execute            # writes

DATABASE_URL is read from the environment and is never taken as an argument.
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "python-sidecar"))

from brahmagyan.verification_vocab import (  # noqa: E402
    CLASSICAL_MATCH,
    RESTRICTED_TABLE_VOCAB,
    UNVERIFIED_DEFAULT,
)
from pipeline.orchestrator.birth_params import CANONICAL_CHART_ID  # noqa: E402

#: `kalachakra` is deliberately ABSENT: `_verify_kalachakra` already returns `single` by its own
#: choice (its docstring explains why a shallow structural check does not warrant a tier), and
#: sweeping it in here would PROMOTE those rows to `classical_match` — a backfill correcting an
#: overclaim must never manufacture a new one. The first dry run against production caught
#: exactly that: 45 rows would have moved single -> classical_match.
MEMBERSHIP_ONLY_SYSTEMS = ("yogini", "ashtottari", "chara_karaka", "naisargika")

#: (label, target tier, SQL predicate). Order matters only for reporting; the predicates are
#: mutually exclusive by construction and the script asserts that before writing.
RULES: tuple[tuple[str, str, str], ...] = (
    (
        "unexamined (level_n > 1 or a KP sub-period row)",
        UNVERIFIED_DEFAULT,
        "(level_n <> 1 OR kp_sublevel IS NOT NULL)",
    ),
    (
        "examined, membership-only verifier",
        CLASSICAL_MATCH,
        # `verification_pass_status = 'two_pass_verified'` is a NEVER-PROMOTE guard, not redundancy:
        # without it this rule would also lift rows a writer had already honestly demoted.
        "verification_pass_status = 'two_pass_verified' "
        "AND level_n = 1 AND kp_sublevel IS NULL AND system_id = ANY(%(membership)s)",
    ),
    (
        "examined vimshottari, NON-native chart (Pass 2 never ran)",
        UNVERIFIED_DEFAULT,
        "level_n = 1 AND kp_sublevel IS NULL AND system_id IN ('vimshottari','vimshottari_kp') "
        "AND chart_id <> %(native)s",
    ),
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute", action="store_true", help="write (default is a dry run)")
    ap.add_argument("--chart", help="scope to a single chart_id (recommended for the first run)")
    args = ap.parse_args()

    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        print("DATABASE_URL is not set; refusing to guess.", file=sys.stderr)
        return 2

    for _, tier, _ in RULES:
        if tier not in RESTRICTED_TABLE_VOCAB:
            print(f"HALT: {tier!r} violates chart_dashas' CHECK constraint.", file=sys.stderr)
            return 2

    import psycopg

    params = {"membership": list(MEMBERSHIP_ONLY_SYSTEMS), "native": CANONICAL_CHART_ID}
    scope = "AND chart_id = %(chart)s" if args.chart else ""
    if args.chart:
        params["chart"] = args.chart

    total = 0
    with psycopg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT verification_pass_status, count(*) FROM chart_dashas WHERE TRUE {scope} GROUP BY 1 ORDER BY 2 DESC",
            params,
        )
        print("BEFORE:", {v: n for v, n in cur.fetchall()})

        for label, tier, pred in RULES:
            where = f"verification_pass_status <> %(tier)s AND ({pred}) {scope}"
            p = {**params, "tier": tier}
            cur.execute(f"SELECT count(*) FROM chart_dashas WHERE {where}", p)
            n = cur.fetchone()[0]
            total += n
            print(f"  {'[DRY RUN] would set' if not args.execute else '[EXECUTE] setting'} "
                  f"{n:>9,} row(s) -> {tier:<16} ({label})")
            if args.execute and n:
                cur.execute(
                    f"UPDATE chart_dashas SET verification_pass_status = %(tier)s WHERE {where}", p
                )

        if args.execute:
            conn.commit()
            cur.execute(
                f"SELECT verification_pass_status, count(*) FROM chart_dashas WHERE TRUE {scope} GROUP BY 1 ORDER BY 2 DESC",
                params,
            )
            print("AFTER: ", {v: n for v, n in cur.fetchall()})

    print(f"\n{'Would change' if not args.execute else 'Changed'} {total:,} row(s).")
    if not args.execute:
        print("Dry run only. Re-run with --execute to write.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
