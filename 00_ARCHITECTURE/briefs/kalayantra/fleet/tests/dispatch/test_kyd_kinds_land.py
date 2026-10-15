"""kyd_kinds_land.py — the REGEN, MERGE and COMPLETE kinds of the dispatcher (relaunch plan v2.7 §6; packet
KV3-B-KYDKINDS-LAND v1).

Every case of kinds_land.json is a small world (the tracker's `ky next --json`, the plan model, the item's events,
the PR as GitHub shows it, the holds, files under the run directory, and the reply of every command) and a list of
steps. A step calls the module once and states what must come back: the intents, the result, and — exactly, in
order — every command, tracker call, action record, awaiting item and journal line the module issued.

`ctx` is a recording double. A command the case does not name fails the test, so nothing here can reach the real
`gh`, `ky`, `git` or a fleet script. Paths in a case are written with {root} {run} {fleet} {scratch} {repo} {wt};
the test replaces them with directories of its own under pytest's tmp_path.
"""
import copy
import hashlib
import importlib
import json
import os
import re
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
FLEET = HERE.parents[1]
sys.path.insert(0, str(FLEET))

import kyd_kinds_land as M  # noqa: E402

DOC = json.loads((HERE / "kinds_land.json").read_text(encoding="utf-8"))
CASES = DOC["cases"]
NOW = "2026-10-12T10:00:00Z"
CONTROLLER = "CTL-dispatcher-20261012T100000Z-4242"

LAUNCH_KEYS = ("job_id key item kind role stream slot worktree branch base_sha head digest verdict_phase evidence_fp "
               "pr registered_head queue_authorised prerequisites test_digests migration_number loop max_loops model "
               "effort permission_mode max_turns deadline claude_bin mcp_config extra_lean_flags disallowed_tools "
               "job_scratch prompt_path stdout_path stderr_path tmp_path tests se_ephe_path swe_ephe_path card_path "
               "packet_path boundary regen fixture locks controller_id").split()
LIFECYCLE_KEYS = ("phase pid pgid process_start provider_session_id claim_id renewed_at exit_code outcome result_path "
                  "result_event checkpoint failure_fp attempt requeued ended_at").split()
INTENT_KEYS = {"kind", "item", "key", "stream", "role", "pool", "runner", "queue", "claim", "locks", "tier",
               "not_slot", "head", "digest", "verdict_phase", "evidence_fp", "card", "packet", "header"}


def fill(value, dirs):
    """The case with its {root} … {wt} placeholders replaced."""
    if isinstance(value, str):
        for name, path in dirs.items():
            value = value.replace("{%s}" % name, path)
        return value
    if isinstance(value, list):
        return [fill(v, dirs) for v in value]
    if isinstance(value, dict):
        return {fill(k, dirs): fill(v, dirs) for k, v in value.items()}
    return value


def write_file(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, str):
        path.write_text(content, encoding="utf-8")
    else:
        path.write_text(json.dumps(content), encoding="utf-8")


class World:
    """What the double answers from. A step's `world` patch, and the `then` of a command reply, change it."""

    def __init__(self, spec, dirs):
        self.dirs = dirs
        self.next = None
        self.events = {}
        self.pr = {}
        self.sh = []
        self.ky = []
        self.act = "honest"
        self.apply(spec)

    def apply(self, patch):
        for key, value in patch.items():
            if key in ("next", "act"):
                setattr(self, key, copy.deepcopy(value))
            elif key in ("events", "pr"):
                getattr(self, key).update(copy.deepcopy(value))
            elif key == "events_append":
                for item, rows in value.items():
                    self.events.setdefault(item, []).extend(copy.deepcopy(rows))
            elif key in ("sh", "ky"):                       # newest rules first: a patch overrides the case's reply
                setattr(self, key, copy.deepcopy(value) + getattr(self, key))
            elif key == "model_items":
                write_file(Path(self.dirs["repo"]) / "plan_model.json", {"items": value})
            elif key == "model_raw":
                write_file(Path(self.dirs["repo"]) / "plan_model.json", value)
            elif key == "files":
                for path, content in value.items():
                    write_file(path, content)
            elif key == "rm":
                for path in value:
                    os.remove(path)
            elif key == "decisions":
                with open(Path(self.dirs["run"]) / "DECISIONS_SURROGATE.jsonl", "a", encoding="utf-8") as handle:
                    for line in value:
                        handle.write((line if isinstance(line, str) else json.dumps(line)) + "\n")
            else:
                raise AssertionError("unknown world key %r" % key)

    def reply(self, rules, argv):
        for rule in rules:
            if all(token in argv for token in rule["has"]):
                if "then" in rule:
                    self.apply(rule["then"])
                return rule.get("rc", 0), rule.get("out", ""), rule.get("err", "")
        raise AssertionError("the case names no reply for %r" % (argv,))


class Ctx:
    """The recording double of the engine's ctx (the packet's Contract)."""

    def __init__(self, world, dirs, calls):
        self._world, self._calls = world, calls
        self.root, self.run, self.fleet = dirs["root"], dirs["run"], dirs["fleet"]
        self.scratch, self.repo = dirs["scratch"], dirs["repo"]
        self.controller_id = CONTROLLER
        self.model = str(Path(dirs["repo"]) / "plan_model.json")
        self.pr_reads = 0

    @property
    def next(self):
        return copy.deepcopy(self._world.next)

    def sh(self, argv, env=None, cwd=None, timeout=120):
        assert isinstance(argv, list) and all(isinstance(a, str) for a in argv), argv
        call = {"sh": list(argv)}
        if env is not None:
            call["env"] = dict(env)
        if cwd is not None:
            call["cwd"] = str(cwd)
        if timeout != 120:
            call["timeout"] = timeout
        self._calls.append(call)
        return self._world.reply(self._world.sh, list(argv))

    def ky(self, *args, stream=None, lane=None):
        assert all(isinstance(a, str) for a in args), args
        self._calls.append({"ky": list(args), "stream": stream, "lane": lane})
        return self._world.reply(self._world.ky, list(args))

    def act(self, action_id, kind, inputs, target, effect, observer):
        json.dumps(inputs), json.dumps(target)                    # a record is plain JSON
        self._calls.append({"act": action_id, "kind": kind, "inputs": copy.deepcopy(inputs),
                            "target": copy.deepcopy(target)})
        mode = self._world.act
        if mode == "recorded_done":                               # an earlier attempt finished: the effect is skipped
            return "done", {"earlier": True}
        if mode == "in_progress":                                 # somebody else may be in the middle of it
            return "unknown", {}
        result = effect()
        assert isinstance(result, dict), "effect() returns the observed result as a dict"
        json.dumps(result)
        answer = observer({"action_id": action_id, "kind": kind, "inputs": inputs, "target": target})
        assert isinstance(answer, tuple) and len(answer) == 2 and answer[0] in ("done", "not_done", "unknown"), answer
        json.dumps(answer[1])
        if mode == "naive":                                       # an engine that calls every finished effect done
            return "done", result
        return {"done": "done", "not_done": "failed", "unknown": "unknown"}[answer[0]], answer[1]

    def events(self, item):
        return copy.deepcopy(self._world.events.get(item, []))

    def pr(self, item):
        self.pr_reads += 1
        return copy.deepcopy(self._world.pr.get(item))

    def awaiting(self, slug, question, options, evidence, item, class_hint):
        assert re.fullmatch(r"[a-z0-9-]+", slug), slug            # schemas/awaiting.json: the id's slug
        aid = "AW-20261012T100000Z-%s" % slug
        doc = {"schema": "ky.awaiting/1", "id": aid, "created_at": NOW,
               "raised_by": {"role": "dispatcher", "session_id": CONTROLLER, "job_id": None}, "item": item,
               "question": question, "options": options, "recommendation": None, "evidence": evidence,
               "deadline": None, "class_hint": class_hint, "blocks": "item"}
        write_file(Path(self.run) / "awaiting" / (aid + ".json"), doc)
        self._calls.append({"awaiting": slug, "item": item, "class_hint": class_hint, "options": options,
                            "evidence": evidence, "question": question})
        return doc

    def journal(self, event, text):
        assert isinstance(text, str) and text
        self._calls.append({"journal": event, "text": text})


def make_job(intent, job_id, dirs):
    """The job state as kyd_jobs.open writes it: every key, null unless the intent or its header sets a LAUNCH key.
    Header keys that are not launch keys (`action`, …) do not reach the job state — `start` must not need them."""
    job = dict.fromkeys(LAUNCH_KEYS + LIFECYCLE_KEYS)
    for key in LAUNCH_KEYS:
        if key in intent:
            job[key] = copy.deepcopy(intent[key])
    for key, value in intent["header"].items():
        if key in LAUNCH_KEYS:
            job[key] = copy.deepcopy(value)
    job.update(job_id=job_id, worktree=dirs["repo"], controller_id=CONTROLLER, phase="prepared")
    return job


def tree(directory):
    """Every file under a directory with its bytes: what a read-only call must leave unchanged."""
    out = {}
    for base, _dirs, files in os.walk(directory):
        for name in files:
            path = os.path.join(base, name)
            with open(path, "rb") as handle:
                out[path] = handle.read()
    return out


def subset(expected, actual, where):
    """`expected` holds within `actual`: a dict names the keys it pins, everything else is compared exactly."""
    if isinstance(expected, dict) and isinstance(actual, dict):
        for key, value in expected.items():
            assert key in actual, "%s: %r is missing in %r" % (where, key, actual)
            subset(value, actual[key], "%s.%s" % (where, key))
    else:
        assert expected == actual, "%s: expected %r, got %r" % (where, expected, actual)


def check_calls(expected, actual, where):
    assert [sorted(set(c) & {"sh", "ky", "act", "awaiting", "journal"}) for c in actual] == \
        [sorted(set(c) & {"sh", "ky", "act", "awaiting", "journal"}) for c in expected], \
        "%s: calls differ\nexpected %s\nactual   %s" % (where, json.dumps(expected, indent=1), json.dumps(actual, indent=1))
    for index, (want, got) in enumerate(zip(expected, actual)):
        subset(want, got, "%s call %d" % (where, index))


def check_intent_shape(intent):
    assert set(intent) == INTENT_KEYS, sorted(set(intent) ^ INTENT_KEYS)
    assert intent["kind"] in M.KINDS and intent["role"] == intent["kind"].lower()
    assert intent["runner"] == "script" and intent["pool"] is None and intent["claim"] is None
    assert intent["tier"] is None and intent["not_slot"] is None and intent["card"] is None and intent["packet"] is None
    assert isinstance(intent["queue"], bool) and isinstance(intent["locks"], list) and isinstance(intent["header"], dict)
    assert (intent["head"] is None) != (intent["digest"] is None), "exactly one of head and digest"
    assert re.fullmatch(r"[0-9a-f]{64}", intent["evidence_fp"])
    identity = intent["head"] or intent["digest"]
    twelve = hashlib.sha256(("%s\n%s" % (identity, intent["evidence_fp"])).encode("utf-8")).hexdigest()[:12]
    assert intent["key"] == "%s.%s.%s" % (intent["kind"], intent["item"], twelve)
    json.dumps(intent)


def without_derived(intent):
    return {k: v for k, v in intent.items() if k not in ("key", "evidence_fp")}


@pytest.fixture
def dirs(tmp_path):
    out = {name: str(tmp_path / name) for name in ("root", "run", "fleet", "scratch", "repo", "wt")}
    out["run"] = str(tmp_path / "root" / "run")
    for path in out.values():
        os.makedirs(path, exist_ok=True)
    return out


@pytest.fixture(autouse=True)
def fixed_clock(monkeypatch):
    monkeypatch.setattr(M, "_utc", lambda: NOW)


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_case(case, dirs, monkeypatch):
    world = World(fill(case["world"], dirs), dirs)
    calls = []
    ctx = Ctx(world, dirs, calls)
    intents = []
    for number, raw in enumerate(case["steps"]):
        step = fill(raw, dirs)
        where = "%s step %d (%s)" % (case["name"], number, step["op"])
        if "world" in step:
            world.apply(step["world"])
        del calls[:]
        before = tree(dirs["root"])
        reads = ctx.pr_reads
        if step["op"] == "intents":
            intents = M.intents(ctx)
            for intent in intents:
                check_intent_shape(intent)
            assert [without_derived(i) for i in intents] == step["intents"], \
                "%s: intents\n%s" % (where, json.dumps([without_derived(i) for i in intents], indent=1))
            assert len({i["key"] for i in intents}) == len(intents)
            assert tree(dirs["root"]) == before, "%s: intents() wrote a file" % where
            assert all(set(c) & {"sh", "journal"} for c in calls), "%s: intents() acted: %r" % (where, calls)
        elif step["op"] == "start":
            job = make_job(intents[step.get("intent", 0)], step["job_id"], dirs)
            job.update(step.get("job", {}))
            result = M.start(ctx, job)
            assert set(result) == {"outcome", "detail", "failure_fp"}, result
            assert result["outcome"] in ("done", "blocked", "failed", "refused"), result
            assert isinstance(result["detail"], str) and result["detail"], result
            subset(step["result"], result, where)
            assert ctx.pr_reads > reads or job["kind"] != "MERGE", "%s: start did not read the PR again" % where
        elif step["op"] == "park":
            result = M.park(ctx, intents[step.get("intent", 0)])
            subset(step["result"], result, where)
        elif step["op"] == "accepted":
            assert M.accepted_head(ctx, step["item"]) == step["accepted"], where
        elif step["op"] == "restart":                             # a new dispatcher process: nothing lives in memory
            importlib.reload(M)
            monkeypatch.setattr(M, "_utc", lambda: NOW)
            ctx = Ctx(world, dirs, calls)
            intents = []
        else:
            raise AssertionError("unknown op %r" % step["op"])
        if "calls" in step:
            check_calls(step["calls"], calls, where)
        for path, content in step.get("files", {}).items():
            if content is None:
                assert not os.path.lexists(path), "%s: %s exists" % (where, path)
            else:
                with open(path, encoding="utf-8") as handle:
                    assert json.load(handle) == content, "%s: %s" % (where, path)
        for forbidden in step.get("never", []):
            assert not any(forbidden in json.dumps(c) for c in calls), "%s: %r was issued" % (where, forbidden)


def names():
    return {c["name"] for c in CASES}


def test_fixture_covers_the_packet():
    """The acceptance list of the packet, by case name: a case that is deleted or renamed fails here."""
    required = {
        "regen_confined_to_declared_outputs", "regen_exit_codes", "regen_dirty_outside_generated",
        "merge_at_the_accepted_head", "merge_at_an_inherited_head",
        "negative_hold_merges_one_parked_request_no_gh", "negative_pr_head_differs_from_registered_head",
        "negative_substantive_resolution_not_inherited",
        "cancel_after_head_change_then_rejected", "parked_request_across_a_restart",
        "complete_code", "complete_artifact", "complete_operation", "complete_packet",
        "complete_refusals", "complete_waits_for_strict_dependencies",
        # review round 1, KL-B1: a queue authorisation is bound to the head it was given at
        "cancel_when_the_queued_head_moved_to_a_registered_inheriting_head",
        "cancel_when_the_queued_head_moved_to_a_directly_accepted_head",
        "cancel_when_the_queued_head_moved_under_hold_merges", "cancel_when_the_queued_head_is_unknown",
        # review round 1, KL-B2: an unknown inheritance answer invalidates nothing
        "cancel_inherit_unknown_invalidates_nothing", "queued_head_unchanged_acceptance_unknown_is_left_alone",
    }
    assert required <= names(), sorted(required - names())
    kinds = {i["kind"] for c in CASES for s in c["steps"] for i in s.get("intents", [])}
    assert kinds == set(M.KINDS)
    outcomes = {s["result"]["outcome"] for c in CASES for s in c["steps"] if s["op"] == "start"}
    assert outcomes == {"done", "blocked", "failed", "refused"}


def test_kinds_and_entry_points():
    assert M.KINDS == ("REGEN", "MERGE", "COMPLETE")
    for name in ("intents", "start", "park", "accepted_head"):
        assert callable(getattr(M, name))


def test_key_is_the_packets_formula():
    """`<kind>.<item>.<12 hex of sha256(head or digest, evidence_fp)>`, from values computed here, not by the module."""
    head, fp = "a" * 40, hashlib.sha256(b"x").hexdigest()
    twelve = hashlib.sha256((head + "\n" + fp).encode()).hexdigest()[:12]
    assert M._key("MERGE", "K-1", head, fp) == "MERGE.K-1." + twelve
    assert M._key("MERGE", "K-1", "b" * 40, fp) != M._key("MERGE", "K-1", head, fp)
    assert M._key("MERGE", "K-1", head, hashlib.sha256(b"y").hexdigest()) != M._key("MERGE", "K-1", head, fp)


def test_start_of_an_unknown_kind_or_a_stale_tracker_is_refused(dirs):
    world = World({"next": None}, dirs)
    calls = []
    ctx = Ctx(world, dirs, calls)
    job = dict.fromkeys(LAUNCH_KEYS + LIFECYCLE_KEYS)
    job.update(job_id="J-1", kind="BUILD", item="K-1", key="BUILD.K-1.000000000000")
    assert M.start(ctx, job)["outcome"] == "refused"
    for kind in M.KINDS:
        job.update(kind=kind, key="%s.K-1.000000000000" % kind)
        result = M.start(ctx, job)
        assert result["outcome"] == "refused" and result["failure_fp"] == "stale", result
    assert calls == []


def test_park_refuses_what_is_not_a_queue_submission_under_the_hold(dirs):
    """park writes only for a `queue` intent while HOLD_MERGES is present; anything else leaves no file."""
    world = World({}, dirs)
    calls = []
    ctx = Ctx(world, dirs, calls)
    intent = {"kind": "MERGE", "item": "K-1", "queue": True, "head": "a" * 40,
              "header": {"action": "submit", "pr": 7, "registered_head": "a" * 40}}
    assert M.park(ctx, intent)["parked"] is False                          # no hold
    write_file(Path(dirs["run"]) / "HOLD_MERGES", "certification hold\n")
    assert M.park(ctx, dict(intent, queue=False))["parked"] is False       # not a queue intent
    assert M.park(ctx, dict(intent, kind="COMPLETE"))["parked"] is False
    assert M.park(ctx, dict(intent, item="../K-1"))["parked"] is False     # never a path outside merge_requests/
    assert M.park(ctx, dict(intent, header={"action": "submit", "pr": 7, "registered_head": "zz"}))["parked"] is False
    assert not (Path(dirs["run"]) / "merge_requests").exists()
    assert M.park(ctx, intent)["parked"] is True
    assert calls == []


def test_importing_the_module_runs_nothing_and_it_calls_no_process_itself():
    """Deterministic and double-able: every command goes through ctx.sh / ctx.ky / ctx.act, never a subprocess."""
    source = (FLEET / "kyd_kinds_land.py").read_text(encoding="utf-8")
    for forbidden in ("import subprocess", "os.system", "os.popen", "Popen(", "--force", "rebase", "--admin"):
        assert forbidden not in source, forbidden
