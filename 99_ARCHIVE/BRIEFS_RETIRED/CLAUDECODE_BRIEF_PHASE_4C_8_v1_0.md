---
artifact: CLAUDECODE_BRIEF_PHASE_4C_8_v1_0.md
type: CLAUDECODE_BRIEF
version: 1.0
status: COMPLETE
authored_by: Cowork 2026-05-19
session_id: 4C-8
session_name: 4C-8 — Ask-Madhav prompt deep links + Panchang context injection
executor: Claude Code sub-agent (Conductor)
worktree:
  branch: feature/phase-4c-panchang
  path_absolute: /Users/Dev/Vibe-Coding/Apps/Panchang
predecessor: 4C-7
governing_plan: 00_ARCHITECTURE/PHASE_4C_PANCHANG_MASTER_PLAN_v1_0.md §4.4.3
---

# CLAUDECODE_BRIEF — Phase 4C-8
## Ask-Madhav prompt deep links with Panchang context block injection

Inline 💬 affordances throughout /panchang. Click any opens chat at `/clients/[id]/consume` with a pre-loaded prompt + hidden Panchang JSON context block. The planner sees the context and decides whether to re-query or rely on it.

---

## §0 — Pre-flight
```bash
cd /Users/Dev/Vibe-Coding/Apps/Panchang
test -f 00_ARCHITECTURE/PHASE_4C_7_CLOSE_v1_0.md  # 4C-7 closed
test -d platform/src/app/clients
# Verify consume page exists
ls platform/src/app/clients/[id]/consume/ 2>/dev/null
# Check existing chat-context injection pattern (search for how prompts are pre-loaded)
grep -rn "prompt.*=.*encodeURIComponent" platform/src/app/ | head -5
```

## §2 — Mandatory reads
1. `CLAUDE.md` §C
2. Master plan §4.4.3 (Ask-Madhav spec)
3. `platform/src/app/clients/[id]/consume/page.tsx` (chat entry — see how prompts pass in)
4. Pipeline planner: where it picks up context blocks from query input

## §3 — Scope (9 items)

### Item 1 — `AskMadhavLink` component
Create `platform/src/app/panchang/components/AskMadhavLink.tsx`. Reusable inline link with 💬 icon. Props:
- `prompt: string` — the visible user prompt
- `panchang_context?: object` — optional JSON to inject as hidden context
- `chart_id?: string` — passes through

Renders as a small icon-only button (`<i class="ti ti-message-circle">`). On click:
1. Encodes prompt + context as URL params
2. Opens `/clients/[chart_id]/consume?prompt=<encoded>&context=<encoded_json>` in a new tab (or current tab — match existing project pattern)

**AC.4C8.1:** Component renders + click opens chat with correct query params.

### Item 2 — Context block injection at chat entry
Update `platform/src/app/clients/[id]/consume/page.tsx` (or the chat init flow): if `context` query param present, parse as JSON and inject into the chat's first user message as a hidden block:

```
<panchang_context>
<!-- AUTO-INJECTED FROM /panchang ON YYYY-MM-DD AT LOCATION (lat, lon) -->
{...full panchang JSON...}
</panchang_context>

<user_question>
{the visible prompt}
</user_question>
```

The planner/synthesis prompts already handle wrapping conventions; the `<panchang_context>` block is new. Update the synthesis prompt to recognize and use it.

**AC.4C8.2:** Pre-loaded prompt arrives with hidden context block; chat renders the visible question; planner sees both.

### Item 3 — Synthesis prompt awareness
Update `platform/src/lib/synthesis/prompts.ts` (or wherever the synthesis prompt template lives) to acknowledge `<panchang_context>`:

```
If the user's message contains a <panchang_context> block, treat that as
authoritative L1.5 Panchang state for the date/location specified within.
Cite from this context using [PANCHANG:<field>] markers. You do NOT need
to call query_panchanga for this exchange unless the user asks about a
different date or location.
```

**AC.4C8.3:** Synthesis prompt updated; planner respects the embedded context (verify via probe).

### Item 4 — Planner context-recognition rule
Update `00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md` to add a rule: when query body includes `<panchang_context>`, prefer answering directly from that context instead of re-querying `query_panchanga` for the same date/location. Save tokens, faster response.

**AC.4C8.4:** Rule added; planner respects context inheritance.

### Item 5 — Wire AskMadhavLink throughout /panchang page

Sprinkle the 💬 button across UI elements per master plan §4.4.3 suggestions:

| Element | Prompt |
|---|---|
| Tithi row in `PrimaryStrip` | "What does <tithi_name> mean for me today?" |
| Active special yoga in `SpecialYogasList` | "Explain why today's <yoga_name> matters for major decisions." |
| Retrograde flag in `PlanetaryGrid` | "What's <planet> retrograde doing in my chart right now?" |
| Tara Bala badge in `PrimaryStrip` (when personalised) | "Is today a <tara_name> for me? What does that mean for planning?" |
| Muhurat result in `MuhuratResultsList` | "Walk me through why this date is ranked highest for <event>." |

Each link injects the day's full Panchang JSON as the `panchang_context`.

**AC.4C8.5:** 💬 affordances present on all 5 element types; click pre-loads chat with prompt + context.

### Item 6 — Context-budget guard
The full Panchang JSON is ~3-5 KB. With the synthesis prompt + history, that's small enough not to be a problem. But: if `panchang_context` field is over 10 KB (e.g., a range result instead of single day), truncate to essentials and add a note "(truncated; query_panchanga for full detail)".

**AC.4C8.6:** Size guard tested with a 30-day range injected as context.

### Item 7 — UX polish
- 💬 buttons styled as small ghost-style icons (no heavy visual weight; don't compete with primary content)
- Hover tooltip preview of the prompt that will be sent
- Optional: a settings toggle "Always inject Panchang context when using Ask Madhav" — defaults on, can be disabled by power users who want fresh queries

**AC.4C8.7:** Visual review confirms unobtrusive UX.

### Item 8 — E2E test + planner probe
- E2E: click 💬 on Tithi row → chat opens → message sent → planner does NOT call query_panchanga (context is sufficient) → synthesis answers using injected data
- Planner probe: query "What's today's tithi?" WITH context block → planner emits 0 tool_calls (relies on context). WITHOUT context block → planner emits query_panchanga.

**AC.4C8.8:** E2E + probes PASS.

### Item 9 — Close
CURRENT_STATE: 4C.8 CLOSED; SESSION_LOG; brief flip; FINAL_SUMMARY; queue advance to 4C-9.

**AC.4C8.9:** Done.

---

## §5 — Constraints
**may_touch:** `platform/src/app/panchang/components/AskMadhavLink.tsx` (new); /panchang component wiring (PrimaryStrip, SpecialYogasList, PlanetaryGrid, MuhuratResultsList — embed the link); `platform/src/app/clients/[id]/consume/page.tsx` (context block injection); `platform/src/lib/synthesis/prompts.ts` (synthesis prompt update); `00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md` (planner rule update); tests; governance state files; this brief.
**must_not_touch:** sidecar; engine; retrieve/; muhurat backend; iCal code from 4C-7; corpus; master plan.

## §6 — Close checklist
- [ ] 9 ACs PASS
- [ ] Synthesis prompt update tested via probe
- [ ] Planner rule update verified
- [ ] E2E test PASS
- [ ] Context budget guard tested
- [ ] FINAL_SUMMARY emitted

## §7 — LLM stack
Gemini primary; Anthropic BANNED.

## §8 — Context carried
- Master plan §4.4.3 fully specifies the deep-link UX
- Context block injection is a new pattern in the chat flow; document carefully so future features (e.g., FORENSIC context injection) can follow the pattern

## §9 — Canary
The "context-aware planner skip" probe. If planner still calls query_panchanga even when context is provided, the rule update didn't land — performance suffers (extra tool call per chat turn). Halt and fix the rule.

*End — 4C-8.*
