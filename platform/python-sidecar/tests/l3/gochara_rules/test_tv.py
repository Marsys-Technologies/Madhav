"""O-TV-* — three-field valence oracles (GOCHARA_DESIGN_SPECS_v1_4 §3)."""
from __future__ import annotations

import pytest

from services.gochara_rules.valence import compute_valence


def test_otv1_bereavement_adverse():
    # bereavement-class window admitted by P3 (father frame: Saturn 253.43°
    # vs natal Jupiter 249.79° 9L: Δ = 3.64° = 3°38′24″, in the 9th)
    assert abs(253.43 - 249.79) == pytest.approx(3.64, abs=1e-9)
    v = compute_valence("bereavement", evidence_for=0.5, evidence_against=0.0)
    assert v.evidence_for_occurrence > 0
    assert v.outcome_valence_for_native == "adverse"
    # mutation: the all-favourable era table (E5) is the regression — an
    # outcome of 'favourable' fails
    assert v.outcome_valence_for_native != "favourable"


def test_otv2_contested_occurrence_not_mixed():
    # 2013-12 marriage window: evidence for AND against occurrence both > 0
    v = compute_valence("marriage", evidence_for=0.7, evidence_against=0.3)
    # both fields stand — occurrence contested, reported as such; never
    # netted to neutral
    assert v.evidence_for_occurrence == 0.7
    assert v.evidence_against_occurrence == 0.3
    assert v.occurrence == "contested"
    # outcome still favourable (marriage class polarity) — NOT 'mixed'
    assert v.outcome_valence_for_native == "favourable"
    # mutation: deriving mixed from contested occurrence fails
    assert v.outcome_valence_for_native != "mixed"


def test_otv3_unresolved_operand_unqualified():
    # window whose AV operand is unresolved (P5c donor matrix absent — the
    # current chart state pending the ga_strength rebuild)
    v = compute_valence("career_entry", evidence_for=0.4,
                        evidence_against=0.0,
                        unresolved_operand="P5c donor matrix")
    assert v.outcome_valence_for_native == "unqualified"
    assert v.unresolved_operand == "P5c donor matrix"
    # mutation: a silent default (1.0 or 'favourable') fails
    assert v.outcome_valence_for_native != "favourable"
