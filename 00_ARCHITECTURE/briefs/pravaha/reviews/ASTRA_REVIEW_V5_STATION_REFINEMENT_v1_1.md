VERDICT: ACCEPT_WITH_AMENDMENTS

Reviewed `944ccf22c250b6ebd0507c18d0f23438efceade4…bd93c03f7ffc6448e1243146832ac61f0f20fea0`. The round-1 runtime defects are corrected. Two amendments remain:

1. **P2 — The numerical regression test still passes the withdrawn arc design.**  
   [station_golden_matrix.py:34](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-stn2/platform/python-sidecar/tests/l3/gochara/station_golden_matrix.py:34) constructs an index directly, without exercising the writer’s refinement wiring. Its digest at line 45 omits occurrence ordinals and contact IDs; the target matrix also omits `5.39°`.

   **Reproduced in memory:** loading round-1 `arcs.py` from `54747b55c` passes the new complete golden comparison. Supplying its production refiner then reproduces **111 → 109 roots** and the **70.5146-second orb-exit displacement**. The separate static API test catches that literal implementation, but the required numerical test does not.

   Amend the regression to exercise production index wiring and `solve_point_edges`, comparing `(ordinal, contact_id, t_exact, t_in, t_out)` against merge-base results, including both Mercury cases.

2. **P3 — The refiner docstring still describes the audit spread as stored uncertainty.**  
   [knots.py:264](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-stn2/platform/python-sidecar/services/gochara_kernel/knots.py:264) says stored `delta_t` is the larger of fit uncertainty and speed disagreement. That is now incorrect.

   At Jupiter JD `2453008.478495535`, `StationFix.delta_t_days` represents **0.250905 seconds**, whereas storage correctly uses **10 seconds**. A caller following this docstring could reintroduce false precision. Describe the returned spread as diagnostic and point explicitly to `station_delta_t_bound_days()`.

The requested checks otherwise support acceptance:

- **Computation:** `arcs.py`, `contacts.py`, `episodes.py`, `record_store.py`, and the v5 writer are byte-identical to the merge base. Mercury `295.8493268245402°` produces **111 roots**, including both restored crossings on 2074-01-24. The `5.39°` exit remains exactly **2076-05-02 17:08:08.395715 UTC**.
- **Station identity and storage:** all **1,066 station ID derivations remain unchanged**. [substrate.py:554](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-stn2/platform/python-sidecar/services/gochara_kernel/substrate.py:554) retains the spline longitude for identity and storage, stores `jd_to_utc(fix.jd)` as `t_exact`, and uses `swiss_station_fit_domain_bound`. The mixed evaluations are documented. Their largest measured longitude discrepancy is **0.040352 arcsecond**, within the retained **1-arcsecond `delta_lambda`**; this interpolation discrepancy must not be confused with the much smaller displacement across the time gap.
- **Bound and gap:** the full-domain test passed with all nine comparison estimators present at every station. The bounds at [knots.py:223](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-stn2/platform/python-sidecar/services/gochara_kernel/knots.py:223) cover the measured disagreements with more than the required factor-of-two margin:

| Body | Stations | Maximum estimator disagreement | Stored bound | Maximum spline gap |
|---|---:|---:|---:|---:|
| Mars | 82 | 1.383 s | 4 s | 1.842 s |
| Mercury | 548 | 0.468 s | 2 s | 16.735 s |
| Jupiter | 159 | 3.684 s | 10 s | 0.984 s |
| Venus | 109 | 1.539 s | 6 s | 2.590 s |
| Saturn | 168 | 1.355 s | 4 s | 0.632 s |

- **Guard D:** [substrate.py:493](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-stn2/platform/python-sidecar/services/gochara_kernel/substrate.py:493) filters by station kind, convention and old regime, then refuses by name. Empty-substrate simulations passed with both tuple and dictionary count rows.
- **Cost:** refinement runs once per station during the single body substrate step; record substeps no longer refine. Measured **219 Swiss calls/station**, or **233,454 calls** for the domain. There is no cross-build memo; retries recompute.
- **Pins and scope:** implementation lock, all **125 writer digests**, changed census hashes and Swiss-state ownership inventory match. No unrelated functional change found.

**Verification:** all 15 new test cases and 36 selected existing test functions passed through direct invocation without filesystem-writing fixtures.

**Not verified:** actual database behavior or production emptiness, full CI, cross-platform determinism, or an absolute astronomical error bound beyond the pinned-domain estimator envelope. No files modified; no database or network accessed.

