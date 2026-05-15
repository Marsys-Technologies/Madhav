---
title: "CHAT_V2 α0 — assistant-ui Fit-Spike Report"
version: "1.0"
status: CURRENT
authored: "2026-05-16"
work_item: "α0"
verdict: GREEN
---

# CHAT_V2 α0 — assistant-ui Fit-Spike Report

## Executive Summary

**Verdict: GREEN**

`@assistant-ui/react` v0.14.5 is a viable foundation for the Chat V2 build. All five spike acceptance criteria pass. Four integration findings discovered during the spike are documented below; all are low-friction workarounds, none require a library change or scope revision.

---

## 1. Acceptance Criteria Results

| # | Criterion | Result | Notes |
|---|---|---|---|
| AC-α0.1 | `AssistantRuntimeProvider` + `useChatRuntime` mount against `/api/chat/spike` without error | **PASS** | Required `DefaultChatTransport` wrapper from `ai` SDK; direct `api` string not valid in v0.14.5 |
| AC-α0.2 | Streaming fixture response renders (text chunks visible before stream ends) | **PASS** | `ThreadPrimitive.Viewport` + `ThreadPrimitive.Messages` stream correctly |
| AC-α0.3 | Reasoning drawer mounts and toggles expand/collapse | **PASS** | `ReasoningMessagePart.text` (not `.reasoning`) — corrected |
| AC-α0.4 | TypeScript builds without errors (`npx tsc --noEmit` exits 0) | **PASS** | See findings F.1–F.3 for corrections made |
| AC-α0.5 | `/dev/chat-spike` page routes correctly under super-admin gate | **PASS** | See finding F.4 for path deviation from brief |

---

## 2. Spike Findings

### F.1 — `useChatRuntime` transport API (breaking from brief)

**Brief expected:** `useChatRuntime({ api: '/api/chat/spike' })`

**Actual required:**
```typescript
import { DefaultChatTransport } from 'ai'
useChatRuntime({ transport: new DefaultChatTransport({ api: '/api/chat/spike' }) })
```

**Root cause:** `@assistant-ui/react-ai-sdk@1.3.26` `UseChatRuntimeOptions` accepts `transport: ChatTransport`, not `api: string` directly. The `api` shorthand existed in older pre-release versions.

**Resolution:** Fixed in `page.tsx`. Carry `DefaultChatTransport` as the pattern for all Chat V2 transport bindings (α1+).

**Risk to α1:** None — standard pattern, well-typed.

---

### F.2 — `MessagePrimitive.Parts` component props (breaking from naive usage)

**Brief expected:** `Text: ({ part }) => <span>{part.text}</span>`

**Actual required:** `Text: (props) => <span>{props.text}</span>`

**Root cause:** Component receive signature is `MessagePartState & TextMessagePart` (merged/flattened). There is no `part` sub-object — `text` is a direct prop. Similarly `ReasoningMessagePart.text` (not `.reasoning`).

**Resolution:** Fixed in `ChatSpikeThread.tsx`. Carry flattened prop pattern for all part-component implementations.

**Risk to α1:** None — straightforward once known.

---

### F.3 — `ComposerPrimitive.If sending` deprecated and unsupported

**Brief expected:** `<ComposerPrimitive.If sending>` / `<ComposerPrimitive.If sending={false}>`

**Actual:** `ComposerPrimitive.If` in v0.14.5 only accepts `editing` and `dictation` props. `sending` is not in the type signature; the component is itself marked deprecated.

**Resolution:** Replaced with `useThreadRuntime()` + `subscribe()` to read `isRunning` state reactively. Renders abort button when running, send button when idle. This pattern is more explicit and survives future assistant-ui API changes.

**Risk to α1:** Low — the `useThreadRuntime` pattern is idiomatic for the library's current API direction.

---

### F.4 — `_dev/` route path deviation (Next.js App Router constraint)

**Brief specified:** `src/app/_dev/chat-spike/page.tsx`

**Actual path used:** `src/app/dev/chat-spike/page.tsx` → accessible at `/dev/chat-spike`

**Root cause:** In Next.js App Router, folder names prefixed with `_` are private (non-routable) by convention. `_dev/` would not produce a `/dev/chat-spike` route — it would 404.

**Resolution:** Used `dev/chat-spike` without underscore prefix. The super-admin gate in `dev/layout.tsx` provides equivalent protection.

**Risk to α1:** None — α1 and all subsequent work items target routes under `/consume/**` or new paths that do not involve the `_dev/` convention.

---

## 3. Component Architecture Assessment

### What works well

- **Primitive composition model** — `ThreadPrimitive`, `MessagePrimitive`, `ComposerPrimitive` provide clean separation. Each primitive handles its own scroll anchoring, state subscription, and re-render boundary. No prop drilling needed.
- **AI SDK 6.x stream protocol** — `createUIMessageStream` + `UIMessageChunk` (`text-start/delta/end`, `reasoning-start/delta/end`, `message-metadata`) is well-supported. The spike fixture streams ~300 reasoning chunks + ~1500 text chunks correctly.
- **`ThreadPrimitive.ScrollToBottom`** — automatic scroll anchoring works without manual `useEffect`. Viewport stays at bottom during streaming.
- **TypeScript coverage** — full type safety on message part components once the flat-props pattern is understood. No `any` casts needed.
- **`data-testid` compatibility** — all primitives accept `asChild` or standard HTML props, enabling clean Playwright targeting.

### Gaps to address in α1+

| Gap | Severity | Resolution path |
|---|---|---|
| No markdown rendering in spike | Low | α1 wires `streamdown` (β PLAN §9.3.3) into the `Text` component; spike intentionally uses `<pre>` for raw verification |
| No KaTeX rendering in spike | Low | Same as above — spike verifies the data arrives; visual math rendering is α1 scope |
| No citation rendering | Low | α1 scope |
| `ComposerPrimitive.If` deprecated | Low | Workaround in place; `useThreadRuntime` pattern is stable |
| No edit/regenerate functionality | Low | UI affordances present (`data-testid="copy-btn"`, `"regenerate-btn"`); wiring is α1+ scope |

---

## 4. Performance Observations (fixture mode)

Fixture streams ~1800 chunks total (reasoning + text), each with 4–8ms synthetic delay (~8–14s total). Observations:

- **No visible stutter** during streaming — React batches updates correctly.
- **Memory** — no observable leak across 5 test sends in the same session.
- **Scroll anchor** — viewport stayed within 50px of bottom throughout all test runs (well under the 200px threshold in `spike.spec.ts`).

---

## 5. Files Created / Modified

| Path | Action | Description |
|---|---|---|
| `platform/src/app/dev/layout.tsx` | Created | Super-admin server gate for `/dev/**` routes |
| `platform/src/app/dev/chat-spike/page.tsx` | Created | Spike page with `AssistantRuntimeProvider` + `useChatRuntime` |
| `platform/src/components/chat-v2/spike/ChatSpikeThread.tsx` | Created | Minimal Thread/Message/Composer using assistant-ui primitives |
| `platform/src/app/api/chat/spike/route.ts` | Created | Streaming fixture endpoint (~6k tokens: reasoning, code, math, citations) |
| `platform/tests/e2e/chat-v2/spike.spec.ts` | Created | Playwright E2E: mount, stream, reasoning drawer, scroll anchor, hover actions |
| `platform/tests/fixtures/chat-v2/spike/anthropic_thinking_6k.json` | Created | Placeholder fixture (TODO-record) |
| `platform/tests/fixtures/chat-v2/streaming-chunks/*.json` | Created | Scaffold chunk fixtures (1char, small, large, mixed) |

---

## 6. α1 Readiness Assessment

The spike confirms assistant-ui v0.14.5 is **ready as the foundation for α1**. Proceed with:

- Replacing `<pre>` raw text with `streamdown` (markdown + KaTeX) in the `Text` component
- Wiring citation rendering via `SourceMessagePart`
- Implementing actual copy/regenerate button functionality
- Expanding the fixture or switching to live provider in non-fixture mode

No blockers. No architectural pivots needed.

---

*α0 spike closed 2026-05-16. Authored by Claude Code on branch `feature/chat-v2-bigbang`.*
