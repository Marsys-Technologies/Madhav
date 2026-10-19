"""U-M-12: `github_run_readback` — a read-only, fixed-argument measurement of ONE protected-window GitHub Actions run, printing the
`ky.window_run/1` line the window watch reads (union pack MISSING.json U-M-01 contract: {run_id, status, conclusion,
capability_step_started, latest_step_progress_at, completed_at, steps[]}; consumers: PACK watch_obs.build_obs / watch_gate._evaluate and
prepare_union.py's `json.loads(line)["run_id"]`).

One oracle per distinct production claim; each cites its source. No `gh`, credential, network or database is touched: the script's `runner`
is a double that returns GitHub REST shaped JSON (Workflow runs: "Get a workflow run" and "List jobs for a workflow run"), and one end-to-end
test runs the script as a subprocess against a stub `gh` on PATH.

  G1  exactly two fixed, read-only `gh api -X GET` calls on the repository's own run                          (REST: GET /repos/{o}/{r}/actions/runs/{id}[/jobs])
  G2  only a decimal run id is accepted; a malformed one stops before any call
  G3  the line carries the U-M-01 contract keys, `schema` ky.window_run/1, and the run's own status / conclusion
  G4  capability_step_started is the start of the ONE step deploy.yml names `Grant temporary public-schema capability`; absent = null
  G5  latest_step_progress_at is the newest step start/completion over all jobs; a time GitHub has not set stays null, never the clock
  G6  completed_at is the newest job completion and only for a completed run
  G7  any record that cannot be read as what it claims REFUSES (no `status` key, exit 1), and gh's stderr is never relayed
  G8  only the two protected-window workflows can be read
  G9  the table binds the kind exactly, DISABLED, and the real `validate` refuses a disabled kind and any other argument
  G10 end to end through the CLI: one JSON line the consumers' own extraction reads; exit 0 / 1
"""
import copy
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
FLEET = HERE.parent
REPO = FLEET.parents[3]
SCRIPT = FLEET / "github_run_readback.py"

spec = importlib.util.spec_from_file_location("github_run_readback_under_test", SCRIPT)
GR = importlib.util.module_from_spec(spec)
spec.loader.exec_module(GR)

RUN_ID = "9876543210"
HEAD = "0123456789abcdef0123456789abcdef01234567"
DEPLOY = ".github/workflows/deploy.yml"
PROVISION = ".github/workflows/gochara-role-provisioning-oneshot.yml"
CAPABILITY = "Grant temporary public-schema capability"
CONTRACT_KEYS = {"run_id", "status", "conclusion", "capability_step_started", "latest_step_progress_at", "completed_at", "steps"}
T = lambda hms: f"2026-10-20T{hms}Z"            # noqa: E731 — a compact stamp builder


def step(number, name, status="completed", conclusion="success", started=None, completed=None):
    return {"name": name, "status": status, "conclusion": conclusion, "number": number, "started_at": started, "completed_at": completed}


def run_body(status="in_progress", conclusion=None, path=DEPLOY, run_id=int(RUN_ID)):
    return {"id": run_id, "path": path, "status": status, "conclusion": conclusion, "event": "workflow_dispatch", "head_sha": HEAD, "run_attempt": 1}


def jobs_body(*jobs):
    return {"total_count": len(jobs), "jobs": list(jobs)}


def job(name, steps, completed=None):
    return {"name": name, "status": "completed" if completed else "in_progress", "completed_at": completed, "steps": steps}


def mid_run_jobs():
    """The migration job part-way: set-up done, capability granted at 10:05:00, the migrate step running since 10:06:30."""
    return jobs_body(
        job("Apply Protected Public-Schema Migrations", [
            step(1, "Set up job", started=T("10:00:00"), completed=T("10:00:02")),
            step(2, "Validate migration database routes", started=T("10:00:02"), completed=T("10:05:00")),
            step(3, CAPABILITY, started=T("10:05:00"), completed=T("10:06:30")),
            step(4, "Apply migrations", status="in_progress", conclusion=None, started=T("10:06:30")),
            step(5, "Revoke temporary public-schema capability", status="pending", conclusion=None),
        ]))


class Gh:
    """Answers the two fixed calls; records every argv."""

    def __init__(self, run=None, jobs=None, rc=None, raw=None):
        self.run = run if run is not None else run_body()
        self.jobs = jobs if jobs is not None else mid_run_jobs()
        self.rc, self.raw, self.calls = rc or {}, raw or {}, []

    def __call__(self, argv):
        self.calls.append(argv)
        which = "jobs" if "/jobs" in argv[-1] else "run"
        body = self.raw.get(which, json.dumps(self.jobs if which == "jobs" else self.run))
        return subprocess.CompletedProcess(argv, self.rc.get(which, 0), body, "ERROR: noisy token ghp_LEAK")


CLOCK = lambda: __import__("datetime").datetime(2026, 10, 20, 10, 9, 0, tzinfo=__import__("datetime").timezone.utc)   # noqa: E731


def measure(gh=None, run_id=RUN_ID):
    gh = gh or Gh()
    return GR.measure(run_id, gh, CLOCK), gh


def refusal(gh, run_id=RUN_ID):
    with pytest.raises(GR.Refused) as caught:
        GR.measure(run_id, gh, CLOCK)
    return str(caught.value)


# ───────────── G1 the calls ─────────────

def test_g1_two_fixed_read_only_calls_on_this_repository():
    record, gh = measure()
    assert gh.calls == [
        ["gh", "api", "-X", "GET", f"repos/Marsys-Technologies/Madhav/actions/runs/{RUN_ID}"],
        ["gh", "api", "-X", "GET", f"repos/Marsys-Technologies/Madhav/actions/runs/{RUN_ID}/jobs?per_page=100"],
    ]
    for argv in gh.calls:                                           # a field flag (-f/-F/--input) would turn gh api into a POST
        assert argv[:5] == ["gh", "api", "-X", "GET", argv[4]] and not {"-f", "-F", "--input", "--method"} & set(argv)
    assert record["repo"] == "Marsys-Technologies/Madhav"


# ───────────── G2 the argument ─────────────

@pytest.mark.parametrize("bad", ["", "0", "01", "12a", "-1", "1 2", "../actions", "1" * 21, "1;rm"])
def test_g2_only_a_decimal_run_id_and_it_stops_before_any_call(bad):
    gh = Gh()
    with pytest.raises(GR.Refused):
        GR.measure(bad, gh, CLOCK)
    assert gh.calls == []


# ───────────── G3 the contract line ─────────────

def test_g3_the_line_carries_the_u_m_01_contract():
    record, _ = measure()
    assert record["schema"] == "ky.window_run/1" and record["readback_status"] == "MEASURED"
    assert CONTRACT_KEYS <= set(record)
    assert (record["run_id"], record["status"], record["conclusion"]) == (int(RUN_ID), "in_progress", None)
    assert record["head_sha"] == HEAD and record["workflow"] == DEPLOY and record["event"] == "workflow_dispatch"
    assert [(s["number"], s["name"]) for s in record["steps"]][:3] == [(1, "Set up job"), (2, "Validate migration database routes"), (3, CAPABILITY)]
    assert set(record["steps"][0]) == {"job", "number", "name", "status", "conclusion", "started_at", "completed_at"}
    done, _ = measure(Gh(run=run_body("completed", "failure")))
    assert (done["status"], done["conclusion"]) == ("completed", "failure")


# ───────────── G4 the exposure clock ─────────────

def test_g4_capability_step_started_is_the_one_step_the_workflow_names_and_absence_is_null():
    deploy_yml = (REPO / DEPLOY).read_text()
    assert f"- name: {CAPABILITY}" in deploy_yml and GR.CAPABILITY_STEP == CAPABILITY      # the name is the workflow's own, not a copy that can drift
    record, _ = measure()
    assert (record["capability_step_found"], record["capability_step_started"]) == (True, T("10:05:00"))
    pending = mid_run_jobs()
    pending["jobs"][0]["steps"][2] = step(3, CAPABILITY, status="pending", conclusion=None)
    waiting, _ = measure(Gh(jobs=pending))
    assert (waiting["capability_step_found"], waiting["capability_step_started"]) == (True, None)      # the step exists but has not started: null, not 'now'
    other, _ = measure(Gh(run=run_body(path=PROVISION), jobs=jobs_body(job("provision", [step(1, "Checkout the dispatched commit", started=T("10:00:00"), completed=T("10:00:03"))]))))
    assert (other["capability_step_found"], other["capability_step_started"]) == (False, None)         # no stand-in step for a workflow without one
    twice = mid_run_jobs()
    twice["jobs"].append(job("Another job", [step(1, CAPABILITY, started=T("10:07:00"), completed=T("10:07:01"))]))
    twice["total_count"] = 2
    assert "more than once" in refusal(Gh(jobs=twice))


# ───────────── G5 step progress ─────────────

def test_g5_latest_step_progress_is_the_newest_start_or_completion_over_every_job_and_unset_is_null():
    record, _ = measure()
    assert record["latest_step_progress_at"] == T("10:06:30")       # the running step's start is the newest time anywhere
    second = mid_run_jobs()
    second["jobs"].append(job("Second job", [step(1, "Set up job", started=T("10:08:10"), completed=T("10:08:40"))]))
    second["total_count"] = 2
    assert measure(Gh(jobs=second))[0]["latest_step_progress_at"] == T("10:08:40")
    queued = jobs_body(job("Apply Protected Public-Schema Migrations", [step(1, "Set up job", status="queued", conclusion=None)]))
    waiting, _ = measure(Gh(run=run_body("waiting"), jobs=queued))
    assert waiting["latest_step_progress_at"] is None and waiting["capability_step_started"] is None      # the approval wait: nothing has run, nothing is invented
    assert measure(Gh(run=run_body("queued"), jobs=jobs_body()))[0]["latest_step_progress_at"] is None
    assert measure(Gh(run=run_body("queued"), jobs={"total_count": 1, "jobs": [{"name": "j", "completed_at": None, "steps": None}]}))[0]["steps"] == []


# ───────────── G6 completion ─────────────

def test_g6_completed_at_is_the_newest_job_completion_and_only_for_a_completed_run():
    finished = mid_run_jobs()
    finished["jobs"][0]["completed_at"] = T("10:09:30")
    finished["jobs"].append(job("Earlier job", [], completed=T("10:01:00")))
    finished["total_count"] = 2
    assert measure(Gh(run=run_body("in_progress"), jobs=copy.deepcopy(finished)))[0]["completed_at"] is None       # a job done inside a running run is not the run done
    assert measure(Gh(run=run_body("completed", "success"), jobs=copy.deepcopy(finished)))[0]["completed_at"] == T("10:09:30")
    unset = mid_run_jobs()
    assert measure(Gh(run=run_body("completed", "cancelled"), jobs=unset))[0]["completed_at"] is None             # GitHub set no time: null, not the clock


# ───────────── G7 refusals ─────────────

@pytest.mark.parametrize("mutate,expected", [
    (lambda r, j: r.update(status="running"), "'status'"),
    (lambda r, j: r.update(status="completed", conclusion=None), "must carry a conclusion"),
    (lambda r, j: r.update(conclusion="success"), "must carry a conclusion"),
    (lambda r, j: r.update(conclusion="great"), "'conclusion'"),
    (lambda r, j: r.update(id=1), "different run id"),
    (lambda r, j: r.update(head_sha="abc"), "head_sha"),
    (lambda r, j: j["jobs"][0]["steps"][3].update(started_at="2026-10-20 10:06:30"), "RFC 3339"),
    (lambda r, j: j["jobs"][0]["steps"][3].update(started_at=1760000000), "RFC 3339"),
    (lambda r, j: j["jobs"][0].update(completed_at="yesterday"), "RFC 3339"),
    (lambda r, j: j.update(total_count=250), "cut short"),
    (lambda r, j: j["jobs"][0]["steps"][0].pop("name"), "no name or number"),
    (lambda r, j: j["jobs"][0]["steps"][0].update(status="exploded"), "'status'"),
])
def test_g7_an_unreadable_record_refuses_whole(mutate, expected):
    run, jobs = run_body(), mid_run_jobs()
    mutate(run, jobs)
    assert expected in refusal(Gh(run=run, jobs=jobs))


@pytest.mark.parametrize("gh,expected", [
    (Gh(rc={"run": 1}), "run: gh exited 1"),
    (Gh(rc={"jobs": 4}), "jobs: gh exited 4"),
    (Gh(raw={"run": "not json"}), "run: gh output is not JSON"),
    (Gh(raw={"jobs": "[]"}), "jobs: gh output is not a JSON object"),
])
def test_g7_a_gh_failure_refuses_and_its_stderr_is_never_relayed(gh, expected):
    message = refusal(gh)
    assert expected in message and "ghp_LEAK" not in message


def test_g7_a_refusal_carries_no_status_key_so_a_consumer_reads_null(capsys):
    gh = Gh(rc={"run": 1})
    assert GR.cli(["--run", RUN_ID], runner=gh) == 1
    record = json.loads(capsys.readouterr().out)
    assert record["schema"] == "ky.window_run/1" and record["readback_status"] == "REFUSED"
    assert "status" not in record and "run_id" not in record and "steps" not in record


# ───────────── G8 the workflow allow-list ─────────────

def test_g8_only_the_two_protected_window_workflows_can_be_read():
    for path in (DEPLOY, PROVISION, DEPLOY + "@refs/heads/main"):
        assert measure(Gh(run=run_body(path=path)))[0]["workflow"] == path.split("@")[0]
    for path in (".github/workflows/ci.yml", ".github/workflows/deploy.yml.bak", "deploy.yml", None, 7):
        assert "protected-window workflow" in refusal(Gh(run=run_body(path=path)))
    for workflow in GR.WORKFLOWS:
        assert (REPO / workflow).is_file(), f"{workflow} no longer exists in the repository"


# ───────────── G9 the table binding, through the real validate ─────────────

def _executor(tmp_path, monkeypatch):
    monkeypatch.setenv("KY_ROOT", str(tmp_path / "ky"))
    spec_ = importlib.util.spec_from_file_location(f"ky_exec_gr_{abs(hash(str(tmp_path)))}", FLEET / "executor.py")
    module = importlib.util.module_from_spec(spec_)
    spec_.loader.exec_module(module)
    return module


def _req(**over):
    req = {"operation_id": "op-gr", "kind": "github_run_readback", "item_id": "KA-3a", "idempotency_key": "key-gr", "requested_by": "adhikarin", "kyd": "kyd-1", "args": {"run": RUN_ID}}
    req.update(over)
    return req


def test_g9_table_entry_is_exact_shipped_disabled_and_the_real_validate_holds(tmp_path, monkeypatch):
    table = json.loads((FLEET / "executor_ops.json").read_text())["ops"]
    entry = table["github_run_readback"]
    assert list(entry)[0] == "enabled" and entry["enabled"] is False                  # shipped disabled: the owner's flip enables it
    assert (entry["production"], entry["read_only"], entry["needs"], entry["fixed_args"], entry["allowed_args"]) == (False, True, "none", [], ["run"])
    assert entry["script"] == "00_ARCHITECTURE/briefs/kalayantra/fleet/github_run_readback.py" and (REPO / entry["script"]).is_file()
    assert entry["requesters"] == ["adhikarin", "v1", "v2"] and "also_needs" not in entry and entry["enabled_by"] == "J-4b"
    ex = _executor(tmp_path, monkeypatch)
    caps = {"none": True}
    assert "is not enabled" in ex.validate(_req(), table, caps)                         # disabled: refused today
    live = copy.deepcopy(table)
    live["github_run_readback"]["enabled"] = True
    assert ex.validate(_req(), live, caps) is None
    assert "disallowed args" in ex.validate(_req(args={"run": RUN_ID, "repo": "other/repo"}), live, caps)
    assert "disallowed args" in ex.validate(_req(args={"workflow": "deploy.yml"}), live, caps)
    assert "may not request" in ex.validate(_req(requested_by="sutradhara"), live, caps)
    assert "unsafe characters" in ex.validate(_req(args={"run": "1 2"}), live, caps)


# ───────────── G10 end to end through the CLI ─────────────

def _stub_gh(directory):
    (directory / "run.json").write_text(json.dumps(run_body("completed", "success")))
    (directory / "jobs.json").write_text(json.dumps(mid_run_jobs()))
    stub = directory / "gh"
    stub.write_text("#!/bin/sh\n"
                    f'echo "$@" >> "{directory}/calls.log"\n'
                    'echo "ERROR: noisy token ghp_LEAK" >&2\n'
                    f'case "$*" in *"/jobs"*) cat "{directory}/jobs.json";; *) cat "{directory}/run.json";; esac\n')
    stub.chmod(0o755)


def test_g10_cli_prints_one_line_the_consumers_own_extraction_reads(tmp_path):
    _stub_gh(tmp_path)
    env = {"PATH": f"{tmp_path}:/usr/bin:/bin", "HOME": str(tmp_path)}
    done = subprocess.run([sys.executable, "-I", str(SCRIPT), "--run", RUN_ID], capture_output=True, text=True, env=env, cwd=tmp_path)
    assert done.returncode == 0, done.stdout + done.stderr
    assert "ghp_LEAK" not in done.stdout + done.stderr
    assert len(done.stdout.strip().splitlines()) == 1
    calls = (tmp_path / "calls.log").read_text().splitlines()
    assert len(calls) == 2 and all(c.startswith("api -X GET repos/Marsys-Technologies/Madhav/actions/runs/") for c in calls)
    # prepare_union.py (U-M-01 consumer): `line.startswith("{") and "ky.window_run/1" in line` then json.loads(line)["run_id"]
    # watch_obs.last_json: the same predicate, then {k: run.get(k) for k in the contract keys}
    line = next(l for l in done.stdout.splitlines() if l.startswith("{") and "ky.window_run/1" in l)
    seen = json.loads(line)
    assert str(seen["run_id"]) == RUN_ID and CONTRACT_KEYS <= set(seen)
    assert (seen["status"], seen["conclusion"], seen["capability_step_started"]) == ("completed", "success", T("10:05:00"))
    bad = subprocess.run([sys.executable, "-I", str(SCRIPT), "--run", "nope"], capture_output=True, text=True, env=env, cwd=tmp_path)
    assert bad.returncode == 1 and json.loads(bad.stdout)["readback_status"] == "REFUSED"
    extra = subprocess.run([sys.executable, "-I", str(SCRIPT), "--run", RUN_ID, "--repo", "x/y"], capture_output=True, text=True, env=env, cwd=tmp_path)
    assert extra.returncode == 2 and len((tmp_path / "calls.log").read_text().splitlines()) == 2
