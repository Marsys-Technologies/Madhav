"""
test_l0_ephemeris_queries_node_pin.py — NODE-SERIES step 1 (SS N-68/N-69), PR A: L0 readers S1-S7, S9, S11.

`ephemeris_daily` stores the TRUE node for Rahu/Ketu (node_mode='true'; the seven other bodies carry
node_mode NULL). L0 will gain a second, MEAN, row set. This suite proves, against REAL SQL executed on an
in-memory SQLite table (the SQL is the code under test; no mocked cursor that ignores it):

  1. GOLDEN EQUIVALENCE — on today's TRUE-only table the pinned reader in `brahmagyan.l0_ephemeris_queries`
     returns exactly what the legacy unpinned reader in `brahmagyan.l0_ephemeris` returns (S1-S7); the two
     routes edited in place (S9 /all_bodies_range, S11 /native_lifetime_meta) return the golden values.
  2. THE PIN BITES — with a synthetic second ('mean') Rahu/Ketu row set beside every TRUE one, the pinned
     readers return the SAME result as without it, while the legacy unpinned read does NOT (duplicates,
     Rahu-vs-Rahu "conjunctions", doubled retrograde days, shifted counts): a negative control that proves
     the fixture would have caught the defect.
  3. LOUD REFUSAL — two rows for one (node body, date) under the pin raise `NodeSeriesError` (HTTP 500 on
     the routes); `require_node_rows` raises on 0 rows, on a hole in the dates, and on 2 rows.
  4. EVERY statement that reads `ephemeris_daily` for a node-capable body carries `NODE_SERIES_PREDICATE`.

No database, no network. SQLite is used only as a SQL engine; the adapter below rewrites psycopg2 `%s` and
`= ANY(%s)` to SQLite syntax and converts ISO-date strings back to `datetime.date`.
"""
from __future__ import annotations

import copy
import re
import sqlite3
from datetime import date, datetime

import pytest

from brahmagyan import ephemeris_routes as routes
from brahmagyan import l0_ephemeris as legacy
from brahmagyan import l0_ephemeris_queries as pinned
from services.w2g.node_series import NODE_SERIES_PREDICATE, NodeSeriesError

DATES = [date(2026, 8, 14), date(2026, 8, 15), date(2026, 8, 16)]
BODIES = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
# tropical longitudes (deg) per body on day 0; +speed per day.  TRUE Rahu/Ketu are exactly 180 apart.
TRUE_LON = {"Sun": 140.0, "Moon": 10.0, "Mars": 200.0, "Mercury": 150.0, "Jupiter": 60.0,
            "Venus": 188.5, "Saturn": 20.0, "Rahu": 330.0, "Ketu": 150.0}
SPEED = {"Sun": 0.96, "Moon": 13.0, "Mars": 0.7, "Mercury": 1.2, "Jupiter": 0.1, "Venus": 1.18,
         "Saturn": -0.05, "Rahu": -0.053, "Ketu": 0.053}      # TRUE Ketu speed is stored inverted (F-L0-08)
CITATION = "pyswisseph + Swiss Ephemeris .se1"

COLUMNS = ("date", "body", "ayanamsha_id", "node_mode", "tropical_longitude", "latitude", "speed_dps",
           "is_retrograde", "sign_number", "degree_in_sign", "nakshatra_number", "source_citation", "computed_at")


def _row(day: date, i: int, body: str, lon: float, speed: float, node_mode, retro: bool | None = None):
    lon = (lon + speed * i) % 360.0
    return (day.isoformat(), body, "tropical", node_mode, lon, 0.0, speed,
            int(speed < 0 if retro is None else retro), int(lon // 30) + 1, lon % 30.0, int(lon / (360 / 27)) + 1,
            CITATION, "2026-09-01T00:00:00+00:00")


def true_rows():
    out = []
    for i, d in enumerate(DATES):
        for b in BODIES:
            out.append(_row(d, i, b, TRUE_LON[b], SPEED[b], "true" if b in ("Rahu", "Ketu") else None))
    # the two spot-check rows check_volume reads
    out.append(_row(date(1984, 2, 5), 0, "Sun", 315.87, 1.0, None))
    out.append(_row(date(2050, 1, 1), 0, "Saturn", 345.0, 0.05, None))
    return out


def mean_rows():
    """A second, MEAN, Rahu/Ketu row set beside every TRUE one (same date/body/ayanamsha, different node_mode):
    11 rows per date instead of 9. MEAN Ketu speed/flag = MEAN Rahu's (the design's corrected convention)."""
    out = []
    for i, d in enumerate(DATES):
        out.append(_row(d, i, "Rahu", TRUE_LON["Rahu"] + 0.3, -0.0529, "mean", retro=True))
        out.append(_row(d, i, "Ketu", TRUE_LON["Ketu"] + 0.3, -0.0529, "mean", retro=True))
    return out


class _Col:
    def __init__(self, name):
        self.name = name


_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _to_param(v):
    if isinstance(v, (date, datetime)):
        return v.isoformat()
    return v


class _Cursor:
    def __init__(self, conn):
        self._conn = conn
        self._cur = conn._db.cursor()
        self.description = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=()):
        self._conn.executed.append(sql)
        params = list(params or [])
        it = iter(params)
        out_params: list = []

        def sub(m):
            v = next(it)
            if m.group(1):                                    # = ANY(%s)  ->  IN (?, ?, ...)
                out_params.extend(_to_param(x) for x in v)
                return "IN (" + ",".join("?" * len(v)) + ")"
            out_params.append(_to_param(v))
            return "?"

        sql2 = re.sub(r"(=\s*ANY\(%s\))|%s", sub, sql)
        self._cur.execute(sql2, out_params)
        self.description = [_Col(d[0]) for d in (self._cur.description or [])]

    def _conv(self, row):
        return tuple(date.fromisoformat(v) if isinstance(v, str) and _ISO.match(v) else v for v in row)

    def fetchall(self):
        return [self._conv(r) for r in self._cur.fetchall()]

    def fetchone(self):
        r = self._cur.fetchone()
        return None if r is None else self._conv(r)


class FakePg:
    """A psycopg2-shaped connection over SQLite. No unique key on purpose (the duplicate-under-pin test inserts one)."""

    def __init__(self, rows):
        self._db = sqlite3.connect(":memory:")
        self._db.execute(f"CREATE TABLE ephemeris_daily ({', '.join(COLUMNS)})")
        self._db.executemany(f"INSERT INTO ephemeris_daily VALUES ({','.join('?' * len(COLUMNS))})", rows)
        self.executed: list[str] = []
        self.closed = False

    def cursor(self):
        return _Cursor(self)

    def close(self):
        self.closed = True


@pytest.fixture
def true_only():
    return FakePg(true_rows())


@pytest.fixture
def with_mean():
    return FakePg(true_rows() + mean_rows())


@pytest.fixture
def dup_true_rahu():
    """Corrupt table: TWO rows for (Rahu, 2026-08-15) with node_mode='true' (the unique key would forbid it)."""
    extra = [_row(DATES[1], 1, "Rahu", TRUE_LON["Rahu"] + 5.0, -0.053, "true")]
    return FakePg(true_rows() + extra)


def _scrub(x):
    """Drop volatile timestamps so two calls can be compared."""
    x = copy.deepcopy(x)
    if isinstance(x, dict):
        return {k: _scrub(v) for k, v in x.items() if k != "computed_at"}
    if isinstance(x, list):
        return [_scrub(v) for v in x]
    return x


# (name, call(module, conn)) for the seven readers moved to the pinned module
READERS = {
    "S1 query_planet_position(all)": lambda m, c: m.query_planet_position("2026-08-15", conn=c),
    "S1 query_planet_position(Rahu)": lambda m, c: m.query_planet_position("2026-08-15", planet="Rahu", conn=c),
    "S1 query_planet_position(Ketu,tropical)": lambda m, c: m.query_planet_position("2026-08-15", planet="Ketu", ayanamsha_id="tropical", conn=c),
    "S2 query_planet_transit(Rahu)": lambda m, c: m.query_planet_transit("Rahu", "2026-08-14", "2026-08-16", conn=c),
    "S2 query_planet_transit(Ketu,sign)": lambda m, c: m.query_planet_transit("Ketu", "2026-08-14", "2026-08-16", sign_number=5, ayanamsha_id="tropical", conn=c),
    "S2 query_planet_transit(Venus)": lambda m, c: m.query_planet_transit("Venus", "2026-08-14", "2026-08-16", conn=c),
    "S3 query_aspects_at_time": lambda m, c: m.query_aspects_at_time("2026-08-15", orb_degrees=1.0, conn=c),
    "S3 query_aspects_at_time(10deg)": lambda m, c: m.query_aspects_at_time("2026-08-15", orb_degrees=10.0, ayanamsha_id="tropical", conn=c),
    "S4 query_retrograde_periods(Rahu)": lambda m, c: m.query_retrograde_periods("Rahu", "2026-08-14", "2026-08-16", conn=c),
    "S4 query_retrograde_periods(Saturn)": lambda m, c: m.query_retrograde_periods("Saturn", "2026-08-14", "2026-08-16", conn=c),
    "S5 get_ephemeris_cache_native_lifetime": lambda m, c: m.get_ephemeris_cache_native_lifetime(conn=c),
    "S6 query_ephemeris(all)": lambda m, c: m.query_ephemeris(conn=c, limit=100),
    "S6 query_ephemeris(Rahu,Ketu)": lambda m, c: m.query_ephemeris(conn=c, bodies=["Rahu", "Ketu"], limit=100),
    "S6 query_ephemeris(window,limit)": lambda m, c: m.query_ephemeris(conn=c, date_start=date(2026, 8, 14), date_end=date(2026, 8, 15), limit=10),
    "S7 check_volume": lambda m, c: m.check_volume(conn=c),
}
# readers whose result is expected to CHANGE under the legacy (unpinned) read once a mean set exists
NODE_SENSITIVE = [k for k in READERS if "Venus" not in k and "Saturn" not in k]


@pytest.mark.parametrize("name", list(READERS))
def test_golden_pinned_equals_legacy_on_the_true_only_table(name, true_only):
    call = READERS[name]
    old = _scrub(call(legacy, FakePg(true_rows())))
    new = _scrub(call(pinned, true_only))
    assert old["ok"] is True if "ok" in old else True
    assert new == old, name


@pytest.mark.parametrize("name", list(READERS))
def test_pinned_ignores_the_mean_series(name, true_only, with_mean):
    call = READERS[name]
    assert _scrub(call(pinned, with_mean)) == _scrub(call(pinned, true_only)), name


@pytest.mark.parametrize("name", NODE_SENSITIVE)
def test_negative_control_the_legacy_unpinned_read_does_change_with_a_mean_series(name, true_only, with_mean):
    """Without this the two tests above could pass on a fixture that never exercises the defect."""
    call = READERS[name]
    assert _scrub(call(legacy, with_mean)) != _scrub(call(legacy, true_only)), name


def test_legacy_defects_are_the_documented_ones(true_only, with_mean):
    """The concrete symptoms in REVIEW_OURS_READERS_STEP0 (S1, S2, S3, S4), reproduced on the legacy reader."""
    pos = legacy.query_planet_position("2026-08-15", conn=with_mean)
    assert pos["count"] == 11 and [p["body"] for p in pos["positions"]].count("Rahu") == 2          # S1 11 rows, 2 Rahu
    tr = legacy.query_planet_transit("Rahu", "2026-08-14", "2026-08-16", conn=with_mean)
    assert tr["count"] == 6                                                                         # S2 each day twice
    asp = legacy.query_aspects_at_time("2026-08-15", orb_degrees=1.0, ayanamsha_id="tropical", conn=with_mean)
    assert any(a["body1"] == "Rahu" and a["body2"] == "Rahu" and a["aspect"] == "conjunction" for a in asp["aspects"])  # S3
    rg = legacy.query_retrograde_periods("Ketu", "2026-08-14", "2026-08-16", conn=with_mean)
    assert rg["total_days_in_window"] == 6                                                           # S4 doubled
    # the pinned ones: one row per (body, date)
    assert pinned.query_planet_position("2026-08-15", conn=with_mean)["count"] == 9
    assert pinned.query_planet_transit("Rahu", "2026-08-14", "2026-08-16", conn=with_mean)["count"] == 3
    assert not any(a["body1"] == a["body2"] for a in
                   pinned.query_aspects_at_time("2026-08-15", orb_degrees=1.0, ayanamsha_id="tropical", conn=with_mean)["aspects"])
    assert pinned.query_retrograde_periods("Ketu", "2026-08-14", "2026-08-16", conn=with_mean)["total_days_in_window"] == 3


def test_a_limit_is_not_consumed_twice_as_fast(with_mean):
    """S2/S6: the LIMIT window must hold 9 bodies per date, not 11."""
    got = pinned.query_ephemeris(conn=with_mean, date_start=date(2026, 8, 14), date_end=date(2026, 8, 14), limit=9)
    assert [r["body"] for r in got["rows"]] == sorted(BODIES)           # all nine, once each, in body order
    legacy_got = legacy.query_ephemeris(conn=with_mean, date_start=date(2026, 8, 14), date_end=date(2026, 8, 14), limit=9)
    assert [r["body"] for r in legacy_got["rows"]] != sorted(BODIES)    # the legacy read spends its LIMIT on duplicates


def test_check_volume_counts_the_pinned_series_so_the_floor_keeps_its_meaning(true_only, with_mean):
    base = pinned.check_volume(conn=true_only)
    assert base["actual_rows"] == len(true_rows())
    assert pinned.check_volume(conn=with_mean)["actual_rows"] == base["actual_rows"]
    assert legacy.check_volume(conn=with_mean)["actual_rows"] == base["actual_rows"] + 6   # the legacy count drifts
    assert base["floor"] == pinned.VOLUME_FLOOR == 825_084


# ---------------------------------------------------------------- empty results keep today's behaviour
@pytest.mark.parametrize("call", [
    lambda m, c: m.query_planet_position("1850-01-01", planet="Rahu", conn=c),
    lambda m, c: m.query_planet_transit("Ketu", "1850-01-01", "1850-01-05", conn=c),
    lambda m, c: m.query_aspects_at_time("1850-01-01", conn=c),
    lambda m, c: m.query_retrograde_periods("Rahu", "1850-01-01", "1850-01-05", conn=c),
    lambda m, c: m.query_ephemeris(conn=c, date_start=date(1850, 1, 1), date_end=date(1850, 1, 5), bodies=["Rahu"]),
])
def test_served_readers_keep_an_honest_empty_result_on_zero_rows(call, true_only):
    old = _scrub(call(legacy, FakePg(true_rows())))
    new = _scrub(call(pinned, true_only))
    assert new == old and new["ok"] is True
    assert new.get("count", new.get("station_count", 0)) == 0


# ---------------------------------------------------------------- loud refusal on 2 rows under the pin
@pytest.mark.parametrize("name", [k for k in READERS if k.split()[0] in ("S1", "S2", "S3", "S4", "S6")
                                  and "Venus" not in k and "Saturn" not in k and "limit" not in k
                                  and not (k.endswith("(Ketu,tropical)") or k.endswith("(Ketu,sign)"))])
def test_two_rows_for_a_node_under_the_pin_raise_instead_of_merging(name, dup_true_rahu):
    # the duplicate is a (Rahu, 2026-08-15) row, so only reads that can see Rahu on that date are parametrized
    call = READERS[name]
    with pytest.raises(NodeSeriesError, match="ambiguous"):
        call(pinned, dup_true_rahu)


# ---------------------------------------------------------------- require_node_rows (the zero-row helper)
def _r(body, d):
    return {"body": body, "date": d}


def test_require_node_rows_passes_on_a_complete_series():
    rows = [_r(b, d) for b in ("Rahu", "Ketu") for d in DATES] + [_r("Sun", DATES[0])]
    pinned.require_node_rows(rows, context="t", dates=DATES)
    pinned.require_node_rows(rows, context="t", bodies=("Rahu",))


def test_require_node_rows_refuses_zero_rows_for_a_requested_node():
    with pytest.raises(NodeSeriesError, match="absent"):
        pinned.require_node_rows([_r("Sun", DATES[0])], context="t")
    with pytest.raises(NodeSeriesError, match="Ketu"):
        pinned.require_node_rows([_r("Rahu", DATES[0])], context="t")
    with pytest.raises(NodeSeriesError):
        pinned.require_node_rows([], context="t", bodies=("Rahu",))


def test_require_node_rows_refuses_a_hole_in_the_dates():
    rows = [_r("Rahu", DATES[0]), _r("Rahu", DATES[2]), _r("Ketu", DATES[0]), _r("Ketu", DATES[1]), _r("Ketu", DATES[2])]
    with pytest.raises(NodeSeriesError, match="hole"):
        pinned.require_node_rows(rows, context="t", dates=DATES)


def test_require_node_rows_refuses_two_rows_and_accepts_positional_rows():
    with pytest.raises(NodeSeriesError, match="ambiguous"):
        pinned.require_node_rows([_r("Rahu", DATES[0]), _r("Rahu", DATES[0]), _r("Ketu", DATES[0])], context="t")
    pinned.require_node_rows([("Rahu", DATES[0], 1.0), ("Ketu", DATES[0], 2.0)], context="t", dates=[DATES[0]])


# ---------------------------------------------------------------- routes S9 and S11 (edited in place)
@pytest.fixture
def route_db(monkeypatch):
    import psycopg2

    holder = {}
    monkeypatch.setenv("DATABASE_URL", "postgresql://fake")

    def connect(_url):
        return holder["conn"]

    monkeypatch.setattr(psycopg2, "connect", connect)
    return holder


def _all_bodies(holder, rows, **kw):
    holder["conn"] = FakePg(rows)
    kw.setdefault("ayanamsha_id", "tropical")        # a direct call does not resolve FastAPI Query() defaults
    kw.setdefault("count_only", False)
    return _scrub(routes.get_all_bodies_range("2026-08-14", "2026-08-16", **kw)), holder["conn"]


def test_s9_all_bodies_range_golden_and_pinned(route_db):
    base, c1 = _all_bodies(route_db, true_rows(), count_only=False, ayanamsha_id="tropical")
    assert base["ok"] is True and base["count"] == 27                                    # 3 days x 9 bodies
    assert [(r["date"], r["body"]) for r in base["rows"]] == [(d.isoformat(), b) for d in DATES for b in sorted(BODIES)]
    with_mean, c2 = _all_bodies(route_db, true_rows() + mean_rows(), count_only=False, ayanamsha_id="tropical")
    assert with_mean == base                                                              # the pin ignores the mean set
    sid, _ = _all_bodies(route_db, true_rows() + mean_rows(), count_only=False, ayanamsha_id="lahiri_chitrapaksha")
    assert sid["count"] == 27 and all(r["body"] for r in sid["rows"])
    cnt, _ = _all_bodies(route_db, true_rows(), count_only=True)
    cnt_mean, _ = _all_bodies(route_db, true_rows() + mean_rows(), count_only=True)
    assert cnt["count"] == 27 and cnt_mean == cnt


def test_s9_negative_control_the_pre_pin_sql_would_have_returned_33_rows(route_db):
    unpinned = ("SELECT date, body FROM ephemeris_daily WHERE date >= %s AND date <= %s AND ayanamsha_id = %s "
                "ORDER BY date, body LIMIT 10000")
    cur = FakePg(true_rows() + mean_rows()).cursor()
    cur.execute(unpinned, ("2026-08-14", "2026-08-16", "tropical"))
    assert len(cur.fetchall()) == 33


def test_s9_two_node_rows_for_a_date_is_a_loud_500_not_a_merge(route_db):
    from fastapi import HTTPException

    route_db["conn"] = FakePg(true_rows() + [_row(DATES[1], 1, "Ketu", 1.0, 0.05, "true")])
    with pytest.raises(HTTPException) as ei:
        routes.get_all_bodies_range("2026-08-14", "2026-08-16", count_only=False, ayanamsha_id="tropical")
    assert ei.value.status_code == 500 and "ambiguous" in str(ei.value.detail)


def test_s11_native_lifetime_meta_counts_the_pinned_series(route_db):
    route_db["conn"] = FakePg(true_rows())
    base = _scrub(routes.get_native_lifetime_meta(start_date="2026-01-01", end_date="2026-12-31", count_only=False))
    route_db["conn"] = FakePg(true_rows() + mean_rows())
    with_mean = _scrub(routes.get_native_lifetime_meta(start_date="2026-01-01", end_date="2026-12-31", count_only=False))
    assert base["coverage"]["total_rows"] == 27 and base["coverage"]["body_count"] == 9 and base["coverage"]["day_count"] == 3
    assert with_mean == base
    # served numbers are deliberately untouched in step 1 (stale constant included)
    assert base["coverage"]["expected_rows"] == 157266


# ---------------------------------------------------------------- every node-capable read carries the pin
def test_every_statement_reading_ephemeris_daily_for_node_capable_bodies_is_pinned(with_mean):
    for name, call in READERS.items():
        conn = FakePg(true_rows())
        call(pinned, conn)
        node_reads = [s for s in conn.executed if "ephemeris_daily" in s and "body = 'Sun'" not in s and "body = 'Saturn'" not in s]
        assert node_reads, name
        for sql in node_reads:
            assert re.sub(r"\s+", " ", NODE_SERIES_PREDICATE) in re.sub(r"\s+", " ", sql), f"{name}: unpinned SQL: {sql[:80]}"


def test_the_predicate_is_pravahas_null_safe_one():
    assert NODE_SERIES_PREDICATE == "(body NOT IN ('Rahu', 'Ketu') OR node_mode = 'true')"
    assert pinned.NODE_SERIES_PREDICATE is NODE_SERIES_PREDICATE
