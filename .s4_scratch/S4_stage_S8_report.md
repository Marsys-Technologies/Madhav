# S4 Pipeline Correctness & Door Parity — Stage S8 (Interpretation & Adjudication / Synthesis)

Investigator lane: S4 fan-out, stage S8 ONLY. Test chart: `1c826d5a-41cb-4450-b4dc-59d440e5f75a` (synthetic). Native chart `482012f1-…` never touched. No fixes attempted — investigation only.

---

## HEADLINE: EDIR E-004 RE-VERIFICATION VERDICT — **STILL BROKEN**

**Evidence-truncation is disclosed ONLY in the machine-readable envelope (`judgment_flags: ['synthesis_evidence_truncated']`), never in reader-visible PROSE, on current `main` (worktree HEAD `f62aeadb0`, 2026-08-27).** This reproduces E-004 exactly as originally seeded. Confirmed via:

1. **Code trace, flag to render, MCP door** (`platform/src/lib/pipeline/prashna_ask_synthesis.ts`):
   - `formatEvidenceBlock()` (line 249) computes `truncatedTools` and pushes an inline disclosure *instruction* string into the `<evidence>` block sent to the model (lines 285–294): `"... [TRUNCATED — kept N of M rows … the reading should not claim exhaustive coverage …]"`. This is a **prompt-level request**, not an enforcement mechanism.
   - `synthesizeReading()` (line 353) sets `judgmentFlags.push('synthesis_evidence_truncated')` at line 380 whenever `truncatedTools.length > 0`.
   - The model's raw response (`interaction.finalText`, line 439) is returned **verbatim** as `result.reading` — no lint, no keyword check, no repair pass, no rejection-and-retry if the returned prose fails to mention the truncation. Compare to the same file's sibling doors: nothing here parallels `lintReaderProse` / `lintVoiceProse` (used in the Portal's `synthesis_stage.ts` for citation-leak and voice-style linting) applied to a truncation-disclosure check.
   - Caller `platform/src/app/api/mcp/prashna_ask/route.ts` line 775 sets `reading: synthesis.reading` and line 787 sets `judgment_flags: judgmentFlags` as two **independent** fields in `readingEnvelope` — no code anywhere splices a disclosure sentence into `reading` when the flag is set.
   - `grep -rn "synthesis_evidence_truncated"` across `platform/src` and `platform-mcp/src`: the flag is set once (line 380), asserted only in tests, and **never consumed** by any downstream renderer to inject prose. It is envelope-only by construction.

2. **Demonstrated-can-fail test (INTEGRATION rung, real result, PASSED)** — `.s4_scratch/S4_stage_S8_e004_repro_test.ts` (originally run from `platform/src/lib/pipeline/__tests__/`, removed after the run per scratch-file discipline; content preserved here for reproduction):
   - Forces truncation with a 400,000-char oversized evidence row (well past `TOTAL_EVIDENCE_BUDGET_CHARS = 320_000`).
   - Mocks `runAdapter` to return a realistic, fluent, confident reading with **zero** truncation/incompleteness language — a plausible and unremarkable LLM failure mode (models routinely ignore meta-instructions buried inside large tool-result blocks).
   - Asserts: `judgment_flags` DOES contain `synthesis_evidence_truncated` (envelope channel works) AND the returned `reading` text matches none of `/truncat/i`, `/partial (coverage|evidence|data)/i`, `/not (all|every) (row|result)/i`, `/incomplete/i`, `/exhaustive/i`, `/only (a portion|some) of/i`.
   - Result: **PASSED** — i.e., the codebase permits (does not prevent) exactly the E-004 failure shape: a `reading` that silently omits truncation while only `judgment_flags` carries it.
   - Command: `cd platform && npx vitest run <path>` → `1 passed (1)`.
   - The **existing** permanent test suite (`platform/src/lib/pipeline/__tests__/prashna_ask_synthesis.test.ts:203-222`, "truncates a genuinely oversized single-row evidence item and discloses it via judgment_flags (RC-08)") only asserts `judgment_flags` contains the flag and that the **outgoing prompt** contains `truncated="true"`. It never asserts on `result.reading` content. All tests in that file share a fixed canned `mockRunAdapter` `finalText` ("Your Mercury-Jupiter period favors steady career growth.") that itself contains no truncation language — the permanent suite has been asserting a green result for over a month (commits `56d4a41f1` W6.2 → `818b61cc5`/`87a759215` RC-07/RC-08, through `d653236c2` P1) without ever checking the one thing E-004 is about.

3. **Fix history shows the gap was never closed, only re-engineered around**: `git log --oneline -- platform/src/lib/pipeline/prashna_ask_synthesis.ts` shows `d2d9fa2fc` (W6.2, initial synthesis stage) → `56d4a41f1` ("cap per-evidence-item serialized size … disclose truncation") → `2df42b610` (W6.3) → `818b61cc5` (RC-07, cost tracker) → `87a759215` (RC-08, "right-size … + bearing-aware trim") → `02c71e4e7` (merge) → `d653236c2` (P1). Every one of these commits improved the **budget/selection algorithm** or the **envelope flag**; none added prose enforcement. "Disclose truncation" in commit `56d4a41f1`'s title refers to the prompt instruction + flag, not a verified reader-visible outcome — the same conflation E-004 was raised to catch.

**Proposed EDIR entry (for the fixer lane / EDIR_V3 filing, not filed by this investigator):**
- **Title**: Evidence-truncation disclosed only in `judgment_flags` envelope, never enforced/verified in reader-visible synthesis prose (MCP door)
- **Class**: failure-honesty / B.10 (no fabricated completeness) — a truncated reading can present as exhaustive to the human reader
- **Proposed severity (proposed)**: S1/S2 — a reader-facing acharya-grade reading claiming completeness while silently dropping evidence rows is a direct violation of B.10/B.11 disclosure discipline, and the failure is silent (no error, no visible flag) to anyone who does not separately inspect `judgment_flags`
- **Lens(es)**: Correctness, Failure-honesty
- **Pipeline stage**: S8 (Interpretation & Adjudication / synthesis) — MCP door specifically (`prashna_ask`)
- **Expected**: reader-visible prose discloses truncation whenever `judgment_flags` contains `synthesis_evidence_truncated` (either verified post-hoc, or synthesized via a template/append rather than left to model compliance)
- **Observed**: prose and envelope are decoupled; the model is *asked* via an inline prompt instruction but nothing checks whether it complied; date of this re-verification 2026-08-28, worktree HEAD `f62aeadb0` (2026-08-27)
- **Code anchor**: `platform/src/lib/pipeline/prashna_ask_synthesis.ts:378-381` (flag set, no verification), `:439-444` (reading returned verbatim), `:285-294` (the unverified prompt instruction); caller `platform/src/app/api/mcp/prashna_ask/route.ts:775,787` (fields kept independent)
- **Proposed fix class**: post-hoc verification/repair pass on `reading` when `synthesis_evidence_truncated` is set (either a lint that fails closed and appends a disclosure sentence, or a second lightweight LLM/deterministic check), OR deterministically append a disclosure sentence to `reading` rather than relying on the model to self-report
- **Rung achieved**: INTEGRATION (real vitest run, mocked adapter, real code paths for `formatEvidenceBlock`/`selectRowsWithinBudget`/`synthesizeReading`)
- **Provenance**: reproduces E-004

---

## Cross-door parity (PPR-30) — S8

**Finding: the two doors don't share a parity gap in the narrow "flag vs prose" sense — they have entirely different evidence-truncation architectures, which is itself a parity gap the charter asks to name specifically rather than fold into "doors differ."**

- **MCP door** (`prashna_ask_synthesis.ts`): deterministic pre-fetch, single non-agentic LLM call. Evidence is pre-truncated by a `TOTAL_EVIDENCE_BUDGET_CHARS=320_000` shared budget with bearing-aware row selection (`selectRowsWithinBudget`), and truncation is signaled via `judgment_flags` (envelope-only, per above).
- **Portal door** (`platform/src/lib/pariprashna/pipeline/synthesis_stage.ts`): agentic loop (`runAgenticLoop`, imported line 37) where the model calls tools **live**. Tool results are executed via `executeMCPTool` (`platform/src/lib/synthesis/mcp_tool_executor.ts:66-71`): `JSON.stringify({ tool, results: result.results, result_count })` returned to the model with **zero size cap, zero row selection, zero truncation logic of any kind**. Confirmed by exhaustive grep: `grep -n -i "truncat" platform/src/lib/pariprashna/pipeline/synthesis_stage.ts` returns only an unrelated prompt-instruction line ("Do not truncate for brevity"); `grep -rn -i "truncat" platform/src/lib/pariprashna/` shows the Portal's only truncation concept is `interpretation_sets.truncated_count` — a **different, later-stage** cap on how many *judgment/interpretation sets* get processed per turn (`platform/src/lib/pariprashna/interpretation/assemble.ts`), disclosed via a real user-facing warning (`persistence_stage.ts:532-540`, `code: 'interpretation_sets_truncated'`) — genuinely a stronger disclosure pattern than the MCP door's evidence-truncation flag, but it answers a different question (interpretation-cap, not raw-evidence-size-cap) and does not cover the MCP door's failure mode at all.
- **No `judgment_flags` vocabulary exists in the Portal pipeline at all** (`grep -n "judgment_flags"` across `synthesis_stage.ts`/`persistence_stage.ts`/`receipt_stage.ts` → no hits) — the two doors don't even share a signaling channel for this class of gap, so "port the fix to both doors" cannot mean "reuse the same flag."
- **Practical consequence**: the MCP door has an evidence-overflow *problem with an honest-but-unverified partial fix* (budget + flag + unheeded prompt ask). The Portal door has **no evidence-overflow handling whatsoever** in this stage — a wide `deep_dive` (up to `DEEP_DIVE_MAX_ITERATIONS=16` re-entries, line 99) accumulating many large tool results could grow the agentic-loop message history unboundedly, with no application-level truncation, no flag, and therefore no disclosure surface to even build prose-enforcement onto. This is a distinct, likely-worse failure mode (silent provider-level context truncation/error with zero telemetry) that the S4 lane flags as a **candidate for a separate EDIR**, not a duplicate of E-004 — filing is left to the fixer/EDIR lane per instructions.

**Proposed second EDIR candidate (for filing lane's judgment, not filed here):**
- **Title**: Portal-door (Paripraśna) agentic-loop tool results have no size cap/truncation handling at all in `executeMCPTool` — asymmetric with MCP door's budgeted approach
- **Class**: door-parity gap, correctness/optimality risk
- **Lens(es)**: Correctness, Optimality, Cross-door parity
- **Pipeline stage**: S8, Portal door
- **Code anchor**: `platform/src/lib/synthesis/mcp_tool_executor.ts:66-71`; `platform/src/lib/synthesis/agentic_loop.ts` (no truncation logic found via grep)
- **Rung achieved**: INTEGRATION (static code trace + grep confirmation, not a forced-repro test — lower confidence than E-004's finding; a repro test would need a real oversized tool result run through the actual agentic loop, out of this lane's time budget)

---

## Dimension 1 — Correctness

- Every asserted fact traces to bundle evidence **by prompt design**: both doors' system prompts (`consumeSystemPromptV2` for MCP via `NO_LIVE_TOOLS_OVERRIDE`, `buildConsultSystemContent` for Portal) instruct citation discipline, and `PARIPRASHNA_CITATION_APPENDIX` is wired into the Portal prompt per commit `4e6301770` ("wire the citation sentinel appendix into the real synthesis prompt (P2-close item 2)"). This is enforced downstream by `lintReaderProse` (`platform/src/lib/pariprashna/citations/register_leak_lint.ts`) on the Portal door — a real, code-level check, unlike the truncation-disclosure gap above. The MCP door (`prashna_ask_synthesis.ts`) has **no equivalent citation-leak lint** on its output at all (not in scope of this stage's remit to fix, but worth noting as a second correctness-adjacent parity gap: the Portal door lints its prose for register leaks; the MCP door's `synthesizeReading` does not lint its `reading` for anything beyond emptiness).
- Alternatives/falsifiers: `NO_LIVE_TOOLS_OVERRIDE` (MCP door, lines 93-117) explicitly instructs honest gap disclosure ("do NOT fabricate content to fill these gaps") but does not explicitly ask for alternatives/falsifiers as a required section — this is a prompt-content question outside this lane's time budget to fully audit against MSR/quality-dimension test-plan §5; flagging for the correctness-focused lane/fixer to cross-check against the full prompt text if not already covered elsewhere.

## Dimension 2 — Optimality

- **Could not obtain a genuine live synthesis-latency-share number.** Investigated `query_trace_steps` via the read-only proxy at `127.0.0.1:55432` (note: the `mcp__postgres__query` tool itself is misconfigured to `127.0.0.1:5433`, ECONNREFUSED in this environment — used `psql` directly against `DATABASE_URL` with port substituted 5433→55432 instead).
- **New, real, LIVE finding (not previously known to this investigation)**: every `step_name='synthesis'` row ever written to `query_trace_steps` (16 rows total, 2026-07-21 through 2026-07-23, the only window this door's trace step appears in) is **permanently stuck at `status='running'`, `latency_ms=NULL`, `completed_at=NULL`** — `SELECT count(*) FROM query_trace_steps WHERE step_name ILIKE '%synth%' AND status='done'` → **0**, ever. Root cause (code trace): `platform/src/app/api/chat/consult/route.ts:1037-1052` allocates `synthesisSeq`/`synthesisStart` and emits a single `step_start` event — `grep -n "synthesisSeq"` in that file shows the variable is **never referenced again**, i.e. no matching `step_done`/completion event is ever emitted for it. Downstream consumers (`platform/src/lib/trace/writer.ts:203,213` and `platform/src/lib/admin/trace_assembler.ts:222`) both contain `CASE`/`.find()` logic keyed on `step_name IN ('synthesis','synthesis_done')` expecting a completion row that **no code path in the repository ever writes** (`grep -rn "'synthesis_done'"` → only the two reader sites, never a writer). Recent traffic (queried 2026-08-22 window) shows **zero** `step_name='synthesis'` rows at all, suggesting either this code path is no longer the primary hit path or the instrumentation has been silently dead longer than the 2026-07-21→23 window. **This means EDIR E-006's "tool dispatch ≈4.0s of an 81.3s turn" / ">95% in planning/synthesis" figures cannot be currently re-derived from `query_trace_steps`** — that number must come from a different measurement or has gone stale; worth flagging to whichever lane owns E-006/optimality re-verification.
- Recommend as a **third EDIR candidate**: synthesis trace-step instrumentation is a §N.8 Earned-Signal violation (a `status` that structurally can never resolve to `done`) — separate from E-004, filed at fixer/lane discretion.
- **Direct instrumentation fallback** (as authorized by the brief): benchmarked `formatEvidenceBlock()` (the MCP door's pre-LLM evidence-trim/format step) on a realistic wide-deepdive shape (10 tools × 200 rows × ~500-char rows, well into truncation territory) — **3.14ms** wall time (`.s4_scratch/S4_stage_S8_report.md` bench inlined below for reproducibility; test removed from tree after running). This confirms the deterministic pre-synthesis overhead is negligible; essentially all synthesis-stage wall time is the LLM round-trip itself, consistent with the "synthesis + planning dominate the turn" framing in EDIR E-006, though I could not verify the specific 4.0s/81.3s ratio against live data (see above).
- Token cost per turn class: `synthesizeReading`'s `QueryRequest` (line 429) does not expose a token-count cap or per-query-class budget in this file; `runAdapter`'s `usage.inputTokens/outputTokens/costUsd` (visible in the interaction result type, e.g. mocked at test line 71) is captured but this investigation did not trace where/whether it's aggregated per query-class — out of time budget for this lane; flagging for the optimality-focused lane if a separate one exists.

## Dimension 3 — Failure-honesty

Covered above under the E-004 headline — this is this stage's core deliverable. Summary: the machine-readable channel (`judgment_flags`) is honest and correct; the human-readable channel (prose) is not enforced to match it. A secondary honest-disclosure win worth crediting: `formatGapsBlock` (lines 321-329) and the gap-handling instruction in `NO_LIVE_TOOLS_OVERRIDE` do correctly push unresolved/empty/leaked/cap-tripped tool gaps into the prompt as an explicit `<evidence_gaps>` block distinct from truncation — that mechanism is architecturally sound (same "ask the model, no verification" limitation applies, but it's a separate, not-yet-investigated failure mode; this lane's time budget prioritized the named E-004 truncation defect per instructions).

## Dimension 4 — Demonstrated-can-fail

The E-004 repro test above IS this section's deliverable. Real result: **PASSED**, i.e. the failure mode is real and reproducible at INTEGRATION rung, not merely theorized. Test file preserved at `.s4_scratch/S4_stage_S8_e004_repro_test.ts` for the fixer lane to re-run (`cd platform && npx vitest run <path-when-restored>`).

---

## Evidence rung summary

- **INTEGRATION** (ceiling, as instructed): real vitest run against real `formatEvidenceBlock`/`selectRowsWithinBudget`/`synthesizeReading` code paths with mocked `runAdapter`/`db.query`, both for the E-004 repro and the bench.
- **LIVE-adjacent**: real `query_trace_steps` production/staging DB rows read via the read-only proxy (`127.0.0.1:55432`, `psql` direct — the `mcp__postgres__query` MCP tool itself is misconfigured to port 5433 in this environment and should be flagged to whoever owns tooling config). This produced the genuine "synthesis trace step never completes" finding, which is new information not previously in this lane's brief.

## Files touched (investigation only, no fixes)

- Created and removed (scratch, per instructions): `platform/src/lib/pipeline/__tests__/s4_e004_prose_disclosure.scratch.test.ts`, `platform/src/lib/pipeline/__tests__/s4_bench.scratch.test.ts` — both deleted after running; the E-004 repro test content is preserved at `.s4_scratch/S4_stage_S8_e004_repro_test.ts`.
- No source files under `platform/` or `platform-mcp/` were modified.
