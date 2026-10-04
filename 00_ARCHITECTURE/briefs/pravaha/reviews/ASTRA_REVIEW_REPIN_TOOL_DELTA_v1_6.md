---
artifact: ASTRA_REVIEW_REPIN_TOOL_DELTA
version: "1.6"
reviewer: "Codex gpt-6-astra"
date: "2026-10-04"
verdict: REJECT
reviewed_commit: 1afc6624efa4d787a0f6a8d2b7f1ccddab616875
authority: "Review only; authorizes nothing."
---

The original counterexamples are fixed, but two blocking gaps remain:

- **P1 — malformed W0 still writes.** `_w0_normalise` (lines 633, 659) silently converts fractional `level_n` values to integers and object-valued longitudes to strings. Both checksum-valid reproductions returned **0 and wrote a capture**. Reject non-integral levels and nonnumeric longitudes before normalization.
- **P1 — CLI exceptions still escape.** A notice generated with `json.dumps`, containing `source_message_id="\ud800"`, causes uncaught `UnicodeEncodeError` during report output, including `--dry-run`. Directory output paths cause uncaught `IsADirectoryError` in comparison and both capture modes (lines 1195, 1348). Validate UTF-8 serialization and output destinations before writes; guard remaining CLI I/O with named STOP/exit 3.

Add regressions for these cases asserting exit 3, zero writes and no CLEAN.

**Verified:** 196 regression cases passed in an in-memory harness on Python 3.13, including all 30 additions; two database tests skipped. Official capture loads: **1,040 rows**, expected data hash. Tool SHA-256 matches the supplied value. No weakening found in baseline refusals or hunks 2–3.

**MAY THE OPERATOR USE HEAD 1afc6624e INSTEAD OF 5a46c9c97 for the SETTLED-1 dry-run comparison, the apply and the post capture — NO.** Apply the changes above and re-review.