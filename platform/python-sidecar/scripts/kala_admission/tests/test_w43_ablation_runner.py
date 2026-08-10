"""
test_w43_ablation_runner.py — Unit tests for the W4.3 ablation runner.

DB-free: all tests operate on the grammar_v3_registry.yaml file and the
ablation runner logic only. No live DB calls, no engine imports.

I2 compliance: zero imports from gochara_grammar/*, gochara_intensity/*,
ka_gochara_sweep/*.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Make the scripts/ directory importable so kala_admission is a package
sys.path.insert(0, str(Path(__file__).parents[2]))

from kala_admission.w43_ablation_runner import (  # noqa: E402
    REQUIRED_FIELDS,
    VALID_ADMISSION_STATES,
    VALID_CITATION_STATUSES,
    _REGISTRY_PATH,
    load_registry,
    run_ablation,
)

# ---------------------------------------------------------------------------
# Canonical set of 9 Wave-2 mechanism IDs expected in the registry
# ---------------------------------------------------------------------------

EXPECTED_MECHANISM_IDS = {
    "w21_av_gating",
    "w22_moorti_nirnaya",
    "w23_tara_bala",
    "w24_sade_sati",
    "w25_kota_chakra",
    "w26_real_eclipses",
    "w27_annual_stack",
    "w28_bhava_degrees",
    "w29_citation_resolution",
}


# ---------------------------------------------------------------------------
# Test 1: Registry loads without error
# ---------------------------------------------------------------------------


def test_registry_loads_without_error():
    """YAML registry must be parseable without exceptions and return a list."""
    mechanisms = load_registry()
    assert isinstance(mechanisms, list), "Registry 'mechanisms' key must yield a list"
    assert len(mechanisms) > 0, "Registry must contain at least one mechanism entry"


# ---------------------------------------------------------------------------
# Test 2: All 9 mechanisms are present
# ---------------------------------------------------------------------------


def test_all_nine_mechanisms_present():
    """All 9 Wave-2 mechanism IDs must appear in the registry."""
    mechanisms = load_registry()
    found_ids = {m["mechanism_id"] for m in mechanisms}
    missing = EXPECTED_MECHANISM_IDS - found_ids
    assert not missing, (
        f"Registry is missing mechanism IDs: {sorted(missing)}. "
        f"Found: {sorted(found_ids)}"
    )


# ---------------------------------------------------------------------------
# Test 3: Each mechanism has all required UTK-R3 fields
# ---------------------------------------------------------------------------


def test_each_mechanism_has_required_fields():
    """Every mechanism entry must have the full UTK-R3 required field set."""
    mechanisms = load_registry()
    errors = []
    for mech in mechanisms:
        mech_id = mech.get("mechanism_id", "<missing>")
        missing = [f for f in REQUIRED_FIELDS if f not in mech]
        if missing:
            errors.append(f"{mech_id}: missing fields {missing}")
    assert not errors, "Mechanisms with missing required fields:\n" + "\n".join(errors)


# ---------------------------------------------------------------------------
# Test 4: admission_state values are valid enum values
# ---------------------------------------------------------------------------


def test_admission_state_values_are_valid():
    """Every mechanism's admission_state must be a valid UTK-R3 enum value."""
    mechanisms = load_registry()
    errors = []
    for mech in mechanisms:
        mech_id = mech.get("mechanism_id", "<missing>")
        state = mech.get("admission_state", "")
        if state not in VALID_ADMISSION_STATES:
            errors.append(
                f"{mech_id}: invalid admission_state '{state}' "
                f"(valid: {sorted(VALID_ADMISSION_STATES)})"
            )
    assert not errors, "Invalid admission_state values:\n" + "\n".join(errors)


# ---------------------------------------------------------------------------
# Test 5: Ablation report JSON has required top-level fields
# ---------------------------------------------------------------------------


def test_ablation_report_has_required_fields():
    """The JSON ablation report produced by run_ablation() must have the required structure."""
    report = run_ablation()  # no output_path → no file written
    required_top_level = [
        "report_version",
        "ablation_wave",
        "registry_path",
        "ablation_method",
        "ablation_method_note",
        "validation_errors",
        "summary",
        "mechanisms",
    ]
    for field in required_top_level:
        assert field in report, f"Ablation report missing top-level field '{field}'"

    # summary sub-fields
    summary = report["summary"]
    required_summary = [
        "total_mechanisms",
        "classically_cited",
        "always_unit_modifier",
        "test_suite_coverage",
        "recommendations",
    ]
    for field in required_summary:
        assert field in summary, f"Ablation report summary missing field '{field}'"

    # Mechanism records must be present and be a list
    assert isinstance(report["mechanisms"], list)
    assert len(report["mechanisms"]) == len(EXPECTED_MECHANISM_IDS)


# ---------------------------------------------------------------------------
# Test 6: Each mechanism record in the report has adjudicator_input
# ---------------------------------------------------------------------------


def test_each_mechanism_record_has_adjudicator_input():
    """Every mechanism record in the ablation report must have an adjudicator_input dict."""
    report = run_ablation()
    for record in report["mechanisms"]:
        mech_id = record.get("mechanism_id", "<missing>")
        assert "adjudicator_input" in record, (
            f"Mechanism record '{mech_id}' missing 'adjudicator_input'"
        )
        adj = record["adjudicator_input"]
        required_adj_fields = [
            "mechanism_id",
            "toggle_key",
            "admission_state_current",
            "classically_cited",
            "classical_citation_text",
            "always_unit_modifier",
            "unit_test_suite_present",
            "unit_test_count",
            "ablation_status",
            "admission_recommendation",
            "admission_recommendation_rationale",
        ]
        for field in required_adj_fields:
            assert field in adj, (
                f"adjudicator_input for '{mech_id}' missing field '{field}'"
            )


# ---------------------------------------------------------------------------
# Test 7: citation_status values are valid
# ---------------------------------------------------------------------------


def test_citation_status_values_are_valid():
    """Every mechanism's citation_status must be one of the valid enum values."""
    mechanisms = load_registry()
    errors = []
    for mech in mechanisms:
        mech_id = mech.get("mechanism_id", "<missing>")
        status = mech.get("citation_status", "")
        if status not in VALID_CITATION_STATUSES:
            errors.append(
                f"{mech_id}: invalid citation_status '{status}' "
                f"(valid: {sorted(VALID_CITATION_STATUSES)})"
            )
    assert not errors, "Invalid citation_status values:\n" + "\n".join(errors)


# ---------------------------------------------------------------------------
# Test 8: toggle_key matches mechanism_id for all non-sub-mechanism entries
# ---------------------------------------------------------------------------


def test_toggle_key_matches_mechanism_id():
    """For Wave-2 top-level mechanisms, toggle_key must equal mechanism_id."""
    mechanisms = load_registry()
    errors = []
    for mech in mechanisms:
        mech_id = mech.get("mechanism_id", "")
        toggle = mech.get("toggle_key", "")
        if mech_id != toggle:
            errors.append(f"'{mech_id}': toggle_key='{toggle}' does not match mechanism_id")
    assert not errors, "toggle_key/mechanism_id mismatches:\n" + "\n".join(errors)


# ---------------------------------------------------------------------------
# Test 9: Unit-modifier mechanisms are correctly flagged in the report
# ---------------------------------------------------------------------------


def test_unit_modifier_mechanisms_flagged():
    """w28 and w29 must be flagged always_unit_modifier=True in the report."""
    report = run_ablation()
    unit_modifier_ids = {"w28_bhava_degrees", "w29_citation_resolution"}
    for record in report["mechanisms"]:
        if record["mechanism_id"] in unit_modifier_ids:
            assert record["always_unit_modifier"] is True, (
                f"{record['mechanism_id']} should have always_unit_modifier=True"
            )
            assert record["adjudicator_input"]["admission_recommendation"] == "structural-only", (
                f"{record['mechanism_id']} unit-modifier mechanism should recommend structural-only"
            )


# ---------------------------------------------------------------------------
# Test 10: No validation errors in the report for the canonical registry
# ---------------------------------------------------------------------------


def test_no_validation_errors_in_canonical_registry():
    """The canonical grammar_v3_registry.yaml must produce zero validation errors."""
    report = run_ablation()
    assert report["validation_errors"] == [], (
        f"Unexpected validation errors in canonical registry:\n"
        + "\n".join(report["validation_errors"])
    )


# ---------------------------------------------------------------------------
# Test 11: ablation_evidence_link is "W4.3" for all mechanisms
# ---------------------------------------------------------------------------


def test_ablation_evidence_link_is_w43():
    """All mechanisms must have ablation_evidence_link set to 'W4.3'."""
    mechanisms = load_registry()
    for mech in mechanisms:
        mech_id = mech.get("mechanism_id", "<missing>")
        link = mech.get("ablation_evidence_link", None)
        assert link == "W4.3", (
            f"{mech_id}: ablation_evidence_link='{link}', expected 'W4.3'"
        )


# ---------------------------------------------------------------------------
# Test 12: admission_ruling_id is "pending" for all Wave-2 mechanisms
# ---------------------------------------------------------------------------


def test_admission_ruling_id_is_pending():
    """All Wave-2 mechanisms must have admission_ruling_id='pending' at W4.3 stage."""
    mechanisms = load_registry()
    for mech in mechanisms:
        mech_id = mech.get("mechanism_id", "<missing>")
        ruling_id = mech.get("admission_ruling_id", None)
        assert ruling_id == "pending", (
            f"{mech_id}: admission_ruling_id='{ruling_id}', expected 'pending'"
        )
