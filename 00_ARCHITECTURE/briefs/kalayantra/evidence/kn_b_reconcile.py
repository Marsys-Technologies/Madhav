#!/usr/bin/env python3
"""Offline KN-B evidence reconciliation; no tracker writes or acceptance authority.

This checks a proposed registration and digest-bound receipt bundle. An independent
reviewer must authenticate receipts and current heads. A clean report is neither
live wiring proof nor permission to close the parent. Missing evidence exits 1.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

ROLES = ('moorti_nirnaya', 'kota_chakra', 'tithi_pravesha',
         'sudarshana_varsha', 'judge_vedha_wiring')
HEX40 = re.compile(r'[0-9a-f]{40}')
HEX64 = re.compile(r'[0-9a-f]{64}')


def _artifact(ref):
    """Load only digest-pinned bytes; an absent digest never authenticates a file."""
    path = Path(ref.get('path', ''))
    if not path.is_file():
        return None, f'missing artifact: {path}'
    digest = ref.get('sha256')
    if not isinstance(digest, str) or not HEX64.fullmatch(digest):
        return None, f'unpinned artifact digest: {path}'
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != digest:
        return None, f'artifact digest mismatch: {path}'
    return raw, None


def inspect_custody(custody):
    _, original_error = _artifact(custody['original_builder'])
    errors = []
    for ref in custody.get('artifacts', []):
        _, error = _artifact(ref)
        if error:
            errors.append(error)
    return {'original_builder_available': original_error is None,
            'original_builder_gap': original_error, 'artifact_errors': errors}


def _receipt_gaps(child, model_item):
    label = child['role']
    raw, error = _artifact(child.get('receipt', {}))
    if error:
        return [f'{label}: {error}']
    try:
        receipt = json.loads(raw)
    except (ValueError, TypeError):
        return [f'{label}: invalid receipt JSON']
    if not isinstance(receipt, dict):
        return [f'{label}: receipt must be an object']
    errors = []
    if receipt.get('item') != child['item']:
        errors.append(f'{label}: receipt item mismatch')
    head = child.get('head')
    if not isinstance(head, str) or not HEX40.fullmatch(head) or receipt.get('head') != head:
        errors.append(f'{label}: independent review must bind exact head')
    if receipt.get('verdict') != 'ACCEPTED':
        errors.append(f'{label}: independent review must be ACCEPTED')
    if not receipt.get('author') or not receipt.get('reviewer') or receipt['author'] == receipt['reviewer']:
        errors.append(f'{label}: reviewer must be independent of author')
    if receipt.get('state') != 'done':
        errors.append(f'{label}: completion must be done; skipped/ready does not count')
    merge = receipt.get('merge_sha')
    if not isinstance(merge, str) or not HEX40.fullmatch(merge):
        errors.append(f'{label}: missing squash merge mapping')
    # Readback applicability must itself be declared. This is an offline bundle
    # format, not a new tracker receipt or a replacement for protected operations.
    if (model_item.get('reviewer_rule') == 'v_exact_head_then_post_deploy_at_merge_commit'
            and receipt.get('readback_required') is not True):
        errors.append(f'{label}: model-required readback cannot be waived by receipt')
    if not isinstance(receipt.get('readback_required'), bool):
        errors.append(f'{label}: readback applicability undeclared')
    elif receipt['readback_required']:
        readback = receipt.get('readback')
        if not isinstance(readback, dict) or readback.get('head') != merge or readback.get('verdict') != 'ACCEPTED':
            errors.append(f'{label}: required merge-head readback missing or unaccepted')
    return errors


def reconcile(model, evidence):
    """Return offline gaps, preserving original upstream and downstream edges.

    Evidence crosswalks use actual registered IDs supplied by the cockpit; this
    tool neither allocates children nor converts the accepted parent's detector.
    """
    rows = model['items']
    errors = []
    counts = Counter(row['id'] for row in rows)
    errors.extend(f'duplicate item: {item}' for item, count in counts.items() if count > 1)
    items = {row['id']: row for row in rows}
    for row in rows:
        for dep in row.get('depends_on', []):
            if dep not in items:
                errors.append(f'{row["id"]}: unknown dependency {dep}')
    state = {}

    def visit(item):
        if state.get(item) == 1:
            errors.append(f'dependency cycle at {item}')
            return
        if state.get(item) == 2:
            return
        state[item] = 1
        for dep in items.get(item, {}).get('depends_on', []):
            visit(dep)
        state[item] = 2

    for item in items:
        visit(item)
    parent = items.get('KA-3b', {})
    if parent.get('join') is not True or parent.get('done_by') != 'join' or parent.get('detector'):
        errors.append('KA-3b: parent join registration absent; branch preacceptance is insufficient')
    deps = parent.get('depends_on', [])
    # The pinned packet's original floor cannot be weakened by editing evidence.
    floor = {'D-R8', 'J-0m', 'KA-3a'} | set(evidence.get('baseline_parent_dependencies', []))
    for dep in sorted(floor - set(deps)):
        errors.append(f'KA-3b: original dependency lost: {dep}')
    for waiter in evidence['baseline_downstream_waiters']:
        if 'KA-3b' not in items.get(waiter, {}).get('depends_on', []):
            errors.append(f'KA-3b: original downstream edge lost: {waiter}')
    children = evidence['children']
    role_counts = Counter(c['role'] for c in children)
    for role in ROLES:
        if role_counts[role] == 0:
            errors.append(f'{role}: missing child correspondence')
        elif role_counts[role] > 1:
            errors.append(f'duplicate role: {role}')
    for role in set(role_counts) - set(ROLES):
        errors.append(f'unknown child role: {role}')
    child_ids = [c['item'] for c in children]
    if len(set(child_ids)) != len(child_ids):
        errors.append('reused child across obligations')
    for dep in set(deps) - floor - set(child_ids):
        owns = items.get(dep, {}).get('brief', {}).get('owns', [])
        if any(any(f'/services/ka_{family}/' in p or f'/writers/ka_{family}.py' in p
                   for family in ROLES[:4]) or '/writers/ka_gochara_v5.py' in p
                   or '/services/gochara_kernel/' in p for p in owns):
            errors.append(f'unmapped family/wiring dependency: {dep}')
    for child in children:
        item, role = child['item'], child['role']
        if item not in items:
            errors.append(f'{role}: unregistered child {item}')
        if item not in deps:
            errors.append(f'{role}: parent child dependency absent: {item}')
        owns = items.get(item, {}).get('brief', {}).get('owns', [])
        families = {family for family in ROLES[:4] if any(
            f'/services/ka_{family}/' in p or f'/writers/ka_{family}.py' in p for p in owns)}
        if role in ROLES[:4] and families != {role}:
            errors.append(f'{role}: ownership must correspond to exactly one family')
        if role == ROLES[4] and (families or not any(
            '/writers/ka_gochara_v5.py' in p or '/services/gochara_kernel/' in p for p in owns)):
            errors.append(f'{role}: independent wiring ownership absent or mixed with a family')
        errors.extend(_receipt_gaps(child, items.get(item, {})))
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', required=True, type=Path)
    parser.add_argument('--evidence', required=True, type=Path)
    parser.add_argument('--verify-custody', action='store_true')
    args = parser.parse_args(argv)
    evidence = json.loads(args.evidence.read_text())
    gaps = reconcile(json.loads(args.model.read_text()), evidence)
    report = {'schema': 'ky.kn_b_reconciliation/1', 'offline_gaps': gaps,
              'acceptance_authority': False, 'production_actions': False}
    if args.verify_custody:
        report['custody'] = inspect_custody(evidence['custody'])
    print(json.dumps(report, indent=2))
    custody = report.get('custody', {})
    return int(bool(gaps or custody.get('artifact_errors') or
                    (args.verify_custody and not custody.get('original_builder_available'))))


if __name__ == '__main__':
    raise SystemExit(main())
