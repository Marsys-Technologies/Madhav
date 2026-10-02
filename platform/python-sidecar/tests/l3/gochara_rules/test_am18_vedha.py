"""AM-18 (ruled): vedha derived from stored residence spans; cited nullification step; O-VI-6.

O-VI-6 (Stream B, steward M20261002T004621-2b84) — literal residence spans, half-open, instant precision:
the pairs come from bg_transit_rules ROWS handed to the accessor (fixtures below are literal L0 rows as read
read-only from production 2026-10-02: graha, primary_house, vedha_house, citation); nothing is copied into the
module under test. Signs 1=Aries … 12=Pisces; natal Moon in Aquarius (11) → house = (sign-11) % 12 + 1.
"""
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

CITE_PG322 = "Phaladipika Adh. XXVI, Sloka 3 — phaladeepika:PG322:C1 (Sastri trans. 1950)"
CITE_PG323 = "Phaladipika Adh. XXVI, Sloka 6 — phaladeepika:PG323:C1 (Sastri trans. 1950)"
UNSRC = "UNSOURCED — no house-transit vedha doctrine for Rahu/Ketu found anywhere in the served corpus"
ROWS = [
    ("sun", 3, 9, CITE_PG322, "favourable"), ("sun", 6, 12, CITE_PG322, "favourable"),
    ("sun", 10, 4, CITE_PG322, "favourable"), ("sun", 11, 5, CITE_PG322, "favourable"),
    ("saturn", 3, 12, CITE_PG322, "favourable"), ("saturn", 6, 9, CITE_PG322, "favourable"),
    ("saturn", 11, 5, CITE_PG322, "favourable"),
    ("mercury", 2, 5, CITE_PG323, "favourable"), ("mercury", 4, 3, CITE_PG323, "favourable"),
    ("venus", 12, 6, CITE_PG323, "favourable"), ("venus", 11, 3, CITE_PG323, "favourable"),
    ("rahu", 3, 9, UNSRC, "favourable"), ("ketu", 6, 12, UNSRC, "favourable"),
]
MOON = 11
PAIRS = pairs_from_rows(ROWS)


def span(sign, a, b):
    return (sign, f"2025-{a}T00:00Z", f"2025-{b}T00:00Z")


def base_residence():
    """Everyone parked in signs that never touch the cases below, then overridden per test."""
    far = lambda s: [span(s, "01-01", "12-31")]
    return {"Sun": far(2), "Mars": far(2), "Mercury": far(2), "Jupiter": far(2), "Venus": far(2),
            "Saturn": far(2), "Rahu": far(2), "Ketu": far(2)}


# ── pairs accessor ─────────────────────────────────────────────────────────────────
def test_pairs_are_read_from_rows_nodes_refused_uncited_refused():
    assert PAIRS[("Sun", 3)] == 9 and PAIRS[("Venus", 12)] == 6 and PAIRS[("Mercury", 2)] == 5
    assert not any(k[0] in ("Rahu", "Ketu") for k in PAIRS)                 # the UNSOURCED node rows are not usable
    with pytest.raises(VedhaPairsError):
        pairs_from_rows([("jupiter", 2, 12, "", "favourable")])             # uncited classical row: refused, not skipped
    with pytest.raises(VedhaPairsError):
        pairs_from_rows([("jupiter", 2, 12, CITE_PG323, "favourable"), ("jupiter", 2, 11, CITE_PG323, "favourable")])
    with pytest.raises(VedhaPairsError):
        pairs_from_rows([("jupiter", 2, 12, CITE_PG323, "unfavourable")])


def test_house_from_moon_is_inclusive():
    assert house_from_moon(11, MOON) == 1 and house_from_moon(1, MOON) == 3 and house_from_moon(7, MOON) == 9


# ── O-VI-6 ─────────────────────────────────────────────────────────────────────────
def test_o_vi_6_abutting_obstructors_exception_and_node_in_one_primary_span():
    # Sun in Aries (3rd from Moon) 04-14 → 05-15; vedha house = 9th = Libra (7).
    res = base_residence()
    res["Mars"] = [span(7, "04-01", "04-25")]               # obstructs 04-14 → 04-25
    res["Jupiter"] = [span(7, "04-25", "05-05")]            # ABUTS Mars exactly at 04-25
    res["Saturn"] = [span(7, "04-01", "06-01")]             # Sun↔Saturn exception: never obstructs the Sun
    res["Rahu"] = [span(7, "05-05", "05-10")]               # a node alone in the vedha house
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
    res2 = base_residence(); res2["Saturn"] = [span(7, "04-01", "06-01")]
    only_exc = derive_vedha("Sun", 3, ("2025-04-14T00:00Z", "2025-05-15T00:00Z"), moon_sign=MOON, residence=res2, pairs=PAIRS)
    assert [s["state"] for s in only_exc["segments"]] == ["inactive"]
    # …but Mars (non-exception control) in the same house obstructs
    res3 = base_residence(); res3["Mars"] = [span(7, "04-01", "06-01")]
    ctrl = derive_vedha("Sun", 3, ("2025-04-14T00:00Z", "2025-05-15T00:00Z"), moon_sign=MOON, residence=res3, pairs=PAIRS)
    assert [s["state"] for s in ctrl["segments"]] == ["active"]


def test_o_vi_6_mercury_has_no_moon_scope_other_primaries_do():
    # Mercury in Pisces (2nd from Moon) 03-01 → 03-20; vedha house 5th = Gemini (3); Venus there from 03-10.
    res = base_residence(); res["Venus"] = [span(3, "03-10", "03-30")]
    m = derive_vedha("Mercury", 2, ("2025-03-01T00:00Z", "2025-03-20T00:00Z"), moon_sign=MOON, residence=res, pairs=PAIRS)
    assert [(s["t_in"][5:10], s["state"], s["scope"]) for s in m["segments"]] == [("03-01", "inactive", None), ("03-10", "active", None)]
    # a non-Mercury primary: the same clean stretch carries the Moon scope
    res2 = base_residence()
    s = derive_vedha("Sun", 3, ("2025-04-14T00:00Z", "2025-05-15T00:00Z"), moon_sign=MOON, residence=res2, pairs=PAIRS)
    assert s["segments"][0]["scope"] == MOON_SCOPE


def test_o_vi_6_cited_obstructor_beats_a_simultaneous_node():
    res = base_residence()
    res["Mars"] = [span(7, "04-20", "05-01")]; res["Rahu"] = [span(7, "04-15", "05-10")]
    out = derive_vedha("Sun", 3, ("2025-04-14T00:00Z", "2025-05-15T00:00Z"), moon_sign=MOON, residence=res, pairs=PAIRS)
    rows = [(s["t_in"][5:10], s["t_out"][5:10], s["state"]) for s in out["segments"]]
    assert rows == [("04-14", "04-15", "inactive"), ("04-15", "04-20", "unqualified"), ("04-20", "05-01", "active"),
                    ("05-01", "05-10", "unqualified"), ("05-10", "05-15", "inactive")]
    # a node boundary INSIDE a cited obstruction must not split it: Rahu enters 04-25 while Mars is still there
    res = base_residence()
    res["Mars"] = [span(7, "04-20", "05-01")]; res["Rahu"] = [span(7, "04-25", "05-10")]
    inner = derive_vedha("Sun", 3, ("2025-04-14T00:00Z", "2025-05-15T00:00Z"), moon_sign=MOON, residence=res, pairs=PAIRS)
    assert [(s["t_in"][5:10], s["t_out"][5:10], s["state"]) for s in inner["segments"]] == [
        ("04-14", "04-20", "inactive"), ("04-20", "05-01", "active"), ("05-01", "05-10", "unqualified"),
        ("05-10", "05-15", "inactive")]


def test_o_vi_6_half_open_edges_and_not_applicable_and_missing_inputs():
    res = base_residence(); res["Mars"] = [span(7, "05-15", "06-15")]       # starts exactly where the Sun's span ends
    out = derive_vedha("Sun", 3, ("2025-04-14T00:00Z", "2025-05-15T00:00Z"), moon_sign=MOON, residence=res, pairs=PAIRS)
    assert [s["state"] for s in out["segments"]] == ["inactive"]
    # adverse residence (Saturn 8th from Moon): no cited pair ⇒ NOT APPLICABLE (declared), no segments, no value
    na = derive_vedha("Saturn", 8, ("2025-04-14T00:00Z", "2025-05-15T00:00Z"), moon_sign=MOON, residence=base_residence(), pairs=PAIRS)
    assert na == {"applicable": False, "reason": "no_cited_vedha_pair_for_this_house", "segments": []}
    # a missing stored obstructor is an error, never silently "clean"
    bad = base_residence(); del bad["Venus"]
    with pytest.raises(VedhaPairsError):
        derive_vedha("Sun", 3, ("2025-04-14T00:00Z", "2025-05-15T00:00Z"), moon_sign=MOON, residence=bad, pairs=PAIRS)


def test_value_mapping_is_the_cited_step_and_never_graded():
    res = base_residence(); res["Mars"] = [span(7, "04-20", "05-01")]; res["Ketu"] = [span(7, "05-01", "05-05")]
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
    seg = {"state": "active", "value": 0.0, "reason": None, "scope": None}
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
    res = base_residence(); res["Rahu"] = [span(7, "04-20", "05-01")]
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
