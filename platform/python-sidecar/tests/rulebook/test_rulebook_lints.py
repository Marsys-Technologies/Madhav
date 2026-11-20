"""E1: P4 semantic lint, licence lint, vedha / frame / testimony lints, import hygiene."""

from __future__ import annotations

from pathlib import Path

import pytest

from services.rulebook import constants as C
from services.rulebook.compiler import compile_card
from services.rulebook.lints import (
    BUILD_FAIL,
    build_ok,
    lint_frame,
    lint_licence,
    lint_p4,
    lint_testimony,
    lint_vedha,
    run_lints,
)

from . import _cards as K


# ── P4 ──────────────────────────────────────────────────────────────────────
P4_POSITIVE = [
    ("same_house", {"bhava": 5}, {"bhava": 5}, "AND"),
    ("aspect_on_transit_house", {"bhava": 5}, {"bhava": 5, "relation": "aspects"}, "AND"),
    ("saturn_on_jupiter_sign", {"bhava": 5}, {"target_role": "ju"}, "AND"),
    ("group_overlap", {"relation": "in_bhava_group", "bhava_group": "kendra"}, {"bhava": 4}, "AND"),
    ("overlapping_house_sets", {"target_bhavas": [2, 5]}, {"target_bhavas": [5, 9]}, "AND"),
]
P4_NEGATIVE = [
    ("disjunction_only", {"bhava": 5}, {"bhava": 5}, "OR"),
    ("different_houses", {"bhava": 5}, {"bhava": 9}, "AND"),
    ("natal_saturn", {"bhava": 5}, {"bhava": 5, "role": "natal_graha", "relation": "occupies"}, "AND"),
    ("no_targets", {}, {}, "AND"),
]


@pytest.mark.parametrize("name,j,s,op", P4_POSITIVE, ids=[c[0] for c in P4_POSITIVE])
def test_p4_positive(name, j, s, op):
    card = K.two_transit_card(j, s, op)
    r = compile_card(card)
    found = lint_p4(card, r)
    assert found and all(f.severity == BUILD_FAIL for f in found)
    assert "P4_DOUBLE_TRANSIT" in r.reasons
    assert not build_ok(found)


@pytest.mark.parametrize("name,j,s,op", P4_NEGATIVE, ids=[c[0] for c in P4_NEGATIVE])
def test_p4_negative(name, j, s, op):
    card = K.two_transit_card(j, s, op)
    r = compile_card(card)
    assert lint_p4(card, r) == []
    assert "P4_DOUBLE_TRANSIT" not in r.reasons


def test_p4_inside_branches_and_exceptions():
    card = K.two_transit_card({"bhava": 5}, {"bhava": 9}, "AND")
    card["field5_typed_operands"] += [
        {"id": "ju9", "role": "transiting_graha", "doctrinal_graha": "guru", "relation": "transits", "bhava": 9},
        {"id": "sa5", "role": "transiting_graha", "doctrinal_graha": "shani", "relation": "transits", "bhava": 5},
    ]
    # (Ju5 AND Sa9) OR (Ju9 AND Sa9): the second branch requires both on house 9
    card["field4_necessary_gate"]["expr"] = {
        "op": "OR",
        "args": [
            {"op": "AND", "args": [{"operand": "ju"}, {"operand": "sa"}]},
            {"op": "AND", "args": [{"operand": "ju9"}, {"operand": "sa"}]},
        ],
    }
    assert lint_p4(card)
    # negated Saturn requires nothing
    card["field4_necessary_gate"]["expr"] = {
        "op": "AND",
        "args": [{"operand": "ju9"}, {"op": "NOT", "args": [{"operand": "sa"}]}],
    }
    assert lint_p4(card) == []
    # in a field-6 exception condition
    card["field6_exceptions"] = [
        {
            "condition": {"op": "AND", "args": [{"operand": "ju"}, {"operand": "sa5"}]},
            "effect": "cancels",
            "school_scope": "same_text_only",
        }
    ]
    assert lint_p4(card)


def test_p4_runs_on_uncompilable_card():
    card = K.two_transit_card({"bhava": 5}, {"bhava": 5})
    card["schema_version"] = "rule-card-v9"
    assert compile_card(card).ir is None
    assert lint_p4(card)


# ── licence ─────────────────────────────────────────────────────────────────
def _pd_card(edition=None):
    card = K.natal_card()
    cite = card["field1_citation"]
    cite["text_id"] = "sarvartha_chintamani"
    cite["passage_ids"] = ["sarvartha_chintamani_pg0001_c01:en:p001"]
    if edition is not None:
        cite["edition"] = edition
    return card


def test_licence_restricted_quote_fails():
    found = lint_licence(K.natal_card())
    assert [f.code for f in found] == ["QUOTE_RESTRICTED_EDITION"]
    assert not build_ok(found)


def test_licence_public_domain_passes():
    assert lint_licence(_pd_card()) == []
    allow = C.licence_allowlist()
    assert lint_licence(_pd_card(allow["public_domain"][0]["edition"])) == []


def test_licence_edition_mismatch_fails():
    assert [f.code for f in lint_licence(_pd_card("Some 1980 reprint"))] == ["QUOTE_EDITION_MISMATCH"]


def test_licence_passage_from_restricted_text_fails():
    card = _pd_card()
    card["field1_citation"]["passage_ids"] = ["bphs_pg0001_c01:en:p001"]
    assert any(f.code == "QUOTE_RESTRICTED_EDITION" for f in lint_licence(card))


def test_licence_nested_quotes_are_checked():
    card = _pd_card()
    card["field3_reference_frame"]["frame_citation"] = {
        "passage_ids": ["phaladeepika_pg0001_c01:en:p001"],
        "quote": "invented frame words for a test only",
    }
    card["field6_exceptions"] = [
        {
            "condition": {"operand": "ven_r"},
            "effect": "reduces",
            "school_scope": "same_text_only",
            "citation": {"work": "x", "text_id": "hora_sara", "quote": "invented words"},
        }
    ]
    codes = [f.detail for f in lint_licence(card)]
    assert any("phaladeepika" in d for d in codes) and any("hora_sara" in d for d in codes)


def test_licence_redacted_card_passes():
    card = K.natal_card()
    card["field1_citation"]["quote"] = ""
    assert lint_licence(card) == []


def test_licence_unknown_edition_fails():
    card = K.natal_card()
    del card["field1_citation"]["text_id"]
    card["field1_citation"]["passage_ids"] = ["not-a-passage-id"]
    assert lint_licence(card)


def test_allowlist_is_conservative():
    allow = C.licence_allowlist()
    pd = {e["text_id"] for e in allow["public_domain"]}
    restricted = {e["text_id"] for e in allow["restricted"]}
    assert pd == {"sarvartha_chintamani"}
    assert {"bphs", "phaladeepika", "hora_sara", "jataka_parijata", "saravali"} <= restricted
    assert not pd & restricted


# ── vedha / frame / testimony ──────────────────────────────────────────────
def test_vedha_lint():
    card = K.venus_vedha_card()
    assert lint_vedha(card) == []
    card["field5_typed_operands"] = card["field5_typed_operands"][:1]
    card["field4_necessary_gate"]["expr"] = {"operand": "ven_t"}
    assert [f.code for f in lint_vedha(card)] == ["VEDHA_CLAUSE_MISSING"]
    card["field1_citation"]["quote"] = "If the test planet passes through the fifth sign it brings trouble."
    assert lint_vedha(card) == []


def test_frame_lints():
    card = K.venus_vedha_card()
    del card["field3_reference_frame"]["frame_terms"]
    del card["field3_reference_frame"]["frame_citation"]
    assert [f.code for f in lint_frame(card, compile_card(card))] == ["FRAME_UNATTESTED"]
    natal = K.natal_card()  # frame-invariant predicate: no lint even without frame words
    assert lint_frame(natal, compile_card(natal)) == []
    d = K.dasha_card()
    d["field3_reference_frame"]["frame"] = "sign_of_transit_only"
    assert "FRAME_PROPOSE_SIGN_INTRINSIC" in [f.code for f in lint_frame(d, compile_card(d))]


def test_testimony_lint_catches_tampered_ir():
    card = K.natal_card()
    card["provenance"] = "commentarial_practice"
    card["commentarial_source"] = {"author": "Synthetic", "work": "Synthetic"}
    r = compile_card(card)
    assert r.ir["counting"] == {"counts_toward_n": False, "testimony": True}
    assert lint_testimony(r.ir) == []
    bad = dict(r.ir, counting={"counts_toward_n": True, "testimony": True})
    assert [f.code for f in lint_testimony(bad)] == ["TESTIMONY_COUNTED"]
    q = dict(compile_card(K.natal_card()).ir, status="quarantined_not_evaluable")
    assert "QUARANTINED_COUNTED" in [f.code for f in lint_testimony(q)]
    e = dict(r.ir, exceptions=[{"effect": "delays", "increments_n": True}])
    assert "NOTE_EFFECT_COUNTED" in [f.code for f in lint_testimony(e)]


def test_run_lints_combines():
    card = K.two_transit_card({"bhava": 5}, {"bhava": 5})
    codes = {f.code for f in run_lints(card, compile_card(card))}
    assert {"P4_DOUBLE_TRANSIT", "QUOTE_RESTRICTED_EDITION"} <= codes


# ── import hygiene (§N.7.3, E0 hazards 1, 7, 8) ────────────────────────────
def test_package_never_imports_gochara_rules_or_reference_tables():
    import ast as pyast  # stdlib parser; the package's own module is services.rulebook.ast

    pkg = Path(C.__file__).parent
    for src in pkg.glob("*.py"):
        tree = pyast.parse(src.read_text(encoding="utf-8"))
        for node in pyast.walk(tree):
            if isinstance(node, pyast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, pyast.ImportFrom):
                names = [node.module or ""] + [a.name for a in node.names]
            else:
                names = []
            assert not any("gochara_rules" in n or n == "ashtakavarga" for n in names), src.name
        # L0 reference tables may be named in docstrings/comments, never in code
        docstrings = {
            id(n.body[0].value)
            for n in pyast.walk(tree)
            if isinstance(n, (pyast.Module, pyast.ClassDef, pyast.FunctionDef))
            and n.body
            and isinstance(n.body[0], pyast.Expr)
            and isinstance(n.body[0].value, pyast.Constant)
        }
        for n in pyast.walk(tree):
            if isinstance(n, pyast.Constant) and isinstance(n.value, str) and id(n) not in docstrings:
                assert "reference_houses" not in n.value and "reference_planets" not in n.value, src.name
