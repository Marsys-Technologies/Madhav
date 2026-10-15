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

from brahmagyan.verification_vocab import TWO_PASS_VERIFIED

logger = logging.getLogger(__name__)

DASHA_SYSTEMS = (
    "vimshottari", "vimshottari_kp", "yogini", "ashtottari",
    "chara_karaka", "naisargika", "mudda", "kalachakra", "narayana",
)


def fetch_dasha_periods(
    conn, chart_id: str, ayanamsha_id: str = "lahiri_chitrapaksha",
    systems: Optional[list[str]] = None, level_n: int = 1,
) -> list[dict]:
    """Legacy MD interface over the governed read, retaining row provenance."""
    return fetch_dasha_periods_multilevel(
        conn, chart_id, ayanamsha_id=ayanamsha_id, systems=systems,
        levels=(level_n,), level_tier_policy=True)


# GOCHARA_DESIGN_SPECS_v1_4 §4.0 (the daśā read contract): rows are selected
# at verification tier `two_pass_verified`; every MD/AD/PD row is the
# half-open interval [start_iso, end_iso); AD is valid only under its MD and
# PD only under its AD (linkage by parent row id, never timestamp overlap).
DEFAULT_LEVELS = (1, 2, 3)  # MD / AD / PD
READ_CONTRACT_TIER = TWO_PASS_VERIFIED


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


def canonicalize_multilevel_rows(rows: list[dict]) -> list[dict]:
    """The §4.0 duplicate rules as ONE pure pass over already-PINNED rows
    (GOCHARA_DESIGN_SPECS_v1_4 §4.0; ASTRA_REVIEW_A5_4 v1.1 P1-2). Used by
    the DB fetch below and by the projection's per-instant selection, so
    the two never drift:

      1. identical-duplicate collapse — rows equal on every contract field
         (system, level, parent, lord, start, end, build, tier) collapse to
         one; the keeper records every source id in `merged_row_ids`;
      2. parent-alias canonicalization — a child whose parent_row_id names
         a COLLAPSED duplicate is re-pointed to the keeper (no orphaning of
         valid children);
      3. sibling `index` — under each (system, level, parent) the surviving
         rows are ordered by start_iso and numbered 0..n-1 (the contract's
         `(level, parent, index)` identity; chart_dashas carries no index
         column, its natural key being (…, level_n, parent_row_id,
         lord_graha, start_date) per migration 653);
      4. `(level, parent, index)` conflict — two surviving siblings whose
         half-open intervals overlap compete for one identity/instant:
         reject both, fail loudly (DashaReadConflict), never row-order pick.
    The pinning (build / ayanāṃśa / tier) MUST happen before this pass —
    the caller's job; this function does not know the pins.
    """
    # 1./2. identical collapse and parent canonicalization, RECURSIVELY by
    # level (ASTRA v1.2 P1-1): a duplicated MD/AD/PD tree collapses at the
    # MD level first; its AD children are re-pointed to the keeper and only
    # THEN collapsed (their identity key now shares the canonical parent),
    # and so on down — descendants are normalised after their parents and
    # collapsed after normalisation, never rejected as overlapping siblings.
    alias: dict[str, str] = {}
    survivors: list[dict] = []
    levels = sorted({int(r.get("level_n") or 0) for r in rows})
    for level in levels:
        keepers: dict[tuple, dict] = {}
        for row in rows:
            if int(row.get("level_n") or 0) != level:
                continue
            row = dict(row)
            parent = row.get("parent_row_id")
            if parent is not None and str(parent) in alias:
                row["parent_row_id_original"] = str(parent)
                row["parent_row_id"] = alias[str(parent)]
            key = tuple(str(row.get(k)) for k in (
                "system_id", "level_n", "parent_row_id", "lord_graha", "start_iso",
                "end_iso", "build_id", "verification_pass_status"))
            rid = str(row.get("dasha_row_id"))
            if key not in keepers:
                row["merged_row_ids"] = sorted(set(map(str, row.get("merged_row_ids") or [])) | {rid})
                keepers[key] = row
                continue
            keeper = keepers[key]
            keeper["merged_row_ids"] = sorted(set(keeper["merged_row_ids"]) | {rid})
            alias[rid] = str(keeper.get("dasha_row_id"))
        survivors.extend(keepers.values())
    # 3./4. sibling index + overlap conflict
    groups: dict[tuple, list[dict]] = {}
    for row in survivors:
        groups.setdefault((str(row.get("system_id")), int(row.get("level_n") or 0),
                           None if row.get("parent_row_id") is None else str(row.get("parent_row_id"))),
                          []).append(row)
    for (system, level, parent), sib in groups.items():
        sib.sort(key=lambda r: (str(r.get("start_iso")), str(r.get("end_iso"))))
        for idx, row in enumerate(sib):
            row["index"] = idx
        for a, b in zip(sib, sib[1:]):
            if str(b.get("start_iso")) < str(a.get("end_iso")):
                raise DashaReadConflict(
                    f"chart_dashas §4.0 (level, parent, index) conflict: {system} "
                    f"level {level} under parent {parent} — rows "
                    f"{a.get('dasha_row_id')} [{a.get('start_iso')}, {a.get('end_iso')}) and "
                    f"{b.get('dasha_row_id')} [{b.get('start_iso')}, {b.get('end_iso')}) "
                    "overlap — both rejected, never silently picked")
    return survivors


def fetch_dasha_periods_multilevel(
    conn, chart_id: str, ayanamsha_id: str = "lahiri_chitrapaksha",
    systems: Optional[list[str]] = None, levels: tuple[int, ...] = DEFAULT_LEVELS,
    tier: str = READ_CONTRACT_TIER, build_id: Optional[str] = None,
    canonicalize: bool = True, level_tier_policy: bool = False,
) -> list[dict]:
    """Public reads always bind settlement before selecting operands.

    No connection is an unavailable read. A conflicting or ungoverned live
    population raises a typed refusal; it is never translated into a vote.
    """
    if conn is None:
        return []
    from services.gochara_kernel.dasha_read import load_governed_dasha_periods
    return load_governed_dasha_periods(
        conn, chart_id, ayanamsha_id=ayanamsha_id, systems=systems,
        levels=levels, tier=tier, build_id=build_id,
        canonicalize=canonicalize, level_tier_policy=level_tier_policy)


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
           "canonicalize_multilevel_rows",
           "build_fixture_dasha_periods", "period_contains", "DashaReadConflict",
           "DEFAULT_LEVELS", "READ_CONTRACT_TIER"]
