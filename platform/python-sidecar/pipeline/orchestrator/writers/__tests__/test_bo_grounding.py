"""bo_grounding writer — row-shaping and insert-contract tests.

The classification logic itself is tested exhaustively in
bodha_writers/__tests__/test_grounding_matcher.py; these tests cover only
this file's own job: turning a GroundingMatch into a DB row correctly.
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[4]))

from bodha_writers.grounding_matcher import GroundingMatch
from pipeline.orchestrator.writers.bo_grounding import _match_to_row, CANONICAL_AYANAMSHAS, ENGINE_VERSION


def test_match_to_row_carries_every_schema_897_column():
    match = GroundingMatch(
        target_kind="yoga_dosha_firing",
        target_id="42",
        grounding_tier="sruti",
        citation_granularity="chapter_verse",
        grounding_evidence_jsonb={"text_id": "bphs", "verse_ref": "1:1"},
        derivation_chain=["bphs:1:1"],
        matched_rule_id="rule-abc",
    )
    row = _match_to_row(match, "chart-1", "lahiri_chitrapaksha", "build-1", "2026-01-01T00:00:00+00:00")

    assert row["chart_id"] == "chart-1"
    assert row["ayanamsha_id"] == "lahiri_chitrapaksha"
    assert row["build_id"] == "build-1"
    assert row["target_kind"] == "yoga_dosha_firing"
    assert row["target_id"] == "42"
    assert row["grounding_tier"] == "sruti"
    assert row["citation_granularity"] == "chapter_verse"
    assert row["matched_rule_id"] == "rule-abc"
    assert row["derivation_chain"] == ["bphs:1:1"]
    assert row["engine_version"] == ENGINE_VERSION
    assert row["computed_at"] == "2026-01-01T00:00:00+00:00"
    # match_id is a fresh UUID minted per row, not carried on the match itself
    assert "match_id" in row and len(row["match_id"]) == 36


def test_match_to_row_serializes_evidence_as_json_string_for_the_jsonb_cast():
    match = GroundingMatch(
        target_kind="msr_signal", target_id="s1", grounding_tier="pratyaksa",
        grounding_evidence_jsonb={"reason": "no citations"},
    )
    row = _match_to_row(match, "chart-1", "lahiri_chitrapaksha", "build-1", "now")
    assert isinstance(row["grounding_evidence_jsonb"], str)
    import json
    assert json.loads(row["grounding_evidence_jsonb"]) == {"reason": "no citations"}


def test_match_to_row_leaves_evidence_none_when_match_has_none():
    match = GroundingMatch(target_kind="msr_signal", target_id="s2", grounding_tier="pratyaksa")
    row = _match_to_row(match, "chart-1", "lahiri_chitrapaksha", "build-1", "now")
    assert row["grounding_evidence_jsonb"] is None


def test_pratyaksa_row_has_null_citation_granularity_and_matched_rule_id():
    match = GroundingMatch(target_kind="msr_signal", target_id="s3", grounding_tier="pratyaksa")
    row = _match_to_row(match, "chart-1", "lahiri_chitrapaksha", "build-1", "now")
    assert row["citation_granularity"] is None
    assert row["matched_rule_id"] is None


def test_canonical_ayanamshas_matches_the_established_five_asset_convention():
    # Same set bo_sudarshana/bo_laksana use — a mismatch here would silently
    # produce rows under an ayanamsha_id no sibling writer ever populates.
    assert CANONICAL_AYANAMSHAS == [
        "lahiri_chitrapaksha", "raman", "krishnamurti",
        "surya_siddhanta_classical", "true_chitra",
    ]
