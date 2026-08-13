"""DHARA engine version flag.

Controls which segment-construction engine ka_kshetra uses during a field build.

Values:
    'sampled'  — current adaptive-bisection engine (DEFAULT, UNTOUCHED).
                 All existing code in integrator.py, hazard.py, stage4_field.py,
                 and stage5_null.py is used as-is. No DHARA code is reached.
    'analytic' — DHARA event-driven sweep engine (Deterministic Hazard-rate
                 Analytic Recomputation Architecture). Replaces
                 integrator.build_segments() with an event-driven sweep over the
                 exact knot set K = sort(K_c UNION K_e), exploiting the piecewise
                 structure of the hazard formula to eliminate unnecessary
                 midpoint evaluations on the ~90-95% of intervals that are
                 exactly log-linear (non-suppression).

Rollout rules (DHARA_DESIGN_v1_0.md §8.2):
    1. The 'sampled' code path is UNTOUCHED. All DHARA code is additive —
       new modules, new functions. No existing function is modified.
    2. The flag-flip ('sampled' -> 'analytic') is a SEPARATE commit, distinct
       from any implementation PR. Commit message:
           feat(ka_kshetra): flip ENGINE_VERSION sampled -> analytic (DHARA)
    3. _RESUME_VERSION bumps on the flag-flip commit, not on implementation
       commits, so a build in progress under 'sampled' is not silently
       switched mid-run.
    4. All implementation lanes (S3) are merged to the integration branch
       BEFORE the flag-flip commit is authored.

Stage routing (§8.4):
    from services.ka_kshetra.engine_config import ENGINE_VERSION

    if ENGINE_VERSION == 'analytic':
        from services.ka_kshetra.dhara_sweep import dhara_build_segments
        segments = dhara_build_segments(evaluator)
    else:
        segments = evaluator.build_segments()

Authority: DHARA_DESIGN_v1_0.md §8.1–§8.4
"""

ENGINE_VERSION: str = 'sampled'
