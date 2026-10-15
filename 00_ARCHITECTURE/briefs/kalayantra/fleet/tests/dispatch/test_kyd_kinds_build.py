"""kyd_kinds_build.py (KV3-B-KYDKINDS-BUILD; relaunch plan v2.7 §6 rows BUILD … ARTIFACT and "Verdict publication").

kinds_build.json holds the cases: a world (what ctx answers, what lies on disk), the call made (`intents`, `start`
or `finish`) and what must come back — the intents, the result, every command, tracker verb, action and journal
line in order, and the files written. ctx is a recording double: nothing here runs ky, gh, git, kyroute.py,
kyverdicts.py or kyboundary.sh; a command the case did not script fails the test.

The packet's three negative cases:
  boundary check not intact: nothing published      finish_verify_boundary_{violated,unknown,unanswered}_publishes_nothing
  a BUILD with neither review nor block: interrupted  finish_build_with_*_is_interrupted
  a step detector null or false: no ky step          step_only_where_the_named_detector_passes,
                                                     start_step_detector_now_{false,null}_runs_no_ky_step
"""
import copy
import hashlib
import json
import os
import re
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
FLEET = HERE.parents[1]
sys.path.insert(0, str(FLEET))

import kyd_kinds_build as B  # noqa: E402

DOC = json.loads((HERE / "kinds_build.json").read_text(encoding="utf-8"))
CASES = DOC["cases"]

# ky.job/1 launch and lifecycle keys, as the packet pins them
LAUNCH_KEYS = ("job_id key item kind role stream slot worktree branch base_sha head digest verdict_phase evidence_fp "
               "pr registered_head queue_authorised prerequisites test_digests migration_number loop max_loops model "
               "effort permission_mode max_turns deadline claude_bin mcp_config extra_lean_flags disallowed_tools "
               "job_scratch prompt_path stdout_path stderr_path tmp_path tests se_ephe_path swe_ephe_path card_path "
               "packet_path boundary regen fixture locks controller_id").split()
LIFECYCLE_KEYS = ("phase pid pgid process_start provider_session_id claim_id renewed_at exit_code outcome result_path "
                  "result_event checkpoint failure_fp attempt requeued ended_at").split()
INTENT_FIELDS = ("kind item key stream role pool runner queue claim locks tier not_slot head digest verdict_phase "
                 "evidence_fp card packet header").split()
EMPTY_INTENT = {"stream": None, "pool": None, "runner": None, "queue": False, "claim": None, "locks": [], "tier": None,
                "not_slot": None, "head": None, "digest": None, "verdict_phase": None, "card": None, "packet": None,
                "header": {}}
ACTION_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,159}\Z")        # kyaction.ID_RE


def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def subst(obj, tokens):
    if isinstance(obj, str):
        for name, value in tokens.items():
            obj = obj.replace("{%s}" % name, value)
        return obj
    if isinstance(obj, list):
        return [subst(x, tokens) for x in obj]
    if isinstance(obj, dict):
        return {subst(k, tokens): subst(v, tokens) for k, v in obj.items()}
    return obj


def packet_text(front):
    return "```json\n%s\n```\n# packet body\n" % json.dumps(front, sort_keys=True)


class Ctx:
    """The recording double of the engine's ctx (the packet's contract)."""

    def __init__(self, tokens, world):
        self.root, self.run, self.fleet = tokens["root"], tokens["run"], tokens["fleet"]
        self.scratch, self.repo = tokens["scratch"], tokens["repo"]
        self.world = world
        self.next = copy.deepcopy(world.get("next"))
        self.priority = list(world.get("priority") or [])
        self.calls = []

    def _reply(self, table, argv):
        for reply in self.world.get(table) or []:
            if all(any(tok == a or a.endswith("/" + tok) for a in argv) for tok in reply["match"]):
                return reply.get("rc"), reply.get("out", ""), reply.get("err", "")
        raise AssertionError("the case scripts no reply for %s %r" % (table, argv))

    def sh(self, argv, env=None, cwd=None, timeout=120):
        assert isinstance(argv, list) and all(isinstance(a, str) for a in argv), argv
        assert env is None, "no command here needs more than the engine's own environment"
        entry = {"sh": list(argv)}
        if cwd is not None:
            entry["cwd"] = cwd
        self.calls.append(entry)
        return self._reply("sh", argv)

    def ky(self, *args, stream=None, lane=None):
        assert all(isinstance(a, str) for a in args), args
        self.calls.append({"ky": list(args), "stream": stream, "lane": lane})
        return self._reply("ky", list(args))

    def act(self, action_id, kind, inputs, target, effect, observer):
        assert ACTION_ID.match(action_id), action_id
        assert isinstance(inputs, dict) and isinstance(target, dict)
        canonical([inputs, target])                                 # plain JSON, as kyaction.begin requires
        self.calls.append({"act": action_id, "kind": kind})
        mode = self.world.get("act", "new")
        if mode == "done":                                          # an earlier attempt finished
            return "done", {"earlier": True}
        if mode == "unfinished":                                    # an earlier attempt neither finished nor failed
            outcome, detail = observer({"action_id": action_id, "kind": kind, "inputs": inputs, "target": target})
            assert outcome in ("done", "not_done", "unknown")
            if outcome == "done":
                return "done", detail
            if outcome == "unknown":
                return "unknown", {"reconcile": detail}
        status, result = effect()
        assert status in ("done", "failed", "unknown") and isinstance(result, dict)
        return status, result

    def events(self, item):
        return copy.deepcopy((self.world.get("events") or {}).get(item, []))

    def pr(self, item):
        return copy.deepcopy((self.world.get("pr") or {}).get(item))

    def accepted(self, item):
        return copy.deepcopy((self.world.get("accepted") or {}).get(item))

    def verify(self, item, step):
        self.calls.append({"verify": [item, step]})
        return (self.world.get("verify") or {}).get("%s/%s" % (item, step))

    def journal(self, event, text):
        self.calls.append({"journal": event, "text": text})


def tokens_for(base, job_id=None):
    root = base / "kalayantra"
    tokens = {"root": str(root), "run": str(root / "run"), "fleet": str(base / "fleet"),
              "scratch": str(base / "scratch"), "repo": str(base / "repo")}
    if job_id:
        tokens["jobdir"] = os.path.join(tokens["run"], "jobs", job_id)
        tokens["jobscratch"] = os.path.join(tokens["scratch"], "jobs", job_id)
    return tokens


def lay_out(tokens, world):
    """Write what the world keeps on disk: packets, job states and plain files."""
    for name in ("run", "fleet", "scratch", "repo"):
        os.makedirs(tokens[name], exist_ok=True)
    packets = os.path.join(tokens["repo"], "00_ARCHITECTURE", "briefs", "kalayantra", "packets")
    os.makedirs(packets, exist_ok=True)
    for item, versions in (world.get("packets") or {}).items():
        for n, front in versions.items():
            Path(packets, "PACKET_%s_v%s.md" % (item, n)).write_text(packet_text(front), encoding="utf-8")
    for job_id, state in (world.get("jobs") or {}).items():
        directory = Path(tokens["run"], "jobs", job_id)
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "state.json").write_text(json.dumps(state), encoding="utf-8")
    for path, text in (world.get("files") or {}).items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        Path(path).write_text(text, encoding="utf-8")


def tree(base):
    """Every path below base with its bytes: what a read-only call must leave as it found it."""
    out = {}
    for directory, names, files in os.walk(base):
        for name in names:
            out[os.path.join(directory, name)] = None
        for name in files:
            path = os.path.join(directory, name)
            out[path] = Path(path).read_bytes()
    return out


def expected_intent(short):
    out = dict(EMPTY_INTENT)
    out.update(short)
    out["role"] = out["kind"].lower()
    return out


def check_intents(got, want):
    assert [(i["kind"], i["item"]) for i in got] == [(w["kind"], w["item"]) for w in want]
    for intent, short in zip(got, want):
        assert sorted(intent) == sorted(INTENT_FIELDS)
        identity = intent["head"] or intent["digest"]
        assert intent["key"] == "%s.%s.%s" % (intent["kind"], intent["item"],
                                              sha(canonical([identity, intent["evidence_fp"]]))[:12])
        assert re.fullmatch(r"[0-9a-f]{64}", intent["evidence_fp"])
        assert {k: v for k, v in intent.items() if k not in ("key", "evidence_fp")} == expected_intent(short)
        for path in (intent["card"], intent["packet"]):
            assert path is None or os.path.isabs(path)
    assert len({i["key"] for i in got}) == len(got)


def make_job(intent, tokens, extra):
    """The prepared job kyd_jobs.open would hand over: the launch keys, those in the intent's header included."""
    job = {key: None for key in LAUNCH_KEYS + LIFECYCLE_KEYS}
    job.update(key=intent["key"], item=intent["item"], kind=intent["kind"], role=intent["role"],
               stream=intent["stream"], head=intent["head"], digest=intent["digest"],
               verdict_phase=intent["verdict_phase"], evidence_fp=intent["evidence_fp"], card_path=intent["card"],
               packet_path=intent["packet"], locks=list(intent["locks"]), phase="prepared")
    job.update({k: v for k, v in intent["header"].items() if k in LAUNCH_KEYS})
    job.update(extra)
    job["job_scratch"] = tokens["jobscratch"]
    return job


def by_op(op):
    return [pytest.param(c, id=c["name"]) for c in CASES if c["op"] == op]


@pytest.mark.parametrize("case", by_op("intents"))
def test_intents(case, tmp_path):
    tokens = tokens_for(tmp_path)
    world, expect = subst(case["world"], tokens), subst(case["expect"], tokens)
    lay_out(tokens, world)
    ctx = Ctx(tokens, world)
    before = tree(tmp_path)
    got = B.intents(ctx)
    check_intents(got, expect["intents"])
    assert ctx.calls == expect["calls"]
    assert not any("ky" in c or "act" in c for c in ctx.calls), "intents is read-only: no tracker verb, no action"
    assert tree(tmp_path) == before, "intents is read-only: nothing on disk may change"


@pytest.mark.parametrize("packet_loops,want", [(None, 2), (1, 1), (3, 3), (5, 5)])
def test_build_max_loops_default_and_packet_override(tmp_path, packet_loops, want):
    """A2 D-17 §2.6: an omitted cap defaults to two; explicit packet caps win."""
    world = copy.deepcopy(CASES[0]["world"])
    world["priority"] = ["K-1"]
    front = world["packets"]["K-1"]["1"]
    front.pop("max_loops")
    if packet_loops is not None:
        front["max_loops"] = packet_loops
    tokens = tokens_for(tmp_path)
    lay_out(tokens, world)
    intent, = B.intents(Ctx(tokens, world))
    assert intent["kind"] == "BUILD"
    assert intent["header"]["max_loops"] == want


@pytest.mark.parametrize("packet_loops,job_loops,want", [(None, None, 2), (None, 4, 4), (3, 4, 3)])
def test_rework_max_loops_default_and_overrides(tmp_path, packet_loops, job_loops, want):
    """The default changes without changing packet > prior job > default precedence."""
    world = copy.deepcopy(next(c["world"] for c in CASES
                               if c["name"] == "escalation_one_rejection_on_a_sonnet_head"))
    front = world["packets"]["K-1"]["1"]
    front.pop("max_loops")
    if packet_loops is not None:
        front["max_loops"] = packet_loops
    job, = world["jobs"].values()
    job.pop("max_loops")
    if job_loops is not None:
        job["max_loops"] = job_loops
    tokens = tokens_for(tmp_path)
    lay_out(tokens, world)
    ctx = Ctx(tokens, world)
    intent, = B.intents(ctx)
    assert intent["kind"] == "REWORK"
    assert intent["header"]["max_loops"] == want
    command = ctx.calls[0]["sh"]
    assert command[command.index("--max-loops") + 1] == str(want)


@pytest.mark.parametrize("case", by_op("start") + by_op("finish"))
def test_start_and_finish(case, tmp_path):
    job_id = case["job"]["job_id"]
    tokens = tokens_for(tmp_path, job_id)
    world, expect = subst(case["world"], tokens), subst(case["expect"], tokens)
    lay_out(tokens, world)
    want = case["job_from"]
    intent = next(i for i in B.intents(Ctx(tokens, world)) if (i["kind"], i["item"]) == (want["kind"], want["item"]))
    job = make_job(intent, tokens, subst(case["job"], tokens))
    os.makedirs(tokens["jobdir"])                               # kyd_jobs.open created both before start
    Path(tokens["jobdir"], "state.json").write_text(json.dumps(dict(job, schema="ky.job/1")))
    os.makedirs(tokens["jobscratch"])
    world = dict(world, **subst(case.get("then") or {}, tokens))
    lay_out(tokens, world)
    ctx = Ctx(tokens, world)
    before = tree(tmp_path)
    result = getattr(B, case["op"])(ctx, copy.deepcopy(job))
    if expect["result"] is None:
        assert result is None, "a model job is launched: start gives no result"
    else:
        assert sorted(result) == ["detail", "failure_fp", "outcome"]
        assert isinstance(result["detail"], str) and result["detail"]
        for key, value in expect["result"].items():
            assert result[key] == value, (key, result)
    assert ctx.calls == expect["calls"]
    after = tree(tmp_path)
    changed = {p for p in set(before) | set(after) if before.get(p) != after.get(p)}
    assert changed == set(expect.get("files") or {}), "only the files the case names may be written"
    for path, content in (expect.get("files") or {}).items():
        assert os.path.isabs(path)
        if "text" in content:
            assert Path(path).read_text(encoding="utf-8") == content["text"]
        else:
            stored = json.loads(Path(path).read_text(encoding="utf-8"))
            assert {k: stored.get(k) for k in content["json"]} == content["json"]
    for path in expect.get("absent") or []:
        assert not os.path.lexists(path)


# ── the fixture itself ──────────────────────────────────────────────────────────────────────────────────────────

REQUIRED_COVER = {
    # each kind and transition
    "BUILD", "REWORK", "STEP", "VERIFY", "ARTIFACT", "order", "build_artifact",
    "start_BUILD", "start_REWORK", "start_STEP", "start_VERIFY", "start_ARTIFACT", "start_retry_ci", "start_block",
    "start_freeze_block", "finish_BUILD_review", "finish_BUILD_block", "finish_REWORK", "finish_VERIFY",
    "finish_ARTIFACT",
    # the packet's negative cases
    "boundary_not_intact", "finish_BUILD_interrupted", "step_detector_null", "step_detector_false",
    "start_step_detector_null", "start_step_detector_false",
    # a Sonnet diff on an Opus rule; each escalation; a retried, then code-class CI failure; already-green
    "sonnet_diff_on_opus_rule", "escalation_sonnet_rejected", "escalation_sonnet_red_max_loops",
    "escalation_opus_rejected_twice", "escalation_continue", "retry_ci", "ci_code_class", "ci_unclassifiable",
    "already_green", "finish_already_green",
}


def test_the_fixture_holds_every_case_the_packet_asks_for():
    covered = {tag for c in CASES for tag in c["covers"]}
    assert REQUIRED_COVER <= covered, sorted(REQUIRED_COVER - covered)
    names = [c["name"] for c in CASES]
    assert len(names) == len(set(names))
    assert {c["op"] for c in CASES} == {"intents", "start", "finish"}


def test_the_fixture_digests_are_those_of_the_bytes_it_lays_out():
    """A digest in the fixture is a claim about bytes: recompute each from the file content the cases write."""
    seen = set()
    for case in CASES:
        for path, text in (case["world"].get("files") or {}).items():
            if path in DOC["digests"]:
                assert sha(text.encode("utf-8")) == DOC["digests"][path], (case["name"], path)
                seen.add(path)
    assert seen == set(DOC["digests"])


# ── the contract's fixed points ─────────────────────────────────────────────────────────────────────────────────

def test_kinds_and_the_order_the_engine_sees():
    assert B.KINDS == ("BUILD", "REWORK", "STEP", "VERIFY", "ARTIFACT")
    assert B.ORDER == ("STEP", "VERIFY", "ARTIFACT", "REWORK", "BUILD")


def named(name):
    return next(c for c in CASES if c["name"] == name)


def run_intents(tmp_path, name):
    tokens = tokens_for(tmp_path)
    world = subst(named(name)["world"], tokens)
    lay_out(tokens, world)
    return tokens, world, B.intents(Ctx(tokens, world))


def test_verify_evidence_fingerprint_is_the_packet_digest_and_the_checks(tmp_path):
    tokens, world, got = run_intents(tmp_path, "verify_registered_head_with_green_checks")
    packet = Path(tokens["repo"], "00_ARCHITECTURE/briefs/kalayantra/packets/PACKET_K-1_v1.md").read_bytes()
    want = sha(canonical({"packet_sha256": sha(packet), "checks": world["pr"]["K-1"]["checks"]}))
    assert got[0]["evidence_fp"] == want
    # a different check result, or a different packet, is different evidence: the job key moves with it
    world["pr"]["K-1"]["checks"]["CI"]["attempt"] = 2
    assert B.intents(Ctx(tokens, world))[0]["key"] != got[0]["key"]
    world["pr"]["K-1"]["checks"]["CI"]["attempt"] = 1
    assert B.intents(Ctx(tokens, world))[0]["key"] == got[0]["key"]
    Path(tokens["repo"], "00_ARCHITECTURE/briefs/kalayantra/packets/PACKET_K-1_v2.md").write_text(
        packet_text({"build_tier": "sonnet", "max_loops": 3, "v": 2}), encoding="utf-8")
    assert B.intents(Ctx(tokens, world))[0]["key"] != got[0]["key"]


def test_intents_are_the_same_on_every_tick(tmp_path):
    """Nothing in an intent depends on a clock or on the order of a dict: two ticks over one world agree."""
    tokens, world, got = run_intents(tmp_path, "order_step_verify_artifact_rework_build")
    assert B.intents(Ctx(tokens, world)) == got


def test_a_retried_ci_failure_becomes_code_class_under_a_new_key(tmp_path):
    """The packet's "a retried, then code-class CI failure" as one story: attempt 1 → a script rerun; the same
    check failing at attempt 2 → a model REWORK, and not the retry's job key again."""
    tokens, world, first = run_intents(tmp_path, "ci_first_failure_is_retried_without_a_model")
    assert [(i["runner"], i["header"].get("action")) for i in first] == [("script", "retry_ci")]
    for check in world["pr"]["K-1"]["checks"].values():
        if check["status"] == "FAILURE":
            check["attempt"] = 2
    world["sh"] = [{"match": ["kyroute.py", "escalate"], "rc": 0, "out": '{"decision": "CONTINUE"}'}]
    second = B.intents(Ctx(tokens, world))
    assert [(i["kind"], i["runner"], i["tier"], i["header"]["reason"]) for i in second] == [
        ("REWORK", "model", "sonnet", "ci")]
    assert second[0]["key"] != first[0]["key"]


def test_an_unfinished_step_action_is_reconciled_from_the_event_log_not_repeated(tmp_path):
    case = named("start_step_records_the_step_after_the_detector_passes")
    job_id = case["job"]["job_id"]
    tokens = tokens_for(tmp_path, job_id)
    world = subst(case["world"], tokens)
    lay_out(tokens, world)
    intent = B.intents(Ctx(tokens, world))[0]
    job = make_job(intent, tokens, subst(case["job"], tokens))
    os.makedirs(tokens["jobdir"])
    world = dict(world, act="unfinished", ky=[], events={"K-1": [
        {"kind": "item", "actor": "stream-K", "item": "K-1", "state": "done", "step": "b"}]})
    ctx = Ctx(tokens, world)
    assert B.start(ctx, job)["outcome"] == "done"
    assert not any("ky" in c for c in ctx.calls), "the step is in the log: ky step is not run a second time"
    # the control: the log does not show the step → the effect runs (and here has no scripted reply)
    ctx = Ctx(tokens, dict(world, events={"K-1": []}))
    with pytest.raises(AssertionError, match="scripts no reply for ky"):
        B.start(ctx, job)


@pytest.mark.parametrize("bad", [None, "", "relative/scratch"])
def test_a_job_without_an_absolute_scratch_gets_no_diff_no_snapshot_and_no_verdict(tmp_path, bad):
    case = named("start_verify_writes_the_pr_diff_and_the_snapshot")
    tokens = tokens_for(tmp_path, case["job"]["job_id"])
    world = subst(case["world"], tokens)
    lay_out(tokens, world)
    intent = B.intents(Ctx(tokens, world))[0]
    job = make_job(intent, tokens, subst(case["job"], tokens))
    job["job_scratch"] = bad
    ctx = Ctx(tokens, world)
    result = B.start(ctx, job)
    assert result["outcome"] == "refused" and result["failure_fp"] == "job_scratch_unknown"
    assert not any(c.get("sh", [""])[0] == "gh" or "kyverdicts.py" in " ".join(c.get("sh", [])) for c in ctx.calls)
    result = B.finish(ctx, job)
    assert result["outcome"] == "failed" and result["failure_fp"] == "job_scratch_unknown"
    assert not any("kyverdicts.py" in " ".join(c.get("sh", [])) for c in ctx.calls), "nothing published"


def test_an_unknown_kind_is_never_launched_or_finished_as_done(tmp_path):
    tokens = tokens_for(tmp_path, "J-1")
    lay_out(tokens, {})
    ctx = Ctx(tokens, {"next": {"running": [], "ready": [], "blocked": []}})
    job = {"job_id": "J-1", "kind": "MERGE", "item": "K-1", "key": "MERGE.K-1.000000000000"}
    assert B.start(ctx, job)["outcome"] == "refused"
    assert B.finish(ctx, job)["outcome"] == "failed"
    assert ctx.calls == []


def test_the_module_imports_only_local_jobs_and_standard_library_and_runs_nothing_on_import():
    source = (FLEET / "kyd_kinds_build.py").read_text(encoding="utf-8")
    imported = set(re.findall(r"^(?:import|from) ([a-z_]+)", source, flags=re.M))
    assert imported <= {"__future__", "hashlib", "json", "os", "re", "kyd_jobs", "kyverdicts"}, imported
    assert "subprocess" not in imported, "every command goes through ctx.sh, ctx.ky or ctx.act"


@pytest.mark.parametrize("item,step", [("K7-3", "density_contracts"), ("K6-5", "reference_protection_switched")])
@pytest.mark.parametrize("named,passed", [(False, True), (True, False), (True, None), (True, True)])
def test_real_step_declarations_require_a_named_detector(tmp_path, item, step, named, passed):
    """The real {evidence, detector:null} declaration is a known wait, never a detector to query."""
    fixture = json.loads((HERE / "post_install_tracker.json").read_text(encoding="utf-8"))
    row = next(r for r in fixture["next"]["running"] if r["id"] == item)
    if named:
        row["step_evidence"][step]["detector"] = {"type": "file_exists", "path": str(tmp_path / "measured")}
    world = {"next": {"running": [row], "ready": [], "blocked": []}, "verify": {item + "/" + step: passed}}
    tokens = tokens_for(tmp_path)
    lay_out(tokens, world)
    ctx = Ctx(tokens, world)
    got = B.intents(ctx)
    assert [(i["kind"], i["item"], i["header"]["step"]) for i in got] == (
        [("STEP", item, step)] if named and passed is True else [])
    assert ctx.calls == ([{"verify": [item, step]}] if named else [])
