#!/usr/bin/env python3
"""Validate an already-exported, independently approved offline L1 bundle.

Reads local bytes only. Does not export, restore, execute SQL, compute chart
facts, obtain approval, or turn a synthetic fixture into canonical L1 authority.
The separate verifier owns canonical-source and schema/grant qualification.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import re

CHART = '482012f1-710e-4a25-994a-93821f5871aa'
REQUIRED_FILES = ('charts.json', 'chart_facts.json', 'chart_dashas.json', 'life_events.json', 'schema.sql', 'grants.sql')


def _json(body):
    def unique(pairs):
        result = {}
        for k, v in pairs:
            if k in result:
                raise ValueError('duplicate JSON field')
            result[k] = v
        return result
    return json.loads(body, object_pairs_hook=unique)


def validate(directory):
    root = Path(directory).resolve()
    def read(name):
        path = root / name
        if path.is_symlink() or path.resolve().parent != root:
            raise ValueError('snapshot reference escapes bundle')
        try:
            return path.read_bytes()
        except OSError:
            raise ValueError('required snapshot input missing') from None
    raw = read('manifest.json')
    m = _json(raw)
    approval = _json(read('approval.json'))
    digest = hashlib.sha256(raw).hexdigest()
    if not isinstance(m, dict) or not isinstance(approval, dict):
        raise ValueError('snapshot manifest and approval must be objects')
    if (m.get('schema') != 'ky.canonical_l1_snapshot/1' or m.get('chart_id') != CHART
            or m.get('source') != 'governed_offline_export' or m.get('canonical') is not True
            or m.get('builder_role') != 'data_plane_builder'
            or not re.fullmatch(r'[0-9a-f]{40}', str(m.get('source_commit', '')))):
        raise ValueError('canonical source, chart, reviewed commit and builder role required')
    try:
        captured = dt.datetime.fromisoformat(m['captured_at'].replace('Z', '+00:00'))
        if captured.tzinfo is None:
            raise ValueError()
    except (KeyError, ValueError, TypeError, AttributeError):
        raise ValueError('timezone-qualified snapshot timestamp required') from None
    if (approval.get('schema') != 'ky.canonical_l1_snapshot_approval/1'
            or approval.get('result') != 'ACCEPTED' or approval.get('by') not in ('v1', 'v2', 'v3', 'v4')
            or approval.get('manifest_sha256') != digest
            or approval.get('canonical_source_verified') is not True or approval.get('schema_grants_verified') is not True):
        raise ValueError('independent approval of these exact canonical-source/schema/grant bytes required')
    files = m.get('files')
    if not isinstance(files, dict) or set(files) != set(REQUIRED_FILES):
        raise ValueError('exact facts/dashas/chart/events/schema/grants inventory required')
    counts = {}
    for name in REQUIRED_FILES:
        body = read(name)
        f = files[name]
        if (not isinstance(f, dict) or type(f.get('bytes')) is not int or len(body) != f['bytes']
                or hashlib.sha256(body).hexdigest() != f.get('sha256')):
            raise ValueError('snapshot file byte digest/length mismatch')
        if name.endswith('.json'):
            rows = _json(body)
            if not isinstance(rows, list) or any(not isinstance(r, dict) for r in rows):
                raise ValueError('snapshot table must be a JSON array of stored rows')
            identity = {'charts.json': 'id', 'chart_facts.json': 'fact_id',
                        'chart_dashas.json': 'dasha_row_id', 'life_events.json': 'event_id'}[name]
            if (name != 'life_events.json' and not rows) or (name == 'charts.json' and len(rows) != 1):
                raise ValueError('canonical chart/facts/dashas may not be empty')
            ids = [r.get(identity) for r in rows]
            if any(not isinstance(i, str) or not i for i in ids) or len(set(ids)) != len(ids):
                raise ValueError('stored row identities must be present and unique')
            if any(r.get('id' if name == 'charts.json' else 'chart_id') != CHART for r in rows):
                raise ValueError('snapshot contains another chart')
            counts[name] = len(rows)
        elif not body.strip():
            raise ValueError('deployment schema/grants may not be empty')
    return dict(schema='ky.canonical_l1_snapshot_validation/1', manifest_sha256=digest,
                status='OFFLINE_BYTES_VALIDATED', chart_id=CHART, counts=counts,
                production_acceptance=False)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    args = parser.parse_args(argv)
    print(json.dumps(validate(args.directory), sort_keys=True))


if __name__ == '__main__':
    main()
