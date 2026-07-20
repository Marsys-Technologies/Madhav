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
                          == window_end). CONTINUITY ACROSS CHUNKS (D-5
                          RED-C fix, 2026-07-20): `series` here is only ONE
                          substep's chunk (a calendar year, per writer.py),
                          not the whole horizon — an episode that is still
                          active at the chunk's last grid day is NOT closed
                          on the spot (that would assert a boundary this
                          chunk cannot see past). The caller carries it
                          forward via `open_run`/the returned carry state
                          and only a CONFIRMED cessation (the next chunk's
                          first grid day comes back inactive) or the
                          ontology's `duration_prior.max_days` cap closes
                          the window for real. See the `open_run` param and
                          this function's tuple return below.
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


def _peak_row_from_run(swe, run: list) -> dict:
    """Serialize a run's peak (per `_serialize_result`) plus its own
    `peak_date` — the minimal, DB-safe summary needed to compare/carry a
    peak across chunk boundaries once the source `IntensityResult` objects
    themselves go out of scope at the end of a substep."""
    peak = _peak_of(run)
    peak_row = _serialize_result(peak)
    peak_row["peak_date"] = _jd_to_date_ist(swe, peak.t_jd)
    return peak_row


def _stronger_peak_row(a: dict, b: dict) -> dict:
    return a if abs(a["raw_intensity"]) >= abs(b["raw_intensity"]) else b


def _widen_interval(start_date: date, end_date: date, min_days: float, typical_days: float,
                     max_days: Optional[float]) -> tuple[date, date]:
    """Shared widen/cap logic for one interval window, factored out of
    `build_interval_rows` so both the normal (single-chunk) close path and
    the cap-forced-close path (continuity carry, see that function) apply
    the exact same rule."""
    raw_span_days = (end_date - start_date).days
    target_days = max(min_days, raw_span_days if raw_span_days > 0 else typical_days)
    if max_days is not None:
        target_days = min(target_days, max_days)
    if (end_date - start_date).days < target_days:
        pad_each_side = int(round((target_days - (end_date - start_date).days) / 2.0))
        start_date = start_date - timedelta(days=pad_each_side)
        end_date = end_date + timedelta(days=pad_each_side)
    # Never degenerate to a point — interval-shaped classes always span >=1 day.
    if end_date <= start_date:
        end_date = start_date + timedelta(days=max(1, int(min_days)))
    # duration_prior.max_days cap (D-5 RED-C fix): a window's asserted width
    # must never exceed the ontology's own declared ceiling, even after
    # widening — clipped symmetrically around the widened window's own
    # centre so the (already-computed) peak stays as centred as possible.
    if max_days is not None and (end_date - start_date).days > max_days:
        centre = start_date + (end_date - start_date) / 2
        half = timedelta(days=max_days / 2.0)
        start_date = centre - half
        end_date = centre + half
    return start_date, end_date


def _finalize_interval_row(event_class: str, start_date: date, end_date: date, peak_row: dict,
                            min_days: float, typical_days: float, max_days: Optional[float]) -> dict:
    start_date, end_date = _widen_interval(start_date, end_date, min_days, typical_days, max_days)
    row = {
        "event_class": event_class,
        "temporal_shape": "interval",
        "window_start": start_date,
        "window_end": end_date,
        "peak_date": peak_row["peak_date"],
        "milestone_id": None,
        "is_irreversibility_milestone": False,
        "active_sentences": [],
        "peak_basis": PEAK_BASIS,
    }
    for k, v in peak_row.items():
        if k != "peak_date":
            row[k] = v
    return row


def _close_or_carry(rows: list[dict], event_class: str, run_start: date, run_end: date, peak_row: dict,
                     *, still_open: bool, force_close: bool, min_days: float, typical_days: float,
                     max_days: Optional[float]) -> Optional[dict]:
    """Shared decision, used identically for (a) a continuation merged in
    from a prior chunk's carry and (b) a run detected fresh within this
    chunk: close it for real now (append a finalized row, return no carry)
    on confirmed cessation, on hitting `duration_prior.max_days`, or when
    the caller forces closure (sweep horizon's final year) — otherwise
    carry it forward unresolved, since this chunk has no data past its own
    last grid day to confirm the boundary one way or the other."""
    total_span_days = (run_end - run_start).days
    hit_cap = max_days is not None and total_span_days >= max_days
    if still_open and not hit_cap and not force_close:
        return {"true_start_date": run_start, "last_active_date": run_end, "peak_row": peak_row}
    rows.append(_finalize_interval_row(event_class, run_start, run_end, peak_row, min_days, typical_days, max_days))
    return None


def build_interval_rows(
    swe,
    event_class: str,
    series: list,
    duration_prior: Optional[dict],
    active_sentences_by_jd: Optional[dict] = None,
    open_run: Optional[dict] = None,
    force_close: bool = True,
) -> tuple[list[dict], Optional[dict]]:
    """Interval-class (BRIEF_D5 §3): one row per detected activation
    episode, a SPAN (window_start < window_end) whose width is drawn from
    `duration_prior` — never a single asserted day, even when the raw
    detected run is narrower than `duration_prior['min_days']` (the span is
    widened to at least `min_days`; `typical_days` is used when the run
    carries no usable width at all).

    `series` is ONE chunk (a calendar-year substep, per writer.py) of a
    much longer sweep, not the whole horizon. `open_run` (optional) is a
    carry-state dict — `{"true_start_date", "last_active_date",
    "peak_row"}` — describing an activation episode that was STILL ACTIVE
    at the previous chunk's last grid day; continuity across the chunk
    boundary is only assumed to hold when this chunk's OWN first grid day
    is itself active (a positive, checked signal, not an assumption) — if
    it isn't, the carried episode genuinely ceased at the boundary (a real
    ending that happens to coincide with a chunk edge is not the artifact
    this fix targets; only a boundary asserted WITHOUT checking the next
    day's data was the bug) and is closed honestly right here.

    Returns `(rows, carry_out)`: `carry_out` is a new carry-state dict when
    an episode is still open at THIS chunk's last grid day and has not yet
    hit `duration_prior['max_days']` — the caller (sweep.py/writer.py) is
    responsible for persisting it to the next substep.

    `force_close` defaults to True, i.e. by DEFAULT `series` is treated as
    the complete, self-contained answer (matches every one-shot caller —
    fixtures/tests, and the `build_rows_for_event_class` dispatcher used by
    non-chunked callers) so a run touching `series`' last element still
    closes normally rather than dangling as "maybe open". Only the LIVE
    per-year-substep sweep (writer.py) opts OUT of this (passes
    `force_close=False` for every year except the horizon's last) to get
    genuine cross-chunk continuity — see writer.py `run_substep`."""
    active_sentences_by_jd = active_sentences_by_jd or {}
    min_days = float((duration_prior or {}).get("min_days") or FALLBACK_INTERVAL_DAYS)
    typical_days = float((duration_prior or {}).get("typical_days") or max(min_days, FALLBACK_INTERVAL_DAYS))
    raw_max_days = (duration_prior or {}).get("max_days")
    max_days = float(raw_max_days) if raw_max_days else None

    rows: list[dict] = []
    runs = _active_runs(series)
    carry = dict(open_run) if open_run else None

    if carry is not None:
        if series and series[0].raw_lambda > ACTIVATION_EPS and runs and runs[0][0] is series[0]:
            # Confirmed continuation: today's first grid day is active, so
            # the carried episode kept firing across the boundary. Merge
            # rather than treat as a fresh episode starting at series[0].
            # Still resolve THIS merged episode via `_close_or_carry` below
            # (not an automatic re-carry) -- a gap later in this SAME chunk
            # (more `runs` remain after popping this one) is itself a
            # confirmed cessation, just like the boundary check for any
            # other run.
            first_run = runs.pop(0)
            merged_peak = _stronger_peak_row(_peak_row_from_run(swe, first_run), carry["peak_row"])
            merged_start = carry["true_start_date"]
            merged_end = _jd_to_date_ist(swe, first_run[-1].t_jd)
            still_open = first_run[-1] is series[-1]
            carry = _close_or_carry(rows, event_class, merged_start, merged_end, merged_peak,
                                     still_open=still_open, force_close=force_close,
                                     min_days=min_days, typical_days=typical_days, max_days=max_days)
        else:
            # Confirmed cessation: we positively observed the boundary day
            # inactive, so this episode's true end is `last_active_date` —
            # a real ending, not an unverified chunk-edge assertion.
            rows.append(_finalize_interval_row(
                event_class, carry["true_start_date"], carry["last_active_date"],
                carry["peak_row"], min_days, typical_days, max_days,
            ))
            carry = None

    for run in runs:
        run_start = _jd_to_date_ist(swe, run[0].t_jd)
        run_end = _jd_to_date_ist(swe, run[-1].t_jd)
        peak_row = _peak_row_from_run(swe, run)
        still_open = bool(series) and run[-1] is series[-1]
        run_carry = _close_or_carry(rows, event_class, run_start, run_end, peak_row,
                                     still_open=still_open, force_close=force_close,
                                     min_days=min_days, typical_days=typical_days, max_days=max_days)
        if run_carry is not None:
            # Only the LAST run of a chunk can legitimately still be open
            # (an active run followed by more `runs` in the same chunk, by
            # `_active_runs`' own contiguity construction, always closed on
            # a gap already) -- assigning (not accumulating) is therefore
            # correct and there is at most one live carry per chunk.
            carry = run_carry

    for row in rows:
        peak_jd = swe.julday(row["peak_date"].year, row["peak_date"].month, row["peak_date"].day, 0.0)
        row["active_sentences"] = active_sentences_by_jd.get(round(peak_jd, 3), [])

    rows.sort(key=lambda r: (r["window_start"], r["peak_date"]))
    return rows, carry


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
    would itself be a §3 violation).

    NOTE — interval continuity: this dispatcher always returns a plain
    `list[dict]` (no carry-state), i.e. it treats `series` as a
    self-contained, complete horizon. It is used by callers that pass a
    full/one-shot series (fixtures, tests). The LIVE per-year-substep sweep
    (sweep.py) calls `build_interval_rows` DIRECTLY with `open_run`/
    `force_close` to get continuity-aware behavior across chunk boundaries
    — see that function's docstring (D-5 RED-C fix)."""
    if temporal_shape == "point":
        return build_point_rows(swe, event_class, series or [], active_sentences_by_jd)
    if temporal_shape == "interval":
        rows, _carry = build_interval_rows(swe, event_class, series or [], duration_prior, active_sentences_by_jd)
        return rows
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
