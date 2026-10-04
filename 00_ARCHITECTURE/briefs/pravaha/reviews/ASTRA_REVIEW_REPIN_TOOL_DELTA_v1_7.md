---
artifact: ASTRA_REVIEW_REPIN_TOOL_DELTA
version: "1.7"
reviewer: "Codex gpt-6-astra"
date: 2026-10-04
verdict: REJECT
reviewed_commit: 22ae1a45d60e17ddb7c810d7bd71cd87c523a166
authority: "Review only; authorizes nothing."
---

Four P1 blockers remain in `repin_dasha_contract.py`:

1. **Malformed captures reach CLEAN** — lines 379–442, 667–672. An otherwise valid `--old-rows` capture with a fractional `level_n` or object-valued natal longitude, with its checksum recomputed, returns **0/CLEAN** and reaches the report write. Both capture modes also accept a NaN natal longitude. **Fix:** share strict row/natal schema validation across capture loading, acquisition and W0, before coercion or writes.

2. **An unlisted literal is rewritten** — lines 1223–1233. Put `2013-01-14T07:17:23+00:00` and `2013-01-14T07:17:23.5+00:00` on one line. The scanner lists only the first; ruling that match `rewrite` changes **both**. The fractional instant was explicitly excluded by detection. **Fix:** preserve match offsets and rewrite only those exact, ruled spans.

3. **Apply preflight can publish false CLEAN** — line 1214. `check_only` returns before validating generated output destinations. When `test_am10_repin_<build8>.py` is a directory, `--apply --out` writes/prints **CLEAN**, then exits 3. **Fix:** construct and validate the complete write plan, including generated destinations and parent directories, before publishing the report.

4. **Malformed CLI text reaches writes** — line 1615. A surrogate-containing `--settled-received` value, under strict UTF-8 stdout, reaches the report and all application writes before returning STOP/3 on encoding. **Fix:** validate CLI strings alongside JSON inputs before any side effect.

The supplied head and tool checksum match. The official capture loads: **1,040 rows**, matching the supplied data SHA-256. The fixed **45+1**, exactly-one-build and G6(a) refusals are unchanged; the verifier-predicate mirror remains restrictive. The wider scan remains report-only. **36 read-only regression cases passed**; exception-guard and per-file atomic-write fault probes held.

All mutation probes used in-memory I/O. No files or databases were changed.

**IS THIS HEAD FIT TO BECOME THE TOOL OF RECORD (merge to the PR 2903 branch) — NO.** Implement the four fixes above and add regression coverage for these counterexamples.