"""A7 D-44: executor-written mechanical acceptance (read-only ops) and mechanical quiescence (fenced production ops).

One doctrine-grounded oracle per distinct production claim (owner decision D-OWNER-TESTS-20261016; root CLAUDE.md §N.8 / §N.7.6 — a signal
is computed by a detector that can read false, otherwise it is null). Each claim has ONE planted reversion: the same oracle is run against a
copy of executor.py with that single line reverted and must FAIL there.

Post-acceptance (read-only kinds, acceptance/<op>.post.json, by executor-mechanical):
  P1 COMPLETED exit-0 read-only run  -> written, binding request sha, output sha, reviewed_commit; the receipt carries the session marker
  P2 non-zero exit / FAILED          -> nothing
  P3 archived request differs from the receipt's request digest -> nothing
  P4 output file differs from the receipt's output digest       -> nothing
  P5 reviewed_commit not merged to origin/main                  -> nothing
  P6 a writing (production) kind    -> nothing (needs one V signer)
  P7 a lane rehearsal               -> nothing
  P8 an existing acceptance is never replaced
Quiescence (acceptance/<op>.quiescence.json):
  Q1 every check holds -> written, and fence_quiescent() accepts it; Q2..Q12 one oracle per distinct condition
  F1 fence_quiescent accepts an executor-mechanical record only when every check in it is true
Admission:
  A1 validate() still refuses executor-mechanical as a PRE-acceptance of a writing operation (v1 stays valid)
Marker:
  M1 the child process of an operation carries PGAPPNAME = session_marker(operation_id)
  S1 quiescence_sessions.sh reports exactly the live sessions carrying the marker (real PostgreSQL on 127.0.0.1:55433)
"""
import datetime as dt
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import types
from pathlib import Path

import pytest

FLEET = Path(__file__).resolve().parents[1]
EXECUTOR_PY = FLEET / "executor.py"
SESSIONS_SH = FLEET / "quiescence_sessions.sh"
TABLE = json.loads((FLEET / "executor_ops.json").read_text())["ops"]
CHART = "482012f1-710e-4a25-994a-93821f5871aa"
EXEC_NAME = "brahma-build-pipeline-job-abc12"
GIT_ENV = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1", "GIT_TERMINAL_PROMPT": "0"}


def git(cwd, *args):
    p = subprocess.run(["git", "-C", str(cwd), "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args],
                       capture_output=True, text=True, env=GIT_ENV)
    assert p.returncode == 0, p.stderr
    return p.stdout.strip()


def iso(delta_s=0):
    return (dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=delta_s)).isoformat(timespec="seconds")


def sha(data):
    return hashlib.sha256(data if isinstance(data, bytes) else data.encode()).hexdigest()


class World:
    """A throwaway KY_ROOT and a throwaway git repository whose origin/main is its first commit; the real run_one / receipt run on it."""

    def __init__(self, tmp, mutations=()):
        self.tmp = tmp
        src = tmp / "src"
        (src / "scripts").mkdir(parents=True)
        (src / "scripts/print_marker.py").write_text("import os\nprint('MARK', os.environ.get('PGAPPNAME'))\n")
        git(tmp, "init", "-q", str(src))
        git(src, "add", "-A"); git(src, "commit", "-q", "-m", "main")
        self.commit = git(src, "rev-parse", "HEAD")
        git(src, "update-ref", "refs/remotes/origin/main", self.commit)
        git(src, "checkout", "-q", "-b", "side"); (src / "side.txt").write_text("x")
        git(src, "add", "-A"); git(src, "commit", "-q", "-m", "side")
        self.stray = git(src, "rev-parse", "HEAD")
        text = EXECUTOR_PY.read_text()
        for old, new in mutations:
            if text.count(old) != 1: raise RuntimeError(f"mutation anchor not unique: {old!r}")      # not an AssertionError: a bad anchor must never read as a failed oracle
            text = text.replace(old, new)
        module_path = tmp / "executor_under_test.py"
        module_path.write_text(text)
        saved = {k: os.environ.get(k) for k in ("KY_ROOT", "KY_SOURCE_REPO")}
        os.environ["KY_ROOT"] = str(tmp / "ky"); os.environ["KY_SOURCE_REPO"] = str(src)
        try:
            spec = importlib.util.spec_from_file_location(f"ky_exec_mech_{abs(hash((str(tmp), tuple(mutations))))}", module_path)
            self.mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(self.mod)
        finally:
            for k, v in saved.items():
                os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)
        m = self.mod
        for d in (m.REQ, m.REC, m.DONE, m.ACC, m.INFLIGHT, m.TMP, m.EXEC, m.KY_ROOT / "logs"):
            d.mkdir(parents=True, exist_ok=True)
        m.PY = sys.executable
        self.real_validate = m.validate
        m.load_table = lambda: TABLE
        m.sync = lambda: None
        m.capabilities = lambda on_main: {"none": True, "pgenv": True, "owner": True, "builder": True, "gcloud": True}
        m.validate = lambda req, table, caps, reserved=False: None

    def request(self, oid, kind="readback_sql", **extra):
        return {"operation_id": oid, "kind": kind, "item_id": "X", "idempotency_key": "k-" + oid, "requested_by": "adhikarin",
                "kyd": "kyd-1", "reviewed_commit": self.commit, "args": {}, **extra}

    def run(self, req, rc=0, out="rows\n", after_move=None):
        m = self.mod
        path = m.INFLIGHT / f"{req['operation_id']}.json"
        path.write_text(json.dumps(req))
        m.execute = lambda r, o: (rc, out)
        if after_move:
            real = shutil

            def move(a, b):
                real.move(a, b); after_move(Path(b))
            m.shutil = types.SimpleNamespace(move=move)
        else:
            m.shutil = shutil
        m.run_one(path, req, TABLE[req["kind"]])
        return m.ACC / f"{req['operation_id']}.post.json"


# ───────────────────────────── post-acceptance ─────────────────────────────

def oracle_p1(w):
    req = w.request("rb-1")
    post = w.run(req)
    assert post.exists(), "no mechanical post-acceptance for a COMPLETED exit-0 read-only run"
    doc = json.loads(post.read_text()); rec = json.loads((w.mod.REC / "rb-1.json").read_text())
    assert (doc["by"], doc["result"], doc["operation_id"], doc["reviewed_commit"]) == ("executor-mechanical", "ACCEPTED", "rb-1", w.commit)
    assert doc["request_sha256"] == w.mod.request_digest(req) == rec["request_sha256"] == w.mod.request_digest(json.loads((w.mod.DONE / "rb-1.json").read_text()))
    assert doc["output_sha256"] == sha((w.mod.REC / "rb-1.output.txt").read_bytes()) == rec["output_sha256"]
    assert doc["receipt_sha256"] == sha((w.mod.REC / "rb-1.json").read_bytes()) and doc["ts"] and all(v is True for v in doc["checks"].values())
    assert rec["session_marker"] == w.mod.session_marker("rb-1")


def oracle_p2(w):
    assert not w.run(w.request("rb-2"), rc=1, out="boom").exists(), "accepted a non-zero exit"


def oracle_p3(w):
    def tamper(done):
        done.write_text(json.dumps(dict(json.loads(done.read_text()), args={"sql_file": "other.sql"})))
    assert not w.run(w.request("rb-3"), after_move=tamper).exists(), "accepted a request that differs from the one the receipt binds"


def oracle_p4(w):
    assert not w.run(w.request("rb-4"), after_move=lambda done: (w.mod.REC / "rb-4.output.txt").write_text("other output")).exists(), \
        "accepted an output that differs from the receipt's digest"


def oracle_p5(w):
    assert not w.run(dict(w.request("rb-5"), reviewed_commit=w.stray)).exists(), "accepted a reviewed_commit that is not merged"


def oracle_p6(w):
    assert not w.run(w.request("bk-6", "backup_snapshot", args={"label": "abc", "scope": "small_test"})).exists(), \
        "a writing operation was accepted mechanically"


def oracle_p7(w):
    post = w.run(w.request("rb-7"))
    assert post.exists()
    post.unlink()
    receipt_path = w.mod.REC / "rb-7.json"
    receipt_path.write_text(json.dumps(dict(json.loads(receipt_path.read_text()), lane_target={"host": "127.0.0.1"})))
    assert w.mod.mechanical_post_acceptance(w.request("rb-7"), w.mod.DONE / "rb-7.json") == "not accepted: not_a_lane_rehearsal"
    assert not post.exists(), "a lane rehearsal was accepted"


def oracle_p8(w):
    (w.mod.ACC / "rb-8.post.json").write_text('{"by": "v1"}')
    w.run(w.request("rb-8"))
    assert (w.mod.ACC / "rb-8.post.json").read_text() == '{"by": "v1"}', "an existing acceptance was replaced"


POST = {
    "p1": (oracle_p1, ('    return None if write_new_json(ACC / f"{req[\'operation_id\']}.post.json", document) else "acceptance already exists; left untouched"', "    return None")),
    "p2": (oracle_p2, ('record.get("status") == "COMPLETED" and type(record.get("exit_code")) is int and record["exit_code"] == 0,', "True,")),
    "p3": (oracle_p3, ('archived_sha == record.get("request_sha256") == request_digest(req),', "True,")),
    "p4": (oracle_p4, ('"output_sha_equals_receipt": digest_bytes(body) == record.get("output_sha256"),', '"output_sha_equals_receipt": True,')),
    "p5": (oracle_p5, ('''(isinstance(commit, str) and SHA.fullmatch(commit) is not None and commit == record.get("reviewed_commit")
                                   and git("merge-base", "--is-ancestor", commit, "origin/main").returncode == 0),''', "True,")),
    "p6": (oracle_p6, ('entry.get("read_only") is True and entry.get("production") is False,', "True,")),
    "p7": (oracle_p7, ('not lane_selected(req) and "lane_target" not in record,', "True,")),
    "p8": (oracle_p8, ("os.link(pending, path)", "os.replace(pending, path)")),
}


@pytest.mark.parametrize("claim", sorted(POST))
def test_post_acceptance_oracle_passes_on_the_real_executor(tmp_path, claim):
    POST[claim][0](World(tmp_path))


@pytest.mark.parametrize("claim", sorted(POST))
def test_post_acceptance_oracle_fails_on_its_planted_reversion(tmp_path, claim):
    oracle, mutation = POST[claim]
    with pytest.raises(AssertionError):
        oracle(World(tmp_path, [mutation]))


# ───────────────────────────── quiescence ─────────────────────────────

def scenario(w, flaw=None, dispatch=False):
    """A fenced, finished production operation plus a completed quiescence_check; `flaw` breaks exactly one thing."""
    m = w.mod; target = "op-t"
    kind = {"teardown": "smalltest_teardown", "readonly_target": "readback_sql"}.get(flaw, "smalltest_dispatch" if dispatch else "backup_snapshot")
    done = {"operation_id": target, "kind": kind, "status": "RUNNING" if flaw == "not_terminal" else "COMPLETED", "exit_code": 0,
            "request_sha256": "a" * 64, "reviewed_commit": w.commit, "ts": iso(-120), "session_marker": m.session_marker(target)}
    if flaw == "no_marker": del done["session_marker"]
    if dispatch: done["launch"] = {"execution_name": EXEC_NAME}
    (m.REC / f"{target}.json").write_text(json.dumps(done))
    m.FENCE.write_text(json.dumps({"operation_id": "op-other" if flaw == "fence_other" else target, "request_sha256": "a" * 64, "ts": iso(-120)}))
    if flaw == "in_flight": (m.INFLIGHT / "x.json").write_text(json.dumps({"operation_id": target}))
    args = {"operation": target}
    if dispatch and flaw != "no_readback":
        output = json.dumps({"schema": "ky.cloudrun_readback/1", "status": "MEASURED", "execution": {
            "name": EXEC_NAME, "outcome": "RUNNING" if flaw == "remote_running" else "SUCCEEDED", "completion_time": iso(-60)}}) + "\n"
        (m.REC / "cr-1.output.txt").write_text(output)
        (m.REC / "cr-1.json").write_text(json.dumps({"operation_id": "cr-1", "kind": "cloudrun_job_readback", "status": "COMPLETED", "exit_code": 0,
                                                     "request_sha256": "b" * 64, "output_sha256": sha(output)}))
        readback_post = {"schema": "ky.mechanical_acceptance/1", "result": "ACCEPTED", "by": "executor-mechanical", "operation_id": "cr-1",
                         "request_sha256": "b" * 64, "checks": {"c": True}}
        if flaw == "readback_empty_checks": readback_post["checks"] = {}
        if flaw == "readback_no_schema": del readback_post["schema"]
        (m.ACC / "cr-1.post.json").write_text(json.dumps(readback_post))
        args["execution_readback"] = "cr-1"
    session = {"schema": "ky.session_readback/1", "status": "MEASURED", "marker": m.session_marker(target), "database": "d",
               "sees_all_sessions": flaw != "blind", "sessions": [{"pid": 7, "state": "idle"}] if flaw == "live_session" else [],
               "measured_at": iso(-300 if flaw == "measured_early" else -10)}
    check = w.request("chk-1", "quiescence_check", args=args)
    w.run(check, rc=1 if flaw == "check_failed" else 0, out=json.dumps(session) + "\n")
    return m.ACC / f"{target}.quiescence.json"


def oracle_q1(w):
    for dispatch in (False, True):
        for f in list(w.mod.ACC.glob("op-t.*")) + list(w.mod.REC.glob("*")) + list(w.mod.DONE.glob("*")): f.unlink()
        path = scenario(w, dispatch=dispatch)
        assert path.exists(), "no mechanical quiescence although every check holds"
        doc = json.loads(path.read_text())
        assert (doc["by"], doc["result"], doc["operation_id"], doc["request_sha256"]) == ("executor-mechanical", "ACCEPTED", "op-t", "a" * 64)
        assert doc["checks"] and all(v is True for v in doc["checks"].values()) and doc["session_check"]["live_sessions"] == 0
        assert (doc["remote_execution"] or {}).get("outcome") == ("SUCCEEDED" if dispatch else None)
        assert w.mod.fence_quiescent() is True, "fence_quiescent refuses the executor's own record"
        assert (w.mod.ACC / "chk-1.post.json").exists(), "the read-only check itself is accepted mechanically"


def blocked(flaw, dispatch=False):
    def oracle(w):
        assert not scenario(w, flaw, dispatch).exists(), f"quiescence written despite: {flaw}"
        assert not w.mod.fence_quiescent()
    return oracle


QUIESCENCE = {
    "q1": (oracle_q1, ("remote_execution_terminal=(remote is not None) if needs_remote else True)", "remote_execution_terminal=(remote is not None) if needs_remote else True)")),
    "q2_not_terminal": (blocked("not_terminal"), ('done.get("operation_id") == target and done.get("status") in ("COMPLETED", "FAILED", "AWAITING_ABSENCE"),', "True,")),
    "q3_in_flight": (blocked("in_flight"), ("target_not_in_flight=None not in inflight and target not in inflight,", "target_not_in_flight=True,")),
    "q4_live_session": (blocked("live_session"), ('no_live_session_carries_the_marker=sessions.get("sessions") == [],', "no_live_session_carries_the_marker=True,")),
    "q5_blind_readback": (blocked("blind"), ('session_readback_sees_every_role=sessions.get("sees_all_sessions") is True,', "session_readback_sees_every_role=True,")),
    "q6_no_marker": (blocked("no_marker"), ('(sessions.get("status") == "MEASURED" and sessions.get("marker") == marker == done.get("session_marker")),', "True,")),
    "q7_fence_other": (blocked("fence_other"), ('fence.get("operation_id") == target and bool(done.get("request_sha256")) and fence.get("request_sha256") == done.get("request_sha256"),', "True,")),
    "q8_measured_early": (blocked("measured_early"), ("session_readback_after_the_target_ended=after_terminal,", "session_readback_after_the_target_ended=True,")),
    "q9_remote_running": (blocked("remote_running", True), ("remote_execution_terminal=(remote is not None) if needs_remote else True)", "remote_execution_terminal=True)")),
    "q10_teardown": (blocked("teardown"), ('target_is_not_a_teardown=done.get("kind") not in TEARDOWN_KINDS,', "target_is_not_a_teardown=True,")),
    "q11_read_only_target": (blocked("readonly_target"), ('target_is_a_production_operation=entry.get("production") is True and "lane_target" not in done,', "target_is_a_production_operation=True,")),
    "q13_readback_record_unproven": (lambda w: [blocked(f, True)(w) for f in ("readback_empty_checks", "readback_no_schema")],
                                     ('(accepted.get("by") != "executor-mechanical"       # same bar as fence_quiescent: the record\'s own schema, and every check present and true\n'
                                      '                 or (accepted.get("schema") == "ky.mechanical_acceptance/1" and isinstance(accepted.get("checks"), dict)\n'
                                      '                     and bool(accepted["checks"]) and all(value is True for value in accepted["checks"].values())))',
                                      '(accepted.get("by") != "executor-mechanical" or all(value is True for value in (accepted.get("checks") or {}).values()))')),
    "q12_check_failed": (blocked("check_failed"), ("checks = dict(own_checks,", "checks = dict(")),
}
# Q1's reversion removes the whole writer: nothing may then be written.
QUIESCENCE["q1"] = (oracle_q1, ('        if req["kind"] == "quiescence_check":\n', '        if False:\n'))


@pytest.mark.parametrize("claim", sorted(QUIESCENCE))
def test_quiescence_oracle_passes_on_the_real_executor(tmp_path, claim):
    QUIESCENCE[claim][0](World(tmp_path))


@pytest.mark.parametrize("claim", sorted(QUIESCENCE))
def test_quiescence_oracle_fails_on_its_planted_reversion(tmp_path, claim):
    oracle, mutation = QUIESCENCE[claim]
    with pytest.raises(AssertionError):
        oracle(World(tmp_path, [mutation]))


def oracle_f1(w):
    m = w.mod
    base = {"schema": "ky.mechanical_quiescence/1", "by": "executor-mechanical", "result": "ACCEPTED", "operation_id": "op-f", "ts": iso(),
            "request_sha256": "c" * 64}
    (m.REC / "op-f.json").write_text(json.dumps({"operation_id": "op-f", "kind": "backup_snapshot", "request_sha256": "c" * 64}))
    m.FENCE.write_text(json.dumps({"operation_id": "op-f", "request_sha256": "c" * 64}))
    (m.ACC / "op-f.quiescence.json").write_text(json.dumps(dict(base, checks={"a": True, "b": False})))
    assert m.fence_quiescent() is False, "a mechanical record with a failed check released the fence"
    (m.ACC / "op-f.quiescence.json").write_text(json.dumps(dict(base, checks={"a": True, "b": True})))
    assert m.fence_quiescent() is True


def test_f1_passes_on_the_real_executor(tmp_path):
    oracle_f1(World(tmp_path))


def test_f1_fails_on_its_planted_reversion(tmp_path):
    mutation = ('''accepted = (proof.get("schema") == "ky.mechanical_quiescence/1" and isinstance(proof.get("checks"), dict)
                    and bool(proof["checks"]) and all(value is True for value in proof["checks"].values()))''', "accepted = True")
    with pytest.raises(AssertionError):
        oracle_f1(World(tmp_path, [mutation]))


# ───────────────────────────── admission ─────────────────────────────

def oracle_a1(w):
    m = w.mod
    m.lease_live = lambda lease: True
    results = {}
    for by in ("v1", "executor-mechanical"):
        oid = "bk-" + by.replace("executor-", "")[:4]
        acc_path = m.ACC / f"{oid}.json"
        req = w.request(oid, "backup_snapshot", args={"label": "abc", "scope": "small_test"}, chart_id=CHART, lease_id="L",
                        expires_at=iso(3600), acceptance_receipt=str(acc_path))
        acc_path.write_text(json.dumps({"result": "ACCEPTED", "by": by, "operation_id": oid, "reviewed_commit": w.commit, "ts": iso(-5),
                                        "request_sha256": m.request_digest(req), "checks": {}}))
        results[by] = w.real_validate(req, TABLE, {"owner": True, "none": True, "pgenv": True, "builder": True, "gcloud": True})
    assert results["v1"] is None, results
    assert results["executor-mechanical"] == "pre-acceptance receipt is not an ACCEPTED receipt by a verifier lane for this operation", results


def test_a1_passes_on_the_real_executor(tmp_path):
    oracle_a1(World(tmp_path))


def test_a1_fails_on_its_planted_reversion(tmp_path):
    mutation = ('a.get("operation_id") != req["operation_id"] or a.get("by") not in ("v1", "v2", "v3", "v4"):',
                'a.get("operation_id") != req["operation_id"] or a.get("by") not in ("v1", "v2", "v3", "v4", "executor-mechanical"):')
    with pytest.raises(AssertionError):
        oracle_a1(World(tmp_path, [mutation]))


# ───────────────────────────── the marker ─────────────────────────────

def oracle_m1(w):
    req = w.request("m-1", "fixture_ro")
    rc, out = w.mod.execute(req, {"script": "scripts/print_marker.py", "needs": "none", "production": False})
    assert rc == 0, out
    assert f"MARK {w.mod.session_marker('m-1')}" in out and w.mod.session_marker("m-1").startswith("ky-op-"), out


def test_m1_passes_on_the_real_executor(tmp_path):
    oracle_m1(World(tmp_path))


def test_m1_fails_on_its_planted_reversion(tmp_path):
    with pytest.raises(AssertionError):
        oracle_m1(World(tmp_path, [('env["PGAPPNAME"] = session_marker(oid)', "pass")]))


# ───────────────────────────── the session readback (real PostgreSQL) ─────────────────────────────

VENV = Path("/Users/Dev/kalayantra")


def oracle_s1(tmp_path, script):
    psycopg = pytest.importorskip("psycopg")
    conninfo = dict(host="127.0.0.1", port=55433, user="postgres", dbname="postgres", connect_timeout=5)
    try:
        psycopg.connect(**conninfo).close()
    except psycopg.OperationalError as exc:
        if os.environ.get("KALA_REQUIRE_DB") == "1":
            pytest.fail(f"KALA_REQUIRE_DB=1 but the test cluster is unreachable: {exc}")
        pytest.skip("test cluster 127.0.0.1:55433 unreachable")
    if not (VENV / "venv/bin/python").exists():
        pytest.skip("venv python missing")
    pgenv = tmp_path / "pgenv.sh"
    pgenv.write_text("export PGHOST=127.0.0.1 PGPORT=55433 PGUSER=postgres PGDATABASE=postgres\n")
    env = {k: v for k, v in os.environ.items() if k in ("PATH", "HOME", "LANG", "TMPDIR")}
    env.update(KY_ROOT=str(VENV), KY_READBACK_PGENV=str(pgenv))
    operation = "op-session-oracle"

    def read():
        p = subprocess.run(["bash", str(script), "--operation", operation, "--execution_readback", "cr-1"], capture_output=True, text=True, env=env, timeout=60)
        assert p.returncode == 0, p.stderr
        return json.loads(p.stdout.strip().splitlines()[-1])

    marker = "ky-op-" + sha(operation)[:16]
    with psycopg.connect(**conninfo, application_name=marker) as held:
        pid = held.info.backend_pid
        live = read()
    assert live["schema"] == "ky.session_readback/1" and live["marker"] == marker and live["sees_all_sessions"] is True
    assert [s["pid"] for s in live["sessions"]] == [pid], live
    assert read()["sessions"] == [], "a closed session is still listed"


def test_s1_passes_on_the_real_script(tmp_path):
    oracle_s1(tmp_path, SESSIONS_SH)


def test_s1_fails_on_its_planted_reversion(tmp_path):
    text = SESSIONS_SH.read_text()
    old = "WHERE application_name = %s AND pid"
    assert text.count(old) == 1
    mutated = tmp_path / "mutated.sh"
    mutated.write_text(text.replace(old, "WHERE application_name <> %s AND pid"))
    with pytest.raises(AssertionError):
        oracle_s1(tmp_path, mutated)


def test_marker_formula_is_the_same_in_the_executor_and_the_script(tmp_path):
    assert World(tmp_path).mod.session_marker("op-session-oracle") == "ky-op-" + sha("op-session-oracle")[:16]
    assert '"ky-op-" + hashlib.sha256(operation.encode()).hexdigest()[:16]' in SESSIONS_SH.read_text()


# ───────── the marker reaches every database connection of every production kind eligible for mechanical quiescence (R3694-B1) ─────────
# A kind is eligible when mechanical_quiescence() can accept it: enabled, production, and not a teardown (executor.py `target_is_not_a_teardown`).
# The *_dryrun kinds are production:false (A8), so `target_is_a_production_operation` refuses them: they are not eligible and carry no row.
# Quiescence reads sessions by application_name; a client that opens connections without the marker (pg_dump under a scrubbed environment was the
# defect) would leave a live session invisible, so "zero sessions" would read green with a backup still running. One row per eligible kind says how
# its connections get the marker; the table must cover exactly the eligible kinds, so a newly eligible kind cannot slip in unproven.
import ast

ROOT = FLEET.parents[3]
PLATFORM_SCRIPTS = ROOT / "platform/scripts"
TEARDOWN_KINDS = ("smalltest_teardown", "measuring_teardown", "century_teardown")
ELIGIBLE = {kind for kind, entry in TABLE.items() if entry.get("enabled") is True and entry.get("production") is True and kind not in TEARDOWN_KINDS}
# route "client_env": the op's own psycopg connections inherit PGAPPNAME and every pg_dump / pg_restore client it starts gets it through client_env().
# route "in_process": every database connection is a psycopg connection opened inside the op's own process from DATABASE_URL (libpq applies PGAPPNAME);
#   a dispatch's remote Cloud Run execution is not covered here — the execution readback covers it (MECHANICAL_ACCEPTANCE §2).
MARKER_ROUTE = {
    "backup_snapshot": "client_env",
    "backup_restore_verify": "client_env",
    "smalltest_dispatch": "in_process",
    "scheduler_pause": "no_database",       # SR-J3-REAPER-PAUSE: needs gcloud only, no DATABASE_URL, no connection at all (test_executor_scheduler_reaper pins that); synchronous, never fenced
    "scheduler_resume": "no_database",
    "measuring_cancel": "no_database",      # SR-J3-CANCEL-NULL: gcloud only, no DATABASE_URL; synchronous, never fenced
    "measuring_dispatch": "in_process",     # J-3a: measuring_launch.py opens only psycopg connections from DATABASE_URL (no PGAPPNAME/application_name in its closure — the next test)
    "century_dispatch": "in_process",       # SR-PREBUILD-ALL: century_launch.py is the same bridge (smalltest_launch.launch_staged) over the same staging closure — the next test scans it
}
# A8 §3 fences only remote_async kinds; the *_dryrun kinds are production:false in executor_ops.json, so they are not eligible and carry no row.
# Teardowns (smalltest_teardown, measuring_teardown, century_teardown) stay excluded by TEARDOWN_KINDS: executor.py `target_is_not_a_teardown` still refuses them.
BACKUP_CARRY = "        env['PGAPPNAME'] = os.environ['PGAPPNAME']"
SUBPROCESS_CALLS = {"run", "Popen", "call", "check_call", "check_output"}


def script_path(kind):
    rel = TABLE[kind]["script"]
    return ROOT / rel


def import_closure(first, overrides):
    """The op's own source files: the script and every repository module it imports (anywhere in the file), with `overrides` {path: text} applied."""
    seen, queue = {}, [first]
    while queue:
        path = queue.pop()
        if path in seen: continue
        seen[path] = overrides.get(path, path.read_text())
        for node in ast.walk(ast.parse(seen[path])):
            names = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or ""] if isinstance(node, ast.ImportFrom) else []
            for name in names:
                for folder in (path.parent, PLATFORM_SCRIPTS):
                    if (folder / (name.split(".")[0] + ".py")).exists(): queue.append(folder / (name.split(".")[0] + ".py"))
    return seen


def marker_violations(kind, overrides=None):
    """Why this kind's connections might not carry the marker (empty = none found)."""
    problems = []
    for path, text in import_closure(script_path(kind), overrides or {}).items():
        tree = ast.parse(text)
        words = {n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)} | {
            k.arg for n in ast.walk(tree) if isinstance(n, ast.Call) for k in n.keywords if k.arg}       # code, not comments
        if any("application_name" in w for w in words): problems.append(f"{path.name} names its own application_name")
        if any("PGAPPNAME" in w for w in words) and not (path.name == "backup_v5_small_test_job.py" and MARKER_ROUTE[kind] == "client_env"):
            problems.append(f"{path.name} touches PGAPPNAME")
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in SUBPROCESS_CALLS:
                env = next((k.value for k in node.keywords if k.arg == "env"), None)
                if env is not None and not (isinstance(env, ast.Call) and getattr(env.func, "id", "") == "client_env"):
                    problems.append(f"{path.name}:{node.lineno} starts a process with its own environment")
            if isinstance(node, ast.Call) and ast.unparse(node.func) in ("os.environ.clear", "os.environ.pop", "os.unsetenv", "os.putenv"):
                problems.append(f"{path.name}:{node.lineno} edits the process environment")
            if isinstance(node, ast.Delete) and any(ast.unparse(t).startswith("os.environ") for t in node.targets):
                problems.append(f"{path.name}:{node.lineno} deletes from the process environment")
    return problems


def test_every_kind_eligible_for_mechanical_quiescence_has_a_marker_route():
    assert ELIGIBLE == set(MARKER_ROUTE), f"eligible kinds {sorted(ELIGIBLE)} differ from the proven routes {sorted(MARKER_ROUTE)}"


@pytest.mark.parametrize("kind", sorted(MARKER_ROUTE))
def test_no_code_of_an_eligible_kind_strips_or_overrides_the_marker(kind):
    assert marker_violations(kind) == []


def test_a_planted_override_of_the_marker_is_detected():
    teardown = PLATFORM_SCRIPTS / "teardown_v5_small_test_job.py"
    planted = teardown.read_text() + "\nos.environ.pop('PGAPPNAME', None)\n"
    assert marker_violations("smalltest_teardown_dryrun", {teardown: planted}), "an op that strips PGAPPNAME went undetected"


def load_backup(text=None):
    path = PLATFORM_SCRIPTS / "backup_v5_small_test_job.py"
    source = path.read_text() if text is None else text
    module = types.ModuleType("backup_under_test"); module.__file__ = str(path)
    sys.path.insert(0, str(PLATFORM_SCRIPTS))
    try: exec(compile(source, str(path), "exec"), module.__dict__)
    finally: sys.path.remove(str(PLATFORM_SCRIPTS))
    return module


def oracle_backup_client_marker(backup, monkeypatch):
    """A real libpq client started with the environment backup.client_env() builds reports the marker as its application_name on the test cluster."""
    psycopg = pytest.importorskip("psycopg")
    settings = dict(host="127.0.0.1", port="55433", user="postgres", dbname="postgres", connect_timeout="5")
    try:
        psycopg.connect(**settings).close()
    except psycopg.OperationalError as exc:
        if os.environ.get("KALA_REQUIRE_DB") == "1":
            pytest.fail(f"KALA_REQUIRE_DB=1 but the test cluster is unreachable: {exc}")
        pytest.skip("test cluster 127.0.0.1:55433 unreachable")
    marker = "ky-op-" + sha("op-backup-marker")[:16]
    monkeypatch.setenv("PGAPPNAME", marker)                    # what executor.execute() gives the child
    env = backup.client_env(settings)
    assert env.get("PGSERVICE") is None and env["PGPASSFILE"] == os.devnull
    probe = "import psycopg; print(psycopg.connect('').execute('SELECT application_name FROM pg_stat_activity WHERE pid = pg_backend_pid()').fetchone()[0])"
    out = subprocess.run([sys.executable, "-c", probe], env=env, capture_output=True, text=True, timeout=60)
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == marker, f"the client's session carries {out.stdout.strip()!r}, not the operation marker: quiescence cannot see it"


@pytest.mark.parametrize("kind", sorted(k for k, route in MARKER_ROUTE.items() if route == "client_env"))
def test_backup_clients_connect_with_the_operation_marker(kind, monkeypatch):
    oracle_backup_client_marker(load_backup(), monkeypatch)


def test_backup_clients_connecting_without_the_marker_is_detected(monkeypatch):
    text = (PLATFORM_SCRIPTS / "backup_v5_small_test_job.py").read_text()
    assert text.count(BACKUP_CARRY) == 1
    with pytest.raises(AssertionError):
        oracle_backup_client_marker(load_backup(text.replace(BACKUP_CARRY, "        pass")), monkeypatch)


def test_backup_client_env_still_drops_every_other_pg_setting_and_the_connection_variables(monkeypatch):
    backup = load_backup()
    for name, value in (("PGSERVICE", "prod"), ("PGHOST", "remote"), ("PGPASSWORD", "x"), ("DATABASE_URL", "x"), ("KY_OWNER_DATABASE_URL", "x"), ("PGAPPNAME", "m")):
        monkeypatch.setenv(name, value)
    env = backup.client_env(backup.scratch_settings("lbl"))
    assert env["PGAPPNAME"] == "m" and "PGSERVICE" not in env and "DATABASE_URL" not in env and "KY_OWNER_DATABASE_URL" not in env
    assert env["PGHOST"] == "127.0.0.1" and env["PGPASSWORD"] != "x"
