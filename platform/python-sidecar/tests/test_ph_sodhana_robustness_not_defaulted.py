"""
test_ph_sodhana_robustness_not_defaulted.py -- SS N-341 (PR-H2), audit item B6.

CLAUDE.md §N.8 (Earned-Signal) / §N.7 item 6 (honest null beats invented judgment):
ph_sodhana's G-LADDER ceiling (`_g_ladder_ceiling`) filled a missing / NULL
ayanamsha_robustness with 3 (`... if ayanamsha_robustness is not None else 3`), i.e. it
silently applied a 0.92 robustness factor as though 3-of-5 ayanamshas had been measured.
Now NULL means "not measured": the robustness term is SKIPPED (factor 1.0, neutral) and
the skip is recorded (confidence_inflation ledger `ayanamsha_robustness_term`, the
expected-value text, and the chart-wide ceiling_inputs_degenerate detector, which keeps
firing when the ceiling is frozen chart-wide even though the frozen robustness is NULL).

Behavioural tests run the real ceiling / detectors / writer row loader; the ast guard pins
the `else 3` default so it cannot silently return.
"""
from __future__ import annotations

import ast
import pathlib
from unittest.mock import MagicMock

import pytest

from services.ph_sodhana.engine import (
    AnchorRow,
    SodhanaContext,
    _g_ladder_ceiling,
    derive_sodhana_flags,
    detect_ceiling_inputs_degenerate,
    detect_confidence_inflation,
)

_SIDECAR = pathlib.Path(__file__).resolve().parent.parent
_ENGINE = _SIDECAR / 'services' / 'ph_sodhana' / 'engine.py'


def _anchor(**kw) -> AnchorRow:
    d = dict(
        anchor_id='a-1', anchor_source='convergence', domain='career',
        confidence_low=0.40, confidence_high=0.55,
        confidence_basis='structural_not_yet_empirical', magnitude='major',
        falsifier='REFUTED if no career event by 2028-01-01. CONFIRMED if documented.',
        derivation_ledger_jsonb={'anchor_source': 'convergence'},
        dasha_consensus_count=3, ayanamsha_robustness=None, convergence_id=1,
    )
    d.update(kw)
    return AnchorRow(**d)


class TestCeilingSkipsUnmeasuredRobustness:
    def test_null_robustness_is_not_filled_with_three(self):
        # n=3: base (0.50 + 0.15) = 0.65. rob=3 would give 0.65 * 0.92 = 0.598 (the old,
        # fabricated bar); NULL skips the term -> 0.65.
        assert _g_ladder_ceiling(3, None) == pytest.approx(0.65)
        assert _g_ladder_ceiling(3, None) != pytest.approx(_g_ladder_ceiling(3, 3))

    def test_measured_values_unchanged(self):
        assert _g_ladder_ceiling(3, 3) == pytest.approx(0.598)
        assert _g_ladder_ceiling(3, 0) == pytest.approx(0.52)     # measured 0 is not "missing"
        assert _g_ladder_ceiling(6, 5) == pytest.approx(0.80)

    def test_null_ceiling_never_stricter_or_laxer_than_the_best_measured_value(self):
        # The skipped term is the neutral element: identical to the unclamped base ladder.
        for n in range(1, 7):
            assert _g_ladder_ceiling(n, None) == pytest.approx(min(0.80, 0.50 + 0.05 * n))


class TestInflationDetectorRecordsTheSkip:
    def test_confidence_between_old_and_new_bar_is_not_flagged_when_unmeasured(self):
        # 0.62 sits between the fabricated 0.598 bar and the neutral 0.65 bar.
        assert detect_confidence_inflation(_anchor(confidence_high=0.62, ayanamsha_robustness=None)) is None
        assert detect_confidence_inflation(_anchor(confidence_high=0.62, ayanamsha_robustness=3)) is not None

    def test_flag_over_neutral_bar_records_skipped_term(self):
        rec = detect_confidence_inflation(_anchor(confidence_high=0.70, ayanamsha_robustness=None))
        assert rec is not None and rec.anomaly_type == 'confidence_inflation'
        assert rec.derivation_ledger_jsonb['ayanamsha_robustness_term'] == 'skipped_not_measured'
        assert rec.derivation_ledger_jsonb['ceiling'] == pytest.approx(0.65)
        assert 'not measured' in rec.expected_value_text
        assert 'rob=3' not in rec.expected_value_text

    def test_measured_robustness_records_applied_term(self):
        rec = detect_confidence_inflation(_anchor(confidence_high=0.70, ayanamsha_robustness=3))
        assert rec is not None
        assert rec.derivation_ledger_jsonb['ayanamsha_robustness_term'] == 'applied'
        assert 'rob=3' in rec.expected_value_text


class TestCeilingInputsDegenerateKeepsFiringOnNullRobustness:
    def _ctx(self, pairs):
        return SodhanaContext(chart_id='cid', anchors=[
            _anchor(anchor_id=f'a{i}', dasha_consensus_count=n, ayanamsha_robustness=r)
            for i, (n, r) in enumerate(pairs)
        ])

    def test_chart_wide_null_robustness_with_constant_n_is_still_a_frozen_ceiling(self):
        # After the ph_nimitta fix every anchor has NULL robustness and n is constant 0:
        # the ceiling is still one chart-wide number. The detector must not go silent.
        rec = detect_ceiling_inputs_degenerate(self._ctx([(0, None)] * 6))
        assert rec is not None
        assert rec.anomaly_type == 'ceiling_inputs_degenerate'
        assert rec.derivation_ledger_jsonb['constant_ayanamsha_robustness'] is None
        assert 'NULL' in rec.observed_value_text and 'not measured' in rec.observed_value_text
        assert 'ayanamsha_robustness=3' not in rec.observed_value_text

    def test_varying_n_with_null_robustness_is_not_flagged(self):
        assert detect_ceiling_inputs_degenerate(self._ctx([(0, None), (1, None), (2, None), (3, None), (0, None), (1, None)])) is None

    def test_mixed_null_and_measured_robustness_is_variance(self):
        assert detect_ceiling_inputs_degenerate(self._ctx([(0, None), (0, 3), (0, None), (0, 3), (0, None), (0, 3)])) is None

    def test_below_min_anchors_still_no_flag(self):
        assert detect_ceiling_inputs_degenerate(self._ctx([(0, None)] * 4)) is None

    def test_derive_sodhana_flags_runs_clean_on_all_null_robustness(self):
        ctx = self._ctx([(0, None)] * 6)
        flags = derive_sodhana_flags(ctx)          # must not raise on None
        assert {f.anomaly_type for f in flags} >= {'ceiling_inputs_degenerate'}


class TestWriterLoaderKeepsNullNull:
    def test_load_anchors_does_not_coerce_null_robustness(self):
        from pipeline.orchestrator.writers.ph_sodhana import PhSodhanaWriter
        cur = MagicMock()
        cur.__enter__ = MagicMock(return_value=cur)
        cur.__exit__ = MagicMock(return_value=False)
        cur.fetchall.return_value = [{
            'anchor_id': 'a-1', 'anchor_source': 'convergence', 'domain': 'career',
            'confidence_low': 0.4, 'confidence_high': 0.5, 'confidence_basis': 'structural_not_yet_empirical',
            'magnitude': 'major', 'falsifier': 'REFUTED CONFIRMED', 'derivation_ledger_jsonb': {},
            'dasha_consensus_count': None, 'ayanamsha_robustness': None, 'convergence_id': 1,
        }]
        conn = MagicMock()
        conn.cursor.return_value = cur
        anchors = PhSodhanaWriter()._load_anchors(conn, 'chart-1')
        assert anchors[0].ayanamsha_robustness is None


class TestAstGuard:
    def test_no_numeric_default_substituted_for_ayanamsha_robustness(self):
        tree = ast.parse(_ENGINE.read_text(), feature_version=(3, 11))
        offenders = []
        for node in ast.walk(tree):
            if isinstance(node, ast.IfExp):
                mentions = any(isinstance(n, ast.Name) and n.id == 'ayanamsha_robustness'
                               for n in ast.walk(node.test))
                if mentions:
                    for branch in (node.body, node.orelse):
                        if isinstance(branch, ast.Constant) and isinstance(branch.value, (int, float)) \
                                and not isinstance(branch.value, bool):
                            offenders.append(ast.unparse(node))
        assert offenders == [], f'numeric default for ayanamsha_robustness reintroduced: {offenders}'

    def test_ceiling_function_has_no_bare_three(self):
        tree = ast.parse(_ENGINE.read_text(), feature_version=(3, 11))
        fn = next(n for n in ast.walk(tree)
                  if isinstance(n, ast.FunctionDef) and n.name == '_g_ladder_ceiling')
        threes = [n for n in ast.walk(fn) if isinstance(n, ast.Constant)
                  and n.value == 3 and not isinstance(n.value, bool)]
        assert threes == [], '_g_ladder_ceiling must not contain the fabricated default 3'
