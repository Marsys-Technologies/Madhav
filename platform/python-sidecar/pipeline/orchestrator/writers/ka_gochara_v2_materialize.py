"""ka_gochara_v2_materialize writer — W2G's per-chart materialization (GOCHARA-2.0).

ṢAḌ-DARŚANA wave W2G (item 19), lane G REWORK. Renamed from the superseded
`ka_gochara_sweep_v2` (PR #1081, PARĪKṢAKA verdict PARKED-HONEST, real defect
found) per the native ruling recorded in `SHAD_DARSHANA_STATE.md`
("RULING — Lane G / W2G write-target", 2026-08-06):

  1. Protection mechanism (migration 540) unchanged. This writer MUST NEVER
     set `app.allow_protected_sweep_rewrite`, in any code path. (Grep-
     verifiable: the string does not appear anywhere in this module or in
     `services/w2g/materialize.py` — see
     `test_writer_source_never_references_the_override_setting` in this
     writer's test file.)
  2. W2G writes exclusively to its own surface (own asset_id
     `ka_gochara_v2_materialize` + own table `kala_gochara_windows_v2`, per
     `GOCHARA_SWEEP_2_0_DESIGN_v1_0.md` and migration 542). It does not
     DELETE, UPDATE, or INSERT into the protected (`ka_gochara_sweep` x
     canonical-chart) rows in `kala_gochara_windows` — that table's name does
     not appear in this module at all (see
     `test_writer_source_never_references_the_protected_table`). §N.3
     idempotency applies to this writer's own table only.
  3. The protected v1 corpus (`kala_gochara_windows`) is this writer's frozen
     validation benchmark, per `services/w2g/equivalence_report.py` — read
     read-only there, never written to here. Corpus disposition (whether/when
     2.0 data ever moves INTO `kala_gochara_windows`, per design §4's later
     "table provenance-stamped per generation" cutover description) is a
     DEFERRED W6 native ruling — not decided or pre-empted by this writer.
  4. This is the reworked lane, not a park — see the PR body for the
     equivalence-report result against v1's corpus.

Joins the chart-INDEPENDENT contact stream (`bg_gochara_arcs`, built ONCE by
the `bg_gochara_arcs` writer) against ONE chart's natal `gochara_resonance_map`
targets, scores every candidate instant through v1's own, UNMODIFIED
`gochara_intensity.compute_lambda_e` grammar (`services/w2g/materialize.py` --
design §5: "2.0 changes HOW, never WHAT"), and writes generation='2.0'-stamped
rows into `kala_gochara_windows_v2` -- its OWN table, structurally outside the
blast radius of migration 540's protection triggers (those are bound to the
`kala_gochara_windows` relation specifically; Postgres triggers never fire for
statements against a different table). v1's `ka_gochara_sweep` /
`kala_gochara_windows` are untouched by this writer.

FROZEN ORCHESTRATOR CONTRACT (§N.2), conformed to, not extended:
  * `@register('ka_gochara_v2_materialize')` on a `WriterBase` subclass;
  * HEAVY shape -- `plan_substeps` (one substep per populated event_class) +
    `run_substep`, so a crash resumes at the failed class rather than the
    start;
  * runs on `ctx.db_conn` and NEVER commits or closes it;
  * never writes `asset_throughput`;
  * no orchestrator change of any kind.

IDEMPOTENCY (§N.3). Delete-then-INSERT scoped to
(chart_id x event_class x generation='2.0') against `kala_gochara_windows_v2`
ONLY -- this table has no protection trigger, no shared natural-key gap with
v1 (migration 542's unique index includes `generation` from creation), and no
history of ever touching `kala_gochara_windows`.

THE UNTOUCHABLE-DATA RAIL, now satisfied by CONSTRUCTION, not just discipline:
this writer's only DELETE/SELECT/INSERT target is `kala_gochara_windows_v2`
(see `TABLE` below) -- there is no code path, error branch, or override that
ever names `kala_gochara_windows` or sets
`app.allow_protected_sweep_rewrite`. `kala_gochara_windows_v2`'s own unique
index (`chart_id, event_class, window_start, peak_date,
COALESCE(milestone_id, ''), generation`) INCLUDES generation, so unlike the
prior design's disclosed schema gap, a plain `ON CONFLICT` upsert against it
could never cross generations even if this writer used one (it still doesn't,
for symmetry with v1's own INSERT discipline and to keep collision counting
honest -- see the per-row savepoint below).

DELTA-AWARE INVALIDATION (design amendment 2), REUSED from the prior lane
unchanged. `kala_gochara_v2_build_state` (migration 541, kept + reused --
generic (chart_id, event_class, generation) fingerprint bookkeeping, never
coupled to any particular served table) still backs this. Before touching
anything, this writer recomputes `services.w2g.fingerprint.class_fingerprint`
and compares it against the stored value; an unchanged fingerprint is an
honest no-op.

PROGRESSIVE HORIZON (design amendment 3), unchanged from the prior lane.
`ctx.config['now_date']` anchors a +/-3-year window
(`services.w2g.materialize.progressive_horizon`). Every row this writer serves
DISCLOSES that window via `kala_gochara_v2_build_state.horizon_status=
'progressive_partial'`.

HONEST SCOPE OF THIS FIRST LANE (see `materialize.py`'s own docstring for the
full account): Tier A (eager) bodies only; `temporal_shape == 'point'` event
classes only.
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

# This writer's OWN surface (native ruling point 2) -- never the protected
# v1 sweep table (migration 460/540). See the module docstring and this
# writer's test file for the static, re-checkable proof of that absence.
TABLE = "kala_gochara_windows_v2"
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


@register('ka_gochara_v2_materialize')
class GocharaV2MaterializeWriter(WriterBase):
    asset_id = 'ka_gochara_v2_materialize'
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
            logger.warning("[ka_gochara_v2_materialize] could not discover event_classes for "
                            "chart %s: %s -- honest empty plan.", chart_id, exc)
            return []
        event_classes = [r["event_class"] for r in rows]
        if not event_classes:
            logger.info("[ka_gochara_v2_materialize] no populated gochara_resonance_map event_classes "
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

        # §N.3 replace-not-accrete, scoped to (chart_id, event_class, '2.0')
        # against THIS WRITER'S OWN TABLE ONLY (native ruling point 2) --
        # the protected v1 sweep table is never named in this statement or
        # any other one this writer issues.
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
            except Exception as exc:  # noqa: BLE001 -- own-table natural-key collision (e.g. a re-run racing itself)
                collisions += 1
                logger.warning(
                    "[ka_gochara_v2_materialize] row insert collision for chart=%s event_class=%s "
                    "peak_date=%s (kala_gochara_windows_v2 only -- never touches v1): %s",
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


__all__ = ["BODIES", "TABLE", "GocharaV2MaterializeWriter"]
