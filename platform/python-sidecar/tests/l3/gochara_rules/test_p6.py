"""O-P6-TARA — P6 Moon-channel tārā oracle (GOCHARA_DESIGN_SPECS_v1_4 §2.2 P6)."""
from __future__ import annotations

from services.gochara_rules.p6 import CHANDRASHTAMA_GENERIC_RULE, annotate, tara


def test_op6_tara_class_6_fixture():
    # twins case: natal star index 24, transit index 20; zero-based inclusive
    # cyclic distance = (20 − 24) mod 27 + 1 = 24; nine-fold class = 24 mod 9
    # = 6.
    r = tara(24, 20)
    assert r["count"] == 24
    assert r["class"] == 6
    # the tārā term is PRESENT with the correct normalised key — a null key
    # (the case-mismatch defect) or absent term fails
    assert r["operator"] == "tara"
    # P6 being testimony, the term annotates and does not weight
    assert r["operator_role"] == "testimony"
    assert r["weight"] == 0.0
    # mutation: a wrong nine-fold class fails
    assert r["class"] != (24 % 9 + 1)  # an off-by-one count is not 6's class


def test_op6_tara_annotation_moves_no_score():
    window = {"window_id": "w1", "score": 0.42, "annotations": []}
    out = annotate(window, tara(24, 20))
    assert out["score"] == 0.42  # bitwise-unchanged
    assert out["annotations"][0]["class"] == 6
    assert window["annotations"] == []  # annotate never mutates in place


def test_op6_chandrashtama_absent_as_generic_rule():
    # chandrāṣṭama absent as a generic rule (predicate count 0) —
    # context-bound 8th-from-Moon rules only
    assert CHANDRASHTAMA_GENERIC_RULE is None
