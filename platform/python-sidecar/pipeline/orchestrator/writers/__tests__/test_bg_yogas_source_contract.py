"""Regression coverage for migration-434 detector yogas in the writer source."""

from brahmagyan.l0_yogas import DETECTOR_YOGAS, YOGAS_CORE


def test_detector_yogas_are_writer_owned_and_identity_disjoint() -> None:
    detector_ids = {yoga["canonical_id"] for yoga in DETECTOR_YOGAS}
    core_ids = {yoga["canonical_id"] for yoga in YOGAS_CORE}

    assert len(YOGAS_CORE) == 144
    assert len(DETECTOR_YOGAS) == 4
    assert detector_ids == {
        "dhana_yoga_house_lords",
        "raja_yoga_kendra_trikona",
        "sarasvati_yoga",
        "vipareeta_raja_yoga",
    }
    assert detector_ids.isdisjoint(core_ids)
