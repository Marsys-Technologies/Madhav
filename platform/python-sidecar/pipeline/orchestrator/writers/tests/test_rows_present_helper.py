"""WFIX-A: the shared row-count reader (writers/_rows_present.py) and the real-Postgres proof of the writers' literal COUNT statements.

Unit tests need no database. The ``pg`` tests run only against an explicitly named LOCAL DISPOSABLE database (same guard as the bg_texts mutation
suite); unset, they skip locally:

  createdb -h 127.0.0.1 -p 55477 -U postgres wfix_a_rows_present_test
  WFIX_A_ROWS_PRESENT_TEST_DATABASE_URL=postgresql://postgres@127.0.0.1:55477/wfix_a_rows_present_test \\
    python -m pytest pipeline/orchestrator/writers/tests/test_rows_present_helper.py -q
"""
from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

import pytest

from pipeline.orchestrator.writers._rows_present import present_count

CHART = "482012f1-710e-4a25-994a-93821f5871aa"


@pytest.mark.parametrize("row, want", [({"n": 4}, 4), ({"count": 0}, 0), ((7,), 7), ([9],  9), ({"n": 5.0}, 5)])
def test_present_count_reads_dict_rows_and_tuple_rows_alike(row, want):
    assert present_count(row) == want


@pytest.mark.parametrize("bad", [None, {"n": None}, {"n": -1}, {"n": 1.5}, {"n": True}, (None,)])
def test_a_non_count_answer_is_an_error_not_a_zero(bad):
    with pytest.raises(RuntimeError, match="not a row count"):
        present_count(bad)


@pytest.mark.parametrize("module, constants", [
    ("bg_ephemeris", ["ROWS_PRESENT_SQL"]), ("bg_ontology", ["ROWS_PRESENT_SQL"]), ("bg_reference", ["ROWS_PRESENT_SQL"]),
    ("bg_formula_constants", ["ROWS_PRESENT_SQL"]), ("bg_vidhi_primitives", ["ROWS_PRESENT_SQL"]), ("bg_sky_calendar", ["ROWS_PRESENT_SQL"]),
    ("bg_texts", ["ROWS_PRESENT_SQL"]), ("bg_text_index", ["ROWS_PRESENT_SQL"]), ("bg_muhurta_lattice", ["ROWS_PRESENT_SQL"]),
    ("bg_medical_mappings", ["ROWS_PRESENT_SQL_PRIMARY", "ROWS_PRESENT_SQL_NAKSHATRA", "ROWS_PRESENT_SQL_SIGN"]),
    ("bg_transit_rules", ["ROWS_PRESENT_SQL_RULES", "ROWS_PRESENT_SQL_ENGINE"]),
    ("bo_bimba", ["ROWS_PRESENT_SQL"]), ("bo_cgm_motifs", ["ROWS_PRESENT_SQL"]), ("bo_karanajala", ["ROWS_PRESENT_SQL"]),
])
def test_every_count_statement_is_a_literal_single_select_the_census_can_scan(module, constants):
    """The census reads these statically (reads-match / Idem): a literal SELECT count over named relations, never an f-string / `+` built table."""
    import importlib
    import re

    mod = importlib.import_module(f"pipeline.orchestrator.writers.{module}")
    src = Path(mod.__file__).read_text(encoding="utf-8")
    for name in constants:
        sql = getattr(mod, name)
        assert re.match(r"^SELECT (count\(|\(SELECT count\()", sql) and ";" not in sql, (module, name, sql)
        assert not re.search(r"\{|\bformat\(", sql), (module, name)
        assert f"{name} =" in src and f"f\"{name}" not in src


# ── real Postgres (disposable, loopback-guarded) ──────────────────────────────────────────────────

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "tests" / "l3"))
DSN = os.environ.get("WFIX_A_ROWS_PRESENT_TEST_DATABASE_URL")


@pytest.fixture()
def pg():
    if not DSN:
        pytest.skip("NOT_RUN: WFIX_A_ROWS_PRESENT_TEST_DATABASE_URL is unset (no disposable Postgres in this job)")
    import psycopg
    import psycopg.rows
    from _disposable_db_guard import validate_disposable_dsn

    validate_disposable_dsn(DSN, "wfix_a_rows_present_test")
    conn = psycopg.connect(DSN, row_factory=psycopg.rows.dict_row)   # the orchestrator's own row factory
    yield conn
    conn.rollback()
    conn.close()


def _count(pg, sql, params=()):
    with pg.cursor() as cur:
        cur.execute(sql, params)
        return present_count(cur.fetchone())


def test_pg_chart_scoped_statements_count_exactly_the_declared_slices(pg):
    from pipeline.orchestrator.writers import bo_bimba, bo_cgm_motifs, bo_karanajala

    other = str(uuid.uuid4())
    with pg.cursor() as cur:
        cur.execute("CREATE TEMP TABLE bodha_cgm_nodes (chart_id uuid, node_type text)")
        cur.execute("CREATE TEMP TABLE bodha_cgm_edges (chart_id uuid)")
        cur.execute("CREATE TEMP TABLE bodha_contradictions (chart_id uuid)")
        cur.execute("CREATE TEMP TABLE bodha_cgm_motifs (chart_id uuid)")
        cur.execute("CREATE TEMP TABLE bodha_cgm_sub_graphs (chart_id uuid)")
        cur.execute("CREATE TEMP TABLE bodha_cgm_chart_topology_summary (chart_id uuid)")
        for t, n in (("graha", 9), ("bhava", 12), ("domain", 13), ("yoga", 4), ("dosha", 2), ("arudha", 12), ("special_lagna", 7), ("other", 5)):
            cur.execute("INSERT INTO bodha_cgm_nodes SELECT %s::uuid, %s FROM generate_series(1, %s)", (CHART, t, n))
        cur.execute("INSERT INTO bodha_cgm_nodes SELECT %s::uuid, 'graha' FROM generate_series(1, 100)", (other,))      # another chart: never counted
        cur.execute("INSERT INTO bodha_cgm_edges SELECT %s::uuid FROM generate_series(1, 30)", (CHART,))
        cur.execute("INSERT INTO bodha_cgm_edges SELECT %s::uuid FROM generate_series(1, 9)", (other,))
        cur.execute("INSERT INTO bodha_contradictions SELECT %s::uuid FROM generate_series(1, 3)", (CHART,))
        cur.execute("INSERT INTO bodha_cgm_motifs SELECT %s::uuid FROM generate_series(1, 20)", (CHART,))
        cur.execute("INSERT INTO bodha_cgm_sub_graphs SELECT %s::uuid FROM generate_series(1, 2)", (CHART,))
        cur.execute("INSERT INTO bodha_cgm_chart_topology_summary SELECT %s::uuid FROM generate_series(1, 5)", (CHART,))
    assert _count(pg, bo_bimba.ROWS_PRESENT_SQL, (CHART,)) == 9 + 12 + 13 + 4 + 2        # the five owned classes; not arudha / special_lagna / other
    assert _count(pg, bo_cgm_motifs.ROWS_PRESENT_SQL, (CHART,) * 3) == 20 + 2 + 5
    assert _count(pg, bo_karanajala.ROWS_PRESENT_SQL, (CHART,) * 3) == 30 + 3 + 12 + 7


def test_pg_muhurta_year_partitions_are_disjoint_and_cover_the_table(pg):
    from pipeline.orchestrator.writers import bg_muhurta_lattice

    with pg.cursor() as cur:
        cur.execute("CREATE TEMP TABLE bg_muhurta_lattice (start_utc timestamp without time zone)")
        cur.execute("INSERT INTO bg_muhurta_lattice VALUES ('2026-12-31 23:59:59'), ('2027-01-01 00:00:00'), ('2027-06-01 00:00:00')")
    d = datetime
    # first planned year: open lower edge; last planned year: open upper edge
    got = [_count(pg, bg_muhurta_lattice.ROWS_PRESENT_SQL, w) for w in ((None, None, d(2027, 1, 1), d(2027, 1, 1)), (d(2027, 1, 1), d(2027, 1, 1), None, None))]
    assert got == [1, 2] and sum(got) == 3                  # the boundary row belongs to exactly ONE year


def test_pg_vidhi_writer_reports_present_rows_on_a_converged_rerun(pg):
    """The real writer, real SQL, real ON CONFLICT ... WHERE IS DISTINCT FROM: the second run changes nothing (every upsert's
    rowcount is 0) yet must report all rows present."""
    from pipeline.orchestrator.writers import ContextSpec
    from pipeline.orchestrator.writers.bg_vidhi_primitives import PRIMITIVE_ROWS, VidhiPrimitivesWriter

    with pg.cursor() as cur:
        cur.execute("""CREATE TEMP TABLE vidhi_primitives (
            primitive_id text PRIMARY KEY, version int, definition text, category text, live_tool text,
            tool_args jsonb, fallback_face text, known_gap text, mandatory_tags text[], cr27_prevents text[],
            updated_at timestamptz)""")
    ctx = ContextSpec(asset_id="bg_vidhi_primitives", build_id=str(uuid.uuid4()), db_conn=pg)
    first = VidhiPrimitivesWriter().run(ctx)
    second = VidhiPrimitivesWriter().run(ctx)
    assert first.rows_inserted == second.rows_inserted == len(PRIMITIVE_ROWS)
    assert "0 inserted/updated, 0 stale deleted" in second.notes      # the rerun really changed nothing
