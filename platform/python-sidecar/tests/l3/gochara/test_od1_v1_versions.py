"""SR-OD1 V1 — the versions the owner-confirmed doctrine batch lands in (rule rows, binder, selection, H table,
ND-H in-place re-derivation, the orb row, P2@1.1.0, the inventory chain — builder side).

V1 adds STRUCTURE and no value: the P1 category mapping is D2's, the orb value is D1's, the vedha provider is C1's. The
oracles are the owner's rulings (OWNER-DOCTRINE-CONFIRMED-20261021; /Users/Dev/kalayantra/run/DECISIONS_SURROGATE.jsonl) and
the classical objective definitions the registry already cites; nothing is a capture of current output.

Claims, each with ONE oracle that fails on its single planted reversion (named in the test):

  V-1  the MEASURING profile is byte-for-byte the 1.0.0 catalogue and selection (MEASURING_BUILD_CONTRACT; `default_profile_intact`)
       (revert: put a 1.3.0 / 1.1.0 ref into the unconditional `BOUND_PATH_REFS` / `SELECTED_PATH_REFS`);
  V-2  the FINAL profile binds P1/P3/P4@1.3.0 and P2@1.1.0 and selects them by default, P5 held at 1.0.0 (P1-MAPPING-DECISION,
       AM-13-RATIFIED, AM-18) (revert: leave P2 / P3 / P4 on their old selection);
  V-3  the eight ND-H classes (P1/P3/P4) and bereavement (P3/P4) stay at 1.2.0 — AM-13-RATIFIED K-4/K-5/K-6, ND-H, ND-P2 rule 3
       (revert: select 1.3.0 for them);
  V-4  maitri_compound is RETIRED from P1 (Q7 b): no 1.3.0 row, named by no P1 row at 1.3.0 or 1.2.0, and the sealed 1.0.0 rows
       are untouched (revert: keep maitri in P1@1.3.0);
  V-5  the 1.2.0 rows are re-derived IN PLACE from the 1.3.0 soft factors (+ karaka_agent), prerequisites unchanged
       (SR-SOLVER-PLAN-1) (revert: leave 1.2.0 on the 1.0.0 factors);
  V-6  the AM-13 bindings K-1..K-3: P3 reads activity_kernel@1.3.0 + graduated_drishti@1.1.0, P4 the kernel only; varga_position is
       unclassified and nodes cast no dṛṣṭi (AM-13-RATIFIED) (revert: classify varga_position as a point kind);
  V-7  the orb row: shipped UNRATIFIED with no value and no reference (D1 is the only place a value enters); the slot, filled with
       the confirmed ND-ORB-SCALE value, yields a ratified row the existing consumer evaluates as 1 − |Δλ|/orb (spec §7.2 inv 3);
       an orb without a ledger reference is refused (revert: ratify without a reference);
  V-8  no shipped registry row carries a placeholder decision reference, and the detector can read false (N.8)
       (revert: a TEST-PLACEHOLDER-ORB reference in a shipped row);
  V-9  ND-ORB-ADMISSION: the confirmed 1.0° admission band equals the built convention band and the verifier's band;
  V-10 the H table of 1.3.0 is the cited truth table for the classes that run it, never another version's H for the eight, and
       the 1.3.0 path rows pin its digest (revert: drop 1.3.0 from `H_TABLE_VERSIONS`);
  V-11 V1 changes no enumeration: P1/P3/P4 at 1.3.0 enumerate exactly the 1.0.0 edges for a class that runs them
       (revert: enumerate under a different H);
  V-12 the binder is closed: every soft factor of every bound path is bound, every persisted selector satisfies the 1154 grammar,
       Form-B dignity rungs are ordered weakest → strongest (revert: bind a path without its factor);
  V-13 the inventory chain (builder): one included version per path, every sealed version accounted, 1.0.0 superseded by 1.3.0 under
       the owner ruling, 1.3.0 not applicable to a class that runs 1.2.0, and the independent verifier derives the SAME pins for
       every class (revert: drop the doctrine chain from the planner);
  V-14 the ND-H in-place measured check can read true: it reports a seeding migration or a 1.2.0 golden row when one exists
       (revert: scan nothing);
  V-15 no scored cell is "unchanged" under the final profile any more (the J4D equality premise): every cell is on a new version or
       suppressed (revert: leave a cell on its measuring version).
"""
from __future__ import annotations

import pytest

from services.gochara_kernel import convention
from services.gochara_kernel import inventory as inv
from services.gochara_kernel import inventory_verifier as ver
from services.gochara_kernel import rule_registry as rr
from services.gochara_kernel import window_verifier as wv
from services.gochara_rules import flat_selector as fs
from services.gochara_rules import kernel_factor
from services.gochara_rules import registry as reg
from services.gochara_rules.registry import composite_ref

from .test_a53_inventory import CHART, DASHA, FULL, H0, H1
from .test_a53_version_selection import V_H, V_P5, VCHART, _view
from .test_nd_h_builder_tiers import EIGHT, OTHERS

ND = reg.ND_H_VERSION
DOC = reg.DOCTRINE_VERSION
ALL_CLASSES = sorted(set(reg.CLASS_BY_NAME) - {"birth_anchor"})
#: the owner-confirmed value of ND-ORB-SCALE / ND-ORB-ADMISSION (DECISIONS_SURROGATE.jsonl, 2026-10-21T12:37Z)
CONFIRMED_ORB = {"orb_deg": 1.0, "orb_decision_ref": "nd_orb_scale"}


@pytest.fixture
def final():
    with rr.rule_profile(final_rules=True):
        yield


# ── V-1 the measuring profile is untouched ────────────────────────────────────────────────────────────

def test_v1_the_measuring_profile_is_exactly_the_1_0_0_catalogue_and_selection():
    one = lambda refs: {v for _p, v in refs}                                    # noqa: E731
    assert rr.bound_path_refs() == tuple((p, "1.0.0") for p in ("P1", "P2", "P3", "P4", "P5"))
    assert one(rr.bound_factor_refs()) == {"1.0.0"}
    for cls in ALL_CLASSES:
        assert set(rr.selected_versions_for(cls).values()) == {"1.0.0"}, cls
    assert {r["rule_version"] for r in rr.path_rows()} == {"1.0.0"}
    assert {r["rule_version"] for r in rr.factor_rows()} == {"1.0.0"}
    # the measuring golden is 1.0.0 only (MEASURING_BUILD_CONTRACT): nothing of V1 may reach that profile
    assert not set(rr.FINAL_ONLY_PATH_REFS) & set(rr.BOUND_PATH_REFS)
    assert not set(rr.FINAL_ONLY_FACTOR_REFS) & set(rr.BOUND_FACTOR_REFS)


# ── V-2 / V-3 the final catalogue and selection ───────────────────────────────────────────────────────────

def test_v2_the_final_profile_binds_the_doctrine_rows_and_selects_them_by_default(final):
    refs = set(rr.bound_path_refs())
    legacy = {(p, "1.0.0") for p in ("P1", "P2", "P3", "P4", "P5")}
    nd_h = {(p, ND) for p in ("P1", "P3", "P4")}
    doctrine = {(p, DOC) for p in ("P1", "P3", "P4")}
    assert refs == legacy | nd_h | doctrine | {("P2", "1.1.0")}
    # P3/P4/P5 @1.1.0 stay unbound (FB-30): the 1.3.0 rows supersede them
    assert not refs & {("P3", "1.1.0"), ("P4", "1.1.0"), ("P5", "1.1.0")}
    for cls in OTHERS:
        if cls == "bereavement":
            continue
        assert rr.selected_versions_for(cls) == {"P1": DOC, "P2": "1.1.0", "P3": DOC, "P4": DOC, "P5": "1.0.0"}, cls


def test_v3_the_nd_h_classes_and_bereavement_keep_1_2_0_on_their_paths(final):
    for cls in EIGHT:
        assert rr.selected_versions_for(cls) == {"P1": ND, "P2": "1.1.0", "P3": ND, "P4": ND, "P5": "1.0.0"}, cls
    # ND-P2 rule 3: bereavement runs P3/P4 at 1.2.0 (its natal-Sun target); its P1 follows the doctrine default
    assert rr.selected_versions_for("bereavement") == {"P1": DOC, "P2": "1.1.0", "P3": ND, "P4": ND, "P5": "1.0.0"}


# ── V-4 / V-5 maitrī retired, the 1.2.0 rows re-derived in place ───────────────────────────────────────

def test_v4_maitri_is_retired_from_p1_and_the_sealed_1_0_0_rows_are_untouched():
    named = {f for ref in (("P1", DOC), ("P1", ND)) for f, _v in reg.RULE_PATHS[ref]["soft_factors"]}
    assert "maitri_compound" not in named
    assert not [k for k in reg.FACTORS if k[0] == "maitri_compound" and k[1] != "1.0.0"]
    assert reg.RETIRED_FACTORS[composite_ref("maitri_compound", "1.0.0")]["retired_from"] == composite_ref("P1", DOC)
    # sealed rows are never edited: P1@1.0.0 still names maitrī, P3@1.0.0 the 1.0.0 kernel and dṛṣṭi (AM-13 history),
    # and the 1.0.0 dignity row keeps its six categories
    assert ("maitri_compound", "1.0.0") in map(tuple, reg.RULE_PATHS[("P1", "1.0.0")]["soft_factors"])
    assert list(map(tuple, reg.RULE_PATHS[("P3", "1.0.0")]["soft_factors"])) == [
        ("activity_kernel", "1.0.0"), ("graduated_drishti", "1.0.0")]
    assert reg.FACTORS[("dignity_of_transit_sign", "1.0.0")]["categories"] == [
        "exaltation", "own", "friendly", "neutral", "inimical", "debility"]


@pytest.mark.parametrize("pid", ["P1", "P3", "P4"])
def test_v5_the_nd_h_rows_take_the_1_3_0_soft_factors_in_place_and_keep_everything_else(pid):
    doctrine, nd_h, base = reg.RULE_PATHS[(pid, DOC)], reg.RULE_PATHS[(pid, ND)], reg.RULE_PATHS[(pid, "1.0.0")]
    assert list(map(tuple, nd_h["soft_factors"])) == [*map(tuple, doctrine["soft_factors"]), ("karaka_agent", ND)]
    assert nd_h["prerequisites"] == base["prerequisites"] == doctrine["prerequisites"]
    assert all(v == DOC or f in ("karaka_agent", "graduated_drishti") for f, v in map(tuple, nd_h["soft_factors"]))
    assert nd_h["ruling_ref"] == reg.ND_H_RULING                      # the ND-H stamp is unchanged by the re-derivation


# ── V-6 the AM-13 bindings ──────────────────────────────────────────────────────────────────────────

def test_v6_am13_bindings_k1_to_k3_and_the_ratified_exclusions():
    assert list(map(tuple, reg.RULE_PATHS[("P3", DOC)]["soft_factors"])) == [
        ("activity_kernel", DOC), ("graduated_drishti", "1.1.0")]
    assert list(map(tuple, reg.RULE_PATHS[("P4", DOC)]["soft_factors"])) == [("activity_kernel", DOC)]
    kernel = reg.FACTORS[("activity_kernel", DOC)]["applicability"]
    assert kernel["span"]["object_kinds"] == ["sign_span", "house_span", "star"]       # extent targets: membership step
    assert "varga_position" not in kernel["span"]["object_kinds"] + kernel["angular"]["object_kinds"]   # unclassified
    drishti = reg.FACTORS[("graduated_drishti", "1.1.0")]
    assert drishti["operand_selector"]["node_cast_aspects"] == "none"                  # nodes cast no dṛṣṭi
    assert drishti["applicability"] == {"relations": ["aspect"]}


# ── V-7 the orb row ──────────────────────────────────────────────────────────────────────────────────

def test_v7_the_shipped_orb_row_is_exactly_what_the_single_slot_declares():
    """A number reaches the row ONLY through `ORB_DECISION_1_3_0` (D1's one-line flip): the shipped selector equals the one the slot
    builds, an empty slot ships no value and no reference, and the consumer then answers blank-with-reason, never a number."""
    flat = reg.FACTORS[("activity_kernel", DOC)]["operand_selector"]
    assert flat == reg.kernel_flat_1_3_0(reg.ORB_DECISION_1_3_0) and fs.kernel_flat_problems(flat) == []
    out = kernel_factor.activity_kernel("degree_point", "point:100.0", factor_ref=("activity_kernel", DOC),
                                        body_longitude_deg=100.25)
    if reg.ORB_DECISION_1_3_0 is None:
        assert flat["orb_state"] == fs.ORB_UNRATIFIED and "orb_deg" not in flat and "orb_decision_ref" not in flat
        assert (out["value"], out["reason"]) == (None, "orb_not_ratified")
    else:
        assert flat["orb_state"] == fs.ORB_RATIFIED and flat["orb_decision_ref"] == reg.ORB_DECISION_1_3_0["orb_decision_ref"]
        assert out["reason"] is None and out["value"] is not None


def test_v7_the_slot_filled_with_the_confirmed_value_is_a_ratified_row_the_existing_consumer_scores(monkeypatch):
    flat = reg.kernel_flat_1_3_0(CONFIRMED_ORB)
    assert fs.kernel_flat_problems(flat) == []
    assert (flat["orb_state"], flat["orb_deg"], flat["orb_decision_ref"]) == (fs.ORB_RATIFIED, 1.0, "nd_orb_scale")
    assert fs.TOKEN_RE.match(flat["orb_decision_ref"])                                  # a selector token (1154 grammar)
    row = dict(reg.FACTORS[("activity_kernel", DOC)], operand_selector=flat, applicability=fs.decode_kernel(flat))
    monkeypatch.setitem(reg.FACTORS, ("activity_kernel", DOC), row)
    ref = ("activity_kernel", DOC)
    score = lambda offset: kernel_factor.activity_kernel(                               # noqa: E731
        "degree_point", "point:100.0", factor_ref=ref, body_longitude_deg=100.0 + offset)["value"]
    # spec §7.2 inv 3 (GOCHARA_DESIGN_SPECS_v1_4): activity = 1 − |Δλ|/orb, zero at and beyond the orb (O-ORB-3)
    assert score(0.0) == 1.0 and score(0.25) == pytest.approx(0.75) and score(-0.25) == pytest.approx(0.75)
    assert score(1.0) == 0.0 and score(1.5) == 0.0


def test_v7_an_orb_without_its_ledger_reference_or_with_a_non_positive_value_is_refused():
    with pytest.raises(ValueError):
        reg.kernel_flat_1_3_0({"orb_deg": 1.0, "orb_decision_ref": None})             # ratified needs a token (not a number alone)
    with pytest.raises(ValueError):
        reg.kernel_flat_1_3_0({"orb_deg": 0.0, "orb_decision_ref": "nd_orb_scale"})
    with pytest.raises(ValueError):
        reg.kernel_flat_1_3_0({"orb_deg": 1.0, "orb_decision_ref": "ND-ORB-SCALE"})   # the ledger id is not a selector token


# ── V-8 no placeholder decision reference ships ────────────────────────────────────────────────────

def _placeholder_refs(factors) -> list[str]:
    """Every `*_decision_ref` value of a factor table that names a test/placeholder decision (N.8: the detector must be able
    to read false — see the planted row below)."""
    bad = []
    for key, row in sorted(factors.items()):
        for source in (row.get("operand_selector") or {}, row):
            for name, value in source.items():
                if name.endswith("decision_ref") and isinstance(value, str) \
                        and value.lower().startswith(("test", "placeholder", "tbd", "todo")):
                    bad.append(f"{key}:{name}={value}")
    return bad


def test_v8_no_shipped_registry_row_carries_a_placeholder_decision_reference():
    assert _placeholder_refs(reg.FACTORS) == []
    planted = dict(reg.FACTORS)                       # the planted reversion: the solver-lane overlay leaking into a shipped row
    planted[("activity_kernel", DOC)] = dict(planted[("activity_kernel", DOC)],
                                             operand_selector=dict(orb_state="ratified", orb_deg=1.0,
                                                                   orb_decision_ref="test_placeholder_orb"))
    assert _placeholder_refs(planted) == ["('activity_kernel', '1.3.0'):orb_decision_ref=test_placeholder_orb"]


# ── V-9 the admission band ───────────────────────────────────────────────────────────────────────────

def test_v9_the_confirmed_admission_band_equals_the_built_convention_and_the_verifiers_band():
    admitted = CONFIRMED_ORB["orb_deg"]                                                 # ND-ORB-ADMISSION: 1.0° (Q1 a)
    assert convention.ORB_TABLE["orb_conj_slow"]["orb_max_deg"] == admitted
    assert convention.ORB_TABLE["orb_drishti_slow"]["orb_max_deg"] == admitted
    assert wv._POINT_ORB_DEG == {"conjunction": admitted, "aspect": admitted}


# ── V-10 the H table ─────────────────────────────────────────────────────────────────────────────────

def test_v10_the_1_3_0_h_table_is_the_cited_truth_table_and_never_another_versions_h_for_the_eight():
    assert reg.H_TABLE_VERSIONS[DOC] == "spec_2_2"
    for cls in OTHERS:                               # a class that runs 1.3.0 reads the very H it read at 1.0.0
        assert reg.signature_houses(cls, CHART, DOC) == reg.signature_houses(cls, CHART, "1.0.0"), cls
    for cls in EIGHT:                                # the eight are not read at 1.3.0: H unknown, not a fallback to 1.2.0's
        assert reg.signature_houses(cls, CHART, DOC) is None, cls
    assert reg.h_table(DOC)["classes"] == reg.h_table("1.0.0")["classes"]
    assert len({reg.h_table_sha256(v) for v in ("1.0.0", "1.1.0", DOC, ND)}) == 4
    for pid in ("P1", "P3", "P4"):
        assert f"sha256:{reg.h_table_sha256(DOC)}" in reg.RULE_PATHS[(pid, DOC)]["score_rule"]
        assert reg.RULE_PATHS[(pid, DOC)]["h_table_version"] == DOC
    with pytest.raises(KeyError):
        reg.signature_houses("marriage", CHART, "9.9.9")


# ── V-11 no enumeration moved ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("cls", ["marriage", "career_entry", "major_loss", "illness_acute", "bereavement"])
def test_v11_p1_p3_p4_at_1_3_0_enumerate_the_1_0_0_edges(cls):
    from services.gochara_kernel import evaluator as ev
    for pid in ("P1", "P3", "P4"):
        if cls == "bereavement" and pid != "P1":
            continue          # bereavement P3/P4 run at 1.2.0 (ND-P2 rule 3): their 1.3.0 pin is not applicable
        old = ev.enumerate_edges(cls, pid, CHART, rule_version="1.0.0")
        new = ev.enumerate_edges(cls, pid, CHART, rule_version=DOC)
        assert old and [ev.replace(e, rule_version="1.0.0") for e in new] == old, (cls, pid)


# ── V-12 the binder is closed ────────────────────────────────────────────────────────────────────────

def test_v12_every_bound_path_names_only_bound_factors_and_every_persisted_selector_is_grammatical(final, monkeypatch):
    rr._membership_consistent()
    bound = set(rr.bound_factor_refs())
    for ref in rr.bound_path_refs():
        assert set(map(tuple, reg.RULE_PATHS[ref]["soft_factors"])) <= bound, ref
    rows = {(r["factor_id"], r["rule_version"]): r for r in rr.factor_rows()}
    assert set(rows) == bound
    for ref, row in rows.items():
        assert fs.flat_problems(row["operand_selector"]) == [], ref
    assert rows[("dignity_of_transit_sign", DOC)]["doctrine_ordering"] == [
        "debility", "inimical", "neutral", "friendly", "own", "mulatrikona", "exaltation"]
    assert rows[("dignity_of_transit_sign", "1.0.0")]["doctrine_ordering"] == [   # the sealed 1.0.0 ordering is untouched
        "debility", "inimical", "neutral", "friendly", "own", "exaltation"]
    # a path whose factor is not bound is refused before any SQL (the closure is a detector, not a convention)
    monkeypatch.setitem(reg.RULE_PATHS, ("P1", DOC),
                        dict(reg.RULE_PATHS[("P1", DOC)], soft_factors=[("combustion", "9.9.9")]))
    with pytest.raises(ValueError, match="not bound"):
        rr._membership_consistent()


# ── V-13 the inventory chain, builder side, against the independent verifier ──────────────────────────────

def _plan_final(cls):
    sealed = list(rr.bound_path_refs())
    selected = rr.selected_versions_for(cls)
    plan = inv.plan_class_inventory(
        event_class=cls, chart=CHART, horizon=(H0, H1), sealed_paths=sealed, capability=FULL, selected_versions=selected,
        path_exclusions={"P5": inv.Exclusion("tier_withheld_by_ruling", "ruling:M20261001T121451-1a8d", "M20261001T121451-1a8d")},
        h_unknown_exclusion=inv.Exclusion("inputs_unavailable", "ruling:TEST-H-UNKNOWN", "TEST-H-UNKNOWN"), dasha_rows=DASHA)
    return plan, ver.derive_class_pins(
        cls, VCHART, sealed, excluded_agents=("moon",), selected_versions={k.lower(): v for k, v in selected.items()},
        path_exclusions=V_P5, h_unknown_exclusion=V_H)


def test_v13_one_included_version_per_path_and_every_sealed_version_accounted_for_a_default_class(final):
    plan, _ = _plan_final("marriage")
    pins = {(p.path_id, p.rule_version): p for p in plan.pins}
    assert set(pins) == set(rr.bound_path_refs())                                       # a TOTAL partition
    for pid in ("P1", "P3", "P4"):
        assert pins[(pid, DOC)].disposition == "included" and pins[(pid, DOC)].obligations
        old = pins[(pid, "1.0.0")]
        assert (old.disposition, old.exclusion_reason, old.ruling_ref, old.basis) == (
            "excluded", "superseded_by_version", None, f"ruling:{reg.DOCTRINE_PATH_RULINGS[pid]}")
        assert pins[(pid, ND)].exclusion_reason == "not_applicable_to_class"
    assert pins[("P2", "1.1.0")].disposition == "included"
    assert pins[("P2", "1.0.0")].basis == inv.supersession_basis("P2", "1.0.0", "1.1.0") \
        == "spec:GOCHARA_SPECS_V1_5_AMENDMENTS@1.5#AM-18-p2-1.0.0-superseded-by-1.1.0"
    assert [p.path_id for p in plan.pins if p.disposition == "included"].count("P3") == 1


def test_v13_a_class_on_1_2_0_does_not_search_1_3_0_and_the_ruling_is_the_one_that_put_it_on_1_2_0(final):
    for cls, ruling in [("business_launch", "ND-H-20261005"), ("bereavement", "ND-P2-20261005")]:
        plan, _ = _plan_final(cls)
        pins = {(p.path_id, p.rule_version): p for p in plan.pins}
        paths = ("P1", "P3", "P4") if cls != "bereavement" else ("P3", "P4")
        for pid in paths:
            assert pins[(pid, ND)].disposition == "included"
            gone = pins[(pid, DOC)]
            assert (gone.disposition, gone.exclusion_reason, gone.basis) == (
                "excluded", "not_applicable_to_class", f"ruling:{ruling}"), (cls, pid)


@pytest.mark.parametrize("cls", ALL_CLASSES)
def test_v13_the_independent_verifier_derives_the_same_pins_as_the_planner(cls, final):
    plan, vpins = _plan_final(cls)
    assert sorted(map(_view, plan.pins)) == sorted(map(_view, vpins)), cls


def test_v13_the_doctrine_chain_is_both_sides_own_table_and_they_agree():
    registry_chain = {(p.lower(), v): tuple(row["superseded_by"])[1] for (p, v), row in reg.DOCTRINE_SUPERSEDED_PATHS.items()}
    assert registry_chain == ver._DOCTRINE_SUPERSEDED
    assert {p.lower(): r for p, r in reg.DOCTRINE_PATH_RULINGS.items()} == ver._DOCTRINE_RULING
    # the AM-13 / AM-18 table is untouched (V1 adds a chain beside it)
    assert reg.SUPERSEDED_PATHS[("P3", "1.0.0")]["superseded_by"] == ("P3", "1.1.0")


def test_v13_without_the_doctrine_chain_a_default_class_cannot_be_planned(final, monkeypatch):
    monkeypatch.setattr(reg, "DOCTRINE_SUPERSEDED_PATHS", {})
    with pytest.raises(inv.InventoryBlocked, match="neither the selected"):
        _plan_final("marriage")


# ── V-15 the J4D "unchanged cell" premise is gone, and says so ──────────────────────────────────────

def test_v15_with_the_doctrine_rows_no_scored_cell_is_unchanged_so_the_j4d_equality_has_nothing_to_compare():
    """Why `kala_db/test_j4d_slice_qualification.py` and `test_j4d_slice_lane_db.py` run on the pre-doctrine final profile: under the
    real registry every P1-P4 cell of every scored class is either on a different version (P1/P3/P4@1.3.0 or 1.2.0, P2@1.1.0) or
    suppressed (parental P2). The measuring-vs-final equality proof is superseded by the trial under window_qualification/1."""
    from scripts.kala_gochara_cutover import j4d_slice_qualify as q
    kinds = {(cls, path): q.cell_expectation(cls, path)["kind"] for cls in ALL_CLASSES for path in ("P1", "P2", "P3", "P4")}
    assert set(kinds.values()) <= {"final", "suppressed"}, sorted(c for c, k in kinds.items() if k == "same")
    assert not [c for c in ALL_CLASSES if q.is_unchanged_class(c)]


# ── V-14 the measured check can read true ───────────────────────────────────────────────────────────

def _check():
    import importlib.util
    from pathlib import Path
    path = Path(__file__).resolve().parents[3] / "scripts" / "kala_gochara_cutover" / "od1_nd_h_in_place_check.py"
    spec = importlib.util.spec_from_file_location("od1_nd_h_in_place_check", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v14_the_in_place_check_finds_nothing_in_the_repository_and_the_measuring_catalogue():
    check = _check()
    assert check.seeding_migrations() == []
    legacy = check.legacy_profile_catalogue()
    assert not legacy["has_1_2_0"] and not legacy["selected_has_1_2_0"]


def test_v14_the_check_reports_a_seeding_migration_and_a_1_2_0_golden_row_when_they_exist(tmp_path):
    check = _check()
    (tmp_path / "platform" / "migrations").mkdir(parents=True)
    (tmp_path / "platform" / "migrations" / "9999_seed.sql").write_text(
        "INSERT INTO public.ka_gochara_rule_path (path_id, rule_version) VALUES ('P1', '1.2.0');\n")
    (tmp_path / "platform" / "migrations" / "9998_read.sql").write_text(
        "SELECT 1 FROM public.ka_gochara_search_path_pin WHERE rule_version = '1.2.0';\n")      # a read is not a seed
    assert check.seeding_migrations(tmp_path) == ["9999_seed.sql: ka_gochara_rule_path"]
    import json
    golden = tmp_path / "golden"
    golden.mkdir()
    (golden / "records.jsonl").write_text(json.dumps({"gkey": json.dumps({"rule_version": "1.2.0"})}) + "\n")
    (golden / "windows.jsonl").write_text(json.dumps({"rule_version": "1.0.0"}) + "\n")
    assert check.golden_versions(golden) == {"records": {"1.2.0": 1}, "windows": {"1.0.0": 1}}
    assert check.measure(golden)["references_1_2_0"] is True
