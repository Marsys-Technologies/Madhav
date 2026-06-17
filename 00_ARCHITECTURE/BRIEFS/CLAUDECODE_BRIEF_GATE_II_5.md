---
brief_id: GATE-II-5-PRODUCTION-ALIGN
version: 1.0
status: ACTIVE-AUTONOMOUS
authored_by: Claude Opus 4.7 (Gate II.5 — Production-State Alignment design session) — 2026-05-13
supersedes_partial: CLAUDECODE_BRIEF_GATE_II_v2_0.md (which closed with 20/20 ACs but against an incomplete pipeline model; this brief completes the alignment against actual production emit)
purpose: >
  Close the production-state gap discovered in Gate II's final fixup session.
  Bring the trace UI from "renders the brief's pipeline model" to "renders
  what production actually emits." Three locked design decisions D9–D11 below
  govern the realignment. Same worktree, same branch, before merge.
executor: Claude Code Sonnet 4.6 (Anti-Gravity, VS Code, --dangerously-skip-permissions)
working_directory: /Users/Dev/Vibe-Coding/Apps/marsys-gate2-trace-align
worktree_branch: feature/gate2-trace-pipeline-align
execution_mode: AUTONOMOUS-OVERNIGHT — single session, no mid-session human input. All manual work consolidated to §11 (pre-flight) and §12 (post-session). Builds directly on the closed Gate II v2.0 work.
model_preference: gemini-2.5-pro (critical); gemini-2.0-flash-lite or deepseek-chat (non-critical). Anthropic BANNED in application logic.
parent_planning_doc: 00_ARCHITECTURE/briefs/OPUS_PLANNING_SESSION_v2_0.md
estimated_runtime: 8–14 hours uninterrupted
relates_to:
  - 99_ARCHIVE/BRIEFS_RETIRED/CLAUDECODE_BRIEF_GATE_II_v2_0.md (predecessor; CLOSED)
  - 00_ARCHITECTURE/POST_GATE_II_FOLLOWUPS.md (FU.1 panel-mode trace emission — still deferred)
  - BLOCKERS.md (from prior fixup pass: §B.1 visual smoke, §B.2 audit_events schema mismatch)
changelog:
  - v1.0 (2026-05-13): Initial brief. Three new locked design decisions D9–D11
    on top of original D1–D8. Adds taxonomy realignment, 21-tool universe,
    and migration 045 for audit_events nullable column additions. Authors the
    Playwright spec that was missing in the prior fixup.
---

# CLAUDECODE_BRIEF — Gate II.5: Production-State Alignment (Autonomous)

## §0 — Read This First

Gate II v2.0 closed at 20/20 ACs but the verification work surfaced that the
brief's pipeline model was incomplete. Production emits:

```
classify → compose_bundle → plan_per_tool → tool_fetch (×N, up to 21 distinct tools) → synthesis → audit
```

The Gate II renderer was built for `planner → retrieval (4 sub-tools) → synthesis → audit`. The mismatch means three things in production:

1. **AuditStepDetail always renders a placeholder.** `loadAuditRow()` queries six columns that don't exist in `audit_events`; the `.catch` silently returns null. Every production query's Audit step shows `placeholder_note`.
2. **The lifecycle graph is misshapen.** `classify`, `compose_bundle`, `plan_per_tool` are not rendered (silently dropped). The Planner and Retrieval nodes are partly or fully empty.
3. **The tool universe is wrong.** The renderer's 4 named retrieval sub-rows can only describe 4 of the 21 actual production tools.

Gate II.5 fixes all three. Three new design decisions (D9–D11) are locked in §3. Everything else inherits from the original brief.

**This brief is designed to run unattended for 8–14 hours.** Same autonomous decision rules (§4.5 of original brief — R1–R9 — plus one addition R10 below). Same worktree, same branch, no merge until this closes.

---

## §1 — Entry Gates

All must pass before W1 begins. Executor runs these checks.

- [ ] `pwd` reports `/Users/Dev/Vibe-Coding/Apps/marsys-gate2-trace-align`
- [ ] `git branch --show-current` reports `feature/gate2-trace-pipeline-align`
- [ ] `git status` clean (no uncommitted changes)
- [ ] `git log -5 --oneline` shows the prior Gate II + fixup commits including 9f99d22
- [ ] `git pull --ff-only origin feature/gate2-trace-pipeline-align` succeeds
- [ ] `cd platform && ls node_modules` non-empty
- [ ] `npm test --silent --run` baseline — capture pass/fail count (this is the regression floor)
- [ ] `tsc --noEmit` baseline — capture pre-existing error count as the floor
- [ ] `npm run lint` baseline state captured
- [ ] Read `CLAUDECODE_BRIEF.md` (this file, copied to worktree root by §11)
- [ ] Read `99_ARCHIVE/BRIEFS_RETIRED/CLAUDECODE_BRIEF_GATE_II_v2_0.md` (predecessor, archived)
- [ ] Read `CLOSE_REPORT.md` §13 (post-close fixup) and `BLOCKERS.md`
- [ ] Read `GAP_ANALYSIS.md` §J in full
- [ ] Re-read original brief §3 (D1–D8) and §4.5 (R1–R9) — these still apply

**Cowork thread / conversation name to propose at first response:** `MARSYS Gate II.5 Exec — Production-State Alignment`

**If any entry gate fails:** write `BLOCKERS.md` (append, do not overwrite) at worktree root, halt.

---

## §2 — Scope

### may_touch

```
platform/src/components/trace/**
platform/src/components/consume/TraceDrawer.tsx          (thin shell only)
platform/src/lib/admin/trace_assembler.ts
platform/src/lib/admin/trace_client.ts
platform/src/lib/admin/trace_schema.ts
platform/src/app/api/admin/trace/[query_id]/**
platform/src/app/api/trace/stream/[queryId]/**
platform/tests/**                                        (trace + fixtures + e2e)
platform/supabase/migrations/045_*.sql                   (USE THIS SLOT per D11)
00_ARCHITECTURE/POST_GATE_II_FOLLOWUPS.md                (append-only)
00_ARCHITECTURE/CURRENT_STATE_v1_0.md                    (memory-correction footnote only — see W9)
CLAUDECODE_BRIEF.md                                      (this file)
CLOSE_REPORT.md
DISCOVERY_REPORT.md                                      (worktree root; W1 deliverable)
SESSION_NOTES_GATE_II_5.md                               (worktree root; running notes)
```

### must_not_touch

```
platform/src/lib/planner/**, platform/src/lib/retrieval/**,
platform/src/lib/synthesis/**, platform/src/lib/audit/**     (pipeline emitters; READ ONLY)
platform/src/components/consume/ConsumeChat.tsx
platform/src/components/consume/AnswerView.tsx
platform/src/components/consume/StreamingAnswer.tsx
platform/src/app/api/chat/consume/route.ts
platform/src/components/performance/**                       (Gate I territory)
platform/src/components/shared/AppShellRail.tsx              (Gate IV nav cleanup)
platform/src/components/shared/MobileNavSheet.tsx            (Gate IV nav cleanup)
platform/supabase/migrations/043_*, 044_*, 046_*             (other gates' ranges)
platform/src/lib/audit/audit_writer.ts (or wherever the audit writer lives)  (audit WRITE-path is a separate follow-up)
01_FACTS_LAYER/**, 025_HOLISTIC_SYNTHESIS/**, 06_LEARNING_LAYER/**
00_ARCHITECTURE/CANONICAL_ARTIFACTS_*.md, MACRO_PLAN_*.md, PROJECT_ARCHITECTURE_*.md
```

**No new npm packages without flagging in `BLOCKERS.md` and proceeding around it.**
**Playwright browsers may be downloaded via `npx playwright install` (runtime download, not an npm dep — allowed).**

---

## §3 — Locked Design Decisions (D1–D8 inherited; D9–D11 new)

D1–D8 from the original brief still apply. **Three new decisions for Gate II.5:**

| # | Topic | Decision |
|---|---|---|
| D9 | Stage taxonomy | **Use production names, grouped.** Lifecycle nodes in order: **Planning** [classify + compose_bundle + plan_per_tool inside, rendered as a container with 3 inline sub-step rows] → **Retrieval** [container with 21 tool_fetch sub-rows, see D10] → **Synthesis** → **Audit** → **Checkpoints** (collapsible group per D1). Stage discriminants in `trace_schema.ts` use the production names verbatim. |
| D10 | Tool universe | **All 21 production tools always rendered as sub-rows under Retrieval.** Sub-rows that did not fire in this query render dimmed (same treatment as D1's disabled checkpoints). Stable lifecycle shape across every query. The 21 tool names come from discovery (W1) — executor enumerates them from the retrieval orchestrator and the trace_steps DB table. |
| D11 | Audit fields | **Use migration 045** to ADD three nullable columns to `audit_events`: `disclosure_tier TEXT`, `b10_compliant BOOLEAN`, `b11_compliant BOOLEAN`. Non-destructive. Renderer reads the existing columns (`id`, `audit_status`, `audit_warnings`, plus whatever else discovery surfaces) AND the new nullable ones. Null values render as "—" with a tooltip ("not yet tracked — pending audit writer update"). The audit writer remains in must_not_touch — updating it to populate the new columns is a separate scoped follow-up. |

**On D1–D8 inheritance:** the lifecycle shape change in D9 supersedes D5's specific "single Retrieval node with 4 sub-rows" — D10 widens it to 21 sub-rows AND D9 adds the Planning supercontainer. All other D-decisions stand: D1 checkpoints, D2 latency display, D3 QueryPlan banner/Planner detail, D4 schema source-of-truth, D6 synthesis mode branching, D7 orphan deletions (already done), D8 supporting components (already done).

---

## §4 — Work Items

Execute in numbered order. Each work item commits at its end.

### W1 — Discovery (~90 min)

**Goal:** Produce `DISCOVERY_REPORT.md` at the worktree root with a complete picture of production state before writing any code.

**Steps:**

1. **Audit events schema.** Query the live audit_events schema:
   ```bash
   psql "$DATABASE_URL" -c "\d audit_events"
   ```
   Save the full column listing (name, type, nullable, default) to DISCOVERY_REPORT.md §A. Cross-reference with what `loadAuditRow()` currently queries — list every (a) column queried but missing, (b) column present but not queried.

2. **Production stage vocabulary.** Query the live trace_steps table:
   ```sql
   SELECT step_type, COUNT(*) AS occurrences, MIN(created_at) AS first_seen, MAX(created_at) AS last_seen
   FROM query_trace_steps
   WHERE created_at > NOW() - INTERVAL '14 days'
   GROUP BY step_type
   ORDER BY occurrences DESC;
   ```
   (Replace `query_trace_steps` with whatever the actual table name is — confirm from `trace_assembler.ts`.) Save to DISCOVERY_REPORT.md §B. Cross-reference with what trace_schema.ts currently declares as `PipelineStage` — list (a) stages emitted but not in schema, (b) stages in schema but not emitted.

3. **21-tool enumeration.** For tool_fetch steps, enumerate the distinct tool names:
   ```sql
   SELECT DISTINCT metadata->>'tool_name' AS tool_name, COUNT(*) AS occurrences
   FROM query_trace_steps
   WHERE step_type = 'tool_fetch'
     AND created_at > NOW() - INTERVAL '30 days'
   GROUP BY tool_name
   ORDER BY occurrences DESC;
   ```
   (Verify the actual JSON path of `tool_name` from inspecting a real row first — could be `metadata.tool`, `metadata.tool_name`, `metadata.name`.) Save to DISCOVERY_REPORT.md §C with the full list, counts, and execution frequency.

4. **Per-stage metadata shapes.** For each production stage (classify, compose_bundle, plan_per_tool, tool_fetch, synthesis, audit), pull one representative row and document its `metadata` JSON shape. Save to DISCOVERY_REPORT.md §D as a TypeScript interface sketch per stage.

5. **Existing renderer mismatch inventory.** Walk through every step-detail variant in `components/trace/` and document what it currently expects vs what the discovered production shape actually provides. Save to DISCOVERY_REPORT.md §E.

6. **compose_bundle confirmation.** Check the retrieval orchestrator / planner module for whether compose_bundle is the renamed ContextAssembly. Look for git history hints (`git log --all --diff-filter=R -- '**/context_assembly*' '**/compose_bundle*'`), the actual code that emits the step, and any comments referencing the rename. Save findings to DISCOVERY_REPORT.md §F. This unblocks W9 (memory correction).

7. Commit `DISCOVERY_REPORT.md`:
   ```
   git add DISCOVERY_REPORT.md
   git commit -m "Gate II.5 W1: production-state discovery report"
   ```

8. **Do NOT pause for native review.** Proceed directly to W2. The autonomous decision rules in §4.5 (especially R1, R2, R8) cover any ambiguity discovery surfaces.

---

### W2 — Migration 045 (~30 min)

**Goal:** Add the three nullable columns to `audit_events` per D11.

1. Author `platform/supabase/migrations/045_audit_events_disclosure_compliance.sql`:
   ```sql
   -- Migration 045: Gate II.5 — Add nullable disclosure + B10/B11 compliance columns
   -- to audit_events so AuditStepDetail can render the full audit context.
   --
   -- Non-destructive: adds nullable columns only. No data backfill.
   -- Audit writer updates to populate these columns are a SEPARATE follow-up
   -- (see POST_GATE_II_FOLLOWUPS.md FU.2 — to be authored in W9).
   --
   -- FK dependents enumerated via:
   --   SELECT conname, conrelid::regclass AS dependent_table
   --   FROM pg_constraint WHERE confrelid = 'audit_events'::regclass;
   -- (Document the result inline before merge)

   ALTER TABLE audit_events
     ADD COLUMN IF NOT EXISTS disclosure_tier TEXT,
     ADD COLUMN IF NOT EXISTS b10_compliant BOOLEAN,
     ADD COLUMN IF NOT EXISTS b11_compliant BOOLEAN;

   -- Down migration:
   -- ALTER TABLE audit_events
   --   DROP COLUMN IF EXISTS disclosure_tier,
   --   DROP COLUMN IF EXISTS b10_compliant,
   --   DROP COLUMN IF EXISTS b11_compliant;
   ```

2. Run the FK-dependents check and patch the comment header with results.

3. Apply the migration locally (Cloud SQL Auth Proxy must be running per §11):
   ```bash
   cd platform
   npm run db:migrate   # or whatever the project's migration command is
   psql "$DATABASE_URL" -c "\d audit_events"   # verify the three new columns
   ```

4. Commit:
   ```
   git add platform/supabase/migrations/045_audit_events_disclosure_compliance.sql
   git commit -m "Gate II.5 W2: migration 045 — audit_events disclosure + compliance columns"
   ```

---

### W3 — trace_schema.ts updates (~60 min)

**Goal:** Update the schema source-of-truth to use production names and the discovered metadata shapes.

1. Update `PipelineStage` union to match production discovery (W1 §B):
   ```typescript
   export type PipelineStage =
     | 'classify'
     | 'compose_bundle'
     | 'plan_per_tool'
     | 'tool_fetch'
     | 'synthesis'
     | 'audit'
     | 'checkpoint_4_5'
     | 'checkpoint_5_5'
     | 'checkpoint_8_5';
   ```
   Include any additional stages discovery surfaced.

2. Update `RetrievalSubTool` to enumerate all 21 production tools (from W1 §C). If the prior session used `string` (per the J.1 finding), now formalize it as a string literal union for type safety:
   ```typescript
   export type RetrievalSubTool =
     | 'vector_search'
     | 'cgm_graph_walk'
     | 'structured_sql'
     | 'hybrid_rank'
     // ... 17 more from W1 §C
     ;
   ```

3. Update per-stage metadata interfaces to match the W1 §D discovered shapes:
   - `ClassifyStepMetadata` — the classification output (query_class, confidence, reasoning if present)
   - `ComposeBundleStepMetadata` — the bundled context shape (signal counts, layer breakdown, etc.)
   - `PlanPerToolStepMetadata` — per-tool plan (tool name, plan, parameters, expected_count if present)
   - `ToolFetchStepMetadata` — per-tool execution (tool name, rows fetched, latency, hit rate, top score)
   - `SynthesisStepMetadata` — existing single_model / panel discriminated union; verify against discovery
   - `AuditStepMetadata` — combines existing columns + new nullable D11 columns:
     ```typescript
     export interface AuditStepMetadata {
       id: string;                       // existing audit_events.id
       audit_status: string;             // existing
       audit_warnings: string[] | null;  // existing
       disclosure_tier: string | null;   // new (D11)
       b10_compliant: boolean | null;    // new (D11)
       b11_compliant: boolean | null;    // new (D11)
       // ... plus any other existing columns discovery surfaced
     }
     ```

4. Update `AssembledTrace` if the discovery surfaced additional top-level fields.

5. The grouped lifecycle shape (Planning + Retrieval supercontainers) is a renderer concern; do NOT encode it in the schema. The schema reflects production emit; W4 + W5 do the grouping.

6. Commit:
   ```
   git commit -m "Gate II.5 W3: trace_schema aligned with production stages + 21-tool universe + audit fields"
   ```

---

### W4 — trace_assembler.ts realignment (~90 min)

**Goal:** The assembler maps production trace_steps rows + audit_events rows into AssembledTrace correctly.

1. **Fix `loadAuditRow()`**: replace the broken query with one that selects the actual columns from `audit_events`:
   ```sql
   SELECT id, audit_status, audit_warnings, disclosure_tier, b10_compliant, b11_compliant
   FROM audit_events WHERE query_id = $1
   ```
   (Include any additional columns discovery surfaced.) Remove the `.catch` that silently returned null — let errors propagate, but handle the legitimate "no audit_events row yet" case as a defined empty state, not as a silent null.

2. **Stage row mapping**: handle every production stage from W1 §B. For each row, build the corresponding TraceStep with `stage: <production_name>` and metadata typed per W3.

3. **plan_per_tool**: each row is its own TraceStep; the lifecycle grouping (under "Planning") is the renderer's concern, not the assembler's.

4. **tool_fetch handling**: every tool_fetch row becomes a TraceStep with `stage: 'tool_fetch'` and `metadata.tool_name` populated. The renderer (W5) groups them under the Retrieval container.

5. **Unknown stage handling**: per §4.5 R1 — if a row's step_type is not in the PipelineStage union (e.g., a future stage we haven't accounted for), render it as a TraceStep with `stage: 'unknown'` and the raw step_type in metadata. Do NOT throw.

6. **`satisfies` discipline**: all returned objects use `satisfies AssembledTrace`, not `as`.

7. Run trace_assembler tests; fix any fixture mismatches.

8. Commit:
   ```
   git commit -m "Gate II.5 W4: trace_assembler aligned with production stages + audit_events fix"
   ```

---

### W5 — LifecycleGraph realignment (~150 min)

**Goal:** Render the grouped shape from D9 + D10.

1. **New rendering pattern: StageContainer.** Both Planning and Retrieval are containers with inline sub-rows. Author a `StageContainer.tsx` (or similar reusable component under `components/trace/`) that:
   - Renders a container header row (label, status badge, optional total latency summary if applicable per D2)
   - Renders inline child sub-rows (no separate panel; same dimmed-when-skipped pattern as D1's checkpoints expanded view)
   - Supports both step-children (clickable rows that open a step-detail panel) and metadata-only children

2. **LifecycleGraph node sequence** (top-level nodes, in order):
   - **Planning** (StageContainer with 3 inline sub-rows: classify, compose_bundle, plan_per_tool)
   - **Retrieval** (StageContainer with 21 inline sub-rows, one per production tool from W1 §C; sub-rows dim if not fired in this query)
   - **Synthesis** (single node)
   - **Audit** (single node)
   - **Checkpoints** (collapsible group per D1 — already implemented; verify it still works under the new structure)

3. **Keyboard navigation + a11y**: preserve focus order through the new structure. Screen-reader labels updated to use production stage names.

4. **No per-step latency on lifecycle nodes** (D2 still holds). Total wall-clock pill stays on the drawer header (W5 of original brief).

5. Commit:
   ```
   git commit -m "Gate II.5 W5: LifecycleGraph realigned to grouped production shape"
   ```

---

### W6 — Step-detail variants realignment (~150 min)

**Goal:** Every clickable lifecycle row opens a step-detail panel with correct, populated content.

1. **Restructure step-detail registry**: the old `PlannerStepDetail` + `RetrievalStepDetail` + etc. need to map onto the new stage taxonomy. Recommended structure:
   - `ClassifyStepDetail.tsx` — renders query_class, confidence, reasoning per discovery
   - `ComposeBundleStepDetail.tsx` — renders bundled context summary (signal counts, layer breakdown)
   - `PlanPerToolStepDetail.tsx` — renders per-tool plan + parameters + expected count
   - `ToolFetchStepDetail.tsx` — renders rows fetched, latency, hit rate, top score per tool (one tool per panel)
   - `SynthesisStepDetail.tsx` — discriminated render on `mode: 'single_model' | 'panel'` (already implemented; verify)
   - `AuditStepDetail.tsx` — renders the full new AuditStepMetadata shape:
     - audit_status as a status pill (green/yellow/red based on value)
     - audit_warnings as a warnings list
     - disclosure_tier as a badge (if null: "—" with tooltip "not yet tracked — pending audit writer update")
     - b10_compliant + b11_compliant as compliance badges (null → "—" with same tooltip)
     - audit_event_id (the `id` column) as a copyable ID pill

2. **Delete `ClassifyStepDetail` and `ContextAssemblyStepDetail` if they still exist** in their pre-Gate-II form (the original brief said delete them; ContextAssembly's renamed-but-preserved nature complicates this — author NEW `ClassifyStepDetail` and `ComposeBundleStepDetail` aligned with production rather than reviving the old ones). The deleted ones in Gate II v2.0 stay deleted; what we author now is structurally new code under the same or similar filenames.

3. **All step-detail variants must**:
   - Show step latency in the metadata section (D2)
   - Import their type contracts from `trace_schema.ts`
   - Gracefully handle null/missing fields (D11's nullable audit columns especially — see R10 below)

4. **QueryPlan banner (D3)**: re-source the banner from the `classify` step's metadata if `query_plan` is not a top-level AssembledTrace field. If discovery showed `query_plan` is still produced separately, leave banner sourcing as-is. Document the choice in SESSION_NOTES_GATE_II_5.md.

5. **Registry / dynamic-import map**: update the step-detail-component registry so that clicking a lifecycle sub-row resolves to the correct component.

6. Commit:
   ```
   git commit -m "Gate II.5 W6: step-detail variants realigned for production taxonomy"
   ```

---

### W7 — Supporting trace components (~60 min)

**Goal:** Re-audit HealthRail, QueryDNAPanel, RetrievalScorecard against the new taxonomy.

The original Gate II already audited these (W6 of v2.0). With the taxonomy now widening from 4 to ~6+ stages and from 4 to 21 retrieval tools, re-audit:

1. **HealthRail**: any anomaly detectors keyed on stage names need to map to the new vocabulary. If detectors were named `plannerStallDetector` / `retrievalSlowDetector`, rename to match (`classifyStallDetector`, `toolFetchSlowDetector`, etc.) — or rename to be stage-agnostic (`stageLatencyDetector` parameterized by stage). Verify no external consumers depend on old names.

2. **QueryDNAPanel**: if it visualizes the pipeline shape, regenerate the shape from the new taxonomy. The "DNA" representation should encode the production stage sequence, not the brief's 4 stages.

3. **RetrievalScorecard**: per-tool variance across 21 tools should be visible. Single-aggregate metrics that mask the long tail need to be re-thought; at minimum, show "tools fired" (count of distinct tools), and a top-N scoring view.

4. Add a top-of-file comment to each touched file: `// Realigned for production state 2026-05-13 (Gate II.5 W7).`

5. Commit:
   ```
   git commit -m "Gate II.5 W7: supporting trace components realigned"
   ```

---

### W8 — Visual smoke spec (author + run) (~90 min)

**Goal:** Close BLOCKERS.md §B.1. Author the Playwright spec that was missing in the prior fixup; run it.

1. Confirm Playwright is installed (`grep '"@playwright/test"' platform/package.json`). If yes, proceed. If no: flag in BLOCKERS.md, skip the spec authoring; do API-only smoke instead.

2. Author `platform/tests/e2e/gate_ii_trace_smoke.spec.ts`:
   - Test name: `gate-ii-trace-smoke renders production pipeline correctly`
   - Auth strategy: in priority order
     - Use `playwright.config.*` globalSetup / storageState if one exists
     - Use `SMOKE_SESSION_COOKIE` env var if present (set via `await context.addCookies(...)`)
     - Use `TEST_SUPER_ADMIN_EMAIL` + `TEST_SUPER_ADMIN_PASSWORD` env vars to perform a login flow at test start
     - If none available: skip the test with `test.skip()` and a clear message
   - Steps:
     1. Navigate to `/clients/<test-client-id>/consume` (use whatever test client id the project uses; check existing e2e tests for the pattern)
     2. Submit a known golden-set query
     3. Wait for streaming answer to begin
     4. Open the trace drawer (find the trace toggle button by stable test id or accessible name)
     5. Wait for lifecycle graph to render
     6. Screenshot the entire drawer → `drawer_full.png`
     7. Screenshot the sticky QueryPlan banner → `banner.png`
     8. Verify and screenshot: Planning container with 3 sub-rows visible → `planning_container.png`
     9. Verify and screenshot: Retrieval container with 21 sub-rows visible (dimmed for not-fired) → `retrieval_container.png`
     10. Verify and screenshot: Checkpoints group expanded → `checkpoints_expanded.png`
     11. Click into each step-detail panel and screenshot: planner_step.png, classify_step.png, compose_bundle_step.png, plan_per_tool_step.png, tool_fetch_step.png, synthesis_step.png, audit_step.png

3. Run the spec:
   ```bash
   cd platform
   npx playwright install chromium --with-deps 2>&1 | tail -5
   <auth env vars> npx playwright test gate_ii_trace_smoke --reporter=list --workers=1
   ```

4. If the run produces screenshots: save to `platform/tests/screenshots/gate_ii_smoke/` and write a README.md listing each file + the reviewer checklist.

5. If the run fails on auth: document the exact missing env vars in CLOSE_REPORT §14; do NOT commit speculative auth code.

6. Commit:
   ```
   git add platform/tests/e2e/gate_ii_trace_smoke.spec.ts
   git add platform/tests/screenshots/gate_ii_smoke/ 2>/dev/null
   git commit -m "Gate II.5 W8: Playwright smoke spec authored + run"
   ```

---

### W9 — Memory + governance correction (~30 min)

**Goal:** Correct the project-state record that compose_bundle is functionally context-assembly under a new name (per W1 §F).

1. **Author follow-up FU.2** in `00_ARCHITECTURE/POST_GATE_II_FOLLOWUPS.md` (append, do not overwrite FU.1):
   ```markdown
   ## FU.2 — Audit writer column population

   **Source:** Gate II.5 W2 (migration 045) added `disclosure_tier`,
   `b10_compliant`, `b11_compliant` as nullable columns to `audit_events`.
   The audit writer (must_not_touch in this session) does not yet populate
   them. AuditStepDetail renders them as "—" with a "not yet tracked"
   tooltip.

   **Status:** DEFERRED — separate scoped session required.

   **When-Then:**
   WHEN the project decides to track disclosure tier + B.10/B.11 compliance
   per audit event
   THEN scope a session that touches the audit writer (currently must_not_touch)
   and adds population logic. Estimated effort: 2–4 hours including tests
   and a sample backfill.

   ## FU.3 — compose_bundle naming + memory correction

   **Source:** Gate II.5 W1 §F discovery confirmed that `compose_bundle` is
   functionally what was called "ContextAssembly" before Pipeline-Transform-S1
   (2026-05-11). The transform retired the `CONTEXT_ASSEMBLY_ENABLED` feature
   flag but renamed and preserved the underlying stage.

   **Status:** Documentation correction needed in:
   - Native's MEMORY.md (the user-tier memory note claiming
     "CONTEXT_ASSEMBLY_ENABLED removed Pipeline-Transform-S1" needs a
     "renamed to compose_bundle" footnote)
   - CLAUDE.md §F if it carries the same claim
   - 00_ARCHITECTURE/CURRENT_STATE_v1_0.md if relevant

   This brief touches 00_ARCHITECTURE/CURRENT_STATE_v1_0.md in W9 only to
   add a footnote. The native MEMORY.md correction is surfaced for native
   action in §12 post-session review (this session cannot touch user-tier
   memory files).
   ```

2. **Update `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` ONLY** with a one-paragraph correction footnote in §2 or wherever the pipeline architecture is described:
   ```markdown
   > **Production-state correction (2026-05-13, Gate II.5 W9):** The stage
   > previously called "context_assembly" was not removed in Pipeline-
   > Transform-S1 (2026-05-11). The feature flag `CONTEXT_ASSEMBLY_ENABLED`
   > was retired, but the underlying step was renamed to `compose_bundle`
   > and continues to emit in production trace_steps. See Gate II.5
   > DISCOVERY_REPORT.md §F.
   ```

3. **Do NOT modify** MEMORY.md, CLAUDE.md, CANONICAL_ARTIFACTS, MACRO_PLAN, or PROJECT_ARCHITECTURE. Those are out of scope (per §2 must_not_touch). The native applies any further corrections manually in §12.

4. Commit:
   ```
   git add 00_ARCHITECTURE/POST_GATE_II_FOLLOWUPS.md 00_ARCHITECTURE/CURRENT_STATE_v1_0.md
   git commit -m "Gate II.5 W9: POST_GATE_II_FOLLOWUPS appended; CURRENT_STATE compose_bundle footnote"
   ```

---

### W10 — Test coverage (~120 min)

**Goal:** Fixtures and tests reflect the new schema, taxonomy, and renderers.

1. **Regenerate golden fixtures** for `trace_assembler.test.ts`:
   - Planning-only fixture (3 sub-stages emitted, no retrieval)
   - Planning + Retrieval (subset of 21 tools fired)
   - Planning + Retrieval (all 21 tools fired)
   - Full pipeline with single-model synthesis
   - Full pipeline with panel synthesis (forward-compat fixture)
   - Full pipeline with audit columns null (D11 new columns empty)
   - Full pipeline with audit columns populated (synthetic future state)
   - Full pipeline with all 3 checkpoints fired
   - Full pipeline with no checkpoints fired
   - Pipeline with unknown stage in rows (verify R1 graceful render)

2. **trace_schema.test.ts** type-level tests:
   - PipelineStage union exhaustiveness
   - RetrievalSubTool covers all 21 declared tools
   - AuditStepMetadata discriminated render

3. **Component snapshot tests** for each step-detail variant (one per stage type).

4. **LifecycleGraph component tests**:
   - All-21-tools-rendered with subset fired → assert 21 sub-rows present, dim state correct
   - All-3-Planning-sub-stages rendered → assert Planning container with 3 inline rows
   - Audit step with null disclosure_tier → assert "—" placeholder + tooltip

5. **QueryPlan banner test**: source from classify step metadata; render correctly.

6. **Regression bar**:
   ```bash
   cd platform
   npm test --silent --run
   npx tsc --noEmit
   npm run lint
   ```
   No new failures beyond the Phase A baseline.

7. **Vitest mock pattern**: `mockImplementation(function() { ... })`, not arrow functions.

8. Commit:
   ```
   git commit -m "Gate II.5 W10: test coverage for production-state taxonomy"
   ```

---

### W11 — Re-run J.2 live verification (~30 min)

**Goal:** Re-execute the live DB spot-check from prior fixup §B.2, now that loadAuditRow + AuditStepDetail are fixed.

1. Cloud SQL Auth Proxy is running per §11 prerequisite.
2. Find a recent query_id with an audit_events row (same query as the prior fixup if still available — query_id 5067ea2a-… or similar).
3. Curl `/api/admin/trace/<query_id>` with admin auth.
4. Inspect the Audit step in the response:
   - `metadata.audit_status` — real value (not null, not placeholder)
   - `metadata.audit_warnings` — array (possibly empty)
   - `metadata.disclosure_tier`, `metadata.b10_compliant`, `metadata.b11_compliant` — null is acceptable (writer hasn't populated yet), but the field must be present
   - `metadata.id` — real UUID
5. Save the response to `platform/tests/fixtures/gate_ii_5_j2_live_verification.json`.
6. Update CLOSE_REPORT.md §14 W11 with the verification result.
7. Commit:
   ```
   git commit -m "Gate II.5 W11: J.2 live verification — audit JOIN populated"
   ```

---

## §4.5 — Autonomous Decision Rules (R1–R9 inherited; R10 new)

R1–R9 from original brief §4.5 still apply. **One addition:**

**R10 — Null nullable-column rendering.**
When a D11 column (disclosure_tier, b10_compliant, b11_compliant) is null because the audit writer has not yet been updated to populate it:
- Render the field as "—" (em-dash)
- Attach a tooltip: "Not yet tracked — pending audit writer update (POST_GATE_II_FOLLOWUPS.md FU.2)"
- Do NOT hide the field; the field's absence would imply it doesn't exist, which is misleading
- The tooltip pattern is `<span title="...">—</span>` or your design system's equivalent

---

## §5 — Acceptance Criteria

All checked off in the session-close artifact.

- [ ] **AC.1** DISCOVERY_REPORT.md exists at worktree root, committed, with sections §A–§F populated
- [ ] **AC.2** Migration 045 applied locally; `\d audit_events` shows the three new nullable columns
- [ ] **AC.3** trace_schema.ts PipelineStage union uses production names (classify, compose_bundle, plan_per_tool, tool_fetch, synthesis, audit + checkpoint_*)
- [ ] **AC.4** trace_schema.ts RetrievalSubTool enumerates all 21 production tools (from DISCOVERY §C)
- [ ] **AC.5** trace_schema.ts AuditStepMetadata includes existing + 3 new nullable columns
- [ ] **AC.6** loadAuditRow() queries the actual audit_events columns; no silent .catch returning null
- [ ] **AC.7** LifecycleGraph renders the grouped shape: Planning [3 inline sub-rows] → Retrieval [21 inline sub-rows] → Synthesis → Audit → Checkpoints
- [ ] **AC.8** Each clickable sub-row opens the correct step-detail panel with populated metadata
- [ ] **AC.9** AuditStepDetail renders audit_status, audit_warnings, plus disclosure_tier/b10/b11 (null → "—" with tooltip)
- [ ] **AC.10** HealthRail, QueryDNAPanel, RetrievalScorecard updated for new taxonomy and 21-tool universe
- [ ] **AC.11** Playwright spec authored at `platform/tests/e2e/gate_ii_trace_smoke.spec.ts`; run succeeded OR failure documented with exact env-var requirements for native re-run
- [ ] **AC.12** Screenshots saved to `platform/tests/screenshots/gate_ii_smoke/` with README.md (if W8 run succeeded)
- [ ] **AC.13** `00_ARCHITECTURE/POST_GATE_II_FOLLOWUPS.md` appended with FU.2 (audit writer follow-up) and FU.3 (compose_bundle / memory correction)
- [ ] **AC.14** `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` carries the compose_bundle correction footnote
- [ ] **AC.15** `npm test --silent --run` — no NEW failures beyond Phase A baseline
- [ ] **AC.16** `npx tsc --noEmit` — no NEW TS errors beyond baseline
- [ ] **AC.17** `npm run lint` — no NEW lint errors beyond baseline
- [ ] **AC.18** W11 J.2 live verification: audit JOIN returns real values for a recent query_id; fixture saved
- [ ] **AC.19** No files touched outside §2 may_touch; must_not_touch list respected
- [ ] **AC.20** CLAUDECODE_BRIEF.md (this file) moved to `00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_GATE_II_5_v1_0.md` with frontmatter `status: COMPLETE`
- [ ] **AC.21** SESSION_LOG.md entry appended
- [ ] **AC.22** BLOCKERS.md either absent OR contains only documented (non-fatal) items with re-run instructions
- [ ] **AC.23** Final commit pushed to `origin/feature/gate2-trace-pipeline-align`
- [ ] **AC.24** CLOSE_REPORT.md §14 (Gate II.5 results) appended

---

## §6 — LLM Stack

No production LLM calls. Same rules as predecessor:
- Default: gemini-2.5-pro
- Non-critical: gemini-2.0-flash-lite or deepseek-chat
- BANNED: anthropic/* — flag if seen in any touched file

---

## §7 — Migration Numbers

- Migration 045 (Gate II's reserved slot): **NOW USED** per D11. Non-destructive (nullable ADD only).
- Do not touch 043, 044, 046.

---

## §8 — Project Rules (encoded reminders)

- **B.10:** trace data must not contain LLM-fabricated chart values — flag if seen, do not silently fix.
- **B.11:** trace renderings must not imply synthesis bypassed L2.5.
- **ROOT_FILE_POLICY:** CLAUDECODE_BRIEF.md (this file) is the only file at project root for the session duration; moves to `00_ARCHITECTURE/briefs/` at close (AC.20).
- **GCS URIs:** unlikely in trace code; if hit, read GCS_LAYOUT first.
- **Vitest mocks:** `mockImplementation(function() {...})`, not arrows.
- **FK enumeration before DELETE in migration 045:** migration 045 is ADD-only (non-destructive); FK enumeration documented in the migration comment header for governance compliance.

---

## §9 — Session Close Checklist

Executor runs autonomously at session end.

1. All AC.1–AC.24 evaluated with pass/fail and committed to CLOSE_REPORT.md §14
2. `npm test --silent --run` final count vs baseline delta
3. `tsc --noEmit` delta
4. `npm run lint` delta
5. W11 fixture saved at `platform/tests/fixtures/gate_ii_5_j2_live_verification.json`
6. W8 screenshots present (if W8 succeeded) at `platform/tests/screenshots/gate_ii_smoke/`
7. `git status` clean
8. DISCOVERY_REPORT.md, SESSION_NOTES_GATE_II_5.md, optionally BLOCKERS.md committed
9. CLAUDECODE_BRIEF.md moved to `00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_GATE_II_5_v1_0.md` with `status: COMPLETE`, `closed_on: YYYY-MM-DD`
10. `00_ARCHITECTURE/SESSION_LOG.md` entry appended
11. `git push origin feature/gate2-trace-pipeline-align`
12. Stop any background services (proxy, dev server) that THIS session started
13. Print final summary to stdout:
    ```
    Gate II.5 closed at <UTC>. {N}/24 ACs pass. {M} blockers.
    Production stages aligned. 21 tools rendered. Audit columns fixed.
    See CLOSE_REPORT.md §14 for details.
    ```

---

## §10 — Out of Scope (explicit non-goals)

- Modifying the audit writer to populate disclosure_tier / b10_compliant / b11_compliant (FU.2 — separate session)
- Modifying any pipeline emitter (planner, retrieval orchestrator, synthesis, audit writer, checkpoints)
- Modifying ConsumeChat / AnswerView / StreamingAnswer or the consume API route
- Modifying MEMORY.md or CLAUDE.md or CANONICAL_ARTIFACTS / MACRO_PLAN / PROJECT_ARCHITECTURE (compose_bundle correction is surfaced to §12 native)
- Nav items (Gate IV)
- Performance Command Center (Gate I)
- Intelligent Chat Interface (Gate III)
- Creating the merge PR (still deferred per OPUS_PLANNING_SESSION §9 merge sequence)
- Panel-mode trace emission validation (FU.1 — when emitter activates)
- L5+ / M5 work

---

## §11 — Manual Prerequisites (BEFORE session kickoff — native runs once)

The native runs this block in Terminal before triggering the executor session. After this completes, the executor handles the rest.

```bash
# Step 1 — Verify Gate II worktree state
cd /Users/Dev/Vibe-Coding/Apps/marsys-gate2-trace-align
git status                          # must be clean
git branch --show-current           # must be feature/gate2-trace-pipeline-align
git pull --ff-only origin feature/gate2-trace-pipeline-align

# Step 2 — Copy the Gate II.5 brief into the worktree as CLAUDECODE_BRIEF.md
cp /Users/Dev/Vibe-Coding/Apps/Madhav/CLAUDECODE_BRIEF_GATE_II_5.md \
   /Users/Dev/Vibe-Coding/Apps/marsys-gate2-trace-align/CLAUDECODE_BRIEF.md

# Step 3 — Commit the brief on the feature branch
git add CLAUDECODE_BRIEF.md
git commit -m "Gate II.5: install autonomous execution brief v1.0"

# Step 4 — Start Cloud SQL Auth Proxy (REQUIRED — Gate II.5 needs DB access)
# Use whatever command your project uses; common patterns:
#   scripts/start-proxy.sh         &
#   make proxy                     &
#   cloud-sql-proxy <CONN_NAME>    &
# Verify the proxy is listening:
psql "$DATABASE_URL" -c "SELECT 1;"

# Step 5 — (Optional but strongly recommended for W8 visual smoke)
#         Set one of these auth env-vars so Playwright can run unattended:
#   export SMOKE_SESSION_COOKIE="<value from authenticated browser session>"
#   # OR
#   export TEST_SUPER_ADMIN_EMAIL="<email>"
#   export TEST_SUPER_ADMIN_PASSWORD="<password>"
# Without these, W8 will gracefully skip and surface a re-run command in
# CLOSE_REPORT.

# Step 6 — Launch Claude Code in the worktree with permissions disabled
cd /Users/Dev/Vibe-Coding/Apps/marsys-gate2-trace-align
claude --dangerously-skip-permissions
# Then paste the trigger prompt.
```

---

## §12 — Manual Post-Session Review (AFTER executor completes)

```bash
# Step 1 — Pull the worktree state
cd /Users/Dev/Vibe-Coding/Apps/marsys-gate2-trace-align
git fetch origin
git log -1 --oneline

# Step 2 — Read CLOSE_REPORT.md §14
cat CLOSE_REPORT.md | sed -n '/^## §14 /,/^## §/p'

# Step 3 — Read DISCOVERY_REPORT.md end-to-end (esp. §F compose_bundle finding)
cat DISCOVERY_REPORT.md
```

Review actions:

1. **Visual confirmation**: open `platform/tests/screenshots/gate_ii_smoke/` and walk through each screenshot against the README.md reviewer checklist.
2. **If W8 was skipped** (no auth env vars): set the env vars per the CLOSE_REPORT re-run instructions and run the Playwright spec manually:
   ```bash
   cd platform
   <env vars> npx playwright test gate_ii_trace_smoke --reporter=list
   ```
3. **MEMORY.md correction** (cannot be done by the executor): update the memory note that incorrectly states ContextAssembly was removed in Pipeline-Transform-S1. The accurate note is "ContextAssembly was renamed to compose_bundle and preserved; only the feature flag was retired." Use whatever memory-update tool / interface this project uses.
4. **CLAUDE.md spot-check**: search for the same "ContextAssembly removed" claim and apply the same correction if present.
5. **Merge decision**: once visual smoke is confirmed and corrections are applied, Gate II's branch is ready to merge. Hold until Gates I and III also close, then run the merge sequence in `00_ARCHITECTURE/briefs/OPUS_PLANNING_SESSION_v2_0.md §9`.

---

*End of CLAUDECODE_BRIEF — Gate II.5: Production-State Alignment v1.0*
*Designed by Claude Opus 4.7 — 2026-05-13*
*Eleven design decisions locked (D1–D8 inherited + D9–D11 new). Single-session overnight autonomous run, same worktree as Gate II v2.0, merge-blocking.*
