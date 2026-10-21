"""K8-REG remainder, database half: engine-form integrity (SR-K8REG-OPEN; the governance half is platform/scripts/governance/__tests__/test_k8_remainder.py).

Three claims, each against a real PostgreSQL (the guarded disposable cluster) and never a constant:
  1. the remainder migration splices ONE conjunct into ka_sangam's registered contract, keeps every 670 conjunct, changes no other row or column,
     is idempotent and refuses (changing nothing) when the row is not in the registered shape;
  2. the conjunct holds on the REAL ka_sangam jury writer's output, holds on an empty layer (every default legacy dispatch), and reads false on each
     of three planted corruptions the 1350 CHECKs and foreign keys cannot see (the contract: services/ka_sangam/jury/candidate_contract.json);
  3. a replay of the registry-writing migrations shows which ka_* rows carry an engine-form integrity_check_sql, and that exactly two do not.
"""
from pathlib import Path
import os
import re
import sys
from uuid import uuid4

import psycopg
import pytest

# Reuse the real-writer fixture of the K4 end-to-end suite (it builds the 1330/1350 schema and opens a building candidate).
from tests.l3.kala_db.ka_sangam.test_jury_candidate_end_to_end import ctx, writer  # noqa: F401

ROOT = Path(__file__).resolve().parents[6]
MIGRATIONS = ROOT / 'platform/migrations'
sys.path.insert(0, str(ROOT / 'platform/scripts/governance'))
# Planted-reversion proofs point this at a mutated COPY of the migration; the committed tests never set it.
OVERRIDE = os.environ.get('K8R_MIGRATION')


def migration_path() -> Path:
    if OVERRIDE:
        return Path(OVERRIDE)
    found = sorted(MIGRATIONS.glob('*_k8_registry_remainder.sql'))
    assert len(found) == 1, found
    return found[0]


def migration_sql() -> str:
    return migration_path().read_text()


def conjunct() -> str:
    return re.search(r'\$k8_jury\$(.*?)\$k8_jury\$', migration_sql(), re.S)[1]


def sangam_670_contract() -> str:
    text = (MIGRATIONS / '670_nirmana_l3_w3_integrity_contracts.sql').read_text()
    mine = []
    for block in text.split('UPDATE asset_registry SET integrity_check_sql = $ck$')[1:]:
        body, _, after = block.partition('$ck$')
        if re.match(r"\s*WHERE asset_id = 'ka_sangam';", after):
            mine.append(body)
    assert len(mine) == 1
    return mine[0]


REGISTRY_DDL = '''CREATE TABLE asset_registry (
  asset_id text PRIMARY KEY, depends_on text[], has_substeps boolean, count_sql text, integrity_check_sql text, is_active boolean,
  catalog_status text, superseded_by text, data_disposition text, has_writer boolean, target_table text, clear_tables text[],
  natural_key_partition text, target_floor int, volume_explanation text, expected_volume_formula text, expected_volume_inputs jsonb,
  size_sql text, english_description text, layer text, writer_timeout_seconds int, estimated_seconds int, scope text, asset_kind text,
  asset_type text, health_probe jsonb, rebuild_on_probe_fail boolean, sort_order int)'''


def seed_ids() -> list[str]:
    return re.findall(r"^    asset_id: '(ka_[^']+)'", (ROOT / 'platform/scripts/seed/asset_registry_seed.ts').read_text(), re.M)


def apply_file(conn, schema: str, path: Path) -> None:
    # Older migrations (1019, 1022) carry their own BEGIN/COMMIT; the test owns the transaction, so those two lines are dropped (migrate.ts does the same).
    text = re.sub(r'^\s*(?:BEGIN|COMMIT);\s*$', '', path.read_text(), flags=re.M)
    conn.execute(text.replace('public.', schema + '.'))


@pytest.fixture
def conn(kala_db_dsn):
    schema = 'k8r_' + uuid4().hex[:12]
    with psycopg.connect(kala_db_dsn) as c:
        c.execute(f'CREATE SCHEMA {schema}')
        c.execute(f'SET LOCAL search_path TO {schema}, public')
        c.schema = schema
        yield c
        c.rollback()


def snapshot(conn):
    return {r[0]['asset_id']: r[0] for r in conn.execute('SELECT to_jsonb(a) FROM asset_registry a').fetchall()}


@pytest.fixture
def stub(conn):
    conn.execute(REGISTRY_DDL)
    for aid in seed_ids():
        conn.execute("INSERT INTO asset_registry(asset_id,is_active,catalog_status,scope,asset_kind,asset_type,integrity_check_sql) "
                     "VALUES (%s,true,'CURRENT','per_chart','data','data',%s)", (aid, 'SELECT true /* ' + aid + ' */'))
    conn.execute('UPDATE asset_registry SET integrity_check_sql=%s WHERE asset_id=%s', (sangam_670_contract(), 'ka_sangam'))
    return conn


# ═════════════ 1. the migration ═════════════

def test_integrity_engine_form_migration_splices_once_keeps_670_and_touches_only_ka_sangam(stub):
    before = snapshot(stub)
    apply_file(stub, stub.schema, migration_path())
    once = snapshot(stub)
    old = before['ka_sangam']['integrity_check_sql']
    new = once['ka_sangam']['integrity_check_sql']
    body = re.sub(r'\s*AS integrity_passed\s*$', '', old)
    assert new.startswith(body) and new.rstrip().endswith('AS integrity_passed')
    assert new.count('-- K8-REG remainder: candidate jury (K4-2a)') == 1
    assert conjunct() in new
    for aid, row in before.items():
        for column, value in row.items():
            if (aid, column) != ('ka_sangam', 'integrity_check_sql'):
                assert once[aid][column] == value, (aid, column)
    apply_file(stub, stub.schema, migration_path())
    assert snapshot(stub) == once


def test_integrity_engine_form_migration_result_is_engine_form(stub):
    import asset_census as ac
    apply_file(stub, stub.schema, migration_path())
    sql = snapshot(stub)['ka_sangam']['integrity_check_sql']
    assert ac.integrity_sql_problem(sql) is None
    assert not re.search(r'\$\d+', re.sub(r'--[^\n]*', '', sql)), 'a bind parameter: the engine passes none'


@pytest.mark.parametrize('damage', ['missing_row', 'null_contract', 'no_tail'])
def test_integrity_engine_form_migration_refuses_an_unregistered_shape_and_changes_nothing(stub, damage):
    if damage == 'missing_row':
        stub.execute("DELETE FROM asset_registry WHERE asset_id='ka_sangam'")
        expected = 'missing asset identity'
    elif damage == 'null_contract':
        stub.execute("UPDATE asset_registry SET integrity_check_sql=NULL WHERE asset_id='ka_sangam'")
        expected = 'no registered integrity contract'
    else:
        stub.execute("UPDATE asset_registry SET integrity_check_sql='SELECT true' WHERE asset_id='ka_sangam'")
        expected = 'does not end with AS integrity_passed'
    before = snapshot(stub)
    with pytest.raises(psycopg.Error, match=expected):
        with stub.transaction():
            apply_file(stub, stub.schema, migration_path())
    assert snapshot(stub) == before


# ═════════════ 2. the conjunct on the real writer ═════════════

def holds(ctx):
    row = ctx.db_conn.execute('SELECT (true ' + conjunct() + ') AS integrity_passed').fetchone()
    return row[0]


def all_columns(conn, table):
    return [r[0] for r in conn.execute(
        'SELECT column_name FROM information_schema.columns WHERE table_schema=current_schema() AND table_name=%s ORDER BY ordinal_position',
        (table,)).fetchall()]


def corrupt_and_check(ctx, statement, params=()):
    """Plant one corruption inside a savepoint, read the conjunct, roll the corruption back."""
    with ctx.db_conn.transaction(force_rollback=True):
        ctx.db_conn.execute(statement, params)
        return holds(ctx)


def test_integrity_engine_form_conjunct_holds_on_an_empty_layer_as_every_legacy_dispatch_leaves_it(ctx):
    assert ctx.db_conn.execute('SELECT count(*) FROM kala_jury_candidate').fetchone()[0] == 0
    assert holds(ctx) is True


def test_integrity_engine_form_conjunct_holds_on_the_real_jury_writer_output_and_reads_each_planted_corruption_false(ctx):
    assert writer().run(ctx).rows_inserted == 1
    candidates = ctx.db_conn.execute('SELECT count(*) FROM kala_jury_candidate').fetchone()[0]
    segments = ctx.db_conn.execute('SELECT count(*) FROM kala_jury_candidate_segment').fetchone()[0]
    assert candidates == 1 and segments >= 1, 'the writer output must be non-empty or the check proves nothing'
    assert holds(ctx) is True

    cols = all_columns(ctx.db_conn, 'kala_jury_candidate')
    select = ','.join("'jury:planted'" if c == 'assertion_id' else c for c in cols)
    # (K8-a) a second canonical assertion for the same chart x generation x class
    assert corrupt_and_check(ctx, f'INSERT INTO kala_jury_candidate ({",".join(cols)}) SELECT {select} FROM kala_jury_candidate') is False
    # (K8-b) a segment that starts inside an existing one overlaps it (half-open: the existing end is after the new start)
    assert corrupt_and_check(ctx, '''INSERT INTO kala_jury_candidate_segment
        SELECT chart_id,generation,event_class,assertion_id, segment_start + interval '1 millisecond', segment_end + interval '1 hour',
               support_vector, support_roots FROM kala_jury_candidate_segment LIMIT 1''') is False
    # (K8-c) a source-root key for a group that the support vector does not name
    assert corrupt_and_check(ctx, '''UPDATE kala_jury_candidate_segment SET support_roots = support_roots || '{"G-Z": []}'::jsonb''') is False
    # control: touching a segment without breaking any of the three keeps the check true (it is not trivially false)
    assert corrupt_and_check(ctx, '''UPDATE kala_jury_candidate_segment SET support_roots = support_roots''') is True


# ═════════════ 3. which ka_* rows carry an engine-form check ═════════════

# Migrations that write integrity_check_sql of a ka_* row, in applied order, replayed on a stub registry. 1091 and 1230 (a gated repin of ka_gochara and
# its revert to the 670 contract) are not replayed: their guards require the production row state, and 1230's stated end state is the 670 contract.
REPLAY = ['670', '933', '1019', '1022', '1023', '1026', '1150', '1339', '1341', '1353', '1354', '1355', '1356', '1375', '1389']
NO_CHECK = {'ka_gochara_v4_41_candidate', 'ka_gochara_v5'}
PIN_BOUND = {'ka_kalasutra', 'ka_kala_darshana', 'ka_jivana_parva', 'ka_taranga'}


@pytest.fixture
def replayed(conn):
    schema = conn.schema
    conn.execute(REGISTRY_DDL)
    for aid in seed_ids():
        conn.execute("INSERT INTO asset_registry(asset_id,is_active,catalog_status,scope,asset_kind,asset_type) VALUES (%s,true,'CURRENT','per_chart','data','data')", (aid,))
    # Minimal stand-ins for the tables the replayed migrations alter or reference; their columns are only what those statements name.
    conn.execute('''CREATE TABLE build_runs(id uuid PRIMARY KEY, chart_id uuid, created_at timestamptz DEFAULT now());
      CREATE TABLE chart_facts(fact_id text, chart_id uuid, build_id uuid, ayanamsha_id text, fact_category text, fact_subject text, fact_key text);
      CREATE TABLE kala_layer_candidate(chart_id uuid NOT NULL, generation text NOT NULL, build_id uuid, state text, conventions jsonb, PRIMARY KEY(chart_id,generation));
      CREATE TABLE kala_avadhi(chart_id uuid, system_id text, level_n int, period_start date, period_end date, lord_graha text, dossier jsonb, generation text);
      CREATE TABLE kala_activation_predicates(chart_id uuid, signal_id text NOT NULL, ayanamsha_id text, signature_class text);
      CREATE TABLE kala_activation(chart_id uuid); CREATE TABLE kala_darshana(chart_id uuid);
      CREATE TABLE kala_jivana_parva(chart_id uuid); CREATE TABLE kala_taranga(chart_id uuid)''')
    for number in REPLAY:
        apply_file(conn, schema, next(MIGRATIONS.glob(number + '_*.sql')))
    return conn


def test_integrity_engine_form_replay_every_ka_row_but_two_carries_an_engine_form_check(replayed):
    import asset_census as ac
    rows = {r[0]: r[1] for r in replayed.execute("SELECT asset_id, integrity_check_sql FROM asset_registry WHERE asset_id LIKE 'ka\\_%'").fetchall()}
    assert len(rows) == 25
    assert {a for a, sql in rows.items() if sql is None} == NO_CHECK
    for aid, sql in rows.items():
        if sql is None:
            continue
        assert ac.integrity_sql_problem(sql) is None, aid
        assert not re.search(r'\$\d+', re.sub(r'--[^\n]*', '', sql)), f'{aid}: bind parameter'


def test_integrity_engine_form_replay_pin_bound_detectors_are_exactly_the_accepted_k6_set(replayed):
    """1375 binds the three K6 detectors to transaction-local pins on purpose (a probe without pins reads false). Any other asset gaining that
    dependence would read false in the engine's own parameterless probe, so the set is pinned. ka_taranga's 1389 detector is replayed too."""
    bound = {a for (a,) in replayed.execute("SELECT asset_id FROM asset_registry WHERE integrity_check_sql LIKE '%current_setting(%kala.integrity_%'").fetchall()}
    assert bound == PIN_BOUND


def test_integrity_engine_form_replay_then_remainder_extends_only_ka_sangam(replayed):
    before = snapshot(replayed)
    apply_file(replayed, replayed.schema, migration_path())
    after = snapshot(replayed)
    changed = {a for a in before if before[a] != after[a]}
    assert changed == {'ka_sangam'}
    assert '-- K8-REG remainder: candidate jury (K4-2a)' in after['ka_sangam']['integrity_check_sql']


# ═════════════ 4. the second fingerprint declaration, against the real 1342 tables ═════════════

import json  # noqa: E402

A = '00000000-0000-0000-0000-00000000000a'
B = '00000000-0000-0000-0000-00000000000b'
AYAN = 'lahiri_chitrapaksha'


@pytest.fixture
def f1(isolated_kala_db_dsn):
    """The real migration-1342 tables (public, as fingerprint_asset requires) with two charts and two retained generations for chart A."""
    with psycopg.connect(isolated_kala_db_dsn) as c:
        c.execute('CREATE TABLE asset_registry(asset_id text PRIMARY KEY, depends_on text[])')
        c.execute("INSERT INTO asset_registry VALUES ('ka_gochara_resonance', ARRAY['ka_yojaka'])")
        c.execute(re.sub(r'^\s*(?:BEGIN|COMMIT);\s*$', '', (MIGRATIONS / '1342_k2_2_f1_relationships.sql').read_text(), flags=re.M))
        gens = [(A, 'candidate:one-generation'), (A, 'candidate:two-generation'), (B, 'candidate:one-generation')]
        for chart, gen in gens:
            c.execute('INSERT INTO kala_f1_target_object VALUES (%s,%s,%s,%s,%s,%s,%s,%s::jsonb)',
                      (chart, AYAN, gen, 'graha:SUN', 'graha', 285.5, None, '["f1"]'))
            c.execute('INSERT INTO kala_f1_relationship VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                      (chart, AYAN, gen, 'edge-1', 'career', 'graha:SUN', 'lord', 'lagna', 'mech', 'rule', 'prov', 'ref', None, 'resolved'))
        c.commit()
        yield c
        c.rollback()
        c.execute('DROP TABLE kala_f1_relationship, kala_f1_target_object, asset_registry')
        c.commit()


def committed_resonance_fingerprint():
    return json.loads((ROOT / 'platform/scripts/governance/asset_declarations.json').read_text())['assets']['ka_gochara_resonance']['fingerprint']


def measure_f1(conn, chart=A):
    import kala_fingerprint_declarations as mod
    with conn.transaction():
        conn.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
        return mod.fingerprint_asset(conn, 'ka_gochara_resonance', committed_resonance_fingerprint(), chart)


def test_fingerprint_resonance_declared_keys_equal_the_real_1342_primary_keys_and_hash_all_retained_generations(f1):
    first = measure_f1(f1)
    assert first['coverage'] == 'partial' and first['production_certification'] is None
    assert {t: v['rows'] for t, v in first['tables'].items()} == {'kala_f1_target_object': 2, 'kala_f1_relationship': 2}


def test_fingerprint_resonance_foreign_chart_change_is_invisible_and_own_change_or_deletion_moves_the_hash(f1):
    first = measure_f1(f1)
    f1.execute("UPDATE kala_f1_relationship SET role='karaka' WHERE chart_id=%s", (B,)); f1.commit()
    assert measure_f1(f1) == first
    f1.execute("UPDATE kala_f1_relationship SET role='karaka' WHERE chart_id=%s AND generation='candidate:two-generation'", (A,)); f1.commit()
    changed = measure_f1(f1)
    assert changed['sha256'] != first['sha256']
    f1.execute("DELETE FROM kala_f1_relationship WHERE chart_id=%s AND generation='candidate:two-generation'", (A,)); f1.commit()
    assert measure_f1(f1)['sha256'] != changed['sha256']
