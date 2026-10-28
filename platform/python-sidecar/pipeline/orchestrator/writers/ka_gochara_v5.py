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
import hashlib
import json
import logging
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from pipeline.orchestrator.writers import (
    ContextSpec,
    SubStep,
    WriterBase,
    WriterResult,
    register,
)
from services.gochara_kernel import evaluator as gk_evaluator
from services.gochara_kernel import horizon as gk_horizon


from services.gochara_kernel import stretch_sink as gk_stretch_sink


from services.gochara_kernel import ephemeris_pins as gk_ephemeris_pins
from services.gochara_kernel.native_conn import native_connection
from services.gochara_kernel import arcs as gk_arcs
from services.gochara_kernel.dasha_read import PERIOD_TABLE_ENDS_REASON, make_period_rows_for, make_period_rows_for_snapshot
from services.gochara_kernel.chart_context import (fetch_chart_context, fetch_chart_context_from_snapshot,
                                                   require_complete)
from services.gochara_kernel.knots import calc_sidereal_lon, calc_sidereal_lon_speed, sample_knots
from services.gochara_kernel.record_store import (RecordStore,
                                                  materialise_record_grain,
                                                  write_class_coverage)
from services.gochara_kernel import inventory as gk_inventory
from services.gochara_kernel import input_vector as gk_input_vector
from services.gochara_kernel import input_vector_verifier as gk_input_vector_verifier
from services.gochara_kernel import window_sweep as gk_window_sweep
from services.gochara_kernel import p1_operands as gk_p1_operands
from services.gochara_kernel import p1_operands_check as gk_p1_operands_check
from services.gochara_kernel import vedha_source as gk_vedha_source
from services.gochara_kernel import result_policy as gk_result_policy
from services.gochara_kernel import contact_certify as gk_contact_certify
from services.gochara_kernel import near_miss as gk_near_miss
from services.gochara_kernel import record_store as gk_record_store
from services.gochara_kernel.record_verifier import (verify_p1_anchors, verify_p1_house_descriptor,
                                                    verify_p1_support)
from services.gochara_kernel import window_gate as gk_window_gate
from services.gochara_kernel import window_verifier as gk_window_verifier
from services.gochara_kernel.window_verifier import verify_window_semantics
from services.gochara_kernel.window_store import WindowStore
from services.gochara_kernel import inventory_verifier as gk_verifier
from services.gochara_kernel import ledger as gk_ledger
from services.gochara_kernel import build_ledger as gk_build_ledger
from services.gochara_kernel.dasha_read import LEVEL_N, load_pinned_vimshottari
from services.gochara_kernel.inventory_store import InventoryStore
from services.gochara_kernel import rule_registry as gk_rule_registry
from services.gochara_kernel.rule_registry import BOUND_PATHS, RuleRegistryStore
from services.gochara_rules import registry as gk_rules_registry
from services.gochara_kernel.substrate import (SUBSTRATE_BODIES, production_arc_index,
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
def _drishti_answer(agent: str, offset: int, factor_ref: tuple) -> dict:
    """Stream B's `gochara_rules.drishti.graduated_drishti` (cited table; CALLED, never copied), called
    with the MEMBERSHIP's own factor ref (a 1.1.0 path calls the 1.1.0 row). The returned `factor` is
    verified against the ref asked for — a source answering for a different row is a refusal, never
    re-labelled."""
    from services.gochara_rules import drishti as rules_drishti
    ref = tuple(factor_ref)
    out = rules_drishti.graduated_drishti(gk_window_sweep.graha_title(agent), offset, factor_ref=ref)
    if tuple(out.get("factor") or ()) != ref:
        raise gk_window_sweep.SweepRefusal(
            f"graduated_drishti answered for {out.get('factor')!r}, asked for {ref!r}")
    return out


def _drishti_source(agent: str, offset: int, factor_ref: tuple):
    """The graduated-dṛṣṭi value. It is None for an operand the table cannot classify (an offset the bound rule does
    not define, a node) — the sweep reads that as an undeterminable instant (unqualified), never a default."""
    return _drishti_answer(agent, offset, factor_ref)["value"]


def _drishti_reason(agent: str, offset: int, factor_ref: tuple):
    """Why `_drishti_source` is None at this operand — the table's own named reason (SR-D6-OBJECTIVE-UNKNOWN; None when the
    value is known). The sweep passes it through as the factor's `unknown_reason` instead of its generic code."""
    return _drishti_answer(agent, offset, factor_ref).get("reason")


# an optional attribute on the source (the pattern the vedha source uses with `.overlay`): the `(agent, offset, ref) -> value`
# signature every caller and test relies on is unchanged
_drishti_source.reason = _drishti_reason


# The two operand SOURCES the sweep calls but this writer does not own. None = a named missing input
# in the sweep (graduated_drishti_source_not_landed / vedha_overlay_not_bound), and the same fact is
# handed to the independent window verifier, so builder and verifier cannot disagree on it.
DRISHTI_SOURCE = _drishti_source
VEDHA_SOURCE = None         # an EXPLICIT binding (a steward ruling, or a test's); None ⇒ the active rule profile decides — `vedha_source()`
#: SR-OD1 C1 (VEDHA-SOURCE, ND-NODE-VEDHA, ND-VIPAREETA — owner-confirmed 2026-10-21): the vedha operand of the FINAL (doctrine)
#: rule profile is DERIVED (Phaladīpikā XXVI house-vedha only; nodes obstruct) from the obstructors' sign residence, itself derived at the
#: instant from the pinned ephemeris (SR-VEDHA-RESIDENCE-SOURCE) — no longer from the stored residence contacts. The measuring
#: profile keeps its pre-doctrine contract byte for byte: the overlay stays unbound there (`vedha_overlay_not_bound`).
FINAL_VEDHA_SOURCE = gk_vedha_source.SOURCE


def vedha_source():
    """The vedha operand source of the ACTIVE rule profile (read at call time): an explicit `VEDHA_SOURCE` binding wins; else the
    derived source under the final profile; else None. Builder, input vector and verification job all ask THIS, so none of them
    can disagree with another about whether the overlay is bound."""
    if VEDHA_SOURCE is not None:
        return VEDHA_SOURCE
    return FINAL_VEDHA_SOURCE if gk_rule_registry.final_rules_active() else None
# SR-OD1 P1a: P1's dignity / combustion / maitrī operand sources are bound when the owner-table PR (D2) supplies the value rules
# `{factor_id: p1_operands.ValueRule}`. None = unbound: P1 windows keep their named blank (`value_mapping_undeclared`) and the three L0
# reference tables are not a dependency of the build (`_l0_consumed`).
P1_VALUE_RULES = None
# AM-5 (v1.5 amendments; migration 1206): the search-completeness chain.
MANIFEST_SUBSTEP = "manifest"
SNAPSHOT_SUBSTEP = "snapshot"
INVENTORY_SUBSTEP_PREFIX = "inventory:"
VERIFY_SUBSTEP_PREFIX = "verify:"

# The VERIFIER's own copy of the standing rulings — deliberately NOT imported from
# the builder's inventory module: the verifier is told its rulings independently of the
# code it checks (draft §AM-5 item 4 / O-RP-9). P4 is switched OFF by the panel closure
# FOURQ-CLOSURE-20261027 (retired_pending_reauthor; provenance DOUBLE-TRANSIT-PROVENANCE-20261027).
VERIFIER_PATH_RULINGS = {"p5": {"reason": "tier_withheld_by_ruling",
                                "basis": "ruling:ST-P5-HOLD-20261001",
                                "ruling_ref": "ST-P5-HOLD-20261001"},
                         "p4": {"reason": "tier_withheld_by_ruling",
                                "basis": "ruling:FOURQ-CLOSURE-20261027",
                                "ruling_ref": "FOURQ-CLOSURE-20261027"}}
VERIFIER_H_UNKNOWN_RULING = {"reason": "inputs_unavailable",
                             "basis": "ruling:ST-H-UNKNOWN-20261002",
                             "ruling_ref": "ST-H-UNKNOWN-20261002"}

GENERATION = "5.0"
# interval_sweep record grains: P1–P4 only. P5 record grains HOLD (D7 —
# 'av_qualifier' joins the kgrr vocabulary only at the v1.5 contract fold;
# brief §interval_sweep + the batch list). The hold is a plan-level absence,
# never a silent skip: the substep labels say so.
# A path the registry switches off (P4 — FOURQ-CLOSURE-20261027) is a plan-level absence too: the inventory pins it
# `excluded / tier_withheld_by_ruling`, so a record or window step for it would build a grain the inventory does not
# include and the generation-wide output check (`window_gate.generation_output_problems`) would refuse the whole class.
def _record_paths() -> tuple[str, ...]:
    """The bound paths with a record grain: P5 held, and any path the registry switches off — read at call time."""
    return tuple(p for p in BOUND_PATHS if p != "P5" and gk_rules_registry.path_disabled(p) is None)


RECORD_PATHS = _record_paths()
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

# ── gochara_v5_test_slice (C46; Stream A's spec M20261003T181323-f9c7 §3) ─────
# A staged test run carries a digest-protected marker in build_runs.plan_manifest
# (found through ctx.build_id + ctx.db_conn — never ctx.config). ABSENT key =
# today's behaviour, byte-identical. PRESENT but malformed, an unknown run, any
# extra field, a class outside SCORED_CLASSES or a horizon outside
# DEFAULT_HORIZON = a named TestSliceRefusal, never a guess. A valid marker
# narrows the plan to the marker's classes over the marker's horizon and stamps
# the candidate manifest's input vector with stored_scope='test_slice' plus the
# marker digest — a scope no verifier vocabulary knows, so the verification job
# refuses it by name and the candidate is unsealable by construction. The writer
# never publishes either way.
MEASURING_HORIZON = gk_horizon.RULED_HORIZON


MEASURING_RUN = "all_classes_full"


TEST_SLICE_KEY = "gochara_v5_test_slice"
TEST_SLICE_SCHEMA = "gochara_v5_test_slice/1"
TEST_SLICE_RUNS = ("all_classes_1y", "one_class_full", "all_classes_full")      # all_classes_full: the measuring build (every scored class, the whole derived horizon)
TEST_SLICE_SCOPE = "test_slice"
_ONE_YEAR = timedelta(days=366)
_TEST_SLICE_FIELDS = frozenset({"schema", "run", "horizon", "classes"})


class TestSliceRefusal(Exception):
    """The gochara_v5_test_slice marker in build_runs.plan_manifest is present
    but malformed (or conflicts with ctx.config) — refused by name, never
    guessed, never silently defaulted."""

    __test__ = False      # not a pytest class (Stream A C46 review note a)


@dataclasses.dataclass(frozen=True)
class TestSlice:
    __test__ = False      # not a pytest class (Stream A C46 review note a)

    run: str
    horizon: tuple
    classes: tuple                     # in SCORED_CLASSES order
    marker: dict
    digest: str


def _manifest_digest(manifest) -> str:
    """sha256 of the canonical JSON of a run manifest — the SAME canonicalisation as the runner's
    `_canonical_manifest_digest` (recursively key-sorted objects, array order kept, ASCII-escaped, no spaces); a test pins the two
    equal on real manifests."""
    return hashlib.sha256(
        json.dumps(manifest, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _plan_manifest(ctx: ContextSpec) -> dict | None:
    """build_runs.plan_manifest for this run, or None when the run carries no manifest. Read through ctx.build_id +
    ctx.db_conn — never ctx.config. A schema without build_runs at all (the partial disposable mirrors the kernel's own DB
    tests build) is read inside a savepoint and treated as 'no marker' — a missing row and a missing table both mean the default
    path; a malformed marker NEVER does.

    EVERY read verifies the manifest against `plan_manifest_digest` (the runner verifies it once, at preflight, and the plan is
    fixed at asset start): a manifest that is present but whose digest is missing or does not match what is stored now was
    CHANGED after dispatch — the marker may have been added, removed or replaced mid-run — and is refused by name, never read.
    (Fable P1 on PR 3110: a key removed before the manifest substep stamped a full-horizon default candidate on a plan narrowed
    to one class.)"""
    if ctx.db_conn is None:
        # Connection-free PLANNING (a dry run that only lists the plan; the lifecycle and snapshot-order tests do this). Such a call
        # cannot read a marker and nothing executes, so it returns the default plan — ONLY for a dry run. A LIVE call with no
        # connection is a contract violation and is refused by name: a live run must never silently fall back to the default plan
        # because the marker could not be read.
        if ctx.dry_run:
            return None
        raise TestSliceRefusal(
            f"{ASSET_ID}: {TEST_SLICE_KEY}: a live plan needs a connection to read build_runs.plan_manifest — refused, never "
            "planned as the default (only a dry run may plan without one)")

    def read():
        return ctx.db_conn.execute(
            "SELECT plan_manifest, plan_manifest_digest FROM public.build_runs WHERE id = %s",
            (str(ctx.build_id),)).fetchone()
    try:
        row = _in_savepoint(ctx.db_conn, read)
    except Exception as exc:  # noqa: BLE001 - the driver module is never named here (writer purity);
        if type(exc).__name__ != "UndefinedTable":   # only an ABSENT table reads as 'no marker'
            raise
        return None
    if row is None:
        return None
    manifest = row[0] if not isinstance(row, dict) else row.get("plan_manifest")
    stored_digest = row[1] if not isinstance(row, dict) else row.get("plan_manifest_digest")
    if manifest is None:
        return None                      # a row with no manifest: the default path, as before
    if isinstance(manifest, str):
        try:
            manifest = json.loads(manifest)
        except ValueError as exc:
            raise TestSliceRefusal(
                f"{ASSET_ID}: {TEST_SLICE_KEY}: build_runs.plan_manifest is not valid JSON ({exc}) — refused, "
                "never read as 'no marker'") from exc
        if manifest is None:
            return None
    if not isinstance(manifest, dict):
        # P2-3 (Codex): an array that CONTAINS the marker used to read as 'no marker' and yield the full plan —
        # a writer that fails open. A manifest that is present must be an object.
        raise TestSliceRefusal(
            f"{ASSET_ID}: {TEST_SLICE_KEY}: build_runs.plan_manifest is {type(manifest).__name__}, not an object — "
            "refused, never read as 'no marker'")
    if not isinstance(stored_digest, str) or stored_digest != _manifest_digest(manifest):
        raise TestSliceRefusal(
            f"{ASSET_ID}: {TEST_SLICE_KEY}: build_runs.plan_manifest does not match its plan_manifest_digest "
            f"(stored digest {stored_digest!r}, manifest digest {_manifest_digest(manifest)!r}) — the manifest changed after "
            "dispatch (a marker added, removed or replaced mid-run is exactly that); refused, never read")
    return manifest


def _in_savepoint(conn, read):
    """Run `read` so that a failing read (an absent table) cannot poison the caller's transaction, WITHOUT ever being the
    one that commits: the orchestrator owns commit (frozen contract).

    On a connection that is IDLE and not autocommit, `conn.transaction()` would open its OWN outermost transaction and COMMIT it
    at exit — a writer-side commit (Fable P3: `plan_substeps` can be the first thing the driver calls on a fresh connection). There
    a manual SAVEPOINT is used: the first statement opens the connection's implicit transaction, which stays open and is never
    committed here. In every other state (already inside a transaction, or an autocommit test connection that has no outer
    transaction to disturb) `transaction()` is a real savepoint or the test harness's own."""
    tx = getattr(conn, "transaction", None)
    if tx is None:
        return read()
    status = getattr(getattr(conn, "info", None), "transaction_status", None)
    idle = status is not None and getattr(status, "name", str(status)) == "IDLE"
    if idle and not getattr(conn, "autocommit", False):
        conn.execute("SAVEPOINT gochara_v5_marker_read")
        try:
            out = read()
        except Exception:
            conn.execute("ROLLBACK TO SAVEPOINT gochara_v5_marker_read")
            raise
        conn.execute("RELEASE SAVEPOINT gochara_v5_marker_read")
        return out
    with tx():
        return read()


def _parse_slice_horizon(raw, outer=None) -> tuple:
    outer = DEFAULT_HORIZON if outer is None else outer          # callers pass the shape's own bound (`_outer_for_run`)
    def refuse(msg):
        raise TestSliceRefusal(f"{ASSET_ID}: {TEST_SLICE_KEY}: {msg}")
    if (not isinstance(raw, (list, tuple)) or len(raw) != 2
            or not all(isinstance(x, str) for x in raw)):
        refuse(f"horizon {raw!r} is not a pair of ISO timestamps — refused, never guessed")
    try:
        pts = tuple(datetime.fromisoformat(x) for x in raw)
    except (ValueError, OverflowError) as exc:
        refuse(f"horizon {raw!r} is not parseable ISO 8601 ({exc})")
    if any(p.tzinfo is None for p in pts):
        refuse(f"horizon {raw!r} carries a naive timestamp — an unstated zone is never guessed")
    try:
        start, end = (p.astimezone(timezone.utc) for p in pts)
    except (ValueError, OverflowError) as exc:      # e.g. 0001-01-01T00:00:00+01:00 overflows the UTC conversion
        refuse(f"horizon {raw!r} cannot be converted to UTC ({type(exc).__name__}: {exc})")
    if not start < end:
        refuse(f"horizon {raw!r} is empty or inverted")
    if start < outer[0] or end > outer[1]:
        refuse(f"horizon [{start.isoformat()}, {end.isoformat()}) reaches outside "
               f"{'DEFAULT_HORIZON' if tuple(outer) == tuple(DEFAULT_HORIZON) else 'the chart horizon'} "
               f"[{outer[0].isoformat()}, {outer[1].isoformat()}) — refused, never clipped")
    return (start, end)


def _outer_for_run(run, outer=None) -> tuple:
    """The outer horizon a marker of this run is validated against. `all_classes_full` (the measuring build): the scope validated from chart/run inputs
    when the caller has them, else the owner-approved MEASURING_HORIZON (staging and teardown stamp checks have no run inputs). Every other shape: DEFAULT_HORIZON, exactly as on main — an `outer` argument is only ever used for all_classes_full."""
    if run == MEASURING_RUN:
        return MEASURING_HORIZON if outer is None else outer
    return DEFAULT_HORIZON


def _validate_test_slice(marker, outer=None) -> TestSlice:
    """The marker, strictly. Every deviation is a named TestSliceRefusal — the writer never
    guesses a scope it was not explicitly given. `outer` is the chart's DERIVED horizon (FB-4) and applies to `all_classes_full` ONLY: the run-time call
    passes it, the dispatch's staging call and the teardown's stamp proof pass nothing (MEASURING_HORIZON). The two older shapes keep DEFAULT_HORIZON."""
    def refuse(msg):
        raise TestSliceRefusal(f"{ASSET_ID}: {TEST_SLICE_KEY}: {msg}")
    if not isinstance(marker, dict):
        refuse(f"marker is {type(marker).__name__}, not an object")
    extra = sorted(set(marker) - _TEST_SLICE_FIELDS)
    missing = sorted(_TEST_SLICE_FIELDS - set(marker))
    if extra:
        refuse(f"unexpected field(s) {extra} — the schema admits exactly {sorted(_TEST_SLICE_FIELDS)}")
    if missing:
        refuse(f"missing field(s) {missing}")
    if marker["schema"] != TEST_SLICE_SCHEMA:
        refuse(f"schema {marker['schema']!r} != {TEST_SLICE_SCHEMA!r}")
    run = marker["run"]
    if run not in TEST_SLICE_RUNS:
        refuse(f"unknown run {run!r} (known: {list(TEST_SLICE_RUNS)})")
    outer = _outer_for_run(run, outer)
    horizon = _parse_slice_horizon(marker["horizon"], outer)
    classes = marker["classes"]
    if (not isinstance(classes, list) or not classes
            or any(not isinstance(c, str) for c in classes)):
        refuse(f"classes {classes!r} is not a non-empty list of class names")
    unknown = [c for c in classes if c not in SCORED_CLASSES]
    if unknown:
        refuse(f"classes {unknown} are not scored classes (SCORED_CLASSES)")
    if len(set(classes)) != len(classes):
        refuse(f"classes {classes!r} names a class twice")
    if run == "all_classes_1y":
        if set(classes) != set(SCORED_CLASSES):
            refuse(f"run 'all_classes_1y' is all {len(SCORED_CLASSES)} scored classes, "
                   f"not {sorted(classes)}")
        if horizon[1] - horizon[0] > _ONE_YEAR:
            refuse(f"run 'all_classes_1y' is a 1-year horizon, not {horizon[1] - horizon[0]}")
    elif run == "all_classes_full":
        if set(classes) != set(SCORED_CLASSES):
            refuse(f"run 'all_classes_full' is all {len(SCORED_CLASSES)} scored classes, not {sorted(classes)}")
        if tuple(horizon) != tuple(outer):
            refuse("run 'all_classes_full' is the chart's whole derived horizon "
                   f"[{outer[0].isoformat()}, {outer[1].isoformat()}), not "
                   f"[{horizon[0].isoformat()}, {horizon[1].isoformat()})")
    else:  # one_class_full
        if len(classes) != 1:
            refuse(f"run 'one_class_full' is exactly one class, not {sorted(classes)}")
        if horizon != DEFAULT_HORIZON:
            refuse("run 'one_class_full' is the full DEFAULT_HORIZON, not "
                   f"[{horizon[0].isoformat()}, {horizon[1].isoformat()})")
    ordered = tuple(c for c in SCORED_CLASSES if c in set(classes))
    digest = hashlib.sha256(
        gk_input_vector.canonical_json(marker).encode("utf-8")).hexdigest()
    return TestSlice(run=run, horizon=horizon, classes=ordered, marker=dict(marker), digest=digest)


def _log_verify_outcome(substep_key: str, result: WriterResult) -> WriterResult:
    """VERIFIER-R2-GO: the in-build verification outcome reaches the run log — the runner never reads a substep's notes
    (the run exits 0 and the verdict is read from the database), so without this a class the verifier could not derive
    would be invisible. INFO for every verify/window outcome; WARNING when the notes say UNVERIFIED (a class or window the
    verifier could not independently derive: it cannot seal and does not satisfy a verification gate). Logging only: the
    result is returned unchanged, so the frozen orchestrator contract and the substep's stored outcome are untouched."""
    notes = result.notes or ""
    if "UNVERIFIED" in notes:
        logger.warning("%s: %s: %s", ASSET_ID, substep_key, notes)
    else:
        logger.info("%s: %s: %s", ASSET_ID, substep_key, notes)
    return result


def _test_slice(ctx: ContextSpec) -> TestSlice | None:
    """The run's validated test-slice marker, or None — the ABSENT key is today's behaviour,
    byte-identical."""
    manifest = _plan_manifest(ctx)
    if manifest is None or TEST_SLICE_KEY not in manifest:
        return None
    if ctx.config.get("gochara_v5_final_rules") is True:
        raise TestSliceRefusal("final_rules_require_candidate: a test slice always uses the measuring rules")
    marker = manifest[TEST_SLICE_KEY]
    # FB-4, `all_classes_full` ONLY (steward MB-CODEX-1 ruling 1): the marker's outer bound is the chart's DERIVED horizon whenever the run carries the chart's birth
    # parameters (the orchestrator always passes them), so a marker staged for a different horizon than the chart inputs now derive is refused by name. The two older
    # shapes (and a marker that is not an object, refused below by name) consume only the declared scope: they are validated against DEFAULT_HORIZON as on main.
    outer = None
    if isinstance(marker, dict) and marker.get("run") == MEASURING_RUN and ctx.config.get("birth_params") and ctx.db_conn is not None:
        outer = _derived_outer_bound(ctx)
    return _validate_test_slice(marker, outer)


def _slice_component(slice_: TestSlice) -> dict:
    """The manifest-vector component that makes a sliced candidate unsealable by construction: stored_scope='test_slice' (a
    value no verifier vocabulary knows) plus the marker digest — and, for audit (Fable P1 iii), the run shape, the classes and
    the horizon IN CLEAR, so a reader of the manifest alone sees how narrow the candidate is."""
    return {"schema": TEST_SLICE_SCHEMA, "marker_digest": slice_.digest, "run": slice_.run,
            "classes": list(slice_.classes), "horizon": [slice_.horizon[0].isoformat(), slice_.horizon[1].isoformat()]}


def _slice_excluded_agents(slice_: "TestSlice | None"):
    """The excluded transiting bodies the writer's IN-BUILD self-checks are TOLD under a validated marker: the DEFAULT stored scope's
    (`stored_non_moon` → the Moon), because a test slice narrows classes and horizon, never which bodies the stored tier holds. None
    without a marker: the verifiers then read the manifest's own scope exactly as before. (Stream B P1 on PR 3110: with the stored
    scope `test_slice`, `verify_p1_anchors` and the inventory re-derivation raised Unverifiable at the first P1 grain.) This changes
    only what the BUILD reports about itself; the verification JOB, the seal flow and serving always pass nothing and so still read
    the stored scope and refuse a sliced candidate by name."""
    if slice_ is None:
        return None
    return gk_verifier.excluded_agents_of_scope(gk_input_vector.STORED_SCOPE)


# ── gochara_v5_defer_in_build_verify (SR-W3-SHAPE item 3; DESIGN_NOTE_W3 §C) ──
# The in-build `verify:<class>` is a report-only SELF-CHECK: it persists no verification row, and the separate verification job
# (`services/gochara_kernel/verification_job.py:_verify_class`) re-derives the same inventory, ledger and contact-geometry digests before it
# writes the rows the gate and the seal read. A FINAL build may therefore defer it under this strict-boolean config key: the substep stays in
# the plan (the plan's length and order are unchanged) and returns the NAMED no-op `VERIFY_DEFERRED_STATUS`. The choice is an input of the
# build, bound into the manifest vector (`in_build_verify`), so a build that skipped the self-check is distinguishable from one that ran it
# (§N.8) and a run whose flag differs from its manifest drifts by name. REFUSED under any test-slice marker (the measuring build included: there
# the in-build verify is the ONLY producer of the STRETCH_SINK/1 records) and for a build that is not on the final rules. Absent or False =
# today's behaviour, byte-identical vector.
DEFER_VERIFY_KEY = "gochara_v5_defer_in_build_verify"
DEFER_VERIFY_SCHEMA = "gochara_v5_in_build_verify/1"
VERIFY_DEFERRED_STATUS = "deferred_to_independent_verification"


class DeferVerifyRefusal(ValueError):
    """`gochara_v5_defer_in_build_verify` is not a boolean, or is set on a run shape that must run its in-build verify — refused by
    name, never coerced, never ignored."""


def _defer_in_build_verify(ctx: ContextSpec, slice_: "TestSlice | None") -> bool:
    """True when this run defers its in-build `verify:<class>` (validated); False when the key is absent or False."""
    if DEFER_VERIFY_KEY not in ctx.config:
        return False
    value = ctx.config[DEFER_VERIFY_KEY]
    if type(value) is not bool:
        raise DeferVerifyRefusal(f"{ASSET_ID}: {DEFER_VERIFY_KEY} must be a boolean, got {value!r} — refused, never coerced")
    if not value:
        return False
    if slice_ is not None:
        raise DeferVerifyRefusal(
            f"{ASSET_ID}: {DEFER_VERIFY_KEY}: defer_verify_refused_for_test_slice — run {slice_.run!r} carries a "
            f"{TEST_SLICE_KEY} marker; a test slice or measuring build must run its in-build verify (the only producer of "
            f"{gk_stretch_sink.SCHEMA}); final builds only")
    if ctx.config.get("gochara_v5_final_rules") is not True:
        raise DeferVerifyRefusal(
            f"{ASSET_ID}: {DEFER_VERIFY_KEY}: defer_verify_requires_final_rules — only a final build (gochara_v5_final_rules "
            "true, no test-slice marker) may defer its in-build verify")
    return True


def _verify_component(defer: bool) -> dict | None:
    """The manifest-vector component recording a deferred in-build verify; None (no component) when the self-check runs."""
    return {"schema": DEFER_VERIFY_SCHEMA, "status": VERIFY_DEFERRED_STATUS} if defer else None


def _scope_normalised(vector: dict, slice_: TestSlice | None) -> dict:
    """The vector the in-build independent derivation check sees (Stream A C46 review R1/R1b, Codex P1-2):
    identical in EVERY component, with only the slice's identity removed — stored_scope back to the default and the
    test_slice key dropped. The STORED manifest vector keeps both, so the verification JOB still refuses a sliced
    manifest by name, while the BUILD still proves the ephemeris files, the library, the probe, L0, the registry and
    the implementation against the real image.

    The normalisation is bound to the run's VALIDATED marker (`_test_slice(ctx)`), never to what the vector says about
    itself: with no marker the vector is returned UNCHANGED (a default context has nothing to normalise; a stamp on its
    vector is refused by `verify_live` and by `verify_inputs` as before); with a marker ONLY a vector carrying exactly
    the scope `test_slice` AND exactly this marker's {schema, marker_digest} component is normalised — an empty
    component, a wrong digest, a missing or half stamp is a named refusal."""
    if slice_ is None:
        return dict(vector)
    expected = _slice_component(slice_)
    if vector.get("stored_scope") != TEST_SLICE_SCOPE or vector.get("test_slice") != expected:
        raise TestSliceRefusal(
            f"{ASSET_ID}: {TEST_SLICE_KEY}: the input vector's slice stamp (stored_scope={vector.get('stored_scope')!r}, "
            f"test_slice={vector.get('test_slice')!r}) is not the run's validated marker ({TEST_SLICE_SCOPE!r}, "
            f"{expected!r}) — refused, never normalised")
    v = dict(vector)
    v["stored_scope"] = gk_input_vector.STORED_SCOPE
    v.pop("test_slice", None)
    return v


_STATION_JD_CACHE: dict = {}


_STATION_REFINED_CACHE: dict = {}


def _station_instants_in(body: str, t0: datetime, t1: datetime, ephe_path: str | None) -> list[str]:
    """The STORED-PATH station instants (ISO, UTC) of `body` (DB lowercase) inside [t0, t1): the SEAM test and `station_at` of the sink (MB-2.3: the station row's
    `t_exact` is `station_at`). These are the instants the substrate STORES (`SkyEventStore.build_boundary_substrate`; `substrate.stored_station_instant` is that
    expression) for each station of the production arc index, NOT the arc index's own spline extrema, which differ from them by up to the measured spline bound
    (13 s for Mercury, February 2026). The arc index is `substrate.production_arc_index` (the one production function), cached per process; only the stations whose
    spline instant lies within the body's spline error bound of the window are refined, each once. A body with no stations has none."""
    from datetime import timedelta
    from services.gochara_kernel.knots import SPLINE_STATION_ERROR_BOUND_SECONDS
    from services.gochara_kernel.substrate import jd_to_utc, production_arc_index, stored_station_instant
    title = body.title()
    key = (body, ephe_path)
    if key not in _STATION_JD_CACHE:
        _STATION_JD_CACHE[key] = tuple(production_arc_index(title, ephe_path).stations)
    margin = timedelta(seconds=SPLINE_STATION_ERROR_BOUND_SECONDS.get(title, 0.0) + 5.0)
    out = []
    for jd in _STATION_JD_CACHE[key]:
        spline = jd_to_utc(jd)
        if not (t0 - margin <= spline < t1 + margin):
            continue
        if (title, jd, ephe_path) not in _STATION_REFINED_CACHE:
            _STATION_REFINED_CACHE[(title, jd, ephe_path)] = stored_station_instant(title, jd, ephe_path)
        refined = _STATION_REFINED_CACHE[(title, jd, ephe_path)]
        if t0 <= refined < t1:
            out.append(refined.isoformat())
    return out


def _stretch_sink_records(event_class: str, horizon, stretch_sink: list, position_at, ephe_path: str | None) -> list[dict]:
    """The class's STRETCH_SINK/1 records (MEASURING_BUILD_CONTRACT MB-2) from the certifier's per-stretch results; seams, wraps and horizon clipping are added
    here from the arc index, the ray levels and the ephemeris."""
    from datetime import timedelta
    from services.gochara_kernel.window_verifier import _ASPECT_ANGLES, _POINT_ORB_DEG

    def wrapped_inside(body: str, t0: datetime, t1: datetime) -> bool:
        n = max(2, min(200, int((t1 - t0).total_seconds() // 21600) + 2))                  # at most every six hours, never more than 200 samples
        lons = [float(position_at(body, t0 + (t1 - t0) * k / (n - 1))) for k in range(n)]
        return any(abs(b - a) > 180.0 for a, b in zip(lons, lons[1:]))
    return gk_stretch_sink.build_records(
        event_class=event_class, horizon=(horizon[0], horizon[1]), stretches=stretch_sink,
        stations_in=lambda body, t0, t1: _station_instants_in(body, t0, t1, ephe_path),
        levels_for=lambda body, relation, target: gk_stretch_sink.levels_of(relation, target, _ASPECT_ANGLES.get(body, ())),
        orb_for=lambda relation: _POINT_ORB_DEG.get(relation), body_wrapped_inside=wrapped_inside)


def _emit_stretch_sink(event_class: str, horizon, stretch_sink: list, position_at, ephe_path: str | None) -> dict:
    """Log the records (WARNING for a certification finding, INFO for the rest) and the per-class summary; return the summary."""
    records = _stretch_sink_records(event_class, horizon, stretch_sink, position_at, ephe_path)
    for r in records:
        logger.log(logging.WARNING if r["kind"] in gk_stretch_sink.WARNING_KINDS else logging.INFO, "%s", gk_stretch_sink.log_line(r))
    summary = gk_stretch_sink.summary(event_class, GENERATION, (horizon[0], horizon[1]), records, stretch_sink)
    logger.warning("%s", gk_stretch_sink.summary_line(summary))
    return summary


class AssetNotBuilding(RuntimeError):
    """The state guard: this asset's `asset_throughput` row for the chart exists and is not `building` — the orchestrator has given up on the asset
    (a fired `writer_timeout_seconds` marks it `error` and does NOT stop the writer thread), so a further substep must not write."""


def _require_building(ctx: ContextSpec, chart_id: str) -> None:
    """Steward TIMEOUT-RULING 2 / GUARD-PRECHECK-ACK: at the top of every substep ONE read of `asset_throughput.state` for (chart, asset) on ctx.db_conn,
    refused BY NAME when it is not `building`. NO write (reading is inside the frozen contract: section 5 forbids the writer WRITING asset_throughput;
    the orchestrator is the sole build-state writer). `run_asset` upserts and commits `building` before the first substep, the per-substep heartbeat
    never changes `state`, and an eviction by the watchdog commits `error` on another connection, which this READ COMMITTED read sees at the next
    substep: the post-timeout window is bounded to the substep already in flight.

    Skip-on-absent: with NO row (the writer driven directly by a harness or a unit test, or a schema without the table) there is nothing to read and
    the guard does not refuse; the real runner always has the row. Skipped for a dry run (nothing is written, and a dry run may have no `building` row)."""
    if ctx.dry_run or ctx.db_conn is None:
        return

    def read():
        return ctx.db_conn.execute(
            "SELECT state FROM public.asset_throughput WHERE chart_id = %s AND asset_id = %s", (chart_id, ASSET_ID)).fetchone()
    try:
        row = _in_savepoint(ctx.db_conn, read)
    except Exception as exc:  # noqa: BLE001 - the driver module is never named here (writer purity)
        if type(exc).__name__ != "UndefinedTable":
            raise
        return
    if row is None:
        return
    state = row["state"] if isinstance(row, dict) else row[0]
    if state != "building":
        raise AssetNotBuilding(
            f"asset_not_building: {ASSET_ID}: asset_throughput.state for chart {chart_id} is {state!r}, not 'building' — the orchestrator has given up on this asset "
            "(a writer timeout or an operator stop marks it error and does not stop this thread): no further substep is written")


class HorizonUnderivable(RuntimeError):
    """FB-2: no horizon was configured and one cannot be derived (no birth date, or no database): refused by name — a build never falls back to a
    constant horizon."""


def _as_date(value) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            pass
    raise HorizonUnderivable(f"{ASSET_ID}: birth date {value!r} is not a date — the horizon cannot be derived (refused, never guessed)")


def _row_values(row) -> tuple:
    return tuple(row.values()) if isinstance(row, dict) else tuple(row)


def _derive_horizon(ctx: ContextSpec, *, ruling: bool = True) -> "gk_horizon.ChartHorizon":
    """Validate the ruled measuring scope from chart/run inputs only.

    (I) INTERPRETATION: the standing circularity rail takes precedence over
    outcome-based scope selection. The measurement detector remains separate;
    the field records the ruled scope and consumes no outcome rows.
    """
    birth_params = ctx.config.get("birth_params")
    if not birth_params or birth_params.get("datetime_iso") in (None, ""):
        raise HorizonUnderivable(f"{ASSET_ID}: no birth date in ctx.config['birth_params']['datetime_iso'] — refused by name")
    if ctx.db_conn is None:
        raise HorizonUnderivable(f"{ASSET_ID}: no connection to read this build's date — refused by name")
    birth = _as_date(str(birth_params["datetime_iso"])[:10])
    chart_id = str(ctx.config["chart_id"])
    row = ctx.db_conn.execute("SELECT created_at FROM public.build_runs WHERE id = %s", (str(ctx.build_id),)).fetchone()
    if row is None:
        raise HorizonUnderivable(f"{ASSET_ID}: build run {ctx.build_id!r} has no created_at — refused by name")
    created = _row_values(row)[0]
    build_date = created.astimezone(timezone.utc).date() if isinstance(created, datetime) else _as_date(created)
    end_date = gk_horizon.add_years(birth, gk_horizon.HORIZON_YEARS)
    end = datetime(end_date.year, end_date.month, end_date.day, tzinfo=timezone.utc)
    start = MEASURING_HORIZON[0]
    if "horizon" in ctx.config:
        configured = ctx.config["horizon"]
        if isinstance(configured, (tuple, list)) and len(configured) == 2 and all(isinstance(day, datetime) for day in configured):
            configured = [day.isoformat() for day in configured]
        start, configured_end = _parse_slice_horizon(configured, (start, end))
        if configured_end != end:
            raise gk_horizon.HorizonDerivationDisagreesWithRuling("configured end is not the birth centenary")
    if start >= end:
        raise gk_horizon.HorizonEmpty(f"empty interval [{start}, {end})")
    if start.date() < birth:
        raise gk_horizon.HorizonStartBeforeBirth(f"the start {start} precedes birth {birth}")
    if start.date() > build_date:
        raise gk_horizon.HorizonStartInTheFuture(f"the start {start} follows build {build_date}")
    gk_horizon.require_inside_substrate_domain((start, end))
    if ruling and (start, end) != MEASURING_HORIZON:
        raise gk_horizon.HorizonDerivationDisagreesWithRuling(
            f"derived {[start.isoformat(), end.isoformat()]}, ruled {[day.isoformat() for day in MEASURING_HORIZON]}")
    return gk_horizon.ChartHorizon(start, end, gk_horizon.BASIS_RULED_HORIZON, chart_id=chart_id, build_date=build_date, birth_date=birth)


def _pinned_horizon_basis(ctx: ContextSpec) -> dict | None:
    """The `horizon_basis/1` record the candidate manifest pinned (its input vector), or None when no manifest vector exists yet (plan time, the manifest substep)
    or the vector carries no basis."""
    stored = InventoryStore(ctx.db_conn).manifest_vector(str(ctx.config["chart_id"]), GENERATION)
    return None if not isinstance(stored, dict) else stored.get("horizon_basis")


def _derived_outer_bound(ctx: ContextSpec) -> tuple:
    """The all_classes_full scope validated from chart/run inputs: the PINNED basis comes FIRST. Once the manifest has pinned a
    basis, current chart inputs are compared with it and a config edit that changed the derived horizon refuses
    `horizon_basis_horizon_changed`, not the ruling guard's token; the ruling guard (`horizon_derivation_disagrees_with_ruling`) applies at PLAN time and at the
    manifest substep, i.e. while nothing is pinned yet."""
    pinned = _pinned_horizon_basis(ctx)
    if pinned is None:
        return _derive_horizon(ctx).bounds
    live = _derive_horizon(ctx, ruling=False)
    _raise_if_horizon_changed(live.basis_record(), pinned)
    return live.bounds


def _horizon_basis(ctx: ContextSpec, slice_: "TestSlice | None") -> dict | None:
    """The record pinned in the manifest vector beside the horizon (MB-ADDITIONS 3; FB-2): the basis of the derivation the run's horizon was validated against, for
    the measuring build (an `all_classes_full` marker) AND — SR-J4E-HORIZON-BASIS — for a CENTURY build (unmarked, staged through `gochara_v5_century_config`; its
    candidate used to carry no pin, so the completion and teardown gates read FALSE on it). NOTHING otherwise: an ordinary build and the two older slice shapes get no
    basis component, so their vectors stay byte-identical to main's (steward MB-CODEX-1 ruling 1) — the discriminator is the staged century config, never merely 'a
    horizon is configured'. None also for a context without birth parameters or without a connection (a harness, a unit test)."""
    if not ctx.config.get("birth_params") or ctx.db_conn is None:
        return None
    if slice_ is None:
        if ctx.config.get(CENTURY_STAGED_KEY) is not True:
            return None
    elif slice_.run != MEASURING_RUN:
        return None
    return _derive_horizon(ctx, ruling=_pinned_horizon_basis(ctx) is None).basis_record()


def _effective_horizon(ctx: ContextSpec, slice_: TestSlice | None):
    """The marker's horizon under a slice; else EXACTLY what main used: `ctx.config.get("horizon", DEFAULT_HORIZON)` — an absent key is DEFAULT_HORIZON, an
    explicit null stays None (and fails downstream as it always did; Codex P2-4: it must not be quietly turned into the default). Ordinary builds retain their
    existing scope (steward MB-CODEX-1 ruling 1). Under a marker a config horizon that is present and null, or that CONTRADICTS the marker, is ambiguous —
    refused, never guessed."""
    if slice_ is None:
        return ctx.config.get("horizon", DEFAULT_HORIZON)
    if "horizon" in ctx.config:
        cfg = ctx.config["horizon"]
        if cfg is None or tuple(cfg) != tuple(slice_.horizon):
            raise TestSliceRefusal(
                f"{ASSET_ID}: {TEST_SLICE_KEY}: ctx.config['horizon'] {cfg!r} contradicts the "
                f"marker horizon {slice_.horizon!r} — refused, never guessed")
    return slice_.horizon


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
    # SR-OD1 D3 (B.3): the owner rulings the vedha operand stands on are part of the identity whenever a vedha source is bound
    if vedha_source() is not None:
        out += [{"id": rid, "factor": "vedha_attenuation@1.3.0", "rule": rule} for rid, rule in gk_vedha_source.RULINGS.items()]
    # R9-5: the PD level of P1 is explicitly authorised TESTIMONY under a named limitation (part of the identity)
    out.append({"id": gk_evaluator.P1_PD_RULING, "limitation": gk_evaluator.P1_PD_LIMITATION,
                "rule": "p1_pd_level_is_testimony_never_scored"})
    return out


EPHE_ENV_VAR = "SE_EPHE_PATH"
# The pinned Swiss Ephemeris files the kernel opens, with their sha256: ONE shared constant (services/gochara_kernel/ephemeris_pins.py),
# the same pins Dockerfile.pipeline checks at image build and CI checks at every download (a test asserts the places agree).
PINNED_EPHE_FILES = tuple(gk_ephemeris_pins.PINNED_SE1_SHA256)


class EphemerisConfigRefusal(RuntimeError):
    """The Swiss Ephemeris directory this run would use is not configured, is ambiguous, does not exist, lacks a pinned file, or is not the
    pinned bytes."""


_PIN_VERIFIED: dict[tuple, str] = {}        # (real path, size, mtime_ns) -> sha256 already verified against the pin, per process


def _verify_pinned_bytes(directory: Path, source: str) -> None:
    """Every pinned file must be the pinned BYTES (sha256), checked at EVERY substep so the body substeps and the manifest that binds the file
    digests run over the same corpus. The hash is cached per process by real path, size and mtime, so the cost is paid once; a file that is
    replaced or touched is hashed again."""
    for name, pinned in gk_ephemeris_pins.PINNED_SE1_SHA256.items():
        file = (directory / name)
        real = os.path.realpath(file)
        stat = os.stat(real)
        key = (real, stat.st_size, stat.st_mtime_ns)
        if _PIN_VERIFIED.get(key) == pinned:
            continue
        digest = hashlib.sha256(Path(real).read_bytes()).hexdigest()
        if digest != pinned:
            raise EphemerisConfigRefusal(
                f"{ASSET_ID}: {name} in the Swiss Ephemeris directory from {source} ({str(directory)!r}) is not the pinned corpus: "
                f"sha256 {digest} != pinned {pinned} — refused before any computation")
        _PIN_VERIFIED[key] = digest


def _ephe_path(ctx: ContextSpec) -> str:
    """The ephemeris directory for this substep. Resolution order: `ctx.config["ephe_path"]` when supplied (tests and any caller that
    supplies it keep their behaviour), else the process environment `SE_EPHE_PATH` — the variable the Swiss C library itself honours, which
    panchang_engine/swiss_backend.py requires, CI exports for every gochara test and Dockerfile.pipeline sets in the image (the real
    orchestrator never puts ephe_path in ctx.config, so a real build used to fail at the manifest substep, after the body phase).
    Why this name and not SWE_EPHE_PATH: ruling N-28 (panchang_engine/swiss_backend.py) makes SE_EPHE_PATH the single source of truth and
    states SWE_EPHE_PATH is NOT consulted; the pipeline image sets both to /app/ephe. The sibling v4.41 writer's resolver (config, then
    SWE_EPHE_PATH, then a dev-checkout default) is deliberately not copied: its silent default is what this resolver refuses.

    REFUSED BY NAME, no default: (1) neither supplied; (2) an EXPLICITLY supplied config value that is not a usable path (an empty string is
    refused, never read as 'absent': only a missing key or None falls back); (3) BOTH a config path and `SE_EPHE_PATH` present and not the
    same real directory — the Swiss library honours the environment variable itself even after `set_ephe_path(<config path>)`
    (panchang_engine/swiss_backend.py documents it), so two different directories would let calculations fall back to the other corpus;
    (4) not a directory; (5) a pinned file missing; (6) a pinned file whose sha256 is not the pin. Called from every substep, so the FIRST
    ('rules') refuses a mis-provisioned job in seconds, and every substep (bodies included) provably runs over the same pinned bytes."""
    supplied = "ephe_path" in ctx.config and ctx.config["ephe_path"] is not None
    env_value = os.environ.get(EPHE_ENV_VAR) or ""
    if supplied:
        configured = ctx.config["ephe_path"]
        if not isinstance(configured, (str, os.PathLike)) or not str(configured).strip():
            raise EphemerisConfigRefusal(
                f"{ASSET_ID}: ctx.config['ephe_path'] was supplied as {configured!r}, which is not a usable path — refused (only an "
                "absent key or None falls back to the environment)")
        path, source = str(configured), "ctx.config['ephe_path']"
        if env_value and os.path.realpath(env_value) != os.path.realpath(path):
            raise EphemerisConfigRefusal(
                f"{ASSET_ID}: ctx.config['ephe_path'] ({path!r}) and the environment variable {EPHE_ENV_VAR} ({env_value!r}) name "
                "different directories — refused: the Swiss library honours the environment variable too, so calculations could "
                "silently use the other corpus; make them the same directory or unset one")
    else:
        path, source = env_value, f"environment variable {EPHE_ENV_VAR}"
        if not path:
            raise EphemerisConfigRefusal(
                f"{ASSET_ID}: no Swiss Ephemeris directory is configured: ctx.config has no 'ephe_path' and {EPHE_ENV_VAR} is not set "
                "in the process environment — refused at the first substep, nothing built (the pipeline image sets "
                f"{EPHE_ENV_VAR}=/app/ephe; a job that overrides it must name a directory holding {list(PINNED_EPHE_FILES)})")
    directory = Path(path)
    if not directory.is_dir():
        raise EphemerisConfigRefusal(f"{ASSET_ID}: the Swiss Ephemeris directory from {source} ({path!r}) is not a directory — refused")
    missing = [name for name in PINNED_EPHE_FILES if not (directory / name).is_file()]
    if missing:
        raise EphemerisConfigRefusal(
            f"{ASSET_ID}: the Swiss Ephemeris directory from {source} ({path!r}) lacks the pinned file(s) {missing} — refused")
    _verify_pinned_bytes(directory, source)
    return path


class HorizonMismatch(RuntimeError):
    """A5.5f: this run's horizon is not the horizon its candidate manifest was published for."""


def _require_manifest_horizon(ctx: ContextSpec, chart_id: str, slice_: "TestSlice | None" = None) -> None:
    """Every chain-writing substep (snapshot, inventory, coverage, record, window, verify) passes through
    `_verify_live_inputs`, and so through this guard: the horizon this run is configured with must be EXACTLY the horizon
    its candidate manifest (kala_gochara_publication) was published for. Nothing used to compare the two, so an
    invocation that skipped the manifest/snapshot head under a different horizon could mix horizons in one generation
    (the contact insert would then refuse by name, but only at the first shared contact). Refused by name, nothing
    written, for a horizon longer OR shorter than the manifest's."""
    row = ctx.db_conn.execute(
        "SELECT lower(horizon), upper(horizon) FROM public.kala_gochara_publication"
        " WHERE chart_id = %s AND generation = %s", (chart_id, GENERATION)).fetchone()
    if row is None:
        raise RuntimeError(f"{ASSET_ID}: no candidate manifest for generation {GENERATION} — the manifest substep runs first")
    lo, hi = tuple(row.values()) if isinstance(row, dict) else tuple(row)
    horizon = _effective_horizon(ctx, slice_)          # the marker's horizon under a slice, else the configured one
    # exact instants: any difference, even sub-microsecond or a zone that moves the instant, refuses (fail-closed)
    if horizon is None or (lo, hi) != (horizon[0], horizon[1]):
        raise HorizonMismatch(
            f"{ASSET_ID}: horizon guard: this run's horizon {horizon!r} is not the candidate manifest's "
            f"[{lo.isoformat()}, {hi.isoformat()}) for chart {chart_id} generation {GENERATION} — refused, nothing "
            "written; a different horizon is a new build through the manifest substep, never a continuation")


class HorizonBasisHorizonChanged(RuntimeError):
    """`horizon_basis_horizon_changed`: a log edit changed the derived horizon after the manifest pinned it (MEASURING_BUILD_CONTRACT v1.0 MB-1.5)."""


def _raise_if_horizon_changed(live: dict, pinned: dict) -> None:
    """`horizon_basis_horizon_changed` when the live derivation's horizon or basis differs from the pinned one (MB-1.5)."""
    if live.get("horizon") != pinned.get("horizon") or live.get("basis") != pinned.get("basis"):
        raise HorizonBasisHorizonChanged(
            f"horizon_basis_horizon_changed: the derived horizon is now {live.get('horizon')} (basis {live.get('basis')}), the manifest pinned {pinned.get('horizon')} "
            f"(basis {pinned.get('basis')}); changed inputs: {gk_input_vector.diff_vectors({'horizon_basis': pinned}, {'horizon_basis': live})}")


def _live_basis_for_check(ctx: ContextSpec, slice_: "TestSlice | None", stored: dict):
    """Compare current chart/run inputs with the pinned scope before writing.

    Scope/basis changes refuse by name; other input changes are reported and
    retain the pinned basis. No outcome rows participate in this comparison.
    """
    live = _horizon_basis(ctx, slice_)
    pinned = stored.get("horizon_basis")
    if live is None or pinned is None or live == pinned:
        return live
    _raise_if_horizon_changed(live, pinned)
    logger.warning("horizon_basis_inputs_changed: %s", json.dumps(gk_input_vector.diff_vectors({"horizon_basis": pinned}, {"horizon_basis": live})))
    return pinned


def _verify_live_inputs(ctx: ContextSpec, chart_id: str) -> None:
    """R6: a substep must consume the inputs its manifest was bound to. The vector is recomputed from
    what is consumed NOW (registry rows, ephemeris files, orb policy, rulings, implementation) and
    compared; any drift is refused by component, never continued."""
    stored = InventoryStore(ctx.db_conn).manifest_vector(chart_id, GENERATION)
    if stored is None:
        raise RuntimeError(f"{ASSET_ID}: no candidate manifest vector for generation {GENERATION} — "
                           "the manifest substep runs first")
    # Codex P1-2: the expected scope and slice component come from the run's VALIDATED marker, never from the stored
    # vector being checked (verify_live used to copy them from it, so a sliced run accepted a default vector and a
    # default run a sliced one). Passed explicitly, a missing, changed or forged stamp is a named drift.
    slice_ = _test_slice(ctx)
    _require_manifest_horizon(ctx, chart_id, slice_)
    gk_input_vector.verify_live(
        ctx.db_conn, stored,
        sky_convention_id=SkyEventStore(ctx.db_conn).register_convention(),
        ephe_path=_ephe_path(ctx), path_refs=gk_rule_registry.bound_path_refs(),
        rulings=_applicable_rulings(),
        stored_scope=TEST_SLICE_SCOPE if slice_ is not None else gk_input_vector.STORED_SCOPE,
        # D-FLIP F-10: the expected scored edge comes from the governed source, never from the stored vector being checked (a forged pin drifts by name)
        scored_until=gk_input_vector.scored_until_instant(),
        # SR-W3-SHAPE 3: the expected deferral comes from the run's VALIDATED config, never from the stored vector (Codex P1-2)
        in_build_verify=_verify_component(_defer_in_build_verify(ctx, slice_)),
        test_slice=_slice_component(slice_) if slice_ is not None else None,
        horizon_basis=_live_basis_for_check(ctx, slice_, stored))
    # ... and every component that can be derived WITHOUT the builder's code is (registry + L0 + sky in
    # Postgres, ephemeris files + runtime library + implementation by direct hashing). Under a slice the
    # check runs on the SCOPE-NORMALISED copy: the stored vector's unknown scope is the unsealability
    # proof and belongs to the verification job — the build still proves the real image (R1).
    gk_input_vector_verifier.verify_inputs(
        ctx.db_conn, _scope_normalised(stored, slice_), ephe_path=_ephe_path(ctx),
        modules=gk_input_vector.IMPLEMENTATION_MODULES, path_refs=gk_rule_registry.bound_path_refs(),
        require_scored_classes=True, require_scored_until=True)


def _p1_form_b_bound() -> bool:
    """D2: does the bound catalogue contain a P1 version whose soft-factor rows declare the owner's Form B table (P1@1.3.0)? The answer
    follows the registry, not a flag: the day `("P1", "1.3.0")` joins `BOUND_PATH_REFS` the build consumes P1's L0 tables and numbers P1."""
    from services.gochara_rules import p1_valence as _pv, registry as _rules_registry
    return any(pid == "P1" and _pv.has_form_b([_rules_registry.FACTORS[ref] for ref in _rules_registry.RULE_PATHS[(pid, ver)]["soft_factors"]])
               for pid, ver in gk_rule_registry.bound_path_refs())


def _l0_consumed() -> tuple[str, ...]:
    """The L0 authorities this build ACTUALLY consumes (R8-1). The vedha pairs feed P2's vedha operand only;
    while the vedha source is unbound (`vedha_source()`) nothing reads them, so `bg_transit_rules` is not a dependency of the
    build and is neither loaded nor bound. The same rule holds for P1's three reference tables: they are consumed only when the P1 operand
    sources are bound (`P1_VALUE_RULES`, or a bound P1 version that declares the Form B table)."""
    return (("bg_transit_rules",) if vedha_source() is not None else ()) \
        + (("bg_combustion_orbs", "bg_dignity_reference", "bg_graha_naisargika_friendship")
           if P1_VALUE_RULES is not None or _p1_form_b_bound() else ())


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


def _p1_consulted_dasha_keys(chart: dict, classes) -> set[tuple[str, int | None]]:
    """The (lord, level_n) pairs the record grain reads daśā rows for: for every P1 TRANSIT edge of the classes, its ANCHOR
    lord (`period_anchor_lord`, else the agent) at its anchor level (`None` = every level, the legacy union) — the same
    key `materialise_record_grain._p1_running_support` hands to `make_period_rows_for` (AM-21 part 2)."""
    keys: set[tuple[str, int | None]] = set()
    for event_class in classes:
        for edge in gk_evaluator.enumerate_edges(
                event_class, "P1", chart, rule_version=gk_rule_registry.selected_path_version(event_class, "P1")):
            if edge.transit:
                keys.add(((edge.period_anchor_lord or edge.agent).lower(),
                          LEVEL_N[edge.period_anchor_level] if edge.period_anchor_level else None))
    return keys


def _class_of_grain(key: str) -> str | None:
    """The event class a per-class substep key names, or None for a class-less substep."""
    if key.startswith((INVENTORY_SUBSTEP_PREFIX, COVERAGE_SUBSTEP_PREFIX, VERIFY_SUBSTEP_PREFIX)):
        return key.split(":", 1)[1]
    if key.startswith((RECORD_SUBSTEP_PREFIX, WINDOW_SUBSTEP_PREFIX)):
        return key.split(":", 2)[1]
    return None


# ── gochara_v5_century_config (F-CHANNEL; SR-W34-PREP-RULINGS 1) ──────────────────────────────────────────────────────────────────────────
# The production orchestrator builds `ctx.config` from chart_id and birth_params ONLY (the FROZEN asset_runner), so an unmarked (century) run had no way to
# receive the final-rule profile, the verify-deferral switch or the horizon and ran the measuring profile over the code-default horizon. The century
# dispatch now STAGES them in `build_runs.plan_manifest[gochara_v5_century_config]`; that manifest is covered by `plan_manifest_digest`, which every read
# below verifies (`_plan_manifest`), so the three values are fixed at dispatch and a change mid-run is refused by name. The writer overlays them on
# `ctx.config` (where the rest of the writer already reads them) and then REFUSES a run that is not a test slice and still has no explicit rule profile
# or no explicit horizon — never a silent default to the measuring profile or to DEFAULT_HORIZON.
# OD-1 (SR-OD1-NUMERICAL): the numeric-RESULT policy is a fourth staged value (schema /2). The century build is the first NUMERICAL-policy build, so its
# policy is chosen by the dispatch and named in the config; `DEFAULT_RESULT_POLICY` (all-null) stays the default of measuring / test runs ONLY, and a final-rules
# run that arrives with no explicit `result_policy` is refused by name (`run_result_policy_required`).
CENTURY_CONFIG_KEY = "gochara_v5_century_config"
CENTURY_CONFIG_SCHEMA = "gochara_v5_century_config/2"
_CENTURY_CONFIG_FIELDS = frozenset({"schema", "final_rules", "defer_in_build_verify", "horizon", "result_policy"})
_RESULT_POLICY_KEY = "result_policy"
#: set by `_resolve_run_config` (and by nothing else) on a run whose plan manifest carries the century config: the writer's own record that this is a CENTURY build — it
#: gates the committed-substep ledger / resume and the horizon_basis pin. A caller that supplies it is refused (a harness cannot switch a run into century mode by config).
CENTURY_STAGED_KEY = "gochara_v5_century_staged"
#: SR-RESUME-EXPLICIT-BINDING: the plan_manifest key the executor's century_resume binding stages (`gk_build_ledger.RESUME_BINDING_KEY`) and, once validated, the writer's own
#: record of it in the resolved config — set by `_resolve_run_config` and by nothing else. It is the ONLY signal that lets a run resume over ledger rows.
RESUME_BINDING_KEY = gk_build_ledger.RESUME_BINDING_KEY
RESUME_BINDING_STAGED_KEY = "gochara_v5_century_resume_binding"
_FINAL_RULES_KEY = "gochara_v5_final_rules"
#: SR-B1-Q3C-JOB: the trial's explicit selection of P1@1.3.0 (Form B, the Q3(c) side rule). Absent / False = today's behaviour, byte-identical. It is not a
#: century-config field: only a trial harness (`j4d_slice_qualify --p1-form-b`) sets it, so a production dispatch can never carry it.
_P1_FORM_B_KEY = "gochara_v5_p1_form_b"


def _p1_form_b_kwargs(ctx) -> dict:
    """The profile's `p1_form_b` argument iff the run's config names the key — the default call stays exactly `rule_profile(final_rules=...)`."""
    return {"p1_form_b": ctx.config[_P1_FORM_B_KEY]} if _P1_FORM_B_KEY in ctx.config else {}
_CENTURY_DEFER_KEY = "gochara_v5_defer_in_build_verify"


class CenturyConfigRefusal(ValueError):
    """The gochara_v5_century_config component of build_runs.plan_manifest is malformed or contradicts ctx.config — refused by name, never guessed."""


class RunProfileRefusal(CenturyConfigRefusal):
    """run_rule_profile_required: a run that is not a test slice arrived with no explicit gochara_v5_final_rules — it would have run the measuring profile."""


class RunResultPolicyRefusal(CenturyConfigRefusal):
    """run_result_policy_required: a final-rules run arrived with no explicit result_policy — it would have run the all-null default (OD-1)."""


class RunHorizonRefusal(CenturyConfigRefusal):
    """run_horizon_required: a run that is not a test slice arrived with no explicit horizon — it would have run the code-default DEFAULT_HORIZON."""


def validate_century_config(raw) -> dict:
    """The canonical century-config component, or a named refusal. Used at staging (the dispatch) and at run time (the writer), so what is staged is by construction
    what the writer accepts. `horizon` is the two derived bounds as tz-aware ISO timestamps (stored in UTC, half-open, inside the substrate domain)."""
    def refuse(msg):
        raise CenturyConfigRefusal(f"{ASSET_ID}: {CENTURY_CONFIG_KEY}: {msg} — refused, never guessed")
    if not isinstance(raw, dict):
        refuse(f"the component is {type(raw).__name__}, not an object")
    if set(raw) != _CENTURY_CONFIG_FIELDS:
        refuse(f"fields {sorted(raw)} are not exactly {sorted(_CENTURY_CONFIG_FIELDS)}")
    if raw["schema"] != CENTURY_CONFIG_SCHEMA:
        refuse(f"schema {raw['schema']!r} is not {CENTURY_CONFIG_SCHEMA!r}")
    for field in ("final_rules", "defer_in_build_verify"):
        if type(raw[field]) is not bool:
            refuse(f"{field} {raw[field]!r} is not a boolean")
    if raw["defer_in_build_verify"] and not raw["final_rules"]:
        refuse("defer_in_build_verify needs final_rules (only a final build may defer its in-build verify)")
    if raw["result_policy"] not in gk_result_policy.RESULT_POLICIES:
        refuse(f"result_policy {raw['result_policy']!r} is not one of {gk_result_policy.RESULT_POLICIES}")
    horizon = raw["horizon"]
    if not isinstance(horizon, (list, tuple)) or len(horizon) != 2 or not all(isinstance(x, str) for x in horizon):
        refuse(f"horizon {horizon!r} is not a pair of ISO timestamps")
    try:
        points = tuple(datetime.fromisoformat(x) for x in horizon)
    except (ValueError, OverflowError):
        refuse(f"horizon {horizon!r} is not parseable ISO 8601")
    if any(p.tzinfo is None for p in points):
        refuse(f"horizon {horizon!r} carries a naive timestamp")
    try:
        start, end = (p.astimezone(timezone.utc) for p in points)
    except (ValueError, OverflowError):
        refuse(f"horizon {horizon!r} cannot be converted to UTC")
    if not start < end:
        refuse(f"horizon {horizon!r} is empty or inverted")
    gk_horizon.require_inside_substrate_domain((start, end))
    return {"schema": CENTURY_CONFIG_SCHEMA, "final_rules": raw["final_rules"], "defer_in_build_verify": raw["defer_in_build_verify"],
            "horizon": [start.isoformat(), end.isoformat()], "result_policy": raw["result_policy"]}


def _resolve_run_config(ctx: ContextSpec) -> ContextSpec:
    """`ctx` with the staged century config overlaid on its config, and the explicit-profile / explicit-horizon guard applied to every run that is not a test slice.
    A test slice (the measuring build included) is exempt: it sets its scope in its marker and its rules are always the measuring ones. A dry run executes
    nothing (it plans without a connection), so the guard does not apply to it; the overlay still does when a manifest is readable.
    Called by `plan_substeps` and, after its configuration checks, by `run_substep` — never at entry, so a mis-provisioned job still refuses before any database use."""
    if CENTURY_STAGED_KEY in ctx.config:
        raise CenturyConfigRefusal(f"{ASSET_ID}: {CENTURY_STAGED_KEY} is set by the writer from the staged {CENTURY_CONFIG_KEY} and by nothing else — refused, never accepted from the caller")
    if RESUME_BINDING_STAGED_KEY in ctx.config:
        raise CenturyConfigRefusal(f"{ASSET_ID}: {RESUME_BINDING_STAGED_KEY} is set by the writer from the staged {RESUME_BINDING_KEY} and by nothing else — refused, never accepted from the caller")
    manifest = _plan_manifest(ctx)
    marked = manifest is not None and TEST_SLICE_KEY in manifest
    if manifest is not None and CENTURY_CONFIG_KEY in manifest:
        if marked:
            raise CenturyConfigRefusal(f"{ASSET_ID}: {CENTURY_CONFIG_KEY}: a run carrying a {TEST_SLICE_KEY} marker takes no century config — refused, never guessed")
        staged = validate_century_config(manifest[CENTURY_CONFIG_KEY])
        wanted = {_FINAL_RULES_KEY: staged["final_rules"], _CENTURY_DEFER_KEY: staged["defer_in_build_verify"],
                  "horizon": tuple(datetime.fromisoformat(x) for x in staged["horizon"]), _RESULT_POLICY_KEY: staged["result_policy"]}
        merged = dict(ctx.config)
        merged[CENTURY_STAGED_KEY] = True
        for key, value in wanted.items():
            present = merged.get(key)
            if key in merged and (tuple(present) if key == "horizon" and isinstance(present, (list, tuple)) else present) != value:
                raise CenturyConfigRefusal(f"{ASSET_ID}: {CENTURY_CONFIG_KEY}: ctx.config[{key!r}] {present!r} contradicts the staged value {value!r} — refused, never guessed")
            merged[key] = value
        if RESUME_BINDING_KEY in manifest:           # SR-RESUME-EXPLICIT-BINDING: validated here, judged against the ledger in `_resume_plan`
            merged[RESUME_BINDING_STAGED_KEY] = gk_build_ledger.validate_resume_binding(manifest[RESUME_BINDING_KEY])
        ctx = dataclasses.replace(ctx, config=merged)
    elif manifest is not None and RESUME_BINDING_KEY in manifest:
        raise ResumeRefused("resume_binding_without_century_config",
                            f"{ASSET_ID}: {RESUME_BINDING_KEY} is staged on a run that carries no {CENTURY_CONFIG_KEY}: only a century run resumes — refused, never guessed")
    if not marked and not ctx.dry_run:
        if ctx.config.get(_FINAL_RULES_KEY) is None:
            raise RunProfileRefusal(f"{ASSET_ID}: run_rule_profile_required: this run is not a test slice and names no {_FINAL_RULES_KEY} — "
                                    "it would run the measuring rule profile; stage it through the century dispatch (final_rules)")
        if ctx.config.get("horizon") is None:
            raise RunHorizonRefusal(f"{ASSET_ID}: run_horizon_required: this run is not a test slice and names no horizon — it would run the "
                                    "code-default DEFAULT_HORIZON; stage it through the century dispatch (horizon)")
        # OD-1: a final-rules run names its numeric-result policy; the all-null default belongs to measuring / test runs only (F-CHANNEL)
        if ctx.config.get(_FINAL_RULES_KEY) is True and ctx.config.get(_RESULT_POLICY_KEY) is None:
            raise RunResultPolicyRefusal(f"{ASSET_ID}: run_result_policy_required: this final-rules run is not a test slice and names no {_RESULT_POLICY_KEY} — "
                                         "it would run the all-null default policy; stage it through the century dispatch (result_policy)")
    return ctx


def _with_rule_profile(method):
    """Pre-build isolation: final rules require explicit candidate configuration."""
    from functools import wraps

    @wraps(method)
    def profiled(self, ctx, *args, **kwargs):
        final = ctx.config.get("gochara_v5_final_rules", False)
        with gk_rule_registry.rule_profile(final_rules=final, **_p1_form_b_kwargs(ctx)):
            return method(self, ctx, *args, **kwargs)
    return profiled


# ── the committed-substep ledger / writer-side resume (SR-RESUME-NOW; OWNER-RESUMABLE-REQUIRED-20261025; migration 1410) ──────────────────────────────
# The frozen orchestrator never feeds `completed_keys`, so a failed century build restarted from zero. The writer therefore plans only what is not yet done:
# every substep of a CENTURY build (a run staged through `gochara_v5_century_config`) records itself in `ka_gochara_build_ledger` inside its own transaction,
# and a later dispatch whose ledger exists resumes — after `build_ledger` has proved the program, the horizon, the manifest and every recorded substep's rows
# unchanged — by skipping the recorded substeps INCLUDING `manifest` and `snapshot` (the head: `snapshot` replaces the whole chain, `manifest` would silently
# rebind the input vector to the new code). Any difference refuses by name (`ResumeRefused`): a program fix means teardown + a fresh build. Every other run (a
# test slice, the measuring build, a harness) takes the whole-build plan exactly as before: no ledger rows, no resume.
# SR-RESUME-EXPLICIT-BINDING: the ledger alone authorises nothing. A run resumes ONLY when its staged plan_manifest carries `gochara_v5_century_resume` (the executor's
# century_resume binding: the resumed run, the program identity, the ordered ledgered substeps) and that binding describes exactly the ledger; a century run WITHOUT it
# that finds rows another run ledgered refuses `fresh_run_found_ledger` (it never resumes and never deletes).
ResumeRefused = gk_build_ledger.ResumeRefused


def _ledger_active(ctx: ContextSpec) -> bool:
    """True only for a run that is staged as a century build: `_resolve_run_config` found `gochara_v5_century_config` (and no test-slice marker) in its plan manifest and
    said so in the resolved config. Reads nothing: an ordinary run's statements are exactly main's. A dry run executes nothing and a run without a connection
    cannot record, so neither records or resumes. (I) INTERPRETATION: the gate is the staged century config, the one signal the production orchestrator can deliver
    (it builds ctx.config from chart_id and birth_params only), so slices keep their replay semantics."""
    return not ctx.dry_run and ctx.db_conn is not None and ctx.config.get(CENTURY_STAGED_KEY) is True


def _writer_digest() -> str:
    from pipeline.orchestrator.writer_runtime_support import get_writer_source_hash
    return get_writer_source_hash(ASSET_ID)


def _ledger_binding(ctx: ContextSpec, keys) -> "gk_build_ledger.Binding":
    """The identity of the program running NOW, against which every ledger row is judged."""
    horizon = tuple(h.astimezone(timezone.utc) for h in _effective_horizon(ctx, None))
    return gk_build_ledger.Binding(
        implementation_digest=gk_window_gate.implementation_digest(), writer_digest=_writer_digest(), horizon=horizon,
        plan_digest=gk_build_ledger.plan_digest(
            asset_id=ASSET_ID, keys=keys, final_rules=ctx.config.get(_FINAL_RULES_KEY),
            defer_in_build_verify=ctx.config.get(_CENTURY_DEFER_KEY, False), result_policy=ctx.config.get(_RESULT_POLICY_KEY), horizon=horizon))


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

    @_with_rule_profile
    def plan_substeps(self, ctx: ContextSpec) -> list[SubStep]:
        """Plan (pin 5): 'rules' → 'convention' → 'body:<Body>' ×8.

        Static by design: the rule catalogue, the convention vector and the
        8-body substrate set are pinned constants (Moon excluded — EPHEMERAL
        per pin 6). The chart-scope refusal lives here too — a foreign chart
        is refused at PLAN time, not first at execution time.

        C46 test slice: a gochara_v5_test_slice marker in the run's
        plan_manifest narrows the class loop to the marker's classes; no
        marker = the full SCORED_CLASSES plan, byte-identical to today."""
        ctx = _native_ctx(ctx)
        _require_pinned_chart(ctx.config["chart_id"])
        ctx = _resolve_run_config(ctx)         # F-CHANNEL: the staged century config overlaid; an unmarked run without an explicit profile / horizon refused
        slice_ = _test_slice(ctx)
        _defer_in_build_verify(ctx, slice_)         # SR-W3-SHAPE 3: a refused flag is refused at PLAN time; the plan itself never changes
        classes = slice_.classes if slice_ is not None else SCORED_CLASSES
        steps = self._full_plan(classes)
        if not _ledger_active(ctx):
            return steps                            # no century ledger: EXACTLY the whole-build plan, as before (every slice, measuring and harness run)
        return self._resume_plan(ctx, steps)

    @staticmethod
    def _full_plan(classes) -> list[SubStep]:
        """The whole plan for `classes`, unfiltered — the plan of every fresh build and the reference a resume plans against."""
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
        for event_class in classes:
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

    def _resume_plan(self, ctx: ContextSpec, steps: list[SubStep]) -> list[SubStep]:
        """The plan of a CENTURY run: the whole plan when the ledger of (chart, generation) is empty (a fresh build, byte for byte as before), else the plan minus
        the recorded substeps after the resume has been proved safe. READ ONLY (the SATYA-DIPA probe calls this inside a savepoint)."""
        chart_id = str(ctx.config["chart_id"])
        keys = [s.key for s in steps]

        binding = ctx.config.get(RESUME_BINDING_STAGED_KEY)

        def resume():
            entries = gk_build_ledger.load(ctx.db_conn, chart_id, GENERATION)
            if binding is None:
                gk_build_ledger.check_not_a_fresh_run_over_a_ledger(entries, ctx.build_id)   # SR-RESUME-EXPLICIT-BINDING: a ledger alone never authorises a skip
            else:
                gk_build_ledger.check_resume_binding(binding, entries, ctx.build_id)         # the explicit binding must describe exactly the ledger it continues
            if not entries:
                return steps
            gk_build_ledger.check_binding(entries, _ledger_binding(ctx, keys), keys)
            if any(e.substep_key == MANIFEST_SUBSTEP for e in entries):
                gk_build_ledger.check_manifest(ctx.db_conn, chart_id, GENERATION, entries, require_horizon_basis=bool(ctx.config.get("birth_params")))
                try:
                    _verify_live_inputs(ctx, chart_id)       # the live ephemeris / library / registry / implementation inputs still equal the manifest's vector
                except (gk_input_vector.InputDrift, HorizonMismatch, HorizonBasisHorizonChanged) as exc:
                    raise ResumeRefused("resume_program_changed", f"{type(exc).__name__}: {exc}") from exc
                except EphemerisConfigRefusal:
                    raise
                except RuntimeError as exc:                   # verify_inputs: the independent derivation disagrees with the manifest
                    raise ResumeRefused("resume_program_changed", f"{type(exc).__name__}: {exc}") from exc
            gk_build_ledger.verify_chain(ctx.db_conn, chart_id, GENERATION, entries)
            done = {e.substep_key for e in entries}
            return [s for s in steps if s.key not in done]
        return _in_savepoint(ctx.db_conn, resume)

    def _record_ledger(self, ctx: ContextSpec, step: SubStep, chart_id: str, result: WriterResult) -> None:
        """The last act of a substep of a century run: its ledger row, in the SAME transaction (the orchestrator commits after it). Never commits."""
        if not _ledger_active(ctx):
            return
        keys = [s.key for s in self._full_plan(SCORED_CLASSES)]
        if step.key not in keys:
            return
        ordinal = keys.index(step.key)
        manifest_id = vec = None
        if ordinal >= keys.index(MANIFEST_SUBSTEP):
            ident = gk_build_ledger.manifest_identity(ctx.db_conn, chart_id, GENERATION)
            if ident is not None:
                manifest_id, vec = ident[0], ident[2]
        scope, scope_digest = gk_build_ledger.measure_scope(ctx.db_conn, chart_id, GENERATION, step.key)
        gk_build_ledger.record(
            ctx.db_conn, chart_id, GENERATION, key=step.key, ordinal=ordinal, binding=_ledger_binding(ctx, keys), manifest_id=manifest_id,
            vec_sha=vec, build_run_id=ctx.build_id, rows_written=int(result.rows_inserted or 0), scope=scope, scope_digest=scope_digest)

    @_with_rule_profile
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
        _ephe_path(ctx)         # every substep resolves it, so the FIRST ('rules') refuses a mis-provisioned job in seconds (no database use)
        # F-CHANNEL: the staged century config is overlaid and an unmarked run without an explicit profile / horizon refused HERE — after the configuration checks
        # above (no database use before them) and before the first read of the rule profile; the rest of the substep runs under the RESOLVED profile.
        ctx = _resolve_run_config(ctx)
        with gk_rule_registry.rule_profile(final_rules=ctx.config.get(_FINAL_RULES_KEY, False), **_p1_form_b_kwargs(ctx)):
            return self._run_resolved_substep(ctx, step, chart_id)

    def _run_resolved_substep(self, ctx: ContextSpec, step: SubStep, chart_id: str) -> WriterResult:
        """The substep proper, under the resolved config and rule profile (see `run_substep`), then — for a century run — its ledger row in the same transaction."""
        result = self._execute_substep(ctx, step, chart_id)
        self._record_ledger(ctx, step, chart_id, result)
        return result

    def _execute_substep(self, ctx: ContextSpec, step: SubStep, chart_id: str) -> WriterResult:
        """The substep proper (see `_run_resolved_substep`)."""
        # DELIBERATE CHANGE TO EVERY v5 BUILD (steward MB-CODEX-2 ruling 2), not only the measuring shape: the state guard. The frozen runner's watchdog marks an asset
        # `error` on a fired `writer_timeout_seconds` and does NOT stop the writer thread, so an evicted thread could keep committing substeps; the final build needs this
        # protection too. A healthy build (state `building`) behaves exactly as before apart from this one read-only SELECT per substep; a dry run and an absent row skip it;
        # any other state refuses `asset_not_building` BEFORE any write.
        _require_building(ctx, chart_id)
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
        # the slice read comes AFTER the chart lock: the lock stays the first statement of every
        # substrate substep (ruling B / N13), and an out-of-slice grain writes nothing either way
        slice_ = _test_slice(ctx)
        grain_class = _class_of_grain(step.key)
        if slice_ is not None and grain_class is not None and grain_class not in slice_.classes:
            # Fable P1 (scenario B): this used to RETURN success, so a marker replaced mid-run quietly skipped every grain
            # outside the new marker. The plan is fixed at asset start from the marker then read; a substep for a class the
            # marker now read does not name means the two disagree: refused by name, never skipped.
            raise TestSliceRefusal(
                f"{ASSET_ID}: {TEST_SLICE_KEY}: substep {step.key!r} names class {grain_class!r}, which is not in the run's "
                f"validated marker {list(slice_.classes)} — the plan and the marker disagree (the stored plan_manifest changed "
                "after the plan was fixed); refused, never skipped")
        if step.key == CONVENTION_SUBSTEP:
            store = SkyEventStore(ctx.db_conn)
            cid = store.register_convention()
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                notes=f"convention {cid[:24]}… registered (idempotent)")
        if (step.key in (MANIFEST_SUBSTEP, SNAPSHOT_SUBSTEP)
                or step.key.startswith((INVENTORY_SUBSTEP_PREFIX, VERIFY_SUBSTEP_PREFIX))):
            if step.key != MANIFEST_SUBSTEP:
                _verify_live_inputs(ctx, chart_id)
            result = self._run_inventory_phase(ctx, step, chart_id, slice_)
            return _log_verify_outcome(step.key, result) if step.key.startswith(VERIFY_SUBSTEP_PREFIX) else result
        if step.key.startswith((COVERAGE_SUBSTEP_PREFIX, RECORD_SUBSTEP_PREFIX)):
            _verify_live_inputs(ctx, chart_id)
            return self._run_record_phase(ctx, step, chart_id, slice_)
        if step.key.startswith(WINDOW_SUBSTEP_PREFIX):
            _verify_live_inputs(ctx, chart_id)
            return _log_verify_outcome(step.key, self._run_window_phase(ctx, step, chart_id))
        body = step.key[len(BODY_SUBSTEP_PREFIX):]
        if body not in SUBSTRATE_BODIES:
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                notes=f"unknown body substep {step.key!r}")
        ephe_path = _ephe_path(ctx)
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
                             chart_id: str, slice_: TestSlice | None = None) -> WriterResult:
        """AM-5 chain (chart lock already taken by the caller; every INVENTORY write takes
        the global SHARED key after it — chart → global SHARED, draft item 7):
        `manifest` → `snapshot` → `inventory:<class>` → (coverage, records) →
        `verify:<class>`. Sealing is NOT this writer's step (A6)."""
        horizon = _effective_horizon(ctx, slice_)
        ephe_path = _ephe_path(ctx)
        inv_store = InventoryStore(ctx.db_conn)
        rstore = RecordStore(ctx.db_conn)

        if step.key == MANIFEST_SUBSTEP:
            if slice_ is not None and slice_.run == MEASURING_RUN:
                gk_horizon.require_inside_substrate_domain((horizon[0], horizon[1]))        # FB-3 for the measuring build's derived horizon (refused by name, never clipped)
            sky_cid = SkyEventStore(ctx.db_conn).register_convention()
            kala_cid = rstore.ensure_kala_convention()
            rstore.ensure_bridge(kala_cid, sky_cid)
            vector = gk_input_vector.build_input_vector(
                ctx.db_conn, sky_convention_id=sky_cid, ephe_path=ephe_path,
                path_refs=gk_rule_registry.bound_path_refs(), rulings=_applicable_rulings(),
                l0_consumed=_l0_consumed(),
                # R9-1: the policy is an INPUT of the build, chosen here and bound into the manifest; every later
                # stage reads it back FROM the manifest — nothing downstream holds its own constant
                result_policy=ctx.config.get("result_policy", gk_input_vector.DEFAULT_RESULT_POLICY),
                # G8: the EXPECTED class census this generation is built for, pinned in the manifest vector; the verification job
                # re-derives it from the verifier's own universe and the seal-time completeness function (migration 1306) compares
                # the claimed classes with it
                scored_classes=SCORED_CLASSES,
                # D-FLIP F-10: the exclusive end of the scored horizon, from the evaluation protocol's observation-mask end (never a constant here); the served surface
                # marks windows past it unscored, and the independent verifier re-derives it from the same governed source
                scored_until=gk_input_vector.scored_until_instant(),
                # C46: a sliced build is unsealable by construction — stored_scope no verifier
                # vocabulary knows, plus the marker digest; absent marker = the default, unchanged
                stored_scope=TEST_SLICE_SCOPE if slice_ is not None else gk_input_vector.STORED_SCOPE,
                # SR-W3-SHAPE 3: a deferred in-build verify is an input of the build (§N.8); absent flag = no component
                in_build_verify=_verify_component(_defer_in_build_verify(ctx, slice_)),
                test_slice=_slice_component(slice_) if slice_ is not None else None,
                horizon_basis=_horizon_basis(ctx, slice_))
            # every component that can be derived without the builder's code is derived a SECOND way and the two
            # must agree before the identity is bound. Under a test slice the check runs on the SCOPE-NORMALISED
            # copy (Stream A C46 review R1): the stored vector's scope is REFUSED BY NAME only at the verification
            # job (the unsealability proof); the build still proves the ephemeris/registry/implementation.
            gk_input_vector_verifier.verify_inputs(
                ctx.db_conn, _scope_normalised(vector, slice_), ephe_path=ephe_path, modules=gk_input_vector.IMPLEMENTATION_MODULES,
                path_refs=gk_rule_registry.bound_path_refs(),
                jd_range=gk_input_vector.consumed_jd_range(horizon), require_scored_classes=True, require_scored_until=True)
            jd = horizon[0].timestamp() / 86400.0 + _JD_UNIX_EPOCH
            _lon, retflag = calc_sidereal_lon("Sun", jd, ephe_path)
            if not (retflag & 2):
                raise RuntimeError(f"manifest: Swiss backend probe retflag {retflag} (F-14)")
            mid = gk_ledger.publish_candidate(
                ctx.db_conn, chart_id, GENERATION, kala_cid, vector,
                {"backend": "swieph", "probe_retflag": int(retflag)},
                f"[{horizon[0].isoformat()},{horizon[1].isoformat()})",
                writer_asset_id=ASSET_ID)
            slice_note = (f"; TEST SLICE {slice_.run} (marker {slice_.digest[:12]}…): "
                          "stored_scope='test_slice' — unsealable by construction, the verifier "
                          "refuses the scope by name; the in-build derivation check ran on the "
                          "scope-normalised copy" if slice_ is not None else "")
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                notes=f"candidate manifest {mid[:8]}… (input vector {gk_input_vector.VECTOR_SCHEMA}: "
                                      f"registry digest {vector['registry']['digest'][:12]}…, "
                                      f"{len(vector['ephemeris']['files'])} ephemeris files, node "
                                      f"series, both orb policies, rulings, implementation){slice_note}")

        if step.key == SNAPSHOT_SUBSTEP:
            context = fetch_chart_context(ctx.db_conn, chart_id)
            require_complete(context)
            sky_cid = SkyEventStore(ctx.db_conn).register_convention()
            rows, contract = load_pinned_vimshottari(ctx.db_conn, chart_id)
            lo, hi = horizon
            dasha_ids = [str(r["dasha_row_id"]) for r in rows
                         if int(r["level_n"]) in (1, 2, 3)
                         and r["start_iso"] < hi and r["end_iso"] > lo]
            # J-2a-P1L (B.3): a P1 record's period_running_at is judged from EVERY pinned row of its anchor (lord, level),
            # wherever it lies — a 'false' is a measured negative from rows wholly outside the horizon. Those consulted
            # rows are consumed inputs, so the ledger lists them too (only while P1 minting is open: otherwise nothing
            # consults a row). An anchor with no pinned row at all has nothing to list and stays 'unknown' (N.7.6).
            # (I) INTERPRETATION (merge of main's J-2a-P1L with this PR's G12 copy): this ledger is for a LEGACY snapshot (ids, no copy). A snapshot WITH a
            # copy (1305) stores only the rows OVERLAPPING the horizon — the database refuses a copy row outside it (period_outside_horizon) — and its
            # builder and verifier both read `held` from that copy, so an anchor wholly outside the horizon is the honest 'unknown' there, never a stored 'false'.
            if p1_minting_closed_reason(ctx.db_conn) is None and not inv_store.snapshot_copy_available():
                consulted = _p1_consulted_dasha_keys(
                    {"lagna_deg": context["lagna_deg"], "natal": context["natal"]},
                    slice_.classes if slice_ is not None else SCORED_CLASSES)
                have = set(dasha_ids)
                dasha_ids += [str(r["dasha_row_id"]) for r in rows
                              if int(r["level_n"]) in (1, 2, 3) and str(r["dasha_row_id"]) not in have
                              and any(str(r.get("lord_graha", "")).lower() == lord
                                      and (level is None or int(r["level_n"]) == level)
                                      for lord, level in consulted)]
            # A5.5f (G7): a rebuild REPLACES the whole unsealed CANDIDATE chart x generation output chain, never accretes. THE CONTRACT: a dispatch that finds no
            # ledger rows (every non-century run, and a fresh century build) is a WHOLE-BUILD REPLAY: the orchestrator drives the full plan (asset_runner calls
            # _drive_substeps without completed_keys), so this snapshot substep always runs, always first among the chain-writing substeps, and a failed build
            # restarts from zero on retry. The replace sits at this one per-plan reset point: it runs before every substep that writes chain rows (inventory /
            # coverage / record / window), so a dispatch can never wipe what it wrote itself. SR-RESUME-NOW: a CENTURY run resumes instead, from its own ledger
            # (`ka_gochara_build_ledger`, migration 1410): `plan_substeps` omits the recorded substeps, `manifest` and `snapshot` among them, only after
            # `build_ledger` has proved the program, horizon, manifest and every recorded substep's rows unchanged; so this replace never runs over a partial
            # chain. An invocation that skips the head without a ledger (a CLI, a harness) is not a supported mode: the horizon guard in _verify_live_inputs
            # refuses one that would mix horizons. A sealed generation, and a manifest that is not a candidate, are refused by name before any delete.
            replaced = rstore.delete_generation_chain(chart_id=chart_id, generation=GENERATION)
            # ND-P2 (migration 1308): the near-miss layer is part of the SAME whole-generation replace. It runs after the chain delete, which has
            # already refused a sealed generation and a manifest that is not a candidate, and it runs under a test slice too (a slice stores no
            # near-miss, so a slice that replaces a full candidate must not leave that candidate's near-miss rows behind). Layer absent = nothing to do.
            nm_store = gk_near_miss.NearMissStore(ctx.db_conn)
            nm_replaced = (nm_store.delete_generation(chart_id=chart_id, generation=GENERATION)
                           if nm_store.layer_present() else None)
            inv_store.delete_generation_inventory(chart_id, GENERATION)
            digest = inv_store.insert_snapshot(
                chart_id=chart_id, generation=GENERATION, convention_id=sky_cid,
                consumed_fact_ids=context["source_fact_ids"],
                consumed_dasha_row_ids=dasha_ids)
            if inv_store.snapshot_copy_available():
                gk_verifier.validate_consumed_dasha_population(
                    ctx.db_conn, chart_id=chart_id, generation=GENERATION, against_live=True)
                identity = "SELF-CONTAINED: stored L1 copy independently checked at capture (G12)"
            else:
                identity = "LEGACY: no L1 copy; apply snapshot-copy migration before any seal"
                logger.warning("%s: %s", ASSET_ID, identity)
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=1,
                notes=(f"search-input snapshot {digest[:12]}…: {len(context['source_fact_ids'])} "
                       f"L1 facts, {len(dasha_ids)} daśā rows (build "
                       f"{contract.get('build_id')}); {identity}; no AV declarations (P5 held); chain replaced "
                       f"(windows {replaced['windows']}, records {replaced['records']}, contacts "
                       f"{replaced['contacts']}, coverage {replaced['coverage']})"
                       + (f"; near-miss layer replaced (near-misses {nm_replaced['near_misses']}, searches {nm_replaced['searches']})"
                          if nm_replaced is not None else "")))

        event_class = step.key.split(":", 1)[1]
        if event_class not in SCORED_CLASSES:
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                notes=f"unknown class {event_class!r}")

        if step.key.startswith(INVENTORY_SUBSTEP_PREFIX):
            # G12 (Codex round 1, ruling 3): the ONE capture is the snapshot substep; from here on the build computes from the snapshot's COPY only
            context = fetch_chart_context_from_snapshot(ctx.db_conn, chart_id, GENERATION)
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
        if _defer_in_build_verify(ctx, slice_):
            # SR-W3-SHAPE 3: _verify_live_inputs (run before this phase) has already proved the manifest records the deferral
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                notes=f"verify {event_class}: {VERIFY_DEFERRED_STATUS} — in-build self-check deferred by "
                                      f"{DEFER_VERIFY_KEY} (bound in the manifest vector as in_build_verify); nothing derived, "
                                      "nothing persisted; the separate verification job re-derives the inventory, ledger and "
                                      "contact-geometry digests and persists the 1206 and 1240 rows; the candidate gate stays "
                                      "CLOSED until it has run")
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
                selected_versions=stored_sel or None,
                excluded_agents=_slice_excluded_agents(slice_))
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
        # aspect-to-span contacts are certified like every other contact by `certify_contact_geometry` below — the
        # DERIVED-tolerance, union-of-contacts contract (R10-6); the fixed-tolerance sampling precheck that used to run
        # here (3 s / 6 h) contradicted it and is removed.
        horizon = _effective_horizon(ctx, slice_)
        ephe_path = _ephe_path(ctx)

        def position_at(body: str, t: datetime) -> float:
            jd = t.timestamp() / 86400.0 + _JD_UNIX_EPOCH
            lon, retflag = calc_sidereal_lon(body.title(), jd, ephe_path)
            if not (retflag & 2):
                raise RuntimeError(f"position probe {body} @ {t.isoformat()}: retflag {retflag} "
                                   "lacks the Swiss bit (F-14)")
            return lon

        position_at.cache_key = ("swiss", ephe_path)
        # R9-3: the COMPLETE contact geometry of every concrete transit obligation, reconstructed from the ephemeris
        # and compared with the ledger both ways (interior exits/re-entries, bridged and omitted contacts all fail);
        # incomplete evidence raises GeometryUnavailable — no complete-search claim without it
        # NEAR-MISSES (ND-P2-20261005 rules 1-2). An in-band interval with no exact crossing (this builder mints a point contact only around an exact
        # root) is a NEAR-MISS: a separate kind with its own storage, never a contact. Three cases, decided from what the run and the schema ARE:
        #   * a VALIDATED test slice (GRAZE-INTERIM, unchanged): reported in the notes, not raised, NOT stored — a slice is unsealable, torn down by a
        #     tool that knows a closed table list, and must not depend on a migration of the second window;
        #   * a full build WITH the near-miss storage (migration 1308): the builder stored its own near-misses at the record substeps; the certifier
        #     classifies independently, from the ephemeris alone, and the two sets must agree object for object or the build refuses BY NAME;
        #   * a full build WITHOUT the storage: no sink, exactly as before ND-P2 — the first near-miss is refused (there is nowhere to keep it).
        # Every other certification failure raises in all three.
        nm_store = gk_near_miss.NearMissStore(ctx.db_conn)
        nm_layer = slice_ is None and nm_store.layer_present()
        graze_sink: list | None = [] if (slice_ is not None or nm_layer) else None
        # MEASURING_BUILD_CONTRACT MB-2: under a slice every reconstructed stretch is ALSO handed to the structured STRETCH_SINK/1 (one log line per record and one
        # summary line per class, emitted even when the certification then raises: the finally). POLICY: the MEASURING build (all_classes_full) exists to COUNT
        # defects in one run, so there near-misses, unresolved stretches and omissions are sunk with their reason and the class CONTINUES (steward ruling 4(f) /
        # OS-6; the acceptance then fails by name on omissions); every other shape, and any non-slice build, keeps the old behaviour.
        stretch_sink: list | None = [] if slice_ is not None else None
        policy = (gk_contact_certify.POLICY_SINK_ALL if slice_ is not None and slice_.run == "all_classes_full" else gk_contact_certify.POLICY_RAISE)
        sink_summary = None
        try:
            geometry = gk_contact_certify.certify_contact_geometry(
                ctx.db_conn, chart_id=chart_id, generation=GENERATION, event_class=event_class, position_at=position_at,
                graze_sink=graze_sink, stretch_sink=stretch_sink, sink_policy=policy)
        finally:
            if stretch_sink is not None:
                sink_summary = _emit_stretch_sink(event_class, horizon, stretch_sink, position_at, ephe_path)
        graze_note = ""
        if nm_layer:
            keys = self._near_miss_obligation_keys(ctx, chart_id, event_class)
            stored_nm = nm_store.stored_for_keys(chart_id=chart_id, generation=GENERATION, keys=keys)
            nm_problems = gk_near_miss.reconcile_with_certifier(
                reported=graze_sink, stored=stored_nm, searched=nm_store.searched_keys(chart_id=chart_id, generation=GENERATION),
                obligations=keys, horizon=horizon)
            if nm_problems:
                raise RuntimeError(f"near-miss certification failed {event_class}: " + "; ".join(nm_problems))
            graze_note = (f"; NEAR-MISSES: {len(graze_sink)} certified and stored for this class's {len(keys)} point obligation(s), each its own "
                          f"standalone UNSCORED interval (standing {gk_near_miss.STANDING}, {gk_near_miss.SCORE_REASON}); none is a contact, a "
                          "record or a window member")
        elif graze_sink:
            graze_note = (f"; GRAZES REPORTED, NOT RAISED (validated test slice; {len(graze_sink)}): " + " | ".join(
                f"{g['body']} {g['relation']} {g['target']} level {g['level_deg']} in band {g['interval'][0]} to {g['interval'][1]}, closest "
                f"{g['closest_approach_deg']} deg at {g['closest_approach_at']}, peak activity {g['peak_activity']}"
                + (f", whole stretch clipped by the horizon at its {' and '.join(g['clipped_by_horizon'])} (horizon part {g['horizon_interval'][0]} to {g['horizon_interval'][1]})"
                   if g.get("clipped_by_horizon") else "") for g in graze_sink))
            logger.warning("%s: %s %s", ASSET_ID, event_class, graze_note.strip("; "))
        # R9-6.1: the builder NEVER persists a verification row (it holds no privilege to, and the database cannot tell a
        # builder-written "independent" verification from a real one). Everything above is the builder's in-build
        # SELF-CHECK, reported; persistence of the 1206 inventory row and every 1240 window row belongs to the separate
        # verification job (`pipeline/orchestrator/verification_job.py`, run by the verifier principal after the build).
        # R8-4: the candidate gate's window half — every included P1–P4 grain of this class must carry a
        # VERIFIED, current, input-bound verification result. The build refuses a class that cannot pass it
        # rather than leave a candidate no sealer could accept (UNVERIFIED_DYNAMIC / missing both fail).
        sink_note = ("" if sink_summary is None else
                     f"; {gk_stretch_sink.SCHEMA}: {sink_summary['stretches']} stretches, {sink_summary['records']} records, "
                     f"certifier_omissions_present={sum(n for k, n in sink_summary['counts_by_kind_reason'].items() if k.startswith('omission/'))}, "
                     f"digest {sink_summary['record_ids_digest'][:12]}")
        gate_note = ("; verification NOT persisted by the builder — verification_pending_verifier_principal: the separate "
                     "verification job persists the 1206 and 1240 rows; the candidate gate stays CLOSED until it has run")
        return WriterResult(asset_id=self.asset_id, rows_inserted=1,
                            notes=f"verify {event_class}: inventory + ledger digests "
                                  "independently reproduced (report only); "
                                  f"contact geometry (aspect-to-span included) certified complete for "
                                  f"{geometry['obligations_certified']} concrete obligation(s) "
                                  f"({geometry['contacts_expected']} contacts; {geometry['named_limit']}){graze_note}{sink_note}{gate_note}")

    def _run_record_phase(self, ctx: ContextSpec, step: SubStep,
                          chart_id: str, slice_: TestSlice | None = None) -> WriterResult:
        """interval_sweep substeps (the chart lock is already taken by the
        caller — substrate order, N13): `coverage:<class>` writes the class
        partition (pin 7), `record:<class>:<path>` materialises the grain.
        The chart context comes from L1 chart_facts — conflicts/missing are
        NAMED by require_complete, never defaulted."""
        context = fetch_chart_context_from_snapshot(ctx.db_conn, chart_id, GENERATION)     # the snapshot's COPY, never live L1 (G12)
        require_complete(context)
        horizon = _effective_horizon(ctx, slice_)
        ephe_path = _ephe_path(ctx)
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
                arc_cache[body] = production_arc_index(body, ephe_path)       # the ONE production wiring (shared with the substrate)
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
        # P1's period_running_at reads the snapshot's COPY of the §4.0-pinned daśā rows; the
        # read is lazy (only P1 grains with a period_running_at prerequisite
        # ever trigger it) and its build is recorded in the notes below.
        dasha_rows_for, dasha_contract = make_period_rows_for_snapshot(
            ctx.db_conn, chart_id, GENERATION)                                        # the snapshot's COPY, never live L1 (G12)
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
        nm_note, nm_rows = self._store_near_misses(
            ctx, chart_id=chart_id, edges=edges, arc_index_for=arc_index_for, horizon=horizon, position_at=position_at, slice_=slice_)
        inserted += nm_rows
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
                                  position_at=position_at, excluded_agents=_slice_excluded_agents(slice_),
                                  rule_version=gk_rule_registry.selected_path_version(event_class, "P1"))
            # AM-20 (revised): the stored house descriptor is the count from the lagna
            verify_p1_house_descriptor(ctx.db_conn, chart_id=chart_id, generation=GENERATION,
                                       event_class=event_class)
        blanked = counts.get(PERIOD_TABLE_ENDS_REASON, 0)
        table_end_note = (f"; {blanked} P1 supports reach past the end of the stored daśā table: unknown, "
                          f"reason {PERIOD_TABLE_ENDS_REASON}" if blanked else "")
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
                   f"{table_end_note}{gate_note}{nm_note}"))

    @staticmethod
    def _store_near_misses(ctx: ContextSpec, *, chart_id: str, edges, arc_index_for, horizon, position_at,
                           slice_: "TestSlice | None") -> tuple[str, int]:
        """ND-P2-20261005 rules 1-2 (migration 1308): for every transit POINT edge of the grain (the same edges `solve_point_edges` solves),
        find the object's near-misses on the body's full-domain arc index, and store each with the standalone UNSCORED interval it opens, plus
        one search row per object (an object with none is a verified-empty result). Returns (note, rows inserted).

        Nothing here reads or writes a contact, a record, a window or a coverage partition, and nothing on the scored path reads what is
        written. Not run under a test slice (the slice interim reports, see `verify:<class>`), and not when the storage is absent (the layer
        is OFF and a near-miss is refused at verify as before). An object several classes share is stored once; a later grain must derive
        the same rows. Unresolved geometry raises `NearMissUnresolved` — it is never stored as a near-miss."""
        store = gk_near_miss.NearMissStore(ctx.db_conn)
        if slice_ is not None or not store.layer_present():
            return "", 0
        dasha_rows = InventoryStore(ctx.db_conn).consumed_dasha_rows(chart_id, GENERATION)
        seen: set = set()
        objects = stored = reused = rows = 0
        for edge in edges:
            if (not edge.transit or edge.relation not in gk_record_store.POINT_KERNEL_RELATION
                    or not edge.obj.canonical_target.startswith("point:")):
                continue                                   # an aspect to a SPAN is a residence-like contact: no ray level, no near-miss
            source = gk_record_store.POINT_ORB_SOURCE[edge.relation]
            orb = float(gk_record_store.ORB_TABLE[source]["orb_max_deg"])
            obj = gk_near_miss.NearMissObject(
                body=edge.obj.body, relation_kind=edge.obj.relation_kind, canonical_target=edge.obj.canonical_target,
                orb_policy_id=gk_near_miss.orb_policy_id(source, orb), convention_id=edge.obj.convention_id)
            if obj.uuid in seen:
                continue
            seen.add(obj.uuid)
            found = gk_near_miss.solve_object_near_misses(
                obj=obj, index=arc_index_for(edge.agent.title()), orb_deg=orb, horizon=horizon, position_at=position_at)
            out = store.write_object(chart_id=chart_id, generation=GENERATION, obj=obj, horizon=horizon, near_misses=found,
                                     dasha_rows=dasha_rows)
            objects += 1
            stored += out["near_misses"]
            reused += out["reused"]
            rows += out["near_misses"] + out["searches"]
        if not objects:
            return "", 0
        return (f"; near-miss layer: {objects} point object(s) searched ({reused} already stored by another grain), {stored} near-miss(es) "
                f"stored as standalone unscored intervals"), rows

    @staticmethod
    def _near_miss_obligation_keys(ctx: ContextSpec, chart_id: str, event_class: str) -> list[tuple]:
        """The class's concrete POINT obligations (body, relation, target) under its included path pins — the objects a near-miss can exist
        for. The same obligation set the contact-geometry certification walks (period-lord role tokens and the Moon are not concrete transit
        agents here), read from the stored inventory."""
        rows = ctx.db_conn.execute(
            "SELECT DISTINCT o.agent, o.relation, o.target FROM public.ka_gochara_search_obligation o"
            " JOIN public.ka_gochara_search_path_pin p ON (p.chart_id, p.generation, p.event_class, p.path_id, p.rule_version)"
            "   = (o.chart_id, o.generation, o.event_class, o.path_id, o.rule_version) AND p.disposition = 'included'"
            " WHERE o.chart_id = %s AND o.generation = %s AND o.event_class = %s AND o.relation IN ('conjunction', 'aspect')"
            "   AND o.target LIKE 'point:%%' AND o.agent <> 'moon' AND o.agent NOT LIKE 'period_lord:%%'"
            " ORDER BY 1, 2, 3", (chart_id, GENERATION, event_class)).fetchall()
        return [tuple(r.values()) if isinstance(r, dict) else tuple(r) for r in rows]

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
        ephe_path = _ephe_path(ctx)

        def position_at(body: str, t: datetime) -> float:
            jd = t.timestamp() / 86400.0 + _JD_UNIX_EPOCH
            lon, retflag = calc_sidereal_lon(body.title(), jd, ephe_path)
            if not (retflag & 2):
                raise RuntimeError(
                    f"position probe {body} @ {t.isoformat()}: retflag {retflag} lacks the "
                    "Swiss bit (F-14 — a Moshier fallback is a named failure, never a silent probe)")
            return lon

        def speed_at(body: str, t: datetime) -> tuple:
            """The solver's seam (S3): (sidereal longitude, Swiss longitudinal speed in degrees per DAY) from ONE ephemeris call; the same Swiss-bit
            discipline as `position_at`."""
            jd = t.timestamp() / 86400.0 + _JD_UNIX_EPOCH
            lon, speed, retflag = calc_sidereal_lon_speed(body.title(), jd, ephe_path)
            if not (retflag & 2):
                raise RuntimeError(
                    f"speed probe {body} @ {t.isoformat()}: retflag {retflag} lacks the Swiss bit (F-14 — a Moshier fallback is a named failure)")
            return lon, speed

        store = WindowStore(ctx.db_conn)
        # SR-OD1 P1a / D2: the P1 operand sources, only when bound — per-factor `P1_VALUE_RULES`, or the Form B table the grain's version
        # declares (read from the persisted rows the sweep itself evaluates); the L0 tables are read through the validated loaders,
        # never a fallback
        p1_l0 = []

        def p1_operands_for(version: str):
            if path_id != "P1":
                return None
            form_b = gk_p1_operands.form_b_mapping(bound_rows(path_id, version))
            if form_b is None and P1_VALUE_RULES is None:
                return None
            if not p1_l0:
                p1_l0.append(gk_p1_operands.load_p1_l0(ctx.db_conn.cursor()))
            return gk_p1_operands.P1Operands(p1_l0[0], position_at, rules=None if form_b is not None else P1_VALUE_RULES, form_b=form_b)
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
        # R9-6.1: the builder holds NO privilege on the verification tables and never persists a result; the window phase's
        # independent checks below are the in-build SELF-CHECK (reported). The 1240 rows are written by the separate
        # verification job under the verifier principal.
        windows = memberships = 0
        excluded: dict = {}
        reasons: dict = {}
        unqualified = unverified = reproduced = solver_deferred = 0
        for version in versions:        # the path→version map comes from the records, not a constant
            p1_ops = p1_operands_for(version)
            records = store.read_grain(
                chart_id=chart_id, generation=GENERATION, event_class=event_class,
                path_id=path_id, rule_version=version, position_at=position_at, p1=p1_ops, speed_at=speed_at)
            # R4 (SR-Q6-L1-AMEND): a Form B grain records the combustion authority its states were derived from (orb row ids + digest, the
            # L1 module's digest) in every window's qualification provenance; the verifier re-derives the same record from its own reads
            inherited = gk_p1_operands.grain_inheritance(p1_ops)
            vedha = vedha_source()
            if hasattr(vedha, "for_grain"):    # C1: a source bound to this grain (its reads are lazy: only a vedha-bearing record triggers them)
                # SR-VEDHA-RESIDENCE-SOURCE: the obstructors' residence is derived from THIS substep's ephemeris probe, not read from stored contacts
                vedha = vedha.for_grain(ctx.db_conn, chart_id=chart_id, generation=GENERATION, event_class=event_class,
                                        records=records, position_at=position_at)
            # S3: a window with a qualified function-valued member is SOLVED (certified maximum + earliest tie instant) or blank under a named solver reason —
            # never the retired dynamic switch. The budget is per window; the independent solver check runs once, in the verification job (N-6, below).
            drafts, ex = gk_window_sweep.draft_windows(
                event_class, records, bound_rows, drishti=DRISHTI_SOURCE, vedha=vedha,
                solver=gk_window_sweep.PRODUCTION_SOLVER, policy=policy, combustion_inheritance=inherited)
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
            rows = bound_rows(path_id, version)
            # D2: a P1 version that declares the Form B table is re-derived by the verifier's OWN sky + L0 reads (P1c), never from the
            # builder's operands; absent that table the self-check is exactly what it was
            p1_check = (gk_p1_operands_check.P1Check.from_conn(ctx.db_conn, position_at)
                        if path_id == "P1" and gk_p1_operands_check.needs_p1_check(rows) else None)
            report = verify_window_semantics(
                ctx.db_conn, chart_id=chart_id, generation=GENERATION, event_class=event_class,
                path_id=path_id, rule_version=version,
                factor_rows=rows,
                drishti_bound=DRISHTI_SOURCE is not None, vedha_bound=vedha_source() is not None,
                solver_check=False, p1_check=p1_check, ephe_path=ephe_path)             # N-6: the independent prover runs once, in the verification job
            unverified += report["unverified_dynamic"]
            solver_deferred += report["solver_check_deferred_windows"]
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
        pending = unverified - solver_deferred          # numbered by the solver, its independent check left to the verification job (N-6)
        tail = (f"{reproduced} window(s) reproduced exactly"
                + (f", {pending} UNVERIFIED (function-valued members — checked against universal bounds only; this result does NOT satisfy a "
                   "verification gate)" if pending else "")
                + (f", {solver_deferred} numbered by the solver with its independent check DEFERRED to the verification job (not a pass)"
                   if solver_deferred else "") if unverified
                else f"reproduced all {reproduced} window(s) exactly")
        stored_note = ("; verification result NOT persisted by the builder — verification_pending_verifier_principal "
                       "(the separate verification job writes it; the candidate gate stays closed until it has run)")
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
