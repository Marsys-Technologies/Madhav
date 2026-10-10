"""Real SQL build readback, class replacement and published-write mutation."""
import ast
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID

import psycopg
import pytest
from psycopg.types.json import Jsonb

from services.kala_core.manifest import open_candidate
from services.ka_sangam.jury import Opinion
from services.kala_core.measure import Interval
from tests.l3.kala_db.conftest import kala_db_dsn
from tests.l3.ka_sangam.test_jury_writer import CHART, GEN, T, api, fixture_input

ROOT = Path(__file__).parents[5]
BUILD = UUID(int=417)


@pytest.fixture
def ctx(kala_db_dsn):
    # The session DB is guarded/disposable. A transactional schema keeps the
    # original K4-2a migration oracles and this writer fixture independent.
    with psycopg.connect(kala_db_dsn) as conn:
        conn.execute('CREATE SCHEMA jury_writer_fixture')
        conn.execute('SET LOCAL search_path TO jury_writer_fixture, public')
        for name in ('1330_kala_layer_manifest_candidates.sql', '1350_kala_jury_candidate.sql'):
            sql = (ROOT / 'migrations' / name).read_text().replace('public.', 'jury_writer_fixture.')
            conn.execute(sql)
        conn.execute('CREATE TABLE kala_convergence(chart_id uuid, legacy_value text)')
        conn.execute('INSERT INTO kala_convergence VALUES (%s,%s)', (CHART, 'legacy-published-value'))
        conn.execute('INSERT INTO kala_layer_head(chart_id,generation) VALUES (%s,%s)',
                     (CHART, 'published:unchanged'))
        open_candidate(conn, chart_id=CHART, generation=GEN, build_id=str(BUILD),
                       model_digest='fixture:model', rule_registry_version='fixture:rules',
                       conventions={'fixture': True, 'time_axis': 'utc_unix_seconds'})
        yield SimpleNamespace(db_conn=conn, build_id=BUILD, dry_run=False,
            config={'chart_id': CHART, 'jury_fixture_inputs': [fixture_input()]})
        conn.rollback()


def writer():
    from pipeline.orchestrator.writers.ka_sangam import KaSangamWriter
    return KaSangamWriter()


def legacy_read(ctx):
    return (ctx.db_conn.execute('SELECT row_to_json(c)::text FROM kala_convergence c').fetchall(),
            ctx.db_conn.execute('SELECT * FROM kala_layer_head').fetchall())


def candidate_read(ctx):
    return tuple(ctx.db_conn.execute('SELECT row_to_json(c)::text FROM ' + table +
        ' c ORDER BY chart_id,generation,event_class,assertion_id').fetchall()
        for table in ('kala_jury_candidate', 'kala_jury_candidate_segment', 'kala_jury_candidate_contest'))


def test_full_direct_build_repeated_readback_preserves_published_output(ctx):
    before = legacy_read(ctx)
    w = writer()
    assert w.run(ctx).rows_inserted == 1
    first = candidate_read(ctx)
    assert w.run(ctx).rows_inserted == 1
    assert candidate_read(ctx) == first
    assert legacy_read(ctx) == before
    row = ctx.db_conn.execute('SELECT conditional_null,pipeline_null_reason,witness_groups,provenance '
                             'FROM kala_jury_candidate').fetchone()
    assert row[0]['estimand'] == 'jury_incremental_agreement'
    assert row[0]['denominator'] == 32
    assert row[1] == 'whole_pipeline_selector_not_supplied'
    assert next(g for g in row[2] if g['group_id'] == 'G-J')['reason'] == 'jaimini_output_missing'
    assert row[3]['acceptance_scope'] == 'fixture_only'


def test_canonical_reading_attachments_round_trip_in_the_candidate_only(ctx):
    from tests.l3.ka_sangam.test_reading_attachments import attachment_input, claim
    value = attachment_input()
    value['reading_claims'].append(claim('MSR:unattached', event=None))
    ctx.config['jury_fixture_inputs'] = [value]
    before = legacy_read(ctx)
    writer().run(ctx)
    row = ctx.db_conn.execute('SELECT assertion_id,provenance FROM kala_jury_candidate').fetchone()
    report = row[1]['reading_attachment_report']
    assert report['forecasts'][0]['forecast']['assertion_ids'] == [row[0]]
    assert report['forecasts'][0]['reading_attachments'] == ['MSR:signal:1']
    assert report['unattached'][0]['claim']['signal_id'] == 'MSR:unattached'
    assert report['unattached'][0]['reason'] == 'event_mapping_unavailable'
    assert len(report['evaluation_clusters'][0]['forecast_ids']) == 1
    first = candidate_read(ctx)
    value['reading_claims'] *= 20
    writer().run(ctx)
    assert candidate_read(ctx) == first
    assert legacy_read(ctx) == before


def test_conflicting_reading_claim_cannot_replace_existing_candidate(ctx):
    from tests.l3.ka_sangam.test_reading_attachments import attachment_input, claim
    writer().run(ctx)
    before = candidate_read(ctx)
    value = attachment_input()
    value['reading_claims'].append(claim(event=None))
    ctx.config['jury_fixture_inputs'] = [value]
    with pytest.raises(ValueError, match='conflicting reading signal'):
        writer().run(ctx)
    assert candidate_read(ctx) == before


def test_plan_has_no_delete_side_effect_and_invalid_second_class_is_atomic(ctx):
    writer().run(ctx)
    before = candidate_read(ctx)
    w = writer()
    assert [s.key for s in w.plan_substeps(ctx)] == ['class:career']
    assert candidate_read(ctx) == before
    ctx.config['jury_fixture_inputs'].append(fixture_input('family', generation='candidate:wrong'))
    with pytest.raises(ValueError):
        w.plan_substeps(ctx)
    assert candidate_read(ctx) == before


def test_partition_replacement_preserves_other_chart_generation_and_class(ctx):
    from services.ka_sangam.jury.candidate import write_candidate, ClassInput
    write_candidate(ctx, ClassInput.model_validate(fixture_input('family')))
    other = 'candidate:other'
    other_ctx = SimpleNamespace(db_conn=ctx.db_conn, build_id=UUID(int=418), dry_run=False,
                                config={'chart_id': CHART})
    open_candidate(ctx.db_conn, chart_id=CHART, generation=other, build_id=str(other_ctx.build_id),
                   model_digest='fixture', rule_registry_version='fixture', conventions={'fixture': True})
    write_candidate(other_ctx, ClassInput.model_validate(fixture_input(generation=other)))
    other_chart = str(UUID(int=419))
    other_chart_ctx = SimpleNamespace(db_conn=ctx.db_conn, build_id=UUID(int=419), dry_run=False,
                                      config={'chart_id': other_chart})
    open_candidate(ctx.db_conn, chart_id=other_chart, generation=GEN, build_id=str(other_chart_ctx.build_id),
                   model_digest='fixture', rule_registry_version='fixture', conventions={'fixture': True})
    write_candidate(other_chart_ctx, ClassInput.model_validate(fixture_input(chart=other_chart)))
    before = candidate_read(ctx)
    writer().run(ctx)
    after = candidate_read(ctx)
    assert all([r for r in a if 'jury:' in r[0] and 'career' not in r[0]] ==
               [r for r in b if 'jury:' in r[0] and 'career' not in r[0]] for a, b in zip(before, after))
    assert ctx.db_conn.execute('SELECT count(*) FROM kala_jury_candidate').fetchone()[0] == 4
    snapshot = candidate_read(ctx)
    writer().run(ctx)
    assert candidate_read(ctx) == snapshot


@pytest.mark.parametrize('state', ['complete', 'verified', 'published', 'rejected'])
def test_nonbuilding_candidate_cannot_be_written(ctx, state):
    ctx.db_conn.execute('UPDATE kala_layer_candidate SET state=%s WHERE build_id=%s', (state, BUILD))
    with pytest.raises(ValueError):
        writer().run(ctx)
    assert candidate_read(ctx) == ([], [], [])


def test_unadmitted_fixture_and_published_head_cannot_be_written(ctx):
    ctx.db_conn.execute('UPDATE kala_layer_candidate SET conventions=%s WHERE build_id=%s',
                        (Jsonb({'fixture': False}), BUILD))
    with pytest.raises(ValueError):
        writer().run(ctx)
    ctx.db_conn.execute('UPDATE kala_layer_candidate SET conventions=%s WHERE build_id=%s',
                        (Jsonb({'fixture': True}), BUILD))
    ctx.db_conn.execute('UPDATE kala_layer_head SET generation=%s', (GEN,))
    with pytest.raises(ValueError):
        writer().run(ctx)


@pytest.mark.parametrize('change', ['chart', 'generation', 'build'])
def test_build_identity_cannot_write_another_partition(ctx, change):
    if change == 'chart':
        ctx.config['chart_id'] = str(UUID(int=999))
    elif change == 'generation':
        ctx.config['jury_fixture_inputs'] = [fixture_input(generation='candidate:wrong')]
    else:
        ctx.build_id = UUID(int=999)
    with pytest.raises(ValueError):
        writer().run(ctx)


def test_contest_retains_opposing_sides_and_duplicate_predicates_do_not_multiply(ctx):
    value = fixture_input()
    value['opinions'] += (replace(value['opinions'][0], conclusion='adverse'),)
    value['opinions'] *= 12
    ctx.config['jury_fixture_inputs'] = [value] * 12
    writer().run(ctx)
    sides = ctx.db_conn.execute('SELECT sides FROM kala_jury_candidate_contest').fetchall()
    assert len(sides) == 1
    assert {s['conclusion'] for s in sides[0][0]} == {'supportive', 'adverse'}
    assert ctx.db_conn.execute('SELECT count(*) FROM kala_jury_candidate').fetchone()[0] == 1


def test_rollback_and_retry_restore_the_whole_class(ctx):
    writer().run(ctx)
    snapshot = candidate_read(ctx)
    ctx.db_conn.execute('SAVEPOINT killed_substep')
    changed = fixture_input()
    changed['uses'] = ()
    changed['opinions'] = ()
    ctx.config['jury_fixture_inputs'] = [changed]
    writer().run(ctx)
    ctx.db_conn.execute('ROLLBACK TO SAVEPOINT killed_substep')
    assert candidate_read(ctx) == snapshot
    ctx.config['jury_fixture_inputs'] = [fixture_input()]
    writer().run(ctx)
    assert candidate_read(ctx) == snapshot


def test_joint_turning_points_retain_each_class_support_and_have_no_boundary_contact(ctx):
    career = fixture_input()
    family = fixture_input('family')
    family['opinions'] = (replace(family['opinions'][0], interval=Interval(T + 5, T + 15)),)
    ctx.config['jury_fixture_inputs'] = [career, family]
    assert writer().run(ctx).rows_inserted == 2
    rows = ctx.db_conn.execute('SELECT provenance FROM kala_jury_candidate').fetchall()
    assert all(r[0]['turning_points'][0]['event_classes'] == ['career', 'family'] for r in rows)
    first = candidate_read(ctx)
    ctx.config['jury_fixture_inputs'] *= 20
    writer().run(ctx)
    assert candidate_read(ctx) == first
    family['opinions'] = (replace(family['opinions'][0], interval=Interval(T + 10, T + 20)),)
    ctx.config['jury_fixture_inputs'] = [career, family]
    writer().run(ctx)
    assert all(r[0]['turning_points'] == [] for r in ctx.db_conn.execute('SELECT provenance FROM kala_jury_candidate'))


def test_published_write_mutant_fails_compatibility_oracle(ctx, monkeypatch):
    module = api()
    source = Path(module.__file__).read_text()
    original = "cursor.execute('DELETE FROM kala_jury_candidate WHERE chart_id=%s AND generation=%s AND event_class=%s', grain)"
    assert source.count(original) == 1
    tree = ast.parse(source.replace(original, original + "\n        cursor.execute('DELETE FROM kala_convergence')"))
    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'write_candidate')
    scope = dict(module.__dict__)
    exec(compile(ast.Module(body=[function], type_ignores=[]), module.__file__, 'exec'), scope)
    monkeypatch.setattr(module, 'write_candidate', scope['write_candidate'])
    with pytest.raises(AssertionError):
        test_full_direct_build_repeated_readback_preserves_published_output(ctx)


@pytest.mark.parametrize('mode', ['selected', 'conditioned', 'testimony', 'outside_coverage', 'selection_ancestry'])
def test_sql_never_stores_unsupported_operational_contest(ctx, mode):
    from tests.l3.ka_sangam.test_candidate_admission import unsupported
    v = unsupported(mode)
    v["opinions"] += (replace(v["opinions"][0], conclusion="adverse"),)
    ctx.config["jury_fixture_inputs"] = [v]
    writer().run(ctx)
    row = ctx.db_conn.execute("SELECT witness_signature FROM kala_jury_candidate").fetchone()
    assert row[0] == []
    assert ctx.db_conn.execute("SELECT count(*) FROM kala_jury_candidate_contest").fetchone()[0] == 0
