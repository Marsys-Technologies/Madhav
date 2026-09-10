import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      'server-only': path.resolve(__dirname, './src/__mocks__/server-only.ts'),
    },
  },
  test: {
    environment: 'node',
    globals: true,
    include: [
      'src/lib/retrieval/registry/layers/L0_brahmagyan/__tests__/test_query_yoga_catalog_total.ts',
    ],
  },
})
