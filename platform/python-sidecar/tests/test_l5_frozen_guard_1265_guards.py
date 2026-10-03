"""1265 frozen-history guards: BEHAVIOUR tier on a disposable PostgreSQL with production's role set (see l5_frozen_guard_world.py).

Applies the REAL package SQL (sql/1265_l5_frozen_row_guards.sql) exactly as the executor does: as amjis_app inside a transient CREATE capability on
schema public. Every refusal assertion runs as a role that HOLDS the privilege the statement needs and requires the guard's own message prefix, so a
refusal can only be the guard. The executor route (plan hash, dry run, apply, rollback leg) is test_l5_frozen_guard_1265_executor.py.

THE CHART-DELETE FIXTURE (SS N-108) is `cascaded` below: the four tables with chart_id -> charts(id) ON DELETE CASCADE (what migration 1275 adds), the
guards applied, three charts with rows in every table. The 1275 worker can reuse it: `from tests.l5_frozen_guard_world import add_chart_fks, make_world`.
"""
from __future__ import annotations

import hashlib
import re

import pytest

from tests.l5_frozen_guard_world import (CASCADE_TABLES, CHART_A, CHART_B, CHART_C, FORWARD, RUN_1, RUN_2, ROLLBACK, World, add_chart_fks,
                                         body, drop_world, make_world, pg_cluster, pred_row, pros_row)  # noqa: F401  (pg_cluster is a fixture)

REAL = FORWARD.read_text(encoding="utf8")
P_PRED, P_PRO, P_MAN, P_BMPL, P_BUILDER = ("mimamsa_predictions_frozen_row_guard:", "brahma_prospective_ledger_frozen_row_guard:",
                                           "mimamsa_manifestation_sets_frozen_row_guard:", "brahma_mimamsa_prediction_ledger_delete_guard:",
                                           "mimamsa_predictions_builder_guard:")
PRO = {"i": "00000000-0000-4000-8000-0000000000a1", "pt": "00000000-0000-4000-8000-0000000000a2", "c": "00000000-0000-4000-8000-0000000000a3",
       "m": "00000000-0000-4000-8000-0000000000a4", "b": "00000000-0000-4000-8000-0000000000b1"}
EVENT = "eeeeeeee-0000-4000-8000-000000000001"
BM = {"det": "cccccccc-0000-4000-8000-000000000001", "open": "cccccccc-0000-4000-8000-000000000002",
      "dis": "cccccccc-0000-4000-8000-000000000003", "out": "cccccccc-0000-4000-8000-000000000004"}


@pytest.fixture()
def world(pg_cluster):
    w = make_world(pg_cluster)
    yield w
    drop_world(pg_cluster, w)


@pytest.fixture(scope="module")
def shared(pg_cluster):
    """Guards applied + the 1275 FKs, rows in every table. ONLY used by tests that roll back (nothing here is committed by a test)."""
    w = make_world(pg_cluster)
    w.apply_sql(REAL)
    add_chart_fks(w)
    yield w
    drop_world(pg_cluster, w)


@pytest.fixture()
def cascaded(pg_cluster):
    """A private copy of the chart-delete fixture for tests that commit."""
    w = make_world(pg_cluster)
    w.apply_sql(REAL)
    add_chart_fks(w)
    yield w
    drop_world(pg_cluster, w)


def refused(w, role, sql, params=None, prefix=None, contains=None):
    psy = w.pg["psycopg"]
    with w.connect(role) as c:
        try:
            c.execute(sql, params)
        except psy.errors.InsufficientPrivilege as e:
            c.rollback()
            msg = str(e).splitlines()[0]
            if prefix:
                assert msg.startswith(prefix), "refused, but not by the expected guard: " + msg
            else:
                assert any(msg.startswith(p) for p in (P_PRED, P_PRO, P_MAN, P_BMPL, P_BUILDER)), "refused, but not by a guard: " + msg
            if contains:
                assert contains in msg, msg
            return msg
        c.rollback()
    raise AssertionError(role + ": expected the guard to refuse: " + sql)


def passes(w, role, sql, params=None):
    with w.connect(role) as c:
        n = c.execute(sql, params).rowcount
        c.rollback()
        return n


def counts(w, chart=None):
    out = {}
    for t in CASCADE_TABLES:
        q = "SELECT count(*) FROM public." + t + (" WHERE chart_id = %s" if chart else "")
        out[t] = w.query(q, (chart,) if chart else None)[0][0]
    return out


# ================================================================ A. privilege determination (the mirrored roles, no superuser)

def test_the_routine_role_has_no_create_on_public_and_cannot_even_replace_an_existing_function(world):
    assert world.query("SELECT has_schema_privilege('amjis_app','public','CREATE'), has_schema_privilege('amjis_app','public','USAGE')") == [(False, True)]
    psy = world.pg["psycopg"]
    with world.connect("amjis_app") as c:
        with pytest.raises(psy.errors.InsufficientPrivilege, match="permission denied for schema public"):
            c.execute("CREATE OR REPLACE FUNCTION public.mimamsa_predictions_builder_guard() RETURNS trigger LANGUAGE plpgsql AS $x$ BEGIN RETURN NEW; END $x$")


def test_run_as_amjis_app_without_the_capability_it_stops_at_the_gate_naming_the_privilege_and_changes_nothing(world):
    before = world.catalog_state()
    psy = world.pg["psycopg"]
    with pytest.raises(psy.errors.RaiseException) as ei:
        world.apply_sql(REAL, window=False)
    assert "1265: missing privilege" in str(ei.value) and "no CREATE on schema public" in str(ei.value)
    assert world.catalog_state() == before


def test_without_the_gate_the_raw_statement_fails_with_permission_denied_for_schema_public(world):
    start, end = REAL.index("-- 0. GATE"), REAL.index("-- A1. CAPTURE guard")
    psy = world.pg["psycopg"]
    with pytest.raises(psy.errors.InsufficientPrivilege, match="permission denied for schema public"):
        world.apply_sql(REAL[:start] + REAL[end:], window=False)


def test_with_the_capability_it_applies_as_amjis_app_and_the_schema_acl_is_unchanged(world):
    notices = []
    world.apply_sql(REAL, notices=notices)
    assert world.schema_acl() == world.baseline_acl
    rows = world.query("SELECT proname, pg_get_userbyid(proowner), prosecdef, proacl::text FROM pg_proc WHERE proname IN "
                       "('mimamsa_predictions_builder_guard','mimamsa_predictions_frozen_row_guard','brahma_prospective_ledger_frozen_row_guard',"
                       "'mimamsa_manifestation_sets_frozen_row_guard','brahma_mimamsa_prediction_ledger_delete_guard') ORDER BY 1")
    assert [r[:3] for r in rows] == [(n, "amjis_app", False) for n in ("brahma_mimamsa_prediction_ledger_delete_guard", "brahma_prospective_ledger_frozen_row_guard",
                                                                        "mimamsa_manifestation_sets_frozen_row_guard", "mimamsa_predictions_builder_guard",
                                                                        "mimamsa_predictions_frozen_row_guard")]
    assert all(r[3] == "{amjis_app=X/amjis_app}" for r in rows)
    assert world.query("SELECT count(*) FROM pg_trigger WHERE NOT tgisinternal AND tgenabled = 'A'") == [(8,)]
    assert any("TRUNCATE branch skipped for mimamsa_predictions" in n for n in notices)


def test_the_replace_of_the_captured_builder_guard_is_a_no_op(world):
    before = world.query("SELECT md5(prosrc), length(prosrc), proacl::text, pg_get_userbyid(proowner), proconfig::text FROM pg_proc WHERE proname = 'mimamsa_predictions_builder_guard'")
    assert before[0][:2] == ("46c23854275c2712b30860a2b174adb2", 1084) and before[0][2] == "{amjis_app=X/amjis_app}"
    world.apply_sql(REAL)
    assert world.query("SELECT md5(prosrc), length(prosrc), proacl::text, pg_get_userbyid(proowner), proconfig::text FROM pg_proc WHERE proname = 'mimamsa_predictions_builder_guard'") == before


def test_a_fresh_replay_as_superuser_creates_the_captured_function_too(pg_cluster):
    w = make_world(pg_cluster, builder_guard=False, seed=False)
    try:
        w.exec("INSERT INTO brahma_event_ontology VALUES ('ec_x','interval'), ('ec_chain','chain')")
        w.apply_sql(REAL, role="postgres", window=False)
        assert w.query("SELECT md5(prosrc) FROM pg_proc WHERE proname = 'mimamsa_predictions_builder_guard'") == [("46c23854275c2712b30860a2b174adb2",)]
        assert w.query("SELECT count(*) FROM pg_trigger WHERE tgrelid = 'mimamsa_predictions'::regclass AND NOT tgisinternal") == [(3,)]
    finally:
        drop_world(pg_cluster, w)


def _state(w):
    return w.query("SELECT proname, md5(prosrc), proacl::text FROM pg_proc WHERE proname LIKE '%frozen%' OR proname LIKE '%builder_guard' OR proname LIKE '%delete_guard' ORDER BY 1") + \
        w.query("SELECT tgname, tgenabled, tgtype FROM pg_trigger WHERE NOT tgisinternal ORDER BY 1")


def test_rerun_is_idempotent_three_times_and_changes_nothing(world):
    world.apply_sql(REAL)
    state = _state(world)
    for _ in range(3):
        world.apply_sql(REAL)
    assert _state(world) == state and world.schema_acl() == world.baseline_acl


# ================================================================ B. guard behaviour, per table

FROZEN_PRED = [("chart_id", "'99999999-9999-4999-8999-999999999999'"), ("prediction_id", "'renamed'"), ("source_pramana_id", "'rewritten'"),
               ("outcome_claim", "'other claim'"), ("domain", "'health'"), ("observation_window", "'[2030-01-01,2030-02-01)'"),
               ("eval_date", "'2031-01-01'"), ("confidence_band", "'[0.1,0.2)'"), ("magnitude_expected", "'large'"),
               ("falsifier_jsonb", "'{\"k\":2}'"), ("base_rate", "0.5"), ("emitted_at", "'2020-01-01T00:00:00Z'"),
               ("driving_signals", "'[\"other\"]'"), ("frozen_bundle_hash", "'rehashed'"), ("bundle_formula_version", "'v2'"),
               ("created_at", "'2020-01-01T00:00:00Z'"), ("contact_id", "'sha256:abc'")]


@pytest.mark.parametrize("col,val", FROZEN_PRED)
@pytest.mark.parametrize("pid", ["pred_a0", "pred_conf"])
def test_predictions_every_frozen_column_is_immutable_on_pending_and_terminal_rows(shared, col, val, pid):
    for role in ("amjis_app", "role_orchestrator", "postgres"):
        msg = refused(shared, role, "UPDATE mimamsa_predictions SET " + col + " = " + val + " WHERE chart_id = %s AND prediction_id = %s", (CHART_A, pid), prefix=P_PRED)
        assert col in msg


@pytest.mark.parametrize("role", ["amjis_app", "role_orchestrator", "data_plane_builder", "postgres"])
@pytest.mark.parametrize("pid", ["pred_a0", "pred_due", "pred_conf", "pred_den", "pred_exp"])
def test_predictions_delete_is_refused_for_every_role_and_status(shared, role, pid):
    prefix = P_BUILDER if role == "data_plane_builder" and pid in ("pred_conf", "pred_den", "pred_exp") else P_PRED
    refused(shared, role, "DELETE FROM mimamsa_predictions WHERE chart_id = %s AND prediction_id = %s", (CHART_A, pid), prefix=prefix)


def test_predictions_the_live_mi_bhavisya_and_cockpit_clear_deletes_now_fail_loudly(shared):
    sql = "DELETE FROM mimamsa_predictions WHERE chart_id = %s AND lifecycle_status IN ('pending', 'due')"
    refused(shared, "amjis_app", sql, (CHART_A,), prefix=P_PRED)
    refused(shared, "data_plane_builder", sql, (CHART_A,), prefix=P_PRED)
    refused(shared, "amjis_app", "DELETE FROM mimamsa_predictions", prefix=P_PRED)
    assert counts(shared, CHART_A)["mimamsa_predictions"] == 7


@pytest.mark.parametrize("table,prefix", [("mimamsa_predictions", P_PRED), ("brahma_prospective_ledger", P_PRO),
                                          ("mimamsa_manifestation_sets", P_MAN), ("brahma_mimamsa_prediction_ledger", P_BMPL)])
def test_truncate_is_refused_even_for_a_superuser_and_for_a_regranted_owner(shared, table, prefix):
    refused(shared, "postgres", "TRUNCATE public." + table, prefix=prefix)
    refused(shared, "postgres", "TRUNCATE public." + table + " CASCADE", prefix=prefix)
    assert sum(counts(shared).values()) > 0


def test_replication_role_replica_does_not_bypass_because_the_triggers_are_enable_always(shared):
    psy = shared.pg["psycopg"]
    for sql in ("UPDATE mimamsa_predictions SET outcome_claim = 'x'", "DELETE FROM mimamsa_predictions", "DELETE FROM mimamsa_manifestation_sets",
                "DELETE FROM brahma_prospective_ledger", "DELETE FROM brahma_mimamsa_prediction_ledger", "UPDATE brahma_prospective_ledger SET claim = 'x'"):
        with shared.connect("postgres") as c:
            c.execute("SET session_replication_role = replica")
            with pytest.raises(psy.errors.InsufficientPrivilege, match="frozen_row_guard|delete_guard"):
                c.execute(sql)


def test_the_owner_can_disable_a_trigger_and_the_signature_is_tgenabled_not_A(world):
    """Honest limit: PostgreSQL cannot stop a table owner. The detector is tgenabled <> 'A'."""
    world.apply_sql(REAL)
    world.exec("ALTER TABLE mimamsa_predictions DISABLE TRIGGER mimamsa_predictions_frozen_row_guard", role="amjis_app")
    assert world.query("SELECT tgenabled FROM pg_trigger WHERE tgname = 'mimamsa_predictions_frozen_row_guard'") == [("D",)]
    assert passes(world, "amjis_app", "UPDATE mimamsa_predictions SET outcome_claim = 'x' WHERE chart_id = %s", (CHART_A,)) == 7


def test_non_owner_roles_cannot_disable_any_guard(shared):
    psy = shared.pg["psycopg"]
    for role in ("role_orchestrator", "role_ledger_write", "data_plane_builder"):
        for t, trg in (("mimamsa_predictions", "mimamsa_predictions_frozen_row_guard"), ("brahma_prospective_ledger", "brahma_prospective_ledger_frozen_row_guard")):
            with shared.connect(role) as c:
                with pytest.raises(psy.errors.InsufficientPrivilege):
                    c.execute("ALTER TABLE " + t + " DISABLE TRIGGER " + trg)


def test_predictions_legal_transitions_with_the_live_writers_exact_statements(shared):
    ab = "UPDATE mimamsa_predictions SET lifecycle_status = %s WHERE chart_id = %s AND prediction_id = %s AND lifecycle_status = 'pending'"   # mi_abhilekha.py:70
    assert passes(shared, "amjis_app", ab, ("confirmed", CHART_A, "pred_a0")) == 1 and passes(shared, "amjis_app", ab, ("denied", CHART_A, "pred_a1")) == 1
    assert passes(shared, "amjis_app", "UPDATE mimamsa_predictions SET lifecycle_status = 'expired' WHERE chart_id = %s AND prediction_id = %s", (CHART_A, "pred_a2")) == 1
    for src, dst in [("pred_a0", "due"), ("pred_a0", "partial"), ("pred_due", "confirmed"), ("pred_due", "denied"), ("pred_due", "partial"), ("pred_due", "expired")]:
        assert passes(shared, "role_ledger_write", "UPDATE mimamsa_predictions SET lifecycle_status = %s WHERE chart_id = %s AND prediction_id = %s", (dst, CHART_A, src)) == 1, (src, dst)
    assert passes(shared, "amjis_app", "UPDATE mimamsa_predictions SET lifecycle_status = 'expired' WHERE chart_id = %s AND prediction_id = 'pred_exp'", (CHART_A,)) == 1


@pytest.mark.parametrize("pid,dst", [("pred_conf", "pending"), ("pred_conf", "denied"), ("pred_conf", "expired"), ("pred_conf", "due"), ("pred_den", "confirmed"),
                                     ("pred_exp", "pending"), ("pred_exp", "confirmed"), ("pred_due", "pending"), ("pred_a0", "bogus"), ("pred_a0", "Confirmed"),
                                     ("pred_a0", "detected"), ("pred_a0", None)])
def test_predictions_terminal_never_changes_and_no_regression_unknown_or_null_status(shared, pid, dst):
    for role in ("amjis_app", "postgres"):
        refused(shared, role, "UPDATE mimamsa_predictions SET lifecycle_status = %s WHERE chart_id = %s AND prediction_id = %s", (dst, CHART_A, pid), prefix=P_PRED)


def test_predictions_stale_marker_set_once_pending_and_terminal_alike_never_cleared(cascaded):
    cascaded.exec("INSERT INTO build_runs (id) VALUES (%s), (%s)", (RUN_1, RUN_2))
    mark = ("UPDATE mimamsa_predictions SET chart_context_stale_at = NOW(), chart_context_stale_reason = 'chart_details_changed', "
            "chart_context_superseded_by_run_id = %s WHERE chart_id = %s AND chart_context_stale_at IS NULL")
    assert passes(cascaded, "amjis_app", mark, (RUN_1, CHART_A)) == 7        # recomputeChart / chartContextStaleness.ts: pending AND terminal rows
    cascaded.exec(mark.replace("NOW()", "'2026-09-01T00:00:00Z'"), (RUN_1, CHART_A), role="amjis_app")
    refused(cascaded, "amjis_app", "UPDATE mimamsa_predictions SET chart_context_stale_at = NULL, chart_context_stale_reason = NULL WHERE chart_id = %s", (CHART_A,), prefix=P_PRED)
    refused(cascaded, "amjis_app", "UPDATE mimamsa_predictions SET chart_context_stale_at = NOW() WHERE chart_id = %s", (CHART_A,), prefix=P_PRED)
    refused(cascaded, "amjis_app", "UPDATE mimamsa_predictions SET chart_context_superseded_by_run_id = %s WHERE chart_id = %s", (RUN_2, CHART_A), prefix=P_PRED)
    assert passes(cascaded, "amjis_app", mark, (RUN_2, CHART_A)) == 0
    refused(cascaded, "amjis_app", "UPDATE mimamsa_predictions SET chart_context_superseded_by_run_id = %s WHERE chart_id = %s", (RUN_2, CHART_B), prefix=P_PRED)


def test_on_delete_set_null_of_the_supersession_column_works_through_all_guards(cascaded):
    cascaded.exec("INSERT INTO build_runs (id) VALUES (%s)", (RUN_1,))
    for t, key in (("mimamsa_predictions", "chart_id"), ("brahma_prospective_ledger", "chart_id"), ("brahma_mimamsa_prediction_ledger", "chart_id")):
        cascaded.exec("UPDATE " + t + " SET chart_context_stale_at = now(), chart_context_stale_reason = 'chart_details_changed', chart_context_superseded_by_run_id = %s WHERE " + key + " = %s", (RUN_1, CHART_A), role="amjis_app")
    cascaded.exec("DELETE FROM build_runs WHERE id = %s", (RUN_1,), role="amjis_app")
    for t in ("mimamsa_predictions", "brahma_prospective_ledger", "brahma_mimamsa_prediction_ledger"):
        assert cascaded.query("SELECT count(*) FILTER (WHERE chart_context_superseded_by_run_id IS NOT NULL), count(*) FILTER (WHERE chart_context_stale_at IS NOT NULL) FROM " + t) == [(0, cascaded.query("SELECT count(*) FROM " + t + " WHERE chart_id = %s", (CHART_A,))[0][0])]


def test_insert_is_untouched_and_the_builder_guard_still_works(shared):
    psy = shared.pg["psycopg"]
    for role in ("amjis_app", "data_plane_builder"):
        with shared.connect(role) as c:
            c.execute(pred_row(CHART_C, "pred_new_" + role))
            c.rollback()
    with shared.connect("data_plane_builder") as c:
        with pytest.raises(psy.errors.InsufficientPrivilege, match="mimamsa_predictions_builder_guard: data_plane_builder may insert only pending/due"):
            c.execute(pred_row(CHART_C, "pred_bad", "confirmed"))


# ---- brahma_prospective_ledger

FROZEN_PRO = [("claim", "'changed'"), ("falsifier", "'changed'"), ("confidence", "0.9"), ("model", "'changed'"), ("formula_version", "'v9'"),
              ("as_of", "'2020-01-01T00:00:00Z'"), ("generator_class", "'anchor_engine'"), ("filed_by", "'someone'"), ("source_citation", "'other'"),
              ("created_at", "'2020-01-01T00:00:00Z'"), ("contact_id", "'sha256:abc'"), ("observation_window", "'[2030-01-01,2030-06-01)'"),
              ("chart_id", "'99999999-9999-4999-8999-999999999999'"), ("prediction_id", "'99999999-9999-4999-8999-999999999998'")]


@pytest.mark.parametrize("col,val", FROZEN_PRO)
@pytest.mark.parametrize("status", ["i", "m"])
def test_prospective_every_filed_column_is_frozen_open_and_matched(shared, col, val, status):
    for role in ("amjis_app", "role_ledger_write", "postgres"):
        refused(shared, role, "UPDATE brahma_prospective_ledger SET " + col + " = " + val + " WHERE prediction_id = %s", (PRO[status],), prefix=P_PRO, contains=col)


def test_prospective_event_class_and_claim_shape_cannot_be_changed_either(shared):
    refused(shared, "amjis_app", "UPDATE brahma_prospective_ledger SET claim_shape = 'point' WHERE prediction_id = %s", (PRO["i"],), prefix=P_PRO)
    refused(shared, "amjis_app", "UPDATE brahma_prospective_ledger SET event_class = 'ec_point' WHERE prediction_id = %s", (PRO["i"],), prefix=P_PRO)


def test_prospective_the_live_matching_statement_passes_and_the_record_is_complete(shared):
    # prospective_ledger.ts:828
    sql = ("UPDATE brahma_prospective_ledger SET lifecycle_status = 'matched', matched_event_id = %s::uuid, matched_at = now(), match_note = %s "
           "WHERE prediction_id = %s::uuid")
    assert passes(shared, "amjis_app", sql, (EVENT, "note", PRO["i"])) == 1
    assert passes(shared, "amjis_app", sql, (EVENT, "note", PRO["c"])) == 1


@pytest.mark.parametrize("src,dst,ok", [("i", "matched", None), ("i", "lapsed_unobserved", True), ("i", "withdrawn", True), ("i", "confirmed", False), ("i", "falsified", False),
                                        ("m", "confirmed", True), ("m", "falsified", True), ("m", "withdrawn", True), ("m", "open", False), ("m", "lapsed_unobserved", False)])
def test_prospective_transition_matrix(shared, src, dst, ok):
    sql = "UPDATE brahma_prospective_ledger SET lifecycle_status = %s WHERE prediction_id = %s"
    if ok is None:                                            # open -> matched without the match record is refused
        refused(shared, "amjis_app", sql, (dst, PRO[src]), prefix=P_PRO, contains="must carry matched_event_id")
    elif ok:
        assert passes(shared, "amjis_app", sql, (dst, PRO[src])) == 1
    else:
        refused(shared, "amjis_app", sql, (dst, PRO[src]), prefix=P_PRO, contains="transition")


def test_prospective_terminal_statuses_never_change_and_the_match_record_is_written_only_by_open_to_matched(cascaded):
    cascaded.exec("UPDATE brahma_prospective_ledger SET lifecycle_status = 'confirmed' WHERE prediction_id = %s", (PRO["m"],), role="amjis_app")   # legal: matched -> confirmed
    for dst in ("open", "matched", "falsified", "withdrawn", "lapsed_unobserved"):
        refused(cascaded, "amjis_app", "UPDATE brahma_prospective_ledger SET lifecycle_status = %s WHERE prediction_id = %s", (dst, PRO["m"]), prefix=P_PRO)
    refused(cascaded, "amjis_app", "UPDATE brahma_prospective_ledger SET match_note = 'rewritten' WHERE prediction_id = %s", (PRO["m"],), prefix=P_PRO, contains="match record")
    refused(cascaded, "amjis_app", "UPDATE brahma_prospective_ledger SET matched_at = now() WHERE prediction_id = %s", (PRO["i"],), prefix=P_PRO, contains="match record")


@pytest.mark.parametrize("pid", ["i", "pt", "c", "m", "b"])
@pytest.mark.parametrize("role", ["amjis_app", "role_ledger_write", "postgres"])
def test_prospective_delete_is_refused_for_every_status_and_shape(shared, pid, role):
    if role == "role_ledger_write":
        shared.exec("GRANT DELETE ON brahma_prospective_ledger TO role_ledger_write", role="amjis_app")
    refused(shared, role, "DELETE FROM brahma_prospective_ledger WHERE prediction_id = %s", (PRO[pid],), prefix=P_PRO)


def test_prospective_stale_marker_rules_and_no_op_update(shared):
    assert passes(shared, "amjis_app", "UPDATE brahma_prospective_ledger SET chart_context_stale_at = now(), chart_context_stale_reason = 'chart_details_changed' WHERE chart_id = %s AND chart_context_stale_at IS NULL", (CHART_A,)) == 4
    assert passes(shared, "amjis_app", "UPDATE brahma_prospective_ledger SET claim = claim WHERE chart_id = %s", (CHART_A,)) == 4


# ---- mimamsa_manifestation_sets

@pytest.mark.parametrize("col,val", [("chart_id", "'99999999-9999-4999-8999-999999999999'"), ("prediction_id", "'renamed'"), ("channel_id", "'ch_other'"),
                                     ("domain", "'health'"), ("source", "'other'"), ("citation_ref", "'{\"anchor_id\": \"other\"}'"), ("is_literal", "false"),
                                     ("frozen_at", "'2020-01-01T00:00:00Z'")])
def test_manifestation_no_column_is_mutable(shared, col, val):
    for role in ("amjis_app", "role_orchestrator", "postgres"):
        refused(shared, role, "UPDATE mimamsa_manifestation_sets SET " + col + " = " + val + " WHERE chart_id = %s AND prediction_id = 'pred_a0'", (CHART_A,), prefix=P_MAN, contains=col)


def test_manifestation_no_op_update_passes_and_every_delete_is_refused(shared):
    assert passes(shared, "amjis_app", "UPDATE mimamsa_manifestation_sets SET domain = domain WHERE chart_id = %s", (CHART_A,)) == 2
    for role in ("amjis_app", "role_orchestrator", "data_plane_builder", "postgres"):      # the builder's recorded 'd' grant is neutralised by the guard
        refused(shared, role, "DELETE FROM mimamsa_manifestation_sets WHERE chart_id = %s", (CHART_A,), prefix=P_MAN)
    refused(shared, "amjis_app", "DELETE FROM mimamsa_manifestation_sets", prefix=P_MAN)


def test_manifestation_insert_is_untouched_for_the_append_only_writer(shared):
    for role in ("amjis_app", "data_plane_builder"):
        with shared.connect(role) as c:
            c.execute("INSERT INTO mimamsa_manifestation_sets VALUES (%s, 'pred_new', 'ch', 'career', 'phala_anchors', '{}', true, now())", (CHART_C,))
            c.rollback()


# ---- brahma_mimamsa_prediction_ledger (DELETE / TRUNCATE only; its UPDATE trigger is untouched)

@pytest.mark.parametrize("key", ["det", "open", "dis", "out"])
@pytest.mark.parametrize("role", ["amjis_app", "postgres"])
def test_bmpl_delete_is_refused_for_every_status(shared, key, role):
    refused(shared, role, "DELETE FROM brahma_mimamsa_prediction_ledger WHERE id = %s", (BM[key],), prefix=P_BMPL)


def test_bmpl_the_update_freeze_of_migration_470_is_untouched(shared):
    psy = shared.pg["psycopg"]
    assert passes(shared, "amjis_app", "UPDATE brahma_mimamsa_prediction_ledger SET claim_text = 'edited' WHERE id = %s", (BM["det"],)) == 1
    assert passes(shared, "amjis_app", "UPDATE brahma_mimamsa_prediction_ledger SET lifecycle_status = 'window_closed' WHERE id = %s", (BM["open"],)) == 1
    with shared.connect("amjis_app") as c:                     # still the OLD trigger's message (SQLSTATE 23000), not ours
        with pytest.raises(psy.errors.IntegrityConstraintViolation, match="stamp and settled claim fields are immutable"):
            c.execute("UPDATE brahma_mimamsa_prediction_ledger SET claim_text = 'edited' WHERE id = %s", (BM["open"],))


def test_bmpl_message_part_delete_still_nulls_the_reference_through_the_trigger_set(cascaded):
    cascaded.exec("DELETE FROM message_parts WHERE id = 'bbbbbbbb-0000-4000-8000-000000000002'", role="amjis_app")
    assert cascaded.query("SELECT message_part_id FROM brahma_mimamsa_prediction_ledger WHERE id = %s", (BM["open"],)) == [(None,)]


# ================================================================ C. THE CHART-DELETE FIXTURE (SS N-108): ONE fixture, both directions

ORPHAN = "99999999-8888-4777-8666-555555555555"


def _rows_of(w, chart):
    return counts(w, chart)


def test_deleting_the_chart_removes_every_row_of_that_chart_in_all_four_tables_and_touches_no_other_chart(cascaded):
    before_a, before_b, before_c = _rows_of(cascaded, CHART_A), _rows_of(cascaded, CHART_B), _rows_of(cascaded, CHART_C)
    assert all(v > 0 for v in before_a.values()) and before_a == {"mimamsa_predictions": 7, "brahma_prospective_ledger": 4,
                                                                  "mimamsa_manifestation_sets": 2, "brahma_mimamsa_prediction_ledger": 3}
    cascaded.exec("DELETE FROM charts WHERE id = %s", (CHART_A,), role="amjis_app")
    assert _rows_of(cascaded, CHART_A) == {t: 0 for t in CASCADE_TABLES}
    assert _rows_of(cascaded, CHART_B) == before_b and _rows_of(cascaded, CHART_C) == before_c
    assert cascaded.query("SELECT count(*) FROM charts") == [(2,)]


@pytest.mark.parametrize("chart", [CHART_A, CHART_B, CHART_C])
def test_chart_delete_is_atomic_with_its_cascade_and_the_rollback_restores_every_row(cascaded, chart):
    before = counts(cascaded)
    with cascaded.connect("amjis_app") as c:
        c.execute("DELETE FROM charts WHERE id = %s", (chart,))
        assert sum(counts_in(c, chart).values()) == 0
        c.rollback()
    assert counts(cascaded) == before


def counts_in(conn, chart):
    return {t: conn.execute("SELECT count(*) FROM public." + t + " WHERE chart_id = %s", (chart,)).fetchone()[0] for t in CASCADE_TABLES}


def test_a_direct_delete_of_a_row_whose_chart_still_exists_is_refused_in_all_four_tables(shared):
    for role in ("amjis_app", "postgres"):
        refused(shared, role, "DELETE FROM mimamsa_predictions WHERE chart_id = %s AND prediction_id = 'pred_a0'", (CHART_A,), prefix=P_PRED)
        refused(shared, role, "DELETE FROM mimamsa_manifestation_sets WHERE chart_id = %s", (CHART_A,), prefix=P_MAN)
        refused(shared, role, "DELETE FROM brahma_prospective_ledger WHERE chart_id = %s", (CHART_A,), prefix=P_PRO)
        refused(shared, role, "DELETE FROM brahma_mimamsa_prediction_ledger WHERE chart_id = %s", (CHART_A,), prefix=P_BMPL)


def test_a_direct_delete_after_the_chart_row_is_gone_in_the_same_transaction_is_still_refused(shared):
    """The chart's cascade already removes the rows; a SEPARATE direct statement at depth 1 is not the cascade (and the chart-absence alone is not enough)."""
    psy = shared.pg["psycopg"]
    with shared.connect("amjis_app") as c:
        c.execute("ALTER TABLE mimamsa_predictions DROP CONSTRAINT mimamsa_predictions_chart_id_fkey")      # rows now orphan-able in this txn only
        c.execute("DELETE FROM charts WHERE id = %s", (CHART_C,))
        with pytest.raises(psy.errors.InsufficientPrivilege, match=P_PRED):
            c.execute("DELETE FROM mimamsa_predictions WHERE chart_id = %s", (CHART_C,))
        c.rollback()


def test_orphan_rows_whose_chart_never_existed_cannot_be_deleted_directly(world):
    world.apply_sql(REAL)
    world.exec(pred_row(ORPHAN, "pred_orphan"))
    world.exec("INSERT INTO mimamsa_manifestation_sets VALUES (%s, 'pred_orphan', 'ch', 'career', 'phala_anchors', '{}', true, now())", (ORPHAN,))
    world.exec(pros_row(ORPHAN, "interval", "open", "00000000-0000-4000-8000-0000000000c1"))
    world.exec("INSERT INTO brahma_mimamsa_prediction_ledger (chart_id, claim_text) VALUES (%s, 'orphan')", (ORPHAN,))
    for role in ("amjis_app", "postgres"):
        refused(world, role, "DELETE FROM mimamsa_predictions WHERE chart_id = %s", (ORPHAN,), prefix=P_PRED)
        refused(world, role, "DELETE FROM mimamsa_manifestation_sets WHERE chart_id = %s", (ORPHAN,), prefix=P_MAN)
        refused(world, role, "DELETE FROM brahma_prospective_ledger WHERE chart_id = %s", (ORPHAN,), prefix=P_PRO)
        refused(world, role, "DELETE FROM brahma_mimamsa_prediction_ledger WHERE chart_id = %s", (ORPHAN,), prefix=P_BMPL)


@pytest.mark.parametrize("fake", [
    "SET LOCAL madhav.chart_deleted = 'on'", "SET madhav.allow_frozen_delete = 'on'", "SET LOCAL app.chart_context = '{c}'", "SET LOCAL ROLE role_orchestrator",
    "SET LOCAL session_replication_role = origin", "SET LOCAL application_name = 'ri_cascade'", "SET LOCAL search_path = pg_temp, public",
    "SET LOCAL lock_timeout = '1ms'"])
def test_faking_the_condition_with_a_setting_a_role_or_a_set_local_does_not_open_a_direct_delete(shared, fake):
    psy = shared.pg["psycopg"]
    for role in ("amjis_app", "postgres"):
        with shared.connect(role) as c:
            try:
                c.execute(fake.replace("{c}", CHART_A))
            except psy.errors.Error:                       # e.g. SET ROLE refused for this session user: then there is nothing to test
                c.rollback()
                continue
            if "ROLE role_orchestrator" in fake and role == "amjis_app":
                continue
            with pytest.raises(psy.errors.InsufficientPrivilege, match="frozen_row_guard"):
                c.execute("DELETE FROM mimamsa_predictions WHERE chart_id = %s", (CHART_A,))
            c.rollback()


def test_a_user_function_cannot_open_it_by_deleting_the_chart_it_needs_one_that_really_goes(shared):
    """A SECURITY DEFINER function, a DO block and a function called from SELECT all run at trigger depth 1: refused, chart present or gone."""
    psy = shared.pg["psycopg"]
    with shared.connect("postgres") as c:
        c.execute("CREATE FUNCTION pg_temp.del_pred(uuid) RETURNS void LANGUAGE plpgsql SECURITY DEFINER AS $$ BEGIN DELETE FROM public.mimamsa_predictions WHERE chart_id = $1; END $$")
        with pytest.raises(psy.errors.InsufficientPrivilege, match=P_PRED):
            c.execute("SELECT pg_temp.del_pred(%s)", (CHART_A,))
        c.rollback()
    with shared.connect("postgres") as c:
        with pytest.raises(psy.errors.InsufficientPrivilege, match=P_PRED):
            c.execute("DO $$ BEGIN DELETE FROM public.mimamsa_predictions WHERE chart_id = '" + CHART_B + "'; END $$")
        c.rollback()


def test_the_discriminator_itself_depth_one_is_false_depth_two_in_the_cascade_is_true(shared):
    """The helper, called directly (depth 0) and from a trigger at depth 1, is false even for an absent chart; only the cascade makes it true."""
    assert shared.query("SELECT public.l5_frozen_chart_cascade_authorizes(%s), public.l5_frozen_chart_cascade_authorizes(%s), public.l5_frozen_chart_cascade_authorizes(NULL)",
                        (CHART_A, ORPHAN)) == [(False, False, False)]


def test_known_limit_a_user_created_trigger_can_reach_depth_two_for_a_chart_id_that_does_not_exist(world):
    """DOCUMENTED RESIDUAL, pinned so a change is noticed: depth >= 2 is also reached from a trigger a role creates itself; the guard then still
    requires the chart to be ABSENT. So (a) a chart that exists can never be bypassed this way, (b) an orphan row (no chart) can, by someone who can
    CREATE a trigger (DDL). Mitigation: the cascade FKs of 1275 leave no orphans; DDL is owner-only."""
    world.apply_sql(REAL)
    add_chart_fks(world)
    world.exec("CREATE TABLE bait (id int); GRANT ALL ON bait TO amjis_app; CREATE FUNCTION bait_fn() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN DELETE FROM public.mimamsa_predictions "
               "WHERE chart_id = '" + CHART_A + "'; RETURN NULL; END $$; CREATE TRIGGER tb AFTER INSERT ON bait FOR EACH ROW EXECUTE FUNCTION bait_fn()")
    refused(world, "amjis_app", "INSERT INTO bait VALUES (1)", prefix=P_PRED)                       # (a) the chart exists: refused even at depth 2
    assert counts(world, CHART_A)["mimamsa_predictions"] == 7
    world.exec("ALTER TABLE mimamsa_predictions DROP CONSTRAINT mimamsa_predictions_chart_id_fkey", role="amjis_app")
    world.exec("DELETE FROM charts WHERE id = %s", (CHART_A,), role="amjis_app")                    # the chart is really gone, its rows stay (no FK)
    assert counts(world, CHART_A)["mimamsa_predictions"] == 7
    world.exec("INSERT INTO bait VALUES (1)", role="amjis_app")                                     # (b) pinned residual: allowed
    assert counts(world, CHART_A)["mimamsa_predictions"] == 0


def test_truncating_charts_cascade_is_refused_by_the_truncate_guard(shared):
    refused(shared, "postgres", "TRUNCATE public.charts CASCADE", prefix=None)


def test_the_consent_withdrawal_exception_keeps_working_beside_the_cascade_for_all_four_tables(cascaded):
    cascaded.exec("INSERT INTO chart_subject_consent VALUES (%s, 'granted', NULL)", (CHART_B,))
    for t, extra in (("mimamsa_predictions", ""), ("mimamsa_manifestation_sets", ""), ("brahma_prospective_ledger", ""), ("brahma_mimamsa_prediction_ledger", "")):
        refused(cascaded, "amjis_app", "DELETE FROM " + t + " WHERE chart_id = %s", (CHART_B,))
    cascaded.exec("UPDATE chart_subject_consent SET consent_state = 'withdrawn', withdrawn_at = now() WHERE chart_id = %s", (CHART_B,))
    for t in CASCADE_TABLES:                                              # the sweep's own statement, chart STILL present: allowed by the consent exception
        assert passes(cascaded, "amjis_app", "DELETE FROM " + t + " WHERE chart_id = %s", (CHART_B,)) > 0, t
    cascaded.exec("INSERT INTO chart_subject_deletion_disputes (chart_id, status) VALUES (%s, 'open')", (CHART_B,))
    for t in CASCADE_TABLES:
        refused(cascaded, "amjis_app", "DELETE FROM " + t + " WHERE chart_id = %s", (CHART_B,))
    # an open dispute does NOT block the chart's own deletion: deleting the chart is the strongest withdrawal (SS N-108)
    cascaded.exec("DELETE FROM charts WHERE id = %s", (CHART_B,), role="amjis_app")
    assert _rows_of(cascaded, CHART_B) == {t: 0 for t in CASCADE_TABLES}


def test_the_cascade_runs_as_the_table_owner_whoever_deletes_the_chart_and_the_mirrored_roles_that_may_delete_charts(cascaded):
    cascaded.exec("GRANT DELETE ON charts TO role_ledger_write", role="amjis_app")
    cascaded.exec("ALTER TABLE charts NO FORCE ROW LEVEL SECURITY", role="amjis_app")
    cascaded.exec("CREATE POLICY chart_service_policy ON charts FOR ALL TO role_orchestrator, role_ledger_write USING (true)", role="amjis_app")
    cascaded.exec("DELETE FROM charts WHERE id = %s", (CHART_C,), role="role_orchestrator")
    assert _rows_of(cascaded, CHART_C) == {t: 0 for t in CASCADE_TABLES}
    cascaded.exec("DELETE FROM charts WHERE id = %s", (CHART_B,), role="role_ledger_write")
    assert _rows_of(cascaded, CHART_B) == {t: 0 for t in CASCADE_TABLES}
    assert _rows_of(cascaded, CHART_A) != {t: 0 for t in CASCADE_TABLES}


def test_chart_delete_with_the_cascade_still_writes_nothing_else_and_leaves_the_guards_in_place(cascaded):
    state = _state(cascaded)
    cascaded.exec("DELETE FROM charts WHERE id = %s", (CHART_A,), role="amjis_app")
    assert _state(cascaded) == state and cascaded.schema_acl() == cascaded.baseline_acl


# ================================================================ D. the consent-withdrawal exception, per table, without the FKs

def test_withdrawal_exception_conditions_per_table(world):
    world.apply_sql(REAL)
    for t in CASCADE_TABLES:
        refused(world, "amjis_app", "DELETE FROM " + t + " WHERE chart_id = %s", (CHART_B,))
    world.exec("INSERT INTO chart_subject_consent VALUES (%s, 'withdrawn', now())", (CHART_B,))
    for status, ok in (("open", False), ("reopened", False), ("escalated", False), ("resolved", True)):
        world.exec("DELETE FROM chart_subject_deletion_disputes")
        world.exec("INSERT INTO chart_subject_deletion_disputes (chart_id, status) VALUES (%s, %s)", (CHART_B, status))
        for t in CASCADE_TABLES:
            if ok:
                assert passes(world, "amjis_app", "DELETE FROM " + t + " WHERE chart_id = %s", (CHART_B,)) > 0, (t, status)
            else:
                refused(world, "amjis_app", "DELETE FROM " + t + " WHERE chart_id = %s", (CHART_B,))
    # withdrawal never unfreezes UPDATE
    world.exec("DELETE FROM chart_subject_deletion_disputes")
    refused(world, "amjis_app", "UPDATE mimamsa_predictions SET outcome_claim = 'x' WHERE chart_id = %s", (CHART_B,), prefix=P_PRED)
    refused(world, "amjis_app", "UPDATE brahma_prospective_ledger SET claim = 'x' WHERE chart_id = %s", (CHART_B,), prefix=P_PRO)
    refused(world, "amjis_app", "UPDATE mimamsa_manifestation_sets SET domain = 'x' WHERE chart_id = %s", (CHART_B,), prefix=P_MAN)


def test_withdrawal_exception_fails_closed_for_a_role_that_cannot_read_the_consent_tables_and_when_they_are_absent(pg_cluster):
    w = make_world(pg_cluster)
    try:
        w.apply_sql(REAL)
        w.exec("INSERT INTO chart_subject_consent VALUES (%s, 'withdrawn', now())", (CHART_B,))
        refused(w, "role_orchestrator", "DELETE FROM mimamsa_predictions WHERE chart_id = %s", (CHART_B,), prefix=P_PRED)     # no privilege on the consent tables
        assert passes(w, "amjis_app", "DELETE FROM mimamsa_predictions WHERE chart_id = %s", (CHART_B,)) == 2
        w.exec("DROP TABLE chart_subject_consent; DROP TABLE chart_subject_deletion_disputes")
        refused(w, "amjis_app", "DELETE FROM mimamsa_predictions WHERE chart_id = %s", (CHART_B,), prefix=P_PRED)
    finally:
        drop_world(pg_cluster, w)


def test_no_setting_or_role_name_opens_a_direct_delete_on_any_table(shared):
    psy = shared.pg["psycopg"]
    for setting in ("madhav.allow_frozen_delete", "madhav.frozen_row_erasure", "madhav.migration_bypass", "app.allow_frozen_delete"):
        for t in CASCADE_TABLES:
            with shared.connect("amjis_app") as c:
                c.execute("SET " + setting + " = 'on'")
                with pytest.raises(psy.errors.InsufficientPrivilege, match="frozen_row_guard|delete_guard"):
                    c.execute("DELETE FROM " + t + " WHERE chart_id = %s", (CHART_A,))


# ================================================================ E. md5 guards, assertions that RAISE, refusals

def _window_exec(w, sql, role="amjis_app"):
    w.window("grant")
    try:
        w.exec(sql, role=role)
    finally:
        w.window("revoke")


def _raises(w, match, sql=None):
    psy = w.pg["psycopg"]
    with pytest.raises(psy.errors.RaiseException, match=match):
        w.apply_sql(sql or REAL)


def test_md5_guard_refuses_a_changed_live_builder_guard_body_and_changes_nothing(world):
    b = body(REAL, "guard")
    _window_exec(world, "CREATE OR REPLACE FUNCTION public.mimamsa_predictions_builder_guard() RETURNS trigger LANGUAGE plpgsql SECURITY INVOKER "
                 "SET search_path = pg_catalog, pg_temp AS $g$" + b.replace("'pending', 'due'", "'pending', 'due', 'confirmed'") + "$g$")
    before = _state(world)
    _raises(world, "refusing to overwrite it")
    assert _state(world) == before


def test_md5_guard_refuses_a_one_byte_same_length_change(world):
    b = body(REAL, "guard").replace("refusing chart_id", "refusing chart_ID")
    assert len(b) == 1084 and hashlib.md5(b.encode()).hexdigest() != "46c23854275c2712b30860a2b174adb2"
    _window_exec(world, "CREATE OR REPLACE FUNCTION public.mimamsa_predictions_builder_guard() RETURNS trigger LANGUAGE plpgsql SECURITY INVOKER "
                 "SET search_path = pg_catalog, pg_temp AS $g$" + b + "$g$")
    _raises(world, "refusing to overwrite it")


@pytest.mark.parametrize("alter", ["SECURITY DEFINER", "SET search_path = public", "STABLE"])
def test_attribute_drift_of_the_live_builder_guard_with_the_same_body_is_refused(world, alter):
    world.exec("ALTER FUNCTION public.mimamsa_predictions_builder_guard() " + alter, role="amjis_app")
    _raises(world, "other attributes")


def test_a_live_builder_trigger_with_another_shape_is_refused(world):
    world.exec("DROP TRIGGER mimamsa_predictions_builder_guard ON mimamsa_predictions; CREATE TRIGGER mimamsa_predictions_builder_guard BEFORE INSERT ON "
               "mimamsa_predictions FOR EACH ROW EXECUTE FUNCTION public.mimamsa_predictions_builder_guard()", role="amjis_app")
    _raises(world, "is not the captured one")


@pytest.mark.parametrize("tag,sig", [("helper", "l5_frozen_withdrawal_authorizes(p_chart uuid) RETURNS boolean"), ("cascade", "l5_frozen_chart_cascade_authorizes(p_chart uuid) RETURNS boolean"),
                                     ("predictions", "mimamsa_predictions_frozen_row_guard() RETURNS trigger"), ("prospective", "brahma_prospective_ledger_frozen_row_guard() RETURNS trigger"),
                                     ("manifestation", "mimamsa_manifestation_sets_frozen_row_guard() RETURNS trigger"), ("bmpl", "brahma_mimamsa_prediction_ledger_delete_guard() RETURNS trigger")])
def test_a_changed_live_copy_of_any_new_guard_is_refused_and_the_exact_one_is_replaced_quietly(world, tag, sig):
    world.apply_sql(REAL)
    ret = "boolean" if "RETURNS boolean" in sig else "trigger"
    _window_exec(world, "CREATE OR REPLACE FUNCTION public." + sig + " LANGUAGE plpgsql AS $g$ BEGIN " + ("RETURN true;" if ret == "boolean" else "RETURN NEW;") + " END $g$")
    _raises(world, "refusing to overwrite a changed live guard")


def test_the_recorded_builder_grant_is_asserted_and_the_file_raises_if_it_is_absent_or_different(world):
    world.exec("REVOKE DELETE ON mimamsa_predictions FROM data_plane_builder", role="amjis_app")
    _raises(world, "recorded live grant .*mimamsa_predictions")
    world.exec("GRANT DELETE ON mimamsa_predictions TO data_plane_builder; REVOKE INSERT ON mimamsa_manifestation_sets FROM data_plane_builder", role="amjis_app")
    _raises(world, "recorded live grant .*mimamsa_manifestation_sets")
    world.exec("GRANT INSERT ON mimamsa_manifestation_sets TO data_plane_builder; GRANT UPDATE ON mimamsa_manifestation_sets TO data_plane_builder", role="amjis_app")
    _raises(world, "recorded live grant .*mimamsa_manifestation_sets")
    world.exec("REVOKE UPDATE ON mimamsa_manifestation_sets FROM data_plane_builder", role="amjis_app")
    world.apply_sql(REAL)                                              # present as recorded: a no-op, and nothing granted
    assert world.query("SELECT string_agg(privilege_type, ',' ORDER BY privilege_type) FROM information_schema.role_table_grants WHERE grantee = 'data_plane_builder' AND table_name = 'mimamsa_predictions'") == [("DELETE,INSERT,SELECT",)]


def test_the_script_never_grants_so_an_absent_grant_is_never_repaired_silently(world):
    world.exec("REVOKE SELECT ON mimamsa_predictions FROM data_plane_builder", role="amjis_app")
    _raises(world, "does not create it")
    assert world.query("SELECT has_table_privilege('data_plane_builder', 'mimamsa_predictions', 'SELECT')") == [(False,)]


def test_repo_objects_it_builds_beside_must_be_the_repos(world):
    _window_exec(world, "CREATE OR REPLACE FUNCTION public.bmpl_freeze_confirmed() RETURNS trigger LANGUAGE plpgsql AS $x$ BEGIN RETURN NEW; END $x$")
    _raises(world, "is not the repo version")


def test_missing_columns_or_tables_or_non_owner_are_refused_by_the_gate(world):
    world.exec("ALTER TABLE mimamsa_predictions DROP COLUMN contact_id", role="amjis_app")
    _raises(world, "has no column contact_id")


def test_a_role_with_create_but_without_ownership_is_refused_by_the_gate(world):
    with world.connect("data_plane_migrator") as c:
        c.execute("SET LOCAL ROLE data_plane_schema_owner")
        c.execute("GRANT CREATE ON SCHEMA public TO role_orchestrator")
        c.commit()
    psy = world.pg["psycopg"]
    with pytest.raises(psy.errors.RaiseException, match="not a member of the owner"):
        world.apply_sql(REAL, role="role_orchestrator", window=False)


def test_lock_timeout_fails_fast_when_another_session_holds_a_table(world):
    psy = world.pg["psycopg"]
    holder = world.connect("amjis_app")
    holder.execute("LOCK TABLE mimamsa_manifestation_sets IN ACCESS EXCLUSIVE MODE")
    try:
        with pytest.raises(psy.errors.LockNotAvailable):
            world.apply_sql(REAL)
    finally:
        holder.rollback()
        holder.close()


def test_the_in_script_self_test_leaves_nothing_behind(world):
    before = world.catalog_state()["rowdata"]
    world.apply_sql(REAL)
    assert world.catalog_state()["rowdata"] == before
    assert world.query("SELECT count(*) FROM pg_proc WHERE proname LIKE 'm1265%'") == [(0,)]


# ================================================================ F. the ROLLBACK script

def test_rollback_script_removes_exactly_what_the_forward_script_added(world):
    pre = world.catalog_state()
    world.apply_sql(REAL)
    assert world.catalog_state() != pre
    world.apply_sql(ROLLBACK.read_text(encoding="utf8"), window=False)       # DROP needs no CREATE capability
    assert world.catalog_state() == pre


def test_rollback_script_refuses_when_something_is_not_as_installed(world):
    world.apply_sql(REAL)
    world.exec("ALTER TABLE mimamsa_predictions DISABLE TRIGGER mimamsa_predictions_frozen_row_guard", role="amjis_app")
    psy = world.pg["psycopg"]
    with pytest.raises(psy.errors.RaiseException, match="not all present and enabled ALWAYS"):
        world.apply_sql(ROLLBACK.read_text(encoding="utf8"), window=False)


# ================================================================ G. probes shared by the mutation proofs

def run_probes(w: World) -> list:
    """Probe an applied world with the 1275 FKs. Roles hold the privilege each statement needs, so a refusal can only come from a guard.
    Returns the names of probes that did NOT behave. Nothing is committed except the consent / dispute setup rows."""
    psy = w.pg["psycopg"]
    failed = []

    def must_refuse(name, role, sql, params=None, contains=None):
        with w.connect(role) as c:
            try:
                c.execute(sql, params)
                failed.append(name + ": not refused")
            except psy.errors.InsufficientPrivilege as e:
                m = str(e)
                if not any(p.rstrip(":") in m for p in (P_PRED, P_PRO, P_MAN, P_BMPL)) or (contains and contains not in m):
                    failed.append(name + ": refused by something else: " + m.splitlines()[0][:90])
            except Exception as e:  # noqa: BLE001
                failed.append(name + ": unexpected " + type(e).__name__)
            finally:
                c.rollback()

    def must_pass(name, role, sql, params=None, rows=None):
        with w.connect(role) as c:
            try:
                n = c.execute(sql, params).rowcount
                if rows is not None and n != rows:
                    failed.append("%s: affected %s, expected %s" % (name, n, rows))
            except Exception as e:  # noqa: BLE001
                failed.append(name + ": refused " + type(e).__name__)
            finally:
                c.rollback()

    U = "UPDATE mimamsa_predictions SET %s WHERE chart_id = %%s AND prediction_id = %s"
    for col, val in (("source_pramana_id", "'x'"), ("outcome_claim", "'x'"), ("eval_date", "'2031-01-01'"), ("falsifier_jsonb", "'{}'"), ("frozen_bundle_hash", "'x'"),
                     ("contact_id", "'x'"), ("prediction_id", "'x'"), ("confidence_band", "'[0.1,0.2)'")):
        must_refuse("pred update %s pending" % col, "amjis_app", U % (col + " = " + val, "'pred_a0'"), (CHART_A,))
        must_refuse("pred update %s terminal" % col, "postgres", U % (col + " = " + val, "'pred_conf'"), (CHART_A,))
    must_refuse("pred delete pending", "amjis_app", "DELETE FROM mimamsa_predictions WHERE chart_id = %s AND prediction_id = 'pred_a0'", (CHART_A,))
    must_refuse("pred delete due by builder", "data_plane_builder", "DELETE FROM mimamsa_predictions WHERE chart_id = %s AND prediction_id = 'pred_due'", (CHART_A,))
    must_refuse("pred delete terminal", "role_orchestrator", "DELETE FROM mimamsa_predictions WHERE chart_id = %s AND prediction_id = 'pred_conf'", (CHART_A,))
    must_refuse("pred truncate", "postgres", "TRUNCATE mimamsa_predictions", contains="TRUNCATE of public.mimamsa_predictions is refused")
    must_refuse("pred terminal to pending", "postgres", U % ("lifecycle_status = 'pending'", "'pred_conf'"), (CHART_A,))
    must_refuse("pred confirmed to denied", "amjis_app", U % ("lifecycle_status = 'denied'", "'pred_conf'"), (CHART_A,))
    must_refuse("pred unknown status", "amjis_app", U % ("lifecycle_status = 'bogus'", "'pred_a0'"), (CHART_A,))
    must_refuse("pred due to pending", "amjis_app", U % ("lifecycle_status = 'pending'", "'pred_due'"), (CHART_A,))
    must_refuse("pred status NULL", "amjis_app", U % ("lifecycle_status = NULL", "'pred_a0'"), (CHART_A,), contains="transition")
    must_pass("pred pending to confirmed", "amjis_app", U % ("lifecycle_status = 'confirmed'", "'pred_a0'"), (CHART_A,), rows=1)
    must_pass("pred pending to expired", "amjis_app", U % ("lifecycle_status = 'expired'", "'pred_a1'"), (CHART_A,), rows=1)
    must_pass("pred due to partial", "amjis_app", U % ("lifecycle_status = 'partial'", "'pred_due'"), (CHART_A,), rows=1)
    must_pass("pred stale marking", "amjis_app", "UPDATE mimamsa_predictions SET chart_context_stale_at = now(), chart_context_stale_reason = 'chart_details_changed' WHERE chart_id = %s AND chart_context_stale_at IS NULL", (CHART_A,), rows=7)
    # prospective
    for col, val in (("claim", "'x'"), ("confidence", "0.9"), ("falsifier", "'x'"), ("contact_id", "'x'"), ("model", "'x'")):
        must_refuse("pro update " + col, "amjis_app", "UPDATE brahma_prospective_ledger SET " + col + " = " + val + " WHERE prediction_id = %s", (PRO["i"],))
    must_refuse("pro delete", "amjis_app", "DELETE FROM brahma_prospective_ledger WHERE prediction_id = %s", (PRO["i"],))
    must_refuse("pro truncate", "postgres", "TRUNCATE brahma_prospective_ledger", contains="TRUNCATE of public.brahma_prospective_ledger is refused")
    must_refuse("pro open to confirmed", "amjis_app", "UPDATE brahma_prospective_ledger SET lifecycle_status = 'confirmed' WHERE prediction_id = %s", (PRO["i"],))
    must_refuse("pro matched to open", "amjis_app", "UPDATE brahma_prospective_ledger SET lifecycle_status = 'open' WHERE prediction_id = %s", (PRO["m"],))
    must_refuse("pro match note alone", "amjis_app", "UPDATE brahma_prospective_ledger SET match_note = 'x' WHERE prediction_id = %s", (PRO["m"],))
    must_refuse("pro matched without record", "amjis_app", "UPDATE brahma_prospective_ledger SET lifecycle_status = 'matched' WHERE prediction_id = %s", (PRO["i"],))
    must_pass("pro matching statement", "amjis_app", "UPDATE brahma_prospective_ledger SET lifecycle_status = 'matched', matched_event_id = %s::uuid, matched_at = now(), match_note = 'n' WHERE prediction_id = %s::uuid", (EVENT, PRO["i"]), rows=1)
    must_pass("pro matched to confirmed", "amjis_app", "UPDATE brahma_prospective_ledger SET lifecycle_status = 'confirmed' WHERE prediction_id = %s", (PRO["m"],), rows=1)
    # manifestation + bmpl
    must_refuse("man update", "amjis_app", "UPDATE mimamsa_manifestation_sets SET citation_ref = '{}' WHERE chart_id = %s", (CHART_A,))
    must_refuse("man delete", "data_plane_builder", "DELETE FROM mimamsa_manifestation_sets WHERE chart_id = %s", (CHART_A,))
    must_refuse("man truncate", "postgres", "TRUNCATE mimamsa_manifestation_sets", contains="TRUNCATE of public.mimamsa_manifestation_sets is refused")
    must_refuse("bmpl delete", "amjis_app", "DELETE FROM brahma_mimamsa_prediction_ledger WHERE id = %s", (BM["out"],))
    must_refuse("bmpl truncate", "postgres", "TRUNCATE brahma_mimamsa_prediction_ledger", contains="TRUNCATE of public.brahma_mimamsa_prediction_ledger is refused")
    # no setting opens anything
    for setting in ("madhav.allow_frozen_delete", "madhav.frozen_row_erasure", "madhav.migration_bypass", "app.allow_frozen_delete"):
        with w.connect("amjis_app") as c:
            c.execute("SET " + setting + " = 'on'")
            try:
                c.execute("DELETE FROM mimamsa_predictions WHERE chart_id = %s AND prediction_id = 'pred_a2'", (CHART_A,))
                failed.append("setting " + setting + ": delete not refused")
            except psy.errors.InsufficientPrivilege as e:
                if P_PRED.rstrip(":") not in str(e):
                    failed.append("setting " + setting + ": refused by something else")
            c.rollback()
    with w.connect("postgres") as c:
        c.execute("SET session_replication_role = replica")
        try:
            c.execute("UPDATE mimamsa_predictions SET outcome_claim = 'x' WHERE chart_id = %s", (CHART_A,))
            failed.append("replica update: not refused")
        except psy.errors.InsufficientPrivilege:
            pass
        c.rollback()
    # the stale marker is set once: set it (committed on this fresh world, chart C), then clearing it must be refused
    with w.connect("amjis_app") as c:
        c.execute("UPDATE mimamsa_predictions SET chart_context_stale_at = now(), chart_context_stale_reason = 'chart_details_changed' WHERE chart_id = %s", (CHART_C,))
        c.commit()
    must_refuse("pred stale marker cleared", "amjis_app", "UPDATE mimamsa_predictions SET chart_context_stale_at = NULL, chart_context_stale_reason = NULL WHERE chart_id = %s", (CHART_C,))
    # orphan rows (chart never existed) cannot be deleted directly: absence of the chart alone is not the cascade
    with w.connect("amjis_app") as c:
        try:
            c.execute("ALTER TABLE mimamsa_predictions DROP CONSTRAINT mimamsa_predictions_chart_id_fkey")
            c.execute(pred_row("99999999-8888-4777-8666-555555555555", "pred_orphan"))
            c.execute("DELETE FROM mimamsa_predictions WHERE chart_id = '99999999-8888-4777-8666-555555555555'")
            failed.append("orphan direct delete: not refused")
        except psy.errors.InsufficientPrivilege as e:
            if P_PRED.rstrip(":") not in str(e):
                failed.append("orphan direct delete: refused by something else")
        finally:
            c.rollback()
    # depth >= 2 alone is reachable from a user trigger: for a chart that EXISTS the delete must still be refused
    with w.connect("postgres") as c:
        try:
            c.execute("CREATE TABLE bait (id int); CREATE FUNCTION bait_fn() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN DELETE FROM public.mimamsa_predictions WHERE chart_id = '"
                      + CHART_A + "'; RETURN NULL; END $$; CREATE TRIGGER tb AFTER INSERT ON bait FOR EACH ROW EXECUTE FUNCTION bait_fn()")
            c.execute("INSERT INTO bait VALUES (1)")
            failed.append("nested delete of an existing chart: not refused")
        except psy.errors.InsufficientPrivilege as e:
            if P_PRED.rstrip(":") not in str(e):
                failed.append("nested delete of an existing chart: refused by something else")
        finally:
            c.rollback()
    # the same nested delete by a role that cannot read public.charts must fail CLOSED (not open)
    with w.connect("postgres") as c:
        try:
            c.execute("CREATE ROLE probe_nc NOLOGIN; GRANT USAGE ON SCHEMA public TO probe_nc; GRANT SELECT, DELETE ON mimamsa_predictions TO probe_nc; "
                      "CREATE TABLE bait (id int); GRANT INSERT ON bait TO probe_nc; CREATE FUNCTION bait_fn() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN DELETE FROM public.mimamsa_predictions "
                      "WHERE chart_id = '" + CHART_A + "'; RETURN NULL; END $$; CREATE TRIGGER tb AFTER INSERT ON bait FOR EACH ROW EXECUTE FUNCTION bait_fn()")
            c.execute("SET LOCAL ROLE probe_nc")
            c.execute("INSERT INTO bait VALUES (1)")
            failed.append("nested delete by a role that cannot read charts: not refused")
        except psy.errors.InsufficientPrivilege as e:
            if P_PRED.rstrip(":") not in str(e):
                failed.append("nested delete by a role that cannot read charts: refused by something else: " + str(e).splitlines()[0][:80])
        finally:
            c.rollback()
    # chart delete: the cascade works, in every table, for the right chart only; a direct delete beside it is refused
    with w.connect("amjis_app") as c:
        try:
            c.execute("DELETE FROM charts WHERE id = %s", (CHART_C,))
            got = counts_in(c, CHART_C)
            other = counts_in(c, CHART_A)
            if any(got.values()):
                failed.append("chart delete: rows of the chart remain " + str(got))
            if not all(other.values()):
                failed.append("chart delete: another chart was touched " + str(other))
        except psy.errors.Error as e:
            failed.append("chart delete refused: " + type(e).__name__ + " " + str(e).splitlines()[0][:100])
        finally:
            c.rollback()
    # consent withdrawal: granted -> refused, withdrawn -> passes, withdrawn + open dispute -> refused
    with w.connect("postgres") as c:
        c.execute("INSERT INTO chart_subject_consent VALUES (%s, 'granted', NULL)", (CHART_B,))
        c.commit()
    must_refuse("delete after consent granted", "amjis_app", "DELETE FROM mimamsa_predictions WHERE chart_id = %s", (CHART_B,))
    with w.connect("postgres") as c:
        c.execute("UPDATE chart_subject_consent SET consent_state = 'withdrawn', withdrawn_at = now() WHERE chart_id = %s", (CHART_B,))
        c.commit()
    must_pass("delete after withdrawal", "amjis_app", "DELETE FROM mimamsa_predictions WHERE chart_id = %s", (CHART_B,), rows=2)
    must_refuse("delete after withdrawal by a role that cannot read the consent tables", "role_orchestrator", "DELETE FROM mimamsa_predictions WHERE chart_id = %s", (CHART_B,))
    must_pass("manifestation delete after withdrawal", "amjis_app", "DELETE FROM mimamsa_manifestation_sets WHERE chart_id = %s", (CHART_B,), rows=1)
    with w.connect("postgres") as c:
        c.execute("INSERT INTO chart_subject_deletion_disputes (chart_id, status) VALUES (%s, 'open')", (CHART_B,))
        c.commit()
    must_refuse("delete after withdrawal with open dispute", "amjis_app", "DELETE FROM brahma_prospective_ledger WHERE chart_id = %s", (CHART_B,))
    return failed


def _fresh(pg, sql):
    w = make_world(pg)
    w.apply_sql(sql)
    add_chart_fks(w)
    return w


def test_probe_suite_passes_on_the_real_script(pg_cluster):
    w = _fresh(pg_cluster, REAL)
    try:
        assert run_probes(w) == []
    finally:
        drop_world(pg_cluster, w)


# ================================================================ H. mutation proofs

def _strip_selftest(sql):
    a, b = sql.index("-- D2. SELF-TEST"), sql.index("-- E. POST-CHECK")
    return sql[:a] + sql[b:]


def _repin(sql, tag, old_md5):
    return sql.replace(old_md5, hashlib.md5(body(sql, tag).encode()).hexdigest())


def mutate(tag, old, new, count=1):
    b = body(REAL, tag)
    assert b.count(old) == count, "mutation target not found %dx: %r (%d)" % (count, old, b.count(old))
    old_md5 = hashlib.md5(b.encode()).hexdigest()
    return _repin(REAL.replace(b, b.replace(old, new)), tag, old_md5)


MUTANTS = [
    ("predictions: delete refusal removed", lambda: mutate("predictions", "  RAISE EXCEPTION 'mimamsa_predictions_frozen_row_guard: frozen predictions cannot be deleted", "  RETURN OLD; RAISE EXCEPTION 'mimamsa_predictions_frozen_row_guard: frozen predictions cannot be deleted")),
    ("predictions: pending exempt from delete", lambda: mutate("predictions", "  RAISE EXCEPTION 'mimamsa_predictions_frozen_row_guard: frozen predictions cannot be deleted", "  IF OLD.lifecycle_status IN ('pending', 'due') THEN RETURN OLD; END IF;\n  RAISE EXCEPTION 'mimamsa_predictions_frozen_row_guard: frozen predictions cannot be deleted")),
    ("predictions: column comparison off", lambda: mutate("predictions", "IF v_new IS DISTINCT FROM v_old THEN", "IF false THEN")),
    ("predictions: source_pramana_id allow-listed", lambda: mutate("predictions", "ARRAY['lifecycle_status', 'chart_context_stale_at',", "ARRAY['lifecycle_status', 'source_pramana_id', 'chart_context_stale_at',")),
    ("predictions: pending exempt from the column check", lambda: mutate("predictions", "    IF v_new IS DISTINCT FROM v_old THEN", "    IF v_new IS DISTINCT FROM v_old AND OLD.lifecycle_status <> 'pending' THEN")),
    ("predictions: terminal statuses mutable", lambda: mutate("predictions", "OR (OLD.lifecycle_status = 'due'     AND NEW.lifecycle_status IN ('confirmed', 'denied', 'partial', 'expired')),", "OR (OLD.lifecycle_status = 'due'     AND NEW.lifecycle_status IN ('confirmed', 'denied', 'partial', 'expired')) OR OLD.lifecycle_status IN ('confirmed', 'denied', 'partial', 'expired'),")),
    ("predictions: unknown target status accepted", lambda: mutate("predictions", "NEW.lifecycle_status IN ('due', 'confirmed', 'denied', 'partial', 'expired'))", "true)")),
    ("predictions: NULL transition not coalesced to false", lambda: mutate("predictions", "           false)\n      THEN", "           true)\n      THEN")),
    ("predictions: TRUNCATE branch removed", lambda: mutate("predictions", "  IF TG_OP = 'TRUNCATE' THEN\n    RAISE EXCEPTION", "  IF false THEN\n    RAISE EXCEPTION")),
    ("predictions: stale marker clearable", lambda: mutate("predictions", "    IF OLD.chart_context_stale_at IS NOT NULL\n       AND", "    IF false\n       AND")),
    ("predictions: role-name exemption", lambda: mutate("predictions", "  IF TG_OP = 'TRUNCATE' THEN\n", "  IF current_user = 'amjis_app' AND TG_OP <> 'TRUNCATE' THEN RETURN COALESCE(NEW, OLD); END IF;\n  IF TG_OP = 'TRUNCATE' THEN\n")),
    ("predictions: session-setting bypass", lambda: mutate("predictions", "  IF TG_OP = 'TRUNCATE' THEN\n", "  IF current_setting('madhav.allow_frozen_delete', true) = 'on' THEN RETURN COALESCE(NEW, OLD); END IF;\n  IF TG_OP = 'TRUNCATE' THEN\n")),
    ("prospective: delete allowed", lambda: mutate("prospective", "  RAISE EXCEPTION 'brahma_prospective_ledger_frozen_row_guard: filed standing predictions cannot be deleted", "  RETURN OLD; RAISE EXCEPTION 'brahma_prospective_ledger_frozen_row_guard: filed standing predictions cannot be deleted")),
    ("prospective: claim allow-listed", lambda: mutate("prospective", "ARRAY['lifecycle_status', 'matched_event_id',", "ARRAY['lifecycle_status', 'claim', 'matched_event_id',")),
    ("prospective: column comparison off", lambda: mutate("prospective", "IF v_new IS DISTINCT FROM v_old THEN", "IF false THEN")),
    ("prospective: any transition allowed", lambda: mutate("prospective", "      IF NOT COALESCE(\n           (OLD.lifecycle_status = 'open'", "      IF false AND NOT COALESCE(\n           (OLD.lifecycle_status = 'open'")),
    ("prospective: match record writable at any time", lambda: mutate("prospective", "AND NOT COALESCE(OLD.lifecycle_status = 'open' AND NEW.lifecycle_status = 'matched', false) THEN", "AND false THEN")),
    ("prospective: matched without a record accepted", lambda: mutate("prospective", "AND (NEW.matched_event_id IS NULL OR NEW.matched_at IS NULL) THEN", "AND false THEN")),
    ("prospective: TRUNCATE branch removed", lambda: mutate("prospective", "  IF TG_OP = 'TRUNCATE' THEN\n    RAISE EXCEPTION", "  IF false THEN\n    RAISE EXCEPTION")),
    ("manifestation: update allowed", lambda: mutate("manifestation", "IF to_jsonb(NEW) IS DISTINCT FROM to_jsonb(OLD) THEN", "IF false THEN")),
    ("manifestation: delete allowed", lambda: mutate("manifestation", "  RAISE EXCEPTION 'mimamsa_manifestation_sets_frozen_row_guard: frozen manifestation sets cannot be deleted", "  RETURN OLD; RAISE EXCEPTION 'mimamsa_manifestation_sets_frozen_row_guard: frozen manifestation sets cannot be deleted")),
    ("manifestation: TRUNCATE branch removed", lambda: mutate("manifestation", "  IF TG_OP = 'TRUNCATE' THEN\n    RAISE EXCEPTION", "  IF false THEN\n    RAISE EXCEPTION")),
    ("bmpl: delete allowed", lambda: mutate("bmpl", "  RAISE EXCEPTION 'brahma_mimamsa_prediction_ledger_delete_guard: ledger rows cannot be deleted", "  RETURN OLD; RAISE EXCEPTION 'brahma_mimamsa_prediction_ledger_delete_guard: ledger rows cannot be deleted")),
    ("bmpl: TRUNCATE branch removed", lambda: mutate("bmpl", "  IF TG_OP = 'TRUNCATE' THEN\n    RAISE EXCEPTION", "  IF false THEN\n    RAISE EXCEPTION")),
    ("withdrawal helper ignores the consent state", lambda: mutate("helper", "WHERE c.chart_id = p_chart AND c.consent_state = 'withdrawn')", "WHERE c.chart_id = p_chart)")),
    ("withdrawal helper ignores open disputes", lambda: mutate("helper", "\n       AND NOT EXISTS (SELECT 1 FROM public.chart_subject_deletion_disputes d\n                        WHERE d.chart_id = p_chart AND d.status IN ('open', 'reopened', 'escalated'))", "")),
    ("withdrawal helper fails open", lambda: mutate("helper", "    v_authorized := false;\n  END;", "    v_authorized := true;\n  END;")),
    ("cascade: depth test removed (chart-absence alone)", lambda: mutate("cascade", "p_chart IS NULL OR pg_trigger_depth() < 2 OR", "p_chart IS NULL OR")),
    ("cascade: chart-absence test removed (depth alone)", lambda: mutate("cascade", "SELECT NOT EXISTS (SELECT 1 FROM public.charts c WHERE c.id = p_chart) INTO v_gone;", "SELECT true INTO v_gone;")),
    ("cascade: depth threshold 1 (direct delete passes for an absent chart)", lambda: mutate("cascade", "pg_trigger_depth() < 2", "pg_trigger_depth() < 1")),
    ("cascade: fails open on an unreadable charts table", lambda: mutate("cascade", "    v_gone := false;\n  END;", "    v_gone := true;\n  END;")),
    ("cascade: cascade allowance removed from the guards", lambda: REAL.replace("IF public.l5_frozen_chart_cascade_authorizes(OLD.chart_id) THEN", "IF false AND public.l5_frozen_chart_cascade_authorizes(OLD.chart_id) THEN")),
]
# the last mutant edits four guard bodies at once: re-pin each


def _last():
    sql = REAL
    for tag in ("predictions", "prospective", "manifestation", "bmpl"):
        b = body(sql, tag)
        old_md5 = hashlib.md5(b.encode()).hexdigest()
        sql = _repin(sql.replace(b, b.replace("IF public.l5_frozen_chart_cascade_authorizes(OLD.chart_id) THEN", "IF false AND public.l5_frozen_chart_cascade_authorizes(OLD.chart_id) THEN")), tag, old_md5)
    return sql


MUTANTS[-1] = ("cascade: cascade allowance removed from the guards", _last)


@pytest.mark.parametrize("name,make", MUTANTS, ids=[m[0] for m in MUTANTS])
def test_mutant_is_caught_by_the_behaviour_probes_with_the_in_script_self_test_removed(pg_cluster, name, make):
    w = _fresh(pg_cluster, _strip_selftest(make()))
    try:
        failed = run_probes(w)
    finally:
        drop_world(pg_cluster, w)
    assert failed, "mutant survived the probes: " + name


SELFTEST_NAMES = {"predictions: delete refusal removed", "predictions: pending exempt from delete", "predictions: column comparison off", "predictions: source_pramana_id allow-listed",
                  "predictions: pending exempt from the column check", "predictions: terminal statuses mutable", "predictions: unknown target status accepted",
                  "prospective: delete allowed", "prospective: claim allow-listed", "prospective: column comparison off", "prospective: any transition allowed",
                  "prospective: match record writable at any time", "prospective: matched without a record accepted",
                  "manifestation: update allowed", "manifestation: delete allowed", "bmpl: delete allowed"}
SELFTEST_CATCHES = [m for m in MUTANTS if m[0] in SELFTEST_NAMES]
assert len(SELFTEST_CATCHES) == len(SELFTEST_NAMES)


@pytest.mark.parametrize("name,make", SELFTEST_CATCHES, ids=[m[0] for m in SELFTEST_CATCHES])
def test_the_same_mutants_are_caught_by_the_scripts_own_self_test(pg_cluster, name, make):
    w = make_world(pg_cluster)
    try:
        psy = pg_cluster["psycopg"]
        with pytest.raises(psy.errors.RaiseException, match="1265 self-test FAILED"):
            w.apply_sql(make())
    finally:
        drop_world(pg_cluster, w)


FILE_MUTANTS = [
    ("md5 guard on the builder body neutered", lambda s: s.replace("IF f.body_md5 <> '46c23854275c2712b30860a2b174adb2' OR f.body_len <> 1084 THEN", "IF false THEN")),
    ("builder trigger shape check neutered", lambda s: s.replace("ELSIF t.tgtype <> 15 OR", "ELSIF false AND t.tgtype <> 15 OR")),
    ("changed-live-guard refusal neutered", lambda s: s.replace("IF EXISTS (SELECT 1 FROM pg_proc p WHERE p.oid = to_regprocedure('public.' || rec.sig) AND md5(p.prosrc) <> rec.want) THEN", "IF false THEN")),
    ("recorded-grant assertion neutered", lambda s: s.replace("IF privs IS DISTINCT FROM 'DELETE,INSERT,SELECT' OR grantor IS DISTINCT FROM 'amjis_app' OR n <> 1 THEN", "IF false THEN")),
    ("repo-object assertion neutered", lambda s: s.replace("IF NOT FOUND OR f.md5 <> '70c2ddb261d703fa6a33a4feaf39c99c' THEN", "IF false THEN")),
    ("ENABLE ALWAYS dropped", lambda s: s.replace("EXECUTE format('ALTER TABLE public.%I ENABLE ALWAYS TRIGGER %I', rec.tbl, rec.trg);", "NULL;")),
    ("truncate triggers dropped", lambda s: s.replace("        EXECUTE format('CREATE TRIGGER %I BEFORE TRUNCATE ON public.%I FOR EACH STATEMENT EXECUTE FUNCTION public.%I()', rec.trg, rec.tbl, rec.fn);", "        NULL;")),
    ("privilege gate neutered", lambda s: s.replace("IF NOT has_schema_privilege(current_user, 'public', 'CREATE') THEN", "IF false THEN")),
]


def test_file_mutants_change_the_file(pg_cluster):
    for name, f in FILE_MUTANTS:
        assert f(REAL) != REAL, name


def test_file_mutant_gate_neutered_is_caught_by_the_privilege_test(world):
    psy = world.pg["psycopg"]
    with pytest.raises(psy.errors.InsufficientPrivilege, match="permission denied for schema public"):
        world.apply_sql(dict(FILE_MUTANTS)["privilege gate neutered"](REAL), window=False)


def test_file_mutant_enable_always_dropped_is_caught_by_the_post_check_and_by_the_replica_probe(pg_cluster):
    mutant = dict(FILE_MUTANTS)["ENABLE ALWAYS dropped"](REAL)
    w = make_world(pg_cluster)
    try:
        psy = pg_cluster["psycopg"]
        with pytest.raises(psy.errors.RaiseException, match="post-check: expected 11"):
            w.apply_sql(mutant)
        w.apply_sql(_strip_selftest(mutant).replace("  IF bad <> 11 THEN", "  IF false AND bad <> 11 THEN"))
        add_chart_fks(w)
        assert any("replica" in f for f in run_probes(w))
    finally:
        drop_world(pg_cluster, w)


def test_file_mutant_truncate_triggers_dropped_is_caught_by_the_post_check_and_the_truncate_probes(pg_cluster):
    mutant = dict(FILE_MUTANTS)["truncate triggers dropped"](REAL)
    w = make_world(pg_cluster)
    try:
        psy = pg_cluster["psycopg"]
        with pytest.raises(Exception):
            w.apply_sql(mutant)                                    # ALTER TABLE ... ENABLE ALWAYS TRIGGER ..._truncate: no such trigger
        with pytest.raises(psy.errors.RaiseException, match="1265 self-test FAILED.*TRUNCATE"):      # the in-script self-test also catches it (the owner holds TRUNCATE on these three)
            w.apply_sql(mutant.replace("EXECUTE format('ALTER TABLE public.%I ENABLE ALWAYS TRIGGER %I', rec.tbl, rec.trg);",
                                       "IF EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = rec.trg) THEN EXECUTE format('ALTER TABLE public.%I ENABLE ALWAYS TRIGGER %I', rec.tbl, rec.trg); END IF;"))
        w.apply_sql(_strip_selftest(mutant.replace("EXECUTE format('ALTER TABLE public.%I ENABLE ALWAYS TRIGGER %I', rec.tbl, rec.trg);",
                                                   "IF EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = rec.trg) THEN EXECUTE format('ALTER TABLE public.%I ENABLE ALWAYS TRIGGER %I', rec.tbl, rec.trg); END IF;"))
                    .replace("  IF bad <> 11 THEN", "  IF false AND bad <> 11 THEN"))
        add_chart_fks(w)
        assert any("truncate" in f for f in run_probes(w))
    finally:
        drop_world(pg_cluster, w)


@pytest.mark.parametrize("name", ["md5 guard on the builder body neutered", "builder trigger shape check neutered", "changed-live-guard refusal neutered",
                                  "recorded-grant assertion neutered", "repo-object assertion neutered"])
def test_file_mutants_that_neuter_an_assertion_are_caught_by_the_refusal_tests(pg_cluster, name):
    mutant = dict(FILE_MUTANTS)[name](REAL)
    w = make_world(pg_cluster)
    try:
        psy = pg_cluster["psycopg"]
        if name.startswith("md5 guard"):
            _window_exec(w, "CREATE OR REPLACE FUNCTION public.mimamsa_predictions_builder_guard() RETURNS trigger LANGUAGE plpgsql SECURITY INVOKER SET search_path = pg_catalog, pg_temp "
                         "AS $g$" + body(REAL, "guard").replace("'pending', 'due'", "'pending', 'due', 'confirmed'") + "$g$")
        elif name.startswith("builder trigger"):
            w.exec("DROP TRIGGER mimamsa_predictions_builder_guard ON mimamsa_predictions; CREATE TRIGGER mimamsa_predictions_builder_guard BEFORE INSERT ON mimamsa_predictions "
                   "FOR EACH ROW EXECUTE FUNCTION public.mimamsa_predictions_builder_guard()", role="amjis_app")
        elif name.startswith("changed-live"):
            w.apply_sql(REAL)
            _window_exec(w, "CREATE OR REPLACE FUNCTION public.mimamsa_predictions_frozen_row_guard() RETURNS trigger LANGUAGE plpgsql AS $g$ BEGIN RETURN NEW; END $g$")
        elif name.startswith("recorded-grant"):
            w.exec("REVOKE DELETE ON mimamsa_predictions FROM data_plane_builder", role="amjis_app")
        else:
            _window_exec(w, "CREATE OR REPLACE FUNCTION public.bmpl_freeze_confirmed() RETURNS trigger LANGUAGE plpgsql AS $x$ BEGIN RETURN NEW; END $x$")
        with pytest.raises(psy.errors.RaiseException):
            w.apply_sql(REAL)                                      # the real file refuses...
        w.apply_sql(mutant)                                        # ...the mutant does not (that is what makes the refusal test non-vacuous)
    finally:
        drop_world(pg_cluster, w)


# ================================================================ I. RLS assessment (migration 576's g1c policies)

def _install_g1c(w):
    w.exec("""
CREATE OR REPLACE FUNCTION app_chart_context() RETURNS uuid LANGUAGE plpgsql STABLE PARALLEL SAFE AS $ctx$
DECLARE
  raw text;
BEGIN
  raw := nullif(current_setting('app.chart_context', true), '');
  IF raw IS NULL THEN
    RETURN NULL;
  END IF;
  BEGIN
    RETURN raw::uuid;
  EXCEPTION WHEN others THEN
    RETURN NULL;   -- malformed pin == no pin == deny
  END;
END
$ctx$;
GRANT EXECUTE ON FUNCTION app_chart_context() TO PUBLIC;
CREATE POLICY mimamsa_predictions_g1c_chart_context ON mimamsa_predictions AS PERMISSIVE FOR ALL TO role_web_serve, role_sidecar
  USING (chart_id = app_chart_context()) WITH CHECK (chart_id = app_chart_context());
CREATE POLICY mimamsa_predictions_g1c_unscoped ON mimamsa_predictions AS PERMISSIVE FOR ALL TO role_orchestrator, role_ledger_write, role_jobs
  USING (true) WITH CHECK (true);
""")


def _count(w, role, pin=None):
    with w.connect(role) as c:
        if pin:
            c.execute("SET app.chart_context = '" + pin + "'")
        n = c.execute("SELECT count(*) FROM mimamsa_predictions").fetchone()[0]
        c.rollback()
        return n


def test_rls_arming_is_within_the_routine_role_but_hides_every_row_from_roles_without_a_policy(world):
    _install_g1c(world)
    world.exec("ALTER TABLE mimamsa_predictions ENABLE ROW LEVEL SECURITY", role="amjis_app")        # the owner can: no protected step
    assert world.query("SELECT relrowsecurity, relforcerowsecurity FROM pg_class WHERE oid = 'mimamsa_predictions'::regclass") == [(True, False)]
    psy = world.pg["psycopg"]
    with world.connect("role_orchestrator") as c:
        with pytest.raises(psy.errors.InsufficientPrivilege):
            c.execute("ALTER TABLE mimamsa_predictions DISABLE ROW LEVEL SECURITY")
    total = 10
    assert _count(world, "amjis_app") == total and _count(world, "postgres") == total
    assert _count(world, "role_orchestrator") == total and _count(world, "role_ledger_write") == total and _count(world, "role_jobs") == total
    assert _count(world, "role_web_serve") == 0 and _count(world, "role_web_serve", CHART_A) == 7 and _count(world, "role_web_serve", CHART_B) == 2
    assert _count(world, "amjis_inquiry_serve") == 0 and _count(world, "amjis_inquiry_serve", CHART_B) == 2
    assert _count(world, "role_sidecar") == 0 and _count(world, "role_sidecar", CHART_C) == 1
    for role in ("suvarna_reader", "retrieval_census_ro", "nirmana_evidence_ingress_writer", "data_plane_builder"):
        assert _count(world, role) == 0, role


def test_rls_arming_breaks_the_data_plane_builder_silently_on_delete_and_loudly_on_insert(world):
    _install_g1c(world)
    world.exec("ALTER TABLE mimamsa_predictions ENABLE ROW LEVEL SECURITY", role="amjis_app")
    psy = world.pg["psycopg"]
    with world.connect("data_plane_builder") as c:
        assert c.execute("DELETE FROM mimamsa_predictions WHERE chart_id = %s AND lifecycle_status IN ('pending','due')", (CHART_A,)).rowcount == 0
        with pytest.raises(psy.errors.InsufficientPrivilege, match="row-level security"):
            c.execute(pred_row(CHART_C, "pred_new"))


def test_rls_pin_is_client_asserted_so_a_serving_session_can_re_pin_itself(world):
    _install_g1c(world)
    world.exec("ALTER TABLE mimamsa_predictions ENABLE ROW LEVEL SECURITY", role="amjis_app")
    with world.connect("role_web_serve") as c:
        c.execute("SET app.chart_context = '" + CHART_A + "'")
        assert c.execute("SELECT count(*) FROM mimamsa_predictions").fetchone()[0] == 7
        c.execute("SET app.chart_context = '" + CHART_B + "'")
        assert c.execute("SELECT count(*) FROM mimamsa_predictions").fetchone()[0] == 2


def test_rls_does_not_provide_immutability_without_1265(world):
    _install_g1c(world)
    world.exec("ALTER TABLE mimamsa_predictions ENABLE ROW LEVEL SECURITY", role="amjis_app")
    assert passes(world, "amjis_app", "UPDATE mimamsa_predictions SET source_pramana_id = 'x'") == 10
    assert passes(world, "role_orchestrator", "UPDATE mimamsa_predictions SET source_pramana_id = 'x'") == 10
    assert passes(world, "role_orchestrator", "DELETE FROM mimamsa_predictions WHERE lifecycle_status = 'pending'") == 6


def test_with_rls_armed_and_1265_applied_the_guards_hold_independently_of_rls(world):
    world.apply_sql(REAL)
    _install_g1c(world)
    world.exec("ALTER TABLE mimamsa_predictions ENABLE ROW LEVEL SECURITY", role="amjis_app")
    refused(world, "amjis_app", "UPDATE mimamsa_predictions SET source_pramana_id = 'x'", prefix=P_PRED)
    refused(world, "role_orchestrator", "DELETE FROM mimamsa_predictions WHERE lifecycle_status = 'pending'", prefix=P_PRED)
    with world.connect("data_plane_builder") as c:
        assert c.execute("DELETE FROM mimamsa_predictions WHERE chart_id = %s", (CHART_A,)).rowcount == 0      # RLS hides the rows; the guard never sees it


def test_ONE_FIXTURE_direct_delete_refused_then_chart_delete_removes_every_row_of_that_chart_only(cascaded):
    """The N-108 acceptance test, in one fixture (the one migration 1275 can reuse): the four tables carry the 1275 cascade FKs, the guards are on."""
    a0, b0, c0 = counts(cascaded, CHART_A), counts(cascaded, CHART_B), counts(cascaded, CHART_C)
    # 1. a direct DELETE of a prediction whose chart still exists is refused, in every table, for the owner and a superuser
    for role in ("amjis_app", "postgres"):
        refused(cascaded, role, "DELETE FROM mimamsa_predictions WHERE chart_id = %s AND prediction_id = 'pred_a0'", (CHART_A,), prefix=P_PRED)
        refused(cascaded, role, "DELETE FROM mimamsa_manifestation_sets WHERE chart_id = %s", (CHART_A,), prefix=P_MAN)
        refused(cascaded, role, "DELETE FROM brahma_prospective_ledger WHERE chart_id = %s", (CHART_A,), prefix=P_PRO)
        refused(cascaded, role, "DELETE FROM brahma_mimamsa_prediction_ledger WHERE chart_id = %s", (CHART_A,), prefix=P_BMPL)
    assert counts(cascaded, CHART_A) == a0
    # 2. faking the condition does not help
    psy = cascaded.pg["psycopg"]
    with cascaded.connect("amjis_app") as c:
        c.execute("SET LOCAL madhav.chart_deleted = 'on'")
        with pytest.raises(psy.errors.InsufficientPrivilege, match="frozen_row_guard"):
            c.execute("DELETE FROM mimamsa_predictions WHERE chart_id = %s", (CHART_A,))
    # 3. deleting the chart itself removes every row of that chart in all four tables and nothing of any other chart
    cascaded.exec("DELETE FROM charts WHERE id = %s", (CHART_A,), role="amjis_app")
    assert counts(cascaded, CHART_A) == {t: 0 for t in CASCADE_TABLES}
    assert counts(cascaded, CHART_B) == b0 and counts(cascaded, CHART_C) == c0
    # 4. the guard is still on afterwards
    refused(cascaded, "amjis_app", "DELETE FROM mimamsa_predictions WHERE chart_id = %s", (CHART_B,), prefix=P_PRED)


# ================================================================ J. the order of 1265 and 1275 does not matter (same window)

def test_applying_with_the_1275_foreign_keys_already_present_the_self_test_hangs_on_an_existing_chart_and_touches_no_real_row(pg_cluster):
    """REAL FINDING the demo run exposed: the self-test's probe rows used a random chart_id, which the 1275 FKs reject. It now hangs the probes on an existing
    chart and scopes every statement to the probe's own key."""
    w = make_world(pg_cluster)
    try:
        add_chart_fks(w)
        before = w.catalog_state()["rowdata"]
        w.apply_sql(REAL)
        assert w.catalog_state()["rowdata"] == before
        refused(w, "amjis_app", "DELETE FROM mimamsa_predictions WHERE chart_id = %s", (CHART_A,), prefix=P_PRED)
        w.exec("DELETE FROM charts WHERE id = %s", (CHART_A,), role="amjis_app")
        assert counts(w, CHART_A) == {t: 0 for t in CASCADE_TABLES}
        w.apply_sql(REAL)                                                      # re-run after a chart delete: probes hang on another existing chart
    finally:
        drop_world(pg_cluster, w)


def test_with_the_foreign_keys_present_and_no_chart_at_all_the_self_test_cannot_run_and_the_file_fails_closed(pg_cluster):
    w = make_world(pg_cluster, seed=False)
    try:
        w.exec("INSERT INTO brahma_event_ontology VALUES ('ec_x','interval')")
        add_chart_fks(w)
        psy = pg_cluster["psycopg"]
        with pytest.raises(psy.errors.ForeignKeyViolation):
            w.apply_sql(REAL)
        assert w.query("SELECT count(*) FROM pg_proc WHERE proname LIKE '%frozen%'") == [(0,)]
    finally:
        drop_world(pg_cluster, w)
