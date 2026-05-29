"""
Tests for pipeline/render/planets_renderer.py (F-02)

Coverage:
- render_planets_section with empty chart_output (graceful, no crash)
- minimal planet dict → correct H2 header present
- no narration verbs in output
- all 9 classical body names appear in output
- retrograde flag renders correctly
- dignity renders for classical grahas, absent for outer bodies
- D9/D10 varga positions render
- all 23 bodies have an H2 section even if data missing
- _format_body: longitude formatting, nakshatra + pada, N/A fallbacks
"""
import sys
from pathlib import Path

import pytest

# Allow import from python-sidecar root
sys.path.insert(0, str(Path(__file__).parents[3]))

from pipeline.render.planets_renderer import (
    BODIES,
    BODY_DISPLAY_NAMES,
    render_planets_section,
    _format_body,
    _CLASSICAL_GRAHAS,
)
from pipeline.render.base_renderer import lint_narration, NarrationViolation


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MINIMAL_SUN = {
    "id": "sun",
    "longitude": 315.5,
    "latitude": 0.0,
    "speed": 1.01,
    "retrograde": False,
    "sign": "Aquarius",
    "sign_num": 10,
    "nakshatra": "Purva Bhadrapada",
    "pada": 4,
    "degree": 15.5,
    "house": 2,
    "dignity": "friendly",
    "varga_positions": {
        "D1": {"sign": "Aquarius", "lord": "Saturn"},
        "D9": {"sign": "Scorpio", "lord": "Mars"},
        "D10": {"sign": "Taurus", "lord": "Venus"},
    },
    "heliocentric_longitude": 134.2,
    "declination": -20.1,
    "right_ascension": 321.4,
}

MINIMAL_SATURN_RETRO = {
    "id": "saturn",
    "longitude": 220.7,
    "latitude": -2.1,
    "speed": -0.05,
    "retrograde": True,
    "sign": "Scorpio",
    "sign_num": 7,
    "nakshatra": "Anuradha",
    "pada": 2,
    "degree": 10.7,
    "house": 11,
    "dignity": "enemy",
    "varga_positions": {
        "D1": {"sign": "Scorpio", "lord": "Mars"},
        "D9": {"sign": "Libra", "lord": "Venus"},
        "D10": {"sign": "Gemini", "lord": "Mercury"},
    },
    "heliocentric_longitude": 218.0,
    "declination": -18.3,
    "right_ascension": 218.5,
}

MINIMAL_CHIRON = {
    "id": "chiron",
    "longitude": 90.3,
    "latitude": 6.2,
    "speed": 0.02,
    "retrograde": False,
    "sign": "Cancer",
    "sign_num": 3,
    "nakshatra": "Pushya",
    "pada": 1,
    "degree": 0.3,
    "house": 7,
    # No dignity for non-classical
    "varga_positions": {
        "D1": {"sign": "Cancer", "lord": "Moon"},
        "D9": {"sign": "Aries", "lord": "Mars"},
        "D10": {"sign": "Capricorn", "lord": "Saturn"},
    },
    "heliocentric_longitude": 89.9,
    "declination": 23.1,
    "right_ascension": 91.0,
}

FULL_CHART = {"planets": [MINIMAL_SUN, MINIMAL_SATURN_RETRO, MINIMAL_CHIRON]}


# ---------------------------------------------------------------------------
# Graceful degradation
# ---------------------------------------------------------------------------

class TestGracefulDegradation:
    def test_empty_chart_output_does_not_crash(self):
        result = render_planets_section({})
        assert isinstance(result, str)

    def test_empty_planets_list_does_not_crash(self):
        result = render_planets_section({"planets": []})
        assert isinstance(result, str)

    def test_none_planets_does_not_crash(self):
        result = render_planets_section({"planets": None})
        assert isinstance(result, str)

    def test_empty_output_still_has_all_23_h2_sections(self):
        result = render_planets_section({})
        # Every body ID should have an H2 anchor
        for body_id in BODIES:
            assert f"{{#{body_id}}}" in result, f"Missing anchor for body: {body_id}"

    def test_missing_body_data_emits_na(self):
        result = render_planets_section({})
        # With no data, N/A should appear
        assert "N/A" in result

    def test_partial_body_dict_no_crash(self):
        result = render_planets_section({"planets": [{"id": "moon"}]})
        assert isinstance(result, str)
        assert "Moon" in result


# ---------------------------------------------------------------------------
# H2 header presence
# ---------------------------------------------------------------------------

class TestH2Headers:
    def test_sun_h2_header_present(self):
        result = _format_body(MINIMAL_SUN)
        assert "## Sun {#sun}" in result

    def test_saturn_h2_header_present(self):
        result = _format_body(MINIMAL_SATURN_RETRO)
        assert "## Saturn {#saturn}" in result

    def test_chiron_h2_header_present(self):
        result = _format_body(MINIMAL_CHIRON)
        assert "## Chiron {#chiron}" in result

    def test_unknown_body_id_still_gets_header(self):
        result = _format_body({"id": "unknown_body"})
        assert "## " in result

    def test_all_9_classical_names_in_full_render(self):
        classical_names = [
            "Sun", "Moon", "Mars", "Mercury", "Jupiter",
            "Venus", "Saturn", "Rahu", "Ketu",
        ]
        result = render_planets_section({})
        for name in classical_names:
            assert name in result, f"Missing classical body name: {name}"

    def test_outer_planet_names_present(self):
        outer = ["Ceres", "Pallas", "Juno", "Vesta", "Chiron",
                 "Uranus", "Neptune", "Pluto", "Sedna", "Eris"]
        result = render_planets_section({})
        for name in outer:
            assert name in result, f"Missing outer body name: {name}"


# ---------------------------------------------------------------------------
# No narration verbs
# ---------------------------------------------------------------------------

class TestNoNarration:
    def test_single_body_passes_lint(self):
        result = _format_body(MINIMAL_SUN)
        lint_narration(result, "sun")  # must not raise

    def test_full_render_passes_lint(self):
        result = render_planets_section(FULL_CHART)
        lint_narration(result, "planets_section")  # must not raise

    def test_empty_render_passes_lint(self):
        result = render_planets_section({})
        lint_narration(result, "empty_planets")

    def test_forbidden_verbs_not_in_output(self):
        import re
        from pipeline.render.base_renderer import FORBIDDEN_PATTERN
        result = render_planets_section(FULL_CHART)
        matches = FORBIDDEN_PATTERN.findall(result)
        assert matches == [], f"Narration verbs found: {matches}"


# ---------------------------------------------------------------------------
# Retrograde flag
# ---------------------------------------------------------------------------

class TestRetrogradeFl:
    def test_retrograde_false_renders_no(self):
        result = _format_body(MINIMAL_SUN)
        assert "| Retrograde | No |" in result

    def test_retrograde_true_renders_yes(self):
        result = _format_body(MINIMAL_SATURN_RETRO)
        assert "| Retrograde | Yes |" in result

    def test_retrograde_missing_renders_na(self):
        result = _format_body({"id": "sun", "sign": "Aries"})
        assert "| Retrograde | N/A |" in result


# ---------------------------------------------------------------------------
# Dignity
# ---------------------------------------------------------------------------

class TestDignity:
    def test_dignity_present_for_classical_graha(self):
        result = _format_body(MINIMAL_SUN)
        assert "| Dignity | Friendly |" in result

    def test_dignity_enemy_renders(self):
        result = _format_body(MINIMAL_SATURN_RETRO)
        assert "| Dignity | Enemy |" in result

    def test_dignity_absent_for_chiron(self):
        result = _format_body(MINIMAL_CHIRON)
        assert "Dignity" not in result

    def test_dignity_absent_for_uranus(self):
        result = _format_body({"id": "uranus", "sign": "Aries"})
        assert "Dignity" not in result

    def test_dignity_absent_for_mean_lilith(self):
        result = _format_body({"id": "mean_lilith", "sign": "Taurus"})
        assert "Dignity" not in result

    def test_dignity_missing_value_renders_na(self):
        body = {**MINIMAL_SUN, "dignity": None}
        result = _format_body(body)
        assert "| Dignity | N/A |" in result

    def test_rahu_has_dignity_slot(self):
        """Rahu is in _CLASSICAL_GRAHAS so it gets a dignity row."""
        body = {"id": "rahu", "dignity": "neutral"}
        result = _format_body(body)
        assert "Dignity" in result

    def test_ketu_has_dignity_slot(self):
        body = {"id": "ketu", "dignity": "exaltation"}
        result = _format_body(body)
        assert "Dignity" in result


# ---------------------------------------------------------------------------
# Varga positions
# ---------------------------------------------------------------------------

class TestVargaPositions:
    def test_d1_renders_correctly(self):
        result = _format_body(MINIMAL_SUN)
        assert "D1 (Rashi)" in result
        assert "Aquarius" in result
        assert "Saturn" in result

    def test_d9_renders_correctly(self):
        result = _format_body(MINIMAL_SUN)
        assert "D9 (Navamsa)" in result
        assert "Scorpio" in result
        assert "Mars" in result

    def test_d10_renders_correctly(self):
        result = _format_body(MINIMAL_SUN)
        assert "D10 (Dasamsa)" in result
        assert "Taurus" in result
        assert "Venus" in result

    def test_varga_table_header_present(self):
        result = _format_body(MINIMAL_SUN)
        assert "**Varga Positions**" in result

    def test_missing_varga_positions_renders_na(self):
        body = {"id": "sun", "sign": "Aries"}
        result = _format_body(body)
        assert "**Varga Positions**" in result
        assert "N/A" in result

    def test_partial_varga_positions_renders_gracefully(self):
        body = {
            "id": "moon",
            "varga_positions": {
                "D1": {"sign": "Taurus", "lord": "Venus"},
                # D9 and D10 missing
            }
        }
        result = _format_body(body)
        assert "D1 (Rashi)" in result
        assert "D9 (Navamsa)" in result  # row still present
        assert "D10 (Dasamsa)" in result


# ---------------------------------------------------------------------------
# Longitude formatting
# ---------------------------------------------------------------------------

class TestLongitudeFormatting:
    def test_longitude_sign_present(self):
        result = _format_body(MINIMAL_SUN)
        assert "Aquarius" in result

    def test_longitude_degree_formatted(self):
        result = _format_body(MINIMAL_SUN)
        # 15.5 degrees → 15°30'
        assert "15°30'" in result

    def test_longitude_missing_renders_na(self):
        result = _format_body({"id": "sun"})
        assert "N/A" in result

    def test_nakshatra_pada_present(self):
        result = _format_body(MINIMAL_SUN)
        assert "Purva Bhadrapada Pada 4" in result

    def test_nakshatra_missing_renders_na(self):
        result = _format_body({"id": "sun"})
        # Without nakshatra the row should show N/A
        assert "N/A" in result

    def test_latitude_formatted(self):
        result = _format_body(MINIMAL_SUN)
        assert "| Latitude | 0.000° |" in result

    def test_speed_formatted(self):
        result = _format_body(MINIMAL_SUN)
        assert "| Speed | 1.010°/day |" in result

    def test_negative_declination_formatted(self):
        result = _format_body(MINIMAL_SUN)
        assert "| Declination | -20.100° |" in result

    def test_right_ascension_formatted(self):
        result = _format_body(MINIMAL_SUN)
        assert "| Right Ascension | 321.400° |" in result

    def test_heliocentric_longitude_formatted(self):
        result = _format_body(MINIMAL_SUN)
        assert "| Heliocentric Lon | 134.200° |" in result


# ---------------------------------------------------------------------------
# Body count and ordering
# ---------------------------------------------------------------------------

class TestBodyCountAndOrder:
    def test_bodies_list_has_25_entries(self):
        # Spec says "23 bodies" but enumerates: 9 classical + 4 node variants
        # + 2 Liliths + 10 outer/asteroids = 25.  Enumerated list governs.
        assert len(BODIES) == 25

    def test_body_display_names_covers_all_bodies(self):
        for body_id in BODIES:
            assert body_id in BODY_DISPLAY_NAMES, f"Missing display name for: {body_id}"

    def test_classical_grahas_set_size(self):
        assert len(_CLASSICAL_GRAHAS) == 9

    def test_sun_is_first_body(self):
        assert BODIES[0] == "sun"

    def test_eris_is_last_body(self):
        assert BODIES[-1] == "eris"

    def test_full_render_body_order_preserved(self):
        result = render_planets_section({})
        positions = {body_id: result.find(f"{{#{body_id}}}") for body_id in BODIES}
        ordered = sorted(positions.items(), key=lambda x: x[1])
        ordered_ids = [k for k, _ in ordered]
        assert ordered_ids == BODIES, "Bodies rendered out of canonical order"

    def test_render_with_reordered_input_still_uses_canonical_order(self):
        """Even if planets list is in reverse order, output order is canonical."""
        planets = [
            {"id": "eris", "sign": "Aries"},
            {"id": "sun", "sign": "Aquarius", "degree": 15.0,
             "nakshatra": "PB", "pada": 1},
        ]
        result = render_planets_section({"planets": planets})
        sun_pos = result.find("{#sun}")
        eris_pos = result.find("{#eris}")
        assert sun_pos < eris_pos, "Sun should appear before Eris"


# ---------------------------------------------------------------------------
# Integration: render_planets_section with full data
# ---------------------------------------------------------------------------

class TestRenderPlanetsSection:
    def test_returns_string(self):
        assert isinstance(render_planets_section(FULL_CHART), str)

    def test_sun_data_in_output(self):
        result = render_planets_section(FULL_CHART)
        assert "Purva Bhadrapada" in result
        assert "Friendly" in result

    def test_saturn_retrograde_in_output(self):
        result = render_planets_section(FULL_CHART)
        assert "| Retrograde | Yes |" in result

    def test_chiron_no_dignity_in_output(self):
        result = render_planets_section(FULL_CHART)
        # Chiron block should not have a Dignity row
        chiron_start = result.find("{#chiron}")
        # Find the next body anchor after Chiron
        next_anchor = result.find("## ", chiron_start + 1)
        chiron_block = result[chiron_start:next_anchor] if next_anchor != -1 else result[chiron_start:]
        assert "Dignity" not in chiron_block

    def test_varga_positions_in_output(self):
        result = render_planets_section(FULL_CHART)
        assert "D9 (Navamsa)" in result
        assert "D10 (Dasamsa)" in result
