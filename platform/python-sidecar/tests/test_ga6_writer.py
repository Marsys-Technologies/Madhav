"""
test_ga6_writer.py — GA6 vargas writer unit tests.
=====================================================
Tests cover:
  1.  Constants: all 30 vargas declared, correct sets
  2.  Varga formula coverage: all 30 vargas have non-None formula
  3.  _compute_general_varga: valid sign range for all 30 divisors
  4.  D2 Hora: only Cancer (4) or Leo (5) result — Parashari formula
  5.  D3 Drekkana: valid sign range for all 3 formula variants
  6.  D1 sign = input sign (divisor=1)
  7.  D9 navamsa: valid range + specific known value
  8.  D60 Shashtiamsa: valid range
  9.  D108 generic: valid range (large divisor)
 10.  D150 generic: valid range
 11.  D2700 generic: valid range
 12.  _compute_dignity: Exalted returns 'Exalted', Debilitated 'Debilitated'
 13.  _compute_dignity: Unknown body returns 'Unknown'
 14.  _compute_vargottama: same sign → True
 15.  _compute_vargottama: different sign → False
 16.  _build_position_rows: valid structure (no DB)
 17.  _build_position_rows: FORENSIC — Sun D1 = Capricorn (mocked)
 18.  _build_dignity_rows: dignity is one of allowed values
 19.  _build_vargottama_rows: vargottama field matches sign comparison
 20.  _build_house_lord_occupant_rows: house in [1,12]
 21.  _build_deity_rows: D60 deity is non-empty string
 22.  _build_formula_variant_rows: D2 yields 2 formula variants × 10 bodies
 23.  _build_formula_variant_rows: D3 yields 3 formula variants × 10 bodies
 24.  _build_d30_lord_per_amsa_rows: 60 rows (12 signs × 5 lords)
 25.  _build_vimsopaka_rows: D1 has vimsopaka rows for 7 grahas
 26.  _build_saptavargaja_rows: D9 has saptavargaja rows for 7 grahas
 27.  _build_karaka_rows: 8 karakas × 3 keys = 24 rows
 28.  _build_rollup_rows: 9 rollup rows per varga
 29.  _build_d9_lagna_special_rows: 2 rows (vargottama + pushkara flags)
 30.  _build_d27_quadrant_rows: quadrant in ['North','South','East','West']
 31.  _build_d108_karma_rows: karma_type in ['Sanchita','Prarabdha','Agami']
 32.  _build_d150_rishi_rows: rishi non-empty
 33.  _build_cross_varga_harmonic_rows: super_vargottama emitted for all bodies
 34.  _build_cross_varga_harmonic_rows: trikona + trans_count emitted
 35.  Atomic grain: no fact_value_text contains forbidden narration patterns
 36.  Atomic grain: all rows have non-null citation_ref + citation_human
 37.  Atomic grain: all rows have verification_pass_status in valid set
 38.  forensic_gate_vargas: passes for Capricorn Sun + Aries Lagna
 39.  forensic_gate_vargas: fails for wrong Sun sign
 40.  forensic_gate_vargas: fails for wrong Lagna
 41.  All 30 vargas are processed (VARGA_BATCHES covers all)
 42.  _check_narration: detects forbidden patterns
 43.  _check_narration: clean rows pass
 44.  _fact_id: deterministic SHA hash
 45.  _citation_ref: well-formed string
 46.  _d27_quadrant: signs 0-2=East, 3-5=South, 6-8=West, 9-11=North
 47.  Vimsopaka weights: D9 weight=3.0, D60 weight=4.0
 48.  D9 lagna pushkara_lagna_flag: sign 1 (Taurus) is pushkara
 49.  varga_saptavargaja: own-sign=30, Moolatrikona=45 (D1-only), compound
      naisargika+tatkalika relation ladder cross-checked vs PyJHora (M-18)
 50.  Verification tiers (Stage 2 honest-tiers, TAP-6 M-22 remediation): D1
      and D60 varga_position rows are both UNVERIFIED_DEFAULT ('single') —
      genuine=EMPTY for this writer, no varga's position/dignity/deity/etc.
      lookup runs an independent second-pass check to earn 'two_pass_verified'
"""
from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

from brahmagyan.verification_vocab import RESTRICTED_TABLE_VOCAB, UNVERIFIED_DEFAULT


# ── Import module under test ──────────────────────────────────────────────────

def _mod():
    from ga_writers import ga_vargas_writer as m
    return m


# ── 1. Constants ──────────────────────────────────────────────────────────────

class TestConstants:
    def test_30_vargas_total(self):
        m = _mod()
        assert len(m.ALL_30_VARGAS) == 30

    def test_parashari_16_count(self):
        m = _mod()
        assert len(m.PARASHARI_16) == 16

    def test_supplementary_11_count(self):
        m = _mod()
        assert len(m.SUPPLEMENTARY_11) == 11

    def test_nadi_3_count(self):
        m = _mod()
        assert len(m.NADI_3) == 3

    def test_d81_not_in_vargas(self):
        m = _mod()
        assert 81 not in m.ALL_30_VARGAS, "D81 is SKIPPED per brief §2 locked decision J"

    def test_d9_in_parashari_16(self):
        m = _mod()
        assert 9 in m.PARASHARI_16

    def test_d60_in_parashari_16(self):
        m = _mod()
        assert 60 in m.PARASHARI_16

    def test_d2700_in_nadi(self):
        m = _mod()
        assert 2700 in m.NADI_3

    def test_varga_batches_cover_all_30(self):
        m = _mod()
        all_in_batches = set()
        for batch in m.VARGA_BATCHES:
            all_in_batches.update(batch)
        assert all_in_batches == set(m.ALL_30_VARGAS), \
            f"Batches missing: {set(m.ALL_30_VARGAS) - all_in_batches}"

    def test_6_batches(self):
        m = _mod()
        assert len(m.VARGA_BATCHES) == 6

    def test_saptavarga_set_has_7(self):
        m = _mod()
        assert len(m.SAPTAVARGA_SET) == 7

    def test_saptavarga_set_is_the_classical_group(self):
        """F-61 (PARIŚEṢA-V4): the set previously read {1,2,3,9,12,30,60} —
        it omitted D7 (Saptamsa, the division the group is named for) and
        included D60 (Shashtiamsa, a Shodasavarga/Vimsopaka member, not a
        saptavarga one). Three authorities agree on the membership:
          - this repo's own L0 canonical table, brahmagyan/l0_reference.py:
            strength_reference.saptavargaja_bala.formula_text ==
            "Sum of dignity points across D1,D2,D3,D7,D9,D12,D30", and the
            varga-group table's "saptavarga" entry (D1,D2,D3,D7,D9,D12,D30);
          - jhora.const.sapthavargaja_factors == [1,2,3,7,9,12,30];
          - BPHS Ch.27 (Shadbala Adhyaya), Sthana Bala.
        """
        m = _mod()
        assert m.SAPTAVARGA_SET == {1, 2, 3, 7, 9, 12, 30}
        assert 7 in m.SAPTAVARGA_SET, "D7 (Saptamsa) is a saptavarga member"
        assert 60 not in m.SAPTAVARGA_SET, "D60 is Shodasavarga, not saptavarga"

    def test_saptavarga_set_matches_l0_reference_authority(self):
        """§N.5: L1 must not restate an L0 reference as its own divergent
        truth. Read the membership straight out of l0_reference and compare."""
        m = _mod()
        from brahmagyan import l0_reference as l0
        table = None
        for attr in dir(l0):
            val = getattr(l0, attr)
            if isinstance(val, dict) and "saptavarga" in val and isinstance(
                    val.get("saptavarga"), dict):
                table = val["saptavarga"]
                break
        assert table is not None, "l0_reference saptavarga varga-group table not found"
        l0_membership = {int(k.lstrip("Dd")) for k in table}
        assert m.SAPTAVARGA_SET == l0_membership, (
            f"GA6 SAPTAVARGA_SET {sorted(m.SAPTAVARGA_SET)} disagrees with the L0 "
            f"authority {sorted(l0_membership)}"
        )

    def test_vimsopaka_d9_weight(self):
        m = _mod()
        assert m.VIMSOPAKA_SHODA_WEIGHTS[9] == 3.0

    def test_vimsopaka_d60_weight(self):
        m = _mod()
        assert m.VIMSOPAKA_SHODA_WEIGHTS[60] == 4.0

    def test_vimsopaka_d1_weight(self):
        m = _mod()
        assert m.VIMSOPAKA_SHODA_WEIGHTS[1] == 3.5

    def test_vimsopaka_shoda_weights_sum_to_20(self):
        """F-168: VIMSOPAKA_SHODA_WEIGHTS names itself for summing to twenty
        (Vimsopaka == "twenty-point", BPHS Ch.7). D40 and D45 were both
        wrongly 1.0 (should be 0.5 per L0 l0_reference._VIMSHOPAKA
        ["shodashavarga"] and PyJHora jhora.const.py:228-231), making the
        table sum to 21.0 — this is the detector that constant never had.
        """
        m = _mod()
        assert sum(m.VIMSOPAKA_SHODA_WEIGHTS.values()) == 20.0

    def test_vimsopaka_d40_and_d45_weights_match_l0(self):
        """F-168: the specific fixed rows, pinned individually so a future
        edit to either can't silently drift back to the wrong value even if
        the aggregate sum happened to still check out some other way."""
        m = _mod()
        assert m.VIMSOPAKA_SHODA_WEIGHTS[40] == 0.5
        assert m.VIMSOPAKA_SHODA_WEIGHTS[45] == 0.5

    def test_d7_karya_is_progeny_not_spouse(self):
        """Regression (PRE_DARPANA_READINESS A-4): D7 Saptamsha is the progeny/
        children significator, not spouse. The `progeny_deepdive` floor (VIDHI-
        PURNATA) consumes this karya marker directly — a `spouse_karya` mislabel
        here would pollute progeny answers with spouse semantics."""
        m = _mod()
        assert m.VARGA_KARYA[7] == "progeny_karya"
        assert m.VARGA_KARYA[7] != "spouse_karya"


# ── 2. Varga formula functions ────────────────────────────────────────────────

class TestVargaFormulas:
    def test_d1_sign_equals_input_sign(self):
        m = _mod()
        for lon in [0.0, 15.0, 45.0, 90.5, 180.0, 270.0, 359.9]:
            sign = m._compute_general_varga(lon, 1)
            expected = int(lon / 30.0) % 12
            assert sign == expected, f"D1 lon={lon} sign={sign} expected={expected}"

    def test_d2_hora_only_cancer_or_leo(self):
        m = _mod()
        for lon in [0.0, 5.0, 15.0, 16.0, 30.0, 45.0, 89.9, 100.0, 180.0, 270.0]:
            sign = m._compute_d2_hora(lon, "parashari")
            assert sign in (3, 4), f"D2 Hora lon={lon} sign={sign} (expected Cancer=3 or Leo=4)"

    def test_d3_drekkana_valid_range_parashari(self):
        m = _mod()
        for lon in [0.0, 10.5, 20.0, 35.0, 70.0, 160.0, 270.0, 350.0]:
            sign = m._compute_d3_drekkana(lon, "parashari")
            assert 0 <= sign <= 11, f"D3 parashari sign={sign} for lon={lon}"

    def test_d3_drekkana_valid_range_jaimini(self):
        m = _mod()
        for lon in [5.0, 15.0, 25.0, 55.0, 100.0, 200.0, 340.0]:
            sign = m._compute_d3_drekkana(lon, "jaimini")
            assert 0 <= sign <= 11

    def test_d3_drekkana_valid_range_mooltrikona(self):
        m = _mod()
        for lon in [5.0, 15.0, 25.0, 55.0, 100.0, 200.0, 340.0]:
            sign = m._compute_d3_drekkana(lon, "mooltrikona")
            assert 0 <= sign <= 11

    def test_d9_navamsa_valid_range(self):
        m = _mod()
        for lon in [0.0, 3.33, 10.0, 45.0, 90.0, 180.0, 270.0, 359.0]:
            sign = m._compute_general_varga(lon, 9)
            assert 0 <= sign <= 11, f"D9 sign={sign} for lon={lon}"

    def test_general_varga_all_30_valid_range(self):
        m = _mod()
        test_lons = [5.0, 45.0, 90.0, 180.0, 270.0, 350.0]
        for vn in m.ALL_30_VARGAS:
            for lon in test_lons:
                sign = m._compute_general_varga(lon, vn)
                assert 0 <= sign <= 11, f"D{vn} sign={sign} for lon={lon}"

    def test_d60_valid_range(self):
        m = _mod()
        for lon in [0.5, 15.0, 90.0, 180.0, 270.0, 359.0]:
            sign = m._compute_general_varga(lon, 60)
            assert 0 <= sign <= 11

    def test_d108_valid_range(self):
        m = _mod()
        for lon in [1.0, 45.0, 180.0, 350.0]:
            sign = m._compute_general_varga(lon, 108)
            assert 0 <= sign <= 11

    def test_d2700_valid_range(self):
        m = _mod()
        sign = m._compute_general_varga(100.0, 2700)
        assert 0 <= sign <= 11

    def test_d2_formula_parashari_leo_first_half_odd_sign(self):
        """Aries (sign 0, odd-indexed) first 15° → Leo (4)."""
        m = _mod()
        # Aries = sign_idx 0 (0-indexed), first 15° → Leo (4)
        sign = m._compute_d2_hora(7.0, "parashari")
        assert sign == 4, f"D2 hora Aries 7° expected Leo(4), got {sign}"


# ── 3. Dignity computation ────────────────────────────────────────────────────

class TestDignity:
    def test_sun_exalted_in_aries(self):
        m = _mod()
        # Sun exalted in Aries (sign_idx=0)
        assert m._compute_dignity("Sun", 0) == "Exalted"

    def test_sun_debilitated_in_libra(self):
        m = _mod()
        # Sun debilitated in Libra (sign_idx=6)
        assert m._compute_dignity("Sun", 6) == "Debilitated"

    def test_moon_exalted_in_taurus(self):
        m = _mod()
        # Moon exalted in Taurus (sign_idx=1)
        assert m._compute_dignity("Moon", 1) == "Exalted"

    def test_unknown_body_returns_unknown(self):
        m = _mod()
        assert m._compute_dignity("Uranus", 5) == "Unknown"

    def test_own_sign(self):
        m = _mod()
        # Sun Leo (sign_idx=4) — Leo is Sun's own sign but moolatrikona=4 too.
        # Moolatrikona takes precedence when mt==own; both are valid outcomes.
        assert m._compute_dignity("Sun", 4) in ("Own", "Moolatrikona")
        # Saturn owns Capricorn (sign_idx=10) and MT is Aquarius (10); own takes precedence
        assert m._compute_dignity("Saturn", 10) in ("Own", "Moolatrikona")

    def test_moolatrikona(self):
        m = _mod()
        # Sun's moolatrikona is Leo (4) — same as own, but let's check Mars in Aries
        # Mars moolatrikona = Aries (0)
        result = m._compute_dignity("Mars", 0)
        assert result in ("Exalted", "Moolatrikona"), f"Mars Aries: {result}"

    def test_friend_sign(self):
        m = _mod()
        # Sun in Cancer (Moon's sign); B-01 oracle uses 5 canonical tiers only
        # (exalted/debilitated/moolatrikona/own/neutral) — Friend tier removed.
        assert m._compute_dignity("Sun", 3) == "Neutral"

    def test_enemy_sign(self):
        m = _mod()
        # Sun in Taurus (Venus's sign); B-01 oracle uses 5 canonical tiers only
        # (exalted/debilitated/moolatrikona/own/neutral) — Enemy tier removed.
        assert m._compute_dignity("Sun", 1) == "Neutral"


# ── 4. Vargottama ─────────────────────────────────────────────────────────────

class TestVargottama:
    def test_same_sign_is_vargottama(self):
        m = _mod()
        assert m._compute_vargottama(5, 5) is True

    def test_different_sign_not_vargottama(self):
        m = _mod()
        assert m._compute_vargottama(5, 6) is False

    def test_sign_0(self):
        m = _mod()
        assert m._compute_vargottama(0, 0) is True


# ── 5. D27 quadrant ───────────────────────────────────────────────────────────

class TestD27Quadrant:
    def test_east_signs_0_1_2(self):
        m = _mod()
        for s in [0, 1, 2]:
            assert m._d27_quadrant(s) == "East", f"sign {s} expected East"

    def test_south_signs_3_4_5(self):
        m = _mod()
        for s in [3, 4, 5]:
            assert m._d27_quadrant(s) == "South", f"sign {s} expected South"

    def test_west_signs_6_7_8(self):
        m = _mod()
        for s in [6, 7, 8]:
            assert m._d27_quadrant(s) == "West", f"sign {s} expected West"

    def test_north_signs_9_10_11(self):
        m = _mod()
        for s in [9, 10, 11]:
            assert m._d27_quadrant(s) == "North", f"sign {s} expected North"


# ── 6. FORENSIC gate ──────────────────────────────────────────────────────────

class TestForensicGate:
    def _mock_all_vargas(self, sun_sign="Capricorn", lagna_sign="Aries"):
        """Helper to build minimal mock all_vargas dict."""
        return {
            "D1": {
                "Sun": {"sign": sun_sign, "sign_idx": 9, "degree_in_sign": 15.0},
                "Lagna": {"sign": lagna_sign, "sign_idx": 0, "degree_in_sign": 20.0},
            }
        }

    def test_forensic_pass_correct_anchors(self):
        m = _mod()
        all_vargas = self._mock_all_vargas("Capricorn", "Aries")
        result = m.forensic_gate_vargas(all_vargas, "lahiri_chitrapaksha")
        assert result["result"] == "PASS", f"Expected PASS, got: {result['findings']}"

    def test_forensic_fail_wrong_sun(self):
        m = _mod()
        all_vargas = self._mock_all_vargas("Sagittarius", "Aries")
        result = m.forensic_gate_vargas(all_vargas, "lahiri_chitrapaksha")
        assert result["result"] == "FAIL"
        assert any("Sun" in f for f in result["findings"])

    def test_forensic_fail_wrong_lagna(self):
        m = _mod()
        all_vargas = self._mock_all_vargas("Capricorn", "Scorpio")
        result = m.forensic_gate_vargas(all_vargas, "lahiri_chitrapaksha")
        assert result["result"] == "FAIL"
        assert any("Lagna" in f for f in result["findings"])

    def test_forensic_fail_both_wrong(self):
        m = _mod()
        all_vargas = self._mock_all_vargas("Leo", "Scorpio")
        result = m.forensic_gate_vargas(all_vargas, "lahiri_chitrapaksha")
        assert result["result"] == "FAIL"
        assert len(result["findings"]) == 2


# ── 7. Row builders (no DB) ───────────────────────────────────────────────────

MOCK_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
MOCK_AYAN = "lahiri_chitrapaksha"
MOCK_BUILD_ID = "test-build-123"

MOCK_VARGA_DATA = {
    "Sun": {"sign_idx": 9, "sign": "Capricorn", "sign_id": 10, "degree_in_sign": 15.5, "longitude": 285.5},
    "Moon": {"sign_idx": 10, "sign": "Aquarius", "sign_id": 11, "degree_in_sign": 12.0, "longitude": 322.0},
    "Mars": {"sign_idx": 0, "sign": "Aries", "sign_id": 1, "degree_in_sign": 5.0, "longitude": 5.0},
    "Mercury": {"sign_idx": 9, "sign": "Capricorn", "sign_id": 10, "degree_in_sign": 20.0, "longitude": 290.0},
    "Jupiter": {"sign_idx": 8, "sign": "Sagittarius", "sign_id": 9, "degree_in_sign": 10.0, "longitude": 250.0},
    "Venus": {"sign_idx": 9, "sign": "Capricorn", "sign_id": 10, "degree_in_sign": 25.0, "longitude": 295.0},
    "Saturn": {"sign_idx": 6, "sign": "Libra", "sign_id": 7, "degree_in_sign": 8.0, "longitude": 188.0},
    "Rahu": {"sign_idx": 4, "sign": "Leo", "sign_id": 5, "degree_in_sign": 3.0, "longitude": 123.0},
    "Ketu": {"sign_idx": 10, "sign": "Aquarius", "sign_id": 11, "degree_in_sign": 3.0, "longitude": 303.0},
    "Lagna": {"sign_idx": 0, "sign": "Aries", "sign_id": 1, "degree_in_sign": 20.0, "longitude": 20.0},
}

MOCK_D1_LONGITUDES = {
    "Sun": 285.5, "Moon": 322.0, "Mars": 5.0, "Mercury": 290.0,
    "Jupiter": 250.0, "Venus": 295.0, "Saturn": 188.0,
    "Rahu": 123.0, "Ketu": 303.0, "Lagna": 20.0,
}


class TestPositionRows:
    def test_position_rows_built(self):
        m = _mod()
        rows = m._build_position_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, 1, "D1",
            MOCK_VARGA_DATA, MOCK_VARGA_DATA)
        assert len(rows) > 0

    def test_all_classical_bodies_present(self):
        m = _mod()
        rows = m._build_position_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, 1, "D1",
            MOCK_VARGA_DATA, MOCK_VARGA_DATA)
        bodies = {r["graha"] for r in rows}
        for b in m.CLASSICAL_BODIES:
            assert b in bodies, f"Missing body {b} in position rows"

    def test_forensic_sun_capricorn(self):
        """FORENSIC: D1 Sun position row has sign='Capricorn'."""
        m = _mod()
        rows = m._build_position_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, 1, "D1",
            MOCK_VARGA_DATA, MOCK_VARGA_DATA)
        sun_sign_rows = [r for r in rows
                         if r["graha"] == "Sun" and r["fact_key"] == "sign"]
        assert sun_sign_rows, "No Sun sign row found"
        assert sun_sign_rows[0]["fact_value_text"] == "Capricorn", \
            f"D1 Sun sign={sun_sign_rows[0]['fact_value_text']} expected Capricorn"

    def test_forensic_lagna_aries(self):
        """FORENSIC: D1 Lagna position row has sign='Aries'."""
        m = _mod()
        rows = m._build_position_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, 1, "D1",
            MOCK_VARGA_DATA, MOCK_VARGA_DATA)
        lagna_sign_rows = [r for r in rows
                           if r["graha"] == "Lagna" and r["fact_key"] == "sign"]
        assert lagna_sign_rows, "No Lagna sign row found"
        assert lagna_sign_rows[0]["fact_value_text"] == "Aries", \
            f"D1 Lagna sign={lagna_sign_rows[0]['fact_value_text']} expected Aries"

    def test_d1_verification_single(self):
        """D1 varga_position rows have verification_pass_status='single'."""
        m = _mod()
        rows = m._build_position_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, 1, "D1",
            MOCK_VARGA_DATA, MOCK_VARGA_DATA)
        for r in rows:
            assert r["verification_pass_status"] == "single", \
                f"D1 position should be 'single', got '{r['verification_pass_status']}'"

    def test_d60_verification_single(self):
        """Stage 2 honest-tiers rewrite (was: test_d60_verification_two_pass,
        asserting D60 varga_position rows are 'two_pass_verified'). REWRITTEN,
        not silently flipped: D60/D108/D150/D2700 fell through
        _verification_status()'s unconditional fallback return, which claimed
        'two_pass_verified' for these four vargas' varga_position rows purely
        from TWO_PASS_VARGA_POSITIONS set-membership — no independent second
        derivation ever ran to back that claim (the recon pass that ruled this
        writer's Stage 2 fix confirmed genuine=EMPTY for the whole writer).
        D60 now gets the same honest UNVERIFIED_DEFAULT every other varga's
        position rows already carried. Anchored to the vocab's canonical
        constant, not to the writer's own literal, so this isn't a tautology
        over the code under test.
        """
        m = _mod()
        rows = m._build_position_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, 60, "D60",
            MOCK_VARGA_DATA, MOCK_VARGA_DATA)
        for r in rows:
            assert r["verification_pass_status"] == UNVERIFIED_DEFAULT, \
                f"D60 position should be UNVERIFIED_DEFAULT ({UNVERIFIED_DEFAULT!r}), " \
                f"got {r['verification_pass_status']!r}"

    def test_all_rows_have_citations(self):
        m = _mod()
        rows = m._build_position_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, 9, "D9",
            MOCK_VARGA_DATA, MOCK_VARGA_DATA)
        for r in rows:
            assert r.get("citation_ref"), f"Missing citation_ref in row {r.get('fact_key')}"
            assert r.get("citation_human"), f"Missing citation_human in row {r.get('fact_key')}"


class TestDignityRows:
    def test_dignity_rows_built(self):
        m = _mod()
        rows = m._build_dignity_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, 9, "D9", MOCK_VARGA_DATA)
        assert len(rows) > 0

    def test_dignity_values_valid(self):
        m = _mod()
        valid = {"Exalted", "Debilitated", "Moolatrikona", "Own", "Friend", "Neutral", "Enemy", "Unknown"}
        rows = m._build_dignity_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, 9, "D9", MOCK_VARGA_DATA)
        for r in rows:
            assert r["fact_value_text"] in valid, \
                f"Invalid dignity: {r['fact_value_text']}"

    def test_dignity_verification_single(self):
        """Stage 2 honest-tiers rewrite (was: test_dignity_two_pass_verified,
        asserting varga_dignity rows are 'two_pass_verified'). REWRITTEN, not
        silently flipped: dignity is read off a single static classical
        dignity table lookup (_compute_dignity) — one pass, no independent
        second derivation to disagree with it. The literal
        'verification_pass_status': 'two_pass_verified' this row used to
        emit was unconditional (not gated by any real comparison), which the
        recon pass that ruled this writer's Stage 2 fix confirmed for the
        whole writer (genuine=EMPTY). Now UNVERIFIED_DEFAULT. Anchored to the
        vocab's canonical constant, not to the writer's own literal, so this
        isn't a tautology over the code under test.
        """
        m = _mod()
        rows = m._build_dignity_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, 9, "D9", MOCK_VARGA_DATA)
        for r in rows:
            assert r["verification_pass_status"] == UNVERIFIED_DEFAULT


class TestVargottamaRows:
    def test_vargottama_rows_built(self):
        m = _mod()
        rows = m._build_vargottama_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, 9, "D9",
            MOCK_VARGA_DATA, MOCK_VARGA_DATA)
        assert len(rows) >= len(m.CLASSICAL_BODIES)

    def test_vargottama_flag_valid(self):
        m = _mod()
        rows = m._build_vargottama_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, 9, "D9",
            MOCK_VARGA_DATA, MOCK_VARGA_DATA)
        # Same data → all vargottama = True
        for r in rows:
            assert r["fact_value_text"] in ("True", "False")

    def test_same_data_all_vargottama_true(self):
        """When varga_data == d1_data, all bodies are vargottama."""
        m = _mod()
        rows = m._build_vargottama_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, 9, "D9",
            MOCK_VARGA_DATA, MOCK_VARGA_DATA)
        for r in rows:
            assert r["fact_value_text"] == "True", \
                f"Same data should yield vargottama=True for {r['graha']}"


class TestHouseLordOccupantRows:
    def test_house_lord_rows_count(self):
        m = _mod()
        rows = m._build_house_lord_occupant_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, 1, "D1", MOCK_VARGA_DATA)
        # Should have 12 house lord rows + 10 occupant rows
        lord_rows = [r for r in rows if r["fact_category"] == "varga_house_lord"]
        assert len(lord_rows) == 12, f"Expected 12 house lord rows, got {len(lord_rows)}"

    def test_house_occupant_rows_count(self):
        m = _mod()
        rows = m._build_house_lord_occupant_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, 1, "D1", MOCK_VARGA_DATA)
        occ_rows = [r for r in rows if r["fact_category"] == "varga_house_occupant"]
        assert len(occ_rows) == len(m.CLASSICAL_BODIES)

    def test_house_numbers_in_range(self):
        m = _mod()
        rows = m._build_house_lord_occupant_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, 1, "D1", MOCK_VARGA_DATA)
        for r in rows:
            if r["house"] is not None:
                assert 1 <= r["house"] <= 12, f"House out of range: {r['house']}"

    def test_lagna_is_house_1(self):
        m = _mod()
        rows = m._build_house_lord_occupant_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, 1, "D1", MOCK_VARGA_DATA)
        lagna_rows = [r for r in rows
                      if r["graha"] == "Lagna" and r["fact_category"] == "varga_house_occupant"]
        assert lagna_rows, "No Lagna house occupant row"
        assert lagna_rows[0]["house"] == 1, f"Lagna should be in house 1, got {lagna_rows[0]['house']}"


class _FakeShashtiamshaCursor:
    """Mimics a psycopg cursor returning the bg_shashtiamsha_deities rows
    (migration 430) with deity_name floored NULL, per canonical-or-floor
    doctrine (M-17)."""
    def __init__(self, rows):
        self._rows = rows

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, *a, **kw):
        return None

    def fetchall(self):
        return self._rows


class _FakeShashtiamshaConn:
    """Fake DB connection for D60 deity-row tests: returns the real
    23-kroora/37-soumya split (deity_name NULL) for every amsa_number 1-60,
    so tests exercise the actual M-17 JOIN path rather than mocking away
    the fix."""
    def __init__(self):
        # Real 23 kroora amsa_numbers (1-based), cross-derived from PyJHora's
        # own jhora.const.shashti_amsa_rulers_kroora -- same data as migration 430.
        kroora = {1, 2, 8, 9, 10, 11, 12, 15, 16, 30, 31, 32, 33, 34, 35,
                  40, 42, 43, 44, 48, 51, 52, 59}
        self._rows = [
            (n, "kroora" if n in kroora else "soumya", None)
            for n in range(1, 61)
        ]

    def cursor(self, row_factory=None):
        return _FakeShashtiamshaCursor(self._rows)


class TestDeityRows:
    def test_d60_deity_rows_built(self):
        m = _mod()
        m._SHASHTIAMSHA_CACHE = None  # force our fake conn's data to be used
        # M-17 fix: D60 quality now resolves via a JOIN against
        # bg_shashtiamsha_deities (migration 430), so this needs a conn.
        rows = m._build_deity_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, 60, "D60", MOCK_VARGA_DATA,
            conn=_FakeShashtiamshaConn())
        assert len(rows) > 0

    def test_d60_quality_non_empty_deity_floored_null(self):
        """M-17: quality (kroora->Malefic/soumya->Benefic) is real and
        non-empty for every graha; deity_name is canonical-or-floor NULL
        (no primary BPHS Ch.7 verse-level citation available) -- so NO
        varga_deity_attribution/deity row should be emitted for D60, only
        varga_deity_attribution/quality rows."""
        m = _mod()
        m._SHASHTIAMSHA_CACHE = None  # force our fake conn's data to be used
        rows = m._build_deity_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, 60, "D60", MOCK_VARGA_DATA,
            conn=_FakeShashtiamshaConn())
        assert rows, "Expected quality rows for D60"
        for r in rows:
            if r["fact_key"] == "quality":
                assert r["fact_value_text"] in ("Malefic", "Benefic"), \
                    f"Bad quality for {r['graha']}: {r['fact_value_text']}"
            elif r["fact_key"] == "deity":
                pytest.fail(
                    f"D60 deity_name must be floored NULL (no row emitted), "
                    f"got a deity row for {r['graha']}")

    def test_d60_no_conn_floors_honestly(self):
        """Without a live conn (cache miss), D60 must floor to zero rows
        rather than fabricate -- canonical-or-floor, not a computable
        substitute."""
        m = _mod()
        m._SHASHTIAMSHA_CACHE = None  # ensure no stale cache from other tests
        rows = m._build_deity_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, 60, "D60", MOCK_VARGA_DATA,
            conn=None)
        assert rows == [], "No conn -> floor to zero rows, never fabricate"
        m._SHASHTIAMSHA_CACHE = None  # reset for subsequent tests

    def test_d9_deity_present(self):
        m = _mod()
        rows = m._build_deity_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, 9, "D9", MOCK_VARGA_DATA)
        assert len(rows) > 0

    def test_d2_deity_surya_or_chandra(self):
        m = _mod()
        rows = m._build_deity_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, 2, "D2", MOCK_VARGA_DATA)
        for r in rows:
            if r["fact_key"] == "deity":
                assert r["fact_value_text"] in ("Surya", "Chandra"), \
                    f"D2 deity expected Surya/Chandra, got {r['fact_value_text']}"

    def test_d108_karma_type_in_set(self):
        m = _mod()
        rows = m._build_d108_karma_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, MOCK_VARGA_DATA)
        valid = {"Sanchita", "Prarabdha", "Agami"}
        for r in rows:
            assert r["fact_value_text"] in valid, \
                f"D108 karma={r['fact_value_text']} not in {valid}"


class TestFormulaVariantRows:
    def test_d2_two_variants(self):
        m = _mod()
        rows = m._build_formula_variant_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, 2, "D2", MOCK_D1_LONGITUDES)
        variants = {r["fact_key"] for r in rows}
        assert "sign_parashari" in variants
        assert "sign_jaimini" in variants

    def test_d3_three_variants(self):
        m = _mod()
        rows = m._build_formula_variant_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, 3, "D3", MOCK_D1_LONGITUDES)
        variants = {r["fact_key"] for r in rows}
        assert "sign_parashari" in variants
        assert "sign_jaimini" in variants
        assert "sign_mooltrikona" in variants

    def test_d2_bodies_count(self):
        m = _mod()
        rows = m._build_formula_variant_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, 2, "D2", MOCK_D1_LONGITUDES)
        # 2 variants × 10 bodies = 20 rows
        assert len(rows) == 2 * len(m.CLASSICAL_BODIES), \
            f"Expected {2 * len(m.CLASSICAL_BODIES)} rows, got {len(rows)}"

    def test_d3_bodies_count(self):
        m = _mod()
        rows = m._build_formula_variant_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, 3, "D3", MOCK_D1_LONGITUDES)
        assert len(rows) == 3 * len(m.CLASSICAL_BODIES), \
            f"Expected {3 * len(m.CLASSICAL_BODIES)} rows, got {len(rows)}"

    def test_non_d2_d3_returns_empty(self):
        m = _mod()
        rows = m._build_formula_variant_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, 9, "D9", MOCK_D1_LONGITUDES)
        assert rows == [], "Non-D2/D3 should return empty"


class TestD30LordPerAmsa:
    def test_60_rows(self):
        m = _mod()
        rows = m._build_d30_lord_per_amsa_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, MOCK_BUILD_ID)
        assert len(rows) == 60, f"Expected 60 D30 lord rows, got {len(rows)}"

    def test_lords_in_5(self):
        m = _mod()
        rows = m._build_d30_lord_per_amsa_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, MOCK_BUILD_ID)
        valid_lords = {"Mars", "Saturn", "Jupiter", "Mercury", "Venus"}
        for r in rows:
            assert r["fact_value_text"] in valid_lords, \
                f"D30 lord={r['fact_value_text']} not in {valid_lords}"

    def test_verification_single(self):
        """Stage 2 honest-tiers rewrite (was: test_verification_two_pass,
        asserting varga_d30_lord_per_amsa rows are 'two_pass_verified').
        REWRITTEN, not silently flipped: the D30 khavedamsa lord-per-amsa
        table is a single static lookup, with no independent second
        derivation behind the emitted 'two_pass_verified' literal — the
        recon pass that ruled this writer's Stage 2 fix confirmed
        genuine=EMPTY for the whole writer. Now UNVERIFIED_DEFAULT. Anchored
        to the vocab's canonical constant, not to the writer's own literal,
        so this isn't a tautology over the code under test.
        """
        m = _mod()
        rows = m._build_d30_lord_per_amsa_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, MOCK_BUILD_ID)
        for r in rows:
            assert r["verification_pass_status"] == UNVERIFIED_DEFAULT


class TestVimsopakaRows:
    def test_d1_has_7_rows(self):
        m = _mod()
        rows = m._build_vimsopaka_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, 1, "D1", MOCK_VARGA_DATA)
        assert len(rows) == 7, f"Expected 7 vimsopaka rows for D1, got {len(rows)}"

    def test_non_shodasavarga_returns_empty(self):
        m = _mod()
        # D5 is not in Shodasavarga vimsopaka weights
        rows = m._build_vimsopaka_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, 5, "D5", MOCK_VARGA_DATA)
        assert rows == [], "D5 not in Shodasavarga should return empty"

    def test_contribution_non_negative(self):
        m = _mod()
        rows = m._build_vimsopaka_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, 9, "D9", MOCK_VARGA_DATA)
        for r in rows:
            assert r["fact_value_num"] >= 0, f"Negative vimsopaka contribution for {r['graha']}"


class TestSaptavargajaRows:
    def test_d9_in_saptavarga(self):
        m = _mod()
        assert 9 in m.SAPTAVARGA_SET

    def test_d9_has_7_rows(self):
        m = _mod()
        rows = m._build_saptavargaja_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, 9, "D9", MOCK_VARGA_DATA)
        assert len(rows) == 7, f"Expected 7 saptavargaja rows for D9, got {len(rows)}"

    def test_non_saptavarga_returns_empty(self):
        m = _mod()
        rows = m._build_saptavargaja_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, 5, "D5", MOCK_VARGA_DATA)
        assert rows == [], "D5 not in Saptavarga should return empty"

    def test_own_sign_score_30(self):
        """M-18 fix: classical Saptavargaja Bala has NO separate 'Exalted'
        bucket (that is a distinct Sthana-bala sub-component elsewhere in
        Shadbala) -- own-sign (Swakshetra) scores 30 regardless of varga.
        MOCK_VARGA_DATA already places Mars in its own sign (Aries,
        sign_idx=0, dtab['own']=[0,7]) and Jupiter in its own sign
        (Sagittarius, sign_idx=8, dtab['own']=[8,11])."""
        m = _mod()
        rows = m._build_saptavargaja_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, 9, "D9", MOCK_VARGA_DATA)
        by_graha = {r["graha"]: r for r in rows}
        assert by_graha["Mars"]["fact_value_num"] == 30.0
        assert by_graha["Mars"]["fact_value_text"] == "Own"
        assert by_graha["Jupiter"]["fact_value_num"] == 30.0
        assert by_graha["Jupiter"]["fact_value_text"] == "Own"

    def test_moolatrikona_only_applies_to_d1(self):
        """Moolatrikona (45.0) is a D1/Rasi-only concept per PyJHora's own
        dcf==1 guard in _sapthavargaja_bala_1/_2 -- must NOT fire for D9
        even when a graha sits in its Moolatrikona sign_idx."""
        m = _mod()
        # Sun's Moolatrikona is sign_idx=4 (Leo) per DIGNITY_TABLE["Sun"]["mt"].
        mt_data = {**MOCK_VARGA_DATA,
                   "Sun": {"sign_idx": 4, "sign": "Leo", "sign_id": 5,
                           "degree_in_sign": 10.0, "longitude": 130.0}}
        rows = m._build_saptavargaja_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, 9, "D9", mt_data)
        sun_rows = [r for r in rows if r["graha"] == "Sun"]
        assert sun_rows, "No Sun saptavargaja row"
        # Sun in its own sign (Leo, dtab['own']=[4]) at D9 -> "Own"=30, not
        # Moolatrikona=45 (that branch is gated on varga_n==1 only).
        assert sun_rows[0]["fact_value_num"] == 30.0
        assert sun_rows[0]["fact_value_text"] == "Own"

    def test_compound_relation_matches_classical_hand_derivation(self):
        """M-18: manual classical-rule re-derivation for Sun and Mercury in
        D9 (MOCK_VARGA_DATA), cross-checked against PyJHora's own
        house._get_compound_relationships_of_planets delegation.

        Sun sits in Capricorn (sign_idx=9), lord Saturn (sign_idx=6):
          - Naisargika (natural): Sun-Saturn = enemies (classical BPHS).
          - Tatkalika (temporary): house-distance Sun->Saturn = (6-9)%12=9
            (0-based) = 10th from Sun -> temporary FRIEND (2/3/4/10/11/12
            rule).
          - Compound: natural-enemy + temporary-friend = Sama (neutral) ->
            virupa 7.5.

        Mercury sits in Capricorn (sign_idx=9), same lord Saturn:
          - Naisargika: Mercury has no natural enmity with Saturn (only
            Moon is Mercury's natural enemy) -> neutral.
          - Tatkalika: house-distance Mercury->Saturn = (6-9)%12=9 (0-based)
            = 10th -> temporary FRIEND.
          - Compound: natural-neutral + temporary-friend = Mitra (friend)
            -> virupa 15.0.
        """
        m = _mod()
        rows = m._build_saptavargaja_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, 9, "D9", MOCK_VARGA_DATA)
        by_graha = {r["graha"]: r for r in rows}
        assert by_graha["Sun"]["fact_value_text"] == "Sama"
        assert by_graha["Sun"]["fact_value_num"] == 7.5
        assert by_graha["Mercury"]["fact_value_text"] == "Mitra"
        assert by_graha["Mercury"]["fact_value_num"] == 15.0


class TestAshtakavargaRows:
    """M-4 fix: BAV/SAV now delegate to PyJHora's real 8x8 contributor-map
    engine (jhora.horoscope.chart.ashtakavarga.get_ashtaka_varga) instead of
    the removed hand-rolled loop that credited every contributor to every
    graha's grid identically (making all 8 BAVs -- and SAV -- degenerate
    8x-duplicates of one array)."""

    def test_sav_classical_invariant_337(self):
        """Sarvashtakavarga sum across all 12 signs is a pure combinatorial
        identity of the fixed BENEFIC_HOUSES contributor-list lengths --
        ALWAYS 337 regardless of chart/varga. This is the Ring-1
        self-verification gate documented in _compute_ashtakavarga_bav's
        docstring; independently reproduced here against MOCK_VARGA_DATA."""
        m = _mod()
        positions = {b: MOCK_VARGA_DATA[b]["sign_idx"] for b in MOCK_VARGA_DATA}
        av = m._compute_ashtakavarga_bav(positions)
        assert sum(av["sarva"]) == 337, \
            f"SAV classical invariant violated: sum={sum(av['sarva'])}"

    def test_bav_grids_are_not_all_identical(self):
        """The core M-4 bug: every BAV grid degenerate-duplicated one array.
        Assert at least two grahas' BAV grids differ (they must, for a
        real chart -- this is the direct regression guard)."""
        m = _mod()
        positions = {b: MOCK_VARGA_DATA[b]["sign_idx"] for b in MOCK_VARGA_DATA}
        av = m._compute_ashtakavarga_bav(positions)
        bindus = av["bav"]
        grids = list(bindus.values())
        assert not all(g == grids[0] for g in grids), \
            "All BAV grids identical -- M-4 loop bug has regressed"

    def test_build_ashtakavarga_rows_emits_8_grids_of_12_plus_sav(self):
        """7 grahas x 12 signs (BAV) + 12 signs (SAV) = 96 rows per varga."""
        m = _mod()
        rows = m._build_ashtakavarga_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, 9, "D9", MOCK_VARGA_DATA)
        assert len(rows) == 96, f"Expected 96 varga_ashtakavarga rows, got {len(rows)}"
        sav_rows = [r for r in rows if r["graha"] == "SARVA"]
        assert len(sav_rows) == 12
        assert sum(r["fact_value_num"] for r in sav_rows) == 337.0

    def test_bindus_bounded_0_to_8(self):
        m = _mod()
        rows = m._build_ashtakavarga_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, 9, "D9", MOCK_VARGA_DATA)
        for r in rows:
            if r["graha"] != "SARVA":
                assert 0 <= r["fact_value_num"] <= 8, \
                    f"{r['graha']} bindu out of [0,8]: {r['fact_value_num']}"


class TestKarakaRows:
    def test_24_rows_total(self):
        """8 karakas × 3 keys (assigned_graha, sign, dignity) = 24 rows."""
        m = _mod()
        rows = m._build_karaka_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, 10, "D10",
            MOCK_VARGA_DATA, MOCK_D1_LONGITUDES)
        assert len(rows) == 24, f"Expected 24 karaka rows, got {len(rows)}"

    def test_all_8_karakas_present(self):
        m = _mod()
        rows = m._build_karaka_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, 10, "D10",
            MOCK_VARGA_DATA, MOCK_D1_LONGITUDES)
        subjects = {r["fact_subject"].split(".")[-1] for r in rows}
        for k in m.JAIMINI_KARAKA_NAMES:
            assert k in subjects, f"Missing karaka {k}"


class TestRollupRows:
    def test_9_rollup_rows(self):
        m = _mod()
        rows = m._build_rollup_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, 1, "D1",
            MOCK_VARGA_DATA, MOCK_VARGA_DATA)
        assert len(rows) == 9, f"Expected 9 rollup rows, got {len(rows)}"

    def test_rollup_keys(self):
        m = _mod()
        rows = m._build_rollup_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, 1, "D1",
            MOCK_VARGA_DATA, MOCK_VARGA_DATA)
        keys = {r["fact_key"] for r in rows}
        required = {"vargottama_count", "exalted_count", "debilitated_count",
                    "overall_dignity_score", "own_sign_count", "friendly_count"}
        for k in required:
            assert k in keys, f"Missing rollup key: {k}"


class TestD9LagnaSpecial:
    def test_2_rows(self):
        m = _mod()
        rows = m._build_d9_lagna_special_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, MOCK_VARGA_DATA)
        assert len(rows) == 2, f"Expected 2 D9 lagna special rows, got {len(rows)}"

    def test_both_flags_present(self):
        m = _mod()
        rows = m._build_d9_lagna_special_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, MOCK_VARGA_DATA)
        keys = {r["fact_key"] for r in rows}
        assert "vargottama_lagna_flag" in keys
        assert "pushkara_lagna_flag" in keys

    def test_taurus_lagna_is_pushkara(self):
        """Taurus (sign_idx=1) is a Pushkara Lagna sign."""
        m = _mod()
        taurus_data = {**MOCK_VARGA_DATA,
                       "Lagna": {"sign_idx": 1, "sign": "Taurus", "sign_id": 2,
                                 "degree_in_sign": 15.0, "longitude": 45.0}}
        rows = m._build_d9_lagna_special_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, taurus_data)
        pushkara_rows = [r for r in rows if r["fact_key"] == "pushkara_lagna_flag"]
        assert pushkara_rows, "No pushkara_lagna_flag row"
        assert pushkara_rows[0]["fact_value_text"] == "True", \
            "Taurus should be Pushkara Lagna"


class TestD27QuadrantRows:
    def test_rows_for_all_bodies(self):
        m = _mod()
        rows = m._build_d27_quadrant_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, MOCK_VARGA_DATA)
        assert len(rows) == len(m.CLASSICAL_BODIES)

    def test_quadrant_valid_values(self):
        m = _mod()
        valid = {"North", "South", "East", "West"}
        rows = m._build_d27_quadrant_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, MOCK_VARGA_DATA)
        for r in rows:
            assert r["fact_value_text"] in valid, \
                f"D27 quadrant={r['fact_value_text']} not valid"

    def test_lagna_aries_east(self):
        """Lagna in Aries (sign_idx=0) → East quadrant."""
        m = _mod()
        rows = m._build_d27_quadrant_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, MOCK_VARGA_DATA)
        lagna_rows = [r for r in rows if r["graha"] == "Lagna"]
        assert lagna_rows, "No Lagna D27 row"
        assert lagna_rows[0]["fact_value_text"] == "East", \
            f"Aries Lagna should be East, got {lagna_rows[0]['fact_value_text']}"

    def test_single_verification(self):
        m = _mod()
        rows = m._build_d27_quadrant_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, MOCK_VARGA_DATA)
        for r in rows:
            assert r["verification_pass_status"] == "single"


class TestCrossVargaHarmonics:
    def _make_all_varga_signs(self, same_sign_count=3):
        """Helper: set body in same sign for exactly N vargas → super_vargottama.
        Uses sign 0 (Aries) for the first N vargas, sign 6 (Libra) for the rest.
        Sign 6 is chosen so that (i % 12) cycles do not accidentally land on 0.
        """
        m = _mod()
        signs = {}
        for body in m.CLASSICAL_BODIES:
            body_signs = {}
            # D1 must be sign 0 (trans_count measures match with D1)
            # first N vargas (incl D1) = sign 0; rest = sign 6
            for i, vn in enumerate(m.ALL_30_VARGAS):
                vid = f"D{vn}"
                body_signs[vid] = 0 if i < same_sign_count else 6
            signs[body] = body_signs
        return signs

    def test_super_vargottama_rows_emitted(self):
        m = _mod()
        all_signs = self._make_all_varga_signs(3)
        rows = m._build_cross_varga_harmonic_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, all_signs)
        cats = {r["fact_category"] for r in rows}
        assert "varga_super_vargottama_flag" in cats

    def test_trikona_rows_emitted(self):
        m = _mod()
        all_signs = self._make_all_varga_signs(3)
        rows = m._build_cross_varga_harmonic_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, all_signs)
        cats = {r["fact_category"] for r in rows}
        assert "varga_trikona_vargottama_flag" in cats

    def test_trans_count_rows_emitted(self):
        m = _mod()
        all_signs = self._make_all_varga_signs(5)
        rows = m._build_cross_varga_harmonic_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, all_signs)
        cats = {r["fact_category"] for r in rows}
        assert "varga_trans_vargottama_count" in cats

    def test_all_bodies_have_super_vargottama_row(self):
        m = _mod()
        all_signs = self._make_all_varga_signs(3)
        rows = m._build_cross_varga_harmonic_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, all_signs)
        sv_rows = [r for r in rows if r["fact_category"] == "varga_super_vargottama_flag"]
        bodies_with_sv = {r["graha"] for r in sv_rows}
        for body in m.CLASSICAL_BODIES:
            assert body in bodies_with_sv, f"Missing super_vargottama for {body}"

    def test_3_vargas_same_sign_is_super(self):
        m = _mod()
        all_signs = self._make_all_varga_signs(3)
        rows = m._build_cross_varga_harmonic_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, all_signs)
        sv_rows = [r for r in rows
                   if r["fact_category"] == "varga_super_vargottama_flag"
                   and r["graha"] == "Sun"]
        assert sv_rows, "No super_vargottama row for Sun"
        assert sv_rows[0]["fact_value_text"] == "True", \
            f"3 same-sign vargas should be super_vargottama=True"

    def test_2_vargas_not_super(self):
        m = _mod()
        all_signs = self._make_all_varga_signs(2)
        rows = m._build_cross_varga_harmonic_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, all_signs)
        sv_rows = [r for r in rows
                   if r["fact_category"] == "varga_super_vargottama_flag"
                   and r["graha"] == "Sun"]
        assert sv_rows, "No super_vargottama row for Sun"
        assert sv_rows[0]["fact_value_text"] == "False", \
            f"2 same-sign vargas should NOT be super_vargottama"


# ── 8. No-narration linter ────────────────────────────────────────────────────

class TestNarrationLinter:
    def test_forbidden_pattern_detected(self):
        m = _mod()
        bad_rows = [{"fact_category": "varga_position", "fact_key": "sign",
                     "fact_value_text": "Sun indicates Capricorn", "citation_human": "test"}]
        findings = m._check_narration(bad_rows)
        assert len(findings) > 0

    def test_clean_rows_pass(self):
        m = _mod()
        clean_rows = [{"fact_category": "varga_position", "fact_key": "sign",
                       "fact_value_text": "Capricorn", "citation_human": "Sun D1 sign: Capricorn."}]
        findings = m._check_narration(clean_rows)
        assert findings == []

    def test_none_value_ignored(self):
        m = _mod()
        rows = [{"fact_category": "varga_dignity", "fact_key": "dignity",
                 "fact_value_text": None, "citation_human": "Sun D1 dignity: Exalted."}]
        findings = m._check_narration(rows)
        assert findings == []


# ── 9. Atomic grain ───────────────────────────────────────────────────────────

class TestAtomicGrain:
    """All rows from builders must have valid atomic grain structure."""

    def _all_rows(self):
        m = _mod()
        all_rows = []
        all_rows += m._build_position_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, 1, "D1",
            MOCK_VARGA_DATA, MOCK_VARGA_DATA)
        all_rows += m._build_dignity_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, 9, "D9", MOCK_VARGA_DATA)
        all_rows += m._build_vargottama_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, 9, "D9",
            MOCK_VARGA_DATA, MOCK_VARGA_DATA)
        all_rows += m._build_house_lord_occupant_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, 1, "D1", MOCK_VARGA_DATA)
        return all_rows

    def test_all_rows_have_citation_ref(self):
        for r in self._all_rows():
            assert r.get("citation_ref"), f"Missing citation_ref: {r.get('fact_key')}"

    def test_all_rows_have_citation_human(self):
        for r in self._all_rows():
            assert r.get("citation_human"), f"Missing citation_human: {r.get('fact_key')}"

    def test_all_rows_valid_verification_status(self):
        """Correctness fix independent of the Stage 2 demotion: this test used
        to hardcode its own copy of the restricted-table vocabulary set
        instead of importing it from brahmagyan.verification_vocab (the
        settled single source of truth per that module's docstring, defect
        #5 in its own changelog). The hand-maintained copy happened to agree
        member-for-member with RESTRICTED_TABLE_VOCAB today, but a future
        change to one would silently desync from the other. Import from
        source instead.
        """
        m = _mod()
        valid = RESTRICTED_TABLE_VOCAB
        for r in self._all_rows():
            status = r.get("verification_pass_status")
            assert status in valid, f"Invalid status={status} for {r.get('fact_key')}"

    def test_no_narration_in_any_row(self):
        m = _mod()
        findings = m._check_narration(self._all_rows())
        assert findings == [], f"Narration found: {findings}"

    def test_all_rows_have_engine_version(self):
        for r in self._all_rows():
            assert r.get("engine_version"), f"Missing engine_version: {r.get('fact_key')}"

    def test_all_rows_have_fact_category(self):
        for r in self._all_rows():
            assert r.get("fact_category"), f"Missing fact_category: {r.get('fact_key')}"


# ── 10. Utility functions ─────────────────────────────────────────────────────

class TestUtilityFunctions:
    def test_fact_id_deterministic(self):
        m = _mod()
        fid1 = m._fact_id("D9", "Sun", "varga_position", "sign",
                           MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID)
        fid2 = m._fact_id("D9", "Sun", "varga_position", "sign",
                           MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID)
        assert fid1 == fid2, "fact_id must be deterministic"

    def test_fact_id_unique_for_different_keys(self):
        m = _mod()
        fid1 = m._fact_id("D9", "Sun", "varga_position", "sign",
                           MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID)
        fid2 = m._fact_id("D9", "Sun", "varga_position", "sign_id",
                           MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID)
        assert fid1 != fid2, "Different keys must produce different fact_ids"

    def test_citation_ref_well_formed(self):
        m = _mod()
        ref = m._citation_ref("varga_position", "D9", "Sun", "sign",
                               MOCK_CHART_ID, MOCK_AYAN, "0.3.0")
        assert ref.startswith("varga_position.D9.Sun.sign@chart=")
        assert "ay=" in ref
        assert "eng=" in ref

    def test_check_near_boundary_at_edge(self):
        m = _mod()
        result = m._check_near_boundary(0.1)  # Near beginning of sign
        assert result["near_sign_boundary"] is True

    def test_check_near_boundary_midpoint(self):
        m = _mod()
        result = m._check_near_boundary(15.0)  # Mid-sign
        assert result["near_sign_boundary"] is False


# ── 11. D30 lord helper ───────────────────────────────────────────────────────

class TestD30LordHelper:
    def test_mars_leads_odd_sign(self):
        m = _mod()
        # Odd sign (sign_idx=0, Aries), 2° → Mars region (0-5)
        assert m._compute_d30_lord(0, 2.0) == "Mars"

    def test_venus_leads_even_sign(self):
        m = _mod()
        # Even sign (sign_idx=1, Taurus), 2° → Venus region (0-5)
        assert m._compute_d30_lord(1, 2.0) == "Venus"

    def test_saturn_odd_sign_middle(self):
        m = _mod()
        # Odd sign (sign_idx=0), 7° → Saturn region (5-10)
        assert m._compute_d30_lord(0, 7.0) == "Saturn"


# ── 12. Pushkara rows ────────────────────────────────────────────────────────

class TestPushkaraRows:
    def test_pushkara_rows_built(self):
        m = _mod()
        rows = m._build_pushkara_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, 9, "D9",
            MOCK_VARGA_DATA, MOCK_D1_LONGITUDES)
        assert len(rows) > 0

    def test_pushkara_bhaga_flag_valid(self):
        m = _mod()
        rows = m._build_pushkara_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, 1, "D1",
            MOCK_VARGA_DATA, MOCK_D1_LONGITUDES)
        bhaga_rows = [r for r in rows if r["fact_category"] == "varga_pushkara_bhaga_flag"]
        for r in bhaga_rows:
            assert r["fact_value_text"] in ("True", "False")


# ── 13. Lal Kitab rows ────────────────────────────────────────────────────────

class TestLalKitabRows:
    def test_d9_has_lal_kitab_rows(self):
        m = _mod()
        rows = m._build_lal_kitab_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, 9, "D9",
            MOCK_VARGA_DATA, MOCK_VARGA_DATA)
        assert len(rows) > 0

    def test_d12_has_lal_kitab_rows(self):
        m = _mod()
        rows = m._build_lal_kitab_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, 12, "D12",
            MOCK_VARGA_DATA, MOCK_VARGA_DATA)
        assert len(rows) > 0

    def test_d1_no_lal_kitab_rows(self):
        m = _mod()
        rows = m._build_lal_kitab_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, 1, "D1",
            MOCK_VARGA_DATA, MOCK_VARGA_DATA)
        assert rows == [], "D1 should have no Lal Kitab rows"


# ── 14. D150/D2700 rishi rows ────────────────────────────────────────────────

class TestRishiRows:
    def test_d150_rishi_rows(self):
        m = _mod()
        rows = m._build_d150_rishi_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, 150, MOCK_VARGA_DATA)
        assert len(rows) > 0

    def test_d2700_rishi_rows(self):
        m = _mod()
        rows = m._build_d150_rishi_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, 2700, MOCK_VARGA_DATA)
        assert len(rows) > 0

    def test_rishi_non_empty(self):
        m = _mod()
        rows = m._build_d150_rishi_rows(
            MOCK_CHART_ID, MOCK_AYAN, MOCK_BUILD_ID, 150, MOCK_VARGA_DATA)
        for r in rows:
            assert r["fact_value_text"], f"Empty rishi for {r['graha']}"
