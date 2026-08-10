"""
test_w31_27_class_coverage.py — W3.1 coverage assertions for ka_gochara_resonance.

Verifies:
1. TARGET_EVENT_CLASSES has exactly 27 entries.
2. Every entry is a canonical brahma_event_ontology event_class_id (matches DOMAIN_MAP).
3. TARGET_EVENT_CLASSES covers the complete DOMAIN_MAP (no canonical class missing).
4. No duplicates in the tuple.
5. FORMULA_VERSION is updated to v2.0.
6. COVERAGE_QUALITY_NOTES exists and has one entry per event class.
7. The 6 original classes (legacy 3 + health/adverse 3) remain in their historical positions
   (legacy-first ordering guarantee — ka_gochara_sweep substep-plan stability).
8. build_resonance_rows is DB-free and returns honest empty lists when given no data
   (I4: no fabricated targets).
"""
from __future__ import annotations

import pytest

from services.gochara_grammar.event_class_scope import DOMAIN_MAP
from services.ka_gochara_resonance.writer import (
    TARGET_EVENT_CLASSES,
    FORMULA_VERSION,
    COVERAGE_QUALITY_NOTES,
    build_resonance_rows,
    _ALL_27_EVENT_CLASSES,
)

# ── 1. Exact count ────────────────────────────────────────────────────────────

def test_target_event_classes_has_27_entries():
    assert len(TARGET_EVENT_CLASSES) == 27, (
        f"Expected 27 event classes; got {len(TARGET_EVENT_CLASSES)}: {list(TARGET_EVENT_CLASSES)}"
    )


# ── 2. Every member is a canonical ontology class ────────────────────────────

def test_all_target_classes_are_canonical():
    unknown = [ec for ec in TARGET_EVENT_CLASSES if ec not in DOMAIN_MAP]
    assert unknown == [], (
        f"TARGET_EVENT_CLASSES names non-canonical event classes (not in DOMAIN_MAP): {unknown}. "
        "Every member must be a brahma_event_ontology event_class_id."
    )


# ── 3. Complete coverage — no DOMAIN_MAP class missing ───────────────────────

def test_target_event_classes_covers_all_domain_map_classes():
    missing = [ec for ec in DOMAIN_MAP if ec not in TARGET_EVENT_CLASSES]
    assert missing == [], (
        f"TARGET_EVENT_CLASSES is missing canonical DOMAIN_MAP classes: {missing}. "
        "W3.1 target is complete 27-class coverage."
    )


# ── 4. No duplicates ─────────────────────────────────────────────────────────

def test_no_duplicates_in_target_event_classes():
    seen: set[str] = set()
    dupes = []
    for ec in TARGET_EVENT_CLASSES:
        if ec in seen:
            dupes.append(ec)
        seen.add(ec)
    assert dupes == [], f"Duplicate event classes found in TARGET_EVENT_CLASSES: {dupes}"


# ── 5. FORMULA_VERSION bumped to v2.0 ────────────────────────────────────────

def test_formula_version_is_v2():
    assert FORMULA_VERSION == "ka_gochara_resonance_v2.0", (
        f"Expected FORMULA_VERSION='ka_gochara_resonance_v2.0'; got '{FORMULA_VERSION}'. "
        "W3.1 requires a version bump to signal the expanded 27-class scope."
    )


# ── 6. COVERAGE_QUALITY_NOTES completeness ───────────────────────────────────

def test_coverage_quality_notes_has_entry_for_every_class():
    missing = [ec for ec in TARGET_EVENT_CLASSES if ec not in COVERAGE_QUALITY_NOTES]
    assert missing == [], (
        f"COVERAGE_QUALITY_NOTES is missing entries for: {missing}. "
        "Every event class must have a quality note (I4 documentation)."
    )

def test_coverage_quality_notes_has_no_extra_entries():
    extra = [ec for ec in COVERAGE_QUALITY_NOTES if ec not in TARGET_EVENT_CLASSES]
    assert extra == [], (
        f"COVERAGE_QUALITY_NOTES has entries for unknown classes: {extra}."
    )

def test_coverage_quality_notes_values_are_non_empty_strings():
    empty = [ec for ec, note in COVERAGE_QUALITY_NOTES.items() if not isinstance(note, str) or not note.strip()]
    assert empty == [], (
        f"COVERAGE_QUALITY_NOTES entries must be non-empty strings; blank/None found for: {empty}"
    )


# ── 7. Historical ordering — legacy 6 in position ────────────────────────────

_LEGACY_3 = ("marriage", "major_gain", "career_advancement")
_HEALTH_3 = ("illness_acute", "chronic_onset", "surgery")

def test_legacy_3_are_first():
    first_3 = TARGET_EVENT_CLASSES[:3]
    assert first_3 == _LEGACY_3, (
        f"Legacy 3 classes must occupy positions 0-2 (substep-plan stability). "
        f"Got: {first_3}"
    )

def test_health_adverse_3_are_positions_3_to_5():
    positions_3_5 = TARGET_EVENT_CLASSES[3:6]
    assert positions_3_5 == _HEALTH_3, (
        f"Health/adverse 3 classes must occupy positions 3-5 (substep-plan stability). "
        f"Got: {positions_3_5}"
    )


# ── 8. build_resonance_rows — honest empty output when given no data ──────────

@pytest.mark.parametrize("event_class", list(TARGET_EVENT_CLASSES))
def test_build_resonance_rows_empty_inputs_return_empty(event_class: str):
    """I4: no data in -> no fabricated rows out. build_resonance_rows must never
    invent bhava/lord/karaka targets when the caller passes no data."""
    rows = build_resonance_rows(
        event_class,
        houses=(),
        lords=(),
        karakas=(),
        ontology_citation=None,
        transit_rule_rows=(),
        sensitive_fact_rows=(),
        arudha_fact_rows=(),
        yoga_firing_rows=(),
        dasha_rows=(),
    )
    assert rows == [], (
        f"build_resonance_rows({event_class!r}) with all-empty inputs returned "
        f"{len(rows)} rows — expected 0. I4 violation: fabricated targets."
    )


@pytest.mark.parametrize("event_class", list(TARGET_EVENT_CLASSES))
def test_build_resonance_rows_bhava_from_houses(event_class: str):
    """Given a house list, bhava rows are emitted — one per valid numeric house."""
    rows = build_resonance_rows(
        event_class,
        houses=["7", "2"],
        lords=(),
        karakas=(),
        ontology_citation="BPHS ch.7",
        transit_rule_rows=(),
        sensitive_fact_rows=(),
        arudha_fact_rows=(),
        yoga_firing_rows=(),
        dasha_rows=(),
    )
    bhava_refs = {r["target_ref"] for r in rows if r["target_type"] == "bhava"}
    assert bhava_refs == {"7", "2"}, (
        f"build_resonance_rows({event_class!r}) with houses=[7,2] should produce "
        f"bhava rows {{7,2}}; got {bhava_refs}"
    )
    # All bhava rows must NOT be flagged uncited_extension when citation provided
    for r in rows:
        if r["target_type"] == "bhava":
            assert r["uncited_extension"] is False
            assert r["classical_citation"] == "BPHS ch.7"


@pytest.mark.parametrize("event_class", list(TARGET_EVENT_CLASSES))
def test_build_resonance_rows_no_duplicate_target_keys(event_class: str):
    """Dedup on (target_type, target_ref) must hold even with overlapping inputs."""
    rows = build_resonance_rows(
        event_class,
        houses=["7", "7", "2"],  # duplicate house
        lords=["7L", "7L"],       # duplicate lord
        karakas=["Venus", "Venus"],  # duplicate karaka
        ontology_citation=None,
        transit_rule_rows=(),
        sensitive_fact_rows=(),
        arudha_fact_rows=(),
        yoga_firing_rows=(),
        dasha_rows=(),
    )
    keys = [(r["target_type"], r["target_ref"]) for r in rows]
    assert len(keys) == len(set(keys)), (
        f"build_resonance_rows({event_class!r}) produced duplicate (target_type, target_ref) "
        f"keys: {[k for k in keys if keys.count(k) > 1]}"
    )


# ── Structural integrity: _ALL_27_EVENT_CLASSES alias ────────────────────────

def test_all_27_alias_equals_target():
    """TARGET_EVENT_CLASSES must equal _ALL_27_EVENT_CLASSES (they are the same object by assignment)."""
    assert TARGET_EVENT_CLASSES is _ALL_27_EVENT_CLASSES, (
        "TARGET_EVENT_CLASSES must be assigned from _ALL_27_EVENT_CLASSES directly."
    )
