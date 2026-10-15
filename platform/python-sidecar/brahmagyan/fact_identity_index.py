"""
fact_identity_index.py -- the ONE implementation of "populate `chart_fact_identity`
(migration 552) from `chart_facts` for ONE chart".

Two callers, one body (so they cannot drift):
  * the registered orchestrator writer `ga_fact_identity`
    (`pipeline/orchestrator/writers/ga_fact_identity.py`), on `ctx.db_conn`;
  * the hand-run script `scripts/build_fact_identity_index.py` (G-IDX), on its own
    connection, which re-exports `build_index_for_chart` / `INSERT_SQL` from here.

Rules (CLAUDE.md N.2 / N.3 / N.7 / N.8):
  * chart_facts is only ever SELECTed. The only table written is `chart_fact_identity`.
  * Per-chart delete-then-insert scoped to `chart_id`: a rebuild REPLACES, never accretes.
  * This function NEVER commits, rolls back or closes the connection it is handed; the
    caller (orchestrator savepoint / the script) owns the transaction.
  * Every cursor asks for `tuple_row` explicitly. The orchestrator's connection uses
    `dict_row` by default (pipeline/orchestrator/db.py); a bare `conn.cursor()` would make
    `fetchone()[0]` fail there.
  * Every number in the returned summary comes from a real count (total / parsed /
    identity_free / gap from the classifier; `rows_in_table` from a SELECT count(*) after the
    insert, None in a dry-run). It feeds `brahmagyan.fact_identity_check.check_identity_index`.

Import closure: this module imports only `fact_identity_check` (-> `fact_identity_parser`).
Adding the `ga_fact_identity` writer as a NEW importer edits neither file, so no other writer's
provenance digest moves (ga_panchanga already imports the parser; it is untouched here). Do not
edit the parser or the check module in a PR that must not move ga_panchanga's digest.
"""
from __future__ import annotations

import time

from brahmagyan.fact_identity_check import classify_fact

FETCH_BATCH = 20_000
INSERT_BATCH = 5_000

INSERT_SQL = """
    INSERT INTO chart_fact_identity (
        fact_id, chart_id, entity_kind, graha_code, graha_code_secondary,
        house_num, house_num_secondary, varga_id, sign_num,
        parse_rule, parsed_from, build_id, computed_at
    ) VALUES (
        %(fact_id)s, %(chart_id)s, %(entity_kind)s, %(graha_code)s, %(graha_code_secondary)s,
        %(house_num)s, %(house_num_secondary)s, %(varga_id)s, %(sign_num)s,
        %(parse_rule)s, %(parsed_from)s, %(build_id)s, now()
    )
"""


def parsed_from(fact_subject: str, fact_key: str | None) -> str:
    return f"fact_subject={fact_subject!r};fact_key={fact_key!r}"


def build_index_for_chart(conn, chart_id: str, dry_run: bool = False) -> dict:
    """Delete-then-insert scoped to `chart_id` (N.3). Returns a summary dict with the real,
    computed counts (N.8 -- every number here comes from an actual detector query / actual
    row count, not an estimate). Does not commit."""
    from psycopg.rows import tuple_row

    t0 = time.time()
    total = parsed = identity_free = gap = 0
    entity_kind_counts: dict[str, int] = {}
    identity_free_reasons: dict[str, int] = {}
    gap_examples: dict[tuple, str] = {}

    with conn.cursor(row_factory=tuple_row) as read_cur:
        read_cur.execute(
            "SELECT fact_id, fact_category, fact_subject, fact_key, build_id "
            "FROM chart_facts WHERE chart_id = %s",
            (chart_id,),
        )
        rows_to_insert = []

        with conn.cursor(row_factory=tuple_row) as write_cur:
            if not dry_run:
                write_cur.execute(
                    "DELETE FROM chart_fact_identity WHERE chart_id = %s",
                    (chart_id,),
                )
                deleted = write_cur.rowcount
            else:
                deleted = None

            while True:
                batch = read_cur.fetchmany(FETCH_BATCH)
                if not batch:
                    break
                for fact_id, fact_category, fact_subject, fact_key, build_id in batch:
                    total += 1
                    kind, payload = classify_fact(fact_category, fact_subject, fact_key)
                    if kind == "parsed":
                        match = payload
                        parsed += 1
                        entity_kind_counts[match.entity_kind] = entity_kind_counts.get(match.entity_kind, 0) + 1
                        rows_to_insert.append({
                            "fact_id": fact_id,
                            "chart_id": chart_id,
                            "entity_kind": match.entity_kind,
                            "graha_code": match.graha_code,
                            "graha_code_secondary": match.graha_code_secondary,
                            "house_num": match.house_num,
                            "house_num_secondary": match.house_num_secondary,
                            "varga_id": match.varga_id,
                            "sign_num": match.sign_num,
                            "parse_rule": match.parse_rule,
                            "parsed_from": parsed_from(fact_subject, fact_key),
                            "build_id": str(build_id) if build_id else None,
                        })
                        if len(rows_to_insert) >= INSERT_BATCH and not dry_run:
                            write_cur.executemany(INSERT_SQL, rows_to_insert)
                            rows_to_insert = []
                        continue

                    if kind == "identity_free":
                        identity_free += 1
                        identity_free_reasons[payload] = identity_free_reasons.get(payload, 0) + 1
                    else:  # "gap": neither parsed nor a recognised identity-free token
                        gap += 1
                        key = (fact_category, fact_key)
                        if key not in gap_examples:
                            gap_examples[key] = fact_subject

            if rows_to_insert and not dry_run:
                write_cur.executemany(INSERT_SQL, rows_to_insert)

            # The detector behind `rows == parsed`: count what is ACTUALLY in the
            # table for this chart after the insert (same transaction). Not
            # measured in a dry-run -> None (NOT_EVALUATED), never assumed.
            rows_in_table = None
            if not dry_run:
                write_cur.execute(
                    "SELECT count(*) FROM chart_fact_identity WHERE chart_id = %s",
                    (chart_id,),
                )
                rows_in_table = int(write_cur.fetchone()[0])

    denom = parsed + gap
    coverage_pct = (100.0 * parsed / denom) if denom else 100.0

    return {
        "chart_id": chart_id,
        "deleted_prior_rows": deleted,
        "total_facts": total,
        "parsed": parsed,
        "identity_free": identity_free,
        "gap": gap,
        "rows_in_table": rows_in_table,
        "coverage_of_identity_bearing_pct": round(coverage_pct, 4),
        "entity_kind_counts": entity_kind_counts,
        "identity_free_reasons": identity_free_reasons,
        "gap_examples": gap_examples,
        "elapsed_sec": round(time.time() - t0, 2),
    }
