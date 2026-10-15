"""kyd_admit.py (KV3-B-KYDADMIT, relaunch plan v2.7 §5 base contract, §6 admission, §8.6): every case of admit.json,
with ctx a recording double over throwaway repositories. git runs for real in those repositories; kypacket.py,
kyroute.py, local_db.sh and precheck.sh are answered by the case (their own packets test them). Nothing here touches
the real ky, gh, docker, a database or /Users/Dev/kalayantra."""
import copy
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys
import types
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
FLEET = HERE.parents[1]
sys.path.insert(0, str(FLEET))

import kyd_admit  # noqa: E402

DOC = json.loads((HERE / "admit.json").read_text(encoding="utf-8"))
CASES = DOC["cases"]
ABSENT = "$ABSENT"
CTL = "CTL-dispatcher-20261012T090000Z-4242"
NOW = datetime.datetime(2026, 10, 12, 9, 0, 0, tzinfo=datetime.timezone.utc)
DEADLINE_SECONDS = 10800
ASSERTION = "AssertionError: kala window is empty"
TEST_PATH = "tests/test_new.py"
TEST_BODY = "def test_new():\n    assert window(), 'kala window is empty'\n"
ZERO = "0" * 40
SEED = {"schema_sha256": "1" * 64, "ledger_sha256": "2" * 64, "registry_sha256": "3" * 64}
TURNS = {"build": 150, "verify": 60, "merge": 30}
# /usr/bin/git is a launcher on this platform (about 0.1 s a call); the tests run the program it resolves to. The
# module's own argv still says kyd_admit.GIT, which the double checks before it runs the command.
_found = subprocess.run(["/usr/bin/xcrun", "-f", "git"], capture_output=True, text=True) if os.path.exists("/usr/bin/xcrun") else None
REAL_GIT = _found.stdout.strip() if _found is not None and _found.returncode == 0 and os.path.isabs(_found.stdout.strip()) else "/usr/bin/git"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git_env(home):
    return {"PATH": "/usr/bin:/bin", "HOME": str(home), "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid", "GIT_COMMITTER_NAME": "t",
            "GIT_COMMITTER_EMAIL": "t@example.invalid", "GIT_AUTHOR_DATE": "2026-10-12T09:00:00Z",
            "GIT_COMMITTER_DATE": "2026-10-12T09:00:00Z"}


def merged(base, over):
    out = copy.deepcopy(base)
    for key, value in (over or {}).items():
        if value == ABSENT:
            out.pop(key, None)
        else:
            out[key] = value
    return out


class World:
    """One throwaway campaign: a repository with the commits the cases name, a run directory, a fleet directory and
    a worktree root, built from the case's `setup` on top of an admissible default."""

    def __init__(self, tmp, case, seed=None):
        self.tmp, self.call = Path(os.path.realpath(tmp)), case["call"]
        self.repo, self.run, self.fleet = self.tmp / "repo", self.tmp / "run", self.tmp / "fleet"
        self.scratch, self.wt = self.tmp / "scratch", self.tmp / "wt"
        for d in (self.run, self.fleet, self.scratch, self.wt, self.tmp / "packets"):
            d.mkdir()
        self.env = git_env(self.tmp)
        self.sym = {"$CTL": CTL, "$ZERO": ZERO, "$REPO": str(self.repo), "$DIGEST": sha(TEST_BODY.encode()),
                    "$DEADLINE": "2026-10-12T12:00:00Z"}
        if seed is None:
            self.repo.mkdir()
            self._commits()
            return
        shutil.copytree(seed.repo, self.repo, symlinks=True)
        self.sym.update({k: seed.sym[k] for k in ("$C0", "$H", "$S", "$T", "$OTHER", "$M2")})
        (self.fleet / "mcp.none.json").write_text('{"mcpServers":{}}\n')
        (self.fleet / "mcp.marsys-only.json").write_text('{"mcpServers":{"marsys":{}}}\n')
        self.sym.update({"$MCP_NONE": str(self.fleet / "mcp.none.json"),
                         "$MCP_MARSYS": str(self.fleet / "mcp.marsys-only.json"),
                         "$MCP_MARSYS_SHA": sha((self.fleet / "mcp.marsys-only.json").read_bytes())})
        self.setup = self.sub(case.get("setup") or {})
        s = self.setup
        self.git("checkout", "-q", "-B", "main", {"stack": self.sym["$H"], "squash": self.sym["$S"]}.get(
            s.get("base", "plain"), self.sym["$C0"]))
        self.sym["$BASE"] = self.git("rev-parse", "HEAD")
        self.intent = merged({"kind": "BUILD", "item": "K9-1", "role": "build", "pool": "builder", "tier": "sonnet",
                              "packet": str(self.tmp / "packets" / "PACKET_K9-1_v1.md"), "runner": "model",
                              "locks": ["item.K9-1"]}, s.get("intent"))
        self.slot = s["slot"] if "slot" in s else "b1"
        self.item_wt = self.wt / "kalayantra-k9-1"
        self.sym["$WT"] = str(self.item_wt)
        self._packet(s)
        self._model(s)
        self._qualifications(s)
        self._receipts(s)
        self._worktrees(s)
        self._prior_jobs(s)
        if self.call == "admit":
            self._job(s)

    def git(self, *args, cwd=None, check=True):
        p = subprocess.run([REAL_GIT, *args], cwd=str(cwd or self.repo), env=self.env, capture_output=True, text=True)
        if check and p.returncode != 0:
            raise AssertionError("git %s: %s" % (" ".join(args), p.stderr))
        return p.stdout.strip()

    def sub(self, value):
        if isinstance(value, dict):
            return {k: self.sub(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self.sub(v) for v in value]
        if isinstance(value, str) and "$" in value and value != ABSENT:
            for name in sorted(self.sym, key=len, reverse=True):
                value = value.replace(name, self.sym[name])
        return value

    def _commit(self, name, body, message):
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body)
        self.git("add", "--", name)
        self.git("commit", "-q", "-m", message)
        return self.git("rev-parse", "HEAD")

    def _commits(self):
        self.git("init", "-q", "-b", "main")
        c0 = self._commit("a.txt", "a\n", "first")
        self.git("checkout", "-q", "-b", "kalayantra/k8-1")
        h = self._commit("lib.txt", "lib\n", "K8-1 work")
        self.git("checkout", "-q", "-B", "landed", c0)
        s = self._commit("lib.txt", "lib\n", "K8-1 (#7), squashed")
        self.git("checkout", "-q", "-B", "tests", c0)
        t = self._commit(TEST_PATH, TEST_BODY, "K9-1 tests")
        self.git("checkout", "-q", "main")
        other = self.git("commit-tree", c0 + "^{tree}", "-p", c0, "-m", "other")
        m2 = self.git("commit-tree", h + "^{tree}", "-p", c0, "-p", h, "-m", "merge")
        self.sym.update({"$C0": c0, "$H": h, "$S": s, "$T": t, "$OTHER": other, "$M2": m2})

    def _packet(self, s):
        front = merged({"id": "K9-1", "kind": "feature", "needs_chart_data": False,
                        "test_commits": [{"sha": self.sym["$T"], "digest": self.sym["$DIGEST"], "path": TEST_PATH}],
                        "expected_failing_assertion": ASSERTION}, s.get("packet_front"))
        self.front = front
        text = "{not json" if s.get("packet_garbage") else json.dumps(front, indent=0)
        (self.tmp / "packets" / "PACKET_K9-1_v1.md").write_text("```json\n%s\n```\n# K9-1\n\nbody\n" % text)

    def _model(self, s):
        items = s.get("model_items", [
            {"id": "K9-1", "depends_on": s.get("depends_on", []), "completion_kind": "code",
             "brief": merged({"owns": ["platform/x.py"]}, {"migration": s["migration"]} if "migration" in s else {})},
            {"id": "K8-1", "depends_on": [], "completion_kind": "code", "brief": {}},
            {"id": "A-1", "depends_on": [], "completion_kind": "artifact", "brief": {}},
            # the plan model's joins and decisions carry no completion_kind; they stand for what lies beneath them
            {"id": "J-1", "depends_on": ["K8-1"], "join": True, "done_by": "join"},
            {"id": "D-2", "depends_on": ["K8-1"], "done_by": "decision", "decision": "D-2"},
            {"id": "D-1", "depends_on": ["J-1"], "done_by": "decision", "decision": "D-1"},
            {"id": "A-2", "depends_on": ["K8-1"], "completion_kind": "artifact", "brief": {}},
            {"id": "X-1", "depends_on": [], "completion_kind": "magic", "brief": {}},
            {"id": "J-U", "depends_on": ["NOPE-1"], "join": True, "done_by": "join"},
            {"id": "J-B", "depends_on": "K8-1", "join": True, "done_by": "join"},
            {"id": "J-C1", "depends_on": ["J-C2"], "join": True, "done_by": "join"},
            {"id": "J-C2", "depends_on": ["J-C1", "K8-1"], "join": True, "done_by": "join"}])
        self.model = self.tmp / "plan_model.json"
        self.model.write_text("{" if s.get("model_broken") else json.dumps({"items": items}))

    def _qualifications(self, s):
        if s.get("qual_absent"):
            return
        (self.run / "QUALIFICATIONS").mkdir()
        for role, turns in TURNS.items():
            for model in ("claude-sonnet-5-5", "claude-opus-5-5"):
                binds = merged({"model": model, "effort": "high", "permission_mode": "bypassPermissions",
                                "max_turns": turns, "deadline_seconds": DEADLINE_SECONDS, "claude_bin": "/opt/fake/claude",
                                "mcp_config_sha256": sha((self.fleet / "mcp.none.json").read_bytes()),
                                "extra_flags": ["--disable-slash-commands"], "disallowed_tools": ["Task", "WebFetch"]},
                               s.get("qual_binds"))
                doc = merged({"schema": "ky.qualification/1", "role": role, "model": model, "context": "launchd",
                              "result": "PASS", "binds": binds}, s.get("qual"))
                (self.run / "QUALIFICATIONS" / (kyd_admit.qualification_name(role, model,
                    self.setup.get("packet_front", {}).get("needs_chart_data", False),
                    bool((kyd_admit.front_matter(self.intent["packet"])[0] or {}).get("test_commits"))))).write_text(json.dumps(doc))

    def _receipts(self, s):
        (self.run / "local_db").mkdir()
        over = s.get("receipt", {})
        if over is None or not isinstance(self.slot, str) or "/" in self.slot or " " in self.slot:
            return
        doc = merged({"schema": "ky.slot_db/1", "slot": self.slot, "database": "ky_" + self.slot, "result": "READY",
                      "reason": None, "session_id": CTL, "container": {"name": "ky-pg", "id": "c0ffee"},
                      "mount_source": str(self.scratch / "db" / CTL / "pgdata"), "seed": SEED},
                     over if isinstance(over, dict) else {})
        (self.run / "local_db" / (self.slot + ".json")).write_text("{not json" if over == "garbage" else json.dumps(doc))

    def _worktrees(self, s):
        w = s.get("worktrees") or {}
        for i in range(w.get("own", 0)):
            self.git("worktree", "add", "-q", "--detach", str(self.wt / ("kalayantra-own-%d" % i)), "main")
        for i in range(w.get("other", 0)):
            self.git("worktree", "add", "-q", "--detach", str(self.wt / ("other-%d" % i)), "main")
        state = s.get("item_worktree", "ok") if self.call == "admit" else w.get("item")
        if state in (True, "ok", "stack", "wrong_branch"):
            branch = "elsewhere" if state == "wrong_branch" else "kalayantra/k9-1"
            self.git("worktree", "add", "-q", "-b", branch, str(self.item_wt), self.sym["$H"] if state == "stack" else "main")
            self.sym["$WTHEAD"] = self.git("rev-parse", "HEAD", cwd=self.item_wt)

    def _prior_jobs(self, s):
        for i, state in enumerate(s.get("prior_jobs") or []):
            d = self.run / "jobs" / ("J-20261011T00000%dZ-b1" % i)
            d.mkdir(parents=True)
            (d / "state.json").write_text("{not json" if state == "garbage" else json.dumps(
                merged({"schema": "ky.job/1", "job_id": d.name, "phase": "ended"}, state)))

    def _job(self, s):
        present = s.get("tests_present")
        if present and self.item_wt.is_dir():
            target = self.item_wt / TEST_PATH
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("def test_new():\n    assert True\n" if present == "different" else TEST_BODY)
            if present != "untracked":
                self.git("add", "--", TEST_PATH, cwd=self.item_wt)
                self.git("commit", "-q", "-m", "tests", cwd=self.item_wt)
        lock = s.get("lock", "own")
        if lock != "absent":
            d = self.run / "locks" / "item.K9-1"
            d.mkdir(parents=True)
            (d / "owner.json").write_text(json.dumps({"session_or_run_id": CTL if lock == "own" else "CTL-other", "pid": 1}))
        self.sym["$JOBBASE"] = self.git("rev-parse", "HEAD", cwd=self.item_wt) if self.item_wt.is_dir() else self.sym["$BASE"]
        self.job = merged({"job_id": "J-20261012T090000Z-b1", "item": "K9-1", "kind": "BUILD", "slot": "b1",
                           "worktree": str(self.item_wt), "branch": "kalayantra/k9-1", "base_sha": self.sym["$JOBBASE"],
                           "locks": ["item.K9-1"], "packet_path": str(self.tmp / "packets" / "PACKET_K9-1_v1.md"),
                           "test_digests": [d["digest"] for d in self.front.get("test_commits") or [] if isinstance(d, dict)],
                           "controller_id": CTL}, s.get("job"))

    def footprint(self):
        """Everything precheck may not change: every file of the run directory, of the repository (its .git with the
        refs, the index and the worktree registrations included), of the worktrees and of the scratch root."""
        return {str(p.relative_to(self.tmp)): sha(p.read_bytes()) if p.is_file() else "-"
                for root in (self.run, self.repo, self.wt, self.scratch) for p in sorted(root.rglob("*")) if not p.is_symlink()}


class Ctx:
    """The engine's ctx as KV3-B-KYDADMIT's contract names it; records every command, question and owner-wait."""

    def __init__(self, world):
        s, self.world = world.setup, world
        self.paths = types.SimpleNamespace(root=str(world.tmp), run=str(world.run), fleet=str(world.fleet),
                                           scratch=str(world.scratch), repo=str(world.repo))
        self.model, self.controller_id = str(world.model), CTL
        self.limits = merged({"builders": 6, "verifiers": 4, "copies": 10}, s.get("limits"))
        if s.get("next", {}) != ABSENT:
            self.next = s["next"] if "next" in s else {"version": 7, "ready": [{"id": "K9-1"}]}
        self.commands, self.calls, self.asked, self.waits = [], [], [], []

    def now(self):
        return self.world.setup["now"] if "now" in self.world.setup else NOW

    def sh(self, argv, env=None, cwd=None, timeout=120):
        assert all(isinstance(a, str) for a in argv), argv
        assert cwd is None or os.path.isabs(str(cwd)), cwd
        if argv[0] == kyd_admit.GIT:
            p = subprocess.run([REAL_GIT] + argv[1:], cwd=cwd, env=dict(self.world.env, **(env or {})), capture_output=True, text=True)
            return p.returncode, p.stdout, p.stderr
        self.calls.append({"argv": list(argv), "env": env, "cwd": cwd, "timeout": timeout})
        script = next(a for a in argv if a.endswith((".py", ".sh")))
        assert os.path.dirname(script) == str(self.world.fleet), script
        name, rest = os.path.basename(script), argv[argv.index(script) + 1:]
        self.commands.append(" ".join([name] + rest))
        s = self.world.setup
        if name == "kypacket.py":
            reply = merged({"rc": 0}, s.get("packet"))
            out = json.dumps({"schema": "ky.packet_check/1", "packet": rest[1], "id": "K9-1",
                              "admitted": reply.get("admitted", reply["rc"] == 0), "reasons": reply.get("reasons", [])})
        elif name == "kyroute.py":
            reply = merged({"rc": 0, "tier": "sonnet"}, s.get("route"))
            out = json.dumps({"mode": "packet", "decision": {0: "ROUTE", 3: "STOP"}.get(reply["rc"]),
                              "tier": reply["tier"] if reply["rc"] == 0 else None, "frozen": reply.get("frozen", [])})
        elif name == "local_db.sh":
            reply = merged({"rc": 0}, s.get({"check": "db_check", "up": "up", "db": "db"}[rest[0]]))
            out = "ky_%s READY\n" % self.world.slot
        elif name == "precheck.sh":
            reply = merged({"rc": 1, "out": "%s\nPRECHECK RED\n" % ASSERTION}, s.get("precheck"))
            out = ""
        else:
            raise AssertionError("unexpected command %r" % (argv,))
        if reply["rc"] is None:
            return None, "", "timed out"
        return reply["rc"], reply.get("out", out), ""

    def pr(self, item):
        self.asked.append(item)
        return (self.world.setup.get("pr") or {}).get(item)

    def accepted(self, item):
        self.asked.append(item)
        return (self.world.setup.get("accepted") or {}).get(item)

    def awaiting(self, slug, question, options, evidence, item, class_hint):
        assert question and isinstance(options, list) and options and all(set(o) == {"id", "text"} for o in options)
        assert isinstance(evidence, list) and class_hint in ("routine", "veto", "hard_stop", "unknown")
        self.waits.append(slug)


def subset(want, got, where="facts"):
    if isinstance(want, dict):
        assert isinstance(got, dict), "%s: %r is not an object" % (where, got)
        for key, value in want.items():
            assert key in got, "%s: no %s in %r" % (where, key, sorted(got))
            subset(value, got[key], "%s.%s" % (where, key))
    elif isinstance(want, list):
        assert isinstance(got, list) and len(got) == len(want), "%s: %r != %r" % (where, got, want)
        for i, value in enumerate(want):
            subset(value, got[i], "%s[%d]" % (where, i))
    else:
        assert got == want and type(got) is type(want), "%s: %r != %r" % (where, got, want)


@pytest.fixture(autouse=True)
def worktree_root(monkeypatch, tmp_path):
    monkeypatch.setattr(kyd_admit, "WORKTREE_ROOT", os.path.join(os.path.realpath(tmp_path), "wt"))


@pytest.fixture(scope="session")
def seed(tmp_path_factory):
    """The commits every case names, made once; each case works on its own copy."""
    return World(tmp_path_factory.mktemp("seed"), {"call": "seed"})


def run_case(tmp_path, case, seed):
    world = World(tmp_path, case, seed)
    kyd_admit.WORKTREE_ROOT = str(world.wt)         # restored by the worktree_root fixture
    ctx = Ctx(world)
    if case["call"] == "precheck":
        before = world.footprint()
        result = kyd_admit.precheck(ctx, world.intent, world.slot)
        assert world.footprint() == before, "precheck is read-only"
    elif case["call"] == "provision":
        result = kyd_admit.provision(ctx, world.slot)
    else:
        result = kyd_admit.admit(ctx, world.job)
    return world, ctx, result


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_case(tmp_path, case, seed):
    world, ctx, result = run_case(tmp_path, case, seed)
    want = world.sub(case["expect"])
    assert set(result) == {"admitted", "refusals", "facts"}
    for r in result["refusals"]:
        assert set(r) == {"code", "detail"} and isinstance(r["code"], str) and isinstance(r["detail"], str) and r["detail"]
    codes = sorted({r["code"] for r in result["refusals"]})
    assert codes == want["codes"], result["refusals"]
    assert result["admitted"] is want["admitted"]
    assert result["admitted"] is (not result["refusals"])
    subset(want.get("facts", {}), result["facts"])
    details = {}
    for r in result["refusals"]:
        details.setdefault(r["code"], []).append(r["detail"])
    for code, text in want.get("detail_contains", {}).items():
        assert any(text in d for d in details[code]), details[code]
    for text in want.get("ran", []):
        assert any(text in c for c in ctx.commands), ctx.commands
    for text in want.get("not_ran", []):
        assert not any(text in c for c in ctx.commands), ctx.commands
    if "ran_exactly" in want:
        assert ctx.commands == want["ran_exactly"]
    if "awaiting" in want:
        assert ctx.waits == want["awaiting"]
    for item in want.get("not_asked", []):
        assert item not in ctx.asked
    if case["call"] != "admit":
        return
    admission = world.run / "admission" / "K9-1.json"
    if "admission" in want:
        if want["admission"] is None:
            assert not admission.exists()
        else:
            assert json.loads(admission.read_text()) == want["admission"]
    if world.item_wt.is_dir():
        head_before = world.sym["$JOBBASE"]
        head = world.git("rev-parse", "HEAD", cwd=world.item_wt)
        if want.get("committed") is True:
            assert head != head_before and world.git("rev-list", "--count", "%s..%s" % (head_before, head), cwd=world.item_wt) == "1"
            assert world.git("show", "--name-only", "--format=", head, cwd=world.item_wt) == TEST_PATH
            assert sha((world.item_wt / TEST_PATH).read_bytes()) == world.sym["$DIGEST"]
            assert world.git("status", "--porcelain", cwd=world.item_wt) == ""
        elif want.get("committed") is False:
            assert head == head_before
        if want.get("clean"):
            assert world.git("status", "--porcelain", cwd=world.item_wt) == "" and not (world.item_wt / TEST_PATH).exists()
    if "precheck_env" in want:
        call = [c for c in ctx.calls if c["argv"][-2:] == [str(world.fleet / "precheck.sh"), "--item"]]
        assert len(call) == 1 and call[0]["env"] == want["precheck_env"] and call[0]["cwd"] == str(world.item_wt)
        assert call[0]["argv"] == ["bash", str(world.fleet / "precheck.sh"), "--item"] and call[0]["timeout"] >= 600


def exact(prefix, call="precheck"):
    return [c for c in CASES if c["call"] == call and c["expect"]["codes"] == [prefix]]


def test_fixture_covers_the_acceptance():
    """admit.json holds what the packet's Acceptance line lists; a deleted case fails here, not silently."""
    assert DOC["schema"] == "ky.test.admit/1" and len({c["name"] for c in CASES}) == len(CASES)
    admitted = [c for c in CASES if c["call"] == "precheck" and c["expect"]["admitted"]]
    pools = {(c["setup"].get("intent") or {}).get("pool", "builder") for c in admitted}
    assert pools >= {"builder", "verifier", None}
    for code in kyd_admit.PRECHECK_CODES:
        assert exact(code), "no precheck case refused with %s alone" % code
    for code in kyd_admit.ADMIT_CODES:
        assert exact(code, "admit"), "no admit case refused with %s alone" % code
    for code in ("slot_not_ready", "slot_foreign"):
        assert exact(code, "provision")
    names = " | ".join(c["name"] for c in CASES)
    for needle in ("accepted unmerged stack", "squash-landed prerequisite", "missing code", "incorrect mapping",
                   "changed mapping", "KU-02 wrong mount", "KU-02 stale READY receipt", "KU-02 ownership conflict",
                   "expected-red", "already-green", "unclassified", "migration present", "migration NONE",
                   "tests and digests absent", "join over code", "decision over code", "unknown dependency",
                   "head in base, PR MERGED, merge commit not a commit here"):
        assert needle in names, needle
    stale = [c for c in CASES if c["expect"]["codes"] == ["stale"]]
    assert {(c["setup"].get("intent") or {}).get("pool", "builder") for c in stale} >= {"builder", "verifier", None}
    results = {(c["expect"].get("facts") or {}).get("result") for c in CASES if c["call"] == "admit"}
    assert results >= {"expected_red", "already_green", "unclassified", None}


def test_command_lines(tmp_path, seed):
    """The four commands are the ones their packets fix, argument for argument."""
    world, ctx, result = run_case(tmp_path, {"call": "precheck", "setup": {}}, seed)
    assert result["admitted"], result["refusals"]
    fleet, packet = str(world.fleet), world.intent["packet"]
    assert [c["argv"] for c in ctx.calls] == [
        ["python3", "-B", fleet + "/kypacket.py", "check", packet, "--repo", str(world.repo)],
        ["python3", "-B", fleet + "/kyroute.py", "packet", "--packet", packet, "--model", str(world.model), "--repo", str(world.repo)],
        ["bash", fleet + "/local_db.sh", "check", "b1"]]
    assert all(c["env"] is None for c in ctx.calls)


@pytest.mark.parametrize("now, want", [
    (datetime.datetime(2026, 10, 12, 9, 0, 0), "2026-10-12T12:00:00Z"),
    (datetime.datetime(2026, 10, 12, 14, 30, 0, tzinfo=datetime.timezone(datetime.timedelta(hours=5, minutes=30))), "2026-10-12T12:00:00Z"),
    (1791795600, "2026-10-12T12:00:00Z"),
    (True, None), ("2026-10-12T09:00:00Z", None), (float("nan"), None)])
def test_deadline_is_utc_text_or_unknown(now, want):
    assert kyd_admit.deadline_text(now, DEADLINE_SECONDS) == want


def test_facts_keys_are_the_ones_kyd_jobs_reads(tmp_path, seed):
    world, ctx, result = run_case(tmp_path, {"call": "precheck", "setup": {}}, seed)
    assert set(result["facts"]) == {"tier", "launch", "base_sha", "prerequisites", "tests", "test_digests", "migration"}
    assert set(result["facts"]["launch"]) == {"model", "effort", "permission_mode", "max_turns", "deadline", "claude_bin",
                                             "mcp_config", "extra_lean_flags", "disallowed_tools"}


def test_refused_precheck_never_carries_launch_facts(tmp_path, seed):
    """A refused launch check leaves facts.launch null: no half-built launch configuration reaches a job state."""
    for case in CASES:
        if case["call"] == "precheck" and "launch" in case["expect"]["codes"]:
            d = tmp_path / str(CASES.index(case))
            d.mkdir()
            _, _, result = run_case(d, case, seed)
            assert result["facts"]["launch"] is None, case["name"]
