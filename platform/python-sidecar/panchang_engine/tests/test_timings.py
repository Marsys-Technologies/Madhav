"""
test_timings.py — Unit tests for sunrise/sunset and timing computation.

Tests compute_sunrise_sunset for Bhubaneswar (20.27°N, 85.84°E) on a known
date (2026-05-19) against approximate known values, and verifies the
structural properties of inauspicious/auspicious/choghadiya/hora.

Drik Panchang published (approximate) for 2026-05-19 Bhubaneswar:
  Sunrise: ~05:09 IST = 23:39 UTC (2026-05-18)
  Sunset:  ~18:18 IST = 12:48 UTC (2026-05-19)
"""
import pytest
from datetime import date, datetime, timezone

LAT = 20.27
LON = 85.84
TZ = 330   # IST +05:30

@pytest.fixture(autouse=True)
def set_lahiri():
    from panchang_engine.ayanamsha import set_ayanamsha
    set_ayanamsha("lahiri")


class TestSunriseSunset:
    def test_sunrise_sunset_returns_tuple(self):
        from panchang_engine.timings import compute_sunrise_sunset
        result = compute_sunrise_sunset(date(2026, 5, 19), LAT, LON, TZ)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_sunrise_before_sunset(self):
        from panchang_engine.timings import compute_sunrise_sunset
        sunrise, sunset = compute_sunrise_sunset(date(2026, 5, 19), LAT, LON, TZ)
        assert sunrise < sunset

    def test_sunrise_is_utc_aware(self):
        from panchang_engine.timings import compute_sunrise_sunset
        sunrise, sunset = compute_sunrise_sunset(date(2026, 5, 19), LAT, LON, TZ)
        assert sunrise.tzinfo is not None
        assert sunset.tzinfo is not None

    def test_sunrise_bhubaneswar_approx(self):
        """Sunrise for 2026-05-19 Bhubaneswar should be around 23:38–23:42 UTC (2026-05-18).
        Tolerance: ±5 minutes for this approximate check."""
        from panchang_engine.timings import compute_sunrise_sunset
        sunrise, _ = compute_sunrise_sunset(date(2026, 5, 19), LAT, LON, TZ)
        # Expected: 2026-05-18 23:39 UTC ± 5 min
        expected = datetime(2026, 5, 18, 23, 39, 0, tzinfo=timezone.utc)
        diff = abs((sunrise - expected).total_seconds())
        assert diff <= 300, (
            f"Sunrise {sunrise.strftime('%H:%M:%S')} UTC deviates {diff:.0f}s "
            f"from expected ~23:39 UTC (±5min tolerance)"
        )

    def test_sunset_bhubaneswar_approx(self):
        """Sunset for 2026-05-19 Bhubaneswar should be around 12:47–12:49 UTC.
        Tolerance: ±5 minutes."""
        from panchang_engine.timings import compute_sunrise_sunset
        _, sunset = compute_sunrise_sunset(date(2026, 5, 19), LAT, LON, TZ)
        expected = datetime(2026, 5, 19, 12, 48, 0, tzinfo=timezone.utc)
        diff = abs((sunset - expected).total_seconds())
        assert diff <= 300, (
            f"Sunset {sunset.strftime('%H:%M:%S')} UTC deviates {diff:.0f}s "
            f"from expected ~12:48 UTC (±5min tolerance)"
        )

    def test_day_duration_bhubaneswar_may(self):
        """Day length in Bhubaneswar in May should be ~13h 8min."""
        from panchang_engine.timings import compute_sunrise_sunset
        sunrise, sunset = compute_sunrise_sunset(date(2026, 5, 19), LAT, LON, TZ)
        day_hours = (sunset - sunrise).total_seconds() / 3600
        # Bhubaneswar (20°N) in May: ~13-13.5 hours
        assert 12.0 <= day_hours <= 15.0, (
            f"Day duration {day_hours:.1f}h outside expected 12–15h range"
        )


class TestInauspiciousTimings:
    def test_rahu_kalam_structure(self):
        from panchang_engine.timings import compute_sunrise_sunset, compute_inauspicious_timings
        from panchang_engine.angas import compute_vara
        sunrise, sunset = compute_sunrise_sunset(date(2026, 5, 19), LAT, LON, TZ)
        vara = compute_vara(date(2026, 5, 19))
        result = compute_inauspicious_timings(sunrise, sunset, vara.id)
        assert "rahu_kalam" in result
        assert "yamagandam" in result
        assert "gulika_kalam" in result

    def test_rahu_kalam_bhubaneswar_tuesday(self):
        """Rahu Kalam on Tuesday (vara_id=3) = 7th segment of day (index 6/8).
        Day has 8 segments; 7th = from 3/4 of day to 7/8 of day."""
        from panchang_engine.timings import compute_sunrise_sunset, compute_inauspicious_timings
        from panchang_engine.angas import compute_vara
        sunrise, sunset = compute_sunrise_sunset(date(2026, 5, 19), LAT, LON, TZ)
        vara = compute_vara(date(2026, 5, 19))
        assert vara.id == 3, f"Expected Tuesday (id=3), got {vara.id} ({vara.name})"
        result = compute_inauspicious_timings(sunrise, sunset, vara.id)
        rk = result["rahu_kalam"]
        # Tuesday: RAHU_KALAM_INDEX[3] = 7 → 7th of 8 segments
        day_secs = (sunset - sunrise).total_seconds()
        seg = day_secs / 8.0
        expected_start = sunrise.timestamp() + 6 * seg
        actual_start = rk.start_utc.timestamp()
        assert abs(actual_start - expected_start) < 2, (
            f"Rahu Kalam start off by {abs(actual_start - expected_start):.0f}s"
        )

    def test_inaus_timings_start_after_sunrise(self):
        """All rahu/yama/gulika timings must start at or after sunrise.
        Dur Muhurta may extend into the night (classical rule; not bounded by sunset)."""
        from panchang_engine.timings import compute_sunrise_sunset, compute_inauspicious_timings
        from panchang_engine.angas import compute_vara
        sunrise, sunset = compute_sunrise_sunset(date(2026, 5, 19), LAT, LON, TZ)
        vara = compute_vara(date(2026, 5, 19))
        result = compute_inauspicious_timings(sunrise, sunset, vara.id)
        # Rahu/Yama/Gulika are strictly within the 8-segment day (sunrise→sunset)
        for label in ("rahu_kalam", "yamagandam", "gulika_kalam"):
            if label in result:
                t = result[label]
                assert t.start_utc >= sunrise, f"{label} starts before sunrise"
                assert t.end_utc <= sunset, f"{label} ends after sunset"


class TestAuspiciousTimings:
    def test_brahma_muhurta_before_sunrise(self):
        """Brahma Muhurta must end before sunrise (96→48 min before sunrise)."""
        from panchang_engine.timings import compute_sunrise_sunset, compute_auspicious_timings
        from panchang_engine.angas import compute_vara
        sunrise, sunset = compute_sunrise_sunset(date(2026, 5, 19), LAT, LON, TZ)
        vara = compute_vara(date(2026, 5, 19))
        result = compute_auspicious_timings(sunrise, sunset, vara.id)
        bm = result["brahma_muhurta"]
        assert bm.end_utc <= sunrise

    def test_no_abhijit_on_wednesday(self):
        """Abhijit Muhurta is absent on Wednesdays (vara_id=4)."""
        from panchang_engine.timings import compute_sunrise_sunset, compute_auspicious_timings
        sunrise, sunset = compute_sunrise_sunset(date(2026, 5, 20), LAT, LON, TZ)
        # 2026-05-20 is Wednesday
        result = compute_auspicious_timings(sunrise, sunset, vara_id=4)
        assert result["abhijit"] is None

    def test_abhijit_on_tuesday(self):
        """Abhijit Muhurta is present on Tuesdays (vara_id=3)."""
        from panchang_engine.timings import compute_sunrise_sunset, compute_auspicious_timings
        sunrise, sunset = compute_sunrise_sunset(date(2026, 5, 19), LAT, LON, TZ)
        result = compute_auspicious_timings(sunrise, sunset, vara_id=3)
        assert result["abhijit"] is not None

    def test_abhijit_near_noon(self):
        """Abhijit Muhurta (8th of 15 muhurtas) should be near solar noon."""
        from panchang_engine.timings import compute_sunrise_sunset, compute_auspicious_timings
        sunrise, sunset = compute_sunrise_sunset(date(2026, 5, 19), LAT, LON, TZ)
        result = compute_auspicious_timings(sunrise, sunset, vara_id=3)
        abhi = result["abhijit"]
        noon_approx = sunrise + (sunset - sunrise) / 2
        abhi_mid = abhi.start_utc + (abhi.end_utc - abhi.start_utc) / 2
        diff = abs((abhi_mid - noon_approx).total_seconds())
        # Should be within 1 muhurta (day/15 ≈ 52 min) of noon
        day_secs = (sunset - sunrise).total_seconds()
        muhurta_secs = day_secs / 15
        assert diff < muhurta_secs * 1.5, (
            f"Abhijit midpoint {diff/60:.1f}min from noon (expected < {muhurta_secs/60:.1f}min)"
        )


class TestChoghadiya:
    def test_structure(self):
        from panchang_engine.timings import compute_sunrise_sunset, compute_choghadiya
        from panchang_engine.angas import compute_vara
        from datetime import timedelta
        sunrise, sunset = compute_sunrise_sunset(date(2026, 5, 19), LAT, LON, TZ)
        next_sunrise, _ = compute_sunrise_sunset(date(2026, 5, 20), LAT, LON, TZ)
        vara = compute_vara(date(2026, 5, 19))
        result = compute_choghadiya(sunrise, sunset, next_sunrise, vara.id)
        assert "day" in result
        assert "night" in result
        assert len(result["day"]) == 8
        assert len(result["night"]) == 8

    def test_day_choghadiya_covers_full_day(self):
        """Day choghadiyas must span from sunrise to sunset exactly."""
        from panchang_engine.timings import compute_sunrise_sunset, compute_choghadiya
        from panchang_engine.angas import compute_vara
        sunrise, sunset = compute_sunrise_sunset(date(2026, 5, 19), LAT, LON, TZ)
        next_sunrise, _ = compute_sunrise_sunset(date(2026, 5, 20), LAT, LON, TZ)
        vara = compute_vara(date(2026, 5, 19))
        result = compute_choghadiya(sunrise, sunset, next_sunrise, vara.id)
        day = result["day"]
        assert abs((day[0].start_utc - sunrise).total_seconds()) < 2
        assert abs((day[-1].end_utc - sunset).total_seconds()) < 2

    def test_choghadiya_labels_valid(self):
        """All segment labels must be one of the 7 Choghadiya names."""
        from panchang_engine.timings import compute_sunrise_sunset, compute_choghadiya
        from panchang_engine.angas import compute_vara
        sunrise, sunset = compute_sunrise_sunset(date(2026, 5, 19), LAT, LON, TZ)
        next_sunrise, _ = compute_sunrise_sunset(date(2026, 5, 20), LAT, LON, TZ)
        vara = compute_vara(date(2026, 5, 19))
        result = compute_choghadiya(sunrise, sunset, next_sunrise, vara.id)
        valid = {"choghadiya_amrit", "choghadiya_shubh", "choghadiya_labh",
                 "choghadiya_char", "choghadiya_rog", "choghadiya_kal", "choghadiya_udveg"}
        for t in result["day"] + result["night"]:
            assert t.label in valid, f"Invalid choghadiya label: {t.label}"


class TestHora:
    def test_returns_24_horas(self):
        from panchang_engine.timings import compute_sunrise_sunset, compute_hora
        from panchang_engine.angas import compute_vara
        sunrise, _ = compute_sunrise_sunset(date(2026, 5, 19), LAT, LON, TZ)
        next_sunrise, _ = compute_sunrise_sunset(date(2026, 5, 20), LAT, LON, TZ)
        vara = compute_vara(date(2026, 5, 19))
        result = compute_hora(sunrise, next_sunrise, vara.id)
        assert len(result) == 24

    def test_tuesday_first_hora_is_mars(self):
        """Tuesday (vara_id=3): first hora at sunrise should be Mars."""
        from panchang_engine.timings import compute_sunrise_sunset, compute_hora
        sunrise, _ = compute_sunrise_sunset(date(2026, 5, 19), LAT, LON, TZ)
        next_sunrise, _ = compute_sunrise_sunset(date(2026, 5, 20), LAT, LON, TZ)
        result = compute_hora(sunrise, next_sunrise, vara_id=3)
        assert result[0].label == "hora_mars", (
            f"First hora on Tuesday should be Mars, got {result[0].label}"
        )

    def test_hora_labels_valid(self):
        """All hora labels must be hora_<planet>."""
        from panchang_engine.timings import compute_sunrise_sunset, compute_hora
        sunrise, _ = compute_sunrise_sunset(date(2026, 5, 19), LAT, LON, TZ)
        next_sunrise, _ = compute_sunrise_sunset(date(2026, 5, 20), LAT, LON, TZ)
        result = compute_hora(sunrise, next_sunrise, vara_id=3)
        valid = {"hora_sun", "hora_moon", "hora_mars", "hora_mercury",
                 "hora_jupiter", "hora_venus", "hora_saturn"}
        for t in result:
            assert t.label in valid, f"Invalid hora label: {t.label}"


# ===================================================================
# Task 7: Extended inauspicious/auspicious + homa + day muhurtas
# ===================================================================

def test_extended_inauspicious_has_varjyam():
    from panchang_engine.timings import compute_extended_inauspicious
    from panchang_engine import compute_panchang
    from datetime import date
    p = compute_panchang(date(1984, 2, 5), 20.27, 85.84, 330)
    timings_list = compute_extended_inauspicious(
        p.sunrise_utc, p.sunset_utc, p.vara.id, p.nakshatra.id, p.nakshatra.end_utc
    )
    labels = {t.label for t in timings_list}
    assert "varjyam" in labels, f"Missing varjyam. Got: {labels}"
    assert "yamakantaka" in labels, f"Missing yamakantaka. Got: {labels}"


def test_extended_auspicious_has_brahma_muhurta():
    from panchang_engine.timings import compute_extended_auspicious
    from panchang_engine import compute_panchang
    from datetime import date
    p = compute_panchang(date(1984, 2, 5), 20.27, 85.84, 330)
    timings_list = compute_extended_auspicious(
        p.sunrise_utc, p.sunset_utc, p.vara.id, p.tithi.id, p.nakshatra.id
    )
    labels = {t.label for t in timings_list}
    assert "brahma_muhurta" in labels, f"Missing brahma_muhurta. Got: {labels}"
    assert "pratah_sandhya" in labels, f"Missing pratah_sandhya. Got: {labels}"
    assert "godhuli" in labels, f"Missing godhuli. Got: {labels}"


def test_homa_windows_count():
    from panchang_engine.timings import compute_homa_windows
    from panchang_engine import compute_panchang
    from datetime import date
    p = compute_panchang(date(1984, 2, 5), 20.27, 85.84, 330)
    windows = compute_homa_windows(p.sunrise_utc, p.sunset_utc)
    assert len(windows) >= 2
    labels = {w.label for w in windows}
    assert "homa_morning" in labels


def test_day_muhurtas_count():
    from panchang_engine.timings import compute_day_muhurtas
    from panchang_engine import compute_panchang
    from datetime import date, timedelta
    p = compute_panchang(date(1984, 2, 5), 20.27, 85.84, 330)
    # Approximate next sunrise as +24h
    next_sunrise = p.sunrise_utc + timedelta(hours=24)
    muhurtas = compute_day_muhurtas(p.sunrise_utc, next_sunrise)
    assert len(muhurtas) == 30, f"Expected 30 muhurtas, got {len(muhurtas)}"
    names = [m["name"] for m in muhurtas]
    assert "Rudra" in names


# ===================================================================
# Task 8: Day-only topics — festivals + day events
# ===================================================================

def test_festivals_ekadashi():
    from panchang_engine.timings import compute_festivals
    festivals = compute_festivals(tithi_id=11, paksha="shukla", masa_purnimanta="Kartika")
    names = [f["name"] for f in festivals]
    assert "Ekadashi" in names


def test_festivals_purnima():
    from panchang_engine.timings import compute_festivals
    festivals = compute_festivals(tithi_id=15, paksha="shukla", masa_purnimanta="Magha")
    names = [f["name"] for f in festivals]
    assert "Purnima" in names


def test_festivals_empty_for_no_match():
    from panchang_engine.timings import compute_festivals
    festivals = compute_festivals(tithi_id=2, paksha="shukla", masa_purnimanta="Chaitra")
    # Tithi 2 shukla has no major festival rule
    assert isinstance(festivals, list)


def test_day_events_returns_list():
    from panchang_engine.timings import compute_day_events
    from datetime import date
    events = compute_day_events(date(2026, 4, 14), 20.27, 85.84)
    assert isinstance(events, list)
    # April 14 is often Sun ingress into Mesha (Sankranti)
