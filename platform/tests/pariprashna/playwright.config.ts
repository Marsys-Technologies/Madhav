/**
 * Paripraśna acceptance harness — Playwright configuration.
 *
 * Runs against the standalone replay server (scripts/replay/server.ts), NOT
 * against `npm run dev` — this battery has no dependency on the Next.js app
 * at all (deliberately: S-1/C-1 don't exist yet). `webServer` starts the
 * replay server automatically; `reuseExistingServer` lets a locally-running
 * instance be reused for faster iteration.
 *
 * Projects:
 *   - chromium: primary desktop battery.
 *   - mobile-390x844: brief-mandated G-MOBILE requirement — runs the FULL
 *     battery (every spec in this directory), not just a mobile-only file,
 *     at a 390x844 viewport.
 *
 * Run: `npm run pariprashna:gates` (desktop) or
 *      `npm run pariprashna:gates:mobile` (mobile project only).
 *
 * Seeded-violation ("red") runs pass `PARIPRASHNA_VIOLATE=<key>` — gate
 * specs read this env var and append `&violate=<key>` to the harness URL.
 * See scripts/replay/selftest.ts for the automated red-then-green proof
 * runner.
 */
import { defineConfig, devices } from '@playwright/test'

const PORT = process.env.PARIPRASHNA_REPLAY_PORT ?? '4795'

export default defineConfig({
  testDir: '.',
  testMatch: ['gates/**/*.spec.ts'],
  timeout: 30_000,
  expect: { timeout: 5_000 },
  workers: 1,
  reporter: process.env.CI ? 'github' : 'list',
  use: {
    baseURL: `http://localhost:${PORT}`,
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
  },
  webServer: {
    command: 'npm run pariprashna:replay-server',
    url: `http://localhost:${PORT}/health`,
    reuseExistingServer: !process.env.CI,
    timeout: 30_000,
    env: { PARIPRASHNA_REPLAY_PORT: PORT },
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    {
      name: 'mobile-390x844',
      use: { ...devices['Desktop Chrome'], viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true },
    },
  ],
})
