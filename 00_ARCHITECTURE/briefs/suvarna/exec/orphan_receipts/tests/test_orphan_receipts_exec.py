"""Tests for orphan_receipts_exec.py against a disposable local Postgres (see conftest.py). Every refusal has a test."""
import hashlib
import json
import os
import pathlib
import stat

import psycopg
import pytest

import conftest
import fixture_schema as fx

CANON, W, DECL = fx.CANON, fx.W, fx.DECL
EXEC_DIR = pathlib.Path(__file__).resolve().parent.parent


def failed(res):
    return set(res["failed_checks"])


def rows(cl, db, asset="ga_positions", chart=CANON):
    r = cl.su(db, "SELECT partition_key, receipt_state FROM asset_provenance_receipts WHERE asset_id=%s AND chart_id=%s ORDER BY 1", (asset, chart))
    f = cl.su(db, "SELECT partition_key, freshness_state FROM asset_freshness WHERE asset_id=%s AND chart_id=%s ORDER BY 1", (asset, chart))
    return r, f


def assert_unchanged(cl, db, before):
    assert cl.image(db) == before


# ------------------------------------------------------------------------------------------------ plan text + hash (no DB)
def test_plan_txt_is_the_rendering_for_the_committed_executor(mod):
    text = (EXEC_DIR / "plan.txt").read_text()
    assert text.rstrip("\n") == mod.render_plan("ga_positions", CANON, mod.exec_sha()), "regenerate plan.txt: python3 make_plan.py"


def test_plan_hash_is_offline_and_binds_the_executor(mod):
    h = mod.plan_hash("ga_positions", CANON)
    plan = mod.render_plan("ga_positions", CANON, mod.exec_sha())
    assert h == hashlib.sha256((plan + "\n" + json.dumps(mod.expected_diff("ga_positions", CANON))).encode()).hexdigest()
    assert mod.exec_sha() in plan
    assert mod.plan_hash("ga_positions", CANON, "0" * 64) != h            # a different executor sha is a different hash
    assert mod.plan_hash("bo_laksana", CANON) != h                        # asset-bound
    assert mod.plan_hash("ga_positions", "cb73cd3d-0000-4000-8000-000000000001") != h  # chart-bound


def test_plan_md_quotes_the_current_hashes_and_plan_txt(mod):
    md = (EXEC_DIR / "PLAN.md").read_text()
    assert mod.exec_sha() in md and mod.sha_file(mod.VERDICT_SQL_FILE) in md
    for a in ("ga_positions", "bo_laksana", "bo_sangati", "bo_cgm_motifs", "bo_upaya"):
        assert mod.plan_hash(a, CANON) in md, a
    assert (EXEC_DIR / "plan.txt").read_text().rstrip("\n") in md


def test_plan_text_contains_the_exact_delete_statements(mod):
    plan = mod.render_plan("ga_positions", CANON, "0" * 64)
    assert "DELETE FROM public.asset_freshness WHERE asset_id = 'ga_positions'" in plan
    assert "DELETE FROM public.asset_provenance_receipts WHERE asset_id = 'ga_positions'" in plan
    assert plan.count("DELETE FROM") == 2
    assert "SET LOCAL lock_timeout = '5s'" in plan and "SET LOCAL statement_timeout = '5s'" in plan


# ------------------------------------------------------------------------------------------------ CLI parameters
def test_cli_requires_explicit_asset_and_chart_and_mode(mod):
    for argv in ([], ["--asset", "ga_positions", "--dry-run"], ["--chart", CANON, "--dry-run"], ["--asset", "ga_positions", "--chart", CANON]):
        with pytest.raises(SystemExit):
            mod.parse_args(argv)


def test_cli_rejects_bad_asset_and_chart(mod):
    for argv in (["--asset", "GA;DROP", "--chart", CANON, "--dry-run"], ["--asset", "ga_positions", "--chart", "not-a-uuid", "--dry-run"]):
        with pytest.raises(SystemExit):
            mod.parse_args(argv)


def test_apply_requires_expect_plan_and_min_build_after(mod, runner, cluster, db):
    before = cluster.image(db)
    with pytest.raises(SystemExit):
        mod.parse_args(["--asset", "ga_positions", "--chart", CANON, "--apply"])
    a = mod.parse_args(["--asset", "ga_positions", "--chart", CANON, "--apply", "--expect-plan", mod.plan_hash("ga_positions", CANON)])
    with pytest.raises(SystemExit, match="min-build-after"):
        mod.execute(a, lambda: pytest.fail("must not connect"), evidence_root=runner.ev)
    a = mod.parse_args(["--asset", "ga_positions", "--chart", CANON, "--apply", "--expect-plan", mod.plan_hash("ga_positions", CANON),
                        "--min-build-after", "2026-10-05T09:00:00"])  # naive timestamp
    with pytest.raises(SystemExit, match="timezone"):
        mod.execute(a, lambda: pytest.fail("must not connect"), evidence_root=runner.ev)
    assert_unchanged(cluster, db, before)


def test_hash_mismatch_on_apply_refuses_before_connecting(mod, runner, cluster, db):
    before = cluster.image(db)
    a = mod.parse_args(["--asset", "ga_positions", "--chart", CANON, "--apply", "--expect-plan", "0" * 64, "--min-build-after", fx.MIN_AFTER])
    with pytest.raises(SystemExit, match="does not equal the plan hash"):
        mod.execute(a, lambda: pytest.fail("must not connect"), evidence_root=runner.ev)
    assert not os.path.exists(runner.ev)                 # nothing written either
    assert_unchanged(cluster, db, before)


def test_hash_for_other_asset_does_not_authorise_this_asset(mod, runner, cluster, db):
    before = cluster.image(db)
    with pytest.raises(SystemExit, match="does not equal the plan hash"):
        runner.run("apply", expect_plan=mod.plan_hash("bo_laksana", CANON))
    assert_unchanged(cluster, db, before)


# ------------------------------------------------------------------------------------------------ happy path
def test_dry_run_all_checks_hold_and_rolls_back_byte_identically(runner, cluster, db, mod):
    before = cluster.image(db)
    code, res = runner.run("dry")
    assert code == 0, res
    assert res["status"] == "DRY_RUN_ROLLED_BACK_ALL_CHECKS_HOLD" and res["failed_checks"] == [] and res["skipped_checks"] == []
    assert res["plan_hash"] == mod.plan_hash("ga_positions", CANON)
    assert res["verdict_diff"] == {"ga_positions": ["receipt_not_proven", "RESOLVED"]}
    rc = res["rowcounts"]
    assert rc["orphan_rows_found"] == {"asset_provenance_receipts": 1, "asset_freshness": 1}
    assert rc["delete_rowcounts"] == {"asset_provenance_receipts": 1, "asset_freshness": 1}
    assert rc["chart_scoped_before"]["asset_provenance_receipts"] - rc["chart_scoped_after"]["asset_provenance_receipts"] == 1
    assert rc["chart_scoped_before"]["asset_freshness"] - rc["chart_scoped_after"]["asset_freshness"] == 1
    assert res["acl_diff"] == [] and res["rls_diff"] == res["policy_diff"] == res["membership_diff"] == res["owner_diff"] == 0
    assert res["verdict_counts"]["after"]["resolved"] == res["verdict_counts"]["before"]["resolved"] + 1
    assert res["checks"]["A_membership_diff_empty"]["detail"]["transient_membership_granted"] is (conftest.ADMIN_USER == "adm")  # adm is not a member of amjis_app
    assert_unchanged(cluster, db, before)               # ROLLBACK: DB byte-identical, incl. catalogs and memberships
    assert rows(cluster, db) == ([(W, "unknown"), (DECL, "proven")], [(W, "stale"), (DECL, "fresh")])


def test_dry_run_without_min_build_after_is_a_counterfactual_not_a_rehearsal(runner, cluster, db):
    """Today's production shape: the OLD declared receipt is already proven/fresh and 'later' than the orphan's build, so
    without the --min-build-after gate every check would hold. The dry run must say so plainly and exit 3 (apply refuses)."""
    before = cluster.image(db)
    code, res = runner.run("dry", min_after=None)
    assert code == 3 and res["status"] == "DRY_RUN_ROLLED_BACK_COUNTERFACTUAL_NO_MIN_BUILD_AFTER" and res["warnings"]
    assert res["verdict_diff"] == {"ga_positions": ["receipt_not_proven", "RESOLVED"]}      # shows what the delete WOULD do
    assert_unchanged(cluster, db, before)


def test_evidence_files_modes_hashes_and_content(runner, mod):
    code, res = runner.run("dry")
    bi = res["before_images"]
    d = pathlib.Path(bi["dir"])
    assert d.name.startswith("ga_positions_482012f1_") and d.name.endswith("Z") and len(d.name.split("_")[-1]) == 22
    assert stat.S_IMODE(d.stat().st_mode) == 0o700
    for n in ("before_images.json", "reversal.sql", "SHA256SUMS"):
        assert stat.S_IMODE((d / n).stat().st_mode) == 0o600
    for n in ("before_images.json", "reversal.sql"):
        assert bi[n]["sha256"] == hashlib.sha256((d / n).read_bytes()).hexdigest()
        assert "%s  %s" % (bi[n]["sha256"], n) in (d / "SHA256SUMS").read_text()
    saved = json.loads((d / "result.json").read_text())                   # the printed diff JSON is kept with the evidence
    assert saved["plan_hash"] == res["plan_hash"] and saved["status"] == res["status"] == "DRY_RUN_ROLLED_BACK_ALL_CHECKS_HOLD"
    img = json.loads((d / "before_images.json").read_text())
    rec = img["tables"]["asset_provenance_receipts"]["rows"]
    fr = img["tables"]["asset_freshness"]["rows"]
    assert len(rec) == 1 and len(fr) == 1 and rec[0]["partition_key"] == W and fr[0]["partition_key"] == W
    assert set(rec[0]) == {"asset_id", "chart_id", "scope_key", "partition_key", "receipt_version", "code_digest", "config_digest",
                           "upstream_digest", "partition_digest", "output_digest", "upstream_receipts", "receipt_state",
                           "unknown_reasons", "observed_at", "build_id", "output_digest_spec_sha256"}   # ALL columns
    assert set(fr[0]) == {"asset_id", "chart_id", "scope_key", "partition_key", "freshness_state", "reasons", "receipt_version", "observed_at"}
    rev = (d / "reversal.sql").read_text()
    assert rev.count("INSERT INTO") == 2 and "scope_key" not in rev.split("BEGIN;")[1].split("VALUES")[0]  # generated column not inserted
    assert "SET LOCAL ROLE amjis_app" in rev


def test_apply_commits_exactly_two_rows_and_reversal_restores_byte_for_byte(runner, cluster, db, mod):
    before = cluster.image(db)
    code, res = runner.run("apply")
    assert code == 0 and res["status"] == "COMMITTED", res
    r, f = rows(cluster, db)
    assert r == [(DECL, "proven")] and f == [(DECL, "fresh")]               # only the W pair is gone
    after = cluster.image(db)
    assert after["asset_provenance_receipts"][1] == before["asset_provenance_receipts"][1] - 1
    assert after["asset_freshness"][1] == before["asset_freshness"][1] - 1
    for t in ("charts", "asset_registry", "asset_output_digest_specs", "build_runs", "build_run_assets"):
        assert after[t] == before[t]                                            # nothing else touched
    for k in ("rel", "pol", "mem"):
        assert after[k] == before[k]                                            # ACL/RLS/policy/membership identical (transient membership revoked)
    # the resolver now serves ga_positions, and only ga_positions moved
    verdicts_after = {a: v for a, v, _ in cluster.su(db, mod.load_verdict_sql().replace("%(chart)s", "'%s'" % CANON))}
    assert verdicts_after["ga_positions"] == "RESOLVED" and verdicts_after["bo_laksana"] == "receipt_not_proven"
    # reversal: re-inserts both rows; whole DB returns to the pre-apply image, byte for byte
    rev = pathlib.Path(res["before_images"]["reversal.sql"]["path"])
    p = cluster.psql_file(db, rev)
    assert p.returncode == 0, p.stderr
    assert cluster.image(db) == before


def test_apply_with_matching_evidence_digest_commits(runner, cluster, db):
    _, dry = runner.run("dry")
    code, res = runner.run("apply", expect_evidence=dry["evidence_digest"])
    assert code == 0 and res["status"] == "COMMITTED"
    assert res["evidence_digest"] == dry["evidence_digest"]                     # dry run and apply show the identical evidence


def test_apply_with_wrong_evidence_digest_refuses_and_rolls_back(runner, cluster, db):
    before = cluster.image(db)
    code, res = runner.run("apply", expect_evidence="0" * 64)
    assert code == 1 and res["status"] == "REFUSED_ROLLED_BACK" and failed(res) == {"E_evidence_digest_matches_expected"}
    assert_unchanged(cluster, db, before)


def test_generalised_to_a_second_asset_and_leaves_the_first_alone(runner, cluster, db):
    """The same executor, parameterised by --asset, retires bo_laksana's pair and touches nothing of ga_positions."""
    code, res = runner.run("apply", asset="bo_laksana")
    assert code == 0, res
    assert res["verdict_diff"] == {"bo_laksana": ["receipt_not_proven", "RESOLVED"]}
    assert rows(cluster, db, "bo_laksana")[0] == [(DECL, "proven")]
    assert rows(cluster, db, "ga_positions") == ([(W, "unknown"), (DECL, "proven")], [(W, "stale"), (DECL, "fresh")])


def test_chart_scoping_other_charts_rows_never_touched(runner, cluster, db):
    """A W row of the SAME asset on another chart is a different key and must survive."""
    cluster.su(db, "INSERT INTO build_runs (id, chart_id, scope, action, state, plan, triggered_by, created_at) VALUES (%s,%s,'asset','rebuild','completed','{}','f','2026-09-07')", (fx.uid("xo"), fx.OTHER))
    cluster.su(db, "INSERT INTO asset_provenance_receipts (asset_id, chart_id, partition_key, receipt_version, receipt_state, build_id) VALUES ('ga_positions',%s,%s,'v','unknown',%s)", (fx.OTHER, W, fx.uid("xo")))
    cluster.su(db, "INSERT INTO asset_freshness (asset_id, chart_id, partition_key, freshness_state, receipt_version) VALUES ('ga_positions',%s,%s,'stale','v')", (fx.OTHER, W))
    code, res = runner.run("apply")
    assert code == 0, res
    assert cluster.su(db, "SELECT count(*) FROM asset_provenance_receipts WHERE asset_id='ga_positions' AND chart_id=%s", (fx.OTHER,)) == [(1,)]
    assert cluster.su(db, "SELECT count(*) FROM asset_freshness WHERE asset_id='ga_positions' AND chart_id=%s", (fx.OTHER,)) == [(1,)]


# ------------------------------------------------------------------------------------------------ refusals (each also in apply mode: nothing committed)
def refused(runner, cluster, db, expect_failed, mode="apply", **kw):
    before = cluster.image(db)
    code, res = runner.run(mode, **kw)
    assert code != 0, res
    assert res["status"] in ("REFUSED_ROLLED_BACK", "DRY_RUN_ROLLED_BACK_REFUSED")
    assert expect_failed <= failed(res), (expect_failed, res["failed_checks"])
    assert_unchanged(cluster, db, before)            # rolled back: DB byte-identical
    return res


def test_refuse_not_an_orphan_registry_declares_no_partition(runner, cluster, db):
    cluster.su(db, "UPDATE asset_registry SET natural_key_partition=NULL WHERE asset_id='ga_positions'")
    res = refused(runner, cluster, db, {"P1_registry_declares_partition"})
    assert res["checks"]["D_delete_rowcounts_are_1_and_1"]["ok"] is None        # no DELETE was even issued


def test_refuse_registry_declares_the_whole_asset_key_itself(runner, cluster, db):
    cluster.su(db, "UPDATE asset_registry SET natural_key_partition=%s WHERE asset_id='ga_positions'", (W,))
    refused(runner, cluster, db, {"P1_registry_declares_partition"})


def test_refuse_asset_not_in_registry(runner, cluster, db):
    before = cluster.image(db)
    code, res = runner.run("dry", asset="ga_not_registered")
    assert code == 2 and "P1_registry_declares_partition" in failed(res) and "P4_rowcount_receipt_is_1" in failed(res)
    assert_unchanged(cluster, db, before)


def test_refuse_no_declared_partition_receipt_exists(runner, cluster, db):
    cluster.su(db, "DELETE FROM asset_freshness WHERE asset_id='ga_positions' AND partition_key=%s", (DECL,))
    cluster.su(db, "DELETE FROM asset_provenance_receipts WHERE asset_id='ga_positions' AND partition_key=%s", (DECL,))
    res = refused(runner, cluster, db, {"P3_later_proven_declared_receipt"})
    assert res["checks"]["P3_later_proven_declared_receipt"]["detail"] == {"found": False}


@pytest.mark.parametrize("sql", [
    "UPDATE asset_provenance_receipts SET receipt_state='unknown', output_digest_spec_sha256=NULL WHERE asset_id='ga_positions' AND partition_key=%(d)s",
    "UPDATE asset_freshness SET freshness_state='stale' WHERE asset_id='ga_positions' AND partition_key=%(d)s",
    "UPDATE asset_freshness SET freshness_state='unknown' WHERE asset_id='ga_positions' AND partition_key=%(d)s",
    "UPDATE build_runs SET state='failed' WHERE id=(SELECT build_id FROM asset_provenance_receipts WHERE asset_id='ga_positions' AND partition_key=%(d)s)",
    "DELETE FROM build_run_assets WHERE run_id=(SELECT build_id FROM asset_provenance_receipts WHERE asset_id='ga_positions' AND partition_key=%(d)s)",
], ids=["declared-unknown", "declared-stale", "declared-freshness-unknown", "declared-build-not-completed", "declared-build-asset-row-missing"])
def test_refuse_declared_receipt_not_proven_fresh_or_not_from_a_completed_build(runner, cluster, db, sql):
    cluster.su(db, sql, {"d": DECL})
    refused(runner, cluster, db, {"P3_later_proven_declared_receipt"})


def test_refuse_declared_receipt_older_than_min_build_after(runner, cluster, db):
    """The S-L1 guard: the OLD declared receipts (like production's 09-07 rows) must not satisfy 'from the rebuild'."""
    res = refused(runner, cluster, db, {"P3_later_proven_declared_receipt"}, min_after="2026-10-05T11:00:00+00:00")
    d = res["checks"]["P3_later_proven_declared_receipt"]["detail"]
    assert d["found"] and d["after_min_build_after"] is False and d["newer_than_orphan_build"] is True


def test_refuse_declared_receipt_observed_after_but_build_created_before_min(runner, cluster, db):
    cluster.su(db, "UPDATE build_runs SET created_at='2026-10-05T08:00:00Z' WHERE id=(SELECT build_id FROM asset_provenance_receipts WHERE asset_id='ga_positions' AND partition_key=%s)", (DECL,))
    refused(runner, cluster, db, {"P3_later_proven_declared_receipt"})     # receipt observed 10:00:30 > 09:00 but its build was created 08:00


def test_refuse_old_09_07_style_declared_receipt_even_without_min_build_after_gate_it_must_be_newer_than_orphan_build(runner, cluster, db):
    """Declared receipt whose build is OLDER than the orphan's build can never supersede it (dry-run without --min-build-after)."""
    cluster.su(db, "UPDATE build_runs SET created_at='2026-09-01T00:00:00Z' WHERE id=(SELECT build_id FROM asset_provenance_receipts WHERE asset_id='ga_positions' AND partition_key=%s)", (DECL,))
    res = refused(runner, cluster, db, {"P3_later_proven_declared_receipt"}, mode="dry", min_after=None)
    assert res["checks"]["P3_later_proven_declared_receipt"]["detail"]["newer_than_orphan_build"] is False


def test_refuse_orphan_row_is_proven_never_delete_a_proven_row(runner, cluster, db):
    cluster.su(db, "UPDATE asset_provenance_receipts SET receipt_state='proven' WHERE asset_id='ga_positions' AND partition_key=%s", (W,))
    refused(runner, cluster, db, {"P2_orphan_is_unproven"})


def test_refuse_orphan_freshness_is_fresh(runner, cluster, db):
    cluster.su(db, "UPDATE asset_freshness SET freshness_state='fresh' WHERE asset_id='ga_positions' AND partition_key=%s", (W,))
    refused(runner, cluster, db, {"P2_orphan_is_unproven"})


def test_refuse_rowcount_zero_receipt(runner, cluster, db):
    cluster.su(db, "DELETE FROM asset_provenance_receipts WHERE asset_id='ga_positions' AND partition_key=%s", (W,))
    refused(runner, cluster, db, {"P4_rowcount_receipt_is_1"})


def test_refuse_rowcount_zero_freshness(runner, cluster, db):
    cluster.su(db, "DELETE FROM asset_freshness WHERE asset_id='ga_positions' AND partition_key=%s", (W,))
    refused(runner, cluster, db, {"P4_rowcount_freshness_is_1"})


def test_refuse_rowcount_two(runner, cluster, db):
    """The real PK makes 2 impossible; drop it in the fixture to prove the check refuses anyway (defence in depth)."""
    cluster.su(db, "ALTER TABLE asset_provenance_receipts DROP CONSTRAINT asset_provenance_receipts_pkey")
    cluster.su(db, "ALTER TABLE asset_freshness DROP CONSTRAINT asset_freshness_pkey")
    cluster.su(db, "INSERT INTO asset_provenance_receipts (asset_id, chart_id, partition_key, receipt_version, receipt_state, observed_at, build_id) "
                   "SELECT asset_id, chart_id, partition_key, receipt_version, receipt_state, observed_at, build_id FROM asset_provenance_receipts WHERE asset_id='ga_positions' AND partition_key=%s", (W,))
    cluster.su(db, "INSERT INTO asset_freshness (asset_id, chart_id, partition_key, freshness_state, receipt_version, observed_at) "
                   "SELECT asset_id, chart_id, partition_key, freshness_state, receipt_version, observed_at FROM asset_freshness WHERE asset_id='ga_positions' AND partition_key=%s", (W,))
    res = refused(runner, cluster, db, {"P4_rowcount_receipt_is_1", "P4_rowcount_freshness_is_1"})
    assert res["checks"]["P4_rowcount_receipt_is_1"]["detail"] == {"found": 2}


@pytest.mark.parametrize("state", ["planned", "running", "paused"])
def test_refuse_build_in_flight_on_another_chart(runner, cluster, db, state):
    cluster.su(db, "INSERT INTO build_runs (chart_id, scope, action, state, plan, triggered_by) VALUES (%s,'asset','rebuild',%s,'{}','fixture')", (fx.OTHER, state))
    res = refused(runner, cluster, db, {"P5_no_build_in_flight"})
    assert res["checks"]["P5_no_build_in_flight"]["detail"]["chart_prefix_state"] == [["cb73cd3d", state]]
    assert res["checks"]["D_delete_rowcounts_are_1_and_1"]["ok"] is None


def test_refuse_build_in_flight_on_the_same_chart(runner, cluster, db):
    cluster.su(db, "INSERT INTO build_runs (chart_id, scope, action, state, plan, triggered_by) VALUES (%s,'asset','rebuild','running','{}','fixture')", (CANON,))
    refused(runner, cluster, db, {"P5_no_build_in_flight"})


@pytest.mark.parametrize("ddl,check", [
    ("GRANT SELECT ON public.build_run_assets TO drift_target", "A_acl_diff_empty"),
    ("GRANT DELETE ON public.asset_freshness TO data_plane_builder", "A_acl_diff_empty"),
    ("ALTER TABLE public.build_run_assets ENABLE ROW LEVEL SECURITY", "A_rls_diff_empty"),
    ("CREATE POLICY drift_policy ON public.build_run_assets USING (true)", "A_policy_diff_empty"),
    ("GRANT drift_target TO drift_member", "A_membership_diff_empty"),
    ("ALTER TABLE public.charts OWNER TO drift_target", "A_owner_diff_empty"),
], ids=["extra-grant", "builder-gains-DELETE", "rls-enabled", "policy-created", "membership-added", "owner-changed"])
def test_refuse_acl_rls_policy_membership_drift_mid_flight(runner, cluster, db, ddl, check):
    """A SECURITY DEFINER trigger (superuser-owned) fires during the DELETE and changes the catalog mid-transaction."""
    cluster.su(db, "CREATE FUNCTION public.drift_fn() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS "
                   "$f$ BEGIN EXECUTE %s; RETURN NULL; END $f$" % ("$q$" + ddl + "$q$"))
    cluster.su(db, "CREATE TRIGGER drift AFTER DELETE ON public.asset_freshness FOR EACH ROW EXECUTE FUNCTION public.drift_fn()")
    refused(runner, cluster, db, {check})


def test_refuse_verdict_diff_contains_an_extra_asset(runner, cluster, db):
    """A side-effect (trigger) flips ANOTHER asset's verdict during the DELETE: the diff is no longer exactly {asset: ...}."""
    cluster.su(db, "CREATE FUNCTION public.side_fn() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS "
                   "$f$ BEGIN UPDATE public.asset_freshness SET freshness_state='stale' WHERE asset_id='ga_vargas' AND chart_id='%s'; RETURN NULL; END $f$" % CANON)
    cluster.su(db, "CREATE TRIGGER side AFTER DELETE ON public.asset_freshness FOR EACH ROW EXECUTE FUNCTION public.side_fn()")
    res = refused(runner, cluster, db, {"V_verdict_diff_is_exactly_the_asset", "D_no_other_row_touched"})
    assert res["checks"]["V_verdict_diff_is_exactly_the_asset"]["detail"]["diff"] == {
        "ga_positions": ["receipt_not_proven", "RESOLVED"], "ga_vargas": ["RESOLVED", "receipt_not_fresh"]}


def test_refuse_verdict_diff_when_asset_does_not_become_resolved(runner, cluster, db):
    """Resolver says the declared partition is unfit for another reason (spec retired): deleting the W row would not RESOLVE it."""
    cluster.su(db, "UPDATE asset_output_digest_specs SET retired_at=now() WHERE asset_id='ga_positions'")
    refused(runner, cluster, db, {"V_verdict_diff_is_exactly_the_asset"})


def test_refuse_other_row_touched_by_a_side_effect_without_verdict_change(runner, cluster, db):
    cluster.su(db, "CREATE FUNCTION public.side2_fn() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS "
                   "$f$ BEGIN UPDATE public.asset_freshness SET reasons='[\"x\"]'::jsonb WHERE asset_id='ga_vargas' AND chart_id='%s'; RETURN NULL; END $f$" % CANON)
    cluster.su(db, "CREATE TRIGGER side2 AFTER DELETE ON public.asset_freshness FOR EACH ROW EXECUTE FUNCTION public.side2_fn()")
    res = refused(runner, cluster, db, {"D_no_other_row_touched"})
    assert "V_verdict_diff_is_exactly_the_asset" not in failed(res)           # verdicts unchanged: ONLY the md5 map caught it


def test_refuse_delete_rowcount_not_1_when_state_guard_excludes_row(runner, cluster, db, mod):
    """A BEFORE DELETE trigger that swallows the delete (RETURN NULL) yields rowcount 0: refused, not committed."""
    cluster.su(db, "CREATE FUNCTION public.swallow_fn() RETURNS trigger LANGUAGE plpgsql AS $f$ BEGIN RETURN NULL; END $f$")
    cluster.su(db, "CREATE TRIGGER swallow BEFORE DELETE ON public.asset_provenance_receipts FOR EACH ROW EXECUTE FUNCTION public.swallow_fn()")
    res = refused(runner, cluster, db, {"D_delete_rowcounts_are_1_and_1"})
    assert res["checks"]["D_delete_rowcounts_are_1_and_1"]["detail"] == {"freshness": 1, "receipt": 0}


# ------------------------------------------------------------------------------------------------ evidence
def test_refuse_to_start_when_before_image_dir_is_unwritable(runner, cluster, db, tmp_path):
    ro = tmp_path / "ro"
    ro.mkdir()
    ro.chmod(0o500)
    try:
        if os.access(ro, os.W_OK):
            pytest.skip("running as a user that ignores directory modes")
        before = cluster.image(db)
        code, res = runner.run("apply", evidence_root=str(ro / "OrphanReceipts"))
        assert code == 1 and res["status"] == "ABORTED_ROLLED_BACK" and "before-images not writable" in res["reason"]
        assert_unchanged(cluster, db, before)                       # nothing deleted: the evidence is written BEFORE any DELETE
        code, res = runner.run("dry", evidence_root=str(ro / "OrphanReceipts"))
        assert code == 1 and res["status"] == "ABORTED_ROLLED_BACK"  # the dry run aborts too
    finally:
        ro.chmod(0o700)


def test_evidence_written_even_when_a_precheck_refuses(runner, cluster, db):
    cluster.su(db, "DELETE FROM asset_provenance_receipts WHERE asset_id='ga_positions' AND partition_key=%s", (DECL,))
    code, res = runner.run("dry")
    assert code == 2
    d = pathlib.Path(res["before_images"]["dir"])
    assert (d / "before_images.json").exists() and (d / "reversal.sql").exists()


def test_two_runs_in_the_same_second_do_not_overwrite_evidence(runner, mod):
    import datetime as dt
    now = dt.datetime(2026, 10, 6, 1, 2, 3, tzinfo=dt.timezone.utc)
    a = runner.args("dry")
    c1, r1 = mod.execute(a, lambda: runner.cl.conn(runner.db, user=conftest.ADMIN_USER), evidence_root=runner.ev, now=now)
    c2, r2 = mod.execute(a, lambda: runner.cl.conn(runner.db, user=conftest.ADMIN_USER), evidence_root=runner.ev, now=now)
    assert c1 == 0 and c2 == 1 and r2["status"] == "ABORTED_ROLLED_BACK"      # O_EXCL / exist_ok=False: never silently overwritten


# ------------------------------------------------------------------------------------------------ the SQL files
def test_sql_files_are_read_only_single_statements():
    for f in ("orphan_count.sql", "resolver_verdicts.sql"):
        body = "\n".join(l for l in (EXEC_DIR / f).read_text().splitlines() if not l.lstrip().startswith("--")).upper()
        for bad in ("INSERT ", "UPDATE ", "DELETE ", "DROP ", "ALTER ", "GRANT ", "TRUNCATE ", "CREATE "):
            assert bad not in body.replace("FOR UPDATE", "")


def test_orphan_count_sql_counts_exactly_the_orphans(cluster, db):
    sql = (EXEC_DIR / "orphan_count.sql").read_text()
    got = cluster.su(db, sql)
    assert sorted((r[0], str(r[1]), r[2], r[3], r[4]) for r in got) == [
        ("bo_laksana", CANON, W, True, 2), ("ga_positions", CANON, W, True, 2)]     # ga_vargas' W row is the live key: not an orphan
    cluster.su(db, "DELETE FROM asset_freshness WHERE partition_key=%s AND asset_id IN ('ga_positions','bo_laksana')", (W,))
    cluster.su(db, "DELETE FROM asset_provenance_receipts WHERE partition_key=%s AND asset_id IN ('ga_positions','bo_laksana')", (W,))
    assert cluster.su(db, sql) == []                                                   # the standing check reads clean afterwards


def test_resolver_sql_matches_expected_verdicts_on_the_fixture(cluster, db, mod):
    got = {a: v for a, v, _ in cluster.su(db, mod.load_verdict_sql().replace("%(chart)s", "'%s'" % CANON))}
    assert got == {"ga_positions": "receipt_not_proven", "bo_laksana": "receipt_not_proven", "ga_vargas": "RESOLVED",
                   "ga_strength": "receipt_spec_retired", "ka_stale_like": "receipt_not_fresh"}


def test_lock_timeout_5s_a_blocked_table_fails_loudly_and_rolls_back(runner, cluster, db):
    """Another session holds a conflicting lock: the executor must not wait forever (lock_timeout 5s) and must change nothing."""
    before = cluster.image(db)
    with cluster.conn(db) as holder:
        holder.cursor().execute("LOCK TABLE public.asset_freshness IN ROW EXCLUSIVE MODE")     # what an in-flight builder write holds
        # lock_timeout and statement_timeout are both 5s (as specified), so whichever fires first ends the wait
        with pytest.raises((psycopg.errors.LockNotAvailable, psycopg.errors.QueryCanceled)):
            runner.run("apply")
        holder.rollback()
    assert_unchanged(cluster, db, before)
