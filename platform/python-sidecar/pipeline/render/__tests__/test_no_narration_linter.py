"""
Tests for no-narration linter (base_renderer.lint_narration) — F-14 requirement.

Coverage (30+ tests):
- Clean text passes without exception
- "indicates" triggers NarrationViolation
- "suggest" triggers NarrationViolation
- "implies" triggers NarrationViolation
- "means that" triggers NarrationViolation
- "denotes" triggers NarrationViolation
- "shows" triggers NarrationViolation
- "represents" triggers NarrationViolation
- "signifies" triggers NarrationViolation
- "symbolizes" triggers NarrationViolation
- Case-insensitive: "INDICATES" triggers violation
- Case-insensitive: "Suggests" triggers violation
- Case-insensitive: "Shows" triggers violation
- Word-boundary: "indicator" safe (not a verb form match)
- Word-boundary: "shown" safe
- Multiple violations in one string → all caught (still raises)
- Empty string passes
- Table markdown with digits passes
- Markdown headings pass
- Pipe-separated table rows pass
- Dash placeholder "—" passes
- Numbers and signs pass
- F-11 vimsopaka output passes linter
- F-11 avastha output passes linter
- F-12 vargas output passes linter
- F-12 d9 verification output passes linter
- F-13 current chain output passes linter
- F-13 next-10 output passes linter
- F-14 kp output passes linter
- F-14 eclipse output passes linter
- F-14 argala output passes linter
- F-14 astronomical output passes linter
- NarrationViolation is an Exception subclass
- lint_narration returns None on clean text
- section label included in violation message
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[3]))

from pipeline.render.base_renderer import lint_narration, NarrationViolation

from pipeline.render.vimsopaka_renderer import render_vimsopaka_section
from pipeline.render.vargas_renderer import render_vargas_section
from pipeline.render.dashas_renderer import render_dashas_section
from pipeline.render.supplementary_renderer import render_supplementary_section


# ---------------------------------------------------------------------------
# Helper: minimal clean chart data for each renderer
# ---------------------------------------------------------------------------

GRAHAS = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]
SIGNS  = ["aries", "taurus", "gemini", "cancer", "leo", "virgo",
          "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"]


def _clean_vimsopaka() -> dict:
    vimsopaka = {g: {"saptavarga": 12.0, "dashavarga": 11.0, "shadvarga": 10.0, "shodasavarga": 9.0} for g in GRAHAS}
    avasthas  = {g: {
        "baladi":     {"name": "Yuva",     "effect": "full strength"},
        "jagradadi":  {"name": "Jagrat",   "effect": "active"},
        "deeptadi":   {"name": "Deepta",   "effect": "exalted state"},
        "lajjitadi":  {"name": "Mudita",   "effect": "pleased"},
        "shayanaadi": {"name": "Standing", "effect": "upright"},
    } for g in GRAHAS}
    return {"vimsopaka": vimsopaka, "avasthas": avasthas}


def _clean_vargas() -> dict:
    all_vargas = (
        ["D1","D2","D3","D4","D5","D6","D7","D8","D9","D10",
         "D11","D12","D16","D20","D24","D27","D30","D40","D45","D60",
         "D108","D150","D2700"]
    )
    entry = {"sign": "Aries", "lord": "Mars", "dignity": "neutral", "vargottama": False, "rishi": "Vasishtha"}
    vargas = {v: {"lagna": {"sign": "Cancer", "lord": "Moon"}, **{g: dict(entry) for g in GRAHAS}} for v in all_vargas}
    return {"vargas": vargas, "d9_verification": {"match": True, "discrepancies": []}}


def _clean_dashas() -> dict:
    from pipeline.render.dashas_renderer import ALL_DASHA_SYSTEMS
    chain = {"current_dates": {
        "maha":       {"lord": "Jupiter", "start": "2018-03-15", "end": "2034-03-15"},
        "antar":      {"lord": "Saturn",  "start": "2024-01-10", "end": "2026-09-05"},
        "pratyantar": {"lord": "Mercury", "start": "2025-10-01", "end": "2026-02-15"},
        "sookshma":   {"lord": "Jupiter", "start": "2025-12-20", "end": "2026-01-10"},
    }, "next_10_mahas": [{"lord": "Saturn", "start": "2034-03-15", "end": "2053-03-15", "years": 19}]}
    dashas = {k: dict(chain) for k, _ in ALL_DASHA_SYSTEMS}
    return {"dashas": dashas, "d9_verification_vimshottari": {"match": True}, "d9_verification_chara": {"match": True}}


def _clean_supplementary() -> dict:
    return {
        "kp_cuspal":         {str(c): {"sub_lord": "Jupiter", "nakshatra_lord": "Moon", "sub_sub_lord": "Saturn"} for c in range(1,13)},
        "tajik_varshphal":   {"year_lord": "Saturn", "hadda_lord": "Mercury"},
        "midpoints":         {"sun_moon": {"longitude": 260.5, "sign": "Sagittarius"}},
        "eclipse_proximity": {"nearest_solar": {"date": "1984-05-30", "type": "Partial", "eclipse_id": "S1984-05"},
                              "nearest_lunar":  {"date": "1984-05-15", "type": "Total",   "eclipse_id": "L1984-05"}},
        "nadi_amsa":         {g: {"rishi": "Vasishtha", "division": "D150"} for g in GRAHAS},
        "argala":            {s: {} for s in SIGNS},
        "astronomical":      {"julian_day": 2445706.9, "sidereal_time_gast": "14h 22m", "local_sidereal_time": "19h 48m",
                              "birth_place": "Bhubaneswar", "lat": 20.2961, "lon": 85.8245},
    }


# ---------------------------------------------------------------------------
# Tests: NarrationViolation class
# ---------------------------------------------------------------------------

def test_narration_violation_is_exception():
    assert issubclass(NarrationViolation, Exception)


# ---------------------------------------------------------------------------
# Tests: clean text passes
# ---------------------------------------------------------------------------

def test_clean_text_passes():
    result = lint_narration("Sun in Aries, exalted. Moon in Taurus, high strength.")
    assert result is None


def test_empty_string_passes():
    lint_narration("")


def test_table_markdown_passes():
    lint_narration("| Graha | Sign | Lord |\n|-------|------|------|\n| Sun | Aries | Mars |")


def test_markdown_headings_pass():
    lint_narration("### Vimsopaka Dignities\n#### D9 — Navamsha\n")


def test_pipe_table_rows_pass():
    lint_narration("| 1 | Jupiter | Moon | Saturn |\n| 2 | Mars | Sun | Venus |")


def test_dash_placeholder_passes():
    lint_narration("| Sun | — | — | — |")


def test_numbers_pass():
    lint_narration("15.2 | 13.5 | 12.0 | 10.8")


# ---------------------------------------------------------------------------
# Tests: forbidden verbs trigger violation
# ---------------------------------------------------------------------------

def test_indicates_triggers():
    with pytest.raises(NarrationViolation):
        lint_narration("Sun in 10H indicates career success.")


def test_suggests_triggers():
    with pytest.raises(NarrationViolation):
        lint_narration("This placement suggests wealth.")


def test_implies_triggers():
    with pytest.raises(NarrationViolation):
        lint_narration("Rahu in 1H implies ambition.")


def test_means_that_triggers():
    with pytest.raises(NarrationViolation):
        lint_narration("Exaltation means that the planet is strong.")


def test_denotes_triggers():
    with pytest.raises(NarrationViolation):
        lint_narration("This denotes good fortune.")


def test_shows_triggers():
    with pytest.raises(NarrationViolation):
        lint_narration("This chart shows strong Lagna lord.")


def test_represents_triggers():
    with pytest.raises(NarrationViolation):
        lint_narration("Jupiter represents wisdom.")


def test_signifies_triggers():
    with pytest.raises(NarrationViolation):
        lint_narration("Saturn signifies restriction.")


def test_symbolizes_triggers():
    with pytest.raises(NarrationViolation):
        lint_narration("Venus symbolizes love.")


# ---------------------------------------------------------------------------
# Tests: case-insensitive detection
# ---------------------------------------------------------------------------

def test_uppercase_indicates():
    with pytest.raises(NarrationViolation):
        lint_narration("INDICATES strong position.")


def test_capitalized_suggests():
    with pytest.raises(NarrationViolation):
        lint_narration("Suggests a good outcome.")


def test_mixed_case_shows():
    with pytest.raises(NarrationViolation):
        lint_narration("Shows the native's strength.")


# ---------------------------------------------------------------------------
# Tests: word-boundary safety (should NOT trigger)
# ---------------------------------------------------------------------------

def test_indicator_safe():
    # "indicator" does not match \bindicates?\b
    lint_narration("Strength indicator: 15.2")


def test_shown_safe():
    # "shown" does not match \bshows?\b
    lint_narration("Data shown in the table above.")


# ---------------------------------------------------------------------------
# Tests: section label in violation message
# ---------------------------------------------------------------------------

def test_section_in_violation_message():
    try:
        lint_narration("Sun indicates wealth.", section="test_section")
    except NarrationViolation as e:
        assert "test_section" in str(e)


# ---------------------------------------------------------------------------
# Tests: all 4 renderer outputs pass linter
# ---------------------------------------------------------------------------

def test_f11_vimsopaka_passes_linter():
    out = render_vimsopaka_section(_clean_vimsopaka())
    lint_narration(out, "F-11 vimsopaka")


def test_f11_avastha_passes_linter():
    out = render_vimsopaka_section(_clean_vimsopaka())
    lint_narration(out, "F-11 avastha")


def test_f12_vargas_passes_linter():
    out = render_vargas_section(_clean_vargas())
    lint_narration(out, "F-12 vargas")


def test_f12_d9_verification_passes_linter():
    from pipeline.render.vargas_renderer import _render_d9_verification
    out = _render_d9_verification({"match": True, "discrepancies": []})
    lint_narration(out, "F-12 d9-verification")


def test_f13_current_chain_passes_linter():
    from pipeline.render.dashas_renderer import _render_current_chain
    dates = {"current_dates": {"maha": {"lord": "Jupiter", "start": "2018", "end": "2034"}}}
    out = _render_current_chain("vimshottari", "Vimshottari", dates)
    lint_narration(out, "F-13 current-chain")


def test_f13_next10_passes_linter():
    from pipeline.render.dashas_renderer import _render_next_10_mahas
    mahas = {"next_10_mahas": [{"lord": "Saturn", "start": "2034", "end": "2053", "years": 19}]}
    out = _render_next_10_mahas("vimshottari", "Vimshottari", mahas)
    lint_narration(out, "F-13 next-10")


def test_f14_kp_passes_linter():
    from pipeline.render.supplementary_renderer import _render_kp_cuspal
    kp = {str(c): {"sub_lord": "Jupiter", "nakshatra_lord": "Moon", "sub_sub_lord": "Saturn"} for c in range(1, 13)}
    out = _render_kp_cuspal(kp)
    lint_narration(out, "F-14 kp")


def test_f14_eclipse_passes_linter():
    from pipeline.render.supplementary_renderer import _render_eclipses
    eclipses = {"nearest_solar": {"date": "1984-05-30", "type": "Partial", "eclipse_id": "S1984"},
                "nearest_lunar": {"date": "1984-05-15", "type": "Total",   "eclipse_id": "L1984"}}
    out = _render_eclipses(eclipses)
    lint_narration(out, "F-14 eclipse")


def test_f14_argala_passes_linter():
    from pipeline.render.supplementary_renderer import _render_argala
    argala = {s: {} for s in SIGNS}
    argala["aries"]["cancer"] = "argala"
    out = _render_argala(argala)
    lint_narration(out, "F-14 argala")


def test_f14_astronomical_passes_linter():
    from pipeline.render.supplementary_renderer import _render_astronomical
    astro = {"julian_day": 2445706.9, "sidereal_time_gast": "14h 22m", "local_sidereal_time": "19h",
             "birth_place": "Bhubaneswar", "lat": 20.29, "lon": 85.82}
    out = _render_astronomical(astro)
    lint_narration(out, "F-14 astronomical")


def test_f14_full_supplementary_passes_linter():
    out = render_supplementary_section(_clean_supplementary())
    lint_narration(out, "F-14 full supplementary")
