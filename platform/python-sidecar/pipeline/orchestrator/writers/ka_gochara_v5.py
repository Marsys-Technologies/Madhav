"""ka_gochara_v5 — Pravāha A5.3: the '5.0' gochara writer SKELETON.

INERT BY DESIGN (campaign item A5.3, step writerbase_conformance, PARTIAL;
steward ruling M20261001T014547-357e pins 1-2). This module is the registered
skeleton ONLY: it conforms to the frozen WriterBase contract, is discoverable
via @register, hard-refuses every chart other than the pinned candidate chart,
and every execution path then raises NotImplementedError. The geometry/solver
work is explicitly BLOCKED pending steward pins 3-7 — no astrology is
implemented here, and none may land in this module before that ruling.

Mirrors the PR #2799 inert-candidate pattern (ka_gochara_v4_41_candidate):
  * @register('ka_gochara_v5') on a WriterBase subclass, asset_id pinned.
  * Chart-scope refusal: any chart_id ≠ PINNED_CHART_ID raises ChartRefusal
    BEFORE any planning or execution (fail-closed; never a silent no-op).
  * Every execution path (run / plan_substeps / the inherited run_substep,
    which delegates to run) raises
    NotImplementedError("A5.3: geometry/solver pending steward pins 3-7")
    AFTER the chart-scope check.
  * ctx.dry_run: the template (ka_gochara_v4_41_candidate) carries no dry_run
    branch — and this skeleton goes further: since NO execution path exists
    yet, dry_run=True changes nothing; the NotImplementedError still raises.
    There is no write path to suppress, so there is nothing for dry_run to
    skip.
  * Never commits/rolls back/closes ctx.db_conn; never opens a connection;
    never writes asset_throughput (there is no DB touch at all).
  * Registry row: asset_registry_seed.ts with is_active=false (inert to
    runPreparation's planning set and recalibrationEnqueue's writer sweep) —
    same mechanism as PR #2799, no migration. Pins admission (digests /
    analysis-layer pins / capability census) is a separate governed step and
    is deliberately NOT part of this change.

FROZEN ORCHESTRATOR CONTRACT (§N.2)
------------------------------------
  * @register('ka_gochara_v5') on a WriterBase subclass
  * LIGHT shape: run(ctx) implemented; plan_substeps(ctx) overridden only to
    keep the chart-scope refusal on the planning path too
  * ctx.db_conn — never touched at all in this skeleton
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

logger = logging.getLogger(__name__)

ASSET_ID = "ka_gochara_v5"

# Pravāha A5.3 inherits the A2.5 one-chart discipline (steward dispatch
# CHART_ID): a candidate-generation writer must never be plannable for an
# arbitrary chart. The skeleton hard-refuses any other chart BEFORE any
# planning or execution — fail-closed, never a silent no-op.
PINNED_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"

PENDING_MESSAGE = "A5.3: geometry/solver pending steward pins 3-7"


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
    """Pravāha A5.3 INERT skeleton: registered, chart-scoped, no execution.

    See the module docstring. Every execution path raises NotImplementedError
    after the chart-scope check; the geometry/solver lands only after steward
    pins 3-7.
    """

    asset_id = ASSET_ID
    has_substeps = False

    # No delegated modules yet (the template's source_paths surface is unused
    # here — nothing to delegate to until pins 3-7).

    def plan_substeps(self, ctx: ContextSpec) -> list[SubStep]:
        """Chart-scope refusal on the planning path, then the pending gate.

        The orchestrator calls plan_substeps before any sub-step runs, so the
        refusal must live here too — a foreign chart is refused at PLAN time,
        not first at execution time."""
        _require_pinned_chart(ctx.config["chart_id"])
        raise NotImplementedError(PENDING_MESSAGE)

    def run(self, ctx: ContextSpec) -> WriterResult:
        """Chart-scope refusal, then the pending gate.

        No DB touch of any kind: ctx.db_conn is never read, written,
        committed, rolled back or closed, and no connection is opened.
        ctx.dry_run changes nothing — there is no write path to suppress."""
        _require_pinned_chart(ctx.config["chart_id"])
        raise NotImplementedError(PENDING_MESSAGE)
