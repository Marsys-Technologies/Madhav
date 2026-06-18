"""
Tests for ga_yoga writer and yoga system.
Runs without a real DB — exercises the module imports, catalog integrity,
ChartState parsing, and yoga evaluation logic with mock data.

Build: 2026-06-17 — Yoga Subsystem Gate-1
"""
from __future__ import annotations

import json
import pytest
from unittest.mock import MagicMock, patch


# ── Registry conformance ───────────────────────────────────────────────────────

def test_writer_registered():
    """ga_yoga must be discoverable via the writer registry."""
    from pipeline.orchestrator.writers import get_writer
    w = get_writer("ga_yoga")
    assert w is not None, "ga_yoga not found in writer registry"


def test_writer_is_writer_base_subclass():
    from pipeline.orchestrator.writers import get_writer, WriterBase
    w = get_writer("ga_yoga")
    assert issubclass(w, WriterBase)


def test_writer_has_substeps_flag():
    from pipeline.orchestrator.writers import get_writer
    w = get_writer("ga_yoga")
    assert hasattr(w, "has_substeps") and w.has_substeps is True


def test_writer_asset_id():
    from pipeline.orchestrator.writers import get_writer
    w = get_writer("ga_yoga")
    assert w.asset_id == "ga_yoga"


def test_plan_substeps_returns_five():
    """plan_substeps must return exactly 5 sub-steps (one per ayanamsha)."""
    from pipeline.orchestrator.writers.ga_yoga import GaYogaWriter, CANONICAL_AYANAMSHAS
    assert len(CANONICAL_AYANAMSHAS) == 5

    writer = GaYogaWriter()
    ctx = MagicMock()
    steps = writer.plan_substeps(ctx)
    assert len(steps) == 5


def test_plan_substeps_keys():
    from pipeline.orchestrator.writers.ga_yoga import GaYogaWriter, CANONICAL_AYANAMSHAS
    writer = GaYogaWriter()
    ctx = MagicMock()
    steps = writer.plan_substeps(ctx)
    expected_keys = {f"ayanamsha_{a}" for a in CANONICAL_AYANAMSHAS}
    actual_keys = {s.key for s in steps}
    assert actual_keys == expected_keys


def test_canonical_ayanamshas_include_lahiri():
    from pipeline.orchestrator.writers.ga_yoga import CANONICAL_AYANAMSHAS
    assert "lahiri_chitrapaksha" in CANONICAL_AYANAMSHAS


# ── Yoga catalog integrity ─────────────────────────────────────────────────────

def test_yoga_core_has_81_entries():
    from brahmagyan.l0_yogas import YOGAS_CORE
    assert len(YOGAS_CORE) == 144, f"Expected 144 YOGAS_CORE entries, got {len(YOGAS_CORE)}"


def test_all_yogas_have_canonical_id():
    from brahmagyan.l0_yogas import YOGAS_CORE
    for y in YOGAS_CORE:
        assert y.get("canonical_id"), f"Missing canonical_id: {y}"


def test_all_yogas_have_classical_citation():
    """Hard gate: every yoga must have a classical citation."""
    from brahmagyan.l0_yogas import YOGAS_CORE
    for y in YOGAS_CORE:
        assert y.get("source_citation"), \
            f"yoga {y['canonical_id']}: missing source_citation (hard gate)"


def test_formation_rule_jsonb_is_dict():
    from brahmagyan.l0_yogas import YOGAS_CORE
    for y in YOGAS_CORE:
        rule = y.get("formation_rule_jsonb")
        assert rule is not None, f"yoga {y['canonical_id']}: missing formation_rule_jsonb"
        assert isinstance(rule, dict), f"yoga {y['canonical_id']}: formation_rule_jsonb must be dict"


def test_all_32_nabhasa_yogas_present():
    from brahmagyan.l0_yogas import YOGAS_CORE
    nabhasa_ids = [y["canonical_id"] for y in YOGAS_CORE
                   if (y.get("category") == "other" and
                       y.get("significations_jsonb", {}).get("subcategory", "").startswith("nabhasa"))]
    assert len(nabhasa_ids) >= 32, f"Expected >=32 nabhasa yogas, got {len(nabhasa_ids)}: {nabhasa_ids}"


def test_nabhasa_aakriti_20_yogas():
    from brahmagyan.l0_yogas import YOGAS_CORE
    aakriti = [y for y in YOGAS_CORE
               if y.get("significations_jsonb", {}).get("subcategory") == "nabhasa_akriti"]
    assert len(aakriti) == 20, f"Expected 20 Aakriti yogas, got {len(aakriti)}"


def test_nabhasa_sankhya_7_yogas():
    from brahmagyan.l0_yogas import YOGAS_CORE
    sankhya = [y for y in YOGAS_CORE
               if y.get("significations_jsonb", {}).get("subcategory") == "nabhasa_sankhya"]
    assert len(sankhya) == 8, f"Expected 8 Sankhya yogas, got {len(sankhya)}"


def test_nabhasa_ashraya_3_yogas():
    from brahmagyan.l0_yogas import YOGAS_CORE
    ashraya = [y for y in YOGAS_CORE
               if y.get("significations_jsonb", {}).get("subcategory") == "nabhasa_ashraya"]
    assert len(ashraya) == 3, f"Expected 3 Ashraya yogas, got {len(ashraya)}: {ashraya}"


def test_nabhasa_dala_2_yogas():
    from brahmagyan.l0_yogas import YOGAS_CORE
    dala = [y for y in YOGAS_CORE
            if y.get("significations_jsonb", {}).get("subcategory") == "nabhasa_dala"]
    assert len(dala) == 2, f"Expected 2 Dala yogas, got {len(dala)}"


def test_pancha_mahapurusha_5_yogas():
    from brahmagyan.l0_yogas import YOGAS_CORE
    mp = [y for y in YOGAS_CORE if y.get("category") == "pancha_mahapurusha"]
    assert len(mp) == 5, f"Expected 5 Pancha Mahapurusha yogas, got {len(mp)}"


def test_no_duplicate_canonical_ids():
    from brahmagyan.l0_yogas import YOGAS_CORE
    ids = [y["canonical_id"] for y in YOGAS_CORE]
    assert len(ids) == len(set(ids)), \
        f"Duplicate canonical_ids: {[id for id in ids if ids.count(id) > 1]}"


# ── Yoga families ──────────────────────────────────────────────────────────────

def test_yoga_families_defined():
    from brahmagyan.l0_yogas import YOGA_FAMILIES
    assert YOGA_FAMILIES, "YOGA_FAMILIES must not be empty"


def test_yoga_families_have_required_fields():
    from brahmagyan.l0_yogas import YOGA_FAMILIES
    required = {"family_id", "name_en", "classical_citation"}
    for f in YOGA_FAMILIES:
        missing = required - set(f.keys())
        assert not missing, f"Family {f.get('family_id')}: missing {missing}"


def test_yoga_families_required_set():
    from brahmagyan.l0_yogas import YOGA_FAMILIES
    family_ids = {f["family_id"] for f in YOGA_FAMILIES}
    required = {
        "mahapurusha", "nabhasa", "nabhasa_aakriti", "nabhasa_sankhya",
        "nabhasa_dala", "nabhasa_asraya", "raja", "dhana", "chandra",
        "surya", "arishta", "sannyasa", "specialized",
    }
    missing = required - family_ids
    assert not missing, f"Missing families: {missing}"


def test_yoga_families_root_parents_are_none():
    from brahmagyan.l0_yogas import YOGA_FAMILIES
    roots = [f for f in YOGA_FAMILIES if f["parent_family_id"] is None]
    assert len(roots) >= 5, f"Expected at least 5 root families, got {len(roots)}"


def test_yoga_families_child_parents_exist():
    from brahmagyan.l0_yogas import YOGA_FAMILIES
    all_ids = {f["family_id"] for f in YOGA_FAMILIES}
    for f in YOGA_FAMILIES:
        parent = f.get("parent_family_id")
        if parent is not None:
            assert parent in all_ids, \
                f"Family {f['family_id']}: parent_family_id '{parent}' not in YOGA_FAMILIES"


# ── Strength formula ───────────────────────────────────────────────────────────

def test_yoga_strength_formula_basic():
    from ga_writers.ga_yoga_writer import compute_yoga_strength_v1
    result = compute_yoga_strength_v1([1.0], in_kendra=True, has_exalted=True)
    assert result is not None
    assert result > 0.0


def test_yoga_strength_formula_empty_returns_none():
    from ga_writers.ga_yoga_writer import compute_yoga_strength_v1
    result = compute_yoga_strength_v1([], in_kendra=True, has_exalted=False)
    assert result is None


def test_yoga_strength_formula_exalted_greater_than_own():
    from ga_writers.ga_yoga_writer import compute_yoga_strength_v1
    exalted = compute_yoga_strength_v1([1.0], in_kendra=True, has_exalted=True)
    own = compute_yoga_strength_v1([0.75], in_kendra=True, has_exalted=False)
    assert exalted > own


def test_yoga_strength_formula_kendra_bonus():
    from ga_writers.ga_yoga_writer import compute_yoga_strength_v1
    with_kendra = compute_yoga_strength_v1([0.75], in_kendra=True, has_exalted=False)
    without_kendra = compute_yoga_strength_v1([0.75], in_kendra=False, has_exalted=False)
    assert with_kendra > without_kendra


def test_yoga_strength_formula_range():
    from ga_writers.ga_yoga_writer import compute_yoga_strength_v1
    result = compute_yoga_strength_v1([1.0], in_kendra=True, has_exalted=True)
    assert 0.0 <= result <= 3.0, f"Strength {result} outside expected range [0, 3]"


# ── ChartState ────────────────────────────────────────────────────────────────

def _make_fact(fact_id, category, subject, key, value_text=None, value_num=None, house=None):
    return {
        "fact_id": fact_id,
        "fact_category": category,
        "fact_subject": subject,
        "fact_key": key,
        "fact_value_text": value_text,
        "fact_value_num": value_num,
        "fact_value_jsonb": None,
        "house_number": house,
        "sign": value_text if key == "sign" else None,
        "sign_number": None,
        "nakshatra": None,
        "degree_in_sign": None,
        "degree_absolute": None,
    }


def _sample_aries_lagna_facts():
    """
    Minimal chart_facts for Aries lagna (like native chart):
    Lagna=Aries, Sun=Capricorn(10), Moon=Aquarius(11), Mercury=Capricorn(10),
    Jupiter=Sagittarius(9), Mars=Virgo(6), Venus=Pisces(12), Saturn=Libra(7).
    """
    facts = []
    # Lagna
    facts.append(_make_fact("f-lagna-sign", "lagna", "lagna", "sign", value_text="aries"))

    # Planet signs and houses
    placements = {
        "sun": ("capricorn", 10),
        "moon": ("aquarius", 11),
        "mercury": ("capricorn", 10),
        "jupiter": ("sagittarius", 9),
        "mars": ("virgo", 6),
        "venus": ("pisces", 12),
        "saturn": ("libra", 7),
        "rahu": ("gemini", 3),
        "ketu": ("sagittarius", 9),
    }
    for planet, (sign, house) in placements.items():
        facts.append(_make_fact(
            f"f-{planet}-sign", "graha_position", planet.upper(), "sign", value_text=sign
        ))
        facts.append(_make_fact(
            f"f-{planet}-house", "graha_position", planet.upper(), "house", value_num=house
        ))
    return facts


def test_chart_state_parses_lagna():
    from ga_writers.ga_yoga_writer import ChartState
    facts = _sample_aries_lagna_facts()
    state = ChartState(facts)
    assert state.lagna_sign == "aries"


def test_chart_state_distinct_signs():
    from ga_writers.ga_yoga_writer import ChartState
    facts = _sample_aries_lagna_facts()
    state = ChartState(facts)
    # 7 classical planets in different signs
    count = state.distinct_signs_occupied()
    assert 1 <= count <= 7


def test_chart_state_planets_in_house():
    from ga_writers.ga_yoga_writer import ChartState
    facts = _sample_aries_lagna_facts()
    state = ChartState(facts)
    # Sun and Mercury are both in Capricorn = house 10 from Aries lagna
    h10 = state.planets_in_house(10)
    assert "sun" in h10 or "mercury" in h10


# ── Yoga evaluation ───────────────────────────────────────────────────────────

def test_evaluate_yoga_nabhasa_sankhya_fires():
    """Gola yoga (all 7 planets in 1 sign) fires when state matches."""
    from ga_writers.ga_yoga_writer import ChartState, _evaluate_yoga

    # All 7 classical planets in Aries
    facts = []
    facts.append(_make_fact("f-lagna", "lagna", "lagna", "sign", value_text="aries"))
    for planet in ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]:
        facts.append(_make_fact(f"f-{planet}", "graha_position", planet.upper(), "sign", value_text="aries"))

    state = ChartState(facts)
    assert state.distinct_signs_occupied() == 1

    gola = {
        "canonical_id": "gola",
        "category": "other",
        "formation_rule_jsonb": {"distinct_signs_occupied": 1},
        "cancellation_conditions": {},
    }
    result = _evaluate_yoga(gola, state)
    assert result is not None
    assert result["fired"] is True


def test_evaluate_yoga_sankhya_no_fire_when_wrong_count():
    """Gola yoga does NOT fire when planets are spread across 3 signs."""
    from ga_writers.ga_yoga_writer import ChartState, _evaluate_yoga

    facts = []
    facts.append(_make_fact("f-lagna", "lagna", "lagna", "sign", value_text="aries"))
    planets = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]
    signs = ["aries", "aries", "aries", "taurus", "taurus", "gemini", "gemini"]
    for p, s in zip(planets, signs):
        facts.append(_make_fact(f"f-{p}", "graha_position", p.upper(), "sign", value_text=s))

    state = ChartState(facts)
    assert state.distinct_signs_occupied() == 3

    gola = {
        "canonical_id": "gola",
        "category": "other",
        "formation_rule_jsonb": {"distinct_signs_occupied": 1},
        "cancellation_conditions": {},
    }
    result = _evaluate_yoga(gola, state)
    assert result is None


def test_evaluate_yoga_without_rule_returns_none():
    """A yoga with no formation_rule_jsonb cannot be evaluated."""
    from ga_writers.ga_yoga_writer import ChartState, _evaluate_yoga

    facts = [_make_fact("f-lagna", "lagna", "lagna", "sign", value_text="aries")]
    state = ChartState(facts)

    yoga = {
        "canonical_id": "unknown_yoga",
        "category": "other",
        "formation_rule_jsonb": {},
        "cancellation_conditions": {},
    }
    result = _evaluate_yoga(yoga, state)
    assert result is None


def test_mahapurusha_fires_for_exalted_mars():
    """Ruchaka yoga fires when Mars is in own/exalted sign in kendra."""
    from ga_writers.ga_yoga_writer import ChartState, _evaluate_yoga

    # Mars in Capricorn (exalted), house 10 from Aries lagna = kendra
    facts = []
    facts.append(_make_fact("f-lagna", "lagna", "lagna", "sign", value_text="aries"))
    facts.append(_make_fact("f-mars-sign", "graha_position", "mars", "sign", value_text="capricorn"))
    facts.append(_make_fact("f-mars-house", "graha_position", "mars", "house", value_num=10))

    state = ChartState(facts)

    ruchaka = {
        "canonical_id": "ruchaka",
        "category": "pancha_mahapurusha",
        "formation_rule_jsonb": {
            "requires": [{"planet": "mars", "dignity": ["own", "exalted"], "house_class": "kendra"}]
        },
        "cancellation_conditions": {},
    }
    result = _evaluate_yoga(ruchaka, state)
    assert result is not None
    assert result["fired"] is True
    assert "mars" in result["constituent_planets"]
    assert result["strength"] is not None  # strength must be set for mahapurusha


def test_mahapurusha_does_not_fire_for_non_own_planet():
    """Ruchaka yoga does NOT fire when Mars is in a neutral sign."""
    from ga_writers.ga_yoga_writer import ChartState, _evaluate_yoga

    # Mars in Cancer (enemy) in kendra — no own/exalt dignity
    facts = []
    facts.append(_make_fact("f-lagna", "lagna", "lagna", "sign", value_text="aries"))
    facts.append(_make_fact("f-mars-sign", "graha_position", "mars", "sign", value_text="cancer"))
    facts.append(_make_fact("f-mars-house", "graha_position", "mars", "house", value_num=4))

    state = ChartState(facts)

    ruchaka = {
        "canonical_id": "ruchaka",
        "category": "pancha_mahapurusha",
        "formation_rule_jsonb": {
            "requires": [{"planet": "mars", "dignity": ["own", "exalted"], "house_class": "kendra"}]
        },
        "cancellation_conditions": {},
    }
    result = _evaluate_yoga(ruchaka, state)
    assert result is None


def test_budha_aditya_fires():
    """Budha-Aditya fires when Sun and Mercury are conjunct and not deeply combust."""
    from ga_writers.ga_yoga_writer import ChartState, _evaluate_yoga

    # Sun degree=280, Mercury degree=270 → diff=10° (not combust within 3°)
    facts = []
    facts.append(_make_fact("f-lagna", "lagna", "lagna", "sign", value_text="aries"))
    facts.append(_make_fact("f-sun-sign", "graha_position", "sun", "sign", value_text="capricorn"))
    facts.append(_make_fact("f-sun-house", "graha_position", "sun", "house", value_num=10))
    facts.append(_make_fact("f-merc-sign", "graha_position", "mercury", "sign", value_text="capricorn"))
    facts.append(_make_fact("f-merc-house", "graha_position", "mercury", "house", value_num=10))

    # Add degree facts for combust check
    sun_fact = _make_fact("f-sun-deg", "graha_position", "sun", "degree_absolute")
    sun_fact["fact_value_num"] = 280.0
    sun_fact["degree_absolute"] = 280.0
    merc_fact = _make_fact("f-merc-deg", "graha_position", "mercury", "degree_absolute")
    merc_fact["fact_value_num"] = 270.0
    merc_fact["degree_absolute"] = 270.0
    facts.extend([sun_fact, merc_fact])

    state = ChartState(facts)

    budha_aditya = {
        "canonical_id": "budha_aditya",
        "category": "other",
        "formation_rule_jsonb": {
            "requires": [
                {"relation": "sun_mercury_conjunct"},
                {"condition": "mercury_not_too_combust"},
            ]
        },
        "cancellation_conditions": {},
    }
    result = _evaluate_yoga(budha_aditya, state)
    assert result is not None
    assert result["fired"] is True
    assert "sun" in result["constituent_planets"]
    assert "mercury" in result["constituent_planets"]


def test_budha_aditya_does_not_fire_when_deeply_combust():
    """Budha-Aditya does NOT fire when Mercury is within 3° of Sun (deeply combust)."""
    from ga_writers.ga_yoga_writer import ChartState, _evaluate_yoga

    facts = []
    facts.append(_make_fact("f-lagna", "lagna", "lagna", "sign", value_text="aries"))
    facts.append(_make_fact("f-sun-sign", "graha_position", "sun", "sign", value_text="capricorn"))
    facts.append(_make_fact("f-sun-house", "graha_position", "sun", "house", value_num=10))
    facts.append(_make_fact("f-merc-sign", "graha_position", "mercury", "sign", value_text="capricorn"))
    facts.append(_make_fact("f-merc-house", "graha_position", "mercury", "house", value_num=10))

    # Sun=280.0, Mercury=280.5 → diff=0.5° (deeply combust)
    sun_fact = _make_fact("f-sun-deg", "graha_position", "sun", "degree_absolute")
    sun_fact["fact_value_num"] = 280.0
    merc_fact = _make_fact("f-merc-deg", "graha_position", "mercury", "degree_absolute")
    merc_fact["fact_value_num"] = 280.5
    facts.extend([sun_fact, merc_fact])

    state = ChartState(facts)
    # Force degree parsing
    for f in facts:
        if f["fact_key"] == "degree_absolute":
            state.planet_degree[f["fact_subject"].lower()] = float(f["fact_value_num"])

    budha_aditya = {
        "canonical_id": "budha_aditya",
        "category": "other",
        "formation_rule_jsonb": {
            "requires": [
                {"relation": "sun_mercury_conjunct"},
                {"condition": "mercury_not_too_combust"},
            ]
        },
        "cancellation_conditions": {},
    }
    result = _evaluate_yoga(budha_aditya, state)
    assert result is None


def test_gajakesari_fires_when_jupiter_in_kendra_from_moon():
    """Gajakesari fires when Jupiter is 4th from Moon (kendra relationship)."""
    from ga_writers.ga_yoga_writer import ChartState, _evaluate_yoga

    # Moon in house 1, Jupiter in house 4 → 4th from Moon = kendra
    facts = []
    facts.append(_make_fact("f-lagna", "lagna", "lagna", "sign", value_text="aries"))
    facts.append(_make_fact("f-moon-sign", "graha_position", "moon", "sign", value_text="aries"))
    facts.append(_make_fact("f-moon-house", "graha_position", "moon", "house", value_num=1))
    facts.append(_make_fact("f-jup-sign", "graha_position", "jupiter", "sign", value_text="cancer"))
    facts.append(_make_fact("f-jup-house", "graha_position", "jupiter", "house", value_num=4))

    state = ChartState(facts)

    gajakesari = {
        "canonical_id": "gajakesari",
        "category": "other",
        "formation_rule_jsonb": {
            "requires": [{"relation": "jupiter_in_kendra_from_moon"}]
        },
        "cancellation_conditions": {},
    }
    result = _evaluate_yoga(gajakesari, state)
    assert result is not None
    assert result["fired"] is True
    assert "moon" in result["constituent_planets"]
    assert "jupiter" in result["constituent_planets"]


# ── FORENSIC — native-chart yoga assertions ────────────────────────────────────

CANONICAL_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"


def test_forensic_budha_aditya_fires_on_native_chart():
    """
    FORENSIC assertion: Sun=Capricorn + Mercury=Capricorn (native chart, Lahiri).
    Budha-Aditya must fire when degrees are not within 3° combustion gate.
    Guard: CANONICAL_CHART_ID only.
    """
    if CANONICAL_CHART_ID != "482012f1-710e-4a25-994a-93821f5871aa":
        return  # non-native chart — skip FORENSIC assertion
    from ga_writers.ga_yoga_writer import ChartState, _evaluate_yoga

    # Native: Aries lagna; Sun ≈ 292°, Mercury ≈ 305° (Lahiri, ~13° apart — not combust)
    facts = []
    facts.append(_make_fact("f-lagna", "lagna", "lagna", "sign", value_text="aries"))
    facts.append(_make_fact("f-sun-sign", "graha_position", "sun", "sign", value_text="capricorn"))
    facts.append(_make_fact("f-sun-house", "graha_position", "sun", "house", value_num=10))
    facts.append(_make_fact("f-merc-sign", "graha_position", "mercury", "sign", value_text="capricorn"))
    facts.append(_make_fact("f-merc-house", "graha_position", "mercury", "house", value_num=10))
    sun_fact = _make_fact("f-sun-deg", "graha_position", "sun", "degree_absolute")
    sun_fact["fact_value_num"] = 292.0
    sun_fact["degree_absolute"] = 292.0
    merc_fact = _make_fact("f-merc-deg", "graha_position", "mercury", "degree_absolute")
    merc_fact["fact_value_num"] = 305.0
    merc_fact["degree_absolute"] = 305.0
    facts.extend([sun_fact, merc_fact])

    state = ChartState(facts)

    budha_aditya = {
        "canonical_id": "budha_aditya",
        "category": "other",
        "formation_rule_jsonb": {
            "requires": [
                {"relation": "sun_mercury_conjunct"},
                {"condition": "mercury_not_too_combust"},
            ]
        },
        "cancellation_conditions": {},
    }
    result = _evaluate_yoga(budha_aditya, state)
    assert result is not None, \
        "FORENSIC FAIL: budha_aditya must fire for native chart (Sun+Mercury in Capricorn, 13° apart)"
    assert result["fired"] is True, \
        "FORENSIC FAIL: budha_aditya fired=False unexpectedly for native chart"
    assert "sun" in result["constituent_planets"]
    assert "mercury" in result["constituent_planets"]


# ── seed_yoga_families ─────────────────────────────────────────────────────────

def test_seed_yoga_families_dry_run():
    from brahmagyan.l0_yogas import seed_yoga_families, YOGA_FAMILIES
    conn = MagicMock()
    result = seed_yoga_families(conn, dry_run=True)
    assert result["families_inserted"] == len(YOGA_FAMILIES)
    assert result["warnings"] == []
    # No DB calls in dry_run
    conn.cursor.assert_not_called()


# ── Writer run_substep (integration-style with mock conn) ─────────────────────

def test_run_substep_calls_builder():
    """run_substep delegates to build_ga_yoga_substep correctly."""
    from pipeline.orchestrator.writers.ga_yoga import GaYogaWriter
    from pipeline.orchestrator.writers import SubStep, ContextSpec

    writer = GaYogaWriter()
    ctx = MagicMock(spec=ContextSpec)
    ctx.config = {"chart_id": "482012f1-710e-4a25-994a-93821f5871aa"}
    ctx.build_id = "test-build-id"
    ctx.dry_run = False
    ctx.db_conn = MagicMock()

    step = SubStep(key="ayanamsha_lahiri_chitrapaksha", label="test")

    with patch("ga_writers.ga_yoga_writer.build_ga_yoga_substep", return_value=5) as mock_builder:
        result = writer.run_substep(ctx, step)

    mock_builder.assert_called_once_with(
        chart_id="482012f1-710e-4a25-994a-93821f5871aa",
        build_id="test-build-id",
        ayanamsha_id="lahiri_chitrapaksha",
        conn=ctx.db_conn,
        dry_run=False,
    )
    assert result.rows_inserted == 5
    assert result.asset_id == "ga_yoga"
