"""ga_vargas natural key must not collapse distinct rows (Nirmāṇa F-A2, Q-L1-01).

`chart_divisionals_unique_idx` was (chart_id, graha, ayanamsha_id, varga,
fact_category, fact_key) and both INSERTs ended `ON CONFLICT (...) DO NOTHING`
on that key. Rows that differ only in `fact_subject` therefore collapsed
silently, on every chart:

  varga_ashtakavarga           2,880 built per ayanamsha ->   240 stored (12 sign rows per graha x varga -> 1)
  varga_house_lord               360 built per ayanamsha ->   210 stored (a lord of two houses keeps one)
  varga_d30_lord_per_amsa         60 built per ayanamsha ->    10 stored (the L1 decision sheet's D30 "60 to 10")
  scope_cap (INVARIANT)            6 built per call       ->     2 stored (five floored bodies share one key)

These tests run the REAL row builders and the REAL SQL text against a fake
database that enforces uniqueness on exactly the columns the statement's own
`ON CONFLICT` clause names, so a regression to the six-column target (or an index
that no longer matches) makes them fail. No database is opened.
"""
from __future__ import annotations

import re
from typing import Any

import pytest

CHART = "482012f1-710e-4a25-994a-93821f5871aa"
BUILD = "11111111-1111-1111-1111-111111111111"
SEVEN = ("chart_id", "graha", "ayanamsha_id", "varga", "fact_category", "fact_key", "fact_subject")
SIX = SEVEN[:-1]


def _indexdef(cols: tuple[str, ...]) -> str:
    return (
        "CREATE UNIQUE INDEX chart_divisionals_unique_idx ON public.chart_divisionals "
        f"USING btree ({', '.join(cols)}) NULLS NOT DISTINCT"
    )


class _Result:
    def __init__(self, row: Any = None) -> None:
        self._row = row

    def fetchone(self) -> Any:
        return self._row


class FakeDB:
    """Just enough of a psycopg3 connection for ga_vargas, with a real unique index.

    `index_cols` is the live unique index; an INSERT whose ON CONFLICT target does
    not name exactly those columns fails the way PostgreSQL does.
    """

    def __init__(self, index_cols: tuple[str, ...] = SEVEN) -> None:
        self.index_cols = index_cols
        self.rows: dict[tuple, dict] = {}
        self.deletes = 0

    # -- connection surface -------------------------------------------------
    def execute(self, sql: str, params: Any = None) -> _Result:
        s = " ".join(sql.split())
        if "FROM pg_indexes" in s:
            return _Result({"indexdef": _indexdef(self.index_cols)})
        if s.startswith("SELECT COUNT(*) FROM chart_divisionals"):
            return _Result({"count": 0})
        if s.startswith("DELETE FROM chart_divisionals"):
            self._delete(s, params)
            return _Result()
        raise AssertionError(f"unexpected SQL: {s[:120]}")

    def cursor(self, **_kw: Any) -> "_Cursor":
        return _Cursor(self)

    # -- helpers --------------------------------------------------------------
    def _delete(self, s: str, params: Any) -> None:
        self.deletes += 1
        if "ayanamsha_id = 'INVARIANT'" in s:
            doomed = [k for k, r in self.rows.items()
                      if r["chart_id"] == params[0] and r["ayanamsha_id"] == "INVARIANT"]
        else:
            cid, vargas = params[0], set(params[1])
            ayas = set(params[2]) if len(params) > 2 else None
            doomed = [k for k, r in self.rows.items()
                      if r["chart_id"] == cid and r["varga"] in vargas
                      and (ayas is None or r["ayanamsha_id"] in ayas)]
        for k in doomed:
            del self.rows[k]

    def insert(self, sql: str, row: dict) -> int:
        target = re.search(r"ON CONFLICT \(([^)]*)\)", sql)
        assert target, "statement has no explicit ON CONFLICT target"
        cols = tuple(c.strip() for c in target.group(1).split(","))
        if cols != self.index_cols:
            raise RuntimeError(
                "there is no unique or exclusion constraint matching the ON CONFLICT specification"
            )
        key = tuple(row.get(c) for c in cols)
        if key in self.rows:
            return 0
        self.rows[key] = row
        return 1

    def count(self, category: str, ayanamsha: str | None = None) -> int:
        return sum(1 for r in self.rows.values()
                   if r["fact_category"] == category
                   and (ayanamsha is None or r["ayanamsha_id"] == ayanamsha))


class _Cursor:
    def __init__(self, db: FakeDB) -> None:
        self.db = db
        self.rowcount = 0

    def __enter__(self) -> "_Cursor":
        return self

    def __exit__(self, *_exc: object) -> None:
        return None

    def execute(self, sql: str, params: Any = None) -> None:
        if sql.startswith(("SAVEPOINT", "RELEASE", "ROLLBACK")):
            return
        self.rowcount = self.db.insert(sql, params)

    def executemany(self, sql: str, rows: Any) -> None:
        n = 0
        for r in list(rows):
            n += self.db.insert(sql, r)
        self.rowcount = n


def _w():
    from ga_writers import ga_vargas_writer as w
    return w


def _legal(rows: list[dict]) -> list[dict]:
    for r in rows:
        r.setdefault("verification_pass_status", "single")
    return rows


# --------------------------------------------------------------------------
# the key itself
# --------------------------------------------------------------------------

def test_conflict_targets_name_the_seven_column_key() -> None:
    w = _w()
    assert w.UNIQUE_KEY_COLUMNS == SEVEN
    for sql in (w._UPSERT_SQL, w._UPSERT_WITH_FACT_ID_SQL):
        m = re.search(r"ON CONFLICT \(([^)]*)\) DO NOTHING", sql)
        assert m, "both INSERTs need an explicit conflict target"
        assert tuple(c.strip() for c in m.group(1).split(",")) == SEVEN


# --------------------------------------------------------------------------
# the D30 case (the decision sheet's "60 to 10") and its two siblings
# --------------------------------------------------------------------------

def test_d30_lords_all_sixty_rows_land_per_ayanamsha() -> None:
    w = _w()
    rows = _legal(w._build_d30_lord_per_amsa_rows(CHART, "lahiri_chitrapaksha", BUILD, BUILD))
    assert len(rows) == 60

    db = FakeDB(SEVEN)
    stats = w.new_write_stats()
    landed = w._write_rows_batch(db, rows, set(), stats)
    assert landed == 60 and db.count("varga_d30_lord_per_amsa") == 60
    assert stats["collided"] == 0

    # the same rows on the pre-F-A2 six-column key collapse to the measured 10
    legacy = {tuple(r[c] for c in SIX) for r in rows}
    assert len(legacy) == 10


def test_house_lord_and_ashtakavarga_rows_all_land() -> None:
    w = _w()
    # D1 with a lagna and seven grahas is enough to exercise both builders
    varga_data = {b: {"sign_idx": i % 12, "degree_in_sign": 5.0 + i} for i, b in enumerate(w.CLASSICAL_BODIES)}
    hl = _legal(w._build_house_lord_occupant_rows(CHART, "lahiri_chitrapaksha", BUILD, 1, "D1", varga_data))
    av = _legal(w._build_ashtakavarga_rows(CHART, "lahiri_chitrapaksha", BUILD, 1, "D1", varga_data))
    lords = [r for r in hl if r["fact_category"] == "varga_house_lord"]
    assert len(lords) == 12 and len(av) == 96

    db = FakeDB(SEVEN)
    w._write_rows_batch(db, lords + av, set(), w.new_write_stats())
    assert db.count("varga_house_lord") == 12
    assert db.count("varga_ashtakavarga") == 96
    assert len({tuple(r[c] for c in SIX) for r in lords}) < 12
    assert len({tuple(r[c] for c in SIX) for r in av}) == 8


# --------------------------------------------------------------------------
# a full ayanamsha sub-step, end to end (real builders, real SQL, fake database)
# --------------------------------------------------------------------------

# bg_shashtiamsha_deities as read from production (suvarna_reader, 2026-10-02): 60 amsas, quality only,
# every deity_name NULL ("canonical-or-floor NULL"). k = kroora, s = soumya.
_REAL_D60_QUALITY = "kkssssskkkkksskkssssssssssssskkkkkksssskskkksssksskkssssssks"


def real_deity_cache() -> dict:
    return {i + 1: {"quality": "kroora" if c == "k" else "soumya", "deity_name": None}
            for i, c in enumerate(_REAL_D60_QUALITY)}


@pytest.fixture()
def _deities(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(_w(), "_SHASHTIAMSHA_CACHE", real_deity_cache())


@pytest.fixture()
def _karakas(monkeypatch: pytest.MonkeyPatch) -> None:
    """ga_vargas now INHERITS the karaka assignment from ga_sensitive's stored rows (ga_writers/_karaka_roles.py, #2984) and fails closed
    without them; the FakeDB stores no chart_facts, so supply a clean 8-rank assignment (this file tests the unique-key grain, not the karaka read)."""
    w = _w()
    monkeypatch.setattr(w, "_read_jaimini_karakas", lambda conn, chart_id, ayanamsha_id: dict(zip(
        w.JAIMINI_KARAKA_NAMES, ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu"))))


BIRTH = {"datetime_iso": "1984-02-05T10:43:00", "latitude_deg": 20.2961,
         "longitude_deg": 85.8245, "tz_offset_hours": 5.5}


def test_full_substep_stores_every_row_it_builds(_deities: None, _karakas: None) -> None:
    w = _w()
    db = FakeDB(SEVEN)
    s = w.build_ga_vargas(CHART, BUILD, conn=db, birth_params=BIRTH,
                          ayanamsha_subset=["lahiri_chitrapaksha"])
    assert s["status"] == "PASS"
    assert s["rows_collided"] == 0 and s["rows_db_skipped"] == 0 and s["rows_failed"] == 0
    assert s["rows_attempted"] == s["rows_landed"] == s["total_rows_written"] == len(db.rows)
    # the S-L1 acceptance numbers, per ayanamsha: 7,718 stored + 6 sentinels (7,724 attempted)
    assert s["rows_attempted"] == 7724
    assert sum(1 for r in db.rows.values() if r["ayanamsha_id"] != "INVARIANT") == 7718
    # the three collapsed families, at their intended grain
    assert db.count("varga_d30_lord_per_amsa", "lahiri_chitrapaksha") == 60
    assert db.count("varga_house_lord", "lahiri_chitrapaksha") == 12 * 30
    assert db.count("varga_ashtakavarga", "lahiri_chitrapaksha") == 96 * 30
    # the six scope-cap sentinels (D81 + five floored bodies) all survive
    assert db.count("scope_cap", "INVARIANT") == 6


def test_full_substep_on_the_old_key_loses_the_known_rows(_deities: None) -> None:
    """Documents the defect: an index on the six-column key is refused loudly."""
    w = _w()
    db = FakeDB(SIX)
    with pytest.raises(RuntimeError, match="F-A2"):
        w.build_ga_vargas(CHART, BUILD, conn=db, birth_params=BIRTH,
                          ayanamsha_subset=["lahiri_chitrapaksha"])
    assert db.rows == {}, "nothing may be written against a mismatched key grain"


# --------------------------------------------------------------------------
# collision detection and honest counts
# --------------------------------------------------------------------------

def _row(subject: str, **over: Any) -> dict:
    r = {
        "chart_id": CHART, "graha": "Mars", "ayanamsha_id": "lahiri_chitrapaksha",
        "varga": "D30", "fact_category": "varga_d30_lord_per_amsa", "fact_key": "Mars_0_5",
        "fact_subject": subject, "verification_pass_status": "single",
    }
    r.update(over)
    return r


def test_rows_differing_only_in_subject_both_land() -> None:
    w = _w()
    db = FakeDB(SEVEN)
    stats = w.new_write_stats()
    assert w._write_rows_batch(db, [_row("D30.S1"), _row("D30.S3")], set(), stats) == 2
    assert stats["collided"] == 0


def test_a_true_duplicate_key_is_counted_sampled_and_not_called_a_success() -> None:
    w = _w()
    db = FakeDB(SEVEN)
    stats = w.new_write_stats()
    landed = w._write_rows_batch(db, [_row("D30.S1"), _row("D30.S1", fact_value_text="x")], set(), stats)
    assert landed == 1, "only the row that landed may be counted"
    assert stats["attempted"] == 2 and stats["landed"] == 1
    assert stats["collided"] == 1 and stats["db_skipped"] == 0, "a colliding row is counted once, in collided"
    assert stats["collision_samples"][0][-1] == "D30.S1"


def test_a_collision_with_an_earlier_batch_of_the_same_run_is_detected() -> None:
    w = _w()
    db = FakeDB(SEVEN)
    stats = w.new_write_stats()
    cleared: set = set()
    w._write_rows_batch(db, [_row("D30.S1")], cleared, stats)
    w._write_rows_batch(db, [_row("D30.S1")], cleared, stats)
    assert stats["collided"] == 1 and stats["landed"] == 1 and stats["attempted"] == 2


class _BatchBroken(FakeDB):
    """executemany fails, so _write_rows_batch takes the per-row fallback path."""

    def cursor(self, **_kw: Any) -> "_Cursor":
        cur = super().cursor()

        def boom(sql: str, rows: Any) -> None:
            raise RuntimeError("batch refused")

        cur.executemany = boom  # type: ignore[method-assign]
        return cur


def test_per_row_path_counts_stored_rows_not_attempted_ones() -> None:
    """Mutants M2b/M5b: the per-row fallback once counted every attempted row as written."""
    w = _w()
    db = _BatchBroken(SEVEN)
    stats = w.new_write_stats()
    landed = w._write_rows_batch(db, [_row("A"), _row("A"), _row("B")], set(), stats)
    assert landed == 2, "the duplicate was skipped by the database: it did not land"
    assert (stats["attempted"], stats["landed"], stats["collided"], stats["db_skipped"], stats["failed"]) == (3, 2, 1, 0, 0)
    assert len(db.rows) == 2


def test_per_row_path_reports_an_unexplained_skip_as_db_skipped() -> None:
    w = _w()
    db = _BatchBroken(SEVEN)
    stale = _row("A")
    db.rows[tuple(stale[c] for c in SEVEN)] = stale          # a row the delete scope did not clear
    stats = w.new_write_stats()
    cleared = {(CHART, "lahiri_chitrapaksha", "D30")}        # scope already cleared this run: no DELETE
    landed = w._write_rows_batch(db, [_row("A"), _row("B")], cleared, stats)
    assert landed == 1
    assert (stats["landed"], stats["collided"], stats["db_skipped"]) == (1, 0, 1)


def test_batch_path_counts_an_unexplained_skip_once() -> None:
    w = _w()
    db = FakeDB(SEVEN)
    stale = _row("A")
    db.rows[tuple(stale[c] for c in SEVEN)] = stale
    stats = w.new_write_stats()
    cleared = {(CHART, "lahiri_chitrapaksha", "D30")}
    w._write_rows_batch(db, [_row("A"), _row("B"), _row("B")], cleared, stats)
    # A: skipped by the database (unexplained); second B: a detected collision, also skipped (explained)
    assert (stats["landed"], stats["collided"], stats["db_skipped"]) == (1, 1, 1)
    assert stats["attempted"] - stats["landed"] == stats["collided"] + stats["db_skipped"] + stats["failed"]


def test_per_row_path_rejections_raise_after_counting() -> None:
    w = _w()

    class _RejectB(_BatchBroken):
        def insert(self, sql: str, row: dict) -> int:
            if row["fact_subject"] == "B":
                raise RuntimeError("check constraint")
            return super().insert(sql, row)

    stats = w.new_write_stats()
    with pytest.raises(RuntimeError, match="1 of 2 rows were rejected"):
        w._write_rows_batch(_RejectB(SEVEN), [_row("A"), _row("B")], set(), stats)
    assert (stats["landed"], stats["failed"]) == (1, 1)


def test_find_key_collisions_is_pure_and_order_independent() -> None:
    w = _w()
    rows = [_row("A"), _row("B"), _row("A")]
    assert len(w.find_key_collisions(rows)) == 1
    assert w.find_key_collisions([_row("A"), _row("B")]) == []


def test_rows_the_database_rejects_are_not_swallowed() -> None:
    """The per-row fallback used to log each rejection and return a smaller number,
    so a table that refuses every INSERT (RLS with no policy) ended 'lit' with 0 rows."""
    w = _w()

    class _Refusing(FakeDB):
        def insert(self, sql: str, row: dict) -> int:
            raise RuntimeError("new row violates row-level security policy")

    with pytest.raises(RuntimeError, match="rejected by the database"):
        w._write_rows_batch(_Refusing(SEVEN), [_row("D30.S1"), _row("D30.S2")], set(), w.new_write_stats())


def test_sentinels_replaced_per_ayanamsha_are_not_run_collisions(_deities: None, _karakas: None) -> None:
    """The legacy multi-ayanamsha call re-deletes and re-emits the INVARIANT sentinels."""
    w = _w()
    db = FakeDB(SEVEN)
    s = w.build_ga_vargas(CHART, BUILD, conn=db, birth_params=BIRTH,
                          ayanamsha_subset=["lahiri_chitrapaksha", "true_chitra"])
    assert s["rows_collided"] == 0
    assert db.count("scope_cap", "INVARIANT") == 6


# --------------------------------------------------------------------------
# preflight
# --------------------------------------------------------------------------

def test_preflight_accepts_only_the_seven_column_index() -> None:
    w = _w()
    w.assert_unique_key_grain(FakeDB(SEVEN))
    with pytest.raises(RuntimeError, match="F-A2"):
        w.assert_unique_key_grain(FakeDB(SIX))


def test_preflight_fails_closed_when_the_index_cannot_be_read() -> None:
    w = _w()

    class _Blind(FakeDB):
        def execute(self, sql: str, params: Any = None) -> _Result:
            return _Result(None)

    with pytest.raises(RuntimeError, match="cannot read"):
        w.assert_unique_key_grain(_Blind(SEVEN))


# --------------------------------------------------------------------------
# orchestrator adapter: rows_inserted = stored rows; the rest is surfaced
# --------------------------------------------------------------------------

def test_adapter_reports_stored_rows_and_surfaces_the_rest(monkeypatch: pytest.MonkeyPatch) -> None:
    from pipeline.orchestrator.writers import ga_vargas as adapter
    from ga_writers import ga_vargas_writer as w

    def stub(**_kw: Any) -> dict:
        return {"total_rows_written": 7700, "rows_attempted": 7724, "rows_landed": 7700,
                "rows_collided": 20, "rows_db_skipped": 4, "rows_failed": 0,
                "collision_samples": [("k",)]}

    monkeypatch.setattr(w, "build_ga_vargas", stub)

    class _Ctx:
        config = {"chart_id": CHART, "birth_params": BIRTH}
        build_id = BUILD
        db_conn = None

    class _Step:
        key = "lahiri_chitrapaksha"

    res = adapter.GaVargasWriter.run_substep.__wrapped__(adapter.GaVargasWriter(), _Ctx(), _Step())
    assert res.rows_inserted == 7700 and res.rows_skipped == 24
    assert "20 unique-key collisions" in res.notes
