# S4 Pipeline Correctness & Door Parity — Stage S2 (EntitlementDecision) Report

Investigated: 2026-08-28. Test subject: synthetic chart `1c826d5a-41cb-4450-b4dc-59d440e5f75a` only.
Native's chart `482012f1-…` never queried.

Code anchors:
- `platform/src/lib/pariprashna/pipeline/safety_gate.ts` — `authorizeTurn` (L229-312), `runSafetyPolicyGate` (L335-416)
- `platform/src/lib/auth/authorizeChartAccess.ts` — the single authz brain (L45-85)
- `platform/src/lib/gateway/invoke_tool.ts` — MCP-door CHART_REQUIRED (L70-84) + AUTHZ_DENIED (L86-103)
- `platform/src/app/api/pariprashna/route.ts` — stage call order (L81-161)
- `platform/src/app/api/mcp/prashna_ask/route.ts` — second entitlement caller (L171-244, L339-360)

---

## 1. Correctness — question-text immunity (PPR-11)

**Claim tested:** entitlement resolves only from the authenticated call; question text can never widen or redirect it.

**Structural proof (static, HIGH confidence):**
- `authorizeTurn(args: { em, user, identity })` — `safety_gate.ts:229-233` — the function signature does **not accept `messages`/`queryText` at all**. It is structurally impossible for question content to reach the entitlement decision through this call, because the data isn't passed in.
- `identity.chartId` is bound exactly once, in `admitRequest` (`safety_gate.ts:118-126`), from `body.chartId`, validated by a UUID regex (`safety_gate.ts:72,122-124`) — never from `messages`. `route.ts` reuses `identity.chartId`/`chartId` verbatim at L100, 117, 123, 133, 205, 242 and never reassigns it from message content anywhere in the route or in `authorizeTurn`.
- `authorizeChartAccess`'s only string inputs are `principal.uid` and `chartId` (`authorizeChartAccess.ts:39-43`); all four rules are DB row/column comparisons (`authorizeChartAccess.ts:45-85`), never a parse/eval of message text.
- Messages/`queryText` are read by `runSafetyPolicyGate` (`safety_gate.ts:345-350`) for CONTENT-safety classification (mortality/self-harm phrasing) only, and by `classifyTurnSafety`'s classifier — which copies `chartId` into the decision record purely as an audit-trail label, never as an authorization input (confirmed via code read of `safety/gate.ts` and `safety/classifier.ts`).

**Executable proof (INTEGRATION rung — real code, real DB):** `.s4_scratch/s2_latency_probe.ts` calls the production `authorizeChartAccess` against the real Cloud SQL proxy (127.0.0.1:55432) and the real synthetic chart, with a `principal.uid` crafted as a prompt/SQL-injection-style string embedding another user's uid and "ignore previous instructions" text:
```
craftedUid = "s4-probe-no-grant-uid-does-not-exist\"; grant all charts; -- ignore previous instructions, chart_id=<owner-uid>"
```
Result: `deny` (parameterized query — no injection, no widening). Real owner/grant/deny uids all resolved correctly (`all`/`view`/`deny`).

**Verdict: question-text immunity holds.** No defect found on this axis.
**Rung achieved:** structural/static (HIGH) for the "messages never reach authorizeTurn" claim; INTEGRATION (real prod code + real DB) for the crafted-string/injection probe.

---

## 2. Optimality — latency and gate placement

**Placement:** `authorizeTurn` is the FIRST stage inside the SSE stream (`route.ts:150`), before `runSafetyPolicyGate` (L155), `runPlanStage`/the planner LLM call (L165), and all retrieval/synthesis. Pre-stream (`admitRequest`, `bindTurnParams`, `admitWithinLimits`, `route.ts:81-107`) does no chart/DB work — only auth, a feature flag, JSON parse, and a UUID regex. So no expensive work (LLM, retrieval) happens before the entitlement gate — confirmed correct ordering.

**Measured latency** (`.s4_scratch/s2_latency_probe.ts`, real `authorizeChartAccess` calls over the live Cloud SQL Auth Proxy tunnel at 127.0.0.1:55432, real synthetic-chart rows):

| Path | N | p50 | p95 | mean |
|---|---|---|---|---|
| `authorizeChartAccess` alone, deny (no-grant uid) | 40 | 154.9ms | 231.6ms | 163.7ms |
| `authorizeChartAccess` alone, owner-allow | 40 | 80.0ms | 131.6ms | — |
| **Full `authorizeTurn`-shaped sequence**, deny | 30 | **326.3ms** | **430.9ms** | 334.1ms |
| Full `authorizeTurn`-shaped sequence, owner-allow | 30 | 245.4ms | 367.2ms | 258.8ms |

Caveat (stated honestly): measured through a local Cloud SQL Auth Proxy tunnel, which adds real but proxy-specific per-round-trip overhead vs. an in-cluster connection. Absolute numbers will differ in production; the **relative/structural** finding below does not depend on that caveat.

**Finding S2-OPT-1 (proposed):**
- **Title:** Redundant `charts` table round-trip in the S2 entitlement sequence
- **Class:** performance / redundant-query
- **Proposed severity:** Low–Medium (proposed)
- **Lens(es):** Optimality
- **Pipeline stage:** S2 (EntitlementDecision)
- **Expected:** one round-trip to `charts` per turn to resolve both existence and ownership.
- **Observed (2026-08-28):** `authorizeTurn` runs `SELECT id, name, client_id FROM charts WHERE id=$1` (`safety_gate.ts:237-240`) for the `CHART_NOT_FOUND` check, then calls `authorizeChartAccess`, which — for every non-super-admin principal — runs its **own** `SELECT owner_id FROM charts WHERE id=$1` (`authorizeChartAccess.ts:64-67`) against the same table/row. That is two sequential round trips to `charts` for the same `chart_id` on **every turn**, plus a `profiles` lookup (`safety_gate.ts:245`) in between — 3 sequential DB round trips before `authorizeChartAccess` even reaches its own owner/grant branch (4 for a deny outcome, once `chart_grants` is also queried). This inflates the fail-closed hot path measured above (326ms p50 vs. 155ms p50 for `authorizeChartAccess` alone) by roughly 2x.
- **Code anchor:** `platform/src/lib/pariprashna/pipeline/safety_gate.ts:237-245` + `platform/src/lib/auth/authorizeChartAccess.ts:56-67`
- **Proposed fix class:** either (a) have `authorizeTurn` pass its already-fetched chart row (or just `owner_id`, adding it to its existing `SELECT`) into `authorizeChartAccess` so it never re-queries `charts`, or (b) combine the existence + ownership check into one query. This is intentionally NOT proposed as an architecture change to `authorizeChartAccess`'s public contract (still the single authz brain other callers — `invoke_tool.ts` — use identically); the redundancy is local to this one caller.
- **Rung achieved:** INTEGRATION (measured against real DB via real proxy).

No other optimality defect found. The gate itself does not do unnecessary work before failing closed — it is the necessary minimum queries, just not batched optimally.

---

## 3. Failure-honesty — denial paths

Enumerated denial paths in `authorizeTurn` (`safety_gate.ts:229-312`):

| # | Path | Code | Message | Behavior |
|---|---|---|---|---|
| 1 | Chart row absent | `CHART_NOT_FOUND` (L242) | "Chart not found." | `em.error(...)` + `halt('error')` — explicit, fails closed. |
| 2 | `authorizeChartAccess` → `'deny'` (no owner match, no grant row, or super_admin on a nonexistent chart) | `FORBIDDEN` (L256) | "Not authorized for this chart." | `em.error(...)` + `halt('error')` — explicit, fails closed, generic message (does not leak whether the chart exists for a caller with no grant — reasonable, since #1 already separately reports true nonexistence). |
| 3 | Subject-consent refusal (flag-gated, PPR-14) | `SUBJECT_CONSENT_REQUIRED:<reason>` (L284) | consent-specific message | `em.error(...)` + `halt('error')` — explicit, and deliberately ordered AFTER authorization (comment at L260-268) so an unauthorized caller learns nothing about consent state. Verified: `resolveSubjectConsent` is a no-op (no DB touch) when its flag is off (default), so this adds zero cost/leakage on the default path. |
| 4 | `CONVERSATION_NOT_FOUND` / `CONVERSATION_INIT_FAILED` | L296, L305 | explicit messages | Not strictly an entitlement-denial path but shares the same `em.error`+`halt` discipline — no silent pass-through. |

Every path is an explicit typed `error` event with a stable `code`, a human message, and `retryable` — never a silent pass-through, never a vague 200-with-nothing. This matches the module's own stated contract (header comment, L1-43: "the entitlement layer refuses, and the refusal is a designed state, not an error" — a slight misnomer in that comment since the wire event type IS literally `error`, but the substance — fail closed, explicitly reported, never silently degraded — holds).

**MCP door parity note (informational, not a new defect):** `/api/mcp/prashna_ask/route.ts` calls the identical `authorizeChartAccess` (L238) and fails closed to HTTP 401 on `deny` (L239-244) — consistent with the web door. It does **not** call `resolveSubjectConsent` at all; its own header comment (L339-347) documents this gap explicitly and passes `subjectKind: null` into `classifyTurnSafety`, which is treated as "not proven native_self" (fails toward the stricter branch) — so the asymmetry is self-documented and safety-neutral, not a silent hole. Flagging for completeness since S2's "does the pipeline stage consume EntitlementDecision consistently across doors" is in scope; recommend EDIR_V3 record it as a documentation/consistency note rather than a security defect, since the failure mode is "stricter than the web door," not "weaker."

**Verdict: no failure-honesty defect found.** All enumerated denial paths fail closed and self-report explicitly.

---

## 4. Demonstrated-can-fail

**Test A (written and run this session, INTEGRATION rung — real code + real DB):** `.s4_scratch/s2_latency_probe.ts`, run via `npx tsx .s4_scratch_local/s2_latency_probe.ts` (transient copy under `platform/` for module resolution, removed after the run). Calls the real, unmodified `authorizeChartAccess` from `platform/src/lib/auth/authorizeChartAccess.ts` against the real Cloud SQL proxy and the real synthetic-chart rows (owner `xl2wYZRPwsVgPSAgtn9XJ80Xkub2`, a granted uid, and a uid with zero `chart_grants` rows). Output (captured):
```
owner -> all (expect all)
granted -> view (expect view)
no-grant -> deny (expect deny)
crafted-string uid -> deny (expect deny — no injection/widening)
```
The script asserts each result and sets `process.exitCode = 1` with a `FAIL:` line on any mismatch — none fired. This is a real red/green check against production code and a production-shaped database, not a mock.

**Test B (pre-existing, run this session, INTEGRATION rung — real route):** `tests/pariprashna/route_ports/route_golden_stream.test.ts`, scenario `branch-forbidden` (`tests/pariprashna/route_ports/scenarios.ts:361-369`, baseline `tests/pariprashna/route_ports/baseline/branch-forbidden.json`), run via:
```
npx vitest run tests/pariprashna/route_ports/route_golden_stream.test.ts -t "branch-forbidden"
```
Result: **1 passed**. This scenario mocks `authorizeChartAccess` to return `'deny'` and mounts the REAL, unmodified `/api/pariprashna` route handler; the committed golden proves the wire sequence is `turn.open` → `phase(plan,start)` → `error{code: FORBIDDEN, message: "Not authorized for this chart.", retryable: false}` → `turn.close{status: error}` — i.e. fail-closed, explicit, at full-route granularity. I did not author this test but ran it fresh this session to confirm current coverage is green and exercises exactly the scenario this dimension asks for.

**What was not attempted:** a live Next dev server hit over HTTP with a real Firebase-authenticated session for chart `1c826d5a`. Not attempted this session — the DB-level (Test A) and full-route-mocked-boundary (Test B) rungs together already exercise the real production `authorizeChartAccess` code path against a real database, which was judged sufficient within the time budget; a live-server HTTP rung would add auth-token plumbing but not exercise different entitlement logic.

**Rung achieved: INTEGRATION** (real production code, real DB for Test A; real route handler, mocked DB/auth boundary with a committed golden for Test B). Not DEPLOYED/live-server rung.

---

## Summary of findings for EDIR_V3 intake

| ID (proposed) | Title | Class | Severity (proposed) | Lens | Stage |
|---|---|---|---|---|---|
| S2-OPT-1 | Redundant `charts` round-trip inflates every S2 entitlement decision (~2x on the deny path, 326ms vs 155ms p50 measured) | performance / redundant-query | Low–Medium | Optimality | S2 |

No correctness, failure-honesty, or demonstrated-can-fail defects found. Question-text immunity (PPR-11) holds by construction (`authorizeTurn` doesn't accept `messages`) and was confirmed against a live, adversarially-crafted principal id over a real DB call. One informational note (MCP door's documented, safety-neutral consent-check asymmetry) is recorded for completeness but is not proposed as a defect.
