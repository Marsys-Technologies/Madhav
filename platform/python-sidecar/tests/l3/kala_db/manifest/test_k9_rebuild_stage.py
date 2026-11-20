"""K9-4b `k9_rebuild_stage` (ruling SR-PREP-LANES-1 (2)): the production staging of the frozen build_runs row and the ONE open candidate that `orchestrator_rebuild` requires.

Source of each claim: publication.py `_run` / `_candidate` / `inspect_rebuild` (the refusals "candidate build run is absent", "candidate must still be building", "candidate grain plan
must cover every build writer exactly"), manifest.open_candidate (the candidate pins the live head), and the ruling's wording ("never a second frozen row / candidate; names what
exists"). Root CLAUDE.md §N.8: each oracle passes on the real module and FAILS on a copy with that ONE claim's line reverted (the planted reversion). The schema below mirrors the
production DDL of build_runs / build_run_assets (state, action, digest and pair CHECKs; triggered_by NOT NULL) on the disposable cluster; only the columns the staging touches differ.

  S1 what is staged is what `orchestrator_rebuild` then accepts: inspect_rebuild returns PLAN_ONLY for exactly the staged plan, and the frozen manifest validates
  S2 the staged candidate is publishable once its run completes and every planned grain is attested: publication's own grain-plan check accepts it (the grain plan is complete)
  S3 the candidate is `building`, pins the live head as expected_head_generation, and the served head and every other row are untouched
  S4 the plan must be the ordered closed plan; a valid but non-canonical order is refused and nothing is written
  S5 a second staging never happens: an open run / building candidate, or the same run id with different content, is refused BY NAME and writes nothing
  S6 the identical request again is idempotent: ALREADY_STAGED, written False, the database byte-identical
  S7 a served head that differs from the request's expected-head refuses (the exposure readback is stale) and writes nothing
  S8 the natal build must hold chart facts; otherwise refused, nothing written
  S9 the dry run writes nothing: ROLLED_BACK with the rollback read back, and the same request then stages for real
  S10 the CLI prints one JSON document and exits 0 (staged / dry run), 2 (refused)
"""
import contextlib
import importlib.util
import json
import uuid
from pathlib import Path

import psycopg
import pytest

from services.kala_core import publication
from services.kala_core import rebuild_stage as real
from services.kala_core.manifest import attest_grain
from tests.l3.kala_db.manifest.test_publication_ops import db, snapshot  # noqa: F401  (db is a fixture)

CHART = real.CANONICAL_CHART
NATAL = '7377833e-5d3b-4e70-8bef-1318904f470e'
REGISTRY = {'ga_positions': [], 'ka_yojaka': ['ga_positions'], 'ka_vedha_gochara': ['ga_positions'], 'ka_gochara': ['ka_yojaka']}
PLAN = ['ka_vedha_gochara', 'ka_yojaka', 'ka_gochara']       # the registry-derived order: waves [[ka_vedha_gochara, ka_yojaka], [ka_gochara]]
WRITER_ATTESTS = ['ka_yojaka:inputs', 'ka_gochara:inputs'] + [f'ka_vedha_gochara:lahiri_chitrapaksha:{k}' for k in ('house_vedha', 'latta', 'sarvatobhadra')]
DIGESTS = {a: (str(i + 1) * 64) for i, a in enumerate(PLAN)}


def digests(assets):
    return {a: DIGESTS[a] for a in assets}


@pytest.fixture
def staging_db(db):                                           # noqa: F811
    db.execute('DROP TABLE build_runs')
    db.execute('''CREATE TABLE build_runs (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(), chart_id uuid NOT NULL, scope text NOT NULL, scope_target text, action text NOT NULL,
        state text NOT NULL DEFAULT 'planned', plan jsonb NOT NULL, triggered_by text NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
        plan_manifest jsonb, plan_manifest_digest text,
        CONSTRAINT build_runs_action_check CHECK (action = ANY (ARRAY['build','update','rebuild','cascade'])),
        CONSTRAINT build_runs_plan_manifest_digest_check CHECK (plan_manifest_digest IS NULL OR plan_manifest_digest ~ '^[0-9a-f]{64}$'),
        CONSTRAINT build_runs_plan_manifest_pair_check CHECK ((plan_manifest IS NULL) = (plan_manifest_digest IS NULL)),
        CONSTRAINT build_runs_scope_check CHECK (scope = ANY (ARRAY['global','layer','asset','asset_set'])),
        CONSTRAINT build_runs_state_check CHECK (state = ANY (ARRAY['planned','running','paused','completed','stopped','failed'])))''')
    db.execute('''CREATE TABLE build_run_assets (run_id uuid NOT NULL, asset_id text NOT NULL, "position" integer NOT NULL, state text NOT NULL DEFAULT 'queued',
        CONSTRAINT build_run_assets_state_check CHECK (state = ANY (ARRAY['queued','building','complete','skipped','error','aborted'])))''')
    db.execute('''CREATE TABLE asset_registry (asset_id text PRIMARY KEY, scope text NOT NULL DEFAULT 'per_chart', depends_on text[], natural_key_partition text,
        target_table text, is_active boolean NOT NULL DEFAULT true, has_writer boolean NOT NULL DEFAULT true)''')
    for asset, deps in REGISTRY.items():
        db.execute('INSERT INTO asset_registry (asset_id, depends_on, target_table) VALUES (%s,%s,%s)', (asset, deps, 't_' + asset))
    db.execute('CREATE TABLE chart_facts (chart_id uuid NOT NULL, build_id uuid NOT NULL, fact_key text)')
    db.execute('INSERT INTO chart_facts VALUES (%s,%s,%s)', (CHART, NATAL, 'fixture'))
    db.execute("INSERT INTO kala_layer_head (chart_id, generation) VALUES (%s,%s)", (CHART, 'g-0'))
    db.commit()
    return db


def request(**over):
    return dict(run_id=str(uuid.uuid4()), assets=list(PLAN), natal_build=NATAL, expected_head='g-0', commit=True, digest_fn=digests) | over


def stage(module, conn, **over):
    return module.stage(conn, **request(**over))


def counts(conn):
    return {t: conn.execute(f'SELECT count(*) FROM {t}').fetchone()[0] for t in ('build_runs', 'build_run_assets', 'kala_layer_candidate')}


def attempt(module, conn, **over):
    """(result, error text): a refusal of the real module or of a reverted copy (whatever it raises) is data for the oracle, never a harness crash."""
    conn.rollback()
    try:
        return stage(module, conn, **over), None
    except Exception as exc:                                  # noqa: BLE001 -- a reverted module may fail with a database error instead of a named refusal
        conn.rollback()
        return None, f'{type(exc).__name__}: {exc}'


def must_stage(module, conn, **over):
    result, error = attempt(module, conn, **over)
    assert error is None, error
    return result


# ------------------------------------------------------------------ oracles (each takes the module under test and the fixture connection)


def s1(module, conn):
    result = must_stage(module, conn)
    assert result['status'] == 'STAGED' and result['written'] is True
    run_id = result['run_id']
    accepted = publication.inspect_rebuild(conn, run_id=run_id, assets=','.join(PLAN))
    assert accepted['status'] == 'PLAN_ONLY' and accepted['planned_assets'] == PLAN and accepted['run_id'] == run_id
    from pipeline.orchestrator.runner import validate_frozen_run_manifest
    row = conn.execute('SELECT id, chart_id, scope, scope_target, action, plan, state, plan_manifest, plan_manifest_digest FROM build_runs WHERE id=%s', (run_id,)).fetchone()
    frozen = validate_frozen_run_manifest(dict(zip(('id', 'chart_id', 'scope', 'scope_target', 'action', 'plan', 'state', 'plan_manifest', 'plan_manifest_digest'), row)))
    assert frozen.plan == PLAN and frozen.expected_code_digests == digests(PLAN) and row[6] == 'planned' and row[4] == 'rebuild'
    assert frozen.asset_deps['ka_gochara'] == ['ka_yojaka']
    assert conn.execute("SELECT count(*) FROM build_run_assets WHERE run_id=%s AND state='queued'", (run_id,)).fetchone()[0] == len(PLAN)
    with pytest.raises(ValueError):                           # the assets the request names must equal the frozen plan exactly
        publication.inspect_rebuild(conn, run_id=run_id, assets='ka_yojaka')


def s2(module, conn):
    result = must_stage(module, conn)
    run_id, generation = result['run_id'], result['generation']
    conn.execute("UPDATE build_runs SET state='completed' WHERE id=%s", (run_id,))
    cand = conn.execute('SELECT chart_id, build_id, expected_head_generation FROM kala_layer_candidate WHERE build_id=%s', (run_id,)).fetchone()
    from services.kala_core.manifest import Candidate
    c = Candidate(str(cand[0]), generation, str(cand[1]), cand[2])
    plan = conn.execute('SELECT conventions FROM kala_layer_candidate WHERE build_id=%s', (run_id,)).fetchone()[0]['publication_grains']
    for key in WRITER_ATTESTS:                                # what the writers themselves attest (writer_grain.grain_key; ka_vedha_gochara/storage.py:120), stated independently of the module
        attest_grain(conn, c, grain_key=key, result_state='rows', input_vector=key + '-vector')
    conn.commit()
    try:
        candidate, detail = publication._candidate(conn, run_id, generation)         # the very check verify / publish make first
    except Exception as exc:                                                          # noqa: BLE001
        raise AssertionError(f'publication would refuse the staged candidate: {exc}') from exc
    assert candidate.expected_head_generation == 'g-0' and set(detail['run']['plan']) == set(plan) == set(PLAN)
    assert detail['grains'] == tuple(sorted(WRITER_ATTESTS))
    assert plan['ka_gochara'] == ['ka_gochara:inputs']


def s3(module, conn):
    before_head = conn.execute('SELECT chart_id, generation FROM kala_layer_head').fetchall()
    result = must_stage(module, conn)
    staged = result['staged']
    assert staged['candidate']['state'] == 'building' and staged['candidate']['expected_head'] == 'g-0' and staged['candidate']['generation'] == 'candidate:' + result['run_id']
    assert staged['candidate']['natal'] == {'build_id': NATAL, 'ayanamsha_id': real.AYANAMSHA_ID}
    assert conn.execute('SELECT chart_id, generation FROM kala_layer_head').fetchall() == before_head, 'the served head moved'
    assert conn.execute('SELECT count(*) FROM kala_layer_candidate_grain').fetchone()[0] == 0, 'staging attests no grain: that is the writers\' act'
    assert conn.execute("SELECT count(*) FROM kala_layer_candidate WHERE state <> 'building'").fetchone()[0] == 0


def s4(module, conn):
    before = counts(conn)
    result, error = attempt(module, conn, assets=['ka_yojaka', 'ka_vedha_gochara', 'ka_gochara'])      # a valid dependency order that is not the registry-derived one
    assert result is None and error and 'ordered closed plan' in error, error
    result, error = attempt(module, conn, assets=['ka_gochara', 'ka_yojaka', 'ka_vedha_gochara'])        # a dependency violation
    assert result is None and error and 'dependency' in error, error
    result, error = attempt(module, conn, assets=['ka_yojaka', 'ka_not_registered'])
    assert result is None and error and 'ka_not_registered' in error, error
    assert counts(conn) == before, 'a refused plan wrote'
    assert must_stage(module, conn)['status'] == 'STAGED', 'control failed — the closed plan in registry order stages'


def s5(module, conn):
    first = must_stage(module, conn)
    assert first['status'] == 'STAGED'
    before = snapshot(conn), counts(conn)
    result, error = attempt(module, conn)                    # a NEW run id while the first run and candidate are open
    assert result is None and error and first['run_id'] in error and 'open rebuild run' in error, error
    assert (snapshot(conn), counts(conn)) == before, 'a refused second staging wrote'
    same_id, error = attempt(module, conn, run_id=first['run_id'], assets=['ka_vedha_gochara', 'ka_yojaka'])     # the same run id with other content
    assert same_id is None and error and first['run_id'] in error and 'already exists' in error, error
    conn.execute("UPDATE build_runs SET state='completed'")                                                        # the run finished but its candidate still builds
    conn.commit()
    result, error = attempt(module, conn)
    assert result is None and error and 'building candidate' in error and first['generation'] in error, error
    assert counts(conn) == {'build_runs': 1, 'build_run_assets': len(PLAN), 'kala_layer_candidate': 1}


def s6(module, conn):
    first = must_stage(module, conn)
    before = snapshot(conn), counts(conn)
    again = must_stage(module, conn, run_id=first['run_id'])
    assert again['status'] == 'ALREADY_STAGED' and again['written'] is False and again['staged'] == first['staged']
    assert (snapshot(conn), counts(conn)) == before
    changed, error = attempt(module, conn, run_id=first['run_id'], expected_head='g-0', natal_build=str(uuid.uuid4()))
    assert changed is None and error, 'the same run id with another natal build is not the identical request'
    conn.execute("UPDATE build_runs SET state='running'")
    conn.commit()
    started, error = attempt(module, conn, run_id=first['run_id'])
    assert started is None and error and 'already exists' in error and 'running' in error, 'a run that has started is not "already staged"'


def s7(module, conn):
    before = snapshot(conn), counts(conn)
    result, error = attempt(module, conn, expected_head='g-9')
    assert result is None and error and "'g-0'" in error and 'stale' in error, error
    result, error = attempt(module, conn, expected_head='NONE')
    assert result is None and error and 'stale' in error, error
    assert (snapshot(conn), counts(conn)) == before
    conn.execute('DELETE FROM kala_layer_head')
    conn.commit()
    result = must_stage(module, conn, expected_head='NONE')
    assert result['status'] == 'STAGED' and result['staged']['candidate']['expected_head'] is None


def s8(module, conn):
    before = counts(conn)
    result, error = attempt(module, conn, natal_build=str(uuid.uuid4()))
    assert result is None and error and 'natal build' in error, error
    assert counts(conn) == before


def s9(module, conn):
    before = snapshot(conn), counts(conn)
    result = must_stage(module, conn, commit=False)
    assert result['status'] == 'ROLLED_BACK' and result['rollback_confirmed'] is True and result['written'] is False
    conn.rollback()
    assert (snapshot(conn), counts(conn)) == before, 'the dry run persisted something'
    assert must_stage(module, conn, run_id=result['run_id'])['status'] == 'STAGED', 'the same request then stages for real'


ORACLES = {
    'S1': (s1, ('digest = canonical_digest(manifest)\n', "digest = canonical_digest({**manifest, 'unfrozen': True})\n")),
    'S2': (s2, ("return {a: ([f'ka_vedha_gochara:{AYANAMSHA_ID}:{k}' for k in VEDHA_KINDS] if a == 'ka_vedha_gochara' else [grain_key(a)]) for a in plan}",
                "return {a: ([f'ka_vedha_gochara:{AYANAMSHA_ID}:{k}' for k in VEDHA_KINDS[:2]] if a == 'ka_vedha_gochara' else [grain_key(a)]) for a in plan}")),
    'S3': (s3, ("    cand = open_candidate(conn, chart_id=CANONICAL_CHART,", "    conn.execute(\"UPDATE kala_layer_head SET generation = %s WHERE chart_id = %s\", (generation_of(run_id), CANONICAL_CHART))\n    cand = open_candidate(conn, chart_id=CANONICAL_CHART,")),
    'S4': (s4, ("    if closed_plan(edges, assets) != assets:\n", "    if False:\n")),
    'S5': (s5, ("    problem = existing_problem(conn, run_id)\n", "    problem = None\n")),
    'S6': (s6, ("        if same:\n", "        if False:\n")),
    'S7': (s7, ("    if live != expected_head:\n", "    if False:\n")),
    'S8': (s8, ("    if conn.execute('SELECT 1 FROM chart_facts", "    if False and conn.execute('SELECT 1 FROM chart_facts")),
    'S9': (s9, ("    if not commit:\n", "    if False:\n")),
}


def mutated(module, tmp_path, old, new):
    source = Path(module.__file__).read_text()
    assert source.count(old) == 1, f'reversion anchor is not unique: {old!r}'
    path = tmp_path / 'mutated_rebuild_stage.py'
    path.write_text(source.replace(old, new))
    spec = importlib.util.spec_from_file_location('mutated_rebuild_stage', path)
    copy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(copy)
    return copy


@pytest.mark.parametrize('claim', sorted(ORACLES))
def test_oracle_passes_on_the_real_module(staging_db, claim):
    ORACLES[claim][0](real, staging_db)


@pytest.mark.parametrize('claim', sorted(ORACLES))
def test_oracle_fails_on_its_planted_reversion(staging_db, tmp_path, claim):
    oracle, (old, new) = ORACLES[claim]
    with pytest.raises(AssertionError):
        oracle(mutated(real, tmp_path, old, new), staging_db)


# ------------------------------------------------------------------ S10: the command line


@pytest.mark.parametrize('operation,code,status', [('stage', 0, 'STAGED'), ('stage-dryrun', 0, 'ROLLED_BACK')])
def test_s10_the_cli_prints_one_document(staging_db, monkeypatch, capsys, operation, code, status):
    monkeypatch.setenv('DATABASE_URL', 'guarded-local-staging-fixture')
    monkeypatch.setattr(real.psycopg, 'connect', lambda *a, **k: contextlib.nullcontext(staging_db))
    run_id = str(uuid.uuid4())
    argv = [operation, '--run-id', run_id, '--assets', ','.join(PLAN), '--natal-build', NATAL, '--expected-head', 'g-0']
    assert real.main(argv, digest_fn=digests) == code
    out = json.loads(capsys.readouterr().out)
    assert out['status'] == status and out['run_id'] == run_id and out['written'] is (operation == 'stage')


def test_s10_a_refusal_exits_2_with_the_reason_and_no_connection_diagnostics(staging_db, monkeypatch, capsys):
    monkeypatch.setenv('DATABASE_URL', 'guarded-local-staging-fixture')
    monkeypatch.setattr(real.psycopg, 'connect', lambda *a, **k: contextlib.nullcontext(staging_db))
    argv = ['stage', '--run-id', str(uuid.uuid4()), '--assets', 'ka_gochara,ka_yojaka', '--natal-build', NATAL, '--expected-head', 'g-0']
    assert real.main(argv, digest_fn=digests) == 2
    out = json.loads(capsys.readouterr().out)
    assert out['status'] == 'REFUSED' and 'ka_yojaka must precede ka_gochara' in out['reason']


def test_s10_no_database_url_refuses(monkeypatch, capsys):
    monkeypatch.delenv('DATABASE_URL', raising=False)
    assert real.main(['stage', '--run-id', str(uuid.uuid4()), '--assets', 'ka_yojaka', '--natal-build', NATAL, '--expected-head', 'NONE'], digest_fn=digests) == 2
    assert json.loads(capsys.readouterr().out)['status'] == 'REFUSED'


def test_the_vedha_grain_kinds_are_the_writers_own():
    """B.10: the three grain kinds are read from the writer's source, not remembered: ka_vedha_gochara attests `ka_vedha_gochara:<ayanamsha>:<vedha_kind>` per header kind."""
    source = (Path(__file__).resolve().parents[4] / 'services/ka_vedha_gochara/storage.py').read_text()
    assert 'attest_grain(cur,candidate,grain_key=f"ka_vedha_gochara:{pin[\'ayanamsha_id\']}:{h[\'vedha_kind\']}"' in source
    for kind in real.VEDHA_KINDS:
        assert any(kind in p.read_text() for p in (Path(__file__).resolve().parents[4] / 'services/ka_vedha_gochara').glob('*.py')), kind
