"""
test_dashas_writer.py — Unit tests for dashas_writer.py A7-S1 through A7-S4
============================================================================
All tests run without DB connection (conn=None path).
Requires at minimum 30 assertions.

canonical_id: A7-TEST
stream: A
session: A7-S1-S4 [BUILD-ORCH-A7-S1-S4]
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

# ── Import the module under test ──────────────────────────────────────────────
from pipeline.writers.dashas_writer import (
    # Constants
    VIMSHOTTARI_SEQUENCE, VIMSHOTTARI_YEARS, VIMSHOTTARI_TOTAL,
    YOGINI_LORDS, YOGINI_GRAHAS, YOGINI_YEARS, YOGINI_TOTAL,
    ASHTOTTARI_SEQUENCE, ASHTOTTARI_YEARS, ASHTOTTARI_TOTAL,
    NAISARGIKA_SEQUENCE, NAISARGIKA_TOTAL,
    MUDDA_DAYS, MUDDA_TOTAL_DAYS,
    ZODIAC_SIGNS,
    # Computation functions
    compute_antardasha,
    compute_pratyantar,
    compute_sookshma,
    compute_yogini_sequence,
    compute_ashtottari_sequence,
    compute_naisargika_sequence,
    compute_mudda_for_year,
    # Helpers
    _yogini_start_idx,
    _ashtottari_start_idx,
    _collect_vimshottari_rows,
    _collect_yogini_rows,
    _collect_ashtottari_rows,
    _collect_naisargika_rows,
    _collect_mudda_rows,
    _collect_jaimini_chara_rows,
    _collect_kalachakra_rows,
    _extract_moon_data,
    _extract_lagna_sign,
    _extract_birth_dt,
    _parse_iso,
    # Main entry
    write,
)

# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

BIRTH_DT = datetime(1984, 2, 5, 5, 13, 0, tzinfo=timezone.utc)
CHART_ID  = "test-chart-0000-0000-000000000001"
AYA_ID    = "lahiri"
BUILD_ID  = "test-build-001"


def _make_maha_seq():
    """Minimal synthetic mahadasha_sequence covering 1984-2104."""
    seq = []
    lords   = VIMSHOTTARI_SEQUENCE  # 9 lords
    years   = [VIMSHOTTARI_YEARS[l] for l in lords]
    current = BIRTH_DT
    for i, lord in enumerate(lords):
        yrs = years[i]
        end = current + timedelta(days=yrs * 365.25)
        seq.append({
            "lord":      lord,
            "start_iso": current.isoformat(),
            "end_iso":   end.isoformat(),
        })
        current = end
    return seq


def _make_chart_output(moon_nakshatra_id: int = 22,
                        moon_deg_in_nak: float = 5.0,
                        moon_lon: float = 295.0):
    return {
        "birth_datetime": BIRTH_DT.isoformat(),
        "lagna": {"sign": "Scorpio"},
        "dashas": {
            "system": "vimshottari",
            "mahadasha_sequence": _make_maha_seq(),
        },
        "grahas": [
            {
                "name": "Moon",
                "longitude": moon_lon,
                "nakshatra_id": moon_nakshatra_id,
            },
            {"name": "Sun",     "longitude": 292.0, "sign": "Capricorn"},
            {"name": "Mars",    "longitude": 90.0,  "sign": "Cancer"},
            {"name": "Jupiter", "longitude": 240.0, "sign": "Sagittarius"},
        ],
    }


# ─────────────────────────────────────────────────────────────────────────────
# §1 — Constants sanity
# ─────────────────────────────────────────────────────────────────────────────

def test_vimshottari_total():
    """Vimshottari period_lengths must sum to 120."""
    assert sum(VIMSHOTTARI_YEARS.values()) == VIMSHOTTARI_TOTAL == 120  # A1

def test_vimshottari_sequence_length():
    """Vimshottari sequence has 9 elements."""
    assert len(VIMSHOTTARI_SEQUENCE) == 9  # A2

def test_yogini_total():
    """Yogini periods sum to 36 years."""
    assert sum(YOGINI_YEARS) == YOGINI_TOTAL == 36  # A3

def test_yogini_8_elements():
    """Yogini has exactly 8 lords."""
    assert len(YOGINI_LORDS) == 8  # A4
    assert len(YOGINI_GRAHAS) == 8  # A5

def test_ashtottari_total():
    """Ashtottari period_lengths sum to 108 years."""
    assert sum(ASHTOTTARI_YEARS.values()) == ASHTOTTARI_TOTAL == 108  # A6

def test_naisargika_total():
    """Naisargika sequence sums to ~120 years."""
    assert NAISARGIKA_TOTAL == 120  # A7
    assert sum(y for _, y in NAISARGIKA_SEQUENCE) == 120  # A8

def test_mudda_days_total():
    """Mudda days sum to exactly 365."""
    assert MUDDA_TOTAL_DAYS == 365  # A9
    assert sum(MUDDA_DAYS.values()) == 365  # A10


# ─────────────────────────────────────────────────────────────────────────────
# §2 — Vimshottari antardasha
# ─────────────────────────────────────────────────────────────────────────────

def test_antardasha_returns_9_periods():
    """compute_antardasha returns exactly 9 periods."""
    start = BIRTH_DT
    end   = start + timedelta(days=16 * 365.25)
    antars = compute_antardasha("Jupiter", start, end)
    assert len(antars) == 9  # A11

def test_antardasha_sum_equals_maha_duration():
    """Sum of antardasha durations equals mahadasha duration."""
    start    = BIRTH_DT
    end      = start + timedelta(days=16 * 365.25)
    maha_days = (end - start).total_seconds() / 86400
    antars    = compute_antardasha("Jupiter", start, end)
    antar_sum = sum(a["duration_days"] for a in antars)
    assert abs(antar_sum - maha_days) < 0.1  # A12

def test_antardasha_first_lord_is_maha_lord():
    """First antardasha lord is always the mahadasha lord itself."""
    start  = BIRTH_DT
    end    = start + timedelta(days=7 * 365.25)
    antars = compute_antardasha("Ketu", start, end)
    assert antars[0]["antar_lord"] == "Ketu"  # A13

def test_antardasha_jupiter_self_first():
    """Jupiter mahadasha → first antardasha starts with Jupiter."""
    start  = BIRTH_DT
    end    = start + timedelta(days=16 * 365.25)
    antars = compute_antardasha("Jupiter", start, end)
    assert antars[0]["antar_lord"] == "Jupiter"  # A14


# ─────────────────────────────────────────────────────────────────────────────
# §3 — Vimshottari pratyantar / sookshma
# ─────────────────────────────────────────────────────────────────────────────

def test_pratyantar_returns_9_periods():
    """compute_pratyantar returns 9 periods."""
    start  = BIRTH_DT
    end    = start + timedelta(days=1000)
    prats  = compute_pratyantar("Jupiter", "Saturn", start, end)
    assert len(prats) == 9  # A15

def test_pratyantar_sum_equals_antar_duration():
    """Sum of pratyantar durations equals antar duration."""
    start      = BIRTH_DT
    end        = start + timedelta(days=1000)
    antar_days = 1000.0
    prats      = compute_pratyantar("Jupiter", "Saturn", start, end)
    prat_sum   = sum(p["duration_days"] for p in prats)
    assert abs(prat_sum - antar_days) < 0.1  # A16

def test_sookshma_returns_9_periods():
    """compute_sookshma returns 9 periods."""
    start  = BIRTH_DT
    end    = start + timedelta(days=30)
    sooks  = compute_sookshma("Jupiter", "Saturn", "Mercury", start, end)
    assert len(sooks) == 9  # A17

def test_sookshma_sum_equals_pratyantar_duration():
    """Sum of sookshma durations equals pratyantar duration."""
    start  = BIRTH_DT
    end    = start + timedelta(days=30)
    prat_days = 30.0
    sooks  = compute_sookshma("Jupiter", "Saturn", "Mercury", start, end)
    sook_sum = sum(s["duration_days"] for s in sooks)
    assert abs(sook_sum - prat_days) < 0.1  # A18

def test_vimshottari_nested_total_duration():
    """Maha → Antar → Pratyantar → Sookshma total duration matches maha."""
    start    = BIRTH_DT
    end      = start + timedelta(days=16 * 365.25)
    maha_days = (end - start).total_seconds() / 86400
    antars   = compute_antardasha("Jupiter", start, end)
    total_sookshma_days = 0.0
    for antar in antars:
        a_start = _parse_iso(antar["start_iso"])
        a_end   = _parse_iso(antar["end_iso"])
        prats   = compute_pratyantar("Jupiter", antar["antar_lord"], a_start, a_end)
        for prat in prats:
            p_start = _parse_iso(prat["start_iso"])
            p_end   = _parse_iso(prat["end_iso"])
            sooks   = compute_sookshma("Jupiter", antar["antar_lord"],
                                        prat["pratyantar_lord"], p_start, p_end)
            total_sookshma_days += sum(s["duration_days"] for s in sooks)
    assert abs(total_sookshma_days - maha_days) < 1.0  # A19


# ─────────────────────────────────────────────────────────────────────────────
# §4 — Yogini
# ─────────────────────────────────────────────────────────────────────────────

def test_yogini_start_idx_nakshatra_1():
    """Nakshatra 1 → Mangala (index 0)."""
    assert _yogini_start_idx(1) == 0  # A20

def test_yogini_start_idx_nakshatra_9():
    """Nakshatra 9 → index 0 (9-1)%8=0 → Mangala."""
    assert _yogini_start_idx(9) == 0  # A21

def test_yogini_start_idx_nakshatra_22():
    """Nakshatra 22 → (22-1)%8 = 5 → Ulka."""
    assert _yogini_start_idx(22) == 5  # A22

def test_yogini_sequence_starts_correctly_nak22():
    """For nakshatra 22 (deg_in_nak=5), first period is Ulka."""
    seq = compute_yogini_sequence(22, 5.0, BIRTH_DT)
    assert len(seq) > 0  # A23
    assert seq[0]["yogini"] == "Ulka"  # A24

def test_yogini_sequence_balance_less_than_full_period():
    """Balance period is always ≤ full period years."""
    seq = compute_yogini_sequence(22, 5.0, BIRTH_DT)
    full_years = YOGINI_YEARS[_yogini_start_idx(22)]
    assert seq[0]["years"] <= full_years  # A25
    assert seq[0]["is_balance"] is True  # A26

def test_yogini_second_period_is_full():
    """Second period (first full cycle) should not be marked is_balance."""
    seq = compute_yogini_sequence(22, 5.0, BIRTH_DT)
    assert seq[1]["is_balance"] is False  # A27

def test_yogini_sequence_covers_2100():
    """Yogini sequence extends past 2100."""
    seq = compute_yogini_sequence(1, 0.0, BIRTH_DT)
    last_end = _parse_iso(seq[-1]["end_iso"])
    assert last_end.year >= 2100  # A28


# ─────────────────────────────────────────────────────────────────────────────
# §5 — Ashtottari
# ─────────────────────────────────────────────────────────────────────────────

def test_ashtottari_start_nak1_is_sun():
    """Nakshatra 1 → Sun (index 0)."""
    assert _ashtottari_start_idx(1) == 0  # A29
    assert ASHTOTTARI_SEQUENCE[0] == "Sun"  # A30

def test_ashtottari_sequence_8_lords():
    """Ashtottari has 8 lords."""
    assert len(ASHTOTTARI_SEQUENCE) == 8  # A31

def test_ashtottari_sequence_covers_birth():
    """Ashtottari sequence starts from birth datetime."""
    seq = compute_ashtottari_sequence(1, 0.0, BIRTH_DT)
    first_start = _parse_iso(seq[0]["start_iso"])
    assert first_start.date() == BIRTH_DT.date()  # A32


# ─────────────────────────────────────────────────────────────────────────────
# §6 — Naisargika
# ─────────────────────────────────────────────────────────────────────────────

def test_naisargika_sequence_7_planets():
    """Naisargika has 7 planets."""
    assert len(NAISARGIKA_SEQUENCE) == 7  # A33

def test_naisargika_first_is_moon():
    """Naisargika starts with Moon (1 year)."""
    assert NAISARGIKA_SEQUENCE[0] == ("Moon", 1)  # A34

def test_naisargika_last_is_saturn():
    """Naisargika ends with Saturn (50 years)."""
    assert NAISARGIKA_SEQUENCE[-1] == ("Saturn", 50)  # A35

def test_naisargika_compute_7_periods():
    """compute_naisargika_sequence returns 7 main periods."""
    seq = compute_naisargika_sequence(BIRTH_DT)
    assert len(seq) == 7  # A36

def test_naisargika_total_duration():
    """Naisargika total duration ≈ 120 years."""
    seq       = compute_naisargika_sequence(BIRTH_DT)
    first_dt  = _parse_iso(seq[0]["start_iso"])
    last_dt   = _parse_iso(seq[-1]["end_iso"])
    total_yrs = (last_dt - first_dt).days / 365.25
    assert abs(total_yrs - 120) < 1.0  # A37


# ─────────────────────────────────────────────────────────────────────────────
# §7 — Mudda
# ─────────────────────────────────────────────────────────────────────────────

def test_mudda_days_sum_365():
    """Mudda days sum to exactly 365."""
    assert sum(MUDDA_DAYS.values()) == 365  # A38

def test_mudda_for_year_returns_9():
    """compute_mudda_for_year returns 9 periods."""
    year_start = datetime(1984, 1, 1, tzinfo=timezone.utc)
    periods    = compute_mudda_for_year("Jupiter", year_start)
    assert len(periods) == 9  # A39

def test_mudda_for_year_sum_365_days():
    """Mudda year total duration = 365 days."""
    year_start = datetime(1984, 1, 1, tzinfo=timezone.utc)
    periods    = compute_mudda_for_year("Ketu", year_start)
    total_days = sum(p["duration_days"] for p in periods)
    assert abs(total_days - 365.0) < 0.01  # A40

def test_mudda_for_year_first_lord_matches_start():
    """Mudda starting lord = mahadasha lord passed in."""
    year_start = datetime(1984, 1, 1, tzinfo=timezone.utc)
    periods    = compute_mudda_for_year("Saturn", year_start)
    assert periods[0]["lord"] == "Saturn"  # A41


# ─────────────────────────────────────────────────────────────────────────────
# §8 — Row collection functions (no DB)
# ─────────────────────────────────────────────────────────────────────────────

def test_collect_vimshottari_rows_positive():
    """Vimshottari row collection returns > 0 rows."""
    rows = _collect_vimshottari_rows(
        CHART_ID, AYA_ID, BUILD_ID, _make_maha_seq()
    )
    assert len(rows) > 0  # A42

def test_collect_vimshottari_rows_contains_sookshma():
    """Vimshottari rows include sookshma-level entries."""
    rows = _collect_vimshottari_rows(
        CHART_ID, AYA_ID, BUILD_ID, _make_maha_seq()
    )
    # fact_key is the 11th column (index 10) in the tuple: "period_{level}"
    levels = {r[10] for r in rows}  # fact_key column
    assert "period_sookshma" in levels  # A43
    assert "period_maha"     in levels  # A44
    assert "period_antar"    in levels  # A45
    assert "period_pratyantar" in levels  # A46

def test_collect_yogini_rows_positive():
    """Yogini rows > 0."""
    rows = _collect_yogini_rows(
        CHART_ID, AYA_ID, BUILD_ID, 22, 5.0, BIRTH_DT
    )
    assert len(rows) > 0  # A47

def test_collect_ashtottari_rows_positive():
    """Ashtottari rows > 0."""
    rows = _collect_ashtottari_rows(
        CHART_ID, AYA_ID, BUILD_ID, 1, 0.0, BIRTH_DT
    )
    assert len(rows) > 0  # A48

def test_collect_naisargika_rows_count():
    """Naisargika rows include main + antar levels."""
    rows = _collect_naisargika_rows(
        CHART_ID, AYA_ID, BUILD_ID, BIRTH_DT
    )
    levels = {r[10] for r in rows}
    assert "period_maha"  in levels  # A49
    assert "period_antar" in levels  # A50

def test_collect_mudda_rows_multiple_years():
    """Mudda rows span multiple years (>>9)."""
    rows = _collect_mudda_rows(
        CHART_ID, AYA_ID, BUILD_ID, BIRTH_DT, _make_maha_seq()
    )
    assert len(rows) > 100  # A51  (9 periods × many years)

def test_collect_jaimini_chara_rows_positive():
    """Jaimini Chara rows > 0."""
    rows = _collect_jaimini_chara_rows(
        CHART_ID, AYA_ID, BUILD_ID,
        BIRTH_DT, "Scorpio",
        [{"name": "Jupiter", "longitude": 240.0, "sign": "Sagittarius"}],
    )
    assert len(rows) > 0  # A52

def test_collect_kalachakra_rows_positive():
    """Kalachakra rows > 0."""
    rows = _collect_kalachakra_rows(
        CHART_ID, AYA_ID, BUILD_ID, BIRTH_DT, 295.0
    )
    assert len(rows) > 0  # A53


# ─────────────────────────────────────────────────────────────────────────────
# §9 — Row tuple structure
# ─────────────────────────────────────────────────────────────────────────────

def test_row_tuple_length():
    """Every generated row tuple has the expected 21-column structure."""
    rows = _collect_vimshottari_rows(
        CHART_ID, AYA_ID, BUILD_ID, _make_maha_seq()[:1]  # Just first maha
    )
    for row in rows[:5]:  # Spot-check first 5
        assert len(row) == 21, f"Expected 21 columns, got {len(row)}"  # A54

def test_row_fact_value_jsonb_is_valid_json():
    """fact_value_jsonb column (index 13) is valid JSON."""
    rows = _collect_vimshottari_rows(
        CHART_ID, AYA_ID, BUILD_ID, _make_maha_seq()[:1]
    )
    assert len(rows) > 0
    for row in rows[:3]:
        jsonb_val = row[13]
        parsed = json.loads(jsonb_val)  # Must not raise
        assert isinstance(parsed, dict)  # A55

def test_row_fact_id_is_16_chars():
    """fact_id (index 0) is exactly 16 hex chars."""
    rows = _collect_vimshottari_rows(
        CHART_ID, AYA_ID, BUILD_ID, _make_maha_seq()[:1]
    )
    for row in rows[:5]:
        assert len(row[0]) == 16  # A56

def test_row_fact_category_prefix():
    """fact_category (index 8) starts with 'dasha_'."""
    rows = _collect_vimshottari_rows(
        CHART_ID, AYA_ID, BUILD_ID, _make_maha_seq()[:1]
    )
    for row in rows[:5]:
        assert row[8].startswith("dasha_")  # A57


# ─────────────────────────────────────────────────────────────────────────────
# §10 — Helper extraction functions
# ─────────────────────────────────────────────────────────────────────────────

def test_extract_moon_data_from_standard_grahas():
    """_extract_moon_data correctly extracts nakshatra_id and degree."""
    grahas = [
        {"name": "Moon", "longitude": 295.0, "nakshatra_id": 22},
        {"name": "Sun",  "longitude": 292.0},
    ]
    nak_id, deg_in_nak, lon = _extract_moon_data(grahas)
    assert nak_id == 22  # A58
    assert abs(lon - 295.0) < 0.01  # A59

def test_extract_moon_data_fallback():
    """_extract_moon_data falls back gracefully when Moon not found."""
    nak_id, deg_in_nak, lon = _extract_moon_data([])
    assert nak_id >= 1  # A60
    assert nak_id <= 27  # A61

def test_extract_lagna_sign():
    """_extract_lagna_sign extracts sign from chart_output."""
    co = {"lagna": {"sign": "Scorpio"}}
    assert _extract_lagna_sign(co) == "Scorpio"  # A62

def test_extract_birth_dt():
    """_extract_birth_dt returns a tz-aware datetime."""
    co  = {"birth_datetime": "1984-02-05T05:13:00+00:00"}
    dt  = _extract_birth_dt(co)
    assert dt.tzinfo is not None  # A63
    assert dt.year == 1984  # A64
    assert dt.month == 2  # A65


# ─────────────────────────────────────────────────────────────────────────────
# §11 — write() function (conn=None dry-run)
# ─────────────────────────────────────────────────────────────────────────────

def test_write_returns_positive_count_conn_none():
    """write() with conn=None returns > 0 (dry-run row count)."""
    co    = _make_chart_output(moon_nakshatra_id=22, moon_deg_in_nak=5.0, moon_lon=295.0)
    count = write(BUILD_ID, CHART_ID, AYA_ID, co, conn=None)
    assert count > 0  # A66

def test_write_returns_large_count_for_full_chart():
    """write() with full mahadasha_sequence returns > 1000 rows."""
    co    = _make_chart_output(moon_nakshatra_id=14, moon_deg_in_nak=3.0, moon_lon=176.0)
    count = write(BUILD_ID, CHART_ID, AYA_ID, co, conn=None)
    assert count > 1000  # A67 — Vimshottari alone is thousands of rows

def test_write_with_empty_maha_seq():
    """write() with no mahadasha_sequence still writes non-Vimshottari rows."""
    co = {
        "birth_datetime": BIRTH_DT.isoformat(),
        "lagna": {"sign": "Scorpio"},
        "dashas": {"system": "vimshottari", "mahadasha_sequence": []},
        "grahas": [{"name": "Moon", "longitude": 295.0, "nakshatra_id": 22}],
    }
    count = write(BUILD_ID, CHART_ID, AYA_ID, co, conn=None)
    assert count > 0  # A68 — Yogini + Naisargika + others still produce rows

def test_write_different_ayanamshas_produce_same_count():
    """write() row count should be consistent across ayanamshas (same birth)."""
    co     = _make_chart_output()
    count1 = write(BUILD_ID, CHART_ID, "lahiri",   co, conn=None)
    count2 = write(BUILD_ID, CHART_ID, "krishnamurti", co, conn=None)
    # Counts should be equal (same computation, different ayanamsha_id label)
    assert count1 == count2  # A69

def test_write_all_7_systems_contribute():
    """Verify that each of the 7 systems generates at least 1 row."""
    co = _make_chart_output()
    # Use collect functions individually
    rows_vimsh  = _collect_vimshottari_rows(CHART_ID, AYA_ID, BUILD_ID, _make_maha_seq())
    rows_yogini = _collect_yogini_rows(CHART_ID, AYA_ID, BUILD_ID, 22, 5.0, BIRTH_DT)
    rows_ash    = _collect_ashtottari_rows(CHART_ID, AYA_ID, BUILD_ID, 22, 5.0, BIRTH_DT)
    rows_nais   = _collect_naisargika_rows(CHART_ID, AYA_ID, BUILD_ID, BIRTH_DT)
    rows_mudda  = _collect_mudda_rows(CHART_ID, AYA_ID, BUILD_ID, BIRTH_DT, _make_maha_seq())
    rows_jaim   = _collect_jaimini_chara_rows(CHART_ID, AYA_ID, BUILD_ID, BIRTH_DT, "Scorpio", [])
    rows_kc     = _collect_kalachakra_rows(CHART_ID, AYA_ID, BUILD_ID, BIRTH_DT, 295.0)

    assert len(rows_vimsh)  > 0  # A70
    assert len(rows_yogini) > 0  # A71
    assert len(rows_ash)    > 0  # A72
    assert len(rows_nais)   > 0  # A73
    assert len(rows_mudda)  > 0  # A74
    assert len(rows_jaim)   > 0  # A75
    assert len(rows_kc)     > 0  # A76


# ─────────────────────────────────────────────────────────────────────────────
# §12 — Chronological ordering and continuity
# ─────────────────────────────────────────────────────────────────────────────

def test_vimshottari_maha_periods_are_chronological():
    """Mahadasha periods in a maha_seq must be chronologically ordered."""
    seq = _make_maha_seq()
    for i in range(len(seq) - 1):
        end_i    = _parse_iso(seq[i]["end_iso"])
        start_i1 = _parse_iso(seq[i + 1]["start_iso"])
        assert abs((end_i - start_i1).total_seconds()) < 1.0  # A77 — contiguous

def test_naisargika_sequence_contiguous():
    """Naisargika periods must be contiguous."""
    seq = compute_naisargika_sequence(BIRTH_DT)
    for i in range(len(seq) - 1):
        end_i    = _parse_iso(seq[i]["end_iso"])
        start_i1 = _parse_iso(seq[i + 1]["start_iso"])
        assert abs((end_i - start_i1).total_seconds()) < 1.0  # A78

def test_yogini_sequence_contiguous():
    """Yogini main periods must be contiguous."""
    seq = compute_yogini_sequence(5, 3.0, BIRTH_DT)
    for i in range(min(10, len(seq) - 1)):
        end_i    = _parse_iso(seq[i]["end_iso"])
        start_i1 = _parse_iso(seq[i + 1]["start_iso"])
        assert abs((end_i - start_i1).total_seconds()) < 1.0  # A79


# ─────────────────────────────────────────────────────────────────────────────
# §13 — Window filter
# ─────────────────────────────────────────────────────────────────────────────

def test_vimshottari_rows_within_window():
    """All Vimshottari rows have periods overlapping 1950-2100 window."""
    from pipeline.writers.dashas_writer import WINDOW_START, WINDOW_END
    rows = _collect_vimshottari_rows(CHART_ID, AYA_ID, BUILD_ID, _make_maha_seq())
    for row in rows:
        period_data = json.loads(row[13])
        start = _parse_iso(period_data["start_iso"])
        end   = _parse_iso(period_data["end_iso"])
        # Must overlap [WINDOW_START, WINDOW_END]
        assert end > WINDOW_START and start < WINDOW_END  # A80
