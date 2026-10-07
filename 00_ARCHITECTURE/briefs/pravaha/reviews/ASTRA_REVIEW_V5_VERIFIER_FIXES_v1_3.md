VERDICT: ACCEPT

Reviewed the full change and round-4 delta through `bd9dc966d40f850e6718b1e2f94d59c65cb2a45d`. **Both steward rulings are resolved. No P1/P2/P3 findings.**

| Ruling | Assessment and evidence |
|---|---|
| **1. Horizon endpoints are open independently of `t_exact`** | **Resolved on both sides.** [window_verifier.py:780](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-ver4/platform/python-sidecar/services/gochara_kernel/window_verifier.py:780) reads the horizon from the member’s own coverage partition. [Line 813](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-ver4/platform/python-sidecar/services/gochara_kernel/window_verifier.py:813) determines openness without consulting `t_exact`. The separate [exact-crossing check at line 601](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-ver4/platform/python-sidecar/services/gochara_kernel/window_verifier.py:601) checks both span containment and ephemeris longitude. |
| **2. Classify clipped grazes from their continued stretch** | **Resolved, with conservative refusal when continuation cannot be established.** [contact_certify.py:88](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-ver4/platform/python-sidecar/services/gochara_kernel/contact_certify.py:88) reconstructs beyond each clipped edge until the overlapping stretch has interior endpoints. [Line 154](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-ver4/platform/python-sidecar/services/gochara_kernel/contact_certify.py:154) rejects crossings and applies the clearance proof throughout that extended stretch. |

**An open endpoint does not excuse an omission inside the horizon.** Continuation beyond the coverage boundary is legitimately outside that partition’s claim. Other endpoints retain their checks, and [contact_certify.py:203](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-ver4/platform/python-sidecar/services/gochara_kernel/contact_certify.py:203) still compares the complete reconstructed contact set against the stored union. I reproduced a genuinely shortened contact failing while its opposite endpoint coincided with the horizon.

The continuation’s limits are explicit in its behavior:

- It tries **60, 120, 240, 480 and 960 days** beyond each clipped edge. Although `max_extension_days` defaults to 1500, doubling means **960 days is the last attempted extension**.
- A stretch still unresolved then returns `None`; its omission remains and certification raises.
- Unavailable ephemeris data aborts reconstruction; it never becomes a graze. I exercised this failure path.
- Missing contacts whose crossings lie just outside **either** horizon edge still produce omissions with an empty graze sink.
- The clearance recursion terminates at the 60-second floor and refuses an unproved leaf.

The **production caller remains slice-only**: [ka_gochara_v5.py:821](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-ver4/platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py:821) obtains the validated marker, and [line 1049](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-ver4/platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py:1049) enables the sink only from that result. Without a marker, omissions retain their previous behavior. The separate verification job rejects slice manifests and supplies no sink.

**Verification:** 175 selected tests passed; 54 tests requiring database or file-writing fixtures were deselected. The tests distinguish accepted clips from interior truncation, incorrect exact instants, real omissions and grazes. Independently, I:

- Replayed the original **Sun / `point:265.39` / January 9, 2025** example using the real solver and pinned ephemeris; both certifiers now pass. The corresponding end-clipped case also passes.
- Confirmed the real calendar-2004 Jupiter clipped graze.
- Exercised two crossings entirely outside the horizon: the clearance proof rejects them; disabling that proof in memory falsely classifies them.
- Verified all implementation/stage locks, the **125-writer inventory**, census fingerprints and `git diff --check`.

**Plain answer:** with this change, the ephemeris fix on main and the separately reviewed wrap-cut builder fix assumed merged, **I see no additional demonstrated code blocker to either requested slice completing**. Unavailable geometry or an unproved continuation can still stop execution deliberately.

**Not verified:** completion through the real runner/database, current chart rows or chart-specific counts, migrations/permissions, deployment of either external fix, or full-run performance. Computations used fixture chart data and real ephemeris with in-memory rows. No files were modified; no database or network was used.

