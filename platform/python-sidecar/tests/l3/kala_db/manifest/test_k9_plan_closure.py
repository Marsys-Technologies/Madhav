"""SR-K9-PUBLISHABLE round 4, finding N4: the K9-4a plan must be closed under its dependencies.

The race. `ka_gochara` declares `ka_gochara_resonance`, which declares `ka_yojaka` (migration 1392, the K8-REG registry
truth). The five-writer plan (ka_yojaka, ka_vedha_gochara, ka_gochara, ka_sangam, ka_vighnakara) did not hold the
resonance asset. When `ka_yojaka` completes with a changed output, `staleness.py` stales every out-of-plan dependent
(`targets = downstream - plan_set`), and a planned writer is refused at entry when a DECLARED dependency is not lit
(`asset_runner.deps_unsatisfied`): `ka_gochara` ran only if it started before `ka_yojaka` finished (rehearsal r4, XA/XB).

Claims, one doctrine-grounded oracle each (the sources are the orchestrator's own staleness / readiness rules above and
the registry itself, never a list kept in the code; B.3, B.10):
  P1 a plan that leaves out an asset BETWEEN two planned assets is refused, naming the asset and the closed plan
  P2 the closed plan is admitted, and it holds the intermediate before the planned writer that declares it
  P3 a plan listed against its dependencies (a dependent before its dependency) is refused
  P4 the refusal is reached through the executor-facing entry (`rebuild` and `rebuild-dryrun`), before any delegation
  P5 the intermediate writer attests its candidate grain when bound to a candidate (publication needs one per plan
     writer, publication.py `_candidate`), attests nothing for an ordinary rebuild, and attests nothing when its map is
     incomplete (the publication is then refused rather than carrying a half map)
"""
import importlib
import json
from pathlib import Path
from types import SimpleNamespace
import uuid

import psycopg
from psycopg import sql
from psycopg.rows import dict_row
import pytest

from services.kala_core import publication
from tests.l3.kala_db.manifest.test_publication_admission import Session, registry, run, wired  # noqa: F401
from tests.l3.kala_db.manifest.test_publication_ops import db, prepare  # noqa: F401  (db is a fixture)

ADMISSION = importlib.import_module('services.kala_core.publication_admission')
REPO = Path(__file__).resolve().parents[6]
MIGRATIONS = REPO / 'platform/migrations'
# The D-13 / K9-4a plan as the rehearsal ran it (the set the cockpit gives the executor; its order is derived).
PLAN = ['ka_yojaka', 'ka_vedha_gochara', 'ka_gochara', 'ka_sangam', 'ka_vighnakara']
MIDDLE = 'ka_gochara_resonance'


@pytest.fixture(scope='module')
def edges():
    """The registry as migration 1392 (K8-REG) leaves it, over the committed reconstruction of the rest."""
    base = {row['asset_id']: list(row['depends_on'] or [])
            for row in json.loads((REPO / '00_ARCHITECTURE/control/registry_input_draft.json').read_text())}
    corrections = json.loads((MIGRATIONS / '1392_k8_registry_truth.sql').read_text().split('$k8_rows$')[1])
    base.update({row['asset_id']: list(row['depends_on']) for row in corrections if 'depends_on' in row})
    return base


# ---------------------------------------------------------------- P1, P2, P3: the plan itself


def test_the_registry_really_puts_the_resonance_asset_between_yojaka_and_gochara(edges):
    # Premise of the finding, read from the registry and not asserted by this test.
    assert 'ka_yojaka' in edges[MIDDLE] and MIDDLE in edges['ka_gochara']


def test_a_plan_without_the_asset_between_two_planned_writers_is_refused_and_names_it(edges):
    reason = ADMISSION.assets_refusal(edges, PLAN)
    assert reason and MIDDLE in reason and 'not closed' in reason
    assert 'between ka_yojaka and ka_gochara' in reason
    assert MIDDLE + ',ka_gochara' in reason          # the refusal carries the corrected, ordered plan


def test_the_closed_plan_is_admitted_with_the_asset_ahead_of_the_writer_that_declares_it(edges):
    closed = ADMISSION.closed_plan(edges, PLAN)
    assert set(closed) == set(PLAN) | {MIDDLE} and len(closed) == len(PLAN) + 1
    assert closed.index('ka_yojaka') < closed.index(MIDDLE) < closed.index('ka_gochara')
    assert ADMISSION.assets_refusal(edges, closed) is None


def test_closing_a_plan_gives_the_derived_order_whatever_order_it_was_listed_in(edges):
    # SR-K9-WAVE-ORDER: the order is derived from depends_on (levels, ties by asset id), never kept from the caller's list.
    derived = ['ka_vedha_gochara', 'ka_yojaka', MIDDLE, 'ka_gochara', 'ka_sangam', 'ka_vighnakara']
    listed = ['ka_yojaka', MIDDLE, 'ka_vedha_gochara', 'ka_gochara', 'ka_sangam', 'ka_vighnakara']   # valid, but hand-ordered
    assert ADMISSION.closed_plan(edges, listed) == derived
    assert ADMISSION.closed_plan(edges, list(reversed(listed))) == derived


def test_a_planned_asset_listed_before_its_dependency_is_refused(edges):
    swapped = ['ka_gochara', MIDDLE, 'ka_yojaka', 'ka_vedha_gochara', 'ka_sangam', 'ka_vighnakara']
    reason = ADMISSION.assets_refusal(edges, swapped)
    assert reason and 'ka_yojaka must precede ' + MIDDLE in reason and 'order' in reason
    assert ADMISSION.assets_refusal(edges, ['ka_yojaka', MIDDLE, 'ka_vedha_gochara', 'ka_gochara', 'ka_sangam',
                                            'ka_vighnakara']) is None


def test_an_independent_plan_is_not_flagged_and_a_cycle_terminates():
    flat = {'a': [], 'b': [], 'c': ['a']}
    assert ADMISSION.assets_refusal(flat, ['a', 'b']) is None
    ADMISSION.assets_refusal({'x': ['y'], 'y': ['x']}, ['x', 'y'])      # a registry cycle terminates, it does not recurse


# ---------------------------------------------------------------- P4: the executor-facing entry


GRAPH = {'ga_positions': [], 'ka_yojaka': ['ga_positions'], MIDDLE: ['ka_yojaka'], 'ka_gochara': [MIDDLE]}


@pytest.mark.parametrize('operation', ['rebuild', 'rebuild-dryrun'])
def test_the_entry_refuses_the_open_plan_and_delegates_nothing(wired, monkeypatch, capsys, operation):
    registry(wired, GRAPH)
    c = prepare(wired, writers=('ka_yojaka', 'ka_gochara'))
    monkeypatch.setattr(publication, 'main', lambda argv: pytest.fail('a refused plan must not be delegated'))
    code, out = run([operation, '--run-id', c.build_id, '--assets', 'ka_yojaka,ka_gochara'], capsys)
    assert code == 2 and out['status'] == 'REFUSED' and MIDDLE in out['reason']


def test_the_entry_admits_the_closed_plan_in_order(wired, monkeypatch, capsys):
    registry(wired, GRAPH)
    c = prepare(wired, writers=('ka_yojaka', MIDDLE, 'ka_gochara'))
    calls = []
    def delegate(argv):
        calls.append(argv)
        print(json.dumps({'status': 'BUILD_COMPLETED', 'run_id': c.build_id}))
        return 0
    monkeypatch.setattr(publication, 'main', delegate)
    code, out = run(['rebuild', '--run-id', c.build_id, '--assets', f'ka_yojaka,{MIDDLE},ka_gochara'], capsys)
    assert code == 0 and len(calls) == 1 and out['status'] == 'BUILD_COMPLETED'


# ---------------------------------------------------------------- P5: the intermediate writer's candidate grain


CHART = '00000000-0000-0000-0000-0000000000c1'
BUILD = '00000000-0000-0000-0000-0000000000d1'
GENERATION = 'candidate:' + BUILD


@pytest.fixture
def conn(kala_db_dsn):
    schema = 'k9res_' + uuid.uuid4().hex
    with psycopg.connect(kala_db_dsn, row_factory=dict_row) as c:
        c.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema)))
        c.execute(sql.SQL('SET search_path TO {}, public').format(sql.Identifier(schema)))
        q = sql.Identifier(schema).as_string(c) + '.'
        c.execute((MIGRATIONS / '1330_kala_layer_manifest_candidates.sql').read_text()
                  .split('-- A separately dispatched verifier')[0].replace('public.', q))
        # The map as migrations 459/550/1080 leave it (the columns and the 4-column key migration 1404 widens), then migration 1404 itself,
        # applied verbatim: the writer under test writes (chart, generation) partitions and reads the served view, so a fixture table without
        # them would test a database that no longer exists. The orchestrator's run tables and the registry rows 1404 measures and edits are
        # stand-ins with only the columns it reads.
        c.execute('CREATE TABLE gochara_resonance_map (id BIGSERIAL PRIMARY KEY, chart_id uuid NOT NULL, event_class text NOT NULL, '
                  'target_type text NOT NULL, target_ref text NOT NULL, weight numeric NOT NULL, classical_citation text, '
                  'uncited_extension boolean, source_rule_id text, computed_at timestamptz NOT NULL DEFAULT now(), '
                  'target_resolution_state text NOT NULL DEFAULT \'resolved\', target_qualifier text, '
                  'UNIQUE (chart_id, event_class, target_type, target_ref))')
        c.execute('CREATE TABLE build_runs (id uuid PRIMARY KEY, chart_id uuid)')
        c.execute('CREATE TABLE build_run_assets (run_id uuid, asset_id text, state text, started_at timestamptz, ended_at timestamptz)')
        c.execute('CREATE TABLE asset_registry (asset_id text PRIMARY KEY, count_sql text)')
        c.execute("INSERT INTO asset_registry VALUES ('ka_gochara_resonance', 'SELECT COUNT(*) FROM gochara_resonance_map WHERE chart_id=$1')")
        c.execute('CREATE TABLE asset_output_digest_specs (asset_id text NOT NULL, spec_sha256 text NOT NULL, spec jsonb NOT NULL, '
                  'reviewed_at timestamptz NOT NULL DEFAULT now(), retired_at timestamptz, PRIMARY KEY (asset_id, spec_sha256))')
        c.execute(next(iter(sorted(MIGRATIONS.glob('1404_*.sql')))).read_text())     # no schema-qualified name in the file: the search path decides
        try:
            yield c
        finally:
            c.rollback()


def _open_candidate(conn):
    from services.kala_core.manifest import open_candidate
    return open_candidate(conn, chart_id=CHART, generation=GENERATION, build_id=BUILD, model_digest='fixture',
                          rule_registry_version='fixture',
                          conventions={'publication_grains': {MIDDLE: [MIDDLE + ':inputs']}})


def _writer(monkeypatch, *, complete=True):
    """The resonance writer with its L1 reads replaced by planted rows (the grain is what is under test)."""
    mod = importlib.import_module('services.ka_gochara_resonance.writer')
    classes = list(mod.TARGET_EVENT_CLASSES)
    def rows(conn, chart_id, event_class, report=None):
        if not complete and event_class == classes[0]:
            return []
        return [dict(event_class=event_class, target_type='bhava', target_ref='H7', weight=1.0,
                     classical_citation='planted', uncited_extension=False, source_rule_id=None,
                     target_resolution_state='resolved', target_qualifier=None)]
    monkeypatch.setattr(mod, '_fetch_event_class_rows', rows)
    monkeypatch.setattr(mod, '_fetch_chart_resolution_context', lambda conn, chart_id: {'sign_lords': {}})
    monkeypatch.setattr(mod, '_fetch_m6_context', lambda conn, chart_id: {})
    monkeypatch.setattr(mod, '_build_m6_derived_rows', lambda *a, **k: [])
    monkeypatch.setattr(mod, '_stamp_target_resolution', lambda *a, **k: None)
    monkeypatch.setattr(mod, '_build_wp3c_notes', lambda *a, **k: 'planted')
    return mod.KaGocharaResonanceWriter()


def _ctx(conn, build_id):
    return SimpleNamespace(db_conn=conn, config={'chart_id': CHART}, dry_run=False, build_id=build_id)


def _grains(conn):
    return [r['grain_key'] for r in conn.execute('SELECT grain_key FROM kala_layer_candidate_grain '
                                                 'WHERE chart_id=%s AND generation=%s', (CHART, GENERATION))]


def test_a_candidate_bound_build_attests_the_resonance_grain(conn, monkeypatch):
    _open_candidate(conn)
    result = _writer(monkeypatch).run(_ctx(conn, BUILD))
    assert result.rows_inserted > 0
    assert _grains(conn) == [MIDDLE + ':inputs']
    state = conn.execute('SELECT result_state FROM kala_layer_candidate_grain').fetchone()['result_state']
    assert state == 'rows'


def test_an_ordinary_rebuild_attests_nothing(conn, monkeypatch):
    _open_candidate(conn)
    _writer(monkeypatch).run(_ctx(conn, str(uuid.uuid4())))      # a build bound to no candidate
    assert _grains(conn) == []


def test_an_incomplete_map_attests_nothing_so_publication_is_refused(conn, monkeypatch):
    _open_candidate(conn)
    result = _writer(monkeypatch, complete=False).run(_ctx(conn, BUILD))
    assert result.rows_inserted == 0 and 'incomplete' in result.notes
    assert _grains(conn) == []
