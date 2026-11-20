"""Offline certification evidence readers; never execute the census or award PASS."""
from __future__ import annotations

import ast
import json
from pathlib import Path
import re

REGISTRY_PATH = Path('platform/scripts/governance/asset_census.py')
DIGEST_PATH = 'platform/src/generated/nirmana-writer-digests.json'
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
# (I) INTERPRETATION: pin the complete approved rev-5 registrar reading.
# A prefix/token check or prose blacklist cannot establish consistency of an
# arbitrary later claim. Wording changes require an explicit evidence update;
# the SQL-oracle pass below is distinct from a current-detector PASS.
# Authority: control/kalayantra/plan_model.json:4898,4920 (FAIL/routed R-10).
REGISTRAR_IDEM_READING = (
    'FAIL under current Idem.pattern detector for insert_immutable_checked; '
    'reviewed immutable-insertion detector treatment routed to PLAN section7/R-10. '
    'Never delete issued history. Repeat and changed-retry SQL oracles pass; '
    'no production certificate'
)
PRIORITY_TESTS = frozenset({
    VIEW_ROOT + '__tests__/f131_priority_ranking_glossary.test.ts',
    'platform-mcp/src/tools/kala_views/f171_disclosure_receipt_regression.test.ts',
})
# K5-G1b / ALGO §3.20: independently declared candidate output footprint.
# Include intermediate operands and provenance as well as final products.
KSHETRA_OUTPUTS = frozenset({
    'kala_field_provenance_candidate', 'kala_field_salience_candidate',
    'kala_insights_candidate', 'kala_timeline_spec_candidate',
    'kala_field_windows_candidate', 'kala_field_null_candidate',
    'kala_field_candidate', 'kala_field_snapshots_candidate',
    'kala_field_primitives_candidate', 'kala_field_boundaries_candidate',
    'kala_field_clocks_candidate', 'kala_field_routes_candidate',
    'kala_field_promise_edges_candidate', 'kala_field_promise_nodes_candidate',
    'kala_field_kinematics_candidate', 'build_substep_progress_candidate',
    'kala_layer_candidate_grain',
})
KSHETRA_UNMEASURED_READING = (
    'UNMEASURED in production. Candidate structural oracles are code evidence only; '
    'no census PASS claimed.'
)
KSHETRA_NO_DETECTOR_READING = (
    ' NO_DETECTOR for the explicitly listed missing detectors.'
)


def _text(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _text_fields(value, fields) -> bool:
    return isinstance(value, dict) and all(_text(value.get(key)) for key in fields)


def _source_line_exists(root: Path, reference) -> bool:
    if not _text(reference):
        return False
    file, separator, line = reference.rpartition(':')
    path = (root / file).resolve()
    return (bool(separator) and line.isdecimal() and int(line) > 0
            and path.is_relative_to(root.resolve()) and path.is_file()
            and int(line) <= len(path.read_text().splitlines()))


def validate_contract_data(root: Path, mapping: dict) -> list[str]:
    """Check meaningful declarations for data writers and non-writing services.

    (I) INTERPRETATION: K8 declarations bind real inventory entries and source
    locators; a service may declare no tables or ledger source. This validates
    offline contract evidence, never its live truth or production certification.
    """
    errors = []
    data = mapping.get('kind') == 'data'
    if mapping.get('kind') not in {'data', 'service'}:
        errors.append('invalid contract kind')
    asset = mapping.get('asset') if data else mapping.get('asset_id')
    digest_field = 'writer_digest' if data else 'writer_digest_entry'
    reference = mapping.get(digest_field)
    expected = f'{DIGEST_PATH}:{asset}' if data else f'{DIGEST_PATH}#/writers/{asset}'
    try:
        inventory = json.loads((root / DIGEST_PATH).read_text())
        digest = inventory['writers'].get(asset)
        valid_digest = (reference == expected and isinstance(digest, str)
                        and re.fullmatch(r'[0-9a-f]{64}', digest))
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        valid_digest = False
    if not valid_digest:
        errors.append(f'invalid {digest_field} inventory binding')

    carriage = mapping.get('carriage')
    if (not isinstance(carriage, dict)
            or carriage.get('nature') not in {
                'source', 'transcription', 'computation', 'derivation', 'ratified_judgment'}
            or (data and not _text_fields(carriage, ('served_surface', 'evidence')))
            or not _source_line_exists(root, carriage.get('evidence') if data
                                       else carriage.get('served_call'))):
        errors.append('invalid carriage declaration/source locator')

    ledger = mapping.get('ldgr_source')
    if not (not data and 'ldgr_source' in mapping and ledger is None):
        if (not _text_fields(ledger, ('column', 'state'))
                or not re.fullmatch(r'[a-z_][a-z0-9_]*(?:\.[a-z_][a-z0-9_]*)+',
                                    ledger['column'])):
            errors.append('invalid ldgr_source declaration')

    tables = mapping.get('produced_tables')
    if (not isinstance(tables, list) or (data and not tables)
            or any(not isinstance(table, str) or not re.fullmatch(
                r'[a-z_][a-z0-9_]*(?:\.[a-z_][a-z0-9_]*)?', table) for table in tables)):
        errors.append('invalid produced_tables declaration')
    if asset == 'ka_kshetra' and (not isinstance(tables, list)
            or any(not isinstance(table, str) for table in tables)
            or set(tables) != KSHETRA_OUTPUTS or len(tables) != len(KSHETRA_OUTPUTS)):
        errors.append('incomplete Kshetra candidate output footprint')

    fingerprint = mapping.get('semantic_fingerprint')
    fields = ('inputs', 'outputs', 'oracles') if data else (
        'contract_version', 'dominance', 'front', 'ordering', 'live_jury_binding')
    if (not _text_fields(fingerprint, fields)
            or (not data and (
                not isinstance(fingerprint.get('axes'), list) or not fingerprint['axes']
                or not all(_text(axis) for axis in fingerprint['axes'])
                or not isinstance(fingerprint.get('fixed_weights'), bool)))):
        errors.append('invalid semantic_fingerprint declaration')
    if not _text(mapping.get('disposition')):
        errors.append('invalid disposition declaration')
    return errors


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
    errors = validate_contract_data(root, mapping)
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
            # PLAN §7 Idem + plan_model K6-5: insert_immutable_checked reads
            # FAIL under Idem.pattern rev 5; R-10 is routed, not earned PASS.
            # Pin this independently of the mapping's mutable prose/revisions.
            if (mapping.get('asset') == 'ka_bhavishya_lekha' and gate == 'Idem'):
                reading = evidence.get('expected_reading')
                if (criteria['Idem.pattern']['revision'] != 5
                        or not _text(reading)
                        or ' '.join(reading.split()) != REGISTRAR_IDEM_READING
                        or evidence.get('verdict', 'FAIL') != 'FAIL'):
                    errors.append('Idem reading contradicts declared current-detector FAIL/R-10 disposition')
            none = {key for key in expected if criteria[key]['detector'] == 'NONE'}
            # §N.8: an offline mapping cannot earn a live detector verdict.
            # (I) INTERPRETATION: pin the complete approved reading, including
            # detector absence; a token/prefix check admits contradictory prose.
            if mapping.get('asset') == 'ka_kshetra':
                reading = KSHETRA_UNMEASURED_READING + (KSHETRA_NO_DETECTOR_READING if none else '')
                if evidence.get('expected_reading') != reading:
                    errors.append(f'unearned Kshetra production reading: {gate}')
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
