"""Step 1 of the node-series change (steward M20261001T215732-f156 / M20261001T215759-56f5;
census: Suvarṇa SS `census_ephemeris_nodes.md`): every Gochara-family reader of
`ephemeris_daily` pins the Rahu/Ketu series to `node_mode='true'`, NULL-safely, and is loud
on an ambiguous series; `ka_moorti_nirnaya` never refines a TRUE-series root against the
kernel's MEAN objective.

Three layers, none of which re-implements the rule it checks:

  * REAL PostgreSQL (a throwaway database this module creates and drops; NOT_RUN — never a
    fallback to another DSN — when no disposable server is reachable): the PRODUCTION readers
    run against an `ephemeris_daily` carrying the TRUE series AND a decoy MEAN series whose
    longitudes differ on every date and whose retrograde flag is set on every date. A reader
    that does not pin reads the wrong longitude, doubles a date, or unions retrograde days.
  * The kernel branch, through the real `_build_kernel_arcs` / `find_boundary_roots`; only the
    single Swiss seam (`calc_sidereal_lon`) is replaced, by a MEAN-node body.
  * Recorded SQL: the statements production code actually issues, captured by the QueryFn.
"""
from __future__ import annotations

import os
import sys
import uuid
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import psycopg
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from _disposable_db_guard import (  # noqa: E402
    RefusedError,
    assert_disposable_connection,
    validate_disposable_dsn,
)

from services.gochara_kernel import contacts as kernel_contacts
from services.gochara_kernel.overlays import date_to_jd
from services.ka_moorti_nirnaya import writer as moorti_writer
from services.ka_vedha_gochara import writer as vedha_writer
from services.w2g.node_series import (
    NODE_CONVENTION_MISMATCH_REASON,
    NODE_SERIES_PREDICATE,
    NodeSeriesError,
    assert_one_row_per_date,
)

MAINT_DSN = os.environ.get(
    "NODE_PIN_MAINT_DSN", "postgresql://wp6:local@localhost:55434/postgres")

DAY0 = date(2026, 11, 19)
N_DAYS = 20
RETRO_DAYS_TRUE = {3, 4}          # the TRUE node is retrograde on these days only
DECOY_OFFSET = 97.0               # the decoy MEAN longitude = TRUE + 97° on every date


def _true_lon(body: str, i: int) -> float:
    return {"Sun": 280.0 + i, "Rahu": 100.0 - 0.053 * i, "Ketu": 280.0 - 0.053 * i}[body]


def _day(i: int) -> date:
    return DAY0 + timedelta(days=i)


# ── real PostgreSQL ──────────────────────────────────────────────────────────

_DDL = """
CREATE TABLE ephemeris_daily (
  date DATE NOT NULL, body TEXT NOT NULL, ayanamsha_id TEXT NOT NULL,
  tropical_longitude NUMERIC(9,6) NOT NULL,           -- the real column types (ws2_l0_ephemeris.sql)
  speed_dps NUMERIC(10,7) NOT NULL DEFAULT 0.0,
  is_retrograde BOOLEAN NOT NULL DEFAULT FALSE,
  sign_number SMALLINT GENERATED ALWAYS AS (FLOOR(tropical_longitude / 30)::SMALLINT + 1) STORED,
  nakshatra_number SMALLINT GENERATED ALWAYS AS
    (FLOOR(tropical_longitude / (360.0/27))::SMALLINT + 1) STORED,
  node_mode TEXT,
  UNIQUE NULLS NOT DISTINCT (date, body, ayanamsha_id, node_mode)
);
CREATE TABLE bg_gochara_arcs (
  substrate_version TEXT NOT NULL, body TEXT NOT NULL, arc_index INT NOT NULL,
  start_jd DOUBLE PRECISION NOT NULL, end_jd DOUBLE PRECISION NOT NULL,
  start_lon_unwrapped_deg DOUBLE PRECISION NOT NULL,
  end_lon_unwrapped_deg DOUBLE PRECISION NOT NULL,
  direction INT NOT NULL, wrap_index INT NOT NULL
);
"""

_INSERT = (
    "INSERT INTO ephemeris_daily (date, body, ayanamsha_id, tropical_longitude, speed_dps,"
    " is_retrograde, node_mode) VALUES (%s,%s,'tropical',%s,%s,%s,%s)"
)


def _seed(cur) -> None:
    for i in range(N_DAYS):
        cur.execute(_INSERT, (_day(i), "Sun", _true_lon("Sun", i), 1.0, False, None))
        for body in ("Rahu", "Ketu"):
            lon = _true_lon(body, i)
            cur.execute(_INSERT, (_day(i), body, lon, -0.05, i in RETRO_DAYS_TRUE, "true"))
            cur.execute(_INSERT, (_day(i), body, (lon + DECOY_OFFSET) % 360.0, -0.05, True, "mean"))


@pytest.fixture
def node_db():
    """A database THIS fixture creates and drops (disposable-server rule: it refuses to run
    anywhere else). NOT_RUN when the maintenance server is unreachable."""
    from ._disposable_db_guard import check_admin_dsn, guarded_admin_connect
    check_admin_dsn(MAINT_DSN)          # a hostile / multi-host / non-loopback DSN is a configuration ERROR (was: first-host-only urlsplit)
    parts = urlsplit(MAINT_DSN)
    try:
        maint = guarded_admin_connect(MAINT_DSN, autocommit=True, connect_timeout=3)
    except psycopg.OperationalError as exc:
        pytest.skip(f"NOT_RUN: disposable PostgreSQL unreachable ({exc.__class__.__name__})")
    name = f"nodepin_{uuid.uuid4().hex[:12]}"
    maint.execute(f'CREATE DATABASE "{name}"')
    dsn = urlunsplit(parts._replace(path="/" + name))
    conn = psycopg.connect(dsn, autocommit=True)
    assert_disposable_connection(conn, name)
    try:
        conn.execute(_DDL)
        _seed(conn.cursor())
        yield conn
    finally:
        conn.close()
        maint.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        maint.close()


def _make_pinned_series_ambiguous(conn, day, body, *, retro=False) -> None:
    """Model the state the pin must refuse: two `node_mode='true'` rows for one date. The
    live unique key today is (date, body, ayanamsha_id) — step 2 widens it — so the fixture's
    key is dropped here to let the second row in."""
    name = conn.execute(
        "SELECT conname FROM pg_constraint WHERE conrelid = 'ephemeris_daily'::regclass"
        " AND contype = 'u'").fetchone()[0]
    conn.execute(f'ALTER TABLE ephemeris_daily DROP CONSTRAINT "{name}"')
    conn.execute(_INSERT, (day, body, 11.0, -0.05, retro, "true"))


def test_the_fixture_really_carries_two_node_series(node_db):
    rows = node_db.execute(
        "SELECT node_mode, count(*) FROM ephemeris_daily WHERE body='Rahu' GROUP BY 1 ORDER BY 1"
    ).fetchall()
    assert rows == [("mean", N_DAYS), ("true", N_DAYS)]
    assert node_db.execute(
        "SELECT count(*) FROM ephemeris_daily WHERE body='Sun' AND node_mode IS NULL"
    ).fetchone()[0] == N_DAYS


# P5 / P6 ─ the moorti and vedha daily-longitude readers

@pytest.mark.parametrize("module", [moorti_writer, vedha_writer], ids=["moorti", "vedha"])
def test_p5_p6_daily_sidereal_reader_reads_only_the_true_series(node_db, module):
    bodies = ("Sun", "Rahu", "Ketu")
    got = module._fetch_daily_sidereal_by_body(
        node_db, _day(0), _day(N_DAYS - 1), 0.0, bodies)
    for body in bodies:
        assert [d for d, _ in got[body]] == [_day(i) for i in range(N_DAYS)], body
        assert [lon for _, lon in got[body]] == pytest.approx(
            [_true_lon(body, i) % 360.0 for i in range(N_DAYS)], abs=1e-5), body


@pytest.mark.parametrize("module", [moorti_writer, vedha_writer], ids=["moorti", "vedha"])
def test_p5_p6_a_duplicate_date_fails_loudly(node_db, module):
    _make_pinned_series_ambiguous(node_db, _day(1), "Rahu")
    with pytest.raises(NodeSeriesError, match="Rahu"):
        module._fetch_daily_sidereal_by_body(node_db, _day(0), _day(N_DAYS - 1), 0.0, ("Rahu",))


# P7 ─ vedha retrograde days (the worst silent one: TRUE and MEAN days were UNIONED)

def test_p7_retrograde_days_are_the_true_nodes_not_the_union_with_the_mean_nodes(node_db):
    retro = vedha_writer._fetch_retrograde_dates(
        node_db, _day(0), _day(N_DAYS - 1), ("Sun", "Rahu", "Ketu"))
    assert retro["Rahu"] == {_day(i) for i in RETRO_DAYS_TRUE}
    assert retro["Ketu"] == {_day(i) for i in RETRO_DAYS_TRUE}
    assert "Sun" not in retro            # never retrograde in the fixture — and not dropped by an error


def test_p7_a_duplicate_pinned_retrograde_row_fails_loudly(node_db):
    _make_pinned_series_ambiguous(node_db, _day(3), "Rahu", retro=True)
    with pytest.raises(NodeSeriesError, match="Rahu"):
        vedha_writer._fetch_retrograde_dates(node_db, _day(0), _day(N_DAYS - 1), ("Rahu",))


# ── recorded SQL: the statements production code actually issues ─────────────

def test_every_reader_statement_carries_the_null_safe_pin():
    statements = {
        "P5 moorti range": moorti_writer._FETCH_EPHEMERIS_RANGE_SQL,
        "P6 vedha range": vedha_writer._FETCH_EPHEMERIS_RANGE_SQL,
        "P7 vedha retrograde": vedha_writer._FETCH_RETROGRADE_SQL,
    }
    for name, sql in statements.items():
        assert NODE_SERIES_PREDICATE in sql, name
    assert NODE_SERIES_PREDICATE == "(body NOT IN ('Rahu', 'Ketu') OR node_mode = 'true')"
    # a bare `node_mode = 'true'` is the NULL trap
    assert "AND node_mode = 'true'" not in "".join(statements.values())


def test_assert_one_row_per_date_only_polices_the_node_bodies_and_accepts_both_row_shapes():
    assert_one_row_per_date(
        [{"body": "Sun", "date": 1}, {"body": "Sun", "date": 1}], context="x")   # key-enforced bodies
    assert_one_row_per_date([("Rahu", 1), ("Rahu", 2), ("Ketu", 1)], context="x")
    with pytest.raises(NodeSeriesError):
        assert_one_row_per_date([("Rahu", 1), ("Rahu", 1)], context="x")


# ── moorti: never refine a TRUE-series root against the kernel's MEAN objective ──

# Suvarṇa's failing root (steward M20261001T215759-56f5): sidereal 300.0000° Lahiri, root
# bracket JD 2461363.2257..2461374.1451 — the TRUE series crosses at 2461370.25, the kernel's
# MEAN objective at 2461380.5, OUTSIDE the bracket.
TRUE_CROSSING_JD = 2461370.25
MEAN_CROSSING_JD = 2461380.5
NODE_RATE = -0.053   # deg/day (retrograde)


def _true_series():
    return [(DAY0 + timedelta(days=i), 300.0 + NODE_RATE * (date_to_jd(DAY0 + timedelta(days=i)) - TRUE_CROSSING_JD))
            for i in range(12)]


class _MeanSwiss:
    """The single Swiss seam, as the MEAN node: crosses 300° at 2461380.5 and carries SWIEPH."""

    def __init__(self):
        self.calls: list[tuple[str, float]] = []

    def __call__(self, body, jd, ephe_path):
        self.calls.append((body, jd))
        return 300.0 + NODE_RATE * (jd - MEAN_CROSSING_JD), 2


def test_a_true_series_root_is_kept_unrefined_and_recorded_not_a_lost_bracket(monkeypatch):
    swiss = _MeanSwiss()
    monkeypatch.setattr(kernel_contacts, "calc_sidereal_lon", swiss)
    _idx, roots, solver = moorti_writer._build_kernel_arcs({"Rahu": _true_series()}, ("Rahu",))
    assert len(roots["Rahu"]) == 1
    root = roots["Rahu"][0]
    assert root.exact_jd == root.spline_exact_jd == pytest.approx(TRUE_CROSSING_JD, abs=1e-2)
    assert solver["Rahu"] == {
        "method": "spline_unrefined", "backend": "not_probed",
        "reason": "node_convention_mismatch(series=true,kernel=mean)",
    }
    assert solver["Rahu"]["reason"] == NODE_CONVENTION_MISMATCH_REASON
    assert swiss.calls == [], "Swiss must not be called at all for a mismatched-convention node body"
    notes = moorti_writer._solver_notes(solver)
    assert ("Rahu:spline_unrefined|not_probed|"
            "node_convention_mismatch(series=true,kernel=mean)") in notes
    assert "ingress_solver_node_convention_unrefined=1" in notes
    assert "ingress_solver_degraded=0" in notes      # a different reason from a backend gap


def test_non_node_bodies_are_still_swiss_refined_beside_a_mismatched_node(monkeypatch):
    jd0 = date_to_jd(DAY0)

    def _calc(body, jd, ephe_path):
        if body == "Sun":
            return (299.5 + 0.98 * (jd - jd0)) % 360.0, 2
        return 300.0 + NODE_RATE * (jd - MEAN_CROSSING_JD), 2

    monkeypatch.setattr(kernel_contacts, "calc_sidereal_lon", _calc)
    sun = [(DAY0 + timedelta(days=i), (299.5 + 0.98 * i) % 360.0) for i in range(12)]
    _idx, roots, solver = moorti_writer._build_kernel_arcs(
        {"Sun": sun, "Rahu": _true_series()}, ("Sun", "Rahu"))
    assert solver["Sun"] == {"method": "swiss_refined", "backend": "swieph"}
    assert solver["Rahu"]["reason"] == NODE_CONVENTION_MISMATCH_REASON
    assert roots["Sun"] and roots["Rahu"]


def test_the_refinement_still_loses_its_bracket_if_a_true_root_is_refined_against_mean(monkeypatch):
    """The failure the branch exists to prevent, reproduced on the SAME inputs through the
    real contact solver — so the test above is not passing for an unrelated reason."""
    monkeypatch.setattr(kernel_contacts, "calc_sidereal_lon", _MeanSwiss())
    from services.gochara_kernel import arcs as kernel_arcs
    series = _true_series()
    jds = [date_to_jd(d) for d, _ in series]
    arc_index = kernel_arcs.build_arc_index("Rahu", jds, [lon for _, lon in series])
    with pytest.raises(ValueError, match="lost its bracket"):
        kernel_contacts.find_boundary_roots(arc_index, "Rahu", "sign_ingress", refine=True)
