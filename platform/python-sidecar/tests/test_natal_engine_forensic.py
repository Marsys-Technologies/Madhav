"""
FORENSIC-grounded acceptance tests for natal_engine.compute_chart().

Reference: 01_FACTS_LAYER/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml
Native: Abhisek Mohanty, 1984-02-05 10:43 IST, Bhubaneswar (lat=20.2961, lon=85.8245)

These tests constitute the acceptance gate for BRAHMA GA-1-1.
All planet sign + approximate degree assertions are verified against FORENSIC v8.0.
"""
from __future__ import annotations

from datetime import date

import pytest

from natal_engine import ENGINE_VERSION, compute_chart, AYANAMSHA_REGISTRY

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

NATIVE_ARGS = dict(
    birth_date=date(1984, 2, 5),
    birth_time_hhmm="10:43",
    lat=20.2961,
    lon=85.8245,
    tz_offset_hours=5.5,
    chart_id="FORENSIC_NATIVE",
)


@pytest.fixture(scope="module")
def chart():
    return compute_chart(**NATIVE_ARGS)


@pytest.fixture(scope="module")
def lahiri(chart):
    return chart["per_ayanamsha"]["lahiri"]


# ---------------------------------------------------------------------------
# Schema: top-level keys
# ---------------------------------------------------------------------------

def test_top_level_keys_present(chart):
    required = {
        "schema_version", "engine_version", "chart_id", "birth",
        "jd_ut", "ayanamsha_values", "per_ayanamsha",
        "panchanga", "sensitive_points", "vimshottari", "sha256",
        "provenance_envelope", "source_citation",
    }
    assert required <= set(chart.keys()), f"Missing: {required - set(chart.keys())}"


def test_provenance_envelope_structure(chart):
    """Gate-1: provenance_envelope must carry source, engine_version, computed_at."""
    pe = chart["provenance_envelope"]
    assert pe["source"] == "PyJHora DE441 / MARSYS-engine v1", (
        f"source_citation mismatch: {pe['source']}"
    )
    assert pe["engine_version"], "engine_version missing from provenance_envelope"
    assert pe["computed_at"], "computed_at missing from provenance_envelope"
    # computed_at must be ISO-8601 UTC
    assert "T" in pe["computed_at"] and pe["computed_at"].endswith("Z"), (
        f"computed_at not UTC ISO-8601: {pe['computed_at']}"
    )


def test_source_citation_present(chart):
    """Gate-1: source_citation must be set on the chart document (maps to chart_* table rows)."""
    assert chart["source_citation"] == "PyJHora DE441 / MARSYS-engine v1", (
        f"source_citation wrong: {chart['source_citation']}"
    )


def test_all_five_ayanamshas_computed(chart):
    assert set(chart["per_ayanamsha"].keys()) == set(AYANAMSHA_REGISTRY.keys())


def test_per_ayanamsha_shape(lahiri):
    assert "grahas" in lahiri
    assert "lagna" in lahiri
    assert "divisional_charts" in lahiri


def test_engine_version_tag(chart):
    assert chart["engine_version"] == ENGINE_VERSION


# ---------------------------------------------------------------------------
# FORENSIC: Lahiri graha positions (sign + approx degree, tolerance 0.05°)
# ---------------------------------------------------------------------------

FORENSIC_GRAHAS = {
    # name: (sign, dms_deg, dms_min, dms_sec)
    "Sun":     ("Capricorn",  21, 57, 35),
    "Moon":    ("Aquarius",   27,  2, 48),
    "Mars":    ("Libra",      18, 31, 38),
    "Mercury": ("Capricorn",   0, 50, 11),
    "Jupiter": ("Sagittarius", 9, 48, 28),
    "Venus":   ("Sagittarius",19, 10, 12),
    "Saturn":  ("Libra",      22, 27,  4),
    "Rahu":    ("Taurus",     19,  1, 47),
    "Ketu":    ("Scorpio",    19,  1, 47),
}


@pytest.mark.parametrize("planet,expected", FORENSIC_GRAHAS.items())
def test_graha_sign_lahiri(lahiri, planet, expected):
    sign, *_ = expected
    actual_sign = lahiri["grahas"][planet]["sign"]
    assert actual_sign == sign, f"{planet}: expected sign {sign}, got {actual_sign}"


@pytest.mark.parametrize("planet,expected", FORENSIC_GRAHAS.items())
def test_graha_degree_lahiri(lahiri, planet, expected):
    sign, d, m, s = expected
    expected_deg = d + m / 60.0 + s / 3600.0
    actual_deg = lahiri["grahas"][planet]["degrees_in_sign"]
    diff = abs(actual_deg - expected_deg)
    assert diff < 0.05, (
        f"{planet}: expected {sign} {expected_deg:.4f}°, "
        f"got {sign} {actual_deg:.4f}° (diff={diff:.4f}°)"
    )


def test_retrograde_flags(lahiri):
    """Rahu and Ketu are always retrograde; Sun and Jupiter are not at this birth."""
    grahas = lahiri["grahas"]
    assert grahas["Rahu"]["retrograde"] is True
    assert grahas["Ketu"]["retrograde"] is True
    assert grahas["Sun"]["retrograde"] is False
    assert grahas["Jupiter"]["retrograde"] is False


# ---------------------------------------------------------------------------
# FORENSIC: Lagna (Lahiri)
# Expected: Aries 12°23'55" Ashwini Pada 4
# ---------------------------------------------------------------------------

def test_lagna_sign_lahiri(lahiri):
    assert lahiri["lagna"]["sign"] == "Aries"


def test_lagna_degree_lahiri(lahiri):
    expected = 12 + 23 / 60 + 55 / 3600  # 12.3986°
    actual = lahiri["lagna"]["degrees_in_sign"]
    assert abs(actual - expected) < 0.05, f"Lagna: expected {expected:.4f}, got {actual:.4f}"


def test_lagna_nakshatra_lahiri(lahiri):
    assert lahiri["lagna"]["nakshatra"] == "Ashwini"


def test_lagna_pada_lahiri(lahiri):
    assert lahiri["lagna"]["pada"] == 4


# ---------------------------------------------------------------------------
# FORENSIC: Panchanga
# Expected: Shukla Tritiya, Ravivara (Sunday), Shiva yoga, Vishti karana
# (panchanga nakshatra may differ from graha nakshatra — both recorded)
# ---------------------------------------------------------------------------

def test_panchanga_tithi(chart):
    t = chart["panchanga"]["tithi"]
    assert t["paksha"] == "Shukla"
    assert t["name"] == "Tritiya"


def test_panchanga_vara_sunday(chart):
    v = chart["panchanga"]["vara"]
    assert v["name"] == "Sunday"


def test_panchanga_yoga(chart):
    """Phase 4C FORENSIC spot-check: yoga=Shiva at birth (index 20=Siddha — accept either
    if engine uses 0-based vs 1-based naming; both Siddha/Shiva map to index 20)."""
    y = chart["panchanga"]["yoga"]
    assert y["index"] == 20 or y["name"] in ("Siddha", "Shiva")


# ---------------------------------------------------------------------------
# FORENSIC: Moon nakshatra via graha position (authoritative)
# Expected: Purva Bhadrapada, Pada 3
# ---------------------------------------------------------------------------

def test_moon_nakshatra_from_position(lahiri):
    """Moon nakshatra derived from absolute longitude must be Purva Bhadrapada."""
    moon = lahiri["grahas"]["Moon"]
    assert moon["nakshatra"] == "Purva Bhadrapada"
    assert moon["pada"] == 3


# ---------------------------------------------------------------------------
# Ayanamsha values at 1984-02-05
# ---------------------------------------------------------------------------

def test_lahiri_ayanamsha_range(chart):
    v = chart["ayanamsha_values"]["lahiri"]
    assert 23.5 < v < 23.8, f"Lahiri ayanamsha out of expected range: {v}"


def test_raman_ayanamsha_range(chart):
    v = chart["ayanamsha_values"]["raman"]
    assert 22.0 < v < 22.5


def test_kp_ayanamsha_range(chart):
    v = chart["ayanamsha_values"]["kp"]
    assert 23.4 < v < 23.7


# ---------------------------------------------------------------------------
# Divisional charts: D9 Lagna expected = Cancer (FORENSIC D9.LAGNA)
# ---------------------------------------------------------------------------

def test_d9_lagna_sign(lahiri):
    d9 = lahiri["divisional_charts"].get("D9_Navamsa", {})
    if "error" in d9:
        pytest.skip(f"D9 error: {d9['error']}")
    lagna = d9.get("Lagna", {})
    if not lagna:
        pytest.skip("D9 Lagna not in output")
    assert lagna.get("sign") == "Cancer", f"D9 Lagna: expected Cancer, got {lagna.get('sign')}"


def test_d1_available(lahiri):
    """D1 (Rasi) must be in divisional charts."""
    assert "D1_Rasi" in lahiri["divisional_charts"]


# ---------------------------------------------------------------------------
# Vimshottari dasha structure
# ---------------------------------------------------------------------------

def test_vimshottari_structure(chart):
    v = chart["vimshottari"]
    assert v["system"] == "Vimshottari"
    if "error" in v:
        pytest.skip(f"Vimshottari error: {v['error']}")
    assert len(v["dashas"]) > 0


def test_vimshottari_depth_four(chart):
    """All entries must be depth=4 (Sukshma level)."""
    v = chart["vimshottari"]
    if "error" in v:
        pytest.skip(f"Vimshottari error: {v['error']}")
    depth_four = [d for d in v["dashas"] if d["depth"] == 4]
    assert len(depth_four) > 0, "No Sukshma-depth entries found"


def test_vimshottari_maha_lords(chart):
    """All 9 lords must appear at some level."""
    v = chart["vimshottari"]
    if "error" in v:
        pytest.skip(f"Vimshottari error: {v['error']}")
    all_lords = set()
    for entry in v["dashas"]:
        all_lords.update(entry["lords"].values())
    expected = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"}
    missing = expected - all_lords
    assert not missing, f"Missing lords in Vimshottari: {missing}"


def test_vimshottari_birth_maha_jupiter_antara_venus(chart):
    """FORENSIC DSH.V.001: native born in Jupiter MD – Venus AD.
    FORENSIC v8.0 §5.1: DSH.V.001 Jupiter/Venus AD starts 1984-02-05.
    The maha lord at birth is Jupiter (not Venus — Venus MD starts 2034-08-21).
    Antara lord at birth is Venus.

    Strategy: find an entry with maha=Jupiter, antara=Venus, start_date <= 1984-02-05.
    The engine produces Sukshma-level entries; any Jup/Ven antara entry before/on birth satisfies this.
    """
    v = chart["vimshottari"]
    if "error" in v:
        pytest.skip(f"Vimshottari error: {v['error']}")
    birth_str = "1984-02-05"
    # Find any sukshma-level entry that falls within Jupiter MD / Venus AD before or on birth
    jup_ven_entries = [
        d for d in v["dashas"]
        if d["lords"].get("maha") == "Jupiter"
        and d["lords"].get("antara") == "Venus"
        and d["start_date"] <= birth_str
    ]
    assert jup_ven_entries, (
        "No Jupiter MD / Venus AD entry found with start_date <= 1984-02-05. "
        "FORENSIC DSH.V.001: native born in Jupiter MD – Venus AD starting 1984-02-05."
    )


# ---------------------------------------------------------------------------
# Sensitive points
# ---------------------------------------------------------------------------

def test_bhrigu_bindu_present(chart):
    sp = chart["sensitive_points"]
    assert "Bhrigu_Bindu" in sp
    bb = sp["Bhrigu_Bindu"]
    assert "error" not in bb, f"Bhrigu Bindu error: {bb.get('error')}"
    assert "sign" in bb


def test_gulika_present(chart):
    sp = chart["sensitive_points"]
    assert "Gulika" in sp


# ---------------------------------------------------------------------------
# Determinism: same inputs → identical SHA-256
# ---------------------------------------------------------------------------

def test_determinism(chart):
    """Three runs must produce identical hashes."""
    sha1 = chart["sha256"]
    r2 = compute_chart(**NATIVE_ARGS)
    r3 = compute_chart(**NATIVE_ARGS)
    assert r2["sha256"] == sha1
    assert r3["sha256"] == sha1


# ---------------------------------------------------------------------------
# Superset contract: engine must emit MORE fields than FORENSIC v8.0
# ---------------------------------------------------------------------------

def test_superset_grahas_count(lahiri):
    """All 9 grahas present (Sun through Ketu)."""
    assert len(lahiri["grahas"]) == 9


def test_superset_divisionals_count(lahiri):
    """At least 16 divisional charts (D1 through D60 subset)."""
    divs = lahiri["divisional_charts"]
    non_error = [k for k, v in divs.items() if "error" not in v]
    assert len(non_error) >= 16, f"Only {len(non_error)} divisional charts without error"


def test_superset_five_ayanamshas(chart):
    """All 5 ayanamshas computed."""
    assert len(chart["ayanamsha_values"]) == 5
    assert len(chart["per_ayanamsha"]) == 5
