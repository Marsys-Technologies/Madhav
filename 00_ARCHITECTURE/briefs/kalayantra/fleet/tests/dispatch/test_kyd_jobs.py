"""kyd_jobs.py — the dispatcher's job lifecycle (relaunch plan v2.7 §5 KT-08, §6 "Claims, locks, renewals",
"Terminal release (KT-07)", "Failure accounting"; packet KV3-B-KYDJOBS v1).

Every case of jobs.json is one scripted life of one or more jobs: its `steps` are run in order against a
recording ctx double, and the case passes only when each job ends in its expected state sequence (every
persisted phase, in order, `ended:<outcome>` last) and the recorded tracker calls, shell calls, owner-waits,
handled records and job keys are the expected ones. The jobs themselves are real processes: a fake kyjob.sh,
written into the case's own fleet folder, plays the behaviour the step names (done, blocked, a refusal, a quota
refusal, a sleeper, a sleeper that ignores TERM, a leader that leaves a member behind).

Nothing here touches /Users/Dev/kalayantra, the real `ky`, `gh`, `git`, `claude`, launchctl, a database or the
network. ctx.ky is a small claim tracker over <run>/claims/<slot>.json (the file `ky release` itself reads);
ctx.sh records its argv and answers from the case's replies; ctx.act is built over the real kyaction.py. A
"restart" is a new ctx with a new controller_id and no child handles; a "crash" is an exception thrown out of
the module's own state write, before or after the write that marks a close step.

Signals: the only groups ever signalled are those this test started through kyd_jobs.launch, known by pid and
start identity; whatever is still running when a case ends is killed by that identity and reaped.
"""
import copy
import json
import os
import re
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

HERE = Path(__file__).resolve().parent
FLEET = HERE.parents[1]
sys.path.insert(0, str(FLEET))

import kyaction as ka  # noqa: E402
import kyloop  # noqa: E402
import kyd_jobs as J  # noqa: E402

CASES = json.loads((HERE / "jobs.json").read_text(encoding="utf-8"))
SHA_A, SHA_B, SHA_C = "a" * 40, "b" * 40, "c" * 40

FAKE_KYJOB = r"""#!/bin/bash
# a fake job: plays the behaviour the test wrote into its scratch folder
S="$KY_SCRATCH/jobs/$1"
B="$(cat "$S/behaviour" 2>/dev/null)"
ITEM="$(cat "$S/item" 2>/dev/null)"
result() {
  printf '{"schema":"ky.job_result/1","job_id":"%s","item":"%s","status":"%s","branch":null,"head_sha":null,"pr_number":null,"tests":[],"blocked_reason":%s,"notes":""}\n' \
    "$1" "$ITEM" "$2" "$3" > "$S/result.json"
}
printf '{"type":"system","subtype":"init","session_id":"sess-%s"}\n' "$1" > "$S/stdout.jsonl"
case "$B" in
  done) result "$1" done null
        printf '{"type":"result","subtype":"success","is_error":false,"num_turns":3,"usage":{"input_tokens":7}}\n' >> "$S/stdout.jsonl"
        exit 0 ;;
  blocked) result "$1" blocked '"freeze: fleet/FROZEN_PATHS.txt"'; exit 0 ;;
  failed) result "$1" failed null; exit 1 ;;
  noresult) exit 0 ;;
  otherjob) result "J-19700101T000000Z-zz" done null; exit 0 ;;
  symlink) result "$1" done null; mv "$S/result.json" "$S/elsewhere.json"; ln -s "$S/elsewhere.json" "$S/result.json"; exit 0 ;;
  refuse) printf '{"job_id":"%s","code":65,"reason":"state: launch key model is absent","at":"2026-10-12T00:00:00Z"}\n' "$1" > "$S/kyjob.refusal.json"
          echo "kyjob.sh: REFUSED 65 state" >&2; exit 65 ;;
  quota) printf '{"type":"rate_limit_event","rate_limit_info":{"status":"rejected","rateLimitType":"five_hour"}}\n' >> "$S/stdout.jsonl"
         exit 1 ;;
  sleep) exec /bin/sleep 600 ;;
  ignore_term) trap '' TERM; exec /bin/sleep 600 ;;
  survivor) /bin/sleep 600 & exit 0 ;;
  *) exit 99 ;;
esac
"""


class Crash(BaseException):
    """The controller dies here. Not an Exception: nothing in the module may catch it and carry on."""


class Log:
    def __init__(self):
        self.ky, self.sh, self.awaiting, self.journal = [], [], [], []


class Ctx:
    """The recording double of the engine's ctx (packet "Contract")."""

    def __init__(self, world, controller_id):
        self.world, self.controller_id = world, controller_id
        self.root, self.run, self.fleet = world.root, world.run, world.fleet
        self.scratch, self.repo = world.scratch, world.repo

    # ---- sh: recorded, answered from the case's replies, else by what the real command would leave behind
    def sh(self, argv, env=None, cwd=None, timeout=120):
        line = " ".join(str(a) for a in argv)
        self.world.log.sh.append(line)
        for rule in self.world.replies:
            if rule["match"] in line:
                return rule.get("rc", 0), rule.get("out", ""), rule.get("err", "")
        if " worktree add " in line:
            path = next(a for a in argv if str(a).startswith(str(self.world.worktrees)))
            os.makedirs(path)
            return 0, "", ""
        if " worktree remove " in line:
            os.rmdir(argv[-1])
            return 0, "", ""
        if "rev-parse" in line:
            return 1, "", ""                     # the branch does not exist yet
        if "kyalloc.py" in line:
            return 0, json.dumps({"item": "x", "branch": "y", "numbers": [1401], "status": "active",
                                  "reused": False, "claim_row": "| 1401 |"}), ""
        return 0, "", ""

    # ---- ky: a claim tracker over <run>/claims/<worker>.json, as pravaha_tracker's claims.py keeps it
    def ky(self, *args, stream=None, lane=None):
        world = self.world
        world.log.ky.append("%s [%s/%s]" % (" ".join(str(a) for a in args), stream, lane))
        lost = False
        for rule in world.ky_replies:
            if rule["match"] == args[0]:
                if rule.get("then") != "lost":
                    return rule.get("rc", 2), rule.get("out", ""), rule.get("err", "refused: by the case")
                lost = True                               # the verb happens; its answer never arrives
        path = world.run / "claims" / ("%s.json" % lane)
        current = json.loads(path.read_text()) if path.exists() else None
        active = current is not None and current["state"] in ("acquired", "renewed")
        if args[0] == "claim":
            if active:
                return 2, "", "refused: worker already holds an active claim"
            world.claims += 1
            event = {"kind": "claim", "actor": "stream-%s:%s" % (stream, lane), "item": args[1], "state": "acquired",
                     "worker_id": lane, "claim_id": "claim-%d" % world.claims, "lease_s": 10800}
        elif args[0] in ("renew", "release"):
            if not active:
                return 2, "", "refused: claim is not active for this worker"
            event = dict(current, state="renewed" if args[0] == "renew" else "released")
        else:
            return 64, "", "usage"
        os.makedirs(path.parent, exist_ok=True)
        path.write_text(json.dumps(event))
        return (None, "", "") if lost else (0, json.dumps(event) + "\n", "")

    # ---- act: kyaction's record around a side effect (effect() → (done | failed | unknown, result))
    def act(self, action_id, kind, inputs, target, effect, observer):
        actor = {"role": "dispatcher", "holder_kind": "controller", "controller_id": self.controller_id}
        status, record = ka.begin(self.run, action_id, kind, actor, inputs, target, kind)
        if status in ("done", "failed"):
            return status, record["result"]
        if status == "in_progress":
            return "unknown", {"reason": "another actor is in the middle of it"}
        if status == "unfinished":
            outcome, after = ka.reconcile(self.run, action_id, observer, by=self.controller_id)
            if outcome == "done":
                return "done", after["result"]
            if outcome != "not_done":
                return "unknown", {"reason": "reconciliation: %s" % outcome}
        outcome, result = effect()
        if outcome == "done":
            ka.complete(self.run, action_id, result)
        elif outcome == "failed":
            ka.fail(self.run, action_id, result)
        return outcome, result

    def awaiting(self, slug, question, options, evidence, item, class_hint):
        assert re.match(r"^[a-z0-9-]+\Z", slug), slug
        assert isinstance(question, str) and question and isinstance(options, list) and isinstance(evidence, list)
        assert class_hint in ("routine", "veto", "hard_stop", "unknown")
        self.world.log.awaiting.append({"slug": slug, "question": question, "item": item})

    def journal(self, event, text):
        self.world.log.journal.append("%s: %s" % (event, text))


class World:
    def __init__(self, tmp, monkeypatch):
        self.root = tmp / "kalayantra"
        self.run, self.fleet = self.root / "run", self.root / "fleet_live"
        self.scratch, self.repo, self.worktrees = tmp / "scratch", tmp / "repo", tmp / "worktrees"
        for d in (self.run, self.fleet, self.scratch, self.repo, self.worktrees):
            os.makedirs(d)
        (self.fleet / "kyjob.sh").write_text(FAKE_KYJOB)
        (self.fleet / "card.md").write_text("card: TEST\n- one rule\n")
        (self.fleet / "packet.md").write_text("# PACKET T v1\nbody without a final newline")
        monkeypatch.setattr(J, "WORKTREES", str(self.worktrees))
        monkeypatch.setattr(J, "TERM_WAIT_S", 1.0)
        monkeypatch.setattr(J, "_CHILDREN", {})
        self.log, self.replies, self.ky_replies, self.claims = Log(), [], [], 0
        self.jobs, self.procs, self.states, self.steps_seen = {}, {}, {}, {}
        self.crash_after = self.crash_before = None
        self.ctx = Ctx(self, "CTL-dispatcher-20261012T000000Z-1")
        self.lstart, self.stop = {}, threading.Event()
        threading.Thread(target=self.reap, daemon=True).start()
        real_save = J._save

        def saving(ctx, job):
            jid = job["job_id"]
            marked = set(((job.get("checkpoint") or {}).get("steps") or {}))
            new = marked - self.steps_seen.get(jid, set())
            if self.crash_before in new:
                self.crash_before = None
                raise Crash("before the write that marks %s" % sorted(new))
            real_save(ctx, job)
            self.steps_seen[jid] = marked
            label = "ended:%s" % job["outcome"] if job["phase"] == "ended" else job["phase"]
            seq = self.states.setdefault(jid, [])
            if not seq or seq[-1] != label:
                seq.append(label)
            if self.crash_after in new:
                self.crash_after = None
                raise Crash("after the write that marks %s" % sorted(new))

        monkeypatch.setattr(J, "_save", saving)

    # ---- helpers
    def fill(self, value):
        if isinstance(value, dict):
            return {k: self.fill(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self.fill(v) for v in value]
        if isinstance(value, str) and value.startswith("@"):
            return {"@card": str(self.fleet / "card.md"), "@packet": str(self.fleet / "packet.md"),
                    "@future": ka.utc(time.time() + 3600), "@past": ka.utc(time.time() - 60),
                    "@long_ago": ka.utc(time.time() - 7200), "@mcp": str(self.fleet / "mcp.none.json"),
                    "@A": SHA_A, "@B": SHA_B, "@C": SHA_C}[value]
        return value

    def intent(self, given):
        given = self.fill(given)
        kind, item = given.get("kind", "BUILD"), given["item"]
        base = {"kind": kind, "item": item, "stream": "K", "role": kind.lower(), "pool": "builder", "runner": "model",
                "claim": "K", "locks": ["item.%s" % item], "head": None, "digest": None, "verdict_phase": None,
                "evidence_fp": None, "card": str(self.fleet / "card.md"), "packet": str(self.fleet / "packet.md"),
                "header": {"loop": 1, "max_loops": 3}}
        if kind == "VERIFY":
            base.update(stream="V", pool="verifier", claim=None, head=SHA_A, verdict_phase="pre_merge")
        if kind == "REGEN":
            base.update(pool=None, runner="script", claim=None, card=None, packet=None)
        base.update(given)
        base.setdefault("key", "%s.%s.%s" % (kind, item, ka.sha_bytes(ka.canonical(
            [base["head"] or base["digest"], base["evidence_fp"]]))[:12]))
        return base

    def facts(self, given, drop=()):
        base = {"tier": "opus", "base_sha": SHA_B, "prerequisites": [], "tests": [], "test_digests": [],
                "migration": None,
                "launch": {"model": "claude-opus-5-5", "effort": "high", "permission_mode": "bypassPermissions",
                           "max_turns": 150, "deadline": "@future", "claude_bin": "/Users/Dev/.local/bin/claude",
                           "mcp_config": "@mcp", "extra_lean_flags": ["--disable-slash-commands"],
                           "disallowed_tools": ["WebFetch"]}}
        base.update(given or {})
        for key in drop:
            base.pop(key, None)
        return self.fill(base)

    def state(self, alias):
        return json.loads((self.run / "jobs" / self.jobs[alias] / "state.json").read_text())

    def patch(self, alias, change):
        path = self.run / "jobs" / self.jobs[alias] / "state.json"
        doc = json.loads(path.read_text())
        doc.update(self.fill(change))
        path.write_text(json.dumps(doc))

    def process_state(self, alias):
        s = self.state(alias)
        proc = self.procs.get(s["job_id"])
        if proc is not None:
            proc.poll()                                   # the test is the parent: it collects what has exited
        return kyloop.job_state(proc.pid, proc.pid, self.lstart[proc.pid]) if proc is not None else "unknown"

    def reap(self):
        """Collect whatever has exited, as launchd does for a job whose controller is gone: the test process is
        every job's parent, and a leader nobody collects would stay "unknown" for ever."""
        while not self.stop.wait(0.05):
            for proc in list(self.procs.values()):
                proc.poll()

    def slug(self, alias):
        return re.sub(r"[^a-z0-9-]", "-", self.jobs[alias].lower())

    def named(self, value, slugs=False):
        """`<alias>` in an expectation stands for that job's id (in an owner-wait slug: its slug form)."""
        if isinstance(value, dict):
            return {k: self.named(v, slugs) for k, v in value.items()}
        if isinstance(value, list):
            return [self.named(v, slugs) for v in value]
        if isinstance(value, str):
            for alias in self.jobs:
                value = value.replace("<%s>" % alias, self.slug(alias) if slugs else self.jobs[alias])
        return value

    def cleanup(self):
        """Kill what this test started and is still there — the group of a leader that still runs with the start
        identity recorded at launch, or the group a gone leader left members in — then collect it."""
        self.stop.set()
        for proc in self.procs.values():
            proc.poll()
            state = kyloop.job_state(proc.pid, proc.pid, self.lstart.get(proc.pid))
            if state in ("live", "survivors"):
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except OSError:
                    pass
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                pass


@pytest.fixture
def world(tmp_path, monkeypatch):
    for name in ("KY_ROOT", "KY_RUN", "KY_FLEET", "KY_SCRATCH"):       # nothing may fall back to the live tree
        monkeypatch.setenv(name, str(tmp_path / "guard"))
    w = World(tmp_path, monkeypatch)
    yield w
    w.cleanup()


def wait_for(predicate, seconds=10.0):
    end = time.time() + seconds
    while time.time() < end:
        if predicate():
            return True
        time.sleep(0.05)
    return predicate()


# ───────────────────────────── the interpreter of jobs.json ─────────────────────────────

def run_step(world, step):
    op = step["op"]
    if op == "open":
        before = set(os.listdir(world.run / "jobs")) if os.path.isdir(world.run / "jobs") else set()
        job = J.open(world.ctx, world.intent(step["intent"]), step.get("slot"),
                     world.facts(step.get("facts"), step.get("drop_facts", ())))
        assert (job is not None) == (step.get("expect", "job") == "job"), "open: %r, %s" % (job, world.log.journal[-3:])
        if job is not None:
            world.jobs[step["as"]] = job["job_id"]
            assert job["phase"] == "prepared" and job["pid"] is None
        else:                                             # a refused open may leave the record of a refused job
            left = [n for n in sorted(os.listdir(world.run / "jobs")) if n not in before and n.startswith("J-")] \
                if os.path.isdir(world.run / "jobs") else []
            assert len(left) <= 1
            for name in left:
                world.jobs[step["as"]] = name
                assert world.state(step["as"])["phase"] == "ended", "a refused open left a job that is not ended"
    elif op == "launch":
        s = world.state(step["job"])
        Path(s["job_scratch"], "behaviour").write_text(step["behaviour"])
        Path(s["job_scratch"], "item").write_text(s["item"])
        before = dict(J._CHILDREN)
        after = J.launch(world.ctx, s)
        assert after["phase"] == step.get("expect_phase", "live"), after
        for jid, proc in J._CHILDREN.items():
            if jid not in before:
                world.procs[jid] = proc
                world.lstart[proc.pid] = after["process_start"]
    elif op == "wait":
        assert wait_for(lambda: world.process_state(step["job"]) == step["for"]), \
            "%s is %s, not %s" % (step["job"], world.process_state(step["job"]), step["for"])
    elif op == "supervise":
        got = sorted(j["job_id"] for j in J.supervise(world.ctx))
        if "expect" in step:
            assert got == sorted(world.jobs[a] for a in step["expect"]), (got, world.jobs)
    elif op == "recover":
        got = {j["job_id"]: j for j in J.recover(world.ctx)}
        if "expect" in step:
            assert sorted(got) == sorted(world.jobs[a] for a in step["expect"]), (sorted(got), world.jobs)
    elif op == "close":
        world.crash_after, world.crash_before = step.get("crash_after"), step.get("crash_before_persist")
        result = world.fill(step.get("result"))
        if world.crash_after or world.crash_before:
            with pytest.raises(Crash):
                J.close(world.ctx, world.state(step["job"]), result)
        else:
            after = J.close(world.ctx, world.state(step["job"]), result)
            assert after["phase"] == step.get("expect_phase", "ended"), after
        assert world.crash_after is None and world.crash_before is None, "the crash point was never reached"
    elif op == "restart":
        J._CHILDREN.clear()                               # a new process holds no child handle
        if step.get("owners_gone"):                       # as a real restart leaves them: the old pid is gone
            pid, start = gone_owner()
            for name in sorted(os.listdir(world.run / "locks")):
                if not name.startswith("."):
                    rewrite_owner(world, name, pid=pid, pgid=pid, process_start=start)
        world.ctx = Ctx(world, step["controller"])
    elif op == "set":
        world.patch(step["job"], step["patch"])
    elif op == "claim_file":
        path = world.run / "claims" / ("%s.json" % step["slot"])
        if step.get("remove"):
            path.unlink()
        else:
            path.write_text(json.dumps(dict(json.loads(path.read_text()), **step["patch"])))
    elif op == "reply":
        world.replies.insert(0, {k: v for k, v in step.items() if k != "op"})
    elif op == "ky_reply":
        world.ky_replies.insert(0, {k: v for k, v in step.items() if k != "op"})
    elif op == "unreply":
        world.replies[:] = [r for r in world.replies if r["match"] != step["match"]]
        world.ky_replies[:] = [r for r in world.ky_replies if r["match"] != step["match"]]
    elif op == "attempts":
        assert J.attempts(world.ctx, world.intent(step["intent"])) == step["expect"]
    elif op == "expect":
        check(world, step)
    else:
        raise AssertionError("unknown op %r" % op)


def check(world, want):
    if "states" in want:
        assert {a: world.states.get(world.jobs[a]) for a in want["states"]} == want["states"]
    if "ky" in want:
        assert world.log.ky == want["ky"]
    for needle in want.get("sh", []):
        assert any(world.named(needle) in line for line in world.log.sh), (needle, world.log.sh)
    for needle in want.get("sh_absent", []):
        assert not any(world.named(needle) in line for line in world.log.sh), (needle, world.log.sh)
    if "awaiting" in want:
        assert [a["slug"] for a in world.log.awaiting] == world.named(want["awaiting"], slugs=True), world.log.awaiting
    for needle in want.get("question", []):
        assert any(needle in a["question"] for a in world.log.awaiting), (needle, world.log.awaiting)
    for alias, there in want.get("handled", {}).items():
        key = world.state(alias)["key"]
        assert (world.run / "handled" / ("job.%s.json" % key)).exists() is there, (alias, there)
    for alias, state in want.get("process", {}).items():
        assert world.process_state(alias) == state, (alias, world.process_state(alias))
    for alias, keys in want.get("job", {}).items():
        s = world.state(alias)
        assert {k: s[k] for k in keys} == world.named(world.fill(keys)), {k: s[k] for k in keys}
    for name, there in want.get("locks", {}).items():
        assert os.path.isdir(world.run / "locks" / name) is there, (name, sorted(os.listdir(world.run / "locks")))
    for name, alias in want.get("lock_owner", {}).items():   # the lock is still that job's, bound to its key
        owner = json.loads((world.run / "locks" / name / "owner.json").read_text())
        assert owner["session_or_run_id"].endswith(":job.%s" % world.state(alias)["key"]), (name, owner)
    if "failures" in want:
        got = json.loads((world.run / "jobs" / "failures.json").read_text())
        slim = {item: {fp: {"count": e["count"], "evidence_fp": e["evidence_fp"]} for fp, e in fps.items()}
                for item, fps in got.items()}
        assert slim == want["failures"]
    for alias, keys in want.get("prompt_header", {}).items():
        s = world.state(alias)
        prompt = Path(s["prompt_path"]).read_bytes()
        card, packet = Path(s["card_path"]).read_bytes(), Path(s["packet_path"]).read_bytes()
        assert prompt.startswith(card)                              # as kyjob.sh checks it
        rest = prompt[len(card):].lstrip(b"\n")
        assert rest.startswith(packet)
        rest = rest[len(packet):].lstrip(b"\n")
        assert rest.startswith(b"--- job header ---\n")
        header = json.loads(rest[len(b"--- job header ---\n"):])
        assert header["job_id"] == s["job_id"]
        for key in ("item", "worktree", "branch", "base_sha", "deadline"):
            assert header[key] == s[key]
        assert {k: header[k] for k in keys} == world.fill(keys), header


@pytest.mark.parametrize("case", CASES["cases"], ids=[c["name"] for c in CASES["cases"]])
def test_case(world, case):
    for n, step in enumerate(case["steps"]):
        try:
            run_step(world, step)
        except AssertionError as e:
            raise AssertionError("%s step %d (%s): %s\njournal: %s" % (case["name"], n, step["op"], e,
                                                                       world.log.journal[-6:])) from e
    check(world, case["expect"])
    assert case["expect"].get("states"), "a case names the state sequence its jobs end in"
    for alias in world.jobs:                              # every job a case opened is accounted for
        assert alias in case["expect"]["states"], "%s: no expected state sequence for %s" % (case["name"], alias)


def test_the_packet_acceptance_list_is_covered_by_cases():
    """Each line of the packet's Acceptance names at least one case (by the tag the case carries)."""
    tags = {t for c in CASES["cases"] for t in c["covers"]}
    wanted = {"kt07.three_successive_builds", "kt07.immediate_rework", "kt07.blocked_exit", "kt07.restart",
              "negative.one_release", "negative.other_claim_id", "negative.unknown_process",
              "recover.gone", "recover.live", "recover.unknown", "recover.prepared", "recover.terminating",
              "refusal_after_open", "facts.with", "facts.without", "counts_survive_restart", "regen.base_sha"}
    assert wanted <= tags, sorted(wanted - tags)
    restarts = {c["steps"][i].get("crash_after") for c in CASES["cases"] if "kt07.restart" in c["covers"]
                for i in range(len(c["steps"]))} - {None}
    assert restarts == set(J.CLOSE_STEPS[:-1]), "a restart between each pair of close steps: %s" % sorted(restarts)
    names = [c["name"] for c in CASES["cases"]]
    assert len(names) == len(set(names))


# ───────────────────────────── what a case file does not say well ─────────────────────────────

def opened(world, item="K-1", slot="b1", **intent):
    job = J.open(world.ctx, world.intent(dict(intent, item=item)), slot, world.facts(None))
    assert job is not None, world.log.journal
    world.jobs[item] = job["job_id"]
    return job


def test_a_job_state_holds_exactly_the_pinned_keys_and_absolute_paths(world):
    job = opened(world)
    on_disk = world.state("K-1")
    assert on_disk == job
    assert set(on_disk) == {"schema"} | set(J.LAUNCH_KEYS) | set(J.LIFECYCLE_KEYS)
    assert on_disk["schema"] == "ky.job/1" and on_disk["phase"] == "prepared"
    assert re.match(r"^J-[0-9]{8}T[0-9]{6}Z-b1\Z", on_disk["job_id"])
    scratch = str(world.scratch / "jobs" / on_disk["job_id"])
    assert on_disk["job_scratch"] == scratch
    assert [on_disk[k] for k in ("prompt_path", "stdout_path", "stderr_path", "tmp_path")] == \
        [scratch + "/prompt.md", scratch + "/stdout.jsonl", scratch + "/stderr.log", scratch + "/tmp"]
    assert os.path.isfile(scratch + "/prompt.md") and os.path.isfile(scratch + "/stdout.jsonl")
    assert os.path.isfile(scratch + "/stderr.log") and os.path.isdir(scratch + "/tmp")
    for key in ("worktree", "job_scratch", "prompt_path", "stdout_path", "stderr_path", "tmp_path", "card_path",
                "packet_path", "claude_bin", "mcp_config"):
        assert os.path.isabs(on_disk[key]), key
    assert on_disk["worktree"] == str(world.worktrees / "kalayantra-k-1") and on_disk["branch"] == "kalayantra/k-1"
    assert on_disk["controller_id"] == world.ctx.controller_id and on_disk["boundary"] is None
    assert on_disk["attempt"] == 1 and on_disk["claim_id"] == "claim-1"


def test_job_ids_are_created_exclusively(world, monkeypatch):
    monkeypatch.setattr(J, "_now", lambda: 1791798000.0)                # one frozen second
    first = opened(world, "K-1", "b1")
    J.close(world.ctx, first, {"outcome": "refused", "detail": "x", "failure_fp": None})
    second = opened(world, "K-2", "b1")
    third = J.open(world.ctx, world.intent({"item": "R-1", "kind": "REGEN"}), None, world.facts(None))
    fourth_scratch = world.scratch / "jobs" / (first["job_id"] + ".3")
    os.makedirs(fourth_scratch)                                         # a stale scratch folder is never reused
    J.close(world.ctx, second, {"outcome": "refused", "detail": "x", "failure_fp": None})
    fourth = opened(world, "K-3", "b1")
    assert [first["job_id"], second["job_id"], third["job_id"], fourth["job_id"]] == \
        ["J-20261012T094000Z-b1", "J-20261012T094000Z-b1.2", "J-20261012T094000Z-regen", "J-20261012T094000Z-b1.4"]
    assert [j["job_id"] for j in J.load(world.ctx)] == ["J-20261012T094000Z-b1", "J-20261012T094000Z-b1.2",
                                                        "J-20261012T094000Z-b1.4", "J-20261012T094000Z-regen"]


def test_load_reads_legacy_jobs_first_and_quarantines_bad_folders(world):
    job = opened(world)
    for n in (10, 2):
        d = world.run / "jobs" / ("legacy-%d" % n)
        os.makedirs(d)
        (d / "state.json").write_text(json.dumps(dict(job, job_id="legacy-%d" % n, phase="ended", slot=None)))
    (world.run / "jobs" / "failures.json").write_text("{}")             # not a job
    assert [j["job_id"] for j in J.load(world.ctx)] == ["legacy-2", "legacy-10", job["job_id"]]
    bad = world.run / "jobs" / "J-20260101T000000Z-b2"
    os.makedirs(bad)
    for text in (None, "{not json", "[]", '{"schema":"ky.legacy_job_state/1"}'):
        if text is not None:
            (bad / "state.json").write_text(text)
        assert [j["job_id"] for j in J.load(world.ctx)] == ["legacy-2", "legacy-10", job["job_id"]]
    notices = [line for line in world.log.journal if bad.name in line]
    assert len(notices) == 1 and "state.json" in notices[0]
    # A repaired folder is read again; quarantine never moves or rewrites it.
    (bad / "state.json").write_text(json.dumps(dict(job, job_id=bad.name, phase="ended", slot=None)))
    assert len(J.load(world.ctx)) == 4


@pytest.mark.parametrize("change,reason", [({"phase": "finished"}, "phase"), ({"job_id": "another"}, "job_id"),
                                          ({"key": {}}, "key"), ({"slot": []}, "slot"), ({"locks": "lock"}, "locks"),
                                          ({"phase": "finished", "slot": None}, "phase"),
                                          ({"phase": "finished", "slot": "b2"}, "phase")])
def test_malformed_canonical_job_is_local_error_and_keeps_its_reservations(world, change, reason):
    job = opened(world)
    bad = world.run / "jobs" / job["job_id"] / "state.json"
    text = json.dumps(dict(job, **change))
    bad.write_text(text)
    assert J.load(world.ctx) == []
    assert J.supervise(world.ctx) == []
    assert J.recover(world.ctx) == []
    notices = [line for line in world.log.journal if job["job_id"] in line]
    assert len(notices) == 1 and "dispatcher error" in notices[0] and reason in notices[0]
    assert J.open(world.ctx, world.intent({"item": "K-2"}), "b1", world.facts(None)) is None
    other = J.open(world.ctx, world.intent({"item": "K-2"}), "b3", world.facts(None))
    assert other is not None
    assert bad.read_text() == text



@pytest.mark.parametrize("state", [None, "{not json", "[]", "{}", '{"schema":null}', "unreadable"])
def test_unknown_native_state_reserves_slot_and_unidentified_item(world, monkeypatch, state):
    job = opened(world)
    path = world.run / "jobs" / job["job_id"] / "state.json"
    if state is None:
        path.unlink()
    elif state != "unreadable":
        path.write_text(state)
    original = path.read_bytes() if path.exists() else None
    if state == "unreadable":
        real = ka.read_json
        monkeypatch.setattr(ka, "read_json", lambda p: (None, "unreadable: PermissionError")
                            if Path(p) == path else real(p))
    for _ in range(3):
        assert J.load(world.ctx) == []
        assert J.supervise(world.ctx) == []
        assert J.recover(world.ctx) == []
    assert J._look(world.ctx, "new-key", "b1") is not None
    # The item cannot be reconstructed from a native folder name. Even another slot must not reuse it.
    assert J.open(world.ctx, world.intent({"item": "K-1", "key": "changed-key"}), "b3", world.facts(None)) is None
    assert J.open(world.ctx, world.intent({"item": "K-2"}), "b1", world.facts(None)) is None
    notices = [line for line in world.log.journal if job["job_id"] in line and "dispatcher error" in line]
    assert len(notices) == 1
    assert (path.read_bytes() if path.exists() else None) == original


@pytest.mark.parametrize("missing_slot", [False, True])
def test_invalid_phase_null_or_missing_slot_reserves_item_across_keys(world, missing_slot):
    job = opened(world)
    path = world.run / "jobs" / job["job_id"] / "state.json"
    bad = dict(job, phase="finished", slot=None)
    if missing_slot:
        del bad["slot"]
    path.write_text(json.dumps(bad))
    original = path.read_bytes()
    assert J._look(world.ctx, "new-key", "b1") is not None
    assert J._look(world.ctx, "changed-key", "b3", "K-1") is not None
    assert J.open(world.ctx, world.intent({"item": "K-1", "key": "changed-key"}), "b3", world.facts(None)) is None
    assert J.open(world.ctx, world.intent({"item": "K-2"}), "b1", world.facts(None)) is None
    assert J.open(world.ctx, world.intent({"item": "K-2"}), "b3", world.facts(None)) is not None
    assert path.read_bytes() == original

def test_foreign_schema_is_quarantined_once_with_its_reason(world):
    job = opened(world)
    bad = world.run / "jobs" / "legacy-3337" / "state.json"
    bad.parent.mkdir()
    bad.write_text('{"schema":"ky.legacy_job_state/1","job_id":"legacy-3337"}')
    original = bad.read_bytes()
    for _ in range(3):
        assert [j["job_id"] for j in J.load(world.ctx)] == [job["job_id"]]
    notices = [line for line in world.log.journal if "legacy-3337" in line]
    assert len(notices) == 1 and "job quarantine" in notices[0] and "schema is not ky.job/1" in notices[0]
    assert bad.read_bytes() == original


# These cases catch folder-first classification, overly broad foreign-schema classification,
# dropped reservations, repeated notices and accidental writes during load/supervise/recover.
IDENTITY_FOLDERS = ["J-20261013T000000Z-b1", "legacy-2", "adopted-native"]
STATE_DEFECTS = [
    pytest.param({}, id="valid"),
    pytest.param({"phase": "bad"}, id="phase"),
    pytest.param({"job_id": "another"}, id="job-id"),
    pytest.param({"key": {}}, id="key"),
    pytest.param({"item": []}, id="item"),
    pytest.param({"kind": 7}, id="kind"),
    pytest.param({"slot": []}, id="slot"),
    pytest.param({"slot": "b2", "phase": "bad"}, id="different-slot"),
    pytest.param({"slot": None, "phase": "bad"}, id="null-slot"),
    pytest.param({"controller_id": False}, id="controller-id"),
    *[pytest.param({key: "not-a-list"}, id=key) for key in
      ("prerequisites", "test_digests", "extra_lean_flags", "disallowed_tools", "tests", "locks")],
]


def identity_state(tmp_path, name, doc):
    path = tmp_path / "run" / "jobs" / name / "state.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(doc))
    notices = []
    ctx = SimpleNamespace(run=tmp_path / "run", controller_id="CTL-test",
                          journal=lambda *args: notices.append(args))
    return ctx, path, notices


@pytest.mark.parametrize("name", IDENTITY_FOLDERS)
@pytest.mark.parametrize("change", STATE_DEFECTS)
def test_state_identity_native_decision_table(tmp_path, name, change):
    doc = dict(schema="ky.job/1", job_id=name, phase="live", key="old-key", item="K-1",
               slot="b1", controller_id="CTL-test")
    doc.update(change)
    ctx, path, notices = identity_state(tmp_path, name, doc)
    original = path.read_bytes()
    for _ in range(3):
        loaded = J.load(ctx)
        if not change:
            assert [job["job_id"] for job in loaded] == [name]
            assert ctx._job_errors == {}
        else:
            assert loaded == []
            assert name in ctx._job_errors
            assert J.supervise(ctx) == []
            assert J.recover(ctx) == []
        # Check each independently: a matched item must not hide lost slot/key ownership.
        if "slot" not in change or change["slot"] == "b2":
            slot = "b2" if change.get("slot") == "b2" else "b1"
            assert J._look(ctx, "new-key", slot, "K-2") is not None
        if name.startswith("J-"):
            assert J._look(ctx, "new-key", "b1", "K-2") is not None
        if "key" not in change:
            assert J._look(ctx, "old-key", "b3", "K-2") is not None
        if change and "item" not in change:
            assert J._look(ctx, "new-key", "b3", "K-1") is not None
        assert (J._look(ctx, "new-key", "b3", "K-2") is not None) == ("item" in change)
    if change:
        assert len(notices) == 1 and notices[0][0] == "dispatcher error"
    else:
        assert notices == []
    assert path.read_bytes() == original


@pytest.mark.parametrize("name", IDENTITY_FOLDERS)
@pytest.mark.parametrize("identity", [
    {"schema": "ky.bootstrap_job_state/3"},
    {"schema": "ky.legacy_job_state/1"},
    {"launcher": "cockpit-direct"},
])
@pytest.mark.parametrize("change", STATE_DEFECTS)
def test_state_identity_foreign_decision_table(tmp_path, name, identity, change):
    doc = dict(job_id=name, phase="live", key="old-key", item="K-1", slot="b1")
    doc.update(identity)
    doc.update(change)
    ctx, path, notices = identity_state(tmp_path, name, doc)
    original = path.read_bytes()
    for _ in range(3):
        assert J.load(ctx) == []
        assert ctx._job_errors == {}
        assert J.supervise(ctx) == []
        assert J.recover(ctx) == []
        assert J._look(ctx, "old-key", "b1", "K-1") is None
    assert len(notices) == 1 and notices[0][0] == "job quarantine"
    assert path.read_bytes() == original


@pytest.mark.parametrize("name", IDENTITY_FOLDERS)
@pytest.mark.parametrize("state", [
    None, "{not json", "unreadable", "[]", "null", '"text"', "7", "true", "{}",
    '{"schema":null}', '{"schema":false}', '{"schema":7}', '{"schema":[]}', '{"schema":{}}',
    '{"schema":""}', '{"schema":"ky.unrecognized/1"}',
    '{"schema":"ky.job/2","launcher":"cockpit-direct"}',
    '{"schema":null,"launcher":"cockpit-direct"}',
])
def test_state_without_identity_decision_table(tmp_path, monkeypatch, name, state):
    ctx, path, notices = identity_state(tmp_path, name, {})
    if state is None:
        path.unlink()
    elif state != "unreadable":
        path.write_text(state)
    original = path.read_bytes() if path.exists() else None
    if state == "unreadable":
        real = ka.read_json
        monkeypatch.setattr(ka, "read_json", lambda p: (None, "unreadable: PermissionError")
                            if Path(p) == path else real(p))
    for _ in range(3):
        assert J.load(ctx) == []
        assert name in ctx._job_errors
        assert J.supervise(ctx) == []
        assert J.recover(ctx) == []
        assert J._look(ctx, "new-key", "b1", "K-2") is not None
        assert J._look(ctx, "other-key", "b3", "K-1") is not None
        assert J._look(ctx, "other-key", None, "K-2") is not None
    if name.startswith("J-"):
        assert ctx._job_errors[name]["encoded_slot"] == "b1"
    assert len(notices) == 1 and notices[0][0] == "dispatcher error"
    assert (path.read_bytes() if path.exists() else None) == original


@pytest.mark.parametrize("name", IDENTITY_FOLDERS)
def test_native_schema_wins_over_cockpit_launcher_marker(tmp_path, name):
    ctx, path, notices = identity_state(tmp_path, name, dict(
        schema="ky.job/1", job_id=name, phase="bad", launcher="cockpit-direct",
        key="old-key", item="K-1", slot="b1"))
    original = path.read_bytes()
    assert J._look(ctx, "new-key", "b1", "K-2") is not None
    assert J._look(ctx, "old-key", "b3", "K-2") is not None
    assert J._look(ctx, "new-key", "b3", "K-1") is not None
    assert len(notices) == 1 and notices[0][0] == "dispatcher error"
    assert path.read_bytes() == original


@pytest.mark.parametrize("name", IDENTITY_FOLDERS)
@pytest.mark.parametrize("missing", ["phase", "job_id", "slot"])
def test_native_identity_with_missing_field_keeps_declared_reservations(tmp_path, name, missing):
    doc = dict(schema="ky.job/1", job_id=name, phase="bad", key="old-key", item="K-1", slot="b1")
    del doc[missing]
    ctx, path, notices = identity_state(tmp_path, name, doc)
    original = path.read_bytes()
    assert J._look(ctx, "old-key", "b3", "K-2") is not None
    assert J._look(ctx, "new-key", "b3", "K-1") is not None
    if missing != "slot" or name.startswith("J-"):
        assert J._look(ctx, "new-key", "b1", "K-2") is not None
    assert len(notices) == 1 and notices[0][0] == "dispatcher error"
    assert path.read_bytes() == original


@pytest.mark.parametrize("name", IDENTITY_FOLDERS)
def test_unrecognized_schema_keeps_readable_reservations(tmp_path, name):
    ctx, path, notices = identity_state(tmp_path, name, dict(
        schema="ky.unrecognized/1", job_id=name, phase="live", key="old-key", item="K-1", slot="b2"))
    original = path.read_bytes()
    assert J._look(ctx, "new-key", "b2", "K-2") is not None
    assert J._look(ctx, "old-key", "b3", "K-2") is not None
    assert J._look(ctx, "new-key", "b3", "K-1") is not None
    if name.startswith("J-"):
        assert J._look(ctx, "new-key", "b1", "K-2") is not None
    assert len(notices) == 1 and notices[0][0] == "dispatcher error"
    assert path.read_bytes() == original


def test_reviewer_probe_legacy_native_phase_mutation_refuses_open(world):
    # Exact WB-01-R transition, with no original J folder or locks to mask reservation loss.
    _, path, _ = identity_state(world.root, "legacy-2", dict(
        schema="ky.job/1", job_id="legacy-2", phase="live", item="K-1", slot="b1", key="old-key"))
    assert len(J.load(world.ctx)) == 1
    assert J._look(world.ctx, "new-key", "b1") is not None
    doc = json.loads(path.read_text())
    doc["phase"] = "bad"
    path.write_text(json.dumps(doc))
    original = path.read_bytes()
    assert J.load(world.ctx) == []
    for intent, slot in [({"item": "K-2", "key": "new-key"}, "b1"),
                         ({"item": "K-2", "key": "old-key"}, "b3"),
                         ({"item": "K-1", "key": "new-key"}, "b3")]:
        assert J.open(world.ctx, world.intent(intent), slot, world.facts(None)) is None
    assert world.log.ky == [] and world.log.sh == []
    assert J.open(world.ctx, world.intent({"item": "K-2"}), "b3", world.facts(None)) is not None
    assert path.read_bytes() == original
    assert len([line for line in world.log.journal if "legacy-2" in line and "dispatcher error" in line]) == 1


@pytest.mark.parametrize("deadline", ["2026-10-12 13:25:11", "2026-10-12T13:25:11+00:00", "2026-10-12T13:25:11.5Z",
                                      "2026-13-40T00:00:00Z", 1791798000, ""])
def test_a_time_key_in_any_other_form_is_unknown_and_refuses(world, deadline):
    facts = world.facts(None)
    facts["launch"]["deadline"] = deadline
    assert J.open(world.ctx, world.intent({"item": "K-1"}), "b1", facts) is None
    assert world.log.ky == []
    assert not os.path.exists(world.run / "jobs") or os.listdir(world.run / "jobs") == []
    assert not os.path.isdir(world.run / "locks")                          # refused before anything was touched
    job = opened(world)                                                  # … and a state that was changed later
    world.patch("K-1", {"deadline": deadline})
    after = J.launch(world.ctx, world.state("K-1"))
    assert after["phase"] == "prepared" and after["pid"] is None and J._CHILDREN == {}
    assert any("deadline" in line for line in world.log.journal)
    J.close(world.ctx, job, {"outcome": "refused", "detail": "deadline", "failure_fp": None})


def test_a_live_job_whose_deadline_cannot_be_read_is_neither_timed_out_nor_renewed(world):
    opened(world)
    run_step(world, {"op": "launch", "job": "K-1", "behaviour": "sleep"})
    world.patch("K-1", {"deadline": "soon", "renewed_at": "a while ago"})
    assert J.supervise(world.ctx) == []
    assert world.process_state("K-1") == "live" and world.state("K-1")["phase"] == "live"
    assert [a["slug"] for a in world.log.awaiting] == ["job-%s-time-unknown" % world.slug("K-1")]
    assert world.log.ky == ["claim K-1 --worker b1 --lease 10800 [K/b1]"]
    assert J.supervise(world.ctx) == [] and len(world.log.awaiting) == 1          # asked once


def test_a_signal_goes_only_to_a_group_whose_state_can_be_told(world):
    """The termination path itself: with a start identity that cannot be compared, or a recorded group that is
    not the leader's own, nothing is signalled — not TERM and not, after the wait, KILL."""
    opened(world)
    run_step(world, {"op": "launch", "job": "K-1", "behaviour": "sleep"})
    real = world.state("K-1")
    for forged in ({"process_start": "not a start identity"}, {"process_start": None}, {"pid": "pending"}):
        assert J._terminate(dict(real, **forged)) == "unknown"
        assert world.process_state("K-1") == "live"
    for forged in ({"pgid": os.getpgrp()}, {"pgid": 1}, {"pgid": True}, {"pgid": None}):
        assert J._signal(dict(real, **forged), signal.SIGKILL) is False
    me = dict(real, pid=os.getpid(), pgid=os.getpid())
    assert J._signal(me, signal.SIGKILL) is False                       # never this process or its own group
    time.sleep(0.2)
    assert world.process_state("K-1") == "live"
    assert J._terminate(real) == "gone" and world.process_state("K-1") == "gone"      # and the real one works


def gone_owner():
    """{pid, process_start} of a process this test started and collected: positively gone."""
    proc = subprocess.Popen(["/bin/sleep", "0"])
    start = kyloop.ps_identity(proc.pid)
    proc.wait()
    assert wait_for(lambda: kyloop.ps_probe(proc.pid) == ("gone",))
    return proc.pid, start[1] if start else "Thu Jan  1 00:00:00 1970"


def rewrite_owner(world, name, **change):
    path = world.run / "locks" / name / "owner.json"
    path.write_text(json.dumps(dict(json.loads(path.read_text()), **change)))


def test_the_locks_of_a_controller_that_is_gone_are_taken_over_and_released(world):
    """After a real restart the locks name a process that no longer exists: close takes them over (kyaction's
    positively-gone rule) and releases them; a lock that names a third party is left alone and the job waits."""
    job = opened(world)
    pid, start = gone_owner()
    key = job["key"]
    for name in ("job.%s" % key, "item.K-1"):
        rewrite_owner(world, name, pid=pid, pgid=pid, process_start=start)
    world.ctx = Ctx(world, "CTL-dispatcher-20261012T010000Z-2")
    after = J.close(world.ctx, world.state("K-1"), {"outcome": "refused", "detail": "x", "failure_fp": None})
    assert after["phase"] == "ended" and os.listdir(world.run / "locks") == [".takeover.guard"]

    job = opened(world, "K-2", "b2")
    rewrite_owner(world, "item.K-2", session_or_run_id="CTL-planner-1")           # somebody else's now
    after = J.close(world.ctx, job, {"outcome": "refused", "detail": "x", "failure_fp": None})
    assert after["phase"] == "terminating" and os.path.isdir(world.run / "locks" / "item.K-2")
    assert [a["slug"] for a in world.log.awaiting] == ["job-%s-locks" % world.slug("K-2")]
    assert J.open(world.ctx, world.intent({"item": "K-3"}), "b2", world.facts(None)) is None      # the slot is kept
    after = J.close(world.ctx, world.state("K-2"), None)                         # asked again: still not this job's
    assert after["phase"] == "terminating" and os.path.isdir(world.run / "locks" / "item.K-2")
    assert len(world.log.awaiting) == 1
    rewrite_owner(world, "item.K-2", session_or_run_id="CTL-dispatcher-20261012T010000Z-2:job.%s" % job["key"])
    assert J.supervise(world.ctx)[0]["job_id"] == job["job_id"]                  # still terminating: closed again
    assert J.close(world.ctx, job, None)["phase"] == "ended"


def test_a_lock_released_just_before_a_crash_and_taken_by_another_job_is_never_released_again(world, monkeypatch):
    """KYDJOBS-R1-B1, the narrowest window: the controller dies after item.K-1 was released and before that release
    was recorded; a REWORK job of the item takes item.K-1; the resumed close leaves it with that job."""
    first = opened(world, "K-1", "b1")
    real = ka.release_lock

    def dying(lock):
        released = real(lock)
        if lock.path.name == "item.K-1":
            monkeypatch.setattr(ka, "release_lock", real)
            raise Crash("after the release of item.K-1, before it was recorded")
        return released

    monkeypatch.setattr(ka, "release_lock", dying)
    with pytest.raises(Crash):
        J.close(world.ctx, first, {"outcome": "refused", "detail": "x", "failure_fp": None})
    second = J.open(world.ctx, world.intent({"kind": "REWORK", "item": "K-1"}), "b2", world.facts(None))
    assert second is not None, world.log.journal
    taken = json.loads((world.run / "locks" / "item.K-1" / "owner.json").read_text())
    assert J.close(world.ctx, world.state("K-1"), None)["phase"] == "ended"
    assert json.loads((world.run / "locks" / "item.K-1" / "owner.json").read_text()) == taken
    assert J.open(world.ctx, world.intent({"kind": "VERIFY", "item": "K-1"}), "v1", world.facts(None)) is None
    assert world.states[second["job_id"]] == ["prepared"] and world.log.awaiting == []


def test_an_adopted_job_gets_its_locks_under_the_new_controller(world):
    job = opened(world)
    run_step(world, {"op": "launch", "job": "K-1", "behaviour": "sleep"})
    pid, start = gone_owner()
    for name in ("job.%s" % job["key"], "item.K-1"):
        rewrite_owner(world, name, pid=pid, pgid=pid, process_start=start)
    run_step(world, {"op": "restart", "controller": "CTL-dispatcher-20261012T010000Z-2"})
    assert [j["job_id"] for j in J.recover(world.ctx)] == [job["job_id"]]
    for name in ("job.%s" % job["key"], "item.K-1"):
        owner = json.loads((world.run / "locks" / name / "owner.json").read_text())
        assert owner["session_or_run_id"] == "CTL-dispatcher-20261012T010000Z-2:job.%s" % job["key"]
        assert owner["pid"] == os.getpid()                                       # bound to the job, not only its controller
    assert world.state("K-1")["controller_id"] == "CTL-dispatcher-20261012T010000Z-2"
    assert J.recover(world.ctx) == []                                            # it is this controller's job now


def job_record(world, job, slug, kind, inputs):
    actor = {"role": job["role"], "holder_kind": "job", "controller_id": job["controller_id"], "run_id": job["job_id"]}
    aid = "JOB-%s-%s" % (job["job_id"], slug)
    assert ka.begin(world.run, aid, kind, actor, inputs, {"item": job["item"]}, "pushed")[0] == "new"
    return aid


def test_the_action_records_a_job_left_unfinished_are_settled_as_kyloop_does(world):
    job = opened(world)
    ref = {"remote": "origin", "ref": "kalayantra/k-1"}
    pushed = job_record(world, job, "push", "git_push", dict(ref, commit=SHA_A))
    absent = job_record(world, job, "push2", "git_push", dict(ref, commit=SHA_C))
    other = job_record(world, job, "pr", "gh_pr_create", {"title": "x"})
    world.replies.append({"match": "ls-remote", "rc": 0, "out": "%s\trefs/heads/kalayantra/k-1\n" % SHA_A})
    run_step(world, {"op": "launch", "job": "K-1", "behaviour": "done"})
    run_step(world, {"op": "wait", "job": "K-1", "for": "gone"})
    assert [j["job_id"] for j in J.supervise(world.ctx)] == [job["job_id"]]
    assert ka.load(world.run, pushed)["state"] == "DONE"
    assert ka.load(world.run, absent)["state"] == "FAILED"                # positively not there: the next job's
    assert ka.load(world.run, other)["state"] == "INTENDED"               # no observer: unknown, asked once
    assert [a["slug"] for a in world.log.awaiting] == ["job-action-" + re.sub(r"[^a-z0-9-]", "-", other.lower())]
    assert any("git -C %s ls-remote origin refs/heads/kalayantra/k-1" % job["worktree"] in s for s in world.log.sh)
    J.supervise(world.ctx)
    assert len(world.log.awaiting) == 1 and ka.load(world.run, other)["state"] == "INTENDED"
    assert J.close(world.ctx, world.state("K-1"), {"outcome": "done", "detail": "", "failure_fp": None})["phase"] == "ended"


def test_an_open_that_cannot_write_its_job_leaves_no_lock_and_no_claim(world, monkeypatch):
    def nothing_held():
        locks = world.run / "locks"
        return world.log.ky == [] and (not locks.exists() or [n for n in os.listdir(locks) if n[0] != "."] == [])

    (world.run / "jobs").mkdir()
    (world.run / "jobs" / "failures.json").write_text("[]")              # the failure table cannot be read:
    with pytest.raises(J.JobsUnreadable, match="failures.json"):         # refused before anything is touched
        J.open(world.ctx, world.intent({"item": "K-1"}), "b1", world.facts(None))
    assert nothing_held() and os.listdir(world.run / "jobs") == ["failures.json"]
    os.unlink(world.run / "jobs" / "failures.json")

    def full(ctx, state):
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(J, "_reserve", full)
    assert J.open(world.ctx, world.intent({"item": "K-1"}), "b1", world.facts(None)) is None
    assert nothing_held() and os.listdir(world.run / "jobs") == []
    assert any("No space left" in line for line in world.log.journal)


def test_a_launch_that_cannot_start_leaves_nothing_pending(world):
    job = opened(world)
    os.rename(world.fleet / "kyjob.sh", world.fleet / "kyjob.sh.away")
    real = subprocess.Popen

    def refusing(argv, **kw):
        if argv[:1] == ["/bin/bash"] and str(argv[1]).endswith("kyjob.sh"):
            raise OSError("no such launcher")
        return real(argv, **kw)

    J.subprocess.Popen, keep = refusing, J.subprocess.Popen
    try:
        after = J.launch(world.ctx, job)
    finally:
        J.subprocess.Popen = keep
    assert after["phase"] == "prepared" and after["pid"] is None
    assert ka.load(world.run, "ACT-launch-%s" % job["job_id"])["state"] == "FAILED"
    assert J.close(world.ctx, after, {"outcome": "refused", "detail": "launch", "failure_fp": None})["phase"] == "ended"
    assert world.states[job["job_id"]] == ["prepared", "terminating", "ended:refused"]


def test_the_launch_is_one_new_session_with_no_input_and_the_ctx_paths(world, monkeypatch):
    job = opened(world)
    seen = {}
    real = subprocess.Popen

    def recording(argv, **kw):
        if argv[:1] == ["/bin/bash"] and str(argv[1]).endswith("kyjob.sh"):
            seen.update(argv=list(argv), kw=kw)
        return real(argv, **kw)

    monkeypatch.setattr(J.subprocess, "Popen", recording)
    Path(job["job_scratch"], "behaviour").write_text("done")
    Path(job["job_scratch"], "item").write_text("K-1")
    after = J.launch(world.ctx, job)
    world.procs[job["job_id"]] = J._CHILDREN[job["job_id"]]
    world.lstart[after["pid"]] = after["process_start"]
    assert seen["argv"] == ["/bin/bash", str(world.fleet / "kyjob.sh"), job["job_id"]]
    assert seen["kw"]["stdin"] == subprocess.DEVNULL and seen["kw"]["start_new_session"] is True
    env = seen["kw"]["env"]
    assert {k: env[k] for k in ("KY_ROOT", "KY_RUN", "KY_FLEET", "KY_SCRATCH")} == {
        "KY_ROOT": str(world.root), "KY_RUN": str(world.run), "KY_FLEET": str(world.fleet),
        "KY_SCRATCH": str(world.scratch)}
    assert set(env) <= {"HOME", "USER", "LANG", "TERM", "PATH", "KY_ROOT", "KY_RUN", "KY_FLEET", "KY_SCRATCH"}
    assert after["pid"] == after["pgid"] == J._CHILDREN[job["job_id"]].pid and after["process_start"]
    assert J.launch(world.ctx, after) == world.state("K-1") and len(J._CHILDREN) == 1     # never a second start


def test_codex_launch_action_and_activity_are_annotated(tmp_path, monkeypatch):
    """A Codex launch must persist its mode on inputs, observations and checkpoint."""
    import kyjob_engines as engines
    w = World(tmp_path, monkeypatch)
    try:
        job = J.open(w.ctx, w.intent({'item': 'KV3-T'}), 'k1', w.facts({}))
        (Path(job['job_scratch']) / 'behaviour').write_text('done')
        (Path(job['job_scratch']) / 'item').write_text(job['item'])
        monkeypatch.setattr(engines, 'prepare', lambda ctx, value: None)
        job.update(engine='codex', sandbox_mode='full', stall_seconds=300)
        J._save(w.ctx, job)
        live = J.launch(w.ctx, job)
        proc = J._CHILDREN[live['job_id']]
        w.procs[live['job_id']] = proc
        w.lstart[proc.pid] = live['process_start']
        doc = json.loads((w.run / 'actions' / ('ACT-launch-' + job['job_id'] + '.json')).read_text())
        for key in ('inputs', 'target', 'result'):
            assert doc[key]['engine'] == 'codex'
            assert doc[key]['sandbox'] == 'full (owner direction 2026-10-12)'
        assert live['checkpoint']['codex_activity']['sandbox_mode'] == 'full'
    finally:
        w.cleanup()


def test_codex_surviving_group_stalls_before_deadline(tmp_path, monkeypatch):
    """A gone leader cannot exempt its silent tool group from Codex's stall limit."""
    w = World(tmp_path, monkeypatch)
    try:
        job = J.open(w.ctx, w.intent({'item': 'KV3-T'}), 'k1', w.facts({}))
        job.update(engine='codex', sandbox_mode='locked', stall_seconds=1,
                   pid=234567, pgid=234567, process_start='test-owned', phase='live')
        job['checkpoint'] = {'codex_activity': {'launched_at': 1, 'last_growth_at': 1, 'bytes': [0, 0]}}
        for key in ('stdout_path', 'stderr_path'):
            Path(job[key]).write_text('')
        J._save(w.ctx, job)
        monkeypatch.setattr(J, '_now', lambda: 100)
        states = ['survivors']
        monkeypatch.setattr(J, '_process', lambda j: states[0])
        def reap(j):
            states[0] = 'gone'
            return 'gone'
        monkeypatch.setattr(J, '_terminate', reap)  # state probe only: never signal this synthetic pid
        ended = J.supervise(w.ctx)
        assert ended and ended[0]['failure_fp'] == 'codex_stalled'
        assert ended[0]['outcome'] == 'failed'
    finally:
        w.cleanup()


def test_codex_claim_release_and_failure_records_name_mode(tmp_path, monkeypatch):
    import kyjob_engines as engines
    w = World(tmp_path, monkeypatch)
    try:
        monkeypatch.setattr(engines, 'prepare', lambda ctx, value: None)
        facts = w.facts({})
        facts['launch'].update(engine='codex', sandbox_mode='full', launch_config_path=str(tmp_path/'cfg.json'))
        job = J.open(w.ctx, w.intent({'item': 'KV3-T'}), 'k1', facts)
        assert job is not None
        ended = J.close(w.ctx, job, {'outcome': 'failed', 'failure_fp': 'codex_stalled'})
        assert ended['phase'] == 'ended'
        for path in (w.run/'actions').glob('ACT-*.json'):
            doc = json.loads(path.read_text())
            for key in ('inputs', 'target', 'result'):
                assert doc[key]['engine'] == 'codex'
                assert doc[key]['sandbox'] == 'full (owner direction 2026-10-12)'
        failure = json.loads((w.run/'jobs/failures.json').read_text())['KV3-T']['codex_stalled']
        assert failure['engine'] == 'codex' and failure['sandbox_mode'] == 'full'
    finally:
        w.cleanup()


@pytest.mark.parametrize('growth', [None, 'stdout_path', 'stderr_path'])
def test_codex_recovered_real_survivors_are_supervised(world, monkeypatch, growth):
    """Restart loses child handles, but not silence or the identity-safe TERM/KILL obligation."""
    import kyjob_engines as engines
    job = opened(world)
    (world.fleet / 'kyjob.sh').write_text(
        '#!/bin/bash\ntrap "" TERM\n/bin/sleep 600 &\n'
        'while [ ! -f "$KY_SCRATCH/jobs/$1/exit-leader" ]; do /bin/sleep .02; done\nexit 0\n')
    monkeypatch.setattr(engines, 'prepare', lambda ctx, value: None)
    job.update(engine='codex', sandbox_mode='full', stall_seconds=10)
    J._save(world.ctx, job)
    job = J.launch(world.ctx, job)
    proc = J._CHILDREN[job['job_id']]
    world.procs[job['job_id']] = proc
    world.lstart[proc.pid] = job['process_start']
    assert job['process_start'] is not None
    Path(job['job_scratch'], 'exit-leader').touch()
    proc.wait(timeout=5)
    assert J._process(job) == 'survivors'
    # Persist observed bytes and silence, then discard every controller child handle.
    job['checkpoint']['codex_activity'].update(launched_at=100, last_growth_at=100, bytes=[0, 0])
    J._save(world.ctx, job)
    J._CHILDREN.clear()
    world.ctx = Ctx(world, 'CTL-codex-restarted')
    now = [111]
    monkeypatch.setattr(J, '_now', lambda: now[0])
    signals = []
    real_signal = J._signal
    def recording(value, sig):
        signals.append(sig)
        return real_signal(value, sig)
    monkeypatch.setattr(J, '_signal', recording)
    if growth:
        Path(job[growth]).write_text('new output')
    adopted = J.recover(world.ctx)
    assert len(adopted) == 1 and adopted[0]['controller_id'] == world.ctx.controller_id
    for name in ['job.' + job['key']] + job['locks']:
        owner = json.loads((world.run / 'locks' / name / 'owner.json').read_text())
        assert owner['session_or_run_id'] == world.ctx.controller_id + ':job.' + job['key']
    if growth:
        assert J.supervise(world.ctx) == []
        assert signals == [] and J._process(job) == 'survivors'
        persisted = J._fresh(world.ctx, job)
        assert persisted['checkpoint']['codex_activity']['last_growth_at'] == 111
        assert persisted['failure_fp'] is None
        assert json.loads((world.run / 'claims/b1.json').read_text())['state'] == 'acquired'
        now[0] = 121
    stopped = J.supervise(world.ctx)
    assert len(stopped) == 1 and stopped[0]['failure_fp'] == 'codex_stalled'
    assert signals == [signal.SIGTERM, signal.SIGKILL]
    assert J._process(stopped[0]) == 'gone'
    ended = J.close(world.ctx, stopped[0])
    assert ended['phase'] == 'ended' and ended['outcome'] == 'failed'
    assert ended['checkpoint']['codex_activity']['reason'] == 'codex_stalled'
    failure = json.loads((world.run / 'jobs/failures.json').read_text())[job['item']]['codex_stalled']
    assert failure['count'] == 1 and failure['last_job'] == job['job_id']
    assert J.close(world.ctx, ended)['phase'] == 'ended'
    assert json.loads((world.run / 'jobs/failures.json').read_text())[job['item']]['codex_stalled']['count'] == 1
    assert json.loads((world.run / 'claims/b1.json').read_text())['state'] == 'released'
    assert not (world.run / ('locks/item.' + job['item'])).exists()
    assert not (world.run / ('locks/job.' + job['key'])).exists()


@pytest.mark.parametrize('phase', ['live', 'terminating'])
@pytest.mark.parametrize('condition', ['silent', 'deadline', 'unknown', 'foreign_lock', 'survives',
                                      'activity_missing', 'activity_invalid', 'deadline_unknown'])
def test_codex_restart_supervision_fences(world, monkeypatch, phase, condition):
    """Known groups resume clocks/stops; unknown evidence and unsuccessful stops retain resources."""
    job = opened(world)
    job.update(engine='codex', sandbox_mode='locked', stall_seconds=10,
               pid=234567, pgid=234567, process_start='test-owned', phase=phase)
    activity = dict(launched_at=1, last_growth_at=1, bytes=[0, 0])
    J._checkpoint(job)['codex_activity'] = activity
    for key in ('stdout_path', 'stderr_path'):
        Path(job[key]).write_text('')
    if phase == 'terminating':
        job.update(outcome='failed', failure_fp='codex_stalled')
    if condition == 'deadline_unknown':
        job.update(deadline='unknown', outcome=None, failure_fp=None)
        activity.update(launched_at=90, last_growth_at=99)
    if condition == 'deadline':
        job.update(deadline=ka.utc(50), outcome='timed_out' if phase == 'terminating' else None,
                   failure_fp=None)
        activity.update(launched_at=90, last_growth_at=99)
    if condition == 'activity_missing':
        job['checkpoint'].pop('codex_activity')
        job.update(outcome=None, failure_fp=None)
    if condition == 'activity_invalid':
        activity['last_growth_at'] = None
        job.update(outcome=None, failure_fp=None)
    J._save(world.ctx, job)
    if condition == 'foreign_lock':
        rewrite_owner(world, 'item.' + job['item'], session_or_run_id='CTL-foreign')
    state = ['unknown' if condition == 'unknown' else 'survivors']
    stops = []
    monkeypatch.setattr(J, '_process', lambda value: state[0])
    def stop(value):
        stops.append(value['job_id'])
        if condition != 'survives':
            state[0] = 'gone'
        return state[0]
    monkeypatch.setattr(J, '_terminate', stop)  # synthetic identity is never signalled
    monkeypatch.setattr(J, '_now', lambda: 100)
    world.ctx = Ctx(world, 'CTL-codex-restarted')
    J.recover(world.ctx)
    for _ in range(2):
        for pending in J.supervise(world.ctx):
            J.close(world.ctx, pending)
    after = J._fresh(world.ctx, job)
    held = condition in ('unknown', 'foreign_lock', 'survives', 'activity_missing', 'activity_invalid', 'deadline_unknown')
    if held:
        assert after['phase'] != 'ended'
        assert json.loads((world.run / 'claims/b1.json').read_text())['state'] == 'acquired'
        assert (world.run / ('locks/item.' + job['item'])).exists()
        if condition == 'survives':
            assert stops and after['failure_fp'] == 'codex_stalled'
        else:
            assert stops == []
        assert world.log.awaiting
    else:
        assert stops and after['phase'] == 'ended'
        assert after['outcome'] == ('timed_out' if condition == 'deadline' else 'failed')
        assert json.loads((world.run / 'claims/b1.json').read_text())['state'] == 'released'


def test_claude_survivors_keep_legacy_recovery(world, monkeypatch):
    job = opened(world)
    job.update(pid=234567, pgid=234567, process_start='test-owned', phase='live')
    J._save(world.ctx, job)
    monkeypatch.setattr(J, '_process', lambda value: 'survivors')
    monkeypatch.setattr(J, '_terminate', lambda value: pytest.fail('Claude survivor was signalled'))
    world.ctx = Ctx(world, 'CTL-claude-restarted')
    assert J.recover(world.ctx) == [] and J.supervise(world.ctx) == []
    assert J._fresh(world.ctx, job)['controller_id'] == job['controller_id']
    assert len(world.log.awaiting) == 1
