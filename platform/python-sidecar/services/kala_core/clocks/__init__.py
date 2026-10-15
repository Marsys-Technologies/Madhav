"""F2 clock readers over a single, pinned L1 ``chart_dashas`` build.

This module deliberately interprets periods authored by L1; it never derives a
daśā schedule and it never substitutes the wall clock for ``as_of``.  Consumers
must supply the build, ayanāṃśa, and tier they intend to read so rows from a
different L1 convention cannot be silently mixed into a context.
"""
from __future__ import annotations

from services.gochara_kernel.dasha_read import (
    dasha_query, execute_governed_dasha_query)

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Literal

from brahmagyan.verification_vocab import RESTRICTED_TABLE_VOCAB, DIVERGENT_FLAGGED

from .methods import (
    Applicability, AshtottariFacts, ClockFact, DashaMethod, KalachakraFacts,
    assess_ashtottari, dasha_method, stored_system, validate_f2_row,
)
from .uncertainty import BoundaryUncertainty, boundary_shift, boundary_sigma


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
    sigma: timedelta | None
    scenario_id: str | None
    boundary_truncated: bool
    endpoint: Literal["start", "end"] = "start"
    method: DashaMethod | None = None
    build_id: str | None = None
    ayanamsha_id: str | None = None
    tier: str | None = None
    uncertainty_artifact: str | None = None


@dataclass(frozen=True)
class PeriodContext:
    """The hierarchy active at one explicit instant in a pinned L1 build."""

    as_of: datetime
    lords: dict[str, str]
    period_ids: dict[str, str]
    applicability: Literal["applicable", "method_inapplicable", "unknown"]
    sigma_boundary: timedelta | None
    scenario_id: str | None
    sandhi: bool
    sandhi_window: timedelta
    boundary_truncated: bool
    method: DashaMethod | None = None
    build_id: str | None = None
    ayanamsha_id: str | None = None
    tier: str | None = None
    applicability_detail: Applicability | None = None
    method_detail: KalachakraFacts | None = None
    uncertainty_artifact: str | None = None


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
    if not build_id:
        raise ClockUnavailable("build_not_pinned")
    if tier not in RESTRICTED_TABLE_VOCAB or tier == DIVERGENT_FLAGGED:
        raise ClockUnavailable("tier_unavailable")
    rows = execute_governed_dasha_query(
        conn, chart_id, dasha_query('clock_rows'),
        [chart_id, system, ayanamsha_id],
     ayanamsha_id=ayanamsha_id, clock_tier=tier).fetchall()
    return validate_clock_rows(rows, build_id=build_id, tier=tier)


def validate_clock_rows(rows, *, build_id, tier):
    """Pure validation for rows already obtained through the governed loader."""
    if not build_id:
        raise ClockUnavailable("build_not_pinned")
    if tier not in RESTRICTED_TABLE_VOCAB or tier == DIVERGENT_FLAGGED:
        raise ClockUnavailable("tier_unavailable")
    # Coherence is checked before tier selection, including unconsumed rows.
    if not rows or any(str(row.get("build_id")) != str(build_id) for row in rows):
        raise ClockUnavailable("build_not_pinned")
    result: list[dict[str, Any]] = []
    for row in rows:
        if row.get("verification_pass_status") != tier:
            continue
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
    if not result:
        raise ClockUnavailable("tier_unavailable")
    return result


def _lord(row: dict[str, Any]) -> str:
    lord = row.get("lord_graha")
    if not lord:
        raise RuntimeError(f"pinned chart_dashas row {row.get('dasha_row_id')!r} has no lord")
    return str(lord)


def _method(system: str) -> DashaMethod:
    method = dasha_method(system)
    if method.l1_producer is None:
        raise ClockUnavailable(f"method_not_built: {method.method_id.value}")
    return method


def boundaries(
    conn: Any, chart_id: str, system: str, *, as_of: datetime,
    build_id: str, ayanamsha_id: str, tier: str,
    level: Literal["MD", "AD", "PD", "SD"] | None = None,
    uncertainty: BoundaryUncertainty | None = None,
    scenario_id: str | None = None,
    method_facts: AshtottariFacts | KalachakraFacts | None = None,
) -> list[Boundary]:
    """Read both stored endpoints, retaining row identity and clipping flags.

    (I) INTERPRETATION: enumeration retains both sides of a shared instant,
    rather than losing either row's provenance or end-truncation qualification.
    ``as_of`` is the explicit request instant, never a wall-clock default.
    """
    _as_utc(as_of)
    method = _method(system)
    rows = _read_rows(conn, chart_id, stored_system(system), build_id=build_id,
                      ayanamsha_id=ayanamsha_id, tier=tier)
    by_id = {str(row["dasha_row_id"]): row for row in rows}
    if len(by_id) != len(rows):
        raise ClockUnavailable("ambiguous_period")
    for row in rows:
        if int(row["level_n"]) > 1:
            parent = by_id.get(str(row.get("parent_row_id")))
            if parent is None or int(parent["level_n"]) != int(row["level_n"]) - 1:
                raise ClockUnavailable("hierarchy_unavailable")
            _check_containment(row, parent)
        if method.method_id.value == "ashtottari":
            if assess_ashtottari(method_facts).state != "applicable":
                raise ClockUnavailable("applicability_unknown_or_inapplicable")
        elif row.get("applies_to_this_chart_flag") is not True:
            raise ClockUnavailable("applicability_unknown_or_inapplicable")
    sigma = boundary_sigma(uncertainty) if uncertainty is not None else None
    return [Boundary(
        instant=row[f"{endpoint}_iso"], level=_LEVEL_NAMES[int(row["level_n"])],
        lord=_lord(row), source_row_id=str(row["dasha_row_id"]), sigma=sigma,
        scenario_id=scenario_id, endpoint=endpoint,
        boundary_truncated=bool(row.get(f"is_truncated_at_window_{endpoint}")),
        method=method, build_id=build_id, ayanamsha_id=ayanamsha_id, tier=tier,
        uncertainty_artifact=uncertainty.artifact_id if uncertainty else None,
    ) for row in rows if level is None or _LEVEL_NAMES[int(row["level_n"])] == level
      for endpoint in ("start", "end")]


def _check_containment(child, parent):
    if not (parent["start_iso"] <= child["start_iso"] < child["end_iso"] <= parent["end_iso"]):
        raise ClockUnavailable("hierarchy_unavailable: child interval outside parent")


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
    if not roots:
        raise ClockUnavailable("hierarchy_unavailable" if active_by_level else "coverage_gap")
    if len(roots) != 1:
        raise ClockUnavailable("ambiguous_period")
    lineage = [roots[0]]
    for level in range(2, 5):
        candidates = [
            row for row in active_by_level.get(level, [])
            if str(row.get("parent_row_id")) == str(lineage[-1]["dasha_row_id"])
        ]
        if not candidates:
            if active_by_level.get(level) or any(
                active_by_level.get(deeper_level) for deeper_level in range(level + 1, 5)
            ):
                raise ClockUnavailable("hierarchy_unavailable")
            continue
        if len(candidates) != 1:
            raise ClockUnavailable("ambiguous_period")
        _check_containment(candidates[0], lineage[-1])
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
    uncertainty: BoundaryUncertainty | None = None,
    method_facts: AshtottariFacts | KalachakraFacts | None = None,
    scenario_id: str | None = None,
) -> PeriodContext:
    """Read the MD–SD hierarchy from the settlement-bound loader."""
    _as_utc(as_of)
    _method(system)
    rows = _read_rows(conn, chart_id, stored_system(system), build_id=build_id,
                      ayanamsha_id=ayanamsha_id, tier=tier)
    return period_context_from_rows(
        rows, chart_id, as_of, system, build_id=build_id, ayanamsha_id=ayanamsha_id,
        tier=tier, uncertainty=uncertainty, method_facts=method_facts, scenario_id=scenario_id)


def period_context_from_rows(
    rows: list[dict[str, Any]],
    chart_id: str,
    as_of: datetime,
    system: str,
    *,
    build_id: str,
    ayanamsha_id: str,
    tier: str,
    uncertainty: BoundaryUncertainty | None = None,
    method_facts: AshtottariFacts | KalachakraFacts | None = None,
    scenario_id: str | None = None,
) -> PeriodContext:
    """Evaluate a previously governed row slice without another SQL read."""
    as_of = _as_utc(as_of)
    method = _method(system)
    rows = validate_clock_rows(rows, build_id=build_id, tier=tier)
    active = _active_hierarchy(rows, as_of)
    lords = {_LEVEL_NAMES[int(row["level_n"])]: _lord(row) for row in active}

    own_spans = [row["end_iso"] - row["start_iso"] for row in active]
    windows = [span * _SANDHI_FRACTION for span in own_spans]
    distances = [min(abs(as_of - row["start_iso"]), abs(row["end_iso"] - as_of)) for row in active]
    # The scalar reports a band that actually contains as_of when one exists.
    in_band = [i for i in range(len(active)) if distances[i] <= windows[i]]
    choices = in_band or list(range(len(active)))
    sandhi_window = windows[min(choices, key=lambda i: distances[i])]
    applicability: Literal["applicable", "method_inapplicable", "unknown"]
    flags = {row.get("applies_to_this_chart_flag") for row in active}
    detail = None
    if method.method_id.value == "ashtottari":
        if method_facts is not None and not isinstance(method_facts, AshtottariFacts):
            raise TypeError("Aṣṭottarī requires AshtottariFacts")
        detail = assess_ashtottari(method_facts)
        applicability = detail.state
    elif False in flags:
        applicability = "method_inapplicable"
    elif flags == {True}:
        applicability = "applicable"
    else:
        applicability = "unknown"
    method_detail = None
    if method.method_id.value == "kalachakra":
        if method_facts is not None and not isinstance(method_facts, KalachakraFacts):
            raise TypeError("Kālacakra requires KalachakraFacts")
        method_detail = method_facts
    return PeriodContext(
        as_of=as_of,
        lords=lords,
        period_ids={
            _LEVEL_NAMES[int(row["level_n"])]: str(row["dasha_row_id"])
            for row in active
        },
        applicability=applicability,
        sigma_boundary=boundary_sigma(uncertainty) if uncertainty is not None else None,
        scenario_id=scenario_id,
        sandhi=any(distance <= window for distance, window in zip(distances, windows)),
        sandhi_window=sandhi_window,
        boundary_truncated=any(
            row.get("is_truncated_at_window_start") or row.get("is_truncated_at_window_end")
            for row in active
        ),
        method=method, build_id=build_id, ayanamsha_id=ayanamsha_id, tier=tier,
        applicability_detail=detail or Applicability(applicability),
        method_detail=method_detail,
        uncertainty_artifact=uncertainty.artifact_id if uncertainty else None,
    )


@dataclass(frozen=True)
class ClockScenario:
    """A sensitivity variant computed by L1 and read by its own pin.

    Non-default start conventions are admitted for the nakṣatra ladder only.
    This is an artifact reference, not a request to recompute a schedule in F2.
    """
    scenario_id: str
    build_id: str
    ayanamsha_id: str
    tier: str
    start_convention: Literal["moon_star", "lagna_star", "satyacharya"]
    artifact_id: str
    fact_ids: tuple[str, ...]
    uncertainty: BoundaryUncertainty | None = None
    method_facts: AshtottariFacts | KalachakraFacts | None = None


@dataclass(frozen=True)
class ScenarioResult:
    scenario: ClockScenario
    context: PeriodContext
    boundaries: tuple[Boundary, ...]


def scenario_set(conn: Any, chart_id: str, as_of: datetime, system: str, *, scenarios: tuple[ClockScenario, ...]) -> tuple[ScenarioResult, ...]:
    method = _method(system)
    results = []
    seen = set()
    for scenario in scenarios:
        if not all((scenario.scenario_id, scenario.build_id, scenario.ayanamsha_id, scenario.tier, scenario.artifact_id, scenario.fact_ids)) or not all(scenario.fact_ids):
            raise ValueError("scenario requires a complete L1 pin and artifact references")
        if scenario.scenario_id in seen:
            raise ValueError("duplicate scenario id")
        seen.add(scenario.scenario_id)
        if scenario.start_convention not in ("moon_star", "lagna_star", "satyacharya"):
            raise ValueError("unsupported start convention; Mūla is a distinct method")
        has_start_variants = "moon_nakshatra" in method.ancestry_groups and bool(
            {"fruition_ladder", "sub_lord_refinement"}.intersection(method.tags)
        )
        if scenario.start_convention != "moon_star" and not has_start_variants:
            raise ValueError("start variants apply to the nakshatra ladder only")
        pin = dict(build_id=scenario.build_id, ayanamsha_id=scenario.ayanamsha_id,
                   tier=scenario.tier, scenario_id=scenario.scenario_id, uncertainty=scenario.uncertainty)
        context = period_context(conn, chart_id, as_of, system, method_facts=scenario.method_facts, **pin)
        results.append(ScenarioResult(scenario, context, tuple(boundaries(conn, chart_id, system, as_of=as_of, method_facts=scenario.method_facts, **pin))))
    return tuple(results)


__all__ = [
    "Boundary", "ClockUnavailable", "PeriodContext", "boundaries", "period_context",
    "DashaMethod", "dasha_method", "ClockFact", "AshtottariFacts", "assess_ashtottari",
    "KalachakraFacts", "BoundaryUncertainty", "boundary_sigma", "boundary_shift",
    "ClockScenario", "ScenarioResult", "scenario_set", "validate_f2_row",
]
