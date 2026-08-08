"""
Lane B0 (PRATIJÑĀ v4, R21) — registry harmonization property tests.

Per CHECKPOINT_RECORD_v1_0.md Decision 2: parental_event added, bereavement
reframed to maraka doctrine, career_change differentiated from career_entry,
and no two event classes may share an identical populated factor set (the
career_entry===career_change defect this test was written to catch).
"""
from __future__ import annotations

from pipeline.orchestrator.writers.bo_pratijna_karyatva import KARYATVA_REGISTRY, get_karyatva


def _factor_set(km):
    return (
        tuple(sorted(km.primary_bhava)),
        tuple(sorted(km.karaka_grahas)),
        km.dusthana_required,
        km.divisional,
        tuple(sorted(km.yoga_keywords)),
        tuple(sorted(km.condition_malefic_grahas)),
    )


def test_registry_has_27_classes():
    assert len(KARYATVA_REGISTRY) == 27, (
        f"expected 27 event classes (brahma_event_ontology count), got {len(KARYATVA_REGISTRY)}"
    )


def test_parental_event_present_per_spec_section_7():
    km = get_karyatva("parental_event")
    assert km is not None
    assert km.primary_bhava == [4, 9]
    assert km.karaka_grahas == ["Moon", "Sun"]
    assert km.dusthana_required is False
    assert km.divisional == "D12"
    assert km.yoga_keywords == ["matru", "pitru"]
    assert km.condition_malefic_grahas == ["Saturn", "Rahu"]
    assert km.citations == [
        "BPHS ch.4 (mother)",
        "BPHS ch.9 (father)",
        "BPHS ch.6 (dwadashamsha)",
    ]


def test_bereavement_reframed_to_maraka_doctrine():
    km = get_karyatva("bereavement")
    assert km is not None
    assert km.primary_bhava == [8, 12, 2]
    assert km.karaka_grahas == ["Saturn", "Ketu"]
    assert km.divisional == "D8"
    assert any("maraka" in c.lower() for c in km.citations), (
        "bereavement citations must reference maraka doctrine (BPHS maraka-sthana)"
    )


def test_career_change_differentiated_via_rahu_d10():
    km = get_karyatva("career_change")
    assert km is not None
    assert km.primary_bhava == [10, 3, 9]
    assert km.karaka_grahas == ["Rahu"]
    assert km.divisional == "D10"


def test_career_entry_unchanged():
    km = get_karyatva("career_entry")
    assert km is not None
    assert km.primary_bhava == [10]
    assert km.karaka_grahas == ["Sun", "Saturn"]
    assert km.divisional == "D10"


def test_no_two_classes_share_an_identical_populated_factor_set():
    """The property test from CHECKPOINT_RECORD Decision 2(d): the
    career_entry===career_change identity is the marriage===separation defect
    class, now prevented structurally for every pair in the registry."""
    by_factor_set: dict[tuple, list[str]] = {}
    for class_id, km in KARYATVA_REGISTRY.items():
        key = _factor_set(km)
        by_factor_set.setdefault(key, []).append(class_id)

    collisions = {k: v for k, v in by_factor_set.items() if len(v) > 1}
    assert not collisions, f"classes with identical factor sets (not allowed): {collisions}"
