"""
test_ph_nimitta_robustness_not_fabricated.py -- SS N-341 (PR-H2), audit item B5, as amended
by the SS N-391 FLOOR ruling (Kala review of #3401).

CLAUDE.md §N.8 (Earned-Signal) / §N.7 item 6 (honest null beats invented judgment):
ph_nimitta used to write the CONSTANT `ayanamsha_robustness = 3` on every anchor and
multiply a 0.92 modifier into every posterior, although nothing measures cross-ayanamsha
robustness (kala_convergence carries no such column; the writer reads one ayanamsha per
signal). The rule now is:

  * NimittaContext.ayanamsha_robustness defaults to None (no module default constant),
    the writer's _build_ctx supplies None and the column stays NULL,
  * compute_posterior applies the STRICTEST factor (the floor, 0.80 = the modifier at
    robustness 0) as a stated lower bound -- NOT x1.0, which would make "not measured"
    the best possible score. The lift vector stores that floor number (never null) and
    ayanamsha_robustness_status='not_measured_floor_applied',
  * a caller that supplies a REAL 0..5 measurement still gets the 0.80..1.00 modifier and
    ayanamsha_robustness_status='measured'.

Each behavioural test runs the real function / row builder; the ast guards pin the
default, the derivation of the floor, and that nothing returns the unmeasured case to 1.0.
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


_FLOOR = 0.80          # the strictest factor: modifier at robustness 0
_OLD_CONSTANT = 0.92   # the retired fabricated constant 3 -> 0.80 + 3/5*0.20


class TestComputePosteriorAppliesTheFloorWhenUnmeasured:
    def test_default_call_records_the_floor_status_and_a_non_null_modifier(self):
        _, lift = compute_posterior(0.10, 5.0, 'conditional', 2, 0.4)
        d = lift.as_dict()
        assert d['ayanamsha_robustness_modifier'] == pytest.approx(_FLOOR)
        assert d['ayanamsha_robustness_modifier'] is not None
        assert d['ayanamsha_robustness_status'] == 'not_measured_floor_applied'

    def test_explicit_none_equals_default(self):
        a = compute_posterior(0.10, 5.0, 'conditional', 2, 0.4)
        b = compute_posterior(0.10, 5.0, 'conditional', 2, 0.4, ayanamsha_robustness=None)
        assert a[0] == b[0]
        assert a[1].as_dict() == b[1].as_dict()

    def test_unmeasured_posterior_is_the_other_four_factors_times_the_floor(self):
        # base 0.10, conditional grade 5.0 -> promise 1.75; 2 systems -> activation 1.4;
        # potency 0.4 -> trigger 1.2. 0.10*1.75*1.4*1.2 = 0.294; no clamp is hit.
        p, lift = compute_posterior(0.10, 5.0, 'conditional', 2, 0.4)
        others = lift.base_rate * lift.promise_lift * lift.activation_lift * lift.trigger_lift
        assert others == pytest.approx(0.294, abs=1e-3)
        assert 0.02 < others * _FLOOR < 0.95          # no clamp involved
        assert p == pytest.approx(0.294 * _FLOOR, abs=1e-4)      # 0.2352
        assert p == pytest.approx(0.2352, abs=1e-4)
        # NOT the skipped (x1.0) value, and NOT the retired fabricated 0.92 constant
        assert p != pytest.approx(0.294, abs=1e-3)
        assert p != pytest.approx(0.294 * _OLD_CONSTANT, abs=1e-3)

    def test_floor_versus_old_constant_lowers_the_posterior_by_0_80_over_0_92(self):
        p_floor, _ = compute_posterior(0.10, 5.0, 'conditional', 2, 0.4)
        p_old_constant, _ = compute_posterior(0.10, 5.0, 'conditional', 2, 0.4, ayanamsha_robustness=3)
        assert p_old_constant == pytest.approx(0.2705, abs=1e-4)          # 0.294 * 0.92
        assert p_floor / p_old_constant == pytest.approx(_FLOOR / _OLD_CONSTANT, abs=2e-3)
        assert 1.0 - p_floor / p_old_constant == pytest.approx(0.1304, abs=2e-3)   # about 13% lower

    def test_unmeasured_is_never_better_than_any_measured_value(self):
        p_none, _ = compute_posterior(0.10, 5.0, 'conditional', 2, 0.4)
        for r in range(0, 6):
            p_r, _ = compute_posterior(0.10, 5.0, 'conditional', 2, 0.4, ayanamsha_robustness=r)
            assert p_none <= p_r + 1e-12, f'unmeasured outranks measured robustness {r}'

    def test_a_real_measurement_still_wins_over_the_floor(self):
        _, lift4 = compute_posterior(0.10, 5.0, 'conditional', 2, 0.4, ayanamsha_robustness=4)
        assert lift4.ayanamsha_robustness_modifier == pytest.approx(0.96)
        assert lift4.as_dict()['ayanamsha_robustness_status'] == 'measured'
        _, lift5 = compute_posterior(0.10, 5.0, 'conditional', 2, 0.4, ayanamsha_robustness=5)
        assert lift5.ayanamsha_robustness_modifier == pytest.approx(1.00)
        assert lift5.as_dict()['ayanamsha_robustness_status'] == 'measured'
        # a genuine measured 0 has the same NUMBER as the floor but is a measurement
        _, lift0 = compute_posterior(0.10, 5.0, 'conditional', 2, 0.4, ayanamsha_robustness=0)
        assert lift0.ayanamsha_robustness_modifier == pytest.approx(_FLOOR)
        assert lift0.as_dict()['ayanamsha_robustness_status'] == 'measured'

    def test_status_is_exactly_the_agreed_strings(self):
        from services.ph_nimitta.engine import _robustness_status
        assert _robustness_status(None) == 'not_measured_floor_applied'
        assert _robustness_status(0) == 'measured'
        assert _robustness_status(5) == 'measured'

    def test_floor_is_derived_from_the_measured_mapping(self):
        from services.ph_nimitta import engine as E
        assert E._ROBUSTNESS_FLOOR_MODIFIER == E._measured_modifier(0) == pytest.approx(_FLOOR)
        assert E._robustness_modifier(None) == E._ROBUSTNESS_FLOOR_MODIFIER
        assert all(E._measured_modifier(r) >= E._ROBUSTNESS_FLOOR_MODIFIER for r in range(0, 6))

    def test_lift_vector_is_json_serialisable_with_the_floor_modifier(self):
        import json
        _, lift = compute_posterior(0.10, 5.0, 'conditional', 2, 0.4)
        round_trip = json.loads(json.dumps(lift.as_dict()))
        assert round_trip['ayanamsha_robustness_modifier'] == pytest.approx(_FLOOR)
        assert round_trip['ayanamsha_robustness_status'] == 'not_measured_floor_applied'
        assert set(round_trip) == {
            'base_rate', 'promise_lift', 'activation_lift', 'trigger_lift',
            'ayanamsha_robustness_modifier', 'ayanamsha_robustness_status', 'posterior',
        }


class TestRowBuilderCarriesNoFabricatedRobustness:
    _ROW = {'convergence_id': 42, 'signal_id': '11111111-1111-1111-1111-111111111111'}

    def test_default_context_has_no_robustness(self):
        assert NimittaContext().ayanamsha_robustness is None

    def test_derived_anchor_row_stores_null_robustness(self):
        a = derive_anchor_from_convergence(self._ROW, NimittaContext(), n_independent=4)
        assert a.ayanamsha_robustness is None          # the COLUMN stays NULL
        assert a.lift_vector['ayanamsha_robustness_modifier'] == pytest.approx(_FLOOR)
        assert a.lift_vector['ayanamsha_robustness_status'] == 'not_measured_floor_applied'

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
        assert a.lift_vector['ayanamsha_robustness_status'] == 'not_measured_floor_applied'


# ---------------------------------------------------------------- ast guards


def _is_numeric_const(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) \
        and not isinstance(node.value, bool)


class TestAstGuards:
    def test_engine_robustness_constants_are_only_the_scale_status_and_a_derived_floor(self):
        tree = _tree(_ENGINE)
        found = {}
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name) and 'ROBUSTNESS' in t.id.upper():
                        found[t.id] = node.value
        assert set(found) == {
            '_ROBUSTNESS_MOD_MIN', '_ROBUSTNESS_MOD_SPAN',
            '_ROBUSTNESS_STATUS_MEASURED', '_ROBUSTNESS_STATUS_FLOOR', '_ROBUSTNESS_FLOOR_MODIFIER',
        }, f'unexpected robustness constant(s) in engine: {sorted(found)}'
        floor = found['_ROBUSTNESS_FLOOR_MODIFIER']
        # the floor is DERIVED from the measured mapping (robustness 0), never a literal
        assert isinstance(floor, ast.Call) and isinstance(floor.func, ast.Name) \
            and floor.func.id == '_measured_modifier'
        assert isinstance(floor.args[0], ast.Constant) and floor.args[0].value == 0
        assert found['_ROBUSTNESS_STATUS_FLOOR'].value == 'not_measured_floor_applied'
        assert found['_ROBUSTNESS_STATUS_MEASURED'].value == 'measured'

    def test_nothing_returns_the_unmeasured_case_to_one(self):
        tree = _tree(_ENGINE)
        fns = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
        # (a) _robustness_modifier: the None branch returns the floor name, never a number
        none_branch = next(
            n for n in ast.walk(fns['_robustness_modifier'])
            if isinstance(n, ast.If) and 'ayanamsha_robustness is None' in ast.unparse(n.test)
        )
        ret = [r for r in none_branch.body if isinstance(r, ast.Return)]
        assert len(ret) == 1 and isinstance(ret[0].value, ast.Name) \
            and ret[0].value.id == '_ROBUSTNESS_FLOOR_MODIFIER'
        # (b) no function returns a bare numeric constant 1 / 1.0 from the robustness helpers
        for name in ('_robustness_modifier', '_measured_modifier', '_robustness_term'):
            for r in ast.walk(fns[name]):
                if isinstance(r, ast.Return):
                    assert not _is_numeric_const(r.value), f'{name} returns a literal number'
        # (c) compute_posterior has no "x if rob_mod is None" skip and no numeric-literal IfExp
        for n in ast.walk(fns['compute_posterior']):
            if isinstance(n, ast.IfExp):
                assert 'rob' not in ast.unparse(n.test), ast.unparse(n)
            if isinstance(n, ast.Compare) and 'rob_mod' in ast.unparse(n):
                raise AssertionError(f'compute_posterior branches on rob_mod: {ast.unparse(n)}')
        # (d) the retired skip wording is gone from the engine source
        src = _ENGINE.read_text()
        for stale in ('neutral skip', 'term skipped', 'SKIPS the term', 'SKIPPED when None',
                      'skipped_not_measured', "'not_measured'"):
            assert stale not in src, f'stale skip wording in engine: {stale!r}'

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
