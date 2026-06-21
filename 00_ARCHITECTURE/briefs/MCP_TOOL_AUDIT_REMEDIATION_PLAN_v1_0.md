---
canonical_id: MCP_TOOL_AUDIT_REMEDIATION_PLAN
version: 1.0
status: ACTIVE
authored: 2026-05-26
author: Cowork (Abhisek Mohanty)
description: >
  Full remediation plan for the 40-tool MCP audit that revealed 71% average
  pass rate. Identifies 4 root-cause clusters, 2 code sessions, 1 operator
  prompt, and 2 optional P3 data-seeding sessions to recover the full manifest
  to ≥95%.
---

# MCP Tool Audit Remediation Plan v1.0

## 1 — Context

The Audit 2 snapshot (2026-05-26) tested all 40 registered MCP tools.
Headline results:

| Cohort | Tools | Average |
|---|---|---|
| Original 20 tools (re-audit) | 20 | 85% (+4 pts from Audit 1) |
| New 20 tools (first test) | 20 | 57% |
| **Full manifest** | **40** | **71%** |

Six tools are completely non-functional (0%). Another nine are degraded
(20–75%). The six tools performing excellently as new additions
(`chart_summary`, `cluster_atlas`, `contradiction_register`,
`pattern_register`, `resonance_register`, `query_kp_ruling_planets`) need
no work.

Target after this plan: **≥95% full-manifest average**.

---

## 2 — Root-Cause Clusters

Four independent clusters account for all failures. Fixing them in
priority order takes the manifest from 71% → ~95%.

### Cluster 1 — MARSYS_REPO_ROOT / Docker corpus gap (P0)
**Affects:** `read_asset` (0%), `query_cdlm_lookup` (0%),
`query_rm_walk` (0%), `query_ucn_walk` (0%)  
**+Impact if fixed:** ~+15 pts on full-manifest average

Three compounding bugs:

**Bug C1a — MCP Docker image never includes the markdown corpus.**
`platform-mcp/Dockerfile` copies only `dist/` and `resources/`. The
canonical markdown files (`025_HOLISTIC_SYNTHESIS/CDLM_v1_1.md`,
`RM_v2_0.md`, `UCN_v4_0.md`, `CGM_v9_0.md`, `MSR_v5_0.md`;
`01_FACTS_LAYER/FORENSIC…`, `LEL…`; `00_ARCHITECTURE/…`) are never
included. They exist only on the developer's laptop. The MCP container
has no corpus at `/app/025_HOLISTIC_SYNTHESIS/` — so `read_asset` and
the three CDLM/RM/UCN file-based tools always get ENOENT.

**Bug C1b — `resolveRepoRoot()` path depth is wrong.**
File: `platform-mcp/src/tools/read_asset.ts` (lines 51-55).
Comment says "go up 3 levels: `dist/tools → dist → app-root → repo-root`".
But at runtime `__dirname = /app/dist/tools`. Three levels up =
`/app/../.. = /` (container root), not `/app`. The correct depth
is **two levels** (`dist/tools → dist → /app`).

**Bug C1c — `SAFE_ASSET_MAP` has stale MSR version string.**
File: `platform-mcp/src/tools/read_asset.ts` line 76.
Map reads `'025_HOLISTIC_SYNTHESIS/MSR_v3_0.md'`.
Disk has `MSR_v5_0.md`. MSR reads will ENOENT even after C1a/C1b are
fixed.

**Bug C1d — `query_cdlm_lookup` / `query_rm_walk` / `query_ucn_walk`
use `__dirname`-relative paths inside a Next.js compiled bundle.**
Files: `platform/src/lib/retrieve/query_cdlm_lookup.ts` (line 27),
`query_rm_walk.ts`, `query_ucn_walk.ts`.
Pattern:
```ts
const CDLM_PATH = path.resolve(__dirname,
  '../../../../025_HOLISTIC_SYNTHESIS/CDLM_v1_1.md')
```
In the compiled Next.js output, `__dirname` resolves to
`.next/server/chunks/` — four levels up no longer reaches `/app/platform`.
`process.cwd()` is stable at `/app/platform` in Cloud Run. Fix: switch
all three files from `__dirname`-relative to `process.cwd()`-relative.
The `platform/cloudbuild.yaml` already copies `025_HOLISTIC_SYNTHESIS/`
to `platform/025_HOLISTIC_SYNTHESIS/` in the build context, so
`process.cwd()` resolution works without any Dockerfile change for the
web service.

---

### Cluster 2 — chart_id UUID vs DB key mismatch (P1)
**Affects:** `query_varshphal` (25% — 0 rows every call)  
**+Impact if fixed:** +4 pts

**Bug C2a — Wrong chart_id hardcoded in MCP wrapper.**
File: `platform-mcp/src/tools/query_varshphal.ts` line 38.
```ts
const NATIVE_CHART_ID = '362f9f17-95a5-490b-a5a7-027d3e0efda0'
```
This is the Firebase/Firestore document UUID. The `varshaphala` table
stores every row under `chart_id = 'abhisek_mohanty_primary'` (the DB
key, not the Firebase UUID). The MCP wrapper's override guarantees 0
rows on every call.

The platform-side retrieval tool (`platform/src/lib/retrieve/
query_varshaphala.ts`) correctly defaults to `'abhisek_mohanty_primary'`;
the break is purely in the MCP wrapper.

---

### Cluster 3 — Dispatcher wiring gap (P1)
**Affects:** `get_cgm_subgraph` (35% — 0 rows)  
**+Impact if fixed:** +2 pts (more when CGM tables are seeded)

**Bug C3a — `node_id` param never wired into `queryPlan.graph_seed_hints`.**
File: `platform/src/app/api/mcp/primitives/[tool]/route.ts` lines 178-195.
The dispatcher builds `queryPlan` with no `graph_seed_hints` field. The
`cgm_graph_walk` retrieval tool (`platform/src/lib/retrieve/
cgm_graph_walk.ts` lines 129-131) returns an empty bundle immediately
when `graph_seed_hints` is empty or missing:
```ts
const seeds = plan.graph_seed_hints?.length > 0 ? plan.graph_seed_hints : []
if (seeds.length === 0) { return buildEmptyBundle(...) }
```
`toolParams.node_id` is available to the dispatcher but never propagated.

---

### Cluster 4 — Sidecar schema / availability (P1-P2)
**Affects:** `muhurta_finder` (0%), `temporal` (20%)  
**+Impact if fixed:** +5 pts

**Bug C4a — `muhurta_finder` passes free-text event string to sidecar
that validates against a strict enum.**
File: `platform-mcp/src/tools/muhurta_finder.ts`.
The MCP schema defines `event: z.string()` with description "pass any
string — the engine uses fuzzy taxonomy". In practice the python sidecar
endpoint `/api/compute/muhurat` validates against a closed enum
(`vivah`, `griha_pravesh`, `vyapara`, `yatra`, `property_purchase`,
`mantra_initiation`) and returns HTTP 422 for unrecognised values.
"travel" → 422 every time. Fix: either (a) restrict MCP schema to the
sidecar enum and add an alias mapping ("travel" → "yatra"), or
(b) fix the sidecar to accept fuzzy input. Option (a) is in scope here.

**Config C4b — `amjis-sidecar` cold-starts cause `temporal` timeouts.**
The python sidecar has `min-instances=0`. The `temporal` tool dispatches
to `/transits`, `/ephemeris`, `/dasha_chain` on the sidecar. First call
in a cold window exceeds the MCP request timeout. Fix: set
`amjis-sidecar` to `min-instances=1` via `gcloud run services update`.

---

### Known-intentional / not bugs

| Tool | Status | Notes |
|---|---|---|
| `query_jaimini_drishti` | Intentional stub | Documented in source as M6+ scope. Returns `not_implemented`. No fix. |
| `vector_search` | Infra check needed | `GCP_PROJECT` + `VERTEX_AI_LOCATION` + `VECTOR_SEARCH_ENABLED` env vars on amjis-web may be missing. Operator config check, no code change. |
| `holistic_bundle` (70%) | Cascading from Cluster 1 | UCN/RM/CDLM sub-tools fail because `read_asset` fails. Once C1 is fixed, sub-tool scores recover and bundle score improves. The "PANCHANG subset not firing" note in the audit is also expected to resolve since `date` IS the correct param name — it was likely masking a cascade from the read_asset failures. |
| `tool_health` / `data_coverage` | Accurate reflections | They correctly reflect tool call history and data table states. Auto-heal once upstream tools work. |
| `timeline_query` (25%) | Unseeded data | `rag_chunks` has no `doc_type = 'l5_timeline'` rows — no build script created them. P3 scope — new bootstrap script required. |
| `get_cgm_subgraph` (partial) | Unseeded data (secondary) | Even after C3a is fixed, `l25_cgm_nodes` / `l25_cgm_edges` tables are empty. P3 scope — seeding script required. |

---

## 3 — Fix Topology

```
Stream A (platform-mcp package → amjis-mcp redeploy)
  │
  ├── MCP-REM-S1: Docker + read_asset + query_varshphal + muhurta_finder
  │               All 4 MCP-package code changes in one session.
  │               1 build → 1 amjis-mcp redeploy.
  │
Stream B (platform package → amjis-web redeploy)
  │
  ├── MCP-REM-S2: query_cdlm/rm/ucn process.cwd() + cgm dispatcher wiring
  │               All 4 platform-package code changes in one session.
  │               1 build → 1 amjis-web redeploy.
  │
  ↓ (both streams can run in parallel — no shared files)

Operator steps (no Claude Code session — gcloud commands only)
  │
  ├── MCP-REM-OPS: amjis-sidecar min-instances=1
  │               + verify vector_search env vars on amjis-web
  │

[After P0+P1 deployed and verified]

Stream C (data seeding — P3, deferred)
  │
  ├── MCP-REM-S3: CGM graph seeding from CGM_v9_0.md
  ├── MCP-REM-S4: L5 timeline rag_chunks bootstrap
  │
  ↓

Validation
  │
  └── MCP-REM-S5: Full 40-tool re-audit, governance seal, SESSION_LOG append
```

Streams A and B are **parallel-safe** (no shared files, different packages,
different Cloud Run services). They can be opened simultaneously in two
Antigravity windows on separate branches.

---

## 4 — Session Specifications

---

### MCP-REM-S1 — Platform-MCP package: Docker + read_asset + varshphal + muhurta_finder

**Branch:** `fix/mcp-rem-s1`  
**Worktree:** `/Users/Dev/Vibe-Coding/Apps/MadhavMCPRem-S1`  
**Package:** `platform-mcp/` only  
**May touch:** `platform-mcp/Dockerfile`, `platform-mcp/cloudbuild.yaml`, `platform-mcp/src/tools/read_asset.ts`, `platform-mcp/src/tools/query_varshphal.ts`, `platform-mcp/src/tools/muhurta_finder.ts`, test files for those three tools  
**Must NOT touch:** `platform/` (any file), `00_ARCHITECTURE/`, any database migration

**Changes:**

#### C1a — Dockerfile: copy markdown corpus into image

In `platform-mcp/Dockerfile`, before the final `CMD` line, add:
```dockerfile
# Canonical markdown corpus required by read_asset and file-based retrieval tools
COPY 025_HOLISTIC_SYNTHESIS/ ./025_HOLISTIC_SYNTHESIS/
COPY 01_FACTS_LAYER/ ./01_FACTS_LAYER/
COPY 00_ARCHITECTURE/MACRO_PLAN_v2_0.md ./00_ARCHITECTURE/MACRO_PLAN_v2_0.md
COPY 00_ARCHITECTURE/PROJECT_ARCHITECTURE_v2_2.md ./00_ARCHITECTURE/PROJECT_ARCHITECTURE_v2_2.md
COPY 00_ARCHITECTURE/CURRENT_STATE_v1_0.md ./00_ARCHITECTURE/CURRENT_STATE_v1_0.md
```

These five `COPY` directives must come from the **repository root** as the build
context. Verify that `platform-mcp/cloudbuild.yaml` step 1 (`docker build`)
sets the build context to the repo root (`-f platform-mcp/Dockerfile .`), or
add a step to move the required folders into the build context before the
`docker build` step if the context is currently restricted to `platform-mcp/`.

**Acceptance check C1a:** `docker run --rm <built-image> ls /app/025_HOLISTIC_SYNTHESIS/` returns `CDLM_v1_1.md MSR_v5_0.md UCN_v4_0.md CGM_v9_0.md RM_v2_0.md`.

#### C1b — read_asset.ts: fix path depth (3 levels → 2 levels)

File: `platform-mcp/src/tools/read_asset.ts` (the `resolveRepoRoot` function).

Change:
```ts
return join(__dirname, '..', '..', '..')
```
to:
```ts
return join(__dirname, '..', '..')
```
Update the inline comment to reflect: `// dist/tools → dist → /app`.

**Acceptance check C1b:** In a unit test (`read_asset.test.ts`), mock `__dirname = '/app/dist/tools'` and assert `resolveRepoRoot()` returns `/app`.

#### C1c — read_asset.ts: fix stale MSR version in SAFE_ASSET_MAP

File: `platform-mcp/src/tools/read_asset.ts` line 76.

Change:
```ts
MSR: '025_HOLISTIC_SYNTHESIS/MSR_v3_0.md',
```
to:
```ts
MSR: '025_HOLISTIC_SYNTHESIS/MSR_v5_0.md',
```

**Acceptance check C1c:** `read_asset({ canonical_id: 'MSR' })` test passes without ENOENT.

#### C2a — query_varshphal.ts: fix chart_id

File: `platform-mcp/src/tools/query_varshphal.ts` line 38.

Change:
```ts
const NATIVE_CHART_ID = '362f9f17-95a5-490b-a5a7-027d3e0efda0'
```
to:
```ts
const NATIVE_CHART_ID = 'abhisek_mohanty_primary'
```

Update the JSDoc comment on that constant: remove the UUID and explain this is
the DB key used by the `varshaphala` table.

**Acceptance check C2a:** `query_varshphal({ year: 2026 })` integration test
returns `ok: true` with `result.varshaphala` array non-empty (≥1 row).

#### C4a — muhurta_finder.ts: restrict event param to sidecar enum + add alias map

File: `platform-mcp/src/tools/muhurta_finder.ts`.

Step 1 — Replace `z.string()` with a `z.enum()` for the `event` field:
```ts
const SIDECAR_EVENTS = [
  'vivah', 'griha_pravesh', 'vyapara', 'yatra',
  'property_purchase', 'mantra_initiation'
] as const

// User-friendly alias → sidecar taxonomy
const EVENT_ALIAS: Record<string, typeof SIDECAR_EVENTS[number]> = {
  marriage:        'vivah',
  house_entry:     'griha_pravesh',
  business_start:  'vyapara',
  travel:          'yatra',
  vehicle_purchase:'property_purchase',
}
```

Step 2 — In the tool schema, change the `event` field from `z.string()` to:
```ts
event: z.enum([...SIDECAR_EVENTS, ...Object.keys(EVENT_ALIAS)] as [string, ...string[]])
  .describe('Event type. Accepted: ' + [...SIDECAR_EVENTS, ...Object.keys(EVENT_ALIAS)].join(', '))
```

Step 3 — Before dispatching to the platform primitive, resolve aliases:
```ts
const resolvedEvent = EVENT_ALIAS[args.event] ?? args.event
```

Step 4 — Update the tool description (`MUHURTA_FINDER_DESCRIPTION`) to list
the accepted event values explicitly.

**Acceptance check C4a:** `muhurta_finder({ event: 'travel', date_from: '2026-06-01', date_to: '2026-06-30' })` no longer returns HTTP 422. `muhurta_finder({ event: 'vivah', ... })` also passes.

**Session close ACs:**
1. `npm run build` passes with 0 TypeScript errors in `platform-mcp/`.
2. `npm test` passes in `platform-mcp/` (all existing + updated tests green).
3. `docker build -f platform-mcp/Dockerfile . -t mcp-rem-s1-test` succeeds.
4. `docker run --rm mcp-rem-s1-test ls /app/025_HOLISTIC_SYNTHESIS/` shows all 5 canonical files.
5. Commit on `fix/mcp-rem-s1` with message: `fix(mcp): Docker corpus copy + read_asset path depth + MSR version + varshphal chart_id + muhurta event enum`.

---

### MCP-REM-S2 — Platform package: cdlm/rm/ucn path fix + cgm dispatcher wiring

**Branch:** `fix/mcp-rem-s2`  
**Worktree:** `/Users/Dev/Vibe-Coding/Apps/MadhavMCPRem-S2`  
**Package:** `platform/` only  
**May touch:** `platform/src/lib/retrieve/query_cdlm_lookup.ts`, `platform/src/lib/retrieve/query_rm_walk.ts`, `platform/src/lib/retrieve/query_ucn_walk.ts`, `platform/src/app/api/mcp/primitives/[tool]/route.ts`, test files for the above  
**Must NOT touch:** `platform-mcp/` (any file), any database migration, any other `platform/` file

**Changes:**

#### C1d — query_cdlm_lookup / query_rm_walk / query_ucn_walk: switch to process.cwd()

All three files use the same pattern:
```ts
const CDLM_PATH = path.resolve(__dirname, '../../../../025_HOLISTIC_SYNTHESIS/CDLM_v1_1.md')
```
(and equivalents for RM, UCN).

For all three, replace `__dirname`-relative resolution with `process.cwd()`-relative:

`query_cdlm_lookup.ts`:
```ts
const CDLM_PATH = path.resolve(process.cwd(), '025_HOLISTIC_SYNTHESIS/CDLM_v1_1.md')
```

`query_rm_walk.ts`:
```ts
const RM_PATH = path.resolve(process.cwd(), '025_HOLISTIC_SYNTHESIS/RM_v2_0.md')
```

`query_ucn_walk.ts`:
```ts
const UCN_PATH = path.resolve(process.cwd(), '025_HOLISTIC_SYNTHESIS/UCN_v4_0.md')
```

The `platform/cloudbuild.yaml` pre-build step already copies
`025_HOLISTIC_SYNTHESIS/` to `platform/025_HOLISTIC_SYNTHESIS/`
(i.e. into the web build context), so `process.cwd() = /app/platform` at
Cloud Run runtime resolves to the correct paths. No Dockerfile change needed.

**Acceptance check C1d:** Update unit tests for each tool to use the process.cwd()
resolution and assert no ENOENT. Add a test that verifies the resolved path ends
with `025_HOLISTIC_SYNTHESIS/CDLM_v1_1.md` (and equivalents).

#### C3a — Primitives dispatcher: wire node_id → graph_seed_hints for CGM

File: `platform/src/app/api/mcp/primitives/[tool]/route.ts`.

After the `const queryPlan = { ... }` block (around line 195), add:
```ts
// CGM graph traversal: wire node_id + hops from toolParams into queryPlan
// (cgm_graph_walk returns empty bundle immediately if graph_seed_hints is missing)
if (retrievalToolName === 'cgm_graph_walk') {
  if (toolParams.node_id) {
    (queryPlan as Record<string, unknown>).graph_seed_hints = [String(toolParams.node_id)]
  }
  if (typeof toolParams.hops === 'number') {
    (queryPlan as Record<string, unknown>).graph_traversal_depth = toolParams.hops
  }
}
```

This is a surgical 6-line addition. It has no effect on any other tool.

**Acceptance check C3a:** Integration test: call `get_cgm_subgraph({ node_id: 'SIG.MSR.001', hops: 1 })` via the primitives endpoint. Even with empty CGM tables the response must be `{ ok: true, result: { nodes: [], edges: [] } }` — not the "no seeds" early-exit error bundle.

**Session close ACs:**
1. `npm run build` passes with 0 TypeScript errors in `platform/`.
2. `npm test` passes in `platform/` (all existing + updated tests green, including the three retrieval tool tests and the CGM dispatcher test).
3. Commit on `fix/mcp-rem-s2` with message: `fix(platform): process.cwd() path resolution for cdlm/rm/ucn + cgm dispatcher graph_seed_hints wiring`.

---

### MCP-REM-OPS — Operator config steps (no Claude Code session)

These are pure `gcloud` commands. Paste into terminal or a brief Claude Code
"operator" session. No branch, no PR needed — env var changes are live immediately.

**Step OPS-1: Set amjis-sidecar min-instances=1**
```bash
gcloud run services update amjis-sidecar \
  --region=asia-south1 \
  --project=madhav-astrology \
  --min-instances=1
```
Verify:
```bash
gcloud run services describe amjis-sidecar \
  --region=asia-south1 --project=madhav-astrology \
  --format='value(spec.template.spec.containers[0].resources.limits.cpu,
    metadata.annotations."autoscaling.knative.dev/minScale")'
```
Expected: minScale = 1.

**Step OPS-2: Verify and set vector_search env vars on amjis-web**
```bash
gcloud run services describe amjis-web \
  --region=asia-south1 --project=madhav-astrology \
  --format='value(spec.template.spec.containers[0].env)'
```
Confirm `GCP_PROJECT`, `VERTEX_AI_LOCATION`, `VECTOR_SEARCH_ENABLED` are present.
If any are missing:
```bash
gcloud run services update amjis-web \
  --region=asia-south1 --project=madhav-astrology \
  --update-env-vars="GCP_PROJECT=madhav-astrology,\
VERTEX_AI_LOCATION=asia-south1,\
VECTOR_SEARCH_ENABLED=true"
```

**Step OPS-3: Deploy amjis-mcp after MCP-REM-S1 merges to main**
```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
gcloud builds submit --config platform-mcp/cloudbuild.yaml --project madhav-astrology
```

**Step OPS-4: Deploy amjis-web after MCP-REM-S2 merges to main**
```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
gcloud builds submit --config cloudbuild.yaml --project madhav-astrology
```

**Step OPS-5: Post-deploy log watch (both services, 5 min)**
```bash
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="amjis-mcp" AND severity>=ERROR' \
  --project=madhav-astrology --freshness=5m --limit=20
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="amjis-web" AND severity>=ERROR' \
  --project=madhav-astrology --freshness=5m --limit=20
```

**Acceptance:** 0 new ERROR entries referencing MARSYS_REPO_ROOT, ENOENT, 422, or process.cwd() in either log.

---

### MCP-REM-S3 — CGM graph seeding (P3, deferred)

**Trigger:** Only after MCP-REM-S1 + S2 + OPS complete and audit shows `get_cgm_subgraph` still scoring 0 rows despite the dispatcher fix.  
**Branch:** `fix/mcp-rem-cgm-seed`  
**Package:** New script in `platform/scripts/`  
**May touch:** `platform/scripts/data/seed_cgm_graph.ts` (new), `platform/src/lib/db/` (read-only)  
**Must NOT touch:** existing migrations, `025_HOLISTIC_SYNTHESIS/CGM_v9_0.md` source

**Scope:** Parse `025_HOLISTIC_SYNTHESIS/CGM_v9_0.md` for the structured
cross-domain linkage declarations. INSERT rows into `l25_cgm_nodes` and
`l25_cgm_edges` tables (migration `018_l2_5_structured.sql` already created them).
Idempotent: `ON CONFLICT DO NOTHING` on both tables.

**Acceptance check MCP-REM-S3:** After script execution, `SELECT count(*) FROM l25_cgm_nodes` > 0. `get_cgm_subgraph({ node_id: 'SIG.MSR.001', hops: 2 })` returns non-empty nodes array.

---

### MCP-REM-S4 — L5 timeline rag_chunks (P3, deferred)

**Trigger:** Only after P0+P1 fixes are live and `timeline_query` still scores 0.  
**Branch:** `fix/mcp-rem-l5-seed`  
**May touch:** New bootstrap script in `platform/scripts/data/seed_l5_timeline_chunks.ts`  
**Must NOT touch:** existing `rag_chunks` rows with other doc_types

**Scope:** Identify the L5 source documents (dasha arc narratives, structural
inflection point writeups in `05_TEMPORAL_ENGINES/` or equivalent). Chunk them
and INSERT into `rag_chunks` with `doc_type = 'l5_timeline'`. Idempotent via
`ON CONFLICT DO NOTHING`.

**Acceptance check MCP-REM-S4:** `SELECT count(*) FROM rag_chunks WHERE doc_type = 'l5_timeline'` > 0. `timeline_query({ query: 'Saturn dasha arc' })` returns ≥1 chunk.

---

### MCP-REM-S5 — Full re-audit + governance seal

**Trigger:** After MCP-REM-S1, S2, OPS all complete and both services deployed.  
**Branch:** None (direct main or governance-only branch)  
**Scope:**
1. Re-run the full 40-tool MCP audit (same methodology as Audit 2).
2. Verify score ≥95% full-manifest average.
3. Per-cluster confirmation:
   - Cluster 1: `read_asset` returns content for MSR, UCN, CDLM, RM.
   - Cluster 2: `query_varshphal({ year: 2026 })` returns ≥1 row.
   - Cluster 3: `get_cgm_subgraph({ node_id: '...', hops: 1 })` no longer early-exits.
   - Cluster 4: `muhurta_finder({ event: 'travel', ... })` no longer 422; `temporal` responds without timeout.
4. Append `MCP-AUDIT-REM-COMPLETE` entry to `SESSION_LOG.md`.
5. Update `CURRENT_STATE_v1_0.md §2 recent completions`.
6. Bump `CLAUDE.md §E` MCP Transformation / MCP workstream status note to reflect "Tool Audit Remediation v1.0 COMPLETE".

---

## 5 — Expected Outcome by Session

| After | Tools fixed | Projected avg |
|---|---|---|
| Baseline (now) | — | 71% |
| MCP-REM-S1 deployed | `read_asset`, `query_varshphal`, `muhurta_finder` | ~79% |
| MCP-REM-S2 deployed | `query_cdlm_lookup`, `query_rm_walk`, `query_ucn_walk`, `get_cgm_subgraph` | ~87% |
| OPS complete | `temporal` (cold-start gone), `vector_search` (if env vars were missing) | ~91% |
| OPS + cascade recovery | `holistic_bundle` UCN/RM/CDLM sub-tools recover | ~95% |
| S3 + S4 (P3) | `get_cgm_subgraph` with data, `timeline_query` | ~98% |

---

## 6 — Out of Scope

| Tool | Why out of scope |
|---|---|
| `query_jaimini_drishti` | Intentional stub — implementation is M6+ per the tool source. No fix warranted until Jaimini engine is built. |
| `query_transit_event` (−3) | Slight degradation (Saturn ingress not found) is a data freshness issue, not a code bug. Will improve as ephemeris is kept current. |
| `data_coverage` null actual_rows | Accurately reflects empty tables (CGM, L5). Heals when P3 seeding runs. |
| `tool_health` null metrics | No call history yet. Heals after tools are used in production. |

---

## 7 — Dependency Graph

```
MCP-REM-S1 ─────────────────┐
  (platform-mcp code fixes)  │
                             ├──► MCP-REM-OPS (deploy + config)
MCP-REM-S2 ─────────────────┘       │
  (platform code fixes)             │
                                    ▼
                               MCP-REM-S5 (validation + seal)
                                    │
                       (optional)   ▼
                           MCP-REM-S3 + S4 (P3 seeding)
```

S1 and S2 are **fully parallel** — different packages, different services,
no shared files.

OPS steps 1-2 (sidecar + env vars) can run **immediately** without waiting for
S1 or S2.

OPS steps 3-4 (deploy) must wait for S1/S2 to merge to main.

---

## 8 — Conductor Queue (if using autonomous execution)

If running via the Conductor framework, the session queue for this plan lives at:
`00_ARCHITECTURE/CONDUCTOR/mcp-rem/session_queue.yaml`

Recommended: S1 and S2 as parallel entries (separate worktrees); OPS as a
`requires_human_approval: true` entry; S5 (validation) after OPS.

---

*End of MCP_TOOL_AUDIT_REMEDIATION_PLAN_v1_0.md*
