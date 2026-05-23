---
artifact: R11F_LIVE_ARC_PLAN_v1_0.md
canonical_id: R11F_LIVE_ARC_PLAN
version: 1.0
status: CURRENT
authored: 2026-05-23
branch: feature/r11f-wiring-arc
purpose: >
  Live arc plan for R11.F — the dispatch wiring arc that closes the D.3 and E.1–E.4
  gaps left open after the R11.A–E substrate + dispatch-wiring sessions.
  7 sessions. Single branch. Single PR at the end.
---

# R11.F — Live Arc Plan (Dispatch Wiring)

## §1 — What this arc delivers

Two concrete gaps remain from the R11.A–E arc:

| Gap | Flag | Description |
|---|---|---|
| D.3 | `MARSYS_FLAG_R11D_GEMINI_CACHE` | Gemini cachedContent API — `adapter.cache()` → `genai.caches.create()` → cachedContent ID passed to streamText |
| E.1 | `MARSYS_FLAG_R11E_ANTHROPIC_LOOP` | Anthropic stop_reason=tool_use agentic loop wired into route.ts via `runAgenticLoop()` |
| E.2 | `MARSYS_FLAG_R11E_GEMINI_LOOP` | Gemini finish_reason=function_calls agentic loop |
| E.3 | `MARSYS_FLAG_R11E_DEEPSEEK_LOOP` | DeepSeek finish_reason=tool_calls loop |
| E.4 | `MARSYS_FLAG_R11E_NVIDIA_LOOP` | NVIDIA finish_reason=tool_calls loop |

After this arc: all 5 flags above become flippable. Operator runs the gcloud commands
from `ROLLOUT_PHASE_R11F_RESULT.md` to activate them one at a time with log verification.

## §2 — Session inventory

| Session | Title | Type | Branch target |
|---|---|---|---|
| F-S1 | Pre-flight + agentic_loop engine | serial | feature/r11f-wiring-arc |
| F-S2 | Per-provider chat() tool-event emission | 5-way parallel | feature/r11f-wiring-arc (isolation: worktree) |
| F-S3 | Route.ts E wiring (agentic loop) | serial | feature/r11f-wiring-arc |
| F-S4 | Route.ts D.3 wiring (Gemini cache) | serial | feature/r11f-wiring-arc |
| F-S5 | CI validation | serial | feature/r11f-wiring-arc |
| F-S6 | PR + merge + deploy | serial | main (via PR) |
| F-S7 | Governance close-out | serial | main |

## §3 — Key files

| File | Role |
|---|---|
| `platform/src/app/api/chat/consume/route.ts` | Dispatch block (lines 904–988) — needs E + D.3 wiring |
| `platform/src/lib/synthesis/agentic_loop.ts` | Engine — needs `runAgenticLoop()` added |
| `platform/src/lib/providers/*/adapter.ts` | Per-provider — needs tool-event emission in `chat()` |
| `platform/src/lib/providers/google/cached_content.ts` | Helpers — already has `buildCacheCreatePayload()` |
| `platform/src/lib/config/feature_flags.ts` | Flag declarations (already has R11E_* and R11D_GEMINI_CACHE) |
| `platform/deploy.yml` | Session 7: add `MARSYS_FLAG_R11D_GEMINI_CACHE=true` |

## §4 — Constraints

- All 7 sessions commit to `feature/r11f-wiring-arc`.
- F-S2 uses `isolation: worktree` per sub-agent to avoid git conflicts; coordinator merges all 5 after PASS.
- No production flag flips. Session 7 surfaces gcloud commands only.
- No new npm packages. Gemini cache creation uses raw fetch() with `GOOGLE_GENERATIVE_AI_API_KEY`.
- Brief: `R11V2_DISPATCH_WIRING_FULL_BRIEF_v1_0.md` — acceptance criteria live there.

## §5 — HALT conditions

Any sub-agent FAIL → Conductor writes `R11F_HALT_S<N>.md` and STOPS.
Do NOT fix-forward. Do NOT retry. Surface to operator for triage.

---
*R11F_LIVE_ARC_PLAN_v1_0.md — authored 2026-05-23*
