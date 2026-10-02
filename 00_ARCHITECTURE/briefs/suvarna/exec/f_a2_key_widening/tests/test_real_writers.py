"""The REAL writers of this branch through the REAL capture and completion path, on the combined plan's end state.

ga_vargas (F-A2 writer: seven-column ON CONFLICT target) is run for all five ayanamshas as data_plane_builder: every row passes the real
guard and capture trigger and every partition passes the real complete_l1_data_plane_partition (reported rows == distinct captured
identities: the check the unwidened trigger would abort). ga_structural runs its first ayanamsha sub-step on the function toggled between the
LIVE body and the patched body (the trigger arguments stay widened), to show patch A on real producer rows. The upstream ga_positions /
ga_strength / ga_panchanga / ga_sensitive facts are fixtures (superuser, triggers off). ga_nakshatra needs reference tables the replay does
not model and is reported NOT LOADED; ga_structural reads whatever upstream exists and floors the rest (the writer's own B.10 behaviour).

Skipped without Swiss Ephemeris files (SE_EPHE_PATH, default /tmp/se1)."""
from __future__ import annotations

import pathlib
import subprocess

import pytest

import conftest as cf
import real_writers as rw

pytestmark = pytest.mark.skipif(not rw.ephemeris_available(), reason="Swiss Ephemeris files not found (SE_EPHE_PATH)")


@pytest.fixture()
def runner(cluster, mod, db, tmp_path):
    return cf.Runner(cluster, mod, db, tmp_path)


def run_substeps(cluster, db, asset, only=None):
    import ga_writers.ga_vargas_writer as gvw
    gvw._SHASHTIAMSHA_CACHE = None            # the writer caches the deity reference per process (a failed read caches {}): reset per run
    run = rw.new_run(cluster, db, asset)
    conn = rw.connect(cluster, db)
    try:
        out = rw.drive(rw.load_writer(asset), rw.context(cluster, db, asset, run, conn), only=only)
        conn.close()
        rw.finish_run(cluster, db, run, asset)
        return run, out, None
    except Exception as exc:
        conn.rollback()
        conn.close()
        rw.fail_run(cluster, db, run, asset)
        return run, None, exc


def test_the_new_ga_vargas_writer_fails_closed_on_the_six_column_index_and_writes_nothing(runner, cluster, db):
    cluster.su(db, "GRANT SELECT ON public.bg_shashtiamsha_deities TO data_plane_builder")
    rw.load_upstream(cluster, db, ("ga_positions",))
    run, out, exc = run_substeps(cluster, db, "ga_vargas", {"lahiri_chitrapaksha"})
    assert out is None and "F-A2" in str(exc) and "chart_divisionals_unique_idx" in str(exc)
    assert cluster.su(db, "SELECT count(*) FROM chart_divisionals")[0][0] == 0


def test_FINDING_the_builder_cannot_read_bg_shashtiamsha_deities_so_the_ga_vargas_build_aborts(runner, cluster, db, mod):
    """FINDING (not caused by this plan; reproduced on the replay with production's ACL as read live 2026-10-02): data_plane_builder has NO
    SELECT on public.bg_shashtiamsha_deities, which the ga_vargas writer reads inside the build transaction. The writer catches the error and
    floors, but the failed statement has already aborted the transaction (InFailedSqlTransaction on the next statement). Whatever role runs the
    S-L1 ga_vargas build needs that table readable (ordinary migration by the table's owner amjis_app)."""
    assert runner.run("apply")[0] == 0                          # (the apply needs migration 1255 live: modelled by the db fixture)
    cluster.su(db, "REVOKE SELECT ON public.bg_shashtiamsha_deities FROM data_plane_builder")        # production TODAY: no 1255, builder cannot read the table
    assert cluster.su(db, "SELECT has_table_privilege('data_plane_builder','public.bg_shashtiamsha_deities','SELECT')")[0][0] is False
    rw.load_upstream(cluster, db, ("ga_positions",))
    run, out, exc = run_substeps(cluster, db, "ga_vargas", {"lahiri_chitrapaksha"})
    assert out is None and type(exc).__name__ == "InFailedSqlTransaction", exc


def test_ga_vargas_all_five_ayanamshas_pass_capture_and_completion_and_the_f_a2_acceptance_check(runner, cluster, db, mod):
    cluster.su(db, "GRANT SELECT ON public.bg_shashtiamsha_deities TO data_plane_builder")        # see the FINDING test
    assert runner.run("apply")[0] == 0
    rw.load_upstream(cluster, db, ("ga_positions",))
    run, out, exc = run_substeps(cluster, db, "ga_vargas")
    assert exc is None, exc
    assert sorted(out) == ["krishnamurti", "lahiri_chitrapaksha", "raman", "surya_siddhanta_classical", "true_chitra"]
    assert set(out.values()) == {7724} and sum(out.values()) == 38620            # attempted == landed per partition (6 sentinels re-inserted per call)
    assert cluster.su(db, "SELECT count(*) FROM chart_divisionals")[0][0] == 38596
    # every partition completed through the real completion function, and the generation is complete
    assert cluster.su(db, "SELECT status FROM l1_data_plane_generations WHERE generation_id=%s AND asset_id='ga_vargas'", (run,)) == [("complete",)]
    # capture identity == stored rows (the arithmetic the unwidened trigger would break): distinct identities of the final table rows
    assert cluster.su(db, "SELECT count(DISTINCT row_identity) FROM l1_data_plane_row_snapshots WHERE source_table='chart_divisionals' "
                          "AND generation_id=%s", (run,))[0][0] >= 38596
    six = cluster.su(db, "SELECT count(*) FROM (SELECT DISTINCT chart_id, graha, ayanamsha_id, varga, fact_category, fact_key FROM chart_divisionals) x")[0][0]
    assert six < 38596, "the legacy six-argument identity would have collapsed rows: the abort the plan prevents"
    # the F-A2 acceptance check (read-only SELECT) with the canonical chart literal replaced by the synthetic chart
    sql = (cf.EXEC_DIR / "s_l1_ga_vargas_acceptance_check.sql").read_text().replace("482012f1-710e-4a25-994a-93821f5871aa", cf.CHART)
    f = pathlib.Path(cluster.sockdir) / "acceptance.sql"
    f.write_text(sql)
    r = subprocess.run([cf.PSQL, "-X", "-A", "-t", "-F", "|", "-h", "127.0.0.1", "-p", str(cluster.port), "-U", "rehearsal_reader", "-d", db,
                        "-f", str(f)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    rows = [ln.split("|") for ln in r.stdout.splitlines() if ln.strip()]
    statuses = {ln[0]: ln[-1] for ln in rows if ln[-1] in ("PASS", "FAIL")}
    assert statuses and all(v == "PASS" for v in statuses.values()), rows
    assert any(ln[1].startswith("ACCEPTED") and ln[-1] == "PASS" for ln in rows), rows


def test_ga_structural_on_real_rows_fails_on_the_live_body_and_passes_on_the_patched_body(runner, cluster, db, mod):
    cluster.su(db, "GRANT SELECT ON public.bg_shashtiamsha_deities TO data_plane_builder")
    assert runner.run("apply")[0] == 0
    up = rw.load_upstream(cluster, db, ("ga_positions", "ga_vargas", "ga_strength", "ga_panchanga", "ga_sensitive"))
    assert up["ga_positions"] == 1205
    import ga_writers.ga_structural_writer as gsw
    rw.shim_ascendant_longitude(gsw)
    sub = {"ayanamsha_lahiri_chitrapaksha"}
    # live body (patch A absent; the trigger arguments stay widened): the real producer rows abort the capture
    cluster.su(db, mod.CAPTURE_PATCH.live_def())
    run, out, exc = run_substeps(cluster, db, "ga_structural", sub)
    assert out is None and type(exc).__name__ == "CheckViolation" and "l1_data_plane_fact_snapshots_check" in str(exc), exc
    # patched body: capture and completion pass on the same rows
    cluster.su(db, mod.CAPTURE_PATCH.patched_def())
    run, out, exc = run_substeps(cluster, db, "ga_structural", sub)
    assert exc is None, exc
    assert out["ayanamsha_lahiri_chitrapaksha"] > 0
    marked = cluster.su(db, "SELECT count(*) FROM l1_data_plane_fact_snapshots WHERE generation_id=%s AND grain_jsonb ? 'typed_value_column'", (run,))[0][0]
    assert marked > 0, "real ga_structural rows carry more than one typed value: the companion marker must appear"
    unmarked_multi = cluster.su(db, """SELECT count(*) FROM l1_data_plane_fact_snapshots fs JOIN l1_data_plane_row_snapshots rs ON rs.snapshot_id=fs.row_snapshot_id
        WHERE fs.generation_id=%s AND num_nonnulls(fs.value_num, fs.value_text, fs.value_jsonb) <> 1 AND fs.missingness_state IN ('present','zero')""", (run,))[0][0]
    assert unmarked_multi == 0
    # every marked row keeps the complete producer row in the row snapshot
    lost = cluster.su(db, """SELECT count(*) FROM l1_data_plane_fact_snapshots fs JOIN l1_data_plane_row_snapshots rs ON rs.snapshot_id=fs.row_snapshot_id
        WHERE fs.generation_id=%s AND fs.grain_jsonb ? 'typed_value_column' AND jsonb_array_length(fs.grain_jsonb->'companion_value_columns') > 0
          AND NOT EXISTS (SELECT 1 FROM jsonb_array_elements_text(fs.grain_jsonb->'companion_value_columns') c(col)
                          WHERE rs.source_row_jsonb ? c.col AND rs.source_row_jsonb->c.col IS NOT NULL AND rs.source_row_jsonb->>c.col <> 'null')""", (run,))[0][0]
    assert lost == 0
