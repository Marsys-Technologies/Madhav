"""
test_ph_sodhana_robustness_not_defaulted.py -- SS N-341 (PR-H2), audit item B6, as amended by
the SS N-391 FLOOR ruling (Kala review of #3401, findings 3 and 4).

CLAUDE.md §N.8 (Earned-Signal) / §N.7 item 6 (honest null beats invented judgment):
ph_sodhana's G-LADDER ceiling (`_g_ladder_ceiling`) filled a missing / NULL
ayanamsha_robustness with 3 (`... if ayanamsha_robustness is not None else 3`), i.e. it
silently applied a 0.92 robustness factor as though 3-of-5 ayanamshas had been measured.
Now NULL means "not measured" and takes the STRICTEST factor (0.80, the factor at robustness 0)
as a stated lower bound: NOT x1.0 (that made "not measured" the loosest, best-possible bar) and
not the fabricated 3. The confidence_inflation ledger records `ayanamsha_robustness_term` =
'not_measured_floor_applied' | 'applied'.

detect_ceiling_inputs_degenerate (Kala finding 4) compares the EFFECTIVE factor each anchor's
ceiling used, not the raw column. The pre-fix detector returned None for raw values {None, 5}
although the ceiling was a single chart-wide 0.55; under the floor rule {None, 5} are two
different factors (0.80 / 1.00) so None is the right verdict, while {None, 0} and {5, 7} are
different raw values with ONE effective factor and must fire.
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


_FLOOR = 0.80


class TestCeilingAppliesTheFloorToUnmeasuredRobustness:
    def test_null_robustness_takes_the_strictest_factor(self):
        # n=3: base 0.65. NULL -> 0.65 * 0.80 = 0.52 (the strictest bar). The skipped x1.0 would be
        # 0.65 and the retired fabricated 3 would be 0.598.
        assert _g_ladder_ceiling(3, None) == pytest.approx(0.52)
        assert _g_ladder_ceiling(3, None) != pytest.approx(0.65)
        assert _g_ladder_ceiling(3, None) != pytest.approx(_g_ladder_ceiling(3, 3))
        assert _g_ladder_ceiling(3, None) == pytest.approx(_g_ladder_ceiling(3, 0))

    def test_measured_values_unchanged(self):
        assert _g_ladder_ceiling(3, 3) == pytest.approx(0.598)
        assert _g_ladder_ceiling(3, 0) == pytest.approx(0.52)
        assert _g_ladder_ceiling(6, 5) == pytest.approx(0.80)

    def test_null_ceiling_is_never_laxer_than_any_measured_ceiling(self):
        for n in range(1, 7):
            for r in range(0, 6):
                assert _g_ladder_ceiling(n, None) <= _g_ladder_ceiling(n, r) + 1e-12
            assert _g_ladder_ceiling(n, None) == pytest.approx(min(0.80, (0.50 + 0.05 * n) * _FLOOR))

    def test_floor_is_derived_from_the_measured_scale(self):
        from services.ph_sodhana import engine as E
        assert E._ROBUSTNESS_FLOOR_FACTOR == E._measured_robustness_factor(0) == pytest.approx(_FLOOR)
        assert E._effective_robustness_factor(None) == E._ROBUSTNESS_FLOOR_FACTOR
        assert E._effective_robustness_factor(5) == pytest.approx(1.00)
        assert E._effective_robustness_factor(7) == pytest.approx(1.00)    # clamped like the ceiling


class TestInflationDetectorRecordsTheFloor:
    def test_confidence_above_the_floor_bar_is_flagged_when_unmeasured(self):
        # 0.62 sat between the retired 0.598 bar and the (wrong) skipped 0.65 bar; the floor bar is 0.52.
        assert detect_confidence_inflation(_anchor(confidence_high=0.62, ayanamsha_robustness=None)) is not None
        assert detect_confidence_inflation(_anchor(confidence_high=0.50, ayanamsha_robustness=None)) is None

    def test_flag_records_the_floor_term_and_says_so(self):
        rec = detect_confidence_inflation(_anchor(confidence_high=0.70, ayanamsha_robustness=None))
        assert rec is not None and rec.anomaly_type == 'confidence_inflation'
        assert rec.derivation_ledger_jsonb['ayanamsha_robustness_term'] == 'not_measured_floor_applied'
        assert rec.derivation_ledger_jsonb['ceiling'] == pytest.approx(0.52)
        assert 'not measured' in rec.expected_value_text
        assert 'strictest factor applied as a lower bound' in rec.expected_value_text
        assert 'skipped' not in rec.expected_value_text
        assert 'rob=3' not in rec.expected_value_text

    def test_measured_robustness_records_applied_term(self):
        rec = detect_confidence_inflation(_anchor(confidence_high=0.70, ayanamsha_robustness=3))
        assert rec is not None
        assert rec.derivation_ledger_jsonb['ayanamsha_robustness_term'] == 'applied'
        assert 'rob=3' in rec.expected_value_text

    def test_measured_zero_is_applied_not_floor(self):
        rec = detect_confidence_inflation(_anchor(confidence_high=0.70, ayanamsha_robustness=0))
        assert rec is not None and rec.derivation_ledger_jsonb['ayanamsha_robustness_term'] == 'applied'


class TestCeilingInputsDegenerateComparesTheEffectiveFactor:
    def _ctx(self, pairs):
        return SodhanaContext(chart_id='cid', anchors=[
            _anchor(anchor_id=f'a{i}', dasha_consensus_count=n, ayanamsha_robustness=r)
            for i, (n, r) in enumerate(pairs)
        ])

    @staticmethod
    def _ceilings(ctx):
        return {round(_g_ladder_ceiling(a.dasha_consensus_count, a.ayanamsha_robustness), 9) for a in ctx.anchors}

    def test_all_null_is_one_chart_wide_ceiling_and_fires(self):
        ctx = self._ctx([(0, None)] * 6)
        assert len(self._ceilings(ctx)) == 1
        rec = detect_ceiling_inputs_degenerate(ctx)
        assert rec is not None and rec.anomaly_type == 'ceiling_inputs_degenerate'
        led = rec.derivation_ledger_jsonb
        assert led['constant_ayanamsha_robustness'] is None
        assert led['constant_ayanamsha_robustness_factor'] == pytest.approx(_FLOOR)
        assert led['ayanamsha_robustness_raw_values'] == [None]
        assert 'effective' in rec.observed_value_text and '0.80' in rec.observed_value_text
        assert 'ayanamsha_robustness=3' not in rec.observed_value_text

    def test_all_five_is_one_chart_wide_ceiling_and_fires(self):
        ctx = self._ctx([(0, 5)] * 6)
        assert len(self._ceilings(ctx)) == 1
        rec = detect_ceiling_inputs_degenerate(ctx)
        assert rec is not None
        assert rec.derivation_ledger_jsonb['constant_ayanamsha_robustness'] == 5
        assert rec.derivation_ledger_jsonb['constant_ayanamsha_robustness_factor'] == pytest.approx(1.00)

    def test_kala_finding_4_none_and_five_are_different_effective_factors_so_not_degenerate(self):
        # Reproduced on the pre-fix code (HEAD of the PR): raw {None, 5} -> ONE ceiling (0.55,
        # both mapped to x1.0) and the detector returned None (a false negative). Under the floor
        # rule None -> 0.80 and 5 -> 1.00: the ceiling genuinely varies per anchor.
        ctx = self._ctx([(0, None), (0, 5)] * 3)
        assert len(self._ceilings(ctx)) == 2
        assert detect_ceiling_inputs_degenerate(ctx) is None

    def test_none_and_zero_differ_raw_but_share_one_effective_factor_and_fire(self):
        # A detector comparing the RAW column would see two values and stay silent although the
        # ceiling is one chart-wide number.
        ctx = self._ctx([(0, None), (0, 0)] * 3)
        assert len(self._ceilings(ctx)) == 1
        rec = detect_ceiling_inputs_degenerate(ctx)
        assert rec is not None
        assert rec.derivation_ledger_jsonb['ayanamsha_robustness_raw_values'] == [None, 0]
        assert rec.derivation_ledger_jsonb['constant_ayanamsha_robustness'] is None

    def test_values_above_the_clamp_share_one_effective_factor_and_fire(self):
        ctx = self._ctx([(0, 5), (0, 7)] * 3)
        assert len(self._ceilings(ctx)) == 1
        assert detect_ceiling_inputs_degenerate(ctx) is not None

    def test_mixed_measured_values_are_variance_not_degenerate(self):
        ctx = self._ctx([(0, 1), (0, 3), (0, 2), (0, 5), (0, 4), (0, 3)])
        assert len(self._ceilings(ctx)) > 1
        assert detect_ceiling_inputs_degenerate(ctx) is None

    def test_varying_n_with_null_robustness_is_not_flagged(self):
        assert detect_ceiling_inputs_degenerate(self._ctx([(0, None), (1, None), (2, None), (3, None), (0, None), (1, None)])) is None

    def test_below_min_anchors_still_no_flag(self):
        assert detect_ceiling_inputs_degenerate(self._ctx([(0, None)] * 4)) is None

    def test_derive_sodhana_flags_runs_on_all_null_robustness(self):
        flags = derive_sodhana_flags(self._ctx([(0, None)] * 6))          # must not raise on None
        assert {f.anomaly_type for f in flags} >= {'ceiling_inputs_degenerate'}

    def test_ledger_and_record_are_json_serialisable(self):
        import json
        rec = detect_ceiling_inputs_degenerate(self._ctx([(0, None), (0, 0)] * 3))
        json.dumps(rec.derivation_ledger_jsonb)


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

    def test_floor_is_derived_and_nothing_returns_the_unmeasured_case_to_one(self):
        tree = ast.parse(_ENGINE.read_text(), feature_version=(3, 11))
        consts = {}
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name) and 'ROBUSTNESS' in t.id:
                        consts[t.id] = node.value
        assert '_ROBUSTNESS_TERM_SKIPPED_FACTOR' not in consts, 'the x1.0 skip constant came back'
        floor = consts['_ROBUSTNESS_FLOOR_FACTOR']
        assert isinstance(floor, ast.Call) and floor.func.id == '_measured_robustness_factor' \
            and floor.args[0].value == 0, 'floor must be derived from the measured scale at robustness 0'
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_effective_robustness_factor')
        ifexp = next(n for n in ast.walk(fn) if isinstance(n, ast.IfExp))
        assert isinstance(ifexp.body, ast.Name) and ifexp.body.id == '_ROBUSTNESS_FLOOR_FACTOR'
        for node in ast.walk(tree):                      # no literal 1 / 1.0 on either arm of a robustness IfExp
            if isinstance(node, ast.IfExp) and 'ayanamsha_robustness' in ast.unparse(node.test):
                for br in (node.body, node.orelse):
                    assert not (isinstance(br, ast.Constant) and isinstance(br.value, (int, float))), ast.unparse(node)

    def test_degenerate_detector_uses_the_effective_factor_not_the_raw_column(self):
        tree = ast.parse(_ENGINE.read_text(), feature_version=(3, 11))
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'detect_ceiling_inputs_degenerate')
        calls = {c.func.id for c in ast.walk(fn) if isinstance(c, ast.Call) and isinstance(c.func, ast.Name)}
        assert '_effective_robustness_factor' in calls
        assign = next(a for a in ast.walk(fn) if isinstance(a, ast.Assign)
                      and any(isinstance(t, ast.Name) and t.id == 'rob_values' for t in a.targets))
        assert '_effective_robustness_factor' in ast.unparse(assign.value)
