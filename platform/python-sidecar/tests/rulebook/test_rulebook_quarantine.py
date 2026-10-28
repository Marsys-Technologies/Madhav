"""E1: every typed quarantine reason fires on a synthetic card, and a clean card compiles active."""

from __future__ import annotations

import pytest

from services.rulebook import constants as C
from services.rulebook.compiler import compile_card
from services.rulebook.quarantine import Reason

from . import _cards as K


def _op(card, oid):
    return next(o for o in card["field5_typed_operands"] if o["id"] == oid)


def m_schema(c):
    c["schema_version"] = "rule-card-v9"


def m_dangling(c):
    c["field4_necessary_gate"]["expr"] = {"op": "AND", "args": [{"operand": "ven_t"}, {"operand": "nope"}]}


def m_unmapped(c):
    _op(c, "ven_r")["relation"] = "is_dasha_lord"


def m_role_relation(c):
    _op(c, "sat_av")["role"] = "bhava"


def m_unbound(c):
    del _op(c, "ven_r")["doctrinal_graha"]


def m_target_unbound(c):
    del _op(c, "ven_t")["bhava"]


def m_or_not_verse(c):
    c["field1_citation"]["quote"] = (
        "During the period when the sub lord stands sixth and eighth the native meets obstacles."
    )


def m_tautology(c):
    c["field1_citation"]["quote"] += " whether benefic or malefic"
    ops = c["field5_typed_operands"]
    ops[0] = {"id": "ben", "role": "transiting_graha", "graha_class": "benefic", "relation": "transits", "bhava": 5}
    ops.append({"id": "mal", "role": "transiting_graha", "graha_class": "malefic", "relation": "transits", "bhava": 5})
    c["field4_necessary_gate"]["expr"] = {
        "op": "AND",
        "args": [{"op": "OR", "args": [{"operand": "ben"}, {"operand": "mal"}]}, {"operand": "ven_v"}],
    }


def m_missing_comparator(c):
    c["field7_discrete_arithmetic"] = []


def m_ambiguous(c):
    c["field7_discrete_arithmetic"].append({"kind": "bindus_of_8", "bindus": 8, "comparator": "eq"})


def m_bindu_unlinked(c):
    del _op(c, "sat_av")["target_role"]


def m_bindu_convention(c):
    _op(c, "sat_av")["quote_terms"] = ["no dots", "its own chart"]


def m_frame_missing(c):
    del c["field3_reference_frame"]


def m_frame_deferred(c):
    c["field3_reference_frame"]["frame"] = "surya_lagna"


def m_frame_role(c):
    c["field3_reference_frame"]["frame"] = "natal_position_of_role"


def m_frame_plane(c):
    c["field3_reference_frame"]["frame"] = "sign_of_transit_only"


def m_plane_role(c):
    c["field2_target_scope"]["category"] = "transit"


def m_mean(c):
    _op(c, "ven_t")["quote_terms"].append("mean planet")


def m_node_model(c):
    _op(c, "ven_t")["doctrinal_graha"] = "rahu"
    _op(c, "ven_t")["quote_terms"] = ["mean node", "fifth sign"]


def m_non_unique(c):
    c["field5_typed_operands"] = [
        {"id": "kar", "role": "karaka", "doctrinal_graha": "guru", "relation": "occupies", "bhava": 1}
    ]
    c["field4_necessary_gate"]["expr"] = {"operand": "kar"}


def m_class_condition(c):
    op = _op(c, "ven_t")
    del op["doctrinal_graha"]
    op["graha_class"] = "natural_benefic"


def m_class_sense(c):
    op = _op(c, "ven_t")
    del op["doctrinal_graha"]
    op["graha_class"] = "benefic"


def m_df02(c):
    op = _op(c, "ad6")
    del op["bhava"]
    op["relation"] = "in_bhava_group"
    op["bhava_group"] = "panaphara"


def m_vedha_exempt(c):
    _op(c, "ven_v")["quote_terms"].append("planets other than the Sun")


def m_obstructor(c):
    _op(c, "ven_v")["quote_terms"] = ["struck by malefics", "ninth"]


def m_scope(c):
    c["field6_exceptions"] = [{"condition": {"operand": "ven_v"}, "effect": "cancels", "school_scope": "parashari"}]


def m_p4(c):
    pass


CASES = [
    (Reason.SCHEMA_INVALID, K.venus_vedha_card, m_schema),
    (Reason.DANGLING_OPERAND_REF, K.venus_vedha_card, m_dangling),
    (Reason.OPERAND_SOURCE_UNMAPPED, K.natal_card, m_unmapped),
    (Reason.ROLE_RELATION_MISMATCH, K.av_card, m_role_relation),
    (Reason.UNBOUND_OPERAND, K.natal_card, m_unbound),
    (Reason.TARGET_UNBOUND, K.venus_vedha_card, m_target_unbound),
    (Reason.OR_NOT_VERSE_STATED, K.dasha_card, m_or_not_verse),
    (Reason.TAUTOLOGICAL_DISJUNCTION, K.venus_vedha_card, m_tautology),
    (Reason.MISSING_COMPARATOR, K.av_card, m_missing_comparator),
    (Reason.AMBIGUOUS_COMPARATOR_BINDING, K.av_card, m_ambiguous),
    (Reason.BINDU_TARGET_UNLINKED, K.av_card, m_bindu_unlinked),
    (Reason.BINDU_CONVENTION_UNDECLARED, K.av_card, m_bindu_convention),
    (Reason.FRAME_MISSING, K.venus_vedha_card, m_frame_missing),
    (Reason.FRAME_UNSUPPORTED_V1, K.venus_vedha_card, m_frame_deferred),
    (Reason.FRAME_ROLE_UNBOUND, K.venus_vedha_card, m_frame_role),
    (Reason.FRAME_PLANE_CONTRADICTION, K.dasha_card, m_frame_plane),
    (Reason.PLANE_ROLE_CONTRADICTION, K.natal_card, m_plane_role),
    (Reason.MEAN_OPERAND, K.venus_vedha_card, m_mean),
    (Reason.NODE_MODEL_MISMATCH, K.venus_vedha_card, m_node_model),
    (Reason.NON_UNIQUE_LOOKUP, K.natal_card, m_non_unique),
    (Reason.GRAHA_CLASS_CONDITION_MISSING, K.venus_vedha_card, m_class_condition),
    (Reason.GRAHA_CLASS_SENSE_UNPINNED, K.venus_vedha_card, m_class_sense),
    (Reason.BHAVA_GROUP_DF02_OPEN, K.dasha_card, m_df02),
    (Reason.VEDHA_EXEMPTION_NOT_ENCODABLE, K.venus_vedha_card, m_vedha_exempt),
    (Reason.UNDECLARED_OBSTRUCTOR_SET, K.venus_vedha_card, m_obstructor),
    (Reason.SCHOOL_SCOPE_TEXTS_UNDECLARED, K.venus_vedha_card, m_scope),
    (Reason.P4_DOUBLE_TRANSIT, lambda: K.two_transit_card({"bhava": 5}, {"bhava": 5}), m_p4),
]


@pytest.mark.parametrize("factory", [K.venus_vedha_card, K.dasha_card, K.av_card, K.natal_card])
def test_clean_fixtures_compile_active(factory):
    r = compile_card(factory())
    assert r.status == "active", r.reasons
    assert r.findings == []
    assert r.ir["counting"]["counts_toward_n"] is True


@pytest.mark.parametrize("reason,factory,mutate", CASES, ids=[c[0].value for c in CASES])
def test_each_reason_quarantines(reason, factory, mutate):
    card = factory()
    mutate(card)
    r = compile_card(card)
    assert reason.value in r.reasons
    assert r.status == "quarantined_not_evaluable"
    if r.ir is not None:
        assert r.ir["counting"]["counts_toward_n"] is False


def test_every_reason_has_a_case():
    # V12_FIELD_NOT_EVALUATED is covered in test_rulebook_schema_v12.py
    assert {c[0] for c in CASES} | {Reason.V12_FIELD_NOT_EVALUATED} == set(Reason)


def test_frame_never_defaulted():
    card = K.venus_vedha_card()
    del card["field3_reference_frame"]
    r = compile_card(card)
    assert r.ir is None and r.reasons == ["FRAME_MISSING"]


def test_no_default_comparator_inserted():
    card = K.av_card()
    card["field7_discrete_arithmetic"] = []
    r = compile_card(card)
    av = [a for a in r.ir["gate"]["args"] if a["operand_id"] == "sat_av"][0]
    assert av["comparison"] is None


def test_card_stated_comparator_is_carried_verbatim():
    r = compile_card(K.av_card())
    av = [a for a in r.ir["gate"]["args"] if a["operand_id"] == "sat_av"][0]
    assert av["comparison"] == {"kind": "bindus_of_8", "op": "eq", "value": 0, "count_convention": "benefic_points"}


def test_self_declared_benefic_dots_convention():
    card = K.av_card()
    card["field1_citation"]["text_id"] = "bphs"
    card["field1_citation"]["passage_ids"] = ["bphs_pg0001_c01:en:p001"]
    assert compile_card(card).status == "active"  # 'benefic dots': the verse states the polarity


def test_venus_vedha_obstructor_set_partial_na():
    r = compile_card(K.venus_vedha_card())
    v = [a for a in r.ir["gate"]["args"] if a["relation"] == "vedha_by"][0]["obstructors"]
    assert v["primary"] == "shukra"
    assert set(v["undeclared"]) == {"chandra", "rahu", "ketu"}
    assert "shukra" not in v["certain"] and v["exempt"] == []
    assert "vedha_obstructor_status_moon_nodes" in r.convention_pending


def test_node_model_requirements():
    t = K.venus_vedha_card()
    op = t["field5_typed_operands"][0]
    op["doctrinal_graha"] = "rahu"
    r = compile_card(t)
    assert r.status == "active"
    assert r.ir["gate"]["args"][0]["node_model"] == "true"  # L0 transit
    n = K.natal_card()
    n["field5_typed_operands"][0]["doctrinal_graha"] = "rahu"
    assert compile_card(n).ir["gate"]["node_model"] == "mean"  # L1 natal
    n["field5_typed_operands"][0]["quote_terms"] = ["true node"]
    assert "NODE_MODEL_MISMATCH" in compile_card(n).reasons
    n["field5_typed_operands"][0]["quote_terms"] = ["mean node"]
    assert compile_card(n).status == "active"  # matches L1


def test_bhava_groups_from_package_constants():
    card = K.dasha_card()
    op = card["field5_typed_operands"][1]
    del op["bhava"]
    op["relation"] = "in_bhava_group"
    op["bhava_group"] = "kendra"
    r = compile_card(card)
    assert r.status == "active"
    assert C.BHAVA_GROUPS["kendra"]["members"] == (1, 4, 7, 10)
    assert C.BHAVA_GROUPS["panaphara"]["members"] == (2, 5, 8, 11)
    assert C.BHAVA_GROUPS["apoklima"]["members"] == (3, 6, 9, 12)
    for g in ("kendra", "panaphara", "apoklima"):
        assert any(p.startswith("bphs_") for p in C.BHAVA_GROUPS[g]["citation"])


def test_frame_role_operand_is_typed():
    card = K.venus_vedha_card()
    card["field3_reference_frame"] = {
        "frame": "natal_position_of_role",
        "frame_role": "kar",
        "frame_terms": ["from the karaka"],
    }
    card["field5_typed_operands"].append(
        {"id": "kar", "role": "karaka", "doctrinal_graha": "guru", "relation": "occupies", "bhava": 1}
    )
    r = compile_card(card)
    assert "NON_UNIQUE_LOOKUP" in r.reasons  # karaka school unpinned, even outside the gate
    assert r.ir["frame"]["role_operand"]["operand_id"] == "kar"
