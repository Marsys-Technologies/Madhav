"""SR-RESUME-INTEGRATION (rulings SR-RESUME-INTEGRATION, SR-RESUME-EXPLICIT-BINDING): "the WRITER lane's migration 1410 is the source of truth; the executor side adapts to it,
never the reverse. The reconciliation commit is checked by a test that reads the ledger schema from 1410 (not a hand-copied constant)."

THIS TEST READS THE MIGRATION. `ledger_migration_support.find_migration()` finds the migration that creates public.ka_gochara_build_ledger (the repository's platform/migrations;
before the writer lane has merged, its branch via read-only `git show`) and PARSES its CREATE TABLE. Nothing below restates a column.

  L1 every ledger column the executor's SQL reads (the resume readback, v5_small_test_shared.resume_readback_sql) is a column of the migration's table, the table is the migration's,
     and the executor reads every column its gate consumes — fail-on-revert: a column renamed in a copy of the migration, and a column renamed in a copy of the executor, each fail
  L2 against the local cluster, on a TEMP table built from the migration's own column names and types, the readback runs and yields a proof the gate admits — fail-on-revert: the same
     table with one column renamed makes the readback fail (the executor's SQL cannot silently read a column that is not there)
  L3 the live admission of the staging binding (dispatch_v5_century_resume_job.resume_gate) reads the ledger's identity columns from the same table — fail-on-revert: one renamed column
  L4 the types the gate interprets (scope jsonb, horizon tstzrange, ordinal/rows_written integer) are the migration's

If the migration cannot be found the tests SKIP with that reason (a skip is "not measured", never a pass); with KALA_REQUIRE_LEDGER_MIGRATION=1 they FAIL instead. After the writer lane
merges the migration is in the tree and nothing here skips.
"""
import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1]
for folder in (SCRIPTS, SCRIPTS / '__tests__'):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

import century_resume_support as S  # noqa: E402
import ledger_migration_support as M  # noqa: E402
import v5_small_test_shared as shared  # noqa: E402

CLUSTER = os.environ.get('KALA_ADMIN_DSN', 'postgresql://postgres@127.0.0.1:55433/postgres')
# what the gate INTERPRETS of a column's type (a statement of how it reads the data, measured against the migration, never a source of names)
INTERPRETED_TYPES = {'scope': 'jsonb', 'horizon': 'tstzrange', 'ordinal': 'integer', 'rows_written': 'integer', 'manifest_id': 'uuid'}


@pytest.fixture(scope='module')
def migration():
    found = M.find_migration()
    if found is None:
        reason = 'no migration creating public.ka_gochara_build_ledger in platform/migrations or on the writer lane branch'
        if os.environ.get('KALA_REQUIRE_LEDGER_MIGRATION') == '1':
            pytest.fail('KALA_REQUIRE_LEDGER_MIGRATION=1 and ' + reason)
        pytest.skip(reason + ': the ledger schema was NOT measured')
    return found


def schema_problems(parsed, module=shared):
    """What is wrong between the migration's ledger table and the executor's reading of it. [] = nothing. Pure."""
    problems = []
    columns = parsed['columns']
    if module.RESUME_LEDGER_TABLE != parsed['table']:
        problems.append(f'table {module.RESUME_LEDGER_TABLE} is not the migration table {parsed["table"]}')
    sql = module.resume_readback_sql()
    if f' FROM {parsed["table"]} l ' not in sql:
        problems.append(f'the readback does not read FROM {parsed["table"]}')
    used = M.sql_references(sql)
    unknown = sorted(used - set(columns))
    if unknown:
        problems.append(f'the readback reads column(s) the migration does not create: {unknown}')
    consumed = set(module.RESUME_LEDGER_COLUMNS) | {module.RESUME_LEDGER_HORIZON}
    unread = sorted(consumed - used)
    if unread:
        problems.append(f'the gate consumes column(s) the readback does not read: {unread}')
    absent = sorted(consumed - set(columns))
    if absent:
        problems.append(f'the gate consumes column(s) the migration does not create: {absent}')
    for column, wanted in INTERPRETED_TYPES.items():
        if column in columns and columns[column] != wanted:
            problems.append(f'column {column} is {columns[column]} in the migration, the gate reads it as {wanted}')
    for column in ('chart_id', 'generation'):                      # the scoping columns of every statement over the ledger
        if column not in columns:
            problems.append(f'the migration table has no {column} column')
    return problems


def test_l1_the_executors_ledger_reading_is_the_migrations(migration):
    label, text = migration
    parsed = M.parse_ledger(text)
    assert schema_problems(parsed) == [], label


def test_l1_a_column_renamed_in_the_migration_is_caught(migration):
    _, text = migration
    for old in ('implementation_digest', 'scope_digest', 'build_run_id', 'horizon'):
        drifted = M.parse_ledger(M.rename_column(text, old, old + '_x'))
        problems = schema_problems(drifted)
        assert problems and old in ' '.join(problems), (old, problems)


def test_l1_a_column_renamed_in_the_executor_is_caught(migration, tmp_path):
    """The ONE planted reversion on the production side: the executor selects `library_digest` where the migration has `implementation_digest`."""
    _, text = migration
    source = Path(shared.__file__).read_text()
    old = "RESUME_LEDGER_COLUMNS = ('substep_key', 'ordinal', 'manifest_id', 'vector_sha256', 'implementation_digest',"
    assert source.count(old) == 1
    path = tmp_path / 'shared_reverted.py'
    path.write_text(source.replace(old, old.replace('implementation_digest', 'library_digest')))
    spec = importlib.util.spec_from_file_location('shared_reverted', path)
    reverted = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reverted)
    problems = schema_problems(M.parse_ledger(text), reverted)
    assert problems and 'library_digest' in ' '.join(problems), problems


def test_l4_the_types_the_gate_interprets_are_the_migrations(migration):
    parsed = M.parse_ledger(migration[1])
    for column, wanted in INTERPRETED_TYPES.items():
        assert parsed['columns'][column] == wanted, column


# ───────────────────────────── the local cluster ─────────────────────────────
def _cluster():
    try:
        import psycopg
        return psycopg.connect(CLUSTER, autocommit=True, connect_timeout=3)
    except Exception:
        if os.environ.get('KALA_REQUIRE_DB') == '1':
            pytest.fail('KALA_REQUIRE_DB=1 and the local cluster is unreachable')
        pytest.skip('local cluster unreachable: deferred to CI')


def temp_ledger(conn, parsed):
    """TEMP tables only (in the cluster's own `postgres` database, shadowing the real names for this one session; nothing outlives the connection). The ledger is built from the
    MIGRATION'S column names and types; the chain tables the readback counts are minimal stand-ins."""
    for table in shared.RESUME_CHAIN_TABLES + shared.RESUME_NEVER_PRESENT:
        conn.execute(f'CREATE TEMP TABLE {table} (chart_id uuid, generation text, partition_kind text)')
    conn.execute('CREATE TEMP TABLE kala_gochara_publication (chart_id uuid, generation text, status text, manifest_id uuid)')
    conn.execute(f'CREATE TEMP TABLE {parsed["table"]} (' + ', '.join(f'{c} {t}' for c, t in parsed['columns'].items()) + ')')


def fill_ledger(conn, parsed, rows):
    columns = [c for c in parsed['columns'] if c in S.ledger_rows()[0] or c in ('chart_id', 'generation')]
    for row in rows:
        values = {'chart_id': shared.CHART_ID, 'generation': '5.0', **{k: v for k, v in row.items() if k != 'horizon'},
                  'horizon': f"[{row['horizon'][0]},{row['horizon'][1]})"}
        values['scope'] = None if row['scope'] is None else json.dumps(row['scope'])
        conn.execute(f'INSERT INTO {parsed["table"]} ({", ".join(columns)}) VALUES ({", ".join(["%s"] * len(columns))})', [values[c] for c in columns])


def fill_chain(conn, rows):
    for table, n in S.census_of(rows).items():
        for _ in range(n):
            conn.execute(f'INSERT INTO {table} (chart_id, generation, partition_kind) VALUES (%s, %s, %s)', [shared.CHART_ID, '5.0', 'event_class'])
    conn.execute("INSERT INTO kala_gochara_publication VALUES (%s, '5.0', 'candidate', %s)", [shared.CHART_ID, S.MANIFEST_ID])
    conn.execute("INSERT INTO ka_gochara_eval_window VALUES (gen_random_uuid(), '4.0', 'event_class')")      # another generation's row is not this chart's census


def test_l2_against_the_migrations_table_the_readback_yields_a_proof_the_gate_admits(migration, tmp_path):
    parsed = M.parse_ledger(migration[1])
    rows = S.ledger_rows()
    conn = _cluster()
    with conn:
        temp_ledger(conn, parsed)
        fill_ledger(conn, parsed, rows)
        fill_chain(conn, rows)
        measured = json.loads(conn.execute(shared.resume_readback_sql()).fetchone()[0])
    assert [r['substep_key'] for r in measured['ledger']] == [r['substep_key'] for r in rows]
    for got, want in zip(measured['ledger'], rows):
        assert shared._resume_horizon(got['horizon']) == shared._resume_horizon(want['horizon']), 'the tstzrange is read back as the same two instants'
        assert {k: v for k, v in got.items() if k != 'horizon'} == {k: v for k, v in want.items() if k != 'horizon'}
    assert measured['census'] == S.census_of(rows) and measured['manifest'] == {'count': 1, 'status': 'candidate', 'manifest_id': S.MANIFEST_ID}
    root = tmp_path / 'ops'
    root.mkdir()
    prior = S.launch(root, 'dispatch-1')
    receipt, acceptance = S.readback(root, measured)
    req = {'operation_id': 'resume-1', 'kind': 'century_resume', 'item_id': 'J-4e', 'args': dict(S.ARGS), 'resumes': prior, 'resume_run_id': S.RUN,
           'program_identity': dict(S.IDENTITY), 'resume_receipt': receipt, 'resume_acceptance': acceptance}
    assert shared.century_request_problem(req, root) is None, 'the measured readback of the migration-shaped ledger is admitted by the gate'
    binding = shared.resume_binding(req, root)
    assert binding['ledger_substeps'] == [r['substep_key'] for r in rows] and binding['resumes_run_id'] == S.RUN


def test_l2_a_column_renamed_in_the_migration_makes_the_readback_fail(migration):
    import psycopg
    drifted = M.parse_ledger(M.rename_column(migration[1], 'implementation_digest', 'impl_digest'))
    conn = _cluster()
    with conn:
        temp_ledger(conn, drifted)
        with pytest.raises(psycopg.errors.UndefinedColumn, match='implementation_digest'):
            conn.execute(shared.resume_readback_sql())


def test_l3_the_live_admission_reads_the_migrations_identity_columns(migration, tmp_path):
    """dispatch_v5_century_resume_job.resume_gate counts ledger rows by writer / implementation / plan digest: against the migration's table it admits the matching program and
    refuses the others; against a table whose column was renamed it cannot run."""
    import psycopg
    import psycopg.rows
    import dispatch_v5_century_resume_job as job
    parsed = M.parse_ledger(migration[1])
    identity = dict(S.IDENTITY)
    req = {'resume_run_id': S.RUN, 'program_identity': identity}
    manifest = {'status': 'candidate'}

    def gate_on(parsed_table, **change):
        conn = psycopg.connect(CLUSTER, autocommit=True, connect_timeout=3, row_factory=psycopg.rows.dict_row)
        with conn:
            temp_ledger(conn, parsed_table)
            fill_ledger(conn, parsed_table, S.ledger_rows(identity=dict(identity, **change)))
            conn.execute('CREATE TEMP TABLE build_runs (id uuid, chart_id uuid, state text, triggered_by text)')
            conn.execute('INSERT INTO build_runs VALUES (%s, %s, %s, %s)', [S.RUN, shared.CHART_ID, 'failed', shared.CENTURY_TRIGGERED_BY])
            return job.resume_gate(req)(conn.cursor(), [], manifest)

    _cluster().close()                      # skip (or fail under KALA_REQUIRE_DB=1) here when the cluster is unreachable
    assert 'RESUME of century run' in gate_on(parsed)[0], 'control failed — the ledger of the request\'s program is admitted'
    for column in ('writer_digest', 'implementation_digest', 'plan_digest'):
        with pytest.raises(shared.Refused, match=column):
            gate_on(parsed, **{column: '1' * 64})
    drifted = M.parse_ledger(M.rename_column(migration[1], 'plan_digest', 'plan_sha'))
    with pytest.raises(psycopg.errors.UndefinedColumn, match='plan_digest'):
        gate_on(drifted)
