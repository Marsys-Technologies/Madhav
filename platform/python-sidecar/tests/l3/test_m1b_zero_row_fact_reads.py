"""
NIRMĀṆA L3-W3 — the two zero-row fact reads the L3 `depends_on` audit turned up.

Both are the same family as M4 (`ka_avadhi`): a query written against a `fact_category`/`fact_key`
vocabulary that does not exist, returning zero rows on every chart, and degrading to a silent
`None` because the only failure path is a log line. Neither surfaces to a caller.

  1. `ka_vighnakara._fetch_natal_lagna_lon` asked for `fact_key='longitude'`. Measured live: 0 rows.
     The real fact is `longitude_sidereal` under `fact_category='graha_position'` (12.4311° for the
     canonical chart on lahiri).
  2. `ka_kshetra`'s natal-lagna lookup asked for `fact_category='lagna'`. Measured live: 0 rows —
     and 0 for `lagna_position` too, so the audit's proposed replacement was also wrong. Same real
     source. That lookup additionally filtered on `fact_key` alone with no `fact_subject`, so even
     with the right category it would have matched any body's longitude and bucketed THAT into a
     lagna sign.

These are source-shape guards. They fail against the pre-fix queries, which is the point: a query
that returns nothing forever cannot be caught by a test that mocks its result.
"""
from __future__ import annotations

import inspect

from pipeline.orchestrator.writers import ka_vighnakara as vighnakara_mod


def _sql_of(fn) -> str:
    return inspect.getsource(fn)


def test_vighnakara_lagna_read_uses_the_fact_key_that_exists() -> None:
    src = _sql_of(vighnakara_mod.KaVighnakaraWriter._fetch_natal_lagna_lon)
    assert "longitude_sidereal" in src, "the real key is longitude_sidereal, not longitude"
    assert "fact_category = 'graha_position'" in src, "§N.7 item 2: the category must be pinned"
    assert "ORDER BY" in src and src.index("ORDER BY") < src.index("LIMIT"), (
        "§N.7 item 2: a LIMIT 1 without a total ORDER BY picks arbitrarily"
    )


def test_vighnakara_no_longer_asks_for_the_nonexistent_bare_longitude_key() -> None:
    src = "\n".join(
        line.split("#", 1)[0] for line in _sql_of(vighnakara_mod.KaVighnakaraWriter._fetch_natal_lagna_lon).splitlines()
    )
    assert "fact_key = 'longitude'\n" not in src and "'longitude' AND" not in src, (
        "the bare 'longitude' key returns zero rows on every chart"
    )


def test_kshetra_lagna_read_is_corrected_and_pins_its_subject() -> None:
    """Read from the file: importing services.ka_kshetra.writer pulls a heavy dependency chain."""
    import pathlib

    root = pathlib.Path(__file__).resolve().parents[2]
    src = (root / "services/ka_kshetra/writer.py").read_text()
    code = "\n".join(line.split("#", 1)[0] for line in src.splitlines())

    assert "fact_category = 'lagna'\n" not in code, (
        "fact_category='lagna' does not exist — 0 rows on every chart"
    )
    # The corrected query, all three pins together.
    assert "fact_category = 'graha_position'" in code
    assert "fact_subject = 'LAGNA'" in code, (
        "without a subject pin the query buckets some other body's longitude into a lagna sign"
    )
    assert "longitude_sidereal" in code
