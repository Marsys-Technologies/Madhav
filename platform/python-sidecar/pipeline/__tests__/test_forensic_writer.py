"""
test_forensic_writer.py — Contract tests for A2_forensic_render writer.

Stream F implementation landed: forensic_writer.write() is now real.

Test coverage:
  A. Constants (ASSET_ID, ASSET_LABEL)
  B. Dry-run (conn=None) returns rows_written=1 with non-empty content_md
  C. No-narration linter passes on rendered document
  D. All 13 section anchors present in rendered markdown
  E. Determinism: re-render same inputs → byte-identical markdown
     (excluding rendered_at field)
  F. DB error propagates (no silent swallow)
  G. shape_adapter smoke — to_render_input() returns expected top-level keys
"""
from __future__ import annotations

import re
import sys
import os
import unittest.mock as mock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pipeline.writers.forensic_writer import write, ASSET_ID, ASSET_LABEL, _SECTION_REGISTRY
from pipeline.render._chart_output_adapter import to_render_input


# ---------------------------------------------------------------------------
# Minimal chart_output fixture (empty data → all sections render as N/A,
# no NarrationViolation, all 13 anchors present)
# ---------------------------------------------------------------------------

_MINIMAL_CHART_OUTPUT: dict = {}

_TYPICAL_CHART_OUTPUT: dict = {
    "planets": [
        {
            "id": "sun", "name": "Sun",
            "degree_in_sign": 1.96, "sign": "Capricorn",
            "sign_id": 10, "nakshatra": "Uttara Ashadha", "pada": 1,
            "retrograde": False, "dignity_status": "debilitated",
            "house": 10, "longitude_deg": 291.96,
        },
        {
            "id": "moon", "name": "Moon",
            "degree_in_sign": 2.70, "sign": "Aquarius",
            "sign_id": 11, "nakshatra": "Purva Bhadrapada", "pada": 2,
            "retrograde": False, "dignity_status": "neutral",
            "house": 11, "longitude_deg": 302.70,
        },
    ],
    "houses": [
        {"house_number": h, "house_num": h, "sign": sign, "sign_id": i + 1,
         "sign_lord": lord}
        for h, (i, sign, lord) in enumerate([
            (0, "Aries", "Mars"), (1, "Taurus", "Venus"),
            (2, "Gemini", "Mercury"), (3, "Cancer", "Moon"),
            (4, "Leo", "Sun"), (5, "Virgo", "Mercury"),
            (6, "Libra", "Venus"), (7, "Scorpio", "Mars"),
            (8, "Sagittarius", "Jupiter"), (9, "Capricorn", "Saturn"),
            (10, "Aquarius", "Saturn"), (11, "Pisces", "Jupiter"),
        ], start=1)
    ],
    "panchanga": {
        "tithi": "Shukla Tritiya",
        "vara": "Ravivara",
        "nakshatra": "Purva Bhadrapada",
        "nakshatra_pada": 2,
        "yoga": "Shiva",
        "karana": "Garaja",
    },
    "dashas": {
        "system": "vimshottari",
        "mahadasha_sequence": [
            {"lord": "Saturn", "years": 19, "start_iso": "1984-02-05T00:00:00", "end_iso": "2003-02-05T00:00:00"},
            {"lord": "Mercury", "years": 17, "start_iso": "2003-02-05T00:00:00", "end_iso": "2020-02-05T00:00:00"},
        ],
    },
}


# ---------------------------------------------------------------------------
# A. Constants
# ---------------------------------------------------------------------------

class TestConstants:
    def test_asset_id(self):
        assert ASSET_ID == "A2_forensic_render"

    def test_asset_label_nonempty(self):
        assert ASSET_LABEL

    def test_section_registry_has_13(self):
        assert len(_SECTION_REGISTRY) == 13


# ---------------------------------------------------------------------------
# B. Dry-run returns 1
# ---------------------------------------------------------------------------

class TestDryRun:
    def test_empty_input_returns_one(self):
        result = write(
            build_id="test-build",
            chart_id="test-chart",
            ayanamsha_id="lahiri",
            chart_output=_MINIMAL_CHART_OUTPUT,
            conn=None,
        )
        assert result == 1, f"expected 1 (dry-run), got {result}"

    def test_typical_input_returns_one(self):
        result = write(
            build_id="test-build",
            chart_id="362f9f17-95a5-490b-a5a7-027d3e0efda0",
            ayanamsha_id="lahiri",
            chart_output=_TYPICAL_CHART_OUTPUT,
            conn=None,
        )
        assert result == 1

    def test_extra_kwarg_accepted(self):
        result = write(
            build_id="test-build",
            chart_id="test-chart",
            ayanamsha_id="kp",
            chart_output=_MINIMAL_CHART_OUTPUT,
            conn=None,
            extra={"context": "smoke"},
        )
        assert result == 1


# ---------------------------------------------------------------------------
# C. No-narration linter passes
# ---------------------------------------------------------------------------

class TestNarrationLinter:
    _FORBIDDEN = re.compile(
        r'\b(indicates?|suggests?|implies?|means?\s+that|denotes?|shows?|represents?|signifies?|symbolizes?)\b',
        re.IGNORECASE,
    )

    def _render(self, chart_output=None) -> str:
        """Return rendered markdown (dry-run)."""
        import importlib
        from pipeline.render.base_renderer import ForensicRenderer
        from pipeline.render._chart_output_adapter import to_render_input
        ri = to_render_input(chart_output or _MINIMAL_CHART_OUTPUT)
        renderer = ForensicRenderer()
        fw = importlib.import_module("pipeline.writers.forensic_writer")
        for title, mod_path, fn_name in fw._SECTION_REGISTRY:
            mod = importlib.import_module(mod_path)
            fn = getattr(mod, fn_name)
            renderer.register_section(title, fn)
        return renderer.render(ri, chart_id="x", ayanamsha_id="lahiri",
                               engine_version="pyjhora/1.0.0", build_id="x")

    def test_no_forbidden_verbs_minimal(self):
        md = self._render(_MINIMAL_CHART_OUTPUT)
        matches = self._FORBIDDEN.findall(md)
        assert not matches, f"narration verbs found: {set(matches)}"

    def test_no_forbidden_verbs_typical(self):
        md = self._render(_TYPICAL_CHART_OUTPUT)
        matches = self._FORBIDDEN.findall(md)
        assert not matches, f"narration verbs found: {set(matches)}"


# ---------------------------------------------------------------------------
# D. All 13 section anchors present
# ---------------------------------------------------------------------------

class TestSectionAnchors:
    def _render(self, chart_output=None) -> str:
        import importlib
        from pipeline.render.base_renderer import ForensicRenderer
        from pipeline.render._chart_output_adapter import to_render_input
        ri = to_render_input(chart_output or _MINIMAL_CHART_OUTPUT)
        renderer = ForensicRenderer()
        fw = importlib.import_module("pipeline.writers.forensic_writer")
        for title, mod_path, fn_name in fw._SECTION_REGISTRY:
            mod = importlib.import_module(mod_path)
            fn = getattr(mod, fn_name)
            renderer.register_section(title, fn)
        return renderer.render(ri, chart_id="x", ayanamsha_id="lahiri",
                               engine_version="pyjhora/1.0.0", build_id="x")

    def test_all_13_anchors_present(self):
        from pipeline.render.base_renderer import anchor_id
        fw_mod = __import__("pipeline.writers.forensic_writer",
                             fromlist=["_SECTION_REGISTRY"])
        md = self._render()
        for title, _, _ in fw_mod._SECTION_REGISTRY:
            aid = anchor_id(title)
            assert f"#{aid}" in md, (
                f"Anchor #{aid!r} (from section {title!r}) not found in markdown"
            )


# ---------------------------------------------------------------------------
# E. Determinism (excluding rendered_at timestamp)
# ---------------------------------------------------------------------------

class TestDeterminism:
    _TS_RE = re.compile(r'^rendered_at:.*$', re.MULTILINE)

    def _strip_ts(self, md: str) -> str:
        return self._TS_RE.sub("rendered_at: <STRIPPED>", md)

    def _render_once(self) -> str:
        import importlib
        from pipeline.render.base_renderer import ForensicRenderer
        from pipeline.render._chart_output_adapter import to_render_input
        ri = to_render_input(_TYPICAL_CHART_OUTPUT)
        renderer = ForensicRenderer()
        fw = importlib.import_module("pipeline.writers.forensic_writer")
        for title, mod_path, fn_name in fw._SECTION_REGISTRY:
            mod = importlib.import_module(mod_path)
            fn = getattr(mod, fn_name)
            renderer.register_section(title, fn)
        return renderer.render(ri, chart_id="362f9f17",
                               ayanamsha_id="lahiri",
                               engine_version="pyjhora/1.0.0",
                               build_id="det-test")

    def test_render_is_deterministic(self):
        md1 = self._strip_ts(self._render_once())
        md2 = self._strip_ts(self._render_once())
        assert md1 == md2, "Re-render produced different output (non-deterministic)"


# ---------------------------------------------------------------------------
# F. DB errors propagate (not swallowed)
# ---------------------------------------------------------------------------

class TestDbErrorPropagation:
    def test_db_error_raises(self):
        bad_conn = mock.MagicMock()
        bad_conn.cursor.side_effect = RuntimeError("simulated DB error")
        with pytest.raises(RuntimeError):
            write(
                build_id="error-test",
                chart_id="test-chart",
                ayanamsha_id="lahiri",
                chart_output=_MINIMAL_CHART_OUTPUT,
                conn=bad_conn,
            )


# ---------------------------------------------------------------------------
# G. Adapter smoke: to_render_input produces expected keys
# ---------------------------------------------------------------------------

class TestAdapterSmoke:
    def test_planets_has_degree_alias(self):
        inp = {"planets": [{"id": "sun", "degree_in_sign": 5.5, "sign": "Aries"}]}
        out = to_render_input(inp)
        planets = out.get("planets") or []
        assert any(p.get("degree") == 5.5 for p in planets)

    def test_houses_has_6_systems(self):
        inp = {"houses": [{"house_number": i, "sign": "Aries", "sign_lord": "Mars"}
                          for i in range(1, 13)]}
        out = to_render_input(inp)
        for sys_key in ("placidus", "whole_sign", "equal", "koch", "campanus", "porphyry"):
            assert sys_key in out["houses"], f"houses system {sys_key!r} missing"

    def test_panchanga_tithi_becomes_dict(self):
        inp = {"panchanga": {"tithi": "Shukla Tritiya", "vara": "Ravivara",
                             "nakshatra": "Ashwini", "yoga": "Vishkumbha",
                             "karana": "Bava"}}
        out = to_render_input(inp)
        assert isinstance(out["panchanga"]["tithi"], dict)
        assert out["panchanga"]["tithi"]["name"] == "Shukla Tritiya"

    def test_dashas_wraps_mahadasha_sequence(self):
        inp = {"dashas": {"system": "vimshottari", "mahadasha_sequence": [
            {"lord": "Saturn", "years": 19, "start_iso": "1984-02-05T00:00:00",
             "end_iso": "2003-02-05T00:00:00"},
        ]}}
        out = to_render_input(inp)
        assert "vimshottari" in out["dashas"]
        next_10 = out["dashas"]["vimshottari"].get("next_10_mahas", [])
        assert len(next_10) == 1
        assert next_10[0]["lord"] == "Saturn"

    def test_vargas_converts_list_to_dict(self):
        inp = {"vargas": {"D1": [
            {"name": "Lagna", "sign": "Aries", "sign_id": 1, "degree_in_sign": 20.0},
            {"name": "Sun", "sign": "Capricorn", "sign_id": 10, "degree_in_sign": 1.96},
        ]}}
        out = to_render_input(inp)
        d1 = out["vargas"]["D1"]
        assert isinstance(d1, dict), "D1 should be a dict after adaptation"
        assert "lagna" in d1
        assert "sun" in d1
        assert d1["lagna"]["sign"] == "Aries"
        assert d1["sun"]["sign"] == "Capricorn"
