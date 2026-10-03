"""C18 (steward M20261002T052941-db54) — the ka_gochara writer's (generation
'2.0', ka_gochara_v2_materialize) delete-then-insert write path on
kala_gochara_windows_v2, exercised AS the production builder role.

C16 flagged that production carries data_plane_builder=arwd/amjis_app on
public.kala_gochara_windows_v2 (+ USAGE/SELECT on its identity sequence) with
no migration recording it; migration 1238 (this task) records that ACL. This
suite proves the recorded ACL is sufficient for the writer's own SQL layer:
its exact scoped DELETE (pipeline/orchestrator/writers/ka_gochara.py run
loop) and its exact INSERT_SQL with one minimal literal row land as an
AUTHENTICATED data_plane_builder connection, and the row reads back.

The writer itself cannot be driven without an ephemeris run (its arc source
and intensity grammar need the Swiss corpus), so — as in C15 — its SQL layer
is driven directly: the production DELETE text and the production INSERT_SQL
constant from the real writer module, never re-typed here (§N.8).

SCHEMA: the C7 suite's grant-target schema builder (reused verbatim — it
builds kala_gochara_windows_v2 from the real 542 file) plus migration 559
(term_breakdown / lambda_v3_ci_* / ci_source — the only columns the writer's
INSERT_SQL needs beyond 542), applied verbatim AS amjis_app. The eight grant
migrations (1211/1216/1217/1220/1225/1231/1237/1238) are then applied
verbatim by the shared fixture.

Requires a THROWAWAY database; skipped unless C7_BUILDER_ROLE_TEST_DATABASE_URL
is set (same disposable identity as the C7/C15 suites):

  createdb -h 127.0.0.1 -p 55432 -U postgres c7_builder_role_test
  C7_BUILDER_ROLE_TEST_DATABASE_URL=postgresql://postgres@127.0.0.1:55432/c7_builder_role_test \
    python -m pytest tests/l3/test_builder_role_ka_gochara_windows_v2.py -q
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

DSN = os.environ.get("C7_BUILDER_ROLE_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not DSN, reason="NOT_RUN: set C7_BUILDER_ROLE_TEST_DATABASE_URL to the disposable Postgres")

CHART = "c18c18c1-0000-4000-8000-00000000c18a"


@pytest.fixture(scope="module")
def builder_world():
    import psycopg

    BR.require_disposable(DSN)
    admin = psycopg.connect(DSN, autocommit=True, connect_timeout=5)
    try:
        BR.provision(admin)
        applied = {"c7_grant_target_schema": C7._build_schema_as_owner(admin)}
        with BR.as_owner(admin):
            # The only columns the writer's INSERT_SQL needs beyond 542's
            # table (559 is a self-contained idempotent ALTER DO block).
            p559 = BR._find_migration("559")
            admin.execute(p559.read_text())
            applied["v2_w15_decomp"] = p559.name
        applied["grant_migrations"] = BR.apply_grant_migrations(admin)
        yield {"admin": admin, "applied": applied}
    finally:
        try:
            admin.execute("DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;")
            for role in (BR.BUILDER_ROLE, BR.OWNER_ROLE):
                admin.execute(f"DROP OWNED BY {role} CASCADE")
        finally:
            admin.close()


def _minimal_row() -> dict:
    """One literal '2.0' point row — the exact parameter set the writer's own
    INSERT_SQL consumes (valence mapped through the writer's own vocabulary
    bridge, generation through its own constant)."""
    return {
        "chart_id": CHART,
        "event_class": "career_entry",
        "temporal_shape": "point",
        "window_start": date(2026, 1, 1),
        "window_end": date(2026, 1, 1),
        "peak_date": date(2026, 1, 1),
        "milestone_id": None,
        "is_irreversibility_milestone": False,
        "signed_intensity": 0.5,
        "raw_intensity": 0.5,
        "valence": kg._map_valence("favourable"),
        "is_adverse": False,
        "active_sentences": "[]",
        "contributing_systems": "[]",
        "suppression_state": "{}",
        "peak_basis": "gochara_lambda_e_v1",
        "calibration_state": "structural_prior",
        "source": "fixture",
        "generation": kg.GENERATION_V2,
        "term_breakdown": "{}",
        "lambda_v3_ci_low": None,
        "lambda_v3_ci_high": None,
        "ci_source": None,
    }


def test_v2_writer_delete_then_insert_lands_as_builder(builder_world):
    """SUCCEEDS — the writer's exact scoped DELETE (chart × event_class ×
    generation='2.0') and its exact INSERT_SQL land as data_plane_builder,
    and the row reads back on the same builder connection. Proven privileges:
    SELECT/INSERT/DELETE on kala_gochara_windows_v2 + USAGE on its identity
    sequence (the INSERT draws nextval) — the ACL migration 1238 records."""
    with BR.connect_as_builder(DSN, connect_timeout=5) as conn:
        conn.execute(
            f"DELETE FROM {kg.TABLE} WHERE chart_id = %s AND event_class = %s AND generation = %s",
            (CHART, "career_entry", kg.GENERATION_V2))
        conn.execute(kg.INSERT_SQL, _minimal_row())
        conn.commit()
    with BR.connect_as_builder(DSN, connect_timeout=5) as conn:
        got = conn.execute(
            f"SELECT count(*) FROM {kg.TABLE} WHERE chart_id = %s AND generation = %s",
            (CHART, kg.GENERATION_V2)).fetchone()[0]
        assert got == 1, f"{kg.TABLE}: expected 1 '{kg.GENERATION_V2}' row, found {got}"


def test_grant_migrations_covering_v2_applied(builder_world):
    """CONTROL — the fixture really applied the REAL grant migration files,
    1238 among them (never a re-typed grant)."""
    names = builder_world["applied"]["grant_migrations"]
    assert [Path(p).name for p in BR.grant_migration_files()] == names
    assert any(n.startswith("1238_") for n in names)
