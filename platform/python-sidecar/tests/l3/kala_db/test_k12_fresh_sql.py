"""Fresh independent K12 real-writer cancellation probe."""
import pytest
from tests.l3.kala_db.conftest import kala_db_dsn as guarded_database
from psycopg.types.json import Jsonb
from pipeline.orchestrator.writers import SubStep
from pipeline.orchestrator.writers.ka_yojaka import KaYojakaWriter
from tests.l3.kala_db.test_k2_1b_source_writer import db as source_database, ctx, CHART, BUILD


@pytest.fixture(scope='module')
def regression_dsn():
    yield from guarded_database.__wrapped__()


@pytest.fixture
def db(regression_dsn):
    yield from source_database.__wrapped__(regression_dsn)


def test_unknown_targeted_cancellation_survives_writer_as_unresolved(db):
    spec=dict(rule_id='NB-1',kind='defeats',target_yoga_canonical_id='sunapha',
        target_event_class_id='major_gain',rule_version='fixture-v1',source_locator='fixture:source:1')
    db.execute("INSERT INTO brahma_yoga_catalog VALUES ('neecha_bhanga_raja_yoga',%s,%s,%s)",
        (Jsonb({'fixture':True}),Jsonb([{'text_id':'bphs'}]),Jsonb([spec])))
    db.execute('''INSERT INTO ga_yoga_firings(chart_id,ayanamsha_id,yoga_canonical_id,
        constituent_fact_ids,constituent_planets,build_id,bhanga_active,bhanga_rule_fired,grounds_jsonb)
        VALUES (%s,'a','neecha_bhanga_raja_yoga','["CODEX-moon"]','["Moon"]',%s,true,'NB-1',%s)''',
        (CHART,BUILD,Jsonb({'cancellation_evidence':[{'rule_id':'NB-1','fact_ids':['missing-cancellation-fact']}]})))
    KaYojakaWriter().run_substep(ctx(db),SubStep('class:major_gain'))
    state,ledger=db.execute("SELECT conclusion_state_jsonb,derivation_ledger_jsonb FROM kala_activation_predicates WHERE generation='candidate:CODEX-197' AND event_class_id='major_gain'").fetchone()
    assert state['effective_state']=='unresolved', state
    assert state['scored'] is False
    assert ledger['defeats'] or ledger['cancellation_unqualified']
    assert state['null_reason'] == ledger['null_reason'] == 'missing_defeat_facts'
    assert state['effective_reason'] == ledger['effective_reason']
    assert state['effective_reason']['conclusion_ids'] == ['a:sunapha:major_gain:conclusion']
    assert state['effective_reason']['missing_fact_ids'] == ['missing-cancellation-fact']
    assert state['effective_reason']['defeat_ids'] == [ledger['defeats'][0]['defeat_id']]
    assert ledger['defeats'][0]['fact_ids'] == ['missing-cancellation-fact']
