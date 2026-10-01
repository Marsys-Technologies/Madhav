"""ka_gochara_v5 — Pravāha A5.3: the '5.0' gochara writer.

PHASE 1 (geometry_store) LANDED: substeps `convention` → `body:<Body>` ×8
build the §6.1 sky-event substrate (boundary events per body over the pinned
convention domain, stations always swiss_refined) via
services/gochara_kernel/substrate.py, under the implementation pins
(steward 2026-10-01, M20261001T015412-6df0; brief
A5_3_REGISTERED_WRITER_BRIEF_v1_0.md). Moon is excluded from the materialised
substrate (pin 6: EPHEMERAL, moon_on_demand). Later steps (rule_binding,
window_evaluator, interval_sweep, day_on_demand) extend this plan; the spec
text folds the pins into v1.5 at the A5.5 Codex gate.

Discipline (unchanged from the skeleton):
  * @register('ka_gochara_v5') on a WriterBase subclass, asset_id pinned.
  * Chart-scope refusal: any chart_id ≠ PINNED_CHART_ID raises ChartRefusal
    BEFORE any planning or execution (fail-closed; never a silent no-op).
  * Every write rides ctx.db_conn — never committed, rolled back or closed
    here; no other connection is ever opened.
  * The chart family key (ka_gochara_lock_chart) is taken before any
    substrate write (steward ruling B / N13 substrate order).
  * Candidate-only: nothing here publishes, seals or flips a generation.
  * Registry row: asset_registry_seed.ts with is_active=false (inert to
    runPreparation's planning set and recalibrationEnqueue's writer sweep) —
    same mechanism as PR #2799, no migration. Pins admission (digests /
    analysis-layer pins / capability census) is a separate governed step and
    is deliberately NOT part of this change.

FROZEN ORCHESTRATOR CONTRACT (§N.2)
------------------------------------
  * @register('ka_gochara_v5') on a WriterBase subclass
  * SUBSTEP shape: plan_substeps(ctx) static (convention → body ×8);
    run_substep(ctx, step) per pin-5 grain; run(ctx) inherited (aggregates)
  * ctx.db_conn — writes only inside the orchestrator's transaction
  * never writes asset_throughput
"""
from __future__ import annotations

import logging

from pipeline.orchestrator.writers import (
    ContextSpec,
    SubStep,
    WriterBase,
    WriterResult,
    register,
)
from services.gochara_kernel.substrate import SUBSTRATE_BODIES, SkyEventStore

logger = logging.getLogger(__name__)

ASSET_ID = "ka_gochara_v5"

CONVENTION_SUBSTEP = "convention"
BODY_SUBSTEP_PREFIX = "body:"

# Pravāha A5.3 inherits the A2.5 one-chart discipline (steward dispatch
# CHART_ID): a candidate-generation writer must never be plannable for an
# arbitrary chart. The skeleton hard-refuses any other chart BEFORE any
# planning or execution — fail-closed, never a silent no-op.
PINNED_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"


class ChartRefusal(Exception):
    """ctx.config['chart_id'] is not the pinned A5.3 candidate chart — refused
    BEFORE any planning or execution (fail-closed; never a silent no-op)."""


def _require_pinned_chart(chart_id: str) -> None:
    if chart_id != PINNED_CHART_ID:
        raise ChartRefusal(
            f"{ASSET_ID}: chart_id {chart_id!r} is not the pinned A5.3 "
            f"candidate chart {PINNED_CHART_ID} — refusing (fail-closed; "
            "this asset is inert to all planners and admits no execution "
            "surface until steward pins 3-7 land)")


@register(ASSET_ID)
class GocharaV5Writer(WriterBase):
    """Pravāha A5.3: the '5.0' writer — phase-1 geometry store landed.

    Chart-scoped (fail-closed) and substep-grained per pin 5: `convention`
    then `body:<Body>` ×8 (Moon excluded — pin 6 EPHEMERAL). Later steps
    (rule_binding, window_evaluator, interval_sweep, day_on_demand) extend
    the plan; nothing here flips or publishes anything."""

    asset_id = ASSET_ID
    has_substeps = True

    # No delegated modules yet (the template's source_paths surface is unused
    # here — nothing to delegate to until pins 3-7).

    def plan_substeps(self, ctx: ContextSpec) -> list[SubStep]:
        """Phase-1 plan (pin 5): 'convention' → 'body:<Body>' ×8.

        Static by design: the convention vector and the 8-body substrate set
        are pinned constants (Moon excluded — EPHEMERAL per pin 6). The
        chart-scope refusal lives here too — a foreign chart is refused at
        PLAN time, not first at execution time."""
        _require_pinned_chart(ctx.config["chart_id"])
        steps = [SubStep(key=CONVENTION_SUBSTEP,
                         label="§6.1 convention row (pin 3: idempotent under the chart lock)")]
        steps.extend(
            SubStep(key=f"{BODY_SUBSTEP_PREFIX}{body}",
                    label=f"phase-1 boundary substrate + stations: {body}")
            for body in SUBSTRATE_BODIES
        )
        return steps

    def run_substep(self, ctx: ContextSpec, step: SubStep) -> WriterResult:
        """Phase-1 geometry store (pin 5 grain: per-body boundary substrate).

        Every write rides ctx.db_conn — never committed, rolled back or
        closed here, and no other connection is opened. The chart family key
        is taken first (substrate order, steward ruling B / N13): the
        substrate chart-lock trigger refuses any write without it.
        ctx.dry_run suppresses the solve AND the write (there is nothing to
        stage)."""
        chart_id = ctx.config["chart_id"]
        _require_pinned_chart(chart_id)
        if step.key != CONVENTION_SUBSTEP and not step.key.startswith(BODY_SUBSTEP_PREFIX):
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                notes=f"unknown substep {step.key!r}")
        if ctx.dry_run:
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                notes=f"dry_run: {step.key} not solved, nothing written")
        self._take_chart_lock(ctx, chart_id)
        if step.key == CONVENTION_SUBSTEP:
            store = SkyEventStore(ctx.db_conn)
            cid = store.register_convention()
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                notes=f"convention {cid[:24]}… registered (idempotent)")
        body = step.key[len(BODY_SUBSTEP_PREFIX):]
        if body not in SUBSTRATE_BODIES:
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                notes=f"unknown body substep {step.key!r}")
        ephe_path = ctx.config.get("ephe_path")
        store = SkyEventStore(ctx.db_conn)
        counts = store.build_boundary_substrate(body, ephe_path=ephe_path)
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=counts["events"] + counts["stations"],
            notes=(f"{body}: {counts['events']} boundary events + "
                   f"{counts['stations']} stations over {counts['objects']} "
                   "physical objects (idempotent insert-if-absent)"))

    # ------------------------------------------------------------------

    @staticmethod
    def _take_chart_lock(ctx: ContextSpec, chart_id: str) -> None:
        """Steward ruling B / N13 substrate order: the chart family key
        precedes every substrate tuple. ka_gochara_lock_chart takes the
        xact-scoped advisory lock AND marks gochara5.chart_locked so the
        statement-level trigger admits the following writes."""
        ctx.db_conn.execute(
            "SELECT public.ka_gochara_lock_chart(%s::uuid)", (chart_id,)
        )
