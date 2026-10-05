"""C48a / G1 (REBUILD_AND_UPSTREAM_SEQUENCING_v1_0): a sealed generation must be
re-checkable against upstream drift. `staleness.sealed_generation_staleness` recomputes
the snapshot's digests from the LIVE L1/daśā rows with the database's own digest
functions and reports per-component drift, sealed or not.

Runs on the same throwaway database as the A5.3 store tests (real 1206 chain, L1
tables stubbed): the drift cases mutate the stubbed upstream rows exactly the way a
production rebuild would.
"""
from __future__ import annotations

import pytest

from services.gochara_kernel import staleness

from .test_a53_inventory import (CHART_ID, DASHA, DASHA_IDS, PINNED_BUILD, _boot, _plan,
                                 _write, create_am5_database, drop_am5_database)


@pytest.fixture(scope="module")
def _dsn():
    admin, name, dsn = create_am5_database("c48a")
    try:
        yield dsn
    finally:
        drop_am5_database(admin, name)


@pytest.fixture()
def conn(_dsn):
    import psycopg
    c = psycopg.connect(_dsn, autocommit=True, connect_timeout=3)
    yield c
    c.close()


def _fresh(conn, generation):
    store, sky, _kala = _boot(conn, generation)
    _write(conn, store, sky, generation, _plan())
    return store


def _seal(conn, generation):
    """Mark the generation sealed. What is under test is the staleness READ, not the
    seal path, so (precedent: test_a53_builder_restricted_flow / perf_a53_seal_cost) the
    row is inserted with the seal table's guards disabled — sealing properly would need
    the whole coverage-partition + verification chain this fixture does not build."""
    with conn.transaction():
        manifest = conn.execute(
            "SELECT manifest_id FROM public.kala_gochara_publication"
            " WHERE chart_id = %s AND generation = %s", (CHART_ID, generation)).fetchone()[0]
        conn.execute("ALTER TABLE public.ka_gochara_generation_seal DISABLE TRIGGER USER")
        conn.execute(
            "INSERT INTO public.ka_gochara_generation_seal (chart_id, generation, manifest_id)"
            " VALUES (%s, %s, %s)", (CHART_ID, generation, manifest))
        conn.execute("ALTER TABLE public.ka_gochara_generation_seal ENABLE TRIGGER USER")


def test_a_fresh_candidate_reports_no_drift_and_not_sealed(conn):
    _fresh(conn, "5.20")
    out = staleness.sealed_generation_staleness(conn, CHART_ID, "5.20")
    assert out["sealed"] is False
    assert out["drifted"] is False and out["drifted_components"] == []
    assert all(c["same"] for c in out["components"].values())


def test_a_sealed_generation_with_untouched_inputs_reports_no_drift(conn):
    _fresh(conn, "5.21")
    _seal(conn, "5.21")
    out = staleness.sealed_generation_staleness(conn, CHART_ID, "5.21")
    assert out["sealed"] is True and out["drifted"] is False


def test_a_changed_l1_fact_is_named_drift_even_under_a_seal(conn):
    """G1's exact case: the generation is sealed, then an upstream L1 row changes."""
    _fresh(conn, "5.22")
    _seal(conn, "5.22")
    with conn.transaction():
        conn.execute("UPDATE public.chart_facts SET fact_value_num = fact_value_num + 1"
                     " WHERE fact_id = 'fact-SUN' AND chart_id = %s", (CHART_ID,))
    out = staleness.sealed_generation_staleness(conn, CHART_ID, "5.22")
    assert out["sealed"] is True
    assert out["components"]["l1_facts"]["same"] is False
    assert out["components"]["dasha"]["same"] is True
    assert out["components"]["input"]["same"] is False
    assert out["drifted_components"] == ["input", "l1_facts"]
    with conn.transaction():
        conn.execute("UPDATE public.chart_facts SET fact_value_num = fact_value_num - 1"
                     " WHERE fact_id = 'fact-SUN' AND chart_id = %s", (CHART_ID,))


def test_a_deleted_dasha_row_is_drift_by_the_missing_rule(conn):
    _fresh(conn, "5.23")
    with conn.transaction():
        conn.execute("DELETE FROM public.chart_dashas WHERE dasha_row_id = %s::uuid",
                     (DASHA_IDS[0],))
    out = staleness.sealed_generation_staleness(conn, CHART_ID, "5.23")
    assert out["drifted_components"] == ["dasha", "input"]
    with conn.transaction():
        row = DASHA[0]
        conn.execute("INSERT INTO public.chart_dashas(dasha_row_id, chart_id, ayanamsha_id,"
                     " system_id, level_n, parent_row_id, lord_graha, start_iso, end_iso,"
                     " build_id, verification_pass_status)"
                     " VALUES (%s::uuid, %s, 'lahiri_chitrapaksha', 'vimshottari', %s, NULL,"
                     " %s, %s, %s, %s, 'two_pass_verified')",
                     (row.row_id, CHART_ID, row.level, row.lord.title(), row.start, row.end,
                      PINNED_BUILD))
    assert staleness.sealed_generation_staleness(conn, CHART_ID, "5.23")["drifted"] is False


def test_drift_is_reported_for_a_candidate_too(conn):
    """The check is not seal-gated: a candidate whose inputs drifted is named as well."""
    _fresh(conn, "5.24")
    with conn.transaction():
        conn.execute("UPDATE public.chart_facts SET fact_key = 'longitude_tropical'"
                     " WHERE fact_id = 'fact-MOON' AND chart_id = %s", (CHART_ID,))
    out = staleness.sealed_generation_staleness(conn, CHART_ID, "5.24")
    assert out["sealed"] is False and out["drifted"] is True
    with conn.transaction():
        conn.execute("UPDATE public.chart_facts SET fact_key = 'longitude_sidereal'"
                     " WHERE fact_id = 'fact-MOON' AND chart_id = %s", (CHART_ID,))


def test_a_generation_without_a_snapshot_is_a_named_refusal(conn):
    with pytest.raises(staleness.SnapshotMissingError):
        staleness.sealed_generation_staleness(conn, CHART_ID, "5.99")
