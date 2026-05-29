"""
Tests for A4-S7 emitters:
  emit_sun_moon_dynamics, emit_agni_vasa, emit_panchaka,
  emit_disha_shul, emit_shoonya_rashis.

Native birth: 1984-02-05, tithi=3 (Shukla Tritiya), nakshatra~26 (Purva Bhadrapada), vara=0 (Sunday).
"""
import pytest
from pipeline.writers.panchanga_writer_a4 import (
    emit_sun_moon_dynamics,
    emit_agni_vasa,
    emit_panchaka,
    emit_disha_shul,
    emit_shoonya_rashis,
    _AGNI_VASA_NAMES,
    _PANCHAKA_TYPES,
    _DISHA_SHUL_BY_WEEKDAY,
)

CHART_ID = "test-chart-a4s7-00000000"
BUILD_ID = "test-build-a4s7"

# Native panchanga values
TITHI_NUM = 3      # Shukla Tritiya
NAK_NUM   = 26     # Purva Bhadrapada  (panchaka-active range 23-27)
WEEKDAY   = 0      # Sunday

# Sample ISO timestamps for sun_moon_dynamics
T_PRAVESH  = "1984-02-05T05:00:00"
T_ARAMBHA  = "1984-02-05T17:30:00"
N_PRAVESH  = "1984-02-05T04:30:00"
N_ARAMBHA  = "1984-02-06T05:00:00"
Y_PRAVESH  = "1984-02-05T06:00:00"
Y_ARAMBHA  = "1984-02-06T06:30:00"
K_PRAVESH  = "1984-02-05T10:43:00"
K_ARAMBHA  = "1984-02-05T16:00:00"


# ── emit_sun_moon_dynamics ────────────────────────────────────────────────────

@pytest.fixture
def smd_rows():
    return emit_sun_moon_dynamics(
        CHART_ID, BUILD_ID,
        T_PRAVESH, T_ARAMBHA,
        N_PRAVESH, N_ARAMBHA,
        Y_PRAVESH, Y_ARAMBHA,
        K_PRAVESH, K_ARAMBHA,
    )


def test_sun_moon_dynamics_row_count(smd_rows):
    assert len(smd_rows) == 8


def test_sun_moon_dynamics_keys(smd_rows):
    expected_keys = {
        'tithi_pravesh_iso', 'tithi_arambha_iso',
        'nakshatra_pravesh_iso', 'nakshatra_arambha_iso',
        'yoga_pravesh_iso', 'yoga_arambha_iso',
        'karana_pravesh_iso', 'karana_arambha_iso',
    }
    emitted_keys = {r['fact_key'] for r in smd_rows}
    assert emitted_keys == expected_keys


def test_sun_moon_dynamics_category(smd_rows):
    cats = {r['fact_category'] for r in smd_rows}
    assert cats == {'panchanga_sun_moon_dynamics'}


def test_sun_moon_dynamics_ayanamsha(smd_rows):
    assert all(r['ayanamsha_id'] == 'INVARIANT' for r in smd_rows)


def test_sun_moon_dynamics_vps(smd_rows):
    assert all(r['verification_pass_status'] == 'single' for r in smd_rows)


# ── emit_agni_vasa ────────────────────────────────────────────────────────────

@pytest.fixture
def agni_rows():
    return emit_agni_vasa(CHART_ID, BUILD_ID, TITHI_NUM, NAK_NUM, WEEKDAY)


def test_agni_vasa_row_count(agni_rows):
    assert len(agni_rows) == 3


def test_agni_vasa_keys(agni_rows):
    keys = {r['fact_key'] for r in agni_rows}
    assert keys == {'residence', 'computation_formula', 'yagna_auspicious_flag'}


def test_agni_vasa_residence_valid(agni_rows):
    res_row = next(r for r in agni_rows if r['fact_key'] == 'residence')
    assert res_row['fact_value_text'] in _AGNI_VASA_NAMES.values()


def test_agni_vasa_formula_contains_residue(agni_rows):
    # Native: (3 + 0 + 26 + 0) % 4 = 29 % 4 = 1 → Akasha
    formula_row = next(r for r in agni_rows if r['fact_key'] == 'computation_formula')
    assert '%4=' in formula_row['fact_value_text']


def test_agni_vasa_native_result(agni_rows):
    # tithi=3, paksha=0 (Shukla), nak=26, vara=0 → (3+0+26+0)%4 = 1 → Akasha
    res_row = next(r for r in agni_rows if r['fact_key'] == 'residence')
    assert res_row['fact_value_text'] == 'Akasha'


def test_agni_vasa_two_pass_verified(agni_rows):
    assert all(r['verification_pass_status'] == 'two_pass_verified' for r in agni_rows)


# ── emit_panchaka ─────────────────────────────────────────────────────────────

@pytest.fixture
def panchaka_rows_active():
    # nakshatra=26 → panchaka active; Sunday → Mrityu type
    return emit_panchaka(CHART_ID, BUILD_ID, TITHI_NUM, NAK_NUM, WEEKDAY)


@pytest.fixture
def panchaka_rows_inactive():
    # nakshatra=10 → panchaka NOT active
    return emit_panchaka(CHART_ID, BUILD_ID, TITHI_NUM, 10, WEEKDAY)


def test_panchaka_active_row_count(panchaka_rows_active):
    assert len(panchaka_rows_active) == 6


def test_panchaka_inactive_row_count(panchaka_rows_inactive):
    assert len(panchaka_rows_inactive) == 6


def test_panchaka_flag_active(panchaka_rows_active):
    flag = next(r for r in panchaka_rows_active if r['fact_category'] == 'panchaka_flag')
    assert flag['fact_value_text'] == 'True'


def test_panchaka_flag_inactive(panchaka_rows_inactive):
    flag = next(r for r in panchaka_rows_inactive if r['fact_category'] == 'panchaka_flag')
    assert flag['fact_value_text'] == 'False'


def test_panchaka_active_type_mrityu_on_sunday(panchaka_rows_active):
    # Sunday + panchaka active → Mrityu should be True, others False
    mrityu_row = next(
        r for r in panchaka_rows_active
        if r['fact_category'] == 'panchanga_panchaka_mrityu'
    )
    assert mrityu_row['fact_value_text'] == 'True'
    # All other types should be False
    for ptype in _PANCHAKA_TYPES:
        if ptype != 'Mrityu':
            row = next(
                r for r in panchaka_rows_active
                if r['fact_category'] == f'panchanga_panchaka_{ptype.lower()}'
            )
            assert row['fact_value_text'] == 'False'


def test_panchaka_all_inactive_when_not_in_range(panchaka_rows_inactive):
    type_rows = [r for r in panchaka_rows_inactive if r['fact_category'] != 'panchaka_flag']
    assert all(r['fact_value_text'] == 'False' for r in type_rows)


# ── emit_disha_shul ───────────────────────────────────────────────────────────

@pytest.fixture
def disha_rows():
    return emit_disha_shul(CHART_ID, BUILD_ID, WEEKDAY)


def test_disha_shul_row_count(disha_rows):
    assert len(disha_rows) == 2


def test_disha_shul_keys(disha_rows):
    keys = {r['fact_key'] for r in disha_rows}
    assert keys == {'direction_to_avoid', 'weekday_reference'}


def test_disha_shul_sunday_is_west(disha_rows):
    # Native born Sunday → Disha Shul = West
    dir_row = next(r for r in disha_rows if r['fact_key'] == 'direction_to_avoid')
    assert dir_row['fact_value_text'] == 'West'


def test_disha_shul_thursday_is_south():
    rows = emit_disha_shul(CHART_ID, BUILD_ID, 4)  # Thursday
    dir_row = next(r for r in rows if r['fact_key'] == 'direction_to_avoid')
    assert dir_row['fact_value_text'] == 'South'


def test_disha_shul_ayanamsha(disha_rows):
    assert all(r['ayanamsha_id'] == 'INVARIANT' for r in disha_rows)


# ── emit_shoonya_rashis ───────────────────────────────────────────────────────

@pytest.fixture
def shoonya_rows():
    return emit_shoonya_rashis(CHART_ID, BUILD_ID, TITHI_NUM, NAK_NUM)


def test_shoonya_row_count(shoonya_rows):
    assert len(shoonya_rows) == 2


def test_shoonya_categories(shoonya_rows):
    cats = {r['fact_category'] for r in shoonya_rows}
    assert cats == {'panchanga_tithi_shoonya_rashi', 'panchanga_nakshatra_shoonya_rashi'}


def test_shoonya_key_is_void_sign(shoonya_rows):
    assert all(r['fact_key'] == 'void_sign' for r in shoonya_rows)


def test_shoonya_tithi3_is_mithuna(shoonya_rows):
    # tithi=3 → Mithuna
    tithi_row = next(
        r for r in shoonya_rows if r['fact_category'] == 'panchanga_tithi_shoonya_rashi'
    )
    assert tithi_row['fact_value_text'] == 'Mithuna'


def test_shoonya_nak26_is_makara(shoonya_rows):
    # nakshatra=26 (Purva Bhadrapada) → Makara
    nak_row = next(
        r for r in shoonya_rows if r['fact_category'] == 'panchanga_nakshatra_shoonya_rashi'
    )
    assert nak_row['fact_value_text'] == 'Makara'
