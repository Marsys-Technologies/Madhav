"""One assertion, real SQL, typed states, candidate pin and mutation oracles."""
from copy import deepcopy
import re
from types import SimpleNamespace

import pytest
from psycopg.types.json import Jsonb

from services.kala_core.manifest import open_candidate
from pipeline.orchestrator.writers.ka_kala_darshana import KaKalaDarshanaWriter
from tests.l3.kala_core.e2e.test_assertion import envelope
from tests.l3.kala_db.e2e.conftest import REPO

CHART = envelope()["chart_id"]
BUILD = "00000000-0000-0000-0000-000000000002"


def seed(conn):
    conn.execute("INSERT INTO kala_obstruction (chart_id, obstruction_type, severity, severity_score) "
                 "VALUES (%s, 'malefic_transit', 'mild', 0.25)", (CHART,))
    conn.execute("INSERT INTO kala_darshana (chart_id, effective_score, net_label) VALUES (%s, 0.7, 'neutral')", (CHART,))
    conn.execute("INSERT INTO kala_gochara_windows "
                 "(id, chart_id, generation, event_class, temporal_shape, window_start, window_end, peak_date, "
                 "signed_intensity, raw_intensity, valence, is_adverse, source) "
                 "VALUES (11, %s, 'candidate-a', 'career', 'interval', '2026-10-01', '2026-10-03', '2026-10-02', "
                 "0, 0, 'unknown', false, 'fixture')", (CHART,))
    axes = deepcopy(envelope()["payload"])
    axes.pop("effective_state")
    conn.execute("UPDATE kala_gochara_windows SET suppression_state = %s WHERE id = 11", (Jsonb(axes),))


def ctx(conn, row=None, build_id=BUILD):
    return SimpleNamespace(db_conn=conn, build_id=build_id, dry_run=False,
                           config={"chart_id": CHART, "kala_assertion_fixture": row or envelope()})


def candidate(conn):
    return open_candidate(conn, chart_id=CHART, generation="candidate-a", build_id=BUILD,
                          model_digest="fixture-v1", rule_registry_version="fixture-v1", conventions={"fixture": True})


def legacy(conn):
    return [conn.execute(f"SELECT to_jsonb(t)::text FROM {t} t WHERE generation IS NULL ORDER BY id").fetchall()
            for t in ("kala_obstruction", "kala_darshana")]


def test_migration_adds_candidate_columns_without_rekeying_legacy(conn):
    columns = conn.execute("SELECT column_name FROM information_schema.columns "
                           "WHERE table_schema LIKE 'pg_temp_%' AND table_name = 'kala_obstruction'").fetchall()
    assert {"generation", "assertion_id", "effective_state", "exposure", "knowledge", "defeat_state"} <= {r[0] for r in columns}


def test_no_candidate_dispatch_completes_without_touching_legacy(conn):
    seed(conn)
    before = legacy(conn)
    result = KaKalaDarshanaWriter().run(ctx(conn))
    assert result.rows_inserted == 0
    assert legacy(conn) == before
    assert conn.execute("SELECT count(*) FROM kala_darshana WHERE generation IS NOT NULL").fetchone()[0] == 0


def test_candidate_read_model_carries_cancelled_state_and_source_ids(conn):
    seed(conn)
    candidate(conn)
    before = legacy(conn)
    assert KaKalaDarshanaWriter().run(ctx(conn)).rows_inserted == 1
    assert conn.execute("SELECT effective_state, defeat_state, severity_score FROM kala_obstruction "
                        "WHERE generation = 'candidate-a'").fetchone() == ("obstruction_cancelled", "cancelled", 0.0)
    assert conn.execute("SELECT candidate_effective_state, source_assertion_ids, effective_score FROM kala_darshana "
                        "WHERE generation = 'candidate-a'").fetchone() == ("obstruction_cancelled", ["negative:window:11"], 0.0)
    assert legacy(conn) == before
    KaKalaDarshanaWriter().run(ctx(conn))
    assert conn.execute("SELECT count(*) FROM kala_darshana WHERE generation = 'candidate-a'").fetchone()[0] == 1


@pytest.mark.parametrize("mutation", ["current", "other_chart", "missing_source", "wrong_source_generation", "wrong_source_interval", "invented_intraday", "live_candidate", "source_axes"])
def test_database_mutations_fail_before_any_candidate_write(conn, mutation):
    seed(conn)
    candidate(conn)
    row = deepcopy(envelope())
    if mutation == "current": row["generation"] = "current"
    if mutation == "other_chart": row["chart_id"] = "00000000-0000-0000-0000-000000000099"
    if mutation == "missing_source": row["roots"]["record_ids"] = ["999"]
    if mutation == "wrong_source_generation": conn.execute("UPDATE kala_gochara_windows SET generation = 'current'")
    if mutation == "wrong_source_interval": row["interval"]["t1"] = "2026-10-04T00:00:00Z"
    if mutation == "invented_intraday": row["interval"]["t0"] = "2026-10-01T12:00:00Z"
    if mutation == "live_candidate": conn.execute("UPDATE kala_layer_candidate SET conventions = '{}'::jsonb")
    if mutation == "source_axes": conn.execute("UPDATE kala_gochara_windows SET suppression_state = '{}'::jsonb")
    with pytest.raises(ValueError):
        KaKalaDarshanaWriter().run(ctx(conn, row))
    assert conn.execute("SELECT count(*) FROM kala_obstruction WHERE generation IS NOT NULL").fetchone()[0] == 0


def test_registry_query_returns_the_pinned_candidate_and_never_current(conn):
    seed(conn)
    candidate(conn)
    KaKalaDarshanaWriter().run(ctx(conn))
    ts = (REPO / "platform/src/lib/retrieval/registry/layers/L3_kala/query_assertion_fixture.ts").read_text()
    # Execute the capability's actual SQL, rather than a test reimplementation.
    sql = re.search(r"export const ASSERTION_FIXTURE_SQL = `(.*?)`", ts, re.S).group(1)
    sql = sql.replace("$1", "%s").replace("$2", "%s")
    rows = conn.execute(sql, (CHART, "candidate-a")).fetchall()
    assert len(rows) == 1
    assert rows[0][2:5] == ("obstruction_cancelled", ["negative:window:11"], envelope()["roots"]["record_ids"])
    assert conn.execute(sql, (CHART, "current")).fetchall() == []


def test_testimony_writes_no_numeric_contribution(conn):
    seed(conn)
    candidate(conn)
    row = envelope()
    row["operator_role"] = "testimony"
    KaKalaDarshanaWriter().run(ctx(conn, row))
    assert conn.execute("SELECT effective_score FROM kala_darshana WHERE generation = 'candidate-a'").fetchone()[0] == 0


def test_l4_pratikara_keeps_reading_only_legacy_obstructions(conn):
    from pipeline.orchestrator.writers.ph_pratikara import PhPratikaraWriter
    conn.execute("CREATE TEMP TABLE kala_convergence (convergence_id bigint, window_start date, "
                 "window_end date, domain text, constituent_factors jsonb)")
    seed(conn)
    candidate(conn)
    before = PhPratikaraWriter()._load_obstructions(conn, CHART)
    KaKalaDarshanaWriter().run(ctx(conn))
    assert PhPratikaraWriter()._load_obstructions(conn, CHART) == before


def test_runtime_dict_row_connection_can_run_the_slice(conn):
    from psycopg.rows import dict_row
    seed(conn)
    candidate(conn)
    conn.row_factory = dict_row
    assert KaKalaDarshanaWriter().run(ctx(conn)).rows_inserted == 1


def test_a_published_partition_cannot_be_replaced(conn):
    seed(conn)
    candidate(conn)
    KaKalaDarshanaWriter().run(ctx(conn))
    conn.execute("UPDATE kala_layer_candidate SET state = 'published'")
    before = conn.execute("SELECT to_jsonb(d)::text FROM kala_darshana d ORDER BY id").fetchall()
    with pytest.raises(ValueError, match="building candidate"):
        KaKalaDarshanaWriter().run(ctx(conn))
    assert conn.execute("SELECT to_jsonb(d)::text FROM kala_darshana d ORDER BY id").fetchall() == before
