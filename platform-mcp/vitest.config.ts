import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    environment: 'node',
    globals: true,
    include: [
      'test/**/*.test.ts',
      'test/bench/run.ts',
    ],
    exclude: ['**/node_modules/**', '**/dist/**'],
  },
})
