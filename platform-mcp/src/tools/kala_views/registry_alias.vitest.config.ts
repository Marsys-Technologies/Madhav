import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vitest/config'

// Test-only integration with the platform descriptor. Runtime packages remain separate.
export default defineConfig({
  resolve: { alias: { '@': fileURLToPath(new URL('../../../../platform/src/', import.meta.url)) } },
  test: { environment: 'node', include: ['src/**/*.test.ts'] },
})
