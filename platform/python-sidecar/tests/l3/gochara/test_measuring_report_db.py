"""Measuring-build readers (read_records, read_measuring_view) on the stub chart's REAL applied schema.

The world is the A5.3 test world (1081 + 1152-1157 + 1206 + 1240, L1 tables stubbed): one booted generation with ONE
admitted P3 record (Saturn in Libra, Jan 10 - Feb 20 of the test year) and a window per windowed path. The expected values are
the seeded geometry, written by hand from `_boot_p3`, never read back from the readers.
"""
from __future__ import annotations

import json
import uuid
from datetime import date, datetime, timezone

import pytest

from services.gochara_kernel import measuring_report as mr

from .test_a53_inventory import CHART_ID, H0, H1
from .test_a53_p1_support import GEN, _t, world  # noqa: F401  (fresh AM-5 DB incl. 1240)
from .test_a53_window_verification_gate import _boot_p3, _windows



def _set_manifest(conn, vector: dict, *, status="candidate", horizon=(H0, H1)):
    """The booted world already holds the generation's ONE publication row (UNIQUE (chart_id, generation)); rewrite its vector,
    status and horizon as the superuser under replica role (the guards under test are not what is observed here)."""
    with conn.transaction():
        conn.execute("SET LOCAL session_replication_role = replica")
        n = conn.execute("UPDATE public.kala_gochara_publication SET input_generation_vector = %s::jsonb, status = %s, horizon = tstzrange(%s, %s)"
                         " WHERE chart_id = %s AND generation = %s", (json.dumps(vector), status, horizon[0], horizon[1], CHART_ID, GEN)).rowcount
    assert n == 1


def test_read_records_returns_the_stored_admitted_record_with_its_exact_support_and_never_defaults_the_tag(world):
    _boot_p3(world)
    recs = mr.read_records(world.conn, CHART_ID, GEN)
    assert recs == [mr.SupportRecord("marriage", "P3", "saturn", ((_t(1, 10), _t(2, 20)),), "base")]
    horizon = (date(2025, 1, 1), date(2025, 3, 1))                                  # the test world's two months: 59 days
    rep = mr.class_share_report(recs, [], horizon)["classes"]["marriage"]
    assert mr.horizon_days(horizon) == 59
    # Jan 10 .. Feb 20 (exclusive, midnight end): 22 January days (10..31) + 19 February days (1..19) = 41
    assert rep["admitted_days"]["P3_slow"] == rep["admitted_days"]["P3_union"] == rep["admitted_days"]["class_union"] == 41
    assert rep["admitted_days"]["P3_fast"] == 0 and rep["admitted_share"]["P3_union"] == 41 / 59


def test_read_records_refuses_a_stored_rule_version_that_is_not_bound_today(world):
    _boot_p3(world)
    with world.conn.transaction():
        world.conn.execute("SET LOCAL session_replication_role = replica")
        world.conn.execute("UPDATE public.ka_gochara_relationship_record SET rule_version = '1.2.0' WHERE chart_id = %s AND generation = %s", (CHART_ID, GEN))
    with pytest.raises(mr.MeasuringReportError, match="rule_version_not_in_scope"):
        mr.read_records(world.conn, CHART_ID, GEN)


def test_the_view_reads_a_candidate_manifest_the_marker_the_classes_with_rows_and_the_bound_versions(world):
    _boot_p3(world)
    vector = {"stored_scope": "test_slice",
              "test_slice": {"schema": "gochara_v5_test_slice/1", "marker_digest": "d" * 64, "run": "all_classes_full",
                             "classes": sorted(mr.SCORED_CLASSES), "horizon": ["2025-01-01", "2025-03-01"]}}
    _set_manifest(world.conn, vector)
    v = mr.read_measuring_view(world.conn, CHART_ID, GEN)
    assert (v.stored_scope, v.run, v.sealed, v.published) == ("test_slice", "all_classes_full", False, False)
    assert v.horizon == (H0, H1) and v.marker_horizon == ("2025-01-01", "2025-03-01")
    assert v.rule_versions == frozenset({"1.0.0"}) and v.classes_with_records == frozenset({"marriage"})
    assert v.near_miss_rows_stored is None and v.marker_classes == mr.SCORED_CLASSES and v.status == "candidate"        # the store is absent: unknown
    # the stored tstzrange form (tz-aware instants) is accepted without a TypeError and agrees with the date form
    assert mr.measuring_refusals(v, expected_horizon=(date(2025, 1, 1), date(2025, 3, 1))) == [], \
        mr.measuring_refusals(v, expected_horizon=(date(2025, 1, 1), date(2025, 3, 1)))
    # and a different derived horizon is a named mismatch on the same stored form
    assert any(x.startswith("horizon_mismatch") for x in mr.measuring_refusals(v, expected_horizon=(date(2025, 1, 2), date(2025, 3, 1))))


def test_a_published_manifest_and_a_missing_one_are_each_named(world):
    _boot_p3(world)
    _set_manifest(world.conn, {"stored_scope": "test_slice", "test_slice": {"run": "all_classes_full", "classes": [], "horizon": []}}, status="published")
    v = mr.read_measuring_view(world.conn, CHART_ID, GEN)
    assert v.published is True and "measuring_build_published" in mr.measuring_refusals(v, expected_horizon=(date(2025, 1, 1), date(2025, 3, 1)))
    with world.conn.transaction():
        world.conn.execute("SET LOCAL session_replication_role = replica")
        world.conn.execute("DELETE FROM public.kala_gochara_publication WHERE chart_id = %s AND generation = %s", (CHART_ID, GEN))
    with pytest.raises(mr.MeasuringReportError, match="measuring_manifest_missing"):
        mr.read_measuring_view(world.conn, CHART_ID, GEN)


def test_a_vector_without_a_marker_reads_as_no_scope_and_no_run_and_is_refused_not_crashed(world):
    _boot_p3(world)
    _set_manifest(world.conn, {"stored_scope": "stored_non_moon"})
    v = mr.read_measuring_view(world.conn, CHART_ID, GEN)
    assert v.run is None and v.marker_classes == frozenset() and v.marker_horizon is None
    out = mr.measuring_refusals(v, expected_horizon=(date(2025, 1, 1), date(2025, 3, 1)))
    assert any(x.startswith("measuring_scope_not_test_slice") for x in out) and any(x.startswith("measuring_run_not_all_classes_full") for x in out)


def test_a_sealed_generation_is_read_as_sealed_and_refused(world):
    _boot_p3(world)
    _set_manifest(world.conn, {"stored_scope": "test_slice", "test_slice": {"schema": "gochara_v5_test_slice/1", "marker_digest": "d" * 64, "run": "all_classes_full",
                                                                         "classes": sorted(mr.SCORED_CLASSES), "horizon": ["2025-01-01", "2025-03-01"]}})
    assert mr.read_measuring_view(world.conn, CHART_ID, GEN).sealed is False
    with world.conn.transaction():
        world.conn.execute("SET LOCAL session_replication_role = replica")                 # the seal guards are not what is observed here
        world.conn.execute("INSERT INTO public.ka_gochara_generation_seal (chart_id, generation, manifest_id)"
                           " SELECT chart_id, generation, manifest_id FROM public.kala_gochara_publication WHERE chart_id = %s AND generation = %s",
                           (CHART_ID, GEN))
    v = mr.read_measuring_view(world.conn, CHART_ID, GEN)
    assert v.sealed is True and "measuring_build_sealed" in mr.measuring_refusals(v, expected_horizon=(date(2025, 1, 1), date(2025, 3, 1)))


def test_a_superseded_generation_is_named_not_passed_unnoticed(world):
    _boot_p3(world)
    _set_manifest(world.conn, {"stored_scope": "test_slice", "test_slice": {"schema": "gochara_v5_test_slice/1", "marker_digest": "d" * 64, "run": "all_classes_full",
                                                                         "classes": sorted(mr.SCORED_CLASSES), "horizon": ["2025-01-01", "2025-03-01"]}}, status="superseded")
    v = mr.read_measuring_view(world.conn, CHART_ID, GEN)
    assert v.status == "superseded" and any(x.startswith("measuring_status_not_candidate") for x in mr.measuring_refusals(v, expected_horizon=(date(2025, 1, 1), date(2025, 3, 1))))


def test_an_admitted_testimony_record_is_not_read_into_a_scored_share(world):
    _boot_p3(world)
    assert len(mr.read_records(world.conn, CHART_ID, GEN)) == 1
    with world.conn.transaction():
        world.conn.execute("SET LOCAL session_replication_role = replica")                 # the role/provenance guards are not what is observed here
        n = world.conn.execute("UPDATE public.ka_gochara_relationship_record SET operator_role = 'testimony' WHERE chart_id = %s AND generation = %s"
                               " AND admission_state = 'admitted'", (CHART_ID, GEN)).rowcount
    assert n == 1
    assert mr.read_records(world.conn, CHART_ID, GEN) == []                                # an admitted TESTIMONY record changes no admission: never a scored share


def test_the_view_reports_the_paths_that_hold_rows(world):
    _boot_p3(world)
    _set_manifest(world.conn, {"stored_scope": "test_slice", "test_slice": {"schema": "gochara_v5_test_slice/1", "marker_digest": "d" * 64,
                                                                         "run": "all_classes_full", "classes": sorted(mr.SCORED_CLASSES),
                                                                         "horizon": ["2025-01-01", "2025-03-01"]}})
    v = mr.read_measuring_view(world.conn, CHART_ID, GEN)
    assert ("marriage", "P3") in v.class_paths_with_rows and v.classes_with_records == frozenset({"marriage"})


def test_mb6_real_run_producer_basis_survives_manifest_storage_and_rejects_wrong_bounds(world):
    """Actual producer reads a local run; MB-6 reads its stored JSON, with no LEL table.

    The independent runtime/sink envelope is synthetic, as in the pure MB-6
    tests: this proves compatibility, not a real measuring operation's verdict.
    """
    from pipeline.orchestrator.writers import ContextSpec
    from pipeline.orchestrator.writers import ka_gochara_v5 as writer
    from .test_mb_horizon_shape_guard import BIRTH_PARAMS
    from .test_measuring_report import BIRTH, BUILD, H, T, _mb6_view

    _boot_p3(world)
    run_id = str(uuid.uuid4())
    # The AM-5 world predates these two reader inputs; stub only their read
    # columns, as the J-1a fixture does. All publication storage is real DDL.
    world.conn.execute("CREATE TABLE public.build_runs (id uuid PRIMARY KEY, created_at timestamptz NOT NULL)")
    world.conn.execute("CREATE TABLE public.kala_gochara_authority (chart_id uuid PRIMARY KEY, authoritative_generation text)")
    world.conn.execute("INSERT INTO public.build_runs VALUES (%s, %s)", (run_id, T(2026, 10, 5)))
    ctx = ContextSpec(asset_id=writer.ASSET_ID, build_id=run_id, db_conn=world.conn,
                      config={"chart_id": CHART_ID, "birth_params": BIRTH_PARAMS}, dry_run=False)
    basis = writer._derive_horizon(ctx).basis_record()
    vector = {"stored_scope": "test_slice", "horizon_basis": basis,
              "test_slice": {"schema": "gochara_v5_test_slice/1", "marker_digest": "d" * 64,
                             "run": "all_classes_full", "classes": sorted(mr.SCORED_CLASSES),
                             "horizon": ["1998-01-01", "2084-02-05"]}}
    evidence = _mb6_view()

    def accept():
        return mr.read_measuring_acceptance(
            world.conn, CHART_ID, GEN, expected_horizon=H, birth_date=BIRTH, build_date=BUILD,
            run_verdict=evidence.run_verdict, sink_counts=evidence.sink_counts)

    _set_manifest(world.conn, vector, horizon=(T(1998, 1, 1), T(2084, 2, 5)))
    result = accept()
    assert result["accepted"] is True, result["refusals"]
    basis["horizon"][0] = "1999-01-01T00:00:00+00:00"
    _set_manifest(world.conn, vector, horizon=(T(1998, 1, 1), T(2084, 2, 5)))
    result = accept()
    assert result["accepted"] is False and "horizon_mismatch" in result["refusals"]
