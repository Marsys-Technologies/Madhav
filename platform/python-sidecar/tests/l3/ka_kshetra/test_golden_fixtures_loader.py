"""
tests/l3/ka_kshetra/test_golden_fixtures_loader.py — SAMPŪRTI-Δ2 V1 DHĀRĀ harness.

TDD FIRST COMMIT: this test is written BEFORE the fixture file exists and
BEFORE the generator runs.  Running it now must produce failures:

    - golden_fixtures/sampled_engine_v1_fixtures.json does not exist
    - load_golden_fixtures / get_fixture are therefore unavailable

After the second commit (generator run + loader written), every assertion here
must be GREEN without modification to this file.

What the assertions pin:

1. The file exists at the expected canonical path.
2. The top-level envelope carries the required schema keys.
3. ≥3 event classes are present.
4. ≥3 decade indices (0, 1, 2) are present per class.
5. Both canonical chart_ids are present.
6. Every fixture entry carries the required fields (windows, null_stats,
   engine, engine_version, segment_count, ln_lambda_at_peak).
7. The three required edge cases are represented:
     - suppression_active: at least one window with is_suppression_active=True
     - empty_class (ClassSkipped): at least one entry with skipped=True
     - zero_clock: at least one entry flagged zero_weight_clocks=True

Authority: SAMPŪRTI-Δ2 V1 spec (task brief).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Make the sidecar root importable from any working directory.
_SIDECAR_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_SIDECAR_ROOT))

_FIXTURE_DIR = Path(__file__).parent / 'golden_fixtures'
_FIXTURE_PATH = _FIXTURE_DIR / 'sampled_engine_v1_fixtures.json'

REQUIRED_EVENT_CLASSES = {'career_change', 'marriage', 'relocation'}
REQUIRED_DECADE_INDICES = {0, 1, 2}
REQUIRED_CHART_IDS = {
    '482012f1-710e-4a25-994a-93821f5871aa',
    'abhinandan-1c826d5a',
}
REQUIRED_FIXTURE_KEYS = {
    'chart_id',
    'event_class',
    'decade_start_days',
    'decade_end_days',
    'engine',
    'engine_version',
    'windows',
    'null_stats',
    'segment_count',
    'ln_lambda_at_peak',
}
REQUIRED_NULL_STATS_KEYS = {
    'replicate_count',
    'rank_of_real',
    'p_value',
    'null_expected_counts',
}
REQUIRED_WINDOW_KEYS = {
    'window_start',
    'window_end',
    'peak_days',
    'expected_count',
    'is_suppression_active',
}


# ── existence ─────────────────────────────────────────────────────────────────

class TestFixtureFileExists:
    def test_golden_fixtures_directory_exists(self):
        assert _FIXTURE_DIR.is_dir(), (
            f'golden_fixtures/ directory not found at {_FIXTURE_DIR}. '
            'Run generate_golden_fixtures.py to create it.'
        )

    def test_fixture_json_file_exists(self):
        assert _FIXTURE_PATH.is_file(), (
            f'Fixture file not found at {_FIXTURE_PATH}. '
            'Run generate_golden_fixtures.py to produce it.'
        )


# ── loader import ─────────────────────────────────────────────────────────────

@pytest.fixture(scope='module')
def fixtures_data():
    """Load the fixture file exactly once for all structural assertions."""
    if not _FIXTURE_PATH.is_file():
        pytest.skip('Fixture file not yet generated — run generate_golden_fixtures.py first')
    from tests.l3.ka_kshetra.golden_fixtures import load_golden_fixtures
    return load_golden_fixtures()


# ── top-level envelope ────────────────────────────────────────────────────────

class TestTopLevelEnvelope:
    def test_fixtures_key_present(self, fixtures_data):
        assert 'fixtures' in fixtures_data, 'Top-level key "fixtures" missing'

    def test_meta_key_present(self, fixtures_data):
        assert 'meta' in fixtures_data, 'Top-level key "meta" missing'

    def test_meta_engine_field(self, fixtures_data):
        assert fixtures_data['meta'].get('engine') == 'sampled'

    def test_meta_engine_version_field(self, fixtures_data):
        assert fixtures_data['meta'].get('engine_version') == 3

    def test_meta_generator_field_present(self, fixtures_data):
        assert 'generator' in fixtures_data['meta']

    def test_meta_generated_at_field_present(self, fixtures_data):
        assert 'generated_at' in fixtures_data['meta']


# ── coverage: classes, decades, charts ───────────────────────────────────────

class TestCoverage:
    def _all_fixtures(self, fixtures_data) -> list[dict]:
        return list(fixtures_data['fixtures'].values())

    def test_at_least_three_event_classes(self, fixtures_data):
        classes = {f['event_class'] for f in self._all_fixtures(fixtures_data)}
        assert REQUIRED_EVENT_CLASSES <= classes, (
            f'Missing event classes: {REQUIRED_EVENT_CLASSES - classes}'
        )

    def test_at_least_three_decade_indices(self, fixtures_data):
        decades = {f.get('decade_index') for f in self._all_fixtures(fixtures_data)}
        assert REQUIRED_DECADE_INDICES <= decades, (
            f'Missing decade indices: {REQUIRED_DECADE_INDICES - decades}'
        )

    def test_both_chart_ids_present(self, fixtures_data):
        charts = {f['chart_id'] for f in self._all_fixtures(fixtures_data)}
        assert REQUIRED_CHART_IDS <= charts, (
            f'Missing chart_ids: {REQUIRED_CHART_IDS - charts}'
        )

    def test_decade_windows_are_correct_ranges(self, fixtures_data):
        # Decade 0 = 0–3650 days, 1 = 3650–7300, 2 = 7300–10950
        expected_ranges = {
            0: (0, 3650),
            1: (3650, 7300),
            2: (7300, 10950),
        }
        for f in self._all_fixtures(fixtures_data):
            idx = f.get('decade_index')
            if idx in expected_ranges:
                lo, hi = expected_ranges[idx]
                assert f['decade_start_days'] == lo, (
                    f"decade_index={idx} start should be {lo}, got {f['decade_start_days']}"
                )
                assert f['decade_end_days'] == hi, (
                    f"decade_index={idx} end should be {hi}, got {f['decade_end_days']}"
                )


# ── per-fixture field structure ───────────────────────────────────────────────

class TestFixtureFieldStructure:
    def _all_fixtures(self, fixtures_data) -> list[dict]:
        return list(fixtures_data['fixtures'].values())

    def test_every_fixture_has_required_keys(self, fixtures_data):
        for key, entry in fixtures_data['fixtures'].items():
            missing = REQUIRED_FIXTURE_KEYS - set(entry.keys())
            assert not missing, (
                f'Fixture {key!r} is missing required keys: {missing}'
            )

    def test_engine_is_sampled_on_every_fixture(self, fixtures_data):
        for key, entry in fixtures_data['fixtures'].items():
            if entry.get('skipped'):
                continue   # skipped classes have no engine field
            assert entry.get('engine') == 'sampled', (
                f'Fixture {key!r} has engine={entry.get("engine")!r}, expected "sampled"'
            )

    def test_engine_version_is_3_on_every_fixture(self, fixtures_data):
        for key, entry in fixtures_data['fixtures'].items():
            if entry.get('skipped'):
                continue
            assert entry.get('engine_version') == 3, (
                f'Fixture {key!r} has engine_version={entry.get("engine_version")!r}, expected 3'
            )

    def test_windows_is_a_list(self, fixtures_data):
        for key, entry in fixtures_data['fixtures'].items():
            if entry.get('skipped'):
                continue
            assert isinstance(entry.get('windows'), list), (
                f'Fixture {key!r}: "windows" must be a list'
            )

    def test_every_window_has_required_keys(self, fixtures_data):
        for key, entry in fixtures_data['fixtures'].items():
            if entry.get('skipped'):
                continue
            for i, w in enumerate(entry.get('windows', [])):
                missing = REQUIRED_WINDOW_KEYS - set(w.keys())
                assert not missing, (
                    f'Fixture {key!r} window[{i}] missing keys: {missing}'
                )

    def test_null_stats_has_required_keys(self, fixtures_data):
        for key, entry in fixtures_data['fixtures'].items():
            if entry.get('skipped'):
                continue
            ns = entry.get('null_stats', {})
            missing = REQUIRED_NULL_STATS_KEYS - set(ns.keys())
            assert not missing, (
                f'Fixture {key!r} null_stats missing keys: {missing}'
            )

    def test_null_stats_replicate_count_is_256(self, fixtures_data):
        for key, entry in fixtures_data['fixtures'].items():
            if entry.get('skipped'):
                continue
            rc = entry.get('null_stats', {}).get('replicate_count')
            assert rc == 256, (
                f'Fixture {key!r} null_stats.replicate_count={rc!r}, expected 256'
            )

    def test_segment_count_is_positive_integer(self, fixtures_data):
        for key, entry in fixtures_data['fixtures'].items():
            if entry.get('skipped'):
                continue
            sc = entry.get('segment_count')
            assert isinstance(sc, int) and sc > 0, (
                f'Fixture {key!r} segment_count={sc!r} must be a positive int'
            )

    def test_ln_lambda_at_peak_is_finite_float(self, fixtures_data):
        import math
        for key, entry in fixtures_data['fixtures'].items():
            if entry.get('skipped'):
                continue
            v = entry.get('ln_lambda_at_peak')
            assert isinstance(v, float) and math.isfinite(v), (
                f'Fixture {key!r} ln_lambda_at_peak={v!r} must be a finite float'
            )


# ── edge cases ────────────────────────────────────────────────────────────────

class TestEdgeCases:
    def _all_fixtures(self, fixtures_data) -> list[dict]:
        return list(fixtures_data['fixtures'].values())

    def test_suppression_active_case_present(self, fixtures_data):
        """At least one window must have is_suppression_active=True."""
        found = any(
            w.get('is_suppression_active') is True
            for f in self._all_fixtures(fixtures_data)
            if not f.get('skipped')
            for w in f.get('windows', [])
        )
        assert found, (
            'No fixture window has is_suppression_active=True. '
            'The generator must include a vedha/obstruction scenario.'
        )

    def test_empty_class_skip_present(self, fixtures_data):
        """At least one entry must represent a ClassSkipped (no prior) scenario."""
        found = any(
            f.get('skipped') is True
            for f in self._all_fixtures(fixtures_data)
        )
        assert found, (
            'No fixture entry has skipped=True. '
            'The generator must include an empty-class (no brahma_class_priors) scenario.'
        )

    def test_zero_weight_clock_case_present(self, fixtures_data):
        """At least one entry must flag zero-weight clocks."""
        found = any(
            f.get('zero_weight_clocks') is True
            for f in self._all_fixtures(fixtures_data)
            if not f.get('skipped')
        )
        assert found, (
            'No fixture entry has zero_weight_clocks=True. '
            'The generator must include a scenario where all clocks have w_s=0.'
        )


# ── loader API ────────────────────────────────────────────────────────────────

class TestLoaderAPI:
    def test_get_fixture_returns_the_correct_entry(self, fixtures_data):
        from tests.l3.ka_kshetra.golden_fixtures import get_fixture
        # Grab any key from the fixture to verify round-trip
        some_key = next(iter(fixtures_data['fixtures']))
        chart_id, event_class, decade_idx_str = some_key.split(':', 2)
        decade_idx = int(decade_idx_str)
        entry = get_fixture(chart_id, event_class, decade_idx)
        assert entry['chart_id'] == chart_id
        assert entry['event_class'] == event_class
        assert entry['decade_index'] == decade_idx

    def test_get_fixture_raises_key_error_on_unknown(self):
        from tests.l3.ka_kshetra.golden_fixtures import get_fixture
        with pytest.raises(KeyError):
            get_fixture('no-such-chart', 'no-such-class', 999)
