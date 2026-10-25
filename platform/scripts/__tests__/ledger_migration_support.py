"""Reads the committed-substep LEDGER's schema from the WRITER lane's migration (SR-RESUME-INTEGRATION: "the WRITER lane's migration 1410 is the source of truth; the executor
side adapts to it, never the reverse"). Nothing here restates a column: the table name, the column names and their types are PARSED out of the migration's CREATE TABLE, and every
fixture that needs the ledger APPLIES the migration itself (`ledger_connection`), never a hand-written table.

`find_migration()` returns (repo-relative path, text) of the migration that creates `public.ka_gochara_build_ledger`, read from the repository's platform/migrations ONLY (migration
1410 is in the tree since #3916). If it is not there the caller FAILS (`MigrationMissing`): a missing migration is never a skip and never a fallback to another checkout or branch.
"""
import contextlib
import importlib.util
import os
import re
import sys
import uuid
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
MIGRATIONS = REPO / 'platform/migrations'
TABLE = 'ka_gochara_build_ledger'
CREATE = re.compile(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:public\.)?' + TABLE + r'\s*\(', re.I)
CLUSTER = os.environ.get('KALA_ADMIN_DSN', 'postgresql://postgres@127.0.0.1:55433/postgres')
DB_PREFIX = 'ky_ledger_'
CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'


class MigrationMissing(AssertionError):
    """No migration in platform/migrations creates public.ka_gochara_build_ledger: the ledger schema cannot be measured and no fixture can build it."""


def _strip_comments(text):
    return re.sub(r'--[^\n]*', '', text)


def find_migration():
    for path in sorted(MIGRATIONS.glob('*.sql')):
        text = path.read_text(encoding='utf-8', errors='ignore')
        if CREATE.search(_strip_comments(text)):
            return str(path.relative_to(REPO)), text
    raise MigrationMissing('no migration in platform/migrations creates public.' + TABLE)


def _guard():
    """The sidecar suite's disposable-database guard (loaded by path: `tests` is not a package of this folder)."""
    path = REPO / 'platform/python-sidecar/tests/l3/gochara/_disposable_db_guard.py'
    spec = importlib.util.spec_from_file_location('ky_ledger_disposable_db_guard', path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@contextlib.contextmanager
def ledger_connection(*, migration_text=None, row_factory=None):
    """A connection to a fresh ky_ledger_* database on the local disposable cluster in which the REAL migration has been APPLIED, after the two tables it refuses to run without
    (public.charts, public.kala_gochara_publication) exist as bare tables and the canonical chart is a row of public.charts (the ledger's foreign key). `migration_text` replaces the
    tree's text (a planted schema drift). The database is dropped on exit. The cluster being unreachable fails under KALA_REQUIRE_DB=1 and skips otherwise."""
    import psycopg
    import pytest
    from psycopg.conninfo import make_conninfo
    guard = _guard()
    try:
        admin = guard.guarded_admin_connect(CLUSTER, autocommit=True, connect_timeout=3)
    except guard.UnsafeAdminDSN:
        raise                                                     # a hostile admin DSN is a configuration error, never a skip
    except Exception:
        if os.environ.get('KALA_REQUIRE_DB') == '1':
            pytest.fail('KALA_REQUIRE_DB=1 and the local cluster is unreachable')
        pytest.skip('local cluster unreachable: deferred to CI')
    text = find_migration()[1] if migration_text is None else migration_text
    name = DB_PREFIX + uuid.uuid4().hex[:10]
    admin.execute(f'CREATE DATABASE "{name}"')
    try:
        conn = psycopg.connect(make_conninfo(CLUSTER, dbname=name), autocommit=True, connect_timeout=3, **({'row_factory': row_factory} if row_factory else {}))
        try:
            conn.execute('CREATE TABLE public.charts (id uuid PRIMARY KEY)')
            conn.execute('CREATE TABLE public.kala_gochara_publication (chart_id uuid, generation text)')
            conn.execute('INSERT INTO public.charts (id) VALUES (%s)', [CHART_ID])
            with conn.transaction():                              # the migration runner owns the transaction (SET LOCAL lock_timeout)
                conn.execute(text)
            yield conn
        finally:
            conn.close()
    finally:
        assert name.startswith(DB_PREFIX), name                   # never drop what we did not create
        admin.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        admin.close()


def _top_level_items(body):
    items, depth, current = [], 0, ''
    for char in body:
        if char == '(':
            depth += 1
        elif char == ')':
            depth -= 1
        if char == ',' and depth == 0:
            items.append(current)
            current = ''
        else:
            current += char
    items.append(current)
    return [' '.join(item.split()) for item in items if item.strip()]


def parse_ledger(text):
    """{'table': name, 'columns': {column: type token}} of the ledger table created by `text`. Constraint clauses are not columns."""
    text = _strip_comments(text)
    match = CREATE.search(text)
    if match is None:
        raise ValueError('the migration does not create ' + TABLE)
    depth, end = 1, match.end()
    while depth and end < len(text):
        depth += {'(': 1, ')': -1}.get(text[end], 0)
        end += 1
    columns = {}
    for item in _top_level_items(text[match.end():end - 1]):
        words = item.split()
        if words[0].upper() in ('CONSTRAINT', 'PRIMARY', 'FOREIGN', 'UNIQUE', 'CHECK', 'EXCLUDE', 'LIKE'):
            continue
        columns[words[0]] = words[1].lower()
    return {'table': TABLE, 'columns': columns}


_FORMAT_TYPE = {'timestamptz': 'timestamp with time zone'}


def held_columns(conn):
    """{column: type} of the ledger table a database actually holds, and `migration_columns(text)` the same as the migration's CREATE TABLE states it (an equality of the two
    says the database's ledger IS the migration applied, not a hand-written table)."""
    return {name: kind for name, kind in conn.execute(
        "SELECT a.attname, format_type(a.atttypid, NULL) FROM pg_attribute a WHERE a.attrelid = %s::regclass AND a.attnum > 0 AND NOT a.attisdropped", ['public.' + TABLE])}


def migration_columns(text):
    return {column: _FORMAT_TYPE.get(kind, kind) for column, kind in parse_ledger(text)['columns'].items()}


def sql_references(sql, alias='l'):
    """Every `<alias>.<column>` an SQL text reads."""
    return set(re.findall(r'\b' + re.escape(alias) + r'\.([a-z_][a-z0-9_]*)', sql))


def rename_column(text, old, new):
    """The migration text with ONE column renamed in its CREATE TABLE column definition (a planted schema drift for the fail-on-revert proof)."""
    match = CREATE.search(text)
    head, tail = text[:match.end()], text[match.end():]
    pattern = re.compile(r'(?m)^(\s*)' + re.escape(old) + r'(\s+(?:UUID|TEXT|INTEGER|TSTZRANGE|JSONB|TIMESTAMPTZ)\b)', re.I)
    if len(pattern.findall(tail)) != 1:
        raise RuntimeError('planted rename anchor not unique: ' + old)        # a bad anchor must never read as a failed oracle
    return head + pattern.sub(lambda m: m.group(1) + new + m.group(2), tail, count=1)


def rename_column_everywhere(text, old, new):
    """The migration text with ONE column renamed in every statement (definition, constraints, post-apply checks), so the drifted migration still APPLIES: a planted schema drift for
    the database tests. (`rename_column` renames the definition only and is for the pure parse checks; applied, it would fail inside the migration's own CHECK constraints.)"""
    drifted, count = re.subn(r'\b' + re.escape(old) + r'\b', new, text)
    if not count:
        raise RuntimeError('planted rename anchor not found: ' + old)
    return drifted
