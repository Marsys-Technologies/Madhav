"""J4P-B4/B5: real PostgreSQL must refuse malformed ordinary periods.

Ported from the independent review's test_review_clock_sql.py (two required
refusals and one valid control). Intervals are synthetic; only settlement
identity labels are reused. The mandatory kala-db-tests CI job collects this
file with KALA_REQUIRE_DB=1, so unavailable DB proof cannot silently skip.
"""
from datetime import datetime, timezone
import json

import psycopg
import psycopg.rows
import pytest

from services.gochara_kernel import dasha_read as reader
from services.kala_core import clocks

SETTLEMENT = json.loads(reader.SETTLEMENT_PATH.read_text())
CHART, BUILD = SETTLEMENT["chart_id"], SETTLEMENT["run_id"]
AYA = "lahiri_chitrapaksha"
AS_OF = datetime(2026, 1, 9, tzinfo=timezone.utc)
START = datetime(2026, 1, 1, tzinfo=timezone.utc)
END = datetime(2026, 2, 1, tzinfo=timezone.utc)


@pytest.fixture
def db(kala_db_dsn):
    with psycopg.connect(kala_db_dsn, row_factory=psycopg.rows.dict_row) as conn:
        conn.execute("""CREATE TABLE chart_dashas (
            dasha_row_id uuid, chart_id uuid, build_id uuid, system_id text,
            ayanamsha_id text, level_n int, parent_row_id uuid, lord_graha text,
            start_iso timestamptz, end_iso timestamptz,
            verification_pass_status text, applies_to_this_chart_flag bool,
            is_truncated_at_window_start bool, is_truncated_at_window_end bool,
            start_date date, end_date date, lord_to_parent_relationship text,
            kp_sublevel text)""")   # the real column the verifier's population read selects
        for system in ("vimshottari", "yogini"):
            conn.execute("""INSERT INTO chart_dashas
                (dasha_row_id, chart_id, build_id, system_id, ayanamsha_id,
                 level_n, lord_graha, start_iso, end_iso, verification_pass_status,
                 applies_to_this_chart_flag, is_truncated_at_window_start,
                 is_truncated_at_window_end)
                VALUES (gen_random_uuid(), %s, %s, %s, %s, 1, 'Saturn',
                        %s, %s, 'two_pass_verified', true, false, false)""",
                (CHART, BUILD, system, AYA, START, END))
        yield conn
        conn.rollback()


def read(conn, path="boundaries"):
    if path == "avadhi":
        # The writer's real projection, followed by its existing F2 validator.
        rows = reader.execute_governed_dasha_query(
            conn, CHART, reader.dasha_query("avadhi_periods"),
            (CHART, AYA, ["yogini"]), ayanamsha_id=AYA,
            clock_tier="two_pass_verified").fetchall()
        return clocks.validate_clock_rows(rows, build_id=BUILD, tier="two_pass_verified")
    if path == "boundaries":
        return clocks.boundaries(
            conn, CHART, "yogini", as_of=AS_OF, build_id=BUILD,
            ayanamsha_id=AYA, tier="two_pass_verified")
    return clocks.period_context(
            conn, CHART, AS_OF, "yogini", build_id=BUILD,
            ayanamsha_id=AYA, tier="two_pass_verified")


def add_period(conn, end, *, start=START):
    conn.execute("""INSERT INTO chart_dashas
        (dasha_row_id, chart_id, build_id, system_id, ayanamsha_id, level_n,
         lord_graha, start_iso, end_iso, verification_pass_status,
         applies_to_this_chart_flag, is_truncated_at_window_start,
         is_truncated_at_window_end)
        VALUES (gen_random_uuid(), %s, %s, 'yogini', %s, 1, 'Mars',
                %s, %s, 'two_pass_verified', true, false, false)""",
        (CHART, BUILD, AYA, start, end))


def test_valid_settled_clock_still_has_both_boundaries(db):
    boundaries = read(db)
    assert [(b.instant, b.endpoint, b.lord) for b in boundaries] == [
        (START, "start", "Saturn"), (END, "end", "Saturn")]
    assert all((b.build_id, b.ayanamsha_id, b.tier) ==
               (BUILD, AYA, "two_pass_verified") for b in boundaries)
    assert read(db, "period_context").lords == {"MD": "Saturn"}
    assert len(read(db, "avadhi")) == 1


@pytest.mark.parametrize("path", ["boundaries", "period_context", "avadhi"])
@pytest.mark.parametrize("end", ["2026-01-01Z", "2025-12-31Z"])
def test_malformed_period_must_refuse_instead_of_being_silently_erased(db, end, path):
    add_period(db, end)
    # B5 moves this refusal before projection, at the shared reader boundary.
    with pytest.raises(reader.DashaBuildRefused, match="dasha_period_malformed.*non-positive period"):
        read(db, path)


@pytest.mark.parametrize("path", ["boundaries", "period_context", "avadhi"])
@pytest.mark.parametrize("start,end", [(None, END), (START, None)])
def test_missing_boundary_must_refuse(db, path, start, end):
    add_period(db, end, start=start)
    with pytest.raises(reader.DashaBuildRefused, match="dasha_period_malformed.*no datetime boundary"):
        read(db, path)


@pytest.mark.parametrize("mutation,reason", [
    ("lord_graha = NULL", "no lord"),
    ("level_n = 2, parent_row_id = gen_random_uuid()", "hierarchy_unavailable"),
    ("applies_to_this_chart_flag = NULL", "applicability_unknown_or_inapplicable"),
])
def test_other_f2_forbidden_shapes_remain_visible_to_validator(db, mutation, reason):
    db.execute(f"UPDATE chart_dashas SET {mutation} WHERE system_id = 'yogini'")
    with pytest.raises(clocks.ClockUnavailable, match=reason):
        read(db)


def test_scope_cap_is_an_explicit_non_period_namespace(db):
    db.execute("""INSERT INTO chart_dashas
        (dasha_row_id, chart_id, build_id, system_id, ayanamsha_id,
         level_n, start_iso, end_iso, verification_pass_status)
        VALUES (gen_random_uuid(), %s, %s, 'scope_cap', 'INVARIANT',
                4, %s, %s, 'two_pass_verified')""", (CHART, BUILD, START, START))
    assert len(read(db)) == 2


@pytest.mark.parametrize("end", ["2026-01-01Z", "2025-12-31Z", None])
def test_live_independent_verifier_refuses_before_ledger_and_record_range_cuts(db, end):
    from services.gochara_kernel import inventory_verifier as verifier

    db.execute("""CREATE TABLE ka_gochara_search_input_snapshot (
        chart_id uuid, generation text, consumed_fact_ids text[], consumed_dasha_row_ids uuid[])""")   # the 1206 columns the verifier reads (snapshot_copies)
    db.execute("""CREATE TABLE ka_gochara_search_inventory (
        chart_id uuid, generation text, horizon tstzrange)""")
    # A corrupt pinned row omitted from the snapshot must still refuse.
    db.execute("""INSERT INTO chart_dashas
        (dasha_row_id, chart_id, build_id, system_id, ayanamsha_id, level_n,
         lord_graha, start_iso, end_iso, verification_pass_status)
        VALUES (gen_random_uuid(), %s, %s, 'vimshottari', %s, 1,
                'Mars', %s, %s, 'two_pass_verified')""", (CHART, BUILD, AYA, START, end))
    db.execute("""INSERT INTO ka_gochara_search_input_snapshot
        SELECT %s, '5.0', ARRAY[]::text[], array_agg(dasha_row_id) FROM chart_dashas
        WHERE system_id = 'vimshottari' AND lord_graha = 'Saturn'""", (CHART,))
    db.execute("""INSERT INTO ka_gochara_search_inventory
        VALUES (%s, '5.0', tstzrange(%s, %s, '[)'))""", (CHART, START, END))
    # The independent verifier uses tuple rows, as in the production job.
    db.row_factory = psycopg.rows.tuple_row
    with pytest.raises(verifier.Unverifiable, match="invalid period"):
        verifier.validate_consumed_dasha_population(db, chart_id=CHART, generation="5.0")
