"""DB9 regression — dict_row cursors must not be indexed positionally.

Root cause (root-caused 2026-08-08, SIDDHANTA arc-finishing run):
the orchestrator connection is built with `row_factory=psycopg.rows.dict_row`
(pipeline/orchestrator/db.py). Three Kāla writers opened a BARE `conn.cursor()`
in their natal-Moon helper, inherited that dict factory, and then indexed the
result positionally (`row[1]`). On a dict row that is a key lookup for the
integer key 1, which does not exist -> `KeyError: 1`, failing the whole asset.

Recorded live errors (asset_throughput, chart 482012f1, 2026-08-08 00:24 UTC):
  ka_kota_chakra    writer.py:126  if not row or row[1] is None:  KeyError: 1
  ka_moorti_nirnaya writer.py:114  if not row or row[1] is None:  KeyError: 1
  ka_tithi_pravesha writer.py:106  if not row or row[1] is None:  KeyError: 1

All three tables were confirmed 0 rows for that chart — the helper fails before
the writer's DELETE, so there were no partial writes, only an empty asset.

These tests drive the real helpers with a dict-row cursor (the production shape)
and assert they read the value correctly instead of raising.
"""
from __future__ import annotations

import pytest


class _DictRowCursor:
    """Cursor that returns dict rows — the production row_factory shape.

    Deliberately ignores the requested row_factory: the point is to prove the
    helper is correct under the connection default that actually broke it.
    """

    def __init__(self, row):
        self._row = row

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        return self

    def fetchone(self):
        return self._row


class _DictRowConn:
    def __init__(self, row):
        self._row = row

    def cursor(self, *args, **kwargs):
        return _DictRowCursor(self._row)


MOON_ROW = {"fact_id": "abc123deadbeef01", "fact_value_num": 295.5}


def test_kota_chakra_reads_dict_row_without_keyerror():
    from services.ka_kota_chakra.writer import _fetch_janma_nakshatra_idx

    result = _fetch_janma_nakshatra_idx(_DictRowConn(MOON_ROW), "chart-x")

    assert result is not None, "helper returned None on a well-formed dict row"
    nak_idx, fact_id = result
    assert fact_id == "abc123deadbeef01"
    assert 0 <= nak_idx < 27


def test_moorti_nirnaya_reads_dict_row_without_keyerror():
    from services.ka_moorti_nirnaya.writer import _fetch_janma_nakshatra_idx

    result = _fetch_janma_nakshatra_idx(_DictRowConn(MOON_ROW), "chart-x")

    assert result is not None
    nak_idx, fact_id = result
    assert fact_id == "abc123deadbeef01"
    assert 0 <= nak_idx < 27


def test_tithi_pravesha_reads_dict_row_without_keyerror():
    from services.ka_tithi_pravesha.writer import _fetch_natal_moon_longitude

    result = _fetch_natal_moon_longitude(_DictRowConn(MOON_ROW), "chart-x")

    assert result is not None
    lon, fact_id = result
    assert lon == pytest.approx(295.5)
    assert fact_id == "abc123deadbeef01"


# ── Honest-absence must survive the fix (B.10: never fabricate) ───────────────


@pytest.mark.parametrize("row", [None, {"fact_id": "x", "fact_value_num": None}])
def test_all_three_return_none_on_absent_fact(row):
    """Missing L1 dependency must still yield None, not a fabricated value.

    This is the branch the original code got RIGHT; the fix must not break it.
    """
    from services.ka_kota_chakra.writer import _fetch_janma_nakshatra_idx as kota
    from services.ka_moorti_nirnaya.writer import _fetch_janma_nakshatra_idx as moorti
    from services.ka_tithi_pravesha.writer import _fetch_natal_moon_longitude as tithi

    for fn in (kota, moorti, tithi):
        assert fn(_DictRowConn(row), "chart-x") is None, (
            f"{fn.__module__} fabricated a value for an absent natal Moon fact"
        )


def test_positional_access_would_still_raise_on_dict_row():
    """MUTATION CONTROL: proves these tests can actually fail.

    Reproduces the exact original defect against the same dict row. If this
    does NOT raise KeyError, the test fixture is not reproducing production's
    row shape and the three tests above prove nothing.
    """
    with pytest.raises(KeyError):
        _ = MOON_ROW[1]
