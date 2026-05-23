---
artifact: ROLLOUT_PHASE_R11G_RESULT.md
arc: R11.G
status: COMPLETE
authored: 2026-05-23
authored_by: G-S7 (autonomous arc governance close)
purpose: >
  Rollout result record for R11.G — tool executor wiring, SettingsDropdown, and
  NEXT_PUBLIC parity flag activation. Counterpart to ROLLOUT_PHASE_R11F_RESULT.md.
---

# R11.G — Rollout Result

## §1 — Arc summary

| Field | Value |
|---|---|
| Arc | R11.G (tool executor + toggle redesign + flag activation) |
| Branch | feature/r11g-tool-executor-toggle |
| PR | #152 |
| Merge SHA | 52e18cb5 |
| Cloud Run revision | amjis-web-00367-b59 |
| Sessions | 7 (G-S1 through G-S6 + G-S7 governance) |
| Completed | 2026-05-23 |

## §2 — Session result paths

| Session | Commit SHA | Description |
|---|---|---|
| G-S1 | ba4796bb | Real MCP tool executor wired (mcp_tool_executor.ts + route.ts integration + tests) |
| G-S2 | 6e9e9dbb | SettingsDropdown component + ConsumeChatV2 mount + MultiProviderParityToggle deleted |
| G-S3 | 17e25fc3 | Default-classic behavior tests |
| G-S4 | 64d41c4e | Vitest baseline diff PASS (0 new failures; KNOWN_PRE_EXISTING_FAILURES v1.3) |
| G-S5 | 49b7c3aa | Server-side integration smoke 13/13 PASS |
| G-S6 | PR #152, merge SHA 52e18cb5 | Cloud Run revision amjis-web-00367-b59 |
| G-S7 | (governance close) | STREAM_R11V2_COMPLETE.md §8 + CLAUDE.md v4.0 + CURRENT_STATE v5.53 |

## §3 — Deliverables

### 3.1 — Tool executor wiring

`mcp_tool_executor.ts` implements real MCP dispatch to the MARSYS retrieval tool registry. All 5 provider gates in `route.ts` pass `executeMCPTool` to `runAgenticLoop`, replacing the stub null executor from R11.F. Tool errors return `"ERROR: <msg>"` strings; the loop does not abort on tool errors — it continues iterating with the error string as the tool result.

### 3.2 — Settings dropdown

`SettingsDropdown.tsx`: gear icon in the ConsumeChat header renders a dropdown with a "Chat experience" section. Two clearly labeled radio options:
- **"Classic Marsys"** (default) — original ConsumeChat shell; no R11.B chrome active.
- **"Claude-style chat"** — activates R11.B look-and-feel (bubble-less assistant messages, 768px reading column, serif/sans/mono typography stack).

`MultiProviderParityToggle.tsx` deleted (0 callers remain after ConsumeChatV2 mount updated).

### 3.3 — NEXT_PUBLIC flag activation

`deploy.yml` build-args updated:
- `NEXT_PUBLIC_MARSYS_FLAG_R11V2_MULTI_PROVIDER_PARITY` → default `true`
- `NEXT_PUBLIC_MARSYS_FLAG_R11B_LOOK_AND_FEEL` → default `true`

Settings dropdown is now VISIBLE in production. Default `localStorage` state (null) → Classic shell; existing users see no surprise change.

## §4 — Test results

| Suite | Count | Result |
|---|---|---|
| agentic-loop-engine.test.ts | 5 new tests | PASS |
| SettingsDropdown.test.tsx | 12 tests | PASS |
| useMultiProviderParity.test.tsx | 7 new tests | PASS |
| r11g-server-smoke/ | 13 tests | PASS |
| **New tests total** | **37** | **PASS** |
| Pre-existing failures baseline | 18 | KNOWN_PRE_EXISTING_FAILURES.md v1.3 |
| R11.G regressions | 0 | PASS |

## §5 — Production verification steps

Open production `/consume`, then:

1. **Settings dropdown visible**: Click gear icon (⚙) in the chat header. Confirm the dropdown renders with a "Chat experience" section containing two radio options.
2. **Default state**: Confirm "Classic Marsys" radio is selected by default (first visit / cleared localStorage).
3. **Toggle test**: Click "Claude-style chat" → refresh → confirm R11.B chrome activates (bubble-less assistant messages, 768px reading column, serif typography). Click "Classic Marsys" → refresh → confirm original shell restores.
4. **Tool executor**: Submit a query that triggers an agentic tool call. Confirm tool results appear inline (not empty strings). Check Cloud Run logs for `executeMCPTool` dispatch entries.

## §6 — Flag state after R11.G

| Flag | Type | Value | Live since |
|---|---|---|---|
| `MARSYS_FLAG_R11V2_USE_ADAPTERS` | server-side | `true` | rev 356 (deploy.yml) |
| `MARSYS_FLAG_R11D_PROMPT_LAYOUT` | server-side | `true` | rev 356 (deploy.yml) |
| `MARSYS_FLAG_R11D_ANTHROPIC_CACHE` | server-side | `true` | rev 356 (deploy.yml) |
| `NEXT_PUBLIC_MARSYS_FLAG_R11V2_MULTI_PROVIDER_PARITY` | NEXT_PUBLIC | `true` | rev amjis-web-00367-b59 (deploy.yml) |
| `NEXT_PUBLIC_MARSYS_FLAG_R11B_LOOK_AND_FEEL` | NEXT_PUBLIC | `true` | rev amjis-web-00367-b59 (deploy.yml) |
| `MARSYS_FLAG_R11D_GEMINI_CACHE` | server-side | `false` | rolled back rev 357 |
| `MARSYS_FLAG_R11E_*_LOOP` (×4) | server-side | operator-controlled | see ROLLOUT_PHASE_R11F_RESULT.md |

## §7 — Operator follow-up

1. **Verify Settings dropdown in production** per §5 above.
2. **R11.E loop flags**: Flip individually per `ROLLOUT_PHASE_R11F_RESULT.md` (E.1 first, then E.2–E.4 in 15-min windows). All E flags are now wired to real `agentic_loop.ts` engine with real `executeMCPTool` dispatch (R11.G close-out).
3. **Persist E flags in deploy.yml** after each verified flip (same pattern as D.1/D.2 in commit `fbe8ff32`).

---

*ROLLOUT_PHASE_R11G_RESULT.md — authored 2026-05-23 by G-S7 governance close session.*
