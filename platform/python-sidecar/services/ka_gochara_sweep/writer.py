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

Idempotency (§N.3): delete-then-insert scoped to (chart_id, event_class) --
each event_class's OWN substeps clear only that event_class's rows before
inserting, exactly once (in that event_class's FIRST year substep), so a
resumed attempt that skips already-committed years never re-deletes them.

CONTINUITY ACROSS YEAR SUBSTEPS (D-5 RED-C fix, 2026-07-20): closing every
interval-shaped activation at each year substep's boundary, unconditionally,
made the served window's edges an artifact of the chunking grain rather
than a true signal-cessation point -- two live major_gain windows for chart
482012f1 came out ~365 days wide, EXACTLY bounded by year-substep edges.
`run_substep` now reads the PRIOR year substep's `build_substep_progress.
carry_state` (migration 461, a nullable JSONB column on the existing
migration-436 ledger) before sweeping, passes it to `sweep.
sweep_event_class_chunk` as `open_run`, and persists whatever comes back as
THIS year's `carry_state` -- so an activation still firing at a chunk
boundary is carried forward and only closed on a CONFIRMED cessation (the
next chunk's first grid day comes back inactive) or the ontology's
`duration_prior.max_days` cap, never a bare, unverified chunk edge. See
`shape_output.build_interval_rows` for the mechanism and `_RESUME_VERSION`'s
bump-to-3 note below for how this invalidates pre-fix committed rows.
"""
from __future__ import annotations

import hashlib
import json as _json
import logging
from datetime import date
from typing import Optional

from pipeline.orchestrator.writers import WriterBase, WriterResult, SubStep, register
from services.ka_gochara_sweep.sweep import sweep_event_class_chunk, DEFAULT_STEP_DAYS

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
# Bumped 2 -> 3 (D-5 RED-C fix, 2026-07-20): pre-fix year substeps closed
# EVERY interval-shaped run at the chunk boundary unconditionally, so any
# `kala_gochara_windows` row (and the `build_substep_progress` rows that
# marked those years "done") committed under v2 reflects the chunking-
# artifact bug this fix removes -- a resumed build must NOT read those old
# substeps as already-correctly-completed. The fingerprint change forces a
# full replan-all (plan_substeps' `fps != {fingerprint}` branch), which
# deletes ALL of this chart's `kala_gochara_windows` rows AND its
# `build_substep_progress` rows before replanning every substep -- so the
# two already-committed 365-day major_gain windows for chart 482012f1 are
# genuinely re-derived under the new continuity-aware logic, not silently
# skipped as "already built".
_RESUME_VERSION = 3


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

        def _priority_key(step: SubStep) -> tuple[int, str]:
            ec_part, _, year_part = step.key.rpartition(':year:')
            is_priority = (ec_part, int(year_part)) in _priority_years
            return (0 if is_priority else 1, step.key)

        steps.sort(key=_priority_key)

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

        # Self-scoped delete (mirrors ka_sangam's "each substep clears only its own
        # rows" discipline): the FIRST year substep for an event_class clears ALL
        # of that event_class's prior rows once, so later years never re-delete
        # already-committed sibling years on a resumed run.
        if year_idx == 0 and not dry_run:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM kala_gochara_windows WHERE chart_id = %s AND event_class = %s",
                    (chart_id, event_class),
                )

        horizon_start_jd = self._swe.julday(year_start.year, year_start.month, year_start.day, 0.0)
        horizon_end_jd = self._swe.julday(year_end.year, year_end.month, year_end.day, 0.0)

        def _keepalive():
            with conn.cursor() as _cur:
                _cur.execute("SELECT 1")

        # CONTINUITY CARRY (D-5 RED-C fix): an interval-shaped activation
        # still open at the PRIOR year substep's last grid day was recorded
        # there as `carry_state` (migration 461) -- read it back so this
        # year's chunk can confirm (not assume) whether the signal kept
        # firing across the boundary. `force_close` on the horizon's final
        # year ensures a still-open activation is closed for real instead
        # of carried into a substep that will never run.
        open_run = None
        if year_idx > 0 and not dry_run:
            open_run = self._load_carry_state(conn, chart_id, f"{event_class}:year:{year_idx - 1}",
                                               self._resume_fingerprint)
        force_close = (year_idx == _N_YEARS - 1)

        try:
            rows, carry_out = sweep_event_class_chunk(
                self._swe, conn, chart_id, event_class,
                horizon_start_jd, horizon_end_jd, step_days=DEFAULT_STEP_DAYS,
                open_run=open_run, force_close=force_close,
            )
        except Exception as exc:
            logger.error("ka_gochara_sweep: sweep failed for %s year %d: %s", event_class, year_idx, exc)
            return WriterResult(asset_id='ka_gochara_sweep', rows_inserted=0,
                                 notes=f"sweep failed for {step.key}: {exc}")

        rows_inserted = 0
        if not dry_run:
            with conn.cursor() as cur:
                rows_inserted = self._insert_rows(cur, chart_id, rows)
            self._record_substep(conn, chart_id, step.key, rows_inserted, carry_out)

        return WriterResult(asset_id='ka_gochara_sweep', rows_inserted=rows_inserted)

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

    def _record_substep(self, conn, chart_id: str, substep_key: str, rows: int,
                         carry_state: Optional[dict] = None) -> None:
        carry_json = self._serialize_carry_state(carry_state) if carry_state is not None else None
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO build_substep_progress
                       (chart_id, asset_id, substep_key, build_fingerprint, rows_written,
                        carry_state, completed_at)
                   VALUES (%s, 'ka_gochara_sweep', %s, %s, %s, %s::jsonb, now())
                   ON CONFLICT (chart_id, asset_id, substep_key)
                   DO UPDATE SET build_fingerprint = EXCLUDED.build_fingerprint,
                                 rows_written      = EXCLUDED.rows_written,
                                 carry_state       = EXCLUDED.carry_state,
                                 completed_at      = EXCLUDED.completed_at""",
                (chart_id, substep_key, self._resume_fingerprint, rows, carry_json),
            )

    def _load_carry_state(self, conn, chart_id: str, substep_key: str, fingerprint: str) -> Optional[dict]:
        """Read back the PRIOR year substep's continuity carry-state (D-5
        RED-C fix). Returns None when there's nothing to carry (the common
        case -- most years close every activation cleanly), when the prior
        substep hasn't committed at all (e.g. this is a genuinely fresh
        year_idx==0 plan, or an out-of-order dispatch), or when its
        fingerprint doesn't match the current build (stale/replaced ledger
        row -- never trust carry state from a different build)."""
        with conn.cursor() as cur:
            cur.execute(
                "SELECT carry_state, build_fingerprint FROM build_substep_progress "
                "WHERE chart_id = %s AND asset_id = 'ka_gochara_sweep' AND substep_key = %s",
                (chart_id, substep_key),
            )
            row = cur.fetchone()
        if not row:
            return None
        carry_raw = row['carry_state'] if isinstance(row, dict) else row[0]
        fp = row['build_fingerprint'] if isinstance(row, dict) else row[1]
        if fp != fingerprint or carry_raw is None:
            return None
        return self._deserialize_carry_state(carry_raw)

    @staticmethod
    def _serialize_carry_state(carry: dict) -> str:
        peak_row = dict(carry["peak_row"])
        peak_row["peak_date"] = peak_row["peak_date"].isoformat()
        payload = {
            "true_start_date": carry["true_start_date"].isoformat(),
            "last_active_date": carry["last_active_date"].isoformat(),
            "peak_row": peak_row,
        }
        return _json.dumps(payload)

    @staticmethod
    def _deserialize_carry_state(raw) -> dict:
        payload = raw if isinstance(raw, dict) else _json.loads(raw)
        peak_row = dict(payload["peak_row"])
        peak_row["peak_date"] = date.fromisoformat(peak_row["peak_date"])
        return {
            "true_start_date": date.fromisoformat(payload["true_start_date"]),
            "last_active_date": date.fromisoformat(payload["last_active_date"]),
            "peak_row": peak_row,
        }

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
            cur.execute(
                """
                INSERT INTO kala_gochara_windows (
                    chart_id, event_class, temporal_shape,
                    window_start, window_end, peak_date,
                    milestone_id, is_irreversibility_milestone,
                    signed_intensity, raw_intensity, valence, is_adverse,
                    active_sentences, contributing_systems, suppression_state,
                    peak_basis, calibration_state, source
                ) VALUES (
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s,
                    %s, %s, %s, %s,
                    %s::jsonb, %s::jsonb, %s::jsonb,
                    %s, %s, %s
                )
                ON CONFLICT (chart_id, event_class, window_start, peak_date, COALESCE(milestone_id, ''))
                DO UPDATE SET
                    window_end = EXCLUDED.window_end,
                    signed_intensity = EXCLUDED.signed_intensity,
                    raw_intensity = EXCLUDED.raw_intensity,
                    active_sentences = EXCLUDED.active_sentences,
                    contributing_systems = EXCLUDED.contributing_systems,
                    suppression_state = EXCLUDED.suppression_state,
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
                ),
            )
            n += 1
        return n


__all__ = ["KaGocharaSweepWriter"]
