# MARSYS-JIS MCP Server

The MARSYS-JIS MCP Server exposes the Jyotish instrument as a Model Context
Protocol service. External Claude sessions (Claude Chat custom integrations,
Cowork remote MCPs) connect to this service and gain access to 16 tools
spanning the full MARSYS-JIS capability surface — from the end-to-end
synthesis pipeline to surgical primitive lookups, raw canonical asset reads,
and observability tooling.

This service is intentionally thin: it is an SDK adapter. All astrological
intelligence, synthesis logic, retrieval tools, and governance enforcement
live on the platform (the `amjis-web` Cloud Run service). The MCP server's
job is to validate Bearer API keys, translate MCP tool calls into HTTPS
requests to `/api/mcp/*`, and translate responses back into MCP tool results.

For the full architectural specification see:
`00_ARCHITECTURE/BRIEFS/MCP_BRIEF_v1_0.md`.

---

## Architecture

The MCP server sits between external MCP clients and the MARSYS platform:

```
Claude Chat / Cowork
       │
       │  (Bearer API key, MCP protocol over HTTP/SSE)
       ▼
platform-mcp (amjis-mcp Cloud Run service)   ← this service
   validates Bearer key → resolves principal
   POST /api/mcp/* with X-MCP-Internal-Token + principal headers
       │
       │  (HTTPS, service-to-service identity token)
       ▼
platform (amjis-web Cloud Run service)
   /api/mcp/execute  — planner → tools → synthesis → envelope
   /api/mcp/plan     — planner only (plan_query)
   /api/mcp/primitives/{tool}  — surgical tool dispatch (MCP-3)
   /api/mcp/keys/validate      — Bearer key validation
```

All governance rules (B.11 Whole-Chart-Read floor, audience-tier stamping,
epistemics block, trace logging, PPL discipline) are enforced on the platform
side. The MCP server cannot bypass them. Every response carries a `trace_id`
the caller can pass to `get_trace()` for full pipeline auditability.

---

## Prerequisites

- **Node.js 20+** (`node --version` should print `v20.*` or higher)
- **TypeScript** (installed as a dev dependency; `npm run typecheck` uses it)
- A running MARSYS platform instance (local Next.js dev server or Cloud Run)

Required environment variables (copy `.env.example` to `.env.local`):

| Variable | Description |
|---|---|
| `PLATFORM_URL` | Base URL of the amjis-web platform (no trailing slash) |
| `MCP_INTERNAL_TOKEN` | Shared secret for X-MCP-Internal-Token service auth |
| `MCP_PORT` | HTTP listen port (default: 8080) |
| `SERVICE_TOKEN` | (Local dev only) Static identity token override |

---

## Local development

```bash
cd platform-mcp
npm install

# Copy env template and fill in values
cp .env.example .env.local
# edit .env.local — set PLATFORM_URL=http://localhost:3000 for local dev

# Start the MCP server in watch mode (reloads on file changes)
npm run dev

# Type-check without building
npm run typecheck
```

The server listens on `http://localhost:8080` (or `MCP_PORT` if set).
Health check: `curl http://localhost:8080/health`

For local testing, ensure the MARSYS platform is running on port 3000 and that
`MCP_INTERNAL_TOKEN` matches the `MCP_INTERNAL_TOKEN` env var on the platform.

---

## Deployment

The MCP server is deployed as a Cloud Run service named `amjis-mcp` in
`asia-south1`, sibling to `amjis-web` and `amjis-sidecar`.

**First deploy (operator steps):**

1. Update `cloudbuild.yaml` — replace the `PLATFORM_URL=https://amjis-web-PLACEHOLDER-...`
   placeholder with the actual `amjis-web` Cloud Run URL.
2. Set `MCP_INTERNAL_TOKEN` on both services to the same shared secret (use
   Cloud Run secrets or `--set-env-vars`).
3. Trigger the Cloud Build pipeline (or run manually):
   ```bash
   cd platform-mcp
   npm run build
   docker build -t gcr.io/<project-id>/amjis-mcp:latest .
   gcloud run deploy amjis-mcp \
     --image gcr.io/<project-id>/amjis-mcp:latest \
     --region asia-south1 \
     --memory 512Mi --min-instances 1 --concurrency 80 \
     --allow-unauthenticated \
     --set-env-vars PLATFORM_URL=<amjis-web-url>,MCP_INTERNAL_TOKEN=<secret>
   ```

**Subsequent deploys** are automated via the Cloud Build trigger configured
for the `feature/mcp-server` branch (and `main` after merge).

---

## Tools (v1)

The MCP server registers the following 16 tools across 5 tiers:

### Tier 1 — End-to-end pipeline
| Tool | Status |
|---|---|
| `ask_madhav` | **LIVE** (MCP-2-S1) |

### Tier 2 — Plan inspection & explicit execution
| Tool | Status |
|---|---|
| `plan_query` | **LIVE** (MCP-2-S1) |
| `execute_plan` | **LIVE** (MCP-2-S1) |

### Tier 3 — Surgical primitives (landing MCP-3-S1)
| Tool | Underlying tool |
|---|---|
| `query_chart_facts` | `chart_facts_query` |
| `query_signals` | `msr_sql` |
| `query_dasha_periods` | `query_dasha_periods` |
| `query_panchanga` | `query_panchanga` |
| `query_ephemeris` | `query_ephemeris` |
| `query_transit_event` | `query_transit_event` |
| `lel_query` | `lel_query` |
| `vector_search` | `vector_search` |
| `get_cgm_subgraph` | `cgm_graph_walk` |
| `cross_school_lookup` | `multi_school_signal_lookup` |

### Tier 4 — Raw asset reads (landing MCP-3-S2)
| Tool | Status |
|---|---|
| `read_asset` | MCP-3-S2 |

### Tier 5 — Observability (landing MCP-3-S2)
| Tool | Status |
|---|---|
| `get_trace` | MCP-3-S2 |
| `list_recent_queries` | MCP-3-S2 |

### Writes (landing MCP-4-S1)
| Tool | Status |
|---|---|
| `log_prediction` | MCP-4-S1 |
| `record_outcome` | MCP-4-S1 |
| `flag_disagreement` | MCP-4-S1 |

---

## Resources

Two MCP resources are served at session attach (landing MCP-2-S2):

| URI | Content | Location |
|---|---|---|
| `marsys://chart-overview` | Compact summary of Abhisek's chart: lagna, key placements, active dasha, top 5 L2.5 themes, elevator-pitch synthesis | `resources/chart-overview.md` |
| `marsys://house-rules` | Operating manual for Claude: school commitments, terminology conventions, quality bars, disclosure tier, when to defer | `resources/house-rules.md` |

---

## Auth

Each principal gets a long-lived API key of the form `mcp_<env>_<random40>`.
Keys are issued via the platform admin UI at `/admin/mcp/keys` (super_admin
tier required). Keys are shown exactly once at issuance and never again; store
them in a password manager.

To use the MCP server:
1. Obtain an API key from the platform admin.
2. Configure your MCP client with the server URL and Bearer auth.
3. In Claude Chat: Settings → Integrations → Add custom integration → enter
   the `amjis-mcp` URL and paste the API key.
4. In Cowork: add the remote MCP in your Claude Code project config.

---

*MARSYS-JIS MCP Server v1.0.0 — concurrent workstream, runs alongside M5-A.*
*See `00_ARCHITECTURE/BRIEFS/MCP_BRIEF_v1_0.md` for full specification.*
