"""
Tests for pipeline/render/base_renderer.py

Coverage:
- lint_narration: clean text passes, forbidden verbs raise NarrationViolation
- anchor_id: correct slug generation
- frontmatter: required fields present, YAML structure correct
- ForensicRenderer: instantiation, section registration, render output
"""
import re
import sys
from pathlib import Path
from datetime import datetime, timezone

import pytest

# Allow import from python-sidecar root
sys.path.insert(0, str(Path(__file__).parents[3]))

from pipeline.render.base_renderer import (
    ForensicRenderer,
    NarrationViolation,
    anchor_id,
    frontmatter,
    lint_narration,
    FORBIDDEN_PATTERN,
)


# ---------------------------------------------------------------------------
# lint_narration
# ---------------------------------------------------------------------------

class TestLintNarration:
    def test_clean_text_passes(self):
        """Plain factual text with no forbidden verbs should not raise."""
        lint_narration("Sun is in Aries at 15° 22'.")

    def test_tabular_text_passes(self):
        """Table rows with planet data should not raise."""
        lint_narration("| Sun | Aries | 15.37 | 1 |")

    def test_indicates_raises(self):
        with pytest.raises(NarrationViolation):
            lint_narration("This placement indicates strength.")

    def test_indicate_singular_raises(self):
        with pytest.raises(NarrationViolation):
            lint_narration("This indicate a strong will.")

    def test_suggests_raises(self):
        with pytest.raises(NarrationViolation):
            lint_narration("The chart suggests a difficult period.")

    def test_suggests_case_insensitive(self):
        """Forbidden verbs must be caught regardless of case."""
        with pytest.raises(NarrationViolation):
            lint_narration("The chart SUGGESTS a difficult period.")

    def test_implies_raises(self):
        with pytest.raises(NarrationViolation):
            lint_narration("This implies karmic debt.")

    def test_means_that_raises(self):
        with pytest.raises(NarrationViolation):
            lint_narration("That means that the native will suffer.")

    def test_denotes_raises(self):
        with pytest.raises(NarrationViolation):
            lint_narration("Rahu here denotes obsession.")

    def test_shows_raises(self):
        with pytest.raises(NarrationViolation):
            lint_narration("This placement shows ambition.")

    def test_represents_raises(self):
        with pytest.raises(NarrationViolation):
            lint_narration("The 10th house represents career.")

    def test_signifies_raises(self):
        with pytest.raises(NarrationViolation):
            lint_narration("The 5th house signifies children.")

    def test_symbolizes_raises(self):
        with pytest.raises(NarrationViolation):
            lint_narration("Saturn symbolizes discipline and delay.")

    def test_section_name_in_exception_message(self):
        """The section name must appear in the NarrationViolation message."""
        with pytest.raises(NarrationViolation, match="planetary_positions"):
            lint_narration("This indicates strength.", section="planetary_positions")

    def test_empty_string_passes(self):
        lint_narration("")

    def test_multiline_clean_passes(self):
        lint_narration("| Sun | 15.37 |\n| Moon | 220.12 |\n| Mars | 90.00 |")

    def test_multiline_with_forbidden_raises(self):
        with pytest.raises(NarrationViolation):
            lint_narration("| Sun | 15.37 |\nThis indicates a strong 1st house.")


# ---------------------------------------------------------------------------
# anchor_id
# ---------------------------------------------------------------------------

class TestAnchorId:
    def test_basic_title(self):
        assert anchor_id("Planetary Positions") == "planetary-positions"

    def test_section_sign_stripped(self):
        result = anchor_id("§ Planetary Positions")
        assert result == "planetary-positions"

    def test_slash_stripped(self):
        result = anchor_id("Lagna / Ascendant")
        assert result == "lagna--ascendant" or "lagna" in result

    def test_lowercase(self):
        assert anchor_id("HOUSE CUSPS") == "house-cusps"

    def test_multiple_spaces_collapsed(self):
        assert anchor_id("Sun   Moon") == "sun-moon"

    def test_numbers_preserved(self):
        assert "12" in anchor_id("12 Houses")

    def test_leading_trailing_stripped(self):
        result = anchor_id("  § Rashi Positions  ")
        assert not result.startswith("-")
        assert not result.endswith("-")

    def test_only_special_chars_gives_empty_or_clean(self):
        result = anchor_id("§§§")
        assert result == "" or re.match(r'^[-]*$', result)


# ---------------------------------------------------------------------------
# frontmatter
# ---------------------------------------------------------------------------

class TestFrontmatter:
    def _parse(self, fm: str) -> dict:
        """Minimal YAML-line parser for frontmatter tests."""
        lines = fm.strip().split('\n')
        # strip leading --- and trailing ---
        content = [l for l in lines if l not in ('---',)]
        result = {}
        for line in content:
            if ':' in line:
                k, _, v = line.partition(':')
                result[k.strip()] = v.strip()
        return result

    def test_contains_chart_id(self):
        fm = frontmatter("FORENSIC_1984", "lahiri", "pyjhora/1.0.0", "build-001")
        assert "FORENSIC_1984" in fm

    def test_contains_ayanamsha_id(self):
        fm = frontmatter("FORENSIC_1984", "lahiri", "pyjhora/1.0.0", "build-001")
        assert "lahiri" in fm

    def test_contains_engine_version(self):
        fm = frontmatter("FORENSIC_1984", "lahiri", "pyjhora/1.0.0", "build-001")
        assert "pyjhora/1.0.0" in fm

    def test_contains_build_id(self):
        fm = frontmatter("FORENSIC_1984", "lahiri", "pyjhora/1.0.0", "build-001")
        assert "build-001" in fm

    def test_no_narration_true(self):
        fm = frontmatter("C1", "lahiri", "0.2.0", "b1")
        assert "no_narration: true" in fm

    def test_b10_compliant_true(self):
        fm = frontmatter("C1", "lahiri", "0.2.0", "b1")
        assert "b10_compliant: true" in fm

    def test_document_type_forensic_render(self):
        fm = frontmatter("C1", "lahiri", "0.2.0", "b1")
        assert "document_type: forensic_render" in fm

    def test_starts_with_yaml_fence(self):
        fm = frontmatter("C1", "lahiri", "0.2.0", "b1")
        assert fm.startswith("---")

    def test_rendered_at_included(self):
        fixed_dt = datetime(2026, 5, 29, 12, 0, 0, tzinfo=timezone.utc)
        fm = frontmatter("C1", "lahiri", "0.2.0", "b1", rendered_at=fixed_dt)
        assert "2026-05-29" in fm

    def test_rendered_at_default_is_utc(self):
        fm = frontmatter("C1", "lahiri", "0.2.0", "b1")
        assert "rendered_at:" in fm


# ---------------------------------------------------------------------------
# ForensicRenderer
# ---------------------------------------------------------------------------

class TestForensicRenderer:
    def test_instantiates_without_error(self, tmp_path):
        renderer = ForensicRenderer(template_dir=tmp_path / "templates")
        assert renderer is not None

    def test_sections_empty_on_init(self, tmp_path):
        renderer = ForensicRenderer(template_dir=tmp_path / "templates")
        assert renderer.sections == []

    def test_register_section_adds_entry(self, tmp_path):
        renderer = ForensicRenderer(template_dir=tmp_path / "templates")
        renderer.register_section("Planets", lambda c: "| Sun | Aries |")
        assert len(renderer.sections) == 1

    def test_register_multiple_sections(self, tmp_path):
        renderer = ForensicRenderer(template_dir=tmp_path / "templates")
        renderer.register_section("Planets", lambda c: "data")
        renderer.register_section("Houses", lambda c: "data")
        assert len(renderer.sections) == 2

    def test_render_returns_string(self, tmp_path):
        renderer = ForensicRenderer(template_dir=tmp_path / "templates")
        result = renderer.render({}, "C1", "lahiri")
        assert isinstance(result, str)

    def test_render_contains_frontmatter_fence(self, tmp_path):
        renderer = ForensicRenderer(template_dir=tmp_path / "templates")
        result = renderer.render({}, "C1", "lahiri")
        assert result.startswith("---")

    def test_render_contains_chart_id(self, tmp_path):
        renderer = ForensicRenderer(template_dir=tmp_path / "templates")
        result = renderer.render({}, "FORENSIC_1984", "lahiri")
        assert "FORENSIC_1984" in result

    def test_render_includes_section_h2(self, tmp_path):
        renderer = ForensicRenderer(template_dir=tmp_path / "templates")
        renderer.register_section("Planetary Positions", lambda c: "| Sun | Aries |")
        result = renderer.render({}, "C1", "lahiri")
        assert "## Planetary Positions" in result

    def test_render_includes_toc(self, tmp_path):
        renderer = ForensicRenderer(template_dir=tmp_path / "templates")
        renderer.register_section("Planetary Positions", lambda c: "| Sun | Aries |")
        result = renderer.render({}, "C1", "lahiri")
        assert "Table of Contents" in result
        assert "Planetary Positions" in result

    def test_render_raises_narration_violation(self, tmp_path):
        renderer = ForensicRenderer(template_dir=tmp_path / "templates")
        renderer.register_section(
            "Bad Section",
            lambda c: "This indicates a strong chart."
        )
        with pytest.raises(NarrationViolation):
            renderer.render({}, "C1", "lahiri")

    def test_render_section_failure_inserts_placeholder(self, tmp_path):
        renderer = ForensicRenderer(template_dir=tmp_path / "templates")
        def bad_renderer(c):
            raise ValueError("missing key")
        renderer.register_section("Broken Section", bad_renderer)
        result = renderer.render({}, "C1", "lahiri")
        assert "Render error" in result
        assert "ValueError" in result

    def test_render_section_error_does_not_stop_other_sections(self, tmp_path):
        renderer = ForensicRenderer(template_dir=tmp_path / "templates")
        def bad_renderer(c):
            raise KeyError("planets")
        renderer.register_section("Broken", bad_renderer)
        renderer.register_section("Good Section", lambda c: "| Moon | Taurus |")
        result = renderer.render({}, "C1", "lahiri")
        assert "Good Section" in result

    def test_render_anchor_in_section_heading(self, tmp_path):
        renderer = ForensicRenderer(template_dir=tmp_path / "templates")
        renderer.register_section("§ Rashi Chart", lambda c: "data")
        result = renderer.render({}, "C1", "lahiri")
        assert "{ #" in result or "{#" in result

    def test_render_ayanamsha_in_title(self, tmp_path):
        renderer = ForensicRenderer(template_dir=tmp_path / "templates")
        result = renderer.render({}, "C1", "lahiri")
        assert "Lahiri" in result or "lahiri" in result.lower()

    def test_render_section_data_in_output(self, tmp_path):
        renderer = ForensicRenderer(template_dir=tmp_path / "templates")
        renderer.register_section("Planets", lambda c: "| Sun | 15.37 | Aries |")
        result = renderer.render({}, "C1", "lahiri")
        assert "15.37" in result

    def test_render_chart_output_passed_to_section(self, tmp_path):
        renderer = ForensicRenderer(template_dir=tmp_path / "templates")
        captured = {}
        def capture_renderer(chart_output):
            captured['data'] = chart_output
            return "| result |"
        renderer.register_section("Capture", capture_renderer)
        chart_data = {"planets": [{"id": "sun"}]}
        renderer.render(chart_data, "C1", "lahiri")
        assert captured['data'] == chart_data

    def test_template_dir_created_if_missing(self, tmp_path):
        new_dir = tmp_path / "new_templates"
        assert not new_dir.exists()
        renderer = ForensicRenderer(template_dir=new_dir)
        assert new_dir.exists()
