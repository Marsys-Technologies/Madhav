"""
Tests for A3 fixes to ka_sangam — three remediations:
  B6: C7 enrichment query uses lahiri_chitrapaksha (not bare lahiri)
  B4-src: domain column propagated from MSR signal to convergence row
  O7: Mode D (AV-bindhu) convergence sub-mode

Each fix has a FAIL-BEFORE / PASS-AFTER test as required by the swarm contract.
"""
from __future__ import annotations

import os
import sys
from datetime import date, timedelta
from unittest.mock import MagicMock, patch, call
from typing import Any

import pytest

# Ensure the sidecar root is on sys.path
_SIDECAR = os.path.join(os.path.dirname(__file__), "..", "..")
if _SIDECAR not in sys.path:
    sys.path.insert(0, _SIDECAR)

from services.ka_sangam.engine import (
    EnrichmentContext,
    mode_d_av_bindhu,
    _date_to_jd,
    _SAV_STRONG_THRESHOLD,
    _AV_SCAN_PLANETS,
    _SIGN_NAMES,
)


# ═══════════════════════════════════════════════════════════════════════════════
# B6 — Ayanamsha Key Mismatch (P1)
# FAIL-BEFORE: query contains bare 'lahiri'
# PASS-AFTER:  query contains 'lahiri_chitrapaksha' and NOT bare 'lahiri' (in value position)
# ═══════════════════════════════════════════════════════════════════════════════

class TestB6AyanamshaKey:
    """B6: C7 enrichment query must use 'lahiri_chitrapaksha', not bare 'lahiri'."""

    _writer_path = os.path.join(
        os.path.dirname(__file__), "..", "..",
        "pipeline", "orchestrator", "writers", "ka_sangam.py"
    )

    def _read_writer(self) -> str:
        with open(self._writer_path) as f:
            return f.read()

    def test_c7_enrichment_uses_lahiri_chitrapaksha(self):
        """
        B6 PASS-AFTER: _build_enrichment_context uses ayanamsha_id = 'lahiri_chitrapaksha'.
        The literal string 'lahiri_chitrapaksha' must appear in the writer source.
        """
        src = self._read_writer()
        assert "'lahiri_chitrapaksha'" in src, (
            "B6: writer must query ayanamsha_id = 'lahiri_chitrapaksha' in _build_enrichment_context"
        )

    def test_c7_enrichment_not_bare_lahiri_in_ayanamsha_query(self):
        """
        B6 PASS-AFTER: the ashtakavarga enrichment query must NOT use the bare string 'lahiri'
        as an ayanamsha_id value (it is a prefix/substring of 'lahiri_chitrapaksha', but the
        literal equality must not match the old value).

        We verify by checking no ayanamsha_id = 'lahiri' line exists in the enrichment block
        (i.e. the only occurrence of ayanamsha_id = 'lahiri' in the comment is replaced
        by 'lahiri_chitrapaksha' in the WHERE clause).
        """
        src = self._read_writer()
        # After fix, the WHERE clause must NOT contain the bare-'lahiri' equality.
        # The comment may still reference 'lahiri' (that is fine).
        # Check that the word 'lahiri\'' (with closing quote, not chitrapaksha) does not
        # appear in any SQL WHERE clause context.  We look for the old pattern.
        old_pattern = "ayanamsha_id = 'lahiri'"
        # Old pattern must NOT appear as a standalone SQL equality (without _chitrapaksha)
        # Strategy: find occurrences of old_pattern and assert none remain.
        import re
        # Match exactly 'lahiri' (not 'lahiri_chitrapaksha')
        matches = re.findall(r"ayanamsha_id\s*=\s*'lahiri'", src)
        assert not matches, (
            f"B6: old ayanamsha_id = 'lahiri' pattern still present in writer: {matches}"
        )

    def test_c7_enrichment_ayanamsha_key_in_sql_context(self):
        """
        B6 PASS-AFTER: 'lahiri_chitrapaksha' appears within an ayanamsha_id WHERE clause.
        """
        src = self._read_writer()
        import re
        matches = re.findall(r"ayanamsha_id\s*=\s*'lahiri_chitrapaksha'", src)
        assert matches, (
            "B6: no ayanamsha_id = 'lahiri_chitrapaksha' WHERE clause found in writer"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# B4-src — Domain Column Propagation (P1)
# FAIL-BEFORE: 'domain' column absent from INSERT / always None
# PASS-AFTER:  domain column present in INSERT, populated from primary_domain on window
# ═══════════════════════════════════════════════════════════════════════════════

class TestB4SrcDomainPropagation:
    """B4-src: domain must be propagated from MSR signal through to kala_convergence INSERT."""

    _writer_path = os.path.join(
        os.path.dirname(__file__), "..", "..",
        "pipeline", "orchestrator", "writers", "ka_sangam.py"
    )

    def _read_writer(self) -> str:
        with open(self._writer_path) as f:
            return f.read()

    def test_domain_column_in_insert_statement(self):
        """
        B4-src PASS-AFTER: INSERT INTO kala_convergence must include 'domain' in column list.
        """
        src = self._read_writer()
        assert 'domain' in src, "B4-src: 'domain' keyword missing from writer"
        # More specific: domain must appear in the INSERT column list context
        assert 'horizon_tier, domain' in src or 'domain\n' in src or ', domain' in src, (
            "B4-src: 'domain' must appear in the INSERT column list in _insert_windows"
        )

    def test_domains_affected_array_fetched_in_signal_query(self):
        """
        B4-src PASS-AFTER: 'domains_affected_array' must be SELECTed from bodha_msr_signals
        in the plan_substeps signal enrichment query.
        """
        src = self._read_writer()
        assert 'domains_affected_array' in src, (
            "B4-src: 'domains_affected_array' not fetched from bodha_msr_signals"
        )

    def test_primary_domain_key_in_pred_dicts(self):
        """
        B4-src PASS-AFTER: 'primary_domain' must be set on pred_dicts entries.
        """
        src = self._read_writer()
        assert "primary_domain" in src, (
            "B4-src: 'primary_domain' key not set on pred_dicts in plan_substeps"
        )

    def test_domain_propagated_to_window_in_generate_windows(self):
        """
        B4-src PASS-AFTER: _generate_windows must stamp w['primary_domain'] on each window.
        """
        src = self._read_writer()
        assert "w['primary_domain'] = primary_domain" in src, (
            "B4-src: _generate_windows must stamp primary_domain onto each window dict"
        )

    def test_domain_in_insert_values(self):
        """
        B4-src PASS-AFTER: w.get('primary_domain') must appear in the INSERT VALUES tuple.
        """
        src = self._read_writer()
        assert "w.get('primary_domain')" in src, (
            "B4-src: _insert_windows must pass w.get('primary_domain') to INSERT VALUES"
        )

    def test_domain_propagation_end_to_end_logic(self):
        """
        B4-src PASS-AFTER: end-to-end logic check using mock _generate_windows output.

        Simulates a window dict with primary_domain='career' flowing into _insert_windows
        and verifies the INSERT receives 'career' as the domain value.
        """
        # Build a minimal window with primary_domain set
        w = {
            'mode': 'A',
            'window_start': date(2026, 1, 1),
            'window_end':   date(2026, 1, 31),
            'peak_date':    date(2026, 1, 15),
            'convergence_score': 0.72,
            'orb_strength': 0.85,
            'rarity_years': 5.0,
            'constituent_factors': {
                'dasha_score': 0.6,
                'nakshatra': 'Pushya',
            },
            'source_citation': 'mode_a/YOGA/Jupiter@270.0°/2026-01-15',
            'is_off_dasha_discovery': False,
            'signal_id': 'aaaaaaaa-0000-0000-0000-000000000001',
            'primary_domain': 'career',   # B4-src: populated from MSR signal
        }

        # Capture the INSERT call arguments
        mock_cur = MagicMock()
        mock_cur.execute = MagicMock()

        from pipeline.orchestrator.writers.ka_sangam import KaSangamWriter
        writer = KaSangamWriter.__new__(KaSangamWriter)

        writer._insert_windows(mock_cur, 'test-chart-id', [w], 'near')

        # The INSERT must have been called
        assert mock_cur.execute.called, "B4-src: _insert_windows must call cur.execute"

        # Extract the params tuple from the first execute call
        call_args = mock_cur.execute.call_args
        params = call_args[0][1]   # second positional arg = params tuple

        # domain is the last parameter
        domain_value = params[-1]
        assert domain_value == 'career', (
            f"B4-src: expected domain='career' in INSERT params, got {domain_value!r}"
        )

    def test_domain_none_when_signal_has_no_domains(self):
        """
        B4-src PASS-AFTER: domain=None acceptable when source signal has no domain tags.
        """
        w = {
            'mode': 'B',
            'window_start': date(2026, 3, 1),
            'window_end':   date(2026, 3, 31),
            'peak_date':    date(2026, 3, 15),
            'convergence_score': 0.55,
            'orb_strength': 0.65,
            'rarity_years': 2.0,
            'constituent_factors': {},
            'source_citation': 'mode_b/DOSHA/Saturn@0.0°/2026-03-15',
            'is_off_dasha_discovery': True,
            'signal_id': 'bbbbbbbb-0000-0000-0000-000000000002',
            'primary_domain': None,   # no domain tags on this signal
        }

        mock_cur = MagicMock()
        from pipeline.orchestrator.writers.ka_sangam import KaSangamWriter
        writer = KaSangamWriter.__new__(KaSangamWriter)
        writer._insert_windows(mock_cur, 'test-chart-id', [w], 'near')

        call_args = mock_cur.execute.call_args
        params = call_args[0][1]
        domain_value = params[-1]
        assert domain_value is None, (
            f"B4-src: expected domain=None when no signal domains, got {domain_value!r}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# O7 — AV-Bindhu Convergence Sub-Mode (Mode D)
# FAIL-BEFORE: no Mode D function exists; no AV-bindhu windows produced
# PASS-AFTER:  mode_d_av_bindhu produces windows for SAV >= threshold signs;
#              excludes below-threshold signs
# ═══════════════════════════════════════════════════════════════════════════════

class TestO7AvBindhuMode:
    """O7: Mode D AV-bindhu convergence sub-mode tests."""

    def _make_predicate(self, dignity_score: float = 0.8) -> dict:
        return {
            'signal_id': 'dddddddd-0000-0000-0000-000000000001',
            'signature_class': 'YOGA',
            'dignity_score': dignity_score,
            'dasha_eligibility_rule_jsonb': {'eligibility_score': 0.7},
            'transit_trigger_jsonb': {'target_longitude_deg': 270.0, 'orb_deg': 5.0},
            'strength_affliction_hook_jsonb': {},
            'derivation_ledger_jsonb': {},
        }

    def _make_enrichment_with_strong_sign(
        self,
        sign_num: int = 1,    # Aries
        sav: int = 32,        # above 28 threshold
    ) -> EnrichmentContext:
        return EnrichmentContext(
            ashtakavarga_bindu={'SARVA': {sign_num: sav}},
        )

    def _make_enrichment_with_weak_sign(
        self,
        sign_num: int = 2,    # Taurus
        sav: int = 20,        # below 28 threshold
    ) -> EnrichmentContext:
        return EnrichmentContext(
            ashtakavarga_bindu={'SARVA': {sign_num: sav}},
        )

    def _make_gochara_service(self, sign_name: str = 'Aries') -> Any:
        """Build a mock gochara service that returns one ingress for the given sign."""
        mock_gs = MagicMock()

        ingress_ev = MagicMock()
        ingress_ev.event_jd = _date_to_jd(date(2027, 3, 21))  # Saturn enters Aries

        def _find_ingresses(planet, target_sign, start_jd, end_jd):
            if target_sign == sign_name:
                return [ingress_ev]
            return []

        mock_gs.find_ingresses.side_effect = _find_ingresses
        return mock_gs

    # ── Existence ───────────────────────────────────────────────────────────────

    def test_mode_d_function_exists(self):
        """O7: mode_d_av_bindhu must be importable from engine."""
        # Already imported at top of file; this test just makes it explicit
        assert callable(mode_d_av_bindhu), "O7: mode_d_av_bindhu not callable"

    def test_sav_threshold_is_28(self):
        """O7: classical SAV threshold must be 28 (Phaladeepika / BPHS)."""
        assert _SAV_STRONG_THRESHOLD == 28, (
            f"O7: SAV threshold must be 28, got {_SAV_STRONG_THRESHOLD}"
        )

    def test_av_scan_planets_include_slow_movers(self):
        """O7: AV scan planets must include Jupiter and Saturn (slow-moving; meaningful timing)."""
        assert 'Jupiter' in _AV_SCAN_PLANETS, "O7: Jupiter must be in _AV_SCAN_PLANETS"
        assert 'Saturn' in _AV_SCAN_PLANETS, "O7: Saturn must be in _AV_SCAN_PLANETS"

    # ── Core behaviour ─────────────────────────────────────────────────────────

    def test_av_bindhu_produces_windows_for_strong_sign(self):
        """
        O7 PASS-AFTER: mode_d_av_bindhu emits windows when a sign has SAV >= threshold.
        """
        pred      = self._make_predicate()
        ctx       = self._make_enrichment_with_strong_sign(sign_num=1, sav=32)
        mock_gs   = self._make_gochara_service(sign_name='Aries')
        start_jd  = _date_to_jd(date(2026, 1, 1))
        end_jd    = _date_to_jd(date(2030, 1, 1))

        windows = mode_d_av_bindhu(
            predicate=pred,
            horizon_start_jd=start_jd,
            horizon_end_jd=end_jd,
            gochara_service=mock_gs,
            enrichment_context=ctx,
        )

        assert len(windows) > 0, (
            "O7: mode_d_av_bindhu must emit windows for a sign with SAV >= 28"
        )

    def test_av_bindhu_excludes_below_threshold_sign(self):
        """
        O7 PASS-AFTER: mode_d_av_bindhu emits NO windows when all signs have SAV < threshold.
        """
        pred     = self._make_predicate()
        ctx      = self._make_enrichment_with_weak_sign(sign_num=2, sav=20)
        mock_gs  = self._make_gochara_service(sign_name='Taurus')
        start_jd = _date_to_jd(date(2026, 1, 1))
        end_jd   = _date_to_jd(date(2030, 1, 1))

        windows = mode_d_av_bindhu(
            predicate=pred,
            horizon_start_jd=start_jd,
            horizon_end_jd=end_jd,
            gochara_service=mock_gs,
            enrichment_context=ctx,
        )

        assert len(windows) == 0, (
            f"O7: mode_d_av_bindhu must NOT emit windows for SAV=20 (below threshold=28), "
            f"got {len(windows)} windows"
        )

    def test_av_bindhu_threshold_boundary_at_28(self):
        """O7: SAV exactly at threshold (28) → windows emitted (inclusive)."""
        pred     = self._make_predicate()
        ctx      = EnrichmentContext(ashtakavarga_bindu={'SARVA': {9: 28}})  # Sagittarius SAV=28
        mock_gs  = self._make_gochara_service(sign_name='Sagittarius')
        start_jd = _date_to_jd(date(2026, 1, 1))
        end_jd   = _date_to_jd(date(2030, 1, 1))

        windows = mode_d_av_bindhu(
            predicate=pred,
            horizon_start_jd=start_jd,
            horizon_end_jd=end_jd,
            gochara_service=mock_gs,
            enrichment_context=ctx,
        )

        assert len(windows) > 0, (
            "O7: SAV=28 (at threshold) must be INCLUDED (>= not >)"
        )

    def test_av_bindhu_just_below_threshold(self):
        """O7: SAV=27 (one below threshold) → no windows."""
        pred     = self._make_predicate()
        ctx      = EnrichmentContext(ashtakavarga_bindu={'SARVA': {9: 27}})
        mock_gs  = self._make_gochara_service(sign_name='Sagittarius')
        start_jd = _date_to_jd(date(2026, 1, 1))
        end_jd   = _date_to_jd(date(2030, 1, 1))

        windows = mode_d_av_bindhu(
            predicate=pred,
            horizon_start_jd=start_jd,
            horizon_end_jd=end_jd,
            gochara_service=mock_gs,
            enrichment_context=ctx,
        )

        assert len(windows) == 0, (
            "O7: SAV=27 (below threshold=28) must produce 0 windows"
        )

    # ── Window structure ────────────────────────────────────────────────────────

    def test_av_bindhu_windows_have_required_fields(self):
        """O7: all Mode D windows must have the required convergence window fields."""
        pred      = self._make_predicate()
        ctx       = self._make_enrichment_with_strong_sign(sign_num=1, sav=35)
        mock_gs   = self._make_gochara_service(sign_name='Aries')
        start_jd  = _date_to_jd(date(2026, 1, 1))
        end_jd    = _date_to_jd(date(2030, 1, 1))

        windows = mode_d_av_bindhu(
            predicate=pred,
            horizon_start_jd=start_jd,
            horizon_end_jd=end_jd,
            gochara_service=mock_gs,
            enrichment_context=ctx,
        )

        required = {
            'mode', 'window_start', 'window_end', 'peak_date',
            'convergence_score', 'orb_strength', 'constituent_factors',
            'source_citation', 'is_off_dasha_discovery', 'rarity_years',
        }
        for w in windows:
            missing = required - set(w.keys())
            assert not missing, f"O7: Mode D window missing fields: {missing}"

    def test_av_bindhu_mode_field_is_d(self):
        """O7: all Mode D windows must have mode='D'."""
        pred      = self._make_predicate()
        ctx       = self._make_enrichment_with_strong_sign(sign_num=1, sav=35)
        mock_gs   = self._make_gochara_service(sign_name='Aries')
        start_jd  = _date_to_jd(date(2026, 1, 1))
        end_jd    = _date_to_jd(date(2030, 1, 1))

        windows = mode_d_av_bindhu(
            predicate=pred,
            horizon_start_jd=start_jd,
            horizon_end_jd=end_jd,
            gochara_service=mock_gs,
            enrichment_context=ctx,
        )

        for w in windows:
            assert w['mode'] == 'D', f"O7: expected mode='D', got {w['mode']!r}"

    def test_av_bindhu_is_off_dasha_discovery_false(self):
        """O7: Mode D windows must have is_off_dasha_discovery=False (SAV is dasha-independent)."""
        pred      = self._make_predicate()
        ctx       = self._make_enrichment_with_strong_sign(sign_num=1, sav=35)
        mock_gs   = self._make_gochara_service(sign_name='Aries')
        start_jd  = _date_to_jd(date(2026, 1, 1))
        end_jd    = _date_to_jd(date(2030, 1, 1))

        windows = mode_d_av_bindhu(
            predicate=pred,
            horizon_start_jd=start_jd,
            horizon_end_jd=end_jd,
            gochara_service=mock_gs,
            enrichment_context=ctx,
        )

        for w in windows:
            assert w['is_off_dasha_discovery'] is False, (
                "O7: Mode D is dasha-independent by design → is_off_dasha_discovery must be False"
            )

    def test_av_bindhu_convergence_score_range(self):
        """O7: Mode D convergence_score must be in [0, 1]."""
        pred      = self._make_predicate()
        ctx       = self._make_enrichment_with_strong_sign(sign_num=1, sav=50)
        mock_gs   = self._make_gochara_service(sign_name='Aries')
        start_jd  = _date_to_jd(date(2026, 1, 1))
        end_jd    = _date_to_jd(date(2030, 1, 1))

        windows = mode_d_av_bindhu(
            predicate=pred,
            horizon_start_jd=start_jd,
            horizon_end_jd=end_jd,
            gochara_service=mock_gs,
            enrichment_context=ctx,
        )

        for w in windows:
            cs = w['convergence_score']
            assert 0.0 <= cs <= 1.0, f"O7: convergence_score {cs} out of [0,1]"

    def test_av_bindhu_constituent_factors_has_sav_fields(self):
        """O7: constituent_factors must include sav_bindhu and sav_threshold."""
        pred      = self._make_predicate()
        ctx       = self._make_enrichment_with_strong_sign(sign_num=1, sav=35)
        mock_gs   = self._make_gochara_service(sign_name='Aries')
        start_jd  = _date_to_jd(date(2026, 1, 1))
        end_jd    = _date_to_jd(date(2030, 1, 1))

        windows = mode_d_av_bindhu(
            predicate=pred,
            horizon_start_jd=start_jd,
            horizon_end_jd=end_jd,
            gochara_service=mock_gs,
            enrichment_context=ctx,
        )

        for w in windows:
            cf = w.get('constituent_factors', {})
            assert 'sav_bindhu' in cf, "O7: constituent_factors must include 'sav_bindhu'"
            assert 'sav_threshold' in cf, "O7: constituent_factors must include 'sav_threshold'"
            assert cf['sav_bindhu'] == 35, f"O7: sav_bindhu mismatch: {cf['sav_bindhu']}"
            assert cf['sav_threshold'] == 28

    def test_av_bindhu_source_citation_starts_with_mode_d(self):
        """O7: source_citation must start with 'mode_d/'."""
        pred      = self._make_predicate()
        ctx       = self._make_enrichment_with_strong_sign(sign_num=1, sav=35)
        mock_gs   = self._make_gochara_service(sign_name='Aries')
        start_jd  = _date_to_jd(date(2026, 1, 1))
        end_jd    = _date_to_jd(date(2030, 1, 1))

        windows = mode_d_av_bindhu(
            predicate=pred,
            horizon_start_jd=start_jd,
            horizon_end_jd=end_jd,
            gochara_service=mock_gs,
            enrichment_context=ctx,
        )

        for w in windows:
            assert w['source_citation'].startswith('mode_d/'), (
                f"O7: source_citation must start with 'mode_d/', got {w['source_citation']!r}"
            )

    # ── No-gochara guard ────────────────────────────────────────────────────────

    def test_av_bindhu_returns_empty_when_no_gochara(self):
        """O7: mode_d_av_bindhu returns [] when gochara_service is None."""
        pred     = self._make_predicate()
        ctx      = self._make_enrichment_with_strong_sign(sign_num=1, sav=35)
        start_jd = _date_to_jd(date(2026, 1, 1))
        end_jd   = _date_to_jd(date(2030, 1, 1))

        windows = mode_d_av_bindhu(
            predicate=pred,
            horizon_start_jd=start_jd,
            horizon_end_jd=end_jd,
            gochara_service=None,
            enrichment_context=ctx,
        )

        assert windows == [], "O7: must return [] when gochara_service is None"

    def test_av_bindhu_returns_empty_when_no_sarva_data(self):
        """O7: mode_d_av_bindhu returns [] when SARVA data is absent from EnrichmentContext."""
        pred     = self._make_predicate()
        # EnrichmentContext with no SARVA key
        ctx      = EnrichmentContext(ashtakavarga_bindu={'Sun': {1: 5, 2: 3}})
        mock_gs  = self._make_gochara_service(sign_name='Aries')
        start_jd = _date_to_jd(date(2026, 1, 1))
        end_jd   = _date_to_jd(date(2030, 1, 1))

        windows = mode_d_av_bindhu(
            predicate=pred,
            horizon_start_jd=start_jd,
            horizon_end_jd=end_jd,
            gochara_service=mock_gs,
            enrichment_context=ctx,
        )

        assert windows == [], "O7: must return [] when no SARVA key in ashtakavarga_bindu"

    # ── Mode D wired in writer ──────────────────────────────────────────────────

    def test_mode_d_imported_in_writer(self):
        """O7: ka_sangam.py must import mode_d_av_bindhu from the engine."""
        writer_path = os.path.join(
            os.path.dirname(__file__), "..", "..",
            "pipeline", "orchestrator", "writers", "ka_sangam.py"
        )
        with open(writer_path) as f:
            src = f.read()
        assert 'mode_d_av_bindhu' in src, (
            "O7: mode_d_av_bindhu must be imported in ka_sangam.py"
        )

    def test_mode_d_wired_in_generate_windows(self):
        """O7: _generate_windows must call mode_d_av_bindhu."""
        writer_path = os.path.join(
            os.path.dirname(__file__), "..", "..",
            "pipeline", "orchestrator", "writers", "ka_sangam.py"
        )
        with open(writer_path) as f:
            src = f.read()
        # mode_d_av_bindhu must be called (not just imported)
        # Look for call pattern: mode_d_av_bindhu(
        assert 'mode_d_av_bindhu(' in src, (
            "O7: _generate_windows must call mode_d_av_bindhu(...)"
        )

    def test_mode_d_emitted_once_across_multiple_predicates(self):
        """
        O7 BLOCKING FIX: Mode D runs only for first predicate — N predicates must
        produce the same Mode D rows as one predicate, not N×K rows.

        Regression guard for the bug where mode_d_av_bindhu was called inside the
        predicate loop without a guard, producing N×duplicate windows that bypassed
        the dedup key (which includes signal_id, so different signal_ids from
        different predicates created distinct duplicate rows).
        """
        from pipeline.orchestrator.writers.ka_sangam import KaSangamWriter

        # Build 3 predicates with distinct signal_ids (simulates the real N=200 scenario)
        def _make_pred(uid_suffix: str, dignity: float = 0.7) -> dict:
            return {
                'signal_id': f'dddddddd-0000-0000-0000-{uid_suffix}',
                'signature_class': 'YOGA',
                'dignity_score': dignity,
                'primary_domain': 'career',
                'dasha_eligibility_rule_jsonb': {'eligibility_score': 0.7},
                'transit_trigger_jsonb': {'target_longitude_deg': 90.0, 'orb_deg': 5.0},
                'strength_affliction_hook_jsonb': {},
                'derivation_ledger_jsonb': {},
            }

        pred_a = _make_pred('000000000001')
        pred_b = _make_pred('000000000002')
        pred_c = _make_pred('000000000003')
        three_preds = [pred_a, pred_b, pred_c]

        # EnrichmentContext with one strong sign (SAV=32 for Aries)
        ctx = EnrichmentContext(ashtakavarga_bindu={'SARVA': {1: 32}})

        # Gochara service: returns one ingress for Aries (the strong sign)
        mock_gs = MagicMock()
        ingress_ev = MagicMock()
        ingress_ev.event_jd = _date_to_jd(date(2027, 3, 21))

        def _find_ingresses(planet, target_sign, start_jd, end_jd):
            if target_sign == 'Aries':
                return [ingress_ev]
            return []

        mock_gs.find_ingresses.side_effect = _find_ingresses

        start_jd = _date_to_jd(date(2026, 1, 1))
        end_jd   = _date_to_jd(date(2030, 1, 1))

        # Patch Mode A and Mode B to return empty (isolate Mode D behaviour)
        with patch('pipeline.orchestrator.writers.ka_sangam.mode_a_search', return_value=[]), \
             patch('pipeline.orchestrator.writers.ka_sangam.mode_b_sweep', return_value=[]):
            writer = KaSangamWriter.__new__(KaSangamWriter)
            all_windows = writer._generate_windows(
                pred_dicts=three_preds,
                horizon_start=date(2026, 1, 1),
                horizon_end=date(2030, 1, 1),
                dasha_kala_service=MagicMock(),
                gochara_service=mock_gs,
                chart_id='test-chart-id',
                keepalive=None,
                enrichment_context=ctx,
                muhurta_service=None,
            )

        # Compute how many Mode D rows a single predicate produces
        with patch('pipeline.orchestrator.writers.ka_sangam.mode_a_search', return_value=[]), \
             patch('pipeline.orchestrator.writers.ka_sangam.mode_b_sweep', return_value=[]):
            writer2 = KaSangamWriter.__new__(KaSangamWriter)
            single_windows = writer2._generate_windows(
                pred_dicts=[pred_a],
                horizon_start=date(2026, 1, 1),
                horizon_end=date(2030, 1, 1),
                dasha_kala_service=MagicMock(),
                gochara_service=mock_gs,
                chart_id='test-chart-id',
                keepalive=None,
                enrichment_context=ctx,
                muhurta_service=None,
            )

        mode_d_all    = [w for w in all_windows    if w.get('mode') == 'D']
        mode_d_single = [w for w in single_windows if w.get('mode') == 'D']

        assert len(mode_d_single) > 0, (
            "O7 guard test: single predicate produced 0 Mode D windows — "
            "check gochara mock or EnrichmentContext"
        )
        assert len(mode_d_all) == len(mode_d_single), (
            f"O7 BLOCKING: Mode D emitted {len(mode_d_all)} windows for 3 predicates "
            f"but only {len(mode_d_single)} for 1 predicate — "
            f"the guard (pred_dict is pred_dicts[0]) is not working correctly. "
            f"Expected {len(mode_d_single)}, got {len(mode_d_all)}."
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Migration 361 static checks
# ═══════════════════════════════════════════════════════════════════════════════

class TestMigration361:
    """Verify migration 361 SQL file exists and has the expected content."""

    # tests/l3/ → tests/ → python-sidecar/ → platform/ → supabase/migrations/
    _migration_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "..",
        "supabase", "migrations", "361_kala_convergence_domain.sql"
    )

    def _read_migration(self) -> str:
        with open(self._migration_path) as f:
            return f.read()

    def test_migration_file_exists(self):
        """Migration 361 SQL file must exist."""
        assert os.path.isfile(self._migration_path), (
            f"Migration file missing: {self._migration_path}"
        )

    def test_migration_adds_domain_column(self):
        """Migration 361 must add the domain column to kala_convergence."""
        sql = self._read_migration()
        assert 'ADD COLUMN IF NOT EXISTS domain TEXT' in sql, (
            "Migration 361 must contain 'ADD COLUMN IF NOT EXISTS domain TEXT'"
        )

    def test_migration_widens_mode_constraint_to_include_d(self):
        """Migration 361 must widen the mode CHECK constraint to include 'D'."""
        sql = self._read_migration()
        assert "'D'" in sql or "'D'::text" in sql, (
            "Migration 361 must include 'D' in the mode CHECK constraint"
        )
        assert 'kala_convergence_mode_check' in sql, (
            "Migration 361 must reference kala_convergence_mode_check constraint"
        )

    def test_migration_is_idempotent(self):
        """Migration 361 must use IF NOT EXISTS / DROP IF EXISTS patterns."""
        sql = self._read_migration()
        assert 'IF NOT EXISTS' in sql, (
            "Migration 361 must be idempotent (IF NOT EXISTS)"
        )
        assert 'DROP CONSTRAINT IF EXISTS' in sql, (
            "Migration 361 must use DROP CONSTRAINT IF EXISTS before re-adding"
        )
