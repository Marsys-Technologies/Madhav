"""SR-K9-PUBLISHABLE: publication admits a candidate whose in-scope writers all
attested their grain (the D13 plan of the K9-4a rehearsal: ka_yojaka,
ka_vedha_gochara, ka_sangam, ka_vighnakara, ka_gochara).

Rehearsal X-20261020T090430Z found publication could never admit a plan holding
ka_sangam / ka_vighnakara / ka_gochara (no grain) or ka_vedha_gochara (inert).
Here the four writers run through the real `_drive_substeps` with the runner's
context (chart_id + birth_params), against the REAL candidate/grain/verification
tables (migration 1330) and vedha tables (1383); `services.kala_core.publication`
then verifies the inventory it pinned at candidate-open (publication.py:52-68).

ka_yojaka is not changed by this item: its `ka_yojaka:inputs` grain is attested
here by the same manifest contract (a stand-in, stated, not a claim about its writer).
Writer windowing/doctrine is covered by each writer's own suites; the doctrine
stand-ins are patched exactly as in test_k9_writer_grains.py.
"""
import hashlib
import json
from pathlib import Path
import uuid

import psycopg
from psycopg import sql
from psycopg.rows import dict_row, tuple_row
import pytest

from pipeline.orchestrator import asset_runner
from pipeline.orchestrator.writers import ContextSpec
from services.ka_vedha_gochara.writer import KaVedhaGocharaWriter
from services.kala_core import publication
from services.kala_core.manifest import attest_grain, open_candidate
from tests.l3.kala_db.manifest import test_k9_writer_grains as base
from tests.l3.kala_db.manifest.test_k9_writer_grains import (
    BIRTH, drive, gochara, predicate, sangam, vighnakara, convergence)  # noqa: F401 (fixtures)

MIGRATIONS = Path(__file__).resolve().parents[5] / 'migrations'
CHART = base.CHART
GENERATION = 'candidate:k9-grains'
WRITERS = ('ka_yojaka', 'ka_vedha_gochara', 'ka_sangam', 'ka_vighnakara', 'ka_gochara')
NATAL = str(uuid.uuid4())
AYANAMSHA = 'lahiri_chitrapaksha'
PLAN = {'ka_yojaka': ['ka_yojaka:inputs'],
        'ka_vedha_gochara': [f'ka_vedha_gochara:{AYANAMSHA}:{k}' for k in ('house_vedha', 'latta', 'sarvatobhadra')],
        'ka_sangam': ['ka_sangam:inputs'], 'ka_vighnakara': ['ka_vighnakara:inputs'],
        'ka_gochara': ['ka_gochara:inputs']}


@pytest.fixture
def conn(kala_db_dsn):
    schema = 'k9pub_' + uuid.uuid4().hex
    with psycopg.connect(kala_db_dsn, row_factory=dict_row) as c:
        c.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema)))
        c.execute(sql.SQL('SET search_path TO {}, public').format(sql.Identifier(schema)))
        q = sql.Identifier(schema).as_string(c) + '.'
        c.execute((MIGRATIONS / '1330_kala_layer_manifest_candidates.sql').read_text()
                  .split('-- A separately dispatched verifier')[0].replace('public.', q))
        c.execute('CREATE TABLE build_runs (id uuid PRIMARY KEY, chart_id uuid, scope text, scope_target text, '
                  'action text, plan jsonb, state text, plan_manifest jsonb, plan_manifest_digest text)')
        c.execute('CREATE TABLE asset_throughput (chart_id uuid, asset_id text, last_built_at timestamptz, '
                  'rows_written integer)')
        for ddl in (
            'CREATE TABLE kala_activation_predicates (id serial, chart_id uuid, ayanamsha_id text, signal_id text, '
            'signature_class text, dasha_eligibility_rule_jsonb jsonb, transit_trigger_jsonb jsonb, '
            'strength_affliction_hook_jsonb jsonb, derivation_ledger_jsonb jsonb, generation text, '
            'mechanism_route text, conclusion_state_jsonb jsonb)',
            'CREATE TABLE bodha_msr_signals (signal_id text, dignity_score numeric, configuration_jsonb jsonb, '
            'domains_affected_array text[])',
            'CREATE TABLE build_substep_progress (chart_id uuid, asset_id text, substep_key text, '
            'build_fingerprint text, rows_written integer, completed_at timestamptz, '
            'PRIMARY KEY(chart_id, asset_id, substep_key))',
            'CREATE TABLE kala_convergence (convergence_id serial, chart_id uuid, signal_id text, mode text, '
            'peak_date date, convergence_score numeric, orb_strength numeric, window_start date, window_end date, '
            'horizon_tier text, generation text NOT NULL DEFAULT \'legacy\')',
            'CREATE VIEW kala_convergence_served AS SELECT * FROM kala_convergence',     # migration 1405: readers take the served view
            'CREATE TABLE kala_obstruction (id serial, chart_id uuid, convergence_id integer, signal_id text, '
            'obstruction_type text, severity text, severity_score numeric, override_score numeric, '
            'obstruction_detail jsonb, source_citation text, generation text)',
            'CREATE TABLE chart_facts (fact_id text PRIMARY KEY, chart_id uuid, build_id uuid, ayanamsha_id text, '
            'fact_category text, fact_subject text, fact_key text, fact_value_num numeric)',
            'CREATE TABLE bg_transit_rules (graha text, primary_house integer, vedha_house integer, '
            'classical_citation text, rule_type text)',
            'CREATE TABLE bg_phaladeepika_latta (graha text, count_from_graha integer, direction text, '
            'source_citation text, verse_ref text)',
            'CREATE TABLE classical_text_chunks (chunk_id text, text_id text, chapter integer, verse_start integer, '
            'verse_end integer, content_en text)',
            'CREATE TABLE kala_vedha_gochara (id uuid PRIMARY KEY, chart_id uuid, detail jsonb, window_start date, '
            'UNIQUE(chart_id, window_start))'):
            c.execute(ddl)
        c.execute((MIGRATIONS / '1383_ka_3a_vedha_candidate_intervals.sql').read_text().replace('public.', q))
        from tests.l3.ka_vedha_gochara.test_overlays import ROWS
        for row in ROWS:
            c.execute('INSERT INTO bg_transit_rules VALUES (%s,%s,%s,%s,%s)', row)
        c.execute("INSERT INTO chart_facts VALUES ('moon-ref', %s, %s, %s, 'graha_position', 'MOON', "
                  "'longitude_sidereal', 300)", (CHART, NATAL, AYANAMSHA))
        try:
            yield c
        finally:
            c.rollback()   # the schema and everything in it lived in this one transaction


def open_plan(conn, plan=PLAN):
    build = base.BUILD
    cand = open_candidate(conn, chart_id=CHART, generation=GENERATION, build_id=build,
                          model_digest='fixture', rule_registry_version='fixture',
                          conventions={'publication_grains': plan,
                                       'natal': {'build_id': NATAL, 'ayanamsha_id': AYANAMSHA}})
    manifest = dict(version='nirmana-run-manifest/v1', chart_id=CHART, scope='layer', scope_target='L3',
                    action='rebuild', waves=[list(WRITERS)], assets=[dict(
                        asset_id=w, scope='chart', depends_on=[], natural_key_partition=None,
                        has_cowriters=False, expected_code_digest='a' * 64) for w in WRITERS])
    digest = hashlib.sha256(json.dumps(manifest, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    # The vedha guard (1383) requires the pinned natal build to be a build of this chart.
    conn.execute('INSERT INTO build_runs (id, chart_id) VALUES (%s, %s)', (NATAL, CHART))
    conn.execute('INSERT INTO build_runs VALUES (%s,%s,%s,%s,%s,%s::jsonb,%s,%s::jsonb,%s)',
                 (build, CHART, 'layer', 'L3', 'rebuild', json.dumps(list(WRITERS)), 'completed',
                  json.dumps(manifest), digest))
    return cand


def run_in_scope_writers(conn, cand, writers):
    """Dispatch exactly as the runner does; ka_yojaka's grain by the same manifest contract."""
    from pipeline.orchestrator.writers.ka_gochara import KaGocharaWriter
    from pipeline.orchestrator.writers.ka_sangam import KaSangamWriter
    from pipeline.orchestrator.writers.ka_vighnakara import KaVighnakaraWriter
    classes = {'ka_vedha_gochara': KaVedhaGocharaWriter, 'ka_sangam': KaSangamWriter,
               'ka_vighnakara': KaVighnakaraWriter, 'ka_gochara': KaGocharaWriter}
    with conn.cursor(row_factory=tuple_row) as cur:   # manifest reads positionally; the connection is dict-row
        attest_grain(cur, cand, grain_key='ka_yojaka:inputs', result_state='zero_rows', input_vector='yojaka-fixture')
    for asset in writers:
        drive(conn, classes[asset](), asset)


def accept(conn, cand):
    rows = conn.execute('SELECT grain_key, input_vector FROM kala_layer_candidate_grain WHERE chart_id=%s '
                        'AND generation=%s ORDER BY grain_key', (cand.chart_id, cand.generation)).fetchall()
    digest = hashlib.sha256(json.dumps([(r['grain_key'], r['input_vector']) for r in rows],
                                       separators=(',', ':')).encode()).hexdigest()
    conn.execute("INSERT INTO kala_layer_verification VALUES (%s,%s,'verifier_principal','accepted',%s::jsonb,now())",
                 (cand.chart_id, cand.generation, json.dumps({'input_digest': digest})))


def test_publication_admits_a_layer_whose_in_scope_writers_all_attested(conn, sangam, vighnakara, gochara):
    predicate(conn, GENERATION, 'S-CAND', '2032-02-02')
    cand = open_plan(conn)
    run_in_scope_writers(conn, cand, WRITERS[1:])
    held = {r['grain_key'] for r in conn.execute('SELECT grain_key FROM kala_layer_candidate_grain').fetchall()}
    assert held == {g for grains in PLAN.values() for g in grains}
    accept(conn, cand)
    conn.row_factory = tuple_row   # publication reads positionally; the writers above ran on dict rows
    assert publication.publish(conn, run_id=cand.build_id, generation=GENERATION, expected_head=None)['status'] == 'PUBLISHED'
    assert conn.execute('SELECT generation FROM kala_layer_head WHERE chart_id=%s', (CHART,)).fetchone()[0] == GENERATION


@pytest.mark.parametrize('missing', ['ka_vedha_gochara', 'ka_sangam', 'ka_vighnakara', 'ka_gochara'])
def test_publication_refuses_when_one_in_scope_writer_did_not_attest(conn, sangam, vighnakara, gochara, missing):
    predicate(conn, GENERATION, 'S-CAND', '2032-02-02')
    cand = open_plan(conn)
    run_in_scope_writers(conn, cand, [w for w in WRITERS[1:] if w != missing])
    accept(conn, cand)
    conn.row_factory = tuple_row
    with pytest.raises(ValueError, match='grain'):
        publication.publish(conn, run_id=cand.build_id, generation=GENERATION, expected_head=None)
    assert conn.execute('SELECT count(*) FROM kala_layer_head').fetchone()[0] == 0
