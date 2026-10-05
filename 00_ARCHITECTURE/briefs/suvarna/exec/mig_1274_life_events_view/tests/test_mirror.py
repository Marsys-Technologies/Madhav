"""Mirror tests on a disposable PostgreSQL holding production's roles, schema-public owner/ACL, life_events (columns, ACL, policies, accessor, default ACL)
and SYNTHETIC rows for three charts. The executor runs as the administrator role (non-superuser CREATEROLE), exactly as in production.

Shown here: the builder reads ONLY its own chart's rows through the view; the GUC unset / malformed / wrong -> 0 rows; the builder still has NO direct
SELECT on life_events; the view is read-only for it; nothing else moved (schema ACL byte-identical, table ACL, memberships, rows); the rollback leg
restores the pre-state exactly; and a MUTATION of each safeguard is refused (nothing committed).
"""
from __future__ import annotations

import json
import pathlib

import psycopg
import pytest

from conftest import ADMIN_USER, CHART_A, CHART_B, CHART_C, EXEC_DIR

pytestmark = pytest.mark.usefixtures("cluster")

VIEW = "public.life_events_chart_scoped"


def builder(cl, db):
    return cl.conn(db, user="data_plane_builder", autocommit=True)


def scalar(cl, db, sql, user="postgres", params=None):
    return cl.su(db, sql, params, user=user)[0][0]


def as_builder_count(cl, db, chart_setting, rel="life_events_chart_scoped"):
    with builder(cl, db) as c:
        cur = c.cursor()
        cur.execute("BEGIN")
        if chart_setting is not None:
            cur.execute("SELECT set_config('app.chart_context', %s, true)", (chart_setting,))
        cur.execute(f"SELECT count(*), count(*) FILTER (WHERE chart_id::text <> %s) FROM public.{rel}", (chart_setting or "",))
        n, foreign = cur.fetchone()
        cur.execute("ROLLBACK")
        return n, foreign


# ---------------------------------------------------------------------------------------------------------------- the mirror itself
def test_the_mirror_is_production_shaped(cluster, db):
    s = scalar(cluster, db, "SELECT relacl::text FROM pg_class WHERE oid='public.life_events'::regclass")
    assert s == ("{amjis_app=arwdDxt/amjis_app,retrieval_census_ro=r/amjis_app,role_web_serve=r/amjis_app,role_orchestrator=arwd/amjis_app,"
                 "role_jobs=r/amjis_app,nirmana_evidence_ingress_writer=r/amjis_app,suvarna_reader=r/amjis_app}")
    assert scalar(cluster, db, "SELECT nspacl::text FROM pg_namespace WHERE nspname='public'") == (
        "{data_plane_schema_owner=UC/data_plane_schema_owner,data_plane_l1_owner=UC/data_plane_schema_owner,data_plane_l2_owner=UC/data_plane_schema_owner,"
        "data_plane_migrator=U/data_plane_schema_owner,data_plane_builder=U/data_plane_schema_owner,data_plane_verifier=U/data_plane_schema_owner,"
        "amjis_app=U/data_plane_schema_owner,role_web_serve=U/data_plane_schema_owner,purna_inquiry_owner=U/data_plane_schema_owner,"
        "suvarna_reader=U/data_plane_schema_owner}")
    assert scalar(cluster, db, "SELECT relrowsecurity FROM pg_class WHERE oid='public.life_events'::regclass") is False
    assert scalar(cluster, db, "SELECT count(*) FROM pg_policy WHERE polrelid='public.life_events'::regclass") == 2
    assert scalar(cluster, db, "SELECT has_table_privilege('data_plane_builder','public.life_events','SELECT')") is False
    # the PRODUCTION column ACL (independent review HIGH-1): the builder holds column-level SELECT on exactly five columns, granted by amjis_app
    assert scalar(cluster, db, "SELECT string_agg(attname||':'||attacl::text, ',' ORDER BY attname) FROM pg_attribute "
                               "WHERE attrelid='public.life_events'::regclass AND attacl IS NOT NULL") == (
        "category:{data_plane_builder=r/amjis_app},description:{data_plane_builder=r/amjis_app},event_date:{data_plane_builder=r/amjis_app},"
        "id:{data_plane_builder=r/amjis_app},outcome_observed:{data_plane_builder=r/amjis_app}")
    # ...and so TODAY the builder reads those five columns (free text included) of every chart straight from the table; chart_id it cannot read
    with builder(cluster, db) as c:
        assert c.execute("SELECT count(DISTINCT id) FROM public.life_events").fetchone()[0] == 8
        c.execute("SELECT description FROM public.life_events LIMIT 1")
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        with builder(cluster, db) as c:
            c.execute("SELECT chart_id FROM public.life_events")
    # the administrator is Cloud SQL's postgres: CREATEROLE, not a superuser, no USAGE on public, a member of none of the roles it will assume
    assert scalar(cluster, db, f"SELECT rolcreaterole AND NOT rolsuper FROM pg_roles WHERE rolname='{ADMIN_USER}'") is True
    assert scalar(cluster, db, f"SELECT has_schema_privilege('{ADMIN_USER}','public','USAGE')") is False


# ------------------------------------------------------------------------------------------------------------------- dry run / apply
def test_dry_run_holds_every_check_and_changes_nothing(runner, mod):
    before = runner.state()
    code, res = runner.run("dry-run")
    assert code == 0, (res["failed_checks"], res["details"])
    assert res["status"] == "DRY_RUN_ROLLED_BACK_ALL_CHECKS_HOLD" and res["failed_checks"] == []
    assert len(res["evidence_digest"]) == 64
    assert runner.state() == before                                  # ROLLBACK: nothing at all moved
    assert res["counts"] == {"probe_n": "5", "other_n": "3", "total_n": "8"}       # counts only, never content
    assert {"step_s1_assume_owner_roles", "step_s8_post_assertions", "post_builder_select_on_view",
            "post_view_acl_is_exactly_owner_plus_builder_select", "post_schema_acl_unchanged"} <= set(res["checks"])
    outcome = json.loads((pathlib.Path(res["evidence_dir"]) / "outcome.json").read_text())
    assert outcome["status"] == "dry_run" and outcome["plan_hash"] == res["plan_hash"] and outcome["evidence_digest"] == res["evidence_digest"]
    assert outcome["python_executable"] and outcome["python_version"] and outcome["psycopg_version"]


def test_apply_commits_and_the_builder_reads_only_its_own_chart(cluster, db, runner):
    before = runner.state()
    code, res = runner.run("apply")
    assert code == 0 and res["status"] == "COMMITTED", res
    after = runner.state()
    # what moved: exactly the view appeared
    assert after["view"] == "life_events_chart_scoped" and before["view"] is None
    for k in ("schema_acl", "schema_owner", "table_acl", "memberships", "rows", "row_digest", "fn", "default_acl"):
        assert after[k] == before[k], k                              # nothing else changed, schema ACL byte-identical, no membership left over
    assert before["col_acl"] and after["col_acl"] is None            # the ONLY ACL that moved on life_events: the builder's five column grants are gone
    assert after["other_objects"].replace("life_events_chart_scoped:v,", "").replace(",life_events_chart_scoped:v", "") == before["other_objects"]

    # the builder: reads ONLY the pinned chart's rows
    assert as_builder_count(cluster, db, CHART_A) == (5, 0)
    assert as_builder_count(cluster, db, CHART_B) == (3, 0)
    # fail closed: GUC unset / empty / malformed / a chart without events / a random chart
    assert as_builder_count(cluster, db, None)[0] == 0
    assert as_builder_count(cluster, db, "")[0] == 0
    assert as_builder_count(cluster, db, "not-a-uuid")[0] == 0
    assert as_builder_count(cluster, db, CHART_C)[0] == 0
    assert as_builder_count(cluster, db, "ffffffff-ffff-4fff-bfff-ffffffffffff")[0] == 0
    # the builder STILL has no direct privilege on the table (any column) and the view is read-only for it
    assert scalar(cluster, db, "SELECT has_table_privilege('data_plane_builder','public.life_events','SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER')") is False
    assert scalar(cluster, db, "SELECT has_any_column_privilege('data_plane_builder','public.life_events','SELECT,INSERT,UPDATE,REFERENCES')") is False
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        with builder(cluster, db) as c:
            c.execute("SELECT 1 FROM public.life_events")
    for col in ("id", "event_date", "category", "description", "outcome_observed", "chart_id", "event_id", "domain"):      # the five former columns and the rest
        assert scalar(cluster, db, f"SELECT has_column_privilege('data_plane_builder','public.life_events','{col}','SELECT')") is False, col
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            with builder(cluster, db) as c:
                c.execute(f"SELECT {col} FROM public.life_events")
    for stmt in ("INSERT INTO public.life_events_chart_scoped (id) VALUES (gen_random_uuid())",
                 "UPDATE public.life_events_chart_scoped SET category = category", "DELETE FROM public.life_events_chart_scoped"):
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            with builder(cluster, db) as c:
                c.execute(stmt)
    # the view exposes exactly the six columns, none of the private ones (no free text)
    with builder(cluster, db) as c:
        cols = [d.name for d in c.execute("SELECT * FROM public.life_events_chart_scoped LIMIT 0").description]
    assert cols == list(mod_columns())
    for private in ("description", "provenance", "chart_state", "significance", "source_citation", "recorded_at", "pool_consent"):
        assert private not in cols
    # SS N-109 data minimisation: no free text reachable through the view, whatever the pinned chart
    with pytest.raises(psycopg.errors.UndefinedColumn):
        with builder(cluster, db) as c:
            c.execute("SELECT description FROM public.life_events_chart_scoped")
    with builder(cluster, db) as c:
        c.execute("BEGIN")
        c.execute("SELECT set_config('app.chart_context', %s, true)", (CHART_A,))
        dump = json.dumps([list(map(str, r)) for r in c.execute("SELECT * FROM public.life_events_chart_scoped").fetchall()])
        c.execute("ROLLBACK")
    assert "SYNTHETIC" not in dump and "PRIVATE" not in dump
    # nobody else gained anything: PUBLIC and retrieval_census_ro (the default-ACL grantee) have nothing; the ACL is {owner, builder SELECT}
    acl = scalar(cluster, db, "SELECT relacl::text FROM pg_class WHERE oid='public.life_events_chart_scoped'::regclass")
    assert acl == "{amjis_app=arwdDxt/amjis_app,data_plane_builder=r/amjis_app}", acl
    for role in ("retrieval_census_ro", "role_web_serve", "role_jobs", "role_orchestrator", "suvarna_reader", "data_plane_verifier", "data_plane_migrator"):
        assert scalar(cluster, db, f"SELECT has_table_privilege('{role}','{VIEW}','SELECT')") is False, role
    # security barrier, owner = the table owner, a plain view; the transient CREATE is gone
    assert scalar(cluster, db, "SELECT reloptions::text FROM pg_class WHERE oid='public.life_events_chart_scoped'::regclass") == "{security_barrier=true}"
    assert scalar(cluster, db, "SELECT pg_get_userbyid(relowner) FROM pg_class WHERE oid='public.life_events_chart_scoped'::regclass") == "amjis_app"
    assert scalar(cluster, db, "SELECT has_schema_privilege('amjis_app','public','CREATE')") is False
    outcome = json.loads((pathlib.Path(res["evidence_dir"]) / "outcome.json").read_text())
    assert outcome["status"] == "applied"


def mod_columns():
    import conftest
    return conftest.load_exec("cols_probe").VIEW_COLUMNS


def test_applying_twice_is_refused(runner, mod):
    assert runner.run("apply")[0] == 0
    code, res = runner.run("apply")
    assert code in (1, 2) and "pre_view_absent" in res["failed_checks"]


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


def test_count_mode_reads_only(runner):
    before = runner.state()
    code, res = runner.run("count")
    assert code == 0 and res["status"] == "COUNT_READ_ONLY_OK" and runner.state() == before


# ------------------------------------------------------------------------------------------------------------------------- rollback
def test_rollback_restores_the_pre_state_exactly(cluster, db, runner):
    before = runner.state()
    assert runner.run("apply")[0] == 0
    assert runner.state()["view"] is not None
    code, dry = runner.run("rollback-dry-run")
    assert code == 0 and dry["status"] == "DRY_RUN_ROLLED_BACK_ALL_CHECKS_HOLD"
    assert runner.state()["view"] is not None                                  # the dry run rolled back
    code, res = runner.run("rollback")
    assert code == 0 and res["status"] == "COMMITTED", res
    assert runner.state() == before                                            # byte-for-byte the starting state
    assert scalar(cluster, db, "SELECT has_table_privilege('data_plane_builder','public.life_events','SELECT')") is False


def test_rollback_without_the_view_is_refused(runner):
    code, res = runner.run("rollback")
    assert code in (1, 2) and "pre_view_present" in res["failed_checks"]


def test_rollback_refuses_to_drop_a_different_object_of_that_name(cluster, db, runner):
    cluster.su(db, "REVOKE SELECT (id, event_date, category, description, outcome_observed) ON public.life_events FROM data_plane_builder", user="amjis_app")   # (the state after a forward leg)
    cluster.su(db, "SET ROLE data_plane_schema_owner; GRANT CREATE ON SCHEMA public TO amjis_app; RESET ROLE;")        # (superuser may do both)
    cluster.su(db, "CREATE VIEW public.life_events_chart_scoped AS SELECT 1 AS x")
    code, res = runner.run("rollback")
    assert code in (1, 2) and "step_r2_preconditions" in res["failed_checks"]
    assert scalar(cluster, db, "SELECT count(*) FROM pg_class WHERE relname='life_events_chart_scoped'") == 1


# ------------------------------------------------------------------------------------------------------------------- precondition refusals
def test_refused_when_the_builder_already_holds_a_table_grant(cluster, db, runner):
    cluster.su(db, "GRANT SELECT ON public.life_events TO data_plane_builder", user="amjis_app")
    before = runner.state()
    code, res = runner.run("dry-run")
    assert code == 2 and "pre_builder_has_no_table_level_privilege" in res["failed_checks"]
    assert runner.state() == before


@pytest.mark.parametrize("sql", [
    "REVOKE SELECT (description) ON public.life_events FROM data_plane_builder",                       # four of the five
    "GRANT SELECT (chart_id) ON public.life_events TO data_plane_builder",                             # a sixth column
    "GRANT UPDATE (category) ON public.life_events TO data_plane_builder",                             # another privilege
    "GRANT SELECT (id) ON public.life_events TO data_plane_builder WITH GRANT OPTION",                 # grantable
    "REVOKE SELECT (id, event_date, category, description, outcome_observed) ON public.life_events FROM data_plane_builder",   # none (not the state approved)
], ids=["four_of_five", "sixth_column", "update_priv", "grant_option", "none"])
def test_refused_unless_the_builder_column_acl_is_exactly_the_five_production_grants(cluster, db, runner, sql):
    cluster.su(db, sql, user="amjis_app")
    before = runner.state()
    code, res = runner.run("dry-run")
    assert code == 2 and "pre_builder_holds_exactly_the_five_column_selects_from_the_owner" in res["failed_checks"], res["failed_checks"]
    assert runner.state() == before


def test_refused_on_the_wrong_connection_superuser_database_or_major(cluster, db, runner, mod, monkeypatch):
    """LOW-1 (review): the plan only runs as the expected administrator, non-superuser, on the expected database, on PostgreSQL 15."""
    code, res = runner.run("dry-run", user="postgres")                            # the cluster superuser
    assert code == 2 and "pre_connected_as_expected_admin" in res["failed_checks"]
    monkeypatch.setattr(mod, "EXPECTED_DATABASE", "amjis")                          # a same-shaped CLONE named differently
    code, res = runner.run("dry-run")
    assert code == 2 and "pre_connected_as_expected_admin" in res["failed_checks"]
    monkeypatch.setattr(mod, "EXPECTED_DATABASE", db)
    monkeypatch.setattr(mod, "EXPECTED_MAJOR", cluster.major + 1)
    code, res = runner.run("dry-run")
    assert code == 2 and "pre_connected_as_expected_admin" in res["failed_checks"]
    monkeypatch.setattr(mod, "EXPECTED_MAJOR", cluster.major)
    cluster.su(db, "CREATE ROLE other_admin LOGIN CREATEROLE")
    code, res = runner.run("dry-run", user="other_admin")                           # a CREATEROLE login that is not THE expected administrator
    assert code == 2 and "pre_connected_as_expected_admin" in res["failed_checks"]


def test_refused_when_the_view_already_exists(cluster, db, runner):
    assert runner.run("apply")[0] == 0
    code, res = runner.run("dry-run")
    assert code == 2 and "pre_view_absent" in res["failed_checks"]


def test_refused_when_the_administrator_cannot_assume_the_roles(cluster, db, runner):
    cluster.su(db, "CREATE ROLE weak_admin LOGIN")                              # no CREATEROLE, no membership
    code, res = runner.run("dry-run", user="weak_admin")
    assert code == 2 and "pre_admin_can_assume_the_roles" in res["failed_checks"]


def test_refused_when_row_level_security_is_on(cluster, db, runner):
    cluster.su(db, "ALTER TABLE public.life_events ENABLE ROW LEVEL SECURITY")
    code, res = runner.run("dry-run")
    assert code == 2 and "pre_table_owner_and_rls" in res["failed_checks"]


def test_refused_when_the_accessor_is_not_the_g1c_one(cluster, db, runner):
    cluster.su(db, "CREATE OR REPLACE FUNCTION public.app_chart_context() RETURNS uuid LANGUAGE sql STABLE AS $$ SELECT NULL::uuid $$")
    code, res = runner.run("dry-run")
    assert code == 2 and "step_s2_preconditions" in res["failed_checks"]


# --------------------------------------------------------------------------------------------------------------------------- mutations
def mutate(mod, monkeypatch, tmp_path, old, new, rollback=False):
    src = (mod.SQL_ROLLBACK if rollback else mod.SQL_FORWARD).read_text()
    assert old in src, old
    p = tmp_path / ("mut_rb.sql" if rollback else "mut.sql")
    p.write_text(src.replace(old, new, 1))
    monkeypatch.setattr(mod, "SQL_ROLLBACK" if rollback else "SQL_FORWARD", p)


MUTANTS = {
    "grant_never_made": ("GRANT SELECT ON public.life_events_chart_scoped TO data_plane_builder;", "-- (grant removed)"),
    "grant_by_a_role_that_does_not_own_the_view":
        ("GRANT SELECT ON public.life_events_chart_scoped TO data_plane_builder;", "RESET ROLE; SET LOCAL ROLE data_plane_schema_owner; GRANT SELECT ON public.life_events_chart_scoped TO data_plane_builder;"),
    "grant_to_public": ("GRANT SELECT ON public.life_events_chart_scoped TO data_plane_builder;",
                        "GRANT SELECT ON public.life_events_chart_scoped TO data_plane_builder, PUBLIC;"),
    "default_acl_grantee_not_revoked": ("REVOKE ALL ON public.life_events_chart_scoped FROM PUBLIC, retrieval_census_ro;", "-- (revoke removed)"),
    "no_security_barrier": ("WITH (security_barrier = true) AS", "AS"),
    "security_invoker_instead": ("WITH (security_barrier = true) AS", "WITH (security_barrier = true, security_invoker = true) AS"),
    "chart_filter_removed": ("WHERE chart_id = public.app_chart_context();", "WHERE true;"),
    "filter_on_a_constant_not_the_guc": ("WHERE chart_id = public.app_chart_context();", "WHERE chart_id = 'aaaaaaaa-1111-4222-8333-00000000000a'::uuid;"),
    "transient_create_never_revoked": ("REVOKE CREATE ON SCHEMA public FROM amjis_app;", "-- (revoke removed)"),
    "extra_column_exposed": ("SELECT id, event_id, event_date, category, domain, chart_id\n    FROM public.life_events",
                             "SELECT id, event_id, event_date, category, domain, chart_id, provenance\n    FROM public.life_events"),
    "description_free_text_exposed": ("SELECT id, event_id, event_date, category, domain, chart_id\n    FROM public.life_events",
                                      "SELECT id, event_id, event_date, category, domain, description, chart_id\n    FROM public.life_events"),
    "outcome_observed_exposed": ("SELECT id, event_id, event_date, category, domain, chart_id\n    FROM public.life_events",
                                 "SELECT id, event_id, event_date, category, domain, outcome_observed, chart_id\n    FROM public.life_events"),
    "column_grants_never_revoked": ("REVOKE SELECT (id, event_date, category, description, outcome_observed) ON public.life_events FROM data_plane_builder;", "-- (column revoke removed)"),
    "only_four_of_five_columns_revoked": ("REVOKE SELECT (id, event_date, category, description, outcome_observed) ON public.life_events FROM data_plane_builder;",
                                          "REVOKE SELECT (id, event_date, category, outcome_observed) ON public.life_events FROM data_plane_builder;"),
    "other_roles_column_acl_touched": ("REVOKE SELECT (id, event_date, category, description, outcome_observed) ON public.life_events FROM data_plane_builder;",
                                       "REVOKE SELECT (id, event_date, category, description, outcome_observed) ON public.life_events FROM data_plane_builder; GRANT SELECT (id) ON public.life_events TO role_web_serve;"),
}


@pytest.mark.parametrize("name", sorted(MUTANTS))
def test_each_mutated_safeguard_is_refused_and_nothing_is_committed(name, cluster, db, runner, mod, monkeypatch, tmp_path):
    old, new = MUTANTS[name]
    mutate(mod, monkeypatch, tmp_path, old, new)
    before = runner.state()
    code, dry = runner.run("dry-run")
    print("MUTANT", name, "->", dry["failed_checks"], {k: v for k, v in dry["details"].items() if k.startswith("step_")})
    assert code == 2 and dry["failed_checks"], (name, dry)
    code, res = runner.execute(runner.args("apply", expect_evidence=dry["evidence_digest"]))
    assert code == 1 and res["status"] == "REFUSED_ROLLED_BACK" and res["failed_checks"], (name, res)
    assert runner.state() == before, name                             # not one catalog fact moved


def test_a_warning_only_grant_is_caught_by_the_s8_assertion_not_committed(cluster, db, runner, mod, monkeypatch, tmp_path):
    """The W1-audit trap (P2): a GRANT by a role that holds the privilege WITHOUT grant option is only a WARNING in PostgreSQL ("no privileges were granted")
    and the transaction commits. Here the probes are removed so that ONLY the asserting has_table_privilege check of s8 stands between that silent no-op and COMMIT."""
    src = mod.SQL_FORWARD.read_text()
    a, b = src.index("-- @@STEP s6_behavioural_probe_as_owner"), src.index("-- @@STEP s8_post_assertions")
    src = src[:a] + src[b:]
    old = "GRANT SELECT ON public.life_events_chart_scoped TO data_plane_builder;"
    new = ("GRANT SELECT ON public.life_events_chart_scoped TO data_plane_schema_owner;\nRESET ROLE;\nSET LOCAL ROLE data_plane_schema_owner;\n"
           "GRANT SELECT ON public.life_events_chart_scoped TO data_plane_builder;\nRESET ROLE;\nSET LOCAL ROLE amjis_app;")
    assert old in src
    p = tmp_path / "warn.sql"
    p.write_text(src.replace(old, new, 1))
    monkeypatch.setattr(mod, "SQL_FORWARD", p)
    before = runner.state()
    code, dry = runner.run("dry-run")
    assert code == 2 and dry["failed_checks"] == ["step_s8_post_assertions"], dry["failed_checks"]
    assert "the GRANT did not take" in dry["details"]["step_s8_post_assertions"]
    code, res = runner.execute(runner.args("apply", expect_evidence=dry["evidence_digest"]))
    assert code == 1 and res["status"] == "REFUSED_ROLLED_BACK"
    assert runner.state() == before


def test_the_unmutated_plan_is_green_so_the_mutants_are_what_turns_it_red(runner):
    assert runner.run("dry-run")[0] == 0


def test_a_bare_grant_by_a_role_without_grant_rights_is_a_warning_not_an_error_in_postgres(cluster, db):
    """Why s8 asserts has_table_privilege: PostgreSQL itself only WARNs (no error) and the transaction commits (W1 audit P2); the assertion is the detector."""
    with cluster.conn(db, user="suvarna_reader", autocommit=True) as c:
        c.execute("GRANT SELECT ON public.life_events TO data_plane_builder")           # not the owner, no grant option: a WARNING, no exception
    assert scalar(cluster, db, "SELECT has_table_privilege('data_plane_builder','public.life_events','SELECT')") is False


# ----------------------------------------------------------------------------------------------------------------- interpreter binding (exit 92)
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


def test_apply_refuses_with_exit_92_when_the_dry_run_recorded_no_interpreter(runner, mod):
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


def test_a_superuser_administrator_is_refused(runner):
    code, res = runner.run("dry-run", user="postgres")
    assert code == 2 and res["failed_checks"] == ["pre_connected_as_expected_admin"], res["failed_checks"]


def test_a_failed_step_leaves_a_failed_outcome_file(runner, mod, monkeypatch, tmp_path):
    p = tmp_path / "bad.sql"
    p.write_text(mod.SQL_FORWARD.read_text().replace("CREATE VIEW public.life_events_chart_scoped", "CREATE VIEW public.no_such_schema_x.v", 1))
    monkeypatch.setattr(mod, "SQL_FORWARD", p)
    code, res = runner.run("dry-run")
    outcome = json.loads((pathlib.Path(res["evidence_dir"]) / "outcome.json").read_text())
    assert code == 2 and outcome["status"] == "failed" and outcome["failed_checks"]


# ----------------------------------------------------------------------------------------------------- rollback leg: exact column-grant restoration
ROLLBACK_MUTANTS = {
    "rollback_regrants_only_four_columns": ("GRANT SELECT (id, event_date, category, description, outcome_observed) ON public.life_events TO data_plane_builder;",
                                            "GRANT SELECT (id, event_date, category, outcome_observed) ON public.life_events TO data_plane_builder;"),
    "rollback_never_regrants": ("GRANT SELECT (id, event_date, category, description, outcome_observed) ON public.life_events TO data_plane_builder;", "-- (regrant removed)"),
    "rollback_regrants_with_grant_option": ("GRANT SELECT (id, event_date, category, description, outcome_observed) ON public.life_events TO data_plane_builder;",
                                            "GRANT SELECT (id, event_date, category, description, outcome_observed) ON public.life_events TO data_plane_builder WITH GRANT OPTION;"),
    "rollback_grants_the_table_instead": ("GRANT SELECT (id, event_date, category, description, outcome_observed) ON public.life_events TO data_plane_builder;",
                                          "GRANT SELECT ON public.life_events TO data_plane_builder;"),
}


@pytest.mark.parametrize("name", sorted(ROLLBACK_MUTANTS))
def test_each_mutated_rollback_is_refused_and_leaves_the_applied_state(name, runner, mod, monkeypatch, tmp_path):
    assert runner.run("apply")[0] == 0
    applied = runner.state()
    old, new = ROLLBACK_MUTANTS[name]
    mutate(mod, monkeypatch, tmp_path, old, new, rollback=True)
    code, dry = runner.run("rollback-dry-run")
    print("ROLLBACK-MUTANT", name, "->", dry["failed_checks"], {k: v for k, v in dry["details"].items() if k.startswith("step_")})
    assert code == 2 and dry["failed_checks"], (name, dry)
    code, res = runner.execute(runner.args("rollback", expect_evidence=dry["evidence_digest"]))
    assert code == 1 and res["status"] == "REFUSED_ROLLED_BACK"
    assert runner.state() == applied


def test_rollback_restores_the_original_column_acl_text_and_the_builder_reads_again(cluster, db, runner):
    before = runner.state()
    assert runner.run("apply")[0] == 0
    assert runner.run("rollback")[0] == 0
    after = runner.state()
    assert after["col_acl"] == before["col_acl"] and "data_plane_builder=r/amjis_app" in after["col_acl"]
    with builder(cluster, db) as c:
        c.execute("SELECT description FROM public.life_events LIMIT 1")          # the original (pre-1274) access is back, exactly


def test_rollback_is_refused_if_the_builder_holds_a_column_privilege_after_the_forward_leg(cluster, db, runner):
    assert runner.run("apply")[0] == 0
    cluster.su(db, "GRANT SELECT (id) ON public.life_events TO data_plane_builder", user="amjis_app")
    code, res = runner.run("rollback-dry-run")
    assert code == 2 and "step_r2_preconditions" in res["failed_checks"] or "pre_builder_has_no_privilege_on_life_events" in res["failed_checks"]


# ---------------------------------------------------------------------------------------------- commit_state_unknown has its own exit code (NIT-4)
class _CommitRaises:
    """Delegates to a real connection but the commit() call itself raises (the server may or may not have committed)."""

    def __init__(self, conn, really_commit):
        self._c, self._really = conn, really_commit

    def __getattr__(self, name):
        return getattr(self._c, name)

    def commit(self):
        if self._really:
            self._c.commit()
        raise psycopg.OperationalError("connection dropped at the commit acknowledgement")


@pytest.mark.parametrize("really_commit", [True, False], ids=["server_committed", "server_did_not_commit"])
def test_a_commit_that_raises_is_commit_state_unknown_with_its_own_exit_code(cluster, db, runner, mod, monkeypatch, really_commit):
    _, dry = runner.run("dry-run")
    plan = mod.plan_hash()
    assert mod.EXIT_COMMIT_UNKNOWN == 91 and mod.EXIT_COMMIT_UNKNOWN not in (0, 1, 2, 64, 92, 93, 94, 95, 96, 97, 98)
    monkeypatch.setattr(mod, "launch_gate", lambda: dict(mod.standards().fingerprint(str(mod.gate_dir())), under_test=False))
    monkeypatch.setattr(mod, "connect_admin", lambda: _CommitRaises(cluster.conn(db, user=ADMIN_USER), really_commit))
    monkeypatch.setattr(mod, "install_signal_handlers", lambda: None)
    code = mod.main(["--apply", "--expect-plan", plan, "--expect-evidence", dry["evidence_digest"]])
    assert code == 91
    outcomes = [json.loads(p.read_text()) for p in pathlib.Path(__import__("os").environ["M1274_TEST_EVIDENCE_ROOT"]).glob("apply_*/outcome.json")]
    assert [o["status"] for o in outcomes] == ["commit_state_unknown"]
    assert (runner.state()["view"] is not None) == really_commit               # the database tells the truth the exit code could not
