"""J-6r lane run: build a throwaway ``ky_j6r_*`` database, rehearse the flip and rollback, drop it.

    cd platform/python-sidecar && python -m scripts.kala_gochara_cutover.j6r_lane_run --out EVIDENCE.json

Local lane only: the admin DSN must name exactly one loopback host (the shared
A5.3 guard), the database it creates is ``ky_j6r_<8 hex>`` and is the only one it
ever drops. Writes identifiers, counts and digests only: no chart values, no
personal data, ``acceptance: null`` (acceptance is the independent J-6r review,
and the controller owns /Users/Dev/kalayantra/run/J6R_REHEARSAL.json).
The seals are synthetic admission metadata over the real 527/1236/1379/1382 SQL
(see tests/l3/gochara/test_j6r_rehearsal_db.py); the legacy reader is the
deterministic stored-rows transport fixture. Both are named in the evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import uuid
from pathlib import Path

import psycopg
from psycopg.conninfo import make_conninfo

from scripts.kala_gochara_cutover import j6r_rehearsal as rehearsal
from tests.l3.gochara._disposable_db_guard import guarded_admin_connect
from tests.l3.gochara.test_a53_inventory import CHART_ID, _populate_am5_database
from tests.l3.gochara.test_j6r_rehearsal_db import ROOT, MIGRATIONS, _legacy, seed_rehearsal_lane

DEFAULT_ADMIN_DSN = 'postgresql://postgres@127.0.0.1:55433/postgres'
SQL_USED = ('platform/supabase/migrations/527_kala_gochara_generation_authority.sql',
            'platform/migrations/1236_gochara_authority_refuses_governed_generation.sql',
            'platform/migrations/1379_gochara_sealed_authority.sql',
            'platform/migrations/1382_gochara_authority_no_truncate.sql')


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(admin_dsn: str) -> dict:
    admin = guarded_admin_connect(admin_dsn, autocommit=True, connect_timeout=5)
    name = f'ky_j6r_{uuid.uuid4().hex[:8]}'
    created = dropped = False
    evidence: dict = {}
    try:
        admin.execute(f'CREATE DATABASE "{name}"')
        created = True
        dsn = make_conninfo(admin_dsn, dbname=name)
        with psycopg.connect(dsn, autocommit=True, connect_timeout=5) as conn:
            _populate_am5_database(conn)
            manifests = seed_rehearsal_lane(conn)
            server = conn.execute('SHOW server_version').fetchone()[0]
        evidence = rehearsal.rehearse_committed(
            dsn, chart_id=CHART_ID, expected_previous='3.0', generation='5.0', manifest_id=manifests['5.0'],
            legacy_reader=_legacy, request={'event_classes': ['marriage']})
        with psycopg.connect(dsn, autocommit=True, connect_timeout=5) as conn:
            second = rehearsal.rehearse(conn, chart_id=CHART_ID, expected_previous='3.0', generation='5.0',
                                        manifest_id=manifests['5.0'], legacy_reader=_legacy,
                                        request={'event_classes': ['marriage']})
        evidence = {
            'schema': 'ky.j6r_lane_run/1', 'item': 'J-6r', 'acceptance': None, 'production_activated': False,
            'lane': {'database': name, 'server_version': server, 'created': True},
            'inputs': {'seals': 'synthetic admission metadata (not computation, not verification)',
                       'legacy_reader': 'stored-rows transport fixture',
                       'sql_sha256': {p: _sha(ROOT / p) for p in SQL_USED},
                       'rehearsal_module_sha256': _sha(Path(rehearsal.__file__))},
            'committed_rehearsal': evidence,
            'transactional_rehearsal': {k: second[k] for k in ('schema', 'rollback_bytes_equal', 'retained_rows_equal')}
                                       | {'before_sha256': second['before']['sha256'],
                                          'after_sha256': second['after']['sha256']},
            'bytes_equal_across_rehearsals': evidence['before']['sha256'] == second['before']['sha256'],
        }
    finally:
        if created:
            assert name.startswith('ky_j6r_'), name        # never drop what this run did not create
            admin.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
            dropped = admin.execute('SELECT count(*) FROM pg_database WHERE datname=%s', (name,)).fetchone()[0] == 0
        admin.close()
    if evidence:
        evidence['lane']['dropped_and_absent'] = dropped
    return evidence


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        evidence = run(os.environ.get('GOCHARA_A53_ADMIN_DSN', DEFAULT_ADMIN_DSN))
    except rehearsal.RehearsalRefused as exc:
        print(json.dumps({'status': 'REFUSED', 'reason': str(exc)}))
        return 2
    args.out.write_text(json.dumps(evidence, indent=1, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({'status': 'REHEARSED', 'out': str(args.out), 'dropped': evidence['lane']['dropped_and_absent']}))
    return 0 if evidence['lane']['dropped_and_absent'] else 1


if __name__ == '__main__':
    sys.exit(main())
