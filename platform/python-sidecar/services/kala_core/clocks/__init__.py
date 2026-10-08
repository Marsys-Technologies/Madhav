"""F2 clock readers over a single, pinned L1 ``chart_dashas`` build.

This module deliberately interprets periods authored by L1; it never derives a
daśā schedule and it never substitutes the wall clock for ``as_of``.  Consumers
must supply the build, ayanāṃśa, and tier they intend to read so rows from a
different L1 convention cannot be silently mixed into a context.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Literal


_LEVEL_NAMES = {1: "MD", 2: "AD", 3: "PD", 4: "SD"}
_SANDHI_FRACTION = 0.03


class ClockUnavailable(RuntimeError):
    """A pinned L1 read cannot safely produce the requested clock context."""


@dataclass(frozen=True)
class Boundary:
    """A boundary copied from its pinned L1 row, with no constructed instant."""

    instant: datetime
    level: Literal["MD", "AD", "PD", "SD"]
    lord: str
    source_row_id: str
    sigma: timedelta
    scenario_id: str | None
    boundary_truncated: bool


@dataclass(frozen=True)
class PeriodContext:
    """The hierarchy active at one explicit instant in a pinned L1 build."""

    as_of: datetime
    lords: dict[str, str]
    period_ids: dict[str, str]
    applicability: Literal["applicable", "method_inapplicable", "unknown"]
    sigma_boundary: timedelta
    scenario_id: str | None
    sandhi: bool
    sandhi_window: timedelta
    boundary_truncated: bool


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("as_of and chart_dashas instants must be timezone-aware")
    return value


def _read_rows(
    conn: Any,
    chart_id: str,
    system: str,
    *,
    build_id: str,
    ayanamsha_id: str,
    tier: str,
) -> list[dict[str, Any]]:
    """Read exactly one declared L1 build and convention.

    ``chart_dashas`` is intentionally the only source.  In particular, callers
    cannot get a context through an unpinned ``LIMIT 1`` read.
    """
    rows = conn.execute(
        """
        SELECT dasha_row_id, level_n, lord_graha, lord_sign, parent_row_id,
               start_iso, end_iso, build_id, ayanamsha_id, system_id,
               verification_pass_status, applies_to_this_chart_flag,
               is_truncated_at_window_start, is_truncated_at_window_end
        FROM chart_dashas
        WHERE chart_id = %s AND system_id = %s AND build_id = %s
          AND ayanamsha_id = %s AND verification_pass_status = %s
          AND level_n BETWEEN 1 AND 4
        ORDER BY level_n ASC, start_iso ASC, dasha_row_id ASC
        """,
        [chart_id, system, build_id, ayanamsha_id, tier],
    ).fetchall()
    result: list[dict[str, Any]] = []
    for row in rows:
        normalized = dict(row)
        start, end = normalized.get("start_iso"), normalized.get("end_iso")
        if isinstance(start, str):
            start = datetime.fromisoformat(start)
        if isinstance(end, str):
            end = datetime.fromisoformat(end)
        if not isinstance(start, datetime) or not isinstance(end, datetime):
            raise RuntimeError("pinned chart_dashas row has no datetime boundary")
        normalized["start_iso"] = _as_utc(start)
        normalized["end_iso"] = _as_utc(end)
        if normalized["end_iso"] <= normalized["start_iso"]:
            raise RuntimeError("pinned chart_dashas row has a non-positive period")
        result.append(normalized)
    return result


def _lord(row: dict[str, Any]) -> str:
    lord = row.get("lord_graha") or row.get("lord_sign")
    if not lord:
        raise RuntimeError(f"pinned chart_dashas row {row.get('dasha_row_id')!r} has no lord")
    return str(lord)


def _sigma(row: dict[str, Any]) -> timedelta:
    """No uncertainty column exists on the agreed L1 read surface yet."""
    return timedelta(0)


def boundaries(
    conn: Any,
    chart_id: str,
    system: str,
    *,
    build_id: str,
    ayanamsha_id: str,
    tier: str,
    level: Literal["MD", "AD", "PD", "SD"] | None = None,
) -> list[Boundary]:
    """Return L1 boundary instants verbatim for a pinned chart/system build.

    ``level`` is a projection, not another query: the pinned build is read in
    full first, so it cannot accidentally return a boundary from a different
    convention or tier.
    """
    return [
        Boundary(
            instant=row["start_iso"],
            level=_LEVEL_NAMES[int(row["level_n"])],
            lord=_lord(row),
            source_row_id=str(row["dasha_row_id"]),
            sigma=_sigma(row),
            scenario_id=row.get("scenario_id"),
            boundary_truncated=bool(row.get("is_truncated_at_window_start")),
        )
        for row in _read_rows(
            conn, chart_id, system, build_id=build_id,
            ayanamsha_id=ayanamsha_id, tier=tier,
        )
        if level is None or _LEVEL_NAMES[int(row["level_n"])] == level
    ]


def _active_hierarchy(rows: list[dict[str, Any]], as_of: datetime) -> list[dict[str, Any]]:
    """Choose one active MD→SD lineage and reject an unlinked active child.

    Interval overlap alone is insufficient: independently active periods must
    not be assembled into a hierarchy.  L1's parent ids are the authoritative
    lineage, including for systems that do not produce every depth.
    """
    active_by_level: dict[int, list[dict[str, Any]]] = {}
    for row in rows:
        if row["start_iso"] <= as_of < row["end_iso"]:
            active_by_level.setdefault(int(row["level_n"]), []).append(row)

    roots = active_by_level.get(1, [])
    if len(roots) != 1:
        raise LookupError(f"expected exactly one active MD at {as_of.isoformat()}")
    lineage = [roots[0]]
    for level in range(2, 5):
        candidates = [
            row for row in active_by_level.get(level, [])
            if str(row.get("parent_row_id")) == str(lineage[-1]["dasha_row_id"])
        ]
        if not candidates:
            if any(active_by_level.get(deeper_level) for deeper_level in range(level + 1, 5)):
                raise ClockUnavailable("hierarchy_unavailable")
            continue
        if len(candidates) != 1:
            raise RuntimeError(
                f"pinned chart_dashas build has multiple active {_LEVEL_NAMES[level]} children"
            )
        lineage.append(candidates[0])
    return lineage


def period_context(
    conn: Any,
    chart_id: str,
    as_of: datetime,
    system: str,
    *,
    build_id: str,
    ayanamsha_id: str,
    tier: str,
) -> PeriodContext:
    """Read the MD–SD hierarchy active at the supplied, explicit ``as_of``."""
    as_of = _as_utc(as_of)
    rows = _read_rows(
        conn, chart_id, system, build_id=build_id,
        ayanamsha_id=ayanamsha_id, tier=tier,
    )
    active = _active_hierarchy(rows, as_of)
    lords = {_LEVEL_NAMES[int(row["level_n"])]: _lord(row) for row in active}

    own_spans = [row["end_iso"] - row["start_iso"] for row in active]
    own_span = min(own_spans)
    sandhi_window = own_span * _SANDHI_FRACTION
    nearest_distance = min(
        min(abs(as_of - row["start_iso"]), abs(row["end_iso"] - as_of))
        for row in active
    )
    applicability: Literal["applicable", "method_inapplicable", "unknown"]
    flags = {row.get("applies_to_this_chart_flag") for row in active}
    if False in flags:
        applicability = "method_inapplicable"
    elif flags == {True} and system != "ashtottari":
        applicability = "applicable"
    else:
        applicability = "unknown"
    return PeriodContext(
        as_of=as_of,
        lords=lords,
        period_ids={
            _LEVEL_NAMES[int(row["level_n"])]: str(row["dasha_row_id"])
            for row in active
        },
        applicability=applicability,
        sigma_boundary=max((_sigma(row) for row in active), default=timedelta(0)),
        scenario_id=None,
        sandhi=nearest_distance <= sandhi_window,
        sandhi_window=sandhi_window,
        boundary_truncated=any(
            row.get("is_truncated_at_window_start") or row.get("is_truncated_at_window_end")
            for row in active
        ),
    )


__all__ = ["Boundary", "ClockUnavailable", "PeriodContext", "boundaries", "period_context"]
