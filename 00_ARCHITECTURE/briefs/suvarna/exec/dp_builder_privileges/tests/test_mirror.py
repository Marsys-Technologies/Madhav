"""Mirror tests: the executor against a disposable PostgreSQL 15 whose schema, owners and ACLs are production's (marker `mirror`; see conftest.py).

The administrator is NOT a superuser (CREATEROLE only, like production's `postgres`); the superuser connection is used only to reset the database and to read
facts. Every test starts from, and returns to, the production pre-state (fixture `db`)."""
from __future__ import annotations

import json
import os
import pathlib
import sys
import uuid

import psycopg
import pytest

from conftest import ADMIN, BUILDER, SUPER, mirror, run_mode, Args

pytestmark = mirror

CHART = "11111111-1111-4111-8111-111111111111"


def state(ex):
    """Everything the plan may or may not change, read as the superuser."""
    with psycopg.connect(SUPER) as c:
        cur = c.cursor()
        out = {}
        cur.execute(f"SELECT md5(pg_get_functiondef('public.{ex.BIND_PATCH.signature}'::regprocedure))")
        out["bind_md5"] = cur.fetchone()[0]
        cur.execute(f"SELECT definition_digest FROM {ex.FN_ATT} WHERE function_signature=%s", (ex.BIND_PATCH.signature,))
        out["attestation"] = cur.fetchone()[0]
        out.update({k: v for k, v in ex.snap(cur).items()})
        c.rollback()
    return out


def builder_can_execute(ex):
    with psycopg.connect(SUPER) as c:
        cur = c.cursor()
        res = {}
        for sig, _ in ex.IDENTITY_FUNCTIONS:
            cur.execute("SELECT has_function_privilege(%s, %s, 'EXECUTE')", (ex.BUILDER, "public." + sig))
            res[sig] = cur.fetchone()[0]
        return res


def test_the_administrator_is_a_non_superuser_with_createrole_and_pg_monitor(db):
    with psycopg.connect(ADMIN) as c:
        row = c.execute("SELECT rolsuper, rolcreaterole, session_user, pg_has_role(session_user, 'pg_read_all_stats', 'MEMBER') FROM pg_roles WHERE rolname=session_user").fetchone()
    assert row[0] is False and row[1] is True and row[3] is True, "the mirror administrator mirrors production postgres (CREATEROLE, pg_monitor)"


def test_count_is_read_only_and_ok(ex, db, evidence):
    before = state(ex)
    code, res = run_mode(ex, "count")
    assert code == 0 and res["status"] == "COUNT_READ_ONLY_OK" and res["failed_checks"] == [], res["details"]
    assert state(ex) == before


def test_dry_run_holds_every_check_and_changes_nothing(ex, db, evidence):
    before = state(ex)
    code, res = run_mode(ex, "dry-run")
    assert code == 0 and res["status"] == "DRY_RUN_ROLLED_BACK_ALL_CHECKS_HOLD" and res["failed_checks"] == [], res["details"]
    assert state(ex) == before
    outs = list(evidence.glob("dry-run_*/outcome.json"))
    body = json.loads(outs[0].read_text())
    assert body["status"] == "dry_run" and body["evidence_digest"] == res["evidence_digest"]
    assert all(k in body for k in ex.RUNTIME_KEYS)
    names = set(res["checks"])
    for must in ("post_asserting_privilege_checks_hold", "post_no_other_role_gains_execute_on_any_identity_function", "post_grant_probe_no_other_role_can_select",
                 "post_exactly_1_function_attestation_row_changed", "post_deploy_gate_green", "post_membership_equals_pre_state_after_revoke",
                 "pre_admin_can_see_all_sessions", "pre_id8_signal_ns_body_is_the_bound_body", "post_identity_function_bodies_unchanged"):
        assert must in names and res["checks"][must] is True, must
    assert "post_membership_identical" not in names, "LOW-2: the vacuous membership check is gone"
    assert any(l.startswith("administrator is a member of pg_read_all_stats") for l in res["log"]), "the dry run prints the pg_monitor fact"
    assert any(l.startswith("target: current_user=") and "superuser=False" in l for l in res["log"]), "the dry run prints the connection facts"


def test_apply_commits_exactly_the_planned_change(ex, db, evidence):
    before = state(ex)
    code, dry = run_mode(ex, "dry-run")
    assert code == 0
    code, res = run_mode(ex, "apply", expect_evidence=dry["evidence_digest"])
    assert code == 0 and res["status"] == "COMMITTED" and res["failed_checks"] == [], res["details"]
    after = state(ex)
    p = ex.BIND_PATCH
    assert after["bind_md5"] == p.patched_md5 and after["attestation"] == p.patched_sha256
    assert all(builder_can_execute(ex).values())
    assert after["membership"] == before["membership"], "the administrator's transient membership was revoked"
    for key in ("other_function_acl", "acl", "rls", "policy", "immutable_triggers"):
        assert after[key] == before[key], key
    assert {r[0] for r in before["function"] - after["function"]} == {p.signature}
    gained = {(r[0], r[1]) for r in after["execute_pairs"] - before["execute_pairs"]}
    assert {r for r, _ in gained} == {ex.BUILDER} and len(gained) == 8 and not (before["execute_pairs"] - after["execute_pairs"])
    # the gate stays green on the committed state
    with psycopg.connect(SUPER) as c:
        cur = c.cursor()
        assert ex.gate_red(ex.gate_mirror(cur)) == []
    outs = [json.loads(p_.read_text()) for p_ in evidence.glob("apply_*/outcome.json")]
    assert outs and outs[0]["status"] == "applied"


def test_apply_is_refused_when_the_evidence_digest_differs_and_nothing_changes(ex, db, evidence):
    before = state(ex)
    code, res = run_mode(ex, "apply", expect_evidence="0" * 64)
    assert code == 1 and res["status"] == "REFUSED_ROLLED_BACK" and "evidence_digest_matches_expected" in res["failed_checks"]
    assert state(ex) == before


def test_a_precondition_failure_changes_nothing(ex, db, evidence):
    run = str(uuid.uuid4())
    with psycopg.connect(SUPER, autocommit=True) as c:
        c.execute("INSERT INTO build_runs(id,chart_id,scope,action,state,plan,triggered_by) VALUES (%s,%s,'asset','build','running','{}','test')", (run, CHART))
    try:
        before = state(ex)
        code, res = run_mode(ex, "dry-run")
        assert code == 2 and "pre_no_build_in_flight" in res["failed_checks"]
        assert state(ex) == before
    finally:
        with psycopg.connect(SUPER, autocommit=True) as c:
            c.execute("UPDATE build_runs SET state='completed' WHERE id=%s", (run,))


def test_a_second_apply_is_refused_because_the_live_body_is_no_longer_the_bound_one(ex, db, evidence):
    code, dry = run_mode(ex, "dry-run")
    code, res = run_mode(ex, "apply", expect_evidence=dry["evidence_digest"])
    assert code == 0
    code, res2 = run_mode(ex, "dry-run")
    assert code == 2 and "pre_bind_body_is_the_bound_body" in res2["failed_checks"]


def test_the_asserting_post_check_raises_and_the_transaction_is_rolled_back(ex, db, evidence, monkeypatch):
    """Mutation of the PLAN (one identity function is left un-granted): the DO-block assertion RAISES inside the transaction; nothing is committed."""
    real = ex.grant_stmt
    first = ex.IDENTITY_FUNCTIONS[0][0]
    monkeypatch.setattr(ex, "grant_stmt", lambda sig, revoke: "SELECT 1" if sig == first and not revoke else real(sig, revoke))
    before = state(ex)
    code, res = run_mode(ex, "dry-run")
    assert code == 2 and "post_asserting_privilege_checks_hold" in res["failed_checks"]
    assert state(ex) == before


def test_a_red_deploy_gate_after_the_plan_blocks_the_commit(ex, db, evidence, monkeypatch):
    real = ex.gate_mirror
    calls = []

    def gate(cur, tables=None):
        out = real(cur, tables)
        calls.append(1)
        if len(calls) >= 2:
            out = dict(out, function_digests_unsafe=True)
        return out
    monkeypatch.setattr(ex, "gate_mirror", gate)
    before = state(ex)
    code, res = run_mode(ex, "dry-run")
    assert code == 2 and "post_deploy_gate_green" in res["failed_checks"]
    assert state(ex) == before


def test_granting_any_other_role_is_caught_by_the_no_other_role_check(ex, db, evidence, monkeypatch):
    real = ex.grant_stmt
    first = ex.IDENTITY_FUNCTIONS[0][0]
    monkeypatch.setattr(ex, "grant_stmt", lambda sig, revoke: real(sig, revoke) + (", data_plane_verifier" if sig == first and not revoke else ""))
    before = state(ex)
    code, res = run_mode(ex, "dry-run")
    assert code == 2 and "post_no_other_role_gains_execute_on_any_identity_function" in res["failed_checks"]
    assert state(ex) == before


def test_rollback_restores_the_pre_state_exactly(ex, db, evidence):
    before = state(ex)
    code, dry = run_mode(ex, "dry-run")
    code, res = run_mode(ex, "apply", expect_evidence=dry["evidence_digest"])
    assert code == 0
    applied = state(ex)
    assert applied["bind_md5"] != before["bind_md5"]
    code, rdry = run_mode(ex, "rollback-dry-run")
    assert code == 0 and rdry["failed_checks"] == [], rdry["details"]
    assert state(ex) == applied, "the rollback dry run changed nothing"
    code, rres = run_mode(ex, "rollback", expect_evidence=rdry["evidence_digest"])
    assert code == 0 and rres["status"] == "COMMITTED", rres["details"]
    restored = state(ex)
    for key in ("bind_md5", "attestation", "function", "function_attestation", "identity", "acl", "other_function_acl", "membership", "execute_pairs"):
        assert restored[key] == before[key], key
    assert not any(builder_can_execute(ex).values())


def test_rollback_is_refused_before_the_forward_change(ex, db, evidence):
    code, rdry = run_mode(ex, "rollback-dry-run")
    assert code == 2 and "pre_bind_body_is_the_bound_body" in rdry["failed_checks"]


@pytest.mark.skipif(not os.environ.get("DPBP_SIDECAR_PATH"), reason="DPBP_SIDECAR_PATH (a python-sidecar checkout with PR #3008 and #3029) not provided")
def test_end_to_end_bo_sudarshana_runs_as_the_builder_after_apply_and_no_other_role_reads_the_shadows(ex, db, evidence):
    """The point of 1272 + 1273: before the change the first adapter read fails with permission denied; after it the adapter runs end to end through the real
    asset_runner._run_data_writer as data_plane_builder (no superuser), the integrity check reads the real table, and the shadows are readable by the builder only."""
    sys.path.insert(0, os.environ["DPBP_SIDECAR_PATH"])
    os.environ.setdefault("SE_EPHE_PATH", "/Users/Dev/suvarna-evidence/Se1")
    os.environ["DATABASE_URL"] = BUILDER
    from pipeline.orchestrator.db import connect
    from pipeline.orchestrator import asset_runner as ar
    from pipeline.orchestrator.writers import ContextSpec, discover_all, get_writer

    def attempt():
        conn = connect()
        conn.autocommit = False
        cur = conn.cursor()
        run = str(uuid.uuid4())
        cur.execute("INSERT INTO build_runs(id,chart_id,scope,action,state,plan,triggered_by) VALUES(%s,%s,'asset','build','running','{}','test')", (run, CHART))
        cur.execute("INSERT INTO build_run_assets(run_id,asset_id,position,state) VALUES(%s,'bo_sudarshana',1,'building')", (run,))
        conn.commit()
        discover_all()
        w = get_writer("bo_sudarshana")()
        ctx = ContextSpec(asset_id="bo_sudarshana", build_id=run, db_conn=conn, config={"chart_id": uuid.UUID(CHART), "birth_params": {}})
        try:
            res = w.run(ctx)
            conn.rollback()
            return res, None
        except Exception as exc:
            conn.rollback()
            return None, exc
        finally:
            c2 = connect()
            c2.autocommit = True
            c2.execute("UPDATE build_run_assets SET state='complete' WHERE run_id=%s", (run,))
            c2.execute("UPDATE build_runs SET state='completed' WHERE id=%s", (run,))

    res, exc = attempt()
    assert res is None and "permission denied" in str(exc), exc                      # before: the defect
    code, dry = run_mode(ex, "dry-run")
    code, applied = run_mode(ex, "apply", expect_evidence=dry["evidence_digest"])
    assert code == 0
    res, exc = attempt()
    assert exc is None and res.rows_inserted == 45 and "l2_generation=" in res.notes, exc                     # after: the adapter runs
    # the shadows: owner + builder only
    conn = connect()
    conn.autocommit = False
    cur = conn.cursor()
    run = str(uuid.uuid4())
    cur.execute("INSERT INTO build_runs(id,chart_id,scope,action,state,plan,triggered_by) VALUES(%s,%s,'asset','build','running','{}','test')", (run, CHART))
    cur.execute("INSERT INTO build_run_assets(run_id,asset_id,position,state) VALUES(%s,'bo_sudarshana',1,'building')", (run,))
    cur.execute("SELECT generation_id, semantic_output_digest FROM l1_data_plane_generations g JOIN l1_data_plane_generation_heads h ON h.chart_id=g.chart_id AND h.asset_id=g.asset_id "
                "AND h.current_generation_id=g.generation_id WHERE g.chart_id=%s AND g.asset_id='ga_positions'", (CHART,))
    gen = cur.fetchone()
    vector = json.dumps([{"layer": "L1", "asset_id": "ga_positions", "generation_id": gen["generation_id"], "semantic_output_digest": gen["semantic_output_digest"]}])
    cur.execute("SELECT public.bind_l2_exact_inputs(%s::uuid, %s::jsonb)", (CHART, vector))
    cur.execute("SELECT c.relname, pg_get_userbyid(c.relowner) AS owner, c.relacl::text AS acl FROM pg_class c WHERE c.relnamespace = pg_my_temp_schema() AND c.relkind='r' ORDER BY 1")
    shadows = cur.fetchall()
    assert shadows and all(s["acl"] and ex.BUILDER in s["acl"] for s in shadows if s["relname"] != "l2_data_plane_bind_receipt")
    receipt = [s for s in shadows if s["relname"] == "l2_data_plane_bind_receipt"][0]
    assert not receipt["acl"] or ex.BUILDER not in receipt["acl"], "the bind receipt is not granted"
    for s in shadows:
        if s["relname"] == "l2_data_plane_bind_receipt":
            continue
        grantees = {item.split("=")[0] for item in ex.acl_set(s["acl"])}
        assert grantees == {ex.OWNER_L2, ex.BUILDER}, (s["relname"], grantees)
        cur.execute("SELECT r.rolname FROM pg_roles r WHERE r.rolname NOT LIKE 'pg\\_%%' AND r.rolname NOT IN (%s,%s) AND has_table_privilege(r.oid, to_regclass(%s), 'SELECT')",
                    (ex.OWNER_L2, ex.BUILDER, "pg_temp." + s["relname"]))
        others = [r["rolname"] for r in cur.fetchall()]
        assert others == [] or all(r in ("postgres",) for r in others), (s["relname"], others)      # the container superuser; no production role
    conn.rollback()
    c3 = connect()
    c3.autocommit = True
    c3.execute("UPDATE build_run_assets SET state='complete' WHERE run_id=%s", (run,))
    c3.execute("UPDATE build_runs SET state='completed' WHERE id=%s", (run,))
