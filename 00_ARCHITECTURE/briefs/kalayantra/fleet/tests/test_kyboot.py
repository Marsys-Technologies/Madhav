"""kyboot (relaunch plan v2.7: pairing rule, §4a.1 action records, §7 bootstrap launches and launch
qualification KV-06, §5 job I/O, §6 job identity, §14 B-0c): the bootstrap supervisor. Every launch rule is shown
passing and — on a launch input that is otherwise launchable — refusing for its own named reason.

How the tests are staged (it is what the plan requires of the real thing):
  * the supervisor never runs from this checkout. A session fixture commits byte-identical copies of kyboot.py,
    kyschema.py, the sibling kymanifest.py, the schemas, a card and mcp.none.json into a repository of its own
    (the "immutable staged source"), builds its manifest with the real `kymanifest.py build`, and every test —
    in-process or by command line — runs the copy that lives there;
  * every command-line test goes through the real `kymanifest.py check`. In-process tests answer that one
    subprocess from memory (fixture `gate`) unless they ask for `real_gate`; everything kyboot itself reads from
    the manifest is real in both;
  * the `claude` program is always a fake shell script from fixtures/b0c; the real one is never run."""
import ast
import copy
import datetime as dt
import hashlib
import importlib.util
import json
import os
import plistlib
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
FLEET = HERE.parent
FIX = HERE / "fixtures" / "b0c"
TEMPLATES = FLEET / "templates"
sys.path.insert(0, str(FLEET))

import kyboot  # noqa: E402  — this checkout's file: constants for parametrisation; rebound to the staged copy below
import kymanifest  # noqa: E402  — the sibling's tool (read-only here): it says what a staged source must contain
import kyschema  # noqa: E402

CHECKOUT_KYBOOT = kyboot
MY_SCHEMAS = ["awaiting", "bootstrap_launch_input", "job_result", "packet", "release_receipt", "surrogate_decision"]
BRANCH = "kalayantra/kv3-b-kylock"
ITEM = "KV3-B-KYLOCK"
JOB = "J-20261011T215900Z-b1"
SESSION = "0f1e2d3c-4b5a-4978-8695-a4b3c2d1e0f9"
SECRET = "s3cr3t-value-that-must-never-be-printed"
ROLES = ["bootstrap-builder", "bootstrap-reviewer", "surrogate", "planner"]
LABEL = "in.marsys.kalayantra.boot." + JOB
DOMAIN = f"gui/{os.getuid()}"
needs_plutil = pytest.mark.skipif(not os.path.exists("/usr/bin/plutil"), reason="plutil (macOS) lints the agent's plist")
OTHER_START = "Mon Jan  1 00:00:00 2001"


def _git_dir() -> str:
    """the directory of the real git program (on macOS /usr/bin/git is a slow launcher shim around it)"""
    found = shutil.which("git") or "/usr/bin/git"
    try:
        core = subprocess.run([found, "--exec-path"], capture_output=True, text=True, timeout=30).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        core = ""
    return core if core and os.access(os.path.join(core, "git"), os.X_OK) else os.path.dirname(found)


TOOL_PATH = os.pathsep.join(dict.fromkeys([_git_dir(), "/usr/bin", "/bin"]))
GIT_ENV = {"PATH": TOOL_PATH, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
           "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid"}


def sha(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def stamp(seconds_from_now: float, suffix="Z") -> str:
    when = dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=seconds_from_now)
    return when.strftime("%Y-%m-%dT%H:%M:%S.%f") + suffix


def git_in(repo, *args, home) -> str:
    done = subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True,
                          env=dict(GIT_ENV, HOME=str(home)))
    return done.stdout.strip()


def launch_line(launch) -> list:
    """the qualified launch line, stated independently of kyboot: plan §7, in the order a qualification receipt
    records it — program, fixed flags, extra flags, MCP, denied tools, output, added directories"""
    tools = ["--disallowedTools", *launch["disallowed_tools"]] if launch["disallowed_tools"] else []
    return [launch["claude_bin"], "-p", "--setting-sources", "project", "--permission-mode",
            launch["permission_mode"], "--model", launch["model"], "--effort", launch["effort"], "--max-turns",
            str(launch["max_turns"]), *launch["extra_lean_flags"], "--strict-mcp-config", "--mcp-config",
            launch["mcp_config"], *tools, "--output-format", "stream-json", "--verbose", "--add-dir",
            launch["env"]["KY_ROOT"]]


# --------------------------------------------------------------------------------------------------------------
# the staged source (once per session) and one launchable job (per test)
# --------------------------------------------------------------------------------------------------------------
@pytest.fixture(scope="session", autouse=True)
def staged(tmp_path_factory):
    """the immutable staged source: a repository holding the approved bundle and the committed supervisor files,
    its manifest built by the real kymanifest.py, and a clone of it as the template of a job's worktree"""
    global kyboot
    top = Path(os.path.realpath(tmp_path_factory.mktemp("staged")))
    source, run = top / "source", top / "run"
    fleet = source / kymanifest.FLEET
    for rel in kymanifest.BUNDLE:
        (source / rel).parent.mkdir(parents=True, exist_ok=True)
        (source / rel).write_text("approved bundle file " + rel + "\n", encoding="utf-8")
    for role, canonical, compatibility in kymanifest.PAIRS:
        for rel in (canonical, compatibility):
            (source / rel).parent.mkdir(parents=True, exist_ok=True)
            (source / rel).write_text("generated output " + role + "\n", encoding="utf-8")
    git_in(source, "init", "-q", "-b", "kalayantra/staged-source", home=top)
    git_in(source, "add", "-A", home=top)
    git_in(source, "commit", "-q", "-m", "approved bundle", home=top)
    approved = git_in(source, "rev-parse", "HEAD", home=top)

    (fleet / "schemas").mkdir(parents=True)
    (fleet / "cards").mkdir()
    for name in ("kyboot.py", "kyschema.py", "kymanifest.py", "mcp.none.json"):
        shutil.copyfile(FLEET / name, fleet / name)
    for name in MY_SCHEMAS:
        shutil.copyfile(FLEET / "schemas" / f"{name}.json", fleet / "schemas" / f"{name}.json")
    (fleet / "cards" / "BOOTSTRAP.md").write_text("# BOOTSTRAP card (test stand-in)\n", encoding="utf-8")
    components = sorted([kymanifest.COMPONENT_LIST] + [str(p.relative_to(source)) for p in fleet.rglob("*") if p.is_file()])
    (source / kymanifest.COMPONENT_LIST).write_text("# staged components\n" + "\n".join(components) + "\n",
                                                    encoding="utf-8")
    git_in(source, "add", "-A", home=top)
    git_in(source, "commit", "-q", "-m", "staged supervisor", home=top)
    head = git_in(source, "rev-parse", "HEAD", home=top)

    review = source / "reviews" / "B0C_REVIEW.json"
    review.parent.mkdir()
    review.write_text(json.dumps({"verdict": "ACCEPTED", "reviewer_session_id": "reviewer-session-1",
                                  "source_commit": approved,
                                  "inputs": {rel: sha(source / rel) for rel in components}}), encoding="utf-8")
    run.mkdir()
    (run / "PROBES.json").write_text(json.dumps({"contexts": {}, "extra_lean_flags": {"chosen": []}}), encoding="utf-8")
    built = subprocess.run([sys.executable, str(fleet / "kymanifest.py"), "build", "--repo", str(source), "--run",
                            str(run), "--approved-commit", approved, "--review", str(review), "--out",
                            str(run / "VERSIONS.bootstrap.json")], capture_output=True, text=True,
                           env=dict(GIT_ENV, HOME=str(top), PYTHONDONTWRITEBYTECODE="1"))
    assert built.returncode == 0, built.stderr

    worktree = top / "worktree-template"
    subprocess.run(["git", "clone", "-q", str(source), str(worktree)], check=True, capture_output=True,
                   env=dict(GIT_ENV, HOME=str(top)))
    git_in(worktree, "checkout", "-q", "-b", BRANCH, home=top)
    packet = worktree / kymanifest.K / "packets" / "PACKET_KV3-B-KYLOCK_v1.md"
    packet.parent.mkdir(parents=True)
    packet.write_text("# packet\n", encoding="utf-8")
    git_in(worktree, "add", "-A", home=top)
    git_in(worktree, "commit", "-q", "-m", "bootstrap packet", home=top)
    worktree_head = git_in(worktree, "rev-parse", "HEAD", home=top)
    git_in(worktree, "gc", "-q", home=top)                               # packed: far fewer files to copy per test
    shutil.rmtree(worktree / ".git" / "hooks", ignore_errors=True)       # sample hooks only
    shutil.rmtree(worktree / ".git" / "logs", ignore_errors=True)

    fakes = {}
    for script in sorted(FIX.glob("fake_claude_*.sh")):                 # executable copies, made once: the first
        fakes[script.name] = top / "bin" / script.stem / "claude"       # run of a new file is slow on macOS, and
        fakes[script.name].parent.mkdir(parents=True)                   # the checked-in mode bit is not relied on
        shutil.copyfile(script, fakes[script.name])
        fakes[script.name].chmod(0o755)
    assert sorted(fakes) == ["fake_claude_ok.sh", "fake_claude_old.sh", "fake_claude_stubborn.sh"]
    fakes["launchctl"] = top / "bin" / "fake_launchctl" / "launchctl"   # run by this interpreter, whatever PATH says
    fakes["launchctl"].parent.mkdir(parents=True)
    body = (FIX / "fake_launchctl.py").read_text(encoding="utf-8").split("\n", 1)[1]
    fakes["launchctl"].write_text(f"#!{sys.executable}\n{body}", encoding="utf-8")
    fakes["launchctl"].chmod(0o755)

    spec = importlib.util.spec_from_file_location("kyboot_staged", fleet / "kyboot.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    kyboot = module                                                     # from here on, `kyboot` is the staged copy
    yield {"top": top, "source": source, "fleet": fleet, "approved": approved, "head": head, "review": review,
           "probes": run / "PROBES.json", "manifest": json.loads((run / "VERSIONS.bootstrap.json").read_text()),
           "worktree": worktree, "worktree_head": worktree_head, "fakes": fakes, "components": components}
    kyboot = CHECKOUT_KYBOOT


class World:
    """a launchable bootstrap job on disk: worktree, fake program, prompt/card/packet, scratch and run folders,
    the manifest of the staged source and the qualification receipt of the job's role and model"""

    def __init__(self, tmp: Path, staged: dict):
        self.staged = staged
        self.root = Path(os.path.realpath(tmp))
        self.home = self.root / "home"
        self.scratch = self.root / "scratch" / "20261011-kalayantra-v3"
        self.ky_root = self.root / "kalayantra"
        self.run_dir = self.ky_root / "run"
        self.repo = self.root / "wt" / "kalayantra-kv3-b-kylock"
        self.job_scratch = self.scratch / "jobs" / JOB
        for folder in (self.home, self.run_dir, self.repo.parent, self.job_scratch, self.root / "bin"):
            folder.mkdir(parents=True)
        shutil.copytree(staged["worktree"], self.repo, symlinks=True)
        shutil.copyfile(staged["probes"], self.run_dir / "PROBES.json")
        self.base, self.head = staged["head"], staged["worktree_head"]
        self.prompt = self.job_scratch / "prompt.md"
        self.prompt.write_text("card + packet + job header\n", encoding="utf-8")
        self.fakes = staged["fakes"]
        self.claude = self.fakes["fake_claude_ok.sh"]
        assert shutil.which("launchctl", path=str(self.fakes["launchctl"].parent)) == str(self.fakes["launchctl"])
        self.version_line = "2.1.296 (Claude Code)"
        self.context = "shell"                      # where the qualification receipt says it was earned
        self.auto_qualify = True
        self.launchd = self.root / "fake-launchd"
        self.launch_path = self.root / "launch.json"
        self.manifest_path = self.run_dir / "VERSIONS.bootstrap.json"
        self.kyboot_path = staged["fleet"] / "kyboot.py"
        self.mcp = self.repo / kymanifest.FLEET / "mcp.none.json"
        self.card = self.repo / kymanifest.FLEET / "cards" / "BOOTSTRAP.md"
        self.packet = self.repo / kymanifest.K / "packets" / "PACKET_KV3-B-KYLOCK_v1.md"
        tmp_dir = str(self.job_scratch / "tmp")
        self.launch = {
            "schema": "ky.bootstrap_launch_input/1", "job_id": JOB, "item": ITEM, "kind": "BUILD",
            "role": "bootstrap-builder", "worktree": str(self.repo), "branch": BRANCH, "base_sha": self.base,
            "claude_bin": str(self.claude), "claude_min_version": "2.1.296",
            "model": "claude-opus-5-5", "effort": "high", "permission_mode": "bypassPermissions", "max_turns": 150,
            "mcp_config": str(self.mcp), "mcp_config_sha256": sha(self.mcp),
            "prompt_path": str(self.prompt), "prompt_sha256": sha(self.prompt),
            "card_path": str(self.card), "card_sha256": sha(self.card),
            "packet_path": str(self.packet), "packet_sha256": sha(self.packet),
            "job_scratch": str(self.job_scratch), "stdout_path": str(self.job_scratch / "stdout.jsonl"),
            "stderr_path": str(self.job_scratch / "stderr.log"), "tmp_path": tmp_dir,
            "state_path": str(self.run_dir / "jobs" / JOB / "state.json"),
            "env": {"HOME": str(self.home), "PATH": "/usr/bin:/bin", "LANG": "en_US.UTF-8", "TERM": "dumb",
                    "USER": "tester", "TMPDIR": tmp_dir, "KY_ROOT": str(self.ky_root), "KY_RUN": str(self.run_dir),
                    "KY_ITEM": ITEM},
            "extra_lean_flags": ["--disable-slash-commands"], "disallowed_tools": [],
            "deadline": stamp(3600), "plan_version": "2.7", "approved_source_commit": staged["approved"],
        }
        # SAFETY: the fake launchctl's folder comes first on PATH, so that even a supervisor broken enough to look
        # `launchctl` up by name (a bug, or a mutant of the code under test) can only ever reach the fake; and
        # KY_LAUNCHCTL always names the fake, so the default /bin/launchctl is never the one that is run.
        self.environ = {"PATH": str(self.fakes["launchctl"].parent) + os.pathsep + TOOL_PATH,
                        "HOME": str(self.home), "KY_SCRATCH": str(self.scratch),
                        "KY_RUN": str(self.run_dir), "KY_SCRATCH_ROOT_OVERRIDE": str(self.root),
                        "PYTHONDONTWRITEBYTECODE": "1", "KY_TEST_MARKER": "must-not-reach-the-job",
                        "KY_LAUNCHCTL": str(self.fakes["launchctl"]), "KY_FAKE_LAUNCHD": str(self.launchd)}

    # --- building blocks ---
    def git(self, *args) -> str:
        return git_in(self.repo, *args, home=self.home)

    def commit(self, message) -> str:
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message)
        return self.git("rev-parse", "HEAD")

    def install(self, fixture_name=None, script=None, mode=0o755, says=None, private=False) -> Path:
        """make another program the job's claude_bin: a shared fixture copy, or a file of this test's own.
        `says` is the version line that program prints (the qualification receipt is written from it)."""
        if script is None and mode == 0o755 and not private:
            self.claude = self.fakes[fixture_name]
        else:
            self.claude = self.root / "bin" / "claude"
            if script is None:
                shutil.copyfile(FIX / fixture_name, self.claude)
            else:
                self.claude.write_text(script, encoding="utf-8")
            self.claude.chmod(mode)
        if says is not None:
            self.version_line = says
        elif fixture_name is not None:
            self.version_line = "2.1.239 (Claude Code)" if "old" in fixture_name else "2.1.296 (Claude Code)"
        self.launch["claude_bin"] = str(self.claude)
        return self.claude

    def set_prompt(self, text: str):
        self.prompt.write_text(text, encoding="utf-8")
        self.launch["prompt_sha256"] = sha(self.prompt)

    # --- the qualification receipt and the manifest that records it ---
    def receipt_path(self) -> Path:
        return self.run_dir / "QUALIFICATIONS" / f"{self.launch['role']}-{self.launch['model']}.json"

    def receipt(self) -> dict:
        launch, env = self.launch, self.launch["env"]
        binary = os.path.realpath(launch["claude_bin"])
        return {"schema": "ky.qualification/1", "role": launch["role"], "model": launch["model"],
                "context": self.context, "result": "PASS",
                "binds": {"claude_bin": launch["claude_bin"],
                          "claude_bin_sha256": sha(binary) if os.path.isfile(binary) and os.access(binary, os.R_OK)
                          else "0" * 64,
                          "claude_version": self.version_line, "argv": launch_line(launch), "model": launch["model"],
                          "effort": launch["effort"], "permission_mode": launch["permission_mode"],
                          "max_turns": launch["max_turns"], "deadline_seconds": 3600, "worktree": launch["worktree"],
                          "env_names": sorted(env), "child_path": env.get("PATH"),
                          "prompt_sha256": launch["prompt_sha256"], "mcp_config_sha256": launch["mcp_config_sha256"],
                          "extra_flags": list(launch["extra_lean_flags"]),
                          "disallowed_tools": list(launch["disallowed_tools"]), "add_dirs": [env["KY_ROOT"]]}}

    def qualify(self, change=None, sync=True, replace=None):
        """write the receipt that qualifies the launch input as it stands — after `change` has edited it in
        place, or as the document `replace` — and record it in the manifest"""
        try:
            receipt, path = self.receipt(), self.receipt_path()
        except (KeyError, TypeError, AttributeError):
            return None                     # a launch input too broken to qualify keeps the receipt it had
        if change is not None:
            change(receipt)
        if replace is not None:
            receipt = replace
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(receipt, indent=1) + "\n", encoding="utf-8")
        if sync:
            self.sync_manifest()
        return path

    def sync_manifest(self, change=None):
        """this run folder's manifest: the staged source's real manifest, re-observed for this folder's probes
        and qualification receipts the way kymanifest.py records them, then digested by kymanifest's own code"""
        manifest = copy.deepcopy(self.staged["manifest"])
        manifest.pop("manifest_sha256")
        manifest["probes"]["path"] = str(self.run_dir / "PROBES.json")
        recorded = []
        for path in sorted((self.run_dir / "QUALIFICATIONS").glob("*.json")):
            try:
                result = json.loads(path.read_text()).get("result")
            except (ValueError, AttributeError):
                result = None
            recorded.append({"path": str(path), "sha256": sha(path),
                             "result": result if result in ("PASS", "FAIL") else "unknown"})
        manifest["qualifications"] = recorded
        manifest["qualifications_all_pass"] = bool(recorded) and all(q["result"] == "PASS" for q in recorded)
        if change is not None:
            change(manifest)
        self.manifest_path.write_text(json.dumps(kymanifest.with_digest(manifest), indent=1, ensure_ascii=False,
                                                 sort_keys=True) + "\n", encoding="utf-8")

    def write(self) -> Path:
        self.launch_path.write_text(json.dumps(self.launch, indent=1) + "\n", encoding="utf-8")
        if self.auto_qualify:
            self.qualify()
        return self.launch_path

    def another_job(self, job_id, item=None) -> Path:
        """a second launch input in the same run folder (same role, model and program: the same qualification)"""
        launch = copy.deepcopy(self.launch)
        scratch = self.scratch / "jobs" / job_id
        scratch.mkdir(parents=True)
        (scratch / "prompt.md").write_text("FAKE_SLEEP:0\n", encoding="utf-8")
        launch.update(job_id=job_id, job_scratch=str(scratch), prompt_path=str(scratch / "prompt.md"),
                      prompt_sha256=sha(scratch / "prompt.md"), stdout_path=str(scratch / "stdout.jsonl"),
                      stderr_path=str(scratch / "stderr.log"), tmp_path=str(scratch / "tmp"),
                      state_path=str(self.run_dir / "jobs" / job_id / "state.json"))
        launch["env"]["TMPDIR"] = str(scratch / "tmp")
        if item is not None:
            launch["item"] = launch["env"]["KY_ITEM"] = item
        path = self.root / f"launch-{job_id}.json"
        path.write_text(json.dumps(launch, indent=1) + "\n", encoding="utf-8")
        return path

    # --- acting ---
    def check(self):
        return kyboot.check(str(self.write()), self.environ)

    def run(self, grace=1.0):
        return kyboot.run(str(self.write()), self.environ, grace=grace, report=lambda text: None)

    def cli(self, *args, environ=None, timeout=60):
        self.write()
        used = self.environ if environ is None else environ
        assert used.get("KY_LAUNCHCTL") and used["KY_LAUNCHCTL"] != "/bin/launchctl", "tests never reach launchd"
        return subprocess.run([sys.executable, str(self.kyboot_path), *map(str, args)], capture_output=True,
                              text=True, timeout=timeout, env=self.environ if environ is None else environ)

    def state(self, job=JOB) -> dict:
        return json.loads((self.run_dir / "jobs" / job / "state.json").read_text(encoding="utf-8"))

    def action(self, job=JOB) -> dict:
        return json.loads((self.run_dir / "actions" / f"ACT-launch-{job}.json").read_text(encoding="utf-8"))

    def lock(self, item=ITEM) -> Path:
        return self.run_dir / "locks" / f"kyboot.{item}"

    def launched(self) -> bool:
        return (self.job_scratch / "tmp" / "fake_argv.txt").exists()

    # --- the fake launchd ---
    def mode(self, **how):
        self.launchd.mkdir(exist_ok=True)
        (self.launchd / "mode.json").write_text(json.dumps(how), encoding="utf-8")

    def calls(self) -> list:
        try:
            return [json.loads(line) for line in (self.launchd / "calls.jsonl").read_text().splitlines()]
        except OSError:
            return []

    def loaded(self, label=LABEL):
        try:
            return json.loads((self.launchd / "loaded" / f"{label}.json").read_text())
        except OSError:
            return None

    def plant_loaded(self, job=JOB):
        (self.launchd / "loaded").mkdir(parents=True, exist_ok=True)
        (self.launchd / "loaded" / f"in.marsys.kalayantra.boot.{job}.json").write_text("{}", encoding="utf-8")

    def wait_for(self, what, limit=40.0):
        end = time.monotonic() + limit
        while time.monotonic() < end:
            try:
                got = what()
            except (OSError, ValueError, KeyError):
                got = None
            if got:
                return got
            time.sleep(0.05)
        raise AssertionError("waited in vain")

    def wait_ended(self, job=JOB) -> dict:
        """the submitted job's final state, once its supervisor process has gone too"""
        state = self.wait_for(lambda: self.state(job) if self.state(job)["phase"] in ("ended", "launch_failed") else None)
        assert gone(state["supervisor_pid"], wait=20)
        return self.state(job)

    def reap(self):
        """test hygiene only: if a (failing) test left its fake job alive, end that job's own process group"""
        leaders = set()
        for tmp in self.scratch.glob("jobs/*/tmp"):
            for name in ("fake_pid.txt", "fake_pgid.txt"):
                try:
                    leaders.add(int((tmp / name).read_text().strip()))
                except (OSError, ValueError):
                    pass
        for state in self.run_dir.glob("jobs/*/state.json"):
            try:
                leaders.add(int(json.loads(state.read_text())["pid"]))
            except (OSError, ValueError, TypeError, KeyError):
                pass
        for leader in leaders:
            try:
                if leader <= 1 or os.getpgid(leader) != leader or leader == os.getpgrp():
                    continue
                shown = subprocess.run(["ps", "-o", "command=", "-p", str(leader)], capture_output=True, text=True)
                if str(self.root) in shown.stdout:           # still this test's job, not a reused process id
                    os.killpg(leader, signal.SIGKILL)
            except OSError:
                pass


@pytest.fixture
def world(tmp_path, staged):
    made = World(tmp_path, staged)
    yield made
    made.reap()


@pytest.fixture
def real_gate():
    """ask for this fixture to let an in-process test run the real `kymanifest.py check` subprocess"""
    return True


@pytest.fixture(autouse=True)
def gate(request, monkeypatch):
    """in-process tests answer the manifest-check subprocess from memory (and record that it was asked);
    a test that names `real_gate`, and every command-line test, runs the real kymanifest.py"""
    asked = []
    if "real_gate" not in request.fixturenames:
        def answered(kymanifest_path, manifest_path, source_repo, ky_run, environ):
            asked.append({"kymanifest": kymanifest_path, "manifest": manifest_path, "repo": source_repo, "run": ky_run})
            digest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))["manifest_sha256"]
            return 0, json.dumps({"ok": True, "manifest_sha256": digest, "components": 0}), ""
        monkeypatch.setattr(kyboot, "run_manifest_check", answered)
    return asked


def refused(world, *needles):
    """the launch input is refused and ONE finding carries every needle"""
    result = world.check()
    assert not result.ok, "accepted, but a refusal was expected"
    assert any(all(n in line for n in needles) for line in result.findings), \
        f"no finding carries all of {needles!r}:\n" + "\n".join(result.findings)
    return result.findings


def gone(pid: int, wait=5.0) -> bool:
    limit = time.monotonic() + wait
    while time.monotonic() < limit:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return True
        except PermissionError:
            pass
        time.sleep(0.05)
    return False


def dead_process():
    """(pid, start identity) of a process of ours that has exited and been collected"""
    proc = subprocess.Popen(["/bin/sleep", "30"])
    start = kyboot.process_start(proc.pid)
    proc.kill()
    proc.wait()
    assert start and gone(proc.pid)
    return proc.pid, start


# --------------------------------------------------------------------------------------------------------------
# the staging itself
# --------------------------------------------------------------------------------------------------------------
def test_the_supervisor_under_test_is_the_staged_copy_and_is_byte_identical_to_this_checkout(staged):
    assert Path(kyboot.__file__) == staged["fleet"] / "kyboot.py" != Path(CHECKOUT_KYBOOT.__file__)
    for name in ("kyboot.py", "kyschema.py", "kymanifest.py", "mcp.none.json"):
        assert (staged["fleet"] / name).read_bytes() == (FLEET / name).read_bytes(), name
    for name in MY_SCHEMAS:
        assert (staged["fleet"] / "schemas" / f"{name}.json").read_bytes() == \
            (FLEET / "schemas" / f"{name}.json").read_bytes(), name
    assert kyboot.schema_names() == MY_SCHEMAS
    for constant in ("PATH_FIELDS", "HASHED_FILES", "BENEATH_JOB_SCRATCH", "ENV_ALLOWLIST", "SUPERVISOR_CODE"):
        assert getattr(kyboot, constant) == getattr(CHECKOUT_KYBOOT, constant), constant


def test_the_copied_repository_is_a_real_work_tree_on_the_expected_branch(world, staged):
    assert world.git("rev-parse", "--show-toplevel") == str(world.repo)
    assert world.git("rev-parse", "--abbrev-ref", "HEAD") == BRANCH
    assert world.git("rev-parse", "HEAD") == world.head != world.base
    assert world.git("status", "--porcelain") == ""
    assert world.git("cat-file", "-t", staged["approved"]) == "commit"
    assert world.mcp.read_bytes() == (FLEET / "mcp.none.json").read_bytes()


# --------------------------------------------------------------------------------------------------------------
# check — the positive case, then one refusal per rule
# --------------------------------------------------------------------------------------------------------------
def test_a_complete_launch_input_passes_check_in_process_and_by_cli(world, gate):
    result = world.check()
    assert result.findings == []
    assert result.facts["claude_version"] == "2.1.296 (Claude Code)"
    assert result.facts["worktree_head"] == world.head
    assert result.facts["scratch_root_override"] is True
    assert len(gate) == 1                                     # the manifest gate was asked
    cli = world.cli("check", world.launch_path)
    assert cli.returncode == 0, cli.stderr
    assert cli.stdout.startswith("CHECK-PASSED") and JOB in cli.stdout and "role bootstrap-builder" in cli.stdout
    assert not (world.run_dir / "jobs").exists() and not world.launched()      # check launches nothing
    assert not (world.run_dir / "actions").exists() and not (world.run_dir / "locks").exists()


def test_the_fixture_launch_input_is_refused_on_this_host_for_real_reasons(tmp_path):
    """the static example names paths that are not prepared here: shape-valid is not launchable"""
    result = kyboot.check(str(FIX / "launch_input.json"), {"PATH": TOOL_PATH, "KY_SCRATCH": str(tmp_path),
                                                           "KY_SCRATCH_ROOT_OVERRIDE": str(tmp_path),
                                                           "KY_RUN": str(tmp_path / "run")})
    assert not result.ok and not any(line.startswith("schema:") for line in result.findings)


def test_a_missing_field_refuses_and_names_the_field(world):
    del world.launch["deadline"]
    refused(world, "schema:", "required property 'deadline' is missing")
    cli = world.cli("check", world.launch_path)
    assert cli.returncode == 1 and "required property 'deadline' is missing" in cli.stderr
    assert "nothing was launched" in cli.stderr


def test_every_field_of_the_launch_input_is_required(world):
    required = kyschema.load_json(FLEET / "schemas" / "bootstrap_launch_input.json")["required"]
    assert len(required) == 33 and "role" in required
    complete = copy.deepcopy(world.launch)
    world.write()
    world.auto_qualify = False
    for field in required:
        world.launch = copy.deepcopy(complete)
        del world.launch[field]
        refused(world, "schema:", f"required property '{field}' is missing")


def test_absent_or_unknown_permission_mode_refuses_and_each_named_mode_passes(world):
    for mode in ("bypassPermissions", "acceptEdits", "default", "plan"):
        world.launch["permission_mode"] = mode
        assert world.check().findings == []
    world.launch["permission_mode"] = "dontAsk"
    refused(world, "schema:", "$.permission_mode", "is not one of")
    del world.launch["permission_mode"]
    refused(world, "schema:", "required property 'permission_mode' is missing")


def test_an_unreadable_or_duplicate_key_launch_input_refuses(world):
    world.write()
    world.launch_path.write_text('{"env": {"HOME": "/a"}, "env": {"PGPASSWORD": "x"}}', encoding="utf-8")
    result = kyboot.check(str(world.launch_path), world.environ)
    assert any("duplicate key 'env'" in line for line in result.findings)
    result = kyboot.check(str(world.root / "absent.json"), world.environ)
    assert any("launch input: cannot read" in line for line in result.findings)


def test_an_unfilled_placeholder_refuses_wherever_it_is(world):
    world.launch["card_path"] = "<CARD_PATH>"
    refused(world, "$.card_path: unfilled placeholder '<CARD_PATH>'")
    world.launch["card_path"] = str(world.card)
    world.launch["env"]["KY_FLEET"] = "/Users/Dev/<KY_FLEET>"
    refused(world, "$.env.KY_FLEET: unfilled placeholder")
    del world.launch["env"]["KY_FLEET"]
    world.launch["env"]["<NAME>"] = "x"
    refused(world, "$.env: unfilled placeholder in the name '<NAME>'")
    del world.launch["env"]["<NAME>"]
    assert world.check().findings == []


@pytest.mark.parametrize("field", kyboot.PATH_FIELDS)
def test_a_relative_path_refuses(world, field):
    world.launch[field] = "relative/" + os.path.basename(world.launch[field])
    refused(world, f"{field}: not an absolute path")


def test_a_path_that_is_not_normalised_refuses(world):
    world.launch["worktree"] = str(world.repo) + "/../" + world.repo.name
    refused(world, "worktree: path is not normalised")
    world.launch["worktree"] = str(world.repo) + "/"
    refused(world, "worktree: path is not normalised")


def test_path_fields_cover_every_path_the_launch_input_names():
    properties = kyschema.load_json(FLEET / "schemas" / "bootstrap_launch_input.json")["properties"]
    named = {name for name in properties if name.endswith("_path") or name in
             ("worktree", "claude_bin", "mcp_config", "job_scratch")}
    assert named == set(kyboot.PATH_FIELDS)


# ---- worktree, branch, base -------------------------------------------------------------------------------------
def test_a_missing_worktree_refuses(world):
    world.launch["worktree"] = str(world.root / "absent")
    refused(world, "worktree: does not exist or is not a directory")


def test_a_directory_that_is_not_a_git_work_tree_refuses(world):
    plain = world.root / "plain"
    plain.mkdir()
    (plain / ".git").write_text("gitdir: /nonexistent/kyboot-test\n", encoding="utf-8")   # no parent repository
    world.launch["worktree"] = str(plain)                                                  # can answer for it
    refused(world, f"worktree: not a git work tree: {plain}")


def test_a_subdirectory_of_a_work_tree_refuses(world):
    world.launch["worktree"] = str(world.repo / "00_ARCHITECTURE")
    refused(world, "worktree: is not the top level of its git work tree")


def test_the_wrong_branch_refuses(world):
    world.launch["branch"] = "kalayantra/other"
    refused(world, "branch: the worktree is on 'kalayantra/kv3-b-kylock'", "says 'kalayantra/other'")


def test_a_detached_head_refuses(world):
    world.git("checkout", "-q", "--detach")
    refused(world, "branch: the worktree is on 'a detached HEAD'")


def test_a_branch_without_a_commit_refuses(world):
    empty = world.root / "wt" / "empty"
    empty.mkdir()
    git_in(empty, "init", "-q", "-b", BRANCH, home=world.home)
    world.launch["worktree"] = str(empty)
    refused(world, "worktree: HEAD does not name a commit")


def test_a_base_that_is_not_an_ancestor_of_head_refuses(world):
    world.git("checkout", "-q", "-b", "side", world.base)
    (world.repo / "side.txt").write_text("side\n", encoding="utf-8")
    side = world.commit("side")
    world.git("checkout", "-q", BRANCH)
    world.launch["base_sha"] = side
    refused(world, f"base_sha: {side} is not an ancestor of HEAD {world.head}")
    world.launch["base_sha"] = world.head                     # HEAD is its own ancestor
    assert world.check().findings == []


def test_a_base_or_approved_commit_that_does_not_exist_refuses(world):
    world.launch["base_sha"] = "f" * 40
    refused(world, "base_sha: " + "f" * 40 + " is not a commit in the worktree's repository")
    world.launch["base_sha"] = world.base
    world.launch["approved_source_commit"] = "e" * 40
    refused(world, "approved_source_commit: " + "e" * 40 + " is not a commit in the worktree's repository")


def test_git_redirection_variables_in_the_supervisor_environment_are_not_obeyed(world, real_gate):
    """neither by kyboot's own git questions nor by the manifest tool it starts"""
    other = world.root / "other"
    other.mkdir()
    git_in(other, "init", "-q", "-b", "elsewhere", home=world.home)
    world.environ["GIT_DIR"] = str(other / ".git")
    world.environ["GIT_WORK_TREE"] = str(other)
    assert world.check().findings == []


GIT_ANSWERS = [
    ("not inside a work tree", 0, "false\n{wt}\n{head}\nrefs/heads/{branch}", "worktree: not a git work tree"),
    ("no answer", 128, "", "worktree: not a git work tree"),
    ("only the first answer", 128, "true", "worktree: not a git work tree"),
    ("another top level", 0, "true\n/somewhere/else\n{head}\nrefs/heads/{branch}", "worktree: is not the top level"),
    ("git failed after answering", 128, "true\n{wt}\n{head}\nrefs/heads/{branch}", "worktree: HEAD does not name a commit"),
    ("no branch line", 0, "true\n{wt}\n{head}", "worktree: HEAD does not name a commit"),
    ("HEAD is not a commit id", 0, "true\n{wt}\nHEAD\nrefs/heads/{branch}", "worktree: HEAD does not name a commit"),
    ("a fifth line", 0, "true\n{wt}\n{head}\nrefs/heads/{branch}\nextra", "worktree: HEAD does not name a commit"),
]


@pytest.mark.parametrize("what,code,answer,reason", GIT_ANSWERS, ids=[c[0] for c in GIT_ANSWERS])
def test_gits_answer_about_the_worktree_is_read_strictly(world, monkeypatch, what, code, answer, reason):
    """the one combined question (inside · top level · HEAD commit · HEAD branch): any answer that is not exactly
    the four expected lines from a successful git is a refusal, never a guess"""
    real = kyboot._git

    def answered(worktree, environ, *args):
        if args[:2] == ("rev-parse", "--is-inside-work-tree") and worktree == str(world.repo):
            return code, answer.format(wt=world.repo, head=world.head, branch=BRANCH)
        return real(worktree, environ, *args)

    assert world.check().findings == []
    monkeypatch.setattr(kyboot, "_git", answered)
    refused(world, reason)


# ---- the program ------------------------------------------------------------------------------------------------
def test_a_program_below_the_pinned_version_refuses(world, capsys):
    world.install("fake_claude_old.sh")
    refused(world, "claude_bin: version 2.1.239 is below the pinned minimum 2.1.296")
    assert world.run() == 1 and "2.1.239" in capsys.readouterr().err
    assert not (world.job_scratch / "tmp" / "fake_old_was_launched.txt").exists()
    assert not Path(world.launch["state_path"]).exists()


@pytest.mark.parametrize("line", ["Claude Code (version unknown)", "v2.1.296", "2.1.296-beta.1", "2.1", ""])
def test_an_unparsable_version_refuses(world, line):
    world.install(script=f"#!/bin/bash\necho '{line}'\n", says=line)
    refused(world, "claude_bin: version output is not X.Y.Z")


@pytest.mark.parametrize("line", ["2.1.296", "2.1.297 (Claude Code)", "2.1.1000", "2.10.0", "3.0.0 (Claude Code)"])
def test_the_version_comparison_is_numeric_and_at_or_above_the_pin_passes(world, line):
    world.install(script=f"#!/bin/bash\necho '{line}'\n", says=line)
    assert world.check().findings == []


@pytest.mark.parametrize("line,expected", [("2.1.295", "2.1.295"), ("2.0.999", "2.0.999"), ("1.9.999", "1.9.999")])
def test_every_lower_version_refuses(world, line, expected):
    world.install(script=f"#!/bin/bash\necho '{line} (Claude Code)'\n", says=line)
    refused(world, f"claude_bin: version {expected} is below the pinned minimum 2.1.296")


def test_a_program_that_is_missing_not_executable_or_failing_refuses(world):
    world.install("fake_claude_ok.sh", mode=0o644)
    refused(world, "claude_bin: not executable")
    world.install(script="#!/bin/bash\necho '2.1.296'\nexit 3\n", says="2.1.296")
    refused(world, "claude_bin: --version exited 3")
    world.claude.unlink()
    refused(world, "claude_bin: does not exist or is not a file")


def test_a_program_that_cannot_be_started_refuses(world):
    world.install(script="#!/nonexistent/interpreter\n", says="2.1.296")
    refused(world, "claude_bin: --version could not be run")


def test_parse_version():
    assert kyboot.parse_version("2.1.296 (Claude Code)\n") == (2, 1, 296)
    assert kyboot.parse_version("10.0.0") == (10, 0, 0)
    assert kyboot.parse_version("2.1.296-beta") is None and kyboot.parse_version("") is None
    assert kyboot.parse_version("claude 2.1.296") is None
    assert (2, 1, 1000) > (2, 1, 296) > (2, 1, 239)


# ---- hashes and the MCP configuration -----------------------------------------------------------------------------
@pytest.mark.parametrize("path_field,hash_field", kyboot.HASHED_FILES)
def test_a_changed_file_refuses_by_hash(world, path_field, hash_field):
    with open(world.launch[path_field], "ab") as handle:
        handle.write(b"tampered\n")
    refused(world, f"{path_field}: sha256 mismatch", f"{hash_field} says {world.launch[hash_field]}")


@pytest.mark.parametrize("path_field,hash_field", kyboot.HASHED_FILES)
def test_a_missing_hashed_file_refuses(world, path_field, hash_field):
    os.unlink(world.launch[path_field])
    refused(world, f"{path_field}: does not exist or is not a file")


@pytest.mark.skipif(os.geteuid() == 0, reason="root reads every file")
def test_an_unreadable_hashed_file_refuses(world):
    packet = Path(world.launch["packet_path"])
    packet.chmod(0o000)
    try:
        refused(world, "packet_path: cannot be read")
    finally:
        packet.chmod(0o644)


def test_hashed_files_are_the_four_the_plan_names():
    assert sorted(kyboot.HASHED_FILES) == sorted([("prompt_path", "prompt_sha256"), ("card_path", "card_sha256"),
                                                  ("packet_path", "packet_sha256"), ("mcp_config", "mcp_config_sha256")])


@pytest.mark.parametrize("content,reason", [
    ('{"mcpServers":{"marsys":{"command":"x"}}}\n', "the content must be exactly"),
    ('{"mcpServers":{},"other":1}\n', "the content must be exactly"),
    ('{}\n', "the content must be exactly"),
    ('[]\n', "the content must be exactly"),
    ('{"mcpServers":[]}\n', "the content must be exactly"),
    ('{"mcpServers":{},"mcpServers":{"x":{}}}\n', "duplicate key 'mcpServers'"),
    ('{"mcpServers":{}', "is not acceptable JSON"),
])
def test_an_mcp_configuration_that_is_not_the_empty_one_refuses_even_when_its_hash_matches(world, content, reason):
    Path(world.launch["mcp_config"]).write_text(content, encoding="utf-8")
    world.launch["mcp_config_sha256"] = sha(world.launch["mcp_config"])
    findings = refused(world, "mcp_config:", reason)
    assert not any("sha256 mismatch" in line for line in findings)
    assert any("is not the reviewed" in line for line in findings)       # and it is not the manifest's file either


def test_the_staged_empty_mcp_configuration_is_byte_exact(world):
    assert (FLEET / "mcp.none.json").read_bytes() == b'{"mcpServers":{}}\n'
    assert world.launch["mcp_config_sha256"] == sha(FLEET / "mcp.none.json")


# ---- scratch and state locations -----------------------------------------------------------------------------------
def test_ky_scratch_is_required(world):
    del world.environ["KY_SCRATCH"]
    refused(world, "KY_SCRATCH: not set in the environment")


def test_ky_scratch_must_be_an_existing_absolute_directory(world):
    world.environ["KY_SCRATCH"] = str(world.root / "no-such-scratch")
    refused(world, "KY_SCRATCH:", "is not an existing absolute directory")
    world.environ["KY_SCRATCH"] = "scratch"
    refused(world, "KY_SCRATCH: 'scratch' is not an existing absolute directory")


def test_ky_run_must_be_a_normalised_absolute_path(world):
    for bad in ("run", str(world.run_dir) + "/", str(world.ky_root) + "/x/../run"):
        world.environ["KY_RUN"] = bad
        refused(world, "KY_RUN:", "is not a normalised absolute path")


def test_a_tmp_path_that_is_a_file_refuses(world):
    Path(world.launch["tmp_path"]).write_text("not a directory\n", encoding="utf-8")
    refused(world, "tmp_path:", "exists and is not a directory")


def test_ky_scratch_outside_the_root_refuses(world):
    inner = world.root / "inner-root"
    inner.mkdir()
    world.environ["KY_SCRATCH_ROOT_OVERRIDE"] = str(inner)
    refused(world, f"KY_SCRATCH: {world.scratch} is not beneath the scratch root {inner}")


def test_without_the_override_the_root_is_the_owner_scratch_folder(world):
    del world.environ["KY_SCRATCH_ROOT_OVERRIDE"]
    world.environ["KY_SCRATCH"] = str(FIX)                    # exists, and is not under the owner's scratch root
    refused(world, "KY_SCRATCH:", "is not beneath the scratch root /Users/Dev/scratch.noindex")
    assert kyboot.DEFAULT_SCRATCH_ROOT == "/Users/Dev/scratch.noindex"


@pytest.mark.skipif(not str(Path(__file__).resolve()).startswith("/Users/Dev/") or
                    not os.path.isdir("/Users/Dev/scratch.noindex"), reason="the owner's scratch root is not on this host")
def test_without_the_override_a_scratch_folder_under_the_owner_root_passes(world):
    if not str(world.root).startswith("/Users/Dev/scratch.noindex/"):
        pytest.skip("pytest's base temp is not under the owner's scratch root")
    del world.environ["KY_SCRATCH_ROOT_OVERRIDE"]
    result = world.check()
    assert result.findings == [] and result.facts["scratch_root_override"] is False


def test_the_override_cannot_point_at_a_system_temporary_directory_or_at_nothing(world):
    world.environ["KY_SCRATCH_ROOT_OVERRIDE"] = "/tmp"
    refused(world, "KY_SCRATCH_ROOT_OVERRIDE:", "under a system temporary directory")
    world.environ["KY_SCRATCH_ROOT_OVERRIDE"] = str(world.root / "absent")
    refused(world, "KY_SCRATCH_ROOT_OVERRIDE: is set but is not an existing absolute directory")
    world.environ["KY_SCRATCH_ROOT_OVERRIDE"] = ""
    refused(world, "KY_SCRATCH_ROOT_OVERRIDE: is set but is not an existing absolute directory")


def test_a_job_scratch_that_is_not_the_jobs_folder_of_this_job_refuses(world):
    other = world.scratch / "jobs" / "J-OTHER"
    other.mkdir()
    world.launch["job_scratch"] = str(other)
    refused(world, f"job_scratch: {other} is not <KY_SCRATCH>/jobs/<job_id> = {world.job_scratch}")


def test_a_job_scratch_that_is_a_symlink_out_of_the_scratch_folder_refuses(world):
    elsewhere = world.root / "elsewhere"
    shutil.move(str(world.job_scratch), str(elsewhere))
    os.symlink(str(elsewhere), str(world.job_scratch))
    refused(world, f"job_scratch: {elsewhere} is not <KY_SCRATCH>/jobs/<job_id> = {world.job_scratch}")


@pytest.mark.parametrize("field", kyboot.BENEATH_JOB_SCRATCH)
def test_job_files_outside_the_job_scratch_refuse(world, field):
    outside = world.root / "outside"
    outside.mkdir()
    target = outside / os.path.basename(world.launch[field])
    if field == "prompt_path":
        shutil.copyfile(world.prompt, target)
    world.launch[field] = str(target)
    refused(world, f"{field}: {target} is not beneath job_scratch {world.job_scratch}")


def test_beneath_job_scratch_names_the_four_paths_of_plan_section_5():
    assert sorted(kyboot.BENEATH_JOB_SCRATCH) == ["prompt_path", "stderr_path", "stdout_path", "tmp_path"]


def test_job_files_that_collide_refuse(world):
    world.launch["stderr_path"] = world.launch["stdout_path"]
    refused(world, "must all differ")
    world.launch["stderr_path"] = str(world.job_scratch / "stderr.log")
    world.launch["stdout_path"] = str(world.job_scratch / "result.json")
    refused(world, "must all differ")


def test_a_state_path_that_is_not_the_job_state_file_refuses(world):
    world.launch["state_path"] = str(world.run_dir / "jobs" / "J-OTHER" / "state.json")
    refused(world, "state_path:", f"is not <KY_RUN>/jobs/<job_id>/state.json = {world.run_dir}/jobs/{JOB}/state.json")


def test_ky_run_defaults_to_the_campaign_run_folder(world):
    world.write()
    del world.environ["KY_RUN"]
    result = kyboot.check(str(world.launch_path), world.environ, str(world.manifest_path))
    assert any(f"state_path: {world.launch['state_path']} is not <KY_RUN>/jobs/<job_id>/state.json = "
               f"/Users/Dev/kalayantra/run/jobs/{JOB}/state.json" in line for line in result.findings)
    assert kyboot.DEFAULT_KY_RUN == "/Users/Dev/kalayantra/run" and result.facts["ky_run"] == kyboot.DEFAULT_KY_RUN


# ---- the job environment --------------------------------------------------------------------------------------------
@pytest.mark.parametrize("name", ["DATABASE_URL", "KALA_DATABASE_URL", "PGPASSWORD", "ANTHROPIC_API_KEY",
                                  "GITHUB_TOKEN", "TOKEN", "MY_SECRET_THING", "client_secret", "Anthropic_Api_Key"])
def test_a_credential_bearing_name_in_the_job_environment_refuses_without_echoing_its_value(world, name):
    world.launch["env"][name] = SECRET
    findings = refused(world, f"env: {name} is a forbidden credential-bearing name")
    assert any(f"env: {name} is not in the plan §7 allowlist" in line for line in findings)
    assert not any(SECRET in line for line in findings)


def test_a_credential_in_the_job_environment_is_refused_by_every_command_without_its_value(world):
    world.launch["env"]["PGPASSWORD"] = SECRET
    for command in ("check", "argv", "run"):
        cli = world.cli(command, world.launch_path)
        assert cli.returncode == 1 and "env: PGPASSWORD is a forbidden credential-bearing name" in cli.stderr
        assert SECRET not in cli.stdout + cli.stderr
    assert not world.launched() and not (world.run_dir / "jobs").exists()


@pytest.mark.parametrize("name", ["FOO", "NODE_OPTIONS", "DYLD_INSERT_LIBRARIES", "LD_PRELOAD", "CLAUDE_CONFIG_DIR", "home"])
def test_a_name_outside_the_allowlist_refuses_for_that_reason_alone(world, name):
    world.launch["env"][name] = "x"
    findings = refused(world, f"env: {name} is not in the plan §7 allowlist")
    assert not any("forbidden credential-bearing" in line for line in findings)


def test_every_allowlisted_name_is_accepted_and_the_allowlist_is_the_plan_line(world):
    assert sorted(kyboot.ENV_ALLOWLIST) == sorted([
        "HOME", "PATH", "LANG", "TERM", "USER", "TMPDIR", "ZDOTDIR", "KY_ROOT", "KY_RUN", "KY_FLEET", "KY_STREAM",
        "KY_LANE", "KY_ITEM", "KY_PY", "SE_EPHE_PATH", "SWE_EPHE_PATH", "TESTS"])
    assert not any(kyboot.forbidden_env_name(name) for name in kyboot.ENV_ALLOWLIST)
    world.launch["env"].update({
        "ZDOTDIR": str(world.ky_root / "zdotdir"),
        "KY_FLEET": str(world.ky_root / "fleet_live"), "KY_STREAM": "K", "KY_LANE": "b1",
        "KY_PY": str(world.ky_root / "venv" / "bin" / "python"), "SE_EPHE_PATH": str(world.ky_root / "ephe"),
        "SWE_EPHE_PATH": str(world.ky_root / "ephe"), "TESTS": "a/test_x.py\nb/test_y.py"})
    assert set(world.launch["env"]) == set(kyboot.ENV_ALLOWLIST)
    assert world.check().findings == []


def test_forbidden_env_name_pattern():
    for name in ("DATABASE_URL", "X_DATABASE_URL", "PGPASSWORD", "ANTHROPIC_API_KEY", "A_TOKEN_B", "SECRETS"):
        assert kyboot.forbidden_env_name(name), name
    for name in ("DATABASE_URLS", "PGPASS", "ANTHROPIC_API", "TOKE", "HOME", "KY_ROOT"):
        assert not kyboot.forbidden_env_name(name), name


@pytest.mark.parametrize("name", ["HOME", "PATH", "KY_ROOT", "TMPDIR"])
def test_a_missing_required_environment_name_refuses(world, name):
    assert kyboot.ENV_REQUIRED == ("HOME", "PATH", "KY_ROOT", "TMPDIR")
    del world.launch["env"][name]
    refused(world, f"env: required name {name} is missing")


def test_environment_values_must_be_strings_and_paths_absolute(world):
    world.launch["env"]["LANG"] = 5
    refused(world, "env.LANG: the value must be a string without NUL")
    world.launch["env"]["LANG"] = "en_US.UTF-8"
    world.launch["env"]["KY_FLEET"] = "fleet_live"
    refused(world, "env.KY_FLEET: not an absolute path")
    del world.launch["env"]["KY_FLEET"]
    world.launch["env"]["PATH"] = "bin:/usr/bin:/bin"
    refused(world, "env.PATH: entry 'bin' is not an absolute path")
    world.launch["env"]["PATH"] = "/usr/bin::/bin"
    refused(world, "env.PATH: entry '' is not an absolute path")


def test_environment_values_must_agree_with_the_launch_input(world):
    world.launch["env"]["TMPDIR"] = str(world.root)
    refused(world, "env.TMPDIR:", "must equal tmp_path")
    world.launch["env"]["TMPDIR"] = world.launch["tmp_path"]
    world.launch["env"]["KY_RUN"] = str(world.root / "other-run")
    refused(world, "env.KY_RUN:", "differs from the supervisor's KY_RUN")
    world.launch["env"]["KY_RUN"] = str(world.run_dir)
    world.launch["env"]["KY_ITEM"] = "KV3-B-OTHER"
    refused(world, "env.KY_ITEM:", "differs from item")
    world.launch["env"]["KY_ITEM"] = ITEM
    world.launch["env"]["KY_ROOT"] = str(world.root / "no-such-root")
    refused(world, "env.KY_ROOT:", "is not an existing directory")


def test_the_program_is_not_probed_and_not_qualified_with_a_refused_environment(world):
    marker = world.root / "version-was-run"
    world.install(script=f"#!/bin/bash\necho ran > '{marker}'\necho '2.1.296'\n", says="2.1.296")
    world.launch["env"]["PGPASSWORD"] = SECRET
    findings = refused(world, "claude_bin: --version was not run because the job environment is refused")
    assert "qualification: not compared because the job environment is refused" in findings
    assert not marker.exists()
    del world.launch["env"]["PGPASSWORD"]
    assert world.check().findings == [] and marker.exists()


# ---- flags, effort, turns, deadline -----------------------------------------------------------------------------------
@pytest.mark.parametrize("flag", ["--bare", "--dangerously-skip-permissions", "--mcp-config", "--settings",
                                  "--setting-sources", "--mcp-config=/x/mcp.json", "--settings=/x/settings.json",
                                  "--setting-sources=user", "--bare=1"])
def test_the_five_forbidden_flags_refuse(world, flag):
    world.launch["extra_lean_flags"].append(flag)
    refused(world, f"extra_lean_flags: {flag.split('=')[0]} is forbidden")


@pytest.mark.parametrize("flag", ["--permission-mode=plan", "--model=claude-sonnet-5-5", "--effort=xhigh",
                                  "--max-turns=999", "--strict-mcp-config", "--output-format=text", "--verbose",
                                  "--add-dir=/", "--print", "--dangerously-load-development-channels",
                                  "--allow-dangerously-skip-permissions"])
def test_flags_the_launch_line_owns_or_that_bypass_permissions_refuse(world, flag):
    world.launch["extra_lean_flags"] = [flag]
    refused(world, f"extra_lean_flags: {flag.split('=')[0]} is forbidden")


def test_flag_refusals_never_echo_a_flag_value(world):
    world.write()
    world.auto_qualify = False                               # the receipt on disk qualifies the line without it
    world.launch["extra_lean_flags"] = [f"--settings={SECRET}"]
    findings = refused(world, "extra_lean_flags: --settings is forbidden")
    assert any("binds.argv is not this launch's line" in line and '"--settings=…"' in line for line in findings)
    assert not any(SECRET in line for line in findings)
    world.launch["extra_lean_flags"] = [f"--api key {SECRET}"]
    findings = refused(world, "schema: $.extra_lean_flags[0]: refused by the launch-input schema (value not shown)")
    assert not any(SECRET in line for line in findings)
    world.launch["extra_lean_flags"] = []
    world.launch["disallowed_tools"] = [f"-{SECRET}"]
    assert not any(SECRET in line for line in refused(world, "schema: $.disallowed_tools[0]: refused"))


def test_lean_flags_that_are_not_forbidden_pass(world):
    world.launch["extra_lean_flags"] = ["--disable-slash-commands", "--no-session-persistence=false"]
    assert world.check().findings == []
    world.launch["extra_lean_flags"] = []
    assert world.check().findings == []


@pytest.mark.parametrize("kind,effort,expected", [("BUILD", "xhigh", "high"), ("REWORK", "xhigh", "high"),
                                                  ("VERIFY", "xhigh", "high"), ("ARTIFACT", "xhigh", "high"),
                                                  ("PLAN", "high", "xhigh")])
def test_the_wrong_effort_for_the_kind_refuses(world, kind, effort, expected):
    world.launch.update(kind=kind, effort=effort, max_turns=1)
    refused(world, f"effort: kind {kind} requires effort {expected}, found {effort}")


@pytest.mark.parametrize("kind,cap", [("BUILD", 150), ("REWORK", 100), ("VERIFY", 60), ("ARTIFACT", 60), ("PLAN", 300)])
def test_the_turn_cap_of_each_kind_is_enforced_at_its_boundary(world, kind, cap):
    assert kyboot.TURN_CAPS[kind] == cap
    world.launch.update(kind=kind, effort="xhigh" if kind == "PLAN" else "high", max_turns=cap)
    assert world.check().findings == []
    world.launch["max_turns"] = cap + 1
    refused(world, f"max_turns: {cap + 1} exceeds the cap {cap} for kind {kind}")


def test_turn_caps_cover_exactly_the_kinds_the_schema_admits():
    kinds = kyschema.load_json(FLEET / "schemas" / "bootstrap_launch_input.json")["properties"]["kind"]["enum"]
    assert sorted(kinds) == sorted(kyboot.TURN_CAPS)


def test_a_deadline_in_the_past_refuses(world):
    world.launch["deadline"] = stamp(-1)
    refused(world, "deadline:", "is not in the future")
    world.launch["deadline"] = "2020-01-01T00:00:00Z"
    refused(world, "deadline: 2020-01-01T00:00:00Z is not in the future")


@pytest.mark.parametrize("text", ["2099-01-01 00:00:00", "2099-01-01T00:00:00", "2099-01-01T00:00:00+05:30",
                                  "2099-01-01T00:00:00-00:00", "2099-13-40T00:00:00Z", "2099-01-01T25:00:00Z",
                                  "tomorrow", "4070908800", "2099-01-01T00:00:00Z\n"])
def test_a_deadline_that_is_not_utc_iso_8601_refuses(world, text):
    world.launch["deadline"] = text
    refused(world, "deadline: not a UTC ISO-8601 timestamp")


def test_a_future_deadline_in_either_utc_spelling_passes(world):
    for text in (stamp(60), stamp(60, "+00:00"), "2099-01-01T00:00:00Z"):
        world.launch["deadline"] = text
        assert world.check().findings == []
    assert kyboot.parse_utc("1970-01-01T00:00:01.5Z") == 1.5
    assert kyboot.parse_utc("1970-01-01T00:00:00+00:00") == 0.0


@pytest.mark.parametrize("role", ROLES)
def test_a_missing_or_non_positive_turn_limit_or_deadline_refuses_for_every_role(world, role):
    """plan §7 KV-06: 'Missing or non-positive turn limits or wall-clock deadlines refuse launch for every role'"""
    world.launch["role"] = role
    assert world.check().findings == []
    good = copy.deepcopy(world.launch)
    world.auto_qualify = False
    for turns in (0, -5):
        world.launch = dict(copy.deepcopy(good), max_turns=turns)
        refused(world, "schema: $.max_turns:", "is less than the minimum 1")
    for field in ("max_turns", "deadline"):
        world.launch = copy.deepcopy(good)
        del world.launch[field]
        refused(world, f"required property '{field}' is missing")
    for text in (stamp(0), stamp(-3600), "1970-01-01T00:00:00Z"):
        world.launch = dict(copy.deepcopy(good), deadline=text)
        refused(world, "deadline:", "is not in the future")
    for text in ("", "0", "-1"):
        world.launch = dict(copy.deepcopy(good), deadline=text)
        assert not world.check().ok


# ---- credentials in the supervisor's own environment → 78 ---------------------------------------------------------------
@pytest.mark.parametrize("name", ["DATABASE_URL", "KALA_DATABASE_URL", "PGPASSWORD", "ANTHROPIC_API_KEY"])
@pytest.mark.parametrize("command", ["check", "argv", "run"])
def test_a_credential_name_in_the_supervisors_own_environment_exits_78(world, name, command):
    environ = dict(world.environ, **{name: SECRET})
    cli = world.cli(command, world.launch_path, environ=environ)
    assert cli.returncode == 78
    assert name in cli.stderr and SECRET not in cli.stdout + cli.stderr
    assert not Path(world.launch["state_path"]).exists() and not world.launched()


def test_a_credential_name_set_but_empty_still_exits_78_and_other_names_do_not(world):
    assert world.cli("check", world.launch_path, environ=dict(world.environ, PGPASSWORD="")).returncode == 78
    harmless = dict(world.environ, DATABASE_URLS="x", PGPASSWORDS="x", MY_ANTHROPIC_API_KEY_NOTE="x")
    assert world.cli("check", world.launch_path, environ=harmless).returncode == 0
    assert kyboot.own_env_credentials({"A_DATABASE_URL": "1", "PGPASSWORD": "2", "HOME": "/h"}) == \
        ["A_DATABASE_URL", "PGPASSWORD"]


# --------------------------------------------------------------------------------------------------------------
# the supervisor is the reviewed source; the manifest gate (plan v2.7 pairing rule, §14 B-0c)
# --------------------------------------------------------------------------------------------------------------
def test_the_real_manifest_gate_passes_and_what_the_supervisor_verified_is_recorded(world, real_gate, staged):
    result = world.check()
    assert result.findings == []
    manifest = json.loads(world.manifest_path.read_text())
    assert result.facts["manifest_sha256"] == manifest["manifest_sha256"]
    assert result.facts["manifest_file_sha256"] == sha(world.manifest_path)
    assert result.facts["supervisor_sha256"] == sha(staged["fleet"] / "kyboot.py") == sha(FLEET / "kyboot.py")
    assert result.facts["source_repo"] == str(staged["source"])
    assert result.facts["manifest_path"] == str(world.manifest_path)          # the default: <KY_RUN>/VERSIONS…


def test_the_gate_is_asked_before_every_launch_with_the_reviewed_tool_the_source_and_the_run_folder(world, gate, staged):
    world.check()
    assert gate == [{"kymanifest": str(staged["fleet"] / "kymanifest.py"), "manifest": str(world.manifest_path),
                     "repo": str(staged["source"]), "run": str(world.run_dir)}]
    assert world.run() == 0
    assert len(gate) == 2 and gate[1] == gate[0]


@pytest.mark.parametrize("command", ["check", "argv", "run"])
def test_a_manifest_that_no_longer_matches_disk_refuses_every_command(world, command):
    world.write()
    (world.run_dir / "PROBES.json").unlink()                 # what the real kymanifest.py check re-observes
    world.auto_qualify = False
    cli = world.cli(command, world.launch_path)
    assert cli.returncode == 1 and cli.stdout == ""
    assert "manifest gate: refused: probes not recorded" in cli.stderr
    assert not world.launched() and not (world.run_dir / "jobs").exists() and not (world.run_dir / "actions").exists()


def test_a_review_receipt_that_is_not_accepted_refuses_through_the_real_gate(world, real_gate, staged):
    review = staged["review"]
    original = review.read_bytes()
    try:
        review.write_text(json.dumps(dict(json.loads(original), verdict="REJECTED")), encoding="utf-8")
        refused(world, "manifest gate: refused: review verdict is not ACCEPTED")
    finally:
        review.write_bytes(original)
    assert world.check().findings == []


def test_a_gate_that_exits_non_zero_or_does_not_confirm_the_digest_refuses(world, monkeypatch):
    monkeypatch.setattr(kyboot, "run_manifest_check", lambda *a: (1, "", "refused: component differs from HEAD: x\nmore\n"))
    refused(world, "manifest gate: refused: component differs from HEAD: x")
    monkeypatch.setattr(kyboot, "run_manifest_check", lambda *a: (3, "", ""))
    refused(world, "manifest gate: kymanifest.py check exited 3")
    world.write()
    digest = json.loads(world.manifest_path.read_text())["manifest_sha256"]
    for said in ("", "not json", json.dumps({"ok": True, "manifest_sha256": "0" * 64}), json.dumps({"ok": False}),
                 json.dumps({"ok": False, "manifest_sha256": digest}), json.dumps({"ok": "yes", "manifest_sha256": digest}),
                 json.dumps({"manifest_sha256": digest}), json.dumps([1])):
        monkeypatch.setattr(kyboot, "run_manifest_check", lambda *a, said=said: (0, said, ""))
        refused(world, "manifest gate: kymanifest.py check exited 0 without confirming this manifest's digest")


def test_the_manifest_option_names_the_manifest_and_the_default_is_the_run_folder(world):
    world.write()
    world.auto_qualify = False
    elsewhere = world.root / "VERSIONS.elsewhere.json"
    shutil.move(str(world.manifest_path), str(elsewhere))
    missing = world.cli("check", world.launch_path)
    assert missing.returncode == 1 and f"manifest: cannot read {world.manifest_path}" in missing.stderr
    named = world.cli("check", world.launch_path, "--manifest", elsewhere)
    assert named.returncode == 0, named.stderr
    assert world.cli("argv", world.launch_path, "--manifest", elsewhere).returncode == 0
    wrong = world.cli("run", world.launch_path, "--manifest", world.root / "nowhere.json")
    assert wrong.returncode == 1 and "manifest: cannot read" in wrong.stderr and not world.launched()
    assert world.cli("run", world.launch_path, "--manifest", elsewhere, "--grace", "1").returncode == 0
    assert world.state()["manifest_path"] == str(elsewhere)


@pytest.mark.parametrize("change,reason", [
    (lambda m: m.update(manifest_sha256="0" * 64), "manifest: manifest_sha256 does not match the manifest's content"),
    (lambda m: m.update(plan_version="2.6"), "manifest: manifest_sha256 does not match the manifest's content"),
    (lambda m: m["components"].append({"path": "x", "sha256": "0" * 64}), "manifest_sha256 does not match"),
])
def test_a_manifest_edited_after_it_was_digested_refuses(world, change, reason):
    world.write()
    world.auto_qualify = False
    manifest = json.loads(world.manifest_path.read_text())
    change(manifest)
    world.manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    refused(world, reason)


@pytest.mark.parametrize("change,reason", [
    (lambda m: m.update(mode="campaign"), "is not a ky.versions_bootstrap/1 manifest in mode bootstrap"),
    (lambda m: m.update(schema="ky.versions/1"), "is not a ky.versions_bootstrap/1 manifest in mode bootstrap"),
    (lambda m: m.update(approved_source_commit="HEAD"), "manifest: approved_source_commit is not a 40-hex commit id"),
    (lambda m: m.update(components="all"), "manifest: components is not a list of distinct {path, sha256} entries"),
    (lambda m: m["components"].append(dict(m["components"][0])), "manifest: components is not a list of distinct"),
    (lambda m: m["components"][0].update(sha256="abc"), "manifest: components is not a list of distinct"),
])
def test_a_well_digested_manifest_of_the_wrong_shape_refuses(world, gate, change, reason):
    world.write()
    world.auto_qualify = False
    world.sync_manifest(change)
    refused(world, reason)
    assert gate == []                                         # nothing was asked of a manifest that cannot be read


def test_a_manifest_that_is_not_json_or_repeats_a_key_refuses(world):
    world.write()
    world.auto_qualify = False
    world.manifest_path.write_text('{"schema": "ky.versions_bootstrap/1", "schema": "x"}', encoding="utf-8")
    refused(world, "manifest:", "duplicate key 'schema'")
    world.manifest_path.write_text("[]", encoding="utf-8")
    refused(world, "is not a ky.versions_bootstrap/1 manifest")


@pytest.mark.parametrize("name", ["kyboot.py", "kyschema.py", "kymanifest.py"])
def test_the_supervisor_refuses_unless_its_own_code_is_the_reviewed_bytes(world, gate, name):
    assert kyboot.SUPERVISOR_CODE == ("kyboot.py", "kyschema.py", "kymanifest.py")
    relative = f"{kymanifest.FLEET}/{name}"
    world.write()
    world.auto_qualify = False

    def other_bytes(manifest):
        entry = next(c for c in manifest["components"] if c["path"] == relative)
        entry["sha256"] = "7" * 64
    world.sync_manifest(other_bytes)
    findings = refused(world, f"supervisor: {relative} is not the reviewed file", "the manifest says " + "7" * 64)
    assert "manifest gate: kymanifest.py check was not run because the supervisor's own code is not the reviewed code" \
        in findings
    assert gate == []                                         # an unreviewed gate is never executed

    world.sync_manifest(lambda m: m["components"].remove(next(c for c in m["components"] if c["path"] == relative)))
    refused(world, f"supervisor: {relative} is not a component of the manifest")
    assert gate == []
    world.sync_manifest()
    assert world.check().findings == [] and len(gate) == 1


def test_a_supervisor_whose_code_is_not_reviewed_launches_nothing(world):
    world.write()
    world.auto_qualify = False
    world.sync_manifest(lambda m: next(c for c in m["components"]
                                       if c["path"].endswith("/kyboot.py")).update(sha256="7" * 64))
    assert world.run() == 1
    assert not world.launched() and not (world.run_dir / "jobs").exists() and not (world.run_dir / "locks").exists()


def test_the_supervisor_never_runs_from_the_installed_fleet(world, staged):
    assert kyboot.INSTALLED_FLEET == "/Users/Dev/kalayantra/fleet_live"
    assert kyboot.installed_fleet_root("/Users/Dev/kalayantra/fleet_live/kyboot.py", {}) == kyboot.INSTALLED_FLEET
    assert kyboot.installed_fleet_root("/Users/Dev/kalayantra/fleet_live", {}) == kyboot.INSTALLED_FLEET
    assert kyboot.installed_fleet_root("/Users/Dev/kalayantra/fleet_live_other/kyboot.py", {}) is None
    assert kyboot.installed_fleet_root(kyboot.__file__, {}) is None
    assert kyboot.installed_fleet_root(kyboot.__file__, {"KY_FLEET": "relative"}) is None
    assert kyboot.installed_fleet_root(kyboot.__file__, {"KY_FLEET": str(staged["fleet"])}) == str(staged["fleet"])
    world.environ["KY_FLEET"] = str(staged["fleet"])          # "the installed fleet is where I am running from"
    refused(world, f"supervisor: {staged['fleet'] / 'kyboot.py'} runs from the installed fleet {staged['fleet']}")
    assert world.run() == 1 and not world.launched() and not (world.run_dir / "jobs").exists()
    world.environ["KY_FLEET"] = str(world.ky_root / "fleet_live")
    assert world.check().findings == []


def test_a_supervisor_outside_any_repository_refuses(world, staged):
    loose = world.root / "loose"
    loose.mkdir()
    (loose / ".git").write_text("gitdir: /nonexistent/kyboot-test\n", encoding="utf-8")
    for name in ("kyboot.py", "kyschema.py", "kymanifest.py"):
        shutil.copyfile(staged["fleet"] / name, loose / name)
    shutil.copytree(staged["fleet"] / "schemas", loose / "schemas")
    spec = importlib.util.spec_from_file_location("kyboot_loose", loose / "kyboot.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.check(str(world.write()), world.environ)
    assert any(f"supervisor: {loose / 'kyboot.py'} is not inside a git work tree" in line for line in result.findings)


def test_the_launch_input_must_name_the_commit_and_plan_version_the_manifest_authorises(world):
    world.launch["approved_source_commit"] = world.head       # a real commit of the repository, but not the approved one
    refused(world, f"approved_source_commit: the launch input says {world.head}, the manifest authorises "
                   f"{world.staged['approved']}")
    world.launch["approved_source_commit"] = world.staged["approved"]
    world.write()
    world.auto_qualify = False
    world.sync_manifest(lambda m: m.update(plan_version="2.6"))
    refused(world, "manifest: its plan_version '2.6' is not the launch input's '2.7'")


@pytest.mark.parametrize("path_field,hash_field", [("card_path", "card_sha256"), ("mcp_config", "mcp_config_sha256")])
def test_the_card_and_the_mcp_configuration_must_be_manifest_components(world, staged, path_field, hash_field):
    assert kyboot.MANIFEST_BOUND_FILES == (("card_path", "card_sha256"), ("mcp_config", "mcp_config_sha256"))
    relative = os.path.relpath(world.launch[path_field], world.repo)
    in_source = staged["source"] / relative
    assert world.check().findings == []                       # the worktree's copy at the component's path
    world.launch[path_field] = str(in_source)                 # the reviewed source's own file
    assert world.check().findings == []
    world.launch[path_field] = str(world.repo / relative)

    stray = world.root / "stray" / os.path.basename(relative)             # the right bytes in the wrong place
    stray.parent.mkdir()
    shutil.copyfile(in_source, stray)
    world.launch[path_field] = str(stray)
    refused(world, f"{path_field}: {stray} is not a component of the manifest")

    world.auto_qualify = False                                             # even a manifest that lists a path
    world.sync_manifest(lambda m: m["components"].append(                  # climbing out of the roots binds nothing
        {"path": os.path.relpath(stray, world.repo), "sha256": sha(stray)}))
    refused(world, f"{path_field}: {stray} is not a component of the manifest")
    world.auto_qualify = True

    unlisted = world.repo / "README.unlisted"                              # in the worktree, but not a component
    shutil.copyfile(in_source, unlisted)
    world.launch[path_field] = str(unlisted)
    refused(world, f"{path_field}: {unlisted} is not a component of the manifest")

    world.launch[path_field] = str(world.repo / relative)                  # the right place with other bytes
    with open(world.launch[path_field], "ab") as handle:
        handle.write(b" \n")
    world.launch[hash_field] = sha(world.launch[path_field])
    findings = refused(world, f"{path_field}: {hash_field} {world.launch[hash_field]} is not the reviewed",
                       f"of manifest component {relative}")
    assert not any(f"{path_field}: sha256 mismatch" in line for line in findings)


def test_the_packet_and_the_prompt_are_per_job_and_are_not_manifest_components(world, staged):
    for field in ("packet_path", "prompt_path"):
        assert not any(c.endswith(os.path.basename(world.launch[field])) for c in staged["components"])
    assert world.check().findings == []


# --------------------------------------------------------------------------------------------------------------
# the qualification gate (plan §7 KV-06)
# --------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("role", ROLES)
@pytest.mark.parametrize("model", ["claude-opus-5-5", "claude-sonnet-5-5"])
def test_each_role_and_model_is_launchable_only_with_its_own_receipt(world, role, model):
    world.launch.update(role=role, model=model)
    assert world.check().findings == []
    assert world.receipt_path().name == f"{role}-{model}.json"
    world.auto_qualify = False
    world.receipt_path().unlink()
    world.sync_manifest()
    refused(world, f"qualification: no receipt at {world.run_dir}/QUALIFICATIONS/{role}-{model}.json")


def test_a_receipt_of_another_role_or_model_does_not_qualify_this_one(world):
    world.write()
    world.auto_qualify = False
    world.launch["role"] = "bootstrap-reviewer"
    refused(world, "qualification: no receipt at", "bootstrap-reviewer-claude-opus-5-5.json")
    shutil.copyfile(world.run_dir / "QUALIFICATIONS" / "bootstrap-builder-claude-opus-5-5.json", world.receipt_path())
    world.sync_manifest()
    refused(world, "qualification: the receipt's role \"bootstrap-builder\" is not the launch input's 'bootstrap-reviewer'")
    world.launch.update(role="bootstrap-builder", model="claude-sonnet-5-5")
    shutil.copyfile(world.run_dir / "QUALIFICATIONS" / "bootstrap-builder-claude-opus-5-5.json", world.receipt_path())
    world.sync_manifest()
    refused(world, "qualification: the receipt's model \"claude-opus-5-5\" is not the launch input's 'claude-sonnet-5-5'")


@pytest.mark.parametrize("result", ["FAIL", "unknown", "pass", "PASS ", "", None, True, 1, ["PASS"]])
def test_only_a_result_of_exactly_pass_qualifies(world, result):
    world.write()
    world.auto_qualify = False
    world.qualify(lambda r: r.update(result=result))
    findings = refused(world, "qualification: result is", "only \"PASS\" qualifies a launch")
    assert any("the manifest records as PASS" in line for line in findings)       # and the manifest says so too
    world.qualify(lambda r: r.pop("result"))
    refused(world, "qualification: result is null", "only \"PASS\" qualifies a launch")


def test_a_failed_qualification_launches_nothing(world):
    world.write()
    world.auto_qualify = False
    world.qualify(lambda r: r.update(result="FAIL"))
    for command in ("check", "argv", "run"):
        cli = world.cli(command, world.launch_path)
        assert cli.returncode == 1 and cli.stdout == "" and "only \"PASS\" qualifies" in cli.stderr
    assert not world.launched() and not (world.run_dir / "jobs").exists() and not (world.run_dir / "actions").exists()


def test_a_receipt_the_manifest_does_not_record_or_records_differently_refuses(world):
    world.write()
    world.auto_qualify = False
    world.qualify(lambda r: r.update(context="launchd"), sync=False)              # other bytes than recorded
    refused(world, "qualification: the receipt is not the one the manifest records as PASS")
    world.qualify()
    world.sync_manifest(lambda m: m.update(qualifications=[]))
    refused(world, "qualification: the receipt is not recorded in the manifest")
    world.sync_manifest(lambda m: m["qualifications"][0].update(result="unknown"))
    refused(world, "qualification: the receipt is not the one the manifest records as PASS")
    world.sync_manifest()
    assert world.check().findings == []


@pytest.mark.parametrize("change,reason", [
    (lambda r: r.update(schema="ky.qualification/2"), "is not a ky.qualification/1 receipt"),
    (lambda r: r.pop("schema"), "is not a ky.qualification/1 receipt"),
    (lambda r: r.pop("binds"), "qualification: the receipt carries no binds"),
    (lambda r: r.update(binds=[]), "qualification: the receipt carries no binds"),
])
def test_a_receipt_of_the_wrong_shape_refuses(world, change, reason):
    world.write()
    world.auto_qualify = False
    world.qualify(change)
    refused(world, reason)
    for document in ("not a receipt", ["PASS"], 7):
        world.qualify(replace=document)
        refused(world, "is not a ky.qualification/1 receipt")


def test_a_receipt_that_is_not_json_refuses(world):
    world.write()
    world.auto_qualify = False
    world.receipt_path().write_text('{"result": "PASS", "result": "FAIL"}', encoding="utf-8")
    world.sync_manifest()
    refused(world, "qualification:", "duplicate key 'result'")


BIND_CHANGES = [
    ("claude_bin", "/usr/local/bin/claude"),
    ("claude_bin_sha256", "9" * 64),
    ("claude_version", "2.1.297 (Claude Code)"),
    ("claude_version", "not a version"),
    ("claude_version", 2),
    ("model", "claude-sonnet-5-5"),
    ("effort", "xhigh"),
    ("permission_mode", "acceptEdits"),
    ("max_turns", 149),
    ("max_turns", "150"),
    ("max_turns", 150.0),
    ("max_turns", True),
    ("mcp_config_sha256", "9" * 64),
    ("env_names", ["HOME", "PATH"]),
    ("env_names", "HOME"),
]


@pytest.mark.parametrize("name,value", BIND_CHANGES, ids=[f"{n}={i}" for i, (n, _) in enumerate(BIND_CHANGES)])
def test_every_bound_fact_must_bind_this_launch(world, name, value):
    assert world.check().findings == []
    world.auto_qualify = False
    world.qualify(lambda r: r["binds"].update({name: value}))
    findings = refused(world, f"qualification: binds.{name}", "does not bind this launch")
    assert len([line for line in findings if line.startswith("qualification:")]) == 1
    world.qualify(lambda r: r["binds"].pop(name))
    refused(world, f"qualification: binds.{name} is missing")


def test_the_bound_facts_are_the_ones_named_for_the_gate():
    names = {name for name, _ in BIND_CHANGES}
    assert names == {"claude_bin", "claude_bin_sha256", "claude_version", "model", "effort", "permission_mode",
                     "max_turns", "mcp_config_sha256", "env_names"}


def test_the_bound_version_is_compared_as_a_version_and_the_program_hash_is_of_the_resolved_file(world):
    world.write()
    world.auto_qualify = False
    world.qualify(lambda r: r["binds"].update(claude_version="2.1.296"))      # the same version, written bare
    assert world.check().findings == []
    link = world.root / "bin" / "claude-link"
    os.symlink(str(world.claude), str(link))
    world.launch["claude_bin"] = str(link)
    world.auto_qualify = True
    result = world.check()
    assert result.findings == [] and result.facts["claude_bin_sha256"] == sha(world.claude)
    assert result.facts["claude_bin_realpath"] == str(world.claude)


def test_the_environment_names_must_equal_the_sorted_names_of_the_job_environment(world):
    world.write()
    world.auto_qualify = False
    names = sorted(world.launch["env"])
    world.qualify(lambda r: r["binds"].update(env_names=list(reversed(names))))
    refused(world, "qualification: binds.env_names", "does not bind this launch")
    world.qualify(lambda r: r["binds"].update(env_names=names + ["ZDOTDIR"]))
    refused(world, "qualification: binds.env_names", "does not bind this launch")
    world.qualify()
    world.launch["env"]["LANG"] = "C"                                           # a value may differ; a name may not
    assert world.check().findings == []
    world.launch["env"]["KY_LANE"] = "b1"
    refused(world, "qualification: binds.env_names", "does not bind this launch")


def test_the_worktree_is_not_compared_and_the_launch_line_is_compared_without_it(world):
    other = "/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-probe"

    def probed_elsewhere(receipt):
        binds = receipt["binds"]
        binds["argv"] = [element.replace(binds["worktree"], other) for element in binds["argv"]]
        binds["worktree"] = other
    world.write()
    world.auto_qualify = False
    world.qualify(probed_elsewhere)
    receipt = json.loads(world.receipt_path().read_text())
    assert receipt["binds"]["worktree"] == other and any(a.startswith(other) for a in receipt["binds"]["argv"])
    assert world.check().findings == []

    def other_mcp_file(receipt):                             # the MCP path is bound by its hash, not by its place
        argv = receipt["binds"]["argv"]
        argv[argv.index("--mcp-config") + 1] = "/somewhere/else/mcp.none.json"
    world.qualify(other_mcp_file)
    assert world.check().findings == []


ARGV_CHANGES = [
    ("an extra flag", lambda a: a.insert(a.index("--strict-mcp-config"), "--no-chrome")),
    ("a missing flag", lambda a: a.remove("--disable-slash-commands")),
    ("another order", lambda a: a.append(a.pop(a.index("--verbose")))),
    ("another added directory", lambda a: a.__setitem__(len(a) - 1, "/")),
    ("another program", lambda a: a.__setitem__(0, "/usr/local/bin/claude")),
    ("another turn limit", lambda a: a.__setitem__(a.index("--max-turns") + 1, "151")),
    ("another permission mode", lambda a: a.__setitem__(a.index("--permission-mode") + 1, "plan")),
    ("no strict MCP", lambda a: a.remove("--strict-mcp-config")),
    ("a bare job", lambda a: a.insert(2, "--bare")),
    ("a second added directory", lambda a: a.extend(["--add-dir", "/Users"])),
    ("denied tools", lambda a: a.insert(a.index("--output-format"), "--disallowedTools") or
     a.insert(a.index("--output-format"), "WebFetch")),
    ("truncated", lambda a: a.pop()),
]


@pytest.mark.parametrize("what,change", ARGV_CHANGES, ids=[c[0] for c in ARGV_CHANGES])
def test_a_receipt_whose_launch_line_differs_in_any_flag_or_order_refuses(world, what, change):
    world.write()
    world.auto_qualify = False
    world.qualify(lambda r: change(r["binds"]["argv"]))
    findings = refused(world, "qualification: binds.argv is not this launch's line (same flags, same order)")
    assert len([line for line in findings if line.startswith("qualification:")]) == 1


def test_a_receipt_without_a_launch_line_refuses(world):
    world.write()
    world.auto_qualify = False
    world.qualify(lambda r: r["binds"].pop("argv"))
    refused(world, "qualification: binds.argv is missing")
    world.qualify(lambda r: r["binds"].update(argv="claude -p"))
    refused(world, "qualification: binds.argv is not a list of strings")
    world.qualify(lambda r: r["binds"].update(argv=["claude", 7]))
    refused(world, "qualification: binds.argv is not a list of strings")


def test_portable_argv():
    wt = "/w/item"
    line = ["/bin/claude", "-p", "--mcp-config", "/w/item/fleet/mcp.none.json", "--add-dir", "/w/item", "--add-dir",
            "/w/item-other", "--x=/w/item/y"]
    assert kyboot.portable_argv(line, wt) == ["/bin/claude", "-p", "--mcp-config", "<MCP_CONFIG>", "--add-dir",
                                              "<WORKTREE>", "--add-dir", "/w/item-other", "--x=/w/item/y"]
    assert kyboot.portable_argv(["a", "--mcp-config", "m"], None) == ["a", "--mcp-config", "<MCP_CONFIG>"]
    assert kyboot.portable_argv(["/w/item/bin/claude"], wt) == ["<WORKTREE>/bin/claude"]
    assert kyboot.portable_argv([], wt) == []


def test_a_launch_changed_after_it_was_qualified_refuses(world):
    assert world.check().findings == []
    world.auto_qualify = False
    world.launch["extra_lean_flags"] = []
    refused(world, "qualification: binds.argv is not this launch's line")
    world.launch["extra_lean_flags"] = ["--disable-slash-commands"]
    world.launch["permission_mode"] = "plan"
    refused(world, "qualification: binds.permission_mode \"bypassPermissions\" does not bind this launch (\"plan\")")
    world.launch["permission_mode"] = "bypassPermissions"
    world.launch["disallowed_tools"] = ["WebFetch"]
    refused(world, "qualification: binds.argv is not this launch's line")
    world.launch["disallowed_tools"] = []
    world.launch["max_turns"] = 100
    refused(world, "qualification: binds.max_turns 150 does not bind this launch (100)")
    world.launch["max_turns"] = 150
    world.install("fake_claude_stubborn.sh")                 # another program file at another path, same version
    findings = refused(world, "qualification: binds.claude_bin_sha256", "does not bind this launch")
    assert any("qualification: binds.claude_bin " in line for line in findings)


# --------------------------------------------------------------------------------------------------------------
# argv
# --------------------------------------------------------------------------------------------------------------
def test_argv_is_the_plan_launch_line_with_a_clean_environment_and_is_deterministic(world):
    first = world.cli("argv", world.launch_path)
    second = world.cli("argv", world.launch_path)
    assert first.returncode == 0, first.stderr
    assert first.stdout == second.stdout
    out = json.loads(first.stdout)
    assert sorted(out) == ["argv", "cwd", "env"]
    assert out["cwd"] == str(world.repo)
    assert out["argv"] == launch_line(world.launch) == [
        str(world.claude), "-p", "--setting-sources", "project", "--permission-mode", "bypassPermissions",
        "--model", "claude-opus-5-5", "--effort", "high", "--max-turns", "150", "--disable-slash-commands",
        "--strict-mcp-config", "--mcp-config", str(world.mcp),
        "--output-format", "stream-json", "--verbose", "--add-dir", str(world.ky_root)]
    assert out["env"] == world.launch["env"] and out["env"]["TMPDIR"] == world.launch["tmp_path"]
    assert "KY_TEST_MARKER" not in out["env"] and "KY_SCRATCH" not in out["env"]


def test_argv_carries_disallowed_tools_and_extra_flags_in_the_qualified_order(world):
    world.launch["disallowed_tools"] = ["Bash(git push:*)", "WebFetch"]
    world.launch["extra_lean_flags"] = ["--disable-slash-commands", "--no-chrome"]
    world.launch.update(kind="PLAN", role="planner", effort="xhigh", max_turns=300, permission_mode="plan")
    out = json.loads(world.cli("argv", world.launch_path).stdout)
    argv = out["argv"]
    assert argv == launch_line(world.launch) == json.loads(world.receipt_path().read_text())["binds"]["argv"]
    at = argv.index("--disallowedTools")
    assert argv[at:at + 4] == ["--disallowedTools", "Bash(git push:*)", "WebFetch", "--output-format"]
    assert argv[at - 3:at] == ["--strict-mcp-config", "--mcp-config", str(world.mcp)]
    assert argv[10:14] == ["--max-turns", "300", "--disable-slash-commands", "--no-chrome"]
    assert argv[argv.index("--effort") + 1] == "xhigh" and argv[argv.index("--permission-mode") + 1] == "plan"
    assert argv[-5:] == ["--output-format", "stream-json", "--verbose", "--add-dir", str(world.ky_root)]


def test_argv_refuses_what_check_refuses(world):
    world.launch["extra_lean_flags"].append("--bare")
    cli = world.cli("argv", world.launch_path)
    assert cli.returncode == 1 and cli.stdout == "" and "--bare is forbidden" in cli.stderr


def test_the_launch_line_never_contains_a_forbidden_flag(world):
    argv = kyboot.build_launch(world.launch)["argv"]
    assert not set(argv) & {"--bare", "--dangerously-skip-permissions", "--settings"}
    assert argv.count("--mcp-config") == 1 and argv.count("--setting-sources") == 1
    assert argv[argv.index("--setting-sources") + 1] == "project"


# --------------------------------------------------------------------------------------------------------------
# run
# --------------------------------------------------------------------------------------------------------------
def test_run_launches_the_checked_line_in_a_new_session_and_records_the_job(world, staged):
    launch_sha = sha(world.write())
    cli = world.cli("run", world.launch_path)
    assert cli.returncode == 0, cli.stderr
    state = world.state()
    assert json.loads(cli.stdout) == state
    tmp = world.job_scratch / "tmp"
    # the job received exactly the checked launch line, environment, working directory and prompt
    assert (tmp / "fake_argv.txt").read_text().splitlines() == launch_line(world.launch)[1:] == state["argv"][1:]
    names = {line.split("=", 1)[0] for line in (tmp / "fake_env.txt").read_text().splitlines()}
    assert names - {"PWD", "OLDPWD", "SHLVL", "_"} == set(world.launch["env"])
    assert f"TMPDIR={tmp}" in (tmp / "fake_env.txt").read_text().splitlines()
    assert "KY_TEST_MARKER" not in names and "KY_SCRATCH" not in names
    assert (tmp / "fake_cwd.txt").read_text().strip() == str(world.repo)
    assert (tmp / "fake_stdin.txt").read_text() == world.prompt.read_text()
    # its own process group and session, recorded as observed
    assert state["pid"] == state["pgid"] == int((tmp / "fake_pgid.txt").read_text())
    assert state["pgid"] != os.getpgid(0)
    assert state["process_start"] and state["supervisor_pid"] != state["pid"]
    # identity and outcome
    for key in ("job_id", "item", "kind", "role", "worktree", "branch", "base_sha", "model", "effort"):
        assert state[key] == world.launch[key], key
    for key in ("prompt_path", "stdout_path", "stderr_path", "tmp_path"):
        assert state[key] == world.launch[key] and os.path.isabs(state[key]), key
    assert state["launch_input_sha256"] == launch_sha
    assert state["worktree_head"] == world.head and state["claude_version"] == "2.1.296 (Claude Code)"
    assert state["scratch_root_override"] is True and state["scratch_root"] == str(world.root)
    assert state["phase"] == "ended" and state["termination"] == "exited"
    assert state["exit_code"] == 0 and state["exit_signal"] is None
    assert state["leftover_group"] == "none" and state["group_gone"] is True
    assert kyboot.parse_utc(state["started_at"]) <= kyboot.parse_utc(state["ended_at"])
    assert state["provider_session_id"] == SESSION
    assert state["result_event"] == {"subtype": "success", "is_error": False, "num_turns": 3,
                                     "usage": {"input_tokens": 31000, "output_tokens": 120}}
    assert state["job_result_valid"] is None and state["job_result_errors"] == []
    assert SESSION in Path(world.launch["stdout_path"]).read_text()
    assert Path(world.launch["stderr_path"]).read_text() == "fake stderr line\n"
    assert sorted(p.name for p in Path(world.launch["state_path"]).parent.iterdir()) == ["state.json"]
    # what the supervisor verified about itself and its authority (plan v2.7)
    assert state["supervisor_sha256"] == sha(staged["fleet"] / "kyboot.py") == sha(FLEET / "kyboot.py")
    assert state["supervisor_path"] == str(staged["fleet"] / "kyboot.py") and state["source_repo"] == str(staged["source"])
    assert state["manifest_sha256"] == json.loads(world.manifest_path.read_text())["manifest_sha256"]
    assert state["manifest_file_sha256"] == sha(world.manifest_path) and state["manifest_path"] == str(world.manifest_path)
    assert state["qualification_path"] == str(world.receipt_path())
    assert state["qualification_sha256"] == sha(world.receipt_path())
    assert state["claude_bin_sha256"] == sha(world.claude)
    assert state["lock_path"] == str(world.lock()) and state["lock_taken_over_from"] is None
    assert state["launch_context"] == "shell" and state["launch_context_parent_pid_injected"] is False
    assert state["label"] is None and time.strptime(state["supervisor_process_start"], kyboot.LSTART_FMT)
    assert world.calls() == []                                # a shell run never talks to launchd
    assert state["action_path"] == str(world.run_dir / "actions" / f"ACT-launch-{JOB}.json")


def test_run_refuses_a_second_run_of_the_same_job(world, capsys):
    assert world.run() == 0
    before = Path(world.launch["state_path"]).read_bytes()
    action_before = (world.run_dir / "actions" / f"ACT-launch-{JOB}.json").read_bytes()
    (world.job_scratch / "tmp" / "fake_argv.txt").unlink()
    capsys.readouterr()
    assert world.run() == 1
    said = capsys.readouterr().err
    assert "already exists for job " + JOB in said and "no silent re-run" in said and "never repeat it" in said
    assert Path(world.launch["state_path"]).read_bytes() == before and not world.launched()
    assert (world.run_dir / "actions" / f"ACT-launch-{JOB}.json").read_bytes() == action_before


def test_run_refuses_when_a_state_file_already_exists_and_leaves_it_untouched(world, capsys):
    state_path = Path(world.launch["state_path"])
    state_path.parent.mkdir(parents=True)
    state_path.write_text('{"phase": "running", "pid": 1}\n', encoding="utf-8")
    assert world.run() == 1
    said = capsys.readouterr().err
    assert "state_path:" in said and "already exists" in said
    assert state_path.read_text(encoding="utf-8") == '{"phase": "running", "pid": 1}\n'
    assert not world.launched() and not Path(world.launch["stdout_path"]).exists()
    assert not (world.run_dir / "actions").exists() and not world.lock().exists()


def test_a_state_file_that_appears_after_the_existence_check_is_still_never_overwritten(world, monkeypatch):
    """two supervisors racing for one job id: the creation itself is exclusive, not only the look before it"""
    state_path = Path(world.launch["state_path"])
    original = kyboot.sha256_file

    def other_supervisor_wins(path):
        if str(path) == str(world.launch_path):          # run() hashes the launch input after its existence check
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text('{"owner": "the other supervisor"}\n', encoding="utf-8")
        return original(path)

    monkeypatch.setattr(kyboot, "sha256_file", other_supervisor_wins)
    assert world.run() == 1
    assert state_path.read_text(encoding="utf-8") == '{"owner": "the other supervisor"}\n'
    assert not world.launched() and not Path(world.launch["stdout_path"]).exists()
    assert sorted(p.name for p in state_path.parent.iterdir()) == ["state.json"]
    action = world.action()
    assert action["state"] == "FAILED" and action["result"]["reason"] == "state.json already exists"
    assert not world.lock().exists()


@pytest.mark.parametrize("which", ["stdout_path", "stderr_path", "result.json"])
def test_run_refuses_to_overwrite_an_earlier_output(world, which, capsys):
    target = world.job_scratch / "result.json" if which == "result.json" else Path(world.launch[which])
    target.write_text("earlier\n", encoding="utf-8")
    assert world.run() == 1
    said = capsys.readouterr().err
    assert f"{which}:" in said and "already exists" in said
    assert target.read_text(encoding="utf-8") == "earlier\n"
    assert not Path(world.launch["state_path"]).exists() and not world.launched()


def test_run_refuses_what_check_refuses_and_launches_nothing(world, capsys):
    world.launch["max_turns"] = 151
    assert world.run() == 1 and "max_turns: 151 exceeds the cap 150" in capsys.readouterr().err
    assert not Path(world.launch["state_path"]).exists() and not world.launched()
    assert not (world.run_dir / "actions").exists() and not (world.run_dir / "locks").exists()


def result_line(**changes) -> str:
    result = {"schema": "ky.job_result/1", "job_id": JOB, "item": ITEM, "status": "done",
              "branch": BRANCH, "head_sha": "a" * 40, "pr_number": None,
              "tests": [{"cmd": "pytest", "exit": 0, "summary": "ok"}], "blocked_reason": None, "notes": ""}
    result.update(changes)
    return "FAKE_RESULT_JSON:" + json.dumps(result) + "\n"


@pytest.mark.parametrize("line", [result_line(), result_line(head_sha=None, branch=None),
                                  result_line(pr_number=7), result_line(head_sha=None, proposed_verdict={"verdict": "ACCEPTED"})])
def test_a_valid_job_result_is_recorded_as_valid(world, line):
    world.set_prompt("do the work\n" + line)
    assert world.run() == 0
    state = world.state()
    assert state["job_result_valid"] is True and state["job_result_errors"] == []


@pytest.mark.parametrize("line,reason", [
    (result_line(pr_number=7, head_sha=None), "$.head_sha: expected type string"),
    (result_line(status="blocked", blocked_reason=None), "$.blocked_reason: expected type string"),
    (result_line(job_id="J-SOMEONE-ELSE"), "is not this job's job_id"),
    (result_line(item="KV3-B-OTHER"), "is not this job's item"),
    ("FAKE_RESULT_JSON:{not json\n", "is not acceptable JSON"),
    ('FAKE_RESULT_JSON:{"schema":"ky.job_result/1","schema":"ky.job_result/1"}\n', "duplicate key 'schema'"),
])
def test_an_invalid_job_result_is_recorded_as_invalid_and_run_does_not_exit_0(world, line, reason):
    world.set_prompt(line)
    code = world.run()
    state = world.state()
    assert state["exit_code"] == 0 and state["termination"] == "exited"
    assert state["job_result_valid"] is False
    assert any(reason in error for error in state["job_result_errors"]), state["job_result_errors"]
    assert code == 3


def test_a_job_that_exits_non_zero_is_recorded_and_run_exits_3(world):
    world.set_prompt("FAKE_EXIT:7\n")
    code = world.run()
    state = world.state()
    assert code == 3
    assert state["exit_code"] == 7 and state["termination"] == "exited" and state["group_gone"] is True
    action = world.action()
    assert action["state"] == "DONE" and action["result"]["exit_code"] == 7 and action["result"]["supervisor_exit"] == 3


def test_the_provider_session_id_is_never_invented(world):
    world.set_prompt("FAKE_NO_SESSION\n")
    assert world.run() == 0
    state = world.state()
    assert state["provider_session_id"] is None
    assert state["result_event"]["subtype"] == "success"


def test_a_stream_without_a_result_event_records_none(world):
    world.set_prompt("FAKE_NO_RESULT_EVENT\n")
    assert world.run() == 0
    state = world.state()
    assert state["result_event"] is None and state["provider_session_id"] == SESSION


def test_stream_readers(tmp_path):
    stream = tmp_path / "s.jsonl"
    stream.write_text("\n".join([
        "not json", "[1, 2]", '"session_id"', '{"type":"system","session_id":7}', '{"type":"system","session_id":""}',
        '{"type":"system","subtype":"init","session_id":"first"}', '{"type":"assistant","session_id":"second"}',
        '{"type":"result","subtype":"error_max_turns","is_error":true,"num_turns":150}',
        '{"type":"result","subtype":"success","is_error":false,"num_turns":4,"usage":{"input_tokens":1}}', ""]),
        encoding="utf-8")
    assert kyboot.first_session_id(str(stream)) == "first"
    assert kyboot.final_result_event(str(stream)) == {"subtype": "success", "is_error": False, "num_turns": 4,
                                                      "usage": {"input_tokens": 1}}
    only = tmp_path / "one.jsonl"
    only.write_text('{"type":"result","subtype":"error_during_execution"}\n', encoding="utf-8")
    assert kyboot.final_result_event(str(only)) == {"subtype": "error_during_execution", "is_error": None,
                                                    "num_turns": None, "usage": None}
    assert kyboot.first_session_id(str(only)) is None
    assert kyboot.first_session_id(str(tmp_path / "absent")) is None
    assert kyboot.final_result_event(str(tmp_path / "absent")) is None
    cut = tmp_path / "cut.jsonl"
    cut.write_text('{"type":"system"}\n{"session_id":"would-be-cut-in-the-middle"}\n', encoding="utf-8")
    assert kyboot.first_session_id(str(cut), limit=30) is None           # a cut line is not an object: skipped
    assert kyboot.first_session_id(str(cut), limit=len(cut.read_bytes()) - 1) == "would-be-cut-in-the-middle"
    assert kyboot.first_session_id(str(cut), limit=4096) == "would-be-cut-in-the-middle"


def test_the_deadline_ends_a_job_that_obeys_sigterm(world):
    world.set_prompt("FAKE_SLEEP:60\n")
    world.launch["deadline"] = stamp(4)
    started = time.monotonic()
    cli = world.cli("run", world.launch_path, "--grace", "10")
    elapsed = time.monotonic() - started
    state = world.state()
    assert cli.returncode == 124, cli.stderr
    assert state["termination"] == "timed_out_term" and state["group_gone"] is True
    assert state["exit_code"] is None and state["exit_signal"] == signal.SIGTERM
    assert state["provider_session_id"] == SESSION and state["result_event"] is None
    assert 2.5 < elapsed < 12.0                        # it waited for the deadline, and not for the whole grace
    assert gone(state["pid"])
    action = world.action()
    assert action["state"] == "DONE" and action["result"]["termination"] == "timed_out_term"
    assert action["result"]["supervisor_exit"] == 124 and not world.lock().exists()


def test_the_deadline_kills_a_job_that_ignores_sigterm_and_the_whole_group_is_gone(world):
    world.install("fake_claude_stubborn.sh")
    world.launch["deadline"] = stamp(4)
    started = time.monotonic()
    cli = world.cli("run", world.launch_path, "--grace", "1")
    elapsed = time.monotonic() - started
    state = world.state()
    assert cli.returncode == 124, cli.stderr
    assert state["termination"] == "timed_out_kill" and state["group_gone"] is True
    assert state["exit_signal"] == signal.SIGKILL and state["exit_code"] is None
    assert state["provider_session_id"] == "5e55105e-0000-4000-8000-0000000000aa"
    assert state["grace_seconds"] == 1.0 and elapsed >= 4.0      # deadline, then the grace, then SIGKILL
    tmp = world.job_scratch / "tmp"
    leader, child = int((tmp / "fake_pid.txt").read_text()), int((tmp / "fake_child_pid.txt").read_text())
    assert leader == state["pid"] and child != leader
    assert gone(leader) and gone(child)
    with pytest.raises(ProcessLookupError):
        os.killpg(state["pgid"], 0)
    assert world.action()["result"]["termination"] == "timed_out_kill" and not world.lock().exists()


def test_members_a_job_leaves_behind_in_its_group_are_ended_and_reported(world):
    world.set_prompt("FAKE_LEFTOVER:60\n")
    code = world.run(grace=5)
    state = world.state()
    assert code == 0
    assert state["termination"] == "exited" and state["exit_code"] == 0
    assert state["leftover_group"] == "terminated" and state["group_gone"] is True
    assert gone(int((world.job_scratch / "tmp" / "fake_leftover_pid.txt").read_text()))


def wait_until_running(world, job=JOB, limit=20.0):
    end = time.monotonic() + limit
    state_path = world.run_dir / "jobs" / job / "state.json"
    while time.monotonic() < end:
        try:
            state = json.loads(state_path.read_text())
            owner = json.loads((world.lock(state["item"]) / "owner.json").read_text())
            if state["phase"] == "running" and state["process_start"] and owner.get("child"):
                return state, owner
        except (OSError, ValueError, KeyError):
            pass
        time.sleep(0.05)
    raise AssertionError("the job did not reach the running phase")


def start_supervisor(world, launch_path, *options):
    return subprocess.Popen([sys.executable, str(world.kyboot_path), "run", str(launch_path), *options],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=world.environ)


def test_a_signal_to_the_supervisor_ends_the_job_and_is_recorded(world):
    world.set_prompt("FAKE_SLEEP:60\n")
    world.write()
    proc = start_supervisor(world, world.launch_path, "--grace", "5")
    try:
        wait_until_running(world)
        proc.send_signal(signal.SIGTERM)
        proc.communicate(timeout=30)
    finally:
        if proc.poll() is None:
            proc.kill()
    state = world.state()
    assert proc.returncode == 130
    assert state["termination"] == "interrupted_term" and state["supervisor_signal"] == signal.SIGTERM
    assert state["group_gone"] is True and gone(state["pid"])
    assert world.action()["state"] == "DONE" and not world.lock().exists()


def test_a_supervisor_error_still_ends_the_job_and_is_recorded(world, monkeypatch):
    world.set_prompt("FAKE_SLEEP:60\n")

    def broken(path, limit=None):
        if limit is not None:
            raise RuntimeError("scan failed")
        return None

    monkeypatch.setattr(kyboot, "first_session_id", broken)
    code = world.run(grace=5)
    state = world.state()
    assert code == 130
    assert state["termination"] == "interrupted_term" and state["supervisor_error"] == "RuntimeError: scan failed"
    assert state["group_gone"] is True and gone(state["pid"])


def test_a_group_that_cannot_be_confirmed_gone_is_reported_not_assumed_and_keeps_its_item_locked(world, monkeypatch):
    monkeypatch.setattr(kyboot, "group_state", lambda pgid: "unreaped")
    monkeypatch.setattr(kyboot, "KILL_CONFIRM_SECONDS", 0.2)
    code = world.run(grace=0.2)
    state = world.state()
    assert code == 5
    assert state["group_gone"] is False and state["termination"] == "exited" and state["exit_code"] == 0
    action = world.action()
    assert action["state"] == "FAILED" and action["result"]["group_gone"] is False
    owner = json.loads((world.lock() / "owner.json").read_text())          # the lock stays, naming the job
    assert owner["child"]["pid"] == state["pid"] and owner["child"]["job_id"] == JOB


def test_a_job_that_does_not_lead_its_own_process_group_is_killed_by_pid_and_no_group_is_signalled(world, monkeypatch):
    """if the new session did not take effect the 'job group' would be the supervisor's own: never signal it"""
    world.set_prompt("FAKE_SLEEP:60\n")
    signalled = []
    monkeypatch.setattr(kyboot.os, "getpgid", lambda pid: os.getpgrp())
    monkeypatch.setattr(kyboot.os, "killpg", lambda pgid, signum: signalled.append((pgid, signum)))
    code = world.run()
    state = world.state()
    assert code == 3 and signalled == []
    assert state["phase"] == "launch_failed" and "not the leader of its own process group" in state["launch_error"]
    assert state["pgid"] == os.getpgrp() and gone(state["pid"])
    assert world.action()["state"] == "FAILED" and not world.lock().exists()


def after_check(monkeypatch, act):
    """run `act` once, between the passed check and the launch (the item lock is the first thing run() takes)"""
    original = kyboot.acquire_item_lock

    def then_acquire(*args):
        act()
        return original(*args)

    monkeypatch.setattr(kyboot, "acquire_item_lock", then_acquire)


def test_a_prompt_changed_between_check_and_launch_is_not_launched(world, monkeypatch):
    def inject():
        with open(world.prompt, "ab") as handle:
            handle.write(b"injected after check\n")
    after_check(monkeypatch, inject)
    code = world.run()
    state = world.state()
    assert code == 3
    assert state["phase"] == "launch_failed" and "prompt_path changed after check" in state["launch_error"]
    assert state["pid"] is None and not world.launched()
    action = world.action()
    assert action["state"] == "FAILED" and "prompt_path changed" in action["result"]["launch_error"]
    assert not world.lock().exists()


def test_a_program_that_fails_to_start_at_launch_is_recorded_and_nothing_is_supervised(world, monkeypatch):
    world.install("fake_claude_ok.sh", private=True)
    after_check(monkeypatch, world.claude.unlink)
    code = world.run()
    state = world.state()
    assert code == 3
    assert state["phase"] == "launch_failed" and state["pid"] is None and state["termination"] is None
    assert "claude" in state["launch_error"] and state["ended_at"]
    assert world.action()["state"] == "FAILED" and not world.lock().exists()
    monkeypatch.undo()
    world.install("fake_claude_ok.sh")
    assert world.cli("run", world.launch_path).returncode == 1          # the job id is spent: no silent re-run
    assert world.state()["phase"] == "launch_failed"


def test_state_writes_are_atomic_and_the_first_write_is_exclusive(tmp_path):
    path = tmp_path / "state.json"
    kyboot.write_state(str(path), {"n": 1}, exclusive=True)
    with pytest.raises(FileExistsError):
        kyboot.write_state(str(path), {"n": 2}, exclusive=True)
    assert json.loads(path.read_text()) == {"n": 1}
    kyboot.write_state(str(path), {"n": 3})
    assert json.loads(path.read_text()) == {"n": 3}
    assert sorted(p.name for p in tmp_path.iterdir()) == ["state.json"]


def test_grace_and_the_command_line_must_be_well_formed(world):
    for bad in ("soon", "-1", "601"):
        cli = world.cli("run", world.launch_path, "--grace", bad)
        assert cli.returncode == 2 and "--grace" in cli.stderr
    for words in (["check", world.launch_path, "--grace", "1"], ["argv", world.launch_path, "--grace", "1"],
                  ["run", world.launch_path, "--manifest"], ["run", world.launch_path, "--force", "1"],
                  ["check", world.launch_path, "--manifest", "a", "--manifest", "b"],
                  ["check", world.launch_path, "extra"]):
        cli = world.cli(*words)
        assert cli.returncode == 2 and "usage:" in cli.stderr, words
    assert not Path(world.launch["state_path"]).exists() and not world.launched()
    assert kyboot.DEFAULT_GRACE_SECONDS == 20.0


# --------------------------------------------------------------------------------------------------------------
# the item lock: one live supervisor per item (plan §14 B-0c "its own proven instance lock")
# --------------------------------------------------------------------------------------------------------------
def test_process_matches_is_true_false_or_unknown_and_unknown_is_never_gone(monkeypatch):
    me, started = os.getpid(), kyboot.process_start(os.getpid())
    assert started and time.strptime(started, kyboot.LSTART_FMT)
    assert kyboot.process_matches(me, started) is True
    assert kyboot.process_matches(me, "  " + started.replace(" ", "   ", 1) + " ") is True
    assert kyboot.process_matches(me, OTHER_START) is False                # the id is alive, but it is another process
    dead, dead_start = dead_process()
    assert kyboot.process_matches(dead, dead_start) is False
    for unknown_start in (None, "", "   ", "yesterday", 7):
        assert kyboot.process_matches(me, unknown_start) is None, unknown_start
    for unknown_pid in (None, "123", True, 0, -1, 1.5):
        assert kyboot.process_matches(unknown_pid, started) is None, unknown_pid
    monkeypatch.setattr(kyboot, "ps_identity", lambda pid: None)            # ps could not be asked
    assert kyboot.process_matches(dead, dead_start) is None
    monkeypatch.setattr(kyboot, "ps_identity", lambda pid: ("Z", started))  # exited, not yet collected
    assert kyboot.process_matches(me, started) is False


def test_ps_identity_distinguishes_gone_from_unknown(monkeypatch):
    stat, started = kyboot.ps_identity(os.getpid())
    assert stat and not stat.startswith("Z") and time.strptime(started, kyboot.LSTART_FMT)
    dead, _ = dead_process()
    assert kyboot.ps_identity(dead) == "gone"
    assert kyboot.ps_identity("not a pid") is None

    answers = []
    monkeypatch.setattr(kyboot.subprocess, "run", lambda *a, **k: answers.pop(0))
    done = subprocess.CompletedProcess
    answers[:] = [done([], 1, "", ""), done([], 1, "", "ps: illegal process id\n"), done([], 1, "S", ""),
                  done([], 2, "", ""), done([], 0, "S", ""), done([], 0, "", ""),
                  done([], 0, "Ss   Sun Oct 11 22:22:21 2026    \n", ""), done([], 1, "Ss   Sun Oct 11 22:22:21 2026", "")]
    assert [kyboot.ps_identity(4242) for _ in range(8)] == [
        "gone", None, None, None, None, None, ("Ss", "Sun Oct 11 22:22:21 2026"), None]

    def unavailable(*args, **kwargs):
        raise OSError("ps is not there")
    monkeypatch.setattr(kyboot.subprocess, "run", unavailable)
    assert kyboot.ps_identity(os.getpid()) is None


def test_a_second_supervisor_for_the_same_item_is_refused_while_the_first_lives(world):
    world.set_prompt("FAKE_SLEEP:60\n")
    world.write()
    second = world.another_job("J-20261011T220000Z-b2")
    other_item = world.another_job("J-20261011T220100Z-b3", item="KV3-B-KYALLOC")
    first = start_supervisor(world, world.launch_path, "--grace", "5")
    try:
        state, owner = wait_until_running(world)
        assert owner["pid"] == first.pid and owner["session_or_run_id"].startswith("kyboot-")
        assert sorted(owner) == ["acquired_at", "child", "pgid", "pid", "process_start", "session_or_run_id"]
        assert owner["process_start"] == kyboot.process_start(first.pid) and owner["pgid"] == os.getpgid(first.pid)
        assert owner["child"] == {"job_id": JOB, "pid": state["pid"], "pgid": state["pgid"],
                                  "process_start": state["process_start"]}
        refused_run = subprocess.run([sys.executable, str(world.kyboot_path), "run", str(second)],
                                     capture_output=True, text=True, env=world.environ, timeout=60)
        assert refused_run.returncode == 1
        assert f"item lock: item {ITEM} is held by a live supervisor ({owner['session_or_run_id']}, pid {first.pid})" \
            in refused_run.stderr
        assert not (world.run_dir / "jobs" / "J-20261011T220000Z-b2").exists()
        assert not (world.run_dir / "actions" / "ACT-launch-J-20261011T220000Z-b2.json").exists()
        assert not (world.scratch / "jobs" / "J-20261011T220000Z-b2" / "tmp").exists()
        assert json.loads((world.lock() / "owner.json").read_text()) == owner         # the holder was not disturbed
        elsewhere = subprocess.run([sys.executable, str(world.kyboot_path), "run", str(other_item)],
                                   capture_output=True, text=True, env=world.environ, timeout=60)
        assert elsewhere.returncode == 0, elsewhere.stderr                            # another item is not blocked
        assert world.state("J-20261011T220100Z-b3")["item"] == "KV3-B-KYALLOC"
        assert world.state()["phase"] == "running"
    finally:
        first.send_signal(signal.SIGTERM)
        first.communicate(timeout=30)
    assert first.returncode == 130 and not world.lock().exists()
    after = subprocess.run([sys.executable, str(world.kyboot_path), "run", str(second)], capture_output=True, text=True,
                           env=world.environ, timeout=60)
    assert after.returncode == 0, after.stderr                                        # free once the first ended


def plant_lock(world, owner, item=ITEM) -> Path:
    lock = world.lock(item)
    lock.mkdir(parents=True)
    if owner is not None:
        text = owner if isinstance(owner, str) else json.dumps(owner)
        (lock / "owner.json").write_text(text, encoding="utf-8")
    return lock


def test_a_lock_whose_owner_is_positively_gone_is_taken_over(world):
    dead, dead_start = dead_process()
    owner = {"session_or_run_id": "kyboot-old", "pid": dead, "pgid": dead, "process_start": dead_start,
             "acquired_at": "2026-10-11T20:00:00.000000Z", "child": None}
    plant_lock(world, owner)
    assert world.run() == 0
    state = world.state()
    assert state["lock_taken_over_from"] == owner and state["phase"] == "ended"
    assert not world.lock().exists()
    assert [p.name for p in (world.run_dir / "locks").iterdir()] == []            # no grave left behind


def test_a_lock_whose_owner_id_now_belongs_to_another_process_is_taken_over(world):
    plant_lock(world, {"session_or_run_id": "kyboot-old", "pid": os.getpid(), "pgid": 1,
                       "process_start": OTHER_START, "acquired_at": "x", "child": None})
    assert world.run() == 0
    assert world.state()["lock_taken_over_from"]["process_start"] == OTHER_START


UNKNOWN_OWNERS = [
    ("no owner recorded", None),
    ("owner not json", "{not json"),
    ("owner not an object", "[]"),
    ("live id without a start", {"session_or_run_id": "x", "pid": "SELF", "process_start": None}),
    ("live id with an unreadable start", {"session_or_run_id": "x", "pid": "SELF", "process_start": "a while ago"}),
    ("id is not an integer", {"session_or_run_id": "x", "pid": "4242", "process_start": "START"}),
    ("no id at all", {"session_or_run_id": "x", "process_start": "START"}),
]


@pytest.mark.parametrize("what,owner", UNKNOWN_OWNERS, ids=[c[0] for c in UNKNOWN_OWNERS])
def test_a_lock_whose_owner_cannot_be_identified_is_never_taken_over(world, monkeypatch, capsys, what, owner):
    monkeypatch.setattr(kyboot, "LOCK_OWNER_WAIT_SECONDS", 0.2)
    if isinstance(owner, dict):
        owner = {key: os.getpid() if value == "SELF" else kyboot.process_start(os.getpid()) if value == "START"
                 else value for key, value in owner.items()}
    lock = plant_lock(world, owner)
    before = sorted((p.name, p.read_bytes()) for p in lock.iterdir())
    assert world.run() == 1
    assert sorted((p.name, p.read_bytes()) for p in lock.iterdir()) == before
    assert not world.launched() and not (world.run_dir / "jobs").exists() and not (world.run_dir / "actions").exists()
    said = capsys.readouterr().err
    assert "item lock:" in said and "never taken over" in said


def test_a_lock_is_never_taken_over_when_ps_cannot_be_asked(world, monkeypatch):
    dead, dead_start = dead_process()
    lock = plant_lock(world, {"session_or_run_id": "kyboot-old", "pid": dead, "process_start": dead_start})
    real = kyboot.ps_identity
    monkeypatch.setattr(kyboot, "ps_identity", lambda pid: None)
    assert world.run() == 1 and (lock / "owner.json").exists() and not world.launched()
    monkeypatch.setattr(kyboot, "ps_identity", real)
    assert world.run() == 0                                   # the same lock, once its owner is positively gone


def test_a_lock_held_by_a_live_owner_is_refused(world, capsys):
    me = os.getpid()
    lock = plant_lock(world, {"session_or_run_id": "kyboot-live", "pid": me, "pgid": os.getpgrp(),
                              "process_start": kyboot.process_start(me), "acquired_at": "x", "child": None})
    cli = world.cli("run", world.launch_path)
    assert cli.returncode == 1
    assert f"item lock: item {ITEM} is held by a live supervisor (kyboot-live, pid {me})" in cli.stderr
    assert (lock / "owner.json").exists() and not world.launched()
    assert world.check().findings == []                       # the lock is run's; check takes and needs none


def test_a_dead_owner_whose_recorded_job_is_alive_or_unknown_is_not_taken_over(world, capsys):
    dead, dead_start = dead_process()
    job = subprocess.Popen(["/bin/sleep", "60"])
    try:
        owner = {"session_or_run_id": "kyboot-old", "pid": dead, "process_start": dead_start,
                 "child": {"job_id": "J-OLD", "pid": job.pid, "pgid": job.pid,
                           "process_start": kyboot.process_start(job.pid)}}
        lock = plant_lock(world, owner)
        assert world.run() == 1 and not world.launched()
        assert "the job it recorded is alive or cannot be confirmed gone; reconcile that job" in capsys.readouterr().err
        for unknown_child in ("a job", {"pid": job.pid}, {"pid": "x", "process_start": "y"}):
            (lock / "owner.json").write_text(json.dumps(dict(owner, child=unknown_child)), encoding="utf-8")
            assert world.run() == 1 and not world.launched()
    finally:
        job.kill()
        job.wait()
    (lock / "owner.json").write_text(json.dumps(owner), encoding="utf-8")
    assert world.run() == 0                                   # owner gone and its job gone: taken over
    assert world.state()["lock_taken_over_from"]["child"]["job_id"] == "J-OLD"


def test_the_lock_is_released_only_by_the_run_that_holds_it(world, tmp_path):
    lock, reason, taken = kyboot.acquire_item_lock(str(world.run_dir), ITEM, "kyboot-mine")
    assert reason is None and taken is None and lock == str(world.lock())
    assert kyboot.release_item_lock(lock, "kyboot-someone-else") is False and world.lock().exists()
    again, reason, _ = kyboot.acquire_item_lock(str(world.run_dir), ITEM, "kyboot-second")
    assert again is None and "held by a live supervisor (kyboot-mine" in reason
    assert kyboot.release_item_lock(lock, "kyboot-mine") is True and not world.lock().exists()
    assert kyboot.release_item_lock(lock, "kyboot-mine") is False
    assert kyboot.item_lock_path("/r", "KV3-B-X") == "/r/locks/kyboot.KV3-B-X"


# --------------------------------------------------------------------------------------------------------------
# the action record (plan §4a.1): the intent before the side effect, the observed result after it
# --------------------------------------------------------------------------------------------------------------
def test_the_launch_is_recorded_as_intended_before_the_job_starts_and_completed_with_what_was_observed(world, staged):
    assert world.cli("run", world.launch_path).returncode == 0
    state, action = world.state(), world.action()
    at_launch = json.loads((world.job_scratch / "tmp" / "fake_actions_at_launch.txt").read_text())
    assert (world.job_scratch / "tmp" / "fake_locks_at_launch.txt").read_text().split() == [f"kyboot.{ITEM}"]
    assert sorted(action) == sorted(["schema", "action_id", "kind", "actor", "inputs", "target", "intended_transition",
                                     "created_at", "state", "result", "completed_at"])
    assert at_launch["state"] == "INTENDED" and at_launch["result"] is None and at_launch["completed_at"] is None
    for key in ("schema", "action_id", "kind", "actor", "inputs", "target", "intended_transition", "created_at"):
        assert at_launch[key] == action[key], key                       # completion changes only the outcome fields
    assert action["schema"] == "ky.action/1" and action["action_id"] == f"ACT-launch-{JOB}" and action["kind"] == "launch"
    assert action["actor"] == {"role": "planner", "holder_kind": "supervisor",
                               "controller_id": state["supervisor_run_id"]}
    assert action["inputs"] == {
        "launch_input_path": str(world.launch_path), "launch_input_sha256": sha(world.launch_path),
        "manifest_sha256": state["manifest_sha256"], "supervisor_sha256": sha(staged["fleet"] / "kyboot.py"),
        "qualification_sha256": sha(world.receipt_path()), "prompt_sha256": world.launch["prompt_sha256"],
        "packet_sha256": world.launch["packet_sha256"], "argv": launch_line(world.launch)}
    assert action["target"] == {"job_id": JOB, "item": ITEM, "kind": "BUILD", "role": "bootstrap-builder",
                                "worktree": str(world.repo), "branch": BRANCH,
                                "state_path": world.launch["state_path"]}
    assert JOB in action["intended_transition"] and ITEM in action["intended_transition"]
    assert action["state"] == "DONE"
    assert action["result"] == {"phase": "ended", "termination": "exited", "exit_code": 0, "exit_signal": None,
                                "group_gone": True, "pid": state["pid"], "pgid": state["pgid"],
                                "process_start": state["process_start"], "launch_error": None,
                                "state_path": world.launch["state_path"], "supervisor_exit": 0}
    assert kyboot.parse_utc(action["created_at"]) <= kyboot.parse_utc(state["started_at"])
    assert kyboot.parse_utc(action["completed_at"]) >= kyboot.parse_utc(state["ended_at"])
    assert sorted(p.name for p in (world.run_dir / "actions").iterdir()) == [f"ACT-launch-{JOB}.json"]


def test_an_action_that_was_already_intended_is_never_repeated(world, capsys):
    actions = world.run_dir / "actions"
    actions.mkdir()
    earlier = actions / f"ACT-launch-{JOB}.json"
    earlier.write_text('{"state": "INTENDED"}\n', encoding="utf-8")
    assert world.run() == 1
    said = capsys.readouterr().err
    assert "action:" in said and "never repeat it" in said
    assert not (world.run_dir / "locks").exists()             # refused at the look, before any lock was taken
    assert earlier.read_text() == '{"state": "INTENDED"}\n'
    assert not world.launched() and not Path(world.launch["state_path"]).exists() and not world.lock().exists()


def test_kyboots_action_record_is_one_the_sibling_action_tool_reads(world):
    """kyboot writes the record itself (kyaction.py did not exist when this was written); where the sibling tool
    is present, it must read the record as its own: same schema, same states, a result that is set"""
    if not (FLEET / "kyaction.py").is_file():
        pytest.skip("the sibling kyaction.py is not in this checkout")
    spec = importlib.util.spec_from_file_location("kyaction_sibling", FLEET / "kyaction.py")
    kyaction = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(kyaction)
    assert world.run() == 0
    mine = world.action()
    record = kyaction.load(str(world.run_dir), f"ACT-launch-{JOB}")
    assert record == mine and record["state"] == "DONE" and record["schema"] == kyaction.SCHEMA
    assert kyaction.check_actor(record["actor"]) == record["actor"]
    assert kyaction.unfinished(str(world.run_dir)) == []
    at_launch = json.loads((world.job_scratch / "tmp" / "fake_actions_at_launch.txt").read_text())
    assert at_launch["state"] == "INTENDED" and isinstance(at_launch["intended_transition"], str)
    assert set(at_launch) == {"schema", "action_id", "kind", "actor", "inputs", "target", "intended_transition",
                              "created_at", "state", "result", "completed_at"}


def test_an_action_record_that_appears_after_the_look_is_still_never_overwritten(world, monkeypatch):
    earlier = world.run_dir / "actions" / f"ACT-launch-{JOB}.json"

    def other_actor():
        earlier.parent.mkdir(exist_ok=True)
        earlier.write_text('{"state": "INTENDED", "by": "another actor"}\n', encoding="utf-8")
    after_check(monkeypatch, other_actor)
    assert world.run() == 1
    assert earlier.read_text() == '{"state": "INTENDED", "by": "another actor"}\n'
    assert not world.launched() and not Path(world.launch["state_path"]).exists() and not world.lock().exists()


# --------------------------------------------------------------------------------------------------------------
# what the supervisor never does (plan §14 B-0c; cockpit prompt item 3)
# --------------------------------------------------------------------------------------------------------------
def tree(folder: Path) -> dict:
    return {str(p.relative_to(folder)): (p.read_bytes(), p.stat().st_mtime_ns) for p in sorted(folder.rglob("*"))
            if p.is_file()}


def test_a_run_writes_only_its_job_state_its_action_and_its_lock(world):
    """no role-state file, nothing of the dispatcher's or the loops', nothing in the installed fleet"""
    bystanders = {"PLANNER_STATE.json": '{"role": "planner"}', "CONDUCTOR_STATE.json": '{"role": "conductor"}',
                  "DISPATCHER_STATE.json": "{}", "JOURNAL_PLANNER.md": "journal\n", "loops/planner.json": '{"enabled": true}',
                  "loops/dispatcher.json": '{"enabled": false}', "commands/20261011-1.json": "{}",
                  "DECISIONS_SURROGATE.jsonl": "", "INSTALL_RECEIPT.json": "{}", "claims/b1.json": "{}"}
    for name, text in bystanders.items():
        (world.run_dir / name).parent.mkdir(parents=True, exist_ok=True)
        (world.run_dir / name).write_text(text, encoding="utf-8")
    installed = world.ky_root / "fleet_live"
    installed.mkdir()
    (installed / "kydispatch.py").write_text("raise SystemExit('the dispatcher must never be started')\n")
    (installed / "kyboot.py").write_text("raise SystemExit('never the installed copy')\n")
    world.environ["KY_FLEET"] = str(installed)
    world.launch["env"]["KY_FLEET"] = str(installed)
    world.write()
    before_run, before_fleet, before_source = tree(world.run_dir), tree(installed), tree(world.staged["fleet"])
    world.auto_qualify = False
    cli = world.cli("run", world.launch_path)
    assert cli.returncode == 0, cli.stderr
    after_run = tree(world.run_dir)
    assert tree(installed) == before_fleet                               # fleet_live: not one byte, not one mtime
    assert tree(world.staged["fleet"]) == before_source                  # nor the reviewed source it runs from
    assert {name: after_run[name] for name in before_run} == before_run  # every earlier file is untouched
    assert sorted(set(after_run) - set(before_run)) == [f"actions/ACT-launch-{JOB}.json", f"jobs/{JOB}/state.json"]
    assert [p.name for p in (world.run_dir / "locks").iterdir()] == []
    assert not list(world.run_dir.rglob("*.tmp.*"))


def test_the_supervisor_starts_only_git_ps_the_manifest_tool_and_the_job():
    """static: every process the source can start, and no string that names the dispatcher, the loops or a
    role-state file (docstrings excluded — they say what is never done)"""
    source = (FLEET / "kyboot.py").read_text(encoding="utf-8")
    module = ast.parse(source)
    docstrings = set()
    for node in ast.walk(module):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef)) and ast.get_docstring(node, clean=False):
            docstrings.add(id(node.body[0].value))
    strings = [node.value for node in ast.walk(module)
               if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstrings]
    for banned in ("kydispatch", "kyloop", "kyctl", "kyjob", "_STATE.json", "/bin/sh", "bash", "KeepAlive"):
        assert not any(banned in text for text in strings), banned
    assert [text for text in strings if "fleet_live" in text] == ["/Users/Dev/kalayantra/fleet_live"]
    # the only launchd label it ever names is its own one-shot job's, and the only verbs are these three
    assert [text for text in strings if "in.marsys.kalayantra" in text] == ["in.marsys.kalayantra.boot."]
    verbs = [node.args[1].value for node in ast.walk(module)
             if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "launchctl"]
    assert sorted(verbs) == ["bootout", "bootstrap", "print"]
    starts = []
    for node in ast.walk(module):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in ("run", "Popen") \
                and isinstance(node.func.value, ast.Name) and node.func.value.id == "subprocess":
            starts.append(ast.unparse(node.args[0]))
    assert sorted(starts) == sorted([
        "['git', '-C', worktree, *args]",
        "[binary, '--version']",
        "[sys.executable, '-I', '-B', kymanifest_path, 'check', manifest_path, '--repo', source_repo, '--run', ky_run]",
        "['ps', '-o', 'stat=,lstart=', '-p', str(int(pid))]",
        "plan['argv']",
        "[PLUTIL, '-lint', plist]",
        "[program, *args]",
    ])
    assert kyboot.PLUTIL == "/usr/bin/plutil" and kyboot.DEFAULT_LAUNCHCTL == "/bin/launchctl"
    assert "os.system" not in source and "shell=True" not in source and "os.exec" not in source


# --------------------------------------------------------------------------------------------------------------
# the context a job runs in is the context its qualification was earned in
# --------------------------------------------------------------------------------------------------------------
def as_launchd(world, job=JOB):
    """this supervisor's environment as the fake launchd would make it: the job's label, and pid 1 as parent"""
    world.environ.update(XPC_SERVICE_NAME="in.marsys.kalayantra.boot." + job, KY_TEST_PPID="1")


def test_the_context_is_launchd_only_with_parent_pid_1_and_the_jobs_own_label(monkeypatch):
    assert kyboot.job_label(JOB) == LABEL and kyboot.LABEL_PREFIX == "in.marsys.kalayantra.boot."
    monkeypatch.setattr(kyboot.os, "getppid", lambda: 4242)
    assert kyboot.detect_context({}, JOB) == ("shell", False)
    assert kyboot.detect_context({"XPC_SERVICE_NAME": LABEL}, JOB) == ("shell", False)          # the parent is not 1
    monkeypatch.setattr(kyboot.os, "getppid", lambda: 1)                                         # production: real pid
    assert kyboot.detect_context({"XPC_SERVICE_NAME": LABEL}, JOB) == ("launchd", False)
    assert kyboot.detect_context({}, JOB) == ("shell", False)                                    # no label
    assert kyboot.detect_context({"XPC_SERVICE_NAME": "0"}, JOB) == ("shell", False)             # a terminal's value
    assert kyboot.detect_context({"XPC_SERVICE_NAME": LABEL + "x"}, JOB) == ("shell", False)     # another job's
    assert kyboot.detect_context({"XPC_SERVICE_NAME": LABEL}, "J-OTHER") == ("shell", False)
    assert kyboot.detect_context({"XPC_SERVICE_NAME": "in.marsys.kalayantra.qualify.planner"}, JOB) == ("shell", False)


def test_the_test_only_parent_pid_is_honoured_only_together_with_the_scratch_override(monkeypatch):
    monkeypatch.setattr(kyboot.os, "getppid", lambda: 4242)
    env = {"XPC_SERVICE_NAME": LABEL, "KY_TEST_PPID": "1"}
    assert kyboot.parent_pid(env) == (4242, False)                       # without the override it is not even read
    assert kyboot.detect_context(env, JOB) == ("shell", False)
    env["KY_SCRATCH_ROOT_OVERRIDE"] = "/somewhere"
    assert kyboot.parent_pid(env) == (1, True) and kyboot.detect_context(env, JOB) == ("launchd", True)
    assert kyboot.detect_context(dict(env, KY_TEST_PPID="2"), JOB) == ("shell", True)
    assert kyboot.detect_context(dict(env, KY_TEST_PPID="one"), JOB) == ("shell", True)
    monkeypatch.setattr(kyboot.os, "getppid", lambda: 1)                 # the injection wins over the real parent
    assert kyboot.detect_context(dict(env, KY_TEST_PPID="7"), JOB) == ("shell", True)
    source = Path(kyboot.__file__).read_text(encoding="utf-8")
    assert "TESTS ONLY: KY_TEST_PPID replaces it, and ONLY when KY_SCRATCH_ROOT_OVERRIDE" in source


@pytest.mark.parametrize("earned,how,expected", [
    ("launchd", "shell", "qualification context mismatch: receipt launchd, launch shell"),
    ("shell", "launchd", "qualification context mismatch: receipt shell, launch launchd"),
    ("LAUNCHD", "launchd", "qualification context mismatch: receipt LAUNCHD, launch launchd"),
    (None, "shell", "qualification context mismatch: receipt null, launch shell"),
    (["shell"], "shell", 'qualification context mismatch: receipt ["shell"], launch shell'),
])
def test_a_receipt_earned_in_another_context_does_not_qualify_this_launch(world, earned, how, expected):
    world.context = earned
    if how == "launchd":
        as_launchd(world)
    findings = refused(world, expected)
    assert len([line for line in findings if line.startswith("qualification")]) == 1
    assert world.run() == 1 and not world.launched() and not (world.run_dir / "jobs").exists()


def test_a_receipt_without_a_context_does_not_qualify(world):
    world.write()
    world.auto_qualify = False
    world.qualify(lambda r: r.pop("context"))
    refused(world, "qualification context mismatch: receipt null, launch shell")


def test_a_launchd_run_with_a_launchd_receipt_passes_and_records_its_context(world):
    world.context = "launchd"
    as_launchd(world)
    result = world.check()
    assert result.findings == [] and result.facts["launch_context"] == "launchd"
    assert result.facts["launch_context_parent_pid_injected"] is True
    assert world.run() == 0
    state = world.state()
    assert state["launch_context"] == "launchd" and state["launch_context_parent_pid_injected"] is True
    assert state["label"] == LABEL and state["termination"] == "exited"
    world.environ["XPC_SERVICE_NAME"] = "in.marsys.kalayantra.boot.J-ANOTHER"       # another job's agent: a shell
    refused(world, "qualification context mismatch: receipt launchd, launch shell")


# --------------------------------------------------------------------------------------------------------------
# submit / status / reap: the job as a one-shot launchd user agent (a fake launchctl stands in for launchd)
# --------------------------------------------------------------------------------------------------------------
ALLOWED_AGENT_ENV = ["HOME", "KY_ROOT", "KY_RUN", "KY_SCRATCH", "LANG", "PATH", "USER"]


def read_plist(path) -> dict:
    with open(path, "rb") as handle:
        return plistlib.load(handle)


@needs_plutil
def test_submit_renders_a_one_shot_agent_bootstraps_it_and_returns_while_the_job_runs_in_launchd(world, staged):
    world.context = "launchd"
    world.set_prompt("work\n" + result_line())
    cli = world.cli("submit", world.launch_path)
    assert cli.returncode == 0, cli.stderr
    said = json.loads(cli.stdout)
    plist_path = world.job_scratch / f"{LABEL}.plist"
    assert said == {"job_id": JOB, "label": LABEL, "plist": str(plist_path), "state_path": world.launch["state_path"]}
    # the agent: lints, one shot, this interpreter running the reviewed kyboot's `run` on the same input and manifest
    assert subprocess.run(["/usr/bin/plutil", "-lint", str(plist_path)], capture_output=True).returncode == 0
    plist = read_plist(plist_path)
    assert sorted(plist) == ["EnvironmentVariables", "Label", "ProcessType", "ProgramArguments", "RunAtLoad",
                             "StandardErrorPath", "StandardOutPath"]
    assert "KeepAlive" not in plist and plist["RunAtLoad"] is True and plist["ProcessType"] == "Background"
    assert plist["Label"] == LABEL
    assert plist["ProgramArguments"] == [sys.executable, "-u", str(staged["fleet"] / "kyboot.py"), "run",
                                         str(world.launch_path), "--manifest", str(world.manifest_path)]
    assert os.path.isabs(plist["ProgramArguments"][0]) and os.path.isabs(plist["ProgramArguments"][2])
    assert sorted(plist["EnvironmentVariables"]) == ALLOWED_AGENT_ENV == sorted(kyboot.AGENT_ENV_NAMES)
    assert plist["EnvironmentVariables"] == {
        "PATH": "/opt/homebrew/bin:/usr/bin:/bin", "HOME": str(world.home), "USER": plist["EnvironmentVariables"]["USER"],
        "LANG": "en_US.UTF-8", "KY_RUN": str(world.run_dir), "KY_SCRATCH": str(world.scratch),
        "KY_ROOT": str(world.ky_root)}
    assert plist["EnvironmentVariables"]["USER"] and "KY_TEST_MARKER" not in plist["EnvironmentVariables"]
    assert plist["StandardOutPath"] == str(world.job_scratch / "supervisor.out")
    assert plist["StandardErrorPath"] == str(world.job_scratch / "supervisor.err")
    # the submission is an action: intended before launchd was asked, done with launchctl's exit status
    at_bootstrap = json.loads((world.launchd / "submit_action_at_bootstrap.json").read_text())
    assert len(at_bootstrap) == 1 and at_bootstrap[0]["state"] == "INTENDED" and at_bootstrap[0]["result"] is None
    action = json.loads((world.run_dir / "actions" / f"ACT-submit-{JOB}.json").read_text())
    assert action["action_id"] == f"ACT-submit-{JOB}" and action["kind"] == "submit" and action["state"] == "DONE"
    assert action["result"] == {"launchctl": "bootstrap", "exit": 0, "stderr": "", "label": LABEL, "domain": DOMAIN,
                                "plist": str(plist_path)}
    assert action["target"]["label"] == LABEL and action["target"]["domain"] == DOMAIN
    assert action["inputs"]["plist_sha256"] == sha(plist_path)
    assert action["inputs"]["environment_names"] == ALLOWED_AGENT_ENV
    assert action["inputs"]["program_arguments"] == plist["ProgramArguments"]
    for key in ("schema", "action_id", "kind", "actor", "inputs", "target", "intended_transition", "created_at"):
        assert at_bootstrap[0][key] == action[key], key
    assert world.calls() == [["bootstrap", DOMAIN, str(plist_path)]]
    # launchd (the fake) ran it: in the launchd context, with only the agent's environment
    state = world.wait_ended()
    assert state["launch_context"] == "launchd" and state["label"] == LABEL
    assert state["termination"] == "exited" and state["exit_code"] == 0 and state["job_result_valid"] is True
    assert state["supervisor_pid"] == world.loaded()["pid"]
    assert world.action()["state"] == "DONE" and not world.lock().exists()
    assert set(world.loaded()["env_names"]) == set(ALLOWED_AGENT_ENV) | {"XPC_SERVICE_NAME", "KY_SCRATCH_ROOT_OVERRIDE",
                                                                        "KY_TEST_PPID"}
    names = {line.split("=", 1)[0] for line in (world.job_scratch / "tmp" / "fake_env.txt").read_text().splitlines()}
    assert names - {"PWD", "OLDPWD", "SHLVL", "_"} == set(world.launch["env"])       # the job's env is still its own
    assert json.loads((world.job_scratch / "supervisor.out").read_text()) == state
    assert (world.job_scratch / "supervisor.err").read_text() == ""


@needs_plutil
@pytest.mark.parametrize("what,break_it,reason", [
    ("a turn limit over the cap", lambda w: w.launch.update(max_turns=151), "max_turns: 151 exceeds the cap 150"),
    ("a receipt earned in a shell", lambda w: setattr(w, "context", "shell"),
     "qualification context mismatch: receipt shell, launch launchd"),
    ("a deadline in the past", lambda w: w.launch.update(deadline="2020-01-01T00:00:00Z"), "is not in the future"),
    ("a forbidden flag", lambda w: w.launch["extra_lean_flags"].append("--bare"), "--bare is forbidden"),
    ("a missing field", lambda w: w.launch.pop("role"), "required property 'role' is missing"),
])
def test_submit_refuses_whatever_check_refuses_and_asks_launchd_nothing(world, what, break_it, reason):
    world.context = "launchd"
    break_it(world)
    cli = world.cli("submit", world.launch_path)
    assert cli.returncode == 1 and cli.stdout == "" and reason in cli.stderr
    assert world.calls() == [] and not list(world.job_scratch.glob("*.plist"))
    assert not (world.run_dir / "actions").exists() and not (world.run_dir / "jobs").exists()


@needs_plutil
def test_submit_refuses_when_the_manifest_gate_or_the_qualification_fails(world):
    world.context = "launchd"
    world.write()
    world.auto_qualify = False
    world.qualify(lambda r: r.update(result="FAIL"))
    cli = world.cli("submit", world.launch_path)
    assert cli.returncode == 1 and 'only "PASS" qualifies' in cli.stderr
    world.qualify()
    (world.run_dir / "PROBES.json").unlink()
    cli = world.cli("submit", world.launch_path)
    assert cli.returncode == 1 and "manifest gate: refused: probes not recorded" in cli.stderr
    assert world.calls() == [] and not list(world.job_scratch.glob("*.plist")) and not (world.run_dir / "actions").exists()


@needs_plutil
def test_a_second_submit_and_a_submit_after_a_run_are_refused(world, capsys):
    world.context = "launchd"
    world.mode(start=False)                                   # launchd accepts the agent; nothing runs in this test
    assert world.cli("submit", world.launch_path).returncode == 0
    plist_before = (world.job_scratch / f"{LABEL}.plist").read_bytes()
    action_before = (world.run_dir / "actions" / f"ACT-submit-{JOB}.json").read_bytes()
    again = world.cli("submit", world.launch_path)
    assert again.returncode == 1 and again.stdout == ""
    assert f"submit: action {world.run_dir}/actions/ACT-submit-{JOB}.json already exists" in again.stderr
    assert "never repeat it" in again.stderr
    assert world.calls() == [["bootstrap", DOMAIN, str(world.job_scratch / f"{LABEL}.plist")]]      # asked once
    assert (world.job_scratch / f"{LABEL}.plist").read_bytes() == plist_before
    assert (world.run_dir / "actions" / f"ACT-submit-{JOB}.json").read_bytes() == action_before


@needs_plutil
def test_a_job_that_already_ran_is_not_submitted(world, capsys):
    assert world.run() == 0                                   # a shell run of this job id
    world.context = "launchd"
    capsys.readouterr()
    assert kyboot.submit(str(world.write()), world.environ, report=lambda text: None) == 1
    said = capsys.readouterr().err
    assert f"submit: state_path {world.launch['state_path']} already exists" in said
    assert f"ACT-launch-{JOB}.json already exists" in said and "stdout_path" in said
    assert world.calls() == [] and not list(world.job_scratch.glob("*.plist"))
    assert not (world.run_dir / "actions" / f"ACT-submit-{JOB}.json").exists()


@needs_plutil
def test_a_submission_record_that_appears_after_the_look_is_never_overwritten(world, monkeypatch):
    world.context = "launchd"
    record = world.run_dir / "actions" / f"ACT-submit-{JOB}.json"
    original = kyboot.sha256_file

    def another_submitter(path):
        if str(path).endswith(".plist"):                     # submit hashes the rendered plist just before its record
            record.parent.mkdir(parents=True, exist_ok=True)
            record.write_text('{"by": "another submitter"}\n', encoding="utf-8")
        return original(path)

    monkeypatch.setattr(kyboot, "sha256_file", another_submitter)
    assert kyboot.submit(str(world.write()), world.environ, report=lambda text: None) == 1
    assert record.read_text() == '{"by": "another submitter"}\n'
    assert world.calls() == [] and not list(world.job_scratch.glob("*.plist"))


@needs_plutil
@pytest.mark.parametrize("job_id", ["J-1.", "J..b", "J-20261011T215900Z-b1.."])
def test_a_job_id_that_is_not_a_safe_label_component_is_not_submitted(world, job_id):
    world.context = "launchd"
    world.write()
    other = world.another_job(job_id)
    assert kyschema.validate(kyschema.load_json(FLEET / "schemas" / "bootstrap_launch_input.json"),
                             json.loads(other.read_text())) == []          # a valid job id, but not a label
    cli = subprocess.run([sys.executable, str(world.kyboot_path), "submit", str(other)], capture_output=True, text=True,
                         env=world.environ, timeout=60)
    assert cli.returncode == 1 and f"submit: job_id '{job_id}' is not a safe launchd label component" in cli.stderr
    assert world.calls() == [] and not (world.run_dir / "actions").exists()
    for fine in ("J-1", "j_2.b-3", "20261011.a"):
        assert kyboot._LABEL_COMPONENT.match(fine), fine
    for unsafe in (job_id, "a/b", "a b", ".a", "a.", ""):
        assert not kyboot._LABEL_COMPONENT.match(unsafe), unsafe


@needs_plutil
def test_submit_is_refused_as_root_with_a_relative_launchctl_and_with_a_plist_that_does_not_lint(world, monkeypatch, capsys):
    world.context = "launchd"
    path = str(world.write())
    monkeypatch.setattr(kyboot.os, "geteuid", lambda: 0)
    assert kyboot.submit(path, world.environ, report=lambda text: None) == 1
    assert "submit: refused as root" in capsys.readouterr().err
    monkeypatch.undo()
    world.environ["KY_LAUNCHCTL"] = "launchctl"               # by name: on this PATH that is the fake (see World)
    assert kyboot.submit(path, world.environ, report=lambda text: None) == 1
    assert "submit: KY_LAUNCHCTL is not an absolute path" in capsys.readouterr().err
    assert world.calls() == [] and not list(world.job_scratch.glob("*.plist"))
    world.environ["KY_LAUNCHCTL"] = str(world.fakes["launchctl"])
    monkeypatch.setattr(kyboot, "PLUTIL", "/usr/bin/false")
    assert kyboot.submit(path, world.environ, report=lambda text: None) == 1
    assert "submit: the rendered plist fails plutil -lint (exit 1); it was removed" in capsys.readouterr().err
    monkeypatch.setattr(kyboot, "PLUTIL", str(world.root / "no-plutil"))
    assert kyboot.submit(path, world.environ, report=lambda text: None) == 1
    assert "fails plutil -lint (exit 127)" in capsys.readouterr().err
    assert world.calls() == [] and not list(world.job_scratch.glob("*.plist")) and not (world.run_dir / "actions").exists()


@needs_plutil
def test_the_agents_environment_is_exactly_the_allowed_names_whatever_the_caller_carries(world, monkeypatch, capsys):
    world.context = "launchd"
    world.mode(start=False)
    world.environ.update(NODE_OPTIONS="--inspect", GITHUB_HANDLE="x", LANG="fr_FR.UTF-8", USER="caller-user")
    assert kyboot.submit(str(world.write()), world.environ, report=lambda text: None) == 0
    environment = read_plist(world.job_scratch / f"{LABEL}.plist")["EnvironmentVariables"]
    assert sorted(environment) == ALLOWED_AGENT_ENV
    assert environment["USER"] == "caller-user" and environment["LANG"] == "en_US.UTF-8"
    assert environment["PATH"] == "/opt/homebrew/bin:/usr/bin:/bin" != world.environ["PATH"]
    assert not any(kyboot.forbidden_env_name(name) for name in environment)
    # a name that is not allowed can never be added: the rendering itself is refused
    job2 = world.another_job("J-20261011T220000Z-b2")
    real = kyboot.agent_environment
    monkeypatch.setattr(kyboot, "agent_environment", lambda *a: dict(real(*a), SSH_AUTH_SOCK="/x"))
    assert kyboot.submit(str(job2), world.environ, report=lambda text: None) == 1
    assert "submit: the agent's environment is not exactly the allowed names" in capsys.readouterr().err
    monkeypatch.setattr(kyboot, "agent_environment", lambda *a: {k: v for k, v in real(*a).items() if k != "KY_ROOT"})
    assert kyboot.submit(str(job2), world.environ, report=lambda text: None) == 1
    assert len(world.calls()) == 1


@needs_plutil
def test_a_bootstrap_that_launchd_refuses_is_recorded_as_failed_and_the_job_id_is_spent(world):
    world.context = "launchd"
    world.mode(bootstrap_exit=5)
    cli = world.cli("submit", world.launch_path)
    assert cli.returncode == 3 and "NOT SUBMITTED" in cli.stderr and "launchctl bootstrap exited 5" in cli.stderr
    assert json.loads(cli.stdout)["label"] == LABEL
    action = json.loads((world.run_dir / "actions" / f"ACT-submit-{JOB}.json").read_text())
    assert action["state"] == "FAILED" and action["result"]["exit"] == 5
    assert action["result"]["stderr"] == "Bootstrap failed: 5: Input/output error"
    assert world.loaded() is None and world.cli("submit", world.launch_path).returncode == 1
    world.environ["KY_LAUNCHCTL"] = str(world.root / "no-launchctl")
    job2 = world.another_job("J-20261011T220000Z-b2")
    assert kyboot.submit(str(job2), world.environ, report=lambda text: None) == 3
    failed = json.loads((world.run_dir / "actions" / "ACT-submit-J-20261011T220000Z-b2.json").read_text())
    assert failed["state"] == "FAILED" and failed["result"]["exit"] == 127


@needs_plutil
@pytest.mark.parametrize("mode,why", [({"parent": 4242}, "its parent is not launchd"),
                                      ({"xpc": "in.marsys.kalayantra.boot.J-OTHER"}, "it is another job's agent"),
                                      ({"xpc": "0"}, "it has no service name of its own")])
def test_a_run_that_is_not_really_inside_its_agent_refuses_there_and_reap_leaves_it_alone(world, mode, why):
    world.context = "launchd"
    world.mode(**mode)
    assert world.cli("submit", world.launch_path).returncode == 0          # submit cannot know; the agent does
    said = world.wait_for(lambda: (world.job_scratch / "supervisor.err").read_text()
                          if "reason(s)" in (world.job_scratch / "supervisor.err").read_text() else None)
    assert "qualification context mismatch: receipt launchd, launch shell" in said and "nothing was launched" in said
    assert gone(world.loaded()["pid"], wait=20)
    assert not world.launched() and not (world.run_dir / "jobs").exists()
    assert not (world.run_dir / "actions" / f"ACT-launch-{JOB}.json").exists()
    status = json.loads(world.cli("status", JOB).stdout)["jobs"][0]
    assert status["state"] is None and status["state_file"] == "missing" and status["label_loaded"] is True
    assert status["submit"]["state"] == "DONE" and status["process_alive"] is None
    reaped = json.loads(world.cli("reap", JOB).stdout)["reaped"]
    assert reaped == [{"job_id": JOB, "label": LABEL, "action": "left",
                       "why": "state.json is missing: the job's identity is unknown"}]
    assert [call[0] for call in world.calls()].count("bootout") == 0 and world.loaded() is not None


@needs_plutil
def test_reap_boots_out_a_finished_job_and_verifies_that_it_is_gone(world):
    world.context = "launchd"
    assert world.cli("submit", world.launch_path).returncode == 0
    state = world.wait_ended()
    world.auto_qualify = False                                # from here on this test only reads
    before = tree(world.run_dir)
    status = json.loads(world.cli("status", JOB).stdout)["jobs"][0]
    assert status["label_loaded"] is True and status["process_alive"] is False and status["supervisor_alive"] is False
    assert status["state"]["phase"] == "ended" and status["state"]["launch_context"] == "launchd"
    assert status["state"]["pid"] == state["pid"] and status["submit"]["state"] == "DONE"
    assert tree(world.run_dir) == before                      # status changes nothing
    cli = world.cli("reap")
    assert cli.returncode == 0, cli.stderr
    assert json.loads(cli.stdout) == {"reaped": [{"job_id": JOB, "label": LABEL, "action": "booted_out",
                                                  "why": None, "bootout_exit": 0, "absent": True, "phase": "ended",
                                                  "termination": "exited"}]}
    target = f"{DOMAIN}/{LABEL}"
    assert world.calls()[-3:] == [["print", target], ["bootout", target], ["print", target]]
    assert world.loaded() is None and tree(world.run_dir) == before
    again = json.loads(world.cli("reap", JOB).stdout)["reaped"][0]
    assert again["action"] == "not_loaded" and [c[0] for c in world.calls()].count("bootout") == 1
    assert json.loads(world.cli("status", JOB).stdout)["jobs"][0]["label_loaded"] is False


@needs_plutil
def test_reap_never_boots_out_a_job_that_is_running(world):
    world.context = "launchd"
    world.set_prompt("FAKE_SLEEP:60\n")
    assert world.cli("submit", world.launch_path).returncode == 0
    state, _ = wait_until_running(world)
    try:
        status = json.loads(world.cli("status").stdout)["jobs"]
        assert [job["job_id"] for job in status] == [JOB]
        assert status[0]["process_alive"] is True and status[0]["supervisor_alive"] is True
        assert status[0]["label_loaded"] is True and status[0]["state"]["phase"] == "running"
        reaped = json.loads(world.cli("reap").stdout)["reaped"]
        assert reaped == [{"job_id": JOB, "label": LABEL, "action": "left", "why": "the job's process is alive"}]
        assert [call[0] for call in world.calls()].count("bootout") == 0 and world.loaded() is not None
        assert world.state()["phase"] == "running" and not gone(state["pid"], wait=0.2)
    finally:
        os.kill(state["supervisor_pid"], signal.SIGTERM)       # what `launchctl bootout` would have done to it
    assert world.wait_ended()["termination"] == "interrupted_term"
    assert json.loads(world.cli("reap").stdout)["reaped"][0]["action"] == "booted_out"


def planted_state(world, **fields) -> dict:
    """a state.json as a finished, submitted job would have left it — then altered by `fields`"""
    dead, dead_start = dead_process()
    job, job_start = dead_process()
    state = {"job_id": JOB, "item": ITEM, "phase": "ended", "termination": "exited", "exit_code": 0, "pid": job,
             "process_start": job_start, "supervisor_pid": dead, "supervisor_process_start": dead_start,
             "launch_context": "launchd"}
    state.update(fields)
    path = world.run_dir / "jobs" / JOB / "state.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state), encoding="utf-8")
    world.plant_loaded()
    return state


def test_reap_boots_out_only_when_the_job_and_its_supervisor_are_positively_gone(world):
    me, started = os.getpid(), kyboot.process_start(os.getpid())
    cases = [
        ({"pid": me, "process_start": started}, "the job's process is alive"),
        ({"pid": me, "process_start": None}, "the job's process cannot be identified"),
        ({"pid": me, "process_start": "a while ago"}, "the job's process cannot be identified"),
        ({"pid": "4242"}, "the job's process cannot be identified"),
        ({"supervisor_pid": me, "supervisor_process_start": started}, "the supervisor is alive"),
        ({"supervisor_pid": me, "supervisor_process_start": None}, "the supervisor cannot be identified"),
        ({"supervisor_pid": None}, "the supervisor cannot be identified"),
        ({"phase": "running", "termination": None, "pid": me, "process_start": started}, "the job's process is alive"),
    ]
    for fields, why in cases:
        planted_state(world, **fields)
        entry = kyboot.reap_one(str(world.run_dir), world.environ, JOB)
        assert entry == {"job_id": JOB, "label": LABEL, "action": "left", "why": why}, fields
        status = kyboot.status_of(str(world.run_dir), world.environ, JOB)
        assert status["label_loaded"] is True
        if "job's process" in why:
            assert status["process_alive"] == (True if why.endswith("alive") else "unknown"), fields
        else:
            assert status["supervisor_alive"] == (True if why.endswith("alive") else None
                                                  if fields.get("supervisor_pid", me) is None else "unknown"), fields
    for document in ("{not json", "[]"):
        (world.run_dir / "jobs" / JOB / "state.json").write_text(document, encoding="utf-8")
        entry = kyboot.reap_one(str(world.run_dir), world.environ, JOB)
        assert entry["action"] == "left" and entry["why"] == "state.json is unreadable: the job's identity is unknown"
        assert kyboot.status_of(str(world.run_dir), world.environ, JOB)["state_file"] == "unreadable"
    assert [call[0] for call in world.calls()].count("bootout") == 0 and world.loaded() is not None
    # positively over, in each way a job can be over
    for fields in ({}, {"phase": "launch_failed", "pid": None, "process_start": None, "termination": None},
                   {"phase": "running", "termination": None}, {"phase": "prepared", "pid": None, "termination": None}):
        planted_state(world, **fields)
        entry = kyboot.reap_one(str(world.run_dir), world.environ, JOB)
        assert entry["action"] == "booted_out" and entry["absent"] is True and entry["bootout_exit"] == 0, fields
        assert world.loaded() is None
    assert [call[0] for call in world.calls()].count("bootout") == 4


def test_reap_reports_an_agent_that_is_still_loaded_after_bootout_and_a_launchctl_it_cannot_ask(world, monkeypatch):
    monkeypatch.setattr(kyboot, "ABSENT_CONFIRM_SECONDS", 0.3)
    planted_state(world)
    world.mode(bootout_unloads=False, bootout_exit=5)
    entry = kyboot.reap_one(str(world.run_dir), world.environ, JOB)
    assert entry["action"] == "booted_out" and entry["absent"] is False and entry["bootout_exit"] == 5
    cli = world.cli("reap", JOB)
    assert cli.returncode == 3 and json.loads(cli.stdout)["reaped"][0]["absent"] is False
    world.environ["KY_LAUNCHCTL"] = str(world.root / "no-launchctl")
    entry = kyboot.reap_one(str(world.run_dir), world.environ, JOB)
    assert entry == {"job_id": JOB, "label": LABEL, "action": "left", "why": "launchctl could not be asked"}
    assert kyboot.status_of(str(world.run_dir), world.environ, JOB)["label_loaded"] == "unknown"
    assert kyboot.label_loaded(world.environ, JOB) == "unknown"


def test_launchctl_is_never_looked_up_by_name(world):
    """a relative KY_LAUNCHCTL is not run — not even when a program of that name is on PATH (here: the fake)"""
    planted_state(world)
    world.environ["KY_LAUNCHCTL"] = "launchctl"
    assert shutil.which("launchctl", path=world.environ["PATH"]) == str(world.fakes["launchctl"])
    code, _, error = kyboot.launchctl(world.environ, "print", kyboot.agent_target(JOB))
    assert code == 127 and "is not an absolute path; it was not run" in error
    assert kyboot.label_loaded(world.environ, JOB) == "unknown"
    assert kyboot.reap_one(str(world.run_dir), world.environ, JOB)["why"] == "launchctl could not be asked"
    assert kyboot.status_of(str(world.run_dir), world.environ, JOB)["label_loaded"] == "unknown"
    assert world.calls() == [] and world.loaded() is not None
    world.environ["KY_LAUNCHCTL"] = str(world.fakes["launchctl"])
    assert kyboot.label_loaded(world.environ, JOB) is True and world.calls() == [["print", f"{DOMAIN}/{LABEL}"]]


def test_status_and_reap_are_about_known_jobs_only(world):
    assert json.loads(world.cli("status").stdout) == {"jobs": []}
    assert json.loads(world.cli("reap").stdout) == {"reaped": []}
    for command in ("status", "reap"):
        unknown = world.cli(command, "J-NOBODY")
        assert unknown.returncode == 1 and "no job J-NOBODY" in unknown.stderr
        assert world.cli(command, "../x").returncode == 2 and world.cli(command, "a", "b").returncode == 2
    assert world.calls() == []
    assert world.cli("run", world.launch_path).returncode == 0     # a shell job: it has a state, never an agent
    world.auto_qualify = False
    before = tree(world.run_dir)
    status = json.loads(world.cli("status").stdout)["jobs"]
    assert len(status) == 1 and status[0]["label_loaded"] is False and status[0]["submit"] is None
    assert status[0]["state"]["launch_context"] == "shell" and status[0]["process_alive"] is False
    assert json.loads(world.cli("reap").stdout)["reaped"][0]["action"] == "not_loaded"
    assert [call[0] for call in world.calls()].count("bootout") == 0 and tree(world.run_dir) == before
    assert kyboot.known_jobs(str(world.run_dir)) == [JOB] and kyboot.known_jobs(str(world.root / "nowhere")) == []
    assert kyboot.reap_one(str(world.run_dir), world.environ, JOB)["action"] == "not_loaded"
    planted_state(world, supervisor_pid=os.getpid(), supervisor_process_start=kyboot.process_start(os.getpid()))
    assert kyboot.reap_one(str(world.run_dir), world.environ, JOB)["why"] == "the supervisor is alive"
    assert kyboot.agent_target(JOB) == f"{DOMAIN}/{LABEL}"


# --------------------------------------------------------------------------------------------------------------
# validate, template, README
# --------------------------------------------------------------------------------------------------------------
VALIDATE = [("packet", "packet_bootstrap.json"), ("release_receipt", "release_receipt_wait.json"),
            ("awaiting", "awaiting.json"), ("surrogate_decision", "surrogate_decision_veto.json"),
            ("job_result", "job_result_done.json"), ("bootstrap_launch_input", "launch_input.json")]


def bare_cli(*args):
    return subprocess.run([sys.executable, kyboot.__file__, *map(str, args)], capture_output=True, text=True,
                          timeout=30, env={"PATH": TOOL_PATH, "PYTHONDONTWRITEBYTECODE": "1"})


@pytest.mark.parametrize("name,doc", VALIDATE)
def test_validate_accepts_each_schemas_fixture_and_refuses_it_against_another_schema(name, doc):
    assert sorted(n for n, _ in VALIDATE) == kyboot.schema_names() == MY_SCHEMAS
    ok = bare_cli("validate", name, FIX / doc)
    assert ok.returncode == 0 and "SCHEMA-VALID" in ok.stdout and "shape only" in ok.stdout
    other = next(n for n, _ in VALIDATE if n != name)
    wrong = bare_cli("validate", other, FIX / doc)
    assert wrong.returncode == 1 and "REFUSED" in wrong.stderr


def test_validate_refuses_an_unknown_schema_name_and_a_malformed_command():
    unknown = bare_cli("validate", "nonexistent", FIX / "awaiting.json")
    assert unknown.returncode == 2 and "unknown schema 'nonexistent'" in unknown.stderr
    assert bare_cli("validate", "../kyboot", FIX / "awaiting.json").returncode == 2
    assert bare_cli().returncode == 2 and bare_cli("check").returncode == 2 and bare_cli("launch", "x").returncode == 2
    assert bare_cli("validate", "awaiting", FIX / "absent.json").returncode == 1


def test_the_template_names_exactly_the_schema_fields_and_is_refused_until_filled(world):
    template = kyschema.load_json(TEMPLATES / "BOOTSTRAP_LAUNCH_INPUT.template.json")
    schema = kyschema.load_json(FLEET / "schemas" / "bootstrap_launch_input.json")
    assert sorted(template) == sorted(schema["required"])
    assert template["schema"] == "ky.bootstrap_launch_input/1" and template["claude_min_version"] == "2.1.296"
    assert template["plan_version"] == "2.7" == kymanifest.PLAN_VERSION
    assert set(template["env"]) <= set(kyboot.ENV_ALLOWLIST) and set(kyboot.ENV_REQUIRED) <= set(template["env"])
    world.write()
    result = kyboot.check(str(TEMPLATES / "BOOTSTRAP_LAUNCH_INPUT.template.json"), world.environ)
    assert not result.ok
    unfilled = [line for line in result.findings if "unfilled placeholder" in line]
    variable = sorted(set(template) - {"schema", "claude_min_version", "plan_version"})
    assert "role" in variable
    for field in variable:
        assert any(line.startswith(f"$.{field}") for line in unfilled), f"{field} carries no placeholder"
    cli = world.cli("run", TEMPLATES / "BOOTSTRAP_LAUNCH_INPUT.template.json")
    assert cli.returncode == 1 and "unfilled placeholder" in cli.stderr


def test_the_template_readme_explains_every_field_and_every_gate_within_sixty_lines():
    readme = (TEMPLATES / "BOOTSTRAP_LAUNCH_INPUT.README.md").read_text(encoding="utf-8")
    assert len(readme.splitlines()) <= 60
    schema = kyschema.load_json(FLEET / "schemas" / "bootstrap_launch_input.json")
    for field in schema["required"]:
        assert f"`{field}`" in readme, f"{field} is not explained"
    for phrase in ("refuses launch", "never from memory", "kyboot.py check", "VERSIONS.bootstrap.json",
                   "QUALIFICATIONS/<role>-<model>.json", "never from `fleet_live`", "locks/kyboot.<item>",
                   "actions/ACT-launch-<job_id>.json", "plan v2.7"):
        assert phrase in readme, phrase
