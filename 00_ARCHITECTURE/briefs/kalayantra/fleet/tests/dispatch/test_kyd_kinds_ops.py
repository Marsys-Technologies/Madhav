"""KV3-B-KYDKINDS-OPS: the eight operation/ruling kinds of the dispatcher (relaunch plan v2.7 §6 REQUEST-PREP … PLAN).

`kinds_ops.json` holds the cases. Each case builds a recording ctx double over a throwaway directory, lays down its
files (the plan model the ctx names among them: `ctx.model`), and runs steps — `intents`, `start`, `finish`, `mutate`, `restart` — comparing what the module answered with the
case's expectations: the intents, the exact calls it made (argv of every `sh` / `ky`, every action record, journal line
and awaiting item), the files it wrote, and the files it must not have written.

The tracker's answers are in the shapes pravaha_tracker emits (review r5 KO5-B1): `next` is the `ky next --json`
object {stream, version, running, ready, blocked} of item rows as state.build_snapshot writes them, `events` are
EVENTS.jsonl lines ({kind: item, state: review | blocked}, {kind: verdict}), the inbox rows are message events, and
brief / done_by / join are in the plan model only; declared models also put completion_kind, producer,
reviewer_rule and step_evidence on snapshot rows (TRACKER packet contract 7). `test_the_fixtures_use_the_trackers_shapes`
holds every case to that, against the tracker's own source.

The double starts no process and touches no network: an `sh` or `ky` call no case answered is recorded and fails the
case. The real `ky`, `gh`, executor, kyverdicts and kyboundary are never run. `executor.py` is imported (not run) in
one test only, to prove the static pre-check agrees with its `validate`.
"""
import copy
import hashlib
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
FLEET = HERE.parent.parent
CASES_PATH = HERE / "kinds_ops.json"
MODULE_PATH = FLEET / "kyd_kinds_ops.py"
EXECUTOR_PATH = FLEET / "executor.py"
TABLE_ARGV_TAIL = "origin/main:00_ARCHITECTURE/briefs/kalayantra/fleet/executor_ops.json"
INTENT_FIELDS = {"kind", "item", "key", "stream", "role", "pool", "runner", "queue", "claim", "locks", "tier",
                 "not_slot", "head", "digest", "verdict_phase", "evidence_fp", "card", "packet", "header"}
KEY_RE = re.compile(r"^[A-Z-]+\.[^.\s][^\s]*\.[0-9a-f]{12}$")
MODEL_REL = "00_ARCHITECTURE/control/kalayantra/plan_model.json"
TRACKER = FLEET.parents[3] / "platform" / "scripts" / "governance" / "pravaha_tracker"
EMPTY_NEXT = {"stream": "", "version": 1, "running": [], "ready": [], "blocked": []}
NEXT_STATUSES = {"running": ("running", "review"), "ready": ("ready",), "blocked": ("blocked", "failed", "parked", "conflict")}
# the keys of an item row: state.py build_snapshot (id … cross_stream, **item_status(), deps_open*, the D-46 activation
# fields activation_pending / built_waiting_on_gate / gate_blockers, elapsed_s)
ROW_KEYS = {"id", "title", "lane", "gate", "owner", "depends_on", "cross_stream", "status", "source", "detail", "progress",
            "actor", "evidence", "started_at", "updated_at", "checked_at", "deps_open", "deps_open_strict", "elapsed_s",
            "activation_pending", "built_waiting_on_gate", "gate_blockers"}
# what item_status / build_snapshot add to some rows only
ROW_EXTRAS = {"steps", "outcome", "detector_warning", "deps_merged_pending_deploy", "gaps", "skip_origin"}
ROW_DECLARATIONS = {"completion_kind", "producer", "reviewer_rule", "step_evidence"}


def load_module(name="kyd_kinds_ops_under_test"):
    spec = importlib.util.spec_from_file_location(name, MODULE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_DIGEST = []


def _request_digest():
    """kyd_kinds_ops.request_digest, loaded once for the fixture resolver; test_request_digest_is_the_executors pins it to executor.request_digest."""
    if not _DIGEST:
        _DIGEST.append(load_module("kyd_kinds_ops_request_digest").request_digest)
    return _DIGEST[0]


DOC = json.loads(CASES_PATH.read_text(encoding="utf-8"))
CASES = DOC["cases"]
# the cases that lay down a shape the tracker does NOT emit, on purpose (each says so in its steps): everything else is
# held to the tracker's own shapes by `tracker_shape_faults`
FOREIGN = {"rp_an_unrecognised_tracker_answer_is_unknown_not_an_empty_tracker",
           "model_finish_reads_review_and_block_as_the_tracker_writes_them",
           "prb_a_the_author_and_the_excluded_slot_are_the_review_events_actor",
           "plan_an_unknown_tracker_or_plan_model_is_no_wave_boundary",
           "plan_the_wave_boundary_is_open_items_none_ready_none_running_admitted",
           "ruling_an_inbox_row_that_is_no_message_event_is_unknown"}


def tracker(name):
    """A module of the tracker package in this working copy (imported, never run): the producer of the shapes."""
    if str(TRACKER.parent) not in sys.path:
        sys.path.insert(0, str(TRACKER.parent))
    return importlib.import_module("pravaha_tracker." + name)


def tracker_shape_faults(spec):
    """What in a case's `next`, `events`, inbox rows or plan model is not what pravaha_tracker emits."""
    events, bad = tracker("events"), []
    nxt = spec.get("next", EMPTY_NEXT)
    if nxt is not None:
        if not isinstance(nxt, dict) or set(nxt) != {"stream", "version", "running", "ready", "blocked"}:
            bad.append("next is not the /api/next object: %r" % (sorted(nxt) if isinstance(nxt, dict) else nxt,))
        else:
            for bucket, statuses in NEXT_STATUSES.items():
                for row in nxt[bucket]:
                    if not ROW_KEYS <= set(row) <= ROW_KEYS | ROW_EXTRAS | ROW_DECLARATIONS or row["status"] not in statuses:
                        bad.append("next.%s row %r is not a build_snapshot item row" % (bucket, row.get("id")))
    for item, lines in (spec.get("events") or {}).items():
        for line in lines or []:
            try:
                events.validate(line)
            except events.EventError as exc:
                bad.append("event of %s refused by events.validate: %s (%r)" % (item, exc, line))
                continue
            if line["kind"] in ("item", "verdict") and line.get("item") != item:
                bad.append("event filed under %s names item %r" % (item, line.get("item")))
    for answer in spec.get("ky", []):
        if answer["match"][:1] == ["inbox"] and answer.get("rc", 0) == 0 and isinstance(answer.get("out"), list):
            for line in answer["out"]:
                try:
                    events.validate(line, allow_model_party=True)
                    assert line["kind"] == "message" and line["to"] == "N"
                except (events.EventError, AssertionError, TypeError, KeyError) as exc:
                    bad.append("inbox row is not a message event to N: %s (%r)" % (exc, line))
    model = spec.get("model", {"items": []})
    if isinstance(model, dict) and isinstance(model.get("items"), list):
        for item in model["items"]:
            if isinstance(item, dict) and {"status", "ready"} & set(item):
                bad.append("plan model item %r carries tracker state" % item.get("id"))
    return bad


def canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ───────────────────────────────────────── the ctx double ─────────────────────────────────────────

class Double:
    """The engine's ctx as the packet describes it, recording every call. Nothing here spawns a process."""

    def __init__(self, base, spec, table):
        self.base = Path(base)
        self.root = self.base / "root"
        self.run = self.root / "run"
        self.fleet = self.base / "fleet"
        self.repo = self.base / "repo"
        self.scratch = self.base / "scratch"
        for d in (self.run, self.fleet, self.repo, self.scratch):
            d.mkdir(parents=True, exist_ok=True)
        (self.fleet / "templates").mkdir(exist_ok=True)
        (self.fleet / "templates/LAUNCH_CONFIG.surrogate.json").write_bytes(
            (FLEET / "templates/LAUNCH_CONFIG.surrogate.json").read_bytes())
        self.spec = spec
        self.table = table
        self.calls = []
        self.unmatched = []
        self.next = spec.get("next", EMPTY_NEXT)
        self.act_file = self.base / "act_done.json"
        if not spec.get("no_model_attr"):                              # the engine's ctx names the plan model by path
            self.model = str(self.repo / MODEL_REL)
        self.put_model()

    def put_model(self):
        """The plan model file: the case's `model` (an object, raw text, or null for no file); none given → no items."""
        path = self.repo / MODEL_REL
        content = self.spec.get("model", {"items": []})
        path.parent.mkdir(parents=True, exist_ok=True)
        if content is None:
            if path.exists():
                path.unlink()
        else:
            path.write_text(content if isinstance(content, str) else json.dumps(content), encoding="utf-8")

    def veto_status(self):
        """kyveto.status() as the engine hands it over; a case that names none gets the unreadable answer."""
        return self.spec.get("veto")

    # -- the contract surface
    def sh(self, argv, env=None, cwd=None, timeout=120):
        argv = list(argv)
        if argv[:2] == ["git", "-C"] and argv[3:5] == ["show", TABLE_ARGV_TAIL] and argv[2] == str(self.repo):
            self.calls.append({"fn": "table", "argv": argv})
            rc = self.spec.get("table_rc", 0)
            return rc, (json.dumps({"ops": self.table}) if rc == 0 else ""), ("" if rc == 0 else "fatal")
        self.calls.append({"fn": "sh", "argv": argv})
        return self._answer(self.spec.get("sh", []), argv)

    def ky(self, *args, stream=None, lane=None):
        args = list(args)
        self.calls.append({"fn": "ky", "args": args, "stream": stream, "lane": lane})
        if args[:1] == ["inbox"] and not any(args[:len(r["match"])] == r["match"] for r in self.spec.get("ky", [])):
            return 1, "[]", ""                                         # an inbox no case filled is an empty one (ky inbox --json: exit 1, [])
        return self._answer(self.spec.get("ky", []), args)

    def _answer(self, table, argv):
        for row in table:
            m = row["match"]
            if argv[:len(m)] == m:
                out = row.get("out", "")
                return row.get("rc", 0), (out if isinstance(out, str) else json.dumps(out)), row.get("err", "")
        self.unmatched.append(argv)
        return 127, "", "unmatched in the test double"

    def act(self, action_id, kind, inputs, target, effect, observer):
        done = json.loads(self.act_file.read_text()) if self.act_file.exists() else {}
        call = {"fn": "act", "id": action_id, "kind": kind, "inputs": inputs, "target": target}
        self.calls.append(call)
        if action_id in done:
            call["replayed"] = True
            return "done", done[action_id]
        mode = next((m for prefix, m in self.spec.get("act", {}).items() if action_id.startswith(prefix)), None)
        if mode == "unknown":
            return "unknown", {}
        if mode == "failed":
            return "failed", {"error": "injected"}
        verdict, observed = observer({"action_id": action_id, "kind": kind, "inputs": inputs, "target": target})
        if verdict == "unknown":
            return "unknown", {}
        if verdict == "done":
            call["observed_done"] = True
            result = observed
        else:
            try:
                result = effect()
            except Exception as exc:                                   # kyaction: the observed failure is recorded
                return "failed", {"error": "%s: %s" % (type(exc).__name__, exc)}
            if mode == "crash_after_effect":
                return "unknown", {}
        done[action_id] = result
        self.act_file.write_text(json.dumps(done))
        return "done", result

    def awaiting(self, slug, question, options, evidence, item, class_hint):
        self.calls.append({"fn": "awaiting", "slug": slug, "item": item, "class_hint": class_hint,
                           "question": question, "options": options, "evidence": evidence})
        d = self.run / "awaiting"
        d.mkdir(parents=True, exist_ok=True)
        (d / ("AW-20261012T120000Z-%s.json" % slug)).write_text(json.dumps({"id": "AW-20261012T120000Z-" + slug}))
        return {"slug": slug}

    def journal(self, event, text):
        self.calls.append({"fn": "journal", "event": event, "text": text})
        if self.spec.get("journal_raises"):                            # a journal that cannot be written (a crash point)
            raise OSError("journal unwritable in the test double")

    def events(self, item):
        return self.spec.get("events", {}).get(item, [])

    def pr(self, item):
        return self.spec.get("prs", {}).get(item)

    def now(self):
        return "2026-10-12T12:00:00Z"


# ───────────────────────────────────────── placeholders ─────────────────────────────────────────

class Resolver:
    def __init__(self, double, defs):
        self.d, self.defs = double, defs

    def text(self, s):
        s = re.sub(r"\{\{first12:(\w+)\}\}", lambda m: str(self(self.defs[m.group(1)]))[:12], s)
        s = re.sub(r"\{\{sha:(\w+)\}\}", lambda m: str(self(self.defs[m.group(1)])), s)      # a def's digest inside prose, never a literal hash
        return (s.replace("$JOB_SCRATCH", str(self.d.scratch / "jobs" / "J-test-1")).replace("$SCRATCH", str(self.d.scratch))
                .replace("$RUN", str(self.d.run)).replace("$FLEET", str(self.d.fleet)).replace("$REPO", str(self.d.repo))
                .replace("$WT", str(self.d.base / "wt")))

    def __call__(self, x):
        if isinstance(x, str):
            return self.text(x)
        if isinstance(x, list):
            return [self(v) for v in x]
        if isinstance(x, dict):
            if len(x) == 1:
                (k, v), = x.items()
                if k == "$ref":
                    return self(copy.deepcopy(self.defs[v]))
                if k == "$canon_sha":
                    return sha_text(canon(self(v)))
                if k == "$request_sha":                           # the digest an acceptance binds: executor.request_digest, which A8 §3.9 keeps
                    return _request_digest()(self(v))              # clear of acceptance_receipt, expires_at and any *_expires_at field
                if k == "$sha_text":
                    return sha_text(self(v))
                if k == "$sha256_file":
                    p = Path(self(v))
                    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
                if k == "$key":
                    kind, item, ident, fp = [self(e) for e in v]
                    return "%s.%s.%s" % (kind, item, sha_text(canon([ident, fp]))[:12])
                if k == "$cat":
                    return "".join(str(self(e)) for e in v)
                if k == "$first":
                    return str(self(v[1]))[:v[0]]
                if k == "$set":                                       # {"$set": {...}} — a dict with several keys
                    return {kk: self(vv) for kk, vv in v.items()}
            return {kk: self(vv) for kk, vv in x.items()}
        return x


ANY = "$any"


def subset(expected, actual, path="$"):
    """Every field `expected` names must match; dicts match as subsets, lists elementwise with equal length."""
    if expected == ANY:
        return []
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return ["%s: expected an object, got %r" % (path, actual)]
        bad = []
        for k, v in expected.items():
            if k not in actual:
                bad.append("%s.%s: missing" % (path, k))
            else:
                bad += subset(v, actual[k], "%s.%s" % (path, k))
        return bad
    if isinstance(expected, list):
        if not isinstance(actual, list) or len(expected) != len(actual):
            return ["%s: expected %d items, got %r" % (path, len(expected), actual)]
        bad = []
        for i, (e, a) in enumerate(zip(expected, actual)):
            bad += subset(e, a, "%s[%d]" % (path, i))
        return bad
    return [] if expected == actual else ["%s: expected %r, got %r" % (path, expected, actual)]


def tree(base):
    out = {}
    for p in sorted(Path(base).rglob("*")):
        if p.is_file() and p.name != "act_done.json":
            out[str(p)] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def put_files(resolve, files):
    for name, content in files.items():
        p = Path(resolve(name))
        p.parent.mkdir(parents=True, exist_ok=True)
        if content is None:
            if p.exists():
                p.unlink()
            continue
        content = resolve(content)
        p.write_text(content if isinstance(content, str) else json.dumps(content, indent=1), encoding="utf-8")


def merge_spec(spec, delta):
    for k, v in delta.items():
        if k == "files":
            continue
        if k in ("events", "prs", "act") and isinstance(v, dict) and isinstance(spec.get(k), dict):
            spec[k].update(v)
        else:
            spec[k] = v


# ───────────────────────────────────────── the runner ─────────────────────────────────────────

def run_case(case, tmp_path):
    mod = load_module()
    defs = DOC.get("defs", {})
    spec = copy.deepcopy(case.get("ctx", {}))
    double = Double(tmp_path, spec, DOC["table"])
    resolve = Resolver(double, defs)
    # `next`, `sh`, `ky`, `veto`, `events`, `prs` may carry placeholders: resolve when set
    for k in ("next", "sh", "ky", "veto", "events", "prs", "act"):
        if k in spec:
            spec[k] = resolve(spec[k])
    double.next = spec.get("next", EMPTY_NEXT)
    put_files(resolve, case.get("files", {}))
    last_intents, failures = [], []

    def check(label, bad):
        failures.extend("%s: %s" % (label, b) for b in bad)

    if case["name"] not in FOREIGN:
        check(case["name"] + " fixture", tracker_shape_faults(spec))

    for n, step in enumerate(case["steps"]):
        label = "%s step %d (%s)" % (case["name"], n, step["op"])
        if "mutate" in step:
            delta = step["mutate"]
            merge_spec(spec, resolve({k: v for k, v in delta.items() if k != "files"}))
            double.next = spec.get("next", EMPTY_NEXT)
            double.put_model()
            if case["name"] not in FOREIGN:
                check(label + " fixture", tracker_shape_faults(spec))
            put_files(resolve, delta.get("files", {}))
        double.calls.clear()
        if step["op"] == "mutate":
            continue
        if step["op"] == "restart":
            double = Double(tmp_path, spec, DOC["table"])
            resolve = Resolver(double, defs)
            double.next = spec.get("next", EMPTY_NEXT)
            last_intents = []
            continue
        if step["op"] == "intents":
            before = tree(tmp_path)
            got = mod.intents(double)
            check(label + " read-only tree", [] if tree(tmp_path) == before else ["intents() changed files"])
            said = [c for c in double.calls if c["fn"] == "journal"]     # at most the one `ops_unknown` line of the tick
            side = [c for c in double.calls if c["fn"] not in ("table", "journal") and not (c["fn"] == "ky" and c["args"][:1] == ["inbox"])]
            check(label + " read-only calls", [] if not side else ["intents() made side-effect calls: %r" % side])
            check(label + " one unknown line", [] if len(said) <= 1 and all(c["event"] == "ops_unknown" for c in said)
                  else ["intents() journalled %r" % said])
            wanted = step.get("unknown")                                 # the reasons the tick must say; none named → none said
            text = said[0]["text"] if said else ""
            if wanted is None:
                check(label + " unknown", [] if not said else ["an unknown was journalled that the case does not name: %s" % text])
            else:
                check(label + " unknown", ["no unknown was journalled"] if not said
                      else ["the journal line lacks %r: %s" % (w, text) for w in resolve(wanted) if w not in text])
            for it in got:
                check(label + " intent shape", [] if set(it) == INTENT_FIELDS else ["fields %r" % sorted(set(it) ^ INTENT_FIELDS)])
                check(label + " intent contract", [] if (KEY_RE.match(it["key"]) and it["role"] == it["kind"].lower()
                                                         and it["locks"][0] == "job." + it["key"]
                                                         and it["runner"] in ("model", "script")
                                                         and it["pool"] in ("builder", "verifier", None)
                                                         and it["claim"] in ("K", "V", None)
                                                         and it["header"]["locks"] == it["locks"])
                      else ["bad intent %r" % it])
            last_intents = got or last_intents                       # a later job step may refer to the last non-empty tick
            expected = resolve(step["expect"])
            check(label, subset(expected, got))
        else:
            idx = step.get("intent", 0)
            base_job = {"job_id": "J-test-1", "worktree": str(double.base / "wt"), "slot": None, "controller_id": "ctl-1",
                        "job_scratch": str(double.scratch / "jobs" / "J-test-1"),
                        "result_path": str(double.scratch / "jobs" / "J-test-1" / "result.json"),
                        "exit_code": 0, "provider_session_id": None, "phase": "prepared"}
            Path(base_job["job_scratch"]).mkdir(parents=True, exist_ok=True)
            Path(base_job["worktree"]).mkdir(parents=True, exist_ok=True)
            src = last_intents[idx] if last_intents else {}
            for k in ("key", "item", "kind", "role", "stream", "head", "digest", "verdict_phase", "evidence_fp", "locks"):
                if k in src:
                    base_job[k] = src[k]
            base_job.update(resolve(step.get("job", {})))
            if "files_before" in step:
                put_files(resolve, step["files_before"])
            fn = mod.start if step["op"] == "start" else mod.finish
            before = tree(tmp_path) if step.get("unchanged") else None
            result = fn(double, base_job)
            if "result" in step:
                check(label + " result", subset(resolve(step["result"]), result) if step["result"] is not None
                      else ([] if result is None else ["expected None (launch), got %r" % (result,)]))
            if before is not None:
                check(label + " unchanged", [] if tree(tmp_path) == before else ["the tree changed"])
        if "calls" in step:
            actual = [c for c in double.calls if c["fn"] != "table" and not (step["op"] == "intents" and c["fn"] == "journal")]
            if not any(c["fn"] == "ky" for c in step["calls"]):         # inbox reads are only listed by the cases about the inbox
                actual = [c for c in actual if not (c["fn"] == "ky" and c["args"][:1] == ["inbox"])]
            check(label + " calls", subset(resolve(step["calls"]), actual))
        for name, want in step.get("files", {}).items():
            p = Path(resolve(name))
            if not p.is_file():
                check(label + " file", ["%s was not written" % p])
                continue
            check(label + " file %s" % p.name, subset(resolve(want), json.loads(p.read_text())))
        for name, want in step.get("files_exact", {}).items():
            p = Path(resolve(name))
            got = json.loads(p.read_text()) if p.is_file() else None
            check(label + " exact %s" % p.name, [] if got == resolve(want) else ["%r != %r" % (got, resolve(want))])
        for name in step.get("absent", []):
            check(label + " absent", [] if not Path(resolve(name)).exists() else ["%s exists" % resolve(name)])
        if step.get("table_read") is not None:
            reads = [c for c in double.calls if c["fn"] == "table"]
            check(label + " table", [] if len(reads) >= step["table_read"] else ["origin/main table was not read"])
    check(case["name"] + " unmatched", [] if not double.unmatched else ["unanswered sh/ky calls: %r" % double.unmatched])
    assert not failures, "\n".join(failures)


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_case(case, tmp_path):
    run_case(case, tmp_path)


# ───────────────────────────────────────── the module's own contract ─────────────────────────────────────────

def test_the_eight_kinds_and_nothing_runs_on_import(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    mod = load_module()
    assert mod.KINDS == ("REQUEST-PREP", "PRE-ACCEPT", "EXECUTE", "POST-READBACK", "MODEL", "RULING", "SURROGATE", "PLAN")
    assert callable(mod.intents) and callable(mod.start) and callable(mod.finish)
    assert list(tmp_path.iterdir()) == []


def test_every_kind_is_exercised_by_a_case():
    covered = {c["covers"] for c in CASES}
    assert covered >= set(load_module().KINDS)


def test_the_cases_cover_each_named_negative():
    names = {c["name"] for c in CASES}
    for required in ("sg_handled_at_fingerprint_launches_no_second_job",
                     "sg_pending_veto_evidence_unchanged_launches_nothing",
                     "sg_hard_stop_evidence_unchanged_launches_nothing",
                     "prb_b_wrong_receipt_digest_publishes_nothing",
                     "prb_b_pre_acceptance_record_publishes_nothing",
                     "prb_b_script_head_verdict_does_not_complete",
                     "prb_b_executor_exit_without_semantic_readback",
                     "sg_one_job_across_ticks_and_restarts",
                     "sg_an_item_the_owner_answered_gets_no_surrogate_job",                 # review r1 KO-B1
                     "sg_start_refuses_an_item_the_owner_answered_under_the_lock",
                     "rp_a_model_authored_request_is_bound_to_the_derived_fields",          # review r1 KO-B2
                     "rp_a_model_authored_production_request_keeps_the_stated_fields",
                     "rp_any_prepared_record_of_the_item_counts_as_prepared",
                     "rp_a_model_authored_request_finishes_with_no_boundary_view",          # review r2 KO2-B1
                     "ruling_finish_with_an_exit_1_inbox_that_is_not_an_empty_list_records_nothing"):  # review r3 KO3-B1
        assert required in names, required


def test_the_cases_cover_review_r4():
    """KO4-B1 and the sweep of its family: nothing a model can write alone, nor an unknown, reads as done."""
    names = {c["name"] for c in CASES}
    for required in ("sg_a_hard_stop_with_a_later_failed_or_executed_line_moves_nothing",              # KO4-B1
                     "sg_a_veto_decision_whose_executed_is_not_backed_by_the_handler_moves_nothing",
                     "sg_start_rechecks_the_move_conditions_under_the_lock",
                     "sg_a_backed_executed_or_vetoed_veto_decision_moves_the_item_to_awaiting_done",
                     "sg_a_vetoed_or_failed_row_moves_only_with_a_record_behind_it",                    # sweep
                     "sg_finish_of_a_decide_job_is_not_done_because_the_item_left_the_queue",
                     "pa_an_acceptance_already_in_place_is_done_only_after_every_check",
                     "rp_a_prepared_record_in_place_is_done_only_for_the_checked_request",
                     "prb_publish_is_done_only_when_kyverdicts_says_published",
                     "prb_a_the_wait_marker_is_written_only_after_its_journal_line",
                     "plan_an_unreadable_packet_set_is_not_a_changed_one",
                     "plan_an_unreadable_repacket_file_is_not_an_empty_one",
                     "ex_an_awaiting_file_that_is_not_its_record_is_not_a_raised_item"):
        assert required in names, required


def test_the_cases_cover_review_r5():
    """KO5-B1 (the tracker's and the plan model's real shapes, one case per kind that fails on the guessed ones) and the
    sweep of both families: an unknown is said, a marker is read back, a producer's shape is the fixture's shape."""
    names = {c["name"] for c in CASES}
    for required in ("rp_a_ready_operation_item_in_the_trackers_shape_gets_a_request_prep_job",       # KO5-B1 (a)
                     "rp_an_unrecognised_tracker_answer_is_unknown_not_an_empty_tracker",
                     "rp_brief_and_completion_kind_come_from_the_plan_model_not_the_row",
                     "rp_a_ctx_that_names_no_plan_model_is_unknown",
                     "rp_the_steps_of_brief_op_are_prepared_in_order",
                     "plan_an_unknown_tracker_or_plan_model_is_no_wave_boundary",
                     "model_finish_reads_review_and_block_as_the_tracker_writes_them",               # KO5-B1 (b)
                     "prb_a_the_author_and_the_excluded_slot_are_the_review_events_actor",
                     "pa_an_unreadable_table_is_said_not_read_as_no_request",                        # the sweep
                     "ex_a_request_the_executor_moved_to_inflight_is_submitted_not_owed_again",
                     "ex_a_refused_receipt_that_names_no_request_raises_the_awaiting_item",
                     "ruling_an_inbox_row_that_is_no_message_event_is_unknown",
                     "ruling_a_handled_marker_that_is_not_the_record_handles_nothing",
                     "plan_a_handled_marker_that_is_not_the_record_handles_nothing",
                     "sg_an_awaiting_file_that_is_no_item_is_said_and_the_others_keep_their_job",
                     "sg_a_handled_decision_that_kyveto_status_does_not_show_is_said",
                     "plan_an_admission_record_is_read_back_not_merely_present",
                     "prb_a_a_pull_request_answer_without_its_state_is_unknown",
                     "ex_a_prepared_request_whose_kind_left_the_table_is_said",
                     "rp_an_operation_id_that_is_another_prepared_records_is_said"):
        assert required in names, required
    assert FOREIGN <= names


@pytest.mark.parametrize("declared", [False, True], ids=["legacy", "declared"])
def test_the_fixtures_use_the_trackers_shapes(declared):
    """The fixture shapes are the producer's, measured against its source in this working copy: the item row keys are
    those of a row state.build_snapshot builds (no brief, done_by or join), `/api/next` answers the object the cases
    use, and the detector that holds every case to them does refuse the guessed shapes of the reviewed head."""
    state = tracker("state")
    model = {"tracks": [{"id": "T", "title": "t"}], "streams": [], "phases": [], "decisions": [],
             "items": [{"id": "X-1", "track": "T", "title": "x", "owner": "N", "completion_kind": "operation",
                        "brief": {"op": ["readback_sql"]}, "done_by": None, "join": False}]}
    if declared:
        model["control_plane"] = {"declarations": {}}
    built = state.build_snapshot(model, [], {}, {}, {})["tracks"][0]["items"][0]
    assert set(built) == ROW_KEYS | (ROW_DECLARATIONS if declared else set()) and built["status"] == "ready"
    if declared:
        assert {key: built[key] for key in ROW_DECLARATIONS} == {
            "completion_kind": "operation", "producer": None, "reviewer_rule": None, "step_evidence": None}
    server = (TRACKER / "server.py").read_text(encoding="utf-8")
    assert 'return self._json({"stream": sid, "version": snap.get("version"),' in server
    for bucket, statuses in NEXT_STATUSES.items():
        tests = ('t["status"] == "%s"' % statuses[0] if len(statuses) == 1
                 else 't["status"] in (%s)' % ", ".join('"%s"' % s for s in statuses))
        assert '"%s": [t for t in mine if %s]' % (bucket, tests) in server, bucket
    good = {"next": dict(EMPTY_NEXT, ready=[dict(built)]),
            "events": {"X-1": [{"kind": "item", "actor": "stream-N:b1", "item": "X-1", "state": "review"}]}}
    assert tracker_shape_faults(good) == []
    for guessed in ({"next": [{"id": "X-1", "owner": "N", "status": "ready", "brief": {}}]},                    # a flat list
                    {"next": {"items": []}},
                    {"next": dict(EMPTY_NEXT, ready=[{k: v for k, v in built.items() if k != "status"}])},       # missing status
                    {"next": dict(EMPTY_NEXT, ready=[dict(built, unknown_field=True)])},                        # undocumented key
                    {"next": dict(EMPTY_NEXT, ready=[dict(built, brief={"op": ["readback_sql"]})])},            # a brief on the row
                    {"next": dict(EMPTY_NEXT, running=[dict(built)])},                                          # ready, in `running`
                    {"events": {"X-1": [{"type": "review", "actor": "stream-K:b2", "lane": "b2"}]}},
                    {"events": {"X-1": [{"type": "verdict", "phase": "artifact", "result": "ACCEPTED"}]}},
                    {"ky": [{"match": ["inbox"], "out": [{"msg_id": "M-1", "from": "S", "text": "x"}]}]},
                    {"model": {"items": [{"id": "X-1", "status": "ready"}]}}):
        assert tracker_shape_faults(guessed), guessed


@pytest.mark.parametrize("broken", ["missing_id", "missing_status", "wrong_status"])
def test_a_malformed_declared_tracker_row_is_unknown_and_journalled(tmp_path, broken):
    """Declaration fields do not make malformed producer rows valid or an empty wave boundary."""
    model = {"tracks": [{"id": "T", "title": "t"}], "streams": [], "phases": [], "decisions": [],
             "control_plane": {"declarations": {}},
             "items": [{"id": "X-1", "track": "T", "title": "x", "owner": "S", "completion_kind": "artifact",
                        "producer": "S", "reviewer_rule": "v_artifact_digest_reviewer_not_author"}]}
    row = tracker("state").build_snapshot(model, [], {}, {}, {})["tracks"][0]["items"][0]
    if broken == "wrong_status":
        row["status"] = "running"                          # in the ready bucket
    else:
        row.pop("id" if broken == "missing_id" else "status")
    spec = {"next": dict(EMPTY_NEXT, ready=[row]), "model": model}
    assert tracker_shape_faults(spec)
    double = Double(tmp_path, spec, DOC["table"])
    assert load_module().intents(double) == []
    said = [c for c in double.calls if c["fn"] == "journal"]
    assert len(said) == 1 and said[0]["event"] == "ops_unknown"
    assert "not a tracker item row with that status" in said[0]["text"]


def test_intents_on_the_trackers_own_snapshot_of_the_campaigns_plan_model(tmp_path):
    """End to end on the producers themselves (review r5 KO5-B1): the campaign's plan model, the snapshot
    pravaha_tracker's state.build_snapshot makes of it, bucketed as server.py /api/next does, and the operations table
    in this working copy. A ready N-owned operation item and a ready S-owned item get their jobs; nothing is unknown."""
    state = tracker("state")
    root = FLEET.parents[3]
    model = json.loads((root / MODEL_REL).read_text(encoding="utf-8"))
    table = json.loads((FLEET / "executor_ops.json").read_text(encoding="utf-8"))["ops"]
    items = {i["id"]: i for i in model["items"]}
    usable = lambda e: bool(e) and e.get("enabled") and "TO_BE_SET" not in str(e.get("script", "")) + str(e.get("needs", ""))
    operation = next((i for i in model["items"] if i.get("owner") == "N" and i.get("completion_kind") == "operation"
                      and isinstance(i["brief"].get("op"), list) and usable(table.get(i["brief"]["op"][0]))), None)
    assert operation is not None, "the plan model has no N-owned operation item whose first kind is enabled in the table"
    done, todo = set(), list(operation.get("depends_on", []))
    while todo:                                                        # every dependency of it, completed under the guard
        dep = todo.pop()
        if dep not in done:
            done.add(dep)
            todo.extend(items[dep].get("depends_on", []))
    ts = "2026-10-12T11:00:00+00:00"
    events = [{"kind": "decision", "actor": "steward", "decision": d["id"], "state": "decided", "outcome": "approved", "detail": "x", "ts": ts}
              for d in model.get("decisions", [])]
    events += [{"kind": "item", "actor": "steward", "item": dep, "state": "done", "guarded": True, "evidence": "fixture", "ts": ts}
               for dep in sorted(done)]
    pending = {i: {"status": "pending", "detail": "not matched", "checked_at": ts} for i in items}
    snap = state.build_snapshot(model, events, pending, {}, {})
    flat = [t for tr in snap["tracks"] for t in tr["items"]]
    answer = {"stream": "", "version": 3,                              # server.py do_GET /api/next, sid == ""
              "running": [t for t in flat if t["status"] in ("running", "review")],
              "ready": [t for t in flat if t["status"] == "ready"],
              "blocked": [t for t in flat if t["status"] in ("blocked", "failed", "parked", "conflict")]}
    assert operation["id"] in {t["id"] for t in answer["ready"]}, "the fixture events did not make the operation item ready"
    spec = {"next": json.loads(json.dumps(answer)), "model": model, "events": {}}
    assert tracker_shape_faults(spec) == []
    double = Double(tmp_path, spec, table)
    got = load_module().intents(double)
    said = [c for c in double.calls if c["fn"] == "journal"]
    assert said == [], said
    owed = {(i["kind"], i["item"]) for i in got}
    assert ("REQUEST-PREP", operation["id"]) in owed
    prep = next(i for i in got if i["kind"] == "REQUEST-PREP" and i["item"] == operation["id"])
    assert prep["runner"] == "model"                                   # a kind name states no kyd: the request needs authoring
    ready_s = {t["id"] for t in answer["ready"] if t["owner"] == "S" and items[t["id"]].get("done_by") not in ("decision", "join")
               and items[t["id"]].get("join") is not True} - {"C-3", "C-4"}
    assert {item for kind, item in owed if kind == "MODEL"} == ready_s
    assert not any(kind == "PLAN" for kind, _ in owed)                 # ready work is in flight: no wave boundary


def test_job_key_is_twelve_hex_of_the_head_or_digest_and_evidence_fp():
    mod = load_module()
    assert mod.job_key("SURROGATE", "AW-1", "a" * 64, "b" * 64) == "SURROGATE.AW-1.%s" % sha_text(canon(["a" * 64, "b" * 64]))[:12]


def test_request_digest_is_the_executors():
    """The request digest is executor.request_digest byte for byte, and the static pre-check agrees with
    executor.validate on every non-production request (imported, never run)."""
    mod = load_module()
    spec = importlib.util.spec_from_file_location("executor_for_comparison", EXECUTOR_PATH)
    old = os.environ.get("KY_ROOT")
    os.environ["KY_ROOT"] = "/nonexistent-ky-root-for-test"
    try:
        ex = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ex)
    finally:
        if old is None:
            os.environ.pop("KY_ROOT")
        else:
            os.environ["KY_ROOT"] = old
    table = DOC["table"]
    caps = {"pgenv": True, "builder": True, "owner": True, "gcloud": True, "none": True}
    base = {"operation_id": "OP-X-1", "kind": "readback_sql", "item_id": "X-1", "idempotency_key": "OP-X-1",
            "requested_by": "adhikarin", "kyd": "KYD-1", "args": {"sql_file": "/a/b.sql"}}
    assert mod.SAFE_ID.pattern == ex.SAFE_ID.pattern and mod.SAFE_ARG.pattern == ex.SAFE_ARG.pattern
    assert mod.CANONICAL_CHART == ex.CANONICAL_CHART
    assert mod.request_digest(dict(base, acceptance_receipt="/x")) == ex.request_digest(base) == mod.request_digest(base)
    timed = dict(base, expires_at="2026-10-18T00:00:00+00:00", lease_expires_at="2026-10-18T06:00:00+00:00")   # A8 §3.9: clocks are outside the digest, in both
    assert mod.request_digest(timed) == ex.request_digest(timed) == ex.request_digest(base)
    changed = dict(base, args={"sql_file": "/a/c.sql"})
    assert mod.request_digest(changed) == ex.request_digest(changed) != ex.request_digest(base)
    variants = [base,
                dict(base, kind="layer_verify"),                                  # disabled
                dict(base, kind="nothing_like_it"),                               # unknown
                dict(base, kind="tobeset"),                                       # enabled but TO_BE_SET
                dict(base, requested_by="v3"),                                    # not a requester
                dict(base, args={"other": "x"}),                                  # not an allowed arg
                dict(base, args={"sql_file": "a b; rm"}),                         # unsafe value
                dict(base, operation_id="bad id"),
                dict(base, kyd=""),
                dict(base, requested_by="")]
    for req in variants:
        entry = table.get(req["kind"])
        mine = mod.static_validate(req, entry)
        theirs = ex.validate(req, table, caps, reserved=True)
        assert (mine is None) == (theirs is None), (req, mine, theirs)
