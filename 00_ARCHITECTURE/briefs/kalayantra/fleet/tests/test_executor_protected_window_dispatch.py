"""U-M-01 oracles: the executor kinds protected_window_dispatch and protected_window_dispatch_dryrun (fleet/protected_window_launch.py).

Sources of the rules: the U-M-01 contract (args exactly {flag, ref, head, window_lease_id}; lease-aware per SR-BOLD-02 / W2-M-08; remote-async like measuring_dispatch;
one ky.window_run/1 line; the GitHub protected-environment approval stays a person's act), the prime rule of the shared lease table (executor.lease_live, executor.py:270;
window_lease_gate), and deploy.yml's own declaration of its protected windows (protected_windows.catalog, SR-A6-GCW). No production, no network, no real `gh`: the
GitHub CLI is a recording fake and origin is a local bare repository carrying the lease table.

Claims, one oracle each (a single planted reversion of the named line fails it):
  P1  both kinds ship disabled; the dry-run sibling takes the live kind's args and identity; only the live kind is production + remote_async
  P2  args are exactly {flag, ref, head, window_lease_id}: a missing or extra arg is refused           (the four required parser args)
  P3  ref must be main                                                                                   (plan: `args.ref != "main"`)
  P4  head must be the live tip of main, locally and on the remote                                       (plan: the tip comparison)
  P5  flag must be a protected schema window of deploy.yml at the head                                   (plan: `args.flag not in window_flags`; the real catalog)
  P6  window_lease_id must be the request's own lease_id                                                 (plan: `own != args.window_lease_id`)
  P7  any OTHER ACTIVE lease, or an unreadable table, refuses before `gh workflow run`                   (lease_check / window_lease_gate.verdict)
  P8  the lease is read again immediately before the dispatch                                            (dispatch: the second lease_check)
  P9  the dispatch is exactly `gh workflow run deploy.yml --ref main -f ci_gate=... -f window_lease_id=... -f <flag>=true`
  P10 remote-async: one run view after identification, one ky.window_run/1 line, exit 0 while the run is queued
  P11 ky.window_run/1 fields: capability_step_started, latest_step_progress_at, completed_at, steps[]   (window_run_line)
  P12 a dispatch whose run cannot be identified is exit 1 with run_id null and is never repeated        (dispatch: the identify loop)
  P13 a failed `gh workflow run` is a refusal with no window_run line
  P14 the approval stays a person's: only the reads and the one workflow run reach gh                   (no approval call)
  P15 the dry run makes every check (P3/P4/P7 refuse the same way) and never dispatches
"""
import datetime as dt
import importlib.util
import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
FLEET = HERE.parent
REPO = FLEET.parents[3]
# the two overrides let a revert-proof run this suite against a modified COPY (job folder); unset in CI
LAUNCH_PY = Path(os.environ.get("KY_PWL_COPY") or FLEET / "protected_window_launch.py")
OPS_FILE = Path(os.environ.get("KY_PWL_OPS") or FLEET / "executor_ops.json")
COORD_REL = "00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md"
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))

REPO_LOCATING_VARS = ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE",
                      "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_NAMESPACE")
GIT_ENV = {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1", "GIT_TERMINAL_PROMPT": "0",
           "GIT_AUTHOR_NAME": "fixture", "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
           "GIT_COMMITTER_NAME": "fixture", "GIT_COMMITTER_EMAIL": "fixture@example.invalid"}
FLAG = "fixture_schema_migration"
LEASE = "U-W1W2"
CAPABILITY_STEP = "Apply exact protected public-schema migrations"


def _env():
    return {**{k: v for k, v in os.environ.items() if k not in REPO_LOCATING_VARS}, **GIT_ENV}


def _git(cwd, *args):
    p = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, env=_env())
    assert p.returncode == 0, f"git {args}: {p.stderr[-300:]}"
    return p.stdout.strip()


def _load():
    spec = importlib.util.spec_from_file_location("ky_protected_window_launch_under_test", LAUNCH_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


launch = _load()


def _expiry(hours):
    return (dt.datetime.now(IST) + dt.timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M")


def table(*rows):
    """A lease table in the real shape. A row is (lease_id, hours_to_expiry, state)."""
    body = "".join(f"| {lease} | camp | scope | start | {_expiry(hours)} | {state} |\n" for lease, hours, state in rows)
    return ("# fixture\n\n## 1. Leases\n\n| lease | campaign | scope | start | expires | state |\n|---|---|---|---|---|---|\n"
            + body + "\n## 2. Other\n\n| not | a | lease | row | x | ACTIVE |\n")


FAKE_GH = '''#!{python}
import json, os, sys
d = os.environ["FAKE_GH_DIR"]
a = sys.argv[1:]
open(os.path.join(d, "calls.jsonl"), "a").write(json.dumps(a) + "\\n")
def out(name):
    sys.stdout.write(open(os.path.join(d, name)).read())
if a[:1] == ["api"]:
    sys.stdout.write(json.dumps({{"object": {{"sha": open(os.path.join(d, "remote_head")).read().strip()}}}}))
elif a[:2] == ["workflow", "run"]:
    if os.path.exists(os.path.join(d, "fail_dispatch")): sys.exit(1)
    open(os.path.join(d, "dispatched"), "w").write("1")
elif a[:2] == ["run", "list"]:
    out("runs_after.json" if os.path.exists(os.path.join(d, "dispatched")) else "runs_before.json")
elif a[:2] == ["run", "view"]:
    out("view.json")
else:
    sys.exit(9)
'''


class World:
    """origin = a local bare repo carrying main and campaign-coordination; a recording fake `gh`; `self.head` is origin/main."""

    def __init__(self, tmp_path, lease_table, monkeypatch):
        self.origin, self.repo, self.gh_dir = tmp_path / "origin.git", tmp_path / "checkout", tmp_path / "gh"
        self.gh_dir.mkdir()
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(self.origin)], check=True, env=_env())
        subprocess.run(["git", "init", "-q", "-b", "main", str(self.repo)], check=True, env=_env())
        _git(self.repo, "remote", "add", "origin", str(self.origin))
        (self.repo / "README").write_text("x")
        _git(self.repo, "add", "-A"); _git(self.repo, "commit", "-q", "-m", "main"); _git(self.repo, "push", "-q", "origin", "main")
        self.head = _git(self.repo, "rev-parse", "HEAD")
        if lease_table is not None:
            _git(self.repo, "checkout", "-q", "-b", "campaign-coordination")
            (self.repo / COORD_REL).parent.mkdir(parents=True, exist_ok=True)
            (self.repo / COORD_REL).write_text(lease_table)
            _git(self.repo, "add", "-A"); _git(self.repo, "commit", "-q", "-m", "lease"); _git(self.repo, "push", "-q", "origin", "campaign-coordination")
            _git(self.repo, "checkout", "-q", "main")
        self.gh = self.gh_dir / "gh"
        self.gh.write_text(FAKE_GH.format(python=sys.executable)); self.gh.chmod(self.gh.stat().st_mode | stat.S_IEXEC)
        self.put("remote_head", self.head); self.put("runs_before.json", "[]")
        self.put("runs_after.json", json.dumps([{"databaseId": 777, "headSha": self.head, "event": "workflow_dispatch"}]))
        self.put("view.json", json.dumps(view("queued")))
        monkeypatch.setenv("FAKE_GH_DIR", str(self.gh_dir))
        monkeypatch.setenv("KY_OPERATION_REQUEST", json.dumps({"lease_id": LEASE}))
        monkeypatch.setattr(launch, "window_flags", lambda repo, head: {FLAG, "other_schema_migration"})
        monkeypatch.setattr(launch, "IDENTIFY_POLLS", 3)

    def put(self, name, text):
        (self.gh_dir / name).write_text(text)

    def calls(self):
        f = self.gh_dir / "calls.jsonl"
        return [json.loads(line) for line in f.read_text().splitlines()] if f.exists() else []

    def workflow_runs(self):
        return [c for c in self.calls() if c[:2] == ["workflow", "run"]]

    def go(self, capsys, dry_run=False, **over):
        args = {"flag": FLAG, "ref": "main", "head": self.head, "window_lease_id": LEASE, **over}
        argv = [x for k, v in args.items() for x in (f"--{k}", v)] + (["--dry-run"] if dry_run else [])   # the executor appends `--{key} {value}`
        rc = launch.main(argv, gh=str(self.gh), repo=str(self.repo), sleep=lambda s: None)
        out = capsys.readouterr()
        return rc, out.out, out.err


def view(status, steps=(), conclusion=None, job_completed=None):
    return {"databaseId": 777, "status": status, "conclusion": conclusion,
            "jobs": [{"name": "protected", "status": status, "completedAt": job_completed, "steps": list(steps)}]}


def step(name, status, started=None, completed=None, conclusion=None):
    return {"name": name, "status": status, "conclusion": conclusion, "startedAt": started, "completedAt": completed}


@pytest.fixture
def world(tmp_path, monkeypatch):
    return World(tmp_path, table((LEASE, 5, "ACTIVE")), monkeypatch)


# ───────────────────────────── P1 the table ─────────────────────────────

def test_p1_both_kinds_ship_disabled_and_the_dryrun_takes_the_live_kinds_args():
    ops = json.loads(OPS_FILE.read_text())["ops"]
    live, dry = ops["protected_window_dispatch"], ops["protected_window_dispatch_dryrun"]
    assert live["enabled"] is False and dry["enabled"] is False
    assert live["allowed_args"] == dry["allowed_args"] == ["flag", "ref", "head", "window_lease_id"]   # the mechanical route compares args between a kind and its dry run
    assert live["production"] is True and live["remote_async"] is True       # leased, fenced, returns after dispatch like measuring_dispatch
    assert dry["production"] is False and "remote_async" not in dry and dry["fixed_args"] == ["--dry-run"]
    assert live["script"] == dry["script"] == "00_ARCHITECTURE/briefs/kalayantra/fleet/protected_window_launch.py" and (REPO / live["script"]).is_file()


# ───────────────────────────── P2 args exactly ─────────────────────────────

@pytest.mark.parametrize("drop", ["flag", "ref", "head", "window_lease_id"])
def test_p2_a_missing_arg_is_refused(world, drop):
    args = {"flag": FLAG, "ref": "main", "head": world.head, "window_lease_id": LEASE}
    del args[drop]
    with pytest.raises(SystemExit) as exc:
        launch.main([x for k, v in args.items() for x in (f"--{k}", v)], gh=str(world.gh), repo=str(world.repo))
    assert exc.value.code == 2 and world.calls() == []


def test_p2_an_extra_arg_is_refused(world):
    with pytest.raises(SystemExit) as exc:
        launch.main(["--flag", FLAG, "--ref", "main", "--head", world.head, "--window_lease_id", LEASE, "--classes", "all"], gh=str(world.gh), repo=str(world.repo))
    assert exc.value.code == 2 and world.calls() == []


# ───────────────────── P3/P4/P7 refusals, live and dry-run alike (P15) ─────────────────────

@pytest.mark.parametrize("dry", [False, True])
def test_p3_a_ref_other_than_main_is_refused(world, capsys, dry):
    rc, out, err = world.go(capsys, dry_run=dry, ref="feature")
    assert rc == 1 and "ref must be main" in err and world.workflow_runs() == [] and out == ""


@pytest.mark.parametrize("dry", [False, True])
@pytest.mark.parametrize("stale", ["local", "remote"])
def test_p4_a_head_that_is_not_the_live_tip_of_main_is_refused(world, capsys, dry, stale):
    if stale == "local":
        rc, out, err = world.go(capsys, dry_run=dry, head="1" * 40)
    else:
        world.put("remote_head", "2" * 40)             # main moved on GitHub after this fetch
        rc, out, err = world.go(capsys, dry_run=dry)
    assert rc == 1 and "not the current tip of main" in err and world.workflow_runs() == []


def test_p5_the_flag_must_be_a_protected_window_of_the_real_deploy_workflow():
    pytest.importorskip("yaml")
    sys.path.insert(0, str(FLEET))
    import protected_windows as pw
    real = pw.catalog(pw.GitSource(REPO), "HEAD")                    # deploy.yml's own declaration, read from this tree
    head = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True, text=True, env=_env()).stdout.strip()
    flags = launch.window_flags(str(REPO), head)                      # unpatched here: only the `world` fixture patches it
    assert flags == set(real) and flags, "the launcher must read the same windows the SR-A6-GCW catalog reads"
    assert all(f.endswith("_schema_migration") for f in flags)
    assert not flags & {"force_all_services", "data_plane_cutover", "ci_gate", "emergency_reason", "window_lease_id"}


@pytest.mark.parametrize("dry", [False, True])
def test_p5_a_flag_that_is_not_a_window_is_refused(world, capsys, dry):
    rc, out, err = world.go(capsys, dry_run=dry, flag="force_all_services")
    assert rc == 1 and "not a protected schema window" in err and world.workflow_runs() == []


@pytest.mark.parametrize("dry", [False, True])
def test_p6_the_window_lease_must_be_the_requests_own_lease(world, capsys, monkeypatch, dry):
    monkeypatch.setenv("KY_OPERATION_REQUEST", json.dumps({"lease_id": "SOME-OTHER-LEASE"}))
    rc, out, err = world.go(capsys, dry_run=dry)
    assert rc == 1 and "not the request's own lease_id" in err and world.workflow_runs() == []


def test_p6_a_live_request_without_a_lease_is_refused(world, capsys, monkeypatch):
    monkeypatch.setenv("KY_OPERATION_REQUEST", json.dumps({}))
    rc, out, err = world.go(capsys)
    assert rc == 1 and "no lease_id" in err and world.workflow_runs() == []


@pytest.mark.parametrize("dry", [False, True])
def test_p7_another_active_lease_refuses_before_any_dispatch(tmp_path, monkeypatch, capsys, dry):
    w = World(tmp_path, table((LEASE, 5, "ACTIVE"), ("J-3", 5, "ACTIVE")), monkeypatch)
    rc, out, err = w.go(capsys, dry_run=dry)
    assert rc == 1 and "J-3" in err and w.workflow_runs() == []


@pytest.mark.parametrize("why", ["no_branch", "own_not_active"])
def test_p7_an_unreadable_table_or_an_inactive_own_lease_refuses(tmp_path, monkeypatch, capsys, why):
    w = World(tmp_path, None if why == "no_branch" else table((LEASE, 5, "RELEASED")), monkeypatch)
    rc, out, err = w.go(capsys)
    assert rc == 1 and err.startswith("REFUSED") and w.workflow_runs() == []


# ───────────────────────────── P8 / P9 the dispatch ─────────────────────────────

def test_p8_the_lease_is_read_again_immediately_before_the_dispatch(world, capsys, monkeypatch):
    reads = []
    real = launch.gate.read_table
    def flips_after_planning(repo):
        reads.append(1)
        return real(repo) if len(reads) == 1 else table((LEASE, 5, "ACTIVE"), ("J-3", 5, "ACTIVE"))   # a foreign lease appears after the plan
    monkeypatch.setattr(launch.gate, "read_table", flips_after_planning)
    rc, out, err = world.go(capsys)
    assert rc == 1 and "J-3" in err and len(reads) == 2 and world.workflow_runs() == []


def test_p9_the_dispatch_is_exactly_the_reviewed_workflow_call(world, capsys):
    rc, out, err = world.go(capsys)
    assert rc == 0, err
    assert world.workflow_runs() == [["workflow", "run", "deploy.yml", "--ref", "main", "-f", "ci_gate=require-ci-green",
                                      "-f", f"window_lease_id={LEASE}", "-f", f"{FLAG}=true"]]


# ───────────────────────────── P10 / P11 remote-async and the run line ─────────────────────────────

def test_p10_it_returns_once_the_run_is_identified_with_one_window_run_line(world, capsys):
    world.put("view.json", json.dumps(view("in_progress", [step(CAPABILITY_STEP, "in_progress", "2026-10-20T01:00:00Z")])))   # still running: the window is not waited for
    rc, out, err = world.go(capsys)
    lines = out.strip().splitlines()
    assert rc == 0 and len(lines) == 1, (out, err)
    line = json.loads(lines[0])
    assert line["schema"] == "ky.window_run/1" and line["run_id"] == 777 and line["status"] == "in_progress" and line["completed_at"] is None
    assert [c for c in world.calls() if c[:2] == ["run", "view"]] == [["run", "view", "777", "--json", "databaseId,status,conclusion,jobs"]]


def test_p11_window_run_line_fields():
    queued = launch.window_run_line(view("queued", [step(CAPABILITY_STEP, "pending")]))
    assert set(queued) == {"schema", "run_id", "status", "conclusion", "capability_step_started", "latest_step_progress_at", "completed_at", "steps"}
    assert queued["capability_step_started"] is False and queued["latest_step_progress_at"] is None and queued["completed_at"] is None

    running = launch.window_run_line(view("in_progress", [
        step("Set up job", "completed", "2026-10-20T01:00:00Z", "2026-10-20T01:00:05Z", "success"),
        step(CAPABILITY_STEP, "in_progress", "2026-10-20T01:02:00Z")]))
    assert running["capability_step_started"] is True and running["latest_step_progress_at"] == "2026-10-20T01:02:00Z"
    other_step = launch.window_run_line(view("in_progress", [step("Set up job", "in_progress", "2026-10-20T01:00:00Z")]))
    assert other_step["capability_step_started"] is False            # only the migration step counts

    done = launch.window_run_line(view("completed", [step(CAPABILITY_STEP, "completed", "2026-10-20T01:02:00Z", "2026-10-20T01:09:00Z", "success")],
                                       conclusion="success", job_completed="2026-10-20T01:09:30Z"))
    assert done["conclusion"] == "success" and done["completed_at"] == "2026-10-20T01:09:30Z" and done["latest_step_progress_at"] == "2026-10-20T01:09:00Z"
    assert done["steps"] == [{"job": "protected", "name": CAPABILITY_STEP, "status": "completed", "conclusion": "success",
                              "started_at": "2026-10-20T01:02:00Z", "completed_at": "2026-10-20T01:09:00Z"}]


# ───────────────────────────── P12 / P13 uncertain outcomes ─────────────────────────────

@pytest.mark.parametrize("after", [[], [{"databaseId": 1, "headSha": "x", "event": "workflow_dispatch"}], "two"])
def test_p12_an_unidentified_run_is_exit_1_and_never_dispatched_twice(world, capsys, after):
    if after == "two":
        after = [{"databaseId": i, "headSha": world.head, "event": "workflow_dispatch"} for i in (5, 6)]
    elif after:
        after[0]["headSha"] = "f" * 40           # a run of another head is not this dispatch
    world.put("runs_after.json", json.dumps(after))
    rc, out, err = world.go(capsys)
    line = json.loads(out)
    assert rc == 1 and line["run_id"] is None and line["status"] == "dispatched_unidentified" and "never retry" in err
    assert len(world.workflow_runs()) == 1


def test_p13_a_failed_workflow_run_is_a_refusal_without_a_window_run_line(world, capsys):
    (world.gh_dir / "fail_dispatch").write_text("1")
    rc, out, err = world.go(capsys)
    assert rc == 1 and out == "" and "dispatch failed or is uncertain" in err


# ───────────────────────────── P14 approval stays a person's ─────────────────────────────

def test_p14_only_reads_and_the_one_workflow_run_reach_gh(world, capsys):
    rc, out, err = world.go(capsys)
    assert rc == 0, err
    for call in world.calls():
        kind = tuple(call[:2])
        assert kind in {("api", call[1]), ("workflow", "run"), ("run", "list"), ("run", "view")}, call
        if call[0] == "api":                        # a plain GET of the main ref: no method, no field, no approval/review endpoint
            assert call == ["api", "repos/{owner}/{repo}/git/ref/heads/main"], call
    assert not any("pending_deployments" in " ".join(c) or "approve" in " ".join(c) for c in world.calls())


# ───────────────────────────── P15 the dry run ─────────────────────────────

def test_p15_the_dry_run_prints_its_verdict_and_never_dispatches(world, capsys):
    rc, out, err = world.go(capsys, dry_run=True)
    assert rc == 0, err
    line = json.loads(out)
    assert line["schema"] == "ky.window_dryrun/1" and line["verdict"] == "OK" and line["flag"] == FLAG and line["head"] == world.head and line["window_lease_id"] == LEASE
    assert world.workflow_runs() == [] and [c for c in world.calls() if c[:2] == ["run", "list"]] == []
