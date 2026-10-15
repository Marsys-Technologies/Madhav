"""Real-index, class-rebuild and published-reader proof for K2-1b."""
import ast
from pathlib import Path

import psycopg
import pytest
from psycopg.types.json import Jsonb

from pipeline.orchestrator.writers import ContextSpec, SubStep
from pipeline.orchestrator.writers.ka_yojaka import KaYojakaWriter

ROOT = Path(__file__).parents[3]
CHART = "00000000-0000-0000-0000-000000000197"
SIGNAL = "00000000-0000-0000-0000-000000000198"
BUILD = "00000000-0000-0000-0000-000000000199"


@pytest.mark.parametrize("rows,expected", [
    ([('graha', 'Sun', 0.2), ('graha', 'Moon', 0.4), ('arudha', 'Sun', 0.8)],
     {'Moon': 1.0, 'Sun': 0.5}),
    ([('graha', 'Sun', 0.2), ('bhava', '1', 0.8)], {'Sun': 1.0}),
    ([('arudha', 'Sun', 0.8)], {}),
])
def test_cgm_centrality_uses_only_grahas(kala_db_dsn, rows, expected):
    """Non-graha rows cannot overwrite Sun or change the normalization floor."""
    with psycopg.connect(kala_db_dsn, row_factory=psycopg.rows.dict_row) as conn:
        conn.execute('''CREATE TEMP TABLE bodha_cgm_nodes (
            chart_id uuid, node_type text, node_subject text, pagerank_score numeric)''')
        with conn.cursor() as cur:
            cur.executemany('INSERT INTO bodha_cgm_nodes VALUES (%s,%s,%s,%s)',
                            [(CHART, kind, subject, score) for kind, subject, score in rows])
        assert KaYojakaWriter()._fetch_cgm_pagerank(conn, CHART) == expected


@pytest.fixture
def db(kala_db_dsn):
    with psycopg.connect(kala_db_dsn) as conn:
        # Execute the actual retained schema/index definitions and the PR
        # migrations in an isolated DB, then roll every fixture back.
        sql = (ROOT.parent / "supabase/migrations/243_l3_ka_yojaka.sql").read_text()
        conn.execute(sql.split("INSERT INTO asset_registry")[0])
        sql = (ROOT.parent / "migrations/240_ga_yoga.sql").read_text()
        conn.execute(sql.split("-- Asset registry entry")[0])
        conn.execute('''CREATE TABLE asset_registry(asset_id text PRIMARY KEY,
                     integrity_check_sql text,has_substeps boolean,depends_on text[])''')
        legacy_check = (ROOT.parent / "migrations/1022_nirmana_l3_ka_yojaka_integrity_check_scope_ab.sql").read_text().split('$ck$')[1]
        conn.execute("INSERT INTO asset_registry VALUES ('ka_yojaka',%s,false,ARRAY['ga_yoga'])", (legacy_check,))
        for name in ("1339_k2_1b_promise_graph_columns.sql",):
            conn.execute((ROOT.parent / "migrations" / name).read_text())
        conn.execute('''CREATE TABLE chart_facts (chart_id uuid, fact_id text, ayanamsha_id text,
            fact_category text, fact_subject text, fact_key text, fact_value_num numeric, unit text,
            build_id uuid, verification_pass_status text, fact_value_text text, fact_value_jsonb jsonb,
            citation_ref text);
            ALTER TABLE ga_yoga_firings ADD COLUMN grounds_jsonb jsonb;
            CREATE TABLE brahma_yoga_catalog (canonical_id text, formation_rule_jsonb jsonb,
                classical_citations jsonb, bhanga_rules_jsonb jsonb);
            CREATE TABLE bodha_msr_signals (chart_id uuid, signal_id uuid, ayanamsha_id text,
                constituent_facts_array text[], configuration_jsonb jsonb, dignity_score numeric, build_id uuid);
            CREATE TABLE bodha_cgm_edges(chart_id uuid, ayanamsha_id text, build_id uuid,
                edge_id uuid, edge_properties_jsonb jsonb);
            CREATE TABLE bodha_pratijna(chart_id uuid, ayanamsha_id text, build_id uuid,
                pratijna_id uuid, event_class_id text, derivation jsonb);
            CREATE TABLE kala_layer_head (chart_id uuid PRIMARY KEY, generation text);
            CREATE TABLE kala_layer_candidate (chart_id uuid, generation text, state text, build_id uuid, conventions jsonb);
            CREATE TABLE kala_layer_candidate_grain(chart_id uuid, generation text, grain_key text,
                result_state text, input_vector text, PRIMARY KEY(chart_id,generation,grain_key));''')
        conn.execute("INSERT INTO kala_layer_candidate VALUES (%s,'candidate:CODEX-197','building',%s,%s)",
                     (CHART, BUILD, Jsonb({'natal': {'build_id': BUILD, 'ayanamsha_id': 'a', 'tier': 'two_pass_verified'}})))
        conn.execute('CREATE TABLE bg_transit_rules(id integer)')
        conn.execute("INSERT INTO chart_facts VALUES (%s,'CODEX-moon','a','graha_position','Moon','longitude_sidereal',0,'deg',%s,'two_pass_verified',NULL,NULL,NULL)", (CHART, BUILD))
        conn.execute("INSERT INTO brahma_yoga_catalog VALUES ('sunapha',%s,%s,'[]')",
                     (Jsonb({"fixture": True}), Jsonb([{"text_id": "bphs"}])))
        conn.execute('''INSERT INTO ga_yoga_firings(chart_id,ayanamsha_id,yoga_canonical_id,constituent_fact_ids,
                     constituent_planets,build_id) VALUES (%s,'a','sunapha','["CODEX-moon"]','["Moon"]',%s)''', (CHART, BUILD))
        conn.execute("INSERT INTO bodha_msr_signals VALUES (%s,%s,'a',ARRAY['CODEX-moon'],'{}',0.8,%s)", (CHART, SIGNAL, BUILD))
        conn.execute('''INSERT INTO kala_activation_predicates(chart_id,signal_id,ayanamsha_id,signature_class,
                     dasha_eligibility_rule_jsonb) VALUES (%s,%s,'a','YOGA','{"legacy":true}')''', (CHART, SIGNAL))
        yield conn
        conn.rollback()


def ctx(db, generation="candidate:CODEX-197"):
    return ContextSpec("ka_yojaka", BUILD, db, {"chart_id": CHART, "candidate_generation": generation})


def test_plan_substeps_is_pure_and_canonical_class_grained():
    subject = ContextSpec("ka_yojaka", "CODEX-197", None, {"chart_id": CHART})
    before = dict(subject.config)
    plan = KaYojakaWriter().plan_substeps(subject)
    assert len(plan) == 28
    assert all(step.key.startswith("class:") for step in plan)
    assert subject.config == before


def test_real_indexes_admit_legacy_and_candidate_without_a_net_row_change_on_rebuild(db):
    writer = KaYojakaWriter()
    legacy = db.execute("SELECT * FROM kala_activation_predicates WHERE generation='legacy'").fetchall()
    writer.run_substep(ctx(db), SubStep("class:major_gain"))
    candidate = db.execute("SELECT signal_id,mechanism_id,conclusion_state_jsonb FROM kala_activation_predicates WHERE generation='candidate:CODEX-197'").fetchall()
    assert candidate[0][0] is None  # L1 existence cannot depend on an L2 selection
    assert candidate[0][2]["effective_state"] == "in_force"
    writer.run_substep(ctx(db), SubStep("class:major_gain"))
    assert db.execute("SELECT signal_id,mechanism_id,conclusion_state_jsonb FROM kala_activation_predicates WHERE generation='candidate:CODEX-197'").fetchall() == candidate
    assert db.execute("SELECT * FROM kala_activation_predicates WHERE generation='legacy'").fetchall() == legacy


def test_changed_upstream_refuses_rebuild_and_preserves_every_class(db):
    writer = KaYojakaWriter()
    writer.run_substep(ctx(db), SubStep("class:achievement_recognition"))
    writer.run_substep(ctx(db), SubStep("class:major_gain"))
    db.execute("DELETE FROM ga_yoga_firings")
    db.execute("DELETE FROM bodha_msr_signals")
    with pytest.raises(ValueError, match='input'):
        writer.run_substep(ctx(db), SubStep("class:major_gain"))
    assert sorted(db.execute("SELECT event_class_id FROM kala_activation_predicates WHERE generation='candidate:CODEX-197'").fetchall()) == [("achievement_recognition",), ("major_gain",)]


@pytest.mark.parametrize("generation", ["legacy", "published:old", "candidate:published", "candidate:retained"])
def test_writer_refuses_legacy_current_and_retained_published_generations(db, generation):
    db.execute("INSERT INTO kala_layer_head VALUES (%s,'candidate:published')", (CHART,))
    db.execute("INSERT INTO kala_layer_candidate VALUES (%s,'candidate:retained','published','00000000-0000-0000-0000-000000000200','{}')", (CHART,))
    with pytest.raises(ValueError):
        KaYojakaWriter().run_substep(ctx(db, generation), SubStep("class:major_gain"))


def _reader_sql(name):
    tree = ast.parse((ROOT / "pipeline/orchestrator/writers" / name).read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "execute" and node.args:
            try:
                sql = ast.literal_eval(node.args[0])
            except (ValueError, TypeError):
                continue
            if "FROM kala_activation_predicates" in sql and "SELECT" in sql:
                return sql
    raise AssertionError(f"missing actual consumer query: {name}")


@pytest.mark.parametrize("reader", ["ka_sangam.py", "ka_kalasutra.py", "ka_vighnakara.py", "ph_nimitta.py"])
def test_actual_reader_queries_ignore_candidates_across_repeated_builds(db, reader):
    query = _reader_sql(reader)
    params = (CHART, 200) if reader == "ka_sangam.py" else (CHART, [SIGNAL]) if reader == "ph_nimitta.py" else (CHART,)
    before = db.execute(query, params).fetchall()
    assert before  # planted legacy predicate is observable
    db.execute('''INSERT INTO kala_activation_predicates(chart_id,signal_id,ayanamsha_id,signature_class,
                 generation,dasha_eligibility_rule_jsonb) VALUES (%s,%s,'a','DOSHA',
                 'candidate:other','{"multi_system_confirmation_count":99}')''', (CHART, SIGNAL))
    writer = KaYojakaWriter()
    writer.run_substep(ctx(db), SubStep("class:major_gain"))
    writer.run_substep(ctx(db), SubStep("class:major_gain"))
    assert db.execute(query, params).fetchall() == before


def test_chapter_reader_cannot_attach_an_unpublished_candidate_when_legacy_is_empty(db):
    db.execute('''CREATE TABLE kala_convergence(convergence_id bigint,chart_id uuid,signal_id uuid,
                 peak_date date,convergence_score numeric);
                 CREATE TABLE kala_darshana(convergence_id bigint,effective_score numeric);''')
    db.execute("INSERT INTO kala_convergence VALUES (1,%s,%s,'2000-01-01',0.8)", (CHART, SIGNAL))
    db.execute("DELETE FROM kala_activation_predicates")
    db.execute('''INSERT INTO kala_activation_predicates(chart_id,signal_id,ayanamsha_id,signature_class,
                 generation) VALUES (%s,%s,'a','DOSHA','candidate:other')''', (CHART, SIGNAL))
    assert db.execute(_reader_sql("ka_jivana_parva.py"), (CHART,)).fetchone()[2] is None


@pytest.mark.parametrize("reader", ["ka_sangam.py", "ka_kalasutra.py", "ka_vighnakara.py", "ph_nimitta.py"])
def test_published_effective_defeat_is_not_operationally_active(db, reader):
    db.execute("INSERT INTO kala_layer_head VALUES (%s,'published:CODEX')", (CHART,))
    db.execute('''INSERT INTO kala_activation_predicates(chart_id,signal_id,ayanamsha_id,signature_class,
                 generation,mechanism_route,conclusion_state_jsonb) VALUES (%s,%s,'a','DOSHA',
                 'published:CODEX','admitted','{"effective_state":"defeated","scored":false}')''', (CHART, SIGNAL))
    params = (CHART, 200) if reader == "ka_sangam.py" else (CHART, [SIGNAL]) if reader == "ph_nimitta.py" else (CHART,)
    assert db.execute(_reader_sql(reader), params).fetchall() == []


def test_full_writer_runs_on_l1_without_any_l2_and_keeps_missing_targets_null(db):
    db.execute("DELETE FROM bodha_msr_signals")
    db.execute("UPDATE chart_facts SET fact_value_num=NULL")
    result = KaYojakaWriter().run(ctx(db))
    assert result.rows_inserted == 2
    triggers = db.execute("SELECT transit_trigger_jsonb FROM kala_activation_predicates WHERE generation='candidate:CODEX-197'").fetchall()
    assert all(t[0]["target_longitude_deg"] is None and t[0]["target_identity"] is None for t in triggers)


def test_registered_integrity_contract_accepts_l1_graph_and_rejects_scored_testimony(db):
    db.execute("DELETE FROM kala_activation_predicates WHERE generation='legacy'")
    KaYojakaWriter().run(ctx(db))
    check, heavy = db.execute("SELECT integrity_check_sql,has_substeps FROM asset_registry WHERE asset_id='ka_yojaka'").fetchone()
    assert heavy is True
    assert db.execute(check).fetchone()[0] is True
    db.execute("UPDATE kala_activation_predicates SET mechanism_route='testimony'")
    assert db.execute(check).fetchone()[0] is False


@pytest.mark.parametrize("field", ["qualification", "scored", "fact_state"])
def test_registered_integrity_contract_fails_closed_on_missing_scoring_metadata(db, field):
    db.execute("DELETE FROM kala_activation_predicates WHERE generation='legacy'")
    KaYojakaWriter().run(ctx(db))
    check = db.execute("SELECT integrity_check_sql FROM asset_registry WHERE asset_id='ka_yojaka'").fetchone()[0]
    db.execute("UPDATE kala_activation_predicates SET conclusion_state_jsonb=conclusion_state_jsonb-%s", (field,))
    assert db.execute(check).fetchone()[0] is False


def ledger_rows(db):
    return [r[0] for r in db.execute("SELECT derivation_ledger_jsonb FROM kala_activation_predicates WHERE generation='candidate:CODEX-197' ORDER BY mechanism_id").fetchall()]


@pytest.mark.parametrize('table', ['chart_facts', 'ga_yoga_firings', 'bodha_msr_signals'])
def test_upstream_rebuild_cannot_change_pinned_candidate_inputs(db, table):
    writer = KaYojakaWriter()
    writer.run_substep(ctx(db), SubStep('class:major_gain'))
    before = ledger_rows(db)
    vector = db.execute("SELECT input_vector FROM kala_layer_candidate_grain WHERE grain_key='ka_yojaka:inputs'").fetchone()
    assert vector and len(vector[0]) == 64
    # A rebuild replaces the pinned rows with a later build. Never consume it
    # under the original candidate identity, or erase the original result.
    db.execute(f"UPDATE {table} SET build_id='00000000-0000-0000-0000-000000000201'")
    with pytest.raises(ValueError, match='input'):
        writer.run_substep(ctx(db), SubStep('class:major_gain'))
    assert ledger_rows(db) == before


@pytest.mark.parametrize('column,value', [('build_id', '00000000-0000-0000-0000-000000000201'), ('ayanamsha_id', 'other')])
def test_writer_excludes_foreign_build_and_convention_from_all_three_sources(db, column, value):
    db.execute(f'UPDATE chart_facts SET {column}=%s', (value,))
    db.execute(f'UPDATE ga_yoga_firings SET {column}=%s', (value,))
    db.execute(f'UPDATE bodha_msr_signals SET {column}=%s', (value,))
    assert KaYojakaWriter().run(ctx(db)).rows_inserted == 0


def test_yoga_tier_is_honestly_null_without_losing_constituent_tiers(db):
    KaYojakaWriter().run_substep(ctx(db), SubStep('class:major_gain'))
    row = ledger_rows(db)[0]
    assert row['yoga_tier'] is None
    assert row['null_reason'] == 'ga_yoga_firings_carries_no_verification_tier'
    assert row['constituent_fact_tiers'] == {'CODEX-moon': 'two_pass_verified'}
    assert 'yoga_tier_unavailable' in row['judgment_flags']


def test_cgm_pratijna_attachment_states_reach_writer_output(db):
    db.execute("INSERT INTO bodha_cgm_edges VALUES (%s,'a',%s,%s,%s)",
               (CHART, BUILD, SIGNAL, Jsonb({'copied_value': 0, 'fact_ids': ['CODEX-moon']})))
    db.execute("INSERT INTO bodha_pratijna VALUES (%s,'a',%s,%s,'major_gain',%s)",
               (CHART, BUILD, SIGNAL, Jsonb({'factor_ledger': [{'value': 0}]})))
    KaYojakaWriter().run(ctx(db))
    rows = ledger_rows(db)
    row = next(r for r in rows if r['event_class_id'] == 'major_gain')
    assert row['sources_consulted'] == ['msr', 'cgm', 'pratijna']
    states = {a['source']: a for r in rows for a in r['l2_attachments']}
    assert states['MSR']['state'] == 'present'
    for source in ('CGM', 'Pratijna'):
        assert states[source]['state'] == 'missing_fact'
        assert states[source]['null_reason'] == 'no_fact_root_identity_in_l2_source'
        assert states[source]['fact_ids'] == []
    assert row['source_states'] == {'msr': 'present', 'cgm': 'missing_fact', 'pratijna': 'missing_fact'}


def test_rootless_attachments_are_visible_without_any_l1_formation(db):
    db.execute('DELETE FROM ga_yoga_firings')
    db.execute('DELETE FROM bodha_msr_signals')
    db.execute("INSERT INTO bodha_cgm_edges VALUES (%s,'a',%s,%s,'{}')", (CHART, BUILD, SIGNAL))
    db.execute("INSERT INTO bodha_pratijna VALUES (%s,'a',%s,%s,'major_gain','{}')", (CHART, BUILD, SIGNAL))
    KaYojakaWriter().run(ctx(db))
    rows = ledger_rows(db)
    assert rows and all(r['route'] == 'testimony' and r['scored'] is False for r in rows)
    assert {a['source'] for r in rows for a in r['l2_attachments']} == {'CGM', 'Pratijna'}


def test_missing_natal_pin_refuses_before_any_candidate_replacement(db):
    db.execute("UPDATE kala_layer_candidate SET conventions='{}'")
    with pytest.raises(ValueError, match='natal'):
        KaYojakaWriter().run(ctx(db))
    assert ledger_rows(db) == []


def test_future_earned_yoga_tier_column_is_read_without_a_reader_change(db):
    # Disposable producer-contract fixture, never a migration of an L1 asset.
    db.execute("ALTER TABLE ga_yoga_firings ADD COLUMN verification_pass_status text")
    db.execute("UPDATE ga_yoga_firings SET verification_pass_status='two_pass_verified'")
    KaYojakaWriter().run_substep(ctx(db), SubStep('class:major_gain'))
    assert ledger_rows(db)[0]['yoga_tier'] == 'two_pass_verified'


def test_served_locator_resolution_reaches_the_stored_structural_graph(db):
    db.execute('CREATE TABLE classical_text_chunks(text_id text, verse_ref text)')
    db.execute("INSERT INTO classical_text_chunks VALUES ('bphs','PG286:C1')")
    db.execute("UPDATE chart_facts SET fact_category='aspect_parashari_given',fact_subject='JUP',fact_key='house_7',fact_value_num=1,citation_ref='bphs:PG286:C1'")
    KaYojakaWriter().run_substep(ctx(db), SubStep('class:unqualified'))
    row = next(r for r in ledger_rows(db) if r['source'] == 'chart_facts:CODEX-moon')
    assert row['graph_edges'][0]['provenance'] == 'verse_cited'
    assert row['graph_edges'][0]['source_locator'] == 'bphs:PG286:C1'
