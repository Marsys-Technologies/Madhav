VERDICT: ACCEPT_WITH_AMENDMENTS

Reviewed `d18abd717...477f7219d072d22bf03b4d4d00f02e95886c496b`. The slice and sealing boundaries remain intact, but two new correctness claims are not established. I also reproduced a pre-existing full-horizon blocker.

1. **P2 — Graze classification can hide omitted contacts containing exact crossings.**  
   [contact_certify.py:90](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-ver2/platform/python-sidecar/services/gochara_kernel/contact_certify.py:90) checks hourly samples and a fixed `0.005°` clearance, without bounding movement between samples.

   I reproduced a smooth curve satisfying Venus’s `1.6°/day` speed bound: across one **3,593.538-second** sampling interval, signed distances were approximately **+0.006009°, −0.009°, +0.006009°**. It crosses the exact ray twice; maximum speed was **1.5661°/day**. With both contacts omitted, slice comparison returned **no problems** and reported a graze. Without the sink, it reported the omission.

   Thus a defect dropping both crossings can hide behind the interim under the verifier’s stated assumptions. This is a synthetic counterexample, not a demonstrated planetary occurrence or sealing bypass. Require a clearance-versus-movement proof or independently bounded refinement before declaring “no exact crossing.”

2. **P2 — Measured station curvature is not an upper bound on angular displacement.**  
   [window_verifier.py:678](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-ver2/platform/python-sidecar/services/gochara_kernel/window_verifier.py:678) estimates curvature over ±1 hour; [line 728](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-ver2/platform/python-sidecar/services/gochara_kernel/window_verifier.py:728) treats it as a bound throughout the station-to-junction interval. Smooth, speed-bounded motion does not justify that inequality.

   Reproduction, with `h` measured in hours from the station:

   `longitude = 119.5 + 0.0005 × (1 − exp(−(h/2)^4)) + 10⁻⁹ × h²`

   At **J = S + 3 hours**, the reversal is found, junction speed is below the low-speed threshold, and continuity passes. `_junction_problem` accepts despite actual angular displacement **0.000496844°**, exceeding the allowed **0.000296296°**.

   Compare the actual angular displacement and establish the required intervening bound, or use a justified upper bound on curvature. The current parabola tests cannot expose this error.

3. **P2 — Pre-existing full-horizon blocker: point supports terminate at longitude-wrap cuts.**  
   [arcs.py:300](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-ver2/platform/python-sidecar/services/gochara_kernel/arcs.py:300) splits arcs at **0°/360°**, as well as stations. [record_store.py:216](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-ver2/platform/python-sidecar/services/gochara_kernel/record_store.py:216) confines support to that smaller arc.

   Using the pinned Swiss files and repository chart fixture, `career_change/P3` enumerates Saturn’s aspect to `point:270.84`, including the **0.84° ray**. The writer’s solver starts its 1998 contact at **April 17, 07:36 UTC**; independent reconstruction starts it at **April 16, 01:16 UTC**—about **30 hours earlier**. Member geometry and full contact certification both reject it, including with a graze sink.

   This is outside the new diff, but directly answers E: some valid one-class full-horizon slices still encounter a kernel blocker.

**A. Round-1 amendments**

| Amendment | Assessment |
|---|---|
| H-unknown exclusion | **Resolved/sound.** Acceptance still depends on the verifier’s own class inventory; known-H classes retain population checks. See [record_verifier.py:242](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-ver2/platform/python-sidecar/services/gochara_kernel/record_verifier.py:242). |
| Small positive gaps treated as seams | **Resolved.** Exact stored-instant equality is required at [window_verifier.py:811](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-ver2/platform/python-sidecar/services/gochara_kernel/window_verifier.py:811). |
| Two samples insufficient for continuity | **Resolved under the declared speed bound.** Twenty-five samples cover both endpoints and the junction; clearance ≥ `VMAX × step` excludes an intervening departure. |
| Overlapping episodes | **Resolved for the registered POINT writer’s representation.** Root-local supports partition by arcs; different aspect rays are separated beyond twice the orb. The real Saturn test passed. Historical overlapping representations remain unsupported by this member check. |
| Low speed mistaken for reversal | **Partly resolved.** A monotone slow passage is rejected, but the angular-tolerance claim fails as described above. |

The continuity calculation correctly converts `VMAX_DPS` from **degrees/day** to degrees/second. Default spacing is five seconds; short contacts reduce the margin and spacing. These are fixed natal targets, so body longitude speed is the relevant speed.

A six-hour Swiss speed scan across `DEFAULT_HORIZON` found every body below its declared bound. Mean nodes are used; stored Moon transit contacts are excluded by [evaluator.py:589](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-ver2/platform/python-sidecar/services/gochara_kernel/evaluator.py:589). This supports the bounds empirically; it is not an analytic proof between every sampled instant.

**Double stations:** two reversals inside the ±6-hour bracket can leave equal endpoint velocity signs, causing rejection at line 665. I reproduced that false negative. With multiple reversals, bisection also does not establish that it found the nearest one. No close pair appeared in the real-sky scan; the shortest sampled separation was approximately **19.75 days**, for Mercury.

POINT identification is implemented using both `canonical_target.startswith("point:")` and relation `conjunction`/`aspect`; residence spans cannot receive the exemption.

**B. Slice-only graze boundary**

The production call chain is correctly restricted:

- The writer reads the run’s stored manifest, checks its digest, and validates the marker through `_test_slice` at [ka_gochara_v5.py:378](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-ver2/platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py:378).
- Only a validated `slice_` creates the sink at line 1049. There is no config/environment graze switch.
- The verification job supplies no sink and explicitly rejects slice candidates at [verification_job.py:180](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-ver2/platform/python-sidecar/services/gochara_kernel/verification_job.py:180).
- Seal-brief and seal-flow paths never enable the interim; publication independently refuses slice manifests at [ledger.py:632](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-ver2/platform/python-sidecar/services/gochara_kernel/ledger.py:632).

Classification is attempted only when **no stored contact overlaps the expected interval**. Consequently, ordinary truncated/bridged contacts remain failures. There is no broad exception swallowing other certification failures. Finding 1 is the remaining hole in the “exact crossings always raise” claim.

Findings contain body, relation, target/ray, interval, sampled closest approach/time and peak activity. They appear in the returned geometry dictionary, writer notes and warning log; the builder persists no independent verification attestation.

**C. Logging**

The helper returns the identical `WriterResult`; it does not change transaction or verification behavior. It checks whether notes **contain** `UNVERIFIED`, rather than begin with it—appropriate for the existing prefixed notes. I found no new credential logging. Graze details are duplicated in WARNING and the subsequent INFO outcome; long lists could enlarge or truncate log entries, but I did not measure production log limits.

**D. Pins and tests**

Implementation lock, complete writer-digest inventory, census content hash and census writer-source fingerprint all matched. `git diff --check` passed. No unrelated production changes were present; the ephemeris-copy `chmod` affects test copies only.

**169 selected read-only, database-free tests passed; 74 database/temporary-file fixture cases were deselected.** Existing tests discriminate the ordinary cases, but omit the counterexamples above. I did not rerun the author’s mutation campaign.

**E. Completion through the real runner**

I cannot approve an unconditional completion claim. Besides finding 3, horizon-clipped grazes deliberately remain fatal at [contact_certify.py:84](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-ver2/platform/python-sidecar/services/gochara_kernel/contact_certify.py:84). For example, the added test’s real Jupiter graze, clipped to a **2004 calendar-year slice**, still raises for the interval January 1–January 23.

Conversely, using the repository chart fixture and real ephemeris, contact-set comparison passed for all **14 marriage point-obligation keys over the full horizon**, and **98 distinct point-obligation keys across all classes for 2025**, with the interim enabled. Those are kernel checks, not runner acceptance.

**Not verified:** current database/chart contents, migrations or permissions, database integration tests, actual runner execution, deployed ephemeris provisioning, full census regeneration, SQL performance, or PR-body/G11-note corrections. No files were modified; no database or network was used.

