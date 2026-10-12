"""kyverdicts.py — controller-owned verdict publication and the shared reviewed-patch inheritance predicate
(relaunch plan v2.7 §6 "Verdict publication" and "Inheritance predicate", §4a.1 "Action records"; KU-01's
"invalid inheritance fails" fixture; packet KV3-B-KYVERDICTS).

Everything runs against throwaway Git repositories and a fake `ky` written under pytest's temporary directory.
The real `ky`, the real tracker and /Users/Dev/kalayantra are never touched: an autouse fixture points KY_ROOT,
KY_RUN and KY_BIN at a guard directory, and every call below passes its own environment.

  Contract A (the predicate)   test_predicate_* · test_inherits_* · test_import_*
  Contract B (the verbs)       test_snapshot_* · test_publish_* · test_invalidate_* · test_inherit_cli_* · test_usage_*

A refused publication runs no `ky` command: every refusal test asserts that the fake `ky` was never started.
"""
import hashlib
import io
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
FLEET = HERE.parent
sys.path.insert(0, str(FLEET))

import kyaction  # noqa: E402
import kyverdicts as K  # noqa: E402

PY = sys.executable
DEFAULT_GIT = "/usr/bin/git"
# /usr/bin/git on macOS is a launcher that looks its tool up on every call; the fixtures (and, through KY_GIT, the
# component) use the program it launches where that is installed. The component's own default is tested as such.
GIT = next((p for p in ("/Library/Developer/CommandLineTools/usr/bin/git",) if os.access(p, os.X_OK)), DEFAULT_GIT)
SCHEMAS = FLEET / "schemas"
JOB = "J-20261012T090155Z-v1"
ITEM = "N-467"
VSLOT = "v1"
CID = "controller-test-1"
OUT_KEYS = {"published", "result", "reasons", "action_id"}
# what the fake ky may find in its environment: the allow-list, plus what the interpreter adds for itself on macOS
KY_ENV_ALLOWED = {"PATH", "HOME", "USER", "LANG", "TMPDIR", "KY_ROOT", "KY_RUN", "KY_STREAM", "KY_LANE",
                  "__CF_USER_TEXT_ENCODING", "LC_CTYPE"}

FAKE_KY = r'''#!%(py)s
"""fake ky: records the call, then behaves as the file `mode` beside it says (default: append the verdict event)."""
import json, os, subprocess, sys, time
here = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[1:]
def setting(name, default=None):
    try:
        with open(os.path.join(here, name), encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return default
mode = setting("mode", "ok")
with open(os.path.join(here, "calls.jsonl"), "a", encoding="utf-8") as f:
    f.write(json.dumps({"argv": argv, "env_names": sorted(os.environ), "KY_STREAM": os.environ.get("KY_STREAM"),
                        "KY_LANE": os.environ.get("KY_LANE")}) + "\n")
if mode == "refuse" or not argv or argv[0] != "verdict":
    print("refused: fake ky refuses", file=sys.stderr)
    sys.exit(2)
if mode == "hang":
    limit = time.time() + 30
    while time.time() < limit and not os.path.exists(os.path.join(here, "release")):
        time.sleep(0.05)
opts, rest, i = {}, argv[2:], 0
while i < len(rest):
    opts[rest[i]] = rest[i + 1]
    i += 2
event = {"kind": "verdict", "actor": "stream-%%s:%%s" %% (os.environ.get("KY_STREAM"), os.environ.get("KY_LANE")),
         "item": argv[1], "head": opts.get("--head"), "artifact_digest": opts.get("--artifact-digest"),
         "phase": opts.get("--phase", "pre_merge"), "result": opts.get("--result"), "detail": opts.get("--detail")}
if opts.get("--external-review-path") or opts.get("--external-review-sha256"):
    event["external_review"] = {"path": opts.get("--external-review-path"),
                                "sha256": opts.get("--external-review-sha256")}
event = {k: v for k, v in event.items() if v not in (None, "")}
if mode != "silent":
    with open(setting("events_path"), "a", encoding="utf-8") as f:
        f.write(json.dumps(event, separators=(",", ":")) + "\n")
if mode == "kill_parent":
    parent = os.getppid()
    who = subprocess.run(["/bin/ps", "-o", "command=", "-p", str(parent)], capture_output=True, text=True).stdout
    if "kyverdicts.py" in who:          # only ever the kyverdicts process this very test started
        os.kill(parent, 9)
    sys.exit(0)
if mode == "fail_after_append":
    sys.exit(3)
print(json.dumps(event))
'''


# ───────────────────────────────────────── helpers ─────────────────────────────────────────

@pytest.fixture(autouse=True)
def guard(tmp_path, monkeypatch):
    """Nothing here may reach the installed campaign: the process environment names a guard directory only."""
    root = tmp_path / "guard"
    (root / "run").mkdir(parents=True)
    monkeypatch.setenv("KY_ROOT", str(root))
    monkeypatch.setenv("KY_RUN", str(root / "run"))
    monkeypatch.setenv("KY_BIN", str(root / "bin" / "ky"))
    monkeypatch.setenv("KY_GIT", GIT)
    for name in [n for n in os.environ if n.startswith("GIT_")]:
        monkeypatch.delenv(name)
    assert "/Users/Dev/kalayantra" not in str(tmp_path)
    return root


def git(repo, *args, check=True, stdin=None):
    env = {"PATH": "/usr/bin:/bin", "HOME": str(repo), "LC_ALL": "C", "GIT_CONFIG_NOSYSTEM": "1",
           "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid",
           "GIT_AUTHOR_DATE": "2026-10-12T00:00:00Z", "GIT_COMMITTER_DATE": "2026-10-12T00:00:00Z"}
    r = subprocess.run([GIT, *args], cwd=str(repo), env=env, capture_output=True, text=True, input=stdin)
    if check:
        assert r.returncode == 0, "git %s: %s%s" % (" ".join(args), r.stdout, r.stderr)
    return r.stdout.strip() if check else r


def lines(prefix, changes=None, n=30):
    rows = ["%s%02d" % (prefix, i) for i in range(1, n + 1)]
    for number, text in (changes or {}).items():
        rows[number - 1] = text
    return "\n".join(rows) + "\n"


def commit(repo, message, files=None, raw=None):
    for name, text in (files or {}).items():
        (repo / name).write_text(text, encoding="utf-8")
    for name, data in (raw or {}).items():
        (repo / name).write_bytes(data)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "--allow-empty", "-m", message)
    return git(repo, "rev-parse", "HEAD")


class Scenario:
    """main: base B1 → M2 (b.txt line 20). feat: B1 → OLD (a.txt line 10). Each test derives its new head."""

    def __init__(self, tmp_path, main_branch="main", main_change=None, old_raw=None):
        self.repo = tmp_path / "repo"
        self.repo.mkdir()
        self.main = main_branch
        git(self.repo, "init", "-q", "-b", main_branch)
        self.b1 = commit(self.repo, "base", {"a.txt": lines("a"), "b.txt": lines("b")})
        git(self.repo, "checkout", "-q", "-b", "feat")
        self.old = commit(self.repo, "feature", {"a.txt": lines("a", {10: "a10 feature"})}, raw=old_raw)
        git(self.repo, "checkout", "-q", main_branch)
        self.m2 = commit(self.repo, "main moves", main_change or {"b.txt": lines("b", {20: "b20 main"})})
        git(self.repo, "checkout", "-q", "feat")

    def merge_main(self):
        git(self.repo, "merge", "-q", "--no-ff", "--no-edit", self.main)
        return git(self.repo, "rev-parse", "HEAD")

    def check(self, new, **kw):
        return K.inheritance(str(self.repo), self.old, new, **kw)


def refused(result, reason):
    """The one assertion every negative predicate case goes through."""
    assert result["inherits"] is False, result
    assert result["reason"] == reason, result


def read_events(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def tokens(out):
    return [str(reason).split(":")[0] for reason in out["reasons"]]


class World:
    """One VERIFY job that has just exited: worktree, pre-job snapshot, job result, boundary evidence, fake ky."""

    def __init__(self, tmp_path, snapshot=True):
        self.root = tmp_path / "world"
        self.run_dir = self.root / "kyroot" / "run"
        self.run_dir.mkdir(parents=True)
        self.events = self.run_dir / "EVENTS.jsonl"
        self.events.write_text("", encoding="utf-8")
        self.bin = self.root / "kyroot" / "bin"
        self.bin.mkdir()
        self.ky = self.bin / "ky"
        self.ky.write_text(FAKE_KY % {"py": PY}, encoding="utf-8")
        self.ky.chmod(0o755)
        (self.bin / "events_path").write_text(str(self.events), encoding="utf-8")
        (self.root / "home").mkdir()
        self.env = {"KY_RUN": str(self.run_dir), "KY_ROOT": str(self.root / "kyroot"), "KY_BIN": str(self.ky),
                    "KY_GIT": GIT, "HOME": str(self.root / "home"), "PATH": "/usr/bin:/bin",
                    "KY_CANARY_NOT_ALLOWED": "must-not-reach-ky", "GIT_DIR": "/nonexistent"}
        self.wt = self.root / "wt"
        self.wt.mkdir()
        git(self.wt, "init", "-q", "-b", "main")
        self.head = commit(self.wt, "reviewed", {"code.py": "print('reviewed')\n", "doc.md": "doc\n"})
        self.scratch = self.root / "job"
        self.scratch.mkdir()
        self.snap = self.scratch / "snapshot.json"
        self.result = self.scratch / "result.json"
        self.boundary = self.scratch / "boundary.check.json"
        self.artifact = self.scratch / "artifact.md"
        self.artifact.write_text("the reviewed artifact\n", encoding="utf-8")
        self.digest = hashlib.sha256(self.artifact.read_bytes()).hexdigest()
        self.write_result()
        self.write_boundary()
        if snapshot:
            code, out = self.call(["snapshot", "--worktree", str(self.wt), "--out", str(self.snap)])
            assert code == 0, out

    def mode(self, name):
        (self.bin / "mode").write_text(name, encoding="utf-8")

    def write_result(self, verdict=..., **changes):
        doc = {"schema": "ky.job_result/1", "job_id": JOB, "item": ITEM, "status": "done", "branch": None,
               "head_sha": None, "pr_number": None,
               "tests": [{"cmd": "python3 -m pytest x -q", "exit": 0, "summary": "3 passed (independent run)"}],
               "blocked_reason": None, "notes": "review of the PR head; nothing pushed",
               "proposed_verdict": {"verdict": "ACCEPTED", "phase": "pre_merge", "head": self.head,
                                    "summary": "diff matches the packet; 3 tests re-run green"}}
        if verdict is None:
            del doc["proposed_verdict"]
        elif verdict is not ...:
            doc["proposed_verdict"] = verdict
        doc.update(changes)
        self.result.write_text(json.dumps(doc, indent=1), encoding="utf-8")
        return doc

    def write_boundary(self, **changes):
        doc = {"job_id": JOB, "mechanism": "read-only image", "head_unchanged": True, "status_clean": True,
               "tracked_hashes_unchanged": True, "mechanism_intact": True, "result": "intact"}
        doc.update(changes)
        self.boundary.write_text(json.dumps(doc), encoding="utf-8")

    def publish_argv(self, **over):
        a = {"--job-id": JOB, "--item": ITEM, "--phase": "pre_merge", "--head": self.head, "--vslot": VSLOT,
             "--author-id": "builder-opus-b2", "--reviewer-id": "verifier-opus-v1", "--worktree": str(self.wt),
             "--snapshot": str(self.snap), "--job-exit": "0", "--result": str(self.result),
             "--boundary": str(self.boundary), "--as": CID}
        a.update(over)
        argv = ["publish"]
        for flag, value in a.items():
            if value is not None:
                argv += [flag, str(value)]
        return argv

    def artifact_argv(self, **over):
        over = dict({"--phase": "artifact", "--head": None, "--artifact-digest": self.digest,
                     "--artifact-path": str(self.artifact)}, **over)
        return self.publish_argv(**over)

    def invalidate_argv(self, **over):
        a = {"--item": ITEM, "--phase": "pre_merge", "--head": self.head, "--vslot": VSLOT,
             "--reason": "required check went red after acceptance", "--as": CID}
        a.update(over)
        argv = ["invalidate"]
        for flag, value in a.items():
            if value is not None:
                argv += [flag, str(value)]
        return argv

    def call(self, argv, env=None):
        buffer = io.StringIO()
        code = K.main(list(argv), environ=dict(self.env if env is None else env), stdout=buffer)
        text = buffer.getvalue()
        assert text.count("\n") == 1, "stdout must be exactly one JSON line: %r" % text
        return code, json.loads(text)

    def publish(self, **over):
        return self.call(self.publish_argv(**over))

    def calls(self):
        path = self.bin / "calls.jsonl"
        return read_events(path) if path.exists() else []

    def verdicts(self):
        return [e for e in read_events(self.events) if e.get("kind") == "verdict"]

    def record(self, action_id="VERDICT-" + JOB):
        return kyaction.peek(self.run_dir, action_id)

    def seed(self, result, head=..., detail="job J-OTHER; seeded", **more):
        event = dict({"kind": "verdict", "actor": "stream-V:v2", "item": ITEM,
                      "head": self.head if head is ... else head,
                      "phase": "pre_merge", "result": result, "detail": detail}, **more)
        event = {k: v for k, v in event.items() if v is not None}
        with open(self.events, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")
        return event

    def nothing_published(self):
        assert self.calls() == [], "a refused publication ran ky"
        assert self.verdicts() == []


@pytest.fixture
def world(tmp_path):
    return World(tmp_path)


@pytest.fixture
def scenario(tmp_path):
    return Scenario(tmp_path)


class Crash(BaseException):
    """Stands in for the process dying: nothing between the raise and the test catches or cleans up."""


# ───────────────────────────────── Contract A: the inheritance predicate ─────────────────────────────────

def test_predicate_true_for_a_conflict_free_merge_of_main(scenario):
    new = scenario.merge_main()
    result = scenario.check(new)
    assert result == {"inherits": True, "reason": "identical_patch", "old_head": scenario.old, "new_head": new,
                      "old_base": scenario.b1, "new_base": scenario.m2}
    assert K.inherits(str(scenario.repo), scenario.old, new) is True


def test_predicate_true_when_main_changed_the_same_file_elsewhere(tmp_path):
    """Blob ids and hunk positions move with main; the reviewed patch does not. This is what dropping the `index`
    lines and the `@@` headers is for (the next test shows that nothing else is dropped)."""
    moved = "top1\ntop2\n" + lines("a", {28: "a28 main"})
    s = Scenario(tmp_path, main_change={"a.txt": moved})
    new = s.merge_main()
    flags = ["diff", "--no-color", "--no-ext-diff", "--no-textconv", "--no-renames"]
    old_patch, new_patch = git(s.repo, *flags, s.b1, s.old), git(s.repo, *flags, s.m2, new)
    differing = {a[:2] for a, b in zip(old_patch.splitlines(), new_patch.splitlines()) if a != b}
    assert differing == {"in", "@@"}, "the fixture's two patches differ in their index and @@ lines, and only there"
    result = s.check(new)
    assert result["inherits"] is True and result["reason"] == "identical_patch"


def test_predicate_false_when_main_changed_the_context_of_the_reviewed_hunk(tmp_path):
    s = Scenario(tmp_path, main_change={"a.txt": lines("a", {13: "a13 main"})})    # within three lines of line 10
    new = s.merge_main()                            # git merges it without a conflict
    assert (s.repo / "a.txt").read_text(encoding="utf-8") == lines("a", {10: "a10 feature", 13: "a13 main"})
    refused(s.check(new), "patch_differs")          # unproven: the lines around the change are not the reviewed ones


def test_predicate_true_with_the_exact_bases_given(scenario):
    new = scenario.merge_main()
    result = scenario.check(new, old_base=scenario.b1, new_base=scenario.m2)
    assert result["inherits"] is True and result["reason"] == "identical_patch"


def test_predicate_uses_origin_main_when_there_is_one(scenario):
    new = scenario.merge_main()
    git(scenario.repo, "update-ref", "refs/remotes/origin/main", scenario.m2)
    git(scenario.repo, "branch", "-q", "-D", "main")
    assert scenario.check(new)["inherits"] is True
    # and origin/main wins over a local main that says something else
    git(scenario.repo, "update-ref", "refs/heads/main", scenario.b1)
    result = scenario.check(new)
    assert result["inherits"] is True and result["new_base"] == scenario.m2


def test_predicate_false_for_a_substantive_conflict_resolution(tmp_path):
    s = Scenario(tmp_path, main_change={"a.txt": lines("a", {10: "a10 main"})})
    merge = git(s.repo, "merge", "--no-ff", "--no-edit", "main", check=False)
    assert merge.returncode != 0, "the fixture needs a real conflict"
    new = commit(s.repo, "merge main, resolved by hand", {"a.txt": lines("a", {10: "a10 resolved by hand"})})
    assert git(s.repo, "rev-list", "--no-merges", "%s..%s" % (s.old, new), "^main") == "", \
        "the fixture is merge-only: ancestry alone would have inherited (the legacy merge_only_between rule)"
    refused(s.check(new), "patch_differs")
    assert K.inherits(str(s.repo), s.old, new) is False


def test_predicate_false_when_a_conflict_is_resolved_to_the_branch_side(tmp_path):
    s = Scenario(tmp_path, main_change={"a.txt": lines("a", {10: "a10 main"})})
    git(s.repo, "merge", "--no-ff", "--no-edit", "main", check=False)
    new = commit(s.repo, "merge main, ours", {"a.txt": lines("a", {10: "a10 feature"})})
    refused(s.check(new), "patch_differs")          # an unproven difference: the new head is reviewed


def test_predicate_false_for_a_conflict_free_merge_that_carries_an_extra_change(scenario):
    git(scenario.repo, "merge", "-q", "--no-ff", "--no-commit", "main")
    new = commit(scenario.repo, "evil merge", {"b.txt": lines("b", {20: "b20 main", 5: "b05 slipped in"})})
    assert len(git(scenario.repo, "rev-list", "--parents", "-n", "1", new).split()) == 3
    refused(scenario.check(new), "patch_differs")


def test_predicate_false_for_one_added_commit(scenario):
    scenario.merge_main()
    new = commit(scenario.repo, "one more", {"c.txt": "new file\n"})
    refused(scenario.check(new), "patch_differs")


def test_predicate_false_for_ancestry_alone(scenario):
    new = commit(scenario.repo, "descendant, no merge", {"a.txt": lines("a", {10: "a10 feature", 11: "a11 too"})})
    assert git(scenario.repo, "merge-base", "--is-ancestor", scenario.old, new, check=False).returncode == 0
    refused(scenario.check(new), "patch_differs")


def test_predicate_false_once_the_heads_landed_by_a_merge_commit(scenario):
    """Review B-01 (a): once main contains a head, its derived base IS that head and both patches are empty —
    an empty comparison proves nothing, so the unreviewed added commit does not inherit."""
    new = commit(scenario.repo, "one more, unreviewed", {"c.txt": "unreviewed\n"})
    refused(scenario.check(new), "patch_differs")                   # before landing
    git(scenario.repo, "checkout", "-q", "main")
    git(scenario.repo, "merge", "-q", "--no-ff", "--no-edit", "feat")
    result = scenario.check(new)
    refused(result, "unproven_base")
    assert result["old_base"] == scenario.old and result["new_base"] == new
    assert K.inherits(str(scenario.repo), scenario.old, new) is False


def test_predicate_false_once_the_heads_landed_by_a_fast_forward(scenario):
    merged = scenario.merge_main()
    new = commit(scenario.repo, "one more, unreviewed", {"c.txt": "unreviewed\n"})
    git(scenario.repo, "checkout", "-q", "main")
    git(scenario.repo, "merge", "-q", "--ff-only", "feat")
    assert git(scenario.repo, "rev-parse", "main") == new
    refused(scenario.check(new), "unproven_base")
    refused(scenario.check(merged), "unproven_base")                # even the merge of main: nothing is compared
    assert K.inherits(str(scenario.repo), scenario.old, new) is False


def test_predicate_false_for_a_later_main_commit_after_the_old_head_landed(scenario):
    git(scenario.repo, "checkout", "-q", "main")
    git(scenario.repo, "merge", "-q", "--no-ff", "--no-edit", "feat")
    later = commit(scenario.repo, "unrelated, unreviewed work on main", {"d.txt": "unreviewed\n"})
    result = scenario.check(later)
    refused(result, "unproven_base")
    assert result["old_base"] == scenario.old
    assert K.inherits(str(scenario.repo), scenario.old, later) is False


def test_predicate_false_for_a_given_base_equal_to_its_head_or_an_empty_reviewed_patch(scenario):
    new = scenario.merge_main()
    refused(scenario.check(new, old_base=scenario.old, new_base=new), "unproven_base")
    refused(scenario.check(new, old_base=scenario.b1, new_base=new), "unproven_base")
    refused(scenario.check(new, old_base=scenario.old, new_base=scenario.m2), "unproven_base")
    # base ≠ head, and still nothing reviewed: two empty commits compare equal, and prove nothing
    empty_old = commit(scenario.repo, "empty, reviewed")
    empty_new = commit(scenario.repo, "empty, not reviewed")
    refused(K.inheritance(str(scenario.repo), empty_old, empty_new, old_base=new, new_base=empty_old),
            "unproven_base")


def test_predicate_same_head_is_decided_by_the_same_rules(scenario):
    """old_head == new_head gets no shortcut: it inherits with a real, non-empty patch over a proper base, and is
    refused like any other head once its base degenerates."""
    result = scenario.check(scenario.old)
    assert result["inherits"] is True and result["reason"] == "identical_patch" and result["old_base"] == scenario.b1
    git(scenario.repo, "checkout", "-q", "main")
    git(scenario.repo, "merge", "-q", "--no-ff", "--no-edit", "feat")
    refused(scenario.check(scenario.old), "unproven_base")


STANZA = ["# section %d", "alpha", "beta", "gamma", "enabled = false", "delta", "epsilon", "zeta", ""]


def stanzas(enabled=()):
    rows = []
    for number in (1, 2, 3):
        block = [row % number if "%d" in row else row for row in STANZA]
        if number in enabled:
            block[4] = "enabled = true"
        rows += block
    return "\n".join(rows) + "\n"


def test_predicate_false_when_an_added_commit_moves_the_change_to_identical_context(tmp_path):
    """Review B-02: three stanzas whose lines around the flag are identical. OLD turns stanza 1 on; one added
    commit turns stanza 1 back off and stanza 3 on. With the @@ headers dropped both patches read alike — the
    change is bound to WHERE it applies by the three-way check, and refused."""
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    base = commit(repo, "base", {"conf.ini": stanzas()})
    git(repo, "checkout", "-q", "-b", "feat")
    old = commit(repo, "turn stanza 1 on", {"conf.ini": stanzas(enabled=(1,))})
    new = commit(repo, "move it to stanza 3", {"conf.ini": stanzas(enabled=(3,))})
    flags = ["diff", "--no-color", "--no-ext-diff", "--no-textconv", "--no-renames"]
    strip = lambda text: [x for x in text.splitlines() if not x.startswith(("index ", "@@"))]  # noqa: E731
    assert strip(git(repo, *flags, base, old)) == strip(git(repo, *flags, base, new)), \
        "the fixture's stripped patches are identical"
    result = K.inheritance(str(repo), old, new)
    refused(result, "patch_differs")
    assert result["old_base"] == base and result["new_base"] == base
    assert K.inherits(str(repo), old, new) is False


def test_predicate_true_when_main_shifts_a_change_among_identical_stanzas(tmp_path):
    """Binding the position must still tolerate the line shift main causes: main inserts a stanza above."""
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    commit(repo, "base", {"conf.ini": stanzas()})
    git(repo, "checkout", "-q", "-b", "feat")
    old = commit(repo, "turn stanza 2 on", {"conf.ini": stanzas(enabled=(2,))})
    git(repo, "checkout", "-q", "main")
    commit(repo, "main adds a preamble", {"conf.ini": "; preamble\n; two\n\n" + stanzas()})
    git(repo, "checkout", "-q", "feat")
    git(repo, "merge", "-q", "--no-ff", "--no-edit", "main")
    new = git(repo, "rev-parse", "HEAD")
    result = K.inheritance(str(repo), old, new)
    assert result["inherits"] is True and result["reason"] == "identical_patch", result


def test_predicate_false_for_an_indentation_only_change(scenario):
    merged = scenario.merge_main()
    new = commit(scenario.repo, "indent", {"a.txt": lines("a", {10: "    a10 feature"})})
    assert git(scenario.repo, "diff", "-w", merged, new) == "", "the fixture differs in white space only"
    assert git(scenario.repo, "diff", "--stat", merged, new) != ""
    refused(scenario.check(new), "patch_differs")


def test_predicate_false_for_a_rebased_identical_patch(scenario):
    git(scenario.repo, "checkout", "-q", "-b", "rebased", scenario.m2)
    git(scenario.repo, "cherry-pick", scenario.old)
    new = git(scenario.repo, "rev-parse", "HEAD")
    flags = ["diff", "--no-color", "--no-ext-diff", "--no-textconv", "--no-renames"]
    strip = lambda text: [x for x in text.splitlines() if not x.startswith(("index ", "@@"))]  # noqa: E731
    assert strip(git(scenario.repo, *flags, scenario.b1, scenario.old)) == \
        strip(git(scenario.repo, *flags, scenario.m2, new)), "the fixture's patch is identical"
    refused(scenario.check(new), "not_descendant")   # the equal patch does not replace descent


@pytest.mark.parametrize("which", ["old", "new"])
@pytest.mark.parametrize("bad", ["f" * 40, "abc1234", "", "HEAD", "main", None, 7, "F" * 40])
def test_predicate_false_for_an_unknown_commit(scenario, which, bad):
    new = scenario.merge_main()
    args = (bad, new) if which == "old" else (scenario.old, bad)
    result = K.inheritance(str(scenario.repo), *args)
    refused(result, "unknown_commit")
    assert K.inherits(str(scenario.repo), *args) is False


def test_predicate_false_for_a_tree_or_blob_in_place_of_a_commit(scenario):
    new = scenario.merge_main()
    tree = git(scenario.repo, "rev-parse", new + "^{tree}")
    refused(scenario.check(tree), "unknown_commit")
    refused(scenario.check(new, new_base=tree), "unknown_commit")
    refused(scenario.check(new, old_base="e" * 40), "unknown_commit")
    refused(scenario.check(new, old_base="not-a-sha"), "unknown_commit")


def test_predicate_false_without_a_main_ref(tmp_path):
    s = Scenario(tmp_path, main_branch="trunk")
    new = s.merge_main()
    refused(s.check(new), "unproven_base")
    assert s.check(new)["old_base"] is None and s.check(new)["new_base"] is None
    # the very same commits inherit once their exact bases are bound: it was the base that was unproven
    assert s.check(new, old_base=s.b1, new_base=s.m2)["inherits"] is True
    refused(s.check(new, old_base=s.b1), "unproven_base")


def test_predicate_false_when_the_base_is_ambiguous(scenario):
    git(scenario.repo, "checkout", "-q", "main")
    git(scenario.repo, "merge", "-q", "--no-ff", "--no-edit", "feat")       # main takes the old head …
    git(scenario.repo, "checkout", "-q", "feat")
    git(scenario.repo, "merge", "-q", "--no-ff", "--no-edit", scenario.m2)  # … and feat takes the old main
    new = git(scenario.repo, "rev-parse", "HEAD")
    assert len(git(scenario.repo, "merge-base", "--all", "main", new).split()) == 2
    refused(scenario.check(new), "unproven_base")


def test_predicate_false_when_a_base_is_not_an_ancestor_of_its_head(scenario):
    new = scenario.merge_main()
    refused(scenario.check(new, old_base=scenario.m2, new_base=scenario.m2), "base_not_ancestor")
    refused(scenario.check(new, old_base=scenario.b1, new_base=new + ""), "unproven_base")    # review B-01
    stray = git(scenario.repo, "commit-tree", new + "^{tree}", "-m", "unrelated root")
    refused(scenario.check(new, old_base=scenario.b1, new_base=stray), "base_not_ancestor")


def test_predicate_false_for_a_binary_change(tmp_path):
    s = Scenario(tmp_path, old_raw={"blob.bin": b"\x00\x01\x02\xff" * 64})
    new = s.merge_main()
    refused(s.check(new), "binary_change")           # "Binary files differ" proves nothing about their content
    assert K.inherits(str(s.repo), s.old, new) is False


def test_predicate_false_when_git_times_out(scenario, tmp_path, monkeypatch):
    new = scenario.merge_main()
    slow = tmp_path / "slow_git"
    slow.write_text("#!/bin/sh\n/bin/sleep 30\n", encoding="utf-8")
    slow.chmod(0o755)
    monkeypatch.setenv("KY_GIT", str(slow))
    started = time.monotonic()
    refused(scenario.check(new, timeout=1), "git_failed")
    assert time.monotonic() - started < 15, "the timeout must end the comparison, not the sleep"


def test_predicate_signatures_are_the_contract():
    import inspect
    assert inspect.signature(K.inheritance).parameters["timeout"].default == 60
    assert list(inspect.signature(K.inherits).parameters) == ["repo", "old_head", "new_head"]


@pytest.mark.parametrize("script", ["#!/bin/sh\nexit 0\n", "#!/bin/sh\nexit 1\n", "#!/bin/sh\nexit 128\n"])
def test_predicate_false_when_git_answers_nothing_useful(scenario, tmp_path, monkeypatch, script):
    """Nothing is True by default: a git that exits 0, 1 or 128 without an answer proves no patch."""
    new = scenario.merge_main()
    stub = tmp_path / "stub_git"
    stub.write_text(script, encoding="utf-8")
    stub.chmod(0o755)
    monkeypatch.setenv("KY_GIT", str(stub))
    result = scenario.check(new)
    assert result["inherits"] is False and result["reason"] in K.REFUSALS


@pytest.mark.parametrize("program", ["/nonexistent/git", "git", ""])
def test_predicate_false_when_git_cannot_be_run(scenario, monkeypatch, program):
    new = scenario.merge_main()
    monkeypatch.setenv("KY_GIT", program)
    if program:
        refused(scenario.check(new), "git_failed")
    else:                                           # unset or empty: the default /usr/bin/git
        assert K.DEFAULT_GIT == DEFAULT_GIT and scenario.check(new)["inherits"] is True
        monkeypatch.delenv("KY_GIT")
        assert scenario.check(new)["inherits"] is True


@pytest.mark.parametrize("repo", [None, 7, "", "/nonexistent/repo", b"bytes"])
def test_predicate_never_raises_and_is_false_without_a_repository(scenario, repo):
    new = scenario.merge_main()
    refused(K.inheritance(repo, scenario.old, new), "git_failed")
    assert K.inherits(repo, scenario.old, new) is False


def test_predicate_false_outside_a_repository_and_for_a_bad_timeout(scenario, tmp_path):
    new = scenario.merge_main()
    plain = tmp_path / "plain"
    plain.mkdir()
    refused(K.inheritance(str(plain), scenario.old, new), "git_failed")
    for timeout in (0, -1, None, "soon"):
        refused(scenario.check(new, timeout=timeout), "git_failed")


def test_forcing_the_comparison_equal_fails_a_test(tmp_path, monkeypatch):
    """The mutation check the packet asks for: with the byte comparison forced equal, a negative case above no
    longer holds — so it is that comparison that refuses a changed patch. (Main changing the context of the
    reviewed hunk merges cleanly, so the three-way check beside it does not see it.)"""
    s = Scenario(tmp_path, main_change={"a.txt": lines("a", {13: "a13 main"})})
    new = s.merge_main()
    refused(s.check(new), "patch_differs")
    monkeypatch.setattr(K, "_same_patch", lambda old, new: True)
    with pytest.raises(AssertionError):
        refused(s.check(new), "patch_differs")
    assert s.check(new)["inherits"] is True          # the mutant inherits: the detector is the comparison


def test_forcing_the_position_check_equal_fails_a_test(tmp_path, monkeypatch):
    """The same mutation check for the three-way position check (review B-02): forced equal, the relocation
    fixture inherits."""
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    commit(repo, "base", {"conf.ini": stanzas()})
    git(repo, "checkout", "-q", "-b", "feat")
    old = commit(repo, "turn stanza 1 on", {"conf.ini": stanzas(enabled=(1,))})
    new = commit(repo, "move it to stanza 3", {"conf.ini": stanzas(enabled=(3,))})
    refused(K.inheritance(str(repo), old, new), "patch_differs")
    monkeypatch.setattr(K, "_same_tree", lambda reviewed, observed: True)
    assert K.inheritance(str(repo), old, new)["inherits"] is True


def test_inherits_is_fail_closed_on_any_internal_error(scenario, monkeypatch):
    new = scenario.merge_main()
    assert K.inherits(str(scenario.repo), scenario.old, new) is True

    def boom(*a, **k):
        raise RuntimeError("unexpected")
    monkeypatch.setattr(K, "_compare", boom)
    refused(scenario.check(new), "git_failed")
    assert K.inherits(str(scenario.repo), scenario.old, new) is False
    monkeypatch.setattr(K, "inheritance", lambda *a, **k: {"inherits": 1, "reason": "identical_patch"})
    assert K.inherits(str(scenario.repo), scenario.old, new) is False     # `is True`, not truthiness
    monkeypatch.setattr(K, "inheritance", boom)
    assert K.inherits(str(scenario.repo), scenario.old, new) is False


def test_predicate_ignores_git_variables_of_the_caller(scenario, monkeypatch):
    new = scenario.merge_main()
    monkeypatch.setenv("GIT_DIR", "/nonexistent/.git")
    monkeypatch.setenv("GIT_EXTERNAL_DIFF", "/usr/bin/true")
    assert scenario.check(new)["inherits"] is True


def test_import_runs_nothing(tmp_path):
    """Importing kyverdicts starts no process, reads no environment-named program and writes no file."""
    canary = tmp_path / "canary"
    marker = tmp_path / "ran"
    canary.write_text("#!/bin/sh\n/usr/bin/touch %s\n" % marker, encoding="utf-8")
    canary.chmod(0o755)
    cwd = tmp_path / "cwd"
    cwd.mkdir()
    code = ("import sys; sys.path.insert(0, sys.argv[1]); import kyverdicts; "
            "print([m for m in ('kyaction',) if m in sys.modules]); print(callable(kyverdicts.inherits))")
    r = subprocess.run([PY, "-B", "-c", code, str(FLEET)], cwd=str(cwd), capture_output=True, text=True,
                       env={"PATH": "/usr/bin:/bin", "KY_GIT": str(canary), "KY_BIN": str(canary),
                            "KY_RUN": str(tmp_path / "no-run"), "KY_ROOT": str(tmp_path / "no-root")})
    assert r.returncode == 0, r.stderr
    assert r.stdout.splitlines() == ["[]", "True"] and r.stderr == ""
    assert not marker.exists() and list(cwd.iterdir()) == [] and not (tmp_path / "no-run").exists()


def test_module_uses_the_standard_library_only():
    import ast
    tree = ast.parse((FLEET / "kyverdicts.py").read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.add((node.module or "").split(".")[0])
    if not hasattr(sys, "stdlib_module_names"):
        pytest.skip("sys.stdlib_module_names needs Python 3.10")
    assert names <= set(sys.stdlib_module_names) | {"__future__"}, names


# ───────────────────────────────────── Contract B: snapshot ─────────────────────────────────────

def test_snapshot_records_head_status_and_the_tracked_hash(tmp_path):
    w = World(tmp_path, snapshot=False)
    code, out = w.call(["snapshot", "--worktree", str(w.wt), "--out", str(w.snap)])
    assert code == 0 and set(out) == OUT_KEYS and out["published"] is False and out["action_id"] is None
    snap = json.loads(w.snap.read_text(encoding="utf-8"))
    assert snap["head"] == w.head and snap["status_porcelain"] == ""
    assert len(snap["tracked_sha256"]) == 64 and os.path.isabs(snap["worktree"])
    # sha256 over the sorted (path, work-tree file sha256) list of tracked files
    again = w.scratch / "again.json"
    assert w.call(["snapshot", "--worktree", str(w.wt), "--out", str(again)])[0] == 0
    assert json.loads(again.read_text(encoding="utf-8"))["tracked_sha256"] == snap["tracked_sha256"]
    (w.wt / "code.py").write_text("print('changed')\n", encoding="utf-8")
    (w.wt / "untracked.txt").write_text("x\n", encoding="utf-8")
    third = w.scratch / "third.json"
    assert w.call(["snapshot", "--worktree", str(w.wt), "--out", str(third)])[0] == 0
    changed = json.loads(third.read_text(encoding="utf-8"))
    assert changed["tracked_sha256"] != snap["tracked_sha256"] and changed["head"] == w.head
    assert "code.py" in changed["status_porcelain"] and "untracked.txt" in changed["status_porcelain"]


def test_snapshot_never_replaces_an_existing_snapshot(world):
    before = world.snap.read_bytes()
    (world.wt / "code.py").write_text("print('after the job')\n", encoding="utf-8")
    code, out = world.call(["snapshot", "--worktree", str(world.wt), "--out", str(world.snap)])
    assert code == 1 and tokens(out) == ["snapshot_exists"]
    assert world.snap.read_bytes() == before


def test_snapshot_of_something_unobservable_writes_nothing(world, tmp_path):
    plain = tmp_path / "plain"
    plain.mkdir()
    target = tmp_path / "s.json"
    code, out = world.call(["snapshot", "--worktree", str(plain), "--out", str(target)])
    assert code == 3 and tokens(out) == ["worktree_unobservable"] and not target.exists()
    code, out = world.call(["snapshot", "--worktree", str(tmp_path / "absent"), "--out", str(target)])
    assert code == 66 and not target.exists()
    sub = world.wt / "sub"
    sub.mkdir()
    code, out = world.call(["snapshot", "--worktree", str(sub), "--out", str(target)])
    assert code == 3 and not target.exists()        # a subdirectory would hash only part of the tree


# ───────────────────────────────────── Contract B: publish ─────────────────────────────────────

def test_publish_accepted_runs_ky_verdict_once_under_an_action_record(world):
    code, out = world.publish()
    assert code == 0
    assert out == {"published": True, "result": "ACCEPTED", "reasons": [], "action_id": "VERDICT-" + JOB}
    calls = world.calls()
    assert len(calls) == 1
    assert calls[0]["argv"] == ["verdict", ITEM, "--head", world.head, "--phase", "pre_merge", "--result",
                                "ACCEPTED", "--detail",
                                "job %s; diff matches the packet; 3 tests re-run green" % JOB]
    assert calls[0]["KY_STREAM"] == "V" and calls[0]["KY_LANE"] == VSLOT
    assert set(calls[0]["env_names"]) <= KY_ENV_ALLOWED, set(calls[0]["env_names"]) - KY_ENV_ALLOWED
    assert "KY_CANARY_NOT_ALLOWED" not in calls[0]["env_names"] and "GIT_DIR" not in calls[0]["env_names"]
    events = world.verdicts()
    assert len(events) == 1 and events[0]["result"] == "ACCEPTED" and events[0]["head"] == world.head
    record = world.record()
    assert record["state"] == "DONE" and record["kind"] == "ky.verdict"
    assert record["actor"] == {"role": "dispatcher", "holder_kind": "controller", "controller_id": CID}
    assert record["target"]["item"] == ITEM and record["target"]["head"] == world.head
    assert record["result"]["result"] == "ACCEPTED" and record["result"]["event"]["detail"].startswith("job " + JOB)


def test_publish_twice_leaves_one_accepted_event(world):
    assert world.publish()[0] == 0
    code, out = world.publish()
    assert code == 0 and out["published"] is True and out["result"] == "ACCEPTED"
    assert tokens(out) == ["already_published"]
    assert len(world.calls()) == 1 and len(world.verdicts()) == 1


def test_publish_done_record_is_not_reopened_when_the_tree_later_changes(world):
    assert world.publish()[0] == 0
    commit(world.wt, "the branch moved on", {"code.py": "print('next')\n"})
    code, out = world.publish()
    assert code == 0 and tokens(out) == ["already_published"]
    assert len(world.calls()) == 1 and len(world.verdicts()) == 1


def test_publish_rejected_proposal_publishes_rejected(world):
    world.write_result(verdict={"verdict": "REJECTED", "phase": "pre_merge", "head": world.head,
                                "summary": "test 2 fails on the reviewed head"})
    code, out = world.publish()
    assert code == 0 and out["published"] is True and out["result"] == "REJECTED"
    assert [e["result"] for e in world.verdicts()] == ["REJECTED"]


def test_publish_detail_falls_back_to_the_notes(world):
    world.write_result(verdict={"verdict": "ACCEPTED"})
    assert world.publish()[0] == 0
    assert world.calls()[0]["argv"][-1] == "job %s; review of the PR head; nothing pushed" % JOB


def test_publish_post_deploy_at_the_squash_merge_commit(world):
    squash = "c" * 40
    world.write_result(verdict={"verdict": "ACCEPTED", "phase": "post_deploy", "head": squash, "summary": "ok"})
    code, out = world.publish(**{"--phase": "post_deploy", "--head": squash})
    assert code == 0 and out["published"] is True
    assert world.calls()[0]["argv"][:6] == ["verdict", ITEM, "--head", squash, "--phase", "post_deploy"]


def test_publish_artifact_binds_the_digest_of_the_file(world):
    world.write_result(verdict={"verdict": "ACCEPTED", "phase": "artifact", "artifact_digest": world.digest,
                                "summary": "packet reviewed"})
    code, out = world.call(world.artifact_argv())
    assert code == 0 and out["published"] is True and out["result"] == "ACCEPTED"
    assert world.calls()[0]["argv"][:6] == ["verdict", ITEM, "--artifact-digest", world.digest, "--phase",
                                            "artifact"]
    assert world.verdicts()[0]["artifact_digest"] == world.digest and "head" not in world.verdicts()[0]


def test_publish_passes_the_external_review_pair(world):
    review = world.scratch / "external_review.json"
    review.write_text(json.dumps({"item": ITEM, "result": "ACCEPTED", "by": "codex"}), encoding="utf-8")
    digest = hashlib.sha256(review.read_bytes()).hexdigest()
    code, out = world.publish(**{"--external-review-path": str(review), "--external-review-sha256": digest})
    assert code == 0, out
    assert world.calls()[0]["argv"][-4:] == ["--external-review-path", str(review), "--external-review-sha256",
                                             digest]
    assert world.verdicts()[0]["external_review"] == {"path": str(review), "sha256": digest}


def _job_exit(w):
    return {"--job-exit": "1"}


def _job_killed(w):
    return {"--job-exit": "-9"}


def _result_missing(w):
    w.result.unlink()


def _result_not_json(w):
    w.result.write_text("{not json", encoding="utf-8")


def _result_extra_key(w):
    w.write_result(surprise=True)


def _result_bad_test_row(w):
    w.write_result(tests=[{"cmd": "x", "exit": "0", "summary": "ok"}])


def _result_symlink(w):
    real = w.scratch / "real_result.json"
    w.result.rename(real)
    w.result.symlink_to(real)


def _result_other_job(w):
    w.write_result(job_id="J-20261012T090155Z-v2")


def _result_other_item(w):
    w.write_result(item="N-468")


def _result_failed(w):
    w.write_result(status="failed")


def _result_blocked(w):
    w.write_result(status="blocked", blocked_reason="freeze: x")


def _no_proposal(w):
    w.write_result(verdict=None)


def _proposal_not_a_verdict(w):
    w.write_result(verdict={"verdict": "LGTM", "head": w.head})


def _proposal_lower_case(w):
    w.write_result(verdict={"verdict": "accepted", "head": w.head})


def _proposal_other_head(w):
    w.write_result(verdict={"verdict": "ACCEPTED", "head": "d" * 40})


def _proposal_other_phase(w):
    w.write_result(verdict={"verdict": "ACCEPTED", "phase": "post_deploy", "head": w.head})


def _author_reviews(w):
    return {"--author-id": "opus-v1", "--reviewer-id": "opus-v1"}


def _author_reviews_other_case(w):
    return {"--author-id": "Opus-V1 ", "--reviewer-id": "opus-v1"}


def _head_moved(w):
    git(w.wt, "commit", "-q", "--allow-empty", "-m", "the job committed")


def _head_is_not_the_reviewed_one(w):
    return {"--head": "d" * 40, "_result": {"verdict": "ACCEPTED", "head": "d" * 40}}


def _untracked_file(w):
    (w.wt / "left_behind.txt").write_text("x\n", encoding="utf-8")


def _untracked_file_hidden_by_config(w):
    (w.wt / "left_behind.txt").write_text("x\n", encoding="utf-8")
    git(w.wt, "config", "status.showUntrackedFiles", "no")


def _assume_unchanged(w):
    git(w.wt, "update-index", "--assume-unchanged", "code.py")
    (w.wt / "code.py").write_text("print('edited behind the index')\n", encoding="utf-8")
    assert git(w.wt, "status", "--porcelain") == "", "the fixture hides the edit from git status"


def _skip_worktree(w):
    git(w.wt, "update-index", "--skip-worktree", "doc.md")
    (w.wt / "doc.md").write_text("edited behind the index\n", encoding="utf-8")
    assert git(w.wt, "status", "--porcelain") == ""


def _snapshot_missing(w):
    w.snap.unlink()


def _snapshot_of_another_tree(w):
    doc = json.loads(w.snap.read_text(encoding="utf-8"))
    doc["worktree"] = str(w.root / "elsewhere")
    w.snap.write_text(json.dumps(doc), encoding="utf-8")


def _snapshot_truncated(w):
    w.snap.write_text('{"head": "', encoding="utf-8")


def _boundary_missing(w):
    w.boundary.unlink()


def _boundary_violated(w):
    w.write_boundary(result="violated", tracked_hashes_unchanged=False)


def _boundary_unknown(w):
    w.write_boundary(result="unknown")


def _boundary_flag_false(w):
    w.write_boundary(mechanism_intact=False)


def _boundary_nested_flag_false(w):
    w.write_boundary(worktree={"head_unchanged": True, "status_clean": False})


def _boundary_no_result(w):
    w.boundary.write_text(json.dumps({"job_id": JOB}), encoding="utf-8")


def _boundary_other_job(w):
    w.write_boundary(job_id="J-20261012T090155Z-v2")


def _boundary_not_json(w):
    w.boundary.write_text("intact\n", encoding="utf-8")


def _boundary_empty(w):
    w.boundary.write_text("", encoding="utf-8")


REFUSALS = [
    (_job_exit, "job_exit_nonzero"), (_job_killed, "job_exit_nonzero"),
    (_result_missing, "result_missing"), (_result_not_json, "result_invalid"),
    (_result_extra_key, "result_invalid"), (_result_bad_test_row, "result_invalid"),
    (_result_symlink, "result_invalid"), (_result_other_job, "result_job_mismatch"),
    (_result_other_item, "result_job_mismatch"), (_result_failed, "result_not_done"),
    (_result_blocked, "result_not_done"), (_no_proposal, "verdict_not_proposed"),
    (_proposal_not_a_verdict, "verdict_not_proposed"), (_proposal_lower_case, "verdict_not_proposed"),
    (_proposal_other_head, "verdict_head_mismatch"), (_proposal_other_phase, "verdict_phase_mismatch"),
    (_author_reviews, "author_is_reviewer"), (_author_reviews_other_case, "author_is_reviewer"),
    (_head_moved, "head_moved"), (_head_is_not_the_reviewed_one, "head_not_reviewed"),
    (_untracked_file, "tree_dirty"), (_untracked_file_hidden_by_config, "tree_dirty"),
    (_assume_unchanged, "tracked_changed"), (_skip_worktree, "tracked_changed"),
    (_snapshot_missing, "snapshot_missing"), (_snapshot_of_another_tree, "snapshot_invalid"),
    (_snapshot_truncated, "snapshot_invalid"),
    (_boundary_missing, "boundary_missing"), (_boundary_violated, "boundary_not_intact"),
    (_boundary_unknown, "boundary_not_intact"), (_boundary_flag_false, "boundary_not_intact"),
    (_boundary_nested_flag_false, "boundary_not_intact"), (_boundary_no_result, "boundary_not_intact"),
    (_boundary_other_job, "boundary_job_mismatch"), (_boundary_not_json, "boundary_invalid"),
    (_boundary_empty, "boundary_invalid"),
]


@pytest.mark.parametrize("breakage,reason", REFUSALS, ids=[f.__name__.lstrip("_") for f, _ in REFUSALS])
def test_publish_each_requirement_failing_alone_refuses_without_ky(world, breakage, reason):
    """One requirement broken, every other one met: exit 1, exactly its reason, no ky call, no record, no event."""
    over = breakage(world) or {}
    if "_result" in over:
        world.write_result(verdict=over.pop("_result"))
    code, out = world.publish(**over)
    assert code == 1, out
    assert out["published"] is False and out["result"] is None and out["action_id"] == "VERDICT-" + JOB
    assert tokens(out) == [reason], out
    world.nothing_published()
    assert world.record() is None, "a refusal begins no action"
    # the control — the same fixture with nothing broken publishes — is the first publish test above


def test_publish_modified_tracked_file_is_dirty_and_changed(world):
    (world.wt / "code.py").write_text("print('edited')\n", encoding="utf-8")
    code, out = world.publish()
    assert code == 1 and tokens(out) == ["tree_dirty", "tracked_changed"]
    world.nothing_published()


def test_publish_artifact_requirements(world):
    world.write_result(verdict={"verdict": "ACCEPTED", "phase": "artifact", "artifact_digest": world.digest})
    code, out = world.call(world.artifact_argv(**{"--artifact-digest": "0" * 64}))
    assert code == 1 and tokens(out) == ["verdict_digest_mismatch", "artifact_digest_mismatch"]
    world.artifact.write_text("edited after the review\n", encoding="utf-8")
    code, out = world.call(world.artifact_argv())
    assert code == 1 and tokens(out) == ["artifact_digest_mismatch"]
    world.artifact.unlink()
    code, out = world.call(world.artifact_argv())
    assert code == 1 and tokens(out) == ["artifact_missing"]
    world.nothing_published()
    assert world.record() is None


def test_publish_artifact_refuses_a_proposal_that_names_a_head(world):
    world.write_result()                            # proposes pre_merge at a head
    code, out = world.call(world.artifact_argv())
    assert code == 1 and tokens(out) == ["verdict_head_mismatch", "verdict_phase_mismatch"]
    world.nothing_published()


def test_publish_external_review_must_be_the_named_file(world):
    review = world.scratch / "external_review.json"
    review.write_text("{}", encoding="utf-8")
    code, out = world.publish(**{"--external-review-path": str(review), "--external-review-sha256": "1" * 64})
    assert code == 1 and tokens(out) == ["external_review_sha_mismatch"]
    review.unlink()
    code, out = world.publish(**{"--external-review-path": str(review), "--external-review-sha256": "1" * 64})
    assert code == 1 and tokens(out) == ["external_review_missing"]
    world.nothing_published()


def test_publish_job_result_check_agrees_with_the_schema(world):
    """The hand-written ky.job_result/1 check accepts and refuses exactly what schemas/job_result.json does."""
    import kyschema
    schema = json.loads((SCHEMAS / "job_result.json").read_text(encoding="utf-8"))
    base = world.write_result()
    variants = [base]
    for key in list(base):
        variants.append({k: v for k, v in base.items() if k != key})
    for change in ({"schema": "ky.job_result/2"}, {"job_id": ""}, {"job_id": "-x"}, {"job_id": 5}, {"item": ""},
                   {"status": "ok"}, {"branch": ""}, {"branch": "b"}, {"branch": 5}, {"head_sha": "abc"},
                   {"head_sha": "a" * 40}, {"head_sha": "A" * 40}, {"pr_number": 0}, {"pr_number": 12},
                   {"pr_number": 12, "head_sha": "a" * 40}, {"pr_number": True}, {"pr_number": 1.5},
                   {"tests": {}}, {"tests": []}, {"tests": [{"cmd": "", "exit": 0, "summary": ""}]},
                   {"tests": [{"cmd": "x", "exit": 0}]}, {"tests": [{"cmd": "x", "exit": 0, "summary": "", "n": 1}]},
                   {"tests": [{"cmd": "x", "exit": True, "summary": ""}]}, {"tests": ["x"]},
                   {"tests": [{"cmd": "x", "exit": 1.0, "summary": ""}]},
                   {"blocked_reason": 5}, {"blocked_reason": "why"}, {"status": "blocked"},
                   {"status": "blocked", "blocked_reason": ""}, {"status": "blocked", "blocked_reason": "x"},
                   {"notes": None}, {"notes": ""}, {"proposed_verdict": "ACCEPTED"}, {"proposed_verdict": {}},
                   {"extra": 1}, {"job_id": "a" * 128}, {"job_id": "a" * 129}, {"job_id": "ok\n"}):
        variants.append(dict(base, **change))
    variants += [[], "x", None, 3]
    assert kyschema.lint(schema) == []
    verdicts = [kyschema.validate(schema, doc) == [] for doc in variants]
    assert [doc for doc, by_schema in zip(variants, verdicts) if (K.job_result_problem(doc) is None) != by_schema] == []
    assert verdicts.count(True) >= 8 and verdicts.count(False) >= 30, "the comparison saw both answers"
    assert K.job_result_problem(base) is None and K.job_result_problem(dict(base, extra=1)) is not None


def test_publish_refused_by_ky_fails_the_record_and_stays_refused(world):
    world.mode("refuse")
    code, out = world.publish()
    assert code == 1 and out["published"] is False and tokens(out) == ["ky_refused"]
    assert world.verdicts() == [] and world.record()["state"] == "FAILED"
    world.mode("ok")
    code, out = world.publish()
    assert code == 1 and out["published"] is False and tokens(out) == ["action_failed"]
    assert len(world.calls()) == 1 and world.verdicts() == []


def test_publish_ky_exit_zero_without_the_event_is_unknown(world):
    """Earned signal: ky's exit code is not the publication. No event in the ledger → nothing is claimed."""
    world.mode("silent")
    code, out = world.publish()
    assert code == 3 and out["published"] is False and out["result"] is None
    assert tokens(out) == ["event_not_observed"]
    assert world.record()["state"] == "INTENDED"


def test_publish_event_in_the_ledger_counts_whatever_ky_exited_with(world):
    world.mode("fail_after_append")
    code, out = world.publish()
    assert code == 0 and out["published"] is True and out["result"] == "ACCEPTED"
    assert world.record()["state"] == "DONE" and len(world.verdicts()) == 1


def test_publish_crash_after_ky_before_complete_publishes_no_second_event(world, monkeypatch):
    def die(*a, **k):
        raise Crash()
    monkeypatch.setattr(kyaction, "complete", die)
    with pytest.raises(Crash):
        world.publish()
    assert world.record()["state"] == "INTENDED" and len(world.verdicts()) == 1
    monkeypatch.undo()
    code, out = world.publish()
    assert code == 0 and out["published"] is True and out["result"] == "ACCEPTED"
    assert tokens(out) == ["already_published"]
    assert len(world.calls()) == 1 and len(world.verdicts()) == 1
    assert world.record()["state"] == "DONE" and world.record()["reconciliations"][-1]["outcome"] == "done"
    assert world.publish()[0] == 0 and len(world.calls()) == 1 and len(world.verdicts()) == 1


def test_publish_crash_after_begin_before_ky_publishes_exactly_once(world, monkeypatch):
    def die(*a, **k):
        raise Crash()
    monkeypatch.setattr(K, "_run_ky", die)
    with pytest.raises(Crash):
        world.publish()
    assert world.record()["state"] == "INTENDED" and world.calls() == [] and world.verdicts() == []
    monkeypatch.undo()
    world.seed("ACCEPTED", detail="job J-OTHER; another job's verdict at the same head is not this action")
    code, out = world.publish()
    assert code == 0 and out["published"] is True and out["reasons"] == []
    assert len(world.calls()) == 1 and len(world.verdicts()) == 2
    assert world.publish()[0] == 0 and len(world.calls()) == 1


def test_publish_killed_process_between_begin_and_complete(world):
    """The real thing: the kyverdicts process is SIGKILLed by its own (fake) ky right after the event is appended."""
    world.mode("kill_parent")
    r = subprocess.run([PY, "-B", str(FLEET / "kyverdicts.py"), *world.publish_argv()], capture_output=True,
                       text=True, env=world.env, timeout=120)
    assert r.returncode == -9 and r.stdout == "", (r.returncode, r.stdout, r.stderr)
    assert world.record()["state"] == "INTENDED" and len(world.verdicts()) == 1 and len(world.calls()) == 1
    world.mode("ok")
    r = subprocess.run([PY, "-B", str(FLEET / "kyverdicts.py"), *world.publish_argv()], capture_output=True,
                       text=True, env=world.env, timeout=120)
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout) == {"published": True, "result": "ACCEPTED", "reasons": ["already_published"],
                                    "action_id": "VERDICT-" + JOB}
    assert len(world.calls()) == 1 and len(world.verdicts()) == 1 and world.record()["state"] == "DONE"


@pytest.mark.parametrize("damage", ["missing", "directory", "partial_line"])
def test_publish_unfinished_with_an_unreadable_ledger_is_unknown(world, monkeypatch, damage):
    def die(*a, **k):
        raise Crash()
    monkeypatch.setattr(kyaction, "complete", die)
    with pytest.raises(Crash):
        world.publish()
    monkeypatch.undo()
    if damage == "partial_line":
        with open(world.events, "a", encoding="utf-8") as f:
            f.write('{"kind":"verdict","item":"N-4')
    else:
        world.events.unlink()
        if damage == "directory":
            world.events.mkdir()
    code, out = world.publish()
    assert code == 3 and out["published"] is False and tokens(out) == ["ledger_unreadable"]
    assert len(world.calls()) == 1 and world.record()["state"] == "INTENDED"


def test_publish_unfinished_and_no_longer_publishable_fails_the_record(world, monkeypatch):
    def die(*a, **k):
        raise Crash()
    monkeypatch.setattr(K, "_run_ky", die)
    with pytest.raises(Crash):
        world.publish()
    monkeypatch.undo()
    git(world.wt, "commit", "-q", "--allow-empty", "-m", "moved while the controller was down")
    code, out = world.publish()
    assert code == 1 and out["published"] is False and tokens(out) == ["head_moved"]
    world.nothing_published()
    assert world.record()["state"] == "FAILED"


def test_publish_while_another_process_is_publishing_is_unknown(world):
    world.mode("hang")
    child = subprocess.Popen([PY, "-B", str(FLEET / "kyverdicts.py"), *world.publish_argv()],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=world.env)
    try:
        limit = time.monotonic() + 60
        while not world.calls() and time.monotonic() < limit and child.poll() is None:
            time.sleep(0.05)
        assert len(world.calls()) == 1, "the first publisher never reached ky"
        code, out = world.publish()
        assert code == 3 and out["published"] is False and tokens(out) == ["action_in_progress"]
        assert len(world.calls()) == 1 and world.verdicts() == []
    finally:
        (world.bin / "release").write_text("go", encoding="utf-8")
        stdout, stderr = child.communicate(timeout=120)
    assert child.returncode == 0, stderr
    assert json.loads(stdout)["published"] is True and len(world.verdicts()) == 1 and len(world.calls()) == 1


def test_publish_same_job_for_another_identity_is_a_conflict(world):
    assert world.publish()[0] == 0
    world.write_result(verdict={"verdict": "ACCEPTED", "phase": "post_deploy", "head": "c" * 40})
    code, out = world.publish(**{"--phase": "post_deploy", "--head": "c" * 40})
    assert code == 1 and out["published"] is False and tokens(out) == ["action_conflict"]
    assert len(world.calls()) == 1 and len(world.verdicts()) == 1


def test_publish_same_job_with_another_result_is_a_conflict(world, monkeypatch):
    def die(*a, **k):
        raise Crash()
    monkeypatch.setattr(K, "_run_ky", die)
    with pytest.raises(Crash):
        world.publish()
    monkeypatch.undo()
    world.write_result(verdict={"verdict": "REJECTED", "head": world.head, "summary": "changed its mind"})
    code, out = world.publish()
    assert code == 1 and out["published"] is False and tokens(out) == ["action_conflict"]
    world.nothing_published()


def test_publish_unreadable_action_record_is_unknown(world):
    actions = world.run_dir / "actions"
    actions.mkdir()
    (actions / ("VERDICT-%s.json" % JOB)).write_text("{", encoding="utf-8")
    code, out = world.publish()
    assert code == 3 and out["published"] is False and tokens(out) == ["action_record_unreadable"]
    world.nothing_published()


def test_publish_missing_installation_inputs_exit_66(world):
    for change in ({"KY_RUN": str(world.root / "no-run")}, {"KY_RUN": ""}, {"KY_RUN": "relative/run"},
                   {"KY_BIN": str(world.root / "no-ky")}, {"KY_BIN": "", "KY_ROOT": ""},
                   {"KY_GIT": "/nonexistent/git"}):
        code, out = world.call(world.publish_argv(), env=dict(world.env, **change))
        assert code == 66 and out["published"] is False, (change, out)
    code, out = world.publish(**{"--worktree": str(world.root / "no-worktree")})
    assert code == 66 and out["published"] is False
    world.nothing_published()
    assert world.record() is None


def test_publish_ky_defaults_to_ky_root_bin(world):
    env = {k: v for k, v in world.env.items() if k != "KY_BIN"}
    code, out = world.call(world.publish_argv(), env=env)
    assert code == 0 and out["published"] is True and len(world.calls()) == 1


def test_publish_reads_the_ledger_named_by_events(world):
    other = world.root / "OTHER_EVENTS.jsonl"
    other.write_text("", encoding="utf-8")
    code, out = world.publish(**{"--events": str(other)})     # ky wrote to the run ledger, not to this one
    assert code == 3 and tokens(out) == ["event_not_observed"] and out["published"] is False


@pytest.mark.parametrize("argv", [
    [], ["publish"], ["verdict"], ["--help"], ["publish", "--help"], ["inherit"], ["snapshot"], ["invalidate"],
    ["inherit", "--repo", "/x", "--old-head", "a" * 40], ["snapshot", "--worktree", "/x"],
])
def test_usage_errors_exit_64_and_publish_nothing(world, argv):
    code, out = world.call(argv)
    assert code == 64 and out["published"] is False and out["result"] is None and out["reasons"]
    world.nothing_published()


@pytest.mark.parametrize("over", [
    {"--artifact-digest": "0" * 64}, {"--head": None}, {"--phase": "merged"}, {"--head": "abc"},
    {"--head": "A" * 40}, {"--job-exit": "zero"}, {"--job-id": "../x"}, {"--job-id": ""}, {"--item": "N 467"},
    {"--vslot": "v 1"}, {"--vslot": ""}, {"--as": ""}, {"--author-id": ""}, {"--reviewer-id": " "},
    {"--worktree": "relative/wt"}, {"--snapshot": "s.json"}, {"--result": "result.json"},
    {"--boundary": "b.json"}, {"--events": "EVENTS.jsonl"}, {"--external-review-path": "/x/review.json"},
    {"--external-review-sha256": "1" * 64}, {"--artifact-path": "/x/artifact"},
    {"--phase": "artifact"}, {"--surprise": "1"},
], ids=lambda over: ",".join("%s=%s" % (k, v) for k, v in over.items())[:60])
def test_usage_publish_arguments(world, over):
    code, out = world.publish(**over)
    assert code == 64 and out["published"] is False, out
    world.nothing_published()
    assert world.record() is None


def test_usage_artifact_needs_digest_and_path(world):
    for over in ({"--artifact-path": None}, {"--artifact-digest": None}, {"--artifact-digest": "abc"},
                 {"--head": world.head}, {"--artifact-path": "relative.md"}):
        code, out = world.call(world.artifact_argv(**over))
        assert code == 64 and out["published"] is False, (over, out)
    world.nothing_published()


def test_cli_prints_one_json_object_and_nothing_by_default(world):
    r = subprocess.run([PY, "-B", str(FLEET / "kyverdicts.py")], capture_output=True, text=True, env=world.env)
    assert r.returncode == 64
    assert json.loads(r.stdout) == {"published": False, "result": None, "reasons": json.loads(r.stdout)["reasons"],
                                    "action_id": None}
    world.write_boundary(result="violated")
    r = subprocess.run([PY, "-B", str(FLEET / "kyverdicts.py"), *world.publish_argv()], capture_output=True,
                       text=True, env=world.env)
    assert r.returncode == 1
    assert json.loads(r.stdout) == {"published": False, "result": None, "reasons": ["boundary_not_intact"],
                                    "action_id": "VERDICT-" + JOB}
    world.nothing_published()


# ───────────────────────────────────── Contract B: invalidate ─────────────────────────────────────

def invalidation_id(world, phase="pre_merge", identity=None):
    return "INVALIDATE-%s-%s-%s" % (ITEM, phase, (identity or world.head)[:12])


def test_invalidate_without_a_prior_accepted_appends_nothing(world):
    code, out = world.call(world.invalidate_argv())
    assert code == 1 and out["published"] is False and out["result"] is None
    assert tokens(out) == ["no_prior_verdict"] and out["action_id"] == invalidation_id(world)
    world.nothing_published()
    assert world.record(invalidation_id(world)) is None


def test_invalidate_ignores_an_accepted_of_another_identity(world):
    world.seed("ACCEPTED", head="d" * 40)
    world.seed("ACCEPTED", phase="post_deploy")
    world.seed("ACCEPTED", item="N-468")
    world.seed("ACCEPTED", head=None, artifact_digest=world.digest, phase="artifact")
    before = world.events.read_bytes()
    code, out = world.call(world.invalidate_argv())
    assert code == 1 and tokens(out) == ["no_prior_verdict"]
    assert world.calls() == [] and world.events.read_bytes() == before


def test_invalidate_when_the_latest_verdict_is_rejected_appends_nothing(world):
    world.seed("ACCEPTED")
    world.seed("REJECTED", detail="job J-OTHER; a later review rejected it")
    before = world.events.read_bytes()
    code, out = world.call(world.invalidate_argv())
    assert code == 1 and out["published"] is False and tokens(out) == ["latest_not_accepted"]
    assert world.calls() == [] and world.events.read_bytes() == before
    assert world.record(invalidation_id(world)) is None


def test_invalidate_appends_an_explicit_rejected_once(world):
    assert world.publish()[0] == 0
    code, out = world.call(world.invalidate_argv())
    assert code == 0
    assert out == {"published": True, "result": "REJECTED", "reasons": [], "action_id": invalidation_id(world)}
    call = world.calls()[-1]
    assert call["argv"] == ["verdict", ITEM, "--head", world.head, "--phase", "pre_merge", "--result", "REJECTED",
                            "--detail", "invalidated: required check went red after acceptance"]
    assert call["KY_STREAM"] == "V" and call["KY_LANE"] == VSLOT
    assert set(call["env_names"]) <= KY_ENV_ALLOWED
    assert [e["result"] for e in world.verdicts()] == ["ACCEPTED", "REJECTED"]
    record = world.record(invalidation_id(world))
    assert record["state"] == "DONE" and record["kind"] == "ky.verdict.invalidate"
    assert record["actor"] == {"role": "dispatcher", "holder_kind": "controller", "controller_id": CID}
    code, out = world.call(world.invalidate_argv())
    assert code == 0 and out["published"] is True and tokens(out) == ["already_published"]
    assert len(world.calls()) == 2 and len(world.verdicts()) == 2


def test_invalidate_an_artifact_acceptance(world):
    world.seed("ACCEPTED", head=None, artifact_digest=world.digest, phase="artifact")
    argv = world.invalidate_argv(**{"--phase": "artifact", "--head": None, "--artifact-digest": world.digest})
    code, out = world.call(argv)
    assert code == 0 and out["action_id"] == invalidation_id(world, "artifact", world.digest)
    assert world.calls()[-1]["argv"][:6] == ["verdict", ITEM, "--artifact-digest", world.digest, "--phase",
                                             "artifact"]
    assert [e["result"] for e in world.verdicts()] == ["ACCEPTED", "REJECTED"]


@pytest.mark.parametrize("damage", ["missing", "directory", "partial_line"])
def test_invalidate_with_an_unreadable_ledger_is_unknown(world, damage):
    world.seed("ACCEPTED")
    if damage == "partial_line":
        with open(world.events, "a", encoding="utf-8") as f:
            f.write('{"kind":"verdict"')
    else:
        world.events.unlink()
        if damage == "directory":
            world.events.mkdir()
    code, out = world.call(world.invalidate_argv())
    assert code == 3 and out["published"] is False and tokens(out) == ["ledger_unreadable"]
    assert world.calls() == [] and world.record(invalidation_id(world)) is None


def test_invalidate_crash_between_begin_and_complete_appends_one_rejected(world, monkeypatch):
    world.seed("ACCEPTED")

    def die(*a, **k):
        raise Crash()
    monkeypatch.setattr(kyaction, "complete", die)
    with pytest.raises(Crash):
        world.call(world.invalidate_argv())
    monkeypatch.undo()
    assert world.record(invalidation_id(world))["state"] == "INTENDED"
    code, out = world.call(world.invalidate_argv(**{"--reason": "worded differently on the retry"}))
    assert code == 0 and out["published"] is True and out["result"] == "REJECTED"
    assert len(world.calls()) == 1 and [e["result"] for e in world.verdicts()] == ["ACCEPTED", "REJECTED"]


def test_invalidate_crash_before_ky_appends_one_rejected(world, monkeypatch):
    world.seed("ACCEPTED")

    def die(*a, **k):
        raise Crash()
    monkeypatch.setattr(K, "_run_ky", die)
    with pytest.raises(Crash):
        world.call(world.invalidate_argv())
    monkeypatch.undo()
    assert world.calls() == []
    code, out = world.call(world.invalidate_argv())
    assert code == 0 and out["published"] is True
    assert len(world.calls()) == 1 and [e["result"] for e in world.verdicts()] == ["ACCEPTED", "REJECTED"]
    assert world.call(world.invalidate_argv())[0] == 0 and len(world.calls()) == 1


def accepted_in_force(world, head=None):
    latest = [e for e in world.verdicts() if e.get("head") == (head or world.head) and e.get("phase") == "pre_merge"]
    return bool(latest) and latest[-1]["result"] == "ACCEPTED"


def test_invalidate_refused_by_ky_while_accepted_is_in_force_is_unknown(world):
    """R2-B-01: exit 1 reads 'nothing to invalidate'. With ACCEPTED still in force it is exit 3, nothing may proceed."""
    world.seed("ACCEPTED")
    world.mode("refuse")
    code, out = world.call(world.invalidate_argv())
    assert code == 3 and out["published"] is False and out["result"] is None and tokens(out) == ["ky_refused"]
    assert accepted_in_force(world) and world.record(invalidation_id(world))["state"] == "FAILED"


def test_invalidate_after_a_refused_attempt_retries_and_appends_exactly_one_rejected(world):
    world.seed("ACCEPTED")
    world.mode("refuse")
    assert world.call(world.invalidate_argv())[0] == 3
    world.mode("ok")
    code, out = world.call(world.invalidate_argv(**{"--reason": "worded differently on the retry"}))
    assert code == 0 and out["published"] is True and out["result"] == "REJECTED" and out["reasons"] == []
    assert [e["result"] for e in world.verdicts()] == ["ACCEPTED", "REJECTED"]
    assert world.verdicts()[-1]["detail"] == "invalidated: required check went red after acceptance"
    record = world.record(invalidation_id(world))
    assert record["state"] == "DONE" and len(record["attempts"]) == 1 and record["attempts"][0]["state"] == "FAILED"
    code, out = world.call(world.invalidate_argv())
    assert code == 0 and tokens(out) == ["already_published"]
    assert len(world.calls()) == 2 and len(world.verdicts()) == 2


def test_invalidate_while_ky_keeps_refusing_stays_unknown(world):
    world.seed("ACCEPTED")
    world.mode("refuse")
    for n in range(1, 4):
        code, out = world.call(world.invalidate_argv())
        assert code == 3 and tokens(out) == ["ky_refused"] and len(world.calls()) == n
        assert accepted_in_force(world) and world.record(invalidation_id(world))["state"] == "FAILED"


def test_invalidate_ky_timeout_while_accepted_is_in_force_is_unknown_then_retried(world, monkeypatch):
    world.seed("ACCEPTED")
    world.mode("hang")
    monkeypatch.setattr(K, "KY_TIMEOUT_S", 0.5)
    code, out = world.call(world.invalidate_argv())
    assert code == 3 and tokens(out) == ["ky_timeout"] and accepted_in_force(world)
    world.mode("ok")
    code, out = world.call(world.invalidate_argv())
    assert code == 0 and out["published"] is True
    assert [e["result"] for e in world.verdicts()] == ["ACCEPTED", "REJECTED"] and len(world.calls()) == 2


def test_invalidate_failed_attempt_is_not_retried_once_nothing_is_in_force(world):
    world.seed("ACCEPTED")
    world.mode("refuse")
    assert world.call(world.invalidate_argv())[0] == 3
    world.seed("REJECTED", detail="job J-OTHER; a later review rejected it")
    world.mode("ok")
    code, out = world.call(world.invalidate_argv())
    assert code == 1 and out["published"] is False and tokens(out) == ["latest_not_accepted"]
    assert len(world.calls()) == 1 and world.record(invalidation_id(world))["state"] == "FAILED"


def test_invalidate_record_conflict_while_accepted_is_in_force_is_unknown(world):
    """Two heads sharing 12 hex share a record id: the second identity cannot be recorded, and is not 'nothing'."""
    twin = world.head[:12] + ("f" if world.head[12] != "f" else "e") * 28
    world.seed("ACCEPTED", head=twin)
    assert world.call(world.invalidate_argv(**{"--head": twin}))[0] == 0
    code, out = world.call(world.invalidate_argv())
    assert code == 1 and tokens(out) == ["no_prior_verdict"]
    world.seed("ACCEPTED")
    code, out = world.call(world.invalidate_argv())
    assert code == 3 and out["published"] is False and tokens(out) == ["action_conflict"]
    assert accepted_in_force(world) and len(world.calls()) == 1


def test_invalidate_conflict_raised_by_begin_while_accepted_is_in_force_is_unknown(world, monkeypatch):
    world.seed("ACCEPTED")

    def conflict(*a, **k):
        raise kyaction.ActionConflict("another invalidation of this identity was recorded first")
    monkeypatch.setattr(kyaction, "begin", conflict)
    code, out = world.call(world.invalidate_argv())
    assert code == 3 and tokens(out) == ["action_conflict"] and world.calls() == []


def test_invalidate_record_failed_while_reconciling_is_unknown(world, monkeypatch):
    world.seed("ACCEPTED")

    def die(*a, **k):
        raise Crash()
    monkeypatch.setattr(K, "_run_ky", die)
    with pytest.raises(Crash):
        world.call(world.invalidate_argv())
    monkeypatch.undo()
    monkeypatch.setattr(kyaction, "reconcile", lambda run_dir, action_id, *a, **k: (
        "failed", kyaction.load(run_dir, action_id)))
    code, out = world.call(world.invalidate_argv())
    assert code == 3 and tokens(out) == ["action_failed"] and world.calls() == []


@pytest.mark.parametrize("trouble", ["refuse", "hang", "silent", "conflict", "begin_conflict"])
def test_invalidate_never_exits_1_while_accepted_is_in_force(world, monkeypatch, trouble):
    world.seed("ACCEPTED")
    monkeypatch.setattr(K, "KY_TIMEOUT_S", 0.5)
    if trouble == "conflict":
        kyaction.begin(world.run_dir, invalidation_id(world), "ky.verdict.invalidate", K._actor(
            K._parse(world.invalidate_argv())), {"other": True}, {"other": True}, "another action under this id")
    elif trouble == "begin_conflict":
        def conflict(*a, **k):
            raise kyaction.ActionConflict("raced")
        monkeypatch.setattr(kyaction, "begin", conflict)
    else:
        world.mode(trouble)
    for _ in range(2):
        code, out = world.call(world.invalidate_argv())
        assert accepted_in_force(world) and code == 3 and out["published"] is False, (code, out)


def test_invalidate_an_acceptance_published_after_a_recorded_invalidation_is_unknown(world):
    """The record id is one per identity; a second invalidation cannot be recorded under it. Nothing is appended
    outside an action record and nothing is claimed: exit 3, the queue action may not proceed."""
    world.seed("ACCEPTED")
    assert world.call(world.invalidate_argv())[0] == 0
    world.seed("ACCEPTED", detail="job J-LATER; accepted again at the same head")
    code, out = world.call(world.invalidate_argv())
    assert code == 3 and out["published"] is False and tokens(out) == ["accepted_again_after_invalidation"]
    assert len(world.calls()) == 1


@pytest.mark.parametrize("over", [
    {"--head": None}, {"--artifact-digest": "0" * 64}, {"--reason": ""}, {"--reason": "  "}, {"--phase": "x"},
    {"--item": "a/b"}, {"--vslot": ""}, {"--as": ""}, {"--events": "relative.jsonl"}, {"--head": "abc"},
    {"--phase": "artifact"}, {"--job-id": JOB},
], ids=lambda over: ",".join("%s=%s" % (k, v) for k, v in over.items())[:60])
def test_usage_invalidate_arguments(world, over):
    world.seed("ACCEPTED")
    code, out = world.call(world.invalidate_argv(**over))
    assert code == 64 and out["published"] is False, out
    assert world.calls() == []


# ───────────────────────────────────── Contract B: inherit ─────────────────────────────────────

def test_inherit_cli_prints_the_result_and_publishes_nothing(scenario, world):
    new = scenario.merge_main()
    buffer = io.StringIO()
    env = {"KY_GIT": GIT, "PATH": "/usr/bin:/bin"}                # no KY_RUN, no ky: none is needed
    code = K.main(["inherit", "--repo", str(scenario.repo), "--old-head", scenario.old, "--new-head", new],
                  environ=env, stdout=buffer)
    assert code == 0
    assert json.loads(buffer.getvalue()) == {"inherits": True, "reason": "identical_patch", "old_head": scenario.old,
                                             "new_head": new, "old_base": scenario.b1, "new_base": scenario.m2}
    newer = commit(scenario.repo, "one more", {"c.txt": "x\n"})
    r = subprocess.run([PY, "-B", str(FLEET / "kyverdicts.py"), "inherit", "--repo", str(scenario.repo),
                        "--old-head", scenario.old, "--new-head", newer], capture_output=True, text=True, env=env)
    assert r.returncode == 1 and json.loads(r.stdout)["inherits"] is False
    assert json.loads(r.stdout)["reason"] == "patch_differs"
    r = subprocess.run([PY, "-B", str(FLEET / "kyverdicts.py"), "inherit", "--repo", str(scenario.repo),
                        "--old-head", scenario.old, "--new-head", new, "--old-base", scenario.b1,
                        "--new-base", scenario.m2], capture_output=True, text=True, env=env)
    assert r.returncode == 0 and json.loads(r.stdout)["inherits"] is True
    world.nothing_published()
    assert not (world.run_dir / "actions").exists()


def test_inherit_cli_is_negative_for_everything_it_cannot_prove(scenario, world):
    new = scenario.merge_main()
    for argv in (["--repo", str(scenario.repo / "absent"), "--old-head", scenario.old, "--new-head", new],
                 ["--repo", str(scenario.repo), "--old-head", "f" * 40, "--new-head", new],
                 ["--repo", str(scenario.repo), "--old-head", new, "--new-head", scenario.old]):
        code, out = world.call(["inherit", *argv])
        assert code == 1 and out["inherits"] is False and out["reason"] in K.REFUSALS, out
