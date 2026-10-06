#!/usr/bin/env python3
"""KĀLA-YANTRA fixed-operation executor v1.1 (charter §7) — the ONLY process that holds a production credential.

What it trusts: nothing an agent can edit in a working tree. The operations table and every script it runs are read from
`origin/main` — i.e. only what was reviewed and merged:
  · the table            git show origin/main:00_ARCHITECTURE/briefs/kalayantra/fleet/executor_ops.json
  · a read-only op       its script is extracted from origin/main into run/ops/tmp/ and run from there
  · a production op      a private worktree at the request's `reviewed_commit` (which must be an ancestor of origin/main)
                         is created under $KY_ROOT/exec/, the mapped command runs there, the worktree is removed

Loop: read run/ops/requests/*.json → validate → run → write run/ops/receipts/<operation_id>.json (redacted) → move the
request to run/ops/done/. Agents never see the credential; they read receipts. Read-only operations run in parallel;
production operations run ONE AT A TIME (one build slot). A request that fails validation is refused with a receipt
naming the reason. A production operation interrupted by a restart is NEVER re-run: its receipt says INTERRUPTED and the
postconditions are read back. Every 5 minutes it refreshes run/ops/CAPABILITIES.json (presence only, never a value).
"""
from __future__ import annotations
import concurrent.futures as cf, datetime as dt, json, os, pathlib, re, shutil, subprocess, sys, threading, time

KY_ROOT = pathlib.Path(os.environ.get("KY_ROOT", "/Users/Dev/kalayantra"))
GIT = KY_ROOT / "wt" / "campaign"            # used ONLY as a handle on the shared object store (fetch / show / merge-base / worktree)
RUN = KY_ROOT / "run"; OPS = RUN / "ops"; EXEC = KY_ROOT / "exec"
REQ, REC, DONE, ACC, INFLIGHT, TMP = OPS / "requests", OPS / "receipts", OPS / "done", OPS / "acceptance", OPS / "inflight", OPS / "tmp"
OPS_PATH = "00_ARCHITECTURE/briefs/kalayantra/fleet/executor_ops.json"
COORD_PATH = "00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md"
CANONICAL_CHART = "482012f1-710e-4a25-994a-93821f5871aa"
PY = str(KY_ROOT / "venv" / "bin" / "python")
REDACT = [re.compile(r"postgres(?:ql)?://[^\s'\"]+", re.I), re.compile(r"(password|pgpassword|secret|token|apikey|api_key)\s*[=:]\s*\S+", re.I)]
SAFE_ID = re.compile(r"^[A-Za-z0-9_.-]{1,80}$"); SAFE_ARG = re.compile(r"^[A-Za-z0-9_.:,=/@+-]{1,300}$"); SHA = re.compile(r"^[0-9a-f]{7,40}$")
SEEN = OPS / "idempotency.jsonl"; MAX_TIMEOUT = 6 * 3600
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
    git("fetch", "-q", "origin", "main", "campaign-coordination")

def load_table() -> dict | None:
    p = git("show", f"origin/main:{OPS_PATH}")
    if p.returncode != 0: return None
    try: return json.loads(p.stdout)["ops"]
    except Exception: return None

def capabilities(table_on_main: bool) -> dict:
    caps = {"builder": bool(os.environ.get("KY_BUILDER_DATABASE_URL")), "owner": bool(os.environ.get("KY_OWNER_DATABASE_URL")),
            "pgenv": pathlib.Path("/Users/Dev/.config/pravaha/pgenv.sh").exists(),
            "gcloud": subprocess.run(["gcloud", "auth", "list", "--format=value(account)"], capture_output=True, text=True).stdout.strip() != "",
            "none": True, "ops_table_on_main": table_on_main, "ts": now()}
    (OPS / "CAPABILITIES.json").write_text(json.dumps(caps, indent=1)); return caps

def seen(key: str) -> bool:
    if not SEEN.exists(): return False
    return any(json.loads(l).get("key") == key for l in SEEN.read_text().splitlines() if l.strip())
def mark_seen(key: str, op: str) -> None:
    with _lock, SEEN.open("a") as f: f.write(json.dumps({"key": key, "op": op, "ts": now()}) + "\n")

def lease_live(lease_id: str) -> bool:
    p = git("show", f"origin/campaign-coordination:{COORD_PATH}", timeout=30)
    if p.returncode != 0 or not SAFE_ID.match(lease_id): return False
    return any(lease_id in line and "RELEASED" not in line for line in p.stdout.splitlines())

def receipt(req: dict, status: str, reason: str = "", rc: int | None = None, out: str = "", extra: dict | None = None) -> None:
    r = {"operation_id": req.get("operation_id"), "kind": req.get("kind"), "item_id": req.get("item_id"), "status": status, "reason": reason,
         "exit_code": rc, "stdout_tail": redact(out[-20000:]), "ts": now(), "reviewed_commit": req.get("reviewed_commit"),
         "requested_by": req.get("requested_by"), "kyd": req.get("kyd")}
    if extra: r.update(extra)
    name = req.get("operation_id") if SAFE_ID.match(str(req.get("operation_id", ""))) else "unknown"
    (REC / f"{name}.json").write_text(json.dumps(r, indent=1))
    log(f"{name} {status} {reason}")


def validate(req: dict, table: dict, caps: dict) -> str | None:
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
        if not req.get("lease_id") or not lease_live(req["lease_id"]): return "lease not live on origin/campaign-coordination"
        acc = req.get("acceptance_receipt")
        if not acc or not pathlib.Path(acc).exists() or ACC not in pathlib.Path(acc).resolve().parents: return "pre-acceptance receipt missing (must live under run/ops/acceptance/)"
        try:
            a = json.loads(pathlib.Path(acc).read_text())
        except Exception: return "pre-acceptance receipt unreadable"
        if a.get("result") != "ACCEPTED" or a.get("operation_id") != req["operation_id"] or a.get("by") not in ("v1", "v2"):
            return "pre-acceptance receipt is not an ACCEPTED receipt by a verifier lane for this operation"
        if req.get("expires_at") and req["expires_at"] < now(): return "request expired"
        rc = str(req.get("reviewed_commit", ""))
        if not SHA.match(rc): return "reviewed_commit required for a production operation"
        if git("merge-base", "--is-ancestor", rc, "origin/main").returncode != 0: return "reviewed_commit is not merged to main"
        if a.get("reviewed_commit") != rc: return "the acceptance receipt names a different reviewed_commit"
    if seen(req["idempotency_key"]): return "idempotency key already used"
    return None


def execute(req: dict, op: dict) -> tuple[int, str]:
    oid = req["operation_id"]; script = op["script"]; args: list[str] = list(op.get("fixed_args", []))
    for k, v in (req.get("args") or {}).items(): args += [f"--{k}", str(v)]
    timeout = min(int(req.get("timeout_s", op.get("timeout_s", 3600))), MAX_TIMEOUT)
    env = {k: v for k, v in os.environ.items() if k not in ("DATABASE_URL",)}
    if op["needs"] == "builder": env["DATABASE_URL"] = os.environ["KY_BUILDER_DATABASE_URL"]
    elif op["needs"] == "owner": env["DATABASE_URL"] = os.environ["KY_OWNER_DATABASE_URL"]
    env["SE_EPHE_PATH"] = os.environ.get("SE_EPHE_PATH", str(KY_ROOT / "ephe")); env["KY_ROOT"] = str(KY_ROOT)
    if not op.get("production"):
        src = git("show", f"origin/main:{script}")
        if src.returncode != 0: return 127, f"script {script} is not on origin/main"
        tmp = TMP / f"{oid}.{pathlib.Path(script).name}"; tmp.write_text(src.stdout); tmp.chmod(0o700)
        argv = ([PY, str(tmp)] if script.endswith(".py") else ["bash", str(tmp)]) + args
        try:
            p = subprocess.run(argv, cwd=str(KY_ROOT), env=env, capture_output=True, text=True, timeout=timeout)
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
        p = subprocess.run(argv, cwd=str(cwd), env=env, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout or "") + "\n" + (p.stderr or "")
    finally:
        git("worktree", "remove", "--force", str(wt), timeout=300)


def run_one(path: pathlib.Path, req: dict, op: dict) -> None:
    try:
        rc, out = execute(req, op)
        receipt(req, "COMPLETED" if rc == 0 else "FAILED", "" if rc == 0 else "non-zero exit (read the postconditions; an exit status proves nothing)", rc, out)
    except subprocess.TimeoutExpired as e:
        receipt(req, "FAILED", "timeout — the operation may still have taken effect; read the postconditions", 124, str(e))
    except Exception as e:
        receipt(req, "FAILED", f"executor error: {type(e).__name__}: {redact(str(e))}")
    finally:
        try: shutil.move(str(path), DONE / path.name)
        except Exception: pass


def main() -> int:
    for d in (REQ, REC, DONE, ACC, INFLIGHT, TMP, OPS / "sql", EXEC, KY_ROOT / "logs"): d.mkdir(parents=True, exist_ok=True)
    for f in sorted(INFLIGHT.glob("*.json")):      # a restart never re-runs an operation
        try: req = json.loads(f.read_text())
        except Exception: req = {"operation_id": f.stem}
        receipt(req, "INTERRUPTED", "the executor restarted while this operation was in flight; it was NOT re-run — read the postconditions")
        shutil.move(str(f), DONE / f.name)
    sync(); table = load_table(); caps = capabilities(table is not None); last_caps = time.time(); last_sync = time.time()
    log("executor up; capabilities " + json.dumps({k: v for k, v in caps.items() if k != "ts"}))
    readers = cf.ThreadPoolExecutor(max_workers=4, thread_name_prefix="read"); builder = cf.ThreadPoolExecutor(max_workers=1, thread_name_prefix="prod")
    while True:
        if (RUN / "STOP_executor").exists(): log("STOP_executor present; no new operations; exiting when idle"); readers.shutdown(wait=True); builder.shutdown(wait=True); return 0
        if time.time() - last_sync > 60: sync(); table = load_table(); last_sync = time.time()
        if time.time() - last_caps > 300: caps = capabilities(table is not None); last_caps = time.time()
        if table is None: time.sleep(30); continue          # the operations table is not on main yet (before B-1 merges)
        for f in sorted(REQ.glob("*.json")):
            try: req = json.loads(f.read_text())
            except Exception as e:
                receipt({"operation_id": f.stem}, "REFUSED", f"unreadable request: {e}"); shutil.move(str(f), DONE / f.name); continue
            why = validate(req, table, caps)
            if why:
                receipt(req, "REFUSED", why); shutil.move(str(f), DONE / f.name); continue
            mark_seen(req["idempotency_key"], req["operation_id"])
            flight = INFLIGHT / f.name; shutil.move(str(f), flight)
            op = table[req["kind"]]
            receipt(req, "RUNNING", "accepted; in flight")
            (builder if op.get("production") else readers).submit(run_one, flight, req, op)
        time.sleep(10)


if __name__ == "__main__":
    sys.exit(main())
