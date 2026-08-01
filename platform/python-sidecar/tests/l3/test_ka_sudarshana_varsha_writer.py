"""Writer-shell tests for ka_sudarshana_varsha — the DB-touching orchestration
around the pure logic tested in test_ka_sudarshana_varsha.py."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.ka_sudarshana_varsha.writer import (
    _birth_date_from_config,
    _fetch_natal_reference_signs,
    _sign_idx,
)


class TestSignIdx:
    def test_known_sign(self):
        assert _sign_idx("Aries") == 0
        assert _sign_idx("Pisces") == 11

    def test_unknown_sign_returns_none(self):
        assert _sign_idx("NotASign") is None


class TestBirthDateFromConfig:
    def test_missing_birth_params_returns_none(self):
        ctx = SimpleNamespace(config={})
        assert _birth_date_from_config(ctx) is None

    def test_missing_datetime_iso_returns_none(self):
        ctx = SimpleNamespace(config={"birth_params": {"latitude_deg": 20.3}})
        assert _birth_date_from_config(ctx) is None

    def test_malformed_datetime_iso_returns_none(self):
        ctx = SimpleNamespace(config={"birth_params": {"datetime_iso": "not-a-date"}})
        assert _birth_date_from_config(ctx) is None

    def test_real_shape_from_pipeline_orchestrator_birth_params(self):
        # Exact shape produced by pipeline/orchestrator/birth_params.py's _to_birth_params
        # for the native (CLAUDE.md §B: 1984-02-05, 10:43 IST, Bhubaneswar).
        ctx = SimpleNamespace(config={"birth_params": {
            "datetime_iso": "1984-02-05T10:43:00",
            "latitude_deg": 20.2961,
            "longitude_deg": 85.8245,
            "tz_offset_hours": 5.5,
            "place_name": "Bhubaneswar",
            "subject_label": "",
        }})
        assert _birth_date_from_config(ctx) == date(1984, 2, 5)


class _FakeCursor:
    def __init__(self, fetchall_result):
        self._fetchall_result = fetchall_result

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        pass

    def fetchall(self):
        return self._fetchall_result


class _FakeConn:
    def __init__(self, fetchall_result):
        self._fetchall_result = fetchall_result

    def cursor(self, row_factory=None):
        return _FakeCursor(self._fetchall_result)


class TestFetchNatalReferenceSigns:
    def test_all_three_present(self):
        conn = _FakeConn([
            {"fact_subject": "LAGNA", "fact_value_text": "Aries", "fact_id": "f1"},
            {"fact_subject": "MOON", "fact_value_text": "Aquarius", "fact_id": "f2"},
            {"fact_subject": "SUN", "fact_value_text": "Capricorn", "fact_id": "f3"},
        ])
        result = _fetch_natal_reference_signs(conn, "chart-x")
        assert result is not None
        assert result["LAGNA"]["sign_idx"] == 0
        assert result["MOON"]["sign_idx"] == 10
        assert result["SUN"]["sign_idx"] == 9

    def test_missing_one_returns_none(self):
        conn = _FakeConn([
            {"fact_subject": "LAGNA", "fact_value_text": "Aries", "fact_id": "f1"},
            {"fact_subject": "MOON", "fact_value_text": "Aquarius", "fact_id": "f2"},
        ])
        assert _fetch_natal_reference_signs(conn, "chart-x") is None

    def test_empty_returns_none(self):
        conn = _FakeConn([])
        assert _fetch_natal_reference_signs(conn, "chart-x") is None
