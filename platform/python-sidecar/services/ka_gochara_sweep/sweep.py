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

CONTINUITY ACROSS CHUNKS, ORDER-INDEPENDENTLY, v1-v3 (SUPERSEDED, see v4
below): a chunk boundary must never silently double as a signal-cessation
point. RED-C: `interval`-shaped activations still firing at a year-substep's
last grid day were closed on the spot, unconditionally, so two live
major_gain windows for chart 482012f1 each came out ~365 days wide, EXACTLY
bounded by the writer's per-year substep chunking.

Three prior fix attempts, all REJECTED on independent verification:
  v1 - a cross-substep runtime "carry" (mutable "still open" state threaded
       from one chunk's call to what it ASSUMED was the next). Broken by
       `writer.py`'s real dispatch order (a lexical substep-key sort bug
       plus specimen-priority reordering both violate strict ascending-year
       dispatch) -- a "carry from the immediately prior chunk" is
       meaningless when "prior" isn't well-defined at dispatch time.
  v2 - this module independently RE-EVALUATING the signal one day at a time
       PAST a chunk's own boundary (via `compute_lambda_e`) until finding
       genuine inactivity or a bound tied to `duration_prior.max_days`.
       Order-independent in principle, but the scan bound coupling to
       max_days was itself the bug (see v3).
  v3 - decoupled the scan bound from max_days (a large, safety-only
       constant instead) and anchored the max_days clip to the discovered
       true_start rather than a computed centre. Still relied on a BOUNDED
       scan, though -- a chunk sitting far enough from an episode's true
       edge (deep inside a multi-year episode) could still exhaust even a
       generous bound short of the true edge, computing a wrongly-anchored
       window; independent verification reproduced this with a ~5.5-year
       (2007-day) episode, and flagged that a multi-thousand-day scan for a
       chunk deep inside a long episode also risks approaching
       `writer_timeout_seconds` -- the exact problem that motivated this
       wave's decade->year re-chunk in the first place (see writer.py's own
       CHUNK GRANULARITY note).

CONTINUITY ACROSS CHUNKS, ORDER-INDEPENDENTLY, v4 (D-5 RED-C fix,
2026-07-20, THIRD independent verification -- CURRENT): stop scanning
across chunk boundaries at all. Each year-substep computes ONLY its own
STRICTLY chunk-bounded segment (`shape_output.build_interval_segments` --
zero cross-boundary compute, ~365 evaluations max, NO scan-distance risk at
ANY episode length, however long). Each segment records two cheap booleans
-- was it active at its OWN leftmost grid day, was it active at its OWN
rightmost grid day (`left_active`/`right_active`) -- plus its raw
(unwidened) `raw_start`/`raw_end`.

A SEPARATE, idempotent, DB-DRIVEN consolidation step (writer.py
`_consolidate_interval_segment`) chains a new segment with an ALREADY-
COMMITTED adjacent segment for the same (chart_id, event_class) by looking
up `kala_gochara_windows.continuity_state` (migration 461) -- exact
calendar-date adjacency (`raw_end + 1 day == raw_start`) on PERSISTED
state, never a runtime scan or a dispatch-order assumption. Merging deletes
the consumed neighbor row(s) and inserts ONE new row for the merged span
(delete-then-reinsert, the SAME idempotency pattern already used elsewhere
in this codebase, per §N.3), with `duration_prior.max_days` applied as a
post-hoc clip on the merged span (reusing `shape_output._widen_interval`'s
v3 true-start-anchored clip, still correct and needed here).

WHY THIS HAS NO SCAN-DISTANCE DEPENDENCE, AT ANY EPISODE LENGTH: merge cost
is proportional to the number of ALREADY-COMMITTED adjacent segments (0, 1,
or 2 -- a segment can chain a left neighbor AND a right neighbor in one
step), each found via a single indexed DB lookup, never to how far a signal
extends in calendar time. A 10-year episode costs exactly the same PER-YEAR
consolidation work as a 10-day one -- one bounded local computation plus at
most two O(1) neighbor lookups, every time, regardless of episode length.
This also means correctness is invariant to dispatch order BY
CONSTRUCTION: a new segment always searches BOTH directions against
whatever is CURRENTLY in the database (not "what ran before me" in any
runtime sense), and the invariant "no two date-adjacent
flag-matching rows exist unmerged in the DB" is maintained after every
single consolidation, so at most one neighbor can ever be found on each
side (a longer chain was already collapsed into one row by an earlier
consolidation, in whatever order that happened). It also converges
correctly ACROSS separate dispatches/attempts, not just within one -- a
segment committed in an earlier partial build gets picked up and merged the
moment its neighbor's substep finally runs, in a LATER dispatch, with no
special-casing needed.
"""
from __future__ import annotations

import logging
from typing import Any

from services.gochara_intensity import compute_lambda_e, compute_lambda_e_series
from services.gochara_intensity import gather_configuration_sentences
from services.gochara_intensity.engine import fetch_temporal_shape
from services.gochara_grammar import resonance_map as RM
from services.gochara_grammar import dasha_data as DD
from services.gochara_intensity.enrichment import enrich_targets
from services.gochara_intensity._dbutil import savepoint_scope

from .shape_output import build_rows_for_event_class, build_interval_segments

logger = logging.getLogger(__name__)

DEFAULT_STEP_DAYS = 1.0  # daily grid, per BRIEF_D5 §6


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
    shape-dispatched per BRIEF_D5 §3. For `point`/`chain` shapes, returns
    `kala_gochara_windows`-ready row dicts (still missing `chart_id`/
    `computed_at` — the writer adds those at insert time). For `interval`
    shape, returns RAW SEGMENT dicts (D-5 RED-C fix v4 — see module
    docstring) — `temporal_shape=='interval'`, `raw_start`/`raw_end`/
    `left_active`/`right_active`, and `duration_prior` embedded (so the
    caller doesn't need a second ontology fetch) — NOT yet windowed/
    widened/capped; `writer.py`'s DB-driven consolidation
    (`_consolidate_interval_segment`) turns each into a final served row.
    Honest empty list (not a crash) when G-1 has no resonance-map targets
    for this chart/event_class -- PROMISE, and therefore every lambda_e in
    the chunk, is a real 0.0.

    STRICTLY bounded to `series`' own chunk — NO cross-boundary compute of
    any kind, at any episode length (see module docstring)."""
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
        if shape == "interval":
            rows = build_interval_segments(swe, event_class, series)
            for row in rows:
                row["duration_prior"] = meta["duration_prior"]
        else:
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
