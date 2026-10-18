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
goes to <operation_id>.output.txt with its sha256) → move the request to run/ops/done/.

Production approval binds the request (A8 §3.9): ONE verifier lane's acceptance receipt carries the sha256 of the request as
sorted compact JSON without the fields that may lawfully change after signing — `acceptance_receipt`, `expires_at` and any
`*_expires_at` lease-expiry field (see request_digest) — plus the attestations the kind needs: `dry_run_passed` for a mutating
kind and `backup_taken` for a `*_teardown`. It is valid from its timestamp until the request's `expires_at`; there is no age cap.
The lease must be the ONLY unexpired ACTIVE row of the shared lease table. `*_dryrun` kinds are `production: false` — read-only
with a credential: no lease, acceptance or fence, but a merged `reviewed_commit` (they run in its tree) and a rollback proof in
the receipt.

The production slot is a FENCE file, run/ops/PRODUCTION_PENDING.json. Only a REMOTE-ASYNCHRONOUS kind takes it (A8 §3.11: the
table's `remote_async: true`, or a named dispatch / century / verification job) — written before the operation starts and
RETAINED afterwards — success, failure or interruption — because a dispatch returns while its remote job still runs. Only the
owner surrogate removes it, after the quiescence receipt for that request. Synchronous production kinds take no fence (the one
production worker serialises them); read-only operations are not fenced and run in parallel. A production operation in flight
at a restart is NEVER re-run: its receipt says INTERRUPTED. A refused executor refresh (HOLD, STOP, queued or in-flight work,
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
TEARDOWN_KINDS = ("smalltest_teardown", "measuring_teardown", "century_teardown")   # the committed teardowns that wait for an independent absence
LAUNCH_SCHEMAS = {"smalltest_dispatch": "ky.smalltest_launch/1", "measuring_dispatch": "ky.measuring_launch/1", "century_dispatch": "ky.century_launch/1"}
REMOTE_ASYNC_KINDS = frozenset({"smalltest_dispatch", "measuring_dispatch", "century_dispatch", "verification_job"})   # A8 §3.11: work continues remotely after the child returns — fenced even if a table drops `remote_async`
REFRESH = OPS / "EXECUTOR_REFRESH.json"
SCHEDULER_JOB = "watchdog-reaper"   # platform/scripts/provision_watchdog_scheduler.sh creates exactly this job ...
SCHEDULER_PROJECT = "madhav-astrology"   # ... in this project (GCP_PROJECT default) ...
SCHEDULER_REGION = "asia-south1"   # ... and this region (GCP_REGION default)
SCHEDULER_SCRIPT = "00_ARCHITECTURE/briefs/kalayantra/fleet/scheduler_reaper.py"   # the one reviewed script every scheduler kind (and the backstop) runs
SCHEDULER_ACTION = {"scheduler_readback": "readback", "scheduler_pause_dryrun": "pause", "scheduler_pause": "pause", "scheduler_resume_dryrun": "resume", "scheduler_resume": "resume"}
SCHEDULER_STATES = ("ENABLED", "PAUSED", "DISABLED", "UPDATE_FAILED")   # google.cloud.scheduler.v1.Job.State values a record may report
SCHEDULER_UTC = re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:Z|\+00:00)")
SCHEDULER_BACKSTOP = OPS / "scheduler_backstop"
_lock = threading.Lock()


def now() -> str: return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
def redact(s: str) -> str:
    for rx in REDACT: s = rx.sub("[REDACTED]", s)
    return s
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

def capabilities(table_on_main: bool) -> dict:
    caps = {"builder": bool(os.environ.get("KY_BUILDER_DATABASE_URL")), "owner": bool(os.environ.get("KY_OWNER_DATABASE_URL")),
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
    rc, out = 127, ""
    try:
        if not SHA.fullmatch(commit) or git("merge-base", "--is-ancestor", commit, "origin/main").returncode: raise ValueError("reviewed commit is not merged")
        source = git("show", f"{commit}:{SCHEDULER_SCRIPT}")
        if source.returncode: raise ValueError("resume script unreadable at the reviewed commit")
        script = TMP / f"{oid}.scheduler_reaper.py"; script.write_text(source.stdout)
        env = {k: v for k, v in os.environ.items() if k in CHILD_ENV_ALLOW}
        env["KY_OPERATION_REQUEST"] = json.dumps(req, sort_keys=True, separators=(",", ":")); env["KY_ROOT"] = str(KY_ROOT)
        try: p = run_group([PY, str(script), "--action", "resume", "--job", SCHEDULER_JOB], KY_ROOT, env, 600); rc, out = p.returncode, (p.stdout or "") + "\n" + (p.stderr or "")
        finally: script.unlink(missing_ok=True)
    except Exception as e: out = f"backstop could not run: {type(e).__name__}: {redact(str(e))}"
    proof, problem = scheduler_proof(req, rc, out)
    ok = rc == 0 and problem is None and proof is not None and proof.get("state") == "ENABLED"
    receipt(req, "COMPLETED" if ok else "FAILED", "" if ok else (problem or "backstop resume did not read back ENABLED"), rc, out,
            {"scheduler": proof, "backstop_for": record.get("operation_id"), "attempt": attempt})
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


def measuring_cancel_problem(req: dict) -> str | None:
    """SR-J3-CANCEL-NULL 2(a) admission for `measuring_cancel`, run at the tail of validate (so again immediately before execution): the target
    execution is the one the J-3c `measuring_dispatch` receipt named, and an ABORT / stall verdict is cited; both are cited by file name + sha256 and
    read back byte for byte from run/ops/receipts and run/ops/verdicts. A missing or altered file, a different execution, CONTINUE and NULL all refuse."""
    if req.get("kind") not in ("measuring_cancel", "measuring_cancel_dryrun"): return None
    target = (req.get("args") or {}).get("execution")
    if not (isinstance(target, str) and re.fullmatch(r"brahma-build-pipeline-job-[a-z0-9]+(?:-[a-z0-9]+)*", target)): return "execution must be a brahma-build-pipeline-job execution name"
    if req.get("item_id") != "J-3c": return "measuring cancel belongs to J-3c"
    def cited(folder: str, ref) -> dict | None:
        if not (isinstance(ref, dict) and re.fullmatch(r"[A-Za-z0-9_.-]+\.json", str(ref.get("name", "")))): return None
        path = OPS / folder / ref["name"]
        try:
            if path.resolve().parent != (OPS / folder).resolve(): return None
            body = path.read_bytes(); value = json.loads(body)
        except (OSError, ValueError): return None
        return value if isinstance(value, dict) and digest_bytes(body) == ref.get("sha256") else None
    dispatch = cited("receipts", req.get("dispatch_receipt"))
    if dispatch is None: return "the cited measuring_dispatch receipt is missing, unreadable or does not match its sha256"
    launch = dispatch.get("launch") if isinstance(dispatch.get("launch"), dict) else {}
    if (dispatch.get("kind") != "measuring_dispatch" or dispatch.get("status") != "COMPLETED" or dispatch.get("exit_code") != 0 or dispatch.get("item_id") != "J-3c"
            or req["dispatch_receipt"]["name"] != f"{dispatch.get('operation_id')}.json" or launch.get("status") != "LAUNCHED"):
        return "the cited receipt is not the COMPLETED launch of a J-3c measuring_dispatch"
    if launch.get("execution_name") != target: return "the target execution is not the execution named in the cited measuring_dispatch receipt"
    verdict = cited("verdicts", req.get("verdict"))
    if verdict is None: return "the cited ABORT/stall verdict file is missing, unreadable or does not match its sha256"
    form = re.fullmatch(r"ky\.(reproject|stall)_verdict/\d+", str(verdict.get("schema")))
    if not form or verdict.get("verdict") != {"reproject": "ABORT", "stall": "STALL"}[form.group(1)]: return "the cited verdict is not an ABORT or stall verdict (CONTINUE and NULL never cancel)"
    return None


def measuring_cancel_proof(req: dict, rc: int | None, out: str) -> tuple[dict | None, str | None]:
    """(record, problem) for `measuring_cancel`'s (or its dry run's) complete output. `record` is the ONE ky.measuring_cancel/1 line when it names this
    operation, this request digest, this kind and exactly the targeted execution of the measuring job (else None); `problem` is None only when the state
    read back after the action is CANCELLED (a dry run: when it planned and called nothing). An exit status alone proves nothing, and any other observed
    state is a failure whatever the exit status."""
    dry = req.get("kind") == "measuring_cancel_dryrun"; found = []
    for line in out.splitlines():
        try: value = json.loads(line)
        except ValueError: continue
        if isinstance(value, dict) and value.get("schema") == "ky.measuring_cancel/1": found.append(value)
    if len(found) != 1: return None, "cancel record missing or not unique"
    rec = found[0]       # the project / region / job below are cloudrun_readback.py's constants
    if (rec.get("execution") != (req.get("args") or {}).get("execution") or (rec.get("project"), rec.get("region"), rec.get("job")) != ("madhav-astrology", "asia-south1", "brahma-build-pipeline-job")
            or rec.get("operation_id") != req.get("operation_id") or rec.get("request_sha256") != request_digest(req) or rec.get("dry_run") is not dry):
        return None, "cancel record does not bind this operation, request and targeted execution"
    if dry:
        if rc == 0 and not (rec.get("status") == "DRY_RUN" and rec.get("gcloud_calls") == 0 and rec.get("state") is None and rec.get("changed") is False):
            return rec, "the dry-run record does not prove a plan with no external call"
    elif rc == 0 and not (rec.get("status") == "OK" and rec.get("state") == "CANCELLED"):
        return rec, f"the execution was not read back CANCELLED (observed state: {rec.get('state')})"
    return rec, None


def receipt(req: dict, status: str, reason: str = "", rc: int | None = None, out: str = "", extra: dict | None = None, stdout: str | None = None) -> None:
    """`out` is the complete evidence (stdout, then stderr). `stdout` is the child's stdout alone: the one stream a whole-document proof is parsed from,
    because a child may lawfully print advisory lines on stderr. A caller that does not pass it supplies no proof stream, so such a proof reads as missing."""
    name = req.get("operation_id") if SAFE_ID.match(str(req.get("operation_id", ""))) else "unknown"
    r = {"operation_id": req.get("operation_id"), "kind": req.get("kind"), "item_id": req.get("item_id"), "status": status, "reason": reason,
         "exit_code": rc, "stdout_tail": redact(out[-20000:]), "ts": now(), "reviewed_commit": req.get("reviewed_commit"),
         "requested_by": req.get("requested_by"), "kyd": req.get("kyd"), "request_sha256": request_digest(req) if req.get("kind") else None}
    if lane_selected(req):
        receipt_lane(req, r, status, rc, out)
    if out:                                           # the complete output is evidence; the tail alone must never be mistaken for it
        body = redact(out); output_path = REC / f"{name}.output.txt"; output_path.write_text(body)
        r["output_file"] = str(output_path); r["output_sha256"] = hashlib.sha256(body.encode()).hexdigest(); r["output_bytes"] = len(body.encode())
    if req.get("kind") == "measuring_dispatch_dryrun" and status == "COMPLETED":
        try:
            proof = json.loads(stdout or "")                      # stdout only: the advisory lines on stderr are evidence, never part of the proof
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
    if req.get("kind") == "century_dispatch_dryrun" and status == "COMPLETED":
        try:
            proof = json.loads(out)
            manifest = proof.get("plan_manifest") or {}
            valid = (rc == 0 and proof.get("schema") == "ky.century_staging/1"
                and proof.get("status") == "ROLLED_BACK" and proof.get("rollback_confirmed") is True
                and proof.get("operation_id") == req["operation_id"] and proof.get("request_sha256") == request_digest(req)
                and proof.get("args") == req.get("args") and manifest.get("chart_id") == CANONICAL_CHART
                and manifest.get("scope_target") == "ka_gochara_v5"
                and proof.get("triggered_by") == "gochara-v5-century" and "gochara_v5_test_slice" not in manifest    # a century run carries NO slice marker
                and proof.get("plan_manifest_digest") == digest_bytes(json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()))
        except (ValueError, TypeError, AttributeError):
            valid = False
        if valid:
            r["staging"] = proof
        else:
            r.update(status="FAILED", reason="bound century staging rollback proof missing; reconcile transaction outcome")
    if not lane_selected(req) and req.get("kind") in ("smalltest_dispatch", "measuring_dispatch", "century_dispatch") and status == "COMPLETED":
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
    overlay = overlay_proofs().pop(str(req.get("operation_id")), None)
    if overlay: r["generated_overlay"] = overlay                 # the proof the executor itself measured, never the child's words
    if extra: r.update(extra)
    with _lock: (REC / f"{name}.json").write_text(json.dumps(r, indent=1))
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
                               "century_dispatch", "century_dispatch_dryrun", "century_teardown", "century_teardown_dryrun"):
        return None
    try:
        policy_name = {"measuring": "measuring_request_problem", "century": "century_request_problem"}.get(req["kind"].split("_")[0], "smalltest_request_problem")
        return smalltest_policy(req)[policy_name](req, OPS)
    except Exception:
        return "reviewed small-test evidence policy unavailable or invalid"


def validate(req: dict, table: dict, caps: dict, reserved: bool = False) -> str | None:
    for k in ("operation_id", "kind", "item_id", "idempotency_key", "requested_by", "kyd"):
        if not req.get(k): return f"missing field {k}"
    if not SAFE_ID.match(str(req["operation_id"])): return "operation_id has unsafe characters"
    op = table.get(req["kind"])
    if not op: return f"unknown kind {req['kind']}"
    if not op.get("enabled"): return f"kind {req['kind']} is not enabled (enabled_by {op.get('enabled_by')})"
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
        kind = req["kind"]; required = []                                        # A8 §5: `required_rows` and `restore_verified` are retired as preconditions
        if kind.endswith("_teardown"): required.append("backup_taken")
        if kind not in ("backup_snapshot", "backup_restore_verify") and not kind.endswith("_dryrun"): required.append("dry_run_passed")
        if any((a.get("checks") or {}).get(k) is not True for k in required): return "required backup/restore/dry-run attestation missing"
    if not reserved and seen(req["idempotency_key"]): return "idempotency key already used"
    return smalltest_policy_problem(req) or scheduler_policy_problem(req) or measuring_cancel_problem(req)


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


def child_stdouts(_store: dict = {}) -> dict:
    """In-memory hand-off of each operation's child stdout (alone, without stderr) from execute() to receipt(); execute() keeps returning the
    combined output that is the evidence file."""
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
        return p.returncode, (p.stdout or "") + "\n" + (p.stderr or "")


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
        child_stdouts()[oid] = p.stdout or ""
        return p.returncode, (p.stdout or "") + "\n" + (p.stderr or "")
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
        child_stdouts()[oid] = p.stdout or ""
        return p.returncode, (p.stdout or "") + "\n" + (p.stderr or "")
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
    needs_remote = done.get("kind") in ("smalltest_dispatch", "measuring_dispatch", "century_dispatch") or isinstance(done.get("launch"), dict)
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
        stdout = child_stdouts().pop(req["operation_id"], None)
        extra = None if lane_selected(req) else {"session_marker": session_marker(req["operation_id"])}
        proof, problem = scheduler_proof(req, rc, out) if extra is not None and req["kind"] in SCHEDULER_ACTION else (None, None)
        if proof is not None: extra["scheduler"] = proof        # the state read back AFTER the action, as the reviewed script measured it
        cancelled, cancel_problem = measuring_cancel_proof(req, rc, out) if extra is not None and req["kind"] in ("measuring_cancel", "measuring_cancel_dryrun") else (None, None)
        if cancelled is not None: extra["cancel"] = cancelled   # likewise: the execution state read back after the cancel (CANCELLED, or the observed state beside a FAILED receipt)
        ok = rc == 0 and problem is None and cancel_problem is None
        receipt(req, "COMPLETED" if ok else "FAILED", "" if ok else (problem or cancel_problem or "non-zero exit (read the postconditions; an exit status proves nothing)"), rc, out, extra, stdout)
        if ok and req["kind"] == "scheduler_resume": scheduler_backstop_satisfy(req)
    except subprocess.TimeoutExpired as e:
        receipt(req, "FAILED", "timeout — the local process group was killed; a remote job may still be running: read the postconditions", 124, str(e))
    except Exception as e:
        receipt(req, "FAILED", f"executor error: {type(e).__name__}: {redact(str(e))}")
    finally:
        try: shutil.move(str(path), DONE / path.name)
        except Exception: pass
        mechanical_acceptance(req, DONE / path.name)


def main() -> int:
    for d in (REQ, REC, DONE, ACC, INFLIGHT, TMP, OPS / "sql", EXEC, KY_ROOT / "logs"): d.mkdir(parents=True, exist_ok=True)
    instance_lock = (OPS / "executor.lock").open("a+")
    try: fcntl.flock(instance_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError: return 0                       # another executor owns the boundary
    interrupted = sorted(f.name for f in INFLIGHT.glob("*.json"))
    lane_interrupted = set()
    for name in interrupted:                               # a restart never re-runs an operation, and never frees the production slot
        f = INFLIGHT / name
        try: req = json.loads(f.read_text())
        except Exception: req = {"operation_id": f.stem}
        if lane_selected(req): lane_interrupted.add(name)
        receipt(req, "INTERRUPTED", "the executor restarted while this operation was in flight; it was NOT re-run — read the postconditions")
        shutil.move(str(f), DONE / f.name)
    production_interrupted = [name for name in interrupted if name not in lane_interrupted]
    if production_interrupted and not FENCE.exists(): FENCE.write_text(json.dumps({"interrupted": production_interrupted, "ts": now()}))
    table = None; caps = capabilities(False); last_caps = 0.0; last_sync = 0.0
    log("executor up")
    for _, armed in scheduler_backstop_records():
        if armed.get("status") == "ARMED": log(f"{armed.get('operation_id')} scheduler backstop re-armed from disk: resume {armed.get('job')} at {armed.get('resume_by')}")
    readers = cf.ThreadPoolExecutor(max_workers=4, thread_name_prefix="read"); builder = cf.ThreadPoolExecutor(max_workers=1, thread_name_prefix="prod")
    while True:
        if (RUN / "STOP_executor").exists(): log("STOP_executor present; no new operations; exiting when idle"); readers.shutdown(wait=True); builder.shutdown(wait=True); return 0
        scheduler_backstop_tick()                            # SR-J3-REAPER-PAUSE: before every gate below; the first turn after a restart fires an overdue resume at once
        if time.time() - last_sync > 60:
            try:
                sync()
                refresh_from_main_or_fail_closed()           # A8 §5: a refused refresh is logged REFRESH_REFUSED and recorded; this snapshot keeps serving
                table = load_table()
            except Exception as e: log(f"sync failed: {e}"); table = None
            last_sync = time.time()
        if time.time() - last_caps > 300: caps = capabilities(table is not None); last_caps = time.time()
        if table is None or (KY_ROOT / "HOLD").exists(): time.sleep(10); continue      # no table on main yet (before B-1), refs unreachable, or HOLD
        if FENCE.exists(): fence_quiescent()  # reconcile independent small-test completion; retain the owner-controlled fence
        for f in sorted(REQ.glob("*.json")):
            try: req = json.loads(f.read_text())
            except Exception as e:
                receipt({"operation_id": f.stem}, "REFUSED", f"unreadable request: {e}"); shutil.move(str(f), DONE / f.name); continue
            production = bool((table.get(req.get("kind")) or {}).get("production")) and not lane_selected(req)
            if production and FENCE.exists() and req.get("kind") not in ("scheduler_resume", "measuring_cancel"): continue      # the single production slot is taken; the request waits where it is (a resume of the watchdog is the safe direction and a cancel stops the very dispatch that holds the fence: neither waits)
            why = validate(req, table, caps)
            if why:
                receipt(req, "REFUSED", why); shutil.move(str(f), DONE / f.name); continue
            if production and remote_async(req["kind"], table[req["kind"]]):     # A8 §3.11: a synchronous kind takes no fence
                FENCE.write_text(json.dumps({"operation_id": req["operation_id"], "request_sha256": request_digest(req), "ts": now()}))
            mark_seen(req["idempotency_key"], req["operation_id"])
            flight = INFLIGHT / f.name; shutil.move(str(f), flight)
            op = table[req["kind"]]
            receipt(req, "RUNNING", "accepted; in flight")
            (builder if production else readers).submit(run_one, flight, req, op)
        time.sleep(10)


if __name__ == "__main__":
    sys.exit(main())
