#!/usr/bin/env python3
"""Bind J4 preparation inputs to immutable request bytes. No DB/cloud action.

This output is PREPARATION_ONLY, never a dry-run attestation, executor receipt,
step receipt or authority to enable a job. Declarations are intentionally not
installed in executor_ops or brief.op: no production adapter is allocated here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

DECLARATIONS = Path(__file__).with_name('operations.json')
DECLARATIONS_SHA256 = 'ab22361a6fc9eb4b2dcf3c92493ebe485741cc786e9fc979fcebda5e0f797580'
SHA256 = re.compile(r'[0-9a-f]{64}\Z')
SHA1 = re.compile(r'[0-9a-f]{40}\Z')
IDENTIFIER = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,199}\Z')
CHART = '482012f1-710e-4a25-994a-93821f5871aa'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key')
        result[key] = value
    return result


def strict_json(raw):
    return json.loads(raw, object_pairs_hook=_object,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('non-finite JSON number')))


def read_bytes_bound(path, expected):
    if not isinstance(expected, str) or not SHA256.fullmatch(expected):
        raise ValueError('invalid expected digest')
    raw = Path(path).read_bytes()
    if not raw or hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError('file digest mismatch or empty input')
    return raw


def read_bound(path, expected):
    return strict_json(read_bytes_bound(path, expected))


def declarations():
    return read_bound(DECLARATIONS, DECLARATIONS_SHA256)


def bind(request):
    if not isinstance(request, dict) or set(request) != {
        'schema', 'item', 'phase', 'operation_id', 'request_id', 'reviewed_commit',
        'chart_id', 'generation', 'enabled', 'inputs',
    }:
        raise ValueError('complete request fields must match the preparation contract exactly')
    entry = declarations()['items'].get(request['item'])
    if entry is None or request['schema'] != 'ky.j4ops_preparation_request/1':
        raise ValueError('unknown item or request schema')
    if (type(request['phase']) is not int or request['phase'] != entry['phase']
            or request['generation'] != entry['generation'] or request['chart_id'] != CHART
            or request['enabled'] is not False):
        raise ValueError('phase/chart/generation/disabled scope differs from declaration')
    for field, regex in (('operation_id', IDENTIFIER), ('request_id', IDENTIFIER), ('reviewed_commit', SHA1)):
        if not isinstance(request[field], str) or not regex.fullmatch(request[field]):
            raise ValueError('invalid request identity')
    inputs = request['inputs']
    if not isinstance(inputs, dict) or set(inputs) != set(entry['required_inputs']):
        raise ValueError('required input set differs from declaration')
    for reference in inputs.values():
        if not isinstance(reference, dict) or set(reference) != {'path', 'sha256'}:
            raise ValueError('input reference requires exactly path and sha256')
        if not isinstance(reference['path'], str) or not Path(reference['path']).is_absolute():
            raise ValueError('input path must be absolute')
        read_bytes_bound(reference['path'], reference['sha256'])
    return dict(schema='ky.j4ops_preparation/1', status='PREPARATION_ONLY',
                item=request['item'], phase=request['phase'], operation_id=request['operation_id'],
                request_id=request['request_id'], reviewed_commit=request['reviewed_commit'],
                chart_id=CHART, generation=request['generation'], request_sha256=digest(request),
                declarations_sha256=DECLARATIONS_SHA256,
                runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                inputs=inputs, enabled=False, dry_run_passed=False, operation_completed=False,
                missing=entry['missing'])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('--item', required=True, choices=('J-4a-a25', 'J-4b-a55j', 'J-4c-a55m'))
    parser.add_argument('--request-file', required=True)
    parser.add_argument('--request-sha256', required=True)
    args = parser.parse_args(argv)
    try:
        request = read_bound(args.request_file, args.request_sha256)
        if not isinstance(request, dict) or request.get('item') != args.item:
            raise ValueError('request belongs to another item')
        record = bind(request)
        record['request_file_sha256'] = args.request_sha256
        print(json.dumps(record, sort_keys=True, allow_nan=False))
    except (OSError, ValueError, TypeError, KeyError):
        print('REFUSED: missing, malformed or changed J4 preparation input', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
