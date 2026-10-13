"""KV3-B-KYREGEN (relaunch plan v2.7 §6 REGEN row and inheritance predicate, §4a.1, §8.9): kyregen.sh, the REGEN job
script.

Every test builds its own world under pytest's temporary directory: a bare `origin`, a worktree made with `git init`,
a fixture generator and a fixture test outside the worktree, a recording `ky` double (KY_BIN), a recording git wrapper
(KY_GIT) and temporary KY_ROOT / KY_RUN. The action records are written by the real kyaction.py (KY_FLEET is this
checkout's fleet directory, read only). Nothing here touches /Users/Dev/kalayantra, a real remote, the tracker or a
process the test did not start itself."""
import hashlib
import importlib.util
import json
import os
import signal
import stat
import subprocess
import time
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
FLEET = HERE.parent
SCRIPT = FLEET / "kyregen.sh"
SCHEMAS = FLEET / "schemas"
PY = "/opt/homebrew/bin/python3"
GIT = "/usr/bin/git"
ITEM = "FX-7"
BRANCH = "kalayantra/fx-7"
REF = "refs/heads/" + BRANCH
PR = 41
JOB = "J-20261012T000000Z-regen"
RUN_ID = "R-20261012-regen-1"
PUSH_ID = "JOB-%s-push" % RUN_ID
REVIEW_ID = "JOB-%s-review" % RUN_ID
OUT = "gen/out.txt"
REGEN_KEYS = ["schema", "job_id", "item", "pr", "old_head", "new_head", "old_base", "new_base", "conflicted_paths",
              "outputs", "generator", "tests", "pushed", "review_registered", "inheritance"]
FORBIDDEN = ("--force", "-f", "rebase")


def load_module(name):
    spec = importlib.util.spec_from_file_location(name, FLEET / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


kyaction = load_module("kyaction")
kyschema = load_module("kyschema")

# The fixture generator: gen/out.txt is one line, the sha256 of inputs.txt, so two sides that both change inputs.txt
# always conflict in it. `mode` (a file beside the generator) selects a misbehaviour; `ran` counts the runs.
GENERATOR = '''import hashlib, os, subprocess, sys, time
here = os.path.dirname(os.path.abspath(__file__))
mode = open(os.path.join(here, "mode")).read().strip()
with open(os.path.join(here, "ran"), "a") as f:
    f.write(os.getcwd() + "\\n")
if mode == "hang":
    time.sleep(120)
if mode == "fail":
    sys.exit(9)
if mode != "idle":
    os.makedirs("gen", exist_ok=True)
    with open("gen/out.txt", "w") as f:
        f.write(hashlib.sha256(open("inputs.txt", "rb").read()).hexdigest() + "\\n")
if mode == "stray":
    open("stray.txt", "w").write("undeclared\\n")
if mode == "nested-stray":
    os.makedirs("deep/er", exist_ok=True)
    open("deep/er/stray.txt", "w").write("undeclared\\n")
if mode == "tracked":
    open("other.txt", "a").write("the generator was here\\n")
if mode == "staged":
    open("other.txt", "a").write("the generator was here\\n")
    subprocess.run(["/usr/bin/git", "add", "other.txt"], check=True)
if mode == "delete":
    os.unlink("other.txt")
if mode == "commit":
    subprocess.run(["/usr/bin/git", "add", "gen/out.txt"], check=True)
    subprocess.run(["/usr/bin/git", "commit", "-q", "-m", "the generator committed"], check=True)
'''

# The fixture test: the regenerated output must be the sha256 of the MERGED inputs.txt.
CHECK = '''import hashlib, sys
want = hashlib.sha256(open("inputs.txt", "rb").read()).hexdigest() + "\\n"
sys.exit(0 if open("gen/out.txt").read() == want else 1)
'''

KY_DOUBLE = '''#!%s -IB
import json, os, sys
here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(here, "ky.calls"), "a") as f:
    f.write(json.dumps({"argv": sys.argv[1:], "KY_STREAM": os.environ.get("KY_STREAM"),
                        "KY_LANE": os.environ.get("KY_LANE"), "cwd": os.getcwd()}) + "\\n")
code = os.path.join(here, "ky.exit")
sys.exit(int(open(code).read()) if os.path.exists(code) else 0)
''' % PY

# The git wrapper records every argv (one line per call, each argument followed by US), then runs the real git. `git.mode`: "swallow-push" answers a push with exit 0
# without pushing anything; "blind" makes `ls-remote` fail.
GIT_WRAPPER = '''#!/bin/sh
here=${0%%/*}
{ printf '%%s\\037' "$@"; printf '\\n'; } >> "$here/git.calls"
mode=""
[ -f "$here/git.mode" ] && mode=$(cat "$here/git.mode")
for a in "$@"; do
  [ "$mode" = swallow-push ] && [ "$a" = push ] && exit 0
  [ "$mode" = blind ] && [ "$a" = ls-remote ] && exit 128
done
exec %s "$@"
''' % GIT


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha_file(path):
    return sha_bytes(Path(path).read_bytes())


def lstart(pid):
    return subprocess.run(["/bin/ps", "-o", "lstart=", "-p", str(pid)], capture_output=True, text=True,
                          env={"LC_ALL": "C", "PATH": "/bin:/usr/bin"}).stdout.strip()


def calls(path):
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


class Rig:
    """One fixture world. History: C0 on main; the item branch F1 (changes line 1 of inputs.txt and other.txt,
    regenerates gen/out.txt) is pushed and is the registered head; main moves to C1 (changes the last line of
    inputs.txt, regenerates gen/out.txt; with conflict_other also other.txt). Merging C1 into F1 conflicts in
    gen/out.txt only — or, with conflict_other, in other.txt as well. With generator_in_repo the generator is a tracked
    file (tools/gen.py) that main revises in C1, so the merge itself changes it, without a conflict."""

    def __init__(self, tmp, conflict_other=False, generator_in_repo=False):
        self.tmp = Path(os.path.realpath(tmp))
        self.home, self.root, self.run = self.tmp / "home", self.tmp / "ky_root", self.tmp / "ky_root" / "run"
        self.tools, self.origin, self.wt = self.tmp / "tools", self.tmp / "origin.git", self.tmp / "wt"
        for d in (self.home, self.run / "jobs" / JOB, self.tools):
            d.mkdir(parents=True)
        self.generator, self.check = self.tools / "gen.py", self.tools / "check.py"
        self.generator.write_text(GENERATOR)
        self.check.write_text(CHECK)
        self.set_mode("ok")
        for name, text in (("ky", KY_DOUBLE), ("git", GIT_WRAPPER)):
            (self.tools / name).write_text(text)
            os.chmod(self.tools / name, 0o755)
        self.ky_calls, self.git_calls, self.ran = self.tools / "ky.calls", self.tools / "git.calls", self.tools / "ran"
        self.regen_json = self.run / "jobs" / JOB / "regen.json"
        self.state_json = self.run / "jobs" / JOB / "state.json"
        self.children = []

        self.g("init", "-q", "--bare", str(self.origin), cwd=self.tmp)
        self.g("init", "-q", "-b", "main", str(self.wt), cwd=self.tmp)
        for key, value in (("user.name", "fixture"), ("user.email", "fixture@example.invalid"),
                           ("commit.gpgsign", "false")):
            self.g("config", key, value)
        self.g("remote", "add", "origin", str(self.origin))
        (self.wt / ".gitignore").write_text("__pycache__/\n*.ignored\n")
        (self.wt / "inputs.txt").write_text("".join("line %d\n" % i for i in range(1, 13)))
        (self.wt / "other.txt").write_text("other 1\n")
        (self.wt / "keep.txt").write_text("never touched\n")
        self.inside = self.wt / "tools" / "gen.py"
        if generator_in_repo:
            self.inside.parent.mkdir()
            self.inside.write_text(GENERATOR)
            (self.inside.parent / "mode").write_text("ok\n")
            (self.wt / ".gitignore").write_text("__pycache__/\n*.ignored\ntools/ran\n")
        self.generate()
        self.c0 = self.commit("C0")
        self.g("push", "-q", "origin", "main")
        self.g("checkout", "-q", "-b", BRANCH)
        self.edit_line(1, "line 1 (the item)")
        (self.wt / "other.txt").write_text("other 1 (the item)\n")
        self.generate()
        self.f1 = self.commit("F1")
        self.g("push", "-q", "origin", BRANCH)
        self.g("checkout", "-q", "main")
        self.edit_line(12, "line 12 (main)")
        if conflict_other:
            (self.wt / "other.txt").write_text("other 1 (main)\n")
        if generator_in_repo:
            self.inside.write_text(GENERATOR + "# main's revision\n")
        self.generate()
        self.c1 = self.commit("C1")
        self.g("push", "-q", "origin", "main")
        self.g("checkout", "-q", BRANCH)
        self.out_before = sha_file(self.wt / OUT)
        self.state = {
            "kind": "REGEN", "item": ITEM, "stream": "K", "slot": "K2", "worktree": str(self.wt), "branch": BRANCH,
            "pr": PR, "registered_head": self.f1, "base_sha": self.c1, "queue_authorised": False,
            "regen": {"outputs": [OUT],
                      "generator": {"argv": [PY, "-I", "-B", str(self.generator)], "path": str(self.generator),
                                    "sha256": sha_file(self.generator)},
                      "tests": [[PY, "-I", "-B", str(self.check)]]}}
        self.lock(os.getpid(), lstart(os.getpid()))

    # --- building blocks ---
    def g(self, *args, cwd=None, check=True):
        env = {"PATH": "/usr/bin:/bin", "HOME": str(self.home), "GIT_CONFIG_NOSYSTEM": "1", "LC_ALL": "C",
               "GIT_TERMINAL_PROMPT": "0"}
        r = subprocess.run([GIT] + list(args), cwd=str(cwd or self.wt), env=env, capture_output=True, text=True)
        assert not check or r.returncode == 0, (args, r.stdout, r.stderr)
        return r.stdout.strip()

    def edit_line(self, n, text):
        lines = (self.wt / "inputs.txt").read_text().splitlines()
        lines[n - 1] = text
        (self.wt / "inputs.txt").write_text("\n".join(lines) + "\n")

    def generate(self):
        (self.wt / "gen").mkdir(exist_ok=True)
        (self.wt / OUT).write_text(sha_file(self.wt / "inputs.txt") + "\n")

    def commit(self, message):
        self.g("add", "-A")
        self.g("commit", "-q", "-m", message)
        return self.g("rev-parse", "HEAD")

    def set_mode(self, mode):
        (self.tools / "mode").write_text(mode + "\n")

    def lock(self, pid, start, **more):
        owner = dict({"session_or_run_id": "dispatcher-fixture", "pid": pid, "pgid": os.getpgid(0),
                      "process_start": start, "acquired_at": "2026-10-12T00:00:00Z"}, **more)
        d = self.run / "locks" / ("item." + ITEM)
        d.mkdir(parents=True, exist_ok=True)
        (d / "owner.json").write_text(json.dumps({k: v for k, v in owner.items() if v is not None}))

    def env(self, **over):
        env = {"PATH": "/usr/bin:/bin", "HOME": str(self.home), "TMPDIR": str(self.tmp), "LC_ALL": "C",
               "GIT_CONFIG_NOSYSTEM": "1", "KY_ROOT": str(self.root), "KY_RUN": str(self.run), "KY_FLEET": str(FLEET),
               "KY_RUN_ID": RUN_ID, "KY_ROLE": "regen", "KY_CONTROLLER_ID": "dispatcher-fixture",
               "KY_GIT": str(self.tools / "git"), "KY_BIN": str(self.tools / "ky")}
        env.update(over)
        return {k: v for k, v in env.items() if v is not None}

    def write_state(self):
        self.state_json.write_text(json.dumps(self.state))

    def go(self, *argv, env=None, write=True):
        if write:
            self.write_state()
        return subprocess.run([str(SCRIPT)] + list(argv or (JOB,)), env=env or self.env(), capture_output=True,
                              text=True, stdin=subprocess.DEVNULL, timeout=300, cwd=str(self.tmp))

    # --- observations ---
    def head(self):
        return self.g("rev-parse", "HEAD")

    def remote_head(self, ref=REF):
        out = self.g("ls-remote", str(self.origin), ref, cwd=self.tmp)
        return out.split()[0] if out else None

    def status(self):
        return self.g("status", "--porcelain", "--untracked-files=all")

    def git_argvs(self):
        if not self.git_calls.exists():
            return []
        return [line.split("\x1f")[:-1] for line in self.git_calls.read_text().split("\n")[:-1]]

    def git_verbs(self):
        return [next((a for a in argv if not a.startswith("-")), None) for argv in self.git_argvs()]

    def record(self, action_id):
        path = self.run / "actions" / (action_id + ".json")
        return json.loads(path.read_text()) if path.exists() else None

    def regen(self):
        return json.loads(self.regen_json.read_text())

    def assert_untouched(self, head=None):
        """Clean at the registered head, no merge in progress, nothing pushed, nothing registered, no record."""
        assert self.head() == (head or self.f1)
        assert self.status() == ""
        assert not (self.wt / ".git" / "MERGE_HEAD").exists()
        assert self.remote_head() == self.f1
        assert "push" not in self.git_verbs()
        assert calls(self.ky_calls) == []
        assert not self.regen_json.exists()
        assert not (self.run / "actions").exists() or list((self.run / "actions").iterdir()) == []

    def move_remote(self):
        """Somebody else pushes to the PR branch: the next push from the worktree is not a fast-forward."""
        clone = self.tmp / "elsewhere"
        self.g("clone", "-q", "--branch", BRANCH, str(self.origin), str(clone), cwd=self.tmp)
        for key, value in (("user.name", "other"), ("user.email", "other@example.invalid"), ("commit.gpgsign", "false")):
            self.g("config", key, value, cwd=clone)
        (clone / "keep.txt").write_text("pushed by somebody else\n")
        self.g("commit", "-q", "-am", "elsewhere", cwd=clone)
        self.g("push", "-q", "origin", BRANCH, cwd=clone)
        return self.g("rev-parse", "HEAD", cwd=clone)


@pytest.fixture
def rig(tmp_path):
    r = Rig(tmp_path)
    yield r
    finish(r)


@pytest.fixture
def rig_other(tmp_path):
    r = Rig(tmp_path, conflict_other=True)
    yield r
    finish(r)


def finish(r):
    for child in r.children:                     # only processes this test started itself
        child.kill()
        child.wait()
    for argv in r.git_argvs():                   # acceptance 7: never forced, never rebased — in every test
        assert not [a for a in argv if a in FORBIDDEN or a.startswith("--force") or a.startswith("+")], argv
    for path in ((r.run / "actions").iterdir() if (r.run / "actions").exists() else ()):
        found = kyschema.validate(json.loads((SCHEMAS / "action.json").read_text(encoding="utf-8")),
                                  json.loads(path.read_text()))
        assert found == [], "\n".join(found)


# ───────────────────────────────────────── the file itself ─────────────────────────────────────────

def test_the_script_is_an_executable_bash_script_with_absolute_tools():
    text = SCRIPT.read_text(encoding="utf-8")
    assert text.startswith("#!/bin/bash\n")
    assert stat.S_IMODE(SCRIPT.stat().st_mode) & 0o111 == 0o111
    listed = subprocess.run([GIT, "ls-files", "-s", "--", SCRIPT.name], cwd=str(FLEET), capture_output=True, text=True)
    assert listed.stdout.split()[:1] in ([], ["100755"])        # once it is in the index, its mode is 100755
    assert "python3 -I -B" in text or '"$PY" -I -B' in text     # the embedded program runs isolated, no bytecode
    for word in ("--force", "rebase", " -f ", "printenv"):
        assert word not in text, word


# ───────────────────────────────────────── acceptance 1 ─────────────────────────────────────────

def test_a_confined_conflict_is_merged_regenerated_tested_pushed_and_registered(rig):
    r = rig.go()
    assert r.returncode == 0, r.stderr
    new = rig.head()
    assert len(new) == 40 and new != rig.f1
    assert rig.g("rev-list", "--parents", "-n", "1", "HEAD").split() == [new, rig.f1, rig.c1]     # two parents
    assert rig.g("log", "-1", "--format=%s") == "REGEN %s: merge %s, regenerate declared outputs" % (ITEM, rig.c1)
    assert rig.status() == "" and rig.g("symbolic-ref", "HEAD") == REF

    merged = (rig.wt / "inputs.txt").read_text()
    assert "line 1 (the item)" in merged and "line 12 (main)" in merged                        # both sides
    assert (rig.wt / OUT).read_text() == sha_bytes(merged.encode()) + "\n"                        # regenerated
    assert rig.g("diff", "--name-only", rig.f1, new).split() == [OUT, "inputs.txt"]
    assert rig.g("diff", "--name-only", rig.c1, new).split() == [OUT, "inputs.txt", "other.txt"]
    assert rig.ran.read_text().splitlines() == [str(rig.wt)]                                     # once, in the worktree

    assert rig.remote_head() == new                                                              # pushed
    assert calls(rig.ky_calls) == [{"argv": ["review", ITEM, "--detail", "PR #%d @ %s" % (PR, new)],
                                    "KY_STREAM": "K", "KY_LANE": "K2", "cwd": str(rig.wt)}]

    doc = rig.regen()
    assert list(doc) == REGEN_KEYS
    assert doc == {
        "schema": "ky.regen/1", "job_id": JOB, "item": ITEM, "pr": PR, "old_head": rig.f1, "new_head": new,
        "old_base": rig.c0, "new_base": rig.c1, "conflicted_paths": [OUT],
        "outputs": [{"path": OUT, "sha256_before": rig.out_before, "sha256_after": sha_file(rig.wt / OUT)}],
        "generator": {"argv": rig.state["regen"]["generator"]["argv"], "sha256": sha_file(rig.generator)},
        "tests": [{"argv": rig.state["regen"]["tests"][0], "exit": 0}],
        "pushed": True, "review_registered": True, "inheritance": None}
    assert doc["outputs"][0]["sha256_before"] != doc["outputs"][0]["sha256_after"]
    assert [p.name for p in rig.regen_json.parent.iterdir()] == ["state.json", "regen.json"] or \
        sorted(p.name for p in rig.regen_json.parent.iterdir()) == ["regen.json", "state.json"]    # no temp file left

    push, review = rig.record(PUSH_ID), rig.record(REVIEW_ID)
    assert push["state"] == "DONE" and push["kind"] == "git_push"
    assert push["inputs"] == {"remote": "origin", "ref": REF, "commit": new}
    assert push["result"]["commit"] == new and push["result"]["observed_by"] == "git ls-remote"
    assert push["actor"] == {"role": "regen", "holder_kind": "job", "controller_id": "dispatcher-fixture",
                             "run_id": RUN_ID}
    assert review["state"] == "DONE" and review["kind"] == "tracker_event" and review["result"]["exit"] == 0
    assert review["inputs"]["detail"] == "PR #%d @ %s" % (PR, new)
    assert sorted(p.name for p in (rig.run / "actions").iterdir()) == [PUSH_ID + ".json", REVIEW_ID + ".json"]

    verbs = rig.git_verbs()                       # the order of the side effects: merge, commit, push, then the look
    assert verbs.index("merge") < verbs.index("commit") < verbs.index("push") < len(verbs) - 1 - verbs[::-1].index("ls-remote")
    assert ["merge", "--no-commit", "--no-ff", rig.c1] in rig.git_argvs()
    assert ["push", "origin", "HEAD:" + REF] in rig.git_argvs()
    assert ["ls-remote", "origin", REF] in rig.git_argvs()


def test_the_push_record_is_what_the_controller_observer_reads(rig):
    """kyloop's git_push observer needs {remote, ref, commit} in inputs (or target) and no foreign `repo`."""
    assert rig.go().returncode == 0
    push = rig.record(PUSH_ID)
    assert set(push["inputs"]) == {"remote", "ref", "commit"} and "repo" not in push["target"]
    assert push["target"]["item"] == ITEM and push["target"]["pr"] == PR


def test_a_merge_without_any_conflict_still_regenerates_and_makes_a_two_parent_commit(rig):
    rig.g("checkout", "-q", "main")                         # main gains a commit that touches neither side's files
    (rig.wt / "keep.txt").write_text("touched on main only\n")
    c2 = rig.commit("C2")
    rig.g("checkout", "-q", BRANCH)
    rig.g("merge", "-q", "--no-edit", rig.c1, check=False)  # the item already carries C1, resolved and pushed
    rig.generate()
    resolved = rig.commit("resolved by hand")
    rig.g("push", "-q", "origin", BRANCH)
    rig.git_calls.unlink(missing_ok=True)
    rig.state.update(registered_head=resolved, base_sha=c2)
    r = rig.go()
    assert r.returncode == 0, r.stderr
    doc = rig.regen()
    assert doc["conflicted_paths"] == [] and doc["old_base"] == rig.c1 and doc["new_base"] == c2
    assert doc["outputs"][0]["sha256_before"] == doc["outputs"][0]["sha256_after"]
    assert rig.g("rev-list", "--parents", "-n", "1", "HEAD").split()[1:] == [resolved, c2]
    assert rig.remote_head() == rig.head()


# ───────────────────────────────────────── acceptance 2 ─────────────────────────────────────────

def test_a_conflict_in_an_undeclared_path_changes_nothing(rig_other):
    rig = rig_other
    r = rig.go()
    assert r.returncode == 3, r.stderr
    assert "other.txt" in r.stderr
    rig.assert_untouched()
    assert not rig.ran.exists()                              # the generator never ran
    assert "merge" in rig.git_verbs() and "commit" not in rig.git_verbs()


def test_a_conflict_is_confined_only_by_the_declaration(rig_other):
    """The same history is a REGEN once other.txt is declared too: the detector reads the declaration."""
    rig = rig_other
    rig.state["regen"]["outputs"] = [OUT, "other.txt"]
    r = rig.go()
    assert r.returncode == 4, r.stderr                       # … but this generator leaves other.txt in conflict
    rig.assert_untouched()


# ───────────────────────────────────────── acceptance 3 ─────────────────────────────────────────

def test_a_generator_that_differs_from_its_pin_is_never_run(rig):
    rig.write_state()
    rig.generator.write_text(GENERATOR + "# one byte more\n")
    r = rig.go(write=False)
    assert r.returncode == 4, r.stderr
    rig.assert_untouched()
    assert not rig.ran.exists()
    assert "merge" not in rig.git_verbs()


def test_a_pin_that_is_not_the_generators_hash_is_refused(rig):
    rig.state["regen"]["generator"]["sha256"] = "0" * 64
    assert rig.go().returncode == 4
    rig.assert_untouched()
    assert not rig.ran.exists()


def test_a_generator_that_the_merge_itself_changes_is_not_the_pinned_one(tmp_path):
    """The generator is a tracked file and main revised it: after the merge it is no longer the pinned file."""
    rig = Rig(tmp_path, generator_in_repo=True)
    try:
        rig.state["regen"]["generator"] = {"argv": [PY, "-I", "-B", str(rig.inside)], "path": str(rig.inside),
                                           "sha256": sha_file(rig.inside)}
        r = rig.go()
        assert r.returncode == 4, r.stderr
        assert "after the merge" in r.stderr and "merge" in rig.git_verbs()
        rig.assert_untouched()
        assert not (rig.inside.parent / "ran").exists() and sha_file(rig.inside) == sha_bytes(GENERATOR.encode())
    finally:
        finish(rig)


@pytest.mark.parametrize("mode", ["stray", "nested-stray", "tracked", "staged", "delete", "commit", "fail", "idle"])
def test_a_generator_that_writes_outside_the_declared_outputs_changes_nothing(rig, mode):
    """stray / nested-stray: a new undeclared file · tracked: an undeclared tracked file modified · staged: the same,
    staged by the generator · delete: an undeclared tracked file removed · commit: the generator moved HEAD ·
    fail: it exits non-zero · idle: it leaves the declared output in conflict."""
    rig.set_mode(mode)
    r = rig.go()
    assert r.returncode == 4, r.stderr
    assert rig.ran.read_text().splitlines() == [str(rig.wt)]             # it did run, once
    rig.assert_untouched()
    assert not (rig.wt / "stray.txt").exists() and not (rig.wt / "deep" / "er" / "stray.txt").exists()
    assert (rig.wt / "other.txt").read_text() == "other 1 (the item)\n"
    assert (rig.wt / OUT).read_text() and sha_file(rig.wt / OUT) == rig.out_before


# ───────────────────────────────────────── acceptance 4 ─────────────────────────────────────────

def test_a_failing_test_pushes_nothing(rig):
    rig.state["regen"]["tests"] = [[PY, "-I", "-B", str(rig.check)], [PY, "-I", "-B", "-c", "import sys; sys.exit(7)"],
                                   [PY, "-I", "-B", "-c", "open('never.txt', 'w')"]]
    r = rig.go()
    assert r.returncode == 5, r.stderr
    rig.assert_untouched()
    assert rig.ran.exists() and not (rig.wt / "never.txt").exists()      # the third test never ran
    assert "commit" not in rig.git_verbs()


def test_the_test_runs_against_the_regenerated_merge(rig):
    """The fixture test compares gen/out.txt with the merged inputs.txt: it fails when nothing was regenerated."""
    stale = rig.tools / "stale.py"                # a generator that restores the item's own (stale) output
    stale.write_text("import subprocess\nopen('gen/out.txt', 'w').write(%r)\n" % (rig.wt / OUT).read_text())
    rig.state["regen"]["generator"] = {"argv": [PY, "-I", "-B", str(stale)], "path": str(stale),
                                       "sha256": sha_file(stale)}
    assert rig.go().returncode == 5
    rig.assert_untouched()


@pytest.mark.parametrize("snippet", ["open('left_behind.txt', 'w').write('x')", "open('other.txt', 'a').write('x')"])
def test_a_test_that_changes_the_worktree_pushes_nothing(rig, snippet):
    rig.state["regen"]["tests"].append([PY, "-I", "-B", "-c", snippet])
    r = rig.go()
    assert r.returncode == 5, r.stderr
    rig.assert_untouched()
    assert not (rig.wt / "left_behind.txt").exists()


# ───────────────────────────────────────── acceptance 5 ─────────────────────────────────────────

def refused_before_anything(rig, r, code=73):
    assert r.returncode == code, r.stderr
    assert "merge" not in rig.git_verbs() and "push" not in rig.git_verbs() and "commit" not in rig.git_verbs()
    assert not rig.ran.exists() and calls(rig.ky_calls) == [] and not rig.regen_json.exists()
    assert rig.remote_head() == rig.f1


@pytest.mark.parametrize("dirt", ["untracked", "modified", "staged"])
def test_a_dirty_worktree_is_refused(rig, dirt):
    if dirt == "untracked":
        (rig.wt / "note.txt").write_text("mine\n")
    else:
        (rig.wt / "keep.txt").write_text("edited\n")
        if dirt == "staged":
            rig.g("add", "keep.txt")
    before = rig.status()
    refused_before_anything(rig, rig.go())
    assert rig.status() == before and rig.head() == rig.f1              # the dirt is the owner's: left exactly as it was


def test_a_head_that_is_not_the_registered_head_is_refused(rig):
    (rig.wt / "keep.txt").write_text("one more commit\n")
    moved = rig.commit("unregistered")
    refused_before_anything(rig, rig.go())
    assert rig.head() == moved and rig.status() == ""


def test_an_outstanding_queue_authorisation_is_refused(rig):
    rig.state["queue_authorised"] = True
    refused_before_anything(rig, rig.go())
    rig.assert_untouched()


def test_a_base_that_the_head_already_contains_is_refused(rig):
    rig.state["base_sha"] = rig.c0
    refused_before_anything(rig, rig.go())
    rig.assert_untouched()


def test_a_base_that_is_not_in_the_repository_is_refused(rig):
    rig.state["base_sha"] = "1" * 40
    refused_before_anything(rig, rig.go())
    rig.assert_untouched()


def test_an_absent_item_lock_is_refused(rig):
    (rig.run / "locks" / ("item." + ITEM) / "owner.json").unlink()
    (rig.run / "locks" / ("item." + ITEM)).rmdir()
    refused_before_anything(rig, rig.go())
    rig.assert_untouched()


def test_a_lock_of_another_item_is_not_this_items_lock(rig):
    (rig.run / "locks" / ("item." + ITEM)).rename(rig.run / "locks" / "item.FX-8")
    refused_before_anything(rig, rig.go())


def test_a_foreign_item_lock_is_refused(rig):
    """A live owner that is neither this process nor one of its ancestors."""
    child = subprocess.Popen(["/bin/sleep", "120"])
    rig.children.append(child)
    start = lstart(child.pid)
    assert start
    rig.lock(child.pid, start)
    refused_before_anything(rig, rig.go())
    rig.assert_untouched()


def test_an_item_lock_whose_owner_is_gone_is_refused(rig):
    child = subprocess.Popen(["/usr/bin/true"])
    start = lstart(child.pid) or "Mon Oct 12 00:00:00 2026"
    child.wait()
    rig.lock(child.pid, start)
    refused_before_anything(rig, rig.go())


@pytest.mark.parametrize("case", ["no_start", "no_pid", "another_start", "not_json", "not_an_object"])
def test_an_item_lock_that_cannot_be_judged_is_refused(rig, case):
    """Unknown refuses: an ancestor's pid alone is not a live owner (no start identity, or another one)."""
    owner = rig.run / "locks" / ("item." + ITEM) / "owner.json"
    if case == "no_start":
        rig.lock(os.getpid(), None)
    elif case == "no_pid":
        rig.lock(None, lstart(os.getpid()))
    elif case == "another_start":
        rig.lock(os.getpid(), "Thu Jan  1 00:00:00 1998")
    elif case == "not_json":
        owner.write_text("{")
    else:
        owner.write_text("[]")
    refused_before_anything(rig, rig.go())
    rig.assert_untouched()


# ───────────────────────────────────────── acceptance 6 ─────────────────────────────────────────

def test_a_rejected_push_is_never_reported_as_done(rig):
    elsewhere = rig.move_remote()
    r = rig.go()
    assert r.returncode == 6, r.stderr
    new = rig.head()
    assert new != rig.f1 and rig.remote_head() == elsewhere                      # the merge exists only locally
    push = rig.record(PUSH_ID)
    assert push["state"] == "FAILED" and push["result"]["observed"] == elsewhere and push["result"]["intended"] == new
    assert push["result"]["push_exit"] not in (0, None)
    assert rig.record(REVIEW_ID) is None and calls(rig.ky_calls) == []           # no `ky review`
    doc = rig.regen()
    assert (doc["pushed"], doc["review_registered"], doc["inheritance"]) == (False, None, None)
    assert doc["new_head"] == new and doc["old_head"] == rig.f1


def test_a_push_that_only_claims_success_is_not_pushed(rig):
    """Negative fixture for `pushed`: git push exits 0 but the remote never moved — the remote head decides."""
    (rig.tools / "git.mode").write_text("swallow-push\n")
    r = rig.go()
    assert r.returncode == 6, r.stderr
    assert rig.remote_head() == rig.f1
    push = rig.record(PUSH_ID)
    assert push["state"] == "FAILED" and push["result"]["push_exit"] == 0 and push["result"]["observed"] == rig.f1
    assert rig.regen()["pushed"] is False and calls(rig.ky_calls) == []


def test_a_remote_that_cannot_be_read_leaves_the_push_unknown(rig):
    (rig.tools / "git.mode").write_text("blind\n")
    r = rig.go()
    assert r.returncode == 6, r.stderr
    assert rig.record(PUSH_ID)["state"] == "INTENDED"                            # stays for the controller's reconciliation
    doc = rig.regen()
    assert doc["pushed"] is None and doc["review_registered"] is None
    assert calls(rig.ky_calls) == [] and rig.record(REVIEW_ID) is None
    assert rig.remote_head() == rig.head()                                       # (it was in fact pushed: unknown ≠ false)


def test_a_failed_registration_is_never_reported_as_done(rig):
    (rig.tools / "ky.exit").write_text("3")
    r = rig.go()
    assert r.returncode == 6, r.stderr
    new = rig.head()
    assert rig.remote_head() == new
    doc = rig.regen()
    assert (doc["pushed"], doc["review_registered"], doc["inheritance"]) == (True, False, None)
    assert rig.record(PUSH_ID)["state"] == "DONE"
    review = rig.record(REVIEW_ID)
    assert review["state"] == "FAILED" and review["result"]["exit"] == 3
    assert len(calls(rig.ky_calls)) == 1


def test_a_tracker_cli_that_cannot_be_run_is_not_a_registration(rig):
    r = rig.go(env=rig.env(KY_BIN=str(rig.tools / "no-such-ky")))
    assert r.returncode == 64, r.stderr                                          # refused before anything was merged
    rig.assert_untouched()


@pytest.mark.parametrize("which", ["push", "review"])
def test_an_existing_action_record_forbids_the_side_effect(rig, which):
    """kyaction `begin` exit 3 = the record exists: the side effect is not performed, the outcome is unknown."""
    rig.write_state()
    actor = {"role": "regen", "holder_kind": "job", "controller_id": "dispatcher-fixture", "run_id": RUN_ID}
    aid = PUSH_ID if which == "push" else REVIEW_ID
    kyaction.begin(rig.run, aid, "git_push" if which == "push" else "tracker_event", actor,
                   {"left": "by an earlier attempt"}, {}, "earlier")
    r = rig.go()
    assert r.returncode == 6, r.stderr
    doc = rig.regen()
    assert calls(rig.ky_calls) == []
    if which == "push":
        assert "push" not in rig.git_verbs() and rig.remote_head() == rig.f1
        assert (doc["pushed"], doc["review_registered"]) == (None, None)
    else:
        assert rig.remote_head() == rig.head()
        assert (doc["pushed"], doc["review_registered"]) == (True, None)
    assert rig.record(aid)["inputs"] == {"left": "by an earlier attempt"} and rig.record(aid)["state"] == "INTENDED"


@pytest.mark.parametrize("missing", ["KY_RUN_ID", "KY_ROLE", "KY_CONTROLLER_ID"])
def test_without_the_ids_of_its_action_records_nothing_is_merged(rig, missing):
    r = rig.go(env=rig.env(**{missing: None}))
    assert r.returncode == 64, r.stderr
    rig.assert_untouched()
    assert "merge" not in rig.git_verbs()


# ───────────────────────────────────────── acceptance 7 ─────────────────────────────────────────

def test_a_rerun_after_success_does_nothing(rig):
    assert rig.go().returncode == 0
    new, doc, raw = rig.head(), rig.regen(), rig.regen_json.read_bytes()
    records = {p.name: p.read_bytes() for p in (rig.run / "actions").iterdir()}
    rig.git_calls.unlink()
    r = rig.go()
    assert r.returncode == 0, r.stderr
    assert rig.git_argvs() == []                                                 # not one git command
    assert len(calls(rig.ky_calls)) == 1 and rig.ran.read_text().count("\n") == 1
    assert rig.head() == new and rig.remote_head() == new and rig.regen() == doc and rig.regen_json.read_bytes() == raw
    assert {p.name: p.read_bytes() for p in (rig.run / "actions").iterdir()} == records


def test_a_rerun_after_exit_6_stays_6_until_the_records_are_settled(rig):
    (rig.tools / "ky.exit").write_text("3")
    assert rig.go().returncode == 6
    new, raw = rig.head(), rig.regen_json.read_bytes()
    (rig.tools / "ky.exit").unlink()                                             # ky would succeed now: not retried
    rig.git_calls.unlink()
    r = rig.go()
    assert r.returncode == 6, r.stderr
    assert len(calls(rig.ky_calls)) == 1 and rig.git_argvs() == [] and rig.head() == new
    assert rig.regen_json.read_bytes() == raw and rig.record(REVIEW_ID)["state"] == "FAILED"
    # the controller settles the record (retry, then the observed result): the transition is done, nothing re-runs
    controller = {"role": "regen", "holder_kind": "controller", "controller_id": "dispatcher-fixture"}
    kyaction.retry(rig.run, REVIEW_ID)
    assert rig.go().returncode == 6                                              # reopened is not settled
    kyaction.complete(rig.run, REVIEW_ID, {"exit": 0, "settled_by": controller["controller_id"]})
    r = rig.go()
    assert r.returncode == 0, r.stderr
    assert len(calls(rig.ky_calls)) == 1 and rig.git_argvs() == [] and rig.regen_json.read_bytes() == raw


def test_a_rerun_after_a_rejected_push_never_pushes_again(rig):
    rig.move_remote()
    assert rig.go().returncode == 6
    rig.git_calls.unlink()
    assert rig.go().returncode == 6
    assert rig.git_argvs() == [] and calls(rig.ky_calls) == []


def test_an_unreadable_regen_record_is_never_a_fresh_start(rig):
    rig.regen_json.write_text("{")
    r = rig.go()
    assert r.returncode == 6, r.stderr
    assert rig.git_argvs() == [] and rig.head() == rig.f1 and rig.regen_json.read_text() == "{"


def test_a_regen_record_of_another_registered_head_does_not_stand_in(rig):
    """regen.json of an earlier head (same job id) says done; this registered head is still to be regenerated."""
    rig.regen_json.write_text(json.dumps({"schema": "ky.regen/1", "job_id": JOB, "old_head": rig.c0, "new_head": rig.f1,
                                          "pushed": True, "review_registered": True}))
    r = rig.go()
    assert r.returncode == 0, r.stderr
    assert rig.regen()["old_head"] == rig.f1 and rig.remote_head() == rig.head() != rig.f1


def test_a_termination_signal_while_the_generator_runs_restores_the_worktree(rig):
    rig.set_mode("hang")
    rig.write_state()
    p = subprocess.Popen([str(SCRIPT), JOB], env=rig.env(), cwd=str(rig.tmp), stdin=subprocess.DEVNULL,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    rig.children.append(p)                        # a process this test started itself
    deadline = time.time() + 60
    while not rig.ran.exists() and time.time() < deadline and p.poll() is None:
        time.sleep(0.05)
    assert rig.ran.exists() and p.poll() is None
    p.send_signal(signal.SIGTERM)
    _, err = p.communicate(timeout=60)
    assert p.returncode == 70, err
    rig.assert_untouched()


# ───────────────────────────────────────── usage and invalid state (64) ─────────────────────────────────────────

def test_usage(rig):
    rig.write_state()
    for argv in ([], [JOB, "extra"], ["../" + JOB], ["-h"], [""]):
        r = subprocess.run([str(SCRIPT)] + argv, env=rig.env(), capture_output=True, text=True, stdin=subprocess.DEVNULL)
        assert r.returncode == 64, (argv, r.stderr)
    assert rig.go("J-no-such-job", write=False).returncode == 64                 # no state.json
    rig.assert_untouched()
    assert rig.git_argvs() == []


def change(path, value):
    def apply(state):
        target = state
        for key in path[:-1]:
            target = target[key]
        if value is KeyError:
            del target[path[-1]]
        else:
            target[path[-1]] = value
    return apply


INVALID_STATES = [
    change(["kind"], "BUILD"), change(["kind"], KeyError), change(["item"], "../x"), change(["item"], 7),
    change(["stream"], ""), change(["slot"], None), change(["worktree"], "relative/wt"),
    change(["worktree"], "/nonexistent/kyregen/worktree"), change(["branch"], "-x"), change(["branch"], "a..b"),
    change(["branch"], "+" + BRANCH), change(["pr"], "41"), change(["pr"], 0), change(["pr"], True),
    change(["registered_head"], "abc123"), change(["base_sha"], "HEAD"), change(["base_sha"], "A" * 40),
    change(["queue_authorised"], "false"), change(["queue_authorised"], None), change(["queue_authorised"], KeyError),
    change(["regen"], KeyError), change(["regen", "outputs"], []), change(["regen", "outputs"], [OUT, OUT]),
    change(["regen", "outputs"], ["../outside.txt"]), change(["regen", "outputs"], ["/etc/hosts"]),
    change(["regen", "outputs"], ["gen/../gen/out.txt"]), change(["regen", "outputs"], [".git/config"]),
    change(["regen", "outputs"], ["gen/"]), change(["regen", "outputs"], [""]), change(["regen", "outputs"], OUT),
    change(["regen", "outputs"], ["gen"]),
    change(["regen", "generator", "argv"], []), change(["regen", "generator", "argv"], "gen.py"),
    change(["regen", "generator", "argv"], [PY, 3]), change(["regen", "generator", "path"], "tools/gen.py"),
    change(["regen", "generator", "sha256"], "ABC"), change(["regen", "generator", "sha256"], KeyError),
    change(["regen", "tests"], [[]]), change(["regen", "tests"], ["pytest"]), change(["regen", "tests"], KeyError),
    change(["job_id"], "J-another-job"),
]


def test_an_invalid_state_is_refused_before_anything(rig):
    valid = json.dumps(rig.state)
    for n, apply in enumerate(INVALID_STATES):
        rig.state = json.loads(valid)
        apply(rig.state)
        r = rig.go()
        assert r.returncode == 64, (n, json.dumps(rig.state), r.stderr)
        assert rig.git_verbs().count("merge") == 0 and not rig.ran.exists(), n
        rig.assert_untouched()
    rig.state = json.loads(valid)
    assert rig.go().returncode == 0                # … and the unchanged state is a valid one


def test_a_state_that_is_not_json_or_a_worktree_that_is_another_repository(rig, tmp_path):
    rig.state_json.write_text("{")
    refused_before_anything(rig, rig.go(write=False), code=64)
    sub = rig.wt / "gen"                           # a directory inside the repository is not the worktree itself
    rig.state["worktree"] = str(sub)
    refused_before_anything(rig, rig.go(), code=64)
    rig.assert_untouched()


@pytest.mark.parametrize("name,value", [("KY_RUN", None), ("KY_RUN", "relative/run"), ("KY_FLEET", None),
                                         ("KY_FLEET", "/nonexistent/fleet"), ("KY_RUN_ID", "bad id")])
def test_a_missing_or_malformed_environment_is_usage(rig, name, value):
    r = rig.go(env=rig.env(**{name: value}))
    assert r.returncode == 64, r.stderr
    assert rig.git_argvs() == [] and rig.head() == rig.f1 and not rig.regen_json.exists()


def test_the_tracker_cli_defaults_to_ky_root_bin_and_is_never_guessed(rig):
    """Without KY_BIN the CLI is $KY_ROOT/bin/ky; without KY_ROOT too there is no tracker CLI: refused (64)."""
    (rig.root / "bin").mkdir()
    (rig.root / "bin" / "ky").write_text((rig.tools / "ky").read_text())
    os.chmod(rig.root / "bin" / "ky", 0o755)
    r = rig.go(env=rig.env(KY_BIN=None, KY_ROOT=None))
    assert r.returncode == 64, r.stderr
    rig.assert_untouched()
    r = rig.go(env=rig.env(KY_BIN=None))
    assert r.returncode == 0, r.stderr
    assert calls(rig.root / "bin" / "ky.calls")[0]["argv"][:2] == ["review", ITEM] and calls(rig.ky_calls) == []
