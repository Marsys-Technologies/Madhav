"""ka_gochara_sweep_v2 writer — W2G's per-chart materialization (GOCHARA-2.0).

ṢAḌ-DARŚANA wave W2G (item 19), lane G. Joins the chart-INDEPENDENT contact
stream (`bg_gochara_arcs`, built ONCE by the `bg_gochara_arcs` writer) against
ONE chart's natal `gochara_resonance_map` targets, scores every candidate
instant through v1's own, UNMODIFIED `gochara_intensity.compute_lambda_e`
grammar (`services/w2g/materialize.py` -- design §5: "2.0 changes HOW, never
WHAT"), and writes generation='2.0'-stamped rows into `kala_gochara_windows`
BESIDE v1's rows (ADJUDICATION-6). v1's `ka_gochara_sweep` is untouched by
this writer and stays authoritative -- see PR body for the strangler-fig
disposition; no authority flip is authorized here.

FROZEN ORCHESTRATOR CONTRACT (§N.2), conformed to, not extended:
  * `@register('ka_gochara_sweep_v2')` on a `WriterBase` subclass;
  * HEAVY shape -- `plan_substeps` (one substep per populated event_class) +
    `run_substep`, so a crash resumes at the failed class rather than the
    start (v1's own per-year sub-chunking is not needed here: 2.0 evaluates
    a handful of arc-solved candidate instants per class, not a ~36,500-day
    grid, so one class fits comfortably in one substep -- see the module's
    real measured timing in the PR body);
  * runs on `ctx.db_conn` and NEVER commits or closes it;
  * never writes `asset_throughput`;
  * no orchestrator change of any kind.

IDEMPOTENCY (§N.3). Delete-then-INSERT scoped to
(chart_id x event_class x generation='2.0') -- exactly the sub-step's own
key plus the fixed 2.0 stamp, so a re-run never touches v1's rows (different
`generation` value, never selected by this writer's own DELETE) and never
strands a stale row from a previous 2.0 build of the SAME class.

THE UNTOUCHABLE-DATA RAIL, defended THREE ways, not just asserted:
  1. every DELETE/SELECT this writer issues against `kala_gochara_windows`
     is generation-scoped to '2.0';
  2. INSERTs never use `ON CONFLICT ... DO UPDATE` against the table's
     existing natural-key index (`chart_id, event_class, window_start,
     peak_date, COALESCE(milestone_id, '')`) -- that index predates the
     `generation` column (migration 527) and does NOT include it, so a plain
     upsert on that arbiter could silently overwrite a v1 row if a 2.0
     candidate ever landed on the exact same natural key. Disclosed, real
     schema gap (see PR body) -- NOT fixed in this lane (altering the shared
     table's constraints is exactly the kind of change to the protected
     surface this lane was told to avoid without a dedicated ruling);
  3. each row is inserted inside its OWN `savepoint_scope` (the same
     connection-hygiene helper v1's `gochara_intensity` package already
     uses). A real unique-constraint collision against an existing v1 row
     therefore ROLLS BACK ONLY THAT ONE ROW's savepoint and is counted +
     logged as `collisions_skipped` -- never silently overwritten, never
     poisoning the rest of the substep's own SAVEPOINT.

DELTA-AWARE INVALIDATION (design amendment 2). Before touching anything,
this writer recomputes `services.w2g.fingerprint.class_fingerprint` for
(event_class, GRAMMAR_VERSION, this chart's target_refs, the eager-tier
bodies, their CURRENT `bg_gochara_arcs` fingerprints) and compares it against
`kala_gochara_v2_build_state`'s stored value (migration 541). An unchanged
fingerprint is an honest no-op -- the exact incident
`services/w2g/fingerprint.py`'s own docstring records (v1's single whole-
build fingerprint forcing a ~606-substep replan for a one-class grammar
edit) is structurally impossible here.

PROGRESSIVE HORIZON (design amendment 3). `ctx.config['now_date']` (an
injectable ISO date string, defaulting to the real `date.today()` in
production -- injectable so a test/replay never depends on wall-clock time)
anchors a ±3-year window (`services.w2g.materialize.progressive_horizon`).
Every row this writer serves DISCLOSES that window via
`kala_gochara_v2_build_state.horizon_status='progressive_partial'` -- the
full-century backfill is a future lane's job, not silently claimed here.

HONEST SCOPE OF THIS FIRST LANE (see `materialize.py`'s own docstring for
the full account): Tier A (eager) bodies only; `temporal_shape == 'point'`
event classes only.
"""
from __future__ import annotations

import logging
import time
from datetime import date
from typing import Any

from pipeline.orchestrator.writers import (
    ContextSpec,
    SubStep,
    WriterBase,
    WriterResult,
    register,
)
from services.gochara_grammar import resonance_map as RM
from services.gochara_intensity._dbutil import savepoint_scope
from services.w2g.db_source import DbArcSource
from services.w2g.fingerprint import ARC_ENGINE_VERSION, class_fingerprint
from services.w2g.materialize import (
    GENERATION_V2,
    GRAMMAR_VERSION,
    materialize_event_class,
    progressive_horizon,
)
from services.w2g.tiers import eager_bodies
from pipeline.orchestrator.writers.bg_gochara_arcs import SUBSTRATE_VERSION

logger = logging.getLogger(__name__)

TABLE = "kala_gochara_windows"
BUILD_STATE_TABLE = "kala_gochara_v2_build_state"
BODIES = eager_bodies()  # Tier A only, this lane -- see module docstring

INSERT_SQL = f"""
    INSERT INTO {TABLE}
      (chart_id, event_class, temporal_shape,
       window_start, window_end, peak_date,
       milestone_id, is_irreversibility_milestone,
       signed_intensity, raw_intensity, valence, is_adverse,
       active_sentences, contributing_systems, suppression_state,
       peak_basis, calibration_state, source, generation)
    VALUES
      (%(chart_id)s, %(event_class)s, %(temporal_shape)s,
       %(window_start)s, %(window_end)s, %(peak_date)s,
       %(milestone_id)s, %(is_irreversibility_milestone)s,
       %(signed_intensity)s, %(raw_intensity)s, %(valence)s, %(is_adverse)s,
       %(active_sentences)s::jsonb, %(contributing_systems)s::jsonb, %(suppression_state)s::jsonb,
       %(peak_basis)s, %(calibration_state)s, %(source)s, %(generation)s)
"""


def _query_fn(conn):
    def query(sql: str, params: list[Any] | None = None) -> list[dict[str, Any]]:
        cur = conn.execute(sql, params or [])
        rows = cur.fetchall()
        return [dict(r) if not isinstance(r, dict) else r for r in rows]
    return query


def _json_default(o: Any) -> Any:
    import datetime as _dt
    if isinstance(o, (_dt.date, _dt.datetime)):
        return o.isoformat()
    return str(o)


def _dumps(v: Any) -> str:
    import json as _json
    return _json.dumps(v, default=_json_default)


@register('ka_gochara_sweep_v2')
class GocharaSweepV2Writer(WriterBase):
    asset_id = 'ka_gochara_sweep_v2'
    has_substeps = True

    # ── FROZEN CONTRACT: plan_substeps + run_substep ─────────────────────────

    def plan_substeps(self, ctx: ContextSpec) -> list[SubStep]:
        chart_id = ctx.config['chart_id']
        query = _query_fn(ctx.db_conn)
        try:
            rows = query(
                "SELECT DISTINCT event_class FROM gochara_resonance_map "
                "WHERE chart_id = %s ORDER BY event_class",
                [chart_id],
            )
        except Exception as exc:
            logger.warning("[ka_gochara_sweep_v2] could not discover event_classes for "
                            "chart %s: %s -- honest empty plan.", chart_id, exc)
            return []
        event_classes = [r["event_class"] for r in rows]
        if not event_classes:
            logger.info("[ka_gochara_sweep_v2] no populated gochara_resonance_map event_classes "
                        "for chart %s -- honest empty plan, zero substeps.", chart_id)
        return [SubStep(key=ec, label=f"W2G materialize: {ec}") for ec in event_classes]

    def run_substep(self, ctx: ContextSpec, step: SubStep) -> WriterResult:
        t0 = time.time()
        chart_id = ctx.config['chart_id']
        event_class = step.key
        conn = ctx.db_conn

        try:
            import swisseph as swe
        except Exception as exc:
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                 notes=f"swisseph unavailable: {exc}")

        now_date_str = ctx.config.get('now_date')
        now_date = date.fromisoformat(now_date_str) if now_date_str else date.today()
        horizon = progressive_horizon(now_date)
        horizon_start_jd = swe.julday(horizon.start_date.year, horizon.start_date.month,
                                       horizon.start_date.day, 0.0)
        horizon_end_jd = swe.julday(horizon.end_date.year, horizon.end_date.month,
                                     horizon.end_date.day, 0.0)

        query = _query_fn(conn)

        with savepoint_scope(conn, "w2g_v2_targets"):
            raw_targets = RM.fetch_resonance_targets(conn, chart_id, event_class)

        if not raw_targets:
            self._upsert_build_state(
                conn, chart_id, event_class, class_fp=None, horizon=horizon,
                contacts_evaluated=0, rows_written=0,
                skipped_reason="no gochara_resonance_map targets for this chart/event_class",
                build_id=ctx.build_id,
            )
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                 duration_seconds=time.time() - t0,
                                 notes=f"{event_class}: honest empty -- no resonance targets")

        # ── delta-aware invalidation (design amendment 2) ────────────────────
        arc_fps = self._fetch_arc_fingerprints(query)
        target_refs = [t.target_ref for t in raw_targets]
        fp = class_fingerprint(event_class, GRAMMAR_VERSION, target_refs, BODIES, arc_fps)

        stored_fp = self._stored_fingerprint(query, chart_id, event_class)
        if stored_fp is not None and stored_fp == fp and not ctx.dry_run:
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=0, duration_seconds=time.time() - t0,
                notes=f"{event_class}: unchanged class_fingerprint ({fp}) -- delta-aware "
                      f"invalidation skip, no recompute, no rewrite",
            )

        arc_source = DbArcSource(query, SUBSTRATE_VERSION)

        result = materialize_event_class(
            swe, conn, chart_id, event_class, arc_source,
            horizon_start_jd, horizon_end_jd, bodies=BODIES,
            fetch_resonance_targets=lambda *a, **k: raw_targets,
        )

        if ctx.dry_run:
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=0, rows_skipped=len(result.rows),
                duration_seconds=time.time() - t0,
                notes=f"DRY RUN {event_class}: {result.contacts_evaluated} candidates, "
                      f"{len(result.rows)} would be served -- nothing written",
            )

        if result.skipped_reason is not None:
            self._upsert_build_state(
                conn, chart_id, event_class, class_fp=fp, horizon=horizon,
                contacts_evaluated=result.contacts_evaluated, rows_written=0,
                skipped_reason=result.skipped_reason, build_id=ctx.build_id,
            )
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                 duration_seconds=time.time() - t0,
                                 notes=f"{event_class}: {result.skipped_reason}")

        # §N.3 replace-not-accrete, scoped to (chart_id, event_class, '2.0') --
        # NEVER touches a v1-generation row (see module docstring point 1).
        with conn.cursor() as cur:
            cur.execute(
                f"DELETE FROM {TABLE} WHERE chart_id = %s AND event_class = %s AND generation = %s",
                [chart_id, event_class, GENERATION_V2],
            )

        inserted = 0
        collisions = 0
        for row in result.rows:
            params = {
                "chart_id": chart_id,
                "event_class": row["event_class"],
                "temporal_shape": row["temporal_shape"],
                "window_start": row["window_start"],
                "window_end": row["window_end"],
                "peak_date": row["peak_date"],
                "milestone_id": row["milestone_id"],
                "is_irreversibility_milestone": row["is_irreversibility_milestone"],
                "signed_intensity": row["signed_intensity"],
                "raw_intensity": row["raw_intensity"],
                "valence": row["valence"],
                "is_adverse": row["is_adverse"],
                "active_sentences": _dumps(row["active_sentences"]),
                "contributing_systems": _dumps(row["contributing_systems"]),
                "suppression_state": _dumps(row["suppression_state"]),
                "peak_basis": row["peak_basis"],
                "calibration_state": row["calibration_state"],
                "source": row["source"],
                "generation": GENERATION_V2,
            }
            try:
                with savepoint_scope(conn, "w2g_v2_row_insert"):
                    conn.execute(INSERT_SQL, params)
                inserted += 1
            except Exception as exc:  # noqa: BLE001 -- see point 3, module docstring
                collisions += 1
                logger.warning(
                    "[ka_gochara_sweep_v2] row insert collision for chart=%s event_class=%s "
                    "peak_date=%s -- skipped, v1 row (if any) left untouched: %s",
                    chart_id, event_class, row["peak_date"], exc,
                )

        self._upsert_build_state(
            conn, chart_id, event_class, class_fp=fp, horizon=horizon,
            contacts_evaluated=result.contacts_evaluated, rows_written=inserted,
            skipped_reason=None, build_id=ctx.build_id,
        )

        notes = (
            f"{event_class}: {result.contacts_evaluated} candidates evaluated, "
            f"{inserted} served, {collisions} collision(s) skipped, "
            f"horizon={horizon.start_date}..{horizon.end_date} ({horizon.status})"
        )
        return WriterResult(asset_id=self.asset_id, rows_inserted=inserted,
                             duration_seconds=time.time() - t0, notes=notes)

    def run(self, ctx: ContextSpec) -> WriterResult:
        """CLI / direct-use path: drive this writer's own substeps."""
        t0 = time.time()
        total = 0
        notes: list[str] = []
        for step in self.plan_substeps(ctx):
            result = self.run_substep(ctx, step)
            total += result.rows_inserted
            notes.append(result.notes)
        return WriterResult(asset_id=self.asset_id, rows_inserted=total,
                             duration_seconds=time.time() - t0, notes=" | ".join(notes))

    # ── helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _fetch_arc_fingerprints(query) -> dict[str, str]:
        rows = query(
            f"SELECT DISTINCT body, arc_fingerprint FROM bg_gochara_arcs "
            f"WHERE substrate_version = %s AND body = ANY(%s)",
            [SUBSTRATE_VERSION, list(BODIES)],
        )
        return {r["body"]: r["arc_fingerprint"] for r in rows}

    @staticmethod
    def _stored_fingerprint(query, chart_id: str, event_class: str) -> str | None:
        rows = query(
            f"SELECT class_fingerprint FROM {BUILD_STATE_TABLE} "
            f"WHERE chart_id = %s AND event_class = %s AND generation = %s",
            [chart_id, event_class, GENERATION_V2],
        )
        return rows[0]["class_fingerprint"] if rows else None

    @staticmethod
    def _upsert_build_state(conn, chart_id: str, event_class: str, *, class_fp: str | None,
                             horizon, contacts_evaluated: int, rows_written: int,
                             skipped_reason: str | None, build_id: str) -> None:
        if class_fp is None:
            # Nothing to fingerprint (no targets at all) -- record the honest
            # skip without a fabricated fingerprint value.
            return
        conn.execute(
            f"""
            INSERT INTO {BUILD_STATE_TABLE}
              (chart_id, event_class, generation, class_fingerprint, grammar_version,
               arc_engine_version, bodies_scope, horizon_start_date, horizon_end_date,
               horizon_status, contacts_evaluated, rows_written, skipped_reason, build_id, computed_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now())
            ON CONFLICT (chart_id, event_class, generation) DO UPDATE SET
              class_fingerprint = EXCLUDED.class_fingerprint,
              grammar_version = EXCLUDED.grammar_version,
              arc_engine_version = EXCLUDED.arc_engine_version,
              bodies_scope = EXCLUDED.bodies_scope,
              horizon_start_date = EXCLUDED.horizon_start_date,
              horizon_end_date = EXCLUDED.horizon_end_date,
              horizon_status = EXCLUDED.horizon_status,
              contacts_evaluated = EXCLUDED.contacts_evaluated,
              rows_written = EXCLUDED.rows_written,
              skipped_reason = EXCLUDED.skipped_reason,
              build_id = EXCLUDED.build_id,
              computed_at = now()
            """,
            [chart_id, event_class, GENERATION_V2, class_fp, GRAMMAR_VERSION,
             ARC_ENGINE_VERSION, list(BODIES), horizon.start_date, horizon.end_date,
             horizon.status, contacts_evaluated, rows_written, skipped_reason, build_id],
        )


__all__ = ["BODIES", "GocharaSweepV2Writer"]
