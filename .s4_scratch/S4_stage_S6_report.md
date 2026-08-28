# S4 Pipeline Correctness & Door Parity — Stage S6 (ToolBroker → dispatch)

Investigator lane: S6 only. Test subject: synthetic chart `1c826d5a-41cb-4450-b4dc-59d440e5f75a`
exclusively (never the native chart `482012f1-...`). Evidence rung: **INTEGRATION** — all numbers
below come from executing the real, unmodified production code
(`platform/src/lib/retrieval/qos/dispatch_queue.ts`, `platform/src/lib/pariprashna/pipeline/evidence_stage.ts`,
`platform/src/lib/cache/with_cache.ts`, `platform/src/lib/pipeline/cost_caps.ts`) via a vitest harness,
plus 3 real DB-backed tool calls against the synthetic chart. Measured 2026-08-28.

Test harness: `platform/.s4_scratch/s6_dispatch_measure.test.ts` (7 tests, all passing).
Raw measurement output: `platform/.s4_scratch/s6_measurements.json`.
Run commands:
```
cd platform && npx vitest run .s4_scratch/s6_dispatch_measure.test.ts                 # queue-level tests
cd platform && INTEGRATION=true npx vitest run .s4_scratch/s6_dispatch_measure.test.ts # + real DB per-tool latency
```

## 1. Numeric summary (metric | measured value | method)

| Metric | Measured value | Method |
|---|---|---|
| **Parallelism efficiency** (7 concurrent tasks, realistic latencies 36–121ms, `concurrency:24`) | wall-clock **121ms** / Σlatencies **473ms** = **0.256** | Real `QosDispatchQueue.submit()`, N=7, controlled setTimeout-based simulated tool work |
| **Parallelism efficiency** (evidence_stage.ts's own shape: N=10 via `getSharedQosDispatchQueue()`) | wall-clock **166ms** / Σlatencies **981ms** = **0.169** | Real shared singleton, 10 concurrent `submit()` calls mirroring `evidence_stage.ts`'s `Promise.all(map(...))` shape exactly |
| Per-tool p50 / p95 / mean — `compute_natal_positions` (real DB) | p50=0ms, **p95=48ms**, mean=3.2ms (N=15) | `getToolByName('compute_natal_positions').retrieve()` against synthetic chart, the exact bridge `evidence_stage.ts` calls |
| Per-tool p50 / p95 / mean — `query_dasha_periods` (real DB) | p50=0ms, **p95=1ms**, mean=0.07ms (N=15) | same |
| Per-tool p50 / p95 / mean — `query_panchanga` (real DB) | p50=0ms, **p95=0ms**, mean=0ms (N=15) | same |
| Per-tool latency **vs declared budget** | **N/A — no per-tool latency budget/SLA exists anywhere in the S6 surface** | grep of `CapabilityDescriptor` (registry/types.ts), `dispatch_queue.ts`, `cost_caps.ts` — no `latency_budget`/`timeout_ms`/`sla` field found |
| Queue wait time under load (`concurrency:3`, 12 tasks × 50ms each, submitted at once) | wait p50=**52ms**, p95=**153ms**, max=**153ms**; theoretical floor for the last-dispatched task = 150ms → **~2% overhead** | Real `QosDispatchQueue`, all 12 submitted simultaneously, concurrency capped at 3 |
| Hang/timeout detection | **NOT DETECTED** — never-resolving task did not settle within a 1500ms observation window; no timeout path exists | `Promise.race` of a never-resolving `submit()` against a 1500ms timer, real `dispatch_queue.ts` code |
| Explicit-rejection failure honesty | **CONFIRMED honest** — rejection propagates through `submit()`; `evidence_stage.ts`-shaped test: 3/4 tools in `validToolResults`, the 4th present in `toolEventLog` with `status:'error'` | Two dedicated tests against real dispatch code |
| `cap_tripped` earned-signal status (`prashna_ask` path) | **EARNED** — backed by `CostCapTracker.checkAndRecordCall()` (real `Date.now()` elapsed-ms + real call-count increment vs configured `maxCalls`/`maxWallClockMs`) | Code trace: `platform/src/lib/pipeline/cost_caps.ts:50-89` |
| `maxQueueDepth` (honest-degradation "refuse" half) in the production shared queue | **UNCONFIGURED** — `undefined` (unbounded); `QueueSaturatedError` is unreachable via `getSharedQosDispatchQueue()` in production | Code trace: `dispatch_queue.ts:271-274`; grep confirms zero non-test call sites pass `maxQueueDepth` |
| Duplicate dispatch-loop implementations sharing the same queue singleton | **2** independent copies: `consult/route.ts` (~L900-970) and `evidence_stage.ts` (L75-105, called from `api/pariprashna/route.ts`) | Code trace |

## 2. Correctness

- **Unresolved/failed tool reporting is honest** in `evidence_stage.ts`: every dispatch is wrapped in
  try/catch; a failure produces `toolEventLog.push({name, status:'error', ms, ok_count:0, err_count:1})`
  and the tool is excluded only from `validToolResults` (the results array), never from the event log
  the completeness receipt is built from (`evidence_stage.ts:96-104`, `:107-116`). Demonstrated live —
  see `evidence_stage_shape_failure_honesty` in the measurement JSON.
- **`cap_tripped` in the `prashna_ask` path is a genuinely earned signal**, not a proxy: `CostCapTracker.checkAndRecordCall()`
  (`cost_caps.ts:67-89`) measures real `Date.now() - startedAt` against a real configured `maxWallClockMs`,
  and a real incrementing call counter against `maxCalls`. This passes the §N.8 test ("what code path
  would have to run — and fail — for the signal to read false?" → a genuine one exists and was traced).
- **But the cap only checks BETWEEN calls, never DURING one** — `checkAndRecordCall()` is called before
  each dispatch (`prashna_ask/route.ts:655`), not raced against the in-flight call. A single tool call
  that itself never returns is invisible to the cap: there is no "next iteration" for the tracker to catch
  it on. This is a distinct gap from the cap's own honesty — the detector is honest about what it measures,
  but what it measures does not cover a hang.
- **The dispatch queue's own "refuse" mechanism is dead in production.** `dispatch_queue.ts`'s own
  doc-comment states the honest-degradation rule as "queue/refuse, never thin quality," and
  `QueueSaturatedError`/`maxQueueDepth` correctly implement the refuse half (verified working under
  test at `dispatch_queue.test.ts:201-222`). But `getSharedQosDispatchQueue()` (`dispatch_queue.ts:271-274`)
  constructs the singleton with no options, so `maxQueueDepth` is `undefined` — unbounded. No production
  call site anywhere in `src/` configures it. Under sustained overload the real system queues without limit
  rather than ever refusing, contrary to the module's own stated contract.
- **Two independent dispatch-loop implementations** (`consult/route.ts` inline loop vs. `evidence_stage.ts`)
  both call the same `getSharedQosDispatchQueue()` singleton but are separately written and maintained —
  a door-parity risk: a fix to one (e.g. the timeout gap below) will not automatically apply to the other
  unless both are found and changed together.

## 3. Optimality

- **(a) Per-tool latency**: all three real L1 tools measured against the synthetic chart are fast
  (p95 ≤ 48ms, two of three ≤1ms p95), consistent with simple indexed lookups over a warm connection
  pool (the one 48ms outlier on `compute_natal_positions` is plausibly first-call connection warm-up).
  **No comparison "vs budget" is possible** — no per-tool latency budget/SLA field exists anywhere in
  `CapabilityDescriptor` or the S6 dispatch surface; only an aggregate, whole-job wall-clock cap exists
  (`DEFAULT_COST_CAPS.maxWallClockMs = 120_000`, `cost_caps.ts:104-107`), which bounds the entire
  `prashna_ask` run, not any individual tool.
- **(b) Parallelism efficiency — the headline number: 0.17–0.26**, measured twice against the real
  production `QosDispatchQueue` (once with a hand-built 7-task batch, once reproducing
  `evidence_stage.ts`'s exact `Promise.all(toolsAuthorized.map(...))` shape via the actual shared
  singleton with N=10). Both are well under the 0.3 "near-ideal parallel dispatch" threshold and far
  from the 0.8 "effectively serial" threshold — **S6's dispatch queue genuinely parallelizes concurrent
  tool calls; this is not a serial-execution defect.**
- **(c) Queue wait under load**: with `concurrency:3` and 12 tasks (50ms each) submitted simultaneously,
  measured wait times cluster exactly at the expected FIFO-under-cap tiers (0/52/102/153ms), matching the
  theoretical last-task floor (150ms) within ~2%. The WRR/priority/per-principal-fairness bookkeeping
  layered on top of the raw concurrency cap adds negligible overhead.

## 4. Failure-honesty

- Explicit tool **rejections** (a tool throwing) are honestly surfaced end-to-end: the rejection
  propagates through `QosDispatchQueue.submit()` (never swallowed), is caught by `evidence_stage.ts`'s
  try/catch, and recorded as `status:'error'` in `toolEventLog` — present, not dropped, and clearly
  distinguished from the successful ones feeding `validToolResults`.
- **Tool hangs (never-settling calls) are NOT honestly surfaced — they are not surfaced at all.** No
  code path in `dispatch_queue.ts` (`pump()`, `selectNext()`) or `with_cache.ts`'s `executeWithCache`
  (`await tool.retrieve(plan, plannerParams)`, unbounded) contains any `AbortController`, `setTimeout`,
  or `Promise.race`. A hung tool call occupies a concurrency slot and an array-position in
  `Promise.all` forever. Because `evidence_stage.ts` (and `prashna_ask/route.ts`'s serial loop) `await`
  the full `Promise.all`/loop before emitting anything, **one hung tool blocks the entire retrieve
  stage indefinitely** — no `unresolved`/`error`/`timeout` entry is ever produced for it; the request
  simply never completes until an outer infrastructure timeout (platform/edge function limit) kills the
  *whole* request, at which point even the tools that *did* succeed are lost — the opposite of an honest
  partial/unresolved report.

## 5. Demonstrated-can-fail

Two decisive tests were written and run against the real, unmodified production code
(`platform/.s4_scratch/s6_dispatch_measure.test.ts`, all 7 tests passing):

1. **Hang test** (`hang_not_detected`): submitted `run: () => new Promise(() => {})` (a tool call that
   never resolves or rejects) to a real `QosDispatchQueue`; raced it against a 1500ms timer. Result:
   `window_elapsed_unsettled` — the task never settled. This *is* the failure demonstration: the system
   cannot report a timeout because no code path exists that could ever produce one.
2. **Contrast test** (`evidence_stage_shape_failure_honesty`): 4 tools dispatched (3 succeed, 1 throws)
   through the real queue in `evidence_stage.ts`'s exact shape. The failing tool appears in
   `toolEventLog` with `status:'error'`; `validToolResults`/`validResults` correctly contains only the
   3 successes. This confirms the gap is specific to **hangs**, not to failures generally — explicit
   errors are handled correctly.

## EDIR-shaped findings

**F1 — No per-tool dispatch timeout in S6; a hung tool call blocks the entire retrieve stage and is never reported (proposed severity: HIGH)**
- Class: Correctness / Failure-honesty / Reliability. Lens: Correctness, Failure-honesty. Pipeline stage: S6.
- Expected: per `dispatch_queue.ts`'s own honest-degradation doc-comment ("queue/refuse, never thin quality") and the B.10/§N.8 spirit, a hung call should be bounded and reported as unresolved/timed-out, not silently hang the whole request.
- Observed (2026-08-28): a never-resolving `submit()` task does not settle within a 1500ms observation window; no `AbortController`/`setTimeout`/`Promise.race` exists in `dispatch_queue.ts` or `with_cache.ts`. Evidence: `hang_not_detected` in `s6_measurements.json`.
- Code anchor: `platform/src/lib/retrieval/qos/dispatch_queue.ts:185-204` (`pump()` — `next.run()` unwrapped); `platform/src/lib/cache/with_cache.ts:60-107` (`executeWithCache`, unbounded `await tool.retrieve(...)`); `platform/src/lib/pariprashna/pipeline/evidence_stage.ts:87-91` (submit call site); `platform/src/app/api/mcp/prashna_ask/route.ts:665` (serial-loop call site, same gap).
- Proposed fix class: wrap the `run()` closure (or `next.run()` in `pump()`) in `Promise.race` against a per-tool timeout that rejects, so a timeout flows through the *existing* honest-error path (no new plumbing needed).
- Rung achieved: INTEGRATION.

**F2 — Honest-degradation "refuse" half is unconfigured/unreachable in the production shared queue (proposed severity: MEDIUM)**
- Class: Correctness / Configuration gap. Lens: Correctness, Optimality (backpressure). Pipeline stage: S6.
- Expected: per the module's own contract, sustained overload should eventually refuse (`QueueSaturatedError`) rather than queue unbounded.
- Observed: `getSharedQosDispatchQueue()` builds `new QosDispatchQueue()` with no options; `maxQueueDepth` defaults to `undefined`. Grep confirms no production call site configures it (only test files do).
- Code anchor: `platform/src/lib/retrieval/qos/dispatch_queue.ts:271-274`.
- Proposed fix class: set an explicit `maxQueueDepth` on the shared singleton, or document the unbounded choice as deliberate if intended.
- Rung achieved: INTEGRATION (code trace + exhaustive grep).

**F3 — `cap_tripped`'s detector is earned but structurally cannot see an in-flight hang (proposed severity: MEDIUM)**
- Class: Correctness (Earned-Signal, §N.8-adjacent). Lens: Correctness, Failure-honesty. Pipeline stage: S6.
- Expected: the cost cap should bound total wall-clock exposure of the dispatch loop.
- Observed: `checkAndRecordCall()` is only invoked *before* each dispatch; a call that never returns (F1) leaves no "next iteration" for the tracker to trip on.
- Code anchor: `platform/src/lib/pipeline/cost_caps.ts:67-89`; `platform/src/app/api/mcp/prashna_ask/route.ts:655-671`.
- Proposed fix class: same as F1 — a per-call timeout closes this gap for both paths at once.
- Rung achieved: INTEGRATION (code trace, cross-referenced with F1's live-tested behavior).

**F4 — No per-tool latency budget exists; optimality-vs-budget is structurally unmeasurable (proposed severity: LOW)**
- Class: Optimality / Missing instrumentation. Lens: Optimality. Pipeline stage: S6.
- Expected: a per-tool budget to compare measured p95s against.
- Observed: no `latency_budget`/`timeout_ms`/`sla` field on `CapabilityDescriptor` or anywhere in the S6 surface; only one aggregate, whole-job cap exists (`DEFAULT_COST_CAPS.maxWallClockMs`).
- Code anchor: `platform/src/lib/retrieval/registry/types.ts` (`CapabilityDescriptor`); `platform/src/lib/pipeline/cost_caps.ts:104-107`.
- Proposed fix class: add an optional `expected_latency_ms_p95` field to `CapabilityDescriptor`, populated from measurement, enabling both a real budget comparison and a sane default per-tool timeout value for F1.
- Rung achieved: INTEGRATION-adjacent (exhaustive code search; no live measurement possible against a nonexistent target).

**F5 — Duplicated dispatch-loop implementation across two entry points (door-parity risk) (proposed severity: LOW-MEDIUM)**
- Class: Door Parity / Maintainability. Lens: Door Parity, Correctness. Pipeline stage: S6.
- Expected: one dispatch implementation backing every door, so a fix (e.g. F1) lands everywhere at once.
- Observed: `consult/route.ts` (~L900-970) inlines a near-duplicate of `evidence_stage.ts`'s (L75-105) submit/executeWithCache/toolEventLog loop; both share the `getSharedQosDispatchQueue()` singleton but are separately maintained.
- Code anchor: `platform/src/app/api/chat/consult/route.ts:900-970`; `platform/src/lib/pariprashna/pipeline/evidence_stage.ts:75-105`.
- Proposed fix class: extract the shared dispatch-loop body into one function both routes call.
- Rung achieved: INTEGRATION (code read, both call sites confirmed).

## Positive findings (not defects)

- **P1**: Parallelism is real and effective (ratio 0.17–0.26, not serial) — S6's core dispatch mechanism does what it claims.
- **P2**: Explicit tool rejections are honestly reported end-to-end (queue → evidence_stage → completeness receipt), demonstrated live under test.
- **P3**: `cap_tripped` (prashna_ask path) is a genuine earned signal for what it claims to measure — a real detector, not a stub, per §N.8's own test.
- **P4**: Queue fairness/WRR/concurrency-bound mechanics add negligible (~2%) overhead over the theoretical minimum under simulated concurrent load; the concurrency ceiling itself was never breached in any test.
