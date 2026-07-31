"""
B-NAR-BO — bo_bimba.py:253 (P2, SAMAPTI_NARRATION_TRIAGE_AND_PARTITION_v1_0.md §4.1).

Root cause: the graha-node `dignity_state` field was fabricated by harvesting
whichever `bodha_msr_signals` row happened to reference the graha via
`_parse_graha_from_signal`'s generic key match (signal_type_class-agnostic —
matches "graha"/"primary_graha"/"lord"/"fact_key"), then reading that row's own
`fact_value_text` as if it were a dignity classification.

Live evidence on chart 482012f1 (canonical, verified via direct DB query
against `bodha_cgm_nodes` before this fix): graha nodes carried
`dignity_state` values of "Venus", "Mercury", "Rahu", "Sun_in_H12",
"Moon_in_H8" etc — none of which is a valid dignity classification (own /
exalted / debilitated / neutral / friend / enemy / moolatrikona). No
`signal_type_class` in `bodha_msr_signals` is actually "dignity" (confirmed:
{annual, arudha, bhavat_bhavam_amplifier, composite_state, configuration,
dhana_axis, dosha, karaka_alignment, nakshatra_semantic, panchanga,
parivartana, sade_sati, special_lagna, sudarshana_agreement,
tradition_specific, varga_pattern, varga_ratification_divergence,
vargottama_amplification, yoga}), so the fabrication was guaranteed on every
build, not merely possible.

Fix: `_fetch_d1_dignity` reads L1 `chart_facts.graha_dignity_per_varga`
(fact_key='dignity_state', D1 varga) directly — the correct authority per
CLAUDE.md §N.5 — and `_build_nodes_for_aya` now sources `dignity_state` from
that map instead of from harvested MSR-signal text. A graha missing from the
L1 map gets an honest `None`, never a fabricated "neutral" (§N.7 item 6).

This test reproduces the exact live garbage shapes (conjunction_special_point
with fact_value_text="Venus"; lord_in_house_per_varga with
fact_value_text="Venus_in_H12") in synthetic MSR signals and asserts the
resulting graha node's dignity_state is the L1-sourced value, never the
harvested garbage.
"""
from __future__ import annotations

from pipeline.orchestrator.writers.bo_bimba import _build_nodes_for_aya, KNOWN_GRAHAS

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
AYA = "lahiri_chitrapaksha"
BUILD_ID = "test-build"
NOW = "2026-07-31T00:00:00+00:00"


def _garbage_signals_for_venus() -> list[dict]:
    """Reproduces the exact live shapes that polluted dignity_state for Venus."""
    return [
        {
            # conjunction_special_point:conjunct_VEN — fact_value_text is
            # literally the OTHER planet's name, not a dignity state.
            "signal_type_class": "composite_state",
            "signal_type_id": "conjunction_special_point:conjunct_VEN",
            "configuration_jsonb": {
                "graha": "Venus",
                "fact_key": "conjunct_VEN",
                "fact_value_text": "Venus",
            },
            "computed_salience": 0.828,
            "signal_tradition": "parashari",
        },
        {
            # lord_in_house_per_varga:lord_placement — fact_value_text is a
            # house-placement label, not a dignity state.
            "signal_type_class": "composite_state",
            "signal_type_id": "lord_in_house_per_varga:lord_placement",
            "configuration_jsonb": {
                "lord": "Venus",
                "fact_key": "lord_placement",
                "fact_value_text": "Venus_in_H12",
            },
            "computed_salience": 0.7935,
            "signal_tradition": "parashari",
        },
    ]


def test_dignity_state_comes_from_l1_map_not_harvested_signal_text():
    """The old bug: highest-salience signal referencing the graha 'wins' and
    its fact_value_text gets stamped as dignity_state. Guard: even with only
    garbage-shaped signals present, dignity_state must equal the L1 map's
    value ('exalted'), never "Venus" or "Venus_in_H12"."""
    signals = _garbage_signals_for_venus()
    d1_dignity = {"Venus": "exalted"}

    nodes = _build_nodes_for_aya(CHART_ID, AYA, BUILD_ID, signals, NOW, d1_dignity=d1_dignity)

    venus_node = next(n for n in nodes if n["node_type"] == "graha" and n["node_subject"] == "Venus")
    assert venus_node["dignity_state"] == "exalted"
    assert venus_node["dignity_state"] != "Venus"
    assert venus_node["dignity_state"] != "Venus_in_H12"


def test_dignity_state_is_honest_null_when_l1_map_missing_graha():
    """A graha absent from the L1 dignity map must get None, never a
    fabricated 'neutral' placeholder (CLAUDE.md §N.7 item 6: an honest null
    beats an invented judgment)."""
    signals = _garbage_signals_for_venus()
    d1_dignity: dict[str, str] = {}  # nothing supplied for any graha

    nodes = _build_nodes_for_aya(CHART_ID, AYA, BUILD_ID, signals, NOW, d1_dignity=d1_dignity)

    venus_node = next(n for n in nodes if n["node_type"] == "graha" and n["node_subject"] == "Venus")
    assert venus_node["dignity_state"] is None
    assert venus_node["dignity_state"] != "neutral"


def test_all_known_grahas_get_a_node_regardless_of_dignity_source():
    """Sanity: the fix must not drop any graha node."""
    nodes = _build_nodes_for_aya(CHART_ID, AYA, BUILD_ID, [], NOW, d1_dignity={})
    graha_nodes = {n["node_subject"] for n in nodes if n["node_type"] == "graha"}
    assert graha_nodes == set(KNOWN_GRAHAS)


def test_strength_and_tradition_unaffected_by_dignity_fix():
    """The strength/tradition aggregation (a separate, unflagged concern) must
    still work off the same signals loop after dignity harvesting was
    removed from it."""
    signals = _garbage_signals_for_venus()
    nodes = _build_nodes_for_aya(CHART_ID, AYA, BUILD_ID, signals, NOW, d1_dignity={"Venus": "exalted"})
    venus_node = next(n for n in nodes if n["node_type"] == "graha" and n["node_subject"] == "Venus")
    # Highest computed_salience among the two Venus-referencing signals is 0.828.
    assert venus_node["strength_score"] == 0.828
    assert "parashari" in venus_node["present_in_traditions_array"]
