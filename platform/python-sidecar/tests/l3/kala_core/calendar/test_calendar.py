from datetime import datetime

import pytest

from services.kala_core.calendar import (
    TARA_BALA_RECONCILIATION_V1,
    TARA_BALA_TABLE_V1,
    assess_tara_bala,
    panchanga_at,
)
from services.ka_muhurta_seva import primitives


BHUBANESWAR = {"lat": 20.27, "lon": 85.84, "tz_offset_minutes": 330}


def test_forensic_birth_primitives_reproduce_all_five_angas():
    value = panchanga_at(datetime(1984, 2, 5, 10, 43), BHUBANESWAR)
    assert (value.tithi_id, value.vara_id, value.nakshatra_id, value.yoga_id, value.karana_id) == (3, 1, 25, 20, 5)


def test_location_is_refused_not_defaulted():
    with pytest.raises(ValueError, match="location is required"):
        panchanga_at(datetime(1984, 2, 5, 10, 43), None)


def test_service_is_a_location_required_calendar_facade():
    value = primitives(datetime(1984, 2, 5, 10, 43), BHUBANESWAR)
    assert value.nakshatra_id == 25


def test_second_cycle_vipat_middle_third_is_not_condemned():
    # Position 12 is second-cycle vipat; 25/60 ghatis is its middle third.
    value = assess_tara_bala(1, 12, elapsed_fraction=25 / 60)
    assert value.status == "auspicious"


def test_second_cycle_vipat_first_third_is_condemned():
    value = assess_tara_bala(1, 12, elapsed_fraction=5 / 60)
    assert value.status == "inauspicious"
    assert value.remedy == "dāna prescribed for Vipat tārā (PG67 v.13)"


@pytest.mark.parametrize(
    ("current_nakshatra_id", "elapsed_fraction", "expected_name", "expected_status"),
    (
        (14, 25 / 60, "pratyari", "inauspicious"),
        (16, 45 / 60, "vadha", "inauspicious"),
        (21, 0.0, "vipat", "auspicious"),
    ),
)
def test_pg67_preserves_second_cycle_thirds_and_makes_the_third_cycle_auspicious(
    current_nakshatra_id, elapsed_fraction, expected_name, expected_status
):
    """Breaks if the second-cycle exceptions or third-cycle release is removed."""
    value = assess_tara_bala(1, current_nakshatra_id, elapsed_fraction=elapsed_fraction)
    assert (value.tara_name, value.status) == (expected_name, expected_status)


def test_adverse_second_cycle_stars_carry_their_own_pg67_remedy():
    pratyari = assess_tara_bala(1, 14, elapsed_fraction=25 / 60)
    vadha = assess_tara_bala(1, 16, elapsed_fraction=45 / 60)
    assert pratyari.remedy == "dāna prescribed for Pratyari tārā (PG67 v.13)"
    assert vadha.remedy == "dāna prescribed for Vadha tārā (PG67 v.13)"


# Each legacy reader returns whether that table treats tārā position 1..27
# (birth star Ashwini, current star = position) as adverse.  The numeric tables
# have no adverse label, so a value below the table's own Janma (neutral)
# value is read as adverse.
def _ka_sangam_adverse(position):
    from services.ka_sangam import engine

    def score(index):
        return engine._tara_score_for_nakshatra(engine._NAKSHATRAS_ORDERED[index], 0)

    return score(position - 1) < score(0)


def _w23_adverse(position):
    from services.gochara_v3.mechanisms import w23_tara_bala

    return w23_tara_bala.compute_tara(position, 1)[1] < w23_tara_bala.compute_tara(1, 1)[1]


def _p6_adverse(position):
    from services.gochara_rules import p6

    return p6.tara(1, position)["class_name"] in {"vipat", "pratyari", "vadha"}


def _panchang_engine_adapter_adverse(position):
    from services.gochara_grammar import primitives

    return primitives.get_tara_detail(primitives.compute_tara_position(1, position))["quality"] == "inauspicious"


LEGACY_READERS = {
    "ka_sangam._TARA_SCORES": _ka_sangam_adverse,
    "gochara_v3.w23_tara_bala": _w23_adverse,
    "gochara_rules.p6": _p6_adverse,
    "gochara_grammar.panchang_engine_adapter": _panchang_engine_adapter_adverse,
}
THIRDS = (5 / 60, 25 / 60, 45 / 60)


def _measured_disagreement(reader):
    return tuple(
        position
        for position in range(1, 28)
        if any(
            reader(position) != (assess_tara_bala(1, position, elapsed_fraction=f).status == "inauspicious")
            for f in THIRDS
        )
    )


def test_every_legacy_table_marks_the_first_cycle_like_pg67():
    """Breaks if a legacy table's own first-cycle classification changes."""
    for source, reader in LEGACY_READERS.items():
        assert tuple(p for p in range(1, 10) if reader(p)) == (3, 5, 7), source


@pytest.mark.parametrize("source", sorted(LEGACY_READERS))
def test_recorded_disagreement_is_the_measured_disagreement(source):
    """Reads the legacy table and PG67 position by position, third by third."""
    measured = _measured_disagreement(LEGACY_READERS[source])
    record = TARA_BALA_RECONCILIATION_V1["disagreements"][source]
    assert record["positions"] == measured
    assert record["description"].startswith(f"disagrees with PG67 v.13 at {len(measured)} of 27 positions")


def test_four_legacy_tables_are_retired_in_favour_of_pg67():
    """Breaks if a legacy tārā table silently becomes an active authority again."""
    import ast
    import inspect

    from services.kala_core.calendar import tara_bala

    assert TARA_BALA_TABLE_V1["locator"] == "PG67:C1 v.13"
    assert TARA_BALA_RECONCILIATION_V1["selected_rule"] == "PG67:C1 v.13"
    assert set(TARA_BALA_RECONCILIATION_V1["retired_sources"]) == set(LEGACY_READERS)
    assert set(TARA_BALA_RECONCILIATION_V1["disagreements"]) == set(LEGACY_READERS)
    imported = {
        alias.name if isinstance(node, ast.Import) else node.module or ""
        for node in ast.walk(ast.parse(inspect.getsource(tara_bala)))
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    legacy_roots = ("services.ka_sangam", "services.gochara_v3", "services.gochara_rules", "services.gochara_grammar", "panchang_engine")
    assert not {name for name in imported if name.startswith(legacy_roots)}
