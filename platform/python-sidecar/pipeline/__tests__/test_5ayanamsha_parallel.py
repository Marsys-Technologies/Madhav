"""
Tests for C-02: 5-ayanamsha parallel asyncio runner.

Verifies:
  - run_engine_parallel() returns a dict keyed by all requested ayanamshas
  - partial-failure semantics (some fail, others succeed)
  - total-failure semantics (all fail, returns None values, no exception)
  - stub path (pyjhora_adapter not available)
  - concurrent execution (all ayanamshas attempted even if some raise)
  - load_birth_data() returns dict with required keys
  - return value is always a dict of exactly len(ayanamshas) entries
  - CANONICAL_AYANAMSHAS has exactly 5 entries
  - engine results are keyed by canonical ayanamsha_id strings
"""
from __future__ import annotations

import asyncio
import sys
import types
from unittest.mock import MagicMock, patch

import pytest

# ── Import the module under test ───────────────────────────────────────────────
sys.path.insert(0, "/Users/Dev/Vibe-Coding/Apps/MadhavBO-C/platform/python-sidecar")

from pipeline.build_chart import (
    CANONICAL_AYANAMSHAS,
    load_birth_data,
    run_engine_parallel,
)

# ── Helpers ────────────────────────────────────────────────────────────────────

def make_fake_compute_chart(fail_on: set | None = None, raise_on: set | None = None):
    """
    Return a fake compute_chart function.

    fail_on  : ayanamshas that should raise an Exception.
    raise_on : alias for fail_on (same semantics).
    """
    bad = (fail_on or set()) | (raise_on or set())

    def _compute(inputs, engine_version=None, ayanamsha_id=None, **kwargs):
        if ayanamsha_id in bad:
            raise RuntimeError(f"Simulated engine failure for {ayanamsha_id}")
        return {
            "ayanamsha_id": ayanamsha_id,
            "chart_id": inputs.get("subject_label", "unknown"),
            "computed": True,
        }

    return _compute


def inject_engine(compute_fn):
    """Inject a fake pyjhora_adapter module into sys.modules."""
    fake_module = types.ModuleType("pyjhora_adapter")
    fake_module.compute_chart = compute_fn
    sys.modules["pyjhora_adapter"] = fake_module
    return fake_module


def remove_engine():
    """Remove pyjhora_adapter from sys.modules (restores real adapter on next import)."""
    sys.modules.pop("pyjhora_adapter", None)


def stub_sentinel():
    """
    Return a context manager that forces the stub path in run_engine_parallel.

    run_engine_parallel does `from pyjhora_adapter import compute_chart` inside a
    try/except ImportError.  We force that import to fail by temporarily placing
    a broken sentinel in sys.modules["pyjhora_adapter"] that has no compute_chart
    attribute, causing an ImportError on `from pyjhora_adapter import compute_chart`.
    """
    import contextlib

    @contextlib.contextmanager
    def _ctx():
        broken = types.ModuleType("pyjhora_adapter")
        old = sys.modules.get("pyjhora_adapter")
        sys.modules["pyjhora_adapter"] = broken
        try:
            yield
        finally:
            if old is None:
                sys.modules.pop("pyjhora_adapter", None)
            else:
                sys.modules["pyjhora_adapter"] = old

    return _ctx()


# ── CANONICAL_AYANAMSHAS sanity ────────────────────────────────────────────────

class TestCanonicalAyanamshas:
    def test_exactly_five_entries(self):
        """CANONICAL_AYANAMSHAS must have exactly 5 entries."""
        assert len(CANONICAL_AYANAMSHAS) == 5  # assertion 1

    def test_all_strings(self):
        """All entries must be non-empty strings."""
        for a in CANONICAL_AYANAMSHAS:
            assert isinstance(a, str) and len(a) > 0  # assertions 2-6 (5 entries)

    def test_expected_ids_present(self):
        """Verify known canonical IDs are in the list."""
        assert "lahiri" in CANONICAL_AYANAMSHAS  # assertion 7
        assert "kp" in CANONICAL_AYANAMSHAS  # assertion 8
        assert "raman" in CANONICAL_AYANAMSHAS  # assertion 9


# ── run_engine_parallel — stub path (pyjhora_adapter unavailable) ─────────────────

_BD = {"birth_date": "1984-02-05", "birth_time": "10:43", "lat": 20.27, "lon": 85.84, "tz_offset": 5.5}


class TestRunEngineParallelStubPath:
    """Tests for the stub code-path (no pyjhora_adapter available)."""

    def test_stub_returns_dict(self):
        """Stub path returns a dict."""
        with stub_sentinel():
            result = asyncio.run(run_engine_parallel("chart-1", CANONICAL_AYANAMSHAS, _BD))
        assert isinstance(result, dict)  # assertion 10

    def test_stub_returns_all_ayanamshas(self):
        """Stub path returns exactly len(ayanamshas) keys."""
        with stub_sentinel():
            result = asyncio.run(run_engine_parallel("chart-1", CANONICAL_AYANAMSHAS, _BD))
        assert len(result) == len(CANONICAL_AYANAMSHAS)  # assertion 11

    def test_stub_keys_match_ayanamshas(self):
        """Stub path keys are exactly the requested ayanamsha IDs."""
        with stub_sentinel():
            result = asyncio.run(run_engine_parallel("chart-1", CANONICAL_AYANAMSHAS, _BD))
        assert set(result.keys()) == set(CANONICAL_AYANAMSHAS)  # assertion 12

    def test_stub_values_not_none(self):
        """Stub path values are non-None dicts."""
        with stub_sentinel():
            result = asyncio.run(run_engine_parallel("chart-1", CANONICAL_AYANAMSHAS, _BD))
        for ayan, val in result.items():
            assert val is not None  # assertions 13-17 (5 entries)

    def test_stub_result_contains_chart_id(self):
        """Stub results embed the chart_id."""
        with stub_sentinel():
            result = asyncio.run(run_engine_parallel("chart-xyz", CANONICAL_AYANAMSHAS, _BD))
        for val in result.values():
            assert val.get("chart_id") == "chart-xyz"  # assertions 18-22


# ── run_engine_parallel — real engine path (injected fake) ────────────────────

class TestRunEngineParallelRealPath:
    def setup_method(self):
        inject_engine(make_fake_compute_chart())

    def teardown_method(self):
        remove_engine()

    def test_success_returns_dict(self):
        """All-success path returns a dict."""
        result = asyncio.run(run_engine_parallel("chart-2", CANONICAL_AYANAMSHAS, _BD))
        assert isinstance(result, dict)  # assertion 23

    def test_success_all_keys_present(self):
        """All-success path has all 5 ayanamsha keys."""
        result = asyncio.run(run_engine_parallel("chart-2", CANONICAL_AYANAMSHAS, _BD))
        assert set(result.keys()) == set(CANONICAL_AYANAMSHAS)  # assertion 24

    def test_success_no_none_values(self):
        """All-success path: no None values in result."""
        result = asyncio.run(run_engine_parallel("chart-2", CANONICAL_AYANAMSHAS, _BD))
        none_count = sum(1 for v in result.values() if v is None)
        assert none_count == 0  # assertion 25

    def test_success_exact_count(self):
        """Return value has exactly len(ayanamshas) entries."""
        result = asyncio.run(run_engine_parallel("chart-2", CANONICAL_AYANAMSHAS, _BD))
        assert len(result) == len(CANONICAL_AYANAMSHAS)  # assertion 26


class TestRunEngineParallelPartialFailure:
    def teardown_method(self):
        remove_engine()

    def test_partial_failure_returns_dict(self):
        """Partial failure still returns a dict."""
        inject_engine(make_fake_compute_chart(fail_on={"lahiri"}))
        result = asyncio.run(run_engine_parallel("chart-3", CANONICAL_AYANAMSHAS, _BD))
        assert isinstance(result, dict)  # assertion 27

    def test_partial_failure_all_keys_present(self):
        """Partial failure: all ayanamsha keys still present in result."""
        inject_engine(make_fake_compute_chart(fail_on={"lahiri"}))
        result = asyncio.run(run_engine_parallel("chart-3", CANONICAL_AYANAMSHAS, _BD))
        assert set(result.keys()) == set(CANONICAL_AYANAMSHAS)  # assertion 28

    def test_partial_failure_failed_ayanamsha_is_none(self):
        """The ayanamsha that failed must have None value."""
        inject_engine(make_fake_compute_chart(fail_on={"lahiri"}))
        result = asyncio.run(run_engine_parallel("chart-3", CANONICAL_AYANAMSHAS, _BD))
        assert result["lahiri"] is None  # assertion 29

    def test_partial_failure_successful_ayanamshas_have_values(self):
        """The ayanamshas that succeeded must have non-None values."""
        inject_engine(make_fake_compute_chart(fail_on={"lahiri"}))
        result = asyncio.run(run_engine_parallel("chart-3", CANONICAL_AYANAMSHAS, _BD))
        for ayan in CANONICAL_AYANAMSHAS:
            if ayan != "lahiri":
                assert result[ayan] is not None  # assertions 30-33

    def test_partial_failure_exact_count(self):
        """Partial failure: result has exactly len(ayanamshas) entries."""
        inject_engine(make_fake_compute_chart(fail_on={"kp", "raman"}))
        result = asyncio.run(run_engine_parallel("chart-3", CANONICAL_AYANAMSHAS, _BD))
        assert len(result) == len(CANONICAL_AYANAMSHAS)  # assertion 34


class TestRunEngineParallelTotalFailure:
    def teardown_method(self):
        remove_engine()

    def test_total_failure_does_not_raise(self):
        """Total failure: no exception propagated."""
        inject_engine(make_fake_compute_chart(fail_on=set(CANONICAL_AYANAMSHAS)))
        try:
            asyncio.run(run_engine_parallel("chart-4", CANONICAL_AYANAMSHAS, _BD))
            raised = False
        except Exception:
            raised = True
        assert not raised  # assertion 35

    def test_total_failure_returns_dict(self):
        """Total failure: return value is a dict."""
        inject_engine(make_fake_compute_chart(fail_on=set(CANONICAL_AYANAMSHAS)))
        result = asyncio.run(run_engine_parallel("chart-4", CANONICAL_AYANAMSHAS, _BD))
        assert isinstance(result, dict)  # assertion 36

    def test_total_failure_all_values_none(self):
        """Total failure: all values are None."""
        inject_engine(make_fake_compute_chart(fail_on=set(CANONICAL_AYANAMSHAS)))
        result = asyncio.run(run_engine_parallel("chart-4", CANONICAL_AYANAMSHAS, _BD))
        assert all(v is None for v in result.values())  # assertion 37

    def test_total_failure_all_keys_present(self):
        """Total failure: all ayanamsha keys still present."""
        inject_engine(make_fake_compute_chart(fail_on=set(CANONICAL_AYANAMSHAS)))
        result = asyncio.run(run_engine_parallel("chart-4", CANONICAL_AYANAMSHAS, _BD))
        assert set(result.keys()) == set(CANONICAL_AYANAMSHAS)  # assertion 38


# ── Concurrent execution: all ayanamshas attempted ────────────────────────────

class TestConcurrentExecution:
    def teardown_method(self):
        remove_engine()

    def test_all_ayanamshas_attempted_despite_first_failure(self):
        """
        Even if the first ayanamsha would fail, all others must be attempted
        and produce results.
        """
        called = []

        def tracking_compute(inputs, engine_version=None, ayanamsha_id=None, **kwargs):
            called.append(ayanamsha_id)
            if ayanamsha_id == CANONICAL_AYANAMSHAS[0]:
                raise RuntimeError("first fails")
            return {"ayanamsha_id": ayanamsha_id, "computed": True}

        inject_engine(tracking_compute)
        result = asyncio.run(run_engine_parallel("chart-5", CANONICAL_AYANAMSHAS, _BD))
        # All 5 must have been called
        assert len(called) == len(CANONICAL_AYANAMSHAS)  # assertion 39
        # 4 successful results
        successful = [v for v in result.values() if v is not None]
        assert len(successful) == len(CANONICAL_AYANAMSHAS) - 1  # assertion 40
        # Result still has all 5 keys
        assert len(result) == len(CANONICAL_AYANAMSHAS)  # assertion 41


# ── load_birth_data ────────────────────────────────────────────────────────────

class TestLoadBirthData:
    def _make_conn(self, row):
        """Return a mock DB connection that yields the given row."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.__enter__ = lambda s: mock_cursor
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_cursor.fetchone.return_value = row
        mock_conn.cursor.return_value = mock_cursor
        return mock_conn

    def setup_method(self):
        # Clear cache between tests
        import pipeline.build_chart as bc
        bc._chart_birth_data_cache.clear()

    def test_returns_dict(self):
        """load_birth_data returns a dict."""
        conn = self._make_conn(("1984-02-05", "10:43:00", 20.27, 85.84, 5.5))
        result = load_birth_data(conn, "chart-abc")
        assert isinstance(result, dict)  # assertion 42

    def test_required_keys_present(self):
        """load_birth_data result has all required keys."""
        conn = self._make_conn(("1984-02-05", "10:43:00", 20.27, 85.84, 5.5))
        result = load_birth_data(conn, "chart-abc")
        for key in ("birth_date", "birth_time", "lat", "lon", "tz_offset"):
            assert key in result  # assertions 43-47

    def test_lat_lon_are_floats(self):
        """lat and lon are floats."""
        conn = self._make_conn(("1984-02-05", "10:43:00", 20.27, 85.84, 5.5))
        result = load_birth_data(conn, "chart-abc")
        assert isinstance(result["lat"], float)  # assertion 48
        assert isinstance(result["lon"], float)  # assertion 49

    def test_tz_offset_is_float(self):
        """tz_offset is a float."""
        conn = self._make_conn(("1984-02-05", "10:43:00", 20.27, 85.84, 5.5))
        result = load_birth_data(conn, "chart-abc")
        assert isinstance(result["tz_offset"], float)  # assertion 50

    def test_none_lat_defaults_to_bhubaneswar(self):
        """None lat/lon defaults to Bhubaneswar coordinates."""
        conn = self._make_conn(("1984-02-05", "10:43:00", None, None, 5.5))
        result = load_birth_data(conn, "chart-def")
        assert result["lat"] == 20.27  # assertion 51
        assert result["lon"] == 85.84  # assertion 52

    def test_none_birth_time_defaults_to_midnight(self):
        """None birth_time defaults to '00:00'."""
        conn = self._make_conn(("1984-02-05", None, 20.27, 85.84, 5.5))
        result = load_birth_data(conn, "chart-ghi")
        assert result["birth_time"] == "00:00"  # assertion 53

    def test_none_tz_defaults_to_ist(self):
        """None tz_offset defaults to 5.5 (IST)."""
        conn = self._make_conn(("1984-02-05", "10:43:00", 20.27, 85.84, None))
        result = load_birth_data(conn, "chart-jkl")
        assert result["tz_offset"] == 5.5  # assertion 54

    def test_caching(self):
        """Second call for same chart_id does not hit DB again."""
        conn = self._make_conn(("1984-02-05", "10:43:00", 20.27, 85.84, 5.5))
        load_birth_data(conn, "chart-mno")
        load_birth_data(conn, "chart-mno")
        # cursor() called only once (for first fetch; second hits cache)
        assert conn.cursor.call_count == 1  # assertion 55

    def test_raises_for_missing_chart(self):
        """load_birth_data raises ValueError when chart_id not found."""
        conn = self._make_conn(None)
        with pytest.raises(ValueError, match="not found"):
            load_birth_data(conn, "nonexistent-chart")  # assertion 56 (exception raised)


# ── Return value invariants ────────────────────────────────────────────────────

class TestReturnValueInvariants:
    def teardown_method(self):
        remove_engine()

    def test_custom_ayanamsha_list(self):
        """Works with a custom (non-canonical) list of ayanamshas."""
        custom = ["lahiri", "raman"]
        inject_engine(make_fake_compute_chart())
        result = asyncio.run(run_engine_parallel("chart-6", custom, _BD))
        assert len(result) == len(custom)  # assertion 57
        assert set(result.keys()) == set(custom)  # assertion 58

    def test_result_values_are_dicts_on_success(self):
        """On full success each value is a dict."""
        inject_engine(make_fake_compute_chart())
        result = asyncio.run(run_engine_parallel("chart-7", CANONICAL_AYANAMSHAS, _BD))
        for val in result.values():
            assert isinstance(val, dict)  # assertions 59-63

    def test_result_never_raises(self):
        """run_engine_parallel never propagates engine exceptions."""
        inject_engine(make_fake_compute_chart(fail_on=set(CANONICAL_AYANAMSHAS)))
        try:
            asyncio.run(run_engine_parallel("chart-8", CANONICAL_AYANAMSHAS, _BD))
            no_exception = True
        except Exception:
            no_exception = False
        assert no_exception  # assertion 64
