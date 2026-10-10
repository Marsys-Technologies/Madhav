"""KYD-139 consumer oracles: real SQL reads, isolation and planning safety."""
from importlib import import_module
from types import SimpleNamespace
from uuid import UUID

import pytest
from psycopg.rows import dict_row, tuple_row

from services.kala_core.manifest import open_candidate
from tests.l3.kala_db.conftest import kala_db_dsn
from tests.l3.kala_db.ka_sangam.test_jury_candidate_end_to_end import ctx, writer, legacy_read
from tests.l3.ka_sangam.test_jury_writer import CHART, GEN, fixture_input


def reader(name):
    if name == 'ka_tulana':
        return import_module('services.ka_tulana.ranker').KaTulanaService()
    module = import_module('pipeline.orchestrator.writers.' + name)
    return getattr(module, {'ka_kala_darshana': 'KaKalaDarshanaWriter',
                            'ka_bhavishya_lekha': 'KaBhavishyaLekhaWriter'}[name])()


READERS = ['ka_kala_darshana', 'ka_bhavishya_lekha', 'ka_tulana']


@pytest.mark.parametrize('name', READERS)
def test_legacy_shim_returns_stored_value_and_never_candidate_fallback(ctx, name):
    writer().run(ctx)
    result = reader(name).read_jury(ctx)
    assert result.rows == ({'chart_id': UUID(CHART), 'legacy_value': 'legacy-published-value'},)


@pytest.mark.parametrize('name', READERS)
def test_candidate_reader_returns_dw_signature_and_named_unavailable_identities(ctx, name):
    writer().run(ctx)
    ctx.db_conn.execute("UPDATE kala_jury_candidate SET conditional_effect=-0.25, "
                        "witness_signature='[\"G-P\",\"G-T\"]'")
    before = legacy_read(ctx)
    view = reader(name).read_jury(ctx, generation=GEN).rows[0]
    assert (view.dw, view.witness_signature) == (-0.25, ('G-P', 'G-T'))
    assert view.acceptance_scope == 'fixture_only'
    assert view.identities == {key: None for key in
                              ('convergence_id', 'signal_id', 'peak_date', 'issuance_identity')}
    assert all(reason == 'stage_to_reader_mapping_unadmitted' for reason in view.unavailable.values())
    assert view.provenance['anchor']['stage'] == 'judge'
    assert legacy_read(ctx) == before


@pytest.mark.parametrize('name', READERS)
@pytest.mark.parametrize('value', [0.0, None])
def test_candidate_zero_and_null_are_never_confidence_defaults(ctx, name, value):
    writer().run(ctx)
    ctx.db_conn.execute('UPDATE kala_jury_candidate SET conditional_effect=%s', (value,))
    assert reader(name).read_jury(ctx, generation=GEN).rows[0].dw == value


@pytest.mark.parametrize('change', ['generation', 'chart', 'build', 'published', 'nonfixture', 'rejected'])
def test_candidate_reader_refuses_wrong_or_unadmitted_binding(ctx, change):
    writer().run(ctx)
    generation = GEN
    if change == 'generation':
        generation = 'candidate:other'
    elif change == 'chart':
        ctx.config['chart_id'] = str(UUID(int=999))
    elif change == 'build':
        ctx.build_id = UUID(int=999)
    elif change == 'published':
        ctx.db_conn.execute('UPDATE kala_layer_head SET generation=%s', (GEN,))
    elif change == 'nonfixture':
        ctx.db_conn.execute("UPDATE kala_layer_candidate SET conventions='{}'")
    else:
        ctx.db_conn.execute("UPDATE kala_layer_candidate SET state='rejected'")
    with pytest.raises(ValueError):
        reader('ka_kala_darshana').read_jury(ctx, generation=generation)


def test_candidate_read_does_not_mutate_in_read_only_transaction(ctx):
    writer().run(ctx)
    # Setting read-only after writes is permitted; subsequent DML is forbidden.
    ctx.db_conn.execute('SET LOCAL transaction_read_only=on')
    assert reader('ka_bhavishya_lekha').read_jury(ctx, generation=GEN).rows[0].event_class == 'career'


@pytest.mark.parametrize('name', READERS[:2])
def test_explicit_candidate_writer_dispatch_cannot_mutate_legacy_outputs(ctx, name):
    writer().run(ctx)
    before = legacy_read(ctx)
    ctx.config['jury_reader_generation'] = GEN
    result = reader(name).run(ctx)
    assert result.rows_inserted == 0
    assert 'stage_to_reader_mapping_unadmitted' in result.notes
    assert legacy_read(ctx) == before


def test_candidate_read_isolation_and_filter_mutations(ctx, monkeypatch):
    from services.ka_sangam.jury import candidate, reader as implementation
    writer().run(ctx)
    other = 'candidate:other'
    other_ctx = SimpleNamespace(db_conn=ctx.db_conn, build_id=UUID(int=418), dry_run=False,
                                config={'chart_id': CHART})
    open_candidate(ctx.db_conn, chart_id=CHART, generation=other, build_id=str(other_ctx.build_id),
                   model_digest='fixture', rule_registry_version='fixture', conventions={'fixture': True})
    candidate.write_candidate(other_ctx, candidate.ClassInput.model_validate(fixture_input(generation=other)))
    other_chart = str(UUID(int=419))
    other_ctx.config['chart_id'] = other_chart
    other_ctx.build_id = UUID(int=419)
    open_candidate(ctx.db_conn, chart_id=other_chart, generation=GEN, build_id=str(other_ctx.build_id),
                   model_digest='fixture', rule_registry_version='fixture', conventions={'fixture': True})
    candidate.write_candidate(other_ctx, candidate.ClassInput.model_validate(fixture_input(chart=other_chart)))

    def isolation_oracle():
        views = reader('ka_kala_darshana').read_jury(ctx, generation=GEN).rows
        assert [(v.chart_id, v.generation) for v in views] == [(CHART, GEN)]

    isolation_oracle()
    original = implementation.CANDIDATE_SQL
    for predicate in ('chart_id=%s', 'generation=%s'):
        monkeypatch.setattr(implementation, 'CANDIDATE_SQL', original.replace(predicate, '%s::text IS NOT NULL'))
        with pytest.raises(AssertionError):
            isolation_oracle()
    monkeypatch.setattr(implementation, 'CANDIDATE_SQL', original)
    isolation_oracle()


def test_legacy_planning_and_reprobe_leave_rows_and_ledger_unchanged(ctx, monkeypatch):
    module = import_module('pipeline.orchestrator.writers.ka_sangam')
    ctx.config.pop('jury_fixture_inputs')
    ctx.db_conn.execute('''CREATE TABLE kala_activation_predicates (
        id int, chart_id uuid, ayanamsha_id text, signal_id uuid, signature_class text,
        dasha_eligibility_rule_jsonb jsonb, transit_trigger_jsonb jsonb,
        strength_affliction_hook_jsonb jsonb, derivation_ledger_jsonb jsonb,
        generation text, mechanism_route text, conclusion_state_jsonb jsonb)''')
    ctx.db_conn.execute('''CREATE TABLE bodha_msr_signals (signal_id uuid, dignity_score float)''')
    ctx.db_conn.execute('''CREATE TABLE build_substep_progress (
        chart_id uuid, asset_id text, substep_key text, build_fingerprint text)''')
    ctx.db_conn.execute("INSERT INTO build_substep_progress VALUES (%s,'ka_sangam','near','stale')", (CHART,))
    for name in ('KaDashaKalaService', 'KaGocharaService', 'KaMuhurtaSevaService'):
        monkeypatch.setattr(module, name, lambda *args: None)
    monkeypatch.setattr(module._LegacyKaSangamWriter, '_build_enrichment_context', lambda *args: None)
    monkeypatch.setattr(module._LegacyKaSangamWriter, '_resolve_native_chart_context', lambda *args: None)
    monkeypatch.setattr(module._LegacyKaSangamWriter, '_derive_birth_year', lambda *args: 1984)
    monkeypatch.setattr(module._LegacyKaSangamWriter, '_build_house_lord_map', lambda *args: {})
    before = legacy_read(ctx)
    for _ in range(2):
        ctx.db_conn.row_factory = dict_row
        assert [s.key for s in writer().plan_substeps(ctx)] == ['near']
        ctx.db_conn.row_factory = tuple_row
        assert legacy_read(ctx) == before
        assert ctx.db_conn.execute('SELECT build_fingerprint FROM build_substep_progress').fetchall() == [('stale',)]
