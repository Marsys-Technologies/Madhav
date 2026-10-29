"""Static planning (what the engine can evaluate, which nodes it would read), UNIT_MANIFEST and bundle."""

from __future__ import annotations

import copy
import hashlib
import json

import pytest

from services.rulebook.compiler import compile_card
from services.rulebook.engine import constants as K
from services.rulebook.engine import plan as P
from services.rulebook.engine import units as U
from services.rulebook.engine.irtree import operand_table
from tests.rulebook import _cards as E1

from . import _cardkit as CK


def _plan(card):
    res = compile_card(card)
    assert res.status == "active", res.reasons
    return P.plan_card(res.ir, operand_table(card))


def test_transit_card_plans_as_house_predicate_and_reads_no_node():
    p = _plan(CK.saturn_transit())
    assert p.preds["t"].kind == P.TRANSIT_HOUSE and p.frame.kind == "moon"
    assert not p.excluded_node and not p.lord_generic and p.transit_bodies == ["shani"]
    assert p.preds["t"].p("targets") == [3, 6, 11]


def test_transit_of_a_node_is_named_and_excluded():
    p = _plan(CK.saturn_transit(graha="rahu"))
    assert p.excluded_node and p.node_named == ["rahu:transit_position"] and p.transit_bodies == []


def test_vedha_card_is_excluded_because_its_obstructor_set_includes_nodes():
    p = _plan(E1.venus_vedha_card())
    assert p.excluded_node
    assert {"rahu:vedha_obstructor", "ketu:vedha_obstructor"} <= set(p.node_named)


def test_natal_conjunction_with_a_node_is_excluded_but_with_a_graha_is_not():
    ops = lambda partner: [
        CK.op("a", "natal_graha", "conjoins", "surya", target_role="b"),
        CK.op("b", "natal_graha", "conjoins", partner, target_role="a"),
    ]
    mk = lambda partner: CK.mk_card("SYN-C", "natal_promise", {"op": "AND", "args": [{"operand": "a"}, {"operand": "b"}]}, ops(partner))
    assert _plan(mk("ketu")).excluded_node
    assert not _plan(mk("mangala")).excluded_node


def test_dasha_lord_identity_of_a_node_is_evaluated_not_excluded():
    card = CK.mk_card(
        "SYN-ID",
        "dasha",
        {"op": "AND", "args": [{"operand": "md"}, {"operand": "ad"}]},
        [CK.op("md", "dasha_lord", "is_dasha_lord", "rahu"), CK.op("ad", "antardasha_lord", "is_antardasha_lord", "ketu")],
    )
    p = _plan(card)
    assert not p.excluded_node and not p.lord_generic


def test_reading_the_dasha_lord_without_naming_it_is_lord_generic():
    p = _plan(E1.dasha_card())
    assert p.lord_generic and not p.excluded_node and p.frame.kind == "md_lord"
    flag = CK.mk_card("SYN-FL", "dasha", {"operand": "f"}, [CK.op("f", "dasha_lord", "retrograde")], frame="dasha_lord_natal_position")
    assert _plan(flag).lord_generic


def test_naming_a_node_in_a_dasha_lord_position_read_is_excluded():
    card = CK.mk_card("SYN-DP", "dasha", {"operand": "a"}, [CK.op("a", "antardasha_lord", "occupies", "rahu", bhava=6)])
    assert _plan(card).excluded_node


def test_exceptions_are_not_evaluated_in_v1_and_fail_closed():
    card = CK.saturn_transit()
    res = compile_card(card)
    ir = copy.deepcopy(res.ir)
    ir["exceptions"] = [{"effect": "cancels"}]
    with pytest.raises(P.Unsupported) as e:
        P.plan_card(ir, operand_table(card))
    assert e.value.code == "EXCEPTIONS_NOT_EVALUATED"


def test_ir_that_disagrees_with_the_card_operands_is_refused():
    card = CK.saturn_transit()
    res = compile_card(card)
    ops = operand_table(card)
    ops["t"]["target_bhavas"] = [3, 6, 12]
    with pytest.raises(P.Unsupported) as e:
        P.plan_card(res.ir, ops)
    assert e.value.code == "IR_OPERAND_MISMATCH"
    ops2 = operand_table(card)
    ops2["t"]["doctrinal_graha"] = "guru"
    with pytest.raises(P.Unsupported):
        P.plan_card(res.ir, ops2)


def test_p4_double_transit_is_refused_by_the_compiler_and_by_the_planner():
    card = E1.two_transit_card({"target_bhavas": [11]}, {"target_bhavas": [11]})
    res = compile_card(card)
    assert res.status != "active" and "P4_DOUBLE_TRANSIT" in res.reasons
    with pytest.raises(P.Unsupported):
        P.plan_card(res.ir, operand_table(card)) if res.ir else (_ for _ in ()).throw(P.Unsupported("NOT_ACTIVE"))


def _unbound_transit():
    return CK.mk_card("SYN-UNB", "transit", {"operand": "t"}, [CK.op("t", "transiting_graha", "transits", None, target_bhavas=[3])], frame="chandra_lagna")


def test_a_quarantined_card_is_never_planned():
    card = _unbound_transit()
    res = compile_card(card)
    assert res.status != "active"
    with pytest.raises(P.Unsupported) as e:
        P.plan_card(res.ir, operand_table(card))
    assert e.value.code == "NOT_ACTIVE"


def test_an_active_card_the_engine_cannot_evaluate_is_refused_with_a_code():
    card = E1.av_card()  # compiles active (comparator supplied) but aṣṭakavarga operands are not evaluated in v1
    res = compile_card(card)
    assert res.status == "active"
    with pytest.raises(P.Unsupported) as e:
        P.plan_card(res.ir, operand_table(card))
    assert e.value.code  # a stable reason code is always given


def test_bhava_lord_without_the_lord_bhava_is_refused():
    card = CK.mk_card("SYN-BL", "natal_promise", {"operand": "l"}, [CK.op("l", "bhava_lord", "occupies", target_bhavas=[1])])
    res = compile_card(card)
    if res.status == "active":
        with pytest.raises(P.Unsupported):
            P.plan_card(res.ir, operand_table(card))


# ── units / manifest / bundle ────────────────────────────────────────────
def _world():
    cards = {
        "RB1-C001": [CK.saturn_transit("SYN-S1", (3, 6, 11))],  # conflict-free, evaluable
        "RB1-C002": [CK.saturn_transit("SYN-S2", (5,), graha="surya")],  # cluster VC01 member, evaluable
        "RB1-C003": [CK.saturn_transit("SYN-S3", (5,), graha="rahu")],  # cluster VC01 member, node-excluded
        "RB1-C004": [E1.dasha_card()],  # conflict-free, lord generic
        "RB1-C005": [CK.saturn_transit("SYN-S5", (5,), graha="rahu")],  # conflict-free, node-excluded
        "RB1-C006": [_unbound_transit()],  # conflict-free, quarantined by the compiler
        "RB1-C008": [E1.av_card()],  # conflict-free, active but not evaluable by the engine
        "RB1-C007": [CK.saturn_transit("SYN-S7", (2,), graha="guru"), CK.saturn_transit("SYN-S7B", (2,), graha="guru")],  # two member cards
    }
    rows = {
        "RB1-C001": {"category": "transit", "polarity": "promotive"},
        "RB1-C002": {"category": "transit", "polarity": "obstructive"},
        "RB1-C003": {"category": "transit", "polarity": "obstructive"},
        "RB1-C004": {"category": "dasha", "polarity": "obstructive"},
        "RB1-C005": {"category": "transit", "polarity": "promotive"},
        "RB1-C006": {"category": "transit", "polarity": "obstructive"},
        "RB1-C007": {"category": "transit", "polarity": "promotive"},
        "RB1-C008": {"category": "transit", "polarity": "obstructive"},
    }
    return CK.final_cards(rows, {"RB1-VC01": ["RB1-C002", "RB1-C003"]}), CK.attested_rules(cards)


def test_units_are_conflict_free_rules_plus_clusters_and_statuses_follow_the_planner():
    final, att = _world()
    units, recs, counts = U.build_units(final, att)
    by = {u["unit_id"]: u for u in units}
    assert counts["units"] == 7 and counts["conflict_free_units"] == 6 and counts["cluster_units"] == 1
    assert {u["unit_id"] for u in units} == {"RB1-C001", "RB1-C004", "RB1-C005", "RB1-C006", "RB1-C007", "RB1-C008", "RB1-VC01"}
    assert by["RB1-C001"]["status"] == U.EVALUABLE
    assert by["RB1-VC01"]["status"] == U.EVALUABLE and by["RB1-VC01"]["evaluable_members"] == ["RB1-C002"]  # one member excluded, unit still scored
    assert recs["RB1-C003"]["status"] == U.EXCLUDED_NODE and by["RB1-C005"]["status"] == U.EXCLUDED_NODE
    assert by["RB1-C006"]["status"] == "quarantined" and recs["RB1-C006"]["status"] == U.Q_COMPILE
    assert recs["RB1-C004"]["lord_generic"] is True and recs["RB1-C001"]["lord_generic"] is False
    assert by["RB1-C001"]["plane"] == "transit" and by["RB1-C001"]["polarity"] == "promotive" and by["RB1-C001"]["area_tags"] == ["GENERAL"]
    assert recs["RB1-C008"]["status"] == U.Q_ENGINE and len(recs["RB1-C008"]["reasons"]) == 1
    assert counts["unit_status"] == {"evaluable": 4, "excluded_node": 1, "quarantined": 2}
    assert len(recs["RB1-C007"]["member_cards"]) == 2 and recs["RB1-C007"]["logic_agree"] is True


def test_unit_hash_is_deterministic_and_sensitive_to_the_compiled_card():
    final, att = _world()
    u1 = U.build_units(final, att)[0]
    u2 = U.build_units(final, copy.deepcopy(att))[0]
    assert [u["unit_sha256"] for u in u1] == [u["unit_sha256"] for u in u2]
    att3 = copy.deepcopy(att)
    att3["rules"][0]["cards"][0]["ir_sha256"] = "0" * 64
    u3 = U.build_units(final, att3)[0]
    assert {u["unit_id"]: u["unit_sha256"] for u in u1} != {u["unit_id"]: u["unit_sha256"] for u in u3}


def test_build_units_fails_closed_on_inconsistent_inputs():
    final, att = _world()
    bad = copy.deepcopy(att)
    bad["rules"].pop()
    with pytest.raises(ValueError):
        U.build_units(final, bad)
    bad2 = copy.deepcopy(final)
    bad2["variant_conflict_clusters"][0]["variants"].append("RB1-C001")
    with pytest.raises(ValueError):
        U.build_units(bad2, att)
    with pytest.raises(ValueError):
        U.build_units(final, dict(att, attested_schema="x"))


def test_bundle_holds_only_evaluable_rules_and_no_words():
    final, att = _world()
    _units, recs, _c = U.build_units(final, att)
    b = U.build_bundle(att, recs)
    assert set(b["rules"]) == {"RB1-C001", "RB1-C002", "RB1-C004", "RB1-C007"}
    text = json.dumps(b)
    for needle in ('"quote"', '"witnesses"', '"quote_terms"', "named planet", "When the named"):
        assert needle not in text


def test_a_hash_form_card_that_could_not_be_converted_quarantines_the_rule():
    final, att = _world()
    att = copy.deepcopy(att)
    c = att["rules"][0]["cards"][0]
    c.update(status="unattested", hash_error="NotLocated: term", ir=None, ir_sha256=None, card_sha256=None)
    _u, recs, _c = U.build_units(final, att)
    assert recs["RB1-C001"]["status"] == U.Q_COMPILE and "HASH_FORM_UNCONVERTIBLE" in recs["RB1-C001"]["reasons"]
    assert recs["RB1-C001"]["compile_status"] == "quarantined"


def test_cli_builds_manifest_and_bundle_files_with_matching_hashes(tmp_path):
    from services.rulebook.engine import cli

    final, att = _world()
    fp, ap, yp = tmp_path / "final.json", tmp_path / "att.json", tmp_path / "y.md"
    fp.write_text(json.dumps(final))
    ap.write_text(json.dumps(att))
    yp.write_text("yardstick stand-in")
    out = tmp_path / "out"
    res = cli.build_manifest(fp, ap, yp, out)
    mbytes = (out / "UNIT_MANIFEST_v1_0.json").read_bytes()
    assert hashlib.sha256(mbytes).hexdigest() == res["manifest_sha256"]
    assert (out / "UNIT_MANIFEST_v1_0.sha256").read_text().split()[0] == res["manifest_sha256"]
    man = json.loads(mbytes)
    assert man["bundle_sha256"] == hashlib.sha256((out / "RULE_BUNDLE_v1_0.json").read_bytes()).hexdigest()
    assert man["binds"]["yardstick_sha256"] == hashlib.sha256(b"yardstick stand-in").hexdigest()
    assert man["conventions"]["node_policy_id"] == K.NODE_POLICY_ID and man["conventions"]["p4_double_transit"] == "off"
    assert "services/rulebook/engine/plan.py" in man["source_tree_sha256"]
    res2 = cli.build_manifest(fp, ap, yp, tmp_path / "out2")
    assert res2["manifest_sha256"] == res["manifest_sha256"]  # same inputs, same bytes
