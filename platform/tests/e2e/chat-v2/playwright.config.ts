/**
 * Chat V2 workstream — Playwright configuration.
 * Used by `npm run chat-v2:e2e` and related scripts.
 *
 * Covers:
 *  - 3 desktop browsers (Chromium, Firefox, WebKit)
 *  - 2 mobile viewports (375px iPhone SE, 768px iPad Mini)
 *
 * All chat-v2 specs run with MARSYS_FIXTURE_MODE=true (set by globalSetup)
 * so they do not call real provider APIs.
 */
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: '.',
  globalSetup: './global-setup',
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL ?? 'http://localhost:3000',
    screenshot: 'only-on-failure',
    trace: 'on-first-retry',
    video: 'off',
  },
  timeout: 30_000,
  expect: {
    timeout: 5_000,
  },
  workers: process.env.CI ? 1 : 2,
  reporter: process.env.CI ? 'github' : 'list',
  snapshotDir: './__visuals__',
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
    {
      name: 'Mobile Safari 375',
      use: { ...devices['iPhone SE'] },
    },
    {
      name: 'iPad Safari 768',
      use: { ...devices['iPad Mini'] },
    },
  ],
})
