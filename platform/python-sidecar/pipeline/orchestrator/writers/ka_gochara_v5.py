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
from datetime import datetime, timedelta, timezone
from pathlib import Path

from pipeline.orchestrator.writers import (
    ContextSpec,
    SubStep,
    WriterBase,
    WriterResult,
    register,
)
from services.gochara_kernel import evaluator as gk_evaluator
from services.gochara_kernel import ephemeris_pins as gk_ephemeris_pins
from services.gochara_kernel.native_conn import native_connection
from services.gochara_kernel import arcs as gk_arcs
from services.gochara_kernel.dasha_read import make_period_rows_for
from services.gochara_kernel.chart_context import (fetch_chart_context,
                                                   require_complete)
from services.gochara_kernel.knots import calc_sidereal_lon, sample_knots, station_refiner
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
TEST_SLICE_KEY = "gochara_v5_test_slice"
TEST_SLICE_SCHEMA = "gochara_v5_test_slice/1"
TEST_SLICE_RUNS = ("all_classes_1y", "one_class_full")
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


def _parse_slice_horizon(raw) -> tuple:
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
    if start < DEFAULT_HORIZON[0] or end > DEFAULT_HORIZON[1]:
        refuse(f"horizon [{start.isoformat()}, {end.isoformat()}) reaches outside DEFAULT_HORIZON "
               f"[{DEFAULT_HORIZON[0].isoformat()}, {DEFAULT_HORIZON[1].isoformat()}) — refused, never clipped")
    return (start, end)


def _validate_test_slice(marker) -> TestSlice:
    """The marker, strictly. Every deviation is a named TestSliceRefusal — the writer never
    guesses a scope it was not explicitly given."""
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
    horizon = _parse_slice_horizon(marker["horizon"])
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


def _test_slice(ctx: ContextSpec) -> TestSlice | None:
    """The run's validated test-slice marker, or None — the ABSENT key is today's behaviour,
    byte-identical."""
    manifest = _plan_manifest(ctx)
    if manifest is None or TEST_SLICE_KEY not in manifest:
        return None
    return _validate_test_slice(manifest[TEST_SLICE_KEY])


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


def _effective_horizon(ctx: ContextSpec, slice_: TestSlice | None):
    """The marker's horizon under a slice; else EXACTLY what main used: `ctx.config.get("horizon", DEFAULT_HORIZON)` —
    an absent key is DEFAULT_HORIZON, an explicit null stays None (and fails downstream as it always did; Codex P2-4: it
    must not be quietly turned into the default). Under a marker a config horizon that is present and null, or that
    CONTRADICTS the marker, is ambiguous — refused, never guessed."""
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
        test_slice=_slice_component(slice_) if slice_ is not None else None)
    # ... and every component that can be derived WITHOUT the builder's code is (registry + L0 + sky in
    # Postgres, ephemeris files + runtime library + implementation by direct hashing). Under a slice the
    # check runs on the SCOPE-NORMALISED copy: the stored vector's unknown scope is the unsealability
    # proof and belongs to the verification job — the build still proves the real image (R1).
    gk_input_vector_verifier.verify_inputs(
        ctx.db_conn, _scope_normalised(stored, slice_), ephe_path=_ephe_path(ctx),
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


def _class_of_grain(key: str) -> str | None:
    """The event class a per-class substep key names, or None for a class-less substep."""
    if key.startswith((INVENTORY_SUBSTEP_PREFIX, COVERAGE_SUBSTEP_PREFIX, VERIFY_SUBSTEP_PREFIX)):
        return key.split(":", 1)[1]
    if key.startswith((RECORD_SUBSTEP_PREFIX, WINDOW_SUBSTEP_PREFIX)):
        return key.split(":", 2)[1]
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
        is refused at PLAN time, not first at execution time.

        C46 test slice: a gochara_v5_test_slice marker in the run's
        plan_manifest narrows the class loop to the marker's classes; no
        marker = the full SCORED_CLASSES plan, byte-identical to today."""
        ctx = _native_ctx(ctx)
        _require_pinned_chart(ctx.config["chart_id"])
        slice_ = _test_slice(ctx)
        classes = slice_.classes if slice_ is not None else SCORED_CLASSES
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
        _ephe_path(ctx)         # every substep resolves it, so the FIRST ('rules') refuses a mis-provisioned job in seconds
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
            return self._run_inventory_phase(ctx, step, chart_id, slice_)
        if step.key.startswith((COVERAGE_SUBSTEP_PREFIX, RECORD_SUBSTEP_PREFIX)):
            _verify_live_inputs(ctx, chart_id)
            return self._run_record_phase(ctx, step, chart_id, slice_)
        if step.key.startswith(WINDOW_SUBSTEP_PREFIX):
            _verify_live_inputs(ctx, chart_id)
            return self._run_window_phase(ctx, step, chart_id)
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
                # C46: a sliced build is unsealable by construction — stored_scope no verifier
                # vocabulary knows, plus the marker digest; absent marker = the default, unchanged
                stored_scope=TEST_SLICE_SCOPE if slice_ is not None else gk_input_vector.STORED_SCOPE,
                test_slice=_slice_component(slice_) if slice_ is not None else None)
            # every component that can be derived without the builder's code is derived a SECOND way and the two
            # must agree before the identity is bound. Under a test slice the check runs on the SCOPE-NORMALISED
            # copy (Stream A C46 review R1): the stored vector's scope is REFUSED BY NAME only at the verification
            # job (the unsealability proof); the build still proves the ephemeris/registry/implementation.
            gk_input_vector_verifier.verify_inputs(
                ctx.db_conn, _scope_normalised(vector, slice_), ephe_path=ephe_path, modules=gk_input_vector.IMPLEMENTATION_MODULES,
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
            # A5.5f (G7): a rebuild REPLACES the whole unsealed CANDIDATE chart x generation output chain, never
            # accretes. THE CONTRACT: every dispatch of this asset is a WHOLE-BUILD REPLAY. The orchestrator drives the
            # full plan on every dispatch (asset_runner calls _drive_substeps without completed_keys), so this
            # snapshot substep always runs, always first among the chain-writing substeps, and a failed build restarts
            # from zero on retry. There is NO resume and none is built here (the orchestrator is frozen). That is why
            # the replace can sit at this one per-plan reset point: it runs before every substep that writes chain rows
            # (inventory / coverage / record / window), so a dispatch can never wipe what it wrote itself. An
            # invocation that SKIPS the head (a CLI, a harness, a future resume) is not a supported mode: the horizon
            # guard in _verify_live_inputs refuses one that would mix horizons. A sealed generation, and a manifest
            # that is not a candidate, are refused by name before any delete.
            replaced = rstore.delete_generation_chain(chart_id=chart_id, generation=GENERATION)
            inv_store.delete_generation_inventory(chart_id, GENERATION)
            digest = inv_store.insert_snapshot(
                chart_id=chart_id, generation=GENERATION, convention_id=sky_cid,
                consumed_fact_ids=context["source_fact_ids"],
                consumed_dasha_row_ids=dasha_ids)
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=1,
                notes=(f"search-input snapshot {digest[:12]}…: {len(context['source_fact_ids'])} "
                       f"L1 facts, {len(dasha_ids)} daśā rows (build "
                       f"{contract.get('build_id')}); no AV declarations (P5 held); chain replaced "
                       f"(windows {replaced['windows']}, records {replaced['records']}, contacts "
                       f"{replaced['contacts']}, coverage {replaced['coverage']})"))

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
        geometry = gk_contact_certify.certify_contact_geometry(
            ctx.db_conn, chart_id=chart_id, generation=GENERATION, event_class=event_class, position_at=position_at)
        # R9-6.1: the builder NEVER persists a verification row (it holds no privilege to, and the database cannot tell a
        # builder-written "independent" verification from a real one). Everything above is the builder's in-build
        # SELF-CHECK, reported; persistence of the 1206 inventory row and every 1240 window row belongs to the separate
        # verification job (`pipeline/orchestrator/verification_job.py`, run by the verifier principal after the build).
        # R8-4: the candidate gate's window half — every included P1–P4 grain of this class must carry a
        # VERIFIED, current, input-bound verification result. The build refuses a class that cannot pass it
        # rather than leave a candidate no sealer could accept (UNVERIFIED_DYNAMIC / missing both fail).
        gate_note = ("; verification NOT persisted by the builder — verification_pending_verifier_principal: the separate "
                     "verification job persists the 1206 and 1240 rows; the candidate gate stays CLOSED until it has run")
        return WriterResult(asset_id=self.asset_id, rows_inserted=1,
                            notes=f"verify {event_class}: inventory + ledger digests "
                                  "independently reproduced (report only); "
                                  f"contact geometry (aspect-to-span included) certified complete for "
                                  f"{geometry['obligations_certified']} concrete obligation(s) "
                                  f"({geometry['contacts_expected']} contacts; {geometry['named_limit']}){gate_note}")

    def _run_record_phase(self, ctx: ContextSpec, step: SubStep,
                          chart_id: str, slice_: TestSlice | None = None) -> WriterResult:
        """interval_sweep substeps (the chart lock is already taken by the
        caller — substrate order, N13): `coverage:<class>` writes the class
        partition (pin 7), `record:<class>:<path>` materialises the grain.
        The chart context comes from L1 chart_facts — conflicts/missing are
        NAMED by require_complete, never defaulted."""
        context = fetch_chart_context(ctx.db_conn, chart_id)
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
                ks = sample_knots(body, SUBSTRATE_DOMAIN_START.date(),
                                  SUBSTRATE_DOMAIN_END.date(), ephe_path)
                arc_cache[body] = gk_arcs.build_arc_index(
                    body, ks.knot_jds, ks.longitudes_deg,
                    station_refiner=station_refiner(body, ephe_path))      # ONE station instant: the ephemeris one, as the substrate stores it
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
                                  position_at=position_at, excluded_agents=_slice_excluded_agents(slice_))
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
        ephe_path = _ephe_path(ctx)

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
        # R9-6.1: the builder holds NO privilege on the verification tables and never persists a result; the window phase's
        # independent checks below are the in-build SELF-CHECK (reported). The 1240 rows are written by the separate
        # verification job under the verifier principal.
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
