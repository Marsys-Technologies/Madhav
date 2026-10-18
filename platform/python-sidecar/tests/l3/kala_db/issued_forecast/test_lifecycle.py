"""K6-5a: exercise the shipped lifecycle DDL and the real immutable registrar."""
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import psycopg
from psycopg.types.json import Jsonb
import pytest

from services.kala_core.idempotency import ImmutableIssueConflict, insert_immutable_checked
from tests.l3.kala_db.conftest import kala_db_dsn  # noqa: F401 — module-local disposable fixture

ROOT = Path(__file__).parents[5]
MIGRATION = ROOT / "migrations/1351_issued_forecast_lifecycle.sql"
FINITE_INTERVALS = ROOT / "migrations/1352_issued_forecast_finite_intervals.sql"
GUARDS = [ROOT / "migrations/1380_issued_forecast_immutability_guard.sql"]
CHART = UUID("11111111-1111-4111-8111-111111111111")
ISSUE = UUID("22222222-2222-4222-8222-222222222222")
OUTCOME = UUID("33333333-3333-4333-8333-333333333333")
AT = datetime(2026, 10, 10, 10, tzinfo=timezone.utc)


@pytest.fixture(scope="module")
def database(kala_db_dsn):
    assert MIGRATION.is_file(), "K6-5a lifecycle is absent on base"
    with psycopg.connect(kala_db_dsn) as conn:
        # Real manifest key from migration 1330; no published row is fabricated.
        conn.execute("CREATE TABLE kala_layer_candidate (chart_id uuid NOT NULL, "
                     "generation text NOT NULL, PRIMARY KEY (chart_id, generation))")
        conn.execute("INSERT INTO kala_layer_candidate VALUES (%s, 'fixture:v1')", (CHART,))
        conn.execute(MIGRATION.read_text())
        conn.execute(FINITE_INTERVALS.read_text())
        for guard in GUARDS:
            conn.execute(guard.read_text())
    return kala_db_dsn


@pytest.fixture
def conn(database):
    with psycopg.connect(database) as connection:
        yield connection
        connection.rollback()


def row(conn, **changes):
    intervals = conn.execute(
        "SELECT '{[2027-01-01 00:00Z,2027-01-03 00:00Z),"
        "[2027-02-01 00:00Z,2027-02-03 00:00Z)}'::tstzmultirange"
    ).fetchone()[0]
    return dict({
        "issue_id": ISSUE, "version": 1, "chart_id": CHART,
        "generation": "fixture:v1", "event_class": "career_change",
        "phase": "fruition", "affected_person": "native", "episode": "career:1",
        "issued_at": AT, "information_cutoff": AT,
        "delivered_at": AT, "delivery_channel": "fixture:native-inbox",
        "delivered_statement": "A career change in either disclosed interval.",
        "result_policy": "all_null", "calibration_status": "uncalibrated",
        "intervals": intervals, "disclosed_grain": "day",
        "point_functional": "none", "probability_target": None,
        "falsifier": Jsonb({"ontology_locator": "fixture:career_change:1",
                           "observation_predicate": "no career change in either interval"}),
    }, **changes)


def insert(conn, **changes):
    value = row(conn, **changes)
    return insert_immutable_checked(conn, "issued_forecast",
                                    {"issue_id": value["issue_id"], "version": value["version"]}, value)


def outcome(conn, version=1, outcome_id=OUTCOME):
    conn.execute("INSERT INTO issued_forecast_outcome "
                 "(outcome_id, issue_id, version, observed_at, recorded_at, observation) "
                 "VALUES (%s, %s, %s, %s, %s, %s)",
                 (outcome_id, ISSUE, version, AT, AT, Jsonb({"occurred": True})))


def test_referenced_issue_cannot_be_deleted(conn):
    insert(conn)
    outcome(conn)
    with pytest.raises(psycopg.errors.ObjectNotInPrerequisiteState):
        with conn.transaction():
            conn.execute("DELETE FROM issued_forecast WHERE issue_id = %s", (ISSUE,))
    assert conn.execute("SELECT issue_id, version FROM issued_forecast_outcome").fetchall() == [(ISSUE, 1)]


def test_reference_fk_independently_refuses_the_planted_delete(conn):
    insert(conn)
    outcome(conn)
    # Local mutation: even removing the append-only trigger cannot orphan an
    # outcome. This transaction is rolled back; no production trigger changes.
    conn.execute("ALTER TABLE issued_forecast DISABLE TRIGGER issued_forecast_immutable_rows")
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        with conn.transaction():
            conn.execute("DELETE FROM issued_forecast WHERE issue_id = %s", (ISSUE,))
    assert conn.execute("SELECT count(*) FROM issued_forecast").fetchone() == (1,)


def test_identical_retry_keeps_the_delivered_statement_and_changed_retry_fails(conn):
    assert insert(conn) is True
    assert insert(conn) is False
    with pytest.raises(ImmutableIssueConflict):
        insert(conn, delivered_statement="Changed after delivery")
    assert conn.execute("SELECT delivered_statement FROM issued_forecast").fetchone() == (
        "A career change in either disclosed interval.",)


def test_refinements_are_distinct_issues_but_credit_clusters_by_episode(conn):
    insert(conn)
    insert(conn, version=2, delivered_statement="Refined statement")
    outcome(conn)
    outcome(conn, version=2, outcome_id=UUID("44444444-4444-4444-8444-444444444444"))
    assert conn.execute("SELECT count(*) FROM issued_forecast").fetchone() == (2,)
    assert conn.execute("SELECT count(*) FROM (SELECT DISTINCT chart_id, event_class, phase, "
                        "affected_person, episode FROM issued_forecast "
                        "JOIN issued_forecast_outcome USING (issue_id, version)) episodes").fetchone() == (1,)


@pytest.mark.parametrize("statement", [
    "UPDATE issued_forecast SET delivered_statement = 'rewritten'",
    "UPDATE issued_forecast SET version = 2",
    "UPDATE issued_forecast SET point_functional = 'midpoint'",
    "UPDATE issued_forecast SET episode = 'career:2'",
    "UPDATE issued_forecast SET phase = 'onset'",
    "UPDATE issued_forecast SET affected_person = 'partner'",
    "DELETE FROM issued_forecast",
    "TRUNCATE issued_forecast CASCADE",
    "UPDATE issued_forecast_outcome SET observation = '{}'::jsonb",
    "UPDATE issued_forecast_outcome SET observed_at = observed_at + interval '1 day'",
    "UPDATE issued_forecast_outcome SET recorded_at = recorded_at + interval '1 day'",
    "UPDATE issued_forecast_outcome SET outcome_id = gen_random_uuid()",
    "DELETE FROM issued_forecast_outcome",
    "TRUNCATE issued_forecast_outcome",
])
def test_sql_mutations_cannot_rewrite_or_erase_issued_history(conn, statement):
    insert(conn)
    outcome(conn)
    with pytest.raises(psycopg.errors.ObjectNotInPrerequisiteState):
        with conn.transaction():
            conn.execute(statement)
    assert conn.execute("SELECT count(*) FROM issued_forecast_outcome").fetchone() == (1,)


@pytest.mark.parametrize("changes", [
    {"version": 0}, {"delivery_channel": " "}, {"delivered_at": None},
    {"delivered_statement": ""}, {"information_cutoff": datetime(2027, 1, 1, tzinfo=timezone.utc)},
    {"probability_target": 0.7},
    {"probability_target": -0.1, "calibration_status": "calibrated", "result_policy": "calibrated_probability"},
    {"probability_target": 1.1, "calibration_status": "calibrated", "result_policy": "calibrated_probability"},
    {"probability_target": 0.7, "calibration_status": "calibrated"},
    {"event_class": ""}, {"episode": ""}, {"disclosed_grain": ""},
    {"point_functional": ""}, {"falsifier": Jsonb({})},
])
def test_new_issue_requires_delivery_identity_and_qualified_probability(conn, changes):
    with pytest.raises((psycopg.errors.CheckViolation, psycopg.errors.NotNullViolation)):
        insert(conn, **changes)


def test_calibrated_probability_and_disconnected_intervals_are_preserved(conn):
    insert(conn, calibration_status="calibrated", result_policy="calibrated_probability", probability_target=0.7)
    assert conn.execute("SELECT count(*) FROM issued_forecast, "
                        "unnest(intervals) AS part").fetchone() == (2,)
    assert conn.execute("SELECT probability_target::float8 FROM issued_forecast").fetchone() == (0.7,)


def test_empty_interval_is_not_an_issued_forecast(conn):
    empty = conn.execute("SELECT '{}'::tstzmultirange").fetchone()[0]
    with pytest.raises(psycopg.errors.CheckViolation):
        insert(conn, intervals=empty)


@pytest.mark.parametrize("literal", [
    "{[2027-01-01 00:00Z,)}", "{(,2027-01-01 00:00Z)}",
    "{(2027-01-01 00:00Z,2027-01-03 00:00Z)}",
    "{[2027-01-01 00:00Z,2027-01-03 00:00Z]}",
    "{[2027-01-01 00:00Z,infinity)}", "{[-infinity,2027-01-01 00:00Z)}",
])
def test_issued_intervals_cannot_hide_unbounded_or_wrong_grain_boundaries(conn, literal):
    with pytest.raises(psycopg.errors.CheckViolation):
        insert(conn, intervals=literal)


def test_unknown_manifest_or_issue_is_refused(conn):
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        with conn.transaction():
            insert(conn, generation="fixture:missing")
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        with conn.transaction():
            outcome(conn)
    assert conn.execute("SELECT count(*) FROM issued_forecast_outcome").fetchone() == (0,)


def test_reapplying_migration_preserves_issues_and_outcomes(conn):
    insert(conn)
    outcome(conn)
    before = conn.execute("SELECT to_jsonb(i) FROM issued_forecast i").fetchall()
    conn.execute(MIGRATION.read_text())
    conn.execute(FINITE_INTERVALS.read_text())
    assert conn.execute("SELECT to_jsonb(i) FROM issued_forecast i").fetchall() == before


@pytest.mark.parametrize('table', ['issued_forecast', 'issued_forecast_outcome'])
def test_each_declared_truncate_guard_independently_refuses_empty_table(conn, table):
    # Empty tables have no row guards to mask a missing statement trigger.
    # Disable only the neighbour's guard so CASCADE cannot mask this one either.
    neighbour = ('issued_forecast_outcome' if table == 'issued_forecast' else 'issued_forecast')
    conn.execute(f'ALTER TABLE {neighbour} DISABLE TRIGGER USER')
    with pytest.raises(psycopg.errors.ObjectNotInPrerequisiteState) as refused:
        with conn.transaction():
            conn.execute(f'TRUNCATE {table} CASCADE')
    assert f'on {table} refused' in str(refused.value)


@pytest.mark.parametrize('table,column,change', [
    ('issued_forecast', 'delivered_statement', "point_functional = 'midpoint'"),
    ('issued_forecast_outcome', 'observation', "observed_at = observed_at + interval '1 day'"),
])
def test_guard_migration_repairs_narrowed_update_triggers_without_rewriting_history(conn, table, column, change):
    insert(conn)
    outcome(conn)
    before = [conn.execute(f'SELECT to_jsonb(t) FROM {name} t').fetchall()
              for name in ('issued_forecast', 'issued_forecast_outcome')]
    trigger = f'{table}_immutable_rows'
    conn.execute(f'DROP TRIGGER {trigger} ON {table}')
    conn.execute(f'CREATE TRIGGER {trigger} BEFORE UPDATE OF {column} OR DELETE ON {table} '
                 'FOR EACH ROW EXECUTE FUNCTION public.issued_forecast_refuse_mutation()')
    # Simulate an installed narrow trigger; the additive guard must repair it.
    # 1351 alone uses IF NOT EXISTS and demonstrably leaves this drift intact.
    for migration in [MIGRATION, FINITE_INTERVALS, *GUARDS]:
        conn.execute(migration.read_text())
    for guard in GUARDS:  # Reapplication must be safe with delivered rows present.
        conn.execute(guard.read_text())
    with pytest.raises(psycopg.errors.ObjectNotInPrerequisiteState):
        with conn.transaction():
            conn.execute(f'UPDATE {table} SET {change}')
    after = [conn.execute(f'SELECT to_jsonb(t) FROM {name} t').fetchall()
             for name in ('issued_forecast', 'issued_forecast_outcome')]
    assert after == before
