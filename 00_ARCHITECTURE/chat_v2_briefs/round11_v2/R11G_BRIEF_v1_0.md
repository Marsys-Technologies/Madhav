---
canonical_id: R11G_BRIEF
version: 1.0
status: CURRENT
authored: 2026-05-23
purpose: Complete brief for R11.G — tool executor wiring + toggle redesign + NEXT_PUBLIC build flag activation. Ground truth for the autonomous Conductor arc.
parent_plan: R11G_LIVE_ARC_PLAN_v1_0.md
predecessor_arc: R11.F (dispatch wiring) — COMPLETE
---

# R11.G — Brief

## §1 — Scope statement

Three concerns delivered in one arc:

1. **Tool executor wiring.** Replace the stub `toolExecutor` callback in `runAgenticLoop` invocations (route.ts) with a real function that dispatches MCP tools and returns their results. Closes the F-S3 deliberate stub.
2. **Toggle redesign.** Replace the inline `MultiProviderParityToggle` with a polished Settings dropdown. Two clearly labeled radio options ("Classic Marsys" / "Claude-style chat") with descriptive copy.
3. **Build flag activation.** Flip the NEXT_PUBLIC build flags in deploy.yml from default-false to default-true, so the Settings dropdown's chat-shell radio is VISIBLE in production. Default localStorage state still renders Classic — no surprise change for existing users.

All R11.E loop flags + R11.D D.3 flag stay operator-controlled and out of arc scope. R11.G does NOT touch them.

## §2 — File scope

### may_touch

- `platform/src/app/api/consume/route.ts` — replace stub toolExecutor (5 provider gates)
- `platform/src/lib/synthesis/agentic_loop.ts` — only if tool executor signature needs extending (unlikely; current signature `(toolCall: LoopToolCall) => Promise<string>` is fine)
- `platform/src/components/consume/SettingsDropdown.tsx` — NEW
- `platform/src/components/consume/MultiProviderParityToggle.tsx` — may be deleted or kept as a sub-component of SettingsDropdown
- `platform/src/components/consume/ConsumeChatV2.tsx` — replace MultiProviderParityToggle mount with SettingsDropdown mount
- `platform/src/lib/chat-v2/useMultiProviderParity.ts` — likely no changes; verify default behavior is correct
- `platform/src/app/globals.css` — minor additions for SettingsDropdown styles if needed
- `.github/workflows/deploy.yml` — flip 2 NEXT_PUBLIC build args from `|| 'false'` to `|| 'true'`
- `platform/tests/**/r11g-*.test.*` — new test files
- `00_ARCHITECTURE/chat_v2_briefs/round11_v2/SESSION_R11G_S<N>_RESULT.md` files
- Governance docs at end-of-arc

### must_not_touch

- Any path under `00_ARCHITECTURE/CONDUCTOR/*MCPT*`
- `PROJECT_MEMORY_MCP_TRANSFORMATION_v1_0.md`
- `platform/src/lib/providers/dispatcher.ts` public API
- `platform/src/lib/providers/capabilities.ts`
- `platform/src/lib/providers/types.ts`
- `platform/src/lib/providers/<provider>/adapter.ts` (5 adapters — stable from R11.F)
- `platform/src/lib/config/feature_flags.ts` source flag union (no new flags this arc)
- Any migration file
- R11.E loop flag env_vars in deploy.yml — those stay operator-controlled
- R11.D D.3 Gemini cache flag — same
- Any UI other than the consume chat shell

## §3 — Tool executor wiring (Session 1)

### Goal

`runAgenticLoop` calls `toolExecutor(toolCall)` for every tool the model emits. Currently passed a stub that returns `"Tool not available in adapter dispatch"`. Replace with real dispatch.

### Implementation steps

1. Identify the existing planner tool-execution path in `route.ts`. The planner builds a fact bundle by calling tools like `query_panchanga`, `query_dasha_periods`, etc. Find that code.

2. Extract it as a reusable async function with this signature:

   ```ts
   async function executeMCPTool(
     toolCall: LoopToolCall,  // { id, name, input }
     ctx: {
       chartId: string
       userId: string
       audienceTier: AudienceTier
       // any other context needed for tool execution
     }
   ): Promise<string> {
     // Look up tool by name from the MCP tool registry
     // Validate input against tool's schema
     // Dispatch via the same path planner uses
     // Return result serialized as a string the LLM can consume (typically JSON)
     // On error: return string starting with "ERROR: " — loop should NOT abort, model should be able to react
   }
   ```

3. In `route.ts` dispatch block, wherever R11E_<PROVIDER>_LOOP gates an `adapter.chat` → `runAgenticLoop` swap, replace the stub toolExecutor with `(toolCall) => executeMCPTool(toolCall, { chartId, userId, audienceTier })`.

4. Both planner pre-fetch path AND agentic-loop tool-call path now share the same execution function.

### Acceptance (Session 1)

- AC.G1.1: `executeMCPTool` function exists, exported (or accessible) from a logical home in route.ts or `lib/synthesis/`.
- AC.G1.2: All 5 provider gates in route.ts pass the real executor to runAgenticLoop (no remaining "Tool not available in adapter dispatch" strings).
- AC.G1.3: `platform/tests/providers/agentic-loop-engine.test.ts` extended with test that uses real executeMCPTool with mocked MCP backend → loop produces real tool results.
- AC.G1.4: Tool execution failure (mocked) → loop continues with error string fed to LLM; loop does NOT throw.
- AC.G1.5: Vitest baseline diff = 0 NEW failures.

## §4 — Toggle redesign (Session 2)

### Goal

Replace the inline tiny toggle next to PanelModeToggle with a polished Settings dropdown — gear icon → menu → "Chat experience" section → two radio options.

### Component spec — SettingsDropdown.tsx

```tsx
// platform/src/components/consume/SettingsDropdown.tsx
'use client'

import { useState } from 'react'
import { Settings as SettingsIcon } from 'lucide-react'
import {
  useChatShellMode,
  PARITY_ENV_ENABLED,
} from '@/lib/chat-v2/useMultiProviderParity'

export function SettingsDropdown() {
  const [open, setOpen] = useState(false)
  const { mode, setMode } = useChatShellMode()

  // Hidden entirely when env-var kill-switch is false
  if (!PARITY_ENV_ENABLED) return null

  return (
    <div className="relative" data-testid="settings-dropdown">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        aria-label="Settings"
        aria-expanded={open}
        className="..."
      >
        <SettingsIcon size={18} />
      </button>

      {open && (
        <div
          role="menu"
          className="absolute right-0 mt-2 w-72 rounded-md border bg-popover p-3 shadow-md"
          data-testid="settings-dropdown-menu"
        >
          <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">
            Chat experience
          </div>

          <label className="flex items-start gap-2 cursor-pointer p-2 rounded hover:bg-accent">
            <input
              type="radio"
              name="chat-shell"
              checked={mode === 'classic'}
              onChange={() => setMode('classic')}
              data-testid="chat-shell-classic"
              className="mt-1"
            />
            <div>
              <div className="font-medium text-sm">Classic Marsys</div>
              <div className="text-xs text-muted-foreground">
                Familiar interface with full Marsys branding.
              </div>
            </div>
          </label>

          <label className="flex items-start gap-2 cursor-pointer p-2 rounded hover:bg-accent">
            <input
              type="radio"
              name="chat-shell"
              checked={mode === 'multi-provider'}
              onChange={() => setMode('multi-provider')}
              data-testid="chat-shell-claude-style"
              className="mt-1"
            />
            <div>
              <div className="font-medium text-sm">Claude-style chat</div>
              <div className="text-xs text-muted-foreground">
                Conversational interface inspired by Claude.ai. Bubble-less, 768px reading column, serif body.
              </div>
            </div>
          </label>

          <div className="text-[10px] text-muted-foreground mt-2 pt-2 border-t">
            Changing chat experience takes effect on next message.
          </div>
        </div>
      )}
    </div>
  )
}
```

### Mount site

In `ConsumeChatV2.tsx` around line 1489, replace:
```tsx
{/* A-S11: Multi-Provider Parity runtime toggle (hidden when env-var false) */}
<MultiProviderParityToggle />
```

With:
```tsx
{/* R11.G: Settings dropdown — replaces inline parity toggle */}
<SettingsDropdown />
```

Decide whether to keep `MultiProviderParityToggle.tsx` as a dead file (cleaner: delete it; gated by no remaining import). The brief recommends DELETING it — there's exactly one mount site, and the new SettingsDropdown encapsulates the same behavior.

### Acceptance (Session 2)

- AC.G2.1: `SettingsDropdown.tsx` exists at the specified path with the component shape above (data-testids present).
- AC.G2.2: `ConsumeChatV2.tsx` mounts `<SettingsDropdown />` in place of the old toggle.
- AC.G2.3: `MultiProviderParityToggle.tsx` deleted (no remaining imports verified by grep).
- AC.G2.4: Component test `platform/tests/components/consume/SettingsDropdown.test.tsx`:
  - Renders gear icon when PARITY_ENV_ENABLED=true
  - Renders nothing when PARITY_ENV_ENABLED=false
  - Click gear → menu opens
  - Click radio → localStorage updates
  - Outside click → menu closes (use React Testing Library + happy-dom)
- AC.G2.5: Vitest baseline diff = 0 NEW failures.

## §5 — Default-state behavior verification (Session 3)

### Goal

Ensure no surprise change for existing users. Default localStorage state → Classic shell.

### Acceptance (Session 3)

- AC.G3.1: `useChatShellMode` with `localStorage.getItem('marsys.chatShellMode') === null` returns `mode: 'classic'`.
- AC.G3.2: `useMultiProviderParity()` returns `false` when localStorage is null, regardless of env-flag state.
- AC.G3.3: SSR-safe — during server render, mode is 'classic'. No hydration mismatch test failures.
- AC.G3.4: New test in `platform/tests/lib/chat-v2/useMultiProviderParity.test.tsx` explicitly covers the null/undefined → classic case (probably already covered; verify + extend if not).
- AC.G3.5: A user with `localStorage['marsys.chatShellMode'] = 'multi-provider'` previously set (your testing localStorage) continues to see Claude-style — preservation of prior preference.

## §6 — Vitest stabilization (Session 4)

Standard. Run full suite, diff against `KNOWN_PRE_EXISTING_FAILURES.md`. Halt on NEW only.

## §7 — Server-side integration smoke (Session 5)

### Test files

New directory: `platform/tests/e2e/r11g-server-smoke/`

- `tool-executor-loop.test.ts`: 3-iteration loop with REAL `executeMCPTool` invocations (MCP backend mocked at the transport layer). Assertions:
  - Each iteration's tool result string flows back to the model's next iteration's `messages` array
  - Tool input JSON is correctly parsed before dispatch
  - Loop completes with final answer text after model emits `end_turn` / `stop`
- `tool-error-recovery.test.ts`: Middle iteration's tool returns `ERROR: <msg>` → loop continues; model receives error string and reacts; loop does NOT abort. AgenticLoopCapExceeded only thrown on iteration cap, not on tool error.
- `multi-tool-fan-out.test.ts`: Single iteration with 2 simultaneous tool calls. Both execute via `Promise.all`. Both results feed back.
- `settings-dropdown.test.tsx`: happy-dom render test. Click gear, click radio, assert localStorage. Click outside, assert menu closes.
- Per-provider sanity: re-use the existing `tests/providers/agentic-loop-engine.test.ts` plus extend for each provider to verify the executor integration works through the provider's actual termination signal.

### Acceptance (Session 5)

- AC.G5.1: All test files PASS.
- AC.G5.2: Server-side result MD records iteration counts + tool exec counts + error-recovery verification.

## §8 — deploy.yml build-flag activation + PR (Session 6)

### Diff to deploy.yml

```yaml
# In the build-args block, change these two lines:
            NEXT_PUBLIC_MARSYS_FLAG_R11V2_MULTI_PROVIDER_PARITY=${{ vars.NEXT_PUBLIC_MARSYS_FLAG_R11V2_MULTI_PROVIDER_PARITY || 'true' }}
            NEXT_PUBLIC_MARSYS_FLAG_R11B_LOOK_AND_FEEL=${{ vars.NEXT_PUBLIC_MARSYS_FLAG_R11B_LOOK_AND_FEEL || 'true' }}
```

(Was `|| 'false'`; flipped to `|| 'true'`.)

This means: unless an operator explicitly sets the GitHub repo var to 'false', the build bakes `true`. The toggle becomes visible in production.

Because the user-facing default is still Classic (localStorage null → classic), this is a safe flip — visibility change only, behavior unchanged for users who don't touch the dropdown.

### Acceptance (Session 6)

- AC.G6.1: deploy.yml has both lines updated.
- AC.G6.2: Branch pushed.
- AC.G6.3: PR opened with descriptive body.
- AC.G6.4: CI passes (or only baseline failures present).
- AC.G6.5: PR auto-merged via `gh pr merge --squash --delete-branch --admin`.
- AC.G6.6: Cloud Run deploy succeeds. Revision ID captured.

## §9 — Surface + governance close (Session 7)

Standard pattern. Write ROLLOUT_PHASE_R11G_RESULT.md. Apply governance amendments to STREAM_R11V2_COMPLETE.md, CLAUDE.md §E, CURRENT_STATE_v1_0.md, .geminirules, .gemini/project_state.md. Single commit on main. Final surface.

The surface message should remind the operator that:
- Tool executor is now real — flipping R11E_*_LOOP flags now produces genuine multi-turn behavior.
- Settings dropdown is visible in production. Default state is Classic; users opt into Claude-style.
- Existing R11.F rollout plan for R11.E flags is unchanged and ready to execute.

## §10 — Risks + mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| Extracting executeMCPTool from route.ts touches too much existing code | Medium | If the dispatch is deeply intertwined, factor minimally — keep the function close to its callsites; tests catch regressions |
| Settings dropdown displaces other header toggles awkwardly | Low | Component spec is clean; keep PanelModeToggle separate unless the redesign explicitly absorbs it |
| Flipping NEXT_PUBLIC default to true breaks build cache or surprise existing users | Low | Default localStorage state is Classic; rendered output unchanged for anyone who hasn't clicked |
| Tool execution timeout in loop (long-running tools) | Medium | Existing tool dispatch has its own timeout; loop inherits that. AgenticLoopCapExceeded provides the upper bound (8 iterations) |
| Click-outside-to-close on dropdown causes accessibility issue | Low | Use existing patterns from PanelModeToggle or shadcn DropdownMenu |
| Existing `MultiProviderParityToggle.tsx` deletion leaves dangling test references | Low | grep before delete; remove orphaned tests in same commit |

## §11 — Out of scope (explicit)

- Removing the toggle entirely / making Claude-style default for all users — locked: opt-in stays.
- Flipping R11.E loop flags in production — operator action, not autonomous.
- Flipping R11.D D.3 Gemini cache flag — same.
- Touching adapter code — stable from R11.F.
- Changes to dispatcher.ts, capabilities.ts, types.ts — those are R11.A substrate.
- Any non-consume UI work.
- MCPT touches.

*End of R11G_BRIEF_v1_0.md*
