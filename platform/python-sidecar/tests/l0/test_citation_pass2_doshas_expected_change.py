"""CITATION-PASS2 bg_doshas: the expected-change declaration for the dispatch tool matches the seed (doshas branch only; the overlay tests are shared with the ontology branch)."""
from __future__ import annotations

K2_ID = "OS-2026-10-05-CITATIONS"


def test_expected_change_files_match_the_seed():
    import json
    import pathlib
    base = pathlib.Path(__file__).resolve().parents[4] / "00_ARCHITECTURE" / "control" / "expected_change"
    d = json.loads((base / "EXPECTED_CHANGE_bg_doshas_citation_pass2.json").read_text(encoding="utf-8"))
    assert set(d) <= {"asset", "expected_post_row_count", "expected_post_fingerprint", "why", "decision", "evidence", "excluded_tables_acknowledged"}
    assert d["asset"] == "bg_doshas" and d["decision"] == K2_ID
    # unit = reference_doshas + brahma_dosha_catalog + the whole shared brahma_ontology (741 rows before, 13 of them removed)
    assert d["expected_post_row_count"] == 66 + 66 + (741 - 13) == 860
    assert "expected_post_fingerprint" not in d or d["expected_post_fingerprint"] is None


def test_formation_spelling_expected_change_declaration_is_count_neutral_and_well_formed():
    """Migration 1361 (formation rules in one spelling family): content-only change, so the declared row count is the same unit as the citation-pass-2 declaration."""
    import json
    import pathlib
    base = pathlib.Path(__file__).resolve().parents[4] / "00_ARCHITECTURE" / "control" / "expected_change"
    d = json.loads((base / "EXPECTED_CHANGE_bg_doshas_formation_spelling.json").read_text(encoding="utf-8"))
    assert set(d) <= {"asset", "expected_post_row_count", "expected_post_fingerprint", "why", "decision", "evidence", "excluded_tables_acknowledged"}
    assert d["asset"] == "bg_doshas" and d["decision"] == "N-430"
    assert d["expected_post_row_count"] == 66 + 66 + (741 - 13) == 860
    assert "expected_post_fingerprint" not in d or d["expected_post_fingerprint"] is None
    prior = json.loads((base / "EXPECTED_CHANGE_bg_doshas_citation_pass2.json").read_text(encoding="utf-8"))
    assert d["expected_post_row_count"] == prior["expected_post_row_count"]
