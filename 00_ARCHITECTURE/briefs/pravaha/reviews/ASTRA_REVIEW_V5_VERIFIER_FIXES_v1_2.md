VERDICT: ACCEPT_WITH_AMENDMENTS

Reviewed the full change through `f58a42e3f79d0a8bb65bb5df82f889f0fa3f3dcc` and the Round 3 delta. **Both steward rulings are resolved.** I found no new correctness defect in that delta, but reproduced another pre-existing verifier blocker beyond the excluded wrap-cut issue.

1. **P2 — A valid horizon-clipped point contact is rejected when its exact crossing remains inside the horizon.**

   [window_verifier.py:791](platform/python-sidecar/services/gochara_kernel/window_verifier.py#L791) sets `open_start` only when `t_exact is None`. However, [record_store.py:277](platform/python-sidecar/services/gochara_kernel/record_store.py#L277) clips the support’s start while retaining an exact crossing inside the horizon.

   Reproduced in memory using the repository chart fixture, checksum-pinned Swiss ephemeris, the full-domain arc index and real `solve_point_edges`:

   - Validated `all_classes_1y` horizon: **2025-01-09 → 2026-01-09**.
   - `marriage/P3`, Sun conjunction `point:265.39`.
   - Stored start: **January 9, 00:00 UTC**.
   - Exact crossing: **January 9, 14:47:50.835 UTC**.
   - Stored end: **January 10, 14:21:23.775 UTC**.

   Contact-set certification accepts this output. Member verification rejects it as “still in the geometry just before the stored start.” Treating its horizon start as open makes the same geometry pass.

   The writer invokes this check at [ka_gochara_v5.py:1272](platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py#L1272). This can therefore stop the window phase. It occurs near **265°**, independently of longitude-wrap cuts. Determine start clipping from the coverage boundary while retaining the valid exact crossing; add this case as a regression test.

2. **P2 — Horizon-clipped grazes remain a completion limitation.**

   [contact_certify.py:109](platform/python-sidecar/services/gochara_kernel/contact_certify.py#L109) deliberately refuses graze classification at either horizon boundary.

   Reproducing the existing Jupiter example over calendar **2004**, the real solver supplies no contact for **January 1 → January 23, 10:14:08 UTC**, while reconstruction finds that interval. Comparison still reports an omission with an empty graze sink.

   This is an intentional conservative boundary, unchanged in Round 3. Nevertheless, a valid all-classes one-year slice encountering it cannot complete. Resolving it requires preserving the no-crossing proof and legitimate truncated-contact checks.

The two requested fixes check out:

| Ruling | Assessment and evidence |
|---|---|
| Graze requires proof | **Resolved.** [contact_certify.py:70](platform/python-sidecar/services/gochara_kernel/contact_certify.py#L70) requires `|d0| + |d1| > VMAX × Δt`, otherwise bisects. This correctly excludes reaching the ray under the declared speed bound. |
| Station tolerance uses actual displacement | **Resolved.** [window_verifier.py:719](platform/python-sidecar/services/gochara_kernel/window_verifier.py#L719) compares ephemeris longitudes directly against accuracy plus reconstruction error. The reversal bracket remains; the permitted double-station refusal is documented at [line 691](platform/python-sidecar/services/gochara_kernel/window_verifier.py#L691). |

For the Round 2 graze counterexample, endpoint clearance sums to approximately **0.012018°**, below the **0.066547°** allowed movement. Refinement reaches the negative midpoint and rejects the graze. I replayed that pair numerically.

I reran the original smooth station counterexample without mocking the low-speed check. Its actual displacement remains **0.000496844°**, exceeding **0.000296296°**; it is now rejected.

**Termination and failure propagation are sound.** Default sampling gaps are at most one hour; six bisections reach the 60-second floor. An unproved leaf returns `False`, classification returns `None`, comparison retains the omission, and [contact_certify.py:218](platform/python-sidecar/services/gochara_kernel/contact_certify.py#L218) raises. I also exercised that unresolved-floor path in memory.

The interim remains restricted in the production call chain: the stored manifest digest is checked at [ka_gochara_v5.py:259](platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py#L259), `_test_slice` validates the marker, and only its result enables the sink at [line 1049](platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py#L1049). The independent verification job rejects slice manifests at [verification_job.py:180](platform/python-sidecar/services/gochara_kernel/verification_job.py#L180) and supplies no sink. Publication also refuses them. The H-unknown exclusion and logging changes retain their intended boundaries.

**160 selected tests passed**, with database and file-writing fixtures excluded. The new double-crossing, refinement, floor-failure and displacement tests discriminate the repaired behavior. They do not cover finding 1. Implementation/stage locks, the complete **125-writer** digest inventory, census content hash and census writer fingerprint all matched; `git diff --check` passed.

**Plain answer:** yes—these horizon-edge cases can still stop valid one-year slices even assuming both external fixes are complete. I found no additional reproduced full-horizon blocker beyond the excluded wrap-cut issue, but have not established completion through the real runner.

**Not verified:** actual runner/database execution, current chart rows, migrations or permissions, deployment of the ephemeris fix, the separate wrap-cut implementation, or full-run performance. The reproductions used real ephemeris computation with fixture chart data and in-memory rows. No files were modified; no database or network was used.