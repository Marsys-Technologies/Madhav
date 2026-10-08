from datetime import datetime

import pytest

from services.kala_core.calendar import TARA_BALA_TABLE_V1, assess_tara_bala, panchanga_at
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


def test_one_pg67_table_retires_the_legacy_score_models():
    assert TARA_BALA_TABLE_V1["locator"] == "PG67:C1 v.13"
    assert "score" not in TARA_BALA_TABLE_V1["rule"]
    assert len(TARA_BALA_TABLE_V1["retired_models"]) == 3
