"""J-1a: complete logical backup paired with measured scratch restore evidence.

Default/--dry-run emits a plan and never opens a DB, invokes a program or
creates a file. The executor alone supplies DATABASE_URL to --execute.
Source capture is read-only. pg_dump uses the exported repeatable-read
snapshot used for EVERY table's count/content measurement. Sequence state
is measured before and after dumping; changing state refuses capture.

(I) INTERPRETATION P01-I1: use the repository backup mechanism's custom-format
pg_dump/pg_restore (--no-owner/--no-privileges), broadened to the whole DB
rather than only irreplaceable table sets. Full data/sequence equality is
required. Roles, grants and external FDW data are not a restore claim.
Foreign tables and large objects are refused, rather than silently omitted.
(I) INTERPRETATION P01-I2: restore ONLY to a new ky_restore_<label> database
on the fleet's existing loopback cluster (local_db.sh:62,338: port 55433,
postgres test role). Never start/stop Docker, reuse/reset an existing DB,
or restore to source. The created database is dropped before evidence can
say verified. This is scratch restore evidence, never production restore.

Archive/evidence lives at KY_ROOT/run/ops/backups/<label>/; labels are unique
and capture refuses to overwrite. Source URL and client errors never print.
Executor request/review/lease/backup gates remain separate from these receipts.

--scope small_test (default: full, the behaviour above, unchanged) is the J-2a
SCOPED backup (surrogate ruling SR-J2A-BACKUP-SCOPE; spec
00_ARCHITECTURE/briefs/kalayantra/fleet/J2A_SCOPED_BACKUP_v1_0.md). It archives
the DEFINITIONS and DATA of exactly the tables the small test can write
(backup_v5_small_test_scope.json, pinned by sha256) and their foreign-key
parents, each named by its own pg_dump -t, in a directory archive taken in
parallel under the exported snapshot. No other relation is locked or dumped, so
a table the backup login cannot read (SR-J2A-BACKUP-POSITIVE) cannot break it.
Row content is measured by bounded SQL aggregates (count and an
order-independent sum of per-row SHA-256), never by streaming sorted row JSON.
Its receipts carry the scope digest and the scoped-content digest, which is what keeps them
valid (SR-BACKUP-VALIDITY-A8: valid while a fresh measurement of the same relations equals it,
no clock); they never claim a "complete database". Restore proof: the scoped definitions cannot recreate the
functions, types and extensions the tables depend on, so the scratch target is
first built from the governed L1 bundle schema (never from production's
catalog) PLUS every migration the archive's own _migrations_applied ledger
records as applied after that bundle and that touches a scope table (derived,
never pinned: SR-J2A-RESTORE-BASE), the scope tables are replaced by the
archive's own definitions and data, and the same counts/digests are compared.
(I) INTERPRETATION J2A-S1: the second same-snapshot table pass is dropped in
scoped mode (REPEATABLE READ cannot make it differ); sequences, which are not
transactional, are still measured before and after the dump.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import subprocess
import sys

import v5_small_test_shared as shared_policy   # the scoped-content digest and measurement method the dispatch check also uses


class BackupRefused(RuntimeError):
    """A safe named refusal; never contains connection settings."""


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    p.add_argument('--operation', choices=['snapshot', 'restore-verify'], required=True)
    p.add_argument('--label', required=True)
    p.add_argument('--scope', choices=['full', 'small_test'], default='full')
    mode = p.add_mutually_exclusive_group()
    mode.add_argument('--dry-run', action='store_true')
    mode.add_argument('--execute', action='store_true')
    args = p.parse_args(argv)
    if not re.fullmatch(r'[a-z][a-z0-9_]{2,39}', args.label) or args.label == 'prod':
        p.error('--label must be a unique lowercase identifier, 3–40 characters, other than prod')
    return args


def scratch_settings(label: str) -> dict:
    # The fleet test cluster's fixed, non-production settings. No source PG*
    # setting, service file or passfile may redirect this connection.
    return {'host': '127.0.0.1', 'hostaddr': '127.0.0.1', 'port': '55433', 'user': 'postgres',
            'password': 'postgres', 'dbname': f'ky_restore_{label}',
            'connect_timeout': '10'}


def client_env(settings: dict) -> dict:
    env = {k: v for k, v in os.environ.items() if not k.startswith('PG') and k not in
           ('DATABASE_URL', 'KY_OWNER_DATABASE_URL', 'KY_BUILDER_DATABASE_URL')}
    mapping = {'host': 'PGHOST', 'hostaddr': 'PGHOSTADDR', 'port': 'PGPORT',
               'user': 'PGUSER', 'password': 'PGPASSWORD', 'dbname': 'PGDATABASE',
               'sslmode': 'PGSSLMODE', 'sslrootcert': 'PGSSLROOTCERT', 'sslcert': 'PGSSLCERT',
               'sslkey': 'PGSSLKEY', 'connect_timeout': 'PGCONNECT_TIMEOUT'}
    # Fail closed for service/unsupported conninfo, rather than silently use
    # a different endpoint or authentication method for the client dump.
    if set(settings) - set(mapping):
        raise BackupRefused('unsupported source connection options')
    env.update({mapping[k]: str(v) for k, v in settings.items()})
    env['PGPASSFILE'] = os.devnull
    return env


def run_client(argv: list[str], settings: dict, timeout: int = 14400) -> None:
    result = subprocess.run(argv, env=client_env(settings), stdout=subprocess.DEVNULL,
                            stderr=subprocess.PIPE, timeout=timeout, check=False)
    if result.returncode:
        raise BackupRefused(f'{argv[0]} failed (exit {result.returncode}; error text withheld)')


def client_output(argv: list[str], settings: dict, timeout: int = 300) -> str:
    result = subprocess.run(argv, env=client_env(settings), stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, timeout=timeout, check=False)
    if result.returncode:
        raise BackupRefused(f'{argv[0]} failed (exit {result.returncode}; error text withheld)')
    return result.stdout.decode('utf-8', 'replace')


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def write_receipt(path: Path, receipt: dict) -> None:
    with path.open('x', encoding='utf-8') as stream:
        os.chmod(path, 0o600)
        json.dump(receipt, stream, indent=2, sort_keys=True)
        stream.write('\n')


def measurements(conn) -> dict:
    """Independent row content/order/coverage and sequence measurements.

    ONLY prevents inheritance/partition double counting. Server-side cursors
    stream sorted canonical row JSON, so a changed row with the same count
    changes SHA-256. C collation + UTC + fixed float settings are used in
    both connections. Missing relations/privileges cause failure.
    """
    from psycopg import sql
    conn.execute("SET LOCAL timezone = 'UTC'")
    conn.execute("SET LOCAL extra_float_digits = 3")
    relations = conn.execute("""SELECT n.nspname, c.relname, c.relkind
        FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname NOT IN ('pg_catalog', 'information_schema') AND n.nspname NOT LIKE 'pg_toast%'
          AND n.nspname NOT LIKE 'pg_temp_%' AND c.relkind IN ('r', 'p', 'm', 'S', 'f')
        ORDER BY n.nspname, c.relname""").fetchall()
    if any(kind == 'f' for _, _, kind in relations):
        raise BackupRefused('foreign-table data is not covered by a logical archive')
    if conn.execute('SELECT EXISTS (SELECT 1 FROM pg_catalog.pg_largeobject_metadata)').fetchone()[0]:
        raise BackupRefused('large objects require separately reviewed capture/restore measurements')
    tables, sequences = {}, {}
    for schema, name, kind in relations:
        key = f'{schema}.{name}'
        relation = sql.Identifier(schema, name)
        if kind == 'S':
            value, called = conn.execute(sql.SQL('SELECT last_value, is_called FROM {}').format(relation)).fetchone()
            sequences[key] = {'last_value': int(value), 'is_called': bool(called)}
        else:
            digest, count = hashlib.sha256(), 0
            query = sql.SQL('SELECT row_to_json(t)::text FROM ONLY {} t ORDER BY row_to_json(t)::text COLLATE "C"').format(relation)
            with conn.cursor(name='ky_backup_measure') as cur:
                cur.execute(query)
                for (row,) in cur:
                    encoded = row.encode('utf-8')
                    digest.update(len(encoded).to_bytes(8, 'big'))
                    digest.update(encoded)
                    count += 1
            tables[key] = {'rows': count, 'sha256': digest.hexdigest()}
    if not tables:
        raise BackupRefused('no measured tables; refusing empty coverage')
    return {'tables': tables, 'sequences': sequences}


def compare_restore(expected: dict, actual: dict) -> None:
    if expected != actual:
        raise BackupRefused('restore row counts/content hashes/sequence state or relation coverage differ')


# ---------------------------------------------------------------------------
# J-2a SCOPED backup (--scope small_test). Everything below is reached only
# through --scope small_test or a ky.smalltest_backup/2 receipt; the full
# mode above is untouched.
# ---------------------------------------------------------------------------
SCOPE_FILE = Path(__file__).with_name('backup_v5_small_test_scope.json')
SCOPED_BACKUP_SCHEMA = 'ky.smalltest_backup/2'
SCOPED_RESTORE_SCHEMA = 'ky.smalltest_restore/2'
SCOPED_MEASUREMENT_METHOD = shared_policy.SCOPED_MEASUREMENT_METHOD   # pinned in the shared policy: one definition for capture and check
SCOPED_DUMP_JOBS = 4
# Condition (5): the whole step must finish in 30 minutes at the observed
# 1.2 MB/s proxy rate. 500 MB of on-disk table data streams as at most ~1 GB of
# COPY text (~14 minutes, before any --jobs gain); a larger scoped set is
# refused up front rather than found out as a timeout. The client timeouts cap
# the rest: 15 + 10 minutes, plus a few minutes of SQL measurement.
SCOPED_DATA_BUDGET_BYTES = 500_000_000
SCOPED_DUMP_TIMEOUT_S = 900
SCOPED_RESTORE_TIMEOUT_S = 600
SCOPED_STATEMENT_TIMEOUT_MS = 300_000
# SR-J2A-BACKUP-POSITIVE restore base: the governed L1 bundle's schema.sql (schema only, in the executor's private
# run directory; read here, never copied). Its sha256 is the bundle manifest's. The five extensions are the ones the
# bundle's own strict restore installed.
# SR-J2A-RESTORE-BASE: the migrations applied AFTER the bundle are never pinned. They are derived at proof time from the
# _migrations_applied ledger the archive itself carries (that table is in the scope): every entry applied after
# SCOPED_RESTORE_BASE_CUT (the bundle manifest's captured_at) whose repository file mentions a scope table, in ledger
# order, each file hash-checked against the ledger's own sha256. (I) INTERPRETATION J2A-B3: "touches a scope table" is a
# whole-word textual mention of a scope table name in the migration file; an over-inclusion or a dynamic-SQL miss fails
# the restore loudly before any receipt. Alternative: carry every post-bundle migration.
SCOPED_RESTORE_BASE_PATH = 'run/canonical_l1/20261016T135745Z/schema.sql'
SCOPED_RESTORE_BASE_SHA256 = '7e15492f09d54b3f4c49e05afe4237b70254d59740e6a1222a0aa4277899700e'
# The cut is a property of the pinned bundle file, like its sha256: schema.sql was written 2026-10-16 22:40:23 IST =
# 17:10:23Z (the manifest's captured_at, 13:57:45Z, dates the chart data, not the schema). Production's ledger has no
# migration between 14:49:45Z (1389, in the bundle) and 22:26:25Z (1393, not in it), so any cut in that gap is equivalent.
SCOPED_RESTORE_BASE_CUT = '2026-10-16T17:10:23+00:00'
SCOPED_RESTORE_BASE_EXTENSIONS = ('vector', 'pgcrypto', 'pg_trgm', 'uuid-ossp', 'btree_gist')
SCOPED_LEDGER_TABLE = 'public._migrations_applied'
# (I) INTERPRETATION J2A-B4: captures taken by an EARLIER version of this script carry no migration ledger digest; the
# ruling re-proves that very backup. Each script digest listed here is such a capture script; its receipts are restored
# through the ledger-derived fallback with the ledger read from the archive itself. Any other script digest, and any
# capture by the current script lacking its ledger digest, is refused as before.
SCOPED_LEGACY_CAPTURE_SCRIPTS = {
    '3f967bf9cd99abe725db9983b50f99d4263e96336c44ee4b2ce3a707022aeb29': 'seedless capture w4r1_20261017t090403z',
}
MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / 'migrations'


def scope_digest(name: str, tables: list[str]) -> str:
    body = {'schema': 'ky.smalltest_backup_scope/1', 'name': name, 'tables': sorted(tables)}
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def load_scope(path: Path | None = None) -> dict:
    """The reviewed scope file -> {name, tables (data), written, guarded_children, sha256}."""
    try:
        raw = json.loads((path or SCOPE_FILE).read_text())
        written = [e['table'] for e in raw['written']]
        context = [e['table'] for e in raw['context']]
        guarded = [e['table'] for e in raw['guarded_children']]
        excludes = [e['table'] for e in raw.get('dump_excludes', [])]
    except (OSError, ValueError, KeyError, TypeError):
        raise BackupRefused('reviewed scope file missing or malformed') from None
    tables = sorted(set(written) | set(context))
    if (raw.get('schema') != 'ky.smalltest_backup_scope/1' or raw.get('name') != 'small_test' or not written
            or len(set(written)) != len(written) or set(written) & set(context)
            or any(re.fullmatch(r'[a-z_][a-z0-9_]*\.[a-z_][a-z0-9_]*', t) is None for t in tables + guarded + excludes)):
        raise BackupRefused('reviewed scope file missing or malformed')
    return {'name': raw['name'], 'tables': tables, 'written': sorted(written), 'guarded_children': sorted(guarded),
            'dump_excludes': sorted(excludes), 'sha256': scope_digest(raw['name'], tables)}


def _qualified_oids(conn, names: list[str]) -> dict[str, tuple[int, str]]:
    rows = conn.execute("""SELECT n.nspname || '.' || c.relname, c.oid::bigint, c.relkind
        FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname || '.' || c.relname = ANY(%s) AND c.relkind IN ('r', 'p', 'v', 'm', 'f', 'S')""",
                        (list(names),)).fetchall()
    return {name: (oid, kind) for name, oid, kind in rows}


_WRITE_TARGET = re.compile(
    r'\b(?:INSERT\s+INTO|DELETE\s+FROM|MERGE\s+INTO|UPDATE)\s+(?:ONLY\s+)?((?:[a-z_][a-z0-9_]*\.)?"?[a-z_][a-z0-9_]*"?)'
    r'(?:\s+(?:AS\s+)?[a-z_]\w*)?(?=\s+SET\b|\s*\(|\s+VALUES\b|\s+SELECT\b|\s+WHERE\b|\s+USING\b|\s*;|\s*$|\s+ON\b|\s+RETURNING\b)',
    re.I)


def trigger_write_targets(source: str) -> set[str]:
    """Tables a trigger function body writes (first level only; comments and string literals ignored)."""
    text = re.sub(r'--[^\n]*', ' ', source)
    text = re.sub(r'/\*.*?\*/', ' ', text, flags=re.S)
    text = re.sub(r"'(?:[^']|'')*'", "''", text)
    found = set()
    for match in _WRITE_TARGET.finditer(text):
        name = match.group(1).replace('"', '').lower()
        if name in ('set', 'new', 'old'):
            continue
        found.add(name if '.' in name else f'public.{name}')
    return found


def scoped_catalog(conn, scope: dict) -> dict:
    """Resolve the archived data set and refuse anything the scope does not honestly cover.

    Runs inside the exported snapshot. Refuses: a scope table missing or not a
    plain table; a trigger on a written table that writes outside the data set;
    a delete/update action of a written table that reaches an unreviewed child;
    a data set larger than the 30-minute budget.
    """
    wanted = scope['tables']
    found = _qualified_oids(conn, wanted)
    missing = [t for t in wanted if t not in found]
    if missing:
        raise BackupRefused('scope table missing on source: ' + ', '.join(missing))
    not_plain = [t for t in wanted if found[t][1] != 'r']
    if not_plain:
        raise BackupRefused('scope table is not an ordinary table: ' + ', '.join(not_plain))
    closure = conn.execute("""WITH RECURSIVE cl(o) AS (
            SELECT unnest(%s::bigint[]::oid[])
            UNION SELECT k.confrelid FROM cl JOIN pg_catalog.pg_constraint k ON k.conrelid = cl.o AND k.contype = 'f')
        SELECT n.nspname || '.' || c.relname, c.oid::bigint, c.relkind
        FROM cl JOIN pg_catalog.pg_class c ON c.oid = cl.o JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
        ORDER BY 1""", ([found[t][0] for t in wanted],)).fetchall()
    data = {name: (oid, kind) for name, oid, kind in closure}
    if any(kind != 'r' for _, kind in data.values()):
        raise BackupRefused('foreign-key parent is not an ordinary table: '
                            + ', '.join(sorted(n for n, (_, k) in data.items() if k != 'r')))
    oids = [oid for oid, _ in data.values()]
    written_oids = [found[t][0] for t in scope['written']]   # only written tables fire triggers or referential actions
    outside = set()
    for table, trigger, body in conn.execute("""SELECT n.nspname || '.' || c.relname, t.tgname, p.prosrc
            FROM pg_catalog.pg_trigger t JOIN pg_catalog.pg_class c ON c.oid = t.tgrelid
            JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace JOIN pg_catalog.pg_proc p ON p.oid = t.tgfoid
            WHERE NOT t.tgisinternal AND t.tgrelid = ANY(%s::bigint[]::oid[])""", (written_oids,)).fetchall():
        outside |= {f'{target} (trigger {trigger} on {table})' for target in trigger_write_targets(body) - set(data)}
    if outside:
        raise BackupRefused('a trigger on a scoped table writes outside the scope: ' + ', '.join(sorted(outside)))
    guarded = set(scope['guarded_children'])
    reach = conn.execute("""SELECT pn.nspname || '.' || pc.relname, cn.nspname || '.' || cc.relname
        FROM pg_catalog.pg_constraint k
        JOIN pg_catalog.pg_class pc ON pc.oid = k.confrelid JOIN pg_catalog.pg_namespace pn ON pn.oid = pc.relnamespace
        JOIN pg_catalog.pg_class cc ON cc.oid = k.conrelid JOIN pg_catalog.pg_namespace cn ON cn.oid = cc.relnamespace
        WHERE k.contype = 'f' AND k.confrelid = ANY(%s::bigint[]::oid[])
          AND (k.confdeltype IN ('c', 'n', 'd') OR k.confupdtype IN ('c', 'n', 'd'))""",
                         (written_oids,)).fetchall()
    unreviewed = sorted({f'{child} (action from {parent})' for parent, child in reach
                         if child not in data and child not in guarded})
    if unreviewed:
        raise BackupRefused('a delete/update action of a written table reaches an unreviewed table: ' + ', '.join(unreviewed))
    sequences = sorted(f'{ns}.{name}' for ns, name in conn.execute("""SELECT sn.nspname, s.relname
        FROM pg_catalog.pg_depend d JOIN pg_catalog.pg_class s ON s.oid = d.objid AND s.relkind = 'S'
        JOIN pg_catalog.pg_namespace sn ON sn.oid = s.relnamespace
        WHERE d.classid = 'pg_catalog.pg_class'::regclass AND d.refclassid = 'pg_catalog.pg_class'::regclass
          AND d.deptype IN ('a', 'i') AND d.refobjid = ANY(%s::bigint[]::oid[])""", (oids,)).fetchall())
    data_bytes = int(conn.execute('SELECT coalesce(sum(pg_catalog.pg_table_size(o)), 0) FROM unnest(%s::bigint[]::oid[]) AS o',
                                  (oids,)).fetchone()[0])
    if data_bytes > SCOPED_DATA_BUDGET_BYTES:
        raise BackupRefused(f'scoped data is {data_bytes} bytes; over the {SCOPED_DATA_BUDGET_BYTES}-byte 30-minute budget')
    return {'tables': sorted(data), 'closure': sorted(set(data) - set(wanted)), 'sequences': sequences,
            'data_bytes': data_bytes, 'dump_excludes': guarded_dump_excludes(conn, scope['dump_excludes'], set(data), oids)}


def guarded_dump_excludes(conn, declared: list[str], data: set[str], data_oids: list[int]) -> list[dict]:
    """The only way a relation outside the explicit -t set is ever named to pg_dump (SR-J2A-BACKUP-POSITIVE, fallback).

    A declared exclusion must lie outside the data set (scope plus foreign-key parents) and have no foreign-key edge
    to or from it; it is recorded with its catalog owner. Anything else refuses the capture.
    """
    out = []
    for name in declared:
        if name in data:
            raise BackupRefused(f'dump exclusion is inside the scope or its foreign-key closure: {name}')
        row = conn.execute("""SELECT c.oid::bigint, pg_catalog.pg_get_userbyid(c.relowner)
            FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname || '.' || c.relname = %s AND c.relkind IN ('r', 'p')""", (name,)).fetchone()
        if row is None:
            continue
        linked = conn.execute("""SELECT 1 FROM pg_catalog.pg_constraint k WHERE k.contype = 'f'
            AND ((k.conrelid = %s::bigint::oid AND k.confrelid = ANY(%s::bigint[]::oid[]))
              OR (k.confrelid = %s::bigint::oid AND k.conrelid = ANY(%s::bigint[]::oid[]))) LIMIT 1""",
                              (row[0], data_oids, row[0], data_oids)).fetchone()
        if linked:
            raise BackupRefused(f'dump exclusion has a foreign-key edge to the scope data: {name}')
        out.append({'table': name, 'owner': row[1]})
    return sorted(out, key=lambda e: e['table'])


def _row_aggregate_sql(relation):
    from psycopg import sql
    return sql.SQL("""SELECT count(*), coalesce(sum(u.h1), 0), coalesce(sum(u.h2), 0) FROM (
        SELECT ('x' || substr(encode(s.d, 'hex'), 1, 16))::bit(64)::bigint::numeric AS h1,
               ('x' || substr(encode(s.d, 'hex'), 17, 16))::bit(64)::bigint::numeric AS h2
        FROM (SELECT sha256(convert_to(row_to_json(t)::text, 'UTF8')) AS d FROM ONLY {} t) s) u""").format(relation)


def measure_sequences(conn, sequences: list[str]) -> dict:
    from psycopg import sql
    out = {}
    for name in sequences:
        schema, seq = name.split('.', 1)
        value, called = conn.execute(sql.SQL('SELECT last_value, is_called FROM {}').format(sql.Identifier(schema, seq))).fetchone()
        out[name] = {'last_value': int(value), 'is_called': bool(called)}
    return out


def scoped_measurements(conn, tables: list[str], sequences: list[str]) -> dict:
    """Per-table (rows, SHA-256 of rows:sum1:sum2) computed IN SQL: one scan, no sort, no row transfer.

    The aggregate is the count and two order-independent sums of the two
    64-bit halves of every row's SHA-256(row_to_json), so any changed, missing,
    duplicated or swapped row changes it, and row order is not a claim.
    """
    from psycopg import sql
    conn.execute("SET LOCAL timezone = 'UTC'")
    conn.execute("SET LOCAL extra_float_digits = 3")
    conn.execute(f"SET LOCAL statement_timeout = {int(SCOPED_STATEMENT_TIMEOUT_MS)}")
    out = {}
    for name in tables:
        schema, table = name.split('.', 1)
        count, h1, h2 = conn.execute(_row_aggregate_sql(sql.Identifier(schema, table))).fetchone()
        out[name] = {'rows': int(count), 'sha256': hashlib.sha256(f'{int(count)}:{int(h1)}:{int(h2)}'.encode()).hexdigest()}
    if not out:
        raise BackupRefused('no measured tables; refusing empty coverage')
    return {'tables': out, 'sequences': measure_sequences(conn, sequences)}


def measure_scope_now(tables: list[str], sequences: list[str], dsn: str | None = None) -> dict:
    """A fresh, strictly read-only measurement of the relations a scoped capture measured, by the same function the
    capture used (scoped_measurements): the check-time side of the scoped-content digest (SR-BACKUP-VALIDITY-A8).
    Opens its own READ ONLY transaction, never writes and always rolls back."""
    import psycopg
    source = dsn or os.environ.get('DATABASE_URL')
    if not source:
        raise BackupRefused('no database connection to measure the scoped content')
    with psycopg.connect(source, autocommit=True) as conn:
        conn.execute('BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY')
        try:
            return scoped_measurements(conn, tables, sequences)
        finally:
            conn.rollback()


def archive_manifest(archive: Path) -> dict:
    """Per-file SHA-256 of a directory archive and one digest over the sorted manifest."""
    files = []
    for path in sorted(p for p in archive.rglob('*') if p.is_file()):
        files.append({'path': path.relative_to(archive).as_posix(), 'bytes': path.stat().st_size, 'sha256': sha256(path)})
    digest = hashlib.sha256(json.dumps(files, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return {'files': files, 'sha256': digest}


def _lock_down(archive: Path) -> None:
    for path in [archive, *archive.rglob('*')]:
        os.chmod(path, 0o700 if path.is_dir() else 0o600)


_TOC_DATA = re.compile(r'^\d+; \d+ \d+ TABLE DATA (\S+) (\S+) \S+$', re.M)


_TOC_TABLE = re.compile(r'^\d+; \d+ \d+ TABLE (\S+) (\S+) \S+$', re.M)


def archive_tables(archive: Path, settings: dict) -> dict[str, set[str]]:
    """The relations whose definitions, and whose data, the archive's table of contents lists."""
    listing = client_output(['pg_restore', '--list', str(archive)], settings)
    return {'definitions': {f'{schema}.{table}' for schema, table in _TOC_TABLE.findall(listing)},
            'data': {f'{schema}.{table}' for schema, table in _TOC_DATA.findall(listing)}}


def _pattern(table: str) -> str:
    def quote(part):
        return '"' + part.replace('"', '""') + '"'
    return f"{quote(table.split('.', 1)[0])}.{quote(table.split('.', 1)[1])}"


def dump_table_args(tables: list[str], excludes: list[dict]) -> list[str]:
    """One quoted -t per relation of the data set (no pattern character widens it); --strict-names makes a
    relation that matches nothing refuse the dump. Nothing else is selected, locked or dumped."""
    return ['--strict-names', *(f'--table={_pattern(t)}' for t in tables),
            *(f"--exclude-table={_pattern(e['table'])}" for e in excludes)]


def _ledger_time(value) -> str:
    """A timestamptz as UTC ISO text, from a datetime (psycopg) or PostgreSQL's text output (pg_dump COPY)."""
    if not isinstance(value, datetime):
        found = re.fullmatch(r'(\d{4}-\d\d-\d\d)[ T](\d\d:\d\d:\d\d)(?:\.(\d{1,6}))?([+-]\d\d)(?::?(\d\d))?', str(value))
        if found is None:
            raise BackupRefused('migration ledger holds a malformed timestamp')
        day, clock, frac, hh, mm = found.groups()
        value = datetime.fromisoformat(f"{day}T{clock}.{(frac or '').ljust(6, '0')}{hh}:{mm or '00'}")
    return value.astimezone(timezone.utc).isoformat()


def ledger_entries(rows) -> list[dict]:
    entries = [{'id': int(i), 'filename': str(f), 'applied_at': _ledger_time(t), 'sha256': str(h)} for i, f, t, h in rows]
    # the earliest production rows predate the sha-256 format (short legacy tokens); a migration the base CARRIES is
    # compared to its file's real SHA-256 in derive_restore_migrations, so an old token can never reach the base
    if not entries or len({e['filename'] for e in entries}) != len(entries) or any(not e['sha256'] for e in entries):
        raise BackupRefused('migration ledger is empty, repeats a migration or holds a blank hash')
    return sorted(entries, key=lambda e: e['id'])


def ledger_digest(entries: list[dict]) -> dict:
    """Identity of a ledger: how many migrations, and a SHA-256 over (name, file hash, applied instant) sorted by name."""
    body = sorted([e['filename'], e['sha256'], e['applied_at']] for e in entries)
    return {'count': len(entries), 'sha256': hashlib.sha256(json.dumps(body, separators=(',', ':')).encode()).hexdigest()}


def ledger_from_connection(conn) -> list[dict]:
    """The ledger as a database holds it: production under the capture snapshot, or the restored scratch target."""
    return ledger_entries(conn.execute(f'SELECT id, filename, applied_at, sha256 FROM ONLY {SCOPED_LEDGER_TABLE} ORDER BY id').fetchall())


def ledger_from_archive(archive: Path, settings: dict) -> list[dict]:
    """The ledger exactly as the archive carries it (its data section for the ledger table), read before any restore."""
    lines = client_output(['pg_restore', '--data-only', '--schema=public', '--table=_migrations_applied',
                           '--file=-', str(archive)], settings).split('\n')
    heads = [n for n, line in enumerate(lines) if line.startswith('COPY ')]
    header = re.fullmatch(r'COPY public\._migrations_applied \(([^)]*)\) FROM stdin;', lines[heads[0]]) if len(heads) == 1 else None
    columns = [c.strip() for c in header.group(1).split(',')] if header else []
    wanted = ('id', 'filename', 'applied_at', 'sha256')
    if not set(wanted) <= set(columns):
        raise BackupRefused('archive holds no readable migration ledger')
    rows = []
    for line in lines[heads[0] + 1:]:
        if line == '\\.':
            break
        cells = line.split('\t')
        picked = [cells[columns.index(c)] for c in wanted] if len(cells) == len(columns) else None
        if picked is None or any('\\' in cell for cell in picked):
            raise BackupRefused('archive migration ledger row is malformed')
        rows.append(tuple(picked))
    else:
        raise BackupRefused('archive migration ledger is truncated')
    return ledger_entries(rows)


def derive_restore_migrations(ledger: list[dict], scope_tables: list[str], migrations_dir: Path | None = None) -> tuple:
    """The (file, sha256) migrations to apply on top of the bundle schema, in ledger order.

    Derived, never pinned: an entry applied after the bundle was cut whose repository file mentions a scope table.
    A candidate whose file is absent, or whose hash is not the one the ledger recorded, refuses (the base would not be
    what production ran).
    """
    cut = datetime.fromisoformat(SCOPED_RESTORE_BASE_CUT)
    mention = re.compile('(?<![A-Za-z0-9_])(?:' + '|'.join(re.escape(t.split('.', 1)[1]) for t in scope_tables)
                         + ')(?![A-Za-z0-9_])', re.I)
    directory = migrations_dir or MIGRATIONS_DIR
    chosen = []
    for entry in ledger:
        if datetime.fromisoformat(entry['applied_at']) <= cut:
            continue
        name = entry['filename']
        path = directory / name
        body = path.read_bytes() if re.fullmatch(r'[A-Za-z0-9_.-]+\.sql', name) and path.is_file() else None
        if body is None:
            raise BackupRefused(f'ledger migration applied after the bundle is missing from the repository: {name}')
        if hashlib.sha256(body).hexdigest() != entry['sha256']:
            raise BackupRefused(f'ledger migration differs from the file production applied: {name}')
        if mention.search(body.decode('utf-8', 'replace')):
            chosen.append((name, entry['sha256']))
    return tuple(chosen)


def restore_base_sql(root: Path, migrations: tuple = ()) -> tuple[str, dict]:
    """The governed L1 bundle schema plus the derived migrations as one executable script, and the identity of what it is built from.

    The bundle's schema.sql is a plain pg_dump with a psql-only restrict/unrestrict guard pair (dropped) and its own
    CREATE SCHEMA public, which the bundle's strict restore ran after dropping the empty public schema, followed by
    the five extensions. It is hash-checked against the bundle manifest before use; never printed or copied.
    `migrations` is derive_restore_migrations' (file, sha256) tuple; each file is hash-checked again as it is read.
    """
    try:
        raw = (root / SCOPED_RESTORE_BASE_PATH).read_bytes()
    except OSError:
        raise BackupRefused('restore base schema (governed L1 bundle) is not readable') from None
    if hashlib.sha256(raw).hexdigest() != SCOPED_RESTORE_BASE_SHA256:
        raise BackupRefused('restore base schema differs from the governed L1 bundle')
    text = ''.join(line for line in raw.decode('utf-8').splitlines(keepends=True)
                   if not line.startswith(('\\restrict ', '\\unrestrict ')))
    marker = '\nCREATE SCHEMA public;'
    if text.count(marker) != 1:
        raise BackupRefused('restore base schema has no single public schema declaration')
    end = text.index(marker) + len(marker)
    extensions = '\n'.join(f'CREATE EXTENSION IF NOT EXISTS "{e}" WITH SCHEMA public;' for e in SCOPED_RESTORE_BASE_EXTENSIONS)
    parts, applied = ['DROP SCHEMA public;\n', text[:end], '\n', extensions, '\n', text[end:]], []
    for name, expected in migrations:
        body = (MIGRATIONS_DIR / name).read_bytes() if re.fullmatch(r'[A-Za-z0-9_.-]+\.sql', name) else b''
        if hashlib.sha256(body).hexdigest() != expected:
            raise BackupRefused(f'restore base migration is missing or differs from the reviewed file: {name}')
        parts.append('\n' + body.decode('utf-8') + '\n')
        applied.append({'file': name, 'sha256': expected})
    return ''.join(parts), {'bundle': SCOPED_RESTORE_BASE_PATH, 'sha256': SCOPED_RESTORE_BASE_SHA256, 'migrations': applied}


def validate_scoped_capture(receipt: dict, archive: Path, label: str) -> dict:
    if receipt.get('schema') != SCOPED_BACKUP_SCHEMA or receipt.get('status') != 'captured':
        raise BackupRefused('complete scoped capture receipt is required')
    if receipt.get('label') != label:
        raise BackupRefused('capture label differs')
    scope = receipt.get('scope')
    current = load_scope()
    if (not isinstance(scope, dict) or scope.get('name') != current['name'] or scope.get('sha256') != current['sha256']
            or not isinstance(scope.get('tables'), list) or not isinstance(scope.get('closure'), list)
            or not isinstance(scope.get('sequences'), list)
            or set(scope['tables']) != set(current['tables']) | set(scope['closure'])):
        raise BackupRefused('capture scope differs from the reviewed scope; recapture required')
    if (not isinstance(scope.get('dump_excludes'), list)
            or any(not isinstance(e, dict) or set(e) != {'table', 'owner'} for e in scope['dump_excludes'])):
        raise BackupRefused('capture dump exclusions are missing or malformed')
    for key, shape in (('migrations_ledger', {'count', 'sha256'}), ('restore_base', {'bundle', 'sha256'})):
        if key in receipt and (not isinstance(receipt[key], dict) or set(receipt[key]) != shape
                               or not isinstance(receipt[key]['sha256'], str)
                               or re.fullmatch('[0-9a-f]{64}', receipt[key]['sha256']) is None):
            raise BackupRefused(f'capture {key} is malformed')
    manifest = receipt.get('archive')
    if (not archive.is_dir() or not isinstance(manifest, dict) or not manifest.get('files')
            or archive_manifest(archive) != {'files': manifest.get('files'), 'sha256': receipt.get('archive_sha256')}):
        raise BackupRefused('archive missing, empty or file hashes differ')
    if receipt.get('measurement_method') != SCOPED_MEASUREMENT_METHOD:
        raise BackupRefused('capture measurement method differs')
    # SR-BACKUP-VALIDITY-A8: a capture is valid while its scoped-content digest is unchanged, not for a time. Only the
    # capture instant is required; an older capture's `not_after` / `seconds` stay readable and are never a gate.
    validity = receipt.get('validity')
    try:
        start = datetime.fromisoformat(validity['not_before'])
    except (KeyError, TypeError, ValueError):
        raise BackupRefused('capture instant is missing or malformed') from None
    if start.tzinfo is None:
        raise BackupRefused('capture instant is missing or malformed')
    values = _check_provenance(receipt)
    _check_measurement_shapes(values)
    if set(values['tables']) != set(scope['tables']) or set(values['sequences']) != set(scope['sequences']):
        raise BackupRefused('measured relations differ from the scope')
    if 'scoped_content_digest' in receipt and receipt['scoped_content_digest'] != shared_policy.scoped_content_digest(values):
        raise BackupRefused('capture scoped-content digest differs from its measurements')
    return values


def validate_capture(receipt: dict, archive: Path, label: str) -> dict:
    if receipt.get('schema') != 'ky.smalltest_backup/1' or receipt.get('status') != 'captured':
        raise BackupRefused('complete capture receipt is required')
    if receipt.get('label') != label:
        raise BackupRefused('capture label differs')
    if not archive.is_file() or archive.stat().st_size == 0 or sha256(archive) != receipt.get('archive_sha256'):
        raise BackupRefused('archive missing, empty or hash differs')
    values = _check_provenance(receipt)
    _check_measurement_shapes(values)
    return values


def _check_provenance(receipt: dict) -> dict:
    values = receipt.get('measurements')
    snapshot_id, source = receipt.get('snapshot'), receipt.get('source')
    # pg_export_snapshot() emits two uppercase, eight-digit hexadecimal fields
    # and a positive decimal export counter (%08X-%08X-%d). Validate the saved
    # identifier's syntax, not its continued availability after capture ends.
    counter = re.fullmatch(r'[0-9A-F]{8}-[0-9A-F]{8}-([1-9][0-9]{0,9})', snapshot_id) if isinstance(snapshot_id, str) else None
    # the export counter is a C int (%d): an identifier beyond 2**31 - 1 cannot have come from pg_export_snapshot()
    if (counter is None or int(counter.group(1)) > 2**31 - 1
            or not isinstance(source, dict) or not isinstance(source.get('database'), str) or not source['database']
            or 'address' not in source or 'port' not in source
            or (source['address'] is None) != (source['port'] is None)
            or (source['address'] is not None and (not isinstance(source['address'], str) or not source['address']
                or type(source['port']) is not int or not 1 <= source['port'] <= 65535))
            or not isinstance(values, dict)):
        raise BackupRefused('capture provenance/measurements are missing or malformed')
    # (I) INTERPRETATION BG-01: snapshot() reads inet_server_addr()::text,
    # never a hostname. Accept IPs with an optional full-width host prefix
    # (/32 or /128), as PostgreSQL emits; Unix sockets retain explicit NULLs.
    if source['address'] is not None:
        try:
            parts = source['address'].split('/')
            address = ipaddress.ip_address(parts[0])
            if ('%' in parts[0] or len(parts) > 2
                    or (len(parts) == 2 and parts[1] != str(address.max_prefixlen))):
                raise ValueError('not a PostgreSQL host address')
        except ValueError:
            raise BackupRefused('capture source address is malformed') from None
    return values


def _check_measurement_shapes(values: dict) -> None:
    if set(values) != {'tables', 'sequences'} or not isinstance(values['tables'], dict) or not values['tables']:
        raise BackupRefused('table coverage is missing')
    for value in values['tables'].values():
        if (not isinstance(value, dict) or set(value) != {'rows', 'sha256'} or type(value['rows']) is not int
                or value['rows'] < 0 or not isinstance(value['sha256'], str)
                or re.fullmatch('[0-9a-f]{64}', value['sha256']) is None):
            raise BackupRefused('invalid table measurements')
    if not isinstance(values['sequences'], dict):
        raise BackupRefused('invalid sequence measurements')
    for value in values['sequences'].values():
        if (not isinstance(value, dict) or set(value) != {'last_value', 'is_called'}
                or type(value['last_value']) is not int or type(value['is_called']) is not bool):
            raise BackupRefused('invalid sequence measurements')


def snapshot(folder: Path, label: str, scope: str = 'full') -> dict:
    if scope == 'small_test':
        return snapshot_scoped(folder, label)
    import psycopg
    from psycopg.conninfo import conninfo_to_dict
    source = os.environ.get('DATABASE_URL')
    if not source:
        raise BackupRefused('executor source connection is missing')
    settings = conninfo_to_dict(source)
    client_env(settings)  # validate before creating any archive directory
    folder.parent.mkdir(parents=True, exist_ok=True)
    folder.mkdir(mode=0o700)  # no overwrite/retry into an existing label
    archive = folder / 'database.dump'
    with psycopg.connect(source, autocommit=True) as conn:
        conn.execute('BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY')
        snapshot_id = conn.execute('SELECT pg_export_snapshot()').fetchone()[0]
        db, address, port = conn.execute('SELECT current_database(), inet_server_addr()::text, inet_server_port()').fetchone()
        measured = measurements(conn)
        run_client(['pg_dump', '--format=custom', '--no-owner', '--no-privileges',
                    f'--snapshot={snapshot_id}', '--file', str(archive)], settings)
        os.chmod(archive, 0o600)
        after = measurements(conn)
        if measured != after:
            raise BackupRefused('source sequence state or measured coverage changed during capture')
        conn.rollback()
    if archive.stat().st_size == 0:
        raise BackupRefused('empty archive')
    receipt = {'schema': 'ky.smalltest_backup/1', 'label': label, 'status': 'captured',
               'ts': datetime.now(timezone.utc).isoformat(), 'snapshot': snapshot_id,
               'source': {'database': db, 'address': address, 'port': port},
               'archive_sha256': sha256(archive), 'measurements': measured,
               'script_sha256': sha256(Path(__file__)),
               'coverage': 'complete logical database; table content and sequence state measured; roles/grants excluded',
               'backup_taken': True, 'restore_verified': None}
    validate_capture(receipt, archive, label)
    write_receipt(folder / 'capture.json', receipt)
    return receipt


def restore_verify(folder: Path, label: str, scope: str = 'full') -> dict:
    import psycopg
    from psycopg import sql
    receipt = json.loads((folder / 'capture.json').read_text())
    if (receipt.get('schema') == SCOPED_BACKUP_SCHEMA) != (scope == 'small_test'):
        raise BackupRefused('capture scope differs from the requested scope')
    if scope == 'small_test':
        return restore_verify_scoped(folder, label, receipt)
    archive = folder / 'database.dump'
    expected = validate_capture(receipt, archive, label)
    if receipt.get('script_sha256') != sha256(Path(__file__)):
        raise BackupRefused('capture script identity changed; recapture required')
    if (folder / 'restore.json').exists():
        raise BackupRefused('restore evidence already exists; use a fresh label')
    target = scratch_settings(label)
    # libpq treats service='' as a service lookup, not as disabling services.
    # Refuse an inherited service before connecting; all scratch endpoint fields
    # are explicit and the passfile/options defaults are disabled below.
    if 'PGSERVICE' in os.environ:
        raise BackupRefused('scratch restore refuses inherited PGSERVICE')
    admin = dict(target, dbname='postgres', passfile=os.devnull, options='')
    with psycopg.connect(**admin, autocommit=True) as control:
        if receipt['source'].get('database') == target['dbname']:
            raise BackupRefused('restore target has the source database name')
        if control.execute('SELECT 1 FROM pg_database WHERE datname = %s', (target['dbname'],)).fetchone():
            raise BackupRefused('restore target already exists; no reuse, reset or deletion is permitted')
        # CREATE is atomic: a concurrent creation fails before the finally
        # block. Only a database created by this invocation can be dropped.
        control.execute(sql.SQL('CREATE DATABASE {} TEMPLATE template0').format(sql.Identifier(target['dbname'])))
        try:
            run_client(['pg_restore', '--exit-on-error', '--single-transaction', '--no-owner', '--no-privileges',
                        '--dbname', target['dbname'], str(archive)], target)
            with psycopg.connect(**dict(target, passfile=os.devnull, options=''), autocommit=True) as conn:
                conn.execute('BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY')
                actual = measurements(conn)
                compare_restore(expected, actual)
                conn.rollback()
        finally:
            control.execute(sql.SQL('DROP DATABASE {}').format(sql.Identifier(target['dbname'])))
    proof = {'schema': 'ky.smalltest_restore/1', 'label': label, 'status': 'verified',
             'ts': datetime.now(timezone.utc).isoformat(), 'archive_sha256': receipt['archive_sha256'],
             'capture_sha256': sha256(folder / 'capture.json'), 'script_sha256': sha256(Path(__file__)),
             'target': {'host': target['host'], 'port': target['port'], 'database': target['dbname']},
             'measurements': actual, 'target_removed': True, 'backup_taken': True, 'restore_verified': True}
    write_receipt(folder / 'restore.json', proof)
    return proof


def snapshot_scoped(folder: Path, label: str) -> dict:
    import psycopg
    from psycopg.conninfo import conninfo_to_dict
    scope = load_scope()
    source = os.environ.get('DATABASE_URL')
    if not source:
        raise BackupRefused('executor source connection is missing')
    settings = conninfo_to_dict(source)
    client_env(settings)  # validate before creating any archive directory
    folder.parent.mkdir(parents=True, exist_ok=True)
    folder.mkdir(mode=0o700)  # no overwrite/retry into an existing label
    archive = folder / 'database.dir'  # pg_dump creates (and requires absent) the directory
    with psycopg.connect(source, autocommit=True) as conn:
        conn.execute('BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY')
        snapshot_id = conn.execute('SELECT pg_export_snapshot()').fetchone()[0]
        snapshot_ts = datetime.now(timezone.utc)
        db, address, port = conn.execute('SELECT current_database(), inet_server_addr()::text, inet_server_port()').fetchone()
        if conn.execute("SELECT EXISTS (SELECT 1 FROM pg_catalog.pg_class WHERE relkind = 'f')").fetchone()[0]:
            raise BackupRefused('foreign-table data is not covered by a logical archive')
        if conn.execute('SELECT EXISTS (SELECT 1 FROM pg_catalog.pg_largeobject_metadata)').fetchone()[0]:
            raise BackupRefused('large objects require separately reviewed capture/restore measurements')
        catalog = scoped_catalog(conn, scope)
        if SCOPED_LEDGER_TABLE not in catalog['tables']:
            raise BackupRefused('the migration ledger table is not in the scope; the restore base cannot be derived')
        ledger = ledger_digest(ledger_from_connection(conn))   # same snapshot as the dump: the ledger the archive carries
        measured = scoped_measurements(conn, catalog['tables'], catalog['sequences'])
        run_client(['pg_dump', '--format=directory', f'--jobs={SCOPED_DUMP_JOBS}', '--no-owner', '--no-privileges',
                    f'--snapshot={snapshot_id}', '--file', str(archive), *dump_table_args(catalog['tables'], catalog['dump_excludes'])],
                   settings, SCOPED_DUMP_TIMEOUT_S)
        _lock_down(archive)
        # Tables cannot differ inside one REPEATABLE READ snapshot; sequences are not transactional.
        if measure_sequences(conn, catalog['sequences']) != measured['sequences']:
            raise BackupRefused('source sequence state changed during capture')
        conn.rollback()
    listed = archive_tables(archive, settings)
    if listed['data'] != set(catalog['tables']):
        raise BackupRefused('archive data entries differ from the scope')
    if listed['definitions'] != set(catalog['tables']):
        raise BackupRefused('archive definitions differ from the scope')
    manifest = archive_manifest(archive)
    if not manifest['files']:
        raise BackupRefused('empty archive')
    receipt = {'schema': SCOPED_BACKUP_SCHEMA, 'label': label, 'status': 'captured',
               'ts': datetime.now(timezone.utc).isoformat(), 'snapshot': snapshot_id, 'snapshot_ts': snapshot_ts.isoformat(),
               'source': {'database': db, 'address': address, 'port': port},
               'archive_sha256': manifest['sha256'], 'archive': {'format': 'directory', 'files': manifest['files']},
               'measurements': measured, 'measurement_method': SCOPED_MEASUREMENT_METHOD,
               'scoped_content_digest': shared_policy.scoped_content_digest(measured),
               'script_sha256': sha256(Path(__file__)),
               'migrations_ledger': ledger,
               'restore_base': {'bundle': SCOPED_RESTORE_BASE_PATH, 'sha256': SCOPED_RESTORE_BASE_SHA256},
               'scope': {'name': scope['name'], 'sha256': scope['sha256'], 'tables': catalog['tables'],
                         'closure': catalog['closure'], 'sequences': catalog['sequences'], 'data_bytes': catalog['data_bytes'],
                         'dump_excludes': catalog['dump_excludes']},
               'validity': {'not_before': snapshot_ts.isoformat(), 'basis': 'scoped_content_digest_unchanged'},
               'coverage': 'SCOPED logical backup, not a complete database: definitions, data, sequences and content '
                           'measurements of the listed scope tables and their foreign-key parents only; every other '
                           "relation's definition and data, functions, types, roles and grants excluded",
               'backup_taken': True, 'restore_verified': None}
    validate_scoped_capture(receipt, archive, label)
    write_receipt(folder / 'capture.json', receipt)
    return receipt


def restore_verify_scoped(folder: Path, label: str, receipt: dict) -> dict:
    import psycopg
    from psycopg import sql
    archive = folder / 'database.dir'
    expected = validate_scoped_capture(receipt, archive, label)
    legacy = receipt.get('script_sha256') in SCOPED_LEGACY_CAPTURE_SCRIPTS
    if receipt.get('script_sha256') != sha256(Path(__file__)) and not legacy:
        raise BackupRefused('capture script identity changed; recapture required')
    if not legacy and ('migrations_ledger' not in receipt or 'restore_base' not in receipt):
        raise BackupRefused('capture records no migration ledger or restore base; recapture required')
    if SCOPED_LEDGER_TABLE not in receipt['scope']['tables']:
        raise BackupRefused('the migration ledger table is not in the captured scope; the restore base cannot be derived')
    if (folder / 'restore.json').exists():
        raise BackupRefused('restore evidence already exists; use a fresh label')
    target = scratch_settings(label)
    if 'PGSERVICE' in os.environ:
        raise BackupRefused('scratch restore refuses inherited PGSERVICE')
    # SR-J2A-RESTORE-BASE: the base is derived from the ledger the ARCHIVE carries (production's state at the snapshot),
    # which must be the ledger the capture recorded when it recorded one. Nothing about the base is pinned.
    ledger = ledger_from_archive(archive, target)
    identity = ledger_digest(ledger)
    if identity['count'] != expected['tables'][SCOPED_LEDGER_TABLE]['rows']:
        raise BackupRefused('archive migration ledger does not have the measured row count')
    if receipt.get('migrations_ledger', identity) != identity:
        raise BackupRefused('migration ledger in the archive differs from the ledger recorded at capture')
    if receipt.get('restore_base', {'bundle': SCOPED_RESTORE_BASE_PATH, 'sha256': SCOPED_RESTORE_BASE_SHA256}) != {
            'bundle': SCOPED_RESTORE_BASE_PATH, 'sha256': SCOPED_RESTORE_BASE_SHA256}:
        raise BackupRefused('restore base recorded at capture differs from the base this proof would use')
    migrations = derive_restore_migrations(ledger, receipt['scope']['tables'])
    admin = dict(target, dbname='postgres', passfile=os.devnull, options='')
    with psycopg.connect(**admin, autocommit=True) as control:
        if receipt['source'].get('database') == target['dbname']:
            raise BackupRefused('restore target has the source database name')
        if control.execute('SELECT 1 FROM pg_database WHERE datname = %s', (target['dbname'],)).fetchone():
            raise BackupRefused('restore target already exists; no reuse, reset or deletion is permitted')
        base_sql, base = restore_base_sql(Path(os.environ.get('KY_ROOT', '/Users/Dev/kalayantra')), migrations)
        base['ledger'] = dict(identity, source='capture' if 'migrations_ledger' in receipt else 'archive')
        control.execute(sql.SQL('CREATE DATABASE {} TEMPLATE template0').format(sql.Identifier(target['dbname'])))
        try:
            with psycopg.connect(**dict(target, passfile=os.devnull, options='')) as prep:
                prep.execute(base_sql)
                # the archive's own definitions replace the base's copies of exactly the data set
                for name in receipt['scope']['tables']:
                    prep.execute(sql.SQL('DROP TABLE IF EXISTS {} CASCADE').format(sql.Identifier(*name.split('.', 1))))
            run_client(['pg_restore', '--exit-on-error', '--single-transaction', '--no-owner', '--no-privileges',
                        '--dbname', target['dbname'], str(archive)], target, SCOPED_RESTORE_TIMEOUT_S)
            with psycopg.connect(**dict(target, passfile=os.devnull, options=''), autocommit=True) as conn:
                conn.execute('BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY')
                if ledger_digest(ledger_from_connection(conn)) != identity:
                    raise BackupRefused('migration ledger at restore differs from the ledger the base was derived from')
                actual = scoped_measurements(conn, receipt['scope']['tables'], receipt['scope']['sequences'])
                compare_restore(expected, actual)
                conn.rollback()
        finally:
            control.execute(sql.SQL('DROP DATABASE {}').format(sql.Identifier(target['dbname'])))
    proof = {'schema': SCOPED_RESTORE_SCHEMA, 'label': label, 'status': 'verified',
             'ts': datetime.now(timezone.utc).isoformat(), 'archive_sha256': receipt['archive_sha256'],
             'capture_sha256': sha256(folder / 'capture.json'), 'script_sha256': sha256(Path(__file__)),
             'target': {'host': target['host'], 'port': target['port'], 'database': target['dbname']},
             'measurements': actual, 'scoped': True, 'scope_sha256': receipt['scope']['sha256'], 'restore_base': base,
             'snapshot_ts': receipt['snapshot_ts'], 'validity': receipt['validity'],
             'target_removed': True, 'backup_taken': True, 'restore_verified': True}
    write_receipt(folder / 'restore.json', proof)
    return proof


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    root = Path(os.environ.get('KY_ROOT', '/Users/Dev/kalayantra'))
    folder = root / 'run/ops/backups' / args.label
    if not args.execute:
        plan = {'operation': args.operation, 'label': args.label, 'status': 'planned',
                'archive_directory': str(folder), 'scratch_database': f'ky_restore_{args.label}',
                'backup_taken': None, 'restore_verified': None}
        if args.scope == 'small_test':
            try:
                plan.update(scope=args.scope, scope_sha256=load_scope()['sha256'], validity_basis='scoped_content_digest_unchanged')
            except BackupRefused as exc:
                print(f'backup refused: {exc}', file=sys.stderr)
                return 1
        print(json.dumps(plan, sort_keys=True))
        return 0
    try:
        proof = (snapshot if args.operation == 'snapshot' else restore_verify)(folder, args.label, args.scope)
        print(json.dumps(proof, sort_keys=True))
        return 0
    except BackupRefused as exc:
        print(f'backup refused: {exc}', file=sys.stderr)
    except Exception as exc:
        print(f'backup failed: {type(exc).__name__}; error text withheld', file=sys.stderr)
    return 1


if __name__ == '__main__':
    sys.exit(main())
