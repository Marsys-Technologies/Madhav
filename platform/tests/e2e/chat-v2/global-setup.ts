/**
 * Chat V2 — Playwright global setup.
 *
 * Responsibilities:
 *  1. Enable fixture mode so E2E tests don't call real providers.
 *  2. Validate the fixture directory tree is present.
 *  3. Write auth storageState.json if MARSYS_SUPER_ADMIN_SESSION is set,
 *     so visual-baseline specs can reach auth-gated routes (/dev/chat-spike).
 *  4. Log configuration for debugging.
 */
import { FullConfig } from '@playwright/test'
import path from 'path'
import fs from 'fs'

const STORAGE_STATE_PATH = path.join(__dirname, 'storageState.json')

export default async function globalSetup(_config: FullConfig): Promise<void> {
  // Activate fixture mode for the server process under test.
  // Next.js reads this via process.env at request time.
  process.env.MARSYS_FIXTURE_MODE = process.env.MARSYS_FIXTURE_MODE ?? 'true'

  if (process.env.MARSYS_FIXTURE_MODE === 'true') {
    const fixtureRoot = path.join(process.cwd(), 'tests', 'fixtures', 'chat-v2')
    if (!fs.existsSync(fixtureRoot)) {
      throw new Error(
        `[chat-v2/global-setup] Fixture root not found: ${fixtureRoot}.\n` +
          'Run the worktree setup or restore fixtures from the repo.',
      )
    }
    console.log(`[chat-v2/global-setup] Fixture mode ENABLED — root: ${fixtureRoot}`)
  } else {
    console.log(
      '[chat-v2/global-setup] Fixture mode DISABLED — tests will call live providers.',
    )
  }

  // If a super-admin session cookie is available, write a Playwright storageState
  // so visual-baseline specs can navigate to auth-gated routes without per-test
  // cookie injection (visual specs don't have beforeEach auth hooks).
  const session = process.env.MARSYS_SUPER_ADMIN_SESSION
  if (session) {
    const storageState = {
      cookies: [
        {
          name: '__session',
          value: session,
          domain: 'localhost',
          path: '/',
          expires: -1,
          httpOnly: false,
          secure: false,
          sameSite: 'Lax' as const,
        },
      ],
      origins: [],
    }
    fs.writeFileSync(STORAGE_STATE_PATH, JSON.stringify(storageState, null, 2))
    console.log(`[chat-v2/global-setup] Auth storageState written → ${STORAGE_STATE_PATH}`)
  } else {
    // No session: write empty storageState so playwright.config.ts can always reference the file.
    // Tests that require auth use test.skip(!SESSION, ...) to self-protect.
    fs.writeFileSync(STORAGE_STATE_PATH, JSON.stringify({ cookies: [], origins: [] }, null, 2))
    console.log('[chat-v2/global-setup] No MARSYS_SUPER_ADMIN_SESSION — empty storageState written')
  }

  // Log base URL for debugging.
  const baseURL = process.env.PLAYWRIGHT_BASE_URL ?? 'http://localhost:3000'
  console.log(`[chat-v2/global-setup] Base URL: ${baseURL}`)
}
