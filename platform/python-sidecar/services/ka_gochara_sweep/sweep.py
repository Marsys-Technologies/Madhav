"""
ka_gochara_sweep.sweep — live sweep driver for D-5 Lane G-4.

Consumes G-3's `services.gochara_intensity` engine (which itself consumes
G-1's `gochara_resonance_map` and G-2's `gochara_grammar` read-only) to
compute a daily-grid lambda_e(t | chart) curve for one (chart_id,
event_class) pair over one horizon chunk, then hands that curve to
`shape_output.build_rows_for_event_class` for BRIEF_D5 §3 shape-aware
row construction.

PERFORMANCE (task brief's explicit warning): a full birth->birth+100y daily
grid is ~36,500 candidate days per event_class. This module follows G-3's
OWN documented batch-efficiency contract:
  - `engine.compute_lambda_e_series` resolves `targets` (gochara_resonance_map
    read) and `dasha_periods` (chart_dashas read) EXACTLY ONCE per chunk call,
    not once per grid day (see engine.py's own module docstring).
  - This module additionally resolves `event_ontology meta` (temporal_shape,
    duration_prior, milestone_template, irreversibility_milestone) ONCE per
    (event_class) call, not once per grid day.
  - `active_sentences` (fact_ids-bearing G-2 ConfigurationSentence rows) are
    gathered a SECOND time, but ONLY at each row's own peak/milestone date
    (a handful of calls per chunk, not one per grid day) — `IntensityResult`
    itself does not carry the raw sentence pool (G-3 keeps it internal to
    `gather_configuration_sentences`), so this is the cheapest way to recover
    the fact_ids/citations the served table needs without re-deriving the
    whole curve.
  - The ORCHESTRATOR-facing writer (`writer.py`) is responsible for calling
    this module in bounded chunks (per event_class x per decade) rather than
    the full 100-year horizon in one call — see that module's docstring.
    THIS module itself places no additional bound beyond honoring the
    `horizon_start_jd`/`horizon_end_jd`/`step_days` the caller passes.

A caller doing LOCAL testing should pass a small `horizon_start_jd`/
`horizon_end_jd` window (a month, a handful of specimen dates) — this
module does not itself refuse a large range, but the task brief is explicit
that materializing the full 100-year horizon is the Cloud Run job's job,
not this lane's local verification step.

CONTINUITY ACROSS CHUNKS, ORDER-INDEPENDENTLY (D-5 RED-C fix v2,
2026-07-20): a chunk boundary must never silently double as a
signal-cessation point. RED-C: `interval`-shaped activations still firing
at a year-substep's last grid day were closed on the spot, unconditionally,
so two live major_gain windows for chart 482012f1 each came out ~365 days
wide, EXACTLY bounded by the writer's per-year substep chunking.

A first fix attempt threaded mutable "still open" state from one chunk's
call to the NEXT chunk's call (a cross-substep carry, persisted between
dispatches). That was REJECTED on independent verification: `writer.py`
does NOT dispatch year substeps in strict ascending order (a lexical
substep-key sort bug plus specimen-priority reordering, D-5 GATE fix, both
violate that assumption) — a "carry from the immediately prior chunk" is
meaningless when "prior" isn't well-defined at dispatch time, and could
silently drop a still-open window's tail if the wrong substep ran first.

The fix here is ORDER-INDEPENDENT instead: `sweep_event_class_chunk`, for
`interval`-shaped classes, checks whether ITS OWN chunk's first/last grid
day is active, and if so, independently RE-EVALUATES the underlying
lambda_e signal one day at a time PAST its own boundary (via `compute_lambda_e`,
the same deterministic pure function `compute_lambda_e_series` uses
internally) until it finds genuine inactivity or hits a bound — NOT by
reading any other substep's output. The resulting EXTENDED series (this
chunk's own days plus whatever cross-boundary days were needed) is then
handed to `shape_output.build_interval_rows`, which is itself back to
being fully stateless (see that module's docstring) and simply closes
every run it finds.

DISCOVERY BOUND vs. duration_prior.max_days — DELIBERATELY DECOUPLED (D-5
RED-C fix v3, 2026-07-20 — second independent verification): a v2 attempt
bounded the boundary-discovery scan itself by `duration_prior.max_days` --
this looked reasonable ("why scan further than the cap could ever serve")
but was WRONG and reintroduced a subtler order-dependence: an episode
LONGER than `max_days` (517 days observed against a 365-day max_days in the
verifier's reproduction) has a TRUE start that can be farther from a given
chunk's own edge than `max_days` -- a chunk sitting deep inside such an
episode (e.g. a year near the far end) would hit its scan bound short of
the true start and compute a SHORTER, WRONGLY-ANCHORED window than a chunk
sitting closer to that edge -- three different chunks, three different
`(window_start, window_end, peak_date)` triples for the SAME real episode,
one of which even lands its peak_date exactly on a chunk boundary (the
RED-C artifact relocated, not eliminated). The discovery scan is now bound
by `_BOUNDARY_SCAN_SAFETY_DAYS` (or a class-scaled multiple of it) --
generous, safety-only, NOT tied to `max_days` at all -- so ANY chunk that
touches the episode finds the SAME true_start/true_end regardless of its
own position within the episode. `duration_prior.max_days` is applied
SEPARATELY, as a pure post-hoc clip on the DISCOVERED true window, anchored
to the discovered `true_start` (see `shape_output._widen_interval`) -- so
every chunk that discovers the same true_start computes the identical
clipped window too, independent of how far past the cap that chunk's own
scan happened to reach.

Cost: zero extra queries for the common case (a chunk whose own first/last
grid day is inactive — most years, for most event_classes). Bounded to
`_BOUNDARY_SCAN_SAFETY_DAYS` (or a class-scaled multiple) extra single-day
evaluations only for a chunk that genuinely touches a boundary-crossing
episode — a real but bounded ONE-TIME cost per boundary-touching chunk
(never a per-day-of-full-history cost), incurred only when needed, not on
every substep. This is comfortably inside the 1800s `writer_timeout_seconds`
budget for the default bound even added on top of a chunk's own ~365-day
computation (see writer.py's own per-day cost accounting) — a chunk that
needs to scan in BOTH directions at once (fully inside a very long episode)
has less margin; if a future dispatch regresses on this, tighten
`_BOUNDARY_SCAN_SAFETY_DAYS` or split the scan into its own substep rather
than raising the writer timeout (mirrors writer.py's own "drop to
per-quarter/per-month chunking rather than raising the timeout" precedent).

ORDER-INDEPENDENCE / no double-serving: this makes ANY two chunks that
touch the SAME real episode compute IDENTICAL results — `compute_lambda_e`
is a pure function of (chart config, targets, dasha_periods, t_jd), and the
scan is always anchored at a FIXED, well-defined calendar boundary (a
year's own Jan-1/Dec-31), not at "wherever a scan happened to start" — so
regardless of WHICH chunk runs first, or WHERE within a long episode it
sits, both independently arrive at the same true_start/true_end/peak (as
long as the discovery bound is generous enough to actually reach the true
edges — see DISCOVERY BOUND note above), hence the same
(window_start, peak_date, milestone_id) natural key, hence the same
`kala_gochara_windows` row — the second chunk's insert just UPSERTs the
identical row via the existing `ON CONFLICT ... DO UPDATE` (writer.py
`_insert_rows`), not a duplicate. This holds for ANY dispatch order:
numeric, the (buggy, now-fixed) lexical order, or specimen-priority-shuffled.

KNOWN LIMITATION (disclosed, not hidden): if a real activation genuinely
outlives the discovery bound itself (`_BOUNDARY_SCAN_SAFETY_DAYS`, several
YEARS by default, scaled up further for large `max_days` classes) from BOTH
directions relative to some chunk's own position, that chunk's scan can
still fall short of a true edge. This is now a far more extreme,
essentially pathological scenario than the v2 design's failure mode (which
broke at ~2x a 365-day `max_days`, i.e. ~2 years) — not observed in this
wave's live data (RED-C's actual major_gain episode is a few hundred days).
Even in that residual case, every served row is still a legitimately
capped, non-artifact window (never wider than `max_days`, never bounded by
a bare chunk edge) — the RED-C defect this fix targets.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from services.gochara_intensity import compute_lambda_e, compute_lambda_e_series
from services.gochara_intensity import gather_configuration_sentences
from services.gochara_intensity.engine import fetch_temporal_shape
from services.gochara_grammar import resonance_map as RM
from services.gochara_grammar import dasha_data as DD
from services.gochara_intensity.enrichment import enrich_targets
from services.gochara_intensity._dbutil import savepoint_scope

from .shape_output import build_rows_for_event_class, build_interval_rows, ACTIVATION_EPS

logger = logging.getLogger(__name__)

DEFAULT_STEP_DAYS = 1.0  # daily grid, per BRIEF_D5 §6

# Safety-only bound for the order-independent boundary-DISCOVERY scan (see
# module docstring's DISCOVERY BOUND note) -- deliberately NOT derived from
# any event_class's `duration_prior.max_days` (that coupling was the v2
# design's bug: an episode longer than max_days could put a chunk's own
# position farther from the true edge than max_days itself). ~4.5 years --
# generous relative to every interval-shaped event_class's max_days in this
# wave (max_days=365 for major_gain; no other interval class currently
# exceeds it), while staying well inside the writer's per-substep timeout
# budget even when triggered from both directions at once (see module
# docstring's Cost note).
_BOUNDARY_SCAN_SAFETY_DAYS = 1500


def _boundary_scan_bound_days(max_days: Optional[float]) -> int:
    """The discovery-scan bound: `_BOUNDARY_SCAN_SAFETY_DAYS`, or 4x a
    larger-than-usual `duration_prior.max_days` if that would exceed it --
    scales the safety margin up for a future event_class with a
    substantially longer declared cap, without coupling the bound TO
    max_days the way v2 did (4x is headroom, not an assumption that the
    true episode never exceeds max_days -- see module docstring)."""
    if max_days:
        return max(_BOUNDARY_SCAN_SAFETY_DAYS, int(max_days) * 4)
    return _BOUNDARY_SCAN_SAFETY_DAYS


def fetch_ontology_meta(conn, event_class: str) -> dict[str, Any]:
    """Live-read the DR-13 shape-relevant slice of `brahma_event_ontology`
    for `event_class` -- temporal_shape, duration_prior, milestone_template,
    irreversibility_milestone. Honest degrade (documented defaults, never a
    crash) on any DB-shape surprise -- mirrors every other read in this
    wave's G-1/G-2/G-3 packages."""
    meta = {
        "temporal_shape": None,
        "duration_prior": None,
        "milestone_template": None,
        "irreversibility_milestone": None,
    }
    if conn is None:
        return meta
    try:
        with savepoint_scope(conn, "ontology_meta"):
            cur = conn.execute(
                "SELECT temporal_shape, duration_prior, milestone_template, irreversibility_milestone "
                "FROM brahma_event_ontology WHERE event_class_id = %s",
                [event_class],
            )
            row = cur.fetchone()
            if row is not None:
                if isinstance(row, dict):
                    meta["temporal_shape"] = row.get("temporal_shape")
                    meta["duration_prior"] = row.get("duration_prior")
                    meta["milestone_template"] = row.get("milestone_template")
                    meta["irreversibility_milestone"] = row.get("irreversibility_milestone")
                else:
                    meta["temporal_shape"], meta["duration_prior"], meta["milestone_template"], \
                        meta["irreversibility_milestone"] = row
    except Exception as exc:  # noqa: BLE001
        logger.info("[ka_gochara_sweep] brahma_event_ontology read failed for event_class=%s: %s",
                    event_class, exc)
    if not meta["temporal_shape"]:
        meta["temporal_shape"] = fetch_temporal_shape(conn, event_class)
    return meta


def _gather_active_sentences_at(swe, conn, chart_id: str, targets, t_jd: float,
                                 window_days: float = 2.0) -> list[dict]:
    """Re-gather G-2's fact_ids-bearing ConfigurationSentence pool for a
    single served row's date (peak or milestone date) -- see module
    docstring's PERFORMANCE note for why this is a bounded, per-row cost,
    not a per-grid-day one."""
    # DEFENSIVE (found live at this lane's verification pass, 2026-07-19):
    # G-2's `primitives.kakshya_cell_crossing` can catch its OWN chart_facts
    # read failure INTERNALLY (logs + returns [], never raises) without
    # itself resetting the connection's transaction state -- so
    # `gather_configuration_sentences` can return a normally-degraded
    # (non-exceptional) result while leaving `conn` in Postgres'
    # "current transaction is aborted" state. G-3's own `compute_lambda_e`
    # never surfaces this because its LATER internal calls (compute_permission,
    # valence.fetch_valence, etc.) each carry their own savepoint_scope-guarded
    # try/except and happen to clear it before returning -- but THIS module
    # calls `gather_configuration_sentences` a SECOND time, standalone, after
    # `compute_lambda_e_series` has already returned, with no such later call
    # to absorb a poisoned state. `savepoint_scope` here is this module's OWN
    # defensive boundary (both the raise-on-failure path AND the
    # silently-swallowed-internally path -- see `_dbutil.savepoint_scope`'s
    # own docstring for how it now covers both) -- not a change to any
    # G-1/G-2/G-3 file (all three remain untouched, must_not_touch honored).
    # CORRECTION (D-5 G-4 second incident, 2026-07-19/20): this used to call
    # `safe_rollback` (bare `conn.rollback()`) unconditionally in a `finally`
    # block -- exactly the pattern that destroys the orchestrator's own
    # `SAVEPOINT writer_exec` when this module runs inside a real substep.
    # `savepoint_scope` replaces both the except-path AND the
    # always-run-regardless-of-outcome `finally` shape with a single
    # SAVEPOINT-scoped block.
    try:
        with savepoint_scope(conn, "active_sentences_regather"):
            sentences = gather_configuration_sentences(swe, conn, chart_id, targets,
                                                        t_jd - window_days, t_jd + window_days)
    except Exception as exc:  # noqa: BLE001
        logger.info("[ka_gochara_sweep] active-sentence re-gather failed at t_jd=%s: %s", t_jd, exc)
        return []
    return [
        {
            "primitive": s.primitive,
            "target_type": s.target_type,
            "target_ref": s.target_ref,
            "transit_planet": s.transit_planet,
            "secondary_planet": s.secondary_planet,
            "event_datetime_ist": s.event_datetime_ist,
            "fact_ids": s.fact_ids,
            "classical_citation": s.classical_citation,
            "uncited_extension": s.uncited_extension,
        }
        for s in sentences
    ]


def _extend_series_across_boundary(
    swe, conn, chart_id: str, event_class: str, series: list, *,
    targets, dasha_periods, shape: str, ayanamsha_id: str,
    horizon_start_jd: float, horizon_end_jd: float, bound_days: int,
) -> list:
    """Order-independent boundary extension (D-5 RED-C fix v2, see module
    docstring). If `series`' own first/last grid day is active, re-evaluate
    the signal one day at a time PAST this chunk's own boundary (a pure,
    deterministic single-day `compute_lambda_e` call — never reading
    another substep's output) until genuine inactivity is found or
    `bound_days` is exhausted. Returns a new, chronologically-ordered
    series (unchanged when neither edge is active — the common case, zero
    extra compute)."""
    if not series:
        return series
    prefix: list = []
    suffix: list = []

    if series[0].raw_lambda > ACTIVATION_EPS:
        jd = horizon_start_jd
        for _ in range(bound_days):
            jd -= 1.0
            try:
                with savepoint_scope(conn, "boundary_scan_backward"):
                    result = compute_lambda_e(
                        swe, conn, chart_id, event_class, jd,
                        targets=targets, dasha_periods=dasha_periods, temporal_shape=shape,
                        ayanamsha_id=ayanamsha_id,
                    )
            except Exception as exc:  # noqa: BLE001
                logger.info("[ka_gochara_sweep] boundary backward-scan failed at jd=%s for %s: %s",
                            jd, event_class, exc)
                break
            prefix.append(result)
            if result.raw_lambda <= ACTIVATION_EPS:
                break
        prefix.reverse()  # was appended latest-first (jd decreasing); series wants chronological order

    if series[-1].raw_lambda > ACTIVATION_EPS:
        # `compute_lambda_e_series` loops `while t <= t_end_jd` (engine.py),
        # so `horizon_end_jd` itself is ALREADY the series' last grid day
        # (a genuine one-day overlap with the NEXT chunk's own
        # horizon_start_jd, a pre-existing property of writer.py's chunk
        # boundaries, not introduced here) -- start probing one day PAST it.
        jd = horizon_end_jd
        for _ in range(bound_days):
            jd += 1.0
            try:
                with savepoint_scope(conn, "boundary_scan_forward"):
                    result = compute_lambda_e(
                        swe, conn, chart_id, event_class, jd,
                        targets=targets, dasha_periods=dasha_periods, temporal_shape=shape,
                        ayanamsha_id=ayanamsha_id,
                    )
            except Exception as exc:  # noqa: BLE001
                logger.info("[ka_gochara_sweep] boundary forward-scan failed at jd=%s for %s: %s",
                            jd, event_class, exc)
                break
            suffix.append(result)
            if result.raw_lambda <= ACTIVATION_EPS:
                break

    if not prefix and not suffix:
        return series
    return prefix + list(series) + suffix


def sweep_event_class_chunk(
    swe,
    conn,
    chart_id: str,
    event_class: str,
    horizon_start_jd: float,
    horizon_end_jd: float,
    step_days: float = DEFAULT_STEP_DAYS,
    ayanamsha_id: str = "lahiri_chitrapaksha",
) -> list[dict]:
    """Compute one (chart_id, event_class) horizon chunk's served rows,
    shape-dispatched per BRIEF_D5 §3. Returns `kala_gochara_windows`-ready
    row dicts (still missing `chart_id`/`computed_at` — the writer adds
    those at insert time). Honest empty list (not a crash) when G-1 has no
    resonance-map targets for this chart/event_class -- PROMISE, and
    therefore every lambda_e in the chunk, is a real 0.0.

    Stateless and order-independent — see module docstring. For
    `interval`-shaped classes, a chunk whose own boundary is active gets its
    `series` transparently extended (bounded, deterministic) before
    `shape_output.build_interval_rows` sees it; the caller (writer.py) does
    not need to pass or persist anything across chunks."""
    meta = fetch_ontology_meta(conn, event_class)
    shape = meta["temporal_shape"] or "point"

    with savepoint_scope(conn, "resonance_targets_sweep"):
        raw_targets = RM.fetch_resonance_targets(conn, chart_id, event_class)
    targets = enrich_targets(conn, raw_targets, ayanamsha_id=ayanamsha_id)
    with savepoint_scope(conn, "dasha_periods_sweep"):
        dasha_periods = DD.fetch_dasha_periods(conn, chart_id, ayanamsha_id=ayanamsha_id)

    if not targets:
        logger.info("[ka_gochara_sweep] no gochara_resonance_map targets for chart=%s event_class=%s "
                    "-- honest empty chunk (PROMISE=0.0), not fabricated.", chart_id, event_class)

    if shape in ("point", "interval"):
        with savepoint_scope(conn, "lambda_e_series"):
            series = compute_lambda_e_series(
                swe, conn, chart_id, event_class, horizon_start_jd, horizon_end_jd, step_days,
                targets=targets, dasha_periods=dasha_periods, temporal_shape=shape,
                ayanamsha_id=ayanamsha_id,
            )
        # (this module's own second query pass, `_gather_active_sentences_at`
        # below, is independently savepoint-scoped -- see that function.)
        active_by_jd: dict[float, list] = {}
        if shape == "interval" and targets:
            max_days = (meta["duration_prior"] or {}).get("max_days")
            # DECOUPLED from max_days (D-5 RED-C fix v3) -- the discovery
            # scan must find the episode's TRUE edges regardless of how far
            # they sit from any one chunk's own position, not just far
            # enough to reach a max_days-wide slice. See module docstring's
            # DISCOVERY BOUND note.
            bound_days = _boundary_scan_bound_days(max_days)
            series = _extend_series_across_boundary(
                swe, conn, chart_id, event_class, series,
                targets=targets, dasha_periods=dasha_periods, shape=shape, ayanamsha_id=ayanamsha_id,
                horizon_start_jd=horizon_start_jd, horizon_end_jd=horizon_end_jd, bound_days=bound_days,
            )
        rows = build_rows_for_event_class(
            swe, event_class, shape, series=series,
            duration_prior=meta["duration_prior"],
        )
        # Now that peak/episode dates are known, re-gather active_sentences
        # ONLY for those specific dates (bounded cost -- see module docstring).
        for row in rows:
            peak_jd = _date_to_jd(swe, row["peak_date"])
            key = round(peak_jd, 3)
            if key not in active_by_jd:
                active_by_jd[key] = _gather_active_sentences_at(swe, conn, chart_id, targets, peak_jd)
            row["active_sentences"] = active_by_jd[key]
        return rows

    if shape == "chain":
        milestone_template = meta["milestone_template"] or []
        if not milestone_template:
            logger.info("[ka_gochara_sweep] chain-shaped event_class=%s has no milestone_template -- "
                        "honest empty chunk.", event_class)
            return []
        # Anchor: the strongest single-instant lambda_e across the horizon,
        # evaluated at the SAME daily grid as point/interval classes (this is
        # the one live query point/interval/chain all three share -- see
        # module docstring's PROMISE-sharing caveat for what this anchor
        # feeds vs. what genuinely varies per milestone).
        series = compute_lambda_e_series(
            swe, conn, chart_id, event_class, horizon_start_jd, horizon_end_jd, step_days,
            targets=targets, dasha_periods=dasha_periods, temporal_shape=shape,
            ayanamsha_id=ayanamsha_id,
        )
        active_runs = [r for r in series if r.raw_lambda > 0.0]
        if not active_runs:
            return []
        anchor = max(active_runs, key=lambda r: (abs(r.signed_lambda), -r.t_jd))
        milestone_results: list[tuple[dict, Any]] = []
        for milestone in milestone_template:
            offset_days = float(milestone.get("typical_offset_days_from_first") or 0.0)
            m_jd = anchor.t_jd + offset_days
            result = compute_lambda_e(
                swe, conn, chart_id, event_class, m_jd,
                targets=targets, dasha_periods=dasha_periods, temporal_shape=shape,
                ayanamsha_id=ayanamsha_id,
            )
            milestone_results.append((milestone, result))
        rows = build_rows_for_event_class(
            swe, event_class, shape,
            anchor_result=anchor, milestone_results=milestone_results,
            irreversibility_milestone=meta["irreversibility_milestone"],
        )
        # rows are already paired 1:1 with milestone_results in order (build_chain_rows
        # iterates milestone_results in the same order it received them).
        for row, (_, result) in zip(rows, milestone_results):
            row["active_sentences"] = _gather_active_sentences_at(swe, conn, chart_id, targets, result.t_jd)
        return rows

    raise ValueError(f"ka_gochara_sweep: unsupported temporal_shape {shape!r} for event_class={event_class!r}")


def _date_to_jd(swe, d) -> float:
    return swe.julday(d.year, d.month, d.day, 0.0)


__all__ = ["fetch_ontology_meta", "sweep_event_class_chunk", "DEFAULT_STEP_DAYS"]
