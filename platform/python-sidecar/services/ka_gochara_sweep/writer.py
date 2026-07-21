"""
ka_gochara_sweep.writer — D-5 Lane G-4 HEAVY WriterBase subclass.

FROZEN orchestrator contract (CLAUDE.md §N.2 / ORCHESTRATOR_CONVERGENCE_CLOSE
§2): `@register('ka_gochara_sweep')`, `plan_substeps(ctx)` + `run_substep(ctx,
step)`, `ctx.db_conn` NEVER committed/rolled-back/closed by this writer, no
`_telemetry`/`asset_throughput` writes (orchestrator is the sole build-state
writer).

SUBSTEP CHUNKING (why this is the ONE G-lane expected to need real
sub-stepping, per BRIEF_D5 §1 G-4 row): a chart-relative birth->birth+100y
daily grid is ~36,500 candidate days. This writer never evaluates that in
one substep. It chunks by (event_class x year): one substep per populated
`gochara_resonance_map` event_class, per 1-year slice of the
birth->birth+100y horizon (100 years) -- mirroring `ka_sangam`'s
per-predicate/per-tier sub-stepping grain (`pipeline/orchestrator/writers/
ka_sangam.py`) and reusing the SAME cross-attempt substep-resumption ledger
(`build_substep_progress`, migration 436) that writer pioneered, so a build
interrupted mid-horizon resumes from the last committed year rather than
restarting the whole sweep.

CHUNK GRANULARITY (D-5 REBUILD lifecycle fix, 2026-07-20): a real Cloud Run
dispatch against chart 482012f1 hit the orchestrator's 1800s
`writer_timeout_seconds` watchdog on a single DECADE-sized substep (~3650
days x full primitive/composition/intensity pipeline per day) with zero
rows committed -- a pure chunking-granularity problem, not a correctness
defect (the SAVEPOINT-poisoning bug this wave also fixed is confirmed
resolved separately; this run had zero transaction-abort errors). Since a
decade (~3650 days) didn't finish in 1800s, per-day cost is >0.49s, so this
writer now chunks per YEAR (~365 days/substep, ~10x finer) -- measured live
against chart 482012f1 (see close-report) at well under the budget with
comfortable margin. If a future chart's per-day cost regresses, drop to
per-quarter/per-month chunking rather than raising the timeout.

Event-class discovery is LIVE, not hardcoded: this writer sweeps whatever
`event_class` values actually have `gochara_resonance_map` rows for this
chart (G-1's populated set) -- sweeping an event_class G-1 has not yet
built targets for would honestly produce zero rows (PROMISE=0.0 for every
grid day, per `sweep.sweep_event_class_chunk`'s own docstring) at real
compute cost, so this writer does not waste substeps on them. As G-1's
coverage grows for a chart, this writer's substep plan grows with it on the
next build -- no code change required.

Idempotency (§N.3): delete-then-insert, done ONCE per (chart_id,
event_class) in `plan_substeps` (see DISPATCH ORDER note below) -- NOT
per-substep. `run_substep` itself never deletes.

DISPATCH ORDER IS NOT ASCENDING-YEAR (load-bearing, read before touching
`plan_substeps`/`run_substep`): `steps` is reordered twice --
specimen-priority promotion (below) moves individual years to the front,
and (fixed 2026-07-20, D-5 RED-C) the STABLE sort that used to key on the
raw `step.key` STRING sorted "…:year:10" before "…:year:9" lexically. Any
substep-level logic in this writer MUST be correct under ARBITRARY
dispatch order -- year 10 can run before year 9, and a specimen year can
run before year 0. Two consequences, both fixed in the D-5 RED-C wave:
  (1) the OLD per-substep "year_idx==0 clears this event_class's rows"
      delete assumed year 0 runs first; under real dispatch order it could
      fire AFTER sibling years already committed rows in the SAME build,
      silently wiping them. REMOVED -- deletion now happens exactly once,
      in `plan_substeps`, before ANY substep of a fresh/replanned build
      runs (see `plan_substeps`' fresh-build branch), which is safe under
      any subsequent dispatch order because nothing deletes again after it.
  (2) three successive attempts at cross-chunk INTERVAL-shape continuity
      (a cross-substep runtime "carry"; a bounded cross-boundary re-scan;
      a bigger bounded re-scan) were all REJECTED on independent
      verification for assuming something about a chunk's OWN position or
      dispatch order that doesn't hold at any scale. The CURRENT mechanism
      (D-5 RED-C fix v4) needs no such assumption at all: `run_substep`
      computes each year's segment STRICTLY within its own chunk (via
      `sweep.sweep_event_class_chunk`, zero cross-boundary compute), then
      `_consolidate_interval_segment` (below) chains it with whatever
      ADJACENT segment is ALREADY COMMITTED in the database -- found by
      exact calendar-date lookup on `kala_gochara_windows.continuity_state`
      (migration 461), never by a runtime scan or an assumption about which
      substep ran before this one. See `sweep.py`'s module docstring for
      the full mechanism and why it has no scan-distance dependency at any
      episode length.
"""
from __future__ import annotations

import hashlib
import json as _json
import logging
from datetime import date
from typing import Optional

from pipeline.orchestrator.writers import WriterBase, WriterResult, SubStep, register
from services.ka_gochara_sweep.sweep import sweep_event_class_chunk, DEFAULT_STEP_DAYS
from services.ka_gochara_sweep.shape_output import finalize_interval_segment

logger = logging.getLogger(__name__)

# Sweep horizon: chart-relative birth -> birth+100y, UNIFORM for every chart
# (BRIEF_D5 §6, ratified ARC PLAN §10 Q3) -- deliberately NOT tied to computed
# longevity/ayurdaya (an Ethical Framework violation to do so).
_HORIZON_YEARS = 100
_N_YEARS = _HORIZON_YEARS  # one substep per calendar year -- see module
                            # docstring's CHUNK GRANULARITY note (was 10
                            # decade-sized substeps; a real dispatch hit the
                            # 1800s writer_timeout_seconds watchdog on a
                            # single decade substep, D-5 REBUILD fix 2026-07-20)

# Bump when substep SEMANTICS change, so an in-flight resume ledger from an
# older writer build is treated as a different build and replanned-all
# (mirrors ka_sangam.py's _KA_SANGAM_RESUME_VERSION). Bumped 2 -> decade to
# year re-chunk changes substep-key SEMANTICS (D-5 REBUILD fix 2026-07-20):
# an old decade-keyed ledger must NOT be misread as a completed year.
# Bumped 2 -> 3 (D-5 RED-C fix v1, 2026-07-20, SUPERSEDED): the first fix
# attempt (cross-substep carry state, assumed ascending dispatch order) is
# no longer what this writer does -- see v4 below.
# Bumped 3 -> 4 (D-5 RED-C fix v2/v3, 2026-07-20, SUPERSEDED): a
# cross-boundary re-scan mechanism (bounded first by max_days, then by a
# larger safety-only constant) -- both later rejected, see v5 below.
# Bumped 4 -> 5 (D-5 RED-C fix v4, 2026-07-20, THIRD independent
# verification): replaced ALL scan-based cross-chunk continuity with
# DB-driven segment consolidation (`_consolidate_interval_segment`) --
# `kala_gochara_windows` rows now carry a `continuity_state` column
# (migration 461) that v2/v3-era rows never had, and the served
# window_start/window_end for a boundary-touching episode is computed
# entirely differently now (chained via committed neighbors, not a
# same-call re-scan). Any row or `build_substep_progress` entry committed
# under v2/v3/v4-numbered-as-v2 reflects behavior this fix removes -- a
# resumed build must NOT read those old substeps as already-correctly-
# completed. The fingerprint change forces a full replan-all
# (plan_substeps' `fps != {fingerprint}` branch), which deletes ALL of this
# chart's `kala_gochara_windows` rows AND its `build_substep_progress` rows
# before replanning every substep -- so chart 482012f1's already-committed
# major_gain rows are genuinely re-derived under the new consolidation
# logic, not silently skipped as "already built".
# Bumped 5 -> 6 (D-5 native disposition, 2026-07-20, gate_run_2 findings
# 1/2 corrected serving semantics): point-class rows now serve one row per
# LOCAL maximum within an active run (`shape_output._local_maxima`), not a
# single global argmax per run -- an old point-class row committed under
# v5 reflects the collapsed, superseded shape and must not be read as
# already-correctly-completed by a resume.
_RESUME_VERSION = 6


# D-4b materialization-time optimization (native directive, 2026-07-21): the
# scoring span is birth_year -> latest LEL event + a 1-year buffer. Verified
# live against chart 482012f1 (`life_events` table, excluding the
# TEST-FIXTURE synthetic row): latest real event 2026-04-16, birth 1984-02-05
# -> scoring span end year 2027 (year_idx 43). Beyond this, B-1's own event
# set has no LEL anchors to score against -- those years only matter for
# B-6's full-span gate, never for B-1's scoring-span domain-completeness
# assertion (BRIEF_D4B §0's own domain-scoped disposition).
_SCORING_SPAN_END_YEAR = 2027

# All 3 of this chart's currently-populated gochara_resonance_map event
# classes correspond to a categorized LEL specimen in the D4B pre-
# registration packet (§1: career, major_gain/windfall, marriage) -- so
# there is currently no "populated but not pre-registered" class for this
# chart. Kept as an explicit, named set (not "all discovered classes") so a
# FUTURE chart/event_class that IS populated but has no scored LEL category
# correctly falls into the lower-priority tier below, rather than silently
# inheriting priority it hasn't earned.
_PRE_REGISTERED_EVENT_CLASSES = frozenset({"career_advancement", "major_gain", "marriage"})


def _substep_sort_key(
    step: SubStep,
    priority_years: set[tuple[str, int]],
    birth_year: int,
    scoring_span_end_year: int = _SCORING_SPAN_END_YEAR,
    pre_registered_classes: frozenset[str] = _PRE_REGISTERED_EVENT_CLASSES,
) -> tuple[int, str, int]:
    """Dispatch-order sort key for `plan_substeps`' `steps` list -- pulled
    out to a module-level function (not a `plan_substeps`-local closure) so
    it is directly unit-testable without needing a DB connection.

    NUMERIC year tiebreak (D-5 RED-C fix, 2026-07-20): sorting on the raw
    `step.key` STRING here was a real, independent bug -- "…:year:10" sorts
    lexically BEFORE "…:year:9" (string comparison, not numeric), so even
    without specimen-priority promotion this writer's dispatch order was
    never truly ascending-by-year. Every substep-level mechanism in this
    writer must be correct under arbitrary dispatch order regardless (see
    module docstring's DISPATCH ORDER note) -- this fix is still worth
    making on its own, since a closer-to-intended dispatch order is
    strictly better for resumability/observability even though correctness
    no longer depends on it.

    B-1-USEFULNESS PRIORITY (D-4b materialization-time optimization,
    2026-07-21, native directive): pure scheduling, zero change to substep
    semantics/keys/idempotency (resumption still keys off
    `{event_class}:year:{year_idx}`). Four tiers, ascending:
      0 -- named specimen years (existing set: windfall 2010/2011, marriage
           2013) -- unchanged from the D-5 gate fix this extends.
      1 -- remaining SCORING-SPAN years (birth_year..scoring_span_end_year)
           for event_classes IN the pre-registered set -- this is where
           BRIEF_D4B §0's scoring-span domain-completeness assertion lives,
           so B-1 unblocks as soon as this tier alone is done.
      2 -- remaining scoring-span years for event_classes NOT in the
           pre-registered set (currently empty for chart 482012f1; kept
           general for a future chart/class with no scored LEL category).
      3 -- FORWARD-span years (scoring_span_end_year+1..birth_year+99) --
           gates only B-6's full-span disposition, never B-1."""
    ec_part, _, year_part = step.key.rpartition(':year:')
    year_idx = int(year_part)
    if (ec_part, year_idx) in priority_years:
        tier = 0
    else:
        calendar_year = birth_year + year_idx
        in_scoring_span = calendar_year <= scoring_span_end_year
        if in_scoring_span and ec_part in pre_registered_classes:
            tier = 1
        elif in_scoring_span:
            tier = 2
        else:
            tier = 3
    return (tier, ec_part, year_idx)


@register('ka_gochara_sweep')
class KaGocharaSweepWriter(WriterBase):
    """G-4 forward sweep: daily-grid lambda_e(t|chart) over birth->birth+100y,
    shape-aware served rows into `kala_gochara_windows`. HEAVY writer: one
    substep per (populated event_class x year)."""
    asset_id = 'ka_gochara_sweep'
    has_substeps = True

    # ── plan ─────────────────────────────────────────────────────────────

    def plan_substeps(self, ctx) -> list[SubStep]:
        conn = ctx.db_conn
        chart_id = ctx.config['chart_id']
        self._chart_id = chart_id

        try:
            import swisseph as swe
            self._swe = swe
        except Exception as exc:
            logger.error("ka_gochara_sweep: swisseph unavailable, cannot plan: %s", exc)
            self._swe = None
            return []

        self._event_classes = self._discover_event_classes(conn, chart_id)
        self._birth_year = self._derive_birth_year(conn, chart_id)

        if not self._event_classes:
            logger.info("ka_gochara_sweep: no populated gochara_resonance_map event_classes "
                        "for chart %s -- honest empty plan, zero substeps.", chart_id)
            return []
        if self._birth_year is None:
            logger.warning("ka_gochara_sweep: could not derive birth_year for chart %s "
                            "(chart_dashas has no level_n=1 rows) -- honest empty plan.", chart_id)
            return []

        steps: list[SubStep] = []
        for ec in self._event_classes:
            for year_idx in range(_N_YEARS):
                steps.append(SubStep(
                    key=f"{ec}:year:{year_idx}",
                    label=f"{ec} year {year_idx} "
                          f"({self._birth_year + year_idx})",
                ))

        # SPECIMEN-PRIORITY ORDERING (D-5 GATE fix, 2026-07-20): the wave's
        # §G gate demands live reproduction of named LEL specimens
        # (BRIEF_D5 §2) as soon as possible, not after a full chronological
        # sweep from birth_year. A first gate run found the chronological
        # order (career_advancement from ~1950) had committed only 2/300
        # substeps with none of the specimen years reached. This reorders
        # `steps` (stable sort) so calendar years overlapping the named
        # specimens' event_classes are dispatched FIRST -- pure scheduling,
        # zero change to substep semantics/keys/idempotency (resumption
        # still keys off `{event_class}:year:{year_idx}`, unaffected by
        # ordering). Sarvatobhadra (~2025-05) has no populated event_class
        # of its own (G-2's honest finding: no classical vedha-grid data
        # exists live) so it cannot be specimen-prioritized this way --
        # unchanged, already-carried limitation.
        _priority_years: set[tuple[str, int]] = set()
        for _yr in (2010, 2011):   # major_gain windfall interval 2010-07->2011-03
            _priority_years.add(("major_gain", _yr - self._birth_year))
        for _yr in (2013,):        # marriage double-transit specimen 2013-12-11
            _priority_years.add(("marriage", _yr - self._birth_year))

        steps.sort(key=lambda step: _substep_sort_key(step, _priority_years, self._birth_year))

        # ── cross-attempt substep resumption (migration 436, ka_sangam pattern) ──
        self._resume_fingerprint = self._compute_build_fingerprint(chart_id)
        if getattr(ctx, 'dry_run', False):
            return steps

        completed = self._load_completed_substeps(conn, chart_id, self._resume_fingerprint)
        if completed is None:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM kala_gochara_windows WHERE chart_id = %s", (chart_id,))
                cur.execute(
                    "DELETE FROM build_substep_progress WHERE chart_id = %s AND asset_id = 'ka_gochara_sweep'",
                    (chart_id,),
                )
            logger.info("ka_gochara_sweep: fresh/replan build for chart %s -- %d substeps "
                        "(%d event_classes x %d years)", chart_id, len(steps),
                        len(self._event_classes), _N_YEARS)
            return steps

        remaining = [s for s in steps if s.key not in completed]
        logger.info("ka_gochara_sweep: RESUMING build for chart %s -- %d/%d substeps already "
                    "committed, %d remaining", chart_id, len(steps) - len(remaining), len(steps),
                    len(remaining))
        return remaining

    # ── dispatch ─────────────────────────────────────────────────────────

    def run_substep(self, ctx, step: SubStep) -> WriterResult:
        conn = ctx.db_conn
        chart_id = self._chart_id
        dry_run = getattr(ctx, 'dry_run', False)

        event_class, _, year_str = step.key.rpartition(':year:')
        year_idx = int(year_str)

        year_start = date(self._birth_year + year_idx, 1, 1)
        year_end = date(self._birth_year + year_idx + 1, 1, 1)

        # NO per-substep delete here (D-5 RED-C fix, 2026-07-20 -- see module
        # docstring's DISPATCH ORDER note point (1)). Deletion happens
        # exactly ONCE per fresh/replanned build, in `plan_substeps`, before
        # any substep runs -- safe under ANY subsequent dispatch order
        # because nothing deletes again after it. The old "year_idx==0
        # clears this event_class's rows" delete assumed year 0 dispatches
        # first, which is false (specimen-priority reordering, and the
        # since-fixed lexical sort bug), and could silently wipe out
        # sibling years already committed earlier in the SAME build.

        horizon_start_jd = self._swe.julday(year_start.year, year_start.month, year_start.day, 0.0)
        horizon_end_jd = self._swe.julday(year_end.year, year_end.month, year_end.day, 0.0)

        def _keepalive():
            with conn.cursor() as _cur:
                _cur.execute("SELECT 1")

        try:
            rows = sweep_event_class_chunk(
                self._swe, conn, chart_id, event_class,
                horizon_start_jd, horizon_end_jd, step_days=DEFAULT_STEP_DAYS,
            )
        except Exception as exc:
            logger.error("ka_gochara_sweep: sweep failed for %s year %d: %s", event_class, year_idx, exc)
            return WriterResult(asset_id='ka_gochara_sweep', rows_inserted=0,
                                 notes=f"sweep failed for {step.key}: {exc}")

        rows_inserted = 0
        if not dry_run:
            if rows and rows[0].get('temporal_shape') == 'interval':
                # D-5 RED-C fix v4: `rows` here are RAW SEGMENTS (see
                # sweep.sweep_event_class_chunk's docstring), not final
                # served rows -- each one is chained with whatever
                # ALREADY-COMMITTED adjacent segment exists in the DB
                # (never a runtime scan or dispatch-order assumption)
                # before being finalized and inserted.
                final_rows = [
                    self._consolidate_interval_segment(conn, chart_id, event_class, segment)
                    for segment in rows
                ]
                with conn.cursor() as cur:
                    rows_inserted = self._insert_rows(cur, chart_id, final_rows)
            else:
                with conn.cursor() as cur:
                    rows_inserted = self._insert_rows(cur, chart_id, rows)
            self._record_substep(conn, chart_id, step.key, rows_inserted)

        return WriterResult(asset_id='ka_gochara_sweep', rows_inserted=rows_inserted)

    # ── interval segment consolidation (D-5 RED-C fix v4) ──────────────────

    def _consolidate_interval_segment(self, conn, chart_id: str, event_class: str, segment: dict) -> dict:
        """DB-driven, order-independent consolidation: chains `segment`
        (one year-substep's own strictly-bounded raw activation span, from
        `shape_output.build_interval_segments`) with any ALREADY-COMMITTED
        adjacent segment for this (chart_id, event_class), found by EXACT
        calendar-date adjacency on `kala_gochara_windows.continuity_state`
        (migration 461) -- never by a runtime scan or an assumption about
        which substep ran before this one. See sweep.py's module docstring
        for the full mechanism, the order-independence argument, and why it
        has no scan-distance dependency at any episode length.

        A segment can chain a LEFT neighbor AND a RIGHT neighbor in one
        call (a fully-active "middle" year of a longer episode) -- each via
        a single O(1) indexed lookup, never a scan. The consumed neighbor
        row(s) are deleted; ONE new row is inserted for the (possibly
        newly-merged) span (delete-then-reinsert, §N.3).

        ADJACENCY IS SAME-CALENDAR-DAY, NOT OFF-BY-ONE (fixed 2026-07-20,
        found during this fix's own test-authoring, before first commit):
        `writer.run_substep` builds each year's `horizon_start_jd`/
        `horizon_end_jd` back-to-back (year N's `horizon_end_jd` IS year
        N+1's `horizon_start_jd`), and `compute_lambda_e_series` loops
        INCLUSIVELY through its own `t_end_jd` (engine.py, unrelated
        must_not_touch module) -- so the shared boundary day (e.g.
        Jan-1-of-year-N+1) is evaluated by BOTH chunks and can appear as
        BOTH year N's `raw_end` AND year N+1's `raw_start`, as the SAME
        date, not date+1/date-1. An off-by-one adjacent_date (the original
        version of this method) never matches a real year-boundary
        neighbor, so two segments sharing a real episode across a year
        boundary silently never merge -- the exact defect this fix exists
        to remove, just relocated one level down. Neighbor lookup below
        therefore searches on EXACT date equality."""
        raw_start: date = segment["raw_start"]
        raw_end: date = segment["raw_end"]
        left_active = bool(segment["left_active"])
        right_active = bool(segment["right_active"])
        peak_row = segment
        duration_prior = segment.get("duration_prior")

        if left_active:
            neighbor = self._find_adjacent_interval_row(
                conn, chart_id, event_class,
                flag_name="right_active", date_field="raw_end", adjacent_date=raw_start,
            )
            if neighbor is not None:
                raw_start = neighbor["raw_start"]
                left_active = neighbor["left_active"]
                peak_row = self._stronger_peak(peak_row, neighbor)
                self._delete_interval_row(conn, neighbor["id"])

        if right_active:
            neighbor = self._find_adjacent_interval_row(
                conn, chart_id, event_class,
                flag_name="left_active", date_field="raw_start", adjacent_date=raw_end,
            )
            if neighbor is not None:
                raw_end = neighbor["raw_end"]
                right_active = neighbor["right_active"]
                peak_row = self._stronger_peak(peak_row, neighbor)
                self._delete_interval_row(conn, neighbor["id"])

        row = finalize_interval_segment(event_class, raw_start, raw_end, peak_row, duration_prior)
        row["continuity_state"] = {
            "left_active": left_active,
            "right_active": right_active,
            "raw_start": raw_start.isoformat(),
            "raw_end": raw_end.isoformat(),
        }
        return row

    @staticmethod
    def _find_adjacent_interval_row(conn, chart_id: str, event_class: str, *,
                                     flag_name: str, date_field: str, adjacent_date: date) -> Optional[dict]:
        """One indexed lookup for an already-committed neighbor segment --
        `flag_name`/`date_field` are literal column-path names this module
        controls (never user input), safe to interpolate. `FOR UPDATE`
        defensively serializes concurrent consolidation attempts on the
        same neighbor row (belt-and-suspenders; substeps are not expected
        to run truly concurrently against the same event_class today, but
        this makes the query safe regardless)."""
        with conn.cursor() as cur:
            cur.execute(
                f"""SELECT id, continuity_state,
                           signed_intensity, raw_intensity, valence, is_adverse,
                           contributing_systems, suppression_state, calibration_state, source,
                           peak_date, active_sentences, peak_basis
                    FROM kala_gochara_windows
                    WHERE chart_id = %s AND event_class = %s AND temporal_shape = 'interval'
                      AND (continuity_state ->> '{flag_name}')::boolean IS TRUE
                      AND (continuity_state ->> '{date_field}')::date = %s
                    FOR UPDATE""",
                (chart_id, event_class, adjacent_date),
            )
            row = cur.fetchone()
        if not row:
            return None
        if isinstance(row, dict):
            neighbor = dict(row)
        else:
            cols = ["id", "continuity_state", "signed_intensity", "raw_intensity", "valence", "is_adverse",
                    "contributing_systems", "suppression_state", "calibration_state", "source",
                    "peak_date", "active_sentences", "peak_basis"]
            neighbor = dict(zip(cols, row))
        cs = neighbor["continuity_state"]
        cs = cs if isinstance(cs, dict) else _json.loads(cs)
        neighbor["raw_start"] = date.fromisoformat(cs["raw_start"])
        neighbor["raw_end"] = date.fromisoformat(cs["raw_end"])
        neighbor["left_active"] = bool(cs["left_active"])
        neighbor["right_active"] = bool(cs["right_active"])
        for jsonb_field in ("contributing_systems", "suppression_state", "active_sentences"):
            v = neighbor.get(jsonb_field)
            if isinstance(v, str):
                neighbor[jsonb_field] = _json.loads(v)
        return neighbor

    @staticmethod
    def _stronger_peak(a: dict, b: dict) -> dict:
        """Deterministic regardless of merge order/argument position: on an
        EXACT magnitude tie, prefer the earlier `peak_date` -- matching
        `shape_output._peak_of`'s own within-segment tie-break convention
        -- so a chain's final peak never depends on which of two equal-
        strength segments happened to be passed as `a` vs `b` in this
        particular merge call (real lambda_e values essentially never tie
        exactly, but synthetic/degenerate data can, and consolidation must
        be order-independent even then)."""
        a_mag = abs(a.get("raw_intensity") or 0.0)
        b_mag = abs(b.get("raw_intensity") or 0.0)
        if a_mag != b_mag:
            return a if a_mag > b_mag else b
        return a if a["peak_date"] <= b["peak_date"] else b

    @staticmethod
    def _delete_interval_row(conn, row_id) -> None:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM kala_gochara_windows WHERE id = %s", (row_id,))

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _discover_event_classes(conn, chart_id: str) -> list[str]:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT DISTINCT event_class FROM gochara_resonance_map "
                    "WHERE chart_id = %s ORDER BY event_class",
                    (chart_id,),
                )
                return [r[0] if not isinstance(r, dict) else r['event_class'] for r in cur.fetchall()]
        except Exception as exc:
            logger.warning("ka_gochara_sweep: could not discover event_classes for chart %s: %s",
                            chart_id, exc)
            return []

    @staticmethod
    def _derive_birth_year(conn, chart_id: str):
        """Chart-relative birth year, NOT hardcoded to any one native
        (CR-87-class discipline) -- mirrors ka_sangam's own
        `_derive_birth_year` technique exactly (earliest level_n=1 MD start
        in chart_dashas): this is the DASHA-BALANCE start, which can predate
        the literal birth date by up to one full mahadasha (the running
        dasha at birth started before birth) -- the SAME accepted
        approximation `ka_sangam.py`'s lifetime tier already uses for its
        birth_date->birth_date+100y horizon, not a new invention."""
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT MIN(start_date) AS birth_date FROM chart_dashas "
                    "WHERE chart_id = %s AND level_n = 1",
                    (chart_id,),
                )
                row = cur.fetchone()
                if row:
                    bd = row['birth_date'] if isinstance(row, dict) else row[0]
                    if bd:
                        return bd.year
        except Exception as exc:
            logger.warning("ka_gochara_sweep: could not derive birth_year for chart %s: %s", chart_id, exc)
        return None

    def _compute_build_fingerprint(self, chart_id: str) -> str:
        parts = [
            f"v={_RESUME_VERSION}",
            f"chart={chart_id}",
            f"birth_year={self._birth_year}",
            f"event_classes={','.join(sorted(self._event_classes))}",
        ]
        return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()

    def _load_completed_substeps(self, conn, chart_id: str, fingerprint: str):
        with conn.cursor() as cur:
            cur.execute(
                "SELECT substep_key, build_fingerprint FROM build_substep_progress "
                "WHERE chart_id = %s AND asset_id = 'ka_gochara_sweep'",
                (chart_id,),
            )
            rows = cur.fetchall()
        if not rows:
            return None
        fps = {r['build_fingerprint'] if isinstance(r, dict) else r[1] for r in rows}
        if fps != {fingerprint}:
            return None
        return {r['substep_key'] if isinstance(r, dict) else r[0] for r in rows}

    def _record_substep(self, conn, chart_id: str, substep_key: str, rows: int) -> None:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO build_substep_progress
                       (chart_id, asset_id, substep_key, build_fingerprint, rows_written, completed_at)
                   VALUES (%s, 'ka_gochara_sweep', %s, %s, %s, now())
                   ON CONFLICT (chart_id, asset_id, substep_key)
                   DO UPDATE SET build_fingerprint = EXCLUDED.build_fingerprint,
                                 rows_written      = EXCLUDED.rows_written,
                                 completed_at      = EXCLUDED.completed_at""",
                (chart_id, substep_key, self._resume_fingerprint, rows),
            )

    @staticmethod
    def _insert_rows(cur, chart_id: str, rows: list[dict]) -> int:
        def _json_default(o):
            # Some upstream detail dicts (dasha periods, permission_detail
            # 'systems' entries) carry raw date/datetime objects from DB
            # driver rows rather than pre-serialized ISO strings -- honest
            # str() fallback so a served JSONB column never silently drops
            # a field, matching this codebase's "never drop data" discipline.
            import datetime as _dt
            if isinstance(o, (_dt.date, _dt.datetime)):
                return o.isoformat()
            return str(o)

        def _dumps(v):
            return _json.dumps(v, default=_json_default)

        n = 0
        for row in rows:
            # `continuity_state` (migration 461, D-5 RED-C fix v4): interval-
            # shape-only, NULL for point/chain rows (`row.get(...)` is None
            # for those -- see shape_output's point/chain builders, which
            # never set this key).
            continuity_state = row.get('continuity_state')
            cur.execute(
                """
                INSERT INTO kala_gochara_windows (
                    chart_id, event_class, temporal_shape,
                    window_start, window_end, peak_date,
                    milestone_id, is_irreversibility_milestone,
                    signed_intensity, raw_intensity, valence, is_adverse,
                    active_sentences, contributing_systems, suppression_state,
                    peak_basis, calibration_state, source, continuity_state
                ) VALUES (
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s,
                    %s, %s, %s, %s,
                    %s::jsonb, %s::jsonb, %s::jsonb,
                    %s, %s, %s, %s::jsonb
                )
                ON CONFLICT (chart_id, event_class, window_start, peak_date, COALESCE(milestone_id, ''))
                DO UPDATE SET
                    window_end = EXCLUDED.window_end,
                    signed_intensity = EXCLUDED.signed_intensity,
                    raw_intensity = EXCLUDED.raw_intensity,
                    active_sentences = EXCLUDED.active_sentences,
                    contributing_systems = EXCLUDED.contributing_systems,
                    suppression_state = EXCLUDED.suppression_state,
                    continuity_state = EXCLUDED.continuity_state,
                    computed_at = now()
                """,
                (
                    chart_id, row['event_class'], row['temporal_shape'],
                    row['window_start'], row['window_end'], row['peak_date'],
                    row.get('milestone_id'), row.get('is_irreversibility_milestone', False),
                    row['signed_intensity'], row['raw_intensity'], row['valence'], row['is_adverse'],
                    _dumps(row.get('active_sentences', [])),
                    _dumps(row.get('contributing_systems', [])),
                    _dumps(row.get('suppression_state', {})),
                    row.get('peak_basis', 'gochara_lambda_e_v1'),
                    row.get('calibration_state', 'structural_prior'),
                    row.get('source', 'live'),
                    _dumps(continuity_state) if continuity_state is not None else None,
                ),
            )
            n += 1
        return n


__all__ = ["KaGocharaSweepWriter"]
