"""
Tests for bg_prashna_rules writer.
Verifies registration, data completeness, and the hard-gate citation rule.
"""
import pytest


def test_writer_is_registered():
    """Writer must be importable and registered under 'bg_prashna_rules'."""
    from pipeline.orchestrator.writers import get_writer  # type: ignore[attr-defined]

    writer = get_writer("bg_prashna_rules")
    assert writer is not None, "bg_prashna_rules must be registered"
    assert writer.asset_id == "bg_prashna_rules"


def test_all_11_tajik_yogas_present():
    """All 11 Tajik horary yogas must be present in the seed data."""
    from brahmagyan.l0_prashna import TAJIK_YOGAS

    expected_ids = {
        "ithasala",
        "eesarpha",
        "nakta",
        "yamaya",
        "manaau",
        "kambula",
        "gairi_kambula",
        "dutthottha",
        "rudda",
        "khallasara",
        "duhphali_kuttha",
    }
    found_ids = {y["yoga_id"] for y in TAJIK_YOGAS}
    assert found_ids == expected_ids, f"Missing yogas: {expected_ids - found_ids}"


def test_kp_249_is_primary():
    """KP-249 method must be present and marked as is_primary=True."""
    from brahmagyan.l0_prashna import PRASHNA_LAGNA_METHODS

    kp = next((m for m in PRASHNA_LAGNA_METHODS if m["method_id"] == "kp_249"), None)
    assert kp is not None, "kp_249 method must exist"
    assert kp["is_primary"] is True, "kp_249 must be marked is_primary=True"


def test_exactly_one_primary_lagna_method():
    """Exactly one Prashna Lagna method should be marked primary."""
    from brahmagyan.l0_prashna import PRASHNA_LAGNA_METHODS

    primaries = [m for m in PRASHNA_LAGNA_METHODS if m.get("is_primary")]
    assert len(primaries) == 1, f"Expected 1 primary method, found {len(primaries)}"


def test_all_question_classes_have_significators():
    """All 12 question classes must have significator entries."""
    from brahmagyan.l0_prashna import SIGNIFICATORS

    expected_classes = {
        "marriage",
        "career",
        "litigation_legal",
        "lost_object",
        "health_illness",
        "finance_wealth",
        "travel_journey",
        "property_land",
        "children_progeny",
        "death_longevity",
        "spiritual_religious",
        "enemy_conflict",
    }
    found_classes = {s["question_class"] for s in SIGNIFICATORS}
    assert found_classes == expected_classes, f"Missing classes: {expected_classes - found_classes}"


def test_all_fructification_rules_have_citations():
    """Hard gate: every fructification rule must have a non-empty classical_citation."""
    from brahmagyan.l0_prashna import FRUCTIFICATION_RULES

    for rule in FRUCTIFICATION_RULES:
        assert rule.get("classical_citation"), (
            f"Fructification rule '{rule['rule_id']}' is missing classical_citation"
        )


def test_no_empty_citations_anywhere():
    """Hard gate: ZERO rows across all seed data may have empty classical_citation."""
    from brahmagyan.l0_prashna import (
        FRUCTIFICATION_RULES,
        PRASHNA_LAGNA_METHODS,
        SIGNIFICATORS,
        SPECIAL_TECHNIQUES,
        TAJIK_YOGAS,
    )

    all_datasets = [
        ("PRASHNA_LAGNA_METHODS", PRASHNA_LAGNA_METHODS),
        ("TAJIK_YOGAS", TAJIK_YOGAS),
        ("SIGNIFICATORS", SIGNIFICATORS),
        ("FRUCTIFICATION_RULES", FRUCTIFICATION_RULES),
        ("SPECIAL_TECHNIQUES", SPECIAL_TECHNIQUES),
    ]

    violations = []
    for dataset_name, dataset in all_datasets:
        for row in dataset:
            citation = row.get("classical_citation", "")
            if not citation or not citation.strip():
                violations.append(f"{dataset_name}: {row}")

    assert not violations, f"Citation hard-gate FAILED — empty citations found:\n" + "\n".join(violations)


def test_dry_run_returns_correct_counts():
    """dry_run=True must return counts without touching the DB."""
    from unittest.mock import MagicMock
    from brahmagyan.l0_prashna import seed_prashna_rules

    counts = seed_prashna_rules(MagicMock(), dry_run=True)

    assert counts["lagna_methods"] == 5
    assert counts["tajik_yogas"] == 11
    assert counts["significators"] == 12
    assert counts["fructification"] == 5
    assert counts["special_techniques"] == 3
    assert counts["total_rules"] == 36


def test_writer_result_structure():
    """WriterResult from dry_run must have expected fields."""
    from unittest.mock import MagicMock
    from pipeline.orchestrator.writers import get_writer

    writer_cls = get_writer("bg_prashna_rules")
    writer = writer_cls()
    ctx = MagicMock()
    ctx.dry_run = True
    ctx.db_conn = MagicMock()

    result = writer.run(ctx)

    assert result.asset_id == "bg_prashna_rules"
    assert result.rows_inserted == 36
    assert "tajik_yogas=11" in result.notes
    assert "lagna_methods=5" in result.notes
