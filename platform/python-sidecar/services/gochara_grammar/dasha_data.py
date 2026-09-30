"""
gochara_grammar.dasha_data — defensive read-side access to `chart_dashas` for
the dasha-coincidence composition operator (#6).

9 dasha systems exist LIVE in `chart_dashas.system_id` (confirmed by direct
query against the canonical chart 482012f1-710e-4a25-994a-93821f5871aa and
cross-checked against the full table): vimshottari, vimshottari_kp, yogini,
ashtottari, chara_karaka, naisargika, mudda, kalachakra, narayana.

NOTE: `pipeline/orchestrator/writers/ka_avadhi.py`'s `_DASHA_SYSTEMS` (7
entries, using the stale id "chara" and missing "narayana"/"vimshottari_kp")
is now OUT OF SYNC with live data -- that file is a separate lane's writer
and is out of scope for this fix; flagged here so it isn't mistaken for the
source of truth. `dasha_coincidence` composes across MULTIPLE of these
(DR-14 plurality) -- NOT Vimśottarī-gated, per BRIEF_D5 §1 G-2 row and §10
promise-ledger row for G-2's composition operators.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

DASHA_SYSTEMS = (
    "vimshottari", "vimshottari_kp", "yogini", "ashtottari",
    "chara_karaka", "naisargika", "mudda", "kalachakra", "narayana",
)


def fetch_dasha_periods(
    conn,
    chart_id: str,
    ayanamsha_id: str = "lahiri_chitrapaksha",
    systems: Optional[list[str]] = None,
    level_n: int = 1,
) -> list[dict]:
    """Read `chart_dashas` rows for chart_id across `systems` (defaults to
    ALL 9 known systems -- the DR-14 plurality requirement). Returns [] on
    any DB-shape surprise (honest empty, not a crash), same discipline as
    `resonance_map.fetch_resonance_targets`. MD-only (level_n=1) by default;
    the multi-level MD/AD/PD read is `fetch_dasha_periods_multilevel`."""
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


# GOCHARA_DESIGN_SPECS_v1_4 §4.0 (the daśā read contract): rows are selected
# at verification tier `two_pass_verified`; every MD/AD/PD row is the
# half-open interval [start_iso, end_iso); AD is valid only under its MD and
# PD only under its AD (linkage by parent row id, never timestamp overlap).
DEFAULT_LEVELS = (1, 2, 3)  # MD / AD / PD
READ_CONTRACT_TIER = "two_pass_verified"


class DashaReadConflict(ValueError):
    """§4.0 duplicate-row rule: two equally-qualified rows conflict for the
    same (system, level, parent, start) — reject both and fail loudly, never
    silently pick one."""


_MULTILEVEL_KEYS = [
    "dasha_row_id", "system_id", "level_n", "parent_row_id", "lord_graha",
    "start_iso", "end_iso", "build_id", "verification_pass_status",
]

# §4.0 identity + contract fields: two rows with the same identity key are
# identical duplicates (collapse) iff every contract field matches; any
# difference is a conflict.
_MULTILEVEL_IDENTITY = ("system_id", "level_n", "parent_row_id", "start_iso")
_MULTILEVEL_CONTRACT_FIELDS = ("lord_graha", "end_iso", "build_id",
                               "verification_pass_status")


def fetch_dasha_periods_multilevel(
    conn,
    chart_id: str,
    ayanamsha_id: str = "lahiri_chitrapaksha",
    systems: Optional[list[str]] = None,
    levels: tuple[int, ...] = DEFAULT_LEVELS,
    tier: str = READ_CONTRACT_TIER,
) -> list[dict]:
    """§4.0 multi-level (MD/AD/PD) read of `chart_dashas`, with parent
    linkage preserved (`parent_row_id`) and the contract's duplicate rules
    enforced:

      * rows are selected at verification tier `two_pass_verified`;
      * identical duplicates (equal on every contract field) collapse to one
        — the surviving row records all source row ids in `merged_row_ids`;
      * conflicting duplicates (same identity, any contract field differs)
        raise DashaReadConflict — fail loudly, never silently pick one.

    Returns [] on a DB-shape surprise (honest empty, same discipline as
    `fetch_dasha_periods`); a CONFLICT is not a DB surprise — it raises.
    `fetch_dasha_periods` (MD-only) is unchanged for its existing callers.
    """
    if conn is None:
        return []
    want_systems = systems or list(DASHA_SYSTEMS)
    try:
        cur = conn.execute(
            """
            SELECT dasha_row_id, system_id, level_n, parent_row_id,
                   lord_graha, start_iso, end_iso, build_id,
                   verification_pass_status
              FROM chart_dashas
             WHERE chart_id = %s AND ayanamsha_id = %s
               AND system_id = ANY(%s) AND level_n = ANY(%s)
               AND verification_pass_status = %s
             ORDER BY system_id, level_n, start_iso
            """,
            [chart_id, ayanamsha_id, want_systems, list(levels), tier],
        )
        rows = cur.fetchall()
    except Exception as exc:  # noqa: BLE001
        logger.info("[dasha_data] multi-level chart_dashas read failed "
                    "(table unreachable or unpopulated): %s", exc)
        return []
    parsed = [row if isinstance(row, dict) else dict(zip(_MULTILEVEL_KEYS, row))
              for row in rows]
    collapsed: dict[tuple, dict] = {}
    for row in parsed:
        key = tuple(str(row[k]) for k in _MULTILEVEL_IDENTITY)
        if key not in collapsed:
            row["merged_row_ids"] = [str(row["dasha_row_id"])]
            collapsed[key] = row
            continue
        keeper = collapsed[key]
        if all(str(keeper[f]) == str(row[f]) for f in _MULTILEVEL_CONTRACT_FIELDS):
            keeper["merged_row_ids"].append(str(row["dasha_row_id"]))
            continue
        raise DashaReadConflict(
            f"chart_dashas §4.0 conflict for {key}: rows "
            f"{keeper['dasha_row_id']} and {row['dasha_row_id']} differ on "
            f"{[f for f in _MULTILEVEL_CONTRACT_FIELDS if str(keeper[f]) != str(row[f])]}"
            " — both rejected, never silently picked")
    return list(collapsed.values())


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


__all__ = ["DASHA_SYSTEMS", "fetch_dasha_periods", "fetch_dasha_periods_multilevel",
           "build_fixture_dasha_periods", "period_contains", "DashaReadConflict",
           "DEFAULT_LEVELS", "READ_CONTRACT_TIER"]
