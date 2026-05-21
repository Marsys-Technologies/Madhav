---
artifact: CLAUDECODE_BRIEF_MCP_0_AUTHOR_v1_0.md
type: CLAUDECODE_BRIEF
version: 1.0
status: PENDING
authored_by: Cowork 2026-05-21
authored_at: 2026-05-21
session_id: MCP-0-AUTHOR
session_name: MCP-0-AUTHOR — Brief authoring meta-session
executor: Claude Code sub-agent (general-purpose, spawned by MCP Conductor)
execution_mode: single autonomous session, --dangerously-skip-permissions
worktree:
  name: MadhavMCP
  branch: feature/mcp-server
  base: main
  path_absolute: /Users/Dev/Vibe-Coding/Apps/MadhavMCP
governing_plan: 00_ARCHITECTURE/BRIEFS/MCP_BRIEF_v1_0.md
reference_brief: 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCP_1_S1_v1_0.md
predecessor_session: (none — first in queue)
next_session_anticipated: MCP-1-S1 (foundation)
---

# CLAUDECODE_BRIEF — MCP-0-AUTHOR
## Brief authoring meta-session: author the 7 remaining sub-briefs

---

## §0 — How to start this session

You are a sub-agent spawned by the MCP Conductor. Your context is fresh.
You are in the MadhavMCP worktree at `/Users/Dev/Vibe-Coding/Apps/MadhavMCP`
on branch `feature/mcp-server`. The Conductor has already pasted your
session prompt; you are now reading this brief.

This is a **governance-only session**. You do NOT touch application code.
You author 7 markdown briefs under `00_ARCHITECTURE/BRIEFS/`.

---

## §1 — Session identity

| Field | Value |
|---|---|
| Session ID | MCP-0-AUTHOR |
| Branch | `feature/mcp-server` |
| Worktree path | `/Users/Dev/Vibe-Coding/Apps/MadhavMCP` |
| Execution mode | Single autonomous session, `--dangerously-skip-permissions` |
| Type | Governance / authoring only (no code) |
| Predecessor | (none — first in queue) |
| Anticipated next | MCP-1-S1 (foundation — already authored, you do not touch it) |

---

## §2 — Mandatory reads at session open (in order)

1. `CLAUDE.md` (§C mandatory list — full read)
2. `00_ARCHITECTURE/BRIEFS/MCP_BRIEF_v1_0.md` — **full read**; this is the
   master brief whose Phase MCP-1 through MCP-5 sections you will translate
   into per-session execution briefs
3. `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCP_1_S1_v1_0.md` — **full read**;
   this is the gold-standard reference brief. Every brief you author MUST
   match its structure (frontmatter shape, §0–§6 sections, level of detail,
   commit cadence, gate command in §6, scope constraints in §5)
4. `00_ARCHITECTURE/CONDUCTOR/session_queue_MCP.yaml` — **full read**;
   confirms which sessions you author, their dependency chain, their gate
   commands (you must align the briefs' §6 acceptance criteria with the
   queue's gate_command for each session)

Optional but recommended for style alignment:
- One existing sibling brief: `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_PHASE_4C_1_S1_v1_0.md`
  (Phase 4C-1-S1 — closest match in style to what you're authoring)

---

## §3 — Scope (7 briefs to author, in order)

Each brief sits at `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_<session_id>_v1_0.md`.
Each must include exactly these sections:

- Frontmatter (see §3.0 below for required keys)
- §0 — How to start this session
- §1 — Session identity
- §2 — Mandatory reads at session open
- §3 — Scope (numbered items; each item has **What**, **AC.ID**, **Why**;
  brief instructs sub-agent to commit after each item)
- §4 — Session-open handshake (boilerplate referencing
  `SESSION_OPEN_TEMPLATE_v1_0.md`)
- §5 — Scope constraints (`may_touch`, `must_not_touch` exact path lists)
- §6 — Session-close checklist (FINAL_SUMMARY block template)

### §3.0 — Frontmatter contract (every brief)

```yaml
---
artifact: CLAUDECODE_BRIEF_<session_id>_v1_0.md
type: CLAUDECODE_BRIEF
version: 1.0
status: PENDING
authored_by: Claude Code sub-agent (MCP-0-AUTHOR)
authored_at: <ISO date — today>
session_id: <session_id>
session_name: <one-line human description>
executor: Claude Code sub-agent (general-purpose, spawned by MCP Conductor)
execution_mode: single autonomous session, --dangerously-skip-permissions
worktree:
  name: MadhavMCP
  branch: feature/mcp-server
  base: main
  path_absolute: /Users/Dev/Vibe-Coding/Apps/MadhavMCP
governing_plan: 00_ARCHITECTURE/BRIEFS/MCP_BRIEF_v1_0.md
reference_brief: 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCP_1_S1_v1_0.md
predecessor_session: <prior session_id>
next_session_anticipated: <next session_id or "MCP-MERGE">
---
```

### §3.1 — Brief 1: CLAUDECODE_BRIEF_MCP_2_S1_v1_0.md

**Session:** MCP-2-S1 — MCP server scaffold (`platform-mcp/`) + Tier-1/2 tools

**Source:** MCP_BRIEF_v1_0.md §5.1 (file structure), §5.2 (data flow), §5.5
(Cloud Run deployment), §5.6 (service-to-service auth), §7.2 (Phase MCP-2
scope and acceptance criteria — note S2 split: this is the engineering
half; resources + tool descriptions land in S2 next session)

**Scope items the brief should specify (each as §3 item with AC.MCP_2_S1.N):**

1. Initialize `platform-mcp/` Node project with `package.json` (Node 20, TypeScript, ESM), `tsconfig.json`, `Dockerfile`, `.gcloudignore`
2. Install `@modelcontextprotocol/sdk` and dependencies
3. Author `platform-mcp/src/server.ts` — HTTP/SSE server entry point
4. Author `platform-mcp/src/client.ts` — calls to `/api/mcp/execute` and `/api/mcp/plan` on platform via Cloud Run service-to-service identity token
5. Author `platform-mcp/src/types.ts` — shared types (envelope, plan, etc.)
6. Author `platform-mcp/src/tools/ask_madhav.ts` — Tier 1 end-to-end tool (descriptions are placeholder; full §4.6-standard descriptions land in MCP-2-S2)
7. Author `platform-mcp/src/tools/plan_query.ts` — Tier 2 plan inspection
8. Author `platform-mcp/src/tools/execute_plan.ts` — Tier 2 explicit execution; re-validates plan against PipelinePlanSchema
9. Author `platform-mcp/cloudbuild.yaml` — Cloud Run deploy config for `amjis-mcp` service in `asia-south1`
10. Author `platform-mcp/README.md` (skeleton — populated through later sessions)
11. Verify `npx tsc --noEmit` passes in `platform-mcp/`

**Gate command (must match session_queue_MCP.yaml exactly):**
```
cd /Users/Dev/Vibe-Coding/Apps/MadhavMCP &&
test -f platform-mcp/package.json &&
test -f platform-mcp/src/server.ts &&
test -f platform-mcp/src/tools/ask_madhav.ts &&
test -f platform-mcp/src/tools/plan_query.ts &&
test -f platform-mcp/src/tools/execute_plan.ts &&
test -f platform-mcp/Dockerfile &&
test -f platform-mcp/cloudbuild.yaml &&
cd platform-mcp && npx tsc --noEmit
```

**may_touch:** `platform-mcp/**`, `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCP_2_S1_v1_0.md` (status flip)
**must_not_touch:** `platform/**` (all platform-side endpoints exist already from MCP-1-S1), `01_FACTS_LAYER/**`, `025_HOLISTIC_SYNTHESIS/**`, other workstreams' files

### §3.2 — Brief 2: CLAUDECODE_BRIEF_MCP_2_S2_v1_0.md

**Session:** MCP-2-S2 — Tool descriptions (§4.6 standard) + MCP resources

**Source:** MCP_BRIEF §4.5 (resources), §4.6 (tool description standard),
§7.2 acceptance criteria AC.2.5–AC.2.7

**Scope items:**

1. Author §4.6-standard descriptions for `ask_madhav`, `plan_query`, `execute_plan`
   (≥120 words each, all 5 blocks present)
2. Draft `platform-mcp/resources/chart-overview.md` — compact summary of
   Abhisek's chart per MCP_BRIEF §4.5.1 (≥500 words, ~600-1000 target).
   Sub-agent reads `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md` for
   source data. Native edits post-merge for polish.
3. Draft `platform-mcp/resources/house-rules.md` — operating manual per
   MCP_BRIEF §4.5.2 (≥300 words, ~400-600 target). Sub-agent reads CLAUDE.md
   §A, §J, and PROJECT_ARCHITECTURE §B for source guidance. Native edits
   post-merge.
4. Author `platform-mcp/src/resources/index.ts` — MCP resource registration
   that serves the two markdown files
5. Verify `npx tsc --noEmit` passes

**Gate command (must match queue):** see session_queue_MCP.yaml MCP-2-S2 entry.

**may_touch:** `platform-mcp/resources/**`, `platform-mcp/src/resources/**`,
`platform-mcp/src/tools/{ask_madhav,plan_query,execute_plan}.ts` (descriptions
update only, not behavior)
**must_not_touch:** `platform/**`, `01_FACTS_LAYER/**` (read only for content
sourcing), `025_HOLISTIC_SYNTHESIS/**`

### §3.3 — Brief 3: CLAUDECODE_BRIEF_MCP_3_S1_v1_0.md

**Session:** MCP-3-S1 — 10 surgical primitives + dispatcher

**Source:** MCP_BRIEF §4.1 Tier 3 (the 10 primitives), §5.3 (data flow for
primitives), §7.3 acceptance criteria

**Scope items:**

1. Author `platform/src/app/api/mcp/primitives/[tool]/route.ts` — generic
   dispatcher that authenticates, validates, calls `getTool(toolName)`, runs
   tool with `surgical: true` in epistemics, logs trace step tagged
   `source: "mcp_primitive"`
2. Author `platform/src/lib/mcp/primitives_registry.ts` — whitelist of which
   10 retrieval tools are exposed (rejects requests for non-whitelisted)
3. Author 10 MCP tool wrappers under `platform-mcp/src/tools/`:
   `query_chart_facts.ts`, `query_signals.ts`, `query_dasha_periods.ts`,
   `query_panchanga.ts`, `query_ephemeris.ts`, `query_transit_event.ts`,
   `lel_query.ts`, `vector_search.ts`, `get_cgm_subgraph.ts`,
   `cross_school_lookup.ts`. Each wrapper hits the dispatcher with the
   right toolName. Each carries §4.6-standard description.
4. Author Jest tests under `platform/src/lib/__tests__/mcp/primitives.test.ts`
   covering: auth, whitelist enforcement, surgical flag stamping, trace
   logging
5. Verify `npx tsc --noEmit` and Jest pass

**Gate command:** see session_queue_MCP.yaml MCP-3-S1 entry.

**may_touch:** `platform/src/app/api/mcp/primitives/**`,
`platform/src/lib/mcp/primitives_registry.ts`,
`platform/src/lib/__tests__/mcp/**`, `platform-mcp/src/tools/<10 files>.ts`
**must_not_touch:** `platform/src/lib/retrieve/**` (existing tools wrapped, not modified)

### §3.4 — Brief 4: CLAUDECODE_BRIEF_MCP_3_S2_v1_0.md

**Session:** MCP-3-S2 — read_asset, get_trace, list_recent_queries + rate limiting

**Source:** MCP_BRIEF §4.1 Tier 4-5, §4.4 (rate limiting), §7.3

**Scope items:**

1. Author `platform/src/app/api/mcp/recent/route.ts` — returns recent MCP
   queries for the calling principal
2. Author `platform/src/lib/mcp/rate_limiter.ts` — per-key RPM + daily token
   budget enforcement; rejects with `{ok: false, error: {class: "rate_limit"}}`
3. Wire rate_limiter into `/api/mcp/execute`, `/api/mcp/plan`,
   `/api/mcp/primitives/[tool]`, `/api/mcp/recent`
4. Author `platform-mcp/src/tools/read_asset.ts` — uses `/api/mcp/execute`
   with a special read-asset mode (or new `/api/mcp/asset` endpoint per
   implementation choice — brief should pick one and document)
5. Author `platform-mcp/src/tools/get_trace.ts` — wraps existing
   `/api/audit/[query_id]/trace` endpoint with MCP envelope
6. Author `platform-mcp/src/tools/list_recent_queries.ts` — calls
   `/api/mcp/recent`
7. Jest tests for rate limiting

**Gate command:** see session_queue_MCP.yaml MCP-3-S2 entry.

**may_touch:** `platform/src/app/api/mcp/recent/**`, `platform/src/app/api/mcp/asset/**`
(if chosen), `platform/src/lib/mcp/rate_limiter.ts`, `platform/src/lib/__tests__/mcp/**`,
`platform-mcp/src/tools/{read_asset,get_trace,list_recent_queries}.ts`
**must_not_touch:** existing audit routes (read-only)

### §3.5 — Brief 5: CLAUDECODE_BRIEF_MCP_4_S1_v1_0.md

**Session:** MCP-4-S1 — Writes (log_prediction, record_outcome, flag_disagreement) + PPL integration

**Source:** MCP_BRIEF §4.1 Tier 5 writes, §6 G4 (PPL discipline), §7.4
acceptance criteria. Note: PPL substrate (formal `06_LEARNING_LAYER/`)
not yet scaffolded — interim path is LEL prediction subsection per
CLAUDE.md §E.

**Scope items:**

1. Author `platform/src/app/api/mcp/writes/[action]/route.ts` — dispatcher
   for log_prediction, record_outcome, flag_disagreement
2. Author `platform/src/lib/mcp/ppl_writer.ts` — interim writer that
   appends to LEL prediction subsection per interim PPL path; carries
   migration TODO comment with reference to `06_LEARNING_LAYER/`
3. Author `platform-mcp/src/tools/log_prediction.ts`
4. Author `platform-mcp/src/tools/record_outcome.ts`
5. Author `platform-mcp/src/tools/flag_disagreement.ts` — writes to
   `00_ARCHITECTURE/DISAGREEMENT_REGISTER_v1_0.md` (LIVING per CLAUDE.md §D)
6. Jest tests for each writer with provenance fields (caller, key_id, trace_id)

**Gate command:** see session_queue_MCP.yaml MCP-4-S1 entry.

**may_touch:** `platform/src/app/api/mcp/writes/**`,
`platform/src/lib/mcp/ppl_writer.ts`, `platform/src/lib/__tests__/mcp/**`,
`platform-mcp/src/tools/{log_prediction,record_outcome,flag_disagreement}.ts`,
`01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` (append-only via the writer),
`00_ARCHITECTURE/DISAGREEMENT_REGISTER_v1_0.md` (append-only)
**must_not_touch:** any non-prediction-subsection LEL entries; existing
disagreement entries

### §3.6 — Brief 6: CLAUDECODE_BRIEF_MCP_4_S2_v1_0.md

**Session:** MCP-4-S2 — Red-team pass per §IS.8(b)

**Source:** CLAUDE.md §M (red-team cadence), MCP_BRIEF §6 G12, §7.4
acceptance criteria

**Scope items:**

1. Author `00_ARCHITECTURE/MCP_RED_TEAM_v1_0.md` with a checklist:
   - Auth bypass attempts (invalid key, expired key, wrong tier)
   - Audience-tier leakage (client tier requesting super-admin-only data)
   - SQL injection / path traversal via tool params
   - Rate limit bypass attempts
   - PPL write tampering (record_outcome for a prediction the caller didn't log)
   - Plan-edit privilege escalation (execute_plan with tier-elevated tools)
   - Trace leakage (decision D12 means full transparency is by design — verify
     intentional, not accidental)
   - B.11 floor bypass via ask_madhav (verify floor enforced)
   - Synthesis_audit fidelity (does it accurately reflect what ran?)
2. Sub-agent runs each test against the local platform + platform-mcp setup
   (start dev server in background if needed) OR runs them as unit/integration
   tests, whichever is more practical
3. Each finding gets a class (1 = blocking, 2 = should-fix, 3 = nice-to-have)
4. Brief mandates: PASS only if `class-1 findings: 0` AND
   `red-team status: PASS` lines present in the report
5. If class-1 findings present → sub-agent emits HALT_NEEDS_HUMAN with
   details

**Gate command:** see session_queue_MCP.yaml MCP-4-S2 entry.

**may_touch:** `00_ARCHITECTURE/MCP_RED_TEAM_v1_0.md`,
test artifacts under `platform/src/lib/__tests__/mcp/red_team/`
**must_not_touch:** any application code (this is a verification session,
not a fix session — fixes go to a follow-up brief if findings emerge)

### §3.7 — Brief 7: CLAUDECODE_BRIEF_MCP_MERGE_v1_0.md

**Session:** MCP-MERGE — Push, open PR, enable auto-merge

**Source:** Native override 2026-05-21 (CONDUCTOR_PROMPT_MCP §2)

**Scope items:**

1. Verify clean working tree
2. Run `git push -u origin feature/mcp-server`
3. Run `gh pr create --title "feat(mcp): MARSYS-JIS MCP Server — workstream complete" --body <body>`
   with body summarizing all 8 prior sessions, citing master brief, listing
   AC coverage
4. Run `gh pr merge --auto --squash --delete-branch <pr_number>`
5. Author `00_ARCHITECTURE/MCP_WORKSTREAM_COMPLETE.md` sealing artifact
   with merge commit SHA placeholder (filled when CI lands)
6. Commit the sealing artifact (gets included via auto-merge once CI passes)

**Gate command:** see session_queue_MCP.yaml MCP-MERGE entry.

**may_touch:** `00_ARCHITECTURE/MCP_WORKSTREAM_COMPLETE.md`
**must_not_touch:** anything else; this is a push-and-merge session only

---

## §4 — Session-open handshake

You are a Conductor sub-agent; the standard SESSION_OPEN template applies
in spirit but the Conductor's FINAL_SUMMARY block is the orchestrator-facing
contract. No separate handshake artifact required for sub-agent sessions.

State briefly at start: "MCP-0-AUTHOR opening. Will author 7 sub-briefs from
MCP_BRIEF_v1_0.md using CLAUDECODE_BRIEF_MCP_1_S1_v1_0.md as the reference
standard."

---

## §5 — Scope constraints

### may_touch
```
00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCP_2_S1_v1_0.md   # CREATE
00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCP_2_S2_v1_0.md   # CREATE
00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCP_3_S1_v1_0.md   # CREATE
00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCP_3_S2_v1_0.md   # CREATE
00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCP_4_S1_v1_0.md   # CREATE
00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCP_4_S2_v1_0.md   # CREATE
00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCP_MERGE_v1_0.md  # CREATE
```

### must_not_touch
```
platform/**                                                # zero application code in this session
platform-mcp/**                                            # zero MCP server code in this session
01_FACTS_LAYER/**                                          # read-only
025_HOLISTIC_SYNTHESIS/**                                  # read-only
00_ARCHITECTURE/BRIEFS/MCP_BRIEF_v1_0.md                   # the master, do not edit
00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCP_1_S1_v1_0.md   # the reference, do not edit
00_ARCHITECTURE/CONDUCTOR/**                               # not yours to touch
00_ARCHITECTURE/CAPABILITY_MANIFEST.json                   # MCP-2-S1 brief will declare the update target
CLAUDE.md                                                  # any §E update is post-workstream-close
any other CLAUDECODE_BRIEF_*                               # other workstreams
```

### Commit cadence

Commit after each brief authored. Commit message format:

```
chore(mcp): MCP-0-AUTHOR — author CLAUDECODE_BRIEF_<session_id>_v1_0.md

Per MCP-0-AUTHOR scope §3.<N>. Source: MCP_BRIEF_v1_0.md §<sections>.
Reference style: CLAUDECODE_BRIEF_MCP_1_S1_v1_0.md.
```

---

## §6 — Session-close checklist (FINAL_SUMMARY)

After all 7 briefs are authored and committed, emit:

```
---FINAL_SUMMARY---
session_id: MCP-0-AUTHOR
status: PASS | HALT_NEEDS_HUMAN
commits:
  - <commit_sha_for_brief_1>
  - <commit_sha_for_brief_2>
  - <commit_sha_for_brief_3>
  - <commit_sha_for_brief_4>
  - <commit_sha_for_brief_5>
  - <commit_sha_for_brief_6>
  - <commit_sha_for_brief_7>
scope_items_completed:
  - AC.MCP_0.1  # CLAUDECODE_BRIEF_MCP_2_S1_v1_0.md authored
  - AC.MCP_0.2  # CLAUDECODE_BRIEF_MCP_2_S2_v1_0.md authored
  - AC.MCP_0.3  # CLAUDECODE_BRIEF_MCP_3_S1_v1_0.md authored
  - AC.MCP_0.4  # CLAUDECODE_BRIEF_MCP_3_S2_v1_0.md authored
  - AC.MCP_0.5  # CLAUDECODE_BRIEF_MCP_4_S1_v1_0.md authored
  - AC.MCP_0.6  # CLAUDECODE_BRIEF_MCP_4_S2_v1_0.md authored
  - AC.MCP_0.7  # CLAUDECODE_BRIEF_MCP_MERGE_v1_0.md authored
scope_items_failed: []
gate_command_runs:
  - name: brief_existence_and_structure_gate
    result: PASS | FAIL
notes_for_orchestrator: >
  All 7 sub-briefs authored from MCP_BRIEF_v1_0.md per §3. Each matches
  the CLAUDECODE_BRIEF_MCP_1_S1 reference style: frontmatter, §0–§6 sections,
  scope items with AC IDs, may_touch/must_not_touch, FINAL_SUMMARY template.
  Queue is now ready for MCP-1-S1 onwards.
human_decision_needed: >
  <empty if PASS>
---END_FINAL_SUMMARY---
```

---

*End of CLAUDECODE_BRIEF_MCP_0_AUTHOR_v1_0.md.*
