---
canonical_id: R11G_LIVE_ARC_PLAN
version: 1.0
status: CURRENT
authored: 2026-05-23
purpose: Complete plan for the autonomous R11.G arc — wire real MCP tool executor into runAgenticLoop's toolExecutor callback (closes the F-S3 stub gap), redesign the Multi-Provider Parity toggle UX + move it into a settings dropdown, activate NEXT_PUBLIC build flags so the toggle is visible in production. Default state stays Classic; users opt into Claude-style.
parent_arc: CHAT_V2_R11V2
prior_arc: R11.F (dispatch wiring) — COMPLETE
worktree: MadhavR11G
branch: feature/r11g-tool-executor-toggle
---

# R11.G — Tool Executor Wiring + Toggle Redesign + Flag Activation

## Locked decisions

| Decision | Choice |
|---|---|
| Default chat shell | Classic (user opts INTO Claude-style) |
| Toggle UX | Substantial redesign — move into settings dropdown + new visual + descriptive copy |
| Tool executor scope | All planner-available tools (full capability) |
| Halt rules | STRICT |
| Production rollout | Deploy code + flip NEXT_PUBLIC build flags during deploy; R11.E loop flags stay operator-controlled |
| Smoke auth | Pre-mint Firebase __session cookie, stash in .env.local |
| Worktree | MadhavR11G on `feature/r11g-tool-executor-toggle` |
| CI baseline | Diff against KNOWN_PRE_EXISTING_FAILURES, halt on NEW only |
| Brief author | Cowork (Session 0 — this conversation) |
| PR strategy | Single PR at end |
| Mirror discipline | Single update in final governance session |

## Total sessions: 1 brief + 7 autonomous = **8 sessions**

| # | Session | Where | Wall-clock |
|---|---|---|---|
| 0 | Brief authoring | Cowork (this conversation) | 45 min |
| 1 | Tool executor wiring (route.ts → agentic_loop callback) | Claude Code via Conductor | 60-90 min |
| 2 | Toggle redesign (Settings dropdown + new visual + copy) | Claude Code via Conductor | 60-90 min |
| 3 | Default-state behavior verification | Claude Code via Conductor | 30 min |
| 4 | Vitest stabilization + baseline diff | Claude Code via Conductor | 30-45 min |
| 5 | Server-side integration smoke (real tools via loop) | Claude Code via Conductor | 45-60 min |
| 6 | deploy.yml build-flag activation + PR + merge + deploy | Claude Code via Conductor | 30-45 min |
| 7 | Surface + governance close + mirrors | Claude Code via Conductor | 30 min |

**Total wall-clock: ~6-8 hours** autonomous. Operator follow-up = flip R11.E flags per existing R11.F rollout plan + open prod, optionally toggle Claude-style shell in your browser.

## What this arc delivers (in user-experience terms)

After R11.G ships and the operator runs the existing R11.E flag flips:

1. The agentic loop now ACTUALLY works — tool calls execute real tool dispatch and return real data. The "thinks-writes-thinks-writes-composes" behavior becomes real, not garbage-stub'd.
2. A polished Settings dropdown appears in the consume header. It contains the chat-experience toggle with clear labels: "Classic Marsys" (default) and "Claude-style chat". Each option has a one-sentence description.
3. Users browsing normally see Classic Marsys (no change for existing users).
4. You + any user who opens Settings → toggles "Claude-style chat" → sees the full R11.B chrome on next render.
5. Both experiences benefit from the live agentic loop + Anthropic cache + Gemini cache (when operator flips those flags).

## Session-by-session

### Session 0 — Brief authoring (Cowork)

I write `R11G_BRIEF_v1_0.md` (companion file in this bundle). Brief covers tool executor extraction, toggle redesign spec, default-state semantics, file scope per session, acceptance criteria, halt rules.

### Session 1 — Tool executor wiring

**Sub-agent task:**

1. Identify the existing MCP tool dispatch code in `route.ts` — the path the planner uses to execute `query_panchanga`, `query_dasha_periods`, `query_chart_facts`, etc.
2. Extract it as a reusable function `executeTool(toolCall: LoopToolCall): Promise<string>` that takes a tool name + parsed input and returns the result as a string suitable for feeding back to the LLM.
3. Replace the stub `toolExecutor` passed to `runAgenticLoop` in route.ts (5 places, one per provider) with the real function.
4. Handle errors gracefully — tool exec failure returns an error string the LLM can recover from, doesn't crash the loop.
5. Tests: extend `platform/tests/providers/agentic-loop-engine.test.ts` to cover real-tool-execution path with mocked MCP dispatch.

**Commit:** `feat(r11g): wire real MCP tool executor into runAgenticLoop callback`

### Session 2 — Toggle redesign

**Sub-agent task:**

1. Create new component `platform/src/components/consume/SettingsDropdown.tsx` — a gear icon + dropdown menu accessible from the consume header.
2. The dropdown contains a section labeled "Chat experience" with two radio options:
   - **Classic Marsys** (default) — "Familiar interface with full Marsys branding."
   - **Claude-style chat** — "Conversational interface inspired by Claude.ai. Bubble-less, reading-column layout."
3. Selection writes to `localStorage['marsys.chatShellMode']` and triggers a re-render (or prompts user to reload for clean state — TBD per implementation).
4. Replace the inline `MultiProviderParityToggle` mount at `ConsumeChatV2.tsx:1489` with the new SettingsDropdown mount.
5. Preserve all existing `useChatShellMode` hook semantics — the dropdown just changes how the choice is presented.
6. The dropdown can also host PanelModeToggle (consolidating the scattered toggles).
7. Tests: new component test + integration test verifying selection persists.

**Commit:** `feat(r11g): redesign chat shell toggle into Settings dropdown`

### Session 3 — Default-state behavior verification

**Sub-agent task:**

1. Verify `useChatShellMode` returns `'classic'` when `localStorage['marsys.chatShellMode']` is null/undefined.
2. Verify SSR-safe rendering — server returns 'classic' shell HTML; client hydrates without flash.
3. Verify a user who has NEVER touched the toggle continues to see Classic shell after R11.G deploys (no surprise change).
4. Verify a user who PREVIOUSLY set `'multi-provider'` (e.g. during your testing) continues to see Claude-style.
5. Tests: extend `platform/tests/lib/chat-v2/useMultiProviderParity.test.tsx` to cover null/undefined → classic.

**Commit:** `test(r11g): verify default-classic + SSR-safe chat shell behavior`

### Session 4 — Vitest stabilization

Same pattern as R11.F-S4. Run full suite, diff against `KNOWN_PRE_EXISTING_FAILURES.md`, halt on NEW failures only.

### Session 5 — Server-side integration smoke

**Sub-agent task:**

1. New tests under `platform/tests/e2e/r11g-server-smoke/`:
   - `tool-executor-loop.test.ts` — drives a 3-iteration loop with REAL tool dispatch mocked at the MCP layer. Asserts tool results flow back into the model's next iteration correctly.
   - `tool-error-recovery.test.ts` — middle-iteration tool error → loop recovers, doesn't abort.
   - `multi-tool-fan-out.test.ts` — single iteration with 2 simultaneous tool calls (model emits both in parallel). Both execute, both results feed back.
2. Per-provider smoke (anthropic, google, openai, deepseek, nvidia) — verify each provider's adapter loop integrates with the real tool executor.
3. Settings dropdown smoke — vitest + happy-dom render test, click the radio options, assert localStorage updates.

All must PASS. Halt on RED.

### Session 6 — deploy.yml build-flag activation + PR + merge + deploy

**Sub-agent task:**

1. Edit `.github/workflows/deploy.yml` — flip the two NEXT_PUBLIC build args from default-false to default-true:
   - `NEXT_PUBLIC_MARSYS_FLAG_R11V2_MULTI_PROVIDER_PARITY=${{ vars.NEXT_PUBLIC_MARSYS_FLAG_R11V2_MULTI_PROVIDER_PARITY || 'true' }}`
   - `NEXT_PUBLIC_MARSYS_FLAG_R11B_LOOK_AND_FEEL=${{ vars.NEXT_PUBLIC_MARSYS_FLAG_R11B_LOOK_AND_FEEL || 'true' }}`
   
   With this, the toggle is VISIBLE in production by default. Default localStorage state (null) still renders Classic shell, so existing users see no change. Users who click "Claude-style" in the Settings dropdown see R11.B chrome.

2. Commit: `chore(r11g): activate NEXT_PUBLIC parity build flags in deploy.yml`
3. `git push -u origin feature/r11g-tool-executor-toggle`
4. Open PR. Wait for CI. Baseline-diff failures.
5. `gh pr merge --squash --delete-branch --admin`. Watch Cloud Run deploy. Capture revision ID.

### Session 7 — Surface + governance close

Standard pattern:
1. Write `ROLLOUT_PHASE_R11G_RESULT.md` with all session results + revision ID.
2. Governance amendments to STREAM_R11V2_COMPLETE.md, CLAUDE.md §E, CURRENT_STATE_v1_0.md.
3. Mirror updates (.geminirules + .gemini/project_state.md).
4. Single commit on main: `docs(r11g): governance close — tool executor + toggle redesign + flag activation live`.
5. Final surface message to operator with R11.E flag flip reminders.

## Halt protocol

Same as R11.F: strict halt on first RED at any session. Conductor writes R11G_HALT_S<N>.md, marks queue entry failed, stops. No retry, no fix-forward.

## Pre-execution operator checklist (before kickoff)

1. Mint Firebase __session cookie (same as R11.F process).
2. Pick a chart UUID for the smoke.
3. The setup prompt walks you through worktree creation + .env.local hydration.
4. Open new Claude Code session at /Users/Dev/Vibe-Coding/Apps/MadhavR11G with `--dangerously-skip-permissions`. Paste kickoff prompt.

## Operator follow-up (after R11.G arc surfaces complete)

1. **Verify in production** — open prod /consume. Confirm Settings dropdown is visible in header. Click it. Confirm two-radio choice appears. Stay on Classic; refresh; confirm still Classic.
2. **Flip to Claude-style** — Settings → "Claude-style chat" → refresh. Confirm R11.B chrome activates (bubble-less, 768px column, serif, hover action bar).
3. **Flip back** — confirm reversible.
4. **Optional: kick off R11.E flag rollout** — per existing `ROLLOUT_PHASE_R11F_RESULT.md`. The tool executor is now real, so flipping R11E_*_LOOP flags will produce genuine multi-turn behavior.

## What R11.G does NOT do

- Does NOT remove the toggle / make Claude-style default (locked: keep opt-in).
- Does NOT touch R11.E loop flags (those stay operator-controlled — keep the R11.F rollout plan intact).
- Does NOT touch R11.D D.3 Gemini cache flag (operator decision).
- Does NOT change adapter dispatch — that's stable from R11.F.
- Does NOT touch MCPT, Phase 4C, or any unrelated workstream.

## File deliverables from this Cowork session

1. `R11G_LIVE_ARC_PLAN_v1_0.md` (this file)
2. `R11G_BRIEF_v1_0.md` (the brief Conductor reads)
3. `R11G_WORKTREE_SETUP_PROMPT.md` (paste-prompt #1)
4. `R11G_CONDUCTOR_KICKOFF_PROMPT.md` (paste-prompt #2)
5. `CONDUCTOR/CONDUCTOR_PROMPT_R11G_v1_0.md` (Conductor working prompt)
6. `CONDUCTOR/session_queue_R11G.yaml` (queue)

*End of R11G_LIVE_ARC_PLAN_v1_0.md*
