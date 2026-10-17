"""Whole-layer independent golden comparisons; no default production oracle.

(I) INTERPRETATION: upstream writer owners register reviewed independent
comparisons here before enablement. Missing oracles REFUSE, never earn PASS.
Tests register real SQL-backed fixture oracles, not production workloads.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import inspect
import json
from pathlib import Path
import re
from typing import Callable

from services.kala_core.verify import VerificationRefused


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


@dataclass(frozen=True)
class GoldenCheck:
    check_id: str
    # Returns {grain: (independently recomputed expected, observed candidate)}.
    compare: Callable


CHECKS: dict[str, tuple[GoldenCheck, ...]] = {}


def checks_digest() -> str:
    """Bind the reviewed checker source files as well as the registered identities.

    The reviewed executor commit also binds their imported implementation closure.
    No request may supply executable code, a module name or an expected value.
    """
    entries = []
    for writer, checks in sorted(CHECKS.items()):
        for check in checks:
            path = inspect.getsourcefile(check.compare)
            if not path:
                raise VerificationRefused('semantic checker must have reviewed file source')
            entries.append((writer, check.check_id, check.compare.__module__, check.compare.__qualname__,
                            hashlib.sha256(Path(path).read_bytes()).hexdigest()))
    entries.append(('publication_checks', hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))
    return digest(entries)


class ReadOnlyReader:
    """Only one prepared SELECT per oracle call; no connection/commit API."""
    def __init__(self, conn):
        self._conn = conn

    def execute(self, query, params=()):
        if not isinstance(query, str) or not re.match(r'\s*SELECT\b', query, re.I) or '\\' in query:
            raise VerificationRefused('golden check must use one SELECT')
        return self._conn.execute(query, params, prepare=True)


def semantic_binding(conn, candidate, binding: dict, semantic_source: str) -> dict:
    if not re.fullmatch(r'[0-9a-f]{64}', semantic_source or '') or semantic_source != checks_digest():
        raise VerificationRefused('semantic source pin differs from reviewed check source')
    run = binding['run']
    plan = binding['grains_by_writer']
    writers = []
    # The plan was validated by the FROZEN parser; never read mutable registry code pins.
    codes = {asset['asset_id']: asset['expected_code_digest'] for asset in run['plan_manifest']['assets']}
    inputs = {key: (vector, state) for key, vector, state in conn.execute(
        'SELECT grain_key, input_vector, result_state FROM kala_layer_candidate_grain '
        'WHERE chart_id=%s AND generation=%s ORDER BY grain_key',
        (candidate.chart_id, candidate.generation)).fetchall()}
    for writer in run['plan']:
        checks = CHECKS.get(writer)
        if not checks or len({check.check_id for check in checks}) != len(checks):
            raise VerificationRefused('every writer requires distinct independent golden checks')
        if any(not check.check_id for check in checks):
            raise VerificationRefused('semantic check identity is required')
        writers.append(dict(writer=writer, code_digest=codes[writer],
                            grains=[dict(grain=key, input_vector=inputs[key][0], result_state=inputs[key][1])
                                    for key in sorted(plan[writer])],
                            checks=[check.check_id for check in checks]))
    return dict(schema='kala.semantic/1', chart_id=candidate.chart_id, generation=candidate.generation,
                build_id=candidate.build_id, plan_manifest_digest=run['plan_manifest_digest'],
                semantic_source=semantic_source, writers=writers)


def semantic_evidence(conn, candidate, binding: dict, semantic_source: str) -> dict:
    """Execute ALL checks for ALL writers/grains before producing evidence."""
    evidence = semantic_binding(conn, candidate, binding, semantic_source)
    reader = ReadOnlyReader(conn)
    measured = []
    for writer in evidence['writers']:
        grains = tuple(row['grain'] for row in writer['grains'])
        for check in CHECKS[writer['writer']]:
            values = check.compare(reader, candidate, grains)
            if not isinstance(values, dict) or set(values) != set(grains):
                raise VerificationRefused('golden check must compare every planned grain exactly')
            for grain in grains:
                pair = values[grain]
                if not isinstance(pair, (tuple, list)) or len(pair) != 2 or pair[0] is None or pair[1] is None:
                    raise VerificationRefused('golden comparison is unavailable')
                expected, observed = map(digest, pair)
                if expected != observed:
                    raise VerificationRefused('independent golden comparison failed')
                measured.append(dict(writer=writer['writer'], grain=grain, check_id=check.check_id,
                                     expected_sha256=expected, observed_sha256=observed))
    return dict(binding=evidence, comparisons=measured)


def require_semantic_receipt(conn, candidate, binding, semantic_source, receipt):
    """Publication checks the immutable verifier's exact source/build/grain binding."""
    expected = semantic_binding(conn, candidate, binding, semantic_source)
    if not isinstance(receipt, dict) or receipt.get('binding') != expected:
        raise VerificationRefused('semantic verification binding is absent or stale')
    comparisons = receipt.get('comparisons')
    required = {(writer['writer'], grain['grain'], check) for writer in expected['writers']
                for grain in writer['grains'] for check in writer['checks']}
    if not isinstance(comparisons, list) or len(comparisons) != len(required):
        raise VerificationRefused('semantic verification comparisons are incomplete')
    observed = set()
    for comparison in comparisons:
        if not isinstance(comparison, dict):
            raise VerificationRefused('semantic verification comparison must be an object')
        identity = tuple(comparison.get(key) for key in ('writer', 'grain', 'check_id'))
        expected_sha = comparison.get('expected_sha256')
        if not re.fullmatch(r'[0-9a-f]{64}', expected_sha or '') or expected_sha != comparison.get('observed_sha256'):
            raise VerificationRefused('semantic verification golden comparison failed')
        observed.add(identity)
    if observed != required:
        raise VerificationRefused('semantic verification omitted a writer or grain')
