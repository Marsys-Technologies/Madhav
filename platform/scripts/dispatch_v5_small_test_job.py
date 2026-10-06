"""
dispatch_v5_small_test_job.py — Pravāha C37: steward-run dispatch of a SMALL
TEST build of asset ka_gochara_v5, modelled on dispatch_a25_v41_candidate_job.py
(same frozen-manifest staging pattern).

SHIPS IN THE PR BUT RUNS ONLY ON STEWARD GO — and only when BOTH
--i-am-steward AND --after-settled-1 are passed (the protected window's
settled-1 precondition). Without both flags the script refuses (exit 2)
before touching anything.

PRECONDITION: migration 1304 (PR 3101) has been applied — it is the ONLY source
of the ka_gochara_v5 registry row's small-test shape (has_substeps true,
writer_timeout_seconds 28800, depends_on [ga_positions, ga_dashas], the
ka_gochara_eval_window counter). This script does NOT insert or alter that row;
it VALIDATES it field by field and refuses on any difference or if the row is
absent (A2 review: the old INSERT carried the pre-1304 shape and could never
fire against a real row).

This script only STAGES, in ONE database transaction, under the Gochara chart lock, and it NEVER changes the registry row:
  0. ADMISSION (Codex PR 3097 rulings; all read-only, all before anything is staged, all refusals named). The chart lock
     `ka_gochara_lock_chart` is taken first (behind a lock_timeout), then:
       - generation '5.0' must not be PUBLISHED, SEALED or the SERVING generation (`v5_small_test_shared.refuse_if_frozen`, the same
         check the teardown makes);
       - the registry row is locked (`SELECT ... FOR SHARE`: a concurrent change blocks until this transaction ends) and validated
         INACTIVE against EXPECTED_REGISTRY_ROW (the 1304 values); it is never activated, because activation fires migration 596's
         freshness invalidation across EVERY chart and the worker does not need it. The reused candidate loader is run on the inactive row;
       - the Nirmana monitor's N-137 conditions (`v5_small_test_shared.end_state_problems`, the ONE copy the teardown uses too):
         catalog_status not RETIRED, nothing depends on the asset, no receipt or build_run_assets evidence of the asset on ANY chart
         from a run that is not a small-test run (a NULL run link counts as non-test);
       - CLEAN RECEIPTS: no provenance receipt of the asset exists for the chart. The orchestrator's delta-skip compares a receipt with the
         chart and birth configuration, not the slice marker, so after one slice a matching proven receipt could make the NEXT run skip
         the writer and re-attribute the old output. The sequence is: run 1, teardown, run 2, teardown;
       - any existing unsealed generation '5.0' candidate output must be a PROVEN small-test slice
         (`v5_small_test_shared.generation_ownership`, the SAME proof the teardown uses): the snapshot substep deletes the whole
         generation's chain, so an existing non-test candidate is refused, never replaced;
  1. asset_throughput forced 'dormant' for the PINNED chart (per_chart scope), as the orchestrator expects for a genuine build;
  2. a build_runs row (scope='asset_set', scope_target=the asset, action='rebuild', triggered_by='gochara-v5-small-test') carrying
     plan_manifest and plan_manifest_digest: build_manifest ('nirmana-run-manifest/v1') PLUS the slice marker merged into the manifest
     BEFORE the sha256 digest is computed. The manifest's asset depends_on is the registry's depends_on (the runner requires the two to be
     equal);
  3. its build_run_assets row.
WHICH ROLE: `data_plane_builder` SUFFICES (production catalog, read-only, Stream B 2026-10-05): it holds every SELECT the admission checks
need, EXECUTE on `ka_gochara_lock_chart`, SELECT/INSERT/UPDATE/DELETE on `asset_throughput`, `build_runs` and `build_run_assets`, and its
column UPDATE grant on `asset_registry` is what makes the `FOR SHARE` row lock work. It never updates `asset_registry.is_active` and deletes
nothing; `amjis_app` is not needed. A real-database test runs this script as a role holding exactly that list.

ANY PRIOR '5.0' OUTPUT REFUSES (Codex round 4 D3): if ANY generation '5.0' candidate, output, snapshot, inventory or manifest exists for
the chart the dispatch refuses, proven small test or not; it never builds over existing output (the snapshot substep replaces the whole
chain). Clear it first with the runbook's teardown. A run that was staged and never executed is failed by the cockpit watchdog after 10
minutes and then carries no receipts and no output: the teardown removes it. Before the watchdog acts it is an active run, which blocks
both this dispatch and the teardown by name.

LOOKUP ONLY (`--list-runs` / `--lookup RUN_ID`, Codex round 4 D1): one READ ONLY transaction, no lock, no admission check, no staging, no
steward flag. After an unknown commit outcome the admission checks would refuse (the run now exists), so this is how the attempted run id is
looked up. The commit-unknown message names the command.

DEADLINES come from the STORED `created_at` the INSERT returns, never the client clock (D4).

THE JOB IMAGE MUST BE THE ONE BUILT FROM THE SAME COMMIT as the checkout this script runs from: the manifest pins the writer digest of this
checkout and `execute_run` refuses a run whose image has a different one. The dispatch prints the expected digest and the commit.

EXECUTE WITHIN 10 MINUTES of a real dispatch: the cockpit watchdog fails a planned run that was never started after 10 minutes
(`watchdog/route.ts`), so the printed `gcloud run jobs execute` must follow promptly or the run must be re-staged.

THE SLICE MARKER is the writer's contract, not a copy of it: plan_manifest[
"gochara_v5_test_slice"] = {"schema": "gochara_v5_test_slice/1", "run":
"all_classes_1y" | "one_class_full", "horizon": [<start>, <end>], "classes":
[...]} — exactly those four fields. Before ANY database connection the built
marker is passed through the WRITER's own validator
(ka_gochara_v5._validate_test_slice, imported from the sidecar), so a marker the
writer would refuse never reaches a staged run:
  * horizons are tz-aware ISO timestamps (a naive timestamp is refused; they are
    stored normalised to UTC). one_class_full defaults to the writer's full
    DEFAULT_HORIZON; all_classes_1y needs --horizon-start/--horizon-end (≤ 366 days,
    inside DEFAULT_HORIZON);
  * classes come from the writer's SCORED_CLASSES (26): --classes all (the default
    for all_classes_1y) or a comma list; one_class_full takes exactly one class.

The chart is the pinned canonical chart 482012f1-710e-4a25-994a-93821f5871aa
ONLY — there is no chart argument; any other chart is refused by construction.
The DSN comes from the PROCESS ENVIRONMENT only (DATABASE_URL): never on argv, never printed, and never read from a file in the
checkout (this script no longer reads `.env.local`). A failure prints the exception CLASS, never its text: a connection error
can carry the credentials.

STAGING NEEDS EXPLICIT INTENT. The default is a DRY RUN: the SAME staging transaction runs but ROLLS BACK instead of committing
and prints the staged plan (run row + manifest) as JSON — nothing is written. Writing the run needs `--execute` (together with the
two steward flags). `--dry-run` is accepted as an explicit spelling of the default; it cannot be combined with `--execute`.

RETENTION: TEAR THE SMALL TEST DOWN WITHIN 90 DAYS. The cockpit watchdog deletes terminal build runs 90 days after their
creation (`app/api/cockpit/watchdog/route.ts`, "M-4") and `asset_provenance_receipts.build_id` is ON DELETE SET NULL; the teardown
refuses a receipt with no run link for good. The dispatch prints the teardown deadline when it stages a run. Past the window the only
way out is the steward recovery runbook, 00_ARCHITECTURE/briefs/pravaha/V5_SMALLTEST_TEARDOWN_RUNBOOK_v1_0.md.

A FAILURE reports what is KNOWN about the transaction (rollback confirmed, rollback not confirmed, or commit outcome unknown — a
COMMIT was sent and no answer came back); it never claims the database is unchanged unless a rollback was confirmed.

THE RESULT IS READ FROM THE DATABASE: the orchestrator process exits 0 even when the run ends failed (execute_run returns normally); read
`build_runs.state` and `build_run_assets` (state, error) for the run id, never the Cloud Run execution status.

Execution happens separately, after steward go:

  gcloud run jobs execute brahma-build-pipeline-job --args=--run-id,<run_id>

Teardown is a SEPARATE script (C38, teardown_v5_small_test_job.py) — this
script never deletes anything.

Usage:
  cd <repo-root>/platform
  python3 scripts/dispatch_v5_small_test_job.py --i-am-steward --after-settled-1 \
      --run all_classes_1y --horizon-start 2025-04-01T00:00:00+00:00 \
      --horizon-end 2026-04-01T00:00:00+00:00 [--classes all] [--execute]
  python3 scripts/dispatch_v5_small_test_job.py --i-am-steward --after-settled-1 \
      --run one_class_full --classes <one scored class> [--execute]
  python3 scripts/dispatch_v5_small_test_job.py --help
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import sys
import uuid

from dispatch_frozen_rebuild import (
    _canonical_json,
    _load_writer_digest,
    build_manifest,
)
import v5_small_test_shared as shared
from v5_small_test_shared import ASSET_ID, CHART_ID, TRIGGERED_BY

LOCK_TIMEOUT = "10s"                      # the chart lock is requested behind this: fail closed, never wait forever
EXECUTE_WITHIN_MINUTES = 10               # the watchdog fails a planned, never-started run after this long (watchdog/route.ts)
RETENTION_DAYS = 90                       # the cockpit watchdog's terminal-run retention (watchdog/route.ts, M-4)
RUNBOOK = "00_ARCHITECTURE/briefs/pravaha/V5_SMALLTEST_TEARDOWN_RUNBOOK_v1_0.md"
OUTCOME_TEXT = {
    "no_transaction": "No transaction was opened.",
    "rolled_back": "ROLLBACK CONFIRMED: this run changed nothing in the database.",
    "rollback_unconfirmed": ("ROLLBACK NOT CONFIRMED: the rollback itself failed. No COMMIT was sent, so the server rolls the "
                             "transaction back when the session ends, but this run did not observe that."),
    "before_commit": ("No COMMIT was sent by this run, so it committed nothing; any open transaction is rolled back by the server "
                      "when the session ends (this run did not observe that)."),
    "committed": ("COMMIT CONFIRMED: the transaction COMMITTED and the small-test run IS STAGED; only reporting the result failed "
                  "afterwards. Do not dispatch again; the run id is named above."),
    "unlabelled": ("What happened to the transaction was NOT recorded for this failure, so nothing is claimed either way: look the attempted "
                   "run id up with the READ-ONLY lookup (python3 scripts/dispatch_v5_small_test_job.py --lookup <the attempted run id>, or "
                   "--list-runs) before any retry."),
    "commit_unknown": ("COMMIT OUTCOME UNKNOWN: the COMMIT statement was sent and no confirmation came back. The staged run may or "
                       "may not exist. Look it up with the READ-ONLY lookup (it needs no admission checks and stages nothing): "
                       "python3 scripts/dispatch_v5_small_test_job.py --lookup <the attempted run id named above> (or --list-runs); do not retry "
                       "before you know. Do not assume either way."),
}


def _AFTER_COMMIT() -> None:
    """The point right after a confirmed COMMIT. Does nothing; it exists so a test can fail exactly here (Codex round 5)."""


def _note_outcome(exc: BaseException, outcome: str) -> None:
    """Attach what is KNOWN about the transaction to the exception, for the process boundary to report."""
    try:
        exc.dispatch_outcome = outcome        # type: ignore[attr-defined]
    except Exception:
        pass

# The shape the ka_gochara_v5 registry row MUST have before staging — the values migration 1304
# (PR 3101) lands, compared field by field. depends_on is compared in 1304's order.
EXPECTED_COUNT_SQL = ("SELECT COUNT(*) FROM ka_gochara_eval_window "
                      "WHERE chart_id=$1 AND generation='5.0'")
EXPECTED_REGISTRY_ROW = {
    "scope": "per_chart",
    "is_active": False,
    "has_writer": True,
    "has_substeps": True,
    "writer_timeout_seconds": 28800,
    "depends_on": ["ga_positions", "ga_dashas"],
    "target_table": "ka_gochara_eval_window",
    "count_sql": EXPECTED_COUNT_SQL,
    "target_floor": 0,
    "estimated_seconds": None,
    # Codex round 4 D2: the fields asset_runner.py reads (the "Asset metadata" block, ~1590-1615) to decide how the asset is run. A row with
    # an integrity_check_sql (or a probe) AND rebuild_on_probe_fail = true takes the PROBE-GREEN SHORTCUT: a passing probe marks the asset
    # built without running the writer. A data writer must route as plain data and must have none of those.
    "asset_kind": "data",
    "asset_type": "data",
    "health_probe": None,
    "integrity_check_sql": None,
    "rebuild_on_probe_fail": False,
}
REGISTRY_READBACK = "platform/scripts/v5_small_test_registry_row_readback.sql"


def _validate_registry_row(cur) -> None:
    """Lock the registry row (FOR SHARE: a concurrent UPDATE or activation blocks until this transaction ends; the lock needs UPDATE on
    at least one column, which the builder holds for its health columns) and validate it INACTIVE, field by field. Never activates."""
    cur.execute(
        """SELECT scope, is_active, has_writer, has_substeps, writer_timeout_seconds,
                  depends_on, target_table, count_sql, target_floor, estimated_seconds,
                  asset_kind, asset_type, health_probe, integrity_check_sql, rebuild_on_probe_fail
           FROM asset_registry WHERE asset_id = %s FOR SHARE""",
        (ASSET_ID,),
    )
    row = cur.fetchone()
    if row is None:
        raise RuntimeError(
            f"asset_registry has no {ASSET_ID} row — migration 1243 (row) and 1304 (small-test "
            "shape) must be applied before this dispatch; this script never inserts it")
    for field, expected in EXPECTED_REGISTRY_ROW.items():
        actual = row[field]
        if field == "depends_on":
            actual = list(actual or [])
        if field in ("health_probe", "integrity_check_sql") and actual == "":
            actual = None                             # an empty string reads as NULL: the runner tests both with bool() (migration 1304 agrees)
        if actual != expected:
            raise RuntimeError(
                f"{ASSET_ID}.{field} is {actual!r}, expected {expected!r} — the registry row "
                "is not in the migration-1304 small-test shape; a non-conforming row would "
                "change how this build is scheduled, budgeted or routed (apply 1304, do not edit by hand; "
                f"{REGISTRY_READBACK} shows the production row)")


SLICE_MARKER_SCHEMA = "gochara_v5_test_slice/1"
SLICE_RUNS = ("all_classes_1y", "one_class_full")


def _writer():
    """The sidecar writer module (its slice contract is the single source of truth)."""
    sidecar = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "python-sidecar"))
    if sidecar not in sys.path:
        sys.path.insert(0, sidecar)
    try:
        import pipeline.orchestrator.writers.ka_gochara_v5 as writer
    except Exception as exc:  # an environment without the sidecar deps cannot validate: refuse, never skip
        raise RuntimeError(
            f"cannot import the ka_gochara_v5 writer to validate the slice marker ({exc!r}); "
            "run this from an environment with the sidecar dependencies") from exc
    return writer


def _utc_iso(label: str, raw: str) -> str:
    try:
        value = datetime.datetime.fromisoformat(raw)
    except ValueError:
        raise RuntimeError(f"{label} {raw!r} is not an ISO 8601 timestamp")
    if value.tzinfo is None:
        raise RuntimeError(
            f"{label} {raw!r} has no timezone — pass a tz-aware timestamp such as "
            "2025-04-01T00:00:00+00:00; an unstated zone is never guessed")
    return value.astimezone(datetime.timezone.utc).isoformat()


def build_slice_marker(*, run: str, classes: str | None = None,
                       horizon_start: str | None = None, horizon_end: str | None = None) -> dict:
    """The slice marker merged into plan_manifest under 'gochara_v5_test_slice', validated by the
    WRITER's own _validate_test_slice before it is returned (a TestSliceRefusal propagates by
    name). classes: None / 'all' = every scored class (all_classes_1y), else a comma list. Horizons
    are tz-aware ISO timestamps, stored in UTC; one_class_full defaults to the full DEFAULT_HORIZON."""
    writer = _writer()
    if run not in SLICE_RUNS or tuple(writer.TEST_SLICE_RUNS) != SLICE_RUNS:
        raise RuntimeError(f"--run must be one of {SLICE_RUNS} (writer: {tuple(writer.TEST_SLICE_RUNS)}), got {run!r}")
    if classes is None:
        if run == "one_class_full":
            raise RuntimeError("--classes must name exactly one scored class for run 'one_class_full'")
        names = list(writer.SCORED_CLASSES)
    elif classes.strip() == "all":
        names = list(writer.SCORED_CLASSES)
    else:
        names = [c.strip() for c in classes.split(",") if c.strip()]
        if not names:
            raise RuntimeError("--classes must be 'all' or a non-empty comma-separated list")
    if horizon_start is None and horizon_end is None and run == "one_class_full":
        start, end = (x.astimezone(datetime.timezone.utc).isoformat() for x in writer.DEFAULT_HORIZON)
    elif horizon_start is None or horizon_end is None:
        raise RuntimeError("--horizon-start and --horizon-end are both required "
                           "(only one_class_full may omit both, meaning the full DEFAULT_HORIZON)")
    else:
        start, end = _utc_iso("horizon_start", horizon_start), _utc_iso("horizon_end", horizon_end)
    marker = {"schema": SLICE_MARKER_SCHEMA, "run": run, "horizon": [start, end], "classes": names}
    validated = writer._validate_test_slice(marker)
    # The marker is STAGED in its exact CANONICAL form: classes in the writer's scored order, horizon as the +00:00 ISO strings the writer's
    # own component stores. The writer hashes the marker as given and stores the normalised form; staging the canonical form makes the two
    # the same text, so the digest in the manifest stamp and the digest of the stored component can never disagree (Codex round 3).
    canonical = {"schema": validated.marker["schema"], "run": validated.run,
                 "horizon": [validated.horizon[0].isoformat(), validated.horizon[1].isoformat()], "classes": list(validated.classes)}
    again = writer._validate_test_slice(canonical)           # the canonical form is a fixed point of the writer's normalisation
    if (again.classes, again.horizon, again.run) != (validated.classes, validated.horizon, validated.run):  # pragma: no cover
        raise RuntimeError("the canonical marker does not normalise to itself")
    return canonical


def build_small_test_manifest(*, candidate, slice_marker: dict) -> tuple[dict, str]:
    """The frozen asset_set manifest PLUS the slice marker, digested once."""
    manifest, _ = build_manifest(
        chart_id=CHART_ID,
        candidate=candidate,
        expected_code_digest=_load_writer_digest(ASSET_ID),
    )
    manifest["gochara_v5_test_slice"] = slice_marker
    digest = hashlib.sha256(_canonical_json(manifest).encode("utf-8")).hexdigest()
    return manifest, digest


def checkout_commit() -> tuple[str, bool]:
    """(HEAD commit of the checkout this script runs from, whether the sidecar or the writer-digest file has UNCOMMITTED changes). Best
    effort: ('unknown', False) when git is unavailable. No shell, fixed arguments."""
    import subprocess
    here = os.path.dirname(os.path.abspath(__file__))
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=here, capture_output=True, text=True, timeout=20, check=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "--", "python-sidecar", "src/generated/nirmana-writer-digests.json"],
                               cwd=os.path.join(here, ".."), capture_output=True, text=True, timeout=20, check=True).stdout.strip()
        return head, bool(dirty)
    except Exception:
        return "unknown", False


def image_skew_notice(manifest: dict) -> list[str]:
    """DB3 (Stream B X3): execute_run REFUSES a run whose job image has a different writer digest from the manifest's ('sidecar code digest
    does not match'; the run is terminalised failed). The manifest's digest comes from THIS checkout, so the job image must be the one built
    from the same commit. Printed with the staged run: the expected writer digest and the commit."""
    commit, dirty = checkout_commit()
    digest = manifest["assets"][0]["expected_code_digest"]
    lines = [f"[dispatch] JOB IMAGE MUST MATCH THIS CHECKOUT: the manifest pins the writer digest {digest} of {ASSET_ID} (from commit "
             f"{commit}); the pipeline job's image must be the one built from that SAME commit, or the runner refuses the run ('sidecar code "
             "digest does not match') and marks it failed. After any later writer change, re-dispatch from the matching checkout."]
    lines.append("[dispatch] READ THE RESULT FROM THE DATABASE, NOT FROM CLOUD RUN: the orchestrator process exits 0 even when the run ends "
                 "failed (execute_run returns normally), so a green Cloud Run execution does not mean the run succeeded. Read build_runs.state and "
                 "build_run_assets (state, error) for the run id printed below.")
    if dirty:
        lines.append("[dispatch] WARNING: this checkout has UNCOMMITTED changes under python-sidecar or the writer-digest file: no built image "
                     "can match the digest pinned above.")
    return lines


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="dispatch_v5_small_test_job.py",
        description="Stage a SMALL TEST build_run of ka_gochara_v5 (steward only).")
    p.add_argument("--i-am-steward", action="store_true",
                   help="required: you are the steward, acting on native authority")
    p.add_argument("--after-settled-1", action="store_true",
                   help="required: the protected window's settled-1 precondition has passed")
    p.add_argument("--run", choices=SLICE_RUNS,
                   help="the small-test run identity: all_classes_1y or one_class_full (required unless --list-runs / --lookup)")
    p.add_argument("--classes", default=None,
                   help="'all' (default for all_classes_1y) or a comma-separated list of scored "
                        "classes; one_class_full takes exactly one")
    p.add_argument("--horizon-start", default=None,
                   help="tz-aware ISO timestamp, e.g. 2025-04-01T00:00:00+00:00 "
                        "(required for all_classes_1y; one_class_full defaults to the full horizon)")
    p.add_argument("--horizon-end", default=None, help="tz-aware ISO timestamp (see --horizon-start)")
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true",
                      help="the DEFAULT: run the same staging transaction, ROLL BACK, print the staged plan")
    mode.add_argument("--execute", action="store_true",
                      help="actually stage the run (COMMIT); without it nothing is written")
    mode.add_argument("--list-runs", action="store_true",
                      help="LOOKUP ONLY: list the existing 'gochara-v5-small-test' runs of the pinned chart (read-only transaction; no "
                           "admission checks, no staging, no steward flags needed)")
    mode.add_argument("--lookup", metavar="RUN_ID", default=None,
                      help="LOOKUP ONLY: report one run id if it exists (same read-only listing as --list-runs)")
    args = p.parse_args(argv)
    if not (args.list_runs or args.lookup) and not args.run:
        p.error("--run is required unless --list-runs or --lookup is given")
    return args


def _take_chart_lock(cur) -> None:
    """The Gochara chart transaction lock (`ka_gochara_lock_chart`), behind a lock_timeout so a competing writer makes the dispatch fail
    closed instead of waiting. Every admission check below runs INSIDE it, to commit."""
    cur.execute("SELECT set_config('lock_timeout', %s, true)", (LOCK_TIMEOUT,))
    cur.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))


def _load_inactive_candidate(cur) -> dict:
    """The reused candidate loader's query (dispatch_frozen_rebuild._load_candidate) WITHOUT its `is_active = true` filter: the registry row
    is read INACTIVE, as it is, and never activated (activation fires migration 596's freshness invalidation across every chart, and the
    worker does not need the row active). A test pins that this SELECT equals the helper's apart from that one filter."""
    cur.execute(
        """
        SELECT ar.asset_id, ar.layer, ar.scope, ar.asset_kind,
               COALESCE(ar.depends_on, '{}') AS depends_on,
               ar.natural_key_partition,
               EXISTS (
                 SELECT 1 FROM asset_registry peer
                  WHERE peer.target_table = ar.target_table
                    AND ar.target_table IS NOT NULL
                    AND peer.asset_id <> ar.asset_id
                    AND peer.is_active = true AND peer.has_writer = true
               ) AS has_cowriters
          FROM asset_registry ar
         WHERE ar.asset_id = %s AND ar.has_writer = true
        """,
        (ASSET_ID,),
    )
    row = cur.fetchone()
    if not row:
        raise RuntimeError(f"writer registry row missing for {ASSET_ID}")
    return dict(row)


def _existing_small_test_runs(cur) -> list[dict]:
    """The small-test runs already on record for the chart (newest first): the listing the dry run prints, which is how an operator looks
    up an attempted run after an unknown commit outcome, and the owned runs whose original markers prove an existing candidate's stamp."""
    cur.execute("SELECT id, state, created_at, plan_manifest_digest FROM build_runs WHERE chart_id = %s AND triggered_by = %s"
                " ORDER BY created_at DESC", (CHART_ID, TRIGGERED_BY))
    return [{"id": str(r["id"]), "state": r["state"], "created_at": str(r["created_at"]),
             "plan_manifest_digest": r["plan_manifest_digest"]} for r in cur.fetchall()]


LOOKUP_COMMAND = "python3 scripts/dispatch_v5_small_test_job.py --lookup <attempted run id>"


def lookup(*, run_id: str | None = None) -> list[dict]:
    """Codex round 4 D1: the lookup-only mode. One READ ONLY transaction: it takes no lock, runs no admission check, stages nothing and
    needs no steward flag. After an unknown commit outcome the admission checks would REFUSE (the staged run now exists), so the operator's
    way to find out whether the attempted run exists cannot be the dry run. Returns the small-test runs of the pinned chart (all of them,
    or only `run_id`)."""
    import psycopg
    import psycopg.rows

    conn = psycopg.connect(os.environ["DATABASE_URL"], row_factory=psycopg.rows.dict_row)
    try:
        conn.autocommit = False
        cur = conn.cursor()
        cur.execute("SET TRANSACTION READ ONLY")
        runs = _existing_small_test_runs(cur)
        conn.rollback()
    finally:
        try:
            conn.close()
        except Exception:
            pass
    return [r for r in runs if run_id is None or r["id"] == run_id]


def _admit(cur) -> tuple[list[dict], list[str]]:
    """Every admission check (Codex PR 3097 rulings 1 to 5), read-only, INSIDE the chart lock and before anything is staged. Returns the
    existing small-test runs and notes for the listing; raises a named refusal otherwise."""
    notes: list[str] = []
    _take_chart_lock(cur)
    shared.refuse_if_frozen(cur)                                   # ruling 1: published / sealed / serving
    cur.execute("SELECT id, state FROM build_runs WHERE chart_id = %s AND state IN ('planned', 'running', 'paused') ORDER BY created_at",
                (CHART_ID,))
    active = cur.fetchall()
    if active:                                                     # DB2: named, before migration 595's one-active-run index raises bare
        raise shared.Refused(
            f"a build run is already active on chart {CHART_ID}: {[(str(r['id']), r['state']) for r in active]} — migration 595 allows one "
            "active run per chart; wait for it to end (a planned run that was never started is failed by the cockpit watchdog after "
            f"{EXECUTE_WITHIN_MINUTES} minutes) or stop it, then dispatch")
    _validate_registry_row(cur)                                    # ruling 4 + 3: row locked FOR SHARE, validated inactive, never activated
    problems = shared.end_state_problems(cur)                      # ruling 2: the monitor's N-137 conditions (the shared copy)
    if problems:
        raise shared.Refused("the Nirmana N-137 conditions for the small-test asset do not hold: " + "; ".join(problems))
    receipts = shared.count(cur, "SELECT count(*) AS n FROM asset_provenance_receipts WHERE asset_id = %s AND chart_id = %s",
                            (ASSET_ID, CHART_ID))
    if receipts:                                                   # ruling 5: the orchestrator's delta-skip could reuse an old receipt
        raise shared.Refused(
            f"{receipts} provenance receipt(s) of {ASSET_ID} exist for chart {CHART_ID}: the orchestrator's delta-skip compares a receipt "
            "with the chart and birth configuration, not the slice marker, so a matching proven receipt could make this run SKIP the writer "
            "and re-attribute the old output to it. Tear the previous small test down first (run 1, teardown, run 2, teardown)")
    existing = _existing_small_test_runs(cur)
    # Codex round 4 D3: ANY prior generation '5.0' candidate, output, snapshot, inventory or manifest REFUSES the dispatch, proven small test or
    # not. The snapshot substep replaces the whole generation's chain, so a dispatch over existing output is exactly the interrupted-replacement
    # hazard; the only way forward is a clean start. The refusal does not name another script: it names the runbook.
    rows, manifest = shared.generation_exists(cur)
    if rows or manifest is not None:
        raise shared.Refused(
            f"generation '{shared.GENERATION}' already has output for chart {CHART_ID} ({rows} output row(s); manifest "
            f"{'present, status ' + str(manifest['status']) if manifest is not None else 'absent'}): this dispatch never builds over it, "
            f"proven small test or not — clear it first, see {RUNBOOK}")
    return existing, notes


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    if args.list_runs or args.lookup:
        run_id = None
        if args.lookup:
            try:
                run_id = str(uuid.UUID(args.lookup))
            except ValueError:
                print(f"REFUSAL: --lookup {args.lookup!r} is not a run id (a UUID)", file=sys.stderr)
                sys.exit(2)
        if not os.environ.get("DATABASE_URL"):
            print("REFUSAL: DATABASE_URL is not set in the process environment (this script reads no file and takes no URL "
                  "argument)", file=sys.stderr)
            sys.exit(2)
        runs = lookup(run_id=run_id)
        if run_id is not None and not runs:
            print(f"[lookup] run {run_id} does NOT exist for chart {CHART_ID} ('{TRIGGERED_BY}' runs: read-only lookup).", file=sys.stderr)
        print(json.dumps({"chart_id": CHART_ID, "triggered_by": TRIGGERED_BY, "runs": runs}, indent=2, sort_keys=True), flush=True)
        return
    if not (args.i_am_steward and args.after_settled_1):
        print("REFUSAL: this dispatch runs only on steward go AFTER settled-1 — "
              "pass BOTH --i-am-steward and --after-settled-1", file=sys.stderr)
        sys.exit(2)
    try:
        slice_marker = build_slice_marker(
            run=args.run, classes=args.classes,
            horizon_start=args.horizon_start, horizon_end=args.horizon_end)
    except Exception as exc:  # RuntimeError or the writer's TestSliceRefusal: nothing touched yet
        print(f"REFUSAL: {exc}", file=sys.stderr)
        sys.exit(2)

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("REFUSAL: DATABASE_URL is not set in the process environment (this script reads no file and takes no URL "
              "argument)", file=sys.stderr)
        sys.exit(2)
    dry_run = not args.execute                       # the default is a dry run: writing needs --execute

    import psycopg
    import psycopg.rows

    try:
        conn = psycopg.connect(database_url, row_factory=psycopg.rows.dict_row)
    except Exception as exc:
        _note_outcome(exc, "no_transaction")
        raise
    conn.autocommit = False
    cur = conn.cursor()

    run_id = str(uuid.uuid4())                       # generated up front so ANY failure message can name the attempted run
    created_at = None                                # the stored value, returned by the INSERT (None on a dry run: no row is kept)
    phase = "open"                                   # open -> committing (COMMIT sent) -> committed
    try:
        existing, notes = _admit(cur)
        candidate = _load_inactive_candidate(cur)    # the row is read inactive; NO UPDATE of asset_registry is ever issued
        manifest, manifest_digest = build_small_test_manifest(
            candidate=candidate, slice_marker=slice_marker)

        # Force dormant (per_chart scope) so the orchestrator treats this as a
        # genuine build, not a no-op over an already-lit asset.
        cur.execute(
            """INSERT INTO asset_throughput (chart_id, asset_id, state)
               VALUES (%s, %s, 'dormant')
               ON CONFLICT (chart_id, asset_id) WHERE chart_id IS NOT NULL
               DO UPDATE SET state = 'dormant', rows_written = 0, last_error = NULL""",
            (CHART_ID, ASSET_ID),
        )

        cur.execute(
            """INSERT INTO build_runs
                 (id, chart_id, scope, scope_target, action, state, plan,
                  plan_manifest, plan_manifest_digest, triggered_by)
               VALUES (%s, %s, 'asset_set', %s, 'rebuild', 'planned', %s::jsonb,
                       %s::jsonb, %s, %s)
               RETURNING created_at""",
            (run_id, CHART_ID, ASSET_ID, json.dumps([ASSET_ID]),
             json.dumps(manifest), manifest_digest, TRIGGERED_BY),
        )
        # Codex round 4 D4: the deadlines come from the STORED created_at (the database clock the watchdog uses), never the client's
        created_at = cur.fetchone()["created_at"]
        cur.execute(
            """INSERT INTO build_run_assets (run_id, asset_id, position, state)
               VALUES (%s, %s, 0, 'queued')""",
            (run_id, ASSET_ID),
        )
        # Codex round 6 (1): EVERYTHING that will be printed is prepared BEFORE the COMMIT, so nothing that can fail after it needs data or work
        report = _prepare_report(dry_run=dry_run, run_id=run_id, manifest=manifest, manifest_digest=manifest_digest, existing=existing,
                                 notes=notes, created_at=created_at)
        if dry_run:
            conn.rollback()
            phase = "rolled_back"
        else:
            phase = "committing"
            conn.commit()
            phase = "committed"
            _AFTER_COMMIT()
        try:
            conn.close()
        except Exception:
            pass
        _emit_report(report)
    except BaseException as exc:
        # ONE handler for the whole transaction life, including the close and the printing: the outcome and the attempted run id are attached
        # to ANY exception, whatever phase it came from (an interrupt included), and the phase alone decides what is claimed
        exc.dispatch_run_id = run_id                 # type: ignore[attr-defined]
        if phase == "committing":                    # the COMMIT was sent and nothing came back: never roll back or claim 'unchanged'
            _note_outcome(exc, "commit_unknown")
        elif phase == "committed":                   # confirmed: no rollback is attempted or reported
            _note_outcome(exc, "committed")
        elif phase == "rolled_back":                 # the dry run's ROLLBACK completed
            _note_outcome(exc, "rolled_back")
        else:                                        # still open: roll back and say whether it was confirmed
            _note_outcome(exc, "rollback_unconfirmed")
            try:
                conn.rollback()
                _note_outcome(exc, "rolled_back")
            except BaseException:
                pass
        try:
            conn.close()
        except BaseException:                        # an interruption here must not replace the exception already propagating
            pass
        raise


def _prepare_report(*, dry_run: bool, run_id: str, manifest: dict, manifest_digest: str, existing: list, notes: list, created_at) -> dict:
    """Everything the run will print, built BEFORE the COMMIT: {'stderr': [lines], 'stdout': [lines]}."""
    plan = {
        "run_id": run_id,
        "chart_id": CHART_ID,
        "asset_id": ASSET_ID,
        "triggered_by": TRIGGERED_BY,
        "plan_manifest_digest": manifest_digest,
        "plan_manifest": manifest,
        "existing_small_test_runs": existing,
        "admission_notes": notes,
    }
    skew = image_skew_notice(manifest)
    if dry_run:
        return {"stderr": [
            f"[dry-run] staged plan for a SMALL TEST build of {ASSET_ID} on chart "
            f"{CHART_ID} — ROLLED BACK, nothing written. Existing small-test runs of this chart: "
            f"{[(r['id'], r['state'], r['created_at']) for r in existing] or 'none'} (an attempted run after an unknown commit outcome "
            f"is looked up with --lookup <run id> or --list-runs, not with this dry run). A real dispatch prints a teardown deadline {RETENTION_DAYS} days out "
            f"(cockpit retention; {RUNBOOK}) and must be executed within {EXECUTE_WITHIN_MINUTES} minutes", *skew],
            "stdout": [json.dumps(plan, indent=2, sort_keys=True)]}
    if created_at is None:                           # cannot happen on a real insert; never fall back to the client clock
        raise RuntimeError("the INSERT returned no created_at, so no deadline can be derived from the database")
    execute_by = (created_at + datetime.timedelta(minutes=EXECUTE_WITHIN_MINUTES)).isoformat(timespec="seconds")
    deadline = (created_at + datetime.timedelta(days=RETENTION_DAYS)).isoformat(timespec="seconds")
    return {"stderr": [
        f"[dispatch] EXECUTE WITHIN {EXECUTE_WITHIN_MINUTES} MINUTES of the stored creation time {created_at.isoformat(timespec='seconds')}: "
        f"the cockpit watchdog fails a planned run that was never started after {EXECUTE_WITHIN_MINUTES} minutes (by {execute_by}); "
        f"launch the command below promptly or re-stage",
        f"[dispatch] TEARDOWN DEADLINE: tear the small test down by {deadline} ({RETENTION_DAYS} days after the stored creation time: the "
        f"cockpit watchdog then deletes the run row and its receipts lose their run link; the teardown refuses those for good — see {RUNBOOK})",
        *skew,
        f"[dispatch] staged v5 SMALL TEST build_run {run_id} for asset "
        f"{ASSET_ID} on chart {CHART_ID} (manifest digest {manifest_digest}); "
        f"asset_registry was not touched. Execute on steward go "
        f"via `gcloud run jobs execute brahma-build-pipeline-job "
        f"--args=--run-id,{run_id}`"],
        "stdout": [run_id]}


def _emit_report(report: dict) -> None:
    for line in report["stderr"]:
        print(line, file=sys.stderr)
    for line in report["stdout"]:
        print(line, flush=True)


def _safe_failure(exc: BaseException) -> str:
    """The class (and SQLSTATE) only — a connection or parse error can carry the credentials in its text — and what is KNOWN about the
    transaction, naming the attempted run. 'Unchanged' is claimed only when a rollback was confirmed."""
    kind = f"{type(exc).__module__}.{type(exc).__name__}"
    state = getattr(exc, "sqlstate", None)
    known = OUTCOME_TEXT.get(getattr(exc, "dispatch_outcome", None) or "unlabelled", OUTCOME_TEXT["unlabelled"])   # never defaults to a no-commit claim
    run = getattr(exc, "dispatch_run_id", None)
    return (f"dispatch failed: {kind}{f' (SQLSTATE {state})' if state else ''}. The exception text is withheld because a "
            f"connection error can carry credentials. {f'Attempted run id: {run}. ' if run else ''}{known}")


def cli(argv: list[str] | None = None) -> int:
    """The process boundary. `main` keeps raising its named refusals (RuntimeError: ids and counts only, never connection text);
    here a refusal is printed, and ANY other exception prints its class only."""
    try:
        main(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else (0 if exc.code is None else 1)
    except KeyboardInterrupt as exc:              # Codex round 5 (1): an interrupt is reported WITH the known transaction outcome
        print(_safe_failure(exc), file=sys.stderr)
        return 130
    except RuntimeError as exc:                   # the named refusals this script raises itself
        known = OUTCOME_TEXT.get(getattr(exc, "dispatch_outcome", None) or "", "")
        run = getattr(exc, "dispatch_run_id", None)
        print(f"dispatch refused: {exc}" + (f"\nAttempted run id: {run}" if run else "") + (f"\n{known}" if known else ""), file=sys.stderr)
        return 1
    except Exception as exc:                      # noqa: BLE001 — the boundary: print the class, never the text
        print(_safe_failure(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(cli())
