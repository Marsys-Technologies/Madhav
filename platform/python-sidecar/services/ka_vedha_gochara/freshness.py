"""§12.9 + step 3 §4 — are a chart's overlay rows (house_vedha AND mūrti) built from what
the reference tables, the node series and the L1 natal operands say NOW?

The detector the L0 re-citation exposed the absence of (CLAUDE.md §N.8). A house_vedha
row carries `detail.upstream_fingerprint`, the digest of the `bg_transit_rules` and
`bg_vedha_malefic_scale` rows its build consumed (logic.upstream_fingerprint); a mūrti row
carries `upstream_fingerprint` for `bg_transit_moorti`. Step 3 §4 folds three more
components into both fingerprints, closing the gate's blindness to the L1 inputs and the
node series: the writer's `formula_version`, the consumed L1 natal-operand identity
(`l1` — fact_id, build_id, stored value text, via the ONE shared helper the writer also
calls) and the consumed node-series identity (`node_series` — the L0-owned
node_series_digest_v1 SQL, raising NodeSeriesError on an empty series). This module
recomputes the same fingerprint from the live tables — through the WRITER'S OWN fetch
functions, so the two cannot drift apart — and compares.

States (only `fresh` admits a build):
  fresh         every overlay row carries a fingerprint equal to the current one
  stale         at least one row has no fingerprint (built before this existed or of a
                kind the writer does not stamp yet — unknown provenance) or a fingerprint
                that no longer matches; also the state when the L1 operand is absent
                (reason `l1_operand_absent`) — never `fresh` on an uncomputable identity
  no_rows       the chart has no overlay rows (nothing was built; not "fresh")
  table_absent  the overlay table does not exist (NOT_RUN, never a pass)

The vedha check reads ALL vedha kinds (step 3 §4.5): rows of a kind that carries no
fingerprint count as `missing` ⇒ stale. `FreshnessReport.components` names how many rows
differ in each component (`rules`, `scale`, `node_series`, `l1`, `formula_version`,
`unstamped`), so a stale verdict is diagnosable.

Reports counts only. No row content is returned.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

import psycopg.rows

from services.gochara_kernel.l1_identity import L1OperandAbsentError, l1_operand_identity
from services.gochara_kernel.node_series_digest import node_series_identity
from services.ka_moorti_nirnaya.logic import moorti_upstream_fingerprint
from services.ka_moorti_nirnaya.writer import (
    _fetch_moorti_table,
    CANONICAL_AYANAMSHA as MOORTI_AYANAMSHA,
    FORMULA_VERSION as MOORTI_FORMULA_VERSION,
    L1_OPERANDS as MOORTI_L1_OPERANDS,
)
from services.ka_vedha_gochara.logic import upstream_fingerprint
from services.ka_vedha_gochara.writer import (
    _fetch_malefic_scale,
    _fetch_vedha_rules,
    CANONICAL_AYANAMSHA as VEDHA_AYANAMSHA,
    FORMULA_VERSION as VEDHA_FORMULA_VERSION,
    L1_OPERANDS as VEDHA_L1_OPERANDS,
)

FRESH, STALE, NO_ROWS, TABLE_ABSENT = "fresh", "stale", "no_rows", "table_absent"

#: the L1 identity could not be computed (a declared operand has no chart_facts row)
L1_OPERAND_ABSENT = "l1_operand_absent"

# Which fingerprint keys each diagnosable component compares (step 3 §4.5).
_COMPONENT_KEYS = {
    "rules": ("bg_transit_rules", "n_transit_rules", "bg_transit_moorti", "n_moorti_rows"),
    "scale": ("bg_vedha_malefic_scale", "n_malefic_scale_rows"),
    "node_series": ("node_series",),
    "l1": ("l1",),
    "formula_version": ("formula_version",),
}


@dataclass
class FreshnessReport:
    state: str
    total: int
    missing: int      # rows with no upstream_fingerprint at all
    mismatched: int   # rows whose fingerprint differs from the current one
    current: Optional[dict]
    components: dict = field(default_factory=dict)  # per-component differing-row counts
    reason: Optional[str] = None                    # e.g. L1_OPERAND_ABSENT

    def summary(self) -> str:
        base = (f"overlay freshness: {self.state} — {self.total} rows, "
                f"{self.missing} without a fingerprint, {self.mismatched} mismatched")
        if self.reason:
            base += f" (reason: {self.reason})"
        if self.components:
            differing = {k: v for k, v in self.components.items() if v}
            if differing:
                base += f" components={differing}"
        return base


def _component_counts(stored: list, current: dict) -> dict:
    """How many stored rows differ from `current` in each named component; a row with
    NO fingerprint counts once under 'unstamped' (and in nothing else)."""
    counts = {name: 0 for name in (*_COMPONENT_KEYS, "unstamped")}
    for fp in stored:
        if fp is None:
            counts["unstamped"] += 1
            continue
        for name, keys in _COMPONENT_KEYS.items():
            if any(fp.get(k) != current.get(k) for k in keys):
                counts[name] += 1
    return counts


def current_fingerprint(conn: Any, chart_id: str) -> dict:
    """The fingerprint a rebuild would stamp right now (same fetch path as the writer):
    the consumed reference rows, the consumed node-series identity (raising
    NodeSeriesError on an empty series), the consumed L1 natal-operand identity
    (raising L1OperandAbsentError when absent) and the writer's formula_version."""
    return upstream_fingerprint(
        _fetch_vedha_rules(conn), _fetch_malefic_scale(conn),
        node_series=node_series_identity(conn),
        l1=l1_operand_identity(conn, chart_id, VEDHA_AYANAMSHA, VEDHA_L1_OPERANDS),
        formula_version=VEDHA_FORMULA_VERSION,
    )


def check_house_vedha_freshness(conn: Any, chart_id: str) -> FreshnessReport:
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute("SELECT to_regclass('kala_vedha_gochara') AS t")
        if cur.fetchone()["t"] is None:
            return FreshnessReport(TABLE_ABSENT, 0, 0, 0, None)
        # Step 3 §4.5: ALL vedha kinds — a row of any kind without a fingerprint
        # counts as stale (missing), never silently skipped.
        cur.execute(
            "SELECT detail->'upstream_fingerprint' AS fp FROM kala_vedha_gochara "
            "WHERE chart_id = %s",
            (chart_id,),
        )
        stored = [r["fp"] for r in cur.fetchall()]
    if not stored:
        return FreshnessReport(NO_ROWS, 0, 0, 0, None)
    try:
        current = current_fingerprint(conn, chart_id)
    except L1OperandAbsentError:
        # The identity cannot be computed — stale, never fresh (step 3 §4.1).
        return FreshnessReport(STALE, len(stored), 0, len(stored), None,
                               reason=L1_OPERAND_ABSENT)
    missing = sum(1 for fp in stored if fp is None)
    mismatched = sum(1 for fp in stored if fp is not None and fp != current)
    state = FRESH if missing == 0 and mismatched == 0 else STALE
    return FreshnessReport(state, len(stored), missing, mismatched, current,
                           components=_component_counts(stored, current))


def gate_allows_build(report: FreshnessReport) -> bool:
    """Only a FRESH report admits a candidate build. Every other state blocks."""
    return report.state == FRESH


# ── mūrti: the same defect class on the second overlay writer ────────────────
def current_moorti_fingerprint(conn: Any, chart_id: str) -> dict:
    """The fingerprint a mūrti rebuild would stamp right now (same fetch path as the
    writer), with the same step-3 §4 components as the vedha fingerprint."""
    return moorti_upstream_fingerprint(
        _fetch_moorti_table(conn),
        node_series=node_series_identity(conn),
        l1=l1_operand_identity(conn, chart_id, MOORTI_AYANAMSHA, MOORTI_L1_OPERANDS),
        formula_version=MOORTI_FORMULA_VERSION,
    )


def check_moorti_freshness(conn: Any, chart_id: str) -> FreshnessReport:
    """Same contract as check_house_vedha_freshness, for kala_moorti_nirnaya.

    A NULL fingerprint is a row built before fingerprints existed: unknown provenance, STALE.
    Counts only; returns no row content.
    """
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute("SELECT to_regclass('kala_moorti_nirnaya') AS t")
        if cur.fetchone()["t"] is None:
            return FreshnessReport(TABLE_ABSENT, 0, 0, 0, None)
        cur.execute(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = 'kala_moorti_nirnaya' AND column_name = 'upstream_fingerprint'"
        )
        has_col = cur.fetchone() is not None
        if not has_col:
            # Migration 1082 not applied: every existing row is unfingerprinted by definition.
            cur.execute("SELECT count(*) AS n FROM kala_moorti_nirnaya WHERE chart_id = %s", (chart_id,))
            n = cur.fetchone()["n"]
            return FreshnessReport(STALE if n else NO_ROWS, n, n, 0, None)
        cur.execute("SELECT upstream_fingerprint AS fp FROM kala_moorti_nirnaya WHERE chart_id = %s", (chart_id,))
        stored = [r["fp"] for r in cur.fetchall()]
    if not stored:
        return FreshnessReport(NO_ROWS, 0, 0, 0, None)
    try:
        current = current_moorti_fingerprint(conn, chart_id)
    except L1OperandAbsentError:
        return FreshnessReport(STALE, len(stored), 0, len(stored), None,
                               reason=L1_OPERAND_ABSENT)
    missing = sum(1 for fp in stored if fp is None)
    mismatched = sum(1 for fp in stored if fp is not None and fp != current)
    state = FRESH if missing == 0 and mismatched == 0 else STALE
    return FreshnessReport(state, len(stored), missing, mismatched, current,
                           components=_component_counts(stored, current))


def check_overlay_freshness(conn: Any, chart_id: str) -> dict:
    """Both overlay writers, keyed by name. One fresh writer must not mask a stale one."""
    return {
        "house_vedha": check_house_vedha_freshness(conn, chart_id),
        "moorti": check_moorti_freshness(conn, chart_id),
    }


def gate_allows_overlays(reports: dict) -> bool:
    """Admit a candidate build only if EVERY overlay writer reads fresh."""
    return all(gate_allows_build(r) for r in reports.values())
