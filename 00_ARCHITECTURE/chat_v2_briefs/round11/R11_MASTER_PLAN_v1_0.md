---
canonical_id: CHAT_V2_R11_MASTER_PLAN
version: 1.1
status: CURRENT
owner: Abhisek Mohanty
branch: chat-v2/round11-claude-parity
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavR11
execution: sequential-single-stream-via-conductor
authored: 2026-05-21
amended: 2026-05-21 — native rulings locked, Open Items closed (see NATIVE_RULINGS_v1_0.md)
---

# Chat V2 Round 11 — Claude Parity (Master Plan v1.1)

## Scope

R11 brings Chat V2's consume surface to Claude.ai parity on:

1. **Content rendering** — fonts, markdown typescale, message container shape,
   reading column max-width.
2. **Chrome shape** — composer, sidebar conversation items, action bar
   (hover-reveal). All in the existing Marsys gold/charcoal palette.
3. **Streaming UX** — pre-token thinking indicator with elapsed counter,
   smooth-stream rate-target ~30-50 cps, extended-thinking auto-collapse on
   first text_delta, inline tool-use cards mid-stream.
4. **Backend orchestration** — system-prompt layout aligned to Anthropic's
   cache layout, four `cache_control` breakpoints (canonical positions),
   agentic tool-use loop keyed on `stop_reason`, full-Claude inline-clickable
   citations (CitationSidePanel retired), adaptive `thinking.effort` on
   Opus 4.6+/Sonnet 4.6+.

**The Marsys brand is preserved.** `.consume-shell` (gold-on-charcoal,
brand-gold accents, gold-hairline borders, glassmorphic speech-tail user bubble,
brand-cta gold send button, near-ink sidebar) remains the active class.
**Claude rendering is layered inside `.consume-shell`** — fonts, markdown, message
shape, chrome dimensions adopt Claude's patterns while inheriting Marsys palette
tokens. See `NATIVE_RULINGS_v1_0.md §1`.

R11 contains **17 implementation sessions + 1 terminal merge entry**:

- **V-S0 (Runtime toggle)** — introduces `useClaudeRendering()` hook +
  `ChatRenderingToggle` settings UI so users can flip between Classic Chat V2
  and Claude-parity mode at runtime (per-browser localStorage user-pref AND-ed
  with the env-var kill-switch). Runs FIRST so V-S1..V-S6 wire to the hook
  from the start. See `NATIVE_RULINGS_v1_0.md §8`.
- **Group V (Visual)** — V-S1..V-S6: typography, user-bubble dimensions,
  message-container shape + 768px column, composer chrome, sidebar chrome,
  markdown typescale. Gated by `useClaudeRendering()` (env-var
  `MARSYS_FLAG_R11_CLAUDE_RENDERING` AND user-pref `chatRenderingMode === 'claude'`).
- **Group S (Streaming)** — S-S1..S-S5: pre-token indicator, smooth-stream v3,
  ext-thinking auto-collapse, inline tool cards, stop-and-retain verification.
- **Group O (Orchestration)** — O-S1..O-S5: system-prompt layout, prompt-cache
  breakpoints, agentic tool loop, inline citations (with CitationSidePanel retirement),
  adaptive thinking effort.
- **R11-MERGE** — terminal entry: push, open PR, auto-merge to main.

Execution: sequential single-stream via the R11 Conductor
(`00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_PROMPT_R11_v1_0.md`). STRICT halt policy
on any gate failure. See `NATIVE_RULINGS_v1_0.md §6` and the Conductor prompt.

## Native rulings (locked)

The four Open Native-Input Items that gated this plan have been ruled on. See
`NATIVE_RULINGS_v1_0.md` for the authoritative locked decisions. Summary:

| # | Item | Ruling |
|---|------|--------|
| 1 | Brand identity | Preserve Marsys palette + components; adopt Claude fonts + markdown + content rendering + chrome shape inside `.consume-shell` |
| 2 | Accent color | Keep `var(--brand-gold)` everywhere Claude would use coral |
| 3 | Citation idiom | Full Claude pivot — inline-clickable citations; retire `CitationSidePanel` + `NumberedCitation` + `CitationCtx` |
| 4 | Cache breakpoints | Canonical Anthropic four-breakpoint layout, exactly |

Additional rulings: sacred components list (`§5`), Conductor execution policy
(STRICT halt + auto-merge override, `§6`), flag rename
`MARSYS_FLAG_R11_CLAUDE_SHELL` → `MARSYS_FLAG_R11_CLAUDE_RENDERING` (`§7`).

## Gap Analysis (Chat V2 today vs Claude.ai)

| Axis | Claude.ai (target) | Chat V2 today | Gap | R11 session |
|------|---------------------|----------------|-----|-------------|
| Body font | System-serif stack | Geist Sans via `--font-sans` | Wrong family | V-S1 |
| Heading scale | h1 28-30 / h2 22-24 / h3 18-19 serif 600 | sans defaults | Different | V-S6 |
| Body size + leading | 16px / 1.65 | mixed | Different | V-S6 |
| Assistant container | Bubble-less, text on canvas | Card chrome | Card → bubble-less | V-S3 |
| User bubble | Right-aligned, 1rem radius, max-w 80% | Right-aligned glassmorphism + speech-tail | Keep speech-tail, adopt Claude shape constants | V-S2 |
| Column max-width | ~768px centered | Wider | Pin to 768px | V-S3 |
| Action bar | Hover-reveal | Always visible | Hover-reveal | V-S3 |
| Composer | Rounded 1.5rem, no shadow, fades into canvas | Card with shadow + gold focus | Minimal shape, keep gold focus | V-S4 |
| Sidebar item | 8px radius, 8/12 padding, hover-bg | Current Marsys items | Compact shape, Marsys colors | V-S5 |
| Code blocks | Mono ~14px, bg=card | Existing | Confirm + adjust | V-S6 |
| Pre-token indicator | Animated dot + "Thinking… Ns" | Streaming dots + reasoning accordion | Add pre-token component | S-S1 |
| Smooth-stream cadence | ~30-50 cps uniform | Y-S3 word-aware (no rate target) | Add rate-target | S-S2 |
| Ext-thinking collapse | Auto-collapse on first text_delta | Auto-collapse on >2000 tokens only | Add stage-transition heuristic | S-S3 |
| Inline tool cards | Labeled icon+verb cards mid-stream | `data-tool` parts emitted but minimal render | New component | S-S4 |
| Stop button | Send morphs to stop; partial retained | R6.5 shipped morph | Verify partial-turn DB persistence | S-S5 |
| Prompt layout | tools → system → messages | Current order unknown | Audit + align | O-S1 |
| Prompt caching | 4 `cache_control` breakpoints | Unknown | Add canonical layout | O-S2 |
| Tool-use loop | `stop_reason: tool_use` while-loop | Single-shot or partial | Add agentic loop | O-S3 |
| Citations | Inline-clickable, no side panel | Footnote `[^N]` + side panel + freshness | Full Claude pivot; retire panel | O-S4 |
| Adaptive thinking | `thinking.effort` on Opus 4.6+ | `thinking.budget_tokens` if any | Param swap | O-S5 |

## Sessions Table (Execution Order)

| # | Session ID | Brief | Flag | Default | Client-side | Risk |
|---|-----------|-------|------|---------|-------------|------|
| 0 | **V-S0** | **runtime-user-toggle** | MARSYS_FLAG_R11_CLAUDE_RENDERING | **false** | yes (NEXT_PUBLIC) | low |
| 1 | V-S1 | claude-typography-stack | MARSYS_FLAG_R11_CLAUDE_RENDERING (via useClaudeRendering hook) | **false** | yes (NEXT_PUBLIC) | medium |
| 2 | V-S2 | user-bubble-dimensions | MARSYS_FLAG_R11_CLAUDE_RENDERING (same) | **false** | yes (NEXT_PUBLIC) | low |
| 3 | V-S3 | message-container-shape | MARSYS_FLAG_R11_CLAUDE_RENDERING (same) | **false** | yes (NEXT_PUBLIC) | medium |
| 4 | V-S4 | composer-chrome | MARSYS_FLAG_R11_CLAUDE_RENDERING (same) | **false** | yes (NEXT_PUBLIC) | low |
| 5 | V-S5 | sidebar-chrome | MARSYS_FLAG_R11_CLAUDE_RENDERING (same) | **false** | yes (NEXT_PUBLIC) | low |
| 6 | V-S6 | markdown-content-typescale | MARSYS_FLAG_R11_CLAUDE_RENDERING (same) | **false** | yes (NEXT_PUBLIC) | low |
| 7 | S-S1 | pre-token-thinking-indicator | FLAGLESS | — | yes | low |
| 8 | S-S2 | smooth-stream-v3-rate-target | MARSYS_FLAG_R11_SMOOTH_STREAM_V3 | true | no (server-side) | medium |
| 9 | S-S3 | extended-thinking-auto-collapse | FLAGLESS | — | yes | low |
| 10 | S-S4 | inline-tool-cards | MARSYS_FLAG_R11_TOOL_CARDS | true | yes (NEXT_PUBLIC) | medium |
| 11 | S-S5 | stop-and-retain-partial | FLAGLESS | — | yes | low |
| 12 | O-S1 | system-prompt-layout-audit | MARSYS_FLAG_R11_PROMPT_LAYOUT_V2 | **false** | no (server-side) | medium |
| 13 | O-S2 | prompt-cache-breakpoints | MARSYS_FLAG_R11_PROMPT_CACHE_V2 | **false** | no (server-side) | HIGH (cost+latency) |
| 14 | O-S3 | agentic-tool-loop | MARSYS_FLAG_R11_AGENTIC_TOOL_LOOP | **false** | no (server-side) | HIGH (behavior) |
| 15 | O-S4 | inline-citation-parity + retire side panel | MARSYS_FLAG_R11_INLINE_CITATIONS | **false** | yes (NEXT_PUBLIC) | medium |
| 16 | O-S5 | adaptive-thinking-effort | FLAGLESS | — | no (server-side) | low |
| 17 | **R11-MERGE** | auto-pr-merge | — | — | — | terminal |

V-S1 through V-S6 share **one flag** so visual parity ships atomically.
R11-MERGE has `requires_human_approval: false` — explicit native override of
Wave 1 Conductor invariant per `NATIVE_RULINGS §6`.

## Flag Classification

### FLAGLESS sessions
- S-S1 (pre-token indicator), S-S3 (auto-collapse), S-S5 (verification), O-S5 (param swap), R11-MERGE (shell only).

### FLAGGED sessions
- V-S1..V-S6: `MARSYS_FLAG_R11_CLAUDE_RENDERING` (single shared flag, default false, NEXT_PUBLIC + deploy.yml build-arg).
- S-S2: `MARSYS_FLAG_R11_SMOOTH_STREAM_V3` (default true, server-side).
- S-S4: `MARSYS_FLAG_R11_TOOL_CARDS` (default true, NEXT_PUBLIC + deploy.yml build-arg).
- O-S1: `MARSYS_FLAG_R11_PROMPT_LAYOUT_V2` (default false, server-side).
- O-S2: `MARSYS_FLAG_R11_PROMPT_CACHE_V2` (default false, server-side; verify hit rate in shadow before flipping default).
- O-S3: `MARSYS_FLAG_R11_AGENTIC_TOOL_LOOP` (default false, server-side; HIGH risk).
- O-S4: `MARSYS_FLAG_R11_INLINE_CITATIONS` (default false, NEXT_PUBLIC + deploy.yml build-arg).

## Amendment Compliance Checklist

R11 inherits all five R10 governing amendments + adds R11-specific Amendment 4.

### Amendment 1 — NEXT_PUBLIC Build-Arg Discipline (HARD GATE)
Every brief with a client-side flag has an AC: "Add flag to deploy.yml --build-arg". Coverage check at R11-MERGE.

### Amendment 2 — Mount-Verification + Parent-Context Integration Test (HARD GATE)
Every visible-component brief has: (a) click-path documented, (b) parent-context integration test asserting the feature renders through the real prop/context chain.

### Amendment 3 — §M.16 Flagless Precedent for Additive Polish
Every session classified as FLAGLESS or FLAGGED explicitly. No purely-additive session carries an unnecessary flag.

### Amendment 4 — Preserved Prompt Blocks (R11-specific)
O-S1 MUST preserve verbatim: (a) R7-S2 footnote citation instruction block (note: this block is being RETIRED in O-S4, but until O-S4 runs, O-S1 preserves it intact); (b) Y-S4 `### Step: <label>` step-marker instructions.

Crossover note: O-S1 runs BEFORE O-S4 in the queue. The R7-S2 footnote block stays intact through O-S1's layout audit and is removed cleanly by O-S4 along with the rest of the footnote system.

### Amendment 5 — Per-Stream deploy.yml Coverage Gate (HARD, at R11-MERGE)
```bash
SOURCE_FLAGS=$(grep -rn "NEXT_PUBLIC_MARSYS_FLAG_R11" platform/src --include="*.ts*" -o | awk -F: '{print $NF}' | sort -u)
YML_FLAGS=$(grep -oE "NEXT_PUBLIC_MARSYS_FLAG_R11_[A-Z_]+" .github/workflows/deploy.yml | sort -u)
```
First set MUST be subset of second. R11-MERGE gate halts otherwise.

## Worktree + Branch

- Worktree path: `/Users/Dev/Vibe-Coding/Apps/MadhavR11`
- Branch: `chat-v2/round11-claude-parity`
- Base: main HEAD as of R11 setup time (per SETUP_WORKTREE.sh)
- Lifecycle: created at R11 open, retired after R11-MERGE auto-merges.

## Conductor

R11 runs via a dedicated Conductor instance:

- Conductor prompt: `00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_PROMPT_R11_v1_0.md`
- Queue: `00_ARCHITECTURE/CONDUCTOR/session_queue_R11.yaml`
- Shared logs: `CONDUCTOR_LOG.md` + `CONDUCTOR_HALT_LOG.md` (R11 entries prefixed `R11 — `).
- Kickoff: `00_ARCHITECTURE/chat_v2_briefs/round11/CLAUDE_CODE_KICKOFF_PROMPT.md` — paste into a fresh Claude Code session pointed at `/Users/Dev/Vibe-Coding/Apps/MadhavR11`.

Sub-agents run with `--dangerously-skip-permissions`. STRICT halt on first gate
failure; Conductor pings Cowork chat. Native types `RESUME <id>` / `SKIP <id>`
/ `ABANDON` to unblock.

## Merge Train Position

R11-MERGE pushes branch + opens PR + enables auto-merge after all 16
implementation sessions PASS and the Amendment 5 coverage gate passes.

**Parallel-workstream caveat:** Two other projects are running in parallel
worktrees as of 2026-05-21. R11's `must_not_touch` declarations protect against
file collisions, but if a parallel project lands on main before R11 does, R11-MERGE
may need to rebase. The auto-merge runs `gh pr merge --auto --squash`; if rebase
is required, the auto-merge waits.

## Rollback Plan

| Scope | Mechanism |
|-------|-----------|
| `MARSYS_FLAG_R11_CLAUDE_RENDERING` | Client-side: rebuild + deploy with flag=false in deploy.yml --build-arg |
| Other client-side flagged sessions (S-S4, O-S4) | Same as above |
| Server-side flagged sessions (S-S2, O-S1, O-S2, O-S3) | Flip Cloud Run runtime env to `false` |
| Default-false sessions | Not active in prod until flag enabled; no rollback needed |
| Flagless sessions (S-S1, S-S3, S-S5, O-S5) | `git revert <commit>` on main, deploy |
| Full R11 rollback | `git revert -m 1 <merge-commit>` of the R11 PR merge |

## Acceptance — R11 close

R11 is complete when:
1. All 16 implementation sessions have `status: passed` in `session_queue_R11.yaml`.
2. Amendment 5 deploy.yml coverage gate passes.
3. R11-MERGE entry passes — PR opened, auto-merge enabled (or completed).
4. `STREAM_R11_COMPLETE.md` authored at `00_ARCHITECTURE/chat_v2_briefs/round11/` summarizing each session close + merge commit SHA when available.
5. The native, in a follow-up Cowork session, amends `CLAUDE.md §E` to declare R11 COMPLETE.

---

*End of R11_MASTER_PLAN_v1_0.md (v1.1, amended 2026-05-21 — Open Items closed; native rulings encoded; flag renamed to MARSYS_FLAG_R11_CLAUDE_RENDERING; CitationSidePanel retirement folded into O-S4; R11-MERGE auto-merge entry added).*
