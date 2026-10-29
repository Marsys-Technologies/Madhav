"""Unit structure (SUR-RB-23): groups, OR, per-episode area filter, Moon on G1 only, the real manifest."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from services.rulebook.scorer import config as C
from services.rulebook.scorer.core import FamilyContext, score_family, scorable_mask
from services.rulebook.scorer.model import ChartTimeline, Episode, MemberSpec, ScorerError, UnitSpec, units_from_manifest

from ._toy import BASE, month_window, runs_series

CAREER = "career_adv_change_entry"
ILLNESS = "illness_chronic_surgery"


def _unit(uid, groups, pol="promotive", moon=()):
    gs = tuple(tuple(MemberSpec(r, frozenset(tags), moon=r in moon) for r, tags in g) for g in groups)
    return UnitSpec(uid, C.FAMILY_DASHA, pol, "cluster", gs)


# ── the per-episode area filter ───────────────────────────────────────────────────
def test_variant_keeps_only_members_whose_own_tags_match_the_episode_area():
    u = _unit("VC", [[("A", [CAREER]), ("B", [ILLNESS]), ("C", [CAREER, ILLNESS])]])
    assert u.variant(CAREER, True).groups == (("A", "C"),)
    assert u.variant(ILLNESS, True).groups == (("B", "C"),)
    assert u.variant("major_gain", True) is None  # no member qualifies: the unit does not apply to this episode
    g = _unit("G", [[("X", [C.GENERAL])]])
    assert g.variant("anything_at_all", True).groups == (("X",),)  # GENERAL applies to every area


def test_unit_does_not_apply_to_an_episode_of_an_area_no_member_carries():
    # CASE 1 (SUR-RB-23): one area's claim is not credited to another area's occurrence
    rng = np.random.default_rng(11)
    n = 365 * 12
    eps_career = []
    t = ChartTimeline("c0", BASE - 5000, BASE, BASE + n - 1)
    rid_b = np.zeros(n, dtype=np.int8)
    for k in range(6):  # six career episodes, months spaced out
        lo, hi = month_window(1990 + k * 2, 3)
        eps_career.append(Episode(0, CAREER, C.FAVOURABLE, C.G2, lo, hi))
        rid_b[lo - BASE : hi - BASE + 1] = 1  # member B (illness claim) is TRUE exactly in the career windows
    t.states["A"] = runs_series(rng, n, 0.2, 20)
    t.states["B"] = rid_b
    u = _unit("VC", [[("A", [CAREER]), ("B", [ILLNESS])]])
    ctx = FamilyContext(C.FAMILY_DASHA, [t], [u])
    # for the career episodes only A enters; B's perfect alignment must not be credited
    assert [v.groups for v in ctx.klass_variants(("promotive", CAREER, C.G2))] == [(("A",),)]
    ep = eps_career[0]
    scored = [e for e, ok in zip(eps_career, scorable_mask(ctx, eps_career)) if ok]
    # an episode of another area has no applicable member: not scored at all
    other = Episode(0, "major_gain", C.FAVOURABLE, C.G2, *month_window(1992, 6))
    assert scorable_mask(ctx, [other]) == [False]
    # and the same unit with B credited would score these episodes near 1; with the filter it must not
    ctx_b_only = FamilyContext(C.FAMILY_DASHA, [t], [_unit("VB", [[("B", [CAREER])]])])
    # (B declared for CAREER: the alignment is then counted and the class score is high)
    from services.rulebook.scorer.core import assemble
    asm_a = assemble(ctx, "5y", scored, False, False)
    asm_b = assemble(ctx_b_only, "5y", [e for e, ok in zip(eps_career, scorable_mask(ctx_b_only, eps_career)) if ok], False, False)
    score_a = sum(r["BT"][r["i0"]] for r in asm_a.recs)
    score_b = sum(r["BT"][r["i0"]] for r in asm_b.recs)
    assert score_b > 0.9 and score_a < score_b - 0.2


def test_always_true_defective_member_of_another_area_does_not_switch_an_or_on():
    # CASE 2 (SUR-RB-23): an E cluster's groups are OR-ed, but only groups with an eligible member count
    rng = np.random.default_rng(12)
    n = 365 * 14
    t = ChartTimeline("c0", BASE - 5000, BASE, BASE + n - 1)
    t.states["X"] = runs_series(rng, n, 0.2, 15)  # the career claim, informative
    t.states["Y"] = np.ones(n, dtype=np.int8)  # the illness claim, defective: TRUE on every day
    u = _unit("VC", [[("X", [CAREER])], [("Y", [ILLNESS])]])
    ctx = FamilyContext(C.FAMILY_DASHA, [t], [u])
    v = u.variant(CAREER, True)
    assert v.groups == (("X",),) and v.components() == (("m", "X"),)  # Y is not in the OR
    eps = [Episode(0, CAREER, C.FAVOURABLE, C.G2, *month_window(1991 + k, 5)) for k in range(8)]
    assert all(scorable_mask(ctx, eps))  # X alone is informative; with Y OR-ed in the state would be constant and the unit dropped
    # for an illness episode only Y qualifies and Y is constant: uninformative, the episode is not scored
    ill = [Episode(0, ILLNESS, C.FAVOURABLE, C.G2, *month_window(1991 + k, 5)) for k in range(3)]
    assert scorable_mask(ctx, ill) == [False, False, False]
    # an area that both groups carry does OR them (the always-true Y then makes the state constant)
    u2 = _unit("VD", [[("X", [CAREER, ILLNESS])], [("Y", [CAREER, ILLNESS])]])
    ctx2 = FamilyContext(C.FAMILY_DASHA, [t], [u2])
    assert ctx2.klass_variants(("promotive", CAREER, C.G2))[0].components()[0][0] == "or"
    assert scorable_mask(ctx2, eps) == [False] * 8


def test_rival_group_members_are_averaged_and_separate_groups_are_ored():
    u = _unit("VC", [[("A", [C.GENERAL]), ("B", [C.GENERAL])]])
    assert u.variant(CAREER, True).components() == (("m", "A"), ("m", "B"))  # one group: percentiles averaged
    u = _unit("VC", [[("A", [C.GENERAL])], [("B", [C.GENERAL])], [("C", [C.GENERAL]), ("D", [C.GENERAL])]])
    comps = u.variant(CAREER, True).components()
    assert len(comps) == 1 and comps[0][0] == "or" and comps[0][1] == (("A",), ("B",), ("C", "D"))


def test_moon_member_is_scored_on_g1_episodes_only():
    u = _unit("VM", [[("MO", [C.GENERAL]), ("SU", [C.GENERAL])]], moon=("MO",))
    assert u.variant(CAREER, moon_ok=False).groups == (("SU",),)
    assert u.variant(CAREER, moon_ok=True).groups == (("MO", "SU"),)
    only_moon = _unit("VM2", [[("MO", [C.GENERAL])]], moon=("MO",))
    assert only_moon.variant(CAREER, moon_ok=False) is None  # on a month episode the unit does not apply
    rng = np.random.default_rng(1)
    n = 3000
    t = ChartTimeline("c", BASE - 4000, BASE, BASE + n - 1, {"MO": runs_series(rng, n, 0.2, 10)})
    ctx = FamilyContext(C.FAMILY_DASHA, [t], [only_moon])
    g2 = Episode(0, CAREER, C.FAVOURABLE, C.G2, *month_window(1991, 7))
    g1 = Episode(0, CAREER, C.FAVOURABLE, C.G1, BASE + 400, BASE + 402)
    assert scorable_mask(ctx, [g2, g1]) == [False, True]


# ── the real manifest and the final cluster table ─────────────────────────────────
LIB = Path("/Users/Dev/Archives/madhav-research-library")
MANIFEST = LIB / "10_engine/unit-manifest/rev3-20261030/UNIT_MANIFEST_v1_0.json"
CLUSTERS = LIB / "02_plans/rule-book-programme/cluster-classification/FINAL_CLUSTER_TABLE_v1_1.json"
needs_library = pytest.mark.skipif(not (MANIFEST.exists() and CLUSTERS.exists()), reason="private research library not on this machine")


@needs_library
def test_final_cluster_table_hash_and_totals():
    assert hashlib.sha256(CLUSTERS.read_bytes()).hexdigest() == C.CLUSTER_TABLE_SHA256
    table = json.loads(CLUSTERS.read_text())
    tally = {}
    for c in table["clusters"]:
        tally[c["scored_as"]] = tally.get(c["scored_as"], 0) + 1
    assert tally == {"E": 13, "R": 9, "MIXED": 8, "SINGLE": 3, "NOT_EVALUABLE": 6}


@needs_library
def test_units_from_the_real_manifest_follow_the_table():
    manifest = json.loads(MANIFEST.read_text())
    table = json.loads(CLUSTERS.read_text())
    by_id = {c["cluster_id"]: c for c in table["clusters"]}
    for plane in (C.FAMILY_DASHA, C.FAMILY_TRANSIT):
        units = units_from_manifest(manifest, table, plane)
        assert units and all(u.plane == plane for u in units)
        ids = {u.unit_id for u in units}
        for u in units:
            ev = {m["rulebook_id"] for x in manifest["units"] if x["unit_id"] == u.unit_id for m in x["members"] if m["status"] == "evaluable"}
            assert {m.rid for m in u.members()} == ev  # only evaluable members, all of them
            if u.kind == "cluster":
                assert [[m.rid for m in g] for g in u.groups] == by_id[u.unit_id]["groups_scored"]
        for cid, row in by_id.items():
            if row["scored_as"] == "NOT_EVALUABLE":
                assert cid not in ids  # never scored
    d = units_from_manifest(manifest, table, C.FAMILY_DASHA)
    assert {u.polarity for u in d} <= {"promotive", "obstructive"}
    # the Moon's one evaluable transit member is flagged
    moon = [m for u in units_from_manifest(manifest, table, C.FAMILY_TRANSIT) for m in u.members() if m.moon]
    assert len(moon) == 1
    # VC30 is the MIXED cluster with eight groups
    vc30 = next(u for u in units_from_manifest(manifest, table, C.FAMILY_TRANSIT) if u.unit_id == "RB1-VC30")
    assert len(vc30.groups) == 8 and vc30.scored_as == "MIXED"


@needs_library
def test_a_cluster_table_that_disagrees_with_the_manifest_is_refused():
    manifest = json.loads(MANIFEST.read_text())
    table = json.loads(CLUSTERS.read_text())
    row = next(c for c in table["clusters"] if c["scored_as"] == "R" and c["cluster_id"] in {u["unit_id"] for u in manifest["units"] if u["plane"] == "dasha"})
    row["groups_scored"] = [row["groups_scored"][0][:1]]  # drop a member the manifest calls evaluable
    with pytest.raises(ScorerError):
        units_from_manifest(manifest, table, C.FAMILY_DASHA)
