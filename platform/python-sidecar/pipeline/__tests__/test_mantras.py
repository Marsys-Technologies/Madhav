"""
test_mantras.py — Tests for G33 mantra/stotra library

Minimum 25 assertions covering:
- MANTRAS count (≥ 30)
- All 9 navagraha beej mantras present
- Schema integrity (required keys)
- Helper function correctness
- Type distribution
- Content spot-checks
"""

import pytest
from pipeline.mantras import (
    MANTRAS,
    REQUIRED_KEYS,
    get_mantra,
    get_mantras_for_graha,
    list_by_type,
    search_mantras,
)

# ---------------------------------------------------------------------------
# 1. Corpus size
# ---------------------------------------------------------------------------

def test_mantras_minimum_count():
    assert len(MANTRAS) >= 30, f"Expected ≥30 entries, got {len(MANTRAS)}"


def test_mantras_substantial_count():
    """Library should contain well over the minimum."""
    assert len(MANTRAS) >= 50, f"Expected ≥50 entries, got {len(MANTRAS)}"


# ---------------------------------------------------------------------------
# 2. Schema integrity — every entry has required keys
# ---------------------------------------------------------------------------

def test_all_entries_have_required_keys():
    for entry in MANTRAS:
        missing = REQUIRED_KEYS - set(entry.keys())
        assert not missing, f"Entry '{entry.get('id', '?')}' missing keys: {missing}"


def test_all_ids_are_strings():
    for entry in MANTRAS:
        assert isinstance(entry["id"], str) and entry["id"], \
            f"Invalid id in entry: {entry}"


def test_all_ids_unique():
    ids = [e["id"] for e in MANTRAS]
    assert len(ids) == len(set(ids)), "Duplicate IDs found in MANTRAS"


def test_recommended_count_positive_int():
    for entry in MANTRAS:
        assert isinstance(entry["recommended_count"], int) and entry["recommended_count"] > 0, \
            f"Bad recommended_count in '{entry['id']}'"


def test_syllable_count_positive_int():
    for entry in MANTRAS:
        assert isinstance(entry["syllable_count"], int) and entry["syllable_count"] > 0, \
            f"Bad syllable_count in '{entry['id']}'"


def test_classical_citation_non_empty():
    for entry in MANTRAS:
        assert entry["classical_citation"].strip(), \
            f"Empty classical_citation in '{entry['id']}'"


# ---------------------------------------------------------------------------
# 3. All 9 navagraha beej mantras present
# ---------------------------------------------------------------------------

BEEJ_IDS = [
    "sun_beej_mantra",
    "moon_beej_mantra",
    "mars_beej_mantra",
    "mercury_beej_mantra",
    "jupiter_beej_mantra",
    "venus_beej_mantra",
    "saturn_beej_mantra",
    "rahu_beej_mantra",
    "ketu_beej_mantra",
]

def test_all_9_graha_beej_mantras_present():
    entry_ids = {e["id"] for e in MANTRAS}
    for bid in BEEJ_IDS:
        assert bid in entry_ids, f"Missing beej mantra: {bid}"


def test_navagraha_beej_count_at_least_9():
    beej_navagraha = [
        e for e in MANTRAS
        if e["mantra_type"] == "beej" and e["graha"] in
        ("sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu")
    ]
    assert len(beej_navagraha) >= 9


# ---------------------------------------------------------------------------
# 4. get_mantra() function
# ---------------------------------------------------------------------------

def test_get_mantra_sun_beej():
    entry = get_mantra("sun_beej_mantra")
    assert entry is not None
    assert entry["graha"] == "sun"
    assert entry["mantra_type"] == "beej"


def test_get_mantra_moon_beej():
    entry = get_mantra("moon_beej_mantra")
    assert entry is not None
    assert entry["graha"] == "moon"


def test_get_mantra_nonexistent_returns_none():
    result = get_mantra("nonexistent_mantra_xyz")
    assert result is None


def test_get_mantra_maha_mrityunjaya():
    entry = get_mantra("maha_mrityunjaya")
    assert entry is not None
    assert "tryambakam" in entry["sanskrit_iast"].lower() or "tryambakam" in entry["transliteration"].lower()


def test_get_mantra_gayatri():
    entry = get_mantra("gayatri_mantra")
    assert entry is not None
    assert "savitur" in entry["sanskrit_iast"] or "savitur" in entry["transliteration"].lower()


# ---------------------------------------------------------------------------
# 5. get_mantras_for_graha() function
# ---------------------------------------------------------------------------

def test_get_mantras_for_graha_sun_at_least_1():
    results = get_mantras_for_graha("sun")
    assert len(results) >= 1


def test_get_mantras_for_graha_sun_multiple():
    results = get_mantras_for_graha("sun")
    assert len(results) >= 3, "Expected multiple sun mantras (beej + gayatri + stotra etc.)"


def test_get_mantras_for_graha_all_9_grahas():
    grahas = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]
    for g in grahas:
        results = get_mantras_for_graha(g)
        assert len(results) >= 1, f"No mantras found for graha: {g}"


def test_get_mantras_for_graha_returns_correct_graha():
    for entry in get_mantras_for_graha("saturn"):
        assert entry["graha"] == "saturn"


def test_get_mantras_for_graha_unknown_returns_empty():
    results = get_mantras_for_graha("pluto")
    assert results == []


# ---------------------------------------------------------------------------
# 6. list_by_type() function
# ---------------------------------------------------------------------------

def test_list_by_type_beej_at_least_9():
    beej = list_by_type("beej")
    assert len(beej) >= 9


def test_list_by_type_stotra_at_least_5():
    stotra = list_by_type("stotra")
    assert len(stotra) >= 5


def test_list_by_type_vedic_at_least_5():
    vedic = list_by_type("vedic")
    assert len(vedic) >= 5


def test_list_by_type_returns_correct_type():
    for entry in list_by_type("beej"):
        assert entry["mantra_type"] == "beej"


def test_list_by_type_unknown_returns_empty():
    result = list_by_type("totally_unknown_type")
    assert result == []


# ---------------------------------------------------------------------------
# 7. search_mantras() function
# ---------------------------------------------------------------------------

def test_search_mantras_surya_returns_results():
    results = search_mantras("surya")
    assert len(results) >= 1


def test_search_mantras_case_insensitive():
    r1 = search_mantras("Gayatri")
    r2 = search_mantras("gayatri")
    assert len(r1) == len(r2) and len(r1) >= 1


def test_search_mantras_rigveda_finds_citations():
    results = search_mantras("rigveda")
    assert len(results) >= 2


def test_search_mantras_no_match_returns_empty():
    results = search_mantras("xyzzy_nonexistent_term_12345")
    assert results == []


# ---------------------------------------------------------------------------
# 8. Specific content spot-checks
# ---------------------------------------------------------------------------

def test_sun_beej_mantra_day_is_sunday():
    entry = get_mantra("sun_beej_mantra")
    assert entry["auspicious_day"] == "Sunday"


def test_moon_beej_mantra_day_is_monday():
    entry = get_mantra("moon_beej_mantra")
    assert entry["auspicious_day"] == "Monday"


def test_saturn_beej_mantra_day_is_saturday():
    entry = get_mantra("saturn_beej_mantra")
    assert entry["auspicious_day"] == "Saturday"


def test_maha_mrityunjaya_recommended_108():
    entry = get_mantra("maha_mrityunjaya")
    assert entry["recommended_count"] == 108


def test_gayatri_syllable_count_24():
    entry = get_mantra("gayatri_mantra")
    assert entry["syllable_count"] == 24


def test_om_pranava_syllable_count_1():
    entry = get_mantra("om_pranava")
    assert entry is not None
    assert entry["syllable_count"] == 1


def test_om_namah_shivaya_syllable_count_5():
    entry = get_mantra("om_namah_shivaya")
    assert entry is not None
    assert entry["syllable_count"] == 5


def test_hanuman_chalisa_day_tuesday():
    entry = get_mantra("hanuman_chalisa_seed")
    assert entry is not None
    assert entry["auspicious_day"] == "Tuesday"


def test_ganesha_vandana_present():
    entry = get_mantra("ganesha_vandana")
    assert entry is not None
    assert "vakra" in entry["transliteration"].lower() or "vakra" in entry["sanskrit_iast"].lower()


def test_vishnu_sahasranama_present():
    entry = get_mantra("vishnu_sahasranama_seed")
    assert entry is not None
    assert entry["mantra_type"] == "sahsranama"


def test_durga_stotra_present():
    entry = get_mantra("durga_stotra_seed")
    assert entry is not None
    assert entry["graha"] is None  # universal Devi, not graha-specific


def test_saraswati_vandana_graha_mercury():
    entry = get_mantra("saraswati_vandana")
    assert entry is not None
    assert entry["graha"] == "mercury"


def test_lakshmi_stotra_graha_venus():
    entry = get_mantra("lakshmi_stotra_seed")
    assert entry is not None
    assert entry["graha"] == "venus"


def test_gayatri_cited_rigveda():
    entry = get_mantra("gayatri_mantra")
    assert "Rigveda" in entry["classical_citation"] or "rigveda" in entry["classical_citation"].lower()


def test_navagraha_stotra_vyasa_all_9_present():
    stotra_ids = [
        "surya_stotra_vyasa",
        "chandra_stotra_vyasa",
        "mangala_stotra_vyasa",
        "budha_stotra_vyasa",
        "guru_stotra_vyasa",
        "shukra_stotra_vyasa",
        "shani_stotra_vyasa",
        "rahu_stotra_vyasa",
        "ketu_stotra_vyasa",
    ]
    entry_ids = {e["id"] for e in MANTRAS}
    for sid in stotra_ids:
        assert sid in entry_ids, f"Missing Vyasa stotra: {sid}"


def test_gayatri_mantras_for_all_9_grahas():
    """Each graha should have at least one Gayatri-style mantra."""
    gayatri_entries = [e for e in MANTRAS if "gayatri" in e["id"].lower() or "gayatri" in e["name"].lower()]
    graha_set = {e["graha"] for e in gayatri_entries if e["graha"] is not None}
    navagraha = {"sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"}
    assert graha_set == navagraha, \
        f"Missing Gayatri mantras for grahas: {navagraha - graha_set}"


def test_total_assertion_count_sanity():
    """Meta: confirm we have a meaningful library."""
    assert len(MANTRAS) >= 70, f"Expected 70+ for a rich library, got {len(MANTRAS)}"
