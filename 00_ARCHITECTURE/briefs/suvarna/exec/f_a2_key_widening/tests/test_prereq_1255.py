"""STEP 0: migration 1255 (PR #2962) must be live before the dry run. READ-ONLY, fails closed, names 1255. The replay's `db` fixture models 1255 (schema/10); here the
grants are REVOKED to prove the refusal, and the verify SQL reads the same state."""
from __future__ import annotations

import subprocess

import pytest

import conftest as cf
from conftest import EXEC_DIR

OWNER_CHECK = "pre_prereq_1255_owner_can_read_brahma_yoga_catalog"
BUILDER_CHECK = "pre_prereq_1255_builder_can_read_the_seven_reference_tables"


@pytest.fixture()
def runner(cluster, mod, db, tmp_path):
    return cf.Runner(cluster, mod, db, tmp_path)


def reader_rows(cluster, db, fname):
    r = subprocess.run([cf.PSQL, "-X", "-A", "-t", "-F", "|", "-h", "127.0.0.1", "-p", str(cluster.port), "-U", "rehearsal_reader", "-d", db,
                        "-f", str(EXEC_DIR / fname)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return {ln.split("|")[0]: ln.split("|") for ln in r.stdout.splitlines() if ln.strip()}


def refused(runner, mode, expect):
    pre = runner.state()
    code, res = runner.run(mode)
    assert code != 0, res
    assert expect in res["failed_checks"], res["failed_checks"]
    assert runner.state() == pre                          # a refusal changes nothing
    return res


def test_the_prerequisite_passes_when_1255_is_live(runner, mod):
    code, res = runner.run("count")
    assert code == 0 and res["checks"][OWNER_CHECK] and res["checks"][BUILDER_CHECK], res["details"]


def test_the_plan_refuses_without_the_owner_grant_and_names_1255(runner, cluster, db):
    cluster.su(db, "REVOKE SELECT ON public.brahma_yoga_catalog FROM data_plane_l1_owner")
    for mode in ("count", "dry-run", "apply"):
        res = refused(runner, mode, OWNER_CHECK)
        assert "migration 1255" in res["details"][OWNER_CHECK] and "brahma_yoga_catalog" in res["details"][OWNER_CHECK]
        assert BUILDER_CHECK not in res["failed_checks"]


@pytest.mark.parametrize("table", ["yoga_family_members", "reference_nakshatra", "reference_nakshatra_pada", "bg_shashtiamsha_deities",
                                   "bg_graha_naisargika_friendship", "bg_motion_state_thresholds", "brahma_vichara_constants"])
def test_the_plan_refuses_when_the_builder_cannot_read_any_one_of_the_seven_tables(runner, cluster, db, table):
    cluster.su(db, f"REVOKE SELECT ON public.{table} FROM data_plane_builder")
    res = refused(runner, "dry-run", BUILDER_CHECK)
    assert "migration 1255" in res["details"][BUILDER_CHECK] and f"public.{table}" in res["details"][BUILDER_CHECK]


def test_a_missing_reference_table_counts_as_missing(runner, cluster, db):
    cluster.su(db, "DROP TABLE public.brahma_vichara_constants")
    refused(runner, "dry-run", BUILDER_CHECK)


def test_the_rollback_does_not_need_1255(runner, cluster, db):
    assert runner.run("apply")[0] == 0
    cluster.su(db, "REVOKE SELECT ON public.brahma_yoga_catalog FROM data_plane_l1_owner")
    code, rb = runner.run("rollback")
    assert code == 0, rb["details"]


@pytest.mark.parametrize("sql", ["verify_before_apply.sql", "verify_after_apply.sql"])
def test_the_verify_sql_reads_the_prerequisite_pass_when_live_and_fail_when_not(runner, cluster, db, sql):
    rows = reader_rows(cluster, db, sql)
    assert rows["60"][-1] == "PASS" and rows["61"][-1] == "PASS", (rows["60"], rows["61"])
    cluster.su(db, "REVOKE SELECT ON public.brahma_yoga_catalog FROM data_plane_l1_owner")
    cluster.su(db, "REVOKE SELECT ON public.reference_nakshatra, public.yoga_family_members FROM data_plane_builder")
    rows = reader_rows(cluster, db, sql)
    assert rows["60"][-1] == "FAIL" and rows["60"][2] == "false" and rows["61"][-1] == "FAIL" and rows["61"][2] == "2"
    assert rows["999"][-1] == "FAIL"
