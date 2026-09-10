"""Tests for MR-47 (PK-R-10) shape_conformance_check — the item-4(ii)
mutation-proof detector.

§N.8 (Earned-Signal Principle): a detector must be PROVEN to fail on a
genuine mismatch, not merely observed to pass on clean data (which could
mean "0 mismatches because nothing was ever checked"). This file's
`test_diagnose_row_mutation_proof_*` tests construct a fixture row whose
`shape_conformance` deliberately disagrees with what its
`temporal_shape`/`resolution`/ontology-shape combination actually implies,
and assert `diagnose_row` catches it.
"""
from __future__ import annotations

from services.gochara_v3.shape_conformance_check import (
    diagnose_row,
    expected_shape_conformance,
)
from services.gochara_v3.shape_conformance_vocab import (
    SHAPE_CONFORMANCE_ONTOLOGY_MATCH,
    SHAPE_CONFORMANCE_POINT_CLASS_ENVELOPE,
)


# ===========================================================================
# expected_shape_conformance — pure classification
# ===========================================================================


def test_interval_hierarchy_row_is_ontology_match():
    result = expected_shape_conformance(
        stored_temporal_shape="interval", stored_resolution="day",
        ontology_temporal_shape="interval",
    )
    assert result == SHAPE_CONFORMANCE_ONTOLOGY_MATCH


def test_chain_row_is_ontology_match():
    result = expected_shape_conformance(
        stored_temporal_shape="chain", stored_resolution=None,
        ontology_temporal_shape="chain",
    )
    assert result == SHAPE_CONFORMANCE_ONTOLOGY_MATCH


def test_genuine_point_row_is_ontology_match():
    """A real point row (e.g. MR-10's v1-promoted rows) — stored shape
    genuinely equals the ontology's declared 'point' shape."""
    result = expected_shape_conformance(
        stored_temporal_shape="point", stored_resolution=None,
        ontology_temporal_shape="point",
    )
    assert result == SHAPE_CONFORMANCE_ONTOLOGY_MATCH


def test_r812_flat_envelope_row_is_point_class_context_envelope():
    """The exact defect PK-R-10 found: ontology says 'point', but the row is
    stored 'interval'/resolution=NULL (R8.12's flat-production branch)."""
    result = expected_shape_conformance(
        stored_temporal_shape="interval", stored_resolution=None,
        ontology_temporal_shape="point",
    )
    assert result == SHAPE_CONFORMANCE_POINT_CLASS_ENVELOPE


def test_point_ontology_with_populated_resolution_is_unclassifiable():
    """A 'point' ontology class whose row somehow carries a non-NULL
    resolution is NOT the R8.12 envelope shape (that shape requires
    resolution IS NULL) and does not match directly either — honest None,
    never a guessed classification (§N.7 item 6)."""
    result = expected_shape_conformance(
        stored_temporal_shape="interval", stored_resolution="era",
        ontology_temporal_shape="point",
    )
    assert result is None


def test_no_ontology_row_found_is_unclassifiable():
    result = expected_shape_conformance(
        stored_temporal_shape="interval", stored_resolution=None,
        ontology_temporal_shape=None,
    )
    assert result is None


def test_shape_mismatch_not_covered_by_either_rule_is_unclassifiable():
    """Structurally-should-be-impossible combination (ontology='interval' but
    row stored 'point') — must not be silently waved through as either
    bucket."""
    result = expected_shape_conformance(
        stored_temporal_shape="point", stored_resolution=None,
        ontology_temporal_shape="interval",
    )
    assert result is None


# ===========================================================================
# diagnose_row — the actual detector (item 4i's engine)
# ===========================================================================


def test_diagnose_row_agrees_on_correct_ontology_match_row():
    mismatch = diagnose_row(
        stored_temporal_shape="interval", stored_resolution="month",
        ontology_temporal_shape="interval",
        stored_shape_conformance=SHAPE_CONFORMANCE_ONTOLOGY_MATCH,
    )
    assert mismatch is None


def test_diagnose_row_agrees_on_correct_envelope_row():
    mismatch = diagnose_row(
        stored_temporal_shape="interval", stored_resolution=None,
        ontology_temporal_shape="point",
        stored_shape_conformance=SHAPE_CONFORMANCE_POINT_CLASS_ENVELOPE,
    )
    assert mismatch is None


# ===========================================================================
# MUTATION-PROOF DETECTOR (item 4ii, §N.8): a deliberately wrong fixture row
# must be caught, proving diagnose_row has teeth and is not "0 mismatches
# because nothing real was ever compared."
# ===========================================================================


def test_diagnose_row_mutation_proof_wrong_shape_conformance_on_envelope_row():
    """The literal PK-R-10 defect, reconstructed as a fixture: a
    point-canonical class's row is genuinely the R8.12 flat envelope
    (temporal_shape='interval', resolution=NULL, ontology='point') but its
    STORED shape_conformance was mutated to claim ONTOLOGY_MATCH (the
    original hardcoding defect's blind spot) instead of the correct
    POINT_CLASS_CONTEXT_ENVELOPE. The detector must catch this."""
    mismatch = diagnose_row(
        stored_temporal_shape="interval", stored_resolution=None,
        ontology_temporal_shape="point",
        stored_shape_conformance=SHAPE_CONFORMANCE_ONTOLOGY_MATCH,  # WRONG on purpose
    )
    assert mismatch is not None, (
        "MUTATION-PROOF FAILURE: diagnose_row did not catch a row whose "
        "stored shape_conformance (ontology_match) disagrees with what its "
        "temporal_shape/resolution/ontology-shape combination actually "
        "implies (point_class_context_envelope) — the detector has no teeth."
    )
    assert "MISMATCH" in mismatch
    assert SHAPE_CONFORMANCE_ONTOLOGY_MATCH in mismatch
    assert SHAPE_CONFORMANCE_POINT_CLASS_ENVELOPE in mismatch


def test_diagnose_row_mutation_proof_deliberately_wrong_temporal_shape():
    """Per the task's own literal instruction: construct a fixture row with
    temporal_shape deliberately set to 'point' incorrectly (a genuine
    interval-hierarchy row whose stored temporal_shape was corrupted to
    'point' while its stored shape_conformance still claims ONTOLOGY_MATCH)
    and assert the detector catches it."""
    mismatch = diagnose_row(
        stored_temporal_shape="point",  # deliberately wrong -- should be 'interval'
        stored_resolution="day",
        ontology_temporal_shape="interval",
        stored_shape_conformance=SHAPE_CONFORMANCE_ONTOLOGY_MATCH,
    )
    assert mismatch is not None, (
        "MUTATION-PROOF FAILURE: diagnose_row did not catch a row whose "
        "temporal_shape was corrupted to 'point' against an 'interval' "
        "ontology class — the detector has no teeth."
    )


def test_diagnose_row_mutation_proof_null_shape_conformance_on_real_mismatch_row():
    """A row that was never backfilled at all (shape_conformance IS NULL)
    but genuinely IS the R8.12 envelope shape must also be flagged — NULL is
    not a free pass."""
    mismatch = diagnose_row(
        stored_temporal_shape="interval", stored_resolution=None,
        ontology_temporal_shape="point",
        stored_shape_conformance=None,
    )
    assert mismatch is not None
