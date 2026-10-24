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


def _grain_refusal(absent: list[str], unplanned: list[str], failed: list[str]) -> str:
    """The refusal text for a candidate whose grains do not match its plan: it names the writers lacking a grain and the keys."""
    lacking = sorted({key.split(':',1)[0] for key in absent + failed})
    parts = ['writers lacking a grain: '+', '.join(lacking)] if lacking else []
    parts += [f'{label} grains: '+', '.join(keys) for label,keys in (('absent',absent),('unplanned',unplanned),('failed',failed)) if keys]
    return 'candidate has absent, unplanned or failed grains; '+'; '.join(parts)


def _candidate(conn: Any, run_id: str, generation: str, *, enforce_zero_rows: bool = False) -> tuple[Candidate, dict]:
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
    observed = {r[0] for r in rows}
    absent = sorted(set(grains) - observed)
    unplanned = sorted(observed - set(grains))
    failed = sorted(r[0] for r in rows if r[1] not in {'rows','zero_rows'})
    if absent or unplanned or failed:
        raise CandidateNotPublishable(_grain_refusal(absent,unplanned,failed))
    # The zero-row detector reads the layer tables and the registry, which the narrow `verifier_principal` role may not (migration 1330 grants it the grain,
    # verification and nothing else; verification only binds a digest). It therefore runs where the serving change is made: `publish`.
    unlabelled = _unexplained_zero_rows(conn,c.chart_id,generation,[r[0] for r in rows if r[1] == 'zero_rows']) if enforce_zero_rows else []
    if unlabelled:
        raise CandidateNotPublishable('zero-row completion without a measured vacuous reason and a passing integrity check: '+'; '.join(unlabelled))
    return c, {'run':run,'grains':tuple(sorted(grains))}


# SR-K9-ADMITTED-ZERO (compensating detector, CLAUDE.md N.8): ka_sangam and ka_vighnakara declare target_floor = 0 (migration 1409), the in-contract
# statement that a writer may correctly produce 0 rows (asset_runner.py "target_floor=0 ... explicit declaration"). That makes the orchestrator's own
# "0 rows = silent failure" signal (state 'dormant') unavailable for them, and the frozen DEP-ASSERT cannot be taught otherwise, so THIS gate (outside the frozen
# path) is the detector: a zero-row grain of these writers publishes only when (1) the emptiness is explained by a named reason that THIS gate re-measures from
# the candidate's own rows (the writers' vacuous=true label, read from rows because WriterResult.notes and the run log are not persisted: FROZEN contract),
# and (2) the asset's registered integrity_check_sql passes now. A measured non-vacuous emptiness (upstream holds windows, the writer wrote none) refuses.
VACUOUS_ZERO_WRITERS = ('ka_sangam', 'ka_vighnakara')


def _scalar(conn: Any, sql: str, params: tuple) -> int:
    return int(conn.execute(sql, params).fetchone()[0] or 0)


def _vacuous_reason(conn: Any, writer: str, chart_id: str, generation: str) -> str | None:
    """The named reason the candidate's zero rows are vacuous, MEASURED from its own rows; None when the emptiness is not explained (the label cannot be true)."""
    windows = _scalar(conn, 'SELECT count(*) FROM kala_convergence WHERE chart_id = %s AND generation = %s', (chart_id, generation))
    if writer == 'ka_vighnakara':     # its upstream is the candidate's peak-dated convergence windows (writers/ka_vighnakara.py run)
        peak = _scalar(conn, 'SELECT count(*) FROM kala_convergence WHERE chart_id = %s AND generation = %s AND peak_date IS NOT NULL', (chart_id, generation))
        return 'empty_upstream_convergence' if peak == 0 else None
    if windows:                       # ka_sangam wrote windows, so its grain cannot honestly read zero_rows
        return None
    # the admitted-predicate filter is the writer's own (writers/ka_sangam.py plan_substeps, candidate branch)
    admitted, unresolved = (int(v or 0) for v in conn.execute(
        'SELECT count(*), count(*) FILTER (WHERE p.signal_id IS NULL) FROM kala_activation_predicates p '
        "WHERE p.chart_id = %s AND p.generation = %s AND p.mechanism_route = 'admitted' "
        "AND p.conclusion_state_jsonb->>'effective_state' = 'in_force' AND p.conclusion_state_jsonb->>'scored' = 'true'",
        (chart_id, generation)).fetchone())
    if admitted == 0:
        return 'no_admitted_predicates'
    # SR-SANGAM-SIGNAL-UNRESOLVED sanctions exactly two honest nulls: nothing admitted, and every admitted predicate signal-less (no window can be attributed).
    # Admitted predicates that DO carry a signal and still wrote 0 windows are the silent failure floor 0 stopped the orchestrator detecting: refuse (N.8).
    return 'all_admitted_signal_unresolved' if unresolved == admitted else None


def _unexplained_zero_rows(conn: Any, chart_id: str, generation: str, zero_grains: list[str]) -> list[str]:
    """One refusal line per zero-row grain of ka_sangam / ka_vighnakara lacking a measured vacuous reason or a passing integrity check; [] when none."""
    problems = []
    for key in sorted(zero_grains):
        writer = key.split(':', 1)[0]
        if writer not in VACUOUS_ZERO_WRITERS:
            continue
        reason = _vacuous_reason(conn, writer, chart_id, generation)
        if reason is None:
            problems.append(f'{key}: zero rows but the candidate holds the input the writer should have turned into rows (not vacuous)')
            continue
        row = conn.execute('SELECT integrity_check_sql FROM asset_registry WHERE asset_id = %s', (writer,)).fetchone()
        if row is None or not row[0]:
            problems.append(f'{key}: vacuous ({reason}) but {writer} has no integrity_check_sql to confirm it')
            continue
        try:
            with conn.transaction():      # a savepoint: a SQL error must not abort the caller's transaction, or the next grain's reads would lose their named reason
                verdict = conn.execute(row[0]).fetchone()
        except psycopg.Error as exc:
            problems.append(f'{key}: vacuous ({reason}) but integrity_check_sql errored: {type(exc).__name__}')
            continue
        if not verdict or not verdict[0]:
            problems.append(f'{key}: vacuous ({reason}) but integrity_check_sql did not pass')
    return problems


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
    c, detail = _candidate(conn,run_id,generation,enforce_zero_rows=True)
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
    # K9-23 CI: plan inspection runs no dry-run detector; §N.8 requires null.
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
