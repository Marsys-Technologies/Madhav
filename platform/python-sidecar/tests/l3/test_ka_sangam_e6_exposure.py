"""Tests for ka_sangam E6 — exposure manifest, outcome record, and binomial gates.

Engine-side only; no DB, no writer, no orchestrator.  Exercises the pure
functions in services/ka_sangam/exposure.py against the D-1/D-2/D-3 rulings.
"""
from __future__ import annotations

import os
import sys
from datetime import date

import pytest

_SIDECAR = os.path.join(os.path.dirname(__file__), "..", "..")
if _SIDECAR not in sys.path:
    sys.path.insert(0, _SIDECAR)

from services.ka_sangam.exposure import (
    PER_STRATUM_N,
    PER_STRATUM_CRITICAL,
    PER_STRATUM_ALPHA,
    PER_STRATUM_POWER,
    INSTRUMENT_N,
    INSTRUMENT_CRITICAL,
    INSTRUMENT_ALPHA,
    INSTRUMENT_POWER,
    NULL_RATE,
    CENSORING_ELEVATED_PCT,
    CENSORING_BLOCK_PCT,
    _binomial_sf,
    find_critical_value,
    compute_power,
    stratum_key,
    infer_domain,
    compute_exposure_manifest,
    build_stratum_outcome,
    evaluate_instrument_outcome,
)


def _window(mode='A', signature_class='CAREER_DIGNITY', kernel_version='separated_v2',
            ws=date(2024, 1, 1), we=date(2024, 6, 1)):
    return {
        'mode': mode,
        'comparability_class': f'ka_sangam/{signature_class}',
        'kernel_version': kernel_version,
        'window_start': ws,
        'window_end': we,
    }


class TestGateConstants:
    """The D-1 triples must satisfy the exact binomial design they name."""

    def test_per_stratum_alpha_and_power(self):
        # alpha = P(X >= 12 | Bin(35, 0.20)) must be ~0.0344
        alpha = _binomial_sf(PER_STRATUM_CRITICAL, PER_STRATUM_N, NULL_RATE)
        assert abs(alpha - PER_STRATUM_ALPHA) < 1e-4
        # power at 0.40 must be ~0.805 (published value is rounded to 3 decimals)
        power = compute_power(PER_STRATUM_N, PER_STRATUM_CRITICAL, 0.40)
        assert abs(power - PER_STRATUM_POWER) < 1e-3

    def test_instrument_alpha_and_power(self):
        alpha = _binomial_sf(INSTRUMENT_CRITICAL, INSTRUMENT_N, NULL_RATE)
        assert abs(alpha - INSTRUMENT_ALPHA) < 1e-4
        power = compute_power(INSTRUMENT_N, INSTRUMENT_CRITICAL, 0.32)
        assert abs(power - INSTRUMENT_POWER) < 1e-3

    def test_find_critical_value_recovers_design(self):
        assert find_critical_value(PER_STRATUM_N, PER_STRATUM_ALPHA) == PER_STRATUM_CRITICAL
        assert find_critical_value(INSTRUMENT_N, INSTRUMENT_ALPHA) == INSTRUMENT_CRITICAL


class TestStratumKey:
    def test_domain_route_method_version(self):
        w = _window(mode='A', signature_class='CAREER_DIGNITY', kernel_version='separated_v2')
        assert stratum_key(w) == ('CAREER', 'A', 'separated_v2')

    def test_unknown_signature_class_becomes_other(self):
        w = _window(signature_class='SOMETHING_ELSE')
        assert stratum_key(w)[0] == 'OTHER'

    def test_legacy_method_version_not_pooled(self):
        w_new = _window(kernel_version='separated_v2')
        w_old = _window(kernel_version='legacy_i16')
        assert stratum_key(w_new) != stratum_key(w_old)


class TestExposureManifest:
    def test_manifest_counts_and_rates(self):
        windows = [
            _window(ws=date(2024, 1, 1), we=date(2024, 6, 1)),   # ~0.416 yr
            _window(ws=date(2024, 6, 1), we=date(2025, 6, 1)),   # ~1.0 yr
            _window(mode='B', ws=date(2024, 1, 1), we=date(2025, 1, 1)),
        ]
        m = compute_exposure_manifest(windows, horizon_start=date(2024, 1, 1),
                                      horizon_end=date(2025, 1, 1))
        assert m.total_windows == 3
        assert abs(m.total_window_years - 2.416) < 0.01
        assert ('CAREER', 'A', 'separated_v2') in m.strata
        assert ('CAREER', 'B', 'separated_v2') in m.strata
        assert m.strata[('CAREER', 'A', 'separated_v2')].window_count == 2
        assert m.strata[('CAREER', 'B', 'separated_v2')].window_count == 1
        assert m.strata[('CAREER', 'A', 'separated_v2')].issuance_rate > 0

    def test_completeness_states(self):
        assert compute_exposure_manifest([], horizon_start=date(2024, 1, 1),
                                         horizon_end=date(2024, 6, 1)).completeness == 'unavailable'
        short = [_window(ws=date(2024, 1, 1), we=date(2024, 6, 1))]
        assert compute_exposure_manifest(short, horizon_start=date(2024, 1, 1),
                                         horizon_end=date(2024, 6, 1)).completeness == 'incomplete'
        long_windows = [_window(ws=date(2024, 1, 1), we=date(2054, 1, 1))]
        assert compute_exposure_manifest(long_windows, horizon_start=date(2024, 1, 1),
                                         horizon_end=date(2054, 1, 1)).completeness == 'complete'

    def test_json_serialisable(self):
        m = compute_exposure_manifest([_window()], horizon_start=date(2024, 1, 1),
                                      horizon_end=date(2025, 1, 1))
        s = m.to_json()
        assert '"CAREER|A|separated_v2"' in s
        assert '"issuance_rate"' in s


class TestStratumOutcome:
    def test_n_excludes_ambiguous_and_censored(self):
        o = build_stratum_outcome(domain='CAREER', route='A', method_version='separated_v2',
                                  hits=10, misses=5, ambiguous=3, censored=2, unobserved=0)
        assert o.n_evaluated == 15
        assert o.total == 20

    def test_hit_rate_interval_and_claim_against_lower_bound(self):
        o = build_stratum_outcome(domain='CAREER', route='A', method_version='separated_v2',
                                  hits=10, misses=5, ambiguous=3, censored=2, unobserved=0)
        assert o.hit_rate_interval == (10/20, 13/20)
        assert o.claim_rate == 10/20

    def test_provisional_insufficient_n(self):
        o = build_stratum_outcome(domain='CAREER', route='A', method_version='separated_v2',
                                  hits=10, misses=10, ambiguous=0, censored=0, unobserved=0)
        assert o.gate_status == 'PROVISIONAL_INSUFFICIENT_N'
        assert o.actual_n == 20

    def test_binomial_gate_passed_when_gate_opens(self):
        # 12 hits in 35 evaluated with no ambiguous/censored passes the per-stratum gate.
        o = build_stratum_outcome(domain='CAREER', route='A', method_version='separated_v2',
                                  hits=PER_STRATUM_CRITICAL, misses=PER_STRATUM_N - PER_STRATUM_CRITICAL,
                                  ambiguous=0, censored=0, unobserved=0)
        assert o.gate_status == 'BINOMIAL_GATE_PASSED'

    def test_below_critical_when_gate_fails(self):
        o = build_stratum_outcome(domain='CAREER', route='A', method_version='separated_v2',
                                  hits=PER_STRATUM_CRITICAL - 1,
                                  misses=PER_STRATUM_N - (PER_STRATUM_CRITICAL - 1),
                                  ambiguous=0, censored=0, unobserved=0)
        assert o.gate_status == 'BELOW_CRITICAL'

    def test_alpha_level_test_uses_actual_n(self):
        # 12 hits in 36 evaluated is NOT significant at level 0.0344
        # (P(X >= 12 | Bin(36, 0.20)) ~= 0.041 > alpha).  The design critical
        # value 12 was computed for n = 35; at any other n the exact p-value
        # against the actual n decides.
        o = build_stratum_outcome(domain='CAREER', route='A', method_version='separated_v2',
                                  hits=12, misses=24, ambiguous=0, censored=0, unobserved=0)
        assert o.n_evaluated == 36
        assert o.gate_status == 'BELOW_CRITICAL'

    def test_censoring_elevated_and_blocked(self):
        # ~10.3% censoring (above the 10% elevated label, below the 20% block);
        # n = 35 meets the design n, so the gate can still pass.
        total = 39
        ambiguous = 4
        hits = 12
        misses = total - hits - ambiguous   # 23 -> n = 35
        o = build_stratum_outcome(domain='CAREER', route='A', method_version='separated_v2',
                                  hits=hits, misses=misses, ambiguous=ambiguous, censored=0, unobserved=0)
        assert o.censoring_rate == pytest.approx(4 / 39)
        assert o.gate_status == 'BINOMIAL_GATE_PASSED'

        # 22.5% censoring blocks regardless of n (n = 31 < 35 here).
        total = 40
        ambiguous = 9
        misses = total - hits - ambiguous   # 19 -> n = 31
        o2 = build_stratum_outcome(domain='CAREER', route='A', method_version='separated_v2',
                                   hits=hits, misses=misses, ambiguous=ambiguous, censored=0, unobserved=0)
        assert o2.censoring_rate == pytest.approx(0.225, abs=1e-9)
        assert o2.gate_status == 'CENSORING_BLOCKED'

    def test_synthetic_chart_is_not_eligible(self):
        o = build_stratum_outcome(domain='CAREER', route='A', method_version='separated_v2',
                                  hits=PER_STRATUM_CRITICAL, misses=PER_STRATUM_N - PER_STRATUM_CRITICAL,
                                  ambiguous=0, censored=0, unobserved=0,
                                  is_synthetic=True)
        assert o.gate_status == 'NOT_ELIGIBLE'

    def test_evaluation_ineligible_is_not_eligible(self):
        o = build_stratum_outcome(domain='CAREER', route='A', method_version='separated_v2',
                                  hits=PER_STRATUM_CRITICAL, misses=PER_STRATUM_N - PER_STRATUM_CRITICAL,
                                  ambiguous=0, censored=0, unobserved=0,
                                  evaluation_eligible=False)
        assert o.gate_status == 'NOT_ELIGIBLE'

    def test_unavailable_when_no_outcomes(self):
        o = build_stratum_outcome(domain='CAREER', route='A', method_version='separated_v2')
        assert o.gate_status == 'UNAVAILABLE'
        assert o.total == 0


class TestInstrumentOutcome:
    def test_pools_only_one_method_version(self):
        s1 = build_stratum_outcome(domain='CAREER', route='A', method_version='separated_v2',
                                   hits=15, misses=15)
        s2 = build_stratum_outcome(domain='HEALTH', route='B', method_version='separated_v2',
                                   hits=15, misses=15)
        s3 = build_stratum_outcome(domain='CAREER', route='A', method_version='legacy_i16',
                                   hits=10, misses=10)
        # Only the two separated_v2 strata pool.
        io = evaluate_instrument_outcome([s1, s2], method_version='separated_v2')
        assert io.method_version == 'separated_v2'
        assert io.n_evaluated == 60
        assert io.hits == 30
        assert io.gate_status == 'PROVISIONAL_INSUFFICIENT_N'  # 60 < 100

    def test_instrument_gate_passed(self):
        strata = [
            build_stratum_outcome(domain='CAREER', route='A', method_version='separated_v2',
                                  hits=15, misses=20),
            build_stratum_outcome(domain='HEALTH', route='B', method_version='separated_v2',
                                  hits=15, misses=20),
            build_stratum_outcome(domain='RELATIONSHIP', route='A', method_version='separated_v2',
                                  hits=5, misses=25),
        ]
        io = evaluate_instrument_outcome(strata, method_version='separated_v2')
        assert io.n_evaluated == 100
        assert io.hits == 35
        assert io.gate_status == 'BINOMIAL_GATE_PASSED'

    def test_instrument_unavailable(self):
        io = evaluate_instrument_outcome([])
        assert io.gate_status == 'UNAVAILABLE'
        assert io.total == 0
