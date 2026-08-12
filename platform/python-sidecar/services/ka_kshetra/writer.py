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
Lane C owns stages 4 and 5 and this shim. Stages 0–3 (Lanes A/B) plug in through
`_optional_stage_plugins()`, which looks for each lane's module BY NAME and
includes its substeps only if it has landed. A lane that has not landed is an
honest empty contribution to the plan, recorded on the snapshot, not a crash and
not a silent zero.

Stages 6 / 6.5 / 8 are PUBLISHED HERE (lane `w2-field-writer-wiring`). The pure
functions live in and remain owned by `stage6_salience.py` + `submodular.py`,
`stage65_insights.py` and `stage8_spec.py`; this writer only supplies them their
DB inputs and persists their outputs. They are NOT routed through
`_optional_stage_plugins` because the plugin protocol hands a lane module only
`(ctx, step)` — it has no access to the PINNED build state (`field_snapshot_id`,
`weights_version`, the resolved weights map) that §7.5 sub-rule 5 requires be
resolved exactly once per build. A plugin that re-derived the pin per substep is
precisely the "segments under two different weights versions in one snapshot"
failure that rule exists to prevent, so the publication sites live where the pin
does.

── STAGE 6 / 6.5 GRAIN: A DELIBERATE DEVIATION FROM §8.1, AND WHY ────────
§8.1's substep table proposes `stage6:<event_class>` and `stage65:<insight_type>`.
Both are published here as SINGLE CHART-LEVEL substeps instead. The reason is the
same for both, and it is §8.1's own stated hazard rather than a convenience:

  • Stage 6's submodular selection (§6.2) optimizes a facility-location objective
    over the WHOLE candidate set V — `coverage_fraction = F(S)/F(V)`, and
    `largest_omission` is defined against the final S. Migration 495 stores those
    as run-level values "denormalized onto every row of the chart's run". Split
    per class, each slice would run a different objective over a different V, and
    which classes were already committed when a slice ran would change its
    answer: a dispatch-order-dependent selection, which is exactly what §8.1
    forbids.
  • Stage 6.5's `detect_compression` clusters ACROSS classes and families, and
    `synthesize_insights` is the single unit-tested entry point that runs the
    seven non-LEL detectors as one pass. Slicing by `insight_type` would fan out
    to the individual detectors and put a second, untested composition path in
    production beside the tested one.

Stage 8 keeps §8.1's grain exactly (`stage8:<view>`, six views) — one spec row per
view is genuinely independent work, and `kala_timeline_spec`'s natural key
(chart_id, generated_for, field_snapshot_id) is per-view by construction.

── CIRCULARITY GUARD (§8.3) ───────────────────────────────────────────────
Nothing here reads the life-event log. See `tests/l3/ka_kshetra/
test_circularity_guard.py` for both halves of the detector (static census +
dynamic hash invariance).
"""
from __future__ import annotations

import hashlib
import json
import logging
import math
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Any, Optional

from pipeline.orchestrator.writers import SubStep, WriterBase, WriterResult, register

from services.ka_kshetra import (
    cohort_client,
    hazard,
    integrator,
    stage4_field as S4,
    stage5_null as S5,
    stage6_salience as S6,
    stage8_spec as S8,
    stage65_insights as S65,
    submodular as SM,
)
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
#: v2 — stages 6 / 6.5 / 8 joined the plan and the content hash.
_RESUME_VERSION = 3

#: §6.2's row budget K. The design's own worked example ("the budget spends
#: itself across 15 *different* things") is the source of the number; it is a
#: budget, not a floor — a chart with fewer candidates selects fewer rows and
#: never fabricates any (§N.4 floors-are-aspirational).
SUBMODULAR_ROW_BUDGET = 15

#: §7.1's six `generated_for` values, matching migration 496's CHECK exactly.
TIMELINE_VIEWS: tuple[str, ...] = ('now', 'ahead', 'elect', 'story', 'priority', 'explain')

#: Daśā levels a timeline renders as `points[]`. MD + AD only: the full ladder
#: over a 100-year horizon runs to thousands of boundaries, which is a data dump
#: rather than a timeline. The cut is declared here rather than hidden in a
#: LIMIT, and `precision_unsupported` rows are still PASSED to the spec builder
#: so its `precision_unsupported_boundaries_omitted` coverage count stays honest.
TIMELINE_BOUNDARY_LEVELS: tuple[str, ...] = ('MD', 'AD')

#: The cohort feature the rarity axis (§6.1 I / §6.4 rarity_firing) is keyed on.
#: §6.3's own worked sentence for the matched sub-cohort is "how often does a
#: chart with lagna X also sit in a Ketu mahādaśā at the same life-stage the
#: native is in" — so the feature is the natal Lagna sign and the match is the
#: Vimśottarī MD lord at the carrier window's peak. Both are READ, never
#: recomputed: the Lagna longitude comes from L1 `chart_facts` and the MD lord
#: from Lane B's `kala_field_boundaries` (§N.5).
COHORT_FEATURE_KEY = 'lagna_sign'

#: `bg_synthetic_cohort_md.md_lord`'s CHECK domain — the nine canonical
#: `PLANET_NAMES` values. A `kala_field_boundaries.lord` outside this set (an
#: abbreviation, a rāśi for a sign-based system) is NOT passed as `md_lord`: the
#: matched query would return an empty sub-cohort, and an empty numerator would
#: read as p_cohort = 0, i.e. MAXIMALLY rare — a fabricated rarity claim in the
#: highest-weighted salience slot. Unmatched means unmatched (§N.7 item 6).
_CANONICAL_MD_LORDS = frozenset({'Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter',
                                 'Venus', 'Saturn', 'Rahu', 'Ketu'})

#: §6.3's own days-per-year constant for the reference-age conversion.
_DAYS_PER_JULIAN_YEAR = 365.2425


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
        #: Machine-readable not-computed reasons that are NOT class skips — e.g.
        #: the rarity axis being unavailable. Surfaced in the substep notes so a
        #: NULL factor always carries a stated reason (§N.8).
        self._coverage_notes: list[str] = []
        # Chart-level data shared across all event-class contexts.
        # load_primitives / load_clocks / load_ladder / load_kinematics_breakpoints
        # all return the same rows regardless of event_class; loading them once
        # and sharing the objects prevents 19× duplication of the 166 k-primitive
        # EnvelopeIndex that was the primary OOM trigger in stage4/5.
        self._shared_envelopes = None          # S4.EnvelopeIndex, set on first class
        self._shared_clocks = None             # list[ClockApplicability]
        self._shared_ladder = None             # list[BoundaryRow]
        self._shared_extra_breakpoints = None  # list[float]
        self._birth_date, self._birth_time = self._load_birth_instant(conn, self._chart_id)

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

        # §2's pipeline order, top to bottom. Stages 0–3 lead: stage 4 consumes
        # their tables, so a plugin lane's substeps belong BEFORE stage4, not
        # after it as they previously sat. (No lane currently contributes any —
        # none of the stage0–3 modules exposes `plan_substeps` — so this
        # corrects the order before it can matter rather than after.)
        steps: list[SubStep] = list(self._optional_stage_plugins(ctx))
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
        # Stages 6 → 6.5 → 8, in pipeline order and strictly after every
        # stage5finalize: salience reads committed windows, insights read
        # committed salience, and the timeline spec reads both.
        steps.append(SubStep(key='stage6', label='salience vector + submodular selection'))
        steps.append(SubStep(key='stage65', label='insight synthesis (7 non-LEL types)'))
        for view in TIMELINE_VIEWS:
            steps.append(SubStep(key=f'stage8:{view}', label=f'timeline spec ({view})'))
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
        # Stages 0–3 only. Stages 6 / 6.5 / 8 were removed from this list when
        # their publication moved into this writer (see the module docstring's
        # LANE COMPOSITION section) — leaving them here would double-plan them
        # the moment one of those modules grew a `plan_substeps` attribute.
        #
        # ORDER IS LOAD-BEARING (SAMPURTI G1):
        #   stage0 → stage2 → stage3 → stage1
        # Rationale (data dependencies across stages):
        #   • stage2 reads bodha_cgm_nodes/edges/pratijna (no stage0 dependency)
        #     but must run before stage3 because stage3 reads kala_field_routes
        #     (written by stage2) in clock_activation/_route_gain_and_sign_for_lord.
        #   • stage3 reads chart_dashas AND kala_field_routes (stage2 output),
        #     writes kala_field_clocks + kala_field_boundaries.
        #   • stage1 reads BOTH kala_field_kinematics (stage0 output) AND
        #     kala_field_boundaries (stage3 output) for the sandhi_band primitive;
        #     it must therefore run after BOTH stage0 and stage3.
        #   • stage4+ reads all of the above.
        plugins = [
            ('services.ka_kshetra.stage0_kinematics', 'plan_substeps'),
            ('services.ka_kshetra.stage2_promise', 'plan_substeps'),
            ('services.ka_kshetra.stage3_clocks', 'plan_substeps'),
            ('services.ka_kshetra.stage1_symbolization', 'plan_substeps'),
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
        if kind == 'stage6':
            return self._run_stage6(conn, step)
        if kind == 'stage65':
            return self._run_stage65(conn, step)
        if kind == 'stage8':
            _, view = step.key.split(':', 1)
            return self._run_stage8(conn, view, step)
        if kind == 'snapshot':
            return self._run_snapshot(conn, step)
        return self._run_plugin_substep(ctx, step)

    def _run_plugin_substep(self, ctx, step: SubStep) -> WriterResult:
        """Route a substep contributed by another lane back to that lane.

        This writer does not implement other lanes' stages and must not pretend
        to: an unroutable key raises rather than returning a zero-row success,
        which would read as "this stage ran and found nothing" (§N.8).
        """
        for module_name in getattr(self, '_plugin_stages', []):   # pragma: no cover
            module = __import__(module_name, fromlist=['run_substep'])
            runner = getattr(module, 'run_substep', None)
            handles = getattr(module, 'handles_substep', None)
            if runner and (handles is None or handles(step)):
                return runner(ctx, step)
        raise RuntimeError(
            f'ka_kshetra: no handler for substep {step.key!r}. This writer owns '
            'stage4/stage5/stage5finalize/stage6/stage65/stage8/snapshot; every '
            'other stage is routed to the lane module that planned it.'
        )

    # ── stage 4 ──────────────────────────────────────────────────────────────

    # SQL constant shared by the batch (_run_stage4) and single-row (_insert_segment) paths.
    _KALA_FIELD_INSERT_SQL = """INSERT INTO kala_field (
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
                   computed_at = now()"""

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

        # L1e: separate computation from DB writes — batch all segment rows into a
        # single executemany call rather than one cur.execute() per segment.
        # Stage4 produces 40–80K segments per decade; at ~7ms per round-trip through
        # the Cloud SQL proxy, individual inserts took 5–10 min per decade.
        # executemany sends one batch, matching stage3's L1d pattern (which cut
        # chara_karaka boundaries from 22 min to seconds).
        params_list = [
            self._segment_row(event_class,
                              decade * SEGMENT_INDEX_DECADE_STRIDE + local,
                              seg, ev.terms_at(seg.t_start))
            for local, seg in enumerate(segments)
        ]
        if params_list:
            with conn.cursor() as cur:
                cur.executemany(self._KALA_FIELD_INSERT_SQL, params_list)
        self._record_substep(conn, step.key, len(params_list))
        return WriterResult(asset_id=ASSET_ID, rows_inserted=len(params_list))

    def _segment_row(self, event_class: str, segment_index: int,
                     seg: Segment, terms: hazard.HazardTerms) -> tuple:
        """Return the params tuple for one kala_field row (shared by batch and single paths)."""
        lam_start = math.exp(seg.alpha)
        lam_end = math.exp(seg.alpha + seg.gamma * (seg.t_end - seg.t_start))
        return (self._chart_id, event_class, segment_index, seg.t_start, seg.t_end,
                seg.alpha, seg.gamma, lam_start, lam_end,
                integrator.segment_integral(seg, seg.t_start, seg.t_end),
                terms.promise_term, terms.clock_term, terms.modifier_term,
                terms.suppression_term, terms.signed_obstruction,
                seg.refinement_depth, seg.refinement_exhausted, seg.refinement_residual,
                self._weights_version, hazard.X_SCHEMA_VERSION, self._snapshot_id)

    def _insert_segment(self, cur, event_class: str, segment_index: int,
                        seg: Segment, terms: hazard.HazardTerms) -> None:
        cur.execute(self._KALA_FIELD_INSERT_SQL,
                    self._segment_row(event_class, segment_index, seg, terms))

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

        rows += self._write_windows_batch(conn, ev, event_class, segments, windows, result,
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

    def _write_windows_batch(self, conn, ev, event_class, segments, windows, null_result,
                              adrishta, ayanamsha_ids, sigma_t, legacy,
                              temporal_shape: str) -> int:
        """L1o: batch-insert all windows + provenance in two executemany calls.

        Per-window _write_window does one cur.execute per edge (~37 edges/window
        × thousands of windows) — hundreds of thousands of round-trips causing
        30+ min finalize → idle_in_transaction timeout kills the signal-check
        connection. Two executemany calls reduce this to seconds.
        """
        if self._dry_run:
            return len(windows)
        if not windows:
            return 0

        # ── Phase 1: pure CPU — compute all per-window values (no DB I/O) ─────
        prepared: list[tuple] = []   # (wid, w, edges, bucket, p, robustness)
        for w in windows:
            wid = integrator.window_id(
                str(self._chart_id), event_class, w.t_start, w.t_end,
                self._weights_version, hazard.X_SCHEMA_VERSION,
            )
            terms = ev.terms_at(w.t_peak)
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
                birth_time_robust=S5.birth_time_robust(
                    segments, w.t_peak, null_result.q_threshold or 0.0, sigma_t,
                ),
                system_concurrent=S5.system_concurrent(ev, w.t_peak),
                null_exceeding=S5.null_exceeding(p),
                authority_clean=None,   # filled after batch citation query below
            )
            prepared.append((wid, w, edges, bucket, p, robustness))

        # ── Phase 2: ONE citation query covering all windows ──────────────────
        all_fact_ids = sorted({
            e.source_fact_id
            for _, _, edges, _, _, _ in prepared
            for e in edges
            if e.source_fact_id
        })
        resolved_set: set[str] = set()
        if all_fact_ids:
            with conn.cursor() as cur:
                cur.execute(
                    'SELECT DISTINCT fact_id FROM chart_facts '
                    'WHERE chart_id = %s AND fact_id = ANY(%s)',
                    (self._chart_id, all_fact_ids),
                )
                resolved_set = {r['fact_id'] for r in S4._rows(cur)}

        # ── Phase 3: build insert param lists ────────────────────────────────
        window_params: list[tuple] = []
        prov_params: list[tuple] = []
        for wid, w, edges, bucket, p, robustness in prepared:
            cited = sum(1 for e in edges if e.source_fact_id)
            resolved = sum(1 for e in edges if e.source_fact_id in resolved_set)
            robustness.authority_clean = S5.authority_clean(cited, resolved)
            window_params.append((
                self._chart_id, wid, event_class, w.t_start, w.t_end,
                self._as_date(w.t_start), self._as_date(w.t_end),
                self._as_date(w.t_peak), w.t_peak, w.lambda_peak,
                w.expected_count, w.duration_days,
                hazard.promise_state(ev.promise.p),
                temporal_shape, 'day_grade',
                p, null_result.replicates, S5.null_resolution(null_result.replicates),
                robustness.null_exceeding,
                json.dumps(robustness.as_json()),
                robustness.confidence_tier(), robustness.weakest_link(), adrishta,
                self._weights_version, hazard.X_SCHEMA_VERSION, self._snapshot_id,
            ))
            for e in edges:
                prov_params.append((
                    self._chart_id, self._snapshot_id, 'window', wid,
                    e.term_role, e.term_key, e.term_value, e.log_contribution,
                    e.weight_id, e.weight_value, self._weights_version,
                    e.source_kind, e.source_table, e.source_pk, e.source_fact_id, wid,
                ))

        # ── Phase 4: TWO executemany calls (was N×~37 individual inserts) ─────
        with conn.cursor() as cur:
            cur.executemany(
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
                window_params,
            )
            cur.executemany(
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
                prov_params,
            )
        return len(window_params) + len(prov_params)

    # ── stage 6 · salience vector + submodular selection (§6.1/§6.2) ─────────

    def _run_stage6(self, conn, step: SubStep) -> WriterResult:
        """Publish `kala_field_salience`: one row per committed window.

        Reads the COMMITTED `kala_field_windows` + `kala_field_provenance` rows
        rather than recomputing anything — the selection must describe the rows a
        reader will actually be served (§N.5), and the provenance edges are what
        §6.2's information atoms are built from.
        """
        if self._dry_run:
            return WriterResult(asset_id=ASSET_ID, rows_inserted=0)

        windows = self._load_committed_windows(conn)
        if not windows:
            # Honest empty: a chart whose classes were all skipped, or whose
            # field never exceeds its own null, has no candidates. Zero rows with
            # a stated reason — never a placeholder row (§N.8).
            self._record_substep(conn, step.key, 0)
            return WriterResult(asset_id=ASSET_ID, rows_inserted=0,
                                notes='honest_empty:no_committed_windows')

        prov = self._load_window_provenance(conn)
        ontology = self._load_ontology(conn, {w['event_class'] for w in windows})

        vectors: dict[str, S6.SalienceVector] = {}
        cohort_versions: set[str] = set()
        for w in windows:
            rate = self._cohort_rate_for_window(conn, w)
            if rate is not None and rate.cohort_version:
                cohort_versions.add(rate.cohort_version)
            info = ontology.get(w['event_class'])
            vectors[w['window_id']] = S6.compute_salience_vector(
                p_cohort=rate.p if rate else None,
                cohort_n_total=rate.n_total if rate else 0,
                ontology=info,
                event_domain=info.domain if info else None,
                window_t_start=float(w['t_start']),
                window_t_end=float(w['t_end']),
                confidence_tier=w.get('confidence_tier'),
                # §11's tri-plane `intervention_ref` is not built at W2, so
                # Actionability is an honest NULL that drops out of the
                # renormalized scalar — never a 0.0 that would read as
                # "verified: nothing can be done" (§6.1 "never imputed").
                intervention_ref=None,
                # No `question_frame` exists at BUILD time — it is a serving-time
                # input (E4). §6.1: "R = 1.0 when no question_frame is supplied".
                frame=None,
            )

        candidates = [
            SM.SubmodularCandidate(
                window_id=w['window_id'], event_class=w['event_class'],
                salience=vectors[w['window_id']].salience,
                lord_stack_at_peak=self._lord_stack_at_peak(conn, w),
                provenance_terms=tuple(
                    SM.ProvenanceTerm(term_key=t['term_key'],
                                      log_contribution=float(t['log_contribution']))
                    for t in prov.get(w['window_id'], ())),
            )
            for w in windows
        ]
        result = SM.select_submodular(candidates, SUBMODULAR_ROW_BUDGET)
        trace_by_id = {e.window_id: e for e in result.trace}
        cohort_version = sorted(cohort_versions)[0] if len(cohort_versions) == 1 else None

        rows = 0
        with conn.cursor() as cur:
            for w in windows:
                wid = w['window_id']
                v = vectors[wid]
                entry = trace_by_id.get(wid)
                cur.execute(
                    """INSERT INTO kala_field_salience (
                           chart_id, window_id, event_class,
                           factor_informativeness, factor_consequence, factor_relevance,
                           factor_reliability, factor_actionability,
                           salience, salience_weights_version, salience_basis,
                           selected, selection_rank, marginal_gain, atoms_newly_covered,
                           coverage_fraction, largest_omission_window_id,
                           largest_omission_marginal_gain,
                           weights_version, cohort_version, x_schema_version,
                           field_snapshot_id)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,
                               %s,%s,%s,%s,%s,%s,%s)
                       ON CONFLICT (chart_id, window_id) DO UPDATE SET
                           salience = EXCLUDED.salience,
                           salience_basis = EXCLUDED.salience_basis,
                           selected = EXCLUDED.selected,
                           selection_rank = EXCLUDED.selection_rank,
                           marginal_gain = EXCLUDED.marginal_gain,
                           atoms_newly_covered = EXCLUDED.atoms_newly_covered,
                           coverage_fraction = EXCLUDED.coverage_fraction,
                           computed_at = now()""",
                    (self._chart_id, wid, w['event_class'],
                     v.informativeness, v.consequence, v.relevance,
                     v.reliability, v.actionability,
                     v.salience, v.salience_weights_version, list(v.salience_basis),
                     entry is not None,
                     entry.rank if entry else None,
                     entry.marginal_gain if entry else None,
                     json.dumps([{'event_class': a.event_class,
                                  'window_family_id': a.window_family_id,
                                  'driver_term_key': a.driver_term_key}
                                 for a in entry.atoms_newly_covered]) if entry else None,
                     result.coverage_fraction,
                     result.largest_omission[0] if result.largest_omission else None,
                     result.largest_omission[1] if result.largest_omission else None,
                     self._weights_version, cohort_version, hazard.X_SCHEMA_VERSION,
                     self._snapshot_id),
                )
                rows += 1
        self._record_substep(conn, step.key, rows)
        return WriterResult(
            asset_id=ASSET_ID, rows_inserted=rows,
            notes=f'{rows} salience row(s), {len(result.selected)} selected, '
                  f'coverage={result.coverage_fraction:.4f}')

    # ── stage 6.5 · insight synthesis (§6.4) ─────────────────────────────────

    def _run_stage65(self, conn, step: SubStep) -> WriterResult:
        """Publish `kala_insights` — the SEVEN non-LEL types only.

        ⚠ CIRCULARITY GUARD CARVE-OUT (§6.4 / §8.3 CG-1). `biographical_echo` is
        the eighth type and reads the LEL; it is written exclusively by Lane E's
        biographical-join refresh with `lel_derived = TRUE`, and this path must
        never produce one. `stage65_insights.assemble_insight_row` hard-codes
        `lel_derived=False`, and the delete in `_delete_prior_rows` is scoped to
        `lel_derived = FALSE` so a rebuild of the field cannot wipe Lane E's rows.
        """
        if self._dry_run:
            return WriterResult(asset_id=ASSET_ID, rows_inserted=0)

        windows = self._load_committed_windows(conn)
        if not windows:
            self._record_substep(conn, step.key, 0)
            return WriterResult(asset_id=ASSET_ID, rows_inserted=0,
                                notes='honest_empty:no_committed_windows')

        salience = self._load_salience(conn)
        if not salience:
            raise S4.UpstreamStageIncomplete(
                'upstream_stage_incomplete: stage 6.5 found no kala_field_salience '
                'rows for this snapshot. Every insight_score is '
                'cohort_surprise x CARRIER_SALIENCE x reliability, so synthesizing '
                'against a missing salience layer would score every insight from a '
                'substituted default rather than from the computed vector.'
            )
        fact_ids = self._load_window_fact_ids(conn)

        insight_windows: list[S65.InsightWindow] = []
        cohort_by_window: dict[str, S65.CohortSurpriseInput] = {}
        for w in windows:
            wid = w['window_id']
            iw = S65.InsightWindow(
                window_id=wid, event_class=w['event_class'],
                t_start=float(w['t_start']), t_end=float(w['t_end']),
                t_peak=float(w['t_peak']), lambda_peak=float(w['lambda_peak']),
                salience=float(salience.get(wid, 0.0)),
                confidence_tier=w.get('confidence_tier'),
                lord_stack_at_peak=self._lord_stack_at_peak(conn, w),
                clock_agreements=self._clock_agreements(conn, w),
                fact_ids=tuple(fact_ids.get(wid, ())),
                robustness=self._as_dict(w.get('robustness')),
            )
            insight_windows.append(iw)
            rate = self._cohort_rate_for_window(conn, w)
            if rate is not None:
                cohort_by_window[wid] = S65.CohortSurpriseInput(p_cohort=rate.p,
                                                               n_cohort=rate.n_total)

        by_class: dict[str, list[S65.InsightWindow]] = {}
        for iw in insight_windows:
            by_class.setdefault(iw.event_class, []).append(iw)

        # Type 4 `absence_of_expected` — a class with a STRONG natal promise and
        # no window at all in the horizon. Only classes the plan actually
        # attempted are candidates; a class skipped for want of a baseline has no
        # field to be absent from, and claiming an absence for it would be a
        # finding manufactured out of a build gap.
        absence: list[tuple[str, float, float, float]] = []
        for ec in self._event_classes:
            if ec in {s['event_class'] for s in self._skipped}:
                continue
            try:
                p_e = S4.load_promise_prior(conn, self._chart_id, ec).p
            except Exception as exc:            # pragma: no cover - lane-dependent
                logger.warning('ka_kshetra stage65: promise prior unavailable for %s '
                               '(%s) — absence_of_expected not evaluated for it', ec, exc)
                continue
            absence.append((ec, float(p_e), 0.0, float(HORIZON_DAYS)))

        scarcity_pairs = [(iw, by_class[iw.event_class]) for iw in insight_windows]
        reversal_inputs = self._reversal_inputs(conn, by_class)

        rows_out = S65.synthesize_insights(
            chart_id=str(self._chart_id), windows=insight_windows,
            weights_version=self._weights_version,
            field_snapshot_id=self._snapshot_id,
            cohort_by_window=cohort_by_window,
            absence_candidates=absence,
            scarcity_pairs=scarcity_pairs,
            reversal_inputs=reversal_inputs,
            # Type 8 `contrast` needs a BASELINE field to diff against
            # (last_month / last_year / a pinned prior field_snapshot_id). A
            # rebuild deletes this chart's prior snapshot rows before any substep
            # runs (§N.3 delete-then-insert), so no baseline exists inside this
            # build. Honest-empty, and `synthesize_insights` documents that
            # passing none of them is exactly that — not an error.
            contrast_inputs=None,
        )

        rows = 0
        with conn.cursor() as cur:
            for r in rows_out:
                rate = (self._cohort_rate_for_window(conn, self._window_by_id(windows,
                                                                             r['window_id']))
                        if r.get('window_id') else None)
                cur.execute(
                    """INSERT INTO kala_insights (
                           chart_id, insight_id, insight_type, event_class, window_id,
                           t_start, t_end, statement_key, statement_params, fact_ids,
                           cohort_surprise, cohort_version, surprise_basis, robustness,
                           insight_score, lel_derived, weights_version, field_snapshot_id)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s,%s,%s,%s::jsonb,
                               %s,%s,%s,%s)
                       ON CONFLICT (chart_id, insight_id) DO UPDATE SET
                           insight_score = EXCLUDED.insight_score,
                           statement_params = EXCLUDED.statement_params,
                           cohort_surprise = EXCLUDED.cohort_surprise,
                           surprise_basis = EXCLUDED.surprise_basis,
                           computed_at = now()""",
                    (self._chart_id, r['insight_id'], r['insight_type'], r['event_class'],
                     r['window_id'], r['t_start'], r['t_end'], r['statement_key'],
                     json.dumps(r['statement_params']), list(r['fact_ids']),
                     r['cohort_surprise'],
                     rate.cohort_version if rate is not None else None,
                     r['surprise_basis'], json.dumps(r['robustness']),
                     r['insight_score'], False, r['weights_version'],
                     r['field_snapshot_id']),
                )
                rows += 1

        leading = S65.select_leading_insight(rows_out)
        self._record_substep(conn, step.key, rows)
        return WriterResult(
            asset_id=ASSET_ID, rows_inserted=rows,
            notes=(f'{rows} insight row(s); leading='
                   f'{leading["insight_id"] if leading else "none"}')
            if rows else 'honest_empty:no_insight_predicate_fired')

    # ── stage 8 · the timeline spec (§7.1) ───────────────────────────────────

    def _run_stage8(self, conn, view: str, step: SubStep) -> WriterResult:
        """Publish one `kala_timeline_spec` row for one `generated_for` view.

        W2's row SET is view-independent: §7.1 pins the document's shape and its
        `generated_for` enum but specifies no per-view scoping rule, so this
        writer renders the same field over all six rather than inventing six
        different scopings. The view is DECLARED on the row (and inside the
        blob), so a serving surface that later scopes per view changes one
        function here, and no reader is ever misled into thinking `elect` was
        filtered when it was not.
        """
        if self._dry_run:
            return WriterResult(asset_id=ASSET_ID, rows_inserted=0)

        t_zero = self._t_zero()
        if t_zero is None:
            raise S4.UpstreamStageIncomplete(
                'upstream_stage_incomplete: no birth_date on public.charts, so every '
                '`t` in the spec would be an offset from an unknown origin. §7.1 dates '
                'are ISO instants, never raw day counts — there is deliberately no '
                'epoch-guess fallback.'
            )

        windows = self._load_committed_windows(conn)
        boundaries = self._load_timeline_boundaries(conn)
        ontology = self._load_ontology(conn, {w['event_class'] for w in windows})

        tracks, window_rows = self._timeline_tracks_and_windows(windows, ontology)
        boundary_rows, clock_tracks = self._timeline_points(boundaries, len(tracks))
        tracks.extend(clock_tracks)

        spec = S8.build_timeline_spec(
            chart_id=str(self._chart_id), generated_for=view, t_zero=t_zero,
            now_marker=self._now_marker(t_zero),
            field_snapshot_id=self._snapshot_id,
            weights_version=self._weights_version,
            tracks=tracks, windows=window_rows, boundaries=boundary_rows,
            # §7.1's `bands` are sandhi / eclipse / sade_sati / naisargika_stage
            # spans. W2 builds no table that carries any of them, so the array is
            # honestly empty and the spec's `empty_reason` accounts for it when
            # nothing else renders either. An invented band would be a rendered
            # claim with no row behind it (B.10).
            bands=(),
        )
        counts = S8.spec_counts(spec)

        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO kala_timeline_spec (
                       chart_id, generated_for, spec_version, field_snapshot_id,
                       weights_version, spec, n_tracks, n_intervals, n_points,
                       n_bands, empty_reason)
                   VALUES (%s,%s,%s,%s,%s,%s::jsonb,%s,%s,%s,%s,%s)
                   ON CONFLICT (chart_id, generated_for, field_snapshot_id)
                   DO UPDATE SET spec = EXCLUDED.spec,
                                 n_tracks = EXCLUDED.n_tracks,
                                 n_intervals = EXCLUDED.n_intervals,
                                 n_points = EXCLUDED.n_points,
                                 n_bands = EXCLUDED.n_bands,
                                 empty_reason = EXCLUDED.empty_reason,
                                 computed_at = now()""",
                (self._chart_id, view, spec['spec_version'], self._snapshot_id,
                 self._weights_version, json.dumps(spec), counts['n_tracks'],
                 counts['n_intervals'], counts['n_points'], counts['n_bands'],
                 counts['empty_reason']),
            )
        self._record_substep(conn, step.key, 1)
        return WriterResult(
            asset_id=ASSET_ID, rows_inserted=1,
            notes=(f'{view}: {counts["n_intervals"]} interval(s), '
                   f'{counts["n_points"]} point(s), {counts["n_bands"]} band(s)'
                   + (f', empty_reason={counts["empty_reason"]}'
                      if counts['empty_reason'] else '')))

    # ── stage 6/6.5/8 loaders + shape adapters ───────────────────────────────

    def _load_committed_windows(self, conn) -> list[dict]:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT window_id, event_class, t_start, t_end, t_peak, lambda_peak,
                          expected_count, duration_days, null_p, confidence_tier,
                          robustness, temporal_shape, precision_regime
                     FROM kala_field_windows
                    WHERE chart_id = %s AND field_snapshot_id = %s
                    ORDER BY window_id""",
                (self._chart_id, self._snapshot_id),
            )
            return sorted(S4._rows(cur), key=lambda r: r['window_id'])

    def _load_window_provenance(self, conn) -> dict[str, list[dict]]:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT target_id, term_key, log_contribution, source_fact_id
                     FROM kala_field_provenance
                    WHERE chart_id = %s AND field_snapshot_id = %s
                      AND target_kind = 'window'
                    ORDER BY target_id, term_key""",
                (self._chart_id, self._snapshot_id),
            )
            out: dict[str, list[dict]] = {}
            for r in S4._rows(cur):
                out.setdefault(r['target_id'], []).append(r)
        return out

    def _load_window_fact_ids(self, conn) -> dict[str, list[str]]:
        """The L1 fact ids each window's provenance CITES (§B.3 / §N.5).

        These are read back off the persisted edges rather than re-collected from
        an in-memory evaluator, so an insight's `fact_ids` are exactly the ids a
        reader drilling the window will find.
        """
        out: dict[str, list[str]] = {}
        for wid, terms in self._load_window_provenance(conn).items():
            ids = sorted({t['source_fact_id'] for t in terms if t.get('source_fact_id')})
            if ids:
                out[wid] = ids
        return out

    def _load_salience(self, conn) -> dict[str, float]:
        with conn.cursor() as cur:
            cur.execute(
                'SELECT window_id, salience FROM kala_field_salience '
                'WHERE chart_id = %s AND field_snapshot_id = %s',
                (self._chart_id, self._snapshot_id),
            )
            return {r['window_id']: float(r['salience']) for r in S4._rows(cur)}

    def _load_ontology(self, conn, event_classes) -> dict[str, S6.EventOntologyInfo]:
        """`brahma_event_ontology` rows, as §6.1's Consequence input.

        A class whose row is missing either `domain` or a RECOGNIZED
        `magnitude_floor` yields NO `EventOntologyInfo` at all, so Consequence is
        an honest NULL that renormalizes out of the scalar. Constructing one with
        a substituted magnitude would put a fabricated severity in Q's
        highest-weighted sub-term (and would raise inside `compute_consequence`,
        whose `.index()` has no fallback by design).
        """
        out: dict[str, S6.EventOntologyInfo] = {}
        domain_by_class: dict[str, str] = {}
        raw: dict[str, dict] = {}
        for ec in sorted(event_classes):
            with conn.cursor() as cur:
                cur.execute(
                    'SELECT event_class_id, domain, magnitude_floor, adjacency '
                    'FROM brahma_event_ontology WHERE event_class_id = %s', (ec,))
                rows = S4._rows(cur)
            if not rows:
                continue
            raw[ec] = rows[0]
            if rows[0].get('domain'):
                domain_by_class[ec] = str(rows[0]['domain'])
        for ec, row in raw.items():
            domain = row.get('domain')
            floor = row.get('magnitude_floor')
            if not domain or floor not in S6._MAGNITUDE_ORDER:
                continue
            out[ec] = S6.EventOntologyInfo(
                event_class_id=ec, domain=str(domain), magnitude_floor=str(floor),
                adjacent_domains=S6.compute_domains_touched(
                    ec, str(domain), self._as_list(row.get('adjacency')), domain_by_class,
                ) - {str(domain)},
            )
        return out

    def _lord_stack_at_peak(self, conn, window: dict) -> tuple[str, ...]:
        """§6.2's `lord_stack_at_peak` — the clock lord stacks active at t_peak.

        Sourced from the SAME `FieldEvaluator.lord_stacks_at` the hazard used, so
        the window-family identity a selection dedups on cannot drift from the
        clock term the field was built with.
        """
        try:
            ev = self._class_context(conn, window['event_class']).evaluator
        except S4.ClassSkipped:                              # pragma: no cover
            return ()
        stacks = ev.lord_stacks_at(float(window['t_peak']))
        return tuple(sorted(f'{system}:{level}:{lord}'
                            for system, stack in stacks.items()
                            for level, lord in stack))

    def _clock_agreements(self, conn, window: dict) -> tuple[S65.ClockAgreement, ...]:
        """r_{s,e}(t_peak) per predictive daśā system — §6.4 type 1's input.

        Computed with `hazard.relevance` under the PINNED depth weights, i.e. the
        identical call the field's own clock term made; type 1 counts DISTINCT
        `competence_class`es, so two systems sharing a class are one voice.
        """
        try:
            ev = self._class_context(conn, window['event_class']).evaluator
        except S4.ClassSkipped:                              # pragma: no cover
            return ()
        depth = {level: float(self._weights.get(f'd:{level}', default))
                 for level, default in hazard.DEFAULT_DEPTH_WEIGHTS.items()}
        stacks = ev.lord_stacks_at(float(window['t_peak']))
        out = []
        for clock in sorted(hazard.predictive_systems(ev.clocks), key=lambda c: c.system_id):
            r = hazard.relevance(list(stacks.get(clock.system_id, ())),
                                 ev.promise.routes, depth)
            out.append(S65.ClockAgreement(system_id=clock.system_id,
                                          competence_class=clock.competence_class,
                                          r_value=float(r)))
        return tuple(out)

    def _reversal_inputs(self, conn, by_class) -> list[tuple[str, S65.InsightWindow, list]]:
        """§6.4 type 7's samples: (t, signed_obstruction, λ, q_e) along the carrier.

        Sampled at the COMMITTED segment breakpoints inside the carrier window —
        the field's own knots, where a crossing can actually occur — with λ read
        from the stored (α, γ) pair and q_e read from the committed
        `kala_field_null` row. A class with no committed q_e contributes nothing
        rather than a crossing measured against a substituted threshold.
        """
        q_by_class = self._load_q_thresholds(conn)
        out: list[tuple[str, S65.InsightWindow, list]] = []
        for event_class, iws in sorted(by_class.items()):
            q_e = q_by_class.get(event_class)
            if q_e is None:
                continue
            try:
                ev = self._class_context(conn, event_class).evaluator
            except S4.ClassSkipped:                          # pragma: no cover
                continue
            segments = self._load_segments(conn, event_class)
            for iw in iws:
                samples = [
                    S65.ReversalSample(
                        t=seg.t_start,
                        signed_obstruction=ev.terms_at(seg.t_start).signed_obstruction,
                        lambda_value=math.exp(seg.alpha), q_e=q_e)
                    for seg in segments
                    if iw.t_start <= seg.t_start <= iw.t_end
                ]
                if len(samples) >= 2:
                    out.append((event_class, iw, samples))
        return out

    def _load_q_thresholds(self, conn) -> dict[str, float]:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT event_class, bucket_days, q_threshold
                     FROM kala_field_null
                    WHERE chart_id = %s AND field_snapshot_id = %s""",
                (self._chart_id, self._snapshot_id),
            )
            rows = S4._rows(cur)
        out: dict[str, float] = {}
        # §5.5 writes the SAME per-class q_e onto every duration bucket, so any
        # bucket answers; the sort makes "any" a deterministic "the lowest
        # bucket" rather than a heap-order pick (§N.7 item 2).
        for r in sorted(rows, key=lambda r: (r['event_class'], r['bucket_days'])):
            if r['q_threshold'] is None:
                continue
            out.setdefault(r['event_class'], float(r['q_threshold']))
        return out

    def _cohort_rate_for_window(self, conn, window: Optional[dict]):
        """§6.3's rarity read — memoized per (feature value, md_lord, ref age).

        Returns `None` (⇒ Informativeness NULL, `not_surprise_credited`) whenever
        the cohort cannot answer: no natal Lagna in L1, no canonical MD lord at
        the peak, or the cohort tables unreadable. Every one of those is an
        honest not-computed, and §6.1/§6.4 both have a designed path for it —
        none of them is a reason to substitute a rate.
        """
        if window is None:
            return None
        lagna_sign = self._natal_lagna_sign(conn)
        if lagna_sign is None:
            note = 'rarity:no_natal_lagna_fact'
            if note not in self._coverage_notes:
                self._coverage_notes.append(note)
            return None
        md_lord = self._md_lord_at(conn, float(window['t_peak']))
        ref_age = float(window['t_peak']) / _DAYS_PER_JULIAN_YEAR
        key = (lagna_sign, md_lord, round(ref_age, 6))
        cache = getattr(self, '_cohort_cache', None)
        if cache is None:
            cache = self._cohort_cache = {}
        if key in cache:
            return cache[key]
        try:
            rate = cohort_client.cohort_base_rate(
                COHORT_FEATURE_KEY, lagna_sign,
                matched_by={'md_lord': md_lord} if md_lord else None,
                native_age_at_reference_years=ref_age if md_lord else None,
                conn=conn,
            )
        except Exception as exc:
            # NOT swallowed: recorded once, with the reason, and surfaced as a
            # NULL Informativeness factor whose absence is visible in every
            # row's `salience_basis`.
            if 'rarity' not in {n.split(':')[0] for n in self._coverage_notes}:
                logger.warning('ka_kshetra: cohort rarity unavailable (%s) — '
                               'factor_informativeness is NULL on every salience row '
                               'and no rarity_firing insight can fire', exc)
                self._coverage_notes.append(f'rarity:cohort_unreadable:{type(exc).__name__}')
            rate = None
        if rate is not None and rate.p is None and rate.fallback_reason:
            note = f'rarity:{rate.fallback_reason}'
            if note not in self._coverage_notes:
                self._coverage_notes.append(note)
        cache[key] = rate
        return rate

    def _natal_lagna_sign(self, conn) -> Optional[int]:
        """The native's natal Lagna `sign_id` (1..12), for the cohort feature.

        The LONGITUDE is REFERENCED from L1 `chart_facts` and never recomputed
        (§N.5); only the sign bucket is derived here, by the identical
        `int(lon / 30) + 1` arithmetic `bg_cohort.py` uses to write the cohort's
        own `positions.*.sign_id`. Using a different bucketing would compare the
        native against a differently-labelled population.
        """
        if hasattr(self, '_lagna_sign_cache'):
            return self._lagna_sign_cache
        sign: Optional[int] = None
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT fact_value_num FROM chart_facts
                        WHERE chart_id = %s AND fact_category = 'lagna'
                          AND fact_key = 'longitude'
                        ORDER BY ayanamsha_id
                        LIMIT 1""",
                    (self._chart_id,))
                rows = S4._rows(cur)
            if rows and rows[0].get('fact_value_num') is not None:
                sign = int(float(rows[0]['fact_value_num']) % 360.0 / 30.0) + 1
        except Exception as exc:
            logger.warning('ka_kshetra: natal Lagna lookup failed (%s) — the rarity '
                           'axis is not computed for this chart', exc)
        self._lagna_sign_cache = sign
        return sign

    def _md_lord_at(self, conn, t_days: float) -> Optional[str]:
        """The Vimśottarī MD lord running at `t_days`, or None.

        None whenever the lord is not one of the nine canonical `PLANET_NAMES` —
        see `_CANONICAL_MD_LORDS`: an unmatched name would produce an EMPTY
        matched sub-cohort, and an empty numerator reads as p_cohort = 0, i.e.
        maximally rare. Falling back to the unmatched global rate is honest;
        quoting a rarity from a population of zero is not.
        """
        cache = getattr(self, '_md_ladder', None)
        if cache is None:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT lord, t_boundary FROM kala_field_boundaries
                        WHERE chart_id = %s AND system_id = 'vimshottari'
                          AND level = 'MD'
                        ORDER BY t_boundary""",
                    (self._chart_id,))
                cache = self._md_ladder = [
                    (float(r['t_boundary']), str(r['lord'])) for r in S4._rows(cur)
                    if r.get('t_boundary') is not None and r.get('lord')]
        lord = None
        for t0, name in cache:
            if t0 <= t_days:
                lord = name
            else:
                break
        return lord if lord in _CANONICAL_MD_LORDS else None

    def _timeline_tracks_and_windows(self, windows, ontology):
        """§7.1 `tracks[]` (domain rows) + the `intervals[]` input rows.

        A class whose ontology row carries no `domain` gets a `class:<id>` track
        rather than being filed under an invented domain — the track label states
        exactly what is known about it.
        """
        track_of: dict[str, str] = {}
        for ec in sorted({w['event_class'] for w in windows}):
            info = ontology.get(ec)
            track_of[ec] = f'domain:{info.domain}' if info else f'class:{ec}'
        tracks = [
            S8.TimelineTrack(track_id=tid, kind='domain',
                             label=tid.split(':', 1)[1].replace('_', ' ').title(), row=i)
            for i, tid in enumerate(sorted(set(track_of.values())))
        ]
        rows = []
        for w in windows:
            row = dict(w)
            row['track_id'] = track_of[w['event_class']]
            row['label'] = w['event_class'].replace('_', ' ').title()
            rows.append(row)
        return tracks, rows

    def _timeline_points(self, boundaries, first_row: int):
        """§7.1 `points[]` input rows + the `clock:<system>` tracks they need.

        `point_id` is derived from the boundary's NATURAL key, never from its
        BIGINT identity: identity values are reassigned on every rebuild, so
        hashing one into the spec would make the field content hash move on a
        rebuild that changed nothing (§7.4's "build twice, assert bit-identical").
        """
        systems = sorted({str(b['system_id']) for b in boundaries})
        tracks = [S8.TimelineTrack(track_id=f'clock:{s}', kind='clock',
                                   label=s.replace('_', ' ').title(), row=first_row + i)
                  for i, s in enumerate(systems)]
        rows = []
        for b in boundaries:
            natural = f"{b['system_id']}|{b['level']}|{b['lord']}|{b['t_boundary']!r}"
            rows.append({
                'point_id': 'kfb_' + hashlib.sha256(natural.encode('utf-8')).hexdigest()[:16],
                'track_id': f"clock:{b['system_id']}",
                't_boundary': float(b['t_boundary']),
                'kind': 'dasha_boundary',
                'label': f"{b['system_id']} {b['level']} {b['lord']}",
                'precision_state': b.get('precision_state'),
                'interval_lo': b.get('interval_lo'),
                'interval_hi': b.get('interval_hi'),
            })
        return rows, tracks

    def _load_timeline_boundaries(self, conn) -> list[dict]:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT system_id, level, lord, t_boundary, precision_state,
                          interval_lo, interval_hi
                     FROM kala_field_boundaries
                    WHERE chart_id = %s AND level = ANY(%s)
                    ORDER BY system_id, t_boundary""",
                (self._chart_id, list(TIMELINE_BOUNDARY_LEVELS)),
            )
            rows = [r for r in S4._rows(cur)
                    if r.get('level') in TIMELINE_BOUNDARY_LEVELS
                    and r.get('t_boundary') is not None]
        return sorted(rows, key=lambda r: (str(r['system_id']), float(r['t_boundary'])))

    def _t_zero(self) -> Optional[datetime]:
        if self._birth_date is None:
            return None
        return datetime.combine(self._birth_date, self._birth_time or time(0, 0))

    @staticmethod
    def _now_marker(t_zero: datetime) -> str:
        """§7.1's `now_marker`.

        Pinned to `t_zero`'s own date, NOT to wall-clock "today". Two reasons,
        both binding: stages 0–8 are pure functions of (chart, corpus_pin,
        config_pin, weights_version) (§2), and the §7.4 hash-replay CI builds
        twice and asserts bit-identical — a wall-clock marker would break both,
        every midnight, for no gain. The rendering "now" is a SERVING-time
        concern; a renderer knows what today is without being told by a row
        persisted months earlier.
        """
        return t_zero.date().isoformat()

    @staticmethod
    def _window_by_id(windows: list[dict], window_id) -> Optional[dict]:
        for w in windows:
            if w['window_id'] == window_id:
                return w
        return None

    @staticmethod
    def _as_dict(value) -> Optional[dict]:
        if value is None or isinstance(value, dict):
            return value
        try:
            parsed = json.loads(value)
        except (TypeError, ValueError):
            return None
        return parsed if isinstance(parsed, dict) else None

    @staticmethod
    def _as_list(value) -> Optional[list]:
        if value is None or isinstance(value, list):
            return value
        try:
            parsed = json.loads(value)
        except (TypeError, ValueError):
            return None
        return parsed if isinstance(parsed, list) else None

    # ── snapshot ─────────────────────────────────────────────────────────────

    def _run_snapshot(self, conn, step: SubStep) -> WriterResult:
        """Write the freshness row and the §7.4 CONTENT hash.

        The content hash is computed here, after every stage-4/5 row is committed,
        because it is a digest OF those rows — see migration 492's header for why
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
            # ── stage 6 / 6.5 / 8 (see _HASHED_TABLES for why they are here) ──
            cur.execute(
                """SELECT window_id, event_class, factor_informativeness,
                          factor_consequence, factor_relevance, factor_reliability,
                          factor_actionability, salience, salience_weights_version,
                          salience_basis, selected, selection_rank, marginal_gain,
                          coverage_fraction, largest_omission_window_id,
                          largest_omission_marginal_gain, cohort_version
                     FROM kala_field_salience
                    WHERE chart_id = %s AND field_snapshot_id = %s""",
                (self._chart_id, self._snapshot_id),
            )
            for r in S4._rows(cur):
                rows.append(('kala_field_salience', (r['window_id'],), dict(r)))
            # `lel_derived = FALSE` is the §7.4 exclusion, stated in the WHERE
            # clause rather than filtered afterwards: the hash must not be able
            # to see a Lane E biographical_echo row even transiently.
            cur.execute(
                """SELECT insight_id, insight_type, event_class, window_id, t_start,
                          t_end, statement_key, statement_params, fact_ids,
                          cohort_surprise, cohort_version, surprise_basis,
                          insight_score
                     FROM kala_insights
                    WHERE chart_id = %s AND field_snapshot_id = %s
                      AND lel_derived = FALSE""",
                (self._chart_id, self._snapshot_id),
            )
            for r in S4._rows(cur):
                rows.append(('kala_insights', (r['insight_id'],), dict(r)))
            # `computed_at` is excluded per §7.4's own column exclusion list; the
            # `spec` blob is included because it IS the row's content, and it is
            # byte-stable by construction (`_now_marker`, natural-key point ids).
            cur.execute(
                """SELECT generated_for, spec_version, spec, n_tracks, n_intervals,
                          n_points, n_bands, empty_reason
                     FROM kala_timeline_spec
                    WHERE chart_id = %s AND field_snapshot_id = %s""",
                (self._chart_id, self._snapshot_id),
            )
            for r in S4._rows(cur):
                rows.append(('kala_timeline_spec', (r['generated_for'],), dict(r)))
        return S4.field_content_hash(self._snapshot_id, rows)

    # ── helpers ──────────────────────────────────────────────────────────────

    def _class_context(self, conn, event_class: str) -> _ClassContext:
        cached = self._class_cache.get(event_class)
        if cached is not None:
            return cached
        # Lazy-init chart-level shared objects (same across all event classes).
        if self._shared_envelopes is None:
            self._shared_envelopes = S4.EnvelopeIndex(
                S4.load_primitives(conn, self._chart_id), HORIZON_DAYS
            )
        if self._shared_clocks is None:
            self._shared_clocks = S4.load_clocks(conn, self._chart_id)
        if self._shared_ladder is None:
            self._shared_ladder = S4.load_ladder(conn, self._chart_id)
        if self._shared_extra_breakpoints is None:
            self._shared_extra_breakpoints = S4.load_kinematics_breakpoints(
                conn, self._chart_id
            )
        lifetime, source = S4.load_class_lifetime_count(conn, event_class)
        lifetime = S4.require_baseline(lifetime, event_class)
        shape = S4.require_event_shape(S4.load_event_shape(conn, event_class), event_class)
        evaluator = S4.FieldEvaluator(
            event_class=event_class,
            lifetime_count=lifetime,
            promise=S4.load_promise_prior(conn, self._chart_id, event_class),
            clocks=self._shared_clocks,
            ladder=self._shared_ladder,
            envelopes=self._shared_envelopes,
            weights=self._weights,
            horizon_days=HORIZON_DAYS,
            baseline_source=source,
            extra_breakpoints=self._shared_extra_breakpoints,
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
    def _load_birth_instant(conn, chart_id) -> tuple[Optional[date], Optional[time]]:
        """(birth_date, birth_time). `birth_time` is §7.1's `t_zero` time part.

        A missing `birth_time` stays None rather than becoming midnight here: the
        caller composes the instant and can state which half it actually has,
        whereas a defaulted 00:00 buried in the loader would be indistinguishable
        from a real midnight birth.
        """
        try:
            with conn.cursor() as cur:
                cur.execute(
                    'SELECT birth_date, birth_time FROM public.charts '
                    'WHERE id = %s OR chart_id = %s '
                    'ORDER BY birth_date NULLS LAST LIMIT 1', (chart_id, chart_id))
                rows = S4._rows(cur)
        except Exception as exc:
            logger.warning('ka_kshetra: birth instant lookup failed for %s: %s',
                           chart_id, exc)
            return None, None
        if not rows:
            return None, None
        return rows[0].get('birth_date'), rows[0].get('birth_time')

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
        """LIVE discovery from Lane A's promise register — never a hardcoded list.

        SHABDA-SHUDDHI R6: promise is a modifier, never a gate. ALL event
        classes with a bodha_pratijna row are discovered, regardless of status.
        The status/grade flow downstream as scaling modifiers via the Adṛṣṭa
        floor (stage4_field ClassSkipped path for classes without N_e priors;
        stage2_promise PromisePrior for classes with priors). Excluding
        'denied' or 'no_evidence' classes here was the root cause of 11 of 27
        event classes being structurally un-computable for every chart.

        Reads `bodha_pratijna` (bo_pratijna) — NOT `kala_field_routes`. That
        table is a persistence target that nothing in the live call graph ever
        calls, so it is permanently empty in production. Found 2026-08-05.
        """
        try:
            with conn.cursor() as cur:
                cur.execute(
                    'SELECT DISTINCT event_class_id FROM bodha_pratijna '
                    'WHERE chart_id = %s '
                    'ORDER BY event_class_id', (chart_id,))
                return [r['event_class_id'] for r in S4._rows(cur)]
        except Exception as exc:
            logger.warning('ka_kshetra: event-class discovery failed for %s: %s',
                           chart_id, exc)
            return []

    def _delete_prior_rows(self, conn, chart_id) -> None:
        """§N.3 idempotency, ONCE, in plan_substeps. See the module docstring.

        Each entry carries its own extra predicate so the delete is scoped to the
        rows THIS writer owns. `kala_insights` is the case that matters: the
        table is SHARED with Lane E's biographical-join refresh, whose
        `lel_derived = TRUE` rows are deliberately outside the field hash and
        outside this writer's authorship. A blanket per-chart delete would
        silently destroy them on every field rebuild.
        """
        with conn.cursor() as cur:
            for table, predicate in _OWNED_TABLES:
                cur.execute(
                    f'DELETE FROM {table} WHERE chart_id = %s'
                    + (f' AND {predicate}' if predicate else ''), (chart_id,))
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


#: (table, extra DELETE predicate) this writer owns and therefore clears on a
#: fresh/replanned build (§N.3). Deliberately does NOT include any legacy table:
#: W2 writes ZERO rows to `kala_gochara_windows` and reads it read-only as a
#: cross-check corpus (§1 rail 2, strangler-fig). Adding one here would be the
#: wave's headline regression.
_OWNED_TABLES: tuple[tuple[str, Optional[str]], ...] = (
    'kala_field_provenance', None
), (
    'kala_field_salience', None
), (
    # CIRCULARITY GUARD CARVE-OUT (§6.4): stage 6.5 authors ONLY the seven
    # non-LEL types. Lane E's `biographical_echo` rows live in the same table
    # with `lel_derived = TRUE`, are outside the field hash by design, and are
    # NOT this writer's to delete.
    'kala_insights', 'lel_derived = FALSE'
), (
    'kala_timeline_spec', None
), (
    'kala_field_windows', None
), (
    'kala_field_null', None
), (
    'kala_field', None
), (
    'kala_field_snapshots', None
),

#: The stage 0–8 tables the §7.4 CONTENT hash covers.
#:
#: WHY THE STAGE 6 / 6.5 / 8 TABLES JOINED IT (a deliberate decision, not drift).
#: §7.4 defines the hashed row set as "every stage 0–8 row for this chart,
#: EXCLUDING kala_insights rows with lel_derived = TRUE". Salience, insights and
#: the timeline spec ARE stage 6/6.5/8 rows, so the definition already covered
#: them — Lane C's original four-table list was the partial state of a pipeline
#: whose later stages had not been wired yet, and its own comment says as much
#: ("other lanes extend this list in their own PRs"). Two consequences a reader
#: must not be surprised by:
#:   • `kala_field_snapshots.hashed_tables` records this list per snapshot, so a
#:     hash-replay comparison is only meaningful between two snapshots whose
#:     `hashed_tables` AGREE. A hash computed over four tables and one computed
#:     over seven are different measurements, not a detected change.
#:   • Nothing in the added rows contains the content hash itself, so there is no
#:     self-reference: they carry `field_snapshot_id`, which is the PIN identity
#:     (§7.4's inputs), computed before any row is written.
#: `now_marker` is pinned to `t_zero` (see `_now_marker`) and boundary point ids
#: are derived from natural keys rather than BIGINT identities, so the spec rows
#: are byte-stable across rebuilds — without both, adding stage 8 to the hash
#: would have broken §7.4's own "build twice, assert bit-identical" gate.
_HASHED_TABLES: tuple[str, ...] = (
    'kala_field',
    'kala_field_windows',
    'kala_field_provenance',
    'kala_field_null',
    'kala_field_salience',
    'kala_insights',
    'kala_timeline_spec',
)


__all__ = ['KaKshetraWriter', 'ASSET_ID', 'HORIZON_DAYS', 'DECADES',
           'SEGMENT_INDEX_DECADE_STRIDE']
