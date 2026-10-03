"""The combined executor against a disposable PostgreSQL holding a replay of migration 1035 on production-shaped roles/owners/ACLs.
Never a real system; the administrator is a fake: a non-superuser CREATEROLE role with no table privilege (PostgreSQL <= 15) or the cluster
superuser (>= 16, DPFA2_TEST_ADMIN=postgres)."""
from __future__ import annotations

import dataclasses
import json
import pathlib
import re
import subprocess
import sys

import psycopg
import pytest

import conftest as cf
import live_manifest as lm
import shapes
from conftest import EXEC_DIR


@pytest.fixture()
def runner(cluster, mod, db, tmp_path):
    return cf.Runner(cluster, mod, db, tmp_path)


def outcome(res):
    return json.loads(pathlib.Path(res["outcome_file"]).read_text())


def reader_rows(cluster, db, fname):
    r = subprocess.run([cf.PSQL, "-X", "-A", "-t", "-F", "|", "-h", "127.0.0.1", "-p", str(cluster.port), "-U", "rehearsal_reader", "-d", db,
                        "-f", str(EXEC_DIR / fname)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    rows = [ln.split("|") for ln in r.stdout.splitlines() if ln.strip()]
    return rows


def only_known_failures(rows):
    """Every verify row is PASS or INFO except check 31, which compares the L2 functions that EXIST with production's md5: the two
    stub functions the gate's regprocedure literals need are not production's text (documented in schema/07)."""
    bad = [r for r in rows if r[-1] not in ("PASS", "INFO") and r[0] not in ("31", "999")]
    assert bad == [], bad
    return {r[0]: r for r in rows}


# ------------------------------------------------------------------------------------------------------------- the model
def test_replay_is_production_faithful(cluster, db, mod):
    rows = cluster.su(db, "SELECT p.oid::regprocedure::text, md5(pg_get_functiondef(p.oid)), length(pg_get_functiondef(p.oid)), "
                          "pg_get_userbyid(p.proowner), p.prosecdef, COALESCE(p.proconfig::text,''), COALESCE(p.proacl::text,'') FROM pg_proc p "
                          "JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='public' AND (p.proname LIKE 'l1\\_data\\_plane\\_%' "
                          "OR p.proname IN ('open_l1_data_plane_generation','capture_l1_data_plane_dasha_partition','authorize_l1_chart_facts_delete',"
                          "'complete_l1_data_plane_partition','select_l1_data_plane_generation','rollback_l1_data_plane_generation'))")
    got = {r[0]: (r[1], r[2], r[3], r[4], r[5], r[6]) for r in rows}
    assert got == lm.LIVE_L1_MANIFEST
    assert cluster.su(db, "SELECT count(*) FROM public.l1_data_plane_trigger_attestations")[0][0] == lm.LIVE_ATTESTATION_COUNTS["trigger"]
    assert cluster.su(db, "SELECT count(*) FROM public.l1_data_plane_function_attestations")[0][0] == lm.LIVE_ATTESTATION_COUNTS["function"]
    assert cluster.su(db, "SELECT definition_digest FROM public.l1_data_plane_trigger_attestations WHERE trigger_name='l1_data_plane_capture' "
                          "AND table_name='chart_divisionals'")[0][0] == lm.LIVE_CAPTURE_TRIGGER_DIGEST
    # production-shaped ownership: tables, functions and attestation tables belong to the protected owners; the admin holds nothing
    assert cluster.su(db, "SELECT pg_get_userbyid(relowner) FROM pg_class WHERE relname='chart_divisionals'")[0][0] == "data_plane_l1_owner"
    assert cluster.su(db, "SELECT pg_get_userbyid(relowner) FROM pg_class WHERE relname='l2_data_plane_trigger_attestations'")[0][0] == "data_plane_l2_owner"
    if cluster.major <= 15:
        assert cluster.su(db, "SELECT has_table_privilege('adm','public.chart_divisionals','SELECT'), has_schema_privilege('adm','public','USAGE')")[0] == (False, False)


# ------------------------------------------------------------------------------------------------------------ the dry run
def test_dry_run_prints_the_diff_and_leaves_everything_identical(runner):
    before = runner.state()
    code, res = runner.run("dry-run")
    assert code == 0 and res["status"] == "DRY_RUN_ROLLED_BACK_ALL_CHECKS_HOLD", res["details"]
    assert runner.state() == before
    log = "\n".join(res["log"])
    assert "commit conditions: ALL HOLD" in log and "AS PLANNED" in log and "UNEXPECTED" not in log
    assert "FUNCTION BODY l1_data_plane_capture_row()" in log and "ACCESS EXCLUSIVE window" in log
    o = outcome(res)
    assert o["status"] == "dry_run" and o["failed_checks"] == [] and o["evidence_digest"] == res["evidence_digest"]
    assert o["plan_hash"] == runner.m.plan_hash() and o["under_test"] is False
    assert o["python_executable"] == sys.executable and o["python_version"] == sys.version        # the interpreter is recorded through the real run path
    ev = pathlib.Path(res["evidence_dir"])
    assert {f.name for f in ev.iterdir()} >= {"outcome.json", "report.txt", "result.json", "before_state.json", "fn_before_l1_data_plane_capture_row.sql"}
    assert (ev / "fn_before_l1_data_plane_capture_row.sql").read_text() == runner.m.CAPTURE_PATCH.live_def()
    assert all(oct(f.stat().st_mode & 0o777) == "0o600" for f in ev.iterdir())


def test_count_is_read_only_and_records_an_outcome(runner):
    before = runner.state()
    code, res = runner.run("count")
    assert code == 0 and res["status"] == "COUNT_READ_ONLY_OK" and runner.state() == before
    assert outcome(res)["status"] == "dry_run"


# ------------------------------------------------------------------------------------------------------------- the apply
def test_apply_commits_exactly_the_expected_diff(runner, cluster, db, mod):
    before = runner.state()
    code, res = runner.run("apply")
    assert code == 0 and res["status"] == "COMMITTED", res["details"]
    after = runner.state()
    p = mod.CAPTURE_PATCH
    # --- the function: body, md5, owner/secdef/config/ACL
    assert before["md5"] == p.live_md5 and after["md5"] == p.patched_md5 and after["fn"] == p.patched_def()
    f_before = {r[0]: r for r in before["snap"]["function"]}
    f_after = {r[0]: r for r in after["snap"]["function"]}
    assert set(f_before) == set(f_after)
    changed = sorted(k for k in f_before if f_before[k] != f_after[k])
    patched = sorted(q.signature for q in mod.FUNCTION_PATCHES)
    assert changed == patched
    for k in changed:
        b, a = f_before[k], f_after[k]
        assert b[2:] == a[2:] and b[2] == "data_plane_l1_owner" and b[3] == "true" and b[4] == '{"search_path=pg_catalog, public, pg_temp"}'   # owner, secdef, config, ACL unchanged
    # --- the other functions keep their md5
    assert all(f_before[k][1] == f_after[k][1] for k in f_before if k not in patched)
    # --- attestation: ONE row per patched function + ONE trigger row; every other row identical
    att_b, att_a = set(map(tuple, before["att"])), set(map(tuple, after["att"]))
    n_trg = len(mod.TRIGGER_CHANGES)
    assert len(att_b - att_a) == len(patched) + n_trg and len(att_a - att_b) == len(patched) + n_trg
    assert {r[1] for r in att_b - att_a} == set(patched) | {c.table for c in mod.TRIGGER_CHANGES}       # ONLY the changed tables' rows
    fn_row = [r for r in att_a - att_b if r[0] == "F" and r[1] == "l1_data_plane_capture_row()"][0]
    assert fn_row[2] == p.patched_sha256 and fn_row[3:] == ("data_plane_l1_owner", "true", '{"search_path=pg_catalog, public, pg_temp"}')
    trg_rows = {r[1]: r for r in att_a - att_b if r[0] == "T"}
    for c in mod.TRIGGER_CHANGES:
        assert trg_rows[c.table][2] == "l1_data_plane_capture" and trg_rows[c.table][5] == c.to_digest
    assert trg_rows["chart_divisionals"][5] == mod.PATCHED_TRG_DIGEST
    # --- index, trigger, comments; nothing else (ACL / RLS / policy / row data / immutable triggers identical)
    assert len(before["snap"]["index"] - after["snap"]["index"]) == 1 and len(after["snap"]["index"] - before["snap"]["index"]) == 1
    assert len(before["snap"]["trigger"] - after["snap"]["trigger"]) == len(mod.TRIGGER_CHANGES)
    assert len(after["snap"]["comment"]) == 7 and len(before["snap"]["comment"]) == 2
    for k in ("acl", "rls", "policy", "rowdata", "immutable_triggers"):
        assert before["snap"][k] == after["snap"][k], k
    # --- the executor's membership snapshot: transient grants revoked
    assert cluster.su(db, "SELECT count(*) FROM pg_auth_members am JOIN pg_roles m ON m.oid=am.member WHERE m.rolname='adm'")[0][0] == 0 \
        or cluster.major > 15
    o = outcome(res)
    assert o["status"] == "applied" and o["failed_checks"] == []
    assert o["python_executable"] == sys.executable and o["python_version"] == sys.version


def test_attestation_drift_is_zero_and_the_gate_is_green_after_apply(runner, cluster, db, mod):
    code, res = runner.run("apply")
    assert code == 0, res["details"]
    with cluster.conn(db) as c:
        cur = c.cursor()
        cur.execute("SET LOCAL search_path = public")             # the gate's own session path
        g = mod.fa2.gate_mirror(cur, cf.L1_TABLES)
        c.rollback()
    assert mod.fa2.gate_red(g) == [] and g["trigger_digest_stored"] == g["trigger_digest_gate_side"] == mod.PATCHED_TRG_DIGEST
    assert g["function_digest_stored"] == g["function_digest_gate_side"] == mod.CAPTURE_PATCH.patched_sha256
    drift = cluster.su(db, """SELECT count(*) FROM public.l1_data_plane_function_attestations a
        LEFT JOIN pg_proc p ON p.oid = to_regprocedure('public.'||a.function_signature)
        WHERE p.oid IS NULL OR a.definition_digest <> encode(digest(pg_get_functiondef(p.oid),'sha256'),'hex')
           OR a.owner_name <> pg_get_userbyid(p.proowner) OR a.security_definer <> p.prosecdef OR a.config IS DISTINCT FROM p.proconfig""")[0][0]
    assert drift == 0


def test_other_trigger_attestations_are_unchanged_by_the_three_hunks(runner, cluster, db, mod):
    """H1-H3 alone (patch A without F-A2's trigger change) touch ONLY the capture-function attestation row: apply the patch-A body by hand."""
    live = mod.CAPTURE_PATCH.live_def()
    a_only = mod.pa.patch_a(live)
    before_att = cluster.su(db, "SELECT table_name, trigger_name, trigger_type, enabled, function_oid, function_signature, definition_digest "
                                "FROM public.l1_data_plane_trigger_attestations ORDER BY 1,2")
    with cluster.conn(db, autocommit=False) as c:
        cur = c.cursor()
        cur.execute("SET LOCAL ROLE data_plane_l1_owner")
        cur.execute(a_only)                                       # composed A compiles
        cur.execute("ALTER TABLE public.l1_data_plane_function_attestations DISABLE TRIGGER l1_data_plane_function_attestations_immutable")
        cur.execute(mod.fn_att_update_sql("l1_data_plane_capture_row()"))
        assert cur.rowcount == 1
        cur.execute("ALTER TABLE public.l1_data_plane_function_attestations ENABLE TRIGGER l1_data_plane_function_attestations_immutable")
        cur.execute("RESET ROLE")
        c.commit()
    assert cluster.su(db, "SELECT table_name, trigger_name, trigger_type, enabled, function_oid, function_signature, definition_digest "
                          "FROM public.l1_data_plane_trigger_attestations ORDER BY 1,2") == before_att
    assert cluster.su(db, "SELECT md5(pg_get_functiondef('public.l1_data_plane_capture_row()'::regprocedure))")[0][0] \
        == __import__("hashlib").md5(a_only.encode()).hexdigest()
    with cluster.conn(db) as c:
        cur = c.cursor()
        cur.execute("SET LOCAL search_path = public")
        g = mod.fa2.gate_mirror(cur, cf.L1_TABLES)
        c.rollback()
    assert mod.fa2.gate_red(g) == []                              # patch A alone attests cleanly


def test_function_only_variants_compile_and_attest(runner, cluster, db, mod):
    """A+F composed compiles and attests (done by the executor); the F-A2 hunk alone compiles too."""
    live = mod.CAPTURE_PATCH.live_def()
    f_only = mod.pa.apply_hunks(live, [mod.FA2_HUNK])
    cluster.su(db, f_only, user="postgres")
    assert cluster.su(db, "SELECT position('fact_subject=' in pg_get_functiondef('public.l1_data_plane_capture_row()'::regprocedure)) > 0")[0][0]


# ------------------------------------------------------------------------ EXPECTED_DIFF: any extra byte fails (in the database too)
def test_a_body_that_differs_by_one_extra_byte_in_the_database_is_refused(runner, mod, monkeypatch):
    before = runner.state()
    orig = mod.apply_leg

    def tampered(cur, leg, on_exclusive=None):
        steps = tuple(dataclasses.replace(s, to_def=s.to_def.replace("RETURN NEW;\nEND;", "RETURN NEW; -- x\nEND;")) for s in leg.functions)
        assert steps[0].to_def != leg.functions[0].to_def
        return orig(cur, dataclasses.replace(leg, functions=steps), on_exclusive)

    monkeypatch.setattr(mod, "apply_leg", tampered)
    code, res = runner.run("apply")
    assert code == 1 and res["status"] == "REFUSED_ROLLED_BACK"
    assert "post_l1_data_plane_capture_row_body_is_exactly_the_bound_body" in res["failed_checks"]
    assert runner.state() == before                                  # rolled back, nothing committed
    assert outcome(res)["status"] == "failed"


def test_a_tampered_hunk_is_refused_before_any_connection(mod, monkeypatch, tmp_path):
    m = cf.load_exec("d6_tamper")
    m.GATE_PINS.update(cf.fixture_pins())
    p = m.CAPTURE_PATCH
    approved = m.plan_hash()                       # the hash the operator was given for the shipped hunks
    monkeypatch.setattr(m, "FUNCTION_PATCHES", (dataclasses.replace(p, hunks=p.hunks[:-1] + (("F", p.hunks[-1][1], p.hunks[-1][2] + " "),)),))
    monkeypatch.setattr(m, "plan_hash", lambda *a, **k: approved)         # even if the operator's hash matches, the body is refused
    args = m.parse_args(["--dry-run", "--expect-plan", approved])
    with pytest.raises(SystemExit):
        m.execute(args, lambda: pytest.fail("connected"))
    o = json.loads(next((tmp_path / "ev").glob("*/outcome.json")).read_text())
    assert o["failed_checks"] == ["expected_diff_mismatch"]


# ----------------------------------------------------------------------------------------- idempotency, evidence, outcome
def test_a_second_apply_refuses_cleanly(runner):
    code, res = runner.run("apply")
    assert code == 0
    mid = runner.state()
    code, res2 = runner.run("apply")
    assert code == 1 and res2["status"] == "REFUSED_ROLLED_BACK"
    assert {"pre_l1_data_plane_capture_row_body_is_the_bound_body", "pre_index_shape", "pre_trigger_shape_chart_divisionals",
            "pre_trigger_shape_chart_vichara"} <= set(res2["failed_checks"])
    assert runner.state() == mid


def test_the_evidence_digest_is_equal_for_dry_run_and_apply_and_a_wrong_digest_is_refused(runner):
    code, dry = runner.run("dry-run")
    code, bad = runner.execute(runner.args("apply", expect_evidence="0" * 64))
    assert code == 1 and bad["failed_checks"] == ["evidence_digest_matches_expected"]
    code, ok = runner.execute(runner.args("apply", expect_evidence=dry["evidence_digest"]))
    assert code == 0 and ok["evidence_digest"] == dry["evidence_digest"]


def test_an_interruption_after_the_commit_records_applied_never_failed(runner, mod, monkeypatch):
    orig = mod.conclude

    def interrupted(o, result, kind, *a, **k):
        if kind == "applied":
            raise KeyboardInterrupt                    # the applied write is interrupted AFTER the COMMIT
        return orig(o, result, kind, *a, **k)
    monkeypatch.setattr(mod, "conclude", interrupted)
    with pytest.raises(KeyboardInterrupt):
        runner.run("apply")
    outs = sorted(runner.tmp.glob("ev/apply_*/outcome.json"))
    body = json.loads(outs[-1].read_text())
    assert body["status"] == "applied" and any(w.startswith("outcome_write_failed_after_commit:") for w in body["warnings"])
    assert runner.state()["md5"] == mod.CAPTURE_PATCH.patched_md5                    # the commit really happened


class CommitProxy:
    """A connection whose commit() can be made to raise (and, optionally, to reach the server first)."""

    def __init__(self, conn, server_commits):
        self._c, self._server_commits = conn, server_commits

    def commit(self):
        if self._server_commits:
            self._c.commit()
        raise psycopg.OperationalError("synthetic: connection dropped at the commit acknowledgement")

    def __getattr__(self, name):
        return getattr(self._c, name)


@pytest.mark.parametrize("server_committed", [False, True], ids=["connection_lost_before_the_server_saw_it", "ack_lost_after_the_server_committed"])
def test_a_commit_call_that_itself_raises_is_commit_state_unknown_not_failed(runner, cluster, db, mod, server_committed):
    """The real server outcome differs between the two cases and the executor cannot know: both are `commit_state_unknown`, never `failed`."""
    pre = runner.state()
    _, dry = runner.execute(runner.args("dry-run"))
    with pytest.raises(psycopg.OperationalError):
        mod.execute(runner.args("apply", expect_evidence=dry["evidence_digest"]),
                    lambda: CommitProxy(cluster.conn(db, user=cf.ADMIN_USER), server_committed),
                    gate_tables=cf.L1_TABLES, writer_runner=cf.writer_runner(mod))
    outs = sorted(runner.tmp.glob("ev/apply_*/outcome.json"))
    body = json.loads(outs[-1].read_text())
    assert body["status"] == "commit_state_unknown" and body["warnings"] == ["commit_raised:OperationalError"] and body["failed_checks"] == []
    assert body["evidence_digest"] == dry["evidence_digest"]
    assert (runner.state()["md5"] == mod.CAPTURE_PATCH.patched_md5) is server_committed        # the outcome is honest about not knowing


def test_a_broken_stderr_never_costs_the_commit_state_unknown_outcome(mod, tmp_path, monkeypatch):
    class BrokenStderr:
        def write(self, *a):
            raise OSError("closed")

        def flush(self):
            raise OSError("closed")
    es = mod.standards()
    d = tmp_path / "run"
    d.mkdir()
    monkeypatch.setattr(mod.sys, "stderr", BrokenStderr())
    with pytest.raises(RuntimeError):
        with mod.safe_outcome_class(es)(d, str(EXEC_DIR / "d6_dataplane_capture_fa2_exec.py"), "a" * 64, dict(es.fingerprint(str(cf.GATE_FIXTURE)), under_test=False)) as o:
            o.mark_commit_unknown("b" * 64, "OperationalError")
            raise RuntimeError("x")
    monkeypatch.undo()
    assert json.loads((d / "outcome.json").read_text())["status"] == "commit_state_unknown"


def test_the_exclusive_window_is_short_and_measured(runner):
    code, res = runner.run("apply")
    m = re.search(r"ACCESS EXCLUSIVE window \(UTC\): \S+ -> \S+; statements inside it: (\d+)", "\n".join(res["log"]))
    assert m and int(m.group(1)) <= 100
    log = "\n".join(res["log"])
    assert log.index("writer-first check") < log.index("ACCESS EXCLUSIVE window")


# ------------------------------------------------------------------------------------------------ the rollback rehearsal
def test_the_rollback_is_rehearsed_apply_verify_rollback_verify_equal_to_the_pre_state(runner, cluster, db, mod):
    pre = runner.state()
    pre_verify = only_known_failures(reader_rows(cluster, db, "verify_before_apply.sql"))
    assert pre["md5"] == mod.CAPTURE_PATCH.live_md5
    code, res = runner.run("apply")
    assert code == 0, res["details"]
    applied = runner.state()
    assert applied != pre and applied["md5"] == mod.CAPTURE_PATCH.patched_md5
    only_known_failures(reader_rows(cluster, db, "verify_after_apply.sql"))
    # rollback dry run: changes nothing, then the real rollback
    code, rd = runner.run("rollback-dry-run")
    assert code == 0 and rd["status"] == "DRY_RUN_ROLLED_BACK_ALL_CHECKS_HOLD", rd["details"]
    assert runner.state() == applied
    code, rb = runner.run("rollback")
    assert code == 0 and rb["status"] == "COMMITTED", rb["details"]
    post = runner.state()
    # equal to the pre-state: every function md5 and the full body, every attestation row, the index, trigger, comments, ACL, RLS, rows
    assert post == pre
    assert post["md5"] == mod.CAPTURE_PATCH.live_md5 == "1e079261aa42eb97a1885a48035e7520"
    assert post["att"] == pre["att"]
    only_known_failures(reader_rows(cluster, db, "verify_before_apply.sql"))
    assert outcome(rb)["status"] == "applied"
    # the forward plan can be applied again after a rollback (the inverse really is the inverse)
    code, again = runner.run("apply")
    assert code == 0 and runner.state() == applied


def test_the_rollback_is_refused_when_widened_rows_collide_on_the_old_key(runner, cluster, db):
    code, res = runner.run("apply")
    assert code == 0
    # two rows sharing the six-column key but differing in fact_subject (legal under the widened index), inserted as the superuser with the
    # guard/capture triggers off
    cols = cluster.su(db, "SELECT column_name, is_nullable, column_default FROM information_schema.columns WHERE table_name='chart_divisionals' "
                          "AND is_nullable='NO' AND column_default IS NULL")
    names = [c[0] for c in cols]
    vals = {"chart_id": f"'{cf.CHART}'", "graha": "'Sun'", "ayanamsha_id": "'lahiri_chitrapaksha'", "varga": "'D1'",
            "fact_category": "'varga_ashtakavarga'", "fact_key": "'bindus'", "build_id": f"'{cf.CHART}'"}
    for n in names:
        vals.setdefault(n, "'x'")
    with cluster.conn(db, autocommit=True) as c:
        c.execute("SET session_replication_role = replica")
        for sub in ("D1.S1", "D1.S2"):
            c.execute(f"INSERT INTO public.chart_divisionals ({', '.join(list(vals) + ['fact_subject'])}) VALUES ({', '.join(list(vals.values()) + [repr(sub)])})")
    mid = runner.state()
    code, rb = runner.run("rollback")
    assert code == 1 and "pre_no_widened_rows_collide_on_the_six_column_key" in rb["failed_checks"]
    assert runner.state() == mid


# ------------------------------------------------------------------------------------------------------- refusal cases
def refusal(runner, expect_checks, mode="apply"):
    before = runner.state()
    code, res = runner.run(mode) if mode != "apply" else runner.run("apply")
    assert code == 1 and res["status"] == "REFUSED_ROLLED_BACK", res
    assert set(expect_checks) <= set(res["failed_checks"]), res["failed_checks"]
    assert runner.state() == before
    assert outcome(res)["status"] == "failed"
    return res


def test_refused_when_the_live_function_md5_differs_from_the_plans(runner, cluster, db, mod):
    body = mod.CAPTURE_PATCH.live_def().replace("RETURN NEW;\nEND;", "RETURN NEW; -- drift\nEND;")
    cluster.su(db, body)                                       # superuser re-creates it: owner becomes the superuser too, so fix the owner
    cluster.su(db, "ALTER FUNCTION public.l1_data_plane_capture_row() OWNER TO data_plane_l1_owner")
    cluster.su(db, "REVOKE ALL ON FUNCTION public.l1_data_plane_capture_row() FROM PUBLIC")
    refusal(runner, ["pre_l1_data_plane_capture_row_body_is_the_bound_body"])


def test_refused_when_the_function_is_not_owned_by_the_l1_owner(runner, cluster, db):
    cluster.su(db, "ALTER FUNCTION public.l1_data_plane_capture_row() OWNER TO data_plane_l2_owner")
    refusal(runner, ["pre_l1_data_plane_capture_row_owner_secdef_config_acl"])


def test_refused_when_the_function_is_missing(runner, cluster, db):
    cluster.su(db, "DROP FUNCTION public.l1_data_plane_capture_row() CASCADE")
    code, res = runner.run("dry-run")
    assert code == 2 and "pre_l1_data_plane_capture_row_present" in res["failed_checks"] and outcome(res)["status"] == "failed"
    code, res = runner.run("apply")
    assert code == 1 and "pre_l1_data_plane_capture_row_present" in res["failed_checks"]


def test_refused_when_the_attestation_row_is_missing(runner, cluster, db):
    cluster.su(db, "ALTER TABLE public.l1_data_plane_function_attestations DISABLE TRIGGER l1_data_plane_function_attestations_immutable")
    cluster.su(db, "DELETE FROM public.l1_data_plane_function_attestations WHERE function_signature='l1_data_plane_capture_row()'")
    cluster.su(db, "ALTER TABLE public.l1_data_plane_function_attestations ENABLE TRIGGER l1_data_plane_function_attestations_immutable")
    refusal(runner, ["pre_l1_data_plane_capture_row_attestation_row"])


def test_refused_when_the_trigger_attestation_row_is_missing(runner, cluster, db):
    cluster.su(db, "ALTER TABLE public.l1_data_plane_trigger_attestations DISABLE TRIGGER l1_data_plane_trigger_attestations_immutable")
    cluster.su(db, "DELETE FROM public.l1_data_plane_trigger_attestations WHERE table_name='chart_divisionals' AND trigger_name='l1_data_plane_capture'")
    cluster.su(db, "ALTER TABLE public.l1_data_plane_trigger_attestations ENABLE TRIGGER l1_data_plane_trigger_attestations_immutable")
    refusal(runner, ["pre_trigger_attestation_row_chart_divisionals"])


def test_refused_when_the_chart_vichara_trigger_attestation_row_is_missing(runner, cluster, db):
    cluster.su(db, "ALTER TABLE public.l1_data_plane_trigger_attestations DISABLE TRIGGER l1_data_plane_trigger_attestations_immutable")
    cluster.su(db, "DELETE FROM public.l1_data_plane_trigger_attestations WHERE table_name='chart_vichara' AND trigger_name='l1_data_plane_capture'")
    cluster.su(db, "ALTER TABLE public.l1_data_plane_trigger_attestations ENABLE TRIGGER l1_data_plane_trigger_attestations_immutable")
    refusal(runner, ["pre_trigger_attestation_row_chart_vichara"])


def test_refused_when_the_administrator_cannot_assume_the_owner_roles(runner, cluster, db):
    cluster.su(db, "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='plainadm') THEN CREATE ROLE plainadm LOGIN; END IF; END $$")
    before = runner.state()
    code, res = runner.run("dry-run", user="plainadm")
    assert code == 2 and "pre_admin_can_assume_the_owner_roles" in res["failed_checks"]
    assert runner.state() == before


def test_refused_while_a_build_is_in_flight_on_any_chart_or_a_generation_is_building(runner, cluster, db):
    cluster.su(db, "INSERT INTO public.build_runs(id, chart_id, state) VALUES (gen_random_uuid(), '1c826d5a-41cb-4450-b4dc-59d440e5f75a', 'running')")
    refusal(runner, ["pre_no_build_in_flight"])
    cluster.su(db, "DELETE FROM public.build_runs")


def test_refused_while_a_builder_session_is_active_and_warned_when_it_is_hidden(runner, cluster, db):
    with cluster.conn(db, user="data_plane_builder") as busy:
        busy.execute("SELECT 1")                                   # idle in transaction
        if cluster.major <= 15:
            # a non-superuser administrator without pg_read_all_stats cannot see the state: a warning, build_runs is then the only guard
            code, res = runner.run("dry-run")
            assert code == 0 and "hidden state" in "\n".join(res["log"])
            cluster.su("postgres", "GRANT pg_read_all_stats TO adm")
        try:
            refusal(runner, ["pre_no_builder_session"])
        finally:
            if cluster.major <= 15:
                cluster.su("postgres", "REVOKE pg_read_all_stats FROM adm")


def test_refused_without_the_writer_first_proof(runner, mod):
    res = runner.execute(runner.args("apply", expect_evidence="0" * 64), runner=cf.writer_runner(mod, tag="e" * 40))[1]
    assert "pre_writer_first" in res["failed_checks"]
    res = runner.execute(runner.args("dry-run", writer_commit=None))[1]            # a dry run may omit it (printed NOT CHECKED)
    assert res["status"] == "DRY_RUN_ROLLED_BACK_ALL_CHECKS_HOLD"
    assert "NOT CHECKED" in "\n".join(res["log"])


def test_refused_when_the_deploy_gate_is_already_red(runner, cluster, db):
    cluster.su(db, "ALTER TABLE public.l1_data_plane_trigger_attestations DISABLE TRIGGER l1_data_plane_trigger_attestations_immutable")
    cluster.su(db, "UPDATE public.l1_data_plane_trigger_attestations SET definition_digest=repeat('0',64) WHERE trigger_name='l1_data_plane_mutation_guard' AND table_name='chart_facts'")
    cluster.su(db, "ALTER TABLE public.l1_data_plane_trigger_attestations ENABLE TRIGGER l1_data_plane_trigger_attestations_immutable")
    res = runner.run("dry-run")[1]
    assert "pre_deploy_gate_green" in res["failed_checks"]


def test_refused_when_the_comments_are_not_the_pre_state(runner, cluster, db):
    cluster.su(db, "COMMENT ON COLUMN public.l1_data_plane_fact_snapshots.value_num IS 'someone documented it first'")
    refusal(runner, ["pre_comments_are_the_pre_state"])


# ---------------------------------------------------------------------------------------------- verification SQL, probes
def test_verify_sql_passes_before_and_after_and_is_read_only(runner, cluster, db):
    rows = only_known_failures(reader_rows(cluster, db, "verify_before_apply.sql"))
    assert rows["11"][-1] == "PASS" and rows["12"][-1] == "PASS" and rows["17"][-1] == "PASS" and rows["20"][-1] == "PASS" and rows["21"][-1] == "PASS"
    runner.run("apply")
    rows = only_known_failures(reader_rows(cluster, db, "verify_after_apply.sql"))
    assert all(rows[k][-1] == "PASS" for k in ("11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "30"))
    # a reader cannot write anything with it: the script is a single SELECT (no DML/DDL keyword at statement start)
    for f in ("verify_before_apply.sql", "verify_after_apply.sql"):
        text = "\n".join(l for l in (EXEC_DIR / f).read_text().splitlines() if not l.strip().startswith("--"))
        assert not re.search(r"(?im)^\s*(insert|update|delete|alter|create|drop|grant|revoke|truncate|comment)\b", text)


def test_verify_sql_fails_on_the_wrong_state(runner, cluster, db):
    rows = {r[0]: r for r in reader_rows(cluster, db, "verify_after_apply.sql")}          # the AFTER script on the pre-state
    assert rows["11"][-1] == "FAIL" and rows["16"][-1] == "FAIL" and rows["999"][-1] == "FAIL"


# ------------------------------------------------------------------------------------- change accounting and the post-apply gate
def _images(mod, wrong=False, extra=False, wrong_trigger_table=False, extra_attestation_table=False):
    """Crafted before/after catalog snapshots for the pure accounting function: the planned change (every patched function and every trigger-change table
    changes, one entry each), optionally the WRONG function changed in place of one patched function (the counts still say N), an UNPLANNED extra function,
    a trigger / attestation row of the WRONG table changed in place of a planned table's, or an extra table's attestation row changed as well."""
    sigs = [p.signature for p in mod.FUNCTION_PATCHES]
    tabs = [c.table for c in mod.TRIGGER_CHANGES]
    other, other_tab = "l1_data_plane_fact_unit(text,text,jsonb)", "chart_facts"
    before = {"index": {("i", "old")}, "trigger": {(t, "tr", "def0", "O") for t in tabs} | {(other_tab, "tr", "def0", "O")},
              "trigger_attestation": {(t, "tr", "d0") for t in tabs} | {(other_tab, "tr", "d0")},
              "function": {(s, "m0") for s in sigs} | {(other, "u0")}, "function_attestation": {(s, "d0") for s in sigs}}
    after = {"index": {("i", "new")}, "trigger": {(t, "tr", "def1", "O") for t in tabs} | {(other_tab, "tr", "def0", "O")},
             "trigger_attestation": {(t, "tr", "d1") for t in tabs} | {(other_tab, "tr", "d0")},
             "function": {(s, "m1") for s in sigs} | {(other, "u0")}, "function_attestation": {(s, "d1") for s in sigs}}
    if wrong:                                   # one patched function untouched, an UNPLANNED one changed in its place: counts equal, identities differ
        after["function"] = {(s, "m1") for s in sigs[:-1]} | {(sigs[-1], "m0"), (other, "u1")}
    if extra:                                   # every patched function changed AND an unplanned one
        after["function"] = {(s, "m1") for s in sigs} | {(other, "u1")}
    if wrong_trigger_table:                     # the last planned table's trigger and attestation untouched, another table's changed in its place
        after["trigger"] = {(t, "tr", "def1", "O") for t in tabs[:-1]} | {(tabs[-1], "tr", "def0", "O"), (other_tab, "tr", "def1", "O")}
        after["trigger_attestation"] = {(t, "tr", "d1") for t in tabs[:-1]} | {(tabs[-1], "tr", "d0"), (other_tab, "tr", "d1")}
    if extra_attestation_table:                 # the planned tables AND one more table's attestation row
        after["trigger_attestation"] = {(t, "tr", "d1") for t in tabs} | {(other_tab, "tr", "d1")}
    return before, after


def acct(mod, **kw):
    b, a = _images(mod, **kw)
    return {n: ok for n, ok, _ in mod.change_accounting(mod.forward_leg(), b, a)}


def test_change_accounting_passes_the_planned_change_and_only_it(mod):
    assert all(acct(mod).values()), acct(mod)


def test_change_accounting_refuses_the_wrong_function_even_when_the_counts_say_one(mod):
    r = acct(mod, wrong=True)
    assert r["post_exactly_%d_function_entries_changed" % len(mod.FUNCTION_PATCHES)] is True               # the counts alone are satisfied...
    assert r["post_changed_functions_are_exactly_the_patched_ones"] is False  # ...the identity check is what refuses


def test_change_accounting_refuses_an_unplanned_second_function_change_by_count(mod):
    r = acct(mod, extra=True)
    assert r["post_exactly_%d_function_entries_changed" % len(mod.FUNCTION_PATCHES)] is False and r["post_changed_functions_are_exactly_the_patched_ones"] is False


def test_the_post_apply_gate_going_red_refuses_the_commit_and_changes_nothing(runner, mod, monkeypatch):
    pre = runner.state()
    _, dry = runner.execute(runner.args("dry-run"))
    real = mod.fa2.gate_mirror
    calls = []

    def red_after(cur, tables):
        g = real(cur, tables)
        calls.append(1)
        return dict(g, function_digests_unsafe=True) if len(calls) >= 2 else g          # the AFTER image only
    monkeypatch.setattr(mod.fa2, "gate_mirror", red_after)
    code, res = runner.execute(runner.args("apply", expect_evidence=dry["evidence_digest"]))
    assert code == 1 and "post_deploy_gate_green" in res["failed_checks"]
    assert runner.state() == pre


def test_change_accounting_refuses_a_trigger_or_attestation_change_of_the_wrong_table_even_when_the_counts_say_n(mod):
    n = len(mod.TRIGGER_CHANGES)
    r = acct(mod, wrong_trigger_table=True)
    assert r[f"post_exactly_{n}_trigger_entries_changed"] is True and r[f"post_exactly_{n}_trigger_attestation_entries_changed"] is True
    assert r["post_changed_triggers_are_exactly_the_planned_tables"] is False
    assert r["post_changed_trigger_attestations_are_exactly_the_planned_tables"] is False


def test_change_accounting_refuses_an_extra_tables_trigger_attestation_row(mod):
    n = len(mod.TRIGGER_CHANGES)
    r = acct(mod, extra_attestation_table=True)
    assert r[f"post_exactly_{n}_trigger_attestation_entries_changed"] is False                 # n+1 rows changed
    assert r["post_changed_trigger_attestations_are_exactly_the_planned_tables"] is False      # and the identity check says which table is extra
    assert acct(mod)["post_changed_trigger_attestations_are_exactly_the_planned_tables"] is True
