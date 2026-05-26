# System Tests — Portal Pipeline E2E

These tests exercise the full portal query pipeline from HTTP request through LLM response.
They are authored as part of SRP-T-4 (System Repair Plan — Test session 4).

## Running

```bash
# From platform/ directory
SMOKE_BASE_URL=http://localhost:3002 \
SMOKE_CHART_ID=362f9f17-95a5-490b-a5a7-027d3e0efda0 \
SMOKE_SESSION_COOKIE=<your_session_cookie> \
npx vitest run src/__tests__/system/
```

All tests skip gracefully when `SMOKE_SESSION_COOKIE` is absent, making this CI-safe.

## Required env vars

| Variable | Required | Default | Description |
|---|---|---|---|
| `SMOKE_BASE_URL` | No | `http://localhost:3000` | Base URL of the running portal |
| `SMOKE_SESSION_COOKIE` | Yes (for live run) | — | Firebase session cookie |
| `SMOKE_CHART_ID` | No | `362f9f17-...` | Chart ID to query against |

## Optional env vars

| Variable | Default | Description |
|---|---|---|
| `SMOKE_TEST_ALL_PROVIDERS` | — | Set to `true` to run all 5 providers (costs tokens) |
| `MCP_BASE_URL` | `SMOKE_BASE_URL` | MCP sidecar base URL |
| `INTEGRATION_TEST_API_KEY` | — | MCP API key (enables MCP channel suite) |

## Test suites

1. **Adapter pipeline active** — verifies R11V2 adapter path, no legacy `createOrchestrator` errors
2. **B.11 floor tools** — verifies the 5 mandatory tools appear in every query trace
3. **forward_looking routing** — verifies future transit/dasha queries reach predictive signals
4. **Multi-provider smoke** — Anthropic default; all 5 providers opt-in via `SMOKE_TEST_ALL_PROVIDERS`
5. **MCP channel smoke** — `msr_sql`, `query_chart_facts`, `temporal` tool endpoints

## Minting a session cookie

```bash
cd platform
npx tsx scripts/mint_session_cookie.ts
```

Follow the prompts to obtain a `__session` cookie value.
