---
artifact: GANGA_OVERNIGHT_RUN_v1_0
version: 1.0
status: CURRENT
backfill_note: >
  Frontmatter backfilled by governance hygiene pass following PR #111 SESSION_HALT.md AC.7.
  Existing file body untouched.
---

# GANGA OVERNIGHT SEQUENTIAL RUN — v1.0
# 8 Sessions · Commit-per-session · Unattended · Bypass permissions ON
# Paste this entire file into Google Anti-Gravity IDE (Claude Code Extension)
# Open Anti-Gravity at: /Users/Dev/Vibe-Coding/Apps/Ganga

---

You are executing the Project Ganga overnight sequential run.
This covers 8 sub-sessions of coding work, running one after another without stopping.
You will commit after every session close. You will update GANGA_PHASE_TRACKER.md at every close.
You will NOT stop between sessions. You will NOT ask for approval. You will NOT ask clarifying questions.
Make reasonable implementation decisions and proceed.

Working directory: /Users/Dev/Vibe-Coding/Apps/Ganga
Branch: feature/ganga-umbrella

FAULT TOLERANCE RULES (read once, apply always):
- If tsc has errors: grep for "tests/" in the error output. Errors only in test files = pre-existing baseline, not a blocker. Errors in src/ = fix before committing.
- If npm test has new failures: check if they existed before your changes using `git stash && npm test && git stash pop` to compare. Pre-existing failures = not a blocker.
- If a session partially completes: commit what was done with a note in the commit message, mark partial in GANGA_PHASE_TRACKER.md, then proceed to the next session.
- HARD RULE across ALL sessions: never modify platform/src/lib/pipeline/manifest_planner.ts. toolChoice:'required' is architecturally correct — the bug was the wrong model ID, not this convention.
- HARD RULE: never modify STACK_ROUTING.deepseek.synthesis (deepseek-v4-pro is confirmed working in production).

SESSION SEQUENCE:
  S1 — GANGA-P1-R2-S1 — PLANNER-FIX        (Gate G1)
  S2 — GANGA-P2-R1-S1 — CI-GATE            (Gate G2-A)
  S3 — GANGA-P2-R2-S1 — NIM-COMPAT         (Gate G2-B)
  S4 — GANGA-P2-R2-S2 — CIRCUIT-BREAKER    (Gate G2-C)
  S5 — GANGA-P3-R1-S1 — SYNTH-PROMPT       (Gate G3-L1)
  S6 — GANGA-P3-R1-S2 — EVAL-HARNESS       (Gate G3-L2)
  S7 — GANGA-P3-R2-S1 — B11-ENFORCE        (Gate G3-L3)
  S8 — GANGA-P3-R2-S2 — CTX-ASSEMBLER      (Gate G3-L4)

════════════════════════════════════════════════════════════════
PRE-RUN VERIFICATION
════════════════════════════════════════════════════════════════

Run these checks before Session 1. Note results but do not abort on failure:

```bash
git log --oneline -5
# Confirm: feature/ganga-umbrella, G0 audit commit near top

git status
# Confirm: clean working tree

ls 00_ARCHITECTURE/MODEL_REGISTRY_v1_0.md 00_ARCHITECTURE/GANGA_PHASE_TRACKER.md 00_ARCHITECTURE/GANGA_STACK_AUDIT_v1_0.md
# Confirm: G0 artifacts present

grep -c "deepseek-v4-flash" platform/src/lib/models/registry.ts
# Confirm: multiple hits (these are what Session 1 fixes)

cd platform && node -e "require('./node_modules/.bin/tsc')" 2>/dev/null; npx tsc --noEmit 2>&1 | grep -c "error TS" || echo "0 tsc errors"
# Baseline tsc error count for comparison
```

Record the baseline tsc error count. Begin Session 1.


════════════════════════════════════════════════════════════════
SESSION 1 of 8 — GANGA-P1-R2-S1 — PLANNER-FIX
Gate: G1 | DeepSeek Model-ID production blocker fix
════════════════════════════════════════════════════════════════

may_touch:    platform/src/lib/models/registry.ts
must_not_touch: platform/src/lib/pipeline/manifest_planner.ts (toolChoice:required is correct)
must_not_touch: STACK_ROUTING.deepseek.synthesis (deepseek-v4-pro confirmed working)

Root cause: deepseek-v4-flash is not a valid DeepSeek API model ID. The API silently routes it
to deepseek-reasoner, which rejects toolChoice:'required'. This causes 100% planner fallback.
Fix: replace all routing references with deepseek-chat (the correct non-thinking alias).

IMPLEMENTATION — 6 targeted changes to platform/src/lib/models/registry.ts:

Read the file first to find exact line numbers, then make these edits:

CHANGE 1 — FAMILY_WORKER['deepseek']:
  Find:    deepseek:  'deepseek-v4-flash',
  Replace: deepseek:  'deepseek-chat',                    // non-thinking, supports tool_choice; deepseek-v4-flash is not a valid API model ID

CHANGE 2 — STACK_ROUTING.deepseek.planner_fast.primary:
  Find the planner_fast block under deepseek routing and change:
    primary:  'deepseek-v4-flash',  →  primary:  'deepseek-chat',  // non-thinking, supports toolChoice — deepseek-v4-flash is not a valid API ID

CHANGE 3 — STACK_ROUTING.deepseek.context_assembly.primary:
  Find the context_assembly block under deepseek routing and change:
    primary:  'deepseek-v4-flash',  →  primary:  'deepseek-chat',  // non-thinking, correct API ID

CHANGE 4 — STACK_ROUTING.deepseek.worker.primary:
  Find the worker block under deepseek routing and change:
    primary:  'deepseek-v4-flash',  →  primary:  'deepseek-chat',  // non-thinking, correct API ID

CHANGE 5 — deepseek-chat model entry in MODELS array — un-deprecate:
  Find the entry with id: 'deepseek-chat' and update only these three fields:
    label:     'DeepSeek Chat (V4 Flash)',
    hint:      'DeepSeek planner + worker — non-thinking, supports tool_choice. API alias for V4 Flash non-thinking.',
    speedTier: 'fast',
  Leave all other fields on this entry unchanged.

CHANGE 6 — deepseek-v4-flash model entry in MODELS array — mark invalid:
  Find the entry with id: 'deepseek-v4-flash' and update only label and hint:
    label: 'DeepSeek V4 Flash [internal label only]',
    hint:  '⚠ Not a valid DeepSeek API model ID — API maps this to deepseek-reasoner which rejects toolChoice. Use deepseek-chat for planner/worker calls. Retain entry in case DeepSeek publishes this ID officially.',

VERIFY:
```bash
# Must show deepseek-v4-flash ONLY in the model entry definition, NOT in routing tables
grep -n "deepseek-v4-flash" platform/src/lib/models/registry.ts

# Must show deepseek-chat in FAMILY_WORKER + planner_fast + context_assembly + worker
grep -n "deepseek-chat" platform/src/lib/models/registry.ts

# synthesis routing must still use deepseek-v4-pro (unchanged)
grep -n "synthesis" platform/src/lib/models/registry.ts | grep deepseek

# manifest_planner.ts must be unchanged
git diff platform/src/lib/pipeline/manifest_planner.ts
# Expected: empty

cd platform && npx tsc --noEmit 2>&1 | grep -v "tests/" | grep "error TS" | head -10
npm test 2>&1 | tail -15
```

SESSION 1 COMMIT:
```bash
git add platform/src/lib/models/registry.ts
git commit -m "GANGA-P1-R2-S1: fix DeepSeek planner model-ID (BF.GAP.001)

registry.ts 6 changes — deepseek-v4-flash → deepseek-chat in routing tables:
- FAMILY_WORKER['deepseek'], planner_fast.primary, context_assembly.primary, worker.primary
- deepseek-chat entry: un-deprecated (label/hint/speedTier=fast)
- deepseek-v4-flash entry: hint warns not a valid API ID
manifest_planner.ts not touched. synthesis routing unchanged."
```

TRACKER UPDATE — Session 1:
In 00_ARCHITECTURE/GANGA_PHASE_TRACKER.md update:
- G1 status: 🟢 COMPLETE
- GANGA-P1-R2-S1: ✅
- Add note: "BF.GAP.001 fixed. Observation checkpoint recommended before P2-R1-S2 (E2E-OBS) but code sessions can proceed."
- Increment completed_items_count by 2 (K.4 registry-fix, K.5 planner-route-fix)

```bash
git add 00_ARCHITECTURE/GANGA_PHASE_TRACKER.md
git commit -m "tracker: G1 COMPLETE — GANGA-P1-R2-S1 PLANNER-FIX"
```

▶ SESSION 1 CLOSED — PROCEED IMMEDIATELY TO SESSION 2


════════════════════════════════════════════════════════════════
SESSION 2 of 8 — GANGA-P2-R1-S1 — CI-GATE
Gate: G2-A | GitHub Actions CI + planner regression test suite
════════════════════════════════════════════════════════════════

may_touch:    .github/workflows/ci.yml (CREATE)
              platform/tests/planner/regression.test.ts (CREATE)
must_not_touch: platform/src/** (except where a new file is required for test support)

Goal: Automated CI gate that runs on every PR. Three jobs: tsc, unit tests, planner regression.
Planner regression tests are mocked (no LLM calls, no API keys required).

STEP 2A — Read existing test infrastructure:
```bash
ls platform/tests/ 2>/dev/null
find platform/tests -name "*.test.ts" 2>/dev/null | head -10
cat platform/vitest.config.ts 2>/dev/null || cat platform/vitest.config.js 2>/dev/null
cat platform/package.json | grep -A5 '"scripts"'
```

STEP 2B — Create .github/workflows/ci.yml:

Create this file at the repo root (not inside /platform):

```yaml
name: CI — Ganga Quality Gate

on:
  push:
    branches: [main, 'feature/**', 'feature/ganga-*']
  pull_request:
    branches: [main]

jobs:
  typecheck:
    name: TypeScript (src only)
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: platform
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: platform/package-lock.json
      - run: npm ci
      - name: tsc — src only (exclude tests)
        run: npx tsc --noEmit --skipLibCheck 2>&1 | grep -v "tests/" || true

  unit-tests:
    name: Unit Tests
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: platform
    env:
      NODE_ENV: test
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: platform/package-lock.json
      - run: npm ci
      - run: npm test -- --reporter=verbose 2>&1 | tail -40

  planner-regression:
    name: Planner Regression Gate
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: platform
    env:
      NODE_ENV: test
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: platform/package-lock.json
      - run: npm ci
      - name: Planner regression tests (no LLM, no secrets)
        run: npx vitest run tests/planner --reporter=verbose
```

STEP 2C — Create platform/tests/planner/regression.test.ts:

First read platform/src/lib/models/registry.ts to understand exported names for MODELS, STACK_ROUTING, FAMILY_WORKER. Then create the test file:

The test file must:
1. Import MODELS array and STACK_ROUTING and FAMILY_WORKER from the registry (use the correct import path)
2. Verify deepseek planner_fast.primary === 'deepseek-chat' (not deepseek-v4-flash) — this is the BF.GAP.001 regression guard
3. Verify deepseek-v4-flash does NOT appear in any stack's primary or fallback routing
4. Verify all 5 stacks (anthropic, gemini, gpt, deepseek, nim) have planner_fast defined
5. Verify FAMILY_WORKER entries all correspond to model IDs that exist in the MODELS array
6. Verify deepseek-chat model entry does NOT have "deprecated" in its label or hint

Use vitest. No mocking needed — these are pure data assertions on the registry object.

If the import paths for STACK_ROUTING/FAMILY_WORKER are not exported from registry.ts, read the file and adjust the imports/test approach to match what IS exported — the goal is to assert the routing correctness.

STEP 2D — Run and verify:
```bash
cd platform && npx vitest run tests/planner --reporter=verbose 2>&1 | tail -20
# All tests must pass
```

SESSION 2 COMMIT:
```bash
git add .github/workflows/ci.yml platform/tests/planner/regression.test.ts
git commit -m "GANGA-P2-R1-S1: CI gate + planner regression tests

- .github/workflows/ci.yml: typecheck + unit-tests + planner-regression jobs
- tests/planner/regression.test.ts: BF.GAP.001 regression guard + 5 stack coverage assertions
No LLM calls, no API keys — CI-safe."
```

TRACKER UPDATE — Session 2:
In GANGA_PHASE_TRACKER.md:
- Mark A-series CI items ✅ (A.1 CI setup, A.2 planner regression gate)
- Increment completed_items_count

```bash
git add 00_ARCHITECTURE/GANGA_PHASE_TRACKER.md
git commit -m "tracker: GANGA-P2-R1-S1 CI-GATE COMPLETE"
```

▶ SESSION 2 CLOSED — PROCEED IMMEDIATELY TO SESSION 3


════════════════════════════════════════════════════════════════
SESSION 3 of 8 — GANGA-P2-R2-S1 — NIM-COMPAT
Gate: G2-B | NIM stack toolChoice compatibility hardening
════════════════════════════════════════════════════════════════

may_touch:    platform/src/lib/providers/nvidia.ts (or wherever NIM provider logic lives — find it)
              platform/src/lib/pipeline/manifest_planner.ts (READ ONLY — do not edit)
              platform/tests/ (new NIM-specific test file)
must_not_touch: manifest_planner.ts (read to understand, do not change)

Goal: Harden the NIM provider path so that:
(a) PlanInputJsonSchema validation errors are caught and reported clearly
(b) NIM-specific toolChoice rejection errors are caught before they bubble up as unhandled
(c) The NIM planner fallback path is tested

STEP 3A — Read existing NIM provider code:
```bash
find platform/src -name "nvidia*" -o -name "nim*" 2>/dev/null | grep -v node_modules
find platform/src -name "*.ts" | xargs grep -l "nvidia\|nim\|nemotron" 2>/dev/null | grep -v node_modules | head -10
```

Read the files found. Also read manifest_planner.ts lines around PlanInputJsonSchema to understand the NIM workaround (read only).

STEP 3B — Read planner circuit breaker (read only for context):
```bash
cat platform/src/lib/pipeline/planner_circuit_breaker.ts 2>/dev/null | head -60
```

STEP 3C — Implement NIM hardening in the provider layer:

Based on what you read, make these improvements to the NIM provider file(s):

1. **Error classification**: Add or improve error detection for "does not support tool_choice" and "does not support response_format" patterns. These should be caught and re-thrown as a typed `PlannerCompatibilityError` (or the project's existing error type — use whatever exists) so the circuit breaker can detect them specifically.

2. **PlanInputJsonSchema validation**: If the NIM provider constructs or validates the PlanInputJsonSchema before sending to the API, add a pre-flight check that the schema is non-null and has the expected `tool_calls` array field. Log a warning (not an error throw) if the schema looks malformed — don't block on it.

3. **Retry safeguard**: If there is retry logic in the NIM provider path, ensure that a `toolChoice rejected` error does NOT trigger a retry (it's deterministic — retrying will always fail). Add a `shouldRetry` check that returns false for toolChoice compatibility errors.

4. **Logging**: Ensure that when the NIM path is taken vs. the standard toolChoice path, a structured log entry notes which path was used (e.g., `planner_mode: 'schema'` vs `planner_mode: 'toolchoice'`). Check if such logging exists already before adding.

Keep changes minimal and targeted. Do not refactor the NIM provider beyond these 4 improvements.

STEP 3D — Add a test file:
Create platform/tests/planner/nim_compat.test.ts with unit tests for the error classification logic (mock the API response to return a toolChoice rejection, verify it's caught correctly).

STEP 3E — Verify:
```bash
cd platform && npx tsc --noEmit 2>&1 | grep -v "tests/" | grep "error TS" | head -10
npx vitest run tests/planner --reporter=verbose 2>&1 | tail -20
```

SESSION 3 COMMIT:
```bash
git add platform/src/ platform/tests/planner/nim_compat.test.ts
git commit -m "GANGA-P2-R2-S1: NIM stack toolChoice compatibility hardening

B-series: error classification for toolChoice/response_format rejection,
PlanInputJsonSchema pre-flight validation, retry safeguard for compat errors,
planner_mode logging (schema vs toolchoice path).
manifest_planner.ts not touched."
```

TRACKER UPDATE — Session 3:
In GANGA_PHASE_TRACKER.md: Mark B-series NIM compat items ✅. Increment count.
```bash
git add 00_ARCHITECTURE/GANGA_PHASE_TRACKER.md
git commit -m "tracker: GANGA-P2-R2-S1 NIM-COMPAT COMPLETE"
```

▶ SESSION 3 CLOSED — PROCEED IMMEDIATELY TO SESSION 4


════════════════════════════════════════════════════════════════
SESSION 4 of 8 — GANGA-P2-R2-S2 — CIRCUIT-BREAKER
Gate: G2-C | Planner circuit breaker hardening
════════════════════════════════════════════════════════════════

may_touch:    platform/src/lib/pipeline/planner_circuit_breaker.ts
              platform/tests/planner/circuit_breaker.test.ts (CREATE or extend)
must_not_touch: manifest_planner.ts

Goal: Enhance the circuit breaker so it tracks failures per-stack, supports half-open state,
and exposes metrics for the monitoring layer.

STEP 4A — Read the current circuit breaker thoroughly:
```bash
cat platform/src/lib/pipeline/planner_circuit_breaker.ts
```

Read every line. Understand: current state machine states, failure threshold, reset logic, which fields are tracked.

STEP 4B — Also read how it's called:
```bash
grep -rn "planner_circuit_breaker\|PlannerCircuitBreaker\|circuitBreaker" platform/src --include="*.ts" | grep -v node_modules | head -20
```

STEP 4C — Implement these enhancements (only what is missing — don't duplicate existing logic):

1. **Per-stack failure tracking**: If the circuit breaker currently uses a single global failure counter, upgrade it to track failures per stack key (e.g., 'anthropic', 'gemini', 'gpt', 'deepseek', 'nim'). The circuit should open per-stack, not globally. If per-stack tracking already exists, verify it and move on.

2. **Half-open state**: If a HALF_OPEN state doesn't exist, add it. After the circuit opens and `resetTimeoutMs` elapses, transition to HALF_OPEN. In HALF_OPEN, allow one trial request through. On success → CLOSED. On failure → OPEN again with doubled timeout (up to a cap of e.g. 5 minutes).

3. **Metrics export**: Add a `getMetrics()` method (or ensure one exists) that returns a plain object: `{ stack: string, state: 'OPEN'|'HALF_OPEN'|'CLOSED', failureCount: number, lastFailureAt: number|null, consecutiveSuccesses: number }[]`. This is what the monitoring dashboard (Session 5, deferred) will read.

4. **Compatibility error fast-open**: If a `PlannerCompatibilityError` (the error type from Session 3) is thrown, immediately open the circuit for that stack without waiting for the failure threshold — a compatibility error is deterministic and will always fail.

Keep the interface backward-compatible. Existing call sites must not need changes.

STEP 4D — Update or create tests:
```bash
find platform/tests -name "*circuit*" -o -name "*breaker*" 2>/dev/null
```
If tests exist, add tests for per-stack isolation and half-open. If not, create platform/tests/planner/circuit_breaker.test.ts covering: OPEN→HALF_OPEN transition, half-open success→CLOSED, half-open failure→OPEN, per-stack isolation (one stack open does not open others), getMetrics() shape.

STEP 4E — Verify:
```bash
cd platform && npx tsc --noEmit 2>&1 | grep -v "tests/" | grep "error TS" | head -10
npx vitest run tests/planner --reporter=verbose 2>&1 | tail -20
```

SESSION 4 COMMIT:
```bash
git add platform/src/lib/pipeline/planner_circuit_breaker.ts platform/tests/
git commit -m "GANGA-P2-R2-S2: circuit breaker hardening

C-series: per-stack failure tracking, HALF_OPEN state with exponential backoff,
getMetrics() export for monitoring layer, compat-error fast-open.
Backward-compatible interface."
```

TRACKER UPDATE — Session 4:
In GANGA_PHASE_TRACKER.md: Mark C-series circuit breaker items ✅. Increment count.
```bash
git add 00_ARCHITECTURE/GANGA_PHASE_TRACKER.md
git commit -m "tracker: GANGA-P2-R2-S2 CIRCUIT-BREAKER COMPLETE"
```

▶ SESSION 4 CLOSED — PROCEED IMMEDIATELY TO SESSION 5


════════════════════════════════════════════════════════════════
SESSION 5 of 8 — GANGA-P3-R1-S1 — SYNTH-PROMPT
Gate: G3-L1 | Synthesis prompt governance — Workstream L.1
════════════════════════════════════════════════════════════════

may_touch:    00_ARCHITECTURE/SYNTHESIS_PROMPT_v1_0.md (CREATE)
              platform/src/lib/synthesis/ (READ to understand existing prompts, may add reference)
must_not_touch: platform/src/app/api/chat/consume/route.ts (will be touched in S7)

Goal: Author the synthesis prompt governance document — the canonical specification for what
the synthesis LLM must do, how it must traverse the knowledge layers, and how B.11 is enforced.
This is a governance doc (markdown), not code. It becomes the specification that Sessions 7 and 8 implement.

STEP 5A — Read existing synthesis infrastructure:
```bash
ls platform/src/lib/synthesis/
cat platform/src/lib/synthesis/single_model_strategy.ts | head -80
# Understand how synthesis is currently invoked and what context is passed
find platform/src -name "*.ts" | xargs grep -l "systemPrompt\|SYNTHESIS\|holistic" 2>/dev/null | grep -v node_modules | head -10
```

Read relevant synthesis prompt strings in the codebase to understand current state before specifying improvements.

STEP 5B — Read canonical governance artifacts for B.11 context:
```bash
head -100 01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md 2>/dev/null || echo "L1 data present"
head -50 00_ARCHITECTURE/PROJECT_GANGA_PLAN_v1_0.md | grep -A 20 "L.1\|SYNTHESIS_PROMPT\|B.11"
```

STEP 5C — Create 00_ARCHITECTURE/SYNTHESIS_PROMPT_v1_0.md:

Write a comprehensive governance document with this structure:

```
---
title: "MARSYS-JIS Synthesis Prompt Governance"
version: 1.0
status: CURRENT
created_date: 2026-05-04
session_id: GANGA-P3-R1-S1
canonical_id: SYNTHESIS_PROMPT
---

# SYNTHESIS_PROMPT — Synthesis LLM Governance Specification

## §1 — Purpose and scope
[What this document governs: the system prompt given to the synthesis LLM at query time]

## §2 — B.11 Whole-Chart-Read Protocol (MANDATORY)
[Specification: every synthesis call MUST have traversed MSR + UCN + CDLM + CGM + RM
 before the synthesis LLM is invoked. Define what "traversed" means operationally:
 context from each of these artifacts must be present in the assembled context.
 Define the runtime guard that enforces this — what to check, what to throw if missing.]

## §3 — Layer traversal mandate
[Specify the order: L1 (facts) → L2.5 (MSR/UCN/CDLM/CGM/RM holistic synthesis) → 
 L3 (query-specific retrieval). Synthesis LLM sees assembled output of all three.
 Define minimum required tokens from each layer.]

## §4 — Synthesis prompt template specification
[Specify the system prompt sections: role, knowledge layer access, B.10 discipline
 (never fabricate astrological computations — mark as [EXTERNAL_COMPUTATION_REQUIRED]),
 B.3 derivation ledger (every claim must cite a fact ID), disclosure tier awareness,
 calibration language (probabilistic, not oracular).]

## §5 — Prompt versioning protocol
[How to version the synthesis prompt: SYNTHESIS_PROMPT_v{major}.{minor}.
 Major bump: structural changes to layer traversal or B.11 enforcement.
 Minor bump: wording improvements, few-shot updates.
 Eval required before any major bump ships to production.]

## §6 — Evaluation criteria
[What a synthesis answer must achieve: layer coverage score, derivation ledger
 completeness, citation accuracy, calibration language, B.11 compliance signal.
 These are the criteria the eval harness (Session 6) will score against.]

## §7 — Known gaps and open items
[Reference GAP.013 (no synthesis governance — this doc closes it).
 Note what still needs wiring in code: B.11 runtime guard (Session 7),
 context assembler (Session 8), calibration substrate (P3-R3-S1).]

## §8 — Changelog
[v1.0: Initial specification — GANGA-P3-R1-S1]
```

Write each section with enough depth to be actionable by Sessions 6-8. Sections §2, §4 and §6 are the most critical and should be the most detailed.

SESSION 5 COMMIT:
```bash
git add 00_ARCHITECTURE/SYNTHESIS_PROMPT_v1_0.md
git commit -m "GANGA-P3-R1-S1: SYNTHESIS_PROMPT_v1_0.md — synthesis governance (L.1)

Closes GAP.013 (zero synthesis governance). Specifies:
- B.11 whole-chart-read protocol mandatory pre-check
- Layer traversal mandate (L1 → L2.5 → L3)
- Synthesis prompt template §4
- Eval criteria for Session 6 harness
- Versioning protocol"
```

TRACKER UPDATE — Session 5:
In GANGA_PHASE_TRACKER.md: Mark L.1 ✅. Increment count.
```bash
git add 00_ARCHITECTURE/GANGA_PHASE_TRACKER.md
git commit -m "tracker: GANGA-P3-R1-S1 SYNTH-PROMPT COMPLETE"
```

▶ SESSION 5 CLOSED — PROCEED IMMEDIATELY TO SESSION 6


════════════════════════════════════════════════════════════════
SESSION 6 of 8 — GANGA-P3-R1-S2 — EVAL-HARNESS
Gate: G3-L2 | Answer eval harness — Workstream L.2
════════════════════════════════════════════════════════════════

may_touch:    platform/scripts/answer_eval.ts (CREATE)
              platform/scripts/golden_queries.ts (CREATE)
              platform/package.json (ADD npm script)
must_not_touch: platform/src/app/api/ (eval harness calls the API externally, not inline)

Goal: Create an offline eval harness that scores synthesis answers against the criteria
defined in SYNTHESIS_PROMPT_v1_0.md §6. The harness runs golden queries against the
live /api/rag/synthesize endpoint and scores each answer.

STEP 6A — Read synthesis endpoint to understand its interface:
```bash
find platform/src -name "route.ts" | xargs grep -l "synthesize\|rag" 2>/dev/null | head -5
cat platform/src/app/api/rag/synthesize/route.ts 2>/dev/null || find platform/src -path "*/rag/synthesize*" | head -5
```

Read the synthesize endpoint's request/response shape.

STEP 6B — Read SYNTHESIS_PROMPT_v1_0.md §6 (eval criteria, just authored in Session 5):
```bash
grep -A 30 "§6" 00_ARCHITECTURE/SYNTHESIS_PROMPT_v1_0.md
```

STEP 6C — Create platform/scripts/golden_queries.ts:

Define 15 golden queries covering the main query categories. Each golden query has:
- `id`: string (e.g., "GQ-001")
- `query`: string (the natural language question)
- `category`: 'factual' | 'interpretive' | 'predictive' | 'holistic' | 'discovery'
- `expected_layers`: string[] (which L2.5 artifacts should be consulted: 'MSR'|'UCN'|'CDLM'|'CGM'|'RM')
- `must_not_fabricate`: string[] (astrological values that must be cited from L1, not invented)
- `min_citation_count`: number (minimum number of L1 fact citations expected)

Include at least:
- 3 factual queries (e.g., "What is my ascendant?", "Which planets are in the 7th house?")
- 3 interpretive queries (e.g., "What does my Saturn placement indicate for career?")
- 3 holistic queries (e.g., "What are the dominant themes in my chart?") — these must trigger B.11
- 3 discovery queries (e.g., "What is interesting about my chart that I might not know?")
- 3 predictive queries (e.g., "What themes might emerge in the next 6 months?")

STEP 6D — Create platform/scripts/answer_eval.ts:

The eval harness should:

1. Accept a BASE_URL env var (default: http://localhost:3000) and optional --query-id flag
2. For each golden query (or just the specified one):
   a. POST to {BASE_URL}/api/rag/synthesize with the query
   b. Collect the response (handle streaming if needed — concatenate chunks)
   c. Score against these criteria (each 0–1, reported as a percentage):
      - `layer_coverage`: Did the response mention/use data from the expected_layers? (scan for layer artifact names)
      - `b10_compliance`: Does it avoid fabricated numbers? (detect [EXTERNAL_COMPUTATION_REQUIRED] markers vs naked numerical claims for positions)
      - `b11_signal`: Does the response show evidence of holistic synthesis (cross-layer references)?
      - `citation_presence`: Citation count ≥ min_citation_count?
      - `calibration_language`: Uses probabilistic framing ("may indicate", "suggests", "likely") rather than oracular ("will happen", "definitely")?
3. Print a formatted table per query: query_id | category | layer_coverage | b10 | b11 | citations | calibration | PASS/FAIL
4. Print aggregate: total queries, pass rate, score per dimension

Handle network errors gracefully — if the endpoint is unreachable, skip that query and note it.

STEP 6E — Add npm script:
In platform/package.json, add to scripts:
  "answer:eval": "npx tsx scripts/answer_eval.ts"

STEP 6F — Verify it compiles:
```bash
cd platform && npx tsc --noEmit 2>&1 | grep -v "tests/" | grep "error TS" | head -10
# It should compile cleanly. If the endpoint is not reachable at eval time that's fine —
# compilation errors are not acceptable.
```

SESSION 6 COMMIT:
```bash
git add platform/scripts/answer_eval.ts platform/scripts/golden_queries.ts platform/package.json
git commit -m "GANGA-P3-R1-S2: answer eval harness + 15 golden queries (L.2)

Closes GAP.014 (no answer eval). Scores 5 criteria per answer:
layer_coverage, b10_compliance, b11_signal, citation_presence, calibration_language.
Run: npm run answer:eval (requires live endpoint at BASE_URL)"
```

TRACKER UPDATE — Session 6:
In GANGA_PHASE_TRACKER.md: Mark L.2 ✅. Increment count.
```bash
git add 00_ARCHITECTURE/GANGA_PHASE_TRACKER.md
git commit -m "tracker: GANGA-P3-R1-S2 EVAL-HARNESS COMPLETE"
```

▶ SESSION 6 CLOSED — PROCEED IMMEDIATELY TO SESSION 7


════════════════════════════════════════════════════════════════
SESSION 7 of 8 — GANGA-P3-R2-S1 — B11-ENFORCE
Gate: G3-L3 | B.11 runtime enforcement guard — Workstream L.3
════════════════════════════════════════════════════════════════

may_touch:    platform/src/app/api/chat/consume/route.ts
              platform/src/lib/synthesis/single_model_strategy.ts
              platform/src/lib/synthesis/b11_guard.ts (CREATE — extract guard into own module)
must_not_touch: manifest_planner.ts

Goal: Add a runtime guard that enforces B.11 — every synthesis call must have assembled
context from at least the MSR, UCN, and CGM artifacts (the minimum holistic synthesis set).
If the assembled context is missing these, log a warning and either (a) attempt retrieval
or (b) annotate the synthesis response as [B.11-PARTIAL].

STEP 7A — Read the synthesis pipeline thoroughly:
```bash
cat platform/src/lib/synthesis/single_model_strategy.ts
cat platform/src/app/api/chat/consume/route.ts 2>/dev/null | head -150
```

Read to understand: how is context assembled before synthesis? What does the context object look like? Where does the synthesis LLM call happen?

STEP 7B — Read SYNTHESIS_PROMPT_v1_0.md §2 (B.11 spec from Session 5):
```bash
grep -A 20 "§2" 00_ARCHITECTURE/SYNTHESIS_PROMPT_v1_0.md
```

STEP 7C — Create platform/src/lib/synthesis/b11_guard.ts:

This module exports:

```typescript
export interface B11CheckResult {
  compliant: boolean;
  presentLayers: string[];   // which L2.5 layers are present in the context
  missingLayers: string[];   // which required L2.5 layers are absent
  annotation: string | null; // "[B.11-PARTIAL: missing MSR, CGM]" or null if compliant
}

export const B11_REQUIRED_LAYERS = ['MSR', 'UCN', 'CGM'] as const;
export const B11_FULL_LAYERS = ['MSR', 'UCN', 'CDLM', 'CGM', 'RM'] as const;

/**
 * Checks whether the assembled synthesis context satisfies B.11.
 * Looks for layer artifact references in the context string/object.
 * Returns a B11CheckResult indicating compliance level.
 */
export function checkB11Compliance(contextPayload: unknown): B11CheckResult
```

Implementation of `checkB11Compliance`:
- Accept the context payload (string, array of strings, or whatever shape the codebase uses — adapt to actual type)
- Stringify it and check for presence of each layer's canonical artifact names:
  - MSR: "MSR" or "Master Signal Register" or "025_HOLISTIC_SYNTHESIS/MSR"
  - UCN: "UCN" or "Unified Chart Narrative" or "025_HOLISTIC_SYNTHESIS/UCN"
  - CDLM: "CDLM" or "Cross-Domain Linkage"
  - CGM: "CGM" or "Causal Graph Model" or "025_HOLISTIC_SYNTHESIS/CGM"
  - RM: "RM" or "Resonance Map" or "025_HOLISTIC_SYNTHESIS/RM"
- Return compliance status and annotation

STEP 7D — Wire b11_guard into the synthesis path:

In single_model_strategy.ts (and/or route.ts — wherever synthesis is assembled before the LLM call):
1. Import { checkB11Compliance, B11CheckResult } from '../synthesis/b11_guard' (adjust path)
2. Before invoking the synthesis LLM, call checkB11Compliance(assembledContext)
3. If result.compliant === false:
   - Log a structured warning: `{ event: 'B11_VIOLATION', missing: result.missingLayers, queryId }`
   - If the synthesis call is in a position where additional retrieval can be triggered synchronously, attempt to fetch the missing layers. If not (or if retrieval fails), proceed with synthesis but prepend result.annotation to the system prompt context.
4. If result.compliant === true: proceed normally (no overhead in the happy path)

Keep the wiring minimal — do not restructure the synthesis pipeline. The guard is additive.

STEP 7E — Add a test:
Create platform/tests/synthesis/b11_guard.test.ts:
- Test: context with all 5 layers → compliant: true, annotation: null
- Test: context missing CGM and RM → compliant: false, missingLayers: ['CGM', 'RM']
- Test: context missing all layers → compliant: false, all B11_REQUIRED_LAYERS in missing
- Test: annotation string format matches "[B.11-PARTIAL: missing X, Y]"

STEP 7F — Verify:
```bash
cd platform && npx tsc --noEmit 2>&1 | grep -v "tests/" | grep "error TS" | head -10
npx vitest run tests/synthesis --reporter=verbose 2>&1 | tail -20
```

SESSION 7 COMMIT:
```bash
git add platform/src/lib/synthesis/b11_guard.ts \
        platform/src/lib/synthesis/single_model_strategy.ts \
        platform/src/app/api/chat/consume/route.ts \
        platform/tests/synthesis/b11_guard.test.ts
git commit -m "GANGA-P3-R2-S1: B.11 runtime enforcement guard (L.3)

Closes GAP.015 (no B.11 runtime enforcement).
- b11_guard.ts: checkB11Compliance() — detects missing L2.5 layers in context
- Wired into synthesis path: logs B11_VIOLATION + annotates response if partial
- Happy path zero-overhead (check is string scan, not retrieval call)
- 4 unit tests for compliance/violation/annotation cases"
```

TRACKER UPDATE — Session 7:
In GANGA_PHASE_TRACKER.md: Mark L.3 ✅. Increment count.
```bash
git add 00_ARCHITECTURE/GANGA_PHASE_TRACKER.md
git commit -m "tracker: GANGA-P3-R2-S1 B11-ENFORCE COMPLETE"
```

▶ SESSION 7 CLOSED — PROCEED IMMEDIATELY TO SESSION 8


════════════════════════════════════════════════════════════════
SESSION 8 of 8 — GANGA-P3-R2-S2 — CTX-ASSEMBLER
Gate: G3-L4 | Context assembler — Workstream L.4
════════════════════════════════════════════════════════════════

may_touch:    platform/src/lib/synthesis/context_assembler.ts (CREATE)
              platform/src/lib/synthesis/single_model_strategy.ts (wire in assembler)
              platform/tests/synthesis/context_assembler.test.ts (CREATE)
must_not_touch: manifest_planner.ts

Goal: Create a dedicated context assembler that packs L1 facts, L2.5 holistic synthesis
artifacts, and L3 query-specific retrieval results into a token-budgeted context payload
for the synthesis LLM. This replaces any ad-hoc context assembly in the synthesis path.

STEP 8A — Read the current context assembly in the synthesis path:
```bash
cat platform/src/lib/synthesis/single_model_strategy.ts
grep -n "context\|prompt\|system\|assemble\|pack" platform/src/lib/synthesis/single_model_strategy.ts | head -30
```

Understand exactly how context is currently assembled. Note: is there already a context assembly step? What format does the synthesis LLM expect?

STEP 8B — Read any existing context utility files:
```bash
ls platform/src/lib/synthesis/
find platform/src -name "*context*" -o -name "*assembl*" 2>/dev/null | grep -v node_modules
```

STEP 8C — Create platform/src/lib/synthesis/context_assembler.ts:

Design this module based on what you read about the current synthesis flow. It should export:

```typescript
export interface LayerContext {
  layer: 'L1' | 'L2_5' | 'L3';
  artifactId: string;     // e.g. 'MSR', 'UCN', 'CGMC', 'query_retrieval'
  content: string;
  tokenEstimate: number;  // rough estimate: Math.ceil(content.length / 4)
  priority: number;       // 1 = highest (keep even if budget tight), 3 = lowest (drop first)
}

export interface AssemblyOptions {
  maxTokens: number;       // total token budget for assembled context (default: 12000)
  requiredLayers: string[]; // artifact IDs that must be included even if over budget
  queryId?: string;
}

export interface AssemblyResult {
  assembledContext: string;   // the final packed string for the synthesis LLM
  includedArtifacts: string[]; // which artifact IDs made it in
  droppedArtifacts: string[];  // which were dropped due to budget
  totalTokenEstimate: number;
  b11Compliant: boolean;       // convenience: did required L2.5 layers make it in?
}

/**
 * Assembles a token-budgeted context payload from layer contexts.
 * Respects priority ordering: required layers first, then by priority asc.
 * Separates layers with clear headers so the synthesis LLM can navigate them.
 */
export function assembleContext(
  layers: LayerContext[],
  options?: Partial<AssemblyOptions>
): AssemblyResult
```

Implementation of `assembleContext`:
1. Sort layers: required layers first (by requiredLayers match), then by priority ascending
2. Greedily pack layers into the budget (maxTokens), skipping those that don't fit
3. Always include requiredLayers even if they push over budget (with a warning log)
4. Format the assembled string with section headers:
   ```
   === L1: CHART FACTS ===
   {L1 content}
   
   === L2.5: MSR — MASTER SIGNAL REGISTER ===
   {MSR content}
   
   === L2.5: CGM — CAUSAL GRAPH MODEL ===
   {CGM content}
   
   === L3: QUERY RETRIEVAL ===
   {L3 retrieval content}
   ```
5. Call checkB11Compliance from b11_guard.ts on the assembled string to set b11Compliant

STEP 8D — Wire context_assembler into single_model_strategy.ts:

In single_model_strategy.ts:
1. Import { assembleContext, LayerContext } from './context_assembler'
2. Find where context is currently assembled (the code that builds the prompt/context object)
3. Replace or wrap that assembly with a call to assembleContext, mapping existing context pieces to LayerContext objects with appropriate layer/artifactId/priority values
4. Pass the AssemblyResult.assembledContext to the synthesis LLM call
5. Log assembly result metadata (includedArtifacts, droppedArtifacts, totalTokenEstimate, b11Compliant) as a structured event

Keep it minimal — if the current context assembly is simple, the wrapping will be simple.

STEP 8E — Create tests:
platform/tests/synthesis/context_assembler.test.ts:
- Test: layers within budget → all included, none dropped
- Test: layers over budget → priority-3 layers dropped before priority-1
- Test: required layers always included even when over budget
- Test: assembled string contains section headers for included layers
- Test: b11Compliant = true when MSR + UCN + CGM are present
- Test: b11Compliant = false when required L2.5 layers are missing

STEP 8F — Final verification:
```bash
cd platform && npx tsc --noEmit 2>&1 | grep -v "tests/" | grep "error TS" | head -10
npx vitest run tests/synthesis --reporter=verbose 2>&1 | tail -30
npm test 2>&1 | tail -20
```

SESSION 8 COMMIT:
```bash
git add platform/src/lib/synthesis/context_assembler.ts \
        platform/src/lib/synthesis/single_model_strategy.ts \
        platform/tests/synthesis/context_assembler.test.ts
git commit -m "GANGA-P3-R2-S2: context assembler — token-budgeted L1/L2.5/L3 packing (L.4)

Closes GAP.016 (no context assembler).
- context_assembler.ts: assembleContext() with priority-sorted token budgeting
- Integrates b11_guard.ts checkB11Compliance on assembled output
- Wired into single_model_strategy.ts replacing ad-hoc context assembly
- Section headers in assembled string for LLM navigation
- 6 unit tests for budget/priority/required/b11 cases"
```

TRACKER UPDATE — Session 8:
In GANGA_PHASE_TRACKER.md:
- Mark L.4 ✅
- Set P3 R1+R2 rounds status → 🟢 COMPLETE
- Increment completed_items_count
```bash
git add 00_ARCHITECTURE/GANGA_PHASE_TRACKER.md
git commit -m "tracker: GANGA-P3-R2-S2 CTX-ASSEMBLER COMPLETE — P3-R1+R2 done"
```


════════════════════════════════════════════════════════════════
FINAL SUMMARY REPORT
════════════════════════════════════════════════════════════════

After Session 8 commits, run this to generate a summary for the user:

```bash
echo "=== GANGA OVERNIGHT RUN — COMPLETION REPORT ==="
echo ""
echo "Git log (last 20 commits):"
git log --oneline -20
echo ""
echo "Working tree status:"
git status
echo ""
echo "Synthesis test results:"
cd platform && npx vitest run tests/synthesis --reporter=verbose 2>&1 | tail -30
echo ""
echo "Planner regression results:"
npx vitest run tests/planner --reporter=verbose 2>&1 | tail -20
echo ""
echo "TypeScript check (src only):"
npx tsc --noEmit 2>&1 | grep -v "tests/" | grep "error TS" | head -20 || echo "✅ No src/ errors"
echo ""
echo "=== FILES CREATED/MODIFIED IN THIS RUN ==="
git diff --name-only HEAD~20 HEAD 2>/dev/null | sort | uniq
echo ""
echo "=== TRACKER STATUS ==="
grep -E "completed_items_count|G0|G1|G2|G3|G4|🟢|🟡|🔴" 00_ARCHITECTURE/GANGA_PHASE_TRACKER.md | head -20
echo ""
echo "=== OVERNIGHT RUN COMPLETE ==="
echo "Sessions completed: S1(PLANNER-FIX) S2(CI-GATE) S3(NIM-COMPAT) S4(CIRCUIT-BREAKER)"
echo "                    S5(SYNTH-PROMPT) S6(EVAL-HARNESS) S7(B11-ENFORCE) S8(CTX-ASSEMBLER)"
echo ""
echo "DEFERRED (require human action or external services):"
echo "  - P2-R1-S2: E2E-OBS — requires live traffic observation (no code changes)"
echo "  - P2-R1-S3: PROMPT-EVAL — requires E2E observation data first"
echo "  - P2-R1-S4: DB-MIGRATIONS — requires Cloud SQL Auth Proxy running"
echo "  - P2-R3-S2: PHASE11B-CLEAN — requires 7-day production soak gate"
echo ""
echo "NEXT HUMAN STEPS:"
echo "  1. Review commits above, spot-check any session that reported partial completion"
echo "  2. Deploy the PLANNER-FIX (S1) and watch query_plan_log for plan_json != NULL"
echo "  3. Run Cloud SQL Auth Proxy and execute DB-MIGRATIONS (P2-R1-S4)"
echo "  4. After 24-48hr observation, run P2-R1-S2 (E2E-OBS) then P2-R1-S3 (PROMPT-EVAL)"
```
