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
                          == window_end), and NEVER wider than
                          `duration_prior.max_days` (D-5 RED-C fix,
                          2026-07-20 — the original bug: nothing enforced
                          this ceiling at all).

                          ORDER-INDEPENDENCE, v1-v3 (SUPERSEDED, see v4
                          below): earlier RED-C fix attempts made `series`
                          (one chunk = one calendar-year substep, per
                          writer.py) either CLOSE-DEFERRING (a cross-substep
                          runtime "carry", v1 -- assumed ascending dispatch
                          order, which is false: a lexical substep-key sort
                          bug plus specimen-priority reordering both violate
                          it) or had `sweep.py` re-evaluate the signal past
                          a chunk's own boundary via a bounded scan (v2/v3
                          -- correct in principle, but a chunk far from an
                          episode's true edge could exhaust its scan budget
                          short of it, computing a wrongly-anchored window;
                          independent verification reproduced this at
                          successively larger episode lengths across three
                          rounds).

                          ORDER-INDEPENDENCE, v4 (D-5 RED-C fix, 2026-07-20,
                          third independent verification -- CURRENT): this
                          function is fully SELF-CONTAINED and stateless --
                          it treats whatever `series` it is handed as the
                          COMPLETE answer, closing every run found. It
                          remains useful for one-shot/complete-series
                          callers (fixtures, the dispatcher below). The LIVE
                          per-year-substep sweep no longer tries to make ONE
                          chunk call resolve a whole cross-boundary episode
                          at all -- see `build_interval_segments` (bounded
                          strictly to its own chunk, zero cross-boundary
                          compute, no scan-distance risk at any episode
                          length) and `sweep.py`/`writer.py`'s DB-driven
                          consolidation (chains already-committed adjacent
                          segments by reading persisted state, never by a
                          runtime scan or dispatch-order assumption).
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


def _local_maxima(run: list) -> list:
    """Every local maximum of `|raw_lambda|` within one contiguous active
    run (D-5 native disposition, 2026-07-20, DR-15/DR-17-compatible fix for
    the "argmax-per-year collapse" defect): a point-shaped event_class was
    serving only the single strongest day per active run, silently dropping
    every other genuine local peak in a multi-modal signal (e.g. a
    dasha-driven system holding a run open all year with its own peak, PLUS
    a separately-timed transit mechanism cresting on a different day within
    the same run) -- collapsing a legitimately multi-peaked density into one
    argmax fabricates false single-peak precision, the same defect class as
    RED-C's chunk-bounded windows (§N.6 lineage).

    Standard local-maximum detection, no tunable knobs beyond `run` itself
    (deliberately NOT specimen-tuned): day i is a local maximum iff its
    magnitude is strictly greater than its left neighbor (or i is the run's
    own first day) AND greater-or-equal to its right neighbor (or i is the
    run's own last day). The >  / >= asymmetry means a flat-topped plateau
    reports exactly ONE representative day -- its EARLIEST day, matching
    `_peak_of`'s own tie-break convention -- not one row per tied day.
    Every detected local max keeps its own full IntensityResult (so the
    caller can attribute a distinct `contributing_systems`/mechanism to
    each), never a single system's detail borrowed across peaks."""
    n = len(run)
    maxima = []
    for i in range(n):
        mag = abs(run[i].signed_lambda)
        left_ok = i == 0 or mag > abs(run[i - 1].signed_lambda)
        right_ok = i == n - 1 or mag >= abs(run[i + 1].signed_lambda)
        if left_ok and right_ok:
            maxima.append(run[i])
    return maxima


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
    """Point-class (BRIEF_D5 §3): one row per detected LOCAL activation
    peak (D-5 native disposition, 2026-07-20 — DR-15/DR-17: multi-modal
    densities are a legitimate served shape; collapsing a run to its single
    global argmax was an arbitrary single-selection collapse. See
    `_local_maxima`'s own docstring for the detection rule and rationale),
    `window_start == window_end == peak_date` on EVERY row. NEVER a span —
    a point-shaped event_class must never assert more temporal precision
    loss/gain than a single dated peak, but a run legitimately carrying
    several distinct local maxima (e.g. two differently-timed mechanisms
    both crossing threshold within the same active stretch) now serves one
    row per maximum, each independently attributed via its own
    `contributing_systems`, not one row speaking for the whole run."""
    active_sentences_by_jd = active_sentences_by_jd or {}
    rows = []
    for run in _active_runs(series):
        for peak in _local_maxima(run):
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


def _widen_interval(start_date: date, end_date: date, min_days: float, typical_days: float,
                     max_days: Optional[float]) -> tuple[date, date]:
    """Widen/cap one detected [start_date, end_date] span, in two
    DELIBERATELY SEPARATE, ORDER-DEPENDENT-SAFE steps (D-5 RED-C fix v3,
    2026-07-20 — second independent verification):

    1. CAP FIRST, anchored to the TRUE (unpadded) `start_date` --
       `end_date = min(end_date, start_date + max_days)`. This must be
       anchored to `start_date`, NEVER to a symmetric centre computed from
       the padded/widened result — a centre-anchored clip depends on
       whatever width THIS PARTICULAR invocation happened to detect, which
       is exactly what broke order-independence for episodes wider than the
       old (bounded-by-max_days) discovery scan: two chunks that
       independently discover the SAME true `start_date` (see
       `sweep.sweep_event_class_chunk`'s boundary-discovery scan, now
       unbounded-by-max_days on its own) but see DIFFERENT (still-correct,
       still-true) `end_date`s before capping would, under the old
       centre-anchored clip, compute two DIFFERENT window rows for the same
       real episode. Anchoring to `start_date` instead means: same
       `start_date` in -> same clipped window out, regardless of how far
       past the cap this particular call's own `end_date` reached.
    2. WIDEN the (already-capped) span up to `min_days` (or `typical_days`
       when it has no usable raw width) — but never back past `max_days`
       (§1 already used the caller's true bounds; this step only pads a
       span that is narrower than the disclosed minimum)."""
    raw_span_days = (end_date - start_date).days
    if max_days is not None and raw_span_days > max_days:
        end_date = start_date + timedelta(days=int(max_days))
        raw_span_days = max_days

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
    return start_date, end_date


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
    widened to at least `min_days`; `typical_days` is used when the run
    carries no usable width at all), and never wider than
    `duration_prior['max_days']`.

    Deliberately STATELESS and self-contained (D-5 RED-C fix v2, see module
    docstring's ORDER-INDEPENDENCE note): `series` is treated as the
    COMPLETE answer for whatever episode(s) it contains — every run found
    is closed, none carried forward. The live per-year-substep sweep
    (sweep.py) is responsible for handing this function a `series` that
    already includes any bounded cross-boundary extension it needed (see
    `sweep.sweep_event_class_chunk`)."""
    active_sentences_by_jd = active_sentences_by_jd or {}
    min_days = float((duration_prior or {}).get("min_days") or FALLBACK_INTERVAL_DAYS)
    typical_days = float((duration_prior or {}).get("typical_days") or max(min_days, FALLBACK_INTERVAL_DAYS))
    raw_max_days = (duration_prior or {}).get("max_days")
    max_days = float(raw_max_days) if raw_max_days else None

    rows = []
    for run in _active_runs(series):
        peak = _peak_of(run)
        peak_date = _jd_to_date_ist(swe, peak.t_jd)
        start_date = _jd_to_date_ist(swe, run[0].t_jd)
        end_date = _jd_to_date_ist(swe, run[-1].t_jd)
        start_date, end_date = _widen_interval(start_date, end_date, min_days, typical_days, max_days)
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


def build_interval_segments(
    swe,
    event_class: str,
    series: list,
    active_sentences_by_jd: Optional[dict] = None,
) -> list[dict]:
    """D-5 RED-C fix v4: pure, cheap, per-chunk segment DETECTION -- no
    widening, no `duration_prior.max_days` cap, no cross-boundary lookahead/
    lookback of any kind. `series` is treated as strictly bounded to ONE
    chunk (one calendar-year substep, per writer.py); each detected run
    becomes a "segment" carrying its RAW (unwidened) `raw_start`/`raw_end`
    plus two booleans: `left_active` (was `series`' own FIRST grid day part
    of this run) and `right_active` (was `series`' own LAST grid day part of
    it). These flags are the ENTIRE cross-chunk-continuity signal this
    function produces -- deliberately not a scan, not a guess, just "did
    this segment touch its own chunk's edge, yes or no."

    The caller (`sweep.py`/`writer.py`) is responsible for the DB-driven
    consolidation that chains segments whose flags/dates line up with an
    ALREADY-COMMITTED neighboring segment for the same (chart_id,
    event_class) -- see `finalize_interval_segment` for turning a
    (possibly-already-merged) raw span into a final served row, and
    `sweep.py`'s module docstring for the full consolidation mechanism and
    why it has no scan-distance dependency at any episode length."""
    active_sentences_by_jd = active_sentences_by_jd or {}
    segments = []
    for run in _active_runs(series):
        peak = _peak_of(run)
        seg = {
            "event_class": event_class,
            "temporal_shape": "interval",
            "raw_start": _jd_to_date_ist(swe, run[0].t_jd),
            "raw_end": _jd_to_date_ist(swe, run[-1].t_jd),
            "left_active": bool(series) and run[0] is series[0],
            "right_active": bool(series) and run[-1] is series[-1],
            "peak_date": _jd_to_date_ist(swe, peak.t_jd),
            "active_sentences": active_sentences_by_jd.get(round(peak.t_jd, 3), []),
            "peak_basis": PEAK_BASIS,
        }
        seg.update(_serialize_result(peak))
        segments.append(seg)
    return segments


def finalize_interval_segment(
    event_class: str,
    raw_start: date,
    raw_end: date,
    peak_row: dict,
    duration_prior: Optional[dict],
) -> dict:
    """D-5 RED-C fix v4: turn a (possibly DB-consolidated/merged) raw
    [raw_start, raw_end] span plus its winning `peak_row` (a segment dict,
    or the result of comparing two segments' peaks — see
    `writer._stronger_peak`) into a final `kala_gochara_windows`-ready row,
    applying the SAME widen/cap discipline as `build_interval_rows`
    (`_widen_interval`, anchored to `raw_start` — see that function's own
    docstring for why the anchor must be the true start, not a computed
    centre). Does NOT set `continuity_state` -- the caller attaches that
    (it depends on whether a merge changed the flags, which this pure
    function has no DB access to know about)."""
    min_days = float((duration_prior or {}).get("min_days") or FALLBACK_INTERVAL_DAYS)
    typical_days = float((duration_prior or {}).get("typical_days") or max(min_days, FALLBACK_INTERVAL_DAYS))
    raw_max_days = (duration_prior or {}).get("max_days")
    max_days = float(raw_max_days) if raw_max_days else None

    window_start, window_end = _widen_interval(raw_start, raw_end, min_days, typical_days, max_days)
    row = {
        "event_class": event_class,
        "temporal_shape": "interval",
        "window_start": window_start,
        "window_end": window_end,
        "peak_date": peak_row["peak_date"],
        "milestone_id": None,
        "is_irreversibility_milestone": False,
        "active_sentences": peak_row.get("active_sentences", []),
        "peak_basis": peak_row.get("peak_basis", PEAK_BASIS),
    }
    for key in ("signed_intensity", "raw_intensity", "valence", "is_adverse",
                "contributing_systems", "suppression_state", "calibration_state", "source"):
        if key in peak_row:
            row[key] = peak_row[key]
    return row


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
    "build_interval_segments",
    "finalize_interval_segment",
    "build_chain_rows",
    "build_rows_for_event_class",
]
