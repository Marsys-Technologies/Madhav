#!/usr/bin/env python3
"""backfill_ga_sensitive_honest_tier.py — T3(d) of the post-salvage close-out (S7 ruling).

`ga_sensitive_writer.py`'s build-fatal guard used to HALT the entire build the instant any row
computed as `single` (no second derivation ran). Owner ruling (2026-08-06, CLAUDE.md §N.2 amended):
`single` is a permitted tier for `ga_sensitive` — the guard now logs and stores those rows honestly
instead of crashing the build (see the two guard sites in `ga_sensitive_writer.py`).

Because the OLD guard raised before any INSERT happened, it could not have left mistagged rows
behind — a halted build persists nothing. This script exists as the audit record for that claim and
as a standing check for the future: if `ga_sensitive`-sourced `chart_facts` rows are ever found
outside the settled vocabulary's legitimate tiers for this writer (`two_pass_verified`, `floored`,
or the now-permitted `single`), it reports them for a real backfill decision. It does not invent a
demotion target — a mistagged row here would need a case-by-case call, not a blanket rule.

`ga_sensitive` rows are identified via `source_calculation LIKE 'pyjhora_adapter.sensitive/%'`
(the writer's own default source_calculation, chart_facts has no dedicated writer/asset_id column).

USAGE
-----
    python backfill_ga_sensitive_honest_tier.py            # report only; this script never writes

DATABASE_URL is read from the environment and is never taken as an argument.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "python-sidecar"))

from brahmagyan.verification_vocab import UNVERIFIED_DEFAULT  # noqa: E402

LEGITIMATE_TIERS = {"two_pass_verified", "floored", UNVERIFIED_DEFAULT}
SOURCE_PATTERN = "pyjhora_adapter.sensitive/%"


def main() -> int:
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        print("DATABASE_URL is not set; refusing to guess.", file=sys.stderr)
        return 2

    import psycopg

    with psycopg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT verification_pass_status, count(*) FROM chart_facts "
            "WHERE source_calculation LIKE %s GROUP BY 1 ORDER BY 2 DESC",
            (SOURCE_PATTERN,),
        )
        rows = cur.fetchall()

    print("ga_sensitive-sourced chart_facts rows by tier:")
    total = 0
    outside_vocab: dict[str, int] = {}
    for status, n in rows:
        total += n
        flag = "" if status in LEGITIMATE_TIERS else "  <-- OUTSIDE the legitimate set for this writer"
        print(f"  {status:<20} {n:>8,}{flag}")
        if status not in LEGITIMATE_TIERS:
            outside_vocab[status] = n

    print(f"\n{total:,} row(s) total.")
    if not outside_vocab:
        print("Nothing to backfill: every existing ga_sensitive row already carries a legitimate "
              "tier (two_pass_verified, floored, or the now-permitted single).")
        return 0

    print(
        f"\n{sum(outside_vocab.values()):,} row(s) carry a tier outside the legitimate set: "
        f"{outside_vocab}. This needs a case-by-case backfill decision — this script intentionally "
        f"does not guess a blanket demotion target.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
