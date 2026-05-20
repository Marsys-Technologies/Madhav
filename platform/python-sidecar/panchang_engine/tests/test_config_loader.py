"""
test_config_loader.py — Tests for config_loader.py (Phase 4C-6-S2).

6 test cases:
  1. load_muhurat_weights returns well-formed dict
  2. get_weights_for_event for each of the 6 MVP events
  3. Cache hits — second call returns same object (lru_cache active)
  4. custom config_path override — load from a temp file
  5. Unknown event falls back to defaults
  6. invalidate_weights_cache allows re-read

AC.4C6S2.2 — Loader works; get_weights_for_event("vivah") returns merged dict;
             caching verified.
"""
import pytest
import tempfile
from pathlib import Path


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clear_cache():
    """Ensure a fresh cache state for each test."""
    from panchang_engine.config_loader import invalidate_weights_cache
    invalidate_weights_cache()
    yield
    invalidate_weights_cache()  # Clean up after test too


@pytest.fixture()
def custom_config(tmp_path) -> Path:
    """Write a minimal custom YAML config for override testing."""
    content = """
defaults:
  tithi: 0.10
  nakshatra: 0.50
  vara: 0.10
  yoga: 0.10
  planet: 0.10
  native: 0.10
  avoid_penalty: 1.0

events:
  vivah:
    nakshatra: 0.60
    tithi: 0.10
    vara: 0.05
    yoga: 0.10
    planet: 0.10
    native: 0.05
    avoid_penalty: 1.0
"""
    p = tmp_path / "test_weights.yaml"
    p.write_text(content)
    return p


# ---------------------------------------------------------------------------
# §1 — load_muhurat_weights
# ---------------------------------------------------------------------------

class TestLoadMuhuratWeights:
    """load_muhurat_weights returns the raw YAML dict."""

    def test_returns_dict_with_defaults_and_events(self):
        """Default config has 'defaults' and 'events' keys."""
        from panchang_engine.config_loader import load_muhurat_weights
        raw = load_muhurat_weights()
        assert isinstance(raw, dict)
        assert "defaults" in raw, "Expected 'defaults' key"
        assert "events" in raw, "Expected 'events' key"

    def test_defaults_has_all_required_factor_keys(self):
        """defaults block contains all 7 weight keys."""
        from panchang_engine.config_loader import load_muhurat_weights
        raw = load_muhurat_weights()
        required = {"tithi", "nakshatra", "vara", "yoga", "planet", "native", "avoid_penalty"}
        missing = required - set(raw["defaults"].keys())
        assert not missing, f"Missing keys in defaults: {missing}"

    def test_avoid_penalty_is_1_in_defaults(self):
        """avoid_penalty must be 1.0 in defaults (hard constraint per master plan §4.4.1)."""
        from panchang_engine.config_loader import load_muhurat_weights
        raw = load_muhurat_weights()
        assert raw["defaults"]["avoid_penalty"] == 1.0

    def test_all_6_events_present(self):
        """All 6 MVP events have explicit override entries."""
        from panchang_engine.config_loader import load_muhurat_weights
        raw = load_muhurat_weights()
        events = raw["events"]
        mvp_events = {
            "vivah", "griha_pravesh", "vyapara",
            "yatra", "property_purchase", "mantra_initiation"
        }
        missing = mvp_events - set(events.keys())
        assert not missing, f"Missing events in YAML: {missing}"


# ---------------------------------------------------------------------------
# §2 — get_weights_for_event for each MVP event
# ---------------------------------------------------------------------------

class TestGetWeightsForEvent:
    """get_weights_for_event returns merged weight dict per event."""

    @pytest.mark.parametrize("event", [
        "vivah",
        "griha_pravesh",
        "vyapara",
        "yatra",
        "property_purchase",
        "mantra_initiation",
    ])
    def test_each_event_returns_full_dict(self, event):
        """Every MVP event returns a dict with all 7 weight keys."""
        from panchang_engine.config_loader import get_weights_for_event
        w = get_weights_for_event(event)
        assert isinstance(w, dict)
        required = {"tithi", "nakshatra", "vara", "yoga", "planet", "native", "avoid_penalty"}
        missing = required - set(w.keys())
        assert not missing, f"Event '{event}' missing keys: {missing}"

    @pytest.mark.parametrize("event", [
        "vivah",
        "griha_pravesh",
        "vyapara",
        "yatra",
        "property_purchase",
        "mantra_initiation",
    ])
    def test_each_event_avoid_penalty_is_1(self, event):
        """avoid_penalty must be 1.0 for every event (hard constraint)."""
        from panchang_engine.config_loader import get_weights_for_event
        w = get_weights_for_event(event)
        assert w["avoid_penalty"] == 1.0, (
            f"Event '{event}' has avoid_penalty={w['avoid_penalty']} — must be 1.0"
        )

    @pytest.mark.parametrize("event", [
        "vivah",
        "griha_pravesh",
        "vyapara",
        "yatra",
        "property_purchase",
        "mantra_initiation",
    ])
    def test_each_event_weights_sum_to_expected(self, event):
        """Per-event positive contributor weights sum to ~1.0 (within 0.001)."""
        from panchang_engine.config_loader import get_weights_for_event
        w = get_weights_for_event(event)
        factors = ["tithi", "nakshatra", "vara", "yoga", "planet", "native"]
        total = sum(w[f] for f in factors)
        assert abs(total - 1.0) < 0.001, (
            f"Event '{event}' weights sum to {total:.4f}, expected ~1.0"
        )

    def test_vivah_nakshatra_weight_is_0_40(self):
        """Vivah event has nakshatra=0.40 (per-event override; classical priority)."""
        from panchang_engine.config_loader import get_weights_for_event
        w = get_weights_for_event("vivah")
        assert w["nakshatra"] == pytest.approx(0.40, abs=0.001)

    def test_property_purchase_yoga_weight_is_highest(self):
        """property_purchase has the highest yoga weight of any event (Tripushkar/Dwipushkar)."""
        from panchang_engine.config_loader import get_weights_for_event
        yoga_weights = {}
        for evt in ["vivah", "griha_pravesh", "vyapara", "yatra", "property_purchase", "mantra_initiation"]:
            yoga_weights[evt] = get_weights_for_event(evt)["yoga"]
        assert yoga_weights["property_purchase"] == max(yoga_weights.values()), (
            f"property_purchase should have highest yoga weight; got {yoga_weights}"
        )

    def test_mantra_initiation_native_weight_is_highest(self):
        """mantra_initiation has the highest native overlay weight of any event."""
        from panchang_engine.config_loader import get_weights_for_event
        native_weights = {}
        for evt in ["vivah", "griha_pravesh", "vyapara", "yatra", "property_purchase", "mantra_initiation"]:
            native_weights[evt] = get_weights_for_event(evt)["native"]
        assert native_weights["mantra_initiation"] == max(native_weights.values()), (
            f"mantra_initiation should have highest native weight; got {native_weights}"
        )


# ---------------------------------------------------------------------------
# §3 — Cache behaviour
# ---------------------------------------------------------------------------

class TestCacheBehaviour:
    """lru_cache is active; second call returns same raw dict object."""

    def test_second_call_returns_same_object(self):
        """load_muhurat_weights is cached — same dict returned on repeated calls."""
        from panchang_engine.config_loader import load_muhurat_weights
        raw1 = load_muhurat_weights()
        raw2 = load_muhurat_weights()
        assert raw1 is raw2, "Expected same object from lru_cache on second call"

    def test_cache_info_shows_hit_after_two_calls(self):
        """After two calls, lru_cache shows at least 1 hit."""
        from panchang_engine.config_loader import load_muhurat_weights
        load_muhurat_weights()  # prime
        load_muhurat_weights()  # hit
        info = load_muhurat_weights.cache_info()
        assert info.hits >= 1, f"Expected cache hits; got {info}"

    def test_invalidate_then_reread(self):
        """invalidate_weights_cache resets hits to 0; next call re-reads from disk."""
        from panchang_engine.config_loader import load_muhurat_weights, invalidate_weights_cache
        raw1 = load_muhurat_weights()
        invalidate_weights_cache()
        info = load_muhurat_weights.cache_info()
        assert info.currsize == 0, f"Cache not empty after invalidate; got {info}"
        raw2 = load_muhurat_weights()
        # Content should be identical even after re-read
        assert raw2["defaults"] == raw1["defaults"]


# ---------------------------------------------------------------------------
# §4 — Custom config_path override
# ---------------------------------------------------------------------------

class TestCustomConfigPath:
    """Passing config_path loads from a different file (test isolation)."""

    def test_custom_path_returns_custom_weights(self, custom_config):
        """Custom config_path loads weights from the supplied file."""
        from panchang_engine.config_loader import load_muhurat_weights
        raw = load_muhurat_weights(config_path=custom_config)
        assert raw["defaults"]["nakshatra"] == pytest.approx(0.50, abs=0.001), (
            "Expected custom nakshatra default 0.50"
        )

    def test_custom_path_get_weights_for_event(self, custom_config):
        """get_weights_for_event uses the custom config_path when supplied."""
        from panchang_engine.config_loader import get_weights_for_event
        w = get_weights_for_event("vivah", config_path=custom_config)
        assert w["nakshatra"] == pytest.approx(0.60, abs=0.001), (
            f"Expected custom vivah nakshatra 0.60, got {w['nakshatra']}"
        )

    def test_custom_path_does_not_pollute_default_cache(self, custom_config):
        """Loading from custom_path does not affect the default config cache."""
        from panchang_engine.config_loader import load_muhurat_weights
        # Load custom first
        custom_raw = load_muhurat_weights(config_path=custom_config)
        assert custom_raw["defaults"]["nakshatra"] == pytest.approx(0.50, abs=0.001)
        # Load default — should still be the bundled config
        default_raw = load_muhurat_weights()
        assert default_raw["defaults"]["nakshatra"] == pytest.approx(0.30, abs=0.001), (
            f"Default cache was polluted by custom load; nakshatra={default_raw['defaults']['nakshatra']}"
        )

    def test_nonexistent_path_raises_file_not_found(self, tmp_path):
        """FileNotFoundError raised for a path that does not exist."""
        from panchang_engine.config_loader import load_muhurat_weights
        missing = tmp_path / "no_such_file.yaml"
        with pytest.raises(FileNotFoundError):
            load_muhurat_weights(config_path=missing)


# ---------------------------------------------------------------------------
# §5 — Unknown event falls back to defaults
# ---------------------------------------------------------------------------

class TestUnknownEventFallback:
    """Unknown events inherit defaults; no KeyError raised."""

    def test_unknown_event_returns_defaults(self):
        """An event not in the YAML events block returns the defaults."""
        from panchang_engine.config_loader import get_weights_for_event, load_muhurat_weights
        w = get_weights_for_event("some_future_event")
        defaults = load_muhurat_weights()["defaults"]
        # All keys should match defaults
        for key in ["tithi", "nakshatra", "vara", "yoga", "planet", "native", "avoid_penalty"]:
            assert w[key] == defaults[key], (
                f"Key '{key}': expected default {defaults[key]}, got {w[key]}"
            )

    def test_unknown_event_no_exception(self):
        """get_weights_for_event does not raise for unknown event."""
        from panchang_engine.config_loader import get_weights_for_event
        try:
            w = get_weights_for_event("completely_unknown")
            assert isinstance(w, dict)
        except Exception as e:
            pytest.fail(f"get_weights_for_event raised for unknown event: {e}")
