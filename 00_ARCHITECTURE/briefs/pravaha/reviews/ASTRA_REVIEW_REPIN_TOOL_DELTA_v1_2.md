---
artifact: ASTRA_REVIEW_REPIN_TOOL_DELTA
version: "1.2"
reviewer: "Codex gpt-6-astra"
date: 2026-10-04
verdict: REJECT
reviewed_commit: 5899499f9fad41ae4cb7cc937094f500763fe989
authority: "Review only; authorizes nothing."
---

Two gaps remain in `load_notice`:

- **Early refusal fails (lines 723–755).** Unknown keys accumulate errors while values are still read. Adding `unexpected_field` plus a JSON integer equal to `10**1000` as tolerance produces uncaught `OverflowError`, not CLI STOP. **Raise the named `ValueError` immediately after identifying unknown keys.**
- **Nested unknowns pass (lines 743–758).** Adding `"typo": 1` beside levels `"1"`, `"2"`, `"3"` produces CLEAN and writes `--out`. **Reject non-level keys while preserving documented additional-level handling.**

The seven-key allow-list is exact. Ordinary unknown, misspelled, case/whitespace variants and extra boundary-object keys refuse without writes. Both new regressions exist; 15 targeted regression functions passed using in-memory files. Add loader/CLI regressions for both counterexamples, requiring STOP, exit 3 and zero writes, including `--apply`.

No other runtime change in this commit; baseline refusals and previously accepted hunks 2–3 remain intact. Commit and tool hash verified.

**MAY THE OPERATOR USE HEAD 5899499f9 (tool sha256 d502ae1d4b6bfad9ca59850e05073659050dcddfbf1600638304c3f7c2d4bcbf) INSTEAD OF 5a46c9c97 for the SETTLED-1 dry-run comparison, the apply and the post capture — NO.** Apply the exact corrections above and re-review.