# Integration Tests

These tests require a running local environment. They are skipped in CI unless
integration env vars are set.

## Setup

1. Start DB proxy: `bash platform/scripts/start_db_proxy.sh`
2. Start Next.js dev server: `cd platform && npm run dev`
3. Set env vars:
   - `DB_PROXY_PORT=5433`
   - `INTEGRATION_TEST_API_KEY=<mcp_api_key>`
   - `INTEGRATION_TEST_BASE_URL=http://localhost:3000`
   - `INTEGRATION_CHART_ID=362f9f17-95a5-490b-a5a7-027d3e0efda0` (optional, this is default)

## Run

```bash
DB_PROXY_PORT=5433 INTEGRATION_TEST_API_KEY=<key> npx vitest run src/__tests__/integration/
```

## CI

Integration tests are skipped when `DB_PROXY_PORT` or `INTEGRATION_TEST_API_KEY` is absent.
They can be enabled in CI by adding the secrets to the GitHub Actions workflow.
