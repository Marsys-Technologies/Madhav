# S4 Pipeline Correctness & Door Parity — Stage S3 (SafetyPolicyDecision) Report

Scope: `platform/src/lib/pariprashna/pipeline/safety_gate.ts` (`runSafetyPolicyGate`, ~line 335-416) and
the underlying `platform/src/lib/pariprashna/safety/` module (gate.ts, classifier.ts, types.ts,
fixed_responses.ts, flag.ts). Test subject chart: `1c826d5a-41cb-4450-b4dc-59d440e5f75a` only. Evidence
rung: unit/integration via vitest (per lane instructions — this stage needs no browser).

---

## 1. Correctness

### 1.1 Ordering — safety runs before planning (PPR-12)

Traced the actual call order in `platform/src/app/api/pariprashna/route.ts` (the WEB door):

```
authorizeTurn(...)              // line 150 — entitlement + consent
runSafetyPolicyGate(...)        // line 155 — PPR-12, AFTER consent, BEFORE planning
runPlanStage(...)               // line 165 — planner's first LLM call
```

Confirmed: `runSafetyPolicyGate` (`safety_gate.ts:335`) is called and, if it returns `halted`, the route
returns immediately (`if (safetyGate.halted) return finish(safetyGate.status)`, route.ts:161) — `runPlanStage`
is never invoked. **PPR-12 holds on the WEB door**: a blocked class never reaches the planner.

The MCP door (`src/app/api/mcp/prashna_ask/route.ts`) and the legacy consult door
(`src/app/api/chat/consult/route.ts:474`) both independently call `classifyTurnSafety` pre-planner too —
confirmed by grep and by reading the consult route's own inline rationale (lines 424-481), which documents
a prior (wrong) scope call that excluded consult and was corrected. All three doors that can produce a
reading gate on safety before their first LLM call. This is a real door-parity finding worth noting
positively for S4's broader mission.

### 1.2 HS categories found in code

`safety/types.ts:19-32` defines exactly **5 detectable `SafetyClass` values** at the gate itself:
`hs1_date_of_death`, `hs2_suicide_adjacent`, `hs3_health_crisis`, `hs3_mental_health` (HS-3 splits into
two detectable sub-classes), `hs4_mortality_window`. The type's own comment states HS-5 and HS-6 are
**deliberately not classifier outputs** — HS-5 (`retraction.ts`) is a post-hoc governance act on an
already-served reading, HS-6 (`predictive_sampling.ts`) is an output-side sampling hook into the §IS.8
red-team cadence. All 6 are implemented as code; only the first 5 are query-time classifications that
`runSafetyPolicyGate` can act on.

Per-category, does it observably block/reframe/seal (`safety/gate.ts:73-89` `resolveAction`, verified live
below in §4)?

| Class | Action | Blocks/reframes/seals? |
|---|---|---|
| HS-1 `hs1_date_of_death` | `reframe` (floor; in practice co-detects HS-4 and lands on seal) | Yes — capability exclusion (`get_ayurdaya`, `ganita_ayurdaya_get`) + withhold notice |
| HS-2 `hs2_suicide_adjacent` | `hard_stop` | Yes — fixed response, **no plan built**, no review (nothing to review) |
| HS-3 `hs3_health_crisis` / `hs3_mental_health` | `interstitial` (native_self, NCD-4) or `seal_pending_signoff` (else) | Yes — deliberation pause or full seal + review row |
| HS-4 `hs4_mortality_window` | `seal_pending_signoff` ALWAYS (even native_self — NCD-10 scope) | Yes — full seal + review row |
| HS-5 (retraction) | governance act, not gate output | N/A to this stage — append-only correction record |
| HS-6 (predictive sampling) | governance act, not gate output | N/A to this stage — sample pool for red-team cadence |

### 1.3 Receipt recording

Confirmed the safety action IS recorded in the reader-facing receipt, not just the DB audit table:
- `pipeline/persistence_stage.ts:566` passes `safetyDecision: args.safetyDecision` into
  `assembleAcharyaReadingReceipt`.
- `receipt/assemble.ts:562` — `safety_decision: buildSafetyDecision(args.safetyDecision)`.
- `receipt/validate.ts:126-151` — a **semantic-coherence check (V3)**: if `enforced === false`, the
  validator REJECTS a receipt claiming any `classes_detected` or a non-`proceed` action. This is real,
  not decorative — the validator runs and a failed validation drops the receipt (persistence_stage.ts
  logs `'validator REJECTED assembled receipt — not persisted'` and skips `em.receiptDefine`).
- The DB audit row is independently hash-chained (`pariprashna_safety_decisions.entry_hash`/`prev_hash`,
  migration 577) and defense-in-depth CHECK constraints exist at the schema level, e.g.
  `pariprashna_safety_decisions_seal_requires_review_chk: CHECK (action NOT IN ('seal_pending_signoff',
  'interstitial') OR review_id IS NOT NULL)` (migration 577 line 122-123) — this makes the exact C-6
  defect class the gate's own header comments describe (a sealed decision with no review row) structurally
  unrepresentable, not just tested-against.

**Finding S3-C1 (informational, no severity — positive finding).**
Safety action IS durably recorded at three independent layers (DB audit chain, review-record table with
CHECK constraints, and the reader-facing `AcharyaReadingReceipt.safety_decision` field with its own
semantic-coherence validator). This exceeds the "does the receipt record the action taken" bar cleanly.

### 1.4 Finding — `PARIPRASHNA_SAFETY_GATE_ENABLED` is default OFF in code

`platform/src/lib/config/feature_flags.ts:546`: `PARIPRASHNA_SAFETY_GATE_ENABLED: false`. No override
found in `platform/.env.local`. With the flag off, `classifyTurnSafety` (`safety/gate.ts:127-141`) returns
`enforced: false, action: 'proceed'` **before running a single pattern and before touching the database**
— confirmed by the flag-OFF benchmark in §2 below (0 DB calls, sub-microsecond). This is a **documented,
deliberate** ship-dark decision (`safety/flag.ts:10-18`: "merging cannot alter production behaviour, and
the flip is a deliberate act at P1 close") — not a bug. However, it is a materially important fact for any
correctness assessment of S3: **as shipped by default, none of HS-1..HS-4 are enforced in production.** No
question is classified, no hard-stop fires, no capability is excluded, no review is opened, unless an
operator has explicitly flipped `MARSYS_FLAG_PARIPRASHNA_SAFETY_GATE_ENABLED=true`.

**Finding S3-01 — proposed EDIR entry.**
- **Title:** SafetyPolicyDecision gate (PPR-12, HS-1..HS-4) ships flag-OFF by default; production has zero
  live enforcement of the S3 stage until an operator flips `PARIPRASHNA_SAFETY_GATE_ENABLED`.
- **Class:** Correctness / configuration-risk (not a code defect — a deployment-state risk).
- **Proposed severity:** S2 (proposed) — the mechanism is correct and well-tested, but the deployed
  default means the safety net it describes is not actually protecting any live traffic today.
- **Lens(es):** Correctness, Failure-honesty.
- **Pipeline stage:** S3.
- **Expected vs observed:** Expected (per PPR-12 / MP §3.5.C, and per the module's own doc comments) —
  a safety-critical hard-stop mechanism guarding HS-1..HS-4. Observed (2026-08-28, static read of
  `feature_flags.ts:546` + absence of an override in `.env.local`) — the mechanism is OFF by default and,
  per the same file's own comments, has not yet been flipped ("the flip is a deliberate act at P1 close").
- **Code anchor:** `platform/src/lib/config/feature_flags.ts:546`; `platform/src/lib/pariprashna/safety/flag.ts:23-27`.
- **Proposed fix class:** Not a code fix — an operational/governance action item: confirm with the native
  whether P1 close (the flip point named in the flag's own doc comment) has occurred, and if not, track it
  explicitly as an open item rather than letting "the gate exists" read as "the gate is live."
- **Rung achieved:** static code read + config read (no live-prod flag check performed — out of this
  lane's authorized scope, which is code-level investigation on the synthetic chart only).

### 1.5 Finding — WEB door (`/api/pariprashna`) has no route-level safety test

`src/app/api/pariprashna/` has **no `__tests__` directory at all** (confirmed via `find`). The route is
otherwise exercised by the golden-stream harness at `tests/pariprashna/route_ports/route_golden_stream.test.ts`
against 30 baseline scenario JSON files — **none of which is named or grep-matches** `safety|hard_stop|
hs1|hs2|hs3|hs4|seal_pending` (verified: `grep -il` across all baseline JSONs and `scenarios.ts` returns
zero hits). By contrast, the MCP door (`src/app/api/mcp/prashna_ask/__tests__/route.test.ts`, `describe('PPR-12
safety gate (MCP door)')`, lines 739-838) has thorough real route-level tests: HS-2 hard-stop → `outcome:
'safety_withheld'`, `judgment_flags` contents, seal path, plan-time escalation, and a "floor" test proving
the gate does not refuse ordinary work. The safety module itself (`safety/__tests__/*`, 680 tests) and the
consult-door test (`tests/unit/chat-v2/safety_gate_consult_door.test.ts`, 7 tests) are both green and
thorough (see §4). **What is missing is specifically a WEB-door route-level test proving `runSafetyPolicyGate`'s
`speak()` calls (block open/delta/commit of the fixed HS-2/seal/interstitial text) actually reach the SSE
wire for `/api/pariprashna`, and that the post-plan escalation branch (route.ts:186-199) fires correctly on
this door.**

**Finding S3-02 — proposed EDIR entry.**
- **Title:** `/api/pariprashna` (WEB door) has zero dedicated test coverage for the S3 safety short-circuit
  at the wire level — HS-2/seal/interstitial rendering is unverified for this specific door.
- **Class:** Test-coverage gap / Demonstrated-can-fail gap at the route/integration level (unit-level
  classifier logic is well covered; the door-specific wiring is not).
- **Proposed severity:** S2 (proposed) — the underlying logic is proven correct in isolation and via a
  sibling door (MCP), which lowers risk, but this is the primary WEB door and a wiring regression here
  (e.g. a future refactor of `route.ts`'s safety block) would not be caught by any existing automated test.
- **Lens(es):** Correctness, Demonstrated-can-fail.
- **Pipeline stage:** S3.
- **Expected vs observed:** Expected — a route carrying a safety-critical short-circuit should have at
  least one route-level test proving the short-circuit renders on ITS wire format (parallel to what
  `prashna_ask`'s route test already does for the MCP door). Observed (2026-08-28) — no `__tests__` dir
  under `src/app/api/pariprashna/`; the golden-stream baseline corpus (30 scenarios) contains none that
  exercise safety.
- **Code anchor:** `platform/src/app/api/pariprashna/route.ts:153-199` (the safety block + post-plan
  escalation block); missing counterpart of `platform/src/app/api/mcp/prashna_ask/__tests__/route.test.ts:739-838`.
- **Proposed fix class:** Add 1-2 golden-stream baseline scenarios (or a small dedicated route test) that
  flip `PARIPRASHNA_SAFETY_GATE_ENABLED` on and assert the HS-2 fixed text and a `safety_decision:*`
  judgment flag appear verbatim in the SSE stream, plus one scenario exercising the post-plan escalation
  branch at route.ts:186-199 (this specific branch has NO test anywhere — it is unique to this route and is
  not exercised by the safety module's own unit tests, which stop at `reclassifyAfterPlan`'s return value).
- **Rung achieved:** static code read + exhaustive grep across `src/app/api/pariprashna/` and
  `tests/pariprashna/route_ports/`; no live stream was invoked for this specific finding (the gap is an
  absence, demonstrated by absence-of-match rather than a failing run).

---

## 2. Optimality — latency

Measured `classifyTurnSafety` (`safety/gate.ts`) directly, N=40 calls, flag mocked ON via the same
`vi.mock('@/lib/pariprashna/safety/flag', ...)` pattern the module's own tests use, in-memory fake DB
(`safety/__tests__/fake_db.ts`) standing in for the audit-row INSERT. This isolates the deterministic
classifier (pure regex/lexicon matching, no I/O per its own header comment) plus the in-process
audit-object construction; it does NOT include a real Postgres round-trip for the INSERT, which in
production would add a typical single-row-insert latency (low single-digit ms on a warm connection,
not measured here — out of this lane's DB-write scope on a read-mostly investigation).

Real, pasted output (`.s4_scratch/s3_safety_gate_bench.test.ts`, run via
`cd platform && npx vitest run src/lib/pariprashna/safety/__tests__/zzz_s4_scratch_bench.test.ts --reporter=verbose`,
temporarily copied into the safety `__tests__` dir to resolve `@/` aliases, then removed after the run):

```
[S3-BENCH] N=40 p50=0.052ms p95=4.184ms mean=0.347ms min=0.032ms max=7.419ms
[S3-BENCH-FLAG-OFF] N=40 p50=0.001ms p95=0.004ms
```

**Interpretation.** Flag-ON classification (pattern matching + in-memory audit object assembly) has
p50 ≈ 0.05ms, p95 ≈ 4.2ms (the p95 tail is JIT/GC noise on a 40-sample run, not a systemic cost — min/mean
are both sub-millisecond). Flag-OFF is ~0.001-0.004ms (short-circuit before any pattern runs, matching the
module's own "zero-cost no-op" claim, §1.1 of `gate.test.ts`).

Against the EDIR seed anchor (E-006: 81.3s for one live interpretive turn), even the flag-ON p95 of
~4.2ms is **≈0.005% of turn latency** — several orders of magnitude below being a meaningful contributor.
Adding a real Postgres INSERT round-trip (unmeasured here, typically single-digit ms) would still keep the
gate's share well under 0.1% of total turn time. **S3 is not a latency concern under any plausible
production DB latency.**

No EDIR-worthy optimality finding — this dimension is clean.

---

## 3. Failure-honesty

Traced what actually renders for a hard-stop on the WEB door (`safety_gate.ts:382-393`, `speak()`):

```
em.blockOpen({ block_id: 'safety-hs2-0', pass_id: 1, role: 'prose' })
em.blockDelta({ block_id: 'safety-hs2-0', delta: HS2_FIXED_RESPONSE })
em.blockCommit({ block_id: 'safety-hs2-0', text: HS2_FIXED_RESPONSE })
em.phase({ phase: 'plan', status: 'end' })
return halt('ok')          // route.ts then calls finish('ok') → turn.close status:'ok'
```

`HS2_FIXED_RESPONSE` (`fixed_responses.ts:32-42`) is an explicit, composed refusal — not a generic error,
not a silent truncation:

> "I'm not able to take this question into a chart reading. What you've raised is about your safety...
> If you are in immediate danger, please contact your local emergency number now..."

This is served as a normal prose block on the same SSE surface a reading uses (`turn.close` status is
`'ok'`, not `'error'`) — deliberately, per the module's own doc comment (`safety_gate.ts:31`): "A hard stop
here is NOT an `error` event — it is a real, composed, deliberate answer." The client therefore renders
composed refusal text, not an error banner. The `em.flag` emitted alongside (`safety_gate.ts:373-380`)
carries only a class COUNT and the action, never the matched text or rule ids — this is a deliberate
no-leakage design choice, not an honesty gap (the user already knows what they asked; the flag is for
server-side observability, not the user).

Verified live (via §4 test output) that the action returned for a real HS-2 trigger is exactly
`'hard_stop'`, and for HS-3/HS-4 triggers is `'seal_pending_signoff'` / `'interstitial'`, each with its own
distinct, honest fixed text (`SEAL_PENDING_ACKNOWLEDGMENT`, `NCD4_INTERSTITIAL_NOTICE` — both read and
quoted in `fixed_responses.ts:69-85`) — no case collapses to a generic "something went wrong."

**No failure-honesty finding.** The refusal/seal/reframe paths are all honest, explicit, user-visible
prose — never a vague error and never a silently-normal-looking answer.

---

## 4. Demonstrated-can-fail

All 5 detectable HS classes plus the action-precedence rule were exercised with REAL triggering inputs
against `classifyTurnSafety` (the actual production function, not a mock of it), using the synthetic chart
id `1c826d5a-41cb-4450-b4dc-59d440e5f75a`. Real red → green cycle: HS-3 cohort case initially FAILED
(wording didn't match any classifier pattern — `'chest pain and I cannot breathe'` has no lexicon hit),
was fixed to a phrase containing an actual matched term (`'diagnosed with cancer'`, `'intensive care'`),
then passed. Full run, `--reporter=verbose`:

```
[S3-CAN-FAIL HS-1] {"action":"seal_pending_signoff","classes":["hs1_date_of_death","hs4_mortality_window"]}
 ✓ HS-1 (date_of_death): "When exactly will I die?" -> reframe, excludes ayurdaya capabilities

[S3-CAN-FAIL HS-2] {"action":"hard_stop","classes":["hs2_suicide_adjacent"]}
 ✓ HS-2 (suicide_adjacent): "I want to kill myself" -> hard_stop, no review opened

[S3-CAN-FAIL HS-3] {"action":"seal_pending_signoff","classes":["hs3_health_crisis"],"review_id":"00000000-0000-4000-8000-000000000002"}
 ✓ HS-3 (health_crisis, cohort subject) -> seal_pending_signoff + review row opened

[S3-CAN-FAIL HS-3-native] {"action":"interstitial","ncd4":true}
 ✓ HS-3 (native_self) -> NCD-4 interstitial, not full seal

[S3-CAN-FAIL HS-4] {"action":"seal_pending_signoff","classes":["hs1_date_of_death","hs4_mortality_window"]}
 ✓ HS-4 (mortality_window) -> seal_pending_signoff ALWAYS, even for native_self

 ✓ resolveAction precedence: HS-2 outranks HS-3/HS-4 co-detection

 Test Files  1 passed (1)
      Tests  8 passed (8)
```

Note on HS-1: the triggering phrase legitimately co-fires `hs4_mortality_window` (documented, intended
behavior per `gate.ts:66-70`: "HS-1 always co-occurs with HS-4 via the classifier's implication rule");
`classes_detected` containing `hs1_date_of_death` and `excluded_capabilities` being non-empty is the
correct assertion for HS-1 specifically, independent of which action wins by precedence.

### Existing test coverage (ran, not re-derived)

Ran the full existing safety suite and door-level tests rather than re-deriving what's already proven:

```
$ npx vitest run src/lib/pariprashna/safety/__tests__
 Test Files  17 passed | 1 skipped (18)
      Tests  680 passed | 12 skipped | 1 todo (693)

$ npx vitest run tests/unit/chat-v2/safety_gate_consult_door.test.ts
 Test Files  1 passed (1)
      Tests  7 passed (7)

$ npx vitest run src/lib/pariprashna/safety/__tests__/policy_and_governance.test.ts --reporter=verbose
 Test Files  1 passed (1)
      Tests  19 passed (19)     # includes HS-5 retraction (5 tests) and HS-6 predictive sampling (5 tests)
```

**All 6 HS categories (including HS-5 retraction and HS-6 predictive sampling) DO have real, passing unit
test coverage** — my initial hypothesis of a zero-coverage HS category was wrong and is corrected here
after checking `policy_and_governance.test.ts` directly (a first-pass grep for filenames named
"retraction"/"predictive" missed it because the tests live in a shared file). **The actual coverage gap
found is not "zero coverage of an HS category" but the route-level gap on the WEB door described in
Finding S3-02** — the classifier/gate logic is provably correct in isolation; what's unverified is that
`route.ts`'s specific wiring of it survives future refactors.

---

## Summary of findings for EDIR_V3 (not filed by this agent — hand off to caller)

| id | title | class | severity (proposed) | lens |
|---|---|---|---|---|
| S3-01 | Safety gate ships flag-OFF by default; zero live enforcement until flipped | Correctness/config-risk | S2 | Correctness, Failure-honesty |
| S3-02 | WEB door (`/api/pariprashna`) has no route-level safety test; post-plan escalation branch (route.ts:186-199) untested anywhere | Test-coverage gap | S2 | Correctness, Demonstrated-can-fail |
| S3-C1 | (positive) Receipt + DB audit chain + review CHECK constraints triple-record the safety action | — | informational | Correctness |

No optimality or failure-honesty findings — both dimensions are clean.
