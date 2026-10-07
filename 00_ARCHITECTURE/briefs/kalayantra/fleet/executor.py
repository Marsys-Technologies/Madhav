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
GIT = KY_ROOT / "wt" / "campaign"            # used ONLY as a handle on the shared object store (fetch / show / merge-base / worktree)
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
    return (isinstance(request_sha256, str) and re.fullmatch(r"[0-9a-f]{64}", request_sha256) is not None
            and proof.get("operation_id") == operation_id and proof.get("request_sha256") == request_sha256
            and proof.get("result") == "ACCEPTED"
            and proof.get("by") in ("v1", "v2") and bool(proof.get("ts")))

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
    if out:                                           # the complete output is evidence; the tail alone must never be mistaken for it
        body = redact(out); output_path = REC / f"{name}.output.txt"; output_path.write_text(body)
        r["output_file"] = str(output_path); r["output_sha256"] = hashlib.sha256(body.encode()).hexdigest(); r["output_bytes"] = len(body.encode())
    if extra: r.update(extra)
    with _lock: (REC / f"{name}.json").write_text(json.dumps(r, indent=1))
    log(f"{name} {status} {reason}")


def validate(req: dict, table: dict, caps: dict, reserved: bool = False) -> str | None:
    for k in ("operation_id", "kind", "item_id", "idempotency_key", "requested_by", "kyd"):
        if not req.get(k): return f"missing field {k}"
    if not SAFE_ID.match(str(req["operation_id"])): return "operation_id has unsafe characters"
    op = table.get(req["kind"])
    if not op: return f"unknown kind {req['kind']}"
    if not op.get("enabled"): return f"kind {req['kind']} is not enabled (enabled_by {op.get('enabled_by')})"
    if "TO_BE_SET" in op.get("script", "") or "TO_BE_SET" in str(op.get("needs", "")): return "operation script not yet reviewed/landed"
    if req["requested_by"] not in op.get("requesters", ["adhikarin"]): return f"requested_by {req['requested_by']} may not request {req['kind']}"
    if not caps.get(op["needs"], False): return f"capability_missing: {op['needs']}"
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
        if a.get("result") != "ACCEPTED" or a.get("operation_id") != req["operation_id"] or a.get("by") not in ("v1", "v2"):
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
    return None


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
    oid = req["operation_id"]; script = op["script"]; args: list[str] = list(op.get("fixed_args", []))
    for k, v in (req.get("args") or {}).items(): args += [f"--{k}", str(v)]
    timeout = min(int(req.get("timeout_s", op.get("timeout_s", 3600))), MAX_TIMEOUT)
    env = {k: v for k, v in os.environ.items() if k in CHILD_ENV_ALLOW}          # neither privileged connection reaches a child by default
    if op["needs"] == "builder": env["DATABASE_URL"] = os.environ["KY_BUILDER_DATABASE_URL"]
    elif op["needs"] == "owner": env["DATABASE_URL"] = os.environ["KY_OWNER_DATABASE_URL"]
    env["SE_EPHE_PATH"] = os.environ.get("SE_EPHE_PATH", str(KY_ROOT / "ephe")); env["KY_ROOT"] = str(KY_ROOT)
    if not op.get("production"):
        src = git("show", f"origin/main:{script}")
        if src.returncode != 0: return 127, f"script {script} is not on origin/main"
        tmp = TMP / f"{oid}.{pathlib.Path(script).name}"; tmp.write_text(src.stdout); tmp.chmod(0o700)
        argv = ([PY, str(tmp)] if script.endswith(".py") else ["bash", str(tmp)]) + args
        try:
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
    for name in interrupted:                               # a restart never re-runs an operation, and never frees the production slot
        f = INFLIGHT / name
        try: req = json.loads(f.read_text())
        except Exception: req = {"operation_id": f.stem}
        receipt(req, "INTERRUPTED", "the executor restarted while this operation was in flight; it was NOT re-run — read the postconditions")
        shutil.move(str(f), DONE / f.name)
    if interrupted and not FENCE.exists(): FENCE.write_text(json.dumps({"interrupted": interrupted, "ts": now()}))
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
        for f in sorted(REQ.glob("*.json")):
            try: req = json.loads(f.read_text())
            except Exception as e:
                receipt({"operation_id": f.stem}, "REFUSED", f"unreadable request: {e}"); shutil.move(str(f), DONE / f.name); continue
            production = bool((table.get(req.get("kind")) or {}).get("production"))
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
