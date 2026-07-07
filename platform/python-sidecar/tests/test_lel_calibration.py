"""
Unit tests for services.mimamsa.lel_calibration (BA Phase-4 R2.2 / W2.2).

Pure decision logic — no DB, no clock, no prod. Fixtures simulate the post-423
schema (chart-scoped life_events) via a fake connection.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from services.mimamsa import lel_calibration as lc


# ── calibration state machine ────────────────────────────────────────────────

class TestCalibrationState:
    def test_zero_is_structural(self):
        assert lc.calibration_state(0) == lc.STATE_STRUCTURAL

    def test_one_is_sparse(self):
        assert lc.calibration_state(1) == lc.STATE_SPARSE

    def test_two_event_roundtrip_is_sparse(self):
        # W3 Abhinandan synthetic round-trip: 2 events must read as sparse
        # (structural→sparse→structural on add-then-remove).
        assert lc.calibration_state(2) == lc.STATE_SPARSE

    def test_just_below_threshold_is_sparse(self):
        assert lc.calibration_state(lc.CALIBRATED_MIN_EVENTS - 1) == lc.STATE_SPARSE

    def test_at_threshold_is_calibrated(self):
        assert lc.calibration_state(lc.CALIBRATED_MIN_EVENTS) == lc.STATE_CALIBRATED

    def test_native_57_is_calibrated(self):
        assert lc.calibration_state(57) == lc.STATE_CALIBRATED

    def test_negative_raises(self):
        with pytest.raises(ValueError):
            lc.calibration_state(-1)


class TestRectificationBasis:
    def test_zero_is_structural_no_lel(self):
        assert lc.rectification_basis(0) == lc.BASIS_STRUCTURAL_NO_LEL

    def test_any_events_is_lel_fit(self):
        assert lc.rectification_basis(1) == lc.BASIS_LEL_FIT
        assert lc.rectification_basis(57) == lc.BASIS_LEL_FIT


class TestLoadBearing:
    def test_only_calibrated_is_load_bearing(self):
        assert lc.is_load_bearing(0) is False
        assert lc.is_load_bearing(3) is False
        assert lc.is_load_bearing(57) is True


class TestJudgmentFlags:
    def test_structural_flags(self):
        f = lc.judgment_flags(0)
        assert f["calibration"] == lc.STATE_STRUCTURAL
        assert f["rectification_basis"] == lc.BASIS_STRUCTURAL_NO_LEL
        assert f["lel_event_count"] == 0
        assert f["load_bearing"] is False

    def test_calibrated_flags(self):
        f = lc.judgment_flags(57)
        assert f["calibration"] == lc.STATE_CALIBRATED
        assert f["rectification_basis"] == lc.BASIS_LEL_FIT
        assert f["lel_event_count"] == 57
        assert f["load_bearing"] is True


# ── recorded_at leakage routing ──────────────────────────────────────────────

class TestRecordedAtPartition:
    def _dt(self, y, m=1, d=1):
        return datetime(y, m, d, tzinfo=timezone.utc)

    def test_pre_instrument_sentinel_always_training(self):
        # The native's 57 rows carry a pre_instrument recorded_at.
        assert lc.recorded_at_partition(self._dt(1999), self._dt(2010)) == lc.PARTITION_TRAINING

    def test_no_snapshot_is_training(self):
        assert lc.recorded_at_partition(self._dt(2025), None) == lc.PARTITION_TRAINING

    def test_recorded_before_snapshot_is_training(self):
        assert lc.recorded_at_partition(self._dt(2025, 1, 1), self._dt(2025, 6, 1)) == lc.PARTITION_TRAINING

    def test_recorded_after_snapshot_is_outcome(self):
        assert lc.recorded_at_partition(self._dt(2025, 12, 1), self._dt(2025, 6, 1)) == lc.PARTITION_OUTCOME

    def test_recorded_equal_snapshot_is_outcome(self):
        # at/after the snapshot → outcome (strict-before rule).
        t = self._dt(2025, 6, 1)
        assert lc.recorded_at_partition(t, t) == lc.PARTITION_OUTCOME

    def test_naive_datetime_assumed_utc(self):
        naive = datetime(2025, 12, 1)
        assert lc.recorded_at_partition(naive, self._dt(2025, 6, 1)) == lc.PARTITION_OUTCOME


# ── cross-chart pool gate ────────────────────────────────────────────────────

class TestPoolGate:
    def test_default_off(self):
        assert lc.pool_enabled(override="off") is False

    def test_explicit_off_variants(self):
        for v in ("off", "0", "false", "", "no"):
            assert lc.pool_enabled(override=v) is False

    def test_on_variants(self):
        for v in ("on", "1", "true", "YES", "Enabled"):
            assert lc.pool_enabled(override=v) is True, v

    def test_may_consume_requires_both_keys(self):
        # consent alone is not enough
        assert lc.may_consume_into_pool(True, override="off") is False
        # pool on alone is not enough
        assert lc.may_consume_into_pool(False, override="on") is False
        # both required
        assert lc.may_consume_into_pool(True, override="on") is True

    def test_env_default_is_off(self, monkeypatch):
        monkeypatch.delenv(lc.POOL_ENV_VAR, raising=False)
        assert lc.pool_enabled() is False


# ── debounced recalibration trigger ──────────────────────────────────────────

class TestShouldRecalibrate:
    def _t(self, secs):
        return datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=secs)

    def test_no_save_never_triggers(self):
        assert lc.should_recalibrate(None, None, self._t(1000)) is False

    def test_within_debounce_waits(self):
        saved = self._t(0)
        now = self._t(30)  # < default 90s
        assert lc.should_recalibrate(saved, None, now) is False

    def test_after_debounce_triggers(self):
        saved = self._t(0)
        now = self._t(120)  # > 90s
        assert lc.should_recalibrate(saved, None, now) is True

    def test_already_recalibrated_after_save_no_trigger(self):
        saved = self._t(0)
        recalced = self._t(10)  # recalced after the save
        now = self._t(1000)
        assert lc.should_recalibrate(saved, recalced, now) is False

    def test_new_save_after_recalibration_triggers(self):
        recalced = self._t(0)
        saved = self._t(100)  # newer save
        now = self._t(300)
        assert lc.should_recalibrate(saved, recalced, now) is True

    def test_custom_debounce(self):
        saved = self._t(0)
        now = self._t(10)
        assert lc.should_recalibrate(saved, None, now, debounce_seconds=5) is True
        assert lc.should_recalibrate(saved, None, now, debounce_seconds=20) is False


# ── thin DB helper with a fake conn (post-423 schema) ────────────────────────

class _FakeCursor:
    def __init__(self, result, raise_exc=None):
        self._result = result
        self._raise = raise_exc
        self.executed = None

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        if self._raise:
            raise self._raise
        self.executed = (sql, params)

    def fetchone(self):
        return self._result


class _FakeConn:
    def __init__(self, result, raise_exc=None):
        self._cursor = _FakeCursor(result, raise_exc)

    def cursor(self, *a, **k):
        return self._cursor


class TestCountChartLelEvents:
    def test_counts_chart_scoped_tuple_row(self):
        conn = _FakeConn((57,))
        assert lc.count_chart_lel_events(conn, "chart-x") == 57
        # verify it filtered by chart_id
        assert "WHERE chart_id" in conn._cursor.executed[0]
        assert conn._cursor.executed[1] == ("chart-x",)

    def test_counts_dict_row(self):
        conn = _FakeConn({"count": 3})
        assert lc.count_chart_lel_events(conn, "chart-x") == 3

    def test_empty_chart_is_zero(self):
        conn = _FakeConn((0,))
        assert lc.count_chart_lel_events(conn, "chart-x") == 0

    def test_missing_table_yields_zero_not_crash(self):
        conn = _FakeConn(None, raise_exc=RuntimeError("relation does not exist"))
        assert lc.count_chart_lel_events(conn, "chart-x") == 0


# ── pool contribution capture (Step-6 capture-now, consume-gated) ────────────

class _RecordingCursor:
    """Captures the INSERT (sql, params) issued by record_pool_contribution."""
    def __init__(self):
        self.executed: list[tuple] = []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        self.executed.append((sql, params))


class _RecordingConn:
    def __init__(self):
        self._cursor = _RecordingCursor()

    def cursor(self, *a, **k):
        return self._cursor


class TestRecordPoolContribution:
    def _run(self, pool_consent, override=None, monkeypatch=None, weights=None):
        conn = _RecordingConn()
        if override is not None and monkeypatch is not None:
            monkeypatch.setenv(lc.POOL_ENV_VAR, override)
        lc.record_pool_contribution(
            conn,
            chart_id="chart-x",
            event_classes=["career.role_change", "health.injury"],
            weights=weights,
            priors_version="priors_v1",
            pool_consent=pool_consent,
        )
        return conn

    def test_builds_the_right_insert(self):
        conn = self._run(pool_consent=True, weights={"a": 0.5})
        assert len(conn._cursor.executed) == 1
        sql, params = conn._cursor.executed[0]
        assert "INSERT INTO mimamsa_pool_contributions" in sql
        assert "chart_id" in sql and "event_classes" in sql and "pool_consent" in sql
        # params order: chart_id, event_classes, weights(jsonb str), priors_version, consent
        assert params[0] == "chart-x"
        assert params[1] == ["career.role_change", "health.injury"]
        assert json.loads(params[2]) == {"a": 0.5}
        assert params[3] == "priors_v1"
        assert params[4] is True

    def test_none_weights_serialize_to_none(self):
        conn = self._run(pool_consent=False, weights=None)
        _sql, params = conn._cursor.executed[0]
        assert params[2] is None

    def test_captures_even_when_pool_flag_off(self, monkeypatch):
        # capture-now: the INSERT happens regardless of the global flag.
        conn = self._run(pool_consent=True, override="off", monkeypatch=monkeypatch)
        assert len(conn._cursor.executed) == 1

    def test_captures_even_without_consent(self):
        # capture is decoupled from consent — consent is stored as provenance only.
        conn = self._run(pool_consent=False)
        _sql, params = conn._cursor.executed[0]
        assert params[4] is False
        assert len(conn._cursor.executed) == 1

    def test_capture_does_not_gate_on_pool_but_consume_does(self, monkeypatch):
        # The capture writes with flag off; the CONSUME side stays gated.
        monkeypatch.setenv(lc.POOL_ENV_VAR, "off")
        conn = self._run(pool_consent=True)
        assert len(conn._cursor.executed) == 1  # captured
        assert lc.may_consume_into_pool(True) is False  # but not consumable
