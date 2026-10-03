"""ka_gochara_v4_41_candidate — Pravāha A2.5: the '4.1' gochara CANDIDATE
chain, run inside the governed build pipeline (brahma-build-pipeline-job).

Replaces the deleted bespoke Cloud Run job that used to drive
scripts/kala_gochara_cutover/step06* out-of-band. Same chain, same pins,
now orchestrator-driven on ctx.db_conn with per-substep savepoints.

ASSET IDENTITY (parameters live HERE, never in ctx.config — that surface is
FROZEN-adjacent and untouched):
  * chart       — ctx.config["chart_id"] (per_chart writer)
  * generation  — fixed '4.1' (CANDIDATE ONLY — never serving, never published,
                  never flipped; see "CANDIDATE-ONLY GUARANTEE" below)
  * horizon     — fixed [1998-01-01T00:00:00+00:00, 2026-04-18T00:00:00+00:00)
                  (the native's narrowed scored horizon; the start is
                  inclusive, the end exclusive)

THE CHAIN WRAPPED (scripts/kala_gochara_cutover/, each refactored to a
conn-injected core whose CLI behaviour is byte-identical to before):
  1. step06_enumerate_episodes.enumerate_core — kernel episode enumeration
     over the horizon (Swiss ephemeris). DB READS ONLY (§12.9 freshness gate,
     gochara_resonance_map, resolution facts); returns (episodes, coverage,
     report) in memory — the writer never touches the CLI's JSON files.
  2. step06_candidate_build's ledger lifecycle — register_convention →
     publish_candidate → write_contacts → write_coverage (ledger.py; does NOT
     commit — the caller owns the transaction).
  3. step06a_class_context.build_all_class_contexts — the per-class
     permission context, derived in-process on the same conn.
  4. step06b_windows_projection.project_windows_core — reads contacts from
     the DB, projects windows, writes kala_gochara_windows rows at generation
     '4.1' (delete-then-insert scoped chart × '4.1'), updates the candidate
     manifest's windows count.

SUBSTEP DECOMPOSITION (honest, idempotent per sub-span):
  * 'manifest'       — once-per-chart ledger bootstrap: §12.9 gate +
                       register_convention (ON CONFLICT DO NOTHING) +
                       publish_candidate (replaces the candidate manifest IN
                       PLACE while status='candidate' — ledger.publish_candidate
                       is re-entry tolerant; refuses a published/superseded/
                       rolled_back manifest). writer_asset_id is recorded as
                       THIS asset, honest provenance.
  * 'body:<Body>' ×8 — one per non-Moon graha (M-3/R7): enumerate_core for
                       that body, then write_contacts/write_coverage with
                       bodies=[body] — the ledger's body-scoped
                       delete-then-insert (chart × '4.1' × body). Per-body
                       enumeration payloads concatenate exactly (the ADK-0020
                       dedupe keys on the pinned §3.2 contact_id, which
                       includes body). Re-running one body's substep replaces
                       exactly that body's rows.
  * 'windows'        — step06a class context (in-process) + step06b core,
                       whose write_windows is already delete-then-insert
                       scoped (chart × '4.1') — the whole windows projection
                       is this substep's sub-span. Re-running replaces the
                       '4.1' window set wholesale and re-stamps the manifest
                       count. A horizon validator runs BEFORE any DML: the
                       horizon is HALF-OPEN [1998-01-01, 2026-04-18) — a row
                       starting on the excluded end date, ending past it, or
                       carrying an out-of-domain peak_date refuses the
                       substep (fail-closed backstop, never a clamp). The
                       enumerator is half-open and exact at the boundary
                       (episodes.py), the projection never samples the
                       excluded end instant (step06b), and the body substep
                       re-validates every enumerated contact's instants
                       BEFORE contact DML (_validate_episodes_within_horizon).

CANDIDATE-ONLY GUARANTEE (steward condition 4) — three independent layers,
none weakened by this writer:
  * Ledger guards (services/gochara_kernel/ledger.py): every mutating call
    this writer makes passes through _require_not_published /
    _candidate_manifest_id — if '4.1' were EVER published, every subsequent
    write refuses with PublishedGenerationRefusal. publish_candidate itself
    refuses any non-candidate manifest. This writer NEVER calls
    ledger.publish() (the flip machinery) — source-guarded in the test
    suite.
  * Serving-side generation authority (platform-mcp
    register_gochara_windows.ts AUTHORITATIVE_GENERATION_FILTER): rows are
    served ONLY where generation = kala_gochara_authority.authoritative_
    generation for the chart. This writer never touches
    kala_gochara_authority — only the release-authority flip (step08) writes
    it — so '4.1' rows are unreachable by every serving read until a steward
    flip that this asset cannot perform.
  * DB trigger (step03_guard_n6a.sql's kala_gochara_generation_guard /
    migration 1071's kala_gochara_windows_generation_guard_row): DELETE/
    UPDATE of 'v1' (and, in production, '3.0') rows raises; '4.1' candidate
    writes pass. This writer's DML is pinned to generation='4.1' — it
    structurally cannot target 'v1'/'3.0' rows (source-guarded).

FROZEN ORCHESTRATOR CONTRACT (§N.2)
------------------------------------
  * @register('ka_gochara_v4_41_candidate') on a WriterBase subclass
  * HEAVY: plan_substeps(ctx) + run_substep(ctx, step)
  * ctx.db_conn — read/written, NEVER committed, rolled back or closed;
    no own connection is ever opened (the whole step06 chain runs on it)
  * never writes asset_throughput

IDEMPOTENCY (§N.3)
------------------
Delete-then-INSERT on ctx.db_conn scoped to the substep key BEFORE INSERT:
  kala_gochara_contacts: (chart × '4.1' × body)        per 'body:<Body>' substep
  kala_gochara_coverage:  (chart × '4.1' × body-partition) per 'body:<Body>' substep
  kala_gochara_windows:   (chart × '4.1')              the 'windows' substep
  kala_gochara_publication: candidate manifest replaced in place (ledger)
"""
from __future__ import annotations

import importlib.util
import logging
import sys
from datetime import date, datetime, timezone
from pathlib import Path

from pipeline.orchestrator.writers import (
    ContextSpec,
    SubStep,
    WriterBase,
    WriterResult,
    register,
)
from panchang_engine import swiss_backend as _swiss_backend

logger = logging.getLogger(__name__)

ASSET_ID = "ka_gochara_v4_41_candidate"

# ASSET IDENTITY — the three pinned parameters of this writer.
GENERATION = "4.1"
HORIZON_START = "1998-01-01T00:00:00+00:00"
HORIZON_END = "2026-04-18T00:00:00+00:00"
HORIZON_TEXT = f"[{HORIZON_START},{HORIZON_END})"
HORIZON_MIN_DATE = date(1998, 1, 1)
HORIZON_MAX_DATE = date(2026, 4, 18)  # exclusive bound's date; rows may not exceed it

# M-3/R7: the eight non-Moon grahas enumerated for persistence (Moon is served
# on demand — never persisted by this chain).
PERSISTED_BODIES: tuple[str, ...] = (
    "Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Rahu", "Ketu",
)

# M-1 ratified candidate-1 enumeration orb (linear_no_box × 5.0°, brief §12.2).
ORB_DEG = 5.0

SIDECAR = Path(__file__).resolve().parents[3]
_CUTOVER = SIDECAR / "scripts" / "kala_gochara_cutover"


def _load_module(path: Path, name: str):
    """Import-by-path (the step06b/ledger precedent: scripts/ is not a package
    and the kernel package __init__ is a sibling workstream's surface)."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


step06_enumerate = _load_module(
    _CUTOVER / "step06_enumerate_episodes.py", "a25_step06_enumerate_episodes")
step06_build = _load_module(
    _CUTOVER / "step06_candidate_build.py", "a25_step06_candidate_build")
step06a_context = _load_module(
    _CUTOVER / "step06a_class_context.py", "a25_step06a_class_context")
step06b_windows = _load_module(
    _CUTOVER / "step06b_windows_projection.py", "a25_step06b_windows_projection")
ledger = _load_module(
    SIDECAR / "services" / "gochara_kernel" / "ledger.py", "a25_gochara_ledger")

DEFAULT_EPHE_PATH = str(SIDECAR.parent.parent / ".run" / "se1")


def resolve_ephe_path(ctx: ContextSpec) -> str:
    """ASTRA A2.5 A5: ephemeris files from the pipeline image's SUPPORTED
    configuration. Resolution order:
      1. ctx.config["ephe_path"]   — explicit per-run override;
      2. $SWE_EPHE_PATH            — the image's own setting (Dockerfile
         .pipeline installs the files under /app/ephe and sets this);
      3. the dev-checkout default (.run/se1).
    The previous code took only (1) and silently fell through to (3), which
    resolves to a non-existent /app/.run/se1 in the image — the Swiss
    backend then answered a non-SWIEPH backend at knot sampling."""
    configured = ctx.config.get("ephe_path")
    if configured:
        return configured
    import os
    env_path = os.environ.get("SWE_EPHE_PATH")
    if env_path:
        return env_path
    return DEFAULT_EPHE_PATH

MANIFEST_SUBSTEP = "manifest"
WINDOWS_SUBSTEP = "windows"
BODY_SUBSTEP_PREFIX = "body:"

# Pravāha A2.5 is a one-chart candidate exercise (steward dispatch
# scripts/dispatch_a25_v41_candidate_job.py CHART_ID). The writer hard-refuses
# any other chart — a candidate generation must never be writable for an
# arbitrary chart via the planner surface.
PINNED_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"


class ChartRefusal(Exception):
    """ctx.config['chart_id'] is not the pinned A2.5 candidate chart — refused
    BEFORE any planning or DML (fail-closed; never a silent no-op)."""


class HorizonViolation(Exception):
    """A projected window row escaped the pinned '4.1' horizon — refused
    BEFORE any DML (fail-closed backstop; never clamped, never served)."""


def _require_pinned_chart(chart_id) -> None:
    """Fail-closed chart guard (ASTRA A2.5 A1: the runner passes chart_id as
    a UUID object; the standalone CLI and dispatch pass strings — BOTH are
    accepted by comparing the canonical string form)."""
    if str(chart_id) != PINNED_CHART_ID:
        raise ChartRefusal(
            f"{ASSET_ID}: chart_id {chart_id!r} is not the pinned A2.5 "
            f"candidate chart {PINNED_CHART_ID} — refusing (fail-closed; "
            "this asset is inert to all planners and runs only via the "
            "steward dispatch)")


def _validate_windows_within_horizon(rows: list[dict]) -> None:
    """Refuse any projected row outside [1998-01-01, 2026-04-18) — HALF-OPEN
    (ASTRA A2.5 A2).

    Rules (a violation is a defect in the chain, not data to trim — raise,
    never clamp):
      * window_start < 1998-01-01            — before the domain;
      * window_start >= 2026-04-18           — a window STARTING on the
        excluded end date is outside the domain (the day row the reviewer
        produced through the real projection);
      * window_end   >  2026-04-18           — past the domain (an exclusive
        interval endpoint may legitimately EQUAL the limit);
      * peak_date outside [window_start, window_end], before the domain, or
        ON/AFTER the excluded end date       — a peak on 2026-04-18 is
        outside the half-open horizon.

    Passed to step06b's project_windows_core as row_validator, so it runs
    after projection and BEFORE write_windows issues a single DML statement."""
    for r in rows:
        ws, we = r["window_start"], r["window_end"]
        if ws < HORIZON_MIN_DATE or ws >= HORIZON_MAX_DATE or we > HORIZON_MAX_DATE:
            raise HorizonViolation(
                f"{ASSET_ID}: projected {r['event_class']} {r.get('resolution')} "
                f"row [{ws}, {we}] escapes the pinned '4.1' horizon "
                f"[{HORIZON_MIN_DATE}, {HORIZON_MAX_DATE}) — refusing the "
                "substep before any DML (fail-closed, never clamped)")
        peak = r.get("peak_date")
        if peak is not None and (peak < HORIZON_MIN_DATE
                                 or peak >= HORIZON_MAX_DATE
                                 or peak < ws or peak > we):
            raise HorizonViolation(
                f"{ASSET_ID}: projected {r['event_class']} {r.get('resolution')} "
                f"row [{ws}, {we}] carries peak_date {peak} outside the "
                f"half-open horizon or its own span — refusing the substep "
                "before any DML (fail-closed, never clamped)")


def _validate_episodes_within_horizon(episodes: list[dict]) -> None:
    """Contact-side backstop (ASTRA A2.5 A2): every enumerated episode's
    instants honour the half-open horizon BEFORE write_contacts. t_in is
    clipped to the start at truncation (>= start); t_out may EQUAL the
    exclusive end; t_exact, when present, must lie strictly inside
    [start, end). Runs after enumeration and BEFORE any contact DML."""
    h_start = datetime.fromisoformat(HORIZON_START)
    h_end = datetime.fromisoformat(HORIZON_END)
    for ep in episodes:
        t_in, t_exact, t_out = ep.get("t_in"), ep.get("t_exact"), ep.get("t_out")
        if t_in is not None and not (h_start <= t_in <= h_end):
            raise HorizonViolation(
                f"{ASSET_ID}: enumerated contact t_in {t_in.isoformat()} "
                "outside the pinned horizon — refusing before contact DML "
                "(fail-closed, never clamped)")
        if t_out is not None and not (h_start <= t_out <= h_end):
            raise HorizonViolation(
                f"{ASSET_ID}: enumerated contact t_out {t_out.isoformat()} "
                "outside the pinned horizon — refusing before contact DML "
                "(fail-closed, never clamped)")
        if t_exact is not None and not (h_start <= t_exact < h_end):
            raise HorizonViolation(
                f"{ASSET_ID}: enumerated contact t_exact "
                f"{t_exact.isoformat()} violates the half-open horizon "
                f"[{HORIZON_START},{HORIZON_END}) — an exact instant on the "
                "excluded end belongs to the next domain; refusing before "
                "contact DML (fail-closed, never clamped)")


@register(ASSET_ID)
class GocharaV41CandidateWriter(WriterBase):
    """Pravāha A2.5 heavy writer: the '4.1' candidate chain, pipeline-governed.

    See the module docstring for the full contract, the substep decomposition
    and the three-layer candidate-only guarantee.
    """

    asset_id = ASSET_ID
    has_substeps = True

    # ASTRA A2.5 A3: the frozen hasher (asset_runner._writer_source_files)
    # follows STATIC imports only — but this writer loads its implementation
    # by importlib-by-path (scripts/ is not a package). Declare the COMPLETE
    # executable source closure so a change to any of these files invalidates
    # this writer's expected code digest:
    #   - this module (planning, guards, substeps);
    #   - the four step06 cutover modules loaded at lines ~150-163;
    #   - gochara_kernel/ledger.py (loaded here AND re-loaded inside
    #     step06_candidate_build._load_ledger / step06b_windows_projection);
    #   - gochara_kernel/legacy_semantics.py (loaded by step06b as `leg`).
    # The hasher extends each root through its static local imports.
    source_paths = [
        "platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v4_41_candidate.py",
        "platform/python-sidecar/scripts/kala_gochara_cutover/step06_enumerate_episodes.py",
        "platform/python-sidecar/scripts/kala_gochara_cutover/step06_candidate_build.py",
        "platform/python-sidecar/scripts/kala_gochara_cutover/step06a_class_context.py",
        "platform/python-sidecar/scripts/kala_gochara_cutover/step06b_windows_projection.py",
        "platform/python-sidecar/services/gochara_kernel/ledger.py",
        "platform/python-sidecar/services/gochara_kernel/legacy_semantics.py",
    ]

    # ------------------------------------------------------------------
    # FROZEN CONTRACT: plan_substeps
    # ------------------------------------------------------------------

    def plan_substeps(self, ctx: ContextSpec) -> list[SubStep]:
        """Fixed, honest plan: 'manifest' → 'body:<Body>' ×8 → 'windows'.

        The plan is static by design — the asset identity pins generation and
        horizon, and the body set is the chain's own M-3/R7 constant. A chart
        with no resonance map fails honestly inside the first body substep
        (NoResonanceMapError), never invents a plan."""
        _require_pinned_chart(ctx.config["chart_id"])
        steps = [SubStep(key=MANIFEST_SUBSTEP,
                         label="'4.1' candidate manifest (convention + gate)")]
        steps.extend(
            SubStep(key=f"{BODY_SUBSTEP_PREFIX}{body}",
                    label=f"'4.1' enumeration + contacts: {body}")
            for body in PERSISTED_BODIES
        )
        steps.append(SubStep(key=WINDOWS_SUBSTEP,
                             label="'4.1' class context + windows projection"))
        return steps

    # ------------------------------------------------------------------
    # FROZEN CONTRACT: run_substep
    # ------------------------------------------------------------------

    def run_substep(self, ctx: ContextSpec, step: SubStep) -> WriterResult:
        chart_id = ctx.config["chart_id"]
        _require_pinned_chart(chart_id)
        if ctx.dry_run:
            # ASTRA A2.5 A8: dry_run is honoured BEFORE every DML path — the
            # inherited run() aggregates through this method, so this single
            # gate covers both entry points; nothing is staged, solved or
            # written.
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=0,
                notes=f"dry_run: {step.key} not executed, nothing written")
        ephe_path = resolve_ephe_path(ctx)
        if step.key == MANIFEST_SUBSTEP:
            return self._run_manifest(ctx, chart_id)
        if step.key == WINDOWS_SUBSTEP:
            return self._run_windows(ctx, chart_id)
        if step.key.startswith(BODY_SUBSTEP_PREFIX):
            body = step.key[len(BODY_SUBSTEP_PREFIX):]
            if body not in PERSISTED_BODIES:
                return WriterResult(
                    asset_id=self.asset_id, rows_inserted=0,
                    notes=f"unknown body substep {step.key!r}")
            return self._run_body(ctx, chart_id, body, ephe_path)
        return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                            notes=f"unknown substep {step.key!r}")

    # ------------------------------------------------------------------
    # Substeps
    # ------------------------------------------------------------------

    def _run_manifest(self, ctx: ContextSpec, chart_id: str) -> WriterResult:
        """Once-per-chart ledger bootstrap on ctx.db_conn (no commit):
        §12.9 gate + register_convention + publish_candidate. Idempotent:
        the convention insert is ON CONFLICT DO NOTHING and a candidate
        manifest is replaced in place; a published '4.1' refuses (which is
        exactly the candidate-only rail)."""
        import time as _time

        t_start = _time.time()
        conn = ctx.db_conn
        # An empty episodes/coverage payload exercises only the manifest half
        # of the ledger lifecycle — contacts/coverage are written per body
        # substep. build_candidate_core is NOT used here because its
        # write_contacts would delete-then-insert an EMPTY payload over the
        # bodies already written; the manifest substep must not touch the
        # contact ledger at all.
        ledger_mod = ledger
        vector = dict(step06_build.GENERATION_VECTOR_FLAGS)
        vector["orb_max_deg"] = ORB_DEG
        vector["orb_ruling"] = "M-1 fallback no-box × 5.0° (unratified)"
        vector["delta_report"] = None
        if str(SIDECAR) not in sys.path:
            sys.path.insert(0, str(SIDECAR))
        from services.ka_vedha_gochara.freshness import (
            check_overlay_freshness, gate_allows_overlays)
        reports = check_overlay_freshness(conn, chart_id)
        vector["vedha_upstream_freshness"] = reports["house_vedha"].state
        vector["moorti_upstream_freshness"] = reports["moorti"].state
        vector["vedha_upstream_fingerprint"] = reports["house_vedha"].current
        vector["moorti_upstream_fingerprint"] = reports["moorti"].current
        if not gate_allows_overlays(reports):
            detail = "; ".join(
                f"{name}: {r.summary()}" for name, r in reports.items())
            raise step06_build.StaleOverlayRefusal(detail)
        # The recorded ephemeris claim is OBSERVED, not asserted (C17 /
        # §N.8 — a status needs a detector behind it): probe the calling
        # thread's live backend over the pinned horizon's JDs. backend_name
        # RAISES SwissBackendError on anything but 'swieph' (and
        # OutOfCorpusRangeError for a date outside the .se1 corpus window),
        # so a Moshier state refuses here — before register_convention —
        # and no manifest is written. probe_retflag is the flag set the
        # helper's Sun + TRUE_NODE probe ran under (FLG_SWIEPH | FLG_SPEED,
        # panchang_engine/swiss_backend.py _observed_backend_name), read
        # from the library rather than re-typed.
        import swisseph as _swe
        horizon_jds = (
            _swe.julday(1998, 1, 1, 12.0),
            _swe.julday(2026, 4, 18, 12.0))
        observed_backend = _swiss_backend.backend_name(*horizon_jds)
        probe_retflag = int(_swe.FLG_SWIEPH | _swe.FLG_SPEED)
        cid = ledger_mod.register_convention(
            conn, step06_build.CONVENTION_VECTOR,
            {"ephemeris_backend": observed_backend, "retflag": probe_retflag})
        manifest_id = ledger_mod.publish_candidate(
            conn, chart_id, GENERATION, cid, vector,
            {"backend": observed_backend, "retflag": probe_retflag}, HORIZON_TEXT,
            writer_asset_id=ASSET_ID)
        elapsed = _time.time() - t_start
        logger.info(
            "[%s] manifest substep chart=%s generation=%s convention=%s "
            "manifest=%s wall_clock_s=%.3f",
            ASSET_ID, chart_id, GENERATION, cid, manifest_id, elapsed)
        return WriterResult(
            asset_id=self.asset_id, rows_inserted=0, rows_updated=1,
            duration_seconds=elapsed,
            notes=(f"'4.1' candidate manifest {manifest_id} (convention {cid}); "
                   f"§12.9 {vector['vedha_upstream_freshness']}/"
                   f"{vector['moorti_upstream_freshness']}; "
                   f"ephemeris_backend={observed_backend} (probed)"))

    def _run_body(self, ctx: ContextSpec, chart_id: str, body: str,
                  ephe_path: str) -> WriterResult:
        """One body's enumeration + body-scoped contact/coverage writes.

        enumerate_core is DB-READ-ONLY on ctx.db_conn and returns the payload
        in memory (no JSON files — those are the CLI's surface). The ledger
        writes then delete-then-insert scoped (chart × '4.1' × body), so a
        partial run re-runs cleanly per body."""
        import time as _time
        t0 = _time.time()
        conn = ctx.db_conn
        h_start = datetime.fromisoformat(HORIZON_START)
        h_end = datetime.fromisoformat(HORIZON_END)
        episodes, coverage, report = step06_enumerate.enumerate_core(
            conn, chart_id=chart_id, generation=GENERATION,
            h_start=h_start, h_end=h_end, horizon_text=HORIZON_TEXT,
            orb_deg=ORB_DEG, ephe_path=ephe_path, refine=True,
            bodies=[body], dropped_refs_path=None)
        _validate_episodes_within_horizon(episodes)
        build_id = f"a25-v41-{ctx.build_id}-{body.lower()}"
        convention_id = report["convention_id"]
        ids = ledger.write_contacts(
            conn, chart_id, GENERATION, convention_id, episodes, build_id,
            bodies=[body])
        n_cov = ledger.write_coverage(
            conn, chart_id, GENERATION, convention_id, coverage, build_id,
            bodies=[body])
        elapsed = _time.time() - t0
        logger.info(
            "[%s] body=%s chart=%s contacts=%d coverage=%d wall_clock_s=%.3f",
            ASSET_ID, body, chart_id, len(ids), n_cov, elapsed)
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=len(ids) + n_cov, duration_seconds=elapsed,
            notes=(f"{body}: {len(ids)} contacts, {n_cov} coverage rows "
                   f"(episodes_truncated_no_exact_kept="
                   f"{report['episodes_truncated_no_exact_kept']})"))

    def _run_windows(self, ctx: ContextSpec, chart_id: str) -> WriterResult:
        """Class context (step06a, in-process) → windows projection (step06b
        core) at generation '4.1', with the horizon validator gating BEFORE
        any DML. write_windows is delete-then-insert scoped (chart × '4.1')
        — this substep's whole sub-span."""
        import time as _time
        t0 = _time.time()
        conn = ctx.db_conn
        import swisseph as swe

        contexts, omitted, null_exact = step06a_context.build_all_class_contexts(
            swe, conn, chart_id, GENERATION)
        out = step06b_windows.project_windows_core(
            conn, chart_id=chart_id, generation=GENERATION,
            baseline_generation=step06b_windows.BASELINE_DEFAULT,
            horizon_jd=(step06b_windows.jd_of(datetime.fromisoformat(HORIZON_START)),
                        step06b_windows.jd_of(datetime.fromisoformat(HORIZON_END))),
            horizon_start=HORIZON_START, horizon_end=HORIZON_END,
            orb_deg=ORB_DEG,
            min_lambda=step06b_windows.MIN_LAMBDA_DEFAULT,
            coarse_step_days=step06b_windows.COARSE_STEP_DAYS_DEFAULT,
            class_contexts=contexts,
            context_source=step06a_context.CONTEXT_SOURCE,
            rehearse_synthetic=False,
            build_id=f"a25-v41-{ctx.build_id}-windows",
            row_validator=_validate_windows_within_horizon)
        report = out["report"]
        elapsed = _time.time() - t0
        # ASTRA v1.3 amendment 1: the horizon stand-in is DISCLOSED here, not only in the
        # projection's class report — rows whose peak is a boundary-limited sample (not a
        # located extremum) are counted in the audit output as well as qualified per row.
        limited = report["horizon_limited"]
        logger.info(
            "[%s] windows substep chart=%s windows=%d classes=%d wall_clock_s=%.3f "
            "horizon_limited_rows=%d final_edge_components=%d peaks_clamped_to_horizon_limit=%d",
            ASSET_ID, chart_id, report["windows_written"],
            report["classes_projected"], elapsed, limited["rows_projected"],
            limited["final_edge_components"], limited["peaks_clamped_to_horizon_limit"])
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=report["windows_written"], duration_seconds=elapsed,
            notes=(f"windows={report['windows_written']} "
                   f"classes={report['classes_projected']} "
                   f"class_context_omitted={len(omitted)} "
                   f"null_t_exact_excluded={null_exact} "
                   f"unmapped={report['contacts_unmapped_no_class']}/"
                   f"{report['contacts_unmapped_relation']} "
                   f"horizon_limited_rows={limited['rows_projected']} "
                   f"final_edge_components={limited['final_edge_components']} "
                   f"peaks_clamped_to_horizon_limit={limited['peaks_clamped_to_horizon_limit']} "
                   f"horizon_limited_basis={limited['peak_basis']}"))
