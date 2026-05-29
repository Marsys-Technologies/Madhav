"""
Tests for G40 (career_mapping) and G45 (ayurveda_mapping) classical reference data.
Minimum 30 assertions required per BUILD-ORCH-A-13 acceptance criteria.
"""

import pytest
from pipeline.career_ayurveda import (
    CAREER_MAPPING,
    HOUSE_CAREER,
    DOSHA_BY_SIGN,
    DOSHA_BY_GRAHA,
    KALAPURUSHA_BODY,
    DISEASE_BY_GRAHA,
    get_career_by_graha,
    get_professions_by_graha,
    get_house_career_signification,
    get_dosha_by_sign,
    get_dosha_by_graha,
    get_body_part,
    get_diseases_by_graha,
)

NINE_GRAHAS = ['sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn', 'rahu', 'ketu']
TWELVE_SIGNS = [
    'aries', 'taurus', 'gemini', 'cancer', 'leo', 'virgo',
    'libra', 'scorpio', 'sagittarius', 'capricorn', 'aquarius', 'pisces',
]


# ---------------------------------------------------------------------------
# G40 — CAREER_MAPPING structural checks
# ---------------------------------------------------------------------------

class TestCareerMappingStructure:
    def test_career_mapping_has_nine_grahas(self):
        assert len(CAREER_MAPPING) == 9

    def test_career_mapping_contains_all_grahas(self):
        for g in NINE_GRAHAS:
            assert g in CAREER_MAPPING, f"Missing graha: {g}"

    def test_each_graha_has_required_keys(self):
        required_keys = {'professions', 'significations', 'industry', 'bphs_chapter', 'classical_citation'}
        for g, data in CAREER_MAPPING.items():
            for key in required_keys:
                assert key in data, f"Missing key '{key}' for graha '{g}'"

    def test_each_graha_professions_is_nonempty_list(self):
        for g in NINE_GRAHAS:
            profs = CAREER_MAPPING[g]['professions']
            assert isinstance(profs, list) and len(profs) > 0, f"Empty professions for {g}"

    def test_classical_citation_is_string(self):
        for g in NINE_GRAHAS:
            assert isinstance(CAREER_MAPPING[g]['classical_citation'], str)


# ---------------------------------------------------------------------------
# G40 — Specific profession spot-checks
# ---------------------------------------------------------------------------

class TestCareerMappingContent:
    def test_sun_professions_include_government_official(self):
        profs = CAREER_MAPPING['sun']['professions']
        assert any('government' in p for p in profs), \
            "Sun professions must include a government-related entry"

    def test_mars_professions_include_military_or_surgery(self):
        profs = CAREER_MAPPING['mars']['professions']
        assert any('military' in p or 'soldier' in p or 'surgery' in p or 'surgeon' in p for p in profs), \
            "Mars professions must include military or surgery"

    def test_mercury_professions_include_writing_or_communication(self):
        profs = CAREER_MAPPING['mercury']['professions']
        communication_terms = {'writer', 'journalist', 'teacher', 'communicator', 'printer', 'translator'}
        assert any(any(term in p for term in communication_terms) for p in profs), \
            "Mercury professions must include a writing/communication profession"

    def test_jupiter_professions_include_judge_or_priest(self):
        profs = CAREER_MAPPING['jupiter']['professions']
        assert any('judge' in p or 'priest' in p or 'lawyer' in p for p in profs)

    def test_venus_professions_include_artist_or_musician(self):
        profs = CAREER_MAPPING['venus']['professions']
        assert any('artist' in p or 'musician' in p or 'designer' in p for p in profs)

    def test_saturn_professions_include_laborer_or_miner(self):
        profs = CAREER_MAPPING['saturn']['professions']
        assert any('labor' in p or 'miner' in p or 'mining' in p for p in profs)

    def test_rahu_professions_include_technology_or_research(self):
        profs = CAREER_MAPPING['rahu']['professions']
        assert any('technolog' in p or 'research' in p or 'aviation' in p for p in profs)

    def test_ketu_professions_include_occult_or_spirituality(self):
        profs = CAREER_MAPPING['ketu']['professions']
        assert any('occult' in p or 'spiritual' in p or 'mystic' in p for p in profs)


# ---------------------------------------------------------------------------
# G40 — HOUSE_CAREER checks
# ---------------------------------------------------------------------------

class TestHouseCareer:
    def test_house_career_has_twelve_entries(self):
        assert len(HOUSE_CAREER) == 12

    def test_house_career_keys_are_1_to_12(self):
        assert set(HOUSE_CAREER.keys()) == set(range(1, 13))

    def test_10th_house_signification_mentions_career_or_profession(self):
        sig = HOUSE_CAREER[10].lower()
        assert 'career' in sig or 'profession' in sig or 'government' in sig

    def test_6th_house_mentions_service_or_employment(self):
        sig = HOUSE_CAREER[6].lower()
        assert 'service' in sig or 'employment' in sig

    def test_2nd_house_mentions_income_or_wealth(self):
        sig = HOUSE_CAREER[2].lower()
        assert 'income' in sig or 'wealth' in sig


# ---------------------------------------------------------------------------
# G40 — API functions
# ---------------------------------------------------------------------------

class TestCareerAPI:
    def test_get_career_by_graha_sun(self):
        result = get_career_by_graha('sun')
        assert 'professions' in result

    def test_get_career_by_graha_case_insensitive(self):
        assert get_career_by_graha('SUN') == get_career_by_graha('sun')
        assert get_career_by_graha('Mars') == get_career_by_graha('mars')

    def test_get_career_by_graha_unknown_returns_empty_dict(self):
        assert get_career_by_graha('earth') == {}

    def test_get_professions_by_graha_mercury_nonempty(self):
        profs = get_professions_by_graha('mercury')
        assert isinstance(profs, list) and len(profs) > 0

    def test_get_professions_by_graha_unknown_returns_empty_list(self):
        assert get_professions_by_graha('pluto') == []

    def test_get_house_career_signification_10(self):
        sig = get_house_career_signification(10)
        assert isinstance(sig, str) and len(sig) > 0

    def test_get_house_career_signification_invalid(self):
        assert get_house_career_signification(0) == ''


# ---------------------------------------------------------------------------
# G45 — DOSHA_BY_SIGN structural checks
# ---------------------------------------------------------------------------

class TestDoshaBySign:
    def test_dosha_by_sign_has_twelve_signs(self):
        assert len(DOSHA_BY_SIGN) == 12

    def test_dosha_by_sign_contains_all_signs(self):
        for sign in TWELVE_SIGNS:
            assert sign in DOSHA_BY_SIGN, f"Missing sign: {sign}"

    def test_dosha_by_sign_primary_dosha_is_valid(self):
        valid_doshas = {'vata', 'pitta', 'kapha'}
        for sign, data in DOSHA_BY_SIGN.items():
            assert data['primary_dosha'] in valid_doshas, \
                f"Invalid primary_dosha for {sign}: {data['primary_dosha']}"

    def test_fire_signs_are_pitta(self):
        for sign in ('aries', 'leo', 'sagittarius'):
            assert DOSHA_BY_SIGN[sign]['primary_dosha'] == 'pitta', \
                f"Fire sign {sign} should be pitta"

    def test_air_signs_are_vata(self):
        for sign in ('gemini', 'libra', 'aquarius'):
            assert DOSHA_BY_SIGN[sign]['primary_dosha'] == 'vata', \
                f"Air sign {sign} should be vata"

    def test_get_dosha_by_sign_aries(self):
        result = get_dosha_by_sign('aries')
        assert result['primary_dosha'] == 'pitta'

    def test_get_dosha_by_sign_taurus(self):
        result = get_dosha_by_sign('taurus')
        assert result['primary_dosha'] == 'kapha'

    def test_get_dosha_by_sign_gemini(self):
        result = get_dosha_by_sign('gemini')
        assert result['primary_dosha'] == 'vata'

    def test_get_dosha_by_sign_case_insensitive(self):
        assert get_dosha_by_sign('ARIES') == get_dosha_by_sign('aries')

    def test_get_dosha_by_sign_unknown_returns_empty_dict(self):
        assert get_dosha_by_sign('not_a_sign') == {}


# ---------------------------------------------------------------------------
# G45 — DOSHA_BY_GRAHA checks
# ---------------------------------------------------------------------------

class TestDoshaByGraha:
    def test_dosha_by_graha_has_nine_grahas(self):
        assert len(DOSHA_BY_GRAHA) == 9

    def test_dosha_by_graha_contains_all_grahas(self):
        for g in NINE_GRAHAS:
            assert g in DOSHA_BY_GRAHA, f"Missing graha: {g}"

    def test_get_dosha_by_graha_mars_is_pitta(self):
        result = get_dosha_by_graha('mars')
        assert result.lower() == 'pitta'

    def test_get_dosha_by_graha_saturn_is_vata(self):
        result = get_dosha_by_graha('saturn')
        assert result.lower() == 'vata'

    def test_get_dosha_by_graha_sun_is_pitta(self):
        result = get_dosha_by_graha('sun')
        assert result.lower() == 'pitta'

    def test_get_dosha_by_graha_jupiter_is_kapha(self):
        result = get_dosha_by_graha('jupiter')
        assert result.lower() == 'kapha'

    def test_get_dosha_by_graha_case_insensitive(self):
        assert get_dosha_by_graha('MARS') == get_dosha_by_graha('mars')

    def test_get_dosha_by_graha_unknown_returns_empty_string(self):
        assert get_dosha_by_graha('earth') == ''


# ---------------------------------------------------------------------------
# G45 — KALAPURUSHA_BODY checks
# ---------------------------------------------------------------------------

class TestKalapurushaBody:
    def test_kalapurusha_body_has_twelve_signs(self):
        assert len(KALAPURUSHA_BODY) == 12

    def test_kalapurusha_body_contains_all_signs(self):
        for sign in TWELVE_SIGNS:
            assert sign in KALAPURUSHA_BODY, f"Missing sign: {sign}"

    def test_get_body_part_aries_is_head(self):
        result = get_body_part('aries')
        assert result.lower() == 'head'

    def test_get_body_part_pisces_is_feet(self):
        result = get_body_part('pisces')
        assert 'feet' in result.lower() or 'foot' in result.lower()

    def test_get_body_part_cancer_mentions_chest(self):
        result = get_body_part('cancer')
        assert 'chest' in result.lower()

    def test_get_body_part_scorpio_mentions_reproductive(self):
        result = get_body_part('scorpio')
        assert 'reproductive' in result.lower()

    def test_get_body_part_case_insensitive(self):
        assert get_body_part('ARIES') == get_body_part('aries')

    def test_get_body_part_unknown_returns_empty_string(self):
        assert get_body_part('not_a_sign') == ''


# ---------------------------------------------------------------------------
# G45 — DISEASE_BY_GRAHA checks
# ---------------------------------------------------------------------------

class TestDiseaseByGraha:
    def test_disease_by_graha_has_nine_grahas(self):
        assert len(DISEASE_BY_GRAHA) == 9

    def test_disease_by_graha_contains_all_grahas(self):
        for g in NINE_GRAHAS:
            assert g in DISEASE_BY_GRAHA, f"Missing graha: {g}"

    def test_get_diseases_by_graha_sun_nonempty(self):
        result = get_diseases_by_graha('sun')
        assert isinstance(result, list) and len(result) > 0

    def test_sun_diseases_include_heart_or_eye(self):
        diseases = get_diseases_by_graha('sun')
        assert any('heart' in d or 'eye' in d or 'bone' in d for d in diseases)

    def test_saturn_diseases_include_chronic_or_arthritis(self):
        diseases = get_diseases_by_graha('saturn')
        assert any('chronic' in d or 'arthritis' in d or 'bone' in d for d in diseases)

    def test_rahu_diseases_include_poison_or_unusual(self):
        diseases = get_diseases_by_graha('rahu')
        assert any('poison' in d or 'unusual' in d or 'epidemic' in d for d in diseases)

    def test_get_diseases_by_graha_case_insensitive(self):
        assert get_diseases_by_graha('SUN') == get_diseases_by_graha('sun')

    def test_get_diseases_by_graha_unknown_returns_empty_list(self):
        assert get_diseases_by_graha('earth') == []

    def test_each_graha_has_at_least_three_diseases(self):
        for g in NINE_GRAHAS:
            diseases = DISEASE_BY_GRAHA[g]
            assert len(diseases) >= 3, f"Graha {g} has fewer than 3 disease entries"
