"""
brahmagyan.l0_orphan_census — read-only orphan census for upsert-only L0 writers.

TI-L0-25 / CF-12 (PR #2829 INDEX section 4 item 8; SS Q12): the L0 idempotency
convention is "a rebuild replaces its own rows, never accretes", but an
`INSERT ... ON CONFLICT DO UPDATE` writer never removes a row it stopped producing,
and the saved `Idem.pattern` PASS only reads the pattern, not the accretion.
Migration 703 (2026-09-06) is the documented instance: it deleted 9 orphans
(1 `bg_parihara_rules`, 8 `bg_muhurta_factor_census`) by hand.

The census is the measurable form of the claim: for each table the writer owns,

    orphans = live natural keys - keys the writer's own code would produce today
    missing = produced keys - live natural keys          (a build that has not run, or failed)

PASS = no orphan; FAIL names them. It is a MEASUREMENT: it never deletes (the
partition-scoped prune, where orphans are found, is a separate, reviewed change) and it
opens its connection read-only.

"Produced keys" come from the writer's own pure key-producing functions (the very
functions `run()` feeds into its upserts), not from a second copy of the rules, so the
census cannot drift from the writer.

Usage (reads DATABASE_URL, or --dsn):

    python -m brahmagyan.l0_orphan_census --asset bg_parihara_rules

Exit status: 0 = PASS (no orphan), 1 = FAIL (orphans found), 2 = could not measure / NO_READING.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Sequence

Key = tuple


@dataclass(frozen=True)
class TableCensus:
    """The census of ONE table owned by an asset."""

    table: str
    key_columns: tuple[str, ...]
    produced_count: int
    live_count: int
    orphans: tuple[Key, ...] = ()      # live, but the writer no longer produces it
    missing: tuple[Key, ...] = ()      # produced, but not live
    duplicate_produced: tuple[Key, ...] = field(default=())   # the writer emits one key twice

    @property
    def verdict(self) -> str:
        if self.orphans:
            return "FAIL"
        if self.produced_count == 0:
            # Nothing to compare against: a table the writer produces no key for cannot
            # read PASS (it could not have read FAIL). CLAUDE.md N.8: null, not green.
            return "NO_READING"
        return "PASS"

    def as_dict(self) -> dict[str, Any]:
        return {
            "table": self.table,
            "key_columns": list(self.key_columns),
            "produced_count": self.produced_count,
            "live_count": self.live_count,
            "orphans": [list(k) for k in self.orphans],
            "missing": [list(k) for k in self.missing],
            "duplicate_produced": [list(k) for k in self.duplicate_produced],
            "verdict": self.verdict,
        }


def census_table(
    table: str,
    key_columns: Sequence[str],
    produced_keys: Iterable[Key],
    live_keys: Iterable[Key],
) -> TableCensus:
    """Pure set arithmetic: orphans = live - produced, missing = produced - live."""
    produced_list = [tuple(k) for k in produced_keys]
    live_list = [tuple(k) for k in live_keys]
    produced, live = set(produced_list), set(live_list)
    seen: set[Key] = set()
    dups: list[Key] = []
    for k in produced_list:
        if k in seen and k not in dups:
            dups.append(k)
        seen.add(k)
    return TableCensus(
        table=table,
        key_columns=tuple(key_columns),
        produced_count=len(produced),
        live_count=len(live),
        orphans=tuple(sorted(live - produced, key=repr)),
        missing=tuple(sorted(produced - live, key=repr)),
        duplicate_produced=tuple(sorted(dups, key=repr)),
    )


def _keys(rows: Iterable[dict[str, Any]], columns: Sequence[str]) -> list[Key]:
    return [tuple(r[c] for c in columns) for r in rows]


def _live_keys(conn: Any, table: str, columns: Sequence[str]) -> list[Key]:
    # `table` and `columns` come from the adapter below, never from user input.
    with conn.cursor() as cur:
        cur.execute(f"SELECT {', '.join(columns)} FROM {table}")  # noqa: S608
        return _keys(cur.fetchall(), columns)


# ── adapters: asset -> [(table, key columns, produced-keys function)] ─────────────────


def _bg_parihara_rules_adapter() -> list[tuple[str, tuple[str, ...], Callable[[Any, str], list[dict]]]]:
    from pipeline.orchestrator.writers.bg_parihara_rules import (
        build_activity_rule_rows,
        build_census_rows,
        fetch_parihara_rows,
    )

    return [
        ("bg_parihara_rules", ("dosha_canonical_id", "cancellation_index"),
         lambda conn, build_id: fetch_parihara_rows(conn, build_id)),
        ("bg_muhurta_activity_rules", ("activity_class", "factor_type", "factor_id"),
         lambda conn, build_id: build_activity_rule_rows(build_id)),
        ("bg_muhurta_factor_census", ("factor_family", "factor_name"),
         lambda conn, build_id: build_census_rows(build_id)),
    ]


ADAPTERS: dict[str, Callable[[], list]] = {
    "bg_parihara_rules": _bg_parihara_rules_adapter,
}


def run_census(conn: Any, asset_id: str, build_id: str = "orphan-census") -> list[TableCensus]:
    """Measure every table of `asset_id`. Reads only; the caller owns the connection."""
    if asset_id not in ADAPTERS:
        raise KeyError(
            f"no orphan-census adapter for {asset_id!r}; adapters: {sorted(ADAPTERS)}"
        )
    out: list[TableCensus] = []
    for table, columns, produce in ADAPTERS[asset_id]():
        produced = _keys(produce(conn, build_id), columns)
        out.append(census_table(table, columns, produced, _live_keys(conn, table, columns)))
    return out


def overall_verdict(tables: Sequence[TableCensus]) -> str:
    verdicts = {t.verdict for t in tables}
    if "FAIL" in verdicts:
        return "FAIL"
    if "NO_READING" in verdicts or not tables:
        return "NO_READING"
    return "PASS"


def report(asset_id: str, tables: Sequence[TableCensus]) -> dict[str, Any]:
    return {
        "asset_id": asset_id,
        "verdict": overall_verdict(tables),
        "orphan_total": sum(len(t.orphans) for t in tables),
        "tables": [t.as_dict() for t in tables],
        "note": (
            "orphans = live natural keys the writer no longer produces. A read-only "
            "measurement: nothing is deleted. `missing` is informational (a build that has "
            "not run) and does not fail the census."
        ),
    }


def _connect_read_only(dsn: str) -> Any:
    import psycopg
    from psycopg.rows import dict_row

    conn = psycopg.connect(dsn, row_factory=dict_row, options="-c default_transaction_read_only=on")
    conn.read_only = True
    return conn


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--asset", required=True, choices=sorted(ADAPTERS))
    ap.add_argument("--dsn", default=os.environ.get("DATABASE_URL"))
    args = ap.parse_args(argv)
    if not args.dsn:
        print("error: no --dsn and no DATABASE_URL", file=sys.stderr)
        return 2
    try:
        conn = _connect_read_only(args.dsn)
        try:
            rep = report(args.asset, run_census(conn, args.asset))
        finally:
            conn.rollback()
            conn.close()
    except Exception as exc:  # the census could not measure: say so, never a clean result
        print(f"error: could not measure: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(rep, indent=2, sort_keys=True, default=str))
    return {"PASS": 0, "FAIL": 1}.get(rep["verdict"], 2)


if __name__ == "__main__":
    raise SystemExit(main())
