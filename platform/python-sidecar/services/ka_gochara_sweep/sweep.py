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
from services.gochara_intensity._dbutil import safe_rollback

from .shape_output import build_rows_for_event_class

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
        safe_rollback(conn)
    if not meta["temporal_shape"]:
        meta["temporal_shape"] = fetch_temporal_shape(conn, event_class)
    return meta


def _gather_active_sentences_at(swe, conn, chart_id: str, targets, t_jd: float,
                                 window_days: float = 2.0) -> list[dict]:
    """Re-gather G-2's fact_ids-bearing ConfigurationSentence pool for a
    single served row's date (peak or milestone date) -- see module
    docstring's PERFORMANCE note for why this is a bounded, per-row cost,
    not a per-grid-day one."""
    try:
        sentences = gather_configuration_sentences(swe, conn, chart_id, targets,
                                                    t_jd - window_days, t_jd + window_days)
    except Exception as exc:  # noqa: BLE001
        logger.info("[ka_gochara_sweep] active-sentence re-gather failed at t_jd=%s: %s", t_jd, exc)
        safe_rollback(conn)
        return []
    finally:
        # DEFENSIVE (found live at this lane's verification pass, 2026-07-19):
        # G-2's `primitives.kakshya_cell_crossing` can catch its OWN chart_facts
        # read failure INTERNALLY (logs + returns [], never raises) without
        # itself resetting the connection's transaction state -- so
        # `gather_configuration_sentences` can return a normally-degraded
        # (non-exceptional) result while leaving `conn` in Postgres'
        # "current transaction is aborted" state. G-3's own `compute_lambda_e`
        # never surfaces this because its LATER internal calls (compute_permission,
        # valence.fetch_valence, etc.) each carry their own safe_rollback-guarded
        # try/except and happen to clear it before returning -- but THIS module
        # calls `gather_configuration_sentences` a SECOND time, standalone, after
        # `compute_lambda_e_series` has already returned, with no such later call
        # to absorb a poisoned state. Unconditional safe_rollback here (success or
        # failure) is this module's OWN defensive boundary, per `_dbutil.py`'s own
        # documented discipline ("called ... right after any of ITS OWN try/except
        # blocks around a G-1/G-2 call catches something") -- not a change to any
        # G-1/G-2/G-3 file (all three remain untouched, must_not_touch honored).
        safe_rollback(conn)
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
    shape-dispatched per BRIEF_D5 §3. Returns `kala_gochara_windows`-ready
    row dicts (still missing `chart_id`/`computed_at` — the writer adds
    those at insert time). Honest empty list (not a crash) when G-1 has no
    resonance-map targets for this chart/event_class -- PROMISE, and
    therefore every lambda_e in the chunk, is a real 0.0."""
    meta = fetch_ontology_meta(conn, event_class)
    shape = meta["temporal_shape"] or "point"

    raw_targets = RM.fetch_resonance_targets(conn, chart_id, event_class)
    safe_rollback(conn)
    targets = enrich_targets(conn, raw_targets, ayanamsha_id=ayanamsha_id)
    dasha_periods = DD.fetch_dasha_periods(conn, chart_id, ayanamsha_id=ayanamsha_id)
    safe_rollback(conn)

    if not targets:
        logger.info("[ka_gochara_sweep] no gochara_resonance_map targets for chart=%s event_class=%s "
                    "-- honest empty chunk (PROMISE=0.0), not fabricated.", chart_id, event_class)

    if shape in ("point", "interval"):
        series = compute_lambda_e_series(
            swe, conn, chart_id, event_class, horizon_start_jd, horizon_end_jd, step_days,
            targets=targets, dasha_periods=dasha_periods, temporal_shape=shape,
            ayanamsha_id=ayanamsha_id,
        )
        safe_rollback(conn)  # defensive reset before this module's own second query pass (see
                              # _gather_active_sentences_at's docstring for why this is needed)
        active_by_jd: dict[float, list] = {}
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
