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


def test_a_non_lowercase_body_or_relation_is_refused_not_hashed():
    """IDENTITY_CANONICAL_BYTES_CONTRACT §1 (steward M20261001T223444-51ba): body and
    relation_kind are the STORED lowercase tokens. The frozen v1.4 uppercase vector
    (`Mars|…|c0|1` → 87b023cc-c9f3-…) can no longer be BUILT — the builder refuses the
    spelling instead of minting a second identity for one body."""
    for bad in ("Mars", "MARS", "mArs", ""):
        with pytest.raises(ValueError, match="LOWERCASE"):
            _po("point:198.52", body=bad)
    for bad in ("Conjunction", "SIGN_INGRESS"):
        with pytest.raises(ValueError, match="LOWERCASE"):
            _po("point:198.52", rel=bad)
    lower = SubstrateContact(physical_object_id=_po("point:198.52"),
                             occurrence_ordinal=1, t_exact=T)
    assert str(lower.contact_id) == "23276d7c-c127-8f4c-9ad5-6b7c8da8020f", \
        "the lowercase stand-in-convention vector is unchanged"


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


# ── F-3 §3: the round-trip guard replaces the withdrawn six-decimal rule ─────

from decimal import Decimal  # noqa: E402


@pytest.mark.parametrize("value,expected", [
    (198.52, "point:198.52"),
    (Decimal("198.52"), "point:198.52"),
    (Decimal("198.5200"), "point:198.52"),            # trailing zeros are never written
    ("198.5200", "point:198.52"),
    (Decimal("198.5200001"), "point:198.5200001"),     # NO quantisation: 7 decimals survive
    (360.0, "point:0.0"),                             # wrapped
    (-0.0, "point:0.0"),                              # never '-0.0'
    (1e-05, "point:0.00001"),                         # no exponent
    (Decimal("0.00001"), "point:0.00001"),
])
def test_point_target_renders_the_contract_text(value, expected):
    assert targets.point_target(value) == expected


@pytest.mark.parametrize("value", [
    Decimal("198.52000000000000000001"),    # more digits than a float64 carries
    "0.1234567890123456789",
    Decimal("359.99999999999999999999"),
])
def test_an_l1_numeric_a_float64_cannot_carry_exactly_is_refused_not_quantised(value):
    with pytest.raises(ValueError, match="float64"):
        targets.point_target(value)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), True])
def test_non_finite_or_non_numeric_longitudes_are_refused(value):
    with pytest.raises(ValueError):
        targets.point_target(value)


def test_seven_decimal_neighbours_are_two_different_objects_with_the_real_convention():
    """Contract §10 (computed from this implementation, independently re-derived by Stream B):
    no quantisation, so 198.5200001 and 198.5200004 do not collapse."""
    c = "sha256:eac922d4c3b0deb700112f2260cd250a0388ab159f4a1c4bca9451281a48e7a3"
    a = _po("point:198.5200001", cid=c)
    b = _po("point:198.5200004", cid=c)
    assert str(a.uuid) == "8df1d125-0ca0-8d67-b4b2-5396034fac6d"
    assert str(b.uuid) == "b284f87b-0f3a-83fc-85d8-5810d4df6de5"
    assert a != b


def test_the_contract_vectors_with_the_real_convention_reproduce():
    c = "sha256:eac922d4c3b0deb700112f2260cd250a0388ab159f4a1c4bca9451281a48e7a3"
    po = _po("point:198.52", cid=c)
    assert str(po.uuid) == "21219d8f-5e7e-89b3-ba66-aa5bf6b8c2f9"
    assert str(SubstrateContact(physical_object_id=po, occurrence_ordinal=1,
                                t_exact=T).contact_id) == "37772ce5-a6af-879f-8e6b-d12bebda58b2"
    sp = _po("span:7", rel="residence", cid=c)
    assert str(sp.uuid) == "3506e433-a930-8822-a184-a039e17b84a2"


def test_the_chart_context_names_a_non_float64_exact_l1_fact_instead_of_quantising_it():
    from services.gochara_kernel.chart_context import fetch_chart_context

    class _Rows:
        def __init__(self, rows):
            self._rows = rows

        def fetchall(self):
            return self._rows

    class _Conn:
        def execute(self, sql, params=()):
            return _Rows([("f1", "MAR", Decimal("198.52000000000000000001")),
                          ("f2", "SUN", Decimal("280.25")), ("f3", "LAGNA", Decimal("10.5"))])

    ctx = fetch_chart_context(_Conn(), "chart")
    assert "graha_position:MAR:not_float64_exact" in ctx["operands_missing"]
    assert "Mars" not in ctx["natal"], "a value a float64 cannot carry must not enter the chart"
    assert ctx["natal"]["Sun"] == 280.25
