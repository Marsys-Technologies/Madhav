"""B-0c control modules (relaunch plan v2.7 §4a.1 "Action records", §4a.3, §4a.5, §4a.6; §6 SURROGATE row;
pairing rule KW-04): kyaction.py (crash-safe action records), kycommands.py (the cockpit command queue) and
kyveto.py (the deterministic veto-window handler), with their three schemas.

Nothing here touches /Users/Dev/kalayantra, the real `ky`, the tracker, launchctl, gh, a database or the
network: every test runs in its own tree under pytest's basetemp with the doubles in fixtures/b0c_control/
(fake_ky, fake_git, crash_tick.py). An autouse fixture points KY_ROOT / KY_RUN / KY_FLEET at a guard directory,
so a code path that fell back to the process environment still could not reach the live tree. Every rule is
shown passing and failing, and a refusal is asserted by its named reason, not only by "something failed".

Time (B-0c rework 1, ruling R3): the veto handler's effecting path reads the wall clock only. In-process tests
replace the module-level `kyveto.wall_clock` (the `clock` helper, `World.tick(now)`); tests that run the real
`kyveto.py tick` in a subprocess cannot drive its clock at all, so every proposal here lies two hours in the
real past (T0) and such a tick simply finds its window long expired. The evidence a real run would hold by
then — kynotify's journal line and the handler's first-seen stamp — is planted by `World.propose`, the stamp
through the handler's own function. Every line the handler appends, in any test, is validated against
schemas/surrogate_decision.json when the test ends.

Set KY_TEST_PYTHON to run the subprocess cases under another interpreter (e.g. /usr/bin/python3 = 3.9).
"""
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

FLEET = Path(__file__).resolve().parents[1]
FIX = FLEET / "tests" / "fixtures" / "b0c_control"
SCHEMAS = FLEET / "schemas"
PY = os.environ.get("KY_TEST_PYTHON") or sys.executable
sys.dont_write_bytecode = True                 # leave no __pycache__ next to the sources under test
sys.path.insert(0, str(FLEET))

import kyaction  # noqa: E402
import kycommands  # noqa: E402
import kyschema  # noqa: E402
import kyveto  # noqa: E402

PINNED_DEFAULT_SOURCE_REPO = kyveto.DEFAULT_SOURCE_REPO          # read before the fixture below replaces it
ACTOR = {"role": "planner", "holder_kind": "cockpit", "session_id": "sess-1"}
COCKPIT = {"kind": "cockpit", "session_id": "sess-1"}
C1, C2, C3 = "1" * 40, "2" * 40, "3" * 40
E1, E2 = "e" * 64, "f" * 64
M1, M2, M3 = "a" * 64, "b" * 64, "c" * 64
T0 = int(time.time()) - 7200                   # every proposal was notified, and first seen, two real hours ago


def iso(offset):
    """UTC ISO-8601 of T0 + offset seconds."""
    return kyaction.utc(T0 + offset)


T_NOTIFY, T_DEADLINE = iso(0), iso(1800)
BEFORE, AT, AFTER, LATER = iso(600), T_DEADLINE, iso(1860), iso(2400)
TD = {"id": "D-41", "outcome": "approved"}
DECISION_SCHEMA = json.loads((SCHEMAS / "surrogate_decision.json").read_text(encoding="utf-8"))
SUB_ENV = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": os.environ.get("HOME", "/nonexistent"),
           "PYTHONDONTWRITEBYTECODE": "1"}


@pytest.fixture(autouse=True)
def _never_the_live_tree(monkeypatch, tmp_path):
    for name, sub in (("KY_ROOT", "guard"), ("KY_RUN", "guard/run"), ("KY_FLEET", "guard/fleet_live")):
        monkeypatch.setenv(name, str(tmp_path / sub))
    for name in ("KY_BIN", "KY_GIT", "KY_SOURCE_REPO", "KY_OWNER_DECISIONS_PATH", "KYVETO_KY_TIMEOUT_S"):
        monkeypatch.delenv(name, raising=False)
    # the default source checkout is a real directory on the campaign host: no test may ever fall back to it
    monkeypatch.setattr(kyveto, "DEFAULT_SOURCE_REPO", str(tmp_path / "no-default-source-repo"))
    monkeypatch.setattr(kyveto, "wall_clock", kyveto.wall_clock)          # whatever a test does to the clock is undone


@pytest.fixture(autouse=True)
def _every_line_the_handler_appends_is_a_valid_decision_line(monkeypatch, tmp_path):
    """Interface with schemas/surrogate_decision.json (supervisor area): the handler never writes a line the
    schema refuses. In-process appends are caught at the call; appends made by a `kyveto.py` subprocess are found
    in the logs afterwards (a handler line carries `at`; the lines tests forge under its name do not)."""
    appended, real = [], kyveto.append_line

    def recording(path, obj):
        appended.append(json.loads(json.dumps(obj)))
        return real(path, obj)

    monkeypatch.setattr(kyveto, "append_line", recording)
    yield
    for log in tmp_path.rglob("DECISIONS_SURROGATE.jsonl"):
        for raw in log.read_bytes().split(b"\n"):
            try:
                line = json.loads(raw)
            except ValueError:
                continue
            if isinstance(line, dict) and line.get("by") == "kyveto" and "at" in line:
                appended.append(line)
    for line in appended:
        found = kyschema.validate(DECISION_SCHEMA, line)
        assert found == [], "the handler appended a line the decision schema refuses:\n%s\n%s" % (
            json.dumps(line, sort_keys=True), "\n".join(found))


# ───────────────────────────────────────────── helpers ─────────────────────────────────────────────

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def schema_errors(name, doc):
    return kyschema.validate(json.loads((SCHEMAS / (name + ".json")).read_text(encoding="utf-8")), doc)


def assert_schema(name, doc):
    found = schema_errors(name, doc)
    assert found == [], "\n".join(found)


def mkrun(tmp_path):
    run = tmp_path / "run"
    run.mkdir()
    return run


def tree(root, skip=("locks",)):
    """{relative path: bytes} of every file under root, the lock directory excepted (locks come and go)."""
    out = {}
    for p in sorted(Path(root).rglob("*")):
        rel = p.relative_to(root)
        if p.is_file() and rel.parts[0] not in skip:
            out[str(rel)] = p.read_bytes()
    return out


def dead_pid():
    p = subprocess.Popen([PY, "-c", "pass"])
    p.wait()
    return p.pid


class clock:
    """Drive the veto handler's one clock, in-process: `with clock(AT): …` (an ISO string or epoch seconds)."""

    def __init__(self, now):
        self.now = kyaction.parse_utc(now) if isinstance(now, str) else float(now)
        assert self.now is not None

    def __enter__(self):
        self.real, kyveto.wall_clock = kyveto.wall_clock, lambda: self.now
        return self

    def __exit__(self, *exc):
        kyveto.wall_clock = self.real


class bystander:
    """A live process that is neither this one nor one of its ancestors: `with bystander() as (pid, start): …`."""

    def __enter__(self):
        self.p = subprocess.Popen([PY, "-c", "import time; time.sleep(120)"])
        for _ in range(200):
            ident = kyaction.ps_identity(self.p.pid)
            if ident:
                return self.p.pid, ident[1]
            time.sleep(0.01)
        raise AssertionError("the bystander process did not start")

    def __exit__(self, *exc):
        self.p.kill()
        self.p.wait()


def no_ps(monkeypatch):
    """`ps` cannot be started at all (the reviewer's probe for CT-03)."""
    monkeypatch.setattr(kyaction, "PS", "/nonexistent/ps")


def hold(run, role, owner_id, pid=None, start=None):
    """The role lock exactly as a controller writes it: $KY_RUN/locks/<role>/owner.json."""
    me = kyaction.self_identity()
    d = Path(run) / "locks" / role
    d.mkdir(parents=True, exist_ok=True)
    (d / "owner.json").write_text(json.dumps({
        "session_or_run_id": owner_id, "pid": me["pid"] if pid is None else pid, "pgid": me["pgid"],
        "process_start": me["process_start"] if start is None else start, "acquired_at": kyaction.utc()}))


PRE = r"""
import json, os, sys, time
sys.path.insert(0, sys.argv[1])
import kyaction, kycommands
go, ready = sys.argv[2], sys.argv[3]
open(os.path.join(ready, str(os.getpid())), "w").close()
while not os.path.exists(go):
    time.sleep(0.0005)
"""


def race(tmp_path, n, argv_for):
    """Start n processes that all wait for the same starting gun; → (returncodes, stdouts, stderrs)."""
    go, ready = tmp_path / "go", tmp_path / "ready"
    ready.mkdir()
    procs = [subprocess.Popen(argv_for(go, ready), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                              env=SUB_ENV) for _ in range(n)]
    deadline = time.time() + 30
    while len(list(ready.iterdir())) < n and time.time() < deadline:
        time.sleep(0.01)
    go.write_text("")
    outs = [p.communicate(timeout=60) for p in procs]
    return [p.returncode for p in procs], [o[0].strip() for o in outs], [o[1] for o in outs]


def snippet(body, *args):
    return lambda go, ready: [PY, "-c", PRE + body, str(FLEET), str(go), str(ready)] + [str(a) for a in args]


# ═════════════════════════════════════════════ schemas ═════════════════════════════════════════════

@pytest.mark.parametrize("name", ["action", "command", "activation_record"])
def test_schema_uses_only_keywords_the_fleet_validator_supports(name):
    r = subprocess.run([PY, str(FLEET / "kyschema.py"), "lint", str(SCHEMAS / (name + ".json"))],
                       capture_output=True, text=True, env=SUB_ENV)
    assert r.returncode == 0, r.stderr


def test_action_schema_admits_the_record_the_cockpit_already_wrote():
    doc = json.loads((FIX / "action_example_cockpit.json").read_text(encoding="utf-8"))
    assert doc["state"] == "DONE"
    assert_schema("action", doc)


@pytest.mark.parametrize("change,needle", [
    ({"state": "INTENDED"}, "result"),                       # INTENDED may not carry a result
    ({"state": "DONE", "result": None, "completed_at": None}, "result"),      # DONE must carry one
    ({"state": "MAYBE"}, "state"),
    ({"action_id": "bad id"}, "action_id"),
    ({"actor": {"role": "planner", "holder_kind": "cockpit"}}, "actor"),       # neither session_id nor controller_id
    ({"actor": {"role": "planner", "holder_kind": "robot", "session_id": "s"}}, "holder_kind"),
    ({"extra": 1}, "extra"),
])
def test_action_schema_refuses(change, needle):
    doc = json.loads((FIX / "action_example_cockpit.json").read_text(encoding="utf-8"))
    doc.update(change)
    found = schema_errors("action", doc)
    assert found and any(needle in line for line in found), found


JOB_ACTOR = {"role": "planner", "holder_kind": "job", "controller_id": "CTL-PLANNER-1", "run_id": "PLANNER-20261011T220000Z"}
JOB_ID = "JOB-PLANNER-20261011T220000Z-push"


def job_doc(**change):
    doc = json.loads((FIX / "action_example_cockpit.json").read_text(encoding="utf-8"))
    doc.update(action_id=JOB_ID, actor=dict(JOB_ACTOR), process=None)
    doc.update(change)
    return doc


def test_action_schema_admits_a_job_authored_record_in_its_own_namespace():
    assert_schema("action", job_doc())
    assert_schema("action", job_doc(action_id="JOB-PLANNER-20261011T220000Z-02-open-pr.2"))     # run …Z-02, slug open-pr.2


@pytest.mark.parametrize("change,needle", [
    ({"action_id": "ACT-push"}, "action_id"),                               # a job writes only JOB-<run_id>-<slug>
    ({"action_id": "JOB-PLANNER-20261011T220000Z-Push"}, "action_id"),      # the slug starts with a lower-case letter
    ({"actor": {"role": "planner", "holder_kind": "job", "controller_id": "c"}}, "actor"),          # no run_id
    ({"actor": {"role": "planner", "holder_kind": "job", "run_id": "r", "session_id": "s"}}, "actor"),
    ({"actor": dict(JOB_ACTOR, session_id="s")}, "actor"),
    ({"actor": {"role": "planner", "holder_kind": "controller", "controller_id": "c"}}, "action_id"),   # JOB- is the jobs'
    ({"actor": {"role": "planner", "holder_kind": "controller", "controller_id": "c", "run_id": "r"},
      "action_id": "ACT-1"}, "actor"),                                      # run_id belongs to a job actor only
    ({"process": {"pid": 7, "process_start": "Mon Oct 12 02:45:03 2026"}}, "process"),     # a job's record names none
])
def test_action_schema_refuses_a_job_record_outside_the_rules(change, needle):
    found = schema_errors("action", job_doc(**change))
    assert found and any(needle in line for line in found), found


def test_action_schema_admits_the_process_that_began_a_record():
    doc = json.loads((FIX / "action_example_cockpit.json").read_text(encoding="utf-8"))
    assert_schema("action", dict(doc, process={"pid": 4242, "process_start": "Mon Oct 12 02:45:03 2026"}))
    assert_schema("action", dict(doc, process=None))
    for bad in ({"pid": 0, "process_start": "x"}, {"pid": 7}, {"pid": 7, "process_start": "x", "pgid": 7}, "me"):
        assert schema_errors("action", dict(doc, process=bad)), bad


# ═════════════════════════════════════════════ kyaction ═════════════════════════════════════════════

def begin(run, aid="ACT-1", inputs=None, target=None, kind="push", actor=ACTOR):
    return kyaction.begin(run, aid, kind, actor, {"branch": "b"} if inputs is None else inputs,
                          {"remote": "origin", "head": C1} if target is None else target, "local head → remote head")


def test_begin_persists_the_intended_record_before_any_side_effect(tmp_path):
    run = mkrun(tmp_path)
    status, rec = begin(run)
    assert status == "new"
    path = run / "actions" / "ACT-1.json"
    assert json.loads(path.read_text(encoding="utf-8")) == rec
    assert list(rec) == ["schema", "action_id", "kind", "actor", "inputs", "target", "intended_transition",
                         "created_at", "state", "result", "completed_at", "process"]      # the cockpit's shape + who
    me = kyaction.self_identity()
    assert rec["process"] == {"pid": os.getpid(), "process_start": me["process_start"]} and me["process_start"]
    assert (rec["schema"], rec["state"], rec["result"], rec["completed_at"]) == ("ky.action/1", "INTENDED", None, None)
    assert rec["actor"] == ACTOR and rec["inputs"] == {"branch": "b"} and rec["target"]["head"] == C1
    assert kyaction.parse_utc(rec["created_at"]) is not None
    assert_schema("action", rec)
    assert sorted(p.name for p in (run / "actions").iterdir()) == ["ACT-1.json"]         # no temp file left


def test_begin_never_overwrites_and_reports_the_existing_state(tmp_path):
    run = mkrun(tmp_path)
    begin(run)
    path = run / "actions" / "ACT-1.json"
    before = path.read_bytes()
    status, rec = begin(run, actor=dict(ACTOR, session_id="another-session"))
    assert status == "unfinished" and rec["actor"] == ACTOR            # reconcile before any retry
    assert path.read_bytes() == before
    kyaction.complete(run, "ACT-1", {"pushed": C1})
    done = path.read_bytes()
    status, rec = begin(run)
    assert status == "done" and rec["result"] == {"pushed": C1}        # the caller skips the side effect
    assert path.read_bytes() == done


def test_begin_reports_failed_and_only_retry_reopens_it(tmp_path):
    run = mkrun(tmp_path)
    begin(run)
    kyaction.fail(run, "ACT-1", {"error": "remote rejected"})
    status, rec = begin(run)
    assert status == "failed" and rec["state"] == "FAILED"
    again = kyaction.retry(run, "ACT-1", dict(ACTOR, session_id="sess-2"))
    assert again["state"] == "INTENDED" and again["result"] is None and again["completed_at"] is None
    assert again["actor"]["session_id"] == "sess-2"
    assert len(again["attempts"]) == 1
    first = again["attempts"][0]
    assert first["state"] == "FAILED" and first["result"] == {"error": "remote rejected"}
    assert first["actor"] == ACTOR and first["n"] == 1 and first["completed_at"]
    assert_schema("action", again)
    assert begin(run)[0] == "unfinished"
    kyaction.complete(run, "ACT-1", {"pushed": C1})
    final = kyaction.load(run, "ACT-1")
    assert final["state"] == "DONE" and len(final["attempts"]) == 1         # failure history is kept
    assert_schema("action", final)


@pytest.mark.parametrize("prepare", ["intended", "done"])
def test_retry_is_refused_unless_the_record_is_failed(tmp_path, prepare):
    run = mkrun(tmp_path)
    begin(run)
    if prepare == "done":
        kyaction.complete(run, "ACT-1", {"ok": True})
    before = (run / "actions" / "ACT-1.json").read_bytes()
    with pytest.raises(kyaction.ActionRefused):
        kyaction.retry(run, "ACT-1")
    assert (run / "actions" / "ACT-1.json").read_bytes() == before


def test_concurrent_begin_in_separate_processes_yields_exactly_one_new(tmp_path):
    run = mkrun(tmp_path)
    body = r"""
s, _ = kyaction.begin(sys.argv[4], "ACT-RACE", "push",
                      {"role": "planner", "holder_kind": "cockpit", "session_id": "s-%d" % os.getpid()},
                      {"a": 1}, {"t": 1}, "x")
print(s)
"""
    codes, outs, errs = race(tmp_path, 8, snippet(body, run))
    assert codes == [0] * 8, errs
    # the seven others see the winner's record: "in_progress" while its process lives, "unfinished" once it is gone
    assert outs.count("new") == 1 and set(outs) <= {"new", "in_progress", "unfinished"}, outs
    rec = kyaction.load(run, "ACT-RACE")
    assert rec["state"] == "INTENDED"
    assert sorted(p.name for p in (run / "actions").iterdir()) == ["ACT-RACE.json"]


def test_a_record_created_by_another_actor_at_the_last_moment_is_not_replaced(tmp_path, monkeypatch):
    """The deterministic form of the race: another actor's record appears after this caller has prepared its
    own and before it is put in place. The creation is exclusive, so this caller gets "unfinished", not "new"."""
    run = mkrun(tmp_path)
    real = kyaction._write_tmp
    other = dict(ACTOR, session_id="the-other-session")

    def raced(path, data, mode):
        tmp = real(path, data, mode)
        if Path(path).name == "ACT-1.json":
            monkeypatch.setattr(kyaction, "_write_tmp", real)
            assert begin(run, actor=other)[0] == "new"
        return tmp

    monkeypatch.setattr(kyaction, "_write_tmp", raced)
    status, rec = begin(run)
    assert status == "unfinished" and rec["actor"] == other
    assert kyaction.load(run, "ACT-1")["actor"] == other
    assert sorted(p.name for p in (run / "actions").iterdir()) == ["ACT-1.json"]


def test_write_exclusive_never_replaces_an_existing_file(tmp_path):
    path = tmp_path / "x.json"
    assert kyaction.write_exclusive(path, "first\n") is True
    assert kyaction.write_exclusive(path, "second\n") is False
    assert path.read_text() == "first\n" and sorted(p.name for p in tmp_path.iterdir()) == ["x.json"]


def test_the_observed_result_is_set_exactly_once(tmp_path):
    run = mkrun(tmp_path)
    begin(run)
    rec = kyaction.complete(run, "ACT-1", {"pushed": C1})
    assert rec["state"] == "DONE" and rec["result"] == {"pushed": C1} and rec["completed_at"]
    path = run / "actions" / "ACT-1.json"
    before = path.read_bytes()
    assert kyaction.complete(run, "ACT-1", {"pushed": C1}) == rec           # the same observation: no rewrite
    assert path.read_bytes() == before
    with pytest.raises(kyaction.ActionRefused):
        kyaction.complete(run, "ACT-1", {"pushed": C2})                     # a different result is refused
    with pytest.raises(kyaction.ActionRefused):
        kyaction.fail(run, "ACT-1", {"error": "late"})                      # DONE never becomes FAILED
    assert path.read_bytes() == before


def test_a_failed_record_is_not_completed_behind_its_back(tmp_path):
    run = mkrun(tmp_path)
    begin(run)
    kyaction.fail(run, "ACT-1", {"error": "x"})
    before = (run / "actions" / "ACT-1.json").read_bytes()
    assert kyaction.fail(run, "ACT-1", {"error": "x"})["state"] == "FAILED"
    with pytest.raises(kyaction.ActionRefused):
        kyaction.fail(run, "ACT-1", {"error": "y"})
    with pytest.raises(kyaction.ActionRefused):
        kyaction.complete(run, "ACT-1", {"ok": True})
    assert (run / "actions" / "ACT-1.json").read_bytes() == before


def test_complete_needs_an_existing_record_and_an_object_result(tmp_path):
    run = mkrun(tmp_path)
    with pytest.raises(kyaction.ActionError):
        kyaction.complete(run, "ACT-NONE", {"ok": True})
    begin(run)
    for bad in (None, "ok", ["ok"], {"when": object()}, {"x": float("nan")}):
        with pytest.raises(kyaction.ActionInvalid):
            kyaction.complete(run, "ACT-1", bad)
    assert kyaction.load(run, "ACT-1")["state"] == "INTENDED"


def test_reconcile_done_records_the_observed_result(tmp_path):
    run = mkrun(tmp_path)
    begin(run)
    seen = []

    def observer(record):
        seen.append(record["target"])
        return "done", {"remote_head": C1}

    outcome, rec = kyaction.reconcile(run, "ACT-1", observer)
    assert outcome == "done" and rec["state"] == "DONE" and rec["result"] == {"remote_head": C1}
    assert seen == [{"remote": "origin", "head": C1}]
    assert [r["outcome"] for r in rec["reconciliations"]] == ["done"]
    assert_schema("action", rec)
    calls = []
    outcome, again = kyaction.reconcile(run, "ACT-1", lambda r: calls.append(1) or ("not_done", "x"))
    assert outcome == "done" and again == rec and calls == []           # nothing left to observe


def test_reconcile_not_done_leaves_the_record_intended_and_says_so(tmp_path):
    run = mkrun(tmp_path)
    begin(run)
    outcome, rec = kyaction.reconcile(run, "ACT-1", lambda r: ("not_done", {"remote_head": C2}))
    assert outcome == "not_done" and rec["state"] == "INTENDED" and rec["result"] is None
    assert rec["reconciliations"][0]["outcome"] == "not_done"
    assert rec["reconciliations"][0]["detail"] == {"remote_head": C2}
    assert begin(run)[0] == "unfinished"            # a past "not done" is not a standing permission
    assert_schema("action", rec)


@pytest.mark.parametrize("observer", [
    lambda r: ("unknown", "github unreachable"),
    lambda r: (_ for _ in ()).throw(RuntimeError("boom")),          # an observer that raises
    lambda r: "done",                                                # not a pair
    lambda r: ("done", "yes"),                                       # "done" without an observed result object
    lambda r: ("finished", {}),                                      # not one of the three outcomes
    lambda r: None,
])
def test_an_unknown_reconciliation_never_becomes_done_and_never_permits_a_retry(tmp_path, observer):
    run = mkrun(tmp_path)
    begin(run)
    outcome, rec = kyaction.reconcile(run, "ACT-1", observer)
    assert outcome == "unknown"
    assert rec["state"] == "INTENDED" and rec["result"] is None and rec["completed_at"] is None
    assert rec["reconciliations"][-1]["outcome"] == "unknown"
    assert begin(run)[0] == "unfinished"
    with pytest.raises(kyaction.ActionRefused):
        kyaction.retry(run, "ACT-1")                    # no blind retry: retry exists only for FAILED
    assert kyaction.load(run, "ACT-1")["state"] == "INTENDED"


def test_repeated_identical_reconciliations_are_counted_not_accumulated(tmp_path):
    run = mkrun(tmp_path)
    begin(run)
    for _ in range(5):
        kyaction.reconcile(run, "ACT-1", lambda r: ("unknown", "tracker down"))
    rec = kyaction.reconcile(run, "ACT-1", lambda r: ("not_done", "absent"))[1]
    assert [(r["outcome"], r["count"]) for r in rec["reconciliations"]] == [("unknown", 5), ("not_done", 1)]
    assert_schema("action", rec)


def test_a_failed_record_is_not_reconciled_into_anything_else(tmp_path):
    run = mkrun(tmp_path)
    begin(run)
    kyaction.fail(run, "ACT-1", {"error": "x"})
    outcome, rec = kyaction.reconcile(run, "ACT-1", lambda r: ("done", {"surprise": True}))
    assert outcome == "failed" and rec["state"] == "FAILED" and "reconciliations" not in rec


def test_unfinished_lists_intended_records_oldest_first(tmp_path):
    run = mkrun(tmp_path)
    assert kyaction.unfinished(run) == []                       # no actions directory yet: nothing recorded
    for aid in ("ACT-c", "ACT-a", "ACT-b", "ACT-done", "ACT-failed"):
        begin(run, aid)
    for aid, when in (("ACT-c", "2026-10-11T10:00:00Z"), ("ACT-a", "2026-10-11T12:00:00Z"),
                      ("ACT-b", "2026-10-11T11:00:00Z")):
        p = run / "actions" / (aid + ".json")
        doc = json.loads(p.read_text())
        doc["created_at"] = when
        p.write_text(json.dumps(doc))
    kyaction.complete(run, "ACT-done", {"ok": True})
    kyaction.fail(run, "ACT-failed", {"error": "x"})
    assert [r["action_id"] for r in kyaction.unfinished(run)] == ["ACT-c", "ACT-b", "ACT-a"]


def test_an_unreadable_record_is_never_silently_treated_as_finished(tmp_path):
    run = mkrun(tmp_path)
    begin(run, "ACT-ok")
    (run / "actions" / "ACT-torn.json").write_text('{"schema": "ky.action/1", "action_id": "ACT-torn", "sta')
    (run / "actions" / "ACT-other.json").write_text(json.dumps({"schema": "ky.action/1", "action_id": "ACT-x",
                                                                 "state": "DONE"}))
    with pytest.raises(kyaction.ActionUnreadable) as e:
        kyaction.unfinished(run)
    assert "ACT-torn.json" in str(e.value) and "ACT-other.json" in str(e.value)
    assert [r["action_id"] for r in kyaction.unfinished(run, strict=False)] == ["ACT-ok"]
    records, problems = kyaction.scan(run)
    assert [r["action_id"] for r in records] == ["ACT-ok"] and len(problems) == 2
    with pytest.raises(kyaction.ActionUnreadable):
        begin(run, "ACT-torn")                       # an existing unreadable record is never replaced
    assert (run / "actions" / "ACT-torn.json").read_text().endswith('"sta')


@pytest.mark.parametrize("aid", ["", "-leading", "has space", "a/b", "../x", "é", "x" * 161, "x\n", None, 7])
def test_action_ids_are_restricted(tmp_path, aid):
    run = mkrun(tmp_path)
    with pytest.raises(kyaction.ActionInvalid):
        begin(run, aid)
    assert not (run / "actions").exists() or list((run / "actions").iterdir()) == []


def test_action_ids_accept_the_documented_alphabet(tmp_path):
    run = mkrun(tmp_path)
    for aid in ("A", "ACT-KW01-planner-state-migration", "SD-20261011T220000Z-1.execute", "a:b_c.d-e", "x" * 160,
                "ACT-launch-" + "j" * 128):          # the bootstrap supervisor's id for its longest job id (128)
        assert begin(run, aid)[0] == "new"
        assert_schema("action", kyaction.load(run, aid))


@pytest.mark.parametrize("field,value", [
    ("inputs", {"when": object()}), ("inputs", {"x": {1, 2}}), ("inputs", [1]), ("inputs", None),
    ("inputs", {"x": float("inf")}), ("inputs", {"t": (1, 2)}), ("inputs", {1: "non-string key"}),
    ("target", {"p": Path("/x")}), ("target", "origin"),
    ("actor", {"role": "planner", "holder_kind": "cockpit"}),
    ("actor", {"role": "planner", "holder_kind": "robot", "session_id": "s"}),
    ("actor", {"role": "", "holder_kind": "cockpit", "session_id": "s"}),
    ("actor", {"role": "planner", "holder_kind": "controller", "controller_id": 7}),
    ("actor", {"role": "planner", "holder_kind": "cockpit", "session_id": "s", "extra": 1}),
    ("kind", ""), ("kind", None),
])
def test_begin_refuses_what_it_cannot_record_faithfully(tmp_path, field, value):
    run = mkrun(tmp_path)
    kw = {"inputs": {"a": 1}, "target": {"t": 1}, "actor": ACTOR, "kind": "push"}
    kw[field] = value
    with pytest.raises(kyaction.ActionInvalid):
        kyaction.begin(run, "ACT-1", kw["kind"], kw["actor"], kw["inputs"], kw["target"], "x")
    assert not (run / "actions" / "ACT-1.json").exists()


def test_a_controller_actor_is_accepted(tmp_path):
    run = mkrun(tmp_path)
    actor = {"role": "veto", "holder_kind": "controller", "controller_id": "ctl-1"}
    assert begin(run, actor=actor)[1]["actor"] == actor


@pytest.mark.parametrize("change", [{"inputs": {"branch": "other"}}, {"target": {"remote": "elsewhere"}},
                                    {"kind": "merge"}])
def test_an_action_id_reused_for_a_different_action_is_a_conflict(tmp_path, change):
    run = mkrun(tmp_path)
    begin(run)
    kyaction.complete(run, "ACT-1", {"ok": True})
    with pytest.raises(kyaction.ActionConflict):          # never "done" for a side effect that was not this one
        begin(run, **change)


def test_the_read_only_verbs_write_nothing(tmp_path):
    run = mkrun(tmp_path)
    begin(run, "ACT-a")
    begin(run, "ACT-b")
    kyaction.complete(run, "ACT-b", {"ok": True})
    env = dict(SUB_ENV, KY_RUN=str(run))
    before = tree(run, skip=())

    def cli(*args):
        return subprocess.run([PY, str(FLEET / "kyaction.py"), *args], capture_output=True, text=True, env=env)

    listed = cli("list")
    assert listed.returncode == 0 and "ACT-a" in listed.stdout and "ACT-b" in listed.stdout
    unfinished = cli("unfinished")
    assert unfinished.returncode == 0 and "ACT-a" in unfinished.stdout and "ACT-b" not in unfinished.stdout
    shown = cli("show", "ACT-b")
    assert shown.returncode == 0 and json.loads(shown.stdout)["state"] == "DONE"
    assert cli("show", "ACT-none").returncode == 1
    assert cli("show", "../etc").returncode == 64
    assert cli("complete", "ACT-a").returncode == 64          # no verb completes a record named on the command line
    assert cli("complete").returncode == 75                   # … and the job verbs need the caller's own namespace
    assert cli().returncode == 64
    assert tree(run, skip=()) == before
    (run / "actions" / "ACT-torn.json").write_text("{")
    bad = cli("unfinished")
    assert bad.returncode == 1 and "ACT-torn.json" in bad.stderr and "ACT-a" in bad.stdout


# ── the lock helper every module shares (§4a.6: mkdir-atomic, owner.json, a second actor skips) ──

def test_lock_is_exclusive_records_its_owner_and_is_released_by_its_owner_only(tmp_path):
    run = mkrun(tmp_path)
    logged = []
    lock = kyaction.acquire_lock(run, "decision.SD-1", "me")
    assert lock is not None
    owner = json.loads((run / "locks" / "decision.SD-1" / "owner.json").read_text())
    assert sorted(owner) == ["acquired_at", "pgid", "pid", "process_start", "session_or_run_id"]
    assert owner["session_or_run_id"] == "me" and owner["pid"] == os.getpid() and owner["process_start"]
    assert kyaction.acquire_lock(run, "decision.SD-1", "another", log=logged.append) is None       # skips …
    assert logged and "decision.SD-1" in logged[0]                                                  # … and logs
    assert kyaction.acquire_lock(run, "decision.SD-2", "another") is not None                       # per-id
    assert kyaction.release_lock(lock) is True
    assert not (run / "locks" / "decision.SD-1").exists()
    again = kyaction.acquire_lock(run, "decision.SD-1", "another")
    assert again is not None
    assert kyaction.release_lock(lock) is False            # the former owner cannot release the new owner's lock
    assert (run / "locks" / "decision.SD-1").is_dir()


def test_a_lock_whose_owner_process_is_gone_is_taken_over(tmp_path):
    run = mkrun(tmp_path)
    hold(run, "decision.SD-1", "crashed", pid=dead_pid(), start="Sun Oct 11 22:00:00 2026")
    lock = kyaction.acquire_lock(run, "decision.SD-1", "me")
    assert lock is not None
    assert json.loads((run / "locks" / "decision.SD-1" / "owner.json").read_text())["session_or_run_id"] == "me"


def owner_of(run, name):
    return json.loads((Path(run) / "locks" / name / "owner.json").read_text())


def test_a_live_owner_is_skipped_and_a_reused_pid_is_positively_gone(tmp_path):
    run = mkrun(tmp_path)
    hold(run, "decision.SD-1", "alive")                                    # this very process: alive, same start
    assert kyaction.acquire_lock(run, "decision.SD-1", "me") is None
    assert owner_of(run, "decision.SD-1")["session_or_run_id"] == "alive"
    hold(run, "decision.SD-3", "reused-pid", start="Thu Jan  1 00:00:00 1970")     # same pid, another process
    assert kyaction.acquire_lock(run, "decision.SD-3", "me") is not None


# ── ruling R2 (CT-03): liveness has three answers, and only "positively gone" is ever taken over ──

def test_process_matches_has_three_answers(monkeypatch):
    me = kyaction.self_identity()
    assert kyaction.process_matches(me["pid"], me["process_start"]) is True
    assert kyaction.process_matches(me["pid"], "Thu Jan  1 00:00:00 1970") is False       # positively another process
    assert kyaction.process_matches(dead_pid(), me["process_start"]) is False             # positively no such process
    assert kyaction.process_matches(me["pid"], "") is None                                 # alive, not comparable
    assert kyaction.process_matches(me["pid"], None) is None
    assert kyaction.process_matches(me["pid"], "the day before yesterday") is None
    for pid in (None, "", str(me["pid"]), float(me["pid"]), True, 0, -1, [me["pid"]]):     # missing / not a pid
        assert kyaction.process_matches(pid, me["process_start"]) is None, pid
    no_ps(monkeypatch)                                                                     # ps cannot be started
    assert kyaction.process_matches(me["pid"], me["process_start"]) is None
    assert kyaction.process_matches(dead_pid(), me["process_start"]) is None               # … so nothing is "gone"


def test_a_zombie_is_positively_gone_even_with_its_own_start_identity(monkeypatch):
    """C2-08: an exited process nobody has reaped still answers `ps` under its pid and its start identity."""
    p = subprocess.Popen([PY, "-c", "pass"])              # exits at once; not reaped until wait() below
    try:
        probe, deadline = None, time.time() + 30
        while time.time() < deadline:
            probe = kyaction.ps_probe(p.pid)
            if probe and probe[0] == "alive" and probe[1].startswith("Z"):
                break
            time.sleep(0.02)
        assert probe and probe[0] == "alive" and probe[1].startswith("Z"), probe       # ps still lists it …
        assert kyaction.process_matches(p.pid, probe[2]) is False                      # … and it is gone all the same
    finally:
        p.wait()
    me = kyaction.self_identity()                         # the same rule on a ps answer written out here
    monkeypatch.setattr(kyaction, "_ps", lambda pid, columns: (0, "Z+ " + me["process_start"], ""))
    assert kyaction.process_matches(me["pid"], me["process_start"]) is False
    monkeypatch.setattr(kyaction, "_ps", lambda pid, columns: (0, "S+ " + me["process_start"], ""))
    assert kyaction.process_matches(me["pid"], me["process_start"]) is True


@pytest.mark.parametrize("answer", ["timeout", "garbage", "error-text", "rc2"])
def test_a_ps_that_does_not_answer_properly_is_unknown_never_gone(monkeypatch, answer):
    class Result:
        returncode, stdout, stderr = {"garbage": (0, "S\n", ""), "error-text": (1, "", "ps: cannot allocate\n"),
                                      "rc2": (2, "", "")}.get(answer, (0, "", ""))

    def fake_run(argv, **kw):
        if answer == "timeout":
            raise subprocess.TimeoutExpired(argv, kw.get("timeout"))
        return Result()

    monkeypatch.setattr(kyaction.subprocess, "run", fake_run)
    assert kyaction.ps_probe(4242) is None and kyaction.process_matches(4242, "Mon Oct 12 02:45:03 2026") is None


@pytest.mark.parametrize("why", ["ps-unavailable", "pid-missing", "pid-not-an-integer", "pid-a-float", "pid-true",
                                 "start-not-comparable", "owner-unreadable", "owner-not-an-object", "ownerless",
                                 "ownerless-and-old"])
def test_a_lock_whose_owner_cannot_be_judged_is_never_taken_over(tmp_path, monkeypatch, why):
    run = mkrun(tmp_path)
    name, d = "veto", run / "locks" / "veto"
    hold(run, name, "the-live-owner")                       # really alive: this very process
    owner = owner_of(run, name)
    if why == "ps-unavailable":
        no_ps(monkeypatch)                                  # the reviewer's probe: a live owner's `veto` lock was taken
    elif why == "pid-missing":
        del owner["pid"]
    elif why == "pid-not-an-integer":
        owner["pid"] = str(owner["pid"])
    elif why == "pid-a-float":
        owner["pid"] = float(owner["pid"])
    elif why == "pid-true":
        owner["pid"] = True
    elif why == "start-not-comparable":
        owner["process_start"] = ""
    (d / "owner.json").write_text("{" if why == "owner-unreadable" else "[]" if why == "owner-not-an-object"
                                  else json.dumps(owner))
    if why.startswith("ownerless"):
        (d / "owner.json").unlink()                         # a bare directory: some other program's, or nobody's
        if why == "ownerless-and-old":
            os.utime(d, (time.time() - 86400, time.time() - 86400))       # age is no evidence
    before, logged = tree(run, skip=()), []
    with pytest.raises(kyaction.LockUnknown) as e:
        kyaction.acquire_lock(run, name, "me", log=logged.append)
    assert e.value.name == name and e.value.detail and isinstance(e.value, kyaction.ActionError)
    assert not isinstance(e.value, kyaction.LockBusy)       # busy is "come back later"; unknown needs attention
    assert tree(run, skip=()) == before and d.is_dir() and logged and "not taken over" in logged[0]
    assert sorted(q.name for q in (run / "locks").iterdir()) == ["veto"]            # no staging directory left behind


def test_an_unknown_owner_is_waited_for_and_then_reported_not_taken(tmp_path, monkeypatch):
    run = mkrun(tmp_path)
    hold(run, "action.ACT-1", "another", start="")
    begin(run)
    monkeypatch.setattr(kyaction, "LOCK_WAIT_S", 0.3)
    started = time.monotonic()
    with pytest.raises(kyaction.LockUnknown):
        kyaction.complete(run, "ACT-1", {"ok": True})
    assert time.monotonic() - started >= 0.3 and kyaction.load(run, "ACT-1")["state"] == "INTENDED"


def test_a_lock_is_put_in_place_complete_with_its_owner(tmp_path, monkeypatch):
    """Acquisition is atomic WITH its owner: what appears at the lock path already holds owner.json."""
    run = mkrun(tmp_path)
    real, seen = kyaction.rename_exclusive, []

    def watching(src, dst):
        seen.append((Path(dst).exists(), json.loads((Path(src) / "owner.json").read_text())["session_or_run_id"]))
        return real(src, dst)

    monkeypatch.setattr(kyaction, "rename_exclusive", watching)
    lock = kyaction.acquire_lock(run, "decision.SD-1", "me")
    assert seen == [(False, "me")] and owner_of(run, "decision.SD-1")["pid"] == os.getpid()
    assert sorted(q.name for q in (run / "locks").iterdir()) == ["decision.SD-1"]
    assert kyaction.release_lock(lock) and list((run / "locks").iterdir()) == []


def test_the_exclusive_rename_never_replaces_what_is_there(tmp_path):
    src, dst = tmp_path / "src", tmp_path / "dst"
    for case in ("empty-directory", "full-directory", "file"):
        src.mkdir()
        (src / "owner.json").write_text("{}")
        if case == "file":
            dst.write_text("x")
        else:
            dst.mkdir()
            if case == "full-directory":
                (dst / "owner.json").write_text('{"theirs": true}')
        with pytest.raises(FileExistsError):
            kyaction.rename_exclusive(src, dst)
        assert (src / "owner.json").exists(), case          # nothing moved
        assert dst.is_file() or sorted(q.name for q in dst.iterdir()) == (
            ["owner.json"] if case == "full-directory" else []), case
        shutil.rmtree(src)
        shutil.rmtree(dst) if dst.is_dir() else dst.unlink()
    src.mkdir()
    kyaction.rename_exclusive(src, dst)
    assert dst.is_dir() and not src.exists()


def test_an_empty_directory_that_appears_at_the_last_moment_is_not_replaced(tmp_path, monkeypatch):
    """rename(2) would replace an empty directory; the kernel's exclusive rename does not."""
    if kyaction._exclusive_rename() is None:
        pytest.skip("no exclusive rename on this platform: the documented fallback applies")
    run = mkrun(tmp_path)
    d = run / "locks" / "decision.SD-1"
    real = kyaction.rename_exclusive

    def raced(src, dst):
        if not d.exists():
            d.mkdir()                                       # another program's mkdir lands just before our rename
        return real(src, dst)

    monkeypatch.setattr(kyaction, "rename_exclusive", raced)
    with pytest.raises(kyaction.LockUnknown):
        kyaction.acquire_lock(run, "decision.SD-1", "me")
    assert d.is_dir() and list(d.iterdir()) == []
    monkeypatch.undo()
    # and it is the KERNEL that refuses, not a look beforehand: here no look could have seen the directory
    src = tmp_path / "staged"
    src.mkdir()
    (src / "owner.json").write_text("{}")
    monkeypatch.setattr(kyaction.os.path, "lexists", lambda path: False)
    try:
        with pytest.raises(FileExistsError):
            kyaction.rename_exclusive(src, d)
    finally:
        monkeypatch.undo()
    assert list(d.iterdir()) == [] and (src / "owner.json").exists()


def test_takeover_is_verified_after_the_rename(tmp_path, monkeypatch):
    """Two contenders, one stale lock (SUP-01's interleaving): B has judged the stale owner gone; before B moves
    the lock aside, A has taken it over and holds it. What B then finds in its grave is A's lock, not the one it
    judged: B puts it back and takes nothing."""
    run = mkrun(tmp_path)
    d = run / "locks" / "decision.SD-1"
    hold(run, "decision.SD-1", "crashed", pid=dead_pid(), start="Sun Oct 11 22:00:00 2026")
    stale, real = owner_of(run, "decision.SD-1"), kyaction.read_json
    a_owner = dict(kyaction.self_identity(), session_or_run_id="contender-A", acquired_at=kyaction.utc())
    state = {"reads": 0}

    def a_wins_between_the_look_and_the_rename(path):
        answer = real(path)
        if Path(path) == d / "owner.json":
            state["reads"] += 1
            if state["reads"] == 2:                         # B's look under the takeover guard still saw "crashed" …
                (d / "owner.json").write_text(json.dumps(a_owner))     # … and now it is A's lock
        return answer

    monkeypatch.setattr(kyaction, "read_json", a_wins_between_the_look_and_the_rename)
    logged = []
    assert kyaction.acquire_lock(run, "decision.SD-1", "contender-B", log=logged.append) is None
    assert state["reads"] >= 2 and owner_of(run, "decision.SD-1") == a_owner        # A's lock is back in place
    assert sorted(q.name for q in (run / "locks").iterdir()) == [".takeover.guard", "decision.SD-1"]
    assert not any("taken over" in line for line in logged) and stale["session_or_run_id"] == "crashed"


def test_release_removes_the_lock_in_one_step_and_only_its_own(tmp_path, monkeypatch):
    run = mkrun(tmp_path)
    lock = kyaction.acquire_lock(run, "decision.SD-1", "me")
    d = run / "locks" / "decision.SD-1"
    other = dict(owner_of(run, "decision.SD-1"), session_or_run_id="someone-else")
    (d / "owner.json").write_text(json.dumps(other))        # it changed hands (it never should; it is checked anyway)
    moved, real = [], os.rename
    with monkeypatch.context() as m:
        m.setattr(kyaction.os, "rename", lambda a, b: moved.append((a, b)) or real(a, b))
        assert kyaction.release_lock(lock) is False and owner_of(run, "decision.SD-1") == other
    assert moved == []                                      # another owner's lock is not even moved aside for a moment
    (d / "owner.json").write_text(json.dumps(dict(other, session_or_run_id="me")))
    assert kyaction.release_lock(lock) is True
    assert list((run / "locks").iterdir()) == []            # no ownerless directory, no grave


@pytest.mark.parametrize("child,taken", [
    (None, True),                                           # no job recorded: the dead owner's lock is free
    ("pending", False),                                     # written BEFORE the launch: there may be a job
    ("something", False), (7, False), ([], False),          # unidentified
    ({"pid": "self", "pgid": "self"}, False),               # the job's leader is alive
    ({"pid": "dead", "pgid": "self"}, False),               # leader gone, but its process group still has members
    ({"pid": "dead", "pgid": 0}, False), ({"pid": "dead"}, False), ({"pid": "dead", "pgid": True}, False),
    ({"pid": "dead", "pgid": "dead"}, True),                # leader positively gone AND killpg(pgid, 0) → ESRCH
])
def test_a_dead_owners_recorded_job_must_be_positively_gone_too(tmp_path, child, taken):
    run, me, gone = mkrun(tmp_path), kyaction.self_identity(), dead_pid()
    if isinstance(child, dict):
        child = {k: (me["pid"] if k == "pid" else me["pgid"]) if v == "self" else gone if v == "dead" else v
                 for k, v in child.items()}
        child["process_start"] = me["process_start"]
    hold(run, "planner", "CTL-PLANNER-crashed", pid=dead_pid(), start="Sun Oct 11 22:00:00 2026")
    d = run / "locks" / "planner"
    (d / "owner.json").write_text(json.dumps(dict(owner_of(run, "planner"), child=child)))
    if taken:
        assert kyaction.acquire_lock(run, "planner", "me") is not None
        assert owner_of(run, "planner")["session_or_run_id"] == "me"
    else:
        with pytest.raises(kyaction.LockUnknown):
            kyaction.acquire_lock(run, "planner", "me")
        assert owner_of(run, "planner")["session_or_run_id"] == "CTL-PLANNER-crashed"


def test_concurrent_takeover_of_a_stale_lock_has_one_winner(tmp_path):
    run = mkrun(tmp_path)
    hold(run, "decision.SD-1", "crashed", pid=dead_pid(), start="Sun Oct 11 22:00:00 2026")
    body = r"""
lock = kyaction.acquire_lock(sys.argv[4], "decision.SD-1", "p-%d" % os.getpid())
print("won" if lock else "skipped")
time.sleep(0.4)
"""
    codes, outs, errs = race(tmp_path, 6, snippet(body, run))
    assert codes == [0] * 6, errs
    assert sorted(outs) == ["skipped"] * 5 + ["won"]


@pytest.mark.parametrize("name", ["", "a/b", "..", "x y", ".hidden", "x" * 201])
def test_lock_names_are_restricted(tmp_path, name):
    with pytest.raises(kyaction.ActionInvalid):
        kyaction.acquire_lock(mkrun(tmp_path), name, "me")


def test_the_longest_action_id_still_has_a_lock_name(tmp_path):
    run = mkrun(tmp_path)
    begin(run, "x" * 160)
    assert kyaction.complete(run, "x" * 160, {"ok": True})["state"] == "DONE"       # lock `action.` + 160 characters


# ── CT-12: "unfinished" is not said while the first actor may still be in the middle of the effect ──

STARTER = r"""
import sys, time
sys.path.insert(0, sys.argv[1])
import kyaction
print(kyaction.begin(sys.argv[2], "ACT-1", "push", {"role": "planner", "holder_kind": "cockpit", "session_id": "first"},
                     {"branch": "b"}, {"remote": "origin", "head": "%s"}, "local head → remote head")[0], flush=True)
time.sleep(120)
""" % C1


def test_begin_says_in_progress_while_the_first_actors_process_is_alive(tmp_path, monkeypatch):
    run = mkrun(tmp_path)
    first = subprocess.Popen([PY, "-c", STARTER, str(FLEET), str(run)], stdout=subprocess.PIPE, text=True, env=SUB_ENV)
    try:
        assert first.stdout.readline().strip() == "new"
        rec = kyaction.load(run, "ACT-1")
        assert rec["process"]["pid"] == first.pid and rec["process"]["process_start"]
        status, seen = begin(run)                           # the first actor may be pushing right now
        assert status == "in_progress" and seen == rec
        with monkeypatch.context() as m:                    # and when it cannot be told, it still may be
            no_ps(m)
            assert begin(run)[0] == "in_progress"
    finally:
        first.kill()
        first.wait()
    assert begin(run)[0] == "unfinished"                    # positively gone: now it is reconciled, not waited for
    assert kyaction.load(run, "ACT-1") == rec               # asking changed nothing


def test_a_record_without_a_recorded_process_is_unfinished_to_a_second_caller(tmp_path):
    run = mkrun(tmp_path)
    begin(run)
    path = run / "actions" / "ACT-1.json"
    doc = json.loads(path.read_text())
    for process in (None, "absent"):                        # a job's record; a record from before this field existed
        if process == "absent":
            doc.pop("process", None)
        else:
            doc["process"] = process
        path.write_text(json.dumps(doc))
        assert begin(run)[0] == "unfinished"


def test_retry_names_the_process_that_reopened_the_record(tmp_path):
    run = mkrun(tmp_path)
    begin(run)
    kyaction.fail(run, "ACT-1", {"error": "x"})
    path = run / "actions" / "ACT-1.json"
    doc = json.loads(path.read_text())
    doc["process"] = {"pid": dead_pid(), "process_start": "Sun Oct 11 22:00:00 2026"}
    path.write_text(json.dumps(doc))
    again = kyaction.retry(run, "ACT-1")
    assert again["process"]["pid"] == os.getpid() and begin(run)[0] == "unfinished"
    assert_schema("action", again)


# ── ruling R8: records a model job writes about its own side effects ──

RUN_ID = JOB_ACTOR["run_id"]


def job_cli(run, verb, doc, run_id=RUN_ID, **env):
    environ = dict(SUB_ENV, KY_RUN=str(run), KY_ROLE="planner", KY_CONTROLLER_ID="CTL-PLANNER-1")
    if run_id is not None:
        environ["KY_RUN_ID"] = run_id
    environ.update(env)
    for name in [k for k, v in environ.items() if v is None]:
        del environ[name]
    return subprocess.run([PY, str(FLEET / "kyaction.py"), verb], capture_output=True, text=True, env=environ,
                          input=doc if isinstance(doc, str) else json.dumps(doc))


def job_begin_doc(aid=JOB_ID, **over):
    return dict({"action_id": aid, "kind": "git_push", "inputs": {"branch": "kalayantra/b0c"},
                 "target": {"remote": "origin", "ref": "refs/heads/kalayantra/b0c", "head": C1},
                 "intended_transition": "origin/kalayantra/b0c → local head"}, **over)


def test_a_job_actor_writes_only_inside_its_own_namespace(tmp_path):
    run = mkrun(tmp_path)
    status, rec = begin(run, JOB_ID, actor=JOB_ACTOR)
    assert status == "new" and rec["actor"] == JOB_ACTOR and rec["process"] is None
    assert_schema("action", rec)
    for aid in ("ACT-1", "CMD-000001-status-abc123", "SD-20261011T220000Z-1.publish", "LAUNCH-" + RUN_ID,
                "JOB-PLANNER-20261011T220000Z-02-push",     # the namespace of ANOTHER run (…Z-02), not a slug of this one
                "JOB-PLANNER-20261011T220000Z-", "JOB-PLANNER-20261011T220000Z-Push", "JOB-OTHER-RUN-push",
                "JOB-" + RUN_ID + "-" + "s" * 49):
        with pytest.raises(kyaction.ActionInvalid):
            begin(run, aid, actor=JOB_ACTOR)
        assert os.listdir(run / "actions") == [JOB_ID + ".json"], aid       # (a listing: the volume may fold case)
    with pytest.raises(kyaction.ActionInvalid):             # … and nobody else writes into it
        begin(run, "JOB-" + RUN_ID + "-pr", actor=ACTOR)
    with pytest.raises(kyaction.ActionInvalid):
        begin(run, "JOB-" + RUN_ID + "-pr", actor={"role": "planner", "holder_kind": "controller", "controller_id": "c"})
    assert sorted(q.name for q in (run / "actions").iterdir()) == [JOB_ID + ".json"]


@pytest.mark.parametrize("actor", [
    {"role": "planner", "holder_kind": "job", "controller_id": "c"},                           # no run
    {"role": "planner", "holder_kind": "job", "run_id": RUN_ID},                               # no controller
    {"role": "planner", "holder_kind": "job", "controller_id": "", "run_id": RUN_ID},
    {"role": "planner", "holder_kind": "job", "controller_id": "c", "run_id": "has space"},
    {"role": "planner", "holder_kind": "job", "controller_id": "c", "run_id": RUN_ID, "session_id": "s"},
    {"role": "planner", "holder_kind": "controller", "controller_id": "c", "run_id": RUN_ID},  # run_id is a job's
])
def test_a_malformed_job_actor_is_refused(tmp_path, actor):
    with pytest.raises(kyaction.ActionInvalid):
        begin(mkrun(tmp_path), JOB_ID, actor=actor)


def test_job_verbs_record_begin_then_the_observed_result(tmp_path):
    run = mkrun(tmp_path)
    r = job_cli(run, "begin", job_begin_doc())
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout) == {"action_id": JOB_ID, "status": "new", "state": "INTENDED"}
    rec = kyaction.load(run, JOB_ID)
    assert rec["actor"] == JOB_ACTOR and rec["kind"] == "git_push" and rec["process"] is None
    assert rec["target"]["head"] == C1
    assert_schema("action", rec)
    again = job_cli(run, "begin", job_begin_doc())          # asked again: exists — do NOT push
    assert again.returncode == 3 and json.loads(again.stdout)["status"] == "unfinished"
    done = job_cli(run, "complete", {"action_id": JOB_ID, "result": {"remote_head": C1}})
    assert done.returncode == 0 and json.loads(done.stdout) == {"action_id": JOB_ID, "state": "DONE"}
    rec = kyaction.load(run, JOB_ID)
    assert rec["state"] == "DONE" and rec["result"] == {"remote_head": C1}
    assert_schema("action", rec)
    assert job_cli(run, "complete", {"action_id": JOB_ID, "result": {"remote_head": C1}}).returncode == 0   # the same again
    assert job_cli(run, "complete", {"action_id": JOB_ID, "result": {"remote_head": C2}}).returncode == 1   # set once
    assert job_cli(run, "fail", {"action_id": JOB_ID, "result": {"error": "late"}}).returncode == 1
    third = job_cli(run, "begin", job_begin_doc())
    assert third.returncode == 3 and json.loads(third.stdout)["status"] == "done"
    assert kyaction.load(run, JOB_ID) == rec
    assert sorted(q.name for q in (run / "actions").iterdir()) == [JOB_ID + ".json"]          # nothing else, no temp file
    assert not (run / "locks" / ("action." + JOB_ID)).exists()


def test_job_verb_fail_records_what_did_not_happen(tmp_path):
    run = mkrun(tmp_path)
    assert job_cli(run, "begin", job_begin_doc()).returncode == 0
    r = job_cli(run, "fail", {"action_id": JOB_ID, "result": {"error": "remote rejected (non-fast-forward)"}})
    assert r.returncode == 0 and json.loads(r.stdout)["state"] == "FAILED"
    again = job_cli(run, "begin", job_begin_doc())
    assert again.returncode == 3 and json.loads(again.stdout)["status"] == "failed"
    assert job_cli(run, "begin", job_begin_doc(kind="git_push_force")).returncode == 1         # another action: conflict


def test_job_verbs_take_the_actor_from_stdin_or_the_environment(tmp_path):
    run = mkrun(tmp_path)
    full = dict(JOB_ACTOR, role="conductor", controller_id="CTL-CONDUCTOR-9")
    r = job_cli(run, "begin", job_begin_doc(actor=full), KY_ROLE=None, KY_CONTROLLER_ID=None)
    assert r.returncode == 0 and kyaction.load(run, JOB_ID)["actor"] == full
    short = job_cli(run, "begin", job_begin_doc("JOB-%s-pr" % RUN_ID, actor={"role": "planner", "controller_id": "C2"}),
                    KY_ROLE=None, KY_CONTROLLER_ID=None)
    assert short.returncode == 0 and kyaction.load(run, "JOB-%s-pr" % RUN_ID)["actor"]["controller_id"] == "C2"
    nobody = job_cli(run, "begin", job_begin_doc("JOB-%s-tag" % RUN_ID), KY_ROLE=None, KY_CONTROLLER_ID=None)
    assert nobody.returncode == 64 and "controller_id" in nobody.stderr
    assert not (run / "actions" / ("JOB-%s-tag.json" % RUN_ID)).exists()


@pytest.mark.parametrize("case,code", [
    ("no-run-id", 75), ("bad-run-id", 75), ("foreign-id", 75), ("controller-id", 75), ("other-runs-namespace", 75),
    ("actor-of-another-run", 75), ("actor-not-a-job", 75), ("not-json", 64), ("not-an-object", 64), ("missing-key", 64),
    ("extra-key", 64), ("inputs-not-an-object", 64), ("no-run-dir", 66), ("relative-run-dir", 66), ("run-unset", 66),
])
def test_job_begin_refuses_and_writes_nothing(tmp_path, case, code):
    run = mkrun(tmp_path)
    doc, kw = job_begin_doc(), {}
    if case == "no-run-id":
        kw["run_id"] = None
    elif case == "bad-run-id":
        kw["run_id"] = "../x"
    elif case == "foreign-id":
        doc["action_id"] = "SD-20261011T220000Z-1.publish"              # the veto handler's own memory
    elif case == "controller-id":
        doc["action_id"] = "LAUNCH-" + RUN_ID
    elif case == "other-runs-namespace":
        doc["action_id"] = "JOB-PLANNER-20261011T220000Z-02-push"
    elif case == "actor-of-another-run":
        doc["actor"] = dict(JOB_ACTOR, run_id="PLANNER-20261011T230000Z")
    elif case == "actor-not-a-job":
        doc["actor"] = {"role": "planner", "holder_kind": "controller", "controller_id": "CTL-PLANNER-1"}
    elif case == "not-json":
        doc = "{not json"
    elif case == "not-an-object":
        doc = [1, 2]
    elif case == "missing-key":
        del doc["target"]
    elif case == "extra-key":
        doc["state"] = "DONE"
    elif case == "inputs-not-an-object":
        doc["inputs"] = "kalayantra/b0c"
    elif case == "no-run-dir":
        kw["KY_RUN"] = str(tmp_path / "no-such-run")
    elif case == "relative-run-dir":
        kw["KY_RUN"] = "run"
    elif case == "run-unset":
        kw.update(KY_RUN=None, KY_ROOT=str(tmp_path))                   # never a guessed default for a writing verb
    r = job_cli(run, "begin", doc, **kw)
    assert r.returncode == code, (r.returncode, r.stdout, r.stderr)
    assert r.stdout == "" and "REFUSED" in r.stderr
    assert not (run / "actions").exists() and not (tmp_path / "no-such-run").exists()


def test_a_job_cannot_finish_or_adopt_a_record_that_is_not_its_own(tmp_path):
    run = mkrun(tmp_path)
    begin(run, "ACT-1")                                                 # the cockpit's
    begin(run, "SD-20261011T220000Z-1.publish", actor={"role": "veto", "holder_kind": "controller", "controller_id": "v"})
    other_run = "PLANNER-20261011T230000Z"
    begin(run, "JOB-%s-push" % other_run, actor=dict(JOB_ACTOR, run_id=other_run))
    before = tree(run, skip=())
    for aid in ("ACT-1", "SD-20261011T220000Z-1.publish", "JOB-%s-push" % other_run):
        for verb in ("complete", "fail"):
            r = job_cli(run, verb, {"action_id": aid, "result": {"ok": True}})
            assert r.returncode == 75, (aid, verb, r.stderr)
    # a record under this run's id that a job of this run did not write (planted by hand) is not adopted either
    planted = dict(kyaction.load(run, "ACT-1"), action_id=JOB_ID)
    (run / "actions" / (JOB_ID + ".json")).write_text(json.dumps(planted))
    assert job_cli(run, "complete", {"action_id": JOB_ID, "result": {"ok": True}}).returncode == 75
    assert job_cli(run, "begin", job_begin_doc()).returncode == 75
    (run / "actions" / (JOB_ID + ".json")).unlink()
    assert job_cli(run, "complete", {"action_id": JOB_ID, "result": {"ok": True}}).returncode == 1     # no such record
    assert job_cli(run, "complete", {"action_id": JOB_ID, "result": "ok"}).returncode in (1, 64)
    assert tree(run, skip=()) == before


def test_a_controller_finds_and_reconciles_exactly_its_runs_job_records(tmp_path):
    """What kyloop does after a child has exited (ruling R8): this run's unfinished JOB-<run_id>-* records."""
    run = mkrun(tmp_path)
    assert job_cli(run, "begin", job_begin_doc()).returncode == 0                               # left unfinished
    assert job_cli(run, "begin", job_begin_doc("JOB-%s-pr" % RUN_ID, kind="pr_open")).returncode == 0
    assert job_cli(run, "complete", {"action_id": "JOB-%s-pr" % RUN_ID, "result": {"pr": 3441}}).returncode == 0
    later = RUN_ID + "-02"                                                                      # the next run's records
    assert job_cli(run, "begin", job_begin_doc("JOB-%s-push" % later), run_id=later).returncode == 0
    begin(run, "LAUNCH-" + RUN_ID, actor={"role": "planner", "holder_kind": "controller", "controller_id": "CTL-PLANNER-1"})
    (run / "actions" / ("JOB-%s-torn.json" % RUN_ID)).write_text('{"schema": "ky.action/1", "action_id": "JOB-')
    (run / "actions" / "quarantine").mkdir()                                                    # kyloop's; never scanned
    (run / "actions" / "quarantine" / "JOB-old.json").write_text("{")
    assert sorted(r["action_id"] for r in kyaction.job_records(run, RUN_ID)) == ["JOB-%s-pr" % RUN_ID, JOB_ID]
    assert [r["action_id"] for r in kyaction.job_records(run, RUN_ID, state="INTENDED")] == [JOB_ID]
    assert [r["action_id"] for r in kyaction.job_records(run, later)] == ["JOB-%s-push" % later]
    assert [name for name, _ in kyaction.unreadable(run)] == ["JOB-%s-torn.json" % RUN_ID]
    assert kyaction.job_slug(JOB_ID, RUN_ID) == "push" and kyaction.job_slug("JOB-%s-push" % later, RUN_ID) is None
    outcome, rec = kyaction.reconcile(run, JOB_ID, lambda r: ("done", {"remote_head": r["target"]["head"]}),
                                      by="CTL-PLANNER-1")                                       # e.g. git ls-remote equality
    assert outcome == "done" and rec["state"] == "DONE" and rec["reconciliations"][0]["by"] == "CTL-PLANNER-1"
    assert_schema("action", rec)


# ═════════════════════════════════════════════ kycommands ═════════════════════════════════════════════

VALID = [
    ("planner", "status", {}), ("veto", "veto", {"decision_id": "SD-20261011T220000Z-1"}),
    ("planner", "decide", {"awaiting_id": "AW-20261011T215900Z-item-1", "answer": "option a"}),
    ("campaign", "pause", {}), ("campaign", "resume", {}), ("conductor", "priority", {"item": "K7-3"}),
    ("dispatcher", "builders", {"n": 5}), ("dispatcher", "verifiers", {"n": 1}),
    ("planner", "loops", {"op": "stop", "loop": "conductor"}), ("dispatcher", "loops", {"op": "status", "loop": "all"}),
    ("conductor", "approve-window", {"id": "W-2"}), ("planner", "handoff", {}),
]


def stems(run):
    return sorted(p.name[:-5] for p in (run / "commands").iterdir() if p.name.endswith(".json"))


@pytest.mark.parametrize("role,command,args", VALID)
def test_submit_writes_one_queued_command(tmp_path, role, command, args):
    run = mkrun(tmp_path)
    cid = kycommands.submit(run, role, command, args, COCKPIT)
    (stem,) = stems(run)
    assert stem.endswith("-" + cid) and len(stem) == len("20261011T220000Z-") + len(cid)
    assert time.strptime(stem[:16], "%Y%m%dT%H%M%SZ")
    doc = json.loads((run / "commands" / (stem + ".json")).read_text(encoding="utf-8"))
    me = kyaction.self_identity()                           # CT-06: the submitting process is recorded with the session
    assert doc == {"schema": "ky.command/1", "id": cid, "created_at": doc["created_at"],
                   "from": dict(COCKPIT, pid=os.getpid(), process_start=me["process_start"]),
                   "role": role, "command": command, "args": args, "state": "QUEUED", "applied_by": None,
                   "applied_at": None, "result": None}
    assert me["process_start"] and kyaction.process_matches(doc["from"]["pid"], doc["from"]["process_start"]) is True
    assert_schema("command", doc)
    assert [d["id"] for d in kycommands.pending(run, role)] == [cid]


@pytest.mark.parametrize("role,command,args,from_", [
    ("planner", "explode", {}, COCKPIT),                                   # unknown command
    ("owner", "status", {}, COCKPIT),                                      # unknown role
    ("planner", "status", {"verbose": True}, COCKPIT),                     # status takes no arguments
    ("campaign", "pause", {"minutes": 5}, COCKPIT),
    ("veto", "veto", {}, COCKPIT), ("veto", "veto", {"decision_id": "D-41"}, COCKPIT),
    ("veto", "veto", {"decision_id": "SD-20261011T220000Z-1", "x": 1}, COCKPIT),
    ("planner", "veto", {"decision_id": "SD-20261011T220000Z-1"}, COCKPIT),    # a veto goes to the veto role
    ("planner", "pause", {}, COCKPIT), ("conductor", "resume", {}, COCKPIT),   # pause/resume are campaign-level
    ("planner", "decide", {"awaiting_id": "AW-20261011T215900Z-x"}, COCKPIT),
    ("planner", "decide", {"awaiting_id": "nope", "answer": "a"}, COCKPIT),
    ("planner", "decide", {"awaiting_id": "AW-20261011T215900Z-x", "answer": ""}, COCKPIT),
    ("conductor", "priority", {"item": ""}, COCKPIT), ("conductor", "priority", {}, COCKPIT),
    ("dispatcher", "builders", {"n": 0}, COCKPIT), ("dispatcher", "builders", {"n": "3"}, COCKPIT),
    ("dispatcher", "builders", {"n": True}, COCKPIT), ("dispatcher", "builders", {"n": 2.0}, COCKPIT),
    ("dispatcher", "verifiers", {"n": -1}, COCKPIT), ("dispatcher", "verifiers", {}, COCKPIT),
    ("planner", "loops", {"op": "restart", "loop": "planner"}, COCKPIT),
    ("planner", "loops", {"op": "stop"}, COCKPIT), ("planner", "loops", {"op": "stop", "loop": "tracker"}, COCKPIT),
    ("conductor", "approve-window", {}, COCKPIT), ("conductor", "approve-window", {"id": ""}, COCKPIT),
    ("planner", "status", [], COCKPIT), ("planner", "status", None, COCKPIT),
    ("planner", "status", {}, {"kind": "surrogate", "session_id": "s"}),    # only the cockpit submits
    ("planner", "status", {}, {"kind": "cockpit"}), ("planner", "status", {}, {"kind": "cockpit", "session_id": ""}),
    ("planner", "status", {}, "sess-1"),
    ("planner", "status", {}, dict(COCKPIT, pid=1, process_start="Thu Jan  1 00:00:00 1970")),   # nobody names a pid:
    ("planner", "status", {}, dict(COCKPIT, pid=os.getpid())),                                   # submit records its own
    ("planner", "status", {}, dict(COCKPIT, host="elsewhere")),
])
def test_submit_refuses_malformed_commands(tmp_path, role, command, args, from_):
    run = mkrun(tmp_path)
    with pytest.raises(kycommands.CommandInvalid):
        kycommands.submit(run, role, command, args, from_)
    assert not (run / "commands").exists() or stems(run) == []


def test_filename_order_is_submission_order_even_within_one_second(tmp_path):
    run = mkrun(tmp_path)
    ids = [kycommands.submit(run, "dispatcher", "builders", {"n": n}, COCKPIT) for n in range(1, 31)]
    assert [d["id"] for d in kycommands.pending(run, "dispatcher")] == ids
    assert [d["args"]["n"] for d in kycommands.pending(run, "dispatcher")] == list(range(1, 31))
    assert len(set(ids)) == 30


def test_a_new_command_sorts_after_a_queue_whose_newest_entry_is_ahead_of_the_clock(tmp_path):
    run = mkrun(tmp_path)
    first = kycommands.submit(run, "campaign", "pause", {}, COCKPIT)
    (old,) = list((run / "commands").iterdir())
    ahead = "29990101T000000Z-" + first                       # as if the wall clock had since stepped back
    old.rename(run / "commands" / (ahead + ".json"))
    second = kycommands.submit(run, "campaign", "resume", {}, COCKPIT)
    third = kycommands.submit(run, "campaign", "pause", {}, COCKPIT)
    assert [d["id"] for d in kycommands.pending(run, "campaign")] == [first, second, third]


def test_pending_is_per_role_and_only_queued(tmp_path):
    run = mkrun(tmp_path)
    a = kycommands.submit(run, "planner", "status", {}, COCKPIT)
    b = kycommands.submit(run, "conductor", "status", {}, COCKPIT)
    c = kycommands.submit(run, "planner", "handoff", {}, COCKPIT)
    hold(run, "planner", "ctl-p")
    assert kycommands.apply(run, a, "ctl-p", lambda cmd: {"ok": True})[0] == "applied"
    assert [d["id"] for d in kycommands.pending(run, "planner")] == [c]
    assert [d["id"] for d in kycommands.pending(run, "conductor")] == [b]
    assert kycommands.pending(run, "veto") == []
    with pytest.raises(kycommands.CommandInvalid):
        kycommands.pending(run, "owner")


def test_apply_by_the_fenced_owner_marks_the_command_applied_exactly_once(tmp_path):
    run = mkrun(tmp_path)
    cid = kycommands.submit(run, "dispatcher", "builders", {"n": 5}, COCKPIT)
    hold(run, "dispatcher", "ctl-d")
    seen = []

    def handler(cmd):
        seen.append((cmd["command"], cmd["args"]))
        return {"builders": 5}

    status, doc = kycommands.apply(run, cid, "ctl-d", handler)
    assert status == "applied" and seen == [("builders", {"n": 5})]
    assert doc["state"] == "APPLIED" and doc["result"] == {"builders": 5} and doc["applied_at"]
    assert doc["applied_by"] == {"role": "dispatcher", "holder_kind": "controller", "controller_id": "ctl-d"}
    assert_schema("command", doc)
    on_disk = json.loads((run / "commands" / (stems(run)[0] + ".json")).read_text())
    assert on_disk == doc
    status, again = kycommands.apply(run, cid, "ctl-d", handler)
    assert status == "already_applied" and again == doc and len(seen) == 1         # never applied twice
    assert not (run / "locks" / ("command." + cid)).exists()                        # the command lock is released
    assert kyaction.load(run, "CMD-" + cid)["state"] == "DONE"


def test_the_recorded_origin_of_a_command_is_shape_checked_not_trusted(tmp_path):
    """CT-06: `from` is a record of origin. A hand-written command with a well-formed `from` is accepted like any
    other — that only the cockpit submits is a convention (module docstring) — while a malformed one is not."""
    run = mkrun(tmp_path)
    (run / "commands").mkdir()
    base = {"schema": "ky.command/1", "created_at": "2026-10-11T22:00:00Z", "role": "planner", "command": "status",
            "args": {}, "state": "QUEUED", "applied_by": None, "applied_at": None, "result": None}
    senders = {"plain": COCKPIT, "recorded": dict(COCKPIT, pid=4242, process_start="Mon Oct 12 02:45:03 2026"),
               "no-start": dict(COCKPIT, pid=4242, process_start=None),
               "bad-pid": dict(COCKPIT, pid="4242"), "bad-start": dict(COCKPIT, pid=4242, process_start=7),
               "extra": dict(COCKPIT, tty="ttys001")}
    for n, (name, sender) in enumerate(sorted(senders.items())):
        doc = dict(base, id="by-hand-" + name, **{"from": sender})
        (run / "commands" / ("20261011T22000%dZ-by-hand-%s.json" % (n, name))).write_text(json.dumps(doc))
        assert (schema_errors("command", doc) == []) == (name in ("plain", "recorded", "no-start")), name
    invalid = {e["doc"]["id"][8:]: bool(e["invalid"]) for e in kycommands.scan(run)[0]}
    assert invalid == {"plain": False, "recorded": False, "no-start": False, "bad-pid": True, "bad-start": True,
                       "extra": True}
    assert "CONVENTION" in kycommands.__doc__ and "not an enforced boundary" in kycommands.__doc__


def test_a_cockpit_holding_the_role_lock_may_apply(tmp_path):
    run = mkrun(tmp_path)
    cid = kycommands.submit(run, "planner", "handoff", {}, COCKPIT)
    hold(run, "planner", "sess-1")
    status, doc = kycommands.apply(run, cid, {"holder_kind": "cockpit", "session_id": "sess-1"}, lambda c: {})
    assert status == "applied"
    assert doc["applied_by"] == {"role": "planner", "holder_kind": "cockpit", "session_id": "sess-1"}
    assert_schema("command", doc)


@pytest.mark.parametrize("applier", [
    {"holder_kind": "job", "controller_id": "sess-1"}, {"holder_kind": "job", "session_id": "sess-1"},
    {"holder_kind": "job", "controller_id": "sess-1", "run_id": "PLANNER-20261011T220000Z"},
    {"holder_kind": "robot", "controller_id": "sess-1"}, {"controller_id": "sess-1"}, "", None,
])
def test_a_job_or_an_unknown_kind_of_holder_never_applies_a_command(tmp_path, applier):
    """C2-09: schemas/command.json admits cockpit | controller | supervisor as `applied_by`; a job actor used to
    pass here and then fail inside kyaction with an error that is not a CommandError."""
    run = mkrun(tmp_path)
    cid = kycommands.submit(run, "planner", "handoff", {}, COCKPIT)
    hold(run, "planner", "sess-1")
    seen = []
    with pytest.raises(kycommands.CommandInvalid, match="applier must be"):
        kycommands.apply(run, cid, applier, lambda c: seen.append(c) or {})
    with pytest.raises(kycommands.CommandInvalid):
        kycommands.applier_identity(applier)
    assert seen == [] and kycommands.find(run, cid)["doc"]["state"] == "QUEUED"
    assert not (run / "actions").exists() and not (run / "locks" / ("command." + cid)).exists()
    assert set(kycommands.APPLIER_KINDS) == set(
        json.loads((SCHEMAS / "command.json").read_text())["$defs"]["actor"]["properties"]["holder_kind"]["enum"])


@pytest.mark.parametrize("lock,reason", [
    ("none", "role_lock_not_held"), ("other", "role_lock_held_by_another"), ("dead", "role_lock_stale"),
    ("unverifiable", "role_lock_owner_unverifiable"), ("wrong-role", "role_lock_not_held"),
    ("no-ps", "role_lock_owner_unverifiable"), ("pid-missing", "role_lock_owner_unverifiable"),
    ("pid-not-an-integer", "role_lock_owner_unverifiable"),
])
def test_an_applier_that_does_not_hold_the_role_lock_is_refused(tmp_path, monkeypatch, lock, reason):
    run = mkrun(tmp_path)
    cid = kycommands.submit(run, "dispatcher", "builders", {"n": 5}, COCKPIT)
    if lock == "other":
        hold(run, "dispatcher", "someone-else")
    elif lock == "dead":
        hold(run, "dispatcher", "ctl-d", pid=dead_pid(), start="Sun Oct 11 22:00:00 2026")
    elif lock == "unverifiable":
        hold(run, "dispatcher", "ctl-d", start="")
    elif lock == "wrong-role":
        hold(run, "planner", "ctl-d")
    elif lock in ("no-ps", "pid-missing", "pid-not-an-integer"):      # the same liveness rule as the locks (R2)
        hold(run, "dispatcher", "ctl-d")
        owner = owner_of(run, "dispatcher")
        if lock == "pid-missing":
            del owner["pid"]
        elif lock == "pid-not-an-integer":
            owner["pid"] = str(owner["pid"])
        (run / "locks" / "dispatcher" / "owner.json").write_text(json.dumps(owner))
        if lock == "no-ps":
            no_ps(monkeypatch)
    before = tree(run)
    called = []
    status, detail = kycommands.apply(run, cid, "ctl-d", lambda c: called.append(1) or {})
    assert status == "refused" and detail["reason"].startswith(reason)
    assert called == [] and tree(run) == before                       # still QUEUED, nothing recorded
    assert [d["id"] for d in kycommands.pending(run, "dispatcher")] == [cid]


# ── CT-05: naming the holder is not holding the lock — the applier must BE the owner process (or its child) ──

def test_another_process_naming_the_holders_id_is_refused(tmp_path):
    """The reviewer's probe: a different process that names the holder id got (True, None)."""
    run = mkrun(tmp_path)
    cid = kycommands.submit(run, "dispatcher", "builders", {"n": 5}, COCKPIT)
    with bystander() as (pid, start):                       # the real controller: alive, and not us nor our ancestor
        hold(run, "dispatcher", "ctl-d", pid=pid, start=start)
        assert kyaction.process_matches(pid, start) is True
        assert kycommands.holds_role_lock(run, "dispatcher", "ctl-d")[0] is False
        before, called = tree(run), []
        status, detail = kycommands.apply(run, cid, "ctl-d", lambda c: called.append(1) or {})
        assert status == "refused" and detail["reason"].startswith("role_lock_not_owned_by_caller")
        assert called == [] and tree(run) == before
    assert [d["id"] for d in kycommands.pending(run, "dispatcher")] == [cid]


def test_the_owner_process_and_its_children_are_the_applier(tmp_path):
    run = mkrun(tmp_path)
    hold(run, "dispatcher", "ctl-d")                        # this process owns the role lock
    assert kycommands.holds_role_lock(run, "dispatcher", "ctl-d") == (True, None)
    assert kyaction.is_self_or_ancestor(os.getpid()) is True and kyaction.is_self_or_ancestor(os.getppid()) is True
    assert kyaction.is_self_or_ancestor(dead_pid()) is False
    for junk in (None, "1", 0, -5, True, 1.0):
        assert kyaction.is_self_or_ancestor(junk) is None
    child = subprocess.run([PY, "-c", "import sys; sys.path.insert(0, sys.argv[1]); import kycommands; "
                            "print(kycommands.holds_role_lock(sys.argv[2], 'dispatcher', 'ctl-d'))",
                            str(FLEET), str(run)], capture_output=True, text=True, env=SUB_ENV)
    assert child.stdout.strip() == "(True, None)", child.stderr        # the helper a lock holder started
    with bystander() as (pid, start):
        assert kyaction.is_self_or_ancestor(pid) is False


def test_an_ancestry_that_cannot_be_read_is_not_ownership(tmp_path, monkeypatch):
    run = mkrun(tmp_path)
    hold(run, "dispatcher", "ctl-d", pid=os.getppid(), start=kyaction.ps_identity(os.getppid())[1])
    assert kycommands.holds_role_lock(run, "dispatcher", "ctl-d") == (True, None)           # our parent owns it
    real = kyaction._ps
    monkeypatch.setattr(kyaction, "_ps", lambda pid, columns: None if columns == "ppid=" else real(pid, columns))
    held, why = kycommands.holds_role_lock(run, "dispatcher", "ctl-d")
    assert (held, why) == (True, None)                      # the parent is known without ps (getppid) …
    with bystander() as (pid, start):                       # … but past it the chain needs ps: unknown is refused
        hold(run, "dispatcher", "ctl-d", pid=pid, start=start)
        held, why = kycommands.holds_role_lock(run, "dispatcher", "ctl-d")
        assert held is False and why.startswith("role_lock_owner_unverifiable")


def test_ownership_is_checked_again_once_the_command_lock_is_held(tmp_path, monkeypatch):
    run = mkrun(tmp_path)
    cid = kycommands.submit(run, "dispatcher", "builders", {"n": 5}, COCKPIT)
    hold(run, "dispatcher", "ctl-d")
    real = kyaction.acquire_lock

    def the_role_lock_changes_hands(run_dir, name, owner_id, **kw):
        lock = real(run_dir, name, owner_id, **kw)
        if name == "command." + cid:
            hold(run, "dispatcher", "its-successor")        # between the first check and the command lock
        return lock

    monkeypatch.setattr(kyaction, "acquire_lock", the_role_lock_changes_hands)
    called = []
    status, detail = kycommands.apply(run, cid, "ctl-d", lambda c: called.append(1) or {})
    assert status == "refused" and detail["reason"].startswith("role_lock_held_by_another") and called == []
    assert kycommands.pending(run, "dispatcher")[0]["state"] == "QUEUED"
    assert not (run / "locks" / ("command." + cid)).exists() and not (run / "actions").exists()


def test_a_command_lock_whose_owner_cannot_be_judged_needs_attention(tmp_path):
    run = mkrun(tmp_path)
    cid = kycommands.submit(run, "dispatcher", "builders", {"n": 5}, COCKPIT)
    hold(run, "dispatcher", "ctl-d")
    hold(run, "command." + cid, "who-knows", start="")
    called = []
    status, detail = kycommands.apply(run, cid, "ctl-d", lambda c: called.append(1) or {})
    assert status == "refused" and detail["reason"].startswith("command_lock_owner_unknown")
    assert detail["attention"] is True and called == []
    assert owner_of(run, "command." + cid)["session_or_run_id"] == "who-knows"          # never taken over


def test_an_application_begun_by_a_process_that_is_still_alive_is_not_reconciled(tmp_path):
    """CT-12 at its caller: the CMD- record says another live process began the application."""
    run = mkrun(tmp_path)
    cid = kycommands.submit(run, "dispatcher", "builders", {"n": 5}, COCKPIT)
    hold(run, "dispatcher", "ctl-d")
    entry = kycommands.find(run, cid)
    kyaction.begin(run, "CMD-" + cid, "command:builders",
                   {"role": "dispatcher", "holder_kind": "controller", "controller_id": "ctl-d"},
                   {"role": "dispatcher", "command": "builders", "args": {"n": 5}},
                   {"command_id": cid, "file": entry["path"].name}, "command %s: QUEUED → APPLIED" % cid)
    path = run / "actions" / ("CMD-%s.json" % cid)
    with bystander() as (pid, start):
        path.write_text(json.dumps(dict(json.loads(path.read_text()), process={"pid": pid, "process_start": start})))
        called, observed = [], []
        status, detail = kycommands.apply(run, cid, "ctl-d", lambda c: called.append(1) or {},
                                          observer=lambda r: observed.append(1) or ("not_done", "x"))
        assert status == "locked" and detail["reason"].startswith("application_in_progress")
        assert called == [] and observed == [] and kycommands.pending(run, "dispatcher")[0]["state"] == "QUEUED"
    status, doc = kycommands.apply(run, cid, "ctl-d", lambda c: {"builders": 5},
                                   observer=lambda r: ("not_done", "KY_WORKERS unchanged"))
    assert status == "applied"                              # that process is gone: reconciled, then applied once


def test_apply_under_contention_runs_the_handler_once(tmp_path):
    run = mkrun(tmp_path)
    cid = kycommands.submit(run, "dispatcher", "builders", {"n": 5}, COCKPIT)
    hold(run, "dispatcher", "ctl-d")                     # the pytest process stays alive as the recorded owner
    body = r"""
def handler(cmd):
    with open(sys.argv[6], "a") as f:
        f.write("handled by %d\n" % os.getpid())
    time.sleep(0.2)
    return {"builders": cmd["args"]["n"]}
status, _ = kycommands.apply(sys.argv[4], sys.argv[5], "ctl-d", handler)
print(status)
"""
    codes, outs, errs = race(tmp_path, 6, snippet(body, run, cid, tmp_path / "effects"))
    assert codes == [0] * 6, errs
    assert outs.count("applied") == 1 and set(outs) <= {"applied", "locked", "already_applied"}, outs
    assert len((tmp_path / "effects").read_text().splitlines()) == 1
    assert json.loads((run / "commands" / (stems(run)[0] + ".json")).read_text())["state"] == "APPLIED"


def test_the_command_is_re_read_under_its_lock(tmp_path, monkeypatch):
    """§4a.6: a lock is always followed by a fresh handled-state check. Another process of the same controller
    settles the command between this caller's first look and its lock: this caller must not handle it again."""
    run = mkrun(tmp_path)
    cid = kycommands.submit(run, "dispatcher", "builders", {"n": 5}, COCKPIT)
    hold(run, "dispatcher", "ctl-d")
    real = kyaction.acquire_lock

    def raced(run_dir, name, owner_id, **kw):
        if name == "command." + cid:
            monkeypatch.setattr(kyaction, "acquire_lock", real)
            assert kycommands.apply(run, cid, "ctl-d", lambda c: {"by": "the other actor"})[0] == "applied"
        return real(run_dir, name, owner_id, **kw)

    monkeypatch.setattr(kyaction, "acquire_lock", raced)
    mine = []
    status, doc = kycommands.apply(run, cid, "ctl-d", lambda c: mine.append(1) or {"by": "me"})
    assert status == "already_applied" and mine == [] and doc["result"] == {"by": "the other actor"}


def test_a_command_locked_by_another_live_actor_is_skipped(tmp_path):
    run = mkrun(tmp_path)
    cid = kycommands.submit(run, "dispatcher", "builders", {"n": 5}, COCKPIT)
    hold(run, "dispatcher", "ctl-d")
    hold(run, "command." + cid, "someone-else")
    called = []
    status, detail = kycommands.apply(run, cid, "ctl-d", lambda c: called.append(1) or {})
    assert status == "locked" and called == []
    assert kycommands.pending(run, "dispatcher")[0]["state"] == "QUEUED"


def test_commands_are_applied_in_filename_order(tmp_path):
    run = mkrun(tmp_path)
    first = kycommands.submit(run, "dispatcher", "builders", {"n": 4}, COCKPIT)
    second = kycommands.submit(run, "dispatcher", "builders", {"n": 6}, COCKPIT)
    other_role = kycommands.submit(run, "planner", "status", {}, COCKPIT)
    hold(run, "dispatcher", "ctl-d")
    hold(run, "planner", "ctl-p")
    status, detail = kycommands.apply(run, second, "ctl-d", lambda c: {})
    assert status == "refused" and detail["reason"] == "earlier_command_pending: " + first
    assert kycommands.apply(run, other_role, "ctl-p", lambda c: {})[0] == "applied"     # other roles do not block
    assert kycommands.apply(run, first, "ctl-d", lambda c: {})[0] == "applied"
    assert kycommands.apply(run, second, "ctl-d", lambda c: {})[0] == "applied"


# ── CT-10: what cannot be read may be an earlier command ──

@pytest.mark.parametrize("torn,blocks", [("20000101T000000Z-torn.json", True), ("29990101T000000Z-torn.json", False),
                                         ("0-not-a-command-name.json", True), ("zz-not-a-command-name.json", False)])
def test_an_unreadable_earlier_file_blocks_the_roles_order(tmp_path, torn, blocks):
    run = mkrun(tmp_path)
    cid = kycommands.submit(run, "dispatcher", "builders", {"n": 5}, COCKPIT)
    (run / "commands" / torn).write_text("{")               # its role cannot be known: it may be the dispatcher's
    hold(run, "dispatcher", "ctl-d")
    called = []
    status, detail = kycommands.apply(run, cid, "ctl-d", lambda c: called.append(1) or {})
    if blocks:
        assert status == "refused" and detail["reason"] == "earlier_command_unreadable: " + torn and called == []
        assert kycommands.pending(run, "dispatcher")[0]["state"] == "QUEUED"
        (run / "commands" / torn).unlink()                  # repaired or removed by whoever looked at it
        assert kycommands.apply(run, cid, "ctl-d", lambda c: {})[0] == "applied"
    else:
        assert status == "applied" and called == [1]        # a LATER unreadable file does not block this command


def test_commands_with_independent_targets_are_not_held_up_by_an_unreadable_file(tmp_path):
    run = mkrun(tmp_path)
    (run / "commands").mkdir()
    (run / "commands" / "20000101T000000Z-torn.json").write_text("{")
    cid = kycommands.submit(run, "veto", "veto", {"decision_id": "SD-20261011T220000Z-1"}, COCKPIT)
    hold(run, "veto", "ctl-v")
    assert kycommands.apply(run, cid, "ctl-v", lambda c: {}, in_order=False)[0] == "applied"


def test_a_handler_rejection_is_recorded_once_with_its_reason(tmp_path):
    run = mkrun(tmp_path)
    cid = kycommands.submit(run, "conductor", "priority", {"item": "K9-9"}, COCKPIT)
    hold(run, "conductor", "ctl-c")
    calls = []

    def handler(cmd):
        calls.append(1)
        raise kycommands.Reject("unknown item K9-9")

    status, doc = kycommands.apply(run, cid, "ctl-c", handler)
    assert status == "rejected" and doc["state"] == "REJECTED" and doc["result"] == {"reason": "unknown item K9-9"}
    assert doc["applied_at"] and doc["applied_by"]["controller_id"] == "ctl-c"
    assert_schema("command", doc)
    status, again = kycommands.apply(run, cid, "ctl-c", handler)
    assert status == "already_rejected" and again == doc and calls == [1]
    assert kycommands.pending(run, "conductor") == []


def test_a_handler_that_raises_is_rejected_and_never_retried(tmp_path):
    run = mkrun(tmp_path)
    cid = kycommands.submit(run, "conductor", "priority", {"item": "K7-3"}, COCKPIT)
    hold(run, "conductor", "ctl-c")
    calls = []

    def handler(cmd):
        calls.append(1)
        raise RuntimeError("half-way")

    status, doc = kycommands.apply(run, cid, "ctl-c", handler)
    assert status == "rejected" and doc["result"]["reason"] == "handler_error: RuntimeError"
    assert kyaction.load(run, "CMD-" + cid)["state"] == "FAILED"
    assert kycommands.apply(run, cid, "ctl-c", handler)[0] == "already_rejected" and calls == [1]


def test_an_application_interrupted_inside_the_handler_is_reconciled_not_repeated(tmp_path):
    run = mkrun(tmp_path)
    cid = kycommands.submit(run, "dispatcher", "builders", {"n": 5}, COCKPIT)
    hold(run, "dispatcher", "ctl-d")
    calls = []

    def dies(cmd):
        calls.append("first")
        raise KeyboardInterrupt            # the process went away inside the handler: nothing is recorded as done

    with pytest.raises(KeyboardInterrupt):
        kycommands.apply(run, cid, "ctl-d", dies)
    assert kyaction.load(run, "CMD-" + cid)["state"] == "INTENDED"
    assert not (run / "locks" / ("command." + cid)).exists()

    def handler(cmd):
        calls.append("again")
        return {"builders": 5}

    status, detail = kycommands.apply(run, cid, "ctl-d", handler)                 # no observer: no blind repeat
    assert status == "unreconciled" and calls == ["first"]
    status, detail = kycommands.apply(run, cid, "ctl-d", handler, observer=lambda r: ("unknown", "cannot tell"))
    assert status == "unreconciled" and calls == ["first"]
    assert kycommands.pending(run, "dispatcher")[0]["state"] == "QUEUED"
    status, doc = kycommands.apply(run, cid, "ctl-d", handler, observer=lambda r: ("done", {"builders": 5}))
    assert status == "applied" and doc["result"] == {"builders": 5} and calls == ["first"]      # observed, not redone


def test_a_reconciliation_that_proves_nothing_happened_lets_the_handler_run(tmp_path):
    run = mkrun(tmp_path)
    cid = kycommands.submit(run, "dispatcher", "builders", {"n": 5}, COCKPIT)
    hold(run, "dispatcher", "ctl-d")
    with pytest.raises(KeyboardInterrupt):
        kycommands.apply(run, cid, "ctl-d", lambda c: (_ for _ in ()).throw(KeyboardInterrupt()))
    calls = []
    status, doc = kycommands.apply(run, cid, "ctl-d", lambda c: calls.append(1) or {"builders": 5},
                                   observer=lambda r: ("not_done", "KY_WORKERS unchanged"))
    assert status == "applied" and calls == [1] and doc["state"] == "APPLIED"


def test_a_hand_written_invalid_command_is_rejected_without_reaching_the_handler(tmp_path):
    run = mkrun(tmp_path)
    (run / "commands").mkdir()
    doc = {"schema": "ky.command/1", "id": "by-hand", "created_at": "2026-10-11T22:00:00Z", "from": COCKPIT,
           "role": "dispatcher", "command": "builders", "args": {"n": "many"}, "state": "QUEUED",
           "applied_by": None, "applied_at": None, "result": None}
    (run / "commands" / "20261011T220000Z-by-hand.json").write_text(json.dumps(doc))
    hold(run, "dispatcher", "ctl-d")
    assert [d["id"] for d in kycommands.pending(run, "dispatcher")] == ["by-hand"]
    called = []
    status, out = kycommands.apply(run, "by-hand", "ctl-d", lambda c: called.append(1) or {})
    assert status == "rejected" and out["result"]["reason"].startswith("invalid_command") and called == []


def test_apply_of_an_unknown_command_is_an_error(tmp_path):
    run = mkrun(tmp_path)
    hold(run, "dispatcher", "ctl-d")
    with pytest.raises(kycommands.CommandError):
        kycommands.apply(run, "no-such-command", "ctl-d", lambda c: {})


def apply_campaign(run, cid):
    hold(run, "campaign", "ctl-campaign")
    assert kycommands.apply(run, cid, "ctl-campaign", lambda c: {})[0] == "applied"


def test_owner_pause_comes_from_the_applied_history_and_only_an_owner_resume_ends_it(tmp_path):
    run = mkrun(tmp_path)
    assert kycommands.owner_paused(run) is False                              # an empty queue: not paused
    p1 = kycommands.submit(run, "campaign", "pause", {}, COCKPIT)
    assert kycommands.owner_paused(run) is False                              # queued is not yet applied …
    state = kycommands.pause_state(run)
    assert (state["state"], state["pending_pause"]) == ("not_paused", p1)     # … but it is visible as pending
    apply_campaign(run, p1)
    assert kycommands.owner_paused(run) is True
    kycommands.submit(run, "planner", "status", {}, COCKPIT)                  # unrelated commands change nothing
    kycommands.submit(run, "dispatcher", "builders", {"n": 6}, COCKPIT)
    r1 = kycommands.submit(run, "campaign", "resume", {}, COCKPIT)
    assert kycommands.owner_paused(run) is True                               # a queued resume has not happened
    apply_campaign(run, r1)
    assert kycommands.owner_paused(run) is False
    p2 = kycommands.submit(run, "campaign", "pause", {}, COCKPIT)
    apply_campaign(run, p2)
    assert kycommands.owner_paused(run) is True                               # pause → resume → pause = paused


def test_a_rejected_resume_does_not_end_a_pause(tmp_path):
    run = mkrun(tmp_path)
    apply_campaign(run, kycommands.submit(run, "campaign", "pause", {}, COCKPIT))
    r = kycommands.submit(run, "campaign", "resume", {}, COCKPIT)
    hold(run, "campaign", "ctl-campaign")

    def refuse(cmd):
        raise kycommands.Reject("gate not open")

    assert kycommands.apply(run, r, "ctl-campaign", refuse)[0] == "rejected"
    assert kycommands.owner_paused(run) is True


def test_a_pause_whose_handler_failed_stays_in_force_as_requested(tmp_path):
    """CT-10: the owner asked for a pause and the role's handler broke while applying it. The request stands."""
    run = mkrun(tmp_path)
    p1 = kycommands.submit(run, "campaign", "pause", {}, COCKPIT)
    hold(run, "campaign", "ctl-campaign")

    def broken(cmd):
        raise OSError("disk full")

    status, doc = kycommands.apply(run, p1, "ctl-campaign", broken)
    assert status == "rejected" and doc["result"]["reason"] == "handler_error: OSError"
    state = kycommands.pause_state(run)
    assert (state["state"], state["applied_pause"], state["pending_pause"], state["pending_kind"]) == (
        "not_paused", None, p1, "handler_error")
    assert kycommands.owner_paused(run) is False            # it is not APPLIED, and is not reported as if it were
    r1 = kycommands.submit(run, "campaign", "resume", {}, COCKPIT)
    assert kycommands.pause_state(run)["pending_pause"] is None             # only the owner's own resume lifts it
    apply_campaign(run, r1)
    assert kycommands.pause_state(run)["pending_pause"] is None


def test_a_pause_the_role_refused_on_purpose_is_not_a_pending_pause(tmp_path):
    run = mkrun(tmp_path)
    p1 = kycommands.submit(run, "campaign", "pause", {}, COCKPIT)
    hold(run, "campaign", "ctl-campaign")

    def refuse(cmd):
        raise kycommands.Reject("no campaign is running")

    assert kycommands.apply(run, p1, "ctl-campaign", refuse)[0] == "rejected"
    state = kycommands.pause_state(run)
    assert (state["state"], state["pending_pause"], state["pending_kind"]) == ("not_paused", None, None)
    p2 = kycommands.submit(run, "campaign", "pause", {}, COCKPIT)
    assert kycommands.pause_state(run)["pending_kind"] == "queued" and kycommands.pause_state(run)["pending_pause"] == p2


@pytest.mark.parametrize("tamper", ["resume-not-from-owner", "torn-file", "pause-on-another-role", "bad-name"])
def test_a_queue_that_cannot_be_read_is_unknown_never_not_paused(tmp_path, tamper):
    run = mkrun(tmp_path)
    apply_campaign(run, kycommands.submit(run, "campaign", "pause", {}, COCKPIT))
    doc = {"schema": "ky.command/1", "id": "x1", "created_at": "2026-10-11T23:00:00Z", "from": COCKPIT,
           "role": "campaign", "command": "resume", "args": {}, "state": "APPLIED",
           "applied_by": {"role": "campaign", "holder_kind": "controller", "controller_id": "c"},
           "applied_at": "2026-10-11T23:00:01Z", "result": {}}
    name = "29991011T230000Z-x1.json"
    if tamper == "resume-not-from-owner":
        doc["from"] = {"kind": "surrogate", "session_id": "surrogate-1"}        # the surrogate never undoes a pause
    elif tamper == "pause-on-another-role":
        doc.update(role="planner", command="pause")
    elif tamper == "bad-name":
        name = "x1.json"
    (run / "commands" / name).write_text("{" if tamper == "torn-file" else json.dumps(doc))
    state = kycommands.pause_state(run)
    assert state["state"] == "unknown" and state["problems"]
    with pytest.raises(kycommands.QueueUnreadable):
        kycommands.owner_paused(run)


def test_commands_cli_submits_and_lists(tmp_path):
    run = mkrun(tmp_path)
    env = dict(SUB_ENV, KY_RUN=str(run))

    def cli(*args):
        return subprocess.run([PY, str(FLEET / "kycommands.py"), *args], capture_output=True, text=True, env=env)

    r = cli("submit", "--role", "dispatcher", "--command", "builders", "--args", '{"n": 5}', "--session", "sess-9")
    assert r.returncode == 0, r.stderr
    cid = r.stdout.strip()
    (doc,) = kycommands.pending(run, "dispatcher")
    assert doc["id"] == cid and doc["args"] == {"n": 5}
    assert sorted(doc["from"]) == ["kind", "pid", "process_start", "session_id"]
    assert (doc["from"]["kind"], doc["from"]["session_id"]) == ("cockpit", "sess-9")
    assert doc["from"]["pid"] not in (os.getpid(), None) and doc["from"]["process_start"]     # the CLI process itself
    assert_schema("command", doc)
    r = cli("submit", "--role", "campaign", "--command", "pause", "--session", "sess-9")
    assert r.returncode == 0
    bad = cli("submit", "--role", "dispatcher", "--command", "builders", "--args", '{"n": 0}', "--session", "sess-9")
    assert bad.returncode == 1 and "n" in bad.stderr
    assert cli("submit", "--role", "dispatcher", "--command", "builders", "--args", "{not json", "--session",
               "s").returncode == 64
    assert cli("submit", "--role", "dispatcher", "--command", "builders").returncode == 64
    before = tree(run, skip=())
    listed = cli("list")
    assert listed.returncode == 0 and cid in listed.stdout and "pause" in listed.stdout
    only = cli("list", "--role", "campaign", "--state", "QUEUED")
    assert only.returncode == 0 and "pause" in only.stdout and cid not in only.stdout
    assert cli("list", "--state", "APPLIED").stdout.strip() == ""
    assert cli("list", "--role", "owner").returncode == 64
    assert cli("apply", cid).returncode == 64                    # applying is not a CLI operation
    assert tree(run, skip=()) == before
    (run / "commands" / "20261011T220000Z-torn.json").write_text("{")
    torn = cli("list")
    assert torn.returncode == 1 and "torn" in torn.stderr and cid in torn.stdout


# ═════════════════════════════════════════════ kyveto ═════════════════════════════════════════════

def cap(builders=6, verifiers=4, **extra):
    return dict({"kind": "capacity", "builders": builders, "verifiers": verifiers}, **extra)


class World:
    """One isolated KY_ROOT: run/, fleet_live/, bin/ky (the double), an authorised bundle and capacity files."""

    def __init__(self, tmp):
        self.tmp = tmp
        self.root, self.repo = tmp / "ky", tmp / "repo"
        self.run, self.fleet = self.root / "run", self.root / "fleet_live"
        for d in (self.run / "awaiting", self.fleet, self.root / "bin", self.repo):
            d.mkdir(parents=True)
        shutil.copy(FIX / "fake_ky", self.root / "bin" / "ky")
        self.log, self.journal = self.run / "DECISIONS_SURROGATE.jsonl", self.run / "JOURNAL_COCKPIT.md"
        self.authorise(C1, E1)
        self.blobs({C1: "d" * 40, C2: "d" * 40, C3: "d" * 40})
        (self.run / "KY_WORKERS").write_text("3\n")
        (self.run / "KY_VERIFIERS").write_text("2\n")
        self.environ = dict(SUB_ENV, KY_ROOT=str(self.root), KY_RUN=str(self.run), KY_FLEET=str(self.fleet),
                            KY_GIT=str(FIX / "fake_git"), KY_SOURCE_REPO=str(self.repo))
        self.n = 0

    @property
    def env(self):
        return kyveto.Env(self.environ)

    def authorise(self, commit, digest):
        (self.run / "PLANNER_STATE.json").write_text(json.dumps(
            {"schema": "ky.role_state/1", "authorised_source": {"source_commit": commit, "entrypoints_digest": digest}}))

    def blobs(self, by_commit):
        (self.repo / "blobs.json").write_text(json.dumps(
            {"%s:%s" % (c, kyveto.OWNER_DECISIONS_PATH): b for c, b in by_commit.items()}))

    def propose(self, target, sid=None, bind=True, awaiting_open=True, notified=T_NOTIFY, seen=T_NOTIFY, **over):
        """A decision line as the surrogate appends it, with what a real run holds beside it by the time its
        window is judged: kynotify's journal line (`notified`: its timestamp, None = no such line) and the
        handler's first-seen stamp (`seen`: when a tick first saw it, None = no tick has seen it yet)."""
        self.n += 1
        sid = sid or "SD-20261011T220000Z-%d" % self.n
        if isinstance(target, dict):
            target = dict(target)
            if bind:
                target["fingerprint"] = kyveto.fingerprint(target, self.env)
        line = {"id": sid, "awaiting": "AW-20261011T215900Z-item-%d" % self.n, "class": "veto",
                "state": "PENDING_VETO", "decision": "raise capacity", "rationale": "nine ready items",
                "evidence": ["run/JOURNAL_DISPATCHER.md"], "target": target,
                "authority": {"source_commit": C1, "entrypoints_digest": E1},
                "notification": {"submitted": True, "ts": T_NOTIFY}, "veto_deadline": T_DEADLINE,
                "effective_at": None, "by": "kalayantra-owner-surrogate", "session": "surrogate-1"}
        line.update(over)
        if notified is not None:
            self.notify(sid, notified)
        self.append(line)
        if seen is not None and line["state"] == "PENDING_VETO":
            self.see(sid, seen)
        if awaiting_open and isinstance(line["awaiting"], str):
            item = {"id": line["awaiting"]}
            td = target.get("tracker_decision") if isinstance(target, dict) else None
            if isinstance(td, dict) and isinstance(td.get("id"), str):
                item["item"] = td["id"]                    # C2-02: the item names the tracker decision it is about
            (self.run / "awaiting" / (line["awaiting"] + ".json")).write_text(json.dumps(item))
        return sid

    def notify(self, sid, at=T_NOTIFY, result="submitted", text="raise capacity", level="decision"):
        """The journal line kynotify.sh leaves (ruling R3): `- <UTC> [<level>] <message> [notify=<result>]`."""
        with open(self.journal, "a", encoding="utf-8") as f:
            f.write("- %s [%s] %s: %s [notify=%s]\n" % (at, level, sid, text, result))

    def see(self, sid, at=T_NOTIFY):
        """The handler's first sight of the proposal, written by the handler's own function at time `at`."""
        stamp, problem = kyveto.first_seen(self.run, sid, kyveto.proposal_of(self.history(sid)),
                                           kyaction.parse_utc(at) if isinstance(at, str) else at)
        assert problem is None, problem
        return stamp

    def stamp(self, sid):
        path = kyveto.stamp_path(self.run, sid)
        return json.loads(path.read_text()) if path.exists() else None

    def refusal(self, sid):
        path = kyveto.stamp_path(self.run, sid, "refused")
        return json.loads(path.read_text()) if path.exists() else None

    def append(self, line):
        with open(self.log, "a", encoding="utf-8") as f:
            f.write(json.dumps(line) + "\n")

    def history(self, sid):
        return [d for d in map(json.loads, self.log.read_text(encoding="utf-8").splitlines()) if d["id"] == sid]

    def states(self, sid):
        return [d["state"] for d in self.history(sid)]

    def tick(self, now, **kw):
        """One pass of the handler with ITS clock at `now` (the only way a test moves time: in-process)."""
        with clock(now):
            return kyveto.tick(self.env, **kw)

    def cli(self, *args, **popen):
        """The real program in its own process: the real wall clock, two hours after every proposal here."""
        return subprocess.run([PY, str(FLEET / "kyveto.py"), *args], capture_output=True, text=True,
                              env=self.environ, **popen)

    def crash(self, point, *args):
        return subprocess.run([PY, str(FIX / "crash_tick.py"), str(FLEET), point, *args], capture_output=True,
                              text=True, env=self.environ)

    def ky_calls(self):
        path = self.root / "fake_ky" / "calls.jsonl"
        return [json.loads(x) for x in path.read_text().splitlines()] if path.exists() else []

    def ky_says(self, name, value):
        (self.root / "fake_ky").mkdir(exist_ok=True)
        (self.root / "fake_ky" / name).write_text(str(value))

    def veto(self, sid):
        return kycommands.submit(self.run, "veto", "veto", {"decision_id": sid}, COCKPIT)

    def command(self, cid):
        return kycommands.find(self.run, cid)["doc"]

    def action(self, aid):
        return kyaction.load(self.run, aid)

    def capacity(self):
        return (self.run / "KY_WORKERS").read_text(), (self.run / "KY_VERIFIERS").read_text()

    def actions(self):
        d = self.run / "actions"
        return sorted(p.name for p in d.iterdir()) if d.exists() else []

    def untouched(self):
        """Nothing was published, executed or recorded as an action."""
        return self.ky_calls() == [] and self.capacity() == ("3\n", "2\n") and self.actions() == []


def one(report, sid):
    found = [d for d in report["decisions"] if d["id"] == sid]
    assert len(found) == 1, report
    return found[0]


def test_defaults_are_the_pinned_paths_and_every_one_is_overridable():
    env = kyveto.Env({})
    assert (str(env.root), str(env.run), str(env.fleet), str(env.ky_bin)) == (
        "/Users/Dev/kalayantra", "/Users/Dev/kalayantra/run", "/Users/Dev/kalayantra/fleet_live",
        "/Users/Dev/kalayantra/bin/ky")
    env = kyveto.Env({"KY_ROOT": "/r", "KY_RUN": "/elsewhere/run", "KY_FLEET": "/f", "KY_BIN": "/b/ky"})
    assert (str(env.root), str(env.run), str(env.fleet), str(env.ky_bin)) == ("/r", "/elsewhere/run", "/f", "/b/ky")
    assert str(kyveto.Env({"KY_ROOT": "/r"}).run) == "/r/run"
    assert PINNED_DEFAULT_SOURCE_REPO == "/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-campaign"


def test_before_expiry_nothing_is_published_or_executed(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap(tracker_decision=TD))
    before = tree(w.run)
    report = w.tick(BEFORE)
    d = one(report, sid)
    assert d["outcome"] == "pending" and d["seconds_remaining"] == 1200
    assert d["veto_deadline"] == d["effective_not_before"] == T_DEADLINE          # when the controller wakes next
    assert (d["record_veto_deadline"], d["first_seen_at"], d["notified_at"]) == (T_DEADLINE, T_NOTIFY, T_NOTIFY)
    assert tree(w.run) == before and w.untouched()
    assert report["attention"] is False
    one_second_early = w.tick(iso(1799))
    assert one(one_second_early, sid)["seconds_remaining"] == 1 and tree(w.run) == before


def test_at_expiry_the_decision_is_published_then_executed_exactly_once(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap(tracker_decision=TD))
    report = w.tick(AT)                                           # the window has run its thirty minutes
    assert one(report, sid)["outcome"] == "executed" and report["attention"] is False
    assert w.states(sid) == ["PENDING_VETO", "EFFECTIVE", "EXECUTED"]
    proposal, effective, executed = w.history(sid)
    for line in (effective, executed):
        assert line["by"] == "kyveto" and line["reason"] and line["effective_at"] == AT and line["at"] == AT
        assert line["target"] == proposal["target"] and line["authority"] == proposal["authority"]
        assert line["awaiting"] == proposal["awaiting"] and line["veto_deadline"] == T_DEADLINE
    assert w.capacity() == ("6\n", "4\n")
    assert [c["argv"] for c in w.ky_calls()] == [["decide", "D-41", "--outcome", "approved", "--as", "steward",
                                                  "--delegated", "--detail", sid + ": raise capacity"]]
    publish, execute = w.action(sid + ".publish"), w.action(sid + ".execute")
    assert publish["state"] == "DONE" and publish["result"]["exit_status"] == 0
    assert publish["result"]["published"] is True and publish["result"]["effective_at"] == AT
    assert execute["state"] == "DONE" and execute["target"] == proposal["target"]
    assert publish["actor"]["role"] == "veto" and execute["actor"]["role"] == "veto"
    for rec in (publish, execute):
        assert_schema("action", rec)
    assert not (w.run / "locks" / ("decision." + sid)).exists()


def test_a_second_tick_after_executed_is_a_no_op(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap(tracker_decision=TD))
    w.tick(AT)
    before, inode = tree(w.run), (w.run / "KY_WORKERS").stat().st_ino
    for now in (AT, AFTER, LATER):
        report = w.tick(now)
        assert report["decisions"] == [] and report["attention"] is False
    assert tree(w.run) == before and len(w.ky_calls()) == 1
    assert (w.run / "KY_WORKERS").stat().st_ino == inode            # not even rewritten
    assert w.states(sid).count("EXECUTED") == 1 and w.states(sid).count("EFFECTIVE") == 1


def test_a_decision_without_a_tracker_decision_publishes_nothing_to_the_tracker(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap())
    assert one(w.tick(AT), sid)["outcome"] == "executed"
    assert w.ky_calls() == [] and w.capacity() == ("6\n", "4\n")
    # the handler's memory of having made it effective is still an action record — one that says nothing was sent
    assert w.actions() == [sid + ".execute.json", sid + ".publish.json"]
    publish = w.action(sid + ".publish")
    assert publish["kind"] == "effective_without_tracker_decision" and publish["target"] == {"tracker_decision": None}
    assert publish["result"] == {"published": False, "effective_at": AT}
    assert w.history(sid)[1]["detail"] == {"publication": sid + ".publish", "published": False}
    assert_schema("action", publish)


def test_ky_receives_an_allow_listed_environment(tmp_path, monkeypatch):
    w = World(tmp_path)
    w.environ.update(DATABASE_URL="postgres://not-a-real-one", ANTHROPIC_API_KEY="not-a-real-one", KY_STREAM="K")
    w.propose(cap(tracker_decision=TD))
    w.tick(AT)
    (call,) = w.ky_calls()
    assert set(call["env_names"]) - {"__CF_USER_TEXT_ENCODING", "LC_CTYPE"} <= set(kyveto.KY_ENV_NAMES)
    assert "DATABASE_URL" not in call["env_names"] and "ANTHROPIC_API_KEY" not in call["env_names"]
    assert "KY_ROOT" in call["env_names"]


# ── CT-01 (ruling R3): the effecting path takes its time from the wall clock and from nobody else ──

def test_the_effecting_path_takes_no_clock_from_its_caller(tmp_path):
    """The reviewer's probe: an honest proposal whose window ends in 30 minutes, then
    `kyveto.py tick --now 2099-01-01T00:00:00Z` → executed, rc 0, effective_at 2099."""
    w = World(tmp_path)
    now = int(time.time())
    sid = w.propose(cap(tracker_decision=TD), notified=kyaction.utc(now), seen=None,
                    notification={"submitted": True, "ts": kyaction.utc(now)}, veto_deadline=kyaction.utc(now + 1800))
    before = tree(w.run)
    for argv in (("tick", "--now", "2099-01-01T00:00:00Z"), ("tick", "--now", kyaction.utc(now + 1801)),
                 ("tick", "--as-of", "2099-01-01T00:00:00Z"), ("tick", "2099-01-01T00:00:00Z")):
        r = w.cli(*argv)
        assert r.returncode == 64 and "no --now" in r.stderr, (argv, r.stdout, r.stderr)       # refused outright
        assert tree(w.run) == before and w.untouched()
    with pytest.raises(TypeError):
        kyveto.tick(w.env, now="2099-01-01T00:00:00Z")                 # the function has no such parameter …
    with pytest.raises(TypeError):
        kyveto.tick(w.env, "2099-01-01T00:00:00Z")                     # … not by position either
    assert tree(w.run) == before and w.untouched()
    w.environ.update(KYVETO_NOW="2099-01-01T00:00:00Z", KY_NOW="2099-01-01T00:00:00Z", NOW="4070908800",
                     KYVETO_CLOCK="2099-01-01T00:00:00Z", SOURCE_DATE_EPOCH="4070908800")
    r = w.cli("tick")                                                  # the real program, the real clock
    assert r.returncode == 0, r.stderr
    report = json.loads(r.stdout)
    d = one(report, sid)
    assert d["outcome"] == "pending" and 1700 <= d["seconds_remaining"] <= 1801       # first sight is rounded UP
    assert abs(kyaction.parse_utc(w.stamp(sid)["first_seen_at"]) - time.time()) < 120
    assert abs(kyaction.parse_utc(report["now"]) - time.time()) < 120
    assert w.states(sid) == ["PENDING_VETO"] and w.untouched()
    assert json.loads(w.cli("status", "--now", "2099-01-01T00:00:00Z").stdout)["now"] == "2099-01-01T00:00:00Z"
    assert w.states(sid) == ["PENDING_VETO"] and w.untouched()         # `status` may be asked about any time: read-only


def test_the_handlers_clock_is_one_module_level_function(tmp_path):
    """What the tests replace in-process; there is no second path to the time of a tick."""
    w = World(tmp_path)
    sid = w.propose(cap())
    with clock(BEFORE):
        assert kyveto.tick(w.env)["now"] == BEFORE
    assert abs(kyveto.wall_clock() - time.time()) < 5                  # and it is the wall clock again
    assert w.states(sid) == ["PENDING_VETO"]


# ── CT-02 (ruling R3): the window is counted from evidence the surrogate does not write ──

def test_first_sight_is_stamped_once_and_binds_the_proposal(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap(), seen=None)
    assert w.stamp(sid) is None
    w.tick(iso(5))
    stamp = w.stamp(sid)
    assert stamp == {"first_seen_at": iso(5), "proposal_line_sha256": kyveto.proposal_sha(w.history(sid)[0])}
    path = kyveto.stamp_path(w.run, sid)
    assert path == w.run / "veto" / (sid + ".first_seen.json") and path.stat().st_mode & 0o222 == 0
    before = path.read_bytes()
    w.tick(iso(900))                                                   # never rewritten by a later sight
    assert path.read_bytes() == before and kyveto.first_seen(w.run, sid, {"other": 1}, 1.0)[0] == stamp
    assert w.tick(iso(950))["decisions"][0]["first_seen_at"] == iso(5)
    other = w.propose(cap(builders=5), seen=None)
    w.tick(T0 + 1000.25)                                               # the clock has fractions; the stamp has seconds
    assert w.stamp(other)["first_seen_at"] == iso(1001)                # rounded UP: never a second too early


def test_a_backdated_proposal_still_waits_thirty_real_minutes_from_first_sight(tmp_path):
    """The reviewer's probe (a): backdated notification.ts / veto_deadline → executed on first sight. Here the
    record AND the journal line claim a window that ended long ago; the handler has never seen the decision."""
    w = World(tmp_path)
    sid = w.propose(cap(tracker_decision=TD), seen=None)               # notified T0, deadline T0 + 30 min: "long over"
    first = T0 + 5000                                                  # the handler's first sight
    d = one(w.tick(first), sid)
    assert d["outcome"] == "pending" and d["seconds_remaining"] == 1800 and d["first_seen_at"] == iso(5000)
    assert d["veto_deadline"] == iso(6800) and d["record_veto_deadline"] == T_DEADLINE
    assert w.untouched()
    d = one(w.tick(first + 1799), sid)
    assert d["outcome"] == "pending" and d["seconds_remaining"] == 1 and w.untouched()
    assert w.states(sid) == ["PENDING_VETO"]
    assert one(w.tick(first + 1800), sid)["outcome"] == "executed"
    assert w.history(sid)[1]["effective_at"] == iso(6800) and w.capacity() == ("6\n", "4\n")


def test_the_window_runs_from_the_later_of_first_sight_and_notification(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap(), notified=iso(600), seen=T_NOTIFY)           # the notification went out ten minutes later
    assert one(w.tick(AT), sid)["seconds_remaining"] == 600
    assert one(w.tick(iso(2399)), sid)["outcome"] == "pending"
    assert one(w.tick(iso(2400)), sid)["outcome"] == "executed"


def test_the_latest_submitted_notification_counts(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap())
    w.notify(sid, iso(900))                                            # the surrogate notified again
    w.notify(sid, iso(1200), result="failed")                          # a failed attempt is no notification
    d = one(w.tick(AT), sid)
    assert d["outcome"] == "pending" and d["notified_at"] == iso(900) and d["seconds_remaining"] == 900
    assert one(w.tick(iso(2700)), sid)["outcome"] == "executed"


@pytest.mark.parametrize("deadline,first_effective", [(600, 1800), (1800, 1800), (3600, 3600)])
def test_never_before_the_records_own_deadline_and_never_before_the_full_window(tmp_path, deadline, first_effective):
    """A deadline the surrogate set too early buys nothing (the handler counts the window itself); a later one
    is honoured."""
    w = World(tmp_path)
    sid = w.propose(cap(), veto_deadline=iso(deadline))
    d = one(w.tick(iso(first_effective - 1)), sid)
    assert d["outcome"] == "pending" and d["seconds_remaining"] == 1 and d["record_veto_deadline"] == iso(deadline)
    assert w.untouched()
    assert one(w.tick(iso(first_effective)), sid)["outcome"] == "executed"


@pytest.mark.parametrize("journal", ["absent", "empty", "failed", "dry", "another-decision", "no-suffix",
                                     "id-not-at-the-start", "unreadable-time", "suffix-inside-the-message",
                                     "smuggled-line-separators", "no-leading-dash"])
def test_a_notification_the_journal_does_not_show_as_submitted_is_unverified(tmp_path, journal):
    """`notification.submitted: true` is the surrogate's word. Without kynotify's own line — message beginning
    `<SD id>:`, ending `[notify=submitted]` — the decision fails at once: notification_unverified."""
    w = World(tmp_path)
    sid = w.propose(cap(tracker_decision=TD), notified=None)
    if journal == "empty":
        w.journal.write_text("")
    elif journal in ("failed", "dry"):
        w.notify(sid, T_NOTIFY, result=journal)
    elif journal == "another-decision":
        w.notify(sid + "1", T_NOTIFY)                                  # SD-…-11 is not SD-…-1
        w.notify("SD-20261011T220000Z-999", T_NOTIFY)
    elif journal == "no-suffix":
        w.journal.write_text("- %s [decision] %s: raise capacity\n" % (T_NOTIFY, sid))
    elif journal == "id-not-at-the-start":
        w.journal.write_text("- %s [decision] re %s: raise capacity [notify=submitted]\n" % (T_NOTIFY, sid))
    elif journal == "unreadable-time":
        w.journal.write_text("- yesterday [decision] %s: raise capacity [notify=submitted]\n" % sid)
    elif journal == "suffix-inside-the-message":
        w.journal.write_text("- %s [decision] %s: raise [notify=submitted] capacity [notify=failed]\n" % (T_NOTIFY, sid))
    elif journal == "smuggled-line-separators":            # ONE physical line: another decision's failed notification
        w.journal.write_text("- %s [decision] SD-20261011T220000Z-9: x [notify=submitted]\u2028- %s [decision] %s: "
                             "raise capacity [notify=submitted]\x85\x0b\x0c\r- %s [decision] %s: again "
                             "[notify=submitted]\x1e [notify=failed]\n" % (T_NOTIFY, T_NOTIFY, sid, T_NOTIFY, sid),
                             encoding="utf-8", newline="")
    elif journal == "no-leading-dash":
        w.journal.write_text("%s [decision] %s: raise capacity [notify=submitted]\n" % (T_NOTIFY, sid))
    report = w.tick(BEFORE)                                            # judged at first sight, not at the deadline
    d = one(report, sid)
    assert (d["outcome"], d["reason"], d["attention"]) == ("failed", "notification_unverified", True)
    assert report["attention"] is True and w.states(sid) == ["PENDING_VETO", "FAILED"] and w.untouched()
    w.notify(sid, T_NOTIFY)                                            # evidence that turns up later resurrects nothing
    assert w.tick(LATER)["decisions"] == [] and w.untouched()


def test_a_journal_that_cannot_be_read_blocks_instead_of_failing(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap(), notified=None)
    w.journal.mkdir()                                                  # there, and not readable as a file
    d = one(w.tick(AT), sid)
    assert d["outcome"] == "blocked" and d["reason"].startswith("journal_unreadable") and d["attention"] is True
    assert w.states(sid) == ["PENDING_VETO"] and w.untouched()
    w.journal.rmdir()
    w.notify(sid, T_NOTIFY)
    assert one(w.tick(AT), sid)["outcome"] == "executed"


def test_a_notification_that_was_not_submitted_prevents_effectiveness(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap(tracker_decision=TD), notification={"submitted": False, "ts": T_NOTIFY})
    report = w.tick(BEFORE)                                            # at first sight: it can never become effective
    d = one(report, sid)
    assert (d["outcome"], d["reason"], d["attention"]) == ("failed", "notification_not_submitted", True)
    assert w.states(sid) == ["PENDING_VETO", "FAILED"]
    failed = w.history(sid)[-1]
    assert failed["by"] == "kyveto" and failed["reason"] == "notification_not_submitted"
    assert failed["effective_at"] is None and w.untouched()
    assert w.tick(AFTER)["decisions"] == []


def test_the_surrogates_word_does_not_replace_the_journal_and_the_journal_does_not_replace_its_word(tmp_path):
    w = World(tmp_path)
    said_no = w.propose(cap(), notification={"submitted": False, "ts": T_NOTIFY})       # journal line present
    said_yes = w.propose(cap(builders=5), notified=None)                                # journal line absent
    report = w.tick(AT)
    assert one(report, said_no)["reason"] == "notification_not_submitted"
    assert one(report, said_yes)["reason"] == "notification_unverified"
    assert w.untouched()


def test_a_forged_effective_line_under_the_handlers_name_skips_nothing(tmp_path):
    """The reviewer's probe (b): an EFFECTIVE line carrying `by: "kyveto"` in the model-writable log was taken as
    the handler's own earlier publication, skipped the deadline and notification checks → executed 30 min early."""
    w = World(tmp_path)
    sid = w.propose(cap(tracker_decision=TD))
    w.append(dict(w.history(sid)[0], state="EFFECTIVE", by="kyveto", effective_at=BEFORE, session="ctl-veto",
                  reason="veto_window_expired_unvetoed"))
    report = w.tick(BEFORE)                                            # twenty minutes of the window are still left
    d = one(report, sid)
    assert (d["outcome"], d["reason"]) == ("failed", "log_claims_effective_without_action_record")
    assert d["attention"] is True and d["anomaly"] == "log_claim_without_action_record" and report["attention"] is True
    assert w.states(sid) == ["PENDING_VETO", "EFFECTIVE", "FAILED"] and w.untouched()
    for now in (AT, LATER):                                            # blocked for good, and reported once
        assert w.tick(now)["decisions"] == [] and w.untouched()


@pytest.mark.parametrize("claim", ["EFFECTIVE", "EXECUTED"])
@pytest.mark.parametrize("by", ["kyveto", "kalayantra-owner-surrogate"])
def test_a_log_line_is_never_evidence_of_what_the_handler_did(tmp_path, claim, by):
    w = World(tmp_path)
    sid = w.propose(cap())
    w.append(dict(w.history(sid)[0], state=claim, by=by, effective_at=AT))
    d = one(w.tick(LATER), sid)                                        # even after the window: the claim is an anomaly
    assert (d["outcome"], d["reason"]) == ("failed", "log_claims_%s_without_action_record" % claim.lower())
    assert d["attention"] is True and w.untouched() and w.states(sid)[-1] == "FAILED"
    assert w.tick(LATER)["decisions"] == []


def test_the_handlers_own_memory_carries_a_decision_across_a_lost_log_line(tmp_path):
    """The other direction: `<id>.publish` is DONE but no EFFECTIVE line was written (a crash right there). The
    action record, not the log, says it is effective: it is completed, not judged afresh, and not re-published."""
    w = World(tmp_path)
    sid = w.propose(cap(tracker_decision=TD))
    real, calls = kyveto.append_line, []

    def crash_before_the_effective_line(path, obj):
        if obj.get("state") == "EFFECTIVE" and not calls:
            calls.append(1)
            raise OSError("no space left on device")
        return real(path, obj)

    kyveto.append_line = crash_before_the_effective_line               # (the autouse fixture restores it)
    d = one(w.tick(AT), sid)
    assert d["outcome"] == "blocked" and d["attention"] is True and w.states(sid) == ["PENDING_VETO"]
    assert w.action(sid + ".publish")["state"] == "DONE" and w.capacity() == ("3\n", "2\n")
    assert one(w.tick(LATER), sid)["outcome"] == "executed"            # effective_at is when it WAS made effective
    assert w.states(sid) == ["PENDING_VETO", "EFFECTIVE", "EXECUTED"] and w.history(sid)[1]["effective_at"] == AT
    assert len(w.ky_calls()) == 1 and w.capacity() == ("6\n", "4\n")


def test_an_action_record_the_veto_role_did_not_write_is_not_the_handlers_memory(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap(tracker_decision=TD))
    kyaction.begin(w.run, sid + ".publish", "tracker_decision_publish",
                   {"role": "planner", "holder_kind": "cockpit", "session_id": "someone"}, {"decision_id": sid}, {}, "x")
    kyaction.complete(w.run, sid + ".publish", {"exit_status": 0})
    report = w.tick(BEFORE)                                            # a planted "already published" skips nothing
    d = one(report, sid)
    assert d["outcome"] == "blocked" and "Foreign" in d["reason"] and d["attention"] is True
    assert w.states(sid) == ["PENDING_VETO"] and w.ky_calls() == [] and w.capacity() == ("3\n", "2\n")
    status = kyveto.status(w.env, now=BEFORE)             # C2-01: what somebody else did under that id is not known
    (row,) = status["decisions"]
    assert row["published"] == "unknown" and row["unresolved"] is True and row["made_effective_by_handler"] is False
    assert status["publication_unknown"] == [sid] and status["attention"] is True


def test_a_first_seen_stamp_that_cannot_be_read_blocks(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap(), seen=None)
    path = kyveto.stamp_path(w.run, sid)
    path.parent.mkdir()
    for junk in ("{", "[]", json.dumps({"first_seen_at": "long ago", "proposal_line_sha256": "0" * 64}),
                 json.dumps({"first_seen_at": T_NOTIFY}), json.dumps({"first_seen_at": T_NOTIFY,
                                                                      "proposal_line_sha256": "abc"})):
        path.write_text(junk)
        d = one(w.tick(LATER), sid)
        assert d["outcome"] == "blocked" and d["reason"].startswith("first_seen_unreadable") and d["attention"] is True
        assert path.read_text() == junk and w.states(sid) == ["PENDING_VETO"] and w.untouched()


def test_a_proposal_rewritten_after_first_sight_is_refused(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap(builders=4))
    line = w.history(sid)[0]
    w.log.write_text(json.dumps(dict(line, rationale="a different story")) + "\n")      # the log was rewritten
    d = one(w.tick(AT), sid)
    assert (d["outcome"], d["reason"], d["attention"]) == ("failed", "decision_record_mutated: proposal", True)
    assert w.untouched()


def test_the_handler_does_not_write_a_line_the_decision_schema_would_refuse(tmp_path):
    """The last line of defence behind "refused, not failed": append() itself checks the line it is about to write."""
    w = World(tmp_path)
    sid = w.propose(cap())
    proposal, before = w.history(sid)[0], w.log.read_bytes()
    handler = kyveto.Handler(w.env, kyaction.parse_utc(AT), None, "ctl-veto", "controller", None, None)
    for bad in (dict(proposal, **{"class": "hard_stop"}), dict(proposal, **{"class": "routine"}),
                dict(proposal, notification=None), dict(proposal, rationale=""), dict(proposal, veto_deadline=None)):
        with pytest.raises(kyveto.Unwritable):
            handler.append(bad, "FAILED", "by_test")
        assert schema_errors("surrogate_decision", handler.line(bad, "FAILED", "by_test"))
    with pytest.raises(kyveto.Unwritable):
        handler.append(proposal, "EFFECTIVE", "by_test")              # a veto-class EFFECTIVE line needs effective_at
    nameless = kyveto.Handler(w.env, kyaction.parse_utc(AT), None, "", "controller", None, None)
    with pytest.raises(kyveto.Unwritable):
        nameless.append(proposal, "FAILED", "by_test")
    assert w.log.read_bytes() == before
    for state, effective_at in (("FAILED", None), ("VETOED", None), ("EFFECTIVE", AT), ("EXECUTED", AT)):
        assert_schema("surrogate_decision", handler.append(proposal, state, "by_test", effective_at, {"k": 1}))
    assert isinstance(kyveto.Unwritable("x"), kyaction.ActionError)


# ── owner veto ──

def test_an_owner_veto_before_expiry_is_final(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap(tracker_decision=TD))
    cid = w.veto(sid)
    report = w.tick(BEFORE)
    assert one(report, sid)["outcome"] == "vetoed"
    assert w.states(sid) == ["PENDING_VETO", "VETOED"]
    vetoed = w.history(sid)[-1]
    assert vetoed["by"] == "kyveto" and vetoed["reason"] == "owner_veto" and vetoed["effective_at"] is None
    assert vetoed["detail"]["command"] == cid
    cmd = w.command(cid)
    assert cmd["state"] == "APPLIED" and cmd["result"]["outcome"] == "VETOED" and cmd["result"]["decision"] == sid
    assert_schema("command", cmd)
    for now in (AT, AFTER):
        assert w.tick(now)["decisions"] == []
    assert w.states(sid) == ["PENDING_VETO", "VETOED"] and w.ky_calls() == [] and w.capacity() == ("3\n", "2\n")
    assert sid + ".execute.json" not in w.actions() and sid + ".publish.json" not in w.actions()


def test_a_veto_arriving_in_the_same_tick_as_expiry_wins(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap(tracker_decision=TD))
    cid = w.veto(sid)                                     # queued, never yet seen by a handler
    report = w.tick(AFTER)                                # the window has already expired
    assert one(report, sid)["outcome"] == "vetoed"
    assert w.states(sid) == ["PENDING_VETO", "VETOED"]
    assert w.ky_calls() == [] and w.capacity() == ("3\n", "2\n")
    assert w.command(cid)["state"] == "APPLIED"


def test_an_owner_veto_wins_even_where_the_decision_would_have_failed(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap(), notified=None, notification={"submitted": False, "ts": T_NOTIFY})
    cid = w.veto(sid)
    assert one(w.tick(BEFORE), sid)["outcome"] == "vetoed" and w.command(cid)["state"] == "APPLIED"


def test_an_already_applied_veto_command_still_vetoes(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap())
    cid = w.veto(sid)
    hold(w.run, "veto", "someone")
    assert kycommands.apply(w.run, cid, "someone", lambda c: {"note": "seen"}, in_order=False)[0] == "applied"
    shutil.rmtree(w.run / "locks" / "veto")
    assert one(w.tick(AFTER), sid)["outcome"] == "vetoed"
    assert w.states(sid) == ["PENDING_VETO", "VETOED"] and w.capacity() == ("3\n", "2\n")


# ── CT-07: a line appended after a decision's terminal state is an anomaly the tick itself reports ──

def test_a_vetoed_decision_is_not_resurrected_by_a_later_pending_line(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap())
    cid = w.veto(sid)
    w.tick(BEFORE)
    w.append(w.history(sid)[0])                           # the proposal is appended again after the veto
    report = w.tick(AFTER)
    d = one(report, sid)
    assert (d["outcome"], d["reason"], d["attention"]) == ("vetoed", "terminal_state_is_final", True)
    assert d["anomaly"] == "line_appended_after_terminal_state" and report["attention"] is True
    assert w.states(sid)[-1] == "VETOED" and "EFFECTIVE" not in w.states(sid) and w.capacity() == ("3\n", "2\n")
    assert w.command(cid)["state"] == "APPLIED"


@pytest.mark.parametrize("terminal", ["VETOED", "FAILED"])
@pytest.mark.parametrize("appended,by", [("EXECUTED", kyveto.SURROGATE), ("EXECUTED", "kyveto"),
                                         ("EFFECTIVE", kyveto.SURROGATE), ("PROPOSED", kyveto.SURROGATE)])
def test_a_line_appended_after_a_terminal_state_is_reported_by_the_tick(tmp_path, terminal, appended, by):
    """The reviewer's probe: after VETOED / FAILED a surrogate-appended EXECUTED became the latest state; the
    tick said nothing and only `status` flagged it."""
    w = World(tmp_path)
    if terminal == "VETOED":
        sid = w.propose(cap(tracker_decision=TD))
        w.veto(sid)
    else:
        sid = w.propose(cap(tracker_decision=TD), notification={"submitted": False, "ts": T_NOTIFY})
    w.tick(BEFORE)
    assert w.states(sid) == ["PENDING_VETO", terminal]
    w.append(dict(w.history(sid)[0], state=appended, by=by, effective_at=AT, session="surrogate-2"))
    r = w.cli("status")
    (row,) = json.loads(r.stdout)["decisions"]
    assert r.returncode == 3 and (row["state"], row["latest_line_state"]) == (terminal, appended)
    assert "line_appended_after_terminal_state" in row["anomalies"]
    report = w.tick(AFTER)
    d = one(report, sid)
    assert (d["outcome"], d["reason"]) == (terminal.lower(), "terminal_state_is_final")
    assert d["attention"] is True and d["anomaly"] == "line_appended_after_terminal_state"
    assert report["attention"] is True and w.states(sid) == ["PENDING_VETO", terminal, appended, terminal]
    assert w.history(sid)[-1]["by"] == "kyveto" and w.ky_calls() == [] and w.capacity() == ("3\n", "2\n")
    assert not any(name.startswith("SD-") for name in w.actions())
    assert w.tick(LATER)["decisions"] == []               # the log says the truth again: reported once
    (row,) = json.loads(w.cli("status").stdout)["decisions"]
    assert (row["state"], row["latest_line_state"]) == (terminal, terminal)


def test_a_failed_decision_is_not_resurrected_by_a_corrected_line(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap(tracker_decision=TD), notification={"submitted": False, "ts": T_NOTIFY})
    assert one(w.tick(AT), sid)["reason"] == "notification_not_submitted"
    w.append(dict(w.history(sid)[0], notification={"submitted": True, "ts": T_NOTIFY}))    # "fixed" under the same id
    d = one(w.tick(AFTER), sid)
    assert (d["outcome"], d["reason"], d["attention"]) == ("failed", "terminal_state_is_final", True)
    assert w.states(sid) == ["PENDING_VETO", "FAILED", "PENDING_VETO", "FAILED"]
    assert w.untouched()


def test_an_executed_decision_is_never_executed_again(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap(tracker_decision=TD))
    w.tick(AT)
    (w.run / "KY_WORKERS").write_text("3\n")              # capacity was lowered again afterwards
    w.append(w.history(sid)[0])
    d = one(w.tick(AFTER), sid)
    assert (d["outcome"], d["reason"], d["attention"]) == ("executed", "terminal_state_is_final", True)
    assert w.capacity() == ("3\n", "4\n") and len(w.ky_calls()) == 1
    for name in w.actions():                              # … not even when its action records have gone missing:
        (w.run / "actions" / name).unlink()               # the log's EXECUTED is then a claim nothing backs
    w.append(w.history(sid)[0])
    d = one(w.tick(LATER), sid)
    assert (d["outcome"], d["attention"]) == ("failed", True) and d["reason"].startswith("log_claims_")
    assert w.capacity() == ("3\n", "4\n") and len(w.ky_calls()) == 1 and w.actions() == []
    assert w.tick(LATER)["decisions"] == []


def test_a_veto_of_a_decision_not_yet_in_its_window_waits_for_it(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap(), state="PROPOSED", notification={"submitted": False, "ts": None}, veto_deadline=T_DEADLINE)
    cid = w.veto(sid)
    assert w.tick(BEFORE)["decisions"] == []
    assert w.command(cid)["state"] == "QUEUED" and w.states(sid) == ["PROPOSED"]        # the veto is not lost
    w.append(dict(w.history(sid)[0], state="PENDING_VETO", notification={"submitted": True, "ts": T_NOTIFY}))
    assert one(w.tick(AFTER), sid)["outcome"] == "vetoed"
    assert w.command(cid)["state"] == "APPLIED" and w.capacity() == ("3\n", "2\n")


def test_other_commands_addressed_to_the_veto_role_are_left_queued_for_the_controller(tmp_path):
    w = World(tmp_path)
    cid = kycommands.submit(w.run, "veto", "status", {}, COCKPIT)
    sid = w.propose(cap())
    vid = w.veto(sid)
    report = w.tick(AFTER)
    assert w.command(cid)["state"] == "QUEUED"            # the veto controller applies or rejects it, never the handler
    assert one(report, sid)["outcome"] == "vetoed" and w.command(vid)["state"] == "APPLIED"   # and it blocks no veto


def test_a_named_holder_settles_the_veto_under_its_own_identity(tmp_path):
    w = World(tmp_path)
    hold(w.run, "veto", "ctl-veto")                       # this process holds the role lock; the tick is its child
    sid = w.propose(cap())
    cid = w.veto(sid)
    r = w.cli("tick", "--as", "ctl-veto")
    assert r.returncode == 0, r.stderr
    assert w.states(sid) == ["PENDING_VETO", "VETOED"] and w.history(sid)[-1]["session"] == "ctl-veto"
    assert w.command(cid)["applied_by"] == {"role": "veto", "holder_kind": "controller", "controller_id": "ctl-veto"}
    assert (w.run / "locks" / "veto").is_dir()             # the controller's role lock is not the tick's to release


def test_the_bootstrap_supervisor_may_run_the_handler(tmp_path):
    w = World(tmp_path)
    hold(w.run, "veto", "kyboot-1")
    sid = w.propose(cap())
    r = w.cli("tick", "--as", "kyboot-1", "--holder-kind", "supervisor")
    assert r.returncode == 0, r.stderr
    assert w.action(sid + ".execute")["actor"] == {"role": "veto", "holder_kind": "supervisor",
                                                   "controller_id": "kyboot-1"}
    assert w.states(sid)[-1] == "EXECUTED"
    assert kyaction.parse_utc(w.history(sid)[1]["effective_at"]) >= time.time() - 120     # the real clock's "now"
    assert w.cli("tick", "--holder-kind", "cockpit").returncode == 64


def test_naming_the_holder_from_a_process_that_is_not_its_child_is_refused(tmp_path):
    """CT-05 at the handler: `tick --as <id>` beside the real controller."""
    w = World(tmp_path)
    sid = w.propose(cap())
    with bystander() as (pid, start):
        hold(w.run, "veto", "ctl-veto", pid=pid, start=start)
        r = w.cli("tick", "--as", "ctl-veto")
        assert r.returncode == 75 and "role_lock_not_owned_by_caller" in r.stderr
        with pytest.raises(kyveto.NotHolder):
            w.tick(AT, holder="ctl-veto")
    assert w.states(sid) == ["PENDING_VETO"] and w.untouched()


def test_the_decision_is_re_read_under_its_lock(tmp_path, monkeypatch):
    """Another handler finishes the decision between this tick's first look and its lock: nothing is done twice."""
    w = World(tmp_path)
    sid = w.propose(cap(tracker_decision=TD))
    real = kyaction.acquire_lock

    def raced(run_dir, name, owner_id, **kw):
        if name == "decision." + sid:
            w.append(dict(w.history(sid)[0], state="VETOED", by="kyveto", reason="owner_veto"))
        return real(run_dir, name, owner_id, **kw)

    monkeypatch.setattr(kyaction, "acquire_lock", raced)
    d = one(w.tick(AT), sid)
    assert (d["outcome"], d["state"]) == ("not_pending", "VETOED")
    assert w.states(sid) == ["PENDING_VETO", "VETOED"] and w.ky_calls() == [] and w.capacity() == ("3\n", "2\n")


def test_a_line_with_an_unknown_state_makes_only_its_own_decision_unusable(tmp_path):
    w = World(tmp_path)
    bad = w.propose(cap(builders=7))
    w.append(dict(w.history(bad)[0], state="APPROVED"))
    w.append(w.history(bad)[0])                           # pending again on top of a line nobody can interpret
    good = w.propose(cap(builders=5))
    w.append({"id": "SD-20261011T220000Z-77", "awaiting": "AW-20261011T215900Z-hard-stop", "class": "hard_stop",
              "decision": "owner only"})                  # a hard-stop record carries no decision state
    report = w.tick(AT)
    assert [d["id"] for d in report["decisions"]] == [good] and one(report, good)["outcome"] == "executed"
    assert report["attention"] is True and any(bad in p for p in report["problems"])
    assert not any("-77" in p for p in report["problems"])
    assert w.capacity() == ("5\n", "4\n") and w.states(bad) == ["PENDING_VETO", "APPROVED", "PENDING_VETO"]


def test_a_veto_that_is_too_late_is_rejected_and_says_so(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap())
    w.tick(AT)
    cid = w.veto(sid)
    report = w.tick(AFTER)
    cmd = w.command(cid)
    assert cmd["state"] == "REJECTED" and cmd["result"]["reason"].startswith("too_late")
    assert w.states(sid) == ["PENDING_VETO", "EFFECTIVE", "EXECUTED"]
    assert [c["id"] for c in report["commands"]] == [cid]


def test_a_veto_for_an_unknown_decision_is_rejected(tmp_path):
    w = World(tmp_path)
    w.propose(cap())
    cid = w.veto("SD-20261011T220000Z-999")
    w.tick(BEFORE)
    assert w.command(cid)["state"] == "REJECTED" and w.command(cid)["result"]["reason"] == "unknown_decision"


# ── records the handler cannot answer with a valid line: refused in its own files, never in the log ──

def refused(w, sid, reason, now=AT):
    """The decision is refused with `reason`: reported once with attention, nothing appended, nothing done."""
    before = w.log.read_bytes()
    report = w.tick(now)
    d = one(report, sid)
    assert d["outcome"] == "refused" and d["reason"].startswith(reason) and d["attention"] is True, d
    assert report["attention"] is True and w.log.read_bytes() == before and w.untouched()
    marker = w.refusal(sid)
    assert marker["reason"] == d["reason"] and marker["refused_at"] == now and marker["published"] is False
    assert w.tick(now)["decisions"] == [] and w.log.read_bytes() == before        # once; `status` keeps showing it
    (row,) = [x for x in kyveto.status(w.env, now=now)["decisions"] if x["id"] == sid]
    assert row["refused"] == d["reason"] and row["unresolved"] is True and "anomaly" not in row
    assert kyveto.status(w.env, now=now)["attention"] is True         # … for as long as its awaiting item is open
    aw = w.run / "awaiting" / ("%s.json" % row["awaiting"])
    if isinstance(row["awaiting"], str) and kycommands.AW_RE.match(row["awaiting"]) and aw.is_file():
        aw.rename(w.run / "awaiting" / "dealt-with.json.done")        # the owner (or the cockpit) dealt with the item
        status = kyveto.status(w.env, now=now)
        (row,) = [x for x in status["decisions"] if x["id"] == sid]
        assert row["refused"] == d["reason"] and "unresolved" not in row and status["attention"] is False
        (w.run / "awaiting" / "dealt-with.json.done").rename(aw)
    return d


def test_a_hard_stop_is_never_delegated_and_never_answered_in_the_log(tmp_path):
    """Interface with schemas/surrogate_decision.json: a hard_stop record may only ever be PROPOSED, so the FAILED
    line the handler used to append for one violated the schema. It appends nothing (ruling R3)."""
    w = World(tmp_path)
    sid = w.propose(cap(tracker_decision=TD), **{"class": "hard_stop"})
    (row,) = kyveto.status(w.env, now=AT)["decisions"]    # before any tick: a hard stop that is not PROPOSED
    assert row["hard_stop"] is True and row["anomaly"] == "hard_stop_record_outside_proposed"
    refused(w, sid, "hard_stop_never_delegated")
    assert w.states(sid) == ["PENDING_VETO"]
    status = kyveto.status(w.env, now=AT)
    (row,) = status["decisions"]
    assert row["hard_stop"] is True and row["refused"] == "hard_stop_never_delegated"
    assert status["hard_stops"] == [sid] and status["attention"] is True      # … and it stays visible as unresolved


def test_status_keeps_an_open_hard_stop_visible_until_the_owner_has_dealt_with_it(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap(), **{"class": "hard_stop", "state": "PROPOSED", "veto_deadline": None,
                              "notification": {"submitted": True, "ts": T_NOTIFY}})
    assert w.tick(AT)["decisions"] == [] and w.states(sid) == ["PROPOSED"]        # the handler does nothing with it
    status = kyveto.status(w.env, now=AT)
    assert status["hard_stops"] == [sid] and status["attention"] is True and "anomaly" not in status["decisions"][0]
    aw = w.run / "awaiting" / (w.history(sid)[0]["awaiting"] + ".json")
    (w.run / "awaiting" / "done").mkdir()
    aw.rename(w.run / "awaiting" / "done" / aw.name)      # the owner decided the item
    status = kyveto.status(w.env, now=AT)
    assert status["hard_stops"] == [] and status["attention"] is False


@pytest.mark.parametrize("over,reason", [
    ({"class": "routine"}, "class_not_veto: routine"), ({"class": "urgent"}, "class_not_veto"),
    ({"class": None}, "class_not_veto"),
    ({"notification": {"submitted": "true", "ts": T_NOTIFY}}, "record_malformed: notification"),
    ({"notification": {"submitted": 1, "ts": T_NOTIFY}}, "record_malformed: notification"),
    ({"notification": {"ts": T_NOTIFY}}, "record_malformed: notification"),
    ({"notification": {"submitted": True}}, "record_malformed: notification"),
    ({"notification": None}, "record_malformed: notification"),
    ({"notification": "submitted"}, "record_malformed: notification"),
    ({"veto_deadline": None}, "record_malformed: veto_deadline"),
    ({"veto_deadline": "soon"}, "record_malformed: veto_deadline"),
    ({"veto_deadline": "2026-10-11 22:30:00"}, "record_malformed: veto_deadline"),
    ({"veto_deadline": 1791757800}, "record_malformed: veto_deadline"),
    ({"authority": None}, "record_malformed: authority"), ({"authority": {}}, "record_malformed: authority"),
    ({"authority": {"source_commit": C1}}, "record_malformed: authority"),
    ({"authority": "e709f60d7"}, "record_malformed: authority"),
    ({"authority": {"source_commit": C1, "entrypoints_digest": E1, "also": 1}}, "record_malformed: authority"),
    ({"awaiting": "the capacity question"}, "record_malformed: awaiting"),
    ({"awaiting": None}, "record_malformed: awaiting"),
    ({"rationale": ""}, "record_malformed: rationale"), ({"decision": None}, "record_malformed: decision"),
    ({"evidence": "run/JOURNAL.md"}, "record_malformed: evidence"), ({"evidence": [1]}, "record_malformed: evidence"),
    ({"effective_at": "later"}, "record_malformed: effective_at"),
])
def test_a_record_the_handler_could_not_answer_validly_is_refused_not_failed(tmp_path, over, reason):
    w = World(tmp_path)
    sid = w.propose(cap(tracker_decision=TD), **over)
    proposal = w.history(sid)[0]
    assert schema_errors("surrogate_decision", proposal), "the case is a valid record after all"
    refused(w, sid, reason)
    assert w.states(sid) == ["PENDING_VETO"]


@pytest.mark.parametrize("target,bind", [("not an object", False), (None, False), ({"builders": 6, "verifiers": 4}, False),
                                         (cap(), False), (dict(cap(), fingerprint=""), False),
                                         (dict(cap(), fingerprint="abc"), False), (dict(cap(), fingerprint=7), False)])
def test_a_veto_target_without_kind_and_fingerprint_is_refused(tmp_path, target, bind):
    w = World(tmp_path)
    sid = w.propose(target, bind=bind)
    refused(w, sid, "record_malformed: target")


def test_an_owner_veto_of_a_refused_record_is_answered(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap(), **{"class": "hard_stop"})
    cid = w.veto(sid)
    report = w.tick(BEFORE)
    assert one(report, sid)["outcome"] == "refused"
    cmd = w.command(cid)
    assert cmd["state"] == "APPLIED" and cmd["result"]["outcome"] == "REFUSED" and "hard_stop" in cmd["result"]["note"]
    assert w.states(sid) == ["PENDING_VETO"] and w.ky_calls() == [] and w.capacity() == ("3\n", "2\n")
    assert w.tick(AT)["commands"] == []                   # settled once


def test_an_unreadable_deadline_never_expires_into_effect(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap(), veto_deadline="2026-13-45T99:99:99Z")       # the schema's shape, and no moment in time
    d = one(w.tick(LATER), sid)
    assert (d["outcome"], d["reason"], d["attention"]) == ("failed", "veto_deadline_unreadable", True)
    assert w.capacity() == ("3\n", "2\n")


# ── holds ──

def test_the_global_hold_keeps_the_decision_pending_without_failing_it(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap(tracker_decision=TD))
    (w.root / "HOLD").write_text("certification\n")
    before = tree(w.run)
    for now in (AT, AFTER):
        d = one(w.tick(now), sid)
        assert d["outcome"] == "held" and d["reasons"] == ["HOLD"]
    assert tree(w.run) == before and w.ky_calls() == [] and w.states(sid) == ["PENDING_VETO"]
    (w.root / "HOLD").unlink()
    assert one(w.tick(LATER), sid)["outcome"] == "executed"
    assert w.history(sid)[-1]["effective_at"] == LATER                 # effective when it was published, not before


def test_an_owner_veto_is_still_honoured_under_the_global_hold(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap())
    (w.root / "HOLD").write_text("x\n")
    w.veto(sid)
    assert one(w.tick(AFTER), sid)["outcome"] == "vetoed"


@pytest.mark.parametrize("applied", [True, False])
def test_an_owner_pause_keeps_the_decision_pending_until_the_owner_resumes(tmp_path, applied):
    w = World(tmp_path)
    sid = w.propose(cap())
    p = kycommands.submit(w.run, "campaign", "pause", {}, COCKPIT)
    if applied:
        apply_campaign(w.run, p)
    d = one(w.tick(AT), sid)
    assert d["outcome"] == "held" and d["reasons"] == ["owner_paused" if applied else "owner_pause_pending"]
    assert w.states(sid) == ["PENDING_VETO"] and w.capacity() == ("3\n", "2\n")
    r = kycommands.submit(w.run, "campaign", "resume", {}, COCKPIT)
    if applied:
        assert one(w.tick(AFTER), sid)["outcome"] == "held"            # a queued resume does not end an applied pause
        apply_campaign(w.run, r)
    assert one(w.tick(LATER), sid)["outcome"] == "executed"


def test_a_pause_whose_handler_failed_still_holds_every_decision(tmp_path):
    """CT-10 at the handler: the owner's pause was REJECTED "handler_error"; nothing may act against it."""
    w = World(tmp_path)
    sid = w.propose(cap())
    p = kycommands.submit(w.run, "campaign", "pause", {}, COCKPIT)
    hold(w.run, "campaign", "ctl-campaign")
    assert kycommands.apply(w.run, p, "ctl-campaign", lambda c: (_ for _ in ()).throw(OSError("x")))[0] == "rejected"
    d = one(w.tick(AT), sid)
    assert d["outcome"] == "held" and d["reasons"] == ["owner_pause_pending"] and w.states(sid) == ["PENDING_VETO"]
    apply_campaign(w.run, kycommands.submit(w.run, "campaign", "resume", {}, COCKPIT))
    assert one(w.tick(LATER), sid)["outcome"] == "executed"


def test_an_unreadable_command_queue_holds_every_decision(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap())
    (w.run / "commands").mkdir()
    (w.run / "commands" / "20261011T220500Z-torn.json").write_text("{")       # it might have been a veto or a pause
    report = w.tick(AFTER)
    d = one(report, sid)
    assert d["outcome"] == "held" and d["reasons"] == ["command_queue_unreadable"]
    assert report["attention"] is True and w.states(sid) == ["PENDING_VETO"] and w.capacity() == ("3\n", "2\n")


def test_stop_veto_holds_execution(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap())
    (w.run / "STOP_veto").write_text("x\n")
    assert one(w.tick(AFTER), sid)["reasons"] == ["STOP_veto"]
    assert w.states(sid) == ["PENDING_VETO"]


# ── the recheck at expiry; CT-11: every failure tells the owner ──

def failed(w, sid, reason, now=AT, **tick):
    """The decision is FAILED with `reason`: one schema-valid line, attention raised, nothing executed."""
    report = w.tick(now, **tick)
    d = one(report, sid)
    assert d["outcome"] == "failed" and d["reason"].startswith(reason), d
    assert d["attention"] is True and report["attention"] is True      # the controller notifies the owner
    last = w.history(sid)[-1]
    assert (last["state"], last["by"], last["reason"]) == ("FAILED", "kyveto", d["reason"])
    assert w.capacity() == ("3\n", "2\n") and sid + ".execute.json" not in w.actions()
    assert w.tick(now, **tick)["decisions"] == []                       # final: reported once, never retried
    return d


def test_a_failed_decision_makes_the_tick_exit_with_attention(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap(tracker_decision=TD))
    (w.run / "KY_WORKERS").write_text("5\n")
    r = w.cli("tick")
    assert r.returncode == 3, r.stderr
    d = one(json.loads(r.stdout), sid)
    assert (d["outcome"], d["reason"], d["attention"]) == ("failed", "target_changed", True)
    assert w.cli("tick").returncode == 0                  # … once


def test_a_target_changed_on_disk_since_the_proposal_is_refused(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap(tracker_decision=TD))
    (w.run / "KY_WORKERS").write_text("5\n")              # someone changed capacity during the window
    report = w.tick(AT)
    d = one(report, sid)
    assert (d["outcome"], d["reason"], d["attention"]) == ("failed", "target_changed", True)
    assert w.states(sid) == ["PENDING_VETO", "FAILED"]
    assert w.capacity() == ("5\n", "2\n") and w.ky_calls() == [] and w.actions() == []


def test_target_parameters_changed_under_the_same_fingerprint_are_refused(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap(builders=4), seen=None)
    line = w.history(sid)[0]
    edited = dict(line, target=dict(line["target"], builders=7))        # same recorded fingerprint, new request
    w.log.write_text(json.dumps(edited) + "\n")
    w.see(sid)                                            # this is the proposal the handler first saw
    failed(w, sid, "target_changed")


def test_a_later_line_that_rebinds_the_target_is_refused(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap(builders=4))
    line = w.history(sid)[0]
    target = cap(builders=7)
    target["fingerprint"] = kyveto.fingerprint(target, w.env)          # a self-consistent, different target
    w.append(dict(line, target=target))
    failed(w, sid, "decision_record_mutated: target")


@pytest.mark.parametrize("field,value", [
    ("decision", "raise capacity to the maximum"),         # what would be published is not what the owner was told
    ("evidence", ["run/SOMETHING_ELSE.md"]), ("notification", {"submitted": True, "ts": iso(-600)}),
])
def test_a_later_line_that_changes_what_the_owner_was_told_is_refused(tmp_path, field, value):
    w = World(tmp_path)
    sid = w.propose(cap(tracker_decision=TD))
    w.append(dict(w.history(sid)[0], **{field: value}))
    failed(w, sid, "decision_record_mutated: " + field)
    assert w.ky_calls() == []


def test_a_later_line_that_shortens_the_window_gains_nothing_and_is_refused(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap(), veto_deadline=iso(3600))
    w.append(dict(w.history(sid)[0], veto_deadline=T_DEADLINE))
    d = one(w.tick(AT), sid)
    assert d["outcome"] == "pending" and d["seconds_remaining"] == 1800        # the PROPOSAL's deadline counts
    failed(w, sid, "decision_record_mutated: veto_deadline", now=iso(3600))


@pytest.mark.parametrize("authority", [
    {"source_commit": C2, "entrypoints_digest": E1}, {"source_commit": C1, "entrypoints_digest": E2},
])
def test_a_changed_authority_is_refused(tmp_path, authority):
    w = World(tmp_path)
    sid = w.propose(cap(tracker_decision=TD), authority=authority)
    failed(w, sid, "authority_changed")
    assert w.ky_calls() == []


def test_the_authorised_bundle_changed_during_the_window(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap())
    w.authorise(C2, E2)                                   # a successor bundle was activated meanwhile
    failed(w, sid, "authority_changed")


# ── ruling R5 / R3: the authority reaches the handler; an authority nobody can establish HOLDS, it does not fail ──

@pytest.mark.parametrize("state", ["missing", "torn", "no-field", "commit-only", "short-commit"])
def test_an_authority_that_cannot_be_established_holds_the_decision(tmp_path, state):
    """The reviewer's probe: every expired decision became terminal FAILED authority_unknown, without attention."""
    w = World(tmp_path)
    sid = w.propose(cap(tracker_decision=TD))
    other = w.propose(cap(builders=5))
    path = w.run / "PLANNER_STATE.json"
    good = path.read_text()
    if state == "missing":
        path.unlink()
    elif state == "torn":
        path.write_text("{")
    elif state == "no-field":
        path.write_text(json.dumps({"schema": "ky.role_state/1"}))
    elif state == "commit-only":
        path.write_text(json.dumps({"authorised_source": C1}))
    else:
        path.write_text(json.dumps({"authorised_source": {"source_commit": "e709f60d7", "entrypoints_digest": E1}}))
    for now in (AT, AFTER):
        report = w.tick(now)
        for held in (sid, other):
            d = one(report, held)
            assert d["outcome"] == "held" and d["reasons"] == ["authority_unknown"] and "attention" not in d
        assert report["attention"] is True and report["authority"]["source"] == "unknown"
        unknown = [p for p in report["problems"] if p.startswith("authority_unknown")]
        assert len(unknown) == 1 and sid in unknown[0] and other in unknown[0]      # ONE attention item for all of them
    assert w.states(sid) == ["PENDING_VETO"] and w.states(other) == ["PENDING_VETO"] and w.untouched()
    assert one(w.tick(BEFORE), sid)["outcome"] == "pending"            # inside the window nobody needs it yet
    path.write_text(good)                                              # the authority is established again
    report = w.tick(LATER)
    assert one(report, sid)["outcome"] == "executed" and report["authority"]["source"] == "planner_state"
    assert not any(p.startswith("authority_unknown") for p in report["problems"])
    assert one(report, other)["reason"] == "target_changed"            # (the first one changed the pool meanwhile)


def test_the_controller_passes_the_authority_it_established(tmp_path):
    """Ruling R5: kyloop's VetoController gives every tick the authority (from the activation chain's terminal
    link, else PLANNER_STATE.json authorised_source). What it passes wins over the state file."""
    w = World(tmp_path)
    (w.run / "PLANNER_STATE.json").unlink()
    sid = w.propose(cap())
    report = w.tick(AT, authorised={"source_commit": C1, "entrypoints_digest": E1})
    assert one(report, sid)["outcome"] == "executed" and report["authority"] == {
        "source_commit": C1, "entrypoints_digest": E1, "source": "arguments"}
    w2 = World(tmp_path / "second")                                    # the state file says C1; the controller says C2
    sid2 = w2.propose(cap())
    failed(w2, sid2, "authority_changed", authorised={"source_commit": C2, "entrypoints_digest": E1})
    w3 = World(tmp_path / "third")                                     # the controller could establish neither source
    sid3 = w3.propose(cap())
    report = w3.tick(AT, authorised=kyveto.UNKNOWN)                    # … although the state file would have answered
    assert one(report, sid3)["reasons"] == ["authority_unknown"] and report["authority"]["source"] == "unknown"
    assert w3.states(sid3) == ["PENDING_VETO"]
    for junk in ("C1", {"source_commit": C1}, {"source_commit": "abc", "entrypoints_digest": E1}, [C1, E1], 7):
        with pytest.raises(ValueError):
            w3.tick(AT, authorised=junk)
    assert w3.states(sid3) == ["PENDING_VETO"] and w3.untouched()


def test_a_state_file_that_an_activation_chain_has_overtaken_is_not_the_authority(tmp_path):
    """Nothing updates PLANNER_STATE.json when a bundle change is activated (a carried obligation). Until somebody
    does, the state file's answer is stale: decisions under the OLD bundle are held, not waved through."""
    w = World(tmp_path)
    sid = w.propose(cap())                                             # proposed under C1
    previous_record(w, new_commit=C2, new_manifest=M2)                 # … and then the bundle moved on to C2
    report = w.tick(AT)
    assert one(report, sid)["reasons"] == ["authority_unknown"]
    assert report["authority"]["source"] == "planner_state_superseded" and report["attention"] is True
    assert w.states(sid) == ["PENDING_VETO"] and w.untouched()
    failed(w, sid, "authority_changed", authorised={"source_commit": C2, "entrypoints_digest": E2})    # told, it decides
    w2 = World(tmp_path / "second")
    sid2 = w2.propose(cap())
    (w2.run / "ACTIVATION_RECORD.7.json").write_text("{")              # a chain nobody can validate
    report = w2.tick(AT)
    assert one(report, sid2)["reasons"] == ["authority_unknown"]
    assert report["authority"]["source"] == "activation_chain_invalid"


def test_authority_given_as_arguments_takes_precedence_over_the_state_file(tmp_path):
    w = World(tmp_path)
    (w.run / "PLANNER_STATE.json").unlink()
    sid = w.propose(cap())
    r = w.cli("tick", "--authorised-commit", C1, "--entrypoints-digest", E1)
    assert r.returncode == 0, r.stderr
    report = json.loads(r.stdout)
    assert one(report, sid)["outcome"] == "executed" and report["authority"]["source"] == "arguments"
    w2 = World(tmp_path / "second")                                    # the state file says C1; the arguments say C2
    sid2 = w2.propose(cap())
    r = w2.cli("tick", "--authorised-commit", C2, "--entrypoints-digest", E1)
    assert r.returncode == 3 and one(json.loads(r.stdout), sid2)["reason"] == "authority_changed"
    assert w2.cli("tick", "--authorised-commit", C1).returncode == 64          # both or neither


# ── publication ──

READBACKS = {"done": lambda record: ("done", {"observed": "tracker readback"}),
             "not_done": lambda record: ("not_done", "no such tracker event")}


def status_row(w, sid):
    """→ (exit status, report, the decision's row) of the real `kyveto.py status`."""
    r = w.cli("status")
    report = json.loads(r.stdout)
    (row,) = [x for x in report["decisions"] if x["id"] == sid]
    return r.returncode, report, row


@pytest.mark.parametrize("record,answer", [
    (None, False),                                                                   # the handler never began
    ({"state": "DONE", "target": {"tracker_decision": None}}, False),                # nothing was to be published
    ({"state": "DONE", "target": {"tracker_decision": "D-41", "outcome": "approved"}}, True),
    ({"state": "INTENDED", "target": {"tracker_decision": "D-41"}, "result": None}, "unknown"),
    ({"state": "FAILED", "target": {"tracker_decision": "D-41"}, "result": {"exit_status": 3}}, "unknown"),
    ({"state": "FAILED", "target": {"tracker_decision": "D-41"}, "result": {"published": "unknown"}}, "unknown"),
    ({"state": "FAILED", "target": {"tracker_decision": "D-41"}, "result": {"published": None}}, "unknown"),
    ({"state": "FAILED", "target": {"tracker_decision": "D-41"}, "result": {"published": False}}, False),
    ({"state": "FAILED", "target": {"tracker_decision": "D-41"}, "result": None}, "unknown"),
    ({"state": "DONE", "target": {}}, "unknown"), ({"state": "DONE", "target": None}, "unknown"),
])
def test_publication_has_three_answers(record, answer):
    """C2-01: published / not published / unknown — and unknown is whatever is not proven either way."""
    got = kyveto.publication(record)
    assert got == answer and type(got) is type(answer)


def test_a_publication_ky_refused_is_failed_never_executed_and_not_called_unpublished(tmp_path):
    """C2-06: a non-zero exit of `ky decide` proves nothing about the tracker. Without a readback the decision is
    FAILED (nothing is executed, nothing retried) and its publication is UNKNOWN — said in the line, the row and
    `status`, never "not published"."""
    w = World(tmp_path)
    w.ky_says("rc", 3)
    sid = w.propose(cap(tracker_decision=TD))
    report = w.tick(AT)
    d = one(report, sid)
    assert d["outcome"] == "failed" and d["reason"] == "publication_failed: rc=3"
    assert d["attention"] is True and d["published"] == "unknown" and report["attention"] is True
    assert w.states(sid) == ["PENDING_VETO", "FAILED"]                 # never EFFECTIVE, never EXECUTED
    assert w.history(sid)[-1]["detail"] == {"published": "unknown"}
    assert w.capacity() == ("3\n", "2\n")
    publish = w.action(sid + ".publish")
    assert publish["state"] == "INTENDED" and len(publish["reconciliations"]) == 1     # unfinished: nothing is known
    seen = publish["reconciliations"][-1]
    assert seen["outcome"] == "unknown" and seen["detail"]["ky_exit_status"] == 3
    assert_schema("action", publish)
    assert w.actions() == [sid + ".publish.json"]                      # the executor was never begun
    w.ky_says("rc", 0)
    assert w.tick(AFTER)["decisions"] == []                            # a failed proposal is not retried
    assert len(w.ky_calls()) == 1 and w.states(sid) == ["PENDING_VETO", "FAILED"]
    rc, status, row = status_row(w, sid)
    assert rc == 3 and row["published"] == "unknown" and row["unresolved"] is True
    assert status["publication_unknown"] == [sid] and status["attention"] is True


def test_a_readback_decides_what_a_refusing_ky_left_behind(tmp_path):
    """C2-06: "unless a readback proves otherwise" — in both directions."""
    w = World(tmp_path)
    w.ky_says("rc", 3)
    sid = w.propose(cap(tracker_decision=TD))
    d = one(w.tick(AT, publish_observer=READBACKS["not_done"]), sid)
    assert d["outcome"] == "failed" and d["reason"] == "publication_failed: rc=3" and "published" not in d
    assert "detail" not in w.history(sid)[-1] and w.capacity() == ("3\n", "2\n")
    publish = w.action(sid + ".publish")
    assert publish["state"] == "FAILED" and publish["result"]["exit_status"] == 3
    assert publish["result"]["published"] is False
    rc, status, row = status_row(w, sid)
    assert rc == 0 and row["published"] is False and "unresolved" not in row and status["publication_unknown"] == []
    other = w.propose(cap(builders=5, tracker_decision=TD))            # the tracker did record it: carried out
    assert one(w.tick(AT, publish_observer=READBACKS["done"]), other)["outcome"] == "executed"
    assert w.states(other) == ["PENDING_VETO", "EFFECTIVE", "EXECUTED"] and w.capacity() == ("5\n", "4\n")
    assert w.action(other + ".publish")["state"] == "DONE" and len(w.ky_calls()) == 2   # one call each, no retry


def test_a_missing_ky_is_refused_before_anything_is_recorded(tmp_path):
    w = World(tmp_path)
    (w.root / "bin" / "ky").unlink()
    sid = w.propose(cap(tracker_decision=TD))
    failed(w, sid, "publication_unavailable")
    assert w.actions() == []


@pytest.mark.parametrize("td", ["D-41", {"id": "D-41"}, {"id": "41", "outcome": "approved"},
                                {"id": "D-41", "outcome": "--force"}, {"id": "D-41", "outcome": ""}, 41, []])
def test_a_tracker_decision_the_handler_cannot_publish_exactly_is_refused(tmp_path, td):
    w = World(tmp_path)
    sid = w.propose(cap(tracker_decision=td))
    failed(w, sid, "tracker_decision_malformed")
    assert w.ky_calls() == []


def ky_never_answers(w, monkeypatch):
    """`ky decide` is started, records its call and then gives no exit status within the handler's timeout.

    C2-07: the handler's timeout runs from the moment the child is spawned, so on a loaded machine a 0.5 s
    timeout could expire before the double had even recorded its call. Here the very same real process is run
    under the very same timeout, and kyveto still meets a real subprocess.TimeoutExpired — only the timeout's
    clock starts once the double's call is on record. Nothing else that calls subprocess.run is changed."""
    w.ky_says("sleep", 600)
    w.environ["KYVETO_KY_TIMEOUT_S"] = "0.5"
    real, ky, calls = subprocess.run, str(w.root / "bin" / "ky"), w.root / "fake_ky" / "calls.jsonl"

    def run(argv, **kw):
        if not (isinstance(argv, list) and argv and argv[0] == ky and kw.get("timeout")):
            return real(argv, **kw)
        before = len(w.ky_calls())
        p = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=kw.get("env"),
                             stdin=kw.get("stdin"))
        try:
            deadline = time.time() + 120
            while (not calls.exists() or len(w.ky_calls()) <= before) and p.poll() is None:
                assert time.time() < deadline, "the ky double never recorded its call"
                time.sleep(0.01)
            out, err = p.communicate(timeout=kw["timeout"])
        except BaseException:                             # TimeoutExpired included: as subprocess.run does
            p.kill()
            p.communicate()
            raise
        return subprocess.CompletedProcess(argv, p.returncode, out, err)

    monkeypatch.setattr(kyveto.subprocess, "run", run)


def unknown_publication(w, monkeypatch, **target):
    """A decision whose `ky decide` timed out: `<id>.publish` INTENDED, the tick blocked. → its id."""
    ky_never_answers(w, monkeypatch)
    sid = w.propose(cap(tracker_decision=TD, **target))
    report = w.tick(AT)
    d = one(report, sid)
    assert (d["outcome"], d["reason"]) == ("blocked", "publication_unreconciled")
    assert report["attention"] is True and w.states(sid) == ["PENDING_VETO"]
    assert w.action(sid + ".publish")["state"] == "INTENDED" and w.capacity() == ("3\n", "2\n")
    assert len(w.ky_calls()) == 1                                       # it was really started, once
    return sid


def test_ky_that_does_not_answer_leaves_the_publication_unknown_and_is_not_repeated(tmp_path, monkeypatch):
    w = World(tmp_path)
    sid = unknown_publication(w, monkeypatch)
    (w.root / "fake_ky" / "sleep").unlink()
    assert one(w.tick(AFTER), sid)["reason"] == "publication_unreconciled"
    assert len(w.ky_calls()) == 1                                       # unknown never permits a blind retry
    assert w.action(sid + ".publish")["reconciliations"][-1]["outcome"] == "unknown"
    rc, status, row = status_row(w, sid)                                # C2-01: and `status` does not call it unpublished
    assert rc == 3 and row["published"] == "unknown" and row["unresolved"] is True
    assert status["publication_unknown"] == [sid]


# ── C2-01: publication has three answers; unknown is never reported as "not published" ──

def test_a_veto_after_ky_timed_out_says_the_publication_is_unknown_until_it_is_reconciled(tmp_path, monkeypatch):
    """The reviewer's probe: `ky decide` gave no exit status, the owner then vetoed — the line said
    published:false, the row carried no attention and nothing ever mentioned it again, while the tracker may hold
    a delegated approval the owner vetoed."""
    w = World(tmp_path)
    sid = unknown_publication(w, monkeypatch)
    cid = w.veto(sid)
    report = w.tick(AFTER)
    d = one(report, sid)
    assert (d["outcome"], d["published"], d["attention"]) == ("vetoed", "unknown", True)
    assert report["attention"] is True
    assert w.states(sid) == ["PENDING_VETO", "VETOED"] and w.capacity() == ("3\n", "2\n")
    assert w.history(sid)[-1]["detail"] == {"command": cid, "published": "unknown"}
    assert w.command(cid)["state"] == "APPLIED" and len(w.ky_calls()) == 1
    assert w.action(sid + ".publish")["state"] == "INTENDED"            # never closed as "not published"
    for _ in range(2):                                                  # final for the tick; unresolved for `status`
        assert w.tick(LATER)["decisions"] == []
        rc, status, row = status_row(w, sid)
        assert rc == 3 and status["attention"] is True and status["publication_unknown"] == [sid]
        assert (row["state"], row["published"], row["unresolved"]) == ("VETOED", "unknown", True)
    # … until the publish record is reconciled: the tracker does hold the approval the owner vetoed
    report = w.tick(LATER, publish_observer=READBACKS["done"])
    d = one(report, sid)
    assert (d["outcome"], d["reason"], d["published"], d["attention"]) == (
        "vetoed", "publication_reconciled", True, True)
    assert report["attention"] is True and w.states(sid) == ["PENDING_VETO", "VETOED"]
    assert len(w.ky_calls()) == 1 and w.capacity() == ("3\n", "2\n")   # reconciled, never re-published or executed
    rc, status, row = status_row(w, sid)
    assert rc == 0 and row["published"] is True and "unresolved" not in row and status["publication_unknown"] == []
    assert w.tick(LATER, publish_observer=READBACKS["done"])["decisions"] == []          # reported once


def test_a_failed_recheck_after_ky_timed_out_says_the_publication_is_unknown(tmp_path, monkeypatch):
    """The same probe through the recheck: FAILED target_changed carried no publication flag at all."""
    w = World(tmp_path)
    sid = unknown_publication(w, monkeypatch)
    (w.run / "KY_WORKERS").write_text("5\n")                           # the target changed while nobody knew
    report = w.tick(AFTER)
    d = one(report, sid)
    assert (d["outcome"], d["reason"], d["published"], d["attention"]) == ("failed", "target_changed", "unknown", True)
    assert w.states(sid) == ["PENDING_VETO", "FAILED"] and w.history(sid)[-1]["detail"] == {"published": "unknown"}
    assert w.capacity() == ("5\n", "2\n") and len(w.ky_calls()) == 1 and sid + ".execute.json" not in w.actions()
    assert w.action(sid + ".publish")["state"] == "INTENDED"
    assert w.tick(LATER)["decisions"] == []
    rc, status, row = status_row(w, sid)
    assert rc == 3 and (row["state"], row["published"], row["unresolved"]) == ("FAILED", "unknown", True)
    # a readback that proves the tracker holds nothing closes it without an alarm
    report = w.tick(LATER, publish_observer=READBACKS["not_done"])
    d = one(report, sid)
    assert (d["outcome"], d["reason"], d["published"]) == ("failed", "publication_reconciled", False)
    assert "attention" not in d and report["attention"] is False
    publish = w.action(sid + ".publish")
    assert publish["state"] == "FAILED" and publish["result"]["published"] is False
    rc, status, row = status_row(w, sid)
    assert rc == 0 and row["published"] is False and "unresolved" not in row
    assert w.tick(LATER, publish_observer=READBACKS["not_done"])["decisions"] == []


@pytest.mark.parametrize("readback,published", [("done", True), ("not_done", False), ("unknown", "unknown"),
                                                ("raises", "unknown")])
def test_a_veto_reads_the_unknown_publication_back_before_it_answers(tmp_path, monkeypatch, readback, published):
    w = World(tmp_path)
    sid = unknown_publication(w, monkeypatch)
    cid = w.veto(sid)
    observer = READBACKS.get(readback) or (lambda record: ("unknown", "tracker unreachable") if readback == "unknown"
                                           else 1 / 0)
    report = w.tick(AFTER, publish_observer=observer)
    d = one(report, sid)
    assert d["outcome"] == "vetoed" and w.history(sid)[-1]["detail"] == {"command": cid, "published": published}
    assert d.get("published", False) == published and d.get("attention", False) is (published is not False)
    assert report["attention"] is (published is not False)
    assert w.action(sid + ".publish")["state"] == {True: "DONE", False: "FAILED", "unknown": "INTENDED"}[published]
    assert len(w.ky_calls()) == 1 and w.capacity() == ("3\n", "2\n") and sid + ".execute.json" not in w.actions()


def test_a_refused_record_carries_the_unknown_publication_too(tmp_path, monkeypatch):
    w = World(tmp_path)
    sid = unknown_publication(w, monkeypatch)
    w.append(dict(w.history(sid)[-1], rationale=""))                    # a line the handler cannot answer validly
    d = one(w.tick(AFTER), sid)
    assert (d["outcome"], d["published"], d["attention"]) == ("refused", "unknown", True)
    assert w.refusal(sid)["published"] == "unknown"
    # the readback pass settles FINISHED decisions only: a refused record stays the owner's, unresolved in `status`
    assert w.tick(LATER, publish_observer=READBACKS["done"])["decisions"] == []
    assert w.action(sid + ".publish")["state"] == "INTENDED"
    rc, status, row = status_row(w, sid)
    assert rc == 3 and row["published"] == "unknown" and row["unresolved"] is True and row["refused"]


# ── crashes: a real SIGKILL in a real process (the real clock), recovered by the next tick ──

def test_restart_between_begin_and_execution_reconciles_then_executes_once(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap(tracker_decision=TD))
    crashed = w.crash("before-execute", "tick")
    assert crashed.returncode == -signal.SIGKILL, crashed.stderr
    assert w.states(sid) == ["PENDING_VETO", "EFFECTIVE"]
    assert w.action(sid + ".execute")["state"] == "INTENDED" and w.capacity() == ("3\n", "2\n")
    assert (w.run / "locks" / ("decision." + sid)).is_dir()            # the dead handler's locks are still there
    assert (w.run / "locks" / "veto").is_dir()
    effective_at = w.history(sid)[1]["effective_at"]
    assert time.time() - 120 <= kyaction.parse_utc(effective_at) <= time.time()         # the wall clock's, not a caller's
    report = w.tick(AFTER)
    assert one(report, sid)["outcome"] == "executed"
    assert w.states(sid) == ["PENDING_VETO", "EFFECTIVE", "EXECUTED"]
    rec = w.action(sid + ".execute")
    assert rec["state"] == "DONE" and [r["outcome"] for r in rec["reconciliations"]] == ["not_done"]
    assert w.capacity() == ("6\n", "4\n") and len(w.ky_calls()) == 1   # published once, before the crash
    assert w.history(sid)[-1]["effective_at"] == effective_at          # when it WAS made effective
    assert w.tick(LATER)["decisions"] == []


def test_restart_after_the_executor_ran_observes_the_effect_instead_of_repeating_it(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap())
    crashed = w.crash("after-execute", "tick")
    assert crashed.returncode == -signal.SIGKILL, crashed.stderr
    assert w.capacity() == ("6\n", "4\n") and w.action(sid + ".execute")["state"] == "INTENDED"
    inodes = [(w.run / n).stat().st_ino for n in ("KY_WORKERS", "KY_VERIFIERS")]
    assert one(w.tick(AFTER), sid)["outcome"] == "executed"
    rec = w.action(sid + ".execute")
    assert rec["state"] == "DONE" and [r["outcome"] for r in rec["reconciliations"]] == ["done"]
    assert [(w.run / n).stat().st_ino for n in ("KY_WORKERS", "KY_VERIFIERS")] == inodes       # not rewritten
    assert w.states(sid) == ["PENDING_VETO", "EFFECTIVE", "EXECUTED"]


def test_a_crash_between_the_two_capacity_files_is_reconciled_as_one_action(tmp_path):
    """CT-08: KY_WORKERS and KY_VERIFIERS are one effect under one action record. Killed after the first file:
    the record is unfinished, its reconciliation sees the pair incomplete, and the executor finishes it."""
    w = World(tmp_path)
    sid = w.propose(cap())
    crashed = w.crash("between-files", "tick")
    assert crashed.returncode == -signal.SIGKILL, crashed.stderr
    assert w.capacity() == ("6\n", "2\n")                              # half the pair
    rec = w.action(sid + ".execute")
    assert rec["state"] == "INTENDED" and rec["target"]["builders"] == 6 and rec["target"]["verifiers"] == 4
    assert w.states(sid) == ["PENDING_VETO", "EFFECTIVE"]
    worker_inode = (w.run / "KY_WORKERS").stat().st_ino
    assert one(w.tick(AFTER), sid)["outcome"] == "executed"
    rec = w.action(sid + ".execute")
    assert rec["state"] == "DONE" and rec["reconciliations"][0]["outcome"] == "not_done"
    assert rec["reconciliations"][0]["detail"]["incomplete"] == ["KY_VERIFIERS"]
    assert rec["result"]["KY_WORKERS"]["written"] is False and rec["result"]["KY_VERIFIERS"]["written"] is True
    assert w.capacity() == ("6\n", "4\n") and (w.run / "KY_WORKERS").stat().st_ino == worker_inode
    assert w.states(sid) == ["PENDING_VETO", "EFFECTIVE", "EXECUTED"]


@pytest.mark.parametrize("point,calls", [("before-publish", 0), ("after-publish", 1)])
def test_restart_inside_the_publication_never_publishes_blindly(tmp_path, point, calls):
    w = World(tmp_path)
    sid = w.propose(cap(tracker_decision=TD))
    crashed = w.crash(point, "tick")
    assert crashed.returncode == -signal.SIGKILL, crashed.stderr
    assert w.states(sid) == ["PENDING_VETO"] and w.action(sid + ".publish")["state"] == "INTENDED"
    assert len(w.ky_calls()) == calls
    r = w.cli("tick")
    assert r.returncode == 3, r.stderr                                  # needs attention: it cannot decide alone
    d = one(json.loads(r.stdout), sid)
    assert (d["outcome"], d["reason"]) == ("blocked", "publication_unreconciled")
    assert len(w.ky_calls()) == calls and w.states(sid) == ["PENDING_VETO"] and w.capacity() == ("3\n", "2\n")
    # a real observation settles it: published → carry on without a second `ky decide`
    report = w.tick(LATER, publish_observer=lambda record: ("done", {"observed": "tracker readback"}))
    assert one(report, sid)["outcome"] == "executed" and len(w.ky_calls()) == calls
    assert w.capacity() == ("6\n", "4\n")


def test_a_publication_proven_not_to_have_happened_is_published_once(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap(tracker_decision=TD))
    w.crash("before-publish", "tick")
    report = w.tick(AFTER, publish_observer=lambda record: ("not_done", "no such tracker event"))
    assert one(report, sid)["outcome"] == "executed" and len(w.ky_calls()) == 1


def test_an_execution_another_live_process_began_is_neither_repeated_nor_reconciled(tmp_path):
    """CT-12 at the handler: `<id>.execute` is INTENDED and the process that began it is still alive."""
    w = World(tmp_path)
    sid = w.propose(cap())
    w.crash("before-execute", "tick")
    path = w.run / "actions" / (sid + ".execute.json")
    with bystander() as (pid, start):
        path.write_text(json.dumps(dict(json.loads(path.read_text()), process={"pid": pid, "process_start": start})))
        report = w.tick(AFTER)
        d = one(report, sid)
        assert (d["outcome"], d["reason"]) == ("locked", "execution_in_progress") and report["attention"] is False
        assert w.capacity() == ("3\n", "2\n") and "reconciliations" not in w.action(sid + ".execute")
    assert one(w.tick(LATER), sid)["outcome"] == "executed" and w.capacity() == ("6\n", "4\n")


def test_a_veto_does_not_fail_an_execution_another_live_process_may_be_carrying_out(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap())
    w.crash("before-execute", "tick")
    path = w.run / "actions" / (sid + ".execute.json")
    cid = w.veto(sid)
    with bystander() as (pid, start):
        path.write_text(json.dumps(dict(json.loads(path.read_text()), process={"pid": pid, "process_start": start})))
        before = path.read_bytes()
        d = one(w.tick(AFTER), sid)                       # not "vetoed before execution": nobody knows that yet
        assert (d["outcome"], d["reason"]) == ("locked", "execution_in_progress") and path.read_bytes() == before
        assert w.states(sid) == ["PENDING_VETO", "EFFECTIVE"] and w.command(cid)["state"] == "QUEUED"
    assert one(w.tick(LATER), sid)["outcome"] == "vetoed"      # that process is gone and wrote nothing: the veto holds
    assert w.capacity() == ("3\n", "2\n") and w.command(cid)["state"] == "APPLIED"


def test_concurrent_handlers_execute_one_proposal_exactly_once(tmp_path):
    w = World(tmp_path)
    hold(w.run, "veto", "ctl-veto")                       # one controller identity, several of its processes
    sid = w.propose(cap(tracker_decision=TD))
    argv = [PY, str(FLEET / "kyveto.py"), "tick", "--as", "ctl-veto"]
    procs = [subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=w.environ)
             for _ in range(6)]
    outs = [p.communicate(timeout=60) for p in procs]
    assert [p.returncode for p in procs] == [0] * 6, [o[1] for o in outs]
    outcomes = [d["outcome"] for o in outs for d in json.loads(o[0])["decisions"] if d["id"] == sid]
    assert outcomes.count("executed") == 1 and set(outcomes) <= {"executed", "locked", "not_pending"}, outcomes
    assert w.states(sid) == ["PENDING_VETO", "EFFECTIVE", "EXECUTED"]
    assert len(w.ky_calls()) == 1 and w.capacity() == ("6\n", "4\n")


def test_only_one_self_fenced_handler_runs_at_a_time(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap())
    hold(w.run, "veto", "another-live-handler")
    report = w.tick(AT)
    assert report["skipped"] == "veto_role_lock_held" and report["decisions"] == [] and report["attention"] is False
    assert w.states(sid) == ["PENDING_VETO"]
    r = w.cli("tick", "--as", "not-the-holder")
    assert r.returncode == 75 and "role_lock_held_by_another" in r.stderr
    assert w.states(sid) == ["PENDING_VETO"] and w.capacity() == ("3\n", "2\n")


# ── ruling R2 at the handler: a lock whose owner cannot be judged is never taken over — and somebody is told ──

@pytest.mark.parametrize("which", ["veto", "decision", "awaiting"])
@pytest.mark.parametrize("why", ["ps-unavailable", "pid-missing", "pid-not-an-integer", "ownerless"])
def test_the_handler_never_takes_over_a_lock_it_cannot_judge(tmp_path, monkeypatch, which, why):
    w = World(tmp_path)
    sid = w.propose(cap(tracker_decision=TD))
    name = {"veto": "veto", "decision": "decision." + sid, "awaiting": "awaiting." + w.history(sid)[0]["awaiting"]}[which]
    hold(w.run, name, "somebody")                         # really alive: this process
    d, owner = w.run / "locks" / name, owner_of(w.run, name)
    if why == "pid-missing":
        del owner["pid"]
    elif why == "pid-not-an-integer":
        owner["pid"] = str(owner["pid"])
    (d / "owner.json").write_text(json.dumps(owner))
    if why == "ownerless":
        (d / "owner.json").unlink()
    with monkeypatch.context() as m:
        if why == "ps-unavailable":
            no_ps(m)
        report = w.tick(AT)
    assert report["attention"] is True
    if which == "veto":
        assert report["skipped"] == "veto_role_lock_owner_unknown" and report["decisions"] == []
        assert report["problems"] and "veto" in report["problems"][0]
    else:
        row = one(report, sid)
        assert row["outcome"] == "blocked" and row["reason"].startswith("lock_owner_unknown") and row["attention"] is True
    assert d.is_dir() and w.states(sid) == ["PENDING_VETO"] and w.untouched()
    if why != "ownerless":
        assert owner_of(w.run, name)["session_or_run_id"] == "somebody"
    assert not (w.run / "locks" / ("decision." + sid)).exists() or which == "decision"       # its own lock released


def test_an_executor_that_fails_after_publication_is_failed_and_flagged(tmp_path, monkeypatch):
    w = World(tmp_path)
    sid = w.propose(cap(tracker_decision=TD))

    def broken(params, ctx):
        raise OSError("disk full")

    monkeypatch.setattr(kyveto.REGISTRY["capacity"], "execute", broken)
    report = w.tick(AT)
    d = one(report, sid)
    assert (d["outcome"], d["reason"]) == ("failed", "execution_failed: executor_error: OSError")
    assert d["published"] is True and d["attention"] is True
    assert w.states(sid) == ["PENDING_VETO", "EFFECTIVE", "FAILED"]            # published, never EXECUTED
    assert w.history(sid)[-1]["detail"] == {"published": True} and report["attention"] is True
    assert w.action(sid + ".execute")["state"] == "FAILED" and w.capacity() == ("3\n", "2\n")
    monkeypatch.undo()
    assert w.tick(AFTER)["decisions"] == [] and w.capacity() == ("3\n", "2\n")     # not retried
    assert len(w.ky_calls()) == 1


def test_a_decision_whose_awaiting_item_is_locked_is_skipped(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap())
    hold(w.run, "awaiting." + w.history(sid)[0]["awaiting"], "a-surrogate-job")
    d = one(w.tick(AT), sid)
    assert (d["outcome"], d["reason"]) == ("locked", "awaiting_item_locked")
    assert w.states(sid) == ["PENDING_VETO"] and w.capacity() == ("3\n", "2\n")
    assert not (w.run / "locks" / ("decision." + sid)).exists()              # its own lock was released again


def test_a_decision_locked_by_another_live_actor_is_skipped(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap())
    hold(w.run, "decision." + sid, "another-live-actor")
    report = w.tick(AT)
    d = one(report, sid)
    assert d["outcome"] == "locked" and w.states(sid) == ["PENDING_VETO"] and w.capacity() == ("3\n", "2\n")
    assert report["attention"] is False                   # a live owner is "come back later", not an alarm


def test_a_torn_decision_log_blocks_every_transition(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap())
    with open(w.log, "a") as f:
        f.write('{"id": "SD-20261011T220000Z-1", "state": "VETO')          # it might have been this decision's veto
    before = w.log.read_bytes()
    report = w.tick(AFTER)
    assert report["attention"] is True and report["decisions"] == [] and report["problems"]
    assert w.log.read_bytes() == before and w.capacity() == ("3\n", "2\n")
    assert w.cli("tick").returncode == 3
    assert w.log.read_bytes() == before and w.actions() == [] and sid


def test_the_handler_starts_its_line_on_a_fresh_row(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap())
    w.log.write_bytes(w.log.read_bytes().rstrip(b"\n"))                # the last writer left no newline
    assert one(w.tick(AT), sid)["outcome"] == "executed"
    assert w.states(sid) == ["PENDING_VETO", "EFFECTIVE", "EXECUTED"]


def test_one_decisions_unexpected_trouble_does_not_end_the_pass(tmp_path, monkeypatch):
    w = World(tmp_path)
    bad, good = w.propose(cap(builders=7)), w.propose(cap(builders=5))
    real = kyveto.Handler.decide

    def decide(self, did, lines, history):
        if did == bad:
            raise RuntimeError("something nobody foresaw")
        return real(self, did, lines, history)

    monkeypatch.setattr(kyveto.Handler, "decide", decide)
    report = w.tick(AT)
    d = one(report, bad)
    assert d["outcome"] == "blocked" and "RuntimeError" in d["reason"] and d["attention"] is True
    assert one(report, good)["outcome"] == "executed" and w.capacity() == ("5\n", "4\n")
    assert not (w.run / "locks" / ("decision." + bad)).exists()


def test_routine_decisions_are_not_the_handlers_business(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap(), **{"class": "routine", "state": "EFFECTIVE", "veto_deadline": None, "effective_at": AT})
    done = w.propose(cap(builders=5), **{"class": "routine", "state": "EXECUTED", "veto_deadline": None,
                                         "effective_at": AT})
    before = tree(w.run)
    report = w.tick(LATER)
    assert report["decisions"] == [] and report["attention"] is False and tree(w.run) == before
    assert w.states(sid) == ["EFFECTIVE"] and w.states(done) == ["EXECUTED"]
    assert kyveto.status(w.env, now=LATER)["attention"] is False       # no anomaly: routine publishes by itself


def test_unknown_target_kind(tmp_path):
    w = World(tmp_path)
    sid = w.propose({"kind": "merge_everything", "fingerprint": "0" * 64}, bind=False)
    failed(w, sid, "unknown_target_kind")


# ── CT-08: capacity — bounds, and the pair of files as one effect ──

@pytest.mark.parametrize("target,needle", [
    ({"kind": "capacity", "builders": 6}, "verifiers"),
    ({"kind": "capacity", "builders": 0, "verifiers": 2}, "builders"),
    ({"kind": "capacity", "builders": "6", "verifiers": 2}, "builders"),
    ({"kind": "capacity", "builders": True, "verifiers": 2}, "builders"),
    ({"kind": "capacity", "builders": 6, "verifiers": 16}, "verifiers"),
    ({"kind": "capacity", "builders": 9, "verifiers": 2}, "builders"),           # KĀLA-YANTRA's share of copies is 8
    ({"kind": "capacity", "builders": 6, "verifiers": 9}, "verifiers"),
    ({"kind": "capacity", "builders": 15, "verifiers": 15}, "builders"),         # the reviewer's probe: accepted before
    ({"kind": "capacity", "builders": 6.0, "verifiers": 2}, "builders"),
    ({"kind": "capacity", "builders": 6, "verifiers": 2, "also": "merge PR 1"}, "also"),
])
def test_a_malformed_capacity_target_is_refused(tmp_path, target, needle):
    w = World(tmp_path)
    sid = w.propose(dict(target, fingerprint="0" * 64), bind=False)
    d = failed(w, sid, "target_malformed")
    assert needle in d["reason"]
    with pytest.raises(kyveto.TargetError):
        kyveto.fingerprint(target, w.env)                 # … and the surrogate cannot even fingerprint it


def test_capacity_is_bounded_at_eight_builders_and_eight_verifiers(tmp_path):
    w = World(tmp_path)
    assert kyveto.CAPACITY_MAX == {"builders": 8, "verifiers": 8}
    sid = w.propose(cap(builders=8, verifiers=8))
    assert one(w.tick(AT), sid)["outcome"] == "executed" and w.capacity() == ("8\n", "8\n")
    sid = w.propose(cap(builders=1, verifiers=1))
    assert one(w.tick(AT), sid)["outcome"] == "executed" and w.capacity() == ("1\n", "1\n")


def test_capacity_writes_are_atomic_and_idempotent(tmp_path):
    w = World(tmp_path)
    capacity = kyveto.REGISTRY["capacity"]
    ctx = kyveto.Ctx(w.env, "SD-20261011T220000Z-1", {"source_commit": C1, "entrypoints_digest": E1}, AT)
    params = cap(builders=6, verifiers=2)                 # verifiers already at the requested value
    outcome, detail = capacity.observer(params, ctx)
    assert outcome == "not_done" and detail["incomplete"] == ["KY_WORKERS"]
    v_inode = (w.run / "KY_VERIFIERS").stat().st_ino
    ok, result = capacity.execute(params, ctx)
    assert ok is True and w.capacity() == ("6\n", "2\n")
    assert result["KY_WORKERS"] == {"before": "3", "after": "6", "written": True}
    assert result["KY_VERIFIERS"] == {"before": "2", "after": "2", "written": False}
    assert (w.run / "KY_VERIFIERS").stat().st_ino == v_inode
    assert sorted(p.name for p in w.run.iterdir() if p.name.startswith(".")) == []        # no temp file left
    w_inode = (w.run / "KY_WORKERS").stat().st_ino
    ok, again = capacity.execute(params, ctx)
    assert ok is True and again["KY_WORKERS"]["written"] is False
    assert (w.run / "KY_WORKERS").stat().st_ino == w_inode and w.capacity() == ("6\n", "2\n")
    assert capacity.observer(params, ctx)[0] == "done"
    (w.run / "KY_WORKERS").unlink()                       # an absent file is a state too, not an error
    assert capacity.observer(params, ctx)[0] == "not_done"
    ok, created = capacity.execute(params, ctx)
    assert ok and created["KY_WORKERS"] == {"before": None, "after": "6", "written": True}


def test_the_fingerprint_binds_the_request_and_the_files_it_will_change(tmp_path):
    w = World(tmp_path)
    base = kyveto.fingerprint(cap(), w.env)
    assert base == kyveto.fingerprint(dict(cap(), fingerprint="ignored"), w.env) and len(base) == 64
    assert kyveto.fingerprint(cap(builders=7), w.env) != base
    assert kyveto.fingerprint(cap(tracker_decision=TD), w.env) != base
    target_file = tmp_path / "target.json"
    target_file.write_text(json.dumps(cap()))
    r = w.cli("fingerprint", "--target", str(target_file))
    assert r.returncode == 0 and r.stdout.strip() == base             # what the surrogate records at proposal
    (w.run / "KY_VERIFIERS").write_text("3\n")
    assert kyveto.fingerprint(cap(), w.env) != base
    target_file.write_text(json.dumps({"kind": "merge_everything"}))
    bad = w.cli("fingerprint", "--target", str(target_file))
    assert bad.returncode == 1 and "unknown_target_kind" in bad.stderr


# ── the awaiting item; CT-09: what is published is the tracker decision the item is about ──

def test_the_awaiting_item_must_still_be_open(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap(), awaiting_open=False)           # resolved or withdrawn during the window
    failed(w, sid, "awaiting_not_open")


@pytest.mark.parametrize("content", ["{", "[]", json.dumps({"id": "AW-20261011T215900Z-another-item"})])
def test_an_awaiting_item_that_cannot_be_read_as_this_item_fails_the_decision(tmp_path, content):
    w = World(tmp_path)
    sid = w.propose(cap(tracker_decision=TD))
    (w.run / "awaiting" / (w.history(sid)[0]["awaiting"] + ".json")).write_text(content)
    failed(w, sid, "awaiting_unreadable")
    assert w.ky_calls() == []


@pytest.mark.parametrize("names,published,ok", [
    ({"item": "D-41"}, {"id": "D-41", "outcome": "approved"}, True),
    ({"item": "D-41"}, {"id": "D-42", "outcome": "approved"}, False),           # another decision than the one asked
    ({"tracker_decision": "D-41"}, {"id": "D-42", "outcome": "approved"}, False),
    ({"tracker_decision": {"id": "D-41"}}, {"id": "D-42", "outcome": "approved"}, False),
    ({"tracker_decision": {"id": "D-41"}, "item": "K7-3"}, {"id": "D-41", "outcome": "approved"}, True),
    ({"item": "D-41"}, None, True),                                             # nothing is published at all
    ({"item": "K7-3"}, {"id": "D-42", "outcome": "approved"}, False),           # C2-02: the item names no tracker
    ({}, {"id": "D-42", "outcome": "approved"}, False),                         # decision: nothing binds D-42 to it
    ({"tracker_decision": {"outcome": "approved"}}, {"id": "D-42", "outcome": "approved"}, False),
    ({"item": "K7-3"}, None, True),                                             # … and nothing is published: fine
])
def test_the_published_tracker_decision_is_the_one_the_awaiting_item_names(tmp_path, names, published, ok):
    w = World(tmp_path)
    sid = w.propose(cap(tracker_decision=published) if published else cap())
    aw = w.history(sid)[0]["awaiting"]
    (w.run / "awaiting" / (aw + ".json")).write_text(json.dumps(dict({"id": aw, "question": "raise capacity?"}, **names)))
    if ok:
        assert one(w.tick(AT), sid)["outcome"] == "executed"
        assert [c["argv"][1] for c in w.ky_calls()] == ([published["id"]] if published else [])
    else:
        d = failed(w, sid, "tracker_decision_not_the_awaiting_items")
        named = kyveto.named_tracker_decision(names)
        assert "D-42" in d["reason"] and (named or "the item names no tracker decision") in d["reason"]
        assert named in ("D-41", None) and w.ky_calls() == [] and w.actions() == []


def test_the_owners_own_decision_supersedes_the_pending_proposal(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap())
    aw = w.history(sid)[0]["awaiting"]
    cid = kycommands.submit(w.run, "planner", "decide", {"awaiting_id": aw, "answer": "keep six"}, COCKPIT)
    d = failed(w, sid, "superseded_by_owner_decide")
    assert d["reason"] == "superseded_by_owner_decide: " + cid


def test_one_awaiting_item_is_decided_by_one_proposal_only(tmp_path):
    w = World(tmp_path)
    first = w.propose(cap(builders=5))
    aw = w.history(first)[0]["awaiting"]
    assert one(w.tick(AT), first)["outcome"] == "executed"
    second = w.propose(cap(builders=7), awaiting=aw)
    report = w.tick(AFTER)
    d = one(report, second)
    assert (d["outcome"], d["reason"], d["attention"]) == ("failed", "awaiting_already_decided: " + first, True)
    assert w.capacity() == ("5\n", "4\n")


# ── plan-bundle changes: the activation chain (pairing rule KW-04) and what "independently reviewed" means (R4) ──

def canonical_digest(body):
    """The manifest digest exactly as kymanifest.py computes it (written out here; compared with it below)."""
    return hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def manifest_doc(commit, owner_blob="d" * 40, **over):
    entrypoints = {role: {"path": "00_ARCHITECTURE/briefs/kalayantra/%s.md" % role.upper(), "sha256": "5" * 64,
                          "git_blob": ("%x" % n) * 40} for n, role in enumerate(kyveto.ENTRYPOINT_ROLES, 1)}
    entrypoints["owner_decisions"] = {"path": kyveto.OWNER_DECISIONS_PATH, "sha256": "6" * 64, "git_blob": owner_blob}
    doc = {"schema": "ky.versions_bootstrap/1", "mode": "bootstrap", "plan_version": "2.8",
           "approved_source_commit": commit, "entrypoints": entrypoints,
           "components": [{"path": "00_ARCHITECTURE/briefs/kalayantra/fleet/kyveto.py", "sha256": "7" * 64}]}
    doc.update(over)
    return doc


def write_manifest(w, commit=C2, doc=None, name=None, stored=None):
    """→ (path, digest): a successor manifest on disk, with the digest of its content (manifest_sha256 excluded)."""
    doc = manifest_doc(commit) if doc is None else doc
    body = {k: v for k, v in doc.items() if k != "manifest_sha256"}
    digest = canonical_digest(body)
    d = w.run / "manifests"
    d.mkdir(exist_ok=True)
    path = d / (name or "VERSIONS.%s.json" % commit[:7])
    path.write_text(json.dumps(dict(body, manifest_sha256=digest if stored is None else stored), indent=1, sort_keys=True))
    return str(path), digest


def receipt(w, name=None, verdict="ACCEPTED", commit=C2, reviewer="astra-review-1", manifest=None, **over):
    d = w.run / "reviews"
    d.mkdir(exist_ok=True)
    doc = {"verdict": verdict, "reviewer_session_id": reviewer, "source_commit": commit, "manifest_sha256": manifest,
           "inputs": {"00_ARCHITECTURE/briefs/kalayantra/fleet/kyveto.py": "7" * 64}}
    doc.update(over)
    path = d / (name or "review-%s.json" % commit[:7])
    path.write_text(json.dumps({k: v for k, v in doc.items() if v is not None or k != "manifest_sha256"}))
    return str(path)


def bundle(w, **over):
    """A plan_bundle_change target C1 → C2 with a real successor manifest and one independent review of it."""
    new_commit = over.get("new_commit", C2)
    path, digest = write_manifest(w, new_commit)
    target = {"kind": "plan_bundle_change", "old_commit": C1, "new_commit": new_commit, "old_manifest_digest": M1,
              "new_manifest_digest": digest, "new_manifest_path": path}
    target.update(over)
    target.setdefault("review_receipts", [receipt(w, commit=target["new_commit"],
                                                  manifest=target["new_manifest_digest"])])
    return target


def records(w):
    return sorted(p.name for p in w.run.glob("ACTIVATION_RECORD*.json"))


ROOT_AUTHORITY = {"source_commit": C1, "entrypoints_digest": E1}


def test_a_bundle_change_writes_the_next_immutable_activation_record(tmp_path):
    w = World(tmp_path)
    target = bundle(w, tracker_decision=TD)
    sid = w.propose(target, decision="adopt plan v2.8")
    assert one(w.tick(AT), sid)["outcome"] == "executed"
    assert records(w) == ["ACTIVATION_RECORD.1.json"]
    path = w.run / "ACTIVATION_RECORD.1.json"
    rec = json.loads(path.read_text())
    assert_schema("activation_record", rec)
    assert (rec["n"], rec["previous"]) == (1, None)
    assert (rec["old_commit"], rec["new_commit"], rec["old_manifest_digest"], rec["new_manifest_digest"]) == (
        C1, C2, M1, target["new_manifest_digest"])
    assert rec["authorising_act"] == {"kind": "surrogate_decision", "id": sid}
    assert rec["campaign_admission"] is False                          # a bundle change never admits the campaign
    (r1,) = rec["review_receipts"]
    assert r1["sha256"] == sha(r1["path"]) and r1["verdict"] == "ACCEPTED"
    assert r1["reviewer_session_id"] == "astra-review-1" and r1["manifest_sha256"] == target["new_manifest_digest"]
    assert rec["new_manifest"]["path"] == target["new_manifest_path"]
    assert rec["new_manifest"]["sha256"] == sha(target["new_manifest_path"])
    assert rec["owner_decisions"] == {"path": kyveto.OWNER_DECISIONS_PATH, "new_path": kyveto.OWNER_DECISIONS_PATH,
                                      "old_blob": "d" * 40, "new_blob": "d" * 40}
    assert path.stat().st_mode & 0o222 == 0                            # read-only
    assert w.action(sid + ".execute")["result"]["sha256"] == sha(path)
    assert len(w.ky_calls()) == 1
    # the successor chains to it by digest; its authority is the bundle the first link activated
    successor = {"source_commit": C2, "entrypoints_digest": rec["new_manifest"]["entrypoints_digest"]}
    w.authorise(**{"commit": successor["source_commit"], "digest": successor["entrypoints_digest"]})
    second = bundle(w, old_commit=C2, new_commit=C3, old_manifest_digest=target["new_manifest_digest"])
    sid2 = w.propose(second, authority=successor)
    assert one(w.tick(AFTER), sid2)["outcome"] == "executed"
    assert records(w) == ["ACTIVATION_RECORD.1.json", "ACTIVATION_RECORD.2.json"]
    rec2 = json.loads((w.run / "ACTIVATION_RECORD.2.json").read_text())
    assert rec2["previous"] == {"file": "ACTIVATION_RECORD.1.json", "sha256": sha(path)} and rec2["n"] == 2
    assert_schema("activation_record", rec2)
    assert json.loads(path.read_text()) == rec                         # the earlier record is untouched


def test_the_manifest_digest_and_the_entrypoints_digest_are_kymanifests_own(tmp_path):
    """Ruling R4: "as kymanifest.py does". The successor's authority (R5) is the link's commit plus the digest of
    its manifest's entrypoints — the very number a surrogate decision under the new bundle carries."""
    try:
        import kymanifest
    except Exception as e:                                # that file is another area's and may be mid-edit
        pytest.skip("kymanifest.py cannot be imported here: %s" % type(e).__name__)
    w = World(tmp_path)
    doc = manifest_doc(C2)
    path, digest = write_manifest(w, C2, doc=doc)
    assert kymanifest.with_digest(doc)["manifest_sha256"] == digest
    change = kyveto.REGISTRY["plan_bundle_change"]
    ctx = kyveto.Ctx(w.env, "SD-20261011T220000Z-7", ROOT_AUTHORITY, AT, sessions=["surrogate-1"])
    params = dict(bundle(w), new_manifest_path=path, new_manifest_digest=digest)
    params["review_receipts"] = [receipt(w, manifest=digest)]
    ok, result = change.execute(params, ctx)
    assert ok is True, result
    rec = json.loads((w.run / "ACTIVATION_RECORD.1.json").read_text())
    assert rec["new_manifest"]["entrypoints_digest"] == kymanifest.entrypoints_digest(doc["entrypoints"])


def chain_refusal(tmp_path, reason, prepare=None, bind=True, **over):
    """A bundle change that must be FAILED with `reason`: no activation record written, nothing published. The
    authority is passed as the controller passes it (R5), so that the refusal is the change's own."""
    w = World(tmp_path)
    target = dict(bundle(w, **over), tracker_decision=TD)
    if prepare:
        prepare(w, target)
    if not bind:
        target["fingerprint"] = "0" * 64
    sid = w.propose(target, bind=bind)
    before = {name: (w.run / name).read_bytes() for name in records(w)}
    report = w.tick(AT, authorised=ROOT_AUTHORITY)
    d = one(report, sid)
    assert d["outcome"] == "failed" and d["reason"].startswith(reason), d
    assert d["attention"] is True and report["attention"] is True
    assert {name: (w.run / name).read_bytes() for name in records(w)} == before          # nothing written
    assert w.ky_calls() == [] and w.states(sid) == ["PENDING_VETO", "FAILED"]
    return w, sid


def test_bundle_change_refused_when_a_review_receipt_is_missing(tmp_path):
    chain_refusal(tmp_path, "review_receipt_missing", review_receipts=["/nonexistent/review.json"])


def test_bundle_change_refused_when_a_review_receipt_is_not_accepted(tmp_path):
    def reject(w, target):
        digest = target["new_manifest_digest"]
        target["review_receipts"] = [receipt(w, manifest=digest),
                                     receipt(w, "review-b.json", verdict="REJECTED", manifest=digest)]
    chain_refusal(tmp_path, "review_receipt_not_accepted", prepare=reject)


def test_bundle_change_refused_when_a_review_is_for_another_commit(tmp_path):
    def other(w, target):
        target["review_receipts"] = [receipt(w, "review-x.json", commit=C3, manifest=target["new_manifest_digest"])]
    chain_refusal(tmp_path, "review_receipt_not_bound", prepare=other)


def test_bundle_change_refused_when_a_review_names_no_reviewer(tmp_path):
    def anonymous(w, target):
        target["review_receipts"] = [receipt(w, reviewer="", manifest=target["new_manifest_digest"])]
    chain_refusal(tmp_path, "review_receipt_not_accepted", prepare=anonymous)


def test_bundle_change_refused_without_any_review_receipt(tmp_path):
    chain_refusal(tmp_path, "target_malformed", bind=False, review_receipts=[])


# CT-04 (ruling R4): "independently reviewed" is computed — reviewer, bound manifest, reviewed inputs, the manifest

@pytest.mark.parametrize("reviewer", ["surrogate-1", " surrogate-1 ", "kalayantra-owner-surrogate"])
def test_a_review_by_the_deciding_session_is_not_independent(tmp_path, reviewer):
    """The reviewer's probe: a receipt whose reviewer is the proposing surrogate session wrote
    ACTIVATION_RECORD.1.json."""
    def self_review(w, target):
        target["review_receipts"] = [receipt(w, reviewer=reviewer, manifest=target["new_manifest_digest"])]
    w, sid = chain_refusal(tmp_path, "review_receipt_not_independent", prepare=self_review)
    assert w.history(sid)[0]["session"] == "surrogate-1" and records(w) == []


def test_one_self_review_among_independent_ones_still_refuses(tmp_path):
    def mixed(w, target):
        digest = target["new_manifest_digest"]
        target["review_receipts"] = [receipt(w, manifest=digest),
                                     receipt(w, "review-own.json", reviewer="surrogate-1", manifest=digest)]
    chain_refusal(tmp_path, "review_receipt_not_independent", prepare=mixed)


@pytest.mark.parametrize("change,reason", [
    ({"manifest": None}, "review_receipt_not_bound"),                       # the receipt binds no manifest at all
    ({"manifest": M3}, "review_receipt_not_bound"),                         # … or another one
    ({"inputs": {}}, "review_receipt_without_inputs"),                      # it names nothing it reviewed
    ({"inputs": None}, "review_receipt_without_inputs"), ({"inputs": ["kyveto.py"]}, "review_receipt_without_inputs"),
])
def test_a_receipt_not_bound_to_the_reviewed_manifest_and_inputs_is_refused(tmp_path, change, reason):
    def prepare(w, target):
        kw = dict({"manifest": target["new_manifest_digest"]}, **change)
        target["review_receipts"] = [receipt(w, "review-c.json", **kw)]
    chain_refusal(tmp_path, reason, prepare=prepare)


def test_a_bundle_change_without_a_manifest_path_is_malformed(tmp_path):
    def drop(w, target):
        del target["new_manifest_path"]
    chain_refusal(tmp_path, "target_malformed", prepare=drop, bind=False)


@pytest.mark.parametrize("how,reason", [
    ("missing", "manifest_missing"), ("torn", "manifest_unreadable"), ("not-an-object", "manifest_unreadable"),
    ("another-digest", "manifest_digest_mismatch"), ("edited-after-review", "manifest_digest_mismatch"),
    ("stored-digest-wrong", "manifest_digest_mismatch"), ("no-entrypoints", "manifest_entrypoints_missing"),
    ("four-roles", "manifest_entrypoints_missing"), ("six-roles", "manifest_entrypoints_missing"),
    ("entry-without-blob", "manifest_entrypoints_missing"), ("entry-with-absolute-path", "manifest_entrypoints_missing"),
    ("another-commit", "manifest_not_for_new_commit"), ("owner-decisions-blob", "manifest_entrypoint_mismatch"),
    ("no-source-commit", "manifest_not_for_new_commit"), ("source-commit-null", "manifest_not_for_new_commit"),
    ("another-entrypoints-digest", "manifest_entrypoints_digest_mismatch"),
    ("entrypoints-digest-null", "manifest_entrypoints_digest_mismatch"),
])
def test_the_successor_manifest_is_checked_not_named(tmp_path, how, reason):
    """The reviewer's finding: new_manifest_digest and the KX-03 entrypoints mapping were never checked against
    a manifest."""
    def prepare(w, target):
        doc = manifest_doc(C2)
        if how == "missing":
            target["new_manifest_path"] = str(w.run / "manifests" / "no-such.json")
            return
        if how == "another-digest":
            target["new_manifest_digest"] = M3            # (the receipt is made to agree with the target, below)
        elif how == "no-entrypoints":
            del doc["entrypoints"]
        elif how == "four-roles":
            del doc["entrypoints"]["strategy"]
        elif how == "six-roles":
            doc["entrypoints"]["extra"] = dict(doc["entrypoints"]["plan"])
        elif how == "entry-without-blob":
            del doc["entrypoints"]["cockpit_prompt"]["git_blob"]
        elif how == "entry-with-absolute-path":
            doc["entrypoints"]["plan"]["path"] = "/Users/Dev/elsewhere/PLAN.md"
        elif how == "another-commit":
            doc["approved_source_commit"] = C3
        elif how == "owner-decisions-blob":
            doc["entrypoints"]["owner_decisions"]["git_blob"] = "9" * 40      # git says d…d at new_commit
        elif how == "no-source-commit":                   # C2-03: a manifest of no commit in particular
            del doc["approved_source_commit"]
        elif how == "source-commit-null":
            doc["approved_source_commit"] = None
        elif how == "another-entrypoints-digest":         # C2-03: kyloop refuses this manifest for the next authority
            doc["entrypoints_digest"] = E2
        elif how == "entrypoints-digest-null":
            doc["entrypoints_digest"] = None
        if how in ("no-entrypoints", "four-roles", "six-roles", "entry-without-blob", "entry-with-absolute-path",
                   "another-commit", "owner-decisions-blob", "no-source-commit", "source-commit-null",
                   "another-entrypoints-digest", "entrypoints-digest-null"):
            target["new_manifest_path"], target["new_manifest_digest"] = write_manifest(w, C2, doc=doc, name="m.json")
        elif how == "stored-digest-wrong":
            write_manifest(w, C2, name=Path(target["new_manifest_path"]).name, stored=M3)
        target["review_receipts"] = [receipt(w, "review-m.json", manifest=target["new_manifest_digest"])]
        if how == "torn":
            Path(target["new_manifest_path"]).write_text("{")
        elif how == "not-an-object":
            Path(target["new_manifest_path"]).write_text("[]")
        elif how == "edited-after-review":                # the proposal is fingerprinted AFTER this edit: the file
            path = Path(target["new_manifest_path"])      # is "unchanged since proposal" and still not the digest
            doc = json.loads(path.read_text())
            doc["components"].append({"path": "something/slipped/in.py", "sha256": "8" * 64})
            path.write_text(json.dumps(doc))
    chain_refusal(tmp_path, reason, prepare=prepare)


@pytest.mark.parametrize("key", ["approved_source_commit", "source_commit"])
def test_a_manifest_that_states_its_commit_and_its_own_entrypoints_digest_is_accepted(tmp_path, key):
    """C2-03, the passing side: the source commit under either name, and the digest of the manifest's own mapping."""
    w = World(tmp_path)
    doc = manifest_doc(C2)
    doc[key] = doc.pop("approved_source_commit")
    doc["entrypoints_digest"] = kyaction.sha_bytes(kyaction.canonical(
        {role: {"path": e["path"], "git_blob": e["git_blob"]} for role, e in doc["entrypoints"].items()}))
    path, digest = write_manifest(w, C2, doc=doc, name="stated.json")
    target = bundle(w, new_manifest_path=path, new_manifest_digest=digest)
    sid = w.propose(target)
    assert one(w.tick(AT, authorised=ROOT_AUTHORITY), sid)["outcome"] == "executed"
    rec = json.loads((w.run / "ACTIVATION_RECORD.1.json").read_text())
    assert rec["new_manifest"]["entrypoints_digest"] == doc["entrypoints_digest"]


def test_the_activation_record_names_the_manifest_by_its_absolute_path(tmp_path):
    """C2-04: a target may name the manifest relative to the run directory; the immutable record may not."""
    w = World(tmp_path)
    path, digest = write_manifest(w, C2)
    relative = os.path.relpath(path, w.run)
    assert not os.path.isabs(relative) and not relative.startswith("..")
    target = bundle(w, new_manifest_path=relative, new_manifest_digest=digest)
    sid = w.propose(target)
    assert one(w.tick(AT, authorised=ROOT_AUTHORITY), sid)["outcome"] == "executed"
    rec = json.loads((w.run / "ACTIVATION_RECORD.1.json").read_text())
    assert_schema("activation_record", rec)
    assert os.path.isabs(rec["new_manifest"]["path"]) and rec["new_manifest"]["path"] == os.path.abspath(path)
    assert rec["new_manifest"]["sha256"] == sha(rec["new_manifest"]["path"])
    assert all(os.path.isabs(r["path"]) for r in rec["review_receipts"])


def test_a_manifest_changed_during_the_window_is_a_changed_target(tmp_path):
    w = World(tmp_path)
    target = bundle(w)
    sid = w.propose(target)
    path = Path(target["new_manifest_path"])
    path.write_text(path.read_text() + "\n")
    failed(w, sid, "target_changed", authorised=ROOT_AUTHORITY)
    assert records(w) == []


def test_the_executor_cannot_vouch_for_independence_without_knowing_the_deciding_session(tmp_path):
    w = World(tmp_path)
    change = kyveto.REGISTRY["plan_bundle_change"]
    ctx = kyveto.Ctx(w.env, "SD-20261011T220000Z-7", ROOT_AUTHORITY, AT)          # no sessions given
    ok, refused_ = change.execute(bundle(w), ctx)
    assert ok is False and refused_["reason"].startswith("review_independence_unverifiable") and records(w) == []


def previous_record(w, new_commit, new_manifest=M1, n=1, previous=None):
    doc = {"schema": "ky.activation_record/1", "n": n, "previous": previous, "old_commit": C3,
           "new_commit": new_commit, "old_manifest_digest": M3, "new_manifest_digest": new_manifest,
           "review_receipts": [], "authorising_act": {"kind": "owner", "id": "by-test"},
           "campaign_admission": False, "created_at": T_NOTIFY, "created_by": "by-test"}
    path = w.run / ("ACTIVATION_RECORD.%d.json" % n)
    path.write_text(json.dumps(doc))
    return path


def test_bundle_change_refused_when_it_does_not_continue_the_chain(tmp_path):
    chain_refusal(tmp_path, "activation_chain_mismatch", prepare=lambda w, t: previous_record(w, new_commit=C3))


def test_bundle_change_refused_when_the_previous_manifest_differs(tmp_path):
    chain_refusal(tmp_path, "activation_chain_mismatch",
                  prepare=lambda w, t: previous_record(w, new_commit=C1, new_manifest=M3))


def test_bundle_change_continues_a_matching_chain(tmp_path):
    w = World(tmp_path)
    prev = previous_record(w, new_commit=C1, new_manifest=M1)
    sid = w.propose(bundle(w))
    assert one(w.tick(AT), sid)["outcome"] == "executed"
    rec = json.loads((w.run / "ACTIVATION_RECORD.2.json").read_text())
    assert rec["previous"] == {"file": prev.name, "sha256": sha(prev)}


def test_bundle_change_refused_when_the_chain_itself_is_broken(tmp_path):
    def broken(w, target):
        previous_record(w, new_commit=C3, n=1)
        previous_record(w, new_commit=C1, n=2, previous={"file": "ACTIVATION_RECORD.1.json", "sha256": "0" * 64})
    chain_refusal(tmp_path, "activation_chain_invalid", prepare=broken)

    def gap(w, target):
        previous_record(w, new_commit=C1, n=3)
    chain_refusal(tmp_path / "gap", "activation_chain_invalid", prepare=gap)


# the chain's shape (cockpit ruling): the trust root is no record; the un-numbered record, when present, is link 0
# and link 1 MUST name it; without it a numbered-only chain starts at link 1 with previous: null; no gaps.

def root_record(w, commit=C1, manifest=M1):
    """B-5's un-numbered final activation record."""
    path = w.run / "ACTIVATION_RECORD.json"
    path.write_text(json.dumps({"final_manifest_digest": manifest, "source_commit": commit,
                                "authorising_act": {"kind": "owner", "id": "by-test"}}))
    return path


def names(path):
    return {"file": path.name, "sha256": sha(path)}


def chain_of(w):
    ctx = kyveto.Ctx(w.env, None, ROOT_AUTHORITY, AT)
    links, err = kyveto.REGISTRY["plan_bundle_change"].chain(ctx)
    return (None if links is None else [n for n, _, _ in links]), err


def test_a_numbered_only_chain_of_one_and_of_two_links_is_valid_and_is_extended(tmp_path):
    w = World(tmp_path)
    assert chain_of(w) == ([], None)                              # the trust root alone: no record at all
    one_link = previous_record(w, new_commit=C3, n=1)             # previous: null
    assert chain_of(w) == ([1], None)
    two = previous_record(w, new_commit=C1, new_manifest=M1, n=2, previous=names(one_link))
    assert chain_of(w) == ([1, 2], None)
    sid = w.propose(bundle(w))
    assert one(w.tick(AT), sid)["outcome"] == "executed"
    third = json.loads((w.run / "ACTIVATION_RECORD.3.json").read_text())
    assert (third["n"], third["previous"]) == (3, names(two)) and chain_of(w) == ([1, 2, 3], None)


def test_the_first_link_of_a_numbered_only_chain_is_written_with_previous_null(tmp_path):
    w = World(tmp_path)
    sid = w.propose(bundle(w))
    assert one(w.tick(AT), sid)["outcome"] == "executed"
    first = json.loads((w.run / "ACTIVATION_RECORD.1.json").read_text())
    assert (first["n"], first["previous"]) == (1, None) and chain_of(w) == ([1], None)


def test_link_one_with_no_predecessor_beside_the_un_numbered_record_is_a_fork(tmp_path):
    def fork(w, target):
        root_record(w)
        previous_record(w, new_commit=C1, new_manifest=M1, n=1)   # previous: null, and it would otherwise continue

    w, sid = chain_refusal(tmp_path, "activation_chain_fork", prepare=fork)
    links, err = chain_of(w)
    assert links is None and err.startswith("activation_chain_fork")          # not accepted, not extended
    assert records(w) == ["ACTIVATION_RECORD.1.json", "ACTIVATION_RECORD.json"]


def test_link_one_naming_another_un_numbered_record_is_invalid(tmp_path):
    def wrong(w, target):
        root_record(w)
        previous_record(w, new_commit=C1, new_manifest=M1, n=1,
                        previous={"file": "ACTIVATION_RECORD.json", "sha256": "0" * 64})
    chain_refusal(tmp_path, "activation_chain_invalid", prepare=wrong)


def test_a_numbered_only_chain_cannot_start_from_a_predecessor_that_does_not_exist(tmp_path):
    def orphan(w, target):
        previous_record(w, new_commit=C1, new_manifest=M1, n=1,
                        previous={"file": "ACTIVATION_RECORD.json", "sha256": "0" * 64})
    chain_refusal(tmp_path, "activation_chain_invalid", prepare=orphan)

    def silent(w, target):                                        # `previous` must be stated, null included
        path = previous_record(w, new_commit=C1, new_manifest=M1, n=1)
        doc = json.loads(path.read_text())
        del doc["previous"]
        path.write_text(json.dumps(doc))
    chain_refusal(tmp_path / "silent", "activation_chain_invalid", prepare=silent)


@pytest.mark.parametrize("with_root", [False, True])
def test_a_gap_in_the_numbering_is_refused(tmp_path, with_root):
    def gap(w, target):
        first = previous_record(w, new_commit=C3, n=1, previous=names(root_record(w)) if with_root else None)
        previous_record(w, new_commit=C1, new_manifest=M1, n=3, previous=names(first))       # link 2 is missing
    w, sid = chain_refusal(tmp_path, "activation_chain_invalid", prepare=gap)
    assert "ACTIVATION_RECORD.2.json is missing" in w.history(sid)[-1]["reason"]
    assert chain_of(w)[0] is None


def test_the_next_link_names_the_true_terminal_link(tmp_path):
    w = World(tmp_path)
    root = root_record(w, commit=C1, manifest=M1)                 # the only link there is
    before = root.read_bytes()
    assert chain_of(w) == ([0], None)
    first_target = bundle(w)
    sid = w.propose(first_target)
    assert one(w.tick(AT), sid)["outcome"] == "executed"
    first = json.loads((w.run / "ACTIVATION_RECORD.1.json").read_text())
    assert (first["n"], first["previous"]) == (1, names(root))    # link 1 names link 0 by sha256
    assert_schema("activation_record", first)
    assert root.read_bytes() == before and chain_of(w) == ([0, 1], None)
    w.authorise(C2, E2)                                           # now link 1 is the terminal link
    sid2 = w.propose(bundle(w, old_commit=C2, new_commit=C3, old_manifest_digest=first_target["new_manifest_digest"]),
                     authority={"source_commit": C2, "entrypoints_digest": E2})
    assert one(w.tick(AFTER), sid2)["outcome"] == "executed"
    second = json.loads((w.run / "ACTIVATION_RECORD.2.json").read_text())
    assert (second["n"], second["previous"]) == (2, names(w.run / "ACTIVATION_RECORD.1.json"))
    assert chain_of(w) == ([0, 1, 2], None)


def test_a_change_that_does_not_continue_the_un_numbered_record_is_refused(tmp_path):
    chain_refusal(tmp_path, "activation_chain_mismatch", prepare=lambda w, t: root_record(w, commit=C3))
    chain_refusal(tmp_path / "manifest", "activation_chain_mismatch",
                  prepare=lambda w, t: root_record(w, commit=C1, manifest=M3))


# KY_SOURCE_REPO absent: DEFAULT_SOURCE_REPO, but only if it exists and is itself a git work tree

@pytest.mark.parametrize("default,expected", [
    ("work-tree", "executed"), ("plain-directory", "owner_decisions_unverifiable"),
    ("missing", "owner_decisions_unverifiable"),
])
def test_without_ky_source_repo_the_default_is_used_only_if_it_is_a_git_work_tree(tmp_path, monkeypatch, default,
                                                                                    expected):
    w = World(tmp_path)
    del w.environ["KY_SOURCE_REPO"]
    if default == "work-tree":
        (w.repo / ".git").write_text("gitdir: elsewhere\n")
    monkeypatch.setattr(kyveto, "DEFAULT_SOURCE_REPO", str(tmp_path / "nowhere" if default == "missing" else w.repo))
    sid = w.propose(bundle(w))
    d = one(w.tick(AT), sid)
    if expected == "executed":                    # the default checkout answered the blob comparison
        assert d["outcome"] == "executed" and records(w) == ["ACTIVATION_RECORD.1.json"]
        assert json.loads((w.run / "ACTIVATION_RECORD.1.json").read_text())["owner_decisions"]["old_blob"] == "d" * 40
    else:                                         # a directory that would have answered is not consulted
        assert (d["outcome"], d["reason"]) == ("failed", expected) and records(w) == []


def test_the_default_checkout_really_decides_when_it_is_used(tmp_path, monkeypatch):
    w = World(tmp_path)
    del w.environ["KY_SOURCE_REPO"]
    (w.repo / ".git").write_text("gitdir: elsewhere\n")
    w.blobs({C1: "d" * 40, C2: "9" * 40})                         # there the owner decisions differ
    monkeypatch.setattr(kyveto, "DEFAULT_SOURCE_REPO", str(w.repo))
    sid = w.propose(bundle(w))
    assert one(w.tick(AT), sid)["reason"] == "owner_decisions_changed_owner_only"


def test_an_explicit_ky_source_repo_is_never_replaced_by_the_default(tmp_path, monkeypatch):
    other = tmp_path / "other-checkout"
    other.mkdir()
    (other / ".git").write_text("gitdir: elsewhere\n")
    (other / "blobs.json").write_text(json.dumps({"%s:%s" % (C1, kyveto.OWNER_DECISIONS_PATH): "d" * 40,
                                                  "%s:%s" % (C2, kyveto.OWNER_DECISIONS_PATH): "9" * 40}))
    monkeypatch.setattr(kyveto, "DEFAULT_SOURCE_REPO", str(other))             # it would say "changed"
    w = World(tmp_path)
    sid = w.propose(bundle(w))
    assert one(w.tick(AT), sid)["outcome"] == "executed"          # the explicit checkout says "unchanged"
    w2 = World(tmp_path / "second")
    (w2.repo / ".git").write_text("gitdir: elsewhere\n")
    monkeypatch.setattr(kyveto, "DEFAULT_SOURCE_REPO", str(w2.repo))           # a perfectly good default …
    w2.environ["KY_SOURCE_REPO"] = ""                                          # … but the variable is set, empty
    sid2 = w2.propose(bundle(w2))
    assert one(w2.tick(AT), sid2)["reason"] == "owner_decisions_unverifiable"


def test_the_work_tree_check_is_gits_own_answer(tmp_path, monkeypatch):
    """Read-only (`git rev-parse --show-toplevel`) against this checkout: the double is not the only evidence."""
    repo, git = FLEET.parents[3], "/usr/bin/git"
    if not os.path.lexists(repo / ".git"):
        pytest.skip("not running from a git checkout")
    environ = dict(SUB_ENV, KY_ROOT=str(tmp_path), KY_GIT=git)
    for path, expected in ((repo, str(repo)), (FLEET, None), (tmp_path, None), (tmp_path / "missing", None)):
        monkeypatch.setattr(kyveto, "DEFAULT_SOURCE_REPO", str(path))
        assert kyveto.default_source_repo(kyveto.Env(environ)) == expected, path     # inside ≠ a work tree itself
    monkeypatch.setattr(kyveto, "DEFAULT_SOURCE_REPO", str(repo))
    assert kyveto.Env(environ).repo == str(repo)                               # absent → the default
    assert kyveto.Env(dict(environ, KY_SOURCE_REPO="/explicit")).repo == "/explicit"
    assert kyveto.Env(dict(environ, KY_SOURCE_REPO="")).repo is None
    assert kyveto.Env(dict(environ, KY_GIT="/nonexistent/git")).repo is None   # git cannot answer → no default


def test_a_default_that_does_not_exist_is_refused_whatever_git_would_say(tmp_path, monkeypatch):
    git = tmp_path / "agreeable-git"                  # a `git` that calls every path a work tree's top level
    git.write_text("#!/bin/sh\nprintf '%s\\n' \"$2\"\n")
    git.chmod(0o755)
    env = kyveto.Env(dict(SUB_ENV, KY_ROOT=str(tmp_path), KY_GIT=str(git)))
    here = tmp_path / "here"
    here.mkdir()
    monkeypatch.setattr(kyveto, "DEFAULT_SOURCE_REPO", str(here))
    assert kyveto.default_source_repo(env) == str(here)            # the double alone would confirm anything …
    monkeypatch.setattr(kyveto, "DEFAULT_SOURCE_REPO", str(tmp_path / "not-there"))
    assert kyveto.default_source_repo(env) is None                 # … so existence is checked on its own
    (tmp_path / "a-file").write_text("x")
    monkeypatch.setattr(kyveto, "DEFAULT_SOURCE_REPO", str(tmp_path / "a-file"))
    assert kyveto.default_source_repo(env) is None
    monkeypatch.setattr(kyveto, "DEFAULT_SOURCE_REPO", "")
    assert kyveto.default_source_repo(env) is None


def test_bundle_change_refused_when_old_commit_is_not_the_authorised_source(tmp_path):
    chain_refusal(tmp_path, "old_commit_not_authorised_source", old_commit=C3)


def test_a_change_to_the_owner_decisions_is_owner_only(tmp_path):
    w, sid = chain_refusal(tmp_path, "owner_decisions_changed_owner_only",
                           prepare=lambda w, t: w.blobs({C1: "d" * 40, C2: "9" * 40}))
    assert w.history(sid)[-1]["reason"] == "owner_decisions_changed_owner_only"


def test_the_owner_decisions_are_compared_where_the_successor_manifest_places_them(tmp_path):
    """KX-03: a successor need not keep the root bundle's file names; its owner-decisions blob must still be the
    old one."""
    moved = "00_ARCHITECTURE/briefs/kalayantra/OWNER_DECISIONS_v1_1.md"

    def prepare_for(new_blob):
        def prepare(w, target):
            doc = manifest_doc(C2)
            doc["entrypoints"]["owner_decisions"] = {"path": moved, "sha256": "6" * 64, "git_blob": new_blob}
            target["new_manifest_path"], target["new_manifest_digest"] = write_manifest(w, C2, doc=doc, name="moved.json")
            target["review_receipts"] = [receipt(w, "review-moved.json", manifest=target["new_manifest_digest"])]
            (w.repo / "blobs.json").write_text(json.dumps({
                "%s:%s" % (C1, kyveto.OWNER_DECISIONS_PATH): "d" * 40, "%s:%s" % (C2, moved): new_blob,
                "%s:%s" % (C2, kyveto.OWNER_DECISIONS_PATH): "d" * 40}))        # the old path would say "unchanged"
        return prepare

    chain_refusal(tmp_path, "owner_decisions_changed_owner_only", prepare=prepare_for("9" * 40))
    w = World(tmp_path / "unchanged")
    target = bundle(w)
    prepare_for("d" * 40)(w, target)
    sid = w.propose(target)
    assert one(w.tick(AT), sid)["outcome"] == "executed"
    rec = json.loads((w.run / "ACTIVATION_RECORD.1.json").read_text())
    assert rec["owner_decisions"]["new_path"] == moved and rec["owner_decisions"]["path"] == kyveto.OWNER_DECISIONS_PATH
    assert_schema("activation_record", rec)


@pytest.mark.parametrize("how", ["no-repo", "unknown-commit", "git-missing"])
def test_owner_decisions_that_cannot_be_compared_are_not_assumed_unchanged(tmp_path, how):
    def prepare(w, target):
        if how == "no-repo":
            del w.environ["KY_SOURCE_REPO"]
        elif how == "unknown-commit":
            w.blobs({C1: "d" * 40})
        else:
            w.environ["KY_GIT"] = "/nonexistent/git"
    chain_refusal(tmp_path, "owner_decisions_unverifiable", prepare=prepare)


def test_changed_review_evidence_is_a_changed_target(tmp_path):
    w = World(tmp_path)
    target = bundle(w)
    sid = w.propose(target)
    Path(target["review_receipts"][0]).write_text(json.dumps(
        {"verdict": "ACCEPTED", "reviewer_session_id": "someone-else", "source_commit": C2,
         "manifest_sha256": target["new_manifest_digest"], "inputs": {"x": "1" * 64}}))
    assert one(w.tick(AT), sid)["reason"] == "target_changed"
    assert records(w) == []


def test_the_bundle_executor_is_idempotent_and_never_overwrites(tmp_path):
    w = World(tmp_path)
    change = kyveto.REGISTRY["plan_bundle_change"]
    sid = "SD-20261011T220000Z-7"
    ctx = kyveto.Ctx(w.env, sid, ROOT_AUTHORITY, AT, sessions=["surrogate-1"])
    params = bundle(w)
    assert change.observer(params, ctx)[0] == "not_done"
    ok, first = change.execute(params, ctx)
    assert ok is True and records(w) == ["ACTIVATION_RECORD.1.json"]
    before = (w.run / "ACTIVATION_RECORD.1.json").read_bytes()
    ok, again = change.execute(params, ctx)                       # the same decision again: the same record
    assert ok is True and again == first and records(w) == ["ACTIVATION_RECORD.1.json"]
    assert (w.run / "ACTIVATION_RECORD.1.json").read_bytes() == before
    outcome, observed = change.observer(params, ctx)
    assert outcome == "done" and observed == first
    other = kyveto.Ctx(w.env, "SD-20261011T220000Z-8", ROOT_AUTHORITY, AT, sessions=["surrogate-1"])
    ok, refused_ = change.execute(params, other)                  # another decision cannot replay the same step
    assert ok is False and refused_["reason"].startswith("activation_chain_mismatch")
    assert records(w) == ["ACTIVATION_RECORD.1.json"]


def test_owner_decisions_blob_comparison_against_the_real_repository():
    """Read-only (`git rev-parse` only) against this checkout: the double is not the only evidence."""
    repo, git = FLEET.parents[3], "/usr/bin/git"

    def commit(rev):
        r = subprocess.run([git, "-C", str(repo), "rev-parse", "--verify", "--quiet", rev + "^{commit}"],
                           capture_output=True, text=True)
        return r.stdout.strip() if r.returncode == 0 else None

    head, same, differs = commit("e709f60d7"), commit("0a36f321e"), commit("fcbc06437")
    if not (head and same and differs):
        pytest.skip("the plan's source commits are not present in this checkout")
    env = kyveto.Env(dict(SUB_ENV, KY_ROOT="/nonexistent", KY_SOURCE_REPO=str(repo), KY_GIT=git))
    blob = kyveto.owner_decisions_blob(env, head)
    assert blob and len(blob) == 40
    assert kyveto.owner_decisions_blob(env, same) == blob                 # unchanged since plan v2.5
    assert kyveto.owner_decisions_blob(env, differs) not in (None, blob)  # v2.4's owner decisions were different
    assert kyveto.owner_decisions_blob(env, "0" * 40) is None             # an unknown commit is unknown, not equal
    assert kyveto.owner_decisions_blob(env, "HEAD") is None               # only full commit ids are compared
    assert kyveto.owner_decisions_blob(env, head, kyveto.OWNER_DECISIONS_PATH) == blob
    for path in ("/etc/passwd", "../x", "a:b", "-x", ""):                 # only a plain repository-relative path
        assert kyveto.owner_decisions_blob(env, head, path) is None


# ── classes whose executors are later deliverables: never a faked success ──

@pytest.mark.parametrize("kind,helper", [("campaign_start", "kygate.sh"), ("protected_window", "executor.py")])
def test_classes_without_an_installed_executor_fail_closed(tmp_path, kind, helper):
    w = World(tmp_path)
    sid = w.propose({"kind": kind, "item": "N-467", "tracker_decision": TD})
    d = one(w.tick(AT), sid)
    assert (d["outcome"], d["reason"], d["attention"]) == ("failed", "executor_unavailable: " + helper, True)
    assert w.ky_calls() == [] and w.actions() == []                   # nothing published for what cannot be executed
    assert not (w.run / "OWNER_RESUME.json").exists()
    # the helper's mere presence is not an executor either
    (w.fleet / helper).write_text("#!/bin/bash\nexit 0\n")
    os.chmod(w.fleet / helper, 0o755)
    sid2 = w.propose({"kind": kind, "item": "N-467"})
    d2 = one(w.tick(AFTER), sid2)
    assert d2["outcome"] == "failed" and d2["reason"].startswith("executor_unavailable: ")
    assert "later deliverable" in d2["reason"] and not (w.run / "OWNER_RESUME.json").exists()
    ctx = kyveto.Ctx(w.env, sid2, ROOT_AUTHORITY, AT)
    ok, result = kyveto.REGISTRY[kind].execute({"kind": kind}, ctx)
    assert ok is False and result["reason"].startswith("executor_unavailable")
    assert kyveto.REGISTRY[kind].observer({"kind": kind}, ctx)[0] == "unknown"


def test_a_merge_class_is_stopped_by_hold_merges(tmp_path):
    w = World(tmp_path)

    class Merge(kyveto.Capacity):
        kind = "test_merge"
        merge_action = True

    kyveto.REGISTRY["test_merge"] = Merge()
    try:
        (w.run / "HOLD_MERGES").write_text("certification\n")
        sid = w.propose({"kind": "test_merge", "builders": 6, "verifiers": 4})
        assert one(w.tick(AT), sid)["reason"] == "class_hold: HOLD_MERGES"
        other = w.propose(cap(builders=5))                # HOLD_MERGES does not concern a capacity decision
        assert one(w.tick(AT), other)["outcome"] == "executed"
    finally:
        del kyveto.REGISTRY["test_merge"]
    assert w.capacity() == ("5\n", "4\n")


# ── veto between effectiveness and execution; status ──

def test_a_veto_after_publication_but_before_execution_still_prevents_execution(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap(tracker_decision=TD))
    w.crash("before-execute", "tick")                     # published and EFFECTIVE, executor not yet run
    cid = w.veto(sid)
    report = w.tick(AFTER)
    assert one(report, sid)["outcome"] == "vetoed"
    assert w.states(sid) == ["PENDING_VETO", "EFFECTIVE", "VETOED"] and w.capacity() == ("3\n", "2\n")
    vetoed = w.history(sid)[-1]
    assert vetoed["detail"]["published"] is True          # the tracker decision is out: the owner must be told
    assert w.action(sid + ".execute")["state"] == "FAILED" and w.command(cid)["state"] == "APPLIED"
    assert report["attention"] is True
    assert w.tick(LATER)["decisions"] == [] and w.capacity() == ("3\n", "2\n")


def test_a_veto_that_arrives_during_the_recheck_stops_the_publication(tmp_path, monkeypatch):
    w = World(tmp_path)
    sid = w.propose(cap(tracker_decision=TD))
    capacity = kyveto.REGISTRY["capacity"]
    seen = []

    def precheck(params, ctx):               # the owner's veto lands after step (3), while (6) is still running
        seen.append(w.veto(sid))
        return None

    monkeypatch.setattr(capacity, "precheck", precheck)
    report = w.tick(AT)
    assert one(report, sid)["outcome"] == "vetoed" and len(seen) == 1
    assert w.states(sid) == ["PENDING_VETO", "VETOED"] and w.ky_calls() == [] and w.capacity() == ("3\n", "2\n")
    assert w.history(sid)[-1]["detail"] == {"command": seen[0], "published": False}
    assert report["attention"] is False and w.actions() == ["CMD-%s.json" % seen[0]]


def test_a_veto_that_arrives_during_the_publication_stops_the_execution(tmp_path, monkeypatch):
    w = World(tmp_path)
    sid = w.propose(cap(tracker_decision=TD))
    real, seen = kyveto.run_ky, []

    def publish_while_the_owner_vetoes(argv, env):
        seen.append(w.veto(sid))
        return real(argv, env)

    monkeypatch.setattr(kyveto, "run_ky", publish_while_the_owner_vetoes)
    report = w.tick(AT)
    assert one(report, sid)["outcome"] == "vetoed" and report["attention"] is True      # published, then vetoed
    assert w.states(sid) == ["PENDING_VETO", "EFFECTIVE", "VETOED"] and w.capacity() == ("3\n", "2\n")
    assert w.history(sid)[-1]["detail"] == {"command": seen[0], "published": True}
    assert sid + ".execute.json" not in w.actions() and len(w.ky_calls()) == 1
    assert w.command(seen[0])["state"] == "APPLIED"


def test_a_veto_of_a_decision_that_published_nothing_raises_no_alarm(tmp_path):
    """`<id>.publish` is DONE for every effective decision; "published" means the TRACKER holds a decision."""
    w = World(tmp_path)
    sid = w.propose(cap())                                # no tracker decision named
    w.crash("before-execute", "tick")
    w.veto(sid)
    report = w.tick(AFTER)
    assert one(report, sid)["outcome"] == "vetoed" and report["attention"] is False
    assert w.history(sid)[-1]["detail"]["published"] is False and w.capacity() == ("3\n", "2\n")


def test_a_veto_after_the_effect_is_in_place_is_too_late(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap())
    w.crash("after-execute", "tick")                      # the capacity files are already written
    cid = w.veto(sid)
    assert one(w.tick(AFTER), sid)["outcome"] == "executed"
    assert w.states(sid)[-1] == "EXECUTED" and w.command(cid)["state"] == "REJECTED"
    assert w.command(cid)["result"]["reason"].startswith("too_late")


def test_status_reports_states_and_changes_nothing(tmp_path):
    w = World(tmp_path)
    pending = w.propose(cap(tracker_decision=TD))
    vetoed = w.propose(cap(builders=5))
    unseen = w.propose(cap(builders=7), seen=None)        # no tick has seen it yet: its window has not begun
    w.veto(vetoed)
    (w.root / "HOLD").write_text("x\n")
    before = tree(w.run, skip=())
    r = w.cli("status", "--now", BEFORE)
    assert r.returncode == 0, r.stderr
    status = json.loads(r.stdout)
    assert tree(w.run, skip=()) == before and w.ky_calls() == []       # read-only: no lock, no line, no stamp, no call
    by_id = {d["id"]: d for d in status["decisions"]}
    assert by_id[pending]["state"] == "PENDING_VETO" and by_id[pending]["seconds_remaining"] == 1200
    assert by_id[pending]["effective_not_before"] == T_DEADLINE and by_id[pending]["first_seen_at"] == T_NOTIFY
    assert by_id[pending]["veto_command"] is None and by_id[vetoed]["veto_command"]
    assert by_id[pending]["notification_submitted"] is True and by_id[pending]["kind"] == "capacity"
    assert by_id[unseen]["first_seen_at"] is None and by_id[unseen]["effective_not_before"] is None
    assert "seconds_remaining" not in by_id[unseen]
    assert status["holds"] == ["HOLD"] and status["authority"]["source"] == "planner_state"
    assert status["now"] == BEFORE and status["hard_stops"] == []
    w.tick(BEFORE)
    after = json.loads(w.cli("status", "--now", BEFORE).stdout)
    assert {d["id"]: d["state"] for d in after["decisions"]} == {pending: "PENDING_VETO", vetoed: "VETOED",
                                                                 unseen: "PENDING_VETO"}
    assert {d["id"]: d for d in after["decisions"]}[unseen]["seconds_remaining"] == 1800


def test_a_veto_class_decision_made_effective_outside_the_handler_is_flagged_and_blocked(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap(), state="EFFECTIVE", effective_at=AT)        # the surrogate published it by itself
    r = w.cli("status", "--now", AFTER)
    (row,) = json.loads(r.stdout)["decisions"]
    assert r.returncode == 3 and row["anomaly"] == "log_claims_effective_without_action_record"
    assert row["made_effective_by_handler"] is False
    report = w.tick(AFTER)                                # ruling R3: an anomaly, attention, that decision blocked
    d = one(report, sid)
    assert (d["outcome"], d["reason"], d["attention"]) == ("failed", "log_claims_effective_without_action_record", True)
    assert w.states(sid) == ["EFFECTIVE", "FAILED"] and w.untouched()                 # and it is not executed here
    assert w.history(sid)[-1]["effective_at"] is None     # the handler never copies a claim out of the log
    assert w.tick(LATER)["decisions"] == []
    r = w.cli("status")                                   # answered by a tick: no longer something to attend to
    (row,) = json.loads(r.stdout)["decisions"]
    assert r.returncode == 0 and row["state"] == "FAILED" and "anomaly" not in row


def test_status_reports_an_unknown_authority_and_log_problems_as_such(tmp_path):
    w = World(tmp_path)
    w.propose(cap())
    (w.run / "PLANNER_STATE.json").unlink()
    with open(w.log, "a") as f:
        f.write("not json\n")
    r = w.cli("status", "--now", BEFORE)
    status = json.loads(r.stdout)
    assert r.returncode == 3 and status["authority"]["source"] == "unknown" and status["problems"]


def test_usage_errors(tmp_path):
    w = World(tmp_path)
    assert w.cli().returncode == 64
    assert w.cli("tick", "--now", "tomorrow").returncode == 64
    assert w.cli("tick", "--now", AT).returncode == 64             # however well-formed: the tick has no clock option
    assert w.cli("status", "--now", "tomorrow").returncode == 64
    assert w.cli("status", "--as", "x").returncode == 64
    assert w.cli("tock").returncode == 64
    assert w.cli("tick", "--authorised-commit", "xyz", "--entrypoints-digest", E1).returncode == 64
    gone = dict(w.environ, KY_RUN=str(tmp_path / "no-such-run"))
    r = subprocess.run([PY, str(FLEET / "kyveto.py"), "tick"], capture_output=True, text=True, env=gone)
    assert r.returncode == 66 and not (tmp_path / "no-such-run").exists()       # never creates a run tree


# ── C3-01 (review round 3): the capacity pair is one effect that can be told apart from nothing ──

def effect_of(w, sid, **params):
    rec = w.action(sid + ".execute")
    ctx = kyveto.Ctx(w.env, sid, None, None)
    return kyveto.REGISTRY["capacity"].effect(cap(**params), ctx, rec["inputs"].get("before"))


def test_the_before_values_are_recorded_with_the_intended_record(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap())
    assert w.crash("between-files", "tick").returncode == -signal.SIGKILL
    rec = w.action(sid + ".execute")
    assert rec["state"] == "INTENDED" and rec["inputs"]["before"] == {"KY_WORKERS": "3\n", "KY_VERIFIERS": "2\n"}
    assert_schema("action", rec)
    answer, detail = effect_of(w, sid)                    # half the pair is NOT nothing
    assert answer == "partial" and detail["in_place"] == ["KY_WORKERS"] and detail["foreign"] == []
    assert one(w.tick(AFTER), sid)["outcome"] == "executed" and w.capacity() == ("6\n", "4\n")
    done = w.action(sid + ".execute")                     # finished under the same record, the same before values
    assert done["state"] == "DONE" and done["inputs"] == rec["inputs"]


def test_the_effect_in_place_has_three_answers_and_absent_is_observed(tmp_path):
    w = World(tmp_path)
    capacity, ctx = kyveto.REGISTRY["capacity"], kyveto.Ctx(World(tmp_path / "w2").env, "SD-1", None, None)
    run = ctx.env.run
    before = capacity.before(cap(), ctx)
    assert before == {"KY_WORKERS": "3\n", "KY_VERIFIERS": "2\n"}
    assert capacity.effect(cap(), ctx, before)[0] == "absent"
    (run / "KY_VERIFIERS").write_text("4\n")
    assert capacity.effect(cap(), ctx, before) == ("partial", {
        "before": {"KY_WORKERS": "3", "KY_VERIFIERS": "2"}, "observed": {"KY_WORKERS": "3", "KY_VERIFIERS": "4"},
        "in_place": ["KY_VERIFIERS"], "foreign": []})
    (run / "KY_WORKERS").write_text("7\n")                # somebody else's value: neither before nor this change's
    answer, detail = capacity.effect(cap(), ctx, before)
    assert answer == "partial" and detail["foreign"] == ["KY_WORKERS"] and detail["in_place"] == ["KY_VERIFIERS"]
    (run / "KY_WORKERS").unlink()                         # a file that vanished is not "nothing in place" either
    assert capacity.effect(cap(), ctx, before)[1]["foreign"] == ["KY_WORKERS"]
    for unrecorded in (None, {}, {"KY_WORKERS": "3\n"}, {"KY_WORKERS": 3, "KY_VERIFIERS": "2\n"}):
        assert capacity.effect(cap(), ctx, unrecorded) == ("unknown", {"error": "before_values_not_recorded"})
    (run / "KY_WORKERS").write_bytes(b"\xff\xfe")
    assert capacity.effect(cap(), ctx, before)[0] == "unknown"
    (run / "KY_WORKERS").write_text("6" * 5000)
    with pytest.raises(ValueError):
        capacity.before(cap(), ctx)                       # what could not be put back exactly is not recorded
    capacity.restore(cap(), ctx, {"KY_WORKERS": None, "KY_VERIFIERS": "2\n"}, ["KY_WORKERS", "KY_VERIFIERS"])
    assert not (run / "KY_WORKERS").exists() and (run / "KY_VERIFIERS").read_text() == "2\n"
    assert w.capacity() == ("3\n", "2\n")                 # the other world was never touched


def test_a_veto_after_a_crash_between_the_two_capacity_files_puts_the_written_half_back(tmp_path):
    """The reviewer's probe: KY_WORKERS already 6, KY_VERIFIERS still 2, the record INTENDED, then the veto."""
    w = World(tmp_path)
    sid = w.propose(cap())
    assert w.crash("between-files", "tick").returncode == -signal.SIGKILL
    assert w.capacity() == ("6\n", "2\n") and w.action(sid + ".execute")["state"] == "INTENDED"
    cid = w.veto(sid)
    report = w.tick(AFTER)
    d = one(report, sid)
    assert (d["outcome"], d["partial_effect"], d["attention"]) == ("vetoed", "restored", True)
    assert report["attention"] is True                    # the vetoed value was in force for a while: said, not hidden
    assert w.capacity() == ("3\n", "2\n")                 # … and the dispatcher no longer reads it
    rec = w.action(sid + ".execute")
    assert rec["state"] == "FAILED" and rec["result"]["reason"] == "vetoed_partial_effect_restored"
    partial = rec["result"]["partial_effect"]
    assert partial["state"] == "restored" and partial["restored"] == ["KY_WORKERS"]
    assert partial["was"] == {"KY_WORKERS": "6", "KY_VERIFIERS": "2"}
    assert partial["observed"] == partial["before"] == {"KY_WORKERS": "3", "KY_VERIFIERS": "2"}
    assert rec["reconciliations"][0]["detail"]["incomplete"] == ["KY_VERIFIERS"]
    line = w.history(sid)[-1]
    assert line["state"] == "VETOED" and line["detail"]["partial_effect"] == partial
    assert w.command(cid)["state"] == "APPLIED"
    rc, status, row = status_row(w, sid)                  # put back and verified: nothing left to attend to
    assert rc == 0 and row["partial_effect"] == "restored" and "unresolved" not in row
    assert status["partial_effects"] == [] and w.tick(LATER)["decisions"] == []


@pytest.mark.parametrize("why", ["foreign-value", "restore-raises", "restore-does-nothing"])
def test_a_partial_effect_that_is_not_put_back_is_reported_never_called_unexecuted(tmp_path, monkeypatch, why):
    w = World(tmp_path)
    sid = w.propose(cap())
    assert w.crash("between-files", "tick").returncode == -signal.SIGKILL
    capacity = kyveto.REGISTRY["capacity"]
    if why == "foreign-value":
        (w.run / "KY_VERIFIERS").write_text("5\n")        # not the before value, not this change's: not ours to undo
    elif why == "restore-raises":
        def broken(p, ctx, before, names):
            raise OSError("read-only file system")
        monkeypatch.setattr(capacity, "restore", broken)
    else:
        monkeypatch.setattr(capacity, "restore", lambda p, ctx, before, names: None)
    left = w.capacity()
    cid = w.veto(sid)
    report = w.tick(AFTER)
    d = one(report, sid)
    assert (d["outcome"], d["partial_effect"], d["attention"]) == ("vetoed", "in_place", True)
    assert report["attention"] is True and w.capacity() == left and left[0] == "6\n"
    rec = w.action(sid + ".execute")
    assert rec["state"] == "FAILED" and rec["result"]["reason"] == "vetoed_with_partial_effect"
    partial = rec["result"]["partial_effect"]
    assert partial["state"] == "in_place" and partial["in_place"] == ["KY_WORKERS"]
    assert partial["foreign"] == (["KY_VERIFIERS"] if why == "foreign-value" else [])
    assert ("restore_error" in partial) == (why == "restore-raises")
    line = w.history(sid)[-1]
    assert line["state"] == "VETOED" and line["detail"]["partial_effect"]["state"] == "in_place"
    assert w.command(cid)["state"] == "APPLIED"
    monkeypatch.undo()
    rc, status, row = status_row(w, sid)                  # still in place: unresolved for as long as that is so
    assert rc == 3 and row["partial_effect"] == "in_place" and row["unresolved"] is True
    assert status["partial_effects"] == [sid] and status["attention"] is True
    assert w.tick(LATER)["decisions"] == [] and w.capacity() == left         # final for the handler; nothing retried
    (w.run / "KY_WORKERS").write_text("3\n")              # the owner puts the pair back
    (w.run / "KY_VERIFIERS").write_text("2\n")
    rc, status, row = status_row(w, sid)                  # … and a FRESH look, not the record, says so
    assert rc == 0 and row["partial_effect"] == "no_longer_in_place" and "unresolved" not in row
    assert status["partial_effects"] == []


def test_vetoed_before_execution_is_recorded_only_after_nothing_was_observed_in_place(tmp_path):
    w = World(tmp_path)
    clean, unknown = w.propose(cap()), None
    w.crash("before-execute", "tick")
    w.veto(clean)
    d = one(w.tick(AFTER), clean)
    assert d["outcome"] == "vetoed" and "partial_effect" not in d and "attention" not in d
    rec = w.action(clean + ".execute")
    assert rec["result"] == {"command": d["command"], "reason": "vetoed_before_execution"}
    assert "partial_effect" not in w.history(clean)[-1]["detail"]
    # a record that holds no before values (written before this rule): "nothing happened" cannot be observed
    w2 = World(tmp_path / "w2")
    unknown = w2.propose(cap())
    w2.crash("before-execute", "tick")
    path = w2.run / "actions" / (unknown + ".execute.json")
    doc = json.loads(path.read_text())
    del doc["inputs"]["before"]
    path.write_text(json.dumps(doc))
    cid = w2.veto(unknown)
    for now in (AFTER, LATER):                            # on every tick, until somebody has looked
        report = w2.tick(now)
        d = one(report, unknown)
        assert (d["outcome"], d["reason"], d["attention"]) == (
            "blocked", "execution_unreconciled: before_values_not_recorded", True)
        assert report["attention"] is True
    assert w2.action(unknown + ".execute")["state"] == "INTENDED" and w2.command(cid)["state"] == "QUEUED"
    assert w2.states(unknown) == ["PENDING_VETO", "EFFECTIVE"]


@pytest.mark.parametrize("restorable", [True, False])
def test_an_executor_error_on_the_second_capacity_file_is_put_back_or_reported(tmp_path, monkeypatch, restorable):
    w = World(tmp_path)
    sid = w.propose(cap(tracker_decision=TD))
    real, pool = kyaction.write_atomic, []

    def flaky(path, data, mode=None):                     # the first pool file is written, then the disk gives up
        if Path(path).name in ("KY_WORKERS", "KY_VERIFIERS"):
            pool.append(Path(path).name)
            if len(pool) == 2 or (len(pool) > 2 and not restorable):
                raise OSError("disk full")
        return real(path, data, mode)

    monkeypatch.setattr(kyaction, "write_atomic", flaky)
    report = w.tick(AT)
    monkeypatch.undo()
    d = one(report, sid)
    assert (d["outcome"], d["reason"]) == ("failed", "execution_failed: executor_error: OSError")
    assert d["attention"] is True and d["published"] is True and pool[:3] == ["KY_WORKERS", "KY_VERIFIERS", "KY_WORKERS"]
    state = "restored" if restorable else "in_place"
    assert d["partial_effect"] == state
    assert w.capacity() == (("3\n", "2\n") if restorable else ("6\n", "2\n"))
    rec = w.action(sid + ".execute")
    assert rec["state"] == "FAILED" and rec["result"]["reason"] == "executor_error: OSError"
    assert rec["result"]["partial_effect"]["state"] == state
    assert rec["inputs"]["before"] == {"KY_WORKERS": "3\n", "KY_VERIFIERS": "2\n"}
    line = w.history(sid)[-1]
    assert line["state"] == "FAILED" and line["detail"]["published"] is True
    assert line["detail"]["partial_effect"] == rec["result"]["partial_effect"]
    rc, status, row = status_row(w, sid)
    assert row["partial_effect"] == state and status["partial_effects"] == ([] if restorable else [sid])
    assert (rc, row.get("unresolved")) == ((0, None) if restorable else (3, True))
    left = w.capacity()
    assert w.tick(LATER)["decisions"] == [] and w.capacity() == left and len(w.ky_calls()) == 1      # never retried


def test_a_failed_execution_found_after_a_restart_still_names_its_partial_effect(tmp_path, monkeypatch):
    """The handler died between closing `<id>.execute` FAILED and its FAILED line: the next tick says both."""
    w = World(tmp_path)
    sid = w.propose(cap())
    w.crash("between-files", "tick")
    (w.run / "KY_VERIFIERS").write_text("5\n")
    partial = {"state": "in_place", "in_place": ["KY_WORKERS"], "foreign": ["KY_VERIFIERS"]}
    kyaction.fail(w.run, sid + ".execute", {"reason": "executor_error: OSError", "partial_effect": partial})
    d = one(w.tick(AFTER), sid)
    assert (d["outcome"], d["partial_effect"], d["attention"]) == ("failed", "in_place", True)
    assert w.history(sid)[-1]["detail"] == {"partial_effect": partial}
    assert status_row(w, sid)[2]["unresolved"] is True


# ── C3-02 (review round 3): a line that steps back takes a decision out of nothing ──

def step_back(w, sid, state="PROPOSED", **over):
    """The surrogate re-rules an unchanged item under the same id: one more line, an earlier state."""
    w.append(dict(w.history(sid)[0], state=state, **over))


def test_needs_handler_once_in_the_window_whatever_the_latest_line_says():
    veto = {"class": "veto"}
    lines = [dict(veto, state="PENDING_VETO"), dict(veto, state="PROPOSED")]
    assert kyveto.needs_handler(lines, False) is True and kyveto.regressed(lines) is True
    assert kyveto.needs_handler([dict(veto, state="PROPOSED")], False) is False          # not yet in its window
    assert kyveto.needs_handler([dict(veto, state="PROPOSED")], False, begun=True) is True
    assert kyveto.needs_handler([{"class": "routine", "state": "EXECUTED"}], False) is False
    assert kyveto.needs_handler(lines + [dict(veto, state="VETOED")], False) is False    # an accepted terminal state
    assert kyveto.regressed([dict(veto, state="PROPOSED"), dict(veto, state="PENDING_VETO")]) is False
    assert kyveto.regressed([dict(veto, state="PENDING_VETO"), dict(veto, state="EFFECTIVE"),
                             dict(veto, state="PENDING_VETO")]) is True
    assert kyveto.accepted_state(lines, False, False) == "PENDING_VETO"
    assert kyveto.accepted_state(lines, True, False) == "EFFECTIVE"


def test_a_proposed_line_after_pending_veto_does_not_take_the_decision_out_of_the_handler(tmp_path):
    """Probe 1: PENDING_VETO, then PROPOSED under the same id. The decision carries on from the handler's memory
    (the proposal and its stamp); the step back is an anomaly somebody is told about."""
    w = World(tmp_path)
    sid = w.propose(cap(tracker_decision=TD))
    step_back(w, sid)
    report = w.tick(BEFORE)
    d = one(report, sid)
    assert (d["outcome"], d["seconds_remaining"]) == ("pending", 1200)
    assert d["anomaly"] == "line_regressed_before_terminal_state" and d["attention"] is True
    assert report["attention"] is True and w.untouched()
    r = w.cli("status", "--now", BEFORE)
    (row,) = json.loads(r.stdout)["decisions"]
    assert r.returncode == 3 and (row["state"], row["latest_line_state"]) == ("PENDING_VETO", "PROPOSED")
    assert row["unresolved"] is True and row["anomaly"] == "line_regressed_before_terminal_state"
    assert row["seconds_remaining"] == 1200
    report = w.tick(AT)                                   # at expiry the owner's notification IS answered
    d = one(report, sid)
    assert d["outcome"] == "executed" and d["anomaly"] == "line_regressed_before_terminal_state"
    assert report["attention"] is True and w.capacity() == ("6\n", "4\n") and len(w.ky_calls()) == 1
    assert w.states(sid) == ["PENDING_VETO", "PROPOSED", "EFFECTIVE", "EXECUTED"]
    assert w.tick(LATER)["decisions"] == []
    rc, status, row = status_row(w, sid)                  # answered by the handler's own lines
    assert rc == 0 and row["state"] == "EXECUTED" and "anomaly" not in row and "unresolved" not in row


def test_an_owner_veto_is_still_answered_after_a_line_stepped_back(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap(tracker_decision=TD))
    step_back(w, sid)
    cid = w.veto(sid)
    d = one(w.tick(BEFORE), sid)
    assert d["outcome"] == "vetoed" and d["anomaly"] == "line_regressed_before_terminal_state"
    assert w.states(sid) == ["PENDING_VETO", "PROPOSED", "VETOED"] and w.command(cid)["state"] == "APPLIED"
    assert w.tick(AT)["decisions"] == [] and w.ky_calls() == [] and w.capacity() == ("3\n", "2\n")


def test_a_step_back_that_changes_what_the_owner_was_told_fails_by_name(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap(tracker_decision=TD))
    step_back(w, sid, decision="raise capacity and merge PR 1")
    d = one(w.tick(AT), sid)
    assert (d["outcome"], d["reason"], d["attention"]) == ("failed", "decision_record_mutated: decision", True)
    assert "published" not in d and w.untouched()         # three-valued: here positively nothing was published
    assert w.states(sid) == ["PENDING_VETO", "PROPOSED", "FAILED"]


def test_a_proposed_line_after_publication_does_not_strand_the_execution(tmp_path):
    """Probe 2: the handler has published (`ky decide` ran, EFFECTIVE, `<id>.execute` INTENDED), then PROPOSED is
    appended. Before: no tick ever looked again and status said PROPOSED, exit 0, with a delegated approval in
    the tracker that nobody executed."""
    w = World(tmp_path)
    sid = w.propose(cap(tracker_decision=TD))
    assert w.crash("before-execute", "tick").returncode == -signal.SIGKILL
    assert len(w.ky_calls()) == 1 and w.action(sid + ".execute")["state"] == "INTENDED"
    step_back(w, sid)
    rc, status, row = status_row(w, sid)
    assert rc == 3 and (row["state"], row["latest_line_state"]) == ("EFFECTIVE", "PROPOSED")
    assert row["unresolved"] is True and row["published"] is True and row["made_effective_by_handler"] is True
    assert row["anomaly"] == "line_regressed_before_terminal_state"
    assert status["unfinished_actions"] == [sid + ".execute"]
    report = w.tick(AFTER)
    d = one(report, sid)
    assert d["outcome"] == "executed" and d["anomaly"] == "line_regressed_before_terminal_state"
    assert report["attention"] is True and w.capacity() == ("6\n", "4\n") and len(w.ky_calls()) == 1
    assert w.states(sid) == ["PENDING_VETO", "EFFECTIVE", "PROPOSED", "EXECUTED"]
    assert w.action(sid + ".execute")["state"] == "DONE"
    assert w.tick(LATER)["decisions"] == []
    rc, status, row = status_row(w, sid)
    assert rc == 0 and row["state"] == "EXECUTED" and status["unfinished_actions"] == []


def test_handler_records_without_a_proposal_in_the_log_are_answered_not_ignored(tmp_path):
    """The log was rewritten to a lone PROPOSED line while the handler holds action records for the id."""
    w = World(tmp_path)
    sid = w.propose(cap(tracker_decision=TD))
    w.crash("before-execute", "tick")
    w.log.write_text(json.dumps(dict(w.history(sid)[0], state="PROPOSED")) + "\n")
    rc, status, row = status_row(w, sid)
    assert rc == 3 and row["anomaly"] == "proposal_missing" and row["unresolved"] is True
    assert row["state"] == "EFFECTIVE"                    # the handler's own publication record says so
    d = one(w.tick(AFTER), sid)
    assert (d["outcome"], d["reason"], d["published"], d["attention"]) == ("failed", "proposal_missing", True, True)
    assert w.capacity() == ("3\n", "2\n") and w.states(sid) == ["PROPOSED", "FAILED"]


# ── C3-06 (review round 3): an EXECUTED line carries effective_at, as the decision schema requires ──

def test_an_executed_line_must_carry_effective_at(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap())
    w.tick(AT)
    proposal, effective, executed = w.history(sid)
    assert executed["state"] == "EXECUTED" and executed["effective_at"] == AT
    assert kyveto.line_problem(executed) is None and kyveto.line_problem(effective) is None
    for line in (effective, executed):
        assert kyveto.line_problem(dict(line, effective_at=None)) == (
            "line_malformed: an %s line carries effective_at" % line["state"])
        assert schema_errors("surrogate_decision", dict(line, effective_at=None))      # the schema agrees
    assert kyveto.line_problem(dict(executed, state="VETOED", effective_at=None)) is None
    handler = kyveto.Handler(w.env, kyaction.parse_utc(AT), None, "ctl-veto", "controller", None, None)
    before = w.log.read_bytes()
    with pytest.raises(kyveto.Unwritable):
        handler.append(executed, "EXECUTED", "executed", None)
    assert w.log.read_bytes() == before                   # nothing was written


# ── C4-01 (review round 4, ruling R14): VETOED / FAILED is final by the handler's own records, never by a line ──

TERMINAL_CLAIM = "terminal_line_not_the_handlers"


def surrogate_line(w, sid, state, **over):
    """One more line under a decision's id as the surrogate writes it when it re-rules a blocked item."""
    line = dict(w.history(sid)[0], state=state, by=kyveto.SURROGATE, session="surrogate-2", reason="re-ruled")
    line.update(over)
    w.append(line)


def half_executed(w, **target):
    """The reviewer's half state: the handler was killed between the two capacity files. → the decision id."""
    sid = w.propose(cap(**target))
    assert w.crash("between-files", "tick").returncode == -signal.SIGKILL
    assert w.capacity() == ("6\n", "2\n") and w.action(sid + ".execute")["state"] == "INTENDED"
    assert w.states(sid) == ["PENDING_VETO", "EFFECTIVE"]
    return sid


def test_a_terminal_line_is_final_by_the_handlers_records_not_by_its_author():
    """The state rule itself: `held` — the handler holds an action record for the decision; `closed` — the state
    the handler closed it with itself (its own marker), which the caller withholds while `<id>.execute` is
    INTENDED or DONE."""
    veto = {"class": "veto"}
    lines = [dict(veto, state="PENDING_VETO"), dict(veto, state="EFFECTIVE")]
    for claim in ("FAILED", "VETOED"):
        for by in ("kyveto", kyveto.SURROGATE):                       # who a line says wrote it plays no part
            claimed = lines + [dict(veto, state=claim, by=by)]
            assert kyveto.first_terminal(claimed, False) == claim     # no record of the handler's: nothing is out
            assert kyveto.first_terminal(claimed, False, held=True) is None
            assert kyveto.first_terminal(claimed, False, held=True, closed=claim) == claim
            assert kyveto.first_terminal(claimed, True, held=True, closed=claim) is None      # executed: EXECUTED only
            assert kyveto.first_terminal(claimed + [dict(veto, state="EXECUTED")], True, held=True) == "EXECUTED"
            assert kyveto.first_terminal(claimed + [dict(veto, state="EXECUTED")], False, held=True) is None
            assert kyveto.needs_handler(claimed, False, begun=True) is True
            assert kyveto.needs_handler(claimed, False, begun=True, closed=claim) is False
            assert kyveto.needs_handler(claimed, True, begun=True, closed=claim) is True
            assert kyveto.needs_handler(claimed, False) is False
            assert kyveto.accepted_state(claimed, True, False) == "EFFECTIVE"
            assert kyveto.accepted_state(claimed, True, False, closed=claim) == claim
            assert kyveto.accepted_state(claimed, True, True, closed=claim) == "EFFECTIVE"
            assert kyveto.accepted_state(claimed, False, False, begun=True) == "PENDING_VETO"
            assert kyveto.accepted_state(claimed, False, False) == claim
    other = lines + [dict(veto, state="VETOED"), dict(veto, state="FAILED")]
    assert kyveto.first_terminal(other, False, held=True, closed="FAILED") == "FAILED"         # the handler's own word
    assert kyveto.first_terminal(other, False, held=True, closed="EXECUTED") is None
    assert kyveto.first_terminal(other, False) == "VETOED"


@pytest.mark.parametrize("restorable", [True, False])
def test_an_executed_claim_over_a_half_written_effect_is_undone_not_only_failed(tmp_path, restorable):
    """Probe (a): the handler was killed between the two capacity files (KY_WORKERS 6, KY_VERIFIERS 2, execute
    INTENDED), then an EXECUTED line appears in the log. Before: FAILED log_claims_executed_without_action_record
    without a look at what was in place — the record stayed INTENDED, KY_WORKERS kept 6, the next tick reported
    nothing and `status` read FAILED, attention false, partial_effects empty."""
    w = World(tmp_path)
    sid = half_executed(w, tracker_decision=TD)
    if not restorable:
        (w.run / "KY_VERIFIERS").write_text("5\n")        # not the before value, not this change's: not ours to undo
    left = w.capacity()
    surrogate_line(w, sid, "EXECUTED", effective_at=AT)
    report = w.tick(AFTER)
    d = one(report, sid)
    assert (d["outcome"], d["reason"]) == ("failed", "log_claims_executed_without_action_record")
    assert d["anomaly"] == "log_claim_without_action_record" and d["attention"] is True and report["attention"] is True
    state = "restored" if restorable else "in_place"
    assert d["partial_effect"] == state and d["published"] is True
    assert w.capacity() == (("3\n", "2\n") if restorable else left)
    rec = w.action(sid + ".execute")
    assert rec["state"] == "FAILED" and rec["result"]["because"] == "log_claims_executed_without_action_record"
    assert rec["result"]["reason"] == ("given_up_partial_effect_restored" if restorable else "given_up_with_partial_effect")
    partial = rec["result"]["partial_effect"]
    assert partial["state"] == state and partial["in_place" if not restorable else "restored"] == ["KY_WORKERS"]
    assert rec["reconciliations"][0]["detail"]["incomplete"] == ["KY_VERIFIERS"]
    assert_schema("action", rec)
    line = w.history(sid)[-1]
    assert (line["state"], line["by"], line["reason"]) == ("FAILED", "kyveto", d["reason"])
    assert line["detail"] == {"published": True, "partial_effect": partial}
    assert w.tick(LATER)["decisions"] == [] and w.capacity() == (("3\n", "2\n") if restorable else left)
    rc, status, row = status_row(w, sid)
    assert row["state"] == "FAILED" and row["partial_effect"] == state and status["unfinished_actions"] == []
    assert (rc, row.get("unresolved"), status["partial_effects"]) == ((0, None, []) if restorable else (3, True, [sid]))


@pytest.mark.parametrize("exit_", ["proposal_missing", "decision_record_mutated: proposal",
                                   "log_claims_effective_without_action_record"])
def test_every_exit_that_gives_a_decision_up_closes_its_unfinished_execution(tmp_path, exit_):
    """Probe (a), "the same exit serves decision_record_mutated: proposal and proposal_missing": every FAILED the
    handler writes while `<id>.execute` is INTENDED first looks at what is in place, as an owner veto does."""
    w = World(tmp_path)
    sid = half_executed(w)
    lines = w.history(sid)
    if exit_ == "proposal_missing":
        w.log.write_text(json.dumps(dict(lines[0], state="PROPOSED")) + "\n")
    elif exit_.startswith("decision_record_mutated"):
        w.log.write_text("".join(json.dumps(x) + "\n" for x in [dict(lines[0], rationale="a different story")] + lines[1:]))
    else:
        (w.run / "actions" / (sid + ".publish.json")).unlink()         # the EFFECTIVE line is a claim nothing backs
    report = w.tick(AFTER)
    d = one(report, sid)
    assert (d["outcome"], d["reason"], d["attention"]) == ("failed", exit_, True)
    assert d["partial_effect"] == "restored" and w.capacity() == ("3\n", "2\n")
    rec = w.action(sid + ".execute")
    assert rec["state"] == "FAILED" and rec["result"]["because"] == exit_
    assert rec["result"]["partial_effect"]["restored"] == ["KY_WORKERS"]
    assert w.history(sid)[-1]["detail"]["partial_effect"] == rec["result"]["partial_effect"]
    assert w.tick(LATER)["decisions"] == [] and kyveto.status(w.env)["unfinished_actions"] == []


def test_an_executed_claim_over_a_complete_effect_is_answered_from_the_disk(tmp_path):
    """The same exit with both files written (killed before the result was recorded): the record is reconciled
    to DONE, so the decision IS executed — the handler says so itself instead of resting FAILED on 6/4."""
    w = World(tmp_path)
    sid = w.propose(cap(tracker_decision=TD))
    assert w.crash("after-execute", "tick").returncode == -signal.SIGKILL
    assert w.capacity() == ("6\n", "4\n") and w.action(sid + ".execute")["state"] == "INTENDED"
    surrogate_line(w, sid, "EXECUTED", effective_at=AT)
    report = w.tick(AFTER)
    d = one(report, sid)
    assert (d["outcome"], d["reason"], d["attention"]) == ("executed", "already_executed", True)
    assert d["instead_of"] == "log_claims_executed_without_action_record" and d["executed"] is True
    assert d["anomaly"] == "log_claim_without_action_record" and d["published"] is True
    rec = w.action(sid + ".execute")
    assert rec["state"] == "DONE" and [r["outcome"] for r in rec["reconciliations"]] == ["done"]
    last = w.history(sid)[-1]
    assert (last["state"], last["by"], last["detail"]["already_executed"]) == ("EXECUTED", "kyveto", d["instead_of"])
    assert w.capacity() == ("6\n", "4\n") and w.tick(LATER)["decisions"] == []
    rc, status, row = status_row(w, sid)
    assert rc == 0 and row["state"] == "EXECUTED" and row["executed_by_handler"] is True


@pytest.mark.parametrize("claim", ["FAILED", "VETOED"])
@pytest.mark.parametrize("restorable", [True, False])
def test_a_terminal_line_over_a_half_written_effect_does_not_end_the_handlers_custody(tmp_path, claim, restorable):
    """Probe (b), first half: the half state, then a FAILED or VETOED line written by the surrogate. Before:
    first_terminal accepted the line, the decision left the handler for good, no tick row, `status` FAILED with
    attention false, the record INTENDED and KY_WORKERS 6."""
    w = World(tmp_path)
    sid = half_executed(w, tracker_decision=TD)
    if not restorable:
        (w.run / "KY_VERIFIERS").write_text("5\n")
    left = w.capacity()
    surrogate_line(w, sid, claim)
    rc, status, row = status_row(w, sid)                  # not final — and somebody is told before any tick ran
    assert rc == 3 and (row["state"], row["latest_line_state"]) == ("EFFECTIVE", claim)
    assert row["unresolved"] is True and row["anomaly"] == TERMINAL_CLAIM
    assert status["unfinished_actions"] == [sid + ".execute"]
    report = w.tick(AFTER)
    d = one(report, sid)
    assert (d["outcome"], d["reason"]) == ("failed", "closed_by_log_line: " + claim)
    assert d["anomaly"] == TERMINAL_CLAIM and d["attention"] is True and report["attention"] is True
    assert d["published"] is True and d["executed"] is False
    state = "restored" if restorable else "in_place"
    assert d["partial_effect"] == state and w.capacity() == (("3\n", "2\n") if restorable else left)
    rec = w.action(sid + ".execute")
    assert rec["state"] == "FAILED" and rec["result"]["partial_effect"]["state"] == state
    assert rec["result"]["because"] == d["reason"]
    line = w.history(sid)[-1]
    assert (line["state"], line["by"], line["reason"]) == ("FAILED", "kyveto", d["reason"])
    assert line["detail"] == {"published": True, "partial_effect": rec["result"]["partial_effect"]}
    assert w.tick(LATER)["decisions"] == []               # answered once: the handler has closed it itself now
    rc, status, row = status_row(w, sid)
    assert row["state"] == "FAILED" and "anomaly" not in row and status["unfinished_actions"] == []
    assert (rc, row.get("unresolved"), status["partial_effects"]) == ((0, None, []) if restorable else (3, True, [sid]))


@pytest.mark.parametrize("claim", ["FAILED", "VETOED"])
def test_a_terminal_line_beside_an_executed_effect_is_overruled_by_the_execution_record(tmp_path, monkeypatch, claim):
    """Probe (b), second half: fully executed (`<id>.execute` DONE, capacity 6/4), the EXECUTED line lost, then
    a FAILED or VETOED line written by the surrogate. Before: `status` FAILED with executed_by_handler true and
    attention false, and no tick ever said a word."""
    w = World(tmp_path)
    sid = w.propose(cap(tracker_decision=TD))
    real = kyveto.Handler.append

    def lose_the_executed_line(self, latest, state, *a, **k):
        if state == "EXECUTED":
            raise OSError("no space left on device")
        return real(self, latest, state, *a, **k)

    with monkeypatch.context() as m:
        m.setattr(kyveto.Handler, "append", lose_the_executed_line)
        assert one(w.tick(AT), sid)["outcome"] == "blocked"
    assert w.states(sid) == ["PENDING_VETO", "EFFECTIVE"] and w.action(sid + ".execute")["state"] == "DONE"
    assert w.capacity() == ("6\n", "4\n")
    surrogate_line(w, sid, claim)
    rc, status, row = status_row(w, sid)
    assert rc == 3 and (row["state"], row["latest_line_state"], row["executed_by_handler"]) == ("EFFECTIVE", claim, True)
    assert row["unresolved"] is True and row["anomaly"] == TERMINAL_CLAIM
    report = w.tick(AFTER)
    d = one(report, sid)
    assert (d["outcome"], d["reason"], d["attention"]) == ("executed", "already_executed", True)
    assert d["instead_of"] == "closed_by_log_line: " + claim and d["anomaly"] == TERMINAL_CLAIM
    assert d["executed"] is True and d["published"] is True and report["attention"] is True
    last = w.history(sid)[-1]
    assert (last["state"], last["by"], last["effective_at"]) == ("EXECUTED", "kyveto", AT)
    assert w.capacity() == ("6\n", "4\n") and len(w.ky_calls()) == 1
    assert w.tick(LATER)["decisions"] == []               # the log says the truth again: reported once
    rc, status, row = status_row(w, sid)
    assert rc == 0 and (row["state"], row["latest_line_state"]) == ("EXECUTED", "EXECUTED")
    assert "unresolved" not in row and "anomaly" not in row


@pytest.mark.parametrize("claim", ["FAILED", "VETOED"])
def test_a_terminal_line_after_publication_is_answered_when_the_handler_closed_nothing(tmp_path, monkeypatch, claim):
    """Probe (c): published, the execution blocked with attention on every tick, then a surrogate FAILED line.
    Before: the blocked row disappeared, the delegated approval stayed in the tracker and nobody was told."""
    w = World(tmp_path)
    sid = w.propose(cap(tracker_decision=TD))
    with monkeypatch.context() as m:
        m.setattr(kyveto.Handler, "execute", lambda self, *a, **k: {
            "outcome": "blocked", "reason": "simulated stop before the execution", "attention": True})
        for now in (AT, AFTER):
            report = w.tick(now)
            assert one(report, sid)["outcome"] == "blocked" and report["attention"] is True
    assert w.states(sid) == ["PENDING_VETO", "EFFECTIVE"] and len(w.ky_calls()) == 1
    assert w.actions() == [sid + ".publish.json"]
    surrogate_line(w, sid, claim)
    rc, status, row = status_row(w, sid)
    assert rc == 3 and (row["state"], row["latest_line_state"], row["published"]) == ("EFFECTIVE", claim, True)
    assert row["unresolved"] is True and row["anomaly"] == TERMINAL_CLAIM
    report = w.tick(LATER)
    d = one(report, sid)
    assert (d["outcome"], d["reason"]) == ("failed", "closed_by_log_line: " + claim)
    assert d["anomaly"] == TERMINAL_CLAIM and d["attention"] is True and report["attention"] is True
    assert d["published"] is True and d["executed"] is False and "partial_effect" not in d
    line = w.history(sid)[-1]
    assert (line["state"], line["by"], line["detail"]) == ("FAILED", "kyveto", {"published": True})
    assert w.capacity() == ("3\n", "2\n") and w.actions() == [sid + ".publish.json"] and len(w.ky_calls()) == 1
    for _ in range(2):                                    # once: the handler has closed it itself now
        assert w.tick(LATER)["decisions"] == []
    rc, status, row = status_row(w, sid)
    assert rc == 0 and row["state"] == "FAILED" and "unresolved" not in row and "anomaly" not in row
    assert row["published"] is True and row["executed_by_handler"] is False


def test_a_terminal_line_over_an_unknown_publication_is_answered_with_the_unknown(tmp_path, monkeypatch):
    """Probe (c) with `ky decide` unanswered: blocked publication_unreconciled on every tick, then FAILED."""
    w = World(tmp_path)
    sid = unknown_publication(w, monkeypatch)
    surrogate_line(w, sid, "FAILED")
    report = w.tick(AFTER)
    d = one(report, sid)
    assert (d["outcome"], d["reason"]) == ("failed", "closed_by_log_line: FAILED")
    assert (d["published"], d["executed"], d["attention"], d["anomaly"]) == ("unknown", False, True, TERMINAL_CLAIM)
    assert w.history(sid)[-1]["detail"] == {"published": "unknown"} and len(w.ky_calls()) == 1
    assert w.tick(LATER)["decisions"] == []
    rc, status, row = status_row(w, sid)                  # the unknown publication stays the owner's to settle
    assert rc == 3 and row["published"] == "unknown" and row["unresolved"] is True and "anomaly" not in row


def test_a_terminal_line_never_silences_an_execution_that_cannot_be_reconciled(tmp_path, monkeypatch):
    """Probe (c) with the record begun: blocked execution_unreconciled on every tick stays exactly that."""
    w = World(tmp_path)
    sid = half_executed(w, tracker_decision=TD)
    capacity = kyveto.REGISTRY["capacity"]
    with monkeypatch.context() as m:
        m.setattr(capacity, "observer", lambda p, ctx: ("unknown", {"error": "the pool files cannot be read"}))
        assert one(w.tick(AFTER), sid)["reason"] == "execution_unreconciled"
        surrogate_line(w, sid, "FAILED")
        for now in (AFTER, LATER):
            report = w.tick(now)
            d = one(report, sid)
            assert (d["outcome"], d["attention"], d["anomaly"]) == ("blocked", True, TERMINAL_CLAIM)
            assert d["reason"] == "execution_unreconciled" and d["giving_up"] == "closed_by_log_line: FAILED"
            assert report["attention"] is True
    assert w.action(sid + ".execute")["state"] == "INTENDED" and w.capacity() == ("6\n", "2\n")
    rc, status, row = status_row(w, sid)
    assert rc == 3 and row["unresolved"] is True and row["state"] == "EFFECTIVE"
    d = one(w.tick(LATER), sid)                           # the files can be read again: closed, put back, said
    assert (d["outcome"], d["partial_effect"]) == ("failed", "restored") and w.capacity() == ("3\n", "2\n")


def test_an_owner_veto_is_still_the_answer_to_a_decision_a_line_claims_closed(tmp_path):
    w = World(tmp_path)
    sid = half_executed(w)
    surrogate_line(w, sid, "FAILED")
    cid = w.veto(sid)
    report = w.tick(AFTER)
    d = one(report, sid)
    assert (d["outcome"], d["command"], d["partial_effect"]) == ("vetoed", cid, "restored")
    assert d["anomaly"] == TERMINAL_CLAIM and d["attention"] is True
    assert d["executed"] is False and d["published"] is False
    assert w.capacity() == ("3\n", "2\n") and w.command(cid)["state"] == "APPLIED"
    assert w.command(cid)["result"]["outcome"] == "VETOED" and report["commands"][0]["status"] == "applied"
    assert w.states(sid)[-2:] == ["FAILED", "VETOED"] and w.history(sid)[-1]["by"] == "kyveto"
    assert w.action(sid + ".execute")["result"]["reason"] == "vetoed_partial_effect_restored"
    assert w.tick(LATER)["decisions"] == []
    rc, status, row = status_row(w, sid)                  # the handler's own closing is what the state is
    assert rc == 0 and (row["state"], row["latest_line_state"]) == ("VETOED", "VETOED")


def test_the_handler_remembers_which_decisions_it_closed_itself(tmp_path):
    """R14, "a state rule, not an authorship rule": a line's `by` is whatever the model wrote. What ends the
    handler's custody of a decision it had begun to act on is its own closing marker beside the action records."""
    w = World(tmp_path)
    sid = w.propose(cap(tracker_decision=TD))
    w.crash("before-execute", "tick")                     # published; `<id>.execute` INTENDED, nothing written
    w.veto(sid)
    assert one(w.tick(AFTER), sid)["outcome"] == "vetoed"
    path = kyveto.stamp_path(w.run, sid, "closed")
    marker = json.loads(path.read_text())
    assert (marker["state"], marker["reason"], marker["closed_at"]) == ("VETOED", "owner_veto", AFTER)
    assert kyveto.closed_as(w.run, sid) == "VETOED" and kyveto.closed_as(w.run, sid, {"state": "FAILED"}) == "VETOED"
    for state in ("INTENDED", "DONE"):                    # such an execution record overrules any closing
        assert kyveto.closed_as(w.run, sid, {"state": state}) is None
    assert w.tick(LATER)["decisions"] == []
    path.unlink()                                         # without it the very same lines are a claim again
    assert kyveto.closed_as(w.run, sid) is None and status_row(w, sid)[2]["anomaly"] == TERMINAL_CLAIM
    d = one(w.tick(LATER), sid)
    assert (d["outcome"], d["anomaly"], d["attention"], d["published"]) == ("vetoed", TERMINAL_CLAIM, True, True)
    assert kyveto.closed_as(w.run, sid) == "VETOED" and w.tick(LATER)["decisions"] == []
    path.unlink()
    path.write_text("{")                                  # a marker that cannot be read closes nothing
    assert kyveto.closed_as(w.run, sid) is None
    path.write_text(json.dumps({"state": "EXECUTED"}))    # … nor does one that names no closing state
    assert kyveto.closed_as(w.run, sid) is None
    # a decision the handler never began to act on needs none: nothing of its own is out, the line is final
    other = w.propose(cap(builders=5), notification={"submitted": False, "ts": T_NOTIFY})
    report = w.tick(AT)
    assert one(report, other)["reason"] == "notification_not_submitted"
    assert one(report, sid)["anomaly"] == TERMINAL_CLAIM  # (the first one's marker was spoilt above: answered again)
    assert not kyveto.stamp_path(w.run, other, "closed").exists() and kyveto.closed_as(w.run, sid) == "VETOED"
    assert w.tick(LATER)["decisions"] == []


# ── C4-02 (review round 4): a veto that arrives after EXECUTED carries attention in the later tick too ──

def test_a_veto_one_tick_after_the_execution_is_reported_with_attention(tmp_path):
    """The reviewer's probe: settled REJECTED too_late with no attention and exit 0, while the same veto inside
    the executing tick carries attention."""
    w = World(tmp_path)
    sid = w.propose(cap(tracker_decision=TD))
    assert one(w.tick(AT), sid)["outcome"] == "executed"
    cid = w.veto(sid)
    report = w.tick(AFTER)
    d = one(report, sid)
    assert (d["outcome"], d["reason"], d["attention"], d["command"]) == ("executed", "veto_too_late", True, cid)
    assert report["attention"] is True and [c["id"] for c in report["commands"]] == [cid]
    cmd = w.command(cid)
    assert cmd["state"] == "REJECTED" and cmd["result"]["reason"].startswith("too_late")
    assert w.states(sid) == ["PENDING_VETO", "EFFECTIVE", "EXECUTED"] and w.capacity() == ("6\n", "4\n")
    again = w.tick(LATER)                                 # said once
    assert again["decisions"] == [] and again["commands"] == [] and again["attention"] is False
    other = w.propose(cap(builders=5))                    # … and the real program exits 3 on it
    assert w.cli("tick").returncode == 0 and w.states(other)[-1] == "EXECUTED"
    w.veto(other)
    r = w.cli("tick")
    assert r.returncode == 3, r.stderr
    assert one(json.loads(r.stdout), other)["reason"] == "veto_too_late"
    assert w.cli("tick").returncode == 0


# ── ruling R16: nothing comes to rest wrong, and no wait goes on, with nobody told ──

@pytest.mark.parametrize("executed", [False, True])
def test_a_record_refused_while_its_execution_is_open_is_not_left_as_it_is(tmp_path, executed):
    """`refuse` is an exit that gives a decision up too: with `<id>.execute` INTENDED it left the half in place
    and the record unfinished behind a refusal that said nothing about either."""
    w = World(tmp_path)
    if executed:
        sid = w.propose(cap())
        assert w.crash("after-execute", "tick").returncode == -signal.SIGKILL
    else:
        sid = half_executed(w)
    w.append(dict(w.history(sid)[0], rationale=""))       # a line the handler cannot answer with a valid one
    report = w.tick(AFTER)
    d = one(report, sid)
    assert d["outcome"] == "refused" and d["reason"] == "record_malformed: rationale" and d["attention"] is True
    rec, marker = w.action(sid + ".execute"), w.refusal(sid)
    if executed:
        assert d["executed"] is True and marker["executed"] is True and "partial_effect" not in d
        assert rec["state"] == "DONE" and w.capacity() == ("6\n", "4\n")
    else:
        assert d["partial_effect"] == "restored" and "executed" not in d and w.capacity() == ("3\n", "2\n")
        assert rec["state"] == "FAILED" and rec["result"]["reason"] == "given_up_partial_effect_restored"
        assert rec["result"]["because"] == "refused: record_malformed: rationale"
        assert marker["partial_effect"] == rec["result"]["partial_effect"]
    assert w.tick(LATER)["decisions"] == [] and kyveto.status(w.env)["unfinished_actions"] == []


def test_a_record_that_turns_out_unanswerable_after_publication_says_what_was_published(tmp_path, monkeypatch):
    """The refusal written when a line could not be appended after all was marked `published: false` whatever
    the tracker held."""
    w = World(tmp_path)
    sid = w.propose(cap(tracker_decision=TD))
    real = kyveto.line_problem
    monkeypatch.setattr(kyveto, "line_problem", lambda line: (
        "line_malformed: by_test" if line.get("state") == "EFFECTIVE" else real(line)))
    report = w.tick(AT)
    d = one(report, sid)
    assert d["outcome"] == "refused" and d["reason"].startswith("record_unanswerable") and d["attention"] is True
    assert d["published"] is True and w.refusal(sid)["published"] is True
    assert len(w.ky_calls()) == 1 and w.capacity() == ("3\n", "2\n") and w.states(sid) == ["PENDING_VETO"]
    rc, status, row = status_row(w, sid)
    assert rc == 3 and row["published"] is True and row["refused"] and row["unresolved"] is True


def test_an_action_whose_first_actor_cannot_be_told_alive_or_gone_is_not_waited_for_in_silence(tmp_path, monkeypatch):
    """`locked … in_progress` means "come back later". When the process that began the action cannot be judged
    at all (`ps` does not answer), later may never come: the row then carries attention."""
    w = World(tmp_path)
    sid = w.propose(cap())
    w.crash("before-execute", "tick")
    shutil.rmtree(w.run / "locks")                        # (the dead handler's own locks are another test's subject)
    path = w.run / "actions" / (sid + ".execute.json")
    with bystander() as (pid, start):
        path.write_text(json.dumps(dict(json.loads(path.read_text()), process={"pid": pid, "process_start": start})))
        quiet = w.tick(AFTER)                             # alive elsewhere: nobody needs to do anything
        assert one(quiet, sid) == {"id": sid, "outcome": "locked", "reason": "execution_in_progress"}
        assert quiet["attention"] is False
        with monkeypatch.context() as m:
            no_ps(m)
            for path_taken in ("executing", "giving up"):
                report = w.tick(AFTER)
                d = one(report, sid)
                assert (d["outcome"], d["reason"], d["attention"]) == ("locked", "execution_in_progress", True), path_taken
                assert d["owner"] == "unknown" and report["attention"] is True
                cid = w.veto(sid) if path_taken == "executing" else cid       # the second pass meets it in `vetoed`
        assert w.capacity() == ("3\n", "2\n") and "reconciliations" not in w.action(sid + ".execute")
        assert w.command(cid)["state"] == "QUEUED" and w.states(sid) == ["PENDING_VETO", "EFFECTIVE"]


def test_status_does_not_read_normal_over_an_execution_nobody_is_carrying_out(tmp_path):
    """`<id>.execute` INTENDED after a crash: until a tick has completed or closed it, part of the effect may be
    in force. `status` listed the record and said nothing needed anybody."""
    w = World(tmp_path)
    sid = half_executed(w)
    rc, status, row = status_row(w, sid)
    assert rc == 3 and row["execution_unfinished"] is True and row["unresolved"] is True
    assert status["unfinished_actions"] == [sid + ".execute"] and row["state"] == "EFFECTIVE"
    path = w.run / "actions" / (sid + ".execute.json")
    doc = json.loads(path.read_text())
    with bystander() as (pid, start):                     # a live process is carrying it out: nothing to attend to
        path.write_text(json.dumps(dict(doc, process={"pid": pid, "process_start": start})))
        rc, status, row = status_row(w, sid)
        assert rc == 0 and "execution_unfinished" not in row and "unresolved" not in row
    path.write_text(json.dumps(doc))
    assert one(w.tick(AFTER), sid)["outcome"] == "executed"
    rc, status, row = status_row(w, sid)
    assert rc == 0 and "execution_unfinished" not in row and status["unfinished_actions"] == []


# ── C4-05 (review round 4): the holds are looked at again wherever the veto is ──

@pytest.mark.parametrize("hold_", ["HOLD", "owner_pause_pending"])
@pytest.mark.parametrize("during", ["recheck", "publication"])
def test_a_hold_placed_while_the_pass_is_under_way_stops_what_has_not_happened_yet(tmp_path, monkeypatch, during, hold_):
    """Holds and the owner pause were read once, before the recheck; a HOLD or pause placed while `ky decide`
    ran (up to 120 s) did not stop that pass from executing."""
    w = World(tmp_path)
    sid = w.propose(cap(tracker_decision=TD))
    placed = []

    def place():
        if hold_ == "HOLD":
            (w.root / "HOLD").write_text("x\n")
        elif not placed:
            placed.append(kycommands.submit(w.run, "campaign", "pause", {}, COCKPIT))

    real_ky = kyveto.run_ky
    with monkeypatch.context() as m:
        if during == "recheck":
            m.setattr(kyveto.REGISTRY["capacity"], "precheck", lambda params, ctx: place())
        else:
            m.setattr(kyveto, "run_ky", lambda argv, env: (place(), real_ky(argv, env))[1])
        report = w.tick(AT)
    d = one(report, sid)
    assert (d["outcome"], d["reasons"]) == ("held", [hold_]) and report["attention"] is False
    assert w.capacity() == ("3\n", "2\n") and sid + ".execute.json" not in w.actions()
    if during == "recheck":                               # nothing was published either
        assert w.ky_calls() == [] and w.states(sid) == ["PENDING_VETO"]
        assert sid + ".publish.json" not in w.actions()
    else:                                                 # published and effective; the execution waits for the hold
        assert len(w.ky_calls()) == 1 and w.states(sid) == ["PENDING_VETO", "EFFECTIVE"]
    assert one(w.tick(AFTER), sid)["outcome"] == "held"
    if hold_ == "HOLD":
        (w.root / "HOLD").unlink()
    else:
        kycommands.submit(w.run, "campaign", "resume", {}, COCKPIT)
    assert one(w.tick(LATER), sid)["outcome"] == "executed"
    assert w.capacity() == ("6\n", "4\n") and len(w.ky_calls()) == 1


# ── C4-04 (review round 4): the immutable activation record names its receipts absolutely, whatever KY_RUN is ──

def test_the_activation_record_names_its_receipts_absolutely_under_a_relative_run_directory(tmp_path, monkeypatch):
    """KY_RUN need not be absolute; only the manifest path was made absolute, the receipt paths were stored as
    they came — relative to wherever the handler happened to run."""
    w = World(tmp_path)
    monkeypatch.chdir(tmp_path)
    target = bundle(w)
    target["review_receipts"] = [os.path.relpath(p, w.run) for p in target["review_receipts"]]
    w.environ["KY_RUN"] = os.path.relpath(w.run, tmp_path)
    assert not os.path.isabs(str(w.env.run)) and not os.path.isabs(target["review_receipts"][0])
    sid = w.propose(target)
    assert one(w.tick(AT, authorised=ROOT_AUTHORITY), sid)["outcome"] == "executed"
    rec = json.loads((w.run / "ACTIVATION_RECORD.1.json").read_text())
    assert_schema("activation_record", rec)
    (r1,) = rec["review_receipts"]
    assert os.path.isabs(r1["path"]) and r1["sha256"] == sha(r1["path"])
    assert os.path.isabs(rec["new_manifest"]["path"])
