---
status: COMPLETE
session: AIOPS_CP_3
authored_at: 2026-05-13
---

# CP.3 Call-Site Inventory

## Direct STACK_ROUTING reads requiring migration

| File | Line(s) | Call type | Action |
|---|---|---|---|
| `platform/src/app/api/chat/consume/route.ts` | 144 | synthesis.primary | migrate to getEffectiveModel |
| `platform/src/app/api/chat/consume/route.ts` | 242 | planner_fast.primary | migrate to getEffectiveModel |
| `platform/src/app/api/chat/consume/route.ts` | 243 | planner_fast.fallback | migrate to getEffectiveModel |
| `platform/src/lib/checkpoints/checkpoint_4_5.ts` | 35 | checkpoint_4_5 (hardcoded) | migrate to getEffectiveModel |
| `platform/src/lib/checkpoints/checkpoint_5_5.ts` | 35 | checkpoint_5_5 (hardcoded) | migrate to getEffectiveModel |
| `platform/src/lib/checkpoints/checkpoint_8_5.ts` | 41 | checkpoint_8_5 (hardcoded) | migrate to getEffectiveModel |

## STACK_ROUTING reads NOT requiring migration

| File | Reason |
|---|---|
| `platform/src/hooks/useChatPreferences.ts` | Client-side validation of stack names only; getEffectiveModel is server-only |
| `platform/src/app/api/admin/aiops/state/route.ts` | Display-only fallback for admin UI state |
| `platform/src/app/api/admin/aiops/routing/[stack]/[call_type]/route.ts` | Before-state capture for audit; not routing an LLM call |
| `platform/src/lib/aiops/probe/runner.ts` | Already uses getEffectiveModel; STACK_ROUTING is the catch() fallback |
| `platform/src/app/(super-admin)/aiops/control/page.tsx` | Admin UI display; not an LLM call site |
| `platform/src/lib/models/registry.ts` | Source of truth; migration target, not a call site |
| `platform/src/lib/models/runtime_config.ts` | The resolver itself; not a call site |

## Eval / smoke / checkpoint scripts

| File | Status |
|---|---|
| `scripts/eval/` | Python-only; no TypeScript migration needed |
| `scripts/answer_eval.ts` | Calls /api/chat/consume (stack passed via env); no direct model selection |
| `scripts/observatory/smoke_test.ts` | Uses hardcoded model as observability fixture (not routing); out of scope |
| `scripts/checkpoint/` | Does not exist |

## Synthesis / panel

| File | Status |
|---|---|
| `platform/src/lib/synthesis/single_model_strategy.ts` | Receives selected_model_id as param; no STACK_ROUTING read |
| `platform/src/lib/synthesis/panel/adjudicator.ts` | Receives adjConfig.model_id as param; no STACK_ROUTING read |
