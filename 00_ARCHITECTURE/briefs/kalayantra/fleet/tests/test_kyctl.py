"""B-0c loop control: kynotify.sh, kyloop.py (deterministic controller), kyctl.sh, launchd
templates and the two loop prompts (relaunch plan v2.7 §4a.1-3, §4a.6, §7, §10, §11, §13).

Nothing here touches the real launchctl, ~/Library/LaunchAgents, the real `claude` or
/Users/Dev/kalayantra: every test runs in its own tree under pytest's basetemp with test
doubles from fixtures/b0c_loops/ (fake_claude, fake_launchctl, fake_ky, fake_helper.sh,
fake_osascript, fake_git). Sleeps are compressed with KY_LOOP_SLEEP_SCALE. An autouse fixture points
KY_ROOT / KY_RUN / KY_FLEET of this process at a guard directory, so an in-process code path
that fell back to the process environment still could not reach the live tree.

The second half covers the wiring of the controller to its three sibling modules (kyaction.py,
kycommands.py, kyveto.py — driven here through their public functions, never edited): the `veto`
role, the owner command queue, action-record reconciliation, the activation chain, the
qualification context, lock-takeover strictness and quota detection. Every rule is shown
passing and failing, and a refusal is asserted by its named reason.
"""
import copy
import hashlib
import json
import os
import plistlib
import re
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

FLEET = Path(__file__).resolve().parents[1]
FIX = FLEET / "tests" / "fixtures" / "b0c_loops"
FIX_CONTROL = FLEET / "tests" / "fixtures" / "b0c_control"      # fake_git only (read, never edited here)
PY = "/opt/homebrew/bin/python3" if os.access("/opt/homebrew/bin/python3", os.X_OK) else shutil.which("python3")
sys.dont_write_bytecode = True                 # leave no __pycache__ next to the sources under test
sys.path.insert(0, str(FLEET))

import kyaction  # noqa: E402
import kycommands  # noqa: E402
import kyloop  # noqa: E402
import kyveto  # noqa: E402

LABELS = {r: "in.marsys.kalayantra." + r for r in ("dispatcher", "planner", "conductor", "veto")}
CONTROL_MODULES = ("kyaction.py", "kycommands.py", "kyveto.py")
CREDENTIAL_NAMES = ("DATABASE_URL", "KY_BUILDER_DATABASE_URL", "PGPASSWORD", "ANTHROPIC_API_KEY")
CHILD_ENV = {"HOME", "USER", "LANG", "TERM", "PATH", "TMPDIR", "ZDOTDIR", "KY_ROOT", "KY_RUN", "KY_FLEET",
             "KY_SCRATCH", "KY_ROLE", "KY_RUN_ID"}
SHELL_NOISE = {"PWD", "OLDPWD", "SHLVL", "_"}          # set by bash itself inside the test double
DIGEST = "ab" * 32


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class World:
    """One isolated KY_ROOT with the scripts under test installed the way B-2 would install them."""

    def __init__(self, tmp):
        self.tmp = tmp
        self.root, self.scratch, self.wt, self.home = tmp / "ky", tmp / "scratch", tmp / "wt", tmp / "home"
        self.run, self.fleet = self.root / "run", self.root / "fleet_live"
        self.la, self.lc = tmp / "LaunchAgents", tmp / "launchctl"
        self.repo = tmp / "source-repo"          # stands for the campaign checkout: fake_git sees its .git
        for d in (self.run, self.fleet, self.scratch, self.wt, self.home, self.la, self.lc,
                  self.root / "bin", self.root / "zdotdir", self.root / "fake_ky", self.repo / ".git"):
            d.mkdir(parents=True)
        self.claude = self.root / "bin" / "claude"
        shutil.copy(FIX / "fake_claude", self.claude)
        shutil.copy(FIX / "fake_ky", self.root / "bin" / "ky")
        for name in ("kyversion.sh", "kygate.sh"):
            shutil.copy(FIX / "fake_helper.sh", self.fleet / name)
        for name in ("kynotify.sh", "kyctl.sh", "kyloop.py") + CONTROL_MODULES:
            shutil.copy(FLEET / name, self.fleet / name)
        shutil.copytree(FLEET / "launchd", self.fleet / "launchd")
        shutil.copytree(FLEET / "prompts", self.fleet / "prompts")
        (self.fleet / "mcp.none.json").write_text('{"mcpServers":{}}\n')
        self.receipt("bootstrap")
        self.write_state({"active": {"next": "B-3"}, "completed_steps": []})
        self.loops_json({"planner": {"worktree": str(self.wt)}, "conductor": {"worktree": str(self.wt)}})

    # ---- files
    def receipt(self, mode):
        (self.run / "INSTALL_RECEIPT.json").write_text(json.dumps({"mode": mode}))

    def write_state(self, obj, role="planner"):
        (self.run / ("%s_STATE.json" % role.upper())).write_text(json.dumps(obj))

    def role_state(self, role="planner"):
        return json.loads((self.run / ("%s_STATE.json" % role.upper())).read_text())

    def loops_json(self, obj):
        (self.run / "loops.json").write_text(json.dumps(obj))

    def modes(self, *modes):
        d = self.root / "bin" / "claude.d"
        d.mkdir(exist_ok=True)
        (d / "modes").write_text("".join(m + "\n" for m in modes))

    def default_mode(self, mode):
        d = self.root / "bin" / "claude.d"
        d.mkdir(exist_ok=True)
        (d / "mode").write_text(mode)

    def calls(self):
        d = self.root / "bin" / "claude.d" / "calls"
        return sorted(int(p.stem) for p in d.glob("*.argv")) if d.is_dir() else []

    def call(self, n, what):
        return (self.root / "bin" / "claude.d" / "calls" / ("%d.%s" % (n, what))).read_text()

    def records(self, role="planner"):
        d = self.run / "loops" / role
        paths = sorted(d.glob(role.upper() + "-*.json"), key=lambda p: p.stem) if d.is_dir() else []
        return [json.loads(p.read_text()) for p in paths]          # run ids sort by stem (…Z < …Z-02)

    def loop_state(self, loop="planner"):
        p = self.run / "loops" / (loop + ".json")
        return json.loads(p.read_text()) if p.exists() else None

    def awaiting(self):
        d = self.run / "awaiting"                # the owner's answers (<id>.owner_decision.json) are not items
        return [json.loads(p.read_text()) for p in sorted(d.glob("*.json"))
                if not p.name.endswith(".owner_decision.json")] if d.is_dir() else []

    def cockpit_journal(self):
        p = self.run / "JOURNAL_COCKPIT.md"
        return p.read_text() if p.exists() else ""

    def stop_file(self, loop="planner"):
        return self.run / ("STOP_" + loop)

    # ---- processes
    def env(self, **extra):
        e = {"PATH": "/opt/homebrew/bin:/usr/bin:/bin", "HOME": str(self.home), "USER": "kytest",
             "LANG": "en_US.UTF-8", "KY_ROOT": str(self.root), "KY_RUN": str(self.run),
             "KY_FLEET": str(self.fleet), "KY_SCRATCH": str(self.scratch), "CLAUDE_BIN": str(self.claude),
             "KY_NOTIFY_DRY": "1", "KY_LOOP_SLEEP_SCALE": "0.001", "KY_LAUNCHCTL": str(FIX / "fake_launchctl"),
             "FAKE_LAUNCHCTL_DIR": str(self.lc), "KY_LAUNCHAGENTS_DIR": str(self.la),
             "KY_SOURCE_REPO": str(self.repo), "KY_GIT": str(FIX / "fake_git")}
        e.update(extra)
        return e

    def kyloop(self, *args, timeout=40, **extra):
        return subprocess.run([PY, str(self.fleet / "kyloop.py"), *args], env=self.env(**extra),
                              capture_output=True, text=True, timeout=timeout)

    def popen(self, role, **extra):
        return subprocess.Popen([PY, str(self.fleet / "kyloop.py"), role], env=self.env(**extra),
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    def kyctl(self, *args, timeout=40, **extra):
        return subprocess.run(["/bin/bash", str(self.fleet / "kyctl.sh"), *args], env=self.env(**extra),
                              capture_output=True, text=True, timeout=timeout)

    def enable(self, loop="planner"):
        r = self.kyloop("admin", "enable", loop, "--reason", "test", "--by", "pytest")
        assert r.returncode == 0, r.stderr

    def qualify(self, role="planner", result="PASS", mutate=None, context="as-expected"):
        """A receipt for the controller's own expectation; `context` None leaves the field out."""
        r = self.kyloop("admin", "expected-qualification", role)
        assert r.returncode == 0, r.stderr
        exp = json.loads(r.stdout)
        binds = exp["binds"]
        if mutate:
            mutate(binds)
        d = self.run / "QUALIFICATIONS"
        d.mkdir(exist_ok=True)
        doc = {"schema": "ky.qualification/1", "role": role, "model": exp["model"], "result": result, "binds": binds}
        if context is not None:
            doc["context"] = exp["context"] if context == "as-expected" else context
        (d / ("%s-%s.json" % (role, exp["model"]))).write_text(json.dumps(doc))

    def ready(self, role="planner"):
        self.enable(role)
        self.qualify(role)

    def rearm(self, role="planner"):
        self.stop_file(role).unlink()
        self.enable(role)

    def resume(self, digest=DIGEST, activation=DIGEST):
        self.receipt("final")
        (self.run / "OWNER_RESUME.json").write_text(json.dumps({"binding": "N-467", "approved_bundle_digest": digest}))
        if activation is not None:
            (self.run / "ACTIVATION_RECORD.json").write_text(json.dumps({"final_manifest_digest": activation}))

    def lc_calls(self):
        p = self.lc / "calls.log"
        return p.read_text().splitlines() if p.exists() else []

    def cleanup(self):
        for p in (self.lc / "pid").glob("*") if (self.lc / "pid").is_dir() else []:
            try:
                os.kill(int(p.read_text()), signal.SIGKILL)
            except (ValueError, ProcessLookupError):
                pass
        hang = self.root / "bin" / "claude.d" / "hang.pid"
        if hang.exists():
            try:
                os.kill(int(hang.read_text()), signal.SIGKILL)
            except (ValueError, ProcessLookupError):
                pass


@pytest.fixture(autouse=True)
def _never_the_live_tree(monkeypatch, tmp_path):
    for name, sub in (("KY_ROOT", "guard"), ("KY_RUN", "guard/run"), ("KY_FLEET", "guard/fleet_live")):
        monkeypatch.setenv(name, str(tmp_path / sub))
    for name in ("KY_BIN", "KY_GIT", "KY_SOURCE_REPO", "KY_OWNER_DECISIONS_PATH", "KYVETO_KY_TIMEOUT_S",
                 "KY_LOOP_SLEEP_SCALE", "KY_LOOP_TEST_CONTEXT", "CLAUDE_BIN"):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def w(tmp_path):
    world = World(tmp_path)
    yield world
    world.cleanup()


def wait_for(pred, timeout=10.0, step=0.02):
    end = time.time() + timeout
    while time.time() < end:
        if pred():
            return True
        time.sleep(step)
    return False


def assert_schema(name, doc):
    """Cross-check against the sibling B-0c schema when it is present in this checkout."""
    schema_path, validator = FLEET / "schemas" / (name + ".json"), FLEET / "kyschema.py"
    if not (schema_path.exists() and validator.exists()):
        return
    import importlib.util
    spec = importlib.util.spec_from_file_location("kyschema_under_test", validator)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.validate(mod.load_json(str(schema_path)), doc) == []


def assert_awaiting_schema(doc):
    assert_schema("awaiting", doc)


def refused_after_runs(w, role="planner"):
    """The single shape of a refused precondition: one awaiting file, STOP, disabled."""
    aw = [a for a in w.awaiting() if a["id"].endswith("-loop-%s-precondition" % role)]
    assert len(aw) == 1, w.awaiting()
    a = aw[0]
    assert a["schema"] == "ky.awaiting/1" and a["class_hint"] == "unknown" and a["blocks"] == "loop"
    assert re.fullmatch(r"AW-\d{8}T\d{6}Z-loop-%s-precondition" % role, a["id"])
    assert a["raised_by"]["role"] == role and a["options"] and a["question"]
    assert_awaiting_schema(a)
    assert w.stop_file(role).exists()
    assert w.loop_state(role)["enabled"] is False
    return a


def refused(w, role="planner"):
    """… and, where the refusal comes before any launch, no model run at all."""
    a = refused_after_runs(w, role)
    assert w.calls() == []
    return a


# ───────────────────────────── kynotify.sh ─────────────────────────────

NASTY = 'say "hi" $(touch PWNED_SUB) `touch PWNED_TICK`; touch PWNED_SEMI\nsecond \'line\' -e x'


def notify(w, *args, **extra):
    return subprocess.run(["/bin/bash", str(w.fleet / "kynotify.sh"), *args], env=w.env(**extra), cwd=str(w.tmp),
                          capture_output=True, text=True, timeout=20)


def test_kynotify_journals_literally_and_never_executes(w):
    r = notify(w, NASTY, "--level", "decision")
    assert r.returncode == 0, r.stderr
    lines = w.cockpit_journal().splitlines()
    assert len(lines) == 1
    flat = NASTY.replace("\n", " ")
    assert re.fullmatch(r"- \d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ \[decision\] " + re.escape(flat), lines[0])
    assert not list(w.tmp.glob("PWNED*")) and not list(w.run.glob("PWNED*"))
    assert "journal=ok" in r.stdout and "notify=dry" in r.stdout


def test_kynotify_message_reaches_notifier_only_as_argument(w):
    log = w.tmp / "osascript.argv"
    r = notify(w, NASTY, KY_NOTIFY_DRY="0", KY_OSASCRIPT=str(FIX / "fake_osascript"), FAKE_OSASCRIPT_LOG=str(log))
    assert r.returncode == 0, r.stderr
    argv = log.read_text()
    flat = NASTY.replace("\n", " ")
    assert argv == "\n".join(["-e", "on run argv", "-e",
                              'display notification (item 1 of argv) with title "KĀLA-YANTRA v3"',
                              "-e", "end run", "--", flat]) + "\n"
    assert not list(w.tmp.glob("PWNED*"))
    assert "notify=submitted" in r.stdout and "[info]" in w.cockpit_journal()


def test_kynotify_failed_notification_still_exits_zero_and_is_recorded(w):
    r = notify(w, "disk is fine", "--level", "hard_stop", KY_NOTIFY_DRY="0",
               KY_OSASCRIPT=str(FIX / "fake_osascript"), FAKE_OSASCRIPT_LOG=str(w.tmp / "o"), FAKE_OSASCRIPT_RC="1")
    assert r.returncode == 0
    lines = w.cockpit_journal().splitlines()
    assert "[hard_stop] disk is fine" in lines[0] and "[notify_failed]" in lines[1]
    assert "notify=failed" in r.stdout


def test_kynotify_failed_journal_append_is_nonzero(w):
    r = notify(w, "hello", KY_RUN=str(w.tmp / "no-such-run-dir"))
    assert r.returncode != 0 and "journal=failed" in r.stdout


@pytest.mark.parametrize("args", [(), ("msg", "--level", "shout"), ("", "--level", "info"), ("a", "b")])
def test_kynotify_usage_errors(w, args):
    r = notify(w, *args)
    assert r.returncode == 64 and w.cockpit_journal() == ""


# ───────────────────────────── kyloop.py: admission ─────────────────────────────

def test_stop_file_takes_precedence_and_disables(w):
    w.ready()
    w.stop_file().write_text("x")
    r = w.kyloop("planner")
    assert r.returncode == 0 and w.calls() == []
    st = w.loop_state()
    assert st["enabled"] is False and "STOP" in st["reason"]
    assert not (w.run / "locks" / "planner").exists()


def test_installed_but_never_started_loop_does_not_run(w):
    """RunAtLoad starts the controller at login; only `kyctl start` (after its guards) enables it."""
    w.qualify()
    r = w.kyloop("planner")
    assert r.returncode == 0 and w.calls() == [] and "not enabled" in r.stderr
    assert w.awaiting() == []


def test_global_hold_waits_without_running_then_proceeds(w):
    w.ready()
    w.modes("stop")
    (w.root / "HOLD").write_text("held")
    p = w.popen("planner")
    try:
        assert wait_for(lambda: (w.loop_state() or {}).get("waiting") == "hold")
        time.sleep(0.3)                               # ten scaled hold polls: still nothing launched
        assert w.calls() == [] and p.poll() is None
        (w.root / "HOLD").unlink()
        assert p.wait(timeout=20) == 0
    finally:
        p.kill()
    assert w.calls() == [1] and (w.root / "HOLD").exists() is False


def test_wave_b_done_verified_exits_cleanly(w):
    w.ready()
    w.receipt("final")
    (w.run / "WAVE_B_DONE").write_text(json.dumps({"final_receipt_sha256": sha(w.run / "INSTALL_RECEIPT.json")}))
    r = w.kyloop("planner")
    assert r.returncode == 0 and w.calls() == [] and w.awaiting() == []
    assert w.loop_state()["enabled"] is False and "WAVE_B_DONE" in w.loop_state()["reason"]


@pytest.mark.parametrize("case", ["bootstrap-receipt", "binds-a-bootstrap-receipt", "stale-binding"])
def test_wave_b_done_marker_alone_is_not_believed(w, case):
    w.ready()
    if case == "bootstrap-receipt":
        (w.run / "WAVE_B_DONE").write_text("")
    elif case == "binds-a-bootstrap-receipt":
        (w.run / "WAVE_B_DONE").write_text(json.dumps({"final_receipt_sha256": sha(w.run / "INSTALL_RECEIPT.json")}))
    else:
        w.receipt("final")
        (w.run / "WAVE_B_DONE").write_text(json.dumps({"final_receipt_sha256": "0" * 64}))
    r = w.kyloop("planner")
    assert r.returncode == 0
    assert "wave_b_done_unverified" in json.dumps(refused(w))


@pytest.mark.parametrize("name", CREDENTIAL_NAMES)
def test_credential_variable_names_refuse_with_78_and_no_value(w, name):
    w.ready()
    r = w.kyloop("planner", **{name: "s3cr3t-value-never-printed"})
    assert r.returncode == 78 and name in r.stderr
    assert "s3cr3t" not in r.stderr + r.stdout and w.calls() == []


def test_missing_install_receipt_raises_once_and_does_not_spin(w):
    w.ready()
    (w.run / "INSTALL_RECEIPT.json").unlink()
    r = w.kyloop("planner")
    assert r.returncode == 0
    a = refused(w)
    assert "install_receipt_missing" in json.dumps(a)
    assert "[decision]" in w.cockpit_journal() and w.cockpit_journal().count("\n") == 1
    w.rearm()
    assert w.kyloop("planner").returncode == 0
    refused(w)                                         # still exactly one awaiting file
    assert w.cockpit_journal().count("\n") == 1         # and no second notification for the same item


def test_planner_accepts_bootstrap_or_final_receipt_only(w):
    w.ready()
    w.receipt("rehearsal")
    assert w.kyloop("planner").returncode == 0
    assert "install_receipt_mode" in json.dumps(refused(w))


def test_low_claude_version_refuses(w):
    w.ready()
    (w.root / "bin" / "claude.d").mkdir(exist_ok=True)
    (w.root / "bin" / "claude.d" / "version").write_text("2.1.239 (Claude Code)\n")
    assert w.kyloop("planner").returncode == 0
    a = json.dumps(refused(w))
    assert "claude_version_below_pin" in a and "2.1.239" in a


def test_non_executable_claude_refuses(w):
    w.ready()
    w.claude.chmod(0o644)
    assert w.kyloop("planner").returncode == 0
    assert "claude_bin_not_executable" in json.dumps(refused(w))


def test_kyversion_failure_refuses_and_planner_uses_bootstrap_mode(w):
    w.ready()
    (w.fleet / "kyversion.sh.rc").write_text("3")
    assert w.kyloop("planner").returncode == 0
    assert "kyversion_failed" in json.dumps(refused(w))
    assert (w.fleet / "kyversion.sh.calls").read_text().splitlines()[0] == "--bootstrap"


def test_missing_kyversion_refuses(w):
    w.ready()
    (w.fleet / "kyversion.sh").unlink()
    assert w.kyloop("planner").returncode == 0
    assert "kyversion_missing" in json.dumps(refused(w))


@pytest.mark.parametrize("case", ["missing", "fail", "unknown", "argv-drift", "prompt-drift"])
def test_launch_needs_a_passing_matching_qualification_receipt(w, case):
    w.enable()
    w.default_mode("stop")
    if case == "fail":
        w.qualify(result="FAIL")
    elif case == "unknown":
        w.qualify(result="unknown")
    elif case == "argv-drift":
        w.qualify(mutate=lambda b: b["argv"].append("--bare"))
    elif case == "prompt-drift":
        w.qualify()
        p = w.fleet / "prompts" / "PLANNER_LOOP_v2_4.md"
        p.write_text(p.read_text() + "\nedited after qualification\n")
    assert w.kyloop("planner").returncode == 0
    assert "qualification_" in json.dumps(refused(w))


def test_legacy_role_state_is_not_adopted(w):
    w.ready()
    w.write_state({"completed_steps": [], "in_progress": {"id": "B-0c"}})      # no `active`: legacy schema
    assert w.kyloop("planner").returncode == 0
    assert "role_state_legacy_schema" in json.dumps(refused(w))


BAD_LOOPS = [
    ("unknown-key", {"planner": {"worktree": "WT", "colour": "blue"}}),
    ("unknown-role", {"planner": {"worktree": "WT"}, "dispatcher": {}}),
    ("turns-string", {"planner": {"worktree": "WT", "max_turns": "300"}}),
    ("turns-bool", {"planner": {"worktree": "WT", "max_turns": True}}),
    ("turns-zero", {"planner": {"worktree": "WT", "max_turns": 0}}),
    ("deadline-negative", {"planner": {"worktree": "WT", "deadline_seconds": -5}}),
    ("relative-worktree", {"planner": {"worktree": "relative/path"}}),
    ("effort-unknown", {"planner": {"worktree": "WT", "effort": "ludicrous"}}),
    ("permission-unknown", {"planner": {"worktree": "WT", "permission_mode": "yolo"}}),
    ("model-type", {"planner": {"worktree": "WT", "model": 7}}),
    ("not-object", ["planner"]),
    ("role-not-object", {"planner": "x"}),
    ("mcp-not-empty", {"planner": {"worktree": "WT", "mcp_config": "MCP_FULL"}}),
]


@pytest.mark.parametrize("label,doc", BAD_LOOPS, ids=[b[0] for b in BAD_LOOPS])
def test_loops_json_is_validated_strictly(w, label, doc):
    w.ready()
    full = w.tmp / "mcp.full.json"
    full.write_text('{"mcpServers":{"x":{"command":"true"}}}')
    text = json.dumps(doc).replace('"WT"', json.dumps(str(w.wt))).replace('"MCP_FULL"', json.dumps(str(full)))
    (w.run / "loops.json").write_text(text)
    assert w.kyloop("planner").returncode == 0
    assert "loops_json_invalid" in json.dumps(refused(w)) or "mcp_config" in json.dumps(refused(w))


def test_unparseable_loops_json_refuses(w):
    w.ready()
    (w.run / "loops.json").write_text("{not json")
    assert w.kyloop("planner").returncode == 0
    assert "loops_json_invalid" in json.dumps(refused(w))


def test_role_state_written_by_anyone_else_stops_the_loop(w):
    """Sole writer (plan §4a.1): a stale child or an observing cockpit writing role state is refused."""
    w.ready()
    w.default_mode("substep")
    (w.root / "HOLD").write_text("held")
    p = w.popen("planner")
    try:
        assert wait_for(lambda: (w.loop_state() or {}).get("waiting") == "hold")
        st = w.role_state()
        st["completed_steps"].append({"id": "B-3.forged", "evidence_sha256": "f" * 64})
        w.write_state(st)
        (w.root / "HOLD").unlink()
        assert p.wait(timeout=20) == 0
    finally:
        p.kill()
    assert "role_state_changed_outside_controller" in json.dumps(refused(w))


def test_kylock_helper_is_used_when_installed(w):
    w.ready()
    w.modes("stop")
    shutil.copy(FIX / "fake_helper.sh", w.fleet / "kylock.sh")
    assert w.kyloop("planner").returncode == 0 and w.calls() == [1]
    calls = (w.fleet / "kylock.sh.calls").read_text().splitlines()
    assert re.fullmatch(r"acquire planner CTL-PLANNER-\d{8}T\d{6}Z-\d+", calls[0])
    assert calls[-1] == calls[0].replace("acquire", "release") and not (w.run / "locks" / "planner").exists()
    (w.fleet / "kylock.sh.rc").write_text("1")              # held elsewhere → this instance exits, runs nothing
    w.rearm()
    w.modes("stop")
    r = w.kyloop("planner")
    assert r.returncode == 0 and w.calls() == [1] and "lock held" in r.stderr


def test_unknown_role_is_a_usage_error(w):
    assert w.kyloop("builder").returncode == 64
    assert w.kyloop("veto", "extra").returncode == 64
    assert w.kyloop("admin", "expected-qualification", "veto").returncode == 64     # the veto role launches no model


# ───────────────────────────── kyloop.py: runs ─────────────────────────────

def test_progressing_runs_loop_again_and_the_controller_persists_checkpoints(w):
    w.ready()
    w.modes("substep", "substep", "stop")
    before = w.role_state()
    r = w.kyloop("planner")
    assert r.returncode == 0, r.stderr
    assert w.calls() == [1, 2, 3]
    recs = w.records()
    assert [x["progressed"] for x in recs] == [True, True, False]
    assert all(x["quota_refusal"] is False and x["exit_code"] == 0 and x["ended_at"] for x in recs)
    for key in ("run_id", "role", "pid", "pgid", "process_start", "started_at", "prompt_path", "stdout_path",
                "stderr_path", "progress_before", "progress_after"):
        assert recs[0][key] not in (None, ""), key
    assert re.fullmatch(r"PLANNER-\d{8}T\d{6}Z(-\d\d)?", recs[0]["run_id"])
    assert recs[0]["provider_session_id"] == "fake-session-1"
    st = w.role_state()
    assert st["active"] == before["active"]                       # the controller touches only what it owns
    steps = st["completed_steps"]
    assert [s["id"] for s in steps] == ["B-3.s1", "B-3.s2"]
    for s in steps:
        assert sha(s["evidence"][0]["path"]) == s["evidence_sha256"] == s["evidence"][0]["sha256"]
        assert s["accepted_by"]["run_id"] in (recs[0]["run_id"], recs[1]["run_id"])
    journal = (w.run / "JOURNAL_PLANNER.md").read_text().splitlines()
    assert len(journal) == 2 and all("B-3.s" in line and "evidence sha256" in line for line in journal)
    ls = w.loop_state()
    assert ls["no_progress_count"] == 1 and ls["breaker"]["open"] is False     # only the final `stop` run idled
    scratch = Path(recs[0]["prompt_path"]).parent
    assert scratch == w.scratch / "loops" / "planner" / recs[0]["run_id"]
    for name in ("prompt.md", "stdout.jsonl", "stderr.log", "tmp", "job.json", "state.snapshot.json"):
        assert (scratch / name).exists(), name


def test_launch_line_and_child_environment(w):
    w.ready()
    w.modes("stop")
    r = w.kyloop("planner", GH_TOKEN="x", AWS_SECRET_ACCESS_KEY="y", UNRELATED_PARENT_VAR="z",
                 OPENAI_API_KEY="k", KY_NOTIFY_DRY="1")
    assert r.returncode == 0, r.stderr
    argv = w.call(1, "argv").splitlines()
    assert argv[0] == "-p" and "--bare" not in argv
    joined = " ".join(argv)
    for frag in ("--setting-sources project", "--permission-mode bypassPermissions", "--model claude-opus-5-5",
                 "--effort xhigh", "--max-turns 300", "--strict-mcp-config",
                 "--mcp-config %s" % (w.fleet / "mcp.none.json"), "--output-format stream-json", "--verbose",
                 "--add-dir %s" % w.root):
        assert frag in joined, frag
    names = set(w.call(1, "envnames").split())
    assert CHILD_ENV <= names and names <= CHILD_ENV | SHELL_NOISE, names ^ CHILD_ENV
    assert not any(n in CREDENTIAL_NAMES or n.endswith("_DATABASE_URL") for n in names)
    assert Path(w.call(1, "cwd").strip()) == w.wt.resolve()
    rec = w.records()[0]
    stdin = w.call(1, "stdin")
    assert stdin == Path(rec["prompt_path"]).read_text()
    assert stdin.startswith((w.fleet / "prompts" / "PLANNER_LOOP_v2_4.md").read_text())
    for frag in (rec["run_id"], "role: planner", "max turns: 300", "state.snapshot.json", "JOURNAL_PLANNER.md"):
        assert frag in stdin, frag
    assert rec["argv"][1:] == argv and sorted(rec["env_names"]) == sorted(CHILD_ENV)
    job = json.loads((Path(rec["prompt_path"]).parent / "job.json").read_text())
    assert [i["id"] for i in job["work_items"]] == ["step.B-3", "step.B-4"]     # B-5 waits for both
    assert job["run_id"] == rec["run_id"] and len(job["fence"]) == 32


def test_three_no_progress_runs_open_the_breaker(w):
    w.ready()
    w.default_mode("noprogress")
    state_before = (w.run / "PLANNER_STATE.json").read_bytes()
    r = w.kyloop("planner")
    assert r.returncode == 0, r.stderr
    assert w.calls() == [1, 2, 3]
    recs = w.records()
    assert [x["progressed"] for x in recs] == [False, False, False]
    assert all(x["state_violation"] is True for x in recs)                  # the child rewrote role state …
    assert (w.run / "PLANNER_STATE.json").read_bytes() == state_before      # … and the controller restored it
    assert (w.run / "JOURNAL_PLANNER.md").read_text().count("fake child journal line") == 3   # not progress
    aw = [a for a in w.awaiting() if a["id"].endswith("-loop-planner-no-progress")]
    assert len(aw) == 1 and aw[0]["blocks"] == "loop" and aw[0]["class_hint"] == "unknown"
    assert_awaiting_schema(aw[0])
    assert w.stop_file().exists()
    ls = w.loop_state()
    assert ls["enabled"] is False and ls["breaker"]["open"] is True and ls["no_progress_count"] == 3
    assert "no-progress" in w.cockpit_journal()


def test_breaker_refuses_restart_until_evidence_changes(w):
    w.ready()
    w.default_mode("noprogress")
    assert w.kyloop("planner").returncode == 0 and w.calls() == [1, 2, 3]
    # the surrogate "decides" and someone restarts: nothing underlying changed → refused again
    for p in (w.run / "awaiting").glob("*.json"):
        p.unlink()
    w.rearm()
    r = w.kyloop("planner")
    assert r.returncode == 0 and w.calls() == [1, 2, 3] and "evidence unchanged" in r.stderr
    assert w.stop_file().exists() and w.loop_state()["breaker"]["open"] is True
    # a recorded changed condition (here: a step accepted elsewhere) reopens it
    st = w.role_state()
    st["completed_steps"].append({"id": "B-3.cockpit", "evidence_sha256": "c" * 64, "note": "by the fenced cockpit"})
    w.write_state(st)
    w.rearm()
    w.modes("stop")
    assert w.kyloop("planner").returncode == 0
    assert w.calls() == [1, 2, 3, 4]
    br = w.loop_state()["breaker"]
    assert br["open"] is False and len(br["history"]) == 1 and br["history"][0]["from"] != br["history"][0]["to"]


def test_no_progress_count_survives_controller_restarts(w):
    w.ready()
    w.default_mode("noprogress-stop")
    for expected in (1, 2):
        assert w.kyloop("planner").returncode == 0
        assert w.loop_state()["no_progress_count"] == expected and w.loop_state()["breaker"]["open"] is False
        w.rearm()
    assert w.kyloop("planner").returncode == 0
    assert w.calls() == [1, 2, 3] and w.loop_state()["breaker"]["open"] is True
    assert any(a["id"].endswith("-loop-planner-no-progress") for a in w.awaiting())


def test_quota_backoff_escalates_caps_and_resets(w):
    w.ready()
    w.modes("quota", "quota-stream", "quota", "quota", "quota", "substep", "quota", "stop")
    t0 = time.time()
    r = w.kyloop("planner", KY_LOOP_SLEEP_SCALE="0.0003")
    assert r.returncode == 0, r.stderr
    assert w.calls() == list(range(1, 9))
    recs = w.records()
    assert [x["quota_refusal"] for x in recs] == [True, True, True, True, True, False, True, False]
    assert [x["backoff_minutes"] for x in recs] == [5, 10, 20, 30, 30, 0, 5, 0]
    assert recs[5]["progressed"] is True
    assert time.time() - t0 >= (5 + 10 + 20 + 30 + 30 + 5) * 60 * 0.0003          # the waits really happened
    assert w.loop_state()["breaker"]["open"] is False and w.loop_state()["no_progress_count"] == 1
    assert w.cockpit_journal().count("quota") == 5       # 5,10,20,30 then (cap: silent) then 5 after the reset


def test_prose_about_limits_and_an_allowed_rate_event_are_not_a_refusal(w):
    w.ready()
    w.modes("ratelimit-allowed", "stop")
    assert w.kyloop("planner").returncode == 0
    recs = w.records()
    assert recs[0]["quota_refusal"] is False and recs[0]["progressed"] is True


def test_quota_backoff_is_honoured_across_a_restart(w):
    w.ready()
    w.modes("quota")
    p = w.popen("planner", KY_LOOP_SLEEP_SCALE="0.01")           # first backoff: 5 min → 3 s
    try:
        assert wait_for(lambda: (w.loop_state() or {}).get("waiting") == "quota_backoff")
        p.send_signal(signal.SIGTERM)
        assert p.wait(timeout=10) == 143
    finally:
        p.kill()
    w.modes("stop")
    t0 = time.time()
    assert w.kyloop("planner", KY_LOOP_SLEEP_SCALE="0.01").returncode == 0
    assert w.calls() == [1, 2] and time.time() - t0 >= 1.5       # the restart waited out the stored not_before


@pytest.mark.parametrize("mode,reason", [("badfence", "fence_mismatch"), ("noevidence", "no_verifiable_evidence"),
                                         ("unassigned", "item_not_assigned"), ("badhash", "evidence_hash_mismatch")])
def test_checkpoint_requests_are_validated_before_they_count(w, mode, reason):
    w.ready()
    w.modes(mode, "stop")
    assert w.kyloop("planner").returncode == 0
    rec = w.records()[0]
    assert rec["progressed"] is False and rec["accepted"] == []
    assert rec["refused"] and rec["refused"][0]["reason"] == reason
    assert w.role_state()["completed_steps"] == []


def test_second_instance_is_refused_and_term_reaches_the_child(w):
    w.ready()
    w.modes("hang")
    a = w.popen("planner")
    hang = w.root / "bin" / "claude.d" / "hang.pid"
    try:
        assert wait_for(hang.exists)
        child = int(hang.read_text())
        owner = json.loads((w.run / "locks" / "planner" / "owner.json").read_text())
        assert owner["pid"] == a.pid and owner["process_start"] and owner["child"]["pid"] == child
        ls = w.loop_state()
        assert ls["expected_child"]["pid"] == child and ls["controller"]["pid"] == a.pid
        b = w.kyloop("planner")
        assert b.returncode == 0 and "lock held" in b.stderr and w.calls() == [1]
        a.send_signal(signal.SIGTERM)
        assert a.wait(timeout=20) == 143                  # no STOP file: not an explicit stop → launchd restarts
    finally:
        a.kill()
    assert wait_for(lambda: subprocess.run(["/bin/ps", "-p", str(child)], capture_output=True).returncode != 0)
    rec = w.records()[0]
    assert rec["terminated_by_signal"] is True and rec["ended_at"] and rec["progressed"] is False
    assert not (w.run / "locks" / "planner").exists()
    assert w.loop_state()["expected_child"] is None


def test_wall_clock_deadline_terminates_the_child(w):
    w.loops_json({"planner": {"worktree": str(w.wt), "deadline_seconds": 600}})
    w.ready()
    w.modes("hang", "stop")
    r = w.kyloop("planner")                                # 600 s × 0.001
    assert r.returncode == 0, r.stderr
    rec = w.records()[0]
    assert rec["timed_out"] is True and rec["progressed"] is False


def test_orphan_child_and_stale_lock_are_reconciled_before_any_replacement(w):
    w.ready()
    w.modes("stop")
    orphan = subprocess.Popen(["/bin/sleep", "60"], start_new_session=True)
    try:
        start = subprocess.run(["/bin/ps", "-o", "lstart=", "-p", str(orphan.pid)], capture_output=True,
                               text=True).stdout.strip()
        dead = subprocess.Popen(["/usr/bin/true"])
        dead.wait()
        lock = w.run / "locks" / "planner"
        lock.mkdir(parents=True)
        (lock / "owner.json").write_text(json.dumps({"session_or_run_id": "CTL-dead", "pid": dead.pid, "pgid": dead.pid,
                                                     "process_start": "Thu Jan  1 00:00:00 1970", "acquired_at": "x"}))
        rid = "PLANNER-20260101T000000Z"
        rs = w.scratch / "loops" / "planner" / rid
        (rs / "out" / "checkpoints").mkdir(parents=True)
        (w.run / "loops" / "planner").mkdir(parents=True, exist_ok=True)
        rec = {"run_id": rid, "role": "planner", "pid": orphan.pid, "pgid": orphan.pid, "process_start": start,
               "started_at": "2026-01-01T00:00:00Z", "ended_at": None, "exit_code": None, "fence": "f" * 32,
               "work_items": [], "out_dir": str(rs / "out"), "stdout_path": str(rs / "stdout.jsonl"),
               "stderr_path": str(rs / "stderr.log"), "deadline_at": "2026-01-01T00:00:01Z",
               "state_snapshot_sha256": sha(w.run / "PLANNER_STATE.json"), "progress_before": {}}
        (w.run / "loops" / "planner" / (rid + ".json")).write_text(json.dumps(rec))
        old_launch(w, rid, controller="CTL-dead")          # the dead controller's intent: what recovery starts from
        st = w.loop_state()
        st["expected_child"] = {"run_id": rid, "pid": orphan.pid, "pgid": orphan.pid, "process_start": start}
        (w.run / "loops" / "planner.json").write_text(json.dumps(st))
        r = w.kyloop("planner")
        assert r.returncode == 0, r.stderr
        assert orphan.wait(timeout=5) != 0                  # past its recorded deadline → terminated by identity
    finally:
        orphan.kill()
    old = json.loads((w.run / "loops" / "planner" / (rid + ".json")).read_text())
    assert old["ended_at"] and old["ended_reason"] == "orphan_reconciled" and old["exit_code"] is None
    assert w.calls() == [1]                                 # exactly one replacement, after reconciliation
    assert "stale" in r.stderr
    act = kyaction.load(w.run, "LAUNCH-" + rid)
    assert act["state"] == "DONE" and act["result"]["ended_reason"] == "orphan_reconciled"
    assert [x["outcome"] for x in act["reconciliations"]] == ["done"]


def test_planner_completion_is_derived_by_the_controller(w):
    done = [{"id": s, "evidence_sha256": "d" * 64, "note": "accepted earlier"} for s in ("B-3", "B-4")]
    w.write_state({"active": {}, "completed_steps": done})
    w.ready()
    w.receipt("final")
    (w.run / "VERSIONS.json").write_text("{}")
    w.modes("step")
    r = w.kyloop("planner")
    assert r.returncode == 0, r.stderr
    assert w.calls() == [1]
    job = json.loads((Path(w.records()[0]["prompt_path"]).parent / "job.json").read_text())
    assert [i["id"] for i in job["work_items"]] == ["step.B-5"]
    marker = json.loads((w.run / "WAVE_B_DONE").read_text())
    assert marker["final_receipt_sha256"] == sha(w.run / "INSTALL_RECEIPT.json")
    assert marker["steps"] == ["B-3", "B-4", "B-5"]
    assert w.loop_state()["enabled"] is False and not w.stop_file().exists()
    assert (w.fleet / "kyversion.sh.calls").read_text().splitlines()[-1] == ""       # normal mode, no arguments


def test_completion_without_a_final_receipt_is_raised_not_claimed(w):
    done = [{"id": s, "evidence_sha256": "d" * 64} for s in ("B-3", "B-4", "B-5")]
    w.write_state({"active": {}, "completed_steps": done})
    w.ready()
    assert w.kyloop("planner").returncode == 0
    assert "completion_unverified" in json.dumps(refused(w))
    assert not (w.run / "WAVE_B_DONE").exists()


def test_item_blocked_by_an_open_owner_wait_is_not_relaunched(w):
    w.ready()
    w.default_mode("stop")
    (w.run / "awaiting").mkdir()
    for step in ("B-3", "B-4"):
        (w.run / "awaiting" / ("AW-20261011T000000Z-%s.json" % step)).write_text(json.dumps(
            {"schema": "ky.awaiting/1", "id": "AW-20261011T000000Z-" + step, "item": step, "blocks": "item"}))
    p = w.popen("planner")
    try:
        assert wait_for(lambda: (w.loop_state() or {}).get("waiting") == "no_eligible_work")
        time.sleep(0.2)
        assert w.calls() == [] and p.poll() is None          # waiting happens in the controller, not in a model
        (w.run / "awaiting" / "AW-20261011T000000Z-B-4.json").unlink()
        assert p.wait(timeout=20) == 0
    finally:
        p.kill()
    job = json.loads((Path(w.records()[0]["prompt_path"]).parent / "job.json").read_text())
    assert [i["id"] for i in job["work_items"]] == ["step.B-4"]


def test_owner_wait_is_a_changed_dependency_and_pauses_that_item_only(w):
    w.ready()
    w.modes("await", "stop")
    assert w.kyloop("planner").returncode == 0
    first, second = w.records()
    assert first["accepted"] == [] and first["dependency_changed"] is True and first["progressed"] is True
    job = json.loads((Path(second["prompt_path"]).parent / "job.json").read_text())
    assert [i["id"] for i in job["work_items"]] == ["step.B-4"]       # B-3 waits for its owner-wait; B-4 goes on
    assert w.loop_state()["no_progress_count"] == 1                    # only the idle `stop` run


# ───────────────────────────── kyloop.py: conductor ─────────────────────────────

def test_conductor_without_owner_resume_exits_and_raises_nothing(w):
    w.ready("conductor")
    r = w.kyloop("conductor")
    assert r.returncode == 0 and w.calls() == [] and w.awaiting() == [] and not w.stop_file("conductor").exists()


def test_conductor_waits_in_the_controller_and_hands_over_a_checked_batch(w):
    w.resume()
    w.ready("conductor")
    w.default_mode("ack")
    (w.root / "fake_ky" / "inbox.S.json").write_text(json.dumps([{"msg_id": "M1", "detail": "$(touch PWNED) one"}]))
    (w.root / "fake_ky" / "inbox.steward.json").write_text(json.dumps([{"msg_id": "M2", "detail": "two"}]))
    (w.run / "handled").mkdir()
    (w.run / "handled" / "msg.M0.json").write_text(json.dumps({"id": "msg.M0"}))
    p = w.popen("conductor")
    try:
        assert wait_for(lambda: w.calls() == [1] and (w.loop_state("conductor") or {}).get("waiting") == "no_eligible_work")
        time.sleep(0.2)
        assert w.calls() == [1]                               # empty inboxes cost no model turns
        w.stop_file("conductor").write_text("x")
        assert p.wait(timeout=20) == 0
    finally:
        p.kill()
    rec = w.records("conductor")[0]
    batch = json.loads((Path(rec["prompt_path"]).parent / "batch.json").read_text())
    assert [(i["id"], i["stream"]) for i in batch["items"]] == [("msg.M1", "S"), ("msg.M2", "steward")]
    assert rec["progressed"] is True and sorted(rec["accepted"]) == ["M1", "M2"]
    assert (w.run / "handled" / "msg.M1.json").exists() and (w.run / "handled" / "msg.M2.json").exists()
    assert "PWNED" not in Path(rec["prompt_path"]).read_text()      # message text never enters the prompt
    assert not list(w.tmp.rglob("PWNED"))
    calls = (w.fleet / "kyversion.sh.calls").read_text().splitlines()
    assert calls[0] == "--expected-manifest-digest " + DIGEST
    assert (w.fleet / "kygate.sh.calls").exists()
    argv = w.call(1, "argv")
    assert "--effort\nhigh" in argv and "--max-turns\n150" in argv
    assert all(line.startswith("inbox ") for line in (w.root / "fake_ky" / "calls.log").read_text().splitlines())
    assert [s["id"] for s in w.role_state("conductor")["completed_steps"]] == ["M1", "M2"]
    assert w.loop_state("conductor")["counters"]["wakeups"] == 1
    assert not list((w.run / "locks").glob("msg.*"))


def test_conductor_message_not_acked_is_not_accepted(w):
    w.resume()
    w.ready("conductor")
    w.default_mode("ack-none")
    (w.root / "fake_ky" / "inbox.S.json").write_text(json.dumps([{"msg_id": "M1", "detail": "one"}]))
    assert w.kyloop("conductor").returncode == 0           # three unaccepted runs → breaker
    recs = w.records("conductor")
    assert len(recs) == 3 and all(x["progressed"] is False for x in recs)
    assert recs[0]["refused"][0]["reason"] == "message_still_unacked"
    assert not (w.run / "handled" / "msg.M1.json").exists()


def test_conductor_blind_event_source_is_raised_not_ignored(w):
    w.resume()
    w.ready("conductor")
    (w.root / "fake_ky" / "rc").write_text("2")              # `ky inbox` fails: neither "some" nor "none"
    r = w.kyloop("conductor")
    assert r.returncode == 0
    assert "event_source_failed" in json.dumps(refused(w, "conductor"))


@pytest.mark.parametrize("case", ["digest-mismatch", "no-activation", "bootstrap-receipt", "gate-closed", "bad-resume"])
def test_conductor_start_up_chain_refuses(w, case):
    if case == "digest-mismatch":
        w.resume(activation="cd" * 32)
    elif case == "no-activation":
        w.resume(activation=None)
    else:
        w.resume()
    w.ready("conductor")
    if case == "bootstrap-receipt":
        w.receipt("bootstrap")
    if case == "gate-closed":
        (w.fleet / "kygate.sh.rc").write_text("1")
    if case == "bad-resume":
        (w.run / "OWNER_RESUME.json").write_text(json.dumps({"approved_bundle_digest": "short"}))
        r = w.kyloop("conductor")
        assert r.returncode == 0 and w.calls() == [] and w.awaiting() == []       # invalid resume: raise nothing
        return
    assert w.kyloop("conductor").returncode == 0
    refused(w, "conductor")


# ───────────────────────────── kyctl.sh ─────────────────────────────

def install(w):
    r = w.kyctl("install")
    assert r.returncode == 0, r.stderr + r.stdout
    return r


def plist(w, loop):
    return w.la / (LABELS[loop] + ".plist")


def test_install_renders_valid_plists_idempotently_and_starts_nothing(w):
    install(w)
    first = {loop: (plist(w, loop).read_bytes(), plist(w, loop).stat().st_mtime_ns) for loop in LABELS}
    for loop in LABELS:
        p = plist(w, loop)
        assert subprocess.run(["/usr/bin/plutil", "-lint", str(p)], capture_output=True).returncode == 0
        d = plistlib.loads(p.read_bytes())
        assert d["Label"] == LABELS[loop] and d["RunAtLoad"] is True
        assert d["KeepAlive"] == {"SuccessfulExit": False}
        assert d["ProcessType"] == "Background" and d["ThrottleInterval"] == 10
        names = {"PATH", "HOME", "USER", "LANG", "KY_ROOT", "KY_RUN", "KY_FLEET", "KY_SCRATCH", "CLAUDE_BIN"}
        if loop != "dispatcher":                # the checkout kyveto.py compares the owner-decisions blob in
            names.add("KY_SOURCE_REPO")
            assert d["EnvironmentVariables"]["KY_SOURCE_REPO"] == str(w.repo)
        assert set(d["EnvironmentVariables"]) == names
        assert d["EnvironmentVariables"]["KY_ROOT"] == str(w.root)
        assert d["EnvironmentVariables"]["CLAUDE_BIN"] == str(w.claude)
        assert "@" not in p.read_text()
        log = str(w.scratch / ("dispatcher" if loop == "dispatcher" else "loops/" + loop) / "launchd.log")
        assert d["StandardOutPath"] == d["StandardErrorPath"] == log and Path(log).parent.is_dir()
    assert plistlib.loads(plist(w, "planner").read_bytes())["ProgramArguments"] == [
        "/opt/homebrew/bin/python3", "-u", str(w.fleet / "kyloop.py"), "planner"]
    assert plistlib.loads(plist(w, "dispatcher").read_bytes())["ProgramArguments"] == [
        "/opt/homebrew/bin/python3", "-u", str(w.fleet / "kydispatch.py")]
    assert plistlib.loads(plist(w, "veto").read_bytes())["ProgramArguments"] == [
        "/opt/homebrew/bin/python3", "-u", str(w.fleet / "kyloop.py"), "veto"]
    r = install(w)
    assert r.stdout.count("unchanged") == len(LABELS) == 4
    assert first == {loop: (plist(w, loop).read_bytes(), plist(w, loop).stat().st_mtime_ns) for loop in LABELS}
    assert w.lc_calls() == [] and w.loop_state("planner") is None


def test_templates_carry_no_credential_and_only_known_placeholders():
    allowed = {"@KY_ROOT@", "@KY_RUN@", "@KY_FLEET@", "@KY_SCRATCH@", "@HOME@", "@USER@", "@CLAUDE_BIN@"}
    for loop, label in LABELS.items():
        text = (FLEET / "launchd" / (label + ".plist")).read_text()
        found = set(re.findall(r"@[A-Z_]+@", text))
        assert found - {"@KY_SOURCE_REPO@"} <= allowed
        assert ("@KY_SOURCE_REPO@" in found) == (loop != "dispatcher")
        assert not re.search(r"(?i)token|secret|password|api_key|DATABASE_URL|PGPASS", text)


def test_install_renders_the_source_repo_from_the_environment_or_its_default(w):
    env = w.env()
    del env["KY_SOURCE_REPO"]
    r = subprocess.run(["/bin/bash", str(w.fleet / "kyctl.sh"), "install"], env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    for loop in ("planner", "conductor", "veto"):
        d = plistlib.loads(plist(w, loop).read_bytes())
        assert d["EnvironmentVariables"]["KY_SOURCE_REPO"] == \
            "/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-campaign"
    assert "KY_SOURCE_REPO" not in plistlib.loads(plist(w, "dispatcher").read_bytes())["EnvironmentVariables"]
    r = w.kyctl("install", KY_SOURCE_REPO="relative/checkout")
    assert r.returncode != 0 and "not an absolute path" in r.stderr


SOURCE_REPOS = ["directory-missing", "not-a-work-tree", "plist-without-the-variable", "git-unavailable"]


@pytest.mark.parametrize("case", SOURCE_REPOS)
def test_veto_start_needs_the_source_repo_of_its_installed_plist_to_be_a_git_work_tree(w, case):
    install(w)
    assert w.kyctl("start", "veto").returncode == 0         # the unbroken configuration starts …
    assert w.kyctl("stop", "veto").returncode == 0
    w.stop_file("veto").unlink()
    n, extra = len(w.lc_calls()), {}
    if case == "directory-missing":
        shutil.rmtree(w.repo)
    elif case == "not-a-work-tree":
        (w.repo / ".git").rmdir()
    elif case == "git-unavailable":                         # what cannot be observed is not assumed
        extra["KY_GIT"] = str(w.tmp / "no-git")
    else:
        d = plistlib.loads(plist(w, "veto").read_bytes())
        del d["EnvironmentVariables"]["KY_SOURCE_REPO"]
        plist(w, "veto").write_bytes(plistlib.dumps(d))
    # the shell's own variable points at a perfectly good checkout: only the installed plist's value counts
    good = w.tmp / "another-checkout"
    (good / ".git").mkdir(parents=True)
    r = w.kyctl("start", "veto", **dict({"KY_SOURCE_REPO": str(good)}, **extra))
    assert r.returncode == 2 and "REFUSED veto: source-repo-missing" in r.stderr, r.stderr
    assert not any(c.startswith(("bootstrap", "kickstart")) for c in w.lc_calls()[n:])
    assert w.loop_state("veto")["enabled"] is False
    assert w.kyctl("start", "planner").returncode == 0      # the guard is the veto loop's alone


def test_the_source_repo_guard_asks_real_git_about_this_checkout(w):
    """Read-only (`git rev-parse --is-inside-work-tree` only): the double is not the only evidence."""
    repo, git = FLEET.parents[3], "/usr/bin/git"
    probe = subprocess.run([git, "-C", str(repo), "rev-parse", "--is-inside-work-tree"], capture_output=True, text=True)
    if probe.returncode != 0 or probe.stdout.strip() != "true":
        pytest.skip("this copy of the sources is not inside a git work tree")
    assert w.kyctl("install", KY_SOURCE_REPO=str(repo), KY_GIT=git).returncode == 0
    r = w.kyctl("start", "veto", KY_GIT=git)
    assert r.returncode == 0 and "bootstrapped" in r.stdout, r.stderr
    assert w.kyctl("stop", "veto", KY_GIT=git).returncode == 0
    w.stop_file("veto").unlink()
    plain = w.tmp / "not-a-checkout"
    plain.mkdir()
    assert w.kyctl("install", KY_SOURCE_REPO=str(plain), KY_GIT=git).returncode == 0
    r = w.kyctl("start", "veto", KY_GIT=git)
    assert r.returncode == 2 and "source-repo-missing" in r.stderr and "not a git work tree" in r.stderr


GUARDS = [
    ("planner", "plist-not-installed", lambda w: plist(w, "planner").unlink()),
    ("planner", "stop-file-present", lambda w: w.stop_file("planner").write_text("x")),
    ("planner", "install-receipt-missing", lambda w: (w.run / "INSTALL_RECEIPT.json").unlink()),
    ("planner", "install-receipt-mode", lambda w: w.receipt("rehearsal")),
    ("planner", "wave-b-done", lambda w: (w.run / "WAVE_B_DONE").write_text("")),
    ("planner", "kyloop-missing", lambda w: (w.fleet / "kyloop.py").rename(w.fleet / "kyloop.py.away")),
    ("conductor", "install-receipt-not-final", lambda w: w.receipt("bootstrap")),
    ("conductor", "owner-resume-missing", lambda w: (w.run / "OWNER_RESUME.json").unlink()),
    ("dispatcher", "dispatcher-missing", lambda w: (w.fleet / "kydispatch.py").unlink()),
    ("dispatcher", "install-receipt-missing", lambda w: (w.run / "INSTALL_RECEIPT.json").unlink()),
    ("veto", "plist-not-installed", lambda w: plist(w, "veto").unlink()),
    ("veto", "stop-file-present", lambda w: w.stop_file("veto").write_text("x")),
    ("veto", "install-receipt-missing", lambda w: (w.run / "INSTALL_RECEIPT.json").unlink()),
    ("veto", "install-receipt-unreadable", lambda w: (w.run / "INSTALL_RECEIPT.json").write_text("{torn")),
    ("veto", "control-module-missing", lambda w: (w.fleet / "kyveto.py").unlink()),
    ("planner", "control-module-missing", lambda w: (w.fleet / "kyaction.py").unlink()),
    ("conductor", "control-module-missing", lambda w: (w.fleet / "kycommands.py").unlink()),
]


@pytest.mark.parametrize("loop,reason,breakit", GUARDS, ids=["%s:%s" % (g[0], g[1]) for g in GUARDS])
def test_each_start_guard_refuses_with_its_reason(w, loop, reason, breakit):
    install(w)
    (w.fleet / "kydispatch.py").write_text("# placeholder: a later deliverable\n")
    w.resume()
    if loop != "conductor":
        w.receipt("bootstrap")
    assert w.kyctl("start", loop).returncode == 0          # the unbroken configuration starts …
    assert w.kyctl("stop", loop).returncode == 0
    w.stop_file(loop).unlink()
    n = len(w.lc_calls())
    breakit(w)
    r = w.kyctl("start", loop)                             # … and each broken one refuses, by name
    assert r.returncode != 0 and ("REFUSED %s: %s" % (loop, reason)) in r.stderr, r.stderr
    assert not any(c.startswith(("bootstrap", "kickstart")) for c in w.lc_calls()[n:])
    assert (w.loop_state(loop) or {}).get("enabled") is not True


def test_start_is_idempotent_and_enables_only_after_the_guards(w):
    install(w)
    r = w.kyctl("start", "planner")
    assert r.returncode == 0 and "bootstrapped" in r.stdout, r.stderr
    assert w.loop_state("planner")["enabled"] is True
    assert sum(c.startswith("bootstrap ") for c in w.lc_calls()) == 1
    assert re.match(r"bootstrap gui/\d+ %s$" % re.escape(str(plist(w, "planner"))),
                    [c for c in w.lc_calls() if c.startswith("bootstrap")][0])
    r2 = w.kyctl("start", "planner")
    assert r2.returncode == 0 and "already running" in r2.stdout
    assert sum(c.startswith(("bootstrap ", "kickstart ")) for c in w.lc_calls()) == 1
    # loaded but not running → kickstart, not a second bootstrap
    os.kill(int((w.lc / "pid" / LABELS["planner"]).read_text()), signal.SIGKILL)
    assert wait_for(lambda: "state=stopped" in w.kyctl("status").stdout.splitlines()[1])
    r3 = w.kyctl("start", "planner")
    assert r3.returncode == 0 and "kickstarted" in r3.stdout
    assert sum(c.startswith("kickstart ") for c in w.lc_calls()) == 1


def test_start_refuses_when_launchd_cannot_be_observed(w):
    install(w)
    r = w.kyctl("start", "planner", KY_LAUNCHCTL=str(w.tmp / "no-launchctl"))
    assert r.returncode == 2 and "REFUSED planner: launchd-state-unknown" in r.stderr
    assert w.loop_state("planner") is None


def test_stop_creates_stop_disables_and_confirms(w):
    install(w)
    assert w.kyctl("start", "planner").returncode == 0
    r = w.kyctl("stop", "planner")
    assert r.returncode == 0, r.stderr
    assert w.stop_file("planner").exists() and w.loop_state("planner")["enabled"] is False
    assert any(c.startswith("bootout gui/") and c.endswith(LABELS["planner"]) for c in w.lc_calls())
    assert not (w.lc / "loaded" / LABELS["planner"]).exists()
    assert w.kyctl("stop", "planner").returncode == 0      # stopping a stopped loop is fine


def test_stop_that_cannot_confirm_is_nonzero(w):
    install(w)
    assert w.kyctl("start", "planner").returncode == 0
    (w.lc / "bootout_stuck").write_text("")
    r = w.kyctl("stop", "planner", KY_LOOP_SLEEP_SCALE="0.001")
    assert r.returncode != 0 and "stop-unconfirmed" in r.stderr and w.stop_file("planner").exists()


def status_line(w, loop, **extra):
    r = w.kyctl("status", **extra)
    assert r.returncode == 0, r.stderr
    return [line for line in r.stdout.splitlines() if line.startswith(loop + " ")][0], r.stdout


def test_status_reports_only_what_it_observed(w):
    line, out = status_line(w, "planner")
    assert "state=not-installed" in line and "running" not in out
    install(w)
    line, _ = status_line(w, "planner")
    assert "state=stopped" in line and "loaded=no" in line and "enabled=unset" in line
    assert w.kyctl("start", "planner").returncode == 0
    line, _ = status_line(w, "planner")
    pid = (w.lc / "pid" / LABELS["planner"]).read_text().strip()
    assert "state=running" in line and ("pid=" + pid) in line and "enabled=true" in line
    # launchctl claims "running" but the pid it names is dead → never "running"
    os.kill(int(pid), signal.SIGKILL)
    (w.lc / "claim_running" / LABELS["planner"]).write_text("")
    assert wait_for(lambda: subprocess.run(["/bin/ps", "-p", pid], capture_output=True).returncode != 0)
    line, _ = status_line(w, "planner")
    assert "state=unknown" in line and "state=running" not in line
    # … and with no pid at all
    (w.lc / "pid" / LABELS["planner"]).write_text("")
    line, _ = status_line(w, "planner")
    assert "state=unknown" in line
    # unparseable launchctl output, or no launchctl at all → unknown, still exit 0
    (w.lc / "print_garbage").write_text("")
    assert "state=unknown" in status_line(w, "planner")[0]
    line, out = status_line(w, "planner", KY_LAUNCHCTL=str(w.tmp / "no-launchctl"))
    assert "state=unknown" in line and "running" not in out.replace("not running", "")


def test_status_flags_last_run_and_awaiting_count(w):
    install(w)
    w.ready()
    w.modes("substep", "noprogress-stop")
    assert w.kyloop("planner").returncode == 0
    (w.root / "HOLD").write_text("h")
    (w.run / "HOLD_MERGES").write_text("m")
    (w.run / "awaiting").mkdir(exist_ok=True)
    (w.run / "awaiting" / "AW-1.json").write_text("{}")
    (w.run / "awaiting" / "AW-2.json").write_text("{}")
    line, out = status_line(w, "planner")
    last = w.records()[-1]
    assert ("last_run=" + last["run_id"]) in line and "progressed=false" in line and "stop=yes" in line
    assert "no_progress=1" in line and "breaker=closed" in line
    flags = [x for x in out.splitlines() if x.startswith("flags ")][0]
    assert "HOLD=present" in flags and "HOLD_MERGES=present" in flags and "WAVE_B_DONE_file=absent" in flags
    assert "awaiting_open=2" in flags
    helpers = [x for x in out.splitlines() if x.startswith("helpers ")][0]
    assert "kydispatch.py=unavailable" in helpers and "kyloop.py=present" in helpers
    assert all((m + "=present") in helpers for m in CONTROL_MODULES)
    # the owner's recorded answer to an item is not a second open item
    (w.run / "awaiting" / "AW-1.owner_decision.json").write_text("{}")
    flags = [x for x in status_line(w, "planner")[1].splitlines() if x.startswith("flags ")][0]
    assert "awaiting_open=2" in flags and "owner_decisions=1" in flags
    assert "progressed=n/a" in status_line(w, "dispatcher")[0]


def test_clear_stop_removes_only_that_loops_stop_file_and_never_a_hold(w):
    install(w)
    w.resume()
    keep = [w.stop_file("conductor"), w.stop_file("dispatcher"), w.root / "HOLD", w.run / "HOLD_MERGES"]
    for p in keep + [w.stop_file("planner")]:
        p.write_text("set by someone else")
    before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in keep}
    r = w.kyctl("start", "planner", "--clear-stop")
    assert r.returncode == 0, r.stderr
    assert not w.stop_file("planner").exists()
    assert before == {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in keep}
    # a refused start does not clear the STOP file it was asked to clear
    assert w.kyctl("stop", "planner").returncode == 0
    (w.run / "INSTALL_RECEIPT.json").unlink()
    assert w.kyctl("start", "planner", "--clear-stop").returncode != 0 and w.stop_file("planner").exists()


def test_no_subcommand_ever_touches_hold_or_hold_merges(w):
    holds = [w.root / "HOLD", w.run / "HOLD_MERGES"]
    for p in holds:
        p.write_text("certification hold — owner: SS")
    before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in holds}
    (w.fleet / "kydispatch.py").write_text("# placeholder\n")
    w.resume()
    for args in (("install",), ("status",), ("start", "all"), ("status",), ("restart", "planner"),
                 ("stop", "all"), ("start", "all", "--clear-stop"), ("stop", "all"), ("uninstall",)):
        w.kyctl(*args)
    assert before == {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in holds}


def test_restart_does_not_clear_a_stop_it_did_not_create(w):
    install(w)
    assert w.kyctl("start", "planner").returncode == 0
    assert w.kyctl("restart", "planner").returncode == 0
    assert not w.stop_file("planner").exists() and (w.lc / "loaded" / LABELS["planner"]).exists()
    assert w.kyctl("stop", "planner").returncode == 0      # e.g. the breaker, or the owner
    r = w.kyctl("restart", "planner")
    assert r.returncode != 0 and "stop-file-present" in r.stderr and w.stop_file("planner").exists()
    assert w.kyctl("restart", "planner", "--clear-stop").returncode == 0


def test_uninstall_refuses_loaded_jobs_and_leaves_foreign_plists(w):
    install(w)
    foreign = w.la / "com.madhav.kalayantra.tracker.plist"
    foreign.write_text("not ours")
    assert w.kyctl("start", "planner").returncode == 0
    r = w.kyctl("uninstall")
    assert r.returncode != 0 and "still-loaded" in r.stderr and plist(w, "planner").exists()
    assert w.kyctl("stop", "planner").returncode == 0
    assert w.kyctl("uninstall").returncode == 0
    assert not any(plist(w, loop).exists() for loop in LABELS) and foreign.read_text() == "not ours"
    assert w.stop_file("planner").exists()                  # run state is not uninstall's to remove


def test_kyctl_refuses_root_and_bad_usage(w):
    r = w.kyctl("status", KY_TEST_ASSUME_ROOT="1")
    assert r.returncode != 0 and "root" in r.stderr
    r = w.kyctl("start", "builder")
    assert r.returncode == 64 and "veto" in r.stderr and "stopped and observed here only" in r.stderr
    assert w.kyctl("frobnicate").returncode == 64
    assert w.kyctl("start").returncode == 64


# ───────────────────────────── loop prompts ─────────────────────────────

@pytest.mark.parametrize("name", ["PLANNER_LOOP_v2_4.md", "CONDUCTOR_LOOP_v2_4.md"])
def test_loop_prompts_contract(name):
    text = (FLEET / "prompts" / name).read_text()
    assert len(text) <= 6000, len(text)
    head = text.split("---")[1]
    for key in ("artifact: " + name, "version:", "paired_plan:", "status: DRAFT — pending the B-0c independent review",
                "never_pasted: true"):
        assert key in head, key
    for frag in ("CLAUDE.md → owner decisions → plan → cards → packets", "**Never:**",
                 "honest unknown beats an invented status", "never from memory", "job.json", "checkpoint"):
        assert frag in text, frag
    assert "--bare" not in text
    assert "inbox --wait" not in text or "never" in text.split("inbox --wait")[0][-80:].lower()
    assert "role-state" in text and "controller" in text and "snapshot" in text


# ═════════════════════════ wiring to kyaction / kycommands / kyveto (plan §4a.1-3, §4a.6) ═════════════════════════

C0, C1, C2 = "1" * 40, "2" * 40, "3" * 40
COMMITS, MANIFESTS = (C0, C1, C2), ("a" * 64, "b" * 64, "c" * 64)
E1 = "e" * 64
COCKPIT = {"kind": "cockpit", "session_id": "cockpit-session-1"}
OLD_CTL = "CTL-PLANNER-20260101T000000Z-1"          # a planner controller that no longer runs
OLD_RUN = "PLANNER-20260101T000000Z"


def iso(t):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))


def epoch(text):
    return kyaction.parse_utc(text)


def dead_pid():
    p = subprocess.Popen(["/usr/bin/true"])
    p.wait()
    return p.pid


def lstart(pid):
    return subprocess.run(["/bin/ps", "-o", "lstart=", "-p", str(pid)], capture_output=True, text=True,
                          env={"LC_ALL": "C", "PATH": "/bin:/usr/bin"}).stdout.strip()


def submit(w, role, command, args=None):
    return kycommands.submit(w.run, role, command, args or {}, COCKPIT)


def command(w, cid):
    return kycommands.find(w.run, cid)["doc"]


def stop_and_wait(w, proc, role, timeout=20):
    w.stop_file(role).write_text("stopped by the test")
    assert proc.wait(timeout=timeout) == 0


@pytest.mark.parametrize("role", ["planner", "veto"])
def test_a_missing_control_module_is_a_refused_precondition_not_a_crash(w, role):
    (w.fleet / "kycommands.py").unlink()
    assert w.kyloop(role).returncode == 0                   # never started: nothing raised, nothing respawned
    assert w.awaiting() == [] and not w.stop_file(role).exists()
    w.enable(role)
    r = w.kyloop(role)
    assert r.returncode == 0 and "Traceback" not in r.stderr
    assert "control_module_missing: kycommands.py" in json.dumps(refused(w, role))
    assert w.kyloop("admin", "show", role).returncode == 0  # the admin switch needs none of the modules


# ───────────────────────────── the veto role ─────────────────────────────

def veto_world(w):
    """What the veto handler needs: the authorised bundle (PLANNER_STATE.json), the capacity files it may change."""
    w.write_state({"active": {"next": "B-3"}, "completed_steps": [],
                   "authorised_source": {"source_commit": C1, "entrypoints_digest": E1}})
    (w.run / "KY_WORKERS").write_text("3\n")
    (w.run / "KY_VERIFIERS").write_text("2\n")
    (w.run / "awaiting").mkdir(exist_ok=True)


def propose(w, n=1, expires_in=2, tracker=True, **over):
    """A PENDING_VETO capacity decision exactly as the surrogate records it; → (decision id, deadline epoch)."""
    deadline = int(time.time()) + expires_in
    target = {"kind": "capacity", "builders": 6, "verifiers": 4}
    if tracker:
        target["tracker_decision"] = {"id": "D-41", "outcome": "approved"}
    env = kyveto.Env({"KY_ROOT": str(w.root), "KY_RUN": str(w.run), "KY_FLEET": str(w.fleet)})
    target["fingerprint"] = kyveto.fingerprint(target, env)
    sid, aw = "SD-20261011T220000Z-%d" % n, "AW-20261011T215900Z-item-%d" % n
    line = {"id": sid, "awaiting": aw, "class": "veto", "state": "PENDING_VETO", "decision": "raise capacity",
            "rationale": "nine ready items", "evidence": [], "target": target,
            "authority": {"source_commit": C1, "entrypoints_digest": E1},
            "notification": {"submitted": True, "ts": iso(deadline - 1800)}, "veto_deadline": iso(deadline),
            "effective_at": None, "by": "kalayantra-owner-surrogate", "session": "surrogate-1"}
    line.update(over)
    with open(w.run / "DECISIONS_SURROGATE.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(line) + "\n")
    (w.run / "awaiting" / (aw + ".json")).write_text(json.dumps({"id": aw}))
    return sid, deadline


def decision_lines(w, sid):
    text = (w.run / "DECISIONS_SURROGATE.jsonl").read_text(encoding="utf-8")
    return [d for d in map(json.loads, text.splitlines()) if d["id"] == sid]


def states(w, sid):
    return [d["state"] for d in decision_lines(w, sid)]


def decide_calls(w):
    p = w.root / "fake_ky" / "calls.log"
    return [x for x in p.read_text().splitlines() if x.startswith("decide ")] if p.exists() else []


def veto_summary(w):
    return (w.loop_state("veto") or {}).get("veto") or {}


def capacity(w):
    return (w.run / "KY_WORKERS").read_text(), (w.run / "KY_VERIFIERS").read_text()


def test_veto_role_makes_a_decision_effective_once_at_expiry_and_never_before(w):
    veto_world(w)
    w.enable("veto")
    sid, deadline = propose(w, expires_in=3)
    p = w.popen("veto")
    try:
        assert wait_for(lambda: veto_summary(w).get("pending") == 1)
        ls = w.loop_state("veto")
        assert ls["veto"]["next_deadline"] == iso(deadline) and ls["controller"]["pid"] == p.pid
        assert ls["last_iteration_at"] and ls["waiting"] == "veto_window"
        owner = json.loads((w.run / "locks" / "veto" / "owner.json").read_text())
        assert re.fullmatch(r"CTL-VETO-\d{8}T\d{6}Z-\d+", owner["session_or_run_id"]) and owner["pid"] == p.pid
        while time.time() < deadline - 0.7:                 # it keeps ticking, and nothing becomes effective
            assert states(w, sid) == ["PENDING_VETO"] and decide_calls(w) == [] and capacity(w) == ("3\n", "2\n")
            assert not (w.run / "actions").exists()
            time.sleep(0.1)
        assert veto_summary(w)["ticks"] >= 3
        assert wait_for(lambda: states(w, sid)[-1] == "EXECUTED", timeout=15)
        ticks = veto_summary(w)["ticks"]
        assert wait_for(lambda: veto_summary(w)["ticks"] >= ticks + 3)      # later ticks change nothing
        assert states(w, sid) == ["PENDING_VETO", "EFFECTIVE", "EXECUTED"] and len(decide_calls(w)) == 1
        effective = decision_lines(w, sid)[1]
        assert effective["by"] == "kyveto" and epoch(effective["effective_at"]) >= deadline
        assert effective["session"] == owner["session_or_run_id"]           # --as <controller_id>
        assert capacity(w) == ("6\n", "4\n")
        assert kyaction.load(w.run, sid + ".publish")["actor"] == {
            "role": "veto", "holder_kind": "controller", "controller_id": owner["session_or_run_id"]}
        assert veto_summary(w)["pending"] == 0 and veto_summary(w)["next_deadline"] is None
        stop_and_wait(w, p, "veto")
    finally:
        p.kill()
    assert w.calls() == []                                  # never a model
    assert not (w.run / "locks" / "veto").exists() and w.loop_state("veto")["controller"] is None
    # a restarted controller neither publishes nor executes again
    w.rearm("veto")
    q = w.popen("veto")
    try:
        ticks = veto_summary(w)["ticks"]
        assert wait_for(lambda: veto_summary(w)["ticks"] >= ticks + 2)
        stop_and_wait(w, q, "veto")
    finally:
        q.kill()
    assert len(decide_calls(w)) == 1 and states(w, sid) == ["PENDING_VETO", "EFFECTIVE", "EXECUTED"]


@pytest.mark.parametrize("vetoed", [True, False])
def test_an_owner_veto_wins_the_tick_in_which_the_window_expires(w, vetoed):
    veto_world(w)
    w.enable("veto")
    sid, _ = propose(w, expires_in=-1)                      # already expired at the controller's first tick
    cid = submit(w, "veto", "veto", {"decision_id": sid}) if vetoed else None
    p = w.popen("veto")
    try:
        assert wait_for(lambda: states(w, sid)[-1] in ("VETOED", "EXECUTED"))
        stop_and_wait(w, p, "veto")
    finally:
        p.kill()
    if not vetoed:                                          # the control: without the veto the same decision executes
        assert states(w, sid) == ["PENDING_VETO", "EFFECTIVE", "EXECUTED"] and len(decide_calls(w)) == 1
        return
    assert states(w, sid) == ["PENDING_VETO", "VETOED"]
    assert decide_calls(w) == [] and capacity(w) == ("3\n", "2\n")
    doc = command(w, cid)
    assert doc["state"] == "APPLIED" and doc["applied_by"]["holder_kind"] == "controller"
    assert doc["applied_by"]["controller_id"].startswith("CTL-VETO-") and doc["applied_by"]["role"] == "veto"


def test_a_new_veto_command_wakes_the_controller_long_before_its_poll_period(w):
    veto_world(w)
    w.enable("veto")
    sid, _ = propose(w, expires_in=3600)
    p = w.popen("veto", KY_LOOP_SLEEP_SCALE="0.5")          # poll period 15 s, deadline in an hour
    try:
        assert wait_for(lambda: veto_summary(w).get("pending") == 1)
        time.sleep(1.2)
        assert veto_summary(w)["ticks"] == 1 and states(w, sid) == ["PENDING_VETO"]     # waiting, not polling
        submit(w, "veto", "veto", {"decision_id": sid})
        assert wait_for(lambda: states(w, sid)[-1] == "VETOED", timeout=6)
        assert wait_for(lambda: veto_summary(w)["ticks"] == 2, timeout=3)      # woken once, by the command
        time.sleep(0.6)
        assert veto_summary(w)["ticks"] == 2 and p.poll() is None              # … and waiting again
        stop_and_wait(w, p, "veto")
    finally:
        p.kill()
    assert decide_calls(w) == []


def test_the_veto_controller_wakes_at_the_deadline_itself_not_at_its_poll_period(w):
    veto_world(w)
    w.enable("veto")
    sid, deadline = propose(w, expires_in=3, tracker=False)
    p = w.popen("veto", KY_LOOP_SLEEP_SCALE="0.5")          # poll period 15 s: only the deadline can wake it in time
    try:
        assert wait_for(lambda: veto_summary(w).get("pending") == 1)
        assert wait_for(lambda: states(w, sid)[-1] == "EXECUTED", timeout=deadline - time.time() + 2.5)
        effective = decision_lines(w, sid)[1]
        assert deadline <= epoch(effective["effective_at"]) <= deadline + 2
        assert wait_for(lambda: veto_summary(w)["ticks"] == 2, timeout=3)      # one tick to learn it, one at expiry
        stop_and_wait(w, p, "veto")
    finally:
        p.kill()
    assert veto_summary(w)["ticks"] == 2 and capacity(w) == ("6\n", "4\n")


def test_an_unreconciled_publication_opens_the_veto_breaker_and_does_not_spin(w):
    veto_world(w)
    w.enable("veto")
    (w.root / "fake_ky" / "decide.sleep").write_text("5")   # `ky decide` gives no exit status within the timeout
    sid, _ = propose(w, expires_in=-1)
    r = w.kyloop("veto", KYVETO_KY_TIMEOUT_S="0.5")
    assert r.returncode == 0, r.stderr                      # it stops by itself: launchd does not respawn exit 0

    def attention():
        return [a for a in w.awaiting() if a["id"].endswith("-loop-veto-attention")]

    (aw,) = attention()
    assert aw["blocks"] == "loop" and aw["item"] == "loop.veto" and aw["raised_by"]["role"] == "veto"
    assert "publication_unreconciled" in json.dumps(aw)
    assert_awaiting_schema(aw)
    ls = w.loop_state("veto")
    assert ls["enabled"] is False and ls["breaker"]["open"] is True and "attention" in ls["reason"]
    assert w.cockpit_journal().count("[decision]") == 1
    assert len(decide_calls(w)) == 1 and states(w, sid) == ["PENDING_VETO"] and capacity(w) == ("3\n", "2\n")
    assert kyaction.load(w.run, sid + ".publish")["state"] == "INTENDED"
    ticks = ls["veto"]["ticks"]
    # restarted with nothing changed: refused before any tick — no second owner-wait, notification or `ky decide`
    (w.root / "fake_ky" / "decide.sleep").unlink()
    w.enable("veto")
    r = w.kyloop("veto")
    assert r.returncode == 0 and "evidence unchanged" in r.stderr
    assert len(attention()) == 1 and w.cockpit_journal().count("[decision]") == 1 and len(decide_calls(w)) == 1
    assert w.loop_state("veto")["veto"]["ticks"] == ticks and w.loop_state("veto")["enabled"] is False
    # recorded changed evidence — the cockpit reconciles the publication against the tracker — reopens it
    kyaction.reconcile(w.run, sid + ".publish", lambda record: ("done", {"observed": "tracker readback"}),
                       by="cockpit-session-1")
    w.enable("veto")
    p = w.popen("veto")
    try:
        assert wait_for(lambda: states(w, sid)[-1] == "EXECUTED")
        stop_and_wait(w, p, "veto")
    finally:
        p.kill()
    assert len(decide_calls(w)) == 1 and capacity(w) == ("6\n", "4\n")      # never published a second time
    br = w.loop_state("veto")["breaker"]
    assert br["open"] is False and len(br["history"]) == 1


def test_veto_honours_the_enabled_switch_stop_and_the_global_hold(w):
    veto_world(w)
    sid, _ = propose(w, expires_in=-1, tracker=False)
    r = w.kyloop("veto")                                    # installed, never started: no tick at all
    assert r.returncode == 0 and "not enabled" in r.stderr
    assert states(w, sid) == ["PENDING_VETO"] and veto_summary(w) == {} and w.awaiting() != []
    w.enable("veto")
    w.stop_file("veto").write_text("x")
    assert w.kyloop("veto").returncode == 0
    assert w.loop_state("veto")["enabled"] is False and "STOP" in w.loop_state("veto")["reason"]
    assert states(w, sid) == ["PENDING_VETO"] and veto_summary(w) == {}
    w.rearm("veto")
    (w.root / "HOLD").write_text("held")
    p = w.popen("veto")
    try:
        assert wait_for(lambda: "HOLD" in (veto_summary(w).get("holds") or []))
        ticks = veto_summary(w)["ticks"]
        assert wait_for(lambda: veto_summary(w)["ticks"] >= ticks + 3)      # it keeps ticking under the hold …
        assert states(w, sid) == ["PENDING_VETO"] and p.poll() is None      # … and kyveto keeps the decision pending
        assert w.loop_state("veto")["waiting"] == "hold" and veto_summary(w)["pending"] == 1
        (w.root / "HOLD").unlink()
        assert wait_for(lambda: states(w, sid)[-1] == "EXECUTED")
        stop_and_wait(w, p, "veto")
    finally:
        p.kill()
    assert capacity(w) == ("6\n", "4\n")


def test_a_decision_that_fails_after_its_publication_is_raised_once_and_the_loop_goes_on(w):
    veto_world(w)
    w.enable("veto")
    (w.root / "fake_ky" / "decide.break_capacity").write_text("")       # the executor fails AFTER `ky decide`
    sid, _ = propose(w, expires_in=-1)
    p = w.popen("veto")
    try:
        assert wait_for(lambda: states(w, sid)[-1] == "FAILED")
        ticks = veto_summary(w)["ticks"]
        assert wait_for(lambda: veto_summary(w)["ticks"] >= ticks + 3)
        ls = w.loop_state("veto")
        assert p.poll() is None and ls["enabled"] is True and ls["breaker"]["open"] is False
        raised = [a for a in w.awaiting() if "-veto-attention-sd-" in a["id"]]
        assert len(raised) == 1 and raised[0]["blocks"] == "none" and raised[0]["item"] == sid
        assert_awaiting_schema(raised[0])
        assert w.cockpit_journal().count("[decision]") == 1 and sid in w.cockpit_journal()
        stop_and_wait(w, p, "veto")
    finally:
        p.kill()
    assert decision_lines(w, sid)[-1]["detail"] == {"published": True}


def test_veto_refuses_without_an_install_receipt(w):
    veto_world(w)
    w.enable("veto")
    sid, _ = propose(w, expires_in=-1, tracker=False)
    (w.run / "INSTALL_RECEIPT.json").unlink()
    assert w.kyloop("veto").returncode == 0
    assert "install_receipt_missing" in json.dumps(refused(w, "veto"))
    assert states(w, sid) == ["PENDING_VETO"] and veto_summary(w) == {}


def test_kyctl_starts_stops_and_reports_the_veto_loop(w):
    install(w)
    r = w.kyctl("start", "veto")
    assert r.returncode == 0 and "bootstrapped" in r.stdout, r.stderr
    assert w.loop_state("veto")["enabled"] is True
    line, _ = status_line(w, "veto")
    assert "state=running" in line and "enabled=true" in line and "last_run=n/a" in line and "veto_pending=-" in line
    assert w.kyctl("stop", "veto").returncode == 0
    assert w.stop_file("veto").exists() and w.loop_state("veto")["enabled"] is False
    assert not (w.lc / "loaded" / LABELS["veto"]).exists()
    # … and what the controller itself recorded about its last tick
    veto_world(w)
    w.rearm("veto")
    _, deadline = propose(w, expires_in=3600)
    p = w.popen("veto")
    try:
        assert wait_for(lambda: veto_summary(w).get("pending") == 1)
        line, _ = status_line(w, "veto")
        assert "veto_pending=1" in line and ("veto_next_deadline=" + iso(deadline)) in line
        stop_and_wait(w, p, "veto")
    finally:
        p.kill()


def test_admin_switch_covers_the_veto_loop(w):
    assert json.loads(w.kyloop("admin", "show", "veto").stdout) == {"present": False, "error": "missing"}
    w.enable("veto")
    assert json.loads(w.kyloop("admin", "show", "veto").stdout)["enabled"] is True


# ───────────────────────────── the owner command queue ─────────────────────────────

STATUS_FACTS = {"state", "pid", "last_exit", "loaded", "plist", "enabled", "stop", "controller", "waiting",
                "last_iteration_age_s", "last_run", "progressed", "no_progress", "breaker"}


def test_owner_commands_are_applied_once_in_order_before_the_launch(w):
    w.ready()
    w.modes("stop")
    install(w)
    ids = [submit(w, "planner", "priority", {"item": "N-467"}), submit(w, "planner", "builders", {"n": 4}),
           submit(w, "planner", "verifiers", {"n": 3}), submit(w, "planner", "priority", {"item": "B-4"}),
           submit(w, "planner", "status"), submit(w, "planner", "loops", {"op": "status", "loop": "planner"})]
    r = w.kyloop("planner")
    assert r.returncode == 0, r.stderr
    docs = [command(w, c) for c in ids]
    assert [d["state"] for d in docs] == ["APPLIED"] * 6
    rec = w.records()[0]
    for d in docs:
        assert d["applied_by"] == {"role": "planner", "holder_kind": "controller",
                                   "controller_id": rec["controller_id"]}
        assert_schema("command", d)
    assert [d["applied_at"] for d in docs] == sorted(d["applied_at"] for d in docs)
    # recorded into role state by the controller (in queue order) and handed to the job as part of its snapshot
    directives = w.role_state()["owner_directives"]
    assert [(x["item"], x["command_id"]) for x in directives["priority"]] == [("N-467", ids[0]), ("B-4", ids[3])]
    assert (directives["builders"]["n"], directives["builders"]["command_id"]) == (4, ids[1])
    assert (directives["verifiers"]["n"], directives["verifiers"]["command_id"]) == (3, ids[2])
    snapshot = json.loads((Path(rec["prompt_path"]).parent / "state.snapshot.json").read_text())
    assert snapshot["owner_directives"] == directives and rec["state_violation"] is False
    # `status` answers with the facts `kyctl.sh status` prints for that loop
    for result in (docs[4]["result"], docs[5]["result"]):
        assert set(result["facts"]) >= STATUS_FACTS and result["line"].startswith("planner state=")
        assert result["facts"]["enabled"] == "true" and result["facts"]["plist"] == "installed"
        assert result["facts"]["controller"] == "-" and result["facts"]["breaker"] == "closed"
    # every command went through its own action record, and a restart applies nothing a second time
    assert all(kyaction.load(w.run, "CMD-" + c)["state"] == "DONE" for c in ids)
    before = {c: kycommands.find(w.run, c)["path"].read_bytes() for c in ids}
    w.rearm()
    w.modes("stop")
    assert w.kyloop("planner").returncode == 0
    assert before == {c: kycommands.find(w.run, c)["path"].read_bytes() for c in ids}
    assert w.role_state()["owner_directives"] == directives and w.calls() == [1, 2]


def test_the_conductor_records_directives_into_its_own_role_state(w):
    w.resume()
    w.ready("conductor")
    cid = submit(w, "conductor", "verifiers", {"n": 2})
    assert not (w.run / "CONDUCTOR_STATE.json").exists()
    p = w.popen("conductor")
    try:
        assert wait_for(lambda: command(w, cid)["state"] == "APPLIED")
        assert wait_for(lambda: (w.loop_state("conductor") or {}).get("waiting") == "no_eligible_work")
        time.sleep(0.2)                                     # its own write is not "written outside the controller"
        assert p.poll() is None
        stop_and_wait(w, p, "conductor")
    finally:
        p.kill()
    st = w.role_state("conductor")
    assert st["owner_directives"]["verifiers"]["n"] == 2 and st["completed_steps"] == [] and w.calls() == []
    assert w.awaiting() == []


def test_loops_stop_disables_the_roles_own_loop_and_nothing_is_launched(w):
    w.ready()
    w.default_mode("substep")
    cid = submit(w, "planner", "loops", {"op": "stop", "loop": "planner"})
    r = w.kyloop("planner")
    assert r.returncode == 0 and w.calls() == []
    ls = w.loop_state()
    assert ls["enabled"] is False and cid in ls["reason"] and ls["disabled_by_command"] == cid
    assert command(w, cid)["state"] == "APPLIED" and not w.stop_file().exists() and w.awaiting() == []
    assert not (w.run / "locks" / "planner").exists()


REJECTS = [
    ("other-loop", "loops", {"op": "stop", "loop": "conductor"}, "not_this_roles_loop"),
    ("all-loops", "loops", {"op": "stop", "loop": "all"}, "not_this_roles_loop"),
    ("start", "loops", {"op": "start", "loop": "planner"}, "loops_start_not_applicable"),
    ("approve-window", "approve-window", {"id": "W-1"}, "unsupported_by_planner_role"),
    ("no-such-item", "decide", {"awaiting_id": "AW-20261011T000000Z-nothing-here", "answer": "yes"},
     "awaiting_item_not_open"),
    ("another-roles-item", "decide", {"awaiting_id": "AW-20261011T000000Z-conductor-item", "answer": "yes"},
     "not_this_roles_item"),
]


@pytest.mark.parametrize("label,name,args,reason", REJECTS, ids=[x[0] for x in REJECTS])
def test_a_command_the_role_cannot_carry_out_is_rejected_with_its_reason(w, label, name, args, reason):
    w.ready()
    w.modes("stop")
    (w.run / "awaiting").mkdir()
    (w.run / "awaiting" / "AW-20261011T000000Z-conductor-item.json").write_text(json.dumps(
        {"schema": "ky.awaiting/1", "id": "AW-20261011T000000Z-conductor-item", "item": "N-1", "blocks": "none",
         "raised_by": {"role": "conductor", "session_id": "x", "job_id": None}}))
    cid = submit(w, "planner", name, args)
    assert w.kyloop("planner").returncode == 0
    doc = command(w, cid)
    assert doc["state"] == "REJECTED" and doc["result"]["reason"].startswith(reason), doc
    assert_schema("command", doc)
    assert w.calls() == [1] and "owner_directives" not in w.role_state()        # nothing changed; the loop went on
    assert not list((w.run / "awaiting").glob("*.owner_decision.json"))
    assert kyaction.load(w.run, "CMD-" + cid)["state"] == "FAILED"


def test_a_hand_written_invalid_command_is_rejected_and_does_not_block_the_queue(w):
    w.ready()
    w.modes("stop")
    (w.run / "commands").mkdir()
    bad = {"schema": "ky.command/1", "id": "000001-pause-abc123", "created_at": "2026-10-11T00:00:00Z",
           "from": COCKPIT, "role": "planner", "command": "pause", "args": {}, "state": "QUEUED",
           "applied_by": None, "applied_at": None, "result": None}          # pause is not the planner's to take
    (w.run / "commands" / "20261011T000000Z-000001-pause-abc123.json").write_text(json.dumps(bad))
    later = submit(w, "planner", "priority", {"item": "B-3"})
    assert w.kyloop("planner").returncode == 0
    assert command(w, "000001-pause-abc123")["state"] == "REJECTED"
    assert command(w, "000001-pause-abc123")["result"]["reason"].startswith("invalid_command")
    assert command(w, later)["state"] == "APPLIED" and w.calls() == [1]
    assert kycommands.owner_paused(w.run) is False


def test_handoff_lets_the_current_child_finish_then_checkpoints_and_disables(w):
    w.ready()
    w.default_mode("wait-substep")
    d = w.root / "bin" / "claude.d"
    p = w.popen("planner")
    try:
        assert wait_for((d / "waiting.1").exists)
        cid = submit(w, "planner", "handoff")
        time.sleep(0.4)
        assert command(w, cid)["state"] == "QUEUED" and p.poll() is None    # never applied under a running child
        (d / "release").write_text("")
        assert p.wait(timeout=20) == 0
    finally:
        p.kill()
    assert w.calls() == [1]                                 # the child finished; no second one, though work remains
    rec = w.records()[0]
    assert rec["progressed"] is True and rec["exit_code"] == 0 and rec["accepted"] == ["B-3.s1"]
    st = w.role_state()
    assert st["handoff"]["command_id"] == cid and st["handoff"]["last_run_id"] == rec["run_id"]
    assert [s["id"] for s in st["completed_steps"]] == ["B-3.s1"]
    ls = w.loop_state()
    assert ls["enabled"] is False and "handoff" in ls["reason"] and ls["disabled_by_command"] == cid
    assert command(w, cid)["state"] == "APPLIED"
    journal = (w.run / "JOURNAL_PLANNER.md").read_text().splitlines()
    assert "B-3.s1" in journal[0] and "handoff" in journal[-1] and cid in journal[-1] and len(journal) == 2


def test_owner_decide_is_written_beside_the_item_and_is_changed_evidence_for_the_breaker(w):
    w.ready()
    w.default_mode("noprogress")
    assert w.kyloop("planner").returncode == 0 and w.calls() == [1, 2, 3]
    (aw,) = [a for a in w.awaiting() if a["id"].endswith("-loop-planner-no-progress")]
    item = w.run / "awaiting" / (aw["id"] + ".json")
    answer = w.run / "awaiting" / (aw["id"] + ".owner_decision.json")
    cid = submit(w, "planner", "decide", {"awaiting_id": aw["id"], "answer": "change-and-restart: prompt fixed"})
    w.rearm()
    w.modes("stop")
    assert w.kyloop("planner").returncode == 0
    assert w.calls() == [1, 2, 3, 4]                        # reopened: nothing else changed but the owner's answer
    od = json.loads(answer.read_text())
    assert (od["answer"], od["command_id"], od["awaiting_id"]) == ("change-and-restart: prompt fixed", cid, aw["id"])
    assert od["applied_by"]["role"] == "planner" and od["from"] == COCKPIT and od["awaiting_sha256"] == sha(item)
    assert command(w, cid)["state"] == "APPLIED" and item.exists()          # the item is not removed by the answer
    br = w.loop_state()["breaker"]
    assert br["open"] is False and len(br["history"]) == 1
    assert not list((w.run / "locks").glob("awaiting.*"))
    # a second answer to the same item is refused; the first stands
    cid2 = submit(w, "planner", "decide", {"awaiting_id": aw["id"], "answer": "keep-stopped"})
    w.rearm()
    w.modes("stop")
    assert w.kyloop("planner").returncode == 0
    assert command(w, cid2)["state"] == "REJECTED"
    assert command(w, cid2)["result"]["reason"].startswith("awaiting_item_already_answered")
    assert json.loads(answer.read_text()) == od


def test_a_command_that_cannot_be_settled_yet_keeps_its_place_and_nothing_is_launched_meanwhile(w):
    w.ready()
    w.default_mode("stop")
    (w.run / "awaiting").mkdir()
    aid = "AW-20261011T000000Z-planner-question"
    (w.run / "awaiting" / (aid + ".json")).write_text(json.dumps(
        {"schema": "ky.awaiting/1", "id": aid, "item": "N-1", "blocks": "none",
         "raised_by": {"role": "planner", "session_id": "x", "job_id": None}}))
    busy = kyaction.acquire_lock(w.run, "awaiting." + aid, "surrogate-job-1")     # another live actor is on the item
    first = submit(w, "planner", "decide", {"awaiting_id": aid, "answer": "yes"})
    later = submit(w, "planner", "priority", {"item": "B-4"})
    p = w.popen("planner")
    try:
        assert wait_for(lambda: (w.loop_state() or {}).get("waiting") == "commands_pending")
        time.sleep(0.3)
        assert w.calls() == [] and p.poll() is None
        assert command(w, first)["state"] == "QUEUED" and command(w, later)["state"] == "QUEUED"   # order is kept
        assert kyaction.release_lock(busy)
        assert p.wait(timeout=20) == 0
    finally:
        p.kill()
    assert command(w, first)["state"] == "APPLIED" and command(w, later)["state"] == "APPLIED"
    assert command(w, first)["applied_at"] <= command(w, later)["applied_at"] and w.calls() == [1]


def test_the_last_look_before_a_launch_honours_stop_enabled_commands_hold_and_pause(w, monkeypatch):
    w.ready()
    for name, value in w.env().items():
        monkeypatch.setenv(name, value)
    c = kyloop.Controller("planner")
    c.load_siblings()
    assert c.acquire_lock()
    try:
        c.state_sha = kyloop.sha_file(c.state_path)
        assert c.launch_gate() is None
        cid = submit(w, "planner", "priority", {"item": "B-3"})
        assert c.launch_gate() == "commands_applied" and command(w, cid)["state"] == "APPLIED"
        assert c.launch_gate() is None
        (w.root / "HOLD").write_text("x")
        assert c.launch_gate() == "hold"
        (w.root / "HOLD").unlink()
        submit(w, "campaign", "pause")
        assert c.launch_gate() == "owner_paused"
        submit(w, "campaign", "resume")
        assert c.launch_gate() is None
        kyloop.update_loop_state(w.run, "planner", lambda d: dict(d, enabled=False))
        assert c.launch_gate() == "not_enabled"
        kyloop.update_loop_state(w.run, "planner", lambda d: dict(d, enabled=True))
        w.stop_file().write_text("x")
        assert c.launch_gate() == "stop"
    finally:
        c.release_lock()


def test_a_hold_set_while_the_controller_looks_for_work_withholds_the_launch(w):
    w.resume()
    w.ready("conductor")
    w.default_mode("ack")
    (w.root / "fake_ky" / "inbox.S.json").write_text(json.dumps([{"msg_id": "M1", "detail": "one"}]))
    (w.root / "fake_ky" / "inbox.touch").write_text(str(w.root / "HOLD"))       # set DURING the inbox poll
    p = w.popen("conductor")
    try:
        assert wait_for(lambda: (w.loop_state("conductor") or {}).get("waiting") == "hold")
        time.sleep(0.3)
        assert w.calls() == [] and p.poll() is None         # the batch was eligible, and still nothing was launched
        (w.root / "fake_ky" / "inbox.touch").unlink()
        (w.root / "HOLD").unlink()
        assert wait_for(lambda: w.calls() == [1])
        stop_and_wait(w, p, "conductor")
    finally:
        p.kill()
    assert not list((w.run / "locks").glob("msg.*"))


def test_an_owner_pause_blocks_every_roles_launches_until_an_owner_resume_is_applied(w):
    w.resume()
    w.ready("planner")
    w.ready("conductor")
    w.default_mode("stop")
    (w.root / "fake_ky" / "inbox.S.json").write_text(json.dumps([{"msg_id": "M1", "detail": "one"}]))
    pause = submit(w, "campaign", "pause")

    def paused(*roles):
        return all((w.loop_state(r) or {}).get("waiting") == "owner_paused" for r in roles)

    c, pl = w.popen("conductor"), w.popen("planner")
    try:
        assert wait_for(lambda: command(w, pause)["state"] == "APPLIED")
        by = command(w, pause)["applied_by"]                # the conductor controller, as owner of the campaign role
        assert by["role"] == "campaign" and by["controller_id"].startswith("CTL-CONDUCTOR-")
        assert wait_for(lambda: paused("planner", "conductor"))
        assert not (w.run / "locks" / "campaign").exists()  # taken only for the application
        time.sleep(0.4)
        assert w.calls() == [] and c.poll() is None and pl.poll() is None
        # nothing but an owner resume lifts it: not a hold that comes and goes, not a controller restart
        (w.root / "HOLD").write_text("x")
        assert wait_for(lambda: (w.loop_state("planner") or {}).get("waiting") == "hold")
        (w.root / "HOLD").unlink()
        assert wait_for(lambda: paused("planner", "conductor"))
        pl.send_signal(signal.SIGTERM)
        assert pl.wait(timeout=10) == 143
        pl = w.popen("planner")
        assert wait_for(lambda: (w.loop_state("planner") or {}).get("controller", {}) is not None and paused("planner"))
        time.sleep(0.3)
        assert w.calls() == [] and kycommands.owner_paused(w.run) is True
        resume = submit(w, "campaign", "resume")
        assert c.wait(timeout=20) == 0 and pl.wait(timeout=20) == 0
    finally:
        c.kill()
        pl.kill()
    assert command(w, resume)["state"] == "APPLIED" and kycommands.owner_paused(w.run) is False
    assert sorted(w.calls()) == [1, 2]                      # one job per role, and only after the resume
    assert w.call(1, "mode") == w.call(2, "mode") == "stop\n"


def test_a_queued_owner_pause_is_honoured_before_the_campaign_role_has_applied_it(w):
    w.ready()
    w.default_mode("stop")
    pause = submit(w, "campaign", "pause")                  # no conductor runs in Wave B: nobody applies it
    p = w.popen("planner")
    try:
        assert wait_for(lambda: (w.loop_state() or {}).get("waiting") == "owner_paused")
        time.sleep(0.3)
        assert w.calls() == [] and p.poll() is None
        assert command(w, pause)["state"] == "QUEUED"       # the planner never applies a campaign command
        assert w.loop_state()["pause"]["state"].startswith("pending")
        submit(w, "campaign", "resume")                     # only the owner's own later wish lifts it
        assert p.wait(timeout=20) == 0
    finally:
        p.kill()
    assert w.calls() == [1] and command(w, pause)["state"] == "QUEUED"


def test_a_command_queue_that_cannot_be_read_is_treated_as_a_pause(w):
    w.ready()
    w.default_mode("stop")
    (w.run / "commands").mkdir()
    torn = w.run / "commands" / "20261011T000000Z-000001-pause-abc123.json"
    torn.write_text("{torn")
    p = w.popen("planner")
    try:
        assert wait_for(lambda: (w.loop_state() or {}).get("waiting") == "owner_paused")
        time.sleep(0.3)
        assert w.calls() == [] and p.poll() is None and w.loop_state()["pause"]["state"].startswith("unknown")
        torn.unlink()
        assert p.wait(timeout=20) == 0
    finally:
        p.kill()
    assert w.calls() == [1]


# ───────────────────────────── action records: every launch, and recovery ─────────────────────────────

def old_run(w, rid=OLD_RUN, role="planner", **over):
    """A run record exactly as a controller that no longer runs left it (unfinished unless told otherwise)."""
    rs = w.scratch / "loops" / role / rid
    (rs / "out" / "checkpoints").mkdir(parents=True)
    (w.run / "loops" / role).mkdir(parents=True, exist_ok=True)
    rec = {"schema": "ky.loop_run/1", "run_id": rid, "role": role, "controller_id": OLD_CTL, "pid": None,
           "pgid": None, "process_start": None, "started_at": "2026-01-01T00:00:00Z", "ended_at": None,
           "exit_code": None, "ended_reason": None, "fence": "f" * 32, "work_items": [], "out_dir": str(rs / "out"),
           "stdout_path": str(rs / "stdout.jsonl"), "stderr_path": str(rs / "stderr.log"),
           "deadline_at": "2026-01-01T00:00:01Z", "progress_before": {},
           "state_snapshot_sha256": sha(w.run / ("%s_STATE.json" % role.upper()))}
    rec.update(over)
    (w.run / "loops" / role / (rid + ".json")).write_text(json.dumps(rec))
    return rec


def old_launch(w, rid=OLD_RUN, role="planner", controller=OLD_CTL):
    """The launch action of that run, still INTENDED: the dead controller never recorded an observed result."""
    status, rec = kyaction.begin(
        w.run, "LAUNCH-" + rid, "launch", {"role": role, "holder_kind": "controller", "controller_id": controller},
        {"run_id": rid}, {"run_id": rid, "role": role}, "launch one bounded %s job %s" % (role, rid))
    assert status == "new"
    return rec


def test_every_launch_is_wrapped_in_an_action_record(w):
    w.ready()
    w.modes("substep", "fail", "stop")
    assert w.kyloop("planner").returncode == 0
    recs = w.records()
    assert [x["exit_code"] for x in recs] == [0, 3, 0]
    for rec in recs:
        act = kyaction.load(w.run, "LAUNCH-" + rec["run_id"])
        assert_schema("action", act)
        assert act["kind"] == "launch" and act["state"] == "DONE"
        assert act["actor"] == {"role": "planner", "holder_kind": "controller",
                                "controller_id": rec["controller_id"]}
        assert act["target"]["run_id"] == rec["run_id"] and act["inputs"]["argv"] == rec["argv"]
        assert act["result"]["exit_code"] == rec["exit_code"] and act["result"]["ended_reason"] == "exited"
        assert act["result"]["pid"] == rec["pid"] and "reconciliations" not in act
    assert kyaction.unfinished(w.run) == []


def test_the_launch_action_is_intended_before_the_child_exists_and_records_a_failed_launch(w, monkeypatch):
    w.ready()
    for name, value in w.env().items():
        monkeypatch.setenv(name, value)
    real_popen, seen = subprocess.Popen, {}

    def popen(argv, *args, **kwargs):
        if list(argv)[1:2] != ["-p"]:
            return real_popen(argv, *args, **kwargs)
        (act,) = kyaction.unfinished(w.run)                 # the intent is on disk before anything is started
        seen.update(state=act["state"], kind=act["kind"], same_argv=act["inputs"]["argv"] == list(argv))
        raise OSError("exec format error")

    c = kyloop.Controller("planner")
    c.load_siblings()
    assert c.acquire_lock()
    try:
        c.cfg, errs = c.load_config()
        assert not errs
        os.makedirs(c.loop_dir, exist_ok=True)
        c.state_sha = kyloop.sha_file(c.state_path)
        monkeypatch.setattr(subprocess, "Popen", popen)
        c.run_job([{"id": "step.B-3", "kind": "step", "key": "B-3"}])
    finally:
        monkeypatch.setattr(subprocess, "Popen", real_popen)
        c.release_lock()
    assert seen == {"state": "INTENDED", "kind": "launch", "same_argv": True}
    (rec,) = w.records()
    assert rec["ended_reason"] == "launch_failed" and rec["pid"] is None and rec["ended_at"]
    act = kyaction.load(w.run, "LAUNCH-" + rec["run_id"])
    assert act["state"] == "FAILED" and act["result"]["ended_reason"] == "launch_failed"
    assert w.calls() == []


@pytest.mark.parametrize("how", ["cannot-be-written", "already-exists"])
def test_nothing_is_launched_when_the_intent_cannot_be_recorded(w, monkeypatch, how):
    w.ready()
    for name, value in w.env().items():
        monkeypatch.setenv(name, value)
    c = kyloop.Controller("planner")
    c.load_siblings()
    assert c.acquire_lock()
    try:
        c.cfg, _ = c.load_config()
        os.makedirs(c.loop_dir, exist_ok=True)
        c.state_sha = kyloop.sha_file(c.state_path)

        def begin(*args, **kwargs):
            if how == "already-exists":
                return "unfinished", {}
            raise kyaction.ActionInvalid("the record cannot be written faithfully")

        monkeypatch.setattr(kyaction, "begin", begin)
        with pytest.raises(kyloop.Refusal) as refusal:
            c.run_job([{"id": "step.B-3", "kind": "step", "key": "B-3"}])
    finally:
        c.release_lock()
    assert "launch_action_not_recorded" in str(refusal.value)
    assert w.calls() == [] and w.records() == []            # no child, and no run record without its intent


def test_a_loop_that_is_not_admitted_raises_nothing_even_when_recovery_would_refuse(w):
    w.qualify()
    old_launch(w)                                           # unknown: there is no run record for it
    r = w.kyloop("planner")                                 # installed, never started
    assert r.returncode == 0 and "not admitted" in r.stderr and w.calls() == []
    assert w.awaiting() == [] and not w.stop_file().exists() and w.loop_state().get("enabled") is not True
    w.enable()
    w.stop_file().write_text("stopped by the owner")
    r = w.kyloop("planner")                                 # started once, stopped since
    assert r.returncode == 0 and w.awaiting() == [] and w.calls() == []
    assert w.loop_state()["enabled"] is False and "STOP" in w.loop_state()["reason"]
    w.rearm()
    assert w.kyloop("planner").returncode == 0              # admitted: now the same condition is raised
    assert "action_unreconciled" in json.dumps(refused(w))


@pytest.mark.parametrize("ended,state", [("exited", "DONE"), ("launch_failed", "FAILED")])
def test_an_unfinished_launch_action_is_settled_from_its_complete_run_record(w, ended, state):
    w.ready()
    w.modes("stop")
    exited = ended == "exited"
    old_run(w, pid=dead_pid() if exited else None, ended_at="2026-01-01T00:10:00Z", exit_code=0 if exited else None,
            ended_reason=ended, progressed=False)
    old_launch(w)
    r = w.kyloop("planner")
    assert r.returncode == 0, r.stderr
    act = kyaction.load(w.run, "LAUNCH-" + OLD_RUN)
    assert act["state"] == state and act["reconciliations"][0]["by"].startswith("CTL-PLANNER-")
    assert act["reconciliations"][0]["outcome"] == ("done" if exited else "not_done")
    if exited:
        assert act["result"]["exit_code"] == 0 and act["result"]["ended_reason"] == "exited"
        assert act["result"]["reconciled"] is True
    else:
        assert act["result"]["ended_reason"] == "launch_failed"
    assert w.calls() == [1] and w.awaiting() == []          # reconciled first, then exactly one new launch


def test_a_child_that_is_positively_gone_is_finalised_and_its_action_completed(w):
    w.ready()
    w.modes("stop")
    old_run(w, pid=dead_pid(), pgid=1, process_start="Thu Jan  1 00:00:00 1970")
    old_launch(w)
    assert w.kyloop("planner").returncode == 0
    run = json.loads((w.run / "loops" / "planner" / (OLD_RUN + ".json")).read_text())
    assert run["ended_at"] and run["ended_reason"] == "interrupted" and run["exit_code"] is None
    act = kyaction.load(w.run, "LAUNCH-" + OLD_RUN)
    assert act["state"] == "DONE" and act["result"]["ended_reason"] == "interrupted"
    assert act["result"]["exit_code"] is None               # the exit status was not observed: null, not invented
    assert w.calls() == [1]


UNKNOWN_ACTIONS = ["no-run-record", "no-child-identity", "live-but-unverifiable", "torn-action-file",
                   "run-record-without-action", "another-kind-of-the-previous-controller",
                   "command-no-longer-queued"]


@pytest.mark.parametrize("case", UNKNOWN_ACTIONS)
def test_an_action_that_cannot_be_observed_is_unknown_and_nothing_is_relaunched(w, case):
    w.ready()
    w.default_mode("stop")
    sleeper, checked = None, None
    previous = {"role": "planner", "holder_kind": "controller", "controller_id": OLD_CTL}
    if case == "no-run-record":
        old_launch(w)
        checked = "LAUNCH-" + OLD_RUN
    elif case == "no-child-identity":                       # died between the intent and the recorded pid
        old_run(w)
        old_launch(w)
        checked = "LAUNCH-" + OLD_RUN
    elif case == "live-but-unverifiable":
        sleeper = subprocess.Popen(["/bin/sleep", "60"], start_new_session=True)
        old_run(w, pid=sleeper.pid, pgid=sleeper.pid, process_start="not a start identity")
        old_launch(w)
        checked = "LAUNCH-" + OLD_RUN
    elif case == "torn-action-file":
        (w.run / "actions").mkdir()
        (w.run / "actions" / "ACT-someone-else.json").write_text("{torn")
    elif case == "run-record-without-action":
        old_run(w, pid=dead_pid(), pgid=1, process_start="Thu Jan  1 00:00:00 1970")
    elif case == "another-kind-of-the-previous-controller":
        kyaction.begin(w.run, "ACT-push-1", "push", previous, {"branch": "x"}, {"remote": "origin"}, "push x")
        checked = "ACT-push-1"
    else:
        kyaction.begin(w.run, "CMD-000001-status-abc123", "command:status", previous,
                       {"role": "planner", "command": "status", "args": {}},
                       {"command_id": "000001-status-abc123", "file": "gone.json"}, "command: QUEUED → APPLIED")
        checked = "CMD-000001-status-abc123"
    try:
        r = w.kyloop("planner")
        assert r.returncode == 0, r.stderr
        assert "action_unreconciled" in json.dumps(refused(w))          # one awaiting file, STOP, disabled, no run
        if sleeper is not None:
            assert sleeper.poll() is None                   # a process that cannot be identified is never signalled
        w.rearm()
        assert w.kyloop("planner").returncode == 0          # … and a restart does not retry it either
        refused(w)
        if checked:
            act = kyaction.load(w.run, checked)
            assert act["state"] == "INTENDED" and act["reconciliations"][-1]["outcome"] == "unknown"
    finally:
        if sleeper is not None:
            sleeper.kill()
            sleeper.wait()


def test_actions_are_reconciled_again_before_every_relaunch(w):
    w.ready()
    w.default_mode("leave-action")                          # the child leaves an unfinished side effect behind
    r = w.kyloop("planner")
    assert r.returncode == 0, r.stderr
    assert w.calls() == [1]                                 # no second launch on top of what cannot be observed
    assert "ACT-push-left-behind" in json.dumps(refused_after_runs(w))
    assert kyaction.load(w.run, "ACT-push-left-behind")["reconciliations"][-1]["outcome"] == "unknown"


def test_unfinished_actions_of_other_actors_do_not_block_the_role(w):
    w.ready()
    w.modes("stop")
    kyaction.begin(w.run, "ACT-KW01", "state_migration",
                   {"role": "planner", "holder_kind": "cockpit", "session_id": "cockpit-session-1"}, {}, {}, "x")
    kyaction.begin(w.run, "ACT-launch-J1", "launch",        # the bootstrap supervisor's own launch record
                   {"role": "planner", "holder_kind": "supervisor", "controller_id": "BOOT-1"}, {},
                   {"job_id": "J1"}, "x")
    kyaction.begin(w.run, "LAUNCH-CONDUCTOR-20260101T000000Z", "launch",
                   {"role": "conductor", "holder_kind": "controller",
                    "controller_id": "CTL-CONDUCTOR-20260101T000000Z-1"},
                   {"run_id": "CONDUCTOR-20260101T000000Z"}, {"run_id": "CONDUCTOR-20260101T000000Z"}, "x")
    assert w.kyloop("planner").returncode == 0
    assert w.calls() == [1] and w.awaiting() == []
    left = kyaction.unfinished(w.run)
    assert sorted(a["action_id"] for a in left) == ["ACT-KW01", "ACT-launch-J1", "LAUNCH-CONDUCTOR-20260101T000000Z"]
    assert all("reconciliations" not in a for a in left)


def test_a_command_interrupted_inside_its_handler_is_observed_not_repeated(w):
    """The previous controller died after recording the directive and before settling the command."""
    w.ready()
    w.modes("stop")
    cid = submit(w, "planner", "builders", {"n": 5})
    entry = kycommands.find(w.run, cid)
    kyaction.begin(w.run, "CMD-" + cid, "command:builders",
                   {"role": "planner", "holder_kind": "controller", "controller_id": OLD_CTL},
                   {"role": "planner", "command": "builders", "args": {"n": 5}},
                   {"command_id": cid, "file": entry["path"].name}, "command %s: QUEUED → APPLIED" % cid)
    st = w.role_state()
    st["owner_directives"] = {"builders": {"n": 5, "command_id": cid, "at": "2026-01-01T00:00:00Z"}}
    w.write_state(st)
    assert w.kyloop("planner").returncode == 0
    assert command(w, cid)["state"] == "APPLIED" and w.calls() == [1]
    act = kyaction.load(w.run, "CMD-" + cid)
    assert act["state"] == "DONE" and [x["outcome"] for x in act["reconciliations"]] == ["done"]
    assert w.role_state()["owner_directives"]["builders"]["at"] == "2026-01-01T00:00:00Z"     # not written again


def test_a_command_a_cockpit_began_and_never_settled_is_unknown_to_the_controller(w):
    w.ready()
    w.default_mode("stop")
    cid = submit(w, "planner", "builders", {"n": 5})
    entry = kycommands.find(w.run, cid)
    kyaction.begin(w.run, "CMD-" + cid, "command:builders",
                   {"role": "planner", "holder_kind": "cockpit", "session_id": "cockpit-session-1"},
                   {"role": "planner", "command": "builders", "args": {"n": 5}},
                   {"command_id": cid, "file": entry["path"].name}, "command %s: QUEUED → APPLIED" % cid)
    assert w.kyloop("planner").returncode == 0
    assert "command_unreconciled" in json.dumps(refused(w))             # not repeated blind, nothing launched
    assert command(w, cid)["state"] == "QUEUED" and "owner_directives" not in w.role_state()
    assert kyaction.load(w.run, "CMD-" + cid)["reconciliations"][-1]["outcome"] == "unknown"


# ───────────────────────────── the conductor's activation chain ─────────────────────────────

def chain(w, links, rooted=True):
    """`links` activation records as they are really written. rooted: the un-numbered record (link 0), then
    `links - 1` bundle changes; not rooted (a bundle change made before B-5): `links` numbered records only, the
    first with previous = null. The numbered ones are written by kyveto's own plan_bundle_change executor.
    → the terminal link's manifest digest."""
    if rooted:
        (w.run / "ACTIVATION_RECORD.json").write_text(json.dumps(
            {"final_manifest_digest": MANIFESTS[0], "source_commit": COMMITS[0],
             "authorising_act": {"kind": "owner", "id": "cockpit-session-1"}}))
    else:
        links += 1                              # one bundle change per numbered record
    repo = w.tmp / "repo"
    repo.mkdir(exist_ok=True)
    (repo / "blobs.json").write_text(json.dumps(
        {"%s:%s" % (c, kyveto.OWNER_DECISIONS_PATH): "d" * 40 for c in COMMITS}))
    (w.run / "reviews").mkdir(exist_ok=True)
    env = kyveto.Env({"KY_ROOT": str(w.root), "KY_RUN": str(w.run), "KY_FLEET": str(w.fleet),
                      "KY_GIT": str(FIX_CONTROL / "fake_git"), "KY_SOURCE_REPO": str(repo),
                      "PATH": "/opt/homebrew/bin:/usr/bin:/bin"})
    change = kyveto.REGISTRY["plan_bundle_change"]
    for n in range(1, links):
        review = w.run / "reviews" / ("review-%d.json" % n)
        review.write_text(json.dumps({"verdict": "ACCEPTED", "reviewer_session_id": "astra-%d" % n,
                                      "source_commit": COMMITS[n]}))
        params = {"kind": "plan_bundle_change", "old_commit": COMMITS[n - 1], "new_commit": COMMITS[n],
                  "old_manifest_digest": MANIFESTS[n - 1], "new_manifest_digest": MANIFESTS[n],
                  "review_receipts": [str(review)]}
        ctx = kyveto.Ctx(env, "SD-20261011T220000Z-%d" % n,
                         {"source_commit": COMMITS[n - 1], "entrypoints_digest": E1}, "2026-10-11T22:30:00Z")
        ok, out = change.execute(params, ctx)
        assert ok, out
    return MANIFESTS[links - 1]


def link_path(w, n):
    return w.run / ("ACTIVATION_RECORD.json" if n == 0 else "ACTIVATION_RECORD.%d.json" % n)


def rewrite(path, **changes):
    doc = json.loads(path.read_text())
    doc.update(changes)
    os.chmod(path, 0o644)
    path.write_text(json.dumps(doc))


def hand_link(w, n, **over):
    """A numbered link written by hand that names its predecessor correctly (so only `over` can break it)."""
    prev = link_path(w, n - 1)
    doc = {"schema": "ky.activation_record/1", "n": n, "previous": {"file": prev.name, "sha256": sha(prev)},
           "old_commit": COMMITS[n - 1], "new_commit": COMMITS[n], "old_manifest_digest": MANIFESTS[n - 1],
           "new_manifest_digest": MANIFESTS[n], "review_receipts": [],
           "authorising_act": {"kind": "owner", "id": "by-test"}, "campaign_admission": False,
           "created_at": "2026-10-11T22:00:00Z", "created_by": "by-test"}
    doc.update(over)
    link_path(w, n).write_text(json.dumps(doc))


def conductor_runs_one_batch(w):
    (w.root / "fake_ky" / "inbox.S.json").write_text(json.dumps([{"msg_id": "M1", "detail": "one"}]))
    w.default_mode("ack")
    p = w.popen("conductor")
    try:
        assert wait_for(lambda: w.calls() == [1]
                        and (w.loop_state("conductor") or {}).get("waiting") == "no_eligible_work")
        stop_and_wait(w, p, "conductor")
    finally:
        p.kill()


@pytest.mark.parametrize("links", [1, 2, 3])
def test_conductor_takes_the_approved_digest_from_the_terminal_link_of_a_valid_chain(w, links):
    terminal = chain(w, links)
    w.resume(digest=terminal, activation=None)
    w.ready("conductor")
    conductor_runs_one_batch(w)
    calls = (w.fleet / "kyversion.sh.calls").read_text().splitlines()
    assert set(calls) == {"--expected-manifest-digest " + terminal}
    seen = w.loop_state("conductor")["activation"]
    assert seen["links"] == links and seen["terminal"] == link_path(w, links - 1).name
    assert seen["terminal_sha256"] == sha(link_path(w, links - 1)) and seen["manifest_digest"] == terminal


@pytest.mark.parametrize("links", [1, 2])
def test_conductor_accepts_a_numbered_only_chain_whose_first_link_has_no_predecessor(w, links):
    """A bundle change made before B-5: there is no un-numbered record; link 1 starts the chain."""
    terminal = chain(w, links, rooted=False)
    assert not link_path(w, 0).exists() and json.loads(link_path(w, 1).read_text())["previous"] is None
    assert terminal == MANIFESTS[links]
    w.resume(digest=terminal, activation=None)
    w.ready("conductor")
    conductor_runs_one_batch(w)
    calls = (w.fleet / "kyversion.sh.calls").read_text().splitlines()
    assert set(calls) == {"--expected-manifest-digest " + terminal}
    seen = w.loop_state("conductor")["activation"]
    assert seen["links"] == links and seen["terminal"] == link_path(w, links).name
    assert seen["terminal_sha256"] == sha(link_path(w, links)) and seen["manifest_digest"] == terminal


def _fork(w):
    shutil.copy(link_path(w, 2), w.run / "ACTIVATION_RECORD.2b.json")


def _second_start(w):
    """Link 1 claims to start the chain (previous: null) although the un-numbered record exists."""
    hand_link(w, 1, previous=None)


BROKEN_CHAINS = [
    # label, rooted, links built, how it is broken, the named refusal
    ("predecessor-hash", True, 3, lambda w: rewrite(link_path(w, 1), created_by="edited afterwards"),
     "activation_chain_broken"),
    ("root-rewritten", True, 2, lambda w: rewrite(link_path(w, 0), note="edited afterwards"),
     "activation_chain_broken"),
    ("gap", True, 3, lambda w: link_path(w, 1).unlink(), "activation_chain_broken"),
    ("fork", True, 3, _fork, "activation_chain_forked"),
    ("misnumbered", True, 2, lambda w: rewrite(link_path(w, 1), n=2), "activation_chain_broken"),
    ("terminal-unreadable", True, 2,
     lambda w: (os.chmod(link_path(w, 1), 0o644), link_path(w, 1).write_text("{torn")), "activation_chain_broken"),
    ("link-1-without-predecessor-beside-the-un-numbered-record", True, 1, _second_start, "activation_chain_forked"),
    ("another-predecessor-named", True, 2,
     lambda w: hand_link(w, 2, previous={"file": "ACTIVATION_RECORD.json", "sha256": sha(link_path(w, 0))}),
     "activation_chain_broken"),
    ("discontinuous-commit", True, 1, lambda w: hand_link(w, 1, old_commit=C2), "activation_chain_broken"),
    ("discontinuous-digest", True, 1, lambda w: hand_link(w, 1, old_manifest_digest="f" * 64),
     "activation_chain_broken"),
    ("link-without-digests", True, 1, lambda w: hand_link(w, 1, new_manifest_digest="short"),
     "activation_chain_broken"),
    ("un-numbered-record-removed-from-under-link-1", True, 2, lambda w: link_path(w, 0).unlink(),
     "activation_chain_broken"),
    ("nothing-at-all", True, 1, lambda w: link_path(w, 0).unlink(), "activation_record_missing"),
    ("root-without-digest", True, 1, lambda w: link_path(w, 0).write_text(json.dumps({"source_commit": C0})),
     "activation_record_invalid"),
    # numbered-only chains (no un-numbered record): contiguous from 1, hashes and continuity as everywhere
    ("numbered-only-gap-at-1", False, 2, lambda w: link_path(w, 1).unlink(), "activation_chain_broken"),
    ("numbered-only-gap-in-the-middle", False, 2,
     lambda w: link_path(w, 2).rename(w.run / "ACTIVATION_RECORD.3.json"), "activation_chain_broken"),
    ("numbered-only-predecessor-hash", False, 2, lambda w: rewrite(link_path(w, 1), created_by="edited afterwards"),
     "activation_chain_broken"),
    ("numbered-only-fork", False, 1,
     lambda w: shutil.copy(link_path(w, 1), w.run / "ACTIVATION_RECORD.1b.json"), "activation_chain_forked"),
    ("numbered-only-terminal-unreadable", False, 1,
     lambda w: (os.chmod(link_path(w, 1), 0o644), link_path(w, 1).write_text("{torn")), "activation_chain_broken"),
]


@pytest.mark.parametrize("label,rooted,links,breakit,reason", BROKEN_CHAINS, ids=[x[0] for x in BROKEN_CHAINS])
def test_conductor_refuses_a_broken_forked_or_missing_chain(w, label, rooted, links, breakit, reason):
    terminal = chain(w, links, rooted)
    w.resume(digest=terminal, activation=None)              # the owner approved what the unbroken chain supplied
    w.ready("conductor")
    breakit(w)
    assert w.kyloop("conductor").returncode == 0
    assert reason in json.dumps(refused(w, "conductor"))
    assert not (w.fleet / "kyversion.sh.calls").exists()    # never falls back to verifying the installed manifest


@pytest.mark.parametrize("links,rooted", [(1, True), (2, True), (3, True), (1, False), (2, False)])
def test_conductor_refuses_when_owner_resume_approves_another_digest_than_the_terminal_link(w, links, rooted):
    terminal = chain(w, links, rooted)
    stale = MANIFESTS[MANIFESTS.index(terminal) - 1] if terminal != MANIFESTS[0] else "cd" * 32
    w.resume(digest=stale, activation=None)                 # approved once, superseded since
    w.ready("conductor")
    assert w.kyloop("conductor").returncode == 0
    assert "approved_digest_mismatch" in json.dumps(refused(w, "conductor"))
    assert not (w.fleet / "kyversion.sh.calls").exists()


# ───────────────────────────── qualification context ─────────────────────────────

def test_the_context_is_launchd_only_with_parent_pid_1_and_the_loops_own_label():
    label = "in.marsys.kalayantra.planner"
    assert kyloop.proven_context(label, 1, label) == "launchd"
    assert kyloop.proven_context(label, 1, "in.marsys.kalayantra.conductor") == "shell"
    assert kyloop.proven_context(label, 1, None) == "shell"
    assert kyloop.proven_context(label, 4242, label) == "shell"
    assert kyloop.proven_context(label, True, label) == "shell"
    assert kyloop.proven_context(label, None, label) == "shell"


CONTEXTS = [
    # receipt says, injected detector answer, sleep scale, the named refusal (None = the loop launches)
    ("shell", None, None, None),
    (None, None, None, "qualification_context_missing"),
    ("", None, None, "qualification_context_missing"),
    ("launchd", None, None, "qualification_context_mismatch"),
    ("launchd", "launchd", None, None),
    ("shell", "launchd", None, "qualification_context_mismatch"),
    ("launchd", "launchd", "1", "qualification_context_mismatch"),      # the injection is ignored at scale 1
    ("elsewhere", "elsewhere", None, "qualification_context_mismatch"),  # … and is never anything but the two
]


@pytest.mark.parametrize("receipt,injected,scale,reason", CONTEXTS,
                         ids=["%s-%s-%s" % (c[0], c[1], c[2]) for c in CONTEXTS])
def test_a_qualification_must_have_been_earned_in_the_controllers_proven_context(w, receipt, injected, scale, reason):
    w.enable()
    w.qualify(context=receipt)
    w.default_mode("stop")
    extra = {}
    if injected:
        extra["KY_LOOP_TEST_CONTEXT"] = injected
    if scale:
        extra["KY_LOOP_SLEEP_SCALE"] = scale
    assert w.kyloop("planner", **extra).returncode == 0
    if reason:
        assert reason in json.dumps(refused(w))
    else:
        assert w.calls() == [1] and w.awaiting() == []


def test_expected_qualification_prints_the_context_it_will_require(w):
    def expected(**extra):
        r = w.kyloop("admin", "expected-qualification", "planner", **extra)
        assert r.returncode == 0, r.stderr
        return json.loads(r.stdout)

    exp = expected()
    assert set(exp) == {"role", "model", "receipt_path", "binds", "context"} and exp["context"] == "shell"
    assert expected(KY_LOOP_TEST_CONTEXT="launchd")["context"] == "launchd"
    assert expected(KY_LOOP_TEST_CONTEXT="launchd", KY_LOOP_SLEEP_SCALE="1")["context"] == "shell"
    assert expected(KY_LOOP_TEST_CONTEXT="launchd")["binds"] == exp["binds"]        # the binds do not depend on it


# ───────────────────────────── lock takeover ─────────────────────────────

def hold_lock(w, role, owner):
    d = w.run / "locks" / role
    d.mkdir(parents=True)
    if owner is not None:
        (d / "owner.json").write_text(owner if isinstance(owner, str) else json.dumps(owner))
    return d


def lock_bytes(lock):
    return {p.name: p.read_bytes() for p in sorted(lock.iterdir())}


def test_process_matches_never_reads_unknown_as_gone(monkeypatch):
    me, gone = os.getpid(), dead_pid()
    start = lstart(me)
    assert kyloop.process_matches(me, start) is True
    assert kyloop.process_matches(me, "Thu Jan  1 00:00:00 1970") is False      # positively another process
    assert kyloop.process_matches(gone, start) is False                         # positively no such process
    assert kyloop.process_matches(me, "not a start identity") is None
    assert kyloop.process_matches(me, None) is None
    for bad in (None, "12", True, 0, -5, 1.5):
        assert kyloop.process_matches(bad, start) is None

    def no_ps(*args, **kwargs):
        raise OSError("ps cannot be asked")

    monkeypatch.setattr(kyloop.subprocess, "run", no_ps)
    assert kyloop.process_matches(me, start) is None and kyloop.process_matches(gone, start) is None


UNKNOWN_OWNERS = {
    "null-pid": {"session_or_run_id": "CTL-x", "pid": None, "process_start": None},
    "string-pid": {"session_or_run_id": "CTL-x", "pid": "4242", "process_start": "Thu Jan  1 00:00:00 1970"},
    "bool-pid": {"session_or_run_id": "CTL-x", "pid": True, "process_start": "Thu Jan  1 00:00:00 1970"},
    "zero-pid": {"session_or_run_id": "CTL-x", "pid": 0, "process_start": "Thu Jan  1 00:00:00 1970"},
    "negative-pid": {"session_or_run_id": "CTL-x", "pid": -7, "process_start": "Thu Jan  1 00:00:00 1970"},
    "no-owner-file": None,
    "torn-owner-file": "{torn",
    "owner-not-an-object": "[1, 2]",
}


@pytest.mark.parametrize("case", sorted(UNKNOWN_OWNERS))
def test_a_lock_whose_owner_cannot_be_identified_is_never_taken_over(w, case):
    w.ready()
    w.default_mode("stop")
    lock = hold_lock(w, "planner", UNKNOWN_OWNERS[case])
    old = time.time() - 7200
    os.utime(lock, (old, old))                              # age is not evidence: there is no grace-period takeover
    before = lock_bytes(lock)
    r = w.kyloop("planner")
    assert r.returncode == 0 and w.calls() == [] and "never taken over" in r.stderr
    assert lock.is_dir() and lock_bytes(lock) == before
    ls = w.loop_state()
    assert ls["waiting"] == "role_lock_owner_unknown" and ls["enabled"] is True
    assert w.awaiting() == [] and not w.stop_file().exists()        # a duplicate start never stops what it cannot see


def test_a_lock_is_never_taken_over_when_ps_cannot_be_asked(w, monkeypatch):
    w.ready()
    lock = hold_lock(w, "planner", {"session_or_run_id": "CTL-dead", "pid": dead_pid(), "pgid": 1,
                                    "process_start": "Thu Jan  1 00:00:00 1970"})
    for name, value in w.env().items():
        monkeypatch.setenv(name, value)
    c = kyloop.Controller("planner")
    real_run = subprocess.run

    def no_ps(argv, *args, **kwargs):
        if list(argv)[:1] == ["/bin/ps"]:
            raise OSError("ps cannot be asked")
        return real_run(argv, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", no_ps)
    assert c.acquire_lock() is False and c.lock_refusal["state"] == "unknown" and lock.is_dir()
    monkeypatch.setattr(subprocess, "run", real_run)        # the same lock, once ps answers: positively gone
    assert c.acquire_lock() is True
    c.release_lock()


def test_a_stale_lock_is_removed_only_while_it_is_still_the_lock_that_was_judged_gone(w, monkeypatch):
    """Two contenders both judged the old owner gone; the slower one must not remove the faster one's fresh lock."""
    w.ready()
    for name, value in w.env().items():
        monkeypatch.setenv(name, value)
    c = kyloop.Controller("planner")
    judged = {"session_or_run_id": "CTL-dead", "pid": dead_pid(), "pgid": 1,
              "process_start": "Thu Jan  1 00:00:00 1970"}
    fresh = {"session_or_run_id": "CTL-PLANNER-other", "holder_kind": "controller", "pid": os.getpid(),
             "process_start": lstart(os.getpid())}
    lock = hold_lock(w, "planner", fresh)                   # the faster contender already holds it
    assert c.remove_stale_lock(judged) is False and lock_bytes(lock) == {"owner.json": json.dumps(fresh).encode()}
    (lock / "owner.json").write_text(json.dumps(judged))    # … whereas the judged lock itself is removed
    assert c.remove_stale_lock(judged) is True and not lock.exists()
    assert c.remove_stale_lock(judged) is False             # nothing there: nothing removed, mkdir decides


@pytest.mark.parametrize("case", ["no-such-process", "pid-reused-by-another-process"])
def test_a_lock_whose_owner_process_is_positively_gone_is_taken_over(w, case):
    w.ready()
    w.modes("stop")
    other = subprocess.Popen(["/bin/sleep", "60"]) if case == "pid-reused-by-another-process" else None
    try:
        hold_lock(w, "planner", {"session_or_run_id": "CTL-dead", "pid": other.pid if other else dead_pid(),
                                 "pgid": 1, "process_start": "Thu Jan  1 00:00:00 1970", "acquired_at": "x"})
        r = w.kyloop("planner")
        assert r.returncode == 0 and w.calls() == [1] and "stale lock taken over" in r.stderr
        assert not (w.run / "locks" / "planner").exists()
        assert other is None or other.poll() is None        # the unrelated process under that pid is left alone
    finally:
        if other is not None:
            other.kill()
            other.wait()


def test_a_live_cockpit_holder_is_respected_and_recorded(w):
    w.ready()
    w.default_mode("stop")
    cockpit = subprocess.Popen(["/bin/sleep", "60"])
    try:
        lock = hold_lock(w, "planner", {"session_or_run_id": "cockpit-session-1", "holder_kind": "cockpit",
                                        "pid": cockpit.pid, "process_start": lstart(cockpit.pid)})
        before = lock_bytes(lock)
        r = w.kyloop("planner")
        assert r.returncode == 0 and w.calls() == []
        ls = w.loop_state()
        assert ls["waiting"] == "role_held_by_cockpit"
        assert ls["lock_wait"]["holder"]["session_or_run_id"] == "cockpit-session-1"
        assert ls["enabled"] is True and w.awaiting() == [] and not w.stop_file().exists()
        assert lock_bytes(lock) == before
    finally:
        cockpit.kill()
        cockpit.wait()
    r = w.kyloop("planner")                                 # the cockpit's process is positively gone now
    assert r.returncode == 0 and w.calls() == [1] and "stale lock taken over" in r.stderr
    assert w.loop_state().get("lock_wait") is None


# ───────────────────────────── quota: the real event shape ─────────────────────────────

RESETS_5H, RESETS_7D = 1791800000, 1792200000
REAL_RATE_EVENT = {"type": "rate_limit_event", "rate_limit_info": {
    "status": "allowed", "rateLimitType": "five_hour", "overageStatus": "rejected",
    "overageDisabledReason": "out_of_credits", "isUsingOverage": False,
    "unifiedWindows": {"five_hour": {"utilization": 0.04, "resetsAt": RESETS_5H},
                       "seven_day": {"utilization": 0.31, "resetsAt": RESETS_7D}}}}
SUCCESS = {"type": "result", "subtype": "success", "is_error": False, "result": "done"}


def rate_event(**info):
    ev = copy.deepcopy(REAL_RATE_EVENT)
    ev["rate_limit_info"].update(info)
    return ev


def quota_of(tmp_path, lines, stderr=""):
    out, err = tmp_path / "stdout.jsonl", tmp_path / "stderr.log"
    out.write_text("".join((x if isinstance(x, str) else json.dumps(x)) + "\n" for x in lines))
    err.write_text(stderr)
    return kyloop.detect_quota(str(out), str(err))


def test_the_real_allowed_event_is_not_a_refusal_whatever_its_overage_status(tmp_path):
    q = quota_of(tmp_path, [REAL_RATE_EVENT, SUCCESS])
    assert q["refusal"] is False and q["unrecognised"] == [] and q["resets_at"] is None


@pytest.mark.parametrize("status", ["rejected", "blocked", "limited", "exceeded"])
def test_each_refusing_status_is_a_refusal_and_carries_the_reset_of_its_window(tmp_path, status):
    q = quota_of(tmp_path, [rate_event(status=status)])
    assert (q["refusal"], q["source"], q["status"]) == (True, "rate_limit_event", status)
    assert (q["rate_limit_type"], q["resets_at"]) == ("five_hour", RESETS_5H)
    assert quota_of(tmp_path, [rate_event(status=status, rateLimitType="seven_day")])["resets_at"] == RESETS_7D
    assert quota_of(tmp_path, [rate_event(status=status, resetsAt=1791900000)])["resets_at"] == 1791900000
    assert quota_of(tmp_path, [rate_event(status=status, rateLimitType="opus_weekly")])["resets_at"] is None


@pytest.mark.parametrize("status", ["allowed_warning", "ALLOWED", "Rejected", "", None, 7])
def test_an_unknown_status_is_recorded_verbatim_and_is_not_a_refusal(tmp_path, status):
    q = quota_of(tmp_path, [rate_event(status=status), rate_event(status=status), SUCCESS])
    assert q["refusal"] is False and q["unrecognised"] == [status]


def test_a_final_error_result_with_refusal_text_is_a_refusal_and_prose_is_not(tmp_path):
    prose = {"type": "assistant", "message": {"content": [{"type": "text", "text": "Claude usage limit reached"}]}}
    assert quota_of(tmp_path, [REAL_RATE_EVENT, prose, SUCCESS])["refusal"] is False
    refused_result = {"type": "result", "subtype": "error_during_execution", "is_error": True,
                      "result": "Claude usage limit reached. Your limit will reset at 3pm (Asia/Calcutta)."}
    q = quota_of(tmp_path, [REAL_RATE_EVENT, refused_result])
    assert (q["refusal"], q["source"], q["resets_at"]) == (True, "result_event", None)
    assert quota_of(tmp_path, [dict(refused_result, is_error=False)])["refusal"] is False
    assert quota_of(tmp_path, [dict(refused_result, result="the build failed")])["refusal"] is False


def emit(w, lines, rc=0, checkpoint=False):
    d = w.root / "bin" / "claude.d"
    d.mkdir(exist_ok=True)
    (d / "emit.jsonl").write_text("".join(json.dumps(x) + "\n" for x in lines))
    (d / "emit.rc").write_text(str(rc))
    if checkpoint:
        (d / "emit.checkpoint").write_text("")


def test_a_run_with_the_real_allowed_event_is_not_a_quota_refusal(w):
    w.ready()
    emit(w, [REAL_RATE_EVENT, SUCCESS], checkpoint=True)
    w.modes("emit", "stop")
    assert w.kyloop("planner").returncode == 0
    rec = w.records()[0]
    assert rec["quota_refusal"] is False and rec["progressed"] is True and rec["backoff_minutes"] == 0
    assert rec["rate_limit_status_unrecognised"] == [] and rec["quota"] is None


def test_a_run_with_an_unknown_status_records_it_verbatim_and_is_not_a_refusal(w):
    w.ready()
    emit(w, [rate_event(status="throttled_maybe"), SUCCESS], checkpoint=True)
    w.modes("emit", "stop")
    assert w.kyloop("planner").returncode == 0
    rec = w.records()[0]
    assert rec["quota_refusal"] is False and rec["rate_limit_status_unrecognised"] == ["throttled_maybe"]
    assert rec["progressed"] is True and w.loop_state()["quota"]["level"] == 0


def test_a_refusal_backs_off_until_the_window_resets_when_that_is_sooner_than_the_step(w):
    w.ready()
    resets = int(time.time()) + 2
    emit(w, [rate_event(status="rejected", unifiedWindows={"five_hour": {"utilization": 1.0, "resetsAt": resets}})],
         rc=1)
    w.modes("emit", "stop")
    t0 = time.time()
    r = w.kyloop("planner", KY_LOOP_SLEEP_SCALE="0.02")     # the 5-minute step is 6 s here; the window resets in ~2 s
    assert r.returncode == 0, r.stderr
    first, second = w.records()
    assert first["quota_refusal"] is True and first["backoff_minutes"] == 5
    q = first["quota"]
    assert (q["status"], q["resets_at"], q["backoff_until"], q["backoff_basis"]) == (
        "rejected", resets, resets, "resets_at")
    assert q["backoff_step_until"] > resets                 # both are recorded
    assert epoch(second["started_at"]) >= resets            # not before the reset …
    assert time.time() - t0 < 5.5                           # … and without waiting out the whole step


@pytest.mark.parametrize("offset", [3600, -100])
def test_a_refusal_backs_off_by_the_step_when_the_reset_is_later_or_already_past(w, offset):
    w.ready()
    resets = int(time.time()) + offset
    emit(w, [rate_event(status="rejected", unifiedWindows={"five_hour": {"utilization": 1.0, "resetsAt": resets}})],
         rc=1)
    w.modes("emit", "stop")
    assert w.kyloop("planner").returncode == 0
    first, second = w.records()                             # it resumed after the (scaled) step
    q = first["quota"]
    assert first["quota_refusal"] is True and q["backoff_basis"] == "backoff_step" and q["resets_at"] == resets
    assert q["backoff_until"] == q["backoff_step_until"]
    assert second["quota_refusal"] is False
