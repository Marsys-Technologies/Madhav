"""
test_ph_nimitta_robustness_not_fabricated.py -- SS N-341 (PR-H2), audit item B5.

CLAUDE.md §N.8 (Earned-Signal) / §N.7 item 6 (honest null beats invented judgment):
ph_nimitta used to write the CONSTANT `ayanamsha_robustness = 3` on every anchor and
multiply a 0.92 modifier into every posterior, although nothing measures cross-ayanamsha
robustness (kala_convergence carries no such column; the writer reads one ayanamsha per
signal). An unmeasured robustness is now None end to end:

  * NimittaContext.ayanamsha_robustness defaults to None (no module default constant),
  * the writer's _build_ctx supplies None,
  * compute_posterior skips the robustness term and records
    ayanamsha_robustness_modifier=None; the served lift vector (as_dict) adds
    ayanamsha_robustness_status='not_measured',
  * a caller that supplies a REAL 0..5 measurement still gets the 0.80..1.00 modifier.

Each behavioural test runs the real function / row builder; the ast guards pin the
constant and the default so it cannot silently return.
"""
from __future__ import annotations

import ast
import pathlib

import pytest

from services.ph_nimitta.engine import (
    AnchorLiftVector,
    NimittaContext,
    compute_posterior,
    derive_anchor_from_convergence,
)

_SIDECAR = pathlib.Path(__file__).resolve().parent.parent
_ENGINE = _SIDECAR / 'services' / 'ph_nimitta' / 'engine.py'
_WRITER = _SIDECAR / 'pipeline' / 'orchestrator' / 'writers' / 'ph_nimitta.py'


def _tree(path: pathlib.Path) -> ast.AST:
    return ast.parse(path.read_text(), feature_version=(3, 11))


# ---------------------------------------------------------------- behavioural


class TestComputePosteriorSkipsUnmeasuredRobustness:
    def test_default_call_records_not_measured_and_no_modifier(self):
        _, lift = compute_posterior(0.10, 5.0, 'conditional', 2, 0.4)
        d = lift.as_dict()
        assert d['ayanamsha_robustness_modifier'] is None
        assert d['ayanamsha_robustness_status'] == 'not_measured'

    def test_explicit_none_equals_default(self):
        a = compute_posterior(0.10, 5.0, 'conditional', 2, 0.4)
        b = compute_posterior(0.10, 5.0, 'conditional', 2, 0.4, ayanamsha_robustness=None)
        assert a[0] == b[0]
        assert a[1].as_dict() == b[1].as_dict()

    def test_unmeasured_posterior_is_the_product_of_the_other_four_factors(self):
        # base 0.10, conditional grade 5.0 -> promise 1.75; 2 systems -> activation 1.4;
        # potency 0.4 -> trigger 1.2. 0.10*1.75*1.4*1.2 = 0.294 exactly: no 0.92 in it.
        p, lift = compute_posterior(0.10, 5.0, 'conditional', 2, 0.4)
        assert p == pytest.approx(0.294, abs=1e-4)
        # the fabricated constant 3 would have produced 0.294 * 0.92 = 0.2705
        assert p != pytest.approx(0.294 * 0.92, abs=1e-3)
        assert lift.promise_lift * lift.activation_lift * lift.trigger_lift * lift.base_rate == pytest.approx(
            p, abs=1e-3
        )

    def test_a_real_measurement_is_still_honoured(self):
        _, lift4 = compute_posterior(0.10, 5.0, 'conditional', 2, 0.4, ayanamsha_robustness=4)
        assert lift4.ayanamsha_robustness_modifier == pytest.approx(0.96)
        assert lift4.as_dict()['ayanamsha_robustness_status'] == 'measured'
        # a genuine measured 0 is a measurement, not "missing"
        _, lift0 = compute_posterior(0.10, 5.0, 'conditional', 2, 0.4, ayanamsha_robustness=0)
        assert lift0.ayanamsha_robustness_modifier == pytest.approx(0.80)
        assert lift0.as_dict()['ayanamsha_robustness_status'] == 'measured'

    def test_lift_vector_is_json_serialisable_with_null_modifier(self):
        import json
        _, lift = compute_posterior(0.10, 5.0, 'conditional', 2, 0.4)
        round_trip = json.loads(json.dumps(lift.as_dict()))
        assert round_trip['ayanamsha_robustness_modifier'] is None


class TestRowBuilderCarriesNoFabricatedRobustness:
    _ROW = {'convergence_id': 42, 'signal_id': '11111111-1111-1111-1111-111111111111'}

    def test_default_context_has_no_robustness(self):
        assert NimittaContext().ayanamsha_robustness is None

    def test_derived_anchor_row_stores_null_robustness(self):
        a = derive_anchor_from_convergence(self._ROW, NimittaContext(), n_independent=4)
        assert a.ayanamsha_robustness is None
        assert a.lift_vector['ayanamsha_robustness_modifier'] is None
        assert a.lift_vector['ayanamsha_robustness_status'] == 'not_measured'

    def test_writer_build_ctx_supplies_none(self):
        from pipeline.orchestrator.writers.ph_nimitta import PhNimittaWriter
        w = PhNimittaWriter()
        ctx = w._build_ctx({'signal_id': 'sig-1'}, {}, {}, {}, {})
        assert ctx.ayanamsha_robustness is None

    def test_writer_ctx_flows_to_a_null_stored_value(self):
        from pipeline.orchestrator.writers.ph_nimitta import PhNimittaWriter
        w = PhNimittaWriter()
        ctx = w._build_ctx({'signal_id': 'sig-1'}, {}, {}, {}, {})
        a = derive_anchor_from_convergence(self._ROW, ctx, n_independent=4)
        assert a.ayanamsha_robustness is None
        assert a.lift_vector['ayanamsha_robustness_status'] == 'not_measured'


# ---------------------------------------------------------------- ast guards


def _is_numeric_const(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) \
        and not isinstance(node.value, bool)


class TestAstGuards:
    def test_engine_has_no_robustness_default_constant(self):
        tree = _tree(_ENGINE)
        bad = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name) and 'ROBUSTNESS' in t.id.upper() \
                            and 'STATUS' not in t.id.upper():
                        bad.append(t.id)
        assert not bad, f'robustness constant(s) reintroduced in engine: {bad}'

    def test_no_numeric_default_for_ayanamsha_robustness_parameter_or_field(self):
        tree = _tree(_ENGINE)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                args = node.args
                pos = args.posonlyargs + args.args
                defaults = [None] * (len(pos) - len(args.defaults)) + list(args.defaults)
                pairs = list(zip(pos, defaults)) + list(zip(args.kwonlyargs, args.kw_defaults))
                for a, d in pairs:
                    if a.arg == 'ayanamsha_robustness' and d is not None:
                        assert not _is_numeric_const(d), (
                            f'{node.name}(ayanamsha_robustness=<number>) is a fabricated default'
                        )
                        assert isinstance(d, ast.Constant) and d.value is None, (
                            f'{node.name}: ayanamsha_robustness default must be None, got {ast.dump(d)}'
                        )
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) \
                    and node.target.id == 'ayanamsha_robustness' and node.value is not None:
                assert isinstance(node.value, ast.Constant) and node.value.value is None, (
                    'dataclass field ayanamsha_robustness must default to None'
                )

    def test_compute_posterior_default_is_literally_none(self):
        tree = _tree(_ENGINE)
        fn = next(n for n in ast.walk(tree)
                  if isinstance(n, ast.FunctionDef) and n.name == 'compute_posterior')
        names = [a.arg for a in fn.args.args]
        d = fn.args.defaults[names.index('ayanamsha_robustness') - (len(names) - len(fn.args.defaults))]
        assert isinstance(d, ast.Constant) and d.value is None

    def test_writer_never_passes_a_numeric_literal_robustness(self):
        tree = _tree(_WRITER)
        seen = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.keyword) and node.arg == 'ayanamsha_robustness':
                seen += 1
                assert not _is_numeric_const(node.value), (
                    'ph_nimitta writer passes a numeric literal as ayanamsha_robustness '
                    '(fabricated constant, SS N-341 / B5)'
                )
        assert seen >= 1, 'guard is vacuous: writer no longer passes ayanamsha_robustness at all'
