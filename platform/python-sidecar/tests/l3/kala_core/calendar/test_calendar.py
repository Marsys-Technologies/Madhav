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


def test_four_legacy_tables_are_reconciled_and_retired_in_favour_of_pg67():
    """Breaks if a legacy tārā table silently becomes an active authority again."""
    assert TARA_BALA_TABLE_V1["locator"] == "PG67:C1 v.13"
    assert TARA_BALA_RECONCILIATION_V1["selected_rule"] == "PG67:C1 v.13"
    assert set(TARA_BALA_RECONCILIATION_V1["retired_sources"]) == {
        "ka_sangam._TARA_SCORES",
        "gochara_v3.w23_tara_bala",
        "gochara_rules.p6",
        "gochara_grammar.panchang_engine_adapter",
    }
    assert set(TARA_BALA_RECONCILIATION_V1["disagreements"]) == set(
        TARA_BALA_RECONCILIATION_V1["retired_sources"]
    )
