#!/usr/bin/env python3
"""J-1a local rehearsal adapter; no production, launch, restore or execute mode.

(I) INTERPRETATION J1A-I1: backup --dry-run is the P01 CLI's no-effect plan,
not backup/restore attestation. Teardown rehearses the initial empty lane only;
a populated lane must use the existing reviewed scope/evidence workflow.
(I) INTERPRETATION J1A-I2: readback_sql with a lane target is a fixed independent
whole-database content/sequence measurement, with no caller-supplied SQL.
"""
from __future__ import annotations

import argparse
import ipaddress
import json
import os
from pathlib import Path
import subprocess
import sys

# This sibling and every child script come from the same reviewed Git export.
import executor

ROOT = Path(__file__).resolve().parents[4]
SCRIPTS = ROOT / 'platform/scripts'
sys.path.insert(0, str(SCRIPTS))
import backup_v5_small_test_job as backup


def digest(value):
    return executor.digest_bytes(json.dumps(value, sort_keys=True, separators=(',', ':'), default=str).encode())


def observe(req):
    """Separate read-only session, explicit settings, verified actual endpoint."""
    import psycopg
    settings = executor.lane_target_settings(req)
    with psycopg.connect(**settings) as conn:
        conn.read_only = True
        db, address, port = conn.execute(
            'SELECT current_database(), inet_server_addr()::text, inet_server_port()').fetchone()
        if db != settings['dbname'] or not ipaddress.ip_interface(address).ip.is_loopback or port != 55433:
            raise ValueError('lane readback server identity differs')
        measured = backup.measurements(conn)
        conn.rollback()
    return dict(database=db, address=address, port=port, measurements=measured)


def child_command(req, op):
    """Use the existing six entry points, but NEVER their production fixed_args."""
    kind = req['kind']
    args = req.get('args', {})
    tail = [value for key, value in args.items() for value in ('--' + key, value)]
    if kind.startswith('backup_'):
        return [sys.executable, str(ROOT / op['script']), '--operation',
                'snapshot' if kind == 'backup_snapshot' else 'restore-verify', '--dry-run', *tail]
    if kind == 'smalltest_dispatch':
        return [sys.executable, str(ROOT / op['script']), '--dry-run', *tail]
    if kind == 'smalltest_dispatch_dryrun':
        return [sys.executable, str(ROOT / op['script']), '--i-am-steward', '--after-settled-1', '--dry-run', *tail]
    if kind in ('smalltest_teardown', 'smalltest_teardown_dryrun'):
        return [sys.executable, str(ROOT / op['script']), '--dry-run']
    raise ValueError('no lane child binding')


def run(req):
    from psycopg.conninfo import make_conninfo
    settings = executor.lane_target_settings(req)  # before any import with effects, connection or child
    table = json.loads((Path(__file__).parent / 'executor_ops.json').read_text())['ops']
    op = table.get(req.get('kind'), {})
    binding = op.get('lane_readback' if req.get('kind') == 'readback_sql' else 'lane_dry_run')
    if not op.get('enabled') or not binding or req.get('requested_by') not in op.get('requesters', ['adhikarin']):
        raise ValueError('lane kind disabled, unbound or requester refused')
    # The adapter also rejects selector/argument confusion if invoked directly.
    if not isinstance(req.get('args', {}), dict) or any(key not in op['allowed_args'] for key in req.get('args', {})):
        raise ValueError('disallowed lane arguments')
    if req['kind'] == 'readback_sql' and req.get('args'):
        raise ValueError('lane readback takes no SQL or arguments')
    qualification = executor.lane_qualification(req)
    before = observe(req)
    output = ''
    if req['kind'] != 'readback_sql':
        scratch = Path(os.environ['TMPDIR'])
        env = executor.lane_child_env(req, scratch)
        env['DATABASE_URL'] = make_conninfo(**settings)
        env['PYTHONPATH'] = str(ROOT / 'platform/python-sidecar')
        child = dict(req)
        # The existing empty-scope check is preserved, not bypassed or weakened.
        # Neither production acceptance nor a launch receipt is fabricated.
        if 'teardown' in req['kind']:
            child.update(kind='smalltest_teardown_dryrun', smalltest_scope={'empty': True})
        env['KY_OPERATION_REQUEST'] = json.dumps(child, sort_keys=True, separators=(',', ':'))
        result = subprocess.run(child_command(req, op), env=env, cwd=ROOT,
                                capture_output=True, text=True, timeout=600, check=False)
        output = result.stdout + '\n' + result.stderr
        if result.returncode:
            # Local dry-run diagnostics contain no inherited credentials. Keep
            # their complete redacted output in executor evidence on failure.
            print(executor.redact(output), file=sys.stderr)
            raise ValueError('lane dry-run child refused or failed')
    after = observe(req)
    if any(entry['after_sha256'] != digest(after) for entry in qualification):
        raise ValueError('final lane readback differs from the six rehearsals')
    if before != after:
        raise ValueError('independent lane content/sequence readback changed')
    proof = dict(schema='ky.smalltest_lane/1', status='DRY_RUN_VERIFIED',
        operation_id=req['operation_id'], request_id=req['request_id'], kind=req['kind'],
        request_sha256=executor.request_digest(req), reviewed_commit=req['reviewed_commit'],
        lane_target=req['lane_target'], dry_run=True, production=False,
        script=op['script'], script_sha256=executor.digest_bytes((ROOT / op['script']).read_bytes()),
        child_output_sha256=executor.digest_bytes(output.encode()),
        before_sha256=digest(before), after_sha256=digest(after), independent_readback=True, unchanged=True,
        qualification=qualification, qualification_sha256=digest(qualification) if qualification else None,
        readback=after, backup_taken=None, restore_verified=None, launched=False)
    # Preserve the real CLI output as part of the executor's complete evidence.
    if output: print(output, end='' if output.endswith('\n') else '\n')
    print(json.dumps(proof, sort_keys=True, default=str), flush=True)
    return proof


def cli(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('--dry-run', action='store_true', required=True)
    parser.add_argument('--lane-target', required=True, help='structured JSON endpoint, matching the executor request')
    args = parser.parse_args(argv)
    try:
        req = json.loads(os.environ['KY_OPERATION_REQUEST'])
        if json.loads(args.lane_target) != req.get('lane_target'):
            raise ValueError('CLI lane target differs from executor request')
        run(req)
        return 0
    except Exception as exc:
        print(f'lane rehearsal refused ({type(exc).__name__}); no production route or launch is available', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(cli())
