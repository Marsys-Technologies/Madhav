"""KV3-B-KYDKINDS-OPS: the eight operation/ruling kinds of the dispatcher (relaunch plan v2.7 §6 REQUEST-PREP … PLAN).

`kinds_ops.json` holds the cases. Each case builds a recording ctx double over a throwaway directory, lays down its
files, and runs steps — `intents`, `start`, `finish`, `mutate`, `restart` — comparing what the module answered with the
case's expectations: the intents, the exact calls it made (argv of every `sh` / `ky`, every action record, journal line
and awaiting item), the files it wrote, and the files it must not have written.

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


def load_module(name="kyd_kinds_ops_under_test"):
    spec = importlib.util.spec_from_file_location(name, MODULE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


DOC = json.loads(CASES_PATH.read_text(encoding="utf-8"))
CASES = DOC["cases"]


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
        self.spec = spec
        self.table = table
        self.calls = []
        self.unmatched = []
        self.next = spec.get("next", [])
        self.act_file = self.base / "act_done.json"

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
            return 1, "", ""                                           # an inbox no case filled is an empty one (ky inbox: exit 1)
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
    double.next = spec.get("next", [])
    put_files(resolve, case.get("files", {}))
    last_intents, failures = [], []

    def check(label, bad):
        failures.extend("%s: %s" % (label, b) for b in bad)

    for n, step in enumerate(case["steps"]):
        label = "%s step %d (%s)" % (case["name"], n, step["op"])
        if "mutate" in step:
            delta = step["mutate"]
            merge_spec(spec, resolve({k: v for k, v in delta.items() if k != "files"}))
            double.next = spec.get("next", [])
            put_files(resolve, delta.get("files", {}))
        double.calls.clear()
        if step["op"] == "mutate":
            continue
        if step["op"] == "restart":
            double = Double(tmp_path, spec, DOC["table"])
            resolve = Resolver(double, defs)
            double.next = spec.get("next", [])
            last_intents = []
            continue
        if step["op"] == "intents":
            before = tree(tmp_path)
            got = mod.intents(double)
            check(label + " read-only tree", [] if tree(tmp_path) == before else ["intents() changed files"])
            side = [c for c in double.calls if c["fn"] not in ("table",) and not (c["fn"] == "ky" and c["args"][:1] == ["inbox"])]
            check(label + " read-only calls", [] if not side else ["intents() made side-effect calls: %r" % side])
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
            actual = [c for c in double.calls if c["fn"] != "table"]
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
                     "sg_one_job_across_ticks_and_restarts"):
        assert required in names, required


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
