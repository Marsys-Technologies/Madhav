VERDICT: ACCEPT_WITH_AMENDMENTS

Fix 1 is sound. Fix 2 handles the reported abutting pairs, but its claimed rejection guarantees and agreement with union certification need amendments. I did **not** demonstrate a complete verification-job bypass.

1. **P2 — A small real ledger gap is accepted as a seam.**  
   [window_verifier.py:721](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-ver/platform/python-sidecar/services/gochara_kernel/window_verifier.py:721) treats endpoints within `probe_seconds`—one second by default—as abutting. Using the added test’s parabola, changing the second contact’s start to `S + 0.5 seconds` still returns `{"contacts": 2}`. The contact certifier rejects that same ledger because its [union operation preserves positive gaps](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-ver/platform/python-sidecar/services/gochara_kernel/contact_certify.py:35). Require genuinely shared endpoints, or establish one explicit, consistent tolerance contract in both verifiers.

2. **P2 — Two inside samples do not establish continuity through the junction.**  
   [_junction_problem at line 665](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-ver/platform/python-sidecar/services/gochara_kernel/window_verifier.py:665) checks before and after the junction, but never the junction itself. I reproduced a smooth parabola peaking just outside the orb: a **40-second excursion**, and separately an **80-second excursion**, both pass member geometry when the stored contacts abut at the maximum. Both samples at ±60 seconds are inside. Full contact certification rejects both bridged ledgers. Check the junction and establish continuity across the interval being exempted.

3. **P2 — The repair still does not implement the complete union contract for overlaps.**  
   The new neighbour search recognizes matching endpoints, not overlapping support. Consequently, valid overlapping episodes retain outside probes at interior union boundaries. This is a **retained inconsistency, not a newly introduced regression**.

   I reproduced it using the pinned Swiss files and the existing [real Saturn episode fixture](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-ver/platform/python-sidecar/tests/l3/gochara/test_a53_boundary_tolerance.py:159): the October 2025–January 2026 overlapping episodes pass `contact_certify`, but member geometry rejects their interior starts/ends. Overlaps are expressly allowed by [A5.3 v1.36](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-ver/00_ARCHITECTURE/briefs/nirmana/l3_autonomous/gochara_wp0_7/A5_3_REGISTERED_WRITER_BRIEF_v1_0.md:1160). I have **not** established that the registered v5 writer’s current `solve_point_edges` path emits that overlapping representation.

4. **P3 — “Station” means low speed here; reversal is not established.**  
   The criterion is independent of builder data, but [boundary_match.py:37](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-ver/platform/python-sidecar/services/gochara_kernel/boundary_match.py:37) measures absolute displacement over ±60 seconds and classifies speeds below **0.001°/day** as stationary. It never checks a change of direction.

   Moving the added test’s split to **30 minutes after** its actual station gives approximately **0.000833°/day**; both verifiers accept it. This follows the specified `boundary_match` criterion, but disproves the stronger assertion that every physically non-station split fails. Either qualify that assertion or require independently bracketed reversal.

**A.** Acceptance is keyed exclusively on the verifier’s literal [_UNKNOWN_H inventory](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-ver/platform/python-sidecar/services/gochara_kernel/inventory_verifier.py:108). The [new branch](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-ver/platform/python-sidecar/services/gochara_kernel/record_verifier.py:242) cannot activate for the 18 known-house classes. Their existing expected-contact and anchor comparisons remain unchanged; this fix creates no empty-ledger exemption for them.

The [exclusion helper](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-ver/platform/python-sidecar/services/gochara_kernel/record_verifier.py:146) refuses known-house classes and checks both records and windows across all rule versions, scoped by chart, generation and class. The [list-parity test](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-ver/platform/python-sidecar/tests/l3/gochara/test_p1_exclusion_h_unknown.py:60) passed.

P3/P4 exclusions are enforced: [generation_output_problems](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-ver/platform/python-sidecar/services/gochara_kernel/window_gate.py:207) rejects records, windows **and membership links** outside included grains. The [job invokes it before class verification](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-ver/platform/python-sidecar/services/gochara_kernel/verification_job.py:355), then independently rederives the inventory.

**B/C.** The requested cases resolve as follows:

| Case | Observed result |
|---|---|
| Arbitrary moving split | Rejected above the speed threshold; the near-station counterexample above passes. |
| Missing partner inside the band | Rejected by the added tests. |
| Station exactly at orb edge | A pair touching the edge from inside passes. A **single remaining piece also passes member geometry**, because the pre-existing angular-edge exception suppresses its outside probe; full certification rejects the omission. |
| Brief departure between pieces | Member geometry can pass; full certification rejects the reproduced cases. |
| Three pieces around two stations | Passed my in-memory reproduction. |
| Horizon-clipped pieces | Clipped pair and station-at-horizon-end reproductions passed. Existing horizon exemptions remain. |

The orb-edge exception is at [window_verifier.py:617](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-ver/platform/python-sidecar/services/gochara_kernel/window_verifier.py:617); horizon handling is at line 709. Junction samples use `min(max(probe_seconds, 60), span/4)`. The subsequent endpoint probe uses the maximum derived margin across both ends, capped at `span/4`, so its inside sample need not be exactly 60 seconds away.

The neighbour query is correctly [scoped to chart, generation, body, relation and canonical target](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-ver/platform/python-sidecar/services/gochara_kernel/window_verifier.py:699). It adds one query per distinct key and repeated linear neighbour scans per contact. Relevant indexes exist, but I did not measure query plans or full-horizon cost.

**D. The pre-existing graze blocker is confirmed.**  
[solve_point_edges](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-ver/platform/python-sidecar/services/gochara_kernel/record_store.py:262) enumerates exact roots and emits occurrences only inside that loop. In an independent synthetic graze, it returned `{}`, while certification reconstructed one approximately 11.83-day interval. The writer’s [verify step calls that certification](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-ver/platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py:947), so an omitted graze fails the build.

The schema requires [`t_exact IS NULL` iff `coverage.truncated`, and truncation iff `clipped_truncated`](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-ver/platform/migrations/1153_gochara_sky_event_substrate.sql:1085). An ordinary no-exact graze therefore lacks an honest representation.

One correction to the author’s identity explanation: v5 contact IDs hash **physical-object identity plus occurrence ordinal**, not the exact timestamp. However, those [ordinals are assigned from the ordered exact-root list](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-ver/platform/python-sidecar/services/gochara_kernel/substrate.py:130). Introducing grazes into that ordering can renumber existing identities.

**E.** Reviewed through `eb4ed401ce851f93a1d6f0c98bc98092231bc066`. Implementation-lock recomputation and the **full writer-inventory check passed**. Census content and writer-source fingerprints match. The diff contains the two verifier fixes, their tests/CI registration and corresponding pins; no unrelated production changes.

Validation: **20 added database-free tests passed**, plus 17 existing pure test bodies invoked without fixtures. The new tests discriminate the reported defects, but omit the counterexamples above.

Not verified: database tests, real orchestrator execution, SQL plans/performance, full census regeneration, or the specific Jupiter **0.396° / 39-day** example. A broader pytest invocation was blocked by temporary-directory fixtures; its setup errors were not product failures. No files were modified; no database or network was used.

