"""test_r6a4_y1_antifabrication.py — R6A.4 regression test.

The original Y-1 fix (commit caa0b727, PR #517, 2026-07-10) killed the vacuous-pass
fabricated-yoga-surface bug in `_evaluate_catalog_rule`'s "requires" loop, but was
never given a permanent committed regression test — it was verified only via an
ad-hoc "158/158" pytest run at the time (see commit message). R6A.4 (verify Y-1
holds + honesty, per CLAUDECODE_BRIEF_R6_YOGA_INTEGRITY_v1_0.md) closes that gap.

This locks in: unrecognized/unevaluable catalog rule shapes hard-fail (False,
"rule_shape_unimplemented:*") rather than vacuously firing (True, "requires_pass"),
across R6A.1/R6A.2's changes to ga_structural_writer.py/ga_yoga_writer.py.
"""
from __future__ import annotations

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from ga_writers.ga_structural_writer import _evaluate_catalog_rule  # noqa: E402

_EMPTY_CHART = {"grahas": []}


class TestEmptyAndMalformedRequires:
    def test_empty_requires_list_hard_fails(self):
        matches, reason = _evaluate_catalog_rule({"requires": []}, _EMPTY_CHART)
        assert matches is False
        assert reason == "rule_shape_unimplemented:empty_requires"

    def test_unstructured_requires_hard_fails(self):
        matches, reason = _evaluate_catalog_rule(
            {"requires": "all 7 planets hemmed between Rahu and Ketu"}, _EMPTY_CHART
        )
        assert matches is False
        assert reason == "rule_shape_unimplemented:unstructured_requires"

    def test_non_dict_requires_element_hard_fails(self):
        matches, reason = _evaluate_catalog_rule({"requires": ["not-a-dict"]}, _EMPTY_CHART)
        assert matches is False
        assert reason == "rule_shape_unimplemented:non_dict_requires_element"


class TestUnrecognizedShapesNeverVacuouslyPass:
    def test_raw_verse_clause_shape_hard_fails(self):
        """The exact OCR-corpus shape that caused the original fabricated-yoga-surface bug."""
        matches, reason = _evaluate_catalog_rule(
            {"requires": [{"raw_verse_clause": "some untranslated corpus fragment"}]},
            _EMPTY_CHART,
        )
        assert matches is False
        assert reason.startswith("rule_shape_unimplemented:")

    def test_determinant_shape_hard_fails(self):
        matches, reason = _evaluate_catalog_rule(
            {"requires": [{"determinant": "strongest_planet"}]}, _EMPTY_CHART
        )
        assert matches is False
        assert reason.startswith("rule_shape_unimplemented:")

    def test_unrecognized_relation_hard_fails(self):
        matches, reason = _evaluate_catalog_rule(
            {"requires": [{"relation": "not_a_real_relation_name"}]}, _EMPTY_CHART
        )
        assert matches is False
        assert reason.startswith("relation_unimplemented:")

    def test_unrecognized_planet_subkey_hard_fails(self):
        """Ring-2's own R6A.1-era finding (Y-1 gap-2): an unimplemented planet
        sub-key must hard-fail, not silently pass through the recognized ones."""
        matches, reason = _evaluate_catalog_rule(
            {"requires": [{"planet": "mars", "condition": "same_sign_in_rasi_and_navamsa"}]},
            _EMPTY_CHART,
        )
        assert matches is False
        assert reason.startswith("rule_shape_unimplemented:planet_subkey:")

    def test_unrecognized_house_class_hard_fails(self):
        matches, reason = _evaluate_catalog_rule(
            {"requires": [{"planet": "saturn", "house_class": "not_a_real_house_class"}]},
            {"grahas": [{"name": "Saturn", "house": 1, "sign": "Capricorn"}]},
        )
        assert matches is False
        assert reason.startswith("rule_shape_unimplemented:house_class:")

    def test_unrecognized_exclude_value_hard_fails(self):
        matches, reason = _evaluate_catalog_rule(
            {"requires": [{"exclude": "not_a_real_exclusion"}]}, _EMPTY_CHART
        )
        assert matches is False
        assert reason.startswith("rule_shape_unimplemented:exclude:")


class TestGenuineRulesStillFireCorrectly:
    """Anti-regression in the other direction: the fail-closed discipline must not
    have become so aggressive that real, evaluable rules stopped firing."""

    def test_real_kendra_dignity_rule_fires(self):
        matches, reason = _evaluate_catalog_rule(
            {"requires": [{"planet": "jupiter", "dignity": ["own", "exalted"], "house_class": "kendra"}]},
            {"grahas": [{"name": "Jupiter", "house": 4, "sign": "Cancer"}]},
        )
        assert matches is True
        assert reason == "requires_pass"

    def test_real_relation_rule_fires(self):
        matches, reason = _evaluate_catalog_rule(
            {"requires": [{"relation": "planet_not_sun_in_2nd_from_moon"}]},
            {"grahas": [
                {"name": "Moon", "house": 1, "sign": "Cancer"},
                {"name": "Mars", "house": 2, "sign": "Leo"},
            ]},
        )
        assert matches is True
        assert reason == "requires_pass"
