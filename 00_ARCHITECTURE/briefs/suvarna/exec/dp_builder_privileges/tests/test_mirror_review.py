"""Mirror tests added after the independent review of PR #3045 (MED-1, LOW-1, LOW-4, NIT-1, NIT-3): each proves a check that cannot be read off the code alone.
Environment as in conftest.py. Every test starts from, and returns to, the production pre-state (fixture `db`)."""
from __future__ import annotations

import json
import os
import uuid

import psycopg
import pytest

from conftest import ADMIN, BUILDER, SUPER, admin_user, mirror, mirror_target, run_mode

pytestmark = mirror

CHART = "11111111-1111-4111-8111-111111111111"


def state_md5(ex):
    with psycopg.connect(SUPER) as c:
        return c.execute(f"select md5(pg_get_functiondef('public.{ex.BIND_PATCH.signature}'::regprocedure))").fetchone()[0]


# ---------------------------------------------------------------------------------------------------------------- MED-1
def test_an_administrator_who_cannot_see_other_sessions_fails_closed_not_silently(ex, db, evidence):
    with psycopg.connect(SUPER, autocommit=True) as c:
        c.execute(f"REVOKE pg_monitor FROM {admin_user()}")
    before = state_md5(ex)
    code, res = run_mode(ex, "dry-run")
    assert code == 2 and "pre_admin_can_see_all_sessions" in res["failed_checks"], res["failed_checks"]
    assert any("is NOT a member of pg_read_all_stats" in l for l in res["log"]), "the refusal says why"
    assert state_md5(ex) == before


def test_a_builder_session_idle_in_transaction_blocks_and_is_seen(ex, db, evidence):
    with psycopg.connect(BUILDER) as b:
        b.execute("SELECT 1")                       # leaves an open transaction (idle in transaction)
        code, res = run_mode(ex, "dry-run")
    assert code == 2 and "pre_no_builder_session" in res["failed_checks"], res["failed_checks"]
    assert "pre_admin_can_see_all_sessions" not in res["failed_checks"]


# ---------------------------------------------------------------------------------------------------------------- NIT-1
def test_a_building_l1_generation_blocks(ex, db, evidence):
    with psycopg.connect(SUPER, autocommit=True) as c:
        c.execute("set session_replication_role=replica")
        c.execute("insert into l1_data_plane_generations(chart_id,asset_id,generation_id,contract_version,l0_semantic_release_id,l0_semantic_release_digest,l0_config_generation_id,"
                  "l0_config_digest,base_context_jsonb,expected_partitions,completed_partitions,status,opened_at) "
                  "select chart_id,asset_id,'99999999-9999-4999-8999-999999999999',contract_version,l0_semantic_release_id,l0_semantic_release_digest,l0_config_generation_id,"
                  "l0_config_digest,base_context_jsonb,expected_partitions,0,'building',now() from l1_data_plane_generations limit 1")
    try:
        code, res = run_mode(ex, "dry-run")
        assert code == 2 and "pre_no_building_generation" in res["failed_checks"], res["failed_checks"]
    finally:
        with psycopg.connect(SUPER, autocommit=True) as c:
            c.execute("set session_replication_role=replica")
            c.execute("delete from l1_data_plane_generations where generation_id='99999999-9999-4999-8999-999999999999'")


def test_an_identity_function_that_is_not_as_bound_blocks_owner_and_body(ex, db, evidence):
    sig = "bodha_signal_identity_namespace()"
    with psycopg.connect(SUPER, autocommit=True) as c:
        original = c.execute(f"select pg_get_functiondef('public.{sig}'::regprocedure)").fetchone()[0]
    try:
        with psycopg.connect(SUPER, autocommit=True) as c:
            c.execute(f"ALTER FUNCTION public.{sig} SECURITY DEFINER")           # owner/secdef/config precondition
        code, res = run_mode(ex, "dry-run")
        assert code == 2 and "pre_id8_signal_ns_owner_secdef_config" in res["failed_checks"], res["failed_checks"]
        with psycopg.connect(SUPER, autocommit=True) as c:
            c.execute(f"ALTER FUNCTION public.{sig} SECURITY INVOKER")
            head, _, tail = original.rpartition("$function$")                     # NIT-2: a changed body, same owner/secdef/config/ACL
            c.execute(head + "-- tampered\n$function$" + tail)
        code, res = run_mode(ex, "dry-run")
        assert code == 2 and "pre_id8_signal_ns_body_is_the_bound_body" in res["failed_checks"], res["failed_checks"]
    finally:
        with psycopg.connect(SUPER, autocommit=True) as c:
            c.execute(f"ALTER FUNCTION public.{sig} SECURITY INVOKER")
            c.execute(original)


def test_the_interpreter_is_bound_into_the_evidence_digest(ex, db, evidence, monkeypatch):
    code, a = run_mode(ex, "dry-run")
    real = ex.runtime_record
    monkeypatch.setattr(ex, "runtime_record", lambda: dict(real(), python_version="9.9.9 other interpreter"))
    code2, b = run_mode(ex, "dry-run")
    assert code == code2 == 0 and a["evidence_digest"] != b["evidence_digest"], "same state, different interpreter: a different digest, so an apply under it is refused"


# ---------------------------------------------------------------------------------------------------------------- LOW-1
@pytest.mark.parametrize("label,make_target", [
    ("a superuser connection, expected name accepted", lambda ex: ex.Target(user=_super_name(), database=mirror_target(ex).database, server_major=15)),
    ("the wrong administrator name", lambda ex: mirror_target(ex, user="somebody_else")),
    ("the wrong database", lambda ex: mirror_target(ex, database="amjis")),
    ("the wrong server major version", lambda ex: mirror_target(ex, server_major=16)),
])
def test_the_wrong_target_is_refused_first_with_its_own_exit_code(ex, db, evidence, label, make_target):
    before = state_md5(ex)
    connect = (lambda: psycopg.connect(SUPER)) if label.startswith("a superuser") else None
    with pytest.raises(SystemExit) as e:
        run_mode(ex, "dry-run", connect=connect, target=make_target(ex))
    assert e.value.code == ex.EXIT_WRONG_TARGET == 94
    outs = [json.loads(p.read_text()) for p in evidence.glob("dry-run_*/outcome.json")]
    assert outs and outs[0]["status"] == "failed" and "connected_to_the_wrong_target" in json.dumps(outs[0]), outs
    assert state_md5(ex) == before


def _super_name():
    with psycopg.connect(SUPER) as c:
        return c.execute("select current_user").fetchone()[0]


def test_a_superuser_connection_is_refused_even_when_it_carries_the_expected_name(ex, db, evidence):
    """The names match (target user = the superuser's own name); the superuser flag alone refuses it."""
    with pytest.raises(SystemExit) as e:
        run_mode(ex, "dry-run", connect=lambda: psycopg.connect(SUPER), target=ex.Target(user=_super_name(), database=mirror_target(ex).database, server_major=15))
    assert e.value.code == 94


# ---------------------------------------------------------------------------------------------------------------- NIT-3
class _CommitRaisesBefore:
    def __init__(self, c): self.c = c
    def __getattr__(self, n): return getattr(self.c, n)

    def commit(self):
        self.c.rollback()
        raise psycopg.OperationalError("simulated connection loss at commit")


class _CommitRaisesAfter:
    def __init__(self, c): self.c = c
    def __getattr__(self, n): return getattr(self.c, n)

    def commit(self):
        self.c.commit()
        raise psycopg.OperationalError("simulated connection loss after commit")


@pytest.mark.parametrize("wrapper,committed", [(_CommitRaisesBefore, False), (_CommitRaisesAfter, True)])
def test_commit_state_unknown_is_recorded_and_has_its_own_exception(ex, db, evidence, wrapper, committed):
    code, dry = run_mode(ex, "dry-run")
    with pytest.raises(ex.CommitStateUnknown) as e:
        run_mode(ex, "apply", expect_evidence=dry["evidence_digest"], connect=lambda: wrapper(psycopg.connect(ADMIN)))
    assert e.value.exc_name == "OperationalError"
    outs = [json.loads(p.read_text()) for p in evidence.glob("apply_*/outcome.json")]
    assert outs and outs[0]["status"] == "commit_state_unknown", outs
    assert (state_md5(ex) == ex.BIND_PATCH.patched_md5) is committed


# ---------------------------------------------------------------------------------------------------------------- LOW-4
def test_the_grant_covers_exactly_the_shadows_this_call_created_never_a_pre_existing_temp_table(ex, db, evidence):
    code, dry = run_mode(ex, "dry-run")
    code, applied = run_mode(ex, "apply", expect_evidence=dry["evidence_digest"])
    assert code == 0
    with psycopg.connect(SUPER) as c:
        cur = c.cursor()
        # owner-owned temp tables that exist BEFORE the bind (as l2_data_plane_msr_delete_receipt does after assert_l2_msr_delete_safe)
        for name in ("l2_data_plane_msr_delete_receipt", "zz_other_owner_owned"):
            cur.execute(f"CREATE TEMP TABLE {name} (x integer)")
            cur.execute(f"ALTER TABLE pg_temp.{name} OWNER TO {ex.OWNER_L2}")
        cur.execute("SELECT g.generation_id, g.semantic_output_digest FROM l1_data_plane_generations g JOIN l1_data_plane_generation_heads h ON h.chart_id=g.chart_id "
                    "AND h.asset_id=g.asset_id AND h.current_generation_id=g.generation_id WHERE g.chart_id=%s AND g.asset_id='ga_positions'", (CHART,))
        gen = cur.fetchone()
        if gen is None:
            pytest.skip("the mirror has no ga_positions head")
        vector = json.dumps([{"layer": "L1", "asset_id": "ga_positions", "generation_id": gen[0], "semantic_output_digest": gen[1]}])
        cur.execute(f"SET SESSION AUTHORIZATION {ex.BUILDER}")                  # session_user = data_plane_builder: what the function requires
        cur.execute("SELECT public.bind_l2_exact_inputs(%s::uuid, %s::jsonb)", (CHART, vector))
        cur.execute("RESET SESSION AUTHORIZATION")
        cur.execute("SELECT c.relname, COALESCE(c.relacl::text,'') FROM pg_class c WHERE c.relnamespace = pg_my_temp_schema() AND c.relkind='r' ORDER BY 1")
        acls = dict(cur.fetchall())
        c.rollback()
    assert "chart_facts" in acls and ex.BUILDER in acls["chart_facts"], "a shadow this call created IS granted"
    for pre in ("l2_data_plane_msr_delete_receipt", "zz_other_owner_owned"):
        assert ex.BUILDER not in acls[pre], f"{pre} existed before the bind and must NOT be granted ({acls[pre]!r})"
    assert ex.BUILDER not in acls["l2_data_plane_bind_receipt"], "the bind receipt is not granted"


# ---------------------------------------------------------------------------------------------------------------- detectors that need their own failing case
def test_a_grant_that_also_changes_an_identity_function_body_is_caught(ex, db, evidence, monkeypatch):
    real = ex.grant_stmt
    first = ex.IDENTITY_FUNCTIONS[0][0]
    monkeypatch.setattr(ex, "grant_stmt", lambda sig, revoke: real(sig, revoke) + (f"; ALTER FUNCTION public.{sig} SET search_path = public" if sig == first and not revoke else ""))
    before = state_md5(ex)
    code, res = run_mode(ex, "dry-run")
    assert code == 2 and "post_identity_function_bodies_unchanged" in res["failed_checks"], res["failed_checks"]
    assert state_md5(ex) == before


def test_losing_a_pre_existing_membership_is_caught_by_the_membership_comparison(ex, db, evidence, monkeypatch):
    """The administrator is ALREADY a member of the owner role (granted beforehand); the executor is made to believe it is not, so it would grant and then REVOKE
    that membership: the net membership differs from the pre-state and the check that compares it must fail."""
    with psycopg.connect(SUPER, autocommit=True) as c:
        c.execute(f"GRANT {ex.OWNER_L2} TO {admin_user()}")
    try:
        real = ex.is_member
        monkeypatch.setattr(ex, "is_member", lambda cur, role: False if role == ex.OWNER_L2 else real(cur, role))
        code, res = run_mode(ex, "dry-run")
        assert code == 2 and "post_membership_equals_pre_state_after_revoke" in res["failed_checks"], res["failed_checks"]
    finally:
        with psycopg.connect(SUPER, autocommit=True) as c:
            c.execute(f"REVOKE {ex.OWNER_L2} FROM {admin_user()}")
