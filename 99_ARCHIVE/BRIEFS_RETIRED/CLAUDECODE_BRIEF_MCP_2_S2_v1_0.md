---
artifact: CLAUDECODE_BRIEF_MCP_2_S2_v1_0.md
type: CLAUDECODE_BRIEF
version: 1.0
status: PENDING
authored_by: Claude Code sub-agent (MCP-0-AUTHOR)
authored_at: 2026-05-21
session_id: MCP-2-S2
session_name: MCP-2-S2 — Tool descriptions (§4.6 standard) + MCP resources
executor: Claude Code sub-agent (general-purpose, spawned by MCP Conductor)
execution_mode: single autonomous session, --dangerously-skip-permissions
worktree:
  name: MadhavMCP
  branch: feature/mcp-server
  base: main
  path_absolute: /Users/Dev/Vibe-Coding/Apps/MadhavMCP
governing_plan: 00_ARCHITECTURE/BRIEFS/MCP_BRIEF_v1_0.md
reference_brief: 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCP_1_S1_v1_0.md
predecessor_session: MCP-2-S1 (MCP server scaffold)
next_session_anticipated: MCP-3-S1 (primitives + dispatcher)
---

# CLAUDECODE_BRIEF — MCP-2-S2
## Tool descriptions (§4.6 standard) + MCP resources (chart-overview + house-rules)

---

## §0 — How to start this session

You are a sub-agent spawned by the MCP Conductor. Your context is fresh.
You are in the MadhavMCP worktree at `/Users/Dev/Vibe-Coding/Apps/MadhavMCP`
on branch `feature/mcp-server`. The Conductor has already pasted your
session prompt; you are now reading this brief.

This session is the **content authoring half of Phase MCP-2**. The
engineering scaffold (`platform-mcp/` service, 3 tools with placeholder
descriptions) was completed in MCP-2-S1. Your job here is:
1. Elevate tool descriptions from placeholders to the §4.6 standard (≥120
   words, all 5 blocks, reviewed inline).
2. Draft the two MCP resources that Claude reads at session attach.
3. Wire the resources into the MCP server's resource protocol.

This session requires reading factual L1 data to draft `chart-overview.md`
and governance docs to draft `house-rules.md`. Those reads are read-only;
no L1 or governance files are modified.

---

## §1 — Session identity

| Field | Value |
|---|---|
| Session ID | MCP-2-S2 |
| Branch | `feature/mcp-server` |
| Worktree path | `/Users/Dev/Vibe-Coding/Apps/MadhavMCP` |
| Execution mode | Single autonomous session, `--dangerously-skip-permissions` |
| Predecessor | MCP-2-S1 (platform-mcp/ scaffold complete) |
| Anticipated next | MCP-3-S1 (10 surgical primitives + dispatcher) |

---

## §2 — Mandatory reads at session open (in order)

1. `CLAUDE.md` (§C mandatory list — full read)
2. `00_ARCHITECTURE/BRIEFS/MCP_BRIEF_v1_0.md` — **focus on §4.5 (MCP
   resources), §4.6 (tool description standard), §7.2 AC.2.5–AC.2.7** and
   the tool taxonomy §4.1 Tier 1 and Tier 2 (understand what each tool
   does before writing its description)
3. `platform-mcp/src/tools/ask_madhav.ts` — read the placeholder description
   and input schema; you will replace the description in-place
4. `platform-mcp/src/tools/plan_query.ts` — same
5. `platform-mcp/src/tools/execute_plan.ts` — same

For `chart-overview.md` content sourcing (read only — do not modify):
6. `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md` — birth data, lagna,
   planetary positions, karakas, dasha state; **authoritative L1 source**

For `house-rules.md` content sourcing (read only):
7. `CLAUDE.md` §A (project mission) and §J (quality standard)
8. `00_ARCHITECTURE/PROJECT_ARCHITECTURE_v2_2.md` §B (architectural principles
   B.1–B.12) — Jyotish school commitments, layer purity rules

---

## §3 — Scope (5 items — execute in order; commit after each)

### Item 1 — §4.6-standard descriptions for `ask_madhav`, `plan_query`, `execute_plan`

**What:** Update the description strings in the three tool files to meet
the §4.6 standard (MCP_BRIEF §4.6). Each description must contain all 5
blocks, ≥120 words:

**Block structure:**
1. **What it does** — 1-2 sentences, plain-language purpose
2. **When to prefer** — 1-2 sentences, differentiates from sibling tools
3. **Input shape hints** — 2-3 lines, param semantics beyond the JSON schema
4. **Output shape preview** — 1 line, what the response envelope looks like
5. **Inline example** — 1 realistic example with params + abbreviated response

**`ask_madhav` description target (~150 words):**
Runs the full MARSYS-JIS astrological pipeline end-to-end: planner
selects retrieval tools, tools execute in parallel, results are synthesized
against the 514-signal MSR corpus, and the answer is returned with citations,
trace ID, and epistemics. The Whole-Chart-Read discipline (B.11) is enforced
by default — at least one L2.5 synthesis tool always fires.

Prefer `ask_madhav` for any question requiring interpretation or synthesis.
Prefer `query_chart_facts` or `query_signals` when the question is a single
fact lookup and you want the raw value without synthesis overhead.

`query` — the question in plain English. `mode` — optional; defaults to
`auto` (planner chooses query_class). Use `holistic` to force B.11 holistic
read; `predictive` to trigger PPL logging. `context_hint` — optional
single-paragraph summary of prior conversation context.

Output: `{ok, answer_markdown, citations[], trace_id, plan, epistemics,
synthesis_audit, suggested_followups[]}`.

Example: `ask_madhav({query: "What does my 10th house say about career in
the current Saturn dasha?", mode: "auto"})` → `{ok: true, answer_markdown:
"...", citations: ["SIG.MSR.234", "SIG.MSR.512"], trace_id: "qry_...", ...}`.

**`plan_query` description target (~130 words):**
Returns the PipelinePlan JSON for a query without executing any retrieval
or synthesis. Use this to inspect which tools the planner would select,
what query class is assigned, and what budget tiers are proposed — before
committing to a full execution.

Prefer `plan_query` when doing differential analysis: call it, edit the
plan (swap tools, change mode, adjust priority), then pass the result to
`execute_plan`. Also prefer it when you want to understand why a prior
`ask_madhav` call chose certain tools — call `plan_query` with the same
query and compare.

`query` — the question string, same format as `ask_madhav`.

Output: `{ok, plan: {query_class, tool_calls[], audience_tier, mode,
...}, trace_id, epistemics}`. The `tool_calls` array lists tools the planner
would invoke with their priority and estimated token cost.

Example: `plan_query({query: "Predict career outcome for Q3 2026"})` →
`{ok: true, plan: {query_class: "predictive", tool_calls: [{tool: "msr_sql",
priority: 1}, {tool: "query_dasha_periods", priority: 2}], ...}}`.

**`execute_plan` description target (~140 words):**
Executes an explicit PipelinePlan object — typically the output of
`plan_query`, optionally edited. This enables the full differential-analysis
workflow: generate a plan, inspect it, modify tool selection or parameters,
then execute the modified plan and compare results to the original.

Prefer `execute_plan` when you want control over exactly which tools run
and in what priority order. The platform re-validates the plan against
PipelinePlanSchema before execution and re-checks audience-tier-permitted
tools — a client-tier caller cannot escalate privileges by editing the plan.
The B.11 Whole-Chart-Read floor is still enforced for holistic queries.

`plan` — a PipelinePlan object from `plan_query` output. Must be a valid
PipelinePlan; invalid plans return `{ok: false, error: {class: "validation",
...}}`.

Output: same envelope as `ask_madhav` — `{ok, answer_markdown, citations[],
trace_id, plan, synthesis_audit, suggested_followups[]}`.

Example: `execute_plan({plan: {...plan from plan_query, tool_calls: [
{tool: "msr_sql", priority: 1}, {tool: "cgm_graph_walk", priority: 1}]}})`.

**Implementation:** Open each of the three tool files from MCP-2-S1 and
replace the description string. Do not change the input schema, handler
code, or export function — description update only.

**AC.MCP_2_S2.1:** All 3 descriptions ≥120 words; all 5 blocks present
(verifiable by grep for "What it does", "When to prefer", "Input shape",
"Output shape", "Example"); gate command confirms presence in
`ask_madhav.ts`. `npx tsc --noEmit` still passes.

**Why:** Tool descriptions are load-bearing — Claude selects tools by
reading them every turn. Per MCP_BRIEF §4.6, generic one-liners produce
poor tool selection. The gate command (session_queue_MCP.yaml MCP-2-S2)
checks for "What it does" and "When to prefer" in `ask_madhav.ts`.

Commit: `docs(mcp): MCP-2-S2 item 1 — §4.6-standard descriptions for ask_madhav, plan_query, execute_plan`

---

### Item 2 — Draft `platform-mcp/resources/chart-overview.md`

**What:** Author `platform-mcp/resources/chart-overview.md` — a compact,
well-structured summary of Abhisek's chart. This is an MCP resource
(read once at session attach); it orients Claude to the singleton chart
so early turns don't burn tool calls on orientation queries.

**Minimum word count:** 500 words (gate: `wc -w < chart-overview.md` ≥ 500).
**Target:** 600–1000 words per MCP_BRIEF §4.5.1.

**Required sections (per MCP_BRIEF §4.5.1):**

1. **Birth data line** — date, time, place, ayanamsha. Source:
   FORENSIC L1 data.
2. **Lagna & key placements** — Lagna sign + lord; Atmakaraka;
   Amatyakaraka; Putrakaraka; Darakaraka. Source: FORENSIC.
3. **Planets-by-house** compact grid — table format, one row per planet,
   columns: Planet | House | Sign | Dignity. Source: FORENSIC.
4. **Active dasha state** — current Mahadasha (lord, start/end); current
   Antardasha (lord, start/end); current Pratyantar if determinable.
   Source: FORENSIC dasha data + current date 2026-05-21.
5. **Top 5 active L2.5 themes** — signal-domain summaries from MSR's
   highest-significance forward-looking entries. Source: FORENSIC +
   L2.5 MSR synthesis (use what you know from the brief; do not fabricate
   specific signal IDs — mark with `[SIGNAL_PLACEHOLDER — sub-agent to
   populate from MSR in MCP-2-S2 or native to update post-merge]` if you
   cannot read MSR).
6. **One-paragraph synthesis** — the "elevator pitch" of this chart as a
   whole. Acharya-grade prose per §J quality standard.

**Important:** Read `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md`
for authoritative birth data and planetary positions. Use only L1-grounded
facts. Mark any value you cannot find as `[EXTERNAL_COMPUTATION_REQUIRED]`
per B.10 — do not invent chart values. The native edits this file post-merge
for final polish; first-draft completeness is the goal.

**AC.MCP_2_S2.2:** File exists at `platform-mcp/resources/chart-overview.md`;
`wc -w` ≥ 500; all 6 required sections present; no fabricated numerical
values (any uncertain value is marked `[EXTERNAL_COMPUTATION_REQUIRED]`
or `[SIGNAL_PLACEHOLDER]`).

**Why:** MCP_BRIEF §4.5 — two resources together replace 5-10 tool calls
of orientation per session. `chart-overview.md` is the chart-facts surface.
The native can iterate content post-merge; the sub-agent provides the
structure and L1-grounded first draft.

Commit: `docs(mcp): MCP-2-S2 item 2 — platform-mcp/resources/chart-overview.md (first draft)`

---

### Item 3 — Draft `platform-mcp/resources/house-rules.md`

**What:** Author `platform-mcp/resources/house-rules.md` — the operating
manual Claude reads at session attach to behave at acharya-grade in the
MARSYS-JIS corpus.

**Minimum word count:** 300 words (gate: `wc -w` ≥ 300).
**Target:** 400–600 words per MCP_BRIEF §4.5.2.

**Required sections (per MCP_BRIEF §4.5.2):**

1. **School commitments** — Parashara primary; Jaimini for karakatva;
   KP for cuspal subtleties; Tajaka for varshaphala. Multi-school
   triangulation when invoked via `cross_school_lookup`.
2. **Terminology conventions** — "Atmakaraka" not "soul significator";
   "shadbala" not "six-fold strength" except on first use; cite signals
   by `SIG.MSR.NNN` ID, not by paraphrase; cite life events by `LEL.NNN`.
3. **Quality bars** — no generic astrology; no "as is known classically"
   without a signal ID or L1 source; predictions carry falsifier + horizon
   + confidence; do not collapse layer separation (facts vs. interpretations).
4. **Disclosure tier** — probabilistic and calibrated; not fortune-telling;
   the `epistemics` block in every response enforces this formally.
5. **When to defer to a tool** — if the question asks for a numerical
   value (planetary degree, dasha date boundary, panchang tithi), call the
   appropriate primitive tool — do not rely on training data for chart
   specifics. Example: for "what is Saturn's exact degree?", call
   `query_chart_facts(category: "dignity")`.
6. **When to escalate / flag** — if MSR signals contradict each other on
   the same domain, surface the contradiction explicitly; do not silently
   pick one. Use `flag_disagreement` if the contradiction is significant.
   If the question is about a different native, explain: MCP is
   singleton-chart (Abhisek only); direct them to the web UI for other
   charts (post-M10 only).

**AC.MCP_2_S2.3:** File exists at `platform-mcp/resources/house-rules.md`;
`wc -w` ≥ 300; all 6 required sections present.

**Why:** `house-rules.md` replaces the 5-10 turn "how does this instrument
work?" preamble that would otherwise consume Claude's context. The gate
command for AC.2.7 in the master brief (held-out test: ≥4/5 questions cite
house-rules conventions correctly) depends on this file being present and
substantive.

Commit: `docs(mcp): MCP-2-S2 item 3 — platform-mcp/resources/house-rules.md (first draft)`

---

### Item 4 — Resource registration (`platform-mcp/src/resources/index.ts`)

**What:** Author `platform-mcp/src/resources/index.ts` that registers
both markdown resources with the MCP server.

```typescript
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { join, dirname } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const RESOURCES_DIR = join(__dirname, '../../resources');

export function registerResources(server: McpServer): void {
  const chartOverview = readFileSync(
    join(RESOURCES_DIR, 'chart-overview.md'), 'utf-8'
  );
  const houseRules = readFileSync(
    join(RESOURCES_DIR, 'house-rules.md'), 'utf-8'
  );

  server.resource(
    'chart-overview',
    'marsys://chart-overview',
    async (_uri) => ({
      contents: [{
        uri: 'marsys://chart-overview',
        mimeType: 'text/markdown',
        text: chartOverview,
      }],
    })
  );

  server.resource(
    'house-rules',
    'marsys://house-rules',
    async (_uri) => ({
      contents: [{
        uri: 'marsys://house-rules',
        mimeType: 'text/markdown',
        text: houseRules,
      }],
    })
  );
}
```

Update `platform-mcp/src/server.ts` to call `registerResources(server)`
alongside the tool registrations. (This is the only MCP-2-S2 change to
`server.ts`; do not otherwise alter the server logic from MCP-2-S1.)

**AC.MCP_2_S2.4:** `platform-mcp/src/resources/index.ts` exports
`registerResources`; `server.ts` calls it; both resources serve valid
markdown content via the MCP resource protocol; `npx tsc --noEmit` passes.

**Why:** Resource registration is what makes Claude read the files at
session attach. Without this wiring, the resources are authored but never
delivered.

Commit: `feat(mcp): MCP-2-S2 item 4 — resource registration in platform-mcp/src/resources/index.ts`

---

### Item 5 — TypeScript gate

**What:** Run `cd platform-mcp && npx tsc --noEmit`. Fix any type errors
introduced by the resource registration wiring before marking complete.

Also confirm the gate command from `session_queue_MCP.yaml` MCP-2-S2
passes locally:
```bash
test -f platform-mcp/resources/chart-overview.md &&
test -f platform-mcp/resources/house-rules.md &&
[ $(wc -w < platform-mcp/resources/chart-overview.md) -ge 500 ] &&
[ $(wc -w < platform-mcp/resources/house-rules.md) -ge 300 ] &&
grep -q "What it does" platform-mcp/src/tools/ask_madhav.ts &&
grep -q "When to prefer" platform-mcp/src/tools/ask_madhav.ts &&
cd platform-mcp && npx tsc --noEmit
```

**AC.MCP_2_S2.5:** Full gate command exits 0.

**Why:** Closing check that all AC in this session are coherently satisfied
before handing off to MCP-3-S1.

Commit: `chore(mcp): MCP-2-S2 item 5 — tsc gate passes; resource word counts verified`

---

## §4 — Session-open handshake

You are a Conductor sub-agent. State briefly at start:

"MCP-2-S2 opening. Will author §4.6-standard descriptions for 3 Tier-1/2
tools, draft chart-overview.md (≥500 words from FORENSIC L1 data), draft
house-rules.md (≥300 words), and wire resource registration. 5 scope items.
Only platform-mcp/ files are modified — no platform/ changes in this session."

---

## §5 — Scope constraints

### may_touch

```
platform-mcp/resources/chart-overview.md                # CREATE
platform-mcp/resources/house-rules.md                   # CREATE
platform-mcp/src/resources/index.ts                     # CREATE
platform-mcp/src/server.ts                              # UPDATE — registerResources() call only
platform-mcp/src/tools/ask_madhav.ts                    # UPDATE — description string only
platform-mcp/src/tools/plan_query.ts                    # UPDATE — description string only
platform-mcp/src/tools/execute_plan.ts                  # UPDATE — description string only
01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md       # READ ONLY — content source for chart-overview
00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCP_2_S2_v1_0.md  # status flip PENDING → COMPLETE
```

### must_not_touch

```
platform/**                                              # zero platform changes in this session
platform-mcp/src/client.ts                              # do not alter client from MCP-2-S1
platform-mcp/src/types.ts                               # do not alter types from MCP-2-S1
platform-mcp/src/tools/ask_madhav.ts                    # BEHAVIOR unchanged — description string only
platform-mcp/src/tools/plan_query.ts                    # BEHAVIOR unchanged — description string only
platform-mcp/src/tools/execute_plan.ts                  # BEHAVIOR unchanged — description string only
platform-mcp/Dockerfile                                  # unchanged
platform-mcp/cloudbuild.yaml                             # unchanged
01_FACTS_LAYER/**                                        # read-only (content source)
025_HOLISTIC_SYNTHESIS/**                                # read-only
00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md                  # sealed
00_ARCHITECTURE/CAPABILITY_MANIFEST.json                # not touched in this session
CLAUDE.md                                               # §E update is post-workstream-close
```

### Commit cadence

Commit after each scope item with format:

```
<type>(mcp): MCP-2-S2 item <N> — <one-line summary>

<2-3 line description>
Acceptance criterion: AC.MCP_2_S2.<N>
```

---

## §6 — Session-close checklist (FINAL_SUMMARY)

After all 5 scope items are completed and the gate command passes, emit:

```
---FINAL_SUMMARY---
session_id: MCP-2-S2
status: PASS | HALT_NEEDS_HUMAN
commits:
  - <sha_item_1>
  - <sha_item_2>
  - <sha_item_3>
  - <sha_item_4>
  - <sha_item_5>
scope_items_completed:
  - AC.MCP_2_S2.1   # §4.6 descriptions for 3 tools
  - AC.MCP_2_S2.2   # chart-overview.md (≥500 words)
  - AC.MCP_2_S2.3   # house-rules.md (≥300 words)
  - AC.MCP_2_S2.4   # resource registration wired
  - AC.MCP_2_S2.5   # tsc gate passes
scope_items_failed: []
gate_command_runs:
  - name: mcp_2_s2_content_gate
    result: PASS | FAIL
notes_for_orchestrator: >
  Tool descriptions elevated to §4.6 standard. chart-overview.md and
  house-rules.md drafted from FORENSIC L1 data + governance docs. Resource
  registration wired into server.ts. Any signal IDs in chart-overview marked
  [SIGNAL_PLACEHOLDER] should be resolved by native post-merge or in a
  follow-up once MSR read access is confirmed. Next session: MCP-3-S1
  (10 surgical primitives + /api/mcp/primitives/[tool] dispatcher).
human_decision_needed: >
  <empty if PASS>
---END_FINAL_SUMMARY---
```

---

*End of CLAUDECODE_BRIEF_MCP_2_S2_v1_0.md.*
