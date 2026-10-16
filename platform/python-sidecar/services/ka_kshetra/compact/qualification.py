"""Clause-level evidence for an isolated fixture trial, never an activation gate.

Full corrected-G1/canonical-chart qualification belongs to the cockpit's
independently reviewed child items. This report deliberately binds the actual
base-branch reference source hashes and says what fixtures it measured.
"""
from __future__ import annotations

import hashlib
import math
import random
from pathlib import Path

from services.ka_kshetra import integrator
from services.ka_kshetra.dhara_null import dhara_compute_null
from .compiler import compile_field
from .representation import CompactField
from .null import compute_null, compare_null, NULL_RTOL, NULL_ATOL

FLOAT_ATOL_NATS = 1e-12


def _bits(rows):
    return [(s.index, *(float(v).hex() for v in (s.t_start, s.t_end, s.alpha, s.gamma)),
             s.refinement_depth, s.refinement_exhausted, s.refinement_residual) for s in rows]


def qualify(ev, *, fixture_id: str, expected_knots, replicates: int = 1024) -> dict:
    compiled = compile_field(ev)
    rows = compiled.field.segments()
    repacked = CompactField.from_segments(rows)
    structure = _bits(rows) == _bits(repacked.segments())
    side_checks = []
    for i, s in enumerate(rows):
        for t, side, toward in ((s.t_start, 'right', math.inf), (s.t_end, 'left', -math.inf)):
            error = abs(compiled.field.ln_lambda(t, side=side) - ev.ln_lambda(math.nextafter(t, toward)))
            side_checks.append((error, compiled.bounds[i]))
    rng = random.Random(5102)
    differential = []
    for _ in range(200):
        t = rng.uniform(0, ev.horizon_days)
        i = compiled.field.segment_index(t)
        error = abs(compiled.field.ln_lambda(t) - ev.ln_lambda(t))
        differential.append((error, compiled.bounds[i]))
    intervals = [(0.0, ev.horizon_days)] + [(s.t_start, s.t_end) for s in rows]
    integrals_equal = all(compiled.field.integral(a, b).hex() ==
                          integrator.integrate(rows, a, b).hex() for a, b in intervals)
    reference_null = dhara_compute_null(ev, replicates=replicates)
    candidate_null = compute_null(ev, replicates=replicates)
    # Freeze observations from the reference before comparing. Interior values
    # exercise ranking; the explicit tie probe exercises the >= convention.
    observations = {b: (sum(values) / len(values), values[0])
                    for b, values in reference_null.max_stats.items()}
    null_comparison = compare_null(reference_null, candidate_null, observations=observations)
    clauses = {
        'structural_equality': {'passed': structure, 'claim': 'lossless packing of compiler output; not legacy partition equality'},
        'per_segment_bound': {'passed': compiled.proven, 'max_log_error_bound': max(compiled.bounds),
                              'exhausted_segments': sum(s.refinement_exhausted for s in rows)},
        'one_sided_discontinuities': {'passed': bool(side_checks) and all(e <= b + FLOAT_ATOL_NATS for e, b in side_checks),
                                     'evaluations': len(side_checks), 'max_abs_error_nats': max(e for e, _ in side_checks)},
        'adversarial_switching_peaks': {'passed': bool(expected_knots) and set(expected_knots) <= set(compiled.operator_knots),
                                        'expected_knots': list(expected_knots)},
        'random_differential': {'passed': all(e <= b + FLOAT_ATOL_NATS for e, b in differential),
                                'evaluations': len(differential), 'max_abs_error_nats': max(e for e, _ in differential)},
        'interval_integrals': {'passed': integrals_equal, 'intervals': len(intervals),
                               'claim': 'bitwise equality for the stored representation using existing integrator'},
        'null_statistics': null_comparison,
    }
    failed = [name for name, result in clauses.items() if not result['passed']]
    root = Path(__file__).resolve().parents[1]
    sources = {name: {'path': 'platform/python-sidecar/services/ka_kshetra/' + name,
                      'sha256': hashlib.sha256((root / name).read_bytes()).hexdigest()}
               for name in ('stage4_field.py', 'hazard.py', 'integrator.py', 'dhara_null.py')}
    candidate_sources = {
        path.name: {'path': 'platform/python-sidecar/services/ka_kshetra/compact/' + path.name,
                    'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
        for path in Path(__file__).resolve().parent.glob('*.py')
    }
    return {
        'fixture_id': fixture_id,
        'status': 'failed_with_failing_clause' if failed else 'implemented_and_proven',
        'failed_clauses': failed, 'clauses': clauses, 'reference': sources, 'candidate': candidate_sources,
        'segment_count': len(rows), 'operator_knots': list(compiled.operator_knots),
        'tolerances': {'tau_nats': compiled.tau, 'floating_atol_nats': FLOAT_ATOL_NATS,
                       'null_rtol': NULL_RTOL, 'null_atol': NULL_ATOL, 'tail_ranks': 'exact'},
        'null_replicates': reference_null.replicates, 'null_shift_count': reference_null.shift_count,
    }


def aggregate(results, *, required_fixtures: set[str]) -> dict:
    names = [r['fixture_id'] for r in results]
    census_ok = bool(required_fixtures) and set(names) == required_fixtures and len(names) == len(set(names))
    required_clauses = {
        'structural_equality', 'per_segment_bound', 'one_sided_discontinuities',
        'adversarial_switching_peaks', 'random_differential', 'interval_integrals', 'null_statistics',
    }
    failed = {}
    for result in results:
        clauses = result.get('clauses', {})
        bad = sorted(name for name in required_clauses if clauses.get(name, {}).get('passed') is not True)
        if bad:
            failed[result['fixture_id']] = bad
    if not census_ok:
        failed['fixture_census'] = sorted(required_fixtures - set(names)) or ['empty, duplicate or unexpected fixtures']
    return {
        'schema': 'ky.compact_contract/1', 'item': 'K5-2',
        'status': 'failed_with_failing_clause' if failed else 'implemented_and_proven',
        'scope': 'synthetic numerical fixtures on the actual base-branch G1 formula; no canonical-chart or upstream-completion claim',
        'production_activation': False, 'dense_path_disposition': 'retain',
        'failed_clauses': failed, 'fixtures': results,
    }
