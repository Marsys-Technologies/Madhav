"""
Tests for pipeline/render/houses_renderer.py (F-03)

Coverage:
- Empty chart_output → no crash, returns string
- All 12 houses present in output
- All 6 house system names appear in comparison table
- A1–A12 present in arudhas section
- No narration verbs (lint_narration passes)
- Co-lord renders correctly when present
- Occupants list renders as comma-separated
- Missing house data → N/A gracefully
- Missing arudha data → N/A gracefully
- Placidus default detail table rendered
- House detail table header present
"""
import sys
from pathlib import Path

import pytest

# Allow import from python-sidecar root
sys.path.insert(0, str(Path(__file__).parents[3]))

from pipeline.render.houses_renderer import (
    HOUSE_SYSTEMS,
    HOUSE_SYSTEM_LABELS,
    ARUDHA_NAMES,
    render_houses_section,
    _render_house_details,
    _render_house_system_comparison,
    _render_arudhas,
)
from pipeline.render.base_renderer import lint_narration, NarrationViolation


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_placidus_house(num: int, sign: str, lord: str, **kwargs) -> dict:
    """Build a minimal placidus house entry."""
    h = {
        "house": num,
        "cusp_longitude": 10.0 + (num - 1) * 30,
        "sign": sign,
        "lord": lord,
        "co_lord": kwargs.get("co_lord"),
        "nakshatra": kwargs.get("nakshatra", "Ashwini"),
        "pada": kwargs.get("pada", 1),
        "occupying_planets": kwargs.get("occupying_planets", []),
    }
    return h


# 12 houses for Placidus
_SIGNS = [
    "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius",
    "Capricorn", "Aquarius", "Pisces", "Aries", "Taurus", "Gemini",
]
_LORDS = [
    "Moon", "Sun", "Mercury", "Venus", "Mars", "Jupiter",
    "Saturn", "Saturn", "Jupiter", "Mars", "Venus", "Mercury",
]

FULL_PLACIDUS: list[dict] = [
    _make_placidus_house(i + 1, _SIGNS[i], _LORDS[i]) for i in range(12)
]

# Override house 1 with co-lord and occupants
FULL_PLACIDUS[0] = _make_placidus_house(
    1, "Cancer", "Moon",
    co_lord=None,
    nakshatra="Pushya",
    pada=2,
    occupying_planets=["jupiter", "mercury"],
)

# Scorpio house (5) gets a co-lord (Ketu in KP)
FULL_PLACIDUS[4] = _make_placidus_house(
    5, "Scorpio", "Mars",
    co_lord="Ketu",
    nakshatra="Anuradha",
    pada=3,
    occupying_planets=[],
)


def _make_system_houses(sign_offset: int = 0) -> list[dict]:
    """Build a 12-house list for a non-Placidus system (signs shifted)."""
    signs = _SIGNS[sign_offset:] + _SIGNS[:sign_offset]
    return [{"house": i + 1, "sign": signs[i]} for i in range(12)]


FULL_HOUSES: dict = {
    "placidus": FULL_PLACIDUS,
    "whole_sign": _make_system_houses(0),
    "equal": _make_system_houses(1),
    "koch": _make_system_houses(2),
    "campanus": _make_system_houses(3),
    "porphyry": _make_system_houses(4),
}

FULL_ARUDHAS: dict = {
    "A1": {"sign": "Capricorn", "longitude": 280.0, "lord": "Saturn"},
    "A2": {"sign": "Leo", "longitude": 130.0, "lord": "Sun"},
    "A3": {"sign": "Aries", "longitude": 10.0, "lord": "Mars"},
    "A4": {"sign": "Virgo", "longitude": 160.0, "lord": "Mercury"},
    "A5": {"sign": "Taurus", "longitude": 40.0, "lord": "Venus"},
    "A6": {"sign": "Sagittarius", "longitude": 250.0, "lord": "Jupiter"},
    "A7": {"sign": "Cancer", "longitude": 100.0, "lord": "Moon"},
    "A8": {"sign": "Aquarius", "longitude": 310.0, "lord": "Saturn"},
    "A9": {"sign": "Pisces", "longitude": 340.0, "lord": "Jupiter"},
    "A10": {"sign": "Gemini", "longitude": 70.0, "lord": "Mercury"},
    "A11": {"sign": "Libra", "longitude": 190.0, "lord": "Venus"},
    "A12": {"sign": "Scorpio", "longitude": 220.0, "lord": "Mars"},
}

FULL_CHART_OUTPUT: dict = {
    "houses": FULL_HOUSES,
    "arudhas": FULL_ARUDHAS,
}


# ---------------------------------------------------------------------------
# Tests — render_houses_section
# ---------------------------------------------------------------------------

class TestRenderHousesSectionEmpty:
    def test_empty_chart_output_returns_string(self):
        result = render_houses_section({})
        assert isinstance(result, str)

    def test_empty_chart_output_no_crash(self):
        """Must not raise."""
        render_houses_section({})

    def test_empty_chart_output_no_narration(self):
        result = render_houses_section({})
        lint_narration(result, "houses")  # must not raise

    def test_empty_output_has_section_headers(self):
        result = render_houses_section({})
        assert "House Details" in result
        assert "House System Comparison" in result
        assert "Arudha Padas" in result


class TestRenderHousesSectionFull:
    def test_returns_string(self):
        assert isinstance(render_houses_section(FULL_CHART_OUTPUT), str)

    def test_no_narration_verbs(self):
        result = render_houses_section(FULL_CHART_OUTPUT)
        lint_narration(result, "houses")

    def test_all_12_houses_in_output(self):
        result = render_houses_section(FULL_CHART_OUTPUT)
        for h in range(1, 13):
            # each house number appears as a table cell
            assert f"| {h} |" in result, f"House {h} missing from output"

    def test_all_6_system_labels_in_comparison(self):
        result = render_houses_section(FULL_CHART_OUTPUT)
        for label in HOUSE_SYSTEM_LABELS.values():
            assert label in result, f"House system label '{label}' missing"

    def test_all_arudhas_a1_to_a12_in_output(self):
        result = render_houses_section(FULL_CHART_OUTPUT)
        for name in ARUDHA_NAMES:
            assert f"| {name} |" in result, f"{name} missing from arudha table"

    def test_co_lord_present_renders(self):
        """House 5 (Scorpio) has co_lord=Ketu; must appear in output."""
        result = render_houses_section(FULL_CHART_OUTPUT)
        assert "Ketu" in result

    def test_co_lord_absent_renders_dash(self):
        """House 1 has no co_lord; cell must render as em-dash."""
        result = _render_house_details(FULL_PLACIDUS)
        # House 1 row — check em-dash for co_lord column
        # Row: | 1 | Cancer | Moon | — | Pushya Pada 2 | ...
        assert "| 1 | Cancer | Moon | — |" in result

    def test_occupants_comma_separated(self):
        """House 1 has jupiter + mercury — must appear comma-separated."""
        result = render_houses_section(FULL_CHART_OUTPUT)
        assert "Jupiter, Mercury" in result

    def test_empty_occupants_renders_dash(self):
        """House 5 has no occupants — must render em-dash."""
        result = _render_house_details(FULL_PLACIDUS)
        # House 5 row ends with | — |
        lines = result.split("\n")
        house5_lines = [l for l in lines if l.startswith("| 5 |")]
        assert len(house5_lines) == 1
        assert house5_lines[0].endswith("| — |")

    def test_arudha_sign_and_lord(self):
        result = render_houses_section(FULL_CHART_OUTPUT)
        assert "Capricorn" in result
        assert "Saturn" in result

    def test_nakshatra_and_pada_rendered(self):
        result = render_houses_section(FULL_CHART_OUTPUT)
        assert "Pushya Pada 2" in result

    def test_comparison_table_header(self):
        result = _render_house_system_comparison(FULL_HOUSES)
        assert "Placidus" in result
        assert "Whole Sign" in result
        assert "Equal" in result
        assert "Koch" in result
        assert "Campanus" in result
        assert "Porphyry" in result

    def test_comparison_has_12_data_rows(self):
        result = _render_house_system_comparison(FULL_HOUSES)
        lines = [l for l in result.split("\n") if l.startswith("| ")]
        # header row + separator... separator doesn't start with "| "
        # so count rows starting with "| 1 |" through "| 12 |"
        data_rows = [l for l in lines if not l.startswith("| House")]
        assert len(data_rows) == 12


# ---------------------------------------------------------------------------
# Tests — missing / partial data
# ---------------------------------------------------------------------------

class TestMissingData:
    def test_missing_houses_key(self):
        result = render_houses_section({"arudhas": FULL_ARUDHAS})
        assert isinstance(result, str)
        # All house rows should be N/A
        assert "N/A" in result

    def test_missing_arudhas_key(self):
        result = render_houses_section({"houses": FULL_HOUSES})
        assert isinstance(result, str)
        # All arudha rows should be N/A
        assert "N/A" in result

    def test_missing_single_house_system(self):
        """If one house system is absent, comparison still renders."""
        partial_houses = {k: v for k, v in FULL_HOUSES.items() if k != "campanus"}
        result = render_houses_section({"houses": partial_houses, "arudhas": FULL_ARUDHAS})
        assert "Campanus" in result  # header still present
        assert "N/A" in result  # missing cells degrade to N/A

    def test_missing_specific_arudha(self):
        partial_arudhas = {k: v for k, v in FULL_ARUDHAS.items() if k != "A7"}
        result = render_houses_section({"houses": FULL_HOUSES, "arudhas": partial_arudhas})
        assert "| A7 |" in result
        # A7 row should have N/A sign + lord
        lines = result.split("\n")
        a7_lines = [l for l in lines if l.startswith("| A7 |")]
        assert len(a7_lines) == 1
        assert "N/A" in a7_lines[0]

    def test_house_missing_nakshatra(self):
        houses = [
            {"house": i + 1, "sign": _SIGNS[i], "lord": _LORDS[i]}
            for i in range(12)
        ]
        result = _render_house_details(houses)
        assert isinstance(result, str)
        assert "N/A" in result  # nakshatra missing → N/A

    def test_fully_empty_arudhas_dict(self):
        result = _render_arudhas({})
        for name in ARUDHA_NAMES:
            assert f"| {name} |" in result
        assert "N/A" in result

    def test_no_narration_on_partial_data(self):
        result = render_houses_section({"houses": {}, "arudhas": {}})
        lint_narration(result, "houses")  # must not raise


# ---------------------------------------------------------------------------
# Tests — HOUSE_SYSTEMS / ARUDHA_NAMES constants
# ---------------------------------------------------------------------------

class TestConstants:
    def test_house_systems_length(self):
        assert len(HOUSE_SYSTEMS) == 6

    def test_arudha_names_length(self):
        assert len(ARUDHA_NAMES) == 12

    def test_arudha_names_format(self):
        for i, name in enumerate(ARUDHA_NAMES, start=1):
            assert name == f"A{i}"

    def test_all_house_systems_have_labels(self):
        for sys_key in HOUSE_SYSTEMS:
            assert sys_key in HOUSE_SYSTEM_LABELS
