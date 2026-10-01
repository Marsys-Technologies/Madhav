"""B6.0 PART 2 — GOCHARA_TEST_ORACLES v1.4 against Stream A's merged A5.3
modules (steward M20261001T125220-a4c1): `services/gochara_kernel/
rule_registry.py` (rule_binding) and `services/gochara_kernel/evaluator.py`
(window_evaluator).

GENERAL RULE (the steward's): every 'then' is asserted on the OUTPUT of the
production modules; where the spec-implied seam has no production output,
the test is a FINDING — `@pytest.mark.xfail(strict=True)` that XPASS-fails
the moment Stream A lands the fix.

Covered here (the enumeration/binding legs; the A5.5-trajectory legs —
admission arithmetic, peak, bit-identical scoring — stay with B5.5's map in
ORACLE_EXECUTION_MAP v1.0):

  O-CF-N6   birth_anchor raises on every implemented path; the marriage
            control is non-empty (an empty control fails the control, not
            just the assertion)
  O-RP-5a   the pinned 8th-from-Moon case: Moon 327.06° Aquarius, Saturn
            transit Virgo — the inclusive count Aquarius 1st … Virgo 8th is
            written out; illness_acute (named class, R3) carries the scored
            Saturn-in-Virgo residence edge; the full RQ-5 plan is the exact
            13-edge set; nothing attaches to any gain class
  O-RP-5b   the testimony half: Sade-Sati phase rows are
            uncited_extension/testimony/D-PADMIT on adverse classes only;
            childbirth (gain) carries NO Sade-Sati edge
  O-RP-3    P4 = the P3 scored edges restricted to {jupiter, saturn} —
            ONE rule (R3-S02), and the agents need NOT share one target
            (the set carries both house-span and lord-point targets)
  O-RP-8    the marriage P3 row set is EXACTLY the qualified set — the
            count arithmetic is written out (34 edges), a Cartesian
            all-agents × all-targets enumeration produces extra rows and
            fails the count
  O-RR-3    natal Saturn 202.43° (Libra = 7th from Aries, count written)
            appears as an OCCUPANT row of the 7th-house span in the
            marriage P1 record set; the 7L Venus ownership row with it
  O-RP-7    the P1 factor inventory as BOUND by rule_binding: every factor
            row carries a declared effect, the binary direction vocab, a
            range inside [0,1], and doctrine orderings run WEAKEST →
            STRONGEST; sad_bala_summary is excluded (D2) and would raise
  O-RP-1    FINDING (strict-xfail): union-not-cascade admission — no
            admission-evaluation seam exists in the A5.3 modules yet
  O-P6-TARA FINDING (strict-xfail): P6 day-tier enumeration (D1 — binds
            with day_on_demand); the tārā term's nine-fold class

Plus the rule_binding store discipline on a fake connection (no DB): a
divergent stored row raises RegistryDivergenceError loudly, an identical
row is reused, an absent row is inserted.

Mutation evidence (applied, run RED, reverted — recorded in the B6.0 PART 2
steward report): (1) Saturn's 8th-from-Moon scored edge dropped from the
P2 adverse plan → O-RP-5a's exact-set test fails; (2) the node-aspect skip
removed → O-RP-8's exact count fails; (3) dignity doctrine ordering
reversed → O-RP-7's ordering test fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from services.gochara_kernel import evaluator as ev  # noqa: E402
from services.gochara_kernel import rule_registry as rb  # noqa: E402

# The oracles' constants block (GOCHARA_TEST_ORACLES v1.4), verbatim —
# lagna 12.43 Aries, the nine natal longitudes.
CHART = {
    "lagna_deg": 12.43,
    "natal": {
        "Sun": 291.96, "Moon": 327.06, "Mars": 198.52, "Mercury": 270.84,
        "Jupiter": 249.79, "Venus": 259.19, "Saturn": 202.43,
        "Rahu": 49.03, "Ketu": 229.03,
    },
}

SIGNS_ARIES_FIRST = (
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
)


def _house_from_moon(sign: str) -> int:
    """The inclusive count from the Moon sign, written out per oracle
    convention: Aquarius 1st, Pisces 2nd, Aries 3rd, Taurus 4th, Gemini
    5th, Cancer 6th, Leo 7th, Virgo 8th, Libra 9th, Scorpio 10th,
    Sagittarius 11th, Capricorn 12th."""
    moon_idx = SIGNS_ARIES_FIRST.index("aquarius")  # natal Moon 327.06°
    return (SIGNS_ARIES_FIRST.index(sign) - moon_idx) % 12 + 1


def _targets(edges):
    return {e.obj.canonical_target for e in edges}


# ── O-CF-N6 ──────────────────────────────────────────────────────────────────


def test_o_cf_n6_birth_anchor_zero_rows_every_path_and_control_nonempty():
    """given the natal-epoch class birth_anchor plus a non-empty control;
    when windows/records are enumerated; then ZERO rows for birth_anchor at
    every resolution and the control returns its known rows."""
    for path in ev.IMPLEMENTED_PATHS:
        with pytest.raises(ValueError, match="birth_anchor"):
            ev.enumerate_edges("birth_anchor", path, CHART)
    control = ev.enumerate_edges("marriage", "P3", CHART)
    assert len(control) > 0, "the marriage control is empty — the CONTROL fails"


# ── O-RP-5a ──────────────────────────────────────────────────────────────────


def test_o_rp_5a_saturn_8th_from_moon_scores_for_illness_acute_only():
    """given natal Moon 327.06° Aquarius and Saturn transiting 172.00°
    Virgo (the count: Aquarius 1st … Virgo 8th); when illness_acute is
    evaluated; then the residence contributes evidence FOR the adverse
    class — enumeration leg: a SCORED Saturn-residence span:virgo edge
    exists for illness_acute and the RQ-5 plan is exactly these 13
    edges."""
    edges = ev.enumerate_p2_edges("illness_acute", CHART)
    saturn_virgo = [e for e in edges
                    if e.agent == "saturn" and e.obj.canonical_target == "span:virgo"]
    assert len(saturn_virgo) == 1
    edge = saturn_virgo[0]
    assert edge.operator_role == "scored" and edge.provenance == "verse_cited"
    assert edge.frame_kind == "moon" and edge.relation == "residence"
    # the exact RQ-5 plan, nothing else: (agent, span, testimony?)
    expected = (
        [("sun", h, False) for h in (12, 8, 1)]
        + [("mars", h, False) for h in (12, 8, 1)]
        + [("jupiter", h, False) for h in (12, 8, 1)]
        + [("saturn", 8, False)]
        + [("saturn", h, True) for h in (12, 1, 2)]
    )
    house_of_span = {1: "aquarius", 2: "pisces", 8: "virgo", 12: "capricorn"}
    expected_set = {(agent, f"span:{house_of_span[h]}", testimony)
                    for agent, h, testimony in expected}
    actual_set = {(e.agent, e.obj.canonical_target,
                   e.operator_role == "testimony") for e in edges}
    assert actual_set == expected_set, (
        f"extra {actual_set - expected_set}; missing {expected_set - actual_set}")
    # attaches NOTHING to any gain class: every gain class's P2 set is the
    # cited favourable table (scored only), none of the adverse plan's spans
    from services.gochara_rules.favourable_houses import favourable_houses
    for gain_class in ("marriage", "childbirth", "major_gain"):
        gain_edges = ev.enumerate_p2_edges(gain_class, CHART)
        assert all(e.operator_role == "scored" for e in gain_edges)
        for e in gain_edges:
            # a gain-class edge is justified only by the favourable table:
            # its span must be a FAVOURABLE house of its agent from the Moon
            assert _house_from_moon(e.obj.canonical_target.removeprefix("span:")) \
                in favourable_houses(e.agent.title()), (gain_class, e)


def test_o_rp_5a_mutation_target_gain_class_attachment_fails():
    """The oracle's mutation: attaching the adverse edge to a gain class
    must fail. Asserted as a property here; demonstrated RED in the PART 2
    report by mutating the polarity gate."""
    from services.gochara_rules.registry import CLASS_BY_NAME
    from services.gochara_rules.favourable_houses import favourable_houses
    for cls, row in CLASS_BY_NAME.items():
        if cls == "birth_anchor" or row["polarity"] == "anchor":
            continue
        edges = ev.enumerate_p2_edges(cls, CHART)
        if row["polarity"] == "adverse":
            assert edges, f"adverse class {cls} enumerates the RQ-5 plan"
            assert all(_house_from_moon(e.obj.canonical_target.removeprefix("span:"))
                       in (12, 8, 1, 2) for e in edges)
        elif row["polarity"] == "gain":
            assert all(_house_from_moon(e.obj.canonical_target.removeprefix("span:"))
                       in favourable_houses(e.agent.title()) for e in edges)
        else:
            assert edges == [], f"non-adverse non-gain class {cls} must be empty"


# ── O-RP-5b ──────────────────────────────────────────────────────────────────


def test_o_rp_5b_sade_sati_phase_rows_are_testimony_and_never_on_gain():
    """the childbirth (gain) class carries NO Sade-Sati edge; the phase
    rows exist as operator_role=testimony (uncited_extension, D-PADMIT) on
    adverse-eligible classes. The zero-score-effect leg (bit-identical
    scoring with vs without) stays with the A5.5 window scorer (B5.5
    O-RP-5b REAL)."""
    adverse = ev.enumerate_p2_edges("illness_acute", CHART)
    testimony = [e for e in adverse if e.operator_role == "testimony"]
    assert {(e.agent, e.obj.canonical_target) for e in testimony} == {
        ("saturn", "span:capricorn"),  # 12th from the Aquarius Moon (count written)
        ("saturn", "span:aquarius"),   # 1st — phase 2
        ("saturn", "span:pisces"),     # 2nd — phase 3
    }
    for e in testimony:
        assert e.provenance == "uncited_extension"
        assert e.ruling_ref == "D-PADMIT"
        assert e.frame_kind == "moon"
    for gain_class in ("childbirth", "marriage", "major_gain"):
        edges = ev.enumerate_p2_edges(gain_class, CHART)
        assert all(e.operator_role != "testimony" for e in edges), gain_class
        sade_sati_spans = {"span:capricorn", "span:aquarius", "span:pisces"}
        assert not any(e.agent == "saturn"
                       and e.obj.canonical_target in sade_sati_spans
                       and e.provenance == "uncited_extension" for e in edges), gain_class


# ── O-RP-3 ───────────────────────────────────────────────────────────────────


def test_o_rp_3_p4_is_one_rule_p3_scored_restricted_to_jupiter_saturn():
    """R3-S02: ONE P4 rule — union within an agent, AND across agents.
    Enumeration leg: the P4 edge set IS the P3 scored edges restricted to
    {jupiter, saturn}, and the agents need NOT share one target (house-span
    and lord-point targets both present per agent)."""
    for cls in ("childbirth", "marriage"):
        p3 = ev.enumerate_p3_edges(cls, CHART)
        p4 = ev.enumerate_p4_edges(cls, CHART)
        expected = [e for e in p3
                    if e.agent in ("jupiter", "saturn") and e.operator_role == "scored"]
        assert {(e.agent, e.relation, e.obj.canonical_target, e.object_role)
                for e in p4} == {(e.agent, e.relation, e.obj.canonical_target, e.object_role)
                                 for e in expected}
        for agent in ("jupiter", "saturn"):
            mine = [e for e in p4 if e.agent == agent]
            spans = {e.obj.canonical_target for e in mine}
            assert any(t.startswith("span:") for t in spans), (cls, agent)
            assert any(t.startswith("point:") for t in spans), (cls, agent)


# ── O-RP-8 ───────────────────────────────────────────────────────────────────


def test_o_rp_8_marriage_p3_exact_qualified_row_set():
    """Only the qualified set is enumerated — exact row set. Marriage (the
    P3 truth table: H = {7}, L(H) = {Venus}; māraka lords of {2, 7}):
    lagna Aries 12.43°, so the 7th is Libra and Venus is at 259.19°.

    The count, written out:
      house edges: 9 agents × 1 house × {residence, aspect} − the 2 node
        aspects (N-14: Rāhu/Ketu cast no dṛṣṭi) = 18 − 2 = 16
      lord edges: 9 agents × 1 lord × {conjunction, aspect} − 2 node
        aspects = 16
      māraka testimony rows: houses 2 and 7 from the lagna = Taurus and
        Libra, both Venus-owned → 2 natal-fact rows
    TOTAL = 34. A Cartesian all-agents × all-targets enumeration produces
    extra rows and fails this count.
    """
    edges = ev.enumerate_p3_edges("marriage", CHART)
    assert len(edges) == 34, f"got {len(edges)}"
    key = lambda e: (e.agent, e.relation, e.obj.canonical_target,  # noqa: E731
                     e.object_role, e.operator_role)
    actual = {key(e) for e in edges}
    agents7 = ("sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn")
    expected = set()
    for a in agents7 + ("rahu", "ketu"):
        expected.add((a, "residence", "span:libra", "signature_house", "scored"))
        expected.add((a, "conjunction", "point:259.19", "lord", "scored"))
    for a in agents7:
        expected.add((a, "aspect", "span:libra", "signature_house", "scored"))
        expected.add((a, "aspect", "point:259.19", "lord", "scored"))
    expected.add(("venus", "ownership", "span:taurus", "maraka_of_house", "testimony"))
    expected.add(("venus", "ownership", "span:libra", "maraka_of_house", "testimony"))
    assert actual == expected, (
        f"extra {sorted(actual - expected)}; missing {sorted(expected - actual)}")
    # every span/point target is a QUALIFIED target only
    assert _targets(edges) <= {"span:libra", "span:taurus", "point:259.19"}


# ── O-RR-3 ───────────────────────────────────────────────────────────────────


def test_o_rr_3_natal_saturn_is_an_occupant_of_the_7th_for_marriage():
    """natal Saturn 202.43° → Libra (Aries 1st … Libra 7th, count written);
    when marriage-class objects are resolved; then natal Saturn appears as
    an OCCUPANT of the 7th-house span in the emitted P1 record set — a run
    resolving only 7L Venus is a recorded miss."""
    edges = ev.enumerate_p1_edges("marriage", CHART)
    saturn_occupancy = [e for e in edges
                        if e.agent == "saturn" and e.relation == "occupancy"]
    assert len(saturn_occupancy) == 1
    edge = saturn_occupancy[0]
    assert edge.obj.canonical_target == "span:libra"
    assert edge.object_role == "signature_house"   # E3 binding of the §1 occupant row
    assert edge.transit is False                   # natal-fact row
    assert edge.provenance == "verse_cited" and edge.operator_role == "scored"
    # the 7L Venus ownership row accompanies it (lord AND occupant, the union)
    assert any(e.agent == "venus" and e.relation == "ownership"
               and e.obj.canonical_target == "span:libra" for e in edges)
    # occupant at a DIFFERENT longitude would fail: no other occupancy row
    # names a non-signature sign for marriage (H = {7} only)
    assert all(e.obj.canonical_target == "span:libra"
               for e in edges if e.relation == "occupancy")


# ── O-RP-7 (rule_binding factor inventory leg) ───────────────────────────────


def test_o_rp_7_bound_factor_inventory_declared_effects_ranges_and_orderings():
    """every factor in the P1 inventory has a declared effect row; factor
    values stay in [0,1]; doctrine-ordered categoricals bind WEAKEST →
    STRONGEST (dignity: debility…exaltation per the virupa anchor); the
    direction field is the binary CHECK vocab (E4)."""
    rows = {r["factor_id"]: r for r in rb.factor_rows()}
    from services.gochara_rules import registry as rules_registry
    p1 = rules_registry.RULE_PATHS[("P1", rb.RULE_VERSION)]
    p1_factors = {fid for fid, _ in p1["soft_factors"]}
    assert p1_factors <= set(rows), f"unbound P1 factors: {p1_factors - set(rows)}"
    for fid in p1_factors:
        row = rows[fid]
        assert row["effect"], f"{fid}: no declared effect"
        assert row["direction"] in ("higher_stronger", "lower_stronger")
        assert 0.0 <= row["range_lower"] <= row["range_upper"] <= 1.0
        if row["doctrine_ordering"] is not None:
            assert len(row["doctrine_ordering"]) >= 2
    assert rows["dignity_of_transit_sign"]["doctrine_ordering"] == [
        "debility", "inimical", "neutral", "friendly", "own", "exaltation"]
    assert rows["agent_nature"]["doctrine_ordering"] == ["malefic", "benefic"]
    assert rows["maitri_compound"]["doctrine_ordering"] == [
        "extreme_enemy", "enemy", "neutral", "friend", "extreme_friend"]
    # D2: sad_bala_summary is deferred (units violate kgf_units_ck) — and
    # binding it would raise, never silently re-unit
    assert "sad_bala_summary" not in rb.BOUND_FACTORS
    original = rb.BOUND_FACTORS
    rb.BOUND_FACTORS = original + ("sad_bala_summary",)
    try:
        with pytest.raises(rb.RegistryDivergenceError, match="units"):
            rb.factor_rows()
    finally:
        rb.BOUND_FACTORS = original


# ── rule_binding: §2.2 frames + the store discipline (fake conn, no DB) ──────


def test_rule_binding_path_frames_match_spec_2_2():
    """E1 per GOCHARA_DESIGN_SPECS_v1_4 §2.2: P1 dasha_lord, P2 moon,
    P3/P4/P5 lagna (P3's bereavement bhavat_bhavam:9 variation is
    class-level, not the path frame)."""
    frames = {r["path_id"]: (r["frame_kind"], r["frame_arg"]) for r in rb.path_rows()}
    assert frames == {
        "P1": ("dasha_lord", None), "P2": ("moon", None),
        "P3": ("lagna", None), "P4": ("lagna", None), "P5": ("lagna", None),
    }
    # every selector role is the path's declared role inventory (E3) and no more
    for r in rb.path_rows():
        roles = {s["object_role"] for s in r["object_selector"]}
        assert roles == set(rb._PATH_ROLES[r["path_id"]])
        agents = {s["agent"] for s in r["object_selector"]}
        assert agents == set(rb._PATH_AGENTS[r["path_id"]])


class _FakeResult:
    def __init__(self, row):
        self._row = row

    def fetchone(self):
        return self._row


class _FakeConn:
    def __init__(self, stored_row=None):
        self.stored_row = stored_row
        self.inserts = []

    def execute(self, sql, params=()):
        if sql.strip().startswith("INSERT"):
            self.inserts.append((sql, params))
        return _FakeResult(self.stored_row)


def test_rule_binding_store_divergence_raises_reuse_and_insert():
    """Insert-if-absent with full-field equality: a divergent stored row is
    a loud RegistryDivergenceError (fix the data, not the detector); an
    identical row is 'reused'; an absent row is inserted."""
    store = rb.RuleRegistryStore(_FakeConn())
    row = {"path_id": "PX", "rule_version": "1.0.0", "frame_kind": "lagna",
           "frame_arg": None}
    # absent → inserted
    assert store._bind("ka_gochara_rule_path", ("path_id", "rule_version"), row) == "inserted"
    # identical → reused (normalised comparison, JSONB vs text tolerant)
    stored = ("PX", "1.0.0", "lagna", None)
    store2 = rb.RuleRegistryStore(_FakeConn(stored))
    assert store2._bind("ka_gochara_rule_path", ("path_id", "rule_version"), row) == "reused"
    # divergent → loud
    tampered = ("PX", "1.0.0", "moon", None)
    store3 = rb.RuleRegistryStore(_FakeConn(tampered))
    with pytest.raises(rb.RegistryDivergenceError, match="diverges"):
        store3._bind("ka_gochara_rule_path", ("path_id", "rule_version"), row)


def test_rule_binding_membership_guard_rejects_dangling_references():
    """§2.1: a bare or dangling composite reference is rejected before any
    SQL — here, P6's catalogue row references predicates/factors the
    binding does not declare, and BOUND_PATHS excludes it (D1)."""
    assert "P6" not in rb.BOUND_PATHS
    rb._membership_consistent()  # the declared set is internally complete
    declared = set(rb.PREDICATES)
    from services.gochara_rules import registry as rules_registry
    for pid in rb.BOUND_PATHS:
        src = rules_registry.RULE_PATHS[(pid, rb.RULE_VERSION)]
        for pred_id, _ in src["prerequisites"]:
            assert pred_id in declared


# ── FINDINGs (strict-xfail; XPASS-fails the moment the seam lands) ───────────


@pytest.mark.xfail(strict=True, reason=(
    "FINDING B6-F16: O-RP-1 on the A5.3 seam — no admission-evaluation "
    "function exists in the A5.3 modules (enumeration + persistence only); "
    "union-not-cascade admission with evidence_against attribution lands "
    "with the admission step"))
def test_o_rp_1_union_not_cascade_on_a53_seam():
    """given a window admitted by P3 with P2's Moon-frame phala adverse at
    the same instant; then the window REMAINS admitted (union), the P2
    record attaches as evidence_against_occurrence on the native's
    own-fortune class only, no cascade exclusion. The spec-implied seam is
    an admission evaluator over the enumerated grains."""
    assert hasattr(ev, "evaluate_admission"), (
        "no admission-evaluation seam in window_evaluator (FINDING B6-F16)")


@pytest.mark.xfail(strict=True, reason=(
    "FINDING B6-F17: O-P6-TARA on the A5.3 seam — P6 is deferred (D1: "
    "binds with the day_on_demand step; the 'inherited' frame-kind needs "
    "the v1.5 contract fold); enumerate_edges refuses P6 today"))
def test_o_p6_tara_day_tier_enumeration_on_a53_seam():
    """given the pinned janma-nakṣatra 24 and day nakṣatra 20 (zero-based
    inclusive cyclic distance 24 → nine-fold class 6); when the P6 day
    evaluation runs; then the tārā term is present with the correct
    normalised key and class, annotating (testimony), never weighting."""
    edges = ev.enumerate_edges("marriage", "P6", CHART)
    assert edges, "P6 day-tier enumeration absent (FINDING B6-F17)"
