---
artifact: OPUS_PLANNING_SESSION_v1_0.md
version: 1.0
status: ACTIVE
authored_by: Claude Sonnet 4.6 (Cowork) — 2026-05-12
purpose: >
  Self-contained briefing document for a Claude Opus 4.7 planning session.
  Carries full project context, current portal state, three pre-M5 gate
  definitions, CLAUDECODE_BRIEF format, and operating instructions.
  Drop this into a fresh Opus conversation to pick up exactly where the
  Sonnet planning session left off.
---

# MARSYS-JIS — Opus Planning Session Brief
## Pre-M5 Gate Design + CLAUDECODE_BRIEF Authoring

---

## §1 — Who You Are and What This Session Does

You are **Claude Opus 4.7** operating as the **design and planning layer** for
the MARSYS-JIS project. You do **not** implement code in this conversation.
Your outputs are:

1. **Design decisions** — scoped, reasoned, aligned with the existing
   architecture. Ask the native (Abhisek) the right questions; make
   recommendations; lock decisions.
2. **CLAUDECODE_BRIEFs** — one per gate. These are the execution dispatchers
   that Claude Code (running in VS Code via the "Anti-Gravity" extension)
   will implement. Every decision you make here gets encoded into the briefs
   so that the executor session has zero ambiguity.
3. **Parallelization map** — identify which gates can run as concurrent
   executor sessions to maximize build velocity.

The native will trigger each executor in a separate Claude Code session in
Anti-Gravity. You never hand off mid-design; you complete the full design
and brief for each gate before the native walks away to execute.

---

## §2 — Project Context (Read This Once, Then Work)

### 2.1 What MARSYS-JIS Is

An LLM-operated Jyotish (Vedic astrology) instrument for the native,
Abhisek Mohanty (b. 1984-02-05, 10:43 IST, Bhubaneswar). The system reads
his chart at acharya-grade depth, surfaces patterns no individual astrologer
could hold in working memory, and makes time-indexed probabilistic predictions
testable against lived reality. Eventually it extends to a research tool for
astrology as a discipline.

### 2.2 The Ten Macro-Phase Arc (M1–M10)

| Phase | Name | Status |
|---|---|---|
| M1 | Corpus Completeness | **CLOSED** 2026-04-19 |
| M2 | Corpus Activation | **CLOSED** 2026-04-28 |
| M3 | Temporal Animation | **CLOSED** 2026-05-01 |
| M4 | Empirical Calibration | **CLOSED** 2026-05-02 |
| **M5** | **Probabilistic Model** | **INCOMING — next** |
| M6 | Prospective Testing | Future |
| M7 | Population Extension | Future |
| M8 | Classical Text Cross-Reference | Future |
| M9 | Multi-School Triangulation | Future |
| M10 | LLM-Acharya Interface + Validation | Future |

**Current state:** M5 has not opened. No `PHASE_M5_PLAN_v1_0.md` exists yet.
M5's first session will author that plan. Before M5 opens, the native wants
three pre-M5 gate implementations completed to ensure the system is
instrumented, observable, and well-surfaced for the probabilistic work ahead.

### 2.3 Tech Stack

- **Framework:** Next.js (App Router, TypeScript)
- **Database:** Cloud SQL (Postgres + pgvector)
- **Storage:** Google Cloud Storage (GCS) — layer-prefix layout (`L1/`, `L2_5/`, `L3/`)
- **Auth:** Firebase Auth
- **Hosting:** Cloud Run
- **Default LLM:** Gemini (Gemini 2.5 Pro for critical, flash variants for non-critical)
- **Fallback LLM:** DeepSeek
- **BANNED LLM:** Anthropic/Claude models for application logic — costs too high.
  Flag immediately if any brief or executor hardcodes Anthropic models.
- **Testing:** Vitest
- **Styling:** Tailwind CSS + shadcn/ui

### 2.4 Current Portal Route Map

The portal has these sections already live:

**Consume (client-facing query interface):**
- `/clients/[id]/consume` — main consume page
- `/clients/[id]/consume/[conversationId]` — conversation detail
- `TraceDrawer.tsx` — live trace panel in the consume UI (currently wired
  to legacy/hybrid pipeline — **this is Gate 2's target**)

**Audit (super-admin):**
- `/audit` — audit list
- `/audit/[query_id]` — query detail
- `/audit/compare` — A/B comparison
- `/audit/predictions` — prediction log

**Observatory (super-admin):**
- `/observatory` — cost/usage observatory
- `/observatory/analytics/*` — anomaly, cache, cost-arc, cost-per-quality,
  pricing-diff, replay
- `/observatory/budgets`, `/observatory/events`, `/observatory/reconciliation`

**Cockpit (build-phase governance):**
- `/cockpit` — main dashboard
- `/cockpit/activity`, `/cockpit/health`, `/cockpit/interventions`
- `/cockpit/parallel`, `/cockpit/plan`, `/cockpit/registry`, `/cockpit/sessions`

**Admin:**
- `/admin` — user management
- `/admin/trace/[query_id]` — admin-side trace view

**API routes of interest:**
- `POST /api/chat/consume` — main query pipeline entry point
- `GET /api/admin/trace/[query_id]` — trace data endpoint
- `GET /api/trace/history` — trace history
- `GET /api/trace/stream/[queryId]` — SSE trace stream
- `GET /api/audit/list` — audit log query
- `GET /api/audit/[query_id]` — single audit record

**Key library files:**
- `platform/src/lib/pipeline/pipeline_planner.ts` — the query planner
  (PLANNER_PROMPT v2.1, 7 query classes, 46 golden entries,
  recall=0.983, precision=0.961 as of 2026-05-11)
- `platform/src/lib/admin/trace_assembler.ts` — assembles trace data
- `platform/src/lib/admin/trace_client.ts` — client for trace API
- `platform/src/components/consume/TraceDrawer.tsx` — the live trace drawer
  in the consume UI (Gate 2 target)

**Active feature flags:**
- `AUDIT_ENABLED=true`
- `MARSYS_FLAG_OBSERVATORY_ENABLED=true`
- All `DISCOVERY_*_ENABLED=true`
- `NEW_QUERY_PIPELINE_ENABLED` — **RETIRED** (Phase 11B 2026-05-11;
  new pipeline is the only pipeline; no flag exists)

### 2.5 The Query Pipeline (New — The Only Pipeline)

The new query pipeline stages (in order):
1. **Planner** — classifies query, produces QueryPlan (7-field schema,
   5 plan types: factual, interpretive, predictive, discovery, holistic)
2. **Retrieval** — hybrid retrieval (vector + graph + structured SQL);
   top-K semantic + ranked structured results
3. **Synthesis** — Gemini (claude-opus-4-6 is NOT used; Gemini is default);
   single-model or panel mode; produces answer + citations + derivation ledger
4. **Audit** — logs query, plan, retrieval results, synthesis output,
   validation verdict, disclosure tier
5. **Checkpoints** — optional LLM-graded quality gates at 4.5, 5.5, 8.5

The legacy/hybrid pipeline was deleted in Phase 11B (2026-05-11).
The `TraceDrawer.tsx` in the consume module still reflects the legacy
stage structure — that's what Gate 2 fixes.

### 2.6 What Exists for Performance Tracking Today

**What exists (ad-hoc):**
- Audit log (`/audit`) captures every query with validator verdict,
  citation count, disclosure tier, and synthesis quality flags
- Observatory (`/observatory`) tracks LLM cost/usage per provider
- Query Trace (`/admin/trace/[query_id]`) shows per-query pipeline trace
  with lifecycle graph, step details, health rail, anomaly detectors
- Eval scripts (golden set, 46 queries) run from CLI — results go to stdout,
  not persisted to the portal

**What does NOT exist:**
- A dedicated performance command center aggregating all queries
  (consume + eval + API) with KPI dashboards, trends, and regression tracking
- Any persistent store for eval run results (golden set runs are ephemeral)
- A single view showing: pass rates, latency trends, citation rates,
  calibration drift, plan accuracy over time

---

## §3 — The Three Pre-M5 Gates

Design and produce a `CLAUDECODE_BRIEF.md` for each gate.
Work through them in order. Gates 1 and 2 may be parallelizable
(see §5); Gate 3 follows both.

---

### Gate 1 — Query Performance Command Center

**What and Why:**

A dedicated, first-class portal section that makes query performance
systemic and observable — replacing ad-hoc CLI analysis and scattered
audit/observatory views with a unified performance command center.

Every query that passes through the system — whether triggered from the
consume UI by the native, run as a backend eval batch, or fired via direct
API — should be captured, tracked, and measured against a consistent set
of KPIs. The Command Center is the instrument for knowing whether M5's
Probabilistic Model is actually improving things.

**Scope to design:**

1. **Data model** — What new tables/columns are needed? The audit log
   already captures raw query data; the Command Center needs aggregated
   views, eval run tracking, and trend tables. Design the DB schema.

2. **Eval run persistence** — Currently golden-set eval runs (`npm run
   eval:*` or similar) output to stdout and are lost. The Command Center
   should persist eval run results (run ID, timestamp, model, golden-set
   version, per-query verdicts, aggregate scores) to the DB.

3. **KPIs to track** — What metrics matter? Candidates:
   - Plan accuracy (recall, precision vs golden set)
   - Citation rate (% of answers with ≥1 citation)
   - Calibration score (% of outputs with confidence bands)
   - B.10 compliance rate (% that avoid fabricated computation)
   - B.11 compliance rate (% that go through L2.5 Holistic Synthesis)
   - Latency (P50, P95 per query class)
   - Synthesis quality pass rate (validator verdict)
   - Retrieval hit rate (top-K with relevant result)
   - Panel vs single-model routing distribution

4. **URL structure** — Where does this live? Options:
   - New `/performance` section (parallel to `/observatory`, `/audit`)
   - Extend `/cockpit` with a `/cockpit/performance` sub-section
   - New `/command-center` top-level route

5. **Views to build:**
   - Summary dashboard — headline KPIs, trend sparklines, health status
   - Query log — all queries (consume + eval), filterable by source/class/date
   - Eval run history — list of eval runs with drill-down per run
   - KPI trends — time-series charts per metric, with regression detection
   - Per-query detail — deep-link into existing audit/trace views

6. **Access control** — Super-admin only (consistent with Observatory pattern)
   or native-accessible?

**Questions to resolve with native before writing the brief:**
- Where should this live in the nav? New top-level or under cockpit?
- Should eval runs be persisted automatically (hook into the eval script)
  or triggered manually from the portal?
- Which KPIs are P0 (must have at launch) vs P1 (nice to have)?
- Should consume-triggered queries and eval-triggered queries be in the
  same query log with a `source` tag, or separate views?

---

### Gate 2 — Live Trace → New Pipeline Alignment

**What and Why:**

The consume module has a `TraceDrawer.tsx` that shows a live trace of
pipeline execution as the native submits a query. This trace was built
against the legacy/hybrid pipeline (which had different stage names,
different step structure, different metadata). The legacy pipeline was
deleted in Phase 11B (2026-05-11). The `TraceDrawer` is now showing
a lie — it either renders incorrectly, shows stale stage names, or
silently fails to map the new pipeline's step structure.

This gate is a surgical, targeted fix: rewire the trace drawer to
accurately reflect the new pipeline's actual stages and metadata.

**Scope to design:**

1. **Audit the gap** — What does `TraceDrawer.tsx` currently render?
   What stage names, step types, and metadata fields does it expect?
   What does the new pipeline actually emit to `trace_assembler.ts`?
   The executor must read both before touching anything.

2. **New pipeline stage map** — Define the canonical stage list and
   metadata schema for the trace drawer:
   - `planner` — QueryPlan fields: query_class, plan_type, tools_selected,
     confidence, reasoning
   - `retrieval` — sub-steps per tool: vector_search, cgm_graph_walk,
     structured_sql, hybrid_rank; results count, top score
   - `synthesis` — model used, token count, panel/single mode,
     checkpoint verdicts if any, disclosure tier
   - `audit` — validator verdict, citation count, B.10/B.11 flags
   - `checkpoints` — if enabled: checkpoint_4_5, checkpoint_5_5, checkpoint_8_5
     with per-checkpoint verdict

3. **Backend alignment** — Does `trace_assembler.ts` already emit the
   correct fields for the new pipeline? Does `GET /api/admin/trace/[query_id]`
   return the right shape? Or does the API also need a schema update?

4. **UI updates** — `TraceDrawer.tsx` stage icons, step labels, duration
   display, metadata panels — all need to match the new pipeline vocabulary.
   No new features; pure alignment.

5. **Test coverage** — `trace_assembler.test.ts` and `trace_route.test.ts`
   exist. Update them to assert the new schema.

**Questions to resolve:**
- Is there a trace schema definition file somewhere, or is it inferred from
  the assembler? (Executor should grep for this before designing the fix.)
- Should the trace drawer show checkpoints as optional expandable steps,
  or always show them even when disabled?
- Should latency be shown per-step in the drawer, or only the total?

---

### Gate 3 — Intelligent Chat Interface

**What and Why:**

The current consume chat interface (`ConsumeChat.tsx`, `AnswerView.tsx`,
`StreamingAnswer.tsx`) is a competent generic chat UI. It does not know
it is operating in a Jyotish domain with a structured query pipeline.
The native wants to transform it into a domain-aware, contextually
intelligent interface.

The native has said he will provide detailed requirements in a dedicated
session. **This gate's design pass in this conversation should focus on
the architecture and skeleton, not the final pixel-level design.**

**Scope to design (skeleton pass only):**

1. **Domain awareness in the input layer:**
   - Query composer should understand query classes (factual, interpretive,
     predictive, discovery, holistic) and optionally surface them
   - Suggested prompts / example queries per class
   - Awareness of current dasha period / active transits as contextual priming

2. **Pipeline-aware response rendering:**
   - The answer view should show which query class was classified,
     which plan type ran, which tools fired — not just the text answer
   - Citation chips already exist (`CitationChip.tsx`); they should be
     enriched with layer provenance (L1 fact vs L2.5 synthesis vs L3 discovery)

3. **Astrological vocabulary support:**
   - Render Sanskrit terms with hover-definitions (e.g., "Vimshottari",
     "Yoga", "Ashtakavarga" should have inline tooltips)
   - Chart context panel — which dasha/sub-dasha/transit is active at today's
     date, shown as a persistent sidebar or collapsible header

4. **Conversational intelligence:**
   - The interface should maintain session context — a follow-up question
     like "what about the 7th house?" should be understood in the context
     of the prior answer, not treated as a fresh query
   - The system prompt powering the consume route should be enriched with
     domain priming (the executor for this gate will need to modify
     `POST /api/chat/consume/route.ts` and the synthesis prompt)

5. **Query history + recall:**
   - Previously asked queries with their answers, accessible in-session
   - Ability to re-run a past query to compare against current pipeline

**Questions to defer to the dedicated Gate 3 design session:**
- Pixel-level visual design
- Specific Sanskrit vocabulary list
- Chart context data sources (which temporal engine outputs to pull)
- Exact system prompt content (this requires iterative tuning)

**Gate 3 dependency:** Gate 3 should run after Gate 2 (the trace alignment)
because the pipeline-aware response rendering depends on the correct
pipeline stage schema being established in Gate 2.

---

## §4 — CLAUDECODE_BRIEF Format

Every brief you author lands at the **project root** as `CLAUDECODE_BRIEF.md`
(per ROOT_FILE_POLICY §2 — it is the active session dispatcher). After
execution, the executor moves it to `00_ARCHITECTURE/briefs/`.

Use this exact structure:

```markdown
---
brief_id: [GATE_ID]-[SESSION_TAG]
version: 1.0
status: ACTIVE
authored_by: Claude Opus 4.7 (Planning Session) — YYYY-MM-DD
purpose: One-sentence summary of what this executor session delivers.
executor: Claude Code (Anti-Gravity, VS Code extension)
model_preference: gemini-2.5-pro (critical paths); gemini-2.0-flash (non-critical)
---

# CLAUDECODE_BRIEF — [Gate Name]

## §0 — Read This First
[2–3 sentences on what this session does and why it matters. No boilerplate.]

## §1 — Entry Gates
- [ ] [Prerequisite check 1]
- [ ] [Prerequisite check 2]
All entry gates must pass before starting work.

## §2 — Active Phase
[Which pre-M5 gate this is; connection to macro plan]

## §3 — Scope
### may_touch
- `platform/src/...` [specific file globs]
- `platform/src/app/api/...`

### must_not_touch
- `01_FACTS_LAYER/**`
- `025_HOLISTIC_SYNTHESIS/**`
- `06_LEARNING_LAYER/**`
- [Other corpus / governance layers]

## §4 — Work Items
Numbered, ordered list of discrete tasks. Each task:
- Has an ID (W1, W2, ...)
- Names the exact file(s) to create or modify
- Describes what to do with enough precision that no design decision
  is left to the executor
- Notes dependencies on prior work items

## §5 — Acceptance Criteria
- [ ] AC.1 — [Specific, testable criterion]
- [ ] AC.2 — ...
All ACs must pass before the session can close.

## §6 — LLM Stack Guidance
- Default: Gemini 2.5 Pro (for any LLM calls inside new features)
- Non-critical: gemini-2.0-flash-lite or deepseek-chat
- BANNED: anthropic/* — do not use any Anthropic model for application logic
- Flag immediately if any existing code hardcodes Anthropic models in
  the files this session touches

## §7 — Tests
- List the test files to create or update
- Minimum coverage bar (e.g., "all new API routes must have ≥5 tests")

## §8 — File Placement Rules
- All new platform code → `platform/src/...`
- All new API routes → `platform/src/app/api/...`
- DB migrations → `platform/supabase/migrations/NNN_description.sql`
  (increment from last migration number)
- New governance docs → `00_ARCHITECTURE/`
- This brief after close → `00_ARCHITECTURE/briefs/`
- NO new files at project root except CLAUDECODE_BRIEF.md itself

## §9 — Session Close Checklist
- [ ] All ACs pass
- [ ] All tests pass (`npm test` green)
- [ ] TypeScript compiles clean (`tsc --noEmit`)
- [ ] ESLint clean
- [ ] This brief moved to `00_ARCHITECTURE/briefs/` and status set COMPLETE
- [ ] `00_ARCHITECTURE/SESSION_LOG.md` entry appended
```

---

## §5 — Parallelization Map

```
Gate 1 (Command Center)   ─────────────────────────────────► [Gate 1 executor]
                                                              (new section, new DB tables,
                                                               new API routes, new UI)

Gate 2 (Trace Alignment)  ─────────────────────────────────► [Gate 2 executor]
                                                              (surgical fix to TraceDrawer +
                                                               trace_assembler schema)

Gates 1 and 2 are PARALLEL-SAFE — they touch different files:
  Gate 1 touches: new /performance routes, new DB schema, new components
  Gate 2 touches: TraceDrawer.tsx, trace_assembler.ts, trace API schema

Gate 3 (Intelligent Chat) ──── depends on Gate 2 ──────────► [Gate 3 executor]
                               (needs correct pipeline schema
                                from Gate 2 before rendering
                                pipeline-aware response UI)

Sequence:
  [This planning session] → Author all 3 briefs
  [Anti-Gravity session A] → Execute Gate 1
  [Anti-Gravity session B] → Execute Gate 2   ← run simultaneously with A
  [Anti-Gravity session C] → Execute Gate 3   ← after Gate 2 closes
```

---

## §6 — Operating Instructions for This Session

1. **Start with Gate 1.** Ask the native the open questions listed in §3 Gate 1.
   Do not proceed until the following are locked:
   - URL/nav placement of the Command Center
   - Eval run persistence mechanism (auto-hook vs manual trigger)
   - P0 KPI list
   - Source tagging approach (consume vs eval in one log)

2. **Then design Gate 1 in full** — DB schema, API routes, component tree,
   KPI definitions. Lock every decision. Write the CLAUDECODE_BRIEF for Gate 1.

3. **Move to Gate 2.** Ask the native the open questions listed in §3 Gate 2.
   Verify your assumptions about the trace schema gap — if you are unsure,
   say so explicitly and flag what the executor must audit first (the brief
   should instruct the executor to read both TraceDrawer.tsx and
   trace_assembler.ts before writing a single line of code).

4. **Design Gate 2** — new stage map, schema changes, UI updates.
   Write the CLAUDECODE_BRIEF for Gate 2.

5. **Gate 3 skeleton.** Do not try to fully design Gate 3 in this session —
   the native has flagged that detailed requirements come in a dedicated
   session. Design the architecture skeleton only: component boundaries,
   data sources, integration points with the pipeline. Write a skeleton
   CLAUDECODE_BRIEF that has the architecture locked but leaves the detailed
   UX/copy/prompt-content for the dedicated Gate 3 design session.

6. **Produce the parallelization map** as a clear instruction to the native
   showing which sessions to trigger simultaneously in Anti-Gravity.

7. **Do not implement code.** If you find yourself writing a TypeScript
   function or SQL table definition in your response (outside of the brief),
   stop — that belongs in the brief's Work Items section, authored precisely
   enough that the executor implements it correctly.

8. **LLM model hygiene.** At any point if the native or context implies
   using Anthropic/Claude models for application logic, flag it immediately.
   The default is Gemini. The fallback is DeepSeek. This is a hard project rule.

---

## §7 — Key Project Rules the Executor Must Follow (embed in every brief)

- **B.10 — No fabricated computation.** The LLM never invents numerical chart
  values. If a value isn't in the L1 corpus, mark `[EXTERNAL_COMPUTATION_REQUIRED]`.
- **B.11 — Whole-Chart-Read Protocol.** Every query routes through L2.5
  Holistic Synthesis (MSR + UCN + CDLM + CGM + RM) before domain-specific answer.
- **File placement** — See ROOT_FILE_POLICY §3. Nothing at project root except
  the active CLAUDECODE_BRIEF.md.
- **GCS URIs** — Read `GCS_LAYOUT_v1_0.md` before writing any `gs://` URI.
  Layer-prefix layout: `L1/`, `L2_5/`, `L3/` — not git directory paths.
- **DB migrations** — Enumerate ALL FK dependents before any DELETE in swap
  transactions. Query `pg_constraint` or grep migrations for `REFERENCES` first.
- **Vitest arrow-function mock pattern** — Use `mockImplementation(function() {...})`
  not arrow functions for Vitest 4.x mocks.
- **Versioning** — Every new canonical governance artifact gets frontmatter with
  `version`, `status`, and `changelog`. Registries must not disagree.

---

## §8 — Quick Reference: What Was Just Shipped (Context for Gap Analysis)

| Item | Status | Notes |
|---|---|---|
| New query pipeline | LIVE | Only pipeline; legacy deleted Phase 11B 2026-05-11 |
| PLANNER_PROMPT v2.1 | LIVE | recall=0.983, precision=0.961, 46 golden queries |
| Phase O Observatory | LIVE | Full cost/usage observatory behind super-admin |
| Query Trace redesign | LIVE | 3 new tables + mat view + lifecycle graph + 7 step variants + health rail |
| Audit view | LIVE | 4 routes (/audit, /audit/[id], /audit/predictions, /audit/compare) |
| TraceDrawer in consume | STALE | Still reflects legacy pipeline stages — Gate 2's target |
| Performance Command Center | MISSING | Does not exist — Gate 1's target |
| Intelligent Chat Interface | BASIC | Generic chat; no domain awareness — Gate 3's target |
| LL.1–LL.7 | ACTIVE | All seven Learning Layer mechanisms active from M4 |
| LL.8 Bayesian updating | SCAFFOLDED | Activates in M5 |

---

## §9 — How to Open This Session

Paste this document into a fresh Claude Opus 4.7 conversation and say:

> "Read the briefing above in full. Then confirm you understand the operating
> mode, the three gates, and the session structure. Start by asking me the
> open questions for Gate 1 so we can lock those decisions and begin designing
> the Command Center."

---

*End of OPUS_PLANNING_SESSION_v1_0.md — 2026-05-12*
*Authored by Claude Sonnet 4.6 (Cowork session) to carry context forward to Opus 4.7.*
