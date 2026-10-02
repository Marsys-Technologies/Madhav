"""C19 (steward M20261002T062943-356e) — the ka_moorti_nirnaya and
ka_vedha_gochara overlay writers' delete-then-insert and the ka_gochara
writer's build-state upsert, exercised AS the production builder role.

C18's report-only gap list found production carries
data_plane_builder=arwd/amjis_app on public.kala_gochara_v2_build_state,
public.kala_moorti_nirnaya and public.kala_vedha_gochara (+ USAGE/SELECT on
the two BIGSERIAL sequences) with no migration recording it; migration 1239
(this task) records those ACLs. This suite proves the recorded ACL is
sufficient for each writer's own write statement, driven AS an AUTHENTICATED
data_plane_builder connection with one minimal literal row per table:

  * services/ka_moorti_nirnaya/writer.py's exact _DELETE_SQL + _INSERT_SQL;
  * services/ka_vedha_gochara/writer.py's exact _DELETE_SQL + _INSERT_SQL;
  * ka_gochara's exact build_state upsert (pipeline/orchestrator/writers/
    ka_gochara.py _record_build_state, invoked directly — its SQL layer,
    never re-typed, §N.8).

The writers themselves cannot be driven without an ephemeris run (their
transit series need the Swiss corpus), so — as in C15/C18 — their SQL layer
is driven directly.

SCHEMA: the C7 suite's grant-target schema builder (reused verbatim — it
builds kala_gochara_v2_build_state from the real 541 file and the two overlay
tables from the real 525/526 files) plus migration 1082 (the stamp columns
the overlay writers' INSERT_SQLs name), applied verbatim AS amjis_app. The
nine grant migrations (1211/1216/1217/1220/1225/1231/1237/1238/1239) are then
applied verbatim by the shared fixture.

Requires a THROWAWAY database; skipped unless C7_BUILDER_ROLE_TEST_DATABASE_URL
is set (same disposable identity as the C7/C15/C18 suites):

  createdb -h 127.0.0.1 -p 55432 -U postgres c7_builder_role_test
  C7_BUILDER_ROLE_TEST_DATABASE_URL=postgresql://postgres@127.0.0.1:55432/c7_builder_role_test \
    python -m pytest tests/l3/test_builder_role_overlay_writers.py -q
"""
from __future__ import annotations

import os
import sys
from datetime import date
from pathlib import Path

import pytest

SIDECAR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SIDECAR))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import _builder_role as BR  # noqa: E402
import test_builder_role_resonance_writer as C7  # noqa: E402
import pipeline.orchestrator.writers.ka_gochara as kg  # noqa: E402
from services.ka_moorti_nirnaya import writer as moorti_writer  # noqa: E402
from services.ka_vedha_gochara import writer as vedha_writer  # noqa: E402

DSN = os.environ.get("C7_BUILDER_ROLE_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not DSN, reason="NOT_RUN: set C7_BUILDER_ROLE_TEST_DATABASE_URL to the disposable Postgres")

CHART = "c19c19c1-0000-4000-8000-00000000c19a"


@pytest.fixture(scope="module")
def builder_world():
    import psycopg

    BR.require_disposable(DSN)
    admin = psycopg.connect(DSN, autocommit=True, connect_timeout=5)
    try:
        BR.provision(admin)
        applied = {"c7_grant_target_schema": C7._build_schema_as_owner(admin)}
        with BR.as_owner(admin):
            # The stamp columns the overlay writers' INSERT_SQLs name (1082 is
            # a self-contained idempotent ALTER pair).
            p1082 = BR._find_migration("1082")
            admin.execute(p1082.read_text())
            applied["overlay_stamp_columns"] = p1082.name
        applied["grant_migrations"] = BR.apply_grant_migrations(admin)
        yield {"admin": admin, "applied": applied}
    finally:
        try:
            admin.execute("DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;")
            for role in (BR.BUILDER_ROLE, BR.OWNER_ROLE):
                admin.execute(f"DROP OWNED BY {role} CASCADE")
        finally:
            admin.close()


def _moorti_row() -> dict:
    """One literal moorti row (moorti_computed=false — the consistency CHECK
    then requires every moorti-derived field to be NULL)."""
    return {
        "chart_id": CHART,
        "ayanamsha_id": "lahiri_chitrapaksha",
        "graha": "Saturn",
        "target_sign_idx": 0,
        "target_sign_name": "Mesha",
        "window_start": date(2030, 1, 1),
        "window_end": date(2030, 1, 2),
        "start_truncated": False,
        "end_truncated": False,
        "moorti_computed": False,
        "moon_nakshatra_idx_at_ingress": None,
        "moon_nakshatra_name_at_ingress": None,
        "janma_nakshatra_idx": 0,
        "janma_nakshatra_fact_id": "fact-1",
        "nakshatra_offset": None,
        "moorti_name": None,
        "quality_tier": None,
        "phala_brief": None,
        "moorti_classical_citation": None,
        "source_qualification": "unsourced",
        "precision_regime": "date_grain",
        "corpus_verifiable": False,
        "formula_version": "v1",
        "upstream_fingerprint": None,
    }


def _vedha_row() -> dict:
    """One literal house_vedha row (grid fields NULL — the scope CHECK ties
    grid_basis to sarvatobhadra rows only)."""
    return {
        "chart_id": CHART,
        "ayanamsha_id": "lahiri_chitrapaksha",
        "vedha_kind": "house_vedha",
        "graha": "Saturn",
        "window_start": date(2030, 1, 1),
        "window_end": date(2030, 1, 2),
        "start_truncated": False,
        "end_truncated": False,
        "janma_reference_fact_id": "fact-1",
        "classical_citation": "citation-1",
        "uncited_extension": False,
        "grid_basis": None,
        "grid_school_tag": None,
        "source_qualification": "verse_cited",
        "precision_regime": "date_grain",
        "corpus_verifiable": True,
        "detail": "{}",
        "formula_version": "v1",
    }


def test_moorti_writer_delete_then_insert_lands_as_builder(builder_world):
    """SUCCEEDS — the ka_moorti_nirnaya writer's exact _DELETE_SQL +
    _INSERT_SQL land as data_plane_builder (the INSERT draws nextval on the
    identity sequence) and the row reads back on a builder connection."""
    with BR.connect_as_builder(DSN, connect_timeout=5) as conn:
        conn.execute(moorti_writer._DELETE_SQL, (CHART,))
        conn.execute(moorti_writer._INSERT_SQL, _moorti_row())
        conn.commit()
    with BR.connect_as_builder(DSN, connect_timeout=5) as conn:
        got = conn.execute(
            "SELECT count(*) FROM kala_moorti_nirnaya WHERE chart_id = %s",
            (CHART,)).fetchone()[0]
        assert got == 1, f"kala_moorti_nirnaya: expected 1 row, found {got}"


def test_vedha_writer_delete_then_insert_lands_as_builder(builder_world):
    """SUCCEEDS — the ka_vedha_gochara writer's exact _DELETE_SQL +
    _INSERT_SQL land as data_plane_builder (the INSERT draws nextval on the
    identity sequence) and the row reads back on a builder connection."""
    with BR.connect_as_builder(DSN, connect_timeout=5) as conn:
        conn.execute(vedha_writer._DELETE_SQL, (CHART,))
        conn.execute(vedha_writer._INSERT_SQL, _vedha_row())
        conn.commit()
    with BR.connect_as_builder(DSN, connect_timeout=5) as conn:
        got = conn.execute(
            "SELECT count(*) FROM kala_vedha_gochara WHERE chart_id = %s",
            (CHART,)).fetchone()[0]
        assert got == 1, f"kala_vedha_gochara: expected 1 row, found {got}"


def test_build_state_upsert_lands_as_builder(builder_world):
    """SUCCEEDS — the ka_gochara writer's build-state upsert
    (KaGocharaWriter._upsert_build_state: INSERT ... ON CONFLICT DO UPDATE on
    kala_gochara_v2_build_state) lands as data_plane_builder, and a second
    call exercises the UPDATE branch in place (still one row). The horizon
    is the writer's own HorizonAttestation type."""
    horizon = kg.progressive_horizon(date(2026, 6, 1))
    with BR.connect_as_builder(DSN, connect_timeout=5) as conn:
        kg.KaGocharaWriter._upsert_build_state(
            conn, CHART, "career_entry", class_fp="fp-1", horizon=horizon,
            contacts_evaluated=1, rows_written=1, skipped_reason=None,
            build_id="c19-build")
        conn.commit()
    with BR.connect_as_builder(DSN, connect_timeout=5) as conn:
        kg.KaGocharaWriter._upsert_build_state(
            conn, CHART, "career_entry", class_fp="fp-2", horizon=horizon,
            contacts_evaluated=2, rows_written=2, skipped_reason=None,
            build_id="c19-build")
        conn.commit()
    with BR.connect_as_builder(DSN, connect_timeout=5) as conn:
        got = conn.execute(
            "SELECT count(*), max(class_fingerprint) FROM kala_gochara_v2_build_state"
            " WHERE chart_id = %s AND generation = %s",
            (CHART, kg.GENERATION_V2)).fetchone()
        assert got[0] == 1 and got[1] == "fp-2", (
            f"kala_gochara_v2_build_state: expected 1 upserted row at fp-2, found {tuple(got)}")


def test_grant_migrations_covering_overlays_applied(builder_world):
    """CONTROL — the fixture really applied the REAL grant migration files,
    1239 among them (never a re-typed grant)."""
    names = builder_world["applied"]["grant_migrations"]
    assert [Path(p).name for p in BR.grant_migration_files()] == names
    assert any(n.startswith("1239_") for n in names)
