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
import path from 'path'

// storageState.json is written by global-setup when MARSYS_SUPER_ADMIN_SESSION is set.
// Always reference the path; Playwright reads it per-test after global-setup runs.
const STORAGE_STATE_PATH = path.join(__dirname, 'storageState.json')

export default defineConfig({
  testDir: '.',
  globalSetup: './global-setup',
  // Auto-start Next.js dev server when no server is already running.
  // CI: always starts fresh (reuseExistingServer=false).
  // Local: reuses operator's running server.
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
    env: {
      MARSYS_FIXTURE_MODE: 'true',
      // Forward Firebase vars from CI env so Next.js can start without auth/invalid-api-key
      NEXT_PUBLIC_FIREBASE_API_KEY: process.env.NEXT_PUBLIC_FIREBASE_API_KEY ?? '',
      NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN ?? '',
      NEXT_PUBLIC_FIREBASE_PROJECT_ID: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID ?? '',
      NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET ?? '',
      NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID ?? '',
      NEXT_PUBLIC_FIREBASE_APP_ID: process.env.NEXT_PUBLIC_FIREBASE_APP_ID ?? '',
    },
  },
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL ?? 'http://localhost:3000',
    screenshot: 'only-on-failure',
    trace: 'on-first-retry',
    video: 'off',
    // storageState.json is written by global-setup when MARSYS_SUPER_ADMIN_SESSION is set.
    // Empty-cookie file written when session absent — no-op but keeps Playwright happy.
    storageState: STORAGE_STATE_PATH,
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
