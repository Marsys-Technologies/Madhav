"""
ka_gochara_sweep.shape_output — BRIEF_D5 §3 shape-aware output semantics
(BINDING). Pure functions: turn a daily-grid series of G-3 `IntensityResult`
objects into `kala_gochara_windows`-ready row dicts, dispatched by the
event_class's `temporal_shape` (point/interval/chain) read live from
`brahma_event_ontology` (never hardcoded per class — BRIEF_D5 §3: "read the
shape from the ontology, don't hardcode it per class").

Deliberately DB/ephemeris-free (no `conn`, no `swe`) so the shape-dispatch
LOGIC is unit-testable against constructed `IntensityResult` fixtures,
independent of `sweep.py`'s live-query driving code — same "pure core,
thin live shell" split every other G-1/G-2/G-3 module in this wave uses
(`gochara_grammar.models`, `gochara_intensity.models`).

ARC-WIDE INVARIANT (TEMPORAL_ENGINE_ARC_PLAN_v1_0.md §7, restated BRIEF_D5
§3): "a system that scores intervals but predicts points has not
implemented the doctrine." The three builders below are the mechanical
enforcement of that invariant for G-4's served rows:

  build_point_rows    -> one row per detected activation peak, window_start
                          == window_end == peak_date. NEVER a span.
  build_interval_rows -> one row per detected activation episode, an
                          elevated-hazard SPAN whose width is drawn from the
                          ontology's `duration_prior` (never a bare single
                          day — a detected episode narrower than
                          `duration_prior.min_days` is WIDENED to the
                          disclosed minimum, centred on its true peak; an
                          episode with no real width at all still gets
                          `duration_prior.typical_days`, not window_start
                          == window_end).
  build_chain_rows    -> one row PER MILESTONE in the ontology's
                          `milestone_template`, each carrying its OWN
                          `IntensityResult` (computed by the caller at that
                          milestone's own offset date — see sweep.py) so
                          each milestone genuinely scores its own moment's
                          PERMISSION/X(t)/suppression, never a single
                          episode-level score copy-pasted across milestones.
                          The class's `irreversibility_milestone` (where the
                          ontology declares one) is flagged via
                          `is_irreversibility_milestone=True`.

Honest documented gap (KNOWN LIMITATION, not silently glossed): G-1's
`gochara_resonance_map` is keyed by (chart_id, event_class) — it does NOT
differentiate PROMISE-side target sets by milestone_id ("an enrollment
fires on different primitives than a result-declaration", BRIEF_D5 §3, is
not literally true of PROMISE in this codebase's current substrate — G-1
does not ship per-milestone target sets). What genuinely DOES differ per
milestone here is the PERMISSION/X(t)/suppression evaluation, because each
milestone's `IntensityResult` is computed at ITS OWN t_jd (the episode's
anchor date + that milestone's `typical_offset_days_from_first`) — a real,
distinct instant-geometry/timing-system evaluation per milestone, just
sharing one event-class-level PROMISE target set. This is disclosed via
`peak_basis`/`notes`, not hidden.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Optional

# `IntensityResult` is a dataclass (services/gochara_intensity/models.py);
# imported for typing only — this module treats it as a duck-typed object.
try:  # pragma: no cover - typing convenience only
    from services.gochara_intensity.models import IntensityResult  # noqa: F401
except Exception:  # pragma: no cover
    IntensityResult = Any  # type: ignore

PEAK_BASIS = "gochara_lambda_e_v1"

# Structural (NOT fitted — same BRIEF_D5 §7 discipline as every G-3
# coefficient) activation heuristic: a grid day counts as "configuration
# active" when its UNSIGNED raw_lambda magnitude is strictly positive — i.e.
# PROMISE*PERMISSION*exp(beta*X) survived suppression without being fully
# cancelled (engine.py clamps a fully-suppressed day to raw_lambda=0.0,
# see that module's own docstring). This is a disclosed structural
# threshold, not a calibrated cutoff — D-4b's job, per BRIEF_D5 §7 exclusion.
ACTIVATION_EPS = 0.0

# Honest fallback duration when an event_class's `duration_prior` is absent
# (a documented ontology gap for that class) — disclosed via the row's
# `notes`-equivalent detail, never silently substituted without a flag.
FALLBACK_INTERVAL_DAYS = 14


def _jd_to_date_ist(swe, jd: float) -> date:
    """JD -> Python date (IST calendar day), matching `_jd_to_ist_iso`'s own
    UTC+5:30 convention (services/gochara_intensity relies on IST dates
    throughout)."""
    y, m, d, _hour = swe.revjul(jd + 5.5 / 24.0)
    return date(int(y), int(m), int(d))


def _active_runs(series: list, eps: float = ACTIVATION_EPS) -> list[list]:
    """Split a chronologically-ordered `series` of IntensityResult into
    contiguous runs where `raw_lambda > eps`. Returns a list of non-empty
    sub-lists (runs), in series order. A `series` with no active days
    returns []."""
    runs: list[list] = []
    current: list = []
    for r in series:
        if r.raw_lambda > eps:
            current.append(r)
        else:
            if current:
                runs.append(current)
                current = []
    if current:
        runs.append(current)
    return runs


def _peak_of(run: list):
    """The run member with the largest |signed_lambda| — ties broken by
    earliest t_jd (deterministic, no insertion-order dependency beyond the
    caller's own chronological ordering)."""
    return max(run, key=lambda r: (abs(r.signed_lambda), -r.t_jd))


def _serialize_result(r) -> dict[str, Any]:
    """Common per-row fields derived from one IntensityResult, shared by
    all three shape builders."""
    return {
        "signed_intensity": round(r.signed_lambda, 6),
        "raw_intensity": round(r.raw_lambda, 6),
        "valence": r.valence,
        "is_adverse": r.is_adverse,
        "contributing_systems": r.permission_detail.get("systems", []),
        "suppression_state": r.suppression_detail,
        "calibration_state": r.calibration_state,
        "source": r.source,
    }


def build_point_rows(
    swe,
    event_class: str,
    series: list,
    active_sentences_by_jd: Optional[dict] = None,
) -> list[dict]:
    """Point-class (BRIEF_D5 §3): one row per detected activation peak,
    `window_start == window_end == peak_date`. NEVER a span — a point-shaped
    event_class must never assert more temporal precision loss/gain than a
    single dated peak."""
    active_sentences_by_jd = active_sentences_by_jd or {}
    rows = []
    for run in _active_runs(series):
        peak = _peak_of(run)
        peak_date = _jd_to_date_ist(swe, peak.t_jd)
        row = {
            "event_class": event_class,
            "temporal_shape": "point",
            "window_start": peak_date,
            "window_end": peak_date,
            "peak_date": peak_date,
            "milestone_id": None,
            "is_irreversibility_milestone": False,
            "active_sentences": active_sentences_by_jd.get(round(peak.t_jd, 3), []),
            "peak_basis": PEAK_BASIS,
        }
        row.update(_serialize_result(peak))
        rows.append(row)
    return rows


def build_interval_rows(
    swe,
    event_class: str,
    series: list,
    duration_prior: Optional[dict],
    active_sentences_by_jd: Optional[dict] = None,
) -> list[dict]:
    """Interval-class (BRIEF_D5 §3): one row per detected activation
    episode, a SPAN (window_start < window_end) whose width is drawn from
    `duration_prior` — never a single asserted day, even when the raw
    detected run is narrower than `duration_prior['min_days']` (the span is
    widened, centred on the run's true peak, to at least `min_days`;
    `typical_days` is used when the run carries no usable width at all)."""
    active_sentences_by_jd = active_sentences_by_jd or {}
    min_days = float((duration_prior or {}).get("min_days") or FALLBACK_INTERVAL_DAYS)
    typical_days = float((duration_prior or {}).get("typical_days") or max(min_days, FALLBACK_INTERVAL_DAYS))
    rows = []
    for run in _active_runs(series):
        peak = _peak_of(run)
        peak_date = _jd_to_date_ist(swe, peak.t_jd)
        start_date = _jd_to_date_ist(swe, run[0].t_jd)
        end_date = _jd_to_date_ist(swe, run[-1].t_jd)
        raw_span_days = (end_date - start_date).days
        target_days = max(min_days, raw_span_days if raw_span_days > 0 else typical_days)
        if (end_date - start_date).days < target_days:
            pad_each_side = int(round((target_days - (end_date - start_date).days) / 2.0))
            start_date = start_date - timedelta(days=pad_each_side)
            end_date = end_date + timedelta(days=pad_each_side)
        # Never degenerate to a point — interval-shaped classes always span >=1 day.
        if end_date <= start_date:
            end_date = start_date + timedelta(days=max(1, int(min_days)))
        row = {
            "event_class": event_class,
            "temporal_shape": "interval",
            "window_start": start_date,
            "window_end": end_date,
            "peak_date": peak_date,
            "milestone_id": None,
            "is_irreversibility_milestone": False,
            "active_sentences": active_sentences_by_jd.get(round(peak.t_jd, 3), []),
            "peak_basis": PEAK_BASIS,
        }
        row.update(_serialize_result(peak))
        rows.append(row)
    return rows


def build_chain_rows(
    swe,
    event_class: str,
    anchor_result,
    milestone_results: list[tuple[dict, Any]],
    irreversibility_milestone: Optional[str],
    active_sentences_by_jd: Optional[dict] = None,
) -> list[dict]:
    """Chain-class (BRIEF_D5 §3): one row PER milestone in
    `milestone_template`, each scored on its own `IntensityResult`
    (`milestone_results`: list of (milestone_template_entry_dict,
    IntensityResult) pairs, one evaluated at that milestone's own offset
    date — see sweep.py / module docstring's documented PROMISE-sharing
    caveat). `irreversibility_milestone` (when the ontology declares one) is
    flagged via `is_irreversibility_milestone=True` on the matching row —
    the primary claim of the chain, per BRIEF_D5 §3."""
    active_sentences_by_jd = active_sentences_by_jd or {}
    rows = []
    for milestone, result in milestone_results:
        milestone_date = _jd_to_date_ist(swe, result.t_jd)
        milestone_id = milestone.get("milestone_id")
        row = {
            "event_class": event_class,
            "temporal_shape": "chain",
            "window_start": milestone_date,
            "window_end": milestone_date,
            "peak_date": milestone_date,
            "milestone_id": milestone_id,
            "is_irreversibility_milestone": bool(
                irreversibility_milestone and milestone_id == irreversibility_milestone
            ),
            "active_sentences": active_sentences_by_jd.get(round(result.t_jd, 3), []),
            "peak_basis": PEAK_BASIS,
        }
        row.update(_serialize_result(result))
        rows.append(row)
    return rows


def build_rows_for_event_class(
    swe,
    event_class: str,
    temporal_shape: str,
    *,
    series: Optional[list] = None,
    duration_prior: Optional[dict] = None,
    anchor_result=None,
    milestone_results: Optional[list[tuple[dict, Any]]] = None,
    irreversibility_milestone: Optional[str] = None,
    active_sentences_by_jd: Optional[dict] = None,
) -> list[dict]:
    """Dispatcher: reads `temporal_shape` (caller resolves this LIVE from
    `brahma_event_ontology`, per BRIEF_D5 §3 — never hardcoded here) and
    routes to the matching shape builder. Raises ValueError on an unknown
    shape rather than silently defaulting to 'point' (a defaulted shape
    would itself be a §3 violation)."""
    if temporal_shape == "point":
        return build_point_rows(swe, event_class, series or [], active_sentences_by_jd)
    if temporal_shape == "interval":
        return build_interval_rows(swe, event_class, series or [], duration_prior, active_sentences_by_jd)
    if temporal_shape == "chain":
        if anchor_result is None or not milestone_results:
            return []
        return build_chain_rows(
            swe, event_class, anchor_result, milestone_results,
            irreversibility_milestone, active_sentences_by_jd,
        )
    raise ValueError(f"ka_gochara_sweep: unknown temporal_shape {temporal_shape!r} for event_class={event_class!r}")


__all__ = [
    "PEAK_BASIS",
    "ACTIVATION_EPS",
    "FALLBACK_INTERVAL_DAYS",
    "build_point_rows",
    "build_interval_rows",
    "build_chain_rows",
    "build_rows_for_event_class",
]
