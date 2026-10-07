VERDICT: REJECT

Reviewed `3d372868…HEAD` at `54747b55c912a1f8e2b652ba0e40e97aba1cfc7c`. The v5 call sites share the refined station value, but contact completeness and stability do not hold.

1. **P1 — Moving the station boundary can delete real crossings and renumber subsequent contacts.**

   [arcs.py:293](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-stn/platform/python-sidecar/services/gochara_kernel/arcs.py:293) replaces station times, while lines 311–312 and 336–337 still evaluate the original spline for the endpoint longitudes. The segment can therefore contain its old spline extremum internally, contradicting its monotonicity assumption. Endpoint-only range selection at [arcs.py:184](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-stn/platform/python-sidecar/services/gochara_kernel/arcs.py:184) can exclude genuine candidates before Swiss refinement runs.

   **Reproduced with the pinned ephemeris, full 1998–2085 domain:**

   - Mercury conjunction target: `295.8493268245402°`.
   - Station moves from JD `2478597.1681910395` to `2478597.168384737`: **16.7355 seconds**.
   - Old index finds Swiss-refined crossings on **2074-01-24 at 15:52:45.436421 and 16:12:11.413521 UTC**.
   - New index finds neither. Full-domain root count changes **111 → 109**.

   Both old roots have Swiss longitude residuals below `2e-13°`. This is actual contact loss. Because [record_store.py:264](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-stn/platform/python-sidecar/services/gochara_kernel/record_store.py:264) assigns ordinals from the resulting ordered list, later crossings also receive different ordinals/contact identities.

   Candidate bounds and solving must remain complete around refined extrema. Merely replacing the boundary time is insufficient.

2. **P1 — Existing station rows are not corrected or superseded; rebuilding creates additional identities.**

   [substrate.py:538](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-stn/platform/python-sidecar/services/gochara_kernel/substrate.py:538) now feeds the Swiss longitude into the station’s identity-bearing target. [targets.py:96](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-stn/platform/python-sidecar/services/gochara_kernel/targets.py:96) preserves its full float precision.

   **All 1,066 station targets changed in my full-domain comparison.** For example, the first 1998 Mercury station changes:

   - Target: `point:357.66380277375407` → `point:357.6638059572209`.
   - Event ID: `264347b0-bb4c-8597-bdb6-a5f6fe940696` → `1aec6767-08f5-8190-a4c0-2b289da090e6`.

   The convention remains unchanged. On a substrate already built by the base revision, [substrate.py:423](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-stn/platform/python-sidecar/services/gochara_kernel/substrate.py:423) inserts another event without `supersedes_event_id`; the old, falsely precise station remains. The existing schema already provides a correction/supersession mechanism: [migration 1153:775](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-stn/platform/migrations/1153_gochara_sky_event_substrate.sql:775).

   This needs an explicit correction path or an enforced fresh-substrate precondition. The “identities unchanged” claim is false for station events.

3. **P2 — Ordinary orb boundaries move, sometimes farther than the station correction; the stability test misses this.**

   Shifting arc endpoints changes the bisection brackets in [record_store.py:202](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-stn/platform/python-sidecar/services/gochara_kernel/record_store.py:202). That solver returns the first midpoint within angular tolerance, so a small bracket change can change its stopping iteration.

   **Reproduced:** Mercury conjunction at `5.39°`, exact crossing JD `2479423.8297482235`. Its ordinary orb exit changes from **2076-05-02 17:08:08.395715** to **17:09:18.910319 UTC**: **70.5146 seconds**. This endpoint is not a station seam.

   The test at [test_station_refine.py:133](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-stn/platform/python-sidecar/tests/l3/gochara/test_station_refine.py:133) compares segment endpoints and fixed-grid roots, never actual point-contact spans. It cannot establish its stated “spans move only at station seams” claim.

The refinement itself has changed from the description supplied. [knots.py:249](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-stn/platform/python-sidecar/services/gochara_kernel/knots.py:249) bisects the sign of Swiss sidereal longitudinal speed over **±1 day**, stopping at width `≤1e-4 day`—15 iterations with the default bracket. It then samples 201 points, fits longitude with a cubic over ±0.05 day, and selects a stationary point. Quadratic speed fits over four windows provide an uncertainty cross-check.

Same-sign bracket endpoints raise `StationRefinementError`; this also refuses a bracket containing two reversals. All sampled real stations were separated by at least **19.7585 days**, so that ambiguity did not arise. Sun and both mean nodes had no stations and incurred no refinement calls. Stored longitude is freshly evaluated at the returned instant.

The old `1e-9 day` precision claim is removed. The new `delta_t` is `max(3σ longitude-fit error, speed-fit disagreement, 1e-9)`, **not a certified bisection bound**. I could not establish that it bounds the actual station error throughout the domain. Extending the test’s own quartic comparison beyond its first six stations produces a Jupiter disagreement of **3.6827 seconds versus reported uncertainty 0.2509 seconds** at JD `2453008.478495535`. Wider-window estimates themselves proved sensitive, so this does not establish which estimator is correct; the precision qualification remains unresolved.

The station-consumer trace is:

| Consumer | Result |
|---|---|
| Arc/segment boundaries | Refined times; original spline evaluator remains—the P1 inconsistency above. |
| Episodes | Station proximity and station-containing intervals consume `index.stations`: [episodes.py:192](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-stn/platform/python-sidecar/services/gochara_kernel/episodes.py:192), lines 357–358. |
| Substrate rows | Consume refined time, longitude and uncertainty directly. |
| v5 record-store spans | Writer supplies a refined index at [ka_gochara_v5.py:1115](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-stn/platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py:1115); spans inherit its arc boundaries. |
| Window/member verifier | Independently locates reversals using finite-difference longitude: [window_verifier.py:671](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-stn/platform/python-sidecar/services/gochara_kernel/window_verifier.py:671). Intentionally independent. |
| Contact verifier | Independently reconstructs and compares interval unions: [contact_certify.py:172](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-stn/platform/python-sidecar/services/gochara_kernel/contact_certify.py:172). |

Unrefined construction remains in `lifecycle.py:58/76`, legacy `step06_enumerate_episodes.py:1100`, `ka_moorti_nirnaya/writer.py:231`, and the Moon paths. These do not feed the reviewed v5 station rows/record-phase index. `stations_spline` has no production computational consumer.

**Cost:** 1,066 stations × **219 Swiss calls = 233,454 additional calls** per complete substrate build. Refinement/index construction took approximately 13.3 seconds locally. The writer’s cache is local to `_run_record_phase` ([line 1109](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-stn/platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py:1109)); each record substep repeats refinement for the bodies it needs. Repeat checks were deterministic in this environment.

**Verification:** 14 new cases and 30 existing seam/wrap test functions passed, executed directly without filesystem-writing pytest fixtures. The Saturn abutment test also passed with refinement injected. In-memory no-op-refinement and false-precision mutations were caught. The implementation lock, five changed writer digests, and census hashes matched. Runtime input-vector geometry/evaluation digests change as expected; window digest, convention and frozen golden files are unchanged. No unrelated functional change found.

**Not verified:** database upgrade behavior against actual stored rows, database-backed integration tests, full CI, cross-platform numerical determinism, or a certified absolute station-error bound. No files modified; no database or network access.