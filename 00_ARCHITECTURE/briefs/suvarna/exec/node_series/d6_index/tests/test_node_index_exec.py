"""node_index_exec.py against a disposable local Postgres (never the project database; the real credential path is never reached)."""
import json
import pathlib

import psycopg
import pytest

from conftest import ADMIN_USER, MIG

IDX = "ephemeris_daily_date_body_ayanamsha_node_mode_uq"


def idx_exists(cluster, db):
    return cluster.su(db, f"SELECT to_regclass('public.{IDX}') IS NOT NULL")[0][0]


def test_dry_run_runs_the_real_ddl_checks_everything_and_always_rolls_back(cluster, runner, db, tmp_path):
    before = cluster.image(db)
    code, rep = runner.dry()
    assert code == 0 and rep["committed"] is False, rep
    assert all(c["ok"] for c in rep["checks"].values()), rep["checks"]
    assert {"P1_pg15", "P2_owner_is_amjis_app", "P3_index_name_free", "P4_old_key_present", "P5_no_mean_rows",
            "P6_no_foreign_write_lock", "A_acl_unchanged", "A_mem_unchanged", "A_nsp_unchanged", "A_index_diff_is_exactly_the_new_index",
            "A_constraints_unchanged", "A_data_unchanged", "A_index_structure"} <= set(rep["checks"])
    assert len(rep["after"]["index_added"]) == 1 and IDX in rep["after"]["index_added"][0]       # the DDL really ran in the txn
    assert cluster.image(db) == before and not idx_exists(cluster, db)                           # ... and was rolled back
    ev = pathlib.Path(rep["evidence"]["dir"])
    assert {p.name for p in ev.iterdir()} == {"before.json", "reversal.sql", "SHA256SUMS"}
    assert f"DROP INDEX public.{IDX};" in (ev / "reversal.sql").read_text()
    assert json.loads((ev / "before.json").read_text())["plan_hash"] == rep["plan_hash"]
    assert oct((ev / "before.json").stat().st_mode & 0o777) == "0o600" and oct(ev.stat().st_mode & 0o777) == "0o700"


def test_apply_commits_only_the_index_and_leaves_acl_owner_membership_and_data_untouched(cluster, runner, db):
    before = cluster.image(db)
    code, rep = runner.apply()
    assert code == 0 and rep["committed"] is True, rep
    after = cluster.image(db)
    assert idx_exists(cluster, db)
    assert after["idx"] == sorted(before["idx"] + [IDX]) and after["con"] == before["con"]
    for k in ("data", "rel", "nsp", "mem"):
        assert after[k] == before[k], k
    # the executor's session user is not left a member of anything
    assert cluster.su(db, f"SELECT count(*) FROM pg_auth_members WHERE member = '{ADMIN_USER}'::regrole")[0][0] == 0 or ADMIN_USER == "postgres"
    assert cluster.su(db, f"SELECT indisunique AND indisvalid AND indnullsnotdistinct FROM pg_index WHERE indexrelid = '{IDX}'::regclass")[0][0]


def test_a_second_apply_refuses_because_the_index_exists(cluster, runner, db):
    assert runner.apply()[0] == 0
    code, rep = runner.apply()
    assert code == 1 and "P3_index_name_free" in rep["refused"] and rep["committed"] is False


def test_plan_hash_mismatch_refuses_and_changes_nothing(cluster, runner, db, mod):
    before = cluster.image(db)
    code, rep = runner.apply(plan="0" * 64)
    assert code == 1 and rep["refused"] == ["PLAN_hash_matches"] and cluster.image(db) == before


def test_evidence_digest_mismatch_refuses_and_changes_nothing(cluster, runner, db):
    before = cluster.image(db)
    code, rep = runner.apply(evidence="f" * 64)
    assert code == 1 and "E_evidence_digest" in rep["refused"] and cluster.image(db) == before and not idx_exists(cluster, db)


def test_state_drift_between_dry_run_and_apply_refuses(cluster, runner, db, mod):
    _, rep = runner.dry()
    cluster.su(db, "INSERT INTO public.ephemeris_daily (date, body, tropical_longitude) VALUES ('2010-01-01', 'Sun', 1)")
    code, rep2 = runner.execute(["--apply", "--expect-plan", mod.plan_hash(), "--expect-evidence", rep["evidence_digest"]])
    assert code == 1 and "E_evidence_digest" in rep2["refused"] and not idx_exists(cluster, db)


@pytest.mark.parametrize("setup,check", [
    ("ALTER TABLE public.ephemeris_daily OWNER TO other_writer", "P2_owner_is_amjis_app"),
    ("DELETE FROM public.ephemeris_daily WHERE date='2000-01-01' AND body='Rahu'; "
     "INSERT INTO public.ephemeris_daily (date, body, tropical_longitude, node_mode) VALUES ('2000-01-01','Rahu',1,'mean')", None),
    ("ALTER TABLE public.ephemeris_daily DROP CONSTRAINT ephemeris_daily_date_body_ayanamsha_id_key", "P4_old_key_present"),
    (f"CREATE TABLE public.{IDX} (x int)", "P3_index_name_free"),
], ids=["not-owned-by-amjis_app", "mean-row-exists", "old-key-missing", "name-taken"])
def test_pre_check_refusals_issue_no_ddl(cluster, runner, db, setup, check):
    cluster.su(db, setup)
    before = cluster.image(db)
    code, rep = runner.dry()
    assert code == 2 and rep["committed"] is False and "after" not in rep       # refused before any DDL ran
    assert (check in rep["refused"]) if check else ("P5_no_mean_rows" in rep["refused"])
    assert cluster.image(db) == before
    code, _ = runner.apply()
    assert code == 1 and cluster.image(db) == before


def test_a_foreign_write_lock_refuses_p6(cluster, runner, db):
    with cluster.conn(db, user="other_writer") as other:            # a rebuild in flight: an open transaction holding RowExclusive
        other.execute("INSERT INTO public.ephemeris_daily (date, body, tropical_longitude) VALUES ('2010-01-01', 'Sun', 1)")
        code, rep = runner.dry()
        assert code == 2 and "P6_no_foreign_write_lock" in rep["refused"]
        other.rollback()
    assert runner.dry()[0] == 0


def test_unwritable_evidence_aborts_and_rolls_back(cluster, runner, db, tmp_path, monkeypatch):
    blocker = tmp_path / "blocker"
    blocker.write_text("x")
    monkeypatch.setenv("NODEIDX_TEST_EVIDENCE_ROOT", str(blocker / "sub"))
    before = cluster.image(db)
    code, rep = runner.dry()
    assert code == 2 and rep["refused"][0].startswith("EVIDENCE:") and cluster.image(db) == before


def test_plan_hash_binds_the_migration_text_and_the_executor(mod, tmp_path, monkeypatch):
    base = mod.plan_hash()
    mutated = tmp_path / "m.sql"
    mutated.write_text(MIG.read_text() + "\n-- one more comment\n")
    monkeypatch.setenv("NODEIDX_TEST_MIGRATION_FILE", str(mutated))
    assert mod.plan_hash() != base
    assert mod.plan_hash(sha="0" * 64) != mod.plan_hash(sha="1" * 64)
    text = mod.render_plan(mod.exec_sha(), mod.sha_file(MIG))
    assert mod.sha_file(MIG) in text and mod.exec_sha() in text and "run_gated.sh" in text


def test_a_migration_that_raises_rolls_everything_back_including_the_memberships(cluster, runner, db, tmp_path, monkeypatch):
    bad = tmp_path / "bad.sql"
    bad.write_text("SET LOCAL lock_timeout = '5s';\nDO $x$ BEGIN RAISE EXCEPTION 'boom'; END $x$;\n")
    monkeypatch.setenv("NODEIDX_TEST_MIGRATION_FILE", str(bad))
    before = cluster.image(db)
    with pytest.raises(psycopg.errors.RaiseException):
        runner.dry()
    assert cluster.image(db) == before


def test_pre_existing_memberships_are_not_revoked(cluster, runner, db):
    if ADMIN_USER == "postgres":
        pytest.skip("superuser admin: no membership needed")
    cluster.su(db, f"GRANT amjis_app TO {ADMIN_USER}")
    before = cluster.image(db)
    code, rep = runner.apply()
    assert code == 0, rep
    after = cluster.image(db)
    assert after["mem"] == before["mem"] and ["amjis_app", ADMIN_USER] in [list(r) for r in after["mem"]]


def test_apply_arguments_are_mandatory(mod):
    with pytest.raises(SystemExit):
        mod.parse_args(["--apply"])
    with pytest.raises(SystemExit):
        mod.parse_args(["--apply", "--expect-plan", "x"])
    with pytest.raises(SystemExit):
        mod.parse_args([])


def test_plan_md_pins_the_current_hashes_and_plan_txt_is_current(mod):
    plan = (pathlib.Path(__file__).resolve().parent.parent / "PLAN.md").read_text()
    assert mod.plan_hash() in plan and mod.exec_sha() in plan and mod.sha_file(MIG) in plan, "re-run make_plan.py --write and update PLAN.md"
    txt = (pathlib.Path(__file__).resolve().parent.parent / "plan.txt").read_text()
    assert txt.rstrip("\n") == mod.render_plan(mod.exec_sha(), mod.sha_file(MIG)), "re-run make_plan.py --write"
