"""Executor operation-adapter acceptance harness. Real validate/run_one/execute/receipt,
with in-process fake Git, child and remote boundaries; no dispatcher, daemon, Git writes,
credentials, cloud or production connections. P01 enables six reviewed small-test bindings; rebuild entries are enabled only in copies.
SQLite exercises DB-API rollback mechanics; it does not qualify a production DB operation.
"""
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
OPS_FILE = FLEET / "executor_ops.json"
DISPATCH_PY = REPO / "platform" / "scripts" / "dispatch_v5_small_test_job.py"
PREFLIGHT_TS = REPO / "platform" / "scripts" / "data-plane-secret-isolation-preflight.ts"
OPS_REL = "00_ARCHITECTURE/briefs/kalayantra/fleet/executor_ops.json"
COORD_REL = "00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md"
PROTECTED = [EXECUTOR_PY, OPS_FILE, DISPATCH_PY, PREFLIGHT_TS]
P01_KINDS = {"backup_snapshot", "backup_restore_verify", "smalltest_dispatch_dryrun",
             "smalltest_dispatch", "smalltest_teardown_dryrun", "smalltest_teardown"}
SCHEDULER_KINDS = {"scheduler_readback", "scheduler_pause_dryrun", "scheduler_pause", "scheduler_resume_dryrun", "scheduler_resume", "measuring_cancel_dryrun", "measuring_cancel"}   # SR-J3-REAPER-PAUSE (+ SR-J3-CANCEL-NULL)
VERIFICATION_KINDS = {"verification_job", "verification_job_dryrun"}   # J-4b (SR-PREBUILD-ALL)
PROBE_KINDS = {"served_probe"}   # SR-TEARDOWN-AUTHORITY-GATE item 3: read-only, production:false
MEASURING_KINDS = {"measuring_dispatch_dryrun", "measuring_dispatch", "measuring_teardown_dryrun", "measuring_teardown"}   # J-3a
K9_KINDS = {"orchestrator_rebuild_dryrun", "orchestrator_rebuild", "layer_verify_dryrun", "layer_verify", "layer_publish_dryrun", "layer_publish",
            "layer_rollback_dryrun", "layer_rollback"}   # K9-23
CENTURY_KINDS = {"century_dispatch_dryrun", "century_dispatch", "century_teardown_dryrun", "century_teardown"}   # SR-PREBUILD-ALL; century_teardown enabled by W3W4 pack verify E1 (signed-only)
FAMILY_CANCEL_KINDS = {"century_cancel_dryrun", "century_cancel", "verification_cancel_dryrun", "verification_cancel"}   # W3W4 pack verify E1: measuring_cancel's siblings
HEAD_KINDS = {"publish_head", "publish_head_dryrun", "rollback_head", "rollback_head_dryrun"}
ENABLED_KINDS = {"readback_sql", "migration_readback", "cloudrun_job_readback", "quiescence_check", "local_schema_seed", "finalize"} | P01_KINDS | MEASURING_KINDS | SCHEDULER_KINDS | VERIFICATION_KINDS | K9_KINDS | CENTURY_KINDS | PROBE_KINDS | FAMILY_CANCEL_KINDS | HEAD_KINDS   # SR-HEAD-POLICY-KEEP: the head kinds are enabled through the head policy
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




def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

A = _load(ADAPTERS_PY, "ky_operation_adapters_under_test")

def sha_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

@pytest.fixture(scope="module", autouse=True)
def protected_sources_unchanged():
    """The sources this item must not touch, and the table, carry the same bytes after the module as before it."""
    before = {str(p): sha_file(p) for p in PROTECTED}
    yield
    assert {str(p): sha_file(p) for p in PROTECTED} == before, "a protected source or the table changed during the tests"

def real_table():
    return json.loads(OPS_FILE.read_text())["ops"]

def fixture_table():
    """A COPY of the table in which the two orchestrator-rebuild kinds stand for an eventual reviewed mapping: enabled,
    the fixture wrapper as script, the mode in fixed_args (I3). Every other entry is the table's, byte for byte."""
    table = real_table()
    for kind, mode in (("orchestrator_rebuild_dryrun", "--dry-run"), ("orchestrator_rebuild", "--execute")):
        table[kind] = dict(table[kind], enabled=True, script=WRAPPER_REL, fixed_args=[mode])
        table[kind].pop("python_module", None)           # K9-23 binds these to a python -m module; this harness runs its file wrapper instead
        table[kind].pop("cwd", None)
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
        run_arg, = [arg for arg in argv if arg.startswith("--args=--run-id,")]
        self.state[run_arg.removeprefix("--args=--run-id,")] = "RUNNING"
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

def step(kind, opid, **more):
    expires = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=2)).isoformat(timespec="seconds")
    base = {"kind": kind, "operation_id": opid, "kyd": "kyd-fixture", "args": {"assets": "ka_fixture", "run-id": RUN_ID},
            "lease_id": LEASE, "reviewed_commit": MERGED, "expires_at": expires}
    base.update(more)
    return base

DRY = lambda **more: step("orchestrator_rebuild_dryrun", "OP-FIX-s1", **more)
RUN = lambda **more: step("orchestrator_rebuild", "OP-FIX-s2", **more)


class Bench:
    """A temporary executor root; all effects beyond it are in-process fakes."""
    def __init__(self, tmp_path, monkeypatch):
        self.root = tmp_path / "ky"
        self.scratch = tmp_path
        monkeypatch.setenv("KY_ROOT", str(self.root))
        monkeypatch.setenv("KY_SOURCE_REPO", str(tmp_path / "no-repository"))
        monkeypatch.setenv("KY_BUILDER_DATABASE_URL", DSN)
        monkeypatch.setenv("KY_OWNER_DATABASE_URL", DSN)
        self.X = X = _load(EXECUTOR_PY, "ky_executor_for_adapters_" + uuid.uuid4().hex)
        for d in (X.REQ, X.REC, X.DONE, X.ACC, X.INFLIGHT, X.TMP, X.EXEC, X.KY_ROOT / "logs"):
            d.mkdir(parents=True, exist_ok=True)
        self.git, self.remote = FakeGit(fixture_table()), FakeRemote()
        self.launched, self.event_log = [], {}
        self.wrapper = fixture_wrapper
        X.git, X.capabilities, X.run_group = self.git, lambda _: dict(ALL_CAPS), self.process
        # The writer-digest overlay (J-2a M12) has its own oracles in test_executor_overlay.py; here `process` is the one wrapper.
        X.apply_generated_overlay = lambda root, commit, env, timeout=600: ({"schema": "ky.generated_overlay/1", "source_sha": commit, "files": {}}, "")
        self.run = X.RUN

    def process(self, argv, cwd, env, timeout):
        self.launched.append({"argv": list(argv), "cwd": str(cwd), "env": dict(env)})
        assert Path(argv[1]).exists()
        rc, out = self.wrapper(argv[2:], env, self.remote)
        return subprocess.CompletedProcess(argv, rc, out, "")

    def execute(self, path, req):
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

    def receipt(self, opid):
        path = self.X.REC / (opid + ".json")
        return path, json.loads(path.read_text())

    def events(self, item):
        return list(self.event_log.get(item, []))

    def verdict(self, prepared):
        self.event_log.setdefault(ITEM, []).append({"kind": "verdict", "item": ITEM, "phase": "artifact",
            "artifact_digest": sha_file(self.X.REC / (prepared["operation_id"] + ".json")),
            "result": "ACCEPTED", "actor": "stream-V:v2"})

    def observation(self, prepared, **fields):
        state = self.remote.state.get(prepared["request"]["args"]["run-id"])
        return dict({"schema": A.OBSERVATION_SCHEMA, "operation_id": prepared["operation_id"],
            "request_sha256": prepared["request_sha256"], "terminal": state in {"SUCCEEDED", "FAILED"},
            "outcome": {"SUCCEEDED": "succeeded", "FAILED": "failed"}.get(state),
            "receipt_sha256": sha_file(self.X.REC / (prepared["operation_id"] + ".json")), "source": "fake remote"}, **fields)

def accepted_request(bench, steps=None):
    spec = (steps or [RUN()])[0]
    req = dict(spec, item_id=ITEM, idempotency_key=spec["operation_id"], requested_by="adhikarin", chart_id=CANONICAL_CHART)
    digest = bench.X.request_digest(req)
    prepared = {"schema": "ky.op_prepared/1", "operation_id": req["operation_id"], "item": ITEM, "step": 1,
        "request": copy.deepcopy(req), "request_sha256": digest, "prepared_by": "controller:fixture", "prepared_by_slot": None}
    acc = bench.X.ACC / (req["operation_id"] + ".json")
    acc.write_text(json.dumps({"result": "ACCEPTED", "operation_id": req["operation_id"], "request_sha256": digest,
        "reviewed_commit": MERGED, "by": "v1", "ts": bench.X.now(), "rows": {"2": True, "3": True},
        "checks": {"backup_taken": True, "restore_verified": True, "dry_run_passed": True}}))
    req["acceptance_receipt"] = str(acc)
    path = bench.X.REQ / (req["operation_id"] + ".json")
    path.write_text(json.dumps(req))
    return prepared, path, req

@pytest.fixture
def bench(tmp_path, monkeypatch):
    return Bench(tmp_path, monkeypatch)

def test_the_fixture_table_differs_from_the_table_in_the_two_fixture_entries_only():
    real, fixture = real_table(), fixture_table()
    assert list(real) == list(fixture)
    assert {k for k in real if real[k] != fixture[k]} == {"orchestrator_rebuild_dryrun", "orchestrator_rebuild"}

def test_the_helpers_copied_constants_are_the_sources(bench):
    X = bench.X
    assert A.CHILD_ENV_ALLOW == X.CHILD_ENV_ALLOW
    assert [r.pattern for r in A.SECRET_VALUE] == [r.pattern for r in X.REDACT]
    assert A.CANONICAL_CHART == X.CANONICAL_CHART == CANONICAL_CHART
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


def test_a_read_only_kind_launches_as_the_helper_states_it(bench):
    table = real_table()
    bench.git.table = table
    bench.git.scripts["00_ARCHITECTURE/briefs/kalayantra/fleet/readback_sql.sh"] = "#!/bin/bash\n"
    bench.wrapper = lambda argv, env, remote: (0, "rows\n")
    req = {"operation_id": "OP-READ", "kind": "migration_readback", "item_id": ITEM, "idempotency_key": "OP-READ",
           "requested_by": "v1", "kyd": "kyd-fixture", "args": {"migration": "0412"}}
    assert bench.X.validate(req, table, dict(ALL_CAPS)) is None
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

def test_a_disabled_or_placeholder_entry_an_unauthorised_requester_or_disallowed_args_refuses(bench):
    X, fixture = bench.X, fixture_table()
    real = real_table()
    base = RUN()
    req = dict({k: base[k] for k in ("kind", "operation_id", "kyd", "args", "lease_id", "reviewed_commit", "expires_at")},
               item_id=ITEM, idempotency_key="OP-FIX-s2", requested_by="adhikarin", chart_id=CANONICAL_CHART)
    for kind, entry in real.items():
        if entry["production"] and not entry["enabled"]:
            assert X.validate(dict(req, kind=kind, args={}), real, ALL_CAPS).startswith("kind %s is not enabled" % kind)
    placeholder = dict(real, publish_head=dict(real["publish_head"], enabled=True, script="TO_BE_SET_FIXTURE"))
    assert X.validate(dict(req, kind="publish_head", args={}), placeholder, ALL_CAPS) == "operation script not yet reviewed/landed"
    for changes, reason in [
        ({"kind": "no_such_kind"}, "unknown kind"),
        ({"requested_by": "b1"}, "requested_by"),
        ({"args": {"sql": "x"}}, "disallowed args"),
        ({"args": {"assets": "ka_fixture; unsafe"}}, "an argument value"),
        ({"chart_id": "other"}, "chart_id"),
    ]:
        assert X.validate(dict(req, **changes), fixture, ALL_CAPS).startswith(reason)


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
    assert with_acceptance(ts=ago(hours=3, seconds=30)) is None                         # A8 §4: no age cap — valid until the request's expires_at
    assert with_acceptance(ts=ago(hours=-1)) == expired                                 # issued in the future
    assert with_acceptance(ts="2026-10-13T08:00:00").startswith("valid approval timestamp")       # no timezone
    assert validate(dict(req, expires_at=ago(seconds=5))) == expired                    # A8 §3.9: expires_at is outside the digest; only the clock refuses
    assert validate(dict(req, expires_at=ago(days=-3))) is None                         # an extension voids nothing
    assert with_acceptance(by="b1").startswith("pre-acceptance receipt is not an ACCEPTED receipt")
    assert with_acceptance(result="REJECTED").startswith("pre-acceptance receipt is not an ACCEPTED receipt")
    for check in ("dry_run_passed",):                                                  # A8 §5: the one attestation a mutating non-teardown kind needs
        partial = {k: v for k, v in accepted["checks"].items() if k != check}
        assert with_acceptance(checks=partial) == "required backup/restore/dry-run attestation missing", check
        assert with_acceptance(checks=dict(accepted["checks"], **{check: "true"})) == "required backup/restore/dry-run attestation missing"
    for retired in ("backup_taken", "restore_verified"):                               # A8 §5: retired as preconditions (backup_taken stays for *_teardown only)
        assert with_acceptance(checks={k: v for k, v in accepted["checks"].items() if k != retired}) is None, retired
    assert with_acceptance(rows={"2": True, "3": False}) is None                        # A8 §5: required_rows retired

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

def test_request_arguments_are_read_in_any_order_and_nothing_else_is_read(bench):
    """The executor appends --key value in the request's own key order, which the request digest does not bind."""
    def parse(argv):
        parser = argparse.ArgumentParser()
        A.add_mode_arguments(parser)
        return vars(A.parse_request_args(argv, ("assets", "run-id"), parser))

    forward = {"assets": "ka_fixture", "run-id": RUN_ID}
    backward = dict(reversed(list(forward.items())))
    assert bench.X.request_digest({"args": forward}) == bench.X.request_digest({"args": backward})
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

@pytest.mark.parametrize("failed_probe", ["rows", "head"])
def test_rehearsal_rolls_back_when_a_during_probe_fails(lane, failed_probe):
    """OPS-NB-02: a real SELECT failure after mutations must leave no transaction or changes."""
    def fail_during(value):
        if lane.in_transaction:
            raise RuntimeError("during probe unavailable")
        return value

    lane.create_function("fail_during", 1, fail_during)
    probes = dict(PROBES)
    head = HEAD
    if failed_probe == "rows":
        probes["rows"] = "SELECT id, fail_during(state) FROM runs ORDER BY id"
    else:
        head = "SELECT fail_during(generation) FROM head"
    try:
        with pytest.raises(sqlite3.OperationalError, match="user-defined function raised exception"):
            A.rehearse(lane, STATEMENTS, probes, head, target=LANE, identity=IDENTITY)
        assert (lane.in_transaction, lane_state(lane)) == (False, ([("r1", "done")], [(7,)]))
    finally:
        lane.rollback()

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

def test_staging_or_a_local_exit_0_without_a_terminal_semantic_readback_cannot_complete(bench):
    prepared, path, req = accepted_request(bench)
    events = lambda: bench.events(ITEM)
    assert A.completion(bench.run, prepared, events(), None) == ("incomplete", "no executor receipt")

    bench.X.receipt(req, "RUNNING", "accepted; in flight")                        # still running
    assert A.completion(bench.run, prepared, events(), bench.observation(prepared))[0] == "incomplete"

    bench.wrapper = lambda argv, env, remote: (0, json.dumps({"staged_run_id": RUN_ID}))        # staged only; exit 0
    assert bench.execute(path, req) is None
    rpath, receipt = bench.receipt("OP-FIX-s2")
    assert (receipt["status"], receipt["exit_code"]) == ("COMPLETED", 0) and bench.remote.submissions == []
    assert A.completion(bench.run, prepared, events(), None) == ("unknown", "no terminal semantic observation of this operation")
    staged = bench.observation(prepared, terminal=False, outcome=None)
    assert A.completion(bench.run, prepared, events(), staged)[0] == "incomplete"

    # even the verifier's ACCEPTED verdict at the receipt digest does not stand in for the terminal observation
    bench.verdict(prepared)
    assert A.completion(bench.run, prepared, events(), None)[0] == "unknown"
    assert A.completion(bench.run, prepared, events(), staged)[0] == "incomplete"
    # Synthetic observations below probe the completion contract's malformed/unbound evidence cases.
    observed = bench.observation(prepared, terminal=True, outcome="succeeded")
    for loose in (dict(terminal="true"), dict(terminal=1), dict(outcome="SUCCEEDED"), dict(outcome=True), dict(schema="other/1")):
        assert A.completion(bench.run, prepared, events(), dict(observed, **loose))[0] != "complete", loose
    assert A.completion(bench.run, prepared, events(), dict(observed, outcome="failed"))[0] == "failed"
    for unbound in (dict(operation_id="OP-FIX-s1"), dict(request_sha256="0" * 64), dict(receipt_sha256="0" * 64)):
        assert A.completion(bench.run, prepared, events(), dict(observed, **unbound))[0] == "refused", unbound
    assert A.completion(bench.run, prepared, None, observed)[0] == "unknown"       # events unreadable
    assert A.completion(bench.run, prepared, [{"kind": "mystery"}], observed)[0] == "unknown"
    assert A.completion(bench.run, prepared, events(), observed) == ("complete", None)

def completed(bench):
    prepared, path, req = accepted_request(bench)
    assert bench.execute(path, req) is None
    bench.remote.state[req["args"]["run-id"]] = "SUCCEEDED"
    rpath, receipt = bench.receipt("OP-FIX-s2")
    return prepared, rpath, receipt


def test_fake_remote_tracks_the_requested_run():
    remote = FakeRemote()
    other_run = "1d1f8a52-6f0e-4c7e-9a3b-5a2a2f6f9c11"
    for run_id in (RUN_ID, other_run):
        A.remote_launch("execute", run_id, remote, environ={})
    assert remote.state == {RUN_ID: "RUNNING", other_run: "RUNNING"}


@pytest.mark.parametrize("remote_state,terminal,outcome,completion", [
    (None, False, None, "incomplete"),
    ("RUNNING", False, None, "incomplete"),
    ("FAILED", True, "failed", "failed"),
    ("SUCCEEDED", True, "succeeded", "complete"),
])
def test_observation_is_derived_from_remote_state(bench, remote_state, terminal, outcome, completion):
    other_run = "1d1f8a52-6f0e-4c7e-9a3b-5a2a2f6f9c11"
    prepared, path, req = accepted_request(bench, [RUN(args={"assets": "ka_fixture", "run-id": other_run})])
    assert bench.execute(path, req) is None
    bench.remote.state[RUN_ID] = "FAILED" if remote_state == "SUCCEEDED" else "SUCCEEDED"
    if remote_state is None:
        bench.remote.state.pop(other_run, None)
    else:
        bench.remote.state[other_run] = remote_state
    bench.verdict(prepared)
    observed = bench.observation(prepared)
    assert (observed["terminal"], observed["outcome"]) == (terminal, outcome)
    assert A.completion(bench.run, prepared, bench.events(ITEM), observed)[0] == completion

@pytest.mark.parametrize("damage", ["missing_output", "empty_output", "changed_output", "other_request", "other_item", "other_operation",
                                    "no_output_digest", "nonzero_exit", "true_exit"])
def test_a_missing_empty_or_changed_output_or_a_wrong_receipt_identity_refuses(bench, damage):
    prepared, rpath, receipt = completed(bench)
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
    state, reason = A.completion(bench.run, prepared, bench.events(ITEM), bench.observation(prepared))
    assert state == "refused" and "measured" in reason


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






def test_dry_run_and_execution_share_the_plan_and_only_terminal_readback_completes(bench):
    dry, path, req = accepted_request(bench, [DRY()])
    before = bench.remote.fingerprint()
    assert bench.execute(path, req) is None
    dry_record = json.loads(Path(bench.receipt(dry["operation_id"])[1]["output_file"]).read_text())
    assert A.dry_run_refusal(dry_record, submissions=len(bench.remote.submissions), before=before,
        after=bench.remote.fingerprint()) is None
    prepared, path, req = accepted_request(bench)
    assert bench.execute(path, req) is None
    receipt = bench.receipt(prepared["operation_id"])[1]
    record = json.loads(Path(receipt["output_file"]).read_text())
    assert record["planned_argv"] == dry_record["planned_argv"] == bench.remote.submissions[0]["argv"]
    assert record["submitted"] is True and dry_record["submitted"] is False
    assert "DATABASE_URL" not in bench.remote.submissions[0]["env"]
    assert A.completion(bench.run, prepared, [], None)[0] == "unknown"
    bench.verdict(prepared)
    assert A.completion(bench.run, prepared, bench.events(ITEM), bench.observation(prepared))[0] == "incomplete"
    bench.remote.state[RUN_ID] = "FAILED"
    assert A.completion(bench.run, prepared, bench.events(ITEM), bench.observation(prepared))[0] == "failed"
    bench.remote.state[RUN_ID] = "SUCCEEDED"
    assert A.completion(bench.run, prepared, bench.events(ITEM), bench.observation(prepared)) == ("complete", None)
    assert bench.X.FENCE.exists() and not bench.X.fence_quiescent()
    proof = {"operation_id": prepared["operation_id"], "request_sha256": prepared["request_sha256"],
        "result": "ACCEPTED", "by": "v2", "ts": bench.X.now()}
    quiescence = bench.X.ACC / (prepared["operation_id"] + ".quiescence.json")
    quiescence.write_text(json.dumps(dict(proof, request_sha256="0" * 64)))
    assert not bench.X.fence_quiescent() and bench.X.FENCE.exists()
    quiescence.write_text(json.dumps(proof))
    assert bench.X.fence_quiescent() and bench.X.FENCE.exists()


def test_completion_works_without_the_retired_dispatcher(bench, monkeypatch):
    prepared, _, _ = completed(bench)
    bench.verdict(prepared)
    real = importlib.util.spec_from_file_location
    def no_dispatcher(name, path, *args, **kwargs):
        assert Path(path).name != "kyd_kinds_ops.py", "executor contract depends on retired dispatcher"
        return real(name, path, *args, **kwargs)
    monkeypatch.setattr(importlib.util, "spec_from_file_location", no_dispatcher)
    adapter = _load(ADAPTERS_PY, "ky_independent_adapter")
    assert adapter.completion(bench.run, prepared, bench.events(ITEM), bench.observation(prepared)) == ("complete", None)


def test_remote_plan_matches_the_current_wave4_launcher(monkeypatch):
    wrapper = _load(FLEET / "smalltest_launch.py", "ky_current_smalltest_launcher")
    seen = []
    def execute(argv, **kwargs):
        seen.append(argv)
        return subprocess.CompletedProcess(argv, 0, "brahma-build-pipeline-job-fixture", "")
    monkeypatch.setattr(wrapper.subprocess, "run", execute)
    wrapper.cloud_launcher(RUN_ID, 20)
    assert A.remote_execute_argv(A.BUILD_JOB, RUN_ID) == seen[0]


def test_only_p01_production_kinds_are_enabled_and_wave4_launch_stays_bound(bench):
    table = real_table()
    assert {k for k, v in table.items() if v["enabled"]} == ENABLED_KINDS
    assert {k for k, v in table.items() if v["production"] and v["enabled"]} == {k for k in P01_KINDS | MEASURING_KINDS | K9_KINDS | CENTURY_KINDS | FAMILY_CANCEL_KINDS | {"scheduler_pause", "scheduler_resume", "measuring_cancel", "verification_job", "publish_head", "rollback_head"} if not k.endswith("_dryrun")}   # A8 §3.8
    entry = table["smalltest_dispatch"]
    assert entry["script"].endswith("/smalltest_launch.py") and entry["also_needs"] == ["gcloud"]
    for kind in ("smalltest_dispatch",):
        fixture = copy.deepcopy(bench.git.table)
        fixture[kind]["enabled"] = True
        caps = dict(ALL_CAPS, gcloud=False)
        assert bench.X.validate(dict(RUN(), item_id=ITEM, idempotency_key="id", requested_by="adhikarin",
            kind=kind, args={}), fixture, caps) == "capability_missing: gcloud"



def test_another_items_verdict_cannot_complete_this_operation(bench):
    prepared, rpath, _ = completed(bench)
    events = [{"kind": "verdict", "item": "K9-OTHER", "phase": "artifact",
               "artifact_digest": sha_file(rpath), "result": "ACCEPTED"}]
    assert A.completion(bench.run, prepared, events, bench.observation(prepared))[0] == "incomplete"


def test_remote_launch_refuses_another_project_even_with_its_matching_principal():
    fake = FakeRemote(service_account="data-plane-builder-runtime@another-project.iam.gserviceaccount.com")
    with pytest.raises(A.Refusal):
        A.remote_launch("execute", RUN_ID, fake, project="another-project", environ={})
    assert fake.submissions == []


@pytest.mark.parametrize("exit_code", [1, 2])
def test_failed_execution_is_receipted_and_cannot_be_retried_automatically(bench, exit_code):
    prepared, path, req = accepted_request(bench)
    bench.wrapper = lambda argv, env, remote: (exit_code, "REFUSAL principal: mismatch")
    assert bench.execute(path, req) is None
    assert bench.receipt(prepared["operation_id"])[1]["status"] == "FAILED"
    assert A.completion(bench.run, prepared, [], bench.observation(prepared))[0] == "refused"
    assert bench.X.validate(req, bench.X.load_table(), ALL_CAPS) == "idempotency key already used"
    assert bench.remote.submissions == [] and bench.X.FENCE.exists()
