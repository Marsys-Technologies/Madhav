"""
service.py — KaDashaKalaService: main entry point for the Dasa-Eligibility service.

Orchestrates:
  1. Lazy pruning tree-walk over chart_dashas (via tree_walk.py)
  2. Eligibility scoring (via eligibility.py)
  3. Cross-dasa agreement computation across 7 systems
  4. Level-4 (Sookshma) floor with optional in-memory Prana subdivision

All 7 systems (vimshottari, yogini, ashtottari, chara_karaka, naisargika,
mudda, kalachakra) are queried.  KP is a Vimshottari sub-level dimension
(kp_sublevel column) -- NOT a standalone system.

NEVER writes to DB.  NEVER calls conn.commit() / conn.rollback().
NEVER persists level-5 (Prana) intervals.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Optional, Set

from .eligibility import EligibilityBand
from .intersection import intersect_segments, agreement_for
from .tree_walk import DashaInterval, walk_eligible_intervals, ALL_DASHA_SYSTEMS

logger = logging.getLogger(__name__)


@dataclass
class CrossDashaAgreement:
    """How many of the 7 systems independently flag a window as eligible."""
    count: int
    systems_agreeing: list[str]


@dataclass
class EligibleWindow:
    """A single eligible interval with eligibility score + cross-dasa agreement."""
    dasha_row_id: str
    chart_id: str
    ayanamsha_id: str
    system_id: str
    level_n: int
    lord_graha: str
    start_date: date
    end_date: date
    ancestor_lords: list[str]
    eligibility_band: EligibilityBand
    eligibility_score: float
    cross_dasha_agreement: CrossDashaAgreement
    kp_sublevel: Optional[str] = None
    kp_sub_lord: Optional[str] = None
    is_prana_computed: bool = False   # True if this is an in-memory level-5 row


@dataclass
class KaDashaKalaResult:
    """Full result from KaDashaKalaService.query()."""
    chart_id: str
    ayanamsha_id: str
    target_lords: list[str]
    related_lords: list[str]
    date_start: date
    date_end: date
    max_level: int
    prana_grain: bool
    systems_queried: list[str]
    windows: list[EligibleWindow]
    # KP sub-level info (from vimshottari rows where kp_sublevel IS NOT NULL)
    kp_windows: list[EligibleWindow] = field(default_factory=list)
    total_windows: int = 0
    high_agreement_count: int = 0   # windows where cross_dasha_agreement.count >= 2


class KaDashaKalaService:
    """
    Dasa-Eligibility service for L3 Kala.

    Parameters
    ----------
    db_conn : psycopg connection (caller-owned)
        Used read-only.  Never committed or rolled back by this service.
    """

    def __init__(self, db_conn: Any):
        self._conn = db_conn

    def query(
        self,
        chart_id: str,
        ayanamsha_id: str,
        target_lords: Set[str],
        related_lords: Set[str],
        date_start: date,
        date_end: date,
        max_level: int = 4,
        min_band: EligibilityBand = EligibilityBand.RELATED,
        prana_grain: bool = False,
        systems: Optional[Set[str]] = None,
        _query_counter: Optional[list] = None,
    ) -> KaDashaKalaResult:
        """
        Run the dasa-eligibility query.

        Parameters
        ----------
        chart_id : str
            UUID of the chart.
        ayanamsha_id : str
            Which ayanamsha to query (e.g. 'lahiri').
        target_lords : set[str]
            Lords that exactly define the target signature.
        related_lords : set[str]
            Lords related to the signature (dispositors, house-lords).
        date_start, date_end : date
            Query window.
        max_level : int
            Maximum dasa depth to serve (1-4).  Default 4 = Sookshma.
        min_band : EligibilityBand
            Minimum band to pass the prune gate at level-1.
            Default RELATED (NEUTRAL MDs are pruned).
        prana_grain : bool
            If True, sub-divide level-4 intervals in-memory to level-5.
            These intervals are returned but NEVER written to DB.
        systems : set[str] | None
            If provided, restrict to these system_ids.  Default: all 7.
        _query_counter : list | None
            Internal testing hook -- see tree_walk.walk_eligible_intervals.

        Returns
        -------
        KaDashaKalaResult
        """
        if max_level < 1 or max_level > 4:
            raise ValueError(f"max_level must be 1-4 (got {max_level})")

        if date_start >= date_end:
            raise ValueError(
                "date_start must be before date_end "
                f"(got {date_start.isoformat()} >= {date_end.isoformat()})"
            )

        if systems is None:
            active_systems = sorted(ALL_DASHA_SYSTEMS)
        else:
            if not systems:
                raise ValueError("systems must not be empty when explicitly provided")
            unknown_systems = sorted(systems - ALL_DASHA_SYSTEMS)
            if unknown_systems:
                raise ValueError(
                    "unknown dasha systems: " + ", ".join(unknown_systems)
                )
            active_systems = sorted(systems)

        # -- Walk each system independently ----------------------------------
        all_intervals: list[DashaInterval] = []
        for sys_id in active_systems:
            try:
                intervals = walk_eligible_intervals(
                    conn=self._conn,
                    chart_id=chart_id,
                    ayanamsha_id=ayanamsha_id,
                    system_id=sys_id,
                    target_lords=target_lords,
                    related_lords=related_lords,
                    date_start=date_start,
                    date_end=date_end,
                    max_level=max_level,
                    min_band=min_band,
                    prana_grain=prana_grain,
                    query_counter=_query_counter,
                )
                all_intervals.extend(intervals)
                logger.info(
                    "[ka_dasha_kala] system=%s found %d eligible intervals",
                    sys_id, len(intervals),
                )
            except Exception as exc:
                # A result that lists a failed system in ``systems_queried`` is
                # indistinguishable from complete evidence to callers.  The L3
                # field contract requires exceptions to fail the call, so never
                # downgrade a system read failure to an apparently valid partial
                # result.
                raise RuntimeError(
                    f"ka_dasha_kala system {sys_id} failed: {exc}"
                ) from exc

        # -- Cross-dasa agreement (R-2) --------------------------------------
        # Atomic simultaneous intersection over ALL intervals (every level,
        # every system). A window's agreement = the number of DISTINCT systems
        # directly co-supporting at least one atomic segment of its span —
        # never the exact-(start,end)-pair key (F-13) and never transitive
        # merging of chained overlappers. Boundary convention: [start, end)
        # (S-H), declared in intersection.py.
        segments = intersect_segments(all_intervals)

        # -- Build result windows --------------------------------------------
        windows: list[EligibleWindow] = []
        kp_windows: list[EligibleWindow] = []

        for iv in all_intervals:
            summary = agreement_for(iv.start_date, iv.end_date, segments)
            agreement = CrossDashaAgreement(
                count=summary.count,
                systems_agreeing=list(summary.systems_agreeing),
            )

            is_prana = (iv.level_n == 5)
            ew = EligibleWindow(
                dasha_row_id=iv.dasha_row_id,
                chart_id=iv.chart_id,
                ayanamsha_id=iv.ayanamsha_id,
                system_id=iv.system_id,
                level_n=iv.level_n,
                lord_graha=iv.lord_graha,
                start_date=iv.start_date,
                end_date=iv.end_date,
                ancestor_lords=iv.ancestor_lords,
                eligibility_band=iv.eligibility_band,
                eligibility_score=iv.eligibility_score,
                cross_dasha_agreement=agreement,
                kp_sublevel=iv.kp_sublevel,
                kp_sub_lord=iv.kp_sub_lord,
                is_prana_computed=is_prana,
            )
            windows.append(ew)

            # KP sub-level windows (vimshottari rows with kp_sublevel set)
            if iv.system_id == "vimshottari" and iv.kp_sublevel:
                kp_windows.append(ew)

        high_agreement = sum(1 for w in windows if w.cross_dasha_agreement.count >= 2)

        return KaDashaKalaResult(
            chart_id=chart_id,
            ayanamsha_id=ayanamsha_id,
            target_lords=sorted(target_lords),
            related_lords=sorted(related_lords),
            date_start=date_start,
            date_end=date_end,
            max_level=max_level,
            prana_grain=prana_grain,
            systems_queried=active_systems,
            windows=windows,
            kp_windows=kp_windows,
            total_windows=len(windows),
            high_agreement_count=high_agreement,
        )

    def confirm_systems_present(
        self,
        chart_id: str,
        ayanamsha_id: str = "lahiri_chitrapaksha",
    ) -> dict[str, int]:
        """
        Return a dict of {system_id: row_count} for the given chart+ayanamsha.
        Used by health-check and self-test.
        """
        sql = """
            SELECT system_id, COUNT(*) AS cnt
            FROM chart_dashas
            WHERE chart_id = %s AND ayanamsha_id = %s
            GROUP BY system_id
            ORDER BY system_id
        """
        rows = self._conn.execute(sql, [chart_id, ayanamsha_id]).fetchall()
        if not rows:
            return {}
        if isinstance(rows[0], dict):
            return {r["system_id"]: int(r["cnt"]) for r in rows}
        return {r[0]: int(r[1]) for r in rows}
