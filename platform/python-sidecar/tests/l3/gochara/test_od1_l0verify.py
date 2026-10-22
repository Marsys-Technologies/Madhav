"""SR-OD1 od1-l0verify — the input-vector verifier derives P1's three L0 digests from its OWN reads.

Claims (one oracle each; the builder is `p1_operands`, the verifier `input_vector_verifier`, which imports nothing from it):
  C1  the verifier's digest of each of `bg_dignity_reference`, `bg_combustion_orbs`, `bg_graha_naisargika_friendship` equals the builder's
      `L0Table.content_digest` over the real L0 seed (migration 250) with migration 1401's Rahu/Ketu node rows applied (SR-1401-VERIFIED).
  C2  a one-row change on the verifier's read (the stored digest is the pre-change one) makes `verify_inputs` DISAGREE, naming the table.
  C3  `verify_inputs` accepts the true vector with all three P1 authorities consumed (no "no independent derivation" refusal).
  C4  an authority the verifier cannot derive is still refused by name.
Normalisation (p1_operands docstring, "L0 DIGESTS"): an array per row in a total order; NUMERIC as `trim_scale(x)::text`; ids/citations/notes
are not consumed.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from services.gochara_kernel import input_vector_verifier as ivv
from services.gochara_kernel import p1_operands as P

from .test_a53_input_vector import _ivv, _vector, db, ephe  # noqa: F401  (the disposable-database fixtures)

MIGRATIONS = Path(__file__).resolve().parents[4] / "migrations"
ASSETS = ("bg_dignity_reference", "bg_combustion_orbs", "bg_graha_naisargika_friendship")

#: one planted one-row change per table, applied to the verifier's read AFTER the build bound its digest
_PLANTS = {
    # Mars' mūlatrikoṇa end degree (BPHS Ch.3): a numeric moves
    "bg_dignity_reference": "UPDATE public.bg_dignity_reference SET moolatrikona_to = moolatrikona_to + 1 WHERE graha = 'Mars'",
    # Saturn's combustion orb (15 -> 16; the OCR-ambiguous reading the 1401 header records as a discrepancy)
    "bg_combustion_orbs": "UPDATE public.bg_combustion_orbs SET orb_degrees = orb_degrees + 1 WHERE graha = 'Saturn'",
    # one natural friendship: Sun -> Moon friend becomes enemy
    "bg_graha_naisargika_friendship": "UPDATE public.bg_graha_naisargika_friendship SET relation = 'enemy'"
                                      " WHERE graha = 'Sun' AND other_graha = 'Moon'",
}


@pytest.fixture()
def l0(db):  # noqa: F811
    db.execute((MIGRATIONS / "250_bg_dignity_reference.sql").read_text(encoding="utf-8"))
    db.execute((MIGRATIONS / "1401_l0_node_dignity_friendship.sql").read_text(encoding="utf-8"))
    return db


def test_c1_the_verifiers_digest_of_each_p1_table_equals_the_builders_over_the_real_seed(l0):
    built = P.load_p1_l0(l0.cursor())
    assert built.digests().keys() == set(ASSETS)
    for asset in ASSETS:
        assert ivv.sql_p1_l0_digest(l0, asset) == built.digests()[asset], asset
    # the node rows are IN the digest (SR-1401-VERIFIED: Rahu moolatrikona Gemini, Ketu Sagittarius)
    assert {r["graha"]: r["moolatrikona_sign"] for r in built.dignity.rows if r["graha"] in ("Rahu", "Ketu")} == {
        "Rahu": "Gemini", "Ketu": "Sagittarius"}


@pytest.mark.parametrize("asset", ASSETS)
def test_c2_a_one_row_change_on_the_verifiers_read_disagrees(l0, ephe, asset):  # noqa: F811
    stored = _vector(l0, ephe, l0_consumed=ASSETS)
    assert stored["l0"] == P.load_p1_l0(l0.cursor()).digests()
    assert _ivv(l0, stored, ephe)["derived"].count("l0") == 1              # the true vector is accepted
    l0.execute(_PLANTS[asset])
    assert ivv.sql_p1_l0_digest(l0, asset) != stored["l0"][asset]
    with pytest.raises(RuntimeError) as exc:
        _ivv(l0, stored, ephe)
    assert f"l0.{asset}" in str(exc.value)
    for other in set(ASSETS) - {asset}:                                      # only the changed table disagrees
        assert f"l0.{other}" not in str(exc.value)


def test_c3_verify_inputs_accepts_the_true_vector_with_all_p1_authorities_consumed(l0, ephe):  # noqa: F811
    stored = _vector(l0, ephe, l0_consumed=ASSETS)
    out = _ivv(l0, stored, ephe)
    assert "l0" in out["derived"]


def test_c4_an_authority_the_verifier_cannot_derive_is_still_refused_by_name(l0, ephe):  # noqa: F811
    stored = _vector(l0, ephe, l0_consumed=ASSETS)
    stored["l0"]["bg_unknown_authority"] = "0" * 64
    with pytest.raises(RuntimeError, match="l0.bg_unknown_authority: no independent derivation"):
        _ivv(l0, stored, ephe)
    with pytest.raises(RuntimeError, match="no independent derivation"):
        ivv.sql_l0_asset_digest(l0, "bg_unknown_authority")


def test_c5_a_numeric_is_one_value_however_many_trailing_zeros_it_carries(l0):
    """`15.0` and `15` are one value (p1_operands: `trim_scale(x)::text`): re-typing the NUMERIC columns with trailing zeros moves neither
    the builder's digest nor the verifier's, and the two still agree."""
    before = {a: ivv.sql_p1_l0_digest(l0, a) for a in ASSETS}
    l0.execute("ALTER TABLE public.bg_combustion_orbs ALTER COLUMN orb_degrees TYPE numeric(6,3), ALTER COLUMN deep_orb_degrees TYPE numeric(6,3)")
    l0.execute("ALTER TABLE public.bg_dignity_reference ALTER COLUMN moolatrikona_from TYPE numeric(6,3),"
               " ALTER COLUMN moolatrikona_to TYPE numeric(6,3)")
    built = P.load_p1_l0(l0.cursor()).digests()
    assert built == before
    assert {a: ivv.sql_p1_l0_digest(l0, a) for a in ASSETS} == before
