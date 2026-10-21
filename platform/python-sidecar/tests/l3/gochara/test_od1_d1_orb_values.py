"""SR-OD1 D1 — the owner-ratified orb (ND-ORB-ADMISSION, ND-ORB-SCALE) and the six AM-13 applicability bindings
(AM-13-RATIFIED, K-1..K-6) as they ship in the registry, with their ledger references (B.3).

Oracles: the owner's rulings (/Users/Dev/kalayantra/run/DECISIONS_SURROGATE.jsonl, 2026-10-21T12:37:41Z; text in
fast/owner-doctrine-answers/ANSWERS.md v2.1 Part A + AM-13) and spec §7.2 invariant 3 (activity = 1 − |Δλ|/orb, zero at and
beyond the orb: O-ORB-3). Every test reads the SHIPPED rows — no synthetic row, no monkeypatch of the registry — so a number
that is not in the shipped row cannot pass. Nothing is a capture of current output.

Claims, each with ONE oracle that fails on its single planted reversion (named in the test):

  D-1  the shipped activity_kernel@1.3.0 row is RATIFIED at 1.0° with its ledger reference `nd_orb_scale` (ND-ORB-SCALE: Q2 a)
       (revert: empty the slot / ship another number);
  D-2  the shipped row scores a point contact as 1 − |Δλ|/1.0 (strength 1 at exact contact, zero at the band edge, no jump)
       (revert: a 2.0° scale);
  D-3  scoring orb = admission band (ND-ORB-ADMISSION and ND-ORB-SCALE are the same 1.0°, so strength reaches zero exactly where
       the contact ceases to exist, O-ORB-3) (revert: a 0.5° scale — the strength would fade out before the band edge);
  D-4  the row's persisted text names its three rulings (ND-ORB-SCALE, ND-ORB-ADMISSION, AM-13-RATIFIED) and both paths' score
       rule names AM-13-RATIFIED; the ledger carries the same value (revert: drop a ruling id from the row text);
  D-5  with the shipped rows neither `orb_not_ratified` nor `applicability_undeclared` can arise for a point or an extent target
       of P3/P4@1.3.0, in the builder's sweep and in the independent verifier (revert: empty the slot);
  D-6  the six AM-13 bindings K-1..K-6 all resolve to a declared applicability — P3 and P4 at 1.3.0 and at 1.2.0 × activity_kernel,
       P3 at 1.3.0 and 1.2.0 × graduated_drishti — with extent targets a membership step, true points the angular kernel, a
       varga_position unclassified (never 1), a residence/conjunction record not-applicable to the dṛṣṭi (AM-13 lines 1260-1265)
       (revert: classify varga_position as a point kind).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from services.gochara_kernel import convention
from services.gochara_kernel import window_sweep as ws
from services.gochara_kernel import window_verifier as wv
from services.gochara_rules import flat_selector as fs
from services.gochara_rules import kernel_factor
from services.gochara_rules import registry as reg
from services.gochara_rules.registry import composite_ref

from .test_a53_window_sweep import _POINT_KINDS, _SPAN_KINDS, _draft, _p4, _rec

DOC = reg.DOCTRINE_VERSION
KERNEL_REF = ("activity_kernel", DOC)
LEDGER = Path("/Users/Dev/kalayantra/run/DECISIONS_SURROGATE.jsonl")
#: the six bindings of AM-13-RATIFIED (ANSWERS.md AM-13): (path, version) × the factor it declares applicability for
SIX_BINDINGS = (
    (("P3", DOC), "activity_kernel"), (("P3", "1.2.0"), "activity_kernel"),                 # K-1 / K-3 (default / ND-H classes)
    (("P3", DOC), "graduated_drishti"), (("P3", "1.2.0"), "graduated_drishti"),             # K-2 / K-4
    (("P4", DOC), "activity_kernel"), (("P4", "1.2.0"), "activity_kernel"),                 # K-5 / K-6
)


def _shipped_rows(path: str, version: str) -> list[dict]:
    return [dict(r) for r in ws.registry_factor_rows(path, version)]


def _kernel_value(offset: float) -> float | None:
    out = kernel_factor.activity_kernel("degree_point", "point:100.0", factor_ref=KERNEL_REF,
                                        body_longitude_deg=100.0 + offset)
    assert out["reason"] is None, out
    return out["value"]


# ── D-1 ───────────────────────────────────────────────────────────────────────────────────────────

def test_d1_the_shipped_orb_row_is_ratified_at_one_degree_with_its_ledger_reference():
    flat = reg.FACTORS[KERNEL_REF]["operand_selector"]
    assert fs.kernel_flat_problems(flat) == []
    assert (flat["orb_state"], flat["orb_deg"]) == (fs.ORB_RATIFIED, 1.0)                  # Q2 (a): 1.0°
    assert flat["orb_decision_ref"] == "nd_orb_scale" == reg.ND_ORB_SCALE_LEDGER_ID.lower().replace("-", "_")
    assert reg.FACTORS[KERNEL_REF]["applicability"]["angular"]["orb_deg"] == 1.0           # the decoded form agrees
    assert reg.FACTORS[KERNEL_REF]["calibration_status"] == "uncalibrated_default"         # ANSWERS Q2: uncalibrated default
    # the superseded 1.1.0 row is NOT edited: it stays the unratified shape (a sealed version is never edited)
    old = reg.FACTORS[("activity_kernel", reg.KERNEL_VERSION)]["operand_selector"]
    assert old["orb_state"] == fs.ORB_UNRATIFIED and "orb_deg" not in old


# ── D-2 ───────────────────────────────────────────────────────────────────────────────────────────

def test_d2_the_shipped_row_scores_a_point_contact_as_one_minus_delta_over_one_degree():
    # spec §7.2 inv 3 with the ratified orb: strength 1 at exact contact, linear fade, zero at and beyond the orb
    assert _kernel_value(0.0) == 1.0
    assert _kernel_value(0.25) == pytest.approx(0.75) and _kernel_value(-0.25) == pytest.approx(0.75)
    assert _kernel_value(0.9) == pytest.approx(0.1)
    assert _kernel_value(1.0) == 0.0 and _kernel_value(1.5) == 0.0


# ── D-3 ───────────────────────────────────────────────────────────────────────────────────────────

def test_d3_scoring_orb_equals_the_admission_band_so_strength_reaches_zero_where_the_contact_ceases():
    scale = reg.FACTORS[KERNEL_REF]["applicability"]["angular"]["orb_deg"]
    assert scale == convention.ORB_TABLE["orb_conj_slow"]["orb_max_deg"] == convention.ORB_TABLE["orb_drishti_slow"]["orb_max_deg"]
    assert wv._POINT_ORB_DEG == {"conjunction": scale, "aspect": scale}                   # the verifier's independent band
    # just inside the admission band the strength is still positive, just outside there is no contact to score (O-ORB-3)
    assert _kernel_value(scale - 0.01) > 0.0 and _kernel_value(scale) == 0.0


# ── D-4 ───────────────────────────────────────────────────────────────────────────────────────────

def test_d4_the_rows_name_the_rulings_they_stand_on_and_the_ledger_carries_the_same_value():
    effect = reg.FACTORS[KERNEL_REF]["effect"]
    for ruling in (reg.ND_ORB_SCALE_LEDGER_ID, reg.ND_ORB_ADMISSION_LEDGER_ID, reg.AM13_LEDGER_ID):
        assert ruling in effect, ruling
    for pid in ("P3", "P4"):
        assert reg.AM13_LEDGER_ID in reg.RULE_PATHS[(pid, DOC)]["score_rule"]
        assert reg.RULE_PATHS[(pid, DOC)]["note"].startswith(reg.AM13_LEDGER_ID)
        assert reg.DOCTRINE_SUPERSEDED_PATHS[(pid, "1.0.0")]["ruling_ref"] == reg.AM13_LEDGER_ID


@pytest.mark.skipif(not LEDGER.is_file(), reason="owner decision ledger not present on this machine (CI): D-1..D-3 still hold")
def test_d4_the_owner_ledger_states_the_value_the_row_carries():
    rows = {}
    for line in LEDGER.read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            rows[r.get("id")] = r
    assert reg.ND_ORB_SCALE_LEDGER_ID in rows and reg.ND_ORB_ADMISSION_LEDGER_ID in rows and reg.AM13_LEDGER_ID in rows
    assert rows[reg.ND_ORB_SCALE_LEDGER_ID]["kind"] == "owner decision" and "1.0 deg" in rows[reg.ND_ORB_SCALE_LEDGER_ID]["decision"]
    assert rows[reg.ND_ORB_ADMISSION_LEDGER_ID]["kind"] == "owner decision" and "1.0 deg" in rows[reg.ND_ORB_ADMISSION_LEDGER_ID]["decision"]
    assert rows[reg.AM13_LEDGER_ID]["kind"] == "owner decision"


# ── D-5 ───────────────────────────────────────────────────────────────────────────────────────────

BLANKS = {"orb_not_ratified", "applicability_undeclared"}


def _records(path, **kw):
    """P3: one record; P4: the Jupiter + Saturn pair its prerequisite needs (distinct roots)."""
    if path == "P4":
        return _p4((0, 10), (0, 10), version=DOC, **kw)
    return [_rec("a", path=path, version=DOC, supports=((0, 10),), **kw)]


@pytest.mark.parametrize("path", ["P3", "P4"])
def test_d5_the_sweep_scores_point_and_extent_records_with_neither_blank_reason(path):
    rows_for = lambda p, v: _shipped_rows(p, v)                                           # noqa: E731  (the SHIPPED rows)
    cases = ((dict(relation="conjunction", kind="house_lord", delta_lambda_at=lambda t: 0.25), 0.75),
             (dict(relation="residence", kind="sign_span"), 1.0))
    for kw, expected in cases:
        (w,), _ = _draft(_records(path, **kw), rows_for)
        assert BLANKS.isdisjoint(w.unresolved), (kw["kind"], w.unresolved)
        assert w.unresolved == {} and w.score == pytest.approx(expected), (kw["kind"], w.score)


@pytest.mark.parametrize("path", ["P3", "P4"])
def test_d5_the_independent_verifier_reads_the_shipped_rows_with_neither_blank_reason(path):
    for row in _shipped_rows(path, DOC):
        if row["factor_id"] != "activity_kernel":
            continue
        for kind in _POINT_KINDS:
            assert wv._row_state(row, {"kind": kind, "relation": "conjunction"}, True, True) == ("fn",), kind
        for kind in _SPAN_KINDS + ("star",):
            assert wv._row_state(row, {"kind": kind, "relation": "residence"}, True, True) == ("const", 1.0), kind


# ── D-6 ───────────────────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("ref,factor_id", SIX_BINDINGS)
def test_d6_each_of_the_six_am13_bindings_resolves_to_a_declared_applicability(ref, factor_id):
    rows = {r["factor_id"]: r for r in _shipped_rows(*ref)}
    assert factor_id in rows, f"{ref} does not name {factor_id}"
    row = rows[factor_id]
    assert row["applicability"], f"{ref} × {factor_id}: applicability undeclared"
    if factor_id == "activity_kernel":
        assert row["rule_version"] == DOC                                                  # the ratified-orb row, not 1.1.0
        assert wv._row_state(row, {"kind": "house_span", "relation": "residence"}, True, True) == ("const", 1.0)  # extent: step
        assert wv._row_state(row, {"kind": "saham", "relation": "aspect"}, True, True) == ("fn",)                 # point: kernel
        # varga_position is NOT classified (AM-13 line 1263): unqualified for a stated reason, never 1
        assert wv._row_state(row, {"kind": "varga_position", "relation": "conjunction"}, True, True) == (
            "unq", "object_kind_not_covered_by_applicability")
    else:
        assert wv._row_state(row, {"kind": "house_lord", "relation": "aspect"}, True, True) == ("fn",)
        for relation in ("residence", "conjunction"):                                      # no offset: declared not-applicable
            assert wv._row_state(row, {"kind": "house_lord", "relation": relation}, True, True) == ("na",), relation
        assert row["operand_selector"]["node_cast_aspects"] == "none"                      # nodes cast no dṛṣṭi


def test_d6_the_sweep_leaves_varga_position_unqualified_and_never_one():
    rows_for = lambda p, v: _shipped_rows(p, v)                                           # noqa: E731
    (w,), _ = _draft(_records("P4", relation="conjunction", kind="varga_position", target="varga:9"), rows_for)
    assert w.score is None and set(w.unresolved) == {"object_kind_not_covered_by_applicability"}
