import { defineConfig, devices } from '@playwright/test'

const baseURL = process.env.AI_CONSOLE_E2E_BASE_URL ?? 'http://localhost:3000'

export default defineConfig({
  testDir: '.',
  testMatch: ['byok-routing.spec.ts'],
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
  webServer: process.env.AI_CONSOLE_E2E_EXTERNAL_SERVER === 'true' ? undefined : {
    command: 'npm run dev',
    url: `${baseURL}/api/health`,
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
    stdout: 'pipe',
    stderr: 'pipe',
  },
})
