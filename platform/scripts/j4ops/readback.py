#!/usr/bin/env python3
"""Pinned, read-only J4 provisioning/second-window evidence capture.

Credentials stay in the executor's libpq environment. No credential read, cloud
command, migration apply or qualification claim. A matched readback measures only
its declared observations; G8, acts, independent review and golden equality are
separate. Expected window bytes MUST come from the reviewed mirror, never from
this target's current state. No default/guessed second-window manifest is shipped.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
SQL_PINS = {'provision.sql': '68ff21eea10cac58b5463827b3936756406a0bb687ef992fb20ea726e531ebcd', 'second_window.sql': '768af8a03cb6bee3467d41d392837bbaed2e9d5b82f1f1b060eaea71be7122ad'}
PRIVILEGES = ('SELECT', 'INSERT', 'UPDATE', 'DELETE', 'TRUNCATE', 'REFERENCES', 'TRIGGER')
WRITE_PRIVILEGES = ('INSERT', 'UPDATE', 'DELETE', 'TRUNCATE')
VERIFICATION_TABLES = ('ka_gochara_eval_window_verification', 'ka_gochara_search_inventory_verification')
IDENTITY_SQL = """SELECT jsonb_build_object(
  'current_database', current_database(), 'current_user', current_user, 'session_user', session_user,
  'server_address', inet_server_addr()::text, 'server_port', inet_server_port(),
  'observed_at', clock_timestamp(), 'server_version_num', current_setting('server_version_num'),
  'transaction_read_only', current_setting('transaction_read_only'),
  'default_transaction_read_only', current_setting('default_transaction_read_only'));
"""


def _strict(raw):
    def pairs(values):
        out = {}
        for key, value in values:
            if key in out:
                raise ValueError('duplicate JSON key')
            out[key] = value
        return out
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('non-finite JSON number')))


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def sql_bytes(name, *, directory=HERE):
    if name not in SQL_PINS:
        raise ValueError('unallocated SQL file')
    raw = (Path(directory) / name).read_bytes()
    if _sha(raw) != SQL_PINS[name]:
        raise ValueError('SQL digest mismatch')
    if any(line.lstrip().startswith(b'\\') for line in raw.splitlines()):
        raise ValueError('psql meta-command refused')
    return raw


def readonly_environment(environ):
    env = dict(environ)
    env['PGOPTIONS'] = (env.get('PGOPTIONS', '') +
                        ' -c default_transaction_read_only=on -c statement_timeout=840000').strip()
    return env


def check_identity(identity, expected_database):
    if (not isinstance(identity, dict) or identity.get('current_database') != expected_database
            or identity.get('transaction_read_only') != 'on'
            or identity.get('default_transaction_read_only') != 'on'):
        raise ValueError('read-only session identity mismatch')


def capture(phase, expected_database, *, runner=subprocess.run, environ=None):
    name = {'provision': 'provision.sql', 'second-window': 'second_window.sql'}[phase]
    raw_sql = sql_bytes(name)
    # All observations from one read-only repeatable-read snapshot/session.
    sql = ('BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;\n' + IDENTITY_SQL +
           raw_sql.decode('utf-8') + '\nROLLBACK;\n')
    result = runner(['psql', '-X', '-q', '-t', '-A', '-v', 'ON_ERROR_STOP=1'],
                    input=sql, capture_output=True, text=True, check=False, timeout=900,
                    env=readonly_environment(os.environ if environ is None else environ))
    if result.returncode:
        raise ValueError('read-only SQL failed; no successful capture')
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    if len(lines) != 2:
        raise ValueError('unexpected readback output shape')
    identity, data = [_strict(line) for line in lines]
    check_identity(identity, expected_database)
    return identity, data, result.stdout.encode('utf-8')


def grant_problems(cells):
    expected = {(role, table, privilege): privilege == 'SELECT'
                for role in ('gochara_verifier', 'gochara_sealer')
                for table in ('chart_facts', 'chart_dashas') for privilege in PRIVILEGES}
    expected.update({('data_plane_builder', table, privilege): False
                     for table in VERIFICATION_TABLES for privilege in WRITE_PRIVILEGES})
    observed = {}
    if not isinstance(cells, list):
        return ['grant matrix is not a list']
    for cell in cells:
        if not isinstance(cell, dict) or set(cell) != {'role', 'table', 'privilege', 'present'}:
            return ['grant cell shape differs']
        key = (cell['role'], cell['table'], cell['privilege'])
        if key in observed:
            return ['duplicate grant cell']
        if type(cell['present']) is not bool:
            return ['grant principal/relation absent or unmeasured']
        observed[key] = cell['present']
    if set(observed) != set(expected):
        return ['grant matrix membership differs']
    return ['%s %s %s differs' % key for key, value in expected.items() if observed[key] is not value]


def window_problems(observed, expected):
    fields = {'server_major', 'ledger', 'functions', 'triggers', 'dormant_writes', 'app_schema_create'}
    if not isinstance(expected, dict) or set(expected) != fields:
        raise ValueError('complete reviewed window expectations required')
    if type(expected['server_major']) is not int or expected['server_major'] < 10:
        raise ValueError('reviewed PostgreSQL major version required')
    for name in ('ledger', 'functions', 'triggers'):
        if not isinstance(expected[name], list) or not expected[name]:
            raise ValueError('nonempty reviewed ledger/function/trigger expectations required')
    if expected['dormant_writes'] != [] or expected['app_schema_create'] is not False:
        raise ValueError('expectations cannot allow dormant writes or app schema CREATE')
    if not isinstance(observed, dict) or set(observed) != fields:
        return ['window readback shape differs']
    return [name + ' differs from reviewed expectation' for name in sorted(fields)
            if observed[name] != expected[name]]


def _write(path, raw):
    with Path(path).open('xb') as stream:
        stream.write(raw)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('--phase', required=True, choices=('provision', 'second-window'))
    parser.add_argument('--expect-db', required=True)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--runner-sha256', required=True)
    parser.add_argument('--expected-file', type=Path)
    parser.add_argument('--expected-sha256')
    args = parser.parse_args(argv)
    try:
        runner_sha = _sha(Path(__file__).read_bytes())
        if runner_sha != args.runner_sha256:
            raise ValueError('runner digest mismatch')
        expected = None
        if args.phase == 'second-window':
            if not args.expected_file or not args.expected_sha256:
                raise ValueError('reviewed window expectations required')
            expected_raw = args.expected_file.read_bytes()
            if not expected_raw or _sha(expected_raw) != args.expected_sha256:
                raise ValueError('expected-file digest mismatch')
            expected = _strict(expected_raw)
            window_problems(expected, expected)  # validate before connecting
        elif args.expected_file or args.expected_sha256:
            raise ValueError('provision expectations are fixed in code')
        args.out.mkdir(parents=True, exist_ok=False)  # preserve immutable earlier evidence
        identity, data, raw = capture(args.phase, args.expect_db)
        problems = grant_problems(data) if args.phase == 'provision' else window_problems(data, expected)
        record = dict(schema='ky.j4ops_readback/1', phase=args.phase,
                      status='READBACK_MATCHED' if not problems else 'READBACK_MISMATCH',
                      identity=identity, problems=problems, runner_sha256=runner_sha,
                      sql_sha256={('provision.sql' if args.phase == 'provision' else 'second_window.sql'):
                                  SQL_PINS['provision.sql' if args.phase == 'provision' else 'second_window.sql']},
                      expected_sha256=args.expected_sha256,
                      operation_completed=False, enabled=False)
        files = {'raw.jsonl': raw, 'readback.json': (json.dumps(record, sort_keys=True) + '\n').encode(),
                 'RUNNER_SHA256': (runner_sha + '\n').encode()}
        for name, value in files.items():
            _write(args.out / name, value)
        _write(args.out / 'MANIFEST.sha256', ''.join(_sha(value) + '  ' + name + '\n'
                                                   for name, value in sorted(files.items())).encode())
        print(json.dumps(record, sort_keys=True))
        return 1 if problems else 0
    except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError):
        print('REFUSED: readback inputs/session failed validation; no qualification claimed', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
