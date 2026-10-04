---
artifact: ASTRA_REVIEW_REPIN_TOOL_DELTA
version: "1.1"
reviewer: "Codex gpt-6-astra"
date: 2026-10-04
verdict: REJECT
reviewed_commit: 17cdf29ea858c355b1b226f95f2a07ff91955aa1
authority: "Review only; authorizes nothing."
---

**One remaining blocker: unknown notice fields are still accepted.** At [repin_dasha_contract.py:742](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-repin2/platform/python-sidecar/scripts/gochara/repin_dasha_contract.py:742), only the three retired fields are refused. In-memory execution confirmed that an otherwise valid notice containing `unexpected_field`, `expected_partition_non_scope`, or `_declared_shape` loads successfully.

1. **Hunk 1’s relaxation is gone.** Whole-table acquisition and pre-flight checks are byte-identical to `5a46c9c97`; constants remain 45+1. No notice can override them. Executed counterexamples: `(44,0,{NEW,OLD})` refuses under ii+iii; `(45,1,{NEW,OTHER})` under ii; `(47,1,{NEW})` under iii. All three specified `expected_*` fields are refused individually and together.
2. **Hunks 2–3 retain their previously sound behavior.** The verifier change is documentation-only in this commit; capture functions remain byte-identical to `5c5f39f3d`. No new weakening of a baseline refusal found.
3. **All four named regressions now exist**, plus the counterexamples. Thirty-four temporary-file-free pytest cases passed; all four named regressions passed with file I/O substituted in memory. The full file could not run normally: no writable TMPDIR was available.
4. **Required fix:** allow only `settled_1`, `source_message_id`, `system_id`, `ayanamsha_id`, `new_build_id`, `expected_shift_seconds`, and `tolerance_seconds` at the notice’s top level. Reject every other key; add loader/CLI regressions proving unknown and misspelled keys produce STOP without writes. Preserve documented additional-level handling.

Verified tool SHA-256: `409806443b72badbae9f9dec69203e7152d70ebcc7c5dd32f00c3e2e75421463`.

**MAY THE OPERATOR USE HEAD 17cdf29ea INSTEAD OF 5a46c9c97 for the SETTLED-1 comparison (dry run), the apply and the post capture — NO; complete the parser fix and regressions above.**