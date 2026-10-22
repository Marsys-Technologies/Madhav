"""G-5 attributed-CPU method (ruling SR-G5-LOAD, 2026-10-22).

The wall method of G-5 (`gates.runtime_projection`) is only meaningful on a quiet machine.  This module measures the same substeps by ATTRIBUTED CPU time instead:
per stage, the user+sys CPU of the harness process that runs the builder / verifier (its threads and reaped children) PLUS the user+sys CPU of the Postgres backends
that serve the trial database, measured from the stage start.  The CPU seconds replace the wall seconds in the SAME projection (`gates.runtime_projection`: the
plan's (base_s + solver_s) · (26/trial_classes) · r · speed_factor), so the century factor r is the wall method's r, not a second opinion.

Backend CPU source (SR-G5-LOAD): `pg_stat_statements` total_exec_time when the extension is PRELOADED on the cluster; otherwise the OS CPU time of the backend PIDs
(`pg_stat_activity.pid` filtered to the trial database, read through /proc on Linux or libproc `proc_pidinfo` on macOS).  The cluster is never reconfigured or
restarted.  `pg_stat_statements` time is elapsed executor time (it includes lock waits and I/O waits), so it is an UPPER BOUND of backend CPU; the record says which
source was used.  The OS source proves itself before it is trusted (`probe_reader`: the reader must agree with `getrusage` on a known burn), so a reader that
returns plausible zeros reads `available: false`, never a number (N.8).

Method selection (`select`): wall when the sampled 1-min load per core stayed ≤ the profile's `runtime.max_load_per_core` (default 1.0) and the slice has the
profile's trial classes; attributed_cpu when the load bound was broken and the CPU record is complete; neither → None, and `apply_to_gate` makes every
wall-or-CPU projection check of G-5 NOT_EVALUATED (the dispatch gate refuses).  A slice smaller than the trial class set is invalid for BOTH methods (the class-less
head is multiplied by 26/n in the formula, DEFECT_MAP D-10): CPU does not repair a slice artefact.

Tolerances (stated, not hoped): a backend that lives and dies between two samples (`interval_s`, default 0.2 s) is seen at most once; its CPU after the last
sighting is lost, so the backend term is a LOWER bound by at most (interval_s × cores busy) per exiting backend.  Attributed CPU is not wall-independent to the last
percent: contention (cache, SMT, Apple P/E-core placement) moves CPU seconds by tens of percent at the extreme; the oracles state the factor they hold."""
from __future__ import annotations

import contextlib
import ctypes
import ctypes.util
import hashlib
import json
import os
import platform
import resource
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Callable

SCHEMA = "ky.g5_attributed_cpu/1"
WALL, ATTRIBUTED_CPU = "wall", "attributed_cpu"
DEFAULT_MAX_LOAD_PER_CORE = 1.0
DEFAULT_TRIAL_CLASSES = 12
WALL_CLAIM = "projected century writer time"                  # the G-5 check whose wall reading this module may replace (gates.g5_runtime)
EFFECTIVE_CLAIM = "projected effective wall (compute + lock wait)"      # T17's wall-based check (gates.g5_effective_wall_checks)
VERIFIER_CLAIM = "verifier solver check"                     # the verifier half of G-5 (gates.g5_runtime)
PGSS = "pg_stat_statements"
OS_SOURCE = "os_process_cpu"
PROBE_BURN_S = 0.15
PROBE_TOLERANCE = (0.20, 0.02)                               # relative, absolute seconds: the reader must match getrusage on the probe burn


# ── reading the CPU of another process ─────────────────────────────────────────────────────────────────────────

def _linux_cpu_s(pid: int) -> float | None:
    try:
        raw = Path(f"/proc/{pid}/stat").read_text()
        fields = raw.rsplit(")", 1)[1].split()               # after the command name; utime / stime are fields 14 / 15 of the file
        return (int(fields[11]) + int(fields[12])) / os.sysconf("SC_CLK_TCK")
    except (OSError, ValueError, IndexError):
        return None


class _TaskInfo(ctypes.Structure):                           # struct proc_taskinfo, <sys/proc_info.h> (96 bytes)
    _fields_ = [("virtual_size", ctypes.c_uint64), ("resident_size", ctypes.c_uint64), ("total_user", ctypes.c_uint64), ("total_system", ctypes.c_uint64),
                ("threads_user", ctypes.c_uint64), ("threads_system", ctypes.c_uint64)] + [(n, ctypes.c_int32) for n in (
                    "policy", "faults", "pageins", "cow_faults", "messages_sent", "messages_received", "syscalls_mach", "syscalls_unix", "csw",
                    "threadnum", "numrunning", "priority")]


class _Timebase(ctypes.Structure):
    _fields_ = [("numer", ctypes.c_uint32), ("denom", ctypes.c_uint32)]


_PROC_PIDTASKINFO = 4
_darwin: dict = {}


def _darwin_cpu_s(pid: int) -> float | None:
    """libproc `proc_pidinfo(PROC_PIDTASKINFO)`: total user + system time of a process we may inspect, in mach ticks → seconds via mach_timebase_info."""
    try:
        if "lib" not in _darwin:
            lib = ctypes.CDLL(ctypes.util.find_library("proc") or "/usr/lib/libproc.dylib", use_errno=True)
            lib.proc_pidinfo.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint64, ctypes.c_void_p, ctypes.c_int]
            lib.proc_pidinfo.restype = ctypes.c_int
            tb = _Timebase()
            ctypes.CDLL("/usr/lib/libSystem.B.dylib").mach_timebase_info(ctypes.byref(tb))
            _darwin.update(lib=lib, scale=tb.numer / tb.denom / 1e9)
        info = _TaskInfo()
        if _darwin["lib"].proc_pidinfo(int(pid), _PROC_PIDTASKINFO, 0, ctypes.byref(info), ctypes.sizeof(info)) != ctypes.sizeof(info):
            return None
        return (info.total_user + info.total_system) * _darwin["scale"]
    except (OSError, AttributeError, ValueError):
        return None


def _ps_cpu_s(pid: int) -> float | None:
    """Last-resort reader: `ps -o time=` (centisecond resolution), [[dd-]hh:]mm:ss.cc."""
    try:
        r = subprocess.run(["ps", "-o", "time=", "-p", str(int(pid))], capture_output=True, text=True, timeout=5)
        txt = r.stdout.strip()
        if r.returncode != 0 or not txt:
            return None
        days, _, rest = txt.rpartition("-")
        secs = 0.0
        for part in rest.split(":"):
            secs = secs * 60 + float(part)
        return secs + (int(days) * 86400 if days else 0)
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def default_reader() -> Callable[[int], float | None]:
    return _linux_cpu_s if sys.platform.startswith("linux") else _darwin_cpu_s if sys.platform == "darwin" else _ps_cpu_s


def reader_name(reader) -> str:
    return {"_linux_cpu_s": "linux:/proc/<pid>/stat", "_darwin_cpu_s": "darwin:libproc proc_pidinfo", "_ps_cpu_s": "ps -o time="}.get(getattr(reader, "__name__", ""), "injected")


def self_cpu_s() -> float:
    """User + system CPU of this process (all threads) and its reaped children."""
    a, b = resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)
    return a.ru_utime + a.ru_stime + b.ru_utime + b.ru_stime


def probe_reader(reader: Callable[[int], float | None], burn_s: float = PROBE_BURN_S) -> tuple[bool, dict]:
    """N.8 detector for the OS source: burn a known amount of CPU in THIS process and require the reader to see it, in agreement with getrusage.  A reader that is
    unreadable, scaled wrongly (the macOS timebase) or reads a constant fails here."""
    pid = os.getpid()
    before, ru0 = reader(pid), resource.getrusage(resource.RUSAGE_SELF)
    if before is None:
        return False, {"reason": "the reader cannot read this process"}
    t = time.process_time()
    while time.process_time() - t < burn_s:
        pass
    after, ru1 = reader(pid), resource.getrusage(resource.RUSAGE_SELF)
    if after is None:
        return False, {"reason": "the reader failed after the burn"}
    seen, truth = after - before, (ru1.ru_utime + ru1.ru_stime) - (ru0.ru_utime + ru0.ru_stime)
    ok = truth > 0 and abs(seen - truth) <= PROBE_TOLERANCE[0] * truth + PROBE_TOLERANCE[1]
    return ok, {"reader_s": round(seen, 4), "getrusage_s": round(truth, 4), "reason": None if ok else "the reader disagrees with getrusage on a known burn"}


def trial_backend_pids(admin_dsn: str, database: str, application_name: str | None = None) -> Callable[[], list[int] | None]:
    """A lister over a SEPARATE admin connection: the pids of every session (client backend, parallel worker, autovacuum worker) attached to `database`; None when the
    admin connection cannot answer.  The lister's own session is on the admin database, so it never lists itself."""
    holder: dict = {}

    def lister():
        sql, args = "SELECT pid FROM pg_stat_activity WHERE datname = %s AND pid <> pg_backend_pid()", [database]
        if application_name:
            sql, args = sql + " AND application_name = %s", args + [application_name]
        for _attempt in (1, 2):                                                  # one reconnect: a single dropped admin connection is not an unknown stage
            try:
                import psycopg
                if "conn" not in holder:
                    holder["conn"] = psycopg.connect(admin_dsn, autocommit=True, connect_timeout=3)
                return [int(r[0]) for r in holder["conn"].execute(sql, args).fetchall()]
            except Exception:                                                    # noqa: BLE001 — an unanswerable lister is unknown, not empty
                _close_quietly(holder.pop("conn", None))
        return None

    def close():
        _close_quietly(holder.pop("conn", None))
    lister.close = close                                                         # type: ignore[attr-defined]
    return lister


def _close_quietly(conn) -> None:
    try:
        if conn is not None:
            conn.close()
    except Exception:                                                            # noqa: BLE001 — closing a dead connection must not mask the run
        pass


def pgss_reader(admin_dsn: str, database: str) -> tuple[Callable[[], float | None] | None, dict]:
    """`pg_stat_statements` total (plan + exec) milliseconds of `database`, as seconds — only when the extension is PRELOADED and installed in that database.
    (None, why) otherwise; never CREATE EXTENSION, never ALTER SYSTEM, never a restart."""
    try:
        import psycopg
        from psycopg.conninfo import make_conninfo
        with psycopg.connect(admin_dsn, autocommit=True, connect_timeout=3) as admin:
            preload = admin.execute("SHOW shared_preload_libraries").fetchone()[0]
        if PGSS not in [p.strip() for p in preload.split(",")]:
            return None, {"preloaded": False, "shared_preload_libraries": preload}
        conn = psycopg.connect(make_conninfo(admin_dsn, dbname=database), autocommit=True, connect_timeout=3)
        conn.execute("SELECT 1 FROM pg_stat_statements LIMIT 1")
    except Exception as exc:                                                     # noqa: BLE001 — recorded by type; the OS source is the fallback
        return None, {"preloaded": "unknown", "reason": type(exc).__name__}

    def read():
        try:
            return float(conn.execute("SELECT coalesce(sum(total_exec_time + total_plan_time), 0) FROM pg_stat_statements "
                                      "WHERE dbid = (SELECT oid FROM pg_database WHERE datname = current_database())").fetchone()[0]) / 1000.0
        except Exception:                                                        # noqa: BLE001
            return None
    read.close = lambda: _close_quietly(conn)                                    # type: ignore[attr-defined]
    return read, {"preloaded": True, "shared_preload_libraries": preload}


# ── the meter ──────────────────────────────────────────────────────────────────────────────────────────────────

class CpuMeter:
    """Per named stage: `wall_s`, `self_cpu_s` (the harness process), `backend_cpu_s` (the trial database's backends), `cpu_s` = their sum, and the highest sampled
    1-min load per core.  A background sampler (every `interval_s`) keeps the last CPU reading of every backend pid it has seen, so a backend that exits mid-stage keeps
    its CPU; `measure()` forces one more sample at both edges.  A stage with ANY sample the lister or the reader could not answer has `backend_cpu_s = None` (unknown,
    never zero), exactly like `trial_eval.StageClock`.  The sampler's own thread CPU is measured and subtracted from the harness term."""

    def __init__(self, lister: Callable[[], list[int] | None], reader: Callable[[int], float | None] | None = None, *, pgss: Callable[[], float | None] | None = None,
                 pgss_info: dict | None = None, interval_s: float = 0.2, load_fn: Callable[[], float] | None = None, ncpu: int | None = None,
                 self_cpu: Callable[[], float] = self_cpu_s, probe: bool = True):
        self.lister, self.reader, self.pgss, self.interval_s = lister, reader or default_reader(), pgss, interval_s
        self.load_fn = load_fn or (lambda: os.getloadavg()[0])
        self.ncpu = ncpu or os.cpu_count() or 1
        self.self_cpu = self_cpu
        self.stages: dict = {}
        self._pids: dict = {}
        self._lock = threading.RLock()
        self._overhead = 0.0
        self._unanswered = 0                     # lister/reader failures since the last stage edge
        self._load_max = 0.0
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._started = False
        self._pgss_base: float | None = None
        self._pgss_last = 0.0
        self.source = {"backend": PGSS if pgss else OS_SOURCE, "reader": None if pgss else reader_name(self.reader), **(pgss_info or {})}
        self.available, self.reason, self.probe = True, None, None
        if not pgss and probe:
            ok, self.probe = probe_reader(self.reader)
            if not ok:
                self.available, self.reason = False, f"OS CPU reader failed its self-check: {self.probe.get('reason')}"

    # sampling ---------------------------------------------------------------------------------------------------
    def _sample(self) -> None:
        """One sample.  Never raises: a sampling failure is an unanswered sample (the stage reads unknown), not a build abort."""
        t = time.thread_time()
        with self._lock:
            try:
                self._sample_locked()
            except Exception:                                                    # noqa: BLE001 — unknown, never zero, never a crash of the measured run
                self._unanswered += 1
            self._overhead += time.thread_time() - t

    def _sample_locked(self) -> None:
        self._load_max = max(self._load_max, self.load_fn() / self.ncpu)
        if self.pgss:
            v = self.pgss()
            self._unanswered += v is None
            if v is not None:
                if self._pgss_base is None:
                    self._pgss_base = v
                self._pgss_last = v
        else:
            pids = self.lister()
            if pids is None:
                self._unanswered += 1
            unreadable = []
            for pid in pids or []:
                cpu = self.reader(pid)
                if cpu is None:
                    unreadable.append(pid)
                    continue
                p = self._pids.get(pid)
                if p is None:
                    # present at the first sample = it pre-dates the meter (count from now); first seen later = born inside the run (count it all)
                    self._pids[pid] = {"base": cpu if not self._started else 0.0, "last": cpu, "retired": 0.0}
                else:
                    if cpu < p["last"]:                      # the pid was reused by another process
                        p["retired"] += p["last"] - p["base"]
                        p["base"] = 0.0
                    p["last"] = cpu
            if unreadable:
                # unreadable AND still listed a moment later = the reader cannot see a live backend (unknown); gone = it exited between the listing and the read
                again = self.lister()
                self._unanswered += sum(1 for pid in unreadable if again is None or (pid in again and self.reader(pid) is None))

    def start(self) -> "CpuMeter":
        if self._thread is None:
            self._sample()                                      # baseline: every pid already there is pre-existing
            self._started = True
            self._stop.clear()

            def loop():
                while not self._stop.wait(self.interval_s):
                    self._sample()
            self._thread = threading.Thread(target=loop, daemon=True)
            self._thread.start()
        return self

    def close(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=5)
            self._thread = None
        for fn in (self.lister, self.pgss):
            closer = getattr(fn, "close", None)
            if callable(closer):
                closer()

    # reading ----------------------------------------------------------------------------------------------------
    def _backend_total(self) -> float:
        if self.pgss:
            return max(0.0, self._pgss_last - (self._pgss_base or 0.0))
        return sum(p["retired"] + p["last"] - p["base"] for p in self._pids.values())

    def _edge(self) -> dict:
        self._sample()
        with self._lock:
            return {"t": time.time(), "self": self.self_cpu() - self._overhead, "backend": self._backend_total()}

    @contextlib.contextmanager
    def measure(self, stage: str | Callable[[], str]):
        """Time a block.  `stage` may be a callable resolved AFTER the block (the build learns a step's kind only when the call returns).  The block's attributed CPU
        is also left in `box['cpu_s']` (None when unknown) for the caller that stores it per step."""
        box: dict = {"cpu_s": None}
        with self._lock:
            self._unanswered, self._load_max = 0, 0.0
        a = self._edge()
        try:
            yield box
        finally:
            b = self._edge()
            with self._lock:
                name = stage() if callable(stage) else stage
                s = self.stages.setdefault(name, {"wall_s": 0.0, "self_cpu_s": 0.0, "backend_cpu_s": 0.0, "unanswered_samples": 0, "load_per_core_max": 0.0, "n": 0})
                s["wall_s"] += b["t"] - a["t"]
                s["self_cpu_s"] += max(0.0, b["self"] - a["self"])
                s["backend_cpu_s"] += max(0.0, b["backend"] - a["backend"])
                s["unanswered_samples"] += self._unanswered
                s["load_per_core_max"] = max(s["load_per_core_max"], self._load_max)
                s["n"] += 1
                box["cpu_s"] = None if s["unanswered_samples"] else round(max(0.0, b["self"] - a["self"]) + max(0.0, b["backend"] - a["backend"]), 3)

    def record(self) -> dict:
        stages = {}
        for name, s in sorted(self.stages.items()):
            unknown = s["unanswered_samples"] > 0 or not self.available
            backend = None if unknown else round(s["backend_cpu_s"], 3)
            stages[name] = {"wall_s": round(s["wall_s"], 3), "self_cpu_s": round(s["self_cpu_s"], 3), "backend_cpu_s": backend,
                            "cpu_s": None if unknown else round(s["self_cpu_s"] + s["backend_cpu_s"], 3), "unanswered_samples": s["unanswered_samples"],
                            "backend_cpu_observed_s": round(s["backend_cpu_s"], 3), "load_per_core_max": round(s["load_per_core_max"], 3), "n": s["n"]}
        by_kind: dict = {}
        for name, s in stages.items():
            if name.startswith("build:") and name != "build:empty" and s["cpu_s"] is not None:
                by_kind[name.split(":", 1)[1]] = round(by_kind.get(name.split(":", 1)[1], 0.0) + s["cpu_s"], 3)
        unknown_stages = sorted(n for n, s in stages.items() if s["cpu_s"] is None)
        loads = [s["load_per_core_max"] for s in stages.values()]
        return {"schema": SCHEMA, "available": bool(self.available and stages and not unknown_stages), "reason": self.reason or (
                    f"stages with unanswered samples: {unknown_stages}" if unknown_stages else None if stages else "no stage was measured"),
                "source": {**self.source, "probe": self.probe}, "interval_s": self.interval_s, "ncpu": self.ncpu,
                "sampler_overhead_s": round(self._overhead, 3), "stages": stages, "by_step_kind": dict(sorted(by_kind.items())),
                "load_per_core_max": max(loads) if loads else None,
                "note": "cpu_s = harness-process user+sys (threads, reaped children, sampler overhead subtracted) + the trial database's backends; a stage with any "
                        "unanswered sample is null (unknown, never zero); a backend that lived and died between two samples loses at most its CPU after the last sighting"}

    def load(self, rec: dict | None) -> None:
        """Resume: restore the stage accumulators of a previous `record()` (the pid table is per process and starts afresh)."""
        for name, s in ((rec or {}).get("stages") or {}).items():
            self.stages[name] = {"wall_s": s["wall_s"], "self_cpu_s": s["self_cpu_s"], "backend_cpu_s": s.get("backend_cpu_observed_s") or 0.0,
                                 "unanswered_samples": s.get("unanswered_samples") or (0 if s.get("cpu_s") is not None else 1),
                                 "load_per_core_max": s.get("load_per_core_max") or 0.0, "n": s.get("n") or 1}


class UnavailableMeter:
    """The meter when there is nothing to attribute backends to (no trial database): every stage is unknown, the record says why (N.8: null, never a zero)."""

    def __init__(self, why: str):
        self.why, self.stages = why, {}

    @contextlib.contextmanager
    def measure(self, stage):
        yield {"cpu_s": None}

    def record(self) -> dict:
        return {"schema": SCHEMA, "available": False, "reason": self.why, "source": {"backend": None}, "stages": {}, "by_step_kind": {}, "load_per_core_max": None}

    def close(self) -> None:
        pass


def make_meter(admin_dsn: str, database: str | None, state: dict | None = None, *, application_name: str | None = None, **kw):
    """The harness's meter: pg_stat_statements when preloaded, else the OS CPU of the trial database's backends.  Restores `state['g5_cpu']` on a resume."""
    if not database:
        return UnavailableMeter("no trial database to attribute backend CPU to")
    pgss, info = pgss_reader(admin_dsn, database)
    m = CpuMeter(trial_backend_pids(admin_dsn, database, application_name), pgss=pgss, pgss_info=info, **kw)
    m.load((state or {}).get("g5_cpu"))
    return m.start()


# ── projection and method selection ────────────────────────────────────────────────────────────────────────────

def cpu_projection(report: dict, profile: dict, runtime_projection: Callable[[dict, dict], dict]) -> dict:
    """The wall method's projection, fed attributed CPU seconds per step kind: same formula, same r, same limit.  projected_writer_s is None when the CPU record is
    absent or incomplete."""
    blk = report.get("g5_cpu") or {}
    kinds = blk.get("by_step_kind") or {}
    view = dict(report)
    view["runtime_s"] = {**(report.get("runtime_s") or {}), "by_step_kind": kinds}
    proj = runtime_projection(view, profile)
    proj["basis"] = ATTRIBUTED_CPU
    if not blk.get("available") or not kinds:
        proj["projected_writer_s"] = None
        proj["projected_writer_s_refined"] = None
        proj["unavailable_reason"] = blk.get("reason") or "no attributed-CPU record in the report"
    return proj


def select(report: dict, profile: dict) -> dict:
    """Which method may G-5 use?  See the module docstring.  Returns {method, reason, inputs}; method None = neither (NOT_EVALUATED)."""
    rt = profile.get("runtime") or {}
    bound = float(rt.get("max_load_per_core", DEFAULT_MAX_LOAD_PER_CORE))
    need = len(profile.get("trial_classes") or []) or DEFAULT_TRIAL_CLASSES
    have = len((report.get("config") or {}).get("classes") or [])
    blk = report.get("g5_cpu")
    out = {"method": None, "reason": None, "inputs": {"max_load_per_core": bound, "trial_classes": have, "classes_required": need,
                                                      "load_per_core_max": None if not blk else blk.get("load_per_core_max"),
                                                      "backend_source": None if not blk else (blk.get("source") or {}).get("backend"),
                                                      "cpu_record_available": None if not blk else bool(blk.get("available"))}}
    if blk is None:
        out.update(method=WALL, reason="a report without an attributed-CPU section: the wall method as before (no load record to test it against)", legacy=True)
        return out
    if have < need:
        out["reason"] = f"the slice has {have} of the {need} trial classes: the century formula would multiply the class-less head by 26/{have} (invalid for both methods)"
        return out
    load = blk.get("load_per_core_max")
    if load is not None and load <= bound:
        out.update(method=WALL, reason=f"load per core {load} ≤ {bound} over every measured stage")
        return out
    why_wall = "the load per core was never sampled" if load is None else f"load per core {load} > {bound}"
    if blk.get("available") and blk.get("by_step_kind"):
        out.update(method=ATTRIBUTED_CPU, reason=f"{why_wall}; attributed CPU used ({(blk.get('source') or {}).get('backend')})")
        return out
    out["reason"] = f"{why_wall}, and the attributed-CPU record is unavailable: {blk.get('reason')}"
    return out


def _replace(checks: list[dict], prefix: str, new: dict | None) -> list[dict]:
    out, done = [], False
    for c in checks:
        if c["claim"].startswith(prefix):
            if new is not None and not done:
                out.append(new)
            done = True
        else:
            out.append(c)
    return out if done or new is None else out + [new]


def apply_to_gate(g5: dict, report: dict, profile: dict, *, check, roll_up, runtime_projection) -> dict:
    """Post-process the G-5 gate that `gates.g5_runtime` (+ the T17 extras) produced: choose the method and make the wall-based checks say so.
    `check` / `roll_up` are gates.check / gates.roll_up (passed in: gates imports this module)."""
    sel = select(report, profile)
    g5["projection_method"] = sel
    method = sel["method"]
    if method == WALL:
        return g5
    checks = g5["checks"]
    wall_note = f"wall method not usable: {sel['reason']}"
    g5["wall_method"] = {"status": "NOT_EVALUATED", "reason": sel["reason"]}
    if method is None:
        for prefix in (WALL_CLAIM, EFFECTIVE_CLAIM, VERIFIER_CLAIM):
            for c in checks:
                if c["claim"].startswith(prefix):
                    c.update(status="NOT_EVALUATED", note=wall_note)
        g5["status"] = roll_up(checks)
        return g5
    blk = report["g5_cpu"]
    proj = cpu_projection(report, profile, runtime_projection)
    limit, cpu_s = proj.get("limit_s"), proj.get("projected_writer_s")
    cpu_check = check("projected century writer time (attributed CPU) ≤ limit", None if cpu_s is None or limit is None else cpu_s <= limit, cpu_s, limit,
                      note=f"{wall_note}; same formula and r as the wall method, CPU seconds per step kind; backend source {(blk.get('source') or {}).get('backend')}")
    checks = _replace(checks, WALL_CLAIM, cpu_check)
    # T17: the lock wait is real elapsed time CPU cannot see, so it is added back (observed, projected like the CPU) rather than dropped
    ew = (report.get("effective_wall") or {}).get("stages") or {}
    writer = {s: v for s, v in ew.items() if s.startswith("build:")}
    lock = [v.get("lock_wait_s") for v in writer.values()]
    scale = (proj.get("century_classes") or 0) / proj["trial_classes"] * (proj.get("r") or 0) * proj.get("speed_factor", 1.0) if proj.get("trial_classes") else None
    if cpu_s is None or limit is None or not writer or scale is None or any(x is None for x in lock):
        eff = check(EFFECTIVE_CLAIM + " ≤ limit [attributed CPU + lock wait]", None, None, limit, note=f"{wall_note}; lock wait or CPU unknown")
    else:
        lock_s = round(sum(lock) * scale, 1)
        eff = check(EFFECTIVE_CLAIM + " ≤ limit [attributed CPU + lock wait]", cpu_s + lock_s <= limit, {"projected_cpu_s": cpu_s, "projected_lock_wait_s": lock_s,
                    "effective_s": round(cpu_s + lock_s, 1)}, limit, note=f"{wall_note}; the lock wait is the sampled elapsed wait, not CPU")
    checks = _replace(checks, EFFECTIVE_CLAIM, eff) if any(c["claim"].startswith(EFFECTIVE_CLAIM) for c in checks) else checks
    # the verifier half: whole-stage attributed CPU of the verify stage per class (an upper bound of the solver check's own CPU), projected by r
    cap = (profile.get("runtime") or {}).get("verifier_solver_check_s_per_class", 600)
    vstages = {s.split(":", 1)[1]: v["cpu_s"] for s, v in (blk.get("stages") or {}).items() if s.startswith("verify:") and v.get("cpu_s") is not None}
    vclaim = "verifier solver check ≤ per-class budget (attributed CPU of the whole verify stage, an upper bound; projected to the century horizon)"
    if not vstages or not proj.get("r"):
        vcheck = check(vclaim, None, "no per-class verify-stage CPU", cap, note=wall_note)
    else:
        worst = max(vstages.items(), key=lambda kv: kv[1])
        vcheck = check(vclaim, worst[1] * proj["r"] <= cap, {"worst_class": worst[0], "measured_cpu_s": worst[1], "projected_s": round(worst[1] * proj["r"], 2)}, cap, note=wall_note)
    checks = _replace(checks, VERIFIER_CLAIM, vcheck)
    g5["checks"] = checks
    g5["status"] = roll_up(checks)
    g5["projection"] = proj
    g5["wall_projection_not_used"] = True
    return g5


def inputs_digest(report: dict) -> str | None:
    blk = report.get("g5_cpu")
    return None if not blk else hashlib.sha256(json.dumps({"stages": blk.get("stages"), "source": blk.get("source"), "by_step_kind": blk.get("by_step_kind")},
                                                          sort_keys=True).encode()).hexdigest()


def equivalence_fields(state: dict) -> dict:
    """What G-5 contributes to the EQUIVALENCE_RECORD's runtime block (a rolling-diagnostic runtime: informational, E4 is not built for it): the method inputs."""
    blk = state.get("g5_cpu")
    if not blk:
        return {"g5_method_inputs": None}
    return {"g5_method_inputs": {"schema": SCHEMA, "backend_source": (blk.get("source") or {}).get("backend"), "reader": (blk.get("source") or {}).get("reader"),
                                 "load_per_core_max": blk.get("load_per_core_max"), "cpu_record_available": bool(blk.get("available")),
                                 "by_step_kind": blk.get("by_step_kind"), "inputs_sha256": inputs_digest({"g5_cpu": blk}),
                                 "method_selected_by": "g5_cpu.select at gate evaluation (see the verdict's gates.G-5.projection_method)"}}


def runtime_platform() -> dict:
    return {"system": platform.system(), "machine": platform.machine(), "python": platform.python_version()}
