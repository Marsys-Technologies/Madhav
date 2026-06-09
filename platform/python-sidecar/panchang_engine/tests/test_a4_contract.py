"""
A4 contract acceptance tests for panchanga_instant.

Verifies that the rich output contract is fully populated at the engine level
(the layer that feeds A4 / ga_panchanga chart asset storage).

Brief §5 requirement: rebuild A4 for the native (birth instant + coords) and
assert that the stored topic-count == the instant contract's populated-topic-count.
"""
import json
import pytest
from datetime import datetime

from panchang_engine import panchanga_instant
from panchang_engine.serialize import panchanga_instant_to_dict

# FORENSIC native: 1984-02-05 10:43 IST, Bhubaneswar (20.27°N, 85.84°E)
BIRTH = datetime(1984, 2, 5, 10, 43)
LAT, LON, TZ = 20.27, 85.84, 330


@pytest.fixture(scope="module")
def native_instant():
    return panchanga_instant(BIRTH, LAT, LON, TZ)


@pytest.fixture(scope="module")
def native_dict(native_instant):
    return panchanga_instant_to_dict(native_instant)


class TestForensicGate:
    """Core FORENSIC gate — angas match known ephemeris for 1984-02-05 10:43 IST."""

    def test_tithi_shukla_tritiya(self, native_instant):
        assert "Tritiya" in native_instant.tithi.name

    def test_nakshatra_purva_bhadrapada(self, native_instant):
        assert "Bhadra" in native_instant.nakshatra.name

    def test_vara_ravivara(self, native_instant):
        assert "Ravi" in native_instant.vara.name

    def test_lagna_mesha(self, native_instant):
        assert native_instant.lagna is not None
        assert native_instant.lagna.ascendant_sign_id == 1
        assert "Mesha" in native_instant.lagna.ascendant_sign_name


class TestTopicCoverage:
    """topics_computed reflects what was actually computed — A4 contract completeness."""

    def test_minimum_18_topics(self, native_instant):
        assert len(native_instant.topics_computed) >= 18

    def test_core_angas_in_topics(self, native_instant):
        assert "angas" in native_instant.topics_computed

    def test_planets_in_topics(self, native_instant):
        assert "planets" in native_instant.topics_computed

    def test_lagna_in_topics(self, native_instant):
        assert "lagna" in native_instant.topics_computed

    def test_upagrahas_in_topics(self, native_instant):
        assert "upagrahas" in native_instant.topics_computed

    def test_outer_planets_in_topics(self, native_instant):
        assert "outer_planets" in native_instant.topics_computed

    def test_sun_moon_in_topics(self, native_instant):
        assert "sun_moon" in native_instant.topics_computed

    def test_inauspicious_in_topics(self, native_instant):
        assert "inauspicious_full" in native_instant.topics_computed

    def test_auspicious_in_topics(self, native_instant):
        assert "auspicious_full" in native_instant.topics_computed

    def test_anandadi_yoga_in_topics(self, native_instant):
        assert "anandadi_yoga" in native_instant.topics_computed

    def test_calendrical_in_topics(self, native_instant):
        assert "calendrical" in native_instant.topics_computed

    def test_homa_windows_in_topics(self, native_instant):
        assert "homa_windows" in native_instant.topics_computed

    def test_shoonya_in_topics(self, native_instant):
        assert "shoonya" in native_instant.topics_computed

    def test_micro_timing_in_topics(self, native_instant):
        assert "micro_timing" in native_instant.topics_computed


class TestRichFieldsPopulated:
    """All rich Optional fields are non-None for the native birth instant."""

    def test_lagna_present(self, native_instant):
        assert native_instant.lagna is not None

    def test_lagna_has_12_cusps(self, native_instant):
        assert len(native_instant.lagna.house_cusps) == 12

    def test_lagna_sign_id_is_positive(self, native_instant):
        assert native_instant.lagna.ascendant_sign_id > 0

    def test_upagrahas_count(self, native_instant):
        assert native_instant.upagrahas is not None
        assert len(native_instant.upagrahas) == 8

    def test_outer_planets_count(self, native_instant):
        assert native_instant.outer_planets is not None
        assert len(native_instant.outer_planets) == 3

    def test_sun_moon_dynamics_present(self, native_instant):
        assert native_instant.sun_moon is not None

    def test_inauspicious_windows_nonempty(self, native_instant):
        assert native_instant.inauspicious_full is not None
        assert len(native_instant.inauspicious_full) > 0

    def test_auspicious_windows_nonempty(self, native_instant):
        assert native_instant.auspicious_full is not None
        assert len(native_instant.auspicious_full) > 0

    def test_anandadi_yoga_present(self, native_instant):
        assert native_instant.anandadi_yoga is not None
        assert native_instant.anandadi_yoga.yoga_name is not None

    def test_vasa_present(self, native_instant):
        assert native_instant.vasa is not None

    def test_calendrical_present(self, native_instant):
        assert native_instant.calendrical is not None
        assert native_instant.calendrical.vikram_samvat is not None

    def test_shoonya_present(self, native_instant):
        assert native_instant.shoonya is not None

    def test_homa_windows_nonempty(self, native_instant):
        assert native_instant.homa_windows is not None
        assert len(native_instant.homa_windows) > 0

    def test_window_membership_present(self, native_instant):
        assert native_instant.window_membership is not None

    def test_micro_timing_present(self, native_instant):
        assert native_instant.micro_timing is not None


class TestA4Contract:
    """
    A4 storage contract: JSON-serializable, topic count 1:1 preserved.

    Brief §5: "assert the stored topic-count == the instant contract's
    populated-topic-count."
    """

    def test_instant_to_dict_is_json_serializable(self, native_dict):
        """No TypeError/ValueError — entire output serializes cleanly."""
        s = json.dumps(native_dict)
        assert len(s) > 0

    def test_dict_topics_match_instant_topics(self, native_instant, native_dict):
        """dict['topics_computed'] == instant.topics_computed — no topic dropped."""
        assert native_dict["topics_computed"] == native_instant.topics_computed

    def test_dict_topic_count_matches(self, native_instant, native_dict):
        """1:1 count parity: A4 stores exactly the topics that were computed."""
        assert len(native_dict["topics_computed"]) == len(native_instant.topics_computed)

    def test_dict_lagna_present(self, native_dict):
        assert native_dict.get("lagna") is not None
        assert native_dict["lagna"]["ascendant_sign_name"] is not None

    def test_dict_upagrahas_serialized(self, native_dict):
        assert len(native_dict.get("upagrahas", [])) == 8

    def test_dict_no_datetime_objects(self, native_dict):
        """Recurse to ensure no raw datetime objects leak into the serialized dict."""
        from datetime import datetime as dt_type

        def _has_raw_datetime(obj):
            if isinstance(obj, dt_type):
                return True
            if isinstance(obj, dict):
                return any(_has_raw_datetime(v) for v in obj.values())
            if isinstance(obj, list):
                return any(_has_raw_datetime(v) for v in obj)
            return False

        assert not _has_raw_datetime(native_dict), \
            "Raw datetime found in serialized output — A4 storage would fail"

    def test_dict_lagna_sign_matches_forensic(self, native_dict):
        """Serialized Lagna sign must match FORENSIC gate (Mesha, id=1)."""
        assert native_dict["lagna"]["ascendant_sign_id"] == 1
        assert "Mesha" in native_dict["lagna"]["ascendant_sign_name"]
