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
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys


class BackupRefused(RuntimeError):
    """A safe named refusal; never contains connection settings."""


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    p.add_argument('--operation', choices=['snapshot', 'restore-verify'], required=True)
    p.add_argument('--label', required=True)
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


def run_client(argv: list[str], settings: dict) -> None:
    result = subprocess.run(argv, env=client_env(settings), stdout=subprocess.DEVNULL,
                            stderr=subprocess.PIPE, timeout=14400, check=False)
    if result.returncode:
        raise BackupRefused(f'{argv[0]} failed (exit {result.returncode}; error text withheld)')


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


def validate_capture(receipt: dict, archive: Path, label: str) -> dict:
    if receipt.get('schema') != 'ky.smalltest_backup/1' or receipt.get('status') != 'captured':
        raise BackupRefused('complete capture receipt is required')
    if receipt.get('label') != label:
        raise BackupRefused('capture label differs')
    if not archive.is_file() or archive.stat().st_size == 0 or sha256(archive) != receipt.get('archive_sha256'):
        raise BackupRefused('archive missing, empty or hash differs')
    values = receipt.get('measurements')
    snapshot_id, source = receipt.get('snapshot'), receipt.get('source')
    # Match the provenance emitted by snapshot(), including explicit NULL
    # endpoint fields for a Unix-socket source. Truthiness alone admits a
    # non-string snapshot or a source with no database identity, defeating the
    # source/restore-target name separation check below.
    if (not isinstance(snapshot_id, str) or not snapshot_id.strip()
            or not isinstance(source, dict) or not isinstance(source.get('database'), str) or not source['database']
            or 'address' not in source or 'port' not in source
            or (source['address'] is None) != (source['port'] is None)
            or (source['address'] is not None and (not isinstance(source['address'], str) or not source['address']
                or type(source['port']) is not int or not 1 <= source['port'] <= 65535))
            or not isinstance(values, dict)):
        raise BackupRefused('capture provenance/measurements are missing or malformed')
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
    return values


def snapshot(folder: Path, label: str) -> dict:
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
    write_receipt(folder / 'capture.json', receipt)
    return receipt


def restore_verify(folder: Path, label: str) -> dict:
    import psycopg
    from psycopg import sql
    receipt = json.loads((folder / 'capture.json').read_text())
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


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    root = Path(os.environ.get('KY_ROOT', '/Users/Dev/kalayantra'))
    folder = root / 'run/ops/backups' / args.label
    if not args.execute:
        print(json.dumps({'operation': args.operation, 'label': args.label, 'status': 'planned',
                          'archive_directory': str(folder), 'scratch_database': f'ky_restore_{args.label}',
                          'backup_taken': None, 'restore_verified': None}, sort_keys=True))
        return 0
    try:
        proof = (snapshot if args.operation == 'snapshot' else restore_verify)(folder, args.label)
        print(json.dumps(proof, sort_keys=True))
        return 0
    except BackupRefused as exc:
        print(f'backup refused: {exc}', file=sys.stderr)
    except Exception as exc:
        print(f'backup failed: {type(exc).__name__}; error text withheld', file=sys.stderr)
    return 1


if __name__ == '__main__':
    sys.exit(main())
