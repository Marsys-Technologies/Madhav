---
artifact: ASTRA_REVIEW_V5_TEST_SLICE
version: "1.0"
reviewer: "Codex gpt-6-astra"
date: 2026-10-04
verdict: REJECT
reviewed_commit: "28c8a4045 (pravaha/c46-v5-test-slice, PR 3110)"
authority: "Review only; authorizes nothing."
---

**MAY PR 3110 AT 28c8a4045 BE MERGED — NO.**

1. **P1 — Slice contacts can survive a later full build.** The [snapshot cleanup](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-slice/platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py:704) deletes inventory and snapshot rows, not the complete output chain. Class-by-class cleanup preserves contacts referenced by another class; [contact insertion](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-slice/platform/python-sidecar/services/gochara_kernel/record_store.py:727) then uses `ON CONFLICT DO NOTHING` without comparing temporal bounds. Contact identities are horizon-independent. I reproduced both classes retaining a slice-clipped `t_out` after requesting the full interval, using real store methods with an in-memory SQL model. Geometry verification should reject this inconsistency, but replacement is broken.

   **Required:** on scope transitions, replace the entire unsealed chart × generation output chain in dependency order before rebuilding. Test shared contacts across classes, both clipping boundaries, and slice→slice→full transitions.

2. **P1 — The active run’s marker is not bound to the live-input check.** The [production caller](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-slice/platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py:372) supplies no expected scope/component; `verify_live` copies these from the stored vector. Consequently, a sliced context accepts a default vector, and a default context accepts a sliced vector. Normalisation also accepts `stored_scope="test_slice", test_slice={}` or a wrong marker digest. These cases passed the real checking functions with controlled input sources. The “lost slice” test supplies explicit expectations that production omits.

   **Required:** pass expectations derived from the validated run marker into `verify_live`; normalise only an exact matching schema/digest pair. Add regressions through the production caller for missing, changed and forged stamps.

3. **P2 — Malformed-container and timestamp handling violates the refusal contract.** The [manifest reader](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-slice/platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py:195) converts non-object manifests to “no marker”; an array containing the marker produces the full 298-step plan. The outer runner rejects this at initial preflight, but the writer itself fails open. UTC conversion of `0001-01-01T00:00:00+01:00` raises an unnamed `OverflowError`.

   **Required:** refuse malformed manifest containers explicitly and wrap timestamp parsing/UTC conversion in named refusals.

4. **P2 — Default behavior changes for an explicit null horizon.** `_effective_horizon` converts `config["horizon"]=None` into `DEFAULT_HORIZON`; main passed through `None` and failed.

   **Required:** preserve the previous no-marker behavior and test absent versus explicitly null configuration.

Confirmed: the default **plan golden** matches main’s 298 steps; both slice shapes are accepted; permission errors propagate. The in-build independent checks really run on a copy. An intact slice stamp is refused by verification preconditions as `stale_inputs`, naming `stored_scope`; the writer only creates candidates, 1240 rejects missing verification, and serving rejects the unknown scope. No successful seal/publish/serve bypass was demonstrated with intact stamps.

The offline implementation-lock check passes: only **evaluation** changes, plus aggregate `fcfb6827… → daaf571d…`. Writer digests, census hashes and regenerated brief goldens are consistent. Literal default input-vector bytes necessarily change with that implementation pin.

**Validation:** 116 selected read-only tests passed; no database tests ran. Missing coverage includes the findings above, permission-error propagation, non-string class members and equal horizon endpoints. The purported [verification-entry-point test](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-slice/platform/python-sidecar/tests/l3/gochara/test_c46_v5_test_slice.py:377) calls `verify_inputs` directly; add an actual job-precondition/entry-point regression. The plan golden does not establish every substep’s default equivalence.

No files or database state were changed.