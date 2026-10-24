"""T1B harness v3.1 — the review's BLOCKING findings (B1, B2, B3) and the dispatch-path fixes (N2, N3, N4).  One oracle per distinct claim; each fails on its single
planted reversion (§N.8: a signal without a detector that can read false is null, not green; testing standard ii)."""
import copy
import os
import subprocess
import sys
import types
from pathlib import Path

import pytest

import fixtures as fx
import gates
import trial_eval as te
import trial_slice as ts
from gates import FAIL, NOT_EVALUATED, PASS

HERE = Path(__file__).resolve().parent
HARNESS = HERE.parent
T = fx.decision_table()


def ev(r, b=None, p=None, **kw):
    gr, gb, gp = fx.a10_good()
    return gates.evaluate(r, b if b is not None else gb, p if p is not None else gp, second_report=fx.second(), dispatch_modules=fx.dispatch_modules(),
                          dispatch_digests=kw.get("dispatch_digests", fx.dispatch_digests()), decision_table=T)


def claims(v, gid, *needles):
    return [c for c in v["gates"][gid]["checks"] if any(n in c["claim"] for n in needles)]


# ── B1 (§N.8): the reason census must be present and account for every blank window, or the absence-of-a-reason checks are not evaluated ──────────────────────

def _no_census(r):
    r = copy.deepcopy(r)
    r.pop("reason_windows_any")
    r["totals"].pop("blank_reasons")
    return r


def _empty_census(r):
    r = copy.deepcopy(r)
    r["reason_windows_any"], r["totals"]["blank_reasons"] = {}, {}
    return r


def _short_census(r):
    r = copy.deepcopy(r)
    r["totals"]["blank_reasons"]["state_boundaries_incomplete"] -= 1          # accounts for 134 of 135 blank windows
    return r


@pytest.mark.parametrize("make", [_no_census, _empty_census, _short_census], ids=["absent", "empty", "short-by-one"])
def test_b1_a_census_that_does_not_account_for_every_blank_window_leaves_the_forbidden_closed_set_and_cap_checks_not_evaluated(make):
    """§N.8 audit question: with 135 blank windows and no (or a partial) reason census nothing was measured, so "no forbidden reason / inside the closed set / cap not
    breached" must read NOT_EVALUATED — never PASS, and never an ALL_GATES_PASS verdict."""
    r, b, p = fx.a10_good()
    assert r["totals"]["blank"] == 135
    v = ev(make(r), b, p)
    absent = claims(v, "G-2", "is blank under") + claims(v, "G-2", "inside the closed allowed set") + claims(v, "G-3", "no forbidden reason", "outside the closed allowed set", "≤")
    assert absent and all(c["status"] == NOT_EVALUATED for c in absent), [(c["claim"], c["status"]) for c in absent]
    assert v["gates"]["G-2"]["status"] == NOT_EVALUATED and v["gates"]["G-3"]["status"] == NOT_EVALUATED
    assert v["overall"] == "NO_DISPATCH_NOT_EVALUATED"


def test_b1_a_complete_census_and_a_run_with_no_blank_window_still_pass():
    """The control: the census accounts for 135 of 135 → PASS; and with zero blank windows an empty census is a complete one."""
    r, b, p = fx.a10_good()
    assert ev(r, b, p)["gates"]["G-2"]["status"] == PASS and ev(r, b, p)["gates"]["G-3"]["status"] == PASS
    z = copy.deepcopy(r)
    z["totals"]["blank"] = 0
    z["totals"]["blank_reasons"], z["reason_windows_any"] = {}, {}
    assert gates.census_gap(z) is None


def test_b1_a_visible_forbidden_reason_still_refuses_when_the_census_is_otherwise_incomplete():
    """A reason that IS visible is a refusal whatever else is missing (T14): the gap must not soften a FAIL into NOT_EVALUATED."""
    r, b, p = fx.a10_good()
    x = _short_census(r)
    x["reason_windows_any"]["orb_not_ratified"] = 3
    v = ev(x, b, p)
    assert claims(v, "G-3", "no forbidden reason")[0]["status"] == FAIL and v["overall"] == "NO_DISPATCH"


# ── B2 (§N.8): two absent digests are not equal ─────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_b2_noninterference_kinds_without_sha256_and_count_on_both_sides_are_not_evaluated_not_equal():
    """None == None was PASS for all four kinds.  A kind with no digest or count on either side compared nothing."""
    r, b, p = fx.a10_good()
    r2, b2 = copy.deepcopy(r), copy.deepcopy(b)
    for x in (r2, b2):
        x["noninterference"]["kinds"] = {k: {} for k in gates.NONINTERFERENCE_KINDS}
    got = [c for c in gates.g7_noninterference_checks(r2, b2, T) if "natural keys equal" in c["claim"]]
    assert len(got) == 4 and all(c["status"] == NOT_EVALUATED for c in got), [(c["claim"], c["status"]) for c in got]
    assert ev(r2, b2, p)["gates"]["G-7"]["status"] == NOT_EVALUATED


def test_b2_one_missing_side_is_not_evaluated_and_the_control_passes():
    r, b, p = fx.a10_good()
    assert all(c["status"] == PASS for c in gates.g7_noninterference_checks(r, b, T) if "natural keys equal" in c["claim"])
    r2 = copy.deepcopy(r)
    del r2["noninterference"]["kinds"]["windows"]["count"]
    one = [c for c in gates.g7_noninterference_checks(r2, b, T) if c["claim"].startswith("windows: natural keys")][0]
    assert one["status"] == NOT_EVALUATED


# ── B3 (claim 7: the v2 fixes kept) ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────

class _Fake(types.ModuleType):
    pass


def _verify_world(monkeypatch, seen):
    """Stub the sidecar modules `verify_stage` imports; `vj.run` records which class census is installed when the verification job runs."""
    class Refused(Exception):
        def __init__(self, code, detail=""):
            self.code, self.detail = code, detail

    real_census = lambda *a, **k: (_ for _ in ()).throw(Refused("class_census_mismatch", "production census"))        # noqa: E731
    vj = _Fake("services.gochara_kernel.verification_job")
    vj._enforce_class_census, vj.VerificationRefused = real_census, Refused
    vj.class_census_violations = lambda pins, claimed: []
    vj._claimed_classes = lambda conn, chart, gen, found: []

    def run(conn, **kw):
        seen["installed"] = vj._enforce_class_census
        return {"classes": {c: {"status": "VERIFIED"} for c in kw["classes"]}, "status": "OK", "gate": []}
    vj.run = run
    vjob = _Fake("pipeline.orchestrator.verification_job")
    vjob._build_kwargs = lambda conn, ephe: {}
    reg = _Fake("services.gochara_kernel.rule_registry")
    import contextlib
    reg.rule_profile = lambda final_rules=True: contextlib.nullcontext()
    wv = _Fake("services.gochara_kernel.window_verifier")
    wv.verify_window_semantics = lambda *a, **k: None
    nwg = _Fake("services.gochara_kernel.numerical_window_gate")
    nwg.generation_verdict = lambda conn, chart, gen, classes=None: {"status": "PASSED", "numbered_windows": 1}        # the real signature: numerical_window_gate.py:151
    pkg = {"pipeline": _Fake("pipeline"), "services": _Fake("services"), "services.gochara_kernel": _Fake("services.gochara_kernel"),
           "pipeline.orchestrator": _Fake("pipeline.orchestrator")}
    pkg["pipeline.orchestrator"].verification_job = vjob
    pkg["services.gochara_kernel"].__dict__.update(verification_job=vj, rule_registry=reg, window_verifier=wv, numerical_window_gate=nwg)
    for k, m in {**pkg, "pipeline.orchestrator.verification_job": vjob, "services.gochara_kernel.verification_job": vj, "services.gochara_kernel.rule_registry": reg,
                 "services.gochara_kernel.window_verifier": wv, "services.gochara_kernel.numerical_window_gate": nwg}.items():
        monkeypatch.setitem(sys.modules, k, m)
    monkeypatch.setattr(ts, "make_clock", lambda state: te.StageClock(lambda: False, interval_s=0.5))

    class Cur:
        def __init__(self, row):
            self.row = row

        def fetchone(self):
            return self.row

        def fetchall(self):
            return []                                                   # no demoted windows in this fake

    class Conn:
        def execute(self, sql, args=()):
            return Cur((1, 1, 0) if sql == ts.VERIFY_ATTESTED_SQL else (1, 1) if sql == ts.LIVE_COUNT_SQL else (0,))
    return vj, real_census, Conn()


def test_b3_a_verify_stage_judges_the_slice_against_the_trial_census_and_restores_the_real_one(monkeypatch, tmp_path):
    """v2 fix (CENSUS_DIAG §3): during the verification job the class census is the TRIAL universe's (`make_trial_census`), not production's (which refuses a slice);
    afterwards the real one is back."""
    seen = {}
    vj, real_census, conn = _verify_world(monkeypatch, seen)
    state = {"classes": ["bereavement", "major_loss"], "verification": {"classes": {}, "ran": False}}
    assert ts.verify_stage(state, tmp_path, conn, None) is True
    assert seen["installed"] is not real_census
    seen["installed"](None, chart_id="x", generation="g", vector={"scored_classes": [f"c{i}" for i in range(26)] + ["bereavement", "major_loss"]}, found=())     # a trial claim inside the pin
    with pytest.raises(vj.VerificationRefused):
        seen["installed"](None, chart_id="x", generation="g", vector={"scored_classes": ["bereavement"]}, found=())                                  # a trial class outside the pin
    assert vj._enforce_class_census is real_census
    assert state["verification"]["ran"] is True


def test_the_recount_records_the_attested_demoted_ids_and_which_of_them_the_live_table_holds_as_numbered():
    """R-6: G-4 matches the attested numbered count against the live one by window_id, so the harness must capture the ids (numerical_window_gate.demotions)."""
    asked = []

    class Cur:
        def __init__(self, rows):
            self.rows = rows

        def fetchone(self):
            return self.rows[0]

        def fetchall(self):
            return self.rows

    class Conn:
        def execute(self, sql, args=()):
            asked.append((sql, args))
            return Cur({ts.VERIFY_ATTESTED_SQL: [(4509, 4491, 0)], ts.LIVE_COUNT_SQL: [(4509, 4492)], ts.VERIFY_DEMOTED_SQL: [("w1", "tie_ambiguous")],
                        ts.LIVE_NUMBERED_AMONG_SQL: [("w1",)]}[sql])
    rec = ts.collect_attestation_recount(Conn(), "c", "g", ["k"])
    assert rec["attested"] == {"windows": 4509, "numbered": 4491, "demoted_windows": [{"window_id": "w1", "reason": "tie_ambiguous"}]}
    assert rec["live"] == {"windows": 4509, "numbered": 4492, "numbered_among_demoted": ["w1"]}
    assert asked[-1][1][-1] == ["w1"]
    import gates
    assert gates.recount_agrees(rec["attested"], rec["live"])[0] is True


def _run_script(tmp_path, env_extra, unset=()):
    stub = tmp_path / "py"
    stub.write_text('#!/bin/sh\nprintf "%s" "${GOCHARA_RUNNER_COMMIT-UNSET}"\n')
    stub.chmod(0o755)
    env = {k: v for k, v in os.environ.items() if not k.startswith(("TRIAL_", "GOCHARA_")) and k not in unset}
    env.update({"TRIAL_PYTHON": str(stub), **env_extra})
    return subprocess.run(["bash", str(HARNESS / "run_trial.sh"), str(tmp_path), str(tmp_path / "out")], env=env, capture_output=True, text=True, timeout=30).stdout


def test_b3_run_trial_names_a_git_archive_export_by_the_trial_code_head_and_never_overrides_an_explicit_name(tmp_path):
    """v2 fix: the verification job names its runner by GOCHARA_RUNNER_COMMIT (window_gate.runner_identity); a `git archive` export has no HEAD, so run_trial.sh exports
    it from TRIAL_CODE_HEAD — only when TRIAL_CODE_HEAD is set and the variable is not already set."""
    head = "ab" * 20
    assert _run_script(tmp_path, {"TRIAL_CODE_HEAD": head}) == head
    assert _run_script(tmp_path, {"TRIAL_CODE_HEAD": head, "GOCHARA_RUNNER_COMMIT": "explicit"}) == "explicit"
    assert _run_script(tmp_path, {}) == "UNSET"


def _rolling_program(run_dir):
    import re
    src = (HERE / "vendor" / "rolling_trial.sh").read_text()
    m = re.search(r'python3 -c "(.*?)" 2>&1\)', src, re.S)
    assert m, "rolling_trial.sh no longer has its report-reading program"
    return m.group(1).replace("$run", str(run_dir))


def test_b3_the_report_carries_the_keys_the_rolling_trial_reads(monkeypatch, tmp_path):
    """The cockpit's rolling trial (fast/rolling_trial.sh, a vendored COPY) pages on `gate.status`, `totals.windows_total`/`blank`, the integer sum of `anomalies` and
    `verification.ran`.  Each is produced here by the harness's own code (analyse, run_gate, verify_stage) and read by the script's own program: a renamed key would
    page every run as NO_REPORT or NOT_RUN."""
    import json

    import test_analyse as ta
    rep = ta.run()
    rep["anomalies"]["number_without_score"] = 2
    monkeypatch.setattr(ts, "discover_gate", lambda sidecar, explicit: ("fakegatemod:gate", ""))
    gm = _Fake("fakegatemod")
    gm.gate = lambda conn, chart_id=None, generation=None: True
    monkeypatch.setitem(sys.modules, "fakegatemod", gm)
    rep["gate"] = ts.run_gate(None, tmp_path, None)
    seen = {}
    _, _, conn = _verify_world(monkeypatch, seen)
    state = {"classes": ["bereavement"]}
    ts.verify_stage(state, tmp_path, conn, None)
    rep["verification"] = state["verification"]
    (tmp_path / "out").mkdir()

    def page():
        (tmp_path / "out" / "trial_report.json").write_text(json.dumps(rep))
        return subprocess.run([sys.executable, "-I", "-c", _rolling_program(tmp_path)], capture_output=True, text=True, timeout=30).stdout.strip()
    t = rep["totals"]
    assert page() == f"PASSED numbered {t['windows_total'] - t['blank']} of {t['windows_total']} defects 2 verify ran", page()
    assert t["windows_total"] == 35 and t["blank"] == 23
    # a verification job that refused reads NOT_RUN with its reason (the other branch of the same key)
    vj = sys.modules["services.gochara_kernel.verification_job"]
    vj.run = lambda conn, **kw: (_ for _ in ()).throw(vj.VerificationRefused("class_census_mismatch", "refused"))
    refused = {"classes": ["bereavement"]}
    ts.verify_stage(refused, tmp_path, conn, None)
    rep["verification"] = refused["verification"]
    assert page().endswith("verify NOT_RUN VerificationRefused class_census_mismatch: refused"), page()


# ── N2: the ephemeris digest is the pinned FILES + the library VERSION; the platform is provenance ─────────────────────────────────────────────────────

def _eph(**over):
    e = {"backend": "swiss", "swe_version": "2.10", "library_sha256": "s" * 64, "platform": "linux/amd64", "files": {"sepl_18.se1": "f" * 64, "semo_18.se1": "e" * 64},
         "probe_digest": "p" * 64}
    e.update(over)
    return e


def test_n2_the_same_ephemeris_files_on_two_platforms_digest_equal_and_one_changed_file_differs():
    arm = fx.digests(ephemeris=_eph(platform="darwin/arm64", library_sha256="a" * 64, probe_digest="q" * 64))
    amd = fx.digests(ephemeris=_eph())
    assert arm["components"]["ephemeris"] == amd["components"]["ephemeris"]
    assert arm["provenance"]["ephemeris"]["platform"] == "darwin/arm64" and amd["provenance"]["ephemeris"]["platform"] == "linux/amd64"      # recorded, beside the digests
    v = gates.g8_digest_checks({"digests_record": arm}, amd)
    assert v[0]["status"] == PASS
    changed = fx.digests(ephemeris=_eph(files={"sepl_18.se1": "0" * 64, "semo_18.se1": "e" * 64}))
    assert changed["components"]["ephemeris"] != amd["components"]["ephemeris"]
    assert gates.g8_digest_checks({"digests_record": changed}, amd)[0]["status"] == FAIL
    assert fx.digests(ephemeris=_eph(swe_version="2.11"))["components"]["ephemeris"] != amd["components"]["ephemeris"]


def test_n2_an_ephemeris_without_files_or_version_gives_no_record():
    assert fx.digests(ephemeris=_eph(files={})) is None and fx.digests(ephemeris=_eph(swe_version=None)) is None


# ── N3: an unanswered probe sample is unknown, not "no one waits" ──────────────────────────────────────────────────────────────────────────────────────

def test_n3_any_unanswered_probe_sample_makes_the_stage_lock_wait_unknown_and_reports_what_was_seen():
    c = te.StageClock(lambda: False, interval_s=0.25)
    c.add("build:record", 10.0, 4, 40, unanswered=1)
    s = c.record()["stages"]["build:record"]
    assert s["lock_wait_s"] is None and s["compute_s"] is None and s["unanswered_samples"] == 1 and s["lock_wait_observed_s"] == 1.0
    c2 = te.StageClock(lambda: False)
    c2.load({"stages": {"build:record": s}})
    again = c2.record()["stages"]["build:record"]
    assert again["lock_wait_s"] is None and again["unanswered_samples"] >= 1 and again["lock_wait_observed_s"] == 1.0
    ok = te.StageClock(lambda: False, interval_s=0.25)
    ok.add("build:record", 10.0, 4, 40, unanswered=0)
    assert ok.record()["stages"]["build:record"]["lock_wait_s"] == 1.0


# ── N4: the probe's admin connection is closed ───────────────────────────────────────────────────────────────────────────────────────────────────────

def test_n4_closing_the_clock_closes_the_lock_probes_admin_connection_and_a_broken_one_is_dropped(monkeypatch):
    opened = []

    class Conn:
        def __init__(self, broken=False):
            self.closed, self.broken = False, broken
            opened.append(self)

        def execute(self, sql, params=()):
            if self.broken:
                raise RuntimeError("gone")
            return types.SimpleNamespace(fetchone=lambda: (0,))

        def close(self):
            self.closed = True
    fake = types.ModuleType("psycopg")
    fake.connect = lambda *a, **k: Conn(broken=len(opened) == 0)
    monkeypatch.setitem(sys.modules, "psycopg", fake)
    probe = te.lock_probe("dsn", "db")
    assert probe() is None and opened[0].closed                      # the broken connection is closed, not leaked
    assert probe() is False and not opened[1].closed
    te.StageClock(probe).close()
    assert opened[1].closed
