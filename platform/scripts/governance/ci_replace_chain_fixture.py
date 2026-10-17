#!/usr/bin/env python3
"""Prepare real per-body sky substrate once in parallel, then restore it in tests.

Only the existing guarded A5.3 fixture creates/drops databases. No production DSN,
SQL substitute, shortened domain, or ephemeris download is used by this helper.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
TABLES = ('ka_gochara_physical_object', 'ka_gochara_sky_event')
SCHEMA = 'ci.replace_chain_substrate/1'


def source_digest(root=ROOT):
    paths = set((root / 'platform/python-sidecar').rglob('*.py'))
    paths.update((root / 'platform/migrations').glob('*.sql'))
    paths.add(root / 'platform/scripts/governance/ci_replace_chain_fixture.py')
    digest = hashlib.sha256()
    for path in sorted(paths):
        if '__pycache__' in path.parts:
            continue
        digest.update(path.relative_to(root).as_posix().encode() + b'\0')
        digest.update(path.read_bytes())
        digest.update(b'\0')
    return digest.hexdigest()


def manifest_files(directory, *, source, bodies, ephe):
    """Verify the complete artifact set before any database write."""
    documents = []
    for path in sorted(directory.glob('*/manifest.json')):
        doc = json.loads(path.read_text())
        if doc.get('schema') != SCHEMA or doc.get('source_digest') != source or doc.get('ephe_sha256') != ephe:
            raise ValueError(f'stale or unbound substrate artifact: {path}')
        if set(doc.get('tables', {})) != set(TABLES):
            raise ValueError(f'incomplete substrate tables: {path}')
        for table in TABLES:
            data = path.parent / (table + '.copy')
            if data.is_symlink() or hashlib.sha256(data.read_bytes()).hexdigest() != doc['tables'][table]['sha256']:
                raise ValueError(f'substrate bytes mismatch: {data}')
            if not isinstance(doc['tables'][table]['rows'], int) or doc['tables'][table]['rows'] <= 0:
                raise ValueError(f'empty substrate table: {data}')
        documents.append((path.parent, doc))
    if sorted(doc['body'] for _, doc in documents) != sorted(bodies):
        raise ValueError('substrate artifacts must cover every body exactly once')
    return documents


def load(conn, directory):
    from services.gochara_kernel.substrate import SUBSTRATE_BODIES
    from tests.l3.gochara.conftest import ACTUAL_CHECKSUMS, _PROBLEMS
    if _PROBLEMS:
        raise ValueError('pinned ephemeris is unavailable')
    documents = manifest_files(Path(directory), source=source_digest(),
                               bodies=SUBSTRATE_BODIES, ephe=ACTUAL_CHECKSUMS)
    with conn.transaction():
        for table in TABLES:
            if conn.execute(f'SELECT count(*) FROM public.{table}').fetchone()[0]:
                raise ValueError(f'refusing substrate restore into nonempty {table}')
            for parent, doc in documents:
                with (parent / (table + '.copy')).open('rb') as data:
                    with conn.cursor().copy(f'COPY public.{table} FROM STDIN') as copy:
                        while chunk := data.read(1024 * 1024):
                            copy.write(chunk)
                actual = conn.execute(f'SELECT count(*) FROM public.{table} WHERE body = %s',
                                      (doc['body'].lower(),)).fetchone()[0]
                if actual != doc['tables'][table]['rows']:
                    raise ValueError(f'substrate row count mismatch: {doc["body"]} {table}')


def build(output, body):
    from pipeline.orchestrator.writers import ContextSpec, SubStep
    from pipeline.orchestrator.writers import ka_gochara_v5 as writer
    from services.gochara_kernel.substrate import SUBSTRATE_BODIES
    from tests.l3.gochara.conftest import ACTUAL_CHECKSUMS, EPHE_PATH, _PROBLEMS, assert_real_ephemeris
    from tests.l3.gochara.test_a53_inventory import CHART_ID, H0, H1, create_am5_database, drop_am5_database
    import psycopg
    if body not in SUBSTRATE_BODIES or _PROBLEMS:
        raise ValueError('unknown body or unavailable pinned ephemeris')
    assert_real_ephemeris()
    started = time.monotonic()
    admin, name, dsn = create_am5_database('a55prep')
    target = output
    target.mkdir(parents=True, exist_ok=True)
    try:
        with psycopg.connect(dsn, autocommit=True, connect_timeout=3) as conn:
            ctx = ContextSpec(asset_id=writer.ASSET_ID, build_id='ci-substrate', db_conn=conn,
                              dry_run=False, config={'chart_id': CHART_ID, 'horizon': (H0, H1), 'ephe_path': EPHE_PATH})
            w = writer.GocharaV5Writer()
            for key in (writer.CONVENTION_SUBSTEP, writer.BODY_SUBSTEP_PREFIX + body):
                with conn.transaction():
                    w.run_substep(ctx, SubStep(key=key, label=key))
            tables = {}
            for table in TABLES:
                path = target / (table + '.copy')
                with path.open('wb') as data:
                    with conn.cursor().copy(f'COPY public.{table} TO STDOUT') as copy:
                        for chunk in copy:
                            data.write(chunk)
                tables[table] = {'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                                 'rows': conn.execute(f'SELECT count(*) FROM public.{table}').fetchone()[0]}
        doc = {'schema': SCHEMA, 'body': body, 'source_digest': source_digest(),
               'ephe_sha256': ACTUAL_CHECKSUMS, 'tables': tables, 'elapsed_seconds': time.monotonic() - started}
        (target / 'manifest.json').write_text(json.dumps(doc, indent=2) + '\n')
        print(json.dumps({'body': body, 'elapsed_seconds': doc['elapsed_seconds'], 'tables': tables}), flush=True)
    finally:
        drop_am5_database(admin, name)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--body', required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    sys.path.insert(0, str(ROOT / 'platform/python-sidecar'))
    build(args.output, args.body)


if __name__ == '__main__':
    main()
