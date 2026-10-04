"""test_e6_s1_stamp_lows.py -- the S1 and STAMP review LOWs that were test gaps (E6.1 follow-up, item 3). Tests only, plus a comment in asset_census.py.

S1: `allowed_literals` on the null convention exempts a declared literal from the fallback test, per text value / per array element / per JSON string leaf. Three corners were
untested: a NULL ELEMENT of a text array (a NULL element is itself a placeholder and must stay a fallback whatever else is allowed), a citext column (compared as text: the
type's case-insensitive equality must not widen the exemption), and enum columns / enum arrays (a label that is a placeholder word, exempted only by name).

STAMP: the sentinel bound of a write-time stamp column is "at or before epoch + 1 day". The PASS text names it; here the bound is pinned EXACTLY (the instant is a sentinel,
one microsecond later is a real time), on both timestamp types, and under every session TimeZone (the predicate compares in the column's own type and must not move with SET TIME ZONE).

Earned signal: each real-SQL reading has a mutation (the NULL guard removed, `<=` weakened to `<`, a bound of two days) that flips it, so the assertions can fail."""
from __future__ import annotations

import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
import test_e6_s1_null_convention as s1  # noqa: E402
import test_e6_s3_alias_ldgr as s3  # noqa: E402
import test_e6_stamp_columns as st  # noqa: E402
from _disposable_pg import disposable_pg  # noqa: E402,F401  (the session fixture)

PASS, FAIL = ac.PASS, ac.FAIL
BR = s1.BR


# ═════════════════════════ S1: allowed_literals corners ═════════════════════════

def _al(column, *values):
    return [dict(column=column, values=list(values), why="a row with nothing to say is stored as this word, a real value of the column")]


def _reading(monkeypatch, pg, setup, types, allowed=None):
    m = s1._mp_real(monkeypatch, pg, setup, "x_t", types, s1._gspec(allowed=allowed))
    return s1._cv(m), m[BR]["null_convention"]["convention"]


@pytest.mark.parametrize("ta, allowed, verdict", [
    ("ARRAY['none','t9']", ["none"], PASS),                         # control: the declared element is exempt (LOW3)
    ("ARRAY['none', NULL]", ["none"], FAIL),                        # a NULL element is a placeholder whatever else is allowed
    ("ARRAY[NULL, 't1']", ["none"], FAIL),
    ("ARRAY[NULL]::text[]", ["none"], FAIL),
    ("ARRAY['none', NULL]", ["none", "N/A"], FAIL),
    ("ARRAY['none','N/A']", ["none"], FAIL),                        # only the declared element is exempt, not its neighbour
    ("ARRAY[]::text[]", ["none"], FAIL),                            # the empty array is a fallback whatever is allowed
])
def test_REAL_SQL_a_null_element_of_a_text_array_stays_a_fallback_under_allowed_literals(monkeypatch, disposable_pg, ta, allowed, verdict):
    setup = s1._arr_setup("ARRAY[1]", "ARRAY[true]", "ARRAY[1]", ta)
    got, conv = _reading(monkeypatch, disposable_pg, setup, s1.ARR_TYPES, _al("ta", *allowed))
    assert got == verdict, (ta, allowed, conv)
    if verdict == FAIL:
        assert conv["fallbacks"] == {"ta": 1}


def test_REAL_SQL_a_null_json_leaf_stays_a_fallback_under_allowed_literals(monkeypatch, disposable_pg):
    setup = ["CREATE TEMP TABLE x_t (k text PRIMARY KEY, doc jsonb NOT NULL, w int NOT NULL) ON COMMIT DROP;",
             "INSERT INTO x_t VALUES ('a', '{\"s\":\"none\",\"t\":null}', 1), ('b', '{\"s\":\"x\"}', 2);"]
    types = {"k": "text", "doc": "jsonb", "w": "integer"}
    got, conv = _reading(monkeypatch, disposable_pg, setup, types, _al("doc", "none"))
    assert got == FAIL and conv["fallbacks"] == {"doc": 1}          # the allowed leaf "none" does not hide the JSON null beside it


def test_MUTATION_without_the_null_element_guard_a_null_element_would_read_as_clean(monkeypatch, disposable_pg):
    """`e.x NOT IN (lits)` is NULL for a NULL element, so the allowed-literals branch needs its explicit `e.x IS NULL OR` to keep the NULL element a fallback. Remove it and the
    SAME data reads PASS: the FAIL above is earned by that clause, not by luck."""
    setup = s1._arr_setup("ARRAY[1]", "ARRAY[true]", "ARRAY[1]", "ARRAY['none', NULL]")
    assert _reading(monkeypatch, disposable_pg, setup, s1.ARR_TYPES, _al("ta", "none"))[0] == FAIL
    real = ac._null_fallback_sql

    def broken(*a, **k):
        sql = real(*a, **k)
        return sql.replace("(e.x IS NULL OR e.x NOT IN", "(e.x NOT IN") if sql else sql                 # None (a column that cannot hold a fallback) passes through
    assert broken("ta", "array_text", False, ["none"]) != real("ta", "array_text", False, ["none"])    # the mutation really edits the predicate
    monkeypatch.setattr(ac, "_null_fallback_sql", broken)
    assert _reading(monkeypatch, disposable_pg, setup, s1.ARR_TYPES, _al("ta", "none"))[0] == PASS


def _citext_setup(rows):
    return ["CREATE EXTENSION IF NOT EXISTS citext;", "CREATE TEMP TABLE x_t (k text PRIMARY KEY, c citext, w int NOT NULL) ON COMMIT DROP;",
            "INSERT INTO x_t VALUES " + ", ".join(f"('{k}', {v}, {i})" for i, (k, v) in enumerate(rows, 1)) + ";"]


CITEXT_TYPES = {"k": "text", "c": "USER-DEFINED", "w": "integer"}


def _need_citext(pg, monkeypatch):
    s3._real(monkeypatch, pg, [])
    if not ac.psql("SELECT 1 FROM pg_available_extensions WHERE name = 'citext'"):
        pytest.skip("the citext extension is not installed in this PostgreSQL")


def test_REAL_SQL_citext_allowed_literals_are_compared_as_text_not_case_insensitively(monkeypatch, disposable_pg):
    _need_citext(disposable_pg, monkeypatch)
    rows = [("a", "'real'"), ("b", "'N/A'"), ("c", "'other'")]
    assert _reading(monkeypatch, disposable_pg, _citext_setup(rows), CITEXT_TYPES)[0] == FAIL                              # undeclared: the placeholder is a fallback
    got, conv = _reading(monkeypatch, disposable_pg, _citext_setup(rows), CITEXT_TYPES, _al("c", "N/A"))
    assert got == PASS and [a["column"] for a in conv["allowed_literals_in_force"]] == ["c"]                                # declared: exempt, and the exemption is in force
    # the stored case is what is compared: citext's case-insensitive '=' would have matched 'n/a', the cast to text does not (the declaration must say what is stored)
    assert _reading(monkeypatch, disposable_pg, _citext_setup(rows), CITEXT_TYPES, _al("c", "n/a"))[0] == FAIL
    assert _reading(monkeypatch, disposable_pg, _citext_setup(rows), CITEXT_TYPES, _al("c", "none"))[0] == FAIL            # another word exempts nothing


def test_REAL_SQL_citext_a_null_cell_is_not_a_fallback_and_an_allowed_literal_changes_nothing_for_it(monkeypatch, disposable_pg):
    _need_citext(disposable_pg, monkeypatch)
    rows = [("a", "NULL"), ("b", "'real'"), ("c", "'other'")]
    spec = s1._gspec([s1._nul("c", ["a"])], allowed=_al("c", "N/A"))
    s3._real(monkeypatch, disposable_pg, _citext_setup(rows))
    m = s1._mp_real(monkeypatch, disposable_pg, _citext_setup(rows), "x_t", CITEXT_TYPES, spec)
    assert s1._cv(m) != FAIL, m[BR]["null_convention"]["convention"]                                                      # a declared-nullable citext with its NULL on the declared key: no fallback


ENUM_TYPES = {"k": "text", "mood": "USER-DEFINED", "w": "integer"}


def _enum_setup(labels, rows):
    return [f"CREATE TYPE mood_t AS ENUM ({', '.join(repr(x) for x in labels)});",
            "CREATE TEMP TABLE x_t (k text PRIMARY KEY, mood mood_t, w int NOT NULL) ON COMMIT DROP;",
            "INSERT INTO x_t VALUES " + ", ".join(f"('{k}', '{v}', {i})" for i, (k, v) in enumerate(rows, 1)) + ";"]


def test_REAL_SQL_an_enum_label_that_is_a_placeholder_word_is_a_fallback_unless_declared(monkeypatch, disposable_pg):
    labels, rows = ("good", "none", "bad"), [("a", "good"), ("b", "none"), ("c", "bad")]
    setup = _enum_setup(labels, rows)
    got, conv = _reading(monkeypatch, disposable_pg, setup, ENUM_TYPES)
    assert got == FAIL and conv["fallbacks"] == {"mood": 1}
    got, conv = _reading(monkeypatch, disposable_pg, setup, ENUM_TYPES, _al("mood", "none"))
    assert got == PASS and [a["column"] for a in conv["allowed_literals_in_force"]] == ["mood"]                            # an enum is text-kind: the exemption takes effect
    assert _reading(monkeypatch, disposable_pg, setup, ENUM_TYPES, _al("mood", "good"))[0] == FAIL                         # exempting another label hides nothing
    both = _enum_setup(("good", "none", "N/A"), [("a", "good"), ("b", "none"), ("c", "N/A")])
    assert _reading(monkeypatch, disposable_pg, both, ENUM_TYPES, _al("mood", "none"))[0] == FAIL                           # two placeholder labels, one exempt: the other still fails


def test_REAL_SQL_an_enum_array_compares_per_element_under_allowed_literals(monkeypatch, disposable_pg):
    def setup(arr_b):
        return ["CREATE TYPE mood_t AS ENUM ('good', 'none', 'bad', 'N/A');",
                "CREATE TEMP TABLE x_t (k text PRIMARY KEY, moods mood_t[], w int NOT NULL) ON COMMIT DROP;",
                f"INSERT INTO x_t VALUES ('a', ARRAY['good']::mood_t[], 1), ('b', {arr_b}, 2), ('c', ARRAY['bad']::mood_t[], 3);"]
    types = {"k": "text", "moods": "ARRAY", "w": "integer"}
    assert _reading(monkeypatch, disposable_pg, setup("ARRAY['good','none']::mood_t[]"), types)[0] == FAIL
    assert _reading(monkeypatch, disposable_pg, setup("ARRAY['good','none']::mood_t[]"), types, _al("moods", "none"))[0] == PASS
    assert _reading(monkeypatch, disposable_pg, setup("ARRAY['none','N/A']::mood_t[]"), types, _al("moods", "none"))[0] == FAIL     # only the declared element
    assert _reading(monkeypatch, disposable_pg, setup("ARRAY['none',NULL]::mood_t[]"), types, _al("moods", "none"))[0] == FAIL      # a NULL element, again


# ═════════════════════════ STAMP: the bound, exactly ═════════════════════════

TYPES = {"timestamptz": ("timestamptz", "timestamp with time zone", "+00"), "timestamp": ("timestamp", "timestamp without time zone", "")}
BOUND, JUST_AFTER, JUST_BEFORE = "1970-01-02 00:00:00", "1970-01-02 00:00:00.000001", "1970-01-01 23:59:59.999999"
ZONES = ["UTC", "Pacific/Kiritimati", "Pacific/Pago_Pago", "Etc/GMT+12", "Etc/GMT-14", "Asia/Kolkata", "Asia/Kathmandu", "America/St_Johns", "America/Los_Angeles",
         "Europe/London", "Australia/Lord_Howe", "Pacific/Chatham"]


def _stamped(monkeypatch, pg, typ, value, zone=None):
    """The STAMP check on the latta fixture with created_at set to `value` on every row (the explicit +00 on timestamptz keeps the INSERTED instant independent of the zone: only the
    DETECTOR's reading may vary, and it must not)."""
    t, dt, off = TYPES[typ]
    setup = list(st._ts_setup(t))
    if zone:
        setup.append(f"SET LOCAL TIME ZONE '{zone}';")
    setup.append(f"UPDATE latta_t SET created_at = '{value}{off}'::{t};")
    return st._real_check(monkeypatch, pg, setup, types=dict(s1.REAL_TYPES, created_at=dt))


def _readings(monkeypatch, pg, typ, zone=None):
    out = {}
    for name, value in (("at", BOUND), ("after", JUST_AFTER), ("before", JUST_BEFORE)):
        r = _stamped(monkeypatch, pg, typ, value, zone)
        out[name] = (r["v"], r["convention"]["stamp_sentinels"])
    return out


EXPECTED = {"at": (FAIL, {"created_at": 8}), "after": (PASS, {}), "before": (FAIL, {"created_at": 8})}


@pytest.mark.parametrize("typ", ["timestamptz", "timestamp"])
def test_REAL_SQL_the_sentinel_bound_is_exactly_epoch_plus_one_day_inclusive(monkeypatch, disposable_pg, typ):
    assert _readings(monkeypatch, disposable_pg, typ) == EXPECTED     # 1970-01-02 00:00:00 IS a sentinel ("at or before"), one microsecond later is a real write time


@pytest.mark.parametrize("typ", ["timestamptz", "timestamp"])
def test_REAL_SQL_set_time_zone_never_moves_the_sentinel_bound(monkeypatch, disposable_pg, typ):
    """The predicate compares in the column's own type ('epoch'::timestamptz + interval '1 day'): for timestamptz the epoch is an instant, for timestamp a wall-clock value, so
    no session TimeZone may shift the boundary. Swept over zones at both ends of the offset range, half-hour and 45-minute zones, and DST / odd-history zones."""
    for zone in ZONES:
        assert _readings(monkeypatch, disposable_pg, typ, zone) == EXPECTED, zone


@pytest.mark.parametrize("typ", ["timestamptz", "timestamp"])
def test_REAL_SQL_the_infinities_are_sentinels_in_every_zone(monkeypatch, disposable_pg, typ):
    for zone in ("UTC", "Pacific/Kiritimati", "America/Los_Angeles"):
        for inf in ("infinity", "-infinity"):
            t, dt, _ = TYPES[typ]
            setup = list(st._ts_setup(t)) + [f"SET LOCAL TIME ZONE '{zone}';", f"UPDATE latta_t SET created_at = '{inf}'::{t};"]
            r = st._real_check(monkeypatch, disposable_pg, setup, types=dict(s1.REAL_TYPES, created_at=dt))
            assert r["v"] == FAIL and r["convention"]["stamp_sentinels"] == {"created_at": 8}, (zone, inf)


def test_the_pass_text_and_the_predicate_name_the_same_bound():
    """The text (PASS and FAIL) says 'at or before epoch + 1 day'; the predicate is `<= 'epoch'::<type> + interval '1 day'`. Both come from one fact: pin the pair so the wording
    and the SQL cannot drift apart."""
    sql = ac._null_stamp_sentinel_sql("c", "timestamptz")
    assert "<= 'epoch'::timestamptz + interval '1 day'" in sql and "= 'infinity'" in sql and "= '-infinity'" in sql
    assert "<= 'epoch'::timestamp + interval '1 day'" in ac._null_stamp_sentinel_sql("c", "timestamp")
    ok = st._grade()
    assert ok["v"] == PASS and "no infinity, -infinity or value at or before epoch + 1 day" in ok["measured"]
    bad = st._grade(stats=st.SSTATS(created_at=dict(sentinel=2)))
    assert bad["v"] == FAIL and "any value at or before epoch + 1 day" in bad["measured"]


@pytest.mark.parametrize("typ", ["timestamptz", "timestamp"])
def test_MUTATION_a_strict_less_than_or_a_wider_bound_changes_the_exact_readings(monkeypatch, disposable_pg, typ):
    """The exact-bound assertions are only worth their name if a different bound reads differently: `<` loses the instant itself, two days wrongly sentences one microsecond after."""
    assert _readings(monkeypatch, disposable_pg, typ) == EXPECTED
    real = ac._null_stamp_sentinel_sql
    monkeypatch.setattr(ac, "_null_stamp_sentinel_sql", lambda col, t: real(col, t).replace("<= 'epoch'", "< 'epoch'"))
    strict = _readings(monkeypatch, disposable_pg, typ)
    assert strict["at"] == (PASS, {}) and strict != EXPECTED
    monkeypatch.setattr(ac, "_null_stamp_sentinel_sql", lambda col, t: real(col, t).replace("interval '1 day'", "interval '2 days'"))
    wide = _readings(monkeypatch, disposable_pg, typ)
    assert wide["after"][0] == FAIL and wide != EXPECTED
