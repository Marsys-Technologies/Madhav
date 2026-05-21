---
artifact: CLAUDECODE_BRIEF_MCP_2_S1_v1_0.md
type: CLAUDECODE_BRIEF
version: 1.0
status: COMPLETE
authored_by: Claude Code sub-agent (MCP-0-AUTHOR)
authored_at: 2026-05-21
session_id: MCP-2-S1
session_name: MCP-2-S1 — MCP server scaffold (platform-mcp/) + Tier-1/2 tools
executor: Claude Code sub-agent (general-purpose, spawned by MCP Conductor)
execution_mode: single autonomous session, --dangerously-skip-permissions
worktree:
  name: MadhavMCP
  branch: feature/mcp-server
  base: main
  path_absolute: /Users/Dev/Vibe-Coding/Apps/MadhavMCP
governing_plan: 00_ARCHITECTURE/BRIEFS/MCP_BRIEF_v1_0.md
reference_brief: 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCP_1_S1_v1_0.md
predecessor_session: MCP-1-S1 (foundation — platform endpoints + auth)
next_session_anticipated: MCP-2-S2 (tool descriptions + resources)
---

# CLAUDECODE_BRIEF — MCP-2-S1
## MCP server scaffold: platform-mcp/ Node service + Tier-1/Tier-2 tools

---

## §0 — How to start this session

You are a sub-agent spawned by the MCP Conductor. Your context is fresh.
You are in the MadhavMCP worktree at `/Users/Dev/Vibe-Coding/Apps/MadhavMCP`
on branch `feature/mcp-server`. The Conductor has already pasted your
session prompt; you are now reading this brief.

This session creates the **`platform-mcp/` Node service** — the HTTP/SSE
MCP server that Claude Chat and Cowork connect to. The platform-side
endpoints (`/api/mcp/*`) were created in MCP-1-S1. This session wires the
MCP SDK adapter on top of those endpoints. No platform-side code changes
in this session.

---

## §1 — Session identity

| Field | Value |
|---|---|
| Session ID | MCP-2-S1 |
| Branch | `feature/mcp-server` |
| Worktree path | `/Users/Dev/Vibe-Coding/Apps/MadhavMCP` |
| Execution mode | Single autonomous session, `--dangerously-skip-permissions` |
| Predecessor | MCP-1-S1 (platform endpoints live) |
| Anticipated next | MCP-2-S2 (tool descriptions + MCP resources) |

---

## §2 — Mandatory reads at session open (in order)

1. `CLAUDE.md` (§C mandatory list — full read)
2. `00_ARCHITECTURE/BRIEFS/MCP_BRIEF_v1_0.md` — **full read**; this session
   implements §5.1 (file structure), §5.2 (data flow for `ask_madhav`),
   §5.3 (primitive data flow), §5.5 (Cloud Run deployment), §5.6
   (service-to-service auth), §7.2 (Phase MCP-2 scope and acceptance
   criteria). Focus on the engineering half — resource authoring lands in
   MCP-2-S2.
3. `platform/src/app/api/mcp/execute/route.ts` — read the endpoint you'll
   be calling from `platform-mcp/src/client.ts`; understand the request
   shape and response envelope
4. `platform/src/lib/mcp/types.ts` — read the McpEnvelope types so your
   MCP server correctly types the call-through responses
5. `platform/src/lib/mcp/epistemics.ts` — understand the envelope builder
   output shape; the MCP server must not re-wrap or transform it

Skim only:
- `@modelcontextprotocol/sdk` npm page — confirm current version and HTTP/SSE
  transport API. Use `npx @modelcontextprotocol/sdk@latest` docs to understand
  `McpServer`, `StreamableHTTPServerTransport`, and tool registration.

---

## §3 — Scope (11 items — execute in order; commit after each)

### Item 1 — Initialize `platform-mcp/` Node project

**What:** Create `platform-mcp/` with the following files:
- `package.json` — Node 20, TypeScript, ESM (`"type": "module"`), scripts:
  `build`, `start`, `dev`, `typecheck`. Dependencies: `@modelcontextprotocol/sdk`,
  `express` (or Hono — choose whichever is lighter for the thin adapter
  role), `google-auth-library` (for service-to-service identity token
  fetch), `node-fetch` or native fetch (Node 20 has it). Dev dependencies:
  `typescript`, `@types/node`, `tsx`.
- `tsconfig.json` — strict, ESM, target ES2022, `outDir: dist`.
- `.gcloudignore` — excludes `node_modules`, `dist`, `.env*`, `*.test.ts`.
- `.env.example` — documents required env vars:
  `PLATFORM_URL` (the `amjis-web` Cloud Run URL),
  `MCP_SERVICE_ACCOUNT_EMAIL` (the `amjis-mcp` service account),
  `MCP_PORT` (default 8080).

**AC.MCP_2_S1.1:** All four files exist; `package.json` declares correct
scripts and `"type": "module"`; `tsconfig.json` has `strict: true` and ESM
settings.

**Why:** The MCP server is a separate Node service. It must be independently
buildable and deployable. Starting with clean project config prevents
drift in later sessions.

Commit: `chore(mcp): MCP-2-S1 item 1 — initialize platform-mcp/ Node project`

---

### Item 2 — Install dependencies

**What:** Run `npm install` inside `platform-mcp/` to populate
`node_modules/` and generate `package-lock.json`. Verify the install
succeeds and `@modelcontextprotocol/sdk` is present.

**AC.MCP_2_S1.2:** `package-lock.json` exists; `node_modules/@modelcontextprotocol/`
exists; `npm install` exits 0.

**Why:** Dependencies must be resolved before TypeScript compilation can
be verified.

Commit: `chore(mcp): MCP-2-S1 item 2 — npm install for platform-mcp`

---

### Item 3 — Shared types (`platform-mcp/src/types.ts`)

**What:** Author `platform-mcp/src/types.ts` with TypeScript interfaces
for the MCP server's internal use:

```typescript
// McpToolCall — the body sent to /api/mcp/execute
export interface McpToolCall {
  tool: 'ask_madhav' | 'plan_query' | 'execute_plan';
  params: Record<string, unknown>;
}

// McpEnvelope — mirrors platform/src/lib/mcp/types.ts
// (duplicate intentionally; the MCP service must not import platform
//  files directly — they run in different Node processes)
export interface EpistemicsBlock { ... }
export interface SynthesisAuditBlock { ... }
export interface McpEnvelope {
  ok: boolean;
  trace_id: string;
  audience_tier: string;
  epistemics: EpistemicsBlock;
  result?: unknown;
  citations?: string[];
  plan?: unknown;
  predictions_logged?: unknown[];
  synthesis_audit?: SynthesisAuditBlock;
  suggested_followups?: string[];
  warnings?: string[];
  error?: {
    class: string;
    message: string;
    remediation?: string;
  };
}

// PlatformCallResult — the resolved call to /api/mcp/execute
export interface PlatformCallResult {
  status: number;
  envelope: McpEnvelope;
}
```

**AC.MCP_2_S1.3:** `types.ts` exports all listed interfaces; no `any`
types (use `unknown` where type is open); `npx tsc --noEmit` passes for
this file.

**Why:** Shared types prevent the platform and MCP server from drifting on
the envelope contract. Duplication is intentional (separate deployment
units — no cross-process imports).

Commit: `chore(mcp): MCP-2-S1 item 3 — platform-mcp/src/types.ts shared interfaces`

---

### Item 4 — Client module (`platform-mcp/src/client.ts`)

**What:** Author `platform-mcp/src/client.ts` which handles all outbound
HTTP calls to the platform. Export:

```typescript
export async function callPlatform(
  toolCall: McpToolCall,
  principal: { user_uid: string; audience_tier: string; key_id: string }
): Promise<PlatformCallResult>
```

Implementation:
1. Fetch a Cloud Run service-to-service identity token from the metadata
   server (`http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/identity?audience=<PLATFORM_URL>`).
   Fall back to a `SERVICE_TOKEN` env var for local dev.
2. POST to `${PLATFORM_URL}/api/mcp/execute` with:
   - `Authorization: Bearer <identity_token>`
   - `X-MCP-User: <principal.user_uid>`
   - `X-MCP-Audience-Tier: <principal.audience_tier>`
   - `X-MCP-Key-Id: <principal.key_id>`
   - JSON body: `{ tool, params }`
3. Return `{ status: response.status, envelope: await response.json() }`.
4. On network error: return `{ status: 503, envelope: errorEnvelope("internal", "Platform unreachable") }`.

Also export:
- `callPlatformPlan(query: string, principal): Promise<PlatformCallResult>` — POSTs to `/api/mcp/plan`
- `callPlatformPrimitive(toolName: string, params, principal): Promise<PlatformCallResult>` — POSTs to `/api/mcp/primitives/{toolName}`

**AC.MCP_2_S1.4:** All three functions exported; handles identity token
fetch with local-dev fallback; network errors return clean error envelope
(no thrown exceptions bubble to the MCP tool layer); TypeScript strict
passes.

**Why:** Central client module — all platform calls route through here.
Easier to add retry logic, timeout, or circuit breaking later without
touching tool code.

Commit: `feat(mcp): MCP-2-S1 item 4 — platform-mcp/src/client.ts platform call module`

---

### Item 5 — `ask_madhav` tool (`platform-mcp/src/tools/ask_madhav.ts`)

**What:** Author `platform-mcp/src/tools/ask_madhav.ts` which registers
the `ask_madhav` MCP tool. Tool description is a **placeholder** in this
session (~30 words); the §4.6-standard description lands in MCP-2-S2.

Placeholder description:
```
Runs the full MARSYS-JIS pipeline for the question and returns a
synthesized answer with citations, trace ID, and epistemics. [Full
description authoring: MCP-2-S2]
```

Input schema:
```json
{
  "type": "object",
  "properties": {
    "query": { "type": "string", "description": "The question to answer." },
    "mode": {
      "type": "string",
      "enum": ["auto", "holistic", "factual", "predictive", "cross_domain",
               "discovery", "remedial", "classical_grounding",
               "multi_school_triangulation"],
      "description": "Query mode. Default: auto.",
      "default": "auto"
    },
    "context_hint": {
      "type": "string",
      "description": "Optional summary of prior conversation context."
    }
  },
  "required": ["query"]
}
```

Handler: call `callPlatform({ tool: 'ask_madhav', params }, principal)` and
return the envelope as the MCP tool result content (JSON stringified).
Errors: if `envelope.ok === false`, return an MCP error result.

Export a function `registerAskMadhav(server: McpServer, getPrincipal: () => Principal)`.

**AC.MCP_2_S1.5:** Tool registers on the MCP server; input schema validates
correctly; handler calls `callPlatform`; TypeScript strict passes.

**Why:** `ask_madhav` is the primary tool. Description is intentionally
placeholder — full §4.6 description is the scope of MCP-2-S2.

Commit: `feat(mcp): MCP-2-S1 item 5 — ask_madhav tool (placeholder description)`

---

### Item 6 — `plan_query` tool (`platform-mcp/src/tools/plan_query.ts`)

**What:** Author `platform-mcp/src/tools/plan_query.ts`.

Placeholder description (~30 words):
```
Returns the PipelinePlan JSON for the query without executing it.
Inspect what tools would run before committing to execution. [Full
description: MCP-2-S2]
```

Input schema:
```json
{
  "type": "object",
  "properties": {
    "query": { "type": "string" }
  },
  "required": ["query"]
}
```

Handler: call `callPlatformPlan(query, principal)` and return the plan
JSON as content.

Export `registerPlanQuery(server: McpServer, getPrincipal: () => Principal)`.

**AC.MCP_2_S1.6:** Tool registers; calls `callPlatformPlan`; TypeScript
strict passes.

**Why:** `plan_query` enables differential-analysis workflows. Description
will be completed in MCP-2-S2.

Commit: `feat(mcp): MCP-2-S1 item 6 — plan_query tool (placeholder description)`

---

### Item 7 — `execute_plan` tool (`platform-mcp/src/tools/execute_plan.ts`)

**What:** Author `platform-mcp/src/tools/execute_plan.ts`.

Placeholder description (~30 words):
```
Executes an explicit PipelinePlan (from plan_query, optionally edited).
Enables plan inspection + modification + re-execution workflows. [Full
description: MCP-2-S2]
```

Input schema:
```json
{
  "type": "object",
  "properties": {
    "plan": {
      "type": "object",
      "description": "A PipelinePlan object, typically from plan_query output."
    }
  },
  "required": ["plan"]
}
```

Handler: call `callPlatform({ tool: 'execute_plan', params: { plan } }, principal)`
and return the envelope. The platform re-validates the plan against
`PipelinePlanSchema` server-side; no client-side re-validation needed.

Export `registerExecutePlan(server: McpServer, getPrincipal: () => Principal)`.

**AC.MCP_2_S1.7:** Tool registers; calls `callPlatform`; TypeScript
strict passes.

**Why:** Completes the plan-inspection tier. Together with `plan_query`,
enables the differential-analysis workflow in MCP_BRIEF §3.

Commit: `feat(mcp): MCP-2-S1 item 7 — execute_plan tool (placeholder description)`

---

### Item 8 — Server entry point (`platform-mcp/src/server.ts`)

**What:** Author `platform-mcp/src/server.ts` — the HTTP/SSE server that
Claude Chat and Cowork connect to.

```typescript
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import express from 'express';
import { validateMcpKeyFromHeader } from './auth.js';
import { registerAskMadhav } from './tools/ask_madhav.js';
import { registerPlanQuery } from './tools/plan_query.js';
import { registerExecutePlan } from './tools/execute_plan.js';

// Each request gets its own McpServer + transport instance
// (stateless — per D10, no conversation history)
const app = express();
app.use(express.json());

app.post('/mcp', async (req, res) => {
  const principal = await validateMcpKeyFromHeader(req.headers.authorization);
  if (!principal) {
    res.status(401).json({ error: 'Unauthorized' });
    return;
  }

  const server = new McpServer({ name: 'marsys-jis', version: '1.0.0' });
  const getPrincipal = () => principal;
  registerAskMadhav(server, getPrincipal);
  registerPlanQuery(server, getPrincipal);
  registerExecutePlan(server, getPrincipal);

  const transport = new StreamableHTTPServerTransport({ sessionIdGenerator: undefined });
  await server.connect(transport);
  await transport.handleRequest(req, res, req.body);
});

// Health check
app.get('/health', (_req, res) => res.json({ status: 'ok', service: 'marsys-mcp' }));

const port = parseInt(process.env.MCP_PORT ?? '8080', 10);
app.listen(port, () => console.log(`MARSYS MCP server listening on :${port}`));
```

Also author `platform-mcp/src/auth.ts` — thin wrapper around the MCP
server's own key validation (calls the platform's `/api/mcp/keys/validate`
endpoint, OR duplicates a lightweight bearer-parse + database lookup if
the MCP server has a direct DB connection. **Architecture decision for
this session:** call-through to platform is the correct approach — MCP
server has no direct DB; it delegates validation to the platform. Add a
`GET /api/mcp/keys/validate` endpoint to the platform that accepts the
raw bearer token and returns `{ valid, user_uid, audience_tier, key_id }`).

**AC.MCP_2_S1.8:** `server.ts` compiles; `auth.ts` exports `validateMcpKeyFromHeader`;
health endpoint defined; all 3 tools registered; TypeScript strict passes.

**Why:** Entry point wires everything together. Per-request McpServer
instances enforce statelessness (D10). Health endpoint is required for
Cloud Run health checks.

Commit: `feat(mcp): MCP-2-S1 item 8 — platform-mcp/src/server.ts HTTP/SSE server`

---

### Item 9 — Cloud Run deploy config

**What:**
- Author `platform-mcp/Dockerfile`:
  ```dockerfile
  FROM node:20-alpine
  WORKDIR /app
  COPY package*.json ./
  RUN npm ci --omit=dev
  COPY dist/ ./dist/
  EXPOSE 8080
  CMD ["node", "dist/server.js"]
  ```
- Author `platform-mcp/cloudbuild.yaml`:
  ```yaml
  steps:
    - name: 'node:20-alpine'
      entrypoint: npm
      args: ['ci']
    - name: 'node:20-alpine'
      entrypoint: npm
      args: ['run', 'build']
    - name: 'gcr.io/cloud-builders/docker'
      args: ['build', '-t', 'gcr.io/$PROJECT_ID/amjis-mcp:$COMMIT_SHA', '.']
    - name: 'gcr.io/cloud-builders/docker'
      args: ['push', 'gcr.io/$PROJECT_ID/amjis-mcp:$COMMIT_SHA']
    - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
      entrypoint: gcloud
      args:
        - run
        - deploy
        - amjis-mcp
        - '--image=gcr.io/$PROJECT_ID/amjis-mcp:$COMMIT_SHA'
        - '--region=asia-south1'
        - '--platform=managed'
        - '--memory=512Mi'
        - '--min-instances=1'
        - '--concurrency=80'
        - '--allow-unauthenticated'
        - '--set-env-vars=PLATFORM_URL=https://amjis-web-<hash>-el.a.run.app'
  images:
    - 'gcr.io/$PROJECT_ID/amjis-mcp:$COMMIT_SHA'
  ```
  Note: `PLATFORM_URL` placeholder is filled by the operator at first deploy.
  Add a comment in the YAML to that effect.

**AC.MCP_2_S1.9:** Both files exist; `Dockerfile` uses Node 20 Alpine;
`cloudbuild.yaml` deploys `amjis-mcp` to `asia-south1` with `min-instances=1`.

**Why:** Deployment config is required for the workstream to be shippable.
Creating it in this session avoids a gap in MCP-MERGE.

Commit: `chore(mcp): MCP-2-S1 item 9 — Dockerfile + cloudbuild.yaml for amjis-mcp`

---

### Item 10 — `platform-mcp/README.md` (skeleton)

**What:** Author `platform-mcp/README.md` with the following sections:
- **MARSYS-JIS MCP Server** — one paragraph overview, link to `MCP_BRIEF_v1_0.md`
- **Architecture** — two-paragraph summary of the MCP server's role
  (thin adapter; logic on platform; `platform-mcp/ → /api/mcp/*`)
- **Prerequisites** — Node 20, env vars required
- **Local development** — `npm install && npm run dev`
- **Deployment** — Cloud Build trigger; Cloud Run service `amjis-mcp`
- **Tools (v1)** — placeholder list: `ask_madhav`, `plan_query`,
  `execute_plan`, 10 primitives (MCP-3-S1), `read_asset`, `get_trace`,
  `list_recent_queries` (MCP-3-S2), `log_prediction`, `record_outcome`,
  `flag_disagreement` (MCP-4-S1)
- **Resources** — `marsys://chart-overview`, `marsys://house-rules`
  (authored MCP-2-S2)
- **Auth** — one paragraph: Bearer key; key issuance via `/admin/mcp/keys`

**AC.MCP_2_S1.10:** README exists; all 8 sections present; tool list
covers all 16 v1 tools + 2 resources.

**Why:** Next session (MCP-2-S2) adds resource content; later sessions add
tools. README serves as the living index.

Commit: `docs(mcp): MCP-2-S1 item 10 — platform-mcp/README.md skeleton`

---

### Item 11 — TypeScript compilation gate

**What:** Run `cd platform-mcp && npx tsc --noEmit` and confirm it exits 0.
Fix any type errors before marking this item complete.

Also run `cd platform-mcp && npm run build` to confirm the compiled output
appears in `dist/`.

**AC.MCP_2_S1.11:** `npx tsc --noEmit` exits 0; `npm run build` exits 0;
`dist/server.js` exists.

**Why:** TypeScript compilation is the gate command for this session. A
type error discovered in a later session is more expensive to fix.

Commit: `chore(mcp): MCP-2-S1 item 11 — tsc gate passes; build artifacts confirmed`

---

## §4 — Session-open handshake

You are a Conductor sub-agent. State briefly at start:

"MCP-2-S1 opening. Will scaffold platform-mcp/ Node service: package.json,
tsconfig, types, client, 3 Tier-1/2 tools (placeholder descriptions),
server.ts, Dockerfile, cloudbuild.yaml, README. 11 scope items.
No platform/ changes in this session — that's owned by MCP-1-S1 (complete)
and MCP-3-S1 (primitives)."

---

## §5 — Scope constraints

### may_touch

```
platform-mcp/package.json                          # CREATE
platform-mcp/package-lock.json                     # CREATE (generated)
platform-mcp/tsconfig.json                         # CREATE
platform-mcp/.gcloudignore                         # CREATE
platform-mcp/.env.example                          # CREATE
platform-mcp/Dockerfile                            # CREATE
platform-mcp/cloudbuild.yaml                       # CREATE
platform-mcp/README.md                             # CREATE
platform-mcp/src/server.ts                         # CREATE
platform-mcp/src/auth.ts                           # CREATE
platform-mcp/src/client.ts                         # CREATE
platform-mcp/src/types.ts                          # CREATE
platform-mcp/src/tools/ask_madhav.ts               # CREATE
platform-mcp/src/tools/plan_query.ts               # CREATE
platform-mcp/src/tools/execute_plan.ts             # CREATE
platform/src/app/api/mcp/keys/validate/route.ts    # CREATE (key validation endpoint needed by MCP server auth)
00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCP_2_S1_v1_0.md  # status flip PENDING → COMPLETE
```

### must_not_touch

```
platform/src/lib/pipeline/**                        # planner unchanged
platform/src/lib/retrieve/**                        # retrieval tools unchanged
platform/src/app/api/chat/consume/**                # orchestrator route unchanged
platform/src/app/api/mcp/execute/**                 # created in MCP-1-S1, do not modify
platform/src/app/api/mcp/keys/route.ts              # created in MCP-1-S1, do not modify
platform/src/lib/mcp/**                             # created in MCP-1-S1, do not modify
01_FACTS_LAYER/**                                   # L1 sealed
025_HOLISTIC_SYNTHESIS/**                           # L2.5 sealed
00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md              # planner prompt sealed
00_ARCHITECTURE/MACRO_PLAN_v2_0.md                  # macro arc unchanged
00_ARCHITECTURE/CAPABILITY_MANIFEST.json            # appended in MCP-2-S1 brief per MCP_BRIEF §11.2
CLAUDE.md                                           # §E update is post-workstream-close
```

### Commit cadence

Commit after each scope item with format:

```
<type>(mcp): MCP-2-S1 item <N> — <one-line summary>

<2-3 line description>
Acceptance criterion: AC.MCP_2_S1.<N>
```

---

## §6 — Session-close checklist (FINAL_SUMMARY)

After all 11 scope items are completed and the gate command passes, emit:

```
---FINAL_SUMMARY---
session_id: MCP-2-S1
status: PASS | HALT_NEEDS_HUMAN
commits:
  - <sha_item_1>
  - <sha_item_2>
  - <sha_item_3>
  - <sha_item_4>
  - <sha_item_5>
  - <sha_item_6>
  - <sha_item_7>
  - <sha_item_8>
  - <sha_item_9>
  - <sha_item_10>
  - <sha_item_11>
scope_items_completed:
  - AC.MCP_2_S1.1   # platform-mcp/ project initialized
  - AC.MCP_2_S1.2   # npm install passed
  - AC.MCP_2_S1.3   # types.ts
  - AC.MCP_2_S1.4   # client.ts
  - AC.MCP_2_S1.5   # ask_madhav tool
  - AC.MCP_2_S1.6   # plan_query tool
  - AC.MCP_2_S1.7   # execute_plan tool
  - AC.MCP_2_S1.8   # server.ts
  - AC.MCP_2_S1.9   # Dockerfile + cloudbuild.yaml
  - AC.MCP_2_S1.10  # README.md skeleton
  - AC.MCP_2_S1.11  # tsc gate passes
scope_items_failed: []
gate_command_runs:
  - name: mcp_2_s1_scaffold_gate
    result: PASS | FAIL
notes_for_orchestrator: >
  platform-mcp/ Node service scaffolded. Tool descriptions are placeholders —
  full §4.6 descriptions land in MCP-2-S2. platform/src/app/api/mcp/keys/validate/
  route added to support MCP server auth (key validation call-through). Next
  session (MCP-2-S2) authors §4.6 descriptions + both MCP resources.
human_decision_needed: >
  <empty if PASS>
---END_FINAL_SUMMARY---
```

---

*End of CLAUDECODE_BRIEF_MCP_2_S1_v1_0.md.*
