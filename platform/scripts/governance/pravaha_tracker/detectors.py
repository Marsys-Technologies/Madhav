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
import subprocess
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass

from .events import now_iso

ENV_PATH = "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"


@dataclass
class DetectorResult:
    status: str            # done | running | pending | blocked | error
    detail: str
    checked_at: str
    source: str
    progress: float | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Config:
    repo: str              # a checkout of the project repo (for git/gh)
    pgenv: str | None      # path to a read-only DB env file (sourced by bash), or None
    home: str              # PRAVAHA_HOME


def _run(cmd, cwd: str | None = None, timeout: int = 60, shell: bool = False) -> tuple[int, str]:
    env = dict(os.environ)
    env["PATH"] = env.get("PATH", "") + ":" + ENV_PATH
    p = subprocess.run(cmd, cwd=cwd, timeout=timeout, shell=shell, capture_output=True, text=True, env=env)
    return p.returncode, (p.stdout if p.returncode == 0 else (p.stderr or p.stdout))


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
        self._fetch_lock = threading.Lock()

    @staticmethod
    def key(spec: dict) -> str:
        return json.dumps(spec, sort_keys=True, ensure_ascii=False)

    def poll(self, specs: list[dict]) -> None:
        """Submit every detector whose TTL has expired. Never blocks."""
        now = time.time()
        for spec in specs:
            k = self.key(spec)
            with self._lock:
                if k in self._inflight or self._due.get(k, 0) > now:
                    continue
                self._inflight.add(k)
            self._pool.submit(self._run_one, k, spec)

    def _run_one(self, k: str, spec: dict) -> None:
        typ = spec.get("type", "?")
        try:
            fn = getattr(self, "d_" + typ)
            res = fn(spec)
        except subprocess.TimeoutExpired:
            res = DetectorResult("error", f"{typ}: timed out", now_iso(), f"detector:{typ}")
        except Exception as exc:  # isolation: one broken detector never takes down the others
            res = DetectorResult("error", f"{typ}: {type(exc).__name__}: {exc}"[:300], now_iso(), f"detector:{typ}")
        with self._lock:
            prev = self.results.get(k)
            self.results[k] = res
            self._inflight.discard(k)
            self._due[k] = time.time() + (self.TTL.get(typ, 60) if res.status != "error" else 30)
        if prev is None or (prev.status, prev.detail, prev.progress) != (res.status, res.detail, res.progress):
            self.on_change()

    def get(self, spec: dict) -> DetectorResult | None:
        with self._lock:
            return self.results.get(self.key(spec))

    def force(self) -> None:
        """Expire every cached result (used when an event arrives, so evidence is re-checked promptly)."""
        with self._lock:
            self._due.clear()

    # -- helpers ------------------------------------------------------------------------------
    def _fetch(self, remote_branch: str) -> None:
        with self._fetch_lock:
            if time.time() - self._fetched.get(remote_branch, 0) < 60:
                return
            _run(["git", "fetch", "-q", "origin", remote_branch], cwd=self.cfg.repo, timeout=90)
            self._fetched[remote_branch] = time.time()

    def _resolve_ref(self, ref: str) -> str:
        if ref.startswith("origin/"):
            self._fetch(ref[len("origin/"):])
        return ref

    def _psql(self, sql: str, timeout: int = 60) -> list[list[str]]:
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
        rc0, _ = _run(["git", "rev-parse", "--verify", "-q", ref], cwd=self.cfg.repo, timeout=30)
        if rc0 != 0:
            return DetectorResult("pending", f"{spec['ref']} does not exist yet", now_iso(), "detector:branch_merged")
        rc, _ = _run(["git", "merge-base", "--is-ancestor", ref, "origin/main"], cwd=self.cfg.repo, timeout=30)
        if rc == 0:
            return DetectorResult("done", f"{spec['ref']} is merged into main", now_iso(), "detector:branch_merged", 1.0)
        # main's merge queue squashes, so a merged branch is never an ancestor of main. Accept a MERGED PR into main
        # whose head commit is exactly the branch's current tip (a later push to the branch is not "merged").
        branch = spec["ref"].split("/", 1)[1] if spec["ref"].startswith("origin/") else spec["ref"]
        rc_t, tip = _run(["git", "rev-parse", ref], cwd=self.cfg.repo, timeout=30)
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
        rc2, n = _run(["git", "rev-list", "--count", f"origin/main..{ref}"], cwd=self.cfg.repo, timeout=30)
        return DetectorResult("running", f"{n.strip() if rc2 == 0 else '?'} commits on {spec['ref']} not yet on main", now_iso(), "detector:branch_merged")

    def d_branch_file_contains(self, spec):
        ref = self._resolve_ref(spec["ref"])
        rc, out = _run(["git", "show", f"{ref}:{spec['path']}"], cwd=self.cfg.repo, timeout=60)
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
    rc, out = _run(["git", "log", "-1", "--format=%ct|%h|%s"], cwd=worktree, timeout=15)
    if rc != 0:
        return {"error": out.strip()[:160]}
    ct, h, subj = (out.strip().split("|", 2) + ["", "", ""])[:3]
    rc_b, br = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=worktree, timeout=15)
    rc_s, st = _run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=worktree, timeout=30)
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
    except Exception:  # noqa: BLE001
        pass
    return "unknown"
