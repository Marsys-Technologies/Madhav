/**
 * vitest.config.ts — R11.G smoke test suite local config
 *
 * Separate config so these server-side integration smokes run with vitest
 * without being blocked by the root vitest.config.ts `tests/e2e/**` exclude.
 *
 * Run: pnpm vitest run tests/e2e/r11g-server-smoke/ --config tests/e2e/r11g-server-smoke/vitest.config.ts
 */

import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: [path.resolve(__dirname, '../../../src/test-setup.ts')],
    globals: true,
    include: ['**/*.{test,spec}.?(c|m)[jt]s?(x)'],
    // No exclude on e2e/** — this is the smoke config
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, '../../../src'),
      'server-only': path.resolve(__dirname, '../../../src/__mocks__/server-only.ts'),
    },
  },
})
