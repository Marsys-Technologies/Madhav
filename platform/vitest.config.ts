import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test-setup.ts'],
    globals: true,
    exclude: [
      '**/node_modules/**',
      '**/dist/**',
      // Playwright e2e suites — run via `playwright test`, not vitest.
      // Exception: tests/e2e/r11g-server-smoke/ uses vitest (server-side smoke, R11.G-S5).
      'tests/e2e/chat-v2/**',
      'tests/e2e/clients.spec.ts',
      'tests/e2e/gate_i_performance_smoke.spec.ts',
      'tests/e2e/gate_ii_trace_smoke.spec.ts',
      'tests/e2e/gate_iii_intelligent_chat_smoke.spec.ts',
      'tests/e2e/portal/**',
      // D-S5 Playwright e2e spec — runs via playwright test, not vitest.
      'tests/e2e/new-client-flow.spec.ts',
      // Playwright visual spec — no env vars in unit mode, file-level FAIL without this guard.
      'tests/visual/R11B_brand_preservation.spec.ts',
      // Integration tests requiring uvicorn (Python sidecar) — not available in CI.
      'tests/integration/test_muhurat_finder_e2e.test.ts',

      // ── TEARDOWN-EXCLUDED — re-enable when L0–L3 tools/contracts are re-registered
      //    (Build-Guarantor Gate-1). These tests were broken by PR #187 (Legacy teardown,
      //    2026-06-02) which cleared RETRIEVAL_TOOLS=[], CONTRACT_CATALOG=[], and removed
      //    FORENSIC_ASTROLOGICAL_DATA_v8_0.md plus other L0 artefacts.
      //    See KNOWN_PRE_EXISTING_FAILURES.md v1.7 for per-test re-enable mapping. ──
      // Group A — CONTRACT_CATALOG=[] (re-enable: L0 Gate-1 contract repopulation)
      'src/lib/gateway/__tests__/gateway.test.ts',
      'src/lib/contract/__tests__/unified_contract.test.ts',
      'src/lib/contract/__tests__/tool_asset_coverage.test.ts',
      // Group B — RETRIEVAL_TOOLS=[] (re-enable: per-layer tool registration)
      'tests/governance/sla_probe_new_tools.test.ts',
      'src/__tests__/integration/mcp_stub_engines.integration.test.ts',
      'tests/synthesis/tool_catalogue_schema_normalization.test.ts',
      'tests/retrieval/tool_catalogue.test.ts',
      'src/lib/router/__tests__/retrieval_capability_spec.test.ts',
      'tests/retrieve/ucn_cdlm_rm.test.ts',
      // Group C — L0 FORENSIC file absent (re-enable: L0 fact-layer file recreated)
      'src/scripts/manifest/__tests__/auto_deriver.test.ts',
      'src/scripts/manifest/__tests__/frontmatter_check.test.ts',
      // Group D — DB/migration infra (re-enable: L0 migration bootstrap complete)
      'src/lib/db/__tests__/observatory_schema.test.ts',
      'src/lib/db/__tests__/migrations.test.ts',
      'src/lib/observatory/__tests__/queries.test.ts',
      // Group E — integration tests requiring live tools (re-enable: L1–L2 tools live)
      'tests/classical/classical_pipeline_integration.test.ts',
      'tests/integration/test_query_panchanga_e2e.test.ts',
      // Group F — build trigger infra (re-enable: new build job wired, Gate-2)
      'src/app/api/build/__tests__/e2e.test.ts',
      'src/app/api/build/__tests__/start_route.test.ts',
    ],
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      // server-only throws in vitest (jsdom env); redirect to a no-op stub.
      'server-only': path.resolve(__dirname, './src/__mocks__/server-only.ts'),
    },
  },
})
