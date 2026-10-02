"""AM-18 (ruled): vedha derived from stored residence spans; cited nullification step; O-VI-6.

O-VI-6 (Stream B, steward M20261002T004621-2b84) — literal residence spans, half-open, instant precision:
the pairs come from bg_transit_rules ROWS handed to the accessor (fixtures below are literal L0 rows as read
read-only from production 2026-10-02: graha, primary_house, vedha_house, citation); nothing is copied into the
module under test. Signs 1=Aries … 12=Pisces; natal Moon in Aquarius (11) → house = (sign-11) % 12 + 1.
"""
import json
import pathlib

import pytest

from services.gochara_rules import registry
from services.gochara_rules.registry import (
    FACTORS, KERNEL_VERSION, RULE_PATHS, RULE_VERSION, SUPERSEDED_FACTORS, SUPERSEDED_PATHS, composite_ref,
)
from services.gochara_rules.vedha_derive import (
    MOON_SCOPE, VedhaPairsError, derive_vedha, house_from_moon, pairs_from_rows, vedha_factor_value, vedha_not_applicable,
)
from services.gochara_rules import flat_selector as FS
VREF = composite_ref("vedha_attenuation", KERNEL_VERSION)

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "l0_vedha_rows_2026_10_02.json"
ROWS = [tuple(r) for r in json.loads(FIXTURE.read_text())]        # the 42 LITERAL bg_transit_rules vedha rows, read-only from production 2026-10-02
CITE_PG322 = "Phaladipika Adh. XXVI, Sloka 3 — phaladeepika:PG322:C1 (Sastri trans. 1950)"
CITE_PG323 = "Phaladipika Adh. XXVI, Sloka 6 — phaladeepika:PG323:C1 (Sastri trans. 1950)"
MOON = 11
PAIRS = pairs_from_rows(ROWS)


def span(sign, a, b):
    return (sign, f"2025-{a}T00:00Z", f"2025-{b}T00:00Z")


def cov(*spans, far_sign=2):
    """The given interesting spans PLUS far_sign filling the rest of 2025 — a graha is always somewhere, so residence COVERS the year
    (Codex round 7 [6a]: absence of coverage is missing data, no longer 'clean')."""
    out, cur = [], "2025-01-01T00:00Z"
    for sg in sorted(spans, key=lambda x: x[1]):
        if cur < sg[1]:
            out.append((far_sign, cur, sg[1]))
        out.append(sg)
        cur = sg[2]
    if cur < "2025-12-31T00:00Z":
        out.append((far_sign, cur, "2025-12-31T00:00Z"))
    return out


def base_residence():
    """Everyone parked in signs that never touch the cases below, then overridden per test."""
    far = lambda s: [span(s, "01-01", "12-31")]
    return {"Sun": far(2), "Mars": far(2), "Mercury": far(2), "Jupiter": far(2), "Venus": far(2),
            "Saturn": far(2), "Rahu": far(2), "Ketu": far(2)}


# ── pairs accessor ─────────────────────────────────────────────────────────────────
def test_pairs_are_read_from_rows_nodes_refused_uncited_refused():
    assert PAIRS[("Sun", 3)] == 9 and PAIRS[("Venus", 12)] == 6 and PAIRS[("Mercury", 2)] == 5
    assert not any(k[0] in ("Rahu", "Ketu") for k in PAIRS)                 # the UNSOURCED node rows are not usable
    assert len(PAIRS) == 36 and PAIRS.census["total"] == 42 and PAIRS.census["classical"]["Venus"] == 9
    assert len(PAIRS.content_digest) == 64
    # uncited / duplicate / unfavourable are still refused, now inside a COMPLETE load (so only the defect can be the cause)
    for bad in (lambda r: r[:0] + [("jupiter", 2, 12, "", "favourable") if x[:2] == ("jupiter", 2) else x for x in r],
                lambda r: r + [("jupiter", 2, 11, CITE_PG323, "favourable")],
                lambda r: [("jupiter", 2, 12, CITE_PG323, "unfavourable") if x[:2] == ("jupiter", 2) else x for x in r]):
        with pytest.raises(VedhaPairsError):
            pairs_from_rows(bad(list(ROWS)))


# ── Codex round 7 [6b] — the load is validated COMPLETE, cited from the supported chunks, and content-bound ───────────
def _mutated(f):
    rows = [list(r) for r in ROWS]
    f(rows)
    return [tuple(r) for r in rows]


def test_a_fabricated_row_is_refused_not_accepted():
    # the exact reproduction: ('sun',1,2,'unrelated citation','favourable') used to load
    with pytest.raises(VedhaPairsError, match="citation|duplicate|incomplete"):
        pairs_from_rows(list(ROWS) + [("sun", 1, 2, "unrelated citation", "favourable")])
    with pytest.raises(VedhaPairsError, match="citation"):
        pairs_from_rows(_mutated(lambda r: r.__setitem__(0, [r[0][0], r[0][1], r[0][2], "Brihat Jataka ch. II", r[0][4]])))
    with pytest.raises(VedhaPairsError, match="citation"):                   # a sloka outside XXVI.3–8
        pairs_from_rows(_mutated(lambda r: r.__setitem__(0, [r[0][0], r[0][1], r[0][2], "Phaladipika Adh. XXVI, Sloka 9 — phaladeepika:PG323:C1", r[0][4]])))


def test_a_missing_pair_is_an_incomplete_authority_not_a_declared_non_applicability():
    for i in (0, 10, 20, 35):
        with pytest.raises(VedhaPairsError, match="incomplete or changed"):
            pairs_from_rows(_mutated(lambda r: r.pop(i)))
    # the old behaviour would have loaded 35 pairs and quietly made that (graha, house) "not applicable"
    with pytest.raises(VedhaPairsError, match="incomplete or changed"):
        pairs_from_rows([r for r in ROWS if not (r[0] == "venus" and r[1] == 12)])


def test_unique_keys_rule_type_and_house_domains():
    first = ROWS[0]
    with pytest.raises(VedhaPairsError, match="duplicate"):
        pairs_from_rows(list(ROWS) + [first])                                   # an identical duplicate row is also refused
    with pytest.raises(VedhaPairsError, match="rule_type"):
        pairs_from_rows(_mutated(lambda r: r.__setitem__(0, [*r[0][:4], None])))   # None is no longer tolerated
    for ph, vh in ((0, 5), (13, 5), (3, 0), (3, 13), (3, 3), (True, 5)):
        with pytest.raises(VedhaPairsError, match="house domain"):
            pairs_from_rows(_mutated(lambda r: r.__setitem__(0, [r[0][0], ph, vh, r[0][3], r[0][4]])))


def test_node_rows_must_stay_l0_flagged_unsourced_and_unknown_grahas_are_refused():
    node = next(i for i, r in enumerate(ROWS) if r[0] == "rahu")
    with pytest.raises(VedhaPairsError, match="ND-NODE-VEDHA"):
        pairs_from_rows(_mutated(lambda r: r.__setitem__(node, [*r[node][:3], CITE_PG322, r[node][4]])))
    with pytest.raises(VedhaPairsError, match="unknown graha"):
        pairs_from_rows(list(ROWS) + [("lagna", 1, 2, CITE_PG322, "favourable")])


def test_content_identity_binds_the_consumed_rows():
    base = PAIRS.content_digest
    assert pairs_from_rows(list(reversed(ROWS))).content_digest == base      # order-independent
    changed = _mutated(lambda r: r.__setitem__(0, [r[0][0], r[0][1], r[0][2], r[0][3].replace("(Sastri trans. 1950)", "(other)"), r[0][4]]))
    assert pairs_from_rows(changed).content_digest != base                   # a changed citation moves the identity
    node = next(i for i, r in enumerate(ROWS) if r[0] == "rahu")
    moved = _mutated(lambda r: r.__setitem__(node, [r[node][0], r[node][1], 8, *r[node][3:]]))
    assert pairs_from_rows(moved).content_digest != base                     # so does a node row (all 42 rows are consumed)


def test_derive_refuses_a_plain_mapping_so_absence_cannot_mean_missing_data():
    with pytest.raises(VedhaPairsError, match="validated"):
        derive_vedha("Sun", 3, ("2025-04-14T00:00Z", "2025-05-15T00:00Z"), moon_sign=MOON, residence=base_residence(), pairs=dict(PAIRS))


def test_house_from_moon_is_inclusive():
    assert house_from_moon(11, MOON) == 1 and house_from_moon(1, MOON) == 3 and house_from_moon(7, MOON) == 9


# ── O-VI-6 ─────────────────────────────────────────────────────────────────────────
def test_o_vi_6_abutting_obstructors_exception_and_node_in_one_primary_span():
    # Sun in Aries (3rd from Moon) 04-14 → 05-15; vedha house = 9th = Libra (7).
    res = base_residence()
    res["Mars"] = cov(span(7, "04-01", "04-25"))               # obstructs 04-14 → 04-25
    res["Jupiter"] = cov(span(7, "04-25", "05-05"))            # ABUTS Mars exactly at 04-25
    res["Saturn"] = cov(span(7, "04-01", "06-01"))             # Sun↔Saturn exception: never obstructs the Sun
    res["Rahu"] = cov(span(7, "05-05", "05-10"))               # a node alone in the vedha house
    out = derive_vedha("Sun", 3, ("2025-04-14T00:00Z", "2025-05-15T00:00Z"), moon_sign=MOON, residence=res, pairs=PAIRS)
    assert out["applicable"] and out["vedha_house"] == 9
    got = [(s["t_in"][5:10], s["t_out"][5:10], s["state"], s["value"], s["reason"], s["scope"], s["obstructors"])
           for s in out["segments"]]
    assert got == [
        ("04-14", "04-25", "active", 0.0, None, None, ["Mars"]),
        ("04-25", "05-05", "active", 0.0, None, None, ["Jupiter"]),            # abutting: no clean gap at 04-25
        ("05-05", "05-10", "unqualified", None, "node_obstruction_undecided", None, []),
        ("05-10", "05-15", "inactive", 1.0, None, MOON_SCOPE, []),
    ]
    # the segments partition the primary span exactly (half-open, no gap, no overlap)
    assert out["segments"][0]["t_in"] == "2025-04-14T00:00Z" and out["segments"][-1]["t_out"] == "2025-05-15T00:00Z"
    for a, b in zip(out["segments"], out["segments"][1:]):
        assert a["t_out"] == b["t_in"]
    # Saturn alone (the exception) leaves the Sun's span clean
    res2 = base_residence(); res2["Saturn"] = cov(span(7, "04-01", "06-01"))
    only_exc = derive_vedha("Sun", 3, ("2025-04-14T00:00Z", "2025-05-15T00:00Z"), moon_sign=MOON, residence=res2, pairs=PAIRS)
    assert [s["state"] for s in only_exc["segments"]] == ["inactive"]
    # …but Mars (non-exception control) in the same house obstructs
    res3 = base_residence(); res3["Mars"] = cov(span(7, "04-01", "06-01"))
    ctrl = derive_vedha("Sun", 3, ("2025-04-14T00:00Z", "2025-05-15T00:00Z"), moon_sign=MOON, residence=res3, pairs=PAIRS)
    assert [s["state"] for s in ctrl["segments"]] == ["active"]


def test_o_vi_6_mercury_has_no_moon_scope_other_primaries_do():
    # Mercury in Pisces (2nd from Moon) 03-01 → 03-20; vedha house 5th = Gemini (3); Venus there from 03-10.
    res = base_residence(); res["Venus"] = cov(span(3, "03-10", "03-30"))
    m = derive_vedha("Mercury", 2, ("2025-03-01T00:00Z", "2025-03-20T00:00Z"), moon_sign=MOON, residence=res, pairs=PAIRS)
    assert [(s["t_in"][5:10], s["state"], s["scope"]) for s in m["segments"]] == [("03-01", "inactive", None), ("03-10", "active", None)]
    # a non-Mercury primary: the same clean stretch carries the Moon scope
    res2 = base_residence()
    s = derive_vedha("Sun", 3, ("2025-04-14T00:00Z", "2025-05-15T00:00Z"), moon_sign=MOON, residence=res2, pairs=PAIRS)
    assert s["segments"][0]["scope"] == MOON_SCOPE


def test_o_vi_6_cited_obstructor_beats_a_simultaneous_node():
    res = base_residence()
    res["Mars"] = cov(span(7, "04-20", "05-01")); res["Rahu"] = cov(span(7, "04-15", "05-10"))
    out = derive_vedha("Sun", 3, ("2025-04-14T00:00Z", "2025-05-15T00:00Z"), moon_sign=MOON, residence=res, pairs=PAIRS)
    rows = [(s["t_in"][5:10], s["t_out"][5:10], s["state"]) for s in out["segments"]]
    assert rows == [("04-14", "04-15", "inactive"), ("04-15", "04-20", "unqualified"), ("04-20", "05-01", "active"),
                    ("05-01", "05-10", "unqualified"), ("05-10", "05-15", "inactive")]
    # a node boundary INSIDE a cited obstruction must not split it: Rahu enters 04-25 while Mars is still there
    res = base_residence()
    res["Mars"] = cov(span(7, "04-20", "05-01")); res["Rahu"] = cov(span(7, "04-25", "05-10"))
    inner = derive_vedha("Sun", 3, ("2025-04-14T00:00Z", "2025-05-15T00:00Z"), moon_sign=MOON, residence=res, pairs=PAIRS)
    assert [(s["t_in"][5:10], s["t_out"][5:10], s["state"]) for s in inner["segments"]] == [
        ("04-14", "04-20", "inactive"), ("04-20", "05-01", "active"), ("05-01", "05-10", "unqualified"),
        ("05-10", "05-15", "inactive")]


def test_o_vi_6_half_open_edges_and_not_applicable_and_missing_inputs():
    res = base_residence(); res["Mars"] = cov(span(7, "05-15", "06-15"))       # starts exactly where the Sun's span ends
    out = derive_vedha("Sun", 3, ("2025-04-14T00:00Z", "2025-05-15T00:00Z"), moon_sign=MOON, residence=res, pairs=PAIRS)
    assert [s["state"] for s in out["segments"]] == ["inactive"]
    # adverse residence (Saturn 8th from Moon): no cited pair ⇒ NOT APPLICABLE (declared), no segments, no value
    na = derive_vedha("Saturn", 8, ("2025-04-14T00:00Z", "2025-05-15T00:00Z"), moon_sign=MOON, residence=base_residence(), pairs=PAIRS)
    assert na == {"applicable": False, "state": "not_applicable", "reason": "no_cited_vedha_pair_for_this_house", "segments": []}


def test_value_mapping_is_the_cited_step_and_never_graded():
    res = base_residence(); res["Mars"] = cov(span(7, "04-20", "05-01")); res["Ketu"] = cov(span(7, "05-01", "05-05"))
    out = derive_vedha("Sun", 3, ("2025-04-14T00:00Z", "2025-05-15T00:00Z"), moon_sign=MOON, residence=res, pairs=PAIRS)
    vals = {s["state"]: vedha_factor_value(s, factor_ref=VREF) for s in out["segments"]}
    assert vals["active"]["value"] == 0.0 and vals["active"]["qualification"] == "vedha_active"
    assert vals["inactive"]["value"] == 1.0 and vals["inactive"]["scope"] == MOON_SCOPE
    assert vals["unqualified"]["value"] is None and vals["unqualified"]["reason"] == "node_obstruction_undecided"
    assert {v["value"] for v in vals.values()} <= {0.0, 1.0, None}


# ── registry: vedha_attenuation@1.1.0 + P2@1.1.0 ───────────────────────────────────
def test_registry_declares_the_ruled_mapping_as_a_flat_selector_and_versions_p2():
    row = FACTORS[VREF]
    flat, ap = row["operand_selector"], row["applicability"]
    assert FS.flat_problems(flat) == [] and FS.decode_vedha(flat) == ap and FS.encode_vedha(ap) == flat      # SQL-admissible + read-back equality
    assert ap["mapping"] == {"active": 0.0, "inactive": 1.0}
    assert ap["scope_on_inactive"] == MOON_SCOPE and ap["scope_not_needed_for"] == ["Mercury"]
    assert "node_obstruction_undecided" in ap["unqualified_reasons"] and flat["vipareeta_state"] == "not_produced_no_served_citation"
    assert row["function"] == "step" and row["range"] == [0.0, 1.0] and row["null_state"] == "unqualified"
    old = FACTORS[composite_ref("vedha_attenuation", RULE_VERSION)]                 # 1.0.0 untouched
    assert "applicability" not in old
    assert SUPERSEDED_FACTORS[composite_ref("vedha_attenuation", RULE_VERSION)]["superseded_by"] == VREF
    p_old, p_new = RULE_PATHS[composite_ref("P2", RULE_VERSION)], RULE_PATHS[composite_ref("P2", KERNEL_VERSION)]
    assert p_new["soft_factors"] == [VREF] and p_new["prerequisites"] == p_old["prerequisites"]
    assert {k: v for k, v in p_new.items() if k not in ("rule_version", "soft_factors")} == \
           {k: v for k, v in p_old.items() if k not in ("rule_version", "soft_factors")}
    assert SUPERSEDED_PATHS[composite_ref("P2", RULE_VERSION)]["superseded_by"] == composite_ref("P2", KERNEL_VERSION)
    for key, path in RULE_PATHS.items():
        for ref in path.get("soft_factors", []):
            assert ref in FACTORS, (key, ref)


def test_version_exact_dispatch_and_declared_non_applicability():
    seg = {"state": "active", "value": 0.0, "reason": None, "scope": None, "obstructors": ["Mars"]}
    assert vedha_factor_value(seg, factor_ref=VREF)["factor"] == VREF
    with pytest.raises(ValueError):
        vedha_factor_value(seg, factor_ref=composite_ref("vedha_attenuation", RULE_VERSION))      # 1.0.0 declares nothing: refused
    with pytest.raises(ValueError):
        vedha_factor_value(seg, factor_ref=composite_ref("activity_kernel", KERNEL_VERSION))
    na = vedha_not_applicable(VREF)
    assert na["not_applicable"] is True and na["factor"] == VREF


def test_qualification_propagates_from_the_node_state_into_the_channel():
    """R1 integration: a node-undecided segment is `value: None` and must make the record's channel NULL (never 0);
    an active (0.0) segment is a genuine zero; a declared non-applicability is skipped."""
    score = pytest.importorskip("services.gochara_rules.score")
    from services.gochara_rules.records import RelationshipRecord
    if not hasattr(score, "unqualified_reasons"):          # R1 (PR #2905) not in this tree yet
        pytest.skip("R1 qualification propagation not present in this tree")
    res = base_residence(); res["Rahu"] = cov(span(7, "04-20", "05-01"))
    out = derive_vedha("Sun", 3, ("2025-04-14T00:00Z", "2025-05-15T00:00Z"), moon_sign=MOON, residence=res, pairs=PAIRS)
    node_seg = next(s for s in out["segments"] if s["state"] == "unqualified")
    rec = RelationshipRecord(chart_id="482012f1-710e-4a25-994a-93821f5871aa", generation="5.0", event_class="marriage", affected_person="native",
                             frame="moon", agent="Sun", relation="residence", object_id="obj:sign:Aries", object_kind="sign_span", object_role="occupant",
                             contact_id="sha256:c-sun", path_id="P2", rule_version="1.1.0", prerequisites=[], provenance="verse_cited", operator_role="scored")
    ev = score.record_channel_value(rec, "marriage", "favourable", [vedha_factor_value(node_seg, factor_ref=VREF)])
    assert ev.get("unqualified") is True
    totals = score.path_channel_scores([rec], "marriage", {rec.record_id: ev})
    assert totals["evidence_for_occurrence"] is None
    active = next(s for s in derive_vedha("Sun", 3, ("2025-04-14T00:00Z", "2025-05-15T00:00Z"), moon_sign=MOON,
                                          residence={**base_residence(), "Mars": [span(7, "04-20", "05-01")]}, pairs=PAIRS)["segments"] if s["state"] == "active")
    ev0 = score.record_channel_value(rec, "marriage", "favourable", [vedha_factor_value(active, factor_ref=VREF)])
    assert score.path_channel_scores([rec], "marriage", {rec.record_id: ev0})["evidence_for_occurrence"] == 0.0     # a known zero, not NULL
    assert score.factor_product([vedha_not_applicable(VREF), {"value": 0.5, "null_state": "unqualified"}]) == 0.5


# ── Codex round 7 [6a] — COVERAGE: missing residence is not inactivity ─────────────────────────────────
import random
from services.gochara_rules import vedha_derive as VD
from services.gochara_rules.vedha_oracle import agrees, oracle_segments, normalise
from services.gochara_rules.vedha_derive import vedha_factor_results

SUN_SPAN = ("2025-04-14T00:00Z", "2025-05-15T00:00Z")


def run(res, primary="Sun", house=3, span_=SUN_SPAN):
    return derive_vedha(primary, house, span_, moon_sign=MOON, residence=res, pairs=PAIRS)


def states(out):
    return [(s["t_in"][5:10], s["t_out"][5:10], s["state"], s["reason"]) for s in out["segments"]]


def test_codex_reproduction_empty_residence_is_unknown_not_inactive():
    empty = {g: [] for g in ("Sun", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")}
    out = run(empty)
    assert states(out) == [("04-14", "05-15", "unqualified", "obstructor_residence_unknown")]
    seg = out["segments"][0]
    assert seg["value"] is None and seg["scope"] is None and seg["unknown_obstructors"] == ["Jupiter", "Mars", "Mercury", "Venus"]   # Saturn is a cited exception; Sun is the primary
    assert "node_residence_unknown" in seg["reasons"]
    # Mercury primary: nothing established either (its obstructor set is smaller — the Moon is excepted — but never empty)
    m = run(empty, "Mercury", 2, ("2025-03-01T00:00Z", "2025-03-20T00:00Z"))
    assert [s["state"] for s in m["segments"]] == ["unqualified"] and m["segments"][0]["scope"] is None
    # a MISSING key is the same thing as an empty list — and neither raises or reads as clean
    absent = {k: v for k, v in base_residence().items() if k not in ("Venus", "Rahu")}
    assert [s["state"] for s in run(absent)["segments"]] == ["unqualified"]


def test_partial_gaps_are_unknown_only_where_the_gap_is_and_a_known_obstruction_wins_over_a_gap():
    res = base_residence()
    res["Mars"] = [(2, "2025-01-01T00:00Z", "2025-04-20T00:00Z"), (2, "2025-05-05T00:00Z", "2025-12-31T00:00Z")]    # gap 04-20 → 05-05
    out = run(res)
    assert states(out) == [("04-14", "04-20", "inactive", None), ("04-20", "05-05", "unqualified", "obstructor_residence_unknown"),
                           ("05-05", "05-15", "inactive", None)]
    assert out["segments"][1]["unknown_obstructors"] == ["Mars"]
    # Jupiter is KNOWN to obstruct 04-25 → 05-01 inside Mars's gap: known cited obstruction → 0.0 settles it
    res["Jupiter"] = cov(span(7, "04-25", "05-01"))
    out = run(res)
    assert states(out) == [("04-14", "04-20", "inactive", None), ("04-20", "04-25", "unqualified", "obstructor_residence_unknown"),
                           ("04-25", "05-01", "active", None), ("05-01", "05-05", "unqualified", "obstructor_residence_unknown"),
                           ("05-05", "05-15", "inactive", None)]
    # a gap OUTSIDE the primary span is irrelevant
    far = base_residence(); far["Venus"] = [(2, "2025-06-01T00:00Z", "2025-12-31T00:00Z")]
    assert [s["state"] for s in run(far)["segments"]] == ["unqualified"]            # begins after the span: the whole span is uncovered
    ok = base_residence(); ok["Venus"] = [(2, "2025-04-01T00:00Z", "2025-06-01T00:00Z")]
    assert [s["state"] for s in run(ok)["segments"]] == ["inactive"]                # covers the span exactly enough


def test_exception_obstructors_need_no_coverage_and_node_gaps_are_named():
    res = base_residence(); res["Saturn"] = []                                      # the Sun↔Saturn exception: never an obstructor, so its data is not needed
    assert [s["state"] for s in run(res)["segments"]] == ["inactive"]
    res = base_residence(); res["Ketu"] = [(2, "2025-01-01T00:00Z", "2025-04-30T00:00Z")]
    out = run(res)
    assert states(out) == [("04-14", "04-30", "inactive", None), ("04-30", "05-15", "unqualified", "node_residence_unknown")]


def test_malformed_residence_is_refused():
    for bad in ([(13, "2025-01-01T00:00Z", "2025-02-01T00:00Z")], [(2, "2025-02-01T00:00Z", "2025-01-01T00:00Z")],
                [(2, "2025-01-01T00:00Z", "2025-03-01T00:00Z"), (3, "2025-02-01T00:00Z", "2025-04-01T00:00Z")]):    # overlap: two signs at once
        res = base_residence(); res["Mars"] = bad
        with pytest.raises(VedhaPairsError):
            run(res)


# ── Codex round 7 [6c] — structured results + an INDEPENDENT oracle ───────────────────────────────────
def test_structured_results_carry_state_reason_scope_and_obstructors():
    res = base_residence(); res["Mars"] = cov(span(7, "04-20", "05-01")); res["Rahu"] = cov(span(7, "05-01", "05-05")); res["Venus"] = []
    out = run(res)
    results = vedha_factor_results(out, factor_ref=VREF)
    by = {r["state"]: r for r in results}
    assert by["active"]["value"] == 0.0 and by["active"]["qualification"] == "vedha_active" and by["active"]["obstructors"] == ["Mars"]
    assert by["unqualified"]["value"] is None and by["unqualified"]["reason"] in ("obstructor_residence_unknown", "node_obstruction_undecided")
    assert by["unqualified"]["unknown_obstructors"] == ["Venus"] and all(r["factor"] == VREF for r in results)
    assert all({"t_in", "t_out", "state", "value", "reason", "reasons", "scope", "qualification", "obstructors"} <= set(r) for r in results)
    clean = vedha_factor_results(run(base_residence()), factor_ref=VREF)
    assert [(r["state"], r["value"], r["scope"]) for r in clean] == [("inactive", 1.0, MOON_SCOPE)]
    na = vedha_factor_results(run(base_residence(), "Saturn", 8), factor_ref=VREF)
    assert len(na) == 1 and na[0]["state"] == "not_applicable" and na[0]["not_applicable"] is True and na[0]["value"] is None and na[0]["factor"] == VREF


def _scenarios():
    """Hand-built edge cases + seeded random residences (half-open abutments, gaps, nodes, exception pairs, Mercury)."""
    out = []
    base = base_residence()
    out.append(("Sun", 3, SUN_SPAN, dict(base)))
    r = base_residence(); r["Mars"] = cov(span(7, "04-01", "04-25")); r["Jupiter"] = cov(span(7, "04-25", "05-05")); r["Rahu"] = cov(span(7, "05-05", "05-10")); out.append(("Sun", 3, SUN_SPAN, r))
    r = base_residence(); r["Mars"] = cov(span(7, "05-15", "06-15")); out.append(("Sun", 3, SUN_SPAN, r))                          # touches at the end (half-open: no obstruction)
    r = base_residence(); r["Mars"] = cov(span(7, "04-01", "04-14")); out.append(("Sun", 3, SUN_SPAN, r))                          # touches at the start
    r = base_residence(); r["Venus"] = cov(span(3, "03-10", "03-30")); out.append(("Mercury", 2, ("2025-03-01T00:00Z", "2025-03-20T00:00Z"), r))
    r = {g: [] for g in base}; out.append(("Sun", 3, SUN_SPAN, r))
    rng = random.Random(20261002)
    days = [f"2025-{m:02d}-{d:02d}T00:00Z" for m in (3, 4, 5, 6) for d in (1, 8, 15, 22)]
    for _ in range(120):
        r = {}
        for g in base:
            cuts = sorted(rng.sample(days, rng.randint(0, 4)))
            spans = []
            for a, b in zip(cuts[0::2], cuts[1::2]):
                spans.append((rng.choice((2, 3, 7, 7, 7)), a, b))
            r[g] = spans
        out.append((rng.choice([("Sun", 3), ("Mars", 3), ("Mercury", 2), ("Venus", 11), ("Jupiter", 5), ("Saturn", 6)]) + (SUN_SPAN, r)) if False else
                   (*rng.choice([("Sun", 3), ("Mars", 3), ("Mercury", 2), ("Venus", 11), ("Jupiter", 5), ("Saturn", 6)]), SUN_SPAN, r))
    return out


def test_the_pointwise_oracle_agrees_with_the_interval_algebra_on_every_scenario():
    sc = _scenarios()
    assert len(sc) > 100
    for primary, house, span_, res in sc:
        assert agrees(run(res, primary, house, span_), primary, house, span_, moon_sign=MOON, residence=res, pairs=PAIRS), (primary, house, res)


def _disagrees_somewhere():
    for primary, house, span_, res in _scenarios():
        try:
            d = run(res, primary, house, span_)
        except Exception:
            return True                                                       # a mutant that crashes is also detected
        if not agrees(d, primary, house, span_, moon_sign=MOON, residence=res, pairs=PAIRS):
            return True
    return False


@pytest.mark.parametrize("name,attr,replacement", [
    ("coverage_ignored", "_coverage_gaps", lambda spans, within: []),                                    # the round-7 defect itself
    ("intersection_not_clipped", "_intersect", lambda a, b: b),                                         # an obstructor span is not clipped to the primary span
    ("house_off_by_one", "house_from_moon", lambda sign, moon: (sign - moon) % 12),
    ("no_subtract", "_subtract", lambda spans, minus: list(spans)),
])
def test_the_oracle_catches_mutants_of_the_interval_algebra(monkeypatch, name, attr, replacement):
    assert not _disagrees_somewhere()
    monkeypatch.setattr(VD, attr, replacement)
    assert _disagrees_somewhere(), name
