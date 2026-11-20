"""Hash form (quote_form "sha256") is a storage form: evaluated, never a silent pass (CR-006 §2.5).

With a witness resolver the card compiles exactly like its clear twin (same logic_sha256) and
every lexical check runs on the resolved words. Without one, each check that needs the words
records TEXT_UNRESOLVED and the card is quarantined. Synthetic cards and invented prose only.
"""

from __future__ import annotations

from services.rulebook import schema as rb_schema
from services.rulebook.compiler import compile_card
from services.rulebook.lints import lint_licence, lint_vedha
from tests.rulebook import _cards as K
from tests.rulebook._hash_form import to_hash_form


def test_hash_form_card_is_valid_and_carries_no_text():
    card, _ = to_hash_form(K.natal_card())
    assert rb_schema.validate_card(card) == [], rb_schema.validate_card(card)
    assert "quote" not in card["field1_citation"]
    assert lint_licence(card) == []  # restricted text id (synthtext), but no clear words


def test_resolved_hash_form_compiles_like_its_clear_twin():
    for make in (K.natal_card, K.dasha_card):  # dasha_card carries a verse-stated OR
        clear = make()
        card, wt = to_hash_form(clear)
        rc, rh = compile_card(clear), compile_card(card, witness_text=wt)
        assert rc.status == "active" and rh.status == "active", rh.reasons
        assert rh.logic_sha256 == rc.logic_sha256
        assert rh.ir["citation"]["quote_sha256"] == card["field1_citation"]["quote_sha256"]


def test_unresolved_hash_form_is_quarantined_text_unresolved_only():
    card, _ = to_hash_form(K.dasha_card())
    r = compile_card(card)
    assert r.status == "quarantined_not_evaluable"
    assert r.reasons == ["TEXT_UNRESOLVED"]
    assert r.ir is not None and r.ir["counting"]["counts_toward_n"] is False


def test_lexical_check_still_runs_on_resolved_text():
    clear = K.natal_card()
    clear["field1_citation"]["quote"] = (
        "The test planet by its mean place in backward motion gives its good results to the native."
    )
    clear["field5_typed_operands"][0]["quote_terms"] = ["test planet", "mean place", "backward motion"]
    card, wt = to_hash_form(clear)
    assert "MEAN_OPERAND" in compile_card(card, witness_text=wt).reasons
    assert compile_card(card).reasons == ["TEXT_UNRESOLVED"]  # never a silent pass


def test_quote_sha256_must_match_resolved_text():
    card, wt = to_hash_form(K.natal_card())
    card["field1_citation"]["quote_sha256"] = "0" * 64
    assert "QUOTE_SHA256_MISMATCH" in compile_card(card, witness_text=wt).reasons


def test_vedha_lint_on_hash_form():
    clear = K.venus_vedha_card()
    clear["field3_reference_frame"]["frame_terms"] = ["from the natal Moon"]  # a contiguous span of the frame quote
    card, wt = to_hash_form(clear)
    assert lint_vedha(card, wt) == []
    assert [f.code for f in lint_vedha(card)] == ["VEDHA_TEXT_UNRESOLVED"]
    card["field5_typed_operands"] = card["field5_typed_operands"][:1]
    card["field4_necessary_gate"]["expr"] = {"operand": "ven_t"}
    assert [f.code for f in lint_vedha(card, wt)] == ["VEDHA_CLAUSE_MISSING"]
