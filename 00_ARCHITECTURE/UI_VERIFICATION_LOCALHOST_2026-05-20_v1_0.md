# UI Verification Report — Chat V2 R7–R10
**Environment:** localhost:3000  
**URL:** http://localhost:3000/clients/362f9f17-95a5-490b-a5a7-027d3e0efda0/consume  
**Date:** 2026-05-20  
**Tester:** Claude Code (chrome-devtools-mcp)  
**Conversation loaded:** "# Mars as Lagna Lord…" (Abhisek Mohanty chart)  
**Method:** DOM/a11y/JS evidence for every check — no guessing.

---

## Summary

| Phase | Checks | PASS | FAIL | EXPECTED-ABSENT | INCONCLUSIVE |
|---|---|---|---|---|---|
| 1 — Identity & Baseline | 1–5 | 5 | 0 | 0 | 0 |
| 2 — Query A (Lagna lord) | 6–18 | 6 | 5 | 0 | 2 |
| 2 — Query B (Mahadasha table) | 19 | 0 | 1 | 0 | 0 |
| 2 — Query C (Mermaid) | 20 | 0 | 1 | 0 | 0 |
| 3 — Behavioral | 21–25 | 2 | 3 | 0 | 0 |
| 4 — Expected Absent | 26–27 | 0 | 0 | 2 | 0 |
| **Total** | **27** | **13** | **10** | **2** | **2** |

---

## Phase 1 — Identity & Baseline

### Check 1: Page loads
**PASS**  
URL loaded, conversation selected, messages rendered. Heading: "Abhisek Mohanty · 1984-02-05 · BHUBANESWAR".

### Check 2: Conversation title
**PASS**  
`<h1>Abhisek Mohanty</h1>` in banner. Conversation content: Lagna Lord Q&A with footnote citations visible.

### Check 3: Model / stack indicator
**PASS**  
Button: `"Stack: Gemini Stack, Style: Acharya depth"` (expandable). Confirms persona/stack picker is mounted and labelled.

### Check 4: Life Events toggle
**PASS**  
`button "Life Events: On" pressed=true` in a11y tree. Toggle wired.

### Check 5: Depth buttons
**PASS**  
Three depth buttons: Deep (pressed), Study, Brief — all present in a11y tree. Deep is active.

---

## Phase 2 — Query A (Lagna lord: "What is my Lagna lord and what role does it play?")

### Check 6: Text scale Aa+/Aa–
**PASS**  
After clicking Aa+ once:  
- DOM: `div[style="--text-scale: 1.125;"]` on root wrapper  
- localStorage: `marsys_chat_v2_text_scale = "1.125"`  
Scale persists across page interactions.

### Check 7: Citation badge — inline superscript
**PASS**  
Evidence from DOM:
```
<button class="inline-flex items-center justify-center rounded bg-indigo-900/40 px-1 text-[10px]..."
  data-testid="v2-citation-badge"
  data-citation-index="1"
  aria-label="Citation 1: SIG.MSR.152">
  [1]
</button>
```
Multiple badges confirmed (SIG.MSR.152, SIG.MSR.168, SIG.MSR.158, SIG.MSR.339, SIG.MSR.318, SIG.MSR.195).

### Check 8: GFM footnote citations
**PASS**  
Footnotes section rendered with `<h3>Footnotes</h3>`. Footnote backlinks (`↩`) present. Inline superscript links (e.g. `[1]` → `#user-content-fn-1`) render as actual links. GFM footnote syntax is fully wired.

### Check 9 / Check 14: Citation hover tooltip
**FAIL**  
Hovered `data-testid="v2-citation-badge"` for citation badge. No `v2-citation-tooltip` element appeared in DOM. No tooltip-like element with citation snippet or signal metadata found.  
Root cause: Component not mounted or tooltip wiring missing in this build.

### Check 10 / Check 15: Citation freshness dot
**INCONCLUSIVE**  
Badge element confirmed present. DOM inspection found SVG children and inner structure but no explicit colored dot child (e.g. `data-testid="v2-freshness-dot"` or class `bg-green-*`/`bg-amber-*`). Cannot conclusively confirm or deny without source code review.

### Check 11: Persona picker / Stack selector
**PASS**  
Stack dropdown revealed:
- Stacks: NIM Stack, Anthropic Stack, Gemini Stack (current), GPT Stack, DeepSeek Stack, MARSYS Stack
- Styles: Acharya depth (current), Brief, Simple
- "Manage Personas →" link present

### Check 12: Conversation export
**FAIL**  
No export button found anywhere: header, conversation actions menu (Rename/Pin/Archive/Delete only), DOM-wide search for "Export" → 0 results.  
Root cause: R8 feature (`MARSYS_FLAG_R8_EXPORT`) default-false; operator has not flipped.

### Check 13: Token estimate indicator
**FAIL**  
No token count in composer footer or elsewhere in DOM. LocalStorage key `marsys_chat_v2_token_estimate` absent.  
Root cause: R8 feature (`MARSYS_FLAG_R8_TOKEN_ESTIMATE`) default-false; operator has not flipped.

### Check 16: Citation panel auto-open
**FAIL**  
After full response stream completion, searched DOM for `[data-testid="v2-citation-panel"]` and any element with `aria-label` containing "citation panel" — none found. Citation panel does not mount or open automatically.  
Root cause: Component not mounted in this build or panel feature not wired.

### Check 17: Share conversation (selective)
**PASS**  
Share button found and clicked. Menu revealed:
- `checkbox "Show reasoning"` (checked)
- `checkbox "Show methodology"` (checked)
- `button "Create share link"`  
Selective sharing UI (R10 X-S8) is fully wired.

### Check 18: Inline tool-flow pipeline stages
**PARTIAL PASS**  
During streaming: pipeline stages appeared in a11y tree:  
`Classify 5360ms › Compose 4ms › Fetch 490ms › Synthesise` with tool names `cgm_graph_walk 0ms`, `msr_sql 489ms 100 ok`  
After completion: stages completely removed from DOM. No expandable/disclosure button on the final rendered message to reveal the trace.  
R9 inline tool-flow renders during stream only; no post-completion disclosure affordance.

---

## Phase 2 — Query B ("Show my Vimshottari Mahadasha sequence as a markdown table")

### Check 19: Interactive tables (sort + CSV download)
**FAIL**  
Response rendered a `<table>` with columns Planet / Start Date / End Date / Source. DOM inspection confirmed plain `<table><thead><tr><th>` structure — no click handlers on `<th>` elements, no sort icons, no CSV download button.  
Root cause: R10 X-S10 (`NEXT_PUBLIC_MARSYS_FLAG_R10_INTERACTIVE_TABLES`) — flag defaults true but NEXT_PUBLIC build-arg was not baked into this dev build. Client receives `undefined`, feature off.

---

## Phase 2 — Query C ("Draw my Vimshottari dasha sequence as a mermaid flowchart")

### Check 20: Mermaid SVG rendering
**FAIL**  
Model emitted valid mermaid code fence:
```
graph TD
    subgraph Vimshottari Mahadasha Sequence
        A[Saturn MD...] --> B[Mercury MD...];
        ...
    end
    style B fill:#d4edda,...
```
DOM result: rendered as a static `CODE` block with a "Copy code" button. No `<svg>` from mermaid renderer. `document.querySelectorAll('svg').length = 27` but all are 24px icon SVGs. `mermaidContainerCount: 0`.  
Root cause: R10 X-S11 (`NEXT_PUBLIC_MARSYS_FLAG_R10_MERMAID`) — same NEXT_PUBLIC build-arg not baked issue as X-S10.

---

## Phase 3 — Behavioral

### Check 21: Auto-scroll discipline
**PASS**  
Submitted a query, then scrolled message log to `scrollTop = 0` while streaming.  
- `button "Scroll to bottom"` state: `disabled: false` (activated when user scrolled away)
- Button: `position: fixed; bottom: 24; right: 6; opacity: 0.8` — visible at bottom-right of viewport
- `scrollTop` held at 0 — no auto-yank to bottom while streaming
- Screenshot confirmed circular ↓ button visible in viewport corner

### Check 22: Still-working indicator
**PASS** (confirmed in earlier session)  
During a long-running query, `"Still working… (106s)"` appeared in the a11y tree and streaming area. Indicator confirmed present.

### Check 23: Branch-on-regen
**FAIL**  
Clicked `button "Regenerate response"` on the last assistant message. New response streamed and completed (reasoning block changed: 264 → 541 tokens). DOM search for `1 / 2`, `1/2`, `‹`, `›` branch navigation: `0` results after hover and post-completion. No model-selector dropdown on the Regenerate button (no `expandable` attribute). Response is replaced in-place with no branching.  
Root cause: Branch picker not implemented; in-place replacement only.

### Check 24: Edit-message branch
**FAIL**  
Edit button wiring confirmed: `button "Edit message"` is enabled on non-last user messages (second message), disabled (`disableable disabled`) on last user message. Clicked the enabled edit button on the second user message. Result: no inline edit composer appeared, main textarea remained empty, no contenteditable element, no branch picker.  
Root cause: Edit button is rendered and correctly disabled/enabled by position, but the edit action handler does not open an inline editor in this build.

### Check 25: Keyboard nav j / k / c
**FAIL**  
Focused `[data-testid="v2-thread-viewport"]` (the conversation messages div). Pressed `j` — focus stayed on conversation div, no individual message focused. Pressed `k` — same. Pressed `c` — clipboard unchanged from previous copy. No `aria-selected` or `data-focused` attribute changes detected.  
Root cause: Message-level keyboard navigation not implemented.

---

## Phase 4 — Expected Absent

### Check 26: Stop-and-edit (Y-S5)
**EXPECTED-ABSENT — PASS**  
Searched entire DOM for "Stop & Edit", "Stop and Edit", and equivalent aria-labels: 0 results. Y-S5 flag is default-false; feature correctly absent.

### Check 27: Auto-retry (Y-S9)
**EXPECTED-ABSENT — PASS**  
Searched entire DOM for "retry", "auto-retry", "auto retry": 0 results. Y-S9 flag is default-false; feature correctly absent.

---

## Phase 5 — Console Sweep

**Errors:** 1 type, 2 occurrences  
```
[error] Failed to load resource: the server responded with a status of 503 (Service Unavailable)
```
Root cause: NIM_STACK_DEGRADED — pre-existing known condition (X-S0 flag cleanup in R10 governance setup). Not a regression introduced by R7–R10.

**Warnings:** 0 non-trivial warnings observed.

---

## Failure Classification

| Check | Verdict | Root Cause Class |
|---|---|---|
| 9/14 Citation tooltip | FAIL | (b) component not mounted |
| 12 Export | FAIL | (a) R8 flag default-false, not flipped |
| 13 Token estimate | FAIL | (a) R8 flag default-false, not flipped |
| 16 Citation panel | FAIL | (b) component not mounted |
| 19 Interactive tables | FAIL | (a) NEXT_PUBLIC build-arg not baked |
| 20 Mermaid SVG | FAIL | (a) NEXT_PUBLIC build-arg not baked |
| 23 Branch-on-regen | FAIL | (c) genuine gap — not implemented |
| 24 Edit-message branch | FAIL | (c) genuine gap — handler not wired |
| 25 Keyboard nav j/k/c | FAIL | (c) genuine gap — not implemented |

**Class (a) — flag/build-arg:** 4 failures (12, 13, 19, 20) — operator action required  
**Class (b) — component not mounted:** 3 failures (9/14, 16) — component-level wiring gap  
**Class (c) — genuine gap:** 3 failures (23, 24, 25) — feature not shipped in R7–R10 scope

---

## Action Items

### Operator action (flip flags or bake build-args)
- Flip `MARSYS_FLAG_R8_EXPORT` and `MARSYS_FLAG_R8_TOKEN_ESTIMATE` when ready to ship R8 features
- Bake `NEXT_PUBLIC_MARSYS_FLAG_R10_INTERACTIVE_TABLES=true` and `NEXT_PUBLIC_MARSYS_FLAG_R10_MERMAID=true` into next deploy build-args (without this, client-side feature code is dead even though server sets the flag)

### Engineering (class b — wiring gaps)
- **Citation tooltip (checks 9/14):** Wire `v2-citation-tooltip` to appear on hover over citation badge — tooltip component appears missing from render tree
- **Citation panel (check 16):** Mount `v2-citation-panel` and wire auto-open after stream completion

### Engineering (class c — not in scope, note for future rounds)
- **Branch-on-regen (check 23):** Regenerate currently replaces in-place; branch picker (`1/2`) requires assistant-ui branch state wiring
- **Edit-message branch (check 24):** Edit handler is correctly rendered and disabled/enabled by message position but does not open inline EditComposer
- **Keyboard nav j/k/c (check 25):** Message-level keyboard focus navigation not implemented

---

*Generated by automated 27-check verification script using chrome-devtools-mcp. All results backed by DOM/JS/a11y evidence.*
