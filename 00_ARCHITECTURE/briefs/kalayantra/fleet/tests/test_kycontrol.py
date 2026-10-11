"""B-0c control modules (relaunch plan v2.7 §4a.1 "Action records", §4a.3, §4a.5, §4a.6; §6 SURROGATE row;
pairing rule KW-04): kyaction.py (crash-safe action records), kycommands.py (the cockpit command queue) and
kyveto.py (the deterministic veto-window handler), with their three schemas.

Nothing here touches /Users/Dev/kalayantra, the real `ky`, the tracker, launchctl, gh, a database or the
network: every test runs in its own tree under pytest's basetemp with the doubles in fixtures/b0c_control/
(fake_ky, fake_git, crash_tick.py). An autouse fixture points KY_ROOT / KY_RUN / KY_FLEET at a guard directory,
so a code path that fell back to the process environment still could not reach the live tree. Every rule is
shown passing and failing, and a refusal is asserted by its named reason, not only by "something failed".

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
T_NOTIFY, T_DEADLINE = "2026-10-11T22:00:00Z", "2026-10-11T22:30:00Z"
BEFORE, AT, AFTER, LATER = "2026-10-11T22:10:00Z", T_DEADLINE, "2026-10-11T22:31:00Z", "2026-10-11T22:40:00Z"
TD = {"id": "D-41", "outcome": "approved"}
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
                         "created_at", "state", "result", "completed_at"]          # the cockpit's shape
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
    assert sorted(outs) == ["new"] + ["unfinished"] * 7
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


@pytest.mark.parametrize("aid", ["", "-leading", "has space", "a/b", "../x", "é", "x" * 121, "x\n", None, 7])
def test_action_ids_are_restricted(tmp_path, aid):
    run = mkrun(tmp_path)
    with pytest.raises(kyaction.ActionInvalid):
        begin(run, aid)
    assert not (run / "actions").exists() or list((run / "actions").iterdir()) == []


def test_action_ids_accept_the_documented_alphabet(tmp_path):
    run = mkrun(tmp_path)
    for aid in ("A", "ACT-KW01-planner-state-migration", "SD-20261011T220000Z-1.execute", "a:b_c.d-e", "x" * 120):
        assert begin(run, aid)[0] == "new"


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


def test_cli_is_read_only(tmp_path):
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
    assert cli("complete", "ACT-a").returncode == 64          # the CLI cannot write
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


def test_a_live_owner_or_an_unverifiable_one_is_never_displaced(tmp_path):
    run = mkrun(tmp_path)
    hold(run, "decision.SD-1", "alive")                                    # this very process: alive, same start
    assert kyaction.acquire_lock(run, "decision.SD-1", "me") is None
    hold(run, "decision.SD-2", "alive-no-start", start="")                 # alive, identity not comparable
    assert kyaction.acquire_lock(run, "decision.SD-2", "me") is None
    hold(run, "decision.SD-3", "reused-pid", start="Thu Jan  1 00:00:00 1970")     # same pid, another process
    assert kyaction.acquire_lock(run, "decision.SD-3", "me") is not None


def test_a_lock_without_an_owner_record_is_held_until_the_grace_period_has_passed(tmp_path):
    run = mkrun(tmp_path)
    d = run / "locks" / "decision.SD-1"
    d.mkdir(parents=True)                                   # another actor is between mkdir and owner.json
    assert kyaction.acquire_lock(run, "decision.SD-1", "me") is None
    old = time.time() - kyaction.OWNERLESS_GRACE_S - 5
    os.utime(d, (old, old))
    assert kyaction.acquire_lock(run, "decision.SD-1", "me") is not None


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


@pytest.mark.parametrize("name", ["", "a/b", "..", "x y", "x" * 161])
def test_lock_names_are_restricted(tmp_path, name):
    with pytest.raises(kyaction.ActionInvalid):
        kyaction.acquire_lock(mkrun(tmp_path), name, "me")


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
    assert doc == {"schema": "ky.command/1", "id": cid, "created_at": doc["created_at"], "from": COCKPIT,
                   "role": role, "command": command, "args": args, "state": "QUEUED", "applied_by": None,
                   "applied_at": None, "result": None}
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


def test_a_cockpit_holding_the_role_lock_may_apply(tmp_path):
    run = mkrun(tmp_path)
    cid = kycommands.submit(run, "planner", "handoff", {}, COCKPIT)
    hold(run, "planner", "sess-1")
    status, doc = kycommands.apply(run, cid, {"holder_kind": "cockpit", "session_id": "sess-1"}, lambda c: {})
    assert status == "applied"
    assert doc["applied_by"] == {"role": "planner", "holder_kind": "cockpit", "session_id": "sess-1"}
    assert_schema("command", doc)


@pytest.mark.parametrize("lock,reason", [
    ("none", "role_lock_not_held"), ("other", "role_lock_held_by_another"), ("dead", "role_lock_stale"),
    ("unverifiable", "role_lock_owner_unverifiable"), ("wrong-role", "role_lock_not_held"),
])
def test_an_applier_that_does_not_hold_the_role_lock_is_refused(tmp_path, lock, reason):
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
    before = tree(run)
    called = []
    status, detail = kycommands.apply(run, cid, "ctl-d", lambda c: called.append(1) or {})
    assert status == "refused" and detail["reason"].startswith(reason)
    assert called == [] and tree(run) == before                       # still QUEUED, nothing recorded
    assert [d["id"] for d in kycommands.pending(run, "dispatcher")] == [cid]


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
    assert doc["id"] == cid and doc["from"] == {"kind": "cockpit", "session_id": "sess-9"} and doc["args"] == {"n": 5}
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
        self.log = self.run / "DECISIONS_SURROGATE.jsonl"
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

    def propose(self, target, sid=None, bind=True, awaiting_open=True, **over):
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
        self.append(line)
        if awaiting_open:
            (self.run / "awaiting" / (line["awaiting"] + ".json")).write_text(json.dumps({"id": line["awaiting"]}))
        return sid

    def append(self, line):
        with open(self.log, "a", encoding="utf-8") as f:
            f.write(json.dumps(line) + "\n")

    def history(self, sid):
        return [d for d in map(json.loads, self.log.read_text(encoding="utf-8").splitlines()) if d["id"] == sid]

    def states(self, sid):
        return [d["state"] for d in self.history(sid)]

    def tick(self, now, **kw):
        return kyveto.tick(self.env, now=now, **kw)

    def cli(self, *args, **popen):
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
    assert tree(w.run) == before and w.ky_calls() == [] and w.actions() == []
    assert report["attention"] is False
    one_second_early = w.tick("2026-10-11T22:29:59Z")
    assert one(one_second_early, sid)["seconds_remaining"] == 1 and tree(w.run) == before


def test_at_expiry_the_decision_is_published_then_executed_exactly_once(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap(tracker_decision=TD))
    report = w.tick(AT)                                           # now == veto_deadline: the window has expired
    assert one(report, sid)["outcome"] == "executed" and report["attention"] is False
    assert w.states(sid) == ["PENDING_VETO", "EFFECTIVE", "EXECUTED"]
    proposal, effective, executed = w.history(sid)
    for line in (effective, executed):
        assert line["by"] == "kyveto" and line["reason"] and line["effective_at"] == AT
        assert line["target"] == proposal["target"] and line["authority"] == proposal["authority"]
        assert line["awaiting"] == proposal["awaiting"] and line["veto_deadline"] == T_DEADLINE
    assert w.capacity() == ("6\n", "4\n")
    assert [c["argv"] for c in w.ky_calls()] == [["decide", "D-41", "--outcome", "approved", "--as", "steward",
                                                  "--delegated", "--detail", sid + ": raise capacity"]]
    publish, execute = w.action(sid + ".publish"), w.action(sid + ".execute")
    assert publish["state"] == "DONE" and publish["result"]["exit_status"] == 0
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
    assert w.ky_calls() == [] and w.actions() == [sid + ".execute.json"]
    assert w.capacity() == ("6\n", "4\n")


def test_ky_receives_an_allow_listed_environment(tmp_path, monkeypatch):
    w = World(tmp_path)
    w.environ.update(DATABASE_URL="postgres://not-a-real-one", ANTHROPIC_API_KEY="not-a-real-one", KY_STREAM="K")
    w.propose(cap(tracker_decision=TD))
    w.tick(AT)
    (call,) = w.ky_calls()
    assert set(call["env_names"]) - {"__CF_USER_TEXT_ENCODING", "LC_CTYPE"} <= set(kyveto.KY_ENV_NAMES)
    assert "DATABASE_URL" not in call["env_names"] and "ANTHROPIC_API_KEY" not in call["env_names"]
    assert "KY_ROOT" in call["env_names"]


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


def test_an_already_applied_veto_command_still_vetoes(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap())
    cid = w.veto(sid)
    hold(w.run, "veto", "someone")
    assert kycommands.apply(w.run, cid, "someone", lambda c: {"note": "seen"}, in_order=False)[0] == "applied"
    shutil.rmtree(w.run / "locks" / "veto")
    assert one(w.tick(AFTER), sid)["outcome"] == "vetoed"
    assert w.states(sid) == ["PENDING_VETO", "VETOED"] and w.capacity() == ("3\n", "2\n")


def test_a_vetoed_decision_is_not_resurrected_by_a_later_pending_line(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap())
    cid = w.veto(sid)
    w.tick(BEFORE)
    w.append(w.history(sid)[0])                           # the proposal is appended again after the veto
    report = w.tick(AFTER)
    assert one(report, sid)["outcome"] == "vetoed"
    assert w.states(sid)[-1] == "VETOED" and "EFFECTIVE" not in w.states(sid) and w.capacity() == ("3\n", "2\n")
    assert w.command(cid)["state"] == "APPLIED"


def test_a_failed_decision_is_not_resurrected_by_a_corrected_line(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap(tracker_decision=TD), notification={"submitted": False, "ts": T_NOTIFY})
    assert one(w.tick(AT), sid)["reason"] == "notification_not_submitted"
    w.append(dict(w.history(sid)[0], notification={"submitted": True, "ts": T_NOTIFY}))    # "fixed" under the same id
    d = one(w.tick(AFTER), sid)
    assert (d["outcome"], d["reason"]) == ("failed", "terminal_state_is_final")
    assert w.states(sid) == ["PENDING_VETO", "FAILED", "PENDING_VETO", "FAILED"]
    assert w.ky_calls() == [] and w.capacity() == ("3\n", "2\n") and w.actions() == []


def test_an_executed_decision_is_never_executed_again(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap(tracker_decision=TD))
    w.tick(AT)
    (w.run / "KY_WORKERS").write_text("3\n")              # capacity was lowered again afterwards
    w.append(w.history(sid)[0])
    d = one(w.tick(AFTER), sid)
    assert (d["outcome"], d["reason"]) == ("executed", "terminal_state_is_final")
    assert w.capacity() == ("3\n", "4\n") and len(w.ky_calls()) == 1
    for name in w.actions():                              # … not even when its action records have gone missing
        (w.run / "actions" / name).unlink()
    w.append(w.history(sid)[0])
    assert one(w.tick(LATER), sid)["outcome"] == "executed"
    assert w.capacity() == ("3\n", "4\n") and len(w.ky_calls()) == 1 and w.actions() == []


def test_a_veto_of_a_decision_not_yet_in_its_window_waits_for_it(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap(), state="PROPOSED", notification={"submitted": False, "ts": None}, veto_deadline=None)
    cid = w.veto(sid)
    assert w.tick(BEFORE)["decisions"] == []
    assert w.command(cid)["state"] == "QUEUED" and w.states(sid) == ["PROPOSED"]        # the veto is not lost
    w.append(dict(w.history(sid)[0], state="PENDING_VETO", notification={"submitted": True, "ts": T_NOTIFY},
                  veto_deadline=T_DEADLINE))
    assert one(w.tick(AFTER), sid)["outcome"] == "vetoed"
    assert w.command(cid)["state"] == "APPLIED" and w.capacity() == ("3\n", "2\n")


def test_other_commands_addressed_to_the_veto_role_are_rejected_not_left_to_block(tmp_path):
    w = World(tmp_path)
    cid = kycommands.submit(w.run, "veto", "status", {}, COCKPIT)
    report = w.tick(BEFORE)
    assert w.command(cid)["state"] == "REJECTED"
    assert w.command(cid)["result"]["reason"] == "unsupported_by_veto_handler: status"
    assert report["commands"][0]["status"] == "rejected"


def test_a_named_holder_settles_the_veto_under_its_own_identity(tmp_path):
    w = World(tmp_path)
    hold(w.run, "veto", "ctl-veto")
    sid = w.propose(cap())
    cid = w.veto(sid)
    r = w.cli("tick", "--now", BEFORE, "--as", "ctl-veto")
    assert r.returncode == 0, r.stderr
    assert w.states(sid) == ["PENDING_VETO", "VETOED"] and w.history(sid)[-1]["session"] == "ctl-veto"
    assert w.command(cid)["applied_by"] == {"role": "veto", "holder_kind": "controller", "controller_id": "ctl-veto"}
    assert (w.run / "locks" / "veto").is_dir()             # the controller's role lock is not the tick's to release


def test_the_bootstrap_supervisor_may_run_the_handler(tmp_path):
    w = World(tmp_path)
    hold(w.run, "veto", "kyboot-1")
    sid = w.propose(cap())
    r = w.cli("tick", "--now", AT, "--as", "kyboot-1", "--holder-kind", "supervisor")
    assert r.returncode == 0, r.stderr
    assert w.action(sid + ".execute")["actor"] == {"role": "veto", "holder_kind": "supervisor",
                                                   "controller_id": "kyboot-1"}
    assert w.states(sid)[-1] == "EXECUTED"
    assert w.cli("tick", "--holder-kind", "cockpit").returncode == 64


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
    bad = w.propose(cap(builders=9))
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


@pytest.mark.parametrize("notification", [
    {"submitted": False, "ts": T_NOTIFY}, {"submitted": "true", "ts": T_NOTIFY}, {"submitted": 1, "ts": T_NOTIFY},
    {"ts": T_NOTIFY}, None, "submitted",
])
def test_a_notification_that_was_not_submitted_prevents_effectiveness(tmp_path, notification):
    w = World(tmp_path)
    sid = w.propose(cap(tracker_decision=TD), notification=notification)
    assert one(w.tick(BEFORE), sid)["outcome"] == "pending"            # judged at expiry, under the lock
    d = one(w.tick(AT), sid)
    assert (d["outcome"], d["reason"]) == ("failed", "notification_not_submitted")
    assert w.states(sid) == ["PENDING_VETO", "FAILED"]
    failed = w.history(sid)[-1]
    assert failed["by"] == "kyveto" and failed["reason"] == "notification_not_submitted"
    assert failed["effective_at"] is None
    assert w.ky_calls() == [] and w.capacity() == ("3\n", "2\n") and w.actions() == []
    assert w.tick(AFTER)["decisions"] == []


@pytest.mark.parametrize("over,reason", [
    ({"notification": {"submitted": True, "ts": "2026-10-11T22:10:00Z"}}, "veto_window_too_short"),
    ({"notification": {"submitted": True}}, "notification_ts_unreadable"),
    ({"notification": {"submitted": True, "ts": "yesterday"}}, "notification_ts_unreadable"),
])
def test_the_owner_gets_the_whole_thirty_minute_window(tmp_path, over, reason):
    w = World(tmp_path)
    sid = w.propose(cap(), **over)
    d = one(w.tick(AT), sid)
    assert (d["outcome"], d["reason"]) == ("failed", reason)
    assert w.capacity() == ("3\n", "2\n")


@pytest.mark.parametrize("deadline", [None, "soon", "2026-10-11 22:30:00", 1791757800])
def test_an_unreadable_deadline_never_expires_into_effect(tmp_path, deadline):
    w = World(tmp_path)
    sid = w.propose(cap(), veto_deadline=deadline)
    d = one(w.tick(LATER), sid)
    assert (d["outcome"], d["reason"]) == ("failed", "veto_deadline_unreadable")
    assert w.capacity() == ("3\n", "2\n")


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


def test_a_target_changed_on_disk_since_the_proposal_is_refused(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap(tracker_decision=TD))
    (w.run / "KY_WORKERS").write_text("5\n")              # someone changed capacity during the window
    d = one(w.tick(AT), sid)
    assert (d["outcome"], d["reason"]) == ("failed", "target_changed")
    assert w.states(sid) == ["PENDING_VETO", "FAILED"]
    assert w.capacity() == ("5\n", "2\n") and w.ky_calls() == [] and w.actions() == []


def test_target_parameters_changed_under_the_same_fingerprint_are_refused(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap(builders=4))
    line = w.history(sid)[0]
    edited = dict(line, target=dict(line["target"], builders=12))       # same recorded fingerprint, new request
    w.log.write_text(json.dumps(edited) + "\n")
    d = one(w.tick(AT), sid)
    assert (d["outcome"], d["reason"]) == ("failed", "target_changed")
    assert w.capacity() == ("3\n", "2\n")


def test_a_later_line_that_rebinds_the_target_is_refused(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap(builders=4))
    line = w.history(sid)[0]
    target = cap(builders=12)
    target["fingerprint"] = kyveto.fingerprint(target, w.env)          # a self-consistent, different target
    w.append(dict(line, target=target))
    d = one(w.tick(AT), sid)
    assert (d["outcome"], d["reason"]) == ("failed", "decision_record_mutated: target")
    assert w.capacity() == ("3\n", "2\n")


def test_a_later_line_that_shortens_the_window_is_refused(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap(), veto_deadline="2026-10-11T23:00:00Z")
    w.append(dict(w.history(sid)[0], veto_deadline=T_DEADLINE))
    d = one(w.tick(AT), sid)
    assert (d["outcome"], d["reason"]) == ("failed", "decision_record_mutated: veto_deadline")


@pytest.mark.parametrize("fingerprint", [None, "", "abc", 7])
def test_a_target_without_a_recorded_fingerprint_is_unbound(tmp_path, fingerprint):
    w = World(tmp_path)
    target = cap()
    if fingerprint is not None:
        target["fingerprint"] = fingerprint
    sid = w.propose(target, bind=False)
    d = one(w.tick(AT), sid)
    assert (d["outcome"], d["reason"]) == ("failed", "target_unbound")
    assert w.capacity() == ("3\n", "2\n")


@pytest.mark.parametrize("authority", [
    {"source_commit": C2, "entrypoints_digest": E1}, {"source_commit": C1, "entrypoints_digest": E2},
])
def test_a_changed_authority_is_refused(tmp_path, authority):
    w = World(tmp_path)
    sid = w.propose(cap(tracker_decision=TD), authority=authority)
    d = one(w.tick(AT), sid)
    assert (d["outcome"], d["reason"]) == ("failed", "authority_changed")
    assert w.ky_calls() == [] and w.capacity() == ("3\n", "2\n")


def test_the_authorised_bundle_changed_during_the_window(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap())
    w.authorise(C2, E2)                                   # a successor bundle was activated meanwhile
    assert one(w.tick(AT), sid)["reason"] == "authority_changed"


@pytest.mark.parametrize("authority", [None, {}, {"source_commit": C1}, "e709f60d7"])
def test_a_decision_without_an_authority_binding_is_refused(tmp_path, authority):
    w = World(tmp_path)
    sid = w.propose(cap(), authority=authority)
    assert one(w.tick(AT), sid)["reason"] == "authority_unbound"
    assert w.capacity() == ("3\n", "2\n")


@pytest.mark.parametrize("state", ["missing", "torn", "no-field", "commit-only", "short-commit"])
def test_an_unreadable_authorised_bundle_is_authority_unknown(tmp_path, state):
    w = World(tmp_path)
    sid = w.propose(cap(tracker_decision=TD))
    path = w.run / "PLANNER_STATE.json"
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
    d = one(w.tick(AT), sid)
    assert (d["outcome"], d["reason"]) == ("failed", "authority_unknown")
    assert w.ky_calls() == [] and w.capacity() == ("3\n", "2\n")


def test_authority_given_as_arguments_takes_precedence_over_the_state_file(tmp_path):
    w = World(tmp_path)
    (w.run / "PLANNER_STATE.json").unlink()
    sid = w.propose(cap())
    r = w.cli("tick", "--now", AT, "--authorised-commit", C1, "--entrypoints-digest", E1)
    assert r.returncode == 0, r.stderr
    report = json.loads(r.stdout)
    assert one(report, sid)["outcome"] == "executed" and report["authority"]["source"] == "arguments"
    w2 = World(tmp_path / "second")                                    # the state file says C1; the arguments say C2
    sid2 = w2.propose(cap())
    r = w2.cli("tick", "--now", AT, "--authorised-commit", C2, "--entrypoints-digest", E1)
    assert one(json.loads(r.stdout), sid2)["reason"] == "authority_changed"
    assert w2.cli("tick", "--now", AT, "--authorised-commit", C1).returncode == 64      # both or neither


def test_a_failed_publication_is_failed_never_executed(tmp_path):
    w = World(tmp_path)
    w.ky_says("rc", 3)
    sid = w.propose(cap(tracker_decision=TD))
    d = one(w.tick(AT), sid)
    assert d["outcome"] == "failed" and d["reason"] == "publication_failed: rc=3"
    assert w.states(sid) == ["PENDING_VETO", "FAILED"]                 # never EFFECTIVE, never EXECUTED
    assert w.capacity() == ("3\n", "2\n")
    publish = w.action(sid + ".publish")
    assert publish["state"] == "FAILED" and publish["result"]["exit_status"] == 3
    assert w.actions() == [sid + ".publish.json"]                      # the executor was never begun
    w.ky_says("rc", 0)
    assert w.tick(AFTER)["decisions"] == []                            # a failed proposal is not retried
    assert len(w.ky_calls()) == 1 and w.states(sid) == ["PENDING_VETO", "FAILED"]


def test_a_missing_ky_is_refused_before_anything_is_recorded(tmp_path):
    w = World(tmp_path)
    (w.root / "bin" / "ky").unlink()
    sid = w.propose(cap(tracker_decision=TD))
    d = one(w.tick(AT), sid)
    assert d["outcome"] == "failed" and d["reason"].startswith("publication_unavailable")
    assert w.actions() == [] and w.capacity() == ("3\n", "2\n")


@pytest.mark.parametrize("td", ["D-41", {"id": "D-41"}, {"id": "41", "outcome": "approved"},
                                {"id": "D-41", "outcome": "--force"}, {"id": "D-41", "outcome": ""}, 41, []])
def test_a_tracker_decision_the_handler_cannot_publish_exactly_is_refused(tmp_path, td):
    w = World(tmp_path)
    sid = w.propose(cap(tracker_decision=td))
    d = one(w.tick(AT), sid)
    assert d["outcome"] == "failed" and d["reason"].startswith("tracker_decision_malformed")
    assert w.ky_calls() == [] and w.capacity() == ("3\n", "2\n")


def test_ky_that_does_not_answer_leaves_the_publication_unknown_and_is_not_repeated(tmp_path):
    w = World(tmp_path)
    w.ky_says("sleep", 5)
    w.environ["KYVETO_KY_TIMEOUT_S"] = "0.5"
    sid = w.propose(cap(tracker_decision=TD))
    report = w.tick(AT)
    d = one(report, sid)
    assert (d["outcome"], d["reason"]) == ("blocked", "publication_unreconciled")
    assert report["attention"] is True and w.states(sid) == ["PENDING_VETO"]
    assert w.action(sid + ".publish")["state"] == "INTENDED" and w.capacity() == ("3\n", "2\n")
    (w.root / "fake_ky" / "sleep").unlink()
    assert one(w.tick(AFTER), sid)["reason"] == "publication_unreconciled"
    assert len(w.ky_calls()) == 1                                       # unknown never permits a blind retry
    assert w.action(sid + ".publish")["reconciliations"][-1]["outcome"] == "unknown"


def test_restart_between_begin_and_execution_reconciles_then_executes_once(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap(tracker_decision=TD))
    crashed = w.crash("before-execute", "tick", "--now", AT)
    assert crashed.returncode == -signal.SIGKILL, crashed.stderr
    assert w.states(sid) == ["PENDING_VETO", "EFFECTIVE"]
    assert w.action(sid + ".execute")["state"] == "INTENDED" and w.capacity() == ("3\n", "2\n")
    assert (w.run / "locks" / ("decision." + sid)).is_dir()            # the dead handler's locks are still there
    assert (w.run / "locks" / "veto").is_dir()
    report = w.tick(AFTER)
    assert one(report, sid)["outcome"] == "executed"
    assert w.states(sid) == ["PENDING_VETO", "EFFECTIVE", "EXECUTED"]
    rec = w.action(sid + ".execute")
    assert rec["state"] == "DONE" and [r["outcome"] for r in rec["reconciliations"]] == ["not_done"]
    assert w.capacity() == ("6\n", "4\n") and len(w.ky_calls()) == 1   # published once, before the crash
    assert w.history(sid)[-1]["effective_at"] == AT
    assert w.tick(LATER)["decisions"] == []


def test_restart_after_the_executor_ran_observes_the_effect_instead_of_repeating_it(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap())
    crashed = w.crash("after-execute", "tick", "--now", AT)
    assert crashed.returncode == -signal.SIGKILL, crashed.stderr
    assert w.capacity() == ("6\n", "4\n") and w.action(sid + ".execute")["state"] == "INTENDED"
    inodes = [(w.run / n).stat().st_ino for n in ("KY_WORKERS", "KY_VERIFIERS")]
    assert one(w.tick(AFTER), sid)["outcome"] == "executed"
    rec = w.action(sid + ".execute")
    assert rec["state"] == "DONE" and [r["outcome"] for r in rec["reconciliations"]] == ["done"]
    assert [(w.run / n).stat().st_ino for n in ("KY_WORKERS", "KY_VERIFIERS")] == inodes       # not rewritten
    assert w.states(sid) == ["PENDING_VETO", "EFFECTIVE", "EXECUTED"]


@pytest.mark.parametrize("point,calls", [("before-publish", 0), ("after-publish", 1)])
def test_restart_inside_the_publication_never_publishes_blindly(tmp_path, point, calls):
    w = World(tmp_path)
    sid = w.propose(cap(tracker_decision=TD))
    crashed = w.crash(point, "tick", "--now", AT)
    assert crashed.returncode == -signal.SIGKILL, crashed.stderr
    assert w.states(sid) == ["PENDING_VETO"] and w.action(sid + ".publish")["state"] == "INTENDED"
    assert len(w.ky_calls()) == calls
    r = w.cli("tick", "--now", AFTER)
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
    w.crash("before-publish", "tick", "--now", AT)
    report = w.tick(AFTER, publish_observer=lambda record: ("not_done", "no such tracker event"))
    assert one(report, sid)["outcome"] == "executed" and len(w.ky_calls()) == 1


def test_concurrent_handlers_execute_one_proposal_exactly_once(tmp_path):
    w = World(tmp_path)
    hold(w.run, "veto", "ctl-veto")                       # one controller identity, several of its processes
    sid = w.propose(cap(tracker_decision=TD))
    argv = [PY, str(FLEET / "kyveto.py"), "tick", "--now", AT, "--as", "ctl-veto"]
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
    assert report["skipped"] == "veto_role_lock_held" and report["decisions"] == []
    assert w.states(sid) == ["PENDING_VETO"]
    r = w.cli("tick", "--now", AT, "--as", "not-the-holder")
    assert r.returncode == 75 and "role_lock_held_by_another" in r.stderr
    assert w.states(sid) == ["PENDING_VETO"] and w.capacity() == ("3\n", "2\n")


def test_an_executor_that_fails_after_publication_is_failed_and_flagged(tmp_path, monkeypatch):
    w = World(tmp_path)
    sid = w.propose(cap(tracker_decision=TD))

    def broken(params, ctx):
        raise OSError("disk full")

    monkeypatch.setattr(kyveto.REGISTRY["capacity"], "execute", broken)
    report = w.tick(AT)
    d = one(report, sid)
    assert (d["outcome"], d["reason"]) == ("failed", "execution_failed: executor_error: OSError")
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
    d = one(w.tick(AT), sid)
    assert d["outcome"] == "locked" and w.states(sid) == ["PENDING_VETO"] and w.capacity() == ("3\n", "2\n")


def test_a_torn_decision_log_blocks_every_transition(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap())
    with open(w.log, "a") as f:
        f.write('{"id": "SD-20261011T220000Z-1", "state": "VETO')          # it might have been this decision's veto
    before = w.log.read_bytes()
    report = w.tick(AFTER)
    assert report["attention"] is True and report["decisions"] == [] and report["problems"]
    assert w.log.read_bytes() == before and w.capacity() == ("3\n", "2\n")
    assert w.cli("tick", "--now", AFTER).returncode == 3
    assert w.log.read_bytes() == before and w.actions() == []


def test_the_handler_starts_its_line_on_a_fresh_row(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap())
    w.log.write_bytes(w.log.read_bytes().rstrip(b"\n"))                # the last writer left no newline
    assert one(w.tick(AT), sid)["outcome"] == "executed"
    assert w.states(sid) == ["PENDING_VETO", "EFFECTIVE", "EXECUTED"]


def test_a_hard_stop_is_never_delegated(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap(), **{"class": "hard_stop"})
    d = one(w.tick(AT), sid)
    assert (d["outcome"], d["reason"]) == ("failed", "hard_stop_never_delegated")
    assert w.capacity() == ("3\n", "2\n")


def test_routine_decisions_are_not_the_handlers_business(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap(), **{"class": "routine", "state": "EFFECTIVE", "veto_deadline": None, "effective_at": AT})
    before = tree(w.run)
    assert w.tick(LATER)["decisions"] == [] and tree(w.run) == before
    assert w.states(sid) == ["EFFECTIVE"]


def test_unknown_target_kind(tmp_path):
    w = World(tmp_path)
    sid = w.propose({"kind": "merge_everything", "fingerprint": "0" * 64}, bind=False)
    d = one(w.tick(AT), sid)
    assert (d["outcome"], d["reason"]) == ("failed", "unknown_target_kind")
    sid2 = w.propose("not an object", bind=False)
    assert one(w.tick(AT), sid2)["reason"] == "target_unbound"


@pytest.mark.parametrize("target,needle", [
    ({"kind": "capacity", "builders": 6}, "verifiers"),
    ({"kind": "capacity", "builders": 0, "verifiers": 2}, "builders"),
    ({"kind": "capacity", "builders": "6", "verifiers": 2}, "builders"),
    ({"kind": "capacity", "builders": True, "verifiers": 2}, "builders"),
    ({"kind": "capacity", "builders": 6, "verifiers": 16}, "verifiers"),
    ({"kind": "capacity", "builders": 6, "verifiers": 2, "also": "merge PR 1"}, "also"),
])
def test_a_malformed_capacity_target_is_refused(tmp_path, target, needle):
    w = World(tmp_path)
    sid = w.propose(dict(target, fingerprint="0" * 64), bind=False)
    d = one(w.tick(AT), sid)
    assert d["outcome"] == "failed" and d["reason"].startswith("target_malformed") and needle in d["reason"]
    assert w.capacity() == ("3\n", "2\n")


def test_the_awaiting_item_must_still_be_open(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap(), awaiting_open=False)           # resolved or withdrawn during the window
    assert one(w.tick(AT), sid)["reason"] == "awaiting_not_open"
    sid2 = w.propose(cap(), awaiting="the capacity question")
    assert one(w.tick(AT), sid2)["reason"] == "awaiting_unbound"
    assert w.capacity() == ("3\n", "2\n")


def test_the_owners_own_decision_supersedes_the_pending_proposal(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap())
    aw = w.history(sid)[0]["awaiting"]
    cid = kycommands.submit(w.run, "planner", "decide", {"awaiting_id": aw, "answer": "keep six"}, COCKPIT)
    d = one(w.tick(AT), sid)
    assert (d["outcome"], d["reason"]) == ("failed", "superseded_by_owner_decide: " + cid)
    assert w.capacity() == ("3\n", "2\n")


def test_one_awaiting_item_is_decided_by_one_proposal_only(tmp_path):
    w = World(tmp_path)
    first = w.propose(cap(builders=5))
    aw = w.history(first)[0]["awaiting"]
    assert one(w.tick(AT), first)["outcome"] == "executed"
    second = w.propose(cap(builders=9), awaiting=aw)
    d = one(w.tick(AFTER), second)
    assert (d["outcome"], d["reason"]) == ("failed", "awaiting_already_decided: " + first)
    assert w.capacity() == ("5\n", "4\n")


def test_capacity_writes_are_atomic_and_idempotent(tmp_path):
    w = World(tmp_path)
    capacity = kyveto.REGISTRY["capacity"]
    ctx = kyveto.Ctx(w.env, "SD-20261011T220000Z-1", {"source_commit": C1, "entrypoints_digest": E1}, AT)
    params = cap(builders=6, verifiers=2)                 # verifiers already at the requested value
    assert capacity.observer(params, ctx)[0] == "not_done"
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


# ── plan-bundle changes: the activation chain (pairing rule KW-04) ──

def receipt(w, name="review-1.json", verdict="ACCEPTED", commit=C2, reviewer="astra-review-1"):
    d = w.run / "reviews"
    d.mkdir(exist_ok=True)
    (d / name).write_text(json.dumps({"verdict": verdict, "reviewer_session_id": reviewer, "source_commit": commit,
                                      "inputs": {}}))
    return str(d / name)


def bundle(w, **over):
    target = {"kind": "plan_bundle_change", "old_commit": C1, "new_commit": C2, "old_manifest_digest": M1,
              "new_manifest_digest": M2}
    target.update(over)
    target.setdefault("review_receipts", [receipt(w, commit=target["new_commit"])])
    return target


def records(w):
    return sorted(p.name for p in w.run.glob("ACTIVATION_RECORD*.json"))


def test_a_bundle_change_writes_the_next_immutable_activation_record(tmp_path):
    w = World(tmp_path)
    sid = w.propose(bundle(w, tracker_decision=TD), decision="adopt plan v2.8")
    assert one(w.tick(AT), sid)["outcome"] == "executed"
    assert records(w) == ["ACTIVATION_RECORD.1.json"]
    path = w.run / "ACTIVATION_RECORD.1.json"
    rec = json.loads(path.read_text())
    assert_schema("activation_record", rec)
    assert (rec["n"], rec["previous"]) == (1, None)
    assert (rec["old_commit"], rec["new_commit"], rec["old_manifest_digest"], rec["new_manifest_digest"]) == (
        C1, C2, M1, M2)
    assert rec["authorising_act"] == {"kind": "surrogate_decision", "id": sid}
    assert rec["campaign_admission"] is False                          # a bundle change never admits the campaign
    (r1,) = rec["review_receipts"]
    assert r1["sha256"] == sha(r1["path"]) and r1["verdict"] == "ACCEPTED"
    assert rec["owner_decisions"] == {"path": kyveto.OWNER_DECISIONS_PATH, "old_blob": "d" * 40, "new_blob": "d" * 40}
    assert path.stat().st_mode & 0o222 == 0                            # read-only
    assert w.action(sid + ".execute")["result"]["sha256"] == sha(path)
    assert len(w.ky_calls()) == 1
    # the successor chains to it by digest
    w.authorise(C2, E2)
    sid2 = w.propose(bundle(w, old_commit=C2, new_commit=C3, old_manifest_digest=M2, new_manifest_digest=M3,
                            review_receipts=[receipt(w, "review-2.json", commit=C3)]),
                     authority={"source_commit": C2, "entrypoints_digest": E2})
    assert one(w.tick(AFTER), sid2)["outcome"] == "executed"
    assert records(w) == ["ACTIVATION_RECORD.1.json", "ACTIVATION_RECORD.2.json"]
    rec2 = json.loads((w.run / "ACTIVATION_RECORD.2.json").read_text())
    assert rec2["previous"] == {"file": "ACTIVATION_RECORD.1.json", "sha256": sha(path)} and rec2["n"] == 2
    assert_schema("activation_record", rec2)
    assert json.loads(path.read_text()) == rec                         # the earlier record is untouched


def chain_refusal(tmp_path, reason, prepare=None, bind=True, **over):
    """A bundle change that must be FAILED with `reason`: no activation record written, nothing published."""
    w = World(tmp_path)
    target = dict(bundle(w, **over), tracker_decision=TD)
    if prepare:
        prepare(w, target)
    if not bind:
        target["fingerprint"] = "0" * 64
    sid = w.propose(target, bind=bind)
    before = {name: (w.run / name).read_bytes() for name in records(w)}
    d = one(w.tick(AT), sid)
    assert d["outcome"] == "failed" and d["reason"].startswith(reason), d
    assert {name: (w.run / name).read_bytes() for name in records(w)} == before          # nothing written
    assert w.ky_calls() == [] and w.states(sid) == ["PENDING_VETO", "FAILED"]
    return w, sid


def test_bundle_change_refused_when_a_review_receipt_is_missing(tmp_path):
    chain_refusal(tmp_path, "review_receipt_missing", review_receipts=["/nonexistent/review.json"])


def test_bundle_change_refused_when_a_review_receipt_is_not_accepted(tmp_path):
    def reject(w, target):
        target["review_receipts"] = [receipt(w), receipt(w, "review-b.json", verdict="REJECTED")]
    chain_refusal(tmp_path, "review_receipt_not_accepted", prepare=reject)


def test_bundle_change_refused_when_a_review_is_for_another_commit(tmp_path):
    def other(w, target):
        target["review_receipts"] = [receipt(w, commit=C3)]
    chain_refusal(tmp_path, "review_receipt_not_bound", prepare=other)


def test_bundle_change_refused_when_a_review_names_no_reviewer(tmp_path):
    def anonymous(w, target):
        target["review_receipts"] = [receipt(w, reviewer="")]
    chain_refusal(tmp_path, "review_receipt_not_accepted", prepare=anonymous)


def test_bundle_change_refused_without_any_review_receipt(tmp_path):
    chain_refusal(tmp_path, "target_malformed", bind=False, review_receipts=[])


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
    ctx = kyveto.Ctx(w.env, None, {"source_commit": C1, "entrypoints_digest": E1}, AT)
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
    sid = w.propose(bundle(w))
    assert one(w.tick(AT), sid)["outcome"] == "executed"
    first = json.loads((w.run / "ACTIVATION_RECORD.1.json").read_text())
    assert (first["n"], first["previous"]) == (1, names(root))    # link 1 names link 0 by sha256
    assert_schema("activation_record", first)
    assert root.read_bytes() == before and chain_of(w) == ([0, 1], None)
    w.authorise(C2, E2)                                           # now link 1 is the terminal link
    sid2 = w.propose(bundle(w, old_commit=C2, new_commit=C3, old_manifest_digest=M2, new_manifest_digest=M3,
                            review_receipts=[receipt(w, "review-2.json", commit=C3)]),
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
        {"verdict": "ACCEPTED", "reviewer_session_id": "someone-else", "source_commit": C2, "inputs": {"x": 1}}))
    assert one(w.tick(AT), sid)["reason"] == "target_changed"
    assert records(w) == []


def test_the_bundle_executor_is_idempotent_and_never_overwrites(tmp_path):
    w = World(tmp_path)
    change = kyveto.REGISTRY["plan_bundle_change"]
    sid = "SD-20261011T220000Z-7"
    ctx = kyveto.Ctx(w.env, sid, {"source_commit": C1, "entrypoints_digest": E1}, AT)
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
    other = kyveto.Ctx(w.env, "SD-20261011T220000Z-8", {"source_commit": C1, "entrypoints_digest": E1}, AT)
    ok, refused = change.execute(params, other)                   # another decision cannot replay the same step
    assert ok is False and refused["reason"].startswith("activation_chain_mismatch")
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


# ── classes whose executors are later deliverables: never a faked success ──

@pytest.mark.parametrize("kind,helper", [("campaign_start", "kygate.sh"), ("protected_window", "executor.py")])
def test_classes_without_an_installed_executor_fail_closed(tmp_path, kind, helper):
    w = World(tmp_path)
    sid = w.propose({"kind": kind, "item": "N-467", "tracker_decision": TD})
    d = one(w.tick(AT), sid)
    assert (d["outcome"], d["reason"]) == ("failed", "executor_unavailable: " + helper)
    assert w.ky_calls() == [] and w.actions() == []                   # nothing published for what cannot be executed
    assert not (w.run / "OWNER_RESUME.json").exists()
    # the helper's mere presence is not an executor either
    (w.fleet / helper).write_text("#!/bin/bash\nexit 0\n")
    os.chmod(w.fleet / helper, 0o755)
    sid2 = w.propose({"kind": kind, "item": "N-467"})
    d2 = one(w.tick(AFTER), sid2)
    assert d2["outcome"] == "failed" and d2["reason"].startswith("executor_unavailable: ")
    assert "later deliverable" in d2["reason"] and not (w.run / "OWNER_RESUME.json").exists()
    ctx = kyveto.Ctx(w.env, sid2, {"source_commit": C1, "entrypoints_digest": E1}, AT)
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
    w.crash("before-execute", "tick", "--now", AT)        # published and EFFECTIVE, executor not yet run
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

    def precheck(params, ctx):               # the owner's veto lands after step (a), while (e) is still running
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


def test_a_veto_after_the_effect_is_in_place_is_too_late(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap())
    w.crash("after-execute", "tick", "--now", AT)         # the capacity files are already written
    cid = w.veto(sid)
    assert one(w.tick(AFTER), sid)["outcome"] == "executed"
    assert w.states(sid)[-1] == "EXECUTED" and w.command(cid)["state"] == "REJECTED"
    assert w.command(cid)["result"]["reason"].startswith("too_late")


def test_status_reports_states_and_changes_nothing(tmp_path):
    w = World(tmp_path)
    pending = w.propose(cap(tracker_decision=TD))
    vetoed = w.propose(cap(builders=5))
    w.veto(vetoed)
    (w.root / "HOLD").write_text("x\n")
    before = tree(w.run, skip=())
    r = w.cli("status", "--now", BEFORE)
    assert r.returncode == 0, r.stderr
    status = json.loads(r.stdout)
    assert tree(w.run, skip=()) == before and w.ky_calls() == []       # read-only: no lock, no line, no call
    by_id = {d["id"]: d for d in status["decisions"]}
    assert by_id[pending]["state"] == "PENDING_VETO" and by_id[pending]["seconds_remaining"] == 1200
    assert by_id[pending]["veto_command"] is None and by_id[vetoed]["veto_command"]
    assert by_id[pending]["notification_submitted"] is True and by_id[pending]["kind"] == "capacity"
    assert status["holds"] == ["HOLD"] and status["authority"]["source"] == "planner_state"
    w.tick(BEFORE)
    after = json.loads(w.cli("status", "--now", BEFORE).stdout)
    assert {d["id"]: d["state"] for d in after["decisions"]} == {pending: "PENDING_VETO", vetoed: "VETOED"}


def test_status_flags_a_veto_class_decision_made_effective_outside_the_handler(tmp_path):
    w = World(tmp_path)
    sid = w.propose(cap(), state="EFFECTIVE", effective_at=AT)        # the surrogate published it by itself
    r = w.cli("status", "--now", AFTER)
    (row,) = json.loads(r.stdout)["decisions"]
    assert r.returncode == 3 and row["anomaly"] == "veto_class_made_effective_outside_the_handler"
    assert w.tick(AFTER)["decisions"] == [] and w.capacity() == ("3\n", "2\n")       # and it is not executed here
    assert w.states(sid) == ["EFFECTIVE"]


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
    assert w.cli("tock").returncode == 64
    assert w.cli("tick", "--authorised-commit", "xyz", "--entrypoints-digest", E1).returncode == 64
    gone = dict(w.environ, KY_RUN=str(tmp_path / "no-such-run"))
    r = subprocess.run([PY, str(FLEET / "kyveto.py"), "tick"], capture_output=True, text=True, env=gone)
    assert r.returncode == 66 and not (tmp_path / "no-such-run").exists()       # never creates a run tree
