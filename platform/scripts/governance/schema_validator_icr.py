#!/usr/bin/env python3
"""
schema_validator_icr.py — Validate YAML artifacts in CONFLICT_PATCHES/PROPOSED/
against the ProposePatchArtifact schema (ICR-S1, 2026-05-21).

Exit codes:
  0 — all files valid, or directory empty (PASS_EMPTY_PROPOSED_DIR)
  1 — one or more files failed validation
"""

import sys
import os
import glob

# Resolve paths relative to the repository root (two levels up from this script)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..', '..'))
PROPOSED_DIR = os.path.join(REPO_ROOT, '00_ARCHITECTURE', 'CONFLICT_PATCHES', 'PROPOSED')

VALID_CONFLICT_CLASSES = {'A', 'B', 'C'}
VALID_STATUSES = {'pending', 'confirmed', 'rejected', 'escalated'}
VALID_TIER_NAMES = {'signal', 'ucn_edges', 'cdlm_links', 'rm_paths', 'synthesis_cache'}

REQUIRED_TOP_LEVEL = [
    'conflict_id',
    'conflict_class',
    'signal_ids_affected',
    'proposed_change',
    'propagation_chain',
    'confidence',
    'authored_by',
    'authored_on',
    'status',
]

REQUIRED_CHAIN_TIER = ['tier', 'tier_name', 'mandatory', 'affected_ids']


def validate_file(path: str) -> list[str]:
    """Return list of error strings; empty list means valid."""
    errors: list[str] = []

    try:
        import yaml  # type: ignore
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except ImportError:
        # Fallback: minimal manual YAML check — just verify it's non-empty text
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        if not content:
            errors.append('File is empty')
        else:
            errors.append('WARNING: PyYAML not installed; only emptiness check performed')
        return errors
    except Exception as e:
        errors.append(f'YAML parse error: {e}')
        return errors

    if not isinstance(data, dict):
        errors.append('Top-level document must be a YAML mapping')
        return errors

    # Required fields presence
    for field in REQUIRED_TOP_LEVEL:
        if field not in data:
            errors.append(f'Missing required field: {field}')

    if errors:
        return errors  # Stop early if required fields missing

    # Type checks
    if not isinstance(data['conflict_id'], str) or not data['conflict_id']:
        errors.append('conflict_id must be a non-empty string')

    cc = data['conflict_class']
    if cc not in VALID_CONFLICT_CLASSES:
        errors.append(f'conflict_class must be one of {VALID_CONFLICT_CLASSES}; got {cc!r}')

    sia = data['signal_ids_affected']
    if not isinstance(sia, list) or len(sia) == 0:
        errors.append('signal_ids_affected must be a non-empty list')
    elif not all(isinstance(s, str) for s in sia):
        errors.append('All signal_ids_affected entries must be strings')

    if not isinstance(data['proposed_change'], str) or not data['proposed_change']:
        errors.append('proposed_change must be a non-empty string')

    chain = data['propagation_chain']
    if not isinstance(chain, list) or len(chain) == 0:
        errors.append('propagation_chain must be a non-empty list')
    else:
        for i, tier in enumerate(chain):
            if not isinstance(tier, dict):
                errors.append(f'propagation_chain[{i}] must be a mapping')
                continue
            for tf in REQUIRED_CHAIN_TIER:
                if tf not in tier:
                    errors.append(f'propagation_chain[{i}] missing required field: {tf}')
            if 'tier' in tier and tier['tier'] not in (1, 2, 3, 4, 5):
                errors.append(f'propagation_chain[{i}].tier must be 1–5; got {tier["tier"]!r}')
            if 'tier_name' in tier and tier['tier_name'] not in VALID_TIER_NAMES:
                errors.append(
                    f'propagation_chain[{i}].tier_name must be one of {VALID_TIER_NAMES}; '
                    f'got {tier["tier_name"]!r}'
                )
            if 'mandatory' in tier and not isinstance(tier['mandatory'], bool):
                errors.append(f'propagation_chain[{i}].mandatory must be a boolean')
            if 'affected_ids' in tier and not isinstance(tier['affected_ids'], list):
                errors.append(f'propagation_chain[{i}].affected_ids must be a list')

    conf = data['confidence']
    if not isinstance(conf, (int, float)) or not (0.0 <= float(conf) <= 1.0):
        errors.append(f'confidence must be a number in [0, 1]; got {conf!r}')

    if not isinstance(data['authored_by'], str) or not data['authored_by']:
        errors.append('authored_by must be a non-empty string')

    if not isinstance(data['authored_on'], str) or not data['authored_on']:
        errors.append('authored_on must be a non-empty string (ISO date)')

    status = data['status']
    if status not in VALID_STATUSES:
        errors.append(f'status must be one of {VALID_STATUSES}; got {status!r}')

    return errors


def main() -> int:
    if not os.path.isdir(PROPOSED_DIR):
        print(f'ERROR: PROPOSED directory not found at: {PROPOSED_DIR}', file=sys.stderr)
        return 1

    yaml_files = sorted(glob.glob(os.path.join(PROPOSED_DIR, '*.yaml')))
    yaml_files += sorted(glob.glob(os.path.join(PROPOSED_DIR, '*.yml')))
    yaml_files = sorted(set(yaml_files))

    if not yaml_files:
        print('PASS_EMPTY_PROPOSED_DIR')
        return 0

    all_valid = True
    for path in yaml_files:
        rel = os.path.relpath(path, REPO_ROOT)
        errors = validate_file(path)
        if errors:
            all_valid = False
            print(f'FAIL  {rel}')
            for e in errors:
                print(f'      - {e}')
        else:
            print(f'PASS  {rel}')

    if all_valid:
        print(f'\nAll {len(yaml_files)} PROPOSED artifact(s) valid.')
        return 0
    else:
        print(f'\nValidation FAILED — fix errors above before promoting to RESOLVED.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
