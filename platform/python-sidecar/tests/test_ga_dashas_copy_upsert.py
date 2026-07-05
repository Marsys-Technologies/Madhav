"""
test_ga_dashas_copy_upsert.py — BA-P3 FIX 2: COPY-based bulk load + completeness
check for ga_dashas_writer.

NO DB required — uses a fake psycopg-shaped connection/cursor/copy object to
verify (a) rows are written via COPY in the correct column order, (b) the
DELETE-then-COPY idempotency scoping still fires before the load, and (c)
build_system() raises loud when the persisted count doesn't match the computed
count instead of silently reporting PASS on a partial write.
"""
from __future__ import annotations

import sys
import pathlib

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from ga_writers import ga_dashas_writer as mod  # noqa: E402


class _FakeCopy:
    def __init__(self, sql, sink):
        self.sql = sql
        self.sink = sink

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def write_row(self, values):
        self.sink.append(values)


class _FakeCursor:
    def __init__(self, sink, deletes):
        self._sink = sink
        self._deletes = deletes

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        self._deletes.append((sql, params))
        return self

    @property
    def rowcount(self):
        return 0

    def copy(self, sql):
        return _FakeCopy(sql, self._sink)


class _FakeConn:
    def __init__(self):
        self.copied_rows: list[tuple] = []
        self.deletes: list[tuple] = []
        self.committed = False

    def cursor(self):
        return _FakeCursor(self.copied_rows, self.deletes)

    def execute(self, sql, params=None):
        # replace_prior_chart_dashas uses conn.execute() directly (via _delete)
        self.deletes.append((sql, params))
        class _R:
            rowcount = 0
        return _R()

    def commit(self):
        self.committed = True


def _sample_rows(n=3):
    rows = []
    for i in range(n):
        rows.append({
            "dasha_row_id": f"row-{i}", "chart_id": "chart-x", "ayanamsha_id": "lahiri",
            "build_id": "build-x", "system_id": "vimshottari", "level_n": 1,
            "parent_row_id": None, "lord_graha": "Jupiter", "lord_sign": "Sagittarius",
            "start_date": None, "end_date": None, "start_iso": None, "end_iso": None,
            "duration_days": 100.0, "sandhi_flag": False, "karaka_role_at_period": None,
            "verification_pass_status": "two_pass_verified", "verification_method": "x",
            "citation_ref": "ref", "citation_human": "human", "computed_at": "now",
            "engine_version": "v", "lord_natal_house_d1": None, "lord_natal_sign": None,
            "lord_natal_nakshatra": None, "lord_natal_dignity_d1": None,
            "lord_natal_shadbala_total": None, "sandhi_with_next_dasha_lord": None,
            "next_dasha_start_iso": None, "concurrent_system_lords_jsonb": None,
            "convergence_count_at_start": None, "applies_to_this_chart_flag": True,
            "period_deity_or_marker": None, "lord_to_parent_relationship": None,
            "varsha_year_lord": None, "anchored_solar_return_iso": None,
            "triggered_yogas_jsonb_atomic": "[]", "lord_transit_at_period_start_jsonb": None,
            "karakas_active_during_period": None, "is_truncated_at_window_start": False,
            "is_truncated_at_window_end": False, "kp_sublevel": None, "kp_sub_lord": None,
            "kp_sub_sub_lord": None,
        })
    return rows


def test_upsert_rows_writes_via_copy_in_column_order():
    conn = _FakeConn()
    rows = _sample_rows(3)

    written = mod._upsert_rows(conn, rows, "vimshottari", "lahiri", commit=False)

    assert written == 3
    assert len(conn.copied_rows) == 3
    # dasha_row_id is _COPY_COLUMNS[0]; chart_id is _COPY_COLUMNS[1]
    assert conn.copied_rows[0][0] == "row-0"
    assert conn.copied_rows[0][1] == "chart-x"
    assert not conn.committed  # commit=False → caller/orchestrator owns commit


def test_upsert_rows_deletes_prior_scope_before_copy():
    conn = _FakeConn()
    rows = _sample_rows(2)

    mod._upsert_rows(conn, rows, "vimshottari", "lahiri", commit=True)

    assert any("DELETE FROM chart_dashas" in sql for sql, _ in conn.deletes)
    assert conn.committed


def test_upsert_rows_empty_is_noop():
    conn = _FakeConn()
    written = mod._upsert_rows(conn, [], "vimshottari", "lahiri")
    assert written == 0
    assert conn.copied_rows == []


def test_upsert_rows_disables_statement_timeout_before_copy():
    """BA-P3 FIX 2c: a large system's COPY (e.g. chara_karaka, ~40K rows) can
    exceed the DB role's default statement_timeout (25-30s) under load. Must
    SET LOCAL statement_timeout = 0 before the COPY, same pattern as every
    other heavy per-chart writer in this codebase."""
    conn = _FakeConn()
    rows = _sample_rows(2)

    mod._upsert_rows(conn, rows, "vimshottari", "lahiri", commit=False)

    assert any(
        sql is not None and "SET LOCAL statement_timeout" in sql
        for sql, _params in conn.deletes
    ), f"expected a SET LOCAL statement_timeout call before COPY, got: {conn.deletes}"


def test_build_system_raises_on_partial_persist(monkeypatch):
    """If _upsert_rows silently persists fewer rows than computed, build_system
    must raise rather than return status=PASS (BA-P3 FIX 2 completeness check)."""
    monkeypatch.setattr(mod, "_get_moon_position", lambda aya, birth: (325.5, mod.BIRTH_JD if hasattr(mod, "BIRTH_JD") else 2445734.5))
    monkeypatch.setattr(mod, "_upsert_rows", lambda conn, rows, sys_id, aya, commit=True: max(0, len(rows) - 1))

    conn = _FakeConn()
    with pytest.raises(RuntimeError, match="completeness check FAILED"):
        mod.build_system(
            "vimshottari", "lahiri", mod.CANONICAL_CHART_ID,
            "build-x", conn=conn,
            birth_params={
                "datetime_iso": "1984-02-05T10:43:00",
                "latitude_deg": 20.2961,
                "longitude_deg": 85.8245,
                "tz_offset_hours": 5.5,
            },
        )
