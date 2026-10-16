"""Reproducible fixture evidence. Exit 1 means the numerical contract failed.

Run from python-sidecar: python -m tests.l3.ka_kshetra.compact.run_contract_trial
--output <job-folder>/COMPACT_CONTRACT_RESULT.json
"""
import argparse
import json
from pathlib import Path

from services.ka_kshetra.compact.qualification import aggregate, qualify
from .fixtures import evaluator, primitive, curved_evaluator, long_horizon_evaluator


def build_report():
    cases = [
        ('corrected_clock', evaluator(), (0, 16, 32)),
        ('max_switch_and_peak', evaluator([
            primitive('contact_moon_ref', ((0, .75), (32, 0))),
            primitive('contact_moon_ref', ((0, 0), (32, .25))),
            primitive('contact_lagna_ref', ((0, 0), (7, 1), (32, 0))),
        ], extra=(3, 9, 23)), (0, 3, 7, 9, 16, 23, 24, 32)),
        ('min_crossing', evaluator([
            primitive('contact_moon_ref', ((0, 0), (32, 1))),
            primitive('contact_lagna_ref', ((0, 1), (32, 0))),
        ], weights={'beta:x3': 1.0}, clock=False), (0, 16, 32)),
        ('steps_and_support_edges', evaluator([
            primitive('contact_moon_ref', ((2, .2), (8, .2), (8, .9), (14, .9))),
        ]), (0, 2, 8, 14, 16, 32)),
        ('curved_suppression', curved_evaluator(), (0, 16, 32)),
        ('long_horizon', long_horizon_evaluator(), (0, 173, 421, 548, 713, 1096)),
        ('shift_seam', evaluator([
            primitive('contact_moon_ref', ((0, .4), (4, 1), (10, .2))),
        ], extra=(30,)), (0, 4, 10, 16, 30, 32)),
    ]
    # Exercise an actual wrapped primitive, with both seam limits retained.
    shifted = cases[-1][1]
    shifted.envelopes = shifted.envelopes.circular_shift(5)
    cases[-1] = ('shift_seam', shifted, (0, 5, 16, 27, 30, 31, 32))
    report = aggregate([
        qualify(ev, fixture_id=name, expected_knots=knots) for name, ev, knots in cases
    ], required_fixtures={name for name, _, _ in cases})
    report['activation_gates'] = [
        'D-VC completed and approved by the cockpit',
        'independently reviewable K5-2 child items and parent join recorded by the cockpit',
        'all numerical clauses on the corrected upstream G1/canonical workload, including null statistics',
        'D-COMPACT decision recorded by the cockpit; consumer item reviewed and landed',
    ]
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    report = build_report()
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({'status': report['status'], 'failed_clauses': report['failed_clauses']}))
    return 0 if report['status'] == 'implemented_and_proven' else 1


if __name__ == '__main__':
    raise SystemExit(main())
