"""§12.9 — is a chart's house_vedha output built from what the reference tables say NOW?

The detector the L0 re-citation exposed the absence of (CLAUDE.md §N.8). A house_vedha
row carries `detail.upstream_fingerprint`, the digest of the `bg_transit_rules` and
`bg_vedha_malefic_scale` rows its build consumed (logic.upstream_fingerprint). This
module recomputes the same digest from the live tables — through the WRITER'S OWN fetch
functions, so the two cannot drift apart — and compares.

States (only `fresh` admits a build):
  fresh         every house_vedha row carries a fingerprint equal to the current one
  stale         at least one row has no fingerprint (built before this existed —
                unknown provenance) or a fingerprint that no longer matches
  no_rows       the chart has no house_vedha rows (nothing was built; not "fresh")
  table_absent  kala_vedha_gochara does not exist (NOT_RUN, never a pass)

Reports counts only. No row content is returned.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import psycopg.rows

from services.ka_vedha_gochara.logic import upstream_fingerprint
from services.ka_vedha_gochara.writer import _fetch_malefic_scale, _fetch_vedha_rules

FRESH, STALE, NO_ROWS, TABLE_ABSENT = "fresh", "stale", "no_rows", "table_absent"


@dataclass
class FreshnessReport:
    state: str
    total: int
    missing: int      # rows with no upstream_fingerprint at all
    mismatched: int   # rows whose fingerprint differs from the current one
    current: Optional[dict]

    def summary(self) -> str:
        return (f"house_vedha freshness: {self.state} — {self.total} rows, "
                f"{self.missing} without a fingerprint, {self.mismatched} mismatched")


def current_fingerprint(conn: Any) -> dict:
    """The fingerprint a rebuild would stamp right now (same fetch path as the writer)."""
    return upstream_fingerprint(_fetch_vedha_rules(conn), _fetch_malefic_scale(conn))


def check_house_vedha_freshness(conn: Any, chart_id: str) -> FreshnessReport:
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute("SELECT to_regclass('kala_vedha_gochara') AS t")
        if cur.fetchone()["t"] is None:
            return FreshnessReport(TABLE_ABSENT, 0, 0, 0, None)
        cur.execute(
            "SELECT detail->'upstream_fingerprint' AS fp FROM kala_vedha_gochara "
            "WHERE chart_id = %s AND vedha_kind = 'house_vedha'",
            (chart_id,),
        )
        stored = [r["fp"] for r in cur.fetchall()]
    if not stored:
        return FreshnessReport(NO_ROWS, 0, 0, 0, None)
    current = current_fingerprint(conn)
    missing = sum(1 for fp in stored if fp is None)
    mismatched = sum(1 for fp in stored if fp is not None and fp != current)
    state = FRESH if missing == 0 and mismatched == 0 else STALE
    return FreshnessReport(state, len(stored), missing, mismatched, current)


def gate_allows_build(report: FreshnessReport) -> bool:
    """Only a FRESH report admits a candidate build. Every other state blocks."""
    return report.state == FRESH
