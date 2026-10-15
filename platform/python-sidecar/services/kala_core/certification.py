"""Offline certification evidence readers; never execute the census or award PASS."""
from __future__ import annotations

import ast
from pathlib import Path
import re

REGISTRY_PATH = Path('platform/scripts/governance/asset_census.py')
VIEW_ROOT = 'platform/src/lib/retrieval/registry/layers/L3_kala/'
# Independent requirements, never inferred from the mapping being validated.
TULANA_CRITERIA = frozenset({
    'Build.contract', 'Idem.pattern', 'Earn.service_state', 'Dens.served',
    'Narr.agree', 'Narr.checkable', 'Narr.fidelity_test', 'Narr.lint',
    'Null.schema_default', 'Null.blank_rows', 'Carr.D1', 'Carr.D2', 'Carr.D3',
})
COMMON_VIEW_TESTS = frozenset({
    VIEW_ROOT + 'views_registry.integration.test.ts', VIEW_ROOT + 'view_common.test.ts',
})
PRIORITY_TESTS = frozenset({
    VIEW_ROOT + '__tests__/f131_priority_ranking_glossary.test.ts',
    'platform-mcp/src/tools/kala_views/f171_disclosure_receipt_regression.test.ts',
})


def read_detector_registry(path: Path) -> tuple[int, dict]:
    """Read the literal revision/detector bindings used by the K7-4 verifier."""
    tree = ast.parse(path.read_text())
    revision = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == 'REGISTRY_REVISION' for t in n.targets))
    registry = next(n.value for n in tree.body if isinstance(n, ast.AnnAssign)
                    and isinstance(n.target, ast.Name) and n.target.id == 'CRITERION_REGISTRY')
    criteria = {ast.literal_eval(k): {x.arg: ast.literal_eval(x.value) for x in v.keywords
                if x.arg in {'revision', 'detector'}} for k, v in zip(registry.keys, registry.values)}
    return revision, criteria


def test_reference_exists(sidecar: Path, reference: str) -> bool:
    """Resolve a pytest function/class node from source without importing DB tests."""
    parts = reference.split('::')
    path = (sidecar / parts[0]).resolve()
    if len(parts) < 2 or not path.is_relative_to((sidecar / 'tests').resolve()):
        return False
    if not path.name.startswith('test_') or path.suffix != '.py':
        return False
    node = ast.parse(path.read_text())
    for name in parts[1:]:
        node = next((n for n in getattr(node, 'body', [])
                     if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                     and n.name == name), None)
        if node is None:
            return False
    return isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith('test_')


def validate_detector_bindings(root: Path, mapping: dict, *, gates=None,
                               required_criteria=TULANA_CRITERIA) -> list[str]:
    """Validate flat K7-4 or grouped K6-5 evidence against independent coverage.

    Gate membership/revisions come from the production registry. A mapping
    cannot shrink its own required set, including criteria with detector NONE.
    """
    errors = []
    revision, criteria = read_detector_registry(root / REGISTRY_PATH)
    if mapping.get('registry_revision') != revision:
        errors.append('stale detector registry revision')
    if gates is not None:
        evidence_gates = mapping.get('gates', {})
        if set(evidence_gates) != set(gates):
            errors.append('nine active gates required')
        for gate in gates:
            evidence = evidence_gates.get(gate, {})
            expected = {key: value['revision'] for key, value in criteria.items()
                        if key.split('.')[0] == gate}
            if not expected or evidence.get('revisions') != expected:
                errors.append(f'missing/stale detector binding: {gate}')
            if not evidence.get('expected_reading'):
                errors.append(f'missing expected reading: {gate}')
            none = {key for key in expected if criteria[key]['detector'] == 'NONE'}
            if set(evidence.get('detector_none', [])) != none:
                errors.append(f'wrong NO_DETECTOR binding: {gate}')
            if none and ('NO_DETECTOR' not in evidence.get('expected_reading', '')
                         or not evidence.get('detector_dependency')):
                errors.append(f'missing NO_DETECTOR dependency: {gate}')
        return errors

    if mapping.get('registry_path') != str(REGISTRY_PATH):
        errors.append('wrong detector registry path')
    detectors = mapping.get('detectors', {})
    if set(detectors) != set(required_criteria):
        errors.append('missing/unknown detector binding')
    for key, evidence in detectors.items():
        criterion = criteria.get(key)
        if criterion is None or any(evidence.get(field) != criterion.get(field)
                                    for field in ('revision', 'detector')):
            errors.append(f'stale detector: {key}')
        expected = 'NO_DETECTOR' if criterion and criterion['detector'] == 'NONE' else 'UNMEASURED'
        if evidence.get('verdict') != expected:
            errors.append(f'unearned verdict: {key}')
    return errors


def validate_fidelity_bindings(root: Path, references, *, required) -> list[str]:
    """Require the claim's real golden identities and executable test sources."""
    if not isinstance(references, list) or not references:
        return ['fidelity evidence required']
    errors = []
    if not set(required) <= set(references):
        errors.append('missing required fidelity test binding')
    for reference in references:
        if reference.startswith('tests/'):
            exists = test_reference_exists(root / 'platform/python-sidecar', reference)
        else:
            path = (root / reference).resolve()
            exists = (path.is_relative_to(root.resolve()) and path.is_file()
                      and path.name.endswith('.test.ts')
                      and re.search(r'\b(?:it|test)(?:\.\w+)*\s*\(', path.read_text()) is not None)
        if not exists:
            errors.append(f'missing fidelity test: {reference}')
    return errors


def validate_view_bindings(root: Path, name: str, view: dict) -> list[str]:
    """Resolve the tier pointer inside the real SQL reader and bind its goldens.

    (I) INTERPRETATION: a tier pointer names the stored-tier expression in
    viewSql, not an arbitrary line in a file that happens to contain SQL.
    Source hashes remain the caller's version-specific evidence pins.
    """
    required = COMMON_VIEW_TESTS | (PRIORITY_TESTS if name == 'priority' else frozenset())
    errors = validate_fidelity_bindings(root, view.get('fidelity_tests'), required=required)
    pointer = view.get('tier_select', '')
    file, separator, line = pointer.rpartition(':')
    if file != VIEW_ROOT + 'view_common.ts' or not separator or not line.isdecimal():
        return errors + [f'invalid tier SELECT binding: {name}']
    source = (root / file).read_text()
    lines = source.splitlines()
    index = int(line) - 1
    function = re.search(r'^export function viewSql\(spec: ViewSpec\): string \{.*?^\}',
                         source, re.MULTILINE | re.DOTALL)
    expression = 'const tier = "to_jsonb(s)->>\'verification_pass_status\'"'
    if (index < 0 or index >= len(lines) or lines[index].strip() != expression
            or function is None):
        return errors + [f'invalid tier SELECT binding: {name}']
    offset = sum(len(s) + 1 for s in lines[:index])
    sql = function.group()
    if (not function.start() <= offset < function.end()
            or not re.search(r'SELECT\s+to_jsonb\(s\)\s*\|\|\s*jsonb_build_object\('
                             r"'verification_pass_status',\s*to_jsonb\(s\)->>'verification_pass_status'\)", sql)
            or 'FROM ${table} s CROSS JOIN published p' not in sql
            or '${tier} IN (${quoted(VERIFIED_PASS_STATUSES)})' not in sql):
        errors.append(f'invalid stored-tier SQL evidence: {name}')
    return errors
