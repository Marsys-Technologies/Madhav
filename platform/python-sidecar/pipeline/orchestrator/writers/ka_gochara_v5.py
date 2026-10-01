"""ka_gochara_v5 — Pravāha A5.3: the '5.0' gochara writer.

PHASE 1 (geometry_store) LANDED: substeps `convention` → `body:<Body>` ×8
build the §6.1 sky-event substrate (boundary events per body over the pinned
convention domain, stations always swiss_refined) via
services/gochara_kernel/substrate.py, under the implementation pins
(steward 2026-10-01, M20261001T015412-6df0; brief
A5_3_REGISTERED_WRITER_BRIEF_v1_0.md). Moon is excluded from the materialised
substrate (pin 6: EPHEMERAL, moon_on_demand).

STEP rule_binding LANDED: the `rules` substep (FIRST in the plan) binds
Stream B's P1–P5 rule catalogue (rule_version 1.0.0) into migration 1154's
registry tables — predicates, factors, paths, composite membership, F3 seals
— via services/gochara_kernel/rule_registry.py, under the Gochara-5 GLOBAL
family key with NO chart lock in this substep (N13 mutual exclusion). P6 and
sad_bala_summary are deferred (rule_registry.py D1/D2). Later steps
(window_evaluator, interval_sweep, day_on_demand) extend this plan; the spec
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
from datetime import datetime, timezone

from pipeline.orchestrator.writers import (
    ContextSpec,
    SubStep,
    WriterBase,
    WriterResult,
    register,
)
from services.gochara_kernel import evaluator as gk_evaluator
from services.gochara_kernel import arcs as gk_arcs
from services.gochara_kernel.dasha_read import make_period_rows_for
from services.gochara_kernel.chart_context import (fetch_chart_context,
                                                   require_complete)
from services.gochara_kernel.knots import calc_sidereal_lon, sample_knots
from services.gochara_kernel.record_store import (RecordStore,
                                                  materialise_record_grain,
                                                  write_class_coverage)
from services.gochara_kernel.rule_registry import BOUND_PATHS, RuleRegistryStore
from services.gochara_kernel.substrate import (SUBSTRATE_BODIES,
                                               SUBSTRATE_DOMAIN_END,
                                               SUBSTRATE_DOMAIN_START,
                                               SkyEventStore)

logger = logging.getLogger(__name__)

ASSET_ID = "ka_gochara_v5"

RULES_SUBSTEP = "rules"
CONVENTION_SUBSTEP = "convention"
BODY_SUBSTEP_PREFIX = "body:"
COVERAGE_SUBSTEP_PREFIX = "coverage:"
RECORD_SUBSTEP_PREFIX = "record:"

GENERATION = "5.0"
# interval_sweep record grains: P1–P4 only. P5 record grains HOLD (D7 —
# 'av_qualifier' joins the kgrr vocabulary only at the v1.5 contract fold;
# brief §interval_sweep + the batch list). The hold is a plan-level absence,
# never a silent skip: the substep labels say so.
RECORD_PATHS = tuple(p for p in BOUND_PATHS if p != "P5")
SCORED_CLASSES = tuple(sorted(gk_evaluator.ROW_MEMBERSHIP))
# The campaign's scored horizon (the A2.5 narrowing: LEL-scored window);
# overridable in config for rehearsals.
DEFAULT_HORIZON = (datetime(1998, 1, 1, tzinfo=timezone.utc),
                   datetime(2026, 4, 17, tzinfo=timezone.utc))
_SIGNS = ("aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra",
          "scorpio", "sagittarius", "capricorn", "aquarius", "pisces")
_JD_UNIX_EPOCH = 2440587.5

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


def _house_resolver(context: dict):
    """house_for(edge, sign) from the chart context, whole-sign from the
    edge's frame anchor: lagna → lagna sign; moon → natal Moon sign;
    bhavat_bhavam:<H> → the H-th house's sign from lagna. `dasha_lord`
    returns None — its anchor needs the §4.0 dasha rows, an open binding
    (brief §interval_sweep); an unresolvable anchor means the occurrence is
    NOT minted (kgrr_evaluated_has_house_ck — a state, never an omission)."""
    lagna_idx = int(context["lagna_deg"] // 30)
    moon_idx = int(context["natal"]["Moon"] // 30)

    def house_for(edge, sign: str) -> int | None:
        s = _SIGNS.index(sign.lower())
        if edge.frame_kind == "lagna":
            anchor = lagna_idx
        elif edge.frame_kind == "moon":
            anchor = moon_idx
        elif edge.frame_kind == "bhavat_bhavam" and edge.frame_arg:
            anchor = (lagna_idx + int(edge.frame_arg) - 1) % 12
        else:
            return None
        return (s - anchor) % 12 + 1
    return house_for


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
        """Plan (pin 5): 'rules' → 'convention' → 'body:<Body>' ×8.

        Static by design: the rule catalogue, the convention vector and the
        8-body substrate set are pinned constants (Moon excluded — EPHEMERAL
        per pin 6). The chart-scope refusal lives here too — a foreign chart
        is refused at PLAN time, not first at execution time."""
        _require_pinned_chart(ctx.config["chart_id"])
        steps = [
            SubStep(key=RULES_SUBSTEP,
                    label="rule_binding: P1–P5 registry + F3 seals (global "
                          "family key — NO chart lock in this substep)"),
            SubStep(key=CONVENTION_SUBSTEP,
                    label="§6.1 convention row (pin 3: idempotent under the chart lock)"),
        ]
        steps.extend(
            SubStep(key=f"{BODY_SUBSTEP_PREFIX}{body}",
                    label=f"phase-1 boundary substrate + stations: {body}")
            for body in SUBSTRATE_BODIES
        )
        # interval_sweep (design v1.1): per class, the coverage partition
        # first (pin 7), then its record grains over P1–P4 (P5 held — D7).
        for event_class in SCORED_CLASSES:
            steps.append(SubStep(
                key=f"{COVERAGE_SUBSTEP_PREFIX}{event_class}",
                label=f"class coverage partition (P1–P4 searched; P5 held — D7): "
                      f"{event_class}"))
            steps.extend(
                SubStep(key=f"{RECORD_SUBSTEP_PREFIX}{event_class}:{pid}",
                        label=f"contact materialisation {event_class}/{pid} "
                              "(residence + point solves + natal facts)")
                for pid in RECORD_PATHS
            )
        return steps

    def run_substep(self, ctx: ContextSpec, step: SubStep) -> WriterResult:
        """One substep per the pin-5 grain ('rules' | 'convention' | per-body).

        Every write rides ctx.db_conn — never committed, rolled back or
        closed here, and no other connection is opened. Lock order (steward
        ruling B / N13): the 'rules' substep takes NO chart lock (the
        registry tables' write guards take the Gochara-5 GLOBAL family key,
        which is mutually exclusive with any chart key); every substrate
        substep takes the chart family key first. ctx.dry_run suppresses the
        solve AND the write (there is nothing to stage)."""
        chart_id = ctx.config["chart_id"]
        _require_pinned_chart(chart_id)
        known = (RULES_SUBSTEP, CONVENTION_SUBSTEP)
        if (step.key not in known
                and not step.key.startswith(BODY_SUBSTEP_PREFIX)
                and not step.key.startswith(COVERAGE_SUBSTEP_PREFIX)
                and not step.key.startswith(RECORD_SUBSTEP_PREFIX)):
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                notes=f"unknown substep {step.key!r}")
        if ctx.dry_run:
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                notes=f"dry_run: {step.key} not solved, nothing written")
        if step.key == RULES_SUBSTEP:
            # rule_binding: registry writes ride the Gochara-5 GLOBAL family
            # key (taken by the tables' write-guard triggers). The chart
            # family key is deliberately NOT taken here — global EXCLUSIVE
            # and chart keys are mutually exclusive (N13). The orchestrator
            # commits per substep, so this substep is its own transaction.
            store = RuleRegistryStore(ctx.db_conn)
            counts = store.seed()
            inserted = (counts["predicates"] + counts["factors"] + counts["paths"]
                        + counts["prerequisites"] + counts["soft_factors"]
                        + counts["seals"])
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=inserted,
                notes=(f"rule catalogue {BOUND_PATHS} seeded + sealed: "
                       f"{inserted} inserted, {counts['reused']} reused "
                       "(idempotent)"))
        self._take_chart_lock(ctx, chart_id)
        if step.key == CONVENTION_SUBSTEP:
            store = SkyEventStore(ctx.db_conn)
            cid = store.register_convention()
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                notes=f"convention {cid[:24]}… registered (idempotent)")
        if step.key.startswith((COVERAGE_SUBSTEP_PREFIX, RECORD_SUBSTEP_PREFIX)):
            return self._run_record_phase(ctx, step, chart_id)
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

    def _run_record_phase(self, ctx: ContextSpec, step: SubStep,
                          chart_id: str) -> WriterResult:
        """interval_sweep substeps (the chart lock is already taken by the
        caller — substrate order, N13): `coverage:<class>` writes the class
        partition (pin 7), `record:<class>:<path>` materialises the grain.
        The chart context comes from L1 chart_facts — conflicts/missing are
        NAMED by require_complete, never defaulted."""
        context = fetch_chart_context(ctx.db_conn, chart_id)
        require_complete(context)
        horizon = ctx.config.get("horizon", DEFAULT_HORIZON)
        ephe_path = ctx.config.get("ephe_path")
        chart = {"lagna_deg": context["lagna_deg"], "natal": context["natal"]}
        store = RecordStore(ctx.db_conn)
        sky_cid = SkyEventStore(ctx.db_conn).register_convention()

        def position_at(body: str, t: datetime) -> float:
            jd = t.timestamp() / 86400.0 + _JD_UNIX_EPOCH
            lon, retflag = calc_sidereal_lon(body.title(), jd, ephe_path)
            if not (retflag & 2):
                raise RuntimeError(
                    f"position probe {body} @ {t.isoformat()}: retflag "
                    f"{retflag} lacks the Swiss bit (F-14 — a Moshier "
                    "fallback is a named failure, never a silent probe)")
            return lon

        house_for = _house_resolver(context)

        # 3/N point solves: one full-domain arc index per body, built lazily
        # (only grains with conjunction/aspect point edges pay for it); the
        # Swiss sampler asserts the SWIEPH backend on every call (F-14).
        arc_cache: dict[str, object] = {}

        def arc_index_for(body: str):
            if body not in arc_cache:
                ks = sample_knots(body, SUBSTRATE_DOMAIN_START.date(),
                                  SUBSTRATE_DOMAIN_END.date(), ephe_path)
                arc_cache[body] = gk_arcs.build_arc_index(
                    body, ks.knot_jds, ks.longitudes_deg)
            return arc_cache[body]

        if step.key.startswith(COVERAGE_SUBSTEP_PREFIX):
            event_class = step.key[len(COVERAGE_SUBSTEP_PREFIX):]
            if event_class not in SCORED_CLASSES:
                return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                    notes=f"unknown coverage class {event_class!r}")
            class_edges = [
                edge
                for pid in RECORD_PATHS
                for edge in gk_evaluator.enumerate_edges(event_class, pid, chart)
            ]
            kala_cid = store.ensure_kala_convention()
            write_class_coverage(
                store, chart_id=chart_id, generation=GENERATION,
                event_class=event_class, class_edges=class_edges,
                horizon=horizon, position_at=position_at,
                sky_convention_id=sky_cid, kala_convention_id=kala_cid,
                build_id=ctx.build_id, arc_index_available=True)
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=1,
                notes=(f"coverage partition {event_class} written "
                       f"(idempotent; {len(class_edges)} declared edges over "
                       f"P1–P4, P5 held — D7)"))

        event_class, path_id = step.key[len(RECORD_SUBSTEP_PREFIX):].split(":", 1)
        if event_class not in SCORED_CLASSES or path_id not in RECORD_PATHS:
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                notes=f"unknown record grain {step.key!r}")
        edges = gk_evaluator.enumerate_edges(event_class, path_id, chart)
        # P1's period_running_at reads L1 chart_dashas under the §4.0 pin; the
        # read is lazy (only P1 grains with a period_running_at prerequisite
        # ever trigger it) and its build is recorded in the notes below.
        dasha_rows_for, dasha_contract = make_period_rows_for(
            ctx.db_conn, chart_id)
        counts = materialise_record_grain(
            store, chart_id=chart_id, generation=GENERATION,
            event_class=event_class, path_id=path_id, edges=edges,
            horizon=horizon, position_at=position_at, house_for=house_for,
            sky_convention_id=sky_cid,
            source_fact_ids=context["source_fact_ids"],
            arc_index_for=arc_index_for, ephe_path=ephe_path,
            dasha_rows_for=dasha_rows_for)
        inserted = counts["contacts"] + counts["records"] + counts["natal_records"]
        return WriterResult(
            asset_id=self.asset_id, rows_inserted=inserted,
            notes=(f"{event_class}/{path_id}: {counts['records']} transit "
                   f"records ({counts['contacts']} contacts, "
                   f"{counts['truncated_contacts']} truncated kept), "
                   f"{counts['natal_records']} natal facts; "
                   f"{counts['prereq_evaluated']} prerequisite results "
                   f"evaluated; dasha_build="
                   f"{dasha_contract['build_id'] if dasha_contract['read'] else 'not_read'}"))

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
