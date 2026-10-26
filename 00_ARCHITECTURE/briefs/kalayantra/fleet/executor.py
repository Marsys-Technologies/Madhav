#!/usr/bin/env python3
"""KĀLA-YANTRA fixed-operation executor v1.3 (charter §7; Amendment A8 §3.8–§3.11) — the ONLY process that holds a production credential.

What it trusts: nothing an agent can edit in a working tree. The operations table and every script it runs are read from
`origin/main` — i.e. only what was reviewed and merged:
  · the table            git show origin/main:00_ARCHITECTURE/briefs/kalayantra/fleet/executor_ops.json
  · a read-only op       its script is extracted from origin/main into run/ops/tmp/ and run from there
  · a production op      a private worktree at the request's `reviewed_commit` (which must be an ancestor of origin/main)
                         is created under $KY_ROOT/exec/, the mapped command runs there, the worktree is removed

Loop: read run/ops/requests/*.json → validate → (production: take the single production slot) → validate AGAIN immediately
before execution → run in its own process group → write run/ops/receipts/<operation_id>.json (redacted; the complete output
is the child's stdout alone, in <operation_id>.output.txt, and its stderr alone in <operation_id>.stderr.txt, each with its own sha256) → move the request to run/ops/done/.

Production approval binds the request (A8 §3.9): ONE verifier lane's acceptance receipt carries the sha256 of the request as
sorted compact JSON without the fields that may lawfully change after signing — `acceptance_receipt`, `expires_at` and any
`*_expires_at` lease-expiry field (see request_digest) — plus the attestation the kind needs: `dry_run_passed` for a mutating
kind (SR-A12-BACKUP-REMOVAL: a `*_teardown` no longer needs `backup_taken`; its dry run, exact scope and absence readback stay mandatory). It is valid from its timestamp until the request's `expires_at`; there is no age cap.
The lease must be the ONLY unexpired ACTIVE row of the shared lease table.

Mechanical acceptance of a production write (OWNER-MINIMAL-PROTECTION-NOW-20261018; SR-MINIMAL-PROTECTION §2): a request with NO `acceptance_receipt` but a
`pack_fill` may instead be accepted by this executor, without a signer, when ALL hold — (1) its bytes equal a VERIFIED pack fill (pack_fill_check: the pack
manifest is on run/ops/PACK_ALLOWLIST.json, which the cockpit writes only from an ACCEPTED verify job; the allow-list pins the template digest per kind; every fixed
field equals the template; no field the template does not define; the fill digest re-derives from the request bytes), (2) its kind's `<kind>_dryrun` COMPLETED OK for
the same request identity in THIS executor's own receipts (dry_run_check; `backup_snapshot` / `backup_restore_verify` have no dry-run kind and need none), (3) the
lease is live. It is recorded as acceptance/<operation_id>.json, by executor-mechanical, with the request digest and the evidence digests, and is re-measured
immediately before execution. NEVER mechanical: deletions (every `*_teardown`) and serving changes (publish_head, layer_publish, rollback_head, layer_rollback), and
measuring_cancel, century_cancel and verification_cancel (held with them): those keep requiring ONE verifier lane's acceptance exactly as above. A request that carries an `acceptance_receipt` is always judged by it. `*_dryrun` kinds are `production: false` — read-only
with a credential: no lease, acceptance or fence, but a merged `reviewed_commit` (they run in its tree) and a rollback proof in
the receipt.

The production slot is a FENCE file, run/ops/PRODUCTION_PENDING.json. Only a REMOTE-ASYNCHRONOUS kind takes it (A8 §3.11: the
table's `remote_async: true`, or a named dispatch / century / verification job) — written before the operation starts and
RETAINED afterwards — success, failure or interruption — because a dispatch returns while its remote job still runs. Only the
owner surrogate removes it, after the quiescence receipt for that request. Synchronous production kinds take no fence (the one
production worker serialises them); read-only operations are not fenced and run in parallel. A production operation in flight
at a restart is NEVER re-run: its receipt says INTERRUPTED, and the restart takes the fence for it. A read-only kind or a `*_dryrun` (`production: false`)
interrupted at a restart takes none; an unknown kind, an unreadable request or an unreadable table fences (W3W4 rehearsal D10). A refused executor refresh (HOLD, STOP, queued or in-flight work,
an unproven fence) is logged as REFRESH_REFUSED and recorded in run/ops/EXECUTOR_REFRESH.json; this snapshot keeps serving.
A child process receives an allow-listed environment plus, at most, the ONE connection its operation needs.

Scheduler pause (SR-J3-REAPER-PAUSE): `scheduler_pause` / `scheduler_resume` (+ `*_dryrun`) and the read-only `scheduler_readback` act on ONE Cloud
Scheduler job, the cockpit watchdog `watchdog-reaper`; every other job name is refused at admission and again in the reviewed script. A pause carries
`resume-by` (UTC, not after its lease's end) and is ARMED before it runs: a durable record under run/ops/scheduler_backstop/ that the loop honours on EVERY
tick — before the table, HOLD or sync gates, and on the first tick after a restart (an overdue record fires immediately). The executor then runs the
reviewed resume script itself, with no request, lease or signer: the signed pause already bound `resume-by`. A failed attempt backs off and retries until
the job reads ENABLED. A verified `scheduler_resume` satisfies (cancels) the armed records. Each scheduler receipt carries the state read back AFTER the action.

Measuring cancel (SR-J3-CANCEL-NULL 2(a)): `measuring_cancel` cancels ONE running Cloud Run execution of the measuring build and only when admission binds it
twice — the target execution must be the one named in the cited `measuring_dispatch` receipt (name + sha256, read back byte for byte) and an ABORT or stall
verdict file must be cited the same way and say so. The receipt carries the execution state read back after the cancel; anything but CANCELLED is FAILED.
Like a resume it is never held by the production fence (the dispatch it stops is what holds it). `measuring_cancel_dryrun` plans the calls and makes none.

The same admission, proof and fence rule serve `century_cancel` (the century build, item J-4e, its `century_dispatch` receipt) and `verification_cancel` (the
verification job `gochara-verification-job`, item J-5s, its `verification_job` receipt), each with a `*_dryrun` twin (CANCEL_FAMILIES). All three cancels are
SIGNED_ONLY: a stop is never mechanical.

Served probe (SR-TEARDOWN-AUTHORITY-GATE item 3): the read-only `served_probe` kind GETs ONE URL, chosen by NAME from the fixed `probe_endpoints` object of its table
entry (a name the table does not declare is refused at admission, before any process starts), sends no credential and follows no redirect, and records the HTTP
status, content type, byte length and sha256 of the body — the body itself only for an endpoint declared `store_body: true` and only if it carries no personal data.
A non-2xx answer, or a record that does not bind this operation, is a FAILED receipt; a 2xx one is accepted mechanically like `readback_sql` (fleet/served_probe.py).

Owner go (OWNER-BUILD-GO-REQUIRED-20261023): "before you start the actual build, take my explicit approval". `century_dispatch` and the production `orchestrator_rebuild`
(never their genuinely dry `*_dryrun` siblings, which stay free), and (SR-OWNER-GATE-HARDEN) ANY table row whose script / python_module is the century launcher
(century_launch.py) or the production rebuild entry (publication_admission with `rebuild` / `--force-execute`), whatever its kind is called, are refused at admission AND again
immediately before execution unless run/ops/owner_go/<operation_id>.json exists and binds THIS request. The owner surrogate writes it, only from the owner's own yes:
{"schema": "ky.owner_go/2", "operation_id", "kind", "item_id", "request_sha256" (the
executor's request_digest of the request: the same sha256 an acceptance binds), "reviewed_commit" (the dispatch head), "owner_yes": true, "owner_words" (verbatim),
"transcript_citation" (session + timestamp, non-empty), "written_by": "madhav-44 (owner surrogate)", "written_at" (timezone-qualified, not in the future), "expires_at" (REQUIRED, ISO-8601 with a timezone: after written_at, at most
12 hours after it, still in the future when the executor judges it — at admission and again before execution), and ONLY when the owner gave a longer window,
"owner_span_hours" (a number, then the longest written_at -> expires_at span) with "owner_span_words" (the owner's words, verbatim, non-empty)}. A symlink at the file or at any
directory below the run root on its path (run/ops, run/ops/owner_go) is refused. A cockpit pages on the refusal reasons `owner_go_missing` (no file) and
`owner_go_mismatch: <field>` (the file names a different request, or lacks a citation, the yes or the writer, is expired or has no valid expiry (`expires_at`), or sits behind
a symlink (`directory` / `file`)). Neither a surrogate
ruling, an earlier approval file (OWNER-CLOUD-RUNS-APPROVED), an environment flag, a lease, an acceptance receipt nor a capability replaces it; deleting the file stops a
queued build. Trials and dry runs need no go.

Century resume (SR-RESUME-NOW, ruling madhav-f9 lane 2; standing owner requirement OWNER-RESUMABLE-REQUIRED-20261025): `century_resume` continues a killed or failed century
build over the substeps the writer's ledger has committed, instead of a teardown and a fresh dispatch. It is modelled on `century_dispatch` — the builder principal, the same
remote-async production fence (REMOTE_ASYNC_KINDS), the century_contract_sha256 binding and the same launch evidence (ky.century_launch/1) — and differs in three things:
(1) it needs its OWN owner go (OWNER_GO_KINDS; a go names its kind and request, so a dispatch go never opens a resume, nor a resume go a dispatch);
(2) its absence gate admits a PARTLY present generation 5.0, and only a ledger-attested one (v5_small_test_shared.resume_evidence, loaded from the reviewed commit like the
dispatch's): the request cites the launch receipt it resumes (`resumes`, `resume_run_id`) and its `program_identity`, and an accepted readback of the ledger must show ONE program,
the request's, whose committed substeps all belong to the resumed lineage and account for exactly the rows present; `century_dispatch` keeps demanding every count zero and no
other kind reaches this gate; (3) the request's program_identity.writer_digest must equal the century contract's writer_source_digest at the reviewed commit, so a resume of
any other program refuses by name. `century_cancel` (+ its dry run) also cancels the execution a `century_resume` launched (CANCEL_FAMILIES `also_dispatch`).
The kind is ENABLED with its launcher mode (`century_launch.py --resume`, which starts the same Cloud Run job over the same staged century config and refuses a program identity
other than the contract's before anything is staged) and its staging-rollback twin `century_resume_dryrun` (platform/scripts/dispatch_v5_century_resume_job.py --dry-run: it stages
in a transaction that is rolled back, commits nothing, claims nothing and calls no cloud service; it needs no owner go). It stays fail-closed until the writer's ledger exists: the
absence gate above admits nothing without an accepted readback of that ledger. The twin makes the mechanical route available only to a request equal to a verified pack fill for
the kind (none exists today); a V lane's acceptance is otherwise required, besides the owner's go.

K9 rebuild staging (SR-PREP-LANES-1 (2), item K9-4b): `k9_rebuild_stage` creates, in production, the frozen build_runs row and the ONE open candidate that
`orchestrator_rebuild` requires (services.kala_core.rebuild_stage, an executor child under the builder DSN; nothing else in this table stages them). It is a production
write (lease, signer or pack-fill acceptance, its dry run `k9_rebuild_stage_dryrun`, which stages in a transaction it rolls back), it needs its OWN owner go (OWNER_GO_KINDS) and
it is admitted only with an accepted, fresh absence readback and exposure readback of the fixed queries in fleet/k9_stage_policy.py (`absence_readback`, `exposure_readback`).
It is neither a deletion nor a serving change, so it is not signed-only; the child refuses by name whatever already exists and never stages a second run or candidate.

Cancel lane (SR-CANCEL-LANE): every production cancel / stall-stop kind (CANCEL_LANE_KINDS, a closed allow-list) runs on its OWN single worker, never on the
production worker, and never waits for the production fence — a cancel queued behind the very operation it must stop would never run. The lane refuses any
kind that is not on the list, every one of them is signed-only, and `orchestrator_rebuild_cancel` is admitted only for the run-id of an `orchestrator_rebuild`
that is in flight.
"""
from __future__ import annotations
import concurrent.futures as cf, datetime as dt, fcntl, hashlib, json, os, pathlib, re, shutil, signal, subprocess, sys, tempfile, threading, time

KY_ROOT = pathlib.Path(os.environ.get("KY_ROOT", "/Users/Dev/kalayantra"))
GIT = pathlib.Path(os.environ.get("KY_SOURCE_REPO", "/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-campaign"))   # used ONLY as a handle on the shared object store (fetch / show / merge-base / worktree); the campaign checkout unless KY_SOURCE_REPO selects another
RUN = KY_ROOT / "run"; OPS = RUN / "ops"; EXEC = KY_ROOT / "exec"
REQ, REC, DONE, ACC, INFLIGHT, TMP = OPS / "requests", OPS / "receipts", OPS / "done", OPS / "acceptance", OPS / "inflight", OPS / "tmp"
FENCE = OPS / "PRODUCTION_PENDING.json"
OPS_PATH = "00_ARCHITECTURE/briefs/kalayantra/fleet/executor_ops.json"
COORD_PATH = "00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md"
CANONICAL_CHART = "482012f1-710e-4a25-994a-93821f5871aa"
PY = str(KY_ROOT / "venv" / "bin" / "python")
REDACT = [re.compile(r"postgres(?:ql)?://[^\s'\"]+", re.I), re.compile(r"(password|pgpassword|secret|token|apikey|api_key)\s*[=:]\s*\S+", re.I)]
SAFE_ID = re.compile(r"^[A-Za-z0-9_.-]{1,80}$"); SAFE_ARG = re.compile(r"^[A-Za-z0-9_.:,=/@+-]{1,300}$"); SHA = re.compile(r"^[0-9a-f]{7,40}$")
CHILD_ENV_ALLOW = {"HOME", "PATH", "LANG", "LC_ALL", "TZ", "TMPDIR", "USER", "LOGNAME", "CLOUDSDK_CONFIG", "GOOGLE_APPLICATION_CREDENTIALS"}
SEEN = OPS / "idempotency.jsonl"; MAX_TIMEOUT = 6 * 3600
UNBOUND_REQUEST_FIELDS = frozenset({"acceptance_receipt", "expires_at"})   # A8 §3.9: plus any `*_expires_at` field — see request_digest; mirrored by kyd_kinds_ops.request_digest and v5_small_test_shared.request_hash
# One element per line, sorted: a kind added by another PR is a one-line insertion that never touches a neighbour's line (SR-CHURN-CUT 5).
TEARDOWN_KINDS = (   # the committed teardowns that wait for an independent absence
    "century_teardown",
    "measuring_teardown",
    "smalltest_teardown",
)
LAUNCH_SCHEMAS = {"smalltest_dispatch": "ky.smalltest_launch/1", "measuring_dispatch": "ky.measuring_launch/1", "century_dispatch": "ky.century_launch/1", "century_resume": "ky.century_launch/1"}
RUN_OPERATION_KINDS = ("orchestrator_rebuild", "orchestrator_rebuild_cancel")      # the operations that act on a K9 rebuild run's writers
RAN_TO_AN_END = ("COMPLETED", "FAILED", "INTERRUPTED")      # receipt statuses of an operation whose child was started and has ended (INTERRUPTED: the executor restarted; the child may live on, so only the session readback proves it)
REMOTE_ASYNC_KINDS = frozenset({   # A8 §3.11: work continues remotely after the child returns — fenced even if a table drops `remote_async`
    "century_dispatch",
    "century_resume",
    "measuring_dispatch",
    "smalltest_dispatch",
    "verification_job",
})
OWNER_GO_KINDS = frozenset({   # OWNER-BUILD-GO-REQUIRED-20261023: the actual build starts only on the owner's explicit yes; the dry-run siblings stay free (SR-RESUME-NOW: a resume is a build too, with its OWN go)
    "century_dispatch",
    "century_resume",
    "k9_rebuild_stage",
    "orchestrator_rebuild",
})
OWNER_GO_DIR = OPS / "owner_go"   # run/ops/owner_go/<operation_id>.json, written only by the owner surrogate from the owner's own words
OWNER_GO_SCHEMA = "ky.owner_go/2"   # /2 (SR-OWNER-GATE-HARDEN) adds the required expires_at
OWNER_GO_DEFAULT_SPAN_HOURS = 12   # the longest written_at -> expires_at span, unless the file states a longer one the owner gave (owner_span_hours + owner_span_words)
OWNER_GO_SCRIPT_NAMES = frozenset({"century_launch.py"})   # SR-OWNER-GATE-HARDEN: the century build launcher is gated whatever the row's kind is called
OWNER_GO_REBUILD_MODULE = "publication_admission"          # ...and so is the production rebuild entry run with one of these tokens (never its `*-dryrun` verbs)
OWNER_GO_REBUILD_TOKENS = frozenset({"rebuild", "--force-execute"})
OWNER_GO_WRITER = "madhav-44 (owner surrogate)"
REFRESH = OPS / "EXECUTOR_REFRESH.json"
LOOP_TICK_S = 10        # the main loop's idle sleep: the finest grain at which any timed gate below can fire
CAPS_REFRESH_S = 30     # A10.1 item 6: CAPABILITIES.json is rewritten at least this often (was 300)
CAPS_FRESH_S = 45       # the freshness bound readers of CAPABILITIES.json apply (unchanged); a snapshot is at most CAPS_REFRESH_S + LOOP_TICK_S old
PACK_ALLOWLIST = OPS / "PACK_ALLOWLIST.json"   # OWNER-MINIMAL-PROTECTION-NOW: written by the cockpit ONLY from an ACCEPTED verify job of a pack; this executor only reads it
SIGNED_ONLY_KINDS = frozenset({   # serving changes, plus the deletion-adjacent cancels (every kind on CANCEL_LANE_KINDS, which a test keeps equal to this set's cancels); every `*_teardown` kind is signed-only too (see mechanical_exempt)
    "century_cancel",
    "layer_publish",
    "layer_rollback",
    "measuring_cancel",
    "orchestrator_rebuild_cancel",
    "publish_head",
    "rollback_head",
    "verification_cancel",
})
CANCEL_LANE_KINDS = frozenset({   # SR-CANCEL-LANE: a CLOSED allow-list (never a name-suffix match); a name with no table entry is simply never requested; tests/test_executor_cancel_lane.py keeps it complete against the table
    "century_cancel",
    "measuring_cancel",
    "orchestrator_rebuild_cancel",
    "verification_cancel",
})
FENCE_EXEMPT_KINDS = frozenset({   # the single production slot is taken: these still run — a resume of the watchdog is the safe direction and a cancel stops the very dispatch that holds the fence (every CANCEL_LANE_KINDS member plus scheduler_resume)
    "century_cancel",
    "measuring_cancel",
    "orchestrator_rebuild_cancel",
    "scheduler_resume",
    "verification_cancel",
})
CANCEL_FAMILIES = {"measuring": {"item": "J-3c", "dispatch": "measuring_dispatch", "schema": "ky.measuring_cancel/1", "job": "brahma-build-pipeline-job", "execution": r"brahma-build-pipeline-job-[a-z0-9]+(?:-[a-z0-9]+)*"}, "century": {"item": "J-4e", "dispatch": "century_dispatch", "also_dispatch": ("century_resume",), "schema": "ky.century_cancel/1", "job": "brahma-build-pipeline-job", "execution": r"brahma-build-pipeline-job-[a-z0-9]+(?:-[a-z0-9]+)*"}, "verification": {"item": "J-5s", "dispatch": "verification_job", "schema": "ky.verification_cancel/1", "job": "gochara-verification-job", "execution": r"gochara-verification-job-[a-z0-9]+(?:-[a-z0-9]+)*"}}   # per family: the request item, the dispatch kind whose receipt names the target (and `also_dispatch`, the kinds that launch the same job and may be cancelled the same way: SR-RESUME-NOW century_resume), the record schema the reviewed script prints, the Cloud Run job and its execution-name shape (the century build runs on the same job as the measuring build)
CANCEL_KINDS = {f"{family}_cancel{twin}": family for family in CANCEL_FAMILIES for twin in ("", "_dryrun")}
NO_DRYRUN_KINDS = frozenset({"backup_snapshot", "backup_restore_verify"})   # the two production kinds with no dry-run kind and no `dry_run_passed` attestation (kyd_kinds_ops.required_checks)
PACK_NEVER_FILLED = frozenset({"kind", "chart_id", "reviewed_commit", "requested_by", "acceptance_receipt", "pack_fill"})   # a pack template pins these (or the request cannot carry them); a fill may never set them
DRYRUN_IDENTITY_FIELDS = ("item_id", "chart_id", "reviewed_commit", "args")   # what "the same request" means between a `<kind>_dryrun` request and its production request
HEX64 = re.compile(r"^[0-9a-f]{64}$")
SCHEDULER_JOB = "watchdog-reaper"   # platform/scripts/provision_watchdog_scheduler.sh creates exactly this job ...
SCHEDULER_PROJECT = "madhav-astrology"   # ... in this project (GCP_PROJECT default) ...
SCHEDULER_REGION = "asia-south1"   # ... and this region (GCP_REGION default)
SCHEDULER_SCRIPT = "00_ARCHITECTURE/briefs/kalayantra/fleet/scheduler_reaper.py"   # the one reviewed script every scheduler kind (and the backstop) runs
SCHEDULER_ACTION = {"scheduler_readback": "readback", "scheduler_pause_dryrun": "pause", "scheduler_pause": "pause", "scheduler_resume_dryrun": "resume", "scheduler_resume": "resume"}
SCHEDULER_STATES = ("ENABLED", "PAUSED", "DISABLED", "UPDATE_FAILED")   # google.cloud.scheduler.v1.Job.State values a record may report
SCHEDULER_UTC = re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:Z|\+00:00)")
SCHEDULER_BACKSTOP = OPS / "scheduler_backstop"
PROBE_SCHEMA = "ky.served_probe/1"
CONSUMER_PROBE_KEY = "KY_CONSUMER_PROBE_KEY"   # J-6l-a61: the executor-held consumer credential; `execute` hands it to a `consumer_probe` child ONLY, under exactly this name
PROBE_SHA256 = re.compile(r"[0-9a-f]{64}")
_lock = threading.Lock()


def now() -> str: return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
def redact(s: str) -> str:
    for rx in REDACT: s = rx.sub("[REDACTED]", s)
    key = os.environ.get(CONSUMER_PROBE_KEY)
    return s.replace(key, "[REDACTED]") if key else s
def log(msg: str) -> None:
    with _lock, (KY_ROOT / "logs" / "executor.log").open("a") as f: f.write(f"{now()} {redact(msg)}\n")
def git(*args: str, timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(GIT), *args], capture_output=True, text=True, timeout=timeout)


def sync() -> None:
    if git("fetch", "-q", "origin", "main", "campaign-coordination").returncode:
        raise RuntimeError("cannot refresh the authoritative refs (origin/main, origin/campaign-coordination)")

def digest_bytes(body: bytes) -> str: return hashlib.sha256(body).hexdigest()
def running_revision() -> str:
    try: return digest_bytes(pathlib.Path(__file__).read_bytes())
    except OSError: return "unreadable"
def main_revision() -> str | None:
    p = git("rev-parse", "origin/main")
    return p.stdout.strip() if p.returncode == 0 and SHA.fullmatch(p.stdout.strip()) else None
def main_executor_source() -> bytes | None:
    p = git("show", f"origin/main:{OPS_PATH.rsplit('/', 1)[0]}/executor.py")
    return p.stdout.encode() if p.returncode == 0 else None

def load_table() -> dict | None:
    p = git("show", f"origin/main:{OPS_PATH}")
    if p.returncode != 0: return None
    try: return json.loads(p.stdout)["ops"]
    except Exception: return None

def capabilities_due(last_caps: float, now_s: float) -> bool:
    return now_s - last_caps >= CAPS_REFRESH_S


def capabilities(table_on_main: bool) -> dict:
    caps = {"builder": bool(os.environ.get("KY_BUILDER_DATABASE_URL")), "owner": bool(os.environ.get("KY_OWNER_DATABASE_URL")),
            "layer_verifier": bool(os.environ.get("KY_LAYER_VERIFIER_DATABASE_URL")),
            "consumer_reader": bool(os.environ.get(CONSUMER_PROBE_KEY)),
            "pgenv": pathlib.Path("/Users/Dev/.config/pravaha/pgenv.sh").exists(),
            "gcloud": subprocess.run(["gcloud", "auth", "list", "--format=value(account)"], capture_output=True, text=True).stdout.strip() != "",
            "none": True, "ops_table_on_main": table_on_main, "production_slot": "PENDING" if FENCE.exists() else "free",
            "executor_revision": running_revision(), "main_revision": main_revision(),
            "refresh_state": refresh_state(), "ts": now()}
    with _lock: (OPS / "CAPABILITIES.json").write_text(json.dumps(caps, indent=1))
    return caps


def refresh_refusal_reason() -> str | None:
    """Return the reason an executor handover must not begin, or ``None``.

    A refresh may only replace an idle executor.  This deliberately checks the
    durable operation state rather than a process name: a request in either
    queue can be active on a remote system, and a retained production fence is
    not proof that its request is quiescent.  The eventual operator-bound
    handover calls this predicate before it stops the current snapshot.
    """
    if (KY_ROOT / "HOLD").exists():
        return "HOLD set; executor refresh is refused"
    if (RUN / "STOP_executor").exists():
        return "STOP_executor set; executor refresh is refused"
    if any(REQ.glob("*.json")):
        return "pending operation request; executor refresh is refused"
    if any(INFLIGHT.glob("*.json")):
        return "in-flight operation; executor refresh is refused"
    if FENCE.exists() and not fence_quiescent():
        return "production fence retained without request-bound quiescence evidence; executor refresh is refused"
    return None

def fence_quiescent() -> bool:
    """A retained fence may survive a safe handover, but only with V's bound receipt.

    The fence itself remains intact.  This merely distinguishes the explicitly
    terminal request it names from an unproven remote operation.
    """
    try:
        fence = json.loads(FENCE.read_text())
        operation_id = str(fence["operation_id"])
        request_sha256 = fence["request_sha256"]
        proof = json.loads((ACC / f"{operation_id}.quiescence.json").read_text())
    except (OSError, KeyError, TypeError, json.JSONDecodeError):
        return False
    accepted = (isinstance(request_sha256, str) and re.fullmatch(r"[0-9a-f]{64}", request_sha256) is not None
            and proof.get("operation_id") == operation_id and proof.get("request_sha256") == request_sha256
            and proof.get("result") == "ACCEPTED"
            and proof.get("by") in ("v1", "v2", "v3", "v4", "executor-mechanical") and bool(proof.get("ts")))
    if accepted and proof.get("by") == "executor-mechanical":      # A7 D-44: only the executor's own measured record, with every check true
        accepted = (proof.get("schema") == "ky.mechanical_quiescence/1" and isinstance(proof.get("checks"), dict)
                    and bool(proof["checks"]) and all(value is True for value in proof["checks"].values()))
    if not accepted:
        return False
    try:
        commit_bytes = (REC / f"{operation_id}.json").read_bytes()
        committed = json.loads(commit_bytes)
        if committed.get("operation_id") != operation_id or committed.get("request_sha256") != request_sha256:
            return False
        if committed.get("kind") in TEARDOWN_KINDS:
            policy = smalltest_policy(committed)
            observed = policy["absence_evidence"](proof, OPS, teardown_receipt=committed)
            completion = dict(schema=f"ky.{committed['kind'].split('_')[0]}_completion/1", status="COMPLETED", operation_id=operation_id,
                request_sha256=request_sha256, reviewed_commit=committed["reviewed_commit"],
                commit_receipt_sha256=digest_bytes(commit_bytes), run_id=observed["run_id"],
                scope_sha256=observed["scope_sha256"], rowset_sha256=observed["rowset_sha256"],
                absence_receipt=proof["absence_receipt"], absence_acceptance=proof["absence_acceptance"])
            # The commit receipt remains immutable: absence binds its digest.
            # Publish completion separately only after the independent detector.
            path = REC / f"{operation_id}.completion.json"
            with _lock:
                staged = path.with_suffix(".json.tmp")
                with staged.open("w") as stream:
                    stream.write(json.dumps(completion, indent=1))
                    stream.flush(); os.fsync(stream.fileno())
                os.replace(staged, path)
    except Exception:
        return False
    return True

def publish_teardown_completions() -> None:
    """SR-TEARDOWN-COMPLETION: publish <op>.completion.json for a COMMITTED teardown receipt (status AWAITING_ABSENCE) once an ACCEPTED absence
    receipt (acceptance/<absence op>.absence.json) binds its digest. The verdict is the reviewed policy's own absence_evidence, the very check
    fence_quiescent runs, and the document is the one fence_quiescent writes; but no fence and no quiescence record is involved: this reads and
    writes receipts only and never touches FENCE. A receipt or candidate the check refuses is skipped; nothing is published for it."""
    candidates = sorted(ACC.glob("*.absence.json"))
    if not candidates: return
    for path in sorted(REC.glob("*.json")):
        if path.name.endswith(".completion.json") or (REC / f"{path.stem}.completion.json").exists(): continue
        try:
            commit_bytes = path.read_bytes()
            committed = json.loads(commit_bytes)
            if (committed.get("kind") not in TEARDOWN_KINDS or committed.get("status") != "AWAITING_ABSENCE"
                    or committed.get("operation_id") != path.stem): continue
            policy = smalltest_policy(committed)
            for accepted in candidates:
                absence = REC / f"{accepted.name[:-len('.absence.json')]}.json"
                if absence == path: continue
                proof = {"absence_receipt": {"name": absence.name, "sha256": digest_bytes(absence.read_bytes())},
                         "absence_acceptance": {"name": accepted.name, "sha256": digest_bytes(accepted.read_bytes())}}
                try: observed = policy["absence_evidence"](proof, OPS, teardown_receipt=committed)
                except Exception: continue
                completion = dict(schema=f"ky.{committed['kind'].split('_')[0]}_completion/1", status="COMPLETED", operation_id=committed["operation_id"],
                    request_sha256=committed["request_sha256"], reviewed_commit=committed["reviewed_commit"],
                    commit_receipt_sha256=digest_bytes(commit_bytes), run_id=observed["run_id"],
                    scope_sha256=observed["scope_sha256"], rowset_sha256=observed["rowset_sha256"],
                    absence_receipt=proof["absence_receipt"], absence_acceptance=proof["absence_acceptance"])
                target = REC / f"{path.stem}.completion.json"
                with _lock:
                    staged = target.with_suffix(".json.tmp")
                    with staged.open("w") as stream:
                        stream.write(json.dumps(completion, indent=1))
                        stream.flush(); os.fsync(stream.fileno())
                    os.replace(staged, target)
                log(f"{path.stem} teardown completion published (absence {absence.stem})")
                break
        except Exception: continue


def publish_head_completions() -> None:
    """M-W56-16: the head twin of publish_teardown_completions. Publish <op>.completion.json (schema ky.head_completion/1) for a COMMITTED
    publish_head / rollback_head receipt (status AWAITING_READBACK) once the filing convention is met (fleet/OPS_CONTRACT.md "Head completion filing"):
    the archived head request done/<op>.json, an acceptance acceptance/<op>.readback.json naming `readback_operation_id`, and that readback's archived
    request done/<rb>.json, receipt receipts/<rb>.json and output receipts/<rb>.output.txt. The verdict is the reviewed policy's own `complete`
    (head_operation.complete, loaded from the request's reviewed_commit like head_policy, never the working tree); for a rollback the policy's
    request_problem is re-run too, so its `rollback_of` must still bind the original publish. Receipts only: never FENCE, never a request, never the
    executor reading or requesting the readback itself. A receipt the policy refuses is skipped (no document, no exception); an existing document is never rewritten."""
    for path in sorted(REC.glob("*.json")):
        if path.name.endswith(".completion.json") or (REC / f"{path.stem}.completion.json").exists(): continue
        try:
            commit_raw = path.read_bytes()
            committed = json.loads(commit_raw)
            if (committed.get("kind") not in ("publish_head", "rollback_head") or committed.get("status") != "AWAITING_READBACK"
                    or committed.get("operation_id") != path.stem): continue
            accepted_path = ACC / f"{path.stem}.readback.json"
            if not accepted_path.exists(): continue
            accepted_raw = accepted_path.read_bytes()
            accepted = json.loads(accepted_raw)
            readback_op = accepted.get("readback_operation_id")
            if not isinstance(readback_op, str) or not SAFE_ID.fullmatch(readback_op) or readback_op == path.stem: continue
            req = json.loads((DONE / f"{path.stem}.json").read_bytes())
            rb_req = json.loads((DONE / f"{readback_op}.json").read_bytes())
            if rb_req.get("requested_by") == req.get("requested_by"): continue      # S-5: the readback is a v-lane's, never the head requester's
            rb_raw = (REC / f"{readback_op}.json").read_bytes()
            output_raw = (REC / f"{readback_op}.output.txt").read_bytes()
            policy = head_policy(req)
            if req.get("kind") == "rollback_head" and policy["request_problem"](req, OPS): continue
            completion = dict(policy["complete"](req, commit_raw, rb_req, rb_raw, output_raw, accepted), schema="ky.head_completion/1",
                readback_operation_id=readback_op,
                source_digests=dict(commit_receipt=digest_bytes(commit_raw), readback_receipt=digest_bytes(rb_raw), acceptance=digest_bytes(accepted_raw)))
        except Exception: continue
        target = REC / f"{path.stem}.completion.json"
        with _lock:
            staged = target.with_suffix(".json.tmp")
            with staged.open("w") as stream:
                stream.write(json.dumps(completion, indent=1))
                stream.flush(); os.fsync(stream.fileno())
            os.replace(staged, target)
        log(f"{path.stem} head completion published (readback {readback_op})")


def refresh_state() -> str:
    try: return str(json.loads(REFRESH.read_text()).get("result", "UNKNOWN"))
    except (OSError, json.JSONDecodeError): return "UNKNOWN"

def handover_from_main() -> str | None:
    """Stage and atomically replace this credential-bearing snapshot from main.

    Return ``None`` when already current or when a safe replacement is staged;
    otherwise return a fail-closed reason.  The caller execs only after the
    source is compiled and the replacement digest is durably recorded.
    """
    source = main_executor_source()
    commit = main_revision()
    if source is None or commit is None:
        return "merged-main executor source or revision unreadable"
    chosen = digest_bytes(source)
    if chosen == running_revision():
        return None
    why = refresh_refusal_reason()
    if why:
        return why
    try:
        compile(source, "origin/main executor.py", "exec")
        staged = EXEC / "executor.py.next"
        staged.write_bytes(source)
        if digest_bytes(staged.read_bytes()) != chosen:
            return "staged executor digest mismatch"
        os.replace(staged, EXEC / "executor.py")
        REFRESH.write_text(json.dumps({"result": "STAGED", "main_revision": commit,
                                       "executor_revision": chosen, "ts": now()}, indent=1))
    except (OSError, SyntaxError) as e:
        return f"replacement staging failed: {type(e).__name__}"
    return None

def refresh_from_main_or_fail_closed() -> bool:
    """Refresh this snapshot; true when the running revision is proven current, false when the refresh was refused.

    A changed source is atomically staged and then exec'd in this same
    credential-bearing process.  A refused or unprovable refresh is what fails
    closed — the handover does not happen — and it is logged as
    ``REFRESH_REFUSED <reason>`` and recorded in EXECUTOR_REFRESH.json.  It
    does NOT close admission (A8 §5): a merged executor change plus a queued
    request must not stop all operations; the current reviewed snapshot keeps
    serving until it is idle and the handover can proceed.
    """
    before = running_revision()
    why = handover_from_main()
    if why:
        REFRESH.write_text(json.dumps({"result": "REFUSED", "reason": why, "ts": now()}, indent=1))
        log(f"REFRESH_REFUSED {why}")
        return False
    if running_revision() != before:
        os.execv(PY, [PY, str(EXEC / "executor.py")])
    source = main_executor_source()
    commit = main_revision()
    if source is None or commit is None or digest_bytes(source) != running_revision():
        REFRESH.write_text(json.dumps({"result": "REFUSED", "reason": "running revision cannot be proven current", "ts": now()}, indent=1))
        log("REFRESH_REFUSED running revision cannot be proven current")
        return False
    REFRESH.write_text(json.dumps({"result": "ACTIVE", "main_revision": commit,
                                   "executor_revision": running_revision(), "ts": now()}, indent=1))
    return True

def seen(key: str) -> bool:
    if not SEEN.exists(): return False
    return any(json.loads(l).get("key") == key for l in SEEN.read_text().splitlines() if l.strip())
def mark_seen(key: str, op: str) -> None:
    with _lock, SEEN.open("a") as f: f.write(json.dumps({"key": key, "op": op, "ts": now()}) + "\n")


def lease_live(lease_id: str) -> bool:
    """True only when `lease_id` is the ONE unexpired ACTIVE row of §1 of the shared lease table (the prime rule: one campaign
    deploys or builds at a time). An ACTIVE row past its stated expiry is dead; an unreadable expiry fails closed."""
    if not SAFE_ID.fullmatch(lease_id): return False
    if git("fetch", "-q", "origin", "campaign-coordination").returncode: return False
    p = git("show", f"origin/campaign-coordination:{COORD_PATH}", timeout=30)
    if p.returncode: return False
    section = p.stdout.split("## 1.", 1)
    if len(section) != 2: return False
    section = section[1].split("## 2.", 1)[0]
    active = []; ist = dt.timezone(dt.timedelta(hours=5, minutes=30))
    for line in section.splitlines():
        if not line.startswith("|"): continue
        cells = [s.strip() for s in line.strip().strip("|").split("|")]
        if len(cells) != 6: continue
        if not re.match(r"^ACTIVE(?:\s|$)", cells[5].replace("*", "").strip()): continue
        try: expiry = dt.datetime.strptime(cells[4][:16], "%Y-%m-%d %H:%M").replace(tzinfo=ist)
        except ValueError: return False
        if expiry > dt.datetime.now(dt.timezone.utc): active.append(cells[0].replace("*", "").strip())
    return active == [lease_id]

def request_digest(req: dict) -> str:
    """The sha256 an acceptance binds (A8 §3.9): the request as sorted compact JSON without the fields that may lawfully change after
    signing — `acceptance_receipt`, `expires_at` and any `*_expires_at` lease-expiry field — so a lease renewal or an expiry extension never
    voids an acceptance. operation_id, kind, item_id, args, reviewed_commit, chart_id, lease_id and every other field stay bound. Mirrored byte
    for byte by kyd_kinds_ops.request_digest (the signer) and platform/scripts/v5_small_test_shared.request_hash (the children check their own binding)."""
    bound = {k: v for k, v in req.items() if k not in UNBOUND_REQUEST_FIELDS and not k.endswith("_expires_at")}
    return hashlib.sha256(json.dumps(bound, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def utc_time(value: str) -> dt.datetime:
    parsed = dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None: raise ValueError("timezone required")
    return parsed.astimezone(dt.timezone.utc)


def lease_expiry(lease_id: str) -> dt.datetime | None:
    """The stated expiry (UTC) of the ACTIVE row `lease_id` in §1 of the shared lease table, read exactly as lease_live reads it; None when
    the table, the row or its expiry cannot be read (a bound that cannot be measured is not a bound)."""
    p = git("show", f"origin/campaign-coordination:{COORD_PATH}", timeout=30)
    if p.returncode: return None
    section = p.stdout.split("## 1.", 1)
    if len(section) != 2: return None
    ist = dt.timezone(dt.timedelta(hours=5, minutes=30))
    for line in section[1].split("## 2.", 1)[0].splitlines():
        if not line.startswith("|"): continue
        cells = [s.strip() for s in line.strip().strip("|").split("|")]
        if len(cells) != 6 or cells[0].replace("*", "").strip() != lease_id: continue
        if not re.match(r"^ACTIVE(?:\s|$)", cells[5].replace("*", "").strip()): continue
        try: return dt.datetime.strptime(cells[4][:16], "%Y-%m-%d %H:%M").replace(tzinfo=ist).astimezone(dt.timezone.utc)
        except ValueError: return None
    return None


def canonical_sha(value) -> str:
    """sha256 of `value` as sorted compact JSON — the digest every pack and dry-run comparison below uses."""
    return digest_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def mechanical_exempt(kind: str) -> bool:
    """OWNER-MINIMAL-PROTECTION-NOW: deletions (every `*_teardown`) and serving changes (publish / rollback of a head or layer) never go mechanical; they keep
    requiring a V1 signer's acceptance exactly as before. `measuring_cancel`, `century_cancel` and `verification_cancel` are held with them (I): none removes data itself, but
    each is the first step of the cancel-then-teardown path the owner named, and a cancelled execution cannot be resumed."""
    return kind.endswith("_teardown") or kind in SIGNED_ONLY_KINDS


def pack_fill_check(req: dict) -> tuple[str | None, dict]:
    """(problem, evidence): do the request's bytes equal a VERIFIED pack fill? A request carries
        pack_fill = {pack_manifest_sha256, template: {kind, fixed: {field: value}, fill: [field names]}, fill_sha256}
    and is a pack fill iff ALL of: the pack manifest digest is on run/ops/PACK_ALLOWLIST.json with verdict ACCEPTED and a verify_job (the cockpit writes an entry
    only from an ACCEPTED verify job); that entry lists sha256(template) for exactly this kind; the template never fills kind, chart_id, reviewed_commit,
    requested_by or an approval field (so the request, which must carry them, has them pinned); every `fixed` field of the request equals the template's value (type-strict); the request has no field the template does
    not define (the clocks `expires_at` / `*_expires_at` excepted); and fill_sha256 equals the digest the executor re-derives from the request's own filled fields."""
    pf = req.get("pack_fill")
    if not (isinstance(pf, dict) and set(pf) == {"pack_manifest_sha256", "template", "fill_sha256"}):
        return "pack_fill must carry exactly pack_manifest_sha256, template and fill_sha256", {}
    manifest, template, declared = pf["pack_manifest_sha256"], pf["template"], pf["fill_sha256"]
    if not (isinstance(manifest, str) and HEX64.fullmatch(manifest) and isinstance(declared, str) and HEX64.fullmatch(declared)):
        return "pack_fill digests must be 64 lowercase hex characters", {}
    try: listing = json.loads(PACK_ALLOWLIST.read_text())
    except (OSError, ValueError): return "the verified-pack allow-list is missing or unreadable", {}
    packs = listing.get("packs") if isinstance(listing, dict) and listing.get("schema") == "ky.pack_allowlist/1" else None
    entry = next((p for p in packs if isinstance(p, dict) and p.get("pack_manifest_sha256") == manifest), None) if isinstance(packs, list) else None
    if entry is None or entry.get("verdict") != "ACCEPTED" or not entry.get("verify_job"):
        return "the pack manifest is not on the verified-pack allow-list", {}
    templates = entry.get("templates"); template_sha = canonical_sha(template)
    if not (isinstance(templates, dict) and templates.get(template_sha) == req.get("kind")):
        return "the pack template is not one the verified pack lists for this kind", {}
    if not (isinstance(template, dict) and set(template) == {"kind", "fixed", "fill"} and template["kind"] == req.get("kind")
            and isinstance(template["fixed"], dict) and isinstance(template["fill"], list) and all(isinstance(n, str) for n in template["fill"])):
        return "the pack template is malformed", {}
    fixed, fill = template["fixed"], template["fill"]
    if set(fill) & PACK_NEVER_FILLED: return "the pack template may not fill kind, chart_id, reviewed_commit, requested_by or an approval field", {}
    clock = lambda k: k in UNBOUND_REQUEST_FIELDS or k.endswith("_expires_at")
    extra = sorted(k for k in req if k != "pack_fill" and not clock(k) and k not in fixed and k not in fill)
    if extra: return f"the request carries fields the pack template does not define: {extra}", {}
    for k, v in fixed.items():
        if not clock(k) and (k not in req or canonical_sha(req[k]) != canonical_sha(v)):
            return f"the request differs from the verified pack template at fixed field {k}", {}
    if canonical_sha({k: req[k] for k in sorted(fill) if k in req and not clock(k)}) != declared:
        return "fill_sha256 does not equal the digest re-derived from the request bytes", {}
    return None, {"pack_manifest_sha256": manifest, "template_sha256": template_sha, "fill_sha256": declared, "verify_job": entry["verify_job"]}


def dry_run_check(req: dict, table: dict) -> tuple[str | None, dict | None]:
    """(problem, evidence): did this kind's `<kind>_dryrun` COMPLETE OK for the same request identity? The executor reads ITS OWN receipt
    (run/ops/receipts, cited by `dryrun_receipt` {name, sha256}) and the archived dry-run request — never a signer's attestation. Same identity = the
    dry-run request and this one agree on DRYRUN_IDENTITY_FIELDS, and the receipt binds that archived request (digest) and its complete output (digest).
    The two kinds with no dry-run kind need none (evidence None)."""
    kind = req["kind"]
    if kind in NO_DRYRUN_KINDS: return None, None
    dry_kind = kind + "_dryrun"; entry = table.get(dry_kind) or {}
    if not entry.get("enabled") or entry.get("production") is not False:
        return f"kind {kind} has no enabled read-only dry-run kind ({dry_kind}), so it needs a V1 signer", None
    ref = req.get("dryrun_receipt")
    if not (isinstance(ref, dict) and set(ref) == {"name", "sha256"} and isinstance(ref["name"], str) and re.fullmatch(r"[A-Za-z0-9_.-]{1,80}\.json", ref["name"])
            and isinstance(ref["sha256"], str) and HEX64.fullmatch(ref["sha256"])):
        return "dryrun_receipt {name, sha256} citing this kind's completed dry run is required", None
    try:
        path = REC / ref["name"]
        if path.resolve().parent != REC.resolve(): return "the dry-run receipt reference escapes the receipts directory", None
        body = path.read_bytes()
        if digest_bytes(body) != ref["sha256"]: return "the dry-run receipt differs from its cited sha256", None
        rec = json.loads(body); dry_oid = rec["operation_id"]
        if not (isinstance(dry_oid, str) and SAFE_ID.fullmatch(dry_oid) and ref["name"] == dry_oid + ".json"): return "the dry-run receipt does not name its own operation", None
        output = (REC / f"{dry_oid}.output.txt").read_bytes()
        archived = json.loads((DONE / f"{dry_oid}.json").read_text())
        ok = (isinstance(rec, dict) and rec.get("kind") == dry_kind and rec.get("status") == "COMPLETED" and type(rec.get("exit_code")) is int and rec["exit_code"] == 0
              and "lane_target" not in rec and digest_bytes(output) == rec.get("output_sha256")
              and isinstance(archived, dict) and archived.get("operation_id") == dry_oid and archived.get("kind") == dry_kind and "lane_target" not in archived
              and request_digest(archived) == rec.get("request_sha256")
              and rec.get("reviewed_commit") == archived.get("reviewed_commit") == req.get("reviewed_commit")
              and all(canonical_sha(archived.get(f)) == canonical_sha(req.get(f)) for f in DRYRUN_IDENTITY_FIELDS))
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return "the dry-run receipt, its output or its archived request cannot be read", None
    if not ok: return "the dry run did not COMPLETE OK (exit 0, complete output, bound archived request) for this request's identity", None
    return None, {"operation_id": dry_oid, "kind": dry_kind, "receipt_sha256": ref["sha256"], "request_sha256": rec["request_sha256"], "output_sha256": rec["output_sha256"]}


def mechanical_problem(req: dict, table: dict) -> tuple[str | None, dict]:
    """(problem, evidence) for the MECHANICAL route to a production write: not a deletion or serving change, merged reviewed_commit, unexpired request,
    request bytes equal a verified pack fill, this kind's dry run completed OK for the same identity. (The lease is checked by validate and again by
    mechanical_pre_acceptance.) Pure reads — nothing is written."""
    kind = req["kind"]
    if mechanical_exempt(kind): return f"kind {kind} is a deletion or serving change: it needs a V1 signer's acceptance, never a mechanical one", {}
    rc = str(req.get("reviewed_commit", ""))
    if not SHA.match(rc): return "reviewed_commit required for a production operation", {}
    if git("merge-base", "--is-ancestor", rc, "origin/main").returncode != 0: return "reviewed_commit is not merged to main", {}
    try:
        if not dt.datetime.now(dt.timezone.utc) < utc_time(req["expires_at"]): return "approval expired or not yet valid", {}
    except (KeyError, TypeError, ValueError): return "valid approval timestamp and a timezone-qualified request expires_at required", {}
    why, pack = pack_fill_check(req)
    if why: return why, {}
    why, dry = dry_run_check(req, table)
    if why: return why, {}
    return None, {"pack": pack, "dry_run": dry}


def mechanical_pre_acceptance(req: dict, table: dict) -> str | None:
    """OWNER-MINIMAL-PROTECTION-NOW: accept a production write MECHANICALLY (instead of a V1 signer) when mechanical_problem finds nothing and the lease is
    live, and record it as acceptance/<operation_id>.json — schema ky.mechanical_acceptance/1, phase pre, by executor-mechanical, the request digest and the
    evidence digests. Returns None when the request is accepted, else the reason. Idempotent: the same request finds its own record; a different record for
    the operation id refuses. validate calls this on admission AND again immediately before execution; nothing it recorded is trusted without re-measuring."""
    problem, evidence = mechanical_problem(req, table)
    if problem: return problem
    lease = lease_live(str(req.get("lease_id", "")))
    if not lease: return "lease is not the single unexpired ACTIVE row on origin/campaign-coordination"
    checks = {"kind_is_not_a_deletion_or_serving_change": True, "reviewed_commit_merged": True, "request_equals_verified_pack_fill": True, "lease_live": lease is True}
    checks["dry_run_completed_ok_for_same_identity" if evidence["dry_run"] else "dry_run_not_applicable_to_kind"] = True
    digest = request_digest(req)
    document = {"schema": "ky.mechanical_acceptance/1", "phase": "pre", "by": "executor-mechanical", "result": "ACCEPTED", "operation_id": req["operation_id"],
                "kind": req["kind"], "request_sha256": digest, "reviewed_commit": req["reviewed_commit"], "lease_id": req["lease_id"], "checks": checks,
                "evidence": evidence, "ts": now()}
    path = ACC / f"{req['operation_id']}.json"
    if write_new_json(path, document): return None
    try: existing = json.loads(path.read_text())
    except (OSError, ValueError): existing = None
    if isinstance(existing, dict) and existing.get("by") == "executor-mechanical" and existing.get("result") == "ACCEPTED" and existing.get("request_sha256") == digest: return None
    return "an acceptance record for this operation already exists and does not bind this request"


def scheduler_policy_problem(req: dict) -> str | None:
    """SR-J3-REAPER-PAUSE admission rules for the scheduler kinds, run at the tail of validate (so again immediately before execution): the job
    is on the allow-list, and a pause names a UTC `resume-by` in the future that is not after the end of its lease."""
    kind = req.get("kind")
    if kind not in SCHEDULER_ACTION: return None
    args = req.get("args") or {}
    if args.get("job", SCHEDULER_JOB) != SCHEDULER_JOB: return f"scheduler job is not on the allow-list (only {SCHEDULER_JOB})"
    if SCHEDULER_ACTION[kind] != "pause": return None
    stamp = args.get("resume-by")
    if not stamp: return "a scheduler pause requires resume-by (the UTC time the watchdog is resumed whatever happens)"
    if not SCHEDULER_UTC.fullmatch(str(stamp)): return "resume-by must be a UTC timestamp YYYY-MM-DDTHH:MM:SS followed by Z or +00:00"
    due = utc_time(stamp)
    if due <= dt.datetime.now(dt.timezone.utc): return "resume-by is not in the future"
    if kind == "scheduler_pause" or req.get("lease_id"):       # the dry run has no lease of its own; when it names one, the same bound applies
        end = lease_expiry(str(req.get("lease_id", "")))
        if end is None: return "the lease end cannot be read, so resume-by cannot be bounded by it"
        if due > end: return "resume-by is after the end of the lease"
    return None


def scheduler_proof(req: dict, rc: int | None, out: str) -> tuple[dict | None, str | None]:
    """(record, problem) for a scheduler kind's complete output. `record` is the ONE ky.scheduler_job/1 line when it names this operation, this
    request digest, this action and exactly the allow-listed project / region / job (else None); `problem` is None only when its status and the
    state read back after the action are what the kind promises. An exit status alone proves nothing."""
    kind = str(req.get("kind")); action = SCHEDULER_ACTION.get(kind)
    found = []
    for line in out.splitlines():
        try: value = json.loads(line)
        except ValueError: continue
        if isinstance(value, dict) and value.get("schema") == "ky.scheduler_job/1": found.append(value)
    if action is None or len(found) != 1: return None, "scheduler record missing or not unique"
    rec = found[0]
    if (rec.get("action") != action or rec.get("dry_run") is not kind.endswith("_dryrun")
            or (rec.get("project"), rec.get("region"), rec.get("job")) != (SCHEDULER_PROJECT, SCHEDULER_REGION, SCHEDULER_JOB)
            or rec.get("operation_id") != req.get("operation_id") or rec.get("request_sha256") != request_digest(req)):
        return None, "scheduler record does not bind this operation, request, action and allow-listed job"
    state = rec.get("state")
    if kind.endswith("_dryrun"):
        kept = rec.get("status") == "DRY_RUN" and rec.get("gcloud_calls") == 0 and state is None and rec.get("changed") is False
    elif action == "readback":
        kept = (rec.get("status") == "MEASURED" and state in SCHEDULER_STATES) or (rec.get("status") == "PARTIAL" and state is None)
    else:
        kept = rec.get("status") == "OK" and state == {"pause": "PAUSED", "resume": "ENABLED"}[action]
    if rc == 0 and not kept: return rec, "scheduler record does not prove the promised status and the state read back after the action"
    return rec, None


def scheduler_write(path: pathlib.Path, document: dict) -> None:
    """Durable replace: temp file, fsync, rename — a crash leaves the old record or the new one, never half of either."""
    pending = path.with_name("." + path.name + ".tmp")
    with pending.open("w") as stream:
        stream.write(json.dumps(document, indent=1)); stream.flush(); os.fsync(stream.fileno())
    os.replace(pending, path)


def scheduler_backstop_records() -> list[tuple[pathlib.Path, dict]]:
    found = []
    for path in sorted(SCHEDULER_BACKSTOP.glob("*.json")):
        try: record = json.loads(path.read_text())
        except (OSError, ValueError):
            noted = scheduler_backstop_records.__dict__.setdefault("noted", set())
            if path.name not in noted: noted.add(path.name); log(f"BACKSTOP_UNREADABLE {path.name}: skipped, read it")
            continue
        if isinstance(record, dict) and record.get("schema") == "ky.scheduler_backstop/1": found.append((path, record))
    return found


def arm_scheduler_backstop(req: dict) -> dict:
    """Write the durable resume record of a scheduler_pause BEFORE the pause runs, so a pause that fails half-way or is interrupted leaves a
    harmless (idempotent) resume behind — never a pause nobody will undo. Refuses (so the pause does not run) if the record cannot be made."""
    stamp = (req.get("args") or {}).get("resume-by"); commit = str(req.get("reviewed_commit", ""))
    if not (isinstance(stamp, str) and SCHEDULER_UTC.fullmatch(stamp)): raise ValueError("backstop not armed: resume-by missing or not UTC")
    if not SHA.fullmatch(commit) or git("cat-file", "-e", f"{commit}:{SCHEDULER_SCRIPT}").returncode:
        raise ValueError("backstop not armed: the resume script does not exist at the reviewed commit")
    record = {"schema": "ky.scheduler_backstop/1", "status": "ARMED", "operation_id": req["operation_id"], "request_sha256": request_digest(req),
              "item_id": req.get("item_id"), "kyd": req.get("kyd"), "job": SCHEDULER_JOB, "resume_by": utc_time(stamp).isoformat(timespec="seconds"),
              "lease_id": req.get("lease_id"), "reviewed_commit": commit, "attempts": 0, "armed_at": now()}
    SCHEDULER_BACKSTOP.mkdir(parents=True, exist_ok=True)
    scheduler_write(SCHEDULER_BACKSTOP / f"{req['operation_id']}.json", record)
    log(f"{req['operation_id']} scheduler backstop armed: resume {SCHEDULER_JOB} at {record['resume_by']}")
    return record


def scheduler_backstop_satisfy(req: dict) -> int:
    """A scheduler_resume whose read-back state was ENABLED has done what every armed record would do: cancel them (keeping the evidence)."""
    count = 0
    for path, record in scheduler_backstop_records():
        if record.get("status") == "ARMED" and record.get("job") == SCHEDULER_JOB:
            scheduler_write(path, dict(record, status="SATISFIED", satisfied_by=req["operation_id"], satisfied_at=now())); count += 1
    return count


def scheduler_backstop_fire(path: pathlib.Path, record: dict, at: dt.datetime) -> bool:
    """Run the reviewed resume script itself — no request queue, lease or signer; the signed pause already bound resume-by — from the commit the
    pause named, and write a receipt. FIRED only if the state read back is ENABLED; otherwise the record stays ARMED with a back-off."""
    try: attempt = int(record.get("attempts", 0)) + 1
    except (TypeError, ValueError): attempt = 1
    oid = "bs-" + hashlib.sha256(str(record.get("operation_id")).encode()).hexdigest()[:12] + f"-{attempt}"
    commit = str(record.get("reviewed_commit", ""))
    req = {"operation_id": oid, "kind": "scheduler_resume", "item_id": str(record.get("item_id") or "unknown"), "idempotency_key": oid,
           "requested_by": "executor-backstop", "kyd": str(record.get("kyd") or "backstop"), "reviewed_commit": commit,
           "args": {"job": SCHEDULER_JOB}, "backstop_for": record.get("operation_id")}
    rc, out, err = 127, "", ""
    try:
        if not SHA.fullmatch(commit) or git("merge-base", "--is-ancestor", commit, "origin/main").returncode: raise ValueError("reviewed commit is not merged")
        source = git("show", f"{commit}:{SCHEDULER_SCRIPT}")
        if source.returncode: raise ValueError("resume script unreadable at the reviewed commit")
        script = TMP / f"{oid}.scheduler_reaper.py"; script.write_text(source.stdout)
        env = {k: v for k, v in os.environ.items() if k in CHILD_ENV_ALLOW}
        env["KY_OPERATION_REQUEST"] = json.dumps(req, sort_keys=True, separators=(",", ":")); env["KY_ROOT"] = str(KY_ROOT)
        try: p = run_group([PY, str(script), "--action", "resume", "--job", SCHEDULER_JOB], KY_ROOT, env, 600); rc, out, err = p.returncode, p.stdout or "", p.stderr or ""
        finally: script.unlink(missing_ok=True)
    except Exception as e: out = f"backstop could not run: {type(e).__name__}: {redact(str(e))}"
    proof, problem = scheduler_proof(req, rc, out)
    ok = rc == 0 and problem is None and proof is not None and proof.get("state") == "ENABLED"
    receipt(req, "COMPLETED" if ok else "FAILED", "" if ok else (problem or "backstop resume did not read back ENABLED"), rc, out,
            {"scheduler": proof, "backstop_for": record.get("operation_id"), "attempt": attempt}, err)
    update = dict(record, attempts=attempt, last_attempt_at=now(), last_receipt=oid)
    if ok: update.update(status="FIRED", fired_at=now())
    else: update["next_attempt_at"] = (at + dt.timedelta(seconds=min(900, 30 * 2 ** (attempt - 1)))).isoformat(timespec="seconds")
    scheduler_write(path, update)
    log(f"{record.get('operation_id')} scheduler backstop {'FIRED' if ok else 'FAILED, will retry'} ({oid})")
    return ok


def scheduler_backstop_tick(at: dt.datetime | None = None) -> list[str]:
    """Honour every ARMED record whose resume-by has passed (or whose back-off has elapsed). Called on every loop turn BEFORE the sync, table and
    HOLD gates, and so on the first turn after a restart: a record that fell due while the executor was down fires immediately. An unreadable
    due time counts as overdue — resuming the watchdog is idempotent and the safe direction. Returns the operation ids it fired."""
    at = at or dt.datetime.now(dt.timezone.utc); fired = []
    for path, record in scheduler_backstop_records():
        if record.get("status") != "ARMED": continue
        try:
            if at < utc_time(record["resume_by"]) or at < utc_time(record.get("next_attempt_at") or record["resume_by"]): continue
        except (KeyError, TypeError, ValueError): pass
        try:
            if scheduler_backstop_fire(path, record, at): fired.append(str(record.get("operation_id")))
        except Exception as e: log(f"{record.get('operation_id')} scheduler backstop error: {type(e).__name__}: {redact(str(e))}")      # never stops the loop; the record stays ARMED
    return fired


def century_contract_problem(req: dict) -> str | None:
    """SR-EDGES-PROOF 2 / SR-HORIZON-PUBLIC: a century dispatch and its dry run are bound to the committed launch contract (fleet/century_contract.json: horizon, classes, policy,
    cap, timeout, image binding). The request carries `century_contract_sha256`; it is admitted only when that equals the sha256 of the file's bytes AT the request's reviewed_commit
    (read with git show, never from a working tree), the file is a ky.century_contract/1, and its launch_args are exactly the request's args. Run at the tail of validate, so again
    immediately before execution. The pack fill pins the field in its template, so a fill bound to a different contract is refused here, whatever its other fields say."""
    if req.get("kind") not in ("century_dispatch", "century_dispatch_dryrun", "century_resume", "century_resume_dryrun"): return None
    declared, rc = req.get("century_contract_sha256"), str(req.get("reviewed_commit", ""))
    if not (isinstance(declared, str) and HEX64.fullmatch(declared)): return "century_contract_sha256 (64 lowercase hex) is required: a century dispatch binds to the committed century contract"
    if not SHA.match(rc): return "reviewed_commit required to read the century contract"
    shown = git("show", f"{rc}:00_ARCHITECTURE/briefs/kalayantra/fleet/century_contract.json")
    if shown.returncode or not getattr(shown, "stdout", ""): return "the century contract is not at the reviewed commit"
    body = shown.stdout.encode("utf-8")
    if digest_bytes(body) != declared: return "century_contract_sha256 does not equal the sha256 of fleet/century_contract.json at the reviewed commit"
    try: contract = json.loads(body)
    except ValueError: return "the century contract at the reviewed commit is not JSON"
    if not isinstance(contract, dict) or contract.get("schema") != "ky.century_contract/1": return "the century contract at the reviewed commit is not a ky.century_contract/1"
    if contract.get("launch_args") != (req.get("args") or {}): return "the request args differ from the century contract's launch_args"
    if req.get("kind") in ("century_resume", "century_resume_dryrun"):      # SR-RESUME-NOW: the program the resume would run is the one the ledger was written by, or it refuses by name (the ledger's side is judged in v5_small_test_shared.resume_evidence)
        identity = req.get("program_identity")
        if not isinstance(identity, dict) or identity.get("writer_digest") != (contract.get("image") or {}).get("writer_source_digest"):
            return "program_identity.writer_digest differs from the century contract's writer_source_digest at the reviewed commit: a resume continues only the same program"
    return None


def owner_go_gated(req: dict, op: dict | None) -> bool:
    """SR-OWNER-GATE-HARDEN: whether the owner's go binds this request. A kind in OWNER_GO_KINDS, OR any table row whose script / python_module is the century build launcher
    (OWNER_GO_SCRIPT_NAMES), OR whose script / python_module is the production rebuild entry (publication_admission) run with the `rebuild` verb or `--force-execute`
    (its fixed_args, or a request arg named like it) — whatever the kind is called, a `*_dryrun` name included: a row is dry by what it runs, never by its name."""
    if req.get("kind") in OWNER_GO_KINDS: return True
    op = op or {}
    names = {pathlib.PurePosixPath(str(op.get("script") or "")).name, str(op.get("python_module") or "").rsplit(".", 1)[-1] + ".py"}
    if names & OWNER_GO_SCRIPT_NAMES: return True
    if OWNER_GO_REBUILD_MODULE + ".py" in names:
        tokens = [str(a) for a in op.get("fixed_args", [])] + [f"--{k}" for k in (req.get("args") or {})]
        return any(t in OWNER_GO_REBUILD_TOKENS for t in tokens)
    return False


def owner_go_problem(req: dict, op: dict | None = None) -> str | None:
    """OWNER-BUILD-GO-REQUIRED-20261023: the owner's explicit go for the actual build. The century dispatch and the production K9 rebuild (OWNER_GO_KINDS, and any row that runs
    their scripts: owner_go_gated; never a genuinely dry sibling) are admitted only when run/ops/owner_go/<operation_id>.json exists and binds THIS request: schema, operation_id,
    kind, item_id, the executor's own request_digest (`request_sha256`) and the dispatch head (`reviewed_commit`) all equal the request's, `owner_yes` is true, `owner_words` and
    `transcript_citation` (session + timestamp) are non-empty, `written_by` is the owner surrogate, `written_at` is a timezone-qualified time not in the future, and `expires_at`
    (SR-OWNER-GATE-HARDEN) is a timezone-qualified time still ahead, after written_at and at most OWNER_GO_DEFAULT_SPAN_HOURS after it (or the longer `owner_span_hours` the file
    states together with the owner's `owner_span_words`). No component of the path below the run root (the file, run/ops/owner_go, run/ops) may be a symlink. Run at the tail of
    validate, so again immediately before execution (removing the file, or its expiry, stops a queued build). The reasons the cockpit pages on are `owner_go_missing` and
    `owner_go_mismatch: <field>`. No surrogate ruling, earlier approval file, environment flag or capability substitutes."""
    if not owner_go_gated(req, op): return None
    path = OWNER_GO_DIR / f"{req.get('operation_id')}.json"
    root = RUN if RUN in path.parents else OWNER_GO_DIR.parent
    directory = path.parent
    while directory != root and directory != directory.parent:
        if directory.is_symlink(): return "owner_go_mismatch: directory"
        directory = directory.parent
    if not path.exists() and not path.is_symlink(): return "owner_go_missing"
    try:
        if path.is_symlink() or not path.is_file(): return "owner_go_mismatch: file"
        go = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError): return "owner_go_mismatch: file"
    if not isinstance(go, dict): return "owner_go_mismatch: file"
    for field, expected in (("schema", OWNER_GO_SCHEMA), ("operation_id", req.get("operation_id")), ("kind", req.get("kind")), ("item_id", req.get("item_id")),
                            ("request_sha256", request_digest(req)), ("reviewed_commit", req.get("reviewed_commit")), ("written_by", OWNER_GO_WRITER)):
        if not isinstance(expected, str) or not expected or go.get(field) != expected: return f"owner_go_mismatch: {field}"
    if go.get("owner_yes") is not True: return "owner_go_mismatch: owner_yes"
    for field in ("owner_words", "transcript_citation"):
        if not isinstance(go.get(field), str) or not go[field].strip(): return f"owner_go_mismatch: {field}"
    now = dt.datetime.now(dt.timezone.utc)
    try: written = utc_time(go.get("written_at"))
    except (TypeError, ValueError): return "owner_go_mismatch: written_at"
    if written > now + dt.timedelta(minutes=5): return "owner_go_mismatch: written_at"
    try: expires = utc_time(go.get("expires_at")) if isinstance(go.get("expires_at"), str) else None
    except ValueError: expires = None
    if expires is None: return "owner_go_mismatch: expires_at"
    span = OWNER_GO_DEFAULT_SPAN_HOURS
    if "owner_span_hours" in go:
        hours = go["owner_span_hours"]
        if type(hours) not in (int, float) or not 0 < hours <= 8760 or not isinstance(go.get("owner_span_words"), str) or not go["owner_span_words"].strip():
            return "owner_go_mismatch: owner_span_hours"
        span = max(span, hours)
    if expires <= written or expires - written > dt.timedelta(hours=span) or expires <= now: return "owner_go_mismatch: expires_at"
    return None


def measuring_cancel_problem(req: dict) -> str | None:
    """SR-J3-CANCEL-NULL 2(a) admission for a cancel kind (`measuring_cancel`, `century_cancel`, `verification_cancel` and their `*_dryrun` twins), run at the tail of
    validate (so again immediately before execution; the name is the J-3c one, the rule is family-aware since W3W4 verify E1): the target execution is the one the family's dispatch receipt named (measuring_dispatch J-3c, century_dispatch J-4e,
    verification_job J-5s), and an ABORT / stall verdict is cited; both are cited by file name + sha256 and read back byte for byte from run/ops/receipts and
    run/ops/verdicts. A missing or altered file, a different execution, another family's receipt, CONTINUE and NULL all refuse."""
    family = CANCEL_KINDS.get(req.get("kind"))
    if family is None: return None
    spec = CANCEL_FAMILIES[family]; dispatch_kind = spec["dispatch"]
    target = (req.get("args") or {}).get("execution")
    if not (isinstance(target, str) and re.fullmatch(spec["execution"], target)): return f"execution must be a {spec['job']} execution name"
    if req.get("item_id") != spec["item"]: return f"{family} cancel belongs to {spec['item']}"
    def cited(folder: str, ref) -> dict | None:
        if not (isinstance(ref, dict) and re.fullmatch(r"[A-Za-z0-9_.-]+\.json", str(ref.get("name", "")))): return None
        path = OPS / folder / ref["name"]
        try:
            if path.resolve().parent != (OPS / folder).resolve(): return None
            body = path.read_bytes(); value = json.loads(body)
        except (OSError, ValueError): return None
        return value if isinstance(value, dict) and digest_bytes(body) == ref.get("sha256") else None
    dispatch = cited("receipts", req.get("dispatch_receipt"))
    if dispatch is None: return f"the cited {dispatch_kind} receipt is missing, unreadable or does not match its sha256"
    launch = dispatch.get("launch") if isinstance(dispatch.get("launch"), dict) else {}
    if (dispatch.get("kind") not in (dispatch_kind, *spec.get("also_dispatch", ())) or dispatch.get("status") != "COMPLETED" or dispatch.get("exit_code") != 0 or dispatch.get("item_id") != spec["item"]
            or req["dispatch_receipt"]["name"] != f"{dispatch.get('operation_id')}.json" or launch.get("status") != "LAUNCHED"):
        return f"the cited receipt is not the COMPLETED launch of a {spec['item']} {' or '.join((dispatch_kind, *spec.get('also_dispatch', ())))}"
    if launch.get("execution_name") != target: return f"the target execution is not the execution named in the cited {dispatch_kind} receipt"
    verdict = cited("verdicts", req.get("verdict"))
    if verdict is None: return "the cited ABORT/stall verdict file is missing, unreadable or does not match its sha256"
    form = re.fullmatch(r"ky\.(reproject|stall)_verdict/\d+", str(verdict.get("schema")))
    if not form or verdict.get("verdict") != {"reproject": "ABORT", "stall": "STALL"}[form.group(1)]: return "the cited verdict is not an ABORT or stall verdict (CONTINUE and NULL never cancel)"
    return None


def orchestrator_rebuild_cancel_problem(req: dict) -> str | None:
    """SR-CANCEL-LANE admission for `orchestrator_rebuild_cancel` (and its dry run), run at the tail of validate (so again immediately before execution): the
    run-id must be the run-id of an `orchestrator_rebuild` request that is in flight (accepted, not yet finished) right now. A cancel of a run nothing is
    running, or of another run, refuses; an unreadable in-flight entry binds nothing."""
    if req.get("kind") not in ("orchestrator_rebuild_cancel", "orchestrator_rebuild_cancel_dryrun"): return None
    run_id = (req.get("args") or {}).get("run-id")
    if not (isinstance(run_id, str) and SAFE_ID.fullmatch(run_id)): return "run-id required: the run of the orchestrator_rebuild to cancel"
    for path in sorted(INFLIGHT.glob("*.json")):
        try: running = json.loads(path.read_text())
        except (OSError, ValueError): continue
        if (isinstance(running, dict) and running.get("kind") == "orchestrator_rebuild" and running.get("operation_id") != req.get("operation_id")
                and isinstance(running.get("args"), dict) and running["args"].get("run-id") == run_id): return None
    return "the target run-id is not the run of an orchestrator_rebuild in flight"


def writer_absence_problem(rebuild: dict) -> str | None:
    """None only when an ACCEPTED quiescence_check of this rebuild shows, measured AFTER the rebuild's terminal receipt, that no database session carries the rebuild's
    PGAPPNAME marker (every connection the rebuild's writers open carries it, see execute()) and that the readback could see every role's sessions. A readback taken
    while a writer still ran lists its session and does not count: the run row reading `stopped` proves nothing about the writer thread (Round A N10)."""
    op = str(rebuild["operation_id"]); marker = session_marker(op)
    if rebuild.get("session_marker") not in (None, marker): return f"the receipt of {op} names a different session marker than its operation id derives"
    try: ended = utc_time(rebuild["ts"])
    except (KeyError, TypeError, ValueError): return f"the receipt of {op} has no readable terminal time"
    for path in sorted(DONE.glob("*.json")):
        try:
            check = json.loads(path.read_text()); got = accepted_readback(str(check["operation_id"]), "quiescence_check")
            if got is None or check.get("kind") != "quiescence_check" or (check.get("args") or {}).get("operation") != op: continue
            lines = [json.loads(line) for line in got[1].decode().splitlines() if line.startswith("{")]
            found = [v for v in lines if isinstance(v, dict) and v.get("schema") == "ky.session_readback/1"]
            seen = found[0] if len(found) == 1 else {}
            if (seen.get("status") == "MEASURED" and seen.get("marker") == marker and seen.get("sees_all_sessions") is True
                    and seen.get("sessions") == [] and utc_time(seen["measured_at"]) >= ended): return None
        except (OSError, ValueError, KeyError, TypeError, AttributeError): continue
    return (f"no accepted session readback of {op} taken after it ended shows zero live sessions carrying its marker {marker}: "
            "file a quiescence_check for it once the rebuild has ended")


def orchestrator_rebuild_teardown_problem(req: dict) -> str | None:
    """Round A N10 (deletion safety; SR-K9-RESONANCE-MAP, N10 part) admission for `orchestrator_rebuild_teardown` and its dry run, run at the tail of validate (so again
    immediately before execution): a teardown is admitted only when (1) no orchestrator_rebuild or orchestrator_rebuild_cancel of the run-id is in flight, (2) every
    one of them that was started has a TERMINAL receipt (a cancel's run row reads `stopped` seconds before its writer thread ends; the rebuild's own receipt is written
    only when its process has ended), (3) at least one orchestrator_rebuild of the run-id was started, and (4) each of those has proof of process absence
    (writer_absence_problem). The run's state in the database is never consulted: it is the very signal that can read `stopped` beside a live writer. The absence
    readback of a deletion therefore runs after all of this, because the teardown cannot start before it holds."""
    if req.get("kind") not in ("orchestrator_rebuild_teardown", "orchestrator_rebuild_teardown_dryrun"): return None
    run_id = (req.get("args") or {}).get("run-id")
    if not (isinstance(run_id, str) and SAFE_ID.fullmatch(run_id)): return "run-id required: the run of the orchestrator_rebuild to tear down"
    named = []
    for folder in (INFLIGHT, DONE):
        for path in sorted(folder.glob("*.json")):
            try: other = json.loads(path.read_text())
            except (OSError, ValueError):
                if folder is INFLIGHT: return f"an unreadable in-flight entry ({path.name}) is unproven quiet: the run's writer cannot be shown to have ended"
                continue
            if not (isinstance(other, dict) and other.get("kind") in RUN_OPERATION_KINDS and isinstance(other.get("args"), dict) and other["args"].get("run-id") == run_id): continue
            if folder is INFLIGHT: return f"{other['kind']} {other.get('operation_id')} of this run is still in flight: a teardown never starts beside a live writer"
            named.append(other)
    started = []
    for other in named:
        op = str(other.get("operation_id"))
        try: record = json.loads((REC / f"{op}.json").read_text())
        except (OSError, ValueError): return f"the receipt of {other['kind']} {op} is unreadable: its end is not proven"
        if not (isinstance(record, dict) and record.get("operation_id") == op and record.get("kind") == other["kind"]): return f"the receipt of {other['kind']} {op} does not bind it"
        if record.get("status") == "REFUSED": continue      # refused before its child was started: nothing ran
        if record.get("status") not in RAN_TO_AN_END: return f"{other['kind']} {op} has no terminal receipt (status {record.get('status')}): the cancelled writer may still be running"
        started.append(record)
    rebuilds = [r for r in started if r["kind"] == "orchestrator_rebuild"]
    if not rebuilds: return "no started orchestrator_rebuild of this run-id has a terminal receipt: the run's writer is not shown to have ended"
    for rebuild in rebuilds:
        why = writer_absence_problem(rebuild)
        if why: return why
    return None


def orchestrator_rebuild_dryrun_problem(req: dict, table: dict) -> str | None:
    """SR-K9-PUBLISHABLE D7 (N.8) admission for the production `orchestrator_rebuild`, run at the tail of validate (so on BOTH routes, signed or mechanical):
    the request is admitted only if THIS executor's own receipt shows a COMPLETED `orchestrator_rebuild_dryrun` for the same identity (dry_run_check). A signer's
    `dry_run_passed` attestation alone never admits it: that attestation has no detector behind it for this kind (the dry run reports a null by design)."""
    if req.get("kind") != "orchestrator_rebuild": return None
    return dry_run_check(req, table)[0]


def measuring_cancel_proof(req: dict, rc: int | None, out: str) -> tuple[dict | None, str | None]:
    """(record, problem) for a cancel kind's (or its dry run's) complete output. `record` is the ONE ky.<family>_cancel/1 line when it names this
    operation, this request digest, this kind and exactly the targeted execution of the family's job (else None); `problem` is None only when the state
    read back after the action is CANCELLED (a dry run: when it planned and called nothing). An exit status alone proves nothing, and any other observed
    state is a failure whatever the exit status."""
    spec = CANCEL_FAMILIES[CANCEL_KINDS[req.get("kind")]]
    dry = str(req.get("kind")).endswith("_dryrun"); found = []
    for line in out.splitlines():
        try: value = json.loads(line)
        except ValueError: continue
        if isinstance(value, dict) and value.get("schema") == spec["schema"]: found.append(value)
    if len(found) != 1: return None, "cancel record missing or not unique"
    rec = found[0]       # the project / region below are cloudrun_readback.py's constants; the job is the family's
    if (rec.get("execution") != (req.get("args") or {}).get("execution") or (rec.get("project"), rec.get("region"), rec.get("job")) != ("madhav-astrology", "asia-south1", spec["job"])
            or rec.get("operation_id") != req.get("operation_id") or rec.get("request_sha256") != request_digest(req) or rec.get("dry_run") is not dry):
        return None, "cancel record does not bind this operation, request and targeted execution"
    if dry:
        if rc == 0 and not (rec.get("status") == "DRY_RUN" and rec.get("gcloud_calls") == 0 and rec.get("state") is None and rec.get("changed") is False):
            return rec, "the dry-run record does not prove a plan with no external call"
    elif rc == 0 and not (rec.get("status") == "OK" and rec.get("state") == "CANCELLED"):
        return rec, f"the execution was not read back CANCELLED (observed state: {rec.get('state')})"
    return rec, None


def served_probe_problem(req: dict, op: dict) -> str | None:
    """SR-TEARDOWN-AUTHORITY-GATE admission for `served_probe`, run at the tail of validate (so again immediately before execution): the endpoint NAME must
    be a key of the fixed `probe_endpoints` object in the kind's own table entry. A request carries no URL, so there is nothing else to check."""
    if req.get("kind") != "served_probe": return None
    declared = op.get("probe_endpoints")
    name = (req.get("args") or {}).get("endpoint")
    if not (isinstance(declared, dict) and isinstance(name, str) and name in declared): return "endpoint is not on the served-probe allow-list in the operation table"
    return None


def served_probe_proof(req: dict, op: dict, rc: int | None, out: str) -> tuple[dict | None, str | None]:
    """(record, problem) for a `served_probe`'s complete output. `record` is the ONE ky.served_probe/1 line when it names this operation, this request
    digest and a declared endpoint with exactly its declared URL (else None); `problem` is None only when the answer was 2xx, the digest and length are
    present, a stored body matches that digest and length, and a body is stored only where the table says it may be. An exit status alone proves nothing."""
    found = []
    for line in out.splitlines():
        try: value = json.loads(line)
        except ValueError: continue
        if isinstance(value, dict) and value.get("schema") == PROBE_SCHEMA: found.append(value)
    if len(found) != 1: return None, "probe record missing or not unique"
    rec = found[0]
    declared = (op.get("probe_endpoints") or {}).get((req.get("args") or {}).get("endpoint")) or {}
    if (not declared or rec.get("endpoint") != (req.get("args") or {}).get("endpoint") or rec.get("url") != declared.get("url") or rec.get("method") != "GET"
            or rec.get("operation_id") != req.get("operation_id") or rec.get("request_sha256") != request_digest(req)):
        return None, "probe record does not bind this operation, request and declared endpoint"
    code = rec.get("http_status")
    if rc == 0 and rec.get("status") != "OK": return rec, f"probe record status is {rec.get('status')}, not OK"
    if not (type(code) is int and 200 <= code < 300):
        return rec, f"the served response is HTTP {code}, not 2xx" if type(code) is int else str(rec.get("reason") or "no HTTP status was read")
    length, digest, body = rec.get("body_bytes"), rec.get("body_sha256"), rec.get("body")
    if not (type(length) is int and length >= 0 and isinstance(digest, str) and PROBE_SHA256.fullmatch(digest)): return rec, "probe record lacks the body length and sha256"
    if rec.get("credentials_sent") is not False: return rec, "probe record does not state that no credential was sent"
    if body is not None:
        if declared.get("store_body") is not True: return rec, "a body was stored for an endpoint declared digest-only"
        raw = body.encode() if isinstance(body, str) else b""
        if not isinstance(body, str) or len(raw) != length or hashlib.sha256(raw).hexdigest() != digest: return rec, "the stored body does not match its recorded length and sha256"
    return rec, None


def consumer_probe_proof(req: dict, rc: int | None, out: str, stderr: str = "") -> tuple[dict | None, str | None]:
    """(record, problem) for a `consumer_probe`'s complete output (J-6l-a61). `record` is the ONE ky.consumer_probe/1 line when it names this operation, this request
    digest and the requested probe id (else None); `problem` is None only when the record is MEASURED with HTTP 200, states `credentials_sent: true` (the header was
    sent) and `credential_echoed: false`, carries its body digest and length, and neither stdout nor stderr contains the credential itself. An exit status alone proves nothing."""
    key = os.environ.get(CONSUMER_PROBE_KEY)
    if key and (key in out or key in stderr): return None, "the credential appears in the probe's output"
    found = []
    for line in out.splitlines():
        try: value = json.loads(line)
        except ValueError: continue
        if isinstance(value, dict) and value.get("schema") == "ky.consumer_probe/1": found.append(value)
    if len(found) != 1: return None, "consumer probe record missing or not unique"
    rec = found[0]
    if (rec.get("probe") != (req.get("args") or {}).get("probe") or rec.get("operation_id") != req.get("operation_id") or rec.get("request_sha256") != request_digest(req)):
        return None, "consumer probe record does not bind this operation, request and probe"
    if rec.get("credential_echoed") is not False: return rec, "probe record does not state that the credential was not echoed"
    if rec.get("status") != "MEASURED": return rec, f"probe record status is {rec.get('status')}, not MEASURED"
    if rec.get("credentials_sent") is not True: return rec, "probe record does not state that the credential was sent in the header"
    code, length, digest = rec.get("http_status"), rec.get("body_bytes"), rec.get("body_sha256")
    if not (type(code) is int and code == 200): return rec, f"the consumer path answered HTTP {code}, not 200"
    if not (type(length) is int and length >= 0 and isinstance(digest, str) and HEX64.fullmatch(digest)): return rec, "probe record lacks the body length and sha256"
    if "body" in rec: return rec, "probe record carries a body"
    return rec, None


def receipt(req: dict, status: str, reason: str = "", rc: int | None = None, out: str | None = None, extra: dict | None = None, stderr: str = "", *, preserve_existing: bool = False) -> None:
    """SR-EXECUTOR-FRAMING: `out` is the child's stdout alone and `stderr` its stderr alone; the executor adds no byte of its own to either. A proof is
    parsed from `out` only (a child may lawfully print advisory lines on stderr). `<op>.output.txt` holds stdout exactly (after redaction) and
    `<op>.stderr.txt` stderr, each with its own sha256/bytes. A receipt made before this change has one combined `output_file` (stdout, "\\n", stderr)
    and no stderr_* fields; it still verifies, because every reader checks the file against `output_sha256` only. `out=None` means nothing ran."""
    name = req.get("operation_id") if SAFE_ID.match(str(req.get("operation_id", ""))) else "unknown"
    r = {"operation_id": req.get("operation_id"), "kind": req.get("kind"), "item_id": req.get("item_id"), "status": status, "reason": reason,
         "exit_code": rc, "stdout_tail": redact((out or "")[-20000:]), "ts": now(), "reviewed_commit": req.get("reviewed_commit"),
         "requested_by": req.get("requested_by"), "kyd": req.get("kyd"), "request_sha256": request_digest(req) if req.get("kind") else None}
    if stderr: r["stderr_tail"] = redact(stderr[-4000:])
    out = out or ""
    receipt_path = REC / f"{name}.json"
    separate_refusal = preserve_existing and status == "REFUSED" and receipt_path.exists()
    if separate_refusal:
        import uuid
        # A rejected request must not replace evidence retained for readback or rollback,
        # even when it is refused before the enabled-kind / request-policy checks.
        r["preserved_receipt"] = {"path": str(receipt_path), "sha256": digest_bytes(receipt_path.read_bytes())}
        refusal_dir = REC / "refusals"
        refusal_dir.mkdir(exist_ok=True)
        receipt_path = refusal_dir / f"{name}.{uuid.uuid4().hex}.json"
    if lane_selected(req):
        receipt_lane(req, r, status, rc, out)
    if out:                                           # the complete output is evidence; the tail alone must never be mistaken for it
        body = redact(out).encode(); output_path = receipt_path.with_suffix(".output.txt"); output_path.write_bytes(body)
        r["output_file"] = str(output_path); r["output_sha256"] = hashlib.sha256(body).hexdigest(); r["output_bytes"] = len(body)
    if stderr:
        body = redact(stderr).encode(); stderr_path = receipt_path.with_suffix(".stderr.txt"); stderr_path.write_bytes(body)
        r["stderr_file"] = str(stderr_path); r["stderr_sha256"] = hashlib.sha256(body).hexdigest(); r["stderr_bytes"] = len(body)
    if req.get("kind") == "measuring_dispatch_dryrun" and status == "COMPLETED":
        try:
            proof = json.loads(out)                               # `out` is stdout alone: the advisory lines on stderr are evidence, never part of the proof
            manifest = proof.get("plan_manifest") or {}
            valid = (rc == 0 and proof.get("schema") == "ky.measuring_staging/1"
                and proof.get("status") == "ROLLED_BACK" and proof.get("rollback_confirmed") is True
                and proof.get("operation_id") == req["operation_id"] and proof.get("request_sha256") == request_digest(req)
                and proof.get("args") == req.get("args") and manifest.get("chart_id") == CANONICAL_CHART
                and manifest.get("scope_target") == "ka_gochara_v5"
                and (manifest.get("gochara_v5_test_slice") or {}).get("run") == "all_classes_full"
                and proof.get("plan_manifest_digest") == digest_bytes(json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()))
        except (ValueError, TypeError, AttributeError):
            valid = False
        if valid:
            r["staging"] = proof
        else:
            r.update(status="FAILED", reason="bound measuring staging rollback proof missing; reconcile transaction outcome")
    if req.get("kind") in ("century_dispatch_dryrun", "century_resume_dryrun") and status == "COMPLETED":
        try:
            proof = json.loads(out)
            manifest = proof.get("plan_manifest") or {}
            valid = (rc == 0 and proof.get("schema") == "ky.century_staging/1"
                and proof.get("status") == "ROLLED_BACK" and proof.get("rollback_confirmed") is True
                and proof.get("operation_id") == req["operation_id"] and proof.get("request_sha256") == request_digest(req)
                and proof.get("args") == req.get("args") and manifest.get("chart_id") == CANONICAL_CHART
                and manifest.get("scope_target") == "ka_gochara_v5"
                and proof.get("triggered_by") == "gochara-v5-century" and "gochara_v5_test_slice" not in manifest    # a century run carries NO slice marker
                and proof.get("plan_manifest_digest") == digest_bytes(json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode())
                and (req["kind"] != "century_resume_dryrun"      # SR-RESUME-NOW: a resume's rollback proof names the run, receipt and program it was staged for, the request's own
                     or proof.get("resume") == {"resumes": (req.get("resumes") or {}).get("name"), "resume_run_id": req.get("resume_run_id"), "program_identity": req.get("program_identity")}))
        except (ValueError, TypeError, AttributeError):
            valid = False
        if valid:
            r["staging"] = proof
        else:
            r.update(status="FAILED", reason="bound century staging rollback proof missing; reconcile transaction outcome")
    if not lane_selected(req) and req.get("kind") in ("smalltest_dispatch", "measuring_dispatch", "century_dispatch", "century_resume") and status == "COMPLETED":
        # A staging UUID/exit zero is never launch evidence. Only the reviewed
        # wrapper's machine record binds the exact run and remote execution.
        records = []
        for line in out.splitlines():
            try:
                value = json.loads(line)
            except (ValueError, TypeError):
                continue
            if isinstance(value, dict) and value.get("schema") == LAUNCH_SCHEMAS[req["kind"]]:
                records.append(value)
        launch = records[0] if len(records) == 1 else {}
        if (rc == 0 and launch.get("status") == "LAUNCHED" and launch.get("chart_id") == CANONICAL_CHART
                and launch.get("asset_id") == "ka_gochara_v5"
                and re.fullmatch(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}", str(launch.get("run_id", "")))
                and re.fullmatch(r"brahma-build-pipeline-job-[a-z0-9]+(?:-[a-z0-9]+)*", str(launch.get("execution_name", "")))
                and re.fullmatch(r"[0-9a-f]{64}", str(launch.get("plan_manifest_digest", "")))):
            r["launch"] = launch
        else:
            r.update(status="FAILED", reason="small-test launch identity missing or invalid; reconcile remote outcome")
    if not lane_selected(req) and req.get("kind") == "verification_job" and status == "COMPLETED":
        # J-4b / PR #3747 B-1: exit zero is not launch evidence. Only the launcher's own machine record binds this operation, this request and the remote execution.
        records = []
        for line in out.splitlines():
            try:
                value = json.loads(line)
            except (ValueError, TypeError):
                continue
            if isinstance(value, dict) and value.get("schema") == "ky.verification_launch/1":
                records.append(value)
        launch = records[0] if len(records) == 1 else {}
        if (rc == 0 and launch.get("status") == "LAUNCHED" and launch.get("operation_id") == req.get("operation_id")
                and launch.get("request_sha256") == request_digest(req) and launch.get("chart_id") == CANONICAL_CHART
                and re.fullmatch(r"gochara-verification-job-[a-z0-9]+(?:-[a-z0-9]+)*", str(launch.get("execution_name", "")))
                and (launch.get("executed_check") or {}).get("status") == "CONFORMS"):
            r["launch"] = launch
        else:
            r.update(status="FAILED", reason="verification launch identity missing or invalid; reconcile remote outcome")
    if not lane_selected(req) and req.get("kind") in (*TEARDOWN_KINDS, "smalltest_teardown_dryrun", "measuring_teardown_dryrun", "century_teardown_dryrun") and status == "COMPLETED":
        records = []
        for line in out.splitlines():
            if line.startswith("teardown_proof\t"):
                try: records.append(json.loads(line.split("\t", 1)[1]))
                except ValueError: pass
        proof = records[0] if len(records) == 1 else {}
        expected = "ROLLED_BACK" if req["kind"].endswith("_dryrun") else "COMMITTED_AWAITING_ABSENCE"
        family = req["kind"].split("_")[0]                    # smalltest | measuring | century
        scope = req.get(f"{family}_scope")
        if (rc == 0 and isinstance(proof, dict) and proof.get("schema") == f"ky.{family}_teardown/1" and proof.get("status") == expected
                and proof.get("request_sha256") == request_digest(req) and proof.get("operation_id") == req["operation_id"]
                and proof.get("scope") == scope
                and proof.get("scope_sha256") == digest_bytes(json.dumps(scope, sort_keys=True, separators=(",", ":")).encode())
                and proof.get("rollback_confirmed") is (expected == "ROLLED_BACK")
                and re.fullmatch(r"[0-9a-f]{64}", str(proof.get("rowset_sha256", "")))):
            r["teardown"] = proof
            if expected == "COMMITTED_AWAITING_ABSENCE": r["status"] = "AWAITING_ABSENCE"
        else:
            r.update(status="FAILED", reason="bound teardown proof missing; reconcile transaction outcome")
    if req.get("kind") in ("publish_head", "rollback_head", "publish_head_dryrun", "rollback_head_dryrun") and status == "COMPLETED":
        try:
            if rc != 0:
                raise ValueError("non-zero head adapter exit")
            proof = head_policy(req)["child_proof"](req, out)
            r["head_change"] = proof
            if not req["kind"].endswith("_dryrun"):
                r["status"] = "AWAITING_READBACK"
        except Exception:
            r.update(status="FAILED", reason="bound head-change proof missing; reconcile through independent readback")
    overlay = overlay_proofs().pop(str(req.get("operation_id")), None)
    if overlay: r["generated_overlay"] = overlay                 # the proof the executor itself measured, never the child's words
    if extra: r.update(extra)
    with _lock, receipt_path.open("x" if separate_refusal else "w") as f:
        f.write(json.dumps(r, indent=1))
    log(f"{name} {status} {reason}")


def smalltest_policy(req: dict):
    """Load evidence rules only from the same reviewed, merged operation source.

    The installed executor is standalone; importing a helper from the mutable
    campaign checkout would cross its trust boundary. No checkout or Git write.
    """
    source = git("show", f"{req['reviewed_commit']}:platform/scripts/v5_small_test_shared.py")
    if source.returncode or not getattr(source, "stdout", ""):
        raise ValueError("reviewed small-test evidence policy unavailable")
    namespace = {"__name__": "reviewed_smalltest_policy", "__file__": "reviewed_smalltest_policy.py"}
    exec(compile(source.stdout, "reviewed small-test evidence policy", "exec"), namespace)
    return namespace


def smalltest_policy_problem(req: dict) -> str | None:
    if req.get("kind") not in ("smalltest_teardown", "smalltest_teardown_dryrun", "smalltest_dispatch", "smalltest_dispatch_dryrun",
                               "measuring_dispatch", "measuring_dispatch_dryrun", "measuring_teardown", "measuring_teardown_dryrun",
                               "century_dispatch", "century_dispatch_dryrun", "century_resume", "century_resume_dryrun", "century_teardown", "century_teardown_dryrun"):
        return None
    try:
        policy_name = {"measuring": "measuring_request_problem", "century": "century_request_problem"}.get(req["kind"].split("_")[0], "smalltest_request_problem")
        return smalltest_policy(req)[policy_name](req, OPS)
    except Exception:
        return "reviewed small-test evidence policy unavailable or invalid"


def head_policy(req: dict):
    """Load the authority policy from the operation's exact reviewed source."""
    source = git("show", f"{req['reviewed_commit']}:00_ARCHITECTURE/briefs/kalayantra/fleet/head_operation.py")
    if source.returncode or not getattr(source, "stdout", ""):
        raise ValueError("reviewed head policy unavailable")
    namespace = {"__name__": "reviewed_head_policy", "__file__": "reviewed_head_policy.py"}
    exec(compile(source.stdout, "reviewed head evidence policy", "exec"), namespace)
    return namespace


def head_policy_problem(req: dict) -> str | None:
    if req.get("kind") not in ("publish_head", "rollback_head", "publish_head_dryrun", "rollback_head_dryrun"):
        return None
    try:
        return head_policy(req)["request_problem"](req, OPS)
    except Exception:
        return "reviewed head evidence policy unavailable or invalid"


def k9_stage_policy(req: dict):
    """Load the K9-4b staging policy (absence / exposure gates) from the operation's exact reviewed source, as head_policy does: no import from a working tree."""
    source = git("show", f"{req['reviewed_commit']}:00_ARCHITECTURE/briefs/kalayantra/fleet/k9_stage_policy.py")
    if source.returncode or not getattr(source, "stdout", ""):
        raise ValueError("reviewed K9 staging policy unavailable")
    namespace = {"__name__": "reviewed_k9_stage_policy", "__file__": "reviewed_k9_stage_policy.py"}
    exec(compile(source.stdout, "reviewed K9 staging policy", "exec"), namespace)
    return namespace


def k9_rebuild_stage_problem(req: dict, table: dict) -> str | None:
    """K9-4b admission for `k9_rebuild_stage` (and its dry run's argument shape), run at the tail of validate (so on both routes, signed or mechanical, and again immediately
    before execution): the staging of the production run and candidate is admitted only with (1) THIS executor's own receipt of a COMPLETED `k9_rebuild_stage_dryrun` for the same
    identity (dry_run_check: a signer's attestation alone never admits it) and (2) an ACCEPTED, fresh absence readback and exposure readback of the fixed queries in the reviewed
    policy. The owner's go, the lease and the signer or pack-fill acceptance are the generic production gates and are judged elsewhere."""
    if req.get("kind") not in ("k9_rebuild_stage", "k9_rebuild_stage_dryrun"): return None
    try:
        why = k9_stage_policy(req)["request_problem"](req, OPS, accepted_readback)
    except Exception:
        return "reviewed K9 staging policy unavailable or invalid"
    if why or req["kind"] != "k9_rebuild_stage": return why
    return dry_run_check(req, table)[0]


def signer_acceptance_problem(req: dict) -> str | None:
    """A8 §3.9: the SIGNED route to a production write — ONE verifier lane's (v1..v4) acceptance receipt, bound to the complete request, carrying the
    attestations the kind needs. Unchanged by OWNER-MINIMAL-PROTECTION-NOW; deletions and serving changes can only be admitted this way."""
    acc = req.get("acceptance_receipt")
    if not acc or not pathlib.Path(acc).exists() or ACC.resolve() not in pathlib.Path(acc).resolve().parents: return "pre-acceptance receipt missing (must live under run/ops/acceptance/)"
    try:
        a = json.loads(pathlib.Path(acc).read_text())
    except Exception: return "pre-acceptance receipt unreadable"
    if a.get("result") != "ACCEPTED" or a.get("operation_id") != req["operation_id"] or a.get("by") not in ("v1", "v2", "v3", "v4"):
        return "pre-acceptance receipt is not an ACCEPTED receipt by a verifier lane for this operation"
    rc = str(req.get("reviewed_commit", ""))
    if not SHA.match(rc): return "reviewed_commit required for a production operation"
    if git("merge-base", "--is-ancestor", rc, "origin/main").returncode != 0: return "reviewed_commit is not merged to main"
    if a.get("reviewed_commit") != rc: return "the acceptance receipt names a different reviewed_commit"
    try:
        current = dt.datetime.now(dt.timezone.utc); issued = utc_time(a["ts"]); expires = utc_time(req["expires_at"])
        if not issued <= current < expires: return "approval expired or not yet valid"      # A8 §4: no age cap — valid until the request's own expiry
    except (KeyError, TypeError, ValueError): return "valid approval timestamp and a timezone-qualified request expires_at required"
    if a.get("request_sha256") != request_digest(req): return "approval does not bind the complete request"
    kind = req["kind"]; required = []                                        # A8 §5: `required_rows` and `restore_verified` are retired as preconditions; SR-A12-BACKUP-REMOVAL: so is `backup_taken` (no dump is taken)
    if kind not in ("backup_snapshot", "backup_restore_verify") and not kind.endswith("_dryrun"): required.append("dry_run_passed")
    if any((a.get("checks") or {}).get(k) is not True for k in required): return "required backup/restore/dry-run attestation missing"
    return None


def validate(req: dict, table: dict, caps: dict, reserved: bool = False) -> str | None:
    for k in ("operation_id", "kind", "item_id", "idempotency_key", "requested_by", "kyd"):
        if not req.get(k): return f"missing field {k}"
    if not SAFE_ID.match(str(req["operation_id"])): return "operation_id has unsafe characters"
    op = table.get(req["kind"])
    if not op: return f"unknown kind {req['kind']}"
    if not op.get("enabled"): return f"kind {req['kind']} is not enabled (enabled_by {op.get('enabled_by')})"
    if req["kind"] in ("publish_head", "rollback_head", "publish_head_dryrun", "rollback_head_dryrun"):
        prior_path = REC / f"{req['operation_id']}.json"
        if prior_path.exists():
            if not reserved:
                return "head operation_id already has a receipt; reconcile instead of re-requesting"
            try:
                prior = json.loads(prior_path.read_text())
                if prior.get("status") != "RUNNING" or prior.get("request_sha256") != request_digest(req):
                    return "reserved head operation no longer matches its RUNNING receipt"
            except Exception:
                return "reserved head operation receipt unreadable"
    if "TO_BE_SET" in op.get("script", "") or "TO_BE_SET" in str(op.get("needs", "")): return "operation script not yet reviewed/landed"
    if req["requested_by"] not in op.get("requesters", ["adhikarin"]): return f"requested_by {req['requested_by']} may not request {req['kind']}"
    if "dry_run" in req and "lane_target" not in req:
        return "dry_run requires an explicit lane target"
    if "lane_target" in req:
        return validate_lane(req, op, reserved)
    if not caps.get(op["needs"], False): return f"capability_missing: {op['needs']}"
    for capability in op.get("also_needs", []):
        if not caps.get(capability, False): return f"capability_missing: {capability}"
    args = req.get("args") or {}
    if req["kind"] == "readback_sql" and req["item_id"] == "K9-4b" and not re.fullmatch(r"[0-9a-f]{64}", str(args.get("sql-sha256", ""))):
        return "K9-4b readback requires a prepared SQL digest"
    bad = [k for k in args if k not in op.get("allowed_args", [])]
    if bad: return f"disallowed args {bad}"
    if any(not SAFE_ARG.match(str(v)) for v in args.values()): return "an argument value has unsafe characters"
    if not op.get("production") and req["kind"].endswith("_dryrun"):
        # A8 §3.8: read-only with a credential — no lease, acceptance or fence; but a credentialed child only ever runs a reviewed, merged tree
        rc = str(req.get("reviewed_commit", ""))
        if not SHA.match(rc): return "reviewed_commit required for a dry-run operation"
        if git("merge-base", "--is-ancestor", rc, "origin/main").returncode != 0: return "reviewed_commit is not merged to main"
    if op.get("production"):
        if req.get("chart_id") != CANONICAL_CHART: return "chart_id is not the canonical chart"
        if not req.get("lease_id") or not lease_live(req["lease_id"]): return "lease is not the single unexpired ACTIVE row on origin/campaign-coordination"
        if not req.get("acceptance_receipt") and req.get("pack_fill") is not None:      # OWNER-MINIMAL-PROTECTION-NOW: no signer named, a pack fill offered -> the mechanical route (a signer's receipt, when present, is always judged as before)
            why = mechanical_pre_acceptance(req, table)
        else: why = signer_acceptance_problem(req)
        if why: return why
    if not reserved and seen(req["idempotency_key"]): return "idempotency key already used"
    why = None
    for check in (   # evaluated in this order, first problem wins; one per line, sorted. Each check is gated on its own kinds and only century_contract_problem and smalltest_policy_problem overlap (century_dispatch[_dryrun]): the century contract's reason is reported first, as before
        lambda: century_contract_problem(req),
        lambda: head_policy_problem(req),
        lambda: k9_rebuild_stage_problem(req, table),
        lambda: measuring_cancel_problem(req),
        lambda: orchestrator_rebuild_cancel_problem(req),
        lambda: orchestrator_rebuild_dryrun_problem(req, table),
        lambda: orchestrator_rebuild_teardown_problem(req),
        lambda: owner_go_problem(req, op),
        lambda: scheduler_policy_problem(req),
        lambda: served_probe_problem(req, op),
        lambda: smalltest_policy_problem(req),
    ):
        why = check()
        if why: return why
    return why


def lane_selected(req: dict) -> bool:
    return "lane_target" in req


def remote_async(kind: str, op: dict) -> bool:
    """A8 §3.11: only a kind whose work continues on a remote system after its child returns takes the production fence — the table's
    `remote_async: true`, or one of REMOTE_ASYNC_KINDS even if a table drops the flag. A synchronous kind is finished when its child is."""
    return op.get("remote_async") is True or kind in REMOTE_ASYNC_KINDS


def lane_target_settings(req: dict) -> dict:
    """A structured endpoint, never libpq text, a service or an inherited URL."""
    target = req.get("lane_target")
    if (not isinstance(target, dict) or set(target) != {"host", "port", "database"}
            or target.get("host") not in ("127.0.0.1", "localhost", "::1")
            or type(target.get("port")) is not int or target["port"] != 55433
            or not isinstance(target.get("database"), str)
            or re.fullmatch(r"ky_[a-z][a-z0-9_]{0,54}", target["database"]) is None):
        raise ValueError("lane target must be one loopback host:55433 and a ky_<lane> database; no other fields")
    if req.get("dry_run") is not True:
        raise ValueError("lane target requires dry_run=true")
    return dict(host=target["host"], hostaddr="::1" if target["host"] == "::1" else "127.0.0.1",
                port="55433", dbname=target["database"], user="postgres", password="",
                passfile=os.devnull, options="", sslmode="disable", connect_timeout="10")


def validate_lane(req: dict, op: dict, reserved: bool = False) -> str | None:
    try:
        lane_target_settings(req)
    except ValueError as exc:
        return str(exc)
    binding = op.get("lane_readback" if req["kind"] == "readback_sql" else "lane_dry_run")
    if not isinstance(binding, dict) or binding != {"script": "00_ARCHITECTURE/briefs/kalayantra/fleet/lane_smalltest.py", "needs": "none"}:
        return "operation has no reviewed lane binding"
    if not isinstance(req.get("request_id"), str) or not SAFE_ID.fullmatch(req["request_id"]):
        return "lane request_id required with safe characters"
    if CANONICAL_CHART != req.get("chart_id"):
        return "chart_id is not the canonical chart"
    args = req.get("args", {})
    if not isinstance(args, dict): return "lane args must be an object"
    if req["kind"] == "readback_sql" and args: return "lane readback takes no SQL or arguments"
    bad = [key for key in args if key not in op.get("allowed_args", [])]
    if bad: return "disallowed args " + str(bad)
    if any(not isinstance(v, str) or not SAFE_ARG.fullmatch(v) for v in args.values()):
        return "an argument value has unsafe characters"
    if req["kind"].startswith("backup_") and re.fullmatch(r"[a-z][a-z0-9_]{2,39}", args.get("label", "")) is None:
        return "lane backup requires a valid label"
    rc = req.get("reviewed_commit", "")
    if not isinstance(rc, str) or re.fullmatch(r"[0-9a-f]{40}", rc) is None:
        return "full reviewed_commit required for a lane operation"
    if git("merge-base", "--is-ancestor", rc, "origin/main").returncode:
        return "lane reviewed_commit is not merged to main"
    for script in (op["script"], binding["script"]):
        if git("cat-file", "-e", f"{rc}:{script}").returncode:
            return f"lane script {script} does not exist at reviewed_commit"
    try:
        if not dt.datetime.now(dt.timezone.utc) < utc_time(req["expires_at"]):
            return "lane request expired"
    except (KeyError, ValueError, TypeError):
        return "timezone-qualified lane expires_at required"
    if seen(req["idempotency_key"]) and not reserved: return "idempotency key already used"
    # A8 §4: the J-1a lane qualification ritual (`lane_receipts`) is no longer an admission precondition; see execute_lane / receipt_lane.
    # Reuse the reviewed small-test admission policy, with the non-mutating
    # child mode. Empty scope is the initial rehearsal, never deletion authority.
    if req["kind"].startswith("smalltest_"):
        child = dict(req)
        if "dispatch" in req["kind"]: child["kind"] = "smalltest_dispatch_dryrun"
        else: child.update(kind="smalltest_teardown_dryrun", smalltest_scope={"empty": True})
        try: return smalltest_policy(req)["smalltest_request_problem"](child, OPS)
        except Exception: return "reviewed small-test evidence policy unavailable or invalid"
    return None


def lane_qualification(req: dict) -> list[dict]:
    """Bind six completed lane rehearsals and their complete output bytes.

    The final readback is an existing readback_sql operation, not a new enabled
    kind. Receipt files are read only under REC, with no caller-provided paths.
    """
    if "lane_receipts" not in req: return []
    refs = req["lane_receipts"]
    kinds = {"backup_snapshot", "backup_restore_verify", "smalltest_dispatch_dryrun", "smalltest_dispatch",
             "smalltest_teardown_dryrun", "smalltest_teardown"}
    if req.get("kind") != "readback_sql" or not isinstance(refs, list) or len(refs) != 6:
        raise ValueError("final lane readback requires exactly six receipts")
    bound = []
    for ref in refs:
        if (not isinstance(ref, dict) or set(ref) != {"name", "sha256"}
                or not isinstance(ref["name"], str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,80}\.json", ref["name"])):
            raise ValueError("invalid lane receipt reference")
        path = REC / ref["name"]
        if path.resolve().parent != REC.resolve(): raise ValueError("lane receipt escapes evidence directory")
        body = path.read_bytes()
        if digest_bytes(body) != ref["sha256"]: raise ValueError("lane receipt byte digest differs")
        record = json.loads(body)
        if not isinstance(record, dict) or not isinstance(record.get("lane"), dict):
            raise ValueError("lane receipt and proof must be JSON objects")
        proof = record["lane"]; kind = record.get("kind")
        oid = record.get("operation_id", "")
        if (kind not in kinds or record.get("item_id") != "J-1a" or record.get("status") != "COMPLETED"
                or type(record.get("exit_code")) is not int or record["exit_code"] != 0
                or not isinstance(oid, str) or not SAFE_ID.fullmatch(oid) or ref["name"] != oid + ".json"
                or not isinstance(record.get("request_id"), str) or not SAFE_ID.fullmatch(record["request_id"])
                or record.get("reviewed_commit") != req["reviewed_commit"]
                or proof.get("schema") != "ky.smalltest_lane/1" or proof.get("status") != "DRY_RUN_VERIFIED"
                or proof.get("lane_target") != req["lane_target"] or proof.get("dry_run") is not True
                or proof.get("independent_readback") is not True or proof.get("unchanged") is not True
                or proof.get("before_sha256") != proof.get("after_sha256")
                or not re.fullmatch(r"[0-9a-f]{64}", str(proof.get("after_sha256", "")))
                or any(proof.get(key) != record.get(key) for key in
                       ("operation_id", "request_id", "request_sha256", "reviewed_commit", "kind"))
                or record.get("evidence_sha256") != digest_bytes(json.dumps(proof, sort_keys=True, separators=(",", ":")).encode())):
            raise ValueError("lane receipt does not prove a bound rehearsal")
        output = REC / (oid + ".output.txt")
        if output.resolve().parent != REC.resolve() or digest_bytes(output.read_bytes()) != record.get("output_sha256"):
            raise ValueError("lane complete output bytes differ")
        bound.append(dict(kind=kind, operation_id=oid, request_id=record["request_id"],
                          receipt_sha256=ref["sha256"], output_sha256=record["output_sha256"],
                          evidence_sha256=record["evidence_sha256"], after_sha256=proof["after_sha256"]))
    if ({entry["kind"] for entry in bound} != kinds or len({entry["operation_id"] for entry in bound}) != 6
            or len({entry["request_id"] for entry in bound}) != 6):
        raise ValueError("six distinct lane operations and requests required")
    if (req.get("operation_id") in {entry["operation_id"] for entry in bound}
            or req.get("request_id") in {entry["request_id"] for entry in bound}):
        raise ValueError("final lane readback identity must be distinct from rehearsals")
    return bound


def child_stderrs(_store: dict = {}) -> dict:
    """In-memory hand-off of each operation's child stderr from execute()/execute_lane() to receipt(); execute() returns the child's stdout alone."""
    return _store


def overlay_proofs(_store: dict = {}) -> dict:
    """In-memory hand-off of each operation's generated-overlay proof from execute()/execute_lane() to receipt(); the
    child's output is never altered (a reader parses it whole) and never trusted for the proof."""
    return _store


def apply_generated_overlay(root: pathlib.Path, commit: str, env: dict, timeout: int = 600) -> tuple[dict | None, str]:
    """A5 D-33: the machine-owned writer-digest file is deliberately non-authoritative on main; CI/deploy overlay bytes generated from
    the reviewed commit. Regenerate it in `root` (a tree of `commit`) with the repository's own generator — the narrowest subset of
    ci_generated.py that covers this file, because the rest of `generate` needs node and npm, which this host does not carry — then
    verify with the generator's own --check in a second process. Returns (proof, "") or (None, reason); the caller fails closed."""
    sidecar = root / "platform/python-sidecar"; digests = "platform/src/generated/nirmana-writer-digests.json"
    child = {k: v for k, v in env.items() if k in {"PATH", "HOME", "LANG", "LC_ALL", "TZ", "TMPDIR", "SE_EPHE_PATH"}}
    child["PYTHONDONTWRITEBYTECODE"] = "1"                      # a digest generator needs no credential, cloud or database reach
    module = [PY, "-m", "pipeline.orchestrator.provenance_inventory"]
    try:
        for step, argv in (("generate", module), ("check", module + ["--check"])):
            p = run_group(argv, sidecar, child, timeout)
            if p.returncode: return None, f"writer-digest {step} exited {p.returncode}: " + redact((p.stderr or p.stdout or "")[-300:])
        files = {digests: digest_bytes((root / digests).read_bytes())}
    except (OSError, subprocess.SubprocessError) as e:
        return None, f"{type(e).__name__}: {redact(str(e))[:300]}"
    manifest = {"schema": "ky.generated_overlay/1", "source_sha": commit, "files": files}
    return dict(manifest, manifest_sha256=digest_bytes(json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode())), ""


def lane_child_env(req: dict, scratch: pathlib.Path) -> dict:
    env = {k: v for k, v in os.environ.items() if k in {"PATH", "LANG", "LC_ALL", "TZ"}}
    env.update(KY_OPERATION_REQUEST=json.dumps(req, sort_keys=True, separators=(",", ":")),
               KY_ROOT=str(scratch), TMPDIR=str(scratch), PGPASSFILE=os.devnull,
               PYTHONDONTWRITEBYTECODE="1", GIT_OPTIONAL_LOCKS="0",
               SE_EPHE_PATH=os.environ.get("SE_EPHE_PATH", str(KY_ROOT / "ephe")))
    return env


def execute_lane(req: dict, op: dict) -> tuple[int, str]:
    """Export only reviewed Git objects; no worktree, credential or cloud call."""
    import tarfile
    why = validate_lane(req, op, reserved=True)
    if why: return 2, why
    with tempfile.TemporaryDirectory(prefix="lane-", dir=TMP) as directory:
        scratch = pathlib.Path(directory)
        archive = scratch / "source.tar"
        paths = ["platform/scripts", "platform/python-sidecar", "platform/src/generated/nirmana-writer-digests.json", OPS_PATH.rsplit("/", 1)[0]]
        with archive.open("wb") as stream:
            result = subprocess.run(["git", "-C", str(GIT), "archive", "--format=tar", req["reviewed_commit"], *paths],
                                    stdout=stream, stderr=subprocess.PIPE, env=lane_child_env(req, scratch), timeout=120)
        if result.returncode: return 127, "lane reviewed source export failed"
        source = scratch / "source"; source.mkdir()
        with tarfile.open(archive) as bundle: bundle.extractall(source, filter="data")
        # A request that still carries the retired J-1a ritual (A8 §4) is bound here and at the receipt, never at admission: stage the
        # evidence bytes for the separately connected observer only through lane_qualification, whose checks keep every name inside
        # REC. The observer rechecks every digest after this copy, so races fail closed.
        if "lane_receipts" in req:
            try: bound = lane_qualification(req)
            except (ValueError, OSError, KeyError, TypeError): return 2, "lane qualification receipts missing, mismatched or incomplete"
            staged = scratch / "run/ops/receipts"; staged.mkdir(parents=True)
            for entry in bound:
                for name in (entry["operation_id"] + ".json", entry["operation_id"] + ".output.txt"):
                    (staged / name).write_bytes((REC / name).read_bytes())
        env = lane_child_env(req, scratch)
        env["PYTHONPATH"] = str(source / "platform/python-sidecar")
        overlay, why = apply_generated_overlay(source, req["reviewed_commit"], env)
        if overlay is None: return 126, "generated overlay refused: " + why
        overlay_proofs()[req["operation_id"]] = overlay
        adapter = op.get("lane_readback", op.get("lane_dry_run"))["script"]
        p = run_group([PY, str(source / adapter), "--dry-run", "--lane-target", json.dumps(req["lane_target"], sort_keys=True)],
                      source, env, min(int(req.get("timeout_s", 900)), MAX_TIMEOUT))
        child_stderrs()[req["operation_id"]] = p.stderr or ""
        return p.returncode, p.stdout or ""


def receipt_lane(req: dict, record: dict, status: str, rc: int | None, out: str) -> None:
    record.update(request_id=req.get("request_id"), lane_target=req.get("lane_target"), dry_run=True,
                  production=False)
    if status != "COMPLETED": return
    proofs = []
    for line in out.splitlines():
        try: value = json.loads(line)
        except ValueError: continue
        if isinstance(value, dict) and value.get("schema") == "ky.smalltest_lane/1": proofs.append(value)
    proof = proofs[0] if len(proofs) == 1 else {}
    valid = (rc == 0 and proof.get("status") == "DRY_RUN_VERIFIED" and proof.get("dry_run") is True
        and proof.get("independent_readback") is True and proof.get("unchanged") is True
        and proof.get("before_sha256") == proof.get("after_sha256")
        and all(re.fullmatch(r"[0-9a-f]{64}", str(proof.get(key, ""))) for key in
                ("before_sha256", "after_sha256", "script_sha256", "child_output_sha256"))
        and all(proof.get(key) == req.get(key) for key in
                ("operation_id", "request_id", "reviewed_commit", "kind", "lane_target"))
        and proof.get("request_sha256") == request_digest(req))
    if "lane_receipts" in req:
        try:
            expected = lane_qualification(req)
            valid = (valid and proof.get("qualification") == expected
                and proof.get("qualification_sha256") == digest_bytes(json.dumps(expected, sort_keys=True, separators=(",", ":")).encode())
                and all(entry["after_sha256"] == proof.get("after_sha256") for entry in expected))
        except (ValueError, OSError, KeyError, TypeError): valid = False
    # Bind the entry script from the reviewed table, not mutable local metadata.
    table_source = git("show", f"{req.get('reviewed_commit')}:{OPS_PATH}")
    try: script = json.loads(table_source.stdout)["ops"][req["kind"]]["script"]
    except (ValueError, KeyError, TypeError, AttributeError): script = None
    if valid and proof.get("script") == script:
        record["lane"] = proof
        record["evidence_sha256"] = digest_bytes(json.dumps(proof, sort_keys=True, separators=(",", ":")).encode())
    else:
        record.update(status="FAILED", reason="bound lane dry-run and independent readback proof missing or invalid")


def run_group(argv: list[str], cwd: pathlib.Path, env: dict, timeout: int) -> subprocess.CompletedProcess:
    """Run in its own process group and leave nothing behind — a timeout or an exit kills every descendant."""
    # A descendant may inherit stdout/stderr after the direct child exits. Pipes would make
    # communicate() wait for that descendant until timeout, misclassifying a finished dispatch.
    # Files retain the complete output without tying completion to inherited pipe handles.
    with tempfile.TemporaryFile(mode="w+t") as stdout, tempfile.TemporaryFile(mode="w+t") as stderr:
        p = subprocess.Popen(argv, cwd=str(cwd), env=env, stdout=stdout, stderr=stderr,
                             text=True, start_new_session=True)
        try:
            rc = p.wait(timeout=timeout)
        finally:
            try: os.killpg(p.pid, signal.SIGKILL)
            except ProcessLookupError: pass
            try: p.wait(timeout=10)
            except Exception: pass
        stdout.seek(0); stderr.seek(0)
        return subprocess.CompletedProcess(argv, rc, stdout.read(), stderr.read())


def execute(req: dict, op: dict) -> tuple[int, str]:
    if lane_selected(req):
        return execute_lane(req, op)
    oid = req["operation_id"]; script = op["script"]; args: list[str] = list(op.get("fixed_args", []))
    for k, v in (req.get("args") or {}).items(): args += [f"--{k}", str(v)]
    timeout = min(int(req.get("timeout_s", op.get("timeout_s", 3600))), MAX_TIMEOUT)
    env = {k: v for k, v in os.environ.items() if k in CHILD_ENV_ALLOW}          # neither privileged connection reaches a child by default
    if op["needs"] == "builder": env["DATABASE_URL"] = os.environ["KY_BUILDER_DATABASE_URL"]
    elif op["needs"] == "owner": env["DATABASE_URL"] = os.environ["KY_OWNER_DATABASE_URL"]
    elif op["needs"] == "layer_verifier": env["DATABASE_URL"] = os.environ["KY_LAYER_VERIFIER_DATABASE_URL"]
    elif op["needs"] == "consumer_reader": env[CONSUMER_PROBE_KEY] = os.environ[CONSUMER_PROBE_KEY]      # J-6l-a61: this kind's child alone receives the consumer credential
    env["KY_OPERATION_REQUEST"] = json.dumps(req, sort_keys=True, separators=(",", ":"))
    env["PGAPPNAME"] = session_marker(oid)                                      # A7 D-44: libpq tags every connection this child opens, so quiescence can see them
    env["SE_EPHE_PATH"] = os.environ.get("SE_EPHE_PATH", str(KY_ROOT / "ephe")); env["KY_ROOT"] = str(KY_ROOT)
    if not op.get("production") and not req["kind"].endswith("_dryrun"):     # a `*_dryrun` is production:false (A8 §3.8) yet runs in its reviewed tree below
        src = git("show", f"origin/main:{script}")
        if src.returncode != 0: return 127, f"script {script} is not on origin/main"
        tmp = TMP / f"{oid}.{pathlib.Path(script).name}"; tmp.write_text(src.stdout); tmp.chmod(0o700)
        argv = ([PY, str(tmp)] if script.endswith(".py") else ["bash", str(tmp)]) + args
        try:
            if req["kind"] == "local_schema_seed":
                # Own scratch per seed operation; never inherit the caller's path.
                with tempfile.TemporaryDirectory(prefix=f"op-{oid}-", dir=EXEC.resolve()) as scratch:
                    env["KY_SCRATCH"] = scratch
                    p = run_group(argv, KY_ROOT, env, timeout)
            else:
                p = run_group(argv, KY_ROOT, env, timeout)
        finally:
            tmp.unlink(missing_ok=True)
        child_stderrs()[oid] = p.stderr or ""
        return p.returncode, p.stdout or ""
    wt = EXEC / f"op-{oid}"
    a = git("worktree", "add", "--detach", str(wt), req["reviewed_commit"], timeout=600)
    if a.returncode != 0: return 126, "cannot create the operation worktree: " + a.stderr[-400:]
    try:
        cwd = wt / op.get("cwd", "")
        if op.get("python_module"): argv = [PY, "-m", op["python_module"]] + args
        elif script.endswith(".py"): argv = [PY, str(wt / script)] + args
        else: argv = ["bash", str(wt / script)] + args
        if not op.get("python_module") and not (wt / script).exists(): return 127, f"script {script} does not exist at {req['reviewed_commit']}"
        overlay, why = apply_generated_overlay(wt, req["reviewed_commit"], env)
        if overlay is None: return 126, "generated overlay refused: " + why
        overlay_proofs()[oid] = overlay
        p = run_group(argv, cwd, env, timeout)
        child_stderrs()[oid] = p.stderr or ""
        return p.returncode, p.stdout or ""
    finally:
        git("worktree", "remove", "--force", str(wt), timeout=300)


def session_marker(operation_id: str) -> str:
    """A7 D-44: the application_name (PGAPPNAME) every database connection of this operation's child carries. Before this, no operation set
    a marker. A remote execution (Cloud Run) opens its own connections without it: those are covered by the execution readback instead."""
    return "ky-op-" + hashlib.sha256(operation_id.encode()).hexdigest()[:16]


def write_new_json(path: pathlib.Path, document: dict) -> bool:
    """Publish `document` at `path` atomically (temp file + hard link); an existing path is never replaced — returns False."""
    pending = path.with_name("." + path.name + f".pending-{os.getpid()}")
    try:
        with pending.open("x") as stream:
            stream.write(json.dumps(document, indent=1)); stream.flush(); os.fsync(stream.fileno())
        os.link(pending, path)
        return True
    except FileExistsError:
        return False
    finally:
        pending.unlink(missing_ok=True)


def measured_identity(req: dict, archived: pathlib.Path) -> tuple[dict, bytes, bytes, dict]:
    """A7 D-44: re-measure from the files the executor itself wrote (never from the process that ran) that `req` ended COMPLETED with exit 0,
    that the archived request is the one the receipt binds, and that the output file is the one the receipt digests.
    Returns (receipt, receipt bytes, output bytes, checks); a check is True only when its comparison held."""
    oid = req["operation_id"]
    receipt_bytes = (REC / f"{oid}.json").read_bytes(); record = json.loads(receipt_bytes)
    body = (REC / f"{oid}.output.txt").read_bytes()
    archived_sha = request_digest(json.loads(archived.read_text()))
    entry = (load_table() or {}).get(req["kind"]) or {}
    commit = req.get("reviewed_commit")
    checks = {
        "receipt_completed_exit_zero": record.get("status") == "COMPLETED" and type(record.get("exit_code")) is int and record["exit_code"] == 0,
        "receipt_names_this_operation": record.get("operation_id") == oid and record.get("kind") == req["kind"],
        "archived_request_sha_equals_receipt": archived_sha == record.get("request_sha256") == request_digest(req),
        "output_sha_equals_receipt": digest_bytes(body) == record.get("output_sha256"),
        "reviewed_commit_merged": (isinstance(commit, str) and SHA.fullmatch(commit) is not None and commit == record.get("reviewed_commit")
                                   and git("merge-base", "--is-ancestor", commit, "origin/main").returncode == 0),
        "kind_read_only_per_table": entry.get("read_only") is True and entry.get("production") is False,
        "not_a_lane_rehearsal": not lane_selected(req) and "lane_target" not in record,
    }
    return record, receipt_bytes, body, {k: bool(v) for k, v in checks.items()}


def mechanical_post_acceptance(req: dict, archived: pathlib.Path) -> str | None:
    """A7 D-44: a COMPLETED exit-0 read-only operation is accepted by the executor itself — no reviewer. Writes acceptance/<op>.post.json
    (by executor-mechanical) only when every identity check above holds; otherwise nothing (honest null) and the reason is returned.
    It judges nothing about the readback's content: op-specific pass criteria stay with whoever consumes it."""
    record, receipt_bytes, body, checks = measured_identity(req, archived)
    failed = sorted(k for k, v in checks.items() if not v)
    if failed: return "not accepted: " + ", ".join(failed)
    document = {"schema": "ky.mechanical_acceptance/1", "phase": "post", "by": "executor-mechanical", "result": "ACCEPTED",
                "operation_id": req["operation_id"], "kind": req["kind"], "request_sha256": record["request_sha256"],
                "reviewed_commit": record["reviewed_commit"], "exit_code": 0, "output_sha256": record["output_sha256"],
                "receipt_sha256": digest_bytes(receipt_bytes), "checks": checks, "ts": now()}
    return None if write_new_json(ACC / f"{req['operation_id']}.post.json", document) else "acceptance already exists; left untouched"


def accepted_cloudrun_execution(readback_id: str, execution_name: str) -> dict | None:
    """The terminal state of `execution_name` as an ACCEPTED cloudrun_job_readback measured it (None when not provable or still running)."""
    if not SAFE_ID.fullmatch(readback_id): return None
    record = json.loads((REC / f"{readback_id}.json").read_text()); body = (REC / f"{readback_id}.output.txt").read_bytes()
    accepted = json.loads((ACC / f"{readback_id}.post.json").read_text())
    if not (record.get("kind") == "cloudrun_job_readback" and record.get("status") == "COMPLETED" and record.get("exit_code") == 0
            and digest_bytes(body) == record.get("output_sha256") and accepted.get("result") == "ACCEPTED"
            and accepted.get("by") in ("v1", "v2", "v3", "v4", "executor-mechanical") and accepted.get("operation_id") == readback_id
            and accepted.get("request_sha256") == record.get("request_sha256")
            and (accepted.get("by") != "executor-mechanical"       # same bar as fence_quiescent: the record's own schema, and every check present and true
                 or (accepted.get("schema") == "ky.mechanical_acceptance/1" and isinstance(accepted.get("checks"), dict)
                     and bool(accepted["checks"]) and all(value is True for value in accepted["checks"].values())))):
        return None
    found = []
    for line in body.decode().splitlines():
        try: value = json.loads(line)
        except ValueError: continue
        if isinstance(value, dict) and value.get("schema") == "ky.cloudrun_readback/1": found.append(value)
    measured = (found[0].get("execution") if len(found) == 1 and found[0].get("status") == "MEASURED" else None) or {}
    if measured.get("name") != execution_name or measured.get("outcome") not in ("SUCCEEDED", "FAILED"): return None
    return {"readback_operation_id": readback_id, "execution": execution_name, "outcome": measured["outcome"],
            "completion_time": measured.get("completion_time"), "readback_output_sha256": record["output_sha256"]}


def accepted_readback(readback_id: str, kind: str) -> tuple[dict, bytes] | None:
    """(receipt, output bytes) of a read-only `kind` operation that COMPLETED with exit 0, whose output file still has the receipt's sha256 and that an ACCEPTED post
    record binds (None when not provable). An unreadable file raises: the callers treat that as not provable. Same bar as accepted_cloudrun_execution, which is a pinned
    function and so is left untouched."""
    if not SAFE_ID.fullmatch(readback_id): return None
    record = json.loads((REC / f"{readback_id}.json").read_text()); body = (REC / f"{readback_id}.output.txt").read_bytes()
    accepted = json.loads((ACC / f"{readback_id}.post.json").read_text())
    if not (record.get("kind") == kind and record.get("status") == "COMPLETED" and record.get("exit_code") == 0 and digest_bytes(body) == record.get("output_sha256")): return None
    if not (accepted.get("result") == "ACCEPTED" and accepted.get("operation_id") == readback_id and accepted.get("request_sha256") == record.get("request_sha256")): return None
    if accepted.get("by") in ("v1", "v2", "v3", "v4"): return record, body
    checks = accepted.get("checks")      # the executor's own mechanical acceptance: its schema, and every check present and true
    if accepted.get("by") == "executor-mechanical" and accepted.get("schema") == "ky.mechanical_acceptance/1" and isinstance(checks, dict) and checks and all(v is True for v in checks.values()):
        return record, body
    return None


def mechanical_quiescence(req: dict, archived: pathlib.Path) -> str | None:
    """A7 D-44: `req` is a completed quiescence_check naming a fenced production operation (args.operation). The executor measures, from its
    own files and the check's session readback, that the operation is quiet — receipt terminal, not in flight, the fence names it, no live
    database session carries its marker (and the readback could see every role's sessions), and, for a dispatch, the remote execution is in a
    terminal state per an ACCEPTED cloudrun_job_readback (args.execution_readback). Writes acceptance/<target>.quiescence.json (by
    executor-mechanical) only if every check holds; fence_quiescent() re-validates it and the cockpit's release-fence then accepts it.
    A teardown is never written here: its release needs the consumer-judged absence evidence the check cannot supply."""
    args = req.get("args") or {}; target = str(args.get("operation", ""))
    if not SAFE_ID.fullmatch(target): return "target operation id missing or unsafe"
    own, own_bytes, body, own_checks = measured_identity(req, archived)
    target_bytes = (REC / f"{target}.json").read_bytes(); done = json.loads(target_bytes)
    entry = (load_table() or {}).get(done.get("kind")) or {}
    try: fence = json.loads(FENCE.read_text())
    except (OSError, ValueError): fence = {}
    inflight = []
    for path in INFLIGHT.glob("*.json"):
        try: inflight.append(json.loads(path.read_text()).get("operation_id"))
        except (OSError, ValueError): inflight.append(None)       # an unreadable in-flight entry is unproven quiet
    found = []
    for line in body.decode().splitlines():
        try: value = json.loads(line)
        except ValueError: continue
        if isinstance(value, dict) and value.get("schema") == "ky.session_readback/1": found.append(value)
    sessions = found[0] if len(found) == 1 else {}
    marker = session_marker(target)
    needs_remote = remote_async(str(done.get("kind")), entry) or isinstance(done.get("launch"), dict)       # every remote_async kind (A8 §3.11): fail closed without an accepted readback of its execution
    remote = None
    if needs_remote:
        try: remote = accepted_cloudrun_execution(str(args.get("execution_readback", "")), str((done.get("launch") or {}).get("execution_name", "")))
        except (OSError, ValueError, TypeError, AttributeError): remote = None
    try: after_terminal = utc_time(sessions["measured_at"]) >= utc_time(done["ts"])
    except (KeyError, TypeError, ValueError): after_terminal = False
    checks = dict(own_checks,
        target_is_a_production_operation=entry.get("production") is True and "lane_target" not in done,
        target_is_not_a_teardown=done.get("kind") not in TEARDOWN_KINDS,
        target_receipt_terminal=done.get("operation_id") == target and done.get("status") in ("COMPLETED", "FAILED", "AWAITING_ABSENCE"),
        fence_names_the_target_request=fence.get("operation_id") == target and bool(done.get("request_sha256")) and fence.get("request_sha256") == done.get("request_sha256"),
        target_not_in_flight=None not in inflight and target not in inflight,
        session_readback_bound_to_the_target_marker=(sessions.get("status") == "MEASURED" and sessions.get("marker") == marker == done.get("session_marker")),
        session_readback_sees_every_role=sessions.get("sees_all_sessions") is True,
        session_readback_after_the_target_ended=after_terminal,
        no_live_session_carries_the_marker=sessions.get("sessions") == [],
        remote_execution_terminal=(remote is not None) if needs_remote else True)
    checks = {k: bool(v) for k, v in checks.items()}
    failed = sorted(k for k, v in checks.items() if not v)
    if failed: return "not quiescent: " + ", ".join(failed)
    document = {"schema": "ky.mechanical_quiescence/1", "by": "executor-mechanical", "result": "ACCEPTED", "operation_id": target,
                "kind": done["kind"], "request_sha256": done["request_sha256"], "reviewed_commit": done.get("reviewed_commit"),
                "target_receipt_sha256": digest_bytes(target_bytes), "checks": checks,
                "session_check": {"operation_id": req["operation_id"], "receipt_sha256": digest_bytes(own_bytes), "marker": marker,
                                  "database": sessions.get("database"), "measured_at": sessions["measured_at"], "live_sessions": 0},
                "remote_execution": remote, "ts": now()}
    return None if write_new_json(ACC / f"{target}.quiescence.json", document) else "quiescence record already exists; left untouched"


def mechanical_acceptance(req: dict, archived: pathlib.Path) -> None:
    """A7 D-44: after a request is archived, write the executor's mechanical acceptance records it is entitled to. Never raises, never
    blocks the queue; the outcome (written, or the exact reason nothing was) goes to the log. Whether the kind is read-only is measured
    inside measured_identity from the table, so a writing kind is simply "not accepted"."""
    try:
        log(f"{req['operation_id']} mechanical post-acceptance: {mechanical_post_acceptance(req, archived) or 'written'}")
        if req["kind"] == "quiescence_check":
            log(f"{(req.get('args') or {}).get('operation')} mechanical quiescence: {mechanical_quiescence(req, archived) or 'written'}")
    except Exception as e:
        log(f"{req.get('operation_id')} mechanical acceptance error: {type(e).__name__}")


def run_one(path: pathlib.Path, req: dict, op: dict) -> None:
    try:
        # authorisation is re-checked immediately before execution, not only when the request was queued
        if (KY_ROOT / "HOLD").exists():
            receipt(req, "REFUSED", "HOLD set before execution"); return
        sync(); current_table = load_table()
        if current_table is None or current_table.get(req["kind"]) != op:
            receipt(req, "REFUSED", "operation definition changed before execution"); return
        why = validate(req, current_table, capabilities(True), reserved=True)
        if why:
            receipt(req, "REFUSED", why); return
        if req["kind"] == "scheduler_pause": arm_scheduler_backstop(req)      # SR-J3-REAPER-PAUSE: armed BEFORE the pause runs; a refusal to arm stops the pause
        rc, out = execute(req, op)
        stderr = child_stderrs().pop(req["operation_id"], "")
        extra = None if lane_selected(req) else {"session_marker": session_marker(req["operation_id"])}
        proof, problem = scheduler_proof(req, rc, out) if extra is not None and req["kind"] in SCHEDULER_ACTION else (None, None)
        if proof is not None: extra["scheduler"] = proof        # the state read back AFTER the action, as the reviewed script measured it
        cancelled, cancel_problem = measuring_cancel_proof(req, rc, out) if extra is not None and req["kind"] in CANCEL_KINDS else (None, None)
        if cancelled is not None: extra["cancel"] = cancelled   # likewise: the execution state read back after the cancel (CANCELLED, or the observed state beside a FAILED receipt)
        probed, probe_problem = served_probe_proof(req, op, rc, out) if extra is not None and req["kind"] == "served_probe" else (None, None)
        if probed is not None: extra["probe"] = probed          # SR-TEARDOWN-AUTHORITY-GATE: status, content type, length and sha256 of the served body (the body only where the table allows)
        consumed, consumer_problem = consumer_probe_proof(req, rc, out, stderr) if extra is not None and req["kind"] == "consumer_probe" else (None, None)
        if consumed is not None: extra["consumer_probe"] = consumed      # J-6l-a61: typed fields only (no body, no credential) — the authenticated consumer-path measurement
        probe_problem = probe_problem or consumer_problem
        ok = rc == 0 and problem is None and cancel_problem is None and probe_problem is None
        receipt(req, "COMPLETED" if ok else "FAILED", "" if ok else (problem or cancel_problem or probe_problem or "non-zero exit (read the postconditions; an exit status proves nothing)"), rc, out, extra, stderr)
        if ok and req["kind"] == "scheduler_resume": scheduler_backstop_satisfy(req)
    except subprocess.TimeoutExpired as e:
        receipt(req, "FAILED", "timeout — the local process group was killed; a remote job may still be running: read the postconditions", 124, str(e))
    except Exception as e:
        receipt(req, "FAILED", f"executor error: {type(e).__name__}: {redact(str(e))}")
    finally:
        try: shutil.move(str(path), DONE / path.name)
        except Exception: pass
        mechanical_acceptance(req, DONE / path.name)


def run_cancel_lane(path: pathlib.Path, req: dict, op: dict) -> None:
    """SR-CANCEL-LANE: what the cancel lane's worker runs. A kind that is not on the closed allow-list is refused here, whatever routed it, and never executed."""
    if req.get("kind") not in CANCEL_LANE_KINDS:
        try: receipt(req, "REFUSED", f"kind {req.get('kind')} is not a cancel kind; the cancel lane runs only {sorted(CANCEL_LANE_KINDS)}")
        finally:
            try: shutil.move(str(path), DONE / path.name)
            except Exception: pass
        return
    run_one(path, req, op)


def pool_for(req: dict, production: bool, readers, builder, cancel_lane):
    """Which worker a request runs on: a production cancel kind -> its own lane; any other production kind -> the single production worker; the rest -> the readers."""
    if production and req.get("kind") in CANCEL_LANE_KINDS: return cancel_lane, run_cancel_lane
    return (builder if production else readers), run_one


def interrupted_takes_fence(req: dict, table: dict | None) -> bool:
    """W3W4 rehearsal D10: an operation interrupted by a restart holds the production slot only when its kind is a production kind in the table.
    A read-only kind or a `*_dryrun` (`production: false`) leaves nothing to reconcile, so it never fences. Fail closed: no table, an unknown
    kind or an entry that does not say `production: false` fences."""
    entry = table.get(req.get("kind")) if isinstance(table, dict) else None
    return not (isinstance(entry, dict) and entry.get("production") is False)


def main() -> int:
    for d in (REQ, REC, DONE, ACC, INFLIGHT, TMP, OPS / "sql", EXEC, KY_ROOT / "logs"): d.mkdir(parents=True, exist_ok=True)
    instance_lock = (OPS / "executor.lock").open("a+")
    try: fcntl.flock(instance_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError: return 0                       # another executor owns the boundary
    interrupted = sorted(f.name for f in INFLIGHT.glob("*.json"))
    unfenced = set(); restart_table = None; restart_table_read = False
    for name in interrupted:                               # a restart never re-runs an operation, and never frees the production slot
        f = INFLIGHT / name
        try: req = json.loads(f.read_text())
        except Exception: req = {"operation_id": f.stem}
        if lane_selected(req): unfenced.add(name)
        else:
            if not restart_table_read:
                try: restart_table = load_table()
                except Exception: restart_table = None     # an unreadable table fences every interrupted non-lane operation
                restart_table_read = True
            if not interrupted_takes_fence(req, restart_table): unfenced.add(name)
        receipt(req, "INTERRUPTED", "the executor restarted while this operation was in flight; it was NOT re-run — read the postconditions")
        shutil.move(str(f), DONE / f.name)
    production_interrupted = [name for name in interrupted if name not in unfenced]
    if production_interrupted and not FENCE.exists(): FENCE.write_text(json.dumps({"interrupted": production_interrupted, "ts": now()}))
    table = None; caps = capabilities(False); last_caps = 0.0; last_sync = 0.0
    log("executor up")
    for _, armed in scheduler_backstop_records():
        if armed.get("status") == "ARMED": log(f"{armed.get('operation_id')} scheduler backstop re-armed from disk: resume {armed.get('job')} at {armed.get('resume_by')}")
    readers = cf.ThreadPoolExecutor(max_workers=4, thread_name_prefix="read"); builder = cf.ThreadPoolExecutor(max_workers=1, thread_name_prefix="prod")
    cancel_lane = cf.ThreadPoolExecutor(max_workers=1, thread_name_prefix="cancel")      # SR-CANCEL-LANE: its own worker, so a cancel never queues behind the production operation it stops
    while True:
        if (RUN / "STOP_executor").exists(): log("STOP_executor present; no new operations; exiting when idle"); readers.shutdown(wait=True); builder.shutdown(wait=True); cancel_lane.shutdown(wait=True); return 0
        scheduler_backstop_tick()                            # SR-J3-REAPER-PAUSE: before every gate below; the first turn after a restart fires an overdue resume at once
        if time.time() - last_sync > 60:
            try:
                sync()
                refresh_from_main_or_fail_closed()           # A8 §5: a refused refresh is logged REFRESH_REFUSED and recorded; this snapshot keeps serving
                table = load_table()
            except Exception as e: log(f"sync failed: {e}"); table = None
            last_sync = time.time()
        if capabilities_due(last_caps, time.time()): caps = capabilities(table is not None); last_caps = time.time()
        if table is None or (KY_ROOT / "HOLD").exists(): time.sleep(LOOP_TICK_S); continue      # no table on main yet (before B-1), refs unreachable, or HOLD
        if FENCE.exists(): fence_quiescent()  # reconcile independent small-test completion; retain the owner-controlled fence
        publish_teardown_completions()        # SR-TEARDOWN-COMPLETION: a committed teardown + its accepted absence complete without a fence
        publish_head_completions()            # M-W56-16: a committed head change + its independent readback and accepted digest complete without a fence
        for f in sorted(REQ.glob("*.json")):
            try: req = json.loads(f.read_text())
            except Exception as e:
                receipt({"operation_id": f.stem}, "REFUSED", f"unreadable request: {e}"); shutil.move(str(f), DONE / f.name); continue
            production = bool((table.get(req.get("kind")) or {}).get("production")) and not lane_selected(req)
            if production and FENCE.exists() and req.get("kind") not in FENCE_EXEMPT_KINDS: continue      # the single production slot is taken; the request waits where it is (FENCE_EXEMPT_KINDS: neither a resume of the watchdog nor a cancel waits)
            why = validate(req, table, caps)
            if why:
                receipt(req, "REFUSED", why, preserve_existing=True); shutil.move(str(f), DONE / f.name); continue
            if production and req["kind"] not in CANCEL_LANE_KINDS and remote_async(req["kind"], table[req["kind"]]):     # A8 §3.11: a synchronous kind takes no fence
                FENCE.write_text(json.dumps({"operation_id": req["operation_id"], "request_sha256": request_digest(req), "ts": now()}))
            mark_seen(req["idempotency_key"], req["operation_id"])
            flight = INFLIGHT / f.name; shutil.move(str(f), flight)
            op = table[req["kind"]]
            receipt(req, "RUNNING", "accepted; in flight")
            pool, work = pool_for(req, production, readers, builder, cancel_lane)
            pool.submit(work, flight, req, op)
        time.sleep(LOOP_TICK_S)


if __name__ == "__main__":
    sys.exit(main())
