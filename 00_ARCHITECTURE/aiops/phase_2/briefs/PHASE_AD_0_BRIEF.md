---
status: OPEN
session_id: AIOPS_AD_0
phase: AD.0
phase_name: "Adapter Layer foundation — branch, skeleton, types"
next_session: AIOPS_AD_1
authored_at: 2026-05-14
authored_by: AIOPS_PHASE_2_MASTER_PLAN_v1_0
---

# CLAUDECODE_BRIEF — AIOPS_AD_0
## AIOps Phase 2, Step 0 — Branch + skeleton + types

---

## §0 — Executor orientation

CP.0 of Phase 2. Establishes the branch, the new module
`platform/src/lib/adapters/`, the type-only skeleton, and the feature flag.
No live code yet — that lands in AD.1+.

Master plan: `00_ARCHITECTURE/aiops/phase_2/AIOPS_PHASE_2_MASTER_PLAN_v1_0.md`
Execution rules: `00_ARCHITECTURE/aiops/AIOPS_EXECUTION_RULES_v1_0.md`
(reused from Phase 1).

**Execution vehicle:** new worktree `../madhav-phase-2-tmp` on branch
`feature/aiops-phase-2-adapters` cut from `main`.

---

## §1 — Mandatory reads

```
1. CLAUDE.md
2. 00_ARCHITECTURE/aiops/phase_2/AIOPS_PHASE_2_MASTER_PLAN_v1_0.md (full)
3. 00_ARCHITECTURE/aiops/AIOPS_EXECUTION_RULES_v1_0.md (full)
4. platform/src/lib/models/registry.ts        (ModelMeta + ReasoningMode shape)
5. platform/src/lib/models/resolver.ts        (existing provider-options pattern)
6. platform/src/lib/synthesis/think_block_filter.ts (existing DeepSeek <think> parsing — soon to be replaced)
7. platform/src/lib/llm/providers/{anthropic,deepseek,gemini,openai,nvidia}_observed.ts (observed wrappers — DO NOT MODIFY)
8. platform/src/lib/config/feature_flags.ts   (where ADAPTERS_ENABLED lands)
```

---

## §2 — Scope

### may_touch
```
platform/src/lib/adapters/**                  # create directory + skeleton
platform/src/lib/config/feature_flags.ts      # add ADAPTERS_ENABLED
00_ARCHITECTURE/aiops/phase_2/**              # any docs needed
CLAUDECODE_BRIEF.md                           # rotate at close
```

### must_not_touch
```
01_FACTS_LAYER/**
025_HOLISTIC_SYNTHESIS/**
06_LEARNING_LAYER/**
platform/src/components/consume/**            # Phase 3 territory
platform/src/lib/components/observatory/**
platform/src/app/api/admin/observatory/**
platform/src/lib/models/registry.ts           # AD.1 territory
platform/src/lib/models/resolver.ts           # AD.4 territory
platform/src/lib/synthesis/**                 # AD.4 territory
platform/src/app/api/chat/consume/**          # AD.4 territory
00_ARCHITECTURE/aiops/AIOPS_MASTER_PLAN_v1_0.md
00_ARCHITECTURE/aiops/phase_briefs/**
```

---

## §3 — Work plan

### 3.1 — Branch + worktree

From whichever directory you're in (the trigger prompt should place this
session in a transient worktree, e.g. `../madhav-phase-2-tmp` on
`feature/aiops-phase-2-adapters`). Confirm:

```bash
cd /Users/Dev/Vibe-Coding/Apps/madhav-phase-2-tmp
git branch --show-current     # expect: feature/aiops-phase-2-adapters
git rev-parse --short HEAD    # expect: at or after the Phase 1 closeout commit 23bed0a
```

If you're somehow not in a worktree on the right branch, BAIL OUT — the
native should create the worktree before triggering this session.

### 3.2 — Feature flag

Edit `platform/src/lib/config/feature_flags.ts`:

Add to the `FeatureFlag` union, after the LL3 flags:

```ts
  // AIOps Phase 2 — Adapter Layer. Default OFF through AD.4; flip in AD.5
  // after stack-smoke parity confirms behavior is unchanged. Env: ADAPTERS_ENABLED.
  | 'ADAPTERS_ENABLED'
```

Add to `DEFAULT_FLAGS`:

```ts
  // AIOps Phase 2 — default OFF through AD.4; flip in AD.5.
  ADAPTERS_ENABLED: false,
```

### 3.3 — Module skeleton

Create directory tree:

```
platform/src/lib/adapters/
├── index.ts            # public exports: runAdapter, streamAdapter, types
├── types.ts            # QueryRequest, ModelInteraction, ModelInteractionEvent, IntermediateEvent
├── dispatcher.ts       # adapterFor(provider): Adapter — picks the right impl
├── providers/
│   ├── adapter_anthropic.ts   # SKELETON in AD.0 (throws "not yet implemented")
│   ├── adapter_deepseek.ts    # SKELETON
│   ├── adapter_gemini.ts      # SKELETON
│   ├── adapter_openai.ts      # SKELETON
│   ├── adapter_nim.ts         # SKELETON
│   └── base.ts                # interface Adapter { stream(req, meta): ReadableStream<ModelInteractionEvent> }
└── __tests__/
    └── types.test.ts          # type-level sanity tests
```

### 3.4 — Types

Author `platform/src/lib/adapters/types.ts` verbatim from the master plan
§4. Export everything.

### 3.5 — Adapter interface

Author `platform/src/lib/adapters/providers/base.ts`:

```ts
import type { ModelMeta } from '@/lib/models/registry'
import type { QueryRequest, ModelInteractionEvent } from '../types'

export interface Adapter {
  readonly providerId: string
  stream(req: QueryRequest, meta: ModelMeta): ReadableStream<ModelInteractionEvent>
}
```

### 3.6 — Skeleton providers (5 files)

Each provider file at this stage is a stub. Example
`adapter_anthropic.ts`:

```ts
import type { ModelMeta } from '@/lib/models/registry'
import type { QueryRequest, ModelInteractionEvent } from '../types'
import type { Adapter } from './base'

export const adapterAnthropic: Adapter = {
  providerId: 'anthropic',
  stream(_req: QueryRequest, _meta: ModelMeta): ReadableStream<ModelInteractionEvent> {
    throw new Error('adapter_anthropic.stream: not yet implemented — AD.3 work')
  },
}
```

Repeat for deepseek, gemini, openai, nim.

### 3.7 — Dispatcher

`platform/src/lib/adapters/dispatcher.ts`:

```ts
import type { Provider } from '@/lib/models/registry'
import type { Adapter } from './providers/base'
import { adapterAnthropic } from './providers/adapter_anthropic'
import { adapterDeepseek } from './providers/adapter_deepseek'
import { adapterGemini } from './providers/adapter_gemini'
import { adapterOpenai } from './providers/adapter_openai'
import { adapterNim } from './providers/adapter_nim'

export function adapterFor(provider: Provider): Adapter {
  switch (provider) {
    case 'anthropic': return adapterAnthropic
    case 'deepseek':  return adapterDeepseek
    case 'google':    return adapterGemini
    case 'openai':    return adapterOpenai
    case 'nvidia':    return adapterNim
    default: {
      const _exhaustive: never = provider
      throw new Error(`Unknown provider: ${String(_exhaustive)}`)
    }
  }
}
```

### 3.8 — Public index

`platform/src/lib/adapters/index.ts`:

```ts
export type {
  QueryRequest,
  ModelInteraction,
  ModelInteractionEvent,
  IntermediateEvent,
  ToolDefinition,
} from './types'

export { adapterFor } from './dispatcher'

// runAdapter and streamAdapter are exported in AD.2 once the dispatcher is wired.
```

### 3.9 — Type-level sanity test

`platform/src/lib/adapters/__tests__/types.test.ts`:

A simple compile-time-only test that the type shapes are correct. Uses
`expectTypeOf` from vitest. ≥10 type assertions covering the main shape
properties + the event union exhaustiveness.

### 3.10 — Smoke

```bash
cd /Users/Dev/Vibe-Coding/Apps/madhav-phase-2-tmp
npm --prefix platform run typecheck 2>&1 | tail -5
npm --prefix platform run lint 2>&1 | tail -5
npm --prefix platform run test -- --run platform/src/lib/adapters/ 2>&1 | tail -10
```

All three must pass.

---

## §4 — Acceptance criteria

| AC | Check | Pass |
|---|---|---|
| AC.AD0.1 | Branch is `feature/aiops-phase-2-adapters` | `git branch --show-current` matches |
| AC.AD0.2 | Feature flag declared | `grep "ADAPTERS_ENABLED" platform/src/lib/config/feature_flags.ts` ≥ 2 matches (union + DEFAULT_FLAGS) |
| AC.AD0.3 | Module directory exists | `test -d platform/src/lib/adapters` |
| AC.AD0.4 | types.ts exports the 5 shapes | grep each of `QueryRequest`, `ModelInteraction`, `ModelInteractionEvent`, `IntermediateEvent`, `ToolDefinition` |
| AC.AD0.5 | Dispatcher exists with exhaustive switch | grep `adapterFor` + check 5 case branches |
| AC.AD0.6 | All 5 provider stubs exist | `ls platform/src/lib/adapters/providers/adapter_*.ts \| wc -l` = 5 |
| AC.AD0.7 | Type tests pass | `npm run test -- --run platform/src/lib/adapters/` exit 0 |
| AC.AD0.8 | typecheck + lint clean | exit 0 each |
| AC.AD0.9 | Scope-violation grep | SCOPE_OK |

---

## §5 — Test minimums

- Type tests: ≥10 assertions covering union exhaustiveness, required fields, optional fields, generic shape.
- No runtime tests yet — those land in AD.2 onward.

---

## §6 — Session close

Standard per R4 + R5:

1. Commit message:
   ```
   feat(aiops-AD.0): adapter layer foundation — module skeleton + types

   - new module platform/src/lib/adapters/ with types.ts, dispatcher.ts, 5 provider stubs
   - all 5 stubs throw "not yet implemented" — real implementations land in AD.3
   - feature flag ADAPTERS_ENABLED added (default false)
   - 10+ type-level sanity tests pass
   - typecheck + lint clean

   AC summary: 9/9 PASS
   ```

2. Rotate `CLAUDECODE_BRIEF.md` to PHASE_AD_1_BRIEF.md contents.

3. Report `[AIOPS-CLOSE] phase=AD.0 status=CLOSED next_phase=AD.1`.

---

## §7 — BAIL OUT triggers (AD.0 specific)

- Branch `feature/aiops-phase-2-adapters` doesn't exist (worktree wasn't set up).
- `platform/src/lib/adapters/` already exists with content (someone partially started this work).
- Feature flag `ADAPTERS_ENABLED` already declared (duplicate entry would break compile).

---

*End of PHASE_AD_0_BRIEF.md*
