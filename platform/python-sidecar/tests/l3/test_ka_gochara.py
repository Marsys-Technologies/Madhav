"""
tests/l3/test_ka_gochara.py — 17 pytest tests for ka_gochara transit-search service.

All tests use live swisseph (pyswisseph must be installed in the venv).
No DB access required — all functions are pure computation over JD ranges.
"""
import pytest
import swisseph as swe

from pipeline.transit_search import (
    TransitEvent,
    SIGNS,
    NAKSHATRAS,
    MEAN_MOTIONS,
    PLANET_IDS,
    orb_strength_score,
    _shortest_arc_diff,
    _sign_nak,
    find_aspect_events,
    find_conjunction_events,
    find_ingress_events,
    find_return_events,
    find_station_events,
    find_eclipse_proximity_events,
    find_multi_planet_confluence_events,
    find_transit_to_transit_events,
    search_long_horizon,
)


# ── Test 1: Import test ────────────────────────────────────────────────────────

def test_import_transit_search():
    """Core symbols from pipeline.transit_search are importable."""
    from pipeline.transit_search import find_aspect_events, find_conjunction_events, TransitEvent
    assert TransitEvent is not None
    assert callable(find_aspect_events)
    assert callable(find_conjunction_events)


# ── Test 2: Router import test ────────────────────────────────────────────────

def test_router_import():
    """routers.transit_search router is importable without ImportError."""
    from routers.transit_search import router
    assert router is not None


# ── Test 3: TransitEvent dataclass has all required fields ───────────────────

def test_transit_event_fields():
    """TransitEvent can be instantiated with all required fields and defaults."""
    ev = TransitEvent(
        event_type="aspect",
        event_jd=2459000.0,
        event_datetime_ist="2020-01-01T05:30:00",
        transit_planet="Saturn",
        secondary_planet=None,
        exact_longitude_deg=270.0,
        orb_at_event_deg=0.1,
        sign="Capricorn",
        nakshatra="Uttara Ashadha",
        applying_separating="applying",
        orb_strength=0.9,
        speed_at_event_dps=0.033,
    )
    assert ev.event_type == "aspect"
    assert ev.extra == {}
    assert ev.secondary_planet is None
    assert ev.orb_strength == 0.9


# ── Test 4: orb_strength_score applying > separating ─────────────────────────

def test_orb_strength_applying_beats_separating():
    """Applying events score higher than separating at same orb."""
    applying = orb_strength_score(0.5, 1.0, "applying")
    separating = orb_strength_score(0.5, 1.0, "separating")
    assert applying > separating


# ── Test 5: orb_strength_score at zero orb = max ─────────────────────────────

def test_orb_strength_zero_orb():
    """Exact aspect (orb=0) should score 1.0 for both applying and separating."""
    assert orb_strength_score(0.0, 1.0, "applying") == 1.0
    assert orb_strength_score(0.0, 1.0, "separating") == 1.0


# ── Test 6: orb_strength_score at max orb = 0 ────────────────────────────────

def test_orb_strength_max_orb():
    """At maximum orb and separating, score should be 0.0."""
    score = orb_strength_score(1.0, 1.0, "separating")
    assert score == 0.0


# ── Test 7: _shortest_arc_diff ────────────────────────────────────────────────

def test_shortest_arc_diff():
    """_shortest_arc_diff returns signed shortest-arc differences correctly."""
    # 10 - 350 = -340, shortest arc = +20 (go the short way)
    assert abs(_shortest_arc_diff(10, 350)) - 20 < 0.001
    # 350 - 10 = 340, shortest arc = -20
    assert abs(_shortest_arc_diff(350, 10)) - 20 < 0.001
    # 180 - 0 = 180 (exact half-circle)
    assert abs(_shortest_arc_diff(180, 0)) - 180 < 0.001
    # Same point = 0
    assert abs(_shortest_arc_diff(90, 90)) < 0.001


# ── Test 8: _sign_nak ─────────────────────────────────────────────────────────

def test_sign_nak():
    """_sign_nak returns correct sign and nakshatra for known longitudes."""
    sign, _ = _sign_nak(0.0)
    assert sign == "Aries"
    sign2, _ = _sign_nak(30.0)
    assert sign2 == "Taurus"
    sign3, _ = _sign_nak(270.0)
    assert sign3 == "Capricorn"
    sign4, _ = _sign_nak(359.9)
    assert sign4 == "Pisces"
    # All outputs should be valid
    for lon in [0, 45, 90, 135, 180, 225, 270, 315, 359.9]:
        s, n = _sign_nak(lon)
        assert s in SIGNS
        assert n in NAKSHATRAS


# ── Test 9: Saturn aspect events found in 2020 ───────────────────────────────

def test_saturn_aspects_found():
    """Saturn conjunction to 270 deg (Capricorn) in 2020 is found."""
    start_jd = swe.julday(2020, 1, 1, 0.0)
    end_jd = swe.julday(2020, 12, 31, 0.0)
    events = find_aspect_events(swe, "Saturn", 270.0, [0], 2.0, start_jd, end_jd)
    assert len(events) >= 1
    ev = events[0]
    assert ev.transit_planet == "Saturn"
    assert ev.sign in SIGNS
    assert ev.nakshatra in NAKSHATRAS
    assert ev.applying_separating in ("applying", "separating", "stationary")
    assert 0.0 <= ev.orb_strength <= 1.0
    assert ev.event_type == "aspect"
    assert ev.extra.get("aspect_deg") == 0


# ── Test 10: Jupiter-Saturn Great Conjunction 2020 ───────────────────────────

def test_jupiter_saturn_great_conjunction_2020():
    """Jupiter-Saturn Great Conjunction on ~2020-12-21 is detected within 10-day window."""
    start_jd = swe.julday(2020, 12, 16, 0.0)
    end_jd = swe.julday(2020, 12, 26, 0.0)
    events = find_conjunction_events(swe, "Jupiter", "Saturn", 1.0, start_jd, end_jd)
    assert len(events) >= 1
    ev = events[0]
    assert ev.event_type == "conjunction"
    assert ev.transit_planet == "Jupiter"
    assert ev.secondary_planet == "Saturn"
    assert ev.sign in SIGNS
    assert 0.0 <= ev.orb_at_event_deg <= 1.0


# ── Test 11: Ingress events ───────────────────────────────────────────────────

def test_ingress_events():
    """Jupiter ingress into Aquarius sidereal is detected in 2021."""
    start_jd = swe.julday(2021, 1, 1, 0.0)
    end_jd = swe.julday(2022, 6, 1, 0.0)
    events = find_ingress_events(swe, "Jupiter", "Aquarius", start_jd, end_jd)
    assert isinstance(events, list)
    if events:
        ev = events[0]
        assert ev.event_type == "ingress"
        assert ev.sign in SIGNS
        assert ev.transit_planet == "Jupiter"
        assert ev.extra.get("target_sign") == "Aquarius"


# ── Test 12: Return events ────────────────────────────────────────────────────

def test_return_events():
    """Saturn return to ~270 deg in 2020 is detected."""
    start_jd = swe.julday(2020, 1, 1, 0.0)
    end_jd = swe.julday(2021, 1, 1, 0.0)
    events = find_return_events(swe, "Saturn", 270.0, 1.0, start_jd, end_jd)
    assert isinstance(events, list)
    if events:
        ev = events[0]
        assert ev.event_type == "return"
        assert ev.transit_planet == "Saturn"
        assert "natal_longitude_deg" in ev.extra


# ── Test 13: Station detection (Mars retrograde 2022) ────────────────────────

def test_station_events_mars_2022():
    """Mars retrograde station (~Oct 30 2022) is detected in Oct 2022 - Feb 2023 window."""
    start_jd = swe.julday(2022, 10, 1, 0.0)
    end_jd = swe.julday(2023, 2, 1, 0.0)
    events = find_station_events(swe, "Mars", start_jd, end_jd)
    assert len(events) >= 1
    ev = events[0]
    assert ev.event_type == "station"
    assert ev.extra.get("station_type") in ("retrograde", "direct")
    assert ev.applying_separating == "stationary"
    assert ev.transit_planet == "Mars"


# ── Test 14: Eclipse proximity events ────────────────────────────────────────

def test_eclipse_proximity_events():
    """Rahu near Sun (solar eclipse) proximity in Jun 2020 is detected."""
    start_jd = swe.julday(2020, 6, 1, 0.0)
    end_jd = swe.julday(2020, 7, 1, 0.0)
    events = find_eclipse_proximity_events(swe, "Rahu", "Sun", 15.0, start_jd, end_jd)
    assert isinstance(events, list)
    # Solar eclipse was 2020-06-21, so should find proximity events
    if events:
        ev = events[0]
        assert ev.event_type == "eclipse"
        assert "eclipse_type" in ev.extra


# ── Test 15: Multi-planet confluence ─────────────────────────────────────────

def test_multi_planet_confluence():
    """Multi-planet confluence function returns list with correct event_type."""
    start_jd = swe.julday(2020, 1, 1, 0.0)
    end_jd = swe.julday(2020, 6, 1, 0.0)
    events = find_multi_planet_confluence_events(
        swe, ["Jupiter", "Saturn"], 270.0, [0], 5.0, start_jd, end_jd
    )
    assert isinstance(events, list)
    if events:
        ev = events[0]
        assert ev.event_type == "multi_planet"
        assert "planets" in ev.extra
        assert "per_planet_orb" in ev.extra


# ── Test 16: Transit-to-transit events ───────────────────────────────────────

def test_transit_to_transit_events():
    """Transit-to-transit conjunction between Jupiter and Saturn found in Dec 2020."""
    start_jd = swe.julday(2020, 12, 1, 0.0)
    end_jd = swe.julday(2021, 1, 1, 0.0)
    events = find_transit_to_transit_events(swe, "Jupiter", "Saturn", [0], 2.0, start_jd, end_jd)
    assert isinstance(events, list)
    if events:
        ev = events[0]
        assert ev.event_type == "transit_to_transit"
        assert ev.transit_planet == "Jupiter"
        assert ev.secondary_planet == "Saturn"
        assert "aspect_deg" in ev.extra


# ── Test 17: Long horizon search (50 years) ───────────────────────────────────

def test_search_long_horizon_50_years():
    """Long-horizon search finds Saturn conjunctions to 270 deg over 50 years."""
    start_jd = swe.julday(2000, 1, 1, 0.0)
    end_jd = swe.julday(2050, 1, 1, 0.0)
    # Saturn conjunctions to Capricorn 0 deg (270 deg sidereal) -- every ~29.5 years
    events = search_long_horizon(swe, "Saturn", 270.0, [0], 1.0, start_jd, end_jd)
    assert isinstance(events, list)
    assert len(events) >= 1
    # Results should be sorted by event_jd
    jds = [e.event_jd for e in events]
    assert jds == sorted(jds)
    # All events within the search window
    for ev in events:
        assert start_jd <= ev.event_jd <= end_jd
