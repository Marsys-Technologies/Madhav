"""G5-CPU (ruling SR-G5-LOAD): G-5 evaluated from ATTRIBUTED CPU time when the wall method's load bound is broken.

One oracle per distinct production claim; the source of each is in its docstring (SR-G5-LOAD; DEFECT_MAP D-10; N.8 earned signals; N.7.6 honest nulls).  Every
measurement oracle runs REAL work: a CPU-burning builder (this process and a reaped child), a busy SQL statement in a real Postgres backend of a disposable database on
the local cluster (KALA_ADMIN_DSN, default 127.0.0.1:55433; created and dropped here), and, for the loaded cases, real CPU-hog processes.  The cluster does not preload
pg_stat_statements, so the OS-CPU source is what is exercised; the pg_stat_statements branch is exercised with a stub reading (it cannot be switched on without
reconfiguring the cluster, which this item must never do).

Stated tolerances (measured on this Mac 2026-10-22, 18 cores = 6 P + 12 E, shared and busy; see g5_cpu.py's docstring):
  * builder CPU vs the process's own CPU clock: ±10 % + 50 ms (observed +2 %: the sampler's own thread is subtracted);
  * backend CPU vs an independent reading of the same pid (`ref_backend_cpu_s`: the scheduler's /proc/<pid>/schedstat on Linux, `ps -o time=` elsewhere): ±10 % + 40 ms
    (observed ±10 ms: macOS ps has 10 ms resolution; Linux procps prints whole seconds, so on Linux ps cannot be the reference);
  * loaded vs quiet attributed CPU for identical work: within ×1.6 of k, and the growth beyond k × quiet at most half the wall's GROWTH (loaded − quiet, so an ambient
    load on the quiet leg cannot fail it).  k = the CPU cost of the same pure burn under the same hogs over its quiet cost, measured in the same attempt (floored at 1):
    CPU seconds move with core placement (P vs E cores), SMT and cache contention, but not with time spent waiting for a core.  On this Mac k ≈ 1 (observed ×1.16..1.43
    over 9 pairs while the wall projection grew ×3.3..4.7); on the linux/amd64 TR VM (2 threads per core) the SMT sibling roughly doubles the cost (2026-10-23: k-free
    ratio ×2.3 with the wall ×3.6), which is the work's own cost, not waiting;
  * wall vs attributed-CPU projection on a not-oversubscribed fixture-scale slice: within ×1.5 (observed ×1.04..1.10): wall = CPU + off-CPU wait, and a serial CPU-bound
    slice that is not starved waits for less than a third of its time."""
import contextlib
import importlib.util
import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

import pytest

import fixtures as fx
import g5_cpu
import gates
import trial_eval as te
import trial_slice as ts
from gates import FAIL, NOT_EVALUATED, PASS

HARNESS = Path(__file__).resolve().parents[1]
REPO = HARNESS.parents[4]
ADMIN_DSN = os.environ.get("KALA_ADMIN_DSN", "postgresql://postgres@127.0.0.1:55433/postgres")
NCPU = os.cpu_count() or 1
SQL_BUSY = "SELECT sum(i::bigint * i) FROM generate_series(1, %s) i"
KINDS = ("body", "record", "window")


# ── the real cluster (disposable database) ──────────────────────────────────────────────────────────────────────

def _guard():
    path = REPO / "platform" / "python-sidecar" / "tests" / "l3" / "gochara" / "_disposable_db_guard.py"
    spec = importlib.util.spec_from_file_location("_g5_disposable_db_guard", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def cluster():
    try:
        import psycopg
        admin = _guard().guarded_admin_connect(ADMIN_DSN, autocommit=True, connect_timeout=3)
    except Exception as exc:                                                     # noqa: BLE001
        if os.environ.get("KALA_REQUIRE_DB") == "1":
            raise
        pytest.skip(f"no local disposable cluster ({type(exc).__name__}); set KALA_REQUIRE_DB=1 to make this a failure")
    from psycopg.conninfo import make_conninfo
    name = f"ky_g5cpu_{uuid.uuid4().hex[:8]}"
    admin.execute(f'CREATE DATABASE "{name}"')
    try:
        yield {"db": name, "dsn": make_conninfo(ADMIN_DSN, dbname=name), "psycopg": psycopg}
    finally:
        admin.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        admin.close()


@pytest.fixture()
def work(cluster):
    """A work connection opened BEFORE the meter starts (so its backend pre-dates the meter and only its CPU from the baseline counts), and its backend pid."""
    conn = cluster["psycopg"].connect(cluster["dsn"], autocommit=True, connect_timeout=5)
    conn.execute("SELECT 1")
    pid = conn.execute("SELECT pg_backend_pid()").fetchone()[0]
    try:
        yield conn, pid
    finally:
        conn.close()


def make_meter(cluster, **kw):
    return g5_cpu.make_meter(ADMIN_DSN, cluster["db"], **kw)


# ── synthetic builder work ──────────────────────────────────────────────────────────────────────────────────────

def burn(n):
    s = 0
    for i in range(n):
        s += i * i
    return s


def ref_backend_cpu_s(pid):
    """The independent truth for a backend's CPU seconds.  Linux: the scheduler's own on-CPU nanoseconds (/proc/<pid>/schedstat field 1; the meter reads the tick-based
    utime+stime of /proc/<pid>/stat, a different kernel account).  Elsewhere: `ps -o time=` (centiseconds on macOS)."""
    if sys.platform.startswith("linux"):
        return int(Path(f"/proc/{int(pid)}/schedstat").read_text().split()[0]) / 1e9
    return g5_cpu._ps_cpu_s(pid)


def burn_cost(n):
    t = time.process_time()
    burn(n)
    return time.process_time() - t


def calibrate(seconds=0.2):
    t = time.process_time()
    burn(200_000)
    return int(seconds / ((time.process_time() - t) / 200_000))


def run_stage(meter, conn, pid, stage, n_burn, n_sql, child_s=0.0):
    """One stage of fixed work: builder burn in this process, an optional child process that burns, a busy SQL statement in the trial database's backend.  Returns the
    independent truths: this process's own CPU clock over the burn, the child's own clock, ps's reading of the backend, and the wall."""
    truth = {}
    t0 = time.time()
    with meter.measure(stage) as box:
        c0 = time.process_time()
        burn(n_burn)
        truth["own"] = time.process_time() - c0
        truth["child"] = 0.0
        if child_s:
            r = subprocess.run([sys.executable, "-I", "-c", f"import time\nt=time.process_time()\nwhile time.process_time()-t<{child_s}: pass\nprint(time.process_time())"],
                               capture_output=True, text=True, timeout=60)
            truth["child"] = float(r.stdout.strip())
        p0 = ref_backend_cpu_s(pid)
        conn.execute(SQL_BUSY, (n_sql,)).fetchone()
        truth["ps_backend"] = ref_backend_cpu_s(pid) - p0
    truth["wall"] = time.time() - t0
    truth["box"] = box
    return truth


# ── (1) the measurement itself ──────────────────────────────────────────────────────────────────────────────────

def test_c1_attributed_cpu_equals_the_known_work_of_a_builder_and_its_postgres_backend(cluster, work):
    """SR-G5-LOAD: 'user+sys of the builder/verifier processes PLUS their Postgres backends'.  Known work: a fixed-count burn here (truth = this process's own CPU
    clock), a reaped child that burns (truth = its own CPU clock), a busy SQL statement in the trial database's backend (truth = an independent reading, ref_backend_cpu_s of that pid;
    plus scaling: three times the rows costs about three times the CPU).  Planted reversion: the backend term is dropped (`_backend_total` returns 0) → fails."""
    conn, pid = work
    n = calibrate(0.25)
    meter = make_meter(cluster)
    try:
        assert meter.source["backend"] == "os_process_cpu" and meter.available, meter.reason
        small = run_stage(meter, conn, pid, "build:body", n, 3_000_000, child_s=0.2)
        big = run_stage(meter, conn, pid, "build:record", n, 9_000_000)
        rec = meter.record()
    finally:
        meter.close()
    s1, s2 = rec["stages"]["build:body"], rec["stages"]["build:record"]
    builder_truth = small["own"] + small["child"]
    assert s1["self_cpu_s"] == pytest.approx(builder_truth, rel=0.10, abs=0.05), (s1, small)          # builder + reaped child
    assert s1["backend_cpu_s"] == pytest.approx(small["ps_backend"], rel=0.10, abs=0.04), (s1, small)  # the backend, against ps
    assert s1["backend_cpu_s"] > 0.05 and s1["backend_cpu_s"] <= small["wall"] * 1.05                  # a single backend cannot out-run the wall
    assert s1["cpu_s"] == pytest.approx(s1["self_cpu_s"] + s1["backend_cpu_s"], abs=0.002)
    assert 2.0 <= s2["backend_cpu_s"] / s1["backend_cpu_s"] <= 4.0, (s1, s2)                           # 3× the rows ≈ 3× the CPU
    assert small["box"]["cpu_s"] == s1["cpu_s"] and rec["by_step_kind"]["body"] == s1["cpu_s"]


# ── (2) loaded machine: wall is NOT_EVALUATED, attributed CPU stays close to the quiet projection ───────────────

class Hogs:
    """CPU hogs: `count` busy processes.  Their number IS the run queue this test created, so it is the (injected) load the meter samples."""

    def __init__(self, count):
        self.procs = [subprocess.Popen([sys.executable, "-I", "-c", "while True: pass"]) for _ in range(count)]

    def runnable(self):
        return 1.0 + sum(p.poll() is None for p in self.procs)

    def stop(self):
        for p in self.procs:
            p.kill()
        for p in self.procs:
            p.wait()


def slice_world(cluster, conn, pid, n_burn, load_fn):
    """A fixture-scale 'slice': three step kinds, one stage each (fixed work), plus a tiny verify stage per class.  Returns the gate-evaluator's report (a10 world with
    this run's wall seconds and its g5_cpu record)."""
    meter = make_meter(cluster, load_fn=load_fn)
    try:
        for kind, k in zip(KINDS, (1, 2, 1)):
            run_stage(meter, conn, pid, f"build:{kind}", n_burn * k, 1_500_000 * k)
        for cls in gates.TRIAL_CLASSES_12:
            with meter.measure(f"verify:{cls}"):
                burn(2000)
        rec = meter.record()
    finally:
        meter.close()
    r = fx.a10_report()
    kinds = {k: rec["stages"][f"build:{k}"]["wall_s"] for k in KINDS}
    r["runtime_s"]["by_step_kind"] = kinds
    r["effective_wall"] = {"schema": "ky.effective_wall/1", "stages": {f"build:{k}": {"wall_s": w, "lock_wait_s": 0.0, "compute_s": w, "max_load_per_core": rec["stages"][f"build:{k}"]["load_per_core_max"]}      # HARNESS-3.2 D-10: the per-stage load the real stage record carries
                                                                              for k, w in kinds.items()}}
    r["g5_cpu"] = rec
    return r


def verdict(report):
    return gates.evaluate(report, fx.a10_baseline(), fx.profile(), decision_table=fx.decision_table(), second_report=fx.second(),
                          dispatch_modules=fx.dispatch_modules(), dispatch_digests=fx.dispatch_digests())


def test_c2_on_a_loaded_machine_wall_is_not_evaluated_and_attributed_cpu_projects_close_to_the_quiet_one(cluster, work):
    """SR-G5-LOAD: wall when the load bound held, attributed_cpu otherwise.  A quiet run and a run under 2×cores real CPU hogs do identical fixed work.  Under the hogs the
    wall method is NOT usable (method attributed_cpu, no wall projection check survives, `wall_method` NOT_EVALUATED) while the CPU projection stays within ×1.6 of the
    quiet one times k, the same burn's own contention cost (observed ×1.16..1.43 on the Mac) although the wall projection is several times larger.  Planted reversion: `select` ignores the load (always WALL) → the loaded run
    would be judged on its inflated wall → fails."""
    conn, pid = work
    n = calibrate(0.2)
    attempts = []
    for _ in range(3):
        quiet = slice_world(cluster, conn, pid, n, lambda: 1.0)
        k_q = burn_cost(n)
        hogs = Hogs(2 * NCPU)
        try:
            time.sleep(0.5)
            k_l = burn_cost(n)
            loaded = slice_world(cluster, conn, pid, n, hogs.runnable)
        finally:
            hogs.stop()
        wall_q = gates.runtime_projection(quiet, fx.profile())["projected_writer_s"]
        wall_l = gates.runtime_projection(loaded, fx.profile())["projected_writer_s"]
        cpu_q = g5_cpu.cpu_projection(quiet, fx.profile(), gates.runtime_projection)["projected_writer_s"]
        cpu_l = g5_cpu.cpu_projection(loaded, fx.profile(), gates.runtime_projection)["projected_writer_s"]
        attempts.append((quiet, loaded, wall_q, wall_l, cpu_q, cpu_l, max(1.0, k_l / k_q)))
        if wall_l / wall_q >= 1.5:                                                   # the hogs really starved the builder: a valid experiment
            break
    # a machine whose own load already inflates the "quiet" leg's wall can leave an attempt in which the hogs added little: such an attempt is not an experiment
    # (its wall did not grow), so it is retried, never judged; no valid attempt fails the test (never skipped).  Judged on the valid attempt that ends the loop.
    quiet, loaded, wall_q, wall_l, cpu_q, cpu_l, k = attempts[-1]
    assert wall_l / wall_q >= 1.5, [(a[2], a[3]) for a in attempts]                       # the hogs really starved the builder: the wall method would have lied
    vq, vl = verdict(quiet), verdict(loaded)
    gq, gl = vq["gates"]["G-5"], vl["gates"]["G-5"]
    assert gq["projection_method"]["method"] == "wall" and gl["projection_method"]["method"] == "attributed_cpu"
    assert gl["projection_method"]["inputs"]["load_per_core_max"] > 1.0 >= gq["projection_method"]["inputs"]["load_per_core_max"]
    claims = [c["claim"] for c in gl["checks"]]
    assert not [c for c in claims if c.startswith(g5_cpu.WALL_CLAIM) and "(attributed CPU)" not in c], claims       # the wall projection check is gone, not green
    assert any("(attributed CPU)" in c for c in claims)
    assert gl["wall_method"]["status"] == NOT_EVALUATED and "load per core" in gl["wall_method"]["reason"]
    assert gl["status"] == PASS and gq["status"] == PASS                                      # the CPU method yields a real verdict under load
    # the same claim, ambient-load-robust: CPU seconds do not follow time spent waiting for a core.  Judged on GROWTH (loaded − quiet) in the same experiment, so an
    # ambient load that already inflated the quiet leg's wall (and so shrank the wall RATIO) cannot fail it: the CPU growth beyond the work's own contention cost (k, the
    # same burn's CPU under the same hogs; SMT siblings and cache, not waiting) is at most half the wall growth, and the CPU ratio stays within ×1.6 of k.
    assert k / 1.6 <= cpu_l / cpu_q <= k * 1.6 and (cpu_l - k * cpu_q) <= (wall_l - wall_q) / 2, (cpu_q, cpu_l, wall_q, wall_l, k)
    assert gl["projection"]["basis"] == "attributed_cpu" and gl["projection"]["projected_writer_s"] == pytest.approx(cpu_l, abs=0.1)


# ── (3) the projection IS the wall formula with the same r ──────────────────────────────────────────────────────

def test_c3_the_cpu_projection_is_the_wall_formula_fed_cpu_seconds_with_the_walls_r():
    """DEFECT_MAP D-10 / PLAN §4.3: (base_s + solver_s) · (26/trial_classes) · r · speed.  Feed the CPU seconds (half the wall seconds here) and a century horizon twice the
    trial's: the CPU projection equals `runtime_projection` on those seconds — same r (2), same scale, same limit — and is half the wall projection.  Planted reversion:
    `cpu_projection` takes the wall seconds (`view = report`) → equals the wall projection → fails."""
    r, b, p = fx.good()
    p["runtime"]["century_horizon"] = ["1998-01-01T00:00:00+00:00", "2170-03-12T00:00:00+00:00"]              # r ≈ 2
    wall = r["runtime_s"]["by_step_kind"]
    cpu = {k: v / 2 for k, v in wall.items()}
    r["g5_cpu"] = {"available": True, "by_step_kind": cpu, "source": {"backend": "os_process_cpu"}, "stages": {}, "load_per_core_max": 3.0}
    proj = g5_cpu.cpu_projection(r, p, gates.runtime_projection)
    ref = gates.runtime_projection({**r, "runtime_s": {**r["runtime_s"], "by_step_kind": cpu}}, p)
    for k in ("base_s", "solver_s", "r", "trial_classes", "century_classes", "projected_writer_s", "projected_writer_s_refined", "limit_s"):
        assert proj[k] == ref[k], k
    wall_proj = gates.runtime_projection(r, p)
    assert proj["r"] == pytest.approx(2.0, rel=1e-3) == wall_proj["r"]
    assert proj["projected_writer_s"] == pytest.approx(wall_proj["projected_writer_s"] / 2, abs=0.2)


# ── (4) agreement on a quiet fixture-scale slice ────────────────────────────────────────────────────────────────

def test_c4_wall_and_attributed_cpu_projections_agree_within_a_stated_factor_on_a_quiet_small_slice(cluster, work):
    """A real class is hours long, so the agreement is measured on a fixture-scale slice (three step kinds of fixed CPU work in this process and its backend, ≈ 2 s).
    Stated factor ×1.5 either way (module docstring): wall = CPU + off-CPU wait.  The machine here is shared, so the agreement is judged NORMALISED by a same-process calibrated reference (the wall per CPU second of a pure fixed burn
    measured around the slice: ambient waiting multiplies both, so it cancels), on the best of up to 5 attempts; it is never skipped.  Planted reversion: `record()` builds `by_step_kind` from `self_cpu_s` only (the backend share is lost) → ratio ≈ 2.8 → fails."""
    conn, pid = work
    n = calibrate(0.2)

    def starvation():
        """The same-process calibrated reference: wall seconds per CPU second of a pure fixed burn right now (1.0 on a free core; > 1 when ambient load makes this process wait)."""
        t, c = time.time(), time.process_time()
        burn(n)
        return max(1.0, (time.time() - t) / (time.process_time() - c))

    attempts = []
    for _ in range(5):
        ref0 = starvation()
        rep = slice_world(cluster, conn, pid, n, lambda: os.getloadavg()[0])
        ref = (ref0 + starvation()) / 2
        wall = gates.runtime_projection(rep, fx.profile())["projected_writer_s"]
        cpu = g5_cpu.cpu_projection(rep, fx.profile(), gates.runtime_projection)["projected_writer_s"]
        attempts.append((wall / cpu / ref, wall / cpu, ref, wall, cpu))              # the agreement NORMALISED by the reference's own wait: ambient load cancels, a lost CPU share does not
        if wall / cpu / ref <= 1.5:
            break
    norm, ratio, ref, wall, cpu = min(attempts)
    assert 0.9 <= norm <= 1.5, attempts
    assert wall > 0 and cpu > 0


# ── (5) a missing backend source is NOT_EVALUATED, never PASS ───────────────────────────────────────────────────

def test_c5_an_unreachable_backend_source_makes_the_stage_unknown_and_g5_not_evaluated(cluster, work):
    """N.8 / SR-G5-LOAD ('if neither method is available G-5 reads NOT_EVALUATED and the dispatch gate refuses').  The lister cannot reach the cluster (port 1): backend CPU
    is UNKNOWN for the stage (null, not 0.0), the record is unavailable, and on a loaded run (wall invalid) the verdict's G-5 is NOT_EVALUATED, the overall verdict is not
    dispatchable.  Planted reversion: an unanswered sample is read as 'no backend CPU' (`backend = round(s["backend_cpu_s"], 3)` regardless) → a number appears → fails."""
    n = calibrate(0.1)
    meter = g5_cpu.CpuMeter(g5_cpu.trial_backend_pids("postgresql://postgres@127.0.0.1:1/postgres", cluster["db"]), load_fn=lambda: 4.0 * NCPU)
    try:
        meter.start()
        for kind in KINDS:
            with meter.measure(f"build:{kind}"):
                burn(n)
        rec = meter.record()
    finally:
        meter.close()
    st = rec["stages"]["build:body"]
    assert st["backend_cpu_s"] is None and st["cpu_s"] is None and st["unanswered_samples"] > 0
    assert rec["available"] is False and rec["by_step_kind"] == {} and "unanswered" in rec["reason"]
    r = fx.a10_report()
    r["g5_cpu"] = rec
    g5 = verdict(r)["gates"]["G-5"]
    assert g5["projection_method"]["method"] is None
    assert g5["status"] == NOT_EVALUATED
    v = verdict(r)
    assert "G-5" in v["not_evaluated"] and v["dispatchable"] is False and v["overall"] != "DISPATCH_GATE_MET"
    assert all(c["status"] == NOT_EVALUATED for c in g5["checks"] if c["claim"].startswith((g5_cpu.WALL_CLAIM, g5_cpu.EFFECTIVE_CLAIM, g5_cpu.VERIFIER_CLAIM)))


def test_c6_an_os_reader_that_returns_plausible_zeros_or_a_wrong_scale_fails_its_self_check():
    """N.8 earned signal: the OS source proves itself on a known burn before it is trusted (reader vs getrusage).  A reader that always answers 0.0 (a number that looks
    fine) or one that answers at half scale (a wrong mach timebase) reads `available: false` with the reason, so no cpu number is ever produced from it.  Planted reversion:
    `probe_reader` returns True unconditionally → the meter is 'available' → fails."""
    real = g5_cpu.default_reader()
    for label, reader in (("zeros", lambda pid: 0.0), ("half scale", lambda pid: (real(pid) or 0.0) / 2)):
        meter = g5_cpu.CpuMeter(lambda: [], reader)
        assert meter.available is False and "self-check" in meter.reason, label
        with meter.measure("build:body"):
            burn(1000)
        assert meter.record()["available"] is False and meter.record()["stages"]["build:body"]["cpu_s"] is None, label
    ok, detail = g5_cpu.probe_reader(real)
    assert ok, detail                                                                          # the real reader passes the same check


# ── selection: wall when the bound held, neither when the slice is not the trial ────────────────────────────────

def cpu_block(load, kinds=None, **over):
    kinds = kinds or {"body": 100.0, "record": 800.0, "window": 50.0}
    blk = {"schema": g5_cpu.SCHEMA, "available": True, "reason": None, "source": {"backend": "os_process_cpu"}, "by_step_kind": kinds, "load_per_core_max": load,
           "stages": {f"verify:{c}": {"cpu_s": 10.0} for c in gates.TRIAL_CLASSES_12}}
    blk.update(over)
    return blk


def test_c7_wall_is_used_unchanged_when_the_load_bound_held():
    """SR-G5-LOAD: 'wall when the load bound held'.  At load per core ≤ 1.0 the G-5 gate is EXACTLY what the wall method gave before this item (same checks, same
    numbers), only the method is recorded.  Planted reversion: `select` prefers attributed CPU whenever it is available → the wall check disappears → fails."""
    r = fx.a10_report()
    before = verdict(r)["gates"]["G-5"]
    r["g5_cpu"] = cpu_block(0.4, kinds={"body": 1.0, "record": 1.0, "window": 1.0})            # CPU seconds wildly different from the wall seconds: they must not be used
    g5 = verdict(r)["gates"]["G-5"]
    assert g5["projection_method"]["method"] == "wall"
    assert g5["checks"] == before["checks"] and g5["projection"] == before["projection"] and g5["status"] == before["status"]


def test_c8_a_slice_smaller_than_the_trial_is_invalid_for_both_methods():
    """DEFECT_MAP D-10: with 1 trial class the class-less head is multiplied by 26 (54 % of the 107 k s) — a slice artefact CPU time does not repair.  A 1-class slice
    reads NOT_EVALUATED whatever the load and whatever CPU record exists.  Planted reversion: the class-count test is removed from `select` → the loaded 1-class
    slice is judged on its CPU → fails."""
    for load in (0.2, 3.0):
        r = fx.a10_report()
        r["config"]["classes"] = ["bereavement"]
        r["g5_cpu"] = cpu_block(load)
        g5 = verdict(r)["gates"]["G-5"]
        assert g5["projection_method"]["method"] is None and "1 of the 12" in g5["projection_method"]["reason"], load
        assert g5["status"] == NOT_EVALUATED, load


def test_c9_a_report_without_a_cpu_record_keeps_the_wall_method_and_says_so():
    """Compatibility: reports written before this item carry no `g5_cpu`; they are judged exactly as before and the verdict names the method."""
    r = fx.a10_report()
    g5 = verdict(r)["gates"]["G-5"]
    assert g5["projection_method"]["method"] == "wall" and g5["projection_method"]["legacy"] is True and g5["status"] == PASS


def test_c10_loaded_with_an_incomplete_cpu_record_and_an_unsampled_load_are_not_wall():
    """An unsampled load is not 'quiet' (N.8): without a load sample the wall method is not asserted, and a CPU record that is not available leaves nothing → neither."""
    r = fx.a10_report()
    r["g5_cpu"] = cpu_block(None, available=False, reason="x", by_step_kind={})
    assert g5_cpu.select(r, fx.profile())["method"] is None
    r["g5_cpu"] = cpu_block(None)
    assert g5_cpu.select(r, fx.profile())["method"] == "attributed_cpu"


def test_c11_the_verifier_half_is_judged_on_cpu_too_and_a_bust_fails():
    """The verifier's per-class budget (600 s) is projected from the verify stage's attributed CPU when the wall is invalid; over it → FAIL, no CPU record → NOT_EVALUATED."""
    r = fx.a10_report()
    r["g5_cpu"] = cpu_block(3.0)
    assert verdict(r)["gates"]["G-5"]["status"] == PASS
    r["g5_cpu"]["stages"]["verify:bereavement"] = {"cpu_s": 601.0}
    g5 = verdict(r)["gates"]["G-5"]
    assert g5["status"] == FAIL and [c for c in g5["checks"] if c["claim"].startswith(g5_cpu.VERIFIER_CLAIM) and c["status"] == FAIL]
    r["g5_cpu"]["stages"] = {}
    assert verdict(r)["gates"]["G-5"]["status"] == NOT_EVALUATED


def test_c12_a_cpu_projection_over_the_limit_fails_and_the_lock_wait_is_added_back():
    """The CPU method is a real gate, not a free pass: a CPU projection over the limit FAILs; and T17's point survives — lock wait is elapsed time CPU cannot see, so the
    effective figure is projected CPU + projected lock wait (a large measured lock wait fails an otherwise passing CPU figure)."""
    r = fx.a10_report()
    r["g5_cpu"] = cpu_block(3.0, kinds={"body": 100.0, "record": 40000.0, "window": 50.0})
    assert verdict(r)["gates"]["G-5"]["status"] == FAIL
    r = fx.a10_report()
    r["g5_cpu"] = cpu_block(3.0)
    r["effective_wall"]["stages"]["build:record"].update({"wall_s": 30000.0, "lock_wait_s": 20000.0, "compute_s": 10000.0})
    g5 = verdict(r)["gates"]["G-5"]
    eff = [c for c in g5["checks"] if c["claim"].startswith(g5_cpu.EFFECTIVE_CLAIM)][0]
    assert eff["status"] == FAIL and eff["observed"]["projected_lock_wait_s"] > 0 and g5["status"] == FAIL


# ── the source of the backend term ──────────────────────────────────────────────────────────────────────────────

def test_c13_pg_stat_statements_is_the_backend_source_when_preloaded_otherwise_the_os_source_is_recorded(cluster):
    """SR-G5-LOAD: pg_stat_statements total_exec_time if the extension is loaded; if NOT preloaded, the OS CPU of the backend pids — and the record says which.  The
    cluster here is not preloaded (the OS source is recorded); the extension branch is exercised with a stub reading whose delta is the backend term.  Planted reversion:
    the stub is ignored (`pgss` never consulted) → the source reads os_process_cpu → fails."""
    reader, info = g5_cpu.pgss_reader(ADMIN_DSN, cluster["db"])
    if info.get("preloaded") is False:
        assert reader is None
        meter = make_meter(cluster)
        try:
            assert meter.source["backend"] == "os_process_cpu" and meter.source["preloaded"] is False and meter.source["reader"]
        finally:
            meter.close()
    readings = iter([10.0, 12.5])
    stub = lambda: next(readings, 12.5)                                                       # noqa: E731
    meter = g5_cpu.CpuMeter(lambda: [], pgss=stub, pgss_info={"preloaded": True}, interval_s=60)
    with meter.measure("build:body"):
        burn(1000)
    rec = meter.record()
    assert rec["source"]["backend"] == "pg_stat_statements" and rec["source"]["preloaded"] is True
    assert rec["stages"]["build:body"]["backend_cpu_s"] == pytest.approx(2.5)


# ── wiring into the trial driver ────────────────────────────────────────────────────────────────────────────────

def test_c14_the_verify_stage_measures_each_class_with_the_meter(monkeypatch, tmp_path):
    """The verifier half needs per-class attributed CPU: `verify_stage` records a `verify:<class>` stage in state['g5_cpu'].  Planted reversion: the meter is dropped from
    the stage's `with` → the stage is absent → fails."""
    import test_t1b_fix as t1b
    vj, real_census, conn = t1b._verify_world(monkeypatch, {})
    monkeypatch.setattr(ts, "make_cpu_meter", lambda state: g5_cpu.CpuMeter(lambda: [], lambda pid: 0.0, probe=False, interval_s=60))
    state = {"classes": ["bereavement", "major_loss"], "verification": {"classes": {}, "ran": False}}
    assert ts.verify_stage(state, tmp_path, conn, None) is True
    assert sorted(s for s in state["g5_cpu"]["stages"] if s.startswith("verify:")) == ["verify:bereavement", "verify:major_loss"]


def test_c15_the_method_inputs_ride_the_equivalence_record(monkeypatch, tmp_path):
    """SR-G5-LOAD: 'the harness records which method was used' in the TR report and the EQUIVALENCE_RECORD fields G-5 feeds.  The pinned inputs' runtime block (a rolling
    diagnostic: informational) and the stage's summary both carry the CPU source, the sampled load and the inputs digest.  Planted reversion: `equivalence_stage` does not
    merge the fields → fails."""
    (tmp_path / "input_vector.json").write_text(json.dumps({"ephemeris": {}}))
    seen = {}
    monkeypatch.setattr(te, "emit_equivalence_record", lambda repo, head, pinned, out_dir, **kw: seen.update(pinned=pinned) or {"status": "COMPLETE"})
    state = {"code": {"head": "a" * 40, "branch": "b"}, "g5_cpu": cpu_block(2.5)}
    rec = ts.equivalence_stage(state, tmp_path, "/repo", None, None, None)
    for doc in (seen["pinned"]["runtime"]["g5_method_inputs"], rec["g5_method_inputs"]):
        assert doc["backend_source"] == "os_process_cpu" and doc["load_per_core_max"] == 2.5 and len(doc["inputs_sha256"]) == 64 and doc["cpu_record_available"] is True
    assert seen["pinned"]["runtime"]["kind"] == "rolling_diagnostic"
