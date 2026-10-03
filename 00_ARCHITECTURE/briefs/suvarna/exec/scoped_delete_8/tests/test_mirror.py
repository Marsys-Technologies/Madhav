"""Mirror tests on a disposable PostgreSQL holding production's roles, schema-public owner/ACL, phala_pramana AND its frozen snapshot phala_pramana__ssv_20260728b
(columns, constraints, indexes, owner, ACL) and the objects the executor reads, with SYNTHETIC rows. The executor runs as the administrator role (non-superuser CREATEROLE), exactly as in production.

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
from conftest import ADMIN_USER, CHART, OTHER_CHART, PROD_PHALA_PRAMANA_ACL, PROD_SHADOW_ACL

pytestmark = pytest.mark.usefixtures("cluster")

IDS = ["649c5828-ba9c-4ca8-9a7f-6ace81fad2e3", "767b84b4-4090-4383-a9a9-ada59a509b1d", "a3c855bb-9698-4c43-bb6b-c85ad1ec0a84",
       "adcfd0d2-e748-4741-9df5-619ad1e8d271", "c4fd0d7c-7502-4b63-bb61-8b693c38375b", "ccdf5abd-6339-48dc-adac-39d8877f2629",
       "db6cc6a0-91a5-4f2e-89ea-33c4fd23fc5c", "f44dea24-ada4-405d-bba7-fe094ce8e1e6"]
SIDS = ["05a53e0a-54c9-4053-9ca2-b5a272d77019", "12cf1a40-a44e-4cfa-8676-17de3f400a43", "1fd500d1-e470-4059-95d7-15b7d318b96b",
        "4649aa1b-20f4-4a7f-90a6-fbf43fb38574", "60b833f7-0d0a-43ed-b904-a25450c3f114", "7af4a789-5f28-4b36-82a7-644a182411f7",
        "8b147ef7-3d7d-4657-9cf1-0dd652144ee9", "a2138a26-3f37-480e-bf71-da03931b147b", "ac243a04-6c4e-4c80-92b9-5ca8999bd644",
        "c89c4d65-c928-4011-928c-fd2288049bc0", "cdd0ef46-6290-4cae-9241-efd89bb109a8", "d6a2f982-a44b-4b6c-92e0-bed3fe44e884",
        "e05205a8-44ae-4329-b363-f28dd1c55fb3", "e16bb71a-7b1b-4021-a4ac-8f286d6411b6", "ef1d58d6-03a3-47bb-a2aa-e32c40d2c642",
        "f9c0087b-529b-4673-a70f-dfc69dba2530"]
PROD_FP = "bf270a4b5b3612827e5ea85885538a99ca4147fd62f1a86882c831c0ff21a4b6"
PROD_SFP = "fe1dc5647a643981b4cfb170e5ded5082125b1bbbe0a1aa0a9c8a84e15264724"
FP_SQL_T = ("SELECT encode(sha256(convert_to(string_agg(concat_ws('|', pramana_id::text, chart_id::text, anchor_id::text, evidence_type, evidence_strength_label, window_status, "
          "(lel_entry_id IS NULL)::text, (lel_entry_jsonb IS NULL)::text, extract(epoch FROM computed_at)::text), E'\\n' ORDER BY pramana_id), 'UTF8')), 'hex') "
          "FROM public.{t} WHERE chart_id = %s AND evidence_type = 'life_event_miss'")
FP_SQL = FP_SQL_T.format(t="phala_pramana")
FP_SQL_SHADOW = FP_SQL_T.format(t="phala_pramana__ssv_20260728b")


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
    for priv in ("SELECT", "INSERT", "DELETE"):                                  # one by one: a comma list means ANY of them
        assert n(runner, f"SELECT has_table_privilege('data_plane_builder','public.phala_pramana','{priv}')") is True, priv
    assert n(runner, "SELECT has_table_privilege('data_plane_builder','public.phala_pramana','UPDATE')") is False
    assert n(runner, "SELECT has_table_privilege('data_plane_builder','public.phala_pramana','TRUNCATE')") is False
    assert n(runner, "SELECT has_table_privilege('suvarna_reader','public.phala_pramana','INSERT,UPDATE,DELETE,TRUNCATE')") is False
    assert n(runner, "SELECT has_table_privilege('data_plane_builder','public.mimamsa_fact_adjustment','SELECT')") is False       # why the reads run as suvarna_reader
    assert n(runner, f"SELECT rolcreaterole AND NOT rolsuper FROM pg_roles WHERE rolname='{ADMIN_USER}'") is True
    assert n(runner, f"SELECT has_schema_privilege('{ADMIN_USER}','public','USAGE')") is False
    assert n(runner, f"SELECT pg_has_role('{ADMIN_USER}','data_plane_builder','MEMBER') OR pg_has_role('{ADMIN_USER}','suvarna_reader','MEMBER') OR pg_has_role('{ADMIN_USER}','amjis_app','MEMBER')") is False
    assert cluster.su(db, "SHOW server_version_num")[0][0].startswith("15")
    # the snapshot: a plain CTAS heap (no constraint / index / trigger / rule / policy / comment), production's ACL, 141 rows (138 + 3), 16 life_event_miss for the bound chart
    S = "public.phala_pramana__ssv_20260728b"
    assert n(runner, f"SELECT relacl::text FROM pg_class WHERE oid='{S}'::regclass") == PROD_SHADOW_ACL
    assert n(runner, f"SELECT count(*) FROM pg_constraint WHERE conrelid='{S}'::regclass OR confrelid='{S}'::regclass") == 0
    assert n(runner, f"SELECT count(*) FROM pg_index WHERE indrelid='{S}'::regclass") == 0
    assert n(runner, f"SELECT count(*) FROM pg_trigger WHERE tgrelid='{S}'::regclass") == 0
    assert n(runner, f"SELECT count(*) FROM pg_policy WHERE polrelid='{S}'::regclass") == 0
    assert n(runner, f"SELECT obj_description('{S}'::regclass, 'pg_class') IS NULL") is True
    assert n(runner, "SELECT count(*) FROM pg_event_trigger") == 0
    assert n(runner, "SELECT string_agg(chart_id::text||':'||n::text, ',' ORDER BY chart_id) FROM (SELECT chart_id, count(*) n FROM public.phala_pramana__ssv_20260728b GROUP BY 1) s") == \
        f"{CHART}:138,{OTHER_CHART}:3"
    assert n(runner, FP_SQL_SHADOW, (CHART,)) == PROD_SFP                       # the 16 rows' non-private fingerprint equals the value measured on PRODUCTION
    # roles: the builder has NOTHING on the snapshot; role_orchestrator holds DELETE there but has NO USAGE on schema public, so only the owner can actually delete
    assert n(runner, f"SELECT has_table_privilege('data_plane_builder','{S}','SELECT,INSERT,UPDATE,DELETE,TRUNCATE')") is False
    assert n(runner, f"SELECT has_table_privilege('role_orchestrator','{S}','DELETE')") is True
    assert n(runner, "SELECT has_schema_privilege('role_orchestrator','public','USAGE')") is False
    assert n(runner, f"SELECT has_table_privilege('amjis_app','{S}','DELETE') AND has_schema_privilege('amjis_app','public','USAGE')") is True
    assert n(runner, f"SELECT has_table_privilege('suvarna_reader','{S}','INSERT,UPDATE,DELETE,TRUNCATE')") is False


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
    assert res["shadow_deleted_ids"] == SIDS and res["shadow_rows_deleted_in_transaction"] == 16          # and exactly the 16 of the snapshot
    assert (res["shadow_chart_total_before"], res["shadow_chart_total_after"]) == (138, 122)
    assert res["shadow_other_charts_before"] == res["shadow_other_charts_after"] == {OTHER_CHART: 3}
    assert res["shadow_deleted_rows_nonprivate_fingerprint_sha256"] == PROD_SFP and res["total_rows_deleted_in_transaction"] == 24
    assert runner.state() == before                                  # ROLLBACK: nothing at all moved
    assert len(res["evidence_digest"]) == 64
    outcome = json.loads((pathlib.Path(res["evidence_dir"]) / "outcome.json").read_text())
    assert outcome["status"] == "dry_run" and outcome["plan_hash"] == res["plan_hash"] and outcome["evidence_digest"] == res["evidence_digest"]
    assert outcome["python_executable"] and outcome["python_version"] and outcome["psycopg_version"] and outcome["libpq_version"]
    assert outcome["deleted_ids"] == IDS and outcome["rows_deleted_in_transaction"] == 8
    assert outcome["chart_total_before"] == 56 and outcome["chart_total_after"] == 48
    assert outcome["other_charts_before"] == outcome["other_charts_after"] == {OTHER_CHART: 4}
    assert outcome["deleted_rows_nonprivate_fingerprint_sha256"] == PROD_FP
    assert outcome["shadow_deleted_ids"] == SIDS and outcome["shadow_chart_total_before"] == 138 and outcome["shadow_chart_total_after"] == 122
    assert outcome["shadow_other_charts_before"] == outcome["shadow_other_charts_after"] == {OTHER_CHART: 3} and outcome["shadow_deleted_rows_nonprivate_fingerprint_sha256"] == PROD_SFP
    assert outcome["total_rows_deleted_in_transaction"] == 24
    assert "INTENDED" in outcome["rollback_baseline_amendment"] and "deleting 16" in outcome["rollback_baseline_amendment"] and "138 -> 122" in outcome["rollback_baseline_amendment"]
    assert outcome["transaction_committed"] is False and outcome["irreversible"] is True and "PR #3047" in outcome["restore"]
    # NO private content anywhere: every private column of the synthetic rows holds a PRIVMARK, none of which may appear in a file or in the output
    assert "PRIVMARK" not in evidence_text(pathlib.Path(res["evidence_dir"]).parent)
    cap = capsys.readouterr()
    assert "PRIVMARK" not in cap.out + cap.err
    names = set(res["checks"])
    for expected in ("step_s1_assume_roles", "step_s2_preconditions_as_reader", "step_s3_delete_as_builder", "step_s4_delete_shadow_as_table_owner", "step_s5_post_assertions_as_reader",
                     "step_s6_restore_memberships", "m_pre_fingerprint_equals_the_pinned_one", "m_post_the_8_ids_are_gone", "m_pre_shadow_exactly_16_rows_match_chart_and_marker",
                     "m_post_shadow_the_16_ids_are_gone", "m_post_shadow_other_charts_counts_unchanged", "post_memberships_restored"):
        assert expected in names, expected


def test_apply_deletes_exactly_the_8_and_nothing_else_moves(runner, mod, capsys):
    before = runner.state()
    code, res = runner.run("apply")
    assert code == 0 and res["status"] == "COMMITTED", (res.get("failed_checks"), res.get("details"))
    after = runner.state()
    assert after["pramana_n"] == before["pramana_n"] - 8 and after["shadow_n"] == before["shadow_n"] - 16 == 125
    assert n(runner, "SELECT count(*) FROM public.phala_pramana WHERE pramana_id = ANY(%s::uuid[])", (IDS,)) == 0
    assert n(runner, "SELECT count(*) FROM public.phala_pramana__ssv_20260728b WHERE pramana_id = ANY(%s::uuid[])", (SIDS,)) == 0
    assert n(runner, "SELECT count(*) FROM public.phala_pramana__ssv_20260728b WHERE chart_id=%s AND evidence_type='life_event_miss'", (CHART,)) == 0
    assert after["by_chart"] == f"{CHART}:48,{OTHER_CHART}:4" and after["shadow_by_chart"] == f"{CHART}:122,{OTHER_CHART}:3"
    assert n(runner, "SELECT count(*) FROM public.phala_pramana WHERE chart_id=%s AND evidence_type='life_event_miss'", (CHART,)) == 0
    # everything else byte-identical: schema ACL, every table ACL and owner, memberships (nothing left over), constraints, triggers, object set, anchors, dependents
    for k in ("schema_acl", "schema_owner", "table_acls", "memberships", "constraints", "triggers", "objects", "anchors", "others"):
        assert after[k] == before[k], k
    # the surviving rows are exactly the pre-image minus the 8 (compared by content, as the superuser)
    outcome = json.loads((pathlib.Path(res["evidence_dir"]) / "outcome.json").read_text())
    assert outcome["status"] == "applied" and outcome["transaction_committed"] is True and outcome["after_is_measured_inside_the_transaction"] is False
    assert outcome["deleted_ids"] == IDS and outcome["chart_total_before"] == 56 and outcome["chart_total_after"] == 48
    assert outcome["shadow_deleted_ids"] == SIDS and outcome["shadow_chart_total_before"] == 138 and outcome["shadow_chart_total_after"] == 122 and outcome["total_rows_deleted_in_transaction"] == 24
    assert outcome["other_charts_before"] == outcome["other_charts_after"] == {OTHER_CHART: 4}
    assert outcome["deleted_rows_nonprivate_fingerprint_sha256"] == PROD_FP
    assert "PRIVMARK" not in evidence_text(pathlib.Path(res["evidence_dir"]).parent)
    cap = capsys.readouterr()
    assert "PRIVMARK" not in cap.out + cap.err
    # the surviving 48 + 4 rows (and the snapshot's 122 + 3) still hold their (synthetic) private columns untouched
    assert n(runner, "SELECT count(*) FROM public.phala_pramana WHERE falsifier_text LIKE 'PRIVMARK-%'") == 52
    assert n(runner, "SELECT count(*) FROM public.phala_pramana__ssv_20260728b WHERE falsifier_text LIKE 'PRIVMARK-%'") == 125


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
    assert_refused(runner, ["pre_no_user_trigger_rule_view_policy_or_inheritance_on_the_table"],
                   setup=lambda: runner.su("CREATE VIEW public.sd8_v AS SELECT pramana_id FROM public.phala_pramana"))


@pytest.mark.parametrize("ddl", [
    "CREATE FUNCTION public.sd8_f() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RETURN OLD; END $$; "
    "CREATE TRIGGER sd8_t AFTER DELETE ON public.phala_pramana FOR EACH ROW EXECUTE FUNCTION public.sd8_f()",
    "CREATE RULE sd8_r AS ON DELETE TO public.phala_pramana DO ALSO NOTHING",
    "CREATE TABLE public.sd8_kid () INHERITS (public.phala_pramana)",
], ids=["trigger", "rule", "inheritance_child"])
def test_a_trigger_rule_or_inheritance_child_is_refused(ddl, runner):
    assert_refused(runner, ["pre_no_user_trigger_rule_view_policy_or_inheritance_on_the_table"], setup=lambda: runner.su(ddl))


def test_row_level_security_on_the_table_is_refused(runner):
    assert_refused(runner, ["pre_table_is_an_ordinary_table_owned_by_amjis_app_without_rls"],
                   setup=lambda: runner.su("ALTER TABLE public.phala_pramana ENABLE ROW LEVEL SECURITY"))


def test_a_changed_acl_for_the_delete_role_is_refused(runner):
    assert_refused(runner, ["pre_delete_role_can_delete_and_reader_cannot_write"],
                   setup=lambda: runner.su("GRANT UPDATE ON public.phala_pramana TO data_plane_builder", ))
    assert_refused(runner, ["pre_delete_role_can_delete_and_reader_cannot_write"],
                   setup=lambda: runner.su("REVOKE UPDATE ON public.phala_pramana FROM data_plane_builder; GRANT DELETE ON public.phala_pramana TO suvarna_reader"))
    assert_refused(runner, ["pre_delete_role_can_delete_and_reader_cannot_write"],
                   setup=lambda: runner.su("REVOKE DELETE ON public.phala_pramana FROM data_plane_builder, suvarna_reader"))      # the builder keeps SELECT but lost DELETE


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
    assert_refused(runner, ["step_s5_post_assertions_as_reader"])


def test_mutation_c_without_any_sql_check_the_python_post_measurement_refuses(runner, mod, monkeypatch, tmp_path):
    src = sql_text(mod)
    src = cut(src.replace(DELETE_PREDICATE, "WHERE evidence_type = 'life_event_miss'\n    RETURNING", 1), S3_CHECKS_START, S3_CHECKS_END)
    src = cut(src, "-- @@STEP s5_post_assertions_as_reader", "-- @@STEP s6_restore_memberships", "-- @@STEP s5_post_assertions_as_reader\nSELECT 1;\n\n")
    set_sql(mod, monkeypatch, tmp_path, src)
    other_chart_miss_decoy(runner)
    dry = assert_refused(runner, ["m_post_other_charts_counts_unchanged", "m_post_deleted_ids_equal_the_bound_ids"])
    assert "step_s5_post_assertions_as_reader" not in dry["failed_checks"]      # the SQL layer was neutered; the python layer alone caught it


def test_mutation_c2_the_python_measurement_does_not_trust_the_recorded_deleted_ids(runner, mod, monkeypatch, tmp_path):
    """Same, and the GUC that records the deleted ids is also removed: the python layer still refuses (it measures the table, not the recording)."""
    src = sql_text(mod)
    src = cut(src.replace("WHERE chart_id = v_chart AND pramana_id = ANY (v_ids) AND evidence_type = 'life_event_miss'\n    RETURNING",
                          "WHERE chart_id = v_chart\n    RETURNING", 1), S3_CHECKS_START, "END\n$sd8$;\nRESET ROLE;\n\n-- @@STEP s4_delete_shadow_as_table_owner")
    src = cut(src, "-- @@STEP s5_post_assertions_as_reader", "-- @@STEP s6_restore_memberships", "-- @@STEP s5_post_assertions_as_reader\nSELECT 1;\n\n")
    set_sql(mod, monkeypatch, tmp_path, src)
    dry = assert_refused(runner, ["m_post_chart_total_reduced_by_exactly_8", "m_post_chart_survivors_are_the_pre_image_minus_the_8", "m_post_deleted_ids_equal_the_bound_ids"])
    assert "step_s3_delete_as_builder" not in dry["failed_checks"] and "step_s5_post_assertions_as_reader" not in dry["failed_checks"]


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
    "builder_lost_delete": "REVOKE DELETE ON public.phala_pramana FROM data_plane_builder",
    "builder_lost_select": "REVOKE SELECT ON public.phala_pramana FROM data_plane_builder",
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


# =========================================================================================================== the SNAPSHOT table (SS extension: 16 more rows)
SHADOW = "public.phala_pramana__ssv_20260728b"
S4_DELETE_PREDICATE = "WHERE chart_id = v_chart AND pramana_id = ANY (v_sids) AND evidence_type = 'life_event_miss'\n    RETURNING"


def insert_shadow(runner, pid, chart, evidence_type, window="past_window", label="indirect"):
    runner.su(f"INSERT INTO {SHADOW} (pramana_id, chart_id, anchor_id, evidence_type, evidence_strength_label, falsifier_text, observable_criteria_jsonb, window_status, "
              "derivation_ledger_jsonb, source_citation, computed_at) VALUES (%s, %s, gen_random_uuid(), %s, %s, 'PRIVMARK', '{}', %s, '{}', 'PRIVMARK', now())",
              (pid, chart, evidence_type, label, window))


def test_matching_looking_snapshot_rows_are_not_deleted(runner):
    """Another chart with the marker, the same chart with another marker, a NULL chart with the marker (the snapshot has no NOT NULL): none is touched."""
    insert_shadow(runner, "d2000001-0000-4000-8000-000000000001", OTHER_CHART, "life_event_miss")
    insert_shadow(runner, "d2000001-0000-4000-8000-000000000002", CHART, "detector_unavailable")
    insert_shadow(runner, "d2000001-0000-4000-8000-000000000003", CHART, "life_event_match", label="direct")
    runner.su(f"INSERT INTO {SHADOW} (pramana_id, chart_id, evidence_type) VALUES ('d2000001-0000-4000-8000-000000000004', NULL, 'life_event_miss')")
    before = runner.state()
    code, res = runner.run("apply")
    assert code == 0 and res["status"] == "COMMITTED", (res.get("failed_checks"), res.get("details"))
    assert res["shadow_deleted_ids"] == SIDS and res["shadow_chart_total_before"] == 140 and res["shadow_chart_total_after"] == 124
    after = runner.state()
    assert after["shadow_n"] == before["shadow_n"] - 16
    for i in range(1, 5):
        assert n(runner, f"SELECT count(*) FROM {SHADOW} WHERE pramana_id = %s", (f"d2000001-0000-4000-8000-00000000000{i}",)) == 1, i
    assert after["shadow_by_chart"] is not None and after["shadow_by_chart"].startswith(f"{CHART}:124,{OTHER_CHART}:4")


# ---------------------------------------------------------------------------------------------------- the snapshot's row-set refusals
def test_fifteen_matching_snapshot_rows_are_refused(runner):
    assert_refused(runner, ["m_pre_shadow_exactly_16_rows_match_chart_and_marker", "step_s2_preconditions_as_reader"],
                   setup=lambda: runner.su(f"DELETE FROM {SHADOW} WHERE pramana_id = %s", (SIDS[0],)))


def test_seventeen_matching_snapshot_rows_are_refused(runner):
    assert_refused(runner, ["m_pre_shadow_exactly_16_rows_match_chart_and_marker", "step_s2_preconditions_as_reader"],
                   setup=lambda: insert_shadow(runner, "d2000009-0000-4000-8000-000000000009", CHART, "life_event_miss"))


def test_different_snapshot_ids_are_refused_even_with_exactly_16_matching_rows(runner):
    assert_refused(runner, ["m_pre_shadow_matching_ids_equal_the_bound_ids", "m_pre_shadow_fingerprint_equals_the_pinned_one", "step_s2_preconditions_as_reader"],
                   setup=lambda: runner.su(f"UPDATE {SHADOW} SET pramana_id = 'e2000009-0000-4000-8000-000000000009' WHERE pramana_id = %s", (SIDS[5],)))


def test_a_changed_non_private_snapshot_value_is_refused(runner):
    assert_refused(runner, ["m_pre_shadow_fingerprint_equals_the_pinned_one", "step_s2_preconditions_as_reader"],
                   setup=lambda: runner.su(f"UPDATE {SHADOW} SET window_status = 'open' WHERE pramana_id = %s", (SIDS[2],)))


def test_a_snapshot_row_carrying_a_life_event_payload_is_refused(runner):
    assert_refused(runner, ["m_pre_shadow_no_matching_row_carries_a_life_event_payload", "step_s2_preconditions_as_reader"],
                   setup=lambda: runner.su(f"UPDATE {SHADOW} SET lel_entry_jsonb = '{{\"summary\": \"PRIVMARK-payload\"}}' WHERE pramana_id = %s", (SIDS[0],)))
    assert_refused(runner, ["m_pre_shadow_no_matching_row_carries_a_life_event_payload"],
                   setup=lambda: runner.su(f"UPDATE {SHADOW} SET lel_entry_id = 5 WHERE pramana_id = %s", (SIDS[1],)))


def test_a_duplicate_of_a_bound_snapshot_id_elsewhere_in_the_table_is_refused(runner):
    """pramana_id is nullable and not unique in the snapshot: a delete by id could reach a row of another chart/marker that carries the same id."""
    dry = assert_refused(runner, ["m_pre_shadow_no_other_row_carries_a_bound_id", "step_s2_preconditions_as_reader"],
                         setup=lambda: runner.su(f"INSERT INTO {SHADOW} (pramana_id, chart_id, evidence_type) VALUES (%s, %s, 'pending_observation')", (SIDS[4], OTHER_CHART)))
    assert dry["shadow_rows_deleted_in_transaction"] == 0


def test_the_two_tables_must_not_carry_each_others_ids(runner):
    assert_refused(runner, ["m_pre_dependents_are_zero", "step_s2_preconditions_as_reader"],
                   setup=lambda: insert_pramana(runner, SIDS[0], OTHER_CHART, "pending_observation", window="open"))          # a phala_pramana row with a bound SHADOW id


SHADOW_DEPENDENTS = {name: sql.replace("649c5828-ba9c-4ca8-9a7f-6ace81fad2e3", SIDS[0]).replace("767b84b4-4090-4383-a9a9-ada59a509b1d", SIDS[1])
                     .replace("a3c855bb-9698-4c43-bb6b-c85ad1ec0a84", SIDS[2]).replace("adcfd0d2-e748-4741-9df5-619ad1e8d271", SIDS[3])
                     .replace("c4fd0d7c-7502-4b63-bb61-8b693c38375b", SIDS[4]).replace("ccdf5abd-6339-48dc-adac-39d8877f2629", SIDS[5])
                     .replace("db6cc6a0-91a5-4f2e-89ea-33c4fd23fc5c", SIDS[6]).replace("f44dea24-ada4-405d-bba7-fe094ce8e1e6", SIDS[15])
                     for name, sql in DEPENDENTS.items() if not name.startswith("phala_pramana_shadow_row")}


@pytest.mark.parametrize("name", sorted(SHADOW_DEPENDENTS))
def test_a_dependent_of_a_snapshot_id_is_refused(name, runner):
    assert SIDS[0] in SHADOW_DEPENDENTS[name] or SIDS[1] in SHADOW_DEPENDENTS[name] or any(i in SHADOW_DEPENDENTS[name] for i in SIDS)
    dry = assert_refused(runner, ["m_pre_dependents_are_zero", "step_s2_preconditions_as_reader"], setup=lambda: runner.su(SHADOW_DEPENDENTS[name]))
    assert dry["rows_deleted_in_transaction"] == 0 and dry["shadow_rows_deleted_in_transaction"] == 0


# ------------------------------------------------------------------- the snapshot's catalog refusals (and the guards: none is bypassed)
SHADOW_GUARDS = {
    "foreign_key": ("pre_shadow_no_foreign_key_references_the_table",
                    f"ALTER TABLE {SHADOW} ADD PRIMARY KEY (pramana_id); CREATE TABLE public.sd8_schild (id serial PRIMARY KEY, pid uuid REFERENCES {SHADOW}(pramana_id) ON DELETE CASCADE)"),
    "dependent_view": ("pre_shadow_no_user_trigger_rule_view_policy_or_inheritance_on_the_table", f"CREATE VIEW public.sd8_sv AS SELECT pramana_id FROM {SHADOW}"),
    "freeze_guard_trigger": ("pre_shadow_no_user_trigger_rule_view_policy_or_inheritance_on_the_table",
                             "CREATE FUNCTION public.sd8_guard() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'snapshot is frozen'; END $$; "
                             f"CREATE TRIGGER sd8_freeze BEFORE DELETE ON {SHADOW} FOR EACH ROW EXECUTE FUNCTION public.sd8_guard()"),
    "rule": ("pre_shadow_no_user_trigger_rule_view_policy_or_inheritance_on_the_table", f"CREATE RULE sd8_sr AS ON DELETE TO {SHADOW} DO INSTEAD NOTHING"),
    "inheritance_child": ("pre_shadow_no_user_trigger_rule_view_policy_or_inheritance_on_the_table", f"CREATE TABLE public.sd8_skid () INHERITS ({SHADOW})"),
    "policy": ("pre_shadow_no_user_trigger_rule_view_policy_or_inheritance_on_the_table", f"CREATE POLICY sd8_p ON {SHADOW} FOR ALL USING (true)"),
    "rls": ("pre_shadow_table_is_an_ordinary_table_owned_by_amjis_app_without_rls", f"ALTER TABLE {SHADOW} ENABLE ROW LEVEL SECURITY"),
    "owner_changed": ("pre_shadow_table_is_an_ordinary_table_owned_by_amjis_app_without_rls", f"ALTER TABLE {SHADOW} OWNER TO data_plane_builder"),
    "builder_gained_a_privilege": ("pre_shadow_delete_role_can_delete_and_reader_cannot_write", f"GRANT SELECT ON {SHADOW} TO data_plane_builder"),
    "reader_gained_delete": ("pre_shadow_delete_role_can_delete_and_reader_cannot_write", f"GRANT DELETE ON {SHADOW} TO suvarna_reader"),
    "owner_lost_delete": ("pre_shadow_delete_role_can_delete_and_reader_cannot_write", f"REVOKE DELETE ON {SHADOW} FROM amjis_app"),
    "owner_lost_schema_usage": ("pre_shadow_delete_role_can_delete_and_reader_cannot_write", "REVOKE USAGE ON SCHEMA public FROM amjis_app"),
}


@pytest.mark.parametrize("name", sorted(SHADOW_GUARDS))
def test_a_snapshot_guard_or_shape_change_is_refused_and_nothing_is_bypassed(name, runner):
    check, ddl = SHADOW_GUARDS[name]
    dry = assert_refused(runner, [check], setup=lambda: runner.su(ddl))
    assert dry["rows_deleted_in_transaction"] == 0 and dry["shadow_rows_deleted_in_transaction"] == 0 and "step_s3_delete_as_builder" not in dry["checks"]


def test_an_event_trigger_anywhere_is_refused(runner):
    runner.su("CREATE FUNCTION public.sd8_evt() RETURNS event_trigger LANGUAGE plpgsql AS $$ BEGIN NULL; END $$")
    try:
        assert_refused(runner, ["pre_no_event_trigger_exists"], setup=lambda: runner.su("CREATE EVENT TRIGGER sd8_et ON ddl_command_end EXECUTE FUNCTION public.sd8_evt()"))
    finally:
        runner.su("DROP EVENT TRIGGER IF EXISTS sd8_et")


def test_an_event_trigger_is_refused_by_the_sql_layer_on_its_own(runner, mod, monkeypatch):
    monkeypatch.setattr(mod, "pre_checks", lambda leg, pre, ck: ck.chk("pre_checks_neutered_by_the_test", True))
    runner.su("CREATE FUNCTION public.sd8_evt() RETURNS event_trigger LANGUAGE plpgsql AS $$ BEGIN NULL; END $$")
    try:
        assert_refused(runner, ["step_s2_preconditions_as_reader"], setup=lambda: runner.su("CREATE EVENT TRIGGER sd8_et ON ddl_command_end EXECUTE FUNCTION public.sd8_evt()"))
    finally:
        runner.su("DROP EVENT TRIGGER IF EXISTS sd8_et")


@pytest.mark.parametrize("name", ["freeze_guard_trigger", "rule", "policy", "rls", "owner_lost_delete", "owner_lost_schema_usage", "builder_gained_a_privilege", "dependent_view",
                                  "inheritance_child"])
def test_the_snapshot_sql_preconditions_refuse_on_their_own(name, runner, mod, monkeypatch):
    monkeypatch.setattr(mod, "pre_checks", lambda leg, pre, ck: ck.chk("pre_checks_neutered_by_the_test", True))
    dry = assert_refused(runner, ["step_s2_preconditions_as_reader"], setup=lambda: runner.su(SHADOW_GUARDS[name][1]))
    assert dry["rows_deleted_in_transaction"] == 0 and "step_s3_delete_as_builder" not in dry["checks"]


# ------------------------------------------------------------------------------------------------------------------ ATOMICITY: all-or-nothing
def test_a_failure_in_the_snapshot_delete_rolls_the_first_delete_back(runner, mod, monkeypatch, tmp_path):
    """s3 deletes the 8 live rows, then s4 fails (nonexistent snapshot table): the dry run AND the apply are refused and the 8 live rows are still there."""
    set_sql(mod, monkeypatch, tmp_path, sql_text(mod).replace("    DELETE FROM ONLY public.phala_pramana__ssv_20260728b\n", "    DELETE FROM ONLY public.no_such_snapshot_x\n", 1))
    before = runner.state()
    code, dry = runner.execute(runner.args("dry-run"))
    assert code == 2 and "step_s4_delete_shadow_as_table_owner" in dry["failed_checks"] and "step_s3_delete_as_builder" not in dry["failed_checks"]
    code, res = runner.execute(runner.args("apply", expect_evidence=dry["evidence_digest"]))
    assert code == 1 and res["status"] == "REFUSED_ROLLED_BACK"
    assert runner.state() == before and n(runner, "SELECT count(*) FROM public.phala_pramana WHERE pramana_id = ANY(%s::uuid[])", (IDS,)) == 8


def test_a_guard_that_refuses_the_snapshot_delete_at_run_time_rolls_everything_back(runner, mod, monkeypatch):
    """The python and SQL preconditions that would catch a freeze-guard trigger are neutered here to prove the transaction itself is all-or-nothing: the guard makes the
    snapshot DELETE fail after the live delete succeeded; the apply is refused and BOTH tables are untouched (the guard is not bypassed)."""
    runner.su("CREATE FUNCTION public.sd8_guard() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'snapshot is frozen'; END $$; "
              f"CREATE TRIGGER sd8_freeze BEFORE DELETE ON {SHADOW} FOR EACH ROW EXECUTE FUNCTION public.sd8_guard()")
    monkeypatch.setattr(mod, "pre_checks", lambda leg, pre, ck: ck.chk("pre_checks_neutered_by_the_test", True))
    src = mod.SQL_FORWARD.read_text()
    a, b = src.index("  SELECT count(*) INTO v_x FROM pg_trigger"), src.index("  SELECT count(*) INTO v_x FROM pg_rewrite")
    import pathlib as _pl
    p = _pl.Path(runner.tmp) / "noguardcheck.sql"
    p.write_text(src[:a] + src[b:])
    monkeypatch.setattr(mod, "SQL_FORWARD", p)
    before = runner.state()
    code, dry = runner.execute(runner.args("dry-run"))
    assert code == 2 and dry["failed_checks"] == ["step_s4_delete_shadow_as_table_owner"], dry["failed_checks"]
    assert "snapshot is frozen" in dry["details"]["step_s4_delete_shadow_as_table_owner"]
    code, res = runner.execute(runner.args("apply", expect_evidence=dry["evidence_digest"]))
    assert code == 1 and res["status"] == "REFUSED_ROLLED_BACK"
    assert runner.state() == before


def test_the_live_delete_does_not_survive_a_refused_snapshot_check(runner):
    """A snapshot precondition failure (15 rows) refuses the whole run: not even the 8 live rows are deleted."""
    runner.su(f"DELETE FROM {SHADOW} WHERE pramana_id = %s", (SIDS[0],))
    before = runner.state()
    code, res = runner.run("apply")
    assert code in (1, 2) and runner.state() == before and n(runner, "SELECT count(*) FROM public.phala_pramana WHERE pramana_id = ANY(%s::uuid[])", (IDS,)) == 8


def test_a_live_precondition_failure_leaves_the_snapshot_untouched(runner):
    runner.su("DELETE FROM public.phala_pramana WHERE pramana_id = %s", (IDS[0],))
    before = runner.state()
    code, res = runner.run("apply")
    assert code in (1, 2) and runner.state() == before and n(runner, f"SELECT count(*) FROM {SHADOW} WHERE pramana_id = ANY(%s::uuid[])", (SIDS,)) == 16


# ------------------------------------------------------------------------------------------------------- the snapshot's role: why the table owner
def test_the_builder_cannot_touch_the_snapshot_and_role_orchestrator_cannot_even_resolve_it(cluster, db):
    with cluster.conn(db, user="data_plane_builder", autocommit=True) as c:
        for stmt in (f"DELETE FROM {SHADOW} WHERE false", f"SELECT 1 FROM {SHADOW}"):
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                c.execute(stmt)
    cluster.su(db, "CREATE ROLE sd8_orch_login LOGIN IN ROLE role_orchestrator")
    with cluster.conn(db, user="sd8_orch_login", autocommit=True) as c:
        with pytest.raises(psycopg.errors.InsufficientPrivilege) as e:
            c.execute(f"DELETE FROM {SHADOW} WHERE false")
        assert "schema public" in str(e.value)                                       # DELETE is granted on the table, but there is no USAGE on the schema


@pytest.mark.parametrize("role", ["data_plane_builder", "suvarna_reader", "role_orchestrator"])
def test_mutation_a_snapshot_delete_run_as_the_wrong_role_is_refused(role, cluster, db, runner, mod, monkeypatch, tmp_path):
    cluster.su(db, f"GRANT {role} TO {ADMIN_USER}")
    src = sql_text(mod)
    a = src.index("-- @@STEP s4_delete_shadow_as_table_owner")
    seg = src[a:].replace("SET LOCAL ROLE amjis_app;", f"SET LOCAL ROLE {role};", 1)
    set_sql(mod, monkeypatch, tmp_path, src[:a] + seg)
    dry = assert_refused(runner, ["step_s4_delete_shadow_as_table_owner"])
    assert "must run as amjis_app" in dry["details"]["step_s4_delete_shadow_as_table_owner"]


@pytest.mark.parametrize("role", ["data_plane_builder", "role_orchestrator"])
def test_mutation_without_the_role_assertion_the_wrong_role_still_cannot_delete_from_the_snapshot(role, cluster, db, runner, mod, monkeypatch, tmp_path):
    cluster.su(db, f"GRANT {role} TO {ADMIN_USER}")
    src = sql_text(mod)
    a = src.index("-- @@STEP s4_delete_shadow_as_table_owner")
    seg = src[a:].replace("SET LOCAL ROLE amjis_app;", f"SET LOCAL ROLE {role};", 1)
    seg = seg.replace("  IF current_user <> 'amjis_app' THEN RAISE EXCEPTION 'sd8 shadow delete: the delete must run as amjis_app, not %', current_user; END IF;\n", "", 1)
    set_sql(mod, monkeypatch, tmp_path, src[:a] + seg)
    dry = assert_refused(runner, ["step_s4_delete_shadow_as_table_owner"])
    assert "permission denied" in dry["details"]["step_s4_delete_shadow_as_table_owner"] and "InsufficientPrivilege" in dry["details"]["step_s4_delete_shadow_as_table_owner"]


# --------------------------------------------------------------------------------------------------------- SQL mutations on the snapshot delete
def test_mutation_snapshot_marker_only_delete_is_refused_by_the_step_count_check(runner, mod, monkeypatch, tmp_path):
    src = sql_text(mod)
    assert S4_DELETE_PREDICATE in src
    set_sql(mod, monkeypatch, tmp_path, src.replace(S4_DELETE_PREDICATE, "WHERE evidence_type = 'life_event_miss'\n    RETURNING", 1))
    insert_shadow(runner, "d2000008-0000-4000-8000-000000000008", OTHER_CHART, "life_event_miss")
    dry = assert_refused(runner, ["step_s4_delete_shadow_as_table_owner"])
    assert "17 rows deleted" in dry["details"]["step_s4_delete_shadow_as_table_owner"]


def test_mutation_snapshot_chart_only_delete_is_refused(runner, mod, monkeypatch, tmp_path):
    set_sql(mod, monkeypatch, tmp_path, sql_text(mod).replace(S4_DELETE_PREDICATE, "WHERE chart_id = v_chart\n    RETURNING", 1))
    dry = assert_refused(runner, ["step_s4_delete_shadow_as_table_owner"])
    assert "138 rows deleted" in dry["details"]["step_s4_delete_shadow_as_table_owner"]


def test_mutation_snapshot_id_only_delete_is_refused(runner, mod, monkeypatch, tmp_path):
    """Without chart/marker in the predicate, a duplicate id on another chart is deleted too: caught by the count (17) at the step."""
    runner.su(f"INSERT INTO {SHADOW} (pramana_id, chart_id, evidence_type) VALUES (%s, %s, 'pending_observation')", (SIDS[3], OTHER_CHART))
    monkeypatch.setattr(mod, "pre_checks", lambda leg, pre, ck: ck.chk("pre_checks_neutered_by_the_test", True))
    src = sql_text(mod)
    src = src.replace(S4_DELETE_PREDICATE, "WHERE pramana_id = ANY (v_sids)\n    RETURNING", 1)
    a, b = src.index("  SELECT count(*) INTO v_x FROM public.phala_pramana__ssv_20260728b WHERE pramana_id = ANY (v_sids);"), src.index("  -- pre-images, compared again in s5")
    set_sql(mod, monkeypatch, tmp_path, src[:a] + src[b:])
    monkeypatch.setattr(mod, "pre_measure_checks", lambda m, ck: ck.chk("m_pre_measured", True))
    dry = assert_refused(runner, ["step_s4_delete_shadow_as_table_owner"])
    assert "17 rows deleted" in dry["details"]["step_s4_delete_shadow_as_table_owner"]


def test_mutation_snapshot_without_the_step_checks_the_sql_post_assertions_refuse(runner, mod, monkeypatch, tmp_path):
    src = sql_text(mod).replace(S4_DELETE_PREDICATE, "WHERE evidence_type = 'life_event_miss'\n    RETURNING", 1)
    a, b = src.index("  IF v_n <> 16 THEN RAISE EXCEPTION 'sd8 shadow delete:"), src.index("  PERFORM set_config('madhav.sd8_deleted_shadow_ids'")
    set_sql(mod, monkeypatch, tmp_path, src[:a] + src[b:])
    insert_shadow(runner, "d2000008-0000-4000-8000-000000000008", OTHER_CHART, "life_event_miss")
    assert_refused(runner, ["step_s5_post_assertions_as_reader"])


def test_mutation_snapshot_without_any_sql_check_the_python_post_measurement_refuses(runner, mod, monkeypatch, tmp_path):
    src = sql_text(mod).replace(S4_DELETE_PREDICATE, "WHERE evidence_type = 'life_event_miss'\n    RETURNING", 1)
    a, b = src.index("  IF v_n <> 16 THEN RAISE EXCEPTION 'sd8 shadow delete:"), src.index("  PERFORM set_config('madhav.sd8_deleted_shadow_ids'")
    src = src[:a] + src[b:]
    src = cut(src, "-- @@STEP s5_post_assertions_as_reader", "-- @@STEP s6_restore_memberships", "-- @@STEP s5_post_assertions_as_reader\nSELECT 1;\n\n")
    set_sql(mod, monkeypatch, tmp_path, src)
    insert_shadow(runner, "d2000008-0000-4000-8000-000000000008", OTHER_CHART, "life_event_miss")
    dry = assert_refused(runner, ["m_post_shadow_other_charts_counts_unchanged", "m_post_shadow_deleted_ids_equal_the_bound_ids"])
    assert "step_s5_post_assertions_as_reader" not in dry["failed_checks"] and "step_s4_delete_shadow_as_table_owner" not in dry["failed_checks"]


def test_mutation_snapshot_sql_preconditions_removed_the_python_ones_still_refuse(runner, mod, monkeypatch, tmp_path):
    src = cut(sql_text(mod), "-- @@STEP s2_preconditions_as_reader", "-- @@STEP s3_delete_as_builder", "-- @@STEP s2_preconditions_as_reader\nSELECT 1;\n\n")
    set_sql(mod, monkeypatch, tmp_path, src)
    insert_shadow(runner, "d2000009-0000-4000-8000-000000000009", CHART, "life_event_miss")
    dry = assert_refused(runner, ["m_pre_shadow_exactly_16_rows_match_chart_and_marker"])
    assert dry["rows_deleted_in_transaction"] == 0 and dry["shadow_rows_deleted_in_transaction"] == 0 and "step_s3_delete_as_builder" not in dry["checks"]


def test_the_shadow_sql_values_edited_are_refused_by_the_executors_own_copy(runner, mod, monkeypatch, tmp_path):
    src = sql_text(mod)
    set_sql(mod, monkeypatch, tmp_path, src.replace(SIDS[0], SIDS[0][:-1] + "0", 1), "sids.sql")
    assert_refused(runner, ["pre_sql_bound_values_equal_the_executor_bound_values"])
    set_sql(mod, monkeypatch, tmp_path, src.replace(PROD_SFP, "0" * 64, 1), "sfp.sql")
    assert_refused(runner, ["pre_sql_bound_values_equal_the_executor_bound_values"])


def test_only_the_two_target_tables_are_ever_written(runner):
    """Everything outside the two tables is byte-identical after an apply (dependents, build_runs, anchors, other snapshots, ACLs, constraints, triggers)."""
    before = runner.state()
    assert runner.run("apply")[0] == 0
    after = runner.state()
    for k in ("schema_acl", "table_acls", "memberships", "constraints", "triggers", "objects", "anchors", "others"):
        assert after[k] == before[k], k
