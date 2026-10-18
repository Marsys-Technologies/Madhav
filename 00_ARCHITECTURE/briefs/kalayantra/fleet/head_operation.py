#!/usr/bin/env python3
"""Disabled J6 authority adapters and evidence contracts (A6 D-40).

No publication/seal/content DML, implicit legacy fallback, enablement or dispatch.
The CLI is executor-only: admission uses G8 and the reviewed policy before the
child receives one connection. A dry run performs the same CAS and rolls back.
A commit is AWAITING_READBACK, never acceptance. Importing this file has no I/O.

(I) INTERPRETATION: G6 checklist names below bind independent attestations to the
complete request. They do not compute seal verification, a deployed-reader probe,
backup, restore or an owner decision. Those remain the independent lane's work.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sys
import uuid

CANONICAL_CHART = '482012f1-710e-4a25-994a-93821f5871aa'
KINDS = ('publish_head', 'rollback_head', 'publish_head_dryrun', 'rollback_head_dryrun')
G6_ROWS = ('exact_generation_manifest_sealed', 'every_included_grain_verified',
           'evaluation_recorded_no_open_engineering_defect', 'authority_constraint_deployed',
           'reader_deployed_sealed_only_no_test_slice', 'reader_horizon_and_rollback_probed',
           'rollback_rehearsal_accepted', 'previous_head_retained',
           'deployed_image_and_migrations_identified', 'D-FLIP_approved')
ROLLBACK_ROWS = ('retained_head_bound_to_publish_receipt', 'rollback_rehearsal_accepted',
                 'deployed_image_and_migrations_identified')
HEAD_KEYS = {'generation', 'flipped_at', 'flipped_by', 'evidence_ref'}
RETAINED_TABLES = ('kala_gochara_publication', 'ka_gochara_generation_seal', 'kala_gochara_windows',
                   'kala_gochara_coverage', 'ka_gochara_eval_window', 'ka_gochara_eval_window_record',
                   'ka_gochara_relationship_record', 'ka_gochara_contact', 'ka_gochara_search_inventory')
HEX64 = re.compile(r'[0-9a-f]{64}\Z')
SAFE_ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,79}\Z')


class Refused(ValueError):
    """A failed pre/postcondition; messages contain no connection information."""


def raw_sha(raw):
    return hashlib.sha256(raw).hexdigest()


def wire(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def sha(value):
    return raw_sha(wire(value))


def request_digest(req):
    # Mirrors executor.request_digest (A8 §3.9): the fields that may lawfully change after signing are not bound.
    return sha({k:v for k,v in req.items() if k not in ('acceptance_receipt','expires_at') and not k.endswith('_expires_at')})


def _unique(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise Refused('duplicate_json_key')
        out[key] = value
    return out


def load_json(raw):
    return json.loads(raw, object_pairs_hook=_unique)


def _time(value):
    value = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    if value.tzinfo is None:
        raise Refused('timezone_required')
    return value.astimezone(dt.timezone.utc).isoformat()


def _head(value):
    if not isinstance(value, dict) or set(value) != HEAD_KEYS:
        raise Refused('full_previous_head_required')
    if not isinstance(value['generation'], str) or not re.fullmatch(r'(?:v1|[1-9][0-9]*\.[0-9]+)', value['generation']):
        raise Refused('invalid_generation')
    if value['flipped_at'] is not None and _time(value['flipped_at']) != value['flipped_at']:
        raise Refused('canonical_utc_head_required')
    if any(value[k] is not None and (not isinstance(value[k], str) or not value[k]) for k in ('flipped_by','evidence_ref')):
        raise Refused('invalid_head_audit')
    return value


def governed(gen):
    return bool(re.fullmatch(r'([5-9]|[1-9][0-9]+)\.[0-9]+', gen))


def shape(req):
    kind = req['kind']
    if kind not in KINDS or req.get('chart_id') != CANONICAL_CHART:
        raise Refused('kind_or_canonical_chart_mismatch')
    if not SAFE_ID.fullmatch(req.get('operation_id', '')) or not re.fullmatch(r'[0-9a-f]{40}',req.get('reviewed_commit','')):
        raise Refused('operation_and_full_reviewed_commit_required')
    scope = req['head_change']
    restore = kind.startswith('rollback_')
    if set(scope) != {'expected_head','target','change_at'} | ({'restore_head'} if restore else set()):
        raise Refused('exact_head_change_scope_required')
    _head(scope['expected_head']); _time(scope['change_at'])
    target = scope['target']
    if set(target) != {'generation','manifest_id'}:
        raise Refused('exact_target_required')
    gen = target['generation']
    if not re.fullmatch(r'(?:v1|[1-9][0-9]*\.[0-9]+)', gen):
        raise Refused('invalid_generation')
    if target['manifest_id'] is not None:
        if str(uuid.UUID(target['manifest_id'])) != target['manifest_id']:
            raise Refused('canonical_manifest_uuid_required')
    if governed(gen) and target['manifest_id'] is None:
        raise Refused('exact_manifest_required')
    if not restore and not governed(gen):
        raise Refused('published_governed_target_required')
    if scope['expected_head']['generation'] == gen:
        raise Refused('head_change_cannot_be_noop')
    if restore and _head(scope['restore_head'])['generation'] != gen:
        raise Refused('retained_generation_mismatch')
    args = {'generation':gen, 'manifest-id':target['manifest_id'] or 'none',
            'expected-head-sha256':sha(scope['expected_head'])}
    if req.get('args') != args:
        raise Refused('args_do_not_bind_exact_head_change')
    return scope


def flip_decision(events):
    """Read the last controller event, as tracker.state.decision_status does.

    Refused is a final residual outcome but never authorizes publish; deferred
    and insufficient_evidence stay open. No event is written or default applied.
    """
    matching = [e for e in events if e.get('kind') == 'decision' and e.get('decision') == 'D-FLIP']
    event = matching[-1] if matching else None
    effective = bool(event and event.get('state') in ('decided','delegated')
                     and event.get('actor') in ('native','steward') and event.get('detail')
                     and event.get('outcome') in ('approved','refused'))
    return dict(effective=effective, outcome=event.get('outcome') if event else None,
                event_sha256=sha(event) if event else None,
                flip_authorized=effective and event['outcome'] == 'approved')


def _bound_file(ref, ops):
    if not isinstance(ref,dict) or set(ref) != {'path','sha256'} or not HEX64.fullmatch(ref.get('sha256','')):
        raise Refused('hash_bound_receipt_required')
    path = Path(ref['path']).resolve(strict=True)
    if not path.is_relative_to((Path(ops)/'receipts').resolve(strict=True)):
        raise Refused('receipt_outside_executor_receipts')
    raw = path.read_bytes()
    if raw_sha(raw) != ref['sha256']:
        raise Refused('receipt_digest_mismatch')
    return load_json(raw)


def request_problem(req, ops):
    """Additional policy after the executor's G8 checks; same reviewed source."""
    if req.get('kind') not in KINDS:
        return None
    try:
        scope = shape(req)
        publish = req['kind'].startswith('publish_')
        if req.get('item_id') != ('J-6' if publish else 'J-6r'):
            raise Refused('head_item_identity_mismatch')
        if publish:
            if scope['target']['generation'] != '5.0':
                raise Refused('J-6_requires_5.0')
            events = [load_json(line) for line in (Path(ops).parent/'EVENTS.jsonl').read_text().splitlines() if line.strip()]
            d = flip_decision(events)
            if not d['flip_authorized'] or req.get('decision_event_sha256') != d['event_sha256']:
                raise Refused('D-FLIP_latest_effective_approved_event_required')
        else:
            original = _bound_file(req.get('rollback_of'), ops)
            proof = original.get('head_change') or {}
            if (original.get('kind') != 'publish_head' or original.get('item_id') != 'J-6'
                    or original.get('status') not in ('AWAITING_READBACK','COMPLETED')
                    or proof.get('schema') != 'ky.head_change/1' or proof.get('status') != 'COMMITTED_AWAITING_READBACK'
                    or proof.get('chart_id') != req['chart_id'] or proof.get('rollback_confirmed') is not False
                    or proof.get('retained_rows_equal') is not True
                    or proof.get('operation_id') != original.get('operation_id')
                    or proof.get('request_sha256') != original.get('request_sha256')
                    or scope['restore_head'] != proof.get('before') or scope['expected_head'] != proof.get('after')):
                raise Refused('rollback_requires_original_full_retained_head')
            fingerprints(proof)
        if not req['kind'].endswith('_dryrun'):
            if not req.get('dry_run_receipt'):
                raise Refused('dry-run_receipt_required')
            dry = _bound_file(req['dry_run_receipt'], ops)
            proof = dry.get('head_change') or {}
            if (dry.get('status') != 'COMPLETED' or dry.get('kind') != req['kind']+'_dryrun'
                    or dry.get('item_id') != req['item_id'] or dry.get('reviewed_commit') != req['reviewed_commit']
                    or proof.get('schema') != 'ky.head_change/1' or proof.get('status') != 'ROLLED_BACK'
                    or proof.get('rollback_confirmed') is not True or proof.get('retained_rows_equal') is not True
                    or proof.get('chart_id') != req['chart_id'] or proof.get('reviewed_commit') != req['reviewed_commit']
                    or proof.get('operation_id') != dry.get('operation_id')
                    or proof.get('request_sha256') != dry.get('request_sha256') or proof.get('head_change') != scope
                    or proof.get('before') != scope['expected_head']):
                raise Refused('dry-run_exact_scope_rollback_receipt_required')
            fingerprints(proof)
        return None
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        # Preserve only fixed refusal messages, never an exception containing a path/DSN.
        exc = sys.exc_info()[1]
        return str(exc) if isinstance(exc, Refused) else ('dry-run_receipt_missing_or_invalid' if not req['kind'].endswith('_dryrun') else 'head_policy_input_missing_or_invalid')


def replacement(req):
    scope = req['head_change']
    if req['kind'].startswith('rollback_'):
        return dict(scope['restore_head'])
    return dict(generation=scope['target']['generation'], flipped_at=_time(scope['change_at']),
                flipped_by='executor:'+req['operation_id'], evidence_ref='request-sha256:'+request_digest(req))


def read_head(conn, chart_id):
    row = conn.execute('SELECT authoritative_generation,flipped_at,flipped_by,evidence_ref'
                       ' FROM public.kala_gochara_authority WHERE chart_id=%s', (chart_id,)).fetchone()
    if row is None:
        raise Refused('previous_head_missing')
    return dict(generation=row[0], flipped_at=row[1].astimezone(dt.timezone.utc).isoformat() if row[1] else None,
                flipped_by=row[2], evidence_ref=row[3])


def retained(conn, chart_id):
    snapshot = {}
    for table in RETAINED_TABLES:  # fixed identifiers only
        rows = conn.execute(f'SELECT to_jsonb(t)::text FROM public.{table} t WHERE chart_id=%s'
                            ' ORDER BY to_jsonb(t)::text',(chart_id,)).fetchall()
        digest = hashlib.sha256()
        for (value,) in rows:
            raw = value.encode(); digest.update(len(raw).to_bytes(8,'big')); digest.update(raw)
        snapshot[table] = dict(rows=len(rows),sha256=digest.hexdigest())
    return snapshot


def _target(conn, req):
    target = req['head_change']['target']
    if not governed(target['generation']):
        return
    row = conn.execute(
        'SELECT p.manifest_id::text FROM public.kala_gochara_publication p'
        ' JOIN public.ka_gochara_generation_seal s ON s.chart_id=p.chart_id'
        ' AND s.generation=p.generation AND s.manifest_id=p.manifest_id'
        " WHERE p.chart_id=%s AND p.generation=%s AND p.manifest_id=%s::uuid AND p.status='published'"
        " AND coalesce(p.input_generation_vector->>'stored_scope','') <> 'test_slice'"
        " AND NOT (p.input_generation_vector ? 'test_slice')"
        ' AND public.ka_gochara_generation_is_sealed(p.chart_id,p.generation)',
        (req['chart_id'],target['generation'],target['manifest_id'])).fetchone()
    if row is None:
        raise Refused('target_not_published_exact_sealed_full_manifest')


def change_head(conn, req, *, dry_run):
    """Transaction owner for this standalone adapter, never a WriterBase writer.

    Execute requires an idle autocommit connection so the returned commit claim
    cannot describe an uncommitted caller savepoint. Dry run may use a savepoint.
    """
    shape(req)
    if dry_run is not req['kind'].endswith('_dryrun'):
        raise Refused('mode_request_mismatch')
    if not dry_run and (not conn.autocommit or conn.info.transaction_status != 0):
        raise Refused('execute_requires_idle_autocommit_connection')
    with conn.transaction(force_rollback=dry_run):
        conn.execute("SET LOCAL lock_timeout='10s'")
        conn.execute("SET LOCAL statement_timeout='10min'")
        conn.execute('SELECT public.ka_gochara_lock_chart(%s::uuid)',(req['chart_id'],))
        before = read_head(conn,req['chart_id'])
        if before != req['head_change']['expected_head']:
            raise Refused('full_head_compare_and_swap_conflict')
        _target(conn,req)
        old = retained(conn,req['chart_id'])
        after = replacement(req)
        row = conn.execute('UPDATE public.kala_gochara_authority SET authoritative_generation=%s,'
            'flipped_at=%s,flipped_by=%s,evidence_ref=%s WHERE chart_id=%s AND'
            ' (authoritative_generation,flipped_at,flipped_by,evidence_ref)'
            ' IS NOT DISTINCT FROM (%s,%s::timestamptz,%s,%s) RETURNING chart_id',
            (after['generation'],after['flipped_at'],after['flipped_by'],after['evidence_ref'],req['chart_id'],
             before['generation'],before['flipped_at'],before['flipped_by'],before['evidence_ref'])).fetchone()
        if row is None or read_head(conn,req['chart_id']) != after:
            raise Refused('full_head_compare_and_swap_conflict')
        new = retained(conn,req['chart_id'])
        if old != new:
            raise Refused('retained_rows_changed')
    if dry_run and read_head(conn,req['chart_id']) != before:
        raise Refused('dry_run_rollback_not_observed')
    return dict(schema='ky.head_change/1', status='ROLLED_BACK' if dry_run else 'COMMITTED_AWAITING_READBACK',
                rollback_confirmed=dry_run, operation_id=req['operation_id'], request_sha256=request_digest(req),
                chart_id=req['chart_id'], reviewed_commit=req['reviewed_commit'], head_change=req['head_change'],
                before=before, after=after, retained_rows_equal=True, retained_before=old, retained_after=new)


def fingerprints(proof):
    before, after = proof.get('retained_before'), proof.get('retained_after')
    if not isinstance(before,dict) or set(before) != set(RETAINED_TABLES) or before != after:
        raise Refused('measured_equal_retained_fingerprints_required')
    for reading in before.values():
        if (not isinstance(reading,dict) or set(reading) != {'rows','sha256'}
                or type(reading['rows']) is not int or reading['rows'] < 0
                or not isinstance(reading['sha256'],str) or not HEX64.fullmatch(reading['sha256'])):
            raise Refused('measured_equal_retained_fingerprints_required')


def child_proof(req, raw):
    proof = load_json(raw)
    dry = req['kind'].endswith('_dryrun')
    if (not isinstance(proof,dict) or proof.get('schema') != 'ky.head_change/1'
            or proof.get('operation_id') != req['operation_id'] or proof.get('request_sha256') != request_digest(req)
            or proof.get('chart_id') != req['chart_id'] or proof.get('reviewed_commit') != req['reviewed_commit']
            or proof.get('head_change') != req['head_change'] or proof.get('before') != req['head_change']['expected_head']
            or proof.get('after') != replacement(req) or proof.get('retained_rows_equal') is not True
            or proof.get('rollback_confirmed') is not dry
            or proof.get('status') != ('ROLLED_BACK' if dry else 'COMMITTED_AWAITING_READBACK')):
        raise Refused('bound_head_change_proof_required')
    fingerprints(proof)
    return proof


def expected_readback(req):
    return dict(schema='ky.head_readback/1', operation_id=req['operation_id'], request_sha256=request_digest(req),
                chart_id=req['chart_id'], target=req['head_change']['target'], head=replacement(req),
                target_matches=True, sealed=True if governed(req['head_change']['target']['generation']) else None)


def readback_sql(req):
    """One read-only SELECT for executor readback_sql, exact operation and manifest.

    Uses only shape-validated literals, with SQL quoting; no caller SQL accepted.
    This measures authority/admission, never claims the deployed consumer switched.
    """
    shape(req)
    quote = lambda value: "'"+str(value).replace("'","''")+"'"
    target = req['head_change']['target']; gen = quote(target['generation']); chart = quote(req['chart_id'])
    manifest = quote(target['manifest_id'])+'::uuid' if target['manifest_id'] else 'NULL::uuid'
    governed_target = governed(target['generation'])
    match = (f"p.manifest_id={manifest} AND p.status='published'"
             " AND coalesce(p.input_generation_vector->>'stored_scope','') <> 'test_slice'"
             " AND NOT (p.input_generation_vector ? 'test_slice')") if governed_target else 'true'
    sealed = 'public.ka_gochara_generation_is_sealed(a.chart_id,a.authoritative_generation)' if governed_target else 'NULL'
    return f"""SELECT jsonb_build_object(
 'schema','ky.head_readback/1','operation_id',{quote(req['operation_id'])},
 'request_sha256',{quote(request_digest(req))},'chart_id',a.chart_id::text,
 'target',jsonb_build_object('generation',{gen},'manifest_id',{manifest}),
 'head',jsonb_build_object('generation',a.authoritative_generation,'flipped_at',
   CASE WHEN a.flipped_at IS NULL THEN NULL ELSE
     to_char(a.flipped_at AT TIME ZONE 'UTC','YYYY-MM-DD\"T\"HH24:MI:SS.US') || '+00:00' END,
   'flipped_by',a.flipped_by,'evidence_ref',a.evidence_ref),
 'target_matches',a.authoritative_generation={gen} AND ({match}), 'sealed',{sealed}) AS head_readback
 FROM public.kala_gochara_authority a LEFT JOIN public.kala_gochara_publication p
 ON p.chart_id=a.chart_id AND p.generation=a.authoritative_generation
 WHERE a.chart_id={chart}::uuid;
"""


def _normalize_readback(value):
    value = dict(value); value['head'] = dict(value['head'])
    if value['head']['flipped_at'] is not None:
        value['head']['flipped_at'] = _time(value['head']['flipped_at'])
    return value


def observe(conn, req):
    row = conn.execute(readback_sql(req)).fetchall()
    if len(row) != 1:
        raise Refused('one_authority_readback_required')
    return _normalize_readback(row[0][0])


def decode_readback(raw):
    rows = list(csv.reader(io.StringIO(raw.decode()),delimiter='\t'))
    while rows and rows[-1] == []:  # execute() appends a newline before stderr
        rows.pop()
    if len(rows) != 2 or rows[0] != ['head_readback'] or len(rows[1]) != 1:
        raise Refused('one_executor_readback_row_required')
    return _normalize_readback(load_json(rows[1][0]))


def complete(req, commit_raw, rb_req, rb_raw, output_raw, accepted):
    """Pure future completion projection; caller/controller owns publication.

    Independent acceptance binds the commit AND actual readback bytes; this
    function never writes the nominated J-6.json path or a step verdict.
    """
    commit, rb = load_json(commit_raw), load_json(rb_raw)
    child_proof(req, wire(commit.get('head_change')))
    if (req['kind'].endswith('_dryrun') or commit.get('status') != 'AWAITING_READBACK'
            or any(commit.get(k) != req.get(k) for k in ('operation_id','kind','item_id','reviewed_commit'))
            or commit.get('request_sha256') != request_digest(req)):
        raise Refused('committed_head_receipt_required')
    if (rb_req.get('kind') != 'readback_sql' or rb_req.get('requested_by') not in ('v1','v2','v3','v4')
            or rb_req.get('item_id') != req['item_id'] or rb_req.get('operation_id') == req['operation_id']
            or (rb_req.get('args') or {}).get('sql_sha256') != raw_sha(readback_sql(req).encode())
            or rb.get('status') != 'COMPLETED' or rb.get('kind') != 'readback_sql'
            or rb.get('operation_id') != rb_req.get('operation_id') or rb.get('item_id') != req['item_id']
            or rb.get('requested_by') != rb_req.get('requested_by')
            or rb.get('request_sha256') != request_digest(rb_req) or rb.get('output_sha256') != raw_sha(output_raw)
            or decode_readback(output_raw) != expected_readback(req)):
        raise Refused('independent_exact_authority_readback_required')
    if (accepted.get('result') != 'ACCEPTED' or accepted.get('by') not in ('v1','v2','v3','v4')
            or accepted.get('by') == req.get('requested_by') or accepted.get('operation_id') != req['operation_id']
            or accepted.get('request_sha256') != request_digest(req) or accepted.get('receipt_sha256') != raw_sha(commit_raw)
            or accepted.get('readback_receipt_sha256') != raw_sha(rb_raw)):
        raise Refused('independent_digest_bound_acceptance_required')
    return dict(commit, status='COMPLETED', commit_receipt_sha256=raw_sha(commit_raw),
                readback_receipt_sha256=raw_sha(rb_raw))


def evidence_main(argv=None):
    """Offline preparation/completion projection; stdout only, no DB or writes."""
    parser = argparse.ArgumentParser(description=__doc__,allow_abbrev=False)
    commands = parser.add_subparsers(dest='command',required=True)
    decision_cmd = commands.add_parser('decision',allow_abbrev=False)
    decision_cmd.add_argument('--events',required=True,type=Path)
    sql_cmd = commands.add_parser('readback-sql',allow_abbrev=False)
    sql_cmd.add_argument('--request',required=True,type=Path)
    complete_cmd = commands.add_parser('complete',allow_abbrev=False)
    for key in ('request','commit-receipt','readback-request','readback-receipt','readback-output','acceptance'):
        complete_cmd.add_argument('--'+key,required=True,type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == 'decision':
            events = [load_json(line) for line in args.events.read_text().splitlines() if line.strip()]
            result = flip_decision(events)
        elif args.command == 'readback-sql':
            print(readback_sql(load_json(args.request.read_bytes())),end='')
            return 0
        else:
            result = complete(load_json(args.request.read_bytes()),args.commit_receipt.read_bytes(),
                              load_json(args.readback_request.read_bytes()),args.readback_receipt.read_bytes(),
                              args.readback_output.read_bytes(),load_json(args.acceptance.read_bytes()))
        print(wire(result).decode())
        return 0
    except Exception:
        print('head evidence refused; inspect bound inputs',file=sys.stderr)
        return 8


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] in ('decision','readback-sql','complete'):
        return evidence_main(argv)
    parser = argparse.ArgumentParser(description=__doc__,allow_abbrev=False)
    parser.add_argument('--kind',required=True,choices=('publish_head','rollback_head'))
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--dry-run',action='store_true'); mode.add_argument('--execute',action='store_true')
    for arg in ('generation','manifest-id','expected-head-sha256'):
        parser.add_argument('--'+arg,required=True)
    args = parser.parse_args(argv)
    try:
        req = load_json(os.environ.get('KY_OPERATION_REQUEST','{}'))
        kind = args.kind+('_dryrun' if args.dry_run else '')
        if req.get('kind') != kind or req.get('args') != {k:getattr(args,k.replace('-','_')) for k in ('generation','manifest-id','expected-head-sha256')}:
            raise Refused('executor_request_and_cli_mismatch')
        ops = Path(os.environ['KY_ROOT'])/'run/ops'
        problem = request_problem(req,ops)
        if problem:
            raise Refused(problem)
        import psycopg
        with psycopg.connect(os.environ['DATABASE_URL'],autocommit=True) as conn:
            proof = change_head(conn,req,dry_run=args.dry_run)
        print(wire(proof).decode())
        return 0
    except Exception:
        # Never print an exception that may contain a DSN or credential.
        print('head operation refused; reconcile the request and independent readback',file=sys.stderr)
        return 8


if __name__ == '__main__':
    raise SystemExit(main())
