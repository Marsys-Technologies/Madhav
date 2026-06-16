"""
Tests for bg_nakshatra writer and l0_nakshatra data module.

Runs WITHOUT a real DB connection — validates data module constants
and writer dry_run path. Matching the pattern from existing bg_reference tests.
"""
import pytest
from brahmagyan.l0_nakshatra import (
    NAKSHATRAS_ENRICHED, PADAS, MATRICES,
    seed_nakshatra, _AKSHARAS,
)


# ── Data module: nakshatra rows ───────────────────────────────────────────────

class TestNakshatrasEnriched:
    def test_count_is_28(self):
        assert len(NAKSHATRAS_ENRICHED) == 28

    def test_ids_sequential_1_to_28(self):
        ids = [r['nakshatra_id'] for r in NAKSHATRAS_ENRICHED]
        assert ids == list(range(1, 29))

    def test_all_required_fields_present(self):
        required = [
            'nakshatra_id', 'name_sa_iast', 'name_sa_devanagari', 'name_en',
            'start_longitude', 'end_longitude', 'vimshottari_lord',
            'presiding_deity', 'gana', 'nadi', 'yoni_en', 'yoni_sex',
            'varna', 'tatva', 'guna', 'nakshatra_gender',
            'muhurta_type', 'motivation', 'classical_source',
            'is_gandanta', 'is_mula_sangya', 'is_panchaka', 'is_abhijit',
        ]
        for row in NAKSHATRAS_ENRICHED:
            for field in required:
                assert field in row, f"Row {row['nakshatra_id']} missing '{field}'"

    def test_gana_values_valid(self):
        valid = {"Deva", "Manushya", "Rakshasa"}
        for row in NAKSHATRAS_ENRICHED:
            assert row['gana'] in valid, f"Invalid gana {row['gana']} for nak {row['nakshatra_id']}"

    def test_nadi_values_valid_for_27(self):
        valid = {"Adi", "Madhya", "Antya"}
        for row in NAKSHATRAS_ENRICHED[:27]:
            assert row['nadi'] in valid, f"Invalid nadi {row['nadi']} for nak {row['nakshatra_id']}"

    def test_abhijit_nadi_is_none(self):
        abhijit = NAKSHATRAS_ENRICHED[27]
        assert abhijit['nadi'] is None
        assert abhijit['yoni_en'] is None
        assert abhijit['yoni_sex'] is None

    def test_yoni_sex_is_M_or_F_for_27(self):
        for row in NAKSHATRAS_ENRICHED[:27]:
            assert row['yoni_sex'] in ('M', 'F'), \
                f"Invalid yoni_sex for nak {row['nakshatra_id']}"

    def test_classical_source_non_null(self):
        for row in NAKSHATRAS_ENRICHED:
            assert row['classical_source'], f"Empty classical_source for nak {row['nakshatra_id']}"

    def test_longitudes_sequential(self):
        for i, row in enumerate(NAKSHATRAS_ENRICHED[:27]):
            assert row['start_longitude'] < row['end_longitude']
            if i < 26:
                assert abs(row['end_longitude'] - NAKSHATRAS_ENRICHED[i + 1]['start_longitude']) < 0.01

    def test_abhijit_is_flagged(self):
        abhijit = NAKSHATRAS_ENRICHED[27]
        assert abhijit['is_abhijit'] is True
        assert abhijit['tradition_scope'] == 'abhijit_28fold'

    def test_gandanta_flags(self):
        gandanta_ids = {r['nakshatra_id'] for r in NAKSHATRAS_ENRICHED if r['is_gandanta']}
        # Jyeshtha-Moola junction and Revati must be flagged
        assert 18 in gandanta_ids or 19 in gandanta_ids
        assert 27 in gandanta_ids

    def test_panchaka_is_last_5(self):
        panchaka_ids = {r['nakshatra_id'] for r in NAKSHATRAS_ENRICHED if r['is_panchaka']}
        assert panchaka_ids == {23, 24, 25, 26, 27}, f"Unexpected panchaka: {panchaka_ids}"

    def test_motivation_values_valid(self):
        valid = {"dharma", "artha", "kama", "moksha"}
        for row in NAKSHATRAS_ENRICHED:
            assert row['motivation'] in valid, \
                f"Invalid motivation '{row['motivation']}' for nak {row['nakshatra_id']}"

    # ── FORENSIC: native Moon = Purva Bhadrapada ──────────────────────────────
    def test_forensic_purva_bhadrapada(self):
        pbp = next(r for r in NAKSHATRAS_ENRICHED if r['nakshatra_id'] == 25)
        assert pbp['name_en'] == 'Purva Bhadrapada'
        assert pbp['vimshottari_lord'] == 'jupiter'
        assert pbp['gana'] == 'Manushya'
        assert pbp['nadi'] == 'Adi'
        assert pbp['yoni_en'] == 'Lion'
        assert 'Aja Ekapada' in pbp['presiding_deity']
        assert pbp['shakti'] is not None and len(pbp['shakti']) > 5
        assert pbp['is_panchaka'] is True


# ── Data module: pada rows ────────────────────────────────────────────────────

class TestPadas:
    def test_count_is_108(self):
        assert len(PADAS) == 108

    def test_absolute_pada_sequential(self):
        for i, p in enumerate(PADAS):
            assert p['absolute_pada'] == i + 1

    def test_navamsa_cycle_restarts_every_12(self):
        signs = [p['pada_navamsa_sign'] for p in PADAS]
        assert signs[0] == 'Aries'
        assert signs[11] == 'Pisces'
        assert signs[12] == 'Aries'   # wraps back

    def test_each_nakshatra_has_4_padas(self):
        from collections import Counter
        nak_counts = Counter(p['nakshatra_id'] for p in PADAS)
        for nak_id in range(1, 28):
            assert nak_counts[nak_id] == 4

    def test_akshara_non_null_for_all(self):
        for p in PADAS:
            assert p['pada_akshara'], f"Empty akshara at pada_id={p['pada_id']}"

    def test_aksharas_table_length(self):
        assert len(_AKSHARAS) == 27

    def test_forensic_pbp_pada_1(self):
        pbp_padas = [p for p in PADAS if p['nakshatra_id'] == 25]
        assert pbp_padas[0]['pada_navamsa_sign'] == 'Aries'
        assert pbp_padas[0]['pada_lord'] == 'mars'
        assert pbp_padas[0]['pada_akshara'] == 'Se'
        assert pbp_padas[0]['absolute_pada'] == 97

    def test_classical_source_non_null(self):
        for p in PADAS:
            assert p['classical_source'], f"Empty classical_source at pada {p['pada_id']}"


# ── Data module: matrices ─────────────────────────────────────────────────────

class TestMatrices:
    def test_tara_count_729(self):
        tara = [r for r in MATRICES if r['matrix_type'] == 'tara_kuta']
        assert len(tara) == 729

    def test_nadi_kuta_count_9(self):
        assert len([r for r in MATRICES if r['matrix_type'] == 'nadi_kuta']) == 9

    def test_nadi_same_gives_0_points(self):
        nadi = {(r['from_key'], r['to_key']): r['guna_points']
                for r in MATRICES if r['matrix_type'] == 'nadi_kuta'}
        for n in ['Adi', 'Madhya', 'Antya']:
            assert nadi[(n, n)] == 0

    def test_nadi_different_gives_8_points(self):
        nadi = {(r['from_key'], r['to_key']): r['guna_points']
                for r in MATRICES if r['matrix_type'] == 'nadi_kuta'}
        assert nadi[('Adi', 'Madhya')] == 8

    def test_gana_same_gives_6_points(self):
        gana = {(r['from_key'], r['to_key']): r['guna_points']
                for r in MATRICES if r['matrix_type'] == 'gana_kuta'}
        for g in ['Deva', 'Manushya', 'Rakshasa']:
            assert gana[(g, g)] == 6

    def test_tara_self_is_atimitra(self):
        tara = {(r['from_key'], r['to_key']): r['relation_value']
                for r in MATRICES if r['matrix_type'] == 'tara_kuta'}
        for n in range(1, 5):
            assert tara[(str(n), str(n))] == 'Atimitra'

    def test_yoni_count_196(self):
        assert len([r for r in MATRICES if r['matrix_type'] == 'yoni_kuta']) == 196

    def test_yoni_enemy_gives_0_points(self):
        yoni = {(r['from_key'], r['to_key']): r['guna_points']
                for r in MATRICES if r['matrix_type'] == 'yoni_kuta'}
        assert yoni[('Horse', 'Buffalo')] == 0
        assert yoni[('Dog', 'Hare')] == 0

    def test_vashya_count_25(self):
        assert len([r for r in MATRICES if r['matrix_type'] == 'vashya_kuta']) == 25

    def test_mahendra_count_729(self):
        assert len([r for r in MATRICES if r['matrix_type'] == 'mahendra']) == 729

    def test_stree_deergha_count_729(self):
        assert len([r for r in MATRICES if r['matrix_type'] == 'stree_deergha']) == 729

    def test_all_rows_have_classical_source(self):
        for r in MATRICES:
            assert r['classical_source'], \
                f"Empty classical_source for {r['matrix_type']}/{r['from_key']}/{r['to_key']}"

    def test_total_matrix_count(self):
        assert len(MATRICES) == 2721


# ── Writer: dry_run + registration ───────────────────────────────────────────

class TestWriter:
    def test_dry_run_returns_counts(self):
        result = seed_nakshatra(conn=None, build_id="test", dry_run=True)
        assert result['reference_nakshatra'] == 28
        assert result['reference_nakshatra_pada'] == 108
        assert result['reference_nakshatra_matrix'] == 2721

    def test_writer_registers(self):
        from pipeline.orchestrator.writers.bg_nakshatra import NakshatraReferenceWriter  # noqa: F401
        from pipeline.orchestrator.writers import _REGISTRY
        assert 'bg_nakshatra' in _REGISTRY

    def test_writer_has_correct_asset_id(self):
        from pipeline.orchestrator.writers.bg_nakshatra import NakshatraReferenceWriter
        assert NakshatraReferenceWriter.asset_id == 'bg_nakshatra'
