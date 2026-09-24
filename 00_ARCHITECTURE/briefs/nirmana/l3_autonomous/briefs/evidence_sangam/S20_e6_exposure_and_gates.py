"""E6 evaluation boundary — exposure manifest + binomial gate detector.
Proposition: services/ka_sangam/exposure.py reproduces the D-1 gate design
EXACTLY (per-stratum n=20, critical>=8, alpha=0.0321; instrument n=50,
critical>=16, alpha=0.0308 — re-set 2026-09-24 on the native's instruction; all verified against exact binomial tails);
strata key on (domain x route x method_version) and never pool method
versions; per D-2, n excludes ambiguous/censored while the rate denominator
includes them and the claim is the lower bound hits/total; censoring >20%
blocks regardless of n; synthetic/ineligible charts are NOT_ELIGIBLE (D-3);
a passed gate reads BINOMIAL_GATE_PASSED, never EMPIRICALLY_EVALUATED; and
the ka_sangam writer attaches the exposure manifest JSON to
WriterResult.notes in BOTH the near and lifetime substeps."""
from _common import *
from datetime import date

from services.ka_sangam.exposure import (
    PER_STRATUM_N, PER_STRATUM_CRITICAL, PER_STRATUM_ALPHA,
    INSTRUMENT_N, INSTRUMENT_CRITICAL, INSTRUMENT_ALPHA,
    NULL_RATE, CENSORING_BLOCK_PCT,
    _binomial_sf, find_critical_value, compute_power,
    stratum_key, infer_domain, compute_exposure_manifest,
    build_stratum_outcome, evaluate_instrument_outcome,
)

head("S20 — E6 exposure manifest + evaluation-boundary gates (D-1/D-2/D-3)")


def _window(mode='A', sig='CAREER_DIGNITY', kv='separated_v2',
            ws=date(2024, 1, 1), we=date(2024, 6, 1)):
    return {'mode': mode, 'comparability_class': f'ka_sangam/{sig}',
            'kernel_version': kv, 'window_start': ws, 'window_end': we}


# Exact binomial reproduction of the published D-1 design numbers.
alpha_s = _binomial_sf(PER_STRATUM_CRITICAL, PER_STRATUM_N, NULL_RATE)
alpha_i = _binomial_sf(INSTRUMENT_CRITICAL, INSTRUMENT_N, NULL_RATE)
power_s = compute_power(PER_STRATUM_N, PER_STRATUM_CRITICAL, 0.50)
power_i = compute_power(INSTRUMENT_N, INSTRUMENT_CRITICAL, 0.40)

# Stratum discipline.
k_new = stratum_key(_window(kv='separated_v2'))
k_old = stratum_key(_window(kv='legacy_i16'))

# Exposure manifest.
m = compute_exposure_manifest(
    [_window(), _window(ws=date(2024, 6, 1), we=date(2025, 6, 1)),
     _window(mode='B', ws=date(2024, 1, 1), we=date(2025, 1, 1))],
    horizon_start=date(2024, 1, 1), horizon_end=date(2025, 1, 1))
m_empty = compute_exposure_manifest([], horizon_start=date(2024, 1, 1),
                                    horizon_end=date(2024, 6, 1))
m_short = compute_exposure_manifest([_window()], horizon_start=date(2024, 1, 1),
                                    horizon_end=date(2024, 6, 1))
m_long = compute_exposure_manifest([_window(ws=date(2024, 1, 1), we=date(2054, 1, 1))],
                                   horizon_start=date(2024, 1, 1), horizon_end=date(2054, 1, 1))

# Outcome records.
o_mixed = build_stratum_outcome(domain='CAREER', route='A', method_version='separated_v2',
                                hits=10, misses=5, ambiguous=3, censored=2)
o_pass = build_stratum_outcome(domain='CAREER', route='A', method_version='separated_v2',
                               hits=8, misses=12)
o_below = build_stratum_outcome(domain='CAREER', route='A', method_version='separated_v2',
                                hits=7, misses=13)
o_low_n = build_stratum_outcome(domain='CAREER', route='A', method_version='separated_v2',
                                hits=5, misses=5)
o_cens = build_stratum_outcome(domain='CAREER', route='A', method_version='separated_v2',
                               hits=8, misses=10, ambiguous=6)   # 25% censoring, n=18
o_synth = build_stratum_outcome(domain='CAREER', route='A', method_version='separated_v2',
                                hits=8, misses=12, is_synthetic=True)
o_empty = build_stratum_outcome(domain='CAREER', route='A', method_version='separated_v2')
io_pass = evaluate_instrument_outcome(
    [build_stratum_outcome(domain='CAREER', route='A', method_version='separated_v2',
                           hits=8, misses=10),
     build_stratum_outcome(domain='HEALTH', route='B', method_version='separated_v2',
                           hits=7, misses=11),
     build_stratum_outcome(domain='RELATIONSHIP', route='A', method_version='separated_v2',
                           hits=3, misses=11)],
    method_version='separated_v2')

# Writer wiring (static): both substeps attach the manifest to notes.
writer_near = grep('pipeline/orchestrator/writers/ka_sangam.py',
                   r'def _substep_near')
writer_lt = grep('pipeline/orchestrator/writers/ka_sangam.py',
                 r'def _substep_lifetime')
manifest_calls = grep('pipeline/orchestrator/writers/ka_sangam.py',
                      r'compute_exposure_manifest\(')
# Behavioural, not expression-pinned: assert the SYMBOL is imported from the
# exposure module, not that the import line has one exact shape. The previous
# pattern pinned a single-name import and went red when `build_scan_coverage`
# joined it — a legitimate change failing a correct build, the S3 defect class.
manifest_import = grep('pipeline/orchestrator/writers/ka_sangam.py',
                       r'from services\.ka_sangam\.exposure import .*compute_exposure_manifest')
# Assert the manifest REACHES notes in both substeps, however it is composed.
# It is now carried under the named key 'exposure_manifest' alongside the scan
# coverage object (synergy audit #4); pinning `notes=manifest.to_json()` would
# forbid composing the two, which is the opposite of what this detector wants.
notes_json = grep('pipeline/orchestrator/writers/ka_sangam.py',
                  r'notes=(manifest\.to_json\(\)|_notes_with_coverage\()')
manifest_in_notes = grep('pipeline/orchestrator/writers/ka_sangam.py',
                         r"'exposure_manifest':")

if NEG:
    # Inverted expectations: the detector must fail on correct code.
    prop("per-stratum alpha reproduces 0.0321", abs(alpha_s - PER_STRATUM_ALPHA) >= 1e-4)
    prop("instrument alpha reproduces 0.0308", abs(alpha_i - INSTRUMENT_ALPHA) >= 1e-4)
    prop("find_critical_value recovers 8 @ n=20", find_critical_value(20, PER_STRATUM_ALPHA) != 8)
    prop("find_critical_value recovers 16 @ n=50", find_critical_value(50, INSTRUMENT_ALPHA) != 16)
    prop("stratum power ~0.868 at 0.50", abs(power_s - 0.868) >= 1e-3)
    prop("instrument power ~0.904 at 0.40", abs(power_i - 0.904) >= 1e-3)
    prop("method versions never pool", k_new == k_old)
    prop("domain inferred from signature class", infer_domain('CAREER_DIGNITY') != 'CAREER')
    prop("manifest counts windows per stratum", m.strata[('CAREER', 'A', 'separated_v2')].window_count != 2)
    prop("completeness: 0 exposure unavailable", m_empty.completeness != 'unavailable')
    prop("completeness: <30y incomplete", m_short.completeness != 'incomplete')
    prop("completeness: >=30y complete", m_long.completeness != 'complete')
    prop("n excludes ambiguous+censored", o_mixed.n_evaluated != 15)
    prop("claim is the lower bound hits/total", o_mixed.claim_rate != 10 / 20)
    prop("8 hits in 20 passes the stratum gate", o_pass.gate_status != 'BINOMIAL_GATE_PASSED')
    prop("7 hits in 20 is below critical", o_below.gate_status != 'BELOW_CRITICAL')
    prop("n=10 is provisional insufficient", o_low_n.gate_status != 'PROVISIONAL_INSUFFICIENT_N')
    prop("25% censoring blocks regardless of n", o_cens.gate_status != 'CENSORING_BLOCKED')
    prop("synthetic chart not eligible", o_synth.gate_status != 'NOT_ELIGIBLE')
    prop("empty stratum unavailable", o_empty.gate_status != 'UNAVAILABLE')
    prop("gate never claims EMPIRICALLY_EVALUATED",
         o_pass.gate_status == 'EMPIRICALLY_EVALUATED' or io_pass.gate_status == 'EMPIRICALLY_EVALUATED')
    prop("instrument gate pools one method_version", io_pass.n_evaluated != 50 or io_pass.gate_status != 'BINOMIAL_GATE_PASSED')
    prop("writer defines near substep", not writer_near)
    prop("writer defines lifetime substep", not writer_lt)
    prop("writer imports compute_exposure_manifest", not manifest_import)
    prop("writer calls compute_exposure_manifest in both substeps", len(manifest_calls) != 2)
    prop("writer attaches manifest JSON to notes in both substeps",
         len(notes_json) != 2 or not manifest_in_notes)
else:
    prop("per-stratum alpha reproduces 0.0321", abs(alpha_s - PER_STRATUM_ALPHA) < 1e-4,
         f"alpha={alpha_s:.6f}")
    prop("instrument alpha reproduces 0.0308", abs(alpha_i - INSTRUMENT_ALPHA) < 1e-4,
         f"alpha={alpha_i:.6f}")
    prop("find_critical_value recovers 8 @ n=20", find_critical_value(20, PER_STRATUM_ALPHA) == 8)
    prop("find_critical_value recovers 16 @ n=50", find_critical_value(50, INSTRUMENT_ALPHA) == 16)
    prop("stratum power ~0.868 at 0.50", abs(power_s - 0.868) < 1e-3, f"power={power_s:.6f}")
    prop("instrument power ~0.904 at 0.40", abs(power_i - 0.904) < 1e-3, f"power={power_i:.6f}")
    prop("method versions never pool", k_new != k_old)
    prop("domain inferred from signature class", infer_domain('CAREER_DIGNITY') == 'CAREER')
    prop("manifest counts windows per stratum", m.strata[('CAREER', 'A', 'separated_v2')].window_count == 2)
    prop("completeness: 0 exposure unavailable", m_empty.completeness == 'unavailable')
    prop("completeness: <30y incomplete", m_short.completeness == 'incomplete')
    prop("completeness: >=30y complete", m_long.completeness == 'complete')
    prop("n excludes ambiguous+censored", o_mixed.n_evaluated == 15 and o_mixed.total == 20)
    prop("claim is the lower bound hits/total", o_mixed.claim_rate == 10 / 20
         and o_mixed.hit_rate_interval == (10 / 20, 13 / 20))
    prop("8 hits in 20 passes the stratum gate", o_pass.gate_status == 'BINOMIAL_GATE_PASSED')
    prop("7 hits in 20 is below critical", o_below.gate_status == 'BELOW_CRITICAL')
    prop("n=10 is provisional insufficient", o_low_n.gate_status == 'PROVISIONAL_INSUFFICIENT_N')
    prop("25% censoring blocks regardless of n", o_cens.gate_status == 'CENSORING_BLOCKED')
    prop("synthetic chart not eligible", o_synth.gate_status == 'NOT_ELIGIBLE')
    prop("empty stratum unavailable", o_empty.gate_status == 'UNAVAILABLE')
    prop("gate never claims EMPIRICALLY_EVALUATED",
         o_pass.gate_status != 'EMPIRICALLY_EVALUATED' and io_pass.gate_status != 'EMPIRICALLY_EVALUATED')
    prop("instrument gate pools one method_version",
         io_pass.n_evaluated == 50 and io_pass.hits == 18
         and io_pass.gate_status == 'BINOMIAL_GATE_PASSED')
    prop("writer defines near substep", bool(writer_near))
    prop("writer defines lifetime substep", bool(writer_lt))
    prop("writer imports compute_exposure_manifest", bool(manifest_import))
    prop("writer calls compute_exposure_manifest in both substeps", len(manifest_calls) == 2,
         f"{len(manifest_calls)} call sites (near + lifetime)")
    prop("writer attaches manifest JSON to notes in both substeps",
         len(notes_json) == 2 and bool(manifest_in_notes),
         f"{len(notes_json)} substeps; manifest carried under a named key")

done("POST-FIX BEHAVIOUR")
