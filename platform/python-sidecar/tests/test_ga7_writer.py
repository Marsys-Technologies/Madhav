"""
test_ga7_writer.py — GA7 dasha writer unit tests
=================================================
Tests for ga_writers.ga_dashas_writer — all 7 dasha systems.
NO DB required — uses mock PyJHora APIs and skip_db=True.

Test coverage:
  1.  CANONICAL_CHART_ID constant correct
  2.  SYSTEMS list has 7 entries
  3.  AYANAMSHAS list has 5 entries
  4.  VIMSHOTTARI_TOTAL_YEARS = 120
  5.  YOGINI_TOTAL_YEARS = 36
  6.  ASHTOTTARI_TOTAL_YEARS = 108
  7.  NAISARGIKA_TOTAL_YEARS = 120
  8.  WINDOW_START = 1950-01-01, WINDOW_END = 2100-12-31
  9.  FORENSIC_VIMSHOTTARI_STARTING_LORD = 'Jupiter'
  10. FORENSIC_MOON_NAK_NAME = 'Purva Bhadrapada'
  11. compute_vimshottari returns rows with level_n in [1,2,3,4] only
  12. compute_vimshottari: ZERO level_n=5 rows (CRITICAL OVERRIDE 1)
  13. compute_vimshottari: starting lord = Jupiter (FORENSIC anchor)
  14. compute_vimshottari: Maha sequence starts with Jupiter
  15. compute_vimshottari: all level_n=1 lords in VIMSHOTTARI_SEQUENCE
  16. compute_vimshottari: all start_date < end_date
  17. compute_vimshottari: all start_date >= WINDOW_START
  18. compute_vimshottari: all end_date <= WINDOW_END
  19. compute_vimshottari: FORENSIC halt on wrong starting lord
  20. KP subperiods: kp_sublevel='sub' rows present for vimshottari L1
  21. KP subperiods: kp_sublevel='sub_sub' rows present
  22. KP subperiods: NO level_n=6 or level_n=7 rows (CRITICAL OVERRIDE 2)
  23. KP subperiods: kp_sub_lord populated on kp_sublevel='sub' rows
  24. KP subperiods: kp_sub_sub_lord populated on kp_sublevel='sub_sub' rows
  25. compute_yogini: all lords in YOGINI_SEQUENCE names
  26. compute_yogini: period_deity_or_marker populated
  27. compute_yogini: level_n in [1,2,3,4] only
  28. compute_yogini: ZERO level_n=5
  29. compute_ashtottari: all lords in ASHTOTTARI_LORDS_ORDER
  30. compute_ashtottari: level_n in [1,2,3,4] only
  31. compute_ashtottari: ZERO level_n=5
  32. compute_ashtottari: applies_to_this_chart_flag = True (Rahu in 5H)
  33. compute_chara: all level_n=1 lords are sign names
  34. compute_chara: level_n in [1,2,3,4] only
  35. compute_naisargika: lords in NAISARGIKA_SEQUENCE lords
  36. compute_naisargika: level_n in [1,2,3,4] only
  37. compute_mudda: hybrid storage — rows in [1984, 2031] range
  38. compute_mudda: varsha_year_lord populated on all rows
  39. compute_mudda: NOT full 150y (no rows past 2032)
  40. compute_mudda: level_n in [1,2,3,4] only
  41. compute_kalachakra: all level_n=1 lords are sign names
  42. compute_kalachakra: level_n in [1,2,3,4] only
  43. compute_kalachakra: anchored_solar_return_iso populated on L1 rows
  44. compute_kalachakra: period_deity_or_marker populated
  45. Addition A: lord_natal_house_d1 populated (not None for known lords)
  46. Addition A: lord_natal_sign populated
  47. Addition A: lord_natal_nakshatra populated
  48. Addition A: lord_natal_dignity_d1 populated
  49. Addition B: sandhi_with_next_dasha_lord populated on non-last L1 rows
  50. Addition B: next_dasha_start_iso populated on non-last L1 rows
  51. Addition C+D: concurrent_system_lords_jsonb = None before post-pass
  52. Addition E: applies_to_this_chart_flag is bool
  53. Addition F: period_deity_or_marker populated for yogini/kalachakra
  54. Addition G: lord_to_parent_relationship in {friend,enemy,neutral,None}
  55. Addition H: varsha_year_lord populated on mudda rows
  56. Addition I: anchored_solar_return_iso populated on kalachakra L1 rows
  57. Addition J (R6 0e-dashameta / V-11): triggered_yogas_jsonb_atomic column dropped
  58. Addition K (R6 0e-dashameta / V-11): lord_transit_at_period_start_jsonb column dropped
  59. Addition Q: karakas_active_during_period is list or None
  60. JSONB: only 1 sanctioned JSONB column non-None for non-kp rows (post V-11 drop)
  61. algebraic invariant: Vimshottari L1 lords match VIMSHOTTARI_SEQUENCE
  62. algebraic invariant: Yogini L1 lords follow YOGINI_SEQUENCE cycle
  63. algebraic invariant: Ashtottari L1 lords follow ASHTOTTARI_SEQUENCE
  64. algebraic invariant: Naisargika L1 lords match NAISARGIKA_SEQUENCE
  65. build_system (skip_db): returns dict with status=PASS for vimshottari
  66. build_system (skip_db): rows_computed > 0
  67. build_system: raises ValueError for unknown system_id
  68. build_system: FORENSIC halt propagated if starting lord wrong
  69. SYSTEMS constant: contains all 7 required system ids
  70. citation_ref format: starts with 'chart_dashas.'
  71. citation_human format: non-empty string
  72. verification_pass_status: all rows have valid status
"""
from __future__ import annotations

import json
import unittest
from datetime import date, datetime, timedelta
from typing import Any
from unittest.mock import MagicMock, patch


# ── Import the writer ─────────────────────────────────────────────────────────

def _get_mod():
    from ga_writers import ga_dashas_writer as mod
    return mod


# ── Fixtures: mock Moon position for FORENSIC native ─────────────────────────

# Purva Bhadrapada occupies degrees 320-333.33° sidereal (nak 25, 0-indexed 24)
# nak_idx_0 = 24, so nak_idx_1 = 25 → lord = Jupiter (FORENSIC)
FORENSIC_MOON_LON = 325.5  # degrees, within Purva Bhadrapada

# Birth JD (approximate for 1984-02-05 10:43 UTC-5:30)
import swisseph as _swe
BIRTH_JD = _swe.julday(1984, 2, 5, 5.21667)  # 10:43 IST = 05:13 UTC

# Minimal birth_params required by resolve_birth_params() (B1 elimination — no native fallback)
NATIVE_BIRTH_PARAMS = {
    "datetime_iso": "1984-02-05T10:43:00",
    "latitude_deg": 20.2961,
    "longitude_deg": 85.8245,
    "tz_offset_hours": 5.5,
    "place_name": "Bhubaneswar",
    "subject_label": "abhisek_mohanty_native",
}


def _mock_get_moon_position(ayanamsha_id: str, birth: dict | None = None):
    """Return FORENSIC Moon position for all ayanamshas."""
    return FORENSIC_MOON_LON, BIRTH_JD


# ── Mock chart_facts connection for chara_karaka (M-7 fix) ───────────────────
# compute_chara_system() now REQUIRES a real chart_facts derivation (no
# NATIVE-hardcoded fallback — MARSYS_DEFECT_GAP_REGISTER_v2_0.md M-7). This
# test suite stays "NO DB required" by mocking chart_facts rows directly,
# same pattern as _mock_get_moon_position above mocks the ephemeris call.
#
# fact_subject uses the REAL abbreviated uppercase codes chart_facts actually
# stores (SUN, MOON, MAR, MER, JUP, VEN, SAT) — NOT full names. A prior
# version of this mock used full names ("Sun", "Moon", ...), which was
# self-consistently wrong with a matching bug in the writer's query and
# never caught the Ring-2-found regression (writer filtered on full names
# against a table keyed by codes, matching zero rows on every real chart).
# Values below are the REAL chart_facts rows for chart_id=482012f1,
# ayanamsha_id=lahiri_chitrapaksha (read-only verification query, r6/0f
# session) — reused here only as realistic mock input, not a live fallback.
_MOCK_CHART_FACTS_CHARA_ROWS = [
    ("SUN", "sign", "Capricorn", None), ("SUN", "degree_in_sign", None, 21.9626172849916),
    ("MOON", "sign", "Aquarius", None), ("MOON", "degree_in_sign", None, 27.055230133129),
    ("MAR", "sign", "Libra", None), ("MAR", "degree_in_sign", None, 18.5191875546223),
    ("MER", "sign", "Capricorn", None), ("MER", "degree_in_sign", None, 0.838753918698387),
    ("JUP", "sign", "Sagittarius", None), ("JUP", "degree_in_sign", None, 9.78749702318149),
    ("VEN", "sign", "Sagittarius", None), ("VEN", "degree_in_sign", None, 19.1726960894562),
    ("SAT", "sign", "Libra", None), ("SAT", "degree_in_sign", None, 22.4319860591954),
]


def _mock_chart_facts_conn(rows: list[tuple]) -> Any:
    """Minimal fake DB connection satisfying ga_dashas_writer's
    _compute_dynamic_chara_params (conn.cursor() as cur: cur.execute(...);
    cur.fetchall())."""

    class _Cur:
        def execute(self, *_a, **_k):
            pass

        def fetchall(self):
            return rows

        def __enter__(self):
            return self

        def __exit__(self, *_a):
            return False

    class _Conn:
        def cursor(self, **_kwargs):
            # Accept (and ignore) row_factory=... — the real writer now forces
            # tuple_row explicitly (2026-07-10 fix for the dict_row-unpack bug);
            # this mock always returns tuples regardless, matching that contract.
            return _Cur()

    return _Conn()


# ── Helper: compute a system with mocked Moon ────────────────────────────────

def _compute_system_rows(system_id: str, limit_cycles: bool = True) -> list[dict]:
    """
    Compute rows for a system using FORENSIC mock Moon position.
    Returns row list (no DB).
    """
    mod = _get_mod()
    moon_sid = FORENSIC_MOON_LON
    birth_jd = BIRTH_JD
    chart_id = mod.CANONICAL_CHART_ID
    build_id = "test-build-00000000-0000-0000-0000-000000000000"
    aya = "lahiri"

    if system_id == "vimshottari":
        rows = mod.compute_vimshottari(moon_sid, birth_jd, aya, chart_id, build_id)
    elif system_id == "yogini":
        rows = mod.compute_yogini_system(moon_sid, birth_jd, aya, chart_id, build_id)
    elif system_id == "ashtottari":
        rows = mod.compute_ashtottari_system(moon_sid, birth_jd, aya, chart_id, build_id)
    elif system_id == "chara_karaka":
        rows = mod.compute_chara_system(
            birth_jd, aya, chart_id, build_id,
            conn=_mock_chart_facts_conn(_MOCK_CHART_FACTS_CHARA_ROWS),
        )
    elif system_id == "naisargika":
        rows = mod.compute_naisargika_system(birth_jd, aya, chart_id, build_id)
    elif system_id == "mudda":
        rows = mod.compute_mudda_system(birth_jd, aya, chart_id, build_id)
    elif system_id == "kalachakra":
        rows = mod.compute_kalachakra_system(moon_sid, birth_jd, aya, chart_id, build_id)
    else:
        raise ValueError(f"Unknown system: {system_id}")
    return rows


# ══════════════════════════════════════════════════════════════════════════════
# Test classes
# ══════════════════════════════════════════════════════════════════════════════

class TestConstants(unittest.TestCase):
    """Tests 1-10: module-level constants."""

    def test_01_canonical_chart_id(self):
        mod = _get_mod()
        assert mod.CANONICAL_CHART_ID == "482012f1-710e-4a25-994a-93821f5871aa"

    def test_02_systems_seven(self):
        mod = _get_mod()
        assert len(mod.SYSTEMS) == 7

    def test_03_ayanamshas_five(self):
        mod = _get_mod()
        assert len(mod.AYANAMSHAS) == 5

    def test_04_vimshottari_total_120(self):
        mod = _get_mod()
        assert mod.VIMSHOTTARI_TOTAL_YEARS == 120

    def test_05_yogini_total_36(self):
        mod = _get_mod()
        assert mod.YOGINI_TOTAL_YEARS == 36

    def test_06_ashtottari_total_108(self):
        mod = _get_mod()
        assert mod.ASHTOTTARI_TOTAL_YEARS == 108

    def test_07_naisargika_total_120(self):
        mod = _get_mod()
        assert mod.NAISARGIKA_TOTAL_YEARS == 120

    def test_08_window_dates(self):
        mod = _get_mod()
        assert mod.WINDOW_START == date(1950, 1, 1)
        assert mod.WINDOW_END == date(2100, 12, 31)

    def test_09_forensic_starting_lord_jupiter(self):
        mod = _get_mod()
        assert mod.FORENSIC_VIMSHOTTARI_STARTING_LORD == "Jupiter"

    def test_10_forensic_moon_nak(self):
        mod = _get_mod()
        assert mod.FORENSIC_MOON_NAK_NAME == "Purva Bhadrapada"

    def test_69_systems_contains_all_7(self):
        mod = _get_mod()
        expected = {
            "vimshottari", "yogini", "ashtottari",
            "chara_karaka", "naisargika", "mudda", "kalachakra",
        }
        assert set(mod.SYSTEMS) == expected


class TestVimshottariSystem(unittest.TestCase):
    """Tests 11-19: Vimshottari computation."""

    @classmethod
    def setUpClass(cls):
        cls.rows = _compute_system_rows("vimshottari")

    def test_11_level_n_in_1_to_4_only(self):
        """CRITICAL OVERRIDE 1: all level_n in {1,2,3,4}."""
        for r in self.rows:
            if r.get("kp_sublevel") is None:
                assert r["level_n"] in (1, 2, 3, 4), (
                    f"level_n={r['level_n']} found (max=4 enforced)"
                )

    def test_12_zero_level_n_5(self):
        """CRITICAL OVERRIDE 1: ZERO level_n=5 rows."""
        level5 = [r for r in self.rows if r["level_n"] == 5]
        assert len(level5) == 0, f"Found {len(level5)} level_n=5 rows — CRITICAL OVERRIDE violated"

    def test_13_starting_lord_jupiter(self):
        """FORENSIC: Vimshottari starting lord = Jupiter."""
        l1_rows = [r for r in self.rows if r["level_n"] == 1 and r.get("kp_sublevel") is None]
        assert len(l1_rows) > 0
        # The L1 row covering birth (1984-02-05) must have lord = Jupiter
        birth = date(1984, 2, 5)
        birth_period = None
        for r in l1_rows:
            if r["start_date"] <= birth <= r["end_date"]:
                birth_period = r
                break
        assert birth_period is not None, "No L1 row covers birth date"
        assert birth_period["lord_graha"] == "Jupiter", (
            f"Starting lord at birth = {birth_period['lord_graha']!r}, expected 'Jupiter'"
        )

    def test_14_maha_sequence_starts_jupiter(self):
        """FORENSIC: First L1 row at or before birth must be Jupiter."""
        mod = _get_mod()
        l1_rows = sorted(
            [r for r in self.rows if r["level_n"] == 1 and r.get("kp_sublevel") is None],
            key=lambda r: r["start_date"],
        )
        birth = date(1984, 2, 5)
        # Find the first L1 period that covers birth
        for r in l1_rows:
            if r["start_date"] <= birth <= r["end_date"]:
                assert r["lord_graha"] == "Jupiter"
                return
        assert False, "No L1 period covers birth date"

    def test_15_all_l1_lords_in_sequence(self):
        mod = _get_mod()
        l1_rows = [r for r in self.rows if r["level_n"] == 1 and r.get("kp_sublevel") is None]
        for r in l1_rows:
            assert r["lord_graha"] in mod.VIMSHOTTARI_SEQUENCE, (
                f"Unexpected lord: {r['lord_graha']!r}"
            )

    def test_16_start_before_end(self):
        for r in self.rows:
            assert r["start_date"] < r["end_date"], (
                f"start_date >= end_date for {r['lord_graha']} {r['start_date']}"
            )

    def test_17_all_start_gte_window_start(self):
        mod = _get_mod()
        for r in self.rows:
            assert r["start_date"] >= mod.WINDOW_START, (
                f"start_date {r['start_date']} < WINDOW_START"
            )

    def test_18_all_end_lte_window_end(self):
        mod = _get_mod()
        for r in self.rows:
            assert r["end_date"] <= mod.WINDOW_END, (
                f"end_date {r['end_date']} > WINDOW_END"
            )

    def test_19_forensic_halt_wrong_lord(self):
        """FORENSIC halt: wrong starting lord raises ValueError."""
        mod = _get_mod()
        # Moon in Ashwini (0°) → lord = Ketu (not Jupiter)
        wrong_moon_sid = 2.0  # Ashwini, lord = Ketu
        with self.assertRaises(ValueError) as ctx:
            mod.compute_vimshottari(
                wrong_moon_sid, BIRTH_JD, "lahiri",
                mod.CANONICAL_CHART_ID, "test-build",
            )
        assert "FORENSIC HALT" in str(ctx.exception)


class TestKPSubperiods(unittest.TestCase):
    """Tests 20-24: KP sub-period dimension (CRITICAL OVERRIDE 2)."""

    @classmethod
    def setUpClass(cls):
        mod = _get_mod()
        cls.vim_rows = _compute_system_rows("vimshottari")
        cls.kp_rows = mod.compute_kp_subperiods(
            cls.vim_rows,
            mod.CANONICAL_CHART_ID,
            "test-build",
            "lahiri",
        )

    def test_20_kp_sub_rows_present(self):
        sub_rows = [r for r in self.kp_rows if r.get("kp_sublevel") == "sub"]
        assert len(sub_rows) > 0, "No KP sub rows found"

    def test_21_kp_sub_sub_rows_present(self):
        sub_sub_rows = [r for r in self.kp_rows if r.get("kp_sublevel") == "sub_sub"]
        assert len(sub_sub_rows) > 0, "No KP sub-sub rows found"

    def test_22_no_level_n_6_or_7(self):
        """CRITICAL OVERRIDE 2: KP rows must NOT use level_n=6 or 7."""
        for r in self.kp_rows:
            assert r["level_n"] not in (6, 7), (
                f"KP row has level_n={r['level_n']} — CRITICAL OVERRIDE 2 violated"
            )

    def test_23_kp_sub_lord_populated(self):
        sub_rows = [r for r in self.kp_rows if r.get("kp_sublevel") == "sub"]
        for r in sub_rows:
            assert r.get("kp_sub_lord") is not None, (
                f"kp_sub_lord is None on kp_sublevel='sub' row"
            )

    def test_24_kp_sub_sub_lord_populated(self):
        sub_sub_rows = [r for r in self.kp_rows if r.get("kp_sublevel") == "sub_sub"]
        for r in sub_sub_rows:
            assert r.get("kp_sub_sub_lord") is not None, (
                f"kp_sub_sub_lord is None on kp_sublevel='sub_sub' row"
            )

    def test_25_classical_and_kp_rows_collide_on_level_n_start_iso_alone(self):
        """
        Regression capture (BA-P3 FIX 2b, migration 414): a KP sub-period
        always begins exactly when its parent classical period begins, so it
        legitimately shares (level_n, start_iso) with a classical Antardasha/
        Pratyantardasha row. (level_n, start_iso) alone is NOT a valid natural
        key across vimshottari + KP rows — this documents that fact so nobody
        reintroduces a bulk-insert path keyed on it alone (chart_dashas'
        DB-level unique index must include kp_sublevel; see migration 414).
        """
        all_rows = self.vim_rows + self.kp_rows
        old_keys = [(r["level_n"], r["start_iso"]) for r in all_rows]
        collisions = len(old_keys) - len(set(old_keys))
        assert collisions > 0, (
            "expected classical/KP rows to collide on (level_n, start_iso) alone "
            "for this fixture — if this no longer collides, the underlying "
            "algorithm changed and migration 414 / this regression test should "
            "be revisited"
        )

    def test_26_classical_and_kp_rows_are_distinct_under_full_natural_key(self):
        """The natural key chart_dashas actually enforces (migration 414):
        (chart_id, ayanamsha_id, system_id, level_n, start_iso, build_id,
        COALESCE(kp_sublevel, '')) — must have zero collisions."""
        all_rows = self.vim_rows + self.kp_rows
        new_keys = [
            (r["level_n"], r["start_iso"], r.get("kp_sublevel") or "")
            for r in all_rows
        ]
        collisions = len(new_keys) - len(set(new_keys))
        assert collisions == 0, (
            f"{collisions} row(s) collide even under the corrected natural key "
            "(level_n, start_iso, kp_sublevel) — a real duplicate, not just the "
            "classical/KP overlap migration 414 fixes"
        )


class TestYoginiSystem(unittest.TestCase):
    """Tests 25-28: Yogini system."""

    @classmethod
    def setUpClass(cls):
        cls.rows = _compute_system_rows("yogini")

    def test_25_all_lords_in_yogini_sequence(self):
        mod = _get_mod()
        yogini_names = {name for name, _, _ in mod.YOGINI_SEQUENCE}
        l1_rows = [r for r in self.rows if r["level_n"] == 1]
        for r in l1_rows:
            assert r["lord_graha"] in yogini_names, (
                f"Unexpected Yogini lord: {r['lord_graha']!r}"
            )

    def test_26_period_deity_populated(self):
        l1_rows = [r for r in self.rows if r["level_n"] == 1]
        for r in l1_rows:
            assert r.get("period_deity_or_marker") is not None, (
                f"period_deity_or_marker None on Yogini L1 row"
            )

    def test_27_level_n_in_1_to_4(self):
        for r in self.rows:
            assert r["level_n"] in (1, 2, 3, 4)

    def test_28_zero_level_n_5(self):
        level5 = [r for r in self.rows if r["level_n"] == 5]
        assert len(level5) == 0


class TestAshtottariSystem(unittest.TestCase):
    """Tests 29-32: Ashtottari system."""

    @classmethod
    def setUpClass(cls):
        cls.rows = _compute_system_rows("ashtottari")

    def test_29_all_lords_in_ashtottari_order(self):
        mod = _get_mod()
        known = set(mod.ASHTOTTARI_LORDS_ORDER)
        l1_rows = [r for r in self.rows if r["level_n"] == 1]
        for r in l1_rows:
            assert r["lord_graha"] in known, (
                f"Unexpected Ashtottari lord: {r['lord_graha']!r}"
            )

    def test_30_level_n_in_1_to_4(self):
        for r in self.rows:
            assert r["level_n"] in (1, 2, 3, 4)

    def test_31_zero_level_n_5(self):
        level5 = [r for r in self.rows if r["level_n"] == 5]
        assert len(level5) == 0

    def test_32_applies_to_chart_flag_true(self):
        """FORENSIC: Rahu in 5H → Ashtottari applicable."""
        for r in self.rows:
            assert r["applies_to_this_chart_flag"] is True


class TestCharaSystem(unittest.TestCase):
    """Tests 33-34: Chara Karaka system."""

    @classmethod
    def setUpClass(cls):
        cls.rows = _compute_system_rows("chara_karaka")

    def test_33_all_l1_lords_are_sign_names(self):
        sign_names = {
            "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
            "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
        }
        l1_rows = [r for r in self.rows if r["level_n"] == 1]
        assert len(l1_rows) > 0
        for r in l1_rows:
            assert r["lord_graha"] in sign_names, (
                f"Chara lord {r['lord_graha']!r} not a sign name"
            )

    def test_34_level_n_in_1_to_4(self):
        for r in self.rows:
            assert r["level_n"] in (1, 2, 3, 4)


class TestNaisargikaSystem(unittest.TestCase):
    """Tests 35-36: Naisargika system."""

    @classmethod
    def setUpClass(cls):
        cls.rows = _compute_system_rows("naisargika")

    def test_35_lords_in_naisargika_sequence(self):
        mod = _get_mod()
        known = {lord for lord, _ in mod.NAISARGIKA_SEQUENCE}
        l1_rows = [r for r in self.rows if r["level_n"] == 1]
        for r in l1_rows:
            assert r["lord_graha"] in known, (
                f"Naisargika lord {r['lord_graha']!r} not in sequence"
            )

    def test_36_level_n_in_1_to_4(self):
        for r in self.rows:
            assert r["level_n"] in (1, 2, 3, 4)


class TestMuddaSystem(unittest.TestCase):
    """Tests 37-40: Mudda (Tajik annual) hybrid storage."""

    @classmethod
    def setUpClass(cls):
        cls.rows = _compute_system_rows("mudda")

    def test_37_hybrid_storage_rows_in_range(self):
        """Hybrid: rows cover 1984-2031 (past+current+next-5y)."""
        l1_rows = [r for r in self.rows if r["level_n"] == 1]
        assert len(l1_rows) > 0, "No Mudda L1 rows"
        dates = [r["start_date"] for r in l1_rows]
        # Must have rows starting from ~1984 (birth year)
        assert any(d.year >= 1984 and d.year <= 1985 for d in dates), (
            "No Mudda rows near birth year 1984"
        )

    def test_38_varsha_year_lord_populated(self):
        """Addition H: varsha_year_lord populated on all Mudda rows."""
        for r in self.rows:
            assert r.get("varsha_year_lord") is not None, (
                f"varsha_year_lord None on Mudda row level_n={r['level_n']}"
            )

    def test_39_not_full_150y(self):
        """Hybrid storage: no rows past 2032."""
        for r in self.rows:
            assert r["start_date"].year <= 2032, (
                f"Mudda row starts {r['start_date']} — past hybrid window (2031)"
            )

    def test_40_level_n_in_1_to_4(self):
        for r in self.rows:
            assert r["level_n"] in (1, 2, 3, 4)


class TestKalachakraSystem(unittest.TestCase):
    """Tests 41-44: Kalachakra system."""

    @classmethod
    def setUpClass(cls):
        cls.rows = _compute_system_rows("kalachakra")

    def test_41_all_l1_lords_are_sign_names(self):
        sign_names = {
            "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
            "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
        }
        l1_rows = [r for r in self.rows if r["level_n"] == 1]
        assert len(l1_rows) > 0
        for r in l1_rows:
            assert r["lord_graha"] in sign_names

    def test_42_level_n_in_1_to_4(self):
        for r in self.rows:
            assert r["level_n"] in (1, 2, 3, 4)

    def test_43_anchored_solar_return_populated(self):
        """Addition I: anchored_solar_return_iso populated on L1 rows."""
        l1_rows = [r for r in self.rows if r["level_n"] == 1]
        for r in l1_rows:
            assert r.get("anchored_solar_return_iso") is not None, (
                f"anchored_solar_return_iso None on Kalachakra L1 row"
            )

    def test_44_period_deity_populated(self):
        l1_rows = [r for r in self.rows if r["level_n"] == 1]
        for r in l1_rows:
            assert r.get("period_deity_or_marker") is not None


# R6 0e-dashameta (register V-1/G-7/D-1): _get_natal_context() now reads
# chart_facts/chart_divisionals via _load_natal_context() (build_system()
# calls that at build time). These tests call compute_* directly (no DB, no
# build_system — "NO DB required" per this module's own docstring), so we
# seed the module's natal-context cache with a fixture that mirrors the REAL
# ground truth queried live from chart_facts (graha_position) + chart_divisionals
# (varga_dignity, D1) for chart 482012f1 / lahiri_chitrapaksha — NOT the old
# hardcoded dict this fix replaced, which was wrong for 6 of 9 grahas.
FORENSIC_NATAL_FIXTURE: dict[str, dict[str, Any]] = {
    "Sun":     {"house_d1": 10, "sign": "Capricorn",   "nakshatra": "Shravana",        "dignity_d1": "enemy_sign",   "shadbala_total": 3.225},
    "Moon":    {"house_d1": 11, "sign": "Aquarius",    "nakshatra": "Purva Bhadrapada", "dignity_d1": "neutral_sign", "shadbala_total": 2.5607},
    "Mars":    {"house_d1": 7,  "sign": "Libra",       "nakshatra": "Swati",            "dignity_d1": "neutral_sign", "shadbala_total": 3.106},
    "Mercury": {"house_d1": 10, "sign": "Capricorn",   "nakshatra": "Uttara Ashadha",   "dignity_d1": "neutral_sign", "shadbala_total": 2.5},
    "Jupiter": {"house_d1": 9,  "sign": "Sagittarius", "nakshatra": "Mula",             "dignity_d1": "moolatrikona", "shadbala_total": 2.6598},
    "Venus":   {"house_d1": 9,  "sign": "Sagittarius", "nakshatra": "Purva Ashadha",    "dignity_d1": "neutral_sign", "shadbala_total": 2.3592},
    "Saturn":  {"house_d1": 7,  "sign": "Libra",       "nakshatra": "Vishakha",         "dignity_d1": "exalted",      "shadbala_total": 3.611},
    "Rahu":    {"house_d1": 2,  "sign": "Taurus",      "nakshatra": "Rohini",           "dignity_d1": "exalted",      "shadbala_total": 0.375},
    "Ketu":    {"house_d1": 8,  "sign": "Scorpio",     "nakshatra": "Jyeshtha",         "dignity_d1": "exalted",      "shadbala_total": 0.625},
}


class TestAdditions(unittest.TestCase):
    """Tests 45-59: All A7 additions A-Q."""

    @classmethod
    def setUpClass(cls):
        mod = _get_mod()
        mod.set_natal_context(mod.CANONICAL_CHART_ID, "lahiri", FORENSIC_NATAL_FIXTURE)
        cls.vim_rows = _compute_system_rows("vimshottari")
        cls.yogini_rows = _compute_system_rows("yogini")
        cls.mudda_rows = _compute_system_rows("mudda")
        cls.kc_rows = _compute_system_rows("kalachakra")

    def _sample_l1(self, rows: list[dict]) -> list[dict]:
        return [r for r in rows if r["level_n"] == 1 and r.get("kp_sublevel") is None][:5]

    def test_45_addition_a_natal_house(self):
        """Addition A: lord_natal_house_d1 populated for known lords."""
        for r in self._sample_l1(self.vim_rows):
            lord = r["lord_graha"]
            # Jupiter should have house_d1 = 9 (FORENSIC natal context)
            if lord == "Jupiter":
                assert r.get("lord_natal_house_d1") == 9, (
                    f"Jupiter natal house expected 9, got {r.get('lord_natal_house_d1')}"
                )

    def test_46_addition_a_natal_sign(self):
        for r in self._sample_l1(self.vim_rows):
            if r["lord_graha"] in ("Jupiter", "Sun", "Saturn"):
                assert r.get("lord_natal_sign") is not None

    def test_47_addition_a_natal_nakshatra(self):
        for r in self._sample_l1(self.vim_rows):
            if r["lord_graha"] == "Jupiter":
                assert r.get("lord_natal_nakshatra") == "Mula"

    def test_48_addition_a_natal_dignity(self):
        for r in self._sample_l1(self.vim_rows):
            if r["lord_graha"] == "Jupiter":
                # R6 0e-dashameta fix: Jupiter's real D1 dignity (chart_divisionals
                # varga_dignity, chart 482012f1) is Moolatrikona, not "own" — the
                # prior hardcoded _NATAL_CONTEXT dict this test used to check
                # against was itself wrong (register V-1).
                assert r.get("lord_natal_dignity_d1") == "moolatrikona"

    def test_49_addition_b_sandhi_lord(self):
        """Addition B: sandhi_with_next_dasha_lord on non-last L1 rows."""
        l1 = self._sample_l1(self.vim_rows)
        mod = _get_mod()
        # Run sandhi post-pass
        mod.compute_sandhi_post_pass(self.vim_rows)
        l1_fresh = [r for r in self.vim_rows if r["level_n"] == 1 and r.get("kp_sublevel") is None]
        # All except last should have sandhi_with_next_dasha_lord populated
        for r in l1_fresh[:-1]:
            assert r.get("sandhi_with_next_dasha_lord") is not None

    def test_50_addition_b_next_start(self):
        mod = _get_mod()
        mod.compute_sandhi_post_pass(self.vim_rows)
        l1_fresh = [r for r in self.vim_rows if r["level_n"] == 1 and r.get("kp_sublevel") is None]
        for r in l1_fresh[:-1]:
            assert r.get("next_dasha_start_iso") is not None

    def test_51_addition_cd_none_before_post_pass(self):
        """Additions C+D: concurrent_system_lords_jsonb is None before post-pass."""
        rows = _compute_system_rows("vimshottari")
        for r in rows[:10]:
            assert r.get("concurrent_system_lords_jsonb") is None

    def test_52_addition_e_applies_flag_is_bool(self):
        for r in self.vim_rows[:10]:
            flag = r.get("applies_to_this_chart_flag")
            assert isinstance(flag, bool), f"applies_to_this_chart_flag={flag!r} is not bool"

    def test_53_addition_f_deity_yogini(self):
        """Addition F: period_deity_or_marker on Yogini rows."""
        l1 = [r for r in self.yogini_rows if r["level_n"] == 1]
        for r in l1:
            assert r.get("period_deity_or_marker") is not None

    def test_54_addition_g_relationship(self):
        """Addition G: lord_to_parent_relationship in valid set."""
        valid = {"friend", "enemy", "neutral", None}
        for r in self.vim_rows[:50]:
            rel = r.get("lord_to_parent_relationship")
            assert rel in valid, f"Invalid relationship: {rel!r}"

    def test_55_addition_h_varsha_lord(self):
        """Addition H: varsha_year_lord on mudda rows."""
        for r in self.mudda_rows[:10]:
            assert r.get("varsha_year_lord") is not None

    def test_56_addition_i_solar_return(self):
        """Addition I: anchored_solar_return_iso on kalachakra L1 rows."""
        l1 = [r for r in self.kc_rows if r["level_n"] == 1]
        for r in l1[:5]:
            assert r.get("anchored_solar_return_iso") is not None

    def test_57_addition_j_triggered_yogas_column_dropped(self):
        """Addition J (R6 0e-dashameta / register V-11): triggered_yogas_jsonb_atomic
        was dropped (migration 428) — it was permanently '[]' with no yoga-trigger
        engine in GA7 to ever populate it (fabrication risk, CLAUDE.md B.10).
        Row dicts must not carry the key at all anymore."""
        for r in self.vim_rows[:10]:
            assert "triggered_yogas_jsonb_atomic" not in r

    def test_58_addition_k_transit_column_dropped(self):
        """Addition K (register V-11): lord_transit_at_period_start_jsonb was
        dropped (migration 428) — always NULL, no transit engine in GA7."""
        for r in self.vim_rows[:10]:
            assert "lord_transit_at_period_start_jsonb" not in r

    def test_59_addition_q_karakas(self):
        """Addition Q: karakas_active_during_period is list or None."""
        for r in self.vim_rows[:20]:
            val = r.get("karakas_active_during_period")
            assert val is None or isinstance(val, list), (
                f"karakas_active_during_period={val!r} is not list or None"
            )


class TestJSONBSanctions(unittest.TestCase):
    """Test 60: Only 1 sanctioned JSONB column (R6 0e-dashameta / register V-11:
    triggered_yogas_jsonb_atomic and lord_transit_at_period_start_jsonb dropped
    via migration 428 — both were permanently dead placeholders with no engine
    in GA7 to populate them; see migration 428's header for the full rationale)."""

    def test_60_only_sanctioned_jsonb_columns(self):
        """
        Only 1 sanctioned JSONB column remains: concurrent_system_lords_jsonb.
        All other JSONB-named fields must not be present as row keys
        carrying JSONB-style data.
        """
        sanctioned = {
            "concurrent_system_lords_jsonb",
        }
        rows = _compute_system_rows("vimshottari")
        for r in rows[:5]:
            # Check no OTHER keys end in _jsonb
            jsonb_keys = {k for k in r.keys() if k.endswith("_jsonb")}
            non_sanctioned = jsonb_keys - sanctioned
            assert not non_sanctioned, (
                f"Non-sanctioned JSONB column(s): {non_sanctioned}"
            )
            # The two dropped columns must genuinely be gone, not just
            # coincidentally absent from `sanctioned`.
            assert "triggered_yogas_jsonb_atomic" not in r
            assert "lord_transit_at_period_start_jsonb" not in r


class TestAlgebraicInvariants(unittest.TestCase):
    """Tests 61-64: Algebraic invariants per system."""

    def test_61_vimshottari_l1_lords_in_sequence(self):
        mod = _get_mod()
        rows = _compute_system_rows("vimshottari")
        l1 = [r for r in rows if r["level_n"] == 1 and r.get("kp_sublevel") is None]
        seq = mod.VIMSHOTTARI_SEQUENCE
        # Consecutive L1 lords must follow the Vimshottari cycle
        for i in range(1, min(len(l1), 10)):
            prev_lord = l1[i - 1]["lord_graha"]
            curr_lord = l1[i]["lord_graha"]
            prev_idx = seq.index(prev_lord)
            expected_next = seq[(prev_idx + 1) % 9]
            assert curr_lord == expected_next, (
                f"Sequence break: {prev_lord} → {curr_lord} (expected {expected_next})"
            )

    def test_62_yogini_l1_lords_follow_cycle(self):
        mod = _get_mod()
        rows = _compute_system_rows("yogini")
        l1 = [r for r in rows if r["level_n"] == 1]
        seq_names = [name for name, _, _ in mod.YOGINI_SEQUENCE]
        for i in range(1, min(len(l1), 8)):
            prev = l1[i - 1]["lord_graha"]
            curr = l1[i]["lord_graha"]
            prev_idx = seq_names.index(prev)
            expected_next = seq_names[(prev_idx + 1) % 8]
            assert curr == expected_next, (
                f"Yogini sequence break: {prev} → {curr} (expected {expected_next})"
            )

    def test_63_ashtottari_l1_lords_in_sequence(self):
        mod = _get_mod()
        rows = _compute_system_rows("ashtottari")
        l1 = [r for r in rows if r["level_n"] == 1]
        seq = [lord for lord, _ in mod.ASHTOTTARI_SEQUENCE]
        if len(l1) < 2:
            return  # Can't test sequence with 1 row
        for i in range(1, min(len(l1), 8)):
            prev = l1[i - 1]["lord_graha"]
            curr = l1[i]["lord_graha"]
            prev_idx = seq.index(prev)
            expected = seq[(prev_idx + 1) % 8]
            assert curr == expected, (
                f"Ashtottari sequence break: {prev} → {curr} (expected {expected})"
            )

    def test_64_naisargika_l1_lords_in_sequence(self):
        mod = _get_mod()
        rows = _compute_system_rows("naisargika")
        l1 = [r for r in rows if r["level_n"] == 1]
        seq = [lord for lord, _ in mod.NAISARGIKA_SEQUENCE]
        for i, r in enumerate(l1):
            expected = seq[i % len(seq)]
            assert r["lord_graha"] == expected, (
                f"Naisargika L1 [{i}] lord={r['lord_graha']!r}, expected={expected!r}"
            )


class TestBuildSystem(unittest.TestCase):
    """Tests 65-68: build_system function."""

    def test_65_build_system_skip_db_returns_pass(self):
        mod = _get_mod()
        with patch.object(mod, "_get_moon_position", side_effect=lambda aya, birth=None: (FORENSIC_MOON_LON, BIRTH_JD)):
            result = mod.build_system("vimshottari", "lahiri", mod.CANONICAL_CHART_ID,
                                      birth_params=NATIVE_BIRTH_PARAMS, skip_db=True)
        assert result["status"] == "PASS", f"build_system returned {result.get('status')}: {result}"

    def test_66_build_system_rows_computed(self):
        mod = _get_mod()
        with patch.object(mod, "_get_moon_position", side_effect=lambda aya, birth=None: (FORENSIC_MOON_LON, BIRTH_JD)):
            result = mod.build_system("vimshottari", "lahiri", mod.CANONICAL_CHART_ID,
                                      birth_params=NATIVE_BIRTH_PARAMS, skip_db=True)
        assert result["rows_computed"] > 0

    def test_67_build_system_unknown_system_raises(self):
        mod = _get_mod()
        with self.assertRaises(ValueError):
            mod.build_system("unknown_system", "lahiri", mod.CANONICAL_CHART_ID,
                             birth_params=NATIVE_BIRTH_PARAMS, skip_db=True)

    def test_68_forensic_halt_propagated(self):
        """build_system propagates FORENSIC halt if starting lord wrong."""
        mod = _get_mod()
        wrong_moon = 2.0  # Ashwini → Ketu lord
        with patch.object(mod, "_get_moon_position", side_effect=lambda aya, birth=None: (wrong_moon, BIRTH_JD)):
            with self.assertRaises(ValueError) as ctx:
                mod.build_system("vimshottari", "lahiri", mod.CANONICAL_CHART_ID,
                                 birth_params=NATIVE_BIRTH_PARAMS, skip_db=True)
        assert "FORENSIC HALT" in str(ctx.exception)


class TestCitationFormat(unittest.TestCase):
    """Tests 70-72: citation format."""

    @classmethod
    def setUpClass(cls):
        cls.rows = _compute_system_rows("vimshottari")

    def test_70_citation_ref_format(self):
        """citation_ref starts with 'chart_dashas.'."""
        for r in self.rows[:20]:
            ref = r.get("citation_ref", "")
            assert ref.startswith("chart_dashas."), (
                f"citation_ref doesn't start with 'chart_dashas.': {ref!r}"
            )

    def test_71_citation_human_non_empty(self):
        for r in self.rows[:20]:
            human = r.get("citation_human", "")
            assert isinstance(human, str) and len(human) > 0

    def test_72_verification_pass_status_valid(self):
        valid_statuses = {"two_pass_verified", "classical_match", "divergent_flagged"}
        for r in self.rows[:20]:
            status = r.get("verification_pass_status")
            assert status in valid_statuses, (
                f"Invalid verification_pass_status: {status!r}"
            )


class TestAllSystemsNoLevelN5(unittest.TestCase):
    """Comprehensive test: all 7 systems produce ZERO level_n=5 rows."""

    def test_all_systems_zero_level_n5(self):
        systems = [
            "vimshottari", "yogini", "ashtottari",
            "chara_karaka", "naisargika", "mudda", "kalachakra",
        ]
        for sys_id in systems:
            with self.subTest(system=sys_id):
                rows = _compute_system_rows(sys_id)
                level5 = [r for r in rows if r["level_n"] == 5]
                assert len(level5) == 0, (
                    f"System {sys_id}: found {len(level5)} level_n=5 rows — "
                    f"CRITICAL OVERRIDE 1 violated"
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)
