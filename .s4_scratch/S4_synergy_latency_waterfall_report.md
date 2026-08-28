# S4 §4.3 Synergy Test #4 — Latency Waterfall Accounting

**Stream:** Paripraśna Assurance S4 (Pipeline Correctness & Door Parity)
**Test subject:** synthetic chart `1c826d5a-41cb-4450-b4dc-59d440e5f75a` (native chart never touched)
**Date:** 2026-08-28
**Rung achieved:** **LIVE** (primary — real end-to-end `prashna_ask`/`prashna_status` MCP-door turn against the deployed pipeline) **+ direct stage-chain instrumentation / static code-path proof** (secondary — used only to decompose the LIVE run's internal buckets; no second HTTP/turn was needed for this layer)

---

## Headline waterfall (native telemetry only)

This is the number the production system can currently prove on its own, with **zero
added instrumentation** — read straight from the real job's `completeness.tools_dispatched[].latency_ms`
(S6, the only stage with a native per-unit timer) against the job's own `elapsed_ms`.

| Stage | Duration (ms) | % of total wall-clock |
|---|---:|---:|
| S6 — ToolBroker dispatch (11 tools, measured) | 705 | 0.69% |
| **UNATTRIBUTED** (no native per-stage timer exists for S1–S5, S7–S11) | **101,697** | **99.31%** |
| **TOTAL (wall-clock)** | **102,402** | **100.00%** |

**This corroborates and sharpens EDIR E-006** (2026-08-23 seed: 81.3s turn, tool dispatch ≈4.0s ≈ 4.9%, >95% unattributed). This run: 102.4s turn, tool dispatch 0.705s ≈ 0.69%, **99.3% unattributed** — same shape, worse ratio (partly because this run's individual tool calls were faster in absolute terms, not because more work happened elsewhere). **Finding stands and is reproduced on a second, independent live turn.**

---

## Best-effort full 11-stage decomposition

Native telemetry stops at the two rows above. To fill in the rest, each remaining
stage was independently investigated by the strongest evidence class available —
never guessed. Evidence class is stated per row.

| # | Stage | Duration (ms) | % of total | Evidence class |
|---|---|---:|---:|---|
| S1 | NormalizedQuery → intent/scope classify | 0.006 | 0.00% | **MEASURED-DIRECT** — `classifyScope()` called directly with the real question text, 20 samples, median shown (`.s4_scratch/time_classifier.ts`). Pure deterministic regex function, zero I/O. |
| S2 | EntitlementDecision | ~101 | 0.10% | **MEASURED-DIRECT** — the exact SQL `authorizeChartAccess.ts` runs (`SELECT owner_id FROM charts WHERE id=$1`) executed 5× against the real DB via Cloud SQL Auth Proxy from this sandbox; median of 5 shown. Caveat: measured over this sandbox's network path to `asia-south1`, not the app server's — likely an *upper bound* vs. a warm, colocated production connection pool. |
| S3 | SafetyPolicyDecision | 0 | 0.00% | **STATIC-PROVEN** — `isSafetyGateEnabled()` (`src/lib/pariprashna/safety/flag.ts:25`) reads `PARIPRASHNA_SAFETY_GATE_ENABLED`, **default OFF**, and `classifyTurnSafety` returns immediately with `enforced:false` when off (`safety/gate.ts:126-139`). Confirmed by the job's `judgment_flags` containing no safety-decision flag. |
| S4 | ScopeTuple / ClarificationRequest | (included in S1) | 0.00% | **MEASURED-DIRECT** — `classifyScope()` produces intent *and* the scope tuple in the same call as S1; there is no separate S4 invocation to time. |
| S5 | AcharyaPlan (planner LLM call + floors/budget/NO-LEAKAGE) | ~7,920 (this run, bounded upper estimate); cf. ~3,925 avg independently measured elsewhere in this stream | ~7.7% (this run) | **INFERRED-BOUNDED**, corroborated by a sibling finding — the first `prashna_status` poll (job elapsed_ms=8,726) already showed the *final*, stable dispatch count (11/11) and a completed dispatch-time figure. So S1+S2+S3+S4+S5+S6 ≤ 8,726 ms. Subtracting the measured/proven-negligible S1(0.006)+S2(101)+S3(0)+S4(0)+S6(705) leaves ≈7,920 ms unaccounted inside that window, attributable to S5. **Not independently timed by this agent** — this is "what's left" inside a proven-tight window, not a stage-entry/exit measurement. The S5-stage agent in this same stream independently measured plan latency directly via 14 real `query_trace_steps` DB rows at **3,925 ms avg** (`.s4_scratch/S4_stage_S5_report.md`) — a different question/turn, same order of magnitude, and a stronger (directly-measured, not subtraction-inferred) number; treat that report's figure as authoritative for S5's typical value, this row's ~7.9s as this specific turn's upper bound. |
| S6 | ToolBroker → dispatch (11 tools) | 705 | 0.69% | **MEASURED-LIVE** — Σ `latency_ms` from the real job's `completeness.tools_dispatched` (native telemetry). |
| S7 | EvidenceBundle assembly | ~0 (not independently measured) | ~0.00% | **STATIC-PROVEN (near-zero)** — `bundle_hydrator.ts` has exactly one `await` (`storage.readFile`, only on a cache-miss path for oversized results) and is otherwise an in-memory transform of results S6 already fetched. |
| S8 | Interpretation & Adjudication (synthesis, streamed LLM output) | ~93,600 (dominant remainder) | ~91.4% | **INFERRED-DOMINANT-REMAINDER** — total (102,402) − dispatch-complete boundary (8,726) = 93,676 ms remains for S7+S8+S9+S10+S11 combined. S7/S9/S10/S11-core are independently proven near-zero (see their rows), so this remainder is overwhelmingly S8. `judgment_flags` includes `synthesis_evidence_truncated`, confirming synthesis ran long enough to truncate — consistent with a long streamed generation dominating wall time, matching EDIR E-004/E-006's pattern. **No native S8 start/end timer exists on the MCP door** to confirm this number directly (see Findings). |
| S9 | Grounding/Safety Validation | ~0 (not independently measured) | ~0.00% | **STATIC-PROVEN (near-zero)** — `validation_stage.ts` has zero `await` calls; pure synchronous citation/register-leak checks over already-generated text. |
| S10 | SemanticReadingParts | ~0 (not independently measured; interleaved, not serial) | ~0.00% (interleaved) | **STATIC-PROVEN (near-zero) + structural note** — `reading_parts.ts` has zero `await` calls, and its block assembly runs **incrementally as S8's stream commits blocks**, not as a separate post-hoc serial pass. Its cost is already inside the S8 window above, not additive. |
| S11 | TurnProvenance + AcharyaReadingReceipt | not independently measured (folded into S8 bucket above) | — | **PARTIAL** — receipt assembly itself (`receipt/assemble.ts`) has zero `await` calls (negligible). But `persistence_stage.ts` (finalize phase) makes **7+ sequential real DB writes/reads** (`writeConversationMessages`, `writeTurn`, `writeTurnDurable`, `fetchMsrSnippets`, `assembleInterpretationSets`, `captureDetectedCandidates`, provenance query) — genuinely I/O-bound and **not independently timed in this pass**. This is the one real, honest gap in the decomposition: some unknown slice of the S8 "remainder" bucket above actually belongs here. |
| | **TOTAL** | **102,402** | **100%** | |

---

## Findings (shaped for EDIR_V3 entry — not filed by this agent)

**Finding 1 — DEFECT (proposed severity: HIGH). Title:** *No native per-stage latency telemetry exists between S1 and S11; the wire/job protocol tracks only 4 coarse buckets, not 11 stages.*
- **Lens(es):** synergy/latency-waterfall
- **Pipeline stage:** CROSS (S1, S2, S3, S4, S5, S7, S9, S10, S11 all lack independent timers)
- **Expected:** §4.3 item 4 requires Σ(11 stage durations) to be reconstructable from telemetry so regressions are locatable to a specific stage.
- **Observed:** The Portal door's own `em.phase()` instrumentation (grep across `pipeline/*.ts` + `route.ts`) emits only 4 named phases — `plan` (covers S1–S5), `retrieve` (covers S6–S7), `synthesize` (covers S8), `finalize` (covers S9–S11) — each with a start/end `ms`, but even *that* coarse 4-bucket signal is Portal-only and was not observable through the MCP door used for this live run (`completeness`/`persistence`/`judgment_flags` carry no phase timings at all, only per-tool `latency_ms`). The single largest cost in the turn (S8 synthesis, ~91% of wall time by this accounting) has **zero direct instrumentation on either door**.
- **Code anchor:** `platform/src/app/api/pariprashna/route.ts:138,322`; `platform/src/lib/pariprashna/pipeline/{plan_stage.ts:213,241; evidence_stage.ts:65,105; synthesis_stage.ts:465,796,883,956; persistence_stage.ts:216; safety_gate.ts:392,398}`.
- **Sharper corroborating evidence (found live in the DB during this investigation, `query_trace_steps` table):** the WEB door DOES have a *partial* mechanism for exactly this — a `step_name='synthesis'` row is inserted with a real `started_at` the instant the last dispatch tool completes (observed live: query_id `14ff45b5-a5d8-4f9b-8c54-dd0b6e0e002d`, `synthesis.started_at = 2026-08-27T23:52:30.346Z`, exactly matching the completion timestamp of the last-finishing dispatch tool `get_strength`). But that row's `status` stays `'running'` and `completed_at`/`latency_ms` are **never populated** — the scaffolding for an S8 timer exists and is silently abandoned mid-build, not simply missing. This independently reproduces the S8-stage agent's own finding in this same stream (`.s4_scratch/S4_stage_S8_report.md`: "all 16 `query_trace_steps` rows for `step_name='synthesis'` stuck `status='running'` forever — E-006 optimality figures can't be re-derived from this table"). Separately, this investigation confirms the **MCP door writes zero rows to `query_trace_steps` at all** (queried the exact time window of this report's own live run, chart `1c826d5a`, 23:48:30–23:51:30 UTC: 0 rows) — consistent with the job result's own `persistence.status:"none"` field and the already-tracked P2-B-004/E-119 finding that the MCP door has no durable persistence path.
- **Proposed fix class:** Add `em.phase()` (or equivalent trace-span) boundaries at each of the 11 architectural stage seams (S1/S2/S3/S4 currently collapsed into one `plan` bucket; S9/S10/S11 currently collapsed into one `finalize` bucket); on the WEB door specifically, complete the already-half-built `query_trace_steps` synthesis row (write `completed_at`/`latency_ms` when synthesis actually finishes — the row and its `started_at` are already there, only the completion write is missing); and surface the same span data through the MCP door's `completeness`/job-result envelope so `prashna_status` final results carry a real waterfall, not just per-tool dispatch numbers.
- **Rung achieved for this finding:** LIVE (confirmed by an actual completed job response inspected field-by-field, plus a live `query_trace_steps` DB read against the real dev DB) + static code read (confirmed by exhaustive grep of every `em.phase(` call site).

**Finding 2 — BASELINE (proposed severity: informational, corroborating). Title:** *Unattributed-time shape reproduces EDIR E-006 on a second independent live turn, with a worse ratio.*
- **Lens(es):** synergy/latency-waterfall
- **Pipeline stage:** CROSS
- **Expected:** Tool dispatch (S6) should be a minority but non-trivial share of turn latency for a deep interpretive question if the architecture's latency budget is roughly evenly spread across the useful work (retrieval + reasoning).
- **Observed:** S6 = 705 ms of 102,402 ms total = 0.69%. E-006's seed was 4.0s of 81.3s = 4.9%. Both readings put >95% (this one >99%) of wall time in the unattributed planning/synthesis/finalize region — i.e., this is not a one-off, it is the structural default for this pipeline's latency profile.
- **Proposed fix class:** none (this is a measurement/observability finding feeding S6 performance baselining, not itself a correctness defect) — feeds directly into S6 (Performance/Resilience stream)'s SLO baseline per §9.
- **Rung achieved:** LIVE.

**Finding 3 — DEFECT (proposed severity: MEDIUM, corroborating/bonus — same live run, same evidence). Title:** *`prashna_status` progress message freezes mid-turn while `elapsed_ms` keeps advancing — reproduces EDIR E-003 shape.*
- **Observed directly in this run:** progress message `"11/~25 tool calls made, 0.7s elapsed"` at `elapsed_ms=8,726` was **still byte-identical** at `elapsed_ms=51,613` (43 seconds later, ~half the turn) before the job completed at `elapsed_ms=102,402`. The `"0.7s elapsed"` in the message is not wall-clock elapsed at all — it is the frozen S6 tool-dispatch-sum (705 ms, confirmed to match this run's own `completeness.tools_dispatched` sum to the decimal), presented to the reader as if it were live progress.
- **Code anchor:** `platform-mcp/src/tools/register_prashna_ask.ts:202` (per test plan §4.3 item 5 anchor).
- **Not the primary deliverable of this test** — filed here only because it fell directly out of the same live run's raw polling log (`.s4_scratch/poll_log.txt`); belongs properly to §4.3 item 5 (Progress truthfulness) if a separate EDIR entry is warranted.

---

## Method detail

1. **LIVE run:** `mcp__marsys-jis-direct__prashna_ask` called with `chart_id=1c826d5a-41cb-4450-b4dc-59d440e5f75a`, a representative deep interpretive question (career/dasha/10H/2H, `response_format:"standard"`, no `scope_tuple` override — let the real planner classify). Polled `prashna_status` 7×, wall-clock timestamped at each poll (`.s4_scratch/poll_log.txt`). Job completed with `status:"complete"`, `elapsed_ms:102402`, full `completeness`/`judgment_flags`/`results` envelope inspected via `jq`-style Python parsing (raw job result: 787,276 bytes, saved by the tool harness — not committed anywhere, ephemeral).
2. **Direct stage-chain instrumentation (S1/S4):** `platform/.s4_scratch/time_classifier.ts` — imported the real `classifyScope()` from `src/lib/vidhi/scope_classifier.ts` via `tsx`, called it 20× with the exact question text used in the live run (after 3 warmup calls), took the median.
3. **Direct stage-chain instrumentation (S2):** `platform/.s4_scratch/direct_stage_timing.mjs` — started the real `cloud-sql-proxy` (using `INSTANCE_CONNECTION_NAME` from the main checkout's `.env.rag`, since this worktree lacks its own copy) and ran the exact SQL `authorizeChartAccess.ts` issues, 5× each for the owner-check and grant-check queries, against the real chart id, over `platform/.env.local`'s `DATABASE_URL`.
4. **Static code-path proof (S3, S7, S9, S10, S11-core):** read each module's source directly and counted `await`/DB-call/LLM-call sites; S3 additionally confirmed via its feature-flag default.
5. **Bounded inference (S5, S8):** derived by subtraction from the two hard boundaries the live run actually gave (first-poll dispatch-complete snapshot at 8,726 ms; job completion at 102,402 ms), after every other stage in each window was independently proven negligible or measured. Explicitly **not** a stage-entry/exit measurement — flagged as the report's own honest limitation, and is exactly Finding 1's evidence.

## Rung honesty statement

- The **headline 2-row table** is 100% LIVE, zero inference.
- The **11-row table**'s S1, S2, S4, S6 are directly measured (LIVE or DIRECT); S3, S7, S9, S10, S11-core are proven negligible by exhaustive static read (not timed, because timing a proven-zero-I/O function adds no information beyond what the classifier micro-benchmark already demonstrates for a comparable pure-TS function); S5 and S8 are the two numbers this report could **not** independently measure — they are bounded/remainder inferences, reported as such, and Finding 1 explains exactly why (no instrumentation exists to measure them directly on either door).
- Persistence writes inside S11 are a known, real, unmeasured gap folded into the S8 estimate — called out explicitly rather than silently absorbed.

## Cleanup

Started two local `cloud-sql-proxy` processes (ports 5433/5434) to run the S2 DB timing probe and the `query_trace_steps` corroboration read; read-only `SELECT`s only (plus one `information_schema.columns` lookup), no writes, no rows mutated. Both terminated by this agent before finishing (PIDs 91452, 25109). One unrelated pre-existing `cloud-sql-proxy` process (PID 20600) was left untouched — not started by this agent.
