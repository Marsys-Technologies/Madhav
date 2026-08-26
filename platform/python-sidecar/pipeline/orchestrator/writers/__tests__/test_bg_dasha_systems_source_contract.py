"""Regression coverage for the complete governed dasha source."""

from brahmagyan.l0_dasha_systems import DASHA_SYSTEMS


def test_kp_is_writer_owned_and_source_identities_are_unique() -> None:
    identities = [system["canonical_id"] for system in DASHA_SYSTEMS]

    assert len(identities) == 20
    assert len(set(identities)) == 20
    assert "kp" in identities
    assert "chara_jaimini" in identities
    assert "jaimini_chara" not in identities
