"""
G1_internal_invariants — Formal acceptance gate for natal_engine.
Replaces jh_parity gate. Runs against live computation (not static oracle).

Categories:
  1. Algebraic invariants — mathematical properties that must always hold
  2. Cross-ayanamsha sanity — relationships between ayanamsha outputs
  3. Classical spot-checks — known values for native birth (BPHS-grounded)
  4. Body completeness — all bodies emitted per E-03/E-04/E-05
  5. Schema invariants — required fields, ranges

Field-name conventions (from live introspection):
  - grahas[*]: longitude_deg, sign, sign_id (1-based), nakshatra_id, pada,
    retrograde, speed_deg_per_day, heliocentric_longitude, declination_deg,
    altitude_deg, varga_position (keys D1/D9/D10)
  - node_variants[*]: longitude (not longitude_deg), sign_index (not sign_id)
  - AYANAMSHA_REGISTRY ids: 'jh_true_chitra', 'lahiri_standard', 'kp'
"""

import pytest

# Native birth inputs dict (1984-02-05 10:43 IST, Bhubaneswar)
_NATIVE_INPUTS = {
    "datetime_iso": "1984-02-05T10:43:00",
    "tz_offset_hours": 5.5,
    "latitude_deg": 20.27,
    "longitude_deg": 85.84,
    "place_name": "Bhubaneswar",
    "subject_label": "native",
}
# Pin computed_at_iso for determinism
_COMPUTED_AT = "1984-02-05T05:13:00+00:00"

from natal_engine import compute_chart, AYANAMSHA_REGISTRY, ayanamsha_value_deg


# ---------------------------------------------------------------------------
# Shared fixture — compute once per module to keep the suite fast.
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def chart():
    return compute_chart(
        _NATIVE_INPUTS,
        ayanamsha_id="jh_true_chitra",
        computed_at_iso=_COMPUTED_AT,
    )


@pytest.fixture(scope="module")
def grahas(chart):
    return chart["grahas"]


# ============================================================
# Category 1: Algebraic Invariants
# ============================================================

def test_ketu_is_rahu_plus_180_true_node(chart):
    """Ketu True longitude must be exactly 180° from Rahu True (osculating nodes)."""
    variants = chart["node_variants"]
    rahu_lon = variants["rahu_true"]["longitude"]
    ketu_lon = variants["ketu_true"]["longitude"]
    delta = abs((ketu_lon - rahu_lon - 180.0) % 360.0)
    if delta > 180.0:
        delta = 360.0 - delta
    assert delta < 0.01, (
        f"Ketu_true not 180° from Rahu_true: "
        f"rahu={rahu_lon:.6f}, ketu={ketu_lon:.6f}, delta={delta:.6f}"
    )


def test_ketu_is_rahu_plus_180_mean_node(chart):
    """Ketu Mean longitude must be exactly 180° from Rahu Mean."""
    variants = chart["node_variants"]
    rahu_lon = variants["rahu_mean"]["longitude"]
    ketu_lon = variants["ketu_mean"]["longitude"]
    delta = abs((ketu_lon - rahu_lon - 180.0) % 360.0)
    if delta > 180.0:
        delta = 360.0 - delta
    assert delta < 0.01, (
        f"Ketu_mean not 180° from Rahu_mean: "
        f"rahu={rahu_lon:.6f}, ketu={ketu_lon:.6f}, delta={delta:.6f}"
    )


def test_all_longitudes_in_range(grahas):
    """All graha longitude_deg values must be in [0, 360)."""
    for g in grahas:
        lon = g["longitude_deg"]
        assert 0.0 <= lon < 360.0, (
            f"longitude_deg out of range: {g['name']} = {lon}"
        )


def test_sign_id_derives_from_longitude(grahas):
    """sign_id (1-based) must equal int(longitude_deg / 30) + 1 for all grahas."""
    for g in grahas:
        lon = g["longitude_deg"]
        expected = int(lon / 30.0) + 1
        actual = g["sign_id"]
        assert actual == expected, (
            f"sign_id {actual} != int({lon:.4f}/30)+1 = {expected} for {g['name']}"
        )


def test_pada_in_range(grahas):
    """Pada must be 1–4 for all grahas."""
    for g in grahas:
        pada = g["pada"]
        assert 1 <= pada <= 4, (
            f"Pada {pada} out of range for {g['name']}"
        )


def test_nakshatra_id_in_range(grahas):
    """nakshatra_id must be 1–27 for all grahas."""
    for g in grahas:
        nak = g["nakshatra_id"]
        assert 1 <= nak <= 27, (
            f"nakshatra_id {nak} out of range for {g['name']}"
        )


def test_node_longitudes_in_range(chart):
    """All four node variant longitudes must be in [0, 360)."""
    for key, body in chart["node_variants"].items():
        lon = body["longitude"]
        assert 0.0 <= lon < 360.0, (
            f"node_variants[{key}].longitude out of range: {lon}"
        )


# ============================================================
# Category 2: Cross-Ayanamsha Sanity
# ============================================================

def test_three_ayanamshas_registered():
    """Registry must contain exactly jh_true_chitra, lahiri_standard, kp."""
    assert "jh_true_chitra" in AYANAMSHA_REGISTRY
    assert "lahiri_standard" in AYANAMSHA_REGISTRY
    assert "kp" in AYANAMSHA_REGISTRY


def test_jh_vs_lahiri_delta_under_2deg():
    """jh_true_chitra and lahiri_standard must differ by < 2° at native birth JD."""
    import swisseph as swe
    jd = swe.julday(1984, 2, 5, 5.2167)
    ayan_jh = ayanamsha_value_deg(jd, "jh_true_chitra")
    ayan_la = ayanamsha_value_deg(jd, "lahiri_standard")
    delta = abs(ayan_jh - ayan_la)
    assert delta < 2.0, (
        f"jh_true_chitra ({ayan_jh:.6f}°) vs lahiri_standard ({ayan_la:.6f}°) "
        f"differ by {delta:.6f}°, expected < 2°"
    )


def test_jh_vs_kp_delta_under_2deg():
    """jh_true_chitra and kp must differ by < 2° at native birth JD."""
    import swisseph as swe
    jd = swe.julday(1984, 2, 5, 5.2167)
    ayan_jh = ayanamsha_value_deg(jd, "jh_true_chitra")
    ayan_kp = ayanamsha_value_deg(jd, "kp")
    delta = abs(ayan_jh - ayan_kp)
    assert delta < 2.0, (
        f"jh_true_chitra ({ayan_jh:.6f}°) vs kp ({ayan_kp:.6f}°) "
        f"differ by {delta:.6f}°, expected < 2°"
    )


def test_cross_ayanamsha_sun_longitude_delta():
    """Sun longitude should differ < 2° between jh_true_chitra and lahiri_standard."""
    r_jh = compute_chart(
        _NATIVE_INPUTS, ayanamsha_id="jh_true_chitra", computed_at_iso=_COMPUTED_AT
    )
    r_la = compute_chart(
        _NATIVE_INPUTS, ayanamsha_id="lahiri_standard", computed_at_iso=_COMPUTED_AT
    )
    sun_jh = next(g for g in r_jh["grahas"] if g["name"] == "Sun")
    sun_la = next(g for g in r_la["grahas"] if g["name"] == "Sun")

    delta = abs(sun_jh["longitude_deg"] - sun_la["longitude_deg"])
    if delta > 180.0:
        delta = 360.0 - delta
    assert delta < 2.0, (
        f"Sun cross-ayanamsha delta {delta:.4f}° > 2° "
        f"(jh={sun_jh['longitude_deg']:.4f}, lahiri={sun_la['longitude_deg']:.4f})"
    )


def test_cross_ayanamsha_constant_offset_invariant():
    """All 9 grahas must shift by the same offset when ayanamsha changes.

    A smaller ayanamsha subtracted from the same tropical longitude yields a
    larger sidereal longitude, so the longitude delta (jh - lahiri) is the
    negation of the ayanamsha delta (jh - lahiri). We therefore compare the
    observed longitude shift against -ayan_delta to get the expected sign.
    The residual must be < 1" (0.000278°) across all 9 grahas.
    """
    import swisseph as swe
    jd = swe.julday(1984, 2, 5, 5.2167)
    # Ayanamsha delta: jh_true_chitra - lahiri_standard
    # Sidereal lon = tropical lon - ayanamsha, so lon_jh - lon_la = ayan_la - ayan_jh
    ayan_delta_deg = (
        ayanamsha_value_deg(jd, "jh_true_chitra")
        - ayanamsha_value_deg(jd, "lahiri_standard")
    )
    expected_lon_delta = -ayan_delta_deg  # longitude shift = negated ayanamsha shift

    r_jh = compute_chart(
        _NATIVE_INPUTS, ayanamsha_id="jh_true_chitra", computed_at_iso=_COMPUTED_AT
    )
    r_la = compute_chart(
        _NATIVE_INPUTS, ayanamsha_id="lahiri_standard", computed_at_iso=_COMPUTED_AT
    )

    for g_jh, g_la in zip(r_jh["grahas"], r_la["grahas"]):
        name = g_jh["name"]
        observed_delta = g_jh["longitude_deg"] - g_la["longitude_deg"]
        # Handle 360° wrap
        if observed_delta > 180.0:
            observed_delta -= 360.0
        elif observed_delta < -180.0:
            observed_delta += 360.0
        residual_arcsec = abs(observed_delta - expected_lon_delta) * 3600.0
        assert residual_arcsec < 1.0, (
            f"Constant-offset invariant violated for {name}: "
            f"expected lon_Δ={expected_lon_delta:.6f}°, "
            f"observed={observed_delta:.6f}°, residual={residual_arcsec:.3f}\""
        )


# ============================================================
# Category 3: Classical Spot-Checks (native 1984-02-05)
# ============================================================

def test_sun_in_capricorn_for_native(grahas):
    """Native born Feb 5 1984 — Sun should be in Capricorn (sign_id=10) under jh_true_chitra."""
    sun = next((g for g in grahas if g["name"] == "Sun"), None)
    assert sun is not None, "Sun not found in grahas"
    assert sun["sign"] == "Capricorn" or sun["sign_id"] == 10, (
        f"Sun should be in Capricorn but got sign={sun['sign']}, sign_id={sun['sign_id']}"
    )


def test_moon_nakshatra_for_native(grahas):
    """Native birth panchanga (confirmed): Moon in Purva Bhadrapada (nakshatra_id=25)."""
    moon = next((g for g in grahas if g["name"] == "Moon"), None)
    assert moon is not None, "Moon not found in grahas"
    assert moon["nakshatra_id"] == 25, (
        f"Moon nakshatra_id should be 25 (Purva Bhadrapada) but got {moon['nakshatra_id']} ({moon['nakshatra']})"
    )


def test_exactly_9_grahas(grahas):
    """Exactly 9 classical grahas must be in chart output (schema invariant)."""
    assert len(grahas) == 9, f"Expected 9 grahas, got {len(grahas)}"


def test_all_9_graha_names_present(grahas):
    """All 9 classical graha names must be present."""
    names = {g["name"] for g in grahas}
    expected = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"}
    missing = expected - names
    assert not missing, f"Missing grahas: {missing}"


# ============================================================
# Category 4: Body Completeness (E-03 / E-04 / E-05)
# ============================================================

def test_node_variants_all_four_present(chart):
    """E-03: chart output must have node_variants with all 4 keys."""
    variants = chart["node_variants"]
    for key in ("rahu_true", "ketu_true", "rahu_mean", "ketu_mean"):
        assert key in variants, f"Missing node variant: {key}"


def test_lilith_variants_present(chart):
    """E-04: chart output must have lilith_variants with lilith_mean + lilith_true."""
    variants = chart["lilith_variants"]
    assert "lilith_mean" in variants, "Missing lilith_mean"
    assert "lilith_true" in variants, "Missing lilith_true"


def test_outer_bodies_present(chart):
    """E-05: outer_bodies dict must be present with uranus/neptune/pluto (always available)."""
    outer = chart.get("outer_bodies")
    assert outer is not None, "outer_bodies key missing from chart output"
    # These three are always available (no separate ephemeris file required)
    for body in ("uranus", "neptune", "pluto"):
        assert body in outer, f"Missing outer body: {body}"
    # Chiron/ceres etc. are present as keys but may be None when .se1 file absent
    for body in ("chiron", "ceres", "pallas", "juno", "vesta"):
        assert body in outer, f"Missing outer_bodies key: {body}"


def test_lilith_longitudes_in_range(chart):
    """Lilith variants must have longitude in [0, 360)."""
    for key, body in chart["lilith_variants"].items():
        lon = body.get("longitude")
        assert lon is not None, f"lilith_variants[{key}] has no 'longitude'"
        assert 0.0 <= lon < 360.0, (
            f"lilith_variants[{key}].longitude out of range: {lon}"
        )


# ============================================================
# Category 5: Schema Invariants
# ============================================================

def test_required_fields_on_all_grahas(grahas):
    """Every graha dict must have all required schema fields."""
    required = {
        "name", "longitude_deg", "sign", "sign_id", "nakshatra",
        "nakshatra_id", "pada", "retrograde", "speed_deg_per_day",
    }
    for g in grahas:
        missing = required - set(g.keys())
        assert not missing, f"Graha {g.get('name', '?')} missing fields: {missing}"


def test_new_coord_fields_present(grahas):
    """E-01/E-02 fields must be present: heliocentric_longitude, declination_deg, altitude_deg."""
    for g in grahas:
        assert "heliocentric_longitude" in g, (
            f"Missing heliocentric_longitude on {g.get('name', '?')}"
        )
        assert "declination_deg" in g, (
            f"Missing declination_deg on {g.get('name', '?')}"
        )
        assert "altitude_deg" in g, (
            f"Missing altitude_deg on {g.get('name', '?')}"
        )


def test_varga_position_on_grahas(grahas):
    """E-06: varga_position with D1/D9/D10 must be present on all grahas."""
    for g in grahas:
        vp = g.get("varga_position", {})
        missing_vargas = {"D1", "D9", "D10"} - set(vp.keys())
        assert not missing_vargas, (
            f"Missing varga_position keys on {g.get('name', '?')}: {missing_vargas}"
        )


def test_varga_position_sign_indices_in_range(grahas):
    """All varga_position sign_index values must be 1–12."""
    for g in grahas:
        vp = g.get("varga_position", {})
        for varga_name, vdata in vp.items():
            si = vdata.get("sign_index")
            assert si is not None, (
                f"sign_index missing from {g.get('name', '?')} varga_position[{varga_name}]"
            )
            assert 1 <= si <= 12, (
                f"sign_index {si} out of range for {g.get('name', '?')}.varga_position[{varga_name}]"
            )


def test_provenance_fields_present(chart):
    """Provenance block must have engine_version and ayanamsha_config_id."""
    prov = chart.get("provenance", {})
    assert "engine_version" in prov, "Missing provenance.engine_version"
    assert "ayanamsha_config_id" in prov, "Missing provenance.ayanamsha_config_id"
    assert prov["ayanamsha_config_id"] == "jh_true_chitra", (
        f"Expected ayanamsha_config_id='jh_true_chitra', got {prov['ayanamsha_config_id']!r}"
    )


def test_ayanamsha_block_present(chart):
    """Top-level ayanamsha block must be present with id + value_deg."""
    ayan = chart.get("ayanamsha", {})
    assert "id" in ayan, "Missing ayanamsha.id"
    assert "value_deg" in ayan, "Missing ayanamsha.value_deg"
    assert ayan["id"] == "jh_true_chitra"
    # jh_true_chitra at native birth is pinned to ~23.619°; verify reasonable range
    val = ayan["value_deg"]
    assert 23.0 < val < 24.0, (
        f"ayanamsha.value_deg={val:.6f} out of expected 23–24° range for jh_true_chitra"
    )


def test_determinism(chart):
    """Two compute_chart calls with identical inputs + pinned computed_at_iso must be identical."""
    chart2 = compute_chart(
        _NATIVE_INPUTS,
        ayanamsha_id="jh_true_chitra",
        computed_at_iso=_COMPUTED_AT,
    )
    # Compare graha longitudes (the key deterministic output)
    for g1, g2 in zip(chart["grahas"], chart2["grahas"]):
        assert g1["longitude_deg"] == g2["longitude_deg"], (
            f"Non-deterministic longitude_deg for {g1['name']}: "
            f"{g1['longitude_deg']} vs {g2['longitude_deg']}"
        )
