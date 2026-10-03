"""Mirror tests on a disposable PostgreSQL holding production's roles, schema-public owner/ACL, phala_pramana (columns, constraints, indexes, owner, ACL) and the
objects the executor reads, with SYNTHETIC rows. The executor runs as the administrator role (non-superuser CREATEROLE), exactly as in production.

Shown here: the dry run shows EXACTLY the 8 bound ids and changes nothing; the apply deletes exactly those 8 (nothing else moves); matching-looking rows (another
chart, another marker) are NOT deleted; the executor REFUSES with 7 or 9 matching rows, with different ids, a different fingerprint, a life-event payload, a
dependent, a foreign key, a new referencing column, a build in flight, a trigger / rule / view / inheritance / RLS, the wrong database / role / server major version,
a different interpreter; and a MUTATION of every safeguard (SQL and python layers separately) is refused with nothing committed.
"""
from __future__ import annotations

import json
import pathlib
import re

import psycopg
import pytest

import conftest as cf
from conftest import ADMIN_USER, CHART, OTHER_CHART, PROD_PHALA_PRAMANA_ACL

pytestmark = pytest.mark.usefixtures("cluster")

IDS = ["649c5828-ba9c-4ca8-9a7f-6ace81fad2e3", "767b84b4-4090-4383-a9a9-ada59a509b1d", "a3c855bb-9698-4c43-bb6b-c85ad1ec0a84",
       "adcfd0d2-e748-4741-9df5-619ad1e8d271", "c4fd0d7c-7502-4b63-bb61-8b693c38375b", "ccdf5abd-6339-48dc-adac-39d8877f2629",
       "db6cc6a0-91a5-4f2e-89ea-33c4fd23fc5c", "f44dea24-ada4-405d-bba7-fe094ce8e1e6"]
PROD_FP = "bf270a4b5b3612827e5ea85885538a99ca4147fd62f1a86882c831c0ff21a4b6"
FP_SQL = ("SELECT encode(sha256(convert_to(string_agg(concat_ws('|', pramana_id::text, chart_id::text, anchor_id::text, evidence_type, evidence_strength_label, window_status, "
          "(lel_entry_id IS NULL)::text, (lel_entry_jsonb IS NULL)::text, extract(epoch FROM computed_at)::text), E'\\n' ORDER BY pramana_id), 'UTF8')), 'hex') "
          "FROM public.phala_pramana WHERE chart_id = %s AND evidence_type = 'life_event_miss'")


def n(runner, sql, params=None):
    return runner.su(sql, params)[0][0]


def evidence_text(root) -> str:
    out = []
    for p in sorted(pathlib.Path(root).rglob("*")):
        if p.is_file():
            out.append(p.read_text(errors="replace"))
    return "\n".join(out)


# ---------------------------------------------------------------------------------------------------------------- the mirror itself
def test_the_mirror_is_production_shaped(cluster, db, runner):
    assert n(runner, "SELECT relacl::text FROM pg_class WHERE oid='public.phala_pramana'::regclass") == PROD_PHALA_PRAMANA_ACL
    assert n(runner, "SELECT pg_get_userbyid(relowner) FROM pg_class WHERE oid='public.phala_pramana'::regclass") == "amjis_app"
    assert n(runner, "SELECT relrowsecurity OR relforcerowsecurity FROM pg_class WHERE oid='public.phala_pramana'::regclass") is False
    # production: 5 constraints (pkey, anchor FK ON DELETE CASCADE, three CHECKs), no user trigger, only the two internal RI triggers of the FK
    assert n(runner, "SELECT count(*) FROM pg_constraint WHERE conrelid='public.phala_pramana'::regclass") == 5
    assert n(runner, "SELECT count(*) FROM pg_constraint WHERE confrelid='public.phala_pramana'::regclass") == 0
    assert n(runner, "SELECT count(*) FROM pg_trigger WHERE tgrelid='public.phala_pramana'::regclass AND NOT tgisinternal") == 0
    assert n(runner, "SELECT count(*) FROM pg_trigger WHERE tgrelid='public.phala_pramana'::regclass AND tgisinternal") == 2
    # production's shape: 56 rows for the bound chart (8 life_event_miss + 3 open + 45 pending), 4 for the canonical chart
    assert n(runner, "SELECT string_agg(chart_id::text||':'||n::text, ',' ORDER BY chart_id) FROM (SELECT chart_id, count(*) n FROM public.phala_pramana GROUP BY 1) s") == \
        f"{CHART}:56,{OTHER_CHART}:4"
    assert n(runner, "SELECT count(*) FROM public.phala_pramana WHERE chart_id=%s AND evidence_type='life_event_miss'", (CHART,)) == 8
    # the 8 rows' non-private fingerprint, computed by the executor's own expression, equals the value measured on PRODUCTION
    assert n(runner, FP_SQL, (CHART,)) == PROD_FP
    # roles: the builder holds exactly SELECT, INSERT, DELETE (no UPDATE / TRUNCATE); the reader nothing that writes; the administrator is CREATEROLE, not a superuser,
    # has no USAGE on public and is a member of none of the roles it will assume
    assert n(runner, "SELECT has_table_privilege('data_plane_builder','public.phala_pramana','SELECT,INSERT,DELETE')") is True
    assert n(runner, "SELECT has_table_privilege('data_plane_builder','public.phala_pramana','UPDATE')") is False
    assert n(runner, "SELECT has_table_privilege('data_plane_builder','public.phala_pramana','TRUNCATE')") is False
    assert n(runner, "SELECT has_table_privilege('suvarna_reader','public.phala_pramana','INSERT,UPDATE,DELETE,TRUNCATE')") is False
    assert n(runner, "SELECT has_table_privilege('data_plane_builder','public.mimamsa_fact_adjustment','SELECT')") is False       # why the reads run as suvarna_reader
    assert n(runner, f"SELECT rolcreaterole AND NOT rolsuper FROM pg_roles WHERE rolname='{ADMIN_USER}'") is True
    assert n(runner, f"SELECT has_schema_privilege('{ADMIN_USER}','public','USAGE')") is False
    assert n(runner, f"SELECT pg_has_role('{ADMIN_USER}','data_plane_builder','MEMBER') OR pg_has_role('{ADMIN_USER}','suvarna_reader','MEMBER')") is False
    assert cluster.su(db, "SHOW server_version_num")[0][0].startswith("15")


# ------------------------------------------------------------------------------------------------------------------- dry run / apply
def test_dry_run_shows_exactly_the_8_ids_and_changes_nothing(runner, mod, capsys):
    before = runner.state()
    code, res = runner.run("dry-run")
    assert code == 0, (res["failed_checks"], res["details"])
    assert res["status"] == "DRY_RUN_ROLLED_BACK_ALL_CHECKS_HOLD" and res["failed_checks"] == []
    assert res["deleted_ids"] == IDS and res["rows_deleted_in_transaction"] == 8              # the dry run SHOWS exactly the 8, by id
    assert (res["chart_total_before"], res["chart_total_after"]) == (56, 48)
    assert res["other_charts_before"] == res["other_charts_after"] == {OTHER_CHART: 4}
    assert res["deleted_rows_nonprivate_fingerprint_sha256"] == PROD_FP
    assert runner.state() == before                                  # ROLLBACK: nothing at all moved
    assert len(res["evidence_digest"]) == 64
    outcome = json.loads((pathlib.Path(res["evidence_dir"]) / "outcome.json").read_text())
    assert outcome["status"] == "dry_run" and outcome["plan_hash"] == res["plan_hash"] and outcome["evidence_digest"] == res["evidence_digest"]
    assert outcome["python_executable"] and outcome["python_version"] and outcome["psycopg_version"] and outcome["libpq_version"]
    assert outcome["deleted_ids"] == IDS and outcome["rows_deleted_in_transaction"] == 8
    assert outcome["chart_total_before"] == 56 and outcome["chart_total_after"] == 48
    assert outcome["other_charts_before"] == outcome["other_charts_after"] == {OTHER_CHART: 4}
    assert outcome["deleted_rows_nonprivate_fingerprint_sha256"] == PROD_FP
    assert outcome["transaction_committed"] is False and outcome["irreversible"] is True and "PR #3047" in outcome["restore"]
    # NO private content anywhere: every private column of the synthetic rows holds a PRIVMARK, none of which may appear in a file or in the output
    assert "PRIVMARK" not in evidence_text(pathlib.Path(res["evidence_dir"]).parent)
    cap = capsys.readouterr()
    assert "PRIVMARK" not in cap.out + cap.err
    names = set(res["checks"])
    for expected in ("step_s1_assume_roles", "step_s2_preconditions_as_reader", "step_s3_delete_as_builder", "step_s4_post_assertions_as_reader",
                     "step_s5_restore_memberships", "m_pre_fingerprint_equals_the_pinned_one", "m_post_the_8_ids_are_gone", "post_memberships_restored"):
        assert expected in names, expected


def test_apply_deletes_exactly_the_8_and_nothing_else_moves(runner, mod, capsys):
    before = runner.state()
    code, res = runner.run("apply")
    assert code == 0 and res["status"] == "COMMITTED", (res.get("failed_checks"), res.get("details"))
    after = runner.state()
    assert after["pramana_n"] == before["pramana_n"] - 8
    assert n(runner, "SELECT count(*) FROM public.phala_pramana WHERE pramana_id = ANY(%s::uuid[])", (IDS,)) == 0
    assert after["by_chart"] == f"{CHART}:48,{OTHER_CHART}:4"
    assert n(runner, "SELECT count(*) FROM public.phala_pramana WHERE chart_id=%s AND evidence_type='life_event_miss'", (CHART,)) == 0
    # everything else byte-identical: schema ACL, every table ACL and owner, memberships (nothing left over), constraints, triggers, object set, anchors, dependents
    for k in ("schema_acl", "schema_owner", "table_acls", "memberships", "constraints", "triggers", "objects", "anchors", "others"):
        assert after[k] == before[k], k
    # the surviving rows are exactly the pre-image minus the 8 (compared by content, as the superuser)
    outcome = json.loads((pathlib.Path(res["evidence_dir"]) / "outcome.json").read_text())
    assert outcome["status"] == "applied" and outcome["transaction_committed"] is True and outcome["after_is_measured_inside_the_transaction"] is False
    assert outcome["deleted_ids"] == IDS and outcome["chart_total_before"] == 56 and outcome["chart_total_after"] == 48
    assert outcome["other_charts_before"] == outcome["other_charts_after"] == {OTHER_CHART: 4}
    assert outcome["deleted_rows_nonprivate_fingerprint_sha256"] == PROD_FP
    assert "PRIVMARK" not in evidence_text(pathlib.Path(res["evidence_dir"]).parent)
    cap = capsys.readouterr()
    assert "PRIVMARK" not in cap.out + cap.err
    # the surviving 48 + 4 rows still hold their (synthetic) private columns untouched
    assert n(runner, "SELECT count(*) FROM public.phala_pramana WHERE falsifier_text LIKE 'PRIVMARK-%'") == 52


def test_matching_looking_rows_are_not_deleted(runner, mod):
    """A 9th matching-LOOKING row is never touched: another chart with the same marker, the same chart with another marker, and the same chart with the same marker
    is a different matter (it makes 9 matches and is REFUSED, see test_nine_matching_rows_are_refused)."""
    runner.su("INSERT INTO public.phala_anchors (anchor_id, chart_id) VALUES ('d0000001-0000-4000-8000-000000000001', %s), ('d0000001-0000-4000-8000-000000000002', %s), "
              "('d0000001-0000-4000-8000-000000000003', %s)", (OTHER_CHART, CHART, CHART))
    runner.su("INSERT INTO public.phala_pramana (pramana_id, chart_id, anchor_id, evidence_type, evidence_strength_label, falsifier_text, observable_criteria_jsonb, window_status, "
              "derivation_ledger_jsonb, source_citation) VALUES "
              "('d1000001-0000-4000-8000-000000000001', %s, 'd0000001-0000-4000-8000-000000000001', 'life_event_miss', 'indirect', 'PRIVMARK-d1', '{}', 'past_window', '{}', 'PRIVMARK'),"
              "('d1000001-0000-4000-8000-000000000002', %s, 'd0000001-0000-4000-8000-000000000002', 'detector_unavailable', 'indirect', 'PRIVMARK-d2', '{}', 'past_window', '{}', 'PRIVMARK'),"
              "('d1000001-0000-4000-8000-000000000003', %s, 'd0000001-0000-4000-8000-000000000003', 'life_event_match', 'direct', 'PRIVMARK-d3', '{}', 'past_window', '{}', 'PRIVMARK')",
              (OTHER_CHART, CHART, CHART))
    before = runner.state()
    code, res = runner.run("apply")
    assert code == 0 and res["status"] == "COMMITTED", (res.get("failed_checks"), res.get("details"))
    assert res["deleted_ids"] == IDS and res["chart_total_before"] == 58 and res["chart_total_after"] == 50
    after = runner.state()
    assert after["pramana_n"] == before["pramana_n"] - 8
    for decoy in ("d1000001-0000-4000-8000-000000000001", "d1000001-0000-4000-8000-000000000002", "d1000001-0000-4000-8000-000000000003"):
        assert n(runner, "SELECT count(*) FROM public.phala_pramana WHERE pramana_id = %s", (decoy,)) == 1, decoy
    assert after["by_chart"] == f"{CHART}:50,{OTHER_CHART}:5"


def test_applying_twice_is_refused(runner):
    assert runner.run("apply")[0] == 0
    before = runner.state()
    code, res = runner.run("apply")
    assert code in (1, 2) and "m_pre_exactly_8_rows_match_chart_and_marker" in res["failed_checks"]
    assert runner.state() == before


def test_a_wrong_plan_or_evidence_is_refused_and_changes_nothing(runner, mod):
    before = runner.state()
    with pytest.raises(SystemExit):
        runner.execute(runner.args("dry-run", expect_plan="0" * 64))
    code, res = runner.execute(runner.args("apply", expect_evidence="0" * 64))
    assert code == 1 and res["status"] == "REFUSED_ROLLED_BACK" and "evidence_digest_matches_expected" in res["failed_checks"]
    assert runner.state() == before
    with pytest.raises(SystemExit):
        mod.parse_args(["--apply", "--expect-plan", mod.plan_hash()])          # --apply without --expect-evidence
    with pytest.raises(SystemExit):
        mod.parse_args(["--dry-run"])                                          # no --expect-plan
    with pytest.raises(SystemExit):
        mod.parse_args(["--rollback", "--expect-plan", mod.plan_hash()])       # there is no rollback leg


def test_a_stale_dry_run_digest_is_refused_when_the_state_moved(runner):
    code, dry = runner.run("dry-run")
    assert code == 0
    runner.su("INSERT INTO public.build_runs (chart_id, state) VALUES (%s, 'completed')", (OTHER_CHART,))      # harmless, but the state is no longer the one dry-run saw
    runner.su("INSERT INTO public.phala_anchors (anchor_id, chart_id) VALUES ('d0000002-0000-4000-8000-000000000001', %s)", (OTHER_CHART,))
    runner.su("INSERT INTO public.phala_pramana (chart_id, anchor_id, evidence_type, evidence_strength_label, falsifier_text, observable_criteria_jsonb, window_status, "
              "derivation_ledger_jsonb, source_citation) VALUES (%s, 'd0000002-0000-4000-8000-000000000001', 'pending_observation', 'indirect', 'PRIVMARK', '{}', 'open', '{}', 'PRIVMARK')",
              (OTHER_CHART,))
    before = runner.state()
    code, res = runner.execute(runner.args("apply", expect_evidence=dry["evidence_digest"]))
    assert code == 1 and res["status"] == "REFUSED_ROLLED_BACK" and "evidence_digest_matches_expected" in res["failed_checks"]
    assert runner.state() == before


def test_count_mode_reads_only_and_deletes_nothing(runner):
    before = runner.state()
    code, res = runner.run("count")
    assert code == 0 and res["status"] == "COUNT_READ_ONLY_OK" and runner.state() == before
    assert res["deleted_ids"] == [] and res["chart_total_before"] == 56 and res["chart_total_after"] is None
    assert "step_s3_delete_as_builder" not in res["checks"]


def test_the_unmutated_plan_is_green_so_the_refusals_are_what_turns_it_red(runner):
    assert runner.run("dry-run")[0] == 0


# ------------------------------------------------------------------------------------------------------------------- refusal helper
def assert_refused(runner, names, setup=None, user=None):
    """The state is changed by `setup`, then: a dry run is REFUSED (exit 2) with every named check failed, rolls back, deletes nothing; an apply that names the dry
    run's digest is REFUSED (exit 1) and rolls back; the state image is byte-identical before and after."""
    if setup:
        setup()
    before = runner.state()
    code, dry = runner.execute(runner.args("dry-run"), user=user)
    assert code == 2 and dry["status"] == "DRY_RUN_ROLLED_BACK_REFUSED", (code, dry.get("failed_checks"))
    missing = [x for x in names if x not in dry["failed_checks"]]
    assert not missing, (missing, dry["failed_checks"], {k: v for k, v in dry["details"].items()})
    assert runner.state() == before
    code, res = runner.execute(runner.args("apply", expect_evidence=dry["evidence_digest"]), user=user)
    assert code == 1 and res["status"] == "REFUSED_ROLLED_BACK" and res["failed_checks"], res
    assert runner.state() == before
    return dry


def insert_pramana(runner, pid, chart, evidence_type, window="past_window", label="indirect", anchor_suffix=None):
    aid = "d0000009-0000-4000-8000-" + (anchor_suffix or pid[-12:])
    runner.su("INSERT INTO public.phala_anchors (anchor_id, chart_id) VALUES (%s, %s)", (aid, chart))
    runner.su("INSERT INTO public.phala_pramana (pramana_id, chart_id, anchor_id, evidence_type, evidence_strength_label, falsifier_text, observable_criteria_jsonb, window_status, "
              "derivation_ledger_jsonb, source_citation) VALUES (%s, %s, %s, %s, %s, 'PRIVMARK', '{}', %s, '{}', 'PRIVMARK')", (pid, chart, aid, evidence_type, label, window))


# ------------------------------------------------------------------------------------------------- the row-set refusals (7, 9, ids, fingerprint, payload)
def test_seven_matching_rows_are_refused(runner):
    assert_refused(runner, ["m_pre_exactly_8_rows_match_chart_and_marker", "step_s2_preconditions_as_reader"],
                   setup=lambda: runner.su("DELETE FROM public.phala_pramana WHERE pramana_id = %s", (IDS[0],)))


def test_nine_matching_rows_are_refused(runner):
    """A 9th (chart, life_event_miss) row: exactly-8 fails, although the 8 bound ids are all present and a delete of the bound ids alone would succeed."""
    assert_refused(runner, ["m_pre_exactly_8_rows_match_chart_and_marker", "step_s2_preconditions_as_reader"],
                   setup=lambda: insert_pramana(runner, "d1000009-0000-4000-8000-000000000009", CHART, "life_event_miss"))


def test_different_ids_are_refused_even_with_exactly_8_matching_rows(runner):
    assert_refused(runner, ["m_pre_matching_ids_equal_the_bound_ids", "m_pre_fingerprint_equals_the_pinned_one", "step_s2_preconditions_as_reader"],
                   setup=lambda: runner.su("UPDATE public.phala_pramana SET pramana_id = 'e1000009-0000-4000-8000-000000000009' WHERE pramana_id = %s", (IDS[3],)))


def test_a_changed_non_private_value_changes_the_fingerprint_and_is_refused(runner):
    assert_refused(runner, ["m_pre_fingerprint_equals_the_pinned_one", "step_s2_preconditions_as_reader"],
                   setup=lambda: runner.su("UPDATE public.phala_pramana SET evidence_strength_label = 'direct' WHERE pramana_id = %s", (IDS[0],)))
    # while a changed PRIVATE column is by design not part of the fingerprint (it is never read)


def test_a_row_carrying_a_life_event_payload_is_refused(runner):
    assert_refused(runner, ["m_pre_no_matching_row_carries_a_life_event_payload", "step_s2_preconditions_as_reader"],
                   setup=lambda: runner.su("UPDATE public.phala_pramana SET lel_entry_jsonb = '{\"summary\": \"PRIVMARK-payload\"}' WHERE pramana_id = %s", (IDS[0],)))
    assert_refused(runner, ["m_pre_no_matching_row_carries_a_life_event_payload"],
                   setup=lambda: runner.su("UPDATE public.phala_pramana SET lel_entry_id = 77 WHERE pramana_id = %s", (IDS[1],)))


# --------------------------------------------------------------------------------------------------------------------- dependents
DEPENDENTS = {
    "mimamsa_predictions_source_pramana_id": "INSERT INTO public.mimamsa_predictions (source_pramana_id) VALUES ('649c5828-ba9c-4ca8-9a7f-6ace81fad2e3')",
    "mimamsa_predictions_id_inside_the_body": "INSERT INTO public.mimamsa_predictions (body) VALUES ('{\"x\": {\"p\": \"f44dea24-ada4-405d-bba7-fe094ce8e1e6\"}}')",
    "mimamsa_predictions_shadow": "INSERT INTO public.mimamsa_predictions__ssv_20260728b (source_pramana_id) VALUES ('a3c855bb-9698-4c43-bb6b-c85ad1ec0a84')",
    "mimamsa_anchor_adjustment_array": "INSERT INTO public.mimamsa_anchor_adjustment (derived_from_pramana_ids) VALUES ('[\"adcfd0d2-e748-4741-9df5-619ad1e8d271\"]')",
    "mimamsa_convergence_adjustment_nested": "INSERT INTO public.mimamsa_convergence_adjustment (derived_from_pramana_ids) VALUES ('{\"a\": [{\"id\": \"c4fd0d7c-7502-4b63-bb61-8b693c38375b\"}]}')",
    "mimamsa_fact_adjustment_array": "INSERT INTO public.mimamsa_fact_adjustment (derived_from_pramana_ids) VALUES ('[\"x\", \"ccdf5abd-6339-48dc-adac-39d8877f2629\"]')",
    "mimamsa_signal_adjustment_scalar": "INSERT INTO public.mimamsa_signal_adjustment (derived_from_pramana_ids) VALUES ('\"db6cc6a0-91a5-4f2e-89ea-33c4fd23fc5c\"')",
    "phala_pramana_shadow_row": "INSERT INTO public.phala_pramana__ssv_20260728b (pramana_id, chart_id, evidence_type) VALUES ('767b84b4-4090-4383-a9a9-ada59a509b1d', '%s', 'life_event_miss')" % CHART,
}


@pytest.mark.parametrize("name", sorted(DEPENDENTS))
def test_a_dependent_is_refused(name, runner):
    dry = assert_refused(runner, ["m_pre_dependents_are_zero", "step_s2_preconditions_as_reader"], setup=lambda: runner.su(DEPENDENTS[name]))
    assert dry["rows_deleted_in_transaction"] == 0


def test_a_foreign_key_referencing_the_table_is_refused(runner):
    def setup():
        runner.su("CREATE TABLE public.sd8_child (id serial PRIMARY KEY, pid uuid REFERENCES public.phala_pramana(pramana_id) ON DELETE CASCADE)")
    assert_refused(runner, ["pre_no_foreign_key_references_the_table"], setup=setup)


def test_a_new_column_that_can_refer_to_a_pramana_id_fails_closed(runner):
    assert_refused(runner, ["m_pre_referencer_columns_are_the_known_set", "step_s2_preconditions_as_reader"],
                   setup=lambda: runner.su("ALTER TABLE public.build_runs ADD COLUMN source_pramana_id uuid"))
    assert_refused(runner, ["m_pre_referencer_columns_are_the_known_set"], setup=lambda: runner.su("ALTER TABLE public.mimamsa_predictions ADD COLUMN linked_pramana_ids jsonb"))


def test_a_dependent_view_trigger_rule_inheritance_or_rls_is_refused(runner):
    assert_refused(runner, ["pre_no_user_trigger_rule_view_or_inheritance_on_the_table"],
                   setup=lambda: runner.su("CREATE VIEW public.sd8_v AS SELECT pramana_id FROM public.phala_pramana"))


@pytest.mark.parametrize("ddl", [
    "CREATE FUNCTION public.sd8_f() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RETURN OLD; END $$; "
    "CREATE TRIGGER sd8_t AFTER DELETE ON public.phala_pramana FOR EACH ROW EXECUTE FUNCTION public.sd8_f()",
    "CREATE RULE sd8_r AS ON DELETE TO public.phala_pramana DO ALSO NOTHING",
    "CREATE TABLE public.sd8_kid () INHERITS (public.phala_pramana)",
], ids=["trigger", "rule", "inheritance_child"])
def test_a_trigger_rule_or_inheritance_child_is_refused(ddl, runner):
    assert_refused(runner, ["pre_no_user_trigger_rule_view_or_inheritance_on_the_table"], setup=lambda: runner.su(ddl))


def test_row_level_security_on_the_table_is_refused(runner):
    assert_refused(runner, ["pre_table_is_an_ordinary_table_owned_by_amjis_app_without_rls"],
                   setup=lambda: runner.su("ALTER TABLE public.phala_pramana ENABLE ROW LEVEL SECURITY"))


def test_a_changed_acl_for_the_delete_role_is_refused(runner):
    assert_refused(runner, ["pre_delete_role_can_delete_and_reader_cannot_write"],
                   setup=lambda: runner.su("GRANT UPDATE ON public.phala_pramana TO data_plane_builder", ))
    assert_refused(runner, ["pre_delete_role_can_delete_and_reader_cannot_write"],
                   setup=lambda: runner.su("REVOKE UPDATE ON public.phala_pramana FROM data_plane_builder; GRANT DELETE ON public.phala_pramana TO suvarna_reader"))


# ----------------------------------------------------------------------------------------------------------------- builds in flight
@pytest.mark.parametrize("chart", [CHART, OTHER_CHART], ids=["on_the_bound_chart", "on_another_chart"])
@pytest.mark.parametrize("state", ["planned", "running", "paused"])
def test_a_build_in_flight_is_refused(chart, state, runner):
    assert_refused(runner, ["m_pre_no_build_in_flight", "step_s2_preconditions_as_reader"],
                   setup=lambda: runner.su("INSERT INTO public.build_runs (chart_id, state) VALUES (%s, %s)", (chart, state)))


# ------------------------------------------------------------------- wrong database / role / server major version / interpreter
def test_the_wrong_database_is_refused(runner, mod, monkeypatch):
    monkeypatch.setattr(mod, "EXPECTED_DATABASE", "amjis")            # production's real name; the disposable database is called something else
    before = runner.state()
    code, dry = runner.execute(runner.args("dry-run"))
    assert code == 2 and "pre_database_is_expected" in dry["failed_checks"]
    assert dry["rows_deleted_in_transaction"] == 0 and runner.state() == before
    code, res = runner.execute(runner.args("apply", expect_evidence=dry["evidence_digest"]))
    assert code == 1 and "pre_database_is_expected" in res["failed_checks"] and runner.state() == before


def test_the_wrong_role_is_refused(cluster, db, runner):
    cluster.su(db, "CREATE ROLE other_admin LOGIN CREATEROLE")                  # can assume the roles, but is not the administrator the plan names
    cluster.su(db, "CREATE ROLE weak_admin LOGIN")                              # no CREATEROLE, no membership: cannot assume them either
    dry = assert_refused(runner, ["pre_session_user_is_the_expected_administrator"], user="other_admin")
    assert "pre_admin_can_assume_the_roles" not in dry["failed_checks"]
    dry = assert_refused(runner, ["pre_session_user_is_the_expected_administrator", "pre_admin_can_assume_the_roles"], user="weak_admin")
    # the table owner and the builder themselves are refused as well (the plan names the administrator)
    assert_refused(runner, ["pre_session_user_is_the_expected_administrator"], user="data_plane_builder")
    # a superuser is not the named administrator either
    assert_refused(runner, ["pre_session_user_is_the_expected_administrator"], user="postgres")


def test_a_server_major_version_other_than_15_is_refused(runner, mod, monkeypatch):
    monkeypatch.setattr(mod, "SERVER_MAJOR", 16)
    dry = assert_refused(runner, ["pre_server_major_is_15"])
    assert dry["rows_deleted_in_transaction"] == 0


def test_apply_refuses_with_exit_92_under_a_different_interpreter_than_the_dry_run(runner, mod):
    code, dry = runner.run("dry-run")
    assert code == 0
    od = pathlib.Path(dry["evidence_dir"]) / "outcome.json"
    body = json.loads(od.read_text())
    assert {"python_executable", "python_version", "psycopg_version", "libpq_version"} <= set(body)
    body["python_executable"] = "/some/other/python3"
    od.write_text(json.dumps(body))
    before = runner.state()
    with pytest.raises(SystemExit) as e:
        runner.execute(runner.args("apply", expect_evidence=dry["evidence_digest"]))
    assert e.value.code == 92 and runner.state() == before


@pytest.mark.parametrize("key", ["python_version", "psycopg_version", "libpq_version"])
def test_apply_refuses_with_exit_92_when_any_recorded_runtime_field_differs(key, runner):
    code, dry = runner.run("dry-run")
    od = pathlib.Path(dry["evidence_dir"]) / "outcome.json"
    body = json.loads(od.read_text())
    body[key] = "different"
    od.write_text(json.dumps(body))
    with pytest.raises(SystemExit) as e:
        runner.execute(runner.args("apply", expect_evidence=dry["evidence_digest"]))
    assert e.value.code == 92


def test_apply_refuses_with_exit_92_when_the_dry_run_recorded_no_interpreter(runner):
    code, dry = runner.run("dry-run")
    od = pathlib.Path(dry["evidence_dir"]) / "outcome.json"
    body = json.loads(od.read_text())
    del body["libpq_version"]
    od.write_text(json.dumps(body))
    with pytest.raises(SystemExit) as e:
        runner.execute(runner.args("apply", expect_evidence=dry["evidence_digest"]))
    assert e.value.code == 92


def test_the_runtime_record_is_bound_into_the_evidence_digest(runner, mod, monkeypatch):
    _, a = runner.run("dry-run")
    _, b = runner.run("dry-run")
    assert a["evidence_digest"] == b["evidence_digest"]                       # deterministic between runs in the same state
    monkeypatch.setattr(mod, "runtime_record", lambda: {"python_executable": "/x", "python_version": "3.99", "psycopg_version": "0", "libpq_version": 0})
    _, c = runner.run("dry-run")
    assert c["evidence_digest"] != a["evidence_digest"]


# --------------------------------------------------------------------------------------------------------------------------- mutations
def sql_text(mod):
    return mod.SQL_FORWARD.read_text()


def cut(src, start, end, replacement=""):
    a, b = src.index(start), src.index(end)
    assert a < b
    return src[:a] + replacement + src[b:]


def set_sql(mod, monkeypatch, tmp_path, text, name="mut.sql"):
    p = tmp_path / name
    p.write_text(text)
    monkeypatch.setattr(mod, "SQL_FORWARD", p)


DELETE_PREDICATE = "WHERE chart_id = v_chart AND pramana_id = ANY (v_ids) AND evidence_type = 'life_event_miss'\n    RETURNING"
S3_CHECKS_START, S3_CHECKS_END = "  IF v_n <> 8 THEN RAISE EXCEPTION 'sd8 delete:", "  PERFORM set_config('madhav.sd8_deleted_ids'"


def other_chart_miss_decoy(runner):
    insert_pramana(runner, "d1000008-0000-4000-8000-000000000008", OTHER_CHART, "life_event_miss")


def test_mutation_a_marker_only_delete_is_refused_by_the_delete_step_count_check(runner, mod, monkeypatch, tmp_path):
    src = sql_text(mod)
    assert DELETE_PREDICATE in src
    set_sql(mod, monkeypatch, tmp_path, src.replace(DELETE_PREDICATE, "WHERE evidence_type = 'life_event_miss'\n    RETURNING", 1))
    other_chart_miss_decoy(runner)
    dry = assert_refused(runner, ["step_s3_delete_as_builder"])
    assert "9 rows deleted" in dry["details"]["step_s3_delete_as_builder"]


def test_mutation_b_marker_only_delete_without_the_delete_step_checks_is_refused_by_the_sql_post_assertions(runner, mod, monkeypatch, tmp_path):
    src = sql_text(mod)
    src = cut(src.replace(DELETE_PREDICATE, "WHERE evidence_type = 'life_event_miss'\n    RETURNING", 1), S3_CHECKS_START, S3_CHECKS_END)
    set_sql(mod, monkeypatch, tmp_path, src)
    other_chart_miss_decoy(runner)
    assert_refused(runner, ["step_s4_post_assertions_as_reader"])


def test_mutation_c_without_any_sql_check_the_python_post_measurement_refuses(runner, mod, monkeypatch, tmp_path):
    src = sql_text(mod)
    src = cut(src.replace(DELETE_PREDICATE, "WHERE evidence_type = 'life_event_miss'\n    RETURNING", 1), S3_CHECKS_START, S3_CHECKS_END)
    src = cut(src, "-- @@STEP s4_post_assertions_as_reader", "-- @@STEP s5_restore_memberships", "-- @@STEP s4_post_assertions_as_reader\nSELECT 1;\n\n")
    set_sql(mod, monkeypatch, tmp_path, src)
    other_chart_miss_decoy(runner)
    dry = assert_refused(runner, ["m_post_other_charts_counts_unchanged", "m_post_deleted_ids_equal_the_bound_ids"])
    assert "step_s4_post_assertions_as_reader" not in dry["failed_checks"]      # the SQL layer was neutered; the python layer alone caught it


def test_mutation_c2_the_python_measurement_does_not_trust_the_recorded_deleted_ids(runner, mod, monkeypatch, tmp_path):
    """Same, and the GUC that records the deleted ids is also removed: the python layer still refuses (it measures the table, not the recording)."""
    src = sql_text(mod)
    src = cut(src.replace("WHERE chart_id = v_chart AND pramana_id = ANY (v_ids) AND evidence_type = 'life_event_miss'\n    RETURNING",
                          "WHERE chart_id = v_chart\n    RETURNING", 1), S3_CHECKS_START, "END\n$sd8$;\nRESET ROLE;\n\n-- @@STEP s4_post")
    src = cut(src, "-- @@STEP s4_post_assertions_as_reader", "-- @@STEP s5_restore_memberships", "-- @@STEP s4_post_assertions_as_reader\nSELECT 1;\n\n")
    set_sql(mod, monkeypatch, tmp_path, src)
    dry = assert_refused(runner, ["m_post_chart_total_reduced_by_exactly_8", "m_post_chart_survivors_are_the_pre_image_minus_the_8", "m_post_deleted_ids_equal_the_bound_ids"])
    assert "step_s3_delete_as_builder" not in dry["failed_checks"] and "step_s4_post_assertions_as_reader" not in dry["failed_checks"]


def test_mutation_d_chart_only_delete_is_refused(runner, mod, monkeypatch, tmp_path):
    src = sql_text(mod)
    set_sql(mod, monkeypatch, tmp_path, src.replace(DELETE_PREDICATE, "WHERE chart_id = v_chart\n    RETURNING", 1))
    dry = assert_refused(runner, ["step_s3_delete_as_builder"])
    assert "56 rows deleted" in dry["details"]["step_s3_delete_as_builder"]


@pytest.mark.parametrize("role", ["amjis_app", "suvarna_reader", "role_orchestrator"])
def test_mutation_e_a_delete_run_as_the_wrong_role_is_refused(role, cluster, db, runner, mod, monkeypatch, tmp_path):
    cluster.su(db, f"GRANT {role} TO {ADMIN_USER}")                       # let the SET ROLE succeed, so only the executor's own role assertion stands in the way
    old = "SET LOCAL ROLE data_plane_builder;\nDO $sd8$\nDECLARE\n  v_chart uuid := current_setting('madhav.sd8_chart')::uuid;\n  v_ids   uuid[] := string_to_array(current_setting('madhav.sd8_ids'), ',')::uuid[];\n  v_n     bigint;"
    src = sql_text(mod)
    assert old in src
    set_sql(mod, monkeypatch, tmp_path, src.replace(old, old.replace("data_plane_builder", role), 1))
    dry = assert_refused(runner, ["step_s3_delete_as_builder"])
    assert "must run as data_plane_builder" in dry["details"]["step_s3_delete_as_builder"]


def test_mutation_f_memberships_never_revoked_is_refused(runner, mod, monkeypatch, tmp_path):
    old = "EXECUTE format('REVOKE %I FROM %I', r, current_user);"
    src = sql_text(mod)
    assert old in src
    set_sql(mod, monkeypatch, tmp_path, src.replace(old, "NULL;", 1))
    assert_refused(runner, ["post_memberships_restored"])


def test_mutation_g_without_the_sql_preconditions_the_python_preconditions_still_refuse_and_nothing_is_deleted(runner, mod, monkeypatch, tmp_path):
    src = cut(sql_text(mod), "-- @@STEP s2_preconditions_as_reader", "-- @@STEP s3_delete_as_builder", "-- @@STEP s2_preconditions_as_reader\nSELECT 1;\n\n")
    set_sql(mod, monkeypatch, tmp_path, src)
    insert_pramana(runner, "d1000009-0000-4000-8000-000000000009", CHART, "life_event_miss")
    dry = assert_refused(runner, ["m_pre_exactly_8_rows_match_chart_and_marker"])
    assert "step_s3_delete_as_builder" not in dry["checks"] and dry["rows_deleted_in_transaction"] == 0      # the DELETE step never ran


def test_mutation_h_an_edited_id_or_fingerprint_in_the_sql_is_refused_by_the_executors_own_copy(runner, mod, monkeypatch, tmp_path):
    src = sql_text(mod)
    set_sql(mod, monkeypatch, tmp_path, src.replace("649c5828-ba9c-4ca8-9a7f-6ace81fad2e3", "649c5828-ba9c-4ca8-9a7f-6ace81fad2e4", 1), "ids.sql")
    assert_refused(runner, ["pre_sql_bound_values_equal_the_executor_bound_values"])
    set_sql(mod, monkeypatch, tmp_path, src.replace("bf270a4b5b3612827e5ea85885538a99ca4147fd62f1a86882c831c0ff21a4b6", "0" * 64, 1), "fp.sql")
    assert_refused(runner, ["pre_sql_bound_values_equal_the_executor_bound_values"])
    set_sql(mod, monkeypatch, tmp_path, src.replace("set_config('madhav.sd8_chart', '1c826d5a-41cb-4450-b4dc-59d440e5f75a'", "set_config('madhav.sd8_chart', '482012f1-710e-4a25-994a-93821f5871aa'", 1), "chart.sql")
    assert_refused(runner, ["pre_sql_bound_values_equal_the_executor_bound_values"])


def test_mutation_i_any_sql_edit_changes_the_plan_hash(runner, mod, monkeypatch, tmp_path):
    base = mod.plan_hash()
    set_sql(mod, monkeypatch, tmp_path, sql_text(mod).replace("FROM ONLY", "FROM", 1))
    assert mod.plan_hash() != base


def test_mutation_j_a_failed_step_leaves_a_failed_outcome_file(runner, mod, monkeypatch, tmp_path):
    set_sql(mod, monkeypatch, tmp_path, sql_text(mod).replace("    DELETE FROM ONLY public.phala_pramana\n", "    DELETE FROM ONLY public.no_such_table_x\n", 1))
    code, res = runner.run("dry-run")
    outcome = json.loads((pathlib.Path(res["evidence_dir"]) / "outcome.json").read_text())
    assert code == 2 and outcome["status"] == "failed" and outcome["failed_checks"]
    assert outcome["rows_deleted_in_transaction"] == 0 and outcome["transaction_committed"] is False


def test_the_builder_cannot_do_more_than_delete_here(cluster, db):
    """Why the builder is the right role: it cannot UPDATE or TRUNCATE phala_pramana, so even a defect in the SQL cannot rewrite or empty the table in one stroke."""
    with cluster.conn(db, user="data_plane_builder", autocommit=True) as c:
        for stmt in ("UPDATE public.phala_pramana SET window_status = window_status", "TRUNCATE public.phala_pramana"):
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                c.execute(stmt)


# ------------------------------------------------------- the SQL layer on its own (python catalog pre-checks neutered): both layers refuse independently
SQL_LAYER_ONLY = {
    "foreign_key": "CREATE TABLE public.sd8_child (id serial PRIMARY KEY, pid uuid REFERENCES public.phala_pramana(pramana_id) ON DELETE CASCADE)",
    "dependent_view": "CREATE VIEW public.sd8_v AS SELECT pramana_id FROM public.phala_pramana",
    "trigger": "CREATE FUNCTION public.sd8_f() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RETURN OLD; END $$; "
               "CREATE TRIGGER sd8_t AFTER DELETE ON public.phala_pramana FOR EACH ROW EXECUTE FUNCTION public.sd8_f()",
    "rule": "CREATE RULE sd8_r AS ON DELETE TO public.phala_pramana DO ALSO NOTHING",
    "inheritance_child": "CREATE TABLE public.sd8_kid () INHERITS (public.phala_pramana)",
    "builder_gained_update": "GRANT UPDATE ON public.phala_pramana TO data_plane_builder",
    "reader_gained_delete": "GRANT DELETE ON public.phala_pramana TO suvarna_reader",
}


@pytest.mark.parametrize("name", sorted(SQL_LAYER_ONLY))
def test_the_sql_preconditions_refuse_on_their_own(name, runner, mod, monkeypatch):
    monkeypatch.setattr(mod, "pre_checks", lambda leg, pre, ck: ck.chk("pre_checks_neutered_by_the_test", True))
    dry = assert_refused(runner, ["step_s2_preconditions_as_reader"], setup=lambda: runner.su(SQL_LAYER_ONLY[name]))
    assert dry["rows_deleted_in_transaction"] == 0 and "step_s3_delete_as_builder" not in dry["checks"]


def test_the_sql_preconditions_refuse_row_level_security_on_their_own(runner, mod, monkeypatch):
    monkeypatch.setattr(mod, "pre_checks", lambda leg, pre, ck: ck.chk("pre_checks_neutered_by_the_test", True))
    dry = assert_refused(runner, ["step_s2_preconditions_as_reader"], setup=lambda: runner.su("ALTER TABLE public.phala_pramana ENABLE ROW LEVEL SECURITY"))
    assert "step_s3_delete_as_builder" not in dry["checks"]


def test_a_real_server_of_another_major_version_is_refused_with_the_real_constant(cluster, runner):
    """Run with PG_BIN pointing at another major (e.g. /opt/homebrew/opt/postgresql@17/bin); skipped on PostgreSQL 15. No monkeypatching: the module's own SERVER_MAJOR = 15."""
    if cluster.major == 15:
        pytest.skip("this cluster IS PostgreSQL 15")
    dry = assert_refused(runner, ["pre_server_major_is_15"])
    assert dry["rows_deleted_in_transaction"] == 0 and not any(k.startswith("step_") for k in dry["checks"])        # refused before any step ran
