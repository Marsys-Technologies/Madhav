"""Schema v1.2 (proposal v0.2, CR-006): v1.1 cards still validate; every new field rejects defaults.

The compiler validates v1.2 fields but does not evaluate them: a card that uses one is quarantined with
V12_FIELD_NOT_EVALUATED.
"""

from __future__ import annotations

import copy
import json

import pytest

from services.rulebook import constants as C
from services.rulebook.compiler import compile_card
from services.rulebook.schema import load_schema, schema_errors, semantic_errors, v12_features, validate_card

from . import _cards as K

V11_FACTORIES = [K.venus_vedha_card, K.dasha_card, K.av_card, K.natal_card]
V12_FACTORIES = [K.v12_vedha_card, K.v12_exempt_card, K.v12_av_card, K.v12_sign_card, K.v12_hash_card]


def _v11_schema():
    with (C.DATA_DIR / "RULE_CARD_SCHEMA_v1_1.json").open(encoding="utf-8") as fh:
        return json.load(fh)


# ── v1.1 compatibility ─────────────────────────────────────────────────────
@pytest.mark.parametrize("factory", V11_FACTORIES)
@pytest.mark.parametrize("version", ["rule-card-v1", "rule-card-v1.1"])
def test_v11_cards_validate_under_both_schemas(factory, version):
    card = factory()
    card["schema_version"] = version
    assert schema_errors(card, _v11_schema()) == []
    assert validate_card(card) == []
    assert v12_features(card) == []
    assert compile_card(card).status == "active"


MUTATIONS_V11 = [
    ("drop_class_group", lambda c: c["field2_target_scope"].pop("class_group")),
    ("bad_frame", lambda c: c["field3_reference_frame"].update(frame="nowhere")),
    ("bad_relation", lambda c: c["field5_typed_operands"][0].update(relation="sits")),
    ("chart_data", lambda c: c["field5_typed_operands"][0].update(sign=3)),
    ("extra_key", lambda c: c.update(extra=1)),
    ("bad_bhava", lambda c: c["field5_typed_operands"][0].update(bhava=13)),
    (
        "bad_field7",
        lambda c: c.update(field7_discrete_arithmetic=[{"kind": "bindus_of_8", "bindus": 9, "comparator": "ge"}]),
    ),
]


@pytest.mark.parametrize("name,mut", MUTATIONS_V11, ids=[m[0] for m in MUTATIONS_V11])
def test_v11_verdict_parity(name, mut):
    """For v1.1 cards, the v1.2 schema accepts and rejects exactly what v1.1 does."""
    card = K.venus_vedha_card()
    mut(card)
    assert bool(schema_errors(card, _v11_schema())) is True
    assert bool(schema_errors(card)) is True


V12_ON_V11 = [
    ("vedha_block", lambda c: K.v12_vedha_card()),
    ("bindu_gate", lambda c: K.v12_av_card()),
    ("target_sign_and_frame", lambda c: K.v12_sign_card()),
    ("hash_form", lambda c: K.v12_hash_card()),
    ("class_groups", lambda c: _with_class_groups(K.v12(K.natal_card()))),
    ("moolatrikona", lambda c: _rel(K.v12(K.natal_card()), "moolatrikona")),
]


def _with_class_groups(card):
    card["field2_target_scope"].pop("class_group")
    card["field2_target_scope"]["class_groups"] = ["major_gain", "cross_cutting"]
    return card


def _rel(card, rel):
    card["field5_typed_operands"][0]["relation"] = rel
    return card


@pytest.mark.parametrize("name,make", V12_ON_V11, ids=[m[0] for m in V12_ON_V11])
def test_v12_keys_rejected_on_v11_versions(name, make):
    card = make(None)
    assert validate_card(card) == [], validate_card(card)  # valid as v1.2
    card["schema_version"] = "rule-card-v1.1"
    assert validate_card(card), f"{name} must be rejected on v1.1"


# ── v1.2 fixtures: valid, validated only ──────────────────────────────────
@pytest.mark.parametrize("factory", [f for f in V12_FACTORIES if f is not K.v12_hash_card])
def test_v12_fixtures_valid_but_not_evaluated(factory):
    card = factory()
    assert validate_card(card) == [], validate_card(card)
    r = compile_card(card)
    assert r.reasons == ["V12_FIELD_NOT_EVALUATED"] and r.ir is None


def test_class_groups_alone_is_evaluated_as_filing_label():
    card = _with_class_groups(K.v12(K.natal_card()))
    r = compile_card(card)
    assert r.status == "active"
    assert r.ir["class_groups"] == ["cross_cutting", "major_gain"]


def test_class_group_xor_class_groups():
    card = _with_class_groups(K.v12(K.natal_card()))
    card["field2_target_scope"]["class_group"] = "major_gain"
    assert validate_card(card)
    card = K.v12(K.natal_card())
    card["field2_target_scope"].pop("class_group")
    assert validate_card(card)


# ── each new field rejects a default ───────────────────────────────────────
def _vv(card):
    return card["field5_typed_operands"][1]["vedha"]


def _bg(card):
    return card["field5_typed_operands"][1]["bindu_gate"]


def _ts(card):
    return card["field5_typed_operands"][1]["target_sign"]


REJECT = [
    # vedha
    ("vedha_no_exemption_block", K.v12_vedha_card, lambda c: _vv(c).pop("exemption")),
    ("vedha_stated_false_no_span", K.v12_vedha_card, lambda c: _vv(c)["exemption"].pop("clause_span")),
    ("vedha_stated_false_empty_span", K.v12_vedha_card, lambda c: _vv(c)["exemption"].update(clause_span=[])),
    (
        "vedha_stated_false_but_exempt_words",
        K.v12_vedha_card,
        lambda c: _vv(c)["exemption"].update(clause_span=["planets other than the slow one"]),
    ),
    ("vedha_stated_true_no_exempt_entry", K.v12_vedha_card, lambda c: _vv(c)["exemption"].update(stated=True)),
    ("vedha_obstructor_unquoted", K.v12_exempt_card, lambda c: _vv(c)["obstructors"][0].pop("quote_terms")),
    ("vedha_obstructor_empty_terms", K.v12_exempt_card, lambda c: _vv(c)["obstructors"][0].update(quote_terms=[])),
    ("vedha_obstructor_bad_status", K.v12_exempt_card, lambda c: _vv(c)["obstructors"][0].update(status="maybe")),
    (
        "vedha_primary_obstructs_itself",
        K.v12_vedha_card,
        lambda c: _vv(c)["obstructors"].append({"graha": "shukra", "status": "obstruct", "quote_terms": ["x"]}),
    ),
    (
        "vedha_duplicate_graha",
        K.v12_exempt_card,
        lambda c: _vv(c)["obstructors"].append({"graha": "shani", "status": "obstruct", "quote_terms": ["x"]}),
    ),
    ("vedha_relation_unquoted", K.v12_vedha_card, lambda c: _vv(c)["obstructor_relation"].pop("quote_terms")),
    ("vedha_relation_other", K.v12_vedha_card, lambda c: _vv(c)["obstructor_relation"].update(relation="conjoins")),
    ("vedha_universal_unquoted", K.v12_vedha_card, lambda c: _vv(c)["universal"].pop("quote_terms")),
    ("vedha_universal_other_operator", K.v12_vedha_card, lambda c: _vv(c)["universal"].update(operator="all_nine")),
    ("vedha_no_pairs", K.v12_vedha_card, lambda c: _vv(c).pop("vedha_pairs")),
    ("vedha_pair_unquoted", K.v12_vedha_card, lambda c: _vv(c)["vedha_pairs"][0].pop("quote_terms")),
    ("vedha_flat_list_alongside", K.v12_vedha_card, lambda c: c["field5_typed_operands"][1].update(target_bhavas=[9])),
    ("vedha_primary_copy", K.v12_vedha_card, lambda c: _vv(c).update(primary="shukra")),
    ("vedha_transit_house_unpaired", K.v12_vedha_card, lambda c: c["field5_typed_operands"][0].update(bhava=4)),
    ("vedha_self_pair", K.v12_vedha_card, lambda c: _vv(c)["vedha_pairs"][0].update(vedha_bhava=5)),
    (
        "vedha_counter_unquoted",
        K.v12_vedha_card,
        lambda c: _vv(c).update(counter_vedha={"kind": "obstructor_itself_under_vedha_does_not_obstruct"}),
    ),
    ("vedha_on_wrong_relation", K.v12_vedha_card, lambda c: c["field5_typed_operands"][1].update(relation="transits")),
    # bindu gate
    ("bindu_free_count_term", K.v12_av_card, lambda c: _bg(c).update(count_term="dots")),
    ("bindu_count_term_unquoted", K.v12_av_card, lambda c: _bg(c).pop("count_term_quote_terms")),
    ("bindu_convention_unquoted", K.v12_av_card, lambda c: _bg(c).pop("convention_terms")),
    ("bindu_no_convention", K.v12_av_card, lambda c: _bg(c).pop("count_convention")),
    ("bindu_relational_no_value", K.v12_av_card, lambda c: _bg(c).pop("value")),
    ("bindu_relational_value_unquoted", K.v12_av_card, lambda c: _bg(c).pop("value_terms")),
    (
        "bindu_rank_with_value",
        K.v12_av_card,
        lambda c: _bg(c).update(
            comparator="max_among_signs", rank_domain={"scope": "all_twelve_signs", "quote_terms": ["highest"]}
        ),
    ),
    (
        "bindu_rank_no_domain",
        K.v12_av_card,
        lambda c: (_bg(c).update(comparator="max_among_signs"), _bg(c).pop("value"), _bg(c).pop("value_terms")),
    ),
    (
        "bindu_rank_domain_unquoted",
        K.v12_av_card,
        lambda c: (
            _bg(c).update(comparator="max_among_signs", rank_domain={"scope": "all_twelve_signs"}),
            _bg(c).pop("value"),
            _bg(c).pop("value_terms"),
        ),
    ),
    ("bindu_bav_value_above_8", K.v12_av_card, lambda c: _bg(c).update(value=9)),
    ("bindu_no_owner", K.v12_av_card, lambda c: _bg(c).pop("varga_owner")),
    ("bindu_owner_unquoted", K.v12_av_card, lambda c: _bg(c).pop("varga_owner_terms")),
    ("bindu_owner_role_mismatch", K.v12_av_card, lambda c: _bg(c).update(varga_owner="sav")),
    ("bindu_owner_differs_from_graha", K.v12_av_card, lambda c: _bg(c).update(varga_owner="guru")),
    ("bindu_no_sodhana", K.v12_av_card, lambda c: _bg(c).pop("sodhana_stage")),
    ("bindu_sodhana_unquoted", K.v12_av_card, lambda c: _bg(c).update(sodhana_stage="trikona")),
    (
        "bindu_and_field7",
        K.v12_av_card,
        lambda c: c["field7_discrete_arithmetic"].append({"kind": "bindus_of_8", "bindus": 0, "comparator": "eq"}),
    ),
    ("bindu_reads_dangling", K.v12_av_card, lambda c: _bg(c).update(reads_sign_of="nope")),
    ("bindu_reads_itself", K.v12_av_card, lambda c: _bg(c).update(reads_sign_of="sat_av")),
    # target_sign / frame
    ("sign_no_locus", K.v12_sign_card, lambda c: _ts(c).pop("locus")),
    ("sign_locus_unquoted", K.v12_sign_card, lambda c: _ts(c).pop("locus_terms")),
    ("sign_locus_contradicts_role", K.v12_sign_card, lambda c: _ts(c).update(locus="natal")),
    (
        "sign_of_role_not_graha",
        K.v12_sign_card,
        lambda c: (
            c["field5_typed_operands"].append({"id": "h5", "role": "bhava", "relation": "occupies", "bhava": 5}),
            _ts(c).update(of_role="h5"),
        ),
    ),
    ("sign_of_role_dangling", K.v12_sign_card, lambda c: _ts(c).update(of_role="nope")),
    ("sign_kind_field", K.v12_sign_card, lambda c: _ts(c).update(kind="exaltation")),
    ("sign_wrong_frame", K.v12_sign_card, lambda c: c["field3_reference_frame"].update(frame="janma_lagna")),
    ("sign_frame_without_terms", K.v12_sign_card, lambda c: c["field3_reference_frame"].pop("frame_terms")),
    ("sign_on_non_dignity", K.v12_sign_card, lambda c: c["field5_typed_operands"][1].update(relation="transits")),
    # hash form / witnesses
    ("hash_with_clear_quote", K.v12_hash_card, lambda c: c["field1_citation"].update(quote="clear words")),
    (
        "hash_with_clear_term",
        K.v12_hash_card,
        lambda c: c["field5_typed_operands"][0].update(quote_terms=["test planet"]),
    ),
    ("hash_without_sha", K.v12_hash_card, lambda c: c["field1_citation"].pop("quote_sha256")),
    ("hash_without_witnesses", K.v12_hash_card, lambda c: c["field1_citation"].pop("witnesses")),
    (
        "witness_empty_range",
        K.v12_hash_card,
        lambda c: c["field5_typed_operands"][0]["quote_terms"][0].update(token_end=1),
    ),
    (
        "witness_uncited_passage",
        K.v12_hash_card,
        lambda c: c["field5_typed_operands"][0]["quote_terms"][0].update(passage_id="synthtext_pg0009_c01:en:p001"),
    ),
    ("clear_form_with_sha", K.v12_vedha_card, lambda c: c["field1_citation"].update(quote_sha256="0" * 64)),
]


@pytest.mark.parametrize("name,factory,mut", REJECT, ids=[r[0] for r in REJECT])
def test_new_fields_reject_defaults(name, factory, mut):
    card = factory()
    assert validate_card(card) == []
    mut(card)
    errs = validate_card(card)
    assert errs, f"{name}: accepted"
    r = compile_card(card)
    assert r.reasons == ["SCHEMA_INVALID"] and r.ir is None


ABSENCE_IS_TYPED = [
    ("no_obstructor_relation", K.v12_vedha_card, lambda c: _vv(c).pop("obstructor_relation")),
    ("no_universal_no_list", K.v12_vedha_card, lambda c: _vv(c).pop("universal")),
    ("no_counter_vedha", K.v12_vedha_card, lambda c: None),
    (
        "owner_undeclared",
        K.v12_av_card,
        lambda c: (_bg(c).update(varga_owner="undeclared"), _bg(c).pop("varga_owner_terms")),
    ),
    (
        "convention_undeclared",
        K.v12_av_card,
        lambda c: (_bg(c).update(count_convention="undeclared"), _bg(c).pop("convention_terms")),
    ),
    (
        "sav_value_above_8",
        K.v12_av_card,
        lambda c: (
            c["field5_typed_operands"][1].update(role="ashtakavarga_sav"),
            c["field5_typed_operands"][1].pop("doctrinal_graha"),
            _bg(c).update(varga_owner="sav", value=30),
        ),
    ),
]


@pytest.mark.parametrize("name,factory,mut", ABSENCE_IS_TYPED, ids=[r[0] for r in ABSENCE_IS_TYPED])
def test_typed_absence_is_valid_and_never_filled(name, factory, mut):
    card = factory()
    before = copy.deepcopy(card)
    mut(card)
    snapshot = copy.deepcopy(card)
    assert validate_card(card) == [], validate_card(card)
    assert card == snapshot  # validation never fills a value in
    assert compile_card(card).reasons == ["V12_FIELD_NOT_EVALUATED"]
    assert before is not card


def test_bindu_convention_map_asserts_no_bphs_polarity():
    conv = C.bindu_conventions()
    for text, terms in conv["texts"].items():
        for term, entry in terms.items():
            assert entry["meaning"] == "undeclared", (text, term)
    card = K.av_card()
    card["field1_citation"]["text_id"] = "bphs"
    card["field1_citation"]["passage_ids"] = ["bphs_pg0001_c01:en:p001"]
    card["field5_typed_operands"][1]["quote_terms"] = ["without rekhas"]
    assert "BINDU_CONVENTION_UNDECLARED" in compile_card(card).reasons


def test_schema_document_is_well_formed():
    s = load_schema()
    assert s["$defs"]["card"]["properties"]["schema_version"]["enum"][-1] == "rule-card-v1.2"
    assert "moolatrikona" in s["$defs"]["operand"]["properties"]["relation"]["enum"]
    assert "sign_intrinsic" in s["$defs"]["card"]["properties"]["field3_reference_frame"]["properties"]["frame"]["enum"]
    assert set(s["$defs"]["bindu_gate"]["properties"]["count_term"]["enum"]) == {"rekha", "bindu", "benefic_dot"}
    assert s["$defs"]["bindu_gate"]["properties"]["sodhana_stage"]["enum"] == [
        "prastara",
        "trikona",
        "ekadhipatya",
        "undeclared",
    ]
    assert "primary" not in s["$defs"]["vedha"]["properties"]

    def keys(o):
        if isinstance(o, dict):
            for k, v in o.items():
                yield k
                yield from keys(v)
        elif isinstance(o, list):
            for v in o:
                yield from keys(v)

    assert "default" not in set(keys(s))  # no JSON Schema default anywhere


def test_semantic_rules_only_run_on_schema_valid_cards():
    assert semantic_errors(K.v12_vedha_card()) == []
