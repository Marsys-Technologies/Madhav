"""test_n350_linkage_stability_not_measured.py: SS N-341/N-347, PR-H1 item 3.

`LinkageInputs.cross_ayanamsha_stability_score` defaulted to 1.0 ("perfectly stable across ayanamshas") though its only caller (bo_sangati) never passes a measured
value: a plausible default standing in for a measurement (§N.8). The default is now None = NOT MEASURED: the factor is not applied (same numbers as the old default,
so no digest moves) and the result reports `stability_factor_applied`. Each test fails if the 1.0 default comes back.
"""
from __future__ import annotations

import dataclasses

from bodha_writers.formulas import LinkageInputs, linkage_formula_v1

SIGNALS = [{"salience": 0.8, "in_contradiction": False}] * 4


def _inp(**kw):
    return LinkageInputs(shared_signals=SIGNALS, high_convergence_count=2, shared_factor_count=3, **kw)


def test_the_default_is_not_measured_not_a_perfect_score():
    default = {f.name: f.default for f in dataclasses.fields(LinkageInputs)}["cross_ayanamsha_stability_score"]
    assert default is None
    assert LinkageInputs().cross_ayanamsha_stability_score is None


def test_unmeasured_stability_is_reported_as_not_applied():
    assert linkage_formula_v1(_inp())["stability_factor_applied"] is False
    assert linkage_formula_v1(LinkageInputs())["stability_factor_applied"] is False


def test_unmeasured_gives_exactly_the_numbers_the_old_default_gave():
    unmeasured = linkage_formula_v1(_inp())
    old_default = linkage_formula_v1(_inp(cross_ayanamsha_stability_score=1.0))
    for key in ("positive_contribution", "negative_contribution", "net_linkage_strength", "computed_linkage_strength", "linkage_formula_version"):
        assert unmeasured[key] == old_default[key], key


def test_a_measured_score_is_applied_and_said_to_be():
    base = linkage_formula_v1(_inp())["computed_linkage_strength"]
    measured = linkage_formula_v1(_inp(cross_ayanamsha_stability_score=0.5))
    assert measured["stability_factor_applied"] is True
    assert measured["computed_linkage_strength"] == round(base * 0.5, 6)


def test_a_measured_one_is_distinguishable_from_unmeasured():
    assert linkage_formula_v1(_inp(cross_ayanamsha_stability_score=1.0))["stability_factor_applied"] is True      # same number, different claim


def test_a_measured_zero_is_applied_not_mistaken_for_missing():
    r = linkage_formula_v1(_inp(cross_ayanamsha_stability_score=0.0))
    assert r["stability_factor_applied"] is True and r["computed_linkage_strength"] == 0.0


def test_a_negative_measured_score_is_floored_at_zero_and_applied():
    r = linkage_formula_v1(_inp(cross_ayanamsha_stability_score=-0.3))
    assert r["stability_factor_applied"] is True and r["computed_linkage_strength"] == 0.0
