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

import dataclasses
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
from services.gochara_kernel.native_conn import native_connection
from services.gochara_kernel import arcs as gk_arcs
from services.gochara_kernel.dasha_read import make_period_rows_for
from services.gochara_kernel.chart_context import (fetch_chart_context,
                                                   require_complete)
from services.gochara_kernel.knots import calc_sidereal_lon, sample_knots
from services.gochara_kernel.record_store import (RecordStore,
                                                  materialise_record_grain,
                                                  write_class_coverage)
from services.gochara_kernel import inventory as gk_inventory
from services.gochara_kernel import input_vector as gk_input_vector
from services.gochara_kernel import input_vector_verifier as gk_input_vector_verifier
from services.gochara_kernel import window_sweep as gk_window_sweep
from services.gochara_kernel import result_policy as gk_result_policy
from services.gochara_kernel import contact_certify as gk_contact_certify
from services.gochara_kernel.record_verifier import (verify_p1_anchors, verify_p1_house_descriptor,
                                                    verify_p1_support)
from services.gochara_kernel import window_gate as gk_window_gate
from services.gochara_kernel import window_verifier as gk_window_verifier
from services.gochara_kernel.window_verifier import verify_window_semantics
from services.gochara_kernel.window_store import WindowStore
from services.gochara_kernel import inventory_verifier as gk_verifier
from services.gochara_kernel import ledger as gk_ledger
from services.gochara_kernel.dasha_read import load_pinned_vimshottari
from services.gochara_kernel.inventory_store import InventoryStore
from services.gochara_kernel import rule_registry as gk_rule_registry
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
# design v1.5: the window sweep — `window:<class>:<path>` after the class's record grains.
WINDOW_SUBSTEP_PREFIX = "window:"
def _drishti_source(agent: str, offset: int, factor_ref: tuple):
    """Stream B's `gochara_rules.drishti.graduated_drishti` (cited table; CALLED, never copied), called
    with the MEMBERSHIP's own factor ref (a 1.1.0 path calls the 1.1.0 row). The returned `factor` is
    verified against the ref asked for — a source answering for a different row is a refusal, never
    re-labelled. Its `value` is None for an operand it cannot classify (a node, a non-aspect offset) —
    the sweep reads that as an undeterminable instant (unqualified), never a default."""
    from services.gochara_rules import drishti as rules_drishti
    ref = tuple(factor_ref)
    out = rules_drishti.graduated_drishti(gk_window_sweep.graha_title(agent), offset, factor_ref=ref)
    if tuple(out.get("factor") or ()) != ref:
        raise gk_window_sweep.SweepRefusal(
            f"graduated_drishti answered for {out.get('factor')!r}, asked for {ref!r}")
    return out["value"]


# The two operand SOURCES the sweep calls but this writer does not own. None = a named missing input
# in the sweep (graduated_drishti_source_not_landed / vedha_overlay_not_bound), and the same fact is
# handed to the independent window verifier, so builder and verifier cannot disagree on it.
DRISHTI_SOURCE = _drishti_source
VEDHA_SOURCE = None         # the overlay binding is a pending steward ruling (kala_vedha_gochara vs derived)
# AM-5 (v1.5 amendments; migration 1206): the search-completeness chain.
MANIFEST_SUBSTEP = "manifest"
SNAPSHOT_SUBSTEP = "snapshot"
INVENTORY_SUBSTEP_PREFIX = "inventory:"
VERIFY_SUBSTEP_PREFIX = "verify:"

# The VERIFIER's own copy of the two standing rulings — deliberately NOT imported from
# the builder's inventory module: the verifier is told its rulings independently of the
# code it checks (draft §AM-5 item 4 / O-RP-9).
VERIFIER_PATH_RULINGS = {"p5": {"reason": "tier_withheld_by_ruling",
                                "basis": "ruling:ST-P5-HOLD-20261001",
                                "ruling_ref": "ST-P5-HOLD-20261001"}}
VERIFIER_H_UNKNOWN_RULING = {"reason": "inputs_unavailable",
                             "basis": "ruling:ST-H-UNKNOWN-20261002",
                             "ruling_ref": "ST-H-UNKNOWN-20261002"}

GENERATION = "5.0"
# interval_sweep record grains: P1–P4 only. P5 record grains HOLD (D7 —
# 'av_qualifier' joins the kgrr vocabulary only at the v1.5 contract fold;
# brief §interval_sweep + the batch list). The hold is a plan-level absence,
# never a silent skip: the substep labels say so.
RECORD_PATHS = tuple(p for p in BOUND_PATHS if p != "P5")
# Window grains: the paths the sweep has an evaluator for (P1–P4; P5 is held). A path absent here
# is a plan-level absence — never a silent skip inside a grain.
WINDOW_PATHS = tuple(p for p in RECORD_PATHS if p in gk_window_sweep.SWEEP_PATHS)
# birth_anchor is excluded from enumeration entirely (O-CF-N6: zero rows) — it is NOT a
# scored class (27 − 1 = 26); the evaluator refuses it by design, so planning it would
# crash the build at its first substep.
SCORED_CLASSES = tuple(sorted(c for c, k in gk_evaluator.ROW_MEMBERSHIP.items()
                              if k is not None))
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


def _applicable_rulings() -> list[dict]:
    """The rulings this build applies (AM-16: they are part of the identity): the two standing
    exclusion rulings, every bound path's own `ruling_ref`, and the Moon-agent exclusion (AM-14)."""
    from services.gochara_kernel import rule_registry as _rr
    path_excl, h_unknown = gk_inventory.standing_exclusions()
    out = [{"id": e.ruling_ref, "reason": e.reason, "basis": e.basis}
           for e in (*path_excl.values(), h_unknown)]
    out += [{"id": r["ruling_ref"], "path": f"{r['path_id']}@{r['rule_version']}"}
            for r in _rr.path_rows() if r["ruling_ref"]]
    out.append({"id": "AM-14", "rule": "moon_agent_excluded_from_stored_tier"})
    return out


def _verify_live_inputs(ctx: ContextSpec, chart_id: str) -> None:
    """R6: a substep must consume the inputs its manifest was bound to. The vector is recomputed from
    what is consumed NOW (registry rows, ephemeris files, orb policy, rulings, implementation) and
    compared; any drift is refused by component, never continued."""
    stored = InventoryStore(ctx.db_conn).manifest_vector(chart_id, GENERATION)
    if stored is None:
        raise RuntimeError(f"{ASSET_ID}: no candidate manifest vector for generation {GENERATION} — "
                           "the manifest substep runs first")
    gk_input_vector.verify_live(
        ctx.db_conn, stored,
        sky_convention_id=SkyEventStore(ctx.db_conn).register_convention(),
        ephe_path=ctx.config.get("ephe_path"), path_refs=gk_rule_registry.bound_path_refs(),
        rulings=_applicable_rulings())
    # ... and every component that can be derived WITHOUT the builder's code is (registry + L0 + sky in
    # Postgres, ephemeris files + runtime library + implementation by direct hashing)
    gk_input_vector_verifier.verify_inputs(
        ctx.db_conn, stored, ephe_path=ctx.config.get("ephe_path"),
        modules=gk_input_vector.IMPLEMENTATION_MODULES, path_refs=gk_rule_registry.bound_path_refs())


def _l0_consumed() -> tuple[str, ...]:
    """The L0 authorities this build ACTUALLY consumes (R8-1). The vedha pairs feed P2's vedha operand only;
    while `VEDHA_SOURCE` is unbound nothing reads them, so `bg_transit_rules` is not a dependency of the
    build and is neither loaded nor bound."""
    return ("bg_transit_rules",) if VEDHA_SOURCE is not None else ()


class ChartRefusal(Exception):
    """ctx.config['chart_id'] is not the pinned A5.3 candidate chart — refused
    BEFORE any planning or execution (fail-closed; never a silent no-op)."""


def _native_ctx(ctx: ContextSpec) -> ContextSpec:
    """`ctx` with its connection presented as tuple rows when the runner's is a dict_row one
    (services.gochara_kernel.native_conn — a caller-owned VIEW, never committed or closed)."""
    conn = native_connection(ctx.db_conn)
    return ctx if conn is ctx.db_conn else dataclasses.replace(ctx, db_conn=conn)


def _require_pinned_chart(chart_id) -> None:
    """Fail-closed chart guard. The governed runner passes `chart_id` as a `uuid.UUID`; the CLI and
    dispatch pass strings — BOTH are accepted by comparing the canonical string form (the A2.5
    ASTRA A1 finding: a guard comparing a UUID to a string refuses the one chart it must admit)."""
    if str(chart_id) != PINNED_CHART_ID:
        raise ChartRefusal(
            f"{ASSET_ID}: chart_id {chart_id!r} is not the pinned A5.3 "
            f"candidate chart {PINNED_CHART_ID} — refusing (fail-closed; "
            "this asset is inert to all planners and admits no execution "
            "surface until steward pins 3-7 land)")


def _house_resolver(context: dict, *, p1_minting: bool = False):
    """house_for(edge, sign) from the chart context, whole-sign from the
    edge's frame anchor: lagna → lagna sign; moon → natal Moon sign;
    bhavat_bhavam:<H> → the H-th house's sign from lagna.

    `dasha_lord` (AM-20 REVISED, ND-P1-FRAME; Phaladīpikā XX.34 "the Bhava it represents when counted from
    the Lagna", XX.59): the inclusive count FROM THE LAGNA — a stored DESCRIPTOR only: nothing in P1 (no
    predicate, factor, admission or channel) reads it; the natal relation to H stays AM-15's lagna count.
    It resolves ONLY while `p1_minting` is True: P1 minting is gated on the applied schema carrying the
    period-anchor columns (`P1_MINTING_GATE`, migration 1233) — until then a `dasha_lord` occurrence has no
    resolvable record key, so it is NOT minted (kgrr_evaluated_has_house_ck — a state, never an omission)."""
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
        elif edge.frame_kind == "dasha_lord" and p1_minting:
            anchor = lagna_idx
        else:
            return None
        return (s - anchor) % 12 + 1
    return house_for


#: The named switch (steward M20261002T031247-e16e): P1 transit records carry a period ANCHOR (lord + level) in
#: their natural key (Stream B's additive migration 1233 — `period_anchor_lord`, `period_anchor_level`; no
#: existing column can carry it). Records minted without it are mis-keyed for the XX.38 forms, so P1 minting is
#: OFF unless the APPLIED schema has both columns AND this writer implements writing them.
P1_MINTING_GATE = "p1_minting_requires_period_anchor_columns"
P1_ANCHOR_MINTING_IMPLEMENTED = True        # AM-21 part 2: anchored enumeration, identity, supports, verification (O-PP-5)


def p1_minting_closed_reason(conn) -> str | None:
    """None when P1 transit records may be minted; else the NAMED reason they are not. Read from the applied
    schema (like the 1232 Moon-scope gate) — never assumed, never a flag someone forgot to flip."""
    if not RecordStore(conn).p1_anchor_columns_available():
        return P1_MINTING_GATE
    if not P1_ANCHOR_MINTING_IMPLEMENTED:
        return "p1_anchor_minting_not_implemented"
    return None


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
        ctx = _native_ctx(ctx)
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
        steps.append(SubStep(
            key=MANIFEST_SUBSTEP,
            label="candidate manifest (the search snapshot's input vector is bound to it)"))
        steps.append(SubStep(
            key=SNAPSHOT_SUBSTEP,
            label="AM-5 search-input snapshot (ONE per generation; L1/daśā/AV digests)"))
        for event_class in SCORED_CLASSES:
            steps.append(SubStep(
                key=f"{INVENTORY_SUBSTEP_PREFIX}{event_class}",
                label=f"AM-5 search inventory: pins → obligations → interval ledger "
                      f"→ finalisation: {event_class}"))
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
            steps.extend(
                SubStep(key=f"{WINDOW_SUBSTEP_PREFIX}{event_class}:{pid}",
                        label=f"window sweep {event_class}/{pid} (connected union of admitted "
                              "supports; score/evidence at the peak; unqualified stays NULL)")
                for pid in WINDOW_PATHS
            )
            steps.append(SubStep(
                key=f"{VERIFY_SUBSTEP_PREFIX}{event_class}",
                label=f"independent inventory verification: {event_class}"))
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
        ctx = _native_ctx(ctx)
        chart_id = str(ctx.config["chart_id"])       # the runner passes a uuid.UUID
        _require_pinned_chart(chart_id)
        known = (RULES_SUBSTEP, CONVENTION_SUBSTEP, MANIFEST_SUBSTEP, SNAPSHOT_SUBSTEP)
        if (step.key not in known
                and not step.key.startswith(INVENTORY_SUBSTEP_PREFIX)
                and not step.key.startswith(VERIFY_SUBSTEP_PREFIX)
                and not step.key.startswith(BODY_SUBSTEP_PREFIX)
                and not step.key.startswith(COVERAGE_SUBSTEP_PREFIX)
                and not step.key.startswith(RECORD_SUBSTEP_PREFIX)
                and not step.key.startswith(WINDOW_SUBSTEP_PREFIX)):
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
        if (step.key in (MANIFEST_SUBSTEP, SNAPSHOT_SUBSTEP)
                or step.key.startswith((INVENTORY_SUBSTEP_PREFIX, VERIFY_SUBSTEP_PREFIX))):
            if step.key != MANIFEST_SUBSTEP:
                _verify_live_inputs(ctx, chart_id)
            return self._run_inventory_phase(ctx, step, chart_id)
        if step.key.startswith((COVERAGE_SUBSTEP_PREFIX, RECORD_SUBSTEP_PREFIX)):
            _verify_live_inputs(ctx, chart_id)
            return self._run_record_phase(ctx, step, chart_id)
        if step.key.startswith(WINDOW_SUBSTEP_PREFIX):
            _verify_live_inputs(ctx, chart_id)
            return self._run_window_phase(ctx, step, chart_id)
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

    def _run_inventory_phase(self, ctx: ContextSpec, step: SubStep,
                             chart_id: str) -> WriterResult:
        """AM-5 chain (chart lock already taken by the caller; every INVENTORY write takes
        the global SHARED key after it — chart → global SHARED, draft item 7):
        `manifest` → `snapshot` → `inventory:<class>` → (coverage, records) →
        `verify:<class>`. Sealing is NOT this writer's step (A6)."""
        horizon = ctx.config.get("horizon", DEFAULT_HORIZON)
        ephe_path = ctx.config.get("ephe_path")
        inv_store = InventoryStore(ctx.db_conn)
        rstore = RecordStore(ctx.db_conn)

        if step.key == MANIFEST_SUBSTEP:
            sky_cid = SkyEventStore(ctx.db_conn).register_convention()
            kala_cid = rstore.ensure_kala_convention()
            rstore.ensure_bridge(kala_cid, sky_cid)
            vector = gk_input_vector.build_input_vector(
                ctx.db_conn, sky_convention_id=sky_cid, ephe_path=ephe_path,
                path_refs=gk_rule_registry.bound_path_refs(), rulings=_applicable_rulings(),
                l0_consumed=_l0_consumed(),
                # R9-1: the policy is an INPUT of the build, chosen here and bound into the manifest; every later
                # stage reads it back FROM the manifest — nothing downstream holds its own constant
                result_policy=ctx.config.get("result_policy", gk_input_vector.DEFAULT_RESULT_POLICY))
            # every component that can be derived without the builder's code is derived a SECOND way and the two
            # must agree before the identity is bound
            inputs_report = gk_input_vector_verifier.verify_inputs(
                ctx.db_conn, vector, ephe_path=ephe_path, modules=gk_input_vector.IMPLEMENTATION_MODULES,
                path_refs=gk_rule_registry.bound_path_refs(),
                jd_range=gk_input_vector.consumed_jd_range(horizon))
            jd = horizon[0].timestamp() / 86400.0 + _JD_UNIX_EPOCH
            _lon, retflag = calc_sidereal_lon("Sun", jd, ephe_path)
            if not (retflag & 2):
                raise RuntimeError(f"manifest: Swiss backend probe retflag {retflag} (F-14)")
            mid = gk_ledger.publish_candidate(
                ctx.db_conn, chart_id, GENERATION, kala_cid, vector,
                {"backend": "swieph", "probe_retflag": int(retflag)},
                f"[{horizon[0].isoformat()},{horizon[1].isoformat()})",
                writer_asset_id=ASSET_ID)
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                notes=f"candidate manifest {mid[:8]}… (input vector {gk_input_vector.VECTOR_SCHEMA}: "
                                      f"registry digest {vector['registry']['digest'][:12]}…, "
                                      f"{len(vector['ephemeris']['files'])} ephemeris files, node "
                                      "series, both orb policies, rulings, implementation)")

        if step.key == SNAPSHOT_SUBSTEP:
            context = fetch_chart_context(ctx.db_conn, chart_id)
            require_complete(context)
            sky_cid = SkyEventStore(ctx.db_conn).register_convention()
            rows, contract = load_pinned_vimshottari(ctx.db_conn, chart_id)
            lo, hi = horizon
            dasha_ids = [str(r["dasha_row_id"]) for r in rows
                         if int(r["level_n"]) in (1, 2, 3)
                         and r["start_iso"] < hi and r["end_iso"] > lo]
            inv_store.delete_generation_inventory(chart_id, GENERATION)
            digest = inv_store.insert_snapshot(
                chart_id=chart_id, generation=GENERATION, convention_id=sky_cid,
                consumed_fact_ids=context["source_fact_ids"],
                consumed_dasha_row_ids=dasha_ids)
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=1,
                notes=(f"search-input snapshot {digest[:12]}…: {len(context['source_fact_ids'])} "
                       f"L1 facts, {len(dasha_ids)} daśā rows (build "
                       f"{contract.get('build_id')}); no AV declarations (P5 held)"))

        event_class = step.key.split(":", 1)[1]
        if event_class not in SCORED_CLASSES:
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                notes=f"unknown class {event_class!r}")

        if step.key.startswith(INVENTORY_SUBSTEP_PREFIX):
            context = fetch_chart_context(ctx.db_conn, chart_id)
            require_complete(context)
            chart = {"lagna_deg": context["lagna_deg"], "natal": context["natal"]}
            digest = inv_store.snapshot_input_digest(chart_id, GENERATION)
            if digest is None:
                return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                    notes=f"inventory {event_class} refused: no search-input "
                                          "snapshot (the snapshot substep runs first)")
            path_excl, h_unknown = gk_inventory.standing_exclusions()
            plan = gk_inventory.plan_class_inventory(
                event_class=event_class, chart=chart, horizon=horizon,
                sealed_paths=inv_store.sealed_rule_paths(),
                selected_versions=gk_rule_registry.selected_versions_for(event_class),
                capability=gk_inventory.SearchCapability(
                    position_probe=True, arc_index=True, aspect_span_solver=True,
                    moon_scope_domain=inv_store.moon_scope_available()),
                path_exclusions=path_excl, h_unknown_exclusion=h_unknown,
                dasha_rows=inv_store.consumed_dasha_rows(chart_id, GENERATION))
            out = inv_store.write_class_inventory(
                chart_id=chart_id, generation=GENERATION, plan=plan, input_digest=digest)
            dispositions = ",".join(f"{p.path_id}:{p.disposition}" for p in plan.pins)
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=out["obligations"] + out["pins"],
                notes=(f"inventory {event_class}: {out['obligations']} obligations, "
                       f"{out['intervals']} intervals, pins {dispositions}; "
                       f"inventory_digest={out['inventory_digest'][:12]}…"))

        # verify:<class> — the INDEPENDENT verifier (shares no code with the builder)
        sealed = inv_store.sealed_rule_paths()
        # R8-2: the verifier re-derives under the ORIGINAL selection stored with the inventory (never today's
        # configuration — historical replay), and the writer separately requires that stored selection to equal
        # the configured one for every path the class actually searches.
        stored_sel = gk_verifier.stored_selection(
            ctx.db_conn, chart_id=chart_id, generation=GENERATION, event_class=event_class)
        configured = {p.lower(): v for p, v in gk_rule_registry.selected_versions_for(event_class).items()}
        drift = {p: (v, configured.get(p)) for p, v in stored_sel.items() if configured.get(p) != v}
        if drift:
            raise RuntimeError(f"verify {event_class}: the stored inventory searched {drift} "
                               "(stored, configured) — the selection drifted from the build configuration")
        try:
            res = gk_verifier.rederive_inventory_digest(
                ctx.db_conn, chart_id=chart_id, generation=GENERATION,
                event_class=event_class, sealed_paths=sealed,
                path_exclusions=VERIFIER_PATH_RULINGS,
                h_unknown_exclusion=VERIFIER_H_UNKNOWN_RULING,
                selected_versions=stored_sel or None)
        except gk_verifier.Unverifiable as exc:
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=0,
                notes=f"verify {event_class}: UNVERIFIED — {exc} (no verification row; the "
                      "class cannot seal until the verifier can derive every path)")
        stored = inv_store.finalised_class_facts(chart_id, GENERATION, event_class)
        if stored is None or res["digest"] != stored["inventory_digest"]:
            raise RuntimeError(
                f"verify {event_class}: the independent derivation DISAGREES with the stored "
                f"inventory (verifier {res['digest']} vs stored "
                f"{stored and stored['inventory_digest']}) — a misreading in one of the two "
                "paths; the build fails rather than store a mismatching verification row")
        led = gk_verifier.rederive_ledger_digest(
            ctx.db_conn, chart_id=chart_id, generation=GENERATION, event_class=event_class,
            obligations=res["obligations"],
            capability={"position_probe": True, "arc_index": True, "aspect_span_solver": True,
                        "moon_scope_domain": inv_store.moon_scope_available()})
        db_led = ctx.db_conn.execute(
            "SELECT ledger_digest FROM public.ka_gochara_search_inventory WHERE chart_id = %s"
            " AND generation = %s AND event_class = %s", (chart_id, GENERATION, event_class)
        ).fetchone()[0]
        if led != db_led:
            raise RuntimeError(
                f"verify {event_class}: the independent LEDGER derivation (daśā cuts / "
                f"resolved agents) disagrees with the stored ledger ({led} vs {db_led})")
        # aspect-to-span: the builder derives these occurrences from residence spans; the verifier
        # re-derives them by SAMPLING + BISECTION (no shared code, no crossings) and the two must
        # agree — the capability the inventory claims is only earned if they do (steward
        # M20261002T000907-c058 (b)). Any disagreement fails the build before a verification row exists.
        horizon = ctx.config.get("horizon", DEFAULT_HORIZON)
        ephe_path = ctx.config.get("ephe_path")

        def position_at(body: str, t: datetime) -> float:
            jd = t.timestamp() / 86400.0 + _JD_UNIX_EPOCH
            lon, retflag = calc_sidereal_lon(body.title(), jd, ephe_path)
            if not (retflag & 2):
                raise RuntimeError(f"position probe {body} @ {t.isoformat()}: retflag {retflag} "
                                   "lacks the Swiss bit (F-14)")
            return lon

        position_at.cache_key = ("swiss", ephe_path)
        spans = gk_verifier.verify_aspect_span_contacts(
            ctx.db_conn, chart_id=chart_id, generation=GENERATION, obligations=res["obligations"],
            position_at=position_at, horizon=horizon,
            _cache=self.__dict__.setdefault("_aspect_span_cache", {}))
        # R9-3: the COMPLETE contact geometry of every concrete transit obligation, reconstructed from the ephemeris
        # and compared with the ledger both ways (interior exits/re-entries, bridged and omitted contacts all fail);
        # incomplete evidence raises GeometryUnavailable — no complete-search claim without it
        geometry = gk_contact_certify.certify_contact_geometry(
            ctx.db_conn, chart_id=chart_id, generation=GENERATION, event_class=event_class, position_at=position_at)
        gk_verifier.write_verification(
            ctx.db_conn, chart_id=chart_id, generation=GENERATION, event_class=event_class,
            rederived_digest=res["digest"])
        # R8-4: the candidate gate's window half — every included P1–P4 grain of this class must carry a
        # VERIFIED, current, input-bound verification result. The build refuses a class that cannot pass it
        # rather than leave a candidate no sealer could accept (UNVERIFIED_DYNAMIC / missing both fail).
        if not gk_window_gate.verification_available(ctx.db_conn):
            gate_note = "; window verification gate NOT evaluated (migration 1240 is not applied)"
        elif not gk_window_gate.can_write_verification(ctx.db_conn):
            # no verifier principal is provisioned: no result CAN exist, so the seal trigger will refuse the
            # candidate; say so rather than fail every class — the roles decision is the named blocker
            # (the builder holds no privilege on the verification table or the gate functions, so it does not READ
            # the gate either: the state is explicit and the seal trigger is the authority)
            gate_note = ("; window verification gate CLOSED — verification_pending_verifier_principal "
                         "(a verifier principal must be provisioned; the candidate cannot be sealed until then)")
        else:
            gk_window_gate.require_candidate_gate(ctx.db_conn, chart_id, GENERATION, event_class)
            gate_note = "; window verification gate passed"
        return WriterResult(asset_id=self.asset_id, rows_inserted=1,
                            notes=f"verify {event_class}: inventory + ledger digests "
                                  "independently reproduced; "
                                  f"{spans['objects_checked']} aspect-to-span object(s) / "
                                  f"{spans['occurrences']} occurrence(s) re-derived by sampling "
                                  f"and matched; contact geometry certified complete for "
                                  f"{geometry['obligations_certified']} concrete obligation(s) "
                                  f"({geometry['contacts_expected']} contacts; {geometry['named_limit']}); "
                                  f"verification row written{gate_note}")

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
        position_at.cache_key = ("swiss", ephe_path)        # lets the independent reconstruction memoise across classes

        p1_closed = p1_minting_closed_reason(ctx.db_conn)
        house_for = _house_resolver(context, p1_minting=p1_closed is None)

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
                for edge in gk_evaluator.enumerate_edges(
                    event_class, pid, chart,
                    rule_version=gk_rule_registry.selected_path_version(event_class, pid))
            ]
            ephemeral_excluded = sum(
                len(gk_evaluator.ephemeral_tier_edges(
                    event_class, pid, chart,
                    rule_version=gk_rule_registry.selected_path_version(event_class, pid)))
                for pid in RECORD_PATHS)
            kala_cid = store.ensure_kala_convention()
            # AM-5: the partition is the guard-facing SUMMARY of the stored inventory —
            # the inventory substep runs first and the partition is aligned to it.
            inv_facts = InventoryStore(ctx.db_conn).finalised_class_facts(
                chart_id, GENERATION, event_class)
            if inv_facts is None:
                return WriterResult(
                    asset_id=self.asset_id, rows_inserted=0,
                    notes=f"coverage {event_class} refused: no finalised search inventory "
                          "(the inventory substep runs first)")
            write_class_coverage(
                store, chart_id=chart_id, generation=GENERATION,
                event_class=event_class, class_edges=class_edges,
                horizon=horizon, position_at=position_at,
                sky_convention_id=sky_cid, kala_convention_id=kala_cid,
                build_id=ctx.build_id, arc_index_available=True,
                inventory_facts=inv_facts, ephemeral_tier_excluded=ephemeral_excluded)
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=1,
                notes=(f"coverage partition {event_class} written "
                       f"(idempotent; {len(class_edges)} declared edges over "
                       f"P1–P4, P5 held — D7; {ephemeral_excluded} Moon-agent transit edge(s) "
                       "excluded by rule — AM-4 ephemeral tier)"))

        event_class, path_id = step.key[len(RECORD_SUBSTEP_PREFIX):].split(":", 1)
        if event_class not in SCORED_CLASSES or path_id not in RECORD_PATHS:
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                notes=f"unknown record grain {step.key!r}")
        path_version = gk_rule_registry.selected_path_version(event_class, path_id)
        edges = gk_evaluator.enumerate_edges(event_class, path_id, chart,
                                             rule_version=path_version)
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
            dasha_rows_for=dasha_rows_for, chart=chart,
            rule_version=path_version)
        inserted = counts["contacts"] + counts["records"] + counts["natal_records"]
        if path_id == "P1":
            # R7 [3]: the restriction to the running periods is re-derived independently (SQL, from the
            # snapshot-bound daśā rows) and must equal what was stored
            verify_p1_support(ctx.db_conn, chart_id=chart_id, generation=GENERATION,
                              event_class=event_class)
            # AM-21 part 2 / R9-2 (iii): the ANCHOR set of every contact of the EXPECTED contact set (reconstructed from
            # the ephemeris), zero-output cases included — only meaningful when P1 minting is OPEN; with the named gate
            # closed nothing was minted, the class makes no P1 completeness claim, and the notes say so
            if not p1_closed:
                verify_p1_anchors(ctx.db_conn, chart_id=chart_id, generation=GENERATION, event_class=event_class,
                                  position_at=position_at)
            # AM-20 (revised): the stored house descriptor is the count from the lagna
            verify_p1_house_descriptor(ctx.db_conn, chart_id=chart_id, generation=GENERATION,
                                       event_class=event_class)
        gate_note = (f"; P1 transit records NOT minted — {p1_closed}" if path_id == "P1" and p1_closed else "")
        return WriterResult(
            asset_id=self.asset_id, rows_inserted=inserted,
            notes=(f"{event_class}/{path_id}: {counts['records']} transit "
                   f"records ({counts['contacts']} contacts, "
                   f"{counts['truncated_contacts']} truncated kept), "
                   f"{counts['natal_records']} natal facts "
                   f"({counts.get('skipped_natal_p1', 0)} P1 natal rows not "
                   f"admission-bearing, {counts.get('unwritable_testimony', 0)} "
                   f"testimony-licence transit records unwritable, "
                   f"{counts.get('p3_enumeration_defects', 0)} P3 enumeration "
                   f"defects); "
                   f"{counts['prereq_evaluated']} prerequisite results "
                   f"evaluated; dasha_build="
                   f"{dasha_contract['build_id'] if dasha_contract['read'] else 'not_read'}"
                   f"{gate_note}"))

    # ------------------------------------------------------------------

    def _run_window_phase(self, ctx: ContextSpec, step: SubStep, chart_id: str) -> WriterResult:
        """`window:<class>:<path>` (chart lock already held — substrate order, N13): the grain's
        stored records → connected-union windows (`window_sweep`) → delete-then-insert
        (`window_store`) → an independent SQL recomputation of the union. Reads the factor rows
        the records' own `rule_version` is sealed against; writes nothing it cannot derive —
        unqualified windows keep NULL score/evidence/peak and a named reason."""
        event_class, path_id = step.key[len(WINDOW_SUBSTEP_PREFIX):].split(":", 1)
        if event_class not in SCORED_CLASSES or path_id not in WINDOW_PATHS:
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                notes=f"unknown window grain {step.key!r}")
        ephe_path = ctx.config.get("ephe_path")

        def position_at(body: str, t: datetime) -> float:
            jd = t.timestamp() / 86400.0 + _JD_UNIX_EPOCH
            lon, retflag = calc_sidereal_lon(body.title(), jd, ephe_path)
            if not (retflag & 2):
                raise RuntimeError(
                    f"position probe {body} @ {t.isoformat()}: retflag {retflag} lacks the "
                    "Swiss bit (F-14 — a Moshier fallback is a named failure, never a silent probe)")
            return lon

        store = WindowStore(ctx.db_conn)
        # R9-1: the result policy is read BACK from the generation's manifest (the vector the build was bound to) —
        # this writer holds no policy constant of its own
        policy = gk_result_policy.manifest_policy(ctx.db_conn, chart_id, GENERATION)
        # R5: the declaration the sweep evaluates is the PERSISTED one, read back (each soft factor at
        # its own membership version, flat applicability decoded and checked) — not a global constant.
        bound_rows = RuleRegistryStore(ctx.db_conn).bound_factor_rows
        # …plus the class's SELECTED version even with no records: a grain with zero windows is still VERIFIED
        # (zero expected), and the candidate gate demands a result for every included grain
        versions = sorted({r[0] for r in ctx.db_conn.execute(
            "SELECT DISTINCT rule_version FROM public.ka_gochara_relationship_record"
            " WHERE chart_id = %s AND generation = %s AND event_class = %s AND path_id = %s"
            " ORDER BY 1", (chart_id, GENERATION, event_class, path_id)).fetchall()}
            | {gk_rule_registry.selected_path_version(event_class, path_id)})
        available = gk_window_gate.verification_available(ctx.db_conn)
        # 1240: the builder deliberately holds NO privilege on the verification table (the writer cannot verify
        # itself); only a provisioned verifier principal may write it
        privileged = available and gk_window_gate.can_write_verification(ctx.db_conn)
        input_digest = (InventoryStore(ctx.db_conn).snapshot_input_digest(chart_id, GENERATION)
                        if privileged else None)
        persist = privileged and input_digest is not None
        windows = memberships = 0
        excluded: dict = {}
        reasons: dict = {}
        unqualified = unverified = reproduced = 0
        for version in versions:        # the path→version map comes from the records, not a constant
            records = store.read_grain(
                chart_id=chart_id, generation=GENERATION, event_class=event_class,
                path_id=path_id, rule_version=version, position_at=position_at)
            drafts, ex = gk_window_sweep.draft_windows(
                event_class, records, bound_rows, drishti=DRISHTI_SOURCE, vedha=VEDHA_SOURCE,
                policy=policy)
            counts = store.replace_grain_windows(
                chart_id=chart_id, generation=GENERATION, event_class=event_class,
                path_id=path_id, rule_version=version, drafts=drafts)
            store.verify_grain(chart_id=chart_id, generation=GENERATION, event_class=event_class,
                               path_id=path_id, rule_version=version)
            gk_window_verifier.verify_member_support(
                ctx.db_conn, chart_id=chart_id, generation=GENERATION, event_class=event_class,
                path_id=path_id, rule_version=version)
            # R8-4: ...and the contact spans themselves against the EPHEMERAL geometry (Swiss probes just inside and
            # just outside each end), not the builder-written contact row
            gk_window_verifier.verify_member_geometry(
                ctx.db_conn, chart_id=chart_id, generation=GENERATION, event_class=event_class,
                path_id=path_id, rule_version=version, position_at=position_at)
            report = verify_window_semantics(
                ctx.db_conn, chart_id=chart_id, generation=GENERATION, event_class=event_class,
                path_id=path_id, rule_version=version,
                factor_rows=bound_rows(path_id, version),
                drishti_bound=DRISHTI_SOURCE is not None, vedha_bound=VEDHA_SOURCE is not None)
            if persist:      # the generation-bound result the candidate gate consumes (R8-4; migration 1240)
                gk_window_gate.record_verification(
                    ctx.db_conn, chart_id=chart_id, generation=GENERATION, event_class=event_class,
                    path_id=path_id, rule_version=version, report=report, input_digest=input_digest)
            unverified += report["unverified_dynamic"]
            reproduced += report["fully_reproduced"]
            windows += counts["windows"]
            memberships += counts["memberships"]
            unqualified += sum(1 for d in drafts if d.score is None)
            for d in drafts:
                if d.score is None:
                    for k, v in d.unresolved.items():
                        reasons[k] = reasons.get(k, 0) + v
            for k, v in ex.items():
                excluded[k] = excluded.get(k, 0) + v
        # qualification summary (the per-window detail is reconstructable from the stored rows)
        why = sorted(f"{k}×{v}" for k, v in reasons.items())
        head = (f"{event_class}/{path_id}: {windows} window(s) ({unqualified} unqualified"
                f"{' — ' + ', '.join(why) if why else ''} — score/evidence/peak NULL, severity NULL by "
                f"ruling), {memberships} membership row(s); excluded records {excluded}; independent SQL "
                "components + member-support geometry checked; semantic re-derivation: ")
        tail = (f"{reproduced} window(s) reproduced exactly, {unverified} UNVERIFIED (function-valued "
                "members — checked against universal bounds only; this result does NOT satisfy a "
                "verification gate)" if unverified
                else f"reproduced all {reproduced} window(s) exactly")
        stored_note = ("; verification result persisted (the candidate gate consumes it)" if persist else
                       "; verification result NOT persisted — "
                       + ("migration 1240 is not applied" if not available else
                          "verification_pending_verifier_principal — the running role holds no INSERT on the "
                          "verification table (no verifier principal is provisioned; a builder never writes it)"
                          if not privileged else
                          "no search-input snapshot to bind it to") + " (the candidate gate stays closed)")
        return WriterResult(asset_id=self.asset_id, rows_inserted=windows + memberships,
                            notes=head + tail + stored_note)

    @staticmethod
    def _take_chart_lock(ctx: ContextSpec, chart_id: str) -> None:
        """Steward ruling B / N13 substrate order: the chart family key
        precedes every substrate tuple. ka_gochara_lock_chart takes the
        xact-scoped advisory lock AND marks gochara5.chart_locked so the
        statement-level trigger admits the following writes."""
        ctx.db_conn.execute(
            "SELECT public.ka_gochara_lock_chart(%s::uuid)", (chart_id,)
        )
