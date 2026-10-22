"""SR-OD1 R8X (TRIAL_READY T17, R8X half) — the two-shard OVERLAP harness on the disposable fixture.

Claims — each has ONE oracle here and the single planted reversion that must make it fail (applied to a copy under the job folder; see result.json):
  T17a the job measures LOCK WAIT apart from COMPUTE: a class that waits for the chart lock reports the wait, and its compute excludes it (the serial projection of the wall rule reads compute)
       — revert: `take_locks` does not time the acquisition
  T17b the harness runs two shards TOGETHER on the fixture and reports, per shard, wall = lock wait + compute and, for the pair, the overlap, the union (effective) wall and the speedup
       — revert: start the shards one after the other (no barrier)
Doctrine: A10.1 B4 / G-5 (the effective wall, lock wait apart from compute), §N.8 (an unmeasured wall is null — `test_b4_a_class_not_started_by_the_run_has_no_wall`).
The world builds ONE class, so the two shards verify that class: the test measures the MECHANISM (the chart lock, the wait, the overlap); the 26-class, seven-shard timing is the trial's.
"""
from __future__ import annotations

import json
import threading
import time

import pytest

from services.gochara_kernel import numerical_window_gate as nwg
from services.gochara_kernel import verification_job as vj

from ._overlap_harness import run_overlap
from .test_a53_inventory import CHART_ID
from .test_a53_p1_support import GEN
from .test_a53_r10_complete_records import CLS, _kwargs, _job_position, LIBRA, built, login, rworld  # noqa: F401
from .test_a53_r12_seal_job import built_numbers  # noqa: F401
from .test_a53_verification_job import PASSWORD

IMAGE = "sha256:" + "1" * 64
EXECUTION = "projects/p/locations/l/jobs/gochara-verification-job/executions/e1"
HOLD_S = 1.5

# G8: opts out of the census by name (conftest.g8_census_opt_out): the world builds one class and the harness measures the lock / overlap mechanism, not the class census
G8_CENSUS_OPT_OUT_REASON = "two-shard overlap and lock-wait measurement on a deliberate one-class marriage world (SR-OD1 R8X)"
pytestmark = pytest.mark.usefixtures("g8_census_opt_out")


@pytest.fixture(autouse=True)
def _job_identity(monkeypatch):
    monkeypatch.setenv("GOCHARA_RUNNER_IMAGE_DIGEST", IMAGE)
    monkeypatch.setenv("CLOUD_RUN_EXECUTION", EXECUTION)


def _walls(w):
    rows = [r[0] if isinstance(r[0], dict) else json.loads(r[0]) for r in w.conn.execute(
        "SELECT runner_identity FROM public.ka_gochara_eval_window_verification ORDER BY path_id").fetchall()]
    return [r.get(nwg.WALL_KEY) for r in rows]


def _kw(w):
    return _kwargs(w, _job_position(w, [LIBRA]))


def test_t17a_a_class_that_waits_for_the_chart_lock_reports_the_wait_apart_from_its_compute(built_numbers, monkeypatch):
    import psycopg
    w = built_numbers
    acquired, release = threading.Event(), threading.Event()

    def blocker():
        with psycopg.connect(w.dsn, autocommit=True) as c, c.transaction():
            c.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
            acquired.set()
            time.sleep(HOLD_S)
        release.set()

    started = vj._class_started

    def started_then_blocked(cls):                                  # the class clock has started: a sibling now takes the chart lock and holds it for HOLD_S
        started(cls)
        threading.Thread(target=blocker, daemon=True).start()
        assert acquired.wait(10)
    monkeypatch.setattr(vj, "_class_started", started_then_blocked)
    kw = _kw(w)
    with login(w, "gochara_verifier") as conn:
        t0 = time.monotonic()
        report = vj.run(conn, chart_id=CHART_ID, generation=GEN, **kw)
        total = time.monotonic() - t0
    assert release.wait(10) and report["status"] == "VERIFIED", report["classes"]
    walls = _walls(w)
    assert len(walls) == 4 and all(x is not None and x["class"] == CLS for x in walls)
    wall = walls[0]
    hold_ms = round((HOLD_S - 0.4) * 1000)
    assert wall["lock_wait_ms"] >= hold_ms, wall                                              # the class waited for the sibling's lock and says so
    assert wall["wall_ms"] == wall["lock_wait_ms"] + wall["compute_ms"], wall                 # wall = lock wait + compute
    assert wall["compute_ms"] <= wall["wall_ms"] - hold_ms and wall["wall_ms"] <= total * 1000 + 1      # the wait is NOT in the compute the wall rule projects from


def test_t17b_two_shards_run_together_and_the_harness_reports_overlap_union_wall_and_lock_wait_apart_from_compute(built_numbers):
    import psycopg
    from psycopg.conninfo import make_conninfo
    w = built_numbers
    kws = [_kw(w), _kw(w)]
    with login(w, "gochara_verifier") as c1:
        with psycopg.connect(make_conninfo(w.dsn, user="gochara_verifier", password=PASSWORD), autocommit=True, connect_timeout=3) as c2:
            res = run_overlap({"A": lambda: vj.run(c1, chart_id=CHART_ID, generation=GEN, **kws[0]), "B": lambda: vj.run(c2, chart_id=CHART_ID, generation=GEN, **kws[1])})
    errs = {n: r.get("error") for n, r in res["shards"].items() if "error" in r}
    assert not errs, errs
    assert all(r["result"]["status"] == "VERIFIED" for r in res["shards"].values())
    assert res["overlapped"] is True and res["overlap_s"] > 0                                  # they ran at the same time (a barrier releases them together)
    for r in res["shards"].values():
        assert r["lock_wait_s"] >= 0 and r["compute_s"] > 0 and abs(r["wall_s"] - r["lock_wait_s"] - r["compute_s"]) < 1e-3
    assert res["union_wall_s"] >= max(r["wall_s"] for r in res["shards"].values()) - 0.01
    assert res["union_wall_s"] <= res["sum_wall_s"] + 0.01 and res["speedup"] is not None and 0.9 <= res["speedup"] <= 2.1
    assert abs(res["lock_wait_total_s"] + res["compute_total_s"] - res["sum_wall_s"]) < 0.01   # the pair's lock wait is reported apart from its compute
    # both shards sat on the chart lock for their class transactions: the wait is real and measured, not assumed zero
    assert res["lock_wait_total_s"] > 0
    assert nwg.generation_verdict(w.conn, CHART_ID, GEN, classes=[CLS])["status"] == "PASSED"      # the rows the pair left are one coherent set


def test_t17b_the_harness_overlap_arithmetic_on_plain_callables():
    res = run_overlap({"A": lambda: time.sleep(0.4), "B": lambda: time.sleep(0.4)})
    assert res["overlapped"] and res["overlap_s"] >= 0.3 and res["union_wall_s"] < 0.7 and res["speedup"] > 1.5
    assert res["lock_wait_total_s"] == 0.0                                                      # no database lock was taken: no wait is invented
    bad = run_overlap({"A": lambda: 1, "B": lambda: (_ for _ in ()).throw(RuntimeError("boom"))})
    assert isinstance(bad["shards"]["B"]["error"], RuntimeError) and bad["shards"]["A"]["result"] == 1      # an error is reported, never swallowed
