"""SR-TR26-G7-RESUME (b)+(d) — the TR-26 kill+resume leg is a STAGED CENTURY run, so the resume reaches the writer's committed-substep ledger.

Finding (review of #3918, NB-1/C9): `run --writer-resume` drove `build_slice(build_id="trial-slice")`: no build_runs row, no staged `gochara_v5_century_config`, so the writer's `_ledger_active` was False, no ledger row was
ever written and the resume re-planned the whole plan; G-7's "nothing re-ran" check would have read FALSE.  The harness now stages the run the way the dispatch does (`completion.stage_century_run`) and hands the writer
nothing but its run id (+, on the resume leg, the explicit `gochara_v5_century_resume` binding the executor would stage); the WRITER decides what to skip.

One oracle per distinct claim; the single planted reversion is named in each docstring.  The claims that need the real writer on a real database (byte-identity resumed vs fresh, the ledger holding exactly the committed
substeps, the program-digest refusal) are the LIVE test at the bottom (opt-in KY_G7_CENTURY_LIVE=1, the local lane cluster and the approved canonical-L1 export); the rest are pure."""
import json
import os
import subprocess
import sys
import types
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

import completion as cp
import test_harness_33 as h33
import test_tr26_resume as t26
import trial_slice as ts

HARNESS = Path(__file__).resolve().parents[1]
A, B = t26.A, t26.B
PLAN = t26.PLAN
RULED = ["1998-01-01T00:00:00+00:00", "2084-02-05T00:00:00+00:00"]
D64 = {k: c * 64 for k, c in (("impl", "1"), ("writer", "2"), ("plan", "3"))}
UTC = timezone.utc
HORIZON = (datetime(1998, 1, 1, tzinfo=UTC), datetime(2084, 2, 5, tzinfo=UTC))


def entry(key, ordinal, **over):
    base = dict(substep_key=key, ordinal=ordinal, manifest_id=None, vector_sha256=None, implementation_digest=D64["impl"], writer_digest=D64["writer"], plan_digest=D64["plan"],
                horizon=HORIZON, build_run_id="killed-run", execution_id=None, rows_written=0, scope=None, scope_digest=None)
    base.update(over)
    return types.SimpleNamespace(**base)


def writer_ledger():
    """The checkout writer's own ledger module, when the sidecar is importable (it judges the binding the harness stages)."""
    pytest.importorskip("psycopg")
    return pytest.importorskip("services.gochara_kernel.build_ledger")


# ── the manifest the harness stages is the one the writer accepts ───────────────────────────────────────────────────────────────────

def test_the_staged_manifest_is_an_unmarked_century_config_the_writer_validates_and_carries_the_binding_only_on_a_resume():
    """The writer's `validate_century_config` accepts exactly this config (final rules, deferred in-build verify, the ruled horizon, the policy) and there is NO test-slice marker (a marked run takes no century
    config and gets no ledger).  Reversion: add a `gochara_v5_test_slice` marker, or drop the config → this fails (and the writer would refuse / never record)."""
    wr = pytest.importorskip("pipeline.orchestrator.writers.ka_gochara_v5")
    m = cp.century_manifest(RULED, "window_qualification/1")
    staged = wr.validate_century_config(m[wr.CENTURY_CONFIG_KEY])
    assert staged["final_rules"] is True and staged["defer_in_build_verify"] is True and staged["result_policy"] == "window_qualification/1"
    assert wr.TEST_SLICE_KEY not in m and cp.RESUME_BINDING_KEY not in m and wr.CENTURY_CONFIG_KEY == "gochara_v5_century_config" and cp.RESUME_BINDING_KEY == wr.RESUME_BINDING_KEY


def test_the_resume_binding_names_the_killed_run_the_ledgers_program_and_its_substeps_in_plan_order_and_the_writer_accepts_it():
    """The explicit binding (SR-RESUME-EXPLICIT-BINDING) is built from the ledger read back: the run being resumed, the identity every row carries, the ordered keys.  The writer's own validator parses it.
    Reversion: list the keys in arrival (not ordinal) order → the ordered-keys assertion fails; hard-code another identity → the program assertion fails."""
    bl = writer_ledger()
    rows = [entry("convention", 1), entry("rules", 0), entry("body:Sun", 2)]               # read back out of order on purpose
    b = cp.resume_binding(rows, "5f1c7b3e-0000-4000-8000-000000000001")
    parsed = bl.validate_resume_binding(b)
    assert list(parsed.ledger_substeps) == ["rules", "convention", "body:Sun"] and parsed.resumes_run_id == "5f1c7b3e-0000-4000-8000-000000000001"
    assert (parsed.implementation_digest, parsed.writer_digest, parsed.plan_digest) == (D64["impl"], D64["writer"], D64["plan"]) and parsed.horizon == HORIZON


def test_an_empty_ledger_has_nothing_to_resume_and_is_refused_by_name_never_staged_empty():
    """Reversion: build the binding from [] (the writer's validator would then refuse `resume_binding_malformed` at the resume, after a run was already staged)."""
    with pytest.raises(ValueError, match="no ledger rows"):
        cp.resume_binding([], "5f1c7b3e-0000-4000-8000-000000000001")


# ── the harness stages the run; the writer decides what to skip ────────────────────────────────────────────────────────────────────

class Recorder:
    """What `stage_century` asked the staging helpers for (the database is not the claim here)."""

    def __init__(self, monkeypatch, ledger=()):
        self.calls = []
        monkeypatch.setattr(cp, "ensure_build_runs", lambda conn, text: self.calls.append(("ensure", None)))
        fake = types.ModuleType("services.gochara_kernel.build_ledger")
        fake.load = lambda conn, chart, generation: list(ledger)
        monkeypatch.setitem(sys.modules, "services", types.ModuleType("services"))
        monkeypatch.setitem(sys.modules, "services.gochara_kernel", types.ModuleType("services.gochara_kernel"))
        sys.modules["services.gochara_kernel"].build_ledger = fake
        monkeypatch.setitem(sys.modules, "services.gochara_kernel.build_ledger", fake)
        n = iter(range(1, 99))

        def stage(conn, **kw):
            rid = f"run-{next(n)}"
            self.calls.append(("stage", rid, kw))
            return rid
        monkeypatch.setattr(cp, "stage_century_run", stage)


@pytest.fixture
def schema_file(tmp_path, monkeypatch):
    (tmp_path / "schema.sql").write_text("-- schema")
    monkeypatch.setattr(ts, "EXPORT", tmp_path)


def test_the_kill_leg_stages_one_unbound_run_a_budget_restart_reuses_it_and_the_resume_leg_binds_a_second_one_to_the_ledger_it_read(monkeypatch, schema_file):
    """Kill leg: one century-staged row, no binding.  A restart of the SAME leg (wall budget) stages nothing new.  Resume leg: a second row that RESUMES the killed run with the ledger read back now.
    Reversion: stage the resume leg without `resumes` (a fresh dispatch over a ledger → the writer's `fresh_run_found_ledger`) or stage a new row on every restart (two active runs)."""
    led = [entry("rules", 0), entry("convention", 1)]
    rec = Recorder(monkeypatch, led)
    state: dict = {}
    first = ts.stage_century(object(), state, writer_resume=False, horizon=HORIZON, policy="window_qualification/1")
    assert ts.stage_century(object(), state, writer_resume=False, horizon=HORIZON, policy="window_qualification/1") == first
    staged = [c for c in rec.calls if c[0] == "stage"]
    assert len(staged) == 1 and "resumes" not in staged[0][2] and staged[0][2]["result_policy"] == "window_qualification/1" and staged[0][2]["ruled_horizon"] == [h.isoformat() for h in HORIZON]
    second = ts.stage_century(object(), state, writer_resume=True, horizon=HORIZON, policy="window_qualification/1")
    assert second != first and ts.stage_century(object(), state, writer_resume=True, horizon=HORIZON, policy="window_qualification/1") == second
    staged = [c for c in rec.calls if c[0] == "stage"]
    assert len(staged) == 2 and staged[1][2]["resumes"] == first and [e.substep_key for e in staged[1][2]["entries"]] == ["rules", "convention"]
    assert state["century"]["ledger_substeps_at_resume"] == ["rules", "convention"]


def test_a_resume_over_a_killed_run_that_ledgered_nothing_and_a_state_with_no_staged_run_both_refuse_by_name(monkeypatch, schema_file, capsys):
    """The ledger-less kill proves nothing about the writer's resume.  Reversion: fall through to a plain (unbound) stage → no refusal."""
    Recorder(monkeypatch, [])
    with pytest.raises(ts.Refused):
        ts.stage_century(object(), {"century": {"run_id": "run-1"}}, writer_resume=True, horizon=HORIZON, policy=None)
    assert "no ledger rows" in capsys.readouterr().err
    with pytest.raises(ts.Refused):
        ts.stage_century(object(), {}, writer_resume=True, horizon=HORIZON, policy=None)
    assert "recorded no staged run" in capsys.readouterr().err


# ── build(): the writer's plan is asked once per leg and the harness skips nothing on a resume ──────────────────────────────────────

def century_leg(monkeypatch, tmp_path, *, century, ledger=True):
    """Kill a fresh build then resume it with the ledger-aware stand-in writer (test_tr26_resume.ledger_aware); returns (state, build_ids handed to build_slice, plan calls per leg)."""
    committed: set = set()
    ids, plans = [], []
    tmp_path.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(ts, "stage_century", lambda conn, state, *, writer_resume, horizon, policy: ("RESUME-RUN" if writer_resume else "KILL-RUN"))
    state = {"classes": [A, B], "requested_policy": "default", "steps": [], "defects": [], "db": "ky_trial_x", "collect": False, "century_staged": century}

    def world(resume):
        w = h33.World(monkeypatch, PLAN, (), 0.0, state)
        if ledger:
            t26.ledger_aware(w, committed)
        mod = sys.modules["pipeline.orchestrator.writers.ka_gochara_v5"]
        base = mod.GocharaV5Writer
        calls = [0]

        class Counting(base):
            def plan_substeps(self, ctx):
                calls[0] += 1
                return base.plan_substeps(self, ctx)
        mod.GocharaV5Writer = Counting
        q = sys.modules["scripts.kala_gochara_cutover.j4d_slice_qualify"]
        inner = q.build_slice
        q.build_slice = lambda conn, **kw: (ids.append(kw["build_id"]), inner(conn, **kw))[1]
        plans.append(calls)
    world(False)
    assert ts.build(state, tmp_path, None, abort_after="auto") is False
    world(True)
    state["writer_resumed"] = True
    assert ts.build(state, tmp_path, None, writer_resume=True) is True
    return state, ids, [c[0] for c in plans]


def test_the_century_legs_hand_the_writer_their_staged_run_ids_and_a_slice_run_still_runs_as_trial_slice(monkeypatch, tmp_path):
    """The kill leg runs under the staged kill run, the resume leg under the staged resume run; without the century flag the harness still says `trial-slice` (the slice/main TR path is unchanged).
    Reversion: pass build_id="trial-slice" always (the finding's defect) → the first assertion fails."""
    _s, ids, _p = century_leg(monkeypatch, tmp_path, century=True)
    assert set(ids[:9]) == {"KILL-RUN"} and set(ids[9:]) == {"RESUME-RUN"}
    _s, ids, _p = century_leg(monkeypatch, tmp_path / "plain", century=False)
    assert set(ids) == {"trial-slice"}


def test_a_century_leg_asks_the_writer_for_its_plan_once_plus_one_confirmation_not_once_per_substep(monkeypatch, tmp_path):
    """A ledger-aware plan re-proves the whole committed chain (verify_chain over every recorded scope), so asking it before EVERY substep is quadratic over a 300-substep century; the orchestrator asks once
    (and again after the last substep to confirm nothing remains) and so does the harness.  Reversion: drop the `planned` cache in build() → the plan is asked once per substep."""
    _s, _ids, plans = century_leg(monkeypatch, tmp_path, century=True)
    assert plans[0] <= 2 and plans[1] <= 2                                         # kill leg: 1 (+1 if it ran to the end); resume leg: 1 + the confirmation


def test_the_resume_executes_only_what_the_writers_ledger_left_and_the_harness_skips_nothing(monkeypatch, tmp_path):
    """before-kill ∪ after-resume == the plan with nothing in both, on the century path, with the harness's own `done` NOT consulted for the resume's start (the writer's plan is).
    Reversion: seed `done` from state["steps"] on a writer_resume → the log would still be disjoint but the harness, not the writer, would be what skipped; assert via the ledger-less writer: it re-runs."""
    state, _ids, _p = century_leg(monkeypatch, tmp_path, century=True)
    rl = ts.resume_leg_section(state)
    assert rl["executed_before_abort"] == PLAN[:9] and rl["executed_after_resume"] == PLAN[9:] and rl["rerun_after_resume"] == [] and rl["century_staged"] is True
    state2, _ids2, _p2 = century_leg(monkeypatch, tmp_path / "noledger", century=True, ledger=False)
    rl2 = ts.resume_leg_section(state2)
    assert rl2["rerun_after_resume"] == sorted(PLAN[:9])                          # a writer with no ledger re-runs all of it: the detector can read false


# ── cmd_run decides the staging ────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_the_kill_and_resume_flags_imply_century_staging_and_a_plain_run_does_not():
    """The kit's s5b needs no change: TRIAL_ABORT_AFTER_SUBSTEP / TRIAL_WRITER_RESUME already select the legs.  Reversion: decide staging from a new flag only → the kit's kill leg would stay unstaged."""
    src = (HARNESS / "trial_slice.py").read_text()
    assert "if abort_after is not None or writer_resume or century_requested(a):" in src
    ns = types.SimpleNamespace
    assert ts.century_requested(ns(century_staged=True)) is True and ts.century_requested(ns(century_staged=False)) is False


# ── LIVE: the real writer, a real database, the approved canonical-L1 export ──────────────────────────────────────────────────────────

live = pytest.mark.skipif(os.environ.get("KY_G7_CENTURY_LIVE") != "1",
                          reason="live kill+resume through the century-staged path: set KY_G7_CENTURY_LIVE=1 (minutes; the local lane cluster + the approved canonical-L1 export)")
LIVE_CLASSES = os.environ.get("KY_G7_CENTURY_CLASSES", "achievement_recognition,bereavement")      # the two LEADING classes of the writer's plan (alphabetical): the ledger must be a prefix of the full plan, and the kill needs a committed class behind it


def run_leg(out, label, env, *args):
    e = {**os.environ, "TRIAL_CLASSES": LIVE_CLASSES, "TRIAL_POLICY": os.environ.get("KY_G7_CENTURY_POLICY", "window_qualification/1"), "TRIAL_LABEL": label, "TRIAL_CODE_HEAD": "0" * 40, **env}
    return subprocess.run(["bash", str(HARNESS / "run_trial.sh"), os.environ["KY_TEST_CHECKOUT"], str(out)], env=e, capture_output=True, text=True, timeout=3 * 3600)


def ledger_keys(db):
    import psycopg
    with psycopg.connect(f"postgresql://postgres@127.0.0.1:55433/{db}", autocommit=True) as c:
        return [r[0] for r in c.execute("SELECT substep_key FROM public.ka_gochara_build_ledger WHERE chart_id = %s::uuid AND generation = %s ORDER BY ordinal", (ts.CHART, ts.GENERATION))]


@live
def test_live_the_resumed_generation_is_byte_identical_to_a_fresh_century_run_and_the_ledger_not_the_harness_skipped(tmp_path):
    """The ruling's three oracles on the real writer.  (a) the resumed generation's window rows are byte-identical PER CLASS to a fresh uninterrupted century-staged run; (b) after the kill the ledger holds exactly the
    substeps the harness saw committed, and the resume ran ONLY the rest; (c) a perturbed program digest refuses by name before any substep.
    Reversion for (a)/(b): resume through the old non-century path (the control test below) → the writer is not handed a ledger: re-ran > 0."""
    fresh = tmp_path / "fresh"
    r = run_leg(fresh, "g7c-fresh", {"TRIAL_CENTURY_STAGED": "1"})
    fs = json.loads((fresh / "state.json").read_text())
    assert "window_rows_digest" in fs, r.stdout[-800:] + r.stderr[-800:]
    leg = tmp_path / "leg"
    r = run_leg(leg, "g7c-kill", {"TRIAL_KEEP_DB": "1", "TRIAL_ABORT_AFTER_SUBSTEP": "auto"})
    assert r.returncode == ts.EX_KILLED, r.stdout[-800:] + r.stderr[-800:]
    ks = json.loads((leg / "state.json").read_text())
    killed = [e["step"] for e in ks["executed_log"] if e["phase"] == "initial"]
    assert ledger_keys(ks["db"]) == killed and killed                              # (b) the ledger is exactly what committed
    p = subprocess.run([sys.executable, "-I", "-X", "utf8", str(HARNESS / "trial_slice.py"), "resume-probe", "--out", str(leg)], capture_output=True, text=True, timeout=1800)
    ps = json.loads((leg / "state.json").read_text())["refusal_probe"]
    assert p.returncode == 0 and ps["refused"] is True and ps["executed_substeps"] == 0 and ps["refusal_name"] == "ResumeRefused" and "digest" in (ps["message"] or "")      # (c)
    r = run_leg(leg, "g7c-resume", {"TRIAL_KEEP_DB": "0", "TRIAL_WRITER_RESUME": "1"})
    rs = json.loads((leg / "state.json").read_text())
    rl = ts.resume_leg_section(rs)
    assert rl["rerun_after_resume"] == [] and rl["executed_before_abort"] == killed and rl["executed_after_resume"], r.stdout[-800:] + r.stderr[-800:]       # (b)
    assert rs["window_rows_digest"]["per_class"] == fs["window_rows_digest"]["per_class"] and rs["window_rows_digest"]["sha256"] == fs["window_rows_digest"]["sha256"]        # (a)
    assert rs["window_rows_digest"]["memberships_sha256"] == fs["window_rows_digest"]["memberships_sha256"]


@live
def test_live_control_resuming_through_the_old_non_century_path_never_reaches_the_ledger_and_re_runs_what_committed(tmp_path):
    """The planted reversion for (b), run for real: the same killed database, but the resume goes through the OLD path (century staging dropped from the state).  The writer then plans the whole plan
    (it is not handed a century run), the harness skips nothing, and the log shows the committed substeps running AGAIN — the detector reads false.  Reversion of this control: none needed (it is one)."""
    leg = tmp_path / "leg"
    r = run_leg(leg, "g7c-ctl-kill", {"TRIAL_KEEP_DB": "1", "TRIAL_ABORT_AFTER_SUBSTEP": "auto"})
    assert r.returncode == ts.EX_KILLED, r.stdout[-800:] + r.stderr[-800:]
    st = json.loads((leg / "state.json").read_text())
    killed = [e["step"] for e in st["executed_log"] if e["phase"] == "initial"]
    st["century_staged"] = False                                                   # the revert: drop the century staging ...
    st["century"] = {}
    import psycopg
    with psycopg.connect(f"postgresql://postgres@127.0.0.1:55433/{st['db']}", autocommit=True) as c:
        c.execute("DROP TABLE public.build_runs")                                  # ... and with it the staged run: the pre-fix database had no build_runs (build_id 'trial-slice' is not a uuid)
    (leg / "state.json").write_text(json.dumps(st))
    # `run --writer-resume` can no longer reach the old path (it stages the century run itself), so the reverted harness is driven in a child process: build(writer_resume=True) with the staging dropped
    code = ("import json, sys; from pathlib import Path; sys.path.insert(0, sys.argv[1]); import trial_slice as ts; leg = Path(sys.argv[2]); st = json.loads((leg / 'state.json').read_text()); "
            "ts.bind_checkout(Path(st['code']['checkout'])); st['writer_resumed'] = True; ts.build(st, leg, None, writer_resume=True); ts.write_json(leg / 'state.json', st)")
    try:
        r = subprocess.run([sys.executable, "-I", "-X", "utf8", "-c", code, str(HARNESS), str(leg)], capture_output=True, text=True, timeout=3 * 3600)
    finally:
        with psycopg.connect(ts.ADMIN_DSN, autocommit=True) as admin:
            admin.execute(f'DROP DATABASE IF EXISTS "{st["db"]}" WITH (FORCE)')
    rl = ts.resume_leg_section(json.loads((leg / "state.json").read_text()))
    assert rl is not None and rl["century_staged"] is False and set(killed) <= set(rl["rerun_after_resume"]), r.stdout[-600:] + r.stderr[-600:]
