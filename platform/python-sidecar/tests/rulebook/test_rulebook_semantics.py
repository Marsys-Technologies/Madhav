"""E1: deterministic IR hashing and bypass tests for the reference semantics."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from services.rulebook.ast import (
    CardOutcome,
    ExceptionNode,
    NotAssessedError,
    Pred,
    QuarantinedCardError,
    Tri,
    card_outcome,
    render_tri,
    tally,
)
from services.rulebook.compiler import canonical_json, compile_card

from . import _cards as K

T, F, NA = Tri.TRUE, Tri.FALSE, Tri.NOT_ASSESSED
SIDECAR = Path(__file__).resolve().parents[2]


# ── determinism ─────────────────────────────────────────────────────────────
def _reorder(obj):
    if isinstance(obj, dict):
        return {k: _reorder(obj[k]) for k in reversed(list(obj))}
    if isinstance(obj, list):
        return [_reorder(v) for v in obj]
    return obj


@pytest.mark.parametrize("factory", [K.venus_vedha_card, K.dasha_card, K.av_card, K.natal_card])
def test_ir_sha_stable_in_process_and_key_order(factory):
    a = compile_card(factory())
    b = compile_card(factory())
    c = compile_card(_reorder(factory()))
    assert a.ir_sha256 == b.ir_sha256 == c.ir_sha256
    assert canonical_json(a.ir) == canonical_json(c.ir)


def test_ir_sha_stable_across_processes():
    code = (
        "import json,sys; sys.path.insert(0, %r); from tests.rulebook import _cards as K;"
        "from services.rulebook.compiler import compile_card;"
        "print(json.dumps([compile_card(f()).ir_sha256 for f in "
        "(K.venus_vedha_card, K.dasha_card, K.av_card, K.natal_card)]))"
    ) % str(SIDECAR)
    outs = set()
    for seed in ("0", "1", "12345"):
        env = dict(os.environ, PYTHONHASHSEED=seed)
        res = subprocess.run(
            [sys.executable, "-c", code], cwd=SIDECAR, env=env, capture_output=True, text=True, check=True
        )
        outs.add(res.stdout.strip())
    assert len(outs) == 1
    local = json.dumps(
        [compile_card(f()).ir_sha256 for f in (K.venus_vedha_card, K.dasha_card, K.av_card, K.natal_card)]
    )
    assert outs == {local}


def test_ir_carries_no_quote_text():
    card = K.venus_vedha_card()
    r = compile_card(card)
    blob = canonical_json(r.ir).decode("utf-8")
    assert card["field1_citation"]["quote"] not in blob
    assert card["field3_reference_frame"]["frame_citation"]["quote"] not in blob
    assert len(r.ir["citation"]["quote_sha256"]) == 64


def test_member_logic_hash_ignores_operand_names():
    a = K.dasha_card()
    b = json.loads(json.dumps(a).replace('"md"', '"major"').replace('"ad6"', '"x6"').replace('"ad8"', '"x8"'))
    ra, rb = compile_card(a), compile_card(b)
    assert ra.ir_sha256 != rb.ir_sha256
    assert ra.logic_sha256 == rb.logic_sha256


# ── bypass tests ────────────────────────────────────────────────────────────
def _compiled(card):
    r = compile_card(card)
    return r, r.ir, r.gate


def test_testimony_never_increments_n():
    card = K.natal_card()
    card["provenance"] = "commentarial_practice"
    card["commentarial_source"] = {"author": "Synthetic", "work": "Synthetic"}
    r, ir, gate = _compiled(card)
    out = card_outcome(ir, gate, r.exceptions, {"ven_r": T})
    assert out.state is T and out.testimony and not out.increments_n
    t = tally([out], "promotive")
    assert t["categories"]["natal_promise"] == "not_assessed"  # no counted card
    assert t["categories_matched"] == 0
    assert t["testimony_matched_flagged"] == 1


def test_verse_card_increments_n():
    r, ir, gate = _compiled(K.natal_card())
    t = tally([card_outcome(ir, gate, r.exceptions, {"ven_r": T})], "promotive")
    assert t["categories"]["natal_promise"] == "matched" and t["categories_matched"] == 1


def test_quarantined_card_cannot_be_evaluated():
    card = K.natal_card()
    del card["field5_typed_operands"][0]["doctrinal_graha"]
    r, ir, gate = _compiled(card)
    assert ir["status"] == "quarantined_not_evaluable"
    with pytest.raises(QuarantinedCardError):
        card_outcome(ir, gate, r.exceptions, {"ven_r": T})


def test_na_is_never_rendered_false():
    r, ir, gate = _compiled(K.natal_card())
    out = card_outcome(ir, gate, r.exceptions, {})  # missing fact -> NA, not False
    assert out.state is NA
    t = tally([out], "promotive")
    assert t["categories"]["natal_promise"] == "not_assessed"
    assert render_tri(out.state) == "not_assessed"
    with pytest.raises(NotAssessedError):
        bool(out.state)
    assert all(v in ("matched", "not_matched", "not_assessed") for v in t["categories"].values())
    assert t["categories"]["natal_promise"] != "not_matched"


def test_mixed_na_and_false_is_not_matched_and_true_wins():
    base = dict(card_id="x", category="transit", polarity="promotive", increments_n=True, testimony=False)
    outs = [CardOutcome(state=NA, **base), CardOutcome(state=F, **base)]
    assert tally(outs, "promotive")["categories"]["transit"] == "not_matched"
    outs.append(CardOutcome(state=T, **base))
    assert tally(outs, "promotive")["categories"]["transit"] == "matched"


def _with_exception(effect, scope="same_text_only"):
    card = K.venus_vedha_card()
    card["field5_typed_operands"].append(
        {"id": "exc", "role": "transiting_graha", "doctrinal_graha": "guru", "relation": "transits", "bhava": 1}
    )
    card["field6_exceptions"] = [{"condition": {"operand": "exc"}, "effect": effect, "school_scope": scope}]
    r = compile_card(card)
    assert r.status == "active", r.reasons
    return r


@pytest.mark.parametrize(
    "effect,exc_val,state,polarity,increments",
    [
        ("cancels", T, F, "obstructive", True),
        ("cancels", F, T, "obstructive", True),
        ("cancels", NA, NA, "obstructive", True),
        ("reverses_polarity", T, T, "promotive", True),
        ("reverses_polarity", NA, NA, "obstructive", True),
        ("reduces", T, T, "obstructive", False),
        ("delays", T, T, "obstructive", False),
        ("delays", NA, NA, "obstructive", True),
    ],
)
def test_exception_table(effect, exc_val, state, polarity, increments):
    r = _with_exception(effect)
    out = card_outcome(r.ir, r.gate, r.exceptions, {"ven_t": T, "ven_v": T, "exc": exc_val})
    assert (out.state, out.polarity, out.increments_n) == (state, polarity, increments)


def test_reduces_and_delays_are_notes_not_n():
    r = _with_exception("reduces")
    out = card_outcome(r.ir, r.gate, r.exceptions, {"ven_t": T, "ven_v": T, "exc": T})
    t = tally([out], "obstructive")
    assert t["categories"]["transit"] == "not_assessed" and t["categories_matched"] == 0
    assert t["qualified_notes"] == 1
    assert r.ir["exceptions"][0]["increments_n"] is False


def test_false_gate_ignores_na_exception():
    r = _with_exception("cancels")
    out = card_outcome(r.ir, r.gate, r.exceptions, {"ven_t": F, "ven_v": T})
    assert out.state is F


def test_non_default_scope_is_alternate_only():
    r = _with_exception("cancels", scope="kerala")
    out = card_outcome(r.ir, r.gate, r.exceptions, {"ven_t": T, "ven_v": T, "exc": T})
    assert out.state is T and out.notes == ("alternate:kerala:cancels",)


def test_or_requires_verse_disjunction():
    from services.rulebook.ast import Or

    p = Pred("a", "natal_graha", "retrograde", "natal", "janma_lagna", {})
    with pytest.raises(ValueError):
        Or((p,), verse_disjunction=False)
    with pytest.raises(ValueError):
        ExceptionNode(p, "weakens", "same_text_only", (), True)
