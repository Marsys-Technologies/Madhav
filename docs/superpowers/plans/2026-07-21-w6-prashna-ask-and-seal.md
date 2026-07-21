# W6 — prashna_ask + Seal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship `prashna_ask` as a real MCP tool wrapping the W4 planner→floor→loop→gates engine (job-handle async transport, dual cost caps, NO-LEAKAGE arm-2 enforcement + CI canary), E2E-verify it live, build genuine load-test tooling and run it against the deployed connector, then seal the whole retrieval-implementation campaign (W1–W6) with the docs/registry closeout the master brief's §H requires.

**Architecture:** `prashna_ask` is a thin MCP-tool wrapper: it validates the C-1 signature (`{chart_id, question, scope_tuple?, response_format}` — no `depth` param), opens a job via a new `JobRegistry` (in-memory, chart-scoped), calls the existing `callPipelinePlanner` → `compileFloorForPlan` → engine loop unmodified, streams MCP-spec `notifications/progress` on the same connection keyed by `progressToken`, and enforces two independent caps (tool-call count ≤10 default, wall-clock ≤120s default) that fail *honestly* — partial result + completeness receipt + `judgment_flag` naming which cap tripped, never silent truncation. NO-LEAKAGE arm-2 is enforced by a projection-compiler filter (drop any capability with `calibration_context_only: true` from the tool set `prashna_ask`'s loop is allowed to call) plus a CI canary that fails the build if a leaked capability is ever reachable. The engine itself (`pipeline_planner.ts`, `compiled_floor_adapter.ts`) is treated as FROZEN for this wave — if it seems to need a change, that's a STOP-and-report per the user's explicit instruction, not a fork.

**Tech Stack:** TypeScript, Next.js API routes (`platform/src/app/api`), MCP SDK (`@modelcontextprotocol/sdk`) in `platform-mcp/src`, Vitest/Jest (match existing test runner — confirm via `platform/package.json` / `platform-mcp/package.json`), existing `chat/consult` route patterns as the sync-tool precedent.

---

## Ground truth carried in from research (do not re-derive)

- Engine entry points, already merged and NOT to be modified: `platform/src/lib/pipeline/pipeline_planner.ts` (`callPipelinePlanner`, line 349), `platform/src/lib/pipeline/compiled_floor_adapter.ts` (`compileFloorForPlan`, line 185), `platform/src/lib/vidhi/scope_classifier.ts`.
- Existing spike (reference only, not the shipped tool): `platform/src/lib/pipeline/prashna_ask_spike.ts` — exports `prashnaAskSpike(...)`, `PrashnaAskSpikeResult`, `PrashnaAskSpikeOptions`, `PrashnaAskSpikeOutcomeError`. W6's real implementation supersedes this file; it is not deleted until the new path is live-verified (then retire it — don't leave two).
- `calibration_context_only?: boolean` already exists on `CapabilityDescriptor` in `platform/src/lib/retrieval/registry/types.ts` (~line 356-365) with a doc comment naming `prashna_ask` explicitly. The flag is set on the right descriptors already (per W5); W6 only adds the *filter* that reads it and the CI canary.
- `platform-mcp/src/lib/response_budget.ts` and `platform/src/lib/retrieval/envelope.ts` are the existing byte/token density-budget precedent to model the new cost-cap module's "fail honestly, never silently thin" discipline on (CLAUDE.md §N.6).
- No job-handle, progress-notification, or cost-cap infrastructure exists anywhere in the repo today — Tasks 1-3 below are genuinely net-new, not integration.
- D-4b (a separate concurrent campaign) just opened and is entering a multi-agent swarm phase — confirmed NOT quiet. **Do not touch `impl/w5-breaking` in this plan.** Re-check liveness (`git branch -a`, `gh pr list --state open`) immediately before Task 14 (the flip), not from this stale note.
- User's ratified doctrine (binding, not a suggestion): cap-exceeded → return the grounded partial result + completeness receipt naming unserved floor items + a `judgment_flag` naming which cap stopped the run. Never silently truncate and present as complete.
- W4 measured: ~51s total request, ~38.7s synthesis alone → the wall-clock cap default of 120s and call-count cap of ≤10 are both real, not arbitrary; confirm against `platform/src/lib/pipeline/__tests__/prashna_ask_spike.test.ts`'s recorded timings before finalizing defaults in Task 3.

## File Structure

New files (Phase 1 core):
- `platform-mcp/src/lib/job_registry.ts` — in-memory job store: create/get/update/complete, chart-scoped, TTL eviction.
- `platform-mcp/src/lib/cost_caps.ts` — `CostCapTracker` class: call-count + wall-clock tracking, `checkAndMaybeStop()` returning a discriminated result the loop checks each iteration.
- `platform-mcp/src/lib/no_leakage_filter.ts` — `filterLeakedCapabilities(capabilities: CapabilityDescriptor[]): CapabilityDescriptor[]` dropping `calibration_context_only: true` entries; used to build the tool set passed into the engine loop for `prashna_ask` specifically (NOT applied to other tools' registries).
- `platform-mcp/src/tools/register_prashna_ask.ts` — the actual MCP tool: request schema (C-1 signature), calls `callPipelinePlanner`/`compileFloorForPlan` via a shared bridge, wires job registry + progress notifications + cost caps + leakage filter.
- `platform-mcp/src/lib/prashna_ask_bridge.ts` — thin adapter calling into `platform/src/lib/pipeline/pipeline_planner.ts`'s exported functions from the MCP process (confirm at Task 4 whether this requires an HTTP call to the Next.js app or a direct import — the existing spike test's "boundary-mocked, no live DB creds" caveat suggests MCP and web may run as separate deployables; resolve this via Task 4's spike, don't assume).
- Test files mirrored under `platform-mcp/src/__tests__/` and `platform-mcp/src/tools/__tests__/` per existing convention (check `m0_entitlement_gate.test.ts` for the pattern).

Modified files:
- `platform/src/lib/retrieval/registry/types.ts` — no new fields expected (calibration_context_only exists); confirm at Task 6, add only if the filter needs a field that isn't there.
- `platform-mcp/src/server.ts` — register the new tool.
- CI config (find via `find .github/workflows -iname "*.yml"`) — add the NO-LEAKAGE canary job.

## Standards this plan must satisfy (binding, from CLAUDE.md + master brief)

- B.10 no fabricated computation — the engine already only ever returns grounded facts; the wrapper must not invent numbers when a cap trips.
- §N.6 Serving Density Principle — cap-exceeded is reported via a `judgment_flags` entry, never a silently-thinned response.
- §I.6 breaking-release hold rule — `impl/w5-breaking` stays parked pending a fresh D-4b liveness check.
- Master brief §G — every PR message cites its plan row (W6/C-1/F-R7/W-17/W-19 etc.), surgical migrations only, no secrets in code/logs.

---

## Phase 1: prashna_ask core contract (TDD, sequential — shared files)

### Task 1: Job registry

**Files:**
- Create: `platform-mcp/src/lib/job_registry.ts`
- Test: `platform-mcp/src/lib/__tests__/job_registry.test.ts`

- [ ] **Step 1: Write the failing test**

```typescript
import { describe, it, expect, vi } from 'vitest';
import { JobRegistry } from '../job_registry';

describe('JobRegistry', () => {
  it('creates a job and retrieves it by id', () => {
    const registry = new JobRegistry();
    const job = registry.create({ chartId: 'chart-1' });
    expect(job.status).toBe('pending');
    expect(registry.get(job.id)?.chartId).toBe('chart-1');
  });

  it('updates progress and marks complete', () => {
    const registry = new JobRegistry();
    const job = registry.create({ chartId: 'chart-1' });
    registry.updateProgress(job.id, { message: 'compiling floor', pct: 40 });
    expect(registry.get(job.id)?.progress?.pct).toBe(40);
    registry.complete(job.id, { ok: true, data: { answer: 'x' } });
    expect(registry.get(job.id)?.status).toBe('complete');
  });

  it('evicts jobs older than the TTL', () => {
    const registry = new JobRegistry({ ttlMs: 1000 });
    const job = registry.create({ chartId: 'chart-1' });
    vi.useFakeTimers();
    vi.advanceTimersByTime(2000);
    registry.sweepExpired();
    expect(registry.get(job.id)).toBeUndefined();
    vi.useRealTimers();
  });

  it('scopes jobs by chart — get() with wrong chartId assertion is caller responsibility, registry stores chartId for the caller to check', () => {
    const registry = new JobRegistry();
    const job = registry.create({ chartId: 'chart-A' });
    expect(registry.get(job.id)?.chartId).toBe('chart-A');
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd platform-mcp && npx vitest run src/lib/__tests__/job_registry.test.ts`
Expected: FAIL — `job_registry` module not found.

- [ ] **Step 3: Write minimal implementation**

```typescript
export type JobStatus = 'pending' | 'running' | 'complete' | 'failed';

export interface JobProgress {
  message: string;
  pct: number;
}

export interface Job<TResult = unknown> {
  id: string;
  chartId: string;
  status: JobStatus;
  progress?: JobProgress;
  result?: TResult;
  error?: string;
  createdAt: number;
}

export class JobRegistry<TResult = unknown> {
  private jobs = new Map<string, Job<TResult>>();
  private ttlMs: number;

  constructor(opts: { ttlMs?: number } = {}) {
    this.ttlMs = opts.ttlMs ?? 15 * 60 * 1000;
  }

  create(input: { chartId: string }): Job<TResult> {
    const job: Job<TResult> = {
      id: crypto.randomUUID(),
      chartId: input.chartId,
      status: 'pending',
      createdAt: Date.now(),
    };
    this.jobs.set(job.id, job);
    return job;
  }

  get(id: string): Job<TResult> | undefined {
    return this.jobs.get(id);
  }

  updateProgress(id: string, progress: JobProgress): void {
    const job = this.jobs.get(id);
    if (!job) return;
    job.status = 'running';
    job.progress = progress;
  }

  complete(id: string, result: TResult): void {
    const job = this.jobs.get(id);
    if (!job) return;
    job.status = 'complete';
    job.result = result;
  }

  fail(id: string, error: string): void {
    const job = this.jobs.get(id);
    if (!job) return;
    job.status = 'failed';
    job.error = error;
  }

  sweepExpired(): void {
    const now = Date.now();
    for (const [id, job] of this.jobs) {
      if (now - job.createdAt > this.ttlMs) this.jobs.delete(id);
    }
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd platform-mcp && npx vitest run src/lib/__tests__/job_registry.test.ts`
Expected: PASS (4/4)

- [ ] **Step 5: Commit**

```bash
git add platform-mcp/src/lib/job_registry.ts platform-mcp/src/lib/__tests__/job_registry.test.ts
git commit -m "feat(w6): job registry for prashna_ask async transport (W6/C-1)"
```

---

### Task 2: Cost cap tracker (dual: call-count + wall-clock, fail-honest)

**Files:**
- Create: `platform-mcp/src/lib/cost_caps.ts`
- Test: `platform-mcp/src/lib/__tests__/cost_caps.test.ts`

- [ ] **Step 1: Write the failing test**

```typescript
import { describe, it, expect, vi } from 'vitest';
import { CostCapTracker } from '../cost_caps';

describe('CostCapTracker', () => {
  it('allows calls under both caps', () => {
    const tracker = new CostCapTracker({ maxCalls: 10, maxWallClockMs: 120_000 });
    for (let i = 0; i < 9; i++) {
      expect(tracker.checkAndRecordCall().stopped).toBe(false);
    }
  });

  it('stops on call-count cap and reports which cap tripped', () => {
    const tracker = new CostCapTracker({ maxCalls: 2, maxWallClockMs: 120_000 });
    tracker.checkAndRecordCall();
    tracker.checkAndRecordCall();
    const result = tracker.checkAndRecordCall();
    expect(result.stopped).toBe(true);
    expect(result.reason).toBe('call_count_cap');
  });

  it('stops on wall-clock cap independent of call count', () => {
    vi.useFakeTimers();
    const tracker = new CostCapTracker({ maxCalls: 10, maxWallClockMs: 1000 });
    vi.advanceTimersByTime(1500);
    const result = tracker.checkAndRecordCall();
    expect(result.stopped).toBe(true);
    expect(result.reason).toBe('wall_clock_cap');
    vi.useRealTimers();
  });

  it('never silently truncates — stopped result always carries a judgmentFlag', () => {
    const tracker = new CostCapTracker({ maxCalls: 1, maxWallClockMs: 120_000 });
    tracker.checkAndRecordCall();
    const result = tracker.checkAndRecordCall();
    expect(result.judgmentFlag).toBe('cost_cap_call_count_exceeded');
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd platform-mcp && npx vitest run src/lib/__tests__/cost_caps.test.ts`
Expected: FAIL — module not found.

- [ ] **Step 3: Write minimal implementation**

```typescript
export interface CostCapConfig {
  maxCalls: number;
  maxWallClockMs: number;
}

export type CostCapStopReason = 'call_count_cap' | 'wall_clock_cap';

export interface CostCapCheckResult {
  stopped: boolean;
  reason?: CostCapStopReason;
  judgmentFlag?: string;
  callsMade: number;
  elapsedMs: number;
}

export class CostCapTracker {
  private calls = 0;
  private readonly startedAt = Date.now();
  private readonly config: CostCapConfig;

  constructor(config: CostCapConfig) {
    this.config = config;
  }

  checkAndRecordCall(): CostCapCheckResult {
    const elapsedMs = Date.now() - this.startedAt;
    if (elapsedMs > this.config.maxWallClockMs) {
      return {
        stopped: true,
        reason: 'wall_clock_cap',
        judgmentFlag: 'cost_cap_wall_clock_exceeded',
        callsMade: this.calls,
        elapsedMs,
      };
    }
    if (this.calls >= this.config.maxCalls) {
      return {
        stopped: true,
        reason: 'call_count_cap',
        judgmentFlag: 'cost_cap_call_count_exceeded',
        callsMade: this.calls,
        elapsedMs,
      };
    }
    this.calls += 1;
    return { stopped: false, callsMade: this.calls, elapsedMs };
  }
}

export const DEFAULT_COST_CAPS: CostCapConfig = {
  maxCalls: 10,
  maxWallClockMs: 120_000,
};
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd platform-mcp && npx vitest run src/lib/__tests__/cost_caps.test.ts`
Expected: PASS (4/4)

- [ ] **Step 5: Commit**

```bash
git add platform-mcp/src/lib/cost_caps.ts platform-mcp/src/lib/__tests__/cost_caps.test.ts
git commit -m "feat(w6): dual cost-cap tracker (call-count + wall-clock, fail-honest)"
```

---

### Task 2b: Per-entitlement cost-cap resolution

The ratified doctrine requires both caps to be configurable *per entitlement*, not a single global default. This task adds the resolution layer; Task 7 wires it into the tool.

**Files:**
- Modify: `platform-mcp/src/lib/cost_caps.ts` (add `resolveCostCapsForEntitlement`)
- Test: `platform-mcp/src/lib/__tests__/cost_caps.test.ts` (extend)
- Read: `platform-mcp/src/lib/authz.ts`, `platform-mcp/src/types.ts` (existing entitlement/role vocabulary — reuse the same tier names, don't invent new ones)

- [ ] **Step 1:** Grep `platform-mcp/src/lib/authz.ts` and `platform-mcp/src/types.ts` for the existing entitlement tier enum/type (e.g. `'consult' | 'full' | ...`) — use those exact tier names as the config keys, confirmed not guessed.
- [ ] **Step 2: Write the failing test**

```typescript
import { describe, it, expect } from 'vitest';
import { resolveCostCapsForEntitlement, DEFAULT_COST_CAPS } from '../cost_caps';

describe('resolveCostCapsForEntitlement', () => {
  it('returns the default caps for the base full-loop entitlement tier', () => {
    // substitute the real tier name found in Step 1 for 'full'
    expect(resolveCostCapsForEntitlement('full')).toEqual(DEFAULT_COST_CAPS);
  });

  it('returns a distinct cap set for a higher entitlement tier', () => {
    const caps = resolveCostCapsForEntitlement('elevated'); // real tier name from Step 1
    expect(caps).not.toEqual(DEFAULT_COST_CAPS);
  });
});
```

- [ ] **Step 3: Write minimal implementation** — a lookup table keyed by the real entitlement tier names from Step 1, falling back to `DEFAULT_COST_CAPS` for any tier without an explicit override:

```typescript
export function resolveCostCapsForEntitlement(entitlement: string): CostCapConfig {
  const overrides: Record<string, CostCapConfig> = {
    // populate with real tier names + values agreed at Step 1 — do not ship placeholder keys
  };
  return overrides[entitlement] ?? DEFAULT_COST_CAPS;
}
```

- [ ] **Step 4: Run test to verify it passes, then commit**

```bash
git add platform-mcp/src/lib/cost_caps.ts platform-mcp/src/lib/__tests__/cost_caps.test.ts
git commit -m "feat(w6): resolve cost caps per entitlement tier (ratified doctrine)"
```

---

### Task 3: Confirm cost-cap defaults against W4's measured timings

**Files:**
- Read: `platform/src/lib/pipeline/__tests__/prashna_ask_spike.test.ts`
- Modify (maybe): `platform-mcp/src/lib/cost_caps.ts` (`DEFAULT_COST_CAPS`)

- [ ] **Step 1:** Grep the spike test file and any STATE.md W4 entries for recorded timings/call counts (`grep -n "51s\|38.7s\|elapsed\|call count\|≤10" platform/src/lib/pipeline/__tests__/prashna_ask_spike.test.ts 00_ARCHITECTURE/briefs/retrieval_impl/STATE.md`).
- [ ] **Step 2:** If measured worst-case synthesis exceeds 80% of the 120s default, raise `maxWallClockMs` accordingly (document why in a code comment citing the measured number — not a magic bump).
- [ ] **Step 3:** Commit only if defaults changed: `git commit -m "fix(w6): calibrate cost-cap defaults against W4 measured timings"`.

---

### Task 4: prashna_ask ↔ engine bridge — resolve the process-boundary question

**Files:**
- Create: `platform-mcp/src/lib/prashna_ask_bridge.ts`
- Test: `platform-mcp/src/lib/__tests__/prashna_ask_bridge.test.ts`

- [ ] **Step 1:** Before writing any code, determine whether `platform-mcp` (the MCP server process) and `platform` (the Next.js web app, which owns `pipeline_planner.ts`) are the same deployable or two separate services. Check: `platform-mcp/package.json` dependencies (does it depend on `platform` as a workspace package, or call it over HTTP?), and `platform-mcp/src/tools/intent_scope_classifier.ts` for the pattern it already uses to reach vidhi logic (grep `import.*from.*platform/src` vs `fetch(`).
- [ ] **Step 2:** Follow whichever pattern `intent_scope_classifier.ts` already established — do not introduce a second integration style. If it's a direct workspace import, `prashna_ask_bridge.ts` does the same for `callPipelinePlanner`/`compileFloorForPlan`. If it's HTTP, model the bridge on the existing HTTP client used there (same base URL config, same auth header pattern).
- [ ] **Step 3: Write the failing test** (shape depends on Step 1's finding — sketch below assumes direct import; adjust if HTTP):

```typescript
import { describe, it, expect, vi } from 'vitest';
import { runPrashnaAskEngine } from '../prashna_ask_bridge';

vi.mock('platform/src/lib/pipeline/pipeline_planner', () => ({
  callPipelinePlanner: vi.fn().mockResolvedValue({ kind: 'plan_receipt', plan: {} }),
}));

describe('prashna_ask_bridge', () => {
  it('calls the frozen engine entry point and returns its outcome unmodified', async () => {
    const result = await runPrashnaAskEngine({ chartId: 'chart-1', question: 'test?' });
    expect(result.kind).toBe('plan_receipt');
  });
});
```

- [ ] **Step 4: Run test to verify it fails, then write minimal implementation calling the real engine function, then re-run to verify it passes.**
- [ ] **Step 5: Commit**

```bash
git add platform-mcp/src/lib/prashna_ask_bridge.ts platform-mcp/src/lib/__tests__/prashna_ask_bridge.test.ts
git commit -m "feat(w6): prashna_ask bridge into the frozen W4 engine (no engine changes)"
```

**STOP condition:** if Step 1/2 reveals the engine cannot be reached from `platform-mcp` without a change to `pipeline_planner.ts` or `compiled_floor_adapter.ts` itself, halt this task and report to the user rather than modifying the frozen engine.

---

### Task 5: NO-LEAKAGE arm-2 filter

**Files:**
- Create: `platform-mcp/src/lib/no_leakage_filter.ts`
- Test: `platform-mcp/src/lib/__tests__/no_leakage_filter.test.ts`
- Read: `platform/src/lib/retrieval/registry/types.ts` (`calibration_context_only` field, ~line 356)

- [ ] **Step 1: Write the failing test**

```typescript
import { describe, it, expect } from 'vitest';
import { filterLeakedCapabilities } from '../no_leakage_filter';
import type { CapabilityDescriptor } from 'platform/src/lib/retrieval/registry/types';

describe('filterLeakedCapabilities', () => {
  it('drops capabilities flagged calibration_context_only', () => {
    const caps = [
      { id: 'a', calibration_context_only: true } as CapabilityDescriptor,
      { id: 'b', calibration_context_only: false } as CapabilityDescriptor,
      { id: 'c' } as CapabilityDescriptor,
    ];
    const result = filterLeakedCapabilities(caps);
    expect(result.map((c) => c.id)).toEqual(['b', 'c']);
  });

  it('is a pure function — does not mutate input', () => {
    const caps = [{ id: 'a', calibration_context_only: true } as CapabilityDescriptor];
    const copy = [...caps];
    filterLeakedCapabilities(caps);
    expect(caps).toEqual(copy);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**
- [ ] **Step 3: Write minimal implementation**

```typescript
import type { CapabilityDescriptor } from 'platform/src/lib/retrieval/registry/types';

export function filterLeakedCapabilities(
  capabilities: readonly CapabilityDescriptor[]
): CapabilityDescriptor[] {
  return capabilities.filter((c) => c.calibration_context_only !== true);
}
```

- [ ] **Step 4: Run test to verify it passes**
- [ ] **Step 5: Commit**

```bash
git add platform-mcp/src/lib/no_leakage_filter.ts platform-mcp/src/lib/__tests__/no_leakage_filter.test.ts
git commit -m "feat(w6): NO-LEAKAGE arm-2 capability filter (F-R7)"
```

---

### Task 6: NO-LEAKAGE CI canary

**Files:**
- Create: `platform-mcp/src/tools/__tests__/no_leakage_canary.test.ts`
- Modify: CI workflow file (find with `grep -rl "vitest run\|npm test" .github/workflows/*.yml`)

- [ ] **Step 1: Write the failing test** — this test asserts against the REAL registry, not a mock, so it catches a future regression where someone adds a leaked capability to prashna_ask's reachable set:

```typescript
import { describe, it, expect } from 'vitest';
import { getAllCapabilities } from 'platform/src/lib/retrieval/registry'; // confirm real export path
import { buildPrashnaAskToolSet } from '../register_prashna_ask';

describe('NO-LEAKAGE CI canary', () => {
  it('prashna_ask tool set contains zero calibration_context_only capabilities', () => {
    const all = getAllCapabilities();
    const toolSet = buildPrashnaAskToolSet(all);
    const leaked = toolSet.filter((c) => c.calibration_context_only === true);
    expect(leaked.map((c) => c.id)).toEqual([]);
  });
});
```

- [ ] **Step 2:** Confirm the real registry export path/name via `grep -n "export.*function.*[Cc]apabilit" platform/src/lib/retrieval/registry/*.ts` before finalizing the import — do not guess the symbol name.
- [ ] **Step 3: Run test to verify it fails (buildPrashnaAskToolSet doesn't exist yet — this will start passing naturally once Task 7 lands `register_prashna_ask.ts`; that's fine, this test's job is to exist and be wired into CI so it never regresses silently).**
- [ ] **Step 4:** Add this test file's path to the CI workflow's required test glob if it isn't already covered by a blanket `vitest run` — confirm with a dry run: `cd platform-mcp && npx vitest run src/tools/__tests__/no_leakage_canary.test.ts` (expected to fail until Task 7 lands; that's the correct TDD-red state to commit at this step, matching Task 7's dependency).
- [ ] **Step 5: Commit**

```bash
git add platform-mcp/src/tools/__tests__/no_leakage_canary.test.ts
git commit -m "test(w6): NO-LEAKAGE CI canary — fails build if a leaked capability becomes reachable"
```

---

### Task 7: register_prashna_ask — the actual MCP tool

**Files:**
- Create: `platform-mcp/src/tools/register_prashna_ask.ts`
- Modify: `platform-mcp/src/server.ts` (register the tool)
- Test: `platform-mcp/src/tools/__tests__/register_prashna_ask.test.ts`
- Read: `platform-mcp/src/tools/intent_scope_classifier.ts` (registration pattern), `platform-mcp/src/types.ts` (entitlement/role types), `platform-mcp/src/lib/authz.ts`

- [ ] **Step 1:** Read `intent_scope_classifier.ts` in full to copy its exact tool-registration shape (schema definition style, error handling, how it reads `ctx`/session).
- [ ] **Step 2: Write the failing test**

```typescript
import { describe, it, expect, vi } from 'vitest';
import { handlePrashnaAsk, PRASHNA_ASK_INPUT_SCHEMA } from '../register_prashna_ask';

describe('register_prashna_ask', () => {
  it('rejects a request carrying a depth param (C-1: no depth param)', async () => {
    const result = PRASHNA_ASK_INPUT_SCHEMA.safeParse({
      chart_id: 'chart-1',
      question: 'What about my career?',
      response_format: 'narrative',
      depth: 'deep',
    });
    expect(result.success).toBe(false);
  });

  it('accepts the C-1 signature without scope_tuple (optional)', () => {
    const result = PRASHNA_ASK_INPUT_SCHEMA.safeParse({
      chart_id: 'chart-1',
      question: 'What about my career?',
      response_format: 'narrative',
    });
    expect(result.success).toBe(true);
  });

  it('returns a job handle immediately rather than blocking for the full answer', async () => {
    const response = await handlePrashnaAsk(
      { chart_id: 'chart-1', question: 'test?', response_format: 'narrative' },
      { entitlement: 'full', progressToken: 'tok-1' }
    );
    expect(response.job_id).toBeDefined();
    expect(response.status).toBe('pending');
  });

  it('rejects a request whose entitlement forbids full-loop calls', async () => {
    await expect(
      handlePrashnaAsk(
        { chart_id: 'chart-1', question: 'test?', response_format: 'narrative' },
        { entitlement: 'consult', progressToken: 'tok-2' }
      )
    ).rejects.toThrow(/entitlement/i);
  });

  it('resolves cost caps from the entitlement tier, not a single global default', async () => {
    const spy = vi.fn();
    await handlePrashnaAsk(
      { chart_id: 'chart-1', question: 'test?', response_format: 'narrative' },
      { entitlement: 'elevated', progressToken: 'tok-3', __onCapsResolved: spy } // test hook — confirm real DI seam at Step 4, this is illustrative
    );
    expect(spy).toHaveBeenCalledWith(expect.not.objectContaining({ maxCalls: 10, maxWallClockMs: 120_000 }));
  });

  it('delivers the terminal result via a progress notification on the same connection, not by requiring a separate poll-by-job_id call', async () => {
    const sendNotification = vi.fn();
    await handlePrashnaAsk(
      { chart_id: 'chart-1', question: 'test?', response_format: 'narrative' },
      { entitlement: 'full', progressToken: 'tok-4', sendNotification }
    );
    // the final notification carries a terminal marker (e.g. progress === total, or a status field) and the full/partial result payload —
    // confirm the exact MCP notifications/progress shape via the SDK docs/types at Step 1, this asserts the intent, not the literal field names
    const calls = sendNotification.mock.calls.map((c) => c[0]);
    const terminal = calls.find((n) => n.result !== undefined || n.status === 'complete' || n.status === 'failed');
    expect(terminal).toBeDefined();
  });
});
```

- [ ] **Step 3: Run test to verify it fails**
- [ ] **Step 4: Write minimal implementation** — schema via whatever validation lib the codebase already uses (check `intent_scope_classifier.ts`/`register_vidhi_plan.ts` for zod vs manual); wire in `JobRegistry`, `CostCapTracker` via `resolveCostCapsForEntitlement(entitlement)` from Task 2b (NOT the raw `DEFAULT_COST_CAPS` — the whole point of Task 2b is that different entitlement tiers get different cap values), `filterLeakedCapabilities`, `prashna_ask_bridge`, and the existing `authz.ts` entitlement check. On job completion, run the loop under `CostCapTracker`; if a cap trips, build the response per the user's binding doctrine: partial grounded result + completeness receipt naming unserved floor items + `judgment_flags: ['cost_cap_call_count_exceeded' | 'cost_cap_wall_clock_exceeded']`. Emit `notifications/progress` (MCP spec) keyed by the caller-supplied `progressToken` at each floor-item completion, AND emit the terminal answer (or partial-result form) as the final `notifications/progress` push on that same connection — `job_id` exists for correlation/logging only; the caller must never be required to separately poll a status endpoint to obtain the finished answer. Confirm the MCP SDK's exact progress-notification payload shape (`platform-mcp` already depends on `@modelcontextprotocol/sdk` — check its type defs for `Notification`/`ProgressNotification`) before finalizing the terminal-delivery field names.
- [ ] **Step 5: Run test to verify it passes**
- [ ] **Step 6: Register in `platform-mcp/src/server.ts`** following the exact pattern used for the most recently added tool there.
- [ ] **Step 7: Re-run the Task 6 canary test — it should now pass** since `buildPrashnaAskToolSet` exists: `cd platform-mcp && npx vitest run src/tools/__tests__/no_leakage_canary.test.ts` → expect PASS.
- [ ] **Step 8: Commit**

```bash
git add platform-mcp/src/tools/register_prashna_ask.ts platform-mcp/src/server.ts platform-mcp/src/tools/__tests__/register_prashna_ask.test.ts
git commit -m "feat(w6): prashna_ask MCP tool — C-1 contract, job-handle transport, per-entitlement cost caps, NO-LEAKAGE (R-5)"
```

- [ ] **Step 9 (D-4b checkpoint):** `git branch -a | grep -i d-4b` + `gh pr list --state open | grep -i d4b` — log the result in a one-line note in this plan's execution log (or the STATE.md entry from Task 9). This is an observation only; do not act on it here — Task 14 is the only place a disposition decision gets made.

---

### Task 8: Retire the spike once the real path is proven

**Files:**
- Delete: `platform/src/lib/pipeline/prashna_ask_spike.ts`, `platform/src/lib/pipeline/__tests__/prashna_ask_spike.test.ts`
- Modify: any doc referencing the spike as current (`RETRIEVAL_STRATEGY_v1_0.md`, `PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md` — grep first, update in place, don't leave stale pointers)

- [ ] **Step 1:** Do NOT do this task until Task 9 (E2E live verification) has passed — the spike is your fallback reference until the real path is proven live.
- [ ] **Step 2:** Delete the two spike files.
- [ ] **Step 3:** Grep `grep -rln "prashna_ask_spike" --include="*.md" --include="*.ts" .` and update every hit to point at `register_prashna_ask.ts` instead.
- [ ] **Step 4:** Run the full test suite to confirm nothing else imported the spike: `cd platform && npm test` (or the project's actual test command — confirm from `package.json` scripts).
- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "chore(w6): retire prashna_ask_spike — superseded by the real MCP tool (Task 9 E2E passed)"
```

---

## Phase 2: E2E verification on chart 1c826d5a

### Task 9: Live E2E through the deployed MCP connector

- [ ] **Step 1:** Confirm the deployed connector's current SHA matches `impl/wave-6`'s target once merged, or find the staging/preview deploy mechanism this repo uses for pre-merge verification (check `.github/workflows` for a preview-deploy-on-PR job).
- [ ] **Step 2:** Using the `marsys-jis-direct` MCP connection already available in this session (or a fresh connection if the schema needs a reconnect — note W5's close report hit exactly this snag), call `prashna_ask` with `chart_id: 482012f1-710e-4a25-994a-93821f5871aa` (the canonical chart), a real question (e.g. "What does my current dasha period suggest about career timing?"), and confirm: job_id returned immediately, progress notifications arrive, final result contains a grounded answer + completeness receipt, and NO-LEAKAGE holds (spot-check the tool set used contains no `calibration_context_only` capability).
- [ ] **Step 3:** Deliberately trigger both cap paths once: a request engineered to need >10 tool calls (broad multi-domain question) and a request with an artificially lowered wall-clock cap (test-only override) — confirm both produce the honest partial-result + judgment_flag shape, not silent truncation.
- [ ] **Step 4:** Record results in `00_ARCHITECTURE/briefs/retrieval_impl/STATE.md` under a new `### W6 — prashna_ask E2E` section, following the existing STATE.md entry style (honest about what was live-verified vs mocked).
- [ ] **Step 5: Commit the STATE.md update.**

```bash
git add 00_ARCHITECTURE/briefs/retrieval_impl/STATE.md
git commit -m "docs(w6): record prashna_ask live E2E on 1c826d5a"
```

---

## Phase 3: Resilience/chaos pass + renames + diagram fix

Master brief §E's literal W6 sequence is "...full contract → resilience/chaos → quality-under-load battery at concurrency → session-semantics rename → diagram fix → docs seal." Chaos/resilience runs BEFORE the load test so any seam-hardening fixes it surfaces are in place before the load test measures the seam under real concurrency — doing it after would let load-test conclusions rest on an unhardened seam.

### Task 10: Resilience/chaos pass on the platform↔platform-mcp seam

**Files:**
- Create: `platform-mcp/src/__tests__/resilience_chaos.test.ts`

- [ ] **Step 1:** Identify the seam's failure modes worth injecting: MCP connection drop mid-job, Next.js API 5xx during a floor-compile call, DB pool exhaustion, sidecar timeout. Check if a chaos-injection utility already exists (`grep -rn "chaos\|fault.inject\|toxiproxy" platform platform-mcp` ) before building one.
- [ ] **Step 2:** For each failure mode, confirm `prashna_ask`'s job-handle path degrades honestly (job marked `failed` with a real error, not silently hung or silently returning a partial result mislabeled as complete).
- [ ] **Step 3:** Write these as integration tests under `platform-mcp/src/__tests__/resilience_chaos.test.ts` using mocked failure injection (fetch/DB client mocks throwing at controlled points), not live production fault injection.
- [ ] **Step 4:** If any failure mode reveals a real bug (e.g. a hung job, a mislabeled partial result), fix it now — the load test in Task 12/13 will otherwise be measuring an unhardened seam.
- [ ] **Step 5: Commit**

```bash
git add platform-mcp/src/__tests__/resilience_chaos.test.ts
git commit -m "test(w6): resilience/chaos pass on the platform↔platform-mcp seam"
```

### Task 11: Session-semantics rename (W-17) + PARIPRASHNA §6.1 diagram fix (W-19)

- [ ] **Step 1:** Find W-17's exact scope: `grep -n "W-17" 00_ARCHITECTURE/RETRIEVAL_PLAN_INDUSTRY_CONSULT_v1_0.md 00_ARCHITECTURE/RETRIEVAL_STRATEGY_v1_0.md` — confirm precisely what rename is authorized before touching anything (do not guess the old/new names).
- [ ] **Step 2:** Apply the rename surgically (search-and-replace with `grep -rl` first to see the full blast radius, then edit each hit — no bulk find/replace across the whole repo without reviewing each file).
- [ ] **Step 3:** Find PARIPRASHNA §6.1 in `PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md`, confirm the diagram defect against W-19's authorization note, fix it.
- [ ] **Step 4: Commit** (two commits, one per fix, since they're independent):

```bash
git commit -m "refactor(w6): session-semantics rename (W-17)"
git commit -m "docs(w6): fix PARIPRASHNA §6.1 diagram (W-19, authorized)"
```

- [ ] **Step 5 (D-4b checkpoint):** `git branch -a | grep -i d-4b` + `gh pr list --state open | grep -i d4b` — log the observation. No action here; Task 14 is where a disposition is decided.

---

## Phase 4: Load-generation tooling + §9.7 four-point test + concurrency battery (folded residual 1)

### Task 12: Build the load-generation harness

**Files:**
- Create: `platform/tests/load/harness.ts` (or match whatever existing `platform/tests/eval/w5_battery` structure looks like — read that directory first for conventions to mirror)
- Read: `platform/tests/eval/w5_battery/` (existing battery harness from W5, reuse its runner/reporting scaffolding rather than building parallel infra)

- [ ] **Step 1:** Read `platform/tests/eval/w5_battery/` fully to find the existing concurrency-run pattern (W-31 already built a concurrency battery for the synchronous compile path per STATE.md) — reuse its HTTP client, chart fixtures, and result-reporting format.
- [ ] **Step 2:** Design the harness around the master brief §9.7's four named pressure points — find and read §9.7 in the strategy doc (`grep -n "9.7" 00_ARCHITECTURE/RETRIEVAL_STRATEGY_v1_0.md`) to get the exact four points and their pass thresholds before writing code (do not assume — the plan author has not read the literal thresholds, only their category names: cache hit-rate under real traffic, concurrency capacity, QoS/backpressure under contention, SLO-per-query-class).
- [ ] **Step 3:** Write the harness as a standalone script (not a unit test — this drives real HTTP load against the deployed connector) with configurable concurrency, target RPS, and duration; it must report per-pressure-point pass/fail against the thresholds found in Step 2, not just raw numbers.
- [ ] **Step 4:** Dry-run the harness against a local/staging instance first at low concurrency (never point an untested load tool at production first).
- [ ] **Step 5: Commit**

```bash
git add platform/tests/load/
git commit -m "feat(w6): load-generation harness for master-brief §9.7 four-point test (folded residual 1)"
```

### Task 13: Run the real four-point load test against the deployed connector

- [ ] **Step 1:** Run the harness against the deployed connector for all four pressure points, at the W-31 concurrency levels already used for the synchronous battery (reuse those numbers, don't invent new ones).
- [ ] **Step 2:** If any pressure point fails its threshold, this is a genuine regression-gated finding, not a note — file it plainly, do not average it away or downplay it.
- [ ] **Step 3:** Re-run the W5 battery itself at concurrency (the "battery re-run at concurrency, W-31" instruction) to confirm no regression versus the W5-recorded baseline (`W5_BATTERY_BASELINE_v1_0.md`).
- [ ] **Step 4:** Write `00_ARCHITECTURE/briefs/retrieval_impl/W6_LOAD_TEST_REPORT_v1_0.md` with full frontmatter (version/status/changelog per B.8), recording pass/fail per pressure point, comparison to baseline, and any regressions found+fixed with PR references.
- [ ] **Step 5: Commit**

```bash
git add 00_ARCHITECTURE/briefs/retrieval_impl/W6_LOAD_TEST_REPORT_v1_0.md
git commit -m "docs(w6): §9.7 four-point load test results — V5 gate's remaining open item now closed"
```

- [ ] **Step 6 (D-4b checkpoint):** `git branch -a | grep -i d-4b` + `gh pr list --state open | grep -i d4b` — log the observation. No action here; Task 14 is where a disposition is decided.

---

## Phase 5: Breaking flip contingency + docs seal + §H final acceptance

### Task 14: Re-check D-4b liveness and land the breaking flip IF genuinely quiet

- [ ] **Step 1:** Immediately before this task (not from any earlier note in this plan or prior session), run live evidence checks: `git branch -a`, `gh pr list --state open`, and check the D-4b worktree(s) for uncommitted/in-flight work.
- [ ] **Step 2:** If D-4b shows any open PRs, active worktree churn, or recent commits in the last few hours — it is NOT quiet. Skip this task, leave `impl/w5-breaking` parked, and note in the seal report that the flip is deferred pending explicit native go-ahead (per the user's instruction: "the flip is the campaign's LAST act before §H — do not seal around it without my explicit say-so").
- [ ] **Step 3:** If genuinely quiet, land the flip per §I.6 discipline: acquire the deploy mutex, re-snapshot baseline probes, merge `impl/w5-breaking`, deploy, verify `list_changed` notification fires, confirm `query_spine_bundle` (the dormant W5 capability) becomes reachable.
- [ ] **Step 4:** Either way, commit a decision record:

```bash
git commit -m "docs(w6): D-4b liveness re-check + breaking-flip disposition (landed|deferred)"
```

### Task 15: Docs seal

- [ ] **Step 1:** Update `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` §2 — new campaign-close entry, version bump, full changelog per this file's own discipline (mirror the style of its existing entries).
- [ ] **Step 2:** Append `00_ARCHITECTURE/SESSION_LOG.md` entry per the session-close template.
- [ ] **Step 3:** Find the master brief's plan-status marker (`grep -n "status\|W6" 00_ARCHITECTURE/briefs/RETRIEVAL_IMPLEMENTATION_MASTER_BRIEF_v1_0.md | head`) and update ONLY the W6 row/section to reflect "implementation complete, pending V6 gate / native read of FINAL_REPORT.md" — do NOT write `CLOSED` or `COMPLETE` on the W6 row, the overall plan status, or the campaign status anywhere in this task. Per the user's explicit instruction, the campaign does not flip COMPLETE until they have read Task 16's `FINAL_REPORT.md` and responded — that flip (if any) happens in a follow-up action outside this plan, not here.
- [ ] **Step 4:** Find and mark the "stale coverage map" superseded (the W-15 doc half mentioned in the brief's W6 text — grep for it, don't guess the filename).
- [ ] **Step 5:** Regenerate `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` via whatever generator script produces it (`grep -rln "CAPABILITY_MANIFEST" --include="*.py" --include="*.ts" 00_ARCHITECTURE platform | grep -i gen`).
- [ ] **Step 6: Commit**

```bash
git add 00_ARCHITECTURE/CURRENT_STATE_v1_0.md 00_ARCHITECTURE/SESSION_LOG.md 00_ARCHITECTURE/briefs/RETRIEVAL_IMPLEMENTATION_MASTER_BRIEF_v1_0.md 00_ARCHITECTURE/CAPABILITY_MANIFEST.json
git commit -m "docs(w6): campaign docs seal — CURRENT_STATE, SESSION_LOG, plan status, manifest regen"
```

### Task 16: §H final acceptance — measure, record, gate

- [ ] **Step 1:** Read master brief §H in full (`sed -n '/^## §H/,/^## §I/p' 00_ARCHITECTURE/briefs/RETRIEVAL_IMPLEMENTATION_MASTER_BRIEF_v1_0.md`) to get the literal targets before claiming any are met.
- [ ] **Step 2:** Measure plan §6 + strategy §7 targets live; run the full probe suite versus the W0 baseline (`00_ARCHITECTURE/briefs/retrieval_impl/BASELINE_PROBES.md`); confirm 100% concept terminal-states via the census generator.
- [ ] **Step 3:** Confirm every branch/worktree this campaign created is cleaned up (`git worktree list`, `git branch -a | grep -E "impl/wave|ret/strategy"`) except any deliberately retained per native ruling (none expected — W1-W6 should all be merged-and-deleted by now).
- [ ] **Step 4:** Confirm `main` SHA == deployed production SHA (both web and MCP services).
- [ ] **Step 5:** Write `00_ARCHITECTURE/briefs/retrieval_impl/FINAL_REPORT.md` — full §H measurement writeup, residuals handoff table (PF-1, RC-2 deferral, OT-5 spike findings, signal_reader polish queue) with named owners, honest about anything not fully closed (e.g. the token-budget cost-cap dimension deferred per this session's own ratified decision).
- [ ] **Step 6:** **STOP at the V6 gate.** Do not flip the campaign to COMPLETE. Present `FINAL_REPORT.md` to the user and wait for their explicit read/approval — this is the one point in the whole plan where the user's own instruction requires a hard stop, not a commit-and-continue.

```bash
git add 00_ARCHITECTURE/briefs/retrieval_impl/FINAL_REPORT.md
git commit -m "docs(w6): FINAL_REPORT.md — §H measurement, V6 gate, awaiting native read"
```

---

## Notes for the executing agent

- Tasks 1, 2, 2b are sequential; Task 3 depends on Task 2/2b; Tasks 4-7 are sequential (shared bridge/registry files feeding `register_prashna_ask.ts`); Task 8 waits on Task 9. Task 9 (E2E) gates everything downstream. Once Task 9 passes: Task 10 (chaos) can run in parallel with Task 11 (renames/diagram fix) — different files, no shared state. Task 12 (load harness) depends on Task 10 having landed any seam fixes it found; Task 13 (four-point test) depends on Task 12. Task 14 onward is strictly sequential and must be last.
- Every phase boundary (end of Task 8, Task 9, Task 11, Task 13) includes a lightweight D-4b liveness checkpoint (observation only) so the mutex re-check in Task 14 isn't the first time liveness was considered — per the folded-residual instruction to monitor D-4b at every wave checkpoint.
- If any task's "Read first, don't guess" step (Tasks 4, 6, 12, 13, 11, 15, 16) reveals the plan's assumption was wrong, stop and correct the plan before proceeding — do not silently improvise past a wrong assumption in a task this size.
- Every commit message should cite its plan row per master brief §G (W6/C-1/F-R7/W-17/W-19/R-5 as applicable) — the commit messages above already do this; keep the convention for any additional commits.
