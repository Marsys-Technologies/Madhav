---
artifact: OPUS_PLANNING_SESSION_v2_0.md
version: 2.0
status: ACTIVE
supersedes: OPUS_PLANNING_SESSION_v1_0.md
authored_by: Claude Sonnet 4.6 (Cowork) — 2026-05-12
purpose: >
  Master planning document for all pre-M5 gates. Contains:
  (1) full project context for Opus 4.7 design conversations,
  (2) verbatim context prompts for each gate conversation,
  (3) worktree setup commands,
  (4) gate naming conventions,
  (5) CLAUDECODE_BRIEF format,
  (6) return protocol for this macro plan conversation,
  (7) Gate IV definition and checklist.
changelog:
  - v2.0 (2026-05-12): Major expansion. Added gate naming, three verbatim
    context prompts, worktree setup commands (bash + Claude Code), Gate IV
    "M5 Launchpad" definition with full acceptance checklist, two-return
    protocol for the macro plan conversation, parallelization map update,
    scope constraints (must_not_touch lists) per gate. Supersedes v1.0.
  - v1.0 (2026-05-12): Initial version — project context, gate definitions,
    CLAUDECODE_BRIEF format, parallelization map.
---

# MARSYS-JIS — Pre-M5 Gates Master Plan v2.0

---

## §1 — The Four Gates at a Glance

| Gate | Name | Worktree | Conversation Name | Mode |
|---|---|---|---|---|
| Gate I | Performance Command Center | `marsys-gate1-perf-center` | MARSYS Gate I — Performance Command Center | Parallel |
| Gate II | Trace Pipeline Alignment | `marsys-gate2-trace-align` | MARSYS Gate II — Trace Pipeline Alignment | Parallel |
| Gate III | Intelligent Chat Interface | `marsys-gate3-smart-chat` | MARSYS Gate III — Intelligent Chat Interface | Parallel |
| Gate IV | M5 Launchpad | *(no worktree — runs on main)* | *(this conversation)* | Sequential — after I+II+III close |

Gates I, II, III run in parallel. Gate IV runs after all three close, handled
in the macro plan conversation (this conversation). After Gate IV closes,
M5 opens — also in this conversation.

---

## §2 — Full Flow

```
[This conversation — macro plan]
  Produces this document. Done for now.

─────────────────────────────────────────────────────────────────────
PHASE: PARALLEL GATE EXECUTION
─────────────────────────────────────────────────────────────────────

[Worktree setup — run once before starting conversations]
  bash: create marsys-gate1-perf-center, marsys-gate2-trace-align,
        marsys-gate3-smart-chat  (see §4 for exact commands)

[3 × Cowork conversations — Opus 4.7 — run simultaneously]
  MARSYS Gate I  → design + CLAUDECODE_BRIEF → executor runs in gate1 worktree
  MARSYS Gate II → design + CLAUDECODE_BRIEF → executor runs in gate2 worktree
  MARSYS Gate III→ design + CLAUDECODE_BRIEF → executor runs in gate3 worktree

[3 × Claude Code sessions — Sonnet 4.6 — Antigravity, dangerously-skip-permissions]
  Gate I executor  → marsys-gate1-perf-center/
  Gate II executor → marsys-gate2-trace-align/    ← all three simultaneous
  Gate III executor→ marsys-gate3-smart-chat/

─────────────────────────────────────────────────────────────────────
RETURN 1 — back to this conversation after all three executor sessions close
─────────────────────────────────────────────────────────────────────

[This conversation]
  Step 1: Gate check — verify I + II + III all closed (see §8)
  Step 2: Execute 3-step merge + nav cleanup (see §6)
  Step 3: Author Gate IV brief (no Opus needed — see §7)
  Step 4: User triggers Gate IV Claude Code executor on main

─────────────────────────────────────────────────────────────────────
RETURN 2 — back to this conversation after Gate IV executor closes
─────────────────────────────────────────────────────────────────────

[This conversation]
  Step 1: Confirm Gate IV acceptance criteria all pass
  Step 2: Declare all pre-M5 gates cleared
  Step 3: Author PHASE_M5_PLAN_v1_0.md → M5 opens
```

---

## §3 — Project Context (for all Opus conversations)

### 3.1 What MARSYS-JIS Is

An LLM-operated Jyotish (Vedic astrology) instrument for Abhisek Mohanty
(b. 1984-02-05, 10:43 IST, Bhubaneswar). The system reads his chart at
acharya-grade depth, surfaces patterns across layers that no individual
astrologer could hold in working memory, and makes time-indexed probabilistic
predictions testable against lived reality.

### 3.2 Macro-Phase Status

| Phase | Name | Status |
|---|---|---|
| M1 | Corpus Completeness | CLOSED 2026-04-19 |
| M2 | Corpus Activation | CLOSED 2026-04-28 |
| M3 | Temporal Animation | CLOSED 2026-05-01 |
| M4 | Empirical Calibration | CLOSED 2026-05-02 |
| **M5** | **Probabilistic Model** | **INCOMING — next** |
| M6–M10 | (future phases) | Future |

### 3.3 Tech Stack

- **Framework:** Next.js (App Router, TypeScript)
- **Database:** Cloud SQL (Postgres + pgvector)
- **Storage:** GCS — layer-prefix layout (`L1/`, `L2_5/`, `L3/`)
- **Auth:** Firebase Auth
- **Hosting:** Cloud Run
- **Default LLM:** Gemini (2.5 Pro for critical; flash variants for non-critical)
- **Fallback LLM:** DeepSeek
- **BANNED LLM:** Anthropic/Claude for application logic — flag immediately if seen
- **Testing:** Vitest
- **Styling:** Tailwind CSS + shadcn/ui

### 3.4 Portal Route Map

**Consume (client-facing query interface):**
- `/clients/[id]/consume` — main consume page
- `/clients/[id]/consume/[conversationId]` — conversation detail
- `components/consume/` — ConsumeChat, AnswerView, StreamingAnswer,
  TraceDrawer (thin shell → TracePanel), LogPredictionAction, TierPicker, etc.

**Trace (rich trace system):**
- `components/trace/` — TracePanel.tsx (v2.0, 63KB), PipelineLifecycleView,
  LifecycleGraph, StepDetail variants (Plan, Fetch, Synthesis, Classify,
  ContextAssembly), HealthRail, QueryDNAPanel, RetrievalScorecard, etc.
- `/api/admin/trace/[query_id]` — trace data endpoint
- `/api/trace/stream/[queryId]` — SSE live trace stream
- `lib/admin/trace_assembler.ts` — assembles trace from DB steps
- `lib/admin/trace_client.ts` — client-side trace API

**Audit:**
- `/audit`, `/audit/[query_id]`, `/audit/compare`, `/audit/predictions`

**Observatory (super-admin):**
- `/observatory` — LLM cost/usage; full analytics suite

**Cockpit:**
- `/cockpit` — build-phase governance dashboard

**Admin:**
- `/admin` — user management

**Shared nav** (DO NOT TOUCH in any gate executor):
- `components/shared/AppShellRail.tsx` — NAV_ITEMS array (desktop)
- `components/shared/MobileNavSheet.tsx` — NAV_ITEMS array (mobile)
- Nav update happens as a single cleanup commit after all three gates merge

### 3.5 The Query Pipeline (New — Only Pipeline)

Stages in order:
1. **Planner** — classifies query into 1 of 7 classes; produces QueryPlan
   (plan_type: factual / interpretive / predictive / discovery / holistic)
2. **Retrieval** — hybrid: vector_search + cgm_graph_walk + structured_sql + hybrid_rank
3. **Synthesis** — Gemini; single-model or panel mode; produces answer + citations
4. **Audit** — logs everything; validator verdict; disclosure tier
5. **Checkpoints** — optional quality gates at 4.5, 5.5, 8.5

Legacy/hybrid pipeline deleted Phase 11B (2026-05-11). No flag exists.
PLANNER_PROMPT v2.1 — recall=0.983, precision=0.961, 46 golden queries.

### 3.6 What Exists vs What's Missing

| Item | Status |
|---|---|
| New query pipeline | LIVE |
| Audit view (/audit) | LIVE |
| Observatory (/observatory) | LIVE |
| Query Trace (TracePanel v2.0) | LIVE but stale — reflects old pipeline stages |
| Performance Command Center | MISSING — Gate I |
| Trace aligned to new pipeline | STALE — Gate II |
| Intelligent Chat Interface | BASIC — Gate III |
| LL.1–LL.7 Learning Layer | ACTIVE (from M4) |
| LL.8 Bayesian updating | SCAFFOLDED (activates in M5) |

### 3.7 Migration Numbers

Last migration: `042_tool_execution_log_scores.sql`

Pre-assigned ranges (to prevent parallel conflicts):
- **Gate I:** 043, 044 (performance schema + eval run table)
- **Gate II:** 045 (trace schema update if needed; may be 0 migrations)
- **Gate III:** 046 (likely 0 migrations — UI/prompt changes only)
- **Gate IV:** no migrations

### 3.8 Scope Constraints Per Gate (must_not_touch)

**Gate I must_not_touch:**
- `components/trace/**`
- `components/consume/**`
- `app/api/chat/consume/**`
- `components/shared/AppShellRail.tsx`
- `components/shared/MobileNavSheet.tsx`
- `01_FACTS_LAYER/**`, `025_HOLISTIC_SYNTHESIS/**`, `06_LEARNING_LAYER/**`

**Gate II must_not_touch:**
- `components/consume/ConsumeChat.tsx`
- `components/consume/AnswerView.tsx`
- `components/consume/StreamingAnswer.tsx`
- `app/api/chat/consume/route.ts`
- `components/performance/**` (Gate I territory)
- `components/shared/AppShellRail.tsx`
- `components/shared/MobileNavSheet.tsx`
- `01_FACTS_LAYER/**`, `025_HOLISTIC_SYNTHESIS/**`, `06_LEARNING_LAYER/**`

**Gate III must_not_touch:**
- `components/trace/**` (Gate II territory — including TraceDrawer, TracePanel)
- `lib/admin/trace_assembler.ts`
- `components/performance/**` (Gate I territory)
- `components/shared/AppShellRail.tsx`
- `components/shared/MobileNavSheet.tsx`
- `01_FACTS_LAYER/**`, `025_HOLISTIC_SYNTHESIS/**`, `06_LEARNING_LAYER/**`

**Rule for all three executors:**
- Do NOT install new npm packages without flagging as a manual step
- Do NOT touch migrations outside your pre-assigned range
- CLAUDECODE_BRIEF.md moves to `00_ARCHITECTURE/briefs/` at session close

---

## §4 — Worktree Setup

Run this once before starting any Cowork conversations.
Either paste into a Claude Code (Antigravity) session pointed at the
Madhav directory, or run directly in Terminal.

### Option A — Paste into a Claude Code session

```
Set up three git worktrees for parallel gate development on the MARSYS-JIS
project. The main repo is at /Users/Dev/Vibe-Coding/Apps/Madhav.

Run the following commands in sequence:

cd /Users/Dev/Vibe-Coding/Apps/Madhav

git worktree add ../marsys-gate1-perf-center -b feature/gate1-perf-command-center
git worktree add ../marsys-gate2-trace-align -b feature/gate2-trace-pipeline-align
git worktree add ../marsys-gate3-smart-chat -b feature/gate3-intelligent-chat

cd /Users/Dev/Vibe-Coding/Apps/marsys-gate1-perf-center/platform && npm install
cd /Users/Dev/Vibe-Coding/Apps/marsys-gate2-trace-align/platform  && npm install
cd /Users/Dev/Vibe-Coding/Apps/marsys-gate3-smart-chat/platform   && npm install

cd /Users/Dev/Vibe-Coding/Apps/Madhav

Confirm all three worktrees exist and npm install completed without errors.
Report the git branch for each worktree.
```

### Option B — Run directly in Terminal

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav

git worktree add ../marsys-gate1-perf-center -b feature/gate1-perf-command-center
git worktree add ../marsys-gate2-trace-align -b feature/gate2-trace-pipeline-align
git worktree add ../marsys-gate3-smart-chat  -b feature/gate3-intelligent-chat

# NOTE: package.json is at platform/, not repo root
cd /Users/Dev/Vibe-Coding/Apps/marsys-gate1-perf-center/platform && npm install &
cd /Users/Dev/Vibe-Coding/Apps/marsys-gate2-trace-align/platform  && npm install &
cd /Users/Dev/Vibe-Coding/Apps/marsys-gate3-smart-chat/platform   && npm install &
wait && echo "All three installs complete."

# Verify
cd /Users/Dev/Vibe-Coding/Apps/Madhav && git worktree list
```

---

## §5 — Verbatim Context Prompts for Each Gate Conversation

Copy each prompt exactly as written. The prompt is the full context;
Opus will read the briefing document for details.

---

### §5.1 — Gate I Context Prompt
**Conversation name: `MARSYS Gate I — Performance Command Center`**
**Worktree: `marsys-gate1-perf-center`**

```
You are Claude Opus 4.7 — the design and planning layer for a pre-M5 gate
on the MARSYS-JIS project.

MARSYS-JIS is an LLM-operated Vedic astrology intelligence system built on
Next.js, Cloud SQL (Postgres + pgvector), Gemini LLM, and Cloud Run.
Four macro-phases (M1–M4) are closed. M5 (Probabilistic Model) opens after
three parallel pre-M5 gates are cleared. This conversation owns Gate I.

GATE I — PERFORMANCE COMMAND CENTER
A new first-class portal section (super-admin gated, route: /performance)
that captures every query — from the consume UI and from backend eval runs —
and tracks it against defined KPIs: plan accuracy, citation rate, calibration
score, B.10/B.11 compliance, latency per query class, synthesis pass rate,
and retrieval hit rate. Nothing like this exists today. It is entirely net-new.

YOUR ROLE
Design this gate and produce a CLAUDECODE_BRIEF.md. Lock all decisions with
the native (Abhisek) before writing the brief. Do not write implementation
code. The executor is Claude Code Sonnet 4.6 in VS Code Anti-Gravity with
--dangerously-skip-permissions, working in the git worktree at
/Users/Dev/Vibe-Coding/Apps/marsys-gate1-perf-center.

FULL CONTEXT
Before doing anything else, read:
  00_ARCHITECTURE/briefs/OPUS_PLANNING_SESSION_v2_0.md
This document has the full tech stack, portal route map, pipeline architecture,
scope constraints, migration number assignments (Gate I gets 043–044),
must_not_touch lists, and the CLAUDECODE_BRIEF format you must use.

START HERE
Ask the native the Gate I scoping questions from §6.1 of the briefing
document. Do not begin designing until these are locked:
  1. URL/nav placement (/performance as top-level — confirm)
  2. Eval run persistence: auto-hook into eval scripts or manual trigger?
  3. P0 KPI list (which metrics must ship at launch)
  4. Source tagging: consume-triggered and eval-triggered queries in one
     log with a source tag, or separate views?
```

---

### §5.2 — Gate II Context Prompt
**Conversation name: `MARSYS Gate II — Trace Pipeline Alignment`**
**Worktree: `marsys-gate2-trace-align`**

```
You are Claude Opus 4.7 — the design and planning layer for a pre-M5 gate
on the MARSYS-JIS project.

MARSYS-JIS is an LLM-operated Vedic astrology intelligence system built on
Next.js, Cloud SQL (Postgres + pgvector), Gemini LLM, and Cloud Run.
The system has a new query pipeline (planner → retrieval → synthesis → audit)
— the ONLY pipeline; the legacy/hybrid was deleted in May 2026. The consume
module has a live trace system (TraceDrawer → TracePanel v2.0, 20+ components)
that shows pipeline execution in real time, but its stage names, step
vocabulary, and metadata schema still reflect the old pipeline. This conversation
owns Gate II.

GATE II — TRACE PIPELINE ALIGNMENT
A surgical, targeted fix. Rewire TracePanel.tsx and its sub-components
(step detail variants, lifecycle nodes, trace assembler) to accurately reflect
the new pipeline's actual stages, metadata fields, and step vocabulary.
No new features. Pure alignment. The executor must audit the gap between
what the trace currently renders and what the new pipeline actually emits
before writing a single line of code.

YOUR ROLE
Design this gate and produce a CLAUDECODE_BRIEF.md. Lock all decisions with
the native (Abhisek) before writing the brief. Do not write implementation
code. The executor is Claude Code Sonnet 4.6 in VS Code Anti-Gravity with
--dangerously-skip-permissions, working in the git worktree at
/Users/Dev/Vibe-Coding/Apps/marsys-gate2-trace-align.

FULL CONTEXT
Before doing anything else, read:
  00_ARCHITECTURE/briefs/OPUS_PLANNING_SESSION_v2_0.md
This document has the full tech stack, portal route map, new pipeline
stage definitions, trace component inventory, scope constraints,
migration number assignments (Gate II gets 045 if needed), must_not_touch
lists, and the CLAUDECODE_BRIEF format you must use.

START HERE
Ask the native the Gate II scoping questions from §6.2 of the briefing
document. Make clear in the brief that the executor's FIRST work item
is to read TracePanel.tsx, trace_assembler.ts, and the trace SSE stream
endpoint side-by-side to produce a gap analysis before any code changes.
Key decisions to lock with the native:
  1. Should checkpoints (4.5, 5.5, 8.5) appear as optional expandable
     steps or always visible even when disabled?
  2. Should per-step latency be shown inline in the drawer or only total?
  3. Is there a trace schema definition file, or is it inferred from
     trace_assembler.ts? (Executor audits this first.)
```

---

### §5.3 — Gate III Context Prompt
**Conversation name: `MARSYS Gate III — Intelligent Chat Interface`**
**Worktree: `marsys-gate3-smart-chat`**

```
You are Claude Opus 4.7 — the design and planning layer for a pre-M5 gate
on the MARSYS-JIS project.

MARSYS-JIS is an LLM-operated Vedic astrology intelligence system built on
Next.js, Cloud SQL (Postgres + pgvector), Gemini LLM, and Cloud Run.
The consume module (ConsumeChat.tsx, AnswerView.tsx, StreamingAnswer.tsx)
is a functional but generic chat interface. It does not know it is operating
in a Jyotish domain with a 7-class query pipeline, an MSR signal corpus
(499 signals), a dasha temporal engine, and a layered L1/L2.5/L3 corpus
architecture. This conversation owns Gate III.

GATE III — INTELLIGENT CHAT INTERFACE
Transform the consume chat into a domain-aware, pipeline-intelligent interface.
Scope includes: query class awareness in the input layer, pipeline-context
display in the answer view (query class badge, plan type, tools fired),
Sanskrit term inline definitions, active dasha/transit context panel,
enriched system prompt in the consume API route, and conversational context
continuity. Gate III does NOT touch trace components (TracePanel, TraceDrawer,
trace_assembler) — those are Gate II's exclusive territory.

YOUR ROLE
Design this gate, gather the native's detailed UX requirements (he has specific
ideas to share), and produce a CLAUDECODE_BRIEF.md. Lock all decisions before
writing the brief. Do not write implementation code. The executor is Claude
Code Sonnet 4.6 in VS Code Anti-Gravity with --dangerously-skip-permissions,
working in the git worktree at
/Users/Dev/Vibe-Coding/Apps/marsys-gate3-smart-chat.

FULL CONTEXT
Before doing anything else, read:
  00_ARCHITECTURE/briefs/OPUS_PLANNING_SESSION_v2_0.md
This document has the full tech stack, portal route map, pipeline architecture,
consume component inventory, scope constraints, must_not_touch lists
(trace components are forbidden), and the CLAUDECODE_BRIEF format you must use.

START HERE
Invite the native to describe his full vision for the Intelligent Chat Interface
in his own words before you begin any architecture design. He has detailed
requirements to share. After he describes the vision, ask the Gate III
scoping questions from §6.3 of the briefing document to lock the scope
boundary and component plan before designing.
```

---

## §6 — Gate Design Questions (for Opus to resolve in each conversation)

### §6.1 — Gate I Open Questions
1. URL/nav: `/performance` as a new top-level section alongside Observatory? *(recommended — confirm)*
2. Eval run persistence: hook into eval scripts automatically, or manual "start eval run" button in the portal?
3. P0 KPIs (must ship at launch) vs P1 (nice to have) — which of these are P0:
   plan accuracy, citation rate, calibration score, B.10/B.11 compliance,
   latency per class, synthesis pass rate, retrieval hit rate?
4. Consume-triggered and eval-triggered queries: one unified log with `source` tag, or separate views?
5. Should the Command Center show real-time ingestion (live as queries come in) or polling-based refresh?

### §6.2 — Gate II Open Questions
1. Is there a formal trace schema definition file, or is the schema inferred from `trace_assembler.ts`?
   *(executor audits this as Work Item 1 before any code changes)*
2. Checkpoints (4.5, 5.5, 8.5): always show as collapsible steps, or only when enabled?
3. Per-step latency: shown inline in each step row, or only total wall-clock time?
4. Should the trace drawer show the QueryPlan fields (query_class, plan_type, tools_selected,
   confidence, reasoning) as a distinct "Planning" step, or as a header above the steps?

### §6.3 — Gate III Open Questions
1. Query class display: show the classified query class (e.g., "Interpretive — Planetary") as a badge
   in the input area before submitting, or only in the answer view after response?
2. Sanskrit term definitions: hover tooltip only, or also a collapsible glossary panel?
3. Dasha/transit context panel: persistent sidebar, collapsible header, or on-demand toggle?
4. Conversational context: how many prior turns should the system prompt carry?
   *(currently capped at 2 — native decision)*
5. Query history recall: within-session only, or persisted across sessions?
6. Suggested prompts / example queries per class: shown on empty state, or always visible?

---

## §7 — Gate IV — M5 Launchpad

**Name:** Gate IV — M5 Launchpad
**Handled by:** This macro plan conversation (no Opus session needed — brief is simple)
**Executor:** Claude Code Sonnet 4.6, Antigravity, `--dangerously-skip-permissions`, on `main`
**Trigger:** After Gates I + II + III are merged to main

### §7.1 — Gate IV Work Items

**W1 — Nav cleanup** *(5 minutes)*
Add all three new nav items in a single commit:
- `components/shared/AppShellRail.tsx` — add to NAV_ITEMS
- `components/shared/MobileNavSheet.tsx` — add to NAV_ITEMS
- Items: Performance Command Center (`/performance`), plus any Gate II/III
  nav additions determined during their design sessions

**W2 — Migration sequence verification**
Confirm migrations 043–046 (whichever were produced by each gate) applied
in correct sequence with no gaps, no FK violations, no down-migration needed.
Run `\d` on key new tables to verify schema matches the brief.

**W3 — End-to-end query flow test**
Submit a query via the consume UI. Verify:
- Trace drawer fires with correct new pipeline stage names (Gate II)
- Query appears in Performance Command Center within expected window (Gate I)
- Answer view shows query class badge and pipeline context (Gate III)
- Audit log captures the query (existing behavior, regression check)

**W4 — Eval run through Command Center**
Trigger a golden-set eval run. Verify:
- The Command Center captures eval-sourced queries with `source: eval` tag
- Aggregate KPI scores update correctly after the run
- Eval run appears in run history with correct timestamp and scores

**W5 — Auth regression check**
Verify all new super-admin routes return 403 for non-super_admin users:
- `GET /performance` (Gate I)
- All new Gate I API routes
- Confirm consume routes remain accessible to native-tier users (Gate III
  changes must not break existing access control)

**W6 — Performance regression check**
Run the golden-set eval (46 queries). Verify:
- Plan accuracy: recall ≥ 0.97, precision ≥ 0.95 (regression from pre-gate baseline)
- P95 latency on `/api/chat/consume` within ±20% of pre-gate baseline
- No synthesis failures introduced by Gate III system prompt changes

**W7 — Full test suite green**
`npm test` — all tests pass on merged main.
`tsc --noEmit` — TypeScript compiles clean.
ESLint clean.

### §7.2 — Gate IV Acceptance Criteria

- [ ] AC.IV.1 — Nav items visible for super_admin on desktop and mobile
- [ ] AC.IV.2 — All migrations 043–046 applied cleanly; no schema errors
- [ ] AC.IV.3 — End-to-end query flow verified (W3 above)
- [ ] AC.IV.4 — Eval run captured in Command Center (W4 above)
- [ ] AC.IV.5 — Auth regression: all new super-admin routes gate correctly
- [ ] AC.IV.6 — Plan accuracy regression: recall ≥ 0.97, precision ≥ 0.95
- [ ] AC.IV.7 — Latency regression within ±20% of baseline
- [ ] AC.IV.8 — Full test suite green; TypeScript clean; ESLint clean

All 8 ACs must pass before Gate IV is declared closed.

---

## §8 — Return Protocol for This Conversation

When the native returns to this conversation (macro plan conversation):

### Return 1 — After Gates I + II + III close

**This conversation runs a gate check first. Do not proceed to merge or
Gate IV until all three pass.**

Gate check (read these artifacts):
- `00_ARCHITECTURE/briefs/` — confirm briefs for Gate I, II, III are present
  with `status: COMPLETE`
- `00_ARCHITECTURE/SESSION_LOG.md` — confirm executor session entries exist
  for all three gates
- `git branch --merged main` — confirm all three feature branches are merged
  *(or ready to merge)*

If any gate is not closed, report which ones are still open and wait.

If all three are closed, proceed to:
1. Execute the merge sequence (§9 below)
2. Author the Gate IV CLAUDECODE_BRIEF in this conversation
3. Native triggers Gate IV Claude Code executor

### Return 2 — After Gate IV closes

**This conversation confirms Gate IV acceptance criteria, then opens M5.**

1. Confirm all AC.IV.1–AC.IV.8 pass
2. Declare: "All pre-M5 gates cleared. System is ready for M5."
3. Author `PHASE_M5_PLAN_v1_0.md`
4. M5 implementation begins

---

## §9 — Merge Sequence (executed on Return 1)

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav

# 1. Gate II first — surgical, smallest, trace foundation for Gate III
git merge --no-ff feature/gate2-trace-pipeline-align

# 2. Gate I — independent, all new files
git merge --no-ff feature/gate1-perf-command-center

# 3. Gate III — rebase first to pick up Gate II's trace schema
git checkout feature/gate3-intelligent-chat
git rebase main
git checkout main
git merge --no-ff feature/gate3-intelligent-chat

# 4. Worktree cleanup
git worktree remove ../marsys-gate1-perf-center
git worktree remove ../marsys-gate2-trace-align
git worktree remove ../marsys-gate3-smart-chat

# Gate IV executor starts here (nav + integration testing on main)
```

---

## §10 — CLAUDECODE_BRIEF Format

Every brief the Opus conversations produce must use this exact structure.
File lands at project root as `CLAUDECODE_BRIEF.md`. After close → `00_ARCHITECTURE/briefs/`.

```markdown
---
brief_id: GATE-[I/II/III]-[SESSION_TAG]
version: 1.0
status: ACTIVE
authored_by: Claude Opus 4.7 ([Gate Name] Design Session) — YYYY-MM-DD
purpose: One-sentence summary.
executor: Claude Code Sonnet 4.6 (Anti-Gravity, VS Code)
working_directory: /Users/Dev/Vibe-Coding/Apps/[worktree-name]
model_preference: gemini-2.5-pro (critical); gemini-2.0-flash-lite (non-critical)
---

# CLAUDECODE_BRIEF — [Gate Name]

## §0 — Read This First
[2–3 sentences on what this session delivers and why.]

## §1 — Entry Gates
- [ ] Worktree exists at [path] on branch feature/gate[N]-[name]
- [ ] npm install completed in worktree
- [ ] [Gate-specific prerequisite]
All entry gates must pass before starting work.

## §2 — Scope

### may_touch
- `platform/src/...` [specific globs]

### must_not_touch
- `components/shared/AppShellRail.tsx`
- `components/shared/MobileNavSheet.tsx`
- [Gate-specific must_not_touch list from §3.8 of this document]
- `01_FACTS_LAYER/**`, `025_HOLISTIC_SYNTHESIS/**`, `06_LEARNING_LAYER/**`

## §3 — Work Items
[W1, W2, W3... — each with exact file targets, what to do, dependencies]

## §4 — Acceptance Criteria
- [ ] AC.1 — [Specific, testable]
- [ ] AC.2 — ...

## §5 — LLM Stack
- Default: gemini-2.5-pro
- Non-critical: gemini-2.0-flash-lite or deepseek-chat
- BANNED: anthropic/* — flag immediately if seen in touched files

## §6 — Tests
[Test files to create/update; minimum coverage bar]

## §7 — Migration Numbers
[Gate I: 043–044 | Gate II: 045 | Gate III: 046]
Do not use migrations outside this range.

## §8 — Session Close Checklist
- [ ] All ACs pass
- [ ] npm test green
- [ ] tsc --noEmit clean
- [ ] ESLint clean
- [ ] CLAUDECODE_BRIEF.md moved to 00_ARCHITECTURE/briefs/ status: COMPLETE
- [ ] SESSION_LOG.md entry appended
- [ ] No files touched outside may_touch list
```

---

## §11 — Key Project Rules (encode in every brief)

- **B.10:** LLM never invents numerical chart values. Mark `[EXTERNAL_COMPUTATION_REQUIRED]`.
- **B.11:** Every query routes through L2.5 Holistic Synthesis first.
- **File placement:** ROOT_FILE_POLICY §3. Nothing at project root except active CLAUDECODE_BRIEF.md.
- **GCS URIs:** Read `GCS_LAYOUT_v1_0.md` before writing any `gs://` path. Layer-prefix: `L1/`, `L2_5/`, `L3/`.
- **DB migrations:** Enumerate ALL FK dependents before DELETE. Query `pg_constraint` first.
- **Vitest mocks:** Use `mockImplementation(function() {...})` not arrow functions (Vitest 4.x).
- **No new npm packages** without flagging as manual step first.
- **No Anthropic models** in application logic — flag and replace with Gemini/DeepSeek.

---

*End of OPUS_PLANNING_SESSION_v2_0.md — 2026-05-12*
*Supersedes v1.0. This is the master document for all pre-M5 gate work.*
