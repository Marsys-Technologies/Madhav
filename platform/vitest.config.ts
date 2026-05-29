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
      // Playwright visual spec — no env vars in unit mode, file-level FAIL without this guard.
      'tests/visual/R11B_brand_preservation.spec.ts',
      // Integration tests requiring uvicorn (Python sidecar) — not available in CI.
      'tests/integration/test_muhurat_finder_e2e.test.ts',
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
