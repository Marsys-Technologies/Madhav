"""
test_ir7_ir8_doc_corrections.py — PK-R-9 IR-7 / IR-8 doc-grep detectors
(2026-08-11).

IR-7: correct the engine.py MR-41(c) comment -- `gochara_vedha_pair` is
unreachable on v3 because `_gather_sentences_no_db` calls it with
`conn=None` AND (per IR-4) no caller supplies `moon_sign_idx`, NOT because
of a "v1-parity-mode-only" scoping distinction; and MR-41(b) DOES change
lambda_v3 through the activity term (nakshatra_ingress_tara's tara-state
detection becoming reachable for graha-anchored targets). The false
"deliberately does NOT change v3 scoring semantics" framing (and the
"v1-PARITY-MODE-ONLY" mis-framing of gochara_vedha_pair's unreachability)
must not appear anywhere in the corrected comment.

IR-8: `_gather_sentences_no_db`'s docstring previously said sarvatobhadra_
vedha "reads bg_transit_rules. Same as above" (false -- it reads
`l1_sarvatobhadra_vedha`/`bg_sarvatobhadra_grid`) and "Suppression still
works via sarvatobhadra_vedha" (false on the v3 path -- v3's suppression
mechanism is `quality_gates`). Both retracted phrases must not appear.

Both detectors are doc-grep tests over the live engine.py source, asserting
the retracted phrases are ABSENT (not merely quoted-and-disclaimed) --
matching the ruling's own instruction to "delete" / "correct", not annotate
in place.
"""
from __future__ import annotations

import inspect

from services.gochara_v3 import engine as ENGINE


def _source() -> str:
    return inspect.getsource(ENGINE)


# ── IR-7 ─────────────────────────────────────────────────────────────────

def test_ir7_retracted_scoring_semantics_claim_is_absent():
    src = _source()
    assert "deliberately does NOT change v3 scoring semantics" not in src
    # Any phrasing variant asserting MR-41 left v3 scoring untouched is the
    # same retracted claim -- checked as a normalized substring too.
    assert "does not change v3 scoring semantics" not in src.lower()


def test_ir7_retracted_parity_mode_only_framing_is_absent():
    """The ALL-CAPS "v1-PARITY-MODE-ONLY" framing (the retracted claim that
    `gochara_vedha_pair`'s v3-unreachability was itself a parity-mode
    scoping fact -- i.e. asserted as the reason, not negated) must be gone.
    Lowercase "v1-parity-mode-only" is NOT banned outright -- it still
    correctly describes `compute_suppression` itself (genuinely
    parity-mode-scoped, an unretracted, true statement), and the CORRECTED
    comment explicitly NEGATES the retracted framing for gochara_vedha_pair
    ("this is not a v1-parity-mode-only gap") -- a substring check on the
    negated phrase would false-positive on that correct sentence, so this
    test targets only the unambiguous ALL-CAPS form the retracted version
    used."""
    src = _source()
    assert "v1-PARITY-MODE-ONLY" not in src


def test_ir7_gochara_vedha_pair_unreachability_names_conn_none_and_moon_sign_idx():
    """The CORRECTED framing (IR-7) must be present: gochara_vedha_pair's
    v3-unreachability is attributed to conn=None (v3's zero-per-JD-DB-access
    design) AND the IR-4 moon_sign_idx gate, not to parity-mode scoping."""
    src = _source()
    assert "conn=None" in src
    assert "moon_sign_idx" in src
    # The corrected wiring-decision comment block itself.
    assert "PK-R-9 CORRECTION" in src


def test_ir7_mr41b_activity_term_impact_is_named():
    """The CORRECTED framing must positively state that MR-41(b) changes
    lambda_v3 through the activity term (not just retract the false claim)."""
    src = _source()
    assert "DOES change" in src or "does change" in src.lower()
    assert "activity" in src.lower()
    assert "orb_decay=0.5" in src or "orb_decay = 0.5" in src


# ── IR-8 ─────────────────────────────────────────────────────────────────

def test_ir8_retracted_sarvatobhadra_source_claim_is_absent():
    src = _source()
    assert "reads bg_transit_rules. Same as above" not in src


def test_ir8_retracted_suppression_still_works_claim_is_absent():
    src = _source()
    assert "Suppression still works via sarvatobhadra_vedha" not in src


def test_ir8_gather_sentences_no_db_names_correct_sarvatobhadra_source():
    """The CORRECTED docstring must name sarvatobhadra_vedha's REAL DB
    sources (l1_sarvatobhadra_vedha / bg_sarvatobhadra_grid), not
    bg_transit_rules."""
    src = inspect.getsource(ENGINE._gather_sentences_no_db)
    assert "l1_sarvatobhadra_vedha" in src or "bg_sarvatobhadra_grid" in src
    assert "quality_gates" in src  # names the REAL v3 suppression mechanism instead
