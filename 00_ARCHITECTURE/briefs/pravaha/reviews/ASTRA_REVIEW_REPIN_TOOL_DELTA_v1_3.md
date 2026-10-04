---
artifact: ASTRA_REVIEW_REPIN_TOOL_DELTA
version: "1.3"
reviewer: "Codex gpt-6-astra"
date: "2026-10-04"
verdict: REJECT
reviewed_commit: b60d2e197c8c80054f0a3b38d2bc1d4c348a8929
authority: "Review only; authorizes nothing."
---

**P1 — Duplicate keys bypass validation** at `repin_dasha_contract.py:739`. An otherwise valid notice containing `"tolerance_seconds":0,"tolerance_seconds":2` returns **CLEAN/0**, attempts the `--out` write, and reaches `apply_repin`. Likewise, duplicating `expected_shift_seconds` hides an earlier object’s `typo`; duplicate level/boundary keys hide NaN or booleans. Confirmed with intercepted writes and apply calls; no files or database changed.

**Required fix:** reject duplicate keys at every object depth using `object_pairs_hook`. Add raw-JSON loader and CLI regressions for top-level, level, and boundary duplicates, requiring named ValueError → STOP/3 and zero writes, including `--apply`.

Both original counterexamples are fixed. All **145 non-database test cases**, including **14 new regression cases**, passed through an in-memory filesystem harness; two database tests were skipped. Other hostile probes were refused. Baseline tests remain unchanged; hunks 2–3 are intact; this follow-up changes no runtime outside notice validation. Supplied hash verified.

**MAY THE OPERATOR USE HEAD b60d2e197 (tool sha256 1e526cab206cb68d3fdb8e11e92dd6001440aa2d82aa8bcd6014e40e25554899) INSTEAD OF 5a46c9c97 for the SETTLED-1 dry-run comparison, the apply and the post capture — NO.**