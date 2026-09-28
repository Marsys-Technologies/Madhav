import { defineConfig, devices } from '@playwright/test'
import { parseLoopbackHttpUrl } from '../../../scripts/ai-console/owner_preflight'

const baseURL = process.env.AI_CONSOLE_E2E_BASE_URL ?? 'http://localhost:3000'
if (!parseLoopbackHttpUrl(baseURL, true)) throw new Error('AIC_E2E_BASE_URL_NOT_LOOPBACK')

export default defineConfig({
  testDir: '.',
  testMatch: ['byok-routing.spec.ts'],
  outputDir: process.env.AI_CONSOLE_E2E_ARTIFACT_DIR ?? '/tmp/madhav-ai-console-e2e-unqualified',
  timeout: 180_000,
  expect: { timeout: 10_000 },
  workers: 1,
  reporter: 'list',
  use: {
    baseURL,
    screenshot: 'off',
    trace: 'off',
    video: 'off',
    navigationTimeout: 30_000,
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
})
