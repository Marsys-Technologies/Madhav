/**
 * vitest.smoke.config.ts — Gate III smoke test runner config.
 *
 * Runs .smoke.ts files (excluded from the default test sweep) against the
 * live Gemini API. Requires GOOGLE_GENERATIVE_AI_API_KEY in .env.local.
 *
 * Usage:
 *   npx vitest run --config vitest.smoke.config.ts
 *   npx vitest run --config vitest.smoke.config.ts tests/smoke/correction_live.smoke.ts
 */

import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    include: ['tests/smoke/**/*.smoke.ts'],
    environment: 'node',
    setupFiles: ['./src/test-setup.ts'],
    globals: true,
    // Live API calls can be slow; allow 90s per test
    testTimeout: 90_000,
    pool: 'forks',
    // Load .env.local so GOOGLE_GENERATIVE_AI_API_KEY is available
    env: {
      ...((() => {
        try {
          const fs = require('fs')
          const contents = fs.readFileSync('.env.local', 'utf-8')
          const env: Record<string, string> = {}
          for (const line of contents.split('\n')) {
            const m = line.match(/^([A-Z_][A-Z0-9_]*)=(.*)$/)
            if (m) env[m[1]] = m[2].trim()
          }
          return env
        } catch { return {} }
      })()),
    },
  },
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') },
  },
})
