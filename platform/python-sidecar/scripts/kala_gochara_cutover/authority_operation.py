"""Disabled J-6m/J-6r executor child: sealed authority CAS and retained-head restore.

The executor alone supplies DATABASE_URL and the accepted complete request.
No ledger rollback, generation deletion, default/v1 fallback or schema mutation.
(I) INTERPRETATION: expected-head is SHA-256 of the complete observed authority
row (including audit metadata); rollback consumes the exact successful publish
output, bound to the executor receipt, instead of accepting a caller-made row.
Dry runs execute the same SQL and guards and roll back their entire transaction.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import uuid

from psycopg.pq import TransactionStatus

from scripts.kala_gochara_cutover.j6r_rehearsal import Head, read_head, _retained

CHART = '482012f1-710e-4a25-994a-93821f5871aa'
SHA = re.compile(r'[0-9a-f]{64}\Z')
SAFE_ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,79}\Z')
PUBLISH_ARGS = {'generation', 'manifest-id', 'expected-head'}
ROLLBACK_ARGS = {'generation', 'expected-head', 'source-operation', 'source-sha256'}


class OperationRefused(RuntimeError):
    pass


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def head_dict(head):
    return {'generation': head.generation,
            'flipped_at': head.flipped_at.astimezone(timezone.utc).isoformat() if head.flipped_at is not None else None,
            'flipped_by': head.flipped_by, 'evidence_ref': head.evidence_ref}


def head_digest(head):
    return digest(head)


def _head(value):
    if not isinstance(value, dict) or set(value) != {'generation', 'flipped_at', 'flipped_by', 'evidence_ref'}:
        raise OperationRefused('invalid_retained_head')
    timestamp = datetime.fromisoformat(value['flipped_at']) if value['flipped_at'] is not None else None
    if timestamp is not None and timestamp.tzinfo is None:
        raise OperationRefused('retained_head_timestamp_requires_timezone')
    return Head(value['generation'], timestamp, value['flipped_by'], value['evidence_ref'])


def validate_request(request, *, dry_run):
    kind = request.get('kind')
    kinds = ('publish_head_dryrun', 'rollback_head_dryrun') if dry_run else ('publish_head', 'rollback_head')
    if kind not in kinds or request.get('chart_id') != CHART:
        raise OperationRefused('request_kind_or_chart_mismatch')
    for key in ('operation_id', 'request_id'):
        if not isinstance(request.get(key), str) or not SAFE_ID.fullmatch(request[key]):
            raise OperationRefused('request_identity_required')
    args = request.get('args')
    allowed = PUBLISH_ARGS if kind.startswith('publish_') else ROLLBACK_ARGS
    if not isinstance(args, dict) or set(args) != allowed or any(not isinstance(v, str) for v in args.values()):
        raise OperationRefused('exact_bounded_arguments_required')
    if not SHA.fullmatch(args['expected-head']):
        raise OperationRefused('expected_full_head_digest_required')
    if kind.startswith('publish_'):
        if args['generation'] != '5.0' or str(uuid.UUID(args['manifest-id'])) != args['manifest-id']:
            raise OperationRefused('governed_5_0_manifest_required')
    elif not SAFE_ID.fullmatch(args['source-operation']) or not SHA.fullmatch(args['source-sha256']):
        raise OperationRefused('bound_publish_source_required')
    return args


def _rollback_source(request, args, evidence_root):
    oid = args['source-operation']  # validate_request checks this before path composition
    root = Path(evidence_root).resolve()
    def load(suffix):
        path = (root / (oid + suffix)).resolve()
        if path.parent != root:
            raise OperationRefused('source_escapes_receipts')
        raw = path.read_bytes()
        return raw, json.loads(raw)
    _, receipt = load('.json')
    raw, proof = load('.output.txt')
    if (hashlib.sha256(raw).hexdigest() != args['source-sha256']
            or receipt.get('output_sha256') != args['source-sha256']
            or receipt.get('operation_id') != oid or receipt.get('kind') != 'publish_head'
            or receipt.get('status') != 'COMPLETED' or receipt.get('exit_code') != 0
            or proof.get('schema') != 'ky.authority_operation/1' or proof.get('status') != 'COMMITTED'
            or proof.get('operation_id') != oid or proof.get('kind') != 'publish_head'
            or proof.get('chart_id') != request['chart_id']
            or receipt.get('request_sha256') != proof.get('request_sha256')
            or not SHA.fullmatch(str(proof.get('request_sha256', '')))
            or proof.get('retained_before') != proof.get('retained_after')
            or head_digest(proof.get('after')) != args['expected-head']):
        raise OperationRefused('publish_source_binding_failed')
    replacement = _head(proof.get('before'))
    if replacement.generation != args['generation']:
        raise OperationRefused('rollback_requires_exact_retained_generation')
    return replacement


def apply(conn, request, *, dry_run, evidence_root=None):
    args = validate_request(request, dry_run=dry_run)
    if not conn.autocommit or conn.info.transaction_status != TransactionStatus.IDLE:
        raise OperationRefused('standalone_idle_autocommit_connection_required')
    replacement = None
    if request['kind'].startswith('rollback_'):
        if evidence_root is None:
            raise OperationRefused('publish_source_required')
        replacement = _rollback_source(request, args, evidence_root)
    request_sha = digest({k: v for k, v in request.items() if k != 'acceptance_receipt'})
    with conn.transaction(force_rollback=dry_run):
        conn.execute("SET LOCAL lock_timeout = '5s'")
        conn.execute("SET LOCAL statement_timeout = '30s'")
        conn.execute('SELECT public.ka_gochara_lock_chart(%s::uuid)', (CHART,))
        previous = read_head(conn, CHART)
        before = head_dict(previous)
        if head_digest(before) != args['expected-head']:
            raise OperationRefused('head_compare_and_swap_conflict')
        if replacement is None:
            admitted = conn.execute(
                'SELECT p.manifest_id FROM public.kala_gochara_publication p'
                ' JOIN public.ka_gochara_generation_seal s ON s.chart_id=p.chart_id'
                ' AND s.generation=p.generation AND s.manifest_id=p.manifest_id'
                " WHERE p.chart_id=%s AND p.generation=%s AND p.manifest_id=%s::uuid AND p.status='published'"
                " AND coalesce(p.input_generation_vector->>'stored_scope','') <> 'test_slice'"
                " AND NOT (p.input_generation_vector ? 'test_slice')",
                (CHART, args['generation'], args['manifest-id'])).fetchone()
            if admitted is None or previous.generation == args['generation']:
                raise OperationRefused('target_not_admissible_or_already_current')
            replacement = Head(args['generation'], datetime.now(timezone.utc), 'kalayantra-executor',
                               'manifest:' + args['manifest-id'])
        retained_before = _retained(conn, CHART)
        # Durable preimage precedes the first write. An interruption leaves an
        # immutable intent for independent readback, never permission to retry.
        if not dry_run:
            root = Path(os.environ['KY_ROOT']) / 'run/ops/authority-intents'
            root.mkdir(parents=True, exist_ok=True)
            intent = {'schema': 'ky.authority_intent/1', 'status': 'PREPARED',
                      'operation_id': request['operation_id'], 'request_id': request['request_id'],
                      'request_sha256': request_sha, 'chart_id': CHART,
                      'before': before, 'after': head_dict(replacement), 'retained_before': retained_before}
            try:
                with (root / (request['operation_id'] + '.json')).open('xb') as handle:
                    handle.write(canonical(intent) + b'\n')
                    handle.flush()
                    os.fsync(handle.fileno())
            except FileExistsError as exc:
                raise OperationRefused('intent_already_exists_reconcile_without_retry') from exc
            directory = os.open(root, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        changed = conn.execute(
            'UPDATE public.kala_gochara_authority SET authoritative_generation=%s,flipped_at=%s,'
            'flipped_by=%s,evidence_ref=%s WHERE chart_id=%s AND'
            ' (authoritative_generation,flipped_at,flipped_by,evidence_ref)'
            ' IS NOT DISTINCT FROM (%s,%s::timestamptz,%s,%s) RETURNING chart_id',
            (replacement.generation, replacement.flipped_at, replacement.flipped_by, replacement.evidence_ref,
             CHART, previous.generation, previous.flipped_at, previous.flipped_by, previous.evidence_ref)).fetchone()
        if changed is None:
            raise OperationRefused('head_compare_and_swap_conflict')
        after = head_dict(read_head(conn, CHART))
        retained_after = _retained(conn, CHART)
        if after != head_dict(replacement) or retained_before != retained_after:
            raise OperationRefused('head_or_retained_rows_readback_failed')
        proof = {'schema': 'ky.authority_operation/1', 'kind': request['kind'], 'chart_id': CHART,
                 'operation_id': request['operation_id'], 'request_id': request['request_id'],
                 'args': dict(args), 'reviewed_commit': request.get('reviewed_commit'),
                 'request_sha256': request_sha, 'before': before, 'after': after,
                 'retained_before': retained_before, 'retained_after': retained_after}
    # Emitted only after the transaction context successfully commits/rolls back.
    proof['status'] = 'ROLLED_BACK' if dry_run else 'COMMITTED'
    if dry_run and head_dict(read_head(conn, CHART)) != before:
        raise OperationRefused('dryrun_rollback_readback_failed')
    return proof



def check_execution_bindings(request, root):
    """Require real rollback-confirmed dry-run bytes and their independent acceptance."""
    oid, output_sha = request.get('dryrun_operation'), request.get('dryrun_output_sha256')
    if (not isinstance(oid, str) or not SAFE_ID.fullmatch(oid)
            or not isinstance(output_sha, str) or not SHA.fullmatch(output_sha)):
        raise OperationRefused('accepted_same_head_dryrun_required')
    root = Path(root)
    receipt = json.loads((root / 'receipts' / (oid + '.json')).read_bytes())
    raw = (root / 'receipts' / (oid + '.output.txt')).read_bytes()
    proof = json.loads(raw)
    accepted = json.loads((root / 'acceptance' / (oid + '.json')).read_bytes())
    commit = request.get('reviewed_commit')
    if (not isinstance(commit, str) or not re.fullmatch(r'[0-9a-f]{40}', commit)
            or hashlib.sha256(raw).hexdigest() != output_sha
            or receipt.get('output_sha256') != output_sha
            or receipt.get('operation_id') != oid or proof.get('operation_id') != oid
            or receipt.get('kind') != request['kind'] + '_dryrun'
            or proof.get('kind') != receipt.get('kind')
            or receipt.get('status') != 'COMPLETED' or receipt.get('exit_code') != 0
            or proof.get('schema') != 'ky.authority_operation/1' or proof.get('status') != 'ROLLED_BACK'
            or proof.get('args') != request['args'] or proof.get('chart_id') != request['chart_id']
            or proof.get('reviewed_commit') != commit or receipt.get('reviewed_commit') != commit
            or proof.get('request_sha256') != receipt.get('request_sha256')
            or proof.get('retained_before') != proof.get('retained_after')
            or head_digest(proof.get('before')) != request['args']['expected-head']
            or accepted.get('result') != 'ACCEPTED' or accepted.get('by') not in ('v1', 'v2', 'v3', 'v4')
            or accepted.get('operation_id') != oid or accepted.get('reviewed_commit') != commit
            or accepted.get('request_sha256') != proof.get('request_sha256')
            or accepted.get('output_sha256') != output_sha):
        raise OperationRefused('accepted_same_head_dryrun_binding_failed')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--dry-run', action='store_true')
    mode.add_argument('--execute', action='store_true')
    parser.add_argument('--kind', required=True, choices=('publish_head', 'rollback_head'))
    for key in sorted(PUBLISH_ARGS | ROLLBACK_ARGS):
        parser.add_argument('--' + key)
    parsed = parser.parse_args(argv)
    try:
        request = json.loads(os.environ['KY_OPERATION_REQUEST'])
        args = {key: getattr(parsed, key.replace('-', '_')) for key in PUBLISH_ARGS | ROLLBACK_ARGS
                if getattr(parsed, key.replace('-', '_')) is not None}
        kind = parsed.kind + ('_dryrun' if parsed.dry_run else '')
        if request.get('kind') != kind or request.get('args') != args:
            raise OperationRefused('executor_transport_mismatch')
        validate_request(request, dry_run=parsed.dry_run)
        if parsed.execute:
            check_execution_bindings(request, Path(os.environ['KY_ROOT']) / 'run/ops')
        import psycopg
        with psycopg.connect(os.environ['DATABASE_URL'], autocommit=True, connect_timeout=5) as conn:
            proof = apply(conn, request, dry_run=parsed.dry_run,
                          evidence_root=Path(os.environ['KY_ROOT']) / 'run/ops/receipts')
        print(canonical(proof).decode())
        return 0
    except Exception as exc:
        # DSNs and exception detail never reach the evidence stream.
        print('authority operation refused (' + type(exc).__name__ + '); reconcile before retry', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
