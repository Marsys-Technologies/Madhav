"""Disabled K9-23 whole-layer operations over the existing manifest protocol.

Independent digest derivation belongs to the separately dispatched verifier.
These operations enforce complete input coverage; they invent no semantic PASS.
"""
from __future__ import annotations
import argparse
import json
import os
from typing import Any
from uuid import UUID

import psycopg
from services.kala_core.manifest import Candidate, CandidateNotPublishable, lock_candidate_inputs, publish_candidate, rollback_head
from services.kala_core.verify import verify_candidate, VerificationRefused

CANONICAL_CHART = '482012f1-710e-4a25-994a-93821f5871aa'


def _run(conn: Any, run_id: str) -> dict:
    from pipeline.orchestrator.runner import validate_frozen_run_manifest
    fields = ('id','chart_id','scope','scope_target','action','plan','state','plan_manifest','plan_manifest_digest')
    row = conn.execute('SELECT '+', '.join(fields)+' FROM build_runs WHERE id = %s',(run_id,)).fetchone()
    if row is None:
        raise ValueError('candidate build run is absent')
    run = dict(zip(fields,row))
    frozen = validate_frozen_run_manifest(run)
    if run['action'] != 'rebuild' or not frozen.plan or any(not a.startswith('ka_') for a in frozen.plan):
        raise ValueError('only an explicit Kāla rebuild plan is permitted')
    if 'ka_bhavishya_lekha' in frozen.plan:
        raise ValueError('issued forecasts are outside the replaceable rebuild set')
    return run


def _candidate(conn: Any, run_id: str, generation: str) -> tuple[Candidate, dict]:
    query = ('SELECT chart_id, build_id, expected_head_generation, state, conventions '
             'FROM kala_layer_candidate WHERE build_id = %s AND generation = %s')
    row = conn.execute(query,(run_id,generation)).fetchone()
    if row is None:
        raise CandidateNotPublishable('candidate is absent or bound to another run')
    c = Candidate(str(row[0]),generation,str(row[1]),row[2])
    lock_candidate_inputs(conn,c)
    row = conn.execute(query,(run_id,generation)).fetchone()
    if row is None or row[3] != 'building':
        raise CandidateNotPublishable('candidate must still be building')
    c = Candidate(str(row[0]),generation,str(row[1]),row[2])
    run = _run(conn,run_id)
    if str(run['chart_id']) != c.chart_id or run['state'] != 'completed':
        raise CandidateNotPublishable('candidate requires its completed build run')
    # (I) INTERPRETATION: K9-1 pins all expected grains at candidate-open.
    # Inferring this inventory from observed rows hides work that never ran.
    plan = row[4].get('publication_grains') if isinstance(row[4],dict) else None
    if not isinstance(plan,dict) or set(plan) != set(run['plan']):
        raise CandidateNotPublishable('candidate grain plan must cover every build writer exactly')
    grains = []
    for writer,keys in plan.items():
        if not isinstance(keys,list) or not keys:
            raise CandidateNotPublishable('every writer needs explicit grains')
        for key in keys:
            if not isinstance(key,str) or not (key == writer or key.startswith(writer+':')):
                raise CandidateNotPublishable('grain key must identify its writer')
            grains.append(key)
    if len(grains) != len(set(grains)):
        raise CandidateNotPublishable('grain plan contains duplicates')
    rows = conn.execute('SELECT grain_key, result_state FROM kala_layer_candidate_grain '
                        'WHERE chart_id = %s AND generation = %s',(c.chart_id,generation)).fetchall()
    if set(grains) != {r[0] for r in rows} or any(r[1] not in {'rows','zero_rows'} for r in rows):
        raise CandidateNotPublishable('candidate has absent, unplanned or failed grains')
    return c, {'run':run,'grains':tuple(sorted(grains))}


def verify(conn: Any, *, run_id: str, generation: str, independently_derived_digest: str) -> dict:
    """Bind an externally re-derived digest after checking every planned grain."""
    if conn.execute('SELECT current_user').fetchone()[0] != 'verifier_principal':
        raise VerificationRefused('verification must run as verifier_principal')
    if len(independently_derived_digest) != 64 or any(c not in '0123456789abcdef' for c in independently_derived_digest):
        raise VerificationRefused('independent digest must be SHA-256')
    c, detail = _candidate(conn,run_id,generation)
    verify_candidate(conn,c,independently_derived_digest=independently_derived_digest)
    return {'status':'INPUT_VERIFICATION_RECORDED','generation':generation,
            'verified_grains':list(detail['grains']),'semantic_verification':None}


def publish(conn: Any, *, run_id: str, generation: str, expected_head: str | None) -> dict:
    c, detail = _candidate(conn,run_id,generation)
    if expected_head != c.expected_head_generation:
        raise CandidateNotPublishable('request expected-head differs from candidate-open pin')
    publish_candidate(conn,c,expected_grains=detail['grains'])
    return {'status':'PUBLISHED','generation':generation,'previous_head':expected_head}


def rollback(conn: Any, *, generation: str, expected_head: str, chart_id: str = CANONICAL_CHART) -> dict:
    current = conn.execute(
        "SELECT expected_head_generation FROM kala_layer_candidate "
        "WHERE chart_id = %s AND generation = %s AND state = 'published'",
        (chart_id, expected_head),
    ).fetchone()
    if current is None or current[0] != generation:
        raise CandidateNotPublishable('rollback must restore the retained previous head')
    rollback_head(conn,chart_id=chart_id,retained_generation=generation,expected_head_generation=expected_head)
    return {'status':'ROLLED_BACK','generation':generation,'previous_head':expected_head}


def inspect_rebuild(conn: Any, *, run_id: str, assets: str) -> dict:
    run = _run(conn,run_id)
    if assets.split(',') != run['plan']:
        raise ValueError('assets must exactly match the frozen ordered plan')
    return {'status':'PLAN_ONLY','run_id':run_id,'chart_id':str(run['chart_id']),
            'planned_assets':run['plan'],'executed_assets':[],'dry_run_passed':None}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='operation',required=True)
    for operation in ('verify','publish','rollback','rebuild-dryrun','rebuild'):
        p = sub.add_parser(operation)
        if operation != 'rollback': p.add_argument('--run-id',required=True,type=UUID)
        if operation.startswith('rebuild'): p.add_argument('--assets',required=True)
        else: p.add_argument('--generation',required=True)
        if operation in ('publish','rollback'): p.add_argument('--expected-head',required=True)
        if operation == 'verify': p.add_argument('--independently-derived-digest',required=True)
    args = parser.parse_args(argv)
    dsn = os.environ.get('DATABASE_URL')
    if not dsn:
        print(json.dumps({'status':'REFUSED','reason':'operation-specific DATABASE_URL is required'}))
        return 2
    try:
        with psycopg.connect(dsn,connect_timeout=5) as conn:
            if args.operation == 'rebuild-dryrun': conn.read_only = True
            if args.operation.startswith('rebuild'):
                result = inspect_rebuild(conn,run_id=str(args.run_id),assets=args.assets)
                if result['chart_id'] != CANONICAL_CHART:
                    raise ValueError('executor operation is canonical-chart scoped')
                if args.operation == 'rebuild':
                    from pipeline.orchestrator.runner import execute_run
                    conn.rollback()
                    execute_run(str(args.run_id))
                    state = conn.execute('SELECT state FROM build_runs WHERE id = %s',(str(args.run_id),)).fetchone()
                    if state is None or state[0] != 'completed':
                        raise ValueError('orchestrator did not complete the build')
                    result = {'status':'BUILD_COMPLETED','run_id':str(args.run_id)}
            elif args.operation == 'rollback':
                result = rollback(conn,generation=args.generation,expected_head=args.expected_head)
            else:
                row = conn.execute('SELECT chart_id FROM kala_layer_candidate WHERE build_id=%s AND generation=%s',
                                   (str(args.run_id),args.generation)).fetchone()
                if row is None or str(row[0]) != CANONICAL_CHART:
                    raise ValueError('candidate is absent or outside canonical chart')
                if args.operation == 'verify':
                    result = verify(conn,run_id=str(args.run_id),generation=args.generation,
                                    independently_derived_digest=args.independently_derived_digest)
                else:
                    result = publish(conn,run_id=str(args.run_id),generation=args.generation,
                                     expected_head=None if args.expected_head == 'NONE' else args.expected_head)
        print(json.dumps(result,sort_keys=True))
        return 0
    except ValueError as exc:
        print(json.dumps({'status':'REFUSED','reason':str(exc)}))
        return 2
    except psycopg.Error:
        # Connection diagnostics may contain secrets: do not echo libpq errors.
        print(json.dumps({'status':'REFUSED','reason':'database operation failed; transaction rolled back'}))
        return 3


if __name__ == '__main__':
    raise SystemExit(main())
