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


# SR-W56-S3 (owner-surrogate ruling 2026-10-21): the settled build's Tājika mudda years overlap
# their successor by minutes (an L1 boundary defect, filed as F-L1-MUDDA-OVERLAP). L1 is not
# changed and no boundary is invented: inside such an overlap the mudda lord is UNRESOLVED and
# every dependent value reads blank with this reason. Any other overlap still raises.
MUDDA_OVERLAP_REASON = "l1_mudda_boundary_overlap"
MUDDA_OVERLAP_MAX_SECONDS = 86_400
MUDDA_SYSTEM = "mudda"
MUDDA_YEAR_LEVEL = 1          # one level-1 row = one varsha (ga_dashas_writer mudda "Varsha" rows)
MUDDA_OVERLAP_KEY = "l1_mudda_boundary_overlaps"


def _instant(value) -> datetime:
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value


def mudda_boundary_overlap_seconds(system: str, level: int, a: dict, b: dict) -> Optional[float]:
    """The overlap, in seconds, of two CONSECUTIVE rows `a` then `b` (sorted by start) iff it is a
    named L1 mudda boundary defect: same chart, mudda, level-1 (year) rows, `a` starting before and
    ending before `b` ends, and 0 < overlap <= 86,400 s. Otherwise None (the caller raises)."""
    if system != MUDDA_SYSTEM or level != MUDDA_YEAR_LEVEL:
        return None
    if a.get("chart_id") != b.get("chart_id"):
        return None
    try:
        a_start, a_end, b_start, b_end = (_instant(x.get(k)) for x, k in
                                          ((a, "start_iso"), (a, "end_iso"), (b, "start_iso"), (b, "end_iso")))
    except (ValueError, TypeError, AttributeError):
        return None
    if not (a_start < b_start < a_end < b_end):
        return None
    seconds = (a_end - b_start).total_seconds()
    return seconds if 0 < seconds <= MUDDA_OVERLAP_MAX_SECONDS else None


def _blank_mudda_overlaps(sib: list[dict], named: list[tuple[int, int]]) -> None:
    """Cut each named pair to its own side of the overlap, so NO row covers the overlap interval
    [b.start, a.end): the instant resolves to no mudda lord (never to a row-order pick). Both rows
    carry the interval and the reason; the stored bounds stay on the row for audit."""
    cuts = []
    for i, j in named:
        a, b = sib[i], sib[j]
        a_end, b_start = a["end_iso"], b["start_iso"]
        cuts.append((a, b, {"reason": MUDDA_OVERLAP_REASON, "start_iso": b_start, "end_iso": a_end,
                            "seconds": (_instant(a_end) - _instant(b_start)).total_seconds()}))
    for a, b, interval in cuts:       # classify on stored bounds first, cut afterwards (a middle row is cut twice)
        a.setdefault("end_iso_stored", a["end_iso"])
        b.setdefault("start_iso_stored", b["start_iso"])
        a["end_iso"], b["start_iso"] = interval["start_iso"], interval["end_iso"]
        for row in (a, b):
            row.setdefault(MUDDA_OVERLAP_KEY, []).append(dict(interval))


def unresolved_mudda_overlap_at(periods, dt_iso) -> Optional[dict]:
    """The named overlap interval ({reason, start_iso, end_iso, seconds}) containing `dt_iso`, or
    None. Half-open [start, end), like every other period."""
    for period in periods:
        for interval in period.get(MUDDA_OVERLAP_KEY) or ():
            if period_contains(interval, dt_iso):
                return interval
    return None


# SR-MUDDA-HORIZON: a dasha table is finite (mudda L1 ends 2032-02-05 on every ayanamsha). At an instant at or after the
# last end of every row a system holds, nothing was measured: "inactive" would assert a checked negative for an unmeasured
# span (§N.7.6), so the readers blank it with this reason instead. A system with NO rows keeps its own "no rows" reason.
HORIZON_EXHAUSTED_REASON = "dasha_horizon_exhausted"


def dasha_horizon_exhausted_at(periods, system_id: str, dt_iso: str) -> Optional[dict]:
    """`{reason, system_id, table_end_iso, levels}` when `system_id` HAS rows in the read but `dt_iso` is at or after the
    last end of all of them (half-open, like every period: t == end is past the table), else None. t before the table end
    is never named here -- a gap or a non-matching lord inside the table is a real, measured "not active". Rows whose end
    cannot be parsed are not evidence of a table end; a system with no parseable end (or no rows) is None."""
    ends, levels = [], set()
    for period in periods:
        if period.get("system_id") != system_id:
            continue
        try:
            ends.append(_instant(period["end_iso"]))
        except (ValueError, KeyError, TypeError, AttributeError):
            continue
        levels.add(int(period.get("level_n") or 1))
    if not ends:
        return None
    try:
        t = _instant(dt_iso)
    except (ValueError, TypeError, AttributeError):
        return None
    table_end = max(ends)
    if t < table_end:
        return None
    return {"reason": HORIZON_EXHAUSTED_REASON, "system_id": system_id,
            "table_end_iso": table_end.isoformat(), "levels": sorted(levels)}


def horizon_exhausted_entries(systems) -> list[dict]:
    """The permission `systems` entries that read `dasha_horizon_exhausted`, as `{system_id, table_end_iso}` -- the count the
    per-run K9 receipt carries. Counted from the entries the readers actually emitted, never re-derived."""
    return [{"system_id": s["system_id"], "table_end_iso": (s.get("detail") or {}).get("table_end_iso")}
            for s in systems if (s.get("detail") or {}).get("reason") == HORIZON_EXHAUSTED_REASON]


def mudda_overlap_census(periods) -> dict:
    """Count of DISTINCT named overlaps in a read (each is carried by both of its rows)."""
    seen = {(str(i["start_iso"]), str(i["end_iso"])): i["seconds"]
            for p in periods for i in (p.get(MUDDA_OVERLAP_KEY) or ())}
    return {"reason": MUDDA_OVERLAP_REASON, "overlaps_named": len(seen),
            "overlap_seconds_total": sum(seen.values())}


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
         ONE named exception (SR-W56-S3, `mudda_boundary_overlap_seconds`): consecutive
         Tājika year rows overlapping by 0 < s <= 86,400 s read as an UNRESOLVED
         interval (`l1_mudda_boundary_overlap`), not a conflict.
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
        named: list[tuple[int, int]] = []
        for i, (a, b) in enumerate(zip(sib, sib[1:])):
            if not str(b.get("start_iso")) < str(a.get("end_iso")):
                continue
            # SR-W56-S3: ONE narrow exception — a consecutive Tājika year pair of a chart whose
            # overlap is a named L1 boundary defect. Anything else is the conflict it always was.
            later = sib[i + 2:]      # a year overlapping a non-adjacent year (or leaving the middle one empty) is no boundary defect
            if (mudda_boundary_overlap_seconds(system, level, a, b) is None
                    or any(str(c.get("start_iso")) <= str(a.get("end_iso")) for c in later)):
                raise DashaReadConflict(
                    f"chart_dashas §4.0 (level, parent, index) conflict: {system} "
                    f"level {level} under parent {parent} — rows "
                    f"{a.get('dasha_row_id')} [{a.get('start_iso')}, {a.get('end_iso')}) and "
                    f"{b.get('dasha_row_id')} [{b.get('start_iso')}, {b.get('end_iso')}) "
                    "overlap — both rejected, never silently picked")
            named.append((i, i + 1))
        _blank_mudda_overlaps(sib, named)
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
           "canonicalize_multilevel_rows", "MUDDA_OVERLAP_REASON", "MUDDA_OVERLAP_MAX_SECONDS",
           "mudda_boundary_overlap_seconds", "unresolved_mudda_overlap_at", "mudda_overlap_census",
           "MUDDA_OVERLAP_KEY", "HORIZON_EXHAUSTED_REASON", "dasha_horizon_exhausted_at", "horizon_exhausted_entries",
           "build_fixture_dasha_periods", "period_contains", "DashaReadConflict",
           "DEFAULT_LEVELS", "READ_CONTRACT_TIER"]
