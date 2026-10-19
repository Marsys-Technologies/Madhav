"""Detectors — the checks that decide whether a plan item is really done.

Earned-signal rule (CLAUDE.md §N.8): wherever a fact can be checked, a detector decides the status;
no typed claim does. Each detector:
- runs in a worker thread with its own timeout, so a slow or failing one never freezes the view;
- is cached for its own TTL (GitHub 2 min, git 1 min, files 15 s, database 1 min, http 10 s);
- returns a DetectorResult that always says when it was checked and what it saw;
- reports `error` (never `done`) when it cannot measure — an unmeasured check is not a pass.

Detector types (plan_model.json ``detector.type``):
  pr_merged            {pr}                       done when the PR is merged
  pr_ready             {pr}                       done when mergeable AND every check passes
  branch_merged        {ref}                      done when ref is an ancestor of origin/main
  branch_file_contains {ref, path, pattern}       done when the committed file on ref matches
  file_exists          {path, min_bytes?}         done when a local file exists (absolute path)
  file_contains        {path, pattern}            done when a local file matches a regex
  db_query             {sql, expect}              read-only; expect "nonempty" | {"min": n}
  http_ok              {url}                      done when the URL answers 2xx (127.0.0.1 only)

Stream activity (not an item detector): ``git_activity(worktree)`` — last commit time/subject and
branch of each stream's worktree, so the dashboard shows work even if a stream forgets to emit.
"""
from __future__ import annotations

import json
import os
import re
import socket
import signal
import subprocess
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import Future, ThreadPoolExecutor
import concurrent.futures
from contextlib import contextmanager
from dataclasses import asdict, dataclass, replace

from .events import now_iso

MAX_CONFIGURED_S = 120.0
# Notes about environment settings that were rejected; health serves them, so a bad value is never silent.
CONFIG_NOTES: list[str] = []


def env_seconds(name: str, default: float, maximum: float = MAX_CONFIGURED_S, notes: list | None = None) -> float:
    """Seconds from the environment: finite, positive, <= maximum. Anything else falls back to `default` and
    leaves a note in `notes` (health) rather than failing the tracker's start."""
    notes = CONFIG_NOTES if notes is None else notes
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        value = float(raw)
    except ValueError:
        value = float("nan")
    if not (0 < value <= maximum):  # NaN fails the comparison too
        notes.append(f"{name}={raw[:40]!r} rejected (need 0 < seconds <= {maximum:g}); using {default:g}")
        return default
    return value


# A loaded machine can make `gh pr list` take longer than 5 s (incident 2026-10-19: ~7.4 s at load ~60).
CALL_TIMEOUT_S = env_seconds("PRAVAHA_CALL_TIMEOUT_S", 5.0)
# Budget for one live verification (`ky done`, the D-46 sweep): all of a detector's calls share it.
VERIFY_BUDGET_S = env_seconds("PRAVAHA_VERIFY_BUDGET_S", 20.0)
_EXTERNAL = threading.local()

ENV_PATH = "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"


@dataclass
class DetectorResult:
    status: str            # done | running | pending | blocked | error
    detail: str
    checked_at: str
    source: str
    progress: float | None = None
    stale: bool = False
    age_s: float | None = None
    error: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Config:
    repo: str              # a checkout of the project repo (for git/gh)
    pgenv: str | None      # path to a read-only DB env file (sourced by bash), or None
    home: str              # PRAVAHA_HOME
    verify_budget_s: float = VERIFY_BUDGET_S


class SourceMonitor:
    """Per-call outcomes; the lock protects memory only, never external work.

    Keep individual call failures so an unrelated successful git command cannot
    hide a timed-out fetch. Health groups these by the operator-visible source.
    """
    def __init__(self):
        self._lock = threading.Lock()
        self._calls: dict[tuple, dict] = {}

    def record(self, source, key, error=None):
        now = time.time()
        with self._lock:
            old = self._calls.get((source, key), {})
            self._calls[(source, key)] = {
                "last_success": old.get("last_success") if error else now,
                "attempted_at": now, "error": error,
            }

    def snapshot(self):
        now = time.time()
        with self._lock:
            calls = list(self._calls.items())
        out = {}
        for (source, _), value in calls:
            row = out.setdefault(source, {"stale": False, "age_s": None, "error": None})
            success = value["last_success"]
            age = round(max(0, now - success), 1) if success is not None else None
            if value["error"]:
                was_stale = row["stale"]
                row.update(stale=True, error=value["error"])
                # A successful local read cannot supply an age for an
                # unmeasured fetch. Failed calls determine a degraded source's age.
                if age is None:
                    row.update(unmeasured=True, age_s=None)
                elif not row.get("unmeasured"):
                    row["age_s"] = max(row["age_s"] or 0, age) if was_stale else age
            elif not row["stale"]:
                row["age_s"] = max(row["age_s"] or 0, age or 0)
        for row in out.values():
            row["sampled_at"] = now
        return out


@contextmanager
def external_context(monitor=None, deadline=float("inf")):
    previous = getattr(_EXTERNAL, "context", (None, float("inf")))
    _EXTERNAL.context = (monitor, deadline)
    try:
        yield
    finally:
        _EXTERNAL.context = previous


def _remaining():
    return max(0, getattr(_EXTERNAL, "context", (None, float("inf")))[1] - time.monotonic())


def _run(cmd, cwd: str | None = None, timeout: float = CALL_TIMEOUT_S, shell: bool = False) -> tuple[int, str]:
    # Call sites may ask for a shorter limit, never a longer one. The live
    # verification deadline also bounds every subprocess in a multi-call detector.
    timeout = min(CALL_TIMEOUT_S, timeout, _remaining())
    if timeout <= 0:
        raise subprocess.TimeoutExpired(cmd, timeout)
    call_deadline = time.monotonic() + timeout
    monitor = getattr(_EXTERNAL, "context", (None,))[0]
    executable = os.path.basename(cmd[0]) if not isinstance(cmd, str) else cmd.split()[0]
    source = {"pmset": "power", "bash": "db", "psql": "db"}.get(executable, executable)
    key = (str(cmd), cwd)
    env = dict(os.environ)
    env["PATH"] = env.get("PATH", "") + ":" + ENV_PATH
    env.update(GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="never")
    p = None
    try:
        p = subprocess.Popen(cmd, cwd=cwd, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             stdin=subprocess.DEVNULL, text=True, env=env, start_new_session=True)
        try:
            out, err = p.communicate(timeout=max(0, call_deadline - time.monotonic()))
        except BaseException:
            # Kill the whole session's process group before draining output pipes.
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            try:
                p.communicate(timeout=0.2)
            except subprocess.TimeoutExpired:
                p.stdout.close()
                p.stderr.close()
                p.wait(timeout=0.2)
            raise
    except BaseException as exc:
        if monitor is not None:
            monitor.record(source, key, "timed out" if isinstance(exc, subprocess.TimeoutExpired) else type(exc).__name__)
        raise
    if monitor is not None:
        monitor.record(source, key, None if p.returncode == 0 else f"exit {p.returncode}")
    return p.returncode, (out if p.returncode == 0 else (err or out))


class Detectors:
    TTL = {"pr_merged": 120, "pr_ready": 120, "branch_merged": 60, "branch_file_contains": 60,
           "file_exists": 15, "file_contains": 15, "db_query": 60, "http_ok": 10}

    def __init__(self, cfg: Config, on_change=None):
        self.cfg = cfg
        self.on_change = on_change or (lambda: None)
        self.results: dict[str, DetectorResult] = {}
        self._due: dict[str, float] = {}
        self._inflight: set[str] = set()
        self._lock = threading.Lock()
        self._pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="detector")
        self._fetched: dict[str, float] = {}
        # This lock protects bookkeeping only; remote I/O never holds it.
        self._fetch_lock = threading.Lock()
        self._fetching: dict[str, tuple[Future, int]] = {}
        self._live = threading.local()
        self._verifying = 0
        self._verify_slots = threading.BoundedSemaphore(4)
        self.sources = SourceMonitor()
        self._measured_at: dict[str, float] = {}

    @staticmethod
    def key(spec: dict) -> str:
        return json.dumps(spec, sort_keys=True, ensure_ascii=False)

    def poll(self, specs: list[dict]) -> None:
        """Submit every detector whose TTL has expired. Never blocks."""
        now = time.time()
        for spec in specs:
            k = self.key(spec)
            with self._lock:
                if self._verifying or k in self._inflight or self._due.get(k, 0) > now:
                    continue
                self._inflight.add(k)
            self._pool.submit(self._run_one, k, spec)

    def _run_one(self, k: str, spec: dict) -> None:
        typ = spec.get("type", "?")
        try:
            fn = getattr(self, "d_" + typ)
            with external_context(self.sources):
                res = fn(spec)
        except (subprocess.TimeoutExpired, TimeoutError):
            with self._lock:
                previous = self.results.get(k)
            res = (replace(previous, stale=True, error=f"{typ}: timed out") if previous is not None
                   else DetectorResult("error", f"{typ}: timed out", now_iso(), f"detector:{typ}", stale=True))
        except Exception as exc:  # isolation: one broken detector never takes down the others
            res = DetectorResult("error", f"{typ}: {type(exc).__name__}: {exc}"[:300], now_iso(), f"detector:{typ}")
        with self._lock:
            prev = self.results.get(k)
            self.results[k] = res
            if not res.stale:
                self._measured_at[k] = time.time()
            self._inflight.discard(k)
            self._due[k] = time.time() + (self.TTL.get(typ, 60) if res.status != "error" else 30)
        if prev is None or (prev.status, prev.detail, prev.progress, prev.stale, prev.error) != (res.status, res.detail, res.progress, res.stale, res.error):
            self.on_change()

    def get(self, spec: dict) -> DetectorResult | None:
        with self._lock:
            key = self.key(spec)
            result = self.results.get(key)
            if result is not None and result.stale:
                measured = self._measured_at.get(key)
                return replace(result, age_s=round(time.time() - measured, 1) if measured else None)
            return result

    def verify(self, spec: dict, requested_at: int | None = None) -> DetectorResult:
        """Fresh live measurement on a separate, bounded, admission-limited worker.

        A timed-out worker never supplies a late success or updates dashboard
        results. Slots stay occupied until workers exit, bounding abandoned work.
        """
        requested_at = requested_at if requested_at is not None else time.monotonic_ns()
        typ = spec.get("type", "?")
        budget = min(MAX_CONFIGURED_S, max(0.01, self.cfg.verify_budget_s))
        deadline = time.monotonic() + budget
        refused = lambda detail: DetectorResult("error", f"{typ}: {detail}", now_iso(), f"detector:{typ}")
        if not self._verify_slots.acquire(blocking=False):
            return refused("live verification workers busy; retry")
        future = concurrent.futures.Future()
        with self._lock:
            self._verifying += 1

        def measure():
            self._live.verify = requested_at
            try:
                with external_context(self.sources, deadline=deadline):
                    result = getattr(self, "d_" + typ)(spec)
                result = result if time.monotonic() < deadline else refused("live measurement timed out")
            except Exception as exc:
                result = refused(f"{type(exc).__name__}: {exc}"[:250])
            finally:
                self._live.verify = None
                with self._lock:
                    self._verifying -= 1
                self._verify_slots.release()
            future.set_result(result)

        threading.Thread(target=measure, name="verify-measurement", daemon=True).start()
        try:
            return future.result(timeout=max(0, deadline - time.monotonic()))
        except concurrent.futures.TimeoutError:
            return refused("live measurement timed out")

    def force(self) -> None:
        """Expire every cached result (used when an event arrives, so evidence is re-checked promptly)."""
        with self._lock:
            self._due.clear()

    # -- helpers ------------------------------------------------------------------------------
    def _fetch(self, remote_branch: str) -> None:
        requested_at = getattr(self._live, "verify", None)
        while True:
            with self._fetch_lock:
                entry = self._fetching.get(remote_branch)
                if entry is None:
                    # Only dashboard polling may reuse a completed fetch's TTL.
                    if requested_at is None and time.time() - self._fetched.get(remote_branch, 0) < 60:
                        return
                    flight = Future()
                    self._fetching[remote_branch] = (flight, time.monotonic_ns())
                    break
                flight, started_at = entry
            if requested_at is None or started_at >= requested_at:
                # Share only a measurement that qualifies for this request.
                flight.result(timeout=min(CALL_TIMEOUT_S, _remaining()))
                return
            # Serialize behind an older same-ref fetch, but neither its success
            # nor its failure measures the branch for this verification request.
            try:
                flight.result(timeout=min(CALL_TIMEOUT_S, _remaining()))
            except concurrent.futures.TimeoutError:
                raise
            except Exception:
                pass
        try:
            rc, out = _run(["git", "fetch", "-q", "origin", remote_branch], cwd=self.cfg.repo)
            if rc != 0:
                raise RuntimeError(f"git fetch {remote_branch}: {out.strip()[:160]}")
        except BaseException as exc:
            with self._fetch_lock:
                flight.set_exception(exc)
                del self._fetching[remote_branch]
            raise
        else:
            with self._fetch_lock:
                self._fetched[remote_branch] = time.time()
                flight.set_result(None)
                del self._fetching[remote_branch]

    def _resolve_ref(self, ref: str) -> str:
        if ref.startswith("origin/"):
            self._fetch(ref[len("origin/"):])
        return ref

    def _psql(self, sql: str, timeout: float = CALL_TIMEOUT_S) -> list[list[str]]:
        if not self.cfg.pgenv or not os.path.exists(self.cfg.pgenv):
            raise RuntimeError("no read-only DB env file configured (PRAVAHA_PGENV) — unmeasured")
        # read-only by construction: every query runs inside a READ ONLY transaction
        wrapped = f"BEGIN TRANSACTION READ ONLY; {sql.rstrip(';')}; ROLLBACK;"
        cmd = f"source {json.dumps(self.cfg.pgenv)} && psql -tAX -F'\t' -v ON_ERROR_STOP=1 -c {json.dumps(wrapped)}"
        rc, out = _run(["bash", "-c", cmd], timeout=timeout)
        if rc != 0:
            raise RuntimeError(out.strip()[:200])
        return [l.split("\t") for l in out.splitlines() if l.strip() and l.strip() not in ("BEGIN", "ROLLBACK")]

    # -- detectors ----------------------------------------------------------------------------
    def d_pr_merged(self, spec):
        rc, out = _run(["gh", "pr", "view", str(spec["pr"]), "--json", "state,mergedAt,mergeable"], cwd=self.cfg.repo)
        if rc != 0:
            return DetectorResult("error", f"gh: {out.strip()[:160]}", now_iso(), "detector:pr_merged")
        d = json.loads(out)
        if d["state"] == "MERGED":
            return DetectorResult("done", f"PR #{spec['pr']} merged {d.get('mergedAt', '')}", now_iso(), "detector:pr_merged", 1.0)
        if d["state"] == "OPEN":
            return DetectorResult("running", f"PR #{spec['pr']} open ({str(d.get('mergeable', '?')).lower()})", now_iso(), "detector:pr_merged")
        return DetectorResult("blocked", f"PR #{spec['pr']} closed without merging", now_iso(), "detector:pr_merged")

    def d_pr_ready(self, spec):
        rc, out = _run(["gh", "pr", "view", str(spec["pr"]), "--json", "state,mergeable,statusCheckRollup"], cwd=self.cfg.repo)
        if rc != 0:
            return DetectorResult("error", f"gh: {out.strip()[:160]}", now_iso(), "detector:pr_ready")
        d = json.loads(out)
        if d["state"] == "MERGED":
            return DetectorResult("done", f"PR #{spec['pr']} already merged", now_iso(), "detector:pr_ready", 1.0)
        checks = d.get("statusCheckRollup") or []
        concl = [(c.get("name") or c.get("context") or "?", (c.get("conclusion") or c.get("state") or "PENDING").upper()) for c in checks]
        bad = [n for n, c in concl if c in ("FAILURE", "ERROR", "CANCELLED", "TIMED_OUT", "ACTION_REQUIRED")]
        pending = [n for n, c in concl if c in ("PENDING", "QUEUED", "IN_PROGRESS", "EXPECTED", "")]
        ok = len(concl) - len(bad) - len(pending)
        mergeable = str(d.get("mergeable", "UNKNOWN"))
        prog = ok / len(concl) if concl else None
        detail = f"{mergeable.lower()}; checks {ok}/{len(concl)} passing" + (f"; failing: {', '.join(bad[:4])}" if bad else "") + (f"; pending {len(pending)}" if pending else "")
        if mergeable == "MERGEABLE" and not bad and not pending and concl:
            return DetectorResult("done", detail, now_iso(), "detector:pr_ready", 1.0)
        status = "blocked" if (mergeable == "CONFLICTING" or bad) else "running"
        return DetectorResult(status, detail, now_iso(), "detector:pr_ready", prog)

    def d_branch_merged(self, spec):
        self._fetch("main")
        ref = self._resolve_ref(spec["ref"])
        rc0, _ = _run(["git", "rev-parse", "--verify", "-q", ref], cwd=self.cfg.repo)
        if rc0 != 0:
            return DetectorResult("pending", f"{spec['ref']} does not exist yet", now_iso(), "detector:branch_merged")
        rc, _ = _run(["git", "merge-base", "--is-ancestor", ref, "origin/main"], cwd=self.cfg.repo)
        if rc == 0:
            return DetectorResult("done", f"{spec['ref']} is merged into main", now_iso(), "detector:branch_merged", 1.0)
        # main's merge queue squashes, so a merged branch is never an ancestor of main. Accept a MERGED PR into main
        # whose head commit is exactly the branch's current tip (a later push to the branch is not "merged").
        branch = spec["ref"].split("/", 1)[1] if spec["ref"].startswith("origin/") else spec["ref"]
        rc_t, tip = _run(["git", "rev-parse", ref], cwd=self.cfg.repo)
        rc_p, out = _run(["gh", "pr", "list", "--state", "merged", "--base", "main", "--head", branch, "--limit", "5",
                          "--json", "number,headRefOid,mergeCommit,mergedAt"], cwd=self.cfg.repo)
        if rc_t == 0 and rc_p == 0:
            try:
                prs = json.loads(out or "[]")
            except ValueError:
                prs = []
            for pr in prs:
                if pr.get("headRefOid") == tip.strip():
                    mc = (pr.get("mergeCommit") or {}).get("oid", "")[:9]
                    return DetectorResult("done", f"{spec['ref']} merged via PR #{pr['number']} (squash {mc}, {pr.get('mergedAt', '')})",
                                          now_iso(), "detector:branch_merged", 1.0)
        rc2, n = _run(["git", "rev-list", "--count", f"origin/main..{ref}"], cwd=self.cfg.repo)
        return DetectorResult("running", f"{n.strip() if rc2 == 0 else '?'} commits on {spec['ref']} not yet on main", now_iso(), "detector:branch_merged")

    def d_branch_file_contains(self, spec):
        ref = self._resolve_ref(spec["ref"])
        rc, out = _run(["git", "show", f"{ref}:{spec['path']}"], cwd=self.cfg.repo)
        if rc != 0:
            return DetectorResult("pending", f"{os.path.basename(spec['path'])} not on {spec['ref']}", now_iso(), "detector:branch_file_contains")
        if re.search(spec["pattern"], out, re.M):
            return DetectorResult("done", f"{os.path.basename(spec['path'])} on {spec['ref']} has it", now_iso(), "detector:branch_file_contains", 1.0)
        return DetectorResult("pending", f"not yet in {os.path.basename(spec['path'])} on {spec['ref']}", now_iso(), "detector:branch_file_contains")

    def d_file_exists(self, spec):
        p = spec["path"]
        if not os.path.exists(p):
            return DetectorResult("pending", f"{os.path.basename(p)} not written yet", now_iso(), "detector:file_exists")
        size = os.path.getsize(p)
        if size < int(spec.get("min_bytes", 1)):
            return DetectorResult("running", f"{os.path.basename(p)} exists but is only {size} bytes", now_iso(), "detector:file_exists")
        return DetectorResult("done", f"{os.path.basename(p)} ({size} bytes)", now_iso(), "detector:file_exists", 1.0)

    def d_file_contains(self, spec):
        p = spec["path"]
        if not os.path.exists(p):
            return DetectorResult("pending", f"{os.path.basename(p)} not written yet", now_iso(), "detector:file_contains")
        with open(p, encoding="utf-8", errors="replace") as f:
            text = f.read()
        if re.search(spec["pattern"], text, re.M):
            return DetectorResult("done", f"{os.path.basename(p)} has it", now_iso(), "detector:file_contains", 1.0)
        return DetectorResult("pending", f"{os.path.basename(p)} does not have it yet", now_iso(), "detector:file_contains")

    def d_db_query(self, spec):
        rows = self._psql(spec["sql"])
        expect = spec.get("expect", "nonempty")
        if expect == "nonempty":
            ok, detail = bool(rows), (f"{len(rows)} row(s): {' | '.join(rows[0])[:120]}" if rows else "no rows")
        elif isinstance(expect, dict) and "min" in expect:
            v = float(rows[0][0]) if rows and rows[0] and rows[0][0] not in ("", None) else 0.0
            ok, detail = v >= float(expect["min"]), f"value {v:g} (need ≥ {expect['min']})"
        else:
            raise ValueError(f"unknown expect {expect!r}")
        return DetectorResult("done" if ok else "pending", detail, now_iso(), "detector:db_query", 1.0 if ok else None)

    def d_http_ok(self, spec):
        url = spec["url"]
        if not (url.startswith("http://127.0.0.1") or url.startswith("http://localhost")):
            raise ValueError("http_ok is limited to 127.0.0.1")
        try:
            with urllib.request.urlopen(url, timeout=3) as r:  # noqa: S310
                code = r.status
        except urllib.error.HTTPError as exc:
            code = exc.code
        except Exception as exc:  # noqa: BLE001
            return DetectorResult("pending", f"unreachable: {type(exc).__name__}", now_iso(), "detector:http_ok")
        if 200 <= code < 300:
            return DetectorResult("done", f"{url} answers {code}", now_iso(), "detector:http_ok", 1.0)
        return DetectorResult("blocked", f"{url} answers {code}", now_iso(), "detector:http_ok")


# --------------------------------------------------------------------------------------------
# Stream activity and environment probes
# --------------------------------------------------------------------------------------------

def git_activity(worktree: str) -> dict:
    """Last commit (time, hash, subject), branch and dirty-file count of a stream's worktree."""
    if not worktree or not os.path.isdir(worktree):
        return {"error": f"worktree not found: {worktree}"}
    rc, out = _run(["git", "log", "-1", "--format=%ct|%h|%s"], cwd=worktree)
    if rc != 0:
        return {"error": out.strip()[:160]}
    ct, h, subj = (out.strip().split("|", 2) + ["", "", ""])[:3]
    rc_b, br = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=worktree)
    rc_s, st = _run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=worktree)
    return {"worktree": worktree, "branch": br.strip() if rc_b == 0 else "?",
            "last_commit_ts": int(ct) if ct.isdigit() else None, "last_commit": h, "subject": subj[:140],
            "dirty_files": len([l for l in st.splitlines() if l.strip()]) if rc_s == 0 else None}


def port_open(port: int, host: str = "127.0.0.1", timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def power_source() -> str:
    try:
        rc, out = _run(["pmset", "-g", "batt"], timeout=5)
        if "AC Power" in out:
            return "ac"
        if "Battery Power" in out:
            m = re.search(r"(\d+)%", out)
            return f"battery {m.group(1)}%" if m else "battery"
    except subprocess.TimeoutExpired:
        raise
    except Exception:  # noqa: BLE001
        pass
    return "unknown"
