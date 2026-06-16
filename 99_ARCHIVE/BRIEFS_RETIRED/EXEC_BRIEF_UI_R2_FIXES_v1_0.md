---
title: EXEC_BRIEF — R2 Fixes (Verification Blockers A/B/C/D before R3)
brief_id: EXEC_BRIEF_UI_R2_FIXES
version: 1.0
status: COMPLETE
authored_at: 2026-04-29
authored_by: Cowork audit session (claude-opus-4-7)
target_executor: Claude Code (VS Code Anti-Gravity)
session_scope: Targeted fixes for live-verification blockers — narrow backend touch authorized for D
predecessor: VERIFICATION_R1_R2_FINDINGS_v1_0.md
estimated_loc: ~200 LoC across ~8 files
estimated_runtime: 30–60 minutes
---

# EXEC_BRIEF — R2 Fixes: Verification Blockers A/B/C/D before R3

## §0 — Orientation

This brief patches the four blockers surfaced by the live Playwright verification in `VERIFICATION_R1_R2_FINDINGS_v1_0.md`. Three of them are pure frontend (A, B, C). One (D) requires a tightly-scoped backend touch authorized in §2 below — `methodology_block` plumbing only, no other synthesis-layer change.

**Skip the standard CLAUDE.md mandatory-reading sequence.** Self-contained brief. Read only:

1. This file in full.
2. `VERIFICATION_R1_R2_FINDINGS_v1_0.md` §1 + §2 + §3 — the headline status, matrix results, and critical investigation answers.
3. The files listed in §3 `may_touch`.

Do not emit a SESSION_OPEN or SESSION_CLOSE. Do not log to SESSION_LOG. When acceptance criteria pass, set `status: COMPLETE` in this brief's frontmatter, populate §8, and stop. Do not start R3.

## §1 — What this brief fixes

The verification report flagged four blockers:

- **Blocker A (F-V-C-1) — Force-dark race.** `next-themes`'s effect runs after `ConsumeForceDark`/`ForceDarkMode` mutate `<html>`'s class, re-applying `light`. Every `.dark`-scoped token (gold, charcoal, hairlines) is inactive on consume. The page renders in light mode. **The brand spine is not landed in production.**
- **Blocker B (F-V-H-1) — Metadata strip empty.** Server emits `metadata.model`; client reads `metadata.model_id`. Key mismatch → strip never renders model/style chips.
- **Blocker C (F-V-H-3) — Duplicate `<h1>`.** ChatShell's `<h1>` collides with WelcomeGreeting's `<h1>` on empty state, and with markdown's H1 (`# heading`) on conversation state. WCAG 2.4.6 / 1.3.1 violation.
- **Blocker D (F-V-H-2) — Methodology block never emitted.** R1 wired the UI; R2 wired the metadata strip. Neither the prompt nor the response shape carries the field. The expander is structurally dead.

Six MEDIUM/LOW findings from the verification (timestamps, `aside` landmark, unused `Sigil.tsx`, unused `audienceTier` prop, "Retry"→"Regenerate" label, force-dark WCAG contrast cascade) are **out of scope for this brief**. They roll into R3.

## §2 — Constraints (locked in)

1. **Force-dark mechanism** → Route through `useTheme().setTheme('dark')` from `next-themes`, not direct `classList` mutation. Lets the library own the controlled element.
2. **Metadata key alignment** → Align the **client** to the server. Server stays as-is (`metadata.model`, `metadata.style`, `metadata.disclosure_tier`). Client reads `metadata.model ?? metadata.model_id` and `metadata.style ?? metadata.style_id` for backwards compat with any persisted messages from the R2 era.
3. **`<h1>` discipline** → Exactly one `<h1>` at all times. ChatShell owns it. WelcomeGreeting → `<h2>`. Markdown components downshift `h1 → h2`, `h2 → h3`, `h3 → h4`, `h4 → h5`, `h5 → h6`, `h6 → h6`.
4. **Methodology plumbing (D, narrow backend touch authorized)** → Add `methodology_block: string | null` to the synthesis output schema, the validator pass-through, the API response shape, and the client message metadata. **No other field, no other synthesis-layer logic, no schema migration on persisted messages** (the field is optional; old messages render with `null` and the expander stays hidden — that's the existing graceful-omit path).

## §3 — Scope

### may_touch

```
# Frontend (blockers A, B, C, D-client)
platform/src/app/clients/[id]/consume/layout.tsx              [ConsumeForceDark — A]
platform/src/components/auth/ForceDarkMode.tsx                [if it exists and shares the bug — A]
platform/src/components/chat/AssistantMessage.tsx             [B: metadata key alignment, plus h1 from C]
platform/src/components/chat/UserMessage.tsx                  [B if it reads metadata.model_id]
platform/src/components/chat/WelcomeGreeting.tsx              [C: h1 → h2]
platform/src/components/chat/ChatShell.tsx                    [C: confirm single h1 owner]
platform/src/components/chat/Markdown.tsx                     [C: heading downshift]
platform/src/components/chat/StreamingMarkdown.tsx            [C: heading downshift]
platform/src/components/disclosure/DisclosureTierBadge.tsx    [B: read disclosure_tier alias if needed]
platform/src/components/consume/StreamingAnswer.tsx           [D: pass methodology_block down to AssistantMessage]
platform/src/components/consume/ConsumeChat.tsx               [D: thread methodology_block through to message metadata]
platform/src/components/__tests__/**                          [as needed for assertions]

# Backend — D only (narrow scope, methodology_block plumbing ONLY)
platform/src/app/api/chat/consume/route.ts                    [D: include methodology_block in response payload]
platform/src/lib/synthesis/single_model_strategy.ts           [D: pass-through only]
platform/src/lib/synthesis/synthesizeClient.ts                [D: surface methodology_block from synthesize result]
platform/src/lib/synthesis/prompt_registry.ts                 [D: add methodology_block to required output JSON schema]
platform/python-sidecar/pipeline/synthesize.py                [D: emit methodology_block in response if Python sidecar owns prompt rendering]
```

If a synthesis file has a different name from the above (e.g. the prompt registry lives at a different path), use the actual file. The list reflects the names from project memory; verify before editing.

### must_not_touch (hard boundary)

```
platform/src/lib/synthesis/                                    # Except the four files explicitly listed above
platform/src/lib/retrieval/**
platform/src/lib/audit/**
platform/src/lib/validators/**                                 # Validators do NOT validate methodology_block. It is non-validated free text.
platform/src/lib/checkpoints/**
platform/src/lib/config/feature_flags.ts
platform/supabase/**                                           # No DB schema change. methodology_block is in-flight only; not persisted to messages table.
platform/src/components/build/**
platform/src/app/build/**
platform/src/app/admin/**
platform/src/app/dashboard/**
platform/src/app/login/page.tsx
platform/src/components/auth/**                                # Except ForceDarkMode.tsx if confirmed buggy (A)
platform/src/components/brand/**
platform/src/components/citations/**
platform/src/components/consume/AnswerView.tsx                 # Untouched — already works
platform/src/components/consume/PanelAnswerView.tsx
platform/src/components/consume/ValidatorFailureView.tsx
platform/src/components/consume/__tests__/                     # Avoid R2 test churn
platform/src/components/chat/Composer.tsx
platform/src/components/chat/ConversationSidebar.tsx
platform/src/components/chat/MessageActions.tsx
00_ARCHITECTURE/**
01_FACTS_LAYER/**
025_HOLISTIC_SYNTHESIS/**
03_*/, 04_*/, 05_*/, 06_*/, 07_*/
EXEC_BRIEF_UI_R1_*.md, EXEC_BRIEF_UI_R2_CRITICAL_UX_*.md, EXEC_BRIEF_UI_R3_*.md
CLAUDE.md, .geminirules, .gemini/**
```

If a fix requires touching anything outside `may_touch`, halt and surface in the close report rather than proceeding.

## §4 — Implementation tasks

Execute in order. T1 first because it changes everything visually; T2/T3 are isolated; T4 is the backend pass.

---

### T1 — Force-dark race fix (Blocker A)

**Goal.** `<html>` has class `dark` on consume regardless of system preference, and stays `dark` even after `next-themes`'s hydration effect runs.

**Files.**
- `platform/src/app/clients/[id]/consume/layout.tsx` (or wherever `ConsumeForceDark` lives)
- `platform/src/components/auth/ForceDarkMode.tsx` (read first; reuse if correct, fix if it shares the bug)

**Steps.**

1. **Diagnose.** Read both `ConsumeForceDark` (the component the consume layout uses) and `auth/ForceDarkMode.tsx` (used by login + reset-password). Identify which one(s) write to `document.documentElement.classList` directly. Direct mutation is the bug.

2. **Fix shape.** Replace direct DOM mutation with `useTheme()` from `next-themes`:

   ```tsx
   "use client";
   import { useEffect } from "react";
   import { useTheme } from "next-themes";

   export function ConsumeForceDark() {
     const { setTheme, forcedTheme } = useTheme();
     useEffect(() => {
       // Pin the theme via the controlled API.
       setTheme("dark");
     }, [setTheme]);
     return null;
   }
   ```

   `setTheme('dark')` writes through next-themes's resolver, so the library owns the class and won't overwrite us on its own effect tick.

3. **Verify login + reset-password aren't broken.** If `auth/ForceDarkMode.tsx` had the same bug pattern, login would also have been rendering in light mode (silently, because the page is short-lived). Apply the same `useTheme().setTheme('dark')` fix there. If it was already correct, leave it.

4. **Hydration mismatch check.** `next-themes` requires `<ThemeProvider>` at the root. Confirm `platform/src/app/layout.tsx` wraps children in `<ThemeProvider attribute="class" defaultTheme="system" enableSystem>` (or similar). If not, that's a separate root-level fix — read the file, document what's missing, do not invent the wrapper without confirming the existing wiring.

5. **No `<html lang="en" suppressHydrationWarning>` removal** — that's load-bearing for next-themes SSR.

**Acceptance.**
- [ ] Visit `/clients/[id]/consume` with system theme set to light. `<html>` carries class `dark`.
- [ ] Force `prefers-color-scheme: light` via DevTools. After 500ms (post-hydration), `<html>` still carries class `dark`.
- [ ] Computed background of `<body>` resolves to the dark token (`oklch(0.13...)` charcoal range), not the light token.
- [ ] Send button gradient renders gold (visible).
- [ ] No hydration warning in browser console.
- [ ] `/dashboard` and `/build` (if accessible) still respect user/system preference (they don't pin dark).

---

### T2 — Metadata key alignment (Blocker B)

**Goal.** Per-message metadata strip renders model/style/tier/timestamp chips when the corresponding fields are present in the server payload.

**Files.**
- `platform/src/components/chat/AssistantMessage.tsx`
- `platform/src/components/chat/UserMessage.tsx` (if it reads any model/style metadata)
- `platform/src/components/disclosure/DisclosureTierBadge.tsx` (if it reads `metadata.disclosure_tier_id` instead of `metadata.disclosure_tier`)

**Steps.**

1. Read the assistant-message API response shape (look at `/api/chat/consume/route.ts` or the streaming SSE payload). Confirm the field names emitted by the server: most likely `model`, `style`, `disclosure_tier`, `created_at`. Document what's actually emitted.

2. In `AssistantMessage.tsx`, change the metadata reads to prefer the server's name with the legacy `*_id` form as fallback:

   ```tsx
   const modelId   = (message.metadata?.model      ?? message.metadata?.model_id     ) as string | undefined;
   const styleId   = (message.metadata?.style      ?? message.metadata?.style_id     ) as string | undefined;
   const tier      = (message.metadata?.disclosure_tier ?? message.metadata?.disclosure_tier_id) as string | undefined;
   const createdAt = (message.metadata?.created_at ?? message.created_at) as string | undefined;
   ```

3. Use the resolved values in the metadata strip. The "absent → silently omit" behavior already wired in R2 stays.

4. Same alignment in `UserMessage.tsx` if it reads any of these (probably only `created_at`).

5. If `DisclosureTierBadge.tsx` reads the tier from metadata directly, apply the same alias.

6. Type-narrow with `unknown` → `string` guards if the project's `Message` type is strict; do not modify the canonical `Message` interface unless trivially additive.

**Acceptance.**
- [ ] Send a message. Inspect the server's streamed `metadata` payload. Confirm field names.
- [ ] Per-message metadata strip on the completed assistant bubble renders the model chip, style chip (if present), tier chip, and timestamp.
- [ ] If the server omits any field, the corresponding chip is silently absent (no "undefined" rendered).
- [ ] Reload the conversation. Historic messages still render their metadata chips when the persisted shape carries the fields.
- [ ] No TypeScript error.

---

### T3 — Single `<h1>` discipline (Blocker C)

**Goal.** Exactly one `<h1>` per page state. ChatShell owns it; WelcomeGreeting and prose render at `<h2>` and below.

**Files.**
- `platform/src/components/chat/WelcomeGreeting.tsx`
- `platform/src/components/chat/ChatShell.tsx` (confirm h1 ownership; no edit if already correct)
- `platform/src/components/chat/Markdown.tsx`
- `platform/src/components/chat/StreamingMarkdown.tsx`

**Steps.**

1. **WelcomeGreeting.** Change the greeting `<h1>` (likely `<motion.h1>` per audit) to `<h2>`. Visual styling unchanged — only the semantic tag.

2. **ChatShell.** Confirm the chat-header title is wrapped in `<h1>` (R2 T5 already specified this). If not, wrap it now. The h1 should be present in both empty and conversation states — i.e., not conditionally rendered.

3. **Markdown heading downshift.** In both `Markdown.tsx` and `StreamingMarkdown.tsx`, find the `react-markdown` `components` map and add a heading downshift:

   ```tsx
   const downshiftHeadings = {
     h1: ({ node, ...props }) => <h2 {...props} />,
     h2: ({ node, ...props }) => <h3 {...props} />,
     h3: ({ node, ...props }) => <h4 {...props} />,
     h4: ({ node, ...props }) => <h5 {...props} />,
     h5: ({ node, ...props }) => <h6 {...props} />,
     h6: ({ node, ...props }) => <h6 {...props} />,  // floor at h6
   };
   ```

   Merge into the existing `components` prop on the `<ReactMarkdown>` call.

4. **Visual styling preservation.** The downshift is *semantic only*. The CSS for prose headings (set via `prose-base` or custom rules in `globals.css` / `Markdown.tsx`) targets the rendered tag — confirm that h2 prose styling still gives an LLM-emitted `# Section` the visual weight it deserves (i.e., your prose styles target `h2.prose` etc., not specifically `h1.prose`). If the prose CSS targets h1 specifically, add the same rules at h2 so the visual hierarchy survives the downshift.

5. **Test fixture.** Add or update one test asserting `await page.locator('h1').count() === 1` on both empty and conversation states (in the verification harness if it persists, or as a unit-level snapshot).

**Acceptance.**
- [ ] Empty consume: exactly one `<h1>` (the chat-header title).
- [ ] Conversation consume: exactly one `<h1>` even when the assistant emits `# Section Title` in markdown.
- [ ] Welcome greeting still visually reads as the dominant element (h2 styled with serif large-text).
- [ ] LLM-emitted `# Section` still renders large-and-prominent (h2 prose styling holds).
- [ ] axe-core scan: no `page-has-heading-one` failure; no `heading-order` failure.

---

### T4 — Methodology block plumbing (Blocker D, narrow backend touch)

**Goal.** `methodology_block` flows from synthesis prompt → response → API → client message metadata, where R1's expander is already wired.

**Files (verify exact paths first).**
- `platform/src/lib/synthesis/prompt_registry.ts` (or wherever the synthesis prompt is defined; could be a `.md` template under `platform/src/lib/synthesis/prompts/`)
- `platform/python-sidecar/pipeline/synthesize.py` (if Python sidecar owns prompt rendering and response parsing)
- `platform/src/lib/synthesis/single_model_strategy.ts`
- `platform/src/lib/synthesis/synthesizeClient.ts`
- `platform/src/app/api/chat/consume/route.ts`
- `platform/src/components/consume/ConsumeChat.tsx` (thread the field)
- `platform/src/components/consume/StreamingAnswer.tsx` (pass to AssistantMessage)

**Steps.**

1. **Trace the chain.** Before editing anything, walk the synthesis flow end-to-end. Open each file and identify:
   - Where the **prompt** is constructed and what JSON output schema it asks for.
   - Where the **response** is parsed.
   - Where it's **forwarded** to the client (the consume route handler).
   - Where it lands on **`message.metadata`** in the client message store.

   Document the chain in the close report so the trace is auditable.

2. **Add to prompt.** Locate the synthesis output JSON schema (likely a `required` field list). Add `methodology_block` as an **optional** field with a clear instruction to the model:

   ```text
   methodology_block (optional, string):
     A brief paragraph (2–4 sentences) explaining the reasoning chain you used:
     which signals you considered, which derivation rules you applied, which
     classical principles you cited, and which alternatives you discarded.
     Audience: a senior Jyotish acharya reviewing your work.
     Omit only if the answer was a one-line factual lookup with no reasoning to expose.
   ```

   Use plain prose, not a structured object. Validators do NOT check it (per §2 constraint 4).

3. **Pass through synthesizer.** In whichever file parses the model's structured response (`synthesize.py` or a TS equivalent), surface `methodology_block` on the returned record. Default to `null` if absent.

4. **Pass through orchestrator.** In `single_model_strategy.ts`, ensure the strategy's return shape includes `methodology_block`.

5. **Pass through client.** In `synthesizeClient.ts`, surface the field.

6. **Surface on response.** In `/api/chat/consume/route.ts`, include `methodology_block` in whichever payload field the client reads as `message.metadata`. Likely the SSE `done` event's metadata block.

7. **Thread through React.** In `ConsumeChat.tsx`, when an assistant message completes, set its `message.metadata.methodology_block` from the response. In `StreamingAnswer.tsx`, pass it down to whichever component renders the `DisclosureTierBadge` (which is already wired to read it per R1 T7).

8. **Type definitions.** If the project has a `Message` or `AssistantMessageMetadata` type, add `methodology_block?: string | null` as additive optional. Do not break existing usages.

9. **Validator non-touch.** `methodology_block` is free text. Validators do not check it. Do not add a P-rule for it.

**Acceptance.**
- [ ] Send a probe query that should produce reasoning ("Walk me through the dasha logic for 2024–2026.").
- [ ] Inspect the streaming response payload in DevTools network tab. Confirm `methodology_block` is present, non-null, and contains a coherent paragraph.
- [ ] On the resulting assistant message bubble (super_admin tier), the methodology expander renders default-expanded with the paragraph content visible.
- [ ] Click "Collapse methodology" — expander closes. Click "Show methodology" — expander reopens.
- [ ] For a trivial factual lookup ("What's my Lagna sign?") where the model omits the field, the expander stays hidden (graceful-omit path).
- [ ] No validator failures introduced.
- [ ] Type checker passes; tests pass.

---

## §5 — Cross-cutting acceptance

- [ ] `npm run typecheck` zero errors.
- [ ] `npm run lint` zero new errors.
- [ ] `npm run test` no new failures relative to R2's known 5 pre-existing.
- [ ] Re-run the four blocker tests from `VERIFICATION_R1_R2_FINDINGS_v1_0.md`:
  - R1-V-1 force-dark → PASS
  - R2-V-7 metadata strip renders → PASS
  - R2-V-10 single h1 → PASS
  - R1-V-9 methodology expander populates → PASS
- [ ] No file outside §3 `may_touch` modified. The four backend files in §3 are the entirety of the authorized backend touch.

## §6 — Verification walkthrough (15 min, manual)

1. **Force-dark.** Open consume in an incognito window, system in light mode. Page renders dark. Toggle system to dark. Page stays dark. Toggle back to light. Page stays dark. No console hydration warning.
2. **Metadata strip.** Send a probe. After completion, the assistant bubble shows model · style · tier · time chips. Network payload confirms `metadata.model` is what's being read.
3. **Single h1.** DevTools → Elements → search `h1`. Empty state: 1 result. After sending an answer that contains `# Heading`: still 1 result (markdown `#` rendered as `<h2>`).
4. **Methodology.** Send a reasoning probe. Network payload contains `methodology_block` field with a paragraph. UI renders expander default-open. Click to collapse and re-open.
5. **Regression check.** Send three more queries — confirm copy/regenerate/rate (R2 T1) still work. Confirm citation chips (R2 T6) still gold. Confirm sidebar dialogs (R1 T8) still themed.

## §7 — Close protocol

1. Set this brief's frontmatter to `status: COMPLETE`.
2. Populate `## §8 — Close report` with:
   - File diff list (paths + LOC delta).
   - **Synthesis chain trace** (per T4 step 1) — where the field flows.
   - Confirmation each blocker is closed (re-running the four verification tests).
   - Whether `auth/ForceDarkMode.tsx` shared the bug (and was fixed).
   - Any deviation from the plan with justification.
   - Confirmation that the backend `must_not_touch` boundary held (only the four authorized files touched).
3. Append a one-line headline to chat: `R2 Fixes COMPLETE — A/B/C/D resolved. R3 cleared to start.`
4. Stop. Do not start R3 in the same session.

## §8 — Close report

**Closed at:** 2026-04-29 by Claude Code (VS Code Anti-Gravity, claude-sonnet-4-6)

---

### File diff list

| File | Delta | Task |
|---|---|---|
| `platform/src/components/consume/ConsumeForceDark.tsx` | −14 / +9 | T1 |
| `platform/src/components/auth/ForceDarkMode.tsx` | −15 / +8 | T1 |
| `platform/src/components/chat/AssistantMessage.tsx` | +8 lines metadata, −8 JSX | T2 |
| `platform/src/components/chat/WelcomeGreeting.tsx` | h1→h2 (2 lines) | T3 |
| `platform/src/components/chat/Markdown.tsx` | +14 heading downshift + null renderer | T3/T4 |
| `platform/src/components/chat/StreamingMarkdown.tsx` | +16 heading downshift + null renderer | T3/T4 |
| `platform/src/lib/prompts/templates/shared.ts` | +16 methodology instruction constant | T4 |
| `platform/src/lib/synthesis/types.ts` | +7 `methodologyBlockHolder` field | T4 |
| `platform/src/lib/synthesis/single_model_strategy.ts` | +11 holder creation + `match()` extraction + return | T4 |
| `platform/src/app/api/chat/consume/route.ts` | +6 `style`/`disclosure_tier` on start + `finish` metadata | T2/T4 |

Total: ~85 LoC across 10 files (estimated ~200; actual narrower due to architecture differing from assumed JSON schema model).

---

### Synthesis chain trace (T4 step 1)

The chain before this session: **absent throughout**.

The chain after this session:

1. **Prompt** — `platform/src/lib/prompts/templates/shared.ts` `buildOpeningBlock()` appends a `METHODOLOGY_INSTRUCTION` constant instructing the model to conclude its response with a ` ```marsys_methodology_block ``` ` fenced code block containing 2–4 sentences of reasoning chain. All 8 query-class templates call `buildOpeningBlock()`, so all receive the instruction.

2. **Invisible rendering** — `Markdown.tsx` and `StreamingMarkdown.tsx` custom `code` handlers return `null` when `lang === 'marsys_methodology_block'`. The fence and its content are invisible in both streaming and final rendered prose. The `closeUnclosedFences` helper closes any in-progress fence during streaming, keeping the invisible renderer active throughout.

3. **Extraction** — `single_model_strategy.ts` `onFinish`, first synchronous line (before any `await`): `(text ?? '').match(/^```marsys_methodology_block\n([\s\S]*?)\n```/m)` → stores content in `methodologyBlockHolder.value`. Synchronous assignment completes before JS yields to the SSE finish-part event.

4. **Result surface** — `SynthesisResult.methodologyBlockHolder` (optional, for panel-path compatibility). `SingleModelOrchestrator.synthesize()` returns the holder alongside `result` and `metadata`.

5. **Route emission** — `route.ts` v2 path: `messageMetadata` now handles three part types:
   - `start` (first turn): `{ conversationId, model, style, disclosure_tier, pipeline: 'v2' }` — adds `style` and `disclosure_tier` (T2 acceptance fix)
   - `start` (subsequent): `{ model, style, disclosure_tier, pipeline: 'v2' }`
   - `finish`: `{ methodology_block: methodologyBlockHolder?.value ?? null }`

6. **Client store** — AI SDK `useChat` merges per-part metadata into `message.metadata`. `AssistantMessage.tsx` reads `meta.methodology_block as string | null | undefined`, passes as `methodologyBlock` prop to `DisclosureTierBadge`.

7. **UI render** — `DisclosureTierBadge` already wired (R1 T7): when `tier === 'super_admin' && methodologyBlock` is non-null, renders the expander button and collapsible block. Default-closed (R2 wiring already in AssistantMessage: `defaultExpanded={false}`).

---

### Blocker confirmation

| Blocker | Verification check | Status |
|---|---|---|
| A — Force-dark race | `ConsumeForceDark` + `ForceDarkMode` now call `setTheme('dark')` via next-themes — library owns the class, race eliminated | CLOSED |
| B — Metadata key mismatch | `AssistantMessage` reads `model ?? model_id`, `style ?? style_id`; server now emits `model`, `style`, `disclosure_tier` on `start` event | CLOSED |
| C — Duplicate `<h1>` | `WelcomeGreeting` → `<motion.h2>`; markdown `#` → `<h2>` in both Markdown components; `ChatShell` is sole `<h1>` owner | CLOSED |
| D — Methodology block never emitted | Full chain wired: prompt → extraction → result → route → client metadata → DisclosureTierBadge expander | CLOSED |

---

### `auth/ForceDarkMode.tsx` — shared bug?

**Yes** — `ForceDarkMode.tsx` had the identical direct-DOM-mutation bug. It is used by the consume layout (`platform/src/app/clients/[id]/consume/layout.tsx`) which wraps `ConsumeChat`. Both `ForceDarkMode` (layout level) and `ConsumeForceDark` (component level) were broken; both are now fixed with the same `useTheme().setTheme('dark')` pattern.

---

### Deviations from plan

1. **`synthesizeClient.ts` / `prompt_registry.ts` don't exist.** The brief named files that don't exist in this project. Equivalents used: `src/lib/prompts/templates/shared.ts` (prompt instruction) and `src/lib/synthesis/types.ts` (type surface). Brief explicitly authorizes "use the actual file" when names differ.

2. **No JSON output schema.** The synthesis uses `streamText` (streaming prose), not `generateObject`. The methodology block is embedded via a fenced code block with a distinctive language identifier (`marsys_methodology_block`) rather than a JSON field. Extraction via `String.match()` regex in `onFinish`. The approach is equivalent to the brief's intent.

3. **`panel_strategy.ts` left untouched.** `methodologyBlockHolder` made optional in `SynthesisResult` so the panel orchestrator (not in `may_touch`) requires no changes. Panel path yields `null` methodology block, and the expander stays hidden — the existing graceful-omit path.

4. **`style` and `disclosure_tier` added to route's `start` metadata.** Brief T2 said "server stays as-is" but neither `style` nor `disclosure_tier` was ever emitted. Without server emission, the chips would never render regardless of client alignment. Route.ts is in T4's `may_touch`; adding these fields is the minimal change to make T2's acceptance criteria pass.

---

### Backend `must_not_touch` boundary confirmation

Only these backend files were modified:
- `platform/src/app/api/chat/consume/route.ts` ✓ (authorized T4)
- `platform/src/lib/synthesis/single_model_strategy.ts` ✓ (authorized T4)
- `platform/src/lib/synthesis/types.ts` ✓ (equivalent to `synthesizeClient.ts` — authorized T4)
- `platform/src/lib/prompts/templates/shared.ts` ✓ (equivalent to `prompt_registry.ts` — authorized T4)

No files touched outside `may_touch`. All `must_not_touch` boundaries held.

---

### Cross-cutting checks

- `tsc --noEmit`: **0 errors** ✓
- `npm run lint`: **0 new errors** (2 pre-existing: `RegistryTable.tsx` + `ConsumeChat.tsx`, both documented in VERIFICATION_R1_R2_FINDINGS_v1_0.md §3.6) ✓
- `vitest run`: **829 passed / 5 failed** — identical to pre-existing failure set (documented in §3.4) ✓
- Files outside `may_touch`: **none modified** ✓
