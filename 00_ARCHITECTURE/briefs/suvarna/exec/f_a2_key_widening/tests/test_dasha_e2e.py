"""Items 2 and 3 (patches B and C) against a DATABASE, through the real capture path as role data_plane_builder: real open_l1_data_plane_generation, guard and
capture triggers, real complete_l1_data_plane_partition. Shapes follow the independent reviewer's end-to-end proof (review-D6).

FIXTURE NOTE: the production catalog has no fact_category_ownership row for `dasha_scope_cap` (migration 1219's seed, not yet applied), so the post-pass
replay would fail at the EXISTING ownership guard before AND after D6. The disposable databases model 1219's row (owner ga_dashas) so that B and C themselves
are what these tests measure; the seed is an external prerequisite of the S-L1 rebuild, not of the D6 apply (plan section 10)."""
from __future__ import annotations

import datetime as dt
import hashlib
import uuid

import psycopg
import psycopg.types.json as pj
import pytest

import conftest as cf

ASSET, AYA = "ga_dashas", "lahiri_chitrapaksha"
POST_PASS = "__concurrency_post_pass__"
CTR = "l1.data-plane.contract.1.0"
OPEN = ("SELECT public.open_l1_data_plane_generation(%s::uuid,%s,%s,%s,%s,NULL,'l1.data-plane.contract.1.0','l0.semantic.2026-09-13.1',"
        "'665096a74a59ea7e0e50ce98fc685899b89f325aca0d91c214f0040e4d259dd1','l0-resource-config-g1',"
        "'d516aecff9d4e05d929dc7fd71a113fd5c53d1f6ea1eb2582caafd3a339c279a')")
DCOLS = ("dasha_row_id,chart_id,ayanamsha_id,build_id,system_id,level_n,lord_graha,start_date,end_date,start_iso,end_iso,duration_days,"
         "verification_pass_status,verification_method,citation_ref,citation_human,engine_version")


@pytest.fixture()
def runner(cluster, mod, db, tmp_path):
    cluster.su(db, "INSERT INTO public.fact_category_ownership(fact_category, owning_asset_id) VALUES ('dasha_scope_cap', 'ga_dashas') ON CONFLICT DO NOTHING")
    return cf.Runner(cluster, mod, db, tmp_path)


def dasha_row(run, system, aya, level, idx, lord="SUN"):
    d0 = dt.date(2000, 1, 1) + dt.timedelta(days=idx)
    d1 = d0 + dt.timedelta(days=1)
    return (str(uuid.uuid5(uuid.NAMESPACE_URL, f"{run}{system}{aya}{idx}")), cf.CHART, aya, run, system, level, lord, d0.isoformat(), d1.isoformat(),
            d0.isoformat() + "T00:00:00+00:00", d1.isoformat() + "T00:00:00+00:00", 1, "two_pass_verified", "m", "ref", "human", "v1")


def ins(cur, rows):
    for r in rows:
        cur.execute(f"INSERT INTO chart_dashas({DCOLS}) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", r)


def sentinel(cur, run):
    cur.execute("INSERT INTO chart_facts(fact_id,chart_id,ayanamsha_id,build_id,fact_category,fact_subject,fact_key,fact_value_jsonb,unit,citation_ref,citation_human,"
                "source_calculation,verification_pass_status,engine_version,computed_at) VALUES (%s,%s,'INVARIANT',%s,'dasha_scope_cap','PRANA_DASHA','level_5_not_computed',"
                "%s,'scope_declaration','R','h','c','single','v1',now())",
                (hashlib.sha256(run.encode()).hexdigest()[:16], cf.CHART, run, pj.Jsonb({"state": "method_inapplicable", "reason": "r"})))


def generation(cluster, db, parts):
    """One ga_dashas generation, one connection and one commit per partition (like the runtime). parts = [(partition_key, body(cur, run) -> reported)].
    Returns ([PASS/FAIL line per partition], (status, completed, expected))."""
    run = str(uuid.uuid4())
    cluster.su(db, "INSERT INTO build_runs(id,chart_id,state) VALUES (%s,%s,'running')", (run, cf.CHART))
    cluster.su(db, "INSERT INTO build_run_assets(run_id,asset_id,state) VALUES (%s,%s,'building')", (run, ASSET))
    lines = []
    try:
        for part, body in parts:
            conn = cluster.conn(db, user="data_plane_builder")
            try:
                cur = conn.cursor()
                cur.execute("SELECT set_config('madhav.l1_asset_id',%s,true), set_config('madhav.l1_chart_id',%s,true), set_config('madhav.l1_generation_id',%s,true), "
                            "set_config('madhav.l1_partition_key',%s,true), set_config('madhav.l1_contract_version',%s,true)", (ASSET, cf.CHART, run, part, CTR))
                cur.execute(OPEN, (cf.CHART, ASSET, run, part, len(parts)))
                reported = body(cur, run)
                cur.execute("SELECT public.complete_l1_data_plane_partition(%s::uuid,%s,%s,%s,%s)", (cf.CHART, ASSET, run, part, reported))
                conn.commit()
                lines.append(f"{part.split(':')[0]}: PASS")
            except psycopg.Error as exc:
                conn.rollback()
                lines.append(f"{part.split(':')[0]}: " + str(exc).splitlines()[0])
                break
            finally:
                conn.close()
        final = cluster.su(db, "SELECT status, completed_partitions, expected_partitions FROM l1_data_plane_generations WHERE generation_id=%s", (run,))
        return lines, (final[0] if final else None)
    finally:
        cluster.su(db, "DELETE FROM build_run_assets WHERE run_id=%s", (run,))
        cluster.su(db, "DELETE FROM build_runs WHERE id=%s", (run,))


def vimshottari(n_vim=10, n_kp=5):
    def body(cur, run):                                 # 10 vimshottari rows and 5 vimshottari_kp rows the same substep has always written
        ins(cur, [dasha_row(run, "vimshottari", AYA, 1, i) for i in range(n_vim)] + [dasha_row(run, "vimshottari_kp", AYA, 4, 100 + i) for i in range(n_kp)])
        return n_vim + n_kp
    return (f"vimshottari:{AYA}", body)


def yogini():
    def body(cur, run):
        ins(cur, [dasha_row(run, "yogini", AYA, 1, 200 + i) for i in range(6)])
        return 6
    return (f"yogini:{AYA}", body)


def post_pass():
    def body(cur, run):                                 # the real post-pass: a concurrency UPDATE + the scope-cap sentinels (one chart_dashas row, one chart_facts row)
        cur.execute("UPDATE chart_dashas SET convergence_count_at_start=2 WHERE chart_id=%s AND build_id=%s AND system_id='yogini'", (cf.CHART, run))
        ins(cur, [dasha_row(run, "scope_cap", "INVARIANT", 4, 900, "KP_LEVELS_BEYOND_SUB_SUB")])
        sentinel(cur, run)
        return 2
    return (POST_PASS, body)


# ------------------------------------------------------------------------------------------------------------------------------ item 2: patch B
def test_B_before_the_plan_a_vimshottari_partition_with_kp_rows_fails_closed(runner, cluster, db):
    lines, final = generation(cluster, db, [vimshottari(), yogini(), post_pass()])
    assert len(lines) == 1 and "dasha partition vimshottari:lahiri_chitrapaksha reported 15 rows but active build scope has 10" in lines[0], lines


def test_B_after_the_plan_the_partition_passes_and_a_three_partition_generation_reaches_complete(runner, cluster, db):
    code, res = runner.run("apply")
    assert code == 0, res["details"]
    lines, final = generation(cluster, db, [vimshottari(), yogini(), post_pass()])
    assert lines == ["vimshottari: PASS", "yogini: PASS", "__concurrency_post_pass__: PASS"], lines
    assert final == ("complete", 3, 3), final
    # the kp rows are in the protected history, inside the vimshottari partition
    kp = cluster.su(db, "SELECT count(*) FROM public.l1_data_plane_dasha_snapshots WHERE partition_key=%s AND (source_row).system_id='vimshottari_kp'", (f"vimshottari:{AYA}",))[0][0]
    assert kp == 5


# ------------------------------------------------------------------------------------------------------------------------------ item 3: patch C
def test_C_before_the_plan_a_post_pass_with_a_dasha_scope_cap_row_fails_closed(runner, cluster, db):
    lines, final = generation(cluster, db, [yogini(), post_pass()])
    assert len(lines) == 2 and lines[0] == "yogini: PASS" and "reported 2 rows but protected capture contains 1" in lines[1], lines


def test_C_after_the_plan_the_post_pass_passes(runner, cluster, db):
    code, res = runner.run("apply")
    assert code == 0, res["details"]
    lines, final = generation(cluster, db, [yogini(), post_pass()])
    assert lines == ["yogini: PASS", "__concurrency_post_pass__: PASS"] and final == ("complete", 2, 2), (lines, final)


def test_after_the_rollback_both_shapes_fail_closed_again(runner, cluster, db):
    assert runner.run("apply")[0] == 0
    code, rb = runner.run("rollback")
    assert code == 0, rb["details"]
    lines, _ = generation(cluster, db, [vimshottari()])
    assert "reported 15 rows but active build scope has 10" in lines[0]
    lines, _ = generation(cluster, db, [yogini(), post_pass()])
    assert "reported 2 rows but protected capture contains 1" in lines[1]
