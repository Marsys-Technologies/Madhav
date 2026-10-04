"""ITEM 5 (K1): the chart_vichara capture-trigger arguments gain `constituent_fact_ids` (nine arguments), ARGUMENTS ONLY, no function hunk, and only that
table's trigger-attestation row is re-attested. chart_vichara has NO natural key: the nine arguments are 'grain plus L1 source-fact provenance set', an
identity for capture, not a uniqueness rule. Disposable PostgreSQL only; the capture path is driven as role data_plane_builder (real generation, real guard and
capture triggers, real complete_l1_data_plane_partition)."""
from __future__ import annotations

import uuid

import psycopg
import pytest

import conftest as cf
import live_manifest as lm

ASSET, PART = "ga_vichara", "ayanamsha:lahiri_chitrapaksha"
OLD8 = ("chart_id", "ayanamsha_id", "vichara_family", "subject", "target", "domain", "varga_id", "formula_version")


@pytest.fixture()
def runner(cluster, mod, db, tmp_path):
    return cf.Runner(cluster, mod, db, tmp_path)


def trigger_args(cluster, db, table):
    d = cluster.su(db, "SELECT pg_get_triggerdef(t.oid,true) FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid WHERE c.relname=%s AND t.tgname='l1_data_plane_capture'", (table,))[0][0]
    return tuple(a.strip().strip("'") for a in d[d.index("l1_data_plane_capture_row(") + len("l1_data_plane_capture_row("):].rstrip(")").split(","))


def attestation(cluster, db, table):
    return cluster.su(db, "SELECT definition_digest FROM public.l1_data_plane_trigger_attestations WHERE table_name=%s AND trigger_name='l1_data_plane_capture'", (table,))[0][0]


def capture_vichara(cluster, db, rows, reported=None):
    """Open a generation for ga_vichara as data_plane_builder, INSERT the rows into chart_vichara (the capture trigger fires), complete the partition.
    Returns None when the completion passes, else the first line of the error."""
    chart = cf.CHART
    run = str(uuid.uuid4())
    cluster.su(db, "INSERT INTO build_runs(id,chart_id,state) VALUES (%s,%s,'running')", (run, chart))
    cluster.su(db, "INSERT INTO build_run_assets(run_id,asset_id,state) VALUES (%s,%s,'building')", (run, ASSET))
    conn = cluster.conn(db, user="data_plane_builder")
    err = None
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT set_config('madhav.l1_asset_id',%s,true), set_config('madhav.l1_chart_id',%s,true), set_config('madhav.l1_generation_id',%s,true), "
                        "set_config('madhav.l1_partition_key',%s,true), set_config('madhav.l1_contract_version','l1.data-plane.contract.1.0',true)", (ASSET, chart, run, PART))
            cur.execute("SELECT public.open_l1_data_plane_generation(%s::uuid,%s,%s,%s,1,NULL,'l1.data-plane.contract.1.0','l0.semantic.2026-09-13.1',"
                        "'665096a74a59ea7e0e50ce98fc685899b89f325aca0d91c214f0040e4d259dd1','l0-resource-config-g1',"
                        "'d516aecff9d4e05d929dc7fd71a113fd5c53d1f6ea1eb2582caafd3a339c279a')", (chart, ASSET, run, PART))
            for fam, subj, tgt, dom, varga, cfids in rows:
                cur.execute("INSERT INTO chart_vichara(chart_id, ayanamsha_id, build_id, vichara_family, subject, actor, target, domain, varga_id, value_num, "
                            "constituent_fact_ids, formula_version) VALUES (%s,'lahiri_chitrapaksha',%s,%s,%s,%s,%s,%s,%s,1,%s,'v1')",
                            (chart, run, fam, subj, subj, tgt, dom, varga, cfids))
            cur.execute("SELECT public.complete_l1_data_plane_partition(%s::uuid,%s,%s,%s,%s)", (chart, ASSET, run, PART, len(rows) if reported is None else reported))
        conn.commit()
    except psycopg.Error as exc:
        err = str(exc).splitlines()[0]
        conn.rollback()
    finally:
        conn.close()
        cluster.su(db, "DELETE FROM build_run_assets WHERE run_id=%s", (run,))
        cluster.su(db, "DELETE FROM build_runs WHERE id=%s", (run,))
    return err


# three rows that share the eight grain columns and differ ONLY in their sorted constituent_fact_ids (the 330 groups of the live data), whole-row distinct
SHARED = [("valence_pass", "SUN", "MOO", "career", "D1", ["f1"]), ("valence_pass", "SUN", "MOO", "career", "D1", ["f1", "f2"]),
          ("valence_pass", "SUN", "MOO", "career", "D1", ["f2", "f3"])]
WHOLE_ROW_DISTINCT_WITH_NULLS = SHARED + [("valence_pass", "VEN", None, None, None, ["f9"]), ("varga_ratification", "MAR", "SAT", "wealth", "D9", ["f4", "f5"])]


def test_replay_matches_the_live_chart_vichara_trigger(cluster, db):
    assert trigger_args(cluster, db, "chart_vichara") == OLD8
    assert attestation(cluster, db, "chart_vichara") == "aa242e3b291de7460d09cbaed833cdf179e8f4f896f1bb0a931028c4708367a8"    # read live as suvarna_reader, 2026-10-02


def test_the_data_ships_as_arguments_only_item_5_has_no_function_hunk(mod):
    c = {x.table: x for x in mod.TRIGGER_CHANGES}["chart_vichara"]
    assert c.to_args == c.from_args + ("constituent_fact_ids",) and not c.swap_index and c.added == ("constituent_fact_ids",)
    assert all("constituent_fact_ids" not in h[1] + h[2] for p in mod.FUNCTION_PATCHES for h in p.hunks)       # no function hunk mentions the new argument
    assert len(mod.FUNCTION_PATCHES) == 3 and "ITEM 5" in mod.render_plan() and "RESERVED" not in mod.render_plan()
    assert "NOT a natural key" in c.note


def test_before_the_apply_the_old_capture_collapses_rows_that_differ_only_in_provenance_and_the_completion_fails_closed(cluster, db):
    err = capture_vichara(cluster, db, SHARED)
    assert err and "reported 3 rows but protected capture contains 1" in err, err


def test_after_the_apply_the_nine_argument_capture_passes_for_whole_row_distinct_rows(runner, cluster, db):
    code, res = runner.run("apply")
    assert code == 0, res["details"]
    assert trigger_args(cluster, db, "chart_vichara") == OLD8 + ("constituent_fact_ids",)
    assert capture_vichara(cluster, db, SHARED) is None
    assert capture_vichara(cluster, db, WHOLE_ROW_DISTINCT_WITH_NULLS) is None


def test_the_owner_half_alone_still_fails_closed_on_an_exact_duplicate_the_writer_must_dedupe(runner, cluster, db):
    code, res = runner.run("apply")
    assert code == 0
    err = capture_vichara(cluster, db, SHARED + [SHARED[0]])                        # an exact duplicate: the writer half (whole-row dedupe) is a separate lane
    assert err and "reported 4 rows but protected capture contains 3" in err, err


def test_post_apply_trigger_args_are_the_target_and_only_vichara_is_reattested(runner, cluster, db, mod):
    pre_att = cluster.su(db, "SELECT table_name, trigger_name, definition_digest FROM public.l1_data_plane_trigger_attestations ORDER BY 1,2")
    code, res = runner.run("apply")
    assert code == 0, res["details"]
    c = {x.table: x for x in mod.TRIGGER_CHANGES}["chart_vichara"]
    assert trigger_args(cluster, db, "chart_vichara") == c.to_args and attestation(cluster, db, "chart_vichara") == c.to_digest
    post_att = cluster.su(db, "SELECT table_name, trigger_name, definition_digest FROM public.l1_data_plane_trigger_attestations ORDER BY 1,2")
    changed = {(a[0], a[1]) for a in post_att if a not in pre_att}
    assert changed == {("chart_vichara", "l1_data_plane_capture"), ("chart_divisionals", "l1_data_plane_capture")}      # nothing else, mutation guards included
    assert res["checks"]["post_vichara_identity_probe"] and res["checks"]["post_trigger_args_are_the_target_chart_vichara"]
    assert res["checks"]["post_changed_trigger_attestations_are_exactly_the_planned_tables"]


def test_a_chart_vichara_trigger_that_differs_from_the_bound_base_is_refused_and_nothing_changes(runner, cluster, db, mod):
    cluster.su(db, "DROP TRIGGER l1_data_plane_capture ON public.chart_vichara")
    cluster.su(db, "CREATE TRIGGER l1_data_plane_capture AFTER INSERT OR UPDATE ON public.chart_vichara FOR EACH ROW EXECUTE FUNCTION "
                   "public.l1_data_plane_capture_row('chart_id','ayanamsha_id','vichara_family','subject','target','domain','varga_id')")      # seven arguments: not the base
    pre = runner.state()
    code, res = runner.run("apply")
    assert code != 0 and "pre_trigger_shape_chart_vichara" in res["failed_checks"]
    assert runner.state() == pre


def test_the_dry_run_and_the_rollback_rehearsal_cover_the_chart_vichara_leg(runner, cluster, db, mod):
    pre = runner.state()
    pre_args, pre_att = trigger_args(cluster, db, "chart_vichara"), attestation(cluster, db, "chart_vichara")
    code, dry = runner.run("dry-run")
    assert code == 0 and runner.state() == pre and trigger_args(cluster, db, "chart_vichara") == pre_args
    assert "CHART_VICHARA IDENTITY PROBE: fixture rows 120; distinct identities live 9 args 120, legacy 8 args" in "\n".join(dry["log"])
    code, res = runner.run("apply")
    assert code == 0
    code, rd = runner.run("rollback-dry-run")
    assert code == 0 and trigger_args(cluster, db, "chart_vichara") == pre_args + ("constituent_fact_ids",)
    code, rb = runner.run("rollback")
    assert code == 0 and rb["status"] == "COMMITTED", rb["details"]
    assert trigger_args(cluster, db, "chart_vichara") == pre_args and attestation(cluster, db, "chart_vichara") == pre_att
    assert runner.state() == pre                                                    # every function md5, every attestation row, index, trigger, comment
    assert capture_vichara(cluster, db, SHARED) is not None                         # and the old shape collapses again


def test_a_probe_whose_fixture_collapses_under_the_nine_arguments_refuses_the_commit(runner, mod, monkeypatch):
    """The identity probe is a real commit condition: if the writer-shaped rows were NOT distinct under the live nine arguments (here: exact duplicates), the
    plan refuses and changes nothing."""
    pre = runner.state()
    _, dry = runner.execute(runner.args("dry-run"))
    monkeypatch.setattr(mod, "_vichara_fixture", lambda: [("00000000-0000-0000-0000-00000000f5f5", "a", "valence_pass", "S", "T", "d", "D1", "v1", ["x"])] * 6)
    code, res = runner.execute(runner.args("apply", expect_evidence=dry["evidence_digest"]))
    assert code == 1 and "post_vichara_identity_probe" in res["failed_checks"]
    assert runner.state() == pre
