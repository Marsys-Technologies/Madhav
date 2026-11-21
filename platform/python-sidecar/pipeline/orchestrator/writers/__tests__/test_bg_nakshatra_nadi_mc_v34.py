"""
Golden-value test: bg_nakshatra nāḍī for all 27 nakshatras vs Muhurta Chintamani v.34.

Source: Muhurta Chintamani Vivāha-prakaraṇa v.34 + ṭīkā, corpus chunk
muhurta_chintamani:PG97:C1 (verse begins on PG96:C2). The lists below are typed
from the verse, independently of the data module, so a regression in either the
seed rows or the module's own reference map is caught.

Regression guard for the defect found 2026-11-16: the seed used a naive
Adi/Madhya/Antya repeating cycle, which mislabelled 10 nakshatras (Rohini, Ardra,
Magha, Uttara Phalguni, Vishakha, Jyeshtha, Shravana, Shatabhisha,
Uttara Bhadrapada, Revati). That value is copied into every chart's L1
nakshatra facts by ga_nakshatra.
"""
import pytest

from brahmagyan.l0_nakshatra import NAKSHATRAS_ENRICHED, NADI_BY_NAKSHATRA_ID_MC_V34
from brahmagyan.citation_pass2_doshas import PASS2_DOSHA_EDITS

# nakshatra_id -> name as typed from the verse lists (canonical spelling).
MC_V34_ADI = {
    1: "Ashwini", 6: "Ardra", 7: "Punarvasu", 12: "Uttara Phalguni", 13: "Hasta",
    18: "Jyeshtha", 19: "Mula", 24: "Shatabhisha", 25: "Purva Bhadrapada",
}
MC_V34_MADHYA = {
    2: "Bharani", 5: "Mrigashira", 8: "Pushya", 11: "Purva Phalguni", 14: "Chitra",
    17: "Anuradha", 20: "Purva Ashadha", 23: "Dhanishta", 26: "Uttara Bhadrapada",
}
MC_V34_ANTYA = {
    3: "Krittika", 4: "Rohini", 9: "Ashlesha", 10: "Magha", 15: "Swati",
    16: "Vishakha", 21: "Uttara Ashadha", 22: "Shravana", 27: "Revati",
}

EXPECTED = {
    **{i: "Adi" for i in MC_V34_ADI},
    **{i: "Madhya" for i in MC_V34_MADHYA},
    **{i: "Antya" for i in MC_V34_ANTYA},
}

# Spelling variants used across the codebase -> canonical spelling above.
_ALIASES = {"moola": "mula", "mrigasira": "mrigashira", "dhanishtha": "dhanishta"}


def _norm(name: str) -> str:
    key = name.lower().replace("-", " ").strip()
    return _ALIASES.get(key, key)


_ROWS = {r["nakshatra_id"]: r for r in NAKSHATRAS_ENRICHED[:27]}
_NAMES = {**MC_V34_ADI, **MC_V34_MADHYA, **MC_V34_ANTYA}


def test_verse_lists_partition_all_27():
    assert len(MC_V34_ADI) == len(MC_V34_MADHYA) == len(MC_V34_ANTYA) == 9
    assert set(EXPECTED) == set(range(1, 28))


@pytest.mark.parametrize("nak_id", range(1, 28))
def test_seed_nadi_matches_mc_v34(nak_id):
    row = _ROWS[nak_id]
    assert _norm(row["name_en"]) == _norm(_NAMES[nak_id]), "id/name alignment"
    assert row["nadi"] == EXPECTED[nak_id], (
        f"{row['name_en']} (id {nak_id}): nadi={row['nadi']!r}, "
        f"MC v.34 says {EXPECTED[nak_id]!r}"
    )


def test_module_reference_map_matches_verse():
    assert NADI_BY_NAKSHATRA_ID_MC_V34 == EXPECTED


def test_abhijit_has_no_nadi():
    assert NAKSHATRAS_ENRICHED[27]["is_abhijit"] is True
    assert NAKSHATRAS_ENRICHED[27]["nadi"] is None


def test_seed_agrees_with_nadi_dosha_rule_lists():
    """The nadi_dosha catalogue row carries the same MC v.34 lists; the two must not drift."""
    lists = PASS2_DOSHA_EDITS["nadi_dosha"]["formation_rule_jsonb"]["nadi_lists_mc_v34"]
    label = {"adya": "Adi", "madhya": "Madhya", "antya": "Antya"}
    by_name = {_norm(r["name_en"]): r["nadi"] for r in _ROWS.values()}
    seen = set()
    for key, names in lists.items():
        for name in names:
            n = _norm(name)
            assert by_name[n] == label[key], f"{name}: seed={by_name[n]}, dosha rule={label[key]}"
            seen.add(n)
    assert seen == set(by_name), "dosha lists must cover exactly the 27 nakshatras"
