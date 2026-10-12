NOTE: 362f9f17-… is a dead phantom; canonical is 482012f1-710e-4a25-994a-93821f5871aa
---
artifact_id: STAGE1_DIAGNOSIS
version: 1.0
status: COMPLETE
produced_by: EXEC_BRIEF_PHASE_11A_INVESTIGATION_v1_0
produced_at: 2026-04-28
executor: Claude Code (Sonnet 4.6)
---

# Stage 1 Diagnosis — Why Is Legacy UI Rendering at `/clients/[id]/consume`?

## 1. Summary

Five investigation streams were run against the codebase in read-only mode. The source code prop chain is **fully and correctly wired**: both consume pages fetch `NEW_QUERY_PIPELINE_ENABLED` via `configService` and pass `pipelineEnabled={true}` to `<ConsumeChat />`. No environment file overrides the flags. The most probable cause of the legacy-UI symptom is **stale in-process module state (Cause #2 variant)**: the dev server's `configService` singleton was instantiated before Phase 11A changed `feature_flags.ts` on Apr 28, so its in-memory flag value is still `false`. A secondary, likely contributing factor is **welcome-state misidentification (Cause #6)**: an empty conversation always renders `<WelcomeGreeting />` regardless of `pipelineEnabled`, which is visually indistinguishable from legacy rendering until a message is sent. Fix: restart the dev server (and optionally nuke `.next/` first). A separate follow-up brief scopes the restart and verification steps.

---

## 2. Environment Audit (Stream A)

### Flags read by code

File: `platform/src/lib/config/feature_flags.ts`

| Flag | Default (line) | Runtime env var key |
|---|---|---|
| `NEW_QUERY_PIPELINE_ENABLED` | `true` (line 37) | `MARSYS_FLAG_NEW_QUERY_PIPELINE_ENABLED` |
| `AUDIT_ENABLED` | `true` (line 41) | `MARSYS_FLAG_AUDIT_ENABLED` |

Env prefix declaration: line 65 — `export const FLAG_ENV_PREFIX = 'MARSYS_FLAG_'`

`configService` reads env vars at singleton construction time (`loadEnvOverrides`, `platform/src/lib/config/index.ts` lines 19–27). Only vars matching `MARSYS_FLAG_<FLAG>` participate. Any other prefix is ignored.

### Active env files surveyed

| File | Flag-related lines | Effect |
|---|---|---|
| `platform/.env.local` | **zero matches** | No override |
| `platform/.env.example` | Lines 41–47: `# MARSYS_FLAG_NEW_QUERY_PIPELINE_ENABLED=false` — **commented out** | No effect (example file) |
| `platform/.env.local.example` | zero matches | No effect |
| `.env.rag` (repo root) | zero matches | No effect |

### Runtime resolution

`process.env['MARSYS_FLAG_NEW_QUERY_PIPELINE_ENABLED']` is **undefined** at runtime — no file sets it. `configService.loadEnvOverrides()` skips the flag (undefined → no override). `configService.getFlag('NEW_QUERY_PIPELINE_ENABLED')` therefore returns the code default: `true`.

**Cause #1 (env override winning) is ruled out.** No active env file sets either flag to `false`.

### Build timestamp anomaly (smoking gun for Cause #2)

| Artifact | Last modified |
|---|---|
| `platform/.next/BUILD_ID` | Apr 26 21:52 (2 days before Phase 11A) |
| `platform/src/lib/config/feature_flags.ts` | Apr 28 11:32 (Phase 11A flag flip — today) |
| `platform/src/lib/config/index.ts` | Apr 27 19:42 |

The `.next/` build predates the Phase 11A flag flip by ~38 hours. If the dev server process has been running since Apr 26 without a restart, the `configService` singleton was created when `DEFAULT_FLAGS.NEW_QUERY_PIPELINE_ENABLED` was still `false`. HMR propagates file changes to browser bundles reliably but is less reliable for server-side module singletons in Next.js App Router dev mode — the `const _instance = new ConfigServiceImpl()` at line 62 of `config/index.ts` may not have been re-evaluated after the Apr 28 file change.

---

## 3. Consume Page Surface Map (Stream B)

### Pages found

| Route URL | File path | Type | Line count |
|---|---|---|---|
| `/clients/{id}/consume` | `platform/src/app/clients/[id]/consume/page.tsx` | Server Component | 63 lines |
| `/clients/{id}/consume/{conversationId}` | `platform/src/app/clients/[id]/consume/[conversationId]/page.tsx` | Server Component | 78 lines |

**No root `/consume/page.tsx` exists.** The directory `platform/src/app/consume/` does not exist at all. The brief's mention of a root consume page was incorrect — the application's consume surface lives entirely under `clients/[id]/consume/`. Native is visiting the correct route.

### Layout

`platform/src/app/clients/[id]/layout.tsx` (28 lines): server component that performs auth + ownership checks, then renders `<div className="flex h-[100dvh] flex-col">{children}</div>`. No feature flag involvement. No effect on the pipeline prop.

### Route parameter note

The actual Next.js route segment is `[id]`, not `[clientId]`. The URL `/clients/362f9f17-95a5-490b-a5a7-027d3e0efda0/consume` maps correctly to `[id]="362f9f17-95a5-490b-a5a7-027d3e0efda0"`. No routing mismatch.

---

## 4. Render Tree Audit (Stream C)

### Per-page prop chain table

| Item | `/clients/[id]/consume/page.tsx` | `/clients/[id]/consume/[conversationId]/page.tsx` |
|---|---|---|
| Imports `configService`? | ✅ line 6 | ✅ line 10 |
| Fetches `NEW_QUERY_PIPELINE_ENABLED`? | ✅ line 42: `configService.getFlag(...)` | ✅ line 55: `configService.getFlag(...)` |
| Passes `pipelineEnabled` to `<ConsumeChat />`? | ✅ line 59 | ✅ line 74 |
| Prop name matches `ConsumeChat` interface? | ✅ `pipelineEnabled` | ✅ `pipelineEnabled` |
| Passes `audienceTier`? | ✅ line 60 | ✅ line 75 |

**Cause #3 (per-client page missed) is ruled out.** Both pages correctly fetch and pass the flag.

### ConsumeChat conditional render

File: `platform/src/components/consume/ConsumeChat.tsx`

- Prop declaration line 65: `pipelineEnabled?: boolean` (optional)
- **Default value line 78: `pipelineEnabled = false`** — if prop is `undefined` for any reason, legacy renders
- Render conditional lines 341–390:

```
messagesEmpty (line 341)
  → true: <WelcomeGreeting /> — NO DisclosureTierBadge, NO StreamingAnswer (pipeline-agnostic)
  → false, pipelineEnabled (line 347)
      → true: <DisclosureTierBadge tier={audienceTier} /> (line 350) + <StreamingAnswer /> (line 366) — NEW UI
      → false: <AdaptiveMessageList /> (line 377) — LEGACY UI
```

**Critical observation:** `<DisclosureTierBadge />` and `<StreamingAnswer />` only render when BOTH `!messagesEmpty` AND `pipelineEnabled === true`. A fresh/new conversation always shows `<WelcomeGreeting />` regardless of `pipelineEnabled` — this is visually identical to the legacy empty state.

### Leaf component chain (new pipeline path)

| Component | File | Imports |
|---|---|---|
| `StreamingAnswer` | `platform/src/components/consume/StreamingAnswer.tsx` | Imports `AnswerView` (line 7) |
| `AnswerView` | `platform/src/components/consume/AnswerView.tsx` | Imports `CitationChip` from `@/components/citations/CitationChip` (line 5) |
| `CitationChip` | `platform/src/components/citations/CitationChip.tsx` | ✅ exists |
| `DisclosureTierBadge` | `platform/src/components/disclosure/DisclosureTierBadge.tsx` | ✅ exists |

The full component tree exists and is correctly wired. **No missing component or import breaks the chain.**

**Cause #4 (ConsumeChat branch logic wrong) is ruled out.** The conditional is correctly structured and un-inverted.

---

## 5. API Route Audit (Stream D)

### Endpoint used by ConsumeChat

File: `platform/src/hooks/useChatSession.ts`

Line 35: `api: '/api/chat/consume'` — this is the new pipeline route, NOT the legacy `/api/consume`.

### Route handler

File: `platform/src/app/api/chat/consume/route.ts`

Line 125: `if (configService.getFlag('NEW_QUERY_PIPELINE_ENABLED')) {`

- **Truthy branch (lines 126–232):** new pipeline — `classify → compose → retrieve → synthesize → audit`. Returns `toUIMessageStreamResponse` with `messageMetadata.pipeline: 'v2'`.
- **Falsy branch (lines 235–336):** legacy — plain `streamText` with `consumeTools`. Returns `toUIMessageStreamResponse` without `pipeline: 'v2'`.

The API route correctly gates on the SAME `configService` singleton as the page. If the singleton has a stale `false` value (Cause #2), BOTH the UI (`pipelineEnabled=false` → `AdaptiveMessageList`) AND the API (falls through to legacy `streamText`) would serve legacy behavior — a consistent end-to-end legacy experience, which matches what native observes.

**Cause #5 (API route bypass) is ruled out** — `useChatSession` posts to the correct route.

---

## 6. Root Cause

### Primary cause: **Cause #2 variant — stale in-process singleton (high confidence)**

Evidence:
- `platform/.next/BUILD_ID` modified Apr 26 21:52 — two days before Phase 11A's flag flip
- `feature_flags.ts` modified Apr 28 11:32 (today) — this is where `NEW_QUERY_PIPELINE_ENABLED` changed from `false` → `true`
- `configService` is a module-level singleton created at `const _instance = new ConfigServiceImpl()` (line 62 of `config/index.ts`) — constructed ONCE at module load time
- If the Next.js dev server process has been running since Apr 26 without restart, the singleton was created before the flag flip and holds `false` in memory
- Next.js App Router dev mode HMR is reliable for client-side modules but less reliable for server-side module re-evaluation of singletons; the in-process Node.js module cache may not have re-created the singleton after the file change
- This explains the complete end-to-end legacy experience: page passes `pipelineEnabled=false` → `ConsumeChat` renders `AdaptiveMessageList`; API route skips the new pipeline and uses legacy `streamText`

### Secondary cause: **Cause #6 — welcome-state misidentification (medium confidence)**

Evidence:
- `ConsumeChat` lines 341–347: when `messagesEmpty === true`, `<WelcomeGreeting />` is unconditionally rendered for BOTH old and new pipeline modes
- `WelcomeGreeting` has no `<StreamingAnswer />`, `<CitationChip />`, or `<DisclosureTierBadge />` — identical in appearance to the legacy empty state
- If native has been looking at fresh conversations without sending a message, they would see the welcome state and believe the new UI has not appeared — even if `pipelineEnabled=true` were correctly resolved

### Ruled out

| Cause | Verdict | Evidence |
|---|---|---|
| #1 — env override | ❌ Ruled out | No active env file sets either flag |
| #3 — per-client page missed | ❌ Ruled out | `clients/[id]/consume/page.tsx` lines 42 + 59 correctly fetch and pass the flag |
| #4 — ConsumeChat branch logic | ❌ Ruled out | Conditional at lines 341–390 is correctly structured |
| #5 — API route bypass | ❌ Ruled out | `useChatSession` posts to `/api/chat/consume` |

---

## 7. Recommended Remediation

**No fix applied in this investigation.** The following is a proposed scope for a follow-up brief.

### Fix A — Restart dev server (definitive resolution for Cause #2)

Risk: **none** (zero code changes).
Effort: < 1 minute.

Steps (for native to execute or a follow-up brief to specify):
1. `CTRL+C` the running `next dev` process.
2. `rm -rf platform/.next` — optional but eliminates any compiled cache that might re-seed stale modules.
3. `npm run dev` (or `pnpm dev`) in the `platform/` directory.
4. Visit `/clients/362f9f17-95a5-490b-a5a7-027d3e0efda0/consume` and send a test message.
5. **Verification**: after receiving a response, the sticky header should show `<DisclosureTierBadge />` (a small tier pill), and the assistant response should render via `StreamingAnswer → AnswerView` (markdown with inline citation chips), NOT `AdaptiveMessageList`.

### Fix B — Disambiguate welcome state (optional UX improvement for Cause #6)

If Cause #2 alone explains the symptom and Fix A resolves it, Fix B is optional. If native wants a visual indicator that the new pipeline is active even before sending a message, a small follow-up could:
- Show `<DisclosureTierBadge />` inside `<WelcomeGreeting />` when `pipelineEnabled=true` (single prop thread-through)
- Or add a subtle banner/chip in the empty state

Scope: `ConsumeChat.tsx` (pass `pipelineEnabled` and `audienceTier` to `WelcomeGreeting`) + `WelcomeGreeting.tsx` (accept and render the badge). Estimated effort: ~30 min. Risk: LOW.

### Suggested follow-up brief structure

```
brief_id: EXEC_BRIEF_PHASE_11A_FIX_v1_0
phase: 11A.fix
scope:
  may_touch:
    - [none, if Fix A is confirmed by native restart]
  must_not_touch:
    - everything else
acceptance_criteria:
  1. Dev server restarted; BUILD_ID timestamp > Apr 28
  2. Send message to /clients/{id}/consume; <DisclosureTierBadge /> visible in sticky header
  3. <StreamingAnswer /> present in DOM (not <AdaptiveMessageList />)
  4. /api/chat/consume response includes metadata.pipeline === 'v2'
```

**2026-04-28 — Restart performed (EXEC_BRIEF_PHASE_11A_RESTART_v1_0):** Stale PIDs 47527 + 85132 killed; `platform/.next` cache cleared; fresh server started (PID 50556) on port 3000; Stream D: HTTP 307 on /consume (expected auth redirect), `NEW_QUERY_PIPELINE_ENABLED: true` confirmed in source + singleton, 9/9 config unit tests pass. New singleton is live; native verification pending.
