"""Measured source binding for operational step receipts, including served soak.

(I) INTERPRETATION: the review's unique matching step names evidence_path;
the evidence names SHA-256-bound request, executor receipt and independent
readback files. No receipt field or MET marker substitutes for their bytes.
"""
import hashlib
import json
from pathlib import Path

from pravaha_tracker.completion import CompletionError


def load_bound(reference, base):
    if not isinstance(reference, dict) or not isinstance(reference.get('path'), str):
        raise CompletionError('bound evidence file path required')
    path = Path(reference['path'])
    if not path.is_absolute():
        path = Path(base).parent / path
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != reference.get('sha256'):
        raise CompletionError('source evidence bytes differ from the reviewed digest')
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise CompletionError('source evidence must be an object')
    return value, path


def check_operation_evidence(receipt, reviewed_step, result_path):
    evidence, path = load_bound({'path': reviewed_step.get('evidence_path'),
                                 'sha256': receipt.get('evidence_sha256')}, result_path)
    for key in ('request_id', 'operation_id'):
        if not isinstance(receipt.get(key), str) or not receipt[key] or evidence.get(key) != receipt[key]:
            raise CompletionError('source evidence request/operation identity mismatch')
    sources = evidence.get('sources')
    if not isinstance(sources, dict):
        raise CompletionError('source request, receipt and readback required')
    request, _ = load_bound(sources.get('request'), path)
    executed, _ = load_bound(sources.get('receipt'), path)
    readback, _ = load_bound(sources.get('readback'), path)
    digest = hashlib.sha256(json.dumps({k: v for k, v in request.items() if k != 'acceptance_receipt'},
                                     sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    if (request.get('request_id') != receipt['request_id']
            or any(value.get('operation_id') != receipt['operation_id'] for value in (request, executed, readback))
            or readback.get('request_id') != receipt['request_id']
            or any(value.get('request_sha256') != digest for value in (executed, readback))
            or any(value.get('reviewed_commit') != request.get('reviewed_commit') for value in (executed, readback))
            or executed.get('status') != 'COMPLETED' or executed.get('exit_code') != 0
            or executed.get('kind') != request.get('kind')
            or readback.get('executor_receipt_sha256') != sources['receipt'].get('sha256')
            or readback.get('result') != 'ACCEPTED' or readback.get('by') not in ('v1', 'v2', 'v3', 'v4')):
        raise CompletionError('source request/receipt/independent readback chain mismatch')
    soak_step = (receipt.get('item') == 'J-6l-a61'
                 and receipt.get('step') == 'owner_soak_rule_and_live_readback')
    if soak_step and evidence.get('schema') != 'ky.served_soak/1':
        raise CompletionError('served soak requires measured sample evidence')
    if evidence.get('schema') == 'ky.served_soak/1':
        from pravaha_tracker.served_soak import check_soak
        check_soak(evidence, path, request=request, readback=readback, reviewed_step=reviewed_step)
