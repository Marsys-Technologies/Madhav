"""Detectors — the checks that decide whether a plan item is really done.

Earned-signal rule (CLAUDE.md §N.8): wherever a fact can be checked, a detector decides the
status; no typed number does. Each detector:
- runs in a worker thread with its own timeout, so a slow or failing one never freezes the view;
- is cached for its own TTL (git 5 min, GitHub 2 min, files 20 s, database 1 min);
- returns a DetectorResult that always says when it was checked and what it saw;
- reports `error` (never `done`) when it cannot measure — an unmeasured check is not a pass.
"""
from __future__ import annotations

import collections
import json
import os
import re
import socket
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass

from .events import now_iso

PIPE_SPLIT = re.compile(r"(?<!\\)\|")
STATE_CLASSES = ("CLOSED_ON_BRANCH", "OPEN", "CLOSED", "DONE", "PARTIAL", "MEASURED",
                 "DEFERRED", "WITHDRAWN", "IN_PROGRESS")


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
    nikasha_root: str      # checkout holding the register and ledgers (campaign/nikasha-test until landed)
    pgenv: str | None      # path to the read-only DB env file (sourced by bash), or None
    home: str              # SUVARNA_HOME
    db_port: int = 5433


def _run(cmd: list[str] | str, cwd: str | None = None, timeout: int = 60, shell: bool = False) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=cwd, timeout=timeout, shell=shell, capture_output=True, text=True)
    return p.returncode, (p.stdout if p.returncode == 0 else (p.stderr or p.stdout))


# --------------------------------------------------------------------------------------------
# Register parsing (shared by several detectors and by the metrics)
# --------------------------------------------------------------------------------------------

def classify_state(cell: str) -> str:
    t = cell.strip().lstrip("*").strip().upper()
    for k in STATE_CLASSES:
        if t.startswith(k):
            return k
    return "OTHER"


def parse_register(path: str) -> dict:
    """Rows keyed by id: {'severity','state_class','state'}; plus the header tally and malformed rows.

    Header-aware: the register holds tables with different column layouts (the build-system rows
    carry two extra columns). Each row is read against the most recent table header above it, and
    the severity and state columns are located by name, never by fixed position. A row whose cell
    count differs from its table's header is flagged malformed (its named columns are still read).
    """
    rows, malformed, header = {}, [], {}
    in_tally = False
    layout = {"n": 9, "severity": 4, "state": 7}  # default: # | change | surfaced | severity | depends | effort | state
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("### 0.1"):
                in_tally = True
                continue
            if in_tally and line.startswith("###"):
                in_tally = False
            if in_tally:
                m = re.match(r"^\|\s*([A-Za-z_ 0-9]+?)\s*\|\s*(\d+)\s*\|", line)
                if m and m.group(1).lower() != "state":
                    header[m.group(1).strip()] = int(m.group(2))
                continue
            if re.match(r"^\|\s*#\s*\|", line):
                names = [c.strip().lower() for c in PIPE_SPLIT.split(line.rstrip("\n"))]
                if "severity" in names and "state" in names:
                    layout = {"n": len(names), "severity": names.index("severity"), "state": names.index("state")}
                continue
            m = re.match(r"^\| (R\d+) \|", line)
            if not m:
                continue
            cells = [c.strip() for c in PIPE_SPLIT.split(line.rstrip("\n"))]
            if len(cells) != layout["n"]:
                malformed.append(m.group(1))
            get = lambda i: cells[i] if i < len(cells) else ""
            state = get(layout["state"])
            rows[m.group(1)] = {"severity": get(layout["severity"]), "state_class": classify_state(state), "state": state[:200]}
    return {"rows": rows, "malformed": malformed, "header": header}


def register_counts(reg: dict) -> dict:
    by_state = collections.Counter(r["state_class"] for r in reg["rows"].values())
    open_by_sev = collections.Counter(r["severity"] for r in reg["rows"].values() if r["state_class"] == "OPEN")
    return {"total": len(reg["rows"]), "by_state": dict(by_state), "open_by_severity": dict(open_by_sev)}


# --------------------------------------------------------------------------------------------
# The detector registry
# --------------------------------------------------------------------------------------------

class Detectors:
    TTL = {"pr_merged": 120, "register_tally_consistent": 20, "register_wellformed": 20,
           "main_file_contains": 300, "main_has_file": 300, "branch_merged": 300,
           "register_rows_closed": 20, "db_columns_exist": 60, "levels_elevated": 60}

    def __init__(self, cfg: Config, on_change=None):
        self.cfg = cfg
        self.on_change = on_change or (lambda: None)
        self.results: dict[str, DetectorResult] = {}
        self._due: dict[str, float] = {}
        self._inflight: set[str] = set()
        self._lock = threading.Lock()
        self._pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="detector")
        self._last_fetch = 0.0
        self._fetch_lock = threading.Lock()

    # -- scheduling ---------------------------------------------------------------------------
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

    # -- helpers ------------------------------------------------------------------------------
    def _fetch_main(self) -> None:
        with self._fetch_lock:
            if time.time() - self._last_fetch < 300:
                return
            _run(["git", "fetch", "-q", "origin", "main"], cwd=self.cfg.repo, timeout=90)
            self._last_fetch = time.time()

    def _register_path(self) -> str:
        return os.path.join(self.cfg.nikasha_root, "00_ARCHITECTURE/briefs/nirmana/NIKASHA_CHANGE_REGISTER_v2_0.md")

    def _psql(self, sql: str, timeout: int = 60) -> list[list[str]]:
        if not self.cfg.pgenv or not os.path.exists(self.cfg.pgenv):
            raise RuntimeError("no read-only DB env file")
        cmd = f"source {self.cfg.pgenv} && psql -tAX -F'\t' -c {json.dumps(sql)}"
        rc, out = _run(["bash", "-c", cmd], timeout=timeout)
        if rc != 0:
            raise RuntimeError(out.strip()[:200])
        return [l.split("\t") for l in out.splitlines() if l.strip()]

    # -- detectors ----------------------------------------------------------------------------
    def d_pr_merged(self, spec):
        rc, out = _run(["gh", "pr", "view", str(spec["pr"]), "--json", "state,mergedAt,mergeable"],
                       cwd=self.cfg.repo, timeout=60)
        if rc != 0:
            return DetectorResult("error", f"gh: {out.strip()[:160]}", now_iso(), "detector:pr_merged")
        d = json.loads(out)
        if d["state"] == "MERGED":
            return DetectorResult("done", f"PR #{spec['pr']} merged {d.get('mergedAt','')}", now_iso(), "detector:pr_merged", 1.0)
        if d["state"] == "OPEN":
            return DetectorResult("running", f"PR #{spec['pr']} open ({d.get('mergeable','?').lower()})", now_iso(), "detector:pr_merged")
        return DetectorResult("blocked", f"PR #{spec['pr']} closed without merging", now_iso(), "detector:pr_merged")

    def d_register_tally_consistent(self, spec):
        reg = parse_register(self._register_path())
        counts = register_counts(reg)["by_state"]
        label = {"OPEN": "OPEN", "CLOSED_ON_BRANCH": "CLOSED_ON_BRANCH", "DONE": "DONE", "CLOSED": "CLOSED",
                 "MEASURED in P6": "MEASURED", "PARTIAL": "PARTIAL"}
        diffs = []
        for name, n in reg["header"].items():
            cls = label.get(name)
            if cls is None:
                continue
            if counts.get(cls, 0) != n:
                diffs.append(f"{name}: header {n} vs rows {counts.get(cls, 0)}")
        for cls, n in counts.items():
            if n and cls not in {label.get(h) for h in reg["header"]}:
                diffs.append(f"{cls}: {n} rows, missing from header")
        if diffs:
            return DetectorResult("pending", "; ".join(diffs)[:300], now_iso(), "detector:register_tally_consistent")
        return DetectorResult("done", "header tallies match the rows", now_iso(), "detector:register_tally_consistent", 1.0)

    def d_register_wellformed(self, spec):
        reg = parse_register(self._register_path())
        if reg["malformed"]:
            return DetectorResult("pending", "malformed rows: " + ", ".join(reg["malformed"]), now_iso(), "detector:register_wellformed")
        return DetectorResult("done", f"all {len(reg['rows'])} rows well-formed", now_iso(), "detector:register_wellformed", 1.0)

    def d_register_rows_closed(self, spec):
        reg = parse_register(self._register_path())
        want = spec["rows"]
        missing = [r for r in want if r not in reg["rows"]]
        if missing:
            return DetectorResult("error", "rows not in register: " + ", ".join(missing), now_iso(), "detector:register_rows_closed")
        closed = [r for r in want if reg["rows"][r]["state_class"] in ("CLOSED", "DONE")]
        partial = [r for r in want if reg["rows"][r]["state_class"] in ("PARTIAL", "IN_PROGRESS", "CLOSED_ON_BRANCH")]
        frac = len(closed) / len(want)
        detail = f"{len(closed)}/{len(want)} closed" + (f"; partial: {', '.join(partial)}" if partial else "")
        if len(closed) == len(want):
            return DetectorResult("done", detail, now_iso(), "detector:register_rows_closed", 1.0)
        status = "running" if (closed or partial) else "pending"
        return DetectorResult(status, detail, now_iso(), "detector:register_rows_closed", frac)

    def d_main_file_contains(self, spec):
        self._fetch_main()
        rc, out = _run(["git", "show", f"origin/main:{spec['path']}"], cwd=self.cfg.repo, timeout=60)
        if rc != 0:
            return DetectorResult("error", f"cannot read {spec['path']} on main", now_iso(), "detector:main_file_contains")
        if re.search(spec["pattern"], out):
            return DetectorResult("done", f"{os.path.basename(spec['path'])} on main mentions it", now_iso(), "detector:main_file_contains", 1.0)
        return DetectorResult("pending", f"not yet in {os.path.basename(spec['path'])} on main", now_iso(), "detector:main_file_contains")

    def d_main_has_file(self, spec):
        self._fetch_main()
        rc, _ = _run(["git", "cat-file", "-e", f"origin/main:{spec['path']}"], cwd=self.cfg.repo, timeout=30)
        if rc == 0:
            return DetectorResult("done", f"{spec['path']} is on main", now_iso(), "detector:main_has_file", 1.0)
        return DetectorResult("pending", f"{os.path.basename(spec['path'])} not on main", now_iso(), "detector:main_has_file")

    def d_branch_merged(self, spec):
        self._fetch_main()
        _run(["git", "fetch", "-q", "origin", spec["ref"].replace("origin/", "")], cwd=self.cfg.repo, timeout=90)
        rc, _ = _run(["git", "merge-base", "--is-ancestor", spec["ref"], "origin/main"], cwd=self.cfg.repo, timeout=30)
        if rc == 0:
            return DetectorResult("done", f"{spec['ref']} is merged into main", now_iso(), "detector:branch_merged", 1.0)
        rc2, n = _run(["git", "rev-list", "--count", f"origin/main..{spec['ref']}"], cwd=self.cfg.repo, timeout=30)
        return DetectorResult("pending", f"{n.strip() if rc2 == 0 else '?'} commits not on main", now_iso(), "detector:branch_merged")

    def d_db_columns_exist(self, spec):
        found = []
        for table, col in spec["columns"]:
            rows = self._psql("select count(*) from information_schema.columns "
                              f"where table_name='{table}' and column_name='{col}'")
            found.append(bool(rows and rows[0][0] == "1"))
        n = sum(found)
        if n == len(found):
            return DetectorResult("done", "all columns present in production", now_iso(), "detector:db_columns_exist", 1.0)
        return DetectorResult("pending" if n == 0 else "running", f"{n}/{len(found)} columns present in production",
                              now_iso(), "detector:db_columns_exist", n / len(found))

    def d_levels_elevated(self, spec):
        lo, hi = spec["levels"]
        levels = dag_levels(self)
        assets = [a for a, lv in levels.items() if lo <= lv <= hi]
        if not assets:
            return DetectorResult("error", f"no assets at levels {lo}–{hi}", now_iso(), "detector:levels_elevated")
        elevated = elevated_assets(self.cfg)
        n = sum(1 for a in assets if a in elevated)
        detail = f"{n}/{len(assets)} assets elevated (proxy: ≥1 certification and no open gap rows)"
        if n == len(assets):
            return DetectorResult("done", detail, now_iso(), "detector:levels_elevated", 1.0)
        return DetectorResult("running" if n else "pending", detail, now_iso(), "detector:levels_elevated", n / len(assets))


# --------------------------------------------------------------------------------------------
# Shared measurements (also used by metrics)
# --------------------------------------------------------------------------------------------

_dag_cache: dict = {"at": 0.0, "levels": {}, "layer": {}}
_dag_lock = threading.Lock()


def dag_levels(det: Detectors) -> dict[str, int]:
    """Dependency level per active asset, from asset_registry.depends_on. Cached 10 minutes."""
    with _dag_lock:
        if time.time() - _dag_cache["at"] < 600 and _dag_cache["levels"]:
            return dict(_dag_cache["levels"])
    rows = det._psql("select asset_id, layer, array_to_string(coalesce(depends_on,'{}'),',') "
                     "from asset_registry where is_active and dead_flag is not true")
    act = {r[0] for r in rows}
    deps = {r[0]: [d for d in (r[2].split(",") if len(r) > 2 and r[2] else []) if d in act] for r in rows}
    layer = {r[0]: r[1] for r in rows}
    lvl: dict[str, int] = {}

    def level(a, stack=()):
        if a in lvl:
            return lvl[a]
        if a in stack:  # cycle guard: never recurse forever on bad registry data
            return 0
        lvl[a] = 0 if not deps[a] else 1 + max(level(d, stack + (a,)) for d in deps[a])
        return lvl[a]

    for a in act:
        level(a)
    with _dag_lock:
        _dag_cache.update(at=time.time(), levels=dict(lvl), layer=layer)
    return lvl


def ledger_state(cfg: Config) -> dict:
    """Open gap rows (last state per gap_id, not superseded) and certification rows."""
    gaps_path = os.path.join(cfg.nikasha_root, "00_ARCHITECTURE/control/asset_gaps.jsonl")
    certs_path = os.path.join(cfg.nikasha_root, "00_ARCHITECTURE/control/asset_certs.jsonl")
    last = {}
    with open(gaps_path, encoding="utf-8") as f:
        for line in f:
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if d.get("asset") == "_schema" or "gap_id" not in d:
                continue
            last[d["gap_id"]] = d
    open_gaps = [d for d in last.values() if d.get("state") in ("OPEN", "RE-OPENED")
                 and d.get("kind", "gap") == "gap" and not d.get("superseded_by")]
    certs = []
    with open(certs_path, encoding="utf-8") as f:
        for line in f:
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if d.get("asset") != "_schema":
                certs.append(d)
    return {"open_gaps": open_gaps, "certs": certs}


def elevated_assets(cfg: Config) -> set[str]:
    """Proxy for ELEVATED until the Nikaṣa tracker's own function is on main (E4.1)."""
    ls = ledger_state(cfg)
    with_open = {d["asset"] for d in ls["open_gaps"]}
    with_cert = {c.get("asset") for c in ls["certs"] if c.get("verdict") in ("PASS", "N/A")}
    return {a for a in with_cert if a not in with_open}


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
    except Exception:
        pass
    return "unknown"
