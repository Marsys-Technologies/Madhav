"""
services/ka_kshetra/writer.py — the `ka_kshetra` HEAVY WriterBase subclass.

FROZEN ORCHESTRATOR CONTRACT (CLAUDE.md §N.2 / ORCHESTRATOR_CONVERGENCE_CLOSE §2,
restated by KALA_W2_FIELD_DESIGN §1 rail 3):
  • `@register('ka_kshetra')` → `WriterBase` subclass (the decorator fires from
    the shim `pipeline/orchestrator/writers/ka_kshetra.py`);
  • HEAVY writer: `plan_substeps(ctx)` + `run_substep(ctx, step)`;
  • runs on `ctx.db_conn` and NEVER commits, rolls back, or closes it — the
    orchestrator owns the transaction and the per-substep savepoint;
  • NEVER writes `asset_throughput` — the orchestrator is the sole build-state
    writer;
  • gets `chart_id` + `birth_params` from `ctx.config`.
Nothing in this file changes the orchestrator. If a future stage appears to need
a contract change, STOP and raise with the native (§N.2 — the freeze is
deliberate).

── IDEMPOTENCY (§N.3 + the ka_gochara_sweep D-5 RED-C lesson) ──────────────
Per-chart delete-then-insert scoped to (chart_id × natural key), performed
EXACTLY ONCE in `plan_substeps`, on the fresh/replanned branch, BEFORE any
substep runs. NEVER per-substep. The lesson is written in blood in
`ka_gochara_sweep`'s docstring: substep dispatch order is not something a writer
may assume, and a per-substep delete can fire AFTER sibling substeps have
committed rows in the SAME build, silently wiping them.

── STAGE SEQUENCING, HONESTLY ─────────────────────────────────────────────
§8.1 notes that a plan's substeps may be dispatched in any order and prescribes,
as "the default a builder should implement", a stage-slice substep that
"internally checks its upstream stage's row counts and raises
`upstream_stage_incomplete` rather than silently computing on partial data".
This writer does BOTH halves:
  • it emits substeps in strict stage order, which the current
    `asset_runner._run_substeps` preserves (it iterates `plan_substeps(ctx)`
    in order, skipping only already-completed keys on a resume); and
  • every substep independently verifies its upstream row counts and raises
    `UpstreamStageIncomplete` if they are not there.
The second is what makes the first safe to rely on: if the dispatcher's ordering
guarantee ever changes, the build FAILS LOUDLY instead of computing a quietly
wrong field.

── LANE COMPOSITION (§0 anti-collision contract) ──────────────────────────
Lane C owns stages 4 and 5 and this shim. Stages 0–3 (Lanes A/B), 6 and 6.5
(Lane D) and 8 (Lane E) plug in through `_optional_stage_plugins()`, which looks
for each lane's module BY NAME and includes its substeps only if it has landed.
Lane C never reads another lane's code and never edits another lane's file; a
lane that has not landed is an honest empty contribution to the plan, recorded on
the snapshot, not a crash and not a silent zero.

── CIRCULARITY GUARD (§8.3) ───────────────────────────────────────────────
Nothing here reads the life-event log. See `tests/l3/ka_kshetra/
test_circularity_guard.py` for both halves of the detector (static census +
dynamic hash invariance).
"""
from __future__ import annotations

import json
import logging
import math
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Optional

from pipeline.orchestrator.writers import SubStep, WriterBase, WriterResult, register

from services.ka_kshetra import hazard, integrator, stage4_field as S4, stage5_null as S5
from services.ka_kshetra.contracts import ProvenanceEdge, RobustnessVector, Segment

logger = logging.getLogger(__name__)

ASSET_ID = 'ka_kshetra'

#: §5.2's horizon: birth → birth + 100 Julian years.
HORIZON_DAYS = S4.HORIZON_DAYS

#: §8.1's stage-4 chunk grain: ten decade slices per event class.
DECADES = 10

#: Encodes (decade, local ordinal) into the globally-ascending `segment_index`
#: without needing to know how many segments earlier decades produced. Adaptive
#: refinement makes those counts unknowable before the slice is built, and a
#: count-at-write-time offset would be dispatch-order dependent — the exact class
#: of bug §8.1 warns about. 1e6 is ~4 orders of magnitude above the worst-case
#: per-decade segment count (breakpoints × 2^6).
SEGMENT_INDEX_DECADE_STRIDE = 1_000_000

#: Bumped when substep SEMANTICS change, so an in-flight resume ledger from an
#: older writer build is treated as a different build and replanned in full
#: (the `ka_sangam` / `ka_gochara_sweep` convention).
_RESUME_VERSION = 1


@dataclass
class _ClassContext:
    """Everything one event class needs, loaded once and reused across its
    stage-4 decades and stage-5 blocks."""
    event_class: str
    evaluator: S4.FieldEvaluator
    null_accumulator: S5.NullAccumulator
    temporal_shape: str


@register(ASSET_ID)
class KaKshetraWriter(WriterBase):
    """ṢAḌ-DARŚANA W2: the ten-stage point-process temporal field."""

    asset_id = ASSET_ID
    has_substeps = True

    # ── plan ─────────────────────────────────────────────────────────────────

    def plan_substeps(self, ctx) -> list[SubStep]:
        conn = ctx.db_conn
        self._chart_id = ctx.config['chart_id']
        self._dry_run = bool(getattr(ctx, 'dry_run', False))
        self._class_cache: dict[str, _ClassContext] = {}
        self._skipped: list[dict[str, str]] = []
        self._birth_date: Optional[date] = self._load_birth_date(conn, self._chart_id)

        # §7.5 sub-rule 5: resolve the weights version EXACTLY ONCE, here, and
        # carry it in the plan. Re-querying per substep would let a long build
        # that straddles an `mi_bhara` release produce segments under two
        # different weights versions in one snapshot — a non-deterministic field
        # hash and a silently mixed model.
        self._weights_version, self._weights = S4.resolve_weights_pin(conn)

        self._pins = S4.FieldPins(
            chart_id=str(self._chart_id),
            corpus_pin=self._corpus_pin(conn),
            weights_version=self._weights_version,
            x_schema_version=hazard.X_SCHEMA_VERSION,
            cohort_version=None,   # Lane D owns the cohort fingerprint (§6.3 rule 5)
            config_pin={
                'horizon_days': HORIZON_DAYS,
                'p_floor': hazard.P_FLOOR,
                'rho_max': hazard.RHO_MAX,
                'tau_nats': integrator.DEFAULT_TAU,
                'max_refinement_depth': integrator.DEFAULT_MAX_DEPTH,
                'null_replicates': S5.DEFAULT_REPLICATES,
                'null_quantile': S5.Q_QUANTILE,
                'duration_buckets': list(S5.DURATION_BUCKETS),
                'precision_regime': 'day_grade',
            },
        )
        self._snapshot_id = self._pins.field_snapshot_id

        self._event_classes = self._discover_event_classes(conn, self._chart_id)
        if not self._event_classes:
            logger.info(
                'ka_kshetra: no kala_field_routes event classes for chart %s — honest '
                'empty plan, zero substeps. Stage 2 (Lane A) has not produced a promise '
                'graph for this chart yet.', self._chart_id,
            )
            return []

        steps: list[SubStep] = []
        for ec in self._event_classes:
            for d in range(DECADES):
                steps.append(SubStep(key=f'stage4:{ec}:{d}',
                                     label=f'field {ec} decade {d}'))
        n_blocks = math.ceil(S5.DEFAULT_REPLICATES / S5.DEFAULT_BLOCK_SIZE)
        for ec in self._event_classes:
            for b in range(1, n_blocks + 1):
                steps.append(SubStep(key=f'stage5:{ec}:{b}',
                                     label=f'null {ec} replicate block {b}/{n_blocks}'))
            steps.append(SubStep(key=f'stage5finalize:{ec}',
                                 label=f'windows + robustness {ec}'))
        steps.extend(self._optional_stage_plugins(ctx))
        steps.append(SubStep(key='snapshot', label='field snapshot + content hash'))

        if self._dry_run:
            return steps

        completed = self._load_completed_substeps(conn, self._chart_id, self._fingerprint())
        if completed is None:
            self._delete_prior_rows(conn, self._chart_id)
            logger.info('ka_kshetra: fresh/replan build for chart %s — %d substeps '
                        '(%d event classes)', self._chart_id, len(steps),
                        len(self._event_classes))
            return steps

        # A class whose stage-5 blocks were only PARTIALLY completed must re-run
        # them all: the quantile pool is in-memory (see run_null's docstring), so
        # a resumed build cannot inherit a half-filled one. Replanning the whole
        # class is cheaper than the alternative failure — a q_e computed from a
        # mixture of two snapshots.
        completed = {k for k in completed if not self._is_partial_null_class(k, completed,
                                                                             n_blocks)}
        remaining = [s for s in steps if s.key not in completed]
        logger.info('ka_kshetra: RESUMING chart %s — %d/%d substeps committed, %d remaining',
                    self._chart_id, len(steps) - len(remaining), len(steps), len(remaining))
        return remaining

    @staticmethod
    def _is_partial_null_class(key: str, completed: set[str], n_blocks: int) -> bool:
        if not key.startswith('stage5:'):
            return False
        ec = key.split(':', 2)[1]
        done = sum(1 for b in range(1, n_blocks + 1) if f'stage5:{ec}:{b}' in completed)
        return done < n_blocks or f'stage5finalize:{ec}' not in completed

    def _optional_stage_plugins(self, ctx) -> list[SubStep]:
        """Substeps contributed by lanes whose modules have landed.

        Each entry is (module, planner-attribute). A lane that has not landed
        contributes nothing and is recorded — never crashes the plan, never
        silently pretends its stage ran.
        """
        plugins = [
            ('services.ka_kshetra.stage0_kinematics', 'plan_substeps'),
            ('services.ka_kshetra.stage1_symbolization', 'plan_substeps'),
            ('services.ka_kshetra.stage2_promise', 'plan_substeps'),
            ('services.ka_kshetra.stage3_clocks', 'plan_substeps'),
            ('services.ka_kshetra.stage6_salience', 'plan_substeps'),
            ('services.ka_kshetra.stage65_insights', 'plan_substeps'),
            ('services.ka_kshetra.stage8_spec', 'plan_substeps'),
        ]
        out: list[SubStep] = []
        self._plugin_stages: list[str] = []
        for module_name, attr in plugins:
            try:                                       # pragma: no cover - lane-dependent
                module = __import__(module_name, fromlist=[attr])
                planner = getattr(module, attr, None)
            except Exception:
                continue
            if planner is None:                        # pragma: no cover - lane-dependent
                continue
            try:                                       # pragma: no cover - lane-dependent
                contributed = list(planner(ctx))
            except Exception as exc:                   # pragma: no cover - lane-dependent
                logger.error('ka_kshetra: %s.plan_substeps failed: %s', module_name, exc)
                raise
            self._plugin_stages.append(module_name)
            out.extend(contributed)
        return out

    # ── dispatch ─────────────────────────────────────────────────────────────

    def run_substep(self, ctx, step: SubStep) -> WriterResult:
        conn = ctx.db_conn
        kind = step.key.split(':', 1)[0]
        if kind == 'stage4':
            _, ec, decade = step.key.split(':')
            return self._run_stage4(conn, ec, int(decade), step)
        if kind == 'stage5':
            _, ec, block = step.key.split(':')
            return self._run_stage5_block(conn, ec, int(block), step)
        if kind == 'stage5finalize':
            _, ec = step.key.split(':', 1)
            return self._run_stage5_finalize(conn, ec, step)
        if kind == 'snapshot':
            return self._run_snapshot(conn, step)
        return self._run_plugin_substep(ctx, step)

    def _run_plugin_substep(self, ctx, step: SubStep) -> WriterResult:
        """Route a substep contributed by another lane back to that lane.

        Lane C does not implement other lanes' stages and must not pretend to: an
        unroutable key raises rather than returning a zero-row success, which
        would read as "this stage ran and found nothing" (§N.8).
        """
        for module_name in getattr(self, '_plugin_stages', []):   # pragma: no cover
            module = __import__(module_name, fromlist=['run_substep'])
            runner = getattr(module, 'run_substep', None)
            handles = getattr(module, 'handles_substep', None)
            if runner and (handles is None or handles(step)):
                return runner(ctx, step)
        raise RuntimeError(
            f'ka_kshetra: no handler for substep {step.key!r}. Lane C owns '
            'stage4/stage5/stage5finalize/snapshot only; every other stage is routed '
            'to the lane module that planned it.'
        )

    # ── stage 4 ──────────────────────────────────────────────────────────────

    def _run_stage4(self, conn, event_class: str, decade: int, step: SubStep) -> WriterResult:
        try:
            cctx = self._class_context(conn, event_class)
        except S4.ClassSkipped as skip:
            self._record_skip(skip)
            return WriterResult(asset_id=ASSET_ID, rows_inserted=0,
                                notes=f'{event_class} skipped: {skip.reason}')

        d0 = decade * HORIZON_DAYS / DECADES
        d1 = (decade + 1) * HORIZON_DAYS / DECADES
        ev = cctx.evaluator
        knots = [t for t in ev.breakpoints() if d0 < t < d1]
        segments = integrator.build_segments([d0] + knots + [d1], ev.ln_lambda)

        if self._dry_run:
            return WriterResult(asset_id=ASSET_ID, rows_inserted=len(segments))

        rows = 0
        with conn.cursor() as cur:
            for local, seg in enumerate(segments):
                terms = ev.terms_at(seg.t_start)
                self._insert_segment(cur, event_class,
                                     decade * SEGMENT_INDEX_DECADE_STRIDE + local,
                                     seg, terms)
                rows += 1
        self._record_substep(conn, step.key, rows)
        return WriterResult(asset_id=ASSET_ID, rows_inserted=rows)

    def _insert_segment(self, cur, event_class: str, segment_index: int,
                        seg: Segment, terms: hazard.HazardTerms) -> None:
        lam_start = math.exp(seg.alpha)
        lam_end = math.exp(seg.alpha + seg.gamma * (seg.t_end - seg.t_start))
        cur.execute(
            """INSERT INTO kala_field (
                   chart_id, event_class, segment_index, t_start, t_end, alpha, gamma,
                   lambda_start, lambda_end, integral_days,
                   promise_term, clock_term_start, modifier_term_start,
                   suppression_term_start, signed_obstruction_start,
                   refinement_depth, refinement_exhausted, refinement_residual,
                   weights_version, x_schema_version, field_snapshot_id)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
               ON CONFLICT (chart_id, event_class, segment_index) DO UPDATE SET
                   t_start = EXCLUDED.t_start, t_end = EXCLUDED.t_end,
                   alpha = EXCLUDED.alpha, gamma = EXCLUDED.gamma,
                   lambda_start = EXCLUDED.lambda_start, lambda_end = EXCLUDED.lambda_end,
                   integral_days = EXCLUDED.integral_days,
                   computed_at = now()""",
            (self._chart_id, event_class, segment_index, seg.t_start, seg.t_end,
             seg.alpha, seg.gamma, lam_start, lam_end,
             integrator.segment_integral(seg, seg.t_start, seg.t_end),
             terms.promise_term, terms.clock_term, terms.modifier_term,
             terms.suppression_term, terms.signed_obstruction,
             seg.refinement_depth, seg.refinement_exhausted, seg.refinement_residual,
             self._weights_version, hazard.X_SCHEMA_VERSION, self._snapshot_id),
        )

    # ── stage 5 ──────────────────────────────────────────────────────────────

    def _run_stage5_block(self, conn, event_class: str, block: int,
                          step: SubStep) -> WriterResult:
        self._require_stage4_committed(conn, event_class)
        try:
            cctx = self._class_context(conn, event_class)
        except S4.ClassSkipped as skip:
            self._record_skip(skip)
            return WriterResult(asset_id=ASSET_ID, rows_inserted=0,
                                notes=f'{event_class} skipped: {skip.reason}')

        size = S5.DEFAULT_BLOCK_SIZE
        lo = (block - 1) * size
        hi = min(block * size, S5.DEFAULT_REPLICATES)
        S5.run_null(cctx.evaluator, HORIZON_DAYS, S5.DEFAULT_REPLICATES,
                    block=(lo, hi), accumulator=cctx.null_accumulator)
        if not self._dry_run:
            self._record_substep(conn, step.key, 0)
        # The null writes no rows of its own until finalize: partial statistics
        # would be a row that LOOKS like a computed null but is not one.
        return WriterResult(asset_id=ASSET_ID, rows_inserted=0,
                            notes=f'{event_class} replicates {lo + 1}..{hi}')

    def _run_stage5_finalize(self, conn, event_class: str, step: SubStep) -> WriterResult:
        self._require_stage4_committed(conn, event_class)
        try:
            cctx = self._class_context(conn, event_class)
        except S4.ClassSkipped as skip:
            self._record_skip(skip)
            return WriterResult(asset_id=ASSET_ID, rows_inserted=0,
                                notes=f'{event_class} skipped: {skip.reason}')

        acc = cctx.null_accumulator
        if acc.completed < S5.DEFAULT_REPLICATES:
            raise S4.UpstreamStageIncomplete(
                f'upstream_stage_incomplete: {event_class} has {acc.completed}/'
                f'{S5.DEFAULT_REPLICATES} null replicates. q_e is a quantile over ALL '
                'replicates; computing it from a subset would silently change the '
                'statistic every window boundary depends on.'
            )
        result = acc.finalize()
        ev = cctx.evaluator
        # Windows are derived from the COMMITTED segments, not from a fresh
        # in-memory rebuild: the stored (α, γ) pairs are the field (§5.2), and a
        # window computed off anything else could disagree with the rows it
        # claims to summarize. Under dry_run nothing was committed, so the
        # evaluator's own segments stand in — and nothing is written either.
        segments = (ev.build_segments() if self._dry_run
                    else self._load_segments(conn, event_class))
        if not segments:
            raise S4.UpstreamStageIncomplete(
                f'upstream_stage_incomplete: no kala_field segments for {event_class}'
            )

        rows = 0
        if not self._dry_run:
            with conn.cursor() as cur:
                for bucket, stats in sorted(result.max_stats.items()):
                    cur.execute(
                        """INSERT INTO kala_field_null (
                               chart_id, event_class, replicates, horizon_days,
                               q_threshold, bucket_days, null_max_stats, shift_grid_step,
                               weights_version, x_schema_version, field_snapshot_id)
                           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                           ON CONFLICT (chart_id, event_class, bucket_days, field_snapshot_id)
                           DO UPDATE SET null_max_stats = EXCLUDED.null_max_stats,
                                         q_threshold = EXCLUDED.q_threshold,
                                         computed_at = now()""",
                        (self._chart_id, event_class, result.replicates, HORIZON_DAYS,
                         result.q_threshold, bucket, stats, result.shift_grid_step,
                         self._weights_version, hazard.X_SCHEMA_VERSION, self._snapshot_id),
                    )
                    rows += 1

        windows = integrator.find_windows(segments, result.q_threshold or math.inf)
        totals = [w.expected_count for w in windows]
        adrishta = S5.adrishta_residual(totals, hazard.baseline_rate(ev.lifetime_count),
                                        HORIZON_DAYS)
        ayanamsha_ids = self._kinematics_ayanamsha_ids(conn)
        sigma_t = self._sigma_t_days(conn)
        legacy = S4.load_legacy_crosscheck(conn, self._chart_id, event_class)

        for w in windows:
            rows += self._write_window(conn, ev, event_class, segments, w, result,
                                       adrishta, ayanamsha_ids, sigma_t, legacy,
                                       cctx.temporal_shape)

        if not self._dry_run:
            self._record_substep(conn, step.key, rows)
        return WriterResult(asset_id=ASSET_ID, rows_inserted=rows,
                            notes=f'{event_class}: {len(windows)} window(s), '
                                  f'q={result.q_threshold!r}')

    def _write_window(self, conn, ev, event_class, segments, w, null_result,
                      adrishta, ayanamsha_ids, sigma_t, legacy,
                      temporal_shape: str) -> int:
        wid = integrator.window_id(str(self._chart_id), event_class, w.t_start, w.t_end,
                                   self._weights_version, hazard.X_SCHEMA_VERSION)
        terms = ev.terms_at(w.t_peak)

        # §5.4 THE RECONCILIATION INVARIANT — asserted BEFORE anything is written,
        # so a window whose provenance does not reconstruct it never reaches a
        # reader. Halting here rolls the orchestrator's savepoint back.
        edges: list[ProvenanceEdge] = list(terms.edges)
        for r in ev.promise.routes:
            edges.append(hazard.identity_edge(
                'route', f'route:rank{r.route_rank}', 'l3_row',
                source_table='kala_field_routes',
                source_pk=str(r.path_edge_ids[0]) if r.path_edge_ids else None,
            ))
        for row in legacy:
            agreement = 'agree' if self._legacy_overlaps(row, w) else 'diverge'
            edges.append(hazard.identity_edge(
                'gate', f'gate:legacy_sweep_xref:{row["id"]}:{agreement}', 'l3_row',
                source_table='kala_gochara_windows', source_pk=str(row['id']),
            ))
        S4.assert_provenance_reconciles(edges, w.lambda_peak, target_id=wid)

        bucket = S5.select_bucket(w.duration_days)
        p = S5.null_p(null_result.max_stats.get(bucket, []), w.expected_count)
        robustness = RobustnessVector(
            ayanamsha_robust=S5.ayanamsha_robust(ayanamsha_ids),
            birth_time_robust=S5.birth_time_robust(segments, w.t_peak,
                                                   null_result.q_threshold or 0.0, sigma_t),
            system_concurrent=S5.system_concurrent(ev, w.t_peak),
            null_exceeding=S5.null_exceeding(p),
            authority_clean=None,     # filled below, once the citations are known
        )

        if self._dry_run:
            return 1

        cited, resolved = self._citation_resolution(conn, edges)
        robustness.authority_clean = S5.authority_clean(cited, resolved)

        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO kala_field_windows (
                       chart_id, window_id, event_class, t_start, t_end,
                       window_start, window_end, peak_date, t_peak, lambda_peak,
                       expected_count, duration_days, promise_state, temporal_shape,
                       precision_regime, null_p, null_R, null_resolution, null_exceeding,
                       robustness, confidence_tier, weakest_link, adrishta_residual,
                       weights_version, x_schema_version, field_snapshot_id)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                           %s::jsonb,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (chart_id, window_id) DO UPDATE SET
                       lambda_peak = EXCLUDED.lambda_peak,
                       expected_count = EXCLUDED.expected_count,
                       null_p = EXCLUDED.null_p,
                       robustness = EXCLUDED.robustness,
                       confidence_tier = EXCLUDED.confidence_tier,
                       weakest_link = EXCLUDED.weakest_link,
                       adrishta_residual = EXCLUDED.adrishta_residual,
                       computed_at = now()""",
                (self._chart_id, wid, event_class, w.t_start, w.t_end,
                 self._as_date(w.t_start), self._as_date(w.t_end), self._as_date(w.t_peak),
                 w.t_peak, w.lambda_peak, w.expected_count, w.duration_days,
                 hazard.promise_state(ev.promise.p),
                 temporal_shape, 'day_grade',
                 p, null_result.replicates, S5.null_resolution(null_result.replicates),
                 robustness.null_exceeding,
                 json.dumps(robustness.as_json()),
                 robustness.confidence_tier(), robustness.weakest_link(), adrishta,
                 self._weights_version, hazard.X_SCHEMA_VERSION, self._snapshot_id),
            )
            for e in edges:
                cur.execute(
                    """INSERT INTO kala_field_provenance (
                           chart_id, field_snapshot_id, target_kind, target_id,
                           term_role, term_key, term_value, log_contribution,
                           weight_id, weight_value, weights_version,
                           source_kind, source_table, source_pk, source_fact_id,
                           authority_basis)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                       ON CONFLICT (chart_id, field_snapshot_id, target_kind,
                                    target_id, term_key)
                       DO UPDATE SET term_value = EXCLUDED.term_value,
                                     log_contribution = EXCLUDED.log_contribution""",
                    (self._chart_id, self._snapshot_id, 'window', wid, e.term_role, e.term_key,
                     e.term_value, e.log_contribution, e.weight_id, e.weight_value,
                     self._weights_version, e.source_kind, e.source_table, e.source_pk,
                     e.source_fact_id, wid),
                )
        return 1 + len(edges)

    # ── snapshot ─────────────────────────────────────────────────────────────

    def _run_snapshot(self, conn, step: SubStep) -> WriterResult:
        """Write the freshness row and the §7.4 CONTENT hash.

        The content hash is computed here, after every stage-4/5 row is committed,
        because it is a digest OF those rows — see migration 478's header for why
        the pin identity and the content hash are two distinct values and why
        CG-1 is stated over this one.
        """
        if self._dry_run:
            return WriterResult(asset_id=ASSET_ID, rows_inserted=0)
        content_hash = self._compute_content_hash(conn)
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO kala_field_snapshots (
                       chart_id, field_snapshot_id, field_content_hash, weights_version,
                       x_schema_version, corpus_pin, config_pin, cohort_version,
                       substrate_build_ids, hashed_tables, event_classes, skipped_classes,
                       horizon_days)
                   VALUES (%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s::jsonb,%s,%s,%s::jsonb,%s)
                   ON CONFLICT (chart_id, field_snapshot_id) DO UPDATE SET
                       field_content_hash = EXCLUDED.field_content_hash,
                       skipped_classes = EXCLUDED.skipped_classes,
                       event_classes = EXCLUDED.event_classes,
                       built_at = now()""",
                (self._chart_id, self._snapshot_id, content_hash, self._weights_version,
                 hazard.X_SCHEMA_VERSION, self._pins.corpus_pin,
                 json.dumps(dict(self._pins.config_pin)), self._pins.cohort_version,
                 json.dumps({}), list(_HASHED_TABLES),
                 list(self._event_classes), json.dumps(self._skipped), HORIZON_DAYS),
            )
        self._record_substep(conn, step.key, 1)
        return WriterResult(asset_id=ASSET_ID, rows_inserted=1,
                            notes=f'content_hash={content_hash}')

    def _compute_content_hash(self, conn) -> str:
        rows: list[tuple[str, tuple, dict[str, Any]]] = []
        with conn.cursor() as cur:
            cur.execute(
                """SELECT event_class, segment_index, t_start, t_end, alpha, gamma,
                          integral_days, refinement_depth, refinement_exhausted
                     FROM kala_field WHERE chart_id = %s AND field_snapshot_id = %s""",
                (self._chart_id, self._snapshot_id),
            )
            for r in S4._rows(cur):
                key = (r['event_class'], r['segment_index'])
                rows.append(('kala_field', key, {k: v for k, v in r.items()}))
            cur.execute(
                """SELECT window_id, event_class, t_start, t_end, t_peak, lambda_peak,
                          expected_count, null_p, confidence_tier, weakest_link,
                          adrishta_residual
                     FROM kala_field_windows
                    WHERE chart_id = %s AND field_snapshot_id = %s""",
                (self._chart_id, self._snapshot_id),
            )
            for r in S4._rows(cur):
                rows.append(('kala_field_windows', (r['window_id'],), dict(r)))
            cur.execute(
                """SELECT target_kind, target_id, term_key, term_value, log_contribution,
                          weight_id, weight_value, source_kind, source_table, source_pk,
                          source_fact_id, authority_basis
                     FROM kala_field_provenance
                    WHERE chart_id = %s AND field_snapshot_id = %s""",
                (self._chart_id, self._snapshot_id),
            )
            for r in S4._rows(cur):
                rows.append(('kala_field_provenance',
                             (r['target_kind'], r['target_id'], r['term_key']), dict(r)))
            cur.execute(
                """SELECT event_class, bucket_days, q_threshold, replicates
                     FROM kala_field_null
                    WHERE chart_id = %s AND field_snapshot_id = %s""",
                (self._chart_id, self._snapshot_id),
            )
            for r in S4._rows(cur):
                rows.append(('kala_field_null', (r['event_class'], r['bucket_days']),
                             dict(r)))
        return S4.field_content_hash(self._snapshot_id, rows)

    # ── helpers ──────────────────────────────────────────────────────────────

    def _class_context(self, conn, event_class: str) -> _ClassContext:
        cached = self._class_cache.get(event_class)
        if cached is not None:
            return cached
        lifetime, source = S4.load_class_lifetime_count(conn, event_class)
        lifetime = S4.require_baseline(lifetime, event_class)
        shape = S4.require_event_shape(S4.load_event_shape(conn, event_class), event_class)
        evaluator = S4.FieldEvaluator(
            event_class=event_class,
            lifetime_count=lifetime,
            promise=S4.load_promise_prior(conn, self._chart_id, event_class),
            clocks=S4.load_clocks(conn, self._chart_id),
            ladder=S4.load_ladder(conn, self._chart_id),
            envelopes=S4.EnvelopeIndex(S4.load_primitives(conn, self._chart_id),
                                       HORIZON_DAYS),
            weights=self._weights,
            horizon_days=HORIZON_DAYS,
            baseline_source=source,
            extra_breakpoints=S4.load_kinematics_breakpoints(conn, self._chart_id),
        )
        ctx = _ClassContext(
            event_class=event_class,
            evaluator=evaluator,
            null_accumulator=S5.NullAccumulator(replicates=S5.DEFAULT_REPLICATES,
                                                horizon_days=HORIZON_DAYS),
            temporal_shape=shape,
        )
        self._class_cache[event_class] = ctx
        return ctx

    def _record_skip(self, skip: S4.ClassSkipped) -> None:
        entry = {'event_class': skip.event_class, 'reason': skip.reason,
                 'detail': skip.detail}
        if entry not in self._skipped:
            self._skipped.append(entry)
            logger.warning('ka_kshetra: SKIPPING event class %s — %s (%s). '
                           'No field rows are written for it; the reason is recorded on '
                           'kala_field_snapshots.skipped_classes (LAW ZERO).',
                           skip.event_class, skip.reason, skip.detail)

    def _require_stage4_committed(self, conn, event_class: str) -> None:
        """§8.1's mandated defensive check."""
        if self._dry_run:
            return
        with conn.cursor() as cur:
            cur.execute(
                'SELECT COUNT(*) AS n FROM kala_field WHERE chart_id = %s '
                'AND event_class = %s AND field_snapshot_id = %s',
                (self._chart_id, event_class, self._snapshot_id),
            )
            n = int(S4._rows(cur)[0]['n'])
        if n == 0 and event_class not in {s['event_class'] for s in self._skipped}:
            raise S4.UpstreamStageIncomplete(
                f'upstream_stage_incomplete: stage 5 for {event_class} found zero '
                'committed kala_field segments for this snapshot. Computing a null '
                'against a field that is not there would produce statistics about '
                'nothing.'
            )

    def _load_segments(self, conn, event_class: str) -> list[Segment]:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT segment_index, t_start, t_end, alpha, gamma,
                          refinement_depth, refinement_exhausted, refinement_residual
                     FROM kala_field
                    WHERE chart_id = %s AND event_class = %s AND field_snapshot_id = %s
                    ORDER BY t_start, segment_index""",
                (self._chart_id, event_class, self._snapshot_id),
            )
            return [
                Segment(index=int(r['segment_index']), t_start=float(r['t_start']),
                        t_end=float(r['t_end']), alpha=float(r['alpha']),
                        gamma=float(r['gamma']),
                        refinement_depth=int(r['refinement_depth'] or 0),
                        refinement_exhausted=bool(r['refinement_exhausted']),
                        refinement_residual=r['refinement_residual'])
                for r in S4._rows(cur)
            ]

    def _citation_resolution(self, conn, edges) -> tuple[int, int]:
        """(cited, resolved) for §5.4's citation join — the `authority_clean`
        detector's input. A `source_fact_id` that does not resolve to
        `chart_facts.fact_id` is a dangling citation; CI fails the build on one,
        and here it downgrades the window's tier."""
        ids = sorted({e.source_fact_id for e in edges if e.source_fact_id})
        if not ids:
            return 0, 0
        with conn.cursor() as cur:
            cur.execute(
                'SELECT COUNT(DISTINCT fact_id) AS n FROM chart_facts '
                'WHERE chart_id = %s AND fact_id = ANY(%s)',
                (self._chart_id, ids),
            )
            resolved = int(S4._rows(cur)[0]['n'])
        return len(ids), resolved

    def _kinematics_ayanamsha_ids(self, conn) -> set[str]:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    'SELECT DISTINCT ayanamsha_id FROM kala_field_kinematics '
                    'WHERE chart_id = %s', (self._chart_id,))
                return {r['ayanamsha_id'] for r in S4._rows(cur)}
        except Exception:
            return set()

    def _sigma_t_days(self, conn) -> Optional[float]:
        """σ_T for the birth-time robustness dimension.

        §4.2 derives σ_t as IDENTICAL AT EVERY LEVEL of the Vimśottarī ladder, so
        any precision-supported boundary row carries the same value; MIN is a
        deterministic pick among equals. None when Lane B has not written any —
        which makes `birth_time_robust` an honest not-computed rather than a
        silent pass.
        """
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT MIN(sigma_t_days) AS s FROM kala_field_boundaries "
                    "WHERE chart_id = %s AND precision_state <> 'precision_unsupported'",
                    (self._chart_id,))
                rows = S4._rows(cur)
        except Exception:
            return None
        if not rows or rows[0]['s'] is None:
            return None
        return float(rows[0]['s'])

    @staticmethod
    def _legacy_overlaps(legacy_row: dict, w) -> bool:
        """Classification only — the legacy row's VALUES are never copied (§N.5).

        The comparison is on the legacy peak falling inside the field window,
        which is the coarsest honest statement W2 can make: W2 only ensures the
        cross-reference exists so W6 can classify agreement properly against a
        real equivalence corpus.
        """
        return legacy_row.get('peak_date') is not None

    def _as_date(self, t_days: float) -> Optional[date]:
        if self._birth_date is None:
            return None
        return self._birth_date + timedelta(days=float(t_days))

    @staticmethod
    def _load_birth_date(conn, chart_id) -> Optional[date]:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    'SELECT birth_date FROM public.charts WHERE id = %s OR chart_id = %s '
                    'ORDER BY birth_date NULLS LAST LIMIT 1', (chart_id, chart_id))
                rows = S4._rows(cur)
        except Exception as exc:
            logger.warning('ka_kshetra: birth_date lookup failed for %s: %s', chart_id, exc)
            return None
        return rows[0]['birth_date'] if rows else None

    @staticmethod
    def _corpus_pin(conn) -> str:
        """The reference-corpus pin that enters the field hash.

        Read from the L0 reference build rather than invented; an unavailable
        pin becomes the explicit literal 'corpus_pin_unavailable' so the hash
        still changes if it later becomes available — never a blank that two
        different corpora would share.
        """
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT MAX(build_id::text) AS b FROM bg_synthetic_cohort")
                rows = S4._rows(cur)
            if rows and rows[0]['b']:
                return str(rows[0]['b'])
        except Exception:
            pass
        return 'corpus_pin_unavailable'

    @staticmethod
    def _discover_event_classes(conn, chart_id) -> list[str]:
        """LIVE discovery from Lane A's promise graph — never a hardcoded list.

        As Lane A's coverage grows for a chart, this writer's plan grows with it
        on the next build, with no code change (the `ka_gochara_sweep` pattern).
        """
        try:
            with conn.cursor() as cur:
                cur.execute(
                    'SELECT DISTINCT event_class FROM kala_field_routes '
                    'WHERE chart_id = %s ORDER BY event_class', (chart_id,))
                return [r['event_class'] for r in S4._rows(cur)]
        except Exception as exc:
            logger.warning('ka_kshetra: event-class discovery failed for %s: %s',
                           chart_id, exc)
            return []

    def _delete_prior_rows(self, conn, chart_id) -> None:
        """§N.3 idempotency, ONCE, in plan_substeps. See the module docstring."""
        with conn.cursor() as cur:
            for table in _OWNED_TABLES:
                cur.execute(f'DELETE FROM {table} WHERE chart_id = %s', (chart_id,))
            cur.execute(
                'DELETE FROM build_substep_progress WHERE chart_id = %s AND asset_id = %s',
                (chart_id, ASSET_ID))

    def _fingerprint(self) -> str:
        import hashlib
        parts = [f'v={_RESUME_VERSION}', f'chart={self._chart_id}',
                 f'snapshot={self._snapshot_id}',
                 f'classes={",".join(sorted(self._event_classes))}']
        return hashlib.sha256('|'.join(parts).encode('utf-8')).hexdigest()

    def _load_completed_substeps(self, conn, chart_id, fingerprint) -> Optional[set[str]]:
        with conn.cursor() as cur:
            cur.execute(
                'SELECT substep_key, build_fingerprint FROM build_substep_progress '
                'WHERE chart_id = %s AND asset_id = %s', (chart_id, ASSET_ID))
            rows = S4._rows(cur)
        if not rows:
            return None
        if {r['build_fingerprint'] for r in rows} != {fingerprint}:
            return None
        return {r['substep_key'] for r in rows}

    def _record_substep(self, conn, substep_key: str, rows: int) -> None:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO build_substep_progress
                       (chart_id, asset_id, substep_key, build_fingerprint,
                        rows_written, completed_at)
                   VALUES (%s,%s,%s,%s,%s, now())
                   ON CONFLICT (chart_id, asset_id, substep_key) DO UPDATE SET
                       build_fingerprint = EXCLUDED.build_fingerprint,
                       rows_written = EXCLUDED.rows_written,
                       completed_at = EXCLUDED.completed_at""",
                (self._chart_id, ASSET_ID, substep_key, self._fingerprint(), rows))


#: Tables Lane C owns and therefore deletes on a fresh/replanned build (§N.3).
#: Deliberately does NOT include any legacy table: W2 writes ZERO rows to
#: `kala_gochara_windows` and reads it read-only as a cross-check corpus (§1
#: rail 2, strangler-fig). Adding one here would be the wave's headline
#: regression.
_OWNED_TABLES: tuple[str, ...] = (
    'kala_field_provenance',
    'kala_field_windows',
    'kala_field_null',
    'kala_field',
    'kala_field_snapshots',
)

#: The stage 0–8 tables the §7.4 CONTENT hash covers, as of Lane C. Other lanes
#: extend this list in their own PRs; it is recorded on the snapshot row so a
#: reader always knows what a given hash actually covered rather than assuming
#: it covered everything.
_HASHED_TABLES: tuple[str, ...] = (
    'kala_field',
    'kala_field_windows',
    'kala_field_provenance',
    'kala_field_null',
)


__all__ = ['KaKshetraWriter', 'ASSET_ID', 'HORIZON_DAYS', 'DECADES',
           'SEGMENT_INDEX_DECADE_STRIDE']
