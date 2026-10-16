#!/usr/bin/env python3
"""KĀLA-YANTRA fixed-operation executor v1.2 (charter §7) — the ONLY process that holds a production credential.

What it trusts: nothing an agent can edit in a working tree. The operations table and every script it runs are read from
`origin/main` — i.e. only what was reviewed and merged:
  · the table            git show origin/main:00_ARCHITECTURE/briefs/kalayantra/fleet/executor_ops.json
  · a read-only op       its script is extracted from origin/main into run/ops/tmp/ and run from there
  · a production op      a private worktree at the request's `reviewed_commit` (which must be an ancestor of origin/main)
                         is created under $KY_ROOT/exec/, the mapped command runs there, the worktree is removed

Loop: read run/ops/requests/*.json → validate → (production: take the single production slot) → validate AGAIN immediately
before execution → run in its own process group → write run/ops/receipts/<operation_id>.json (redacted; the complete output
goes to <operation_id>.output.txt with its sha256) → move the request to run/ops/done/.

Production approval binds the COMPLETE request: the verifier's acceptance receipt carries the sha256 of the request (sorted
compact JSON, without the `acceptance_receipt` field), a timestamp, the checklist rows the operation's table entry requires
and the backup / restore / dry-run attestations. The lease must be the ONLY unexpired ACTIVE row of the shared lease table.

The production slot is a FENCE file, run/ops/PRODUCTION_PENDING.json. It is written before a production operation starts and
is RETAINED afterwards — success, failure or interruption — because a dispatch can return while its remote job still runs.
Only the owner surrogate removes it, after the verifier's quiescence receipt for that request. Read-only operations are not
fenced and run in parallel. A production operation in flight at a restart is NEVER re-run: its receipt says INTERRUPTED.
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
APPROVAL_MAX_AGE_S = 3 * 3600      # an acceptance is written in the verifier's cycle and used in the surrogate's next one
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
            and proof.get("by") in ("v1", "v2", "v3", "v4") and bool(proof.get("ts")))
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
    """Refresh this snapshot, returning true only when it is safe to admit work.

    A changed source is atomically staged and then exec'd in this same
    credential-bearing process.  A failed or unsafe refresh deliberately
    leaves this process alive but closes admission rather than running a
    stale snapshot against new requests.
    """
    before = running_revision()
    why = handover_from_main()
    if why:
        REFRESH.write_text(json.dumps({"result": "REFUSED", "reason": why, "ts": now()}, indent=1))
        log(f"executor refresh refused: {why}")
        return False
    if running_revision() != before:
        os.execv(PY, [PY, str(EXEC / "executor.py")])
    source = main_executor_source()
    commit = main_revision()
    if source is None or commit is None or digest_bytes(source) != running_revision():
        REFRESH.write_text(json.dumps({"result": "REFUSED", "reason": "running revision cannot be proven current", "ts": now()}, indent=1))
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
    bound = {k: v for k, v in req.items() if k != "acceptance_receipt"}
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
            if not issued <= current < expires or (current - issued).total_seconds() > APPROVAL_MAX_AGE_S: return "approval expired or not yet valid"
        except (KeyError, TypeError, ValueError): return "valid approval timestamp and a timezone-qualified request expires_at required"
        if a.get("request_sha256") != request_digest(req): return "approval does not bind the complete request"
        kind = req["kind"]; required = []
        if kind != "backup_snapshot": required.append("backup_taken")
        if kind not in ("backup_snapshot", "backup_restore_verify"): required.append("restore_verified")
        if kind not in ("backup_snapshot", "backup_restore_verify") and not kind.endswith("_dryrun"):
            required.append("dry_run_passed")
            if any((a.get("rows") or {}).get(k) is not True for k in op.get("required_rows", [])): return "required pre-acceptance rows are not all true"
        if any((a.get("checks") or {}).get(k) is not True for k in required): return "required backup/restore/dry-run attestation missing"
    if not reserved and seen(req["idempotency_key"]): return "idempotency key already used"
    return smalltest_policy_problem(req)


def lane_selected(req: dict) -> bool:
    return "lane_target" in req


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
    if "lane_receipts" in req:
        try: lane_qualification(req)
        except (ValueError, OSError, KeyError, TypeError): return "lane qualification receipts missing, mismatched or incomplete"
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
        # Stage immutable evidence bytes for the separately connected observer.
        # It rechecks every digest after this copy, so races fail closed.
        if "lane_receipts" in req:
            staged = scratch / "run/ops/receipts"; staged.mkdir(parents=True)
            for ref in req["lane_receipts"]:
                for name in (ref["name"], ref["name"][:-5] + ".output.txt"):
                    (staged / name).write_bytes((REC / name).read_bytes())
        env = lane_child_env(req, scratch)
        env["PYTHONPATH"] = str(source / "platform/python-sidecar")
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
    env["SE_EPHE_PATH"] = os.environ.get("SE_EPHE_PATH", str(KY_ROOT / "ephe")); env["KY_ROOT"] = str(KY_ROOT)
    if not op.get("production"):
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
        p = run_group(argv, cwd, env, timeout)
        return p.returncode, (p.stdout or "") + "\n" + (p.stderr or "")
    finally:
        git("worktree", "remove", "--force", str(wt), timeout=300)


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
        receipt(req, "COMPLETED" if rc == 0 else "FAILED", "" if rc == 0 else "non-zero exit (read the postconditions; an exit status proves nothing)", rc, out)
    except subprocess.TimeoutExpired as e:
        receipt(req, "FAILED", "timeout — the local process group was killed; a remote job may still be running: read the postconditions", 124, str(e))
    except Exception as e:
        receipt(req, "FAILED", f"executor error: {type(e).__name__}: {redact(str(e))}")
    finally:
        try: shutil.move(str(path), DONE / path.name)
        except Exception: pass


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
                table = load_table() if refresh_from_main_or_fail_closed() else None
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
            if production: FENCE.write_text(json.dumps({"operation_id": req["operation_id"], "request_sha256": request_digest(req), "ts": now()}))
            mark_seen(req["idempotency_key"], req["operation_id"])
            flight = INFLIGHT / f.name; shutil.move(str(f), flight)
            op = table[req["kind"]]
            receipt(req, "RUNNING", "accepted; in flight")
            (builder if production else readers).submit(run_one, flight, req, op)
        time.sleep(10)


if __name__ == "__main__":
    sys.exit(main())
