---
artifact: VERIFY_RC-08.md
residual: RC-08 (synthesis truncation — right-size synthesis_evidence_truncated + bearing-aware)
branch: res/rc08-synthesis-truncation
commit_verified: 87a75921
verifier: independent verifier agent (opus, high effort) — NOT the implementer
verdict: ACCEPT
date: 2026-07-22
---

# VERIFY RC-08 — synthesis_evidence_truncated right-sizing + bearing-aware trim

## Verdict: **ACCEPT** (code + test legs). One sub-leg — the *live trace* — is
deferred to Wave R-C per brief §F batching; it is not an implementer gap and is
recorded below so RC-16 (seal) picks it up.

Verified against `RETRIEVAL_RESIDUAL_CLOSURE_BRIEF_v1_0.md` §E RC-08 (lines
220–228) and §3.5 distillation doctrine (`RETRIEVAL_STRATEGY_v1_0.md` lines
237–260). Files changed (scope-clean, exactly two, both under `may_touch`
`platform/**`):
- `platform/src/lib/pipeline/prashna_ask_synthesis.ts`
- `platform/src/lib/pipeline/__tests__/prashna_ask_synthesis.test.ts`

## (a) Tests rerun independently by verifier

- `npx vitest run src/lib/pipeline/__tests__/prashna_ask_synthesis.test.ts` →
  **22 passed (22)**
- `npx vitest run src/app/api/mcp/prashna_ask/__tests__/route.test.ts` →
  **20 passed (20)** (unaffected, confirmed)
- `npx vitest run src/lib/pipeline/` (full pipeline suite) → **68 passed (68)**
- `npx tsc --noEmit -p tsconfig.json` → **exit 0, clean**
- `npx eslint` on both changed files → **exit 0, clean**

All numbers match the implementer's report. No trust taken on faith — every
command rerun in this verifier's own session.

## (b) DONE bar (brief §E RC-08, verbatim) vs. what was implemented

> **DONE:** a standard deepdive no longer trips the flag OR trips it only when
> genuinely over budget with the highest-bearing evidence retained; the
> dissent/tail rows are provably never the ones truncated; live trace + test.

| DONE-bar leg | Status | Evidence |
|---|---|---|
| Standard deepdive no longer trips the flag | ✅ MET | Test `does not truncate a standard-sized deepdive floor (RC-08)` — 8 tools × 15 rows × 400 chars stays untruncated; passes. Root fix: per-item budget = `TOTAL_EVIDENCE_BUDGET_CHARS (320_000) / evidence.length` floored at `MIN_EVIDENCE_ITEM_CHARS (6_000)` — replaces the flat 8_000/item cap. |
| Trips only when genuinely over budget, highest-bearing retained | ✅ MET | `selectRowsWithinBudget` ranks by `significance + dissent_bonus`, greedily keeps within budget; test `truncates a genuinely oversized single-row evidence item` proves a 400KB monolith still trips honestly. |
| Dissent rows provably never truncated | ✅ MET | Test `never drops the dissent (low-confidence, high-significance) row` (dissent row mid-array survives, `FILLER_399_` dropped) + unit test `ranks a low-confidence row above higher-significance-but-confident filler via the dissent bonus`. |
| Tail rows provably never truncated | ✅ MET | Test `never drops a high-significance "tail" row placed last in the array` — the exact position a blind slice-from-start would cut first — survives. |
| Live trace | ⏳ DEFERRED to Wave R-C | Per brief §F, RC-08 is Wave R-A (code); live traces "see the full cumulative fix set" only after R-A/R-B deploy. Non-interactive session cannot reach the deployed connector (MCP requires OAuth). This is the brief's own batching design, not an implementer omission. **Must be discharged in Wave R-C before RC-16 seal.** |

## (c) Adversarial failure-mode hunt

**Primary listed failure mode — "a cap change that isn't actually bearing-aware": NOT PRESENT.**
The trim is genuinely bearing-ranked, not a relabelled character slice:
- `selectRowsWithinBudget` (prashna_ask_synthesis.ts) sorts by
  `score = significance + (isDissent ? DISSENT_RANK_BONUS(1000) : 0)`, keeps in
  rank order within budget, then re-emits in **original array order** for
  readability. Position no longer determines survival — significance/dissent do.
- Doctrine fidelity confirmed against §3.5 lines 253–260: (a) rank by
  bearing-on-the-question not magnitude ✅; (b) dissent quota for
  low-confidence-high-impact rows ✅ (`DISSENT_CONFIDENCE_THRESHOLD = 0.5`, hard
  1000-pt bonus makes it a floor not a tiebreaker); (c) trim declared via
  disclosure string with kept/total counts + honest `droppedDissentCount` ✅.

**Root-cause claim verified.** The report attributes the over-firing to
`prashna_ask`'s route calling `tool.retrieve()` in-process, bypassing
`platform-mcp`'s `applyResponseBudget`/`finalizeMcpBudget`. Confirmed:
`route.ts` line 405 calls `tool.retrieve(...)` directly; `grep -c
"applyResponseBudget\|finalizeMcpBudget" route.ts` → **0**. The per-item cap in
this file is indeed the only size control on the path. Claim is accurate.

**Field-existence check.** `readBearingHints` reads `significance`/`confidence`
defensively off each row. Confirmed both are real (optional) fields on the shared
tool result type: `src/lib/retrieval/shared_types.ts` lines 70–71
(`confidence?: number`, `significance?: number`). No fantasy fields.

**Minor robustness note (NON-BLOCKING, recommend follow-up):** the degenerate
fallback `keptSerialized.slice(0, perItemBudgetChars)` re-introduces a raw
character slice, but only ever on already-bearing-selected content, so it does
not reopen the position-bias defect. One edge: `PER_ROW_OVERHEAD_CHARS = 40`
undercounts the per-element indentation that `JSON.stringify(array, null, 2)`
adds when a kept row is itself multi-line (>~20 lines), so a set of large
multi-line rows could push the combined real serialization slightly over budget
and trip the last-resort slice, char-cutting the trailing (original-order) kept
rows. This is a narrow, large-row-only edge; budgets are large (≥6_000, typ.
~40_000); disclosure stays honest; and the bearing-ranked *selection* is
unaffected. Recommend a hardening follow-up (account for array indentation in
overhead, or drop the lowest-bearing kept row rather than char-slice) but it does
not defeat the DONE bar and is not a reject.

## (d) Scope / must_not_touch

`git diff main --name-only` → exactly the two pipeline files above. No touch to:
FROZEN orchestrator / WriterBase / `ga_*`/`bo_*`/`ka_*`/`ph_*`/`mi_*` writers;
`chart_facts` semantics / chart computation; LEL; `kala_*`/gochara serving
semantics; D-4b branches/briefs. Clean. No migration introduced (none expected
per §N.4). Commit message cites RC-08.

## Bottom line

**ACCEPT.** Root cause correctly diagnosed and fixed; the cap is proportional
and the truncation is genuinely bearing-aware per §3.5 (dissent + tail
protection proven by dedicated tests); all suites, tsc, and eslint green under
independent rerun; scope is surgical and touches nothing forbidden. The single
outstanding sub-leg is the DONE bar's **live trace**, which brief §F explicitly
batches into Wave R-C after cumulative deploy — it must be captured there before
RC-16 seals RC-08. One non-blocking robustness follow-up (overhead accounting on
the last-resort slice) is recommended but not required for closure.
