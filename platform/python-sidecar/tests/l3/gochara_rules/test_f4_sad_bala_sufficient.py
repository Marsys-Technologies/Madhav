"""F-4 — sad_bala_sufficient v1.0 (AM-6 Option C), steward M20261001T205832-b69b.

Every assertion runs through the REAL registry rows and the REAL evaluator
(`services.gochara_rules.strength`, `score.factor_product`,
`predicates.admission_state`); no rule is re-implemented in the test. The
thresholds below are the CITED figures (Phaladīpikā IV.22-23, corpus locator
phaladeepika:PG79:C1) written out as the test's own oracle — they are read from
the served corpus text, not from memory (see the registry row's citation).
"""
from __future__ import annotations

import copy
import math
from decimal import Decimal

import pytest

from services.gochara_rules import predicates, registry, score, strength

REF = ("sad_bala_sufficient", registry.RULE_VERSION)
CITED = {"Sun": 6.5, "Moon": 6.0, "Mars": 5.0, "Mercury": 7.0,
         "Jupiter": 6.5, "Venus": 5.5, "Saturn": 5.0}
L1_SUBJECT = {"Sun": "SUN", "Moon": "MOON", "Mars": "MAR", "Mercury": "MER",
              "Jupiter": "JUP", "Venus": "VEN", "Saturn": "SAT",
              "Rahu": "RAH_MEAN", "Ketu": "KET_MEAN"}


def operand(graha: str, value, unit: str = "rupa", **extra) -> dict:
    return {"fact_subject": L1_SUBJECT[graha], "value": value, "unit": unit,
            "fact_id": f"F-{graha}", "build_id": "build-x",
            "ayanamsha_id": "lahiri_chitrapaksha",
            "verification_pass_status": "single_pass", **extra}


# ── the registry row ─────────────────────────────────────────────────────────
def test_factor_row_is_a_unitless_step_with_null_state_ON_THE_FACTOR_ROW():
    row = registry.FACTORS[REF]
    assert row["function"] == "step"
    assert row["units"] == "unitless"          # satisfies kgf_units_ck (rupas never was)
    assert row["range"] == [0.0, 1.0]          # an OUTPUT range, never a bound on raw rūpas
    assert row["null_state"] == "unqualified"  # on the versioned FACTOR row (1154:310-334)
    assert row["calibration_status"] == "uncalibrated_default"
    assert row["factor_version_label"] == "v1.0"


def test_null_state_is_not_carried_by_any_path_membership():
    # soft-factor membership is only a composite (factor_id, rule_version) ref (1154:435-445)
    for path in registry.RULE_PATHS.values():
        for ref in path.get("soft_factors", []):
            assert isinstance(ref, tuple) and len(ref) == 2
    for path in registry.RULE_PATHS.values():
        assert "null_state" not in path


def test_thresholds_are_exactly_the_cited_figures_and_nodes_have_none():
    row = registry.FACTORS[REF]
    assert row["thresholds_rupa"] == CITED
    assert set(row["unsupported_agents"]) == {"Rahu", "Ketu"}
    assert "Rahu" not in row["thresholds_rupa"] and "Ketu" not in row["thresholds_rupa"]
    # the three half-rūpa figures are recorded as OCR-degraded fraction glyphs, per figure
    degraded = {g for g, r in row["threshold_reading"].items()
                if r["state"] == "ocr_degraded_fraction_glyph"}
    assert degraded == {"Sun", "Jupiter", "Venus"}
    assert {g: row["threshold_reading"][g]["ocr_glyph"] for g in degraded} == {
        "Sun": "6J-", "Jupiter": "6j", "Venus": "5*"}
    explicit = {g for g, r in row["threshold_reading"].items() if r["state"] == "explicit"}
    assert explicit == {"Moon", "Mars", "Mercury", "Saturn"}
    for g, t in CITED.items():
        assert (t != int(t)) == (g in degraded)   # exactly the half-figures are the degraded ones


def test_citation_identifies_the_edition_translator_and_chunks():
    c = registry.FACTORS[REF]["citation"]
    assert c["verses"] == "IV.22-23" and c["corpus_locator"] == "phaladeepika:PG79:C1"
    assert c["edition"] == "Trans. V. Subrahmanya Sastri, 2nd Ed. 1950, Aruna Press Bangalore"
    assert c["translator"] == "V. Subrahmanya Sastri"
    assert c["document_id"] == "55343940-c408-4633-9f18-551fcbcc7ce7"
    assert c["chunk_id"] == "phaladeepika_pg0079_c01" and len(c["chunk_content_sha256"]) == 64
    b = c["bhavabala_statement"]
    assert b["verse"] == "IV.24" and b["corpus_locator"] == "phaladeepika:PG80:C1"
    assert "ONLY" in b["use"]       # bhāvabala is a separate statement, never combined


def test_deferred_sad_bala_summary_is_retired_by_supersession_not_edited():
    old = registry.FACTORS[("sad_bala_summary", registry.RULE_VERSION)]
    # byte-for-byte as authored: the defect that deferred it is still visible, not erased
    assert old["units"] == "rupas" and old["range"] == [0.0, 1.0]
    assert old["purna_bala_thresholds"] == CITED
    sup = registry.SUPERSEDED_FACTORS[("sad_bala_summary", registry.RULE_VERSION)]
    assert sup["superseded_by"] == REF
    assert REF in registry.FACTORS            # the successor is a NEW row
    # nothing references the retired name as a live soft factor
    for path in registry.RULE_PATHS.values():
        assert ("sad_bala_summary", registry.RULE_VERSION) not in path.get("soft_factors", [])


# ── the evaluator: boundary, equality, nodes, missing ────────────────────────
@pytest.mark.parametrize("graha,threshold", sorted(CITED.items()))
def test_equality_boundary_for_every_supported_graha(graha, threshold):
    at = strength.sad_bala_sufficient(operand(graha, threshold))
    assert at["value"] == 1.0, "equality IS sufficient"
    just_below = strength.sad_bala_sufficient(operand(graha, float(Decimal(str(threshold)) - Decimal("0.01"))))
    assert just_below["value"] == 0.0
    above = strength.sad_bala_sufficient(operand(graha, threshold + 3.0))
    assert above["value"] == 1.0
    assert at["threshold_rupa"] == threshold      # read from the registry row, not a copy here


def test_float_noise_just_below_a_threshold_is_not_sufficient():
    # the exact-decimal comparison: 6.499999999999999 is NOT 6.5
    assert strength.sad_bala_sufficient(operand("Sun", 6.499999999999999))["value"] == 0.0
    assert strength.sad_bala_sufficient(operand("Sun", Decimal("6.5")))["value"] == 1.0


@pytest.mark.parametrize("node", ["Rahu", "Ketu"])
def test_a_node_is_unqualified_never_zero_or_one_and_keeps_its_raw_value(node):
    out = strength.sad_bala_sufficient(operand(node, 0.375))
    assert out["value"] is None and out["null_state"] == "unqualified"
    assert out["reason"] == "no_cited_threshold_for_node"
    assert out["evidence"]["value"] == 0.375 and out["evidence"]["scored"] is False


@pytest.mark.parametrize("bad,reason", [
    (None, "operand_missing"),
    ({"fact_subject": "ZZZ", "value": 7.0, "unit": "rupa"}, "graha_unrecognised"),
    (operand("Sun", 7.0, unit="virupa"), "incompatible_unit"),
    (operand("Sun", None), "operand_missing_or_not_numeric"),
    (operand("Sun", "7.0"), "operand_missing_or_not_numeric"),
    (operand("Sun", True), "operand_missing_or_not_numeric"),
    (operand("Sun", math.nan), "operand_not_a_finite_non_negative_total"),
    (operand("Sun", math.inf), "operand_not_a_finite_non_negative_total"),
    (operand("Sun", -1.0), "operand_not_a_finite_non_negative_total"),
])
def test_missing_incompatible_or_unsupported_operands_leave_the_factor_unqualified(bad, reason):
    out = strength.sad_bala_sufficient(bad)
    assert out["value"] is None and out["null_state"] == "unqualified" and out["reason"] == reason


# ── raw rūpas are typed evidence, never scored ──────────────────────────────
def test_raw_rupas_ride_as_typed_evidence_with_the_l1_rows_own_provenance():
    out = strength.sad_bala_sufficient(operand("Mercury", 7.55, fact_id="abc123"))
    ev = out["evidence"]
    assert ev["kind"] == "typed_operand_evidence" and ev["scored"] is False
    assert (ev["fact_category"], ev["fact_key"], ev["unit"]) == ("graha_shadbala_total", "rupa", "rupa")
    assert ev["value"] == 7.55 and ev["fact_id"] == "abc123"
    assert (ev["build_id"], ev["ayanamsha_id"], ev["verification_pass_status"]) == (
        "build-x", "lahiri_chitrapaksha", "single_pass")
    # the score is the step output; the raw magnitude never enters it
    assert out["value"] in (0.0, 1.0)
    # the tier is COPIED from the row, never stated by the evaluator
    ev2 = strength.sad_bala_sufficient(operand("Mercury", 7.55, verification_pass_status="two_pass_verified"))["evidence"]
    assert ev2["verification_pass_status"] == "two_pass_verified"


def test_l1_subject_and_registry_names_both_resolve():
    for g, code in L1_SUBJECT.items():
        assert strength.graha_name(g) == g and strength.graha_name(code) == g
    assert strength.graha_name("nobody") is None


# ── the evaluator reads the REGISTRY row (no shadow constant) ───────────────
def test_thresholds_come_from_the_registry_row_not_from_a_copy_in_the_evaluator(monkeypatch):
    patched = copy.deepcopy(registry.FACTORS[REF])
    patched["thresholds_rupa"]["Sun"] = 9.0
    monkeypatch.setitem(registry.FACTORS, REF, patched)
    assert strength.sad_bala_sufficient(operand("Sun", 8.0))["value"] == 0.0
    assert strength.sad_bala_sufficient(operand("Sun", 9.0))["value"] == 1.0


# ── the score algebra and the admission boundary ────────────────────────────
def test_factor_results_feed_the_score_algebra_unqualified_propagates_zero_and_one_multiply():
    one = strength.sad_bala_sufficient(operand("Jupiter", 7.8))
    zero = strength.sad_bala_sufficient(operand("Venus", 4.64))
    node = strength.sad_bala_sufficient(operand("Rahu", 0.375))
    assert score.factor_product([one]) == 1.0
    assert score.factor_product([one, zero]) == 0.0
    assert score.factor_product([one, node]) == score.UNQUALIFIED
    assert score.factor_product([zero, node]) == score.UNQUALIFIED     # unqualified propagates, never 0 by default


def test_score_qualification_is_not_admission():
    # 1155:822-832 — admission derives from the path's NECESSARY predicates only
    necessary_all_true = [predicates.TRUE, predicates.TRUE]
    assert predicates.admission_state(necessary_all_true) == predicates.ADMITTED
    # a soft factor that is 0 or unqualified cannot be an input to admission at all …
    assert strength.sad_bala_sufficient(operand("Venus", 4.64))["value"] == 0.0
    assert strength.sad_bala_sufficient(operand("Ketu", 0.625))["value"] is None
    # … so the admission of the same record is unchanged
    assert predicates.admission_state(necessary_all_true) == predicates.ADMITTED
    # and only a necessary predicate can change it
    assert predicates.admission_state([predicates.TRUE, predicates.UNKNOWN]) == predicates.UNQUALIFIED
    assert predicates.admission_state([predicates.TRUE, predicates.FALSE]) == predicates.EXCLUDED
