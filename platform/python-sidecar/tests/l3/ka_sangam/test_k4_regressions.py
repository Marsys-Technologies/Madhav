"""Packet K4 regressions through computation and registered writer boundaries."""
from dataclasses import replace
from datetime import datetime, timezone
from importlib import import_module
from types import SimpleNamespace

import pytest

from services.kala_core.measure import Interval
from tests.l3.ka_sangam.test_jury_writer import api, fixture_input, CHART, GEN, T, H
from tests.l3.ka_sangam.test_jury_qualification import complete_method


def localized_input(start=5, end=10):
    value = fixture_input()
    value['contract_version'] = 'k4-2aw:class_input:v2'
    value['anchor'] = value['anchor'].model_copy(update={'interval':
        value['anchor'].interval.model_copy(update={'t1': datetime.fromtimestamp(T + 10, timezone.utc)})})
    value['experiment_exposure'] = dict(horizon=H, coverage_ref='fixture:coverage',
        source_refs=('fixture:judge', 'fixture:negative_space'))
    value['selection_ancestry'] = dict(assertion_id=value['anchor'].assertion_id,
        method=value['anchor'].method, rule_version=value['anchor'].rule_version,
        source_locator=value['anchor'].source.locator, input_vector_hash=value['anchor'].input_vector_hash,
        parents={'fixture:upstream': ('fixture:judge',)}, review_refs=('fixture:review',))
    method = complete_method(value)
    span = Interval(T + start, T + end)
    value['jaimini'] = replace(method,
        contacts=tuple(replace(c, interval=span) for c in method.contacts),
        assertions=tuple(replace(a, interval=span) for a in method.assertions))
    return value


def capture_writer(monkeypatch):
    statements = []
    class Cursor:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def execute(self, query, params): statements.append((query, params))
    monkeypatch.setattr(api(), 'bind_candidate', lambda ctx, lock: GEN)
    ctx = SimpleNamespace(dry_run=False, build_id='fixture', config={'chart_id': CHART},
                          db_conn=SimpleNamespace(cursor=lambda: Cursor()))
    return ctx, statements


def stored_candidate(monkeypatch, value):
    ctx, statements = capture_writer(monkeypatch)
    ctx.config['jury_fixture_inputs'] = [value]
    writer = import_module('pipeline.orchestrator.writers.ka_sangam').KaSangamWriter()
    assert writer.run(ctx).rows_inserted == 1
    return next(params for query, params in statements if query.startswith('INSERT INTO kala_jury_candidate\n'))


def test_aligned_and_displaced_support_change_compute_and_writer_effect(monkeypatch):
    aligned, displaced = localized_input(), localized_input(15, 20)
    a = api().compute(api().ClassInput.model_validate(aligned)).agreement.conditional
    b = api().compute(api().ClassInput.model_validate(displaced)).agreement.conditional
    # Hand-computed: five of ten selected seconds vs no selected seconds.
    assert (a.observed, b.observed) == (.5, 0.0)
    assert a.effect > 0 and b.effect < 0
    assert a.reason == b.reason == 'exchangeability_not_established'
    assert len(set(a.null_statistics)) > 1
    for value, expected in ((aligned, a), (displaced, b)):
        row = stored_candidate(monkeypatch, value)
        assert row[13] == expected.effect
        assert row[14].obj['observed'] == expected.observed
        assert row[14].obj['denominator'] == 32
        assert row[8].obj['experiment_exposure']['horizon'] == {'start': T, 'end': T + 30}
        assert row[4].timestamp() == T and row[5].timestamp() == T + 10


def test_universal_additional_witness_retains_zero_variance_through_writer(monkeypatch):
    value = localized_input(0, 30)
    result = api().compute(api().ClassInput.model_validate(value)).agreement.conditional
    assert result.observed == 1.0
    assert result.effect == 0.0 and result.reason == 'zero_null_variance'
    row = stored_candidate(monkeypatch, value)
    assert row[13] == 0.0 and row[17] == 'zero_null_variance'


@pytest.mark.parametrize('field', ['experiment_exposure', 'selection_ancestry'])
def test_omitted_required_experiment_metadata_is_refused_before_writes(monkeypatch, field):
    value = localized_input()
    value.pop(field)
    ctx, statements = capture_writer(monkeypatch)
    ctx.config['jury_fixture_inputs'] = [value]
    with pytest.raises(ValueError):
        import_module('pipeline.orchestrator.writers.ka_sangam').KaSangamWriter().run(ctx)
    assert statements == []


def test_original_p8_metadata_omission_is_refused_at_the_writer_boundary(monkeypatch):
    value = fixture_input()
    value['anchor'] = value['anchor'].model_copy(update={'method': 'P8'})
    value.pop('selection_ancestry', None)
    value['jaimini'] = complete_method(value)
    ctx, statements = capture_writer(monkeypatch)
    ctx.config['jury_fixture_inputs'] = [value]
    with pytest.raises(ValueError):
        import_module('pipeline.orchestrator.writers.ka_sangam').KaSangamWriter().run(ctx)
    assert statements == []


@pytest.mark.parametrize('mutation', ['omitted', 'stale_method', 'missing_parent', 'empty', 'wrong_source', 'unresolved_p8'])
def test_p8_without_complete_source_bound_ancestry_cannot_write_credit(monkeypatch, mutation):
    value = localized_input()
    value['anchor'] = value['anchor'].model_copy(update={'method': 'P8'})
    if mutation == 'omitted': value.pop('selection_ancestry')
    elif mutation == 'missing_parent': value['selection_ancestry']['parents'] = {}
    elif mutation == 'empty': value['selection_ancestry']['parents'] = {'fixture:upstream': ()}
    elif mutation == 'wrong_source': value['selection_ancestry']['source_locator'] = 'unbound:source'
    elif mutation == 'unresolved_p8':
        value['selection_ancestry']['method'] = 'P8'
        value['selection_ancestry']['parents'] = {'fixture:upstream': ('P8',)}
    ctx, statements = capture_writer(monkeypatch)
    ctx.config['jury_fixture_inputs'] = [value]
    with pytest.raises(ValueError):
        import_module('pipeline.orchestrator.writers.ka_sangam').KaSangamWriter().run(ctx)
    assert statements == []


def test_bound_p8_ancestry_excludes_gj_contest_and_turning_point_credit(monkeypatch):
    value = localized_input()
    value['jaimini'] = replace(value['jaimini'], assertions=tuple(
        replace(a, conclusion='adverse') for a in value['jaimini'].assertions))
    # Positive control: this actual opposing method creates a contest before
    # its selection ancestry excludes the reused school.
    assert len(api().compute(api().ClassInput.model_validate(value)).contests) == 1
    value['anchor'] = value['anchor'].model_copy(update={'method': 'P8'})
    value['selection_ancestry']['method'] = 'P8'
    value['selection_ancestry']['parents'] = {'fixture:upstream': ('P8', 'jaimini_cara', 'rasi_drishti')}
    result = api().compute(api().ClassInput.model_validate(value))
    assert result.agreement.witness_signature == ('G-P',)
    assert result.contests == ()
    family = localized_input()
    family['anchor'] = family['anchor'].model_copy(update={'subject':
        family['anchor'].subject.model_copy(update={'event_class': 'family'})})
    family['jaimini'] = replace(family['jaimini'], event_class='family')
    family['nodes'] = ()
    family['uses'] = ()
    family['opinions'] = ()
    assert api().joint_turning_points((api().ClassInput.model_validate(localized_input()),
                                     api().ClassInput.model_validate(family)))
    family['anchor'] = family['anchor'].model_copy(update={'method': 'P8'})
    family['selection_ancestry'] = value['selection_ancestry']
    assert api().joint_turning_points((api().ClassInput.model_validate(value),
                                     api().ClassInput.model_validate(family))) == ()
    row = stored_candidate(monkeypatch, value)
    assert row[12].obj == ['G-P']
    assert all('G-J' not in p['groups'] for p in row[8].obj['turning_points'])
    selection = [r for r in row[10].obj if r['role'] == 'selects']
    assert selection and all('jaimini_cara' in r['ancestry'] for r in selection)


@pytest.mark.parametrize('mutation', ['unbound_exposure', 'wrong_coverage', 'outside_exposure',
    'wrong_assertion', 'wrong_hash', 'wrong_rule', 'extra_parent', 'missing_review'])
def test_unlicensed_exposure_or_unbound_ancestry_is_refused(monkeypatch, mutation):
    value = localized_input()
    if mutation == 'unbound_exposure': value['experiment_exposure']['source_refs'] = ('unbound',)
    elif mutation == 'wrong_coverage': value['experiment_exposure']['coverage_ref'] = 'unbound'
    elif mutation == 'outside_exposure': value['experiment_exposure']['horizon'] = Interval(T + 1, T + 30)
    elif mutation == 'wrong_assertion': value['selection_ancestry']['assertion_id'] = 'another:assertion'
    elif mutation == 'wrong_hash': value['selection_ancestry']['input_vector_hash'] = 'b' * 64
    elif mutation == 'wrong_rule': value['selection_ancestry']['rule_version'] = 'unbound'
    elif mutation == 'extra_parent': value['selection_ancestry']['parents']['unbound'] = ('P8',)
    elif mutation == 'missing_review': value['selection_ancestry']['review_refs'] = ()
    ctx, statements = capture_writer(monkeypatch)
    ctx.config['jury_fixture_inputs'] = [value]
    with pytest.raises(ValueError):
        import_module('pipeline.orchestrator.writers.ka_sangam').KaSangamWriter().run(ctx)
    assert statements == []


@pytest.mark.parametrize('function,target,replacement,oracle', [
    ('compute', 'conditioning_intervals=(value.horizon,)',
     'conditioning_intervals=(value.experiment_exposure.horizon,)',
     test_aligned_and_displaced_support_change_compute_and_writer_effect),
    ('_class_evidence', "Use(anchor_id, 'G-P', value.horizon, 'selects', value.selection_ancestry.ancestry)",
     "Use(anchor_id, 'G-P', value.horizon, 'selects')",
     test_bound_p8_ancestry_excludes_gj_contest_and_turning_point_credit),
])
def test_k4_exposure_and_ancestry_mutants_fail_real_oracles(monkeypatch, function, target, replacement, oracle):
    import ast
    from pathlib import Path
    source = Path(api().__file__).read_text()
    assert source.count(target) == 1
    tree = ast.parse(source.replace(target, replacement))
    changed = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == function)
    scope = dict(api().__dict__)
    exec(compile(ast.Module(body=[changed], type_ignores=[]), api().__file__, 'exec'), scope)
    monkeypatch.setattr(api(), function, scope[function])
    with pytest.raises(AssertionError):
        oracle(monkeypatch)


def test_default_dispatch_defers_retirement_without_failing_build_or_changing_legacy_reads(monkeypatch):
    from pipeline.orchestrator.writers import SubStep, WriterResult
    module = import_module('pipeline.orchestrator.writers.ka_sangam')
    ctx, statements = capture_writer(monkeypatch)
    step = SubStep('near')
    calls = []
    monkeypatch.setattr(module._LegacyKaSangamWriter, 'plan_substeps', lambda self, ctx: [step])
    def legacy(self, ctx, received):
        assert received == step
        calls.append(received.key)
        return WriterResult('ka_sangam', 2, notes='legacy fixture output')
    monkeypatch.setattr(module._LegacyKaSangamWriter, 'run_substep', legacy)
    writer = module.KaSangamWriter()
    assert writer.plan_substeps(ctx) == [step]
    result = writer.run(ctx)
    assert result.rows_inserted == 2
    assert calls == ['near']
    assert statements == []
    class StoredCursor:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def execute(self, query, params):
            assert query == 'SELECT * FROM kala_convergence_served WHERE chart_id=%s'     # migration 1405: the stored legacy read is the served partition
            assert params == (CHART,)
        def fetchall(self): return [{'legacy_value': 'published-stored-value', 'confidence_label': 'strong'}]
    ctx.db_conn = SimpleNamespace(cursor=lambda **kwargs: StoredCursor())
    for name, cls in [('ka_kala_darshana', 'KaKalaDarshanaWriter'), ('ka_bhavishya_lekha', 'KaBhavishyaLekhaWriter')]:
        assert getattr(import_module('pipeline.orchestrator.writers.' + name), cls)().read_jury(ctx).rows == (
            {'legacy_value': 'published-stored-value', 'confidence_label': 'strong'},)
    assert import_module('services.ka_tulana.ranker').KaTulanaService().read_jury(ctx).rows == (
        {'legacy_value': 'published-stored-value', 'confidence_label': 'strong'},)
