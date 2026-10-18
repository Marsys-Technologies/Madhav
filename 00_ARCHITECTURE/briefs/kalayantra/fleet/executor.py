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
REMOTE_ASYNC_KINDS = frozenset({"smalltest_dispatch", "measuring_dispatch", "century_dispatch", "verification_job"})   # A8 §3.11: work continues remotely after the child returns — fenced even if a table drops `remote_async`
REFRESH = OPS / "EXECUTOR_REFRESH.json"
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
            "layer_verifier": bool(os.environ.get("KY_LAYER_VERIFIER_DATABASE_URL")),
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
        if committed.get("kind") in ("smalltest_teardown", "measuring_teardown"):
            policy = smalltest_policy(committed)
            observed = policy["absence_evidence"](proof, OPS, teardown_receipt=committed)
            completion = dict(schema="ky.measuring_completion/1" if committed["kind"] == "measuring_teardown" else "ky.smalltest_completion/1", status="COMPLETED", operation_id=operation_id,
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


def receipt(req: dict, status: str, reason: str = "", rc: int | None = None, out: str = "", extra: dict | None = None) -> None:
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
            proof = json.loads(out)
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
    if not lane_selected(req) and req.get("kind") in ("smalltest_dispatch", "measuring_dispatch") and status == "COMPLETED":
        # A staging UUID/exit zero is never launch evidence. Only the reviewed
        # wrapper's machine record binds the exact run and remote execution.
        records = []
        for line in out.splitlines():
            try:
                value = json.loads(line)
            except (ValueError, TypeError):
                continue
            if isinstance(value, dict) and value.get("schema") == ("ky.measuring_launch/1" if req["kind"] == "measuring_dispatch" else "ky.smalltest_launch/1"):
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
    if not lane_selected(req) and req.get("kind") in ("smalltest_teardown", "smalltest_teardown_dryrun", "measuring_teardown", "measuring_teardown_dryrun") and status == "COMPLETED":
        records = []
        for line in out.splitlines():
            if line.startswith("teardown_proof\t"):
                try: records.append(json.loads(line.split("\t", 1)[1]))
                except ValueError: pass
        proof = records[0] if len(records) == 1 else {}
        expected = "ROLLED_BACK" if req["kind"].endswith("_dryrun") else "COMMITTED_AWAITING_ABSENCE"
        measuring = req["kind"].startswith("measuring_")
        scope = req.get("measuring_scope" if measuring else "smalltest_scope")
        if (rc == 0 and isinstance(proof, dict) and proof.get("schema") == ("ky.measuring_teardown/1" if measuring else "ky.smalltest_teardown/1") and proof.get("status") == expected
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
                               "measuring_dispatch", "measuring_dispatch_dryrun", "measuring_teardown", "measuring_teardown_dryrun"):
        return None
    try:
        policy_name = "measuring_request_problem" if req["kind"].startswith("measuring_") else "smalltest_request_problem"
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
    return smalltest_policy_problem(req)


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
    elif op["needs"] == "layer_verifier": env["DATABASE_URL"] = os.environ["KY_LAYER_VERIFIER_DATABASE_URL"]
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
    needs_remote = done.get("kind") in ("smalltest_dispatch", "measuring_dispatch") or isinstance(done.get("launch"), dict)
    remote = None
    if needs_remote:
        try: remote = accepted_cloudrun_execution(str(args.get("execution_readback", "")), str((done.get("launch") or {}).get("execution_name", "")))
        except (OSError, ValueError, TypeError, AttributeError): remote = None
    try: after_terminal = utc_time(sessions["measured_at"]) >= utc_time(done["ts"])
    except (KeyError, TypeError, ValueError): after_terminal = False
    checks = dict(own_checks,
        target_is_a_production_operation=entry.get("production") is True and "lane_target" not in done,
        target_is_not_a_teardown=done.get("kind") not in ("smalltest_teardown", "measuring_teardown"),
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
        rc, out = execute(req, op)
        receipt(req, "COMPLETED" if rc == 0 else "FAILED", "" if rc == 0 else "non-zero exit (read the postconditions; an exit status proves nothing)", rc, out,
                None if lane_selected(req) else {"session_marker": session_marker(req["operation_id"])})
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
    readers = cf.ThreadPoolExecutor(max_workers=4, thread_name_prefix="read"); builder = cf.ThreadPoolExecutor(max_workers=1, thread_name_prefix="prod")
    while True:
        if (RUN / "STOP_executor").exists(): log("STOP_executor present; no new operations; exiting when idle"); readers.shutdown(wait=True); builder.shutdown(wait=True); return 0
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
            if production and FENCE.exists(): continue      # the single production slot is taken; the request waits where it is
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
