#!/usr/bin/env python3
"""K9-4b inert request preparation; no execution or acceptance receipt.

The executor's request digest binds the exact SQL bytes through sql-sha256.
The read-only child verifies those bytes before connecting. Neither a marker
nor child exit zero is operational acceptance; PARĪKṢAKA judges the readback.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
from uuid import UUID


def request_digest(request: dict) -> str:
    bound = {key:value for key,value in request.items() if key != 'acceptance_receipt'}
    return hashlib.sha256(json.dumps(bound,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def prepare_readback(request: dict, *, readback_sql: str) -> dict:
    """Prepare a single-column JSONB readback and bind its bytes to the request."""
    if request.get('item_id') != 'K9-4b' or request.get('kind') != 'readback_sql':
        raise ValueError('only K9-4b readback_sql request preparation is permitted')
    for key in ('operation_id',):
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:-]*',request.get(key,'')):
            raise ValueError('executor operation identity is required')
    if not re.fullmatch(r'[0-9a-f]{40}', request.get('reviewed_commit','')):
        raise ValueError('reviewed source commit is required')
    args = request.get('args')
    if not isinstance(args,dict) or not re.fullmatch(r'run/ops/sql/[A-Za-z0-9_.-]+\.sql',args.get('sql_file','')):
        raise ValueError('readback SQL must have a fixed executor SQL path')
    query = readback_sql.strip()
    if (not re.match(r'SELECT\b',query,re.I) or any(token in query for token in (';','\\','--','/*','*/'))):
        raise ValueError('readback must be one un-commented SELECT without a terminator')
    wrapped = 'SELECT evidence::text AS evidence FROM (' + query + ') AS t'
    prepared = deepcopy(request)
    prepared['args']['sql-sha256'] = hashlib.sha256(wrapped.encode()).hexdigest()
    return dict(schema='kala.readback_preparation/1', request=prepared,
                request_sha256=request_digest(prepared), sql=wrapped,
                operational_acceptance=None)


def _identities(run_id: str, generation: str):
    UUID(run_id)
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,119}',generation) or generation in {'NONE','current'}:
        raise ValueError('explicit candidate generation required')


def writer_readback_sql(run_id: str, generation: str) -> str:
    """Read the recorded run, frozen source plan, complete grain vector and receipt.

    Zero rows stay visible; no row count, input hash or boolean is acceptance.
    The independent reviewer checks each writer's semantic receipt and lineage.
    """
    _identities(run_id,generation)
    return f"""SELECT jsonb_build_object(
        'run', (SELECT to_jsonb(r) FROM build_runs r WHERE r.id='{run_id}'::uuid),
        'candidate', (SELECT to_jsonb(c) FROM kala_layer_candidate c WHERE c.build_id='{run_id}'::uuid AND c.generation='{generation}'),
        'grains', (SELECT jsonb_agg(to_jsonb(g) ORDER BY g.grain_key) FROM kala_layer_candidate_grain g JOIN kala_layer_candidate c USING(chart_id,generation) WHERE c.build_id='{run_id}'::uuid AND c.generation='{generation}'),
        'writers', (SELECT jsonb_agg(to_jsonb(a) ORDER BY a.position, a.asset_id) FROM build_run_assets a WHERE a.run_id='{run_id}'::uuid),
        'lineage', (SELECT jsonb_agg(to_jsonb(p) ORDER BY p.asset_id, p.partition_key) FROM asset_provenance_receipts p WHERE p.build_id='{run_id}'::uuid),
        'verification', (SELECT to_jsonb(v) FROM kala_layer_verification v JOIN kala_layer_candidate c USING(chart_id,generation) WHERE c.build_id='{run_id}'::uuid AND c.generation='{generation}')
    ) AS evidence"""


def publication_readback_sql(run_id: str, generation: str) -> str:
    _identities(run_id,generation)
    # Head is resolved via this recorded run's chart, never ambient "current".
    return writer_readback_sql(run_id,generation).replace(
        "SELECT jsonb_build_object(", f"""SELECT jsonb_build_object(
        'head', (SELECT to_jsonb(h) FROM kala_layer_head h JOIN build_runs r ON r.chart_id=h.chart_id WHERE r.id='{run_id}'::uuid),""",1)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__,allow_abbrev=False)
    parser.add_argument('--request',required=True,type=Path)
    parser.add_argument('--run-id',required=True)
    parser.add_argument('--generation',required=True)
    parser.add_argument('--stage',required=True,choices=['per-writer','publication'])
    args=parser.parse_args(argv)
    query=(writer_readback_sql if args.stage=='per-writer' else publication_readback_sql)(args.run_id,args.generation)
    result=prepare_readback(json.loads(args.request.read_text()),readback_sql=query)
    print(json.dumps(result,sort_keys=True))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
