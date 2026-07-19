"""
gochara_grammar.dasha_data — defensive read-side access to `chart_dashas` for
the dasha-coincidence composition operator (#6).

7 dasha systems exist in `chart_dashas.system_id` per
`pipeline/orchestrator/writers/ka_avadhi.py`'s `_DASHA_SYSTEMS`: vimshottari,
yogini, ashtottari, chara, naisargika, mudda, kalachakra. `dasha_coincidence`
composes across MULTIPLE of these (DR-14 plurality) -- NOT Vimśottarī-gated,
per BRIEF_D5 §1 G-2 row and §10 promise-ledger row for G-2's composition
operators.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

DASHA_SYSTEMS = ("vimshottari", "yogini", "ashtottari", "chara", "naisargika", "mudda", "kalachakra")


def fetch_dasha_periods(
    conn,
    chart_id: str,
    ayanamsha_id: str = "lahiri_chitrapaksha",
    systems: Optional[list[str]] = None,
    level_n: int = 1,
) -> list[dict]:
    """Read `chart_dashas` rows for chart_id across `systems` (defaults to
    ALL 7 known systems -- the DR-14 plurality requirement). Returns [] on
    any DB-shape surprise (honest empty, not a crash), same discipline as
    `resonance_map.fetch_resonance_targets`."""
    if conn is None:
        return []
    want_systems = systems or list(DASHA_SYSTEMS)
    try:
        cur = conn.execute(
            """
            SELECT system_id, level_n, lord_graha, start_iso, end_iso
              FROM chart_dashas
             WHERE chart_id = %s AND ayanamsha_id = %s AND level_n = %s
               AND system_id = ANY(%s)
             ORDER BY system_id, start_iso
            """,
            [chart_id, ayanamsha_id, level_n, want_systems],
        )
        rows = cur.fetchall()
    except Exception as exc:  # noqa: BLE001
        logger.info("[dasha_data] chart_dashas read failed (table unreachable or unpopulated): %s", exc)
        return []
    keys = ["system_id", "level_n", "lord_graha", "start_iso", "end_iso"]
    return [row if isinstance(row, dict) else dict(zip(keys, row)) for row in rows]


def build_fixture_dasha_periods(chart_id: str) -> list[dict]:
    """Well-documented synthetic fixture spanning 2013-12-11 (the wave's
    named double-transit/marriage specimen date) across 2 independent
    timing systems, for tests to exercise dasha_coincidence without live DB
    access. NOT live chart_dashas data."""
    return [
        {"system_id": "vimshottari", "level_n": 1, "lord_graha": "Venus",
         "start_iso": "2012-06-01T00:00:00+00:00", "end_iso": "2015-06-01T00:00:00+00:00"},
        {"system_id": "yogini", "level_n": 1, "lord_graha": "Moon",
         "start_iso": "2013-01-01T00:00:00+00:00", "end_iso": "2014-01-01T00:00:00+00:00"},
    ]


def period_contains(period: dict, dt_iso: str) -> bool:
    """True if the dasha period [start_iso, end_iso) contains dt_iso."""
    try:
        dt = datetime.fromisoformat(dt_iso.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        start = datetime.fromisoformat(str(period["start_iso"]).replace("Z", "+00:00"))
        end = datetime.fromisoformat(str(period["end_iso"]).replace("Z", "+00:00"))
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        return start <= dt < end
    except (ValueError, KeyError, TypeError):
        return False


__all__ = ["DASHA_SYSTEMS", "fetch_dasha_periods", "build_fixture_dasha_periods", "period_contains"]
