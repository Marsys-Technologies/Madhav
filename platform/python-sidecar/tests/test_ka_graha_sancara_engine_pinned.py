"""
tests/test_ka_graha_sancara_engine_pinned.py — NODE-SERIES step 1 (P8/P9): the pinned ephemeris-at-T read.

Covers `services/ka_graha_sancara/engine_pinned.py` (the node-pinned copy of `engine._read_from_bg_ephemeris` /
`engine.get_ephemeris`), the re-pointed callers (`brahmagyan/phala/muhurta.py`, the `ka_graha_sancara` writer) and the
SS-ruled constraint that `engine.py` itself stays byte-untouched (a one-line edit moves ~43 writer digests).

DB-free: a mock connection in the style of tests/test_ka_graha_sancara.py. The real-PostgreSQL proof (same result with a
MEAN series beside the TRUE one, loud refusal when the TRUE node rows are absent) lives in
tests/test_node_series_readers_ignore_mean_rows.py (rows P8 / P9 and the dead-copy LEGACY row).
"""
from __future__ import annotations

import hashlib
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

SIDECAR = Path(__file__).parent.parent
if str(SIDECAR) not in sys.path:
    sys.path.insert(0, str(SIDECAR))

from services.ka_graha_sancara import engine, engine_pinned  # noqa: E402
from services.w2g.node_series import NODE_SERIES_PREDICATE, NodeSeriesError  # noqa: E402

_IST = timezone(timedelta(hours=5, minutes=30))
_DT = datetime(2026, 7, 12, 6, 0, tzinfo=_IST)
_DATE = date(2026, 7, 12)
_LONS = {"Sun": 86.1, "Moon": 200.3, "Mars": 150.2, "Mercury": 100.4, "Jupiter": 95.0, "Venus": 140.7,
         "Saturn": 20.9, "Rahu": 330.5, "Ketu": 150.5}

# sha256 of services/ka_graha_sancara/engine.py as it is on origin/main (verified equal when this test was written).
# SS ruling: engine.py is NOT edited by the node-series work, because a one-line edit moves ~43 writer digests (13 ga_*,
# 23 bo_*, 7 ka_*). The unpinned `_read_from_bg_ephemeris` / `get_ephemeris` stay in it as DEAD COPIES, to be removed at the
# next PLANNED digest move. When that move happens, update this pin in the same PR (that is the point of the friction).
ENGINE_PY_SHA256 = "31c9e32f415b39dd5d04ad56c12d82cd2e81bd88bfee9267766511ec9f97b891"


def _rows(extra=(), skip=()):
    rows = [{"body": b, "tropical_longitude": lon, "speed_dps": 1.0, "is_retrograde": False}
            for b, lon in _LONS.items() if b not in skip]
    rows.extend(extra)
    return rows


def _conn(rows):
    cur = MagicMock()
    cur.fetchall.return_value = rows
    conn = MagicMock()
    conn.cursor.return_value.__enter__ = lambda s: cur
    conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    return conn, cur


def _no_live_fallback():
    """PATH-B must not be reached when a refusal is expected: calling it fails the test loudly."""
    return patch.object(engine, "_compute_live", side_effect=AssertionError("fell through to live compute"))


# ------------------------------------------------------------------------------------------- the pinned read
def test_the_pinned_statement_carries_the_node_series_predicate():
    conn, cur = _conn(_rows())
    result = engine_pinned.get_ephemeris(_DT, ayanamsha="lahiri", db_conn=conn)
    sql = cur.execute.call_args[0][0]
    assert NODE_SERIES_PREDICATE in sql
    assert result.source == "bg_ephemeris" and len(result.grahas) == 9


def test_a_single_series_day_is_served_from_path_a():
    conn, _ = _conn(_rows())
    with _no_live_fallback():
        result = engine_pinned.get_ephemeris(_DT, ayanamsha="lahiri", db_conn=conn)
    assert set(result.grahas) == set(_LONS)
    assert all(g.source == "bg_ephemeris" for g in result.grahas.values())


def test_two_rows_for_one_node_and_date_raise_and_do_not_fall_through_to_live():
    dup = {"body": "Rahu", "tropical_longitude": 331.9, "speed_dps": -0.05, "is_retrograde": True}
    conn, _ = _conn(_rows(extra=[dup]))
    with _no_live_fallback(), pytest.raises(NodeSeriesError):
        engine_pinned.get_ephemeris(_DT, ayanamsha="lahiri", db_conn=conn)


def test_a_day_with_other_bodies_but_no_node_row_raises():
    conn, _ = _conn(_rows(skip=("Ketu",)))
    with _no_live_fallback(), pytest.raises(NodeSeriesError):
        engine_pinned.get_ephemeris(_DT, ayanamsha="lahiri", db_conn=conn)


def test_the_designed_fallbacks_are_kept():
    """No row at all, a missing NON-node body and a database error still fall through to PATH-B (the same TRUE series)."""
    sentinel = {"live": True}
    for conn in (_conn([])[0], _conn(_rows(skip=("Venus",)))[0]):
        with patch.object(engine, "_compute_live", return_value=sentinel) as live:
            result = engine_pinned.get_ephemeris(_DT, ayanamsha="lahiri", db_conn=conn)
        assert result.source == "swisseph_live" and result.grahas is sentinel
        live.assert_called_once()
    broken = MagicMock()
    broken.cursor.side_effect = RuntimeError("connection lost")
    with patch.object(engine, "_compute_live", return_value=sentinel):
        assert engine_pinned.get_ephemeris(_DT, ayanamsha="lahiri", db_conn=broken).source == "swisseph_live"


def test_the_pinned_copy_gives_the_same_grahas_as_the_dead_copy_on_a_single_series_day():
    conn_a, _ = _conn(_rows())
    conn_b, _ = _conn(_rows())
    pinned = engine_pinned.get_ephemeris(_DT, ayanamsha="lahiri", db_conn=conn_a)
    legacy = engine.get_ephemeris(_DT, ayanamsha="lahiri", db_conn=conn_b)
    assert pinned.source == legacy.source == "bg_ephemeris"
    assert pinned.grahas == legacy.grahas


# ------------------------------------------------------------------------------------------- engine.py stays untouched
def test_engine_py_is_byte_identical_to_origin_main():
    """SS ruling: engine.py is untouched (pinned-module route only). Enforced as a sha256 pin of the origin/main bytes."""
    got = hashlib.sha256((SIDECAR / "services" / "ka_graha_sancara" / "engine.py").read_bytes()).hexdigest()
    assert got == ENGINE_PY_SHA256, (
        "services/ka_graha_sancara/engine.py changed. It sits in the digest closure of ~43 writers; do not edit it for the "
        "node-series work. If a planned digest move edits it on purpose, delete the dead unpinned copies in the same PR and "
        "update ENGINE_PY_SHA256."
    )


def test_the_dead_copies_are_still_in_engine_py_and_unpinned():
    src = (SIDECAR / "services" / "ka_graha_sancara" / "engine.py").read_text()
    assert "def _read_from_bg_ephemeris(" in src and "def get_ephemeris(" in src
    assert "NODE_SERIES_PREDICATE" not in src and "node_mode" not in src


def test_the_re_pointed_callers_use_the_pinned_module():
    muhurta = (SIDECAR / "brahmagyan" / "phala" / "muhurta.py").read_text()
    writer = (SIDECAR / "pipeline" / "orchestrator" / "writers" / "ka_graha_sancara.py").read_text()
    for name, src in (("muhurta.py", muhurta), ("writers/ka_graha_sancara.py", writer)):
        assert "ka_graha_sancara.engine_pinned import get_ephemeris" in src, name
        assert not re.search(r"ka_graha_sancara\.engine import[^\n]*\bget_ephemeris\b", src), f"{name} still imports the unpinned copy"


# ------------------------------------------------------------------------------------------- P9: phala/muhurta.py
def _muhurta_connect(rows):
    """A stand-in for `psycopg.connect(...)` as a context manager yielding the mock connection."""
    conn, _ = _conn(rows)
    ctx = MagicMock()
    ctx.__enter__ = lambda s: conn
    ctx.__exit__ = MagicMock(return_value=False)
    return MagicMock(return_value=ctx)


@pytest.fixture()
def muhurta_mod():
    from brahmagyan.phala import muhurta
    muhurta._TRANSIT_SIGNS_CACHE.clear()
    yield muhurta
    muhurta._TRANSIT_SIGNS_CACHE.clear()


def test_muhurta_single_series_day_is_unchanged(muhurta_mod):
    with patch.object(muhurta_mod.psycopg, "connect", _muhurta_connect(_rows())):
        signs = muhurta_mod._read_transiting_sign_ids(_DT, "postgresql://unused")
    assert signs is not None and set(signs) == {g.lower() for g in _LONS}
    assert all(1 <= v <= 12 for v in signs.values())


def test_muhurta_raises_on_two_node_rows_instead_of_returning_unavailable(muhurta_mod):
    dup = {"body": "Ketu", "tropical_longitude": 151.9, "speed_dps": -0.05, "is_retrograde": True}
    with patch.object(muhurta_mod.psycopg, "connect", _muhurta_connect(_rows(extra=[dup]))):
        with pytest.raises(NodeSeriesError):
            muhurta_mod._read_transiting_sign_ids(_DT, "postgresql://unused")


def test_muhurta_refusal_is_not_cached_and_reaches_the_grade(muhurta_mod):
    """The grade call must RAISE, not return (None, {... 'ephemeris_daily_unavailable_for_date'}), and cache nothing."""
    dup = {"body": "Rahu", "tropical_longitude": 331.9, "speed_dps": -0.05, "is_retrograde": True}
    with patch.object(muhurta_mod.psycopg, "connect", _muhurta_connect(_rows(extra=[dup]))), \
            patch.object(muhurta_mod, "_natal_moon_sign_id", return_value=3):
        with pytest.raises(NodeSeriesError):
            muhurta_mod._transit_quality_for_window("chart", _DT, "travel", "postgresql://unused")
    assert muhurta_mod._TRANSIT_SIGNS_CACHE == {}


def test_muhurta_other_failures_keep_the_honest_unavailable_none(muhurta_mod):
    """Behaviour-neutral on every non-node failure: a database error is still the designed honest None."""
    boom = MagicMock(side_effect=RuntimeError("connection refused"))
    with patch.object(muhurta_mod.psycopg, "connect", boom):
        assert muhurta_mod._read_transiting_sign_ids(_DT, "postgresql://unused") is None
    with patch.object(muhurta_mod.psycopg, "connect", boom), patch.object(muhurta_mod, "_natal_moon_sign_id", return_value=3):
        q, details = muhurta_mod._transit_quality_for_window("chart", _DT, "travel", "postgresql://unused")
    assert q is None and details["unavailable_reason"] == "ephemeris_daily_unavailable_for_date"
