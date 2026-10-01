"""A5.3 — AM-2 canonical-target grammar (services/gochara_kernel/targets.py) and
the identity builder (GOCHARA_SPECS_V1_5_AMENDMENTS_DRAFT v0.5, O-RX-1a).

Production code under test: `targets.*` and `substrate.PhysicalObjectId` /
`SubstrateContact`. The expected UUIDs are the draft's PINNED vectors
(independently recomputed by stream B and matched by the reviewer), kept as
literals here — never derived from the code being checked."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from services.gochara_kernel import evaluator as ev
from services.gochara_kernel import targets
from services.gochara_kernel.substrate import (PhysicalObjectId,
                                               SubstrateContact,
                                               physical_object_id)

T = datetime(2025, 3, 10, tzinfo=timezone.utc)


def _po(target: str, body: str = "mars", rel: str = "conjunction", cid: str = "c0"):
    return physical_object_id(body=body, relation_kind=rel,
                              canonical_target=target, convention_id=cid)


# ── the grammar ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize("target", [
    *[f"span:{n}" for n in range(1, 13)],
    "point:198.52", "point:0.0", "point:359.99999999999994", "point:0.00001",
    *[f"star:{n}" for n in range(1, 28)],
])
def test_canonical_targets_are_accepted(target):
    assert _po(target).canonical_target == target


@pytest.mark.parametrize("target", [
    "sign:7",          # fails the SQL shape (kgpo_target_form_ck)
    "span:13", "span:0", "span:07", "span:007",     # builder-rejected (SQL admits them)
    "span:libra", "span:Libra",                      # a NAME is a rendering, not identity
    "span:", "span:-1", "span:1.5",
    "point:360", "point:361.5", "point:1e-05", "point:-1", "point:.5", "point:07.5",
    "star:0", "star:28", "star:07",
    "", "libra", "point", "span",
])
def test_non_canonical_targets_cannot_form_an_identity(target):
    with pytest.raises(ValueError, match="non-canonical target"):
        _po(target)
    with pytest.raises(ValueError):
        targets.validate_canonical_target(target)


def test_span_target_renders_the_absolute_sign_numeral():
    assert targets.span_target("Aries") == "span:1"
    assert targets.span_target("libra") == "span:7"       # the shipped fixture's span:7
    assert targets.span_target("Pisces") == "span:12"
    assert targets.span_target(7) == "span:7"
    for bad in ("scorpion", 0, 13, "", True):
        with pytest.raises(ValueError):
            targets.span_target(bad)


def test_span_numeral_round_trips_to_the_sign_name():
    names = ["aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra",
             "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"]
    for i, name in enumerate(names, start=1):
        assert targets.span_sign_index(f"span:{i}") == i
        assert targets.span_sign_name(f"span:{i}") == name
    with pytest.raises(ValueError):
        targets.span_sign_name("span:libra")


def test_point_target_is_full_precision_decimal_with_no_exponent():
    assert targets.point_target(198.52) == "point:198.52"
    assert targets.point_target(180.0) == "point:180.0"
    # repr() would give '1e-05' — an exponent form the 1153 CHECK refuses
    assert targets.point_target(0.00001) == "point:0.00001"
    assert "e" not in targets.point_target(1.2345e-07)
    # λ is wrapped into [0, 360): the seam renders as point:0.0, never 360
    assert targets.point_target(360.0) == "point:0.0"
    assert targets.point_target(-0.5) == "point:359.5"
    # full precision: NO quantization (the draft's F-3 question is not settled here)
    assert targets.point_target(198.5200001) != targets.point_target(198.5200004)
    # every rendering is itself a canonical identity token
    for lam in (0.0, 1e-9, 29.999999999999996, 198.52, 359.99999999999994):
        targets.validate_canonical_target(targets.point_target(lam))


# ── the identity bytes and the pinned UUIDv8 vectors (AM-2) ──────────────────

def test_identity_bytes_are_body_relation_target_convention_ordinal():
    po = _po("point:198.52")
    assert po.identity_bytes == "mars|conjunction|point:198.52|c0"
    c = SubstrateContact(physical_object_id=po, occurrence_ordinal=1, t_exact=T)
    from services.gochara_kernel.substrate import contact_identity_bytes
    assert contact_identity_bytes(c) == "mars|conjunction|point:198.52|c0|1"


@pytest.mark.parametrize("ordinal,uuid", [
    (1, "23276d7c-c127-8f4c-9ad5-6b7c8da8020f"),
    (2, "b6cd1a15-4820-859f-b6e4-d7e144e59416"),
    (3, "c523b443-fcc4-8665-8bfc-52b6e3e831d9"),
    (4, "8e423fdf-6ab5-842a-ab1f-b31d4720d319"),
])
def test_contact_ids_reproduce_the_pinned_uuidv8_vectors(ordinal, uuid):
    c = SubstrateContact(physical_object_id=_po("point:198.52"),
                         occurrence_ordinal=ordinal, t_exact=T)
    assert str(c.contact_id) == uuid


def test_uppercase_body_is_not_the_canonical_identity():
    """The pinned uppercase vector (O-RX-1a: MUST NOT occur) differs from the
    lowercase one — the stored lowercase form is the identity."""
    upper = SubstrateContact(physical_object_id=_po("point:198.52", body="Mars"),
                             occurrence_ordinal=1, t_exact=T)
    assert str(upper.contact_id) == "87b023cc-c9f3-8979-9b37-96701f285356"
    lower = SubstrateContact(physical_object_id=_po("point:198.52"),
                             occurrence_ordinal=1, t_exact=T)
    assert upper.contact_id != lower.contact_id


# ── the evaluator renders the contract's targets ─────────────────────────────

CHART = {
    "lagna_deg": 12.0,
    "natal": {"Sun": 291.0, "Moon": 327.05, "Mars": 15.0, "Mercury": 300.0,
              "Jupiter": 120.0, "Venus": 330.0, "Saturn": 200.0,
              "Rahu": 80.0, "Ketu": 260.0},
}


def test_enumerated_residence_edges_use_absolute_sign_numerals():
    edges = ev.enumerate_edges("marriage", "P3", CHART)
    spans = {e.obj.canonical_target for e in edges
             if e.obj.canonical_target.startswith("span:")}
    assert spans, "marriage/P3 must enumerate residence spans"
    for t in spans:
        targets.span_sign_index(t)                        # canonical numeral
    # marriage's 7th house from the Aries lagna is Libra ⇒ span:7
    assert "span:7" in spans
    assert not any(t.startswith("span:") and not t[5:].isdigit() for t in spans)
