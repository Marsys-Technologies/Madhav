"""KV3-B-OPS-CONTRACT (relaunch plan v2.7 §6 REQUEST-PREP … POST-READBACK, §8, §14): the shared operation-adapter helper.

What runs here, and what does not:
  · the REAL chain: `kyd_kinds_ops` (its candidates, `start`, `finish`, `static_validate`, `required_checks`) and
    `executor.py` (`validate`, `run_one`, `execute`, `receipt`, `lease_live`, `fence_quiescent`) are imported from this
    working copy and called as functions — never a `main`, never the running executor;
  · FAKES only at the edges: the git handle (`FakeGit`: fetch / show / merge-base / worktree, no repository is written),
    the lease table it shows, the capabilities, the child process (`run_group` → the fixture wrapper, in process), the
    engine's ctx and the remote (`FakeRemote`: one job definition, a count of what was submitted, a settable state);
  · the table on disk is never edited: a case that needs an enabled production kind enables a COPY that only the fake
    git handle shows. The protected sources and the table are hashed before and after the whole module.

Fakes qualify the mechanics. A real database or remote postcondition is each item's to prove; nothing here claims one."""
import argparse
import copy
import datetime as dt
import hashlib
import importlib.util
import json
import os
import re
import shutil
import sqlite3
import subprocess
import uuid
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
FLEET = HERE.parent
REPO = FLEET.parents[3]
ADAPTERS_PY = FLEET / "operation_adapters.py"
EXECUTOR_PY = FLEET / "executor.py"
KINDS_PY = FLEET / "kyd_kinds_ops.py"
OPS_FILE = FLEET / "executor_ops.json"
DISPATCH_PY = REPO / "platform" / "scripts" / "dispatch_v5_small_test_job.py"
PREFLIGHT_TS = REPO / "platform" / "scripts" / "data-plane-secret-isolation-preflight.ts"
OPS_REL = "00_ARCHITECTURE/briefs/kalayantra/fleet/executor_ops.json"
COORD_REL = "00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md"
SOURCE_PIN = "102e4fdf549909eb71d620dc95930c208ffc9f9f"
PINS = {  # the packet's spec_sources, measured at SOURCE_PIN
    "00_ARCHITECTURE/briefs/kalayantra/fleet/executor.py": "37929a82aef5f15fa3d143c39d8d75f8162071291ae86460b843411a4d0f73db",
    OPS_REL: "eb9877fe3c7c5a933a2b6863282d9b28a6f996c4de6e68c1eca8a18b0e347477",
    "00_ARCHITECTURE/briefs/kalayantra/fleet/kyd_kinds_ops.py": "712d47f9e57c63245c0892b1da2181112adb60ec99c22e34f723030fdcca40ed",
    "platform/scripts/dispatch_v5_small_test_job.py": "9419471ff84f40e4a80f5134116f2b09fe4caad1d97992734beea22ebae16081",
    "platform/scripts/data-plane-secret-isolation-preflight.ts": "8d07175c3a8bd2d46b6f53ff59a763615efde07d0d6d7d8fe37b2ce51a681822",
}
PROTECTED = [EXECUTOR_PY, OPS_FILE, KINDS_PY, DISPATCH_PY, PREFLIGHT_TS]
ENABLED_KINDS = {"readback_sql", "migration_readback", "local_schema_seed", "finalize"}
CANONICAL_CHART = "482012f1-710e-4a25-994a-93821f5871aa"
ITEM = "K9-FIXTURE"
LEASE = "LEASE-KY-FIXTURE"
MERGED = "a" * 40
OTHER_MERGED = "b" * 40
UNMERGED = "c" * 40
WRAPPER_REL = "ops/fixture_adapter.py"
RUN_ID = "0d1f8a52-6f0e-4c7e-9a3b-5a2a2f6f9c11"
# Stand-ins shaped like credentials, joined at run time so that no literal in this file is one; nothing connects to DSN.
DSN = "".join(("postgres", "ql://fixture_user", ":", "fixture_pw", "@127.0.0.1:1/ky_fixture"))
CREDENTIAL_SHAPES = [DSN, "".join(("postgres", "://u", ":", "p", "@h/db")), "=".join(("PGPASSWORD", "hunter2")),
                     ": ".join(("token", "abc123")), "=".join(("api_key", "abc")), "=".join(("SECRET", "abc"))]
PROJECT = "madhav-astrology"
BUILDER_SA = "data-plane-builder-runtime@%s.iam.gserviceaccount.com" % PROJECT
VERIFIER_SA = "gochara-verifier-runtime@%s.iam.gserviceaccount.com" % PROJECT
ALL_CAPS = {"builder": True, "owner": True, "pgenv": True, "gcloud": True, "none": True}


def sha_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


A = _load(ADAPTERS_PY, "ky_operation_adapters_under_test")
K = _load(KINDS_PY, "ky_kinds_ops_for_adapters")


@pytest.fixture(scope="module", autouse=True)
def protected_sources_unchanged():
    """The sources this item must not touch, and the table, carry the same bytes after the module as before it."""
    before = {str(p): sha_file(p) for p in PROTECTED}
    yield
    assert {str(p): sha_file(p) for p in PROTECTED} == before, "a protected source or the table changed during the tests"


# ───────────────────────────── the fakes ─────────────────────────────

def real_table():
    return json.loads(OPS_FILE.read_text())["ops"]


def fixture_table():
    """A COPY of the table in which the two orchestrator-rebuild kinds stand for an eventual reviewed mapping: enabled,
    the fixture wrapper as script, the mode in fixed_args (I3). Every other entry is the table's, byte for byte."""
    table = real_table()
    for kind, mode in (("orchestrator_rebuild_dryrun", "--dry-run"), ("orchestrator_rebuild", "--execute")):
        table[kind] = dict(table[kind], enabled=True, script=WRAPPER_REL, fixed_args=[mode], required_rows=["2", "3"])
    return table


def lease_text(rows):
    ist = dt.timezone(dt.timedelta(hours=5, minutes=30))
    lines = ["# coordination", "## 1. Leases", "| id | campaign | scope | from | expiry | status |", "|---|---|---|---|---|---|"]
    for lease_id, hours, status in rows:
        expiry = (dt.datetime.now(ist) + dt.timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M")
        lines.append("| %s | kalayantra | build | now | %s IST | %s |" % (lease_id, expiry, status))
    return "\n".join(lines + ["## 2. History", ""])


class FakeGit:
    """executor.git: answers from memory. `worktree add` lays the reviewed scripts under the path; nothing is a repository."""

    def __init__(self, table):
        self.table = table
        self.leases = [(LEASE, 24, "ACTIVE")]
        self.merged = {MERGED, OTHER_MERGED}
        self.scripts = {WRAPPER_REL: "# the fixture wrapper; the fake process runs it in process\n"}
        self.calls = []

    def __call__(self, *args, timeout=120):
        self.calls.append(list(args))
        done = lambda rc, out="": subprocess.CompletedProcess(list(args), rc, out, "" if rc == 0 else "fatal")
        if args[0] == "fetch":
            return done(0)
        if args[0] == "rev-parse":
            return done(0, MERGED + "\n")
        if args[0] == "show":
            ref, _, path = args[1].partition(":")
            if ref == "origin/main" and path == OPS_REL:
                return done(0, json.dumps({"ops": self.table}))
            if ref == "origin/campaign-coordination" and path == COORD_REL:
                return done(0, lease_text(self.leases))
            if ref == "origin/main" and path in self.scripts:
                return done(0, self.scripts[path])
            return done(128)
        if args[0] == "merge-base":
            return done(0 if args[2] in self.merged else 1)
        if args[:3] == ("worktree", "add", "--detach"):
            if args[4] not in self.merged:
                return done(128)
            for rel, body in self.scripts.items():
                target = Path(args[3]) / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(body)
            return done(0)
        if args[:3] == ("worktree", "remove", "--force"):
            shutil.rmtree(args[3], ignore_errors=True)
            return done(0)
        return done(129)


class FakeRemote:
    """The remote as an adapter's transport sees it: one job definition (non-secret metadata), what was submitted, and
    a state a test sets. `execute` returning 0 says the submission was taken — never that the run ended."""

    def __init__(self, service_account=BUILDER_SA, secret_ref="data-plane-builder-db-url", name=None):
        self.definition = {"metadata": {"name": name or A.BUILD_JOB}, "spec": {"template": {"spec": {"template": {"spec": {
            "serviceAccountName": service_account,
            "containers": [{"env": [{"name": "DATABASE_URL", "valueFrom": {"secretKeyRef": {"name": secret_ref, "key": "latest"}}}]}]}}}}}}
        self.submissions = []
        self.described = []
        self.state = {}                                    # run id → what the remote would answer

    def describe(self, job):
        self.described.append(job)
        return copy.deepcopy(self.definition)

    def execute(self, argv, env):
        self.submissions.append({"argv": list(argv), "env": dict(env)})
        self.state[argv[-1].rsplit(",", 1)[-1]] = "RUNNING"
        return 0, "execution started\n"

    def fingerprint(self):
        return hashlib.sha256(json.dumps([self.submissions, self.state], sort_keys=True).encode()).hexdigest()


def fixture_wrapper(argv, env, remote):
    """What an item's wrapper does with the helper: explicit mode, order-free arguments, one planned remote launch."""
    parser = argparse.ArgumentParser(prog="fixture_adapter.py")
    A.add_mode_arguments(parser)
    try:
        args = A.parse_request_args(argv, ("assets", "run-id"), parser)
        mode = A.resolve_mode(args.dry_run, args.execute)
        return 0, A.emit(A.remote_launch(mode, args.run_id, remote, environ=env))
    except A.Refusal as refusal:
        return 2, "REFUSAL %s: %s" % (refusal.code, refusal)


class Bench:
    """One temporary KY_ROOT with the real executor module bound to it, the real dispatcher module on a ctx double,
    and the fakes between them."""

    def __init__(self, tmp_path, monkeypatch, table=None):
        self.root = tmp_path / "ky"
        monkeypatch.setenv("KY_ROOT", str(self.root))
        monkeypatch.setenv("KY_SOURCE_REPO", str(tmp_path / "no-repository"))
        monkeypatch.setenv("KY_BUILDER_DATABASE_URL", DSN)
        monkeypatch.setenv("KY_OWNER_DATABASE_URL", DSN)
        self.X = X = _load(EXECUTOR_PY, "ky_executor_for_adapters_%s" % uuid.uuid4().hex)
        for d in (X.REQ, X.REC, X.DONE, X.ACC, X.INFLIGHT, X.TMP, X.EXEC, X.KY_ROOT / "logs"):
            d.mkdir(parents=True, exist_ok=True)
        self.git = FakeGit(fixture_table() if table is None else table)
        self.remote = FakeRemote()
        self.launched = []
        self.wrapper = fixture_wrapper
        X.git = self.git
        X.capabilities = lambda table_on_main: dict(ALL_CAPS)
        X.run_group = self.process
        self.run = X.RUN
        self.fleet = tmp_path / "fleet"
        self.repo = tmp_path / "repo"
        self.scratch = tmp_path / "scratch"
        self.model = str(self.repo / "plan_model.json")
        for d in (self.fleet, self.repo, self.scratch):
            d.mkdir(parents=True, exist_ok=True)
        self.next = {"stream": "", "version": 1, "running": [], "ready": [], "blocked": []}
        self.event_log = {}
        self.journalled = []
        self.raised = []
        self.shells = []
        self.jobs = 0

    # -- the fake child process (executor.run_group)
    def process(self, argv, cwd, env, timeout):
        self.launched.append({"argv": list(argv), "cwd": str(cwd), "env": dict(env)})
        assert Path(argv[1]).exists(), "the executor launched a script that is not in its operation worktree"
        rc, out = self.wrapper(argv[2:], env, self.remote)
        return subprocess.CompletedProcess(argv, rc, out, "")

    # -- the engine's ctx (kyd_kinds_ops)
    def sh(self, argv, env=None, cwd=None, timeout=120):
        argv = list(argv)
        self.shells.append(argv)
        if argv[:2] == ["git", "-C"] and argv[3:] == ["show", "origin/main:" + OPS_REL]:
            return 0, json.dumps({"ops": self.git.table}), ""
        if argv[:1] == ["bash"] and argv[1].endswith("kyboundary.sh") and argv[2] == "check":
            return 0, "", ""
        if argv[2:4] == [str(self.fleet / "kyverdicts.py"), "snapshot"]:
            return 0, "", ""
        if argv[2:4] == [str(self.fleet / "kyverdicts.py"), "publish"]:      # the publisher's effect: one verdict event
            opt = dict(zip(argv[4::2], argv[5::2]))
            verdict = json.loads(Path(opt["--result"]).read_text())["proposed_verdict"]["verdict"]
            self.event_log.setdefault(opt["--item"], []).append(
                {"kind": "verdict", "item": opt["--item"], "phase": opt["--phase"], "artifact_digest": opt["--artifact-digest"],
                 "result": verdict, "actor": "stream-V:" + opt["--vslot"]})
            return 0, json.dumps({"published": True, "result": verdict, "action_id": "VERDICT-fixture"}), ""
        return 127, "", "unanswered in the test double"

    def act(self, action_id, kind, inputs, target, effect, observer):
        verdict, observed = observer({"action_id": action_id})
        if verdict == "unknown":
            return "unknown", {}
        return "done", (observed if verdict == "done" else effect())

    def events(self, item):
        return list(self.event_log.get(item, []))

    def pr(self, item):
        return None

    def journal(self, event, text):
        self.journalled.append((event, text))

    def awaiting(self, slug, question, options, evidence, item, class_hint):
        self.raised.append(slug)

    def now(self):
        return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # -- driving the real chain
    def plan(self, steps, item=ITEM):
        Path(self.model).write_text(json.dumps({"items": [{"id": item, "completion_kind": "operation", "brief": {"op": steps}}]}))
        self.next["ready"] = [{"id": item, "owner": "N", "status": "ready"}]

    def owed(self, kind):
        unknown = []
        return [intent for intent, _ in K.CANDIDATES[kind](self, unknown)], unknown

    def job(self, intent, **more):
        self.jobs += 1
        scratch = self.scratch / ("J-%d" % self.jobs)
        scratch.mkdir(parents=True, exist_ok=True)
        return dict(intent, job_id="J-%d" % self.jobs, controller_id="c1", job_scratch=str(scratch),
                    result_path=str(scratch / "result.json"), worktree=str(self.repo), **more)

    def prepare(self):
        intents, unknown = self.owed("REQUEST-PREP")
        assert len(intents) == 1 and intents[0]["runner"] == "script", (intents, unknown)
        assert K.start(self, self.job(intents[0]))["outcome"] == "done"
        docs = [doc for _, doc in K.all_prepared(self.run) if doc["request_sha256"] == intents[0]["digest"]]
        assert len(docs) == 1
        return docs[0]

    def accept(self, prepared, slot="v1", checks=None, rows=None, **changes):
        intents, _ = self.owed("PRE-ACCEPT")
        intent = next(i for i in intents if i["digest"] == prepared["request_sha256"])
        job = self.job(intent, slot=slot, exit_code=0)
        assert K.start(self, job) is None
        req = prepared["request"]
        proposed = {"result": "ACCEPTED", "operation_id": req["operation_id"], "request_sha256": prepared["request_sha256"],
                    "by": slot, "reviewed_commit": req.get("reviewed_commit"),
                    "checks": {"backup_taken": True, "restore_verified": True, "dry_run_passed": True} if checks is None else checks,
                    "rows": {"2": True, "3": True} if rows is None else rows}
        proposed.update(changes)
        (Path(job["job_scratch"]) / "acceptance.json").write_text(json.dumps(proposed))
        return K.finish(self, job)

    def submit(self, prepared):
        intents, unknown = self.owed("EXECUTE")
        intent = next((i for i in intents if i["digest"] == prepared["request_sha256"]), None)
        assert intent is not None, unknown
        assert K.start(self, self.job(intent))["outcome"] == "done"
        path = self.X.REQ / (prepared["request"]["operation_id"] + ".json")
        return path, json.loads(path.read_text())

    def execute(self, path, req):
        """The executor's own steps for one request (its `main` loop, function by function): validate, fence, mark,
        move in flight, RUNNING receipt, run_one."""
        X = self.X
        table = X.load_table()
        why = X.validate(req, table, dict(ALL_CAPS))
        if why:
            return why
        X.FENCE.write_text(json.dumps({"operation_id": req["operation_id"], "request_sha256": X.request_digest(req), "ts": X.now()}))
        X.mark_seen(req["idempotency_key"], req["operation_id"])
        flight = X.INFLIGHT / path.name
        shutil.move(str(path), flight)
        X.receipt(req, "RUNNING", "accepted; in flight")
        X.run_one(flight, req, table[req["kind"]])
        return None

    def receipt(self, opid):
        path = self.X.REC / (opid + ".json")
        return path, json.loads(path.read_text())

    def verdict(self, prepared, slot="v2", verdict="ACCEPTED", **changes):
        intents, unknown = self.owed("POST-READBACK")
        intent = next((i for i in intents if i["item"] == prepared["item"] and i["verdict_phase"] == "artifact"), None)
        assert intent is not None, unknown
        job = self.job(intent, slot=slot, exit_code=0)
        assert K.start(self, job) is None
        Path(job["result_path"]).write_text(json.dumps({"schema": "ky.job_result/1", "status": "done",
                                                        "proposed_verdict": {"verdict": verdict}}))
        job.update(changes)
        return K.finish(self, job), intent

    def observation(self, prepared, **fields):
        """The item's own terminal observation of the remote, bound to the request and to the ACTUAL receipt."""
        opid = prepared["request"]["operation_id"]
        doc = {"schema": A.OBSERVATION_SCHEMA, "operation_id": opid, "request_sha256": prepared["request_sha256"],
               "receipt_sha256": sha_file(self.X.REC / (opid + ".json")), "terminal": True, "outcome": "succeeded",
               "source": "fake remote"}
        doc.update(fields)
        return doc


def step(kind, opid, **more):
    expires = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=2)).isoformat(timespec="seconds")
    base = {"kind": kind, "operation_id": opid, "kyd": "kyd-fixture", "args": {"assets": "ka_fixture", "run-id": RUN_ID},
            "lease_id": LEASE, "reviewed_commit": MERGED, "expires_at": expires}
    base.update(more)
    return base


DRY = lambda **more: step("orchestrator_rebuild_dryrun", "OP-FIX-s1", **more)
RUN = lambda **more: step("orchestrator_rebuild", "OP-FIX-s2", **more)


@pytest.fixture
def bench(tmp_path, monkeypatch):
    return Bench(tmp_path, monkeypatch)


def accepted_request(bench, steps=None, **accept):
    """Prepared, accepted and submitted through the real dispatcher: (prepared, request path, request)."""
    bench.plan(steps or [RUN()])
    prepared = bench.prepare()
    assert bench.accept(prepared, **accept)["outcome"] == "done"
    return (prepared,) + bench.submit(prepared)


# ───────────────────────────── pins, table and the copied constants ─────────────────────────────

@pytest.mark.parametrize("rel", sorted(PINS))
def test_the_spec_sources_are_the_packets_at_the_source_pin(rel):
    p = subprocess.run(["git", "-C", str(REPO), "show", "%s:%s" % (SOURCE_PIN, rel)], capture_output=True)
    assert p.returncode == 0, "cannot read %s at the source pin: %s" % (rel, p.stderr.decode()[-200:])
    assert hashlib.sha256(p.stdout).hexdigest() == PINS[rel]


def test_the_table_has_twenty_one_entries_the_same_four_enabled_and_disabled_backup_rebuild_mappings():
    # PINS guards historical spec sources at SOURCE_PIN; this digest guards the scoped update.
    assert sha_file(OPS_FILE) == "65d3f27eacdc106378500cf6c3b79ef756f7f3022ce86b904e1200a77802c16f"
    ops = real_table()
    assert len(ops) == 21
    assert all(e["enabled"] is True or e["enabled"] is False for e in ops.values())
    assert ENABLED_KINDS == {"readback_sql", "migration_readback", "local_schema_seed", "finalize"}
    assert {k for k, e in ops.items() if e["enabled"]} == ENABLED_KINDS
    prepared_kinds = {"backup_snapshot", "backup_restore_verify", "orchestrator_rebuild_dryrun",
                      "orchestrator_rebuild", "orchestrator_rebuild_readback"}
    assert all(ops[k]["enabled"] is False for k in prepared_kinds)
    disabled = {k: e for k, e in ops.items() if not e["enabled"]}
    assert len(disabled) == 17
    assert len([k for k, e in disabled.items() if "TO_BE_SET" in e["script"]]) == 10
    assert {k for k, e in disabled.items() if "TO_BE_SET" not in e["script"]} == prepared_kinds | {
        "smalltest_dispatch", "smalltest_dispatch_dryrun"}


def test_the_fixture_table_differs_from_the_table_in_the_two_fixture_entries_only():
    real, fixture = real_table(), fixture_table()
    assert list(real) == list(fixture)
    assert {k for k in real if real[k] != fixture[k]} == {"orchestrator_rebuild_dryrun", "orchestrator_rebuild"}


def test_the_helpers_copied_constants_are_the_sources(bench):
    X = bench.X
    assert A.CHILD_ENV_ALLOW == X.CHILD_ENV_ALLOW
    assert [r.pattern for r in A.SECRET_VALUE] == [r.pattern for r in X.REDACT]
    assert A.CANONICAL_CHART == X.CANONICAL_CHART == K.CANONICAL_CHART == CANONICAL_CHART
    ts = PREFLIGHT_TS.read_text()
    assert "process.env.GOOGLE_CLOUD_PROJECT ?? '%s'" % A.DEFAULT_PROJECT in ts
    names = dict(re.findall(r"export const (\w+) = [`']([^`']+)[`']", ts))
    build_sa, build_secret = A.JOB_BINDINGS[A.BUILD_JOB]
    verifier_sa, verifier_secret = A.JOB_BINDINGS[A.VERIFIER_JOB]
    assert names["BUILDER_SERVICE_ACCOUNT"] == build_sa + "@${project}.iam.gserviceaccount.com"
    assert names["VERIFIER_SERVICE_ACCOUNT"] == verifier_sa + "@${project}.iam.gserviceaccount.com"
    assert (names["BUILDER_SECRET"], names["VERIFIER_SECRET"], names["VERIFIER_JOB"]) == (build_secret, verifier_secret, A.VERIFIER_JOB)
    assert "surface.kind === 'job' && surface.name === '%s'" % A.BUILD_JOB in ts
    assert set(A.JOB_BINDINGS) == {A.BUILD_JOB, A.VERIFIER_JOB}
    launch = " ".join(A.remote_execute_argv(A.BUILD_JOB, RUN_ID)).replace(RUN_ID, "<run_id>")
    assert "\n  %s\n" % launch in DISPATCH_PY.read_text()


# ───────────────────────────── the positive chain ─────────────────────────────

def test_prepare_accept_submit_receipt_terminal_readback_and_verdict_in_step_order(bench):
    bench.plan([DRY(), RUN()])
    dry = bench.prepare()
    assert (dry["schema"], dry["step"], dry["item"], dry["operation_id"]) == ("ky.op_prepared/1", 1, ITEM, "OP-FIX-s1")
    assert set(dry) == {"schema", "operation_id", "item", "step", "request", "request_sha256", "prepared_by", "prepared_by_slot"}
    assert dry["request_sha256"] == bench.X.request_digest(dry["request"]) == K.request_digest(dry["request"])
    assert bench.owed("REQUEST-PREP")[0] == [], "step 2 is owed before step 1 has an accepted receipt digest"
    bench.event_log[ITEM] = [None]                         # with no receipt there is no digest to ask a verdict of:
    assert bench.owed("REQUEST-PREP") == ([], []), "step 2 waits on the receipt, and the events were read without one"
    del bench.event_log[ITEM]

    # a dry-run kind needs no dry_run_passed and no rows (executor.validate and required_checks agree)
    assert K.required_checks("orchestrator_rebuild_dryrun") == (["backup_taken", "restore_verified"], False)
    assert bench.accept(dry, checks={"backup_taken": True, "restore_verified": True}, rows={})["outcome"] == "done"
    acceptance = json.loads((bench.X.ACC / "OP-FIX-s1.json").read_text())
    assert set(acceptance) == {"result", "operation_id", "by", "reviewed_commit", "ts", "request_sha256", "rows", "checks"}
    path, req = bench.submit(dry)
    assert {k: v for k, v in req.items() if k != "acceptance_receipt"} == dry["request"]
    assert req["acceptance_receipt"] == str(bench.X.ACC / "OP-FIX-s1.json")
    assert bench.execute(path, req) is None
    rpath, receipt = bench.receipt("OP-FIX-s1")
    assert (receipt["status"], receipt["exit_code"], receipt["request_sha256"]) == ("COMPLETED", 0, dry["request_sha256"])
    dry_record = json.loads(Path(receipt["output_file"]).read_text())
    assert (dry_record["mode"], dry_record["submitted"], dry_record["remote_terminal"]) == ("dry_run", False, None)
    assert bench.remote.submissions == [] and bench.remote.described == [A.BUILD_JOB]
    assert A.dry_run_refusal(dry_record, submissions=len(bench.remote.submissions),
                             before=FakeRemote().fingerprint(), after=bench.remote.fingerprint()) is None

    assert bench.owed("REQUEST-PREP")[0] == [], "step 2 is owed before the receipt's digest has a verdict"
    assert A.completion(bench.run, dry, bench.events(ITEM), bench.observation(dry))[0] == "incomplete"
    result, intent = bench.verdict(dry)
    assert result["outcome"] == "done" and intent["digest"] == sha_file(rpath)
    assert A.completion(bench.run, dry, bench.events(ITEM), bench.observation(dry)) == ("complete", None)

    run = bench.prepare()                                  # only now is step 2 prepared
    assert (run["step"], run["operation_id"]) == (2, "OP-FIX-s2")
    assert bench.accept(run, checks={"backup_taken": True, "restore_verified": True}, rows={"2": True, "3": True})["outcome"] == "failed"
    assert bench.accept(run)["outcome"] == "done"
    path, req = bench.submit(run)
    assert bench.execute(path, req) is None
    rpath, receipt = bench.receipt("OP-FIX-s2")
    assert receipt["status"] == "COMPLETED"
    record = json.loads(Path(receipt["output_file"]).read_text())
    assert (record["mode"], record["submitted"], record["submit_exit"], record["remote_terminal"]) == ("execute", True, 0, None)

    # the dry run planned exactly what the execution submitted, with the same principal and run
    for key in ("planned_argv", "job", "project", "principal", "secrets", "run_id", "env_names"):
        assert record[key] == dry_record[key], key
    assert [s["argv"] for s in bench.remote.submissions] == [record["planned_argv"]]
    assert record["planned_argv"] == ["gcloud", "run", "jobs", "execute", "brahma-build-pipeline-job", "--args=--run-id," + RUN_ID]
    assert record["principal"] == BUILDER_SA and record["secrets"] == ["data-plane-builder-db-url"]

    # the launcher's argv is the table's fixed_args then the request's --key value, as the helper states it
    for launched, prepared, entry in zip(bench.launched, (dry, run), ("orchestrator_rebuild_dryrun", "orchestrator_rebuild")):
        wt = bench.X.EXEC / ("op-" + prepared["request"]["operation_id"])
        assert launched["argv"] == A.launch_argv(bench.git.table[entry], prepared["request"], py=bench.X.PY, script_path=str(wt / WRAPPER_REL))
        assert launched["argv"][2:] == [bench.git.table[entry]["fixed_args"][0], "--assets", "ka_fixture", "--run-id", RUN_ID]
        assert launched["env"]["DATABASE_URL"] == DSN and set(launched["env"]) <= A.CHILD_ENV_ALLOW | {"DATABASE_URL", "SE_EPHE_PATH", "KY_ROOT"}
        assert not wt.exists(), "the operation worktree was left behind"
    # the builder connection the child was given reaches neither gcloud nor any record
    assert all("DATABASE_URL" not in s["env"] and set(s["env"]) <= A.CHILD_ENV_ALLOW for s in bench.remote.submissions)
    for written in list(bench.X.REC.iterdir()) + list(bench.X.DONE.iterdir()) + list(bench.X.ACC.iterdir()):
        assert "fixture_pw" not in written.read_text(), written

    # submitted and receipted with exit 0, the remote still running: not complete; then terminal, then the verdict
    assert bench.remote.state[RUN_ID] == "RUNNING"
    assert A.completion(bench.run, run, bench.events(ITEM), None)[0] == "unknown"
    running = bench.observation(run, terminal=False, outcome=None)
    assert A.completion(bench.run, run, bench.events(ITEM), running)[0] == "incomplete"
    bench.remote.state[RUN_ID] = "SUCCEEDED"
    observed = bench.observation(run)
    assert A.completion(bench.run, run, bench.events(ITEM), observed)[0] == "incomplete"      # no independent verdict yet
    result, intent = bench.verdict(run)
    assert result["outcome"] == "done" and intent["digest"] == sha_file(rpath)
    assert A.completion(bench.run, run, bench.events(ITEM), observed) == ("complete", None)

    # the adapter never releases the production fence; quiescence is the verifier's request-bound record
    fence = json.loads(bench.X.FENCE.read_text())
    assert (fence["operation_id"], fence["request_sha256"]) == ("OP-FIX-s2", run["request_sha256"])
    assert bench.X.fence_quiescent() is False
    proof = {"result": "ACCEPTED", "operation_id": "OP-FIX-s2", "request_sha256": dry["request_sha256"], "by": "v2", "ts": bench.X.now()}
    (bench.X.ACC / "OP-FIX-s2.quiescence.json").write_text(json.dumps(proof))
    assert bench.X.fence_quiescent() is False, "a quiescence record of another request freed the fence"
    (bench.X.ACC / "OP-FIX-s2.quiescence.json").write_text(json.dumps(dict(proof, request_sha256=run["request_sha256"])))
    assert bench.X.fence_quiescent() is True and bench.X.FENCE.exists()


def test_a_read_only_kind_launches_as_the_helper_states_it(bench):
    table = real_table()
    bench.git.table = table
    bench.git.scripts["00_ARCHITECTURE/briefs/kalayantra/fleet/readback_sql.sh"] = "#!/bin/bash\n"
    bench.wrapper = lambda argv, env, remote: (0, "rows\n")
    req = {"operation_id": "OP-READ", "kind": "migration_readback", "item_id": ITEM, "idempotency_key": "OP-READ",
           "requested_by": "v1", "kyd": "kyd-fixture", "args": {"migration": "0412"}}
    assert bench.X.validate(req, table, dict(ALL_CAPS)) is None and K.static_validate(req, table["migration_readback"]) is None
    assert bench.X.execute(req, table["migration_readback"])[0] == 0
    launched = bench.launched[0]
    assert launched["argv"] == A.launch_argv(table["migration_readback"], req, py=bench.X.PY,
                                             script_path=str(bench.X.TMP / "OP-READ.readback_sql.sh"))
    assert launched["argv"][0] == "bash" and "DATABASE_URL" not in launched["env"]


@pytest.mark.parametrize("entry,expected", [
    ({"script": "a/b.py", "fixed_args": ["seed"], "production": True}, ["PY", "/wt/a/b.py", "seed", "--k", "v"]),
    ({"script": "a/b.sh", "production": True}, ["bash", "/wt/a/b.sh", "--k", "v"]),
    ({"script": "a/b.py", "python_module": "pkg.mod", "production": True}, ["PY", "-m", "pkg.mod", "--k", "v"]),
    ({"script": "a/b.py", "python_module": "pkg.mod", "production": False}, ["PY", "/wt/a/b.py", "--k", "v"]),
])
def test_launch_argv_forms(entry, expected):
    assert A.launch_argv(entry, {"args": {"k": "v"}}, py="PY", script_path="/wt/" + entry["script"]) == expected


# ───────────────────────────── negative 1: entry, requester, arguments ─────────────────────────────

def test_a_disabled_or_placeholder_entry_an_unauthorised_requester_or_disallowed_args_refuses(bench):
    X, fixture = bench.X, fixture_table()
    real = real_table()
    base = RUN()
    req = dict({k: base[k] for k in ("kind", "operation_id", "kyd", "args", "lease_id", "reviewed_commit", "expires_at")},
               item_id=ITEM, idempotency_key="OP-FIX-s2", requested_by="adhikarin", chart_id=CANONICAL_CHART)
    both = lambda r, table: (X.validate(r, table, dict(ALL_CAPS)), K.static_validate(r, table.get(r["kind"])))

    # the table as it stands: every production kind is disabled, whichever one a request names
    for kind, entry in real.items():
        if entry["production"]:
            executor, static = both(dict(req, kind=kind, args={}), real)
            assert executor.startswith("kind %s is not enabled" % kind) and static == "kind %s is not enabled" % kind
    for kind in ("smalltest_dispatch", "smalltest_dispatch_dryrun"):       # a script is named, and it is still disabled
        assert "TO_BE_SET" not in real[kind]["script"] and both(dict(req, kind=kind, args={}), real)[0].startswith("kind")
    # enabled by mistake while its script is a placeholder
    placeholder = dict(real, publish_head=dict(real["publish_head"], enabled=True))
    assert both(dict(req, kind="publish_head", args={}), placeholder) == ("operation script not yet reviewed/landed",) * 2
    assert both(dict(req, kind="no_such_kind"), fixture)[0] == "unknown kind no_such_kind"

    assert both(dict(req, requested_by="b1"), fixture) == ("requested_by b1 may not request orchestrator_rebuild",) * 2
    assert both(dict(req, requested_by="v1"), fixture) == ("requested_by v1 may not request orchestrator_rebuild",) * 2
    assert both(dict(req, args={"assets": "ka_fixture", "sql": "x"}), fixture) == ("disallowed args ['sql']",) * 2
    assert both(dict(req, args={"assets": "ka_fixture; rm -rf x"}), fixture) == ("an argument value has unsafe characters",) * 2
    assert both(dict(req, chart_id="362f9f17-0000-0000-0000-000000000000"), fixture) == ("chart_id is not the canonical chart",) * 2
    assert K.static_validate(req, fixture["orchestrator_rebuild"]) is None       # the request itself is well formed

    # the dispatcher prepares nothing for a listed-but-disabled kind, and says nothing is unknown about it
    bench.git.table = real
    bench.plan([RUN()])
    assert bench.owed("REQUEST-PREP") == ([], [])
    assert not (bench.run / "ops" / "prepared").exists()


# ───────────────────────────── negative 2: request, head, expiry, checks ─────────────────────────────

def test_a_changed_request_or_head_an_expired_acceptance_or_an_omitted_check_refuses(bench):
    X = bench.X
    prepared, path, req = accepted_request(bench)
    validate = lambda r: X.validate(r, X.load_table(), dict(ALL_CAPS))
    assert validate(req) is None
    acc_path = X.ACC / "OP-FIX-s2.json"
    accepted = json.loads(acc_path.read_text())

    binds = "approval does not bind the complete request"
    assert validate(dict(req, args=dict(req["args"], assets="ka_other"))) == binds
    assert validate(dict(req, args={"assets": "ka_fixture"})) == binds
    assert validate(dict(req, timeout_s=10)) == binds
    assert validate(dict(req, item_id="K9-OTHER")) == binds
    assert validate(dict(req, kyd="another")) == binds
    assert validate(dict(req, reviewed_commit=OTHER_MERGED)) == "the acceptance receipt names a different reviewed_commit"
    assert validate(dict(req, reviewed_commit=UNMERGED)) == "reviewed_commit is not merged to main"
    assert validate(dict(req, operation_id="OP-FIX-s9")).startswith("pre-acceptance receipt is not an ACCEPTED receipt")
    outside = bench.scratch / "OP-FIX-s2.json"
    outside.write_text(acc_path.read_text())
    assert validate(dict(req, acceptance_receipt=str(outside))).startswith("pre-acceptance receipt missing")
    assert validate({k: v for k, v in req.items() if k != "acceptance_receipt"}).startswith("pre-acceptance receipt missing")

    def with_acceptance(**changes):
        acc_path.write_text(json.dumps(dict(accepted, **changes)))
        try:
            return validate(req)
        finally:
            acc_path.write_text(json.dumps(accepted))

    ago = lambda **delta: (dt.datetime.now(dt.timezone.utc) - dt.timedelta(**delta)).isoformat(timespec="seconds")
    expired = "approval expired or not yet valid"
    assert with_acceptance(ts=ago(hours=3, seconds=30)) == expired                       # older than the three-hour limit
    assert with_acceptance(ts=ago(hours=-1)) == expired                                 # issued in the future
    assert with_acceptance(ts="2026-10-13T08:00:00").startswith("valid approval timestamp")       # no timezone
    assert validate(dict(req, expires_at=ago(seconds=5))) in (expired, binds)           # the request's own expiry is bound too
    assert with_acceptance(by="b1").startswith("pre-acceptance receipt is not an ACCEPTED receipt")
    assert with_acceptance(result="REJECTED").startswith("pre-acceptance receipt is not an ACCEPTED receipt")
    for check in ("backup_taken", "restore_verified", "dry_run_passed"):
        partial = {k: v for k, v in accepted["checks"].items() if k != check}
        assert with_acceptance(checks=partial) == "required backup/restore/dry-run attestation missing", check
        assert with_acceptance(checks=dict(accepted["checks"], **{check: "true"})) == "required backup/restore/dry-run attestation missing"
    assert with_acceptance(rows={"2": True}) == "required pre-acceptance rows are not all true"
    assert with_acceptance(rows={"2": True, "3": False}) == "required pre-acceptance rows are not all true"

    lease = "lease is not the single unexpired ACTIVE row on origin/campaign-coordination"
    bench.git.leases = [(LEASE, 24, "ACTIVE"), ("LEASE-OTHER", 24, "ACTIVE")]
    assert validate(req) == lease
    bench.git.leases = [(LEASE, -1, "ACTIVE")]
    assert validate(req) == lease
    bench.git.leases = [("LEASE-OTHER", 24, "ACTIVE")]
    assert validate(req) == lease
    bench.git.leases = [(LEASE, 24, "ACTIVE"), ("LEASE-OLD", 24, "RELEASED")]
    assert validate(req) is None

    # once executed, the same request is refused by its idempotency key
    assert bench.execute(path, req) is None
    assert bench.receipt("OP-FIX-s2")[1]["status"] == "COMPLETED"
    assert validate(req) == "idempotency key already used"


def test_run_one_refuses_when_the_definition_or_the_approval_changed_after_queueing(bench):
    prepared, path, req = accepted_request(bench)
    X = bench.X
    op = X.load_table()[req["kind"]]
    bench.git.table = dict(bench.git.table, orchestrator_rebuild=dict(op, fixed_args=["--execute", "--force"]))
    X.run_one(path, req, op)
    receipt = bench.receipt("OP-FIX-s2")[1]
    assert (receipt["status"], receipt["reason"]) == ("REFUSED", "operation definition changed before execution")
    assert bench.launched == [] and bench.remote.submissions == []
    (X.KY_ROOT / "HOLD").write_text("")
    X.run_one(X.DONE / path.name, req, op)
    assert bench.receipt("OP-FIX-s2")[1]["reason"] == "HOLD set before execution" and bench.launched == []


@pytest.mark.parametrize("accept,code", [
    ({"checks": {"backup_taken": True, "restore_verified": True}}, "attestation_missing"),
    ({"checks": {"backup_taken": True, "restore_verified": True, "dry_run_passed": 1}}, "attestation_missing"),
    ({"rows": {"2": True}}, "rows_not_true"),
    ({"request_sha256": "0" * 64}, "acceptance_not_bound"),
    ({"reviewed_commit": OTHER_MERGED}, "acceptance_not_bound"),
    ({"by": "v2"}, "acceptance_not_bound"),
    ({"result": "REJECTED"}, "not_accepted"),
    ({"slot": "b1"}, "slot_unknown"),
])
def test_the_dispatcher_writes_no_acceptance_for_an_unbound_or_incomplete_one(bench, accept, code):
    bench.plan([RUN()])
    prepared = bench.prepare()
    result = bench.accept(prepared, **accept)
    assert result["outcome"] == "failed" and result["detail"].startswith(code + ":")
    assert not (bench.X.ACC / "OP-FIX-s2.json").exists()
    assert all(i["digest"] != prepared["request_sha256"] for i in bench.owed("EXECUTE")[0]), "an unaccepted request is submittable"


def test_a_prepared_request_changed_on_disk_is_unknown_and_is_not_submitted(bench):
    bench.plan([RUN()])
    prepared = bench.prepare()
    assert bench.accept(prepared)["outcome"] == "done"
    path = bench.run / "ops" / "prepared" / "OP-FIX-s2.json"
    doc = json.loads(path.read_text())
    doc["request"]["args"]["assets"] = "ka_other"
    path.write_text(json.dumps(doc))
    intents, unknown = bench.owed("EXECUTE")
    assert intents == [] and any("is not a valid ky.op_prepared/1" in u for u in unknown)
    doc["request_sha256"] = K.request_digest(doc["request"])              # re-stamped: a different request than the accepted one
    path.write_text(json.dumps(doc))
    intents, unknown = bench.owed("EXECUTE")
    assert intents == [] and any("is not an ACCEPTED record of the prepared request" in u for u in unknown)


# ───────────────────────────── negative 3: principal, remote target, credentials ─────────────────────────────

@pytest.mark.parametrize("remote,code", [
    (dict(service_account="amjis-web-runtime@%s.iam.gserviceaccount.com" % PROJECT), "principal"),
    (dict(service_account=VERIFIER_SA), "principal"),
    (dict(service_account="data-plane-builder-runtime@another-project.iam.gserviceaccount.com"), "principal"),
    (dict(secret_ref="gochara-verifier-db-url"), "principal"),
    (dict(secret_ref="projects/another-project/secrets/data-plane-builder-db-url"), "principal"),
    (dict(name="some-other-job"), "principal"),
])
def test_a_wrong_runtime_principal_refuses_in_both_modes_and_submits_nothing(remote, code):
    for mode in ("dry_run", "execute"):
        fake = FakeRemote(**remote)
        with pytest.raises(A.Refusal) as refused:
            A.remote_launch(mode, RUN_ID, fake, environ={"PATH": "/usr/bin"})
        assert refused.value.code == code and fake.submissions == []


def test_an_absent_unreadable_or_ambiguous_principal_refuses():
    spec = lambda d: d["spec"]["template"]["spec"]["template"]["spec"]
    good = FakeRemote().definition
    assert A.principal_refusal(A.BUILD_JOB, good) is None
    assert A.principal_refusal(A.BUILD_JOB, good, project="another-project") is not None
    for broken in (None, [], "brahma-build-pipeline-job", {}, {"metadata": {"name": A.BUILD_JOB}}):
        assert A.principal_refusal(A.BUILD_JOB, broken) is not None
    no_account = copy.deepcopy(good); del spec(no_account)["serviceAccountName"]
    no_secret = copy.deepcopy(good); spec(no_secret)["containers"][0]["env"] = []
    two_secrets = copy.deepcopy(good)
    spec(two_secrets)["containers"][0]["env"].append({"name": "X", "valueFrom": {"secretKeyRef": {"name": "amjis-pipeline-db-url", "key": "1"}}})
    two_accounts = copy.deepcopy(good); two_accounts["spec"]["serviceAccount"] = VERIFIER_SA
    aliased = copy.deepcopy(good); aliased["metadata"]["annotations"] = {"run.googleapis.com/secrets": "a:projects/1/secrets/b"}
    literal = copy.deepcopy(good); spec(literal)["containers"][0]["env"].append({"name": "DATABASE_URL", "value": DSN})
    for broken in (no_account, no_secret, two_secrets, two_accounts, aliased, literal):
        assert A.principal_refusal(A.BUILD_JOB, broken) is not None
    assert "fixture_pw" not in A.principal_refusal(A.BUILD_JOB, literal)
    assert "names 2 service accounts" in A.principal_refusal(A.BUILD_JOB, two_accounts)
    assert "names 0 service accounts" in A.principal_refusal(A.BUILD_JOB, no_account)

    # the Gochara verifier's binding is its own job's: it is no other job's, and no whole-layer job has one here
    verifier = FakeRemote(service_account=VERIFIER_SA, secret_ref="gochara-verifier-db-url", name=A.VERIFIER_JOB).definition
    assert A.principal_refusal(A.VERIFIER_JOB, verifier) is None
    assert A.principal_refusal(A.VERIFIER_JOB, good) is not None and A.principal_refusal(A.BUILD_JOB, verifier) is not None
    layer = FakeRemote(service_account=VERIFIER_SA, secret_ref="gochara-verifier-db-url", name="kala-layer-verify-job").definition
    assert "no existing principal binding" in A.principal_refusal("kala-layer-verify-job", layer)


@pytest.mark.parametrize("job", ["gochara-verification-job", "kala-layer-verify-job", "brahma-build-pipeline-job --region=x",
                                 "projects/another/locations/x/jobs/brahma-build-pipeline-job", "", None])
def test_an_arbitrary_remote_target_refuses(job):
    with pytest.raises(A.Refusal) as refused:
        A.remote_execute_argv(job, RUN_ID)
    assert refused.value.code == "remote_target"
    fake = FakeRemote(name=job if isinstance(job, str) and job else None)
    with pytest.raises(A.Refusal):
        A.remote_launch("execute", RUN_ID, fake, job=job, environ={})
    assert fake.submissions == []


@pytest.mark.parametrize("run_id", ["", None, "latest", RUN_ID + ",--chart-id,other", RUN_ID.upper(), "--run-id", RUN_ID + " "])
def test_a_run_id_that_is_not_one_staged_run_refuses(run_id):
    with pytest.raises(A.Refusal) as refused:
        A.remote_execute_argv(A.BUILD_JOB, run_id)
    assert refused.value.code == "run_id"


@pytest.mark.parametrize("value", CREDENTIAL_SHAPES, ids=["dsn", "short_dsn", "pgpassword", "token", "api_key", "secret"])
def test_a_credential_in_argv_or_in_an_agent_job_output_refuses(value):
    assert A.secret_refusal(["gcloud", "run", "jobs", "execute", value]) is not None
    assert A.secret_refusal({"request": {"args": {"label": value}}}) is not None
    assert value not in A.secret_refusal(value)                             # the reason never repeats the value
    with pytest.raises(A.Refusal) as refused:
        A.emit({"schema": A.RECORD_SCHEMA, "notes": [value]})
    assert refused.value.code == "secret_value" and value not in str(refused.value)
    assert A.secret_refusal({"secrets": ["data-plane-builder-db-url"], "principal": BUILDER_SA, "env_names": ["PATH"]}) is None


def test_the_remote_environment_is_the_allow_list_and_never_a_connection():
    environ = {"PATH": "/usr/bin", "HOME": "/h", "CLOUDSDK_CONFIG": "/c", "DATABASE_URL": DSN, "KY_BUILDER_DATABASE_URL": DSN,
               "KY_OWNER_DATABASE_URL": DSN, "SE_EPHE_PATH": "/e", "KY_ROOT": "/k", "AWS_SECRET_ACCESS_KEY": "x"}
    assert A.remote_env(environ) == {"PATH": "/usr/bin", "HOME": "/h", "CLOUDSDK_CONFIG": "/c"}
    fake = FakeRemote()
    record = A.remote_launch("execute", RUN_ID, fake, environ=environ)
    assert fake.submissions[0]["env"] == A.remote_env(environ) and record["env_names"] == ["CLOUDSDK_CONFIG", "HOME", "PATH"]
    assert "fixture_pw" not in A.emit(record)


# ───────────────────────────── negative 4: the mandatory dry run ─────────────────────────────

def test_the_mode_is_explicit_and_defaults_to_a_dry_run():
    parser = argparse.ArgumentParser()
    A.add_mode_arguments(parser)
    parse = lambda argv: A.resolve_mode(**{k: v for k, v in vars(parser.parse_args(argv)).items() if k in ("dry_run", "execute")})
    assert (parse([]), parse(["--dry-run"]), parse(["--execute"])) == ("dry_run", "dry_run", "execute")
    with pytest.raises(A.Refusal) as refused:
        A.resolve_mode(dry_run=True, execute=True)
    assert refused.value.code == "mode"
    for bad in ("true", 1, None):
        with pytest.raises(A.Refusal):
            A.resolve_mode(dry_run=False, execute=bad)
    with pytest.raises(A.Refusal):
        A.remote_launch("EXECUTE", RUN_ID, FakeRemote(), environ={})


def test_request_arguments_are_read_in_any_order_and_nothing_else_is_read():
    """The executor appends --key value in the request's own key order, which the request digest does not bind."""
    def parse(argv):
        parser = argparse.ArgumentParser()
        A.add_mode_arguments(parser)
        return vars(A.parse_request_args(argv, ("assets", "run-id"), parser))

    forward = {"assets": "ka_fixture", "run-id": RUN_ID}
    backward = dict(reversed(list(forward.items())))
    assert K.request_digest({"args": forward}) == K.request_digest({"args": backward})
    entry = {"script": "w.py", "fixed_args": ["--execute"], "production": True}
    one = A.launch_argv(entry, {"args": forward}, py="PY", script_path="/wt/w.py")
    two = A.launch_argv(entry, {"args": backward}, py="PY", script_path="/wt/w.py")
    assert one != two and parse(one[2:]) == parse(two[2:])
    assert parse(one[2:]) == {"dry_run": False, "execute": True, "assets": "ka_fixture", "run_id": RUN_ID}
    for bad in (["--assets", "a", "--assets", "b"], ["--assets", "a", "stray"], ["--assets"], ["--sql", "x"],
                ["--assets=a"], ["--ass", "a"], ["--assets", "-5"], ["--assets", "--execute"], ["--execute", "--execute"], ["--dry-run", "--execute"]):
        with pytest.raises(A.Refusal) as refused:
            parse(bad)
        assert refused.value.code in ("arguments", "mode"), bad


def test_a_dry_run_that_submits_or_leaves_changed_state_fails():
    environ = {"PATH": "/usr/bin"}
    clean = FakeRemote()
    before = clean.fingerprint()
    record = A.remote_launch("dry_run", RUN_ID, clean, environ=environ)
    ok = dict(submissions=len(clean.submissions), before=before, after=clean.fingerprint())
    assert A.dry_run_refusal(record, **ok) is None

    def careless(mode, run_id, remote, environ):            # a wrapper that plans correctly and submits anyway
        planned = A.remote_launch("dry_run", run_id, remote, environ=environ)
        remote.execute(planned["planned_argv"], A.remote_env(environ))
        return planned

    dirty = FakeRemote()
    before = dirty.fingerprint()
    claimed = careless("dry_run", RUN_ID, dirty, environ)
    assert claimed["submitted"] is False                     # the record alone looks clean: the detector reads the remote
    assert "submitted" in A.dry_run_refusal(claimed, submissions=len(dirty.submissions), before=before, after=dirty.fingerprint())
    assert "changed" in A.dry_run_refusal(claimed, submissions=0, before=before, after=dirty.fingerprint())
    assert A.dry_run_refusal(record, **dict(ok, submissions=None)) is not None          # not counted is not zero
    assert A.dry_run_refusal(record, **dict(ok, submissions=False)) is not None
    assert A.dry_run_refusal(record, **dict(ok, before=None, after=None)) is not None   # not measured is not unchanged
    assert A.dry_run_refusal(record, **dict(ok, before="", after="")) is not None
    executed = A.remote_launch("execute", RUN_ID, FakeRemote(), environ=environ)
    assert A.dry_run_refusal(executed, **ok) is not None
    assert A.dry_run_refusal(dict(record, submitted=True), **ok) is not None
    assert A.dry_run_refusal(dict(record, mode="execute"), **ok) is not None
    assert A.dry_run_refusal(dict(record, schema="ky.job_result/1"), **ok) is not None
    assert A.dry_run_refusal(dict(record, planned_argv=[]), **ok) is not None
    assert A.dry_run_refusal(None, **ok) is not None


LANE = {"host": "127.0.0.1", "port": 55433, "database": "ky_b1"}
PROBES = {"rows": "SELECT id, state FROM runs ORDER BY id", "count": "SELECT count(*) FROM runs"}
HEAD = "SELECT generation FROM head"
STATEMENTS = [("INSERT INTO runs (id, state) VALUES (?, ?)", ("r2", "planned")), ("UPDATE head SET generation = ?", (8,))]
IDENTITY = {"script_sha256": "1" * 64, "input_sha256": "2" * 64}


@pytest.fixture
def lane(tmp_path):
    conn = sqlite3.connect(str(tmp_path / "lane.sqlite"))
    conn.execute("CREATE TABLE runs (id TEXT PRIMARY KEY, state TEXT)")
    conn.execute("CREATE TABLE head (generation INTEGER)")
    conn.execute("INSERT INTO runs VALUES ('r1', 'done')")
    conn.execute("INSERT INTO head VALUES (7)")
    conn.commit()
    yield conn
    conn.close()


def lane_state(conn):
    return conn.execute("SELECT id, state FROM runs ORDER BY id").fetchall(), conn.execute(HEAD).fetchall()


def test_a_database_rehearsal_runs_the_statements_rolls_back_and_compares(lane):
    record = A.rehearse(lane, STATEMENTS, PROBES, HEAD, target=LANE, identity=IDENTITY)
    assert lane_state(lane) == ([("r1", "done")], [(7,)])
    assert record["rolled_back"] is True and record["before"] == record["after"] != record["during"]
    assert record["before"]["count"]["rows"] == 1 and record["during"]["rows"]["rows"] == 2
    assert record["before"]["head"]["rows"] == 1 and record["before"]["head"]["sha256"] != record["during"]["head"]["sha256"]
    assert (record["script_sha256"], record["input_sha256"], record["target"]) == ("1" * 64, "2" * 64, LANE)
    assert record["statements_sha256"] == A.rehearse(lane, STATEMENTS, PROBES, HEAD, target=LANE, identity=IDENTITY)["statements_sha256"]
    other = A.rehearse(lane, STATEMENTS[:1], PROBES, HEAD, target=LANE, identity=IDENTITY)
    assert other["statements_sha256"] != record["statements_sha256"]

    # a value changed with the counts unchanged is still a change
    same_count = [("UPDATE runs SET state = ? WHERE id = ?", ("failed", "r1"))]
    assert A.rehearse(lane, same_count, PROBES, HEAD, target=LANE, identity=IDENTITY)["rolled_back"] is True


class Committing:
    """A connection whose rollback keeps the work (what an autocommitting or mis-wired handle does)."""

    def __init__(self, conn):
        self.conn = conn

    def cursor(self):
        return self.conn.cursor()

    def rollback(self):
        self.conn.commit()


class Inert:
    """Fake SQL: every statement 'succeeds' and nothing happens."""

    def __init__(self, conn):
        self.conn = conn

    def cursor(self):
        real = self.conn.cursor()

        class Cursor:
            def execute(self, sql, params=()):
                if sql.lstrip().upper().startswith("SELECT"):
                    real.execute(sql, params)

            def fetchall(self):
                return real.fetchall()

        return Cursor()

    def rollback(self):
        self.conn.rollback()


def test_a_rehearsal_that_proves_no_rollback_refuses(lane):
    def refused(*args, **kwargs):
        with pytest.raises(A.Refusal) as caught:
            A.rehearse(*args, **kwargs)
        return caught.value.code

    assert refused(Committing(lane), STATEMENTS, PROBES, HEAD, target=LANE, identity=IDENTITY) == "rollback_left_changes"
    assert lane_state(lane) == ([("r1", "done"), ("r2", "planned")], [(8,)])            # which is why it refuses
    assert refused(Inert(lane), STATEMENTS, PROBES, HEAD, target=LANE, identity=IDENTITY) == "no_observable_effect"
    noop = [("UPDATE runs SET state = ? WHERE id = ?", ("x", "absent"))]
    assert refused(lane, noop, PROBES, HEAD, target=LANE, identity=IDENTITY) == "no_observable_effect"
    assert refused(lane, [], PROBES, HEAD, target=LANE, identity=IDENTITY) == "rehearsal_scope"
    assert refused(lane, STATEMENTS, {}, HEAD, target=LANE, identity=IDENTITY) == "rehearsal_scope"
    assert refused(lane, STATEMENTS, PROBES, "", target=LANE, identity=IDENTITY) == "rehearsal_scope"
    assert refused(lane, STATEMENTS, dict(PROBES, head=HEAD), HEAD, target=LANE, identity=IDENTITY) == "rehearsal_scope"
    assert refused(lane, STATEMENTS, PROBES, HEAD, target=LANE, identity={"script_sha256": "1" * 64}) == "identity"
    assert refused(lane, STATEMENTS, PROBES, HEAD, target=LANE, identity=dict(IDENTITY, input_sha256="abc")) == "identity"
    for target in ({"host": "10.4.0.3", "port": 5432, "database": "ky_b1"}, {"host": "127.0.0.1", "port": 5432, "database": "amjis"},
                   {"host": "localhost", "port": 55433, "database": "ky_b1"}, {"host": "127.0.0.1", "database": "ky_"}, {}, None, DSN):
        assert refused(lane, STATEMENTS, PROBES, HEAD, target=target, identity=IDENTITY) == "lane_target", target
    broken = [("INSERT INTO runs (id, state) VALUES (?, ?)", ("r3", "planned")), ("INSERT INTO no_such_table VALUES (1)", ())]
    assert refused(lane, broken, PROBES, HEAD, target=LANE, identity=IDENTITY) == "statement_failed"
    assert lane.execute("SELECT count(*) FROM runs").fetchall() == [(2,)], "a failed rehearsal left its statements behind"


def test_a_backup_or_restore_dry_run_claims_preflight_and_scope_and_nothing_about_restore_correctness():
    record = A.scope_record("dry_run", "backup_restore_verify", scope={"label": "pre-k9"}, preflight={"target_reachable": True},
                            identity=IDENTITY)
    assert record["mode"] == "dry_run" and record["restore_verified"] is None and record["submitted"] is False
    assert record["proves"] == ["preflight", "scope"]
    with pytest.raises(A.Refusal):
        A.scope_record("dry_run", "backup_restore_verify", scope={}, preflight={"target_reachable": True}, identity=IDENTITY)
    with pytest.raises(A.Refusal):
        A.scope_record("dry_run", "backup_restore_verify", scope={"label": "x"}, preflight={}, identity=IDENTITY)
    with pytest.raises(A.Refusal):
        A.scope_record("execute", "backup_restore_verify", scope={"label": "x"}, preflight={"ok": True}, identity=IDENTITY)


# ───────────────────────────── negative 5: staging or exit 0 is not completion ─────────────────────────────

def test_staging_or_a_local_exit_0_without_a_terminal_semantic_readback_cannot_complete(bench):
    prepared, path, req = accepted_request(bench)
    events = lambda: bench.events(ITEM)
    assert A.completion(bench.run, prepared, events(), None) == ("incomplete", "no executor receipt")

    bench.X.receipt(req, "RUNNING", "accepted; in flight")                        # still running
    assert A.completion(bench.run, prepared, events(), bench.observation(prepared))[0] == "incomplete"
    assert [i for i in bench.owed("POST-READBACK")[0] if i["item"] == ITEM] == []

    bench.wrapper = lambda argv, env, remote: (0, json.dumps({"staged_run_id": RUN_ID}))        # staged only; exit 0
    assert bench.execute(path, req) is None
    rpath, receipt = bench.receipt("OP-FIX-s2")
    assert (receipt["status"], receipt["exit_code"]) == ("COMPLETED", 0) and bench.remote.submissions == []
    assert A.completion(bench.run, prepared, events(), None) == ("unknown", "no terminal semantic observation of this operation")
    staged = bench.observation(prepared, terminal=False, outcome=None)
    assert A.completion(bench.run, prepared, events(), staged)[0] == "incomplete"

    # even the verifier's ACCEPTED verdict at the receipt digest does not stand in for the terminal observation
    assert bench.verdict(prepared)[0]["outcome"] == "done"
    assert A.completion(bench.run, prepared, events(), None)[0] == "unknown"
    assert A.completion(bench.run, prepared, events(), staged)[0] == "incomplete"
    for loose in (dict(terminal="true"), dict(terminal=1), dict(outcome="SUCCEEDED"), dict(outcome=True), dict(schema="other/1")):
        assert A.completion(bench.run, prepared, events(), bench.observation(prepared, **loose))[0] != "complete", loose
    assert A.completion(bench.run, prepared, events(), bench.observation(prepared, outcome="failed"))[0] == "failed"
    for unbound in (dict(operation_id="OP-FIX-s1"), dict(request_sha256="0" * 64), dict(receipt_sha256="0" * 64)):
        assert A.completion(bench.run, prepared, events(), bench.observation(prepared, **unbound))[0] == "refused", unbound
    assert A.completion(bench.run, prepared, None, bench.observation(prepared))[0] == "unknown"       # events unreadable
    assert A.completion(bench.run, prepared, [{"kind": "mystery"}], bench.observation(prepared))[0] == "unknown"
    assert A.completion(bench.run, prepared, events(), bench.observation(prepared)) == ("complete", None)


@pytest.mark.parametrize("rc,status", [(1, "FAILED"), (2, "FAILED")])
def test_a_failed_local_exit_raises_one_owner_wait_and_no_second_submission(bench, rc, status):
    prepared, path, req = accepted_request(bench)
    bench.wrapper = lambda argv, env, remote: (rc, "REFUSAL principal: mismatch")
    assert bench.execute(path, req) is None
    assert bench.receipt("OP-FIX-s2")[1]["status"] == status
    assert A.completion(bench.run, prepared, bench.events(ITEM), bench.observation(prepared))[0] == "refused"
    intents, _ = bench.owed("EXECUTE")
    assert len(intents) == 1 and K.start(bench, bench.job(intents[0]))["outcome"] == "done"
    assert len(bench.raised) == 1 and bench.raised[0].startswith("exec-op-fix-s2-")
    assert not (bench.X.REQ / "OP-FIX-s2.json").exists() and bench.owed("POST-READBACK")[0] == []


# ───────────────────────────── negative 6: output, receipt identity, receipt-digest verdict ─────────────────────────────

def completed(bench):
    prepared, path, req = accepted_request(bench)
    assert bench.execute(path, req) is None
    rpath, receipt = bench.receipt("OP-FIX-s2")
    return prepared, rpath, receipt


@pytest.mark.parametrize("damage", ["missing_output", "empty_output", "changed_output", "other_request", "other_item", "other_operation",
                                    "no_output_digest", "nonzero_exit", "true_exit"])
def test_a_missing_empty_or_changed_output_or_a_wrong_receipt_identity_refuses(bench, damage):
    prepared, rpath, receipt = completed(bench)
    assert K._b_receipt(bench.run, prepared) is not None
    out = Path(receipt["output_file"])
    if damage == "missing_output":
        out.unlink()
    elif damage == "empty_output":
        out.write_text("")
    elif damage == "changed_output":
        out.write_text(out.read_text().replace('"dry_run"', '"execute"').replace('"submitted": true', '"submitted": false') + " ")
    else:
        change = {"other_request": {"request_sha256": "0" * 64}, "other_item": {"item_id": "K9-OTHER"},
                  "other_operation": {"operation_id": "OP-FIX-s1"}, "no_output_digest": {"output_sha256": None},
                  "nonzero_exit": {"exit_code": 1}, "true_exit": {"exit_code": False}}[damage]
        rpath.write_text(json.dumps(dict(receipt, **change)))
    assert K._b_receipt(bench.run, prepared) is None
    state, reason = A.completion(bench.run, prepared, bench.events(ITEM), bench.observation(prepared))
    assert state == "refused" and "measured" in reason
    intents, unknown = bench.owed("POST-READBACK")
    assert intents == [], "an unmeasured receipt was offered for a verdict"
    if damage != "other_request":
        assert any("carries no measured readback" in u for u in unknown)


def test_a_verdict_at_another_digest_or_a_rejected_one_does_not_complete(bench):
    prepared, rpath, receipt = completed(bench)
    rsha = sha_file(rpath)
    observed = bench.observation(prepared)
    verdict = lambda digest, result: {"kind": "verdict", "item": ITEM, "phase": "artifact", "artifact_digest": digest, "result": result}
    complete = lambda events: A.completion(bench.run, prepared, events, observed)[0]
    assert complete([verdict("0" * 64, "ACCEPTED")]) == "incomplete"
    assert complete([verdict(receipt["output_sha256"], "ACCEPTED")]) == "incomplete"      # the output's digest is not the receipt's
    assert complete([verdict(prepared["request_sha256"], "ACCEPTED")]) == "incomplete"
    assert complete([dict(verdict(rsha, "ACCEPTED"), phase="post_deploy")]) == "incomplete"
    assert complete([dict(verdict(rsha, "ACCEPTED"), head=rsha, artifact_digest=None)]) == "incomplete"
    assert complete([verdict(rsha, "REJECTED")]) == "refused"
    assert complete([verdict(rsha, "ACCEPTED"), verdict(rsha, "REJECTED")]) == "refused"   # the latest verdict rules
    assert complete([verdict(rsha, "REJECTED"), verdict(rsha, "ACCEPTED")]) == "complete"

    # the receipt re-written after the verdict is another artifact: the old verdict no longer completes it
    rpath.write_text(json.dumps(dict(receipt, ts="2026-10-13T00:00:00+00:00"), indent=1))
    stale = [verdict(rsha, "ACCEPTED")]
    assert A.completion(bench.run, prepared, stale, observed)[0] == "refused"              # the observation names the old receipt
    assert A.completion(bench.run, prepared, stale, bench.observation(prepared))[0] == "incomplete"


@pytest.mark.parametrize("mutant,outcome,code", [
    ("digest", "failed", "receipt_digest_mismatch"),
    ("output_digest", "failed", "receipt_digest_mismatch"),
    ("quiescence_added", "failed", "evidence_changed"),
    ("receipt_changed", "failed", "receipt_digest_mismatch"),
    ("no_verdict", "failed", "no_semantic_verdict"),
    ("job_failed", "failed", "job_exit_nonzero"),
    ("builder_slot", "failed", "slot_unknown"),
    ("phase", "failed", "unknown_phase"),
])
def test_the_verdict_binds_the_actual_receipt_digest_and_its_quiescence_evidence(bench, mutant, outcome, code):
    prepared, rpath, receipt = completed(bench)
    intents, _ = bench.owed("POST-READBACK")
    assert len(intents) == 1 and intents[0]["digest"] == sha_file(rpath) and intents[0]["verdict_phase"] == "artifact"
    job = bench.job(intents[0], slot="v2", exit_code=0)
    assert K.start(bench, job) is None
    Path(job["result_path"]).write_text(json.dumps({"status": "done", "proposed_verdict": {"verdict": "ACCEPTED"}}))
    if mutant == "digest":
        job["digest"] = "0" * 64
    elif mutant == "output_digest":
        job["digest"] = receipt["output_sha256"]
    elif mutant == "quiescence_added":
        (bench.X.ACC / "OP-FIX-s2.quiescence.json").write_text(json.dumps({"result": "ACCEPTED"}))
    elif mutant == "receipt_changed":
        rpath.write_text(json.dumps(dict(receipt, reason="edited"), indent=1))
    elif mutant == "no_verdict":
        Path(job["result_path"]).write_text(json.dumps({"status": "done"}))
    elif mutant == "job_failed":
        job["exit_code"] = 1
    elif mutant == "builder_slot":
        job["slot"] = "b1"
    elif mutant == "phase":
        job["verdict_phase"] = "review"
    result = K.finish(bench, job)
    assert result["outcome"] == outcome and result["detail"].startswith(code + ":")
    assert bench.events(ITEM) == [], "a verdict was published"
    assert not any(argv[3:4] == ["publish"] for argv in bench.shells)


def test_changed_quiescence_evidence_is_a_new_fingerprint_and_an_unchanged_one_publishes(bench):
    prepared, rpath, receipt = completed(bench)
    first = bench.owed("POST-READBACK")[0][0]
    (bench.X.ACC / "OP-FIX-s2.quiescence.json").write_text(json.dumps({"result": "ACCEPTED", "by": "v3"}))
    second = bench.owed("POST-READBACK")[0][0]
    assert first["digest"] == second["digest"] == sha_file(rpath)
    assert first["evidence_fp"] != second["evidence_fp"] and first["key"] != second["key"]
    result, intent = bench.verdict(prepared)
    assert result["outcome"] == "done" and intent["key"] == second["key"]
    published = [argv for argv in bench.shells if argv[3:4] == ["publish"]]
    assert len(published) == 1
    opt = dict(zip(published[0][4::2], published[0][5::2]))
    assert (opt["--phase"], opt["--artifact-digest"], opt["--artifact-path"]) == ("artifact", sha_file(rpath), str(rpath))
    assert (opt["--author-id"], opt["--reviewer-id"]) == ("controller:c1", "stream-V:v2")
    assert bench.owed("POST-READBACK")[0] == []
