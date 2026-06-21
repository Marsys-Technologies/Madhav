"""
tree_walk.py — Lazy pruning tree-walk over chart_dashas.

Algorithm
---------
The walk operates top-down:

  1. Fetch all level-1 (Maha-dasa) rows for the requested (chart_id,
     ayanamsha_id, system_id) that overlap the query window.
  2. For each MD, evaluate the lord's eligibility.
       - If NOT eligible (band < min_band) --> PRUNE: do not query its children.
       - If eligible --> descend to level-2 (AD), score, prune again.
  3. Continue to level-3 (PD) and level-4 (Sookshma) with the same rule.
  4. Return a flat list of DashaInterval records for every SURVIVING leaf at
     the requested max_level (or at the deepest available level if shallower).

The key guarantee: children of an ineligible parent are NEVER queried.
Tests verify this via a call-counter on the DB query function.

Level-5 (Prana) policy
-----------------------
chart_dashas enforces a CHECK constraint `level_n <= 4`.  The service
NEVER writes level-5 rows.  When ``prana_grain=True`` is requested, the
service computes level-5 intervals IN-MEMORY via proportional subdivision
of each Sookshma (level-4) interval.  These computed rows are ephemeral
(returned in the response only) and are NEVER persisted.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Callable, List, Optional, Set

from .eligibility import EligibilityBand, score_eligibility, is_eligible_for_pruning

logger = logging.getLogger(__name__)

# Canonical 7 systems in chart_dashas for this project
ALL_DASHA_SYSTEMS = frozenset({
    "vimshottari", "yogini", "ashtottari", "chara_karaka",
    "naisargika", "mudda", "kalachakra",
})


@dataclass
class DashaInterval:
    """One scored dasha interval (a surviving leaf in the pruned tree-walk)."""
    dasha_row_id: str
    chart_id: str
    ayanamsha_id: str
    system_id: str
    level_n: int
    lord_graha: str
    start_date: date
    end_date: date
    parent_row_id: Optional[str]
    # Ancestry lords (level-1 through level-(n-1)), outermost first
    ancestor_lords: List[str] = field(default_factory=list)
    eligibility_band: EligibilityBand = EligibilityBand.NEUTRAL
    eligibility_score: float = 0.20
    kp_sublevel: Optional[str] = None
    kp_sub_lord: Optional[str] = None


def _fetch_level1(
    conn: Any,
    chart_id: str,
    ayanamsha_id: str,
    system_id: str,
    date_start: date,
    date_end: date,
    query_counter: Optional[list] = None,
) -> list[dict]:
    """Fetch all level-1 (MD) rows that overlap [date_start, date_end]."""
    if query_counter is not None:
        query_counter.append(f"level1:{system_id}")

    sql = """
        SELECT dasha_row_id, lord_graha, start_date, end_date,
               kp_sublevel, kp_sub_lord
        FROM chart_dashas
        WHERE chart_id       = %s
          AND ayanamsha_id   = %s
          AND system_id      = %s
          AND level_n        = 1
          AND start_date     < %s
          AND end_date       > %s
        ORDER BY start_date
    """
    rows = conn.execute(sql, [chart_id, ayanamsha_id, system_id,
                               date_end, date_start]).fetchall()
    cols = ["dasha_row_id", "lord_graha", "start_date", "end_date",
            "kp_sublevel", "kp_sub_lord"]
    return [dict(zip(cols, r)) if not isinstance(r, dict) else r for r in rows]


def _fetch_children(
    conn: Any,
    parent_row_id: str,
    date_start: date,
    date_end: date,
    query_counter: Optional[list] = None,
    system_id: str = "",
) -> list[dict]:
    """Fetch direct children of a given parent row that overlap [date_start, date_end]."""
    if query_counter is not None:
        query_counter.append(f"children:{system_id}:{parent_row_id}")

    sql = """
        SELECT dasha_row_id, lord_graha, start_date, end_date, level_n,
               parent_row_id, kp_sublevel, kp_sub_lord
        FROM chart_dashas
        WHERE parent_row_id = %s
          AND start_date    < %s
          AND end_date      > %s
        ORDER BY start_date
    """
    rows = conn.execute(sql, [parent_row_id, date_end, date_start]).fetchall()
    cols = ["dasha_row_id", "lord_graha", "start_date", "end_date", "level_n",
            "parent_row_id", "kp_sublevel", "kp_sub_lord"]
    return [dict(zip(cols, r)) if not isinstance(r, dict) else r for r in rows]


def _subdivide_prana(interval: DashaInterval, n_subdivisions: int = 9) -> list[DashaInterval]:
    """
    In-memory proportional subdivision of a Sookshma (level-4) interval into
    level-5 (Prana) sub-intervals.

    Uses equal-duration subdivision as a proportional proxy.  This is an
    approximation — classical Prana computation uses system-specific ratios,
    but since level-5 is NOT stored and only needed for narrow-window queries,
    equal subdivision is acceptable for service-layer use.

    NEVER writes to DB.  Returns in-memory DashaInterval objects with level_n=5.
    """
    total_days = (interval.end_date - interval.start_date).days
    if total_days <= 0:
        return []

    sub_days = total_days / n_subdivisions
    result = []
    for i in range(n_subdivisions):
        from datetime import timedelta
        frac_start = interval.start_date + timedelta(days=round(i * sub_days))
        frac_end = interval.start_date + timedelta(days=round((i + 1) * sub_days))
        if frac_start >= interval.end_date:
            break
        frac_end = min(frac_end, interval.end_date)

        result.append(DashaInterval(
            dasha_row_id=f"{interval.dasha_row_id}:prana:{i}",
            chart_id=interval.chart_id,
            ayanamsha_id=interval.ayanamsha_id,
            system_id=interval.system_id,
            level_n=5,
            lord_graha=interval.lord_graha,  # same lord (proportional)
            start_date=frac_start,
            end_date=frac_end,
            parent_row_id=interval.dasha_row_id,
            ancestor_lords=interval.ancestor_lords + [interval.lord_graha],
            eligibility_band=interval.eligibility_band,
            eligibility_score=interval.eligibility_score,
        ))
    return result


def walk_eligible_intervals(
    conn: Any,
    chart_id: str,
    ayanamsha_id: str,
    system_id: str,
    target_lords: Set[str],
    related_lords: Set[str],
    date_start: date,
    date_end: date,
    max_level: int = 4,
    min_band: EligibilityBand = EligibilityBand.RELATED,
    prana_grain: bool = False,
    query_counter: Optional[list] = None,
) -> list[DashaInterval]:
    """
    Lazy pruning tree-walk for one (system_id, ayanamsha_id) pair.

    Parameters
    ----------
    conn : psycopg connection (caller-owned; never committed here)
    chart_id : str
    ayanamsha_id : str
    system_id : str
        One of the 7 canonical systems.
    target_lords : set[str]
        Lords that define the target signature (exact-match).
    related_lords : set[str]
        Related lords (dispositors, house-lords).
    date_start, date_end : date
        Query window (inclusive on start, exclusive on end per convention).
    max_level : int
        Maximum depth to descend (1-4).  4 = Sookshma (default).
    min_band : EligibilityBand
        Minimum eligibility band to keep a node (prune below this).
        Default = RELATED (prune NEUTRAL MDs).
    prana_grain : bool
        If True, subdivide Sookshma intervals in-memory into level-5
        (Prana).  These are NEVER written to DB.
    query_counter : list | None
        If provided, each DB query appends a label to this list.
        Used by tests to assert pruning (ineligible subtrees' children
        should NOT appear in this list).

    Returns
    -------
    Flat list of DashaInterval records (surviving leaves).
    """
    results: list[DashaInterval] = []

    # -- Level-1: Maha-dasa ------------------------------------------------
    md_rows = _fetch_level1(
        conn, chart_id, ayanamsha_id, system_id,
        date_start, date_end, query_counter,
    )

    for md in md_rows:
        md_lord = md["lord_graha"]
        md_band, md_score = score_eligibility(md_lord, target_lords, related_lords)
        md_eligible = is_eligible_for_pruning(md_lord, target_lords, related_lords, min_band)

        if not md_eligible:
            # PRUNE: do not query children of this MD
            logger.debug("[tree_walk] PRUNE MD %s (%s) system=%s",
                         md_lord, md_band, system_id)
            continue

        if max_level == 1:
            # Serve at MD level
            interval = DashaInterval(
                dasha_row_id=str(md["dasha_row_id"]),
                chart_id=chart_id,
                ayanamsha_id=ayanamsha_id,
                system_id=system_id,
                level_n=1,
                lord_graha=md_lord,
                start_date=md["start_date"],
                end_date=md["end_date"],
                parent_row_id=None,
                ancestor_lords=[],
                eligibility_band=md_band,
                eligibility_score=md_score,
                kp_sublevel=md.get("kp_sublevel"),
                kp_sub_lord=md.get("kp_sub_lord"),
            )
            results.append(interval)
            continue

        # -- Level-2: Antar-dasa -------------------------------------------
        ad_rows = _fetch_children(
            conn, str(md["dasha_row_id"]), date_start, date_end,
            query_counter, system_id,
        )

        for ad in ad_rows:
            ad_lord = ad["lord_graha"]
            ad_band, ad_score = score_eligibility(ad_lord, target_lords, related_lords)
            ad_eligible = is_eligible_for_pruning(ad_lord, target_lords, related_lords, min_band)

            if not ad_eligible:
                logger.debug("[tree_walk] PRUNE AD %s/%s system=%s",
                             md_lord, ad_lord, system_id)
                continue

            if max_level == 2:
                interval = DashaInterval(
                    dasha_row_id=str(ad["dasha_row_id"]),
                    chart_id=chart_id,
                    ayanamsha_id=ayanamsha_id,
                    system_id=system_id,
                    level_n=2,
                    lord_graha=ad_lord,
                    start_date=ad["start_date"],
                    end_date=ad["end_date"],
                    parent_row_id=str(md["dasha_row_id"]),
                    ancestor_lords=[md_lord],
                    eligibility_band=ad_band,
                    eligibility_score=ad_score,
                    kp_sublevel=ad.get("kp_sublevel"),
                    kp_sub_lord=ad.get("kp_sub_lord"),
                )
                results.append(interval)
                continue

            # -- Level-3: Pratyantar-dasa ------------------------------------
            pd_rows = _fetch_children(
                conn, str(ad["dasha_row_id"]), date_start, date_end,
                query_counter, system_id,
            )

            for pd in pd_rows:
                pd_lord = pd["lord_graha"]
                pd_band, pd_score = score_eligibility(pd_lord, target_lords, related_lords)
                pd_eligible = is_eligible_for_pruning(pd_lord, target_lords, related_lords, min_band)

                if not pd_eligible:
                    logger.debug("[tree_walk] PRUNE PD %s/%s/%s system=%s",
                                 md_lord, ad_lord, pd_lord, system_id)
                    continue

                if max_level == 3:
                    interval = DashaInterval(
                        dasha_row_id=str(pd["dasha_row_id"]),
                        chart_id=chart_id,
                        ayanamsha_id=ayanamsha_id,
                        system_id=system_id,
                        level_n=3,
                        lord_graha=pd_lord,
                        start_date=pd["start_date"],
                        end_date=pd["end_date"],
                        parent_row_id=str(ad["dasha_row_id"]),
                        ancestor_lords=[md_lord, ad_lord],
                        eligibility_band=pd_band,
                        eligibility_score=pd_score,
                        kp_sublevel=pd.get("kp_sublevel"),
                        kp_sub_lord=pd.get("kp_sub_lord"),
                    )
                    results.append(interval)
                    continue

                # -- Level-4: Sookshma (default floor) -----------------------
                sk_rows = _fetch_children(
                    conn, str(pd["dasha_row_id"]), date_start, date_end,
                    query_counter, system_id,
                )

                for sk in sk_rows:
                    sk_lord = sk["lord_graha"]
                    sk_band, sk_score = score_eligibility(sk_lord, target_lords, related_lords)

                    interval = DashaInterval(
                        dasha_row_id=str(sk["dasha_row_id"]),
                        chart_id=chart_id,
                        ayanamsha_id=ayanamsha_id,
                        system_id=system_id,
                        level_n=4,
                        lord_graha=sk_lord,
                        start_date=sk["start_date"],
                        end_date=sk["end_date"],
                        parent_row_id=str(pd["dasha_row_id"]),
                        ancestor_lords=[md_lord, ad_lord, pd_lord],
                        eligibility_band=sk_band,
                        eligibility_score=sk_score,
                        kp_sublevel=sk.get("kp_sublevel"),
                        kp_sub_lord=sk.get("kp_sub_lord"),
                    )

                    if prana_grain:
                        # In-memory level-5 subdivision -- NEVER written to DB
                        prana_intervals = _subdivide_prana(interval)
                        results.extend(prana_intervals)
                    else:
                        results.append(interval)

    return results
