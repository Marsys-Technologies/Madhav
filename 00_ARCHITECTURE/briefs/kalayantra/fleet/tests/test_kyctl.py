"""B-0c loop control: kynotify.sh, kyloop.py (deterministic controller), kyctl.sh, launchd
templates and the two loop prompts (relaunch plan v2.7 §4a.1-3, §4a.6, §7, §10, §11, §13; B-0c rework rulings
R1–R3, R5, R6, R8–R10 and the loops review's findings L-01…L-03, N-01…N-10; part 2: L2-a…L2-d, last section).

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
import contextlib
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
             "KY_SCRATCH", "JOB_SCRATCH", "KY_ROLE", "KY_RUN_ID"}
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

    def resume(self, digest=DIGEST, activation=DIGEST, dispatcher=True):
        """The conductor's world: a final receipt, the owner's resume, the activation record — and (unless told
        otherwise) an installed dispatcher that `kyctl.sh start dispatcher` can really start."""
        self.receipt("final")
        (self.run / "OWNER_RESUME.json").write_text(json.dumps({"binding": "N-467", "approved_bundle_digest": digest}))
        if activation is not None:
            (self.run / "ACTIVATION_RECORD.json").write_text(json.dumps({"final_manifest_digest": activation}))
        if dispatcher:
            (self.fleet / "kydispatch.py").write_text("# placeholder: a later deliverable\n")
            r = self.kyctl("install")
            assert r.returncode == 0, r.stderr

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
    for name, sub in (("KY_ROOT", "guard"), ("KY_RUN", "guard/run"), ("KY_FLEET", "guard/fleet_live"),
                      ("FAKE_LAUNCHCTL_DIR", "guard/launchctl"), ("KY_LAUNCHAGENTS_DIR", "guard/LaunchAgents"),
                      ("KY_SCRATCH", "guard/scratch")):
        monkeypatch.setenv(name, str(tmp_path / sub))
    # … nor the real launchctl or a real notification: an ABSOLUTE test double, whatever a test forgets to set
    monkeypatch.setenv("KY_LAUNCHCTL", str(FIX / "fake_launchctl"))
    monkeypatch.setenv("KY_OSASCRIPT", str(FIX / "fake_osascript"))
    monkeypatch.setenv("FAKE_OSASCRIPT_LOG", str(tmp_path / "guard.osascript"))
    monkeypatch.setenv("KY_NOTIFY_DRY", "1")
    assert os.path.isabs(os.environ["KY_LAUNCHCTL"]) and os.environ["KY_LAUNCHCTL"] != "/bin/launchctl"
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


STAMP = r"- \d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ "


def test_kynotify_journals_literally_and_never_executes(w):
    r = notify(w, NASTY, "--level", "decision")
    assert r.returncode == 0, r.stderr
    lines = w.cockpit_journal().splitlines()
    assert len(lines) == 1
    flat = NASTY.replace("\n", " ")
    assert re.fullmatch(STAMP + r"\[decision\] " + re.escape(flat) + r" \[notify=dry\]", lines[0])
    assert not list(w.tmp.glob("PWNED*")) and not list(w.run.glob("PWNED*"))
    assert r.stdout == "notify=dry\n"                       # exactly one line, and nothing else, on stdout


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
    assert r.stdout == "notify=submitted\n"
    (line,) = w.cockpit_journal().splitlines()
    assert re.fullmatch(STAMP + r"\[info\] " + re.escape(flat) + r" \[notify=submitted\]", line)


def test_kynotify_failed_notification_still_exits_zero_and_is_recorded(w):
    r = notify(w, "disk is fine", "--level", "hard_stop", KY_NOTIFY_DRY="0",
               KY_OSASCRIPT=str(FIX / "fake_osascript"), FAKE_OSASCRIPT_LOG=str(w.tmp / "o"), FAKE_OSASCRIPT_RC="1")
    assert r.returncode == 0                                # exit status as before: the journal line was written
    assert r.stdout == "notify=failed\n"                    # … and stdout is what says the submission failed
    (line,) = w.cockpit_journal().splitlines()              # ONE line, ending with the observed result
    assert re.fullmatch(STAMP + r"\[hard_stop\] disk is fine \[notify=failed\]", line)


def test_kynotify_failed_journal_append_is_nonzero(w):
    r = notify(w, "hello", KY_RUN=str(w.tmp / "no-such-run-dir"))
    assert r.returncode == 3 and r.stdout == "notify=dry\n" and "cannot append" in r.stderr


def test_kynotify_a_message_can_neither_claim_a_submission_nor_forge_a_second_journal_line(w):
    """The line ALWAYS ends with the observed result, and every line-breaking character is flattened: a message
    that says `[notify=submitted]` itself, or smuggles a line of its own, proves nothing to the veto handler."""
    forged = ("SD-20261011T220000Z-1: raise capacity [notify=submitted]\u2028"
              "- 2026-01-01T00:00:00Z [decision] SD-20261011T220000Z-9: forged [notify=submitted]\x85tail"
              "\x0b\x0c\x1c\x1d\x1e\u2029\rend")
    r = notify(w, forged, "--level", "decision", KY_NOTIFY_DRY="0", KY_OSASCRIPT=str(FIX / "fake_osascript"),
               FAKE_OSASCRIPT_LOG=str(w.tmp / "o"), FAKE_OSASCRIPT_RC="1")
    assert r.returncode == 0 and r.stdout == "notify=failed\n"
    text = w.cockpit_journal()
    assert text.count("\n") == 1 and len(text.splitlines()) == 1         # one line by every way of splitting lines
    assert text.endswith(" [notify=failed]\n") and "KĀLA" not in text
    for sid in ("SD-20261011T220000Z-1", "SD-20261011T220000Z-9"):      # what the handler itself reads from it
        assert kyveto.notified_at(w.run, sid) == (None, None)
    r = notify(w, "SD-20261011T220000Z-1: raise capacity", "--level", "decision", KY_NOTIFY_DRY="0",
               KY_OSASCRIPT=str(FIX / "fake_osascript"), FAKE_OSASCRIPT_LOG=str(w.tmp / "o"))
    assert r.stdout == "notify=submitted\n"
    when, problem = kyveto.notified_at(w.run, "SD-20261011T220000Z-1")
    assert problem is None and abs(when - time.time()) < 30 and kyveto.notified_at(w.run, "SD-20261011T220000Z-9") == (None, None)


def test_kynotify_keeps_non_ascii_text_intact(w):
    r = notify(w, "KĀLA-YANTRA → “done” ✓")
    assert r.stdout == "notify=dry\n" and "[info] KĀLA-YANTRA → “done” ✓ [notify=dry]" in w.cockpit_journal()


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


WAVE_B_STEPS = ("B-3", "B-4", "B-5")


def wave_b_complete(w, accepted=WAVE_B_STEPS, evidence=None):
    """A finished Wave B as the controller itself would have left it: the steps accepted in the role state, the
    final receipt, VERSIONS.json — and the marker derive_completion() writes from them."""
    w.write_state({"active": {}, "completed_steps": [
        {"id": s, "evidence_sha256": hashlib.sha256(s.encode()).hexdigest(), "note": "accepted"} for s in accepted]})
    w.receipt("final")
    (w.run / "VERSIONS.json").write_text('{"components": []}')
    marker = {"schema": "ky.wave_b_done/1", "derived_at": "2026-10-12T00:00:00Z", "derived_by": "CTL-PLANNER-earlier",
              "steps": list(WAVE_B_STEPS),
              "step_evidence": dict({s: hashlib.sha256(s.encode()).hexdigest() for s in WAVE_B_STEPS}, **(evidence or {})),
              "final_receipt_sha256": sha(w.run / "INSTALL_RECEIPT.json"),
              "versions_sha256": sha(w.run / "VERSIONS.json")}
    (w.run / "WAVE_B_DONE").write_text(json.dumps(marker))
    return marker


def test_wave_b_done_verified_exits_cleanly(w):
    w.ready()
    wave_b_complete(w)
    r = w.kyloop("planner")
    assert r.returncode == 0 and w.calls() == [] and w.awaiting() == []
    assert w.loop_state()["enabled"] is False and "WAVE_B_DONE verified" in w.loop_state()["reason"]
    assert (w.fleet / "kyversion.sh.calls").read_text().splitlines() == [""]      # the normal mode, re-run now


WAVE_B_UNVERIFIED = [
    # what is wrong with an otherwise complete world, and what the refusal names
    ("no-accepted-steps", "B-3 is not accepted"),
    ("one-step-missing", "B-5 is not accepted"),
    ("step-evidence-differs", "evidence for B-4 differs"),
    ("marker-records-no-evidence", "does not record the evidence"),
    ("marker-names-fewer-steps", "does not record the evidence"),
    ("kyversion-fails", "kyversion.sh did not pass (rc=3)"),
    ("kyversion-missing", "kyversion.sh did not pass (rc=None)"),
    ("versions-changed-since", "does not bind the current VERSIONS.json"),
    ("versions-missing", "does not bind the current VERSIONS.json"),
    ("receipt-changed-since", "does not bind the current INSTALL_RECEIPT.json"),
    ("role-state-unreadable", "role state cannot be read"),
]


@pytest.mark.parametrize("case,why", WAVE_B_UNVERIFIED, ids=[c[0] for c in WAVE_B_UNVERIFIED])
def test_a_wave_b_done_marker_is_re_derived_from_the_accepted_evidence_and_kyversion(w, case, why):
    """L3-02: the marker is believed only when completion can be derived again NOW — the receipt hash it repeats is
    a value any writer can compute. Each case breaks ONE thing in the world the test above verifies."""
    w.ready()
    marker = wave_b_complete(w, accepted={"no-accepted-steps": (), "one-step-missing": ("B-3", "B-4")}.get(case, WAVE_B_STEPS),
                             evidence={"B-4": "e" * 64} if case == "step-evidence-differs" else None)
    if case == "marker-records-no-evidence":
        del marker["step_evidence"]
    elif case == "marker-names-fewer-steps":
        marker["steps"] = ["B-3", "B-4"]
    if case.startswith("marker-"):
        (w.run / "WAVE_B_DONE").write_text(json.dumps(marker))
    elif case == "kyversion-fails":
        (w.fleet / "kyversion.sh.rc").write_text("3")
    elif case == "kyversion-missing":
        (w.fleet / "kyversion.sh").unlink()
    elif case == "versions-changed-since":
        (w.run / "VERSIONS.json").write_text('{"components": ["changed"]}')
    elif case == "versions-missing":
        (w.run / "VERSIONS.json").unlink()
    elif case == "receipt-changed-since":
        (w.run / "INSTALL_RECEIPT.json").write_text(json.dumps({"mode": "final", "installed": "again"}))
    elif case == "role-state-unreadable":
        (w.run / "PLANNER_STATE.json").write_text("{not json")
    r = w.kyloop("planner")
    assert r.returncode == 0
    a = json.dumps(refused(w))
    assert "wave_b_done_unverified" in a and why in a, a
    assert "verified" not in (w.loop_state()["reason"] or "").replace("unverified", "")    # not disabled as complete
    assert "Wave B complete" not in r.stderr


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


ENVNAMES_OSASCRIPT = """#!/bin/bash
# An osascript double that shows nothing and records the NAMES (never a value) of the environment it was given.
/usr/bin/env | /usr/bin/cut -d= -f1 | /usr/bin/sort -u > "${FAKE_OSASCRIPT_LOG:?}"
exit 0
"""


@pytest.mark.parametrize("name", CREDENTIAL_NAMES)
def test_a_credential_variable_name_is_one_item_and_a_stop_and_never_its_value(w, name):
    """N4-01 (this test asserted exit 78 before: launchd respawned the controller every ten seconds, with no item
    and no notification). A refused environment takes the one shape of every other refusal — one awaiting item
    naming the variable, STOP, disabled, exit 0 — and the value reaches nothing: not a log, not a file, not a
    helper this controller starts."""
    w.ready()
    w.default_mode("substep")
    spy = w.tmp / "osascript-envnames"
    spy.write_text(ENVNAMES_OSASCRIPT)
    spy.chmod(0o755)
    extra = {name: "s3cr3t-value-never-printed", "KY_NOTIFY_DRY": "0", "KY_OSASCRIPT": str(spy),
             "FAKE_OSASCRIPT_LOG": str(w.tmp / "notifier.envnames")}
    r = w.kyloop("planner", **extra)
    assert r.returncode == 0 and name in r.stderr and "Traceback" not in r.stderr
    item = refused(w)                                       # one awaiting item, STOP, disabled, no model run
    assert ("credential_variable_present: %s" % name) in json.dumps(item)
    assert w.cockpit_journal().count("[decision]") == 1 and item["id"] in w.cockpit_journal()
    assert not (w.run / "locks" / "planner").exists()
    w.rearm()                                               # started again with the variable still there: nothing new
    r2 = w.kyloop("planner", **extra)
    assert r2.returncode == 0 and refused(w) == item and w.cockpit_journal().count("[decision]") == 1
    assert "s3cr3t" not in r.stderr + r.stdout + r2.stderr + r2.stdout
    for path in list(w.run.rglob("*")) + list(w.scratch.rglob("*")) + list(w.fleet.glob("*.calls")):
        if path.is_file():
            assert b"s3cr3t" not in path.read_bytes(), path
    # the helpers the refusing controller ran (here: the notifier) were not given the variable either
    seen = (w.tmp / "notifier.envnames").read_text().split()
    assert "KY_RUN" in seen and name not in seen


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
    (w.fleet / "kylock.sh.rc").write_text("75")             # held by a live holder → this instance exits, runs nothing
    w.rearm()
    w.modes("stop")
    r = w.kyloop("planner")
    assert r.returncode == 0 and w.calls() == [1] and "lock held" in r.stderr
    assert w.awaiting() == [] and not w.stop_file().exists()        # a duplicate start raises and stops nothing


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
                                         ("unassigned", "item_not_assigned"), ("badhash", "evidence_hash_mismatch"),
                                         ("nulpath", "evidence_malformed"),
                                         ("outside", "evidence_outside_allowed_roots"),
                                         ("symlink-out", "evidence_outside_allowed_roots")])
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


def real_orphan(seconds=60):
    """A process as a dead controller leaves its child: its own session and group leader, reparented to launchd
    (so that it is reaped the moment it ends, exactly like a real orphan). → its pid."""
    out = subprocess.run([PY, "-c", "import subprocess as s, sys; print(s.Popen(['/bin/sleep', sys.argv[1]], "
                                    "start_new_session=True, stdin=s.DEVNULL, stdout=s.DEVNULL, stderr=s.DEVNULL).pid)",
                          str(seconds)], capture_output=True, text=True)
    pid = int(out.stdout)
    assert wait_for(lambda: subprocess.run(["/bin/ps", "-o", "ppid=", "-p", str(pid)], capture_output=True,
                                           text=True).stdout.strip() == "1")
    return pid


def pid_gone(pid):
    return subprocess.run(["/bin/ps", "-p", str(pid)], capture_output=True).returncode != 0


def kill_quietly(pid):
    try:
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def test_orphan_child_and_stale_lock_are_reconciled_before_any_replacement(w):
    w.ready()
    w.modes("stop")
    orphan = real_orphan()
    try:
        start = lstart(orphan)
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
        rec = {"run_id": rid, "role": "planner", "pid": orphan, "pgid": orphan, "process_start": start,
               "started_at": "2026-01-01T00:00:00Z", "ended_at": None, "exit_code": None, "fence": "f" * 32,
               "work_items": [], "out_dir": str(rs / "out"), "stdout_path": str(rs / "stdout.jsonl"),
               "stderr_path": str(rs / "stderr.log"), "deadline_at": "2026-01-01T00:00:01Z",
               "state_snapshot_sha256": sha(w.run / "PLANNER_STATE.json"), "progress_before": {}}
        (w.run / "loops" / "planner" / (rid + ".json")).write_text(json.dumps(rec))
        old_launch(w, rid, controller="CTL-dead")          # the dead controller's intent: what recovery starts from
        st = w.loop_state()
        st["expected_child"] = {"run_id": rid, "pid": orphan, "pgid": orphan, "process_start": start}
        (w.run / "loops" / "planner.json").write_text(json.dumps(st))
        r = w.kyloop("planner")
        assert r.returncode == 0, r.stderr
        assert pid_gone(orphan)                             # past its recorded deadline → terminated by identity
    finally:
        kill_quietly(orphan)
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
    # the marker the controller wrote is the one its own re-derivation accepts (L3-02): disabled as complete
    assert "WAVE_B_DONE verified" in w.loop_state()["reason"] and w.awaiting() == []
    assert marker["step_evidence"] == {e["id"]: e["evidence_sha256"] for e in w.role_state()["completed_steps"]}
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


def test_an_owner_wait_the_job_raised_itself_is_not_progress_and_pauses_that_item_only(w):
    """N-02: only a dependency change the run did not author counts. A job that merely writes an owner-wait has
    made no progress — but the item it blocks is still paused, and the loop goes on with the other."""
    w.ready()
    w.modes("await", "stop")
    assert w.kyloop("planner").returncode == 0
    first, second = w.records()
    assert first["accepted"] == [] and first["dependency_changed"] is False and first["progressed"] is False
    assert first["progress_before"]["dependency_fingerprint"] != first["progress_after"]["dependency_fingerprint"]
    assert first["progress_before"]["external_fingerprint"] == first["progress_after"]["external_fingerprint"]
    job = json.loads((Path(second["prompt_path"]).parent / "job.json").read_text())
    assert [i["id"] for i in job["work_items"]] == ["step.B-4"]       # B-3 waits for its owner-wait; B-4 goes on
    assert w.loop_state()["no_progress_count"] == 2                    # the owner-wait run AND the idle `stop` run


def test_a_dependency_changed_by_someone_else_during_a_run_is_progress(w):
    """The control for N-02: the same idle run, during which another actor's owner-wait appears."""
    w.ready()
    w.default_mode("wait-substep")
    d = w.root / "bin" / "claude.d"
    p = w.popen("planner")
    try:
        assert wait_for((d / "waiting.1").exists)
        (w.run / "awaiting").mkdir(exist_ok=True)
        (w.run / "awaiting" / "AW-20261011T000000Z-b-4-from-the-cockpit.json").write_text(json.dumps(
            {"schema": "ky.awaiting/1", "id": "AW-20261011T000000Z-b-4-from-the-cockpit", "item": "B-4",
             "blocks": "item", "raised_by": {"role": "planner", "session_id": "cockpit-session-1", "job_id": None}}))
        w.stop_file().write_text("x")                       # ends the child without a checkpoint (N-10)
        assert p.wait(timeout=20) == 0
    finally:
        p.kill()
    (rec,) = w.records()
    assert rec["accepted"] == [] and rec["dependency_changed"] is True and rec["progressed"] is True
    assert w.loop_state()["no_progress_count"] == 0


IDLE_CLAUDE = """#!/bin/bash
# An idle job: run <n> announces itself (waiting.<n>), waits until the test releases it (release.<n>), asks for
# nothing and exits 0 by itself.
D="$(cd "$(dirname "$0")" && pwd)/claude.d"
mkdir -p "$D"
if [ "${1:-}" = "--version" ]; then echo "2.1.296 (Claude Code)"; exit 0; fi
cat > /dev/null
n=1
while [ -e "$D/waiting.$n" ]; do n=$((n + 1)); done
: > "$D/waiting.$n"
i=0
while [ ! -e "$D/release.$n" ] && [ "$i" -lt 600 ]; do /bin/sleep 0.05; i=$((i + 1)); done
exit 0
"""


def owner_wait(w, slug, item, role, job_id="J-1", blocks="item"):
    (w.run / "awaiting").mkdir(exist_ok=True)
    path = w.run / "awaiting" / ("AW-20261011T000000Z-%s.json" % slug)
    path.write_text(json.dumps({"schema": "ky.awaiting/1", "id": path.stem, "item": item, "blocks": blocks,
                                "raised_by": {"role": role, "session_id": "session-of-%s" % role, "job_id": job_id}}))
    return path


@pytest.mark.parametrize("change", ["appears", "disappears", "both"])
def test_another_roles_owner_wait_for_another_item_is_not_this_loops_progress(w, change):
    """L3-01: the negative of the control above. During an idle planner run a builder's owner-wait for K9-23
    appears and/or one for K9-24 disappears — routine in a live campaign, and nothing the planner waits on. The run
    stays a no-progress run: counted towards the breaker, the quota level not reset."""
    w.claude.write_text(IDLE_CLAUDE)
    w.ready()
    old = owner_wait(w, "k9-24-from-a-builder", "K9-24", "builder")
    ls_path = w.run / "loops" / "planner.json"
    ls_path.write_text(json.dumps(dict(json.loads(ls_path.read_text()), no_progress_count=1,
                                       quota={"level": 2, "notified_level": 2, "not_before": None})))
    d = w.root / "bin" / "claude.d"
    p = w.popen("planner")
    try:
        assert wait_for((d / "waiting.1").exists)
        if change in ("appears", "both"):
            owner_wait(w, "k9-23-from-a-builder", "K9-23", "builder")
        if change in ("disappears", "both"):
            old.unlink()
        (d / "release.1").write_text("")
        assert wait_for((d / "waiting.2").exists)           # the first run is recorded; the loop went on by itself
        ls = w.loop_state()
        w.stop_file().write_text("x")                       # ends the second run, which proves nothing either way
        assert p.wait(timeout=20) == 0
    finally:
        p.kill()
    rec = w.records()[0]
    assert rec["ended_reason"] == "exited" and rec["accepted"] == []
    assert rec["dependency_changed"] is False and rec["progressed"] is False
    assert rec["progress_before"]["item_keys"] == rec["progress_after"]["item_keys"] == ["B-3", "B-4", "B-5"]
    for basis in ("dependency_fingerprint", "external_fingerprint"):
        assert rec["progress_before"][basis] == rec["progress_after"][basis]
    assert ls["no_progress_count"] == 2 and ls["quota"]["level"] == 2      # counted; the quota level not reset


FINGERPRINT_WAITS = [
    # role, the inbox it last saw, (slug, item, raised by, blocks), does it change this role's fingerprint?
    ("planner", (), ("x", "K9-23", "builder", "item"), False),
    ("planner", (), ("x", "msg.M1", "conductor", "item"), False),
    ("planner", (), ("x", "B-44", "builder", "item"), False),             # not B-4, nor a part of it
    ("planner", (), ("x", "loop.conductor", "conductor", "loop"), False),
    ("planner", (), ("x", "B-4", "cockpit", "item"), True),
    ("planner", (), ("x", "step.B-4", "builder", "item"), True),
    ("planner", (), ("x", "B-4.review", "builder", "item"), True),        # what is_blocked() takes for B-4
    ("planner", (), ("x", "loop.planner", "cockpit", "loop"), True),
    ("conductor", ("M1",), ("x", "K9-23", "builder", "item"), False),
    ("conductor", ("M1",), ("x", "msg.M2", "steward", "item"), False),    # no such message is this role's to handle
    ("conductor", ("M1",), ("x", "B-4", "planner", "item"), False),
    ("conductor", ("M1",), ("x", "loop.planner", "planner", "loop"), False),
    ("conductor", ("M1",), ("x", "msg.M1", "steward", "item"), True),
    ("conductor", ("M1",), ("x", "loop.conductor", "cockpit", "loop"), True),
]


@pytest.mark.parametrize("role,inbox,wait,counts", FINGERPRINT_WAITS,
                         ids=["%s-%s-%s" % (f[0], f[2][1], f[3]) for f in FINGERPRINT_WAITS])
def test_only_an_owner_wait_this_role_waits_on_is_a_changed_dependency(w, monkeypatch, role, inbox, wait, counts):
    """L3-01, the rule itself: a wait enters the role's fingerprints exactly when it blocks this loop or an item
    is_blocked() would be asked about — and leaves them again when it is answered away."""
    c = controller_in_process(w, monkeypatch, role)
    c.inbox_keys = set(inbox)
    before = c.accepted_summary()
    assert before["item_keys"] == (["B-3", "B-4", "B-5"] if role == "planner" else list(inbox))
    path = owner_wait(w, *wait[:3], job_id="J-1" if wait[2] != "cockpit" else None, blocks=wait[3])
    during = c.accepted_summary()
    for basis in ("dependency_fingerprint", "external_fingerprint"):
        assert (during[basis] != before[basis]) is counts, basis
    path.unlink()
    assert c.accepted_summary() == before
    # … while it still BLOCKS whatever it names: scoping the progress signal does not unblock anything
    path = owner_wait(w, *wait[:3], blocks=wait[3])
    loop_blocked, blocked, _ = c.awaiting_blocks()
    assert loop_blocked is (wait[3] == "loop" and wait[1] == "loop.%s" % role)
    assert (wait[3] == "item") == bool(blocked)


def test_a_run_is_compared_over_the_items_its_before_was_taken_over(w, monkeypatch):
    """L3-01: `after` uses the keys recorded in `before` — a conductor that sees another inbox when the run ends
    (or one that inherited the run) does not take the difference in keys for a changed dependency."""
    w.resume(dispatcher=False)
    c = controller_in_process(w, monkeypatch, "conductor")
    c.inbox_keys = {"M1"}
    before = c.accepted_summary(c.item_keys([{"id": "msg.M1", "key": "M1"}]))
    owner_wait(w, "m2-held", "msg.M2", "steward")
    c.inbox_keys = {"M1", "M2"}                             # M2 arrived, already blocked, while the run was idle
    assert c.accepted_summary(before["item_keys"]) == before
    assert c.accepted_summary()["external_fingerprint"] != before["external_fingerprint"]   # a later run's own "before"


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
    allowed = {"@KY_ROOT@", "@KY_RUN@", "@KY_FLEET@", "@KY_SCRATCH@", "@HOME@", "@USER@", "@CLAUDE_BIN@", "@SYSTEM_PATH@"}
    for loop, label in LABELS.items():
        text = (FLEET / "launchd" / (label + ".plist")).read_text()
        found = set(re.findall(r"@[A-Z_]+@", text))
        assert found - {"@KY_SOURCE_REPO@"} <= allowed
        assert ("@KY_SOURCE_REPO@" in found) == (loop != "dispatcher")
        assert not re.search(r"(?i)token|secret|password|api_key|DATABASE_URL|PGPASS", text)
        assert "KY_LOOP_SLEEP_SCALE" not in text and "KY_LOOP_TEST_CONTEXT" not in text      # test hooks: never installed


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
    ("veto", "install-receipt-unreadable", lambda w: (w.run / "INSTALL_RECEIPT.json").write_text('{"mode": ["final"]}')),
    ("veto", "install-receipt-unreadable", lambda w: (w.run / "INSTALL_RECEIPT.json").write_text('{"note": "no mode"}')),
    ("veto", "install-receipt-mode", lambda w: w.receipt("rehearsal")),
    ("veto", "kyversion-missing", lambda w: (w.fleet / "kyversion.sh").unlink()),
    ("veto", "kyversion-failed", lambda w: (w.fleet / "kyversion.sh.rc").write_text("3")),
    ("veto", "control-module-missing", lambda w: (w.fleet / "kyveto.py").unlink()),
    ("planner", "control-module-missing", lambda w: (w.fleet / "kyaction.py").unlink()),
    ("conductor", "control-module-missing", lambda w: (w.fleet / "kycommands.py").unlink()),
]


@pytest.mark.parametrize("loop,reason,breakit", GUARDS,
                         ids=["%s:%s:%d" % (g[0], g[1], n) for n, g in enumerate(GUARDS)])
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


def set_expected_child(w, child, loop="planner"):
    kyloop.update_loop_state(w.run, loop, lambda d: dict(d, expected_child=child))


def test_status_reports_expected_child_liveness_and_the_bundle_that_was_verified(w):
    """N-07 (plan §13 "loop healthy", cockpit prompt item 4): never plist or directory presence."""
    install(w)
    line, _ = status_line(w, "planner")
    assert "child=none child_pid=- bundle=unknown bundle_age_s=- test_hooks=-" in line      # never run: nothing recorded
    w.ready()
    w.modes("hang")
    hang = w.root / "bin" / "claude.d" / "hang.pid"
    p = w.popen("planner")
    try:
        assert wait_for(hang.exists)
        child = int(hang.read_text())
        assert wait_for(lambda: (w.loop_state()["expected_child"] or {}).get("pid") == child)
        line, _ = status_line(w, "planner")
        assert ("child=alive child_pid=%d" % child) in line
        assert re.search(r" bundle=bootstrap:receipt-%s bundle_age_s=\d+ " % sha(w.run / "INSTALL_RECEIPT.json")[:12], line)
        assert "waiting=- " in line                         # a child is expected: no waiting state is claimed
        p.kill()                                            # the controller dies; its child is an orphan now
        p.wait()
        assert ("child=alive child_pid=%d" % child) in status_line(w, "planner")[0]
        kill_quietly(child)
        assert wait_for(lambda: "child=gone" in status_line(w, "planner")[0])
    finally:
        p.kill()
    # what cannot be judged is said so, never guessed
    set_expected_child(w, {"run_id": "PLANNER-X", "pid": None, "pending": True})
    assert "child=pending child_pid=-" in status_line(w, "planner")[0]
    set_expected_child(w, {"run_id": "PLANNER-X", "pid": os.getpid(), "pgid": os.getpid(), "process_start": "?"})
    assert "child=unknown" in status_line(w, "planner")[0]
    set_expected_child(w, None)
    left = json.loads((w.run / "locks" / "planner" / "owner.json").read_text())     # the killed controller's lock
    assert left["pid"] == p.pid and left["child"]["pid"] == child
    shutil.rmtree(w.run / "locks" / "planner")
    assert "child=none" in status_line(w, "planner")[0]
    lock = hold_lock(w, "planner", {"session_or_run_id": "CTL-dead", "pid": dead_pid(), "process_start": "x",
                                    "child": "pending"})       # the loop state is silent; the dead owner's lock is not
    assert "child=pending" in status_line(w, "planner")[0]
    shutil.rmtree(lock)
    (w.run / "loops" / "planner.json").write_text("{torn")
    line, _ = status_line(w, "planner")
    assert "enabled=unknown" in line and "child=unknown" in line and "bundle=unknown" in line
    assert "child=none" in status_line(w, "dispatcher")[0]


def test_stop_is_not_confirmed_while_a_recorded_child_of_a_dead_controller_is_alive(w):
    """N-07: a job that is no longer loaded is not the whole loop."""
    install(w)
    assert w.kyctl("start", "planner").returncode == 0
    orphan = real_orphan()
    try:
        set_expected_child(w, {"run_id": "PLANNER-X", "pid": orphan, "pgid": orphan, "process_start": lstart(orphan)})
        r = w.kyctl("stop", "planner")
        assert r.returncode == 1 and "stop-unconfirmed" in r.stderr and "confirmed)" not in r.stdout
        assert ("is alive (pid %d)" % orphan) in r.stderr and w.stop_file("planner").exists()
        assert not (w.lc / "loaded" / LABELS["planner"]).exists() and not pid_gone(orphan)    # reported, never killed
    finally:
        kill_quietly(orphan)
    assert wait_for(lambda: pid_gone(orphan))
    r = w.kyctl("stop", "planner")
    assert r.returncode == 0 and "no recorded child left (confirmed)" in r.stdout
    set_expected_child(w, {"run_id": "PLANNER-X", "pid": None, "pending": True})      # cannot be judged: not confirmed
    r = w.kyctl("stop", "planner")
    assert r.returncode == 1 and "is pending" in r.stderr


def test_the_conductor_status_names_the_manifest_digest_it_verified(w):
    w.resume()
    w.ready("conductor")
    conductor_until_waiting(w)
    line, _ = status_line(w, "conductor")
    assert ("bundle=final:%s " % DIGEST[:12]) in line and "child=none" in line


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
    assert r.returncode == 64 and "veto" in r.stderr and "takes no queued command" not in r.stderr
    # N3-06: the usage text says what the veto controller applies — each command of its own list, and whose `veto` is
    veto_line = next(x for x in r.stderr.splitlines() if "the veto loop" in x)
    assert kyloop.VetoController.COMMANDS == ("status", "loops", "decide")
    for said in ("`status`", "`loops stop|status veto`", "`decide`", "`veto <decision-id>` is settled by the veto handler"):
        assert said in veto_line, said
    assert w.kyctl("frobnicate").returncode == 64
    assert w.kyctl("start").returncode == 64


# ───────────────────────────── loop prompts ─────────────────────────────

@pytest.mark.parametrize("name", ["PLANNER_LOOP_v2_4.md", "CONDUCTOR_LOOP_v2_4.md"])
def test_loop_prompts_contract(name):
    text = (FLEET / "prompts" / name).read_text()
    assert len(text) <= 6000, len(text)
    head = text.split("---")[1]
    for key in ("artifact: " + name, "version:", "paired_plan:", "status: DRAFT — pending the B-0c independent review",
                "never_pasted: true", "changelog: v2.4 (2026-10-12) "):
        assert key in head, key
    for frag in ("CLAUDE.md → owner decisions → plan → cards → packets", "**Never:**",
                 "honest unknown beats an invented status", "never from memory", "job.json", "checkpoint"):
        assert frag in text, frag
    assert "--bare" not in text
    assert "inbox --wait" not in text or "never" in text.split("inbox --wait")[0][-80:].lower()
    assert "role-state" in text and "controller" in text and "snapshot" in text
    assert len(text.encode("utf-8")) <= 6100            # … and not by much more in bytes either
    # R8: the exact commands by which a job records a side effect, and nothing else under run/actions
    role = name.split("_")[0].lower()
    for verb in ("begin", "complete"):
        assert ('| python3 "$KY_FLEET/kyaction.py" %s' % verb) in text, verb
    assert "# or: fail" in text and '"action_id":"JOB-<run_id>-<slug>"' in text
    assert ('"actor":{"role":"%s","controller_id":"<controller_id>"}' % role) in text
    assert "Exit 3: already recorded" in text and "Never write any other file under `run/actions`" in text
    assert "`controller_id`" in text and "evidence_roots" in text
    assert "actions_dir" not in text                    # a job is never pointed at the directory itself
    # the begin line of the prompt is a real, accepted `kyaction.py begin` input once its placeholders are filled
    line = next(x for x in text.splitlines() if x.strip().startswith("printf") and x.rstrip().endswith("begin"))
    doc = json.loads(line.split("'")[3].replace("{…}", "{}").replace("…", "x"))
    assert set(doc) == {"action_id", "kind", "inputs", "target", "intended_transition", "actor"}
    assert set(doc["actor"]) == {"role", "controller_id"} and isinstance(doc["target"].get("item"), str)


def test_the_prompts_begin_command_is_accepted_by_kyaction_and_its_namespace_is_enforced(w):
    """The command the prompts give, run as a job would run it — against the sibling's real CLI."""
    rid = "PLANNER-20260101T000000Z"
    env = {"PATH": "/opt/homebrew/bin:/usr/bin:/bin", "KY_RUN": str(w.run), "KY_RUN_ID": rid, "KY_ROLE": "planner",
           "KY_FLEET": str(w.fleet), "HOME": str(w.home)}

    def cli(verb, doc):
        return subprocess.run(["/bin/bash", "-c", 'printf \'%s\' "$0" | python3 "$KY_FLEET/kyaction.py" ' + verb,
                               json.dumps(doc)], env=env, capture_output=True, text=True)

    begin = {"action_id": "JOB-%s-push-b3" % rid, "kind": "git_push",
             "inputs": {"remote": "origin", "ref": "refs/heads/x", "commit": "c" * 40}, "target": {"item": "step.B-3"},
             "intended_transition": "push x", "actor": {"role": "planner", "controller_id": "CTL-PLANNER-1"}}
    r = cli("begin", begin)
    assert r.returncode == 0 and json.loads(r.stdout)["status"] == "new", r.stderr
    rec = kyaction.load(w.run, begin["action_id"])
    assert rec["actor"] == {"role": "planner", "holder_kind": "job", "controller_id": "CTL-PLANNER-1", "run_id": rid}
    assert kyaction.is_job_record(rec, rid) and rec["state"] == "INTENDED"
    assert cli("begin", begin).returncode == 3              # already recorded: the job must NOT repeat the side effect
    r = cli("complete", {"action_id": begin["action_id"], "result": {"pushed": True}})
    assert r.returncode == 0 and kyaction.load(w.run, begin["action_id"])["state"] == "DONE"
    for bad in ("ACT-push", "JOB-PLANNER-20260101T000001Z-push", "JOB-%s-Push" % rid):
        r = cli("begin", dict(begin, action_id=bad))
        assert r.returncode == 75 and not (w.run / "actions" / (bad + ".json")).exists(), (bad, r.stderr)


# ═════════════════════════ wiring to kyaction / kycommands / kyveto (plan §4a.1-3, §4a.6) ═════════════════════════

C0, C1, C2 = "1" * 40, "2" * 40, "3" * 40
COMMITS = (C0, C1, C2)
E1 = "e" * 64


def manifest_doc(n):
    """The manifest of bundle n (a version manifest as far as its readers look): the five-role entrypoints mapping
    and the source commit it belongs to. The owner-decisions blob is the same in every bundle (a changed one is
    the owner's alone to authorise)."""
    entry = {role: {"path": "docs/%s.md" % role, "git_blob": "%040x" % (16 * n + i + 1)}
             for i, role in enumerate(kyloop.ENTRYPOINT_ROLES)}
    entry["owner_decisions"] = {"path": kyveto.OWNER_DECISIONS_PATH, "git_blob": "d" * 40}
    doc = {"schema": "ky.versions/1", "mode": "final", "approved_source_commit": COMMITS[n], "entrypoints": entry}
    doc["entrypoints_digest"] = entrypoints_digest(doc)
    return doc


def entrypoints_digest(doc):
    return hashlib.sha256(kyloop.canonical({r: {"path": e["path"], "git_blob": e["git_blob"]}
                                            for r, e in doc["entrypoints"].items()})).hexdigest()


def manifest_digest(doc):
    return hashlib.sha256(kyloop.canonical({k: v for k, v in doc.items() if k != "manifest_sha256"})).hexdigest()


MANIFESTS = tuple(manifest_digest(manifest_doc(n)) for n in range(3))


def write_manifest(w, n, name=None):
    """The manifest file of bundle n, as a manifest builder writes it (with its own digest). → its path."""
    doc = manifest_doc(n)
    path = w.run / (name or "manifests/VERSIONS.%d.json" % n)
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(dict(doc, manifest_sha256=MANIFESTS[n]), indent=1))
    return path
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

def veto_world(w, authorised=True):
    """What the veto handler needs: the authorised bundle (PLANNER_STATE.json), the capacity files it may change."""
    state = {"active": {"next": "B-3"}, "completed_steps": []}
    if authorised:
        state["authorised_source"] = {"source_commit": C1, "entrypoints_digest": E1}
    w.write_state(state)
    (w.run / "KY_WORKERS").write_text("3\n")
    (w.run / "KY_VERIFIERS").write_text("2\n")
    (w.run / "awaiting").mkdir(exist_ok=True)


def journal_line(w, sid, at, result="submitted", text="raise capacity"):
    """The line kynotify.sh leaves in the cockpit journal (ruling R3)."""
    with open(w.run / "JOURNAL_COCKPIT.md", "a", encoding="utf-8") as f:
        f.write("- %s [decision] %s: %s [notify=%s]\n" % (iso(at), sid, text, result))


def propose(w, n=1, expires_in=2, tracker=True, seen=True, notified=True, **over):
    """A PENDING_VETO capacity decision exactly as the surrogate records it, with what a real run holds beside it
    by the time its window is judged and that the surrogate does NOT write (ruling R3): kynotify.sh's journal line
    (`notified`) and the handler's own first-seen stamp (`seen`) — both 30 minutes before the deadline, as for a
    decision that was proposed, notified and first seen half an hour ago. → (decision id, deadline epoch)."""
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
    if notified:
        journal_line(w, sid, deadline - 1800)
    if seen:
        stamp = kyveto.stamp_path(w.run, sid)
        stamp.parent.mkdir(exist_ok=True)
        stamp.write_text(json.dumps({"first_seen_at": iso(deadline - 1800),
                                     "proposal_line_sha256": kyveto.proposal_sha(line)}))
    item = {"id": aw}
    if isinstance(target.get("tracker_decision"), dict):   # the item names the tracker decision that would be published
        item["tracker_decision"] = target["tracker_decision"]["id"]
    (w.run / "awaiting" / (aw + ".json")).write_text(json.dumps(item))
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
    assert w.cockpit_journal().count("veto loop stopped") == 1
    assert len(decide_calls(w)) == 1 and states(w, sid) == ["PENDING_VETO"] and capacity(w) == ("3\n", "2\n")
    assert kyaction.load(w.run, sid + ".publish")["state"] == "INTENDED"
    ticks = ls["veto"]["ticks"]
    # restarted with nothing changed: refused before any tick — no second owner-wait, notification or `ky decide`
    (w.root / "fake_ky" / "decide.sleep").unlink()
    w.enable("veto")
    r = w.kyloop("veto")
    assert r.returncode == 0 and "evidence unchanged" in r.stderr
    assert len(attention()) == 1 and w.cockpit_journal().count("veto loop stopped") == 1 and len(decide_calls(w)) == 1
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
        ticks = veto_summary(w).get("ticks", 0)             # the FAILED line is in the log before the tick that
        assert wait_for(lambda: veto_summary(w).get("ticks", 0) >= ticks + 3)   # wrote it is recorded as a tick
        ls = w.loop_state("veto")
        assert p.poll() is None and ls["enabled"] is True and ls["breaker"]["open"] is False
        raised = [a for a in w.awaiting() if "-veto-attention-sd-" in a["id"]]
        assert len(raised) == 1 and raised[0]["blocks"] == "none" and raised[0]["item"] == sid
        assert_awaiting_schema(raised[0])
        assert w.cockpit_journal().count("veto handler: ") == 1 and sid in w.cockpit_journal()
        stop_and_wait(w, p, "veto")
    finally:
        p.kill()
    assert decision_lines(w, sid)[-1]["detail"] == {"published": True}


VETO_ADMISSION = [
    ("receipt-missing", lambda w: (w.run / "INSTALL_RECEIPT.json").unlink(), "install_receipt_missing"),
    ("receipt-torn", lambda w: (w.run / "INSTALL_RECEIPT.json").write_text("{torn"), "install_receipt_unreadable"),
    ("receipt-not-an-object", lambda w: (w.run / "INSTALL_RECEIPT.json").write_text("[]"), "install_receipt_unreadable"),
    ("mode-rehearsal", lambda w: w.receipt("rehearsal"), "install_receipt_mode"),
    ("mode-absent", lambda w: (w.run / "INSTALL_RECEIPT.json").write_text("{}"), "install_receipt_mode"),
    ("mode-not-a-string", lambda w: (w.run / "INSTALL_RECEIPT.json").write_text('{"mode": ["final"]}'),
     "install_receipt_mode"),
    ("kyversion-fails", lambda w: (w.fleet / "kyversion.sh.rc").write_text("3"), "kyversion_failed"),
    ("kyversion-missing", lambda w: (w.fleet / "kyversion.sh").unlink(), "kyversion_missing"),
]


@pytest.mark.parametrize("label,breakit,reason", VETO_ADMISSION, ids=[c[0] for c in VETO_ADMISSION])
def test_the_veto_loop_is_admitted_only_by_a_receipt_of_a_known_mode_and_a_passing_kyversion(w, label, breakit, reason):
    """L-01: this loop publishes delegated decisions and writes activation records. A receipt file that merely
    exists and parses grants nothing."""
    veto_world(w)
    w.enable("veto")
    sid, _ = propose(w, expires_in=-1, tracker=False)       # due at once: it would be executed by the first tick
    breakit(w)
    r = w.kyloop("veto")
    assert r.returncode == 0 and "Traceback" not in r.stderr
    assert reason in json.dumps(refused(w, "veto"))
    assert states(w, sid) == ["PENDING_VETO"] and veto_summary(w) == {} and capacity(w) == ("3\n", "2\n")
    assert not (w.run / "actions" / (sid + ".publish.json")).exists()


@pytest.mark.parametrize("mode,args", [("bootstrap", "--bootstrap"), ("final", "")])
def test_the_veto_loop_verifies_the_bundle_in_the_mode_of_its_receipt_once_per_receipt(w, mode, args):
    veto_world(w)
    w.enable("veto")
    w.receipt(mode)
    p = w.popen("veto")
    try:
        assert wait_for(lambda: veto_summary(w).get("ticks", 0) >= 4)
        calls = (w.fleet / "kyversion.sh.calls").read_text().splitlines()
        assert calls == [args]                              # at start-up — and not again on every tick
        bundle = w.loop_state("veto")["bundle"]
        assert bundle["receipt_mode"] == mode and bundle["receipt_sha256"] == sha(w.run / "INSTALL_RECEIPT.json")
        assert ("bundle=%s:receipt-%s" % (mode, bundle["receipt_sha256"][:12])) in status_line(w, "veto")[0]
        # the receipt changes under the running loop: verified again, in the mode the NEW receipt names
        other = "final" if mode == "bootstrap" else "bootstrap"
        (w.run / "INSTALL_RECEIPT.json").write_text(json.dumps({"mode": other, "note": "reinstalled"}))
        assert wait_for(lambda: len((w.fleet / "kyversion.sh.calls").read_text().splitlines()) == 2)
        assert (w.fleet / "kyversion.sh.calls").read_text().splitlines()[1] == ("" if mode == "bootstrap" else "--bootstrap")
        assert wait_for(lambda: w.loop_state("veto")["bundle"]["receipt_mode"] == other)
        # … and a receipt that stops qualifying stops the loop, by name
        ticks = veto_summary(w)["ticks"]
        w.receipt("rehearsal")
        assert p.wait(timeout=20) == 0
    finally:
        p.kill()
    assert "install_receipt_mode" in json.dumps(refused(w, "veto")) and veto_summary(w)["ticks"] <= ticks + 1


def test_a_kyversion_that_stops_passing_refuses_the_veto_loop_at_the_next_receipt_change(w):
    veto_world(w)
    w.enable("veto")
    p = w.popen("veto")
    try:
        assert wait_for(lambda: veto_summary(w).get("ticks", 0) >= 2)
        (w.fleet / "kyversion.sh.rc").write_text("1")       # the installed files no longer match the manifest
        (w.run / "INSTALL_RECEIPT.json").write_text(json.dumps({"mode": "bootstrap", "note": "touched"}))
        assert p.wait(timeout=20) == 0
    finally:
        p.kill()
    assert "kyversion_failed" in json.dumps(refused(w, "veto"))


# ───────────────────────────── the authority every tick is given (R5) ─────────────────────────────

def authority_of(w, monkeypatch):
    c = controller_in_process(w, monkeypatch, "veto")
    return c.authority()


def test_the_authority_is_the_planner_states_authorised_source_while_no_chain_exists(w, monkeypatch):
    veto_world(w)
    assert authority_of(w, monkeypatch) == ({"source_commit": C1, "entrypoints_digest": E1}, "planner_state")
    for bad in ({"source_commit": C1}, {"source_commit": "short", "entrypoints_digest": E1},
                {"source_commit": C1, "entrypoints_digest": "e" * 40}, "a string", None):
        state = {"active": {}, "completed_steps": []}
        if bad is not None:
            state["authorised_source"] = bad
        w.write_state(state)
        bundle, why = authority_of(w, monkeypatch)
        assert bundle is None and why.startswith("authorised_source_unreadable"), bad
    (w.run / "PLANNER_STATE.json").write_text("{torn")
    assert authority_of(w, monkeypatch)[0] is None


@pytest.mark.parametrize("links,rooted", [(1, True), (2, True), (3, True), (1, False), (2, False)])
def test_the_authority_is_the_terminal_activation_link_and_its_manifests_entrypoints(w, monkeypatch, links, rooted):
    veto_world(w)                                           # the planner state still names the OLD source (C1, E1)
    terminal = chain(w, links, rooted)
    n = MANIFESTS.index(terminal)
    if n == 0:                                              # link 0 names no manifest path: the installed manifest
        write_manifest(w, 0, "VERSIONS.json")
    bundle, source = authority_of(w, monkeypatch)
    assert bundle == {"source_commit": COMMITS[n], "entrypoints_digest": entrypoints_digest(manifest_doc(n))}
    assert source.startswith("activation_chain: " + link_path(w, n if rooted or n else 1).name)
    if n:                                                   # the very digest kyveto bound into the record it wrote
        assert json.loads(link_path(w, n).read_text())["new_manifest"]["entrypoints_digest"] == bundle["entrypoints_digest"]


def _manifest_gone(w):
    for p in (w.run / "manifests").glob("*.json"):
        p.unlink()


def _manifest_edited(w):
    p = w.run / "manifests" / "VERSIONS.2.json"
    doc = json.loads(p.read_text())
    doc["entrypoints"]["plan"]["git_blob"] = "f" * 40      # another plan than the one that was reviewed
    p.write_text(json.dumps(doc))


def _another_manifest_installed(w):
    _manifest_gone(w)
    write_manifest(w, 1, "VERSIONS.json")                   # a real manifest — of another bundle


UNREADABLE_CHAINS = [
    ("manifest-gone", _manifest_gone, "activation_manifest_unreadable"),
    ("manifest-edited", _manifest_edited, "activation_manifest_unreadable"),
    ("only-another-bundles-manifest", _another_manifest_installed, "activation_manifest_unreadable"),
    ("chain-broken", lambda w: rewrite(link_path(w, 1), created_by="edited afterwards"), "activation_chain_broken"),
    ("chain-forked", lambda w: shutil.copy(link_path(w, 2), w.run / "ACTIVATION_RECORD.2b.json"), "activation_chain_forked"),
    ("terminal-torn", lambda w: (os.chmod(link_path(w, 2), 0o644), link_path(w, 2).write_text("{torn")),
     "activation_chain_broken"),
]


@pytest.mark.parametrize("label,breakit,reason", UNREADABLE_CHAINS, ids=[c[0] for c in UNREADABLE_CHAINS])
def test_a_chain_that_cannot_be_read_is_unknown_and_never_falls_back_to_the_planner_state(w, monkeypatch, label, breakit, reason):
    veto_world(w)                                           # a perfectly readable authorised_source is right there
    chain(w, 3)
    breakit(w)
    bundle, why = authority_of(w, monkeypatch)
    assert bundle is None and why.startswith(reason), why


def test_the_tick_is_given_the_authority_explicitly_and_no_clock(w, monkeypatch):
    """The call form (R3, R5): tick(env=…, authorised=<bundle | kyveto.UNKNOWN>, holder=…, holder_kind=…, log=…)."""
    veto_world(w)
    c = controller_in_process(w, monkeypatch, "veto")
    c.load_siblings()
    seen = []

    def tick(env=None, **kwargs):
        seen.append(kwargs)
        return {"decisions": [], "problems": [], "commands": [], "holds": [], "attention": False}

    monkeypatch.setattr(c.kv, "tick", tick)
    c.tick()
    w.write_state({"active": {}, "completed_steps": []})
    c.tick()
    assert [set(k) for k in seen] == [{"authorised", "holder", "holder_kind", "log"}] * 2       # no `now`, ever
    assert seen[0]["authorised"] == {"source_commit": C1, "entrypoints_digest": E1}
    assert seen[1]["authorised"] == kyveto.UNKNOWN and seen[0]["holder"] == c.controller_id
    assert seen[0]["holder_kind"] == "controller"


def authority_items(w):
    return [a for a in w.awaiting() if a["id"].endswith("-loop-veto-authority-unknown")]


def test_decisions_are_held_with_one_attention_item_while_the_authority_is_unknown(w):
    """R5: neither a chain nor an authorised_source can be read → HELD (never failed), ONE attention item, the loop
    keeps ticking, an owner veto is still honoured, and the hold ends by itself."""
    veto_world(w, authorised=False)
    w.enable("veto")
    one, _ = propose(w, 1, expires_in=-1, tracker=False)
    two, _ = propose(w, 2, expires_in=-1, tracker=False)
    p = w.popen("veto")
    try:
        assert wait_for(lambda: len(authority_items(w)) == 1)
        ticks = veto_summary(w)["ticks"]
        assert wait_for(lambda: veto_summary(w)["ticks"] >= ticks + 4)      # it goes on ticking …
        ls = w.loop_state("veto")
        assert p.poll() is None and ls["enabled"] is True and ls["breaker"]["open"] is False
        assert ls["veto"]["authority"]["known"] is False and ls["veto"]["outcomes"] == {"held": 2}
        assert states(w, one) == states(w, two) == ["PENDING_VETO"] and capacity(w) == ("3\n", "2\n")
        (item,) = authority_items(w)                        # … with ONE item for both decisions, raised once
        assert item["blocks"] == "none" and item["item"] == "loop.veto" and "authorised_source_unreadable" in json.dumps(item)
        assert_awaiting_schema(item)
        assert w.cockpit_journal().count("the authorised bundle cannot be established") == 1
        assert not [a for a in w.awaiting() if "-veto-attention-" in a["id"] or a["id"].endswith("-loop-veto-attention")]
        submit(w, "veto", "veto", {"decision_id": two})     # the owner's veto is honoured under the hold
        assert wait_for(lambda: states(w, two)[-1] == "VETOED")
        veto_world(w)                                       # the fenced planner writer records the authorised source
        assert wait_for(lambda: states(w, one)[-1] == "EXECUTED")
        assert w.loop_state("veto")["veto"]["authority"] == {"known": True, "source": "planner_state"}
        stop_and_wait(w, p, "veto")
    finally:
        p.kill()
    assert states(w, one) == ["PENDING_VETO", "EFFECTIVE", "EXECUTED"] and states(w, two) == ["PENDING_VETO", "VETOED"]
    assert len(authority_items(w)) == 1


def test_a_decision_bound_to_a_superseded_source_is_judged_against_the_chains_terminal_link(w):
    """The chain exists, so it is the only authority: a decision the surrogate bound to the old source (C1, E1) —
    which PLANNER_STATE.json still names — has changed authority and fails, by name."""
    veto_world(w)
    chain(w, 3)                                             # the authorised source is C2 now
    w.enable("veto")
    stale, _ = propose(w, 1, expires_in=-1, tracker=False)
    current, _ = propose(w, 2, expires_in=-1, tracker=False,
                         authority={"source_commit": C2, "entrypoints_digest": entrypoints_digest(manifest_doc(2))})
    p = w.popen("veto")
    try:
        assert wait_for(lambda: states(w, stale)[-1] == "FAILED" and states(w, current)[-1] == "EXECUTED")
        assert wait_for(lambda: "veto" in (w.loop_state("veto") or {}))        # the tick's summary follows its lines
        assert w.loop_state("veto")["veto"]["authority"]["source"].startswith("activation_chain: ACTIVATION_RECORD.2.json")
        stop_and_wait(w, p, "veto")
    finally:
        p.kill()
    assert decision_lines(w, stale)[-1]["reason"] == "authority_changed"


# ───────────────────────────── the window is anchored in evidence the surrogate does not write (R3) ─────────────────

def test_a_backdated_proposal_waits_thirty_real_minutes_from_the_handlers_first_sight(w):
    veto_world(w)
    w.enable("veto")
    sid, deadline = propose(w, expires_in=-3600, tracker=False, seen=False)        # "expired an hour ago"
    t0 = int(time.time())
    p = w.popen("veto")
    try:
        assert wait_for(lambda: veto_summary(w).get("pending") == 1)
        stamp = json.loads(kyveto.stamp_path(w.run, sid).read_text())               # stamped by the handler, now
        assert t0 <= epoch(stamp["first_seen_at"]) <= time.time() + 1
        nxt = epoch(veto_summary(w)["next_deadline"])
        assert t0 + 1800 <= nxt <= time.time() + 1801       # not the record's deadline: first sight + 30 minutes
        ticks = veto_summary(w)["ticks"]
        assert wait_for(lambda: veto_summary(w)["ticks"] >= ticks + 3)
        assert states(w, sid) == ["PENDING_VETO"] and capacity(w) == ("3\n", "2\n")
        stop_and_wait(w, p, "veto")
    finally:
        p.kill()


@pytest.mark.parametrize("osascript_rc,claims,reason", [(1, True, "notification_unverified"),
                                                        (0, False, "notification_not_submitted")])
def test_a_decision_whose_notification_was_not_submitted_never_becomes_effective(w, osascript_rc, claims, reason):
    """End to end with the real notifier: its journal line is what the handler reads, not the record's own claim."""
    veto_world(w)
    w.enable("veto")
    sid, _ = propose(w, expires_in=-1, tracker=False, notified=False,
                     notification={"submitted": claims, "ts": iso(time.time() - 1800)})
    r = notify(w, sid + ": raise capacity", "--level", "decision", KY_NOTIFY_DRY="0",
               KY_OSASCRIPT=str(FIX / "fake_osascript"), FAKE_OSASCRIPT_LOG=str(w.tmp / "o"),
               FAKE_OSASCRIPT_RC=str(osascript_rc))
    assert r.stdout == ("notify=failed\n" if osascript_rc else "notify=submitted\n")
    p = w.popen("veto")
    try:
        assert wait_for(lambda: states(w, sid)[-1] == "FAILED")
        raised = lambda: [a for a in w.awaiting() if "-veto-attention-sd-" in a["id"]]
        assert wait_for(lambda: len(raised()) == 1)         # every FAILED outcome reaches the owner, once
        stop_and_wait(w, p, "veto")
    finally:
        p.kill()
    assert decision_lines(w, sid)[-1]["reason"] == reason and capacity(w) == ("3\n", "2\n")
    assert raised()[0]["item"] == sid and w.loop_state("veto")["breaker"]["open"] is False


def test_a_notification_the_real_notifier_submitted_opens_the_window_at_the_journals_time(w):
    veto_world(w)
    w.enable("veto")
    sid, _ = propose(w, expires_in=-1, tracker=False, notified=False)
    t0 = int(time.time())
    r = notify(w, sid + ": raise capacity", "--level", "decision", KY_NOTIFY_DRY="0",
               KY_OSASCRIPT=str(FIX / "fake_osascript"), FAKE_OSASCRIPT_LOG=str(w.tmp / "o"))
    assert r.stdout == "notify=submitted\n"
    p = w.popen("veto")
    try:
        assert wait_for(lambda: veto_summary(w).get("pending") == 1)
        nxt = epoch(veto_summary(w)["next_deadline"])
        assert t0 + 1800 <= nxt <= time.time() + 1801       # 30 real minutes after the journal's timestamp
        assert states(w, sid) == ["PENDING_VETO"]
        stop_and_wait(w, p, "veto")
    finally:
        p.kill()


def test_a_hard_stop_record_is_never_answered_and_is_raised_once(w):
    veto_world(w)
    w.enable("veto")
    sid, _ = propose(w, expires_in=-1, tracker=False, **{"class": "hard_stop"})
    p = w.popen("veto")
    try:
        raised = lambda: [a for a in w.awaiting() if "-veto-attention-sd-" in a["id"]]
        assert wait_for(lambda: len(raised()) == 1)
        ticks = veto_summary(w)["ticks"]
        assert wait_for(lambda: veto_summary(w)["ticks"] >= ticks + 3)
        assert p.poll() is None and len(raised()) == 1 and "hard_stop_never_delegated" in json.dumps(raised()[0])
        stop_and_wait(w, p, "veto")
    finally:
        p.kill()
    assert states(w, sid) == ["PENDING_VETO"] and decide_calls(w) == [] and capacity(w) == ("3\n", "2\n")


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
                "last_iteration_age_s", "last_run", "progressed", "no_progress", "breaker", "child", "child_pid",
                "bundle", "bundle_age_s", "test_hooks"}


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


def test_handoff_ends_the_running_child_persists_its_checkpoints_and_disables(w):
    """N-10: `handoff` = checkpoint now and stop. The controller sees the queued command within its 15 s look (scaled
    here), ends the child's process group, persists what the child had already returned, applies the command."""
    w.ready()
    w.default_mode("substep-hang")                          # one checkpoint request, then it works on for a minute
    hang = w.root / "bin" / "claude.d" / "hang.pid"
    p = w.popen("planner")
    try:
        assert wait_for(hang.exists)
        child = int(hang.read_text())
        cid = submit(w, "planner", "handoff")
        assert p.wait(timeout=20) == 0
    finally:
        p.kill()
    assert pid_gone(child) and w.calls() == [1]             # ended, and no second one although work remains
    rec = w.records()[0]
    assert rec["ended_reason"] == "stopped" and rec["stop_request"]["command_id"] == cid
    assert rec["stop_request"]["source"] == "command" and rec["stop_request"]["command"] == "handoff"
    assert rec["progressed"] is True and rec["accepted"] == ["B-3.s1"]      # "checkpoint now": what it had returned
    assert kyaction.load(w.run, "LAUNCH-" + rec["run_id"])["result"]["ended_reason"] == "stopped"
    st = w.role_state()
    assert st["handoff"]["command_id"] == cid and st["handoff"]["last_run_id"] == rec["run_id"]
    assert [s["id"] for s in st["completed_steps"]] == ["B-3.s1"]
    ls = w.loop_state()
    assert ls["enabled"] is False and "handoff" in ls["reason"] and ls["disabled_by_command"] == cid
    assert ls["expected_child"] is None and command(w, cid)["state"] == "APPLIED"
    journal = (w.run / "JOURNAL_PLANNER.md").read_text().splitlines()
    assert "B-3.s1" in journal[0] and "handoff" in journal[-1] and cid in journal[-1] and len(journal) == 2
    assert not w.stop_file().exists() and w.awaiting() == []


@pytest.mark.parametrize("how", ["stop-file", "loops-stop"])
def test_a_stop_request_is_seen_while_a_child_runs(w, how):
    """N-10: a hand-made STOP file, or a queued `loops stop`, ends a running child within the look period — not
    when the child would have ended by itself (up to its deadline)."""
    w.ready()
    w.default_mode("hang")
    hang = w.root / "bin" / "claude.d" / "hang.pid"
    p = w.popen("planner")
    t0 = None
    try:
        assert wait_for(hang.exists)
        child, t0 = int(hang.read_text()), time.time()
        cid = submit(w, "planner", "loops", {"op": "stop", "loop": "planner"}) if how == "loops-stop" else None
        if how == "stop-file":
            w.stop_file().write_text("stopped by hand")
        assert p.wait(timeout=20) == 0
    finally:
        p.kill()
    assert time.time() - t0 < 10 and pid_gone(child) and w.calls() == [1]
    rec = w.records()[0]
    assert rec["ended_reason"] == "stopped" and rec["ended_at"] and rec["timed_out"] is False
    assert rec["progressed"] is False and w.loop_state()["no_progress_count"] == 0      # cut short by the owner: no verdict
    assert rec["stop_request"]["source"] == ("stop_file" if how == "stop-file" else "command")
    ls = w.loop_state()
    assert ls["enabled"] is False and ls["expected_child"] is None
    if cid:
        assert command(w, cid)["state"] == "APPLIED" and ls["disabled_by_command"] == cid
    assert not (w.run / "locks" / "planner").exists() and w.awaiting() == []


@pytest.mark.parametrize("queued", [("priority", {"item": "B-4"}), ("loops", {"op": "stop", "loop": "conductor"}),
                                    ("loops", {"op": "status", "loop": "planner"})])
def test_other_queued_commands_do_not_end_a_running_child(w, queued):
    w.ready()
    w.default_mode("wait-substep")
    d = w.root / "bin" / "claude.d"
    p = w.popen("planner")
    try:
        assert wait_for((d / "waiting.1").exists)
        cid = submit(w, "planner", *queued)
        time.sleep(0.8)                                     # dozens of looks at the queue
        assert p.poll() is None and command(w, cid)["state"] == "QUEUED"   # never applied under a running child
        w.modes("stop")
        (d / "release").write_text("")
        assert p.wait(timeout=20) == 0
    finally:
        p.kill()
    assert w.records()[0]["ended_reason"] == "exited" and w.records()[0]["stop_request"] is None
    assert command(w, cid)["state"] in ("APPLIED", "REJECTED")


def test_owner_decide_is_written_beside_the_item_and_is_changed_evidence_for_the_breaker(w):
    """(Changed for R15 / L4-01: this test asserted that the answered item STAYS in run/awaiting — "closing it is
    its consumer's act" — which is the defect: nothing ever closed it. The controller that applies the answer now
    closes the item, by moving it to awaiting/done/.)"""
    w.ready()
    w.default_mode("noprogress")
    assert w.kyloop("planner").returncode == 0 and w.calls() == [1, 2, 3]
    (aw,) = [a for a in w.awaiting() if a["id"].endswith("-loop-planner-no-progress")]
    item = w.run / "awaiting" / (aw["id"] + ".json")
    answer = w.run / "awaiting" / (aw["id"] + ".owner_decision.json")
    closed, asked = w.run / "awaiting" / "done" / item.name, item.read_bytes()
    cid = submit(w, "planner", "decide", {"awaiting_id": aw["id"], "answer": "change-and-restart: prompt fixed"})
    w.rearm()
    w.modes("stop")
    assert w.kyloop("planner").returncode == 0
    assert w.calls() == [1, 2, 3, 4]                        # reopened: nothing else changed but the owner's answer
    od = json.loads(answer.read_text())
    assert (od["answer"], od["command_id"], od["awaiting_id"]) == ("change-and-restart: prompt fixed", cid, aw["id"])
    assert od["applied_by"]["role"] == "planner" and od["awaiting_sha256"] == sha(closed)
    assert {k: od["from"].get(k) for k in COCKPIT} == COCKPIT              # who asked, as the queue recorded it
    assert command(w, cid)["state"] == "APPLIED"
    assert not item.exists() and closed.read_bytes() == asked               # closed by the answer: moved, not deleted
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


def left_by_a_dead_process(w, action_id):
    """kyaction records WHO began a record ({pid, process_start}) and treats one whose beginner is alive as still
    in progress. A record a dead controller (or a cockpit that is gone) left carries a process that is positively
    gone — not this test's own."""
    path = w.run / "actions" / (action_id + ".json")
    doc = json.loads(path.read_text())
    doc["process"] = {"pid": dead_pid(), "process_start": "Thu Jan  1 00:00:00 1970"}
    path.write_text(json.dumps(doc))


def old_launch(w, rid=OLD_RUN, role="planner", controller=OLD_CTL):
    """The launch action of that run, still INTENDED: the dead controller never recorded an observed result."""
    status, rec = kyaction.begin(
        w.run, "LAUNCH-" + rid, "launch", {"role": role, "holder_kind": "controller", "controller_id": controller},
        {"run_id": rid}, {"run_id": rid, "role": role}, "launch one bounded %s job %s" % (role, rid))
    assert status == "new"
    left_by_a_dead_process(w, "LAUNCH-" + rid)
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
    gone = dead_pid()
    old_run(w, pid=gone, pgid=gone, process_start="Thu Jan  1 00:00:00 1970")
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
        gone = dead_pid()
        old_run(w, pid=gone, pgid=gone, process_start="Thu Jan  1 00:00:00 1970")
    elif case == "another-kind-of-the-previous-controller":
        kyaction.begin(w.run, "ACT-push-1", "push", previous, {"branch": "x"}, {"remote": "origin"}, "push x")
        checked = "ACT-push-1"
        left_by_a_dead_process(w, checked)
    else:
        kyaction.begin(w.run, "CMD-000001-status-abc123", "command:status", previous,
                       {"role": "planner", "command": "status", "args": {}},
                       {"command_id": "000001-status-abc123", "file": "gone.json"}, "command: QUEUED → APPLIED")
        checked = "CMD-000001-status-abc123"
        left_by_a_dead_process(w, checked)
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


# ───────────────────────────── what a JOB recorded (R8) ─────────────────────────────

def job_action_items(w):
    return [a for a in w.awaiting() if "-job-action-" in a["id"]]


def quarantine_items(w, role="planner"):
    return [a for a in w.awaiting() if ("-loop-%s-quarantine-" % role) in a["id"]]


def test_an_unfinished_job_record_of_unknown_kind_is_one_owner_wait_and_the_loop_goes_on(w):
    w.ready()
    w.modes("job-unknown", "stop")
    r = w.kyloop("planner")
    assert r.returncode == 0, r.stderr
    first, second = w.records()                             # the loop went on: a second job was launched
    aid = "JOB-%s-open-pr" % first["run_id"]
    assert first["job_actions"] == {"quarantined": [], "reconciled": [], "unknown": [aid]}
    assert first["accepted"] == ["B-3.s1"] and first["progressed"] is True
    act = kyaction.load(w.run, aid)
    assert act["state"] == "INTENDED" and act["actor"]["holder_kind"] == "job"
    assert [(rec["outcome"], rec["by"] == first["controller_id"]) for rec in act["reconciliations"]] == [("unknown", True)]
    (item,) = job_action_items(w)                           # ONE awaiting item naming the record
    assert aid in item["question"] and item["blocks"] == "item" and item["item"] == "step.B-3"
    assert item["raised_by"] == {"role": "planner", "session_id": first["controller_id"], "job_id": None}
    assert_awaiting_schema(item)
    job = json.loads((Path(second["prompt_path"]).parent / "job.json").read_text())
    assert [i["id"] for i in job["work_items"]] == ["step.B-4"]        # … with the OTHER item; B-3 waits
    assert not w.stop_file().read_text().startswith("20")              # stopped by the test's `stop` run, not refused
    assert not [a for a in w.awaiting() if a["id"].endswith("-precondition")]
    # a restart neither retries the side effect nor raises the item a second time, and still launches
    w.rearm()
    w.modes("stop")
    assert w.kyloop("planner").returncode == 0
    assert len(w.records()) == 3 and len(job_action_items(w)) == 1
    again = kyaction.load(w.run, aid)
    assert again["state"] == "INTENDED"                     # observed again by the new controller, never repeated
    assert {rec["outcome"] for rec in again["reconciliations"]} == {"unknown"} and len(again["reconciliations"]) == 2
    assert w.cockpit_journal().count(aid) == 1


def test_an_unfinished_job_record_that_names_no_item_blocks_nothing(w):
    w.ready()
    w.modes("job-unknown-noitem", "stop")
    assert w.kyloop("planner").returncode == 0
    first, second = w.records()
    (item,) = job_action_items(w)
    assert item["blocks"] == "none" and item["item"] == "loop.planner"
    job = json.loads((Path(second["prompt_path"]).parent / "job.json").read_text())
    assert [i["id"] for i in job["work_items"]] == ["step.B-3", "step.B-4"]


PUSH = {"remote": "origin", "ref": "refs/heads/kalayantra/fake", "commit": "c" * 40}


@pytest.mark.parametrize("remote,outcome", [("at-the-commit", "done"), ("elsewhere", "not_done"),
                                            ("no-such-ref", "not_done"), ("cannot-be-asked", "unknown")])
def test_an_unfinished_git_push_is_settled_by_ls_remote_equality(w, remote, outcome):
    w.ready()
    w.modes("job-push", "stop")
    (w.wt / ".git").mkdir()
    if remote == "at-the-commit":
        (w.wt / ".git" / "ls-remote.origin").write_text("%s\t%s\n" % (PUSH["commit"], PUSH["ref"]))
    elif remote == "elsewhere":
        (w.wt / ".git" / "ls-remote.origin").write_text("%s\t%s\n%s\trefs/heads/other\n" % ("d" * 40, PUSH["ref"], PUSH["commit"]))
    elif remote == "cannot-be-asked":
        (w.wt / ".git" / "ls-remote.rc").write_text("128")
    assert w.kyloop("planner").returncode == 0
    first = w.records()[0]
    aid = "JOB-%s-push" % first["run_id"]
    act = kyaction.load(w.run, aid)
    assert act["reconciliations"][0]["outcome"] == outcome
    assert (w.wt / ".git" / "ls-remote.calls").read_text().splitlines()[0] == \
        "-C %s ls-remote origin %s" % (w.wt, PUSH["ref"])
    assert len(w.records()) == 2                            # whatever it was, the loop went on
    if outcome == "done":
        assert act["state"] == "DONE" and act["result"]["commit"] == PUSH["commit"] and act["result"]["reconciled"] is True
        assert first["job_actions"]["reconciled"] == [aid] and job_action_items(w) == []
    elif outcome == "not_done":                             # positively not on the remote: FAILED, never retried here
        assert act["state"] == "FAILED" and act["result"]["intended"] == PUSH["commit"]
        assert act["result"]["observed"] == ("d" * 40 if remote == "elsewhere" else None)
        assert job_action_items(w) == []
    else:
        assert act["state"] == "INTENDED" and first["job_actions"]["unknown"] == [aid]
        assert len(job_action_items(w)) == 1


@pytest.mark.parametrize("field,value", [("remote", "ext::sh -c id"), ("remote", "https://example.invalid/x.git"),
                                         ("remote", "-oProxyCommand=id"), ("ref", "refs/heads/../../x"),
                                         ("ref", "--upload-pack=id"), ("commit", "c" * 39), ("repo", "/etc")])
def test_the_git_push_observer_asks_git_only_about_a_named_remote_of_the_role_worktree(w, monkeypatch, field, value):
    """What a job wrote is data: a URL, an option or another repository is never handed to git."""
    w.ready()
    (w.wt / ".git").mkdir()
    for name, val in w.env().items():
        monkeypatch.setenv(name, val)
    c = kyloop.Controller("planner")
    answer = c.observe_git_push({"inputs": dict(PUSH, **{field: value}), "target": {}})
    assert answer[0] == "unknown" and not (w.wt / ".git" / "ls-remote.calls").exists()
    assert c.observe_git_push({"inputs": dict(PUSH), "target": {}})[0] == "not_done"       # the control: git was asked


def test_a_job_record_the_job_finished_itself_needs_nothing(w):
    w.ready()
    w.modes("job-finished", "stop")
    assert w.kyloop("planner").returncode == 0
    first = w.records()[0]
    assert first["job_actions"] == {"quarantined": [], "reconciled": [], "unknown": []}
    assert kyaction.load(w.run, "JOB-%s-push" % first["run_id"])["state"] == "DONE" and w.awaiting() == []


def test_malformed_job_authored_files_are_quarantined_and_never_stop_the_loop(w):
    w.ready()
    w.modes("job-malformed", "stop")
    kyaction.begin(w.run, "ACT-KW01", "state_migration",    # another actor's record, there before the job ran
                   {"role": "planner", "holder_kind": "cockpit", "session_id": "cockpit-session-1"}, {}, {}, "x")
    r = w.kyloop("planner")
    assert r.returncode == 0, r.stderr
    first, second = w.records()                             # the loop went on
    rid = first["run_id"]
    bad = sorted(["JOB-%s-torn.json" % rid, "JOB-%s-not-a-record.json" % rid, "JOB-%s-wrong-actor.json" % rid,
                  "push-1.json", "ACT-forged-controller.json"])
    assert sorted(first["job_actions"]["quarantined"]) == bad
    assert first["accepted"] == ["B-3.s1"]                  # its checkpoint request still counted
    q = w.run / "actions" / "quarantine"
    moved = sorted(p.name.rsplit(".", 1)[0] for p in q.iterdir())
    assert moved == bad                                     # the bytes are kept, under their names + a timestamp
    assert (q / next(p.name for p in q.iterdir() if p.name.startswith("push-1.json"))).read_text() == \
        json.dumps({"what": "pushed", "when": "now"})
    left = sorted(p.name for p in (w.run / "actions").glob("*.json"))
    assert left == sorted(["ACT-KW01.json", "LAUNCH-%s.json" % rid, "LAUNCH-%s.json" % second["run_id"]] +
                          [p.name for p in (w.run / "actions").glob("NOTIFY-*.json")])
    assert kyaction.unfinished(w.run) == [kyaction.load(w.run, "ACT-KW01")]         # the strict read works again
    (item,) = quarantine_items(w)
    assert item["blocks"] == "none" and all(name in json.dumps(item) for name in bad)
    assert_awaiting_schema(item)
    assert not [a for a in w.awaiting() if a["id"].endswith("-precondition")]


def test_a_malformed_job_file_left_by_a_run_of_a_dead_controller_is_quarantined_at_start_up(w):
    """Start-up recovery: the previous controller died before it could look at what its job had written."""
    w.ready()
    w.modes("stop")
    gone = dead_pid()
    old_run(w, pid=gone, pgid=gone, process_start="Thu Jan  1 00:00:00 1970")
    old_launch(w)
    (w.run / "actions" / ("JOB-%s-torn.json" % OLD_RUN)).write_text("{torn")
    job = {"role": "planner", "holder_kind": "job", "controller_id": OLD_CTL, "run_id": OLD_RUN}
    kyaction.begin(w.run, "JOB-%s-open-pr" % OLD_RUN, "pr_create", job, {"title": "x"}, {}, "open a PR")
    r = w.kyloop("planner")
    assert r.returncode == 0, r.stderr
    assert w.calls() == [1]                                 # recovered, then launched
    assert [p.name.rsplit(".", 1)[0] for p in (w.run / "actions" / "quarantine").iterdir()] == ["JOB-%s-torn.json" % OLD_RUN]
    assert len(quarantine_items(w)) == 1 and len(job_action_items(w)) == 1
    act = kyaction.load(w.run, "JOB-%s-open-pr" % OLD_RUN)
    assert act["state"] == "INTENDED" and act["reconciliations"][-1]["outcome"] == "unknown"
    old = json.loads((w.run / "loops" / "planner" / (OLD_RUN + ".json")).read_text())
    assert old["ended_reason"] == "interrupted" and old["job_actions"]["unknown"] == ["JOB-%s-open-pr" % OLD_RUN]


def test_a_job_record_is_left_alone_while_its_job_is_not_known_gone(w):
    """The run record is unfinished and its child cannot be identified: the launch is unknown (a refusal) — and the
    job's own record is not judged before that."""
    w.ready()
    w.default_mode("stop")
    old_run(w)                                              # no pid: the child was pending
    old_launch(w)
    job = {"role": "planner", "holder_kind": "job", "controller_id": OLD_CTL, "run_id": OLD_RUN}
    kyaction.begin(w.run, "JOB-%s-open-pr" % OLD_RUN, "pr_create", job, {"title": "x"}, {}, "open a PR")
    assert w.kyloop("planner").returncode == 0
    assert "action_unreconciled" in json.dumps(refused(w))
    assert "reconciliations" not in kyaction.load(w.run, "JOB-%s-open-pr" % OLD_RUN) and job_action_items(w) == []


def test_a_job_using_the_prompts_command_leaves_a_record_the_controller_reconciles(w):
    """End to end with the sibling's real CLI: `kyaction.py begin` exactly as the prompt gives it, then the job
    exits without `complete` — the controller settles it from `git ls-remote`."""
    w.ready()
    w.modes("job-cli", "stop")
    (w.wt / ".git").mkdir()
    (w.wt / ".git" / "ls-remote.origin").write_text("%s\t%s\n" % (PUSH["commit"], PUSH["ref"]))
    assert w.kyloop("planner").returncode == 0
    first = w.records()[0]
    assert w.call(1, "kyaction.rc").strip() == "0", w.call(1, "kyaction.err")
    assert json.loads(w.call(1, "kyaction.out"))["status"] == "new"
    aid = "JOB-%s-cli-push" % first["run_id"]
    act = kyaction.load(w.run, aid)
    assert act["actor"] == {"role": "planner", "holder_kind": "job", "controller_id": first["controller_id"],
                            "run_id": first["run_id"]}
    assert act["state"] == "DONE" and first["job_actions"]["reconciled"] == [aid]
    assert_schema("action", act)


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
    left_by_a_dead_process(w, "CMD-" + cid)
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
    left_by_a_dead_process(w, "CMD-" + cid)                 # that cockpit session is gone
    assert w.kyloop("planner").returncode == 0
    assert "command_unreconciled" in json.dumps(refused(w))             # not repeated blind, nothing launched
    assert command(w, cid)["state"] == "QUEUED" and "owner_directives" not in w.role_state()
    assert kyaction.load(w.run, "CMD-" + cid)["reconciliations"][-1]["outcome"] == "unknown"


def test_a_command_whose_application_another_live_process_began_is_waited_for_not_repeated(w):
    """kyaction says who began a record. While that process is alive the application may be in its handler: the
    controller neither repeats nor reconciles it — it waits, launches nothing, and goes on once it is settled."""
    w.ready()
    w.default_mode("stop")
    cid = submit(w, "planner", "builders", {"n": 5})
    entry = kycommands.find(w.run, cid)
    kyaction.begin(w.run, "CMD-" + cid, "command:builders",         # begun by THIS (live) process
                   {"role": "planner", "holder_kind": "cockpit", "session_id": "cockpit-session-1"},
                   {"role": "planner", "command": "builders", "args": {"n": 5}},
                   {"command_id": cid, "file": entry["path"].name}, "command %s: QUEUED → APPLIED" % cid)
    p = w.popen("planner")
    try:
        assert wait_for(lambda: (w.loop_state() or {}).get("waiting") == "commands_pending")
        time.sleep(0.4)
        assert w.calls() == [] and p.poll() is None and command(w, cid)["state"] == "QUEUED"
        assert "reconciliations" not in kyaction.load(w.run, "CMD-" + cid) and w.awaiting() == []
        kyaction.complete(w.run, "CMD-" + cid, {"recorded": "builders"})        # that process finishes its handler
        assert p.wait(timeout=20) == 0
    finally:
        p.kill()
    assert command(w, cid)["state"] == "APPLIED" and w.calls() == [1]
    assert "owner_directives" not in w.role_state()         # its handler ran once, elsewhere — not again here


# ───────────────────────────── the conductor's activation chain ─────────────────────────────

def chain(w, links, rooted=True):
    """`links` activation records as they are really written. rooted: the un-numbered record (link 0), then
    `links - 1` bundle changes; not rooted (a bundle change made before B-5): `links` numbered records only, the
    first with previous = null. The numbered ones are written by kyveto's own plan_bundle_change executor, from a
    manifest file whose digest the change binds and an independent review receipt bound to that digest.
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
        manifest = write_manifest(w, n)
        review = w.run / "reviews" / ("review-%d.json" % n)
        review.write_text(json.dumps({"verdict": "ACCEPTED", "reviewer_session_id": "astra-%d" % n,
                                      "source_commit": COMMITS[n], "manifest_sha256": MANIFESTS[n],
                                      "inputs": {str(manifest): sha(manifest)}}))
        params = {"kind": "plan_bundle_change", "old_commit": COMMITS[n - 1], "new_commit": COMMITS[n],
                  "old_manifest_digest": MANIFESTS[n - 1], "new_manifest_digest": MANIFESTS[n],
                  "new_manifest_path": str(manifest), "review_receipts": [str(review)]}
        ctx = kyveto.Ctx(env, "SD-20261011T220000Z-%d" % n,
                         {"source_commit": COMMITS[n - 1], "entrypoints_digest": E1}, "2026-10-11T22:30:00Z",
                         sessions=["surrogate-1", "kalayantra-owner-surrogate"])
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
    ("launchd", "launchd", None, "qualification_context_mismatch"),    # N3-04: told "launchd" is not launchd …
    ("test-hook:launchd", "launchd", None, None),                        # … it is a context of its own
    ("test-hook:shell", "shell", None, None),
    ("shell", "shell", None, "qualification_context_mismatch"),
    ("test-hook:launchd", None, None, "qualification_context_mismatch"),  # … which no real controller runs in
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
    assert expected(KY_LOOP_TEST_CONTEXT="launchd")["context"] == "test-hook:launchd"   # never reported as proven
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
    assert not w.stop_file().exists()                       # a duplicate start never stops what it cannot see …
    (item,) = w.awaiting()                                  # … but unknown raises attention: ONE item (R2)
    assert item["id"].endswith("-loop-planner-lock-owner-unknown") and item["blocks"] == "none"
    assert str(lock) in json.dumps(item)
    assert_awaiting_schema(item)
    assert w.cockpit_journal().count("[decision]") == 1
    assert w.kyloop("planner").returncode == 0              # looked at again: still not taken, and no second item
    assert lock_bytes(lock) == before and len(w.awaiting()) == 1 and w.cockpit_journal().count("[decision]") == 1
    assert not list((w.run / "locks").glob(".planner.*"))   # nothing was staged, buried or left behind


def test_a_lock_is_never_taken_over_when_ps_cannot_be_asked(w, monkeypatch):
    w.ready()
    lock = hold_lock(w, "planner", {"session_or_run_id": "CTL-dead", "pid": dead_pid(), "pgid": 1,
                                    "process_start": "Thu Jan  1 00:00:00 1970"})
    for name, value in w.env().items():
        monkeypatch.setenv(name, value)
    c = kyloop.Controller("planner")
    assert c.identity()["process_start"]                    # its own identity is known; the OWNER's cannot be asked
    real_run = subprocess.run

    def no_ps(argv, *args, **kwargs):
        if list(argv)[:1] == ["/bin/ps"]:
            raise OSError("ps cannot be asked")
        return real_run(argv, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", no_ps)
    assert c.acquire_lock() is False and c.lock_refusal["state"] == "unknown" and lock.is_dir()
    blind = kyloop.Controller("planner")                    # … and one that cannot read its OWN identity takes no lock
    lock2 = w.run / "locks" / "planner"
    assert blind.acquire_lock() is False and blind.lock_refusal["state"] == "self_unknown" and lock2.is_dir()
    monkeypatch.setattr(subprocess, "run", real_run)        # the same lock, once ps answers: positively gone
    assert c.acquire_lock() is True
    owner = json.loads((lock / "owner.json").read_text())
    assert owner["pid"] == os.getpid() and owner["process_start"] == lstart(os.getpid()) and owner["child"] is None
    c.release_lock()
    assert not lock.exists()


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
    assert c.remove_stale_lock(judged) == "changed" and lock_bytes(lock) == {"owner.json": json.dumps(fresh).encode()}
    (lock / "owner.json").write_text(json.dumps(judged))    # … whereas the judged lock itself is removed
    assert c.remove_stale_lock(judged) == "removed" and not lock.exists()
    assert c.remove_stale_lock(judged) == "absent"          # nothing there: nothing removed
    assert not list((w.run / "locks").glob(".planner.*"))


def swap_owner_before_rename(monkeypatch, lock, fresh):
    """Interleave a faster contender between the slower one's last look and its rename: the moment the slower one
    renames the lock aside, the lock at that path is already the faster one's."""
    real = os.rename

    def rename(src, dst, *args, **kwargs):
        if str(src) == str(lock) and ".grave." in str(dst):
            (lock / "owner.json").write_text(json.dumps(fresh))
        return real(src, dst, *args, **kwargs)

    monkeypatch.setattr(kyloop.os, "rename", rename)


def test_a_takeover_is_verified_after_the_rename_and_a_lock_that_changed_hands_is_put_back(w, monkeypatch):
    """R2 / SUP-01: the judgment is re-checked on what was actually buried, not on what was looked at before."""
    w.ready()
    judged = {"session_or_run_id": "CTL-dead", "pid": dead_pid(), "pgid": 1,
              "process_start": "Thu Jan  1 00:00:00 1970"}
    fresh = {"session_or_run_id": "CTL-PLANNER-faster", "holder_kind": "controller", "pid": os.getpid(),
             "process_start": lstart(os.getpid())}
    lock = hold_lock(w, "planner", judged)
    swap_owner_before_rename(monkeypatch, lock, fresh)
    assert kyloop.lock_bury(lock, judged) == "restored"
    assert lock_bytes(lock) == {"owner.json": json.dumps(fresh).encode()}           # the faster one's lock, untouched
    assert not list((w.run / "locks").glob(".planner.*"))
    # … and when the path was re-taken while it was aside, nothing is overwritten and nothing deleted
    (lock / "owner.json").write_text(json.dumps(judged))
    real_exclusive = kyloop.rename_exclusive

    def retaken(src, dst):
        if ".grave." in str(src):
            raise FileExistsError(17, "File exists", str(dst))
        return real_exclusive(src, dst)

    monkeypatch.setattr(kyloop, "rename_exclusive", retaken)
    assert kyloop.lock_bury(lock, judged) == "conflict"
    (grave,) = list((w.run / "locks").glob(".planner.grave.*"))
    assert json.loads((grave / "owner.json").read_text()) == fresh


def test_two_controllers_never_both_take_a_stale_lock(w, monkeypatch):
    """The whole acquisition, interleaved: the slower contender's takeover finds the faster one's lock and refuses."""
    w.ready()
    for name, value in w.env().items():
        monkeypatch.setenv(name, value)
    c = kyloop.Controller("planner")
    sleeper = subprocess.Popen(["/bin/sleep", "60"])
    try:
        fresh = {"session_or_run_id": "CTL-PLANNER-faster", "holder_kind": "controller", "pid": sleeper.pid,
                 "process_start": lstart(sleeper.pid), "child": None}
        lock = hold_lock(w, "planner", {"session_or_run_id": "CTL-dead", "pid": dead_pid(), "pgid": 1,
                                        "process_start": "Thu Jan  1 00:00:00 1970"})
        swap_owner_before_rename(monkeypatch, lock, fresh)
        assert c.acquire_lock() is False and c.lock_refusal["state"] == "live"
        assert json.loads((lock / "owner.json").read_text()) == fresh and c.lock_held is False
    finally:
        sleeper.kill()
        sleeper.wait()


def test_a_lock_is_created_atomically_with_its_owner_and_never_onto_an_existing_directory(w, monkeypatch):
    """R2: the lock appears complete or not at all — including onto an EMPTY directory, which a plain rename would
    silently replace (an ownerless lock would be taken over by accident)."""
    locks = w.run / "locks"
    locks.mkdir()
    owner = {"session_or_run_id": "CTL-1", "pid": os.getpid(), "process_start": lstart(os.getpid())}
    seen = []
    real = kyloop.rename_exclusive

    def watching(src, dst):
        seen.append((os.path.exists(dst), sorted(os.listdir(src))))     # just before the lock appears
        return real(src, dst)

    monkeypatch.setattr(kyloop, "rename_exclusive", watching)
    assert kyloop.lock_create(locks / "planner", owner) is True
    assert seen == [(False, ["owner.json"])]                # the owner record was complete BEFORE the lock existed
    assert json.loads((locks / "planner" / "owner.json").read_text()) == owner
    assert kyloop.lock_create(locks / "planner", dict(owner, session_or_run_id="CTL-2")) is False
    assert json.loads((locks / "planner" / "owner.json").read_text()) == owner
    monkeypatch.setattr(kyloop, "rename_exclusive", real)
    for native in (True, False):                            # with the kernel's exclusive rename, and without it
        if not native:
            monkeypatch.setattr(kyloop, "_LIBC", [None])
        empty = locks / ("ownerless-%s" % native)
        empty.mkdir()
        assert kyloop.lock_create(empty, owner) is False and list(empty.iterdir()) == []
        with pytest.raises(FileExistsError):
            kyloop.rename_exclusive(locks / "planner", empty)
        assert (locks / "planner" / "owner.json").exists()
    assert sorted(p.name for p in locks.iterdir() if p.name.startswith(".")) == []      # no staging directory left


def test_the_loop_state_mutex_is_a_kernel_lock_and_nothing_is_removed_by_age(w):
    """R2: no age-based removal anywhere. The loop-state mutex is an flock: released by the kernel when its holder
    ends, so a leftover of a crashed writer cannot exist — and an old directory of the former kind is not touched."""
    import fcntl
    w.enable()
    stale = w.run / "locks" / "loopstate.planner"           # what the previous implementation could leave behind
    stale.mkdir(parents=True)
    old = time.time() - 7200
    os.utime(stale, (old, old))
    kyloop.update_loop_state(w.run, "planner", lambda d: dict(d, touched=1))
    assert stale.is_dir() and w.loop_state()["touched"] == 1
    holder = subprocess.Popen([PY, "-c", "import fcntl, os, sys, time; fd = os.open(sys.argv[1], os.O_CREAT | os.O_RDWR); "
                                         "fcntl.flock(fd, fcntl.LOCK_EX); print('held', flush=True); time.sleep(60)",
                               str(w.run / "locks" / ".loopstate.planner.flock")], stdout=subprocess.PIPE, text=True)
    try:
        assert holder.stdout.readline().strip() == "held"
        t0 = time.time()
        writer = w.popen("admin")                           # not used: the admin switch is a plain subprocess below
        writer.kill()
        writer.wait()
        r = subprocess.Popen([PY, str(w.fleet / "kyloop.py"), "admin", "disable", "planner", "--reason", "x"],
                             env=w.env(), stderr=subprocess.PIPE, text=True)
        time.sleep(0.5)
        assert r.poll() is None and w.loop_state()["enabled"] is True      # it waits for the holder …
        holder.kill()                                       # … whose death alone releases the mutex
        holder.wait()
        assert r.wait(timeout=10) == 0 and time.time() - t0 < 9
    finally:
        holder.kill()
    assert w.loop_state()["enabled"] is False and w.loop_state()["touched"] == 1


def test_job_state_calls_a_job_gone_only_when_its_leader_and_its_group_are_gone():
    """R2: leader positively gone AND killpg(pgid, 0) → no such process. Pending, unidentified and unknown never."""
    assert kyloop.job_state(None, None, None) == "unknown"                  # recorded as pending: never gone
    assert kyloop.job_state("12", 12, "x") == "unknown"
    gone = dead_pid()
    assert kyloop.job_state(gone, gone, "Thu Jan  1 00:00:00 1970") == "gone"
    assert kyloop.job_state(gone, 1, "Thu Jan  1 00:00:00 1970") == "unknown"       # a group that is not its own
    assert kyloop.job_state(gone, None, "Thu Jan  1 00:00:00 1970") == "unknown"
    # a leader that ended and left a member of its group behind
    leader = subprocess.Popen(["/bin/sh", "-c", "/bin/sleep 60 & echo $!; exit 0"], start_new_session=True,
                              stdout=subprocess.PIPE, text=True)
    start = lstart(leader.pid)
    member = int(leader.stdout.readline())
    try:
        leader.wait()                                       # (before it is reaped it is a zombie: gone as well)
        assert kyloop.job_state(leader.pid, leader.pid, start) == "survivors"
        assert kyloop.group_gone(leader.pid) is False
    finally:
        kill_quietly(member)
    assert wait_for(lambda: kyloop.job_state(leader.pid, leader.pid, start) == "gone")
    # a live process under a recorded pid whose start identity differs is the pid REUSED: the old job is gone, and
    # the group that pid leads now is someone else's — it is never probed
    other = subprocess.Popen(["/bin/sleep", "60"], start_new_session=True)
    try:
        assert kyloop.job_state(other.pid, other.pid, "Thu Jan  1 00:00:00 1970") == "gone"
        assert kyloop.job_state(other.pid, other.pid, lstart(other.pid)) == "live"
        assert kyloop.job_state(other.pid, other.pid, "not a start identity") == "unknown"
    finally:
        other.kill()
        other.wait()


def test_a_process_group_that_outlived_its_leader_is_never_signalled_and_never_called_gone(w):
    """An inherited run whose leader is gone but whose group is not: the members cannot be identified as that job's
    (the group id may be anyone's by now), so nothing is signalled and the launch stays unknown."""
    w.ready()
    w.default_mode("stop")
    leader = subprocess.Popen(["/bin/sh", "-c", "/bin/sleep 60 & echo $!; exit 0"], start_new_session=True,
                              stdout=subprocess.PIPE, text=True)
    start = lstart(leader.pid)
    member = int(leader.stdout.readline())
    leader.wait()
    try:
        old_run(w, pid=leader.pid, pgid=leader.pid, process_start=start)
        old_launch(w)
        assert w.kyloop("planner").returncode == 0
        assert "action_unreconciled" in json.dumps(refused(w))
        assert not pid_gone(member)                         # left alone
        run = json.loads((w.run / "loops" / "planner" / (OLD_RUN + ".json")).read_text())
        assert run["ended_at"] is None
    finally:
        kill_quietly(member)


def test_a_dead_controller_whose_child_was_pending_is_never_replaced_blind(w):
    """R2: `child: "pending"` is written BEFORE the child is started. The role lock of the dead controller is taken
    over (recovery needs it) — and recovery refuses: the launch is unknown, nothing is relaunched."""
    w.ready()
    w.default_mode("stop")
    hold_lock(w, "planner", {"session_or_run_id": OLD_CTL, "holder_kind": "controller", "pid": dead_pid(), "pgid": 1,
                             "process_start": "Thu Jan  1 00:00:00 1970", "child": "pending"})
    old_run(w)
    old_launch(w)
    r = w.kyloop("planner")
    assert r.returncode == 0 and w.calls() == [] and "never taken for gone while pending" in r.stderr
    assert "action_unreconciled" in json.dumps(refused(w))


def test_the_child_is_recorded_as_pending_before_it_exists(w, monkeypatch):
    w.ready()
    for name, value in w.env().items():
        monkeypatch.setenv(name, value)
    real_popen, seen = subprocess.Popen, {}

    def popen(argv, *args, **kwargs):
        if list(argv)[1:2] != ["-p"]:
            return real_popen(argv, *args, **kwargs)
        seen["owner_child"] = json.loads((w.run / "locks" / "planner" / "owner.json").read_text())["child"]
        seen["expected_child"] = w.loop_state()["expected_child"]
        seen["run_pid"] = w.records()[0]["pid"]
        raise OSError("exec format error")

    c = kyloop.Controller("planner")
    c.load_siblings()
    assert c.acquire_lock()
    try:
        c.cfg, _ = c.load_config()
        os.makedirs(c.loop_dir, exist_ok=True)
        c.state_sha = kyloop.sha_file(c.state_path)
        monkeypatch.setattr(subprocess, "Popen", popen)
        c.run_job([{"id": "step.B-3", "kind": "step", "key": "B-3"}])
        monkeypatch.setattr(subprocess, "Popen", real_popen)
        assert json.loads((w.run / "locks" / "planner" / "owner.json").read_text())["child"] is None
    finally:
        monkeypatch.setattr(subprocess, "Popen", real_popen)
        c.release_lock()
    assert seen["owner_child"] == "pending" and seen["run_pid"] is None
    assert seen["expected_child"]["pending"] is True and seen["expected_child"]["pid"] is None
    assert kyloop.recorded_child(w.run, "planner")[0] == "none"


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


# ───────────────────────────── no crash loops (R10) ─────────────────────────────

def test_sha_file_and_read_json_are_total(tmp_path):
    assert kyloop.sha_file("/tmp/a\x00b") is None and kyloop.sha_file(None) is None
    assert kyloop.sha_file(0) is None                       # a number would be read as a file descriptor
    assert kyloop.sha_file(str(tmp_path)) is None and kyloop.sha_file(str(tmp_path / "absent")) is None
    assert kyloop.read_json("/tmp/a\x00b") == (None, "unreadable: ValueError")
    assert kyloop.read_json(7) == (None, "unreadable: not a path")
    assert kyloop.read_json(str(tmp_path / "absent")) == (None, "missing")
    deep = tmp_path / "deep.json"
    deep.write_text("[" * 200000 + "]" * 200000)
    doc, err = kyloop.read_json(deep)
    assert doc is None and err in ("unreadable: RecursionError", "unreadable: JSONDecodeError")
    (tmp_path / "bad.json").write_bytes(b"\xff\xfe{")
    assert kyloop.read_json(tmp_path / "bad.json")[1].startswith("unreadable")


def test_a_checkpoint_request_with_a_nul_in_its_evidence_path_never_crashes_the_controller(w):
    """L-02 as reported: such a request used to raise ValueError in sha_file — exit 1, a respawn every 10 s, and the
    same exception again in start-up recovery. Now it is a refused request like any other."""
    w.ready()
    w.default_mode("nulpath")
    r = w.kyloop("planner")
    assert r.returncode == 0 and "Traceback" not in r.stderr, r.stderr
    recs = w.records()
    assert len(recs) == 3 and all(x["ended_at"] and x["refused"][0]["reason"] == "evidence_malformed" for x in recs)
    (aw,) = w.awaiting()                                    # exactly one awaiting file: the breaker's
    assert aw["id"].endswith("-loop-planner-no-progress") and w.stop_file().exists()
    assert w.loop_state()["enabled"] is False and kyaction.unfinished(w.run) == []
    for _ in range(2):                                      # a second start — as launchd, or as the owner — does not relaunch
        r = w.kyloop("planner")
        assert r.returncode == 0 and "Traceback" not in r.stderr and w.calls() == [1, 2, 3]
        w.rearm()
    assert len(w.awaiting()) == 1


def test_start_up_recovery_of_a_run_with_a_nul_path_request_finalises_it_and_goes_on(w):
    """The respawn half of L-02: recovery finalises the very run whose outbox holds the request."""
    w.ready()
    w.modes("stop")
    gone = dead_pid()
    rec = old_run(w, pid=gone, pgid=gone, process_start="Thu Jan  1 00:00:00 1970",
                  work_items=[{"id": "step.B-3", "kind": "step", "key": "B-3"}], worktree=str(w.wt))
    old_launch(w)
    req = {"schema": "ky.checkpoint_request/1", "run_id": OLD_RUN, "fence": rec["fence"], "item": "step.B-3",
           "step_id": "B-3.s1", "kind": "substep", "evidence": [{"type": "file", "path": "/tmp/a\x00b", "sha256": "0" * 64}]}
    (Path(rec["out_dir"]) / "checkpoints" / "001.json").write_text(json.dumps(req))
    (Path(rec["out_dir"]) / "checkpoints" / "002.json").write_text("[" * 200000)       # … and one that is not JSON
    r = w.kyloop("planner")
    assert r.returncode == 0 and "Traceback" not in r.stderr, r.stderr
    old = json.loads((w.run / "loops" / "planner" / (OLD_RUN + ".json")).read_text())
    assert [x["reason"] for x in old["refused"]] == ["evidence_malformed", "malformed"] and old["ended_at"]
    assert w.calls() == [1] and w.awaiting() == []          # recovered, and the loop went on


class Signals:
    """Controller.main() installs TERM/INT handlers; an in-process test puts pytest's own back."""

    def __enter__(self):
        self.saved = {s: signal.getsignal(s) for s in (signal.SIGTERM, signal.SIGINT)}

    def __exit__(self, *exc):
        for s, handler in self.saved.items():
            signal.signal(s, handler)


def controller_in_process(w, monkeypatch, role="planner", **extra):
    """A controller in this process that sees what an installed one in the test world sees: that world's
    environment, and no qualification harness beside it (this checkout has the real kyqualify.py beside kyloop.py;
    the world's fleet_live has none unless a test installs its own)."""
    for name, value in w.env(**extra).items():
        monkeypatch.setenv(name, value)
    monkeypatch.setattr(kyloop, "HARNESS", "kyqualify_not_installed_in_the_test_world")
    return (kyloop.VetoController if role == "veto" else kyloop.Controller)(role)


FAULTS = ["prepare", "reconciliation", "finalize", "main"]


@pytest.mark.parametrize("where", FAULTS)
def test_an_unexpected_exception_becomes_one_awaiting_item_stop_disabled_and_exit_0(w, monkeypatch, where):
    """R10: nothing leaves the controller as a traceback launchd would respawn."""
    w.ready()
    w.default_mode("substep")
    real_reconcile = kyloop.Controller.reconcile_actions

    def reconcile(self, full=False):
        if full == (where == "prepare"):
            raise RuntimeError("injected fault in %s" % where)
        return real_reconcile(self, full)

    def boom(self, *args, **kwargs):
        raise RuntimeError("injected fault in %s" % where)

    with monkeypatch.context() as m, Signals():
        if where in ("prepare", "reconciliation"):
            m.setattr(kyloop.Controller, "reconcile_actions", reconcile)
        elif where == "finalize":
            m.setattr(kyloop.Controller, "process_outbox", boom)
        else:
            m.setattr(kyloop.Controller, "eligible_items", boom)
        c = controller_in_process(w, m)
        assert c.main() == 0                                # exit 0: launchd (SuccessfulExit false) does not respawn
        a = refused_after_runs(w)                           # exactly one awaiting file, STOP, disabled
        assert ("controller_fault: %s raised RuntimeError: injected fault in %s" % (where, where)) in json.dumps(a)
        assert w.calls() == ([1] if where == "finalize" else [])
        assert not (w.run / "locks" / "planner").exists() and w.loop_state()["controller"] is None
        if where == "finalize":                             # the child that was running is not left unrecorded for good
            assert kyaction.load(w.run, "LAUNCH-" + w.records()[0]["run_id"])["state"] == "INTENDED"
        calls = w.calls()
        assert controller_in_process(w, m).main() == 0      # a second start, the fault still there: nothing new
        assert len(w.awaiting()) == 1 and w.calls() == calls
    r = w.kyloop("planner")                                 # … and with the fault gone: still stopped, no relaunch
    assert r.returncode == 0 and "Traceback" not in r.stderr and w.calls() == calls
    assert len(w.awaiting()) == 1 and w.stop_file().exists() and w.loop_state()["enabled"] is False


def test_a_fault_before_the_role_lock_is_held_raises_attention_and_stops_nothing(w, monkeypatch):
    """A duplicate start that fails while acquiring never stops a loop it cannot see: exit 0, one item, no STOP."""
    w.ready()

    def boom(self):
        raise OSError("the locks directory cannot be used")

    with monkeypatch.context() as m, Signals():
        m.setattr(kyloop.Controller, "acquire", boom)
        assert controller_in_process(w, m).main() == 0
        assert controller_in_process(w, m).main() == 0
    (item,) = w.awaiting()
    assert item["id"].endswith("-loop-planner-start-fault") and item["blocks"] == "none"
    assert "controller_fault: main raised OSError" in json.dumps(item)
    assert not w.stop_file().exists() and w.loop_state()["enabled"] is True and w.calls() == []


def test_a_fault_while_a_child_runs_ends_the_child_before_the_controller_stops(w, monkeypatch):
    """Nothing started is left unsupervised: a failure of the controller's own bookkeeping after the launch ends
    the child's process group first."""
    w.ready()
    w.default_mode("hang")
    hang = w.root / "bin" / "claude.d" / "hang.pid"

    def boom(self, proc, record, deadline):
        assert wait_for(hang.exists)
        raise OSError("the state directory vanished")

    with monkeypatch.context() as m, Signals():
        m.setattr(kyloop.Controller, "supervise", boom)
        assert controller_in_process(w, m).main() == 0
    assert pid_gone(int(hang.read_text()))
    rec = w.records()[0]
    assert rec["ended_reason"] == "controller_fault" and rec["ended_at"] and "OSError" in rec["supervision_fault"]
    assert "controller_fault: supervision raised OSError" in json.dumps(refused_after_runs(w))
    assert kyaction.load(w.run, "LAUNCH-" + rec["run_id"])["state"] == "DONE"


def test_an_unreadable_loop_state_is_never_rewritten_from_empty(w):
    """N-08: the file holds the switch, the breaker and the no-progress count."""
    w.ready()
    path = w.run / "loops" / "planner.json"
    for text in ("{torn", "[1, 2]"):
        path.write_text(text)
        r = w.kyloop("planner")
        assert r.returncode == 0 and w.calls() == [] and "loop_state_unreadable" in r.stderr
        assert path.read_text() == text                     # untouched
        (item,) = w.awaiting()
        assert item["id"].endswith("-loop-planner-state-unreadable") and str(path) in json.dumps(item)
        assert w.stop_file().exists() and not (w.run / "locks" / "planner").exists()
        for verb in ("enable", "disable"):                  # the switch refuses too, by name
            r = w.kyloop("admin", verb, "planner", "--reason", "x")
            assert r.returncode == 1 and "loop_state_unreadable" in r.stderr and path.read_text() == text
        assert json.loads(w.kyloop("admin", "show", "planner").stdout)["present"] is False
        assert w.kyloop("admin", "child", "planner").stdout.split()[0] == "unknown"
        w.stop_file().unlink()
    assert w.cockpit_journal().count("[decision]") == 1     # one attention item, one notification


def test_the_launch_decision_reads_the_no_progress_count_itself(w):
    """N-09: a controller that died between recording the third no-progress run and opening the breaker."""
    w.ready()
    w.default_mode("substep")
    st = w.loop_state()
    st.update(no_progress_count=3, breaker={"open": False, "history": []})
    (w.run / "loops" / "planner.json").write_text(json.dumps(st))
    r = w.kyloop("planner")
    assert r.returncode == 0 and w.calls() == []            # not one extra launch
    ls = w.loop_state()
    assert ls["breaker"]["open"] is True and ls["enabled"] is False and w.stop_file().exists()
    assert [a["id"].rsplit("-loop-", 1)[1] for a in w.awaiting()] == ["planner-no-progress"]
    st.update(no_progress_count=2, enabled=True)            # the control: one below the limit launches
    (w.run / "loops" / "planner.json").write_text(json.dumps(st))
    w.stop_file().unlink()
    w.modes("stop")
    assert w.kyloop("planner").returncode == 0 and w.calls() == [1]


# ───────────────────────────── evidence, sub-steps, snapshots (N-01, N-03) ─────────────────────────────

def test_evidence_in_the_run_scratch_is_accepted(w):
    w.ready()
    w.modes("substep-scratch", "stop")
    assert w.kyloop("planner").returncode == 0
    rec = w.records()[0]
    assert rec["accepted"] == ["B-3.s1"] and rec["refused"] == []
    assert w.role_state()["completed_steps"][0]["evidence"][0]["path"].startswith(str(w.scratch))


def test_a_whole_step_is_not_accepted_on_a_readable_file_outside_the_allowed_roots(w):
    """N-01 as probed: step B-3 used to be accepted on the hash of /etc/hosts."""
    w.ready()
    w.modes("outside", "stop")
    assert w.kyloop("planner").returncode == 0
    rec = w.records()[0]
    assert rec["refused"][0]["reason"] == "evidence_outside_allowed_roots" and rec["progressed"] is False
    assert w.role_state()["completed_steps"] == []
    job = json.loads((Path(rec["prompt_path"]).parent / "job.json").read_text())
    assert job["evidence_roots"] == [str(w.wt), str(Path(rec["prompt_path"]).parent), str(w.run)]


def test_sub_steps_per_item_are_capped_until_recorded_evidence_changes(w):
    """N-01: a job cannot keep the breaker closed with trivial files. Default cap 20; beyond it a sub-step of that
    item is refused until recorded evidence (an external dependency, an owner's answer) has changed."""
    w.ready()
    w.default_mode("many-substeps")                         # 25 trivial sub-steps of B-3 per run
    r = w.kyloop("planner")
    assert r.returncode == 0, r.stderr
    recs = w.records()
    assert len(recs) == 4                                   # one run that used the cap up, then three without progress
    assert len(recs[0]["accepted"]) == 20 and len(recs[0]["refused"]) == 5
    assert {x["reason"] for x in recs[0]["refused"]} == {"substep_cap_reached"}
    assert all(x["accepted"] == [] and x["progressed"] is False for x in recs[1:])
    assert all({y["reason"] for y in x["refused"]} == {"substep_cap_reached"} for x in recs[1:])
    ls = w.loop_state()
    assert ls["breaker"]["open"] is True and ls["substeps"]["step.B-3"]["count"] == 20
    jobs = [json.loads((Path(x["prompt_path"]).parent / "job.json").read_text()) for x in recs]
    assert [j["work_items"][0]["substeps_left"] for j in jobs] == [20, 0, 0, 0]       # the job is told
    assert [j["work_items"][1]["substeps_left"] for j in jobs] == [20, 20, 20, 20]    # per item
    # the owner's recorded answer is changed evidence: the breaker reopens AND the item's window starts again
    (aw,) = [a for a in w.awaiting() if a["id"].endswith("-loop-planner-no-progress")]
    submit(w, "planner", "decide", {"awaiting_id": aw["id"], "answer": "change-and-restart"})
    (w.root / "bin" / "claude.d" / "substeps").write_text("3")
    w.rearm()
    w.modes("many-substeps", "stop")
    assert w.kyloop("planner").returncode == 0
    after = w.records()[4]
    assert len(after["accepted"]) == 3 and after["refused"] == [] and after["progressed"] is True
    assert w.loop_state()["substeps"]["step.B-3"]["count"] == 3


def test_the_sub_step_cap_is_configurable_and_a_whole_step_is_never_capped(w):
    w.loops_json({"planner": {"worktree": str(w.wt), "substep_cap": 2}})
    w.ready()
    (w.root / "bin" / "claude.d").mkdir(exist_ok=True)
    (w.root / "bin" / "claude.d" / "substeps").write_text("4")
    w.modes("many-substeps", "step", "stop")
    assert w.kyloop("planner").returncode == 0
    first, second = w.records()[:2]
    assert len(first["accepted"]) == 2 and len(first["refused"]) == 2 and first["substep_cap"] == 2
    assert second["accepted"] == ["B-3"]                    # the step itself, on its own evidence
    for bad in (0, -1, True, "20"):
        w.loops_json({"planner": {"worktree": str(w.wt), "substep_cap": bad}})
        assert kyloop_config_errors(w), bad


def kyloop_config_errors(w):
    r = w.kyloop("admin", "expected-qualification", "planner")
    return r.returncode == 1 and "loops_json_invalid" in r.stderr


@pytest.mark.parametrize("mode", ["tamper", "tamper-snapshot-gone"])
def test_a_child_that_writes_role_state_and_tampers_with_its_snapshot_is_refused(w, mode):
    """N-03: restore, flag, count as no progress, raise attention — never adopt the child's version."""
    w.ready()
    w.modes(mode, "stop")
    before = (w.run / "PLANNER_STATE.json").read_bytes()
    assert w.kyloop("planner").returncode == 0
    first = w.records()[0]
    assert (w.run / "PLANNER_STATE.json").read_bytes() == before            # restored from the controller's own copy
    assert first["state_violation"] is True and first["snapshot_intact"] is False
    assert first["accepted"] == [] and first["progressed"] is False         # its valid-looking request is not accepted
    assert first["refused"] == [{"file": first["refused"][0]["file"], "reason": "state_snapshot_tampered"}]
    assert w.role_state()["completed_steps"] == [] and w.loop_state()["no_progress_count"] == 2
    (item,) = [a for a in w.awaiting() if "-state-tamper-" in a["id"]]
    assert item["blocks"] == "none" and first["run_id"] in json.dumps(item)
    assert_awaiting_schema(item)
    forensic = Path(first["prompt_path"]).parent / "state.child_modified.json"
    assert json.loads(forensic.read_text())["heartbeat"] == "child-1"       # the child's version is kept as evidence
    assert len(w.records()) == 2                            # attention, not a stop: the loop went on


def test_a_child_that_only_writes_role_state_is_undone_and_its_requests_still_count(w):
    """The control for N-03: the snapshot is intact, so the run is not refused — the write is undone and flagged."""
    w.ready()
    w.modes("noprogress", "stop")
    before = (w.run / "PLANNER_STATE.json").read_bytes()
    assert w.kyloop("planner").returncode == 0
    first = w.records()[0]
    assert first["state_violation"] is True and first["snapshot_intact"] is True
    assert (w.run / "PLANNER_STATE.json").read_bytes() == before
    assert not [a for a in w.awaiting() if "-state-tamper-" in a["id"]]


def test_a_child_that_leaves_processes_behind_has_them_ended(w):
    """A job is over only when its process group is empty (R2): what a job leaves running is ended, and recorded."""
    w.ready()
    w.modes("leave-survivor", "stop")
    assert w.kyloop("planner").returncode == 0
    survivor = int((w.root / "bin" / "claude.d" / "survivor.pid").read_text())
    assert pid_gone(survivor) and w.records()[0]["survivors"] is True and w.records()[1]["survivors"] is None


# ───────────────────────────── scratch paths and binds (R1, R6) ─────────────────────────────

def test_the_child_gets_its_run_scratch_as_job_scratch_and_the_campaign_scratch_root(w):
    w.ready()
    w.modes("envdump")
    r = w.kyloop("planner")
    assert r.returncode == 0, r.stderr
    rec = w.records()[0]
    run_scratch = str(Path(rec["prompt_path"]).parent)
    assert w.call(1, "job_scratch").strip() == run_scratch and os.path.isabs(run_scratch)
    assert w.call(1, "ky_scratch").strip() == str(w.scratch)
    job = json.loads((Path(run_scratch) / "job.json").read_text())
    assert job["job_scratch"] == run_scratch and "JOB_SCRATCH" in rec["env_names"]
    binds = json.loads(w.kyloop("admin", "expected-qualification", "planner").stdout)["binds"]
    assert "JOB_SCRATCH" in binds["env_names"] and "KY_SCRATCH" in binds["env_names"]


def test_expected_binds_cover_the_project_settings_and_the_zdotdir(w):
    """R6: what `--setting-sources project` puts in force for the job, and the shell start-up files it would read."""
    def binds():
        r = w.kyloop("admin", "expected-qualification", "planner")
        assert r.returncode == 0, r.stderr
        return json.loads(r.stdout)["binds"]

    first = binds()
    assert first["project_settings_sha256"] == "absent"     # this worktree has no .claude/settings.json
    assert first["zdotdir_sha256"] == hashlib.sha256(b"").hexdigest()       # the directory exists and is empty
    assert "harness_sha256" not in first                    # no harness is installed beside this controller
    (w.wt / ".claude").mkdir()
    (w.wt / ".claude" / "settings.json").write_text('{"permissions": {"deny": ["Bash(git push*)"]}}')
    (w.root / "zdotdir" / ".zshenv").write_text("export X=1\n")
    (w.root / "zdotdir" / ".zshrc").write_text("alias ll=ls\n")
    (w.root / "zdotdir" / "sub").mkdir()                    # sub-directories and links are skipped
    os.symlink("/etc/hosts", w.root / "zdotdir" / "link")
    second = binds()
    assert second["project_settings_sha256"] == sha(w.wt / ".claude" / "settings.json")
    assert second["zdotdir_sha256"] == hashlib.sha256(b".zshenv" + b"export X=1\n" + b".zshrc" + b"alias ll=ls\n").hexdigest()
    shutil.rmtree(w.root / "zdotdir")
    assert binds()["zdotdir_sha256"] == "absent"
    (w.wt / ".claude" / "settings.json").unlink()
    (w.wt / ".claude" / "settings.json").mkdir()            # something is there that cannot be bound
    assert binds()["project_settings_sha256"] is None
    fleet = FLEET                                           # the two recipes are the harness's own, byte for byte
    if (fleet / "kyqualify.py").exists():
        import kyqualify
        (w.wt / ".claude" / "settings.json").rmdir()
        (w.wt / ".claude" / "settings.json").write_text("{}")
        (w.root / "zdotdir").mkdir()
        (w.root / "zdotdir" / ".zprofile").write_text("# x\n")
        assert kyloop.project_settings_digest(w.wt) == kyqualify.file_digest(str(w.wt / ".claude" / "settings.json"))
        assert kyloop.zdotdir_digest(w.root / "zdotdir") == kyqualify.directory_digest(str(w.root / "zdotdir"))
        assert kyloop.zdotdir_digest(w.root / "nope") == kyqualify.directory_digest(str(w.root / "nope")) == "absent"


@pytest.mark.parametrize("change", ["project-settings-added", "project-settings-changed", "zdotdir-file-added",
                                    "zdotdir-file-changed"])
def test_a_receipt_stops_qualifying_when_the_project_settings_or_the_zdotdir_change(w, change):
    w.enable()
    w.default_mode("stop")
    if change == "project-settings-changed":
        (w.wt / ".claude").mkdir()
        (w.wt / ".claude" / "settings.json").write_text('{"permissions": {}}')
    if change == "zdotdir-file-changed":
        (w.root / "zdotdir" / ".zshenv").write_text("export X=1\n")
    w.qualify()
    if change.startswith("project"):
        (w.wt / ".claude").mkdir(exist_ok=True)
        (w.wt / ".claude" / "settings.json").write_text('{"permissions": {"allow": ["Bash(git push*)"]}}')
    else:
        (w.root / "zdotdir" / ".zshenv").write_text("export X=2\n")
    assert w.kyloop("planner").returncode == 0
    a = json.dumps(refused(w))
    assert ("qualification_mismatch: %s" % ("project_settings_sha256" if change.startswith("project") else "zdotdir_sha256")) in a


# ───────────────────────────── the receipt check itself (N-05) ─────────────────────────────

FAKE_HARNESS = r"""
import json, os
CONFIG_KEYS = %(keys)r
def check_receipt(doc, cfg, require_context=None, verify_evidence=False, environ=None, report=None):
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "kyqualify.calls"), "a") as f:
        f.write(json.dumps({"role": cfg["role"], "require_context": require_context, "cfg": cfg}) + "\n")
    %(body)s
"""
HARNESS_KEYS = ("schema", "role", "model", "effort", "permission_mode", "max_turns", "deadline_seconds", "worktree",
                "claude_bin", "mcp_config", "prompt_path", "env_names", "child_path", "extra_flags",
                "disallowed_tools", "add_dirs", "intended_tools", "denied_tools")


def install_harness(w, body="return []", keys=HARNESS_KEYS):
    (w.fleet / "kyqualify.py").write_text(FAKE_HARNESS % {"keys": tuple(keys), "body": body})


@pytest.mark.parametrize("field,value,reason", [("schema", "ky.something/1", "qualification_schema"),
                                                ("schema", None, "qualification_schema"),
                                                ("role", "conductor", "qualification_role_mismatch"),
                                                ("model", "claude-haiku-5-5", "qualification_role_mismatch")])
def test_a_receipt_for_another_role_model_or_schema_does_not_qualify(w, field, value, reason):
    w.enable()
    w.qualify()
    w.default_mode("stop")
    path = next((w.run / "QUALIFICATIONS").glob("planner-*.json"))
    doc = json.loads(path.read_text())
    if value is None:
        del doc[field]
    else:
        doc[field] = value
    path.write_text(json.dumps(doc))
    assert w.kyloop("planner").returncode == 0
    assert reason in json.dumps(refused(w))


def test_the_installed_harness_judges_the_receipt_and_its_refusal_refuses_the_launch(w):
    """N-05: with kyqualify.py installed beside the controller, ITS check_receipt decides — given the role's launch
    configuration and the context the controller provably runs in."""
    w.enable()
    w.default_mode("stop")
    install_harness(w)
    w.qualify()                                             # the receipt now also binds the harness
    doc = json.loads(next((w.run / "QUALIFICATIONS").glob("planner-*.json")).read_text())
    assert doc["binds"]["harness_sha256"] == sha(w.fleet / "kyqualify.py")
    assert w.kyloop("planner").returncode == 0 and w.calls() == [1] and w.awaiting() == []
    call = json.loads((w.fleet / "kyqualify.calls").read_text().splitlines()[0])
    assert call["require_context"] == "shell" and call["role"] == "planner"
    cfg = json.loads(w.kyloop("admin", "launch-config", "planner").stdout)
    assert call["cfg"] == cfg and cfg["schema"] == "ky.launch_config/1"
    assert cfg["intended_tools"] == ["Read", "Write", "Edit", "Bash"] and cfg["denied_tools"] == []
    assert cfg["env_names"] == list(kyloop.CHILD_ENV_NAMES) and cfg["add_dirs"] == [str(w.root)]
    assert cfg["worktree"] == str(w.wt) and cfg["prompt_path"] == str(w.fleet / "prompts" / "PLANNER_LOOP_v2_4.md")
    assert w.loop_state()["qualification_check"]["mode"] == "kyqualify.check_receipt"
    # the same receipt, a harness that finds something: refused, by the harness's reason
    install_harness(w, 'return ["result: the receipt says PASS but its checks evaluate to unknown"]')
    w.qualify()
    w.rearm()
    assert w.kyloop("planner").returncode == 0
    a = json.dumps(refused_after_runs(w))
    assert "qualification_refused_by_harness" in a and "its checks evaluate to unknown" in a and w.calls() == [1]


@pytest.mark.parametrize("case,reason", [("raises", "qualification_harness_failed"),
                                         ("needs-more", "qualification_config_incomplete"),
                                         ("changed-since", "qualification_mismatch: harness_sha256"),
                                         ("broken", "qualification_harness_unloadable"),
                                         ("no-entry-point", "qualification_harness_unusable"),
                                         ("removed-since", "qualification_mismatch: harness_sha256")])
def test_a_harness_that_cannot_judge_has_accepted_nothing(w, case, reason):
    w.enable()
    w.default_mode("stop")
    install_harness(w, "raise RuntimeError('cannot judge')" if case == "raises" else "return []",
                    HARNESS_KEYS + ("denied_bash",) if case == "needs-more" else HARNESS_KEYS)
    w.qualify()
    if case == "changed-since":                             # another harness than the one the receipt was written by
        install_harness(w, "return []  # edited after qualification")
    elif case == "removed-since":                           # a receipt that binds a harness nobody can compare
        (w.fleet / "kyqualify.py").unlink()
    elif case == "broken":
        (w.fleet / "kyqualify.py").write_text("import a_module_that_is_not_there\n")
    elif case == "no-entry-point":
        (w.fleet / "kyqualify.py").write_text("CONFIG_KEYS = ()\n")
    if case in ("broken", "no-entry-point"):
        doc_path = next((w.run / "QUALIFICATIONS").glob("planner-*.json"))
        doc = json.loads(doc_path.read_text())
        doc["binds"]["harness_sha256"] = sha(w.fleet / "kyqualify.py")
        doc_path.write_text(json.dumps(doc))
    assert w.kyloop("planner").returncode == 0
    assert reason in json.dumps(refused(w))


def test_without_a_harness_the_controllers_own_comparison_decides_and_says_so(w):
    w.ready()
    w.modes("stop")
    assert w.kyloop("planner").returncode == 0 and w.calls() == [1]
    check = w.loop_state()["qualification_check"]
    assert check["mode"] == "controller_only" and check["context"] == "shell"
    assert check["receipt_sha256"] == sha(next((w.run / "QUALIFICATIONS").glob("planner-*.json")))


# ───────────────────────────── the test hooks say that they were used (N-06) ─────────────────────────────

def test_a_run_under_a_test_hook_says_so_in_its_run_record_and_in_the_loop_state(w):
    w.ready()
    w.modes("stop")
    assert w.kyloop("planner").returncode == 0
    rec, ls = w.records()[0], w.loop_state()
    assert rec["test_hooks"] == ls["test_hooks"] == {"sleep_scale": 0.001, "context_injected": None,
                                                    "context_injection_honoured": False}
    assert "test_hooks=active" in status_line(w, "planner")[0]
    w.qualify(context="test-hook:launchd")
    w.rearm()
    w.modes("stop")
    assert w.kyloop("planner", KY_LOOP_TEST_CONTEXT="launchd").returncode == 0
    assert w.calls() == [1, 2] and w.loop_state()["qualification_check"]["context"] == "test-hook:launchd"
    assert w.records()[1]["test_hooks"] == {"sleep_scale": 0.001, "context_injected": "launchd",
                                            "context_injection_honoured": True}


def test_at_the_production_scale_no_hook_is_recorded_and_an_injected_context_is_refused(w, monkeypatch):
    for name, value in w.env(KY_LOOP_SLEEP_SCALE="1").items():
        monkeypatch.setenv(name, value)
    c = kyloop.Controller("planner")
    assert c.test_hooks() is None and c.context() == "shell"
    monkeypatch.setenv("KY_LOOP_TEST_CONTEXT", "launchd")
    c = kyloop.Controller("planner")
    assert c.context() == "shell"                           # a launchd-labelled context is refused without the scale
    assert c.test_hooks() == {"sleep_scale": 1.0, "context_injected": "launchd", "context_injection_honoured": False}


@pytest.mark.parametrize("hook", [{"KY_LOOP_SLEEP_SCALE": "0.5"}, {"KY_LOOP_TEST_CONTEXT": "shell"},
                                  {"KY_LOOP_SLEEP_SCALE": "0.5", "KY_LOOP_TEST_CONTEXT": "launchd"}])
@pytest.mark.parametrize("role", ["planner", "veto"])
def test_a_controller_that_really_runs_under_launchd_refuses_every_test_hook(w, monkeypatch, hook, role):
    """What an installed plist must never carry: under launchd (parent pid 1, the loop's own label) a hook refuses."""
    w.qualify()
    c = controller_in_process(w, monkeypatch, role, **dict({"KY_LOOP_SLEEP_SCALE": "1"}, **hook))
    monkeypatch.setattr(kyloop.Controller, "real_context", lambda self: "launchd")
    with pytest.raises(kyloop.Refusal) as refusal:
        c.verify_veto() if role == "veto" else c.verify_launch()
    assert "test_hooks_in_launchd_context" in str(refusal.value)
    for name in hook:                                       # the control: without the hook that gate is silent
        monkeypatch.delenv(name)
    c = controller_in_process(w, monkeypatch, role, KY_LOOP_SLEEP_SCALE="1")
    try:
        c.verify_veto() if role == "veto" else c.verify_launch()
    except kyloop.Refusal as r:
        assert "test_hooks_in_launchd_context" not in str(r)


@pytest.mark.parametrize("injected", ["launchd", "shell"])
def test_an_injected_context_is_reported_as_a_hook_context_never_as_a_proven_one(w, monkeypatch, injected):
    """N3-04: a controller started from a shell with both test hooks set does not report `launchd` (or `shell`):
    a receipt earned in the real context does not qualify it."""
    c = controller_in_process(w, monkeypatch, "planner", KY_LOOP_TEST_CONTEXT=injected)
    assert c.scale < 1 and c.real_context() == "shell"
    assert c.context() == "test-hook:" + injected and c.context() not in ("launchd", "shell")
    w.qualify(context=injected)                             # a receipt that says the real context
    cfg, errs = c.load_config()
    assert not errs
    assert "qualification_context_mismatch" in json.dumps(c.check_qualification(cfg))
    w.qualify(context="test-hook:" + injected)              # the control: the same check passes for the hook context
    assert c.check_qualification(cfg) == []


def test_under_launchd_a_missing_harness_refuses_the_launch(w, monkeypatch):
    """N3-05: where the installed loops run, the receipt is judged by kyqualify.check_receipt or not at all."""
    c = controller_in_process(w, monkeypatch, "planner", KY_LOOP_SLEEP_SCALE="1")      # no harness beside it
    monkeypatch.setattr(kyloop.Controller, "real_context", lambda self: "launchd")
    w.qualify(context="launchd")
    cfg, errs = c.load_config()
    assert not errs
    reasons = c.check_qualification(cfg)
    assert len(reasons) == 1 and reasons[0].startswith("qualification_harness_missing") and c.qualification_check is None
    # the control: the same receipt and controller with a harness that accepts it
    calls = []
    harness = type("Harness", (), {"CONFIG_KEYS": (), "check_receipt": staticmethod(
        lambda doc, cfg, require_context=None: calls.append(require_context) or [])})
    monkeypatch.setattr(kyloop.Controller, "load_harness", lambda self: harness)
    assert c.check_qualification(cfg) == [] and calls == ["launchd"]
    assert c.qualification_check["mode"] == "kyqualify.check_receipt"


# ───────────────────────────── the dispatcher start (N-04) ─────────────────────────────

def dispatcher_start_items(w):
    return [a for a in w.awaiting() if a["id"].endswith("-loop-conductor-dispatcher-start")]


def conductor_until_waiting(w, **extra):
    p = w.popen("conductor", **extra)
    try:
        assert wait_for(lambda: (w.loop_state("conductor") or {}).get("waiting") == "no_eligible_work"
                        or p.poll() is not None)
        ls = w.loop_state("conductor")
        if p.poll() is None:
            stop_and_wait(w, p, "conductor")
    finally:
        p.kill()
    return ls


def test_the_conductor_starts_the_dispatcher_through_an_action_record(w):
    w.resume()
    w.ready("conductor")
    ls = conductor_until_waiting(w)
    (act,) = [a for a in kyaction.scan(w.run)[0] if a["kind"] == "dispatcher_start"]
    assert act["action_id"] == "DISPATCHER-START-" + ls["controller"]["controller_id"]
    assert act["state"] == "DONE" and act["result"] == {"rc": 0} and act["actor"]["role"] == "conductor"
    assert ls["dispatcher_start"]["rc"] == 0 and ls["dispatcher_start"]["action"] == act["action_id"]
    assert (w.lc / "loaded" / LABELS["dispatcher"]).exists() and w.loop_state("dispatcher")["enabled"] is True
    assert dispatcher_start_items(w) == []
    assert_schema("action", {k: v for k, v in act.items() if k != "process"})


@pytest.mark.parametrize("how", ["refused", "launchctl-fails"])
def test_a_dispatcher_start_that_fails_is_one_owner_wait_and_is_not_retried_blind(w, how):
    w.resume()
    w.ready("conductor")
    if how == "refused":
        (w.fleet / "kydispatch.py").unlink()                # kyctl.sh start dispatcher → REFUSED, exit 2
    else:
        plist(w, "dispatcher").unlink()                     # … → REFUSED plist-not-installed
    ls = conductor_until_waiting(w)
    (act,) = [a for a in kyaction.scan(w.run)[0] if a["kind"] == "dispatcher_start"]
    assert act["state"] == "FAILED" and act["result"] == {"rc": 2} and ls["dispatcher_start"]["rc"] == 2
    (item,) = dispatcher_start_items(w)
    assert item["blocks"] == "none" and item["item"] == "loop.dispatcher" and act["action_id"] in json.dumps(item)
    assert ls["enabled"] is True and ls["waiting"] == "no_eligible_work"       # the conductor went on
    n = len(w.lc_calls())
    w.rearm("conductor")
    ls = conductor_until_waiting(w)                         # a new controller: the item is still open → no blind retry
    assert "unconfirmed" in ls["dispatcher_start"]["skipped"] and len(dispatcher_start_items(w)) == 1
    assert len([a for a in kyaction.scan(w.run)[0] if a["kind"] == "dispatcher_start"]) == 1
    assert not any(c.startswith(("bootstrap", "kickstart")) for c in w.lc_calls()[n:])


@pytest.mark.parametrize("how", ["switch-off", "stop-file", "switch-unreadable"])
def test_a_dispatcher_the_owner_stopped_is_never_re_enabled_by_the_conductor(w, how):
    w.resume()
    w.ready("conductor")
    if how == "switch-off":                                 # the switch alone (no STOP file) used to be overridden
        assert w.kyloop("admin", "disable", "dispatcher", "--reason", "owner", "--by", "owner").returncode == 0
    elif how == "stop-file":
        w.stop_file("dispatcher").write_text("stopped by the owner")
    else:
        (w.run / "loops").mkdir(exist_ok=True)
        (w.run / "loops" / "dispatcher.json").write_text("{torn")
    before = (w.run / "loops" / "dispatcher.json").read_bytes() if how != "stop-file" else None
    ls = conductor_until_waiting(w)
    assert ls["dispatcher_start"]["skipped"].startswith({"switch-off": "disabled_by_switch", "stop-file": "stop_file_present",
                                                         "switch-unreadable": "dispatcher_switch_unreadable"}[how])
    assert not [a for a in kyaction.scan(w.run)[0] if a["kind"] == "dispatcher_start"]
    assert not any(c.startswith(("bootstrap", "kickstart")) for c in w.lc_calls())
    assert not (w.lc / "loaded" / LABELS["dispatcher"]).exists()
    if before is not None:
        assert (w.run / "loops" / "dispatcher.json").read_bytes() == before


def test_a_dispatcher_start_whose_exit_was_not_observed_is_settled_by_observation(w, monkeypatch):
    """An exit status that was not observed (the helper timed out) is never taken for success: what `kyctl.sh
    status` reports decides — running → done; stopped → failed; anything else → unknown, one owner-wait."""
    w.resume()
    w.ready("conductor")
    for name, value in w.env().items():
        monkeypatch.setenv(name, value)
    for n, (status, state) in enumerate((("dispatcher state=running pid=7", "DONE"),
                                         ("dispatcher state=stopped pid=-", "FAILED"),
                                         ("dispatcher state=unknown pid=-", "INTENDED"))):
        c = kyloop.Controller("conductor")
        c.controller_id += "-%d" % n
        c.load_siblings()
        for p in (w.run / "awaiting").glob("*dispatcher-start.json") if (w.run / "awaiting").is_dir() else []:
            p.unlink()
        monkeypatch.setattr(c, "run_helper", lambda name, args, timeout: 124)       # timed out
        monkeypatch.setattr(c, "observe_dispatcher", lambda record=None, s=status: (
            ("done", {"state": "running"}) if "running" in s else
            ("not_done", {"state": "stopped"}) if "stopped" in s else ("unknown", {"reason": "state=unknown"})))
        c.start_dispatcher()
        act = kyaction.load(w.run, "DISPATCHER-START-" + c.controller_id)
        assert act["state"] == state and act["reconciliations"][0]["outcome"] == {"DONE": "done", "FAILED": "not_done",
                                                                                 "INTENDED": "unknown"}[state]
        assert len(dispatcher_start_items(w)) == (0 if state == "DONE" else 1)
    assert kyloop.Controller("conductor").observe_dispatcher()[0] in ("not_done", "done", "unknown")


# ───────────────────────────── notifications are recorded side effects (N-04) ─────────────────────────────

def test_every_notification_is_wrapped_in_an_action_record(w):
    w.ready()
    w.default_mode("noprogress")
    assert w.kyloop("planner").returncode == 0              # three idle runs → the breaker notifies the owner once
    (act,) = [a for a in kyaction.scan(w.run)[0] if a["kind"] == "notification"]
    rec = w.records()[0]
    assert act["action_id"] == "NOTIFY-%s-1" % rec["controller_id"] and act["state"] == "DONE"
    assert act["actor"] == {"role": "planner", "holder_kind": "controller", "controller_id": rec["controller_id"]}
    assert act["result"] == {"notify": "dry", "rc": 0, "journal": "ok"}
    assert act["inputs"]["level"] == "decision" and act["inputs"]["message"] in w.cockpit_journal()
    last = w.loop_state()["last_notification"]
    assert last["action"] == act["action_id"] and "notify=dry" in last["result"]


@pytest.mark.parametrize("notifier,state,notify", [("fails", "FAILED", "failed"), ("missing", "FAILED", "unavailable")])
def test_a_notification_that_was_not_submitted_is_recorded_as_failed_never_as_made(w, notifier, state, notify):
    w.ready()
    w.default_mode("noprogress")
    if notifier == "missing":
        (w.fleet / "kynotify.sh").unlink()
    r = w.kyloop("planner", KY_NOTIFY_DRY="0", KY_OSASCRIPT=str(FIX / "fake_osascript"),
                 FAKE_OSASCRIPT_LOG=str(w.tmp / "o"), FAKE_OSASCRIPT_RC="1")
    assert r.returncode == 0
    (act,) = [a for a in kyaction.scan(w.run)[0] if a["kind"] == "notification"]
    assert act["state"] == state and act["result"]["notify"] == notify
    if notifier == "fails":
        assert w.cockpit_journal().endswith(" [notify=failed]\n")


def test_a_notification_a_dead_controller_began_is_reconciled_from_the_journal(w):
    w.ready()
    w.modes("stop")
    previous = {"role": "planner", "holder_kind": "controller", "controller_id": OLD_CTL}
    target = {"journal": str(w.run / "JOURNAL_COCKPIT.md"), "channel": "kynotify.sh"}
    kyaction.begin(w.run, "NOTIFY-%s-1" % OLD_CTL, "notification", previous,
                   {"level": "decision", "message": "planner loop stopped: it was journaled"}, target, "notify")
    kyaction.begin(w.run, "NOTIFY-%s-2" % OLD_CTL, "notification", previous,
                   {"level": "info", "message": "planner loop: this one never reached the journal"}, target, "notify")
    for n in (1, 2):
        left_by_a_dead_process(w, "NOTIFY-%s-%d" % (OLD_CTL, n))
    (w.run / "JOURNAL_COCKPIT.md").write_text(
        "- 2026-01-01T00:00:00Z [decision] planner loop stopped: it was journaled [notify=submitted]\n")
    assert w.kyloop("planner").returncode == 0
    one, two = (kyaction.load(w.run, "NOTIFY-%s-%d" % (OLD_CTL, n)) for n in (1, 2))
    assert one["state"] == "DONE" and one["result"]["notify"] == "submitted" and one["result"]["reconciled"] is True
    assert two["state"] == "DONE" and two["result"]["notify"] == "dry"      # positively absent: submitted now, once
    assert w.cockpit_journal().count("this one never reached the journal") == 1
    assert w.cockpit_journal().count("it was journaled") == 1 and w.calls() == [1] and w.awaiting() == []


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


# ───────────────────────────── B-0c part 2: L2-a … L2-d ─────────────────────────────

# L2-a — a message another actor holds locked is waited for in the controller; it is never a second look at once

def conductor_with_inbox(w, *ids):
    w.resume()
    w.ready("conductor")
    w.default_mode("ack")
    (w.root / "fake_ky" / "inbox.S.json").write_text(json.dumps([{"msg_id": m, "detail": "do " + m} for m in ids]))


def lock_waits(w):
    return ((w.loop_state("conductor") or {}).get("counters") or {}).get("item_lock_waits", 0)


def test_a_message_locked_by_another_live_actor_is_waited_for_in_the_controller_and_never_relaunched(w):
    conductor_with_inbox(w, "M1")
    other = kyaction.acquire_lock(w.run, "msg.M1", "another-actor")        # this test process: alive, and not us
    assert other is not None
    p = w.popen("conductor")
    try:
        assert wait_for(lambda: (w.loop_state("conductor") or {}).get("waiting") == "items_locked")
        assert wait_for(lambda: lock_waits(w) >= 3)         # pass after pass it WAITS: a counted waiting state
        ls = w.loop_state("conductor")
        assert p.poll() is None and ls["enabled"] is True and ls["breaker"]["open"] is False
        assert ls["item_lock_wait"]["items"] == ["msg.M1"] and ls["no_progress_count"] == 0
        assert ls["counters"].get("launches", 0) == 0 and ls["expected_child"] is None
        assert w.calls() == [] and w.records("conductor") == [] and w.awaiting() == []     # nothing was launched
        assert not list((w.run / "actions").glob("LAUNCH-*")) if (w.run / "actions").is_dir() else True
        assert json.loads((w.run / "locks" / "msg.M1" / "owner.json").read_text())["session_or_run_id"] == "another-actor"
        assert kyaction.release_lock(other)                 # the other actor is done and did not handle it
        assert wait_for(lambda: w.calls() == [1])           # … and only now is ONE job launched for it
        assert wait_for(lambda: (w.loop_state("conductor") or {}).get("waiting") == "no_eligible_work")
        stop_and_wait(w, p, "conductor")
    finally:
        p.kill()
    (rec,) = w.records("conductor")
    assert [i["id"] for i in rec["work_items"]] == ["msg.M1"] and w.calls() == [1]


def test_a_message_lock_nobody_can_judge_is_waited_for_with_one_attention_item_and_never_taken_over(w):
    conductor_with_inbox(w, "M1")
    (w.run / "locks" / "msg.M1").mkdir(parents=True)       # a bare lock: no owner record at all
    p = w.popen("conductor")
    try:
        assert wait_for(lambda: lock_waits(w) >= 3)
        assert w.loop_state("conductor")["waiting"] == "items_locked" and p.poll() is None
        stop_and_wait(w, p, "conductor")
    finally:
        p.kill()
    assert w.calls() == [] and w.records("conductor") == []
    (item,) = w.awaiting()                                  # ONE item, however many passes waited
    assert item["id"].endswith("-lock-owner-unknown-msg-m1") and item["blocks"] == "none"
    assert (w.run / "locks" / "msg.M1").is_dir() and not (w.run / "locks" / "msg.M1" / "owner.json").exists()


def test_an_unlocked_message_is_launched_without_waiting_for_the_locked_one(w):
    """The negative of the wait: `items_locked` is the state of a pass that could launch NOTHING — not of a pass
    in which one message of several is held by somebody else."""
    conductor_with_inbox(w, "M1", "M2")
    other = kyaction.acquire_lock(w.run, "msg.M1", "another-actor")
    p = w.popen("conductor")
    try:
        assert wait_for(lambda: w.calls() == [1] and len(w.records("conductor")) == 1
                        and w.records("conductor")[0]["ended_at"] is not None)
        assert [i["id"] for i in w.records("conductor")[0]["work_items"]] == ["msg.M2"]
        assert wait_for(lambda: lock_waits(w) >= 1)         # M2 is handled; M1 is still somebody else's: now it waits
        stop_and_wait(w, p, "conductor")
    finally:
        p.kill()
        kyaction.release_lock(other)
    assert w.calls() == [1]


def test_run_job_says_items_locked_only_when_a_lock_kept_everything_back(w, monkeypatch):
    conductor_with_inbox(w, "M1")
    c = controller_in_process(w, monkeypatch, "conductor")
    c.load_siblings()
    c.cfg = {}
    item = {"id": "msg.M1", "kind": "message", "key": "M1", "stream": "S", "message": {"msg_id": "M1"}}
    other = kyaction.acquire_lock(w.run, "msg.M1", "another-actor")
    assert c.run_job([item]) == "items_locked" and c.items_waiting == ["msg.M1"]
    kyaction.release_lock(other)
    (w.run / "handled").mkdir()
    (w.run / "handled" / "msg.M1.json").write_text("{}")   # handled meanwhile: nothing to wait for, nothing launched
    assert c.run_job([item]) is None and c.items_waiting == [] and w.calls() == []
    assert not (w.run / "locks" / "msg.M1").exists()


# L2-b — the veto controller applies its own role's commands; `veto <decision-id>` stays the handler's

def test_the_veto_controller_applies_its_own_roles_queued_commands_and_a_queued_stop_ends_the_loop(w):
    veto_world(w)
    w.enable("veto")
    status = submit(w, "veto", "status")
    other = submit(w, "veto", "priority", {"item": "B-4"})             # not a thing the veto role can carry out
    foreign = submit(w, "veto", "loops", {"op": "stop", "loop": "planner"})
    stop = submit(w, "veto", "loops", {"op": "stop", "loop": "veto"})
    r = w.kyloop("veto")
    assert r.returncode == 0, r.stderr                      # the owner's queued stop ended the loop
    docs = {c: command(w, c) for c in (status, other, foreign, stop)}
    assert [docs[c]["state"] for c in (status, other, foreign, stop)] == ["APPLIED", "REJECTED", "REJECTED", "APPLIED"]
    for d in docs.values():
        assert d["applied_by"]["role"] == "veto" and d["applied_by"]["holder_kind"] == "controller"
        assert re.fullmatch(r"CTL-VETO-\d{8}T\d{6}Z-\d+", d["applied_by"]["controller_id"])
        assert_schema("command", d)
    assert docs[status]["result"]["line"].startswith("veto state=") and docs[status]["result"]["facts"]["enabled"] == "true"
    assert docs[other]["result"]["reason"].startswith("unsupported_by_veto_role: priority")
    assert docs[foreign]["result"]["reason"].startswith("not_this_roles_loop")
    assert "unsupported_by_veto_handler" not in json.dumps(list(docs.values()))
    ls = w.loop_state("veto")
    assert ls["enabled"] is False and ls["disabled_by_command"] == stop and stop in ls["reason"]
    assert ls["commands"]["applied"] == 2 and ls["commands"]["rejected"] == 2
    assert "veto" not in ls                                 # stopped before a single tick
    assert not w.stop_file("veto").exists() and w.awaiting() == [] and not (w.run / "locks" / "veto").exists()
    assert kyaction.load(w.run, "CMD-" + stop)["state"] == "DONE"
    before = {c: kycommands.find(w.run, c)["path"].read_bytes() for c in docs}
    w.enable("veto")                                        # a restart applies nothing a second time
    p = w.popen("veto")
    try:
        assert wait_for(lambda: veto_summary(w).get("ticks", 0) >= 2)
        stop_and_wait(w, p, "veto")
    finally:
        p.kill()
    assert before == {c: kycommands.find(w.run, c)["path"].read_bytes() for c in docs}


def test_a_veto_command_is_never_applied_by_the_controller_itself(w, monkeypatch):
    """The negative: of the veto role's queue the controller leaves `veto <decision-id>` exactly as it found it —
    that one is consumed by the handler's tick, under the decision's lock."""
    veto_world(w)
    w.enable("veto")
    sid, _ = propose(w, expires_in=3600, tracker=False)
    veto = submit(w, "veto", "veto", {"decision_id": sid})
    status = submit(w, "veto", "status")
    c = controller_in_process(w, monkeypatch, "veto")
    assert c.acquire()
    try:
        c.prepare()
        before = kycommands.find(w.run, veto)["path"].read_bytes()
        assert c.apply_commands() is True                   # the status behind it was settled, out of order
        assert command(w, status)["state"] == "APPLIED" and command(w, veto)["state"] == "QUEUED"
        assert kycommands.find(w.run, veto)["path"].read_bytes() == before
        assert not (w.run / "actions" / ("CMD-%s.json" % veto)).exists() and states(w, sid) == ["PENDING_VETO"]
        assert (w.run / "actions" / ("CMD-%s.json" % status)).exists()
        assert c.apply_commands() is False                  # nothing of its own is left: the tick may run
        assert [d["id"] for d in kycommands.pending(w.run, "veto")] == [veto]
    finally:
        c.release_lock()


def test_a_stop_queued_while_the_veto_loop_waits_is_applied_before_the_next_tick(w, monkeypatch):
    veto_world(w)
    w.enable("veto")
    queued, ticks = [], []
    with Signals():
        c = controller_in_process(w, monkeypatch, "veto")

        def tick():
            ticks.append(c.ls().get("enabled"))
            return {"decisions": [], "problems": [], "commands": [], "holds": [], "attention": False}

        def wait_for_event(deadline, seen):                 # the owner queues the stop while the controller waits
            queued.append(submit(w, "veto", "loops", {"op": "stop", "loop": "veto"}))

        monkeypatch.setattr(c, "tick", tick)
        monkeypatch.setattr(c, "wait_for_event", wait_for_event)
        assert c.main() == 0
    assert ticks == [True] and len(queued) == 1             # ONE tick; the stop was honoured before a second one
    assert command(w, queued[0])["state"] == "APPLIED"
    ls = w.loop_state("veto")
    assert ls["enabled"] is False and ls["disabled_by_command"] == queued[0] and ls["controller"] is None
    assert w.awaiting() == [] and not w.stop_file("veto").exists() and not (w.run / "locks" / "veto").exists()


# L2-c — kylock.sh: one function runs it, its exit codes are read one by one, and the child is given to it

FAKE_KYLOCK = """#!/bin/bash
# Test double for kylock.sh (packet KV3-B-KYLOCK call forms): records its argv in <script>.calls and exits with
# the integer in <script>.rc.<verb>, else <script>.rc, else 0; sleeps <script>.sleep seconds first when present.
set -u
printf '%s\\n' "$*" >> "$0.calls"
if [ -f "$0.sleep" ]; then sleep "$(cat "$0.sleep")"; fi
if [ -s "$0.seq.$1" ]; then                      # one exit code per call, first line first; then the files below
  rc="$(head -n 1 "$0.seq.$1")"; tail -n +2 "$0.seq.$1" > "$0.seq.tmp"; mv "$0.seq.tmp" "$0.seq.$1"; exit "$rc"
fi
if [ -f "$0.rc.$1" ]; then exit "$(cat "$0.rc.$1")"; fi
if [ -f "$0.rc" ]; then exit "$(cat "$0.rc")"; fi
echo "kylock: $1 role=$2 state=ok holder=$3 pid=0"
exit 0
"""


def fake_kylock(w, **rcs):
    path = w.fleet / "kylock.sh"
    path.write_text(FAKE_KYLOCK)
    path.chmod(0o755)
    for verb, rc in rcs.items():
        (w.fleet / ("kylock.sh.rc." + verb)).write_text(str(rc))
    return path


def kylock_calls(w):
    p = w.fleet / "kylock.sh.calls"
    return p.read_text().splitlines() if p.exists() else []


def test_kylock_is_one_function_that_answers_none_while_kylock_is_not_installed(w, monkeypatch):
    c = controller_in_process(w, monkeypatch)
    assert c.kylock("acquire") is None                      # not installed: the built-in lock is what holds the role
    (w.fleet / "kylock.sh").write_text(FAKE_KYLOCK)
    (w.fleet / "kylock.sh").chmod(0o644)
    assert c.kylock("acquire") is None and kylock_calls(w) == []       # present but not executable: not installed
    assert c.acquire_lock() and c.lock_mode == "builtin" and (w.run / "locks" / "planner" / "owner.json").exists()
    c.release_lock()
    assert not (w.run / "locks" / "planner").exists() and kylock_calls(w) == []
    fake_kylock(w)
    assert c.kylock("acquire")[:2] == ("ok", 0)
    assert c.kylock("child", "pending")[:2] == ("ok", 0)
    assert kylock_calls(w) == ["acquire planner " + c.controller_id, "child planner %s pending" % c.controller_id]
    for rc, outcome in ((75, "live"), (76, "cockpit"), (77, "unknown"), (74, "release_unproven"), (73, "not_owner"),
                        (70, "bad_identity"), (64, "usage"), (1, "error"), (2, "error"), (127, "error")):
        (w.fleet / "kylock.sh.rc").write_text(str(rc))
        assert c.kylock("acquire")[:2] == (outcome, rc)     # every non-zero code is its own answer, none a success
    (w.fleet / "kylock.sh.rc").unlink()
    (w.fleet / "kylock.sh.sleep").write_text("5")
    t0 = time.time()
    assert c.kylock("acquire", timeout=0.3)[:2] == ("error", None) and time.time() - t0 < 4       # no answer: no lock


KYLOCK_REFUSALS = [
    (75, None, None, "live"),                               # a live holder: a duplicate start, nothing recorded
    (76, "role_held_by_cockpit", None, "cockpit"),
    (77, "role_lock_owner_unknown", "-loop-planner-lock-owner-unknown", "unknown"),
    (70, "role_lock_identity_refused", "-loop-planner-lock-helper-refused", "identity_refused"),
    (74, "role_lock_helper_failed", "-loop-planner-lock-helper-refused", "kylock_error"),   # not an acquire answer
    (1, "role_lock_helper_failed", "-loop-planner-lock-helper-refused", "kylock_error"),
]


@pytest.mark.parametrize("rc,waiting,slug,state", KYLOCK_REFUSALS, ids=["rc%d" % x[0] for x in KYLOCK_REFUSALS])
def test_kylocks_acquire_exit_codes_are_told_apart(w, rc, waiting, slug, state):
    w.ready()
    w.default_mode("stop")
    fake_kylock(w, acquire=rc)
    r = w.kyloop("planner")
    assert r.returncode == 0 and w.calls() == [] and "rc=%d" % rc in r.stderr
    assert len(kylock_calls(w)) == 1 and kylock_calls(w)[0].startswith("acquire planner CTL-PLANNER-")
    assert not w.stop_file().exists() and w.loop_state()["enabled"] is True    # it never stops what it does not hold
    ls = w.loop_state()
    assert ls.get("waiting") == waiting
    if waiting is None:
        assert "lock_wait" not in ls and w.awaiting() == []
    else:
        assert ls["lock_wait"]["state"] == state and ls["lock_wait"]["kylock_rc"] == rc
        assert [a["id"][len("AW-20261011T000000Z"):] for a in w.awaiting()] == ([slug] if slug else [])
    assert w.kyloop("planner").returncode == 0              # a second refused start raises nothing new
    assert len(w.awaiting()) == (1 if slug else 0) and w.calls() == []


def test_the_veto_controller_waits_for_a_live_kylock_holder_and_for_no_other_answer(w, monkeypatch):
    """75 (a live holder: another handler's tick) is waited for, bounded; a cockpit (76) and an unknown owner (77)
    are not: no other answer of kylock.sh is a reason to try again."""
    veto_world(w)
    monkeypatch.setattr(kyloop, "VETO_LOCK_WAIT_S", 60000.0)           # 60 s at the test scale: never the limit here
    fake_kylock(w)
    c = controller_in_process(w, monkeypatch, "veto")
    (w.fleet / "kylock.sh.seq.acquire").write_text("75\n75\n75\n")
    assert c.acquire() is True and c.lock_mode == "kylock"
    assert [x.split()[0] for x in kylock_calls(w)] == ["acquire"] * 4      # three refusals waited for, then acquired
    c.release_lock()
    for rc, state in ((76, "cockpit"), (77, "unknown"), (70, "identity_refused"), (1, "kylock_error")):
        (w.fleet / "kylock.sh.calls").unlink()
        (w.fleet / "kylock.sh.seq.acquire").write_text("%d\n" % rc)       # a second try would be given the lock
        c = controller_in_process(w, monkeypatch, "veto")
        assert c.acquire() is False and c.lock_refusal["state"] == state and len(kylock_calls(w)) == 1


def test_the_child_is_given_to_kylock_before_and_after_it_is_started(w):
    w.ready()
    w.modes("stop")
    fake_kylock(w)
    assert w.kyloop("planner").returncode == 0 and w.calls() == [1]
    (rec,) = w.records()
    ctl = rec["controller_id"]
    calls = kylock_calls(w)
    assert calls[0] == "acquire planner " + ctl and calls[1] == "child planner %s pending" % ctl
    assert calls[3:] == ["child planner %s none" % ctl, "release planner " + ctl]
    prefix = "child planner %s " % ctl
    assert calls[2].startswith(prefix)
    child = json.loads(calls[2][len(prefix):])              # exactly the packet's keys, and the run's own identity
    assert child == {"run_id": rec["run_id"], "pid": rec["pid"], "pgid": rec["pgid"],
                     "process_start": rec["process_start"]}
    assert "lock_release" not in w.loop_state() and len(w.awaiting()) == 0


@pytest.mark.parametrize("rc", [73, 77, 1])
def test_nothing_is_launched_when_kylock_will_not_record_the_pending_child(w, rc):
    w.ready()
    w.default_mode("substep")
    fake_kylock(w, child=rc)
    r = w.kyloop("planner")
    assert r.returncode == 0 and "Traceback" not in r.stderr
    assert "role_lock_child_not_recorded: kylock.sh child pending" in json.dumps(refused(w))     # … and no model run
    (rec,) = w.records()
    assert rec["pid"] is None and rec["ended_reason"] == "launch_failed"
    assert kyaction.load(w.run, "LAUNCH-" + rec["run_id"])["state"] != "INTENDED"     # not left as a launch in doubt
    assert w.loop_state()["expected_child"] is None
    assert [c.split()[0] for c in kylock_calls(w)].count("release") == 1


RELEASES = [(74, "kept", True), (1, "unknown", True), (73, "not_owner", False)]


@pytest.mark.parametrize("rc,state,raised", RELEASES, ids=["rc%d" % x[0] for x in RELEASES])
def test_a_release_kylock_did_not_confirm_is_never_reported_as_released(w, rc, state, raised):
    w.ready()
    w.modes("stop")
    fake_kylock(w, release=rc)
    r = w.kyloop("planner")
    assert r.returncode == 0 and w.calls() == [1] and "NOT released by kylock.sh" in r.stderr
    note = w.loop_state()["lock_release"]
    assert (note["state"], note["kylock_rc"]) == (state, rc) and note["controller_id"] == w.records()[0]["controller_id"]
    items = [a for a in w.awaiting() if a["id"].endswith("-loop-planner-lock-release-unproven")]
    assert len(items) == (1 if raised else 0)
    if rc == 74:                                            # KU-02: the lock is kept, the databases are named
        assert "KEPT the role lock" in items[0]["question"] and note["controller_id"] in json.dumps(items[0])
        assert_awaiting_schema(items[0])
    (w.fleet / "kylock.sh.rc.release").unlink()             # the next controller's own start and clean release
    w.rearm()
    w.modes("stop")
    assert w.kyloop("planner").returncode == 0 and w.calls() == [1, 2]
    assert "lock_release" not in w.loop_state()             # … withdraw the observation; the item stays the owner's
    assert len([a for a in w.awaiting() if a["id"].endswith("-lock-release-unproven")]) == (1 if raised else 0)


# L2-d — the authority is part of what must change before a veto loop stopped for attention ticks again

def test_the_attention_fingerprint_changes_with_the_authority_and_with_nothing_else_unrecorded(w, monkeypatch):
    veto_world(w, authorised=False)
    c = controller_in_process(w, monkeypatch, "veto")
    unknown = c.attention_fingerprint()
    assert c.attention_fingerprint() == unknown             # nothing changed: the same fingerprint
    (w.run / "KY_WORKERS").write_text("9\n")                # not evidence of this stop
    assert c.attention_fingerprint() == unknown
    veto_world(w)                                           # the authorised source is recorded
    known = c.attention_fingerprint()
    assert known != unknown and c.attention_fingerprint() == known
    w.write_state({"active": {}, "completed_steps": [], "authorised_source": {"source_commit": C2, "entrypoints_digest": E1}})
    assert c.attention_fingerprint() not in (known, unknown)        # another bundle is another authority
    veto_world(w, authorised=False)
    assert c.attention_fingerprint() == unknown             # … and it is a function of what is recorded, only


def test_a_veto_stop_taken_without_an_authority_lifts_when_the_authority_returns(w, monkeypatch):
    veto_world(w, authorised=False)
    w.enable("veto")
    c = controller_in_process(w, monkeypatch, "veto")
    c.load_siblings()
    c.open_attention(["SD-20261011T220000Z-1: blocked (error: the bundle could not be read)"])
    ls = w.loop_state("veto")
    assert ls["breaker"]["open"] is True and ls["enabled"] is False and len(w.awaiting()) == 1
    assert c.attention_gate(c.ls()) is True                 # nothing changed: the restart is refused
    assert c.attention_gate(c.ls()) is True and w.loop_state("veto")["breaker"]["open"] is True
    veto_world(w)                                           # the authority returns — and nothing else changed
    assert c.attention_gate(c.ls()) is False
    ls = w.loop_state("veto")
    assert ls["breaker"]["open"] is False and ls["breaker"]["history"][-1]["from"] != ls["breaker"]["history"][-1]["to"]


# ═════════════════════════ an answered owner-wait has an end, on both sides (R15, L4-01) ═════════════════════════
#
# (1) an owner-wait with the OWNER's decision beside it no longer blocks its item or its loop; (2) the controller
# that applies the `decide` writes the decision first and then closes the item (run/awaiting/done/), and for its
# own job-action item carries the chosen option out; (3) the answer is a changed dependency; (4) nothing but an
# owner `decide` is an answer — a record no such command stands behind (a surrogate's, a job's) releases nothing.

def job_wait(w, slug, item, role="planner", blocks="item", class_hint="routine", job_id="PLANNER-20261011T000000Z"):
    """An owner-wait exactly as a job of `role` writes it (prompt item 6). → its id."""
    (w.run / "awaiting").mkdir(exist_ok=True)
    aid = "AW-20261011T000000Z-" + slug
    doc = {"schema": "ky.awaiting/1", "id": aid, "created_at": "2026-10-11T00:00:00Z",
           "raised_by": {"role": role, "session_id": "session-of-%s" % role, "job_id": job_id}, "item": item,
           "question": "May %s go on?" % item, "options": [{"id": "yes", "text": "Go on."}, {"id": "no", "text": "Stop."}],
           "recommendation": "yes", "evidence": [], "deadline": None, "class_hint": class_hint, "blocks": blocks}
    assert_awaiting_schema(doc)
    (w.run / "awaiting" / (aid + ".json")).write_text(json.dumps(doc))
    return aid


def wait_paths(w, aid):
    """(the open item, the owner's decision beside it, the item once it is closed)."""
    d = w.run / "awaiting"
    return d / (aid + ".json"), d / (aid + ".owner_decision.json"), d / "done" / (aid + ".json")


@contextlib.contextmanager
def lock_holder(w, monkeypatch, role="planner"):
    """A controller of the test world in this process that HOLDS its role lock — the fenced owner kycommands.apply
    asks for — without running its loop."""
    c = controller_in_process(w, monkeypatch, role)
    c.load_siblings()
    assert c.acquire_lock()
    c.state_sha = kyloop.sha_file(c.state_path)
    try:
        yield c
    finally:
        c.release_lock()


def eligible(c):
    return [i["id"] for i in c.eligible_items()]


def work_items(rec):
    return [i["id"] for i in json.loads((Path(rec["prompt_path"]).parent / "job.json").read_text())["work_items"]]


def decision_record(aid, cid, answer="yes", **over):
    """What record_owner_decision writes beside an item, as far as its readers look."""
    rec = {"schema": "ky.owner_decision/1", "awaiting_id": aid, "answer": answer, "command_id": cid,
           "from": dict(COCKPIT, pid=1, process_start=None), "command_created_at": "2026-10-11T00:00:00Z",
           "applied_at": "2026-10-11T00:00:01Z", "applied_by": {"role": "planner", "controller_id": OLD_CTL},
           "awaiting_sha256": "0" * 64}
    rec.update(over)
    return rec


def test_an_item_level_wait_the_owner_answered_no_longer_blocks_its_item(w, monkeypatch):
    """L4-01, item level: the planner-job wait on B-3 of the reviewer's probe. Unanswered it blocks B-3 (and B-3
    only); a `decide` that is merely queued is not an answer yet; once the controller has applied it the decision
    lies beside where the item was, the item itself is closed, and B-3 is work again."""
    w.ready()
    aid = job_wait(w, "b-3-question", "B-3")
    item, answer, closed = wait_paths(w, aid)
    asked = item.read_bytes()
    with lock_holder(w, monkeypatch) as c:
        assert eligible(c) == ["step.B-4"] and c.awaiting_blocks() == (False, {"B-3"}, [aid])
        cid = submit(w, "planner", "decide", {"awaiting_id": aid, "answer": "yes: go on"})
        assert eligible(c) == ["step.B-4"]                  # queued, not applied: nothing is recorded as answered
        assert c.apply_commands() is True
        assert eligible(c) == ["step.B-3", "step.B-4"] and c.awaiting_blocks() == (False, set(), [])
    doc = command(w, cid)
    assert doc["state"] == "APPLIED" and kyaction.load(w.run, "CMD-" + cid)["state"] == "DONE"
    od = json.loads(answer.read_text())
    assert od["schema"] == "ky.owner_decision/1"
    assert (od["awaiting_id"], od["answer"], od["command_id"]) == (aid, "yes: go on", cid)
    assert od["applied_by"]["role"] == "planner" and {k: od["from"].get(k) for k in COCKPIT} == COCKPIT
    # the item is closed by the controller that applied the answer — moved, byte for byte, never deleted
    assert not item.exists() and closed.read_bytes() == asked and od["awaiting_sha256"] == sha(closed)
    assert doc["result"]["closed"] == str(closed) and doc["result"]["owner_decision"] == str(answer)
    # … and the record says what was asked, for the job that reads `<awaiting_dir>/<id>.owner_decision.json`
    assert od["wait"]["item"] == "B-3" and od["wait"]["blocks"] == "item" and od["wait"]["class_hint"] == "routine"
    assert od["wait"]["question"] == "May B-3 go on?" and [o["id"] for o in od["wait"]["options"]] == ["yes", "no"]
    assert w.awaiting() == [] and not list((w.run / "locks").glob("awaiting.*"))


def test_a_loop_level_wait_the_owner_answered_no_longer_blocks_the_loop(w, monkeypatch):
    """L4-01, loop level: the answered `blocks: loop` wait of the reviewer's probe left nothing eligible."""
    w.ready()
    aid = job_wait(w, "planner-loop-question", "B-3", blocks="loop")
    with lock_holder(w, monkeypatch) as c:
        assert eligible(c) == [] and c.awaiting_blocks() == (True, set(), [aid])
        cid = submit(w, "planner", "decide", {"awaiting_id": aid, "answer": "yes"})
        assert c.apply_commands() is True
        assert eligible(c) == ["step.B-3", "step.B-4"] and c.awaiting_blocks() == (False, set(), [])
    assert command(w, cid)["state"] == "APPLIED" and wait_paths(w, aid)[2].exists() and w.awaiting() == []


def test_a_running_loop_leaves_no_eligible_work_when_the_owner_answers_its_loop_level_wait(w):
    """The whole path in the real controller: it waits (no model, `no_eligible_work`) while the wait is open, and
    the owner's queued `decide` — applied at the top of its next look — is what ends that wait."""
    w.ready()
    w.default_mode("stop")
    aid = job_wait(w, "planner-loop-question", "B-3", blocks="loop")
    p = w.popen("planner")
    try:
        assert wait_for(lambda: (w.loop_state() or {}).get("waiting") == "no_eligible_work")
        time.sleep(0.3)
        assert w.calls() == [] and p.poll() is None         # an unanswered wait still blocks, in the controller
        cid = submit(w, "planner", "decide", {"awaiting_id": aid, "answer": "yes"})
        assert p.wait(timeout=15) == 0
    finally:
        p.kill()
    assert command(w, cid)["state"] == "APPLIED" and w.calls() == [1]
    assert work_items(w.records()[0]) == ["step.B-3", "step.B-4"]
    assert w.awaiting() == [] and wait_paths(w, aid)[2].exists()


def test_the_owners_answer_to_a_wait_a_job_raised_puts_that_item_back_to_work(w):
    """End to end with the wait a JOB wrote: run 1 raises it for B-3, run 2 goes on with B-4 only; after the
    owner's `decide` the next job is given B-3 again — the step, and B-5 behind it, can run."""
    w.ready()
    w.modes("await", "stop")
    assert w.kyloop("planner").returncode == 0
    (aw,) = w.awaiting()
    assert aw["item"] == "B-3" and work_items(w.records()[1]) == ["step.B-4"]
    cid = submit(w, "planner", "decide", {"awaiting_id": aw["id"], "answer": "a"})
    w.rearm()
    w.modes("stop")
    assert w.kyloop("planner").returncode == 0
    assert command(w, cid)["state"] == "APPLIED" and len(w.records()) == 3
    assert work_items(w.records()[2]) == ["step.B-3", "step.B-4"]
    assert w.awaiting() == [] and wait_paths(w, aw["id"])[2].exists()
    assert json.loads(wait_paths(w, aw["id"])[1].read_text())["wait"]["question"] == aw["question"]


NOT_AN_ANSWER = ["wrong-awaiting-id", "wrong-schema", "not-an-object", "torn", "no-such-command", "not-a-decide",
                 "decide-for-another-item", "another-answer", "rejected-decide"]


@pytest.mark.parametrize("blocks", ["item", "loop"])
@pytest.mark.parametrize("case", NOT_AN_ANSWER)
def test_a_record_that_is_not_the_owners_answer_to_that_wait_releases_nothing(w, monkeypatch, case, blocks):
    """R15 (1), the negatives: a file named like an answer is one only when it is a ky.owner_decision/1 naming THAT
    awaiting id and the queue holds the owner's `decide` it names — for that id, with that answer, not rejected.
    Anything else still blocks. And it is no dead end: the owner's real `decide` is applied over it (the stray
    record is kept, set aside) and releases the wait."""
    w.ready()
    aid = job_wait(w, "b-3-question", "B-3", blocks=blocks)
    other = job_wait(w, "k9-23-question", "K9-23")
    item, answer, closed = wait_paths(w, aid)
    blocked = ([], (True, {"K9-23"}, sorted([aid, other]))) if blocks == "loop" else \
        (["step.B-4"], (False, {"B-3", "K9-23"}, sorted([aid, other])))
    queued = None
    if case in ("wrong-awaiting-id", "wrong-schema", "another-answer"):
        queued = submit(w, "planner", "decide", {"awaiting_id": aid, "answer": "yes"})
        rec = decision_record(aid, queued, **{"wrong-awaiting-id": {"awaiting_id": other},
                                             "wrong-schema": {"schema": "ky.owner_decision/2"},
                                             "another-answer": {"answer": "no"}}[case])
    elif case == "no-such-command":
        rec = decision_record(aid, "000001-decide-ffffff")
    elif case == "not-a-decide":
        rec = decision_record(aid, submit(w, "campaign", "resume"))
    elif case == "decide-for-another-item":
        rec = decision_record(aid, submit(w, "conductor", "decide", {"awaiting_id": other, "answer": "yes"}))
    elif case == "rejected-decide":
        cid = submit(w, "planner", "decide", {"awaiting_id": aid, "answer": "yes"})
        path = kycommands.find(w.run, cid)["path"]
        path.write_text(json.dumps(dict(json.loads(path.read_text()), state="REJECTED",
                                        result={"reason": "not_this_roles_item"})))
        rec = decision_record(aid, cid)
    else:
        rec = [1, 2] if case == "not-an-object" else None
    answer.write_text("{torn" if case == "torn" else json.dumps(rec))
    stray = answer.read_bytes()
    with lock_holder(w, monkeypatch) as c:
        assert (eligible(c), c.awaiting_blocks()) == blocked            # it still blocks, and still counts as open
        cid = queued or submit(w, "planner", "decide", {"awaiting_id": aid, "answer": "yes"})
        assert c.apply_commands() is True
        assert command(w, cid)["state"] == "APPLIED", command(w, cid)
        assert eligible(c) == ["step.B-3", "step.B-4"]
    od = json.loads(answer.read_text())
    assert (od["schema"], od["awaiting_id"], od["answer"], od["command_id"]) == ("ky.owner_decision/1", aid, "yes", cid)
    (aside,) = (w.run / "awaiting" / "done").glob(aid + ".owner_decision.set_aside.*")
    assert aside.read_bytes() == stray and command(w, cid)["result"]["set_aside"] == str(aside)
    assert not item.exists() and closed.exists()


SURROGATE = {"kind": "surrogate", "session_id": "kalayantra-owner-surrogate-1"}


def test_only_an_owner_decide_releases_a_hard_stop_wait(w, monkeypatch):
    """R15 (4). A hard stop is the owner's alone: what the surrogate records about it, a decision the surrogate
    writes beside it and a `decide` it queues under its own name all leave it blocking; the owner's `decide`
    releases it."""
    w.ready()
    aid = job_wait(w, "frozen-contract-change", "B-3", class_hint="hard_stop")
    item, answer, closed = wait_paths(w, aid)
    held = (["step.B-4"], (False, {"B-3"}, [aid]))
    with lock_holder(w, monkeypatch) as c:
        assert (eligible(c), c.awaiting_blocks()) == held
        # the surrogate's own record of it (OS-04, OS-09) — or one that calls it routine and executed
        for n, (cls, state) in enumerate([("hard_stop", "PROPOSED"), ("routine", "EXECUTED")], 1):
            with open(w.run / "DECISIONS_SURROGATE.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps({"id": "SD-20261011T220000Z-%d" % n, "awaiting": aid, "class": cls, "state": state,
                                    "decision": "yes", "by": "kalayantra-owner-surrogate"}) + "\n")
            assert (eligible(c), c.awaiting_blocks()) == held
        # a decision the surrogate writes beside the item: under its own name, or dressed as the cockpit's
        for forged in (decision_record(aid, "SD-20261011T220000Z-2", **{"from": SURROGATE}),
                       decision_record(aid, "000001-decide-abc123"),
                       dict(decision_record(aid, None), decided_by="kalayantra-owner-surrogate")):
            answer.write_text(json.dumps(forged))
            assert (eligible(c), c.awaiting_blocks()) == held, forged
            answer.unlink()
        # a `decide` the surrogate queues itself: the queue takes commands from the cockpit only
        (w.run / "commands").mkdir(exist_ok=True)
        forged = {"schema": "ky.command/1", "id": "000001-decide-abc123", "created_at": "2026-10-11T00:00:00Z",
                  "from": SURROGATE, "role": "planner", "command": "decide", "args": {"awaiting_id": aid, "answer": "yes"},
                  "state": "QUEUED", "applied_by": None, "applied_at": None, "result": None}
        (w.run / "commands" / "20261011T000000Z-000001-decide-abc123.json").write_text(json.dumps(forged))
        answer.write_text(json.dumps(decision_record(aid, "000001-decide-abc123", **{"from": SURROGATE})))
        assert (eligible(c), c.awaiting_blocks()) == held   # … whether it is still queued,
        answer.unlink()
        assert c.apply_commands() is True                   # … or settled: REJECTED, nothing written, nothing moved
        assert command(w, "000001-decide-abc123")["state"] == "REJECTED"
        assert command(w, "000001-decide-abc123")["result"]["reason"].startswith("invalid_command")
        assert not answer.exists() and item.exists() and (eligible(c), c.awaiting_blocks()) == held
        # the owner's own decide releases it
        cid = submit(w, "planner", "decide", {"awaiting_id": aid, "answer": "no: the contract stays frozen"})
        assert c.apply_commands() is True
        assert eligible(c) == ["step.B-3", "step.B-4"] and c.awaiting_blocks() == (False, set(), [])
    od = json.loads(answer.read_text())
    assert command(w, cid)["state"] == "APPLIED" and od["command_id"] == cid and od["wait"]["class_hint"] == "hard_stop"
    assert not item.exists() and closed.exists()


def interrupted_decide(w, aid, moved=False):
    """A `decide` whose controller died inside its handler: the command is still QUEUED, its action record
    INTENDED by a process that is gone, the decision record written — and the item moved, or not yet."""
    item, answer, closed = wait_paths(w, aid)
    cid = submit(w, "planner", "decide", {"awaiting_id": aid, "answer": "yes"})
    entry = kycommands.find(w.run, cid)
    kyaction.begin(w.run, "CMD-" + cid, "command:decide",
                   {"role": "planner", "holder_kind": "controller", "controller_id": OLD_CTL},
                   {"role": "planner", "command": "decide", "args": {"awaiting_id": aid, "answer": "yes"}},
                   {"command_id": cid, "file": entry["path"].name}, "command %s: QUEUED → APPLIED" % cid)
    left_by_a_dead_process(w, "CMD-" + cid)
    answer.write_text(json.dumps(decision_record(aid, cid, awaiting_sha256=sha(item))))
    os.chmod(answer, 0o444)
    if moved:
        closed.parent.mkdir()
        item.rename(closed)
    return cid


@pytest.mark.parametrize("moved", [False, True], ids=["before-the-move", "after-the-move"])
def test_a_decide_interrupted_after_its_record_is_completed_on_the_next_tick_without_a_second_record(w, moved):
    """R15 (2), the crash window: decision written, item not yet moved. The next controller completes it under the
    same action record — the handler runs again and finds its own record — and writes no second decision; when the
    move had happened too, it is observed and nothing runs again."""
    w.ready()
    w.modes("stop")
    aid = job_wait(w, "b-3-question", "B-3")
    item, answer, closed = wait_paths(w, aid)
    asked = item.read_bytes()
    cid = interrupted_decide(w, aid, moved)
    first = answer.read_bytes()
    r = w.kyloop("planner")
    assert r.returncode == 0, r.stderr
    assert command(w, cid)["state"] == "APPLIED" and work_items(w.records()[0]) == ["step.B-3", "step.B-4"]
    assert not item.exists() and closed.read_bytes() == asked
    assert answer.read_bytes() == first                     # the one decision record, untouched
    assert [p.name for p in (w.run / "awaiting").glob("*.owner_decision.json")] == [answer.name]
    assert not list((w.run / "awaiting" / "done").glob("*set_aside*"))
    act = kyaction.load(w.run, "CMD-" + cid)
    assert act["state"] == "DONE" and [x["outcome"] for x in act["reconciliations"]] == ["done" if moved else "not_done"]
    assert w.awaiting() == [] and not list((w.run / "locks").glob("awaiting.*"))


def test_an_answer_whose_item_could_not_be_moved_stands_and_the_move_is_made_on_a_later_tick(w, monkeypatch):
    """The other way a decision can lie beside an open item: the move failed. The command is APPLIED all the same
    (the owner's answer is recorded, and says that the item is not closed), the wait no longer blocks — rule (1)
    — and the controller closes it at a later look."""
    w.ready()
    aid = job_wait(w, "b-3-question", "B-3")
    item, answer, closed = wait_paths(w, aid)
    with lock_holder(w, monkeypatch) as c:
        closed.parent.write_text("a file where the directory should be")
        cid = submit(w, "planner", "decide", {"awaiting_id": aid, "answer": "yes"})
        assert c.apply_commands() is True
        doc = command(w, cid)
        assert doc["state"] == "APPLIED" and doc["result"]["closed"] is None and doc["result"]["close_error"]
        assert item.exists() and json.loads(answer.read_text())["command_id"] == cid
        assert eligible(c) == ["step.B-3", "step.B-4"] and c.awaiting_blocks() == (False, set(), [])
        assert c.apply_commands() is False and item.exists()          # still not possible: tried, nothing lost
        # … and somebody is told, once: the item lies in run/awaiting as if it were open
        (note,) = [a for a in w.awaiting() if a["id"].endswith("-loop-planner-answered-wait-not-closed")]
        assert note["blocks"] == "none" and aid in json.dumps(note) and "FileExistsError" in json.dumps(note)
        assert_awaiting_schema(note)
        assert w.cockpit_journal().count("\n") == 1 and note["id"] in w.cockpit_journal()
        closed.parent.unlink()
        assert c.apply_commands() is False                  # nothing is queued — and what was left is finished
        assert not item.exists() and closed.exists() and eligible(c) == ["step.B-3", "step.B-4"]
    assert [p.name for p in (w.run / "awaiting").glob("*.owner_decision.json")] == [answer.name]


def test_an_answered_wait_is_a_changed_dependency_also_when_a_job_of_this_role_raised_it(w, monkeypatch):
    """R15 (3). The wait a job of this role raised is in no external fingerprint while it is open (N-02: raising it
    is not progress) — the OWNER's answer to it is: nothing the run authored. It resets the no-progress count and
    is recorded evidence for the sub-step window; an answered wait about an item this role does not work on is
    not (L3-01)."""
    w.ready()
    aid = job_wait(w, "b-3-question", "B-3")
    with lock_holder(w, monkeypatch) as c:
        kyloop.update_loop_state(w.run, "planner", lambda d: dict(d, no_progress_count=2))
        before, window = c.accepted_summary(), c.substep_evidence()
        cid = submit(w, "planner", "decide", {"awaiting_id": aid, "answer": "yes"})
        assert c.accepted_summary() == before               # queued is not answered
        assert c.apply_commands() is True
        after = c.accepted_summary()
        for basis in ("dependency_fingerprint", "external_fingerprint"):
            assert after[basis] != before[basis], basis
        assert c.substep_evidence() != window
        ls = w.loop_state()
        assert ls["no_progress_count"] == 0 and ls["evidence_changed"] == dict(ls["evidence_changed"], awaiting_id=aid,
                                                                             by="command:" + cid)
        # the conductor's answered wait for K9-23 — its own controller applied it — is no dependency of the planner
        other = job_wait(w, "k9-23-question", "K9-23", role="conductor")
        theirs = submit(w, "conductor", "decide", {"awaiting_id": other, "answer": "yes"})
        wait_paths(w, other)[1].write_text(json.dumps(decision_record(
            other, theirs, applied_by={"role": "conductor", "controller_id": "CTL-CONDUCTOR-20260101T000000Z-1"},
            wait={"item": "K9-23", "blocks": "item"})))
        assert sorted(c.owner_answers()) == sorted([aid, other])        # both are the owner's answers …
        assert c.accepted_summary() == after                            # … one of them is this role's dependency
        assert c.apply_commands() is False and wait_paths(w, other)[0].exists()     # nor is it this role's to close


@pytest.mark.parametrize("answer,state", [("happened", "DONE"), ("did-not-happen: the PR was never opened", "FAILED")])
def test_the_owners_answer_to_an_unobservable_job_action_is_carried_out_and_frees_the_item(w, answer, state):
    """R15 (2), the controller's own item. A job left a side effect begun and unobserved; the controller raised one
    item-level wait for it. The owner's `decide` names one of its two options, and the controller carries it
    out: the job's record is settled (DONE / FAILED, on the owner's word, said so in its result), the item is
    closed, and the step is work again."""
    w.ready()
    w.modes("job-unknown", "stop")
    assert w.kyloop("planner").returncode == 0
    first = w.records()[0]
    aid = "JOB-%s-open-pr" % first["run_id"]
    (item,) = job_action_items(w)
    assert item["blocks"] == "item" and work_items(w.records()[1]) == ["step.B-4"]
    assert [o["id"] for o in item["options"]] == ["happened", "did-not-happen"]
    cid = submit(w, "planner", "decide", {"awaiting_id": item["id"], "answer": answer})
    w.rearm()
    w.modes("stop")
    assert w.kyloop("planner").returncode == 0
    doc = command(w, cid)
    assert doc["state"] == "APPLIED", doc
    act = kyaction.load(w.run, aid)
    option = answer.split(":")[0]
    assert act["state"] == state and act["result"] == dict(act["result"], settled_by="owner_decision", answer=option,
                                                           command_id=cid, awaiting_id=item["id"], observed=False)
    assert doc["result"]["job_action"] == {"action_id": aid, "state": state, "settled": option}
    assert job_action_items(w) == [] and wait_paths(w, item["id"])[2].exists()
    assert work_items(w.records()[2]) == ["step.B-3", "step.B-4"]
    w.rearm()                                               # a restart finds nothing left to reconcile, or to raise
    w.modes("stop")
    assert w.kyloop("planner").returncode == 0
    assert job_action_items(w) == [] and kyaction.load(w.run, aid) == act and len(w.records()) == 4


def test_an_answer_that_names_no_option_of_a_job_action_item_is_rejected_and_nothing_changes(w):
    """The controller can only carry out an option it offered. Anything else is REJECTED with the options named —
    nothing recorded, the record untouched, the item open and still blocking — so the owner can answer again."""
    w.ready()
    w.modes("job-unknown", "stop")
    assert w.kyloop("planner").returncode == 0
    aid = "JOB-%s-open-pr" % w.records()[0]["run_id"]
    (item,) = job_action_items(w)
    cid = submit(w, "planner", "decide", {"awaiting_id": item["id"], "answer": "perhaps"})
    w.rearm()
    w.modes("stop")
    assert w.kyloop("planner").returncode == 0
    doc = command(w, cid)
    assert doc["state"] == "REJECTED" and doc["result"]["reason"].startswith("answer_not_an_option")
    assert "happened" in doc["result"]["reason"] and "did-not-happen" in doc["result"]["reason"]
    assert kyaction.load(w.run, aid)["state"] == "INTENDED" and len(job_action_items(w)) == 1
    assert not wait_paths(w, item["id"])[1].exists() and work_items(w.records()[2]) == ["step.B-4"]
    again = submit(w, "planner", "decide", {"awaiting_id": item["id"], "answer": "happened"})
    w.rearm()
    w.modes("stop")
    assert w.kyloop("planner").returncode == 0
    assert command(w, again)["state"] == "APPLIED" and kyaction.load(w.run, aid)["state"] == "DONE"


def test_closing_an_answered_wait_is_idempotent_and_never_replaces_or_loses_a_file(w, monkeypatch):
    """What the next look relies on: every step of closing can be made again. A closed item is never replaced —
    an open one of the same id lies beside it under another name, unless it is the same bytes (then it is the
    duplicate) — and a job record that is settled, or gone, is left as it is."""
    w.ready()
    aid = job_wait(w, "b-3-question", "B-3")
    item, _, closed = wait_paths(w, aid)
    asked = item.read_bytes()
    with lock_holder(w, monkeypatch) as c:
        assert c.move_to_done(aid) == str(closed) and closed.read_bytes() == asked and not item.exists()
        assert c.move_to_done(aid) == str(closed)           # nothing left to move: where it lies
        assert c.move_to_done("AW-20261011T000000Z-never-raised") is None
        item.write_bytes(asked)                             # the same item again (a breaker item written back)
        assert c.move_to_done(aid) == str(closed) and not item.exists()
        assert [p.name for p in closed.parent.iterdir()] == [closed.name]
        item.write_text(json.dumps({"schema": "ky.awaiting/1", "id": aid, "question": "another question"}))
        other = Path(c.move_to_done(aid))                   # another item under that id: beside it, neither lost
        assert other != closed and other.parent == closed.parent and closed.read_bytes() == asked
        assert json.loads(other.read_text())["question"] == "another question" and not item.exists()
        # the job-action option: settled once, on the owner's word
        actor = {"role": "planner", "holder_kind": "job", "controller_id": OLD_CTL, "run_id": OLD_RUN}
        act = "JOB-%s-open-pr" % OLD_RUN
        kyaction.begin(w.run, act, "pr_create", actor, {"title": "x"}, {"item": "step.B-3"}, "open a PR")
        answer = decision_record("AW-20261011T000000Z-" + c.job_action_slug(act), "000001-decide-abc123", "did-not-happen")
        first = c.settle_job_action(act, answer["awaiting_id"], answer)
        assert first == {"action_id": act, "state": "FAILED", "settled": "did-not-happen"}
        settled = kyaction.load(w.run, act)
        again = c.settle_job_action(act, answer["awaiting_id"], dict(answer, answer="happened"))
        assert again == {"action_id": act, "state": "FAILED", "settled": "already_settled"}
        assert kyaction.load(w.run, act) == settled         # its observed result is set once
        assert c.settle_job_action("JOB-%s-gone" % OLD_RUN, answer["awaiting_id"], answer)["settled"] == "no_record"
        kyaction.begin(w.run, "ACT-not-a-jobs", "push", {"role": "planner", "holder_kind": "cockpit",
                                                         "session_id": "cockpit-session-1"}, {}, {}, "x")
        assert c.settle_job_action("ACT-not-a-jobs", answer["awaiting_id"], answer)["settled"] == "not_a_job_record_of_this_role"
        assert kyaction.load(w.run, "ACT-not-a-jobs")["state"] == "INTENDED"
        # … and an item is a job-action item only when a controller of this role raised it for exactly that record
        doc = {"raised_by": {"role": "planner", "session_id": OLD_CTL, "job_id": None}, "evidence": ["action: " + act]}
        assert c.job_action_of(answer["awaiting_id"], doc) == act
        assert c.job_action_of("AW-20261011T000000Z-job-action-something-else", doc) is None
        assert c.job_action_of(answer["awaiting_id"], dict(doc, raised_by={"role": "planner", "session_id": "x",
                                                                           "job_id": OLD_RUN})) is None
        assert c.job_action_of(answer["awaiting_id"], dict(doc, evidence=["action: JOB-CONDUCTOR-1-open-pr"])) is None
        assert [c.chosen_option(a) for a in ("happened", " Happened : seen", "did-not-happen", "no", "", None, 7)] == \
            ["happened", "happened", "did-not-happen", None, None, None, None]


def test_a_wait_another_actor_raised_about_this_roles_item_is_answered_through_this_role(w, monkeypatch):
    """R16: a hard stop the STEWARD raised about B-3 blocks the planner — and no controller answers for a role
    that has none. The role whose work it blocks applies the owner's `decide`; a wait that is neither this role's
    nor about its work is still not this role's to answer."""
    w.ready()
    aid = job_wait(w, "b-3-from-the-steward", "step.B-3", role="steward", class_hint="hard_stop", job_id=None)
    foreign = job_wait(w, "k9-23-from-a-builder", "K9-23", role="builder")
    with lock_holder(w, monkeypatch) as c:
        assert eligible(c) == ["step.B-4"]
        cid = submit(w, "planner", "decide", {"awaiting_id": aid, "answer": "yes"})
        no = submit(w, "planner", "decide", {"awaiting_id": foreign, "answer": "yes"})
        assert c.apply_commands() is True
        assert command(w, cid)["state"] == "APPLIED", command(w, cid)
        assert eligible(c) == ["step.B-3", "step.B-4"]
    assert command(w, no)["state"] == "REJECTED" and command(w, no)["result"]["reason"].startswith("not_this_roles_item")
    assert wait_paths(w, foreign)[0].exists() and not wait_paths(w, foreign)[1].exists()


def test_the_veto_controller_closes_the_item_of_its_own_that_the_owner_answered(w, monkeypatch):
    """The same handler serves the veto role: an attention item it raised is answered and closed by a `decide`."""
    veto_world(w)
    w.enable("veto")
    c = controller_in_process(w, monkeypatch, "veto")
    c.load_siblings()
    assert c.acquire()
    try:
        c.raise_final("SD-20261011T220000Z-1", "failed (target_changed)")
        (item,) = w.awaiting()
        cid = submit(w, "veto", "decide", {"awaiting_id": item["id"], "answer": "acknowledge"})
        assert c.apply_commands() is True
    finally:
        c.release_lock()
    assert command(w, cid)["state"] == "APPLIED" and w.awaiting() == []
    assert wait_paths(w, item["id"])[2].exists()
    assert json.loads(wait_paths(w, item["id"])[1].read_text())["applied_by"]["role"] == "veto"


# ───────────────────────────── a refused environment is one item and a stop, never a respawn (N4-01) ─────────────────────────────

def test_a_refused_environment_of_a_loop_that_was_never_started_raises_nothing(w):
    """The other half of the one shape: a loop that is not admitted raises nothing, whatever is wrong around it."""
    r = w.kyloop("planner", PGPASSWORD="fake-not-printed")
    assert r.returncode == 0 and "fake-not-printed" not in r.stderr + r.stdout
    assert w.awaiting() == [] and not w.stop_file().exists() and w.calls() == []


def test_a_bad_sleep_scale_is_one_item_and_a_stop_not_a_respawn(w):
    w.ready()
    w.default_mode("substep")
    for again in (False, True):
        if again:
            w.rearm()
        r = w.kyloop("planner", KY_LOOP_SLEEP_SCALE="7")
        assert r.returncode == 0 and "Traceback" not in r.stderr
        assert "bad_sleep_scale" in json.dumps(refused(w))
    assert w.cockpit_journal().count("[decision]") == 1
    # the admin commands are a person's own, one-shot call: there the same refusal is an exit status
    r = w.kyloop("admin", "expected-qualification", "planner", KY_LOOP_SLEEP_SCALE="7")
    assert r.returncode == 78 and "KY_LOOP_SLEEP_SCALE" in r.stderr


def test_without_a_run_directory_the_controller_notifies_once_and_stops_without_creating_one(w):
    """Nothing can be recorded where there is no run directory: no item, no STOP, no switch. What is left of the one
    shape is ONE notification attempt and exit 0 — launchd does not respawn it every ten seconds — and nothing is
    created in its place."""
    gone, log = w.tmp / "no-such-run", w.tmp / "osascript.argv"
    r = w.kyloop("planner", KY_RUN=str(gone), KY_NOTIFY_DRY="0", KY_OSASCRIPT=str(FIX / "fake_osascript"),
                 FAKE_OSASCRIPT_LOG=str(log))
    assert r.returncode == 0 and "is not a directory" in r.stderr and "notify=submitted" in r.stderr
    assert "planner loop did not start" in log.read_text() and str(gone) in log.read_text()
    assert not gone.exists() and w.calls() == [] and w.awaiting() == []


# ───────────────────────────── R16: a wait that needs a person says so ─────────────────────────────

def queue_items(w, role="planner"):
    return [a for a in w.awaiting() if a["id"].endswith("-loop-%s-command-queue-unreadable" % role)]


def test_a_pause_that_only_a_repaired_queue_can_end_raises_one_attention_item(w):
    """A command queue that cannot be read is honoured as a pause (see above) — but that pause does not end by an
    owner's resume: somebody has to repair the queue. The loop says so once, and goes on waiting."""
    w.ready()
    w.default_mode("stop")
    (w.run / "commands").mkdir()
    torn = w.run / "commands" / "20261011T000000Z-000001-pause-abc123.json"
    torn.write_text("{torn")
    p = w.popen("planner")
    try:
        assert wait_for(lambda: len(queue_items(w)) == 1)
        time.sleep(0.4)                                     # dozens of looks: still one item, one notification
        (item,) = queue_items(w)
        assert item["blocks"] == "none" and torn.name in json.dumps(item) and len(w.awaiting()) == 1
        assert_awaiting_schema(item)
        assert w.cockpit_journal().count("\n") == 1 and item["id"] in w.cockpit_journal()
        assert w.calls() == [] and p.poll() is None and w.loop_state()["waiting"] == "owner_paused"
        assert not w.stop_file().exists() and w.loop_state()["enabled"] is True
        torn.unlink()
        assert p.wait(timeout=20) == 0
    finally:
        p.kill()
    assert w.calls() == [1]


def overdue_items(w, role="planner"):
    return [a for a in w.awaiting() if a["id"].endswith("-loop-%s-commands-not-settled" % role)]


def test_a_queued_command_that_stays_unsettled_is_raised_once_and_the_wait_goes_on(w):
    """A command that cannot be settled yet keeps its place and nothing is launched (see above): a wait that ends
    when another actor lets go. While it is short it is nobody's business — and when it has lasted half an hour
    (1.8 s at the test scale) the loop says so, once: it would otherwise rest in `commands_pending` for good behind
    a holder that never lets go. Nothing is taken over, nothing is stopped."""
    w.ready()
    w.default_mode("stop")
    aid = job_wait(w, "planner-question", "N-1", blocks="none")
    busy = kyaction.acquire_lock(w.run, "awaiting." + aid, "surrogate-job-1")     # a live actor that never lets go
    cid = submit(w, "planner", "decide", {"awaiting_id": aid, "answer": "yes"})
    p = w.popen("planner")
    try:
        assert wait_for(lambda: (w.loop_state() or {}).get("waiting") == "commands_pending")
        time.sleep(0.3)
        assert overdue_items(w) == [] and w.cockpit_journal() == ""       # short: nothing is raised
        assert wait_for(lambda: len(overdue_items(w)) == 1, timeout=20)
        time.sleep(0.5)                                     # hundreds of looks later: still one item, one notification
        (item,) = overdue_items(w)
        assert item["blocks"] == "none" and ("awaiting_item_locked: %s" % aid) in json.dumps(item)
        assert_awaiting_schema(item)
        assert w.cockpit_journal().count("\n") == 1 and item["id"] in w.cockpit_journal()
        assert w.calls() == [] and p.poll() is None and command(w, cid)["state"] == "QUEUED"
        assert w.loop_state()["waiting"] == "commands_pending" and w.loop_state()["enabled"] is True
        assert not w.stop_file().exists() and kyaction.lock_owner(w.run, "awaiting." + aid)[0]["pid"] == os.getpid()
        assert kyaction.release_lock(busy)
        assert p.wait(timeout=20) == 0
        said = p.stderr.read()
    finally:
        p.kill()
    assert command(w, cid)["state"] == "APPLIED" and w.calls() == [1]
    # a wait that is looked at every second says what it waits for when that changes, not two lines a second
    assert said.count("cannot be settled yet") == 1 and said.count("is locked by another actor") == 1


def test_a_second_refusal_for_another_reason_is_raised_although_the_first_item_is_still_open(w):
    """R16. The item of a refused precondition tells the owner to correct the cause and start the loop again —
    nothing asks them to answer or close the item, and in Wave B no surrogate does. A LATER refusal for another
    reason must not hide behind it (STOP, disabled, and nobody told): it is a new item and a new notification. The
    same refusal again is not."""
    w.ready()
    w.default_mode("stop")
    (w.run / "INSTALL_RECEIPT.json").unlink()
    assert w.kyloop("planner").returncode == 0
    first = refused(w)
    assert "install_receipt_missing" in json.dumps(first) and w.cockpit_journal().count("[decision]") == 1
    w.receipt("bootstrap")                                  # corrected, started again as the item says: it runs
    w.rearm()
    assert w.kyloop("planner").returncode == 0 and w.calls() == [1]
    assert w.awaiting() == [first]                          # … and the item is still there: nobody had to close it
    (w.fleet / "kyversion.sh.rc").write_text("3")           # later, something else breaks
    w.rearm()
    assert w.kyloop("planner").returncode == 0 and w.calls() == [1]
    items = [a for a in w.awaiting() if a["id"].endswith("-loop-planner-precondition")]
    assert len(items) == 2 and items[0] == first and items[0]["id"] != items[1]["id"]
    assert "kyversion_failed: rc=3" in json.dumps(items[1]) and "install_receipt_missing" not in json.dumps(items[1])
    assert_awaiting_schema(items[1])
    assert w.cockpit_journal().count("[decision]") == 2 and items[1]["id"] in w.cockpit_journal()
    assert w.stop_file().exists() and w.loop_state()["enabled"] is False
    w.rearm()                                               # the same refusal again: nothing new
    assert w.kyloop("planner").returncode == 0
    assert [a for a in w.awaiting() if a["id"].endswith("-loop-planner-precondition")] == items
    assert w.cockpit_journal().count("[decision]") == 2


def test_a_second_veto_stop_for_another_reason_is_raised_although_the_first_item_is_still_open(w, monkeypatch):
    """R16, the veto loop's own stop: its item says "reconcile, then `kyctl.sh start veto`" — nobody has to close
    it. A later stop for something else is a new item and a new notification; the same stop again is not."""
    veto_world(w)
    w.enable("veto")
    c = controller_in_process(w, monkeypatch, "veto")
    c.load_siblings()

    def stops():
        return [a for a in w.awaiting() if a["id"].endswith("-loop-veto-attention")]

    first_problem = ["SD-20261011T220000Z-1: blocked (publication_unknown)"]
    c.open_attention(first_problem)
    (first,) = stops()
    assert w.cockpit_journal().count("veto loop stopped") == 1 and w.loop_state("veto")["enabled"] is False
    w.enable("veto")                                        # reconciled and started again; the item stays open
    (w.run / "DECISIONS_SURROGATE.jsonl").write_text("")    # (recorded evidence changed)
    c.open_attention(first_problem)                         # the same stop once more: nothing new
    assert stops() == [first] and w.cockpit_journal().count("veto loop stopped") == 1
    assert w.loop_state("veto")["breaker"]["awaiting"]["id"] == first["id"]
    w.enable("veto")
    c.open_attention(["problem: the command queue cannot be read"])     # later, something else
    assert len(stops()) == 2 and stops()[0] == first
    second = stops()[1]
    assert "the command queue cannot be read" in json.dumps(second) and "publication_unknown" not in json.dumps(second)
    assert w.cockpit_journal().count("veto loop stopped") == 2 and second["id"] in w.cockpit_journal()
    ls = w.loop_state("veto")
    assert ls["enabled"] is False and ls["breaker"]["open"] is True and ls["breaker"]["awaiting"]["id"] == second["id"]
    assert_awaiting_schema(second)


def test_an_awaiting_id_is_never_used_twice(w, monkeypatch):
    """The id of a new item is one no item ever had — open, answered or closed: a second item of a slug within the
    same second neither replaces the first nor is born answered by the decision that lies beside the old id."""
    w.ready()
    c = controller_in_process(w, monkeypatch)
    real, d = kyloop.utc, w.run / "awaiting"
    monkeypatch.setattr(kyloop, "utc", lambda fmt="%Y-%m-%dT%H:%M:%SZ", t=None: real(fmt, 1791800000 if t is None else t))

    def raise_one():                                        # every item is made in the same second
        return c.write_awaiting("same-slug", "?", [{"id": "a", "text": "a"}], None, [], blocks="none")["id"]

    first, second = raise_one(), raise_one()
    assert first != second and {a["id"] for a in w.awaiting()} == {first, second}       # the first was not replaced
    (d / "done").mkdir()
    (d / (first + ".json")).rename(d / "done" / (first + ".json"))                      # closed
    (d / (second + ".json")).rename(d / "done" / (second + ".2.json"))                  # answered, and closed elsewhere
    (d / (second + ".owner_decision.json")).write_text("{}")
    third = raise_one()
    assert third not in (first, second) and [a["id"] for a in w.awaiting()] == [third]
    assert c.open_awaiting("same-slug") == [d / (third + ".json")]                      # … and it is open, not born answered
    for aid in (first, second, third):
        assert re.fullmatch(r"AW-\d{8}T\d{6}Z-same-slug", aid)
    assert_awaiting_schema(w.awaiting()[0])


def test_an_owner_pause_itself_raises_nothing(w):
    """The negative: a pause the owner asked for — queued or applied — ends by the owner's resume; no item."""
    w.ready()
    w.default_mode("stop")
    submit(w, "campaign", "pause")
    p = w.popen("planner")
    try:
        assert wait_for(lambda: (w.loop_state() or {}).get("waiting") == "owner_paused")
        time.sleep(0.3)
        assert w.awaiting() == [] and w.cockpit_journal() == "" and p.poll() is None
        submit(w, "campaign", "resume")
        assert p.wait(timeout=20) == 0
    finally:
        p.kill()
    assert w.awaiting() == [] and w.calls() == [1]


# ═════════════════ an executed veto-class owner-wait has an end, on the controller's side (R18, L5-01) ═════════════════
#
# The surrogate leaves a veto-class item in run/awaiting and kyveto.py never moves one. The wait is answered when the
# veto HANDLER itself completed the decision for that awaiting id: its own `<SD id>.execute` action record is DONE
# and the decision reads EXECUTED by the handler's own rule. The controller of the role the wait holds up then
# closes the item under an action record of its own (AWCLOSE-<awaiting id>). A log line alone, and every other
# state, still blocks; a hard stop is the owner's alone.

VETO_CTL = "CTL-VETO-20260101T000000Z-1"
VETO_ACTOR = {"role": "veto", "holder_kind": "controller", "controller_id": VETO_CTL}
VETO_TARGET = {"kind": "capacity", "fingerprint": "f" * 64}


def surrogate_lines(w, aid, *states, n=1, cls="veto"):
    """Lines of ONE decision about that awaiting id in DECISIONS_SURROGATE.jsonl, as they stand there. → its id."""
    sid = "SD-20261011T220000Z-%d" % n
    with open(w.run / "DECISIONS_SURROGATE.jsonl", "a", encoding="utf-8") as f:
        for state in states:
            f.write(json.dumps({"id": sid, "awaiting": aid, "class": cls, "state": state, "decision": "yes",
                                "target": VETO_TARGET, "by": "kyveto" if state in ("EFFECTIVE", "EXECUTED")
                                else "kalayantra-owner-surrogate"}) + "\n")
    return sid


def handler_execute(w, sid, state="DONE", actor=VETO_ACTOR, kind="veto_decision_execute:capacity", decision=None):
    """The class executor's action record exactly as kyveto.Handler.execute names and settles it."""
    kyaction.begin(w.run, sid + ".execute", kind, actor, {"decision_id": decision or sid, "class": "veto",
                                                         "authority": {"source_commit": C1, "entrypoints_digest": E1}},
                   VETO_TARGET, "capacity: builders 4 → 6")
    if state == "DONE":
        kyaction.complete(w.run, sid + ".execute", {"written": True})
    elif state == "FAILED":
        kyaction.fail(w.run, sid + ".execute", {"reason": "target_changed"})
    else:
        left_by_a_dead_process(w, sid + ".execute")
    return w.run / "actions" / (sid + ".execute.json")


def close_record(w, aid):
    return kyaction.load(w.run, "AWCLOSE-" + aid)


def test_an_executed_veto_class_wait_at_item_level_puts_its_item_back_to_work(w, monkeypatch):
    """L5-01, item level — the reviewer's probe: a planner-job wait on B-3 (class_hint veto, blocks item). It blocks
    B-3 through the whole veto window and while EXECUTED is only a line; once the handler's own execute record is
    DONE it blocks nothing, and the planner controller closes the item under one action record — once."""
    w.ready()
    aid = job_wait(w, "b-3-capacity", "B-3", class_hint="veto")
    item, answer, closed = wait_paths(w, aid)
    asked, held = item.read_bytes(), (["step.B-4"], (False, {"B-3"}, [aid]))
    with lock_holder(w, monkeypatch) as c:
        assert (eligible(c), c.awaiting_blocks()) == held
        for state in ("PROPOSED", "PENDING_VETO", "EFFECTIVE", "EXECUTED"):
            sid = surrogate_lines(w, aid, state)
            assert (eligible(c), c.awaiting_blocks()) == held, state        # a line is never the handler's record
            assert c.apply_commands() is False and item.exists()
        record = handler_execute(w, sid)
        assert eligible(c) == ["step.B-3", "step.B-4"] and c.awaiting_blocks() == (False, set(), [])
        assert item.exists()                                # answered already; closed at the controller's next look
        assert c.apply_commands() is False
        assert not item.exists() and closed.read_bytes() == asked and not answer.exists()
        act = close_record(w, aid)
        assert act["state"] == "DONE" and act["kind"] == "awaiting_close:veto_executed"
        assert act["actor"] == dict(act["actor"], role="planner", holder_kind="controller")
        assert act["inputs"] == {"awaiting_id": aid, "decision_id": sid}
        assert act["result"] == dict(act["result"], closed=str(closed), execute_record_sha256=sha(record))
        first = (w.run / "actions" / ("AWCLOSE-%s.json" % aid)).read_bytes()
        assert c.apply_commands() is False                  # idempotent: nothing moved, nothing written again
        assert (w.run / "actions" / ("AWCLOSE-%s.json" % aid)).read_bytes() == first
        assert sorted(p.name for p in closed.parent.iterdir()) == [closed.name]
        assert eligible(c) == ["step.B-3", "step.B-4"] and c.awaiting_blocks() == (False, set(), [])
    assert w.awaiting() == [] and not list((w.run / "locks").glob("awaiting.*"))


def test_an_executed_veto_class_wait_at_loop_level_puts_the_loop_back_to_work(w, monkeypatch):
    """L5-01, loop level: with `blocks: loop` the whole loop rested in no_eligible_work."""
    w.ready()
    aid = job_wait(w, "planner-loop-capacity", "B-3", blocks="loop", class_hint="veto")
    with lock_holder(w, monkeypatch) as c:
        sid = surrogate_lines(w, aid, "PENDING_VETO", "EFFECTIVE", "EXECUTED")
        assert eligible(c) == [] and c.awaiting_blocks() == (True, set(), [aid])
        handler_execute(w, sid)
        assert eligible(c) == ["step.B-3", "step.B-4"] and c.awaiting_blocks() == (False, set(), [])
        assert c.apply_commands() is False
    assert w.awaiting() == [] and wait_paths(w, aid)[2].exists() and close_record(w, aid)["state"] == "DONE"


def test_a_running_loop_goes_on_when_the_handler_executed_its_loop_level_veto_wait(w):
    """The whole path in the real controller: it waits, no model, while the decision is pending; the handler's DONE
    record — no command of anybody — ends the wait, and the job is given the work."""
    w.ready()
    w.default_mode("stop")
    aid = job_wait(w, "planner-loop-capacity", "B-3", blocks="loop", class_hint="veto")
    sid = surrogate_lines(w, aid, "PENDING_VETO", "EFFECTIVE", "EXECUTED")
    p = w.popen("planner")
    try:
        assert wait_for(lambda: (w.loop_state() or {}).get("waiting") == "no_eligible_work")
        time.sleep(0.3)
        assert w.calls() == [] and p.poll() is None         # EXECUTED as a line only: still waiting
        handler_execute(w, sid)
        assert p.wait(timeout=15) == 0
    finally:
        p.kill()
    assert w.calls() == [1] and work_items(w.records()[0]) == ["step.B-3", "step.B-4"]
    assert w.awaiting() == [] and wait_paths(w, aid)[2].exists() and close_record(w, aid)["state"] == "DONE"


STILL_BLOCKS = ["pending-veto", "effective", "vetoed", "failed", "failed-with-failed-record", "bare-executed-line",
                "executed-line-record-intended", "executed-line-record-failed", "done-record-no-executed-line",
                "done-record-not-the-handlers", "done-record-of-a-cockpit", "done-record-of-another-kind",
                "done-record-for-another-decision", "decision-about-another-wait", "decision-not-of-veto-class",
                "log-with-a-line-nobody-can-read"]


@pytest.mark.parametrize("blocks", ["item", "loop"])
@pytest.mark.parametrize("case", STILL_BLOCKS)
def test_a_veto_class_wait_the_handler_did_not_complete_still_blocks(w, monkeypatch, case, blocks):
    """R18, the negatives. Everything short of "the handler's own execute record for THIS decision about THIS wait
    is DONE and the decision reads EXECUTED" leaves the wait blocking and the item where it is — and none of it is
    a dead end: when the handler's record is there, the same wait is released."""
    w.ready()
    aid = job_wait(w, "b-3-capacity", "B-3", blocks=blocks, class_hint="veto")
    other = job_wait(w, "b-4-capacity", "B-4", class_hint="veto")
    item = wait_paths(w, aid)[0]
    held = ([], (True, {"B-4"}, sorted([aid, other]))) if blocks == "loop" else \
        ([], (False, {"B-3", "B-4"}, sorted([aid, other])))
    lines = {"pending-veto": ["PENDING_VETO"], "effective": ["PENDING_VETO", "EFFECTIVE"],
             "vetoed": ["PENDING_VETO", "VETOED"], "failed": ["PENDING_VETO", "FAILED"],
             "failed-with-failed-record": ["PENDING_VETO", "EFFECTIVE", "FAILED"],
             "done-record-no-executed-line": ["PENDING_VETO", "EFFECTIVE"]}.get(
                 case, ["PENDING_VETO", "EFFECTIVE", "EXECUTED"])
    about = other if case == "decision-about-another-wait" else aid
    sid = surrogate_lines(w, about, *lines, cls="routine" if case == "decision-not-of-veto-class" else "veto")
    if case in ("failed-with-failed-record", "executed-line-record-failed"):
        handler_execute(w, sid, "FAILED")
    elif case == "executed-line-record-intended":
        handler_execute(w, sid, "INTENDED")
    elif case == "done-record-not-the-handlers":
        handler_execute(w, sid, actor={"role": "planner", "holder_kind": "controller", "controller_id": OLD_CTL})
    elif case == "done-record-of-a-cockpit":
        handler_execute(w, sid, actor={"role": "veto", "holder_kind": "cockpit", "session_id": "surrogate-1"})
    elif case == "done-record-of-another-kind":
        handler_execute(w, sid, kind="notification")
    elif case == "done-record-for-another-decision":
        handler_execute(w, sid, decision="SD-20261011T220000Z-7")
    elif case in ("done-record-no-executed-line", "decision-not-of-veto-class", "log-with-a-line-nobody-can-read"):
        handler_execute(w, sid)
    if case == "log-with-a-line-nobody-can-read":
        with open(w.run / "DECISIONS_SURROGATE.jsonl", "a", encoding="utf-8") as f:
            f.write("{torn\n")
    if case == "decision-about-another-wait":               # … which IS released: the other one, and only that
        handler_execute(w, sid)
        held = ([], (True, set(), [aid])) if blocks == "loop" else (["step.B-4"], (False, {"B-3"}, [aid]))
    with lock_holder(w, monkeypatch) as c:
        before = c.accepted_summary()
        assert (eligible(c), c.awaiting_blocks()) == held
        assert c.apply_commands() is False
        assert item.exists() and not (w.run / "actions" / ("AWCLOSE-%s.json" % aid)).exists()
        assert (eligible(c), c.awaiting_blocks()) == held
        if case != "decision-about-another-wait":
            assert c.accepted_summary() == before           # and it is no changed dependency
        # no dead end: the handler's own completed decision about this wait releases it
        if case == "log-with-a-line-nobody-can-read":
            log = w.run / "DECISIONS_SURROGATE.jsonl"
            log.write_text(log.read_text().replace("{torn\n", ""))
        else:
            handler_execute(w, surrogate_lines(w, aid, "PENDING_VETO", "EFFECTIVE", "EXECUTED", n=2))
        assert aid not in c.awaiting_blocks()[2] and c.awaiting_blocks()[0] is False
        assert c.apply_commands() is False and not item.exists() and close_record(w, aid)["state"] == "DONE"


@pytest.mark.parametrize("how", ["class-hint", "surrogate-record"])
def test_a_hard_stop_wait_is_not_released_by_an_executed_decision_only_by_an_owner_decide(w, monkeypatch, how):
    """R18: a hard stop is still the owner's alone. Not even an EXECUTED line with a DONE execute record of the
    handler's about that awaiting id releases it — whether the raiser called it a hard stop or the surrogate
    recorded it as one — and the controller does not move it. The owner's `decide` does."""
    w.ready()
    aid = job_wait(w, "frozen-contract-change", "B-3", class_hint="hard_stop" if how == "class-hint" else "veto")
    item, answer, closed = wait_paths(w, aid)
    held = (["step.B-4"], (False, {"B-3"}, [aid]))
    if how == "surrogate-record":
        with open(w.run / "DECISIONS_SURROGATE.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps({"id": "SD-20261011T220000Z-9", "awaiting": aid, "class": "hard_stop",
                                "decision": "owner only", "by": "kalayantra-owner-surrogate"}) + "\n")
    handler_execute(w, surrogate_lines(w, aid, "PENDING_VETO", "EFFECTIVE", "EXECUTED"))
    with lock_holder(w, monkeypatch) as c:
        before = c.accepted_summary()
        assert (eligible(c), c.awaiting_blocks()) == held
        assert c.apply_commands() is False
        assert item.exists() and not closed.exists() and (eligible(c), c.awaiting_blocks()) == held
        assert not (w.run / "actions" / ("AWCLOSE-%s.json" % aid)).exists() and c.accepted_summary() == before
        cid = submit(w, "planner", "decide", {"awaiting_id": aid, "answer": "no: the contract stays frozen"})
        assert c.apply_commands() is True
        assert eligible(c) == ["step.B-3", "step.B-4"] and c.awaiting_blocks() == (False, set(), [])
    assert command(w, cid)["state"] == "APPLIED" and json.loads(answer.read_text())["command_id"] == cid
    assert not item.exists() and closed.exists()


def test_the_release_of_an_executed_veto_class_wait_is_a_changed_dependency(w, monkeypatch):
    """R18: the release is a changed dependency no run authored — also for the wait a job of this role raised (in no
    external fingerprint while open, N-02). It restarts the no-progress count, once, and is evidence for the
    sub-step window; closing the item afterwards changes nothing further. Another role's executed wait about an
    item this role does not work on is neither this role's dependency nor its to close (L3-01)."""
    w.ready()
    aid = job_wait(w, "b-3-capacity", "B-3", class_hint="veto")
    with lock_holder(w, monkeypatch) as c:
        kyloop.update_loop_state(w.run, "planner", lambda d: dict(d, no_progress_count=2))
        sid = surrogate_lines(w, aid, "PENDING_VETO", "EFFECTIVE", "EXECUTED")
        before, window = c.accepted_summary(), c.substep_evidence()
        handler_execute(w, sid)
        after = c.accepted_summary()
        for basis in ("dependency_fingerprint", "external_fingerprint"):
            assert after[basis] != before[basis], basis
        assert c.substep_evidence() != window and w.loop_state()["no_progress_count"] == 2
        assert c.apply_commands() is False                  # the controller closes it: the same evidence, no more
        assert not wait_paths(w, aid)[0].exists() and c.accepted_summary() == after
        ls = w.loop_state()
        assert ls["no_progress_count"] == 0
        assert ls["evidence_changed"] == dict(ls["evidence_changed"], awaiting_id=aid, by="veto:" + sid)
        kyloop.update_loop_state(w.run, "planner", lambda d: dict(d, no_progress_count=2))
        assert c.apply_commands() is False and w.loop_state()["no_progress_count"] == 2     # once
        other = job_wait(w, "k9-23-capacity", "K9-23", role="conductor", class_hint="veto")
        handler_execute(w, surrogate_lines(w, other, "PENDING_VETO", "EFFECTIVE", "EXECUTED", n=2))
        assert c.accepted_summary() == after
        assert c.apply_commands() is False and wait_paths(w, other)[0].exists()
        assert not (w.run / "actions" / ("AWCLOSE-%s.json" % other)).exists()


@pytest.mark.parametrize("moved", [False, True], ids=["before-the-move", "after-the-move"])
def test_a_close_interrupted_before_or_after_the_move_is_completed_on_the_next_look(w, moved):
    """R18, the crash window (as R15's): the controller died with its close record begun — the item not yet moved,
    or moved and the record not yet completed. The next controller is not refused over that record: it completes
    the close under the SAME record, and the job is given B-3."""
    w.ready()
    w.modes("stop")
    aid = job_wait(w, "b-3-capacity", "B-3", class_hint="veto")
    item, _, closed = wait_paths(w, aid)
    asked = item.read_bytes()
    sid = surrogate_lines(w, aid, "PENDING_VETO", "EFFECTIVE", "EXECUTED")
    handler_execute(w, sid)
    kyaction.begin(w.run, "AWCLOSE-" + aid, "awaiting_close:veto_executed",
                   {"role": "planner", "holder_kind": "controller", "controller_id": OLD_CTL},
                   {"awaiting_id": aid, "decision_id": sid}, {"awaiting": aid + ".json"},
                   "close owner-wait %s: awaiting/ → awaiting/done/" % aid)
    left_by_a_dead_process(w, "AWCLOSE-" + aid)
    if moved:
        closed.parent.mkdir()
        item.rename(closed)
    r = w.kyloop("planner")
    assert r.returncode == 0, r.stderr
    assert work_items(w.records()[0]) == ["step.B-3", "step.B-4"]
    assert not item.exists() and closed.read_bytes() == asked
    act = close_record(w, aid)
    assert act["state"] == "DONE" and act["actor"]["controller_id"] == OLD_CTL
    assert w.awaiting() == [] and not list((w.run / "locks").glob("awaiting.*"))


def test_an_executed_veto_wait_that_cannot_be_moved_blocks_nothing_and_is_closed_at_a_later_look(w, monkeypatch):
    """The move failed: the wait is answered all the same, somebody is told once, and a later look closes it."""
    w.ready()
    aid = job_wait(w, "b-3-capacity", "B-3", class_hint="veto")
    item, _, closed = wait_paths(w, aid)
    handler_execute(w, surrogate_lines(w, aid, "PENDING_VETO", "EFFECTIVE", "EXECUTED"))
    with lock_holder(w, monkeypatch) as c:
        closed.parent.write_text("a file where the directory should be")
        for _ in range(2):
            assert c.apply_commands() is False and item.exists()
            assert eligible(c) == ["step.B-3", "step.B-4"]
        assert close_record(w, aid)["state"] == "INTENDED"
        (note,) = [a for a in w.awaiting() if a["id"].endswith("-loop-planner-answered-wait-not-closed")]
        assert note["blocks"] == "none" and aid in json.dumps(note)
        assert note["question"].startswith("The veto handler executed SD-20261011T220000Z-1 for %s, but" % aid)
        assert_awaiting_schema(note)
        closed.parent.unlink()
        assert c.apply_commands() is False
        assert not item.exists() and closed.exists() and close_record(w, aid)["state"] == "DONE"


def test_loop_controller_path_matches_installer_system_path(w, monkeypatch):
    """A successful installer proof must use the system PATH the controllers inherit."""
    program = (FLEET / "install.sh").read_text().split("\n: <<'KYINSTALL_PY'\n", 1)[1].rsplit("\nKYINSTALL_PY\n", 1)[0]
    program = program.rsplit("\nsys.exit(main(sys.argv[1:]))", 1)[0]
    namespace = {"__file__": str(FLEET / "install.sh")}
    exec(compile(program, str(FLEET / "install.sh"), "exec"), namespace)
    system = ["/opt/homebrew/bin", "/usr/local/bin", "/usr/bin", "/bin"]
    assert namespace["BASE_PATH"].split(":") == system
    install(w)
    for loop in LABELS:
        path = plistlib.loads(plist(w, loop).read_bytes())["EnvironmentVariables"]["PATH"]
        assert path.split(":") == [str(w.root / "bin")] + system
    # Qualification binds describe the model child, whose narrower PATH must remain intact.
    for role in ("planner", "conductor"):
        for key, value in w.env().items():
            monkeypatch.setenv(key, value)
        controller = kyloop.Controller(role)
        assert controller.child_path() == str(w.root / "bin") + ":/opt/homebrew/bin:/usr/bin:/bin"
