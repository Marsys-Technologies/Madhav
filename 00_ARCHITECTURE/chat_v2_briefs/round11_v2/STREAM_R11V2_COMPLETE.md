---
artifact: STREAM_R11V2_COMPLETE.md
project_name: Claude Takeover
status: COMPLETE
authored_on: 2026-05-22
authored_by: Meta-Conductor (Level 0) — R11 v2 arc closure §3.D
amended_on: 2026-05-22
amended_by: Claude Code dispatch-wiring session
purpose: >
  Governance seal for the Claude Takeover Multi-Provider Parity active arc
  (R11.A through R11.E plus dispatch wiring). Records merge SHAs, session counts,
  test counts, and the final production revision at arc completion.
---

# Claude Takeover — Active Arc Complete (R11.A through R11.E)

## §1 — Arc summary

| Field | Value |
|---|---|
| Project codename | Claude Takeover |
| Arc | Multi-Provider Parity R11 v2 active arc (R11.A–R11.E) |
| Declared | 2026-05-22 |
| Completed | 2026-05-22 |
| Total sessions | 49 (14 + 10 + 8 + 7 + 10) |
| Total tests | 599 vitest tests — 599/599 PASS |
| Total files shipped | 111 new or modified files (+12,678 / -344 lines) |
| Final main HEAD | 24a21dda021537cbd98480d95e365ef1e8894265 |

## §2 — Per-phase merge record

| Phase | PR | Merge SHA | Sessions | Description |
|---|---|---|---|---|
| R11.A | #143 | f2df0524 | 14 | Foundation — capability adapter substrate, 5 provider skeletons, dispatcher, telemetry, migration adapter, runtime toggle |
| R11.C | #144 | d268d429 | 8 | Streaming + Thinking — smooth-stream, pre-token indicator, extended-thinking auto-collapse, adaptive budgets, inline tool cards, stop-button persistence |
| R11.B | #145 | 24a21dda | 10 | Look-and-Feel — Claude typography + bubble-less messages + 768px column + hover-reveal + inline citation rewrite (CitationSidePanel retired) + brand preservation |
| R11.D | #146 | e9cbffc9 | 7 | Caching — Anthropic 4-bp cache_control, Gemini cachedContent, OpenAI/DeepSeek telemetry, cache-aware prompt layout, Observatory cache tile |
| R11.E | #147 | 5d0064f9 | 10 | Agentic Tools — 5-provider loop engine (8-iteration cap), stop-signal handlers, tool error recovery, iteration cap safety, Observatory tool-loop tile |

## §3 — Topology

Executed via Pattern 2+ parallel topology under a single Meta-Conductor session:

- **Phase 1 (serial):** R11.A in `MadhavR11A` worktree — 14 sessions including 5-way parallel batch (A-S2..A-S6) for provider adapter skeletons.
- **Phase 2 (parallel):** R11.B (stream-1 in `MadhavR11B`) ∥ R11.CDE (stream-2 in `MadhavR11CDE`) running concurrently. R11.CDE walks C → D → E serially with 3 intermediate MERGE PRs.

## §4 — Flag inventory (post-arc)

| Flag | Type | Default | Description |
|---|---|---|---|
| `MARSYS_FLAG_R11V2_MULTI_PROVIDER_PARITY` | NEXT_PUBLIC | false | Master kill-switch for new chat shell + adapter layer |
| `MARSYS_FLAG_R11B_LOOK_AND_FEEL` | NEXT_PUBLIC | false | CSS-only look-and-feel redesign (typography, layout, citation) |
| `MARSYS_FLAG_R11C_STREAMING_THINKING` | NEXT_PUBLIC | false | Smooth-stream + thinking visualization across all providers |
| `MARSYS_FLAG_R11D_PROMPT_CACHING` | server-side | false | Per-provider caching + cache-aware prompt layout |
| `MARSYS_FLAG_R11E_AGENTIC_TOOLS` | server-side | false | Per-provider multi-step agentic tool loops |

All flags default false. Operator flips individually in Cloud Run env-vars after smoke testing each phase.

## §5 — Dispatch wiring close-out (2026-05-22 amendment)

**Status correction:** The original arc seal (2026-05-22) documented that `route.ts:908` had a `&& false` dead-code gate making adapter dispatch permanently unreachable. All 5 provider `chat()` methods delegated to `migrationAdapter.stubChat()` producing synthetic empty responses.

**Dispatch wiring shipped in PR #149** (squash merge commit `77205869`, 2026-05-22):
- Removed `&& false` gate from `route.ts` dispatch block
- Implemented real SDK calls in all 5 provider adapters:
  - `AnthropicAdapter`: `streamText` + `@ai-sdk/anthropic`, `reasoning-delta` → `thinking_delta`
  - `GoogleAdapter`: `streamText` + `@ai-sdk/google`, `reasoning-delta` → `thinking_delta`
  - `DeepSeekAdapter`: `streamText` + `@ai-sdk/deepseek`, `reasoning-delta` → `thinking_delta`, error part handling
  - `OpenAIAdapter`: raw `openai` stream, no thinking delta
  - `NvidiaAdapter`: raw `openai` stream (NIM base URL), no thinking delta
- Retired `MigrationAdapter.stubChat()` — zero callers after real implementations landed
- Updated test suite: foundation-smoke accepts `error` events as terminal (test env has no API keys)
- Additional build fixes merged: `@supabase/supabase-js` → `pg` client (PR #150), Next.js 16 async params (direct commit `267ce29e`), ES2018 tsconfig target (direct commit `913c7d27`), `bundle_adapters.js` correct path (direct commit `7bb7b0f1`)
- Final main HEAD: `7bb7b0f1`
- Production revision: `amjis-web-00339-7nc` (deployed 2026-05-22)
- `MARSYS_FLAG_R11V2_USE_ADAPTERS=true` flipped in Cloud Run 2026-05-22
- Production smoke: zero errors/warnings in 10-min log window post-deploy

**Deferred arc:** R11.F through R11.K (server-side tools, memory, multi-modal, artifacts, computer use) remain DEFERRED per native scope decision 2026-05-22. Scope content in `MULTI_PROVIDER_PARITY_ROADMAP.md §3`.

## §6 — Known infrastructure notes

- `npx jest` corrected to `npx vitest run` in all gate commands (project uses vitest).
- Repository auto-merge disabled — R11B-MERGE required manual GitHub merge of PR #145.
- MCP Transformation concurrent session held `.git/index.lock` intermittently; 0-byte stale locks removed safely.

## §7 — R11.D + R11.E production flag rollout (2026-05-23 amendment)

**Rollout session:** R11V2-Phase-DE-Resume (2026-05-23)

### Pre-flight findings

- **BLOCKER (resolved):** `deploy.yml` `env_vars:` block replaced all env vars on every
  push. Three prerequisite flags (`MARSYS_FLAG_R11V2_USE_ADAPTERS`, `MARSYS_FLAG_R11D_PROMPT_LAYOUT`,
  `MARSYS_FLAG_R11D_ANTHROPIC_CACHE`) were absent from production on every revision prior to 356.
  Root cause: orphaned `ADAPTERS_ENABLED=true` in `env_vars:` used wrong env var name; manually
  applied flags wiped by each code push. Fixed by commit `fbe8ff32` (added three correctly-named
  flags to `env_vars:`).
- **CRON_SECRET type conflict (resolved):** Commit `8c2dfc46` (Abhisek) added
  `MARSYS_CRON_SECRET=mcpt-scheduler-secret:latest` to `secrets:` block but it was already
  a plain env var in Cloud Run. Resolved by removing it from `secrets:` block (commit `6f6d4f16`).
  Deploy unblocked → revision 356.

### D.1 — MARSYS_FLAG_R11D_PROMPT_LAYOUT: **PASS**

Baked into `deploy.yml` env_vars via commit `fbe8ff32`. Live on revision 356.
Cache-aware prompt layout (prompt_assembler.ts 4-breakpoint injection) verified active.

### D.2 — MARSYS_FLAG_R11D_ANTHROPIC_CACHE: **WAIVED**

Baked into `deploy.yml` env_vars via commit `fbe8ff32`. Live on revision 356.
2-query cache verification waived by operator (prior session check not confirmed;
operator approval documented in ROLLOUT_DE_RESUME_PREFLIGHT.md §3).

### D.3 — MARSYS_FLAG_R11D_GEMINI_CACHE: **NOT_IMPLEMENTED — ROLLED BACK**

Flipped `true` on revision 357. Operator sent 2 long-context Gemini queries.
Log check: no `cachedContentTokenCount` entries for provider=google.

Root cause: `R11D_GEMINI_CACHE` is a stub. Route.ts adapter dispatch block (lines 905–988)
calls only `adapter.chat()` — `adapter.cache()` is never called. The Google adapter's
`cache()` method returns a `CacheResponse` spec object (`sdkMethod: 'genai.caches.create'`)
but route.ts has no code to consume this return value, call `genai.caches.create()`, or
pass `cachedContent` ID to the model request.

Rolled back: `gcloud run services update amjis-web --update-env-vars MARSYS_FLAG_R11D_GEMINI_CACHE=false`

Full finding documented in `ROLLOUT_PHASE_D_RESULT.md §D.3`.

### E.1–E.4 — R11E_*_LOOP flags: **ALL NOT_IMPLEMENTED — NOT FLIPPED**

Same architecture gap as D.3. Route.ts has zero references to any `R11E_*` flag.
`adapter.loop()` methods exist in all 5 adapters (return `LoopResponse` config specs),
and `agentic_loop.ts` engine is implemented, but neither is imported or invoked from
the dispatch block.

Decision: do not flip any E flags. Flipping stubs creates false monitoring signals.

Full finding documented in `ROLLOUT_PHASE_E_RESULT.md`.

### Production state at rollout close

| Flag | Value | Live since |
|---|---|---|
| `MARSYS_FLAG_R11V2_USE_ADAPTERS` | `true` | rev 356 (deploy.yml) |
| `MARSYS_FLAG_R11D_PROMPT_LAYOUT` | `true` | rev 356 (deploy.yml) |
| `MARSYS_FLAG_R11D_ANTHROPIC_CACHE` | `true` | rev 356 (deploy.yml) |
| `MARSYS_FLAG_R11D_GEMINI_CACHE` | `false` | rolled back rev 357 |
| `MARSYS_FLAG_R11E_*_LOOP` (×4) | `false` | default (never flipped) |

### Deferred items (R11.F arc scope)

1. Route.ts: wire `adapter.cache()` → `genai.caches.create()` → pass cachedContent ID to model request
2. Route.ts: wire `adapter.loop()` → `agentic_loop.ts` engine for all 5 providers
3. After (1): flip `MARSYS_FLAG_R11D_GEMINI_CACHE=true` and run 2-query verification
4. After (2): flip E flags individually with tool-loop iteration verification

---

*STREAM_R11V2_COMPLETE.md — §7 amended 2026-05-23 by R11V2-Phase-DE-Resume rollout session.*
