"""Unit tests for Nārāyaṇa Daśā (CR-104, D-2 Lane V-6) in ga_dashas_writer.py.

Pure-logic tests using a fake DB conn (no live DB required) — exercises the
odd/even Lagna start-sign rule and the resulting dasha row structure's
internal consistency (§N.4 no-JH-parity-oracle: verification is
internal-consistency + classical-rule re-derivation, not external parity).
"""
from __future__ import annotations

from ga_writers import ga_dashas_writer as sut


class _FakeCursor:
    def __init__(self, row):
        self._row = row

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        self._last = (sql, params)

    def fetchone(self):
        return self._row

    def fetchall(self):
        return []


class _FakeConn:
    def __init__(self, lagna_sign: str):
        self._row = (lagna_sign,)

    def cursor(self, *a, **k):
        return _FakeCursor(self._row)


def test_narayana_start_sign_odd_lagna_is_lagna_itself():
    # Aries = sign 1 (odd) — the native's own forensic lagna.
    conn = _FakeConn("Aries")
    start = sut._compute_narayana_start_sign(conn, "chart-test", "lahiri_chitrapaksha")
    assert start == 0  # Aries, 0-based index 0


def test_narayana_start_sign_even_lagna_is_7th_from_lagna():
    # Taurus = sign 2 (even) -> 7th from Taurus = Scorpio (index 1 + 6 = 7).
    conn = _FakeConn("Taurus")
    start = sut._compute_narayana_start_sign(conn, "chart-test", "lahiri_chitrapaksha")
    assert start == 7  # Scorpio


def test_narayana_start_sign_libra_odd_is_libra_itself():
    # Libra = sign 7 (odd).
    conn = _FakeConn("Libra")
    start = sut._compute_narayana_start_sign(conn, "chart-test", "lahiri_chitrapaksha")
    assert start == 6  # Libra, 0-based index 6


def test_narayana_start_sign_missing_lagna_raises_no_fabrication():
    conn = _FakeConn.__new__(_FakeConn)
    conn._row = (None,)
    import pytest
    with pytest.raises(ValueError, match="missing Lagna sign"):
        sut._compute_narayana_start_sign(conn, "chart-test", "lahiri_chitrapaksha")


def test_verify_narayana_detects_overlap():
    from datetime import date
    rows = [
        {"level_n": 1, "lord_graha": "Aries", "start_date": date(2000, 1, 1), "end_date": date(2010, 1, 1)},
        {"level_n": 1, "lord_graha": "Taurus", "start_date": date(2005, 1, 1), "end_date": date(2015, 1, 1)},
    ]
    verdict = sut._verify_narayana(rows)
    assert verdict.startswith("overlap:")


def test_verify_narayana_consistent_when_non_overlapping():
    from datetime import date
    rows = [
        {"level_n": 1, "lord_graha": "Aries", "start_date": date(2000, 1, 1), "end_date": date(2010, 1, 1)},
        {"level_n": 1, "lord_graha": "Taurus", "start_date": date(2010, 1, 1), "end_date": date(2020, 1, 1)},
    ]
    assert sut._verify_narayana(rows) == "consistent"


def test_narayana_registered_in_systems_list():
    assert "narayana" in sut.SYSTEMS
